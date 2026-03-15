#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"


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


def parse_args():
    parser = argparse.ArgumentParser(description="Prepare MLX chat-format train/valid JSONL.")
    parser.add_argument(
        "--chat-export",
        default=str(DATA_DIR / "training_exports" / "interaction_finetune_chat.jsonl"),
        help="Chat export JSONL.",
    )
    parser.add_argument(
        "--metadata",
        default=str(DATA_DIR / "training_exports" / "interaction_finetune_metadata.jsonl"),
        help="Metadata export JSONL (with split info).",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DATA_DIR / "training_exports" / "mlx_chat"),
        help="Output directory for train/valid JSONL.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    chat_rows = load_jsonl(Path(args.chat_export))
    meta_rows = load_jsonl(Path(args.metadata))

    if len(chat_rows) != len(meta_rows):
        raise SystemExit("Chat export and metadata row counts do not match.")

    train_out = []
    valid_out = []
    for chat_row, meta_row in zip(chat_rows, meta_rows):
        messages = chat_row.get("messages")
        if not isinstance(messages, list) or not messages:
            continue
        split = meta_row.get("split")
        if split == "validation":
            valid_out.append(chat_row)
        else:
            train_out.append(chat_row)

    out_dir = Path(args.output_dir)
    write_jsonl(out_dir / "train.jsonl", train_out)
    write_jsonl(out_dir / "valid.jsonl", valid_out)

    print("Prepared MLX chat dataset")
    print(f"- train rows: {len(train_out)} -> {out_dir / 'train.jsonl'}")
    print(f"- validation rows: {len(valid_out)} -> {out_dir / 'valid.jsonl'}")


if __name__ == "__main__":
    main()
