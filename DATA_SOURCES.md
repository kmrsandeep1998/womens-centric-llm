# Data Sources and Licensing

## Summary

This project separates:
- **Retrieval evidence** (RAG corpus)
- **Training interactions** (reviewed Q&A)

Only sources with explicit training permissions are used for training data.

## Retrieval Sources (RAG)

- Open‑access references indexed into `data/reference_chunks.jsonl`
- Built into `artifacts/knowledge_corpus.jsonl`

## Real‑Data Pipeline Sources

1) **OpenAlex**
   - Metadata only (titles, DOIs, OA status)
   - License: CC0 for metadata

2) **Europe PMC**
   - Full‑text XML for OA articles
   - Per‑article license required before use

## Training Rules

- **Do not** train on sources with unknown or restricted licenses
- All real cases must be human reviewed before inclusion

## Current State

See `docs/ops/run_log_2026-03-15.md` for current pipeline progress.
