#!/usr/bin/env python3
"""Discover attributable news leads from configured RSS feeds. Never auto-score."""
import datetime as dt
import hashlib
import json
import pathlib
import urllib.request
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "config/source-registry.json"
OUT = ROOT / "data/news/candidates.json"
KEYWORDS = ("iran", "iranian", "tehran", "hormuz", "israel", "middle east",
            "nuclear", "sanction", "persian gulf", "hezbollah")

def value(item, name):
    element = item.find(name)
    return "".join(element.itertext()).strip() if element is not None else ""

def harvest(source):
    request = urllib.request.Request(source["endpoint"], headers={
        "User-Agent": "IranSignal-EvidenceResearch/1.0", "Accept": "application/rss+xml, application/xml, text/xml"})
    with urllib.request.urlopen(request, timeout=20) as res:
        payload = res.read(2_000_001)
        if len(payload) > 2_000_000:
            raise ValueError("RSS feed exceeded 2 MB")
    tree = ET.fromstring(payload)
    for item in tree.findall(".//item"):
        title, link = value(item, "title"), value(item, "link")
        published = value(item, "pubDate")
        if not title or not link.startswith(("https://", "http://")):
            continue
        if not any(word in (title + " " + value(item, "description")).lower() for word in KEYWORDS):
            continue
        identifier = hashlib.sha256((source["id"] + "|" + link.split("#")[0]).encode()).hexdigest()[:20]
        yield {"id": identifier, "source_id": source["id"], "title": title,
               "url": link, "published": published, "status": "unverified_candidate",
               "score_effect": None}

def main():
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    old = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else []
    combined = {x["id"]: x for x in old}
    n = 0
    for source in registry["news_sources"]:
        if not (source.get("enabled") and source.get("access") == "official_feed"):
            continue
        try:
            records = list(harvest(source))
        except Exception as exc:
            print(f"Feed {source['id']} unavailable: {exc}")
            continue
        for item in records:
            if item["id"] not in combined:
                combined[item["id"]] = item
                n += 1
        print(f"{source['id']}: {len(records)} matching candidates")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    output = sorted(combined.values(), key=lambda x: x["id"])[:3000]
    OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{n} new candidates; {len(output)} retained. No scenario scores changed.")

if __name__ == "__main__":
    main()
