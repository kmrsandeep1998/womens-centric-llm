# Local Women-Centric AI Build Checklist

## Stage 1: Consolidate Inputs

- [ ] Extract text from all unique `.docx` files
- [ ] Ignore duplicate `(1)` copies
- [ ] Normalize all text into UTF-8 plain text
- [ ] Split by domain and subsection
- [ ] Tag each section with domain metadata
- [ ] Separate retrieval-only from trainable content

## Stage 2: Expand Dataset Structure

- [ ] Add new domain groups from the new docs
- [ ] Add fields for microbiome, pelvic floor, sexual dysfunction, genetics, disability, preconception, products, policy
- [ ] Add localization fields for geography and cultural context
- [ ] Add model behavior fields for uncertainty and escalation

## Stage 3: Build Local Knowledge Corpus

- [ ] Create `knowledge_corpus.jsonl`
- [ ] Create chunk-level metadata
- [ ] Add provenance to every chunk
- [ ] Add source quality ranking
- [ ] Add domain tags

## Stage 4: Build Local Retrieval

- [ ] Choose embedding model
- [ ] Create vector index
- [ ] Add metadata filters
- [ ] Add citation tracking
- [ ] Test retrieval on benchmark queries

## Stage 5: Build Local Structured Engine

- [ ] Create user-input parser
- [ ] Extract structured case features
- [ ] Add red-flag detection
- [ ] Add risk scoring
- [ ] Add abstain logic

## Stage 6: Build the Local Assistant

- [ ] Select local open model
- [ ] Define prompt format
- [ ] Pass in extracted features + retrieved evidence + safety rules
- [ ] Return answer + citations + care level + follow-up questions

## Stage 7: Evaluate

- [ ] Run benchmark set
- [ ] Score safety recall
- [ ] Score citation use
- [ ] Score hallucination failures
- [ ] Score consistency across paraphrases

## Stage 8: Fine-Tune Only If Needed

- [ ] Build train/validation split
- [ ] Create instruction-response pairs
- [ ] Add safety-heavy examples
- [ ] Fine-tune for extraction and response formatting first

## Stage 9: Governance

- [ ] Add model card
- [ ] Add privacy statement
- [ ] Add source-usage statement
- [ ] Add clear limitations
- [ ] Add review process for high-risk outputs
