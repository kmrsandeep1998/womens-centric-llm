# Women-Centric AI Source Inventory and Collection Plan

## Objective

Create a trustworthy source base for a women-centric AI system. This file is a collection plan, not a dump of source text.

## 1. Source Classes

### Tier 1: Highest-priority sources

Use these first for knowledge grounding and retrieval.

- WHO
- CDC
- NIH / NICHD
- Office on Women's Health (U.S. HHS)
- ACOG
- NHS
- NICE
- Major peer-reviewed guidelines and consensus statements

### Tier 2: Strong supporting sources

- Mayo Clinic
- Cleveland Clinic
- Johns Hopkins
- Mass General / Brigham
- Stanford Medicine
- Major academic review papers

### Tier 3: Secondary or community sources

Use carefully and label separately.

- Patient forums
- Social media
- Anonymous Q&A
- Community datasets

These may help capture phrasing and question styles, but should not be treated as clinical truth.

## 2. Topic Coverage Map

### Menstrual health

- Cycle basics
- Normal ranges
- Heavy bleeding
- Irregular periods
- Dysmenorrhea
- PMS / PMDD
- Amenorrhea

### Reproductive context

- Ovulation
- Fertility
- Pregnancy and missed periods
- Emergency contraception
- Postpartum changes
- Breastfeeding/lactation

### Gynecologic conditions

- PCOS
- Endometriosis
- Adenomyosis
- Fibroids
- Polyps
- Ovarian cysts
- Pelvic inflammatory disease
- STIs affecting bleeding

### Endocrine and systemic contributors

- Thyroid disease
- Hyperprolactinemia
- Premature ovarian insufficiency
- Diabetes/metabolic syndrome
- Bleeding disorders
- Iron deficiency/anemia
- Eating disorders / RED-S

### Life-stage topics

- Menarche / puberty
- Reproductive age
- Perimenopause
- Menopause

## 3. Recommended Collection Spreadsheet Fields

Track every source with:

- source_id
- title
- organization
- url
- country
- topic_tags
- source_tier
- document_type
- publication_date
- access_date
- last_checked_date
- license_status
- trainable_for_model_flag
- retrieval_only_flag
- notes

## 4. Recommended Initial Source Targets

### Menstrual and reproductive health

- ACOG FAQ pages on abnormal uterine bleeding, heavy menstrual bleeding, first period, postpartum birth control, PCOS, perimenopausal bleeding
- Office on Women's Health pages on menstrual cycle, period problems, ovulation, emergency contraception, menopause
- NICHD pages on menstruation and irregularities
- NHS pages on bleeding between periods or after sex

### Broader health expansion

- WHO reproductive health pages
- CDC women's health and reproductive health resources
- NICE guidance on heavy menstrual bleeding and related gynecologic conditions
- Government/public health materials on STIs, contraception, pregnancy, and menopause

## 5. Collection Rules

- Prefer original guideline or official education pages over reposts
- Record exact URLs and dates accessed
- Recheck periodically because medical guidance can change
- Do not copy large copyrighted text into training assets
- Track license/usage rights explicitly
- If rights are unclear, use for retrieval/reference only

## 6. Retrieval vs Training Distinction

### Suitable for retrieval grounding

- Official health pages
- Guidelines
- FAQs
- Review articles with allowed access/use

### Suitable for model training only if rights are cleared

- Licensed corpora
- First-party user data with consent
- Internally created annotation data
- De-identified clinical or support data with proper approvals

## 7. Important Warning

The best medical web sources are often ideal for `retrieval`, but not automatically safe to `train on`.

## 8. Local Knowledge Artifacts

- `docs/references/women_health_knowledge_base.md`
  - Scope: Broad synthetic synthesis and curriculum-style summary for menstrual and reproductive health.
  - Status: Useful for retrieval grounding and data-gap planning, but evidence tags should be validated against primary sources before direct clinical use.
- `docs/references/women_health_knowledge_base_v3.md`
  - Scope: Expanded 3.0 synthesis with richer statistics, guideline-level summaries, and AI-product trend notes.
  - Status: High-coverage training seed content; treat as `summary_only` until mapped to primary source evidence.
- `docs/references/women_health_supplemental_reproductive_lifecycle.md`
  - Scope: Supplemental, lifecycle-focused synthesis covering puberty, pregnancy, menopause transition, and broader reproductive-health factors.
  - Status: Use as retrieval summary; validate critical clinical claims before direct training use.

That distinction must stay explicit throughout the project.
