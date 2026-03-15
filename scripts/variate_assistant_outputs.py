#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
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


FOLLOWUP_SETS = [
    "Follow-up questions: When was your last period or bleeding episode? Is pregnancy possible from recent sex? Are you postpartum or breastfeeding? How heavy is the bleeding and do you have dizziness, fainting, fever, or severe pain?",
    "Follow-up questions: Have you taken a pregnancy test? Have you had new or severe pain, fever, or heavy bleeding? Any recent major stress, illness, or weight change?",
    "Follow-up questions: Are you using contraception or did it recently change? Are you breastfeeding or postpartum? Any new discharge, pain, or bleeding between periods?",
]


EXPLANATION_TEMPLATES = [
    "Common factors that shift cycles include stress, recent illness, changes in exercise, and hormonal fluctuations.",
    "Cycle timing can vary due to stress, changes in routine, weight shifts, or contraception changes.",
    "Menstrual timing can vary month to month, especially with stress, travel, or lifestyle changes.",
]


RISK_TEMPLATES = {
    "urgent_care": [
        "This pattern needs urgent medical evaluation.",
        "Because red-flag symptoms may be present, urgent evaluation is recommended.",
    ],
    "emergency_care": [
        "This is an emergency pattern and needs immediate medical care.",
        "Seek emergency care now based on the described red flags.",
    ],
    "prompt_medical_review": [
        "This pattern should be reviewed by a clinician, even if it is not an emergency.",
        "A clinician should review this pattern soon.",
    ],
    "routine_review": [
        "This can be within normal variation, but it is reasonable to monitor and check in if it persists.",
        "This may be normal, but follow up if it continues or worsens.",
    ],
    "normal_variation": [
        "This can be within normal variation, depending on life stage and severity.",
        "This may fit normal variation, but monitor for changes.",
    ],
}

SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")

# Narrative fragments that should never appear.
NARRATIVE_FRAGMENTS = [
    "They came and wen",
    "They came and",
]

# Build a set of follow-up sentences for stripping.
FOLLOWUP_SENTENCES = set()
for block in FOLLOWUP_SETS:
    if block.lower().startswith("follow-up questions:"):
        block = block.split(":", 1)[1].strip()
    for sent in SENTENCE_SPLIT.split(block):
        if sent.strip():
            FOLLOWUP_SENTENCES.add(sent.strip().lower())

# Sentences to remove before rebuilding.
REMOVE_PATTERNS = [
    re.compile(r"^This pattern should be medically reviewed\.$", re.I),
    re.compile(r"^This pattern should be reviewed by a clinician.*$", re.I),
    re.compile(r"^This pattern needs urgent medical evaluation\.$", re.I),
    re.compile(r"^This is an emergency pattern.*$", re.I),
    re.compile(r"^Seek emergency care now.*$", re.I),
    re.compile(r"^This can be within normal variation.*$", re.I),
    re.compile(r"^This may fit normal variation.*$", re.I),
    re.compile(r"^This may be normal, but follow up.*$", re.I),
    re.compile(r"^This is educational information, not a diagnosis\.$", re.I),
    re.compile(r"^Follow-up questions:.*$", re.I),
]


def _split_sentences(text: str) -> List[str]:
    if not text:
        return []
    return [s.strip() for s in SENTENCE_SPLIT.split(text.strip()) if s.strip()]


def _dedupe_sentences(sentences: List[str]) -> List[str]:
    seen = set()
    out = []
    for s in sentences:
        key = s.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(s)
    return out


def _strip_fragments(text: str) -> str:
    cleaned = text
    for frag in NARRATIVE_FRAGMENTS:
        cleaned = cleaned.replace(frag, "")
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    return cleaned


def parse_args():
    parser = argparse.ArgumentParser(description="Add variation to assistant_output templates.")
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
    parser.add_argument("--seed", type=int, default=42, help="Deterministic seed for variation.")
    parser.add_argument("--progress-every", type=int, default=200, help="Print progress every N rows.")
    parser.add_argument("--dry-run", action="store_true", help="Do not write output.")
    return parser.parse_args()


def main():
    import random

    args = parse_args()
    rng = random.Random(args.seed)
    input_path = Path(args.input)
    output_path = Path(args.output)

    rows = load_jsonl(input_path)
    total = len(rows)
    changed = 0

    for i, row in enumerate(rows, 1):
        text = (row.get("assistant_output") or "").strip()
        if not text:
            continue

        # Remove boilerplate lines and dedupe sentences from the original text.
        text = _strip_fragments(text)
        sentences = _split_sentences(text)
        kept = []
        for s in sentences:
            # Drop sentences that match follow-up sentences or explanation templates.
            if s.lower() in FOLLOWUP_SENTENCES:
                continue
            if s in EXPLANATION_TEMPLATES:
                continue
            if s in sum(RISK_TEMPLATES.values(), []):
                continue
            if any(pat.match(s) for pat in REMOVE_PATTERNS):
                continue
            kept.append(s)
        kept = _dedupe_sentences(kept)
        core = " ".join(kept).strip()

        # Choose templates.
        risk = row.get("risk_level") or "routine_review"
        risk_opts = RISK_TEMPLATES.get(risk, RISK_TEMPLATES["routine_review"])
        risk_line = rng.choice(risk_opts)
        expl_line = rng.choice(EXPLANATION_TEMPLATES)
        followups = rng.choice(FOLLOWUP_SETS)

        # Rebuild with variation while preserving core content.
        parts = [expl_line, risk_line]
        if core:
            parts.append(core)
        parts.append("This is educational information, not a diagnosis.")
        parts.append(followups)
        rebuilt = " ".join(parts).strip()
        row["assistant_output"] = rebuilt
        changed += 1
        if args.progress_every and changed % args.progress_every == 0:
            print(f"Variated {changed} rows")

    print(f"Total rows: {total}")
    print(f"Rows changed: {changed}")

    if args.dry_run:
        print("DRY RUN: no output written.")
        return

    if output_path != input_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(output_path, rows)
    print(f"Wrote variated file to {output_path}")


if __name__ == "__main__":
    main()
