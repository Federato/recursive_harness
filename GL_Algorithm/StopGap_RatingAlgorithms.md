# Stop Gap - Employers Liability Coverage - Rating Algorithms

**Source ERC package:** state-filed Rule A2 -- no ISO subline code, no countrywide rating package
(the CW `StopGapRate` factor table is header-only, 0 rows, in every countrywide edition checked)
**Line:** General Liability (GL), state-only Additional Rule A2, filed in 5 monopolistic-fund
jurisdictions -- ND, OH, PR, WA, WY
**Reformatted from:** `docs/gates/GATE-STOPGAP-EMPLOYERS-LIABILITY.md` (filed 2026-09-02, as-of
date 2026-09-02), cross-checked against `docs/rating-engine/03-SUBLINE-COVERAGE-PLAN.md` row 17
and `docs/rating-engine/04-STATE-DEVIATIONS.md`
**Documented:** 2026-09-02

Stop Gap exists only where a state's workers' compensation fund is monopolistic and does not
itself provide employers liability coverage alongside workers' comp. The manual (Rule A2, filed
identically in all five states -- GATE-STOPGAP-EMPLOYERS-LIABILITY.md Section 1) and the raw ERC
package tree (GATE-STOPGAP-EMPLOYERS-LIABILITY.md Section 2) agree exactly on the algorithm below.

> **This coverage is a factor-on-host coverage with a genuine cross-coverage (E18) dependency, not
> a table borrow.** It reads Premises/Operations' own already-computed classification-level
> `BaseRate` and `PremOpsExposureCalc`, not an independent Prem/Ops lookup table -- unlike drone,
> which borrows tables but not computed values (`UnmannedAircraft_RatingAlgorithms.md`, Master
> orchestration section). Stop Gap's premium cannot be computed until Premises/Operations has
> already rated the same classification. (GATE-STOPGAP-EMPLOYERS-LIABILITY.md Section 2.)

**Basis of premium:** each classification's Premises/Operations exposure count
(`PremOpsExposureCalc`), the same exposure base Premises/Operations itself uses -- no separate
Stop Gap exposure base exists.

---

## Master orchestration

Two levels of rule group cooperate: a **policy-level** endorsement rule group (one instance per
attached Stop Gap endorsement) and **four rules added into the classification-level `ErcRate`
override**. Identical rule names and call order confirmed in all five states.

```
GeneralLiabilityRules.ErcCalculateTotalPremium / CallStateErcProcess (top level):
    ForEach GeneralLiabilityStopGapEmployersLiabilityCoverageEndorsementPolLvlTable entry:
        InitializeRuleSet
        ErcProcess -> ErcRate -> SetPremium, SetPremiumIndicator
        CalculateTotalPremium  (summed into the policy total)

GeneralLiabilityClassificationRules.ErcRate (overridden, per classification):
    <run CW ErcRate first>
    1  SetStopGapIncrdLimitFactor   <- LookupILFPremOpsWithArgs (Prem/Ops ILF, Rule 23.D)
    2  SetStopGapFactor             <- LookupStopGapRate(StateCode, ClassificationType)
    3  SetStopGapFinalRate          <- Factor x Prem/Ops BaseRate x ILF x PackageModFactor
                                        x ExperienceRatingModificationFactor x ModToUse
    4  SetStopGapPremium            <- StopGapFinalRate x PremOpsExposureCalc

GeneralLiabilityStopGapEmployersLiabilityCoverageEndorsementPolLvlRules.SetPremium:
    if LimitBodilyInjuryByAccident == LimitBodilyInjuryByDiseaseEachEmployee:
        Premium = sum(StopGapPremium across every classification, every location)
    else:
        Premium = round(ManualPremium x PackageModFactor, 0)     <- refer-to-company branch
```

(GATE-STOPGAP-EMPLOYERS-LIABILITY.md Section 2.)

Not resolved in source docs -- whether `PackageModFactor`, `ExperienceRatingModificationFactor`,
and `ModToUse` are filed rate tables or policy-level copied (`rul:Copy`) values; the gate doc
names them as multipliers in the rule bodies without stating the ERC mechanism behind each.

---

## File map

| Piece | Rule / group | Citation |
|---|---|---|
| Policy-level premium aggregator, entry point | `GeneralLiabilityStopGapEmployersLiabilityCoverageEndorsementPolLvlRules.Rule.xml` | GATE-STOPGAP-EMPLOYERS-LIABILITY.md Section 2 |
| Classification-level rate build-up (4 rules added to `ErcRate`) | `GeneralLiabilityClassificationRules.Rule.xml` | GATE-STOPGAP-EMPLOYERS-LIABILITY.md Section 2 |
| Rate factor table | `StopGapRateDef.RateTableDef.xml` / `StopGapRate.RateTable.csv` | GATE-STOPGAP-EMPLOYERS-LIABILITY.md Sections 3-4 |
| Statistical code table (read) | `StopGapStatCodeDef.RateTableDef.xml` / `StopGapStatCode.RateTable.csv` | GATE-STOPGAP-EMPLOYERS-LIABILITY.md Section 3 |
| Statistical code tables (orphan, 0 rows, unread) | `StopGapManProcContServRiskStatCodeDef`, `StopGapRisksOtherThanManProcContServRiskStatCodeDef` | GATE-STOPGAP-EMPLOYERS-LIABILITY.md Section 3 |
| BI limit domain | `DomainStopGapBIByAccidentOrByDisease.DomainTable.csv` -- 13 whole-dollar bands, $25,000-$10,000,000 (ND) | GATE-STOPGAP-EMPLOYERS-LIABILITY.md Section 5 |
| Top-level wiring | `GeneralLiabilityRules.Rule.xml` -- `InitializeRuleSet`, `CalculateTotalPremium`, `CallStateErcProcess`, `ErcProcess` all `ForEach` over the PolLvl table | GATE-STOPGAP-EMPLOYERS-LIABILITY.md Section 2 |

Not resolved in source docs -- exact line-numbered XML file paths beyond ND's traced locations
(lines 53-55, 108-113, 1332-1339, 1401-1409 in `GeneralLiabilityRules.Rule.xml`); OH/WA/WY/PR were
confirmed to carry the same rule *names* in the same *order* but were not traced line-by-line.

---

## Rate build-up steps (per classification)

### Step 1 -- Premises/Operations Increased Limits Factor
`SetStopGapIncrdLimitFactor` -- guarded by `IsNull(StopGapIncrdLimitFactor)`, so it computes once:

```
StopGapIncrdLimitFactor = LookupILFPremOpsWithArgs(
    assignment = FinalPremOpsIncrdLimitTableAssignmentInt,
    accidentLimit = LimitBodilyInjuryByAccident,
    diseaseLimit = LimitBodilyInjuryByDiseaseAggregate,
)
```

This is the **same** Premises/Operations Increased Limits Factor lookup Prem/Ops itself uses,
called with the submitted Stop Gap limits substituted in place of Prem/Ops' own limits -- per
manual B.1.d: *"using the limit for Bodily Injury By Accident -- Each Accident and Bodily Injury By
Disease -- Each Employee as the Each Occurrence Limit and the Bodily Injury By Disease --
Aggregate Limit as the General Aggregate Limit ... Refer to Rule 23.D."*
(GATE-STOPGAP-EMPLOYERS-LIABILITY.md Section 2.) If the guard finds a null, it writes `0.0`.

There is also a state-overridable `StopGapIncrdLimitFactorOverride` field consumed directly by
`SetStopGapFinalRate`'s alternate branch (see Step 3) when it is non-zero -- not resolved in
source docs what populates this override or under what submission condition it would be set.

### Step 2 -- Stop Gap rate factor
`SetStopGapFactor`:

```
StopGapFactor = LookupStopGapRate(StateCode, ClassificationType)
```

`ClassificationType` is the standard countrywide five-way split used throughout Rule 24/27/29/31/32
(Buildings Or Premises, Contracting Or Servicing, Manufacturing Or Processing, Mercantile,
Miscellaneous) -- not a Stop-Gap-specific classification. It collapses onto the manual's two-bucket
Table A2.B.1.c exactly:

| `ClassificationType` | Factor |
|---|---|
| Manufacturing Or Processing | 0.03 |
| Contracting Or Servicing | 0.03 |
| Buildings Or Premises | 0.02 |
| Mercantile | 0.02 |
| Miscellaneous | 0.02 |

Identical in all five states -- 25/25 cells confirmed (GATE-STOPGAP-EMPLOYERS-LIABILITY.md
Sections 3-4). The countrywide `StopGapRate` table is 0 rows at every edition checked, so the
`FirstNonNull(state, CW)` fallback in `LookupStopGapRate` can never resolve through CW; if the
guard finds a null after both lookups, it writes `0.0`.

---

### Step 3 -- Final rate

`SetStopGapFinalRate` branches on whether `StopGapIncrdLimitFactorOverride` is populated:

```
calcBaseRateStopGap = StopGapFactor x GeneralLiabilityClassificationPremOpsCoverage/BaseRate

if StopGapIncrdLimitFactorOverride == 0.0:
    StopGapFinalRate = round(
        StopGapIncrdLimitFactor x calcBaseRateStopGap
        x PackageModFactor x ExperienceRatingModificationFactor x ModToUse
    , 3)
else:
    StopGapFinalRate = round(
        StopGapIncrdLimitFactorOverride x calcBaseRateStopGap
        x PackageModFactor x ExperienceRatingModificationFactor x ModToUse
    , 3)
```

**`GeneralLiabilityClassificationPremOpsCoverage/BaseRate` is Premises/Operations' own computed
classification-level base rate** -- not an independent lookup, and not a copy of a Prem/Ops table.
This is the E18 cross-coverage dependency named above: Stop Gap cannot rate a classification until
Premises/Operations has already rated that same classification.
(GATE-STOPGAP-EMPLOYERS-LIABILITY.md Section 2.) If neither branch resolves a value, the guard
writes `0.0`.

### Step 4 -- Premium (classification level)

`SetStopGapPremium`:

```
if LimitBodilyInjuryByAccident == LimitBodilyInjuryByDiseaseEachEmployee:
    StopGapPremium = round(StopGapFinalRate x PremOpsExposureCalc, 0)
else:
    StopGapPremium = 0.0
```

`PremOpsExposureCalc` is Premises/Operations' own computed exposure count for the same
classification -- the second half of the E18 dependency. Per manual B.1.e: *"Multiply the number
of units of exposure for each classification by the adjusted premises/operations basic limit
rate(s)."* Note the branch here duplicates the policy-level branch in Step 5 below at the
classification level -- when the limits differ, the classification-level `StopGapPremium` is
forced to `0.0` and the policy-level aggregator switches to the `ManualPremium` path entirely
rather than summing classification premiums.

---

## Premium (policy level)

### Gate
Every attached Stop Gap endorsement instance runs `ErcProcess` -> `ErcRate` ->
`SetPremium`, `SetPremiumIndicator` (GATE-STOPGAP-EMPLOYERS-LIABILITY.md Section 2).

### Branch A -- limits equal (the algorithmic path)
```
Premium = sum(StopGapPremium across every classification, every location)
```

### Branch B -- limits differ (the refer-to-company path)
```
Premium = round(ManualPremium x PackageModFactor, 0)
```

Per manual B.2: *"If the limits for Bodily Injury By Accident -- Each Accident and Bodily Injury
By Disease -- Each Employee differ, refer to company for rating."* ERC does not stop or leave the
field blank on this branch -- it multiplies a **submission-supplied `ManualPremium` field** by the
package modification factor. `ManualPremium` is not computed anywhere in the Stop Gap rule chain;
the submission must carry an already-priced value for this branch to produce a number.
(GATE-STOPGAP-EMPLOYERS-LIABILITY.md Section 2.) This is the same submission-requirement pattern
as OCP's `WorkersCompensationRate` (see `UnmannedAircraft_RatingAlgorithms.md` and
`GATE-370-UNMANNED-AIRCRAFT.md` Sections 6/7a for the general shape of `REFER_TO_COMPANY`
mechanics that still need a carrying field).

`SetPremiumIndicator`: `PremiumIndicator = 1` if `Premium != 0.0`, else `0`.

**`CalculateTotalPremium`, in the PolLvl rule group itself, is the per-instance contribution the
top-level `GeneralLiabilityRules.CalculateTotalPremium` sums over.** Traced directly in
`GeneralLiabilityRules.Rule.xml` (ND, line 112): the top-level rule `ForEach`-es every attached
Stop Gap endorsement instance and calls this PolLvl file's own `CalculateTotalPremium` -- which
tests `PremiumIndicator == 1 AND Premium != 0` and returns `Premium` if so, else `0` -- then sums
the results. The guard exists so an endorsement instance that produced no premium (or one whose
`PremiumIndicator` was never set to `1`) contributes `0` rather than a stray null to the policy
sum. Confirmed as a live, called rule, not boilerplate -- the opposite finding from the empty,
still-called `SetmaximumTakeoffWeightCeiling` rule in `GATE-370-UNMANNED-AIRCRAFT.md` Section 2.

---

## State deviations

**No rating-mechanism deviation among the five states beyond the endorsement form number.** Same
four classification-level rule names, same call order, same table structure, same two factor
values, same ILF borrow, same `ManualPremium` refer-to-company mechanism in all five
(GATE-STOPGAP-EMPLOYERS-LIABILITY.md Section 7).

| State | Endorsement form | Deviation found | Rating effect |
|---|---|---|---|
| ND | CG 04 40 | Calls the stat-code lookup as `LookupStopGapStatCode` rather than a wired-in `SetStopGapStatCode` rule | Statistical reporting only -- no premium effect |
| OH | CG 04 41 | None found | -- |
| WA | CG 04 42 | Manual requires companion form CG 04 50 (Washington Changes -- Who Is An Insured) when Stop Gap attaches; no ERC rule tying the two forms together was located | Not resolved in source docs -- may be a forms-issuance step outside rating scope |
| WY | CG 04 44 | None found | -- |
| PR | CG 04 51 | Carries an unrelated Rule A1 (Coverage For Injury To Co-Employee(s), fully refer-to-company) immediately before Rule A2 | Different coverage -- not a Stop Gap deviation |

Not resolved in source docs -- whether WA's newest package on disk (`GL_WA_20260101_V02`, no
2027-04-01 edition present in this corpus pull) differs from a live 2027-04-01 WA filing that
simply was not pulled (GATE-STOPGAP-EMPLOYERS-LIABILITY.md Section 5).

---

## Supporting lookups

| Rule | Matrix | Keys | Notes |
|---|---|---|---|
| `LookupILFPremOpsWithArgs` | Premises/Operations ILF table | `assignment`, `accidentLimit`, `diseaseLimit` (Stop Gap's own submitted limits, substituted for Prem/Ops' own) | Reused directly -- not a Stop-Gap-specific table |
| `LookupStopGapRate` | `StopGapRateDef` / `StopGapRate` | `StateCode`, `ClassificationType` | State-keyed only; CW layer is 0 rows at every edition checked |
| `LookupStopGapStatCode` | `StopGapStatCodeDef` / `StopGapStatCode` | `StateCode`, `ClassificationType` | Maps the same 5 `ClassificationType` values to 2 stat codes: `92400` (Mfg/Contracting) and `92405` (all other) -- confirms the same .03/.02 boundary a second way |
| (unread) | `StopGapManProcContServRiskStatCodeDef`, `StopGapRisksOtherThanManProcContServRiskStatCodeDef` | -- | 0 rows, no reader found -- orphan tables, same shape as `RailroadLossCost` (`GATE-335-RAILROAD-PROTECTIVE.md` Section 3) |
| `DomainStopGapBIByAccidentOrByDisease` | domain table, not a rate lookup | -- | 13 whole-dollar bands, $25,000-$10,000,000 (ND) -- the legal values for `LimitBodilyInjuryByAccident`, `LimitBodilyInjuryByDiseaseEachEmployee`, `LimitBodilyInjuryByDiseaseAggregate` |

---

## Quick reference -- end-to-end

```
[Classification level, run once per Prem/Ops classification via ErcRate]

StopGapIncrdLimitFactor = LookupILFPremOpsWithArgs(assignment, accidentLimit, diseaseLimit)
                                       (Prem/Ops ILF, Rule 23.D; 0.0 if unresolved)

StopGapFactor = LookupStopGapRate(StateCode, ClassificationType)
                                       (0.03 Mfg/Contracting/Servicing, 0.02 all other;
                                        0.0 if the state files no row -- CW is always 0 rows)

calcBaseRateStopGap = StopGapFactor x PremOpsCoverage.BaseRate
                                       (Prem/Ops' own already-computed classification base rate --
                                        an E18 cross-coverage dependency, not a borrowed table)

StopGapFinalRate = round(
    (StopGapIncrdLimitFactorOverride or StopGapIncrdLimitFactor) x calcBaseRateStopGap
    x PackageModFactor x ExperienceRatingModificationFactor x ModToUse
, 3)

StopGapPremium = round(StopGapFinalRate x PremOpsExposureCalc, 0)
                     if LimitBodilyInjuryByAccident == LimitBodilyInjuryByDiseaseEachEmployee
                 | 0.0  otherwise
                                       (Prem/Ops' own already-computed exposure count)

[Policy level, run once per attached Stop Gap endorsement instance]

Premium = sum(StopGapPremium across every classification, every location)
              if LimitBodilyInjuryByAccident == LimitBodilyInjuryByDiseaseEachEmployee
        | round(ManualPremium x PackageModFactor, 0)
              otherwise    <- refer-to-company branch; ManualPremium is submission-supplied,
                              not computed anywhere in this chain

[Summed into the policy total via GeneralLiabilityRules.CalculateTotalPremium]
```

Rounding: `StopGapFinalRate` to 3 decimal places; `StopGapPremium` and the policy-level `Premium`
to 0 decimal places, per the `DecimalPlaces` attributes on the traced `Product` rules
(GATE-STOPGAP-EMPLOYERS-LIABILITY.md Section 2).

---
