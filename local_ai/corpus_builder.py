from __future__ import annotations

from pathlib import Path
import csv
import json
import re

from .docx_utils import extract_docx_paragraphs, iter_unique_docx


ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS = ROOT / "artifacts"
DATA_DIR = ROOT / "data"
DOCS_DIR = ROOT / "docs"
RAW_DOCS_DIR = ROOT / "raw_docs"


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def chunk_paragraphs(paragraphs, max_chars=1200):
    chunks = []
    buf = []
    size = 0
    for para in paragraphs:
        if size and size + 1 + len(para) > max_chars:
            chunks.append("\n".join(buf))
            buf = [para]
            size = len(para)
        else:
            buf.append(para)
            size += len(para) + 1
    if buf:
        chunks.append("\n".join(buf))
    return chunks


def infer_domain_from_name(name: str) -> str:
    lowered = name.lower()
    if "addon" in lowered:
        return "women_health_extension"
    if "final_extension" in lowered:
        return "women_health_extension"
    if "knowledge_base" in lowered:
        return "women_health_core"
    if "reference" in lowered or "menstrual" in lowered:
        return "menstrual_reproductive_core"
    return "women_health_general"


def build_reference_records():
    path = DATA_DIR / "reference_chunks.jsonl"
    rows = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        rows.append(
            {
                "chunk_id": record["chunk_id"],
                "source_title": record["source_id"],
                "source_type": "official_reference_chunk",
                "domain_group": record["topic_tags"][0] if record["topic_tags"] else "unknown",
                "topic_tags": record["topic_tags"],
                "text": record["text"],
                "claim_summary": record["claim_summary"],
                "evidence_strength": "validated",
                "license_status": record["license_status"],
                "geography_scope": "global_basics",
                "life_stage_scope": "mixed",
                "safety_relevance": "high",
                "trainability": "retrieval_only",
                "validation_status": "guideline_or_official_source_backed",
                "notes": "",
            }
        )
    return rows


def build_markdown_records():
    files = [
        # Keep curated planning docs explicit so they do not regress in future if renamed.
        DOCS_DIR / "planning" / "women_health_dataset_design.md",
        DOCS_DIR / "planning" / "women_health_expansion_roadmap.md",
        DOCS_DIR / "planning" / "documents_analysis_and_llm_plan.md",
    ]
    reference_dir = DOCS_DIR / "references"
    reference_files = sorted(reference_dir.glob("*.md")) if reference_dir.exists() else []
    files = sorted(set(files + reference_files))
    rows = []
    for path in files:
        if not path.exists():
            continue
        text = path.read_text()
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        for idx, chunk in enumerate(chunk_paragraphs(paragraphs), 1):
            rows.append(
                {
                    "chunk_id": f"MD_{slugify(path.stem)}_{idx:03d}",
                    "source_title": str(path.relative_to(ROOT)),
                    "source_type": "local_markdown_summary",
                    "domain_group": infer_domain_from_name(path.name),
                    "topic_tags": [infer_domain_from_name(path.name)],
                    "text": chunk,
                    "claim_summary": chunk.splitlines()[0][:160],
                    "evidence_strength": "summary",
                    "license_status": "local_workspace",
                    "geography_scope": "mixed",
                    "life_stage_scope": "mixed",
                    "safety_relevance": "medium",
                    "trainability": "review_before_training",
                    "validation_status": "local_summary_needs_source_trace",
                    "notes": "",
                }
            )
    return rows


def build_docx_records():
    paths = sorted(RAW_DOCS_DIR.glob("*.docx"))
    rows = []
    for path in iter_unique_docx(paths):
        paragraphs = extract_docx_paragraphs(path)
        chunks = chunk_paragraphs(paragraphs)
        for idx, chunk in enumerate(chunks, 1):
            rows.append(
                {
                    "chunk_id": f"DOCX_{slugify(path.stem)}_{idx:03d}",
                    "source_title": str(path.relative_to(ROOT)),
                    "source_type": "local_docx_manual",
                    "domain_group": infer_domain_from_name(path.name),
                    "topic_tags": [infer_domain_from_name(path.name)],
                    "text": chunk,
                    "claim_summary": chunk.splitlines()[0][:160],
                    "evidence_strength": "research_or_manual_summary",
                    "license_status": "local_workspace",
                    "geography_scope": "mixed",
                    "life_stage_scope": "mixed",
                    "safety_relevance": "medium",
                    "trainability": "retrieval_only_until_verified",
                    "validation_status": "needs_manual_review",
                    "notes": "Derived from local docx manual; do not treat as ground truth without validation.",
                }
            )
    return rows


def write_jsonl(path: Path, rows):
    with path.open("w") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=True) + "\n")


def write_csv(path: Path, rows):
    if not rows:
        return
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def build():
    ARTIFACTS.mkdir(exist_ok=True)
    rows = []
    rows.extend(build_reference_records())
    rows.extend(build_markdown_records())
    rows.extend(build_docx_records())

    write_jsonl(ARTIFACTS / "knowledge_corpus.jsonl", rows)
    index_rows = [
        {
            "chunk_id": row["chunk_id"],
            "source_title": row["source_title"],
            "source_type": row["source_type"],
            "domain_group": row["domain_group"],
            "evidence_strength": row["evidence_strength"],
            "license_status": row["license_status"],
            "trainability": row["trainability"],
            "validation_status": row["validation_status"],
        }
        for row in rows
    ]
    write_csv(ARTIFACTS / "knowledge_chunk_index.csv", index_rows)
    validation_rows = [
        {
            "chunk_id": row["chunk_id"],
            "source_title": row["source_title"],
            "validation_status": row["validation_status"],
            "evidence_strength": row["evidence_strength"],
            "trainability": row["trainability"],
            "notes": row["notes"],
        }
        for row in rows
    ]
    write_csv(ARTIFACTS / "knowledge_validation_matrix.csv", validation_rows)
    return {
        "knowledge_corpus": len(rows),
        "index_rows": len(index_rows),
        "validation_rows": len(validation_rows),
    }
