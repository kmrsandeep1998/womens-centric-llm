#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Any, List


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"


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


def _flag(features: Dict[str, Any], key: str) -> bool:
    return bool(features.get(key))


def build_context_paragraph(row: Dict[str, Any]) -> str:
    features = row.get("extracted_features", {}) or {}
    raw = (row.get("raw_input") or "").strip().lower()
    risk = row.get("risk_level") or "routine_review"

    sentences: List[str] = []

    # Pregnancy risk language
    if _flag(features, "unprotected_sex_recent") or "unprotected sex" in raw:
        sentences.append(
            "Because unprotected sex was mentioned, pregnancy is one possible reason for a late or changed period."
        )
    elif _flag(features, "sexually_active") and ("late" in raw or "missed" in raw):
        sentences.append(
            "When periods are late and there has been recent sex, pregnancy should be considered."
        )

    # Stress, exercise, weight change
    if _flag(features, "stress_level") or "stress" in raw:
        sentences.append(
            "Stress can affect cycle timing and symptoms, so it may be a contributing factor."
        )
    if _flag(features, "exercise_level") or "training" in raw or "exercise" in raw:
        sentences.append(
            "Major changes in exercise or training load can also shift cycle timing."
        )
    if _flag(features, "recent_weight_change_kg") or "weight" in raw:
        sentences.append(
            "Weight changes can influence cycles, especially when combined with stress or heavy exercise."
        )

    # Postpartum/breastfeeding
    if _flag(features, "breastfeeding") or _flag(features, "postpartum_weeks"):
        sentences.append(
            "Postpartum and breastfeeding patterns can delay the return of ovulation and periods."
        )

    # Bleeding severity cues
    if "heavy" in raw or _flag(features, "very_heavy_bleeding") or _flag(features, "clots_present"):
        sentences.append(
            "Very heavy bleeding, large clots, or dizziness are not typical and warrant medical review."
        )

    # Risk-level specific framing
    if risk in {"urgent_care", "emergency_care"}:
        sentences.append(
            "Because red-flag symptoms may be present, urgent evaluation is recommended."
        )
    elif risk in {"prompt_medical_review"}:
        sentences.append(
            "This pattern should be reviewed by a clinician, even if it is not an emergency."
        )
    elif risk in {"normal_variation", "routine_review"}:
        sentences.append(
            "This can be within normal variation, but it is reasonable to monitor and check in if it persists."
        )

    if not sentences:
        sentences.append(
            "Based on what you shared, several common factors can affect menstrual timing and symptoms."
        )

    # Keep short: 2-4 sentences.
    return " ".join(sentences[:4]).strip()


def parse_args():
    parser = argparse.ArgumentParser(description="Enrich assistant_output with a short contextual paragraph.")
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
        help="Print progress every N rows.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Do not write output.")
    return parser.parse_args()


def main():
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    rows = load_jsonl(input_path)
    total = len(rows)
    changed = 0

    for idx, row in enumerate(rows, 1):
        original = (row.get("assistant_output") or "").strip()
        if not original:
            continue
        context = build_context_paragraph(row)
        # Avoid duplicating if already contains the context line.
        if context and context not in original:
            row["assistant_output"] = f"{context} {original}".strip()
            changed += 1
            if args.progress_every and changed % args.progress_every == 0:
                print(f"Enriched {changed} rows")

    print(f"Total rows: {total}")
    print(f"Rows enriched: {changed}")

    if args.dry_run:
        print("DRY RUN: no output written.")
        return

    if output_path != input_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(output_path, rows)
    print(f"Wrote enriched file to {output_path}")


if __name__ == "__main__":
    main()
