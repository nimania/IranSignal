# Civilian Transport Research: Data Contract

This research module is **not** a live asset tracker. It is restricted to date-level civilian aggregates that can be cited and reproduced.

## Input

Add rows to `data/transport/observations.csv` with columns:
`date,metric,region,value,unit,source_url,source_name,observation_scope,verified`.

Allowed metric IDs:
- `civil_flight_volume` (commercial flight counts)
- `flight_cancellations` (aggregate count or consistently defined percentage)
- `commercial_vessel_transits` (aggregate commercial passages)
- `shipping_disruption` (aggregate published warning counts)

Use **one consistent geographic region, unit and observation scope** per time series. `observation_scope` should include the dataset/provider and sampling frame, so unlike datasets are not combined. Do not add aircraft IDs, vessel IMO/MMSI, trajectories, live coordinates, military activity, or sensitive movement observations.

Every usable row needs a valid date, a non-negative numeric value, a source HTTPS URL, and `verified=true`. A 'verified' flag means the data was checked against the attributed source, not a confirmation of any war-related inference.

## Computation

`python scripts/analyze_transport.py` produces `data/transport/analysis.json`.

For each observation date, it compares the current value with the **median of prior 28 calendar days**, requiring at least 7 valid historical observations and a positive baseline. It neither extrapolates missing days nor turns differences into scenario probabilities. Duplicate same-day values are excluded until reconciled.

`python scripts/backtest_transport.py` writes the backtest-readiness report. It does **not** claim accuracy without preregistered binary outcome definitions, lead times, reliable labels, and a temporal out-of-sample evaluation. All indicators are context-only and must not update scenario scores automatically.

## Sources and permissions

Potential data suppliers are licensed aggregate aviation/shipping APIs, regularly published airport or port totals, or openly published statistical bulletins. Their license, time coverage, and reporting lag must be verified before ingestion. News articles may support a narrative but do not substitute for consistent statistical time series.

Initially, the CSV is intentionally header-only; historical figures must not be invented. GitHub Actions recomputes aggregates after verified rows are submitted.
