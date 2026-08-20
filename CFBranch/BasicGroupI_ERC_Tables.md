# Basic Group I — Required ERC Tables

**Source ERC package:** `C:\Projects\ISO_ERC_Files\CF\20260601\CFCW20260601V01`
**Line:** Commercial Property (CF), Countrywide, edition 06-01-2026, V01
**Derived from:** `CauseOfLoss_Building_RatingAlgorithms.md`
**Documented:** 2026-08-18

This lists every ERC rate table (CW and/or state-filed) required to rate Basic Group I building coverage, resolved by tracing `SetBGIRatesAndFactors` and the Basic Group I premium rules in `CommercialPropertyStructureRules.Rule.xml` down to each `Lookup`'s `MatrixFromConstant`, and verified against the actual files in `CFCW20260601V01\Rate Tables`.

All tables follow the two-pass `FirstNonNull(state row, "CW" row)` lookup pattern — a state can override any of these with its own row, but if it doesn't, a CW row is required for the lookup to resolve.

---

## Rate-build-up tables (state-or-CW keyed)

| Table | Used for | Keys |
|---|---|---|
| `BasicGroupIRate` | Class base rate | State\|CW, ClassCode, ConstructionCode, "Not Applicable", "Building" |
| `RatingTerritoryGroupIFactor` | Territory factor | State\|CW, BasicGroupIRatingTerr |
| `ProtectionClassFactor` | Protection class multiplier | State\|CW, ProtectionClass |
| `SubStdConditionRate` | Substandard-condition rate addend | State\|CW, condition A–E args |
| `VacantBldgPreviousOrIntendedOccup` | Vacant-building rate addend (feeds `VacantBuildingRate`) | State\|CW, occupancy |
| `SprinklerLeakageNotExcluded` | Specific/Tentative rating factor | State\|CW |
| `SprinklerLeakageExclNonSprinkleredRate` | COL adjustment subtraction | State\|CW |
| `SprinklerLeakageExclSprinkleredFactor` | COL adjustment factor | State\|CW |
| `VandalismExclFactor` | COL adjustment factor | State\|CW |
| `StdPropPolGroupIFactor` | COL adjustment factor | State\|CW, "Y" |
| `LimitationsOnCovForRoofSurfacingFactor` | Roof-surfacing ACV factor | State\|CW |

## Coinsurance / LOI / deductible tables

| Table | Used for |
|---|---|
| `CoinsuranceFactor` | Standard coinsurance factor (80/90/100%) |
| `LessThan80PctMultiplicativeFactor` | Coinsurance <80% branch |
| `BasicGroupILOIFactorBldg` | Limit-of-insurance factor |
| `DeductibleByLocationFactor` | Deductible-by-location factor |
| `DeductibleFactor` | Standard deductible factor |
| `Deductible250Factor` | Flat $250 deductible factor |
| `MultiResidentialPropSpecialCreditHeatFactor` | Multi-res credit component |
| `MultiResidentialPropSpecialCreditControlFactor` | Multi-res credit component |

## Premium-level tables

| Table | Used for |
|---|---|
| `CyberIncidentExclusionFactors` | Cyber exclusion factor, keyed by cause-of-loss group ("Basic Group I") |
| `CyberIncidentExclusionWithEnsuingCauseOfLossExceptionsFactors` | Cyber exclusion-with-exceptions factor |

## Statistical / subline tables (reporting only, not rate-affecting)

| Table | Used for |
|---|---|
| `DeductibleStatCode` | Statistical reporting code |
| `SublineBasicGroupI` | Subline code |
| `SublineBasicGroupIExcludingSprinklerLeakage` | Subline when sprinkler leakage excluded |
| `SublineBasicGroupIExcludingVandalism` | Subline when vandalism excluded |
| `SublineBasicGroupIExcludingVandalismAndSprinklerLeakage` | Subline when both excluded |

---

## Not ERC tables

`IRPMFactor`, `PackageModFactor`, and `MultiPremiumAndDispersionCreditFactor` are policy-level user/schedule-rated inputs copied down from the policy level (`SetPackageModFactor` / `SetMultiPremiumAndDispersionCreditFactor` use `rul:Copy`, not `rul:Lookup`) — not filed rate tables.

---

## Verification

All 26 tables above were confirmed present as `<TableName>.RateTable.csv` (with matching `<TableName>Def.RateTableDef.xml`) in `CFCW20260601V01\Rate Tables`, by recursively resolving `RunRule` references from `SetBGIRatesAndFactors` and the Basic Group I premium rules to their leaf `Lookup` calls' `MatrixFromConstant` attribute.

> **Correction, 2026-08-19.** "Confirmed present" above checked file existence only, not whether the
> file carries a data row — a gap surfaced when the Personal Property pass hit the same table and
> checked its content. Verified directly: **`BasicGroupIRate.RateTable.csv` and
> `BasicGroupIIRate.RateTable.csv` are header-only — zero data rows, zero `CW` rows.** Both are shared
> between Building and Personal Property. Practical effect: `LookupBasicGroupIRate` and
> `LookupBasicGroupIIRate` resolve to null at the countrywide level for **both** coverages, for **any**
> class/construction/territory/symbol combination — Basic Group I and Basic Group II base rates are
> entirely unresolvable in this package edition without a state-specific filing layered on top. This
> was not caught by the original verification pass and should be treated as the standing check going
> forward: "table exists" and "table has a usable row" are different claims, and only the second one
> is load-bearing. See `BUILD-LOG.md` Entry 3.
