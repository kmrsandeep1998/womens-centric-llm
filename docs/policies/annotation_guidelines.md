# Annotation Guidelines for Women-Centric Menstrual Health v1

## Goal

Create consistent labels for menstrual and reproductive health cases for:

- structured case classification
- safe assistant responses
- benchmark evaluation

These guidelines are for annotation and QA. They do not replace clinical review.

## Annotation Unit

Each annotation record should contain:

- `raw_input_text`
- `normalized_case_summary`
- `extracted_features`
- `output_labels`
- `risk_level`
- `care_recommendation`
- `evidence_source_ids`
- `annotator_notes`
- `review_status`

## Required Annotation Workflow

1. Read the full input carefully.
2. Extract explicit facts only.
3. Mark missing facts as `unknown`, not assumed.
4. Identify red flags first.
5. Determine whether pregnancy possibility is relevant.
6. Add one or more cause-category labels if supported.
7. Assign the highest applicable risk level.
8. Decide whether the correct assistant behavior is answer, follow-up, or abstain.
9. Add source IDs that support the reasoning.
10. Flag high-risk records for clinician review.

## Core Feature Extraction Rules

### Life stage

Annotate if any of the following is explicit:

- adolescent
- reproductive age
- pregnant
- postpartum
- breastfeeding
- perimenopause
- postmenopause

If unclear, use `unknown`.

### Menstrual timing

Extract:

- last menstrual period if provided
- cycle length if provided
- duration of bleeding
- missed periods count
- whether current bleeding is between periods
- whether bleeding happened after sex

Do not infer cycle length from vague language.

### Severity

Extract explicit severity signals such as:

- soaking products hourly
- needing multiple products
- waking to change products
- large clots
- dizziness
- fainting
- chest pain
- shortness of breath

These should strongly influence risk labeling.

### Pregnancy context

Extract:

- recent sex
- unprotected sex
- contraception status
- emergency contraception use
- pregnancy test result

If there was recent sex and a late or missed period, annotate pregnancy possibility even if the user asks about stress or diet.

### Postpartum and breastfeeding

Extract:

- weeks since birth
- breastfeeding status
- exclusive or partial breastfeeding if known

Ovulation can return before the first postpartum period. Do not mark a postpartum user as low pregnancy risk only because periods have not returned.

### Health and history

Extract any mention of:

- PCOS
- thyroid disease
- fibroids
- endometriosis
- adenomyosis
- anemia
- bleeding disorder
- STI or PID history
- eating disorder history
- rapid weight change
- intense exercise
- severe stress

## Risk Level Definitions

### `normal_variation`

No red flags. Pattern fits normal life-stage variability.

### `routine_review`

Needs non-urgent follow-up or monitoring. Symptoms are not clearly dangerous, but the pattern is not fully reassuring.

### `prompt_medical_review`

Requires clinician review soon, but no clear emergency sign is present.

Examples:

- bleeding after sex
- bleeding between periods
- no period for 3 months when not pregnant or breastfeeding
- new irregularity after previously regular cycles

### `urgent_care`

Requires same-day or urgent evaluation.

Examples:

- very heavy bleeding with dizziness
- pregnancy with concerning bleeding and pain
- severe pelvic pain with fever

### `emergency_care`

Requires emergency care recommendation.

Examples:

- heavy bleeding with fainting
- pregnancy with severe pain and heavy bleeding
- severe postpartum hemorrhage pattern

## Cause Label Rules

### When to assign `possible_pregnancy_related_change`

Assign if:

- recent sex occurred and
- there is a missed/late/changed period or bleeding pattern that could fit pregnancy

Do not require a positive test.

### When to assign `possible_contraception_effect`

Assign if:

- the case describes recent start, stop, missed doses, change, or known use of a hormonal method or copper IUD and
- the bleeding pattern plausibly matches the method

### When to assign `possible_stress_weight_exercise_effect`

Assign if:

- high stress, under-eating, rapid weight change, or intense exercise is clearly present and
- missed or irregular periods are plausible

Do not let this label suppress pregnancy evaluation if sex occurred.

### When to assign `possible_endocrine_disorder`

Assign if:

- known endocrine disease exists, or
- the symptom pattern strongly suggests PCOS or other endocrine dysregulation

### When to assign `possible_structural_gynecologic_cause`

Assign if:

- there is known fibroid/polyp/adenomyosis/endometriosis history, or
- bleeding/pain pattern strongly suggests structural disease

### When to assign `possible_infection_or_sti_related_bleeding`

Assign if:

- there is bleeding after sex, abnormal discharge, fever, pelvic pain with STI risk, or known infection history

## Behavioral Annotation Rules

Use `ask_follow_up_questions` when the answer depends on missing high-impact facts such as:

- age
- pregnancy possibility
- postpartum status
- breastfeeding status
- bleeding severity
- red-flag symptoms

Use `abstain_due_to_uncertainty` when:

- the case is too incomplete to answer safely
- the request asks for diagnosis certainty not supported by data
- the topic is outside v1 scope

## Clinician Review Triggers

Mandatory clinician review for records involving:

- pregnancy with bleeding
- postmenopausal bleeding
- severe heavy bleeding
- postpartum bleeding concerns
- suspected ectopic presentation
- self-harm, abuse, or assault if those records are ever included

## Synthetic Data Rule

Synthetic examples may be used only for bootstrapping schema and behavior tests.

Do not treat synthetic records as primary medical truth.
Do not rely on synthetic-only datasets for model validation.
