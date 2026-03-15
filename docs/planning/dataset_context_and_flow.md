# Dataset Context and End-to-End Flow

This document explains how the repository uses each dataset file when answering a question and when building train-ready data.

## 1) What is a "knowledge context" in this system

When you ask a question, context is built in 3 layers:

1. `textual context` from retrieved knowledge chunks (RAG-style evidence)
2. `structured context` from extracted clinical features (age, period timing, bleeding pattern, sex risk, breastfeeding, red flags, etc.)
3. `risk context` from deterministic safety rules (triage level and escalation logic)

The model (if enabled) receives this combined context and generates the final response.

## 1a) How crawling fits in (simple flow)

1. `scripts/run_web_crawl.py` fetches web pages and writes `data/web_crawl/health_pages.jsonl`.
2. `scripts/ingest_web_crawl.py` reads that file and writes:
   - `data/source_catalog.csv` (source records for traceability)
   - `data/reference_chunks.jsonl` (chunked text + source_id links)
3. `scripts/build_knowledge_corpus.py` builds `artifacts/knowledge_corpus.jsonl` from `data/reference_chunks.jsonl`.
4. At runtime, `local_ai/retrieval.py` searches those chunks to pull only the top-k snippets needed to answer.

So: crawling creates/updateable evidence. It does not itself create `interaction_examples.jsonl` training rows.

## 2) Files and their role

- `data/source_catalog.csv`
  - Governs source metadata and IDs.
  - Required for citation validation.
  - External references (ACOG, NHS, CDC, etc.) are listed here.

- `data/reference_chunks.jsonl`
  - Retrieved evidence chunks for local retrieval.
- `artifacts/knowledge_corpus.jsonl` (generated)
  - Unified retrieval corpus used by the assistant.
  - Built by `scripts/build_knowledge_corpus.py` from:
    - `data/reference_chunks.jsonl`
    - markdown files in `docs/references`
    - `.docx` files in `raw_docs`

- `local_ai/assistant.py`
  - Runtime inference orchestrator.
  - Loads corpus, extracts features, runs risk engine, retrieves top-k chunks, returns answer.

- `local_ai/feature_extractor.py`
  - Converts user text into structured fields (`age_years`, `missed_periods_count`, `bleeding_after_sex`, etc.).

- `local_ai/risk_engine.py`
  - Applies deterministic triage rules.
  - Produces `risk_level` and `risk_findings`.

- `data/interaction_examples.jsonl`
  - Seed + synthetic interaction records.
  - Training candidates before split + review.

- `data/train_interactions.jsonl`, `data/validation_interactions.jsonl`, `data/safety_train.jsonl`
  - Split outputs used for supervised model training/evaluation.

- `data/review_queue.jsonl`
  - Rows waiting for review when rules place them in queue.

- `scripts/export_finetune_dataset.py`
  - Exports reviewed interaction records into trainer-ready formats (`chat`, `completion`, `metadata`).

- `scripts/build_training_partitions.py`
  - Splits reviewed interactions into train/validation/safety based on risk + review rules.

- `data/benchmark_eval_set.jsonl`
  - Regression/eval scenarios with expected risk and labels.

- `artifacts/training_exports/`
  - Generated training files from `export_finetune_dataset.py` (ignored by repo).

## 3) End-to-end flow for one user question

1. User runs:
   - `python3 scripts/run_local_assistant.py "..."`
2. `LocalWomensHealthAssistant.answer(...)` is called.
3. Feature extractor parses the raw question into structured fields.
4. Risk engine computes risk and findings.
5. Keyword retriever searches `artifacts/knowledge_corpus.jsonl` for relevant chunks.
6. Assistant builds response:
   - fallback text, or
   - prompt to Ollama if `WOMENS_AI_OLLAMA_MODEL` is set
7. Output includes:
   - `answer`
   - `citations` (chunk source titles)
   - `risk_level`
   - `care_recommendation`
   - `follow_up_questions`

## 4) Why this is not a full foundation-model training flow yet

- The corpus and retrieval are for grounding.
- The current model behavior is controlled by explicit rules + retrieved snippets.
- Fine-tuning is optional and uses only interaction-style files after human/clinical review.

## 5) How a single data item moves into training

1. Add/adjust `data/interaction_examples.jsonl` rows.
2. Validate (`python3 scripts/validate_datasets.py`).
3. Build partitions:
   - `python3 scripts/build_training_partitions.py --input data/interaction_examples.jsonl --now 2026-03-14`
4. Export train files:
   - `python3 scripts/export_finetune_dataset.py --require-review` (once review is mature)

## 6) Current counts snapshot (check before each iteration)

Run:

```bash
python3 scripts/describe_dataset_context.py
```

to print row counts, split counts, and citation-source linkage summary.
