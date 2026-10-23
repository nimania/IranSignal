# Prediction Market Expectations

IranSignal collects Polymarket metadata through the public read-only Gamma API.

- Run: `python scripts/observe_polymarket.py`
- Snapshot: `data/polymarket/latest.json`
- Historical observations: `data/polymarket/daily-YYYY-MM-DD.json`
- Schedule: hourly on GitHub Actions (best effort)
- No wallet, API secret, trade execution, or scenario score changes.

## Interpretation
YES prices are traded market quotes, **not validated real-world probabilities**. They must not be averaged across markets with different deadlines or resolution rules. Volume/liquidity are metadata, not a confidence guarantee. One news event may influence both reporting and market prices, so the latter is not independent corroboration.

## Coverage limitations
The initial collector scans only the first 500 active Gamma markets; hence some Iran markets will be missed. This is **experimental discovery**, not a comprehensive watchlist. Future work: validated event/tag filtering and stable manually approved market IDs, historical CLOB snapshots, correction handling, contractual resolution auditing, and source-specific error monitoring.

No collected observation should change the canonical IranSignal signal ledger automatically.
