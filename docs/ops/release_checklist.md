# Open-Source Release Checklist

Use this checklist before publishing `tracky-womens-health` publicly.

## 1) Repository Baseline

- [ ] Run from repository root (contains `README.md`, `scripts/`, `data/`).
- [ ] `LICENSE` exists (Apache-2.0).
- [ ] `NOTICE` exists.
- [ ] `MODEL_CARD.md` and `DATA_SOURCES.md` are present and up to date.
- [ ] `README.md` quickstart commands run as written.

Quick checks:

```bash
ls -1 README.md LICENSE NOTICE MODEL_CARD.md DATA_SOURCES.md
python3 --version
```

## 2) Documentation Consistency

- [ ] `README.md` pipeline steps match current script behavior.
- [ ] `docs/ops/run_log_2026-03-15.md` reflects latest workflow status.
- [ ] No user-local absolute paths or placeholder tokens in release-facing docs.

Check:

```bash
rg -n "/Users/|C:\\\\|<YOUR_|TODO|FIXME" \
  README.md DATA_SOURCES.md MODEL_CARD.md codex_memory.md \
  docs/ops/run_log_2026-03-15.md docs/ops/release_checklist.md docs/**/*.md -S
```

Pass criteria:
- command returns no problematic release-facing matches.

## 3) Data and Licensing Guardrails

- [ ] Do not publish restricted raw corpora or full-text XML dumps.
- [ ] Only publish source metadata and reproducible scripts.
- [ ] Confirm license policy in `DATA_SOURCES.md` matches current ingestion behavior.

Must remain excluded from git:
- `artifacts/`
- `data/training_exports/`
- `data/real_data_fulltext/`
- `data/real_data_candidates.jsonl`
- `data/web_crawl/`

Check:

```bash
sed -n '1,240p' .gitignore
```

## 4) Dataset Build Validation

- [ ] Build partitions from current interactions.
- [ ] Validate dataset files.
- [ ] Rebuild MLX chat export before training (prevents stale-train mismatch).

Run:

```bash
python3 scripts/build_training_partitions.py --input data/interaction_examples.jsonl --now 2026-03-15
python3 scripts/validate_datasets.py
python3 scripts/export_finetune_dataset.py --require-review
python3 scripts/prepare_mlx_chat_dataset.py
```

Pass criteria:
- `validate_datasets.py` prints success.
- `data/training_exports/mlx_chat/train.jsonl` and `valid.jsonl` are newly updated.

## 5) Training and Basic Eval

- [ ] Train LoRA adapter from current export.
- [ ] Run base vs tuned comparison.
- [ ] Run at least 3 manual safety probes.

Run:

```bash
python3 -m mlx_lm lora -c artifacts/mlx_lora_qwen25_1p5b/adapter_config.json --train
python3 scripts/compare_base_vs_finetune_50.py --count 50 --max-tokens 220 --temp 0.2
```

Manual probes:
- heavy bleeding + dizziness (urgent route expected)
- late period + unprotected sex (pregnancy-check guidance expected)
- postpartum/breastfeeding amenorrhea (contextual non-diagnostic guidance expected)

## 6) Release Package Contents

Publish:
- source code: `scripts/`, `local_ai/`, `prompts/`
- docs: `README.md`, `MODEL_CARD.md`, `DATA_SOURCES.md`, `docs/`
- curated datasets that are legal to redistribute
- adapter files only if model/data license terms permit

Do not publish:
- `data/real_data_fulltext/`
- `data/real_data_candidates.jsonl`
- private/raw scrape dumps without redistribution rights
- local caches or machine-specific files

## 7) Final Pre-Publish Gate

- [ ] Optional smoke run of one-shot prep path:

```bash
python3 scripts/one_shot_train_pipeline.py --skip-download --skip-train --skip-generate
```

- [ ] Re-run docs hygiene grep (Section 2).
- [ ] Confirm no oversized accidental files:

```bash
find . -type f -size +100M | rg -v "^./(artifacts|data/real_data_fulltext|data/training_exports)/"
```

## 8) Publish Steps

1. Create clean repo/branch for release.
2. Add files selected in Section 6.
3. Commit with message like: `release: open-source women-health local training pipeline`.
4. Push and publish repository.
5. If publishing adapters, include:
   - base model ID
   - adapter config
   - training date
   - known limitations/safety boundaries
6. Add issue templates for bug reports and data-license concerns.

## 9) Post-Release Maintenance

- [ ] Track issues for unsafe outputs and template collapse regressions.
- [ ] Keep `MODEL_CARD.md` updated per training run.
- [ ] Add run logs for significant pipeline changes.
- [ ] Version adapter artifacts (`v1`, `v1.1`, etc.) with changelog notes.
