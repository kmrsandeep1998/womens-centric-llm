#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import time
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "domain_lists"


class LinkExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "a":
            return
        for key, value in attrs:
            if key.lower() == "href" and value:
                self.links.append(value)


def fetch(url: str, timeout: int = 25) -> str:
    req = Request(url, headers={"User-Agent": "TrackyCrawler/1.1 (+domain list builder)"})
    with urlopen(req, timeout=timeout) as resp:
        content_type = resp.headers.get("Content-Type", "")
        if "text/html" not in content_type and "application/xhtml" not in content_type:
            return ""
        return resp.read().decode("utf-8", errors="ignore")


def extract_links(base_url: str, html: str) -> list[str]:
    parser = LinkExtractor()
    parser.feed(html)
    links = []
    for link in parser.links:
        if link.startswith("mailto:") or link.startswith("javascript:"):
            continue
        links.append(urljoin(base_url, link))
    return links


def is_internal(url: str, domain: str) -> bool:
    host = urlparse(url).netloc.lower()
    return host == domain or host.endswith(f".{domain}")


def domain_from_url(url: str) -> str:
    return urlparse(url).netloc.lower().replace("www.", "")


def allow_domain(domain: str, allow_suffixes: Iterable[str]) -> bool:
    domain = domain.lower()
    return any(domain.endswith(suffix) for suffix in allow_suffixes)


def parse_args():
    parser = argparse.ArgumentParser(description="Build an India-region domain list from public directories.")
    parser.add_argument(
        "--seed",
        action="append",
        default=[
            "https://igod.gov.in/site_map",
            "https://igod.gov.in/sector/health-and-family-welfare",
        ],
        help="Seed URLs to start crawling (can be repeated).",
    )
    parser.add_argument("--max-pages", type=int, default=2000, help="Max directory pages to crawl.")
    parser.add_argument("--max-depth", type=int, default=3, help="Max crawl depth for directories.")
    parser.add_argument("--sleep-ms", type=int, default=200, help="Sleep between requests (ms).")
    parser.add_argument(
        "--allow-suffix",
        action="append",
        default=[".gov.in", ".nic.in", ".ac.in", ".edu.in", ".res.in"],
        help="Domain suffixes to allow (can be repeated).",
    )
    parser.add_argument(
        "--include-all-in",
        action="store_true",
        help="If set, include any .in domain (broad).",
    )
    parser.add_argument(
        "--output-prefix",
        default="india_gov",
        help="Output file prefix in data/domain_lists/.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    allow_suffixes = args.allow_suffix[:]
    if args.include_all_in and ".in" not in allow_suffixes:
        allow_suffixes.append(".in")

    visited = set()
    queue = [(seed, 0) for seed in args.seed]
    extracted_domains = set()
    raw_records = []

    max_pages = args.max_pages
    max_depth = args.max_depth
    sleep_s = max(args.sleep_ms, 0) / 1000.0

    while queue and len(visited) < max_pages:
        url, depth = queue.pop(0)
        if url in visited:
            continue
        visited.add(url)

        if depth > max_depth:
            continue

        try:
            html = fetch(url)
        except Exception:
            continue

        if not html:
            continue

        links = extract_links(url, html)
        out_links = []
        for link in links:
            link_domain = domain_from_url(link)
            if not link_domain:
                continue
            if is_internal(link, "igod.gov.in"):
                if link not in visited and depth + 1 <= max_depth:
                    queue.append((link, depth + 1))
                continue
            if allow_domain(link_domain, allow_suffixes):
                extracted_domains.add(link_domain)
                out_links.append(link)

        raw_records.append(
            {
                "source_url": url,
                "depth": depth,
                "extracted_external_links": out_links,
            }
        )

        if sleep_s:
            time.sleep(sleep_s)

    domain_list = sorted(extracted_domains)
    prefix = args.output_prefix
    domains_path = DATA_DIR / f"{prefix}_domains.txt"
    seeds_path = DATA_DIR / f"{prefix}_seed_urls.txt"
    raw_path = DATA_DIR / f"{prefix}_source_links.jsonl"

    domains_path.write_text("\n".join(domain_list) + ("\n" if domain_list else ""))
    seeds_path.write_text(
        "\n".join(f"https://{domain}" for domain in domain_list) + ("\n" if domain_list else "")
    )
    raw_path.write_text("\n".join(json.dumps(r, ensure_ascii=True) for r in raw_records) + "\n")

    print("Domain list build complete")
    print(f"- domains: {len(domain_list)} -> {domains_path}")
    print(f"- seeds: {seeds_path}")
    print(f"- raw link log: {raw_path}")


if __name__ == "__main__":
    main()
