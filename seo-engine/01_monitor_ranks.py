"""
01_monitor_ranks.py
Monitors target keywords via DataForSEO Async/Live SERP API ($0.0006-$0.002/SERP)
and detects low-DR / UGC weak-spot opportunities via Open PageRank API (30K free/mo).
Stores daily snapshots in Neon Serverless Postgres (Free Tier) if NEON_DATABASE_URL is set.
"""
import json
import os
from urllib.parse import urlparse
import requests

DOMAIN = os.getenv("SITE_DOMAIN", "componentmind.com")
DFS_LOGIN = os.getenv("DATAFORSEO_LOGIN")
DFS_PASSWORD = os.getenv("DATAFORSEO_PASSWORD")
OPR_API_KEY = os.getenv("OPENPAGERANK_API_KEY")
NEON_URL = os.getenv("NEON_DATABASE_URL")

WEAK_UGC_DOMAINS = {"reddit.com", "quora.com", "medium.com", "dev.to", "linkedin.com", "news.ycombinator.com"}
SEED_KEYWORDS = [
    "componentmind vs storybook",
    "ai ui component audit tool",
    "mcp server design system react",
    "automated core web vitals component ci",
    "storybook alternative for ai agents",
]


def fetch_open_pagerank(domains: list[str]) -> dict[str, float]:
    if not OPR_API_KEY or not domains:
        return {}
    clean = sorted({d.lower().lstrip("www.") for d in domains if d})[:100]
    resp = requests.get(
        "https://openpagerank.com/api/v1.0/getPageRank",
        headers={"API-OPR": OPR_API_KEY},
        params=[("domains[]", d) for d in clean],
        timeout=20,
    )
    resp.raise_for_status()
    out = {}
    for row in resp.json().get("response", []):
        out[row.get("domain", "")] = float(row.get("page_rank_decimal") or 0.0)
    return out


def query_dataforseo_serp(keyword: str) -> dict:
    payload = [{"keyword": keyword, "location_code": 2840, "language_code": "en", "depth": 10}]
    resp = requests.post(
        "https://api.dataforseo.com/v3/serp/google/organic/live/regular",
        auth=(DFS_LOGIN, DFS_PASSWORD),
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    tasks = resp.json().get("tasks", [])
    if not tasks or not tasks[0].get("result"):
        return {"position": None, "url": None, "has_ai_overview": False, "top_domains": []}

    items = tasks[0]["result"][0].get("items", [])
    has_aio = any(i.get("type") == "ai_overview" for i in items)
    organic = [i for i in items if i.get("type") == "organic"][:10]

    my_pos, my_url = None, None
    top_domains = []
    for item in organic:
        url = item.get("url", "")
        host = urlparse(url).netloc.lower().lstrip("www.")
        top_domains.append({"rank": item.get("rank_group"), "domain": host, "url": url})
        if DOMAIN in host and my_pos is None:
            my_pos = item.get("rank_group")
            my_url = url

    return {"position": my_pos, "url": my_url, "has_ai_overview": has_aio, "top_domains": top_domains}


def save_to_neon(results: list[dict]) -> None:
    if not NEON_URL:
        return
    import psycopg2

    with psycopg2.connect(NEON_URL) as conn:
        with conn.cursor() as cur:
            for r in results:
                cur.execute(
                    """
                    INSERT INTO rank_snapshots (keyword, domain, position, ranking_url, has_ai_overview, top_competitors)
                    VALUES (%s, %s, %s, %s, %s, %s::jsonb)
                    ON CONFLICT (keyword, domain, captured_at) DO UPDATE SET
                        position = EXCLUDED.position,
                        ranking_url = EXCLUDED.ranking_url,
                        has_ai_overview = EXCLUDED.has_ai_overview,
                        top_competitors = EXCLUDED.top_competitors;
                    """,
                    (r["keyword"], DOMAIN, r["position"], r["url"], r["has_ai_overview"], json.dumps(r["top_domains"])),
                )


def main() -> None:
    if not (DFS_LOGIN and DFS_PASSWORD):
        print("DATAFORSEO_LOGIN / DATAFORSEO_PASSWORD not configured yet — skipping live SERP fetch.")
        return

    snapshots = []
    all_domains = []
    for kw in SEED_KEYWORDS:
        data = query_dataforseo_serp(kw)
        data["keyword"] = kw
        snapshots.append(data)
        all_domains.extend(d["domain"] for d in data["top_domains"][:5])

    pr_map = fetch_open_pagerank(all_domains)
    for s in snapshots:
        top5 = s["top_domains"][:5]
        weak_hits = [
            d["domain"]
            for d in top5
            if d["domain"] in WEAK_UGC_DOMAINS or (d["domain"] in pr_map and pr_map[d["domain"]] < 3.5)
        ]
        s["weak_spot_hits"] = weak_hits
        print(f"[SERP] {s['keyword']} | Pos: {s['position']} | AIO: {s['has_ai_overview']} | Weak Top-5: {weak_hits}")

    save_to_neon(snapshots)


if __name__ == "__main__":
    main()
