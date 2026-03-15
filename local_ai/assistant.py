from __future__ import annotations

from pathlib import Path
import json
import os
from urllib import request

from .feature_extractor import FeatureExtractor
from .retrieval import KeywordRetriever
from .risk_engine import assess_risk


class LocalWomensHealthAssistant:
    def __init__(self, corpus_path: Path):
        self.retriever = KeywordRetriever.from_jsonl(corpus_path)
        self.root = Path(__file__).resolve().parent.parent
        self.extractor = FeatureExtractor()

    def answer(self, user_text: str, top_k=4):
        extracted_features = self.extractor.extract(user_text)
        risk = assess_risk(user_text, extracted_features=extracted_features)
        chunks = self.retriever.search(user_text, top_k=top_k)
        citations = []
        for chunk in chunks:
            if chunk["source_title"] not in citations:
                citations.append(chunk["source_title"])

        summary_points = [chunk["claim_summary"] for chunk in chunks[:3]]
        follow_ups = [
            "When was your last period or bleeding episode?",
            "Is pregnancy possible from recent sex?",
            "Are you postpartum or breastfeeding?",
            "How heavy is the bleeding and do you have dizziness, fainting, fever, or severe pain?",
        ]

        ollama_model = os.environ.get("WOMENS_AI_OLLAMA_MODEL")
        if ollama_model:
            generated = self._generate_with_ollama(
                user_text=user_text,
                risk=risk,
                chunks=chunks,
                model=ollama_model,
                extracted_features=extracted_features,
                follow_ups=follow_ups,
            )
        else:
            generated = self._fallback_answer(
                risk=risk,
                summary_points=summary_points,
                extracted_features=extracted_features,
                follow_ups=follow_ups,
            )

        return {
            "answer": generated,
            "citations": citations,
            "risk_level": risk["risk_level"],
            "care_recommendation": self._care_recommendation(risk, extracted_features),
            "follow_up_questions": follow_ups if risk["risk_level"] != "normal_variation" else follow_ups[:2],
            "abstain_reason": None,
            "risk_findings": risk["findings"],
            "extracted_features": extracted_features,
        }

    def _fallback_answer(self, risk, summary_points, extracted_features, follow_ups):
        prefix = {
            "emergency_care": "This pattern needs emergency evaluation.",
            "urgent_care": "This pattern needs urgent medical evaluation.",
            "prompt_medical_review": "This pattern should be medically reviewed.",
            "routine_review": "This is not necessarily dangerous, but it should not be ignored.",
            "normal_variation": "This may fit normal variation, depending on life stage and severity.",
        }[risk["risk_level"]]
        evidence = " ".join(summary_points[:2])
        age_context = (
            f" Reported age: {extracted_features.get('age_years')}." if extracted_features.get("age_years") else ""
        )
        extra = ""
        if (
            "pregnancy possibility after sex" in risk["findings"]
            or extracted_features.get("unprotected_sex_recent")
        ):
            extra = (
                " Because pregnancy is a safety concern, a pregnancy test is reasonable if your period is delayed."
            )
        follow_up_block = " ".join(f"{q}" if q.endswith("?") else f"{q}?" for q in follow_ups)
        return (
            f"{prefix} Based on the current knowledge base: {evidence}.{age_context}{extra} "
            f" This is educational information, not a diagnosis. Follow-up questions: {follow_up_block}"
        )

    def _care_recommendation(self, risk, features):
        risk_level = risk["risk_level"]
        risk_findings = [item.lower() for item in risk.get("findings", [])]
        if risk_level == "emergency_care":
            return "Seek emergency care now."
        if risk_level == "urgent_care":
            return "Seek urgent medical evaluation today."
        if risk_level == "prompt_medical_review":
            if "bleeding after sex" in risk_findings:
                return "Arrange clinician review soon, including gynecologic evaluation."
            if features.get("trying_to_conceive") or features.get("infertility_history_flag"):
                return "Arrange clinician review soon for fertility and gynecologic assessment."
            return "Arrange clinician review soon."
        if risk_level == "routine_review":
            if features.get("unprotected_sex_recent") and (
                features.get("last_menstrual_period_days_ago") is not None
                or features.get("missed_periods_count") is not None
            ):
                return "Consider a pregnancy test and review symptoms if delay continues."
            return "Monitor and seek review if symptoms persist or worsen."
        return "Monitor for change and seek review if red flags appear."

    def _generate_with_ollama(self, user_text, risk, chunks, model, extracted_features, follow_ups=None):
        system_prompt = (self.root / "prompts" / "ollama_system_prompt.txt").read_text().strip()
        follow_ups = follow_ups or []
        follow_up_prompt = ""
        if follow_ups:
            follow_up_prompt = "\nFollow-up prompts:\n" + "\n".join(f"- {item}" for item in follow_ups)
        prompt = {
            "model": model,
            "stream": False,
            "prompt": (
                f"{system_prompt}\n\n"
                f"User question:\n{user_text}\n\n"
                f"Risk level already computed: {risk['risk_level']}\n"
                f"Risk findings: {', '.join(risk['findings']) or 'none'}\n"
                f"Extracted_features:\n{json.dumps(extracted_features, sort_keys=True)}\n\n"
                "Evidence:\n"
                + "\n\n".join(
                    f"- {chunk['claim_summary']} ({chunk['source_title']}): {chunk['text']}"
                    for chunk in chunks
                )
                + follow_up_prompt
                + "\n\nReturn a concise answer for the user."
            ),
        }
        req = request.Request(
            os.environ.get("WOMENS_AI_OLLAMA_URL", "http://127.0.0.1:11434/api/generate"),
            data=json.dumps(prompt).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        response = payload.get("response", "").strip()
        if response:
            return response
        return self._fallback_answer(
            risk=risk,
            summary_points=[],
            extracted_features=extracted_features,
            follow_ups=follow_ups,
        )
