#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

sys.path.insert(0, str(ROOT))
from local_ai.assistant import LocalWomensHealthAssistant


def _load_jsonl(path: Path):
    rows = []
    for line_no, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}: line {line_no} invalid json: {exc}") from exc
    return rows


def _load_source_ids():
    path = DATA_DIR / "source_catalog.csv"
    source_ids = set()
    lines = path.read_text().splitlines()
    if not lines:
        return source_ids
    header = lines[0].split(",")
    try:
        idx = header.index("source_id")
    except ValueError:
        return source_ids
    for line in lines[1:]:
        row = line.split(",")
        if len(row) <= idx:
            continue
        source_ids.add(row[idx].strip())
    return source_ids


def _next_interaction_id(existing):
    ids = []
    for row in existing:
        raw_id = str(row.get("interaction_id", ""))
        match = re.match(r"INT(\d+)", raw_id)
        if match:
            ids.append(int(match.group(1)))
    next_id = max(ids, default=0) + 1
    return f"INT{next_id:03d}"


def _build_summary(raw_input, features, hint):
    if hint:
        return hint
    parts = []
    if features.get("late_period"):
        parts.append("late period pattern")
    if features.get("postpartum"):
        parts.append("postpartum context")
    if features.get("breastfeeding"):
        parts.append("breastfeeding context")
    if features.get("bleeding_after_sex"):
        parts.append("postcoital bleeding")
    if features.get("very_heavy_bleeding"):
        parts.append("heavy bleeding")
    if features.get("pregnancy_test_result") and features["pregnancy_test_result"] != "unknown":
        parts.append(f"pregnancy_test={features['pregnancy_test_result']}")
    if not parts:
        return raw_input[:140]
    return "; ".join(parts)


def _filter_citations(citations, source_ids):
    cleaned = []
    for item in citations:
        if item in source_ids and item not in cleaned:
            cleaned.append(item)
    if not cleaned:
        cleaned = ["SRC006", "SRC007"] if "SRC006" in source_ids else ["SRC001"]
    return cleaned


def _has_existing_raw(existing, raw_input):
    return any(row.get("raw_input", "").strip().lower() == raw_input.strip().lower() for row in existing)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--templates",
        default=str(DATA_DIR / "interaction_expansion_templates.jsonl"),
        help="JSONL file containing template inputs to expand",
    )
    parser.add_argument(
        "--output",
        default=str(DATA_DIR / "interaction_examples.jsonl"),
        help="Interaction dataset file to update",
    )
    parser.add_argument(
        "--corpus",
        default=str(ROOT / "artifacts" / "knowledge_corpus.jsonl"),
        help="Knowledge corpus JSONL used by the local assistant",
    )
    parser.add_argument("--limit", type=int, default=0, help="Max number of generated records (0 means all)")
    parser.add_argument(
        "--review-status",
        default="pending_human_review",
        choices=["pending_human_review", "human_reviewed", "clinician_reviewed", "unknown"],
        help="review_status for generated records",
    )
    parser.add_argument("--dry-run", action="store_true", help="Generate preview without writing file")
    return parser.parse_args()


def main():
    args = parse_args()
    template_path = Path(args.templates)
    output_path = Path(args.output)
    corpus_path = Path(args.corpus)

    if not template_path.exists():
        raise SystemExit(f"Template file not found: {template_path}")
    if not output_path.exists():
        raise SystemExit(f"Interaction file not found: {output_path}")
    if not corpus_path.exists():
        raise SystemExit(
            f"Corpus not found: {corpus_path}. Run `python3 scripts/build_knowledge_corpus.py` first."
        )

    templates = _load_jsonl(template_path)
    records = _load_jsonl(output_path)
    source_ids = _load_source_ids()
    assistant = LocalWomensHealthAssistant(corpus_path)

    generated = []
    for row in templates:
        if args.limit and len(generated) >= args.limit:
            break
        raw_input = (row.get("raw_input") or "").strip()
        if not raw_input:
            continue
        if _has_existing_raw(records + generated, raw_input):
            continue

        output = assistant.answer(raw_input)
        features = output.get("extracted_features", {})
        summary = _build_summary(raw_input, features, row.get("summary_hint") or "")
        citation_candidates = row.get("citations") or ["SRC006", "SRC007"]
        citations = _filter_citations(citation_candidates, source_ids)
        risk_level = row.get("risk_level_override") or output.get("risk_level")

        generated.append(
            {
                "interaction_id": _next_interaction_id(records + generated),
                "data_origin": "synthetic_bootstrap",
                "review_status": args.review_status,
                "raw_input": raw_input,
                "normalized_case_summary": summary,
                "extracted_features": features,
                "assistant_output": output.get("answer"),
                "citations": citations,
                "risk_level": risk_level,
                "care_recommendation": output.get("care_recommendation"),
                "abstained": False,
            }
        )

    if not generated:
        print("No new interaction records generated.")
        return

    print("Generated interaction records:")
    for row in generated:
        print(f"{row['interaction_id']} | {row['risk_level']} | {row['normalized_case_summary']}")

    if args.dry_run:
        print(f"DRY RUN only - {len(generated)} records preview, no file write.")
        return

    output_path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=True) for row in records + generated) + "\n"
    )
    print(f"Wrote {len(generated)} new records to {output_path}")


if __name__ == "__main__":
    main()
