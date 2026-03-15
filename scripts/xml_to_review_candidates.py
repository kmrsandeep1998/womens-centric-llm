#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Dict, Any, List


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

TITLE_RE = re.compile(r"<article-title[^>]*>(.*?)</article-title>", re.DOTALL | re.IGNORECASE)
ABSTRACT_RE = re.compile(r"<abstract[^>]*>(.*?)</abstract>", re.DOTALL | re.IGNORECASE)
TAG_RE = re.compile(r"<[^>]+>")


def strip_tags(text: str) -> str:
    text = TAG_RE.sub(" ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


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


def write_jsonl(path: Path, rows: List[Dict[str, Any]]):
    path.write_text("\n".join(json.dumps(r, ensure_ascii=True) for r in rows) + ("\n" if rows else ""))


def next_interaction_id(existing: List[Dict[str, Any]]) -> str:
    ids = []
    for row in existing:
        raw = str(row.get("interaction_id", ""))
        m = re.match(r"INT(\d+)", raw)
        if m:
            ids.append(int(m.group(1)))
    next_id = max(ids, default=0) + 1
    return f"INT{next_id:05d}"


def load_candidates_map(path: Path) -> Dict[str, Dict[str, Any]]:
    mapping: Dict[str, Dict[str, Any]] = {}
    for row in load_jsonl(path):
        pmcid = row.get("pmcid")
        if pmcid:
            mapping[pmcid] = row
    return mapping


def load_source_catalog(path: Path) -> Dict[str, Dict[str, str]]:
    if not path.exists():
        return {}
    rows = {}
    with path.open() as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows[r.get("source_id")] = r
    return rows


def append_source_catalog(path: Path, new_rows: List[Dict[str, str]]):
    exists = path.exists()
    with path.open("a", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
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
            ],
        )
        if not exists:
            writer.writeheader()
        for row in new_rows:
            writer.writerow(row)


def main():
    parser = argparse.ArgumentParser(description="Convert Europe PMC XML to review candidates.")
    parser.add_argument("--xml-dir", default=str(DATA_DIR / "real_data_fulltext"))
    parser.add_argument("--candidates", default=str(DATA_DIR / "real_data_candidates.jsonl"))
    parser.add_argument("--output", default=str(DATA_DIR / "interaction_examples.jsonl"))
    parser.add_argument("--max-files", type=int, default=0, help="Limit XML files (0 = all).")
    parser.add_argument("--now", default="2026-03-15")
    args = parser.parse_args()

    xml_dir = Path(args.xml_dir)
    files = sorted(xml_dir.glob("*.xml"))
    if args.max_files:
        files = files[: args.max_files]

    candidates = load_candidates_map(Path(args.candidates))
    source_catalog_path = DATA_DIR / "source_catalog.csv"
    existing_sources = load_source_catalog(source_catalog_path)

    interactions = load_jsonl(Path(args.output))
    new_sources: List[Dict[str, str]] = []

    created = 0
    for xml_path in files:
        pmcid = xml_path.stem
        meta = candidates.get(pmcid, {})
        title_match = TITLE_RE.search(xml_path.read_text(errors="ignore"))
        title = strip_tags(title_match.group(1)) if title_match else meta.get("title") or pmcid

        abstract_match = ABSTRACT_RE.search(xml_path.read_text(errors="ignore"))
        abstract = strip_tags(abstract_match.group(1)) if abstract_match else ""

        # Ensure source exists.
        source_id = f"PMC_{pmcid}"
        if source_id not in existing_sources:
            license_id = (meta.get("europe_pmc_license") or "unknown").lower()
            trainable = "true" if license_id in {"cc-by", "cc-by-4.0", "cc-by-sa", "cc0", "cc-by-nc"} else "false"
            new_sources.append(
                {
                    "source_id": source_id,
                    "title": title[:200],
                    "organization": "Europe PMC",
                    "url": f"https://europepmc.org/articles/{pmcid}",
                    "country": "global",
                    "topic_tags": "women_health",
                    "source_tier": "tier2",
                    "document_type": "journal_article",
                    "publication_date": str(meta.get("publication_year") or ""),
                    "access_date": args.now,
                    "last_checked_date": args.now,
                    "license_status": license_id or "unknown",
                    "trainable_for_model_flag": trainable,
                    "retrieval_only_flag": "true" if trainable == "false" else "false",
                    "notes": "Imported from Europe PMC XML",
                }
            )

        # Create a review candidate interaction.
        summary = title[:180]
        raw_input = f"Summarize the clinical guidance from this study: {title}."
        if abstract:
            raw_input = f"Based on this abstract, draft patient-friendly guidance: {abstract[:500]}"

        interactions.append(
            {
                "interaction_id": next_interaction_id(interactions),
                "data_origin": "reviewed_annotation",
                "review_status": "pending_human_review",
                "raw_input": raw_input,
                "normalized_case_summary": summary,
                "extracted_features": {},
                "assistant_output": "REVIEW_NEEDED: draft response required.",
                "citations": [source_id],
                "risk_level": "routine_review",
                "care_recommendation": "",
                "abstained": False,
            }
        )
        created += 1

    if new_sources:
        append_source_catalog(source_catalog_path, new_sources)

    write_jsonl(Path(args.output), interactions)
    print(f"Added {created} review candidates to {args.output}")
    if new_sources:
        print(f"Added {len(new_sources)} sources to {source_catalog_path}")


if __name__ == "__main__":
    main()
