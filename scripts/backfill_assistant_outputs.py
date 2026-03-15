#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import List, Dict, Any


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

sys.path.insert(0, str(ROOT))
from local_ai.assistant import LocalWomensHealthAssistant


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows = []
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


def parse_args():
    parser = argparse.ArgumentParser(description="Backfill empty assistant_output fields using local assistant.")
    parser.add_argument(
        "--input",
        default=str(DATA_DIR / "interaction_examples.jsonl"),
        help="Input interaction JSONL.",
    )
    parser.add_argument(
        "--output",
        default=str(DATA_DIR / "interaction_examples.jsonl"),
        help="Output path (in-place by default).",
    )
    parser.add_argument(
        "--corpus",
        default=str(ROOT / "artifacts" / "knowledge_corpus.jsonl"),
        help="Knowledge corpus for retrieval.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Maximum number of empty rows to backfill (0 = all).",
    )
    parser.add_argument(
        "--progress-every",
        type=int,
        default=50,
        help="Print progress every N backfilled rows.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print a line per backfilled row (can be very noisy for large runs).",
    )
    parser.add_argument("--dry-run", action="store_true", help="Do not write output.")
    return parser.parse_args()


def main():
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    corpus_path = Path(args.corpus)

    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")
    if not corpus_path.exists():
        raise SystemExit(
            f"Corpus not found: {corpus_path}. Run `python3 scripts/build_knowledge_corpus.py` first."
        )

    rows = load_jsonl(input_path)
    assistant = LocalWomensHealthAssistant(corpus_path)

    total = len(rows)
    empty_idx = [
        i
        for i, r in enumerate(rows)
        if not (r.get("assistant_output") or "").strip()
    ]
    print(f"Loaded {total} rows; empty assistant_output: {len(empty_idx)}")

    to_fill = empty_idx if args.limit == 0 else empty_idx[: args.limit]
    if not to_fill:
        print("No rows to backfill.")
        return

    filled = 0
    for idx in to_fill:
        row = rows[idx]
        raw = (row.get("raw_input") or "").strip()
        if not raw:
            continue

        try:
            output = assistant.answer(raw)
        except Exception as exc:
            print(f"[warn] failed on {row.get('interaction_id')}: {exc}")
            continue

        row["assistant_output"] = output.get("answer", "")
        if not row.get("care_recommendation"):
            row["care_recommendation"] = output.get("care_recommendation")
        if not row.get("citations"):
            row["citations"] = output.get("citations", [])

        filled += 1
        if args.verbose:
            raw_preview = raw.replace("\n", " ")[:140]
            answer_len = len((row.get("assistant_output") or "").strip())
            risk = output.get("risk_level") or row.get("risk_level")
            citations = output.get("citations") or row.get("citations") or []
            cit_preview = ",".join(citations[:3])
            print(
                f"[{filled}/{len(to_fill)}] {row.get('interaction_id')} "
                f"risk={risk} answer_len={answer_len} citations={len(citations)}[{cit_preview}] | {raw_preview}"
            )
        if args.progress_every and filled % args.progress_every == 0:
            print(f"Backfilled {filled}/{len(to_fill)}")

    print(f"Backfilled {filled}/{len(to_fill)} rows total.")

    if args.dry_run:
        print("DRY RUN: no output written.")
        return

    if output_path != input_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(output_path, rows)
    print(f"Wrote updated file to {output_path}")


if __name__ == "__main__":
    main()
