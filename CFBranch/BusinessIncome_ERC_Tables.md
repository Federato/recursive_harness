# Business Income — Required ERC Tables

**Source ERC package:** `C:\Projects\ISO_ERC_Files\CF\20260601\CFCW20260601V01`
**Line:** Commercial Property (CF), Countrywide, edition 06-01-2026, V01
**Derived from:** `CauseOfLoss_BusinessIncome_RatingAlgorithms.md`
**Documented:** 2026-08-19

This lists every ERC rate table required to rate the plain `CommercialPropertyBusinessIncome` group
(Basic Group I, Basic Group II, Broad, Special, Earthquake, plus the Agreed Value and Extended Period of
Indemnity add-ons), resolved by tracing `SetBlanketRatesAndFactors` and its descendants in
`CommercialPropertyBusinessIncomeRules.Rule.xml` down to each `Lookup`'s `MatrixFromConstant`, plus the
add-on coverage rule files. Every table below was checked for **both** file existence and actual data-row
count against `CFCW20260601V01\Rate Tables` — per BUILD-LOG.md Entry 3, "exists" and "has a usable CW row"
are different claims and only the second is load-bearing. Row counts exclude the header row.

All tables follow the two-pass `FirstNonNull(state row, "CW" row)` lookup pattern.

---

## Tables shared with Building (cross-referenced, not looked up independently by Business Income)

Basic Group I, Basic Group II, and Earthquake do not run their own class/construction/territory lookups —
they read the coinsured Structure's own already-computed rate datadefs (`BasicGroupIBaseRate`,
`BasicGroupIISymbolToUse`/`BasicGroupIIRatingTerr`, `EQBaseRate`) directly via relative datadef paths. The
tables those Building-side lookups depend on are documented in `BasicGroupI_ERC_Tables.md`; they are not
re-verified here except where Business Income also queries them directly (Basic Group II — see below).

| Table | Used for | Verified rows | Note |
|---|---|---|---|
| `BasicGroupIIRate` | Basic Group II base rate (`LookupBasicGroupIIRate`, line 13482) | **0 data rows — header only** | Same table Building uses. `BasicGroupII` rate is unresolvable at CW for both coverages. |
| `LowestBasicGroupIIRate` | Wind/hail-excluded floor rate (`LookupLowestBasicGroupIIRate`, line 13795) | **0 data rows — header only** | Feeds the wind/hail-excluded branch of `SetBasicGroupIICauseOfLossAdjustment`; also unresolvable at CW. |

**Correction carried forward from the Building pass (`BasicGroupI_ERC_Tables.md`).** `BasicGroupIRate.RateTable.csv`
is also header-only (confirmed there). Because Basic Group I Business Income reads the Structure's
`BasicGroupIBaseRate` directly rather than re-deriving it, Basic Group I Business Income inherits this same
unresolvability at the countrywide level — its rate cannot be computed without a state-specific filing
layered on top of *both* the Building's base rate table and Business Income's own adjustment-factor table
(see next section).

---

## Business-Income-specific rate-build-up tables

| Table | Used for | Keys | Verified rows |
|---|---|---|---|
| `BaseRateAdjustmentFactor` | BGI/BGII rate multiplier (`LookupBaseRateAdjustmentFactor`, line 13433) | State\|CW, cause-of-loss ("Basic Group I" / "Basic Group II") | **0 data rows — header only** |
| `BroadFormBaseRate` | Broad base rate (`LookupBroadFormBaseRate`) | State\|CW, ConstructionTypeToUse, covType ("Business Income Without Extra Expense" / "All Other") | 30 data rows (shared table w/ Building; confirmed Business Income covType rows present, e.g. Frame 0.011) |
| `SpecialFormIncldgTheftTimeElementBaseRate` | Special base rate, non-Builders-Risk (`LookupSpecialFormIncldgTheftTimeElementBaseRate`, line 13918) | State\|CW, ConstructionTypeToUse, covType, SpecialIncludingTheftTypeRisk | 24 data rows |
| `SpecialFormBldrsRiskTimeElementBaseRate` | Special base rate, Builders Risk class 1150 | State\|CW, "Y" | 1 data row (CW = 0.018) |
| `SpecialLeaseHoldTimeElementTheftExclusionFactor` | Special theft-exclusion factor | State\|CW, ApartmentCondoIndicator | 2 data rows |
| `BusnIncomeFactor` | Shared coinsurance/type-of-risk `Factor` for BGI/BGII (`LookupBusnIncomeFactor`, line 13635) | State\|CW, CovType, TypeOfRisk, CoinsuranceToUse | 131 data rows |
| `MaxPeriodOfIndemnityFactor` | `Factor`, max-period branch | State\|CW, ... | 22 CW rows |
| `MonthlyLimitOfIndemnityFactor` | `Factor`, monthly-limit branch | State\|CW, ... | 60 CW rows |
| `ExtraExpenseFactor` | `Factor`, Extra-Expense-Only branch | State\|CW, ExtraExpnLimitOnLossPymts | 4 data rows |
| `SprinklerLeakageExclNonSprinkleredRate` | BGI COL adjustment subtraction | State\|CW | 1 data row (single statewide constant) |
| `SprinklerLeakageExclSprinkleredFactor` | BGI COL adjustment factor | State\|CW | 12 data rows |
| `VandalismExclFactor` | BGI/BGII COL adjustment factor | State\|CW | 161 data rows |
| `WindstormOrHailExclFactor` | BGII wind/hail-excluded rebuild | State\|CW | 4 data rows |
| `BldrsRiskFactorBusnIncome` | Builders Risk rate modifier (BGI/BGII/EQ COL adjustment) | State\|CW, "Y" | 1 data row |
| `StoryModFactorTimeElement` | Story modification (feeds `StoryModFactor`, EQ COL adjustment) | State\|CW, ... | 6 data rows |
| `EQSprinklerLeakageOnlyBldgFactor` | EQ COL adjustment factor | State\|CW, "Y" | 1 data row |
| `EarthquakeSubLimitTimeElementFactor` | EQ sub-limit factor | State\|CW, ... | 1 data row |
| `ExpandedLimitsOnLossPaymentFactor` | Expanded Limits on Loss Payment endorsement factor | State\|CW, ... | 3 data rows |
| `WatercraftExclusionBuybackConstructionOptionsConverted` | Watercraft exclusion buyback construction option | State\|CW, ... | 7 data rows |
| `BusnIncomeEducationalInstitutionsExtOfRecoveryFactor` | Educational Institutions extension-of-recovery factor | State\|CW, ... | 13 data rows |
| `TuitionAndFeesFactor` | Educational Institutions tuition/fees factor | State\|CW, ... | 16 data rows |

> **`BaseRateAdjustmentFactor` is header-only at CW — zero data rows.** This is the multiplier
> `SetBGIBaseRateAdjustmentFactor` / `SetBGIIBaseRateAdjustmentFactor` apply on top of the Building's own
> base rate. Combined with `BasicGroupIRate` and `BasicGroupIIRate` also being header-only (confirmed
> above and in `BasicGroupI_ERC_Tables.md`), **Basic Group I and Basic Group II Business Income rating is
> doubly unresolvable at the countrywide level in this package edition** — both the underlying Building
> rate and the Business-Income-specific adjustment factor return null without a state-specific filing.
> `LowestBasicGroupIIRate` (the wind/hail-excluded floor) is also header-only, so the fallback path is
> equally unresolvable.
>
> By contrast, Broad and Special's own dedicated base-rate tables (`BroadFormBaseRate`,
> `SpecialFormIncldgTheftTimeElementBaseRate`, `SpecialFormBldrsRiskTimeElementBaseRate`) **do** carry CW
> data rows — those two forms are resolvable at the countrywide level even though Basic Group I/II and
> Earthquake are not.

---

## Add-on coverage tables (Agreed Value, Extended Period of Indemnity)

| Table | Used for | Keys | Verified rows |
|---|---|---|---|
| `AgreedValueFactorBusnIncome` | Agreed Value surcharge factor | State\|CW, "Y" | 1 data row |
| `ExtendedPeriodFactor` | Extended Period of Indemnity surcharge factor | State\|CW, ExtendedPeriod | 11 data rows |

Both feed the `(Factor - 1) x Rate x (Limit/100)` incremental-surcharge formula documented in the
Rating Algorithms doc — a mechanism unique to these two add-ons among everything traced in this package
so far.

---

## Coinsurance-scan support (not a rate table)

`SetCoinsuranceToUse` resolves `CoinsuranceToUse` by scanning
`../../../../../../CommercialPropertyBlanketRatingTable` for a matching `UnitNumber`, or copying
`BlktCoinsurance` directly for multi-unit-blanket-rated submissions — this is a policy-data scan, not an
ERC rate-table lookup, and has no CSV to verify.

---

## Cyber / premium-level tables

| Table | Used for | Verified rows |
|---|---|---|
| `CyberIncidentExclusionFactors` | Cyber exclusion factor, keyed by cause-of-loss group | 8 data rows |
| `CyberIncidentExclusionWithEnsuingCauseOfLossExceptionsFactors` | Cyber exclusion-with-exceptions factor | 32 data rows |

Same two tables Building and Personal Property use, keyed by cause-of-loss group string (e.g. "Basic
Group I", "Broad", "Special").

---

## Statistical / subline tables (reporting only, not rate-affecting)

| Table | Verified rows |
|---|---|
| `SublineBasicGroupI` | 1 data row |
| `SublineBasicGroupIExcludingSprinklerLeakage` | 1 data row |
| `SublineBasicGroupIExcludingVandalism` | 1 data row |
| `SublineBasicGroupIExcludingVandalismAndSprinklerLeakage` | 1 data row |
| `SublineBasicGroupII` | 1 data row |
| `SublineBasicGroupIIExcludingWindstormOrHail` | 1 data row |
| `SublineBroadForm` | 1 data row |
| `SublineSpecialFormExcludingTheft` | 1 data row |
| `SublineSpecialFormIncludingTheft` | 1 data row |
| `AllOtherDeductibleStatCode` | 24 data rows |
| `BldgCodeEffectivenessGradeStatCode` | 22 data rows |
| `CoinsuranceStatCode` | 10 data rows |
| `MoldDamageCoverageStatCode` | 8 data rows |
| `MoldDamageNoCoverageStatCode` | 1 data row |
| `TimeElementAllOtherCoverageCode` | 1 data row |
| `TimeElementExtraExpenseCoverageCode` | 1 data row |
| `TimeElementOtherThanRentalCoverageCode` | 1 data row |
| `TimeElementRentalCoverageCode` | 1 data row |
| `ScheduleRatedRatingIdentificationCode` | 1 data row |
| `SprinkleredScheduleRatedRatingIdentificationCode` | 1 data row |
| `SubStandardClassRatedRatingIdentificationCode` | 1 data row |
| `ClassRatedRatingIdentificationCode` | 1 data row |
| `BlktClassRatedRatingIdentificationCode` | 1 data row |
| `BlktScheduleRatedRatingIdentificationCode` | 1 data row |
| `BlktSprinkleredScheduleRatedRatingIdentificationCode` | 1 data row |
| `BlktSubStandardClassRatedRatingIdentificationCode` | 1 data row |

These "1 data row" tables are single-value statewide constants (their key shape is `State|CW` + one
constant such as `"Y"`) — a single CW row is a complete, resolvable table for that shape. This is a
different situation from `BasicGroupIIRate` / `LowestBasicGroupIIRate` / `BaseRateAdjustmentFactor`, whose
key shape requires a specific class/symbol/cause-of-loss combination and genuinely has **zero** rows for
any key.

---

## Not ERC tables

`IRPMFactor`, `PackageModFactor`, `MultiPremiumAndDispersionCreditFactor`, and `LossCostMultiplier` are
policy-level user/schedule-rated inputs copied down from the policy level, not filed rate tables — same
as documented in `BasicGroupI_ERC_Tables.md`.

---

## Deductible tables — explicitly absent

No general per-dollar deductible factor table (`DeductibleFactor`, `Deductible250Factor`,
`DeductibleByLocationFactor` equivalents) is referenced anywhere in
`CommercialPropertyBusinessIncomeRules.Rule.xml`'s `MatrixFromConstant` list. The only "Deductible"-named
constructs in the file are the Earthquake flat-dollar-deductible endorsement attach/detach rules
(`CommercialPropertyEarthquakeAndVolcanicEruptionCoverageWithFlatDollarDeductibleBusnIncome` and its
sub-limit variant) — a separate mechanism scoped to those two EQ endorsement forms only, not traced in
this pass. This is a structural absence, not a gap in verification — see the Rating Algorithms doc's
"Structural differences" section, point 3.

---

## Verification summary

All 45 distinct table names referenced from `CommercialPropertyBusinessIncomeRules.Rule.xml` (via
`MatrixFromConstant`) plus the 2 add-on-coverage tables (`AgreedValueFactorBusnIncome`,
`ExtendedPeriodFactor`) and the 2 Building-shared tables checked independently
(`BasicGroupIIRate`, `LowestBasicGroupIIRate`) were confirmed present as `<TableName>.RateTable.csv` files
in `CFCW20260601V01\Rate Tables`, and every one was opened and row-counted directly (not just
existence-checked) per the standing correction from BUILD-LOG.md Entry 3.

**Three tables are header-only with zero data rows at any key**, all load-bearing for Basic Group I /
Basic Group II / the wind/hail-excluded Basic Group II path:

- `BasicGroupIIRate.RateTable.csv`
- `LowestBasicGroupIIRate.RateTable.csv`
- `BaseRateAdjustmentFactor.RateTable.csv`

All other tables checked carry at least one CW data row.
