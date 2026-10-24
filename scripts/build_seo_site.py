#!/usr/bin/env python3
"""Prepare a crawlable, English-first bilingual static IranSignal website.

Run after copying repository HTML to _site/. No third-party dependencies.
All URLs are explicit, public, and stable; no language-based redirects.
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from html import escape
from xml.etree.ElementTree import Element, SubElement, ElementTree, register_namespace

BASE = "https://nimania.github.io/IranSignal/"
AUTHOR = "Nima Afshar Naderi"
AUTHOR_URL = "https://pendar.io/@nima-afshar-naderi"
REPORT = "daily/2026-10-24/military-threat-and-diplomacy/"
FA_REPORT = "fa/" + REPORT
PAIRS = {
    "": "fa/",
    "daily/": "fa/daily/",
    REPORT: FA_REPORT,
    "weekly/": "fa/weekly/",
}
SITE_NAME = "IranSignal"
LEGAL = {
 "about/": ("About IranSignal", "About this independent Iran scenario analysis project", """
<p>IranSignal publishes English-language research and scenario analysis about Iran, with additional Persian editions. Its focus is observable evidence, rival interpretations and testable signals, not predictions presented as facts.</p>
<p>Reports are written by <a href="https://pendar.io/@nima-afshar-naderi">Nima Afshar Naderi</a>. English is the default site language, and Persian reporting is available in the <a href="../fa/">Persian edition</a>.</p>
<p>IranSignal is an editorial research project, not a government agency or financial advisory service. Opinions and scenario assessments are identified as analysis.</p>"""),
 "methodology/": ("Methodology", "How IranSignal distinguishes evidence, scenarios and uncertainty", """
<p>We distinguish verified observations, attributed claims, interpretations and forecasts. A reported statement is not automatically evidence of an operational decision.</p>
<p>Scenario momentum scores describe the directional weight of collected signals. They are not calibrated probabilities and must never be read as percentages.</p>
<p>Sources are linked wherever possible, and several reports repeating one original interview are treated as one underlying source. Alternative explanations and signals that could falsify the working assessment should be stated explicitly.</p>
<p>Dates, publication times and evidence windows matter. Corrections should be reflected on the affected article, with a clear explanation of material changes.</p>"""),
 "editorial-policy/": ("Editorial Policy", "Editorial standards, attribution and corrections at IranSignal", """
<p>Our editorial priority is independently attributable, original analysis. We separate news reporting from commentary and disclose significant uncertainty. We do not invent quotations, dates, source confirmations, probabilities or market measurements.</p>
<p>Material factual changes should be corrected promptly, dated and explained. Source attribution is provided on article pages; any conflicts of interest or sponsorship should be identified to readers.</p>
<p>Automated tools may support research or formatting, but final factual responsibility remains with the named editor. We do not publish unsupported claims simply to satisfy an update schedule.</p>
<p>For corrections or questions use our <a href="../contact/">contact page</a>.</p>"""),
 "contact/": ("Contact", "Editorial feedback and correction requests for IranSignal", """
<p>For editorial corrections, source suggestions, accessibility issues or general questions, contact the publisher through the linked public profiles below.</p>
<p><a href="https://pendar.io/@nima-afshar-naderi">Nima Afshar Naderi — author profile</a></p>
<p><a href="https://github.com/nimania/IranSignal/issues">IranSignal public issue tracker</a> (public messages only; do not post sensitive personal information).</p>
<p>This project does not currently offer a private contact form or dedicated business email. A private contact channel should be added before accepting sensitive inquiries.</p>"""),
 "privacy/": ("Privacy Policy", "Privacy and third-party services used by IranSignal", """
<p><strong>Effective date: 24 October 2026.</strong> IranSignal is a static website hosted on GitHub Pages. We do not currently operate an account registration system, private comment database or an advertising integration.</p>
<p>GitHub Pages and your browser or network providers may process technical request data under their own terms. Article pages can embed YouTube videos; loading or interacting with those embeds may involve Google/YouTube requests, cookies and related data processing under their policies. Embedded media uses youtube-nocookie.com where supported; that does not guarantee zero data collection.</p>
<p>We do not currently claim to use Google Analytics or AdSense. If analytics, personalized advertising or consent management is introduced, this policy and any required consent controls must be updated before launch.</p>
<p>For privacy inquiries, see our <a href="../contact/">contact page</a>. This page describes the codebase as currently configured, not the practices of external sites linked from articles.</p>"""),
 "terms/": ("Terms of Use", "Use and attribution terms for IranSignal content", """
<p>IranSignal provides commentary and research for general information. Scenario analysis is inherently uncertain and is not investment, legal, military or personal safety advice.</p>
<p>Articles may quote or summarize third-party material with attribution and links. External websites and YouTube are operated by their respective providers.</p>
<p>Do not republish complete articles without permission from the rights holder. Short attributed quotations and links are welcome where permitted by applicable law.</p>"""),
}
def url(path): return BASE + path
def static_page(title,desc,body):
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>'+escape(title)+' | IranSignal</title></head>'
            '<body style="font:18px/1.8 system-ui,sans-serif;max-width:850px;margin:30px auto;padding:0 20px;color:#202d3d">'
            '<nav><a href="'+BASE+'">IranSignal</a> · <a href="'+BASE+'daily/">Daily</a> · '
            '<a href="'+BASE+'weekly/">Weekly</a> · <a href="'+BASE+'fa/" lang="fa">فارسی</a></nav>'
            '<h1>'+escape(title)+'</h1>'+body+'</body></html>')
def tidy_head(html):
    if re.search(r'<head\b',html,re.I): return html
    # Some legacy pages put title/meta directly under <html>. Move metadata into a real head.
    m=re.search(r'<html\b[^>]*>',html,re.I)
    if not m: raise ValueError("Missing html tag")
    rest=html[m.end():]
    tags=""
    while True:
        t=re.match(r'\s*(?:<meta\b[^>]*>|<title\b[^>]*>.*?</title>|<link\b[^>]*>)',rest,re.I|re.S)
        if not t: break
        tags+=t.group(0)
        rest=rest[t.end():]
    return html[:m.end()]+"<head>"+tags+"</head>"+rest
def strip_tag(html,pattern):
    return re.sub(pattern,"",html,flags=re.I|re.S)
def enhance(file,relative):
    html=tidy_head(file.read_text(encoding="utf-8"))
    lang="fa" if relative.startswith("fa/") else "en"
    m=re.search(r'<title[^>]*>(.*?)</title>',html,re.I|re.S)
    title=re.sub(r'<[^>]+>',"",m.group(1)).strip() if m else "IranSignal"
    d=re.search(r'<meta\b[^>]*name=["\']description["\'][^>]*>',html,re.I)
    desc=re.search(r'content=["\'](.*?)["\']',d.group(0),re.I).group(1) if d and re.search(r'content=["\'](.*?)["\']',d.group(0),re.I) else title
    desc=desc[:250]
    for marker in ("<!-- SEO:START -->","<!-- SEO:END -->"):
        assert marker not in html,"Unexpected SEO marker collision"
    canonical=url(relative)
    alternates=""
    other=PAIRS.get(relative)
    if other is None:
        other=next((en for en,fa in PAIRS.items() if fa==relative),None)
    if other is not None:
        en=relative if lang=="en" else other
        fa=relative if lang=="fa" else other
        alternates=(f'<link rel="alternate" hreflang="en" href="{url(en)}">'
                    f'<link rel="alternate" hreflang="fa" href="{url(fa)}">')
    schema={"@context":"https://schema.org","@type":"WebPage","name":title,
            "url":canonical,"inLanguage":lang,"isPartOf":{"@type":"WebSite","name":"IranSignal","url":BASE}}
    if relative in (REPORT,FA_REPORT):
        schema={"@context":"https://schema.org","@type":"NewsArticle","headline":title,
                "inLanguage":lang,"mainEntityOfPage":canonical,"datePublished":"2026-10-24",
                "author":{"@type":"Person","name":AUTHOR,"url":AUTHOR_URL},
                "publisher":{"@type":"Organization","name":"IranSignal","url":BASE}}
    extra=('<!-- SEO:START --><link rel="canonical" href="'+canonical+'">'+alternates+
           '<meta property="og:type" content="article">' if relative in (REPORT,FA_REPORT) else
           '<!-- SEO:START --><link rel="canonical" href="'+canonical+'">'+alternates+
           '<meta property="og:type" content="website">')
    extra+='<link rel="stylesheet" href="'+BASE+'assets/editorial.css">'
    extra+=('<meta name="theme-color" content="#12253b">'
            '<meta property="og:site_name" content="IranSignal">'
            '<meta property="og:title" content="'+escape(title,quote=True)+'">'
            '<meta property="og:description" content="'+escape(desc,quote=True)+'">'
            '<meta property="og:url" content="'+canonical+'">'
            '<meta property="og:locale" content="'+("fa_IR" if lang=="fa" else "en_US")+'">'
            '<meta name="twitter:card" content="summary">'
            '<meta name="robots" content="index,follow,max-image-preview:large">'
            '<script type="application/ld+json">'+json.dumps(schema,ensure_ascii=False).replace("</","<\\/")+'</script>'
            '<!-- SEO:END -->')
    html=html.replace("</head>",extra+"</head>",1)
    navlinks=[("Home",""),("Daily Briefs","daily/"),("Weekly Reviews","weekly/"),
              ("Methodology","methodology/"),("About","about/")]
    links=''.join('<a href="'+url(target)+'">'+label+'</a>' for label,target in navlinks)
    links+='<a href="'+url("fa/")+'" lang="fa" dir="rtl">فارسی</a>'
    masthead=('<header class="is-masthead"><div class="is-masthead-inner">'
             '<div><a class="is-logo" href="'+BASE+'">IRAN<span>SIGNAL</span></a>'
             '<div class="is-tagline">Iran Scenario Intelligence · Independent Analysis</div></div>'
             '<div class="is-tagline">Evidence · Scenarios · Perspective</div></div>'
             '<nav class="is-navbar" aria-label="Primary navigation"><div class="is-navbar-inner">'+links+'</div></nav></header>')
    # Pages predate a shared semantic body: guarantee a real body and header.
    if not re.search(r'<body\\b',html,re.I):
        html=html.replace('</head>','</head><body>',1)
        html=html.replace('</html>','</body></html>',1)
    html=re.sub(r'(<body\\b[^>]*>)',lambda m:m.group(1)+masthead,html,count=1,flags=re.I)
    footer=('<footer class="is-trust-footer" style="border-top:1px solid #ccd5dd;margin:40px auto 0;padding:20px 0;font:14px/1.8 system-ui,sans-serif">'
            '<a href="'+BASE+'">Home</a> · <a href="'+BASE+'daily/">Daily</a> · <a href="'+BASE+'weekly/">Weekly</a> · '
            '<a href="'+BASE+'fa/" lang="fa">فارسی</a> · <a href="'+BASE+'about/">About</a> · '
            '<a href="'+BASE+'methodology/">Methodology</a> · <a href="'+BASE+'editorial-policy/">Editorial Policy</a> · '
            '<a href="'+BASE+'privacy/">Privacy</a> · <a href="'+BASE+'contact/">Contact</a> · '
            '<a href="'+BASE+'terms/">Terms</a></footer>')
    if "</body>" in html: html=html.replace("</body>",footer+"</body>",1)
    else: html=html.replace("</html>",footer+"</html>",1)
    file.write_text(html,encoding="utf-8")
def main():
    root=Path("_site")
    if not (root/"index.html").is_file(): raise SystemExit("_site/index.html missing")
    for path,(title,desc,body) in LEGAL.items():
        dest=root/path/"index.html"
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(static_page(title,desc,body),encoding="utf-8")
    # Assets are deployed alongside HTML and never loaded from a third-party CDN.
    if not (root/"assets/editorial.css").is_file():
        raise SystemExit("Missing shared editorial stylesheet")
    for path,title,description,body,language in [
        ("weekly/","Weekly Reviews","Weekly scenario reviews and evidence changes","Our first verified weekly review is being prepared.", "en"),
        ("fa/weekly/","گزارش‌های هفتگی","گزارش‌های هفتگی رادار ایران","اولین گزارش هفتگی پس از تکمیل بررسی‌ها منتشر خواهد شد.", "fa"),
    ]:
        dest=root/path/"index.html"
        dest.parent.mkdir(parents=True,exist_ok=True)
        if language=="fa":
            dest.write_text('<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8"><title>'+title+' | ایران سیگنال</title><meta name="description" content="'+description+'"></head><body><main style="max-width:750px;margin:auto;font:18px/2 system-ui"><a href="'+BASE+'fa/">ایران سیگنال</a><h1>'+title+'</h1><p>'+body+'</p></main></body></html>',encoding="utf-8")
        else: dest.write_text(static_page(title,description,'<p>'+body+'</p>'),encoding="utf-8")
    htmls=sorted(root.rglob("index.html"))
    paths=[str(p.parent.relative_to(root)).replace("\\","/") for p in htmls]
    paths=[("" if x=="." else x+"/") for x in paths]
    for path,file in zip(paths,htmls):
        enhance(file,path)
    (root/"robots.txt").write_text("User-agent: *\nAllow: /\nSitemap: "+url("sitemap.xml")+"\n",encoding="utf-8")
    register_namespace("","http://www.sitemaps.org/schemas/sitemap/0.9")
    register_namespace("xhtml","http://www.w3.org/1999/xhtml")
    ns="http://www.sitemaps.org/schemas/sitemap/0.9"
    xn="http://www.w3.org/1999/xhtml"
    rootxml=Element("{"+ns+"}urlset")
    for path in paths:
        e=SubElement(rootxml,"{"+ns+"}url")
        SubElement(e,"{"+ns+"}loc").text=url(path)
        other=PAIRS.get(path)
        if other is None: other=next((en for en,fa in PAIRS.items() if fa==path),None)
        if other is not None:
            en=path if not path.startswith("fa/") else other
            fa=path if path.startswith("fa/") else other
            for lang,target in [("en",en),("fa",fa)]:
                SubElement(e,"{"+xn+"}link",{"rel":"alternate","hreflang":lang,"href":url(target)})
    ElementTree(rootxml).write(root/"sitemap.xml",encoding="utf-8",xml_declaration=True)
    for path in ("","daily/","fa/","fa/daily/",REPORT,FA_REPORT,
                 "about/","editorial-policy/","privacy/","contact/","weekly/","fa/weekly/"):
        html=(root/path/"index.html").read_text(encoding="utf-8")
        assert '<link rel="canonical" href="'+url(path)+'">' in html,(path,"canonical")
        assert "application/ld+json" in html,(path,"schema")
    assert (root/"sitemap.xml").is_file() and (root/"robots.txt").is_file()
    print("SEO build OK:",len(paths),"crawlable pages; English-first navigation and Persian alternates.")
if __name__=="__main__": main()
