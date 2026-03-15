#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from typing import Dict, List


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DEFAULT_OUTPUT = DATA_DIR / "interaction_examples.jsonl"
DEFAULT_TEMPLATES = DATA_DIR / "interaction_expansion_templates.jsonl"


AGE_POOL = ["22", "24", "27", "29", "31", "34", "38", "41", "44", "47", "52"]
CYCLE_DELAY_POOL = [5, 7, 10, 12, 15, 18, 21, 28, 35]
POSTPARTUM_POOL = [8, 10, 14, 16, 20, 24, 28]
WEIGHT_CHANGE_POOL = ["lost 4 kg", "lost 6 kg", "gained 3 kg", "gained 5 kg", "no major weight change"]
SEX_CONTEXT_POOL = [
    "I had unprotected sex recently.",
    "My partner and I have been trying to conceive.",
    "I had sex about two weeks ago.",
    "I used a condom every time.",
]
STRESS_POOL = [
    "I have been under exam stress.",
    "This started during a very stressful period.",
    "I am in high stress with poor sleep.",
    "I recently changed shift duties.",
]
EXERCISE_POOL = [
    "I started very intense training recently.",
    "My exercise routine became much higher than before.",
    "I have had low activity lately.",
    "I usually walk 30 minutes daily.",
]
FOLLOW_UP_POOL = [
    "Any risk of anemia?",
    "Should I do a pregnancy test?",
    "Could this be normal for my life stage?",
    "Do I need urgent care today?",
]
AGE_PREFIX = [
    "I'm {age}.",
    "I am {age} years old.",
    "At age {age},",
    "I'm {age} and wondering about this.",
]


def load_jsonl(path: Path) -> List[Dict]:
    if not path.exists():
        raise SystemExit(f"Template file not found: {path}")
    rows = []
    for line_no, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"{path}:{line_no} invalid json: {exc}") from exc
    return rows


def write_jsonl(path: Path, rows: List[Dict]):
    path.write_text("\n".join(json.dumps(row, ensure_ascii=True) for row in rows) + "\n")


def _next_interaction_id(existing):
    ids = []
    for row in existing:
        raw_id = str(row.get("interaction_id", ""))
        if raw_id.startswith("INT") and raw_id[3:].isdigit():
            ids.append(int(raw_id[3:]))
    return f"INT{(max(ids, default=0) + 1):03d}"


def _has_existing_raw(existing, raw_input):
    target = raw_input.strip().lower()
    return any(item.get("raw_input", "").strip().lower() == target for item in existing)


def _augment_raw(raw_input: str, rng: random.Random):
    suffixes = []
    if rng.random() < 0.55:
        suffixes.append(rng.choice(AGE_PREFIX).format(age=rng.choice(AGE_POOL)))
    if rng.random() < 0.55:
        delay = rng.choice(CYCLE_DELAY_POOL)
        suffixes.append(f"My last period was about {delay} days ago.")
    if rng.random() < 0.45:
        suffixes.append(rng.choice(STRESS_POOL))
    if rng.random() < 0.45:
        suffixes.append(rng.choice(SEX_CONTEXT_POOL))
    if rng.random() < 0.45:
        suffixes.append(rng.choice(STRESS_POOL))
    if rng.random() < 0.45:
        suffixes.append(rng.choice(EXERCISE_POOL))
    if rng.random() < 0.45:
        suffixes.append(rng.choice(FOLLOW_UP_POOL))
    if rng.random() < 0.35:
        suffixes.append(f"I {rng.choice(WEIGHT_CHANGE_POOL)} over last 2 months.")

    for extra in suffixes:
        if extra not in raw_input:
            raw_input = f"{raw_input} {extra}"
    return raw_input.strip()


def _normalize_row(template, output_id, risk_gate: str | None):
    summary = template.get("summary_hint") or _short_summary(template.get("raw_input", ""))
    citations = template.get("citations") or []
    if risk_gate:
        risk_level = risk_gate
    else:
        risk_level = template.get("risk_level_override") or "normal_variation"
    return {
        "interaction_id": output_id,
        "data_origin": "synthetic_bootstrap_scaled",
        "review_status": template.get("default_review_status", "pending_human_review"),
        "raw_input": template.get("raw_input", ""),
        "normalized_case_summary": summary,
        "extracted_features": {},
        "assistant_output": "",
        "citations": citations,
        "risk_level": risk_level,
        "care_recommendation": "",
        "abstained": False,
    }


def _short_summary(text: str):
    return text[:140] if text else "No structured summary available."


def main():
    parser = argparse.ArgumentParser(description="Generate large synthetic interaction datasets for prototyping.")
    parser.add_argument(
        "--templates",
        default=str(DEFAULT_TEMPLATES),
        help="Template JSONL with raw_input/summaries/citations.",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="Path to interaction_examples.jsonl to append to.",
    )
    parser.add_argument("--target", type=int, default=10000, help="Total target interaction count.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument("--dry-run", action="store_true", help="Generate preview only.")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    templates = load_jsonl(Path(args.templates))
    if not templates:
        raise SystemExit("No templates available.")

    output_path = Path(args.output)
    existing_rows = load_jsonl(output_path) if output_path.exists() else []
    needed = max(args.target - len(existing_rows), 0)
    if needed == 0:
        print(f"Target already met. Existing records: {len(existing_rows)}")
        return

    generated = []
    while len(generated) < needed:
        t = rng.choice(templates)
        raw = t.get("raw_input", "").strip()
        if not raw:
            continue
        variant = _augment_raw(raw, rng)
        if _has_existing_raw(existing_rows + generated, variant):
            continue

        row = _normalize_row(t, _next_interaction_id(existing_rows + generated), t.get("risk_level_override"))
        row["raw_input"] = variant
        row["extracted_features"] = {
            "age_years": int(rng.choice(AGE_POOL)),
            "last_menstrual_period_days_ago": rng.choice(CYCLE_DELAY_POOL),
            "last_menstrual_period_date": None,
            "missed_periods_count": None,
            "bleeding_duration_days": None,
            "flow_level": "unknown",
            "pain_score_0_10": None,
            "red_flags": [],
            "clots_present": False,
            "spotting_between_periods": False,
            "bleeding_after_sex": "sex" in variant.lower() and rng.random() < 0.4,
            "symptoms": [],
            "sexually_active": "sex" in variant.lower(),
            "unprotected_sex_recent": "unprotected" in variant.lower(),
            "last_sex_date": None,
            "pregnancy_test_result": "not_done",
            "pregnancy_known": False,
            "emergency_contraception_used": False,
            "breastfeeding": "breastfeeding" in variant.lower(),
            "exclusive_breastfeeding": "exclusive" in variant.lower(),
            "partial_breastfeeding": "partial" in variant.lower(),
            "postpartum_weeks": None,
            "contraception_method": "unknown",
            "contraception_recent_change": False,
            "stress_level": "high" if "stress" in variant.lower() else "moderate",
            "exercise_level": "high" if "intense" in variant.lower() else "moderate",
            "sleep_hours": None,
            "shift_work_flag": "shift" in variant.lower(),
            "trying_to_conceive": "trying" in variant.lower() or "trying to get" in variant.lower(),
            "infertility_history_flag": False,
            "miscarriage_history_flag": False,
            "abortion_history_flag": False,
            "live_birth_count": None,
            "medications": [],
            "known_conditions": [],
            "weight_kg": None,
            "recent_weight_change_kg": None,
            "extracted_summary": None,
        }
        generated.append(row)

        if len(generated) >= needed:
            break

    preview = min(5, len(generated))
    print("Generated preview:")
    for row in generated[:preview]:
        print(f"- {row['interaction_id']} | {row['risk_level']} | {row['raw_input'][:110]}")

    if args.dry_run:
        print(f"DRY RUN: {len(generated)} rows would be generated.")
        return

    output_path.write_text(
        "\n".join(
            json.dumps(r, ensure_ascii=True)
            for r in existing_rows + generated
        )
        + "\n"
    )
    print(f"Wrote {len(generated)} rows. Total now {len(existing_rows)+len(generated)}.")


if __name__ == "__main__":
    main()
