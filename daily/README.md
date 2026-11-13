# IranSignal Daily Brief publication contract

The English archive is the default edition. Each publication day has one Persian report, one English editorial adaptation of the same report, and one Persian video narration. Telegram receives a concise Persian summary after editorial review.

## Publication workflow
1. Build a shared evidence dossier with source URL, publication/event time, supporting and contrary evidence, and any correction.
2. Write the Persian report and an English editorial adaptation. The English version is not a literal machine translation.
3. Separate verified observations, attributed claims, interpretation and forecasts. Do not turn a reported statement into an operational decision.
4. Add the English article at `daily/YYYY-MM-DD/slug/index.html`, the Persian article at `fa/daily/YYYY-MM-DD/slug/index.html`, and the narration at the Persian article's `full-transcript/index.html` path.
5. Use one stable `report_id` (ISO date plus edition identifier) across the manifest, Persian report and narration.
6. Append one manifest entry with `date`, `slug`, `title`, `summary`, `status: "published"`, `report_id` and author details.
7. Add the concise Telegram edition to `telegram/editorial.json`. The build script prepares a text file; it does not post to Telegram.
8. Keep the manifest sorted by date, newest first. Never silently rewrite old assessments; publish dated corrections.

## Backfill policy
When a publication gap exists, publish a clearly dated catch-up report with an explicit coverage window. Do not create retrospective entries that imply an article was written or reviewed on a date when it was not. A catch-up edition may analyse several days together, but its publication date and evidence cutoff must remain visible.

## Editorial requirements
- Do not publish essential claims that remain unverified without explicit attribution and qualification.
- Link primary documents and reputable reporting wherever possible.
- Do not invent quotations, dates, source confirmations, probabilities or market measurements.
- Scenario momentum points are directional evidence scores, not probabilities. If the source history is stale, state its last actual date and do not label it current.
- Prediction-market prices are market observations, not calibrated event probabilities. Explain contract definitions when they materially affect interpretation.
- A prepared narration is a script, not an uploaded video. Never invent a video URL or embed.

## Automation status
GitHub Actions deploys the static site and builds Telegram text from approved editorial summaries. It does not independently write, fact-check or approve the daily analysis. The scenario feed, cross-repository publication and narration production still require separate checks and human editorial review.
