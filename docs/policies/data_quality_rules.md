# Data Quality Rules for Women-Centric AI Assets

## Dataset Quality Priorities

1. Safety labels are higher priority than coverage.
2. Every training example should carry citations for factual claims.
3. Every reviewable clinical case should have explicit follow-up logic.
4. Synthetic data is useful only when marked and eventually replaced.

## Minimum Field Requirements

### For split interaction files

- `interaction_id` unique
- `raw_input`
- `normalized_case_summary`
- `extracted_features` object (must include at least: `life_stage`, `pregnancy_test_result`, `sexually_active`, `risk_findings`, `symptoms`, `flow_level`)
- `assistant_output`
- `citations` array
- `risk_level`
- `care_recommendation`
- `abstained` boolean
- `human_reviewed` boolean
- `split` one of:
  - `train`
  - `validation`
  - `safety_train`

## Risk Label Integrity

- `risk_level` must be one of:
  - `normal_variation`
  - `routine_review`
  - `prompt_medical_review`
  - `urgent_care`
  - `emergency_care`
- `emergency_care` and `urgent_care` labels must include escalation follow-up and at least one red-flag keyword.
- `prompt_medical_review` + bleeding-after-sex cases must include source-backed explanation and non-normalization language.

## Source Traceability

- Citations should resolve to valid source IDs in `data/source_catalog.csv`.
- Evidence-backed responses should avoid unsupported medical causality claims.

## Coverage Targets

- Reviewed interactions:
  - `train`: progressive target `500` minimum
  - `validation`: `150` minimum
  - `safety_train`: `250` minimum
- Review queue should trend down over each milestone.

## Blocking Conditions

- Duplicate IDs
- Missing required keys
- Empty `assistant_output`
- Unclear risk with red flags
- `breastfeeding` + recent sex + amenorrhea without pregnancy guidance
- Any case without follow-up path when required context is missing

## Dataset Rotation Rule

- Once a case is moved to train/validation/safety, it must stay versioned.
- If corrected, create a new entry with updated version instead of overwriting.
