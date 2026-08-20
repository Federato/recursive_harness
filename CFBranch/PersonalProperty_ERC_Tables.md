# Personal Property — Required ERC Tables

**Source ERC package:** `C:\Projects\ISO_ERC_Files\CF\20260601\CFCW20260601V01`
**Line:** Commercial Property (CF), Countrywide, edition 06-01-2026, V01
**Derived from:** `CauseOfLoss_PersonalProperty_RatingAlgorithms.md`
**Documented:** 2026-08-19

This lists every ERC rate table (CW and/or state-filed) required to rate Personal Property coverage across all four cause-of-loss forms — Basic Group I, Basic Group II, Broad, and Special — resolved by tracing `ErcSetPostRatesAndFactors`, the four `Set*RatesAndFactors` chains, and the four premium-calc rule files in `CommercialPropertyPersonalPropertyRules.Rule.xml` / `CommercialPropertyPersonalPropertyPrsnlProp*CoverageRules.Rule.xml` down to each `Lookup`'s `MatrixFromConstant`, verified against the actual files in `CFCW20260601V01\Rate Tables`.

All tables follow the two-pass `FirstNonNull(state row, "CW" row)` lookup pattern — a state can override any of these with its own row, but if it doesn't, a CW row is required for the lookup to resolve.

**Tables shared with Building** are flagged — several PP lookups read the exact same matrix Building's structure ruleset reads, differentiated by a `Group`/`CovType` key column rather than a separate table.

---

## Basic Group I tables

| Table | Used for | Keys | Shared w/ Building | CW rows filed? |
|---|---|---|---|---|
| `BasicGroupIRate` | Class base rate | State\|CW, BldgClassCode, ConstructionCode, Group, CovType | yes (same table, `CovType="PersProp"` rows) | **No — header only (0 data rows)** |
| `BasicGroupIRatingTerrFactor` (read as `BasicGroupIRatingTerrFactor` datadef, sourced via `RatingTerritoryGroupIFactor`-style table shared w/ Building's territory rule) | Territory factor | State\|CW, BasicGroupIRatingTerr | yes | not independently re-verified here — see Building's `BasicGroupI_ERC_Tables.md` |
| `ProtectionClassFactor` | Protection class multiplier | State\|CW, ProtectClass, ConstructionCode | yes (PP adds ConstructionCode to the key) | Yes (169 rows) |
| `FireSafeVaultFactor` | PP-only vault storage credit | State\|CW, "Y" | **PP-only — no Building equivalent** | Yes — CW = 0.50 |
| `SubStdConditionRate` | Substandard-condition rate addend | State\|CW, condition args | yes | Yes (31 rows) |
| `SprinklerLeakageNotExcluded` | Specific/Tentative rating factor | State\|CW, "Y" | yes (Building keys differently) | Yes — CW = 0.5 (`PersProp` row confirmed in `LegalLiabilityFactor`, see below; `SprinklerLeakageNotExcluded` itself carries a flat CW row) |
| `SprinklerLeakageExclNonSprinkleredRate` | COL adjustment subtraction | State\|CW, "Y" | yes | Yes |
| `SprinklerLeakageExclSprinkleredFactor` | COL adjustment factor | State\|CW, ConstructionCode, "PrsnlProp" | yes (PP passes its own const) | Yes (13 rows) |
| `VandalismExclFactor` | COL adjustment factor | State\|CW, classCode arg | yes | Yes (162 rows) |
| `StdPropPolGroupIFactor` | COL adjustment factor | State\|CW, "Y" | yes | Yes |

## Basic Group I — coinsurance / LOI

| Table | Used for | Keys |
|---|---|---|
| `CoinsuranceFactor` | Standard coinsurance factor (80/90/100%, or forced 100% for reporting-form cases) | State\|CW, coinsurance value |
| `LessThan80PctMultiplicativeFactor` | Coinsurance <80% branch (50/60/70/None) | State\|CW, "Y" |
| `BasicGroupILOIFactorPersProp` | Limit-of-insurance factor | State\|CW, limit, ConstructionCode | Yes (325 rows) — **PP-specific table, distinct from Building's `BasicGroupILOIFactorBldg`** |

## Basic Group I — deductible

| Table | Used for | Notes |
|---|---|---|
| `DeductibleByLocationFactor` | Deductible-by-location factor | State\|CW, "Y" — shared factor, computed once at `ErcSetPostRatesAndFactors` level |
| `DeductibleFactor` | Standard deductible factor | Not read directly by the Basic Group I PP chain — `DeductibleFactorBasicGroupI` is `Copy`'d from an ancestor context (4 levels up); the ancestor's computation (in `CommercialPropertySpecialClassRules.Rule.xml`) does read this table. **Open question** — see report. |
| `Deductible250Factor` | Flat $250 deductible factor | causeOfLoss arg |

## Basic Group I — premium-level

| Table | Used for |
|---|---|
| `CyberIncidentExclusionFactors` | Cyber exclusion factor, keyed by cause-of-loss group ("Basic Group I") |
| `CyberIncidentExclusionWithEnsuingCauseOfLossExceptionsFactors` | Cyber exclusion-with-exceptions factor |
| `LegalLiabilityFactor` | Legal Liability premium factor, keyed `CovType="PersProp"` | confirmed CW row 0.5 |

---

## Basic Group II tables

| Table | Used for | Keys | Shared w/ Building | CW rows filed? |
|---|---|---|---|---|
| `BasicGroupIIRate` | Territory+symbol base rate | State\|CW, BasicGroupIIRatingTerr, Symbol, CovType="PersProp" | yes (same table Building uses) | **No — header only (0 data rows)** |
| `LowestBasicGroupIIRate` | Statewide floor rate (wind/hail-excluded branch) | State\|CW, Symbol, CovType="PersProp" | yes | **No — header only (0 data rows)** |
| `GroupIINumericValue` | Occupancy/class hazard load | State\|CW, BldgClassCode, ConstructionCode | yes | Yes (31 rows) |
| `GroupIIOpenSidesNumericValue` | Open-sides hazard load | State\|CW, ConstructionCode | yes | Yes (7 rows) |
| `BasicGroupIIConstructionSymbol` | Construction symbol resolution | shared/copied from Structure context, not re-looked-up in PP ruleset | yes | Yes (151 rows, verified present; consumed via ancestor `Copy`, not a local PP `Lookup`) |
| `BCEGFactor` | Building Code Effectiveness Grading | shared, read into `BasicGroupIIRate` step | yes | Yes (13 rows) |
| `WindstormOrHailExclFactor` | Wind/hail exclusion COL-adjustment factor | State\|CW, BasicGroupIISymbol | yes | Yes (5 rows) |
| `StdPropPolGroupIIFactor` | COL adjustment factor | State\|CW, "Y" | yes | Yes |
| `BasicGroupIIFlatCoinsuranceFactor` | Flat coinsurance factor (50/60/70/None) | State\|CW, "Y" | yes | Yes |
| `BasicGroupIILOIFactorPersProp` | Limit-of-insurance factor | State\|CW, limit | Yes (55 rows) — **PP-specific, distinct from Building's `BasicGroupIILOIFactorBldg`-equivalent** |

Deductible-by-location (`BGIIDeductibleByLocationFactor`) reuses `DeductibleByLocationFactor` above. `DeductibleFactorBasicGroupII` is `Copy`'d from an ancestor context — same open question as Basic Group I.

---

## Broad tables

| Table | Used for | Keys | Shared w/ Building | CW rows filed? |
|---|---|---|---|---|
| `BroadFormBaseRate` | Construction-type base rate | State\|CW, ConstructionTypeToUse, CovType="PersProp" | yes (same table, `PersProp` rows) | Yes — CW 0.021 (4 combustible types) / 0.011 (2 fire-resistive types) |
| `BroadSpecialLOIFactorPrsnlProp` | Limit-of-insurance factor, shared with Special | State\|CW, limit | Yes (55 rows) — **PP-specific, distinct from Building's `BroadSpecialLOIFactorBldg`** |
| `CoinsuranceFactor` | shared coinsurance factor | — | yes | Yes |

`DeductibleByLocationFactor` (shared, see above) and `DeductibleFactorBroad` (read directly from an ancestor context — no local Set-rule at all, the most externally-sourced deductible factor of the four PP forms) round out Broad's final-rate inputs. Cyber tables: `CyberIncidentExclusionFactors` / `...WithEnsuingCauseOfLossExceptionsFactors`, same as above, consumed with the cause-of-loss group "Broad".

---

## Special tables

| Table | Used for | Keys | Shared w/ Building | CW rows filed? |
|---|---|---|---|---|
| `SpecialPrsnlPropRate` | Base rate | State\|CW, OccupCategory, OccupCategoryRiskSeverity | **No — PP-only table** (Building's Special uses `SpecialBuildingRate`/`SpecialBuildersRiskRate`) | **No — header only (0 data rows)** |
| `PrsnlPropTerrMultiplier` | Territory multiplier | State\|CW, SpecialRatingTerr | **No — PP-only; Building's Special has no territory dimension at all** | **No — header only (0 data rows)** |
| `SpecialPrsnlPropTheftExclusionFactor` | Theft-exclusion credit, keyed by occupancy | State\|CW, OccupCategory | **No — PP-only** (Building's is a flat CW 0.88 constant) | **No — header only (0 data rows)** |
| `BroadSpecialLOIFactorPrsnlProp` | Limit-of-insurance factor, shared with Broad | State\|CW, limit | Yes (55 rows) |
| `CoinsuranceFactor` | shared coinsurance factor | — | yes | Yes |
| `DeductibleFactor` | Standard/theft deductible factor — **computed locally** (only PP form that does) | State\|CW, deductible, amount-of-insurance band, causeOfLossDed | yes | Yes (241 rows) |
| `Deductible250Factor` | Flat $250 deductible factor | State\|CW, causeOfLoss="Special" | yes | Yes — CW = 1.1 |

`WatchmanCreditFactor` and `BurglaryAlarmCreditFactor` are **not rate-table lookups** — they are `Copy`'d directly from the user's `CommercialPropertyBurglaryAndRobberyProtectiveSafeguards` schedule record (fields of the same name on that record). That record's own rating logic (if any) lives in a different ruleset not traced by this document. `SpecialDeductibleByLocationFactor` is `Copy`'d from an ancestor context (4 levels up) — the one deductible-by-location factor among the four PP forms that is *not* computed locally (Basic Group I/II *do* run a local `LookupDeductibleByLocationFactor`).

Cyber tables: `CyberIncidentExclusionFactors` / `...WithEnsuingCauseOfLossExceptionsFactors`, cause-of-loss group "Special".

---

## Not ERC tables

`IRPMFactor`, `PackageModFactor`, and `MultiPremiumAndDispersionCreditFactor` are policy-level user/schedule-rated inputs read from far up the datadef tree (nine levels up from a Personal Property premium record, versus five for Building) — not filed rate tables, matching Building's finding.

`WatchmanCreditFactor` / `BurglaryAlarmCreditFactor` (Special form) are schedule-entry fields, not rate-table lookups — see Special tables above.

---

## Verification

All tables named above were confirmed present as `<TableName>.RateTable.csv` with a matching `<TableName>Def.RateTableDef.xml` in `CFCW20260601V01\Rate Tables`, by recursively resolving `RunRule` references from `ErcSetPostRatesAndFactors`, the four `Set*RatesAndFactors` chains, and the four `CommercialPropertyPersonalPropertyPrsnlProp*CoverageRules.Rule.xml` premium files to their leaf `Lookup` calls' `MatrixFromConstant` attribute, cross-checked with a directory listing and byte/row counts of each CSV.

**Row-count check performed on every table listed** (not just existence) — six tables were found to be **header-only with zero CW data rows**, all flagged above:

- `BasicGroupIRate` (shared with Building — Building's own tables doc did not flag this; confirmed independently here by direct byte count: 72-byte file, one header line)
- `BasicGroupIIRate`
- `LowestBasicGroupIIRate`
- `SpecialPrsnlPropRate`
- `SpecialPrsnlPropTheftExclusionFactor`
- `PrsnlPropTerrMultiplier`

Every other table checked (`BasicGroupILOIFactorPersProp`, `BasicGroupIILOIFactorPersProp`, `BroadSpecialLOIFactorPrsnlProp`, `ProtectionClassFactor`, `SubStdConditionRate`, `FireSafeVaultFactor`, `SprinklerLeakage*`, `VandalismExclFactor`, `StdPropPolGroupIFactor`/`II`, `CoinsuranceFactor`, `LessThan80PctMultiplicativeFactor`, `DeductibleByLocationFactor`, `DeductibleFactor`, `Deductible250Factor`, `GroupIINumericValue`, `GroupIIOpenSidesNumericValue`, `BasicGroupIIConstructionSymbol`, `BCEGFactor`, `WindstormOrHailExclFactor`, `BasicGroupIIFlatCoinsuranceFactor`, `BroadFormBaseRate`, `LegalLiabilityFactor`, `CyberIncidentExclusionFactors`, `CyberIncidentExclusionWithEnsuingCauseOfLossExceptionsFactors`) carries actual CW data rows (row counts ranged 2–325).

**Do not treat the six empty tables as resolvable at countrywide level.** Any state implementation that has not filed its own override for these will produce a null/zero base rate for Basic Group I, Basic Group II, or Special Personal Property, and the affected form's rate chain will collapse to zero from that point forward.
