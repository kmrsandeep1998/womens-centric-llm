# Documents Analysis and Local LLM Build Plan

## What Was Added

The new `.docx` documents materially expand the project beyond the earlier menstrual and reproductive health dataset.

### Files reviewed

- `womens_ai_knowledge_base_v2.docx`
- `womens_ai_addon_v1.docx`
- `womens_ai_final_extension_v2.docx`

### Duplicate files detected

These duplicates are byte-identical copies and do not need separate processing:

- `womens_ai_knowledge_base_v2.docx` = `womens_ai_knowledge_base_v2 (1).docx`
- `womens_ai_addon_v1.docx` = `womens_ai_addon_v1 (1).docx`

## What These New Docs Add

### Base knowledge doc (`womens_ai_knowledge_base_v2.docx`)

Adds large domain depth in:

- reproductive anatomy and physiology
- HPO axis and hormone signaling
- folliculogenesis and ovulation biology
- endometrial phases
- cervical mucus and fertility signs
- lifecycle milestones and ovarian aging
- physical symptoms by phase
- PMS, PMDD, libido, cognition, headaches, GI effects, sleep
- mental health and neurobiology
- nutrition, supplements, phase-based nutrition
- lifestyle factors like stress, exercise, BMI, smoking, alcohol, endocrine disruptors
- sexual activity and relationship effects

### Add-on doc (`womens_ai_addon_v1.docx`)

Adds six critical areas:

- vaginal microbiome
- pelvic floor and chronic pain
- AI/ML and wearables
- sexual dysfunction
- genetics and epigenetics
- India-specific context

### Final extension doc (`womens_ai_final_extension_v2.docx`)

Adds eight more domains:

- preconception health
- endocrine disruptors and environment
- LGBTQ+ and trans menstrual health
- menstrual products
- adolescent puberty education
- disability and menstruation
- cancer screening
- workplace, policy, and partner education

## What This Means for the Project

You now have enough content to plan a broader `women-centric local AI system`.

But you still do **not** have everything required to train a safe custom LLM from scratch.

What you have now:

- strong knowledge coverage
- good topic map
- retrieval seed set
- starter structured cases
- starter interaction examples
- benchmark scenarios
- safety and labeling guidance

What you still lack for a serious local LLM:

- a large rights-cleared training corpus
- reviewed annotation scale
- clinician-reviewed labels
- data ingestion pipelines
- retrieval system
- training/eval code
- experiment tracking
- governance, privacy, and model-card workflow

## Recommended Product Direction

Do **not** start by training a foundation model from scratch.

Build this as a local women-centric assistant in stages:

1. local retrieval knowledge engine
2. local risk/rules engine
3. local structured feature extractor
4. local assistant on top of an open model
5. optional fine-tuning later

This gives you a realistic local system while keeping clinical safety and data needs manageable.

## Recommended Local Model Strategy

### Best v1 local architecture

- Base local model: `Llama 3`, `Mistral`, `Qwen`, or similar open instruct model
- Retrieval: local vector store over your curated women’s health knowledge base
- Risk engine: deterministic Python rules for red flags
- Extractor: structured parser from user text into case JSON
- Answerer: prompt the local model with retrieved evidence + extracted features + safety rules

### Why this is the correct first step

- requires far less data than full LLM pretraining
- runs locally
- easier to audit
- easier to evaluate
- safer for medical-style outputs
- lets you use your current assets immediately

## Step-by-Step Local LLM Plan

### Phase 1: Consolidate the knowledge base

Goal:

- convert all curated knowledge into one machine-usable corpus

Tasks:

1. Extract and normalize text from the `.docx` files
2. De-duplicate overlapping sections
3. Split content into topic-tagged chunks
4. Mark each chunk as:
   - `primary_source_grounded`
   - `secondary_summary`
   - `research_summary`
   - `local_generated_summary`
5. Separate:
   - trainable content
   - retrieval-only content

Outputs:

- `knowledge_corpus.jsonl`
- `knowledge_chunk_index.csv`

### Phase 2: Expand the taxonomy to full women-centric scope

Goal:

- reflect the broader domains introduced by the new docs

New domain groups to add:

- anatomy and physiology
- mental health and neurobiology
- nutrition and supplements
- vaginal microbiome
- pelvic floor and chronic pain
- sexual dysfunction
- genetics and epigenetics
- India-specific localization
- preconception care
- endocrine disruptors
- LGBTQ+ / trans menstrual health
- menstrual products
- disability and menstruation
- cancer screening
- workplace and policy

Outputs:

- updated `domain_coverage_matrix.csv`
- updated `training_schema.json`
- `full_domain_taxonomy.md`

### Phase 3: Define the local system modules

Goal:

- make the local assistant buildable in components

Modules:

1. `ingestion`
   - load CSV/JSONL/docx-derived corpora
2. `chunking`
   - create retrieval chunks with metadata
3. `embedding`
   - build local vector index
4. `retrieval`
   - top-k evidence lookup
5. `feature_extraction`
   - parse user input into structured fields
6. `risk_engine`
   - deterministic escalation logic
7. `response_generator`
   - local model prompt + cited answer
8. `evaluation`
   - benchmark scoring

Outputs:

- module specs
- folder structure
- local run workflow

### Phase 4: Build the training data stack

Goal:

- move from seed examples to usable fine-tuning/eval data

Data layers:

1. `retrieval corpus`
2. `structured case data`
3. `instruction-response examples`
4. `safety refusal / escalation examples`
5. `benchmark eval set`

Tasks:

1. convert current synthetic seed records into schema-compliant training templates
2. create more realistic examples for new domains
3. add clinician-review-needed flags
4. create abstain and uncertainty examples
5. separate:
   - `train`
   - `validation`
   - `benchmark`
   - `safety_only`

Outputs:

- `train_interactions.jsonl`
- `safety_interactions.jsonl`
- `review_queue.jsonl`

### Phase 5: Build the local prototype first

Goal:

- get a working local women-centric assistant before any fine-tuning

Recommended stack:

- Python
- `sentence-transformers` or local embedding model
- FAISS or Chroma
- local open instruct model served with `llama.cpp`, `Ollama`, or `vLLM`

Pipeline:

1. user asks question
2. extractor builds structured case
3. risk engine flags danger
4. retriever fetches evidence
5. local model answers with citations
6. evaluator scores output against benchmark expectations

Outputs:

- runnable local CLI prototype
- local benchmark runner

### Phase 6: Decide on fine-tuning

Only do this after the prototype works.

Use fine-tuning if:

- the local model fails consistently on style or extraction
- benchmark recall is weak
- retrieval alone is insufficient

Do not fine-tune yet for:

- unsupported medical claims
- diagnosis generation
- domains without reviewed examples

Best fine-tuning targets first:

- feature extraction
- safe answer formatting
- follow-up question generation
- abstain/escalation behavior

### Phase 7: Only later consider a custom local LLM

Training from scratch should only be considered if you have:

- very large licensed corpus
- enough compute
- clear reason retrieval + fine-tuning is insufficient
- evaluation and safety pipeline already working

For this project, that is not the current stage.

## Immediate Build Recommendation

The best next implementation step is:

1. create a normalized `knowledge_corpus.jsonl` from all current docs
2. expand schema for the new domains
3. build a local retrieval prototype
4. build a local rule engine
5. run benchmark evaluation locally

## Concrete Decision

If your goal is a `local women-centric AI assistant`, you are ready to build a prototype now.

If your goal is a `fully custom trained women-centric LLM from scratch`, you are not ready yet.

The correct path is:

`local RAG assistant first -> fine-tuned local model second -> custom LLM much later`
