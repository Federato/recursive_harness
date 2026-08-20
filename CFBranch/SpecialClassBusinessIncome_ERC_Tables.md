# Special Class Business Income — Required ERC Tables

**Source ERC package:** `C:\Projects\ISO_ERC_Files\CF\20260601\CFCW20260601V01`
**Line:** Commercial Property (CF), Countrywide, edition 06-01-2026, V01
**Derived from:** `CauseOfLoss_SpecialClassBusinessIncome_RatingAlgorithms.md`
**Documented:** 2026-08-19

This lists every ERC rate table required to rate Special Class Business Income coverage (Basic Group I,
Basic Group II, Broad, Special, and the Agreed Value Earthquake add-on), resolved by tracing
`SetBlanketRatesAndFactors` and its five `Set*RatesAndFactors` chains, plus each premium coverage file's
`SetPremium`, down to every `Lookup`'s `MatrixFromConstant` in
`Rules\CommercialPropertySpecialClassBusnIncomeRules.Rule.xml` and the individual coverage-rule files, and
verified directly against the CSV files in `CFCW20260601V01\Rate Tables`.

Per this project's standing rule (BUILD-LOG.md Entry 3), **every table below was checked for both file
existence and actual data-row count** — "the file exists" and "the file has a usable row" are reported as
separate facts throughout.

Two forms (Basic Group I, Earthquake) do not resolve independent base-rate tables at all — they cross-
reference the coinsured Special Class item's own already-computed `BasicGroupIRate` / `EQRate` datadefs, not
a table lookup. Those cross-references are noted, not listed as tables, since there is no table for them to
resolve.

---

## Rate-build-up tables (state-or-CW keyed)

| Table | Used for | Keys | File exists | Data rows (excl. header) |
|---|---|---|---|---|
| *(none)* — `BasicGroupIRate` cross-referenced from `../../BasicGroupIRate` (coinsured Special Class item), not looked up | Basic Group I rate | n/a — datadef copy, not a matrix lookup | n/a | n/a |
| `BasicGroupIIRate` | Basic Group II base rate | State\|CW, `BasicGroupIIRatingTerr`, `BasicGroupIISymbol`, "Bldg" | **Yes** — `BasicGroupIIRate.RateTable.csv` | **0 — header-only.** Confirmed `wc -l` = 1 (header row only). Basic Group I base rate is unresolvable at CW for this coverage without a state filing. Shared table — same file Building and plain Business Income both read. |
| `LowestBasicGroupIIRate` | Basic Group II wind/hail-excluded floor rate | State\|CW, `BasicGroupIISymbol`, "Bldg" | **Yes** — `LowestBasicGroupIIRate.RateTable.csv` | **0 — header-only.** Confirmed `wc -l` = 1. Same gap as above; also affects Building and plain Business Income (shared file). |
| `BroadFormBaseRate` | Broad base rate | State\|CW, **hard-coded literal `"Frame"`**, covType ("Business Income Without Extra Expense" \| "All Other") | **Yes** — `BroadFormBaseRate.RateTable.csv` | **30 data rows** (31 lines incl. header). Confirmed CW rows resolve for the keys this rule actually uses: `("CW","Frame","Business Income Without Extra Expense",0.011)`, `("CW","Frame","All Other",0.023)`. Table also carries `Bldg` (0.015), `PersProp` (0.021), `BldrRisk` (0.012) rows for other coverage types — shared table across Building, Personal Property, plain Business Income, Special Class Building, and this group. |
| `SpecialFormIncldgTheftTimeElementBaseRate` | Special base rate | State\|CW, **hard-coded literal `"Frame"`**, covType, **hard-coded literal `"Other than Apartments and Condominiums"`** | **Yes** — `SpecialFormIncldgTheftTimeElementBaseRate.RateTable.csv` | **24 data rows** (25 lines incl. header). Confirmed CW rows resolve for the keys this rule actually uses: `("CW","Frame","Business Income Without Extra Expense","Other than Apartments and Condominiums",0.033)`, `("CW","Frame","All Other","Other than Apartments and Condominiums",0.047)`. The table's "Apartments and Condominiums" rows (e.g. 0.016, 0.029) also exist but are unreachable by this rule's hard-coded key — see rating-algorithms doc's open questions. Shared table — same file plain Business Income reads with a data-derived key. |
| *(none)* — `EQRate` cross-referenced from `../../EQRate` (coinsured Special Class item), not looked up | Earthquake rate | n/a — datadef copy, not a matrix lookup | n/a | n/a |
| `SpecialLeaseHoldTimeElementTheftExclusionFactor` | Special theft-exclusion factor | State\|CW, `ApartmentCondoIndicator` | **Yes** — `SpecialLeaseHoldTimeElementTheftExclusionFactor.RateTable.csv` | **2 data rows** (3 lines incl. header): `("CW","Yes",0.96)`, `("CW","No",0.86)`. |
| `VandalismExclFactor` | Basic Group I COL-adjustment factor | State\|CW (+ additional keys, not fully traced) | **Yes** — `VandalismExclFactor.RateTable.csv` | **161 data rows** (162 lines incl. header) — large multi-key table; full key structure not traced in this pass (shared with Building/plain BI's own `VandalismExclFactor`). |
| `WindstormOrHailExclFactor` | Basic Group II wind/hail-excluded rebuild factor | State\|CW, `BasicGroupIISymbol` | **Yes** — `WindstormOrHailExclFactor.RateTable.csv` | **4 data rows** (5 lines incl. header): symbols A (0.35), AA (0.35), AB (0.315), B (0.315) confirmed present. |

## Shared "Factor" tables (Basic Group I / II only)

| Table | Used for | Keys | File exists | Data rows (excl. header) |
|---|---|---|---|---|
| `BusnIncomeFactor` | `TypeOfRiskFactor` — the primary component of the shared `Factor` | State\|CW, `CovType`, `TypeOfRisk`, `CoinsuranceToUse` | **Yes** — `BusnIncomeFactor.RateTable.csv` | **131 data rows** (132 lines incl. header). Identical shared table to plain Business Income's own `BusnIncomeFactor` lookup — not duplicated per coverage group. |
| `MaxPeriodOfIndemnityFactor` | `Factor` when `MaxPeriod = "Yes"` | State\|CW, `CovType`, `TypeOfRisk` | **Yes** — `MaxPeriodOfIndemnityFactor.RateTable.csv` | **22 data rows** (23 lines incl. header). |
| `MonthlyLimitOfIndemnityFactor` | `Factor` when `MonthlyLimitOfIndemnity <> "Not Applicable"` | State\|CW, `CovType`, `TypeOfRisk`, `MonthlyLimitOfIndemnity` | **Yes** — `MonthlyLimitOfIndemnityFactor.RateTable.csv` | **60 data rows** (61 lines incl. header). |
| `ExtraExpenseFactor` | `Factor` when `CovType = "Extra Expense Only"` | State\|CW, `ExtraExpenseLimitOnLossPayment` | **Yes** — `ExtraExpenseFactor.RateTable.csv` | **4 data rows** (5 lines incl. header): `100%,100%,100%` (3.4), `40%,80%,100%` (1.7), `35%,70%,100%` (1.62), `Expanded Limits on Loss Payments` (0). |

## Earthquake sub-limit tables

| Table | Used for | Keys | File exists | Data rows (excl. header) |
|---|---|---|---|---|
| `EarthquakeSubLimitTimeElementFactor` | Sub-limit time-element factor feeding `EQFactor` | State\|CW, constant "Y" | **Yes** — `EarthquakeSubLimitTimeElementFactor.RateTable.csv` | **1 data row** (2 lines incl. header): `("CW","Y",0.999)`. |
| `BusnIncomeFactor` (reused for EQ sub-limit type-of-risk factor via `LookupEQSubLimitBusnIncomeFactor`) | EQ sub-limit type-of-risk component | State\|CW, `CovType`, TypeOfRisk param, `EQSubLimitCoinsurance` | **Yes** — same file as above | 131 data rows (same table, reused with a different 4th key input) |
| *(Other EQ sub-limit percent/coinsurance/type-risk-combination tables referenced by `SetEQSubLimitPercent`, `SetEQSubLimitCoinsurance`, `SetEQSubLimitTypeRiskCombination1/2Factor`)* | Sub-limit machinery | not fully traced in this pass — out of scope per the rating-algorithms doc's Earthquake section | not verified | not verified |

## Agreed Value Earthquake table

| Table | Used for | Keys | File exists | Data rows (excl. header) |
|---|---|---|---|---|
| `AgreedValueFactorBusnIncome` | Agreed Value surcharge factor, `(Factor - 1)` | State\|CW, constant "Y" | **Yes** — `AgreedValueFactorBusnIncome.RateTable.csv` | **1 data row** (2 lines incl. header): `("CW","Y",1.1)`. Identical shared table to plain Business Income's own Agreed Value Earthquake premium file. |

## Premium-level tables

| Table | Used for | Keys | File exists | Data rows (excl. header) |
|---|---|---|---|---|
| `CyberIncidentExclusionFactors` | Cyber exclusion factor, keyed by cause-of-loss group | State\|CW, `CausesOfLossOrPerilGroupPremium` ("Basic Group I" / "Basic Group II" / "Broad" / "Special" / "Earthquake" / ...) | **Yes** — `CyberIncidentExclusionFactors.RateTable.csv` | **8 data rows** (9 lines incl. header). Confirmed CW rows for all five forms this coverage group needs: Basic Group I 0.995, Basic Group II 0.995, Broad 0.995, Special 0.995, Earthquake 1.0 (plus Flood/Spoilage/Equipment Breakdown rows for other coverages, same shared file). |
| `CyberIncidentExclusionWithEnsuingCauseOfLossExceptionsFactors` | Cyber exclusion-with-exceptions factor | State\|CW, `CausesOfLossOrPerilGroupPremium`, `TypeOfLimit`, `AggregateLimit` | **Yes** — `CyberIncidentExclusionWithEnsuingCauseOfLossExceptionsFactors.RateTable.csv` | **32 data rows** (33 lines incl. header). Confirmed CW rows for Basic Group I (1.0), Basic Group II (1.0), Broad (1.0), Special (0.998), Earthquake (1.0) under `"Full Limit","No"` — additional rows exist for other `TypeOfLimit`/`AggregateLimit` combinations, not individually enumerated here. |

## Not ERC tables

`IRPMFactor`, `PackageModFactor`, and `MultiPremiumAndDispersionCreditFactor` are policy-level
user/schedule-rated inputs copied down from the policy level, not filed rate tables — same as every other
coverage group in this package. (`MultiPremiumAndDispersionCreditFactor` is populated during shared prep but
is never actually multiplied into any of this coverage group's premium formulas — see the rating-algorithms
doc's structural-differences section.)

`BasicGroupIRate` and `EQRate` (the two cross-referenced datadefs) are **not** ERC rate tables from this
coverage group's perspective — they are the coinsured Special Class item's own computed rate values,
resolved by that item's own `CommercialPropertySpecialClassRules.Rule.xml` rate chain (out of scope for this
pass; the Special Class Building document covers that chain's own required tables separately, though it does
not enumerate a dedicated tables companion doc as of this writing).

---

## Verification method

All tables above were confirmed present as `<TableName>.RateTable.csv` in
`CFCW20260601V01\Rate Tables`, by resolving every `RunRule`/`Lookup` reference from `SetBlanketRatesAndFactors`,
the five `Set*RatesAndFactors` chains, `SetFactor`, and each premium coverage file's `SetPremium` in
`CommercialPropertySpecialClassBusnIncomeRules.Rule.xml` and the `CommercialPropertySpecialClassBusnIncome*
CoverageRules.Rule.xml` files, down to each `Lookup`'s `MatrixFromConstant` attribute. Row counts were
verified directly against file content (`wc -l` plus targeted `grep` for the specific keys each rule actually
uses), not inferred from file existence alone — per BUILD-LOG.md Entry 3's standing correction.

**Two tables resolve to zero usable CW rows**: `BasicGroupIIRate` and `LowestBasicGroupIIRate` are both
header-only. This blocks Basic Group II base-rate resolution at the countrywide level for this coverage
group, exactly as it does for Building and plain Business Income (all three share the same physical CSV
files). Every other table checked in this pass carries at least the specific CW row(s) this coverage group's
rules actually key into.

**One table has a partially-unreachable row set from this coverage group's perspective**:
`SpecialFormIncldgTheftTimeElementBaseRate` carries both "Apartments and Condominiums" and "Other than
Apartments and Condominiums" rows, but Special Class Business Income's `SetSpecialBaseRate` hard-codes the
"Other than..." key literal — so the "Apartments and Condominiums" rows, while present and filed, can never
be selected by this coverage group's rating logic (they remain reachable from plain Business Income's own
rules against the same file). See the rating-algorithms doc's open questions.

---
