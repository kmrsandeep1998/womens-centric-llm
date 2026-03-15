from __future__ import annotations

from collections import Counter
from math import log
from pathlib import Path
import json
import re


TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str):
    return TOKEN_RE.findall(text.lower())


class KeywordRetriever:
    def __init__(self, rows):
        self.rows = rows
        self.doc_freq = Counter()
        self.doc_terms = []
        self.doc_lengths = []
        for row in rows:
            terms = Counter(tokenize(row["text"]))
            self.doc_terms.append(terms)
            self.doc_lengths.append(sum(terms.values()) or 1)
            for term in terms:
                self.doc_freq[term] += 1
        self.doc_count = len(rows) or 1
        self.avgdl = sum(self.doc_lengths) / len(self.doc_lengths) if self.doc_lengths else 1

    @classmethod
    def from_jsonl(cls, path: Path):
        rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        return cls(rows)

    def score(self, query: str, k1=1.5, b=0.75):
        q_terms = Counter(tokenize(query))
        scores = []
        for idx, terms in enumerate(self.doc_terms):
            score = 0.0
            dl = self.doc_lengths[idx]
            for term, qf in q_terms.items():
                tf = terms.get(term, 0)
                if not tf:
                    continue
                df = self.doc_freq[term]
                idf = log(1 + (self.doc_count - df + 0.5) / (df + 0.5))
                denom = tf + k1 * (1 - b + b * dl / self.avgdl)
                score += idf * ((tf * (k1 + 1)) / denom) * qf
            if score > 0:
                source_weight = {
                    "official_reference_chunk": 1.8,
                    "local_markdown_summary": 0.9,
                    "local_docx_manual": 0.55,
                }.get(self.rows[idx].get("source_type"), 1.0)
                validation_weight = {
                    "guideline_or_official_source_backed": 1.4,
                    "local_summary_needs_source_trace": 0.8,
                    "needs_manual_review": 0.5,
                }.get(self.rows[idx].get("validation_status"), 1.0)
                score *= source_weight * validation_weight
                scores.append((score, self.rows[idx]))
        scores.sort(key=lambda item: item[0], reverse=True)
        return scores

    def search(self, query: str, top_k=5):
        return [row for _, row in self.score(query)[:top_k]]
