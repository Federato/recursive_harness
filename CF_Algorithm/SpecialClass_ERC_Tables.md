# Special Class — Required ERC Tables

**Source ERC package:** `C:\Projects\ISO_ERC_Files\CF\20260601\CFCW20260601V01`
**Line:** Commercial Property (CF), Countrywide, edition 06-01-2026, V01
**Derived from:** `CauseOfLoss_SpecialClass_RatingAlgorithms.md`
**Documented:** 2026-08-19

This lists every ERC rate table (CW and/or state-filed) required to rate Special Class coverage, resolved by tracing `SetBlanketRatesAndFactors`, `SetBGIRatesAndFactors`, `SetBGIIRatesAndFactors`, `SetBroadRatesAndFactors`, `SetSpecialRatesAndFactors`, and the four core premium rulesets in `CommercialPropertySpecialClassRules.Rule.xml` / `CommercialPropertySpecialClass{BasicGroupI,BasicGroupII,Broad,Special}CoverageRules.Rule.xml` down to each `Lookup`'s `MatrixFromConstant`, and verified against the actual files in `CFCW20260601V01\Rate Tables`. All four core forms (not just Basic Group I) are covered, since the chains are short enough to trace fully in one pass.

All tables follow the two-pass `FirstNonNull(state row, "CW" row)` lookup pattern — a state can override any of these with its own row, but if it doesn't, a CW row is required for the lookup to resolve.

---

## Class-description conversion tables (Special Class-specific)

| Table | Used for | Keys | Verified rows (CW) |
|---|---|---|---|
| `SpecialClassDescriptionConvertedOption` | Converts the free-text `ClassDescription` to one of 71 filed "OptionNN" codes, consumed by the Basic Group I base-rate lookup | State\|CW, `ClassDescription` | 71 data rows |
| `SpecialClassBasicGroupIINumber` | Basic Group II's class-specific hazard/numeric value, keyed directly on `ClassDescription` (not a converted option) | State\|CW, `ClassDescription` | 71 data rows |

These two tables are the mechanism by which Special Class substitutes a class-code/construction-code rating basis with a named-class rating basis. Neither exists in the Building datadef group.

## Rate-build-up tables (state-or-CW keyed)

| Table | Used for | Keys | Note |
|---|---|---|---|
| `BasicGroupIRateSpecialClass` | Basic Group I base rate | State\|CW, `SpecialClassDescConvertedOption`, `ProtectionClassToUse` | Special-Class-only table; 213 CW data rows; **no construction key** |
| `BasicGroupIIRate` | Basic Group II base rate | State\|CW, `BasicGroupIIRatingTerr`, `BasicGroupIISymbol`, `"Bldg"` | **Same table Building's Basic Group II uses** |
| `LowestBasicGroupIIRate` | Basic Group II's wind/hail-excluded floor rate | State\|CW, `BasicGroupIISymbol`, `"Bldg"` | Same table Building uses |
| `BroadFormBaseRate` | Broad base rate | State\|CW, literal `"Frame"`, `"Bldg"` | Same table Building/PersProp use, but Special Class always reads the **`"Frame"` row only** (CW 0.015) — construction-blind, confirmed by the literal `Constant` key in `LookupBroadFormBaseRate` |
| `SpecialBuildingRate` | Special form base rate | State\|CW, `"Y"` | **Same table Building's Special form uses — confirmed empty of CW data** (header row only; no `CW` row filed in this package) |
| `SpecialBldgTheftExclusionFactor` | Special form theft-exclusion credit | State\|CW, `"Y"` | Same table Building uses; CW value **0.88** |
| `VandalismExclFactor` | Basic Group I COL-adjustment factor | State\|CW, `ClassCode` (raw class code, not the converted option) | Confirmed present |
| `WindstormOrHailExclFactor` | Basic Group II COL-adjustment factor (wind/hail-excluded branch) | State\|CW, `BasicGroupIISymbol` | Confirmed present |

## Coinsurance / LOI / deductible tables

| Table | Used for | Keys | Note |
|---|---|---|---|
| `CoinsuranceFactor` | Standard coinsurance factor (80/90/100%), shared by BGI, Broad, Special | State\|CW, `Coinsurance` (or `BlktCoinsurance` for the blanket branch) | Same table Building uses |
| `LessThan80PctMultiplicativeFactor` | Coinsurance <80% branch, shared by BGI/Broad/Special/EQ | State\|CW, `"Y"` | Same table Building uses |
| `BasicGroupIIFlatCoinsuranceFactor` | Basic Group II's own flat coinsurance factor (50/60/70/None) | State\|CW, `"Y"` | CW value **1.5** — a surcharge, not a credit |
| `DeductibleByLocationFactor` | By-location deductible factor, shared across BGI/Broad and copied into BGII's/Special's own datadef names | State\|CW, `"Y"` | CW value **0.995**; flat statewide, no ded/limit key (unlike Building's namesake table which may carry more keys — not independently re-verified here) |
| `DeductibleFactor` | Standard deductible factor, used by all four forms | `ded`, `limit` (=`TotAmtInsuranceToUse` or `SpecialTotAmtInsuranceToUse`/`...IncludingTheft...`), `causeOfLossDed` params | Same table Building uses (`"Basic Group I"`, `"Basic Group II"`, `"Other Cause Of Loss"` cause-of-loss-ded values observed) |
| `Deductible250Factor` | Flat $250 deductible factor, used by BGI/BGII/Broad/Special | State\|CW, `causeOfLoss` param (`"Basic"`, `"Broad"`, `"Special"`, `"All Other"`) | CW values: Basic 1.05, Broad 1.05, Special 1.10, All Other 1.10 |

## Unused-but-computed table

| Table | Used for | Keys | Note |
|---|---|---|---|
| `ProtectionClassFactor` | Protection class rate factor | State\|CW, `../../ProtectClass`, `1` | Computed by `SetProtectionClassFactor` (line 5724) but **not consumed by any of the four core rate chains** in this ruleset — protection class instead enters Basic Group I's rate via a base-rate-table key (`ProtectionClassToUse`). See open question in the algorithms doc. |

## Premium-level tables

| Table | Used for |
|---|---|
| `CyberIncidentExclusionFactors` (or equivalent, per-form: BGI/BGII/Broad/Special) | Cyber exclusion factor — read as a policy-level copy, same convention as Building; not independently re-verified as a distinct table name per form in this pass |
| `CyberIncidentExclusionWithEnsuingCauseOfLossExceptionsFactors` (or equivalent) | Cyber exclusion-with-exceptions factor — same convention |

---

## Not ERC tables

`IRPMFactor`, `PackageModFactor`, and `MultiPremiumAndDispersionCreditFactor` are policy-level user/schedule-rated inputs copied down from the policy level (`SetMultiPremiumAndDispersionCreditFactor`, line 2106, uses `rul:Copy` from `../../../../MultiPremiumAndDispersionCreditFactor`, not `rul:Lookup`) — not filed rate tables. Same convention as Building.

`StdPropPolGroupIFactor` and `StdPropPolGroupIIFactor` are likewise `rul:Copy` from `../../../../StdPropPolBasicGroupIFactor` / `...IIFactor` (lines 1986-2017) — policy-level inputs, not ERC tables. Confirmed no `StdPropPolBasicGroupIFactor.RateTable.csv` or `...IIFactor.RateTable.csv` exists in `Rate Tables`.

`MarginClauseRatingFactor` (via `LookupMarginClauseFactor`, line 11368) exists as a table but was not confirmed as consumed by any of the four core rate chains traced — it is set during shared prep (`SetMarginClauseFactor`) but appears to belong to the Blanket Insurance Margin Clause endorsement (`CommercialPropertySpecialClassLimitationOnLossSettlementBlanketInsuranceMarginClauseRules.Rule.xml`), which is out of scope for this pass.

---

## Verification

All tables listed under "Class-description conversion," "Rate-build-up," "Coinsurance / LOI / deductible," and "Unused-but-computed" above were confirmed present as `<TableName>.RateTable.csv` (with matching `<TableName>Def.RateTableDef.xml`, except where noted) in `CFCW20260601V01\Rate Tables`, by resolving each `Lookup`'s `MatrixFromConstant` attribute back to a file on disk:

```
BasicGroupIRateSpecialClass.RateTable.csv          -- 213 CW data rows
BasicGroupIIRate.RateTable.csv
LowestBasicGroupIIRate.RateTable.csv
BroadFormBaseRate.RateTable.csv                     -- CW,Frame,Bldg,0.015 confirmed
SpecialBuildingRate.RateTable.csv                   -- header row only, no CW data row
SpecialBldgTheftExclusionFactor.RateTable.csv        -- CW,Y,0.88
BasicGroupIIFlatCoinsuranceFactor.RateTable.csv      -- CW,Y,1.5
SpecialClassBasicGroupIINumber.RateTable.csv         -- 71 CW data rows
SpecialClassDescriptionConvertedOption.RateTable.csv -- 71 CW data rows
VandalismExclFactor.RateTable.csv
WindstormOrHailExclFactor.RateTable.csv
DeductibleByLocationFactor.RateTable.csv             -- CW,Y,0.995
CoinsuranceFactor.RateTable.csv                      -- CW 80%/90%/100% = 1 / 0.95 / 0.9
LessThan80PctMultiplicativeFactor.RateTable.csv      -- CW,Y,1.5
Deductible250Factor.RateTable.csv                    -- CW Basic/Broad/Special/All Other = 1.05/1.05/1.10/1.10
DeductibleFactor.RateTable.csv
ProtectionClassFactor.RateTable.csv                  -- present but unconsumed downstream
```

### Open items surfaced during verification

- **`SpecialBuildingRate.RateTable.csv` has no `CW` data row** (header only) — the Special form's base rate is unresolved at countrywide level for *both* Building and Special Class, since they share this exact table. Any state implementation must file its own row, or the base rate (and therefore the entire Special-form rate chain) resolves to null/zero.
- **`BasicGroupIISymbol`** (the Basic Group II base-rate/lowest-rate lookup key) has no assignment rule anywhere in `CommercialPropertySpecialClassRules.Rule.xml` — its origin (data entry field vs. a copy from a rule file outside this datadef group) could not be confirmed in this pass.
- The Cyber Incident Exclusion table names per form (`CyberIncidentExclusionFactorBGI`/`BGII`/`Broad`/`Special` and their "...COLExcptns..." counterparts) were confirmed as **policy-level reads** (five levels up the datadef tree, matching Building's convention) but the underlying filed table name(s) were not independently re-verified against a `.RateTable.csv` in this pass — carried over from the Building doc's treatment rather than freshly confirmed for Special Class.
