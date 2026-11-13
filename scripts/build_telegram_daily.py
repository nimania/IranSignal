"""Generate a concise Persian Telegram edition for every published IranSignal daily report.
Run: python3 scripts/build_telegram_daily.py
Requires each Persian article to include a matching entry in telegram/editorial.json.
No credentials, network requests, or automatic Telegram posting.
"""
from __future__ import annotations
import json
import re
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FA_BASE = "https://nimania.github.io/IranSignal/fa/daily/"
EN_BASE = "https://nimania.github.io/IranSignal/daily/"

def build():
    manifest = json.loads((ROOT / "daily/manifest.json").read_text(encoding="utf-8"))
    editorial = json.loads((ROOT / "telegram/editorial.json").read_text(encoding="utf-8"))
    out = ROOT / "telegram/daily"
    out.mkdir(parents=True, exist_ok=True)
    published = [r for r in manifest if r.get("status") == "published"]
    dates = sorted(date.fromisoformat(r["date"]) for r in published)
    if not dates:
        raise SystemExit("No published daily reports in manifest")
    expected = []
    cursor = dates[0]
    while cursor <= dates[-1]:
        expected.append(cursor.isoformat())
        cursor += timedelta(days=1)
    actual = sorted(d.isoformat() for d in dates)
    missing = sorted(set(expected) - set(actual))
    if missing:
        raise SystemExit(f"Missing daily report dates: {', '.join(missing)}")
    for report in published:
        slug = report["slug"]
        data = editorial.get(slug)
        if not data:
            raise SystemExit(f"Missing approved Telegram editorial summary for {slug}")
        for field in ("date_fa", "title", "lead", "analysis", "watch"):
            if not isinstance(data.get(field), str) or not data[field].strip():
                raise SystemExit(f"Missing {field} for {slug}")
        fa_article = ROOT / "fa/daily" / slug / "index.html"
        en_article = ROOT / "daily" / slug / "index.html"
        transcript = ROOT / "fa/daily" / slug / "full-transcript" / "index.html"
        if not fa_article.is_file():
            raise SystemExit(f"Persian article missing for {slug}")
        if not en_article.is_file():
            raise SystemExit(f"English article missing for {slug}")
        if not transcript.is_file():
            raise SystemExit(f"Persian narration script missing for {slug}")
        transcript_html = transcript.read_text(encoding="utf-8")
        match = re.search(r"([0-9,]+) واژه", transcript_html)
        if not match or int(match.group(1).replace(",", "")) < 850:
            raise SystemExit(f"Persian narration is missing a valid word-count note or is under 850 words: {slug}")
        parts = [
            "📡 ایران سیگنال | گزارش روز",
            f"🗓 {data['date_fa']}",
            "",
            f"🔴 {data['title']}",
            "",
            data["lead"],
            "",
            "🔎 جان کلام:",
            data["analysis"],
            "",
            "📍 در رصد بعدی:",
            data["watch"],
            "",
            "📖 گزارش تحلیلی فارسی:",
            FA_BASE + slug + "/",
            "",
            "🌐 English analysis:",
            EN_BASE + slug + "/",
            "",
            "🎙 متن اجرای ویدئوی فارسی:",
            FA_BASE + slug + "/full-transcript/",
            "",
            "✍️ نیما افشارنادری | IranSignal",
        ]
        text = "\n".join(parts) + "\n"
        if len(text) > 3900:
            raise SystemExit(f"Telegram message longer than 3900 characters: {slug}")
        target = out / (slug.replace("/", "--") + ".txt")
        target.write_text(text, encoding="utf-8")
        print(target.relative_to(ROOT), len(text), "chars")
if __name__ == "__main__":
    build()
