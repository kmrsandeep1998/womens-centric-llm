#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"


VALID_STATUSES = {"pending_human_review", "human_reviewed", "clinician_reviewed", "unknown"}


def load_jsonl(path: Path):
    rows = []
    for line_no, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"{path}:{line_no} invalid json: {exc}") from exc
    return rows


def write_jsonl(path: Path, rows):
    if not rows:
        path.write_text("")
        return
    path.write_text("\n".join(json.dumps(row, ensure_ascii=True) for row in rows) + "\n")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Promote interaction rows to a target review_status for prototyping."
    )
    parser.add_argument(
        "--input",
        default=str(DATA_DIR / "interaction_examples.jsonl"),
        help="Input interaction file",
    )
    parser.add_argument(
        "--output",
        default="",
        help="Optional output file; defaults to in-place update of --input",
    )
    parser.add_argument(
        "--status",
        required=True,
        choices=sorted(VALID_STATUSES),
        help="Target review_status value",
    )
    parser.add_argument(
        "--max-records",
        type=int,
        default=0,
        help="Only update first N matching records (0 = all)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional seed for random sampling",
    )
    parser.add_argument(
        "--random-sample",
        action="store_true",
        help="Sample rows randomly instead of first-N order",
    )
    parser.add_argument(
        "--from-status",
        default="",
        help="Only update rows with this current review_status (empty = all)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    rows = load_jsonl(input_path)
    if not rows:
        print("No rows found.")
        return

    candidate_indexes = [
        idx
        for idx, row in enumerate(rows)
        if not args.from_status or row.get("review_status") == args.from_status
    ]

    if not candidate_indexes:
        print(
            "No candidate rows found"
            + (f" for from-status={args.from_status}" if args.from_status else "")
        )
        return

    limit = len(candidate_indexes) if args.max_records <= 0 else min(args.max_records, len(candidate_indexes))
    selected = candidate_indexes
    if args.random_sample:
        rng = random.Random(args.seed)
        rng.shuffle(selected)
    selected = set(selected[:limit])

    updated = 0
    for idx in range(len(rows)):
        if idx in selected:
            rows[idx]["review_status"] = args.status
            rows[idx]["human_reviewed"] = args.status in {"human_reviewed", "clinician_reviewed"}
            rows[idx]["clinician_reviewed"] = args.status == "clinician_reviewed"
            updated += 1

    output_path = Path(args.output) if args.output else input_path
    if output_path.exists() is False and args.output:
        output_path.parent.mkdir(parents=True, exist_ok=True)

    write_jsonl(output_path, rows)
    print(f"Updated {updated} rows to review_status={args.status}.")
    print(f"Wrote {len(rows)} rows to {output_path}.")


if __name__ == "__main__":
    main()
