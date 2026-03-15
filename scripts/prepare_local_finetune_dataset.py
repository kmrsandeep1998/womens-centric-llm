#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
sys.path.insert(0, str(ROOT))

from local_ai.assistant import LocalWomensHealthAssistant


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
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r, ensure_ascii=True) for r in rows) + ("\n" if rows else ""))


def build_prompt(system_text: str, raw_input: str, features: dict, risk_level: str) -> str:
    return (
        "SYSTEM: "
        + system_text.strip()
        + "\nInput: "
        + raw_input.strip()
        + "\nExtracted features: "
        + json.dumps(features, ensure_ascii=True)
        + "\nTarget risk: "
        + (risk_level or "unknown")
        + "\nAssistant:"
    )


def parse_args():
    parser = argparse.ArgumentParser(description="Prepare prompt/completion JSONL for local fine-tuning.")
    parser.add_argument(
        "--train",
        default=str(DATA_DIR / "train_interactions.jsonl"),
        help="Train split JSONL.",
    )
    parser.add_argument(
        "--validation",
        default=str(DATA_DIR / "validation_interactions.jsonl"),
        help="Validation split JSONL.",
    )
    parser.add_argument(
        "--use-exported",
        action="store_true",
        help="Use exported completion + metadata to build train/valid splits.",
    )
    parser.add_argument(
        "--exported-completion",
        default=str(DATA_DIR / "training_exports" / "interaction_finetune_completion.jsonl"),
        help="Completion export JSONL (prompt/completion).",
    )
    parser.add_argument(
        "--exported-metadata",
        default=str(DATA_DIR / "training_exports" / "interaction_finetune_metadata.jsonl"),
        help="Metadata export JSONL (with split info).",
    )
    parser.add_argument(
        "--system-prompt",
        default=str(ROOT / "prompts" / "ollama_system_prompt.txt"),
        help="System prompt to embed in each training prompt.",
    )
    parser.add_argument(
        "--output-train",
        default=str(DATA_DIR / "training_exports" / "local_train.jsonl"),
        help="Output train JSONL (prompt/completion).",
    )
    parser.add_argument(
        "--output-valid",
        default=str(DATA_DIR / "training_exports" / "local_valid.jsonl"),
        help="Output validation JSONL (prompt/completion).",
    )
    parser.add_argument(
        "--fill-missing",
        action="store_true",
        help="Generate missing completions with the local assistant.",
    )
    parser.add_argument(
        "--corpus",
        default=str(ROOT / "artifacts" / "knowledge_corpus.jsonl"),
        help="Knowledge corpus used by the local assistant for fill-missing.",
    )
    parser.add_argument("--max-train", type=int, default=0, help="Limit number of train rows (0 = all).")
    parser.add_argument("--max-valid", type=int, default=0, help="Limit number of validation rows (0 = all).")
    return parser.parse_args()


def build_rows(rows, system_text: str, max_rows: int):
    output = []
    for row in rows:
        if max_rows and len(output) >= max_rows:
            break
        raw_input = (row.get("raw_input") or "").strip()
        completion = (row.get("assistant_output") or "").strip()
        if not raw_input or not completion:
            continue
        features = row.get("extracted_features") or {}
        risk_level = row.get("risk_level") or row.get("label") or "unknown"
        prompt = build_prompt(system_text, raw_input, features, risk_level)
        output.append({"prompt": prompt, "completion": completion})
    return output


def build_rows_from_exports(
    completion_rows,
    metadata_rows,
    max_train: int,
    max_valid: int,
    fill_missing: bool,
    assistant: LocalWomensHealthAssistant | None,
):
    if len(completion_rows) != len(metadata_rows):
        raise SystemExit("Export completion and metadata row counts do not match.")
    train_out = []
    valid_out = []
    for completion_row, meta_row in zip(completion_rows, metadata_rows):
        completion = (completion_row.get("completion") or "").strip()
        if not completion and fill_missing and assistant:
            raw_input = (meta_row.get("raw_input") or "").strip()
            if raw_input:
                output = assistant.answer(raw_input)
                completion = (output.get("answer") or "").strip()
                if completion:
                    completion_row = {
                        "prompt": completion_row.get("prompt"),
                        "completion": completion,
                    }
        if not completion:
            continue
        split = meta_row.get("split")
        if split == "validation":
            if max_valid and len(valid_out) >= max_valid:
                continue
            valid_out.append(completion_row)
        else:
            if max_train and len(train_out) >= max_train:
                continue
            train_out.append(completion_row)
    return train_out, valid_out


def main():
    args = parse_args()
    if args.use_exported:
        completion_rows = load_jsonl(Path(args.exported_completion))
        metadata_rows = load_jsonl(Path(args.exported_metadata))
        assistant = None
        if args.fill_missing:
            corpus_path = Path(args.corpus)
            if not corpus_path.exists():
                raise SystemExit(f"Missing corpus: {corpus_path}")
            assistant = LocalWomensHealthAssistant(corpus_path)
        train_out, valid_out = build_rows_from_exports(
            completion_rows,
            metadata_rows,
            args.max_train,
            args.max_valid,
            args.fill_missing,
            assistant,
        )
    else:
        train_rows = load_jsonl(Path(args.train))
        valid_rows = load_jsonl(Path(args.validation))
        system_path = Path(args.system_prompt)
        if not system_path.exists():
            raise SystemExit(f"Missing system prompt: {system_path}")
        system_text = system_path.read_text()
        train_out = build_rows(train_rows, system_text, args.max_train)
        valid_out = build_rows(valid_rows, system_text, args.max_valid)

    write_jsonl(Path(args.output_train), train_out)
    write_jsonl(Path(args.output_valid), valid_out)

    print("Prepared local fine-tune dataset")
    print(f"- train rows: {len(train_out)} -> {args.output_train}")
    print(f"- validation rows: {len(valid_out)} -> {args.output_valid}")


if __name__ == "__main__":
    main()
