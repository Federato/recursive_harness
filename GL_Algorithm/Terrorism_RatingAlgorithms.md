# Terrorism (Certified Acts / TRIA) — Rating Algorithms

**Source gate doc:** `docs/gates/GATE-TERRORISM.md`
**Line:** General Liability (GL), Rule 55 *(Terrorism Premium Determination)*, TRIA endorsement options and certified-acts premium
**Derived against:** `GL_CW_20260101_V01`, cross-checked against the other two declared parents (per GATE-TERRORISM.md, header)
**Manual:** `GL-MU-2022-TERXV-001`, *Terrorism Premium Determination*, Table A#.A.1.a, plus the Terrorism Supplement to the CLM (3 notices, PEV001–PEV016, TEV001–TEV008)
**Documented:** 2026-08-20
**Forms added:** 2026-09-01, from direct read of `GL-MU-2022-TERXV-001-C.pdf` (Division Six, Terrorism Supplement)
**Reconciled against the built engine:** 2026-10-02 (commit `630ba2f`) — offline engine runs OK@2026-10-02 (GL_OK_20261001_V01 / GL_CW_20261001_V01), OK@2027-04-01 (GL_OK_20270401_V04 / GL_CW_20270401_V02), FL@2026-10-02 and @2027-04-01, NY@2026-10-02 (GL_NY_20260801_V01 / GL_CW_20260101_V01), plus rule-XML diffs of every terrorism rule file across all 12 CW editions; corrections are marked **(engine)** below.

> **Reconciliation summary (2026-10-02).** The form-trigger story below was written from the manual; the
> engine runs ISO's rule XML, and the two differ in five ways that change premiums:
> 1. **The chain is switched by `TerrorismCoverage` plus the *presence* of an NBCR or aggregate-cap
>    endorsement record — never by an exclusion form.** `SetCoverageOnPolicyIndicator` = subline is
>    `Premises/Operations and Products/Completed Operations` AND (`TerrorismCoverage = "Yes"` OR an
>    NBCR record — CG 21 84 / 21 88 / 21 91 — OR a cap record — CG 21 80 (21 82 on Prods) / 21 89 / 21 92). CG 21 73/75/87/90
>    are read only by validation messages; attaching one does not stop a `Yes` policy from being charged.
> 2. **`SetPremium` is a `Choose` with precedence, not a product of optional factors.** `Yes` wins; the
>    NBCR branch and the cap/ILF-ratio branch are mutually exclusive alternatives tried only when
>    `TerrorismCoverage` is not `Yes`. A `Yes` policy carrying CG 21 84 gets **no** 0.58 discount.
> 3. **A declined policy (`TerrorismCoverage = "No"`) is still charged when a cap endorsement is attached**
>    (CW only — FL and NY overrides drop that branch).
> 4. **CW 20270401 V01/V02 add a $1 floor** (premium 0 while the sibling base > 0 → 1). Editions
>    20231201 V02 … 20261001 V01 have no floor and also accept `Subline = "Premises/Operations"` alone.
> 5. **All Other Sublines selects one premium by `Subline`; it does not sum five.** Endorsement-only's
>    `EndorsementPremium` is **computed** (sum of ~294 attached endorsements' premiums), not user-entered.

Terrorism does not fit the shape of the other GL sublines. It has **no base rate, no ELP, and no
loss-cost table of its own.** It is a *premium-on-premium* multiplier: it reads the **finished,
already-rated premiums of sibling coverage groups**, sums them, and applies an exposure-class
factor (plus two optional factors) to produce its own premium. Per GATE-TERRORISM.md § 2, this is
the coverage-group-scope defect pattern "E18" recurring at **policy scope** — terrorism reads four
different groups' final premiums across three sublines and unmanned aircraft, so it must be the
**last thing rated** in a policy (§ 8.1).

Because there is no rate table, this document's "rate build-up" sections are replaced with
**"aggregation and factor application"** — the closest analogue in the terrorism chain to the
CF/GL pattern of base rate → adjustments → final rate.

There are **five** independent premium chains, one per host coverage group (per GATE-TERRORISM.md
§ 1, the `OTHER`-classified population):

- **Prem/Ops** — `GeneralLiabilityTerrorismPremOpsCoverage`
- **Products/Completed Operations** — `GeneralLiabilityTerrorismProdsCompldOpsCoverage`
- **All Other Sublines** — `GeneralLiabilityTerrorismAllOtherSublineCoverage`
- **Unmanned Aircraft** — `GeneralLiabilityUnmannedAircraftTerrorismCoverage`
- **Endorsement-only** — `GeneralLiabilityTerrorismEndorsementCoverage`

This document covers all five.

---

## NEW: Which endorsement form triggers which rating flow

The manual organizes coverage as elective **endorsement options** layered on top of the mandatory
TRIA-required baseline. Which form is attached to the policy — not a hidden condition in the rating
math — is what switches on the NBCR factor, the sub-limit ILF ratio, or takes the policy out of the
aggregation chain entirely. Confirmed by direct read of the manual's Terrorism Supplement, Division
Six (forms below are as printed there; state-suffixed equivalents exist for AK/WA and are structurally
identical to the countrywide numbers unless noted):

| Form | What it does | Effect on the rating flow | Program-status window |
|---|---|---|---|
| **CG 21 70** | Cap on losses only; full certified-acts coverage | Baseline **A.1.a** math only — no optional factor fires | TRIA in effect |
| **CG 21 71** | Excludes non-certified acts committed outside the US | Does not touch the certified-acts premium calc | TRIA in effect |
| **CG 21 73** | Excludes certified acts of terrorism entirely (other-acts coverage stays) | **No terrorism premium — in practice, because it accompanies `TerrorismCoverage = "No"`.** **(engine)** No rating rule reads this record; with `Yes` it only raises *"An Exclusion of Certified Acts of Terrorism Form cannot be attached … when … coverage is accepted"* and the premium is still charged (OK@2027-04-01: PremOps 4, Prods 29) | TRIA in effect |
| **CG 21 75** | Excludes certified acts *and* non-certified acts outside the US | Same as CG 21 73 — validation-only in ERC | TRIA in effect |
| **CG 21 76** | Add-on excluding punitive damages | Riders onto CG 21 80/82/84; no premium-math effect of its own | TRIA in effect |
| **CG 21 80** | Certified-acts coverage capped at a Terrorism Aggregate Limit (Prem/Ops) | **Fires the sub-limit ILF ratio** (A.1.c Steps 1–6) — creates the aggregate-limit-vs-per-occurrence-limit mismatch that ratio prices | TRIA in effect |
| **CG 21 82** | Same as CG 21 80, Products/Completed Ops version | Same ILF-ratio trigger, Prods/CompldOps chain | TRIA in effect |
| **CG 21 84** | Excludes NBCR from certified-acts coverage, subject to statutory cap; only offerable if insured first rejected standard coverage | **Fires the 0.58 NBCR factor** (A.1.b) — **(engine)** only when `TerrorismCoverage` ≠ `Yes` | TRIA in effect |
| **CG 21 87** | Conditional exclusion of all terrorism | No terrorism premium, contingent on Program disposition | Last calendar year of Program, term extends past it |
| **CG 21 88** | Conditional exclusion of NBCR terrorism (broader "terrorism," not just certified acts) | Manual: excludes the peril outright. **(engine)** ERC treats it exactly like CG 21 84 — its record (`…ConditionalExclusionOfTerrorismNuclearBiologicalChemicalDispositionOfAct2002`) is one of the three that fire the 0.58 branch | Last calendar year of Program |
| **CG 21 89** | Conditional aggregate-limit terrorism coverage | Conditional counterpart to CG 21 80/82's ILF-ratio trigger | Last calendar year of Program |
| **CG 21 93** | Extended reporting period for terrorism (claims-made policies) | Required alongside CG 21 87/88 on claims-made policies; no premium-math effect | Last calendar year of Program |
| **CG 21 90** | Exclusion of terrorism (post-termination) | No terrorism premium | After Program termination |
| **CG 21 91** | Exclusion of NBCR terrorism (post-termination) | Excludes the peril outright, like CG 21 88 — **(engine)** and, like CG 21 88, fires the 0.58 branch (`…ExclusionOfTerrorismNuclearBiologicalChemicalTerrorism` record) | After Program termination |
| **CG 21 92** | Aggregate-limit terrorism coverage (post-termination) | Post-termination counterpart to CG 21 80/82's ILF-ratio trigger | After Program termination |

**Key distinction worth flagging:** CG 21 84 (0.58 factor) and CG 21 88/91 (conditional/post-termination
NBCR exclusion) are *not* the same lever. CG 21 84 keeps certified-acts coverage in force and
**discounts** the premium for narrowing out NBCR. CG 21 88/91 **excludes NBCR terrorism outright**
(a broader "terrorism" definition, not limited to certified acts) — those forms don't feed the 0.58
factor at all, since there's no NBCR premium left to discount. **(engine) This is the manual's
reading only.** ERC's `SetPremium` (every CW edition 20231201 V02 → 20270401 V02) puts all three NBCR
records — CG 21 84, CG 21 88 and CG 21 91 — in one `Or` that fires the 0.58 branch. The engine follows
ERC, so CG 21 88/91 *do* discount by 0.58.

The **endorsement-only coverage group** (`GeneralLiabilityTerrorismEndorsementCoverage`) was mapped
by GATE-TERRORISM.md § 8.5 to the aggregate-limit family (CG 21 80 / 21 89 / 21 92). **(engine) The rule
file says otherwise:** it is the terrorism charge on *other endorsements' premiums*. `SetEndorsementPremium`
sums the `Premium` of ~294 attachable GL endorsements (plus a state hook `EndorsementPremiumState`, 0 in
CW), and the group switches on under the same `TerrorismCoverage = Yes` / NBCR / cap test as Prem/Ops
(keyed on `Subline`). See "Endorsement-only — premium" below.

**Resolved from the rule files (engine, 2026-10-02):** "which form is attached" is read as the
**existence of the endorsement's input record** (`Exist AtInputDataDef=…Table/<Endorsement>`), plus the
policy field `TerrorismCoverage`. The records ERC tests:

| Record (policy-level table) | Form | Effect in `SetPremium` |
|---|---|---|
| `TerrorismCoverage = "Yes"` (policy field) | CG 21 70 family | branch 1: × exposure-class factor only |
| `GeneralLiabilityExclusionOfCertifiedActsOfNuclearBiologicalChemicalActsTerrorismCapOnLossesFromCertifiedActs` | CG 21 84 | branch 2: × factor × 0.58 |
| `GeneralLiabilityConditionalExclusionOfTerrorismNuclearBiologicalChemicalDispositionOfAct2002` | CG 21 88 | branch 2 |
| `GeneralLiabilityExclusionOfTerrorismNuclearBiologicalChemicalTerrorism` | CG 21 91 | branch 2 |
| `GeneralLiabilityCertifiedActsOfTerrorismAggregateLimitCapOnLossesFromCertifiedActsOfTerrorismPremOps` (`AggregateLimit`) | CG 21 80 | branch 3: ILF ratio |
| `…AggregateLimitCapOnLossesFromCertifiedActsOfTerrorismProdsCompldOps` | CG 21 82 | branch 3 (Prods chain only) |
| `GeneralLiabilityConditionalLimitationOfCoverageTerrorismSublimitAnnualAggregateTerrorismAct2002` | CG 21 89 | branch 3 |
| `GeneralLiabilityLimitationOfCoverageForTerrorismSubLimitAnnualAggregateBasis` | CG 21 92 | branch 3 |
| `GeneralLiabilityExclusionOfCertifiedActsOfTerrorism` etc. | CG 21 73 / 75 / 87 / 90 | none — validation messages only |

---

## Master orchestration

Per GATE-TERRORISM.md § 1–2, the 20-table terrorism population in the countrywide package classifies
into **12 CAPTURE · 7 OTHER · 1 RATE_DRIVEN** coverage groups; the 7 `OTHER` groups are the ones that
actually produce a terrorism premium, and none of their premium sources appear in the standard
`RATE_SRC` list (`FinalRate · BaseRate · LossCost · ELP · AdjustedBaseRate · AdjustedRate`) — terrorism
is invisible to a rate-driven scan "by construction, not by measurement" (§ 1).

The worked example, `GeneralLiabilityTerrorismPremOpsCoverage` (per GATE-TERRORISM.md § 2):

```
ClassCoveragePremium = GeneralLiabilityClassificationPremOpsCoverage/Premium
                     + GeneralLiabilityClassificationLossOfElectronicDataPremOpsCoverage/Premium
                     + GeneralLiabilityClassificationCyberIncidentLiabilityPremOpsCoverage/Premium

Premium = round( ClassCoveragePremium
                 x CertifiedActsOfTerrorismExposureClassFactorPremises
                 [x CertifiedActsOfTerrorismNuclBioChemRadioFactor]      # fires if CG 21 84 attached
                 [x TerrorismILF / GeneralLiabilityClassificationPremOpsCoverage/FinalILF]  # fires if CG 21 80/89/92 attached
               , 0)
```

**(engine) That single product is not what ERC computes.** The built engine executes
`GeneralLiabilityTerrorismPremOpsCoverageRules.SetPremium` (CW 20270401 V02, identical in V01) as a
first-match `Choose`, inside a subline gate:

```
if Subline != "Premises/Operations and Products/Completed Operations":  calc = 0
elif TerrorismCoverage == "Yes":                                         # branch 1 — wins outright
    calc = round(CCP x ExposureClassFactorPremises, 0)
elif CG 21 84 or CG 21 88 or CG 21 91 record exists:                     # branch 2
    calc = round(CCP x ExposureClassFactorPremises x NuclBioChemRadioFactor, 0)
elif CG 21 80 or CG 21 89 or CG 21 92 record exists:                     # branch 3
    calc = round( round(CCP x ExposureClassFactorPremises, 0)
                  x round(TerrorismILF / PremOpsCoverage.FinalILF, 3) , 0)    # 0 if FinalILF = 0
else:
    calc = 0
Premium = 1   if calc == 0 and CCP > 0       # $1 floor — CW 20270401 V01/V02 only
        = calc otherwise
```

The bracketed terms are **alternatives, never combined**: the NBCR factor and the ILF ratio cannot
both apply, and neither applies to a `Yes` policy. Edition differences (rule-XML hash diff across all
CW editions): 20231201 V02 → 20261001 V01 also accept `Subline = "Premises/Operations"` and have **no
$1 floor**; branch 3's inner `Product` is rounded to 0 dp in every edition (two-stage rounding).

Three structural facts follow (per GATE-TERRORISM.md § 2):

1. Terrorism runs **after every other rating item**, including any not yet built, because it
   consumes finished premiums.
2. It reads a sibling's `FinalILF` in addition to its `Premium` — the sub-limit ratio in Step 4
   needs the host's increased-limits factor, not just its dollar answer.
3. Evaluation order is part of the algorithm at **policy** level, not just within a
   classification — the kernel must expose resolved premium state policy-wide.

`SetTerrorismILF` implements the manual's sub-limit selection exactly (PEV001 A.1.c.(1) and (2)):
when the terrorism aggregate limit is ≤ the policy per-occurrence limit, the ILF is taken with the
aggregate limit as **both** occurrence and aggregate; when it is greater, with the **policy
per-occurrence limit** and the terrorism aggregate (per GATE-TERRORISM.md § 2). This branch only
runs at all when CG 21 80 (or 82/89/92) has put a Terrorism Aggregate Limit on the policy.
**(engine)** The ILF is read from the **Prem/Ops ILF table** (`LookupILFPremOps`; Prods uses
`LookupILFProds`) at the host's increased-limit table assignment. With no cap record, `TerrorismILF`
defaults to **1.0**. Up to CW 20261001 V01 the rule appends `" CSL"` to the aggregate-limit value before
the lookup; **CW 20270401 V01/V02 drop that suffix** (same OI-96/97 cliff as the base limits).
Confirmed: OK cap `AggregateLimit = "100,000"` → `TerrorismILF` 0.94 (Prem/Ops) / 0.97 (Prods) at both
2026-10-02 and 2027-04-01.

---

## File map

| Piece | File / group | Note |
|---|---|---|
| Prem/Ops premium | `GeneralLiabilityTerrorismPremOpsCoverage` | Sums 3 sibling `Premium` values — named explicitly in GATE-TERRORISM.md § 2 |
| Products/Completed Ops premium | `GeneralLiabilityTerrorismProdsCompldOpsCoverage` | Sums 3 sibling `Premium` values — **(engine) confirmed** in `SetClassCoveragePremium`: `…ProdsCompldOpsCoverage`, `…LossOfElectronicDataProdsCompldOpsCoverage`, `…CyberIncidentLiabilityProdsCompldOpsCoverage` |
| All Other Sublines premium | `GeneralLiabilityTerrorismAllOtherSublineCoverage` | **(engine)** *Selects* ONE sibling `Premium` by `Subline` (Liquor / OCP / Pollution / Railroad / UST) — not a sum of 5; `…ExposureClassFactorOther` |
| Unmanned Aircraft premium | `GeneralLiabilityUnmannedAircraftTerrorismCoverage` | Sums 2 sibling `Premium` values — **(engine) confirmed**: drone Coverage A + Coverage B (`SetCoveragePremium` → `CoveragePremium`) |
| Endorsement-only premium | `GeneralLiabilityTerrorismEndorsementCoverage` | **(engine)** `EndorsementPremium` is *computed* — `SetEndorsementPremium` sums ~294 attached endorsements' `Premium` + `EndorsementPremiumState` — times the user-entered lowercase-"of" factor. Gated like Prem/Ops (`Yes` / NBCR / cap) |
| Aggregator-only, writes no `Premium` | `GeneralLiabilityTerrorism` | Per GATE-TERRORISM.md § 1 table |
| Policy-level total | `GeneralLiability` | The policy-level total, per GATE-TERRORISM.md § 1 table |
| Sub-limit ILF rule | `SetTerrorismILF` | PEV001 A.1.c.(1)/(2) two-case limit selection; triggered by **CG 21 80 / 82 / 89 / 92** |
| Endorsement factor validation | `DoMessageWhenNoClassIsAnAboveAverageExposureClassTheExposureClassFactorCanBeFrom0to004` | Only filed bound on the user-entered endorsement factor |
| NBCR discount | `CertifiedActsOfTerrorismNuclBioChemRadioFactor` (0.58) | Triggered by **CG 21 84** — **(engine)** also CG 21 88 / 21 91; never when `TerrorismCoverage = Yes` |
| No terrorism premium | — | **(engine)** `TerrorismCoverage` ≠ `Yes` **and** no NBCR/cap record → `CoverageOnPolicyIndicator = 0`. CG 21 73 / 75 / 87 / 90 are validation-only |
| Manual corpus | `Commercial Line Manuals/GL/Terrorism/` — 3 notices, 113–118 pages each | Ingested as `text/terrorism/`, `knowledge/terrorism.json` per GATE-TERRORISM.md § 0 |
| Population/verification script | `scripts/erc/37_terrorism_align.py` | 5/5 as of the correction in § 3a |
| 12 `CAPTURE`-classified groups | endorsement capture groups, no rating table | Per GATE-TERRORISM.md § 1, "found by name and not by content" |

> Note: `docs/rating-engine/03-SUBLINE-COVERAGE-PLAN.md` § 3.2.10 independently confirms Rule 55 covers
> TRIA endorsement options and certified-acts premium determination (forms cited there as "CG-120 –
> CG-131"), and that **48 of 51** jurisdictions carry a state A-rule whose entire body just redirects to
> the Terrorism Supplement — consistent with the gate's finding that the supplement, not the base
> corpus, holds the rating rules.

---

## Prem/Ops — rate build-up

**Not applicable to this coverage.** There is no base rate, ELP, or loss-cost step. The "rate" input
to terrorism is the already-computed `Premium` (and `FinalILF`) of three sibling coverage groups —
see Master orchestration above.

---

## Prem/Ops — premium

`GeneralLiabilityTerrorismPremOpsCoverage`

### Step 1 — Aggregate sibling premium
```
ClassCoveragePremium = GeneralLiabilityClassificationPremOpsCoverage/Premium
                     + GeneralLiabilityClassificationLossOfElectronicDataPremOpsCoverage/Premium
                     + GeneralLiabilityClassificationCyberIncidentLiabilityPremOpsCoverage/Premium
```
Per GATE-TERRORISM.md § 2. Three named groups, summed. ~~Runs only if CG 21 73 / 75 / 87 / 90 are not
attached.~~ **(engine)** Runs when `CoverageOnPolicyIndicator = 1`, i.e. subline is Prem/Ops + Prods and
`TerrorismCoverage = "Yes"` or an NBCR/cap record exists (rule `SetCoverageOnPolicyIndicator`, changed in
CW 20270401 to require the combined subline). Exclusion forms are not tested. Engine:
`ClassCoveragePremium` = 996 (OK@2026-10-02), 965 (OK@2027-04-01).

### Step 2 — Exposure class factor
```
ExposureClassFactor = lookup CertifiedActsOfTerrorismExposureClassFactorPremises(
    StateCode, PolicyEffectiveWhileTRIAInEffectIndicator, ExposureClass [, Territory in 15 states]
)
```
Countrywide, keyed on `StateCode` / `PolicyEffectiveWhileTRIAInEffectIndicator` / `ExposureClass`:
**Above Average = .009, Average = .004** (per GATE-TERRORISM.md § 3, confirmed against manual Table
A#.A.1.a). The `PolicyEffectiveWhileTRIAInEffectIndicator` key distinguishes the TRIA row from the
"Full (Post-TRIA)" row, but **both currently carry identical values** — a fact worth stating because
an engine that ignored the indicator would still be right today (§ 3). **(engine)** Trace OK@2026-10-02
and @2027-04-01: `CertifiedActsOfTerrorismExposureClassFactor[Factor] keys=['CW', 1, 'Average Exposure
Class'] -> 0.004`, used for both the Premises and Products lookups (one physical table). The class came
from `TerrorismExposureClassesPremises['CW','50017']`. Rule-XML hashes show that CW 20270401 rewrote
`SetTerrorismExposureClassesPremises` and `SetCertifiedActsOfTerrorismExposureClassFactorPremises`. The
OK factor is unchanged (.004).

**15 of 51 jurisdictions** override this to zero countrywide rows and redirect to a state-suffixed
table keyed additionally on `Territory` — see State deviations below (§ 3a). This is a jurisdiction
effect, not a form/endorsement effect.

The exposure class itself is resolved per class code from `TerrorismExposureClassesPremises` in the
resolved package (countrywide plus LA/NJ/NY overrides — see § "The above-average class list" below).

### Step 3 — Nuclear/bio/chem/radio factor (conditional)
```
if applicable:
    Premium_intermediate = Premium_intermediate x CertifiedActsOfTerrorismNuclBioChemRadioFactor
```
CW value **0.58** — manual A.1.b confirms multiplying the additional premium by that factor for the
NBCR-excluded coverage option (per GATE-TERRORISM.md § 3). **(engine)** Not a conditional multiplier on
top of Step 2. It is branch 2 of the `Choose`, taken only when `TerrorismCoverage` ≠ `Yes`:
`round(CCP × factor × 0.58, 0)`, a single rounding. Engine, OK with TerrorismCoverage No + CG 21 84 record
and the cap removed: 996 × 0.004 × 0.58 = 2.31072 → **2**; Prods 7215 × 0.004 × 0.58 = 16.7388 → **17**
(2026-10-02). At 2027-04-01: 965 × … = 2.2388 → 2; 17. With `Yes` + CG 21 84 the result is 4 / 29, i.e. no
discount.

**Resolved (2026-09-01):** the trigger is **CG 21 84** — "Exclusion Of Certified Nuclear, Biological,
Chemical Or Radiological Acts Of Terrorism; Cap On Losses From Certified Acts Of Terrorism." Per the
manual, this option provides certified-acts coverage with NBCR carved out, and it may only be offered
after the insured has first rejected the standard A.1.a coverage. When CG 21 84 is the operative form,
Step 3 fires; otherwise it does not. (Previously logged as "not resolved in source docs" — this closes
that gap against the manual text, though the exact DataDef/flag the *engine* checks for form selection
is still not visible from the manual alone.)

### Step 4 — Sub-limit ILF ratio (conditional)
```
if applicable:
    Premium_intermediate = Premium_intermediate
        x ( TerrorismILF / GeneralLiabilityClassificationPremOpsCoverage/FinalILF )
```
`TerrorismILF` is set by `SetTerrorismILF` per the manual's two-case limit selection (PEV001
A.1.c.(1)/(2) — see Master orchestration). Divides by the **host group's `FinalILF`**, not a
terrorism-side value — E18 exposure, generalized to policy scope (per GATE-TERRORISM.md § 2).

**Trigger:** **CG 21 80** (Prem/Ops) puts a Terrorism Aggregate Limit on the policy that differs from
the per-occurrence limit; that mismatch is exactly what Steps 1–6 of A.1.c price. Absent CG 21 80 (or
its conditional/post-termination counterparts, CG 21 89 / CG 21 92), there is no separate aggregate
limit to reconcile and Step 4 does not fire.

**(engine)** Branch 3 of the `Choose`, taken only when `TerrorismCoverage` ≠ `Yes` and no NBCR record
exists. It rounds twice: `round( round(CCP × factor, 0) × round(TerrorismILF ÷ FinalILF, 3), 0 )`.
**This branch charges a policy that declined terrorism.** The OK engine base (`TerrorismCoverage =
"No"`, CG 21 80 cap at 100,000) gives:

| Run | PremOps | Prods |
|---|---|---|
| OK@2026-10-02 (GL_OK_20261001_V01 / GL_CW_20261001_V01) | 996 × .004 = 3.984 → 4; × round(0.94/2.140, 3) = 0.439 → 1.756 → **2** | 7215 × .004 = 28.86 → 29; × round(0.97/1.76, 3) = 0.551 → 15.979 → **16** |
| OK@2027-04-01 (GL_OK_20270401_V04 / GL_CW_20270401_V02) | 965 × .004 = 3.86 → 4; × 0.438 → 1.752 → **2** | 29 × 0.551 → **16** |

The 2026 figures match ISO's own certified output for the OK sample (`Payloads/OK/1. Output.json`,
TerrorismCoverage No, terrorism 18, account 8,229 — engine 8,229, eff 2026-08-01, GL_OK_20260801_V01 /
GL_CW_20260101_V01).

### Step 5 — Final premium
```
Premium = round(ClassCoveragePremium x ExposureClassFactor
                 [x NuclBioChemRadioFactor] [x TerrorismILF/FinalILF ratio], 0)
```
**(engine)** Read the brackets as "one of", per the `Choose` in Master orchestration. Then the $1 floor
applies in CW 20270401 V01/V02 only. Engine, `Yes` (branch 1): OK 996 × .004 → **4**, Prods 7215 × .004
→ **29** (2026-10-02); 965 × .004 → 4, 29 (2027-04-01).

---

## Products/Completed Operations — differences from Prem/Ops

`GeneralLiabilityTerrorismProdsCompldOpsCoverage`

Structurally identical shape to Prem/Ops — sum three sibling `Premium` values, multiply by an
exposure-class factor, optionally apply the NBCR factor and the sub-limit ILF ratio (per
GATE-TERRORISM.md § 1's "sibling `Premium`, 3 groups summed" entry for this group).

**Not resolved in source docs:** the gate doc names the three Prem/Ops sibling groups explicitly
(§ 2) but does **not** individually name the three Products/Completed Operations siblings. By the
naming convention independently confirmed in `docs/erc/03-RATING-STRUCTURE.md` (§ "class-rated core"
list, which shows parallel `...PremOps / ...ProdsCompldOps` pairs for both
`CyberIncidentLiability` and `LossOfElectronicData` classification groups), the analogous set is
almost certainly:

```
ClassCoveragePremium = GeneralLiabilityClassificationProdsCompldOpsCoverage/Premium
                     + GeneralLiabilityClassificationLossOfElectronicDataProdsCompldOpsCoverage/Premium
                     + GeneralLiabilityClassificationCyberIncidentLiabilityProdsCompldOpsCoverage/Premium
```

but this specific summation is **inferred from naming convention, not directly cited** in
GATE-TERRORISM.md, so it should be verified against the rule file before being treated as filed fact.
**(engine) Verified 2026-10-02:** `GeneralLiabilityTerrorismProdsCompldOpsCoverageRules.SetClassCoveragePremium`
sums exactly those three groups. Engine: `ClassCoveragePremium` = 7215 (OK, both dates).

Exposure class factor uses `CertifiedActsOfTerrorismExposureClassFactorProducts` and
`TerrorismExposureClassesProducts` (the Products-side counterparts named in GATE-TERRORISM.md § 8.4),
keyed the same way as Prem/Ops.

**Forms:** same trigger logic as Prem/Ops, with **CG 21 82** as the Products/Completed Ops
counterpart to CG 21 80 for the ILF sub-limit ratio. CG 21 84's NBCR carve-out is written generically
across certified-acts coverage and applies to this chain the same way. **(engine)** The Prods branch 3
fires on **either** the CG 21 80 (Prem/Ops) **or** the CG 21 82 (Prods) record, or CG 21 89 / 21 92. It
divides by `…ProdsCompldOpsCoverage/FinalILF`, with `TerrorismILF` from `LookupILFProds`. The OK base,
which carries only the CG 21 80 record, therefore also prices Prods at 16. The precedence is the same
`Choose` as Prem/Ops, and the $1 floor appears in 2027 only.

---

## All Other Sublines — differences from Prem/Ops

`GeneralLiabilityTerrorismAllOtherSublineCoverage`

```
ClassCoveragePremium = sum of 5 sibling Premium values   [not individually named in source docs]
Premium = round(ClassCoveragePremium x ExposureClassFactor
                 [x NuclBioChemRadioFactor] [x TerrorismILF/FinalILF ratio], 0)
```

Per GATE-TERRORISM.md § 1 and § 8.3, this path **always uses the Average exposure category** —
manual A.1.a specifies the average exposure category for sublines other than premises/operations or
products/completed operations. Confirmed in ERC as `TerrorismExposureClassesOtherSublines`, a
**1-row constant table** (per § 3, table row 6): `Average Exposure Class`, always. There is no
per-class-code lookup for this path — it is the one branch where the exposure class is fixed rather
than resolved. This is a structural fact of A.1.a, not a form trigger — the same CG 21 84 / CG 21
80-family triggers described above still apply to the conditional factors.

**Not resolved in source docs:** the five specific sibling coverage groups summed into this path are
not individually named in GATE-TERRORISM.md.

**(engine) Resolved, and the shape is different.** `GeneralLiabilityTerrorismAllOtherSublineCoverageRules.SetPremium`
does not sum. It **selects one** sibling premium by the policy `Subline`:

```
Subline = Liquor                 -> GeneralLiabilityClassificationLiquorCoverage/Premium
        = Owners and Contractors -> …OwnersContractorsCoverage/Premium
        = Pollution              -> …PollutionCoverage/Premium
        = Railroad               -> …RailroadCoverage/Premium
        = Underground Storage Tank -> …UndergroundStorageTankCoverage/Premium
then  Yes  -> round(P x CertifiedActsOfTerrorismExposureClassFactorOther, 0)
      NBCR -> round(P x FactorOther x NuclBioChemRadioFactor, 0)      (CG 21 84 / 88 / 91)
      else -> 0
```

There is **no cap / ILF-ratio branch** on this path, and `SetCoverageOnPolicyIndicator` does not test
cap records. In CW 20270401 V01/V02 the $1 floor here is **unconditional**: calc 0 → Premium 1, with no
"base > 0" test, unlike Prem/Ops. TX, VA and VT override this rule (2027 editions) with four branches
(Liquor/OCP/Pollution/Railroad) and no $1 floor. Not exercised by an engine run, because the engine
bases are Prem/Ops+Prods (`CoverageOnPolicyIndicator = 0`, `Premium = 0.0` in every OK run).

---

## Unmanned Aircraft — differences from Prem/Ops

`GeneralLiabilityUnmannedAircraftTerrorismCoverage`

```
ClassCoveragePremium = sum of 2 sibling Premium values   [not individually named in source docs]
Premium = round(ClassCoveragePremium x ExposureClassFactor
                 [x NuclBioChemRadioFactor] [x TerrorismILF/FinalILF ratio], 0)
```

Per GATE-TERRORISM.md § 1. The two summed groups are presumably Unmanned Aircraft's Coverage A and
Coverage B (rated separately per `docs/rating-engine/03-SUBLINE-COVERAGE-PLAN.md` § 3.2.9), but this
pairing is **not resolved in source docs** — the gate doc gives only the count. Form triggers follow
the same shape as the other three aggregation paths.

**(engine) Resolved 2026-10-02.** `SetCoveragePremium`: `CoveragePremium = CovABIPD.Premium +
CovBPAI.Premium` for the same drone. `SetPremium` is the Prem/Ops `Choose` with three substitutions:

- the factor is the **Premises** factor of the classification's first terrorism record
  (`GeneralLiabilityTerrorism[1]/CertifiedActsOfTerrorismExposureClassFactorPremises`);
- branch 3's numerator is the **Prem/Ops** `TerrorismILF` (from `GeneralLiabilityTerrorismPremOpsCoverage`,
  default 1);
- branch 3's denominator is the drone's own `CovABIPD/ILF`, falling back to `CovBPAI/ILF`, then 1.

Engine run: OK + one designated drone (10 lb, aerial photography, owned/operated, suburban,
aggregate 1,000,000; CovA 316 + CovB 216), base cap CG 21 80 at 100,000, TerrorismCoverage No:
532 × .004 = 2.128 → 2 × round(0.94/2.05, 3) = 0.459 → 0.918 → **1**. Same at 2026-10-02 and 2027-04-01.
The $1 floor is 2027-only, as on Prem/Ops.

---

## Endorsement-only — premium

`GeneralLiabilityTerrorismEndorsementCoverage.SetPremium` (per GATE-TERRORISM.md § 6)

```
Premium = round(EndorsementPremium x CertifiedActsofTerrorismExposureClassFactor, 0)
                                       ^^ lowercase "of" — a distinct DataDef, not a typo
```

~~No sibling aggregation — `EndorsementPremium` is a **user-entered input**~~. **(engine)** `EndorsementPremium`
is **computed**. `ErcRate` = `SetEndorsementPremiumState` (writes 0.0 in CW; a state hook, added
20270401) → `SetEndorsementPremium` → `SetPremium` → `SetPremiumIndicator`. `SetEndorsementPremium`
sums `EndorsementPremiumState` plus the `Premium` of every attached instance of ~294 GL endorsements
(296 `RunRule`s in CW 20270401 V02, 294 in 20260101 V01; e.g. CG 21 70 `capOnLossesFromCertifiedActsOfTerrorismPremium`,
the unmanned-aircraft endorsement, additional insureds, …). `SetCoverageOnPolicyIndicator` uses the same
`Yes` / NBCR / cap test as Prem/Ops, keyed on `Subline` (Prem/Ops+Prods, Prods, or the five other
sublines). In 20260101 V01 it also accepts `Premises/Operations` alone. In OK runs it is `1` but
`EndorsementPremium = 0`, so Premium = 0. `CertifiedActsofTerrorismExposureClassFactor` (lowercase "of") is a **separate, user-entered
DataDef**, declared in the XSD, distinct from the table-driven capitalized
`CertifiedActsOfTerrorismExposureClassFactor` used in the four aggregation paths above. Countrywide:
3 writers of the lowercase field, all in retired editions (`GL_CW_20201201_V01`,
`GL_CW_20210801_V01`); **0 writers in any edition currently in force** — it is purely user-entered
today, with 28 readers across the corpus (per GATE-TERRORISM.md § 6).

**Its only filed bound** is enforced by a validation message, not a rate table:

```
DoMessageWhenNoClassIsAnAboveAverageExposureClassTheExposureClassFactorCanBeFrom0to004
```

which tests the three `TerrorismExposureClasses{Premises,Products,OtherSublines}` DataDefs and, when
none evaluates to `Above Average Exposure Class`, requires the entered factor to be `> 0` and
`≤ 0.004` (per GATE-TERRORISM.md § 6). "The guard *is* the algorithm" for this branch — there is no
computed value to check it against.

**Forms triggering this branch:** **CG 21 80 / CG 21 89 / CG 21 92** — the aggregate-limit-only family
across all three program-status windows (per `docs/rating-engine/03-SUBLINE-COVERAGE-PLAN.md` § 3.2.10
/ GATE-TERRORISM.md § 8.5). Note CG 21 80 also appears in the Prem/Ops ILF-ratio trigger above — the
same form can put a policy on the aggregate-limit path, and whether that resolves to *this* branch or
to the sibling-aggregation-plus-ILF-ratio branch is a rule-file-level distinction not resolved from the
manual or gate doc alone. **(engine) Resolved:** both. A cap record switches on the sibling chains
(branch 3) *and* this group. This group has no ILF ratio, only `round(EndorsementPremium × factor, 0)`.
In CW 20270401 V01/V02 a $1 floor applies when the product is 0 and `EndorsementPremium > 0`, which
includes the case where the user never entered the factor. So any 2027 policy with a priced endorsement
and an active terrorism indicator gets at least $1 here.

Applicable forms per `docs/rating-engine/03-SUBLINE-COVERAGE-PLAN.md` § 3.2.10 / GATE-TERRORISM.md
§ 8.5: **CG 21 80 / CG 21 89 / CG 21 92**.

---

## Five-way comparison

| | Prem/Ops | Prods/CompldOps | All Other Sublines | Unmanned Aircraft | Endorsement-only |
|---|---|---|---|---|---|
| Premium source | 3 sibling `Premium`, named | 3 sibling `Premium`, **(engine) confirmed** | **(engine) ONE** sibling `Premium`, chosen by `Subline` | **(engine)** CovA + CovB `Premium` | **(engine)** computed sum of ~294 endorsement premiums |
| Exposure class | resolved per class code (`...Premises`) | resolved per class code (`...Products`) | **fixed: Average, always** (`…FactorOther`) | **(engine)** Premises factor of `GeneralLiabilityTerrorism[1]` | user-entered factor, validated |
| ILF sub-limit ratio | branch 3 (TerrorismCoverage ≠ Yes); **CG 21 80 / 89 / 92** | branch 3; **CG 21 80 / 82 / 89 / 92** | **(engine) none** | **(engine)** branch 3: PremOps `TerrorismILF` ÷ drone CovA ILF | none — no `FinalILF` input |
| NBCR factor (0.58) | branch 2; **CG 21 84 / 88 / 91** | branch 2; same | branch 2; same | branch 2; same | not applicable |
| `Yes` overrides NBCR/cap | yes | yes | yes | yes | n/a |
| $1 floor (CW 20270401 only) | if CCP > 0 | if CCP > 0 | **always** | if CoveragePremium > 0 | if EndorsementPremium > 0 |
| Group | `GeneralLiabilityTerrorismPremOpsCoverage` | `...ProdsCompldOpsCoverage` | `...AllOtherSublineCoverage` | `GeneralLiabilityUnmannedAircraftTerrorismCoverage` | `...EndorsementCoverage` |

---

## The above-average class list, and jurisdiction overrides

Per GATE-TERRORISM.md § 4: the manual prints **142** above-average classifications; ERC countrywide
carries **141** (105 premises, 54 products, 18 in both). The missing class `91600` exists in ERC (136
of 7,502 csv tables) but is **not in the rating population** countrywide — it appears only in the ILF
assignment table, with 0 of 9 such "extra" classes carrying a loss cost or ELP anywhere countrywide.
**New York** rates `91600` (loss costs in all territory shards, an ELP) and its own
`TerrorismExposureClassesPremises` override (1,191 rows, 106 above-average) lists it as
**Above Average**. Counted as a union across jurisdictions rather than countrywide alone: **142 vs.
142, exact.**

Three jurisdictions override the class tables (per GATE-TERRORISM.md § 4):

| Jurisdiction | Rows | Above-average / Average | vs. countrywide |
|---|---|---|---|
| LA | 1,191 | 105 / 54 | adds `93166 93167 93169` as *average*; no above-average change |
| NJ | 1,187 | 105 / 54 | drops `47469` entirely; no above-average change |
| NY | 1,191 | **106** / 54 | adds `49910 49913 49920 91600`, drops `41620`; `91600` is above-average |

None of the three overrides drops an above-average class — a dropped above-average class would
silently become *average* and under-charge by a factor of 2.25 (`.009 → .004`), which the source's
own verification script now asserts against (per GATE-TERRORISM.md § 4).

---

## State deviations — the countrywide exposure-class factor is not the whole story

Per GATE-TERRORISM.md § 3a: **15 of 51 jurisdictions** override
`CertifiedActsOfTerrorismExposureClassFactor` to zero countrywide rows and redirect all three lookup
rules to a state-suffixed table of their own — **CA, CO, CT, FL, IL, MA, MD, MI, NJ, NY, OR, PA, TX,
VA, WA**.

| | Countrywide | The 15 states |
|---|---|---|
| Keys | `StateCode` · `PolicyEffectiveWhileTRIAInEffectIndicator` · `ExposureClass` | same, **plus `Territory`** |
| Distinct factor values | 2 (`.009` / `.004`) | 15, from `.004` to `.133` |
| Spread | 2.25x | **33x** |

Two go further:

- **New York** files a **Manhattan-specific table** with a fifth key column and factors
  `0.038`–`0.098` — up to 10.9x the countrywide above-average factor — via its own
  `…FactorOtherManhattan` lookup rules.
- **California** adds `…FactorRemainderOfTerritory001` alongside `…FactorCA`.

**(engine)** Confirmed for two of the 15: **FL** looks up `CertifiedActsOfTerrorismExposureClassFactorFL`
keyed `['FL', 1, 'Average Exposure Class', '001']` → **0.009** (Average class; the CW Average is .004).
**NY** routes through `CertifiedActsOfTerrorismExposureClassFactorManhattan` (16 rows; keys State, TRIA,
ExposureClass, Territory, **Manhattan**). The table name is `…FactorManhattan`, not `…FactorOtherManhattan`;
the `…OtherManhattan` name belongs to the *lookup rule* for the Other path. The Manhattan key comes from
the location input `CertifiedActsOfTerrorismManhattan`, and the territory from `TerrorismTerritory`.

So terrorism is **territory-rated in 15 states**, applicable across all four aggregation paths (this
is a factor-resolution difference, not a separate premium chain, and not a form/endorsement effect —
it fires purely on risk jurisdiction). This was found by `scripts/erc/40_referral_census.py` probe 6,
not by re-reading gate prose, and is pinned as check 3a in `scripts/erc/37_terrorism_align.py`.

The Terrorism Supplement's rules are organized by version, not by state exception page — **8 `TEV`
endorsement-option versions** (`TEV001` used by 43 of 52), **16 `PEV`** premium-determination versions
(`PEV001` used by 34 of 52), across **52** jurisdiction assignments (50 states + DC + Puerto Rico).
All 16 `PEV` versions carry an identical above-average class list — state versions deviate on *rules*
(disclosure, prorating, conditional-endorsement handling), not on classes (per GATE-TERRORISM.md
§ 5). **Hawaii** is one of the 52 named jurisdictions with no ERC package and no manual documents in
this project's corpus at all — a scope boundary, tracked as OI-54.

### State `SetPremium` overrides (engine, 2026-10-02)

Scan of every state package for terrorism coverage rule files (newest edition per state shown). Most
states override only the endorsement-only group (state endorsement premiums). These override the
premium arithmetic itself:

| State | Overridden | Newest edition | What changes vs CW |
|---|---|---|---|
| **FL** | PremOps, Prods, AllOther, UnmannedAircraft `SetPremium` | 20270401 V04 | **`Yes` branch only.** There is no NBCR branch and no cap branch, so a declined policy carrying a cap record is **not** charged. The $1 floor is kept in 2027. Engine: FL@2027-04-01 (GL_FL_20270401_V04 / GL_CW_20270401_V02), Yes: 1395 × .009 = 12.555 → **13**, Prods 7215 × .009 = 64.935 → **65**. No + CG 21 80: **0** / **0**. FL@2026-10-02 (GL_FL_20260701_V01): 13 / 65 |
| **NY** | PremOps, Prods, AllOther, UnmannedAircraft | 20260801 V01 (also resolved at 2027-04-01, over CW 20260101 V01) | `Yes` branch only. It also accepts `Subline = "Premises/Operations"`, has no floor, and has no NBCR/cap branch. Engine NY@2026-10-02, Yes, territory 001: Manhattan = Yes → 5296 × .055 = 291.28 → **291**, Prods 6845 × .055 → **376**. Manhattan = No → .038 → **201** / **260**. No + CG 21 80 → 0 |
| **AK** | PremOps, Prods, AllOther, UnmannedAircraft | 20260801 V02 (AK 20270401 V01 keeps only AllOther) | The pre-2027 CW shape, except the NBCR branch tests only CG 21 88 / 21 91. **CG 21 84 does not discount in AK** |
| **TX, VA, VT** | AllOther only | 20270401 | Four branches (Liquor / OCP / Pollution / Railroad); UST is not priced; no $1 floor |
| CA, GA, PR | indicator / process only (older editions) | ≤ 2024 | no premium-arithmetic change |

**(engine) Silent-zero finding.** NY with `TerrorismCoverage = Yes` but **no
`CertifiedActsOfTerrorismManhattan` input** misses the Manhattan table (`lookup-miss … keys=['NY', 1,
'Average Exposure Class', '001', None]`). The factor becomes null, and the premium silently comes out
**0 / 0**. There is no refusal and no referral: OI-94 refuses only null *loss costs*, and no register
entry covers a null terrorism factor. The NY engine base also carries a CG 21 73 record, and the
`scripts/variants.py` terrorism control (`terrorism=Yes`) does not set the Manhattan flag.

---

## Conditional-exclusion prorating — decided, not built

Per GATE-TERRORISM.md § 8.7 (register `R27`, decided 2026-08-12): PEV001 A.2 offers two filed
treatments when a conditional TRIA exclusion is attached — (a) pro-rate by day count and re-rate if
Congress extends the Program, or (b) charge the TRIA factors for the entire policy term and refund if
the Program terminates. **Option (b) is taken**, via a submission field defaulted to *yes*. This needs
no proration arithmetic and is exactly what ERC already does — it detects the condition, computes
`PolicyEffectiveWhileTRIAInEffect` and `PolicyExtendsToPostTRIA`, keys the factor table on the TRIA
indicator, and raises an 18,901-character `TerrorismUnderwritingLogic` message. Two residuals: the
pro-rated refund on actual Program termination is a mid-term change transaction (deferred, out of
scope here), and **whether RAaS can be told to rate the full term is unverified (OI-66)**.

This section is about the conditional endorsements (**CG 21 87 / 88 / 89 / 93**) that exist
specifically to handle the Program's anticipated termination mid-policy-term — see the form table
above for what each one does.

---

## Supporting lookups

| Rule / factor | Table | Keys | CW value |
|---|---|---|---|
| `CertifiedActsOfTerrorismExposureClassFactorPremises` | state-suffixed in 15 states, else countrywide | State, TRIA indicator, ExposureClass [, Territory] | Above Average `.009`, Average `.004` |
| `CertifiedActsOfTerrorismExposureClassFactorProducts` | analogous Products-side table | same shape | not individually re-confirmed in gate doc beyond the Premises example |
| `TerrorismExposureClassesPremises` | class-code lookup, per jurisdiction | ClassCode | CW 105 above-average; LA/NJ/NY override |
| `TerrorismExposureClassesProducts` | class-code lookup, per jurisdiction | ClassCode | CW 54 above-average |
| `TerrorismExposureClassesOtherSublines` | 1-row constant | — | `Average Exposure Class`, always |
| `CertifiedActsOfTerrorismNuclBioChemRadioFactor` | filed value, keys `['CW','Y']` (engine trace) | — | `0.58`; triggered by **CG 21 84** — (engine) also 21 88 / 21 91 |
| `CertifiedActsofTerrorismExposureClassFactor` (lowercase "of") | **not a table** — user-entered input (0 writers in CW 20270401 V02, confirmed) | — | validated `>0` and `≤0.004` when no above-average class present; (engine) multiplies the computed `EndorsementPremium` whenever the endorsement group is on |
| `SetTerrorismILF` / `TerrorismILF` | sub-limit selection per PEV001 A.1.c.(1)/(2); (engine) value from `ILFPremOps` / `ILFProds` | policy per-occurrence limit, terrorism aggregate limit (`" CSL"` appended ≤ CW 20261001 V01, not in 20270401) | triggered by **CG 21 80 / 82 / 89 / 92**; default 1.0 |
| `CertifiedActsOfTerrorismExposureClassFactorManhattan` (lookup rules `…PremisesManhattan` / `…ProductsManhattan` / `…OtherManhattan`) | NY Manhattan-specific | State, TRIA, ExposureClass, Territory, Manhattan (Yes/No) | `0.038`–`0.098`; missing Manhattan input → null → $0 (engine) |
| `…FactorRemainderOfTerritory001` / `…FactorCA` | CA-specific | Territory | — |

Ten `DomainYear200{3,4,5}Terrorism*Factor*` domain tables exist countrywide at **0 rows each** —
per GATE-TERRORISM.md § 7, obsolete-year stubs the 2022 notice describes as deleted (referencing
obsolete years and outdated federal share percentages), not evidence of a rating path.

---

## Quick reference — end-to-end, Prem/Ops path

```
ClassCoveragePremium = PremOps.Premium + LossOfElectronicDataPremOps.Premium
                        + CyberIncidentLiabilityPremOps.Premium

ExposureClass         = lookup TerrorismExposureClassesPremises(ClassCode)   [per-jurisdiction override]

ExposureClassFactor   = lookup CertifiedActsOfTerrorismExposureClassFactorPremises(
                             State, TRIAIndicator, ExposureClass [, Territory in 15 states])
                         [CW: Above Average .009 / Average .004]

TerrorismILF          = PEV001 A.1.c.(1)/(2) two-case limit selection   [only if CG 21 80/89/92 attached; else 1.0]

Premium = round( ClassCoveragePremium
                x ExposureClassFactor
                [x 0.58                                     if CG 21 84 attached]
                [x (TerrorismILF / PremOps.FinalILF)         if CG 21 80/89/92 attached]
              , 0)

# (engine) as executed — first match wins, inside Subline = PremOps+Prods:
#   TerrorismCoverage = Yes          -> round(CCP x f, 0)
#   CG 21 84 / 88 / 91 record        -> round(CCP x f x 0.58, 0)
#   CG 21 80 / 89 / 92 record        -> round( round(CCP x f, 0) x round(TerrorismILF/FinalILF, 3), 0)
#   otherwise                        -> 0
#   CW 20270401 V01/V02: if result = 0 and CCP > 0 -> 1
#   FL, NY: first line only (no NBCR, no cap branch)
```

## Quick reference — end-to-end, endorsement-only path

```
EndorsementPremium = EndorsementPremiumState + sum(Premium of every attached GL endorsement, ~294 kinds)   # (engine)
Premium = round(EndorsementPremium x CertifiedActsofTerrorismExposureClassFactor, 0)
          # CW 20270401: 1 if that is 0 while EndorsementPremium > 0

# (engine) Operative whenever TerrorismCoverage = Yes or an NBCR/cap record exists (not only CG 21 80/89/92).
# CertifiedActsofTerrorismExposureClassFactor is user-entered (lowercase "of"), validated:
#   if no class on the policy is Above Average Exposure Class:
#       0 < factor <= 0.004
```

## Quick reference — no premium computed

```
If CG 21 73, CG 21 75, CG 21 87, or CG 21 90 is attached:
    the certified-acts terrorism chain does not run at all.
    Premium (certified acts) = $0
```

**(engine) Correction.** What the built engine actually does:

```
If TerrorismCoverage != "Yes" and no NBCR (CG 21 84/88/91) or cap (CG 21 80/82/89/92) record exists:
    CoverageOnPolicyIndicator = 0 -> Premium = 0.0 on every terrorism group.
CG 21 73 / 75 / 87 / 90 records only feed validation messages; TerrorismCoverage = Yes with
CG 21 73 attached still charges (OK@2027-04-01: 4 + 29) and returns the message
"An Exclusion of Certified Acts of Terrorism Form cannot be attached ... when ... coverage is accepted".
The kernel does not refuse or refer on these messages (strict-erc and underwriting both complete).
```

All other paths (Products/Completed Operations, All Other Sublines, Unmanned Aircraft) follow the
Prem/Ops shape with the sibling-group substitutions and exposure-class fixing noted in their
respective sections above; form triggers follow the same table given at the top of this document.

---
