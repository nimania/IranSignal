#!/usr/bin/env python3
"""Build a minimal Persian-only IranSignal archive for GitHub Pages."""
from __future__ import annotations
import json
import re
from pathlib import Path
from html import escape
from xml.etree.ElementTree import Element, SubElement, ElementTree, register_namespace

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "_site"
BASE = "https://nimania.github.io/IranSignal/"
PREFIX = "/IranSignal"

def clean_persian_pages():
    fa_root = SITE / "fa"
    for page in fa_root.rglob("index.html"):
        html = page.read_text(encoding="utf-8")
        # Remove links to the retired English edition, but preserve external source links.
        html = re.sub(
            r'<a\b(?=[^>]*href=["\'][^"\']*(?:https://nimania\.github\.io/IranSignal|/IranSignal)/daily/)[^>]*>.*?</a>',
            "", html, flags=re.I | re.S
        )
        html = re.sub(r'<link\b(?=[^>]*hreflang=["\']en["\'])[^>]*>', "", html, flags=re.I)
        html = re.sub(r'<script\b[^>]*iran-signal-fa-dashboard\.js[^>]*>.*?</script\s*>', "", html, flags=re.I | re.S)
        html = re.sub(r'<link\b[^>]*iran-signal-fa-dashboard\.css[^>]*>', "", html, flags=re.I)
        html = re.sub(r'<script\b[^>]*src=["\'][^"\']*iran-signal-fa-dashboard\.js[^"\']*["\'][^>]*>\s*</script\s*>', "", html, flags=re.I)
        page.write_text(html, encoding="utf-8")

def archive_page(title, description, records, editorial, canonical):
    cards = []
    for report in records:
        slug = report["slug"]
        item = editorial.get(slug, {})
        date_fa = escape(item.get("date_fa") or report["date"])
        heading = escape(item.get("title") or report.get("title") or report["date"])
        lead = escape(item.get("lead") or report.get("summary") or "")
        report_url = f"{PREFIX}/fa/daily/{slug}/"
        transcript_url = report_url + "full-transcript/"
        cards.append(
            '<article class="entry">'
            f'<div class="date">{date_fa} <span>· {escape(report["date"])}</span></div>'
            f'<h2><a href="{report_url}">{heading}</a></h2>'
            f'<p>{lead}</p>'
            f'<div class="links"><a href="{report_url}">خواندن گزارش</a>'
            f'<a href="{transcript_url}">متن اجرای ویدئو</a></div>'
            '</article>'
        )
    return f'''<!doctype html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="{escape(description, quote=True)}">
<meta name="theme-color" content="#ffffff">
<link rel="canonical" href="{canonical}">
<title>{escape(title)} | ایران سیگنال</title>
<style>
*{{box-sizing:border-box}}
body{{margin:0;background:#fff;color:#202a35;font:17px/1.9 Tahoma,"Vazirmatn",system-ui,sans-serif}}
header{{border-bottom:1px solid #e5e7eb}}
.wrap{{max-width:820px;margin:auto;padding:18px 20px}}
.brand{{font-size:18px;font-weight:700;color:#202a35;text-decoration:none}}
h1{{font-size:30px;line-height:1.5;margin:28px 0 4px}}
.intro{{color:#596574;margin:0 0 24px}}
.entry{{padding:18px 0;border-bottom:1px solid #e5e7eb}}
.date{{font-size:13px;color:#697586}}
.date span{{color:#9aa3ad}}
h2{{font-size:20px;line-height:1.6;margin:3px 0 4px}}
h2 a{{color:#173b5e;text-decoration:none}}
h2 a:hover,.links a:hover{{text-decoration:underline}}
.entry p{{margin:4px 0 8px;color:#46515e;font-size:15px}}
.links{{display:flex;gap:18px;flex-wrap:wrap;font-size:14px}}
.links a,.archive-link{{color:#1769aa;text-decoration:none}}
footer{{padding:20px 0;color:#77818d;font-size:13px}}
@media(max-width:560px){{h1{{font-size:25px}}h2{{font-size:18px}}.wrap{{padding:14px 16px}}}}
</style>
</head>
<body>
<header><div class="wrap"><a class="brand" href="{PREFIX}/">ایران سیگنال</a></div></header>
<main class="wrap">
<h1>{escape(title)}</h1>
<p class="intro">{escape(description)} · آرشیو به ترتیب تازه‌ترین گزارش</p>
<p><a class="archive-link" href="{PREFIX}/telegram/daily/">نسخه‌های آمادهٔ انتشار در تلگرام</a></p>
{''.join(cards)}
<footer>ایران سیگنال · گزارش‌ها، منابع و متن‌های اجرای ویدئو</footer>
</main>
</body>
</html>'''

def main():
    manifest = json.loads((ROOT / "daily/manifest.json").read_text(encoding="utf-8"))
    editorial = json.loads((ROOT / "telegram/editorial.json").read_text(encoding="utf-8"))
    records = sorted(
        (r for r in manifest if r.get("status") == "published"),
        key=lambda r: r["date"], reverse=True
    )
    if not records:
        raise SystemExit("No published Persian reports found")
    for r in records:
        slug = r["slug"]
        if not (SITE / "fa/daily" / slug / "index.html").is_file():
            raise SystemExit(f"Persian report missing: {slug}")
        if not (SITE / "fa/daily" / slug / "full-transcript/index.html").is_file():
            raise SystemExit(f"Persian narration missing: {slug}")
    clean_persian_pages()
    description = "آرشیو سادهٔ گزارش‌های تحلیلی روزانهٔ ایران سیگنال، همراه با متن کامل اجرای ویدئو."
    for path, title in [
        (SITE / "index.html", "آرشیو گزارش‌های ایران سیگنال"),
        (SITE / "fa/index.html", "آرشیو گزارش‌های ایران سیگنال"),
        (SITE / "fa/daily/index.html", "گزارش‌های روزانهٔ ایران سیگنال"),
    ]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(archive_page(title, description, records, editorial, BASE + ("fa/daily/" if "daily" in str(path) else "")), encoding="utf-8")
    # A Persian-only sitemap: no English article pages or language alternates.
    pages = [BASE, BASE + "fa/", BASE + "fa/daily/", BASE + "telegram/daily/"]
    for r in records:
        base = BASE + "fa/daily/" + r["slug"].strip("/") + "/"
        pages.extend([base, base + "full-transcript/"])
    register_namespace("", "http://www.sitemaps.org/schemas/sitemap/0.9")
    ns = "http://www.sitemaps.org/schemas/sitemap/0.9"
    urlset = Element("{" + ns + "}urlset")
    for address in pages:
        node = SubElement(urlset, "{" + ns + "}url")
        SubElement(node, "{" + ns + "}loc").text = address
    ElementTree(urlset).write(SITE / "sitemap.xml", encoding="utf-8", xml_declaration=True)
    (SITE / "robots.txt").write_text(
        "User-agent: *\nAllow: /\nSitemap: " + BASE + "sitemap.xml\n",
        encoding="utf-8"
    )
    print(f"Persian archive generated: {len(records)} reports, {len(records)} narration scripts, no English edition.")

if __name__ == "__main__":
    main()
