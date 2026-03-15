# Real Data Pipeline (Crawl -> Review -> Training)

This pipeline separates **retrieval evidence** from **trainable interactions**.
Scraped web content is **retrieval-only** unless licensing explicitly allows training.

## 1) Source Curation (Required)

1. Build an allowlist of domains with clear training or retrieval terms.
2. For each source, record:
   - `source_id`, `url`, `organization`, `license_status`
   - `trainable_for_model_flag` (true/false)
3. Only sources marked `trainable_for_model_flag=true` can be used to create trainable interactions.

## 2) Crawl (Retrieval Only by Default)

```bash
python3 scripts/run_web_crawl.py \
  --concurrency 20 \
  --per-domain 10 \
  --depth 3 \
  --timestamped-output \
  --ingest
```

Outputs:
- `data/web_crawl/health_pages.jsonl` (raw pages)
- `data/reference_chunks.jsonl` (chunks)
- `data/source_catalog.csv` (source metadata)

## 3) Build Retrieval Corpus

```bash
python3 scripts/build_knowledge_corpus.py
```

This is used at runtime for citations. It does **not** train the model.

## 4) Create Real Interaction Cases

Create a JSONL file with reviewed cases (one per line):

```json
{
  "raw_input": "My period is 10 days late and I had unprotected sex last month.",
  "normalized_case_summary": "Late period after unprotected sex",
  "extracted_features": {"unprotected_sex_recent": true, "stress_level": "high"},
  "assistant_output": "Short, safe, educational response with next steps.",
  "citations": ["SRC006", "SRC007"],
  "risk_level": "routine_review",
  "care_recommendation": "Monitor; test for pregnancy if late.",
  "abstained": false
}
```

Then ingest:

```bash
python3 scripts/ingest_real_cases.py --input data/real_cases.jsonl
```

This appends to `data/review_queue.jsonl`.

## 5) Review + Promotion

Move reviewed cases into:
- `data/train_interactions.jsonl`
- `data/validation_interactions.jsonl`
- `data/safety_train.jsonl`

Only `human_reviewed` or `clinician_reviewed` rows should be used for training.

## 6) Export + Train

```bash
python3 scripts/export_finetune_dataset.py --require-review
python3 scripts/prepare_mlx_chat_dataset.py
python3 -m mlx_lm lora -c artifacts/mlx_lora_qwen25_1p5b/adapter_config.json --train
```

## Notes

- Crawled data is used for **retrieval grounding**, not model training.
- Training data must be **reviewed** and **licensed** for training use.
