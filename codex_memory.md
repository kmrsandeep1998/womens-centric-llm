# Codex Memory

## Project Summary

This repository is a local women-centric AI assistant project. It currently uses:

1. curated local knowledge and source files
2. structured datasets and benchmark cases
3. deterministic safety/risk rules
4. retrieval over a local corpus
5. optional local generation through Ollama

It is currently a `RAG + rules + open local model` system, not a from-scratch custom-trained LLM.

## Current Working Status

- machine used during setup: `Apple M2 MacBook Air`, `8 GB RAM`
- ollama installed successfully
- pulled local model: `llama3.2:3b`
- local benchmark suite currently passes in the prototype pipeline
- benchmark currently passes current suite: `29/29`
- corpus builder currently produces `249` unified knowledge records

## Repo Structure

```text
README.md
codex_memory.md
.gitignore

data/
  source_catalog.csv
  reference_chunks.jsonl
  structured_cases.jsonl
  interaction_examples.jsonl
  interaction_expansion_templates.jsonl
  benchmark_eval_set.jsonl
  domain_coverage_matrix.csv
  training_schema.json

docs/
  planning/
  policies/
  references/

raw_docs/
  womens_ai_knowledge_base_v2.docx
  womens_ai_addon_v1.docx
  womens_ai_final_extension_v2.docx
  duplicates/   # ignored

local_ai/
prompts/
scripts/
artifacts/      # generated, ignored
```

## Files That Matter Most

### Runtime

- `local_ai/assistant.py`
- `local_ai/risk_engine.py`
- `local_ai/retrieval.py`
- `local_ai/corpus_builder.py`
- `prompts/ollama_system_prompt.txt`

### Datasets

- `data/source_catalog.csv`
- `data/reference_chunks.jsonl`
- `data/structured_cases.jsonl`
- `data/interaction_examples.jsonl`
- `data/interaction_expansion_templates.jsonl`
- `data/review_queue.jsonl`
- `data/training_exports/`
- `data/train_interactions.jsonl`
- `data/validation_interactions.jsonl`
- `data/safety_train.jsonl`
- `data/benchmark_eval_set.jsonl`
- `data/training_schema.json`
- `data/domain_coverage_matrix.csv`

### Policy / planning

- `docs/policies/safety_policy.md`
- `docs/policies/annotation_guidelines.md`
- `docs/policies/label_taxonomy.md`
- `docs/planning/documents_analysis_and_llm_plan.md`
- `docs/policies/data_quality_rules.md`
- `docs/policies/review_workflow.md`
- `docs/planning/step_by_step_execution_plan.md`

## Commands To Resume

Validate the seed datasets:

```bash
python3 scripts/validate_datasets.py
```

Inspect full dataset linkage and split coverage:

```bash
python3 scripts/describe_dataset_context.py
```

Build the unified corpus:

```bash
python3 scripts/build_knowledge_corpus.py
```

Run focused crawl + ingestion:

```bash
python3 scripts/run_web_crawl.py --concurrency 20 --per-domain 10 --depth 3 --timestamped-output --ingest
python3 scripts/ingest_web_crawl.py --dry-run
python3 scripts/ingest_web_crawl.py
```

Check local model setup:

```bash
python3 scripts/check_ollama_setup.py
ollama list
```

Run the local assistant without a model:

```bash
python3 scripts/run_local_assistant.py "My period is late by 8 days and I had unprotected sex 3 weeks ago."
```

Run with local Ollama generation:

```bash
WOMENS_AI_OLLAMA_MODEL=llama3.2:3b python3 scripts/run_local_assistant.py "My period is late by 8 days and I had unprotected sex 3 weeks ago."
```

Run the benchmark suite:

```bash
python3 scripts/evaluate_benchmarks.py
```

Rebuild the training partitions from reviewed interactions:

```bash
python3 scripts/build_training_partitions.py --input data/interaction_examples.jsonl --now 2026-03-14
```

Expand interaction seeds from templates:

```bash
python3 scripts/expand_interaction_dataset.py --dry-run
python3 scripts/expand_interaction_dataset.py
```

Build reviewed splits and export fine-tune data:

```bash
python3 scripts/build_training_partitions.py --input data/interaction_examples.jsonl --now 2026-03-14
python3 scripts/export_finetune_dataset.py --require-review
```

Ad-hoc export preview:

```bash
python3 scripts/export_finetune_dataset.py
```

Run benchmark regression check:

```bash
python3 scripts/evaluate_benchmarks.py
```

Current end-to-end flow:

1. User question enters `LocalWomensHealthAssistant.answer()`
2. Feature extraction builds structured context (`local_ai/feature_extractor.py`)
3. Risk evaluation runs using extracted signals (`local_ai/risk_engine.py`)
4. Relevant snippets are retrieved from local corpus (`local_ai/retrieval.py`)
5. Answer is composed from fallback logic or Ollama generation
6. Output JSON includes `answer`, `risk_level`, `care_recommendation`, `citations`, `follow_up_questions`, and `extracted_features`

The full walkthrough has been documented at [docs/planning/dataset_context_and_flow.md](docs/planning/dataset_context_and_flow.md).

## GitHub Push Guidance

Commit:

- `README.md`
- `codex_memory.md`
- `.gitignore`
- everything under `data/`
- everything under `docs/`
- everything under `local_ai/`
- everything under `scripts/`
- everything under `prompts/`
- unique source files under `raw_docs/`

When committing, skip generated `data/training_exports/` artifacts.

Do not commit:

- `artifacts/`
- `.DS_Store`
- `raw_docs/duplicates/`
- local caches or virtualenvs
- downloaded model storage outside the repo

## Architecture

Current architecture:

```text
User question
 -> risk engine
 -> retrieval over local corpus
 -> optional Ollama model generation
 -> answer + citations + care recommendation + follow-up questions
```

## Important Constraints

- public medical sources in the corpus are mainly retrieval-oriented
- many structured examples are still seed or synthetic-style examples
- this is not yet a clinically validated diagnostic system
- from-scratch LLM training is not the current stage

## Best Next Steps

1. replace seed/synthetic examples with reviewed data
2. enforce quality gate with `scripts/validate_datasets.py`
3. maintain review_queue and split datasets as the training control layer
4. improve extraction and retrieval quality
5. strengthen grounding for the Ollama prompt path
6. prepare train/validation/safety splits for fine-tuning
7. export reviewed interaction records with `scripts/export_finetune_dataset.py` before any trainer-specific step
