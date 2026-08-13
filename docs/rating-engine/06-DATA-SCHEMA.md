# 06 — Proposed Data Schema

> **Reconciliation note, 2026-08-11.** This document was derived from the filed manual PDFs and **before any subline
> was derived end to end**. The per-subline gates have since superseded or sharpened some claims
> here — see [`../gates/RECONCILIATION.md`](../gates/RECONCILIATION.md) (items R2, R4). The text below is
> left as the record of what this derivation found on its own; that independence is what makes
> agreement between the two derivations evidence.

Derived from the corpus structure, not from a generic rating-engine template. Each table
below exists because a specific manual construct requires it, and the justifying source is
named.

Dialect: ANSI SQL, written for PostgreSQL. Types are indicative.

---

## 6.0 Design principles forced by the evidence

| # | Principle | Forced by |
|---|---|---|
| 1 | **Rules are keyed semantically, never by printed number** | CW 2027 renumbers 21 rules (§2.3) |
| 2 | **State content is an overlay of typed operations, not a copy of the rulebook** | Exception pages are `REPLACE` / `ADD` / `does not apply` against named paragraphs |
| 3 | **Everything is bitemporal** | 490 notices across 2021–2027; rating as-of-date is a first-class requirement |
| 4 | **ILF tables are state-owned and matrix-shaped** | Rule 56.B: *"displayed in the state exceptions"*; tables are aggregate × occurrence |
| 5 | **The ILTA code is composite and must be decomposed on ingest** | Rule 15.D.2: Prem-Ops Tables 1–3, Prod/CompOps Tables A–C |
| 6 | **Payroll limitation is a typed variant, not a scalar** | 3 distinct shapes across 51 jurisdictions (§5.1) |
| 7 | **`REFER_TO_COMPANY` is a modelled outcome, not an error** | Rules 41, 42, 43, 47, 53 state it explicitly |
| 8 | **Every stored value carries its source PDF, page and edition marker** | Auditability / filing defence |

---

## 6.1 Provenance spine

Every other table references `source_document`. Nothing is stored without provenance.

```sql
CREATE TABLE source_document (
    document_id        BIGSERIAL PRIMARY KEY,
    file_name          TEXT NOT NULL UNIQUE,      -- 'GL-TX-2025-RU-001-C.pdf'
    notice_id          TEXT NOT NULL,             -- 'GL-TX-2025-RU-001'
    line_of_business   TEXT NOT NULL DEFAULT 'GL',
    manual_division    TEXT NOT NULL DEFAULT 'DIVISION SIX',
    jurisdiction       CHAR(2) NOT NULL,          -- 'TX'; 'MU' = countrywide/multistate
    notice_year        SMALLINT NOT NULL,
    notice_seq         SMALLINT NOT NULL,
    circular_refs      TEXT[],                    -- cover page 'Circular Reference(s):'
    filing_refs        TEXT[],                    -- cover page 'Filing Reference(s):'
    edition_marker     TEXT,                      -- '21st Edition 5-20' (page footer)
    sha256             CHAR(64) NOT NULL,
    page_count         INT,
    extraction_engine  TEXT NOT NULL,             -- 'pdftotext-raw' | 'pdftotext-layout' | 'pypdf'
    extraction_status  TEXT NOT NULL,             -- 'OK' | 'RECOVERED' | 'FAILED'
    ingested_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (jurisdiction, notice_year, notice_seq)
);

CREATE TABLE source_span (                        -- anchor for any extracted fact
    span_id      BIGSERIAL PRIMARY KEY,
    document_id  BIGINT NOT NULL REFERENCES source_document,
    page_marker  TEXT,                            -- 'CG-E-2', 'CG-CT-1', 'CG-ILADD-1'
    pdf_page     INT,
    char_start   INT,
    char_end     INT,
    raw_text     TEXT NOT NULL
);
```

> **Do not date a notice from `edition_marker`.** The ERC mapping work already established
> that footer edition markers record when a *page* last changed, not when the notice took
> effect. Effective dates come from the ERC circular metadata join (§6.2).

---

## 6.2 Edition & effective-date model

```sql
CREATE TABLE manual_edition (
    edition_id        BIGSERIAL PRIMARY KEY,
    scope             TEXT NOT NULL CHECK (scope IN ('COUNTRYWIDE','JURISDICTION')),
    jurisdiction      CHAR(2),                    -- NULL when scope='COUNTRYWIDE'
    document_id       BIGINT NOT NULL REFERENCES source_document,
    rule_numbering_id BIGINT NOT NULL REFERENCES rule_numbering_scheme,
    effective_from    DATE NOT NULL,              -- from ERC circular metadata
    effective_to      DATE,                       -- NULL = open
    erc_version       TEXT,                       -- 'GL TX 20250401 V01'
    erc_cw_parent     TEXT,                       -- 'GL_CW_20201201_V01'
    CHECK (scope = 'COUNTRYWIDE' OR jurisdiction IS NOT NULL)
);
CREATE INDEX ON manual_edition (scope, jurisdiction, effective_from, effective_to);
```

`erc_version` / `erc_cw_parent` are the join back to `GL_ERC_to_Manual.xlsx`, preserving the
mapping already completed in Step 3 of the process log.

---

## 6.3 The rule catalog and the renumbering map

This pair of tables is the direct answer to the edition-renumbering hazard.

```sql
-- Stable semantic identity. Never changes across editions.
CREATE TABLE rule_concept (
    rule_key     TEXT PRIMARY KEY,           -- 'GL.PREMIUM_DETERMINATION'
    section      TEXT NOT NULL,              -- 'I' | 'II' | 'III' | 'IV'
    canon_title  TEXT NOT NULL,
    subline_code TEXT,                       -- '332' where the rule is subline-bound
    coverage_key TEXT REFERENCES coverage(coverage_key)
);

CREATE TABLE rule_numbering_scheme (
    rule_numbering_id BIGSERIAL PRIMARY KEY,
    label             TEXT NOT NULL,         -- 'CW-2022' | 'CW-2027'
    document_id       BIGINT REFERENCES source_document
);

-- The map. Resolves a printed number to a concept, WITHIN an edition.
CREATE TABLE rule_number_map (
    rule_numbering_id BIGINT NOT NULL REFERENCES rule_numbering_scheme,
    printed_number    TEXT   NOT NULL,       -- '35' or '21' or 'A2'
    rule_key          TEXT   NOT NULL REFERENCES rule_concept,
    printed_title     TEXT   NOT NULL,
    is_reserved       BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (rule_numbering_id, printed_number)
);
```

Worked example of what this prevents:

| Scheme | printed_number | rule_key |
|---|---|---|
| `CW-2022` | `35` | `GL.PREMIUM_DETERMINATION` |
| `CW-2027` | `21` | `GL.PREMIUM_DETERMINATION` |
| `CW-2022` | `22` | `GL.CGL_DESCRIPTION` |
| `CW-2027` | `22` | `GL.MANDATORY_ENDORSEMENTS` |

A Texas overlay written against `CW-2022` saying *"Rule 22 is replaced"* resolves to
`GL.CGL_DESCRIPTION` — **not** to Mandatory Endorsements. Resolving it under the wrong scheme
silently misapplies the deviation. This is the highest-severity correctness risk in the
project.

---

## 6.4 State overlay — typed deviation operations

```sql
CREATE TYPE deviation_op AS ENUM ('REPLACE','ADD','DELETE','AMEND','TABLE','OTHER');

CREATE TABLE state_deviation (
    deviation_id   BIGSERIAL PRIMARY KEY,
    edition_id     BIGINT NOT NULL REFERENCES manual_edition,   -- jurisdiction-scoped
    rule_key       TEXT   NOT NULL REFERENCES rule_concept,
    printed_number TEXT   NOT NULL,        -- as printed in the exception pages
    op             deviation_op NOT NULL,
    target_path    TEXT,                   -- 'E.2.m' | 'C.2,C.3' | 'D.4' | NULL = whole rule
    body_text      TEXT NOT NULL,
    span_id        BIGINT NOT NULL REFERENCES source_span,
    UNIQUE (edition_id, rule_key, printed_number, op, target_path)
);
CREATE INDEX ON state_deviation (rule_key, op);
```

`target_path` is essential and is directly observable in the corpus — the exception pages
address paragraphs surgically:

| Observed text | `op` | `target_path` |
|---|---|---|
| *"Paragraph A. is replaced by the following"* | `REPLACE` | `A` |
| *"Paragraphs C.2. and C.3. are replaced by the following"* | `REPLACE` | `C.2,C.3` |
| *"The following is added to Paragraph E.2.m."* | `ADD` | `E.2.m` |
| *"The following is added to Rule 11."* | `ADD` | *(NULL — whole rule)* |
| *"Paragraph F. does not apply."* | `DELETE` | `F` |
| *"Rule 34. is replaced by the following: This rule does not apply."* | `REPLACE` | *(NULL)* |

Note the last row: a `REPLACE` whose body is *"This rule does not apply"* is semantically a
deletion but syntactically a replacement. Store the operation **as written** and let the
resolver interpret; do not normalise at ingest, or you lose the ability to reproduce the
manual text.

### State-only additional rules

```sql
CREATE TABLE state_additional_rule (
    a_rule_id      BIGSERIAL PRIMARY KEY,
    edition_id     BIGINT NOT NULL REFERENCES manual_edition,
    printed_number TEXT NOT NULL,          -- 'A1','A2',...
    title          TEXT NOT NULL,
    theme_key      TEXT,                   -- 'TERRORISM_PREMIUM' | 'TERRITORY' | 'STOP_GAP' | ...
    body_text      TEXT NOT NULL,
    span_id        BIGINT NOT NULL REFERENCES source_span
);
```

`theme_key` is needed because A-rule *numbering is not stable across jurisdictions* — Alaska's
`A1` is Attorney's Fees, Alabama's `A2` is Rating Territories. The number carries no meaning
across jurisdictions; only the title does. Observed themes and counts are in
`04-STATE-DEVIATIONS.md` §4.4.

---

## 6.5 Classification & exposure

```sql
CREATE TABLE class_group (
    group_key   TEXT PRIMARY KEY,   -- 'MERCANTILE'
    code_lo     INT NOT NULL,
    code_hi     INT NOT NULL,
    label       TEXT NOT NULL
);
-- seeded: 10000-19999 Mercantile, 40000-49999 Miscellaneous,
--         50000-59999 Manufacturing And Processing,
--         60000-69999 Building Or Premises, 90000-99999 Contracting Or Servicing

CREATE TYPE premium_base AS ENUM
  ('ADMISSIONS','AREA','EACH','GROSS_SALES','PAYROLL',
   'TOTAL_COST','TOTAL_OPERATING_EXPENDITURES','UNITS');

CREATE TABLE classification (
    classification_id BIGSERIAL PRIMARY KEY,
    edition_id        BIGINT NOT NULL REFERENCES manual_edition,   -- countrywide
    class_code        CHAR(5) NOT NULL,
    description       TEXT NOT NULL,
    group_key         TEXT NOT NULL REFERENCES class_group,
    base              premium_base NOT NULL,
    base_unit         TEXT,            -- 'per $1,000 gross sales'
    application       TEXT,
    application_exception TEXT,
    premium_computation_note TEXT,     -- e.g. 'No separate loss cost applies for prod/comp ops'
    has_prodcompops   BOOLEAN,         -- FALSE where the manual shows (-) or code 60000-69999
    span_id           BIGINT NOT NULL REFERENCES source_span,
    UNIQUE (edition_id, class_code)
);

CREATE TABLE classification_cross_ref (      -- 'Separately Classify And Rate:' entries
    classification_id BIGINT NOT NULL REFERENCES classification,
    ref_kind          TEXT NOT NULL,  -- 'SEPARATELY_CLASSIFY' | 'ASSIGN_INSTEAD'
    ref_class_code    CHAR(5),
    ref_text          TEXT NOT NULL
);
```

`has_prodcompops` encodes Rule 48.F.1 directly and prevents rating a products component for
Building-Or-Premises classes.

---

## 6.6 Increased limits — the state-owned core

```sql
-- Which physical Rule 56.B table exists in a jurisdiction's exception pages
CREATE TABLE ilf_table (
    ilf_table_id   BIGSERIAL PRIMARY KEY,
    edition_id     BIGINT NOT NULL REFERENCES manual_edition,   -- jurisdiction-scoped
    table_ordinal  SMALLINT NOT NULL,      -- the n in 'Table 56.B.n.'
    subline_code   TEXT NOT NULL,          -- '334','336','335','332'
    table_family   TEXT NOT NULL,          -- 'PREM_OPS'|'PROD_COMPOPS'|'RAILROAD_PROTECTIVE'
                                           -- |'LIQUOR'|'GOVERNMENTAL_UNITS'|'ELEVATOR_CONTRACTORS'
    table_label    TEXT,                   -- '1','2','3','A','B','C'
    basic_limit    TEXT,                   -- '100/200'
    span_id        BIGINT NOT NULL REFERENCES source_span,
    UNIQUE (edition_id, table_ordinal)
);

-- The matrix cells: aggregate x per-occurrence
CREATE TABLE ilf_factor (
    ilf_table_id     BIGINT NOT NULL REFERENCES ilf_table,
    occurrence_limit INT NOT NULL,         -- in $000s, per Rule 56.A.1
    aggregate_limit  INT NOT NULL,         -- in $000s
    factor           NUMERIC(8,4) NOT NULL,
    refer_to_company BOOLEAN NOT NULL DEFAULT FALSE,   -- the flagged block, Rule 56.A.2
    PRIMARY KEY (ilf_table_id, occurrence_limit, aggregate_limit)
);

-- Class code -> table assignment. The composite code is decomposed here.
CREATE TABLE ilta_assignment (
    edition_id       BIGINT NOT NULL REFERENCES manual_edition,   -- jurisdiction-scoped
    class_code       CHAR(5) NOT NULL,
    raw_code         TEXT NOT NULL,        -- '2B' exactly as printed
    prem_ops_table   TEXT,                 -- '2'  <- digit
    prod_compops_table TEXT,               -- 'B'  <- letter
    basic_limit      TEXT NOT NULL,        -- '100/200'
    span_id          BIGINT NOT NULL REFERENCES source_span,
    PRIMARY KEY (edition_id, class_code, basic_limit)
);
```

`refer_to_company` is not optional decoration — every state ILF page splits into a usable
block and a block captioned *"The following factors MUST be referred to company before
using."* Losing that flag produces quotes the manual forbids.

**Countrywide ILF adjustments** (these *are* CW, unlike the tables themselves):

```sql
CREATE TABLE medpay_ilf_adjustment (          -- CW Table 23.D.3
    group_key    TEXT NOT NULL REFERENCES class_group,
    medpay_limit INT  NOT NULL,               -- 10000,15000,20000,25000
    factor       NUMERIC(6,4) NOT NULL,
    PRIMARY KEY (group_key, medpay_limit)
);
-- applied as: adjusted_ilf = medpay_factor + ilf - 1     (Rule 23.D.2.c)

CREATE TABLE split_limit_weight (             -- CW Rule 23.D.5.c
    group_key   TEXT PRIMARY KEY REFERENCES class_group,
    bi_weight   NUMERIC(6,4) NOT NULL,
    pd_weight   NUMERIC(6,4) NOT NULL,
    constant    NUMERIC(6,4) NOT NULL
);
```

---

## 6.7 State variables (the parameter surface)

A deliberately narrow, typed table rather than a wide per-state row. The manual's variables
are heterogeneous in shape; a wide table would force nulls and lose the shape distinction.

```sql
CREATE TABLE state_variable (
    edition_id  BIGINT NOT NULL REFERENCES manual_edition,
    var_key     TEXT   NOT NULL,     -- see registry below
    variant     TEXT,                -- discriminator, e.g. payroll shape
    num_value   NUMERIC(14,4),
    text_value  TEXT,
    unit        TEXT,                -- 'USD_ANNUAL' | 'USD_WEEKLY' | 'GRADE' | 'PCT'
    span_id     BIGINT NOT NULL REFERENCES source_span,
    PRIMARY KEY (edition_id, var_key, COALESCE(variant,''))
);
```

### Variable registry (every one observed in the corpus)

| `var_key` | Unit | Variants | Coverage |
|---|---|---|---|
| `PAYROLL.SHAPE` | — | `ANNUAL_CAP_BOTH` (45) · `WEEKLY_MINMAX_EXEC+ANNUAL_INDIV` (5) · `ANNUAL_INDIV_ONLY` (1) | 51/51 |
| `PAYROLL.EXEC_ANNUAL` | USD_ANNUAL | — | 45 |
| `PAYROLL.INDIV_ANNUAL` | USD_ANNUAL | — | 46 |
| `PAYROLL.EXEC_WEEKLY_MAX` | USD_WEEKLY | — | 5 |
| `PAYROLL.EXEC_WEEKLY_MIN` | USD_WEEKLY | — | 5 |
| `PAYROLL.SEASONAL_REDUCTION_PCT` | PCT | — | 6 |
| `LIQUOR.NUMERICAL_GRADE` | GRADE | — | 51/51 |
| `TERRITORY.BASIS` | — | `ZIP_LOCATION_OF_RISK` | 27 |
| `MIN_PREMIUM.POLICYWRITING` | USD | — | jurisdiction-specific |
| `STOPGAP.AVAILABLE` | BOOL | — | 5 |
| `ELP.REFERENCED` | BOOL | — | 27 |

---

## 6.8 Rating request / result (bitemporal, auditable)

```sql
CREATE TABLE rating_request (
    request_id      UUID PRIMARY KEY,
    jurisdiction    CHAR(2) NOT NULL,
    effective_date  DATE NOT NULL,          -- selects the edition
    coverage_parts  TEXT[] NOT NULL,
    payload         JSONB NOT NULL,
    requested_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE rating_result (
    request_id     UUID NOT NULL REFERENCES rating_request,
    line_no        INT  NOT NULL,
    coverage_key   TEXT NOT NULL,
    subline_code   TEXT NOT NULL,
    class_code     CHAR(5),
    exposure       NUMERIC(18,4),
    base_rate      NUMERIC(14,6),
    ilf            NUMERIC(10,4),
    deductible_factor NUMERIC(10,4),
    other_factors  JSONB,
    premium        NUMERIC(14,2),
    outcome        TEXT NOT NULL,          -- 'RATED' | 'REFER_TO_COMPANY' | 'INELIGIBLE'
    referral_reason TEXT,
    PRIMARY KEY (request_id, line_no)
);

-- The audit trail: which manual text produced this number
CREATE TABLE rating_trace (
    request_id  UUID NOT NULL REFERENCES rating_request,
    line_no     INT  NOT NULL,
    step_no     INT  NOT NULL,             -- Rule 21 step A..I
    rule_key    TEXT NOT NULL,
    applied_from TEXT NOT NULL,            -- 'CW' | 'STATE_OVERLAY' | 'STATE_A_RULE'
    edition_id  BIGINT NOT NULL REFERENCES manual_edition,
    span_id     BIGINT REFERENCES source_span,
    detail      JSONB,
    PRIMARY KEY (request_id, line_no, step_no)
);
```

`rating_trace` is what makes the engine defensible in a filing or audit conversation: every
premium component points at a paragraph of a named PDF.

---

## 6.9 JSON contract (engine I/O)

```jsonc
// Request
{
  "jurisdiction": "TX",
  "effective_date": "2026-03-01",
  "coverage_parts": ["CGL"],
  "limits": { "occurrence": 1000000, "general_aggregate": 2000000,
              "products_aggregate": 2000000, "medical_payments": 10000,
              "damage_to_premises": 100000 },
  "deductible": { "basis": "PER_OCCURRENCE", "applies_to": "BI_PD",
                  "prem_ops": 5000, "prod_compops": 0 },
  "claims_made": { "enabled": false, "retroactive_date": null },
  "exposures": [
    { "line_no": 1, "class_code": "10015", "territory": "005",
      "base": "GROSS_SALES", "units": 2400 }
  ],
  "payroll_detail": [
    { "line_no": 1, "role": "EXECUTIVE_OFFICER", "count": 3, "reported_annual": 250000 }
  ]
}
```

```jsonc
// Response (abridged)
{
  "request_id": "…",
  "edition": { "countrywide": "GL-MU-2027-RU-001", "state": "GL-TX-2025-RU-001",
               "rule_numbering": "CW-2027" },
  "lines": [
    { "line_no": 1, "coverage": "PREM_OPS", "subline": "334",
      "outcome": "RATED", "premium": 4182.00,
      "trace": [
        { "step": "A", "rule_key": "GL.CLASSIFICATIONS", "applied_from": "CW",
          "detail": { "class_code": "10015", "base": "GROSS_SALES" } },
        { "step": "B", "rule_key": "GL.BASES_OF_PREMIUM", "applied_from": "STATE_OVERLAY",
          "detail": { "payroll_shape": "ANNUAL_CAP_BOTH", "exec_annual": 39800,
                      "source": "GL-TX-2025-RU-001-C.pdf" } },
        { "step": "E", "rule_key": "GL.INCREASED_LIMITS_TABLES", "applied_from": "STATE_OVERLAY",
          "detail": { "ilta_raw": "2B", "prem_ops_table": "2",
                      "occurrence": 1000, "aggregate": 2000, "ilf": 1.23 } }
      ] }
  ],
  "referrals": []
}
```

---

## 6.10 What the schema deliberately does **not** contain

| Absent | Why |
|---|---|
| ~~`loss_cost` populated~~ | **Superseded.** The loss cost corpus supplies these; the tables are specified in §6.14. |
| ~~`elp_value`~~ | **Superseded.** See §6.14. |
| ~~`territory_definition` (ZIP → territory)~~ | **Superseded.** The Territory Pages (`CG-T-n`) of the Rules notices carry it in all 51 jurisdictions; see §6.14. |
| `terrorism_rate` | Terrorism Supplement, outside both corpora (Rule 55 / state A-rules). |
| Experience / schedule / composite rating modifiers | CGLES, CRP, SOR plans — separate manuals. |
| Company loss cost multiplier | Carrier input by design (Rule 23.B). Every stored value is a **pre-LCM ISO loss cost**. |
| Workers Compensation loss costs | Required only for OCP class `15191`; a cross-line dependency (gap G9). |

These are **named and stubbed**, not silently omitted, so that the integration surface is
explicit from day one. See `09-GAPS-AND-OPEN-QUESTIONS.md`.

---

## 6.11 Coverage parts, algorithms and rule suspension

Derived from the canonical rule anatomy in `11-RATING-ARCHITECTURE.md` §11.1–11.2. Every
coverage rule is written to the same skeleton, so one table shape serves all of them — and the
**nullable columns carry meaning**.

```sql
CREATE TYPE algo_archetype AS ENUM (
    'A1_FULL_NINE_STEP',      -- Prem-Ops (21), Prod-CompOps (48), Liquor (45)
    'A2_EIGHT_STEP_NO_BASE',  -- OCP (46), Railroad Protective (49)
    'A3_FACTOR_ON_HOST',      -- Product Withdrawal (44), LoED / Cyber (40)
    'A4_MODIFIER_CHAIN',      -- Unmanned Aircraft (37)
    'A5_REFER_TO_COMPANY'     -- EDL (42), EBL (43), Pollution (47), UST (53), Abuse (41)
);

CREATE TABLE coverage_part (
    coverage_part_id BIGSERIAL PRIMARY KEY,
    edition_id     BIGINT NOT NULL REFERENCES manual_edition,
    rule_key       TEXT   NOT NULL REFERENCES rule_concept,
    subline_code   TEXT,                      -- '334','336','332','335','350','365','370','325'
    coverage_key   TEXT   NOT NULL,           -- 'LIQUOR','OCP','PRINCIPALS_PROTECTIVE',...
    archetype      algo_archetype NOT NULL,
    host_coverage_key TEXT,                   -- A3 only: the subline whose rate it scales
    para_rates     TEXT,                      -- nullable paragraph letters; NULL = absent
    para_ilf       TEXT,
    para_classes   TEXT,
    para_premium   TEXT NOT NULL,
    para_deductible TEXT,                     -- NULL for Rules 46 and 49 — deductible unsupported
    para_claims_made TEXT,
    UNIQUE (edition_id, coverage_key)
);
```

`para_deductible IS NULL` is not missing data — it means the manual provides **no deductible
mechanism** for that coverage, and a deductible on the request must be **rejected at
validation**, never silently ignored.

`host_coverage_key` makes the A3 dependency explicit so the pipeline can topologically order
coverages: Prod/CompOps must rate before Product Withdrawal, LoED and Cyber.

### Rule suspension (Paragraph B)

```sql
CREATE TABLE coverage_rule_suspension (
    coverage_part_id BIGINT NOT NULL REFERENCES coverage_part,
    suspended_rule_key TEXT NOT NULL REFERENCES rule_concept,
    target_path      TEXT,          -- 'A,B,C,D,F' for Rule 45.B over Rule 15; NULL = whole rule
    replacement_path TEXT,          -- 'J' — where the replacement machinery lives
    span_id          BIGINT NOT NULL REFERENCES source_span,
    PRIMARY KEY (coverage_part_id, suspended_rule_key, target_path)
);
```

Evaluated **before** the pipeline runs. Two documented instances: Rule 45.B suspends Rule 15
Paragraphs A–D and F for Liquor; Rule 44.A.4 suspends Rule 16 (Additional Interests) entirely
for Product Withdrawal and swaps `IL 00 03` for `CG 31 98`.

---

## 6.12 Endorsement catalog

From `A3-ENDORSEMENT-CATALOG.md` — **328 distinct forms across 447 placements**.

```sql
CREATE TYPE endorsement_role AS ENUM (
    'COVERAGE_FORM','COVERAGE_TRANSFORM','MANDATORY_MULTISTATE',
    'CONDITIONAL_MANDATORY_MULTISTATE','MANDATORY_CLASSIFICATION_MULTISTATE',
    'STATE_MANDATORY','OPTIONAL_RTC','ADDITIONAL_OPTIONAL_RTC',
    'ADDITIONAL_INSURED','REFERENCED'
);

CREATE TABLE endorsement (
    endorsement_id BIGSERIAL PRIMARY KEY,
    edition_id     BIGINT NOT NULL REFERENCES manual_edition,
    coverage_part_id BIGINT NOT NULL REFERENCES coverage_part,
    form_number    TEXT   NOT NULL,           -- 'CG 04 37'
    form_title     TEXT,
    role           endorsement_role NOT NULL,
    governing_path TEXT,                      -- 'C.1','D.3.j','A.3.a'
    in_loss_cost   BOOLEAN NOT NULL,          -- TRUE for the mandatory family
    carries_limit  BOOLEAN NOT NULL DEFAULT FALSE,
    limit_capped_by TEXT,                     -- 'EACH_OCCURRENCE' | 'GENERAL_AGGREGATE' | ...
    span_id        BIGINT NOT NULL REFERENCES source_span,
    UNIQUE (edition_id, coverage_part_id, form_number)
);
```

> **The key is `(edition, coverage_part, form)` — never `form` alone.** The same form carries
> different roles in different coverage parts, and the catalog is edition-scoped because
> **40 forms are new in CW 2027 and 21 present in CW 2022 are gone**. A prior-edition policy
> validated against the current catalog would be wrongly rejected.

`in_loss_cost = TRUE` inverts the usual sign: **removing** such an endorsement is a
refer-to-company event, because *"the applicable loss cost(s) currently contemplate the
attachment of these endorsements."* An additive-charge-only model cannot express this.

### Attachment constraints

```sql
CREATE TYPE constraint_kind AS ENUM ('MUTUALLY_EXCLUSIVE','FORBIDDEN_WITH','REQUIRES');

CREATE TABLE endorsement_constraint (
    constraint_id  BIGSERIAL PRIMARY KEY,
    edition_id     BIGINT NOT NULL REFERENCES manual_edition,
    kind           constraint_kind NOT NULL,
    form_a         TEXT NOT NULL,
    form_b         TEXT NOT NULL,
    condition_text TEXT,                      -- e.g. liquor grade = 0 gate for CG 24 08
    span_id        BIGINT NOT NULL REFERENCES source_span
);
```

These come from imperatives in the manual body — *"Do not attach more than one of the
endorsements referenced in Paragraph A.3.j."*, *"When Endorsement CG 04 25 … is attached, do
not attach Endorsement CG 21 85"* — and are validated **before** rating, not after.

---

## 6.13 Referral predicates

Several coverages are algorithmic **or** refer-to-company depending on a Declarations field,
so a static per-coverage flag is insufficient (`11-RATING-ARCHITECTURE.md` §11.5.1).

```sql
CREATE TABLE referral_predicate (
    predicate_id   BIGSERIAL PRIMARY KEY,
    edition_id     BIGINT NOT NULL REFERENCES manual_edition,
    coverage_key   TEXT NOT NULL,
    trigger_field  TEXT NOT NULL,   -- 'PARTICIPATION_PERCENTAGE' | 'CUT_OFF_DATE' | ...
    trigger_when   TEXT NOT NULL,   -- 'IS_PRESENT' | 'EXCEEDS_TABLE_MAX' | 'NON_OWNED'
    referral_scope TEXT NOT NULL,   -- 'PREMIUM' | 'FACTOR' | 'WHOLE_COVERAGE'
    manual_text    TEXT NOT NULL,
    span_id        BIGINT NOT NULL REFERENCES source_span
);
```

Documented instances include: Product Withdrawal Participation Percentage and Cut-off Date
(Rule 44.A.5.a.f/g); non-owned unmanned aircraft operated by other parties (Rule 37.C.2.a);
Damage To Premises Rented To You above `$100,000` and Medical Payments above `$25,000`
(Rule 23); ILF interpolation where neither bounding limit appears in the table (Rule 56.A.4);
and every Rule 40 minimum premium (*"Refer to company for minimum premium"*).

---

## 6.14 Loss costs, ELPs and territory (the rate layer)

Derived from `13-LOSS-COSTS-AND-ELP.md`. Three design forces shape this section, and each
rules out the obvious simpler design:

1. **Territory applies to Premises/Operations only.** Products/Completed Operations is always
   written to the reserved statewide territory `999`. A single `territory` column is right;
   a `territory`-less rate table is not.
2. **The cell alphabet is closed and non-numeric values carry meaning.** `–` (not offered) and
   `(a)` (refer) are dispositions, not missing data. A numeric `NULL` cannot distinguish them,
   so the disposition is its own column and `loss_cost` is nullable *because of it*.
3. **Rate resolution is recursive.** `CG-LCADD` mappings express one class's loss cost as a
   percentage of another's, so the rate layer is a small graph, not a flat lookup.

```sql
CREATE TABLE lc_edition (                  -- one per loss cost notice
    lc_edition_id  BIGSERIAL PRIMARY KEY,
    jurisdiction   CHAR(2) NOT NULL,
    notice_id      TEXT NOT NULL UNIQUE,   -- 'GL-AK-2026-LC-001'
    effective_from DATE NOT NULL,          -- from ERC circular metadata, never the page footer
    effective_to   DATE,
    date_confidence TEXT NOT NULL          -- 'HIGH' (cited circular) | 'LOW' (proximity)
        CHECK (date_confidence IN ('HIGH','LOW')),
    vintage        TEXT NOT NULL           -- 'PRE_2027' | 'V2027'  (13-LOSS-COSTS §13.7)
        CHECK (vintage IN ('PRE_2027','V2027')),
    territory_count SMALLINT NOT NULL,
    span_id        BIGINT NOT NULL REFERENCES source_span,
    EXCLUDE USING gist (jurisdiction WITH =, daterange(effective_from, effective_to) WITH &&)
);

CREATE TYPE rate_disposition AS ENUM (
    'PUBLISHED',      -- numeric loss cost
    'NOT_OFFERED',    -- printed '-'  : coverage unavailable for this class/subline
    'REFER'           -- printed '(a)': refer to company, consult the ELP
);

CREATE TABLE loss_cost (
    lc_edition_id BIGINT NOT NULL REFERENCES lc_edition,
    subline_code  CHAR(3) NOT NULL,        -- '334' | '336' | '335' | '370'
    territory     CHAR(3) NOT NULL,        -- '501'... ; ALWAYS '999' for subline 336
    class_code    CHAR(5) NOT NULL,
    disposition   rate_disposition NOT NULL,
    loss_cost     NUMERIC(12,4),           -- NULL unless disposition = 'PUBLISHED'
    basic_limit   TEXT NOT NULL,           -- '100/200' | '100/300' (Railroad Protective)
    span_id       BIGINT NOT NULL REFERENCES source_span,
    PRIMARY KEY (lc_edition_id, subline_code, territory, class_code),
    CHECK ((disposition = 'PUBLISHED') = (loss_cost IS NOT NULL)),
    CHECK (subline_code <> '336' OR territory = '999')
);

CREATE TYPE elp_disposition AS ENUM (
    'MANUAL',         -- 'Manual -' : a loss cost exists on the grid; do not use an ELP
    'PUBLISHED',      -- '$n.nn' with an H/R index
    'RTC',            -- refer to company, no ELP reference available
    'INCLUDED',       -- 'Incl. -' : included in Prem/Ops at no additional charge
    'EXTERNAL_PCT'    -- e.g. OCP 15191: % of the otherwise applicable WC loss costs
);

CREATE TABLE elp (
    lc_edition_id BIGINT NOT NULL REFERENCES lc_edition,
    subline_code  CHAR(3) NOT NULL,
    class_code    CHAR(5) NOT NULL,
    disposition   elp_disposition NOT NULL,
    elp_value     NUMERIC(12,4),            -- NULL unless disposition = 'PUBLISHED'
    homogeneity   SMALLINT CHECK (homogeneity BETWEEN 1 AND 5),    -- Procedure 3
    reliability   CHAR(1)  CHECK (reliability BETWEEN 'A' AND 'E'),-- Procedure 4
    external_line TEXT,                     -- 'WORKERS_COMPENSATION'
    external_pct  NUMERIC(6,3),             -- 75.0
    basic_limit   TEXT NOT NULL,
    span_id       BIGINT NOT NULL REFERENCES source_span,
    PRIMARY KEY (lc_edition_id, subline_code, class_code),
    CHECK ((disposition = 'PUBLISHED') = (elp_value IS NOT NULL)),
    CHECK ((disposition = 'EXTERNAL_PCT') = (external_line IS NOT NULL))
);

-- CG-LCADD: a class whose loss cost is a percentage of another class's
CREATE TABLE loss_cost_mapping (
    lc_edition_id  BIGINT NOT NULL REFERENCES lc_edition,
    class_code     CHAR(5) NOT NULL,
    pct            NUMERIC(6,2) NOT NULL,   -- 100.00, 116.00, 65.00
    source_class   CHAR(5) NOT NULL,
    source_subline CHAR(3) NOT NULL DEFAULT '334',
    span_id        BIGINT NOT NULL REFERENCES source_span,
    PRIMARY KEY (lc_edition_id, class_code)
);

-- The territory domain, as published on the loss cost grids
CREATE TABLE territory (
    lc_edition_id BIGINT NOT NULL REFERENCES lc_edition,
    territory     CHAR(3) NOT NULL,
    PRIMARY KEY (lc_edition_id, territory)
);
```

### Territory definitions — sourced from the **Rules** notices

The ZIP→territory mapping lives on the Territory Pages (`CG-T-n`) of the Rules notice, not the
loss cost notice, so it is keyed on `manual_edition` and not on `lc_edition`. Three resolution
schemes exist and they are not variants of one shape, so the scheme is an explicit column and
the two mapping tables are separate:

```sql
CREATE TYPE territory_scheme AS ENUM (
    'ENTIRE_STATE',   -- 20 jurisdictions: CG-T-1 only, "ENTIRE STATE ... 001"
    'ZIP_TABLE',      -- 27 jurisdictions: CG-T-2..n, "ZIP Codes/Territories In Numerical Order"
    'COUNTY_CITY'     -- CA, FL, NY, TX: county definitions + List Of Important Cities And Towns
);

CREATE TABLE territory_definition_set (
    edition_id     BIGINT PRIMARY KEY REFERENCES manual_edition,  -- jurisdiction-scoped RULES notice
    scheme         territory_scheme NOT NULL,
    default_territory CHAR(3) NOT NULL DEFAULT '999',  -- sublines 335, 336, 350
    span_id        BIGINT NOT NULL REFERENCES source_span
);

CREATE TABLE territory_zip (                -- scheme = 'ZIP_TABLE'
    edition_id  BIGINT NOT NULL REFERENCES territory_definition_set,
    zip_code    CHAR(5) NOT NULL,
    usps_name   TEXT,
    territory   CHAR(3) NOT NULL,
    span_id     BIGINT NOT NULL REFERENCES source_span,
    PRIMARY KEY (edition_id, zip_code)
);

CREATE TABLE territory_place (              -- scheme = 'COUNTY_CITY'
    edition_id  BIGINT NOT NULL REFERENCES territory_definition_set,
    county      TEXT NOT NULL,
    place_name  TEXT,                       -- NULL = the whole county maps to this territory
    territory   CHAR(3) NOT NULL,
    span_id     BIGINT NOT NULL REFERENCES source_span,
    PRIMARY KEY (edition_id, county, COALESCE(place_name,''))
);
```

**Which sublines consume it.** `CG-T-1` states this explicitly and it must not be inferred:
territory applies to **Premises and Operations (334)** and **Liquor Liability (332)**;
OCP/Railroad Protective (335), Pollution (350) and Products/Completed Operations (336) are
always `999`. Note that the 332 half is visible **only** here — there are no liquor loss cost
pages to corroborate it.

**Why `territory_place` is not `territory_zip` with a different key.** A ZIP is an exact,
always-supplied key. `(county, place_name)` is neither: the place lists are 1996–2008 vintage,
a risk address may not name a listed place, and the county must be derived. The resolver for
`COUNTY_CITY` must therefore have an explicit **unmatched → referral** path, which the
`ZIP_TABLE` resolver does not need. Modelling both as one table invites a silent fuzzy match.

Volumes across the latest notice per jurisdiction: **23,719** `territory_zip` rows,
**432** `territory_place` rows.

### Countrywide-valued rate tables

Two published tables are identical in every jurisdiction that carries them (§13.10). Store them
**once**, countrywide-scoped, with an availability join — not 51 copies, which would drift on
the next revision:

```sql
CREATE TABLE cw_rate_table (                -- Unmanned Aircraft (370), OCP/PP (335)
    cw_rate_table_id BIGSERIAL PRIMARY KEY,
    table_key    TEXT NOT NULL,             -- 'UAV_370' | 'OCP_PP_335'
    edition_id   BIGINT NOT NULL REFERENCES manual_edition,
    row_key      TEXT NOT NULL,             -- '1 lb. or less' | class code '16291'
    col_key      TEXT NOT NULL,             -- 'CG 24 50 BI/PD' | 'ALL_TERRITORIES'
    amount       NUMERIC(12,4),             -- NULL when refer-to-company
    refer_to_company BOOLEAN NOT NULL DEFAULT FALSE,
    is_flat_charge BOOLEAN NOT NULL,        -- TRUE for UAV: a dollar amount, NOT a rate
    span_id      BIGINT NOT NULL REFERENCES source_span
);

CREATE TABLE cw_rate_availability (         -- which jurisdictions publish it, per edition
    cw_rate_table_id BIGINT NOT NULL REFERENCES cw_rate_table,
    lc_edition_id    BIGINT NOT NULL REFERENCES lc_edition,
    PRIMARY KEY (cw_rate_table_id, lc_edition_id)
);
```

`is_flat_charge` is load-bearing: the Unmanned Aircraft amounts are **premiums**, not rates,
and multiplying them by an exposure count is a defect the type system should prevent.

### Two corrections this section forces elsewhere

**`classification.has_prodcompops` (§6.5) must move.** It is declared on the countrywide
`classification` table, but the `-` marker that defines it is printed **per jurisdiction** on
the state loss cost page. Replace the column with a view over `loss_cost`:

```sql
CREATE VIEW class_prodcompops_available AS
SELECT lc_edition_id, class_code,
       (disposition <> 'NOT_OFFERED') AS has_prodcompops
FROM   loss_cost
WHERE  subline_code = '336';
```

The Rule 48.F.1 exclusion for class codes `60000`–`69999` remains countrywide and stays where
it is; only the `(−)` half moves.

**`state_variable` gains three rate-layer entries:**

| `var_key` | Unit | Variants | Coverage |
|---|---|---|---|
| `TERRITORY.COUNT` | INT | — | 51/51 (1–20; 20 jurisdictions have exactly 1) |
| `TERRITORY.SCHEME` | — | `ENTIRE_STATE` (20) · `ZIP_TABLE` (27) · `COUNTY_CITY` (4) | 51/51 |
| `LC.VINTAGE` | — | `PRE_2027` (15) · `V2027` (36) | 51/51 |
| `OCP.RATE_SOURCE` | — | `LOSS_COST` (15) · `ELP_ONLY` (36) | 51/51 |

`ELP.REFERENCED` in the §6.7 registry is recorded as covering 27 of 51 jurisdictions, on the
basis of Rules-page references. The ELP Supplement is in fact present in **51/51**; that
variable now records whether a jurisdiction's *rules* cite it, not whether ELPs exist.
