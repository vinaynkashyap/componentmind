"""
02_competitor_nlp.py
Zero-subscription replacement for Surfer SEO / Firecrawl:
- Fetches top competitor URLs via Jina Reader (https://r.jina.ai/{url}, free key up to 500 RPM)
- Computes TF-IDF topical gap terms using scikit-learn
- Emits a structured JSON brief ready for Gemini AI Studio Free / OpenRouter / Bedrock
"""
import json
import os
import sys
import requests
from sklearn.feature_extraction.text import TfidfVectorizer

JINA_API_KEY = os.getenv("JINA_API_KEY")


def fetch_markdown(url: str) -> str:
    headers = {"Accept": "text/plain"}
    if JINA_API_KEY:
        headers["Authorization"] = f"Bearer {JINA_API_KEY}"
    resp = requests.get(f"https://r.jina.ai/{url}", headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.text


def compute_tfidf_gaps(target_text: str, competitor_texts: list[str], top_n: int = 25) -> list[dict]:
    corpus = [target_text] + competitor_texts
    vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=1500)
    matrix = vec.fit_transform(corpus)
    terms = vec.get_feature_names_out()

    target_scores = matrix[0].toarray()[0]
    comp_mean = matrix[1:].toarray().mean(axis=0)

    gaps = []
    for idx, term in enumerate(terms):
        diff = float(comp_mean[idx] - target_scores[idx])
        if diff > 0.015:
            gaps.append({"term": term, "gap_score": round(diff, 4)})
    gaps.sort(key=lambda x: x["gap_score"], reverse=True)
    return gaps[:top_n]


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python 02_competitor_nlp.py <our_url> <competitor_url_1> [competitor_url_2 ...]")
        sys.exit(0)

    our_url, comp_urls = sys.argv[1], sys.argv[2:]
    our_md = fetch_markdown(our_url)
    comp_mds = [fetch_markdown(u) for u in comp_urls]
    gaps = compute_tfidf_gaps(our_md, comp_mds)
    print(json.dumps({"our_url": our_url, "competitors": comp_urls, "missing_topical_terms": gaps}, indent=2))


if __name__ == "__main__":
    main()
