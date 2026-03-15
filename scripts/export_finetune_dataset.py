#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
OUTPUT_DIR = DATA_DIR / "training_exports"


REVIEW_OK = {"human_reviewed", "clinician_reviewed"}


def load_jsonl(path: Path):
    if not path.exists():
        raise SystemExit(f"Input file not found: {path}")
    records = []
    for line_no, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"{path}:{line_no} invalid json: {exc}") from exc
    return records


def write_jsonl(path: Path, rows):
    if not rows:
        path.write_text("")
        return
    path.write_text("\n".join(json.dumps(row, ensure_ascii=True) for row in rows) + "\n")


def build_chat_row(row):
    system_prompt = (
        "You are a women-centric educational assistant. "
        "Use safety-first behavior. Never diagnose. "
        "If danger signs are present, route to medical care and include clear follow-up steps."
    )
    user_payload = {
        "question": row.get("raw_input"),
        "extracted_features": row.get("extracted_features", {}),
        "citations_used": row.get("citations", []),
        "risk_level_target": row.get("risk_level"),
    }
    assistant_output = (row.get("assistant_output") or "").strip()
    return {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=True)},
            {
                "role": "assistant",
                "content": assistant_output,
            },
        ],
    }


def build_completion_row(row):
    features = row.get("extracted_features", {})
    prompt = (
        "SYSTEM: You are a women-centric educational assistant. "
        "Use safety-first responses and cite uncertainty.\n"
        f"Input: {row.get('raw_input')}\n"
        f"Extracted features: {json.dumps(features, ensure_ascii=True)}\n"
        f"Target risk: {row.get('risk_level')}\n"
        "Assistant:"
    )
    completion = (row.get("assistant_output") or "").strip().replace("\n", "\\n")
    return {"prompt": prompt, "completion": completion}


def build_metadata_row(row, source_file):
    return {
        "interaction_id": row.get("interaction_id"),
        "data_origin": row.get("data_origin"),
        "split_source": source_file,
        "review_status": row.get("review_status"),
        "risk_level": row.get("risk_level"),
        "raw_input": row.get("raw_input"),
        "normalized_case_summary": row.get("normalized_case_summary"),
        "human_reviewed": row.get("human_reviewed", False),
        "care_recommendation": row.get("care_recommendation"),
        "abstained": row.get("abstained"),
        "citations": row.get("citations", []),
        "label": row.get("risk_level"),
        "split": row.get("split"),
    }


def main():
    parser = argparse.ArgumentParser(description="Export reviewed interaction records for fine-tuning.")
    parser.add_argument(
        "--source",
        nargs="+",
        default=[
            str(DATA_DIR / "train_interactions.jsonl"),
            str(DATA_DIR / "validation_interactions.jsonl"),
            str(DATA_DIR / "safety_train.jsonl"),
        ],
        help="Input JSONL interaction files (default: train + validation + safety splits)",
    )
    parser.add_argument(
        "--include-raw",
        action="store_true",
        help="Also include interaction_examples.jsonl in export.",
    )
    parser.add_argument(
        "--require-review",
        action="store_true",
        help="Skip non-reviewed rows even if split files contain unreviewed data.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(OUTPUT_DIR),
        help="Directory where exported files are written.",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    chat_rows = []
    completion_rows = []
    metadata_rows = []

    total_seen = 0
    total_exported = 0

    source_paths = args.source
    if args.include_raw and str(DATA_DIR / "interaction_examples.jsonl") not in source_paths:
        source_paths = [str(DATA_DIR / "interaction_examples.jsonl")] + source_paths

    for source in source_paths:
        source_path = Path(source)
        rows = load_jsonl(source_path)
        for row in rows:
            total_seen += 1
            if args.require_review and row.get("review_status") not in REVIEW_OK:
                continue
            chat_rows.append(build_chat_row(row))
            completion_rows.append(build_completion_row(row))
            metadata_rows.append(build_metadata_row(row, source_path.name))
            total_exported += 1

    if total_exported == 0:
        print(
            "No rows exported.\n"
            "Default source set includes all interaction files; if all rows are pending review, "
            "use exported rows with --require-review=false (default) during early prototyping, "
            "and --require-review=true once review status is ready."
        )
        return

    write_jsonl(output_dir / "interaction_finetune_chat.jsonl", chat_rows)
    write_jsonl(output_dir / "interaction_finetune_completion.jsonl", completion_rows)
    write_jsonl(output_dir / "interaction_finetune_metadata.jsonl", metadata_rows)

    summary = {
        "source_files": [str(Path(p)) for p in args.source],
        "total_seen": total_seen,
        "total_exported": total_exported,
        "review_gate_enabled": args.require_review,
        "output_dir": str(output_dir),
        "files": [
            str(output_dir / "interaction_finetune_chat.jsonl"),
            str(output_dir / "interaction_finetune_completion.jsonl"),
            str(output_dir / "interaction_finetune_metadata.jsonl"),
        ],
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
