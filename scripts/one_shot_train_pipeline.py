#!/usr/bin/env python3

"""
One-shot women health training pipeline.

Runs:
1) download fulltext XML from Europe PMC
2) convert XML to review candidates
3) build train/validation/safety/review partitions
4) backfill assistant outputs
5) clean assistant output artifacts
6) (optional) enrich assistant outputs with context
7) (optional) add controlled variation
8) rebuild partitions
9) validate dataset files
10) (optional) run LoRA training
11) (optional) smoke-test generation

Usage:
    python3 scripts/one_shot_train_pipeline.py
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


ROOT = Path(__file__).resolve().parent.parent


@dataclass
class StepResult:
    name: str
    returncode: int


def run_cmd(name: str, cmd: List[str]) -> StepResult:
    print(f"\n[step] {name}", flush=True)
    print(f"[cmd ] {' '.join(cmd)}", flush=True)

    process = subprocess.Popen(
        cmd,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    if process.stdout is None:
        return StepResult(name, 1)

    for line in process.stdout:
        print(line.rstrip("\n"), flush=True)

    process.wait()
    print(f"[done] {name} -> exit {process.returncode}", flush=True)
    return StepResult(name, process.returncode)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run end-to-end local women-health pipeline")

    p.add_argument("--skip-download", action="store_true", help="Skip fulltext download step")
    p.add_argument("--max-downloads", type=int, default=5000)
    p.add_argument("--download-sleep-ms", type=int, default=250)
    p.add_argument("--download-max-retries", type=int, default=5)
    p.add_argument("--download-log-every", type=int, default=50)
    p.add_argument("--download-reload-every", type=int, default=200)
    p.add_argument(
        "--download-print-progress",
        action="store_true",
        help="Print every checked eligible row in download step",
    )
    p.add_argument(
        "--download-request-timeout",
        type=int,
        default=20,
        help="Download HTTP timeout in seconds",
    )

    p.add_argument("--max-files", type=int, default=5000, help="Max XML files to convert into review candidates")
    p.add_argument("--partition-date", default="2026-03-15")

    p.add_argument("--progress-every", type=int, default=5000)
    p.add_argument("--variate-seed", type=int, default=17)
    p.add_argument(
        "--enable-template-augmentation",
        action="store_true",
        help="Enable enrich/variate synthetic template steps (disabled by default).",
    )

    p.add_argument("--skip-train", action="store_true", help="Skip LoRA train step")
    p.add_argument("--train-config", default="artifacts/mlx_lora_qwen25_1p5b/adapter_config.json")
    p.add_argument("--skip-generate", action="store_true", help="Skip smoke generation step")
    p.add_argument(
        "--generate-prompt",
        default="My period is 10 days late and I had unprotected sex last month. What should I do?",
    )
    p.add_argument("--generate-max-tokens", type=int, default=200)
    p.add_argument("--generate-temp", type=float, default=0.2)

    p.add_argument("--continue-on-fail", action="store_true", help="Continue even if a step fails")
    p.add_argument("--python", default=sys.executable, help="Python executable to use")

    return p.parse_args()


def build_steps(args: argparse.Namespace) -> List[List[str]]:
    steps: List[List[str]] = []
    python_cmd = [args.python, "-u"]

    if not args.skip_download:
        download_cmd = [
            *python_cmd,
            "scripts/download_europe_pmc_fulltext.py",
            "--max-downloads",
            str(args.max_downloads),
            "--sleep-ms",
            str(args.download_sleep_ms),
            "--max-retries",
            str(args.download_max_retries),
            "--log-every",
            str(args.download_log_every),
            "--reload-every",
            str(args.download_reload_every),
            "--request-timeout",
            str(args.download_request_timeout),
        ]
        if args.download_print_progress:
            download_cmd.append("--print-progress")
        steps.append(download_cmd)

    steps += [
        [
            *python_cmd,
            "scripts/xml_to_review_candidates.py",
            "--max-files",
            str(args.max_files),
            "--now",
            args.partition_date,
        ],
        [
            *python_cmd,
            "scripts/build_training_partitions.py",
            "--input",
            "data/interaction_examples.jsonl",
            "--now",
            args.partition_date,
        ],
        [
            *python_cmd,
            "scripts/backfill_assistant_outputs.py",
            "--input",
            "data/interaction_examples.jsonl",
            "--limit",
            "0",
            "--progress-every",
            str(args.progress_every),
        ],
        [
            *python_cmd,
            "scripts/clean_assistant_outputs.py",
            "--input",
            "data/interaction_examples.jsonl",
            "--progress-every",
            str(args.progress_every),
        ],
        [
            *python_cmd,
            "scripts/build_training_partitions.py",
            "--input",
            "data/interaction_examples.jsonl",
            "--now",
            args.partition_date,
        ],
        [*python_cmd, "scripts/validate_datasets.py"],
    ]

    if args.enable_template_augmentation:
        steps[5:5] = [
            [
                *python_cmd,
                "scripts/enrich_assistant_outputs.py",
                "--input",
                "data/interaction_examples.jsonl",
                "--progress-every",
                str(args.progress_every),
            ],
            [
                *python_cmd,
                "scripts/variate_assistant_outputs.py",
                "--input",
                "data/interaction_examples.jsonl",
                "--seed",
                str(args.variate_seed),
                "--progress-every",
                str(args.progress_every),
            ],
        ]

    if not args.skip_train:
        steps.append(
            [
                *python_cmd,
                "-m",
                "mlx_lm",
                "lora",
                "-c",
                args.train_config,
                "--train",
            ]
        )

    if not args.skip_generate and not args.skip_train:
        steps.append(
            [
                *python_cmd,
                "-m",
                "mlx_lm",
                "generate",
                "--model",
                "mlx-community/Qwen2.5-1.5B-Instruct-8bit",
                "--adapter-path",
                "artifacts/mlx_lora_qwen25_1p5b",
                "--prompt",
                args.generate_prompt,
                "--max-tokens",
                str(args.generate_max_tokens),
                "--temp",
                str(args.generate_temp),
            ]
        )

    return steps


def main() -> int:
    args = parse_args()

    step_defs = build_steps(args)
    results: List[StepResult] = []
    failed = 0

    for idx, step in enumerate(step_defs, start=1):
        name = step[1] if len(step) > 1 else "step"
        if name == "-u":
            for token in step:
                if token.endswith(".py"):
                    name = token
                    break
            else:
                name = step[2] if len(step) > 2 else "step"
        elif name == "python":
            for token in step[1:]:
                if token == "mlx_lm" or token.endswith(".py"):
                    name = token
                    break
        if name == "xml_to_review_candidates.py":
            name = "xml_to_review_candidates"
        elif name == "build_training_partitions.py":
            name = "build_training_partitions"
        elif name == "download_europe_pmc_fulltext.py":
            name = "download_europe_pmc_fulltext"
        elif name == "backfill_assistant_outputs.py":
            name = "backfill_assistant_outputs"
        elif name == "clean_assistant_outputs.py":
            name = "clean_assistant_outputs"
        elif name == "enrich_assistant_outputs.py":
            name = "enrich_assistant_outputs"
        elif name == "variate_assistant_outputs.py":
            name = "variate_assistant_outputs"
        elif name == "validate_datasets.py":
            name = "validate_datasets"
        elif name == "mlx_lm":
            name = "mlx_lm_train"
        elif name == "generate":
            name = "mlx_lm_generate"

        result = run_cmd(f"{idx:02d}/{len(step_defs)} {name}", step)
        results.append(result)
        if result.returncode != 0:
            failed += 1
            print(f"[fail] {name} failed with code {result.returncode}")
            if not args.continue_on_fail:
                print("[halt] stopping because --continue-on-fail was not set")
                return result.returncode

    print("\npipeline complete")
    print(f"steps passed: {len(results)-failed} / {len(results)}")
    print(f"steps failed: {failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
