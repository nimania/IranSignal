#!/usr/bin/env python3
"""Prospective-only backtest gate: report data readiness, never invent outcomes."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/transport/analysis.json"
OUTCOMES = ROOT / "data/transport/scenario_outcomes.csv"
RESULT = ROOT / "data/transport/backtest.json"

def main():
    points = json.loads(DATA.read_text(encoding="utf-8")).get("points", []) if DATA.exists() else []
    with OUTCOMES.open(newline="", encoding="utf-8") as fh:
        outcomes = list(csv.DictReader(fh))
    # An outcome label only counts if its definition and primary evidence are auditable.
    verified = [r for r in outcomes if r.get("source_url", "").startswith("https://")
                and r.get("definition", "").strip() and r.get("outcome", "").strip() in ("0", "1")]
    days = {r["date"] for r in points}
    eligible = [r for r in verified if r.get("as_of_date") in days]
    # Avoid retrospective cherry-picking; scoring is disabled until an explicit pre-registered protocol exists.
    status = "awaiting_preregistered_protocol" if eligible else "insufficient_labeled_outcomes"
    result = {
        "schema_version": 1, "status": status,
        "verified_outcomes": len(verified), "dated_indicator_observations": len(points),
        "temporally_joinable_labels": len(eligible),
        "claim": "No predictive accuracy, lift, or scenario probability has been established.",
        "note": "Require pre-registered outcome definitions, training/test split by time, lead horizons, and calibration before reporting accuracy."
    }
    RESULT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(status)

if __name__ == "__main__":
    main()
