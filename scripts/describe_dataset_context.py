#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
ARTIFACTS_DIR = ROOT / "artifacts"


def count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text().splitlines() if line.strip())


def load_jsonl(path: Path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def load_csv(path: Path):
    if not path.exists():
        return []
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def source_ids_from_catalog(rows):
    return {row.get("source_id") for row in rows if row.get("source_id")}


def chunk_source_counts(rows):
    counts = Counter(row.get("source_id") for row in rows if row.get("source_id"))
    return counts.most_common(8)


def citation_coverage(rows, source_ids):
    total = 0
    good = 0
    unknown = Counter()
    for row in rows:
        for citation in row.get("citations", []) or []:
            total += 1
            if citation in source_ids:
                good += 1
            else:
                unknown[citation] += 1
    return total, good, dict(unknown)


def print_section(title, payload):
    print(f"\n== {title} ==")
    for key, value in payload.items():
        print(f"{key}: {value}")


def main():
    parser = argparse.ArgumentParser(description="Describe how datasets connect to runtime and training.")
    parser.add_argument("--corpus", default=str(ARTIFACTS_DIR / "knowledge_corpus.jsonl"))
    parser.add_argument("--source-catalog", default=str(DATA_DIR / "source_catalog.csv"))
    args = parser.parse_args()

    corpus_path = Path(args.corpus)
    source_path = Path(args.source_catalog)

    interaction = load_jsonl(DATA_DIR / "interaction_examples.jsonl")
    train = load_jsonl(DATA_DIR / "train_interactions.jsonl")
    validation = load_jsonl(DATA_DIR / "validation_interactions.jsonl")
    safety = load_jsonl(DATA_DIR / "safety_train.jsonl")
    review = load_jsonl(DATA_DIR / "review_queue.jsonl")
    benchmark = load_jsonl(DATA_DIR / "benchmark_eval_set.jsonl")
    source_catalog = load_csv(source_path)
    reference_chunks = load_jsonl(DATA_DIR / "reference_chunks.jsonl")
    corpus = load_jsonl(corpus_path)

    source_ids = source_ids_from_catalog(source_catalog)

    print("Dataset context report")
    print_section(
        "Core Sources",
        {
            "source_catalog_rows": len(source_catalog),
            "reference_chunks_rows": len(reference_chunks),
            "corpus_rows": len(corpus),
            "corpus_exists": corpus_path.exists(),
        },
    )

    print_section(
        "Interaction Data",
        {
            "interaction_examples": len(interaction),
            "train_interactions": len(train),
            "validation_interactions": len(validation),
            "safety_train": len(safety),
            "review_queue": len(review),
            "benchmarks": len(benchmark),
        },
    )

    c_total = count_lines(DATA_DIR / "interaction_examples.jsonl")
    if c_total:
        split_total = len(train) + len(validation) + len(safety) + len(review)
        print_section(
            "Split Integrity",
            {
                "interaction_examples_total": c_total,
                "split_total_sum": split_total,
                "split_coverage_pct": f"{(split_total / c_total * 100):.1f}%",
            },
        )

    if reference_chunks:
        top_sources = chunk_source_counts(reference_chunks)
        top_list = ", ".join(f"{src}:{cnt}" for src, cnt in top_sources)
        print_section("Top Reference Source IDs", {"reference_distribution_top": top_list or "none"})

    if interaction:
        total_citations, known, unknown = citation_coverage(interaction, source_ids)
        print_section(
            "Citation Check (interaction_examples)",
            {
                "citations_total": total_citations,
                "citations_known_in_source_catalog": known,
                "citations_unknown_count": total_citations - known,
                "unknown_top": ", ".join(f"{k}:{v}" for k, v in Counter(unknown).most_common(8)),
            },
        )

    if benchmark:
        labels = Counter()
        for row in benchmark:
            labels[row.get("expected_risk", "unknown")] += 1
        print_section(
            "Benchmark Risk Targets",
            {"expected_risk_distribution": ", ".join(f"{k}:{v}" for k, v in sorted(labels.items()))},
        )

    if source_catalog:
        source_id_list = sorted(list(source_ids))
        recent_ids = source_id_list[:5] + source_id_list[-2:] if len(source_id_list) > 5 else source_id_list
        print_section("Source Metadata", {"sample_source_ids": ", ".join(recent_ids)})

    print("\nHow the pieces connect:")
    print("- interaction files feed build_training_partitions.py")
    print("- training splits feed export_finetune_dataset.py")
    print("- reference_chunks + docs + raw docs feed build_knowledge_corpus.py -> corpus used at inference")
    print("- assistant uses feature extractor + risk engine + corpus retrieval")


if __name__ == "__main__":
    main()
