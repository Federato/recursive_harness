# 11 — Full Rating Architecture

> **Reconciliation note, 2026-08-11.** This document was derived from the filed manual PDFs and **before any subline
> was derived end to end**. The per-subline gates have since superseded or sharpened some claims
> here — see [`../gates/RECONCILIATION.md`](../gates/RECONCILIATION.md) (items R3, R4, R5). The text below is
> left as the record of what this derivation found on its own; that independence is what makes
> agreement between the two derivations evidence.

The complete calculation architecture for every subline, coverage, sub-coverage and
endorsement in the corpus: the ordered algorithm, the inputs each step consumes, the
exceptions that suspend the general rules, and the point at which the state layer intervenes.

**Primary source:** `GL-MU-2027-RU-001-C.pdf` — CW 2027, "1st Edition 4-27", filing
`GL-2024-RRU24`. Paragraph citations below are to that edition. For the 2022/2023 numbering
see `A2-CW-RULE-CATALOG.md`; for how an engine holds both at once see
`12-VERSIONING-AND-EDITIONS.md`.

**Evidence rule:** every step, factor and exception below is quoted or condensed from the
manual text. Where the manual declines to specify, this document says so rather than
supplying a plausible formula. Nothing here is inferred from market practice.

---

## 11.1 The canonical coverage-rule anatomy

Every non-CGL coverage rule in Section III is written to the same skeleton. This is the single
most useful structural fact in the corpus, because it means **one parser and one schema shape
serve every coverage**, and a missing paragraph is itself a meaningful signal.

| Para | Heading | What it contributes to the engine |
|---|---|---|
| A | Description Of Coverage | Coverage part identity; the available coverage form(s) (`CG 00 xx`) |
| B | Exceptions To Section I General Rules | **Which general rules are switched off for this part** |
| C | Mandatory Endorsements | Forms auto-attached; loss cost already contemplates them |
| D | Optional Endorsements — Refer To Company For Rating | Named, described, *not* priced |
| E | Rates / Company Rates | Where the rate comes from, or "refer to company" |
| F | Increased Limits / Classifications | ILF source, or the class list |
| G–I | Coverage-specific paragraphs | Sub-coverage endorsements, grades, classifications |
| — | **Premium Determination** | The ordered algorithm |
| — | Deductibles | Whether Rule 15 applies, and which discount table |
| — | Special Rules Applicable To The Claims-made Coverage Form | Retroactive date, ERP |

Actual paragraph letters vary per rule; the *sequence* does not. Verified letters:

| Rule | Coverage | Rates | ILF | Classes | Premium Determination | Deductibles | Claims-made |
|---|---|---|---|---|---|---|---|
| 45 | Liquor Liability | E | F | G | **I** | J | K |
| 46 | OCP / Principals Protective | E | F | I | **J** | *(none)* | — |
| 47 | Pollution Liability | E | — | F | **G** — refer to company | — | H (ERP) |
| 48 | Products/Completed Ops | D | — | F | **I** | via Rule 15 | G |
| 49 | Railroad Protective | E | E.2 | G | **H** | *(none)* | — |
| 53 | Underground Storage Tank | E | E | F | **E** — refer to company | — | G (retro date) |
| 42 | Electronic Data Liability | E | — | G | **F** — refer to company | — | — |
| 43 | Employee Benefits Liability | C | — | E | **D** — refer to company | — | F/G |
| 41 | Abuse Or Molestation | — | — | — | **C** — refer to company | — | D |

> **Engineering consequence.** `coverage_rule` is a uniform record with nullable paragraph
> slots. The nulls carry meaning: Rule 46 and Rule 49 have **no deductible paragraph at all**,
> so a deductible on an OCP or Railroad Protective policy is not a discount — it is
> unsupported input and must be rejected at validation, not silently ignored.

### Paragraph B is a rule-suspension list, not prose

Paragraph B tells the engine which Section I general rules **do not run** for this part.
Verbatim examples:

- **Rule 45.B (Liquor):** *"Paragraphs A., B., C., D. and F. under Rule 15. Deductibles do not
  apply. Refer to Paragraph J."* — the CGL deductible machinery is replaced wholesale by
  Rule 45.J.
- **Rule 44.A.4 (Product Withdrawal):** *"The Calculation Of Premium Endorsement IL 00 03
  referenced under Rule 5.B.3. does not apply to this Coverage Part. Use Calculation Of
  Premium Endorsement CG 31 98 instead."* and *"Rule 16. Additional Interests does not
  apply."* — additional insureds are **not available** on Product Withdrawal.

The engine must model this as an explicit `suspends[]` edge from a coverage part to general
rules, evaluated *before* the pipeline runs. Treating Section I as unconditionally applicable
is a correctness bug that produces a plausible, wrong premium.

---

## 11.2 The five algorithm archetypes

Every rated coverage in the corpus is one of five shapes. Implement five executors, not
seventeen.

| # | Archetype | Coverages | Distinguishing mechanic |
|---|---|---|---|
| **A1** | Full 9-step | Prem-Ops (21), Prod-CompOps (48), Liquor (45) | classify → base → rate → coverage adj → ILF+deductible → × exposure → + other → total → min premium |
| **A2** | 8-step, no premium-base step, no deductible | OCP / Principals Protective (46), Railroad Protective (49) | exposure base is fixed by the coverage, not by the class |
| **A3** | Factor-on-another-subline | Product Withdrawal (44), LoED / Cyber (40) | computes a host subline's rate first, then applies a published factor |
| **A4** | Modifier chain | Unmanned Aircraft (37) | rate × three independent categorical modifiers, then ILF |
| **A5** | Refer-to-company | EDL (42), EBL (43), Pollution (47), UST (53), Abuse (41) | structure fully specified, premium explicitly not |

---

## 11.3 Archetype A1 — the full nine-step algorithm

### 11.3.1 Premises-Operations — CW Rule 21 (Subline 334)

Verbatim step list, *"The premium for a risk is calculated as follows"*:

| Step | Rule 21 | Operation | Consumes |
|---|---|---|---|
| 1 | A | Determine the applicable classification(s) | Classification Table (Rule 25) |
| 2 | B | Determine the premium base — *"The same premium base applies to both Premises-Operations and Products-Completed Operations"* | Rule 24; class record |
| 3 | C | Select the basic limits rate(s) from the state company rates, **for both** Prem-Ops and Prod-CompOps | state loss cost pages — `13-LOSS-COSTS-AND-ELP.md` §13.6 |
| 4 | D | Adjust the basic limits rate(s) for any coverage change **other than deductibles** | Rule 23.D; claims-made multipliers |
| 5 | E | Adjust by increased limits factors and any other rate modification(s); **adjust for deductible per Rule 15** | state Rule 56.B tables; Rule 15 |
| 6 | F | Multiply units of exposure × adjusted rate, per classification | exposure input |
| 7 | G | Determine any other additional premiums | endorsement charges, Rule 36 |
| 8 | H | Total = step F + step G | — |
| 9 | I | Use H **or the policywriting minimum premium, whichever is greater** | minimum premium |

Three non-obvious constraints, each a defect if missed:

1. **Two parallel rate streams, one exposure count.** Steps 3–5 run twice (Prem-Ops and
   Prod-CompOps) against the *same* base and *same* exposure units from step 2.
2. **The deductible modifies the rate, not the premium** — Rule 15.D.4: *"Deductible discount
   factors are applicable only to the company's basic limits rates and minimum premiums."*
   Applying it to the extended premium is wrong by the amount of the ILF.
3. **Minimum premium is terminal and policy-level** — it is compared after additional
   premiums (step G), not per classification.

**Medical payments folds into the ILF, it does not multiply it** (Rule 23.D.2.c):

```
ILF' = medpay_factor + ILF − 1          e.g. 1.020 + 1.95 − 1 = 1.97   (manual's own example)
```

**Split limits** (Rule 23.D.5): derive BI and PD factors separately, then apply the
countrywide weights — `factor = w_BI·ILF_BI + w_PD·ILF_PD + constant`:

| Class range | w(BI) | w(PD) | Constant |
|---|---|---|---|
| 10000–69999 | 0.97 | 0.11 | −0.03 |
| 90000–99999 (Contracting Or Servicing) | 0.83 | 0.19 | +0.03 |

### 11.3.2 Products/Completed Operations — Rule 48.I (Subline 336)

Same nine steps, with three substitutions:

| Step | Difference from Rule 21 |
|---|---|
| 3 | Rate comes from the **Products/Completed Operations** column of the state loss cost pages, always at **statewide territory `999`** — territory applies to Prem-Ops only |
| 4 | *"Adjust … to reflect claims-made [or] any other coverage change … Claims-made adjustment shall be applied in accordance with Rule 48.D.6. using claims-made multipliers found in Table 48.D.6."* — claims-made is **explicit** here, unlike Rule 21 |
| 9 | *"The Products/Completed Operations premium is the greater of the premium developed in I.8. or the policywriting minimum premium"* — the minimum applies to **this subline's** premium |

**Classification exclusions (Rule 48.F.1)** — a hard eligibility gate, not a rate of zero:
*"Classifications that indicate a (−) on the state loss cost page for products/completed
operations, or any classification for Codes 60000–69999, do not apply."* Building/Premises
classes have no products exposure at all.

ILF selection uses the **letter** of the ILTA code (Tables A–C).

### 11.3.3 Liquor Liability — Rule 45.I (Subline 332)

Nine steps mirroring Rule 21, with the deductible clause reading *"Adjust for coverage written
on a deductible basis"* pointing at Rule 45.J rather than Rule 15.

Coverage-specific inputs:

- **Rule 45.G — Classifications And Premium Bases.** A liquor-specific class list
  (e.g. `50941` All Other — Bring Your Own Alcohol), not the CGL Classification Table.
- **Rule 45.H — Liquor Liability Grades.** *"Liquor liability grades are assigned based upon…"*
  the scale runs 0 (no cause of action against the vendor) through 10 (strict liability); the
  manual states *"Refer to the state exceptions for the applicable grade."* All 51
  jurisdictions supply one; observed range in current notices is **0–8**
  (`05-LOOKUP-TABLES.md` §5.2).
- **Rule 45.J.3 — Deductibles.** *"Deductible discount factors applicable to all risks written
  on this basis must be referred to the company before using. Use Products/Completed
  Operations Deductible Discount Factors — Bodily Injury and Property Damage found in Rule 15.,
  Table 15.E.6."* So liquor deductibles are **refer-to-company but table-anchored** — the
  engine needs the referral flag *and* the Prod/CompOps table binding.
- **Rule 45.J.4** — deductible is effected by endorsement `CG 03 05`.
- **Rule 45.K** — retroactive date and ERP rules for the claims-made form `CG 00 34`.

A grade of `0` is also an **eligibility switch elsewhere**: Rule 36 permits endorsement
`CG 24 08` when *"the indicated liquor liability classification in Rule 45.H. applicable to the
Named Insured's operations is assigned a '0' hazard grade"* or the state grade is `0`. The
liquor grade is therefore consumed by two different subsystems — rating and form eligibility.

Rule 45 is deviated by **all 51 jurisdictions**.

---

## 11.4 Archetype A2 — eight steps, no premium-base step

### 11.4.1 Owners & Contractors Protective — Rule 46.J (Subline 335)

| Step | Rule 46.J | Operation |
|---|---|---|
| 1 | 1 | Determine the applicable classification(s) |
| 2 | 2 | Select the basic limits rate(s) |
| 3 | 3 | Adjust to reflect any coverage change |
| 4 | 4 | Adjust by ILFs **in accordance with Paragraph F.** and any other rate modification(s) |
| 5 | 5 | Multiply units of exposure × adjusted rate |
| 6 | 6 | Determine any other additional premiums |
| 7 | 7 | Total = step 5 + step 6 |
| 8 | 8 | Use step 7 or the policywriting minimum premium, whichever is greater |

**Two paragraphs are absent versus Rule 21: premium base and deductible.** The base is fixed
by the coverage (Total Cost per $1,000), so there is no per-class base lookup; and there is no
deductible mechanism at all. Rule 46.K defers individual-risk situations to Rule 34.

**Rule 46 carries three distinct sub-coverages, not two** — a correction to
`03-SUBLINE-COVERAGE-PLAN.md` §3.2.4:

| Para | Sub-coverage | Form | Classification |
|---|---|---|---|
| A | Owners And Contractors Protective Liability | `CG 00 09` | OCP class list (Rule 46.I) |
| G | **Principals Protective Liability** | `CG 28 07` | `27113` Principals Protective Liability Coverages A and B |
| H | **Construction Project Management Protective Liability** | `CG 31 15` | `93040` Construction Project Management |

Both G and H are described as endorsements that *"convert Owners And Contractors Protective
Liability Coverage Form … CG 00 09 into"* a different coverage form. Architecturally they are
**coverage-part transforms**, not additive endorsements: they change which class list and
which coverage identity applies, while reusing the Rule 46.J algorithm. Modelling them as
ordinary optional endorsements would attach them *on top of* OCP and double-count.

### 11.4.2 Railroad Protective — Rule 49.H (Subline 335)

Identical eight-step shape. Basis of premium is **Total Cost** (Rule 49.F → Rule 24.F). ILFs
come from Paragraph E.2, which resolves to the **dedicated state Rule 56.B.7 Railroad
Protective table** — present in all 51 jurisdictions. Four classes (Rule 49.G): `40011`,
`40012`, `40013`, `40014`.

---

## 11.5 Archetype A3 — factor applied to another subline's rate

These coverages have **no rate of their own**. The engine must compute a host subline first,
then scale it. Ordering is therefore a hard dependency, not a preference.

### 11.5.1 Product Withdrawal — Rule 44

Two delivery mechanisms, rated by two nearly-identical procedures:

- **Rule 44.A** — standalone Product Withdrawal Coverage Form `CG 00 66`
- **Rule 44.B** — Limited Product Withdrawal Expense Endorsement `CG 04 36`, attached to a CGL
  or Products/Completed Operations Coverage Part

Rule 44.A.5.a — Coverage A (Product Withdrawal Expenses) and Coverage B (Products Withdrawal
Liability) are calculated **separately**:

| Step | Operation |
|---|---|
| (1) | Determine classification(s) — *"Use the same classifications which apply to Premises/Operations and Products/Completed Operations risks"* |
| (2) | Determine the premium base |
| (3) | Select the **products/completed operations** basic limits rate(s) |
| (4) | Adjust for any coverage change other than deductibles |
| (5) | Determine the Prod/CompOps ILTA; **multiply the Prod/CompOps basic limit rate by the Product Withdrawal Factor** (Table 44.A.5.a.(5)) |
| (6) | Select the ILF for the limit shown in the Declarations, on that ILTA |
| (7) | Apply Rule 15 deductible adjustment — *"the deductible applies to each product withdrawal"*, using the **"per occurrence" Prod/CompOps BI+PD combined** discount factors |
| (8) | Multiply the basic limit Product Withdrawal rate by the ILF from (7) |
| (9) | Multiply exposure units × adjusted rate |
| b–e | Combine Coverage A + B → add other additional premiums → total → **greater of total or policywriting minimum premium** |

**Table 44.A.5.a.(5) — Product Withdrawal Factors** (a genuine countrywide table):

| Prod/CompOps ILTA | A | B | C |
|---|---|---|---|
| Product Withdrawal **Expense** Factor | 0.25 | 0.19 | 0.13 |
| Product Withdrawal **Liability** Factor | 0.13 | 0.10 | 0.07 |

Two schedule fields suppress the published rating entirely:

- **44.A.5.a.f — Participation Percentage.** The steps *"assume that the insured is not
  participating in the loss other than any deductible"*. If a Participation Percentage is on
  the Declarations → **refer to company** for the associated discount.
- **44.A.5.a.g — Cut-off Date.** The steps contemplate *no* Cut-off Date. If one is shown →
  **refer to company**.

These are input-conditional referrals: the same coverage is algorithmic or refer-to-company
depending on a Declarations field. The engine needs referral **predicates**, not a static
per-coverage flag.

### 11.5.2 Loss Of Electronic Data and Cyber Incident Liability — Rule 40

**New in the CW 2027 edition** — absent from CW 2022/2023.

Endorsement options (Rule 40.A): `CG 04 25` (Cyber Incident Liability), `CG 04 95` (Cyber +
LoED), `CG 04 37` (LoED), `CG 04 71` (LoED, bodily-injury exception deleted). *"Do not attach
more than one of the endorsements referenced in Paragraph A. to the same policy."* And a
cross-rule interlock: when any of these is attached, **do not attach `CG 21 85`** (Rule 36.C.35).

**Rule 40.B.1 — Loss Of Electronic Data (`CG 04 37` / `CG 04 71`):**

| Step | Operation |
|---|---|
| a–c | Classification, premium base, basic limits rate(s) — same as Prem-Ops / Prod-CompOps |
| d | Select ILF at *"the Each Occurrence Limit **equal to** the Loss Of Electronic Data Limit indicated in the Schedule"*; LoED Limit ≤ policy Each Occurrence Limit. ILFs are Rule 56 → **state exceptions** |
| e | If a **property damage** deductible applies, adjust the ILF using the PD deductible discount factor for that ILTA |
| f | Apply adjusted ILF + other rate modifications to the basic limits rate |
| g | **Multiply by the Loss Of Electronic Data Factor** from Table 40.C (`CG 04 37`) or Table 40.D (`CG 04 71`), **separately per subline**; hazard grade from Table 40.F — *"Classifications not displayed in Table 40.F. are assigned to Hazard Grade 1"* |
| h–i | × exposure units; combine across sublines and classifications |
| j–k | *"Determine the application of any minimum premium. **Refer to company for minimum premium.**"* — premium is the greater of (i) and that referral |

**Rule 40.B.2 — Cyber Incident Liability (`CG 04 25`):** same shape, but the ILF is selected
at the **Cyber Incident Occurrence Limit** and **Cyber Incident Aggregate Limit** from the
endorsement Schedule (each capped by the corresponding policy limit), the deductible step
applies to BI **and** PD, and the factor comes from Table 40.E with hazard grades from
Table 40.G.

**`CG 04 95` (Rule 40.B.2.b) is pure composition** — compute 40.B.2.a, compute 40.B.1, add,
then apply the refer-to-company minimum once to the combined result. Implement it as a
composite, never as a third rate table.

**Published factor tables** (values verified against the layout extraction):

| Hazard Grade | 40.C — LoED `CG 04 37` | 40.D — LoED `CG 04 71` | 40.E — Cyber `CG 04 25` |
|---|---|---|---|
| 1 | 0.0010 | 0.0008 | 0.0010 |
| 2 | 0.0030 | 0.0024 | 0.0040 |
| 3 | 0.0050 | 0.0040 | 0.0070 |
| 4 | 0.0070 | 0.0056 | 0.0100 |

Each table publishes the same value for the Premises/Operations and Products/Completed
Operations columns; they are nonetheless **separate columns** in the manual and must stay
separate in the schema — equality today is data, not structure.

**Tables 40.F and 40.G — hazard grade classification assignments** — are large countrywide
lookups (manual pages `CG-60`–`CG-63` for LoED, `CG-64`–`CG-69` for Cyber) mapping class code →
hazard grade, separately for Prem-Ops and Prod-CompOps. They are printed as multi-column
tables whose rows wrap, and **reliable extraction requires layout-aware parsing with a
per-row assertion** (see `08-INGESTION-SPEC.md`). Values are deliberately **not** transcribed
into this document, because a mis-aligned hazard grade silently changes premium by up to 7×.
The default rule — unlisted classes are Hazard Grade 1 — is stated by the manual and is safe.

---

## 11.6 Archetype A4 — modifier chain (Unmanned Aircraft, Rule 37, Subline 370)

Rule 37.C.2 rates **Coverage A (BI+PD)** and **Coverage B (Personal & Advertising Injury)**
separately, and opens with a blanket gate:

> *"All applicable loss costs and modifiers referenced in Paragraphs C.2.b. and C.2.d. and
> Tables D., E. and F. must be referred to company before using."*

| Step | Rule 37.C.2 | Operation |
|---|---|---|
| a | Basis of premium is **each unmanned aircraft**; non-owned aircraft operated by other parties → refer to company |
| b | Select the basic limit rate by **endorsement option** and the aircraft's **Maximum Take-off Weight** |
| c | Adjust for claims-made or other coverage change — *"Use Premises/Operations All Other claims-made multipliers"* from Rule 23 |
| d | Multiply by **three** modifiers: Ownership & Operation (Table 37.D), Usage (Table 37.E), Primary Place Of Operation (Table 37.F) |
| e | Select the ILF on the Each Occurrence Limit and either the policy General Aggregate or the Unmanned Aircraft Liability Aggregate from the endorsement |

**Tie-break rule, stated identically for all three modifiers:** *"If more than one … category
applies to the unmanned aircraft, assign the category with the highest rating modifier."* This
is a `MAX` selection, not a product — multiplying two applicable categories together is a
plausible and wrong implementation.

Rule 37.C.1: the **Exclusion** options (Paragraph B.1) are refer-to-company, so the same rule
contains both a rated path and an unrated path selected by which endorsement is attached.

Rule 37 also carries a **loss-cost interaction**: when `CG 24 55` is attached alongside classes
`10096`, `10097`, `40128` or `50033`, *"the loss costs applicable to that classification
contemplate coverage provided by the endorsement"* — i.e. no additional charge. Charging for
the endorsement on those classes double-counts.

---

## 11.7 Archetype A5 — refer-to-company coverages

The manual specifies these completely **except** for price. They are not out of scope; they
are out of *rating* scope.

| Coverage | Citation | Manual text | Structure that **is** specified |
|---|---|---|---|
| Electronic Data Liability | Rule 42.F | *"Premium Determination — Refer to company."* | Rule 42.G classes: `92900` Payroll basis · `92901` Gross Sales basis · `92909` All Other basis |
| Employee Benefits Liability | Rule 43.D | *"Premium Determination — Refer to company."* | Rule 43.E: class `92105`, base **Number of Employees**; 43.F retroactive date; 43.G ERP option |
| Pollution Liability | Rule 47.G | *"Premium Determination — Refer to company."* | Rule 47.F classes (statistical); 47.E rates refer to company; 47.H ERP endorsement `CG 28 01` |
| Underground Storage Tank | Rule 53.E | *"Refer to company for determination of Policy Limits, Defense Expense Amount, rates and rating procedure."* | Rule 53.F **constructed class code**; 53.G retroactive date |
| Abuse Or Molestation | Rule 41.C | *"Premium Determination — Refer to company for rating."* | Rule 41.B endorsement options; 41.D claims-made retroactive date / ERP |

**UST's class code is composed, not looked up** (Rule 53.F): first digit `2` = UST; second digit
contents (`1` gasoline all grades, `2` oil incl. kerosene/diesel/waste, `3` other); third digit
construction; further digits age and protective devices. The engine needs a **code builder**
with validation, not a lookup table — and the builder must round-trip (decompose an existing
code back to its attributes) for renewal and statistical reporting.

Every A5 coverage still requires full implementation of: classification, exposure base,
eligibility, mandatory endorsements, retroactive date, extended reporting period, and
statistical coding. Only the premium node is carrier-supplied.

---

## 11.8 Endorsements as first-class rating objects

`A3-ENDORSEMENT-CATALOG.md` inventories **328 distinct forms across 447 (coverage part, form)
placements**. The architectural points:

1. **The catalog key is `(coverage_part, form)`, not `form`.** The same form carries different
   roles in different parts. A single global endorsement table is wrong.

2. **Six roles, three premium behaviours.**

   | Role | Premium behaviour |
   |---|---|
   | `COVERAGE_FORM` | Selects the coverage part; no charge of its own |
   | `MANDATORY_MULTISTATE` | **Already inside the loss cost** — never charged separately |
   | `CONDITIONAL_MANDATORY_MULTISTATE` | Inside the loss cost; *removal or replacement* is refer-to-company |
   | `MANDATORY_CLASSIFICATION_MULTISTATE` | Inside the loss cost **of the specific class**; usable on other risks → refer to company |
   | `STATE_MANDATORY` | Per-jurisdiction; from the state exception pages |
   | `OPTIONAL_RTC` / `ADDITIONAL_OPTIONAL_RTC` / `ADDITIONAL_INSURED` | Named and described; **priced by the carrier** |

   The manual's own language for conditional mandatory forms is precise and worth encoding
   verbatim: *"The applicable loss cost(s) currently contemplate the attachment of these
   endorsements. However, these endorsements may be removed or replaced on a refer to company
   basis."* An endorsement that is *inside* the loss cost creates a **negative** referral when
   removed — a case a naive "endorsement = additive charge" model cannot express.

3. **Attachment constraints are rules, not documentation.** The manual states them as
   imperatives — *"Do not attach more than one of the endorsements referenced in Paragraph
   A.3.j. to the same policy"*, *"When Endorsement CG 04 25, CG 04 95, CG 04 37 or CG 04 71 is
   attached to the policy, do not attach Endorsement CG 21 85"*, *"When Endorsement CG 24 08 is
   attached … do not use Endorsements CG 21 50, CG 21 51 or CG 40 09"*. These are
   `mutually_exclusive` and `forbidden_with` edges in the schema and must be validated before
   rating, not after.

4. **Some endorsements transform the coverage part** (`CG 28 07`, `CG 31 15` under Rule 46) —
   see §11.4.1. Role `COVERAGE_TRANSFORM` is required and is not derivable from the heading;
   it comes from the verb *"converts … into"* in the paragraph body.

5. **Sub-coverage endorsements carry their own limit and their own ILF selection** — LoED
   Limit, Cyber Incident Occurrence/Aggregate Limits, Product Withdrawal Each Withdrawal Limit
   (`CG 31 72`). Each is constrained by a policy-level limit (*"shall be less than or equal
   to"*), which is a validation the engine must enforce, not assume.

---

## 11.9 Cross-cutting mechanics and order of operations

The whole-policy pipeline, in the only order the manual permits:

```
1  Resolve edition            (effective date → CW edition + state notice)   → doc 12
2  Apply rule suspensions     (Paragraph B of each attached coverage part)
3  Validate attachment        (mutually-exclusive / forbidden-with / limit ≤ policy limit)
4  Classify                   (Rule 25, or the coverage-specific class list)
5  Determine premium base     (Rule 24 — skipped for archetype A2)
6  Rate each coverage part    (archetype executor A1–A5)
     5a  host sublines first: Prem-Ops, Prod-CompOps       ← A3 depends on these
     5b  dependent coverages: Product Withdrawal, LoED, Cyber
7  Additional premiums        (Rule 36 endorsements, elevator/escalator in CW 2022)
8  Terrorism                  (Rule 55 → Terrorism Supplement, outside corpus)
9  Policy total, then minimum premium comparison  (Rule 21.I — terminal)
10 Rounding                   (Rule 5 / Rule 56.A.4 interpolation half-up at 2dp)
```

**Interpolation of increased limits factors** (Rule 56.A.4) is defined, not left to the
implementer: take the next-lower and next-higher factor, interpolate, and *"all fractions in
the third decimal place shall be considered as an additional unit in the second decimal
place"* — round half-up at two decimals. Where **neither** bounding limit appears in the
table → refer to company. Some factors are printed in a block flagged *"MUST be referred to
company before using"*, so the table is physically split into usable and referral regions —
the schema must carry a per-cell `referral_required` flag, not a per-table one.

**The ILTA code is composite.** A state assignment of `2B` means Premises/Operations Table 2
*and* Products/Completed Operations Table B. One token, two independent table selections, and
it also drives deductible discount selection (Rule 15.D.2). This decoding is the join of Rule
15.D.2 with the state ILTA pages and is stated nowhere in a single place.

**No countrywide ILF table exists.** Rule 56.B: *"The increased limits tables are displayed in
the state exceptions."* The CW layer cannot rate a policy alone — for **any** jurisdiction.
This is the single most consequential architectural fact in the corpus and is why the resolver
in `07-ENGINE-ARCHITECTURE.md` treats CW + state as one composed rulebook rather than a base
with optional overrides.

---

## 11.10 Where the state layer intervenes, by step

Deviation is not uniformly distributed across the algorithm. Mapping the 51-jurisdiction
deviation counts (`04-STATE-DEVIATIONS.md`) onto the pipeline above:

| Pipeline step | Governing rule | Jurisdictions deviating |
|---|---|---|
| Classify | 25, 26, 27, 29, 31, 32 | **0** |
| Determine premium base | 24 | **51** |
| Select basic limits rate | state loss cost pages | n/a — state-sourced by construction, in a **separate notice stream** (`13-LOSS-COSTS-AND-ELP.md`) |
| Coverage adjustment | 23 | 2 |
| Increased limits | 56 | **51** |
| Liquor path | 45 | **51** |
| Prod/CompOps path | 48 | 49 |
| Mandatory endorsements | 22 *(2027)* | 49 |
| Optional endorsements | 36 | 35 |
| Referrals | 2 | 27 |
| Terrorism | 55 + state A-rule | 7 + 48 A-rules |

**The classification apparatus is countrywide and untouched; the money is deviated.** That
asymmetry should drive build sequencing: classification can be built once against CW and
trusted, while every limits/coverage path needs the state overlay before it produces a number.

**State A-rules** — rules that exist only in a state notice with no countrywide counterpart —
are a separate mechanism from exceptions to CW rules. The two largest families:

- *"Terrorism Premium Determination"* — 48 jurisdictions, body: *"Refer to the Terrorism
  Supplement to the CLM."*
- **Stop Gap — Employers Liability** — ND, OH, PR, WA, WY (monopolistic workers-compensation
  jurisdictions). No countrywide rule exists; the coverage is state-only.

An A-rule cannot be modelled as an override of a CW rule, because there is nothing to
override. The schema needs `rule_origin ∈ {COUNTRYWIDE, STATE_EXCEPTION, STATE_ONLY}`.

---

## 11.11 What this architecture still cannot price

> **Substantially revised at Step 7.** The rate pages have arrived
> (`13-LOSS-COSTS-AND-ELP.md`). Step 3 of every A1/A2 algorithm now has an operand.

| Input | Status | Consequence |
|---|---|---|
| State rates / ISO loss costs | ✅ **Supplied**, all 51 jurisdictions, sublines 334/336/335/370 | Step 3 resolves. It is a five-way decision, not a lookup — see `07` §7.3 STEP C |
| ELP Supplement | ✅ **Supplied**, 51/51, ~404 classes each | The `(a)` branch of step 3 resolves |
| Territory Definitions | ✅ **Supplied**, 51/51, on the Rules notices' `CG-T` pages | Territory resolves. Three schemes — ZIP table (27), county/city (4), entire state (20) — and the county/city one needs an unmatched→referral path |
| Terrorism Supplement | ❌ Absent from both corpora | Terrorism premium cannot be computed at all |
| Workers Compensation loss costs | ❌ Absent (cross-line) | Blocks OCP class `15191` only — 51/51 jurisdictions price it as 75% of WC |
| Tables 40.F / 40.G values | ❌ Not extracted | LoED and Cyber hazard grades; extractable from the Rules corpus |
| Rule 37.D/E/F modifier values | ❌ Not published | Manual declares them refer-to-company anyway; the **base** charges are now supplied (§11.6) |

### Three coverages rate differently than this document assumed

The rate pages settle questions the Rules corpus left open:

| Coverage | Rules corpus implied | Rate corpus shows |
|---|---|---|
| **Liquor Liability (332)**, §11.3.3 | A full nine-step A1 algorithm, step 2 *"select the basic limits rate"* | **No published loss cost in any of the 51 jurisdictions** — only Table 5.D ELPs. Liquor is ELP-driven or refer-to-company countrywide |
| **Railroad Protective (335)**, §11.4.2 | A2 eight-step, step 2 selects a rate | **No published loss cost.** Table 5.E rates class `40014` as *"150% of the loss cost for Class Code 16292"* and class `40013` on **number of passenger and freight trains per day** at $100,000/$300,000 basic limits — a rating dimension unique in the program |
| **OCP / Principals Protective (335)**, §11.4.1 | A2 eight-step against published rates | Published loss costs in **15** jurisdictions and **withdrawn in the other 36** during the 2027 filing. The executor needs both paths and must choose per edition |

None of these changes the archetype assignment — the step sequences hold. What changes is
**where step 2/3 sources its operand**, which is a per-jurisdiction, per-edition decision
rather than a constant.

The build posture is unchanged in shape but not in scope: implement all ten pipeline stages
and wire every published factor, but the rate adapter is now a **real, versioned, recursive
resolver over stored data** rather than an injected stub. **The engine is priceable in all 51
jurisdictions** for Premises/Operations and Products/Completed Operations — every input those
two sublines need is in the corpora, with the sole exception of the carrier's own loss cost
multiplier.
