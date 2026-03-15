#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SEED_DIR = ROOT / "data" / "seed_lists"


def parse_args():
    parser = argparse.ArgumentParser(description="Discover URLs via SerpAPI then crawl + ingest in one run.")
    parser.add_argument(
        "--queries",
        default=str(SEED_DIR / "women_health_queries.txt"),
        help="Query list for SerpAPI discovery.",
    )
    parser.add_argument(
        "--discovered-urls",
        default=str(SEED_DIR / "discovered_urls.txt"),
        help="Output file for discovered URLs.",
    )
    parser.add_argument(
        "--discovered-domains",
        default=str(SEED_DIR / "discovered_domains.txt"),
        help="Output file for discovered domains.",
    )
    parser.add_argument("--serpapi-key", default=os.environ.get("SERPAPI_KEY", ""), help="SerpAPI key.")
    parser.add_argument("--discovery-num", type=int, default=100, help="Results per query.")
    parser.add_argument("--discovery-sleep-ms", type=int, default=300, help="Sleep between discovery requests.")
    parser.add_argument("--concurrency", type=int, default=20, help="Crawler concurrency.")
    parser.add_argument("--per-domain", type=int, default=6, help="Crawler per-domain concurrency.")
    parser.add_argument("--depth", type=int, default=1, help="Crawler depth.")
    parser.add_argument("--max-pages", type=int, default=1000000, help="Total crawl page cap.")
    parser.add_argument("--max-pages-per-domain", type=int, default=200, help="Per-domain crawl cap.")
    parser.add_argument("--max-links-per-page", type=int, default=25, help="Links followed per page.")
    parser.add_argument("--min-content-chars", type=int, default=180, help="Minimum content length.")
    parser.add_argument("--timestamped-output", action="store_true", help="Timestamp crawl output.")
    return parser.parse_args()


def run(cmd: list[str]):
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        raise SystemExit(f"Command failed: {' '.join(cmd)}")


def main():
    args = parse_args()
    if not args.serpapi_key:
        raise SystemExit("Missing SERPAPI key. Set SERPAPI_KEY or pass --serpapi-key.")

    discovery_cmd = [
        sys.executable,
        "scripts/discover_urls_serpapi.py",
        "--queries",
        args.queries,
        "--output",
        args.discovered_urls,
        "--domains-output",
        args.discovered_domains,
        "--api-key",
        args.serpapi_key,
        "--num",
        str(args.discovery_num),
        "--sleep-ms",
        str(args.discovery_sleep_ms),
    ]
    run(discovery_cmd)

    crawl_cmd = [
        sys.executable,
        "scripts/run_web_crawl.py",
        "--seed-file",
        args.discovered_urls,
        "--allowed-domain-file",
        args.discovered_domains,
        "--concurrency",
        str(args.concurrency),
        "--per-domain",
        str(args.per-domain),
        "--depth",
        str(args.depth),
        "--max-pages",
        str(args.max_pages),
        "--max-pages-per-domain",
        str(args.max_pages_per_domain),
        "--max-links-per-page",
        str(args.max_links_per_page),
        "--min-content-chars",
        str(args.min_content_chars),
        "--ingest",
    ]
    if args.timestamped_output:
        crawl_cmd.append("--timestamped-output")
    run(crawl_cmd)


if __name__ == "__main__":
    main()
