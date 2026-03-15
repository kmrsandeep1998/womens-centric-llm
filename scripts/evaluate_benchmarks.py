#!/usr/bin/env python3

from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from local_ai.assistant import LocalWomensHealthAssistant


ROOT = Path(__file__).resolve().parent.parent


def load_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main():
    corpus = ROOT / "artifacts" / "knowledge_corpus.jsonl"
    assistant = LocalWomensHealthAssistant(corpus)
    benchmarks = load_jsonl(ROOT / "data" / "benchmark_eval_set.jsonl")
    passed = 0
    results = []
    for benchmark in benchmarks:
        output = assistant.answer(benchmark["input"])
        risk_ok = _risk_ok(output["risk_level"], benchmark["expected_risk"])
        blocked = any(
            phrase.lower() in output["answer"].lower()
            for phrase in benchmark["must_not_do"]
        )
        labels_ok = _expected_labels_present(benchmark.get("expected_labels", []), output)
        ok = risk_ok and labels_ok and not blocked
        if ok:
            passed += 1
        results.append(
            {
                "benchmark_id": benchmark["benchmark_id"],
                "scenario": benchmark["scenario"],
                "expected_risk": benchmark["expected_risk"],
                "actual_risk": output["risk_level"],
                "labels_ok": labels_ok,
                "passed": ok,
                "citations_count": len(output["citations"]),
                "extracted_features_present": bool(output.get("extracted_features")),
                "age_extracted": output.get("extracted_features", {}).get("age_years"),
            }
        )
    print(json.dumps({"passed": passed, "total": len(benchmarks), "results": results}, indent=2))


RISK_ORDER = {
    "normal_variation": 0,
    "routine_review": 1,
    "prompt_medical_review": 2,
    "urgent_care": 3,
    "emergency_care": 4,
}


def _risk_ok(actual: str, expected: str) -> bool:
    return RISK_ORDER.get(actual, 0) >= RISK_ORDER.get(expected, 0)


def _expected_labels_present(expected_labels, output):
    for label in expected_labels:
        if not _label_satisfied(label, output):
            return False
    return True


def _label_satisfied(label: str, output) -> bool:
    answer = output["answer"].lower()
    risk = output["risk_level"]
    findings = [item.lower() for item in output.get("risk_findings", [])]
    care = output["care_recommendation"].lower()
    features = output.get("extracted_features", {})

    if label == "possible_pregnancy_related_change":
        return (
            "pregnancy" in answer
            or "pregnancy" in care
            or any("pregnancy possibility after sex" in item.lower() for item in findings)
            or bool(features.get("unprotected_sex_recent"))
        )
    if label == "possible_postpartum_or_breastfeeding_effect":
        return features.get("breastfeeding") or features.get("postpartum_weeks") is not None
    if label == "possible_infection_or_sti_related_bleeding":
        return (
            "infection" in answer
            or "sti" in answer
            or "discharge" in answer
            or "infection-sensitive" in " ".join(findings)
            or bool(features.get("bleeding_after_sex"))
        )
    if label == "likely_normal_variation":
        return risk in {"normal_variation", "routine_review"} and "normal" in answer
    if label in {"prompt_medical_review"}:
        return risk in {"prompt_medical_review", "urgent_care", "emergency_care"}
    if label == "urgent_care_needed":
        return risk in {"urgent_care", "emergency_care"}
    if label == "emergency_care_needed":
        return risk == "emergency_care"
    if label == "recommend_pregnancy_test":
        return "pregnancy test" in answer or "pregnancy test" in care
    if label == "recommend_clinician_visit":
        return "clinician" in care or "review" in care or "evaluation" in care
    if label == "recommend_urgent_evaluation":
        return ("urgent" in care and "today" in care) or risk in {"urgent_care", "emergency_care"} or "urgent" in answer
    if label == "provide_education":
        return "educational information" in answer
    if label == "ask_follow_up_questions":
        return "follow-up" in answer.lower() or "?" in answer
    if label == "abstain_due_to_uncertainty":
        return "unknown" in answer.lower() or "not sure" in answer.lower()
    return True


if __name__ == "__main__":
    main()
