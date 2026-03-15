#!/usr/bin/env python3

"""
Run paired inference for base model vs fine-tuned adapter across a sample of prompts.

Usage:
  python3 scripts/compare_base_vs_finetune_50.py \
    --count 50 \
    --max-tokens 220 \
    --temp 0.2 \
    --output outputs/compare_base_vs_finetune.jsonl
"""

from __future__ import annotations

import argparse
import json
import re
import random
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"


@dataclass
class PromptItem:
    prompt: str
    prompt_id: str
    source: str


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def get_prompt_from_row(row: Dict[str, Any]) -> Optional[str]:
    for key in (
        "input",
        "raw_input",
        "question",
        "prompt",
        "text",
    ):
        v = row.get(key)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None


def collect_prompts(count: int, seed: int) -> List[PromptItem]:
    random.seed(seed)
    prompts: List[PromptItem] = []

    bench_path = DATA_DIR / "benchmark_eval_set.jsonl"
    if bench_path.exists():
        for row in load_jsonl(bench_path):
            prompt = get_prompt_from_row(row)
            if not prompt:
                continue
            prompts.append(
                PromptItem(
                    prompt=prompt,
                    prompt_id=row.get("benchmark_id", f"bench-{len(prompts):04d}"),
                    source="benchmark_eval_set",
                )
            )

    if len(prompts) < count:
        interaction_path = DATA_DIR / "interaction_examples.jsonl"
        if interaction_path.exists():
            rows = load_jsonl(interaction_path)
            random.shuffle(rows)
            for i, row in enumerate(rows):
                if len(prompts) >= count:
                    break
                prompt = get_prompt_from_row(row)
                if not prompt:
                    continue
                prompts.append(
                    PromptItem(
                        prompt=prompt,
                        prompt_id=row.get("interaction_id", f"int-{i:06d}"),
                        source="interaction_examples",
                    )
                )

    if len(prompts) < count:
        return prompts
    return prompts[:count]


def run_generate(
    prompt: str,
    model: str,
    adapter: Optional[str],
    max_tokens: int,
    temp: float,
) -> Tuple[Optional[str], Dict[str, str]]:
    cmd = [
        sys_executable(),
        "-m",
        "mlx_lm",
        "generate",
        "--model",
        model,
        "--prompt",
        prompt,
        "--max-tokens",
        str(max_tokens),
        "--temp",
        str(temp),
    ]
    if adapter:
        cmd.extend(["--adapter-path", adapter])

    proc = subprocess.run(cmd, capture_output=True, text=True)
    out = proc.stdout
    err = proc.stderr
    parsed = parse_answer(out)
    meta = parse_meta(out, err, proc.returncode)
    return parsed, meta


def parse_answer(stdout: str) -> Optional[str]:
    if not stdout:
        return None
    m = re.search(r"={10,}\n(.*?)\nPrompt:", stdout, re.S)
    if m:
        text = m.group(1).strip()
        if text:
            return text
    marker = "==========" 
    if marker in stdout:
        parts = stdout.split(marker)
        for p in parts:
            p = p.strip()
            if not p:
                continue
            if "Prompt:" in p:
                candidate = p.split("Prompt:")[0].strip()
                if candidate and not candidate.startswith("Fetching") and not candidate.startswith("["):
                    return candidate
        return None
    return stdout.strip().split("Prompt:")[0].strip() if "Prompt:" in stdout else stdout.strip()


def parse_meta(stdout: str, stderr: str, returncode: int) -> Dict[str, str]:
    text = stdout + "\n" + (stderr or "")
    gen_tps = re.search(r"Generation:\s+\d+\s+tokens,\s+([0-9.]+)\s+tokens-per-sec", text)
    prompt_tps = re.search(r"Prompt:\s+\d+\s+tokens,\s+([0-9.]+)\s+tokens-per-sec", text)
    return {
        "exit_code": str(returncode),
        "gen_tps": gen_tps.group(1) if gen_tps else "",
        "prompt_tps": prompt_tps.group(1) if prompt_tps else "",
        "has_warning": "warn" if "warn" in text.lower() else "",
    }


def sys_executable() -> str:
    # Keep parity with the current environment's default Python binary.
    return "python3"


def score_answer(text: str) -> Dict[str, bool]:
    t = (text or "").lower()
    return {
        "has_education_disclaimer": "educational information" in t,
        "has_follow_up": "follow-up" in t or "follow up" in t or "questions" in t,
        "mentions_pregnancy_test": "pregnancy test" in t,
        "mentions_urgent": any(
            k in t
            for k in [
                "urgent medical evaluation",
                "urgent evaluation",
                "emergency care",
                "emergency room",
                "needs urgent",
                "urgent medical",
            ]
        ),
        "mentions_diagnosis": any(
            k in t
            for k in [
                "you have",
                "you are likely",
                "is likely",
                "diagnosis",
            ]
        ),
        "has_not_diagnosis_warning": "not a diagnosis" in t,
    }


def summarize_rows(rows: List[Dict[str, Any]]) -> None:
    total = len(rows)
    if total == 0:
        print("No successful rows to summarize.")
        return

    base_edu = sum(1 for r in rows if r["base_stats"]["has_education_disclaimer"])
    fine_edu = sum(1 for r in rows if r["tuned_stats"]["has_education_disclaimer"])
    base_follow = sum(1 for r in rows if r["base_stats"]["has_follow_up"])
    fine_follow = sum(1 for r in rows if r["tuned_stats"]["has_follow_up"])
    base_urgent = sum(1 for r in rows if r["base_stats"]["mentions_urgent"])
    fine_urgent = sum(1 for r in rows if r["tuned_stats"]["mentions_urgent"])
    base_not_diag = sum(1 for r in rows if r["base_stats"]["has_not_diagnosis_warning"])
    fine_not_diag = sum(1 for r in rows if r["tuned_stats"]["has_not_diagnosis_warning"])

    print("\n=== COMPARISON SUMMARY ===")
    print(f"Total rows: {total}")
    print(f"Education disclaimer present - base: {base_edu}/{total}, tuned: {fine_edu}/{total}")
    print(f"Follow-up present - base: {base_follow}/{total}, tuned: {fine_follow}/{total}")
    print(f"Urgent phrasing present - base: {base_urgent}/{total}, tuned: {fine_urgent}/{total}")
    print(f"Not-a-diagnosis warning - base: {base_not_diag}/{total}, tuned: {fine_not_diag}/{total}")

    len_deltas = [r["len_delta_chars"] for r in rows]
    tps_delta = [r["gen_tps_delta"] for r in rows if r["gen_tps_delta"] is not None]
    if len_deltas:
        print(f"Avg tuned - base answer length: {sum(len_deltas)/len(len_deltas):.1f} chars difference")
    if tps_delta:
        print(f"Avg tuned vs base generation speed delta: {sum(tps_delta)/len(tps_delta):.2f} tokens/s")

    top_improved = sorted(
        rows,
        key=lambda r: (r["tuned_has_follow_up"] - r["base_has_follow_up"])
        + (r["tuned_has_education"] - r["base_has_education"]) * 0.5,
        reverse=True,
    )[:5]
    print("\nTop 5 improvements (by simple delta):")
    for r in top_improved:
        print(
            f"- {r['prompt_id']} from {r['source']} "
            f"education={r['base_has_education']}→{r['tuned_has_education']}, "
            f"followup={r['base_has_follow_up']}→{r['tuned_has_follow_up']}, "
            f"urgency={r['base_has_urgent']}→{r['tuned_has_urgent']}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare base Qwen with fine-tuned adapter.")
    parser.add_argument("--count", type=int, default=50)
    parser.add_argument("--max-tokens", type=int, default=220)
    parser.add_argument("--temp", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument(
        "--model",
        default="mlx-community/Qwen2.5-1.5B-Instruct-8bit",
        help="Base model name/path.",
    )
    parser.add_argument(
        "--adapter-path",
        default="artifacts/mlx_lora_qwen25_1p5b",
        help="Adapter directory for fine-tuned model.",
    )
    parser.add_argument(
        "--output",
        default="outputs/compare_base_vs_finetune_50.jsonl",
        help="Where to write pairwise comparison rows.",
    )
    args = parser.parse_args()

    prompts = collect_prompts(args.count, args.seed)
    if not prompts:
        raise SystemExit("No prompts found in benchmark or interaction files.")
    print(f"Prepared {len(prompts)} prompts for comparison.")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows_out: List[Dict[str, Any]] = []

    for idx, item in enumerate(prompts, start=1):
        print(f"[{idx}/{len(prompts)}] Running prompt {item.prompt_id} from {item.source}")

        base_ans, base_meta = run_generate(
            item.prompt,
            args.model,
            None,
            args.max_tokens,
            args.temp,
        )
        tuned_ans, tuned_meta = run_generate(
            item.prompt,
            args.model,
            args.adapter_path,
            args.max_tokens,
            args.temp,
        )

        base_stats = score_answer(base_ans or "")
        tuned_stats = score_answer(tuned_ans or "")
        base_tps = float(base_meta.get("gen_tps") or 0.0)
        tuned_tps = float(tuned_meta.get("gen_tps") or 0.0)
        tps_delta = tuned_tps - base_tps if tuned_tps or base_tps else None

        row = {
            "prompt_id": item.prompt_id,
            "source": item.source,
            "prompt": item.prompt,
            "base_answer": base_ans,
            "tuned_answer": tuned_ans,
            "base_meta": base_meta,
            "tuned_meta": tuned_meta,
            "base_stats": base_stats,
            "tuned_stats": tuned_stats,
            "len_delta_chars": (len(tuned_ans or "")) - (len(base_ans or "")),
            "len_delta_tokens": len((tuned_ans or "").split()) - len((base_ans or "").split()),
            "gen_tps_delta": tps_delta,
            "base_has_education": int(base_stats["has_education_disclaimer"]),
            "tuned_has_education": int(tuned_stats["has_education_disclaimer"]),
            "base_has_follow_up": int(base_stats["has_follow_up"]),
            "tuned_has_follow_up": int(tuned_stats["has_follow_up"]),
            "base_has_urgent": int(base_stats["mentions_urgent"]),
            "tuned_has_urgent": int(tuned_stats["mentions_urgent"]),
            "base_has_not_diagnosis_warning": int(base_stats["has_not_diagnosis_warning"]),
            "tuned_has_not_diagnosis_warning": int(tuned_stats["has_not_diagnosis_warning"]),
        }
        rows_out.append(row)

        print(f"  base  : {(base_ans or '').splitlines()[0][:120] if base_ans else '[no-answer]'}")
        print(f"  tuned : {(tuned_ans or '').splitlines()[0][:120] if tuned_ans else '[no-answer]'}")
        print()

    output_path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows_out) + "\n")
    print(f"Wrote {len(rows_out)} rows to {output_path}")
    summarize_rows(rows_out)


if __name__ == "__main__":
    main()
