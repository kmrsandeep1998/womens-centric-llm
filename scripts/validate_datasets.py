#!/usr/bin/env python3

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"


def load_jsonl(path: Path):
    records = []
    for line_no, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path.name}:{line_no}: invalid JSON: {exc}") from exc
    return records


def load_csv(path: Path):
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def assert_keys(record_name, record, required):
    missing = [key for key in required if key not in record]
    if missing:
        raise ValueError(f"{record_name}: missing keys: {', '.join(missing)}")


def validate_source_catalog():
    path = DATA_DIR / "source_catalog.csv"
    rows = load_csv(path)
    required = [
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
    ids = set()
    for i, row in enumerate(rows, 2):
        assert_keys(f"{path.name}:{i}", row, required)
        source_id = row["source_id"]
        if source_id in ids:
            raise ValueError(f"{path.name}:{i}: duplicate source_id {source_id}")
        ids.add(source_id)
    return ids


def validate_reference_chunks(source_ids):
    path = DATA_DIR / "reference_chunks.jsonl"
    rows = load_jsonl(path)
    required = [
        "chunk_id",
        "source_id",
        "topic_tags",
        "claim_summary",
        "text",
        "citability",
        "publication_date",
        "license_status",
    ]
    ids = set()
    for i, row in enumerate(rows, 1):
        assert_keys(f"{path.name}:{i}", row, required)
        if row["chunk_id"] in ids:
            raise ValueError(f"{path.name}:{i}: duplicate chunk_id {row['chunk_id']}")
        ids.add(row["chunk_id"])
        if row["source_id"] not in source_ids:
            raise ValueError(f"{path.name}:{i}: unknown source_id {row['source_id']}")
        if not isinstance(row["topic_tags"], list):
            raise ValueError(f"{path.name}:{i}: topic_tags must be a list")


def validate_structured_cases():
    path = DATA_DIR / "structured_cases.jsonl"
    rows = load_jsonl(path)
    required = [
        "case_id",
        "data_origin",
        "review_status",
        "life_stage",
        "age_years",
        "pregnancy_test_result",
        "known_conditions",
        "symptoms",
        "red_flags",
        "output_labels",
        "risk_level",
        "care_recommendation",
    ]
    ids = set()
    allowed_risks = {
        "normal_variation",
        "routine_review",
        "prompt_medical_review",
        "urgent_care",
        "emergency_care",
    }
    for i, row in enumerate(rows, 1):
        assert_keys(f"{path.name}:{i}", row, required)
        if row["case_id"] in ids:
            raise ValueError(f"{path.name}:{i}: duplicate case_id {row['case_id']}")
        ids.add(row["case_id"])
        if row["risk_level"] not in allowed_risks:
            raise ValueError(f"{path.name}:{i}: invalid risk_level {row['risk_level']}")
        for field in ["known_conditions", "symptoms", "red_flags", "output_labels"]:
            if not isinstance(row[field], list):
                raise ValueError(f"{path.name}:{i}: {field} must be a list")


def validate_interactions(source_ids):
    path = DATA_DIR / "interaction_examples.jsonl"
    rows = load_jsonl(path)
    required = [
        "interaction_id",
        "data_origin",
        "review_status",
        "raw_input",
        "normalized_case_summary",
        "extracted_features",
        "assistant_output",
        "citations",
        "risk_level",
        "care_recommendation",
        "abstained",
    ]
    ids = set()
    for i, row in enumerate(rows, 1):
        assert_keys(f"{path.name}:{i}", row, required)
        if row["interaction_id"] in ids:
            raise ValueError(f"{path.name}:{i}: duplicate interaction_id {row['interaction_id']}")
        ids.add(row["interaction_id"])
        if not isinstance(row["extracted_features"], dict):
            raise ValueError(f"{path.name}:{i}: extracted_features must be an object")
        if not isinstance(row["citations"], list):
            raise ValueError(f"{path.name}:{i}: citations must be a list")
        if isinstance(row.get("follow_up_questions"), list) and any(
            not isinstance(item, str) for item in row["follow_up_questions"]
        ):
            raise ValueError(f"{path.name}:{i}: follow_up_questions must be a list of strings")
        unknown = [c for c in row["citations"] if c not in source_ids]
        if unknown:
            raise ValueError(f"{path.name}:{i}: unknown citations: {', '.join(unknown)}")


def _validate_dataset_records(path: Path, required: list, allowed_risks: set, source_ids):
    rows = load_jsonl(path)
    ids = set()
    for i, row in enumerate(rows, 1):
        assert_keys(f"{path.name}:{i}", row, required)
        record_id = row.get("interaction_id") or row.get("queue_id") or row.get("case_id")
        if record_id in ids:
            raise ValueError(f"{path.name}:{i}: duplicate id {record_id}")
        ids.add(record_id)
        if row.get("risk_level") and row["risk_level"] not in allowed_risks:
            raise ValueError(f"{path.name}:{i}: invalid risk_level {row['risk_level']}")
        if row.get("extracted_features") is not None and not isinstance(
            row["extracted_features"], dict
        ):
            raise ValueError(f"{path.name}:{i}: extracted_features must be an object")
        if row.get("citations") is not None and not isinstance(row["citations"], list):
            raise ValueError(f"{path.name}:{i}: citations must be a list")
        if row.get("follow_up_questions") is not None and any(
            not isinstance(item, str) for item in row["follow_up_questions"]
        ):
            raise ValueError(f"{path.name}:{i}: follow_up_questions must be a list of strings")
        if row.get("abstained") is not None and not isinstance(row.get("abstained"), bool):
            raise ValueError(f"{path.name}:{i}: abstained must be boolean")
        citations = row.get("citations")
        if citations:
            unknown = [c for c in citations if c not in source_ids]
            if unknown:
                raise ValueError(f"{path.name}:{i}: unknown citations: {', '.join(unknown)}")


def validate_review_queue():
    path = DATA_DIR / "review_queue.jsonl"
    if not path.exists():
        return
    rows = load_jsonl(path)
    required = [
        "queue_id",
        "origin_file",
        "origin_record_id",
        "severity",
        "reason",
        "status",
        "created_at",
    ]
    ids = set()
    for i, row in enumerate(rows, 1):
        assert_keys(f"{path.name}:{i}", row, required)
        if row["queue_id"] in ids:
            raise ValueError(f"{path.name}:{i}: duplicate queue_id {row['queue_id']}")
        ids.add(row["queue_id"])
        if row["severity"] not in {"low", "medium", "high", "critical"}:
            raise ValueError(f"{path.name}:{i}: invalid severity {row['severity']}")
        if row["status"] not in {"open", "in_review", "resolved", "blocked"}:
            raise ValueError(f"{path.name}:{i}: invalid status {row['status']}")


def validate_interaction_splits(source_ids):
    allowed_risks = {
        "normal_variation",
        "routine_review",
        "prompt_medical_review",
        "urgent_care",
        "emergency_care",
    }
    required = [
        "interaction_id",
        "data_origin",
        "review_status",
        "raw_input",
        "normalized_case_summary",
        "extracted_features",
        "assistant_output",
        "citations",
        "risk_level",
        "care_recommendation",
        "abstained",
        "human_reviewed",
        "split",
    ]
    for filename in [
        "train_interactions.jsonl",
        "validation_interactions.jsonl",
        "safety_train.jsonl",
    ]:
        path = DATA_DIR / filename
        if not path.exists():
            continue
        rows = load_jsonl(path)
        if not rows:
            continue
        _validate_dataset_records(path, required, allowed_risks, source_ids)
        valid_splits = {"train", "validation", "safety_train"}
        for i, row in enumerate(rows, 1):
            if row["split"] not in valid_splits:
                raise ValueError(f"{path.name}:{i}: invalid split {row['split']}")
            if row["human_reviewed"] not in (True, False):
                raise ValueError(f"{path.name}:{i}: human_reviewed must be boolean")


def validate_benchmarks():
    path = DATA_DIR / "benchmark_eval_set.jsonl"
    rows = load_jsonl(path)
    required = [
        "benchmark_id",
        "scenario",
        "input",
        "expected_labels",
        "expected_risk",
        "must_not_do",
        "priority",
    ]
    ids = set()
    for i, row in enumerate(rows, 1):
        assert_keys(f"{path.name}:{i}", row, required)
        if row["benchmark_id"] in ids:
            raise ValueError(f"{path.name}:{i}: duplicate benchmark_id {row['benchmark_id']}")
        ids.add(row["benchmark_id"])
        if not isinstance(row["expected_labels"], list):
            raise ValueError(f"{path.name}:{i}: expected_labels must be a list")
        if not isinstance(row["must_not_do"], list):
            raise ValueError(f"{path.name}:{i}: must_not_do must be a list")


def main():
    source_ids = validate_source_catalog()
    validate_reference_chunks(source_ids)
    validate_structured_cases()
    validate_interactions(source_ids)
    validate_interaction_splits(source_ids)
    validate_review_queue()
    validate_benchmarks()
    print("All dataset files validated successfully.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"VALIDATION ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
