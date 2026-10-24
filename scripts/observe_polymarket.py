#!/usr/bin/env python3
"""Read-only Polymarket research: market discovery and timestamped snapshots.

No trading, credentials, scenario score mutation, or claims of calibrated probabilities.
"""
import datetime as dt
import json
import pathlib
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
TARGET = ROOT / "data/polymarket"
API = "https://gamma-api.polymarket.com/markets"
TERMS = ("iran", "iranian", "tehran", "hormuz", "khamenei", "nuclear deal",
         "persian gulf", "israel-iran", "us-iran", "u.s.-iran")
# Gamma's offset endpoint rejects offsets over 2000 (HTTP 422).
# With 100 markets/page, offsets 0..2000 cover at most 2,100 markets.
# Prefer keyset pagination for broader discovery in a separate change.
MAX_PAGES = 21

def unpack(value):
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
            return decoded if isinstance(decoded, list) else []
        except ValueError:
            return []
    return []

def get_page(offset):
    params = urllib.parse.urlencode({"active":"true","closed":"false",
                                      "limit":"100","offset":str(offset)})
    request = urllib.request.Request(API + "?" + params,headers={
        "Accept":"application/json","User-Agent":"IranSignalResearch/1.0"})
    with urllib.request.urlopen(request,timeout=30) as response:
        body = response.read(3_000_001)
        if len(body) > 3_000_000:
            raise ValueError("Market response too large")
    markets = json.loads(body)
    if not isinstance(markets,list):
        raise ValueError("Unexpected Gamma API schema")
    return markets

def collect():
    matches = []
    for page in range(MAX_PAGES):
        rows = get_page(page*100)
        for market in rows:
            question = str(market.get("question") or "")
            description = str(market.get("description") or "")[:500]
            if not any(t in question.lower() for t in TERMS):
                continue
            outcomes = unpack(market.get("outcomes"))
            prices = unpack(market.get("outcomePrices"))
            yes = None
            if "Yes" in outcomes:
                idx = outcomes.index("Yes")
                if idx < len(prices):
                    try:
                        yes = float(prices[idx])
                        if not 0 <= yes <= 1:
                            yes = None
                    except (TypeError,ValueError):
                        pass
            matches.append({
                "market_id":str(market.get("id","")),
                "condition_id":str(market.get("conditionId","")),
                "question":question,
                "slug":str(market.get("slug","")),
                "end_date":market.get("endDate"),
                "yes_market_price":yes,
                "volume":market.get("volumeNum",market.get("volume")),
                "liquidity":market.get("liquidityNum",market.get("liquidity")),
                "source":"Polymarket Gamma API",
                "status":"market_expectation_not_scenario_probability",
                "resolution_rule_excerpt":description,
            })
        if len(rows)<100:
            break
    return sorted(matches,key=lambda x:x["market_id"])

def main():
    records=collect() # Fail closed; no invented or replaced records on API error.
    now=dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    TARGET.mkdir(parents=True,exist_ok=True)
    snapshot={"observed_at":now,"source_api":API,"coverage_note":"Up to 2,100 active Gamma markets scanned using supported offsets (0..2000); question-filtered coverage is not exhaustive.","markets":records,
      "caveats":["Prices reflect market expectations, not calibrated event probabilities.",
                 "Quoted prices may be illiquid or stale.","Markets may share underlying information.",
                 "Do not mutate scenario scores from market observations."]}
    # Historical comparison: nearest observation at or before the 24h / 7d cutoff.
    # Do not use recent observations as a substitute for an unavailable historical baseline.
    history = []
    for days_ago in range(0, 9):
        historic_date = (dt.datetime.fromisoformat(now) - dt.timedelta(days=days_ago)).date().isoformat()
        path = TARGET / ("daily-" + historic_date + ".json")
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    history.extend(data)
            except (OSError, ValueError):
                print("Skipping unreadable archive: " + historic_date)
    current_time = dt.datetime.fromisoformat(now)
    def change(market, days):
        cutoff = current_time - dt.timedelta(days=days)
        candidates = []
        for prior in history:
            if prior.get("market_id") != market["market_id"]:
                continue
            price = prior.get("yes_market_price")
            if not isinstance(price, (int, float)) or not 0 <= price <= 1:
                continue
            try:
                timestamp = dt.datetime.fromisoformat(prior["observed_at"].replace("Z", "+00:00"))
            except (KeyError, TypeError, ValueError):
                continue
            # At most one day older than the exact lookback to avoid stale comparisons.
            if cutoff - dt.timedelta(days=1) <= timestamp <= cutoff:
                candidates.append((timestamp, price))
        if not candidates or market["yes_market_price"] is None:
            return None
        return round(100 * (market["yes_market_price"] - max(candidates)[1]), 3)
    for market in records:
        market["delta_24h"] = change(market, 1)
        market["delta_7d"] = change(market, 7)
    # Append to date-level archive as hourly observations keyed by UTC hour and market ID.
    day = now[:10]
    archive=TARGET/("daily-"+day+".json")
    existing=json.loads(archive.read_text(encoding="utf-8")) if archive.exists() else []
    hour=now[:13]
    for r in records:
        existing=[x for x in existing if not (x.get("observed_at","")[:13]==hour and x.get("market_id")==r["market_id"])]
        existing.append({"observed_at":now,**r})
    archive.write_text(json.dumps(existing,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (TARGET/"latest.json").write_text(json.dumps(snapshot,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Observed {len(records)} relevant market candidates at {now}. No score changes.")

if __name__=="__main__":
    main()
