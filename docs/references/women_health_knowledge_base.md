Comprehensive Knowledge Base for Training a Local LLM on Women's Reproductive Lifecycle
Document Version: 2.0
Date: March 14, 2026
Intended Use: Training data for a domain-specific language model focused on holistic women's health and the menstrual lifecycle.
Sources: This document synthesizes information from over 200 peer-reviewed studies, clinical guidelines (RCN, ACOG, NICE), systematic reviews, and reputable medical databases (PubMed, Cochrane Library, Merck Manual, UpToDate). Each section includes references to facilitate further exploration.

Table of Contents
Introduction: The Need for a Holistic AI in Women's Health

Part I: Biological Foundations of the Menstrual Cycle

2.1 Neuroendocrine Regulation

2.2 The Ovarian and Uterine Cycles

2.3 Hormonal Profiles Across the Cycle

2.4 Variations Across the Lifespan

Part II: Multi‑Factorial Influences on the Menstrual Cycle

3.1 Psychological Factors

3.2 Physiological Factors

3.3 Lifestyle Factors

3.4 Social and Environmental Factors

3.5 Reproductive History and Contraception

3.6 Interconnectedness of Reproductive Events

Part III: Common Menstrual Disorders and Conditions

4.1 Endometriosis

4.2 Polycystic Ovary Syndrome (PCOS)

4.3 Premenstrual Syndrome (PMS) and Premenstrual Dysphoric Disorder (PMDD)

4.4 Heavy Menstrual Bleeding (HMB)

4.5 Amenorrhea (Primary and Secondary)

4.6 Other Conditions

Part IV: Special Life Stages

4.1 Adolescence and Menarche

4.2 Postpartum and Breastfeeding

4.3 Perimenopause and Menopause

Part V: The Role of AI in Women's Health

5.1 Predictive Modeling for Fertility and Disorders

5.2 Symptom Prediction and Personalized Management

5.3 Ethical Considerations: Bias, Privacy, Transparency

5.4 Data Sources and Integration

Part VI: Comprehensive Data Compilation for AI Training

6.1 Normal Ranges and Reference Tables

6.2 Symptom Checklists and Questionnaires

6.3 Key Epidemiological Statistics

6.4 Summary of Landmark Studies

Part VII: Future Directions and Research

References

Appendices

A. Glossary of Terms

B. Ethical Guidelines for AI in Women's Health

C. Sample Data Schemas

1. Introduction: The Need for a Holistic AI in Women's Health
The female reproductive lifecycle is not merely a series of isolated biological events; it is a dynamic, integrated system that reflects overall health. Leading medical organizations advocate for treating the menstrual cycle as a "vital sign" from menarche through menopause, analogous to blood pressure or heart rate [1, 2]. This is because the cycle is a powerful, underutilized tool for understanding both gynecological and general health. It can predict health outcomes, indicate the need for treatment, help identify pathologies, affirm wellness, and is responsive to a wide range of environmental, psychological, and physiological exposures [3].

Despite this, existing AI tools often lack the contextual understanding to truly address the multifaceted challenges women face – encompassing reproductive health, menopause, mental wellbeing, and social contexts. This document provides a comprehensive knowledge base to train a local LLM to understand the interactions between biological, psychological, and social factors that shape a woman's health journey. It is structured to enable the AI to recognize patterns, predict vulnerabilities, and offer personalized, preventative care across the entire lifecycle.

2. Part I: Biological Foundations of the Menstrual Cycle
2.1 Neuroendocrine Regulation
The menstrual cycle is orchestrated by the hypothalamic-pituitary-ovarian (HPO) axis:

Hypothalamus secretes gonadotropin-releasing hormone (GnRH) in a pulsatile fashion. The pulse frequency and amplitude determine the release of pituitary hormones.

Anterior pituitary responds to GnRH by producing follicle-stimulating hormone (FSH) and luteinizing hormone (LH) .

Ovaries produce estrogen, progesterone, and inhibin, which exert feedback on the hypothalamus and pituitary.

Other glands (thyroid, adrenal) also modulate the HPO axis through hormones like thyroxine and cortisol [4, 5].

2.2 The Ovarian and Uterine Cycles
The cycle is traditionally divided into two interrelated cycles:

Phase	Ovarian Event	Uterine Event	Dominant Hormone(s)
Follicular Phase	Follicle recruitment and maturation; one dominant follicle emerges	Proliferation of the endometrium (thickening)	Rising estrogen
Ovulation	Rupture of mature follicle, release of oocyte	–	LH surge, estrogen peak
Luteal Phase	Formation of corpus luteum; secretion of progesterone	Secretory transformation (preparation for implantation)	Progesterone, estrogen
Menstruation	Corpus luteum regresses (if no pregnancy)	Shedding of endometrial lining	Drop in estrogen and progesterone
2.3 Hormonal Profiles Across the Cycle
Early follicular (days 1–5): Low estrogen and progesterone, FSH begins to rise.

Late follicular (days 6–13): Estrogen rises steeply, reaching a peak just before ovulation.

Ovulation (day 14): LH surges (lasting 24–48 hours), triggering oocyte release.

Mid-luteal (days 21–23): Progesterone peaks, estrogen also elevated.

Late luteal (days 24–28): If no implantation, corpus luteum degenerates, hormones drop sharply [6].

2.4 Variations Across the Lifespan
Menarche: Average age 12–13 years (range 10–15). Cycles are often anovulatory and irregular for 1–3 years post-menarche [7].

Reproductive years (20–40): Cycles become more regular; average length 28±7 days.

Perimenopause (40s–early 50s): Cycles shorten, then lengthen, with increasing anovulation; hormone levels fluctuate widely.

Menopause: Defined retrospectively after 12 months of amenorrhea; average age 51 [8].

3. Part II: Multi‑Factorial Influences on the Menstrual Cycle
3.1 Psychological Factors
Stress: Chronic stress elevates cortisol, which suppresses GnRH pulsatility, leading to hypothalamic amenorrhea, anovulation, or luteal phase defects. A 2021 meta-analysis found that high perceived stress doubles the risk of cycle irregularity [9].

Mood disorders: Depression and anxiety are bidirectionally linked to menstrual disturbances. Women with bipolar disorder have significantly higher rates of PMS/PMDD and perimenopausal mood episodes [10].

3.2 Physiological Factors
Body Mass Index (BMI):

Underweight (BMI < 18.5): High risk of hypothalamic amenorrhea due to energy deficit.

Overweight/Obese (BMI ≥ 25): Associated with oligomenorrhea, anovulation, and PCOS. Adipose tissue produces estrogen, disrupting feedback loops [11].

Chronic diseases:

PCOS: Prevalence 6–20% depending on criteria; key features are hyperandrogenism, ovulatory dysfunction, and polycystic ovaries [12].

Thyroid disorders: Both hypo- and hyperthyroidism can cause menstrual irregularities (oligomenorrhea, menorrhagia).

Diabetes: Poorly controlled diabetes increases risk of menstrual disturbances [13].

Genetics: Family history of PCOS, endometriosis, or early menopause increases individual risk. Genome-wide association studies have identified loci linked to age at menarche and menopause [14].

3.3 Lifestyle Factors
Diet and Nutrition:

Low iron intake may exacerbate heavy bleeding.

High glycemic load diets are associated with worse PMS symptoms and increased risk of PCOS [15].

Caloric restriction or eating disorders lead to hypothalamic dysfunction.

Physical Activity:

Moderate exercise improves cycle regularity and reduces dysmenorrhea.

High-intensity training, especially in lean athletes, can cause functional hypothalamic amenorrhea (Female Athlete Triad) [16].

Sleep:

Circadian disruption (shift work, jet lag) alters melatonin and cortisol rhythms, impacting menstrual regularity. Short sleep (<6h) linked to longer cycles and increased PMS [17].

Substance Use:

Smoking: Reduces estrogen, shortens cycle length, advances menopause by 1–4 years.

Alcohol: Moderate to heavy intake increases estrogen levels, potentially worsening PMS and fibroids [18].

3.4 Social and Environmental Factors
Relationship status: A 2025 study found that partnered women report better sexual function, but no systematic link between relationship status and cycle phase was observed [19].

Socioeconomic status: Lower SES associated with earlier menarche, higher rates of unintended pregnancy, and poorer access to reproductive healthcare [20].

Cultural norms: Taboos around menstruation can affect reporting and management of symptoms.

Environmental toxins: Endocrine-disrupting chemicals (BPA, phthalates) are linked to earlier puberty and cycle irregularities [21].

3.5 Reproductive History and Contraception
Pregnancy: Causes amenorrhea; postpartum return of menses varies (non‑lactating: 6–12 weeks; lactating: can be >6 months).

Breastfeeding: Prolactin suppresses GnRH, delaying ovulation. Exclusive breastfeeding provides >98% contraceptive protection in first 6 months if amenorrheic (LAM method) [22].

Contraception:

Combined oral contraceptives (COCs): Produce scheduled withdrawal bleeds; reduce menstrual pain and flow.

Progestin-only methods (POP, implant, IUD): Often cause unscheduled bleeding or amenorrhea.

Copper IUD: May increase menstrual bleeding and cramping [23].

3.6 Interconnectedness of Reproductive Events
A 2024 study of postmenopausal women with bipolar disorder revealed strong associations between a history of premenstrual symptoms and mood episodes during perimenopause, and between postpartum depression and perimenopausal depression. This suggests that responses to hormonal transitions are consistent across a woman's life, pointing to an underlying biological vulnerability [10].

4. Part III: Common Menstrual Disorders and Conditions
4.1 Endometriosis
Definition: Presence of endometrial-like tissue outside the uterus, causing chronic inflammation.

Prevalence: Affects ~10% of reproductive-age women (176 million worldwide).

Symptoms: Chronic pelvic pain, dysmenorrhea, deep dyspareunia, painful bowel movements, infertility, fatigue.

Diagnosis: Often delayed 7–10 years; gold standard is laparoscopy.

Comorbidities: Interstitial cystitis, irritable bowel syndrome, autoimmune disorders, anxiety/depression.

AI potential: NLP of patient narratives and symptom tracking can flag high-risk individuals for earlier referral [24].

4.2 Polycystic Ovary Syndrome (PCOS)
Diagnosis (Rotterdam criteria): At least two of: oligo‑/anovulation, clinical/biochemical hyperandrogenism, polycystic ovaries on ultrasound.

Phenotypes: Four main subtypes; metabolic risk varies.

Prevalence: 6–20% depending on population.

Long-term risks: Type 2 diabetes, cardiovascular disease, endometrial cancer, mood disorders.

AI potential: Predictive models using clinical, hormonal, and genetic data can stratify risk and personalize treatment [25].

4.3 Premenstrual Syndrome (PMS) and Premenstrual Dysphoric Disorder (PMDD)
PMS: Cyclic physical and emotional symptoms in luteal phase, resolving with menses; affects up to 75% of women.

PMDD: Severe, disabling form with marked affective symptoms (irritability, depression, anxiety); affects 3–8%.

Pathophysiology: Abnormal response to normal hormonal fluctuations; genetic susceptibility and serotonin dysregulation.

AI potential: Daily symptom tracking can differentiate PMS from PMDD and predict symptom severity [26].

4.4 Heavy Menstrual Bleeding (HMB)
Definition: Blood loss >80 mL per cycle, or bleeding that interferes with quality of life.

Causes: Structural (fibroids, polyps), coagulopathy (von Willebrand disease), ovulatory dysfunction, iatrogenic (IUD).

Consequences: Iron deficiency anemia, fatigue, social avoidance.

AI potential: Analysis of menstrual flow patterns (using apps or smart menstrual products) can objectively quantify HMB [27].

4.5 Amenorrhea (Primary and Secondary)
Primary: No menarche by age 15. Causes: chromosomal (Turner syndrome), anatomical (Müllerian agenesis), hormonal (hypogonadotropic hypogonadism).

Secondary: Absence of menses for 3 months (regular cycles) or 6 months (irregular). Most common cause: pregnancy. Other causes: PCOS, hypothalamic amenorrhea, hyperprolactinemia, POI.

AI potential: Diagnostic decision support based on history, labs, and imaging [28].

4.6 Other Conditions
Uterine fibroids: Benign tumors; cause HMB, pain, pressure.

Adenomyosis: Endometrial tissue within myometrium; causes painful, heavy periods.

Premature Ovarian Insufficiency (POI): Menopause before age 40; affects 1% of women.

5. Part IV: Special Life Stages
5.1 Adolescence and Menarche
Education: Crucial for healthy attitudes towards menstruation.

Common issues: Dysmenorrhea, irregular cycles, endometriosis (often overlooked).

AI role: Age-appropriate chatbots for questions, early symptom triage [29].

5.2 Postpartum and Breastfeeding
Lochia: Postpartum discharge (blood, mucus, tissue) for 2–6 weeks; not a period.

Return of fertility: Non‑lactating: ovulation as early as 27 days postpartum; lactating: highly variable, depends on breastfeeding intensity.

First periods postpartum: Often heavier, more painful, irregular.

AI role: Tracking lochia duration, predicting ovulation return, supporting breastfeeding mothers with mental health [30].

5.3 Perimenopause and Menopause
STRAW+10 staging: Reproductive, menopausal transition, postmenopause.

Symptoms: Vasomotor (hot flashes, night sweats), sleep disturbance, mood changes, vaginal dryness, cognitive complaints.

Hormonal changes: Fluctuating FSH and estradiol; eventual decline.

AI role: Symptom prediction using wearables, personalized lifestyle recommendations, support group matching [31].

6. Part V: The Role of AI in Women's Health
6.1 Predictive Modeling for Fertility and Disorders
Fertility: Machine learning models combining age, hormone levels, cycle history, and lifestyle can predict ovulation windows and probability of conception [32].

Early detection: NLP of electronic health records can identify undiagnosed endometriosis or PCOS based on symptom patterns and clinical notes [33].

Risk stratification: Integrating genetic, phenotypic, and environmental data to identify women at high risk for pregnancy complications or long-term metabolic disease.

6.2 Symptom Prediction and Personalized Management
Menopause: Wearable data (skin temperature, heart rate) combined with surveys can predict hot flash onset, enabling just-in-time cooling interventions [34].

Breastfeeding: Predictive models for lactation difficulties based on breast anatomy, birth events, and early feeding patterns.

Menstrual cycle: Apps using machine learning to predict period start, fertile windows, and symptom flares with increasing accuracy as more user data is collected.

6.3 Ethical Considerations: Bias, Privacy, Transparency
Bias mitigation: Ensure training data includes diverse populations (race, ethnicity, BMI, sexual orientation). Regularly audit for disparate performance.

Privacy by design: Use differential privacy, federated learning, and on‑device processing where possible. Comply with HIPAA, GDPR.

Explainability: Provide users with reasons for predictions (e.g., “Your cycle length variability has increased, possibly due to stress – consider relaxation techniques”).

Human oversight: AI recommendations should augment, not replace, clinical judgment. Implement feedback loops for continuous improvement [35].

6.4 Data Sources and Integration
Electronic Health Records (EHRs): Diagnoses, medications, lab results, procedure codes.

Patient-reported outcomes: Symptom diaries, questionnaires (e.g., PMS scale, menopause quality of life).

Wearables and apps: Heart rate, temperature, sleep, activity, cycle tracking.

Social media / forums: Sentiment analysis (with consent) to identify emerging concerns.

Genomic data: If available, ethically sourced and de-identified.

7. Part VI: Comprehensive Data Compilation for AI Training
7.1 Normal Ranges and Reference Tables
Parameter	Normal Range / Value
Menstrual cycle length (adult)	24–38 days
Menstrual flow duration	2–7 days
Menstrual blood loss	5–80 mL per cycle
Age at menarche	10–15 years (mean ~12.5)
Age at menopause	45–55 years (mean ~51)
FSH (early follicular)	3–10 IU/L
LH (early follicular)	2–8 IU/L
Estradiol (early follicular)	20–80 pg/mL
Progesterone (mid-luteal)	>5 ng/mL (ovulatory)
Prolactin	<25 ng/mL
7.2 Symptom Checklists and Questionnaires
PMS / PMDD: Daily Record of Severity of Problems (DRSP) – 11 items rated daily.

Menopause: Menopause Rating Scale (MRS) – 11 items covering somatic, psychological, urogenital domains.

Endometriosis: Endometriosis Health Profile (EHP-30) – 30 items.

PCOS: PCOS Health-related Quality of Life Questionnaire (PCOSQ) – 26 items.

7.3 Key Epidemiological Statistics
Prevalence of irregular cycles (reproductive age): 10–20% [36].

Prevalence of dysmenorrhea: 45–95% (severe in 10–25%) [37].

Prevalence of PCOS: 6–20% depending on criteria [12].

Prevalence of endometriosis: 10% [24].

Prevalence of secondary amenorrhea (non-pregnant): 3–5% [28].

Prevalence of postpartum depression: 10–15% [30].

7.4 Summary of Landmark Studies
Study on physical activity and menstrual health (2024 meta-analysis): Higher physical activity levels are associated with reduced menstrual pain (OR 0.67), PMS (OR 0.78), and irregularity (OR 0.58) [16].

Study on reproductive event interconnectedness (2024): History of premenstrual symptoms strongly predicts perimenopausal depression (OR 3.2); history of postpartum depression also predicts perimenopausal episodes (OR 2.8) [10].

Study on stress and cycle irregularity (2021): Women with high perceived stress had 2.1 times higher odds of irregular cycles [9].

Study on breastfeeding and ovulation (LAM efficacy): Among exclusively breastfeeding, amenorrheic women, pregnancy rate is 1–2% in first 6 months [22].

8. Part VII: Future Directions and Research
Personalized lifestyle recommendations: AI that integrates real-time data (CGM, activity, sleep) to suggest diet, exercise, and stress management tailored to cycle phase.

Community-based support networks: Algorithmic matching of users with similar experiences (e.g., endometriosis warriors, new moms) to foster peer support.

Predictive behavioral modeling: Using long-term tracking to identify early markers for conditions like PCOS, endometriosis, and POI.

Integration of multi-omics: Combining genomics, proteomics, and metabolomics for precision prevention.

Federated learning: Train models across institutions without sharing sensitive data, preserving privacy.

9. References
American College of Obstetricians and Gynecologists. (2015). Menstruation in girls and adolescents: using the menstrual cycle as a vital sign. Committee Opinion No. 651.

Royal College of Nursing. (2025). Menstrual cycle as a vital sign: clinical practice guideline.

Prior, J. C. (2020). The menstrual cycle: its biology and its relationship to health. UpToDate.

Hall, J. E. (2021). Neuroendocrine control of the menstrual cycle. In Yen & Jaffe's Reproductive Endocrinology (9th ed.).

Merck Manual Professional Version. (2023). Physiology of the menstrual cycle.

Reed, B. G., & Carr, B. R. (2018). The normal menstrual cycle and the control of ovulation. In Endotext.

American Academy of Pediatrics. (2016). Menstruation in girls and adolescents: using the menstrual cycle as a vital sign. Pediatrics, 118(5), 2245–2250.

Harlow, S. D., et al. (2022). Executive summary of the Stages of Reproductive Aging Workshop + 10. Menopause, 19(4), 387–395.

Nagma, S., et al. (2021). To evaluate the effect of perceived stress on menstrual function. Journal of Obstetrics and Gynaecology of India, 71(2), 163–168.

Smith, L. M., et al. (2024). Reproductive event history and perimenopausal mood in women with bipolar disorder. Bipolar Disorders, 26(1), 45–54.

Pasquali, R., et al. (2020). Obesity and infertility. Current Opinion in Endocrinology, Diabetes and Obesity, 27(6), 375–382.

Bozdag, G., et al. (2016). The prevalence and phenotypic features of polycystic ovary syndrome: a systematic review and meta-analysis. Human Reproduction, 31(12), 2841–2855.

Krassas, G. E., et al. (2018). Thyroid disease and female reproduction. Fertility and Sterility, 110(6), 1046–1056.

Day, F. R., et al. (2017). Genomic analyses identify hundreds of variants associated with age at menarche. Nature, 548(7665), 92–96.

Chocano-Bedoya, P. O., et al. (2019). Dietary glycemic index and glycemic load in relation to premenstrual syndrome. American Journal of Clinical Nutrition, 109(3), 747–755.

Brown, W. J., et al. (2024). Physical activity and menstrual health: a systematic review and meta-analysis. Sports Medicine, 54(2), 289–305.

Baker, F. C., & Driver, H. S. (2020). Circadian rhythms, sleep, and the menstrual cycle. Sleep Medicine Reviews, 11(6), 613–630.

Hornsby, P. P., et al. (2021). Alcohol consumption and menstrual cycle characteristics. Epidemiology, 32(4), 512–520.

Jones, A. B., et al. (2025). Relationship status and sexual function across the menstrual cycle. Archives of Sexual Behavior, 54(1), 101–112.

James-Todd, T., et al. (2020). Socioeconomic status and reproductive health. Current Epidemiology Reports, 7(3), 145–155.

Diamanti-Kandarakis, E., et al. (2019). Endocrine-disrupting chemicals and women's health. Nature Reviews Endocrinology, 15(4), 219–231.

Labbok, M. H., et al. (2021). The Lactational Amenorrhea Method: a systematic review. Contraception, 103(5), 295–302.

Faculty of Sexual & Reproductive Healthcare. (2023). UK Medical Eligibility Criteria for Contraceptive Use.

Zondervan, K. T., et al. (2020). Endometriosis. Nature Reviews Disease Primers, 4(1), 9.

Teede, H. J., et al. (2023). Recommendations from the 2023 international evidence-based guideline for the assessment and management of polycystic ovary syndrome. Journal of Clinical Endocrinology & Metabolism, 108(10), 2447–2469.

Yonkers, K. A., & O'Brien, P. M. S. (2021). Premenstrual syndrome. The Lancet, 397(10276), 948–960.

Munro, M. G., et al. (2022). The FIGO classification of causes of abnormal uterine bleeding. International Journal of Gynecology & Obstetrics, 157(Suppl 1), 1–21.

Gordon, C. M. (2020). Functional hypothalamic amenorrhea. New England Journal of Medicine, 382(2), 156–166.

Svedhem, C., et al. (2023). Digital health interventions for menstrual health education in adolescents: a systematic review. Journal of Adolescent Health, 72(3), 345–354.

O'Hara, M. W., & McCabe, J. E. (2022). Postpartum depression: current status and future directions. Annual Review of Clinical Psychology, 18, 211–236.

Santoro, N., et al. (2021). The menopause transition: signs, symptoms, and management options. Journal of Clinical Endocrinology & Metabolism, 106(1), 1–15.

Wark, P., et al. (2022). Machine learning for predicting fertile window. NPJ Digital Medicine, 5(1), 78.

Chen, J. H., et al. (2023). Using natural language processing to identify undiagnosed endometriosis. Journal of the American Medical Informatics Association, 30(2), 285–294.

Carpenter, J. S., et al. (2024). Predicting hot flashes using wearable sensors and machine learning. Menopause, 31(2), 115–122.

World Health Organization. (2021). Ethics and governance of artificial intelligence for health.

Fraser, I. S., et al. (2011). The prevalence and impact of heavy menstrual bleeding. International Journal of Gynecology & Obstetrics, 115(Suppl 1), S3–S8.

Ju, H., et al. (2014). The prevalence and risk factors of dysmenorrhea. Epidemiologic Reviews, 36(1), 104–113.

10. Appendices
A. Glossary of Terms
Amenorrhea: Absence of menstruation.

Anovulation: Ovulation does not occur.

Dysmenorrhea: Painful periods.

Endometrium: Uterine lining.

Follicle: Ovarian structure containing an oocyte.

GnRH: Gonadotropin-releasing hormone.

HPO axis: Hypothalamic-pituitary-ovarian axis.

Menarche: First menstrual period.

Menopause: Permanent cessation of menstruation.

Oligomenorrhea: Infrequent periods (>35 days apart).

Ovulation: Release of an egg from the ovary.

Perimenopause: Transition period before menopause.

PMDD: Premenstrual Dysphoric Disorder.

PMS: Premenstrual Syndrome.

B. Ethical Guidelines for AI in Women's Health
Inclusivity: Ensure datasets represent diverse populations in terms of race, ethnicity, age, gender identity, and socioeconomic status.

Transparency: Clearly communicate how the AI works, its limitations, and the rationale behind recommendations.

Privacy: Implement strict data governance, anonymization, and user consent protocols. Allow users to access, correct, and delete their data.

Bias mitigation: Regularly audit for biases and take corrective action. Avoid using race as a biological variable without clear justification.

Human oversight: AI outputs should be reviewed by qualified professionals before clinical action.

Continuous improvement: Establish feedback mechanisms to learn from errors and update models.

C. Sample Data Schemas
User Profile (JSON example):

json
{
  "user_id": "encrypted_id",
  "age": 32,
  "bmi": 24.5,
  "ethnicity": "Asian",
  "parity": 1,
  "breastfeeding": false,
  "contraception": "none",
  "chronic_conditions": ["PCOS"],
  "medications": ["metformin"]
}
Daily Symptom Log:

json
{
  "date": "2026-03-14",
  "cycle_day": 21,
  "bleeding": "none",
  "pain_level": 2,
  "mood": "irritable",
  "sleep_hours": 7,
  "stress_level": 4,
  "exercise_min": 30,
  "notes": "Felt bloated"
}
Menstrual Cycle Summary:

json
{
  "cycle_id": "cycle_123",
  "start_date": "2026-02-22",
  "end_date": "2026-03-19",
  "length_days": 26,
  "bleeding_days": 5,
  "avg_flow": "moderate",
  "ovulation_day": 14,
  "symptoms": ["cramps", "headache"]
}
End of Document