#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from urllib.parse import urlparse, urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "seed_lists"


def fetch_json(url: str, params: dict, timeout: int = 30) -> dict:
    query = urlencode(params)
    req = Request(f"{url}?{query}", headers={"User-Agent": "TrackyCrawler/1.1"})
    with urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="ignore") or "{}")


def normalize_url(raw: str) -> str:
    raw = (raw or "").strip()
    if not raw:
        return ""
    return raw.split("#", 1)[0]


def domain_from_url(raw: str) -> str:
    try:
        return urlparse(raw).netloc.lower().replace("www.", "")
    except Exception:
        return ""


def parse_args():
    parser = argparse.ArgumentParser(description="Discover URLs using SerpAPI.")
    parser.add_argument("--queries", default=str(DATA_DIR / "women_health_queries.txt"))
    parser.add_argument("--output", default=str(DATA_DIR / "discovered_urls.txt"))
    parser.add_argument("--domains-output", default=str(DATA_DIR / "discovered_domains.txt"))
    parser.add_argument("--api-key", default=os.environ.get("SERPAPI_KEY", ""))
    parser.add_argument("--engine", default="google")
    parser.add_argument("--num", type=int, default=100)
    parser.add_argument("--max-queries", type=int, default=0)
    parser.add_argument("--sleep-ms", type=int, default=300)
    return parser.parse_args()


def main():
    args = parse_args()
    if not args.api_key:
        raise SystemExit("Missing SERPAPI key. Set SERPAPI_KEY or pass --api-key.")

    queries = [q.strip() for q in Path(args.queries).read_text().splitlines() if q.strip()]
    if args.max_queries:
        queries = queries[: args.max_queries]

    out_urls = set()
    out_domains = set()
    sleep_s = max(args.sleep_ms, 0) / 1000.0

    for q in queries:
        params = {
            "engine": args.engine,
            "q": q,
            "api_key": args.api_key,
            "num": args.num,
        }
        data = fetch_json("https://serpapi.com/search", params=params)
        for item in data.get("organic_results", []):
            url = normalize_url(item.get("link", ""))
            if not url:
                continue
            out_urls.add(url)
            domain = domain_from_url(url)
            if domain:
                out_domains.add(domain)
        if sleep_s:
            time.sleep(sleep_s)

    urls_path = Path(args.output)
    domains_path = Path(args.domains_output)
    urls_path.write_text("\n".join(sorted(out_urls)) + ("\n" if out_urls else ""))
    domains_path.write_text("\n".join(sorted(out_domains)) + ("\n" if out_domains else ""))

    print("Discovery complete")
    print(f"- queries: {len(queries)}")
    print(f"- urls: {len(out_urls)} -> {urls_path}")
    print(f"- domains: {len(out_domains)} -> {domains_path}")


if __name__ == "__main__":
    main()
