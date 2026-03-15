#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

import requests
import concurrent.futures


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

EUROPE_PMC_SEARCH = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"{path}:{line_no} invalid json: {exc}") from exc
    return rows


def write_jsonl(path: Path, rows: List[Dict[str, Any]]):
    path.write_text("\n".join(json.dumps(r, ensure_ascii=True) for r in rows) + ("\n" if rows else ""))


def europe_pmc_search(query: str, max_retries: int, sleep_ms: int) -> Optional[Dict[str, Any]]:
    params = {
        "query": query,
        "format": "json",
        "pageSize": 1,
        "resultType": "core",
    }
    last_exc: Optional[Exception] = None
    for attempt in range(max_retries):
        try:
            r = requests.get(EUROPE_PMC_SEARCH, params=params, timeout=20)
            if r.status_code in {429, 500, 502, 503, 504}:
                time.sleep((sleep_ms / 1000) * (attempt + 1))
                continue
            if r.status_code != 200:
                return None
            return r.json()
        except Exception as exc:
            last_exc = exc
            time.sleep((sleep_ms / 1000) * (attempt + 1))
    print(f"[warn] Europe PMC request failed after {max_retries} attempts: {last_exc}")
    return None


def normalize_license(value: str) -> str:
    return value.strip().lower().replace(" ", "-")


def main():
    parser = argparse.ArgumentParser(description="Enrich candidates with Europe PMC metadata.")
    parser.add_argument("--input", default=str(DATA_DIR / "real_data_candidates.jsonl"))
    parser.add_argument("--output", default=str(DATA_DIR / "real_data_candidates.jsonl"))
    parser.add_argument("--max-enrich", type=int, default=1000)
    parser.add_argument("--sleep-ms", type=int, default=250)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--log-every", type=int, default=200, help="Log progress every N checked rows.")
    parser.add_argument("--max-retries", type=int, default=5, help="Max retries for Europe PMC calls.")
    parser.add_argument("--concurrency", type=int, default=1, help="Concurrent Europe PMC lookups.")
    parser.add_argument(
        "--refresh-missing-license",
        action="store_true",
        help="Re-enrich rows that have europe_pmc_enriched but missing license.",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    rows = load_jsonl(input_path)
    enriched = 0
    checked = 0

    # Build a list of indices to enrich.
    targets: List[int] = []
    for idx, row in enumerate(rows):
        if args.resume and row.get("europe_pmc_enriched"):
            if not args.refresh_missing_license:
                continue
            if row.get("europe_pmc_license"):
                continue
        doi = row.get("doi")
        if not doi:
            continue
        targets.append(idx)
        if len(targets) >= args.max_enrich:
            break

    def worker(idx: int):
        row = rows[idx]
        doi = row.get("doi")
        if not doi:
            return idx, None
        doi_value = doi.replace("https://doi.org/", "")
        query = f'DOI:{doi_value} OR DOISyntax:"{doi_value}"'
        data = europe_pmc_search(query, args.max_retries, args.sleep_ms)
        return idx, data

    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as executor:
        future_to_idx = {executor.submit(worker, idx): idx for idx in targets}
        for future in concurrent.futures.as_completed(future_to_idx):
            checked += 1
            if args.log_every and checked % args.log_every == 0:
                print(f"Checked {checked} rows, enriched {enriched}")
            idx, data = future.result()
            if not data:
                continue
            hits = data.get("resultList", {}).get("result", [])
            if not hits:
                continue
            hit = hits[0]
            row = rows[idx]
            row["pmcid"] = hit.get("pmcid") or row.get("pmcid")
            raw_license = hit.get("license") or row.get("europe_pmc_license") or ""
            row["europe_pmc_license"] = normalize_license(raw_license)
            row["europe_pmc_journal"] = hit.get("journalTitle")
            row["europe_pmc_is_oa"] = hit.get("isOpenAccess")
            row["europe_pmc_has_fulltext"] = bool(hit.get("hasFullText") or False)
            pmcid = row.get("pmcid")
            if pmcid:
                row["europe_pmc_fulltext_url"] = f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML"
                row["fulltext_xml_url"] = row["europe_pmc_fulltext_url"]
                if row["europe_pmc_license"] and not row["europe_pmc_has_fulltext"]:
                    # If Europe PMC knows the article and returns a PMCID but omits hasFullText,
                    # still attempt direct XML retrieval by PMCID.
                    row["europe_pmc_has_fulltext"] = True
            row["europe_pmc_enriched"] = True
            enriched += 1
            if enriched % 100 == 0:
                print(f"Enriched {enriched}")

    write_jsonl(Path(args.output), rows)
    print(f"Enriched {enriched} rows. Wrote {args.output}")


if __name__ == "__main__":
    main()
