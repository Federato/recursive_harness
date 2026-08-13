# 02 — The Countrywide (CW) Base Rulebook

> **Reconciliation note, 2026-08-11.** This document was derived from the filed manual PDFs and **before any subline
> was derived end to end**. The per-subline gates have since superseded or sharpened some claims
> here — see [`../gates/RECONCILIATION.md`](../gates/RECONCILIATION.md) (items R4). The text below is
> left as the record of what this derivation found on its own; that independence is what makes
> agreement between the two derivations evidence.

**Primary source:** `GL-MU-2027-RU-001-C.pdf` — *Commercial Lines Manual, Division Six —
General Liability, MULTISTATE RULES*, "1st Edition 4-27", filing reference `GL-2024-RRU24`.
**Comparison source:** `GL-MU-2022-RU-001-C.pdf` / `GL-MU-2023-RU-001-C.pdf` (prior numbering).

---

## 2.1 Manual structure

The countrywide manual is organised into four rule sections plus two table sections:

| Section | Rules | Content |
|---|---|---|
| **Section I — General Rules** | 1–17 | Program overview, referrals, policy term, premium computation, rounding, minimum premium, AP/RP changes, cancellations, countersignature, deductibles, additional insureds, coverage part |
| **Section II — Commercial General Liability Coverage Rules** | 20–33 | CGL description, premium determination, mandatory endorsements, rates, bases of premium, classification assignment, claims-made rules |
| **Section III — Miscellaneous Coverage Rules** | 34–55 | Individual-risk rule, optional endorsements, and **every non-CGL subline** |
| **Section IV — Increased Limits** | 56 | ILF procedures + pointer to state tables |
| **Classification Table** | — | 5 class-code groups, `CG-CT-1` … `CG-CT-485` |
| **Index / TOC** | — | `CG-i` … `CG-vi` |

### Classification Table groups (Rule 25 / CW Classification Table)

| Code range | Group | Manual pages |
|---|---|---|
| 10000–19999 | Mercantile | `CG-CT-1` – `CG-CT-88` |
| 40000–49999 | Miscellaneous | `CG-CT-89` – `CG-CT-226` |
| 50000–59999 | Manufacturing And Processing | `CG-CT-227` – `CG-CT-331` |
| 60000–69999 | Building Or Premises — Offices / Residential / Leased To Others | `CG-CT-332` – `CG-CT-369` |
| 90000–99999 | Contracting Or Servicing | `CG-CT-370` – `CG-CT-485` |

Each classification entry carries a fixed record shape, directly usable as a schema:

```
10011 Cannabis Distributors — other than hemp
    Class Code:      10011
    Premium Base:    Gross Sales — per $1,000 gross sales
    Application:     <free text>
    Application Exception:      <optional free text>
    For Premium Computation Purposes:  <optional; e.g. "No separate loss cost applies
                                        for products/completed operations">
    Separately Classify And Rate:      <list of cross-references>
```

---

## 2.2 The countrywide premium algorithm

**CW Rule 21 (2027) / Rule 35 (2022–2023) — Premium Determination**, verbatim structure:

| Step | Rule 21 text (condensed) |
|---|---|
| A | Determine the applicable classification(s) |
| B | Determine the premium base applicable to the classification(s) — *the same premium base applies to both Premises-Operations and Products-Completed Operations* |
| C | Select the basic limits rate(s) for the classification(s) from the state company rates, for **both** Prem-Ops and Prod-CompOps |
| D | Adjust the basic limits rate(s) for any coverage change **other than deductibles** |
| E | Adjust by the appropriate **increased limits factors** and any other rate modification(s); adjust for deductible per Rule 15 |
| F | Multiply units of exposure × adjusted rate, per classification |
| G | Determine any other additional premiums |
| H | Total = F + G |
| I | Use H **or the policywriting minimum premium, whichever is greater** |

This is the spine of the engine. Note three things the engine must honour:

1. **Two parallel rate streams.** Premises-Operations (subline 334) and
   Products/Completed-Operations (subline 336) are rated separately from step C onward but
   share one premium base and one exposure count (step B). They are not two policies; they
   are two rate components of one classification line.
2. **Deductible is applied at the rate level, not the premium level** (step E, and Rule
   15.D.4: *"Deductible discount factors are applicable only to the company's basic limits
   rates and minimum premiums"*).
3. **The minimum-premium comparison is terminal** (step I) — it applies to the whole policy,
   after all additional premiums.

### Rule 23 — Rates and limits

- **Basic limits (Rule 23.C.1):** `$100,000` each occurrence BI+PD; within that,
  `$100,000` per premises for Damage To Premises Rented To You; `$5,000` per person Medical
  Payments; `$100,000` per person/organization Personal & Advertising Injury; all subject to
  a `$200,000` General Aggregate **or** `$200,000` Products-Completed Operations Aggregate.
- **Occurrence limit is shared** (Rule 23.C.2): it applies to both Prem-Ops and
  Prod-CompOps — *"different occurrence limits cannot be selected."*
- **Damage To Premises Rented To You does not auto-increase** with the occurrence limit;
  above `$100,000` → refer to company.
- **Medical Payments** may be increased independently, via **Table 23.D.3**, a genuinely
  countrywide table:

  | Classification group | $10,000 | $15,000 | $20,000 | $25,000 |
  |---|---|---|---|---|
  | Mercantile / Miscellaneous / Manufacturing / Buildings (10000–69999) | 1.007 | 1.011 | 1.014 | 1.016 |
  | Contracting Or Servicing (90000–99999) | 1.011 | 1.017 | 1.022 | 1.026 |

  Applied as (Rule 23.D.2.c): `adjusted ILF = medpay_factor + ILF − 1`.
  Worked example given in the manual: `1.020 + 1.95 − 1 = 1.97`.
  Above `$25,000` each person → refer to company.

- **Split limits (Rule 23.D.5):** derive BI and PD factors separately from the CSL table,
  then apply countrywide weight factors:

  | Classification code | B.I. weight | P.D. weight | Constant |
  |---|---|---|---|
  | 10000–19999 / 40000–49999 / 50000–59999 / 60000–69999 | 0.97 | 0.11 | −0.03 |
  | 90000–99999 (Contracting Or Servicing) | 0.83 | 0.19 | +0.03 |

### Rule 24 — Bases of premium

Eight countrywide bases: **Admissions, Area, Each, Gross Sales, Payroll, Total Cost,
Total Operating Expenditures, Units**. The base is a property of the classification
(Classification Table `Premium Base:` field), not a user choice.

Payroll (24.E) is the only base with a **state-variable limitation** — see §5.1.

### Rule 15 — Deductibles

- Available separately for Prem-Ops and Prod-CompOps, and for BI / PD / BI+PD combined.
- Discount factors are keyed to the **increased limits table assignment**:
  *"provided in accordance with the increased limits tables applicable for
  Premises/Operations, that is, Tables 1-3, and Products/Completed Operations, that is,
  Tables A, B and C."*
- Per-occurrence basis only; per-claim → refer to company.
- Apply only when the insured's retention is not above the basic limit.

> **This paragraph decodes the ILTA code format.** State ILTA pages assign each class code a
> value like `1A`, `2B`, `3C`. That single token is a **composite**: the digit selects the
> Premises/Operations table (1–3) and the letter selects the Products/Completed-Operations
> table (A–C). One lookup, two table selections. This is essential and is not stated in one
> place in the manual — it is the join of Rule 15.D.2 with the state ILTA pages.

### Rule 56 — Increased limits

- Limits expressed in thousands.
- **Interpolation is defined** (56.A.4): take the next-lower and next-higher factor,
  interpolate, and *"all fractions in the third decimal place shall be considered as an
  additional unit in the second decimal place"* (round half-up at 2dp). Where **neither**
  limit appears in the table → refer to company.
- Some factors are flagged *"MUST be referred to company before using"* — the tables are
  physically split into a usable block and a refer-to-company block.
- **56.B: "The increased limits tables are displayed in the state exceptions."**
- **56.C: ILTAs are displayed by classification code in the state pages.**

---

## 2.3 Edition renumbering — a first-class hazard

The 2027 countrywide edition **renumbers 21 rules**. Selected moves, all verified against both
PDFs:

| # | CW 2022 / 2023 | CW 2027 |
|---|---|---|
| 1 | Application Of This Division | **Overview Of The General Liability Program** |
| 3 | Effective Date | *Reserved For Future Use* |
| 14 | Minimum Premiums | *Reserved For Future Use* |
| 16 | Additional Interests | **Additional Insured Endorsements** |
| 17 | *(absent)* | **Coverage Part** |
| 20 | *(absent)* | **Description Of CGL Coverage** |
| 21 | *(absent)* | **Premium Determination** |
| 22 | Description Of CGL Coverage | **Mandatory Endorsements** |
| 35 | **Premium Determination** | *Reserved For Future Use* |
| 40 | *(absent)* | **Cyber Incident Liability And Loss Of Electronic Data Coverage** |
| 50 | Sports Participants | *(absent)* |
| 51 | Elevator Or Escalator Inspection Charge | *(absent)* |
| 52 | Coverage For Insureds For Injury To Leased Workers | *(absent)* |
| 54 | Year 2000 Computer-Related Endorsements | *Reserved For Future Use* |
| 55 | Terrorism Endorsement Options — Federal Backstop | **Terrorism** |

Full table: `A2-CW-RULE-CATALOG.md`.

The full edition-migration model — how a new countrywide edition is diffed, classified into
seven change types, and activated without breaking policies already written — is in
**[`12-VERSIONING-AND-EDITIONS.md`](12-VERSIONING-AND-EDITIONS.md)** §12.5.

**Engineering consequence — non-negotiable:** the printed rule number is a *display label
scoped to an edition*, not an identifier. The engine must key on a stable semantic rule key
(e.g. `GL.PREMIUM_DETERMINATION`) with an edition-scoped map to the printed number. Any state
overlay that says "Rule 22 is replaced" must be resolved through the numbering of **the
edition that overlay was written against**, not the current one. This is specified in
`06-DATA-SCHEMA.md` §6.3 and `07-ENGINE-ARCHITECTURE.md` §7.4.

Note also that the 2027 edition **moves subline codes into the rule titles** (e.g. Rule 42
becomes "Electronic Data Liability Coverage **(Subline Code 325)**"), which is convenient for
automated subline binding but is itself an edition-dependent signal.

---

## 2.4 Sublines defined countrywide

| Subline | Coverage | CW rule (2027) |
|---|---|---|
| **334** | Premises-Operations | 23.A.1 |
| **336** | Products/Completed Operations | 23.A.2, 48 |
| **325** | Electronic Data Liability; Employee Benefits Liability | 42, 43 |
| **332** | Liquor Liability | 45 |
| **335** | Owners & Contractors Protective; Principals Protective; Railroad Protective | 46, 49 |
| **350** | Pollution Liability; Underground Storage Tank | 47, 53 |
| **365** | Product Withdrawal | 44 |
| **370** | Unmanned Aircraft | 37 |

Note that **335 and 350 each carry two distinct coverages with different rating mechanics**,
and **325 likewise**. Subline code is therefore *not* a primary key for a rating plan —
`(subline, coverage)` is. This is reflected in the schema.
