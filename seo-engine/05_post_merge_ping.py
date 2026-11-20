"""
05_post_merge_ping.py
Runs automatically after merging a new/updated landing page to main:
1. Submits updated URLs to IndexNow (Bing / ChatGPT Search / Yandex instant discovery — $0)
2. Checks Core Web Vitals via Google PageSpeed Insights API (25,000 free/day — $0)
"""
import os
import xml.etree.ElementTree as ET
import requests

SITE_DOMAIN = os.getenv("SITE_DOMAIN", "componentmind.com")
INDEXNOW_KEY = os.getenv("INDEXNOW_KEY")
PSI_API_KEY = os.getenv("GOOGLE_PSI_API_KEY")


def read_sitemap_urls(path: str = "sitemap.xml") -> list[str]:
    tree = ET.parse(path)
    root = tree.getroot()
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    return [loc.text.strip() for loc in root.findall("sm:url/sm:loc", ns) if loc.text]


def ping_indexnow(urls: list[str]) -> None:
    if not INDEXNOW_KEY:
        print("INDEXNOW_KEY not set — skipping IndexNow submission.")
        return
    payload = {
        "host": SITE_DOMAIN,
        "key": INDEXNOW_KEY,
        "keyLocation": f"https://{SITE_DOMAIN}/{INDEXNOW_KEY}.txt",
        "urlList": urls,
    }
    resp = requests.post("https://api.indexnow.org/IndexNow", json=payload, timeout=20)
    print(f"[IndexNow] HTTP {resp.status_code} for {len(urls)} URLs")


def check_pagespeed(url: str) -> None:
    params = {"url": url, "strategy": "mobile", "category": ["performance", "seo", "accessibility"]}
    if PSI_API_KEY:
        params["key"] = PSI_API_KEY
    resp = requests.get("https://www.googleapis.com/pagespeedonline/v5/runPagespeed", params=params, timeout=45)
    if resp.status_code != 200:
        print(f"[PSI] Skipped ({resp.status_code}) for {url}")
        return
    cats = resp.json().get("lighthouseResult", {}).get("categories", {})
    summary = {k: round((v.get("score") or 0) * 100) for k, v in cats.items()}
    print(f"[PSI] {url} -> {summary}")


def main() -> None:
    urls = read_sitemap_urls()
    ping_indexnow(urls)
    if urls:
        check_pagespeed(urls[0])


if __name__ == "__main__":
    main()
