#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
import sys
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from local_ai.corpus_builder import chunk_paragraphs


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"


DEFAULT_INPUT = DATA_DIR / "web_crawl" / "health_pages.jsonl"
DEFAULT_REFERENCE_CHUNKS = DATA_DIR / "reference_chunks.jsonl"
DEFAULT_SOURCE_CATALOG = DATA_DIR / "source_catalog.csv"

TOPIC_KEYWORDS = {
    "menstrual": "menstrual_reproductive_core",
    "period": "menstrual_reproductive_core",
    "pregnancy": "pregnancy_fertility",
    "fertility": "pregnancy_fertility",
    "ovulation": "menstrual_reproductive_core",
    "breastfeeding": "postpartum_breastfeeding",
    "postpartum": "postpartum_breastfeeding",
    "pcos": "pcos_endocrine",
    "endometriosis": "endometriosis",
    "fibroid": "structural_uterine",
    "fibroids": "structural_uterine",
    "pid": "infection_sti",
    "sti": "infection_sti",
    "contraception": "contraception",
    "thyroid": "endocrine",
    "hormone": "endocrine",
    "perimenopause": "menopause_perimenopause",
    "menopause": "menopause_perimenopause",
}
MIN_CONTENT_CHARS = 150
SOURCE_CATALOG_FIELDS = [
    "source_id",
    "title",
    "organization",
    "url",
    "country",
    "topic_tags",
    "source_tier",
    "document_type",
    "publication_date",
    "access_date",
    "last_checked_date",
    "license_status",
    "trainable_for_model_flag",
    "retrieval_only_flag",
    "notes",
]


def parse_args():
    parser = argparse.ArgumentParser(description="Ingest crawled women-health pages into training references.")
    parser.add_argument(
        "--input",
        default=str(DEFAULT_INPUT),
        help="Input crawl JSONL file",
    )
    parser.add_argument(
        "--source-catalog",
        default=str(DEFAULT_SOURCE_CATALOG),
        help="Path to source_catalog.csv",
    )
    parser.add_argument(
        "--reference-chunks",
        default=str(DEFAULT_REFERENCE_CHUNKS),
        help="Path to reference_chunks.jsonl",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append to existing reference chunk file (default overwrites)",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=1200,
        help="Max chars per chunk",
    )
    parser.add_argument(
        "--min-chars",
        type=int,
        default=MIN_CONTENT_CHARS,
        help="Skip rows with less than this many cleaned characters",
    )
    parser.add_argument("--dry-run", action="store_true", help="Plan only; do not write outputs")
    return parser.parse_args()


def load_jsonl(path: Path):
    rows = []
    for line_no, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_no} invalid JSON: {exc}") from exc
    return rows


def load_reference_chunks(path: Path):
    if not path.exists():
        return []
    return load_jsonl(path)


def read_source_catalog(path: Path):
    if not path.exists():
        raise SystemExit(f"source catalog not found: {path}")
    rows = []
    with path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    return rows


def write_source_catalog(path: Path, rows):
    if not rows:
        return
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=SOURCE_CATALOG_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def existing_ids(rows):
    ids = set(row["source_id"] for row in rows if row.get("source_id"))
    return ids


def next_source_id(existing: set[str]):
    nums = []
    for source_id in existing:
        m = re.match(r"SRC(\d+)$", source_id)
        if m:
            nums.append(int(m.group(1)))
    return f"SRC{max(nums, default=0) + 1:03d}"


def infer_domain(source: str) -> str:
    host = source.lower()
    if "who.int" in host:
        return "WHO"
    if "cdc.gov" in host:
        return "CDC"
    if "acog.org" in host:
        return "ACOG"
    if "womenshealth.gov" in host:
        return "Office on Women's Health"
    if "nichd.nih.gov" in host:
        return "NICHD"
    if "nhs.uk" in host:
        return "NHS"
    if "nice.org.uk" in host:
        return "NICE"
    if "medlineplus.gov" in host:
        return "MedlinePlus"
    if "mayoclinic.org" in host:
        return "Mayo Clinic"
    if "nih.gov" in host:
        return "NIH"
    return "web"


def infer_topics(url: str, title: str) -> list[str]:
    text = f"{url} {title}".lower()
    topics = []
    for key, topic in TOPIC_KEYWORDS.items():
        if key in text and topic not in topics:
            topics.append(topic)
    if not topics:
        topics = ["women_health_general"]
    # Keep unique order + normalize
    return topics


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def chunk_text(text: str, max_chars: int):
    return chunk_paragraphs([p for p in text.split("\n") if p.strip()], max_chars=max_chars)


def content_hash(url: str, content: str) -> str:
    return hashlib.sha1((url + "\n" + content).encode("utf-8")).hexdigest()


def main():
    args = parse_args()
    input_path = Path(args.input)
    source_catalog_path = Path(args.source_catalog)
    reference_chunks_path = Path(args.reference_chunks)

    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    crawled_rows = load_jsonl(input_path)
    if not crawled_rows:
        print("No crawl rows found.")
        return

    source_rows = read_source_catalog(source_catalog_path)
    existing_source_ids = existing_ids(source_rows)
    source_by_id = {row["source_id"]: row for row in source_rows if row.get("source_id")}
    existing_rows = load_reference_chunks(reference_chunks_path)
    existing_chunk_ids = {row["chunk_id"] for row in existing_rows}
    existing_content_hashes = {row.get("content_sha1") for row in existing_rows if row.get("content_sha1")}

    # Build an URL index to avoid duplicate source rows
    existing_urls = {row["url"]: row["source_id"] for row in source_rows if row.get("url")}

    new_source_rows = []
    new_chunk_rows = []
    skipped_empty = 0
    skipped_too_short = 0
    skipped_existing = 0
    topic_cache = {}
    now = datetime.utcnow().date().isoformat()

    for row in crawled_rows:
        url = (row.get("canonical_url") or row.get("url") or "").strip()
        raw_title = (row.get("title") or "").strip()
        content = clean_text((row.get("content") or "").strip())
        if not url or not content:
            skipped_empty += 1
            continue
        if len(content) < args.min_chars:
            skipped_too_short += 1
            continue

        url_h = content_hash(url, content)
        if url_h in existing_content_hashes:
            skipped_existing += 1
            continue

        source_id = existing_urls.get(url)
        if not source_id:
            source_id = next_source_id(existing_source_ids)
            existing_source_ids.add(source_id)
            existing_urls[url] = source_id

            path = urlparse(url).path.lower()
            source_topics = infer_topics(f"{path} {raw_title}", raw_title)
            # Stable ordering for source topics
            topic_str = ";".join(dict.fromkeys(source_topics))
            source_row = {
                "source_id": source_id,
                "title": raw_title or f"Crawled Page {source_id}",
                "organization": infer_domain(url),
                "url": url,
                "country": "INTL",
                "topic_tags": topic_str,
                "source_tier": "tier2",
                "document_type": "web_scrape",
                "publication_date": row.get("publication_date", "").strip(),
                "access_date": now,
                "last_checked_date": now,
                "license_status": "retrieval_only",
                "trainable_for_model_flag": "false",
                "retrieval_only_flag": "true",
                "notes": "Web-scraped source; needs evidence review before direct clinical claims.",
            }
            source_rows.append(source_row)
            source_by_id[source_id] = source_row
            new_source_rows.append(source_id)
        else:
            source_row = source_by_id.get(source_id)

        chunk_topics = topic_cache.get(source_id)
        if not chunk_topics:
            source_row = source_by_id.get(source_id)
            topic_cache[source_id] = (
                source_row["topic_tags"].split(";") if source_row is not None else ["women_health_general"]
            )
        chunks = chunk_text(content, args.max_chars)
        for idx, chunk in enumerate(chunks, 1):
            chunk_id = f"{source_id}_{idx:03d}"
            if chunk_id in existing_chunk_ids:
                continue
            new_chunk_rows.append(
                {
                    "chunk_id": chunk_id,
                    "source_id": source_id,
                    "topic_tags": topic_cache[source_id],
                    "claim_summary": chunk[:160],
                    "text": chunk,
                    "citability": "medium",
                    "publication_date": source_row.get("publication_date", "") if source_row else "",
                    "license_status": "retrieval_only",
                    "content_sha1": url_h,
                    "source_url": url,
                    "title": raw_title or "Untitled",
                    "accessed_at": row.get("fetched_at") or datetime.utcnow().isoformat(),
                }
            )

    print(
        f"Crawled rows: {len(crawled_rows)}; new sources: {len(new_source_rows)}; new chunks: {len(new_chunk_rows)}"
    )
    print(
        f"Skipped rows: empty={skipped_empty}, short={skipped_too_short}, duplicate-content={skipped_existing}"
    )
    if args.dry_run:
        print("DRY RUN - no files written.")
        return

    if new_source_rows:
        write_source_catalog(source_catalog_path, source_rows)
    all_chunks = existing_rows + new_chunk_rows
    if not args.append and reference_chunks_path.exists():
        # explicit overwrite mode keeps all existing rows plus new rows (never deletes data by default).
        reference_chunks_path.write_text(
            "\n".join(json.dumps(row, ensure_ascii=True) for row in all_chunks) + ("\n" if all_chunks else "")
        )
    elif args.append:
        with reference_chunks_path.open("a") as f:
            for row in new_chunk_rows:
                f.write(json.dumps(row, ensure_ascii=True) + "\n")
    else:
        # default behavior same as append mode with one rewrite path
        reference_chunks_path.write_text(
            "\n".join(json.dumps(row, ensure_ascii=True) for row in all_chunks) + ("\n" if all_chunks else "")
        )

    # Persist a reproducible manifest used by training notebooks.
    manifest = {
        "input_file": str(input_path),
        "run_date": datetime.utcnow().isoformat(),
        "source_catalog": str(source_catalog_path),
        "reference_chunks": str(reference_chunks_path),
        "new_sources": len(new_source_rows),
        "new_chunks": len(new_chunk_rows),
        "skipped": {
            "empty": skipped_empty,
            "too_short": skipped_too_short,
            "existing_content_hash": skipped_existing,
        },
        "topic_keywords_used": list(TOPIC_KEYWORDS.keys()),
    }
    (DATA_DIR / "web_crawl_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=True))

    if new_source_rows:
        print(f"Added {len(new_source_rows)} source catalog rows.")
    print(f"Added {len(new_chunk_rows)} reference chunks.")
    print(f"Wrote manifest to: {DATA_DIR / 'web_crawl_manifest.json'}")


if __name__ == "__main__":
    main()
