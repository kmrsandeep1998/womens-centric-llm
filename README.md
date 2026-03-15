# Tracky Women-Centric AI Starter Pack

This repository contains a local women-centric AI assistant prototype built around:

- curated women’s-health knowledge
- structured datasets
- retrieval
- deterministic safety rules
- benchmark evaluation
- optional local generation through Ollama

Start with [codex_memory.md](codex_memory.md). It is the fastest way for a new engineer or agent to recover context.

## Quick Start (5 Commands)

Run from repo root:

```bash
python3 scripts/build_knowledge_corpus.py
python3 scripts/build_training_partitions.py --input data/interaction_examples.jsonl --now 2026-03-15
python3 scripts/export_finetune_dataset.py --require-review
python3 scripts/prepare_mlx_chat_dataset.py
python3 -m mlx_lm lora -c artifacts/mlx_lora_qwen25_1p5b/adapter_config.json --train
```

Quick test (tuned adapter):

```bash
python3 -m mlx_lm generate \
  --model mlx-community/Qwen2.5-1.5B-Instruct-8bit \
  --adapter-path artifacts/mlx_lora_qwen25_1p5b \
  --prompt "I have very heavy bleeding with clots and feel dizzy. Is this urgent?" \
  --max-tokens 220 --temp 0.2
```

## Repo Layout

```text
data/        core datasets and schema
docs/        planning, policy, and reference docs
raw_docs/    source docx manuals added by the user
local_ai/    runtime package
prompts/     model prompt templates
scripts/     build, validate, benchmark, and run scripts
artifacts/   generated outputs (ignored in git)
```

## Most Important Files

- [codex_memory.md](codex_memory.md): resumable project memory
- [data/source_catalog.csv](data/source_catalog.csv): source ledger
- [data/reference_chunks.jsonl](data/reference_chunks.jsonl): validated retrieval chunks
- [data/structured_cases.jsonl](data/structured_cases.jsonl): structured seed cases
- [data/interaction_examples.jsonl](data/interaction_examples.jsonl): seed interaction examples
- [data/review_queue.jsonl](data/review_queue.jsonl): cases waiting for review
- [data/train_interactions.jsonl](data/train_interactions.jsonl): train split examples
- [data/validation_interactions.jsonl](data/validation_interactions.jsonl): validation split examples
- [data/safety_train.jsonl](data/safety_train.jsonl): safety escalation examples
- [data/benchmark_eval_set.jsonl](data/benchmark_eval_set.jsonl): benchmark suite
- [data/training_schema.json](data/training_schema.json): schema
- [data/interaction_expansion_templates.jsonl](data/interaction_expansion_templates.jsonl): templates for synthetic interaction growth
- [data/training_exports/](data/training_exports/): generated fine-tune-ready dataset artifacts (rebuild via script)
- [docs/policies/safety_policy.md](docs/policies/safety_policy.md): safety rules
- [docs/policies/review_workflow.md](docs/policies/review_workflow.md): review process
- [docs/policies/data_quality_rules.md](docs/policies/data_quality_rules.md): quality requirements for split datasets
- [local_ai/assistant.py](local_ai/assistant.py): assistant orchestration
- [docs/planning/step_by_step_execution_plan.md](docs/planning/step_by_step_execution_plan.md): inference and contribution playbook
- [docs/planning/dataset_context_and_flow.md](docs/planning/dataset_context_and_flow.md): data-flow and context-building map

## Commands

Validate datasets:

```bash
python3 scripts/validate_datasets.py
python3 scripts/describe_dataset_context.py
```

One-shot refresh pipeline (recommended for local reproducibility):

```bash
python3 scripts/one_shot_train_pipeline.py \
  --skip-train \
  --skip-generate \
  --max-downloads 5000 \
  --download-log-every 1 \
  --download-print-progress \
  --continue-on-fail
```

This command performs in order:

- (optional) Europe PMC full-text download
- XML → review candidate conversion
- partition rebuild (train/validation/safety/review)
- assistant output backfill/cleanup
- final dataset validation

Template augmentation (`enrich_assistant_outputs.py` + `variate_assistant_outputs.py`) is now opt-in:

```bash
python3 scripts/one_shot_train_pipeline.py --enable-template-augmentation
```

Use this only when you explicitly want synthetic style shaping; it can increase repetitive response patterns.

## Training Pipeline Overview

Default local pipeline (`scripts/one_shot_train_pipeline.py`) runs in this order:

1. (optional) download licensed Europe PMC XML
2. XML to review-candidate conversion
3. partition build (`train` / `validation` / `safety_train` / `review_queue`)
4. backfill missing assistant outputs
5. cleanup pass to remove noisy/template artifacts
6. partition rebuild
7. dataset validation
8. optional LoRA training (`mlx_lm lora`)
9. optional smoke generation

Defaults and safety:

- `enrich_assistant_outputs.py` and `variate_assistant_outputs.py` are **disabled by default**
- enable only with `--enable-template-augmentation`
- this default avoids template-collapse behavior in fine-tuned outputs

Reproducible run (data prep only):

```bash
python3 scripts/one_shot_train_pipeline.py --skip-download --skip-train --skip-generate
```

Reproducible run (train included):

```bash
python3 scripts/one_shot_train_pipeline.py --skip-download --skip-generate
```

Evaluation check (base vs tuned):

```bash
python3 scripts/compare_base_vs_finetune_50.py --count 50 --max-tokens 220 --temp 0.2
```

## Model Stack and Usage

This project uses three runtime modes:

1. RAG + rules (recommended app mode)
2. Base model only (no adapter)
3. Fine-tuned model (base + LoRA adapter)

### Base and tuned model IDs

- Base model: `mlx-community/Qwen2.5-1.5B-Instruct-8bit`
- Adapter path (local training output): `artifacts/mlx_lora_qwen25_1p5b`
- LoRA config: `artifacts/mlx_lora_qwen25_1p5b/adapter_config.json`

Why this base model:
- Runs on Apple Silicon with MLX
- Small enough for local iteration
- Good instruction-following baseline for safety-focused LoRA adaptation

### Local setup: RAG pipeline

Build retrieval corpus:

```bash
python3 scripts/build_knowledge_corpus.py
```

Run local assistant (RAG + risk engine path):

```bash
python3 scripts/run_local_assistant.py "My period is late by 8 days and I had unprotected sex 3 weeks ago."
```

### Local setup: base vs tuned generation

Base model only:

```bash
python3 -m mlx_lm generate \
  --model mlx-community/Qwen2.5-1.5B-Instruct-8bit \
  --prompt "I have very heavy bleeding with clots and feel dizzy. Is this urgent?" \
  --max-tokens 220 --temp 0.2
```

Fine-tuned model (base + adapter):

```bash
python3 -m mlx_lm generate \
  --model mlx-community/Qwen2.5-1.5B-Instruct-8bit \
  --adapter-path artifacts/mlx_lora_qwen25_1p5b \
  --prompt "I have very heavy bleeding with clots and feel dizzy. Is this urgent?" \
  --max-tokens 220 --temp 0.2
```

### Training flow (required order)

Before training, always rebuild export files (prevents stale training data):

```bash
python3 scripts/build_training_partitions.py --input data/interaction_examples.jsonl --now 2026-03-15
python3 scripts/export_finetune_dataset.py --require-review
python3 scripts/prepare_mlx_chat_dataset.py
python3 -m mlx_lm lora -c artifacts/mlx_lora_qwen25_1p5b/adapter_config.json --train
```

### How to improve quality

- Add reviewed real cases (not only synthetic rows)
- Expand benchmark prompts and run `scripts/compare_base_vs_finetune_50.py`
- Keep template augmentation off by default (`--enable-template-augmentation` only when intentional)
- Rebuild partitions and exports on every training run

### Publish a reusable open-source model

You can publish adapters so others can use the tuned model without your local data dump.

Publish:
- adapter files (`adapters.safetensors`, optional checkpoints)
- `adapter_config.json`
- `MODEL_CARD.md` + training notes
- exact base model ID

Consumer usage (after downloading adapter):

```bash
python3 -m mlx_lm generate \
  --model mlx-community/Qwen2.5-1.5B-Instruct-8bit \
  --adapter-path <downloaded_adapter_dir> \
  --prompt "..." \
  --max-tokens 220 --temp 0.2
```

Note:
- This is behavior tuning, not a new foundation model.
- Do not publish restricted/raw full-text corpora unless redistribution rights are explicit.

Expand synthetic interaction examples (preview and write):

```bash
python3 scripts/expand_interaction_dataset.py --dry-run
python3 scripts/expand_interaction_dataset.py
python3 scripts/validate_datasets.py
python3 scripts/build_training_partitions.py --input data/interaction_examples.jsonl --now 2026-03-14
python3 scripts/evaluate_benchmarks.py
```

Build the unified corpus:

```bash
python3 scripts/build_knowledge_corpus.py
```

Run the local assistant without Ollama:

```bash
python3 scripts/run_local_assistant.py "My period is late by 8 days and I had unprotected sex 3 weeks ago."
```

## Reference Ingestion

- Add curated local references to `docs/references/*.md`.
- The knowledge builder auto-loads all markdown files in `docs/references`, so new files are indexed on the next `python3 scripts/build_knowledge_corpus.py` run.
- Keep external-source claims in `data/source_catalog.csv` and `data/reference_chunks.jsonl` for traceable citations.

### Crawl + Training-Reference Ingestion

Use these two commands to add new web evidence for retrieval training:

1. Crawl targeted women-health pages:

```bash
python3 scripts/run_web_crawl.py \
  --concurrency 20 \
  --per-domain 10 \
  --depth 3 \
  --timestamped-output \
  --ingest
```

2. Convert crawl output into source catalog + reference chunks:

```bash
python3 scripts/ingest_web_crawl.py --dry-run
python3 scripts/ingest_web_crawl.py
```

Output files:
- `data/web_crawl/health_pages.jsonl` (raw crawl output, generated)
- `data/source_catalog.csv` (updated with new `source_id`s)
- `data/reference_chunks.jsonl` (new chunks appended)
- `data/web_crawl_manifest.json` (run summary)

Crawler output now includes the following fields (plus metadata used by ingestion):
- `url`, `canonical_url`, `title`, `publication_date`, `fetched_at`, `content_sha1`, `content`
- `language`, `http_status`, `fetched_host`, `source`

Then rebuild corpus:

```bash
python3 scripts/build_knowledge_corpus.py
```

Why this helps: crawled web content is used for **retrieval grounding**. It does not directly train the model.

To move crawled evidence into model training, interaction rows still need explicit review + partitioning + export in the interaction datasets.

### India Domain List Builder (optional)

If you want a large India-region domain list sourced from public directories, use:

```bash
python3 scripts/build_india_domain_list.py
```

Outputs:
- `data/domain_lists/india_gov_domains.txt`
- `data/domain_lists/india_gov_seed_urls.txt`

Then crawl using:

```bash
python3 scripts/run_web_crawl.py \
  --seed-file data/domain_lists/india_gov_seed_urls.txt \
  --allowed-domain-file data/domain_lists/india_gov_domains.txt \
  --concurrency 20 --per-domain 6 --depth 1 --max-pages-per-domain 200 \
  --timestamped-output --ingest
```

### URL Discovery via SerpAPI (optional)

If you want to auto-discover large numbers of URLs:

```bash
SERPAPI_KEY=... python3 scripts/discover_urls_serpapi.py \
  --queries data/seed_lists/women_health_queries.txt \
  --output data/seed_lists/discovered_urls.txt \
  --domains-output data/seed_lists/discovered_domains.txt
```

Then crawl those domains:

```bash
python3 scripts/run_web_crawl.py \
  --seed-file data/seed_lists/discovered_urls.txt \
  --allowed-domain-file data/seed_lists/discovered_domains.txt \
  --concurrency 20 --per-domain 6 --depth 1 --max-pages-per-domain 200 \
  --timestamped-output --ingest
```

### Safe Seed Builder (no API key)

If you want a safe seed list using Wikipedia + PubMed + your allowlist:

```bash
python3 scripts/build_safe_seed_list.py \
  --queries data/seed_lists/women_health_queries.txt \
  --seed-allowlist data/seed_lists/global_health_seeds.txt \
  --include-wikipedia --include-pubmed
```

Then crawl:

```bash
python3 scripts/run_web_crawl.py \
  --seed-file data/seed_lists/manual_seeds.txt \
  --allowed-domain-file data/seed_lists/manual_domains.txt \
  --concurrency 12 --per-domain 4 --depth 1 --max-pages-per-domain 200 \
  --timestamped-output --ingest
```
```

Check Ollama setup:

```bash
python3 scripts/check_ollama_setup.py
ollama list
```

Run with local Llama generation:

```bash
WOMENS_AI_OLLAMA_MODEL=llama3.2:3b python3 scripts/run_local_assistant.py "My period is late by 8 days and I had unprotected sex 3 weeks ago."
```

Run the benchmark suite:

```bash
python3 scripts/evaluate_benchmarks.py
```

Export training-ready interactions (after splits are reviewed):

```bash
python3 scripts/export_finetune_dataset.py                 # export all rows from interaction files (prototype)
python3 scripts/export_finetune_dataset.py --require-review  # export only reviewed rows
```

## Local Fine-Tune Prep (M2/Mac-safe)

Prepare a local prompt/completion dataset (train + validation):

```bash
python3 scripts/prepare_local_finetune_dataset.py
```

Outputs:
- `data/training_exports/local_train.jsonl`
- `data/training_exports/local_valid.jsonl`

Re-run validation after split updates:

```bash
python3 scripts/validate_datasets.py
```

## MLX LoRA Training (Qwen2.5 1.5B)

Notes:
- Requires Apple Silicon with Metal enabled (MLX is not supported on non-Metal devices).
- Training settings are recorded in `artifacts/mlx_lora_qwen25_1p5b/adapter_config.json`.
- The run below overwrites adapters in `artifacts/mlx_lora_qwen25_1p5b/`.

Before training, verify assistant outputs exist (otherwise loss will collapse to ~0.0):

```bash
python3 - <<'PY'
import json
from pathlib import Path
paths = [
    "data/train_interactions.jsonl",
    "data/validation_interactions.jsonl",
    "data/safety_train.jsonl",
]
for p in paths:
    total = nonempty = 0
    for line in Path(p).read_text().splitlines():
        if not line.strip():
            continue
        total += 1
        row = json.loads(line)
        if (row.get("assistant_output") or "").strip():
            nonempty += 1
    print(p, "total", total, "nonempty", nonempty)
PY
```

Backfill empty `assistant_output` values (recommended for synthetic scale data):

```bash
python3 scripts/backfill_assistant_outputs.py --progress-every 50
```

Clean noisy assistant outputs (recommended after backfill):

```bash
python3 scripts/clean_assistant_outputs.py --progress-every 200
```

```bash
python3 -m mlx_lm.lora \
  --model mlx-community/Qwen2.5-1.5B-Instruct-8bit \
  --train \
  --data data/training_exports/mlx_chat \
  --fine-tune-type lora \
  --batch-size 1 \
  --iters 200 \
  --learning-rate 1e-4 \
  --lora-rank 8 \
  --lora-scale 20 \
  --lora-dropout 0 \
  --max-seq-length 2048 \
  --num-layers 16 \
  --save-every 100 \
  --steps-per-eval 200 \
  --steps-per-report 10 \
  --val-batches 25 \
  --grad-accumulation-steps 1 \
  --mask-prompt \
  --adapter-path artifacts/mlx_lora_qwen25_1p5b \
  --seed 0
```

If you want the full local loop (including real-data ingestion + one-shot training + smoke test), see `docs/ops/run_log_2026-03-15.md` and run:

```bash
python3 scripts/one_shot_train_pipeline.py
```

### Base vs Fine-Tuned Comparison (50 Prompts)

```bash
python3 scripts/compare_base_vs_finetune_50.py \
  --count 50 \
  --max-tokens 220 \
  --temp 0.2 \
  --output outputs/compare_base_vs_finetune_50.jsonl
```

This runs each prompt twice in a single process chain:
- base model (`--model` only)
- tuned model (`--adapter-path` set to `artifacts/mlx_lora_qwen25_1p5b`)

The script prints a summary (safety/disclaimer/follow-up/urgency heuristics) and writes all rows to JSONL.

## Real Data Pipeline

See `docs/policies/real_data_pipeline.md` for the crawl → review → train workflow and the ingestion script.
See `docs/ops/run_log_2026-03-15.md` for the current run history and next steps.

## Open‑Source Release

Recommended release artifacts:
- `LICENSE` (Apache‑2.0)
- `MODEL_CARD.md`
- `DATA_SOURCES.md`
- Code + scripts (`scripts/`, `local_ai/`)

Do not publish:
- `artifacts/` (local model artifacts)
- `data/real_data_fulltext/` (full‑text XML)
- large raw candidate files (rebuild via pipeline)

## Current Status

- local corpus builder implemented
- local retrieval and risk engine implemented
- optional Ollama integration implemented
- seed benchmark suite currently passes in the lightweight prototype

## Git Hygiene

Commit:

- `data/`
- `docs/`
- `local_ai/`
- `prompts/`
- `scripts/`
- `raw_docs/` unique files
- `README.md`
- `codex_memory.md`
- `.gitignore`

Do not commit:

- `artifacts/`
- `data/training_exports/`
- `.DS_Store`
- `raw_docs/duplicates/`
- local model caches, virtualenvs, or temporary files
