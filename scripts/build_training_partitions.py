#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"


VALID_REVIEW_STATUS = {"human_reviewed", "clinician_reviewed"}
HIGH_RISK = {"urgent_care", "emergency_care"}


def load_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def write_jsonl(path: Path, rows):
    path.write_text("\n".join(json.dumps(row, ensure_ascii=True) for row in rows) + ("\n" if rows else ""))


def stable_split_key(value: str):
    digest = hashlib.md5(value.encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def build_partitions(rows, args):
    train = []
    validation = []
    safety = []
    review_queue = []

    for row in rows:
        if row.get("review_status") not in VALID_REVIEW_STATUS:
            review_queue.append(
                {
                    "queue_id": f"RQAUTO{len(review_queue)+1:03d}",
                    "origin_file": "data/interaction_examples.jsonl",
                    "origin_record_id": row["interaction_id"],
                    "severity": "high" if row.get("risk_level") in HIGH_RISK else "medium",
                    "reason": "Unreviewed case requiring quality routing",
                    "status": "open",
                    "created_at": args.now,
                }
            )
            continue

        row = dict(row)
        row["human_reviewed"] = bool(
            row.get("human_reviewed", False)
            if row.get("review_status") in VALID_REVIEW_STATUS
            else False
        )

        if row.get("risk_level") in HIGH_RISK or (
            row.get("risk_level") == "prompt_medical_review"
            and row.get("risk_findings", [])
        ):
            row["split"] = "safety_train"
            safety.append(row)
            continue

        bucket = stable_split_key(row["interaction_id"]) % 5
        row["split"] = "validation" if bucket == 0 else "train"
        if row["split"] == "validation":
            validation.append(row)
        else:
            train.append(row)

    return train, validation, safety, review_queue


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default=str(DATA_DIR / "interaction_examples.jsonl"),
        help="Source interaction examples JSONL",
    )
    parser.add_argument(
        "--now",
        default="2026-03-14",
        help="Review queue created_at timestamp",
    )
    args = parser.parse_args()

    source_path = Path(args.input)
    rows = load_jsonl(source_path)
    train, validation, safety, review_queue = build_partitions(rows, args)

    write_jsonl(DATA_DIR / "train_interactions.jsonl", train)
    write_jsonl(DATA_DIR / "validation_interactions.jsonl", validation)
    write_jsonl(DATA_DIR / "safety_train.jsonl", safety)
    write_jsonl(DATA_DIR / "review_queue.jsonl", review_queue)

    summary = {
        "source_interactions": len(rows),
        "train": len(train),
        "validation": len(validation),
        "safety_train": len(safety),
        "review_queue": len(review_queue),
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
