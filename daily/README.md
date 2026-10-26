# IranSignal Daily Brief publication contract

This folder is a separate, static archive at `/IranSignal/daily/`. The existing scenario dashboard stays independent.

## Publish a reviewed daily brief
1. Produce a shared evidence dossier (source URL, original publication/event times, supporting and contrary evidence, scenario change with explanation, corrections).
2. Write an **English editorial adaptation**, not an unreviewed machine translation of Pendar's Persian article. Explicitly label interpretation, uncertainty and alternatives.
3. Review both languages independently. Use one stable `report_id` (ISO date plus edition identifier) across Pendar, IranSignal and the YouTube narration. Do not publish if essential facts remain unverified.
4. Add a standalone HTML article in `daily/YYYY-MM-DD/slug/index.html` with source links, dates, canonical URL and counterpart link to Pendar. Do not invent a YouTube link before upload.
5. Append a manifest record containing `date`, `slug`, `title`, `summary`, `status: "published"`. Slug format is `YYYY-MM-DD/slug`. Draft entries are not displayed.
6. Keep the daily manifest sorted or let the archive sort by date. Never silently rewrite old predictions; publish dated corrections.

Example **schema only**, not news:
```json
{
  "date": "YYYY-MM-DD",
  "slug": "YYYY-MM-DD/descriptive-slug",
  "title": "Verified editorial headline",
  "summary": "Two-sentence factual overview.",
  "status": "published"
}
```

## Not yet automated
The archive is ready to display approved entries, but **no verified brief is currently seeded**. The external/unknown narration generator, cross-repository publisher, and Pendar homepage integration remain separate implementation tasks. An empty archive is intentional: do not fabricate reports to fill it.

## Daily output format

Each publication day has exactly one comprehensive Persian report, one English adaptation of the same report, and one Persian video narration at the report's `full-transcript/` path. Use one shared report_id and one daily manifest entry. News, scenario momentum, and prediction markets are sections of that daily report, not separate daily editions unless the user explicitly requests a special edition. Preserve the existing day-by-day archives and link the three outputs together. A prepared narration is not an uploaded video; do not invent an embed.
