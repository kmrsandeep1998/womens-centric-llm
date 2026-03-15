# Review Workflow and Escalation Routing

## Goal

Make every new case enter a controlled path before being used for model training or benchmark expansion.

## Workflow Inputs

- Raw candidates from:
  - conversations or telemetry (`review_queue.jsonl`)
  - new `interaction_examples.jsonl` additions
  - structured case exports

## Routing States

- `open`
  - New case needs triage.
  - Allowed to run in benchmark only after triage.
- `in_review`
  - Assigned to a reviewer for risk and label checks.
- `human_reviewed`
  - Reviewed by non-clinician reviewer. Can be used for draft training material.
- `clinician_reviewed`
  - Cleared by a qualified clinician. Preferred for red-flag datasets.
- `rejected`
  - Not safe or too noisy for model-facing use.

## Routing Rules

- Any candidate mentioning:
  - late period + sex
  - bleeding after sex
  - postmenopausal bleeding
  - heavy bleeding + dizziness/fainting/chest symptoms
  - postpartum bleeding with systemic symptoms
  must be marked `high` severity and routed to review first.
- Cases with missing pregnancy context after mention of sex are routed to review even if risk text is mild.
- Cases without source trace or with fabricated claims are rejected unless confirmed.

## Output Destinations

- `data/review_queue.jsonl`:
  - holds all unreviewed or blocked items
- `data/safety_train.jsonl`:
  - reviewed red-flag cases for escalation behavior
- `data/validation_interactions.jsonl`:
  - reviewed neutral and mixed-edge cases for holdout validation
- `data/train_interactions.jsonl`:
  - reviewed standard instructional cases

## Reviewer Checklist

1. Confirm the case text is mapped to the right scenario label(s).
2. Verify citations map to valid source IDs.
3. Ensure red-flag escalation is explicit when required.
4. Set `human_reviewed`/`clinician_reviewed` before training inclusion.
5. Reject if severe safety risk is missed or if claims are non-grounded.

## Escalation

- Any disagreement about whether a case is `urgent_care` vs `prompt_medical_review` must defer to clinician review before dataset inclusion.
