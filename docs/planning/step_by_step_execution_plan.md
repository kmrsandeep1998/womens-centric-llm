# Women-Centric AI: Step-by-Step Execution Plan

This file is the practical runbook: if a new person clones this repo and asks a question in code or in runtime, this is what happens.

## A) Runtime Flow for One User Question

1. User sends a question string to `scripts/run_local_assistant.py`.
2. `LocalWomensHealthAssistant.answer()` runs:
   1. Extract structured features with `local_ai/feature_extractor.py`
      - age/life stage estimates
      - period timing, bleeding intensity, symptoms
      - sexual/reproductive context, breastfeeding/postpartum flags
      - medication/history hints
   2. Run safety/risk scoring in `local_ai/risk_engine.py`
      - maps text+features to ordered risk levels
      - records reason phrases in `risk_findings`
   3. Retrieve top-k matching corpus snippets from `local_ai/retrieval.py`
      - reads `artifacts/knowledge_corpus.jsonl`
   4. Compose response:
      - if `WOMENS_AI_OLLAMA_MODEL` is set, call Ollama `/api/generate`
      - else use local deterministic `_fallback_answer()`
   5. Return structured JSON:
      - `answer`, `citations`, `risk_level`, `care_recommendation`, `follow_up_questions`, `risk_findings`, `extracted_features`
3. The JSON can be consumed directly by UI, API wrapper, or debugging script.

### What happens inside each stage

1. **Input intake**
   - User text goes to the local process as raw text.
   - No full medical record is loaded unless the caller provides conversation history.
2. **Feature extraction (`local_ai/feature_extractor.py`)**
   - Heuristics extract age, LMP timing, flow/heavy bleed signals, sex/pregnancy context, postpartum/breastfeeding state, contraception, and risk indicators.
   - Output is placed in `extracted_features`.
3. **Risk computation (`local_ai/risk_engine.py`)**
   - Risk rules generate `risk_level` (`normal_variation` to `emergency_care`) and `risk_findings`.
4. **Retrieval (`local_ai/retrieval.py`)**
   - BM25-like lexical search over `artifacts/knowledge_corpus.jsonl` scores chunks by term overlap + metadata weights.
   - Top matches become evidence in the prompt and citations.
5. **Response generation**
   - If `WOMENS_AI_OLLAMA_MODEL` is set: local call to Ollama `/api/generate` with system prompt, user text, risk, features, and claims.
   - Else: deterministic fallback from `local_ai/assistant.py`.
6. **Output assembly**
   - Returns structured JSON:
     - `answer`, `citations`, `risk_level`, `care_recommendation`, `follow_up_questions`, `risk_findings`, `extracted_features`.

## B) Current System Type (important to understand limits)

This is a **RAG + rules + optional open LLM** stack.

- It is not from-scratch model training yet.
- It is not a tuned “deeply personalized medical model” yet.
- It is safe for:
  - constrained women’s health Q&A
  - triage routing
  - feature capture
- It is not safe to use as a diagnostic tool.

## C) If someone forks the repo

1. `git clone <repo>`
2. `python3 scripts/build_knowledge_corpus.py` (when raw_docs changed)
3. `python3 scripts/validate_datasets.py`
4. Ask questions:
   - `python3 scripts/run_local_assistant.py "My period is late..."`  
   - `WOMENS_AI_OLLAMA_MODEL=... python3 scripts/run_local_assistant.py ...` for generation
5. Optional:
   - `python3 scripts/evaluate_benchmarks.py` for regression checks
   - `python3 scripts/build_training_partitions.py` after review status updates

## D) What to Push vs Keep Local

Push:
- `data/` (schemas, interactions, benchmark, source catalogs, split files)
- `docs/` (planning, policies, references, memory docs)
- `local_ai/` (retriever, features, risk engine, assistant)
- `scripts/` (build/validate/eval/run scripts)
- `prompts/`
- non-duplicate source docs in `raw_docs/`
- `README.md`, `codex_memory.md`

Do not push:
- `artifacts/` (generated corpus/index artifacts)
- `raw_docs/duplicates/`
- caches, virtualenvs, binary LLM files (`.gguf`, `.bin`)

## E) Step-by-Step Path to Build a Better Model (from here)

1. Increase source quality and licensing clarity
   - complete `docs/references` inventory
   - keep only rights-cleared, versioned content
2. Expand training data
   - more synthetic + clinically reviewed interactions
   - structured labels for all critical branches
   - separate examples by `review_status`
3. Improve extraction
   - move from rule-only parsing to lightweight LLM-assisted extraction
   - preserve deterministic fallback for safety
4. Add dedicated label classifier
   - keep strict safety labels separate from general answer quality labels
5. Train progressively
   - start with retrieval + risk-only tuning
   - then fine-tune a small instruction model only on curated JSON pairs
6. Add evaluator + governance gates
   - run benchmark suite on every commit
   - add abstention/false-positive checks
   - log reviewer decisions and audit drift

## F) What’s Safe to Explain in a Single User Query

- This pipeline answers the question in one pass.
- It does not “read entire internet” at request time; it reasons over the built corpus + local rules.
- If model output is missing or inconsistent, it still returns deterministic fallback with safety language and follow-ups.

## G) Dataset Expansion Loop (What to run now)

Run this whenever you want to grow the interaction dataset quickly and safely.

1. Generate new synthetic interaction rows from templates:

```bash
python3 scripts/expand_interaction_dataset.py
```

2. Validate the expanded file:

```bash
python3 scripts/validate_datasets.py
```

3. Rebuild review queue / splits:

```bash
python3 scripts/build_training_partitions.py --input data/interaction_examples.jsonl --now 2026-03-14T00:00:00Z
```

4. Run benchmark checks again:

```bash
python3 scripts/evaluate_benchmarks.py
```

5. Push only approved reviewed artifacts:
- Keep `data/*`, `docs/*`, `local_ai/*`, `scripts/*`, `prompts/*`, and markdown references in git.
- Rebuild local `artifacts/` during setup, not from repo.

## H) 10K+ Scale and Why Train Split Can Still Be 0

`build_training_partitions.py` only puts rows in train/validation/safety when `review_status` is:

- `human_reviewed`
- `clinician_reviewed`

Rows with `pending_human_review` are intentionally routed to `data/review_queue.jsonl`, so large synthetic generation alone can still produce:

- `interaction_examples.jsonl: 10000`
- `train_interactions.jsonl: 0`
- `review_queue.jsonl: 10000`

For now (prototype) you can force a large, ready file with this sequence:

1. Generate synthetic scale:
   ```bash
   python3 scripts/generate_scaled_interaction_dataset.py --target 10000 --seed 42
   ```
2. Promote rows for prototyping (do not treat as clinically reviewed):
   ```bash
   python3 scripts/set_review_status.py --status human_reviewed --max-records 10000
   ```
3. Rebuild splits:
   ```bash
   python3 scripts/build_training_partitions.py --input data/interaction_examples.jsonl --now 2026-03-14
   ```
4. Export finetune files:
   ```bash
   python3 scripts/export_finetune_dataset.py
   ```

When you are ready for production-grade training, run only reviewed approvals and:

```bash
python3 scripts/set_review_status.py --status human_reviewed --from-status pending_human_review --max-records 250 --seed 42 --random-sample
```

then audit each reviewed batch before continuing. Only then use:

```bash
python3 scripts/export_finetune_dataset.py --require-review
```

## I) First-Run Template Growth

Templates live in:

- `data/interaction_expansion_templates.jsonl`

To preview generated records before writing:

```bash
python3 scripts/expand_interaction_dataset.py --dry-run
```

If this produces only duplicates, update the template file with new user inputs.

## J) Fine-Tune Export (after review is complete)

Run this once reviewed rows exist in split files:

```bash
python3 scripts/build_training_partitions.py --input data/interaction_examples.jsonl --now 2026-03-14
python3 scripts/export_finetune_dataset.py --require-review
```

Generated files:

- `data/training_exports/interaction_finetune_chat.jsonl`
- `data/training_exports/interaction_finetune_completion.jsonl`
- `data/training_exports/interaction_finetune_metadata.jsonl`

## K) Crawler + Crawl-Ingestion Flow

1. Crawl:

```bash
python3 scripts/run_web_crawl.py \
  --concurrency 20 \
  --per-domain 10 \
  --depth 3 \
  --max-pages-per-domain 3000 \
  --max-links-per-page 25 \
  --timestamped-output \
  --ingest
```

2. Convert crawl output to training reference format:

```bash
python3 scripts/ingest_web_crawl.py --dry-run
python3 scripts/ingest_web_crawl.py
```

What gets produced:
- `data/web_crawl/health_pages.jsonl` (raw content)
- `data/source_catalog.csv` (new `source_id`s for crawled URLs)
- `data/reference_chunks.jsonl` (new chunks with `source_id` traces)
- `data/web_crawl_manifest.json` (audit metadata)

Then refresh knowledge corpus:

```bash
python3 scripts/build_knowledge_corpus.py
```

Alternative lower-level command (same crawler, manual settings):

```bash
python3 -m scrapy runspider scripts/scrapers/women_health_spider.py \
  -a max_depth=3 -a max_links_per_page=25 -a min_content_chars=180 \
  -s CONCURRENT_REQUESTS=20 -s CONCURRENT_REQUESTS_PER_DOMAIN=10 \
  -s CLOSESPIDER_PAGECOUNT=1000000
```

### Crawling vs training (quick mental model)

- Crawling **collects knowledge** from web pages.
- `ingest_web_crawl.py` turns that raw crawl into `data/reference_chunks.jsonl` and updates `data/source_catalog.csv`.
- `build_knowledge_corpus.py` makes `artifacts/knowledge_corpus.jsonl` for runtime retrieval.
- Retrieval chunks guide what the assistant cites and talks about.
- Training files are separate: `data/interaction_examples.jsonl`, `train_interactions.jsonl`, `validation_interactions.jsonl`, etc.

## L) India Domain List Builder (optional)

If you need a large India-region domain list from public directories:

```bash
python3 scripts/build_india_domain_list.py
```

Outputs:
- `data/domain_lists/india_gov_domains.txt`
- `data/domain_lists/india_gov_seed_urls.txt`

Then run the crawler against those domains:

```bash
python3 scripts/run_web_crawl.py \
  --seed-file data/domain_lists/india_gov_seed_urls.txt \
  --allowed-domain-file data/domain_lists/india_gov_domains.txt \
  --concurrency 20 --per-domain 6 --depth 1 --max-pages-per-domain 200 \
  --timestamped-output --ingest
```
