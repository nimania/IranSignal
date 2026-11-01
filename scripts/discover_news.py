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


from html.parser import HTMLParser
import re

IRAN_TERMS = ("ایران", "ایرانی", "تهران", "هرمز", "نطنز", "فردو", "بوشهر",
              "سپاه", "برجام", "خلیج فارس", "جمهوری اسلامی", "مرز ایران")

class TelegramPreviewParser(HTMLParser):
    """Parse public channel previews; one post's text never bleeds into another."""
    def __init__(self, handle):
        super().__init__(convert_charrefs=True)
        self.handle = handle
        self.posts = []
        self.current = None
        self.depth = 0
        self.text_depth = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        post = attrs.get("data-post", "")
        if self.current is None and tag == "div" and re.fullmatch(
                re.escape(self.handle) + r"/[1-9]\d*", post):
            self.current = {"post": post, "text": [], "published": ""}
            self.depth = 1
            return
        if self.current is None:
            return
        if tag == "div":
            self.depth += 1
            if "tgme_widget_message_text" in attrs.get("class", "").split():
                self.text_depth = self.depth
        if self.text_depth and tag == "br":
            self.current["text"].append("\n")
        if self.text_depth and tag == "img" and attrs.get("alt"):
            self.current["text"].append(attrs["alt"])
        if tag == "time" and attrs.get("datetime"):
            self.current["published"] = attrs["datetime"]

    def handle_endtag(self, tag):
        if self.current is None or tag != "div":
            return
        if self.text_depth == self.depth:
            self.text_depth = 0
        self.depth -= 1
        if self.depth == 0:
            self.posts.append(self.current)
            self.current = None

    def handle_data(self, value):
        if self.current is not None and self.text_depth:
            self.current["text"].append(value)


def harvest_telegram(source, *, payload=None):
    """Keep source leads only; Telegram posts are never confirmation."""
    handle = source["handle"]
    if payload is None:
        request = urllib.request.Request(source["endpoint"], headers={
            "User-Agent": "IranSignal-EvidenceResearch/1.0",
            "Accept": "text/html"})
        with urllib.request.urlopen(request, timeout=20) as res:
            payload = res.read(2_000_001)
            if len(payload) > 2_000_000:
                raise ValueError("Telegram preview exceeded 2 MB")
    parser = TelegramPreviewParser(handle)
    parser.feed(payload.decode("utf-8", errors="replace") if isinstance(payload, bytes) else payload)
    for post in parser.posts:
        body = " ".join("".join(post["text"]).split())
        if len(body) < 55 or not any(term in body for term in IRAN_TERMS):
            continue
        if not post["published"]:
            continue
        url = "https://t.me/" + post["post"]
        first = body.split("؛", 1)[0].split(":", 1)[0]
        title = (first[:180].rsplit(" ", 1)[0] if len(first) > 180 else first) or body[:180]
        identifier = hashlib.sha256((source["id"] + "|" + url).encode()).hexdigest()[:20]
        yield {"id": identifier, "source_id": source["id"], "title": title,
               "url": url, "published": post["published"],
               "excerpt": body[:800], "source_kind": "public_telegram_preview",
               "status": "unverified_candidate",
               "verification": "requires_independent_primary_or_reputable_source",
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
    for source in registry.get("telegram_sources", []):
        if not (source.get("enabled") and source.get("access") == "public_preview"):
            continue
        try:
            records = list(harvest_telegram(source))
        except Exception as exc:
            print(f"Telegram source {source['id']} unavailable: {exc}")
            continue
        for item in records:
            if item["id"] not in combined:
                combined[item["id"]] = item
                n += 1
        print(f"{source['id']}: {len(records)} Iran-related unverified Telegram leads")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    output = sorted(combined.values(), key=lambda x: x["id"])[:3000]
    OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{n} new candidates; {len(output)} retained. No scenario scores changed.")

if __name__ == "__main__":
    main()
