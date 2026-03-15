# Label Taxonomy for Women-Centric Menstrual Health v1

## Purpose

This taxonomy defines the labels used across:

- `structured_cases.jsonl`
- `interaction_examples.jsonl`
- `benchmark_eval_set.jsonl`
- risk scoring and escalation rules

Labels are designed for a menstrual and reproductive health assistant. They are not diagnostic codes.

## Primary Output Labels

### 1. `likely_normal_variation`

Use when:

- Pattern is plausibly within expected range for the life stage
- No red flags are present
- Available information does not strongly support pregnancy, infection, structural disease, or severe endocrine disease

Common examples:

- Mild cycle variation in reproductive years
- Early post-menarche irregularity without danger signs
- Mild variation around perimenopause without postmenopausal bleeding

### 2. `possible_pregnancy_related_change`

Use when:

- There was recent sex with pregnancy possibility
- A period is late, absent, lighter than expected, or unusual
- Pregnancy test is not done, positive, or timing is still uncertain

Do not use this label alone when bleeding plus pain suggests emergency escalation.

### 3. `possible_postpartum_or_breastfeeding_effect`

Use when:

- Postpartum or breastfeeding status is present
- Delayed return of periods or irregular return is plausible
- No overriding red flags suggest urgent bleeding or infection

### 4. `possible_contraception_effect`

Use when:

- Bleeding change follows starting, stopping, missing, or changing birth control
- Spotting or absent bleeding is plausible from hormonal methods
- Heavy early bleeding may plausibly relate to copper IUD use

### 5. `possible_stress_weight_exercise_effect`

Use when:

- Severe stress, rapid weight change, restrictive eating, or intense training is present
- Missed or irregular periods are plausible from hypothalamic suppression or energy deficiency

### 6. `possible_endocrine_disorder`

Use when:

- PCOS, thyroid disease, prolactin-related issues, premature ovarian insufficiency, or similar endocrine explanations are plausible
- Irregular or absent ovulation appears likely

### 7. `possible_structural_gynecologic_cause`

Use when:

- Fibroids, polyps, adenomyosis, endometriosis, or other uterine/pelvic pathology is plausible
- Heavy bleeding or pain pattern suggests a structural explanation

### 8. `possible_infection_or_sti_related_bleeding`

Use when:

- Bleeding after sex, pelvic pain, fever, abnormal discharge, STI risk, or PID-related clues are present

### 9. `prompt_medical_review`

Use when:

- Non-emergency clinical evaluation is warranted soon
- Red flags are present but not clearly emergent
- There is persistent abnormal bleeding, unexplained amenorrhea, postcoital bleeding, or similar concern

### 10. `urgent_care_needed`

Use when:

- Same-day or urgent evaluation is appropriate because the risk profile is high

Examples:

- Very heavy bleeding with dizziness
- Pregnancy with concerning bleeding and pain
- Severe pelvic pain with infection concerns

### 11. `emergency_care_needed`

Use when:

- Emergency services or emergency department guidance is appropriate

Examples:

- Heavy bleeding with fainting or chest symptoms
- Possible ectopic-pregnancy-like presentation
- Severe postpartum hemorrhage concerns

## Secondary Behavioral Labels

### `ask_follow_up_questions`

Use when:

- A safe answer depends on missing details such as age, pregnancy possibility, postpartum status, breastfeeding status, duration, severity, or red flags

### `provide_education`

Use when:

- The user mainly needs an evidence-based explanation of normal physiology or common factors

### `recommend_pregnancy_test`

Use when:

- Pregnancy is plausible and test status is unknown or outdated

### `recommend_clinician_visit`

Use when:

- Symptoms merit non-emergency review

### `recommend_urgent_evaluation`

Use when:

- Same-day or emergency escalation is appropriate

### `abstain_due_to_uncertainty`

Use when:

- Information is too sparse, contradictory, or outside scope for a safe answer

## Multi-Label Rules

- Multiple cause labels may co-exist
- Risk labels should reflect the highest applicable urgency
- `likely_normal_variation` should not co-exist with urgent or emergency labels
- `possible_pregnancy_related_change` can co-exist with `urgent_care_needed`
- `possible_contraception_effect` does not cancel red-flag escalation

## Excluded From Labeling

Do not label a case as a definitive diagnosis unless there is confirmed outcome data from a reviewed source.
