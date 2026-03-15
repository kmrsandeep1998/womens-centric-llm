# Women-Centric Health Expansion Roadmap

## Purpose

This roadmap expands the project from menstrual-cycle coverage into the broader surrounding domains that materially affect women's symptoms, cycle patterns, fertility, sexual health, and care escalation.

It is designed as a step-by-step execution plan that can be followed iteratively.

## Expansion Principles

- Expand by medically connected domains, not by random topic accumulation
- Prefer official and guideline-backed sources first
- Separate retrieval material from trainable material
- Add new labels and schema fields only when they improve decision quality
- Expand evaluation alongside scope so safety does not regress

## Phase 1: Finish Menstrual-Core Depth

Goal:

- Close the remaining gaps inside the current menstrual domain

Tasks:

1. Expand source coverage for:
   - dysmenorrhea
   - PMS / PMDD
   - painful periods with associated symptoms
   - chronic pelvic pain
   - adolescent cycle development
2. Add features for:
   - nausea, vomiting, diarrhea
   - headache and migraine
   - sleep disruption
   - functional impairment at school/work
3. Add benchmark cases for:
   - severe period pain
   - PMS pattern versus depression/anxiety overlap
   - heavy bleeding with anemia symptoms

Deliverables:

- expanded `source_catalog.csv`
- expanded `reference_chunks.jsonl`
- more reviewed pain- and PMS-related cases

## Phase 2: Add Structural Gynecologic Conditions

Goal:

- Cover disorders that commonly drive pain, heavy bleeding, and fertility issues

Target topics:

- endometriosis
- adenomyosis
- fibroids
- polyps
- ovarian cysts

Tasks:

1. Expand source coverage for each condition
2. Add schema fields for:
   - dyspareunia
   - bowel pain during periods
   - bladder pain during periods
   - unilateral pain
   - known imaging findings
   - infertility history
   - family history where relevant
3. Add case templates and benchmarks for:
   - endometriosis-like pain
   - fibroid-related heavy bleeding
   - ovarian cyst rupture/torsion-style pain

Deliverables:

- structural-condition chunk set
- structural-condition benchmark cases
- updated label guidance for structural differentials

## Phase 3: Add Infection and STI-Related Reproductive Health

Goal:

- Capture infectious causes of pelvic pain, abnormal bleeding, and fertility complications

Target topics:

- PID
- STI-related abnormal bleeding
- bleeding after sex
- vaginal discharge/infection symptom clusters

Tasks:

1. Add sources from CDC, ACOG, Office on Women's Health, and NHS
2. Add features for:
   - abnormal discharge
   - odor
   - itching
   - pain with urination
   - fever
   - STI history
   - partner risk context
3. Add escalation rules for:
   - pelvic pain + fever
   - bleeding after sex
   - pregnancy possibility + infectious symptoms

Deliverables:

- infection-sensitive label set
- STI/PID benchmark coverage
- updated safety rules

## Phase 4: Add Endocrine and Metabolic Overlap

Goal:

- Cover non-gynecologic health conditions that strongly affect menstrual patterns

Target topics:

- PCOS
- thyroid disease
- hyperprolactinemia
- premature ovarian insufficiency
- diabetes/metabolic syndrome
- anemia / iron deficiency

Tasks:

1. Expand sources and schema for:
   - acne
   - hirsutism
   - hair loss
   - fatigue
   - weight change
   - glucose/metabolic markers
   - thyroid symptoms and history
2. Add labs and outcomes where possible:
   - TSH
   - prolactin
   - ferritin
   - hemoglobin
   - A1c
   - androgen markers
3. Add benchmarks for:
   - PCOS-like presentations
   - thyroid-related heavy or absent periods
   - anemia symptoms from bleeding

Deliverables:

- endocrine feature expansion
- endocrine benchmark pack
- updated follow-up question logic

## Phase 5: Add Sexual, Mental, and Quality-of-Life Context

Goal:

- Improve realism and safety by capturing nontrivial adjacent factors

Target topics:

- painful sex
- libido and arousal context
- sexual trauma-sensitive handling
- depression/anxiety overlap with PMS
- sleep disruption
- stress and fatigue
- quality-of-life impairment

Tasks:

1. Add non-diagnostic psychosocial fields
2. Add annotation rules for:
   - when mood symptoms appear cyclical versus persistent
   - when to ask follow-up instead of labeling
3. Add behavior tests for:
   - trauma-sensitive wording
   - uncertainty handling
   - out-of-scope mental health escalation

Deliverables:

- richer interaction examples
- improved abstain/follow-up logic
- bias and sensitivity review updates

## Phase 6: Add Fertility and Reproductive Intent Context

Goal:

- Make the model useful for women who are trying to conceive or worried about fertility impact

Target topics:

- infertility history
- ovulation uncertainty
- recurrent miscarriage context
- STI-related infertility risk
- endometriosis/fibroid fertility impact

Tasks:

1. Add schema fields for:
   - trying_to_conceive
   - infertility_duration
   - prior fertility evaluation
   - miscarriage history
2. Add retrieval chunks on fertility-related consequences
3. Add benchmarks that distinguish:
   - routine fertility concerns
   - urgent pregnancy-related complications

Deliverables:

- fertility-aware feature group
- fertility-related benchmark set

## Phase 7: Replace Bootstrapping Data With Reviewed Data

Goal:

- Move from synthetic seed records to useful training/evaluation assets

Tasks:

1. Create first-party data collection forms
2. Collect consented user questions and structured intake
3. Build annotation queues
4. Review high-risk examples manually
5. Keep synthetic data only for schema tests, not primary model truth

Deliverables:

- real annotation backlog
- clinician-reviewed subset
- revised benchmark set with reviewed labels

## Phase 8: Build the First Working System

Goal:

- Turn the datasets into a runnable prototype

Components:

1. Retrieval over `reference_chunks.jsonl`
2. Feature extraction from user input
3. Rule-based safety engine
4. Risk/category classifier
5. Response generator with citations

Acceptance conditions:

- red flags are escalated consistently
- pregnancy possibility is not missed in late-period cases
- bleeding after sex is not normalized
- postpartum and postmenopausal cases route correctly

## Immediate Next Steps

These are the next concrete actions from the current workspace state:

1. Expand the source ledger with structural, infectious, endocrine, and pain-related domains
2. Expand retrieval chunks for those domains
3. Add new feature groups to the schema docs
4. Add corresponding seed cases and benchmark cases
5. Build an ingestion script that validates JSONL/CSV consistency
6. Add bleeding-disorder, PMDD, POI, adenomyosis, and polyp coverage
7. Add Tier 2 fallback sources where Tier 1 patient guidance is thin
8. Add hyperprolactinemia, infertility workflow, and metabolic-PCOS overlap

## What Was Missing Before This Expansion

The earlier dataset under-covered:

- endometriosis
- fibroids
- painful sex
- chronic pelvic pain
- PID and STI-linked fertility risk
- thyroid-related cycle changes
- ovarian cysts
- PMS overlap with mood conditions
- PMDD severity and safety implications
- adenomyosis
- uterine polyps
- bleeding disorders as a cause of heavy periods
- POI in under-40 amenorrhea
- hyperprolactinemia in amenorrhea and infertility
- infertility workflow and fertility-intent context
- metabolic risk around PCOS and irregular periods
- bowel/bladder-linked menstrual pain
- quality-of-life and sleep disruption

This roadmap is the mechanism to close those gaps in a controlled way.
