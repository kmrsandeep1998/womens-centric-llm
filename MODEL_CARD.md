# Model Card: Tracky Women’s Health Assistant (LoRA)

## Overview

This repository provides a women‑centric health assistant built with:
- rule‑based safety + risk routing
- retrieval‑augmented grounding (RAG)
- LoRA fine‑tuning of a small open model (MLX)

This model is **educational**, not diagnostic.

## Model Type

- Base model: `mlx-community/Qwen2.5-1.5B-Instruct-8bit`
- Fine‑tuning: LoRA adapters
- Context length: 2048 tokens

## Intended Use

- Educational support for menstrual and women’s health topics
- Safety‑first triage routing (urgent vs routine)
- Structured follow‑up question suggestions

## Out of Scope

- Medical diagnosis
- Emergency care decisions
- Legal/financial advice

## Training Data Summary

Two sources:
1) **Synthetic interaction data** (prototype only)
2) **Real-data pipeline** from open‑access literature:
   - OpenAlex (metadata)
   - Europe PMC (licensed OA full text)
   - Human review required before training inclusion

## Safety

- Hard safety escalation rules are in `docs/policies/safety_policy.md`
- High‑risk outputs should be clinician reviewed before use

## Limitations

- Model can hallucinate without RAG
- Quality depends on review rigor
- Synthetic data can create template‑like responses

## License

Code and adapters are released under Apache‑2.0 unless otherwise noted.
