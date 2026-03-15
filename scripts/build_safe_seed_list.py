#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlencode, urljoin, urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent.parent
SEED_DIR = ROOT / "data" / "seed_lists"


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


def fetch(url: str, timeout: int = 20) -> str:
    req = Request(url, headers={"User-Agent": "TrackyCrawler/1.1"})
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


def load_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text().splitlines() if line.strip()]


def pubmed_search_links(query: str, max_links: int) -> list[str]:
    params = urlencode({"term": query})
    url = f"https://pubmed.ncbi.nlm.nih.gov/?{params}"
    html = fetch(url)
    if not html:
        return []
    links = []
    for link in extract_links(url, html):
        if "/"+"" in link:
            pass
        if "pubmed.ncbi.nlm.nih.gov/" in link and link.rstrip("/").split("/")[-1].isdigit():
            links.append(link)
        if len(links) >= max_links:
            break
    return links


def wikipedia_search_links(query: str, max_links: int) -> list[str]:
    params = urlencode({"search": query})
    url = f"https://en.wikipedia.org/w/index.php?{params}"
    html = fetch(url)
    if not html:
        return []
    links = []
    for link in extract_links(url, html):
        if "en.wikipedia.org/wiki/" in link and "Special:" not in link:
            links.append(link)
        if len(links) >= max_links:
            break
    return links


def parse_args():
    parser = argparse.ArgumentParser(description="Build safe seed lists using PubMed + Wikipedia + allowlist domains.")
    parser.add_argument("--queries", default=str(SEED_DIR / "women_health_queries.txt"))
    parser.add_argument("--seed-allowlist", default=str(SEED_DIR / "global_health_seeds.txt"))
    parser.add_argument("--output-urls", default=str(SEED_DIR / "manual_seeds.txt"))
    parser.add_argument("--output-domains", default=str(SEED_DIR / "manual_domains.txt"))
    parser.add_argument("--max-per-query", type=int, default=10, help="Max links per query per source.")
    parser.add_argument("--sleep-ms", type=int, default=200, help="Sleep between requests (ms).")
    parser.add_argument("--include-wikipedia", action="store_true", help="Include Wikipedia search results.")
    parser.add_argument("--include-pubmed", action="store_true", help="Include PubMed search results.")
    return parser.parse_args()


def main():
    args = parse_args()
    queries = load_lines(Path(args.queries))
    allowlist_seeds = load_lines(Path(args.seed_allowlist))

    seed_urls = set(allowlist_seeds)
    domains = {domain_from_url(url) for url in allowlist_seeds if domain_from_url(url)}
    raw_records = []

    sleep_s = max(args.sleep_ms, 0) / 1000.0
    max_links = max(args.max_per_query, 0)

    for q in queries:
        record = {"query": q, "pubmed": [], "wikipedia": []}
        if args.include_pubmed:
            pm_links = pubmed_search_links(q, max_links)
            record["pubmed"] = pm_links
            seed_urls.update(pm_links)
            domains.update({domain_from_url(u) for u in pm_links if domain_from_url(u)})
        if args.include_wikipedia:
            wk_links = wikipedia_search_links(q, max_links)
            record["wikipedia"] = wk_links
            seed_urls.update(wk_links)
            domains.update({domain_from_url(u) for u in wk_links if domain_from_url(u)})
        raw_records.append(record)
        if sleep_s:
            time.sleep(sleep_s)

    urls_path = Path(args.output_urls)
    domains_path = Path(args.output_domains)
    urls_path.write_text("\n".join(sorted(seed_urls)) + ("\n" if seed_urls else ""))
    domains_path.write_text("\n".join(sorted(d for d in domains if d)) + ("\n" if domains else ""))

    (SEED_DIR / "manual_seed_debug.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=True) for r in raw_records) + "\n"
    )

    print("Safe seed list build complete")
    print(f"- queries: {len(queries)}")
    print(f"- seeds: {len(seed_urls)} -> {urls_path}")
    print(f"- domains: {len(domains)} -> {domains_path}")
    print(f"- debug log: {SEED_DIR / 'manual_seed_debug.jsonl'}")


if __name__ == "__main__":
    main()
