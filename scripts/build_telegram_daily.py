"""Generate a concise Persian Telegram edition for every published IranSignal daily report.
Run: python3 scripts/build_telegram_daily.py
Requires each Persian article to include a matching entry in telegram/editorial.json.
No credentials, network requests, or automatic Telegram posting.
"""
from __future__ import annotations
import json
import re
from html import escape
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
    valid_filenames = {r["slug"].replace("/", "--") + ".txt" for r in published}
    for old in out.glob("*.txt"):
        if old.name not in valid_filenames:
            old.unlink()
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
        fa_html = fa_article.read_text(encoding="utf-8")
        en_html = en_article.read_text(encoding="utf-8")
        if '<html lang="fa"' not in fa_html or '<html lang="en"' not in en_html:
            raise SystemExit(f"Incorrect language declaration for {slug}")
        for edition, content in (("Persian", fa_html), ("English", en_html)):
            if 'id="iran-signal-data-snapshot"' not in content or len(re.findall(r"<table\b", content, re.I)) < 2:
                raise SystemExit(f"{edition} scenario and market tables missing for {slug}")
        transcript_html = transcript.read_text(encoding="utf-8")
        if '<html lang="fa"' not in transcript_html:
            raise SystemExit(f"Persian narration language declaration incorrect for {slug}")
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

    cards = []
    for report in sorted(published, key=lambda r: r["date"], reverse=True):
        slug = report["slug"]
        data = editorial[slug]
        filename = slug.replace("/", "--") + ".txt"
        cards.append(
            '<article><small>' + escape(data["date_fa"]) + ' · ' + escape(report["date"]) + '</small>'
            '<h2><a href="./' + escape(filename, quote=True) + '">' + escape(data["title"]) + '</a></h2>'
            '<p>' + escape(data["lead"]) + '</p>'
            '<p><a href="/IranSignal/fa/daily/' + escape(slug, quote=True) + '/">گزارش فارسی</a> · '
            '<a href="/IranSignal/daily/' + escape(slug, quote=True) + '/">English report</a> · '
            '<a href="/IranSignal/fa/daily/' + escape(slug, quote=True) + '/full-transcript/">متن اجرا</a></p></article>'
        )
    index_html = (
        '<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>نسخه‌های آمادهٔ تلگرام | ایران سیگنال</title>'
        '<meta name="description" content="آرشیو خلاصه‌های روزانهٔ آمادهٔ انتشار در تلگرام، همراه با لینک گزارش فارسی، انگلیسی و متن اجرا.">'
        '<style>body{margin:0;background:#f5f7fa;color:#182838;font:17px/1.9 Tahoma,system-ui,sans-serif}'
        'main{max-width:850px;margin:auto;padding:30px 20px}article{background:white;border:1px solid #dce4ed;'
        'border-radius:12px;padding:20px;margin:16px 0}a{color:#176fa0}small{color:#64748b}</style></head>'
        '<body><main><p><a href="/IranSignal/fa/daily/">بازگشت به آرشیو گزارش‌ها</a></p>'
        '<h1>نسخه‌های آمادهٔ تلگرام</h1><p>برای هر روز یک متن مستقل با لینک به سه نسخهٔ گزارش تهیه شده است.</p>'
        + ''.join(cards) + '</main></body></html>'
    )
    (out / "index.html").write_text(index_html, encoding="utf-8")
if __name__ == "__main__":
    build()
