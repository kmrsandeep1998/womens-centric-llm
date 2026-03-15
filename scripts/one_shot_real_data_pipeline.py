#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

import requests
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"


OPENALEX_API = "https://api.openalex.org/works"
EUROPE_PMC_SEARCH = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
EUROPE_PMC_FULLTEXT = "https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML"

# Safe license allowlist for full-text use.
ALLOWED_LICENSES = {
    "cc-by",
    "cc-by-4.0",
    "cc-by-sa",
    "cc0",
    "cc-by-nc",
}


def save_jsonl(path: Path, rows: List[Dict[str, Any]]):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r, ensure_ascii=True) for r in rows) + ("\n" if rows else ""))


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not path.exists():
        return rows
    for line_no, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"{path}:{line_no} invalid json: {exc}") from exc
    return rows


def openalex_query(params: Dict[str, Any], max_retries: int, sleep_ms: int) -> Dict[str, Any]:
    last_exc: Optional[Exception] = None
    for attempt in range(max_retries):
        try:
            r = requests.get(OPENALEX_API, params=params, timeout=30)
            if r.status_code in {429, 500, 502, 503, 504}:
                time.sleep((sleep_ms / 1000) * (attempt + 1))
                continue
            r.raise_for_status()
            return r.json()
        except Exception as exc:
            last_exc = exc
            time.sleep((sleep_ms / 1000) * (attempt + 1))
    raise SystemExit(f"OpenAlex request failed after {max_retries} attempts: {last_exc}")


def europe_pmc_search(query: str, page: int, page_size: int) -> Dict[str, Any]:
    params = {
        "query": query,
        "format": "json",
        "page": page,
        "pageSize": page_size,
    }
    r = requests.get(EUROPE_PMC_SEARCH, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def europe_pmc_fulltext(pmcid: str) -> Optional[str]:
    url = EUROPE_PMC_FULLTEXT.format(pmcid=pmcid)
    r = requests.get(url, timeout=30)
    if r.status_code != 200:
        return None
    return r.text


def main():
    parser = argparse.ArgumentParser(description="One-shot real-data pipeline (OpenAlex + Europe PMC).")
    parser.add_argument("--keywords", required=True, help="Comma-separated keywords.")
    parser.add_argument("--max-works", type=int, default=500, help="Max OpenAlex works.")
    parser.add_argument("--per-page", type=int, default=50, help="OpenAlex page size (max 200).")
    parser.add_argument("--mailto", default="", help="Contact email for OpenAlex politeness.")
    parser.add_argument("--download-fulltext", action="store_true", help="Download Europe PMC full text for OA items.")
    parser.add_argument("--max-fulltext", type=int, default=50, help="Max full-text downloads.")
    parser.add_argument("--sleep-ms", type=int, default=250, help="Sleep between API calls.")
    parser.add_argument("--resume", action="store_true", help="Resume from previous candidates file.")
    parser.add_argument("--split-keywords", action="store_true", help="Query each keyword separately.")
    parser.add_argument("--max-retries", type=int, default=5, help="Max retries for API calls.")
    parser.add_argument("--log-every", type=int, default=1, help="Log progress every N pages.")
    parser.add_argument("--debug", action="store_true", help="Log detailed per-page stats.")
    parser.add_argument("--debug-sample", type=int, default=3, help="Sample size for debug logging.")
    args = parser.parse_args()

    if args.per_page > 200:
        raise SystemExit("OpenAlex per-page must be <= 200.")

    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    if not keywords:
        raise SystemExit("No keywords provided.")

    candidates_path = DATA_DIR / "real_data_candidates.jsonl"
    out_candidates = []
    seen_ids = set()
    if args.resume and candidates_path.exists():
        out_candidates = load_jsonl(candidates_path)
        seen_ids = {row.get("openalex_id") for row in out_candidates if row.get("openalex_id")}

    fulltext_dir = DATA_DIR / "real_data_fulltext"
    fulltext_dir.mkdir(parents=True, exist_ok=True)

    queries = keywords if args.split_keywords else [" ".join(keywords)]
    fetched = 0
    for query in queries:
        cursor = "*"
        page = 0
        while fetched < args.max_works:
            page += 1
            params = {
                "search": query,
                "filter": "is_oa:true",
                "per-page": args.per_page,
                "cursor": cursor,
            }
            if args.mailto:
                params["mailto"] = args.mailto
            data = openalex_query(params, args.max_retries, args.sleep_ms)
            results = data.get("results", [])
            cursor = data.get("meta", {}).get("next_cursor")
            if not results:
                break

            dupes = 0
            pmcid_count = 0
            allowed_license_count = 0
            domain_counts: Dict[str, int] = {}
            for work in results:
                if fetched >= args.max_works:
                    break
                work_id = work.get("id")
                if work_id in seen_ids:
                    dupes += 1
                    continue
                fetched += 1
                seen_ids.add(work_id)
                oa = work.get("open_access", {}) or {}
                license_id = (oa.get("license") or "").lower()
                if license_id in ALLOWED_LICENSES:
                    allowed_license_count += 1
                locations = work.get("locations", []) or []
                pmcid = None
                for loc in locations:
                    if not loc or not isinstance(loc, dict):
                        continue
                    ids = (loc.get("source") or {}).get("ids", {})
                    if "pmcid" in ids:
                        pmcid = ids["pmcid"]
                        break
                if pmcid:
                    pmcid_count += 1
                # Track primary location domain for debug logs.
                primary = work.get("primary_location") or {}
                url = (primary.get("landing_page_url") or "").strip()
                if url:
                    host = urlparse(url).hostname or "unknown"
                    domain_counts[host] = domain_counts.get(host, 0) + 1
                out_candidates.append(
                    {
                        "openalex_id": work_id,
                        "title": work.get("title"),
                        "publication_year": work.get("publication_year"),
                        "doi": work.get("doi"),
                        "open_access": oa,
                        "license": license_id,
                        "pmcid": pmcid,
                        "primary_location": work.get("primary_location"),
                    }
                )

            time.sleep(args.sleep_ms / 1000)
            if args.log_every and page % args.log_every == 0:
                print(
                    f"query='{query}' page={page} fetched={fetched} total_candidates={len(out_candidates)}"
                )
                if args.debug:
                    top_domains = sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                    print(
                        "  stats:"
                        f" results={len(results)} dupes={dupes} pmcid={pmcid_count}"
                        f" allowed_license={allowed_license_count}"
                    )
                    print(f"  top_domains={top_domains}")
                    # Sample titles for traceability without dumping huge logs.
                    sample_titles = [r.get('title') for r in results[: args.debug_sample]]
                    print(f"  sample_titles={sample_titles}")
                # Persist incrementally so resume works even if interrupted.
                save_jsonl(candidates_path, out_candidates)
        # Move to next keyword query.

    save_jsonl(candidates_path, out_candidates)
    print(f"Wrote {len(out_candidates)} candidates to {candidates_path}")

    if not args.download_fulltext:
        return

    downloaded = 0
    for row in out_candidates:
        if downloaded >= args.max_fulltext:
            break
        license_id = row.get("license", "")
        pmcid = row.get("pmcid")
        if not pmcid:
            continue
        if license_id not in ALLOWED_LICENSES:
            continue
        xml = europe_pmc_fulltext(pmcid=pmcid)
        if not xml:
            continue
        (fulltext_dir / f"{pmcid}.xml").write_text(xml)
        downloaded += 1
        time.sleep(args.sleep_ms / 1000)

    print(f"Downloaded {downloaded} full-text XML files into {fulltext_dir}")


if __name__ == "__main__":
    main()
