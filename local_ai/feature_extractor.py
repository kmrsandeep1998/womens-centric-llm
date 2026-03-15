from __future__ import annotations

import re
from typing import Dict


AGE_RE = re.compile(
    r"\b(?:i['’]?\s*am|i['’]?\s*m|my age|age)\s*(?:is)?\s*(\d{1,3})(?:\s*years?)?\b",
    re.IGNORECASE,
)
LAST_PERIOD_DAYS_RE = re.compile(
    r"\b(?:period|last period|bleeding|menses)\b.*?(?:was|is|been|came|came|come)?\s*(?:about|around)?\s*(?P<num>\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+(?P<unit>day|days|week|weeks|month|months)\s+ago",
    re.IGNORECASE,
)
POSTPARTUM_RE = re.compile(
    r"\b(\d+)\s*(?:weeks?|months?)\s+(?:ago|after delivery|postpartum|after birth|after giving birth)\b",
    re.IGNORECASE,
)
PAIN_SCORE_RE = re.compile(r"\b(\d)\s*/\s*10\b")
WORDS_TO_NUM = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}


def _lower(text: str) -> str:
    return text.lower()


def _contains(text: str, phrases) -> bool:
    return any(p in text for p in phrases)


class FeatureExtractor:
    def extract(self, user_text: str) -> Dict:
        text = _lower(user_text)
        features: Dict = {
            "age_years": _extract_age(text),
            "life_stage": _infer_life_stage(text),
            "last_menstrual_period_days_ago": _extract_lmp_days(text),
            "last_menstrual_period_date": None,
            "missed_periods_count": None,
            "bleeding_duration_days": _extract_bleeding_days(text),
            "flow_level": _extract_flow(text),
            "pain_score_0_10": _extract_pain_score(text),
            "red_flags": _extract_red_flags(text),
            "clots_present": _extract_bool(text, ["clot", "large clots", "lots of clots"]),
            "spotting_between_periods": _extract_bool(text, ["spotting", "between periods", "light bleed"]),
            "bleeding_after_sex": _extract_bool(text, ["bleed after sex", "after sex", "postcoital"]),
            "symptoms": _extract_symptom_list(text),
            "sexually_active": _extract_bool(text, ["sex", "sexual"]),
            "unprotected_sex_recent": _extract_bool(
                text,
                ["unprotected sex", "no protection", "without contraception", "raw", "unsafe sex"],
            ),
            "last_sex_date": None,
            "pregnancy_test_result": _extract_pregnancy_test(text),
            "pregnancy_known": _extract_bool(text, ["i'm pregnant", "i am pregnant", "pregnant"]),
            "emergency_contraception_used": _extract_bool(text, ["emergency contraception", "ec pill"]),
            "breastfeeding": _extract_bool(text, ["breastfeeding", "breast fed", "nursing"]),
            "exclusive_breastfeeding": _extract_bool(text, ["exclusive breastfeeding", "only breastfeeding"]),
            "partial_breastfeeding": _extract_bool(text, ["mixed feeding", "combining"]),
            "postpartum_weeks": _extract_postpartum_weeks(text),
            "contraception_method": _extract_contraception(text),
            "contraception_recent_change": _extract_bool(text, ["started", "change", "stopped", "switched"]),
            "stress_level": _extract_stress_level(text),
            "exercise_level": _extract_exercise(text),
            "sleep_hours": _extract_numeric_value(text, ["sleep", "hours"]),
            "shift_work_flag": _extract_bool(text, ["shift", "night shift", "rotating"]),
            "trying_to_conceive": _extract_bool(text, ["trying to get pregnant", "trying for a baby", "trying to conceive"]),
            "infertility_history_flag": _extract_bool(text, ["trying for a baby for a year", "trying for years", "infertility"]),
            "miscarriage_history_flag": False,
            "abortion_history_flag": _extract_bool(text, ["miscarriage", "abortion", "terminated"]),
            "live_birth_count": None,
            "medications": _extract_medications(text),
            "known_conditions": _extract_conditions(text),
            "weight_kg": None,
            "recent_weight_change_kg": _extract_weight_change(text),
        }
        features["extracted_summary"] = _build_summary(features, user_text)
        return features


def _extract_age(text: str):
    for match in AGE_RE.finditer(text):
        value = match.group(1)
        try:
            age = int(value)
        except ValueError:
            continue

        # avoid false matches like "2 days ago", "3 weeks postpartum"
        prefix = text[max(0, match.start() - 12):match.start()].strip()
        suffix_start = match.end()
        suffix = text[suffix_start:suffix_start + 10]
        if _contains(prefix, ["weeks", "week", "months", "month", "days", "day"]) or _contains(suffix, ["days", "day", "weeks", "week", "months", "month"]):
            continue
        if 8 <= age <= 90:
            return age
    return None


def _infer_life_stage(text: str):
    if _contains(text, ["postpartum", "post partum", "gave birth", "after delivery", "after birth", "post delivery"]):
        return "postpartum"
    if _contains(text, ["breastfeeding", "breast fed", "nursing"]):
        return "breastfeeding"
    if _contains(text, ["menopause", "postmenopause", "perimenopause", "after menopause"]):
        return "perimenopause"
    if _contains(text, ["first period", "got my first", "menarche", "started periods", "adolescent", "teen"]):
        return "adolescent"
    return "reproductive"


def _extract_lmp_days(text: str):
    match = LAST_PERIOD_DAYS_RE.search(text)
    if not match:
        return None
    number = match.group("num")
    if not number:
        return None
    if number.isdigit():
        value = int(number)
    else:
        value = WORDS_TO_NUM.get(number.lower())
    if value is None:
        return None
    if "week" in match.group("unit"):
        return value * 7
    if "month" in match.group("unit"):
        return value * 30
    return value


def _extract_bleeding_days(text: str):
    if "heavy" not in text and "soaked" not in text and "for" not in text:
        return None
    match = re.search(r"\b(?:for|lasting|since)\s*(\d{1,2})\s+days?\b", text)
    return int(match.group(1)) if match else None


def _extract_flow(text: str):
    if _contains(text, ["very heavy", "soaked", "pad every hour", "heavy bleeding", "heavy"]):
        return "very_heavy"
    if _contains(text, ["spotting", "light bleed", "light bleeding", "light"]):
        return "light"
    if _contains(text, ["moderate"]) :
        return "moderate"
    return "unknown"


def _extract_pain_score(text: str):
    match = PAIN_SCORE_RE.search(text)
    if match:
        score = int(match.group(1))
        return max(0, min(10, score))
    return None


def _extract_red_flags(text: str):
    red_flags = []
    if _contains(text, ["dizzy", "faint", "fainting", "chest pain", "shortness of breath", "severe bleeding", "very heavy"]):
        red_flags.append("possible_hemodynamic_symptoms")
    if _contains(text, ["postmenopause", "after menopause", "menopause bleeding"]):
        red_flags.append("postmenopausal_bleeding")
    if _contains(text, ["bleed after sex", "postcoital", "after sex"]):
        red_flags.append("postcoital_bleeding")
    if _contains(text, ["one-sided", "one sided", "sudden severe"]):
        red_flags.append("severe_pelvic_pain_pattern")
    if _contains(text, ["can't get pregnant", "trying for a year", "trying to conceive"]):
        red_flags.append("infertility_concern")
    return red_flags


def _extract_symptom_list(text: str):
    symptoms = []
    mapping = {
        "nausea": ["nausea", "nauseous"],
        "cramps": ["cramps", "cramping", "pelvic cramps"],
        "headache": ["headache", "head ache", "migraine"],
        "fatigue": ["tired", "fatigue", "exhausted"],
        "dizziness": ["dizzy", "dizziness", "lightheaded"],
        "fever": ["fever", "feeling hot", "temperature"],
        "discharge": ["discharge", "smelly discharge", "odor", "odour"],
        "rash_itching": ["itch", "itching", "itchy", "rash"],
        "spotting": ["spotting", "light spotting", "postcoital"],
        "breast_tender": ["breast pain", "breast tenderness"],
    }
    for canonical, patterns in mapping.items():
        if _contains(text, patterns):
            symptoms.append(canonical)
    return symptoms


def _extract_bool(text: str, phrases) -> bool:
    return any(phrase in text for phrase in phrases)


def _extract_pregnancy_test(text: str):
    if _contains(text, ["pregnancy test is positive", "test is positive", "pregnancy is positive", "got positive"]):
        return "positive"
    if _contains(text, ["pregnancy test is negative", "test is negative", "pregnancy is negative", "got negative"]):
        return "negative"
    if _contains(text, ["pregnancy test", "not done", "haven't taken", "not taken"]):
        return "not_done"
    return "unknown"


def _extract_postpartum_weeks(text: str):
    match = POSTPARTUM_RE.search(text)
    if not match:
        return None
    amount = int(match.group(1))
    if "month" in match.group(0):
        return amount * 4
    return amount


def _extract_contraception(text: str):
    mapping = {
        "IUD": ["iud", "copper iud", "hormonal iud", "spiral"],
        "pill": ["pill", "birth control pill", "oral contraceptive"],
        "implant": ["implant", "rod"],
        "injection": ["injection", "shot", "depo"],
        "patch": ["patch"],
        "ring": ["ring"],
        "condom": ["condom", "condoms"],
        "none": ["none", "not using", "without protection"],
    }
    for key, values in mapping.items():
        if _contains(text, values):
            return key.lower() if key != "none" else "none"
    return "unknown"


def _extract_stress_level(text: str):
    if _contains(text, ["very stressed", "very stressful", "high stress", "stressed out", "extremely stressed"]):
        return "high"
    if _contains(text, ["a lot of stress", "moderate stress", "stressed"]):
        return "moderate"
    if _contains(text, ["low stress", "little stress"]):
        return "low"
    return "unknown"


def _extract_exercise(text: str):
    if _contains(text, ["intense training", "very high", "marathon", "very active", "daily run"]):
        return "very_high"
    if _contains(text, ["high intensity", "gym", "training hard"]):
        return "high"
    if _contains(text, ["few workouts", "low activity", "sedentary", "not active"]):
        return "low"
    if _contains(text, ["moderate", "regular exercise", "walk daily", "exercise"]):
        return "moderate"
    return "unknown"


def _extract_numeric_value(text: str, tokens):
    for t in tokens:
        m = re.search(rf"{t}\\b.*?(\\d+(?:\\.\\d+)?)", text)
        if m:
            try:
                return float(m.group(1))
            except ValueError:
                return None
    return None


def _extract_weight_change(text: str):
    if _contains(text, ["lost", "lost weight", "weight down", "down by"]):
        return _extract_negative_change(text)
    if _contains(text, ["gained", "gained weight", "weight up", "up by"]):
        return _extract_positive_change(text)
    return None


def _extract_negative_change(text: str):
    m = re.search(r"(?:lost|down|drop)\s*(\d+(?:\.\d+)?)\s*(?:kg|kgs|kilos|pounds|lbs|lb)", text)
    if not m:
        return None
    value = float(m.group(1))
    return -value


def _extract_positive_change(text: str):
    m = re.search(r"(?:gained|up|gain)\s*(\d+(?:\.\d+)?)\s*(?:kg|kgs|kilos|pounds|lbs|lb)", text)
    if not m:
        return None
    return float(m.group(1))


def _extract_medications(text: str):
    meds = []
    for item in [
        "metformin",
        "thyroxine",
        "levothyroxine",
        "ibuprofen",
        "naproxen",
        "aspirin",
        "warfarin",
        "valproate",
    ]:
        if _contains(text, [item]):
            meds.append(item)
    return meds


def _extract_conditions(text: str):
    conditions = []
    for item in [
        "pcos",
        "fibroids",
        "thyroid",
        "endometriosis",
        "adenomyosis",
        "hyperprolactinemia",
        "poi",
    ]:
        if _contains(text, [item]):
            conditions.append(item)
    return conditions


def _build_summary(features, raw_text):
    flags = []
    if features["life_stage"]:
        flags.append(f"life_stage={features['life_stage']}")
    if features["last_menstrual_period_days_ago"] is not None:
        flags.append(f"lmp_days_ago={features['last_menstrual_period_days_ago']}")
    if features["bleeding_after_sex"]:
        flags.append("postcoital_bleeding=true")
    if features["unprotected_sex_recent"]:
        flags.append("recent_unprotected_sex=true")
    if not flags:
        return _summarize_by_keywords(raw_text)
    return "; ".join(flags)


def _summarize_by_keywords(raw_text):
    if not raw_text.strip():
        return "No structured context parsed."
    tokens = _lower(raw_text)[:180].replace("\n", " ")
    return f"Parsed from keywords: {tokens}"
