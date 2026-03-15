#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Set


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"


REQUIRED_KEYS = [
    "raw_input",
    "normalized_case_summary",
    "extracted_features",
    "assistant_output",
    "citations",
    "risk_level",
    "care_recommendation",
]


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows = []
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
    path.write_text("\n".join(json.dumps(r, ensure_ascii=True) for r in rows) + "\n")


def load_source_ids() -> Set[str]:
    catalog = DATA_DIR / "source_catalog.csv"
    if not catalog.exists():
        return set()
    lines = catalog.read_text().splitlines()
    if not lines:
        return set()
    header = lines[0].split(",")
    try:
        idx = header.index("source_id")
    except ValueError:
        return set()
    ids = set()
    for line in lines[1:]:
        row = line.split(",")
        if len(row) > idx:
            ids.add(row[idx].strip())
    return ids


def next_interaction_id(existing: List[Dict[str, Any]]) -> str:
    ids = []
    for row in existing:
        raw = str(row.get("interaction_id", ""))
        m = re.match(r"INT(\d+)", raw)
        if m:
            ids.append(int(m.group(1)))
    next_id = max(ids, default=0) + 1
    return f"INT{next_id:05d}"


def parse_args():
    parser = argparse.ArgumentParser(description="Ingest real reviewed cases into review_queue.jsonl.")
    parser.add_argument("--input", required=True, help="Input JSONL file with real cases.")
    parser.add_argument(
        "--output",
        default=str(DATA_DIR / "review_queue.jsonl"),
        help="Output review queue JSONL (default: data/review_queue.jsonl).",
    )
    parser.add_argument(
        "--data-origin",
        default="reviewed_annotation",
        help="data_origin value to attach to ingested rows.",
    )
    parser.add_argument(
        "--review-status",
        default="pending_human_review",
        choices=["pending_human_review", "human_reviewed", "clinician_reviewed", "rejected", "unknown"],
        help="review_status to attach to ingested rows.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    incoming = load_jsonl(input_path)
    if not incoming:
        raise SystemExit("No rows found in input.")

    existing = load_jsonl(output_path)
    source_ids = load_source_ids()

    appended = 0
    for row in incoming:
        missing = [k for k in REQUIRED_KEYS if k not in row]
        if missing:
            raise SystemExit(f"Missing required keys in row: {missing}")
        if not isinstance(row.get("citations"), list) or not row["citations"]:
            raise SystemExit("Each row must include non-empty citations list.")
        unknown = [c for c in row["citations"] if c not in source_ids]
        if unknown:
            raise SystemExit(f"Unknown citation IDs: {unknown}")

        row["interaction_id"] = next_interaction_id(existing)
        row["data_origin"] = args.data_origin
        row["review_status"] = args.review_status
        row.setdefault("abstained", False)
        row.setdefault("human_reviewed", False)
        row.setdefault("clinician_reviewed", False)
        row.setdefault("split", "unknown")

        existing.append(row)
        appended += 1

    write_jsonl(output_path, existing)
    print(f"Appended {appended} rows to {output_path}")


if __name__ == "__main__":
    main()
