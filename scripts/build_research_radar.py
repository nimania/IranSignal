#!/usr/bin/env python3
"""Build traceable, non-speculative scheduled briefs from published IranSignal archives."""
from __future__ import annotations
import argparse
import json
import os
from datetime import date, datetime, timedelta
from html import escape
from pathlib import Path
from urllib.parse import quote
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
SITE_BASE = "/IranSignal"
NAMES = {"daily": "رادار روزانه", "weekly": "نبض هفته", "monthly": "نقشه ماهانه"}
WINDOWS = {"daily": 3, "weekly": 7, "monthly": 30}
TABS = ["daily", "weekly", "monthly"]
STYLE = """*{box-sizing:border-box}body{margin:0;background:#fff;color:#172333;font:16px/1.95 Tahoma,system-ui,sans-serif}
main,header .wrap{max-width:910px;margin:0 auto;padding:20px}header{border-bottom:1px solid #e5e7eb}
a{color:#245882;text-decoration:none}a:hover{text-decoration:underline}
h1{font-size:29px;line-height:1.5}h2{font-size:20px}p,li{overflow-wrap:anywhere}
.muted{color:#667485}.card{border:1px solid #e3e8ee;border-radius:12px;padding:16px;margin:15px 0}
.small{font-size:13px}.pill{font-size:12px;background:#f3f4f6;padding:3px 9px;border-radius:20px}
nav{display:flex;gap:15px;flex-wrap:wrap}input{width:100%;padding:12px;border:1px solid #aab3bf;border-radius:7px;font:inherit}
footer{border-top:1px solid #ddd;margin-top:35px;padding-top:12px;color:#667485;font-size:12px}
"""

def read_json(path, default):
    p = ROOT / path
    if not p.is_file():
        return default
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)

def write_json(path, obj):
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def write_html(path, html):
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(html, encoding="utf-8")

def page(title, body):
    nav = ('<nav><a href="/IranSignal/">آرشیو ایران سیگنال</a>'
           '<a href="/IranSignal/fa/radar/">گزارش‌های زمان‌بندی‌شده</a>'
           '<a href="/IranSignal/fa/research/">جست‌وجوی پژوهش‌ها</a></nav>')
    return ('<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>' + escape(title) + ' | ایران سیگنال</title><style>' + STYLE +
            '</style></head><body><header><div class="wrap">' + nav +
            '</div></header><main><h1>' + escape(title) + '</h1>' + body +
            '<footer>گزارش خودکار آرشیوی، نه راستی‌آزمایی مستقل و نه توصیه سیاسی. '
            'زمان اجرا ممکن است از برنامه زمان‌بندی عقب بیفتد.</footer></main></body></html>')

def validate_date(row):
    try:
        return date.fromisoformat(str(row["date"]))
    except (TypeError, ValueError, KeyError):
        return None

def valid_slug(slug):
    from re import fullmatch
    return bool(fullmatch(r"[0-9A-Za-z_./-]+", str(slug))) and ".." not in slug

def get_published():
    manifest = read_json("daily/manifest.json", [])
    editorial = read_json("telegram/editorial.json", {})
    result = []
    for entry in manifest:
        d = validate_date(entry)
        slug = entry.get("slug", "")
        if (entry.get("status") != "published" or not d or
                not valid_slug(slug)):
            continue
        info = editorial.get(slug, {})
        result.append({
            "date": d.isoformat(), "slug": slug,
            "title": info.get("title") or entry.get("title") or slug,
            "lead": info.get("lead") or entry.get("summary") or "",
            "url": SITE_BASE + "/fa/daily/" + quote(slug, safe="/-._") + "/",
            "status": "published_archive"
        })
    return sorted(result, key=lambda x: (x["date"], x["slug"]), reverse=True)

def create_brief(mode, as_of, published, knowledge):
    from_date = as_of - timedelta(days=WINDOWS[mode] - 1)
    hits = [r for r in published if from_date.isoformat() <= r["date"] <= as_of.isoformat()]
    signals = []
    for s in knowledge.get("signals", []):
        when = s.get("observed_at", "")
        if from_date.isoformat() <= when <= as_of.isoformat():
            signals.append({
                "id": s.get("id"), "title": s.get("title"),
                "status": s.get("status"), "domain": s.get("domain"),
                "source_report_slug": s.get("source_report_slug")
            })
    return {
        "schema_version": "1.0.0", "type": mode, "title": NAMES[mode] + " | " + as_of.isoformat(),
        "date": as_of.isoformat(), "period_start": from_date.isoformat(),
        "period_end": as_of.isoformat(), "timezone": "Asia/Tehran",
        "generation_method": "deterministic_archive_digest",
        "verification_notice": (
            "خلاصه خودکار گزارش‌های پیش‌تر منتشرشده؛ ادعاهای اصلی مستقلاً در این نوبت راستی‌آزمایی نشده‌اند. "
            "این گزارش کشف تازه، پیش‌بینی و تأیید روند نیست."
        ),
        "archive_report_count": len(hits), "archived_reports": hits,
        "candidate_signal_count": len(signals), "candidate_signals": signals,
        "signal_interpretation": "هیچ سیگنال جدیدی به‌صورت خودکار تأیید یا به روند ارتقا داده نمی‌شود.",
        "evidence_gap": ("" if hits else
            "در بازه مورد بررسی هیچ گزارش منتشرشده تازه‌ای در آرشیو ثبت نشده است. "
            "این موضوع به معنای رخ ندادن رویداد در جهان واقعی نیست."),
        "open_research_questions": [
            {"id": h.get("id"), "title": h.get("title"), "status": h.get("status")}
            for h in knowledge.get("hypotheses", []) if h.get("status") == "open_question"
        ][:12]
    }

def render_brief(r):
    items = []
    for e in r["archived_reports"]:
        items.append('<div class="card"><span class="pill">آرشیو منتشرشده · ' +
                     escape(e["date"]) + '</span><h2><a href="' +
                     escape(e["url"], quote=True) + '">' + escape(e["title"]) +
                     '</a></h2><p>' + escape(e["lead"]) + '</p></div>')
    questions = ''.join('<li>' + escape(q["title"]) + ' <span class="muted">(' +
                        escape(q["id"] or "") + ')</span></li>'
                        for q in r["open_research_questions"])
    candidates = ''.join('<li>' + escape(s["title"]) +
                         ' <span class="muted">— ' +
                         escape(s["status"] or "candidate") + '</span></li>'
                         for s in r["candidate_signals"])
    body = (
      '<p class="muted">بازه: ' + escape(r["period_start"]) + ' تا ' +
      escape(r["period_end"]) + ' | تعداد گزارش‌های آرشیوی: ' +
      str(r["archive_report_count"]) + '</p>'
      '<div class="card"><strong>ماهیت گزارش:</strong> ' +
      escape(r["verification_notice"]) + '</div>'
      '<h2>گزارش‌های مرتبط با بازه</h2>' +
      (''.join(items) or '<p class="muted">' + escape(r["evidence_gap"]) + '</p>') +
      '<h2>سیگنال‌های کاندید ثبت‌شده</h2>' +
      ('<ul>' + candidates + '</ul>' if candidates else
       '<p class="muted">سیگنال جدید تأییدشده‌ای در بانک ثبت نشده است.</p>') +
      '<p class="muted">' + escape(r["signal_interpretation"]) + '</p>'
      '<h2>پرسش‌های باز پژوهش</h2>' +
      ('<ul>' + questions + '</ul>' if questions else '<p>پرسش بازی ثبت نشده است.</p>') +
      '<p><a href="/IranSignal/fa/research/">جست‌وجوی پرونده‌ها و گزارش‌های دیگر</a></p>'
    )
    return page(r["title"], body)

def rebuild_reports():
    all_briefs = []
    for mode in TABS:
        root = ROOT / "research" / "reports" / mode
        values = []
        if root.is_dir():
            for path in root.glob("????-??-??.json"):
                try:
                    r = json.loads(path.read_text(encoding="utf-8"))
                    if r.get("type") == mode and r.get("date") == path.stem:
                        values.append(r)
                except (ValueError, OSError):
                    continue
        values.sort(key=lambda r: r["date"], reverse=True)
        for r in values:
            write_html("fa/radar/" + mode + "/" + r["date"] + "/index.html", render_brief(r))
        cards = ''.join('<div class="card"><a href="/IranSignal/fa/radar/' +
                        mode + '/' + escape(r["date"]) + '/">' +
                        escape(r["title"]) + '</a> <span class="muted small">· ' +
                        str(r["archive_report_count"]) + ' گزارش آرشیوی</span></div>'
                        for r in values)
        write_html("fa/radar/" + mode + "/index.html",
                   page(NAMES[mode], cards or '<p>هنوز گزارشی تولید نشده است.</p>'))
        for r in values:
            all_briefs.append({
                "id": mode + "-" + r["date"], "title": r["title"],
                "kind": "گزارش " + NAMES[mode], "date": r["date"],
                "status": "auto_archive_only",
                "url": SITE_BASE + "/fa/radar/" + mode + "/" + r["date"] + "/"
            })
    links = ''.join('<div class="card"><h2><a href="/IranSignal/fa/radar/' +
                    mode + '/">' + NAMES[mode] + '</a></h2>'
                    '<p>گزارش‌های موجود به ترتیب تاریخ، با ذکر میزان داده و عدم‌قطعیت</p></div>'
                    for mode in TABS)
    write_html("fa/radar/index.html",
               page("رادار ایران | گزارش‌های زمان‌بندی‌شده",
                    '<p>گزارش‌ها از آرشیو منتشرشده و بانک پژوهش ساخته می‌شوند؛ '
                    'در صورت نبود داده تازه، این موضوع صریحاً ذکر می‌شود.</p>' + links))
    return all_briefs

def build_search(published, knowledge, briefs):
    items = list(briefs)
    for a in published:
        items.append({"id": "archive-" + a["slug"], "title": a["title"],
                      "kind": "آرشیو گزارش", "date": a["date"],
                      "status": a["status"], "url": a["url"]})
    for field, kind in [("signals", "سیگنال"), ("hypotheses", "فرضیه"),
                        ("methods", "روش"), ("findings", "یافته")]:
        for obj in knowledge.get(field, []):
            items.append({
                "id": obj.get("id", ""), "title": obj.get("title", ""),
                "kind": kind, "date": obj.get("observed_at") or obj.get("last_reviewed") or "",
                "status": obj.get("status", ""), "url": "/IranSignal/fa/research/",
                "description": obj.get("description") or obj.get("definition") or "",
                "domain": obj.get("domain", "")
            })
    items.sort(key=lambda x: (x.get("date", ""), x.get("id", "")), reverse=True)
    write_json("fa/research/index.json",
               {"schema_version": "1.0.0", "generated_at": datetime.now(ZoneInfo("Asia/Tehran")).isoformat(),
                "items": items, "notice": "نمایه عمومی؛ پیش‌نویس محرمانه یا منابع تأییدنشده به‌عنوان واقعیت منتشر نشده‌اند."})
    js = """
const root=document.getElementById('results'), q=document.getElementById('q'), count=document.getElementById('count');
let items=[];
function render(){
 const phrase=q.value.trim().toLocaleLowerCase('fa');
 const selected=items.filter(i=>[i.title,i.kind,i.id,i.description,i.domain,i.date,i.status].join(' ').toLocaleLowerCase('fa').includes(phrase));
 count.textContent=selected.length+' مورد پیدا شد';
 root.replaceChildren();
 for(const item of selected.slice(0,180)){
  const card=document.createElement('article');card.className='card';
  const a=document.createElement('a');a.textContent=item.title;a.href=item.url;
  const meta=document.createElement('p');meta.className='muted small';
  meta.textContent=[item.kind,item.date,item.status,item.id].filter(Boolean).join(' · ');
  card.append(a,meta);root.append(card);
 }
}
fetch('/IranSignal/fa/research/index.json').then(r=>{if(!r.ok)throw Error(r.status);return r.json()})
 .then(x=>{items=x.items||[];render()}).catch(()=>{count.textContent='خطا در بارگذاری نمایه پژوهش'});
q.addEventListener('input',render);
"""
    body = ('<p>جست‌وجو در عنوان گزارش‌ها، شناسه‌ها، پرسش‌ها و روش‌ها. '
            'این موتور جست‌وجوی واژگانی است، نه پاسخ‌گوی هوشمند زبانی.</p>'
            '<label for="q">عبارت یا شناسه مورد نظر</label>'
            '<input id="q" type="search" placeholder="مثلاً هویت، گاز، IR-20261113-001">'
            '<p id="count" class="muted"></p><section id="results"></section>'
            '<script>' + js + '</script>')
    write_html("fa/research/index.html", page("مغز پژوهشی ایران سیگنال | جست‌وجو", body))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=TABS, default="daily")
    parser.add_argument("--date", help="YYYY-MM-DD date, for a reproducible backfill")
    args = parser.parse_args()
    today = date.fromisoformat(args.date) if args.date else datetime.now(ZoneInfo("Asia/Tehran")).date()
    published = get_published()
    knowledge = read_json("research/knowledge.json", {})
    r = create_brief(args.mode, today, published, knowledge)
    write_json("research/reports/" + args.mode + "/" + today.isoformat() + ".json", r)
    briefs = rebuild_reports()
    build_search(published, knowledge, briefs)
    print(json.dumps({"mode": args.mode, "date": today.isoformat(),
                      "archive_reports_in_window": r["archive_report_count"],
                      "indexed_items": len(briefs) + len(published)}, ensure_ascii=False))

if __name__ == "__main__":
    main()
