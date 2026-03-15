# Women-Centric AI Dataset Design

## Objective

Create a dataset that supports a women-centric AI system across menstrual and related reproductive-health use cases, with space to expand into broader women's health domains.

This document is about dataset design, not model architecture alone.

## 1. Recommended Initial Scope

Start with these high-value domains:

- Menstrual cycle and period irregularities
- Heavy menstrual bleeding
- Dysmenorrhea / pelvic pain
- Pregnancy possibility and missed periods
- Postpartum and breastfeeding cycle changes
- Contraception-related bleeding changes
- PCOS / endocrine contributors
- Perimenopause / menopause bleeding changes
- Infection/STI-related bleeding warnings

Do not start with all of women's health at once. Start with one coherent cluster and expand.

## 2. Data Layers

You need multiple data layers, not one monolithic corpus.

### Layer A: Reference knowledge

Purpose:

- Provide grounded medical facts
- Support retrieval and citations

Examples:

- Guidelines
- Government health pages
- Professional society FAQs
- Peer-reviewed review articles

### Layer B: Structured case data

Purpose:

- Train classifiers and triage logic
- Train structured reasoning over patient features

Examples:

- Age
- Cycle length
- Bleeding duration
- Pain severity
- Pregnancy possibility
- Breastfeeding status
- Contraception
- Known conditions

### Layer C: Labeled text interactions

Purpose:

- Train an assistant to answer questions, summarize cases, and ask follow-up questions

Examples:

- User question -> safe answer
- Symptom description -> structured extraction
- Case summary -> risk label

### Layer D: Outcomes

Purpose:

- Evaluate whether predictions align with later clinical findings

Examples:

- Pregnancy confirmed
- PCOS diagnosed
- Fibroid on ultrasound
- No urgent pathology
- STI confirmed

## 3. Dataset Entities

### Person-level entity

Slow-changing information:

- Age range
- Menarche age
- Parity
- Chronic conditions
- Baseline weight range
- Family history
- Typical cycle pattern

### Episode-level entity

One menstrual event or one care episode:

- LMP date
- Current symptoms
- Bleeding pattern
- Pain level
- Recent sex
- Pregnancy risk
- Medications
- Contraception
- Stress/weight change

### Interaction-level entity

A single conversation or question:

- Raw question
- Cleaned question
- Structured extraction
- Answer
- Citations
- Risk level
- Human review status

## 4. Core Feature Groups

### Demographics and life stage

- age_years
- adolescent_flag
- reproductive_age_flag
- postpartum_flag
- breastfeeding_flag
- perimenopause_flag
- postmenopause_flag
- age_at_menarche_years

### Menstrual history

- last_menstrual_period_date
- average_cycle_length_days
- cycle_min_days
- cycle_max_days
- cycle_variability_days
- bleeding_duration_days
- intermenstrual_bleeding_flag
- postcoital_bleeding_flag
- clotting_flag
- flow_intensity
- skipped_cycles_count

### Symptoms

- pelvic_pain_score
- low_back_pain_flag
- headache_flag
- migraine_flag
- breast_tenderness_flag
- bloating_flag
- fatigue_flag
- nausea_flag
- vomiting_flag
- dizziness_flag
- syncope_flag
- fever_flag
- abnormal_discharge_flag
- dyspareunia_flag
- bowel_symptoms_flag
- urinary_symptoms_flag
- mood_symptoms
- sleep_disruption_flag

### Sexual and reproductive context

- sexually_active_flag
- unprotected_sex_recent_flag
- last_sex_date
- pregnancy_test_result
- pregnancy_known_flag
- emergency_contraception_recent_flag
- trying_to_conceive_flag
- infertility_history_flag
- miscarriage_history_flag
- abortion_history_flag
- live_birth_count
- cesarean_history_flag

### Postpartum and lactation

- postpartum_weeks
- exclusive_breastfeeding_flag
- partial_breastfeeding_flag
- return_of_menses_postpartum_flag

### Contraception

- contraception_method_current
- contraception_method_recent_change_flag
- hormonal_method_flag
- copper_iud_flag
- adherence_issue_flag

### Body composition and behavior

- height_cm
- weight_kg
- bmi
- recent_weight_change_kg
- restrictive_eating_flag
- eating_disorder_history_flag
- exercise_level
- high_training_load_flag
- sleep_hours
- shift_work_flag

### Medical history

- pcos_flag
- thyroid_disease_flag
- diabetes_flag
- anemia_flag
- bleeding_disorder_flag
- fibroid_flag
- polyp_flag
- adenomyosis_flag
- endometriosis_flag
- pid_history_flag
- sti_history_flag
- chronic_pain_flag
- depression_anxiety_flag

### Medication and treatment history

- hormonal_contraceptives
- anticoagulants_flag
- steroid_use_flag
- psychiatric_meds_flag
- fertility_medication_flag
- hormone_therapy_flag
- pain_medication_use

### Labs and clinical findings

- hemoglobin
- ferritin
- tsh
- prolactin
- lh
- fsh
- estradiol
- progesterone
- testosterone
- dheas
- hba1c
- pregnancy_hcg
- ultrasound_fibroid_flag
- ultrasound_cyst_flag
- endometrial_thickness_mm

### Social and environmental context

- marital_status
- relationship_status
- healthcare_access_difficulty_flag
- financial_barrier_flag
- tobacco_use_flag
- alcohol_use_flag
- substance_use_flag
- recent_travel_flag
- major_stress_event_flag

## 5. Target Outputs

### Structured prediction targets

- likely_normal_variation
- possible_pregnancy_related_change
- possible_postpartum_or_breastfeeding_effect
- possible_contraception_effect
- possible_stress_weight_exercise_effect
- possible_endocrine_disorder
- possible_structural_gynecologic_cause
- possible_infection_or_sti
- urgent_medical_review_needed
- emergency_care_needed

### Conversational targets

- ask_follow_up_question
- provide_education
- recommend_pregnancy_test
- recommend_clinician_visit
- recommend_urgent_evaluation
- provide_source_grounded_answer
- abstain_due_to_uncertainty

## 6. Annotation Units

Each record should support:

- raw_input_text
- normalized_case_summary
- extracted_features
- output_labels
- evidence_span_or_source
- annotator_id
- clinician_review_flag
- dataset_split
- version

## 7. High-Risk Cases to Over-Sample

- Pregnancy with bleeding and pain
- Heavy bleeding with dizziness/fainting
- Postmenopausal bleeding
- Bleeding after sex
- Suspected ectopic pregnancy signals
- Severe postpartum bleeding concerns
- Adolescent with very heavy prolonged bleeding
- Possible anemia from heavy periods

## 8. Cases to Include for Balance

- Normal cycle variation
- Mild PMS
- Contraception-related spotting
- Early post-menarche irregularity
- Perimenopausal irregularity without emergency signs
- Breastfeeding-related absent periods

## 9. Data Quality Requirements

- Clear missing-value policy
- Units normalized
- Dates normalized
- Source provenance attached
- Contradictions marked
- Outliers flagged
- Label definitions versioned

## 10. Recommended Splits

- Train
- Validation
- Test
- Safety benchmark
- Temporal holdout if source dates matter

Avoid leakage across the same person or near-duplicate cases.

## 11. Recommended Starting Numbers

These are pragmatic starting points, not strict requirements.

- 200 to 500 manually reviewed reference chunks for retrieval
- 1,000 to 3,000 structured cases for first classifiers
- 500 to 1,500 annotated interaction examples for assistant behavior
- 200+ high-risk benchmark cases

For strong fine-tuning quality, much larger reviewed datasets are usually needed.

## 12. What Not to Use Naively

- Random internet blogs
- Forums as medical truth
- Unlicensed web scraping for training
- Synthetic data as the primary source of medical truth
- Relationship status as a major biologic predictor
- Adult height as a core causal feature

## 13. Best Near-Term Build Strategy

Recommended stack:

1. Curated knowledge base
2. Structured feature extractor
3. Rule-based risk engine
4. Retrieval-augmented assistant
5. Optional fine-tuning once reviewed data volume is adequate
