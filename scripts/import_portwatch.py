#!/usr/bin/env python3
"""Import published, day-level aggregate Strait of Hormuz transit counts (IMF PortWatch).

Do not collect vessel IDs, positions or trajectories. No scenario scoring.
"""
import csv
import datetime as dt
import io
import json
import pathlib
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data/transport/observations.csv"
BASE = "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query"
FIELDS = ["date", "metric", "region", "value", "unit", "source_url", "source_name", "observation_scope", "verified"]
SCOPE = "IMF PortWatch; chokepoint6; n_total; AIS-observed commercial transit calls"
SOURCE = "https://portwatch.imf.org/"
CHOKEPOINT = "chokepoint6"

def fetch_page(offset):
    args = {
        "where": "portid='chokepoint6'", "outFields": "date,n_total,portid",
        "returnGeometry": "false", "orderByFields": "date ASC",
        "resultRecordCount": "500", "resultOffset": str(offset), "f": "json"}
    url = BASE + "?" + urllib.parse.urlencode(args)
    with urllib.request.urlopen(
        urllib.request.Request(url, headers={"User-Agent": "IranSignalResearch/1.0"}), timeout=35
    ) as response:
        data = response.read(3_000_001)
        if len(data) > 3_000_000:
            raise RuntimeError("PortWatch response too large")
    obj = json.loads(data)
    if "error" in obj or not isinstance(obj.get("features"), list):
        raise RuntimeError(f"Invalid PortWatch response: {str(obj.get('error'))[:200]}")
    return obj

def parse_date(v):
    if isinstance(v, (int, float)):
        return dt.datetime.fromtimestamp(v / 1000, tz=dt.timezone.utc).date().isoformat()
    if isinstance(v, str):
        return dt.date.fromisoformat(v[:10]).isoformat()
    raise ValueError("Invalid PortWatch date")

def main():
    imported = {}
    offset = 0
    while True:
        page = fetch_page(offset)
        records = page["features"]
        for item in records:
            a = item.get("attributes", {})
            if str(a.get("portid", "")).lower() != CHOKEPOINT:
                continue
            v = a.get("n_total")
            if v is None:
                continue
            value = float(v)
            if not 0 <= value <= 5000:
                raise ValueError("Suspicious daily transit count")
            date = parse_date(a["date"])
            if date in imported and imported[date] != value:
                raise RuntimeError(f"Conflicting daily count for {date}")
            imported[date] = value
        offset += len(records)
        if not records or (len(records) < 500 and not page.get("exceededTransferLimit")):
            break
        if offset > 20000:
            raise RuntimeError("Exceeded safe pagination limit")
    if len(imported) < 7:
        raise RuntimeError("Too few historical observations; refusing to replace data")
    existing = []
    if OUTPUT.exists():
        with OUTPUT.open(encoding="utf-8", newline="") as stream:
            existing = list(csv.DictReader(stream))
    # Idempotent, preserve data from any other metric or supplier.
    remaining = [r for r in existing if not (
        r.get("metric") == "commercial_vessel_transits" and
        r.get("observation_scope") == SCOPE)]
    for date, value in sorted(imported.items()):
        remaining.append({
            "date": date, "metric": "commercial_vessel_transits", "region": "Strait of Hormuz",
            "value": str(int(value) if value.is_integer() else value), "unit": "daily_calls",
            "source_url": SOURCE, "source_name": "IMF PortWatch",
            "observation_scope": SCOPE, "verified": "true"})
    remaining.sort(key=lambda r:(r.get("date",""),r.get("metric",""),r.get("observation_scope","")))
    buffer = io.StringIO()
    writer=csv.DictWriter(buffer,fieldnames=FIELDS,lineterminator="\n")
    writer.writeheader()
    writer.writerows(remaining)
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(buffer.getvalue(),encoding="utf-8")
    print(f"Imported {len(imported)} published aggregate daily observations from IMF PortWatch. No scenario scores changed.")
    print("Note: PortWatch is delayed and AIS-derived; missing transmissions and revisions are possible.")

if __name__=="__main__":
    main()
