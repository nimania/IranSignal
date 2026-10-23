#!/usr/bin/env python3
"""Auditable, non-tactical, aggregate civilian transport indicator analysis."""
import csv
import datetime as dt
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data/transport/observations.csv"
OUT = ROOT / "data/transport/analysis.json"
ALLOWED = {"civil_flight_volume", "flight_cancellations", "commercial_vessel_transits", "shipping_disruption"}
HIST_DAYS = 28
MIN_BASELINE = 7

def read_rows(path):
    if not path.exists():
        return []
    result = []
    with path.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            if not row.get("date") or not row.get("metric"):
                continue
            date = dt.date.fromisoformat(row["date"])
            metric = row["metric"].strip()
            if metric not in ALLOWED:
                raise ValueError("Unknown metric: " + metric)
            value = float(row["value"])
            if not math.isfinite(value) or value < 0:
                raise ValueError("Invalid aggregate observation")
            if not row.get("source_url", "").startswith("https://"):
                raise ValueError("Evidence source URL required")
            if row.get("verified", "").lower() not in ("true", "yes", "1"):
                continue
            result.append(dict(date=date, metric=metric, region=row["region"].strip(),
                               value=value, source_url=row["source_url"].strip(),
                               unit=row["unit"].strip(), observation_scope=row["observation_scope"].strip()))
    return result

def compute(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[(row["metric"], row["region"], row["unit"], row["observation_scope"])].append(row)
    output = []
    for (metric, region, unit, scope), records in sorted(groups.items()):
        # Do not combine different sampling frames or geographic scopes.
        by_date = defaultdict(list)
        for r in records:
            by_date[r["date"]].append(r)
        # Ambiguous same-day measurements must not be silently summed.
        unique = {day: rs[0] for day, rs in by_date.items() if len(rs) == 1}
        for day in sorted(unique):
            prior = [r["value"] for d, r in unique.items()
                     if day - dt.timedelta(days=HIST_DAYS) <= d < day]
            if len(prior) < MIN_BASELINE:
                continue
            baseline = median(prior)
            if baseline <= 0:
                continue
            current = unique[day]
            output.append({
                "date": day.isoformat(), "metric": metric, "region": region,
                "unit": unit, "observation_scope": scope,
                "value": current["value"], "baseline_median_28d": baseline,
                "baseline_observations": len(prior),
                "delta_pct": round((current["value"] / baseline - 1) * 100, 2),
                "source_url": current["source_url"],
                "role": "context_only_not_scenario_score"
            })
    return output

def main():
    records = read_rows(INPUT)
    results = compute(records)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1, "description": "Civilian aggregate disruption vs trailing 28-day median",
        "source_observations": len(records), "computed_points": len(results),
        "status": "ready" if results else "insufficient_verified_history",
        "method": {"baseline_days": HIST_DAYS, "minimum_baseline_observations": MIN_BASELINE,
                   "provenance": "verified rows with attributable URLs",
                   "no_tactical_tracks": True, "automatic_scenario_scoring": False},
        "points": results
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Processed {len(records)} verified observations; derived {len(results)} aggregate trend points.")

if __name__ == "__main__":
    main()
