#!/usr/bin/env python3
"""Read-only Pendar evidence sync. Does not alter the canonical signal ledger."""
import datetime as dt
import json
import os
import pathlib
import urllib.request

BASE = "https://pendar.io/data/"
OUT = pathlib.Path("data/pendar")
FILES = {
    "iran-scenario-signals.json": list,
    "iran-scenario-history.json": dict,
    "iran-scenario-meta.json": dict,
    "iran-scenario-snapshots.json": dict,
}

def fetch(name, expected):
    req = urllib.request.Request(BASE + name, headers={
        "User-Agent": "IranSignal/1.0 (public evidence sync)",
        "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=25) as response:
        if response.status != 200:
            raise RuntimeError(f"{name}: HTTP {response.status}")
        if int(response.headers.get("Content-Length", "0")) > 15_000_000:
            raise RuntimeError(f"{name}: too large")
        data = response.read(15_000_001)
        if len(data) > 15_000_000:
            raise RuntimeError(f"{name}: too large")
    obj = json.loads(data)
    if not isinstance(obj, expected):
        raise ValueError(f"{name}: invalid top-level JSON")
    return obj

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    completed = {}
    for name, kind in FILES.items():
        try:
            obj = fetch(name, kind)
        except Exception as exc:
            if name == "iran-scenario-snapshots.json":
                print(f"Optional {name}: {exc}")
                continue
            raise
        completed[name] = obj
    # Never replace files when required datasets cannot be obtained.
    for name, obj in completed.items():
        (OUT / name).write_text(
            json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # Stable metadata; do not write a new timestamp if nothing changed.
    print(f"Synced {len(completed)} Pendar datasets; {len(completed['iran-scenario-signals.json'])} candidate signals.")
    print("Source: https://pendar.io/data/ ; data remain attributed, unverified external evidence.")
    print("No scoring or canonical ledger mutations were performed.")

if __name__ == "__main__":
    main()
