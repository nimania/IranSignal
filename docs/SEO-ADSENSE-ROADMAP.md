# IranSignal: English-first site architecture

**Canonical deployment:** https://nimania.github.io/IranSignal/

## URL strategy

- `/` — English homepage / scenario radar.
- `/daily/` — English daily archive; `/daily/YYYY-MM-DD/slug/` for articles.
- `/weekly/` — English weekly archive, initially empty.
- `/fa/` — Persian landing page; `/fa/daily/` and `/fa/weekly/` are separate Persian archives.
- `/fa/daily/YYYY-MM-DD/slug/` — Persian counterpart.
- `/about/`, `/methodology/`, `/editorial-policy/`, `/contact/`, `/privacy/`, `/terms/` — editorial trust and basic legal information.
- `/sitemap.xml` and `/robots.txt` — generated at deploy time.
- Never redirect English visitors automatically to Persian. Language switchers are explicit.

## Deployment and SEO

GitHub Actions deploys static HTML and runs `python3 scripts/build_seo_site.py` against `_site/` before Pages publication. The script adds a unique absolute canonical, language alternatives only for real matching translations, social preview metadata and WebPage/NewsArticle JSON-LD. It also generates an XML sitemap and robots.txt. No new runtime dependencies, tracking pixels, cookie banners, AdSense scripts, or fake publisher IDs.

To test locally:

```bash
rm -rf _site
mkdir -p _site
cp index.html _site/index.html
cp -a daily fa _site/
touch _site/.nojekyll
python3 scripts/build_seo_site.py
```

After deployment: open /sitemap.xml and /robots.txt, verify bilingual article URLs and HTML source, then submit the sitemap in Google Search Console. A sitemap or canonical is not a promise of indexing.

## Editorial operations

Publish original, carefully sourced English analysis, not English UI around predominantly Persian body text. Human-review the English prose and citation claims. Every article should have a descriptive title and summary, a visible author and profile, publication date, clearly differentiated reporting and analysis, sources and corrections when appropriate. Create actual weekly content before filling its archive; do not publish thin or synthetic weekly articles just to populate an empty page.

Ensure the English and Persian counterparts are substantively equivalent before declaring them `hreflang` alternatives; translations need not be word-for-word.

## AdSense readiness (not approval)

Site structure provides consistent navigation, a real author, about/methodology/editorial and contact pages, a privacy disclosure, and a place for unique original articles. These are prerequisites for a credible publishing site but **do not guarantee AdSense approval**. Google determines eligibility under its current program policies. In particular, assess original content value, media rights, dangerous/sensitive content and ad placement policies.

Before applying:
1. Register a verified domain you control, preferably `iransignal.com` (only if available and obtained), then update `BASE`, all canonical links, sitemap and Pages settings together. A custom domain is **not** configured by this change; currently every generated URL points to GitHub Pages.
2. Confirm contact/legal privacy disclosures reflect actual operations. Add a private contact mechanism, cookie/consent management where legally required, and clear sponsorship/corrections processes.
3. Review YouTube embeds and third-party privacy behavior, especially for EEA/UK users. `youtube-nocookie.com` alone is not a universal consent solution.
4. Only after approval insert the real AdSense account code; publish `ads.txt` exactly as issued by Google and do not fabricate it now.
5. Validate in Google Search Console: URL Inspection, coverage, sitemap status, Core Web Vitals, mobile rendering and structured-data testing.

## Technical limits

Currently, policy pages are generated from the source generator during deployment. Edit `scripts/build_seo_site.py` to change them. More articles should be added as static HTML files in `daily/` and `fa/daily/`; sitemap discovers them automatically. The current bilingual URL mapping explicitly pairs only known content and should later be moved to a content manifest to avoid manual mapping as the archive grows.

For 2026-10-24, the original article, Persian adaptation, transcript and unlisted YouTube embed remain present. No need to re-upload the video.
