#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"


SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")

# Heuristic cleanup patterns for noisy RAG artifacts.
DROP_SENTENCE_PATTERNS = [
    re.compile(r"URL has been copied to the clipboard", re.I),
    re.compile(r"Reported age:\s*\d+", re.I),
    re.compile(r"^Based on the current knowledge base:\s*$", re.I),
    re.compile(r"^Based on the current knowledge base:.*$", re.I),
]

# Generic openers that cause template collapse when over-represented.
GENERIC_TEMPLATE_PATTERNS = [
    re.compile(
        r"^Common factors that shift cycles include stress, recent illness, changes in exercise, and hormonal fluctuations\.?$",
        re.I,
    ),
    re.compile(
        r"^Menstrual timing can vary month to month, especially with stress, travel, or lifestyle changes\.?$",
        re.I,
    ),
    re.compile(
        r"^Cycle timing can vary due to stress, changes in routine, weight shifts, or contraception changes\.?$",
        re.I,
    ),
    re.compile(r"^This pattern should be reviewed by a clinician.*$", re.I),
    re.compile(r"^A clinician should review this pattern soon\.?$", re.I),
    re.compile(r"^This pattern needs urgent medical evaluation\.?$", re.I),
    re.compile(r"^Because red-flag symptoms may be present, urgent evaluation is recommended\.?$", re.I),
    re.compile(r"^This can be within normal variation.*$", re.I),
    re.compile(r"^This may fit normal variation.*$", re.I),
    re.compile(r"^This may be normal, but follow up if it continues or worsens\.?$", re.I),
    re.compile(r"^Stress can affect cycle timing and symptoms, so it may be a contributing factor\.?$", re.I),
    re.compile(r"^Major changes in exercise or training load can also shift cycle timing\.?$", re.I),
    re.compile(r"^This is educational information, not a diagnosis\.?$", re.I),
    re.compile(r"^Follow-up questions:.*$", re.I),
]

# Optional name/story fragments that commonly leak from narrative sources.
NAME_SNIPPETS = [
    "Carole",
    "Leila",
    "Lauren",
    "Liz",
    "Leslie",
    "Paula",
    "At 36,",
    "At age",
    "She had ,",
    "He had ,",
]


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


def should_drop_sentence(sentence: str, drop_names: bool) -> bool:
    for pat in DROP_SENTENCE_PATTERNS:
        if pat.search(sentence):
            return True
    if drop_names and any(token in sentence for token in NAME_SNIPPETS):
        return True
    return False


def clean_text(text: str, drop_names: bool) -> Tuple[str, int]:
    if not text:
        return text, 0
    sentences = SENTENCE_SPLIT.split(text.strip())
    kept = []
    removed = 0
    seen = set()
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        if should_drop_sentence(s, drop_names):
            removed += 1
            continue
        if any(pat.match(s) for pat in GENERIC_TEMPLATE_PATTERNS):
            removed += 1
            continue
        key = s.lower()
        if key in seen:
            removed += 1
            continue
        seen.add(key)
        kept.append(s)
    if not kept:
        # Avoid empty outputs by preserving original text if all sentences were stripped.
        return text.strip(), removed
    cleaned = " ".join(kept).strip()
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return cleaned, removed


def parse_args():
    parser = argparse.ArgumentParser(description="Clean noisy assistant_output artifacts.")
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
        "--progress-every",
        type=int,
        default=200,
        help="Print progress every N cleaned rows.",
    )
    parser.add_argument(
        "--drop-names",
        action="store_true",
        help="Drop sentences containing common narrative name fragments.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Do not write output.")
    return parser.parse_args()


def main():
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    rows = load_jsonl(input_path)
    total = len(rows)
    cleaned_rows = 0
    total_removed = 0

    for idx, row in enumerate(rows):
        original = (row.get("assistant_output") or "").strip()
        if not original:
            continue
        cleaned, removed = clean_text(original, args.drop_names)
        if cleaned != original:
            row["assistant_output"] = cleaned
            cleaned_rows += 1
            total_removed += removed
            if args.progress_every and cleaned_rows % args.progress_every == 0:
                print(f"Cleaned {cleaned_rows} rows; sentences removed so far: {total_removed}")

    print(f"Total rows: {total}")
    print(f"Rows changed: {cleaned_rows}")
    print(f"Total sentences removed: {total_removed}")

    if args.dry_run:
        print("DRY RUN: no output written.")
        return

    if output_path != input_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(output_path, rows)
    print(f"Wrote cleaned file to {output_path}")


if __name__ == "__main__":
    main()
