from __future__ import annotations

from typing import Dict


def _has_any(text: str, phrases):
    lowered = text.lower()
    return any(phrase in lowered for phrase in phrases)


def assess_risk(user_text: str, extracted_features: Dict | None = None):
    text = user_text.lower()
    features = extracted_features or {}
    findings = []
    risk = "normal_variation"

    pregnant = _has_any(text, ["i'm pregnant", "i am pregnant", "pregnant"])
    sex_possible = (
        _has_any(
            text,
            [
                "had sex",
                "had sex last",
                "unprotected sex",
                "no protection",
                "without protection",
                "trying to get pregnant",
                "trying for a baby",
                "trying to conceive",
            ],
        )
        or bool(features.get("unprotected_sex_recent"))
        or bool(features.get("sexually_active"))
    )
    bleeding = _has_any(
        text,
        [
            "bleeding",
            "spotting",
            "heavy period",
            "heavy periods",
            "very heavy",
            "soaking",
            "soaked",
            "pads every hour",
            "bleed after sex",
            "heavier",
        ],
    )
    pain = _has_any(text, ["pain", "cramps", "one sided", "one-sided", "pelvic pain"])
    urgent_symptoms = _has_any(
        text, ["faint", "fainting", "dizziness", "dizzy", "short of breath", "chest pain", "weakness", "extremely weak"]
    )
    postpartum = _has_any(
        text,
        [
            "postpartum",
            "gave birth",
            "post partum",
            "weeks ago",
            "months after delivery",
            "weeks after delivery",
            "after giving birth",
        ],
    ) or bool(features.get("postpartum_weeks") is not None)
    breastfeeding = _has_any(text, ["breastfeeding", "nursing"]) or bool(features.get("breastfeeding"))
    postmenopause = _has_any(
        text,
        ["haven't had a period in 4 years", "after menopause", "postmenopause", "postmenopausal"],
    )
    after_sex = _has_any(text, ["after sex", "bleed after sex"])
    fever_or_discharge = _has_any(text, ["fever", "discharge", "bad-smelling discharge", "odor"])
    late_period = _has_any(
        text,
        [
            "late period",
            "late periods",
            "period is late",
            "periods are late",
            "periods keep coming late",
            "periods keep late",
            "missed period",
            "missed periods",
            "haven't had a period",
            "have not had a period",
            "period stopped",
            "period hasn't started",
            "still hasn't come",
            "no period",
            "not got my period",
        ],
    ) or bool(features.get("missed_periods_count"))
    amenorrhea_long = _has_any(
        text, ["3 months", "4 months", "period stopped for 3 months", "period stopped for 4 months", "months without period"]
    )
    heavy_or_prolonged = _has_any(
        text, ["heavy for 8 days", "heavy for 9 days", "longer and heavier", "very heavy", "heavy and long"]
    )
    perimenopause = _has_any(text, ["i'm 47", "i'm 48", "i'm 49", "perimenopause", "cycles are irregular now"])
    pcos_like = _has_any(
        text, ["acne", "facial hair", "dark skin folds", "gaining weight around my waist", "hirsutism"]
    )
    structural_like = _has_any(
        text,
        [
            "pain during sex",
            "sex hurts",
            "painful sex",
            "sex has become painful",
            "bowel pain",
            "pressure in my pelvis",
            "pee often",
            "fibroids",
            "endometriosis",
            "adenomyosis",
        ],
    )
    endocrine_like = _has_any(
        text,
        [
            "thyroid",
            "hot flashes",
            "vaginal dryness",
            "milky discharge",
            "milk from my breasts",
            "milky discharge from my breasts",
            "nipple discharge",
            "galactorrhea",
        ],
    )
    bleeding_disorder_like = _has_any(text, ["nosebleeds", "bruises", "easy bruising", "large bruises"])
    sudden_severe_pain = _has_any(text, ["sudden severe pain", "one side of my pelvis", "one-sided pelvic pain"])
    infertility_like = (
        _has_any(
            text,
            [
                "trying for a baby for a year",
                "trying for years",
                "trying to get pregnant for a year",
                "trying for pregnancy for a year",
                "trying to conceive for a year",
                "tried for a baby more than a year",
                "trying for a baby more than a year",
            ],
        )
        or bool(features.get("trying_to_conceive"))
        or bool(features.get("infertility_history_flag"))
    )
    pmdd_like = _has_any(
        text, ["week before my period", "before my period i become", "rage", "severely anxious", "can't sleep", "severe mood"]
    )

    if postpartum and bleeding and urgent_symptoms:
        findings.append("postpartum bleeding with systemic symptoms")
        risk = "emergency_care"
    elif postmenopause and bleeding:
        findings.append("postmenopausal bleeding")
        risk = "prompt_medical_review"
    elif pregnant and bleeding and pain:
        findings.append("pregnancy with bleeding and pain")
        risk = "urgent_care"
    if late_period and sex_possible:
        findings.append("pregnancy possibility after sex")
        risk = max_risk(risk, "routine_review")

    if after_sex:
        findings.append("bleeding after sex")
        risk = max_risk(risk, "prompt_medical_review")

    if bleeding and urgent_symptoms:
        findings.append("heavy bleeding with systemic symptoms")
        risk = max_risk(risk, "urgent_care")

    if fever_or_discharge and pain:
        findings.append("infection-sensitive pelvic pain pattern")
        risk = max_risk(risk, "urgent_care")

    if breastfeeding and late_period and sex_possible:
        findings.append("breastfeeding delays periods but pregnancy remains possible")
        risk = max_risk(risk, "routine_review")
    elif breastfeeding and postpartum and late_period and not sex_possible:
        findings.append("breastfeeding-related delayed return of periods")
        risk = max_risk(risk, "normal_variation")

    if amenorrhea_long and not (breastfeeding and postpartum and not sex_possible):
        findings.append("prolonged absent periods")
        risk = max_risk(risk, "prompt_medical_review")

    if perimenopause and heavy_or_prolonged:
        findings.append("perimenopausal heavy or prolonged bleeding")
        risk = max_risk(risk, "prompt_medical_review")

    if pcos_like:
        findings.append("possible endocrine or metabolic pattern")
        risk = max_risk(risk, "routine_review")

    if structural_like:
        findings.append("possible structural gynecologic pattern")
        risk = max_risk(risk, "prompt_medical_review")

    if endocrine_like:
        findings.append("possible endocrine contributor")
        risk = max_risk(risk, "prompt_medical_review" if amenorrhea_long or late_period else "routine_review")

    if bleeding_disorder_like and bleeding:
        findings.append("possible bleeding disorder pattern")
        risk = max_risk(risk, "prompt_medical_review")

    if sudden_severe_pain:
        findings.append("sudden severe unilateral pelvic pain")
        risk = max_risk(risk, "urgent_care")

    if infertility_like:
        findings.append("fertility concern with prolonged trying to conceive")
        risk = max_risk(risk, "prompt_medical_review")

    if pmdd_like:
        findings.append("severe cyclical mood symptoms")
        risk = max_risk(risk, "prompt_medical_review")

    # Keep pregnancy as high-priority consideration whenever sex + delayed menses is present
    if (sex_possible and late_period and not pregnant) and not _has_any(text, ["pregnancy test positive", "pregnancy confirmed"]):
        findings.append("pregnancy differential should be screened")
    return {"risk_level": risk, "findings": findings}


RISK_ORDER = {
    "normal_variation": 0,
    "routine_review": 1,
    "prompt_medical_review": 2,
    "urgent_care": 3,
    "emergency_care": 4,
}


def max_risk(a: str, b: str) -> str:
    return a if RISK_ORDER[a] >= RISK_ORDER[b] else b
