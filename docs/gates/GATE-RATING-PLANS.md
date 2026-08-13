# Gate — Rating plans: Schedule · Experience · Composite (build-order item 10)

**Filed 2026-08-12. Tenth gate.** Differential against the nine before it, and the **first gate in
the project where the manual is the richer source.**

**As-of date: 2026-08-12.** Required, not assumed (N4). Derived against **`GL_CW_20270401_V01`**
(the only edition that carries the schedule-rating domains) and cross-checked against the three
declared parents in force.

Measured by [`scripts/erc/38_rating_plans_align.py`](../../scripts/erc/38_rating_plans_align.py)
(**7/7**). Corpora ingested by
[`scripts/15_extract_manual_family.py`](../../scripts/15_extract_manual_family.py).

**This gate closes OI-01, OI-02, OI-03 and OI-55.**

---

## 0. The plans were never missing — the project had stopped looking

`docs/OPEN-ITEMS.md` recorded all three plans as **`PARTIAL`**, each with the same reason: *"`[PDF]`
recorded as absent."* PDF gap **G6** said the plans were unavailable.

**They were on disk.** **52 `CGLES` documents** (Commercial General Liability Experience And
Schedule Rating Plan) and **90 `CRP` documents** (Composite Rating Plan), 654 pages between them —
outside the expert agent's corpus, exactly as the Terrorism Supplement had been (OI-55).

**And there is a specific reason Composite Rating stayed invisible longer than the others:**

| Family | Documents | Line prefix | Years |
|---|---|---|---|
| Composite Rating, first family | **39** | **`GL-`** | 2007–2012 |
| Composite Rating, second family | **51** | **`IL-`** | 2017–2024 |

**It moved to the *Interline* manual in 2017.** A corpus sweep that assumes a General Liability
document begins `GL-` finds **39 of 90**, and the ones it misses are the current ones. That is
habit 8 wearing a filename: a prefix was allowed to define the population.

**All 142 documents extracted cleanly** — 52/52 and 90/90, 654 pages, zero unreadable.

---

## 1. What each corpus covers

| | Schedule & Experience (`CGLES`) | Composite (`CRP`) |
|---|---|---|
| Documents | **52** | **90** |
| Jurisdiction codes | **51** (50 + `MU`) | **51** (50 + `MU`) |
| ERC jurisdictions covered | **50 of 51** | **50 of 51** |
| Editions | 2023 ×50, 2024 ×2 | 2007 ×36, 2009/2011/2012 ×1, 2017 ×50, 2024 ×1 |

**Both corpora cover exactly the same 50**, and the two absentees are named:

- **Hawaii** — absent from every source the project holds (OI-54).
- **Puerto Rico** — **new, and the opposite shape: ERC rates it and neither plan manual covers it.**
  PR inherits the countrywide schedule-rating domains and ships its own `ExpectedExperienceRatio`
  (99 rows) — the **only** jurisdiction of 51 to override that table. **OI-61.**

---

## 2. Schedule Rating — the manual and ERC agree cell for cell

Manual **Rule 9, Table 9** against ERC's `DomainScheduleRatingModification*Pct`:

| Characteristic | Manual range | ERC domain rows | ERC range |
|---|---|---|---|
| Location — exposure **inside** premises | ±5% | **11** | −5% … +5% |
| Location — exposure **outside** premises | ±5% | **11** | −5% … +5% |
| Premises — condition and care | ±10% | **21** | ±10% |
| Equipment — type, condition, care | ±10% | **21** | ±10% |
| Classification — peculiarities | ±10% | **21** | ±10% |
| Employees — selection, training, supervision | ±6% | **13** | ±6% |
| Cooperation — medical facilities | ±2% | **5** | ±2% |
| Cooperation — safety program | ±2% | **5** | ±2% |
| **Maximum credit / debit** | **25%** | 1 row each | **−25 / +25** |

**8 of 8 characteristics agree on both the range and the row count, and ERC ships exactly 8 such
domains — no more, no fewer.** Every domain is enumerated in 1% steps, so a ±n% range is **2n+1**
rows; that identity holds in all eight and is the check, not the row count on its own.

**The 25% cap is filed as data**, `ScheduleRatingMaximumCredit` = `-25` and `…MaximumDebit` = `25`,
one row each — closing OI-01's open question about whether the caps are countrywide. They are, and
**7 of 51 jurisdictions deviate on schedule rating** (§5).

> **Corrected 2026-08-12 by `40_referral_census.py` probe 6.** This section said the 7 deviate *"by
> overriding rules rather than the caps"*. **Nebraska does both**: it empties **both** cap tables to
> zero rows *and* overrides four rules including `ScheduleRatingModificationLogic` — the rule that
> reads `SRPMaximumCredit`/`SRPMaximumDebit` and raises the message. **So the ±25% cap is countrywide
> data with one jurisdiction filing its own mechanism entirely**, and an engine that treats `-25/25`
> as a constant is wrong in Nebraska. The claim "the caps are countrywide" stands; "the deviations do
> not touch them" did not.

**OI-01's other open note resolves too:** the liquor variants
`ScheduleRatingLiquorMaximumCredit` / `…Debit` are 0 rows, and **the countrywide plan contains no
liquor provision at all** — `liquor` appears 0 times in `GL-MU-2023-CGLES-001`. Empty tables for a
plan section that does not exist: N7, not a gap.

---

## 3. Experience Rating — the formula, and a three-column table filed as three tables

**Manual Rule 5.G:**

```
                    AER − EER
EXPERIENCE MOD  =  ───────────  ×  CREDIBILITY
                       EER
```

**ERC `SetExperienceModification`** reads `ERPActualExperienceRatio`, `ERPExpectedExperienceRatio`
and `ERPCredibilityFactor` through `Round · Product · Divide · Subtract` — the same expression, in
the same order. **E10 was closed on ERC evidence alone; it now has its manual citation.**

The chain is `SetActualExperienceRatio` → `SetExperienceCredibilityFactor` →
`SetExperienceModification` → `SetExperienceRatingModificationFactor`, guarded by
`SetExperienceRatingEligibility`, `SetExperienceNumberYearsRequired` and two `DoMessage*` rules
(*at least one completed policy year required*; *years of experience cannot exceed the start-of-business
date*).

### Rule 16 is one printed table and three filed ones

The manual prints **Company Subject Loss Cost | Credibility | Expected Experience Ratio | Maximum
Single Loss** as a single table. ERC files it as **three rate tables of 99 rows each**, sharing one
band key `TotalBasicLimitsCoSubjectLossCost_From/_ToLessThan`:

| | |
|---|---|
| Printed bands parsed from the manual | **97** |
| Bands agreeing with ERC on **all three** columns | **97 of 97 — 291 cells, 0 mismatches** |
| ERC rows per table | **99** = the 97 printed bands + a `[0, 10879) → 0` **eligibility floor** + an open-ended top band to `2³¹−1` |

**The two ERC-only bands are the interesting part.** The floor encodes manual Rule 2 eligibility as
data: below $10,879 of subject loss cost, credibility is `0`, so the modification is `0` and the
risk is not experience rated. **That is an eighth meaning of `0` for N13 and a legitimate one** —
like the liquor grade, it means what it says.

### The near-miss that produced it

The first pass looked for a table called `ExperienceCredibilityFactor`, found **0 rows**, and was
one sentence away from filing *"the credibility table is missing from ERC."* **The rule is named
`LookupExperienceCredibilityFactor`; the table it reads is `CredibilityFactor`.** Resolving the
lookup rather than guessing the table name — the size-of-risk gate's §8 lesson — is what turned a
fabricated gap into a 291-cell agreement.

---

## 4. Composite Rating — executable from ERC, and the manual says so in one sentence

OI-03 recorded: *"the rule file has not been read; whether the plan is executable from ERC alone is
unknown."* **Read. It is three rules, and it is executable.**

```
CalcCompositeRate           = round(TotalClassificationsPremium ÷ CompositeExposure, 8)
FinalCompositeRatingPremium = round(CalcCompositeRate × (FinalAdjustedCompositeExposure
                                                         or CompositeExposure), 0)
```

plus `LookupCompositeRatingExposureIndicatorCode` (**54 rows** in CW 2027, 62 in earlier editions).

**The manual confirms the two-stage shape exactly** — `GL-MU-2007-CRP-001`, Rule 3:

> *"the composite rate determined at the beginning of each policy year is applied to the risk's
> composite exposures at the end of the year to produce the final audited company premium."*

`CalcCompositeRate` is the inception rate; `FinalAdjustedCompositeExposure` is the audited exposure.
**Composite rating is an audit mechanism, not a rating plan in the ordinary sense** — it does not
produce a rate from loss costs, it re-expresses the classification premium as a single rate per
composite exposure unit and re-applies it at audit.

### A rounding precision N10 does not list

`CalcCompositeRate` rounds to **8 decimal places**. N10 records the rounding vocabulary as
*"3dp ×290, 0dp ×238, 4dp ×32, 2dp ×22"*. **There is a fifth value.**

Enumerated across every package: **3 sites at 8dp, in all 10 countrywide editions and 0 of 51
jurisdictions** — `GeneralLiabilityCompositeRating::SetCompositeRate` and **two in Railroad**,
`SetContractCostFactorWOHzd` and `SetContractCostFactorWithHzd`. **Gate 335-RR derived Railroad and
did not record its rounding precision**; a `Decimal` context configured from N10's list would
round two railroad factors to 3dp and one composite rate to 3dp, all silently.

---

## 5. Deviation surface — small, and concentrated on schedule rating

**8 of 51 jurisdictions override any rating-plan rule**, and the shape is lopsided:

| | |
|---|---|
| Deviating on **schedule** rating | **7** — AK, FL, GA, MO, NE, NY, RI |
| Deviating on **experience** rating | **1** — NY (`SetExperienceModification`) |
| Deviating on **composite** rating | **0 of 51** |
| Texas | attaches a form (`AttachFormTexasChangesExperienceRatingModification`) without changing arithmetic |

**Composite rating is countrywide-only**, like Limited Product Withdrawal Expense (gate 365 §9) —
the second such chain found.

**New York again**, and consistently with the [New York differential](NEW-YORK-DIFFERENTIAL.md): it
is the only jurisdiction touching the experience modification itself.

---

## 6. The build plan for item 10

**Three plans, one shared input surface, and they do not compose in the order they are listed.**

### 6.1 Order within the item

1. **Schedule rating first.** Smallest and fully data-driven: 8 domains, 2 caps, one summation and
   one clamp. `SRPTotalModificationPct` against `SRPMaximumCredit`/`SRPMaximumDebit`, enforced by
   `ScheduleRatingModificationLogic`, which writes a **message id** rather than a factor — N15: the
   cap is enforced by a validation rule, not by arithmetic.
2. **Experience rating second.** Needs the three Rule 16 tables and the eligibility guards. Its
   inputs — `ERPTotalIncludedLosses`, `ERPTotalBasicLimitsCoSubjectLossCost` — are **loss history,
   which the corpus does not contain**; they are submission inputs, exactly as OI-02 said.
3. **Composite rating last.** It consumes `TotalClassificationsPremium`, so it runs after every
   classification is rated — the same *runs-last* constraint terrorism has, for the same reason.

### 6.2 What the engine owes

1. **`ScheduleRatingModificationApplies` and `ExperienceRatingApplies` are policy-level flags** of
   the `SizeOfRiskRatingApplies` family. Validate them against their filed domain and refer when
   absent rather than defaulting to "No".
2. **The 25% cap is a `REFER`, not a clamp.** `ScheduleRatingModificationLogic` writes
   `ErcMessageTableId`; it does not truncate the modification. An engine that clamps silently
   prices a risk ISO wants looked at.
3. **Eight decimal places for the composite rate**, and 8dp for the two railroad contract-cost
   factors. Add `8` to the rounding vocabulary (N10) before configuring any `Decimal` context.
4. **Credibility `0` is an eligibility answer, not a missing factor.** Below $10,879 subject loss
   cost the risk is not experience rated; the modification is `0` and that is correct. **Do not
   route it to N13's sentinel register** — this is the taxonomy's second genuinely-zero case.
5. **Loss history is an input, and it genuinely has no oracle.** No STC payload in the ERC corpus
   carries experience-rating losses, and **the 53 RAaS baseline payloads do not either** (confirmed
   by the user, 2026-08-12). So experience rating is the one part of item 10 that cannot be checked
   against a rated output even once the engine exists — unlike schedule and composite rating, which
   can. *(OI-67 corrected the wider claim that the project held only one rated output; this narrower
   claim survives it.)*
6. **Composite rating needs an audit-time re-entry point.** `FinalAdjustedCompositeExposure` is
   supplied after the policy period, so the engine must be able to re-rate a bound policy with a
   new exposure and no other change.

### 6.3 What it does not owe

**No loss-cost derivation, no ILF, no territory.** All three plans operate on premium that other
items have already produced. **Item 10 is the first item that adds no rate lookup of its own** —
which is why its 19 rules are worth less caution than item 6's 150.

---

## 7. Register

| | |
|---|---|
| **OI-01** | **CLOSED.** 8 of 8 schedule characteristics match the manual on range and row count; caps are countrywide data; the liquor variants are empty because the plan has no liquor provision |
| **OI-02** | **CLOSED.** The modification formula is confirmed against Rule 5.G, and Rule 16's three columns match ERC's three tables **97 of 97 bands, 291 cells, 0 mismatches**. The mod factor is still a per-risk input — that part of the item was always right |
| **OI-03** | **CLOSED.** Composite rating is 3 rules and is executable; the manual confirms the inception-rate / audited-exposure shape in one sentence |
| **OI-55** | **CLOSED.** All 142 remaining documents ingested; the agent now routes five corpora and registers **1,119** notices |
| **OI-61** *(new)* | Puerto Rico: ERC rates it under the plans, and neither plan manual covers it. The inverse of Hawaii (OI-54) |
| **OI-62** *(new)* | **N10's rounding vocabulary is one value short.** An 8dp precision exists at 3 sites — the composite rate and two railroad contract-cost factors — and gate 335-RR did not record it |
| **N13** | Eighth meaning of `0`, and the second genuinely-zero one: **credibility `0` below the eligibility floor** |
| **N15** | Third instance of a guard carrying the whole rule: the 25% cap is enforced by a message, not by arithmetic |
| **E10** | Manual citation supplied — closed on ERC evidence in Step 22, confirmed from Rule 5.G today |
| **PDF gap G6** | **Retired.** It said the CGLES, Composite Rating and Size-Of-Risk plans were unavailable. All four claims are now false |

---

## 8. Verification

| | |
|---|---|
| `scripts/erc/38_rating_plans_align.py 20260812` | **7/7** |
| `Agentic/iso-circular-expert/tools/smoke_test.py` | **19/19** (17 + 2 new) |
| `tests/verify_golden.py` · `verify_california.py` · `verify_new_york.py` · `verify_oi50.py` | 80/80 · 11/11 · 10/10 · 7/7 |
| `scripts/erc/34_crosscheck.py` · `35_census_sizeofrisk.py` · `37_terrorism_align.py` | 4/4 · 5/5 · 4/4 |
