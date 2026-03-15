#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from local_ai.retrieval import KeywordRetriever


def load_jsonl(path: Path):
    rows = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))
    return rows


def parse_args():
    parser = argparse.ArgumentParser(description="Compare retrieval results with/without a specific source file.")
    parser.add_argument(
        "--corpus",
        default="artifacts/knowledge_corpus.jsonl",
        help="Path to the knowledge corpus JSONL.",
    )
    parser.add_argument(
        "--benchmarks",
        default="data/benchmark_eval_set.jsonl",
        help="Benchmark dataset JSONL with input field.",
    )
    parser.add_argument(
        "--exclude-source",
        default="docs/references/women_health_supplemental_reproductive_lifecycle.md",
        help="source_title to exclude for comparison.",
    )
    parser.add_argument("--top-k", type=int, default=5, help="Top-k retrieval depth.")
    parser.add_argument(
        "--input-field",
        default="input",
        help="Field name that contains the query text (e.g., input or raw_input).",
    )
    return parser.parse_args()


def _top_ids(retriever: KeywordRetriever, query: str, top_k: int):
    scored = retriever.score(query)
    if not scored:
        return [], 0.0
    top = scored[:top_k]
    ids = [row["chunk_id"] for _, row in top]
    top1_score = top[0][0] if top else 0.0
    return ids, top1_score


def main():
    args = parse_args()
    corpus_rows = load_jsonl(Path(args.corpus))
    benchmark_rows = load_jsonl(Path(args.benchmarks))

    if not corpus_rows:
        raise SystemExit(f"No corpus rows found: {args.corpus}")
    if not benchmark_rows:
        raise SystemExit(f"No benchmark rows found: {args.benchmarks}")

    excluded = [row for row in corpus_rows if row.get("source_title") == args.exclude_source]
    filtered_rows = [row for row in corpus_rows if row.get("source_title") != args.exclude_source]

    full_retriever = KeywordRetriever(corpus_rows)
    filtered_retriever = KeywordRetriever(filtered_rows)

    topk = args.top_k
    hit_count = 0
    top1_changed = 0
    overlap_scores = []
    score_deltas = []

    for row in benchmark_rows:
        query = row.get(args.input_field, "")
        query = (query or "").strip()
        if not query:
            continue

        full_ids, full_top1 = _top_ids(full_retriever, query, topk)
        filtered_ids, filtered_top1 = _top_ids(filtered_retriever, query, topk)

        if excluded:
            if any(
                chunk_id in {r["chunk_id"] for r in excluded} for chunk_id in full_ids
            ):
                hit_count += 1

        if full_ids[:1] != filtered_ids[:1]:
            top1_changed += 1

        if full_ids or filtered_ids:
            overlap = len(set(full_ids) & set(filtered_ids)) / max(len(set(full_ids) | set(filtered_ids)), 1)
            overlap_scores.append(overlap)
        score_deltas.append(full_top1 - filtered_top1)

    total = len([r for r in benchmark_rows if (r.get(args.input_field) or "").strip()])
    print("Retrieval impact comparison")
    print(f"- benchmark_queries: {total}")
    print(f"- excluded_source: {args.exclude_source}")
    print(f"- excluded_chunks: {len(excluded)}")
    print(f"- hit_rate_in_top_{topk}: {hit_count}/{total} ({(hit_count/total*100):.1f}%)")
    print(f"- top1_changed: {top1_changed}/{total} ({(top1_changed/total*100):.1f}%)")
    if overlap_scores:
        print(f"- avg_top_{topk}_overlap: {mean(overlap_scores):.3f}")
    if score_deltas:
        print(f"- avg_top1_score_delta: {mean(score_deltas):.4f}")


if __name__ == "__main__":
    main()
