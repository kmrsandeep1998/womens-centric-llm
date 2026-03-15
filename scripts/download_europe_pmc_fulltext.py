#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

import requests


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

EUROPE_PMC_FULLTEXT = "https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML"

ALLOWED_LICENSES = {
    "cc-by",
    "cc-by-4.0",
    "cc-by-sa",
    "cc-by-sa-4.0",
    "cc0",
    "cc0-1.0",
    "cc-by-nc",
    "cc-by-nc-nd",
    "cc-by-nc-sa",
    "cc-by-nd",
    "cc0-4.0",
    "by",
    "by-sa",
    "by-nc",
}


def normalize_license(value: str) -> str:
    return value.strip().lower().replace(" ", "-")


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            # Skip partial/invalid lines (can happen if file is being written).
            continue
    return rows


def fetch_xml(url: str, max_retries: int, sleep_ms: int, request_timeout: int, pmcid: str) -> Optional[str]:
    last_exc: Optional[Exception] = None
    for attempt in range(max_retries):
        try:
            r = requests.get(url, timeout=request_timeout)
            if r.status_code in {429, 500, 502, 503, 504}:
                print(f"[retry] HTTP {r.status_code} for {url}, attempt={attempt+1}/{max_retries}")
                time.sleep((sleep_ms / 1000) * (attempt + 1))
                continue
            if r.status_code != 200:
                print(f"[warn] HTTP {r.status_code} for PMCID={pmcid} ({url})", flush=True)
                return None
            return r.text
        except Exception as exc:
            last_exc = exc
            print(f"[warn] request failed for PMCID={pmcid} attempt={attempt+1}/{max_retries}: {exc}", flush=True)
            time.sleep((sleep_ms / 1000) * (attempt + 1))
    if last_exc is not None:
        print(f"[warn] Failed to fetch PMCID={pmcid}: {last_exc}", flush=True)
    return None


def main():
    parser = argparse.ArgumentParser(description="Download Europe PMC full text for enriched rows.")
    parser.add_argument("--input", default=str(DATA_DIR / "real_data_candidates.jsonl"))
    parser.add_argument("--output-dir", default=str(DATA_DIR / "real_data_fulltext"))
    parser.add_argument("--max-downloads", type=int, default=500)
    parser.add_argument("--sleep-ms", type=int, default=250)
    parser.add_argument("--max-retries", type=int, default=5)
    parser.add_argument("--request-timeout", type=int, default=20, help="Timeout per HTTP request in seconds.")
    parser.add_argument("--log-every", type=int, default=50)
    parser.add_argument("--reload-every", type=int, default=200, help="Reload candidates after N checks.")
    parser.add_argument("--print-progress", action="store_true", help="Print per-checked row progress including every row.")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    downloaded = 0
    checked = 0
    existing = 0
    failed = 0
    skipped_not_eligible = 0
    rows = load_jsonl(Path(args.input))
    idx = 0
    while downloaded < args.max_downloads and idx < len(rows):
        if args.reload_every and checked % args.reload_every == 0 and checked != 0:
            rows = load_jsonl(Path(args.input))
            idx = 0
        row = rows[idx]
        idx += 1
        if downloaded >= args.max_downloads:
            break
        if not row.get("europe_pmc_enriched"):
            skipped_not_eligible += 1
            continue
        license_id = normalize_license(row.get("europe_pmc_license") or "")
        if license_id not in ALLOWED_LICENSES:
            skipped_not_eligible += 1
            continue
        pmcid = row.get("pmcid")
        if not pmcid:
            skipped_not_eligible += 1
            continue

        checked += 1
        if args.print_progress:
            status = (
                f"Checked {checked} eligible rows, downloaded {downloaded}, "
                f"existing {existing}, failed {failed}"
            )
            if row.get("pmcid"):
                status += f", row pmcid={row.get('pmcid')}"
            print(status, flush=True)
        elif args.log_every and checked % args.log_every == 0:
            print(
                f"Checked {checked} eligible rows, downloaded {downloaded}, "
                f"existing {existing}, failed {failed}",
                flush=True,
            )

        out_path = out_dir / f"{pmcid}.xml"
        if out_path.exists():
            existing += 1
            if args.print_progress:
                print(f"skip (already exists): {pmcid}", flush=True)
            continue
        # Prefer pre-resolved fulltext URL if available from enrichment, then fallback to PMCID endpoint.
        url = row.get("europe_pmc_fulltext_url") or row.get("fulltext_xml_url")
        if not url:
            url = EUROPE_PMC_FULLTEXT.format(pmcid=pmcid)
        print(f"[info] downloading XML for PMCID={pmcid}, url={url}", flush=True)
        if not args.print_progress:
            print(f"Attempting PMCID {pmcid}", flush=True)
        xml = fetch_xml(url, args.max_retries, args.sleep_ms, args.request_timeout, pmcid)

        if not xml:
            failed += 1
            continue
        out_path.write_text(xml)
        downloaded += 1

    print(f"Checked {checked} eligible rows (skipped-not-eligible {skipped_not_eligible})", flush=True)
    print(
        f"Downloaded {downloaded} new XML files to {out_dir}; "
        f"already existed {existing}; failed {failed}",
        flush=True,
    )


if __name__ == "__main__":
    main()
