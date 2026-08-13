# 03 — Rating Plan per Subline and Coverage

> **Reconciliation note, 2026-08-11.** This document was derived from the filed manual PDFs and **before any subline
> was derived end to end**. The per-subline gates have since superseded or sharpened some claims
> here — see [`../gates/RECONCILIATION.md`](../gates/RECONCILIATION.md) (items R3, R4). The text below is
> left as the record of what this derivation found on its own; that independence is what makes
> agreement between the two derivations evidence.

Every coverage the manual rates, with its premium algorithm, exposure base, classification
source, limit mechanics, and where the state layer intervenes.

> **Companion document:** this file is the *plan* — one row per coverage. The **ordered,
> step-by-step algorithm** for each coverage, with the paragraph-level exceptions and the
> endorsement treatment, is in **[`11-RATING-ARCHITECTURE.md`](11-RATING-ARCHITECTURE.md)**.
> Read that for implementation; read this for scope.

**Rule numbers below use the CW 2027 edition** (`GL-MU-2027-RU-001-C.pdf`). See
`A2-CW-RULE-CATALOG.md` for the 2022/2023 equivalents.

---

## 3.0 Reading the table

Each coverage is characterised on six axes the engine must implement:

| Axis | Meaning |
|---|---|
| **Rating mode** | `ALGORITHMIC` (manual gives a closed-form procedure) vs `REFER_TO_COMPANY` (manual explicitly declines to rate) |
| **Exposure base** | Which of the eight Rule 24 bases, or a coverage-specific base |
| **Class source** | CW Classification Table vs a coverage-specific class list |
| **ILF source** | Which state Rule 56.B table applies |
| **Deductible** | Whether Rule 15 applies |
| **State surface** | How many of 51 jurisdictions deviate the governing rule |

**The `REFER_TO_COMPANY` distinction is the single most important scoping decision in the
build.** For several sublines the manual does not compute a premium at all — it hands the
risk to the carrier. Those coverages need a *referral workflow and an override input*, not a
rating formula. Building a formula for them would be inventing rating content the documents
do not contain.

---

## 3.1 Master coverage table

> **Rate-source column added at Step 7.** The `Rating mode` column describes what the *rules*
> prescribe. Whether a published loss cost actually exists to feed it is a separate question,
> answered by the loss cost corpus (`13-LOSS-COSTS-AND-ELP.md`) and summarised in §3.1.1. For
> three coverages the two disagree.

| # | Coverage | Subline | Rule | Rating mode | Exposure base | ILF table | State deviation (of 51) |
|---|---|---|---|---|---|---|---|
| 1 | **Premises-Operations (CGL)** | 334 | 21, 23, 24 | ALGORITHMIC | Rule 24 (per class) | 56.B.1–3 (Tables 1–3) | Rule 24: **51**; Rule 23: 2 |
| 2 | **Products/Completed Operations (CGL)** | 336 | 21, 23, 48 | ALGORITHMIC | Rule 24.D/E/F | 56.B.4–6 (Tables A–C) | Rule 48: **49** |
| 3 | **Liquor Liability** | 332 | 45 | ALGORITHMIC | Rule 45.G class/base | State Liquor table where present | Rule 45: **51** |
| 4 | **Owners & Contractors Protective** | 335 | 46 | ALGORITHMIC | Total Cost per $1,000 | Rule 46.F | Rule 46: **48** |
| 5 | **Principals Protective** | 335 | 46.G (CG 28 07) | ALGORITHMIC | Total Cost per $1,000 | Rule 46.F | Rule 46: **48** |
| 6 | **Railroad Protective** | 335 | 49 | ALGORITHMIC | **Total Cost** (Rule 24.F) | 56.B.7 | Rule 49: **49** |
| 7 | **Product Withdrawal** | 365 | 44 | ALGORITHMIC (factor-derived) | Prod/CompOps base | Derived via Prod/CompOps ILTA | Rule 44: **48** |
| 8 | **Loss Of Electronic Data (CG 04 37 / CG 04 71)** | — | 40 | ALGORITHMIC | Same as Prem-Ops / Prod-CompOps | Occurrence limit = LoED limit | Rule 40: not deviated as "40" |
| 9 | **Cyber Incident Liability** | — | 40 | Hazard-grade driven | Rule 40.G hazard grades | — | — |
| 10 | **Electronic Data Liability (standalone)** | 325 | 42 | **REFER_TO_COMPANY** | 92900/92901/92909 | — | Rule 42: **47** |
| 11 | **Employee Benefits Liability** | 325 | 43 | **REFER_TO_COMPANY** | Class 92105, Number of Employees | — | Rule 43: 9 |
| 12 | **Pollution Liability** | 350 | 47 | **REFER_TO_COMPANY** | Rule 47.F classes | — | Rule 47: **48** |
| 13 | **Underground Storage Tank** | 350 | 53 | **REFER_TO_COMPANY** | **Each insured tank** | — | Rule 53: **48** |
| 14 | **Unmanned Aircraft** | 370 | 37 | ALGORITHMIC (all inputs refer-to-company) | **Each unmanned aircraft** | — | Rule 37: 4 |
| 15 | **Abuse Or Molestation** | — | 41 | **REFER_TO_COMPANY** | — | — | Rule 41: 19 |
| 16 | **Terrorism (certified acts)** | — | 55 | External supplement | — | — | Rule 55: 7 + A-rule in 48 |
| 17 | **Stop Gap — Employers Liability** | — | state A-rule | State-only | — | — | 5 (ND, OH, PR, WA, WY) |

### 3.1.1 Where each coverage's rate actually comes from

| Coverage | Subline | Published loss cost | ELP | Effective rate source |
|---|---|---|---|---|
| Premises-Operations | 334 | **51/51**, by class × territory | 51/51 | Loss cost; ELP on `(a)` |
| Products/Completed Operations | 336 | **51/51**, by class, statewide territory `999` | 51/51 | Loss cost; ELP on `(a)`; `Incl.` means already in 334 |
| OCP / Principals Protective | 335 | **15/51** — withdrawn during the 2027 filing | 51/51 (Table 5.C) | **Both paths required**, chosen per edition |
| Railroad Protective | 335 | **0/51** | 51/51 (Table 5.E) | ELP only. `40014` = 150% of class `16292`; `40013` banded on trains/day at **$100/300** |
| Liquor Liability | 332 | **0/51** | 51/51 (Table 5.D) | **ELP only** — despite Rule 45.I specifying a nine-step algorithm around a basic limits rate |
| Unmanned Aircraft | 370 | **51/51**, identical countrywide | — | **Flat dollar charges, not rates** — no exposure multiplication |
| Product Withdrawal, LoED, Cyber | 365 / — | — | — | Derived from a host subline (A3); unchanged |
| EDL, EBL, Pollution, UST, Abuse | various | — | — | Refer-to-company by rule (A5); unchanged |

**Three corrections to the table above.** Liquor Liability and Railroad Protective are marked
`ALGORITHMIC` because Rules 45 and 49 give ordered step lists — and they do. But neither has a
published basic-limits loss cost in any jurisdiction, so in practice both rate off ELPs or
refer to company. OCP is `ALGORITHMIC` and remains so, but its operand source changes
mid-corpus. See `11-RATING-ARCHITECTURE.md` §11.11.

---

## 3.2 Coverage detail

### 3.2.1 Premises-Operations (Subline 334) — the primary path

Rule 21 A–I (see `02-CW-BASE-RULEBOOK.md` §2.2). Notable mechanics:

- Classification drives **both** the exposure base and the ILTA.
- Basic limits `$100K` occurrence / `$200K` aggregate.
- ILF from the state Rule 56.B Premises/Operations table selected by the **digit** of the
  class's ILTA code (`1`, `2`, `3`).
- Medical-payments increase folds into the ILF: `ILF' = medpay_factor + ILF − 1`.
- Deductible discount applies to the **basic limits rate**, before ILF (Rule 15.D.4).
- Elevator/escalator inspection charge (CW 2022 Rule 51) is an additive premium under
  step G — note it is **absent from the CW 2027 rule list**, a genuine edition difference.

### 3.2.2 Products/Completed Operations (Subline 336)

Rule 48.I. Differs from Prem-Ops in three ways:

1. Rates come from the Prod/CompOps column of the state loss cost pages — and, unlike
   Prem-Ops, always from the **statewide territory `999`**, in all 51 jurisdictions.
2. **Claims-made adjustment is explicit** — Rule 48.D.6 multipliers, Table 48.D.6.
3. Classification exclusions: *"Classifications that indicate a (−) on the state loss cost
   page for products/completed operations, or any classification for Codes 60000–69999, do
   not apply"* (Rule 48.F.1). Building/Premises classes have **no** products exposure.
   The `(−)` marker is now directly readable: it occupies **18.6%** of all loss cost grid
   cells (`13-LOSS-COSTS-AND-ELP.md` §13.4).

ILF from state Rule 56.B Products/Completed-Operations table, selected by the **letter** of
the ILTA code (`A`, `B`, `C`).

### 3.2.3 Liquor Liability (Subline 332)

Rule 45.I mirrors Rule 21 (classify → base → basic rate → coverage adj → ILF → × exposure →
+ other → total). Two state-specific inputs:

- **Liquor Liability Numerical Grade** — Rule 45.H defines the scale (0 = no cause of action
  against the vendor; 1–9 = moderate; 10 = strict liability) and states *"Refer to the state
  exceptions for the applicable grade."* All 51 jurisdictions supply one; observed range in
  current notices is **0–8**. Full table: `05-LOOKUP-TABLES.md` §5.2.
- **Liquor ILF table** — supplied as a separate Rule 56.B table in only **IL, MN, UT**.
  Elsewhere the liquor limit factors are not in the Rules exception pages. Flag as a GAP.

Rule 45 is deviated by **all 51** jurisdictions — the highest-touch subline in the manual.

### 3.2.4 Owners & Contractors Protective / Principals Protective (Subline 335)

Rule 46.J is an **8-step** variant of Rule 21 with a significant omission: **there is no
"determine the premium base" step** and **no deductible step**. Classes are OCP-specific
(e.g. `16291` Construction Operations — Contractor (Not Railroads); `91181` Construction
Operations — Federal, State Or Local Housing Authorities), all on **Total Cost per $1,000**.

Standalone Coverage Part — not an endorsement to the CGL.

**Rule 46 carries three sub-coverages, not two.** Alongside OCP (`CG 00 09`), paragraphs G and
H each *"convert"* the OCP coverage form into a different coverage form:

| Para | Sub-coverage | Form | Class |
|---|---|---|---|
| G | Principals Protective Liability | `CG 28 07` | `27113` |
| H | **Construction Project Management Protective Liability** | `CG 31 15` | `93040` |

These are **coverage-part transforms**, not additive endorsements — see
`11-RATING-ARCHITECTURE.md` §11.4.1.

### 3.2.5 Railroad Protective (Subline 335)

Rule 49. Basis of premium is **Total Cost** (Rule 24.F). Four classes, all Total Cost per
$1,000:

| Code | Classification |
|---|---|
| 40011 | Railroad NOC construction operations — performed **for railroads** |
| 40012 | Railroad NOC construction operations — performed **for interests other than railroads** |
| 40013 | State or federal highway projects |
| 40014 | Operations involving no work within 50 feet of railroad tracks / no exposure to actual train hazards |

Has its **own dedicated state ILF table** — Rule 56.B.7 — present in all 51 jurisdictions.

### 3.2.6 Product Withdrawal (Subline 365)

Rule 44.A.5.a. Coverage A (Product Withdrawal Expenses) and Coverage B (Products Withdrawal
Liability) are rated **separately**. The distinguishing mechanic: the premium is **derived
from the products/completed-operations basic rate** via a *Product Withdrawal Factor* keyed to
the Prod/CompOps ILTA (Table 44.A.5.a.(5)). It is a factor-on-another-subline's-rate coverage,
not an independently rated one — the engine must compute Prod/CompOps first.

### 3.2.7 Loss Of Electronic Data & Cyber Incident Liability (Rule 40, CW 2027)

Rule 40 is **new in the 2027 edition** (absent from CW 2022/2023). Two mechanics:

- **Loss Of Electronic Data (CG 04 37 / CG 04 71):** fully algorithmic — same classes and
  premium base as Prem-Ops/Prod-CompOps; ILF selected at *"the Each Occurrence Limit equal to
  the Loss Of Electronic Data Limit indicated in the Schedule."*
- **Cyber Incident Liability:** driven by **hazard grade classification assignments**
  (Rule 40.F for LoED, 40.G for Cyber), spanning manual pages CG-60 – CG-69. This is a
  substantial CW lookup table — class code → hazard grade — that must be ingested.

### 3.2.8 Refer-to-company coverages

The manual states these explicitly. Quoted verbatim:

| Coverage | Manual text |
|---|---|
| Electronic Data Liability (Rule 42.F) | *"Premium Determination — Refer to company."* |
| Employee Benefits Liability (Rule 43.D) | *"Premium Determination — Refer to company."* |
| Pollution Liability (Rule 47.G) | *"Premium Determination — Refer to company."* |
| UST (Rule 53.E) | *"Refer to company for determination of Policy Limits, Defense Expense Amount, rates and rating procedure."* |
| Abuse Or Molestation (Rule 41.C) | *"Premium Determination — Refer to company for rating."* |

They still need full **structural** implementation — classes, bases, retroactive dates,
extended reporting periods, endorsement eligibility — because those drive policy issuance and
statistical coding even when the premium is carrier-supplied.

Classification/base detail that *is* specified:

- **Electronic Data Liability (Rule 42.G):** `92900` Payroll basis · `92901` Gross Sales
  basis · `92909` All Other basis.
- **Employee Benefits Liability (Rule 43.E):** class `92105`, base **Number of Employees**.
- **UST (Rule 53.F):** base is **each insured tank**; the class code is *composed* —
  first digit `2` (= UST), second digit contents (`1` gasoline all grades, `2` oil incl.
  kerosene/diesel/waste, `3` other), third digit construction, further digits age and
  protective devices. This is a **constructed code**, not a lookup — the engine needs a
  code-builder, not a table.

### 3.2.9 Unmanned Aircraft (Subline 370, Rule 37)

Algorithmic in shape but the manual states *"All applicable loss costs and modifiers
referenced in Paragraphs C.2.b. and C.2.d. and Tables D., E. and F. must be referred to
company before using."* Basis of premium: **each unmanned aircraft**; non-owned aircraft
operated by other parties → refer to company. Rate selection keys on the endorsement option
and the aircraft's **Maximum Take-off Weight**. Three modifier families: Ownership &
Operation (D), Usage (E), Primary Place Of Operation (F). Coverage A and Coverage B are rated
separately.

### 3.2.10 Terrorism (Rule 55) and state A-rules

The countrywide Rule 55 covers TRIA endorsement options and premium determination for
certified acts (CG-120 – CG-131). But **48 of 51** jurisdictions carry a state A-rule titled
*"Terrorism Premium Determination"* whose entire body is: *"Refer to the Terrorism Supplement
to the CLM."* The Terrorism Supplement is **not in this corpus** — see
`09-GAPS-AND-OPEN-QUESTIONS.md`.

---

## 3.3 Coverage-to-state-deviation heat summary

Ranked by how many jurisdictions deviate the governing rule (of 51):

| Rule | Coverage / topic | Jurisdictions |
|---|---|---|
| 24 | Bases Of Premium | **51** |
| 45 | Liquor Liability | **51** |
| 56 | Increased Limits Tables | **51** |
| 22 | Mandatory Endorsements *(2027)* / CGL Description *(2022)* | 49 |
| 48 | Products/Completed Operations | 49 |
| 49 | Railroad Protective | 49 |
| 44 | Product Withdrawal | 48 |
| 46 | OCP / Principals Protective | 48 |
| 47 | Pollution Liability | 48 |
| 53 | Underground Storage Tank | 48 |
| 42 | Electronic Data Liability | 47 |
| 34 | Special Rule For Individual Risk Situations | 37 |
| 36 | Additional Optional Endorsements | 35 |
| 2 | Referrals To Company | 27 |
| 11 | Policy Cancellations | 21 |
| 41 | Abuse Or Molestation | 19 |

Full matrix including all 33 deviated rules: `04-STATE-DEVIATIONS.md` §4.1.
