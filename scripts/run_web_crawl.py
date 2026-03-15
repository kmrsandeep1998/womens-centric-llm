#!/usr/bin/env python3

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

from scrapy.crawler import CrawlerProcess

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.scrapers.women_health_spider import WomenHealthSpider


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run high-signal women-health crawl with async concurrency and focused URL expansion."
    )
    parser.add_argument(
        "--output",
        default="data/web_crawl/health_pages.jsonl",
        help="Output JSONL crawl file path.",
    )
    parser.add_argument("--concurrency", type=int, default=20, help="Total concurrent requests.")
    parser.add_argument(
        "--per-domain",
        type=int,
        default=8,
        help="Concurrent requests per domain.",
    )
    parser.add_argument("--depth", type=int, default=3, help="Max crawl depth.")
    parser.add_argument("--max-pages", type=int, default=1000000, help="Maximum total pages.")
    parser.add_argument(
        "--max-links-per-page",
        type=int,
        default=25,
        help="Limit follow links extracted per crawled page.",
    )
    parser.add_argument(
        "--max-pages-per-domain",
        type=int,
        default=4000,
        help="Per-domain crawl cap to prevent single-site floods.",
    )
    parser.add_argument(
        "--min-content-chars",
        type=int,
        default=180,
        help="Skip pages with less extracted text than this.",
    )
    parser.add_argument(
        "--follow-pubmed-links",
        action="store_true",
        help="Follow non-article PubMed links (disabled by default).",
    )
    parser.add_argument(
        "--timestamped-output",
        action="store_true",
        help="Write output to data/web_crawl/health_pages_<timestamp>.jsonl.",
    )
    parser.add_argument(
        "--seed-file",
        default="",
        help="Optional file with seed URLs (one per line).",
    )
    parser.add_argument(
        "--allowed-domain-file",
        default="",
        help="Optional file with allowed domains (one per line).",
    )
    parser.add_argument(
        "--ingest",
        action="store_true",
        help="Run scripts/ingest_web_crawl.py after crawl.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if args.timestamped_output:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        output_path = output_path.parent / f"health_pages_{ts}.jsonl"

    feed_path = output_path
    feed_uri = str(feed_path)
    settings = {
        "ROBOTSTXT_OBEY": True,
        "CONCURRENT_REQUESTS": args.concurrency,
        "CONCURRENT_REQUESTS_PER_DOMAIN": args.per_domain,
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "DOWNLOAD_TIMEOUT": 25,
        "RETRY_ENABLED": True,
        "RETRY_TIMES": 2,
        "REACTOR_THREADPOOL_MAXSIZE": max(args.concurrency, args.per_domain),
        "DOWNLOAD_DELAY": 0.1,
        "RANDOMIZE_DOWNLOAD_DELAY": False,
        "AUTOTHROTTLE_ENABLED": False,
        "TELNETCONSOLE_ENABLED": False,
        "CLOSESPIDER_PAGECOUNT": args.max_pages,
        "FEEDS": {
            feed_uri: {
                "format": "jsonlines",
                "overwrite": True,
                "encoding": "utf-8",
                "indent": 0,
            }
        },
        "FEED_EXPORT_ENCODING": "utf-8",
        "FEED_EXPORT_FIELDS": [
            "url",
            "source",
            "title",
            "canonical_url",
            "language",
            "http_status",
            "publication_date",
            "crawl_depth",
            "fetched_at",
            "fetched_host",
            "content_sha1",
            "content_len",
            "content",
        ],
    }
    # Keep explicit CLI values as the highest-priority settings.
    process = CrawlerProcess(settings=settings, install_root_handler=True)
    process.crawl(
        WomenHealthSpider,
        max_depth=str(args.depth),
        max_links_per_page=str(args.max_links_per_page),
        min_content_chars=str(args.min_content_chars),
        max_pages_per_domain=str(args.max_pages_per_domain),
        follow_pubmed_links="true" if args.follow_pubmed_links else "false",
        seed_file=args.seed_file,
        allowed_domain_file=args.allowed_domain_file,
    )
    process.start()

    if args.ingest:
        ingest_path = feed_path
        if not ingest_path.exists():
            fallback = Path("data/web_crawl/health_pages.jsonl")
            if fallback.exists():
                ingest_path = fallback
        result = subprocess.run(
            [sys.executable, "scripts/ingest_web_crawl.py", "--input", str(ingest_path)],
            check=False,
        )
        if result.returncode != 0:
            raise SystemExit(f"Ingest step failed for {ingest_path}.")


if __name__ == "__main__":
    main()
