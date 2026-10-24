"""Generate a concise Persian Telegram edition for every published IranSignal daily report.
Run: python3 scripts/build_telegram_daily.py
Requires each Persian article to include a matching entry in telegram/editorial.json.
No credentials, network requests, or automatic Telegram posting.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://nimania.github.io/IranSignal/fa/daily/"

def build():
    manifest = json.loads((ROOT / "daily/manifest.json").read_text(encoding="utf-8"))
    editorial = json.loads((ROOT / "telegram/editorial.json").read_text(encoding="utf-8"))
    out = ROOT / "telegram/daily"
    out.mkdir(parents=True, exist_ok=True)
    published = [r for r in manifest if r.get("status") == "published"]
    for report in published:
        slug = report["slug"]
        data = editorial.get(slug)
        if not data:
            raise SystemExit(f"Missing approved Persian Telegram summary for {slug}")
        for field in ("title", "lead", "analysis", "watch"):
            if not isinstance(data.get(field), str) or not data[field].strip():
                raise SystemExit(f"Missing {field} for {slug}")
        if not (ROOT / "fa/daily" / slug / "index.html").is_file():
            raise SystemExit(f"Persian article missing for {slug}")
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
            "📖 گزارش کامل، منابع و ویدئو:",
            BASE + slug + "/",
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
