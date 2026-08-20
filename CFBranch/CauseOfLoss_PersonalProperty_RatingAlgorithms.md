# Cause of Loss — Personal Property Rating Algorithms

**Source ERC package:** `C:\Projects\ISO_ERC_Files\CF\20260601\CFCW20260601V01`
**Line:** Commercial Property (CF), Countrywide, edition 06-01-2026, V01
**Documented:** 2026-08-19

Personal Property rating lives in the `CommercialPropertyPersonalProperty` datadef group — "contents of the building" coverage, sibling to Building/Structure coverage. Four cause-of-loss forms rate independently, confirmed present by their own `Set*RatesAndFactors` chains and dedicated premium-calc rule files:

- **Basic Group I** — fire, lightning, explosion, smoke, aircraft/vehicles
- **Basic Group II** — windstorm/hail, riot/civil commotion, vandalism, sprinkler leakage, sinkhole
- **Broad** — Basic plus falling objects, weight of snow/ice, water damage, collapse
- **Special** — open perils; all risks of direct physical loss except those excluded

Earthquake is *not* one of these four — it has its own chain (`SetEQRatesAndFactors`) run alongside the four but is a separate coverage/endorsement structure, out of scope here (matching the task's framing of the four cause-of-loss forms).

This document mirrors `CauseOfLoss_Building_RatingAlgorithms.md`. Its companion table inventory is `PersonalProperty_ERC_Tables.md`.

---

## Master orchestration — and how it differs from Building's

Building's `SetBlanketRatesAndFactors` is one big rule in `CommercialPropertyStructureRules.Rule.xml` that runs shared prep then the four chains, all within the **Structure** datadef group (one Structure record per building).

Personal Property's orchestration is split across **two files** and driven by a `ForEach` over **multiple Personal Property records per Occupancy Class**, because a single location can carry several classes/items of personal property (e.g., stock, furniture, machinery — each its own `CommercialPropertyPersonalProperty` row) rather than one structure:

```
CommercialPropertyOccupClassRules.Rule.xml
  SetPostPersonalPropertyRatesAndFactors (line 993)
    ForEach CommercialPropertyPersonalPropertyTable/CommercialPropertyPersonalProperty:
        RunRule ErcSetPostRatesAndFactors   <- in CommercialPropertyPersonalPropertyRules.Rule.xml, line 2312
```

`ErcSetPostRatesAndFactors` (line 2312, `CommercialPropertyPersonalPropertyRules.Rule.xml`) is the true master chain — the direct analogue of Building's `SetBlanketRatesAndFactors`:

```
SetOccupTotalLOIToUse
SetOccupSpecialTotAmtInsurance
SetWindHailIndicatorAndDeductFactor
SetDeductibleByLocationFactor
SetBlktTotalLOIToUse
SetBlktBasicGroupILOIFactor
SetBlktBasicGroupIILOIFactor
SetBlktBroadLOIFactor
SetBlktSpecialLOIFactor
SetBGIRatesAndFactors        (line 2771)
SetBGIIRatesAndFactors       (line 3600)
SetBroadRatesAndFactors      (line 4138)
SetSpecialRatesAndFactors    (line 4382)
SetThefLimitationsRatesAndFactors
SetEQSprinklerLeakageOnlyPrsnlPropFactor
SetEQSprinklerLeakageOnlyFactor
SetEQRatesAndFactors
SetTerrorismSublimitPct / ...TRIA... chain
```

A separate, earlier prep rule, `ErcSetPreliminaryRatesAndFactorsAndDoConditionalMandatoryLogic` (line 801), and `ErcSetRatesAndFactors` (line 791, just sets `RiskType = "Personal Property"`), run before this — invoked from `PersonalPropertyLimitToUse` and `PersonalPropertyCauseofLossAndSpecialExclusionFactor` respectively (also `ForEach`-driven from `CommercialPropertyOccupClassRules.Rule.xml`, lines 1148, 1152). These set `CovForm`, `LossCostMultiplier`, class/construction codes, territory factors, symbol, BCEG, sprinkler/vandalism/wind-hail exclusion factors, etc. — the Personal-Property equivalent of Building's shared-prep block, but scoped per-PersonalProperty-record rather than per-Structure.

**Structural takeaway:** Building rates one Structure per building. Personal Property rates **N PersonalProperty records per Occupancy Class per Location**, each independently running the full four-chain rate build-up. All four chains still compute unconditionally regardless of which cause of loss is selected, exactly as in Building — the coverage-level `SetCoverageOnPolicyIndicator` gate in each premium file decides which one produces premium.

---

## File map

| Piece | File | Anchor |
|---|---|---|
| Master chain-runner | `Rules\CommercialPropertyPersonalPropertyRules.Rule.xml` | `ErcSetPostRatesAndFactors` — line 2312 |
| Per-record prep (called from OccupClass ForEach) | `Rules\CommercialPropertyOccupClassRules.Rule.xml` | `SetPostPersonalPropertyRatesAndFactors` — line 993 |
| Rate build-up, Basic Group I | `Rules\CommercialPropertyPersonalPropertyRules.Rule.xml` | `SetBGIRatesAndFactors` — line 2771 |
| Rate build-up, Basic Group II | `Rules\CommercialPropertyPersonalPropertyRules.Rule.xml` | `SetBGIIRatesAndFactors` — line 3600 |
| Rate build-up, Broad | `Rules\CommercialPropertyPersonalPropertyRules.Rule.xml` | `SetBroadRatesAndFactors` — line 4138 |
| Rate build-up, Special | `Rules\CommercialPropertyPersonalPropertyRules.Rule.xml` | `SetSpecialRatesAndFactors` — line 4382 |
| Premium calc, Basic Group I | `Rules\CommercialPropertyPersonalPropertyPrsnlPropBasicGroupICoverageRules.Rule.xml` | `SetPremium` — line 60 |
| Premium calc, Basic Group II | `Rules\CommercialPropertyPersonalPropertyPrsnlPropBasicGroupIICoverageRules.Rule.xml` | `SetPremium` — line 60 |
| Premium calc, Broad | `Rules\CommercialPropertyPersonalPropertyPrsnlPropBroadCoverageRules.Rule.xml` | `SetPremium` — line 64 |
| Premium calc, Special | `Rules\CommercialPropertyPersonalPropertyPrsnlPropSpecialCoverageRules.Rule.xml` | `SetPremium` — line 169 |
| Base rate tables | `Rate Tables\BasicGroupIRate.RateTable.csv` (shared w/ Building), `BasicGroupIIRate...`, `BroadFormBaseRate...`, `SpecialPrsnlPropRate...` | each + a `...Def.RateTableDef.xml` |
| Form attachment only — **no rating** | `Rules\CommercialPropertyCauseOfLossBasicFormPrsnlPropRules.Rule.xml`, `...CauseOfLossBroadFormPrsnlProp...`, `...CauseOfLossSpecialFormPrsnlProp...` | form name/number lookup; `AttachFormCauseOfLoss*` calls invoked from `ErcDoConditionalMandatoryLogic` (line 882) |

Verified by `grep`-ing the full `Rules` directory for `PersonalProperty|PrsnlProp` filenames — over 80 PP-related rule files exist (endorsements, sublimits, agreed value, inflation guard, vacancy, EQ, utility services, etc.); only the six above carry the core four-form rating logic.

---

## Basic Group I — rate build-up

Executed in order by `SetBGIRatesAndFactors` (line 2771) — a 9-step chain:

```
SetBasicGroupILOIFactor
SetCoinsuranceFactor
SetBasicGroupIBaseRate
SetFireSafeVaultFactor
SetProtectionClassFactor
SetBasicGroupIRate
SetBasicGroupICauseOfLossAdjustment
SetAdjustedBasicGroupIRate
SetFinalBasicGroupIRate           (this also runs SetDeductibleFactorBasicGroupI internally, line 3563)
```

Note LOI factor and coinsurance are computed **before** the base rate here (Building computes base rate first) — order doesn't change the math since each step reads only what it needs, but it is a real difference in rule sequencing.

### Step 1 — Base rate
`SetBasicGroupIBaseRate` (line 3076)

Gate: `RatingType = "Class"` **and** `BldgClassCode` is non-blank **and** `BldgClassCode <> "1150"` (Builders Risk class code is excluded from the class-rate path for PP, unlike Building where 1150 uses a different lookup branch elsewhere). Within the gate:

```
if Group = "YARD":
    if YardPropertyIndicator = "Yard Property - Combustible":
        BasicGroupIBaseRate = LookupBasicGroupIRate(constCode=1, group="YARD", covType="PersProp")
    else:
        BasicGroupIBaseRate = LookupBasicGroupIRate(constCode=3, group="YARD", covType="PersProp")
elif ConstructionCode <> 0 and Group is non-blank:
    BasicGroupIBaseRate = LookupBasicGroupIRate(constCode=ConstructionCode, group=Group, covType="PersProp")
else:
    BasicGroupIBaseRate = 0.0
```
Otherwise (gate fails): `BasicGroupIBaseRate = 0.0`. Assigned only when currently null.

`LookupBasicGroupIRate` (line 19321) reads matrix **`BasicGroupIRate`** — the **same table Building uses** — keyed on:

1. `/*/State/Code` (falls back to `CW`)
2. `BldgClassCode`
3. `constCode` (= `ConstructionCode`, or the YARD-special constants 1/3)
4. `group` (occupancy group letter — `A`/`B`/`C`/`YARD` from `SetGroup`, line 837 of the prep chain — **not** the constant `"Not Applicable"` Building passes)
5. `covType` (= `"PersProp"` — **not** `"Building"`)

**One table, two coverage lines.** `BasicGroupIRate.RateTable.csv` carries both Building and Personal Property rows, differentiated by the `Group`/`CovType` columns. **The countrywide file is header-only — zero data rows** (`BasicGroupIRate.RateTable.csv` is 72 bytes, one header line). This affects Building too (not just PP) but the Building doc did not flag it; confirmed here by direct byte count. Any state implementation must file its own rows; PP class-rated Basic Group I cannot resolve at CW level.

### Step 2 — Fire-safe vault factor (PP-only concept)
`SetFireSafeVaultFactor` (line 3248)

```
if RatingType = "Class":
    if CovType = "Personal Property in a Vault with an Approved Fire Rating":
        FireSafeVaultFactor = LookupFireSafeVaultFactor()   # State|CW, "Y" — CW = 0.50
    else:
        FireSafeVaultFactor = 1.0
else:
    FireSafeVaultFactor = 0.0
```

This factor has **no Building equivalent** — it is a contents-specific credit for property stored in a fire-rated vault. It multiplies directly into the Basic Group I rate (step 4).

### Step 3 — Protection class factor
`SetProtectionClassFactor` (line 3320) — same idea as Building's, but the gate additionally excludes `Group = "YARD"` (unless `YardPropertyIndicator = "Yard Property - Non Combustible"`) and `BldgClassCode` 1751/1752. `LookupProtectionClassFactor` reads matrix `ProtectionClassFactor` keyed on State\|CW, `ProtectClass` (read from 6 levels up — the location), `ConstructionCode`. Falls back to `0.0` if the gate's inner condition fails, `1.0` if the outer gate fails entirely.

### Step 4 — Rate
`SetBasicGroupIRate` (line 3418), 3 decimals, only when currently null:

**Class rated** (`RatingType = "Class"`):

```
BasicGroupIRate =
    ( (BasicGroupIBaseRate x LossCostMultiplier) + SubStdConditionRate )
  x FireSafeVaultFactor
  x ProtectionClassFactor
  x BasicGroupIRatingTerrFactor
```

Note: **no `VacantBuildingRate` addend** in the Sum (Building has one) — vacancy for Personal Property is handled by a separate endorsement family (`CommercialPropertyVacancyPermitPrsnlProp*Rules`), not folded into the base rate here. No roof-surfacing factor either (contents have no roof).

**Specific or Tentative rated** (`RatingType <> "Class"`):

```
BasicGroupIRate = SpecificGroupIRate x LossCostMultiplier x SprinklerLeakageNotExcludedFactor
```

Same shape as Building (minus the roof-surfacing factor Building applies here).

### Step 5 — Cause-of-loss adjustment
`SetBasicGroupICauseOfLossAdjustment` (line 3503)

```
if CovType = "Valuable Papers and Records - Other Than Electronic Data":
    BasicGroupICauseOfLossAdjustment = 0.0
else:
    BasicGroupICauseOfLossAdjustment =
        round(BasicGroupIRate - SprinklerLeakageExclNonSprinkleredRate, 3)
      x SprinklerLeakageExclSprinkleredFactor
      x VandalismExclFactor
      x StdPropPolGroupIFactor
```

The `Valuable Papers` gate has **no Building equivalent** — Building has no such `CovType`. This is a recurring pattern across all four PP chains (see Broad and Special below): coverage types that are separately rated (Valuable Papers, and elsewhere Tobacco Sales Warehouses) get zeroed out of the standard COL-adjustment math so they don't double-rate.

### Step 6 — Coinsurance and limit of insurance
`SetCoinsuranceFactor` (line 2902) and `SetBasicGroupILOIFactor` (line 2784) feed `SetAdjustedBasicGroupIRate` (line 3539):

```
AdjustedBasicGroupIRate =
    BasicGroupILOIFactor
  x BasicGroupICauseOfLossAdjustment
  x CoinsuranceFactor
```

`SetCoinsuranceFactor` differs from Building's version: when `CommercialPropertyAdditionalLocationsSpecialCoinsuranceProvisions` or `CommercialPropertyValueReportingForm` exists, **or** `Coinsurance` is one of the five reporting-form values (`Daily`/`Weekly`/`Monthly`/`Quarterly`/`Policy Year Reporting`), PP **forces the factor to the 100% lookup value** — Building's equivalent branch instead *skips* assignment, leaving the factor unchanged. Both are guarded by `ValuationType <> "Functional Valuation"`.

`SetBasicGroupILOIFactor` (line 2784) is a three-way `Choose`: blanket copy from `BlktBasicGroupILOIFactor` when `IncludedInBlkt = "Yes"` and `BlktIDNum > 0`; otherwise `LookupBasicGroupILOIFactor(OccupTotalLOIToUse)` when `CovType` is neither `"Legal Liability"` nor `"Tobacco Sales Warehouses"` and `ConstructionCode <> 0`; otherwise `1.0`.

### Step 7 — Deductible
`SetFinalBasicGroupIRate` (line 3561) runs `SetDeductibleFactorBasicGroupI` (line 3584) as its first action, then:

```
FinalBasicGroupIRate =
    AdjustedBasicGroupIRate x DeductibleByLocationFactor x DeductibleFactorBasicGroupI
```

**No `MultiResidentialPropSpecialCreditFactor`** — that Building-only multi-residential credit does not appear anywhere in `CommercialPropertyPersonalPropertyRules.Rule.xml` (confirmed by full-file grep).

`SetDeductibleFactorBasicGroupI` (line 3584) is **not a Lookup at all** — it simply `Copy`s `DeductibleFactorBasicGroupI` from **four levels up the datadef tree** (`../../../../DeductibleFactorBasicGroupI`), guarded by `IsNull`. The actual `Choose`-on-`Deductible` computation lives in a different ruleset entirely — `CommercialPropertySpecialClassRules.Rule.xml` (`DataDefGroup="CommercialPropertySpecialClass"`, line 3078) also defines a rule of the same name with a real `Lookup`-based `Choose`. **Open question:** the exact ancestor datadef that "4 levels up" resolves to from within a `CommercialPropertyPersonalProperty` record was not conclusively traced from the schema alone — see Open Questions below. The same Copy-not-Lookup pattern repeats for `DeductibleFactorBasicGroupII` (line 4100) and `DeductibleFactorBroad` (read directly in `SetFinalBroadRate`, line 4375, with no dedicated Set-rule at all). **Special is the exception** — `SetDeductibleFactorSpecial` (line 4426) *does* run its own local `Lookup`.

---

## Basic Group I — premium

`CommercialPropertyPersonalPropertyPrsnlPropBasicGroupICoverageRules.Rule.xml`

### Gate 1 — coverage on policy
`SetCoverageOnPolicyIndicator` (line 32):

```
CoverageOnPolicyIndicator = 1  if NOT Exist(AdditionalLocationsSpecialCoinsuranceProvisions)
                               AND NOT Exist(ValueReportingForm)
                            else 0
```

**This is a fundamentally different gate than Building's.** Building's Basic Group I gate tests whether a cause of loss is selected (`CauseOfLossToUse` not blank/not "Not Applicable"). Personal Property's Basic Group I gate has **nothing to do with cause of loss** — it only checks that the PP record isn't subject to Special Coinsurance Provisions or a Value Reporting Form (both of which are rated by separate rule files: `CommercialPropertyAdditionalCoveredPropertyPrsnlPropRules`, `CommercialPropertyStatementOfValuesPrsnlPropRules`). Every one of the four PP premium files (BGI, BGII, Broad, Special) starts with this identical `NotExist` pair; Broad and Special additionally AND in a `CauseOfLossToUse` equality test (see their sections below) — Basic Group I and Basic Group II do **not** gate on cause of loss at the coverage-indicator level at all.

`ErcProcess` (line 253): if the indicator is 0, `Premium = 0.0`; otherwise runs `ErcRate` → `SetPremium` → `SetPremiumIndicator`.

### Branch A — scheduled, non-blanket (line 63)
Applies when `CovForm` is none of *Legal Liability Coverage Form*, *Tobacco Sales Warehouse Coverage Form*, *Class Rated Building Only, No Personal Property Coverage*, **and** `IncludedInBlkt = "No"`:

```
Premium =
  round(
      IRPMFactor
    x MultiPremiumAndDispersionCreditFactor
    x PackageModFactor
    x FinalBasicGroupIRate
    x (Limit / 100)
  , 0)
  x CyberIncidentExclusionFactorBGI
  x CyberIncidentExclusionCOLExcptnsFactorBGI
```

**Gates on `CovForm`, not `CovType`.** Building's Basic Group I premium gates the scheduled branch on `CovType` (Building/Builders Risk/Improvements and Betterments/Condominium Association). Personal Property gates on `CovForm` — the selected ISO coverage form (e.g. Legal Liability Coverage Form, Tobacco Sales Warehouse Coverage Form) — a policy/coverage-form-level field, not a per-item type field. `IRPMFactor`, `PackageModFactor`, and both cyber factors are read **nine levels up** the tree (`../../../../../../../../../IRPMFactor`) — versus Building's five — reflecting Personal Property's deeper nesting (Location → OccupClass → PersonalProperty → coverage datadef).

### Branch B — Legal Liability (line 111)
Applies when `CovForm = "Legal Liability Coverage Form"`:

```
Premium =
      IRPMFactor
    x PackageModFactor
    x (Limit / 100)
    x LegalLiabAddlInsurableIntFactor    (3 dp)
    x LegalLiabFactor                    (3 dp)
    x BasicGroupICauseOfLossAdjustment   (3 dp)
    x CyberIncidentExclusionFactorBGI
    x CyberIncidentExclusionCOLExcptnsFactorBGI
```

Same concept as Building's Legal Liability branch (uses the COL-adjusted rate, not the final rate — bypassing coinsurance/LOI/deductible). Factor name is `LegalLiabFactor` (PP) vs. `LegalLiabilityFactor` (Building's datadef alias) — both are populated from a `LegalLiabilityFactor` rate table keyed with covType `"PersProp"` vs. Building's `"Bldg"`.

### Branch C — blanket (line 148)
Applies when `CovForm` is none of the three excluded forms **and** `IncludedInBlkt = "Yes"`. Requires `BlktTotalFullValueAmount > 0`, else `Premium = 0.0`:

```
Premium =
  round(
      IRPMFactor
    x MultiPremiumAndDispersionCreditFactor
    x PackageModFactor
    x BlktBasicGroupIAvgRate
    x (FullPrsnlPropValue / BlktTotalFullValueAmount)
    x (BlktLimit / 100)
  , 0)
  x CyberIncidentExclusionFactorBGI
  x CyberIncidentExclusionCOLExcptnsFactorBGI
```

Same shape as Building's blanket branch, with `FullPrsnlPropValue` in place of `FullBldgValue`.

### Branch D — otherwise
`Premium = 0.0`. Catches the three excluded `CovForm`s when not blanketed (Legal Liability is caught by Branch B first; Tobacco Sales Warehouse and "Class Rated Building Only" fall through to zero here — those are rated by their own dedicated rule files, e.g. `CommercialPropertyPersonalPropertyTobaccoSalesWarehousesCoverageRules.Rule.xml`).

### Premium indicator
`SetPremiumIndicator` (line 231) and `CalculateTotalPremium` (line 10) are structurally identical to Building's.

---

## Basic Group II — differences

Executed in order by `SetBGIIRatesAndFactors` (line 3600) — an 11-step chain, same length as Building's:

```
SetBasicGroupIINumericValue
SetBasicGroupIIBaseRate
SetLowestBasicGroupIIBaseRate
SetBasicGroupIIRate
SetBasicGroupIICauseOfLossAdjustment
SetBasicGroupIICoinsuranceFactor
SetBasicGroupIILOIFactor
SetAdjustedBasicGroupIIRate
SetBGIIDeductibleByLocationFactor
SetDeductibleFactorBasicGroupII
SetFinalBasicGroupIIRate
```

Same overall shape as Building's Group II: rated off construction **symbol** + rating **territory** (not class code), with a parallel "lowest rate" path for the windstorm/hail-excluded branch. Key differences from Building's Group II:

### Prerequisites — symbol and territory are Copied, not computed locally
`SetBasicGroupIISymbol` (line 1299) and `SetBasicGroupIIRatingTerr` (line 1304) are plain `Copy`s from ancestor datadefs (`../../../../BasicGroupIISymbolToUse` and `../../../../../../BasicGroupIIRatingTerr`) — the actual symbol-resolution logic (construction-type/stories lookup, class overrides, oil-distributing-station overrides) lives up in the Structure/Location context and is shared between Building and Personal Property, not duplicated in the PP ruleset.

### Step 1 — Numeric value
`SetBasicGroupIINumericValue` (line 3615) — same three-way logic as Building's (class-code override for 0580/0585/1300/1650, open-sides override, else 1.0), but keyed on `BldgClassCode` (PP's field name) rather than `ClassCodeToUse`.

### Step 2 — Base rate
`SetBasicGroupIIBaseRate` (line 3680). `LookupBasicGroupIIRate` (line 19299) reads matrix `BasicGroupIIRate` — **same table Building uses** — keyed on State\|CW, `BasicGroupIIRatingTerr`, `BasicGroupIISymbol`, and covType `"PersProp"` (Building passes `"Bldg"`). **`BasicGroupIIRate.RateTable.csv` is header-only — zero CW data rows.**

### Step 3 — Lowest base rate
`SetLowestBasicGroupIIBaseRate` (line 3737). `LookupLowestBasicGroupIIRate` reads matrix `LowestBasicGroupIIRate` keyed on State\|CW, symbol, `"PersProp"`. **This table is also header-only — zero CW data rows.**

### Step 4 — Rate
`SetBasicGroupIIRate` (line 3788), 3 decimals:

```
BasicGroupIIRate = BasicGroupIIBaseRate x LossCostMultiplier x BasicGroupIINumericValue x BCEGFactor
```

**No roof-surfacing factors** — Building applies `LimitationsOnCovForRoofSurfacingACVFactor` and `...CosmeticExclFactor` here; PP has neither (contents have no roof). `BCEGFactor` is retained (Building Code Effectiveness Grading applies to structural resilience of the building the contents sit in, which still affects contents loss potential).

### Step 5 — Cause-of-loss adjustment
`SetBasicGroupIICauseOfLossAdjustment` (line 3813) — same fire-only gate as Building (zeroes on `"Fire"`/`"Fire and Vandalism"`/`"Fire and Sprinkler Leakage"`/`"Fire, Vandalism and Sprinkler Leakage"`), **plus an additional gate**: `CovType = "Valuable Papers and Records - Other Than Electronic Data"` also zeroes it — the same recurring PP-specific carve-out seen in Basic Group I.

```
BasicGroupIICauseOfLossAdjustment = 0.0                                   if fire-only OR Valuable Papers
                                   | BasicGroupIIRate x StdPropPolGroupIIFactor     if no wind/hail exclusion
                                   | LowestBasicGroupIIBaseRate x LossCostMultiplier
                                       x WindstormOrHailExclFactor x StdPropPolGroupIIFactor    if wind/hail excluded
```

No roof-surfacing factors in the wind/hail-excluded branch either (Building's version applies two roof factors there).

### Step 6 — Coinsurance
`SetBasicGroupIICoinsuranceFactor` (line 3879) — same shape as Building's: flat lookup (State\|CW, `"Y"`) when `Coinsurance` in (50%/60%/70%/None), else copy the shared `CoinsuranceFactor`.

### Step 7 — Limit of insurance
`SetBasicGroupIILOIFactor` (line 3935) — three-way `Choose` (blanket copy / `LookupBasicGroupIILOIFactor(OccupTotalLOIToUse)` guarded by `CovType` not in Legal Liability/Tobacco Sales Warehouses and `OccupTotalLOIToUse > 0` / otherwise 1.0). One fewer branch than Building's four-way (no separate Builders Risk branch).

### Step 8 — Adjusted rate
`SetAdjustedBasicGroupIIRate` (line 4023) — same shape as Building's.

### Step 9 — Deductible by location
`SetBGIIDeductibleByLocationFactor` (line 4045) — same shape as Building's, but the wind/hail gate reads `WindstormHailIndicatorPrsnlProp` (PP's own datadef, distinct name from Building's `WindstormHailIndicator`).

### Step 10 — Deductible factor
`SetDeductibleFactorBasicGroupII` (line 4100) — again a plain `Copy` from four levels up (`../../../../DeductibleFactorBasicGroupII`), not a local `Lookup`/`Choose` — same pattern as Basic Group I above.

### Step 11 — Final rate
`SetFinalBasicGroupIIRate` (line 4116):

```
FinalBasicGroupIIRate = AdjustedBasicGroupIIRate x BGIIDeductibleByLocationFactor x DeductibleFactorBasicGroupII
```

No `MultiResidentialPropSpecialCreditFactor` (consistent with Basic Group I — the credit doesn't exist anywhere in the PP ruleset).

---

## Basic Group II — premium

`CommercialPropertyPersonalPropertyPrsnlPropBasicGroupIICoverageRules.Rule.xml`

Structurally near-identical to the Basic Group I premium file (same `CovForm`/`IncludedInBlkt` gates, same three factor-branches plus otherwise-zero), confirmed by inspection of both files side by side. The only functional delta beyond the obvious datadef renames (`FinalBasicGroupIIRate`, `BasicGroupIICauseOfLossAdjustment`, `BlktBasicGroupIIAvgRate`, `CyberIncidentExclusionFactorBGII`, `CyberIncidentExclusionCOLExcptnsFactorBGII`):

**Branch C (blanket) truncates instead of dividing.** Basic Group I's blanket branch computes `BlktLimit / 100` as a plain decimal `Divide`. Basic Group II's blanket branch (line 200) wraps the same division in `rul:Truncate`:

```
Premium =
  round(
      IRPMFactor x MultiPremiumAndDispersionCreditFactor x PackageModFactor
    x BlktBasicGroupIIAvgRate
    x (FullPrsnlPropValue / BlktTotalFullValueAmount)
    x Truncate(BlktLimit / 100)
  , 0)
  x CyberIncidentExclusionFactorBGII x CyberIncidentExclusionCOLExcptnsFactorBGII
```

This can shave fractional cents off the blanket-limit ratio for Group II that Group I would otherwise retain — a small but real rounding divergence between the two forms within the same coverage.

---

## Broad — rate build-up

Executed in order by `SetBroadRatesAndFactors` (line 4138) — the shortest chain at **5 steps** (Building's Broad chain has 6):

```
SetBroadLOIFactor
SetBroadBaseRate
SetBroadRate
SetAdjustedBroadRate
SetFinalBroadRate
```

No dedicated `SetDeductibleFactorBroad` rule exists at all — `SetFinalBroadRate` reads `../../../../DeductibleFactorBroad` directly (four levels up), with no local Copy or Lookup step in between. As with Basic Group I/II's deductible factors, the real computation happens outside the Personal Property ruleset.

### Step 1 — LOI factor (computed first, unlike Building's ordering)
`SetBroadLOIFactor` (line 4147) — three-way `Choose`: blanket copy from `BlktBroadLOIFactor`; else `LookupBroadSpecialLOIFactor(OccupTotalLOIToUse)` when `CovType` not in (Legal Liability, Tobacco Sales Warehouses) and `OccupTotalLOIToUse > 0`; else `1.0`. No separate Builders Risk branch (Building's Broad LOI rule has one).

### Step 2 — Base rate
`SetBroadBaseRate` (line 4235)

```
if CauseOfLossToUse = "Broad" and ConstructionTypeToUse (4 levels up) is non-blank:
    BroadBaseRate = LookupBroadFormBaseRate()   # covType hard-coded "PersProp"
else:
    BroadBaseRate = 0.0
```

Unlike Building, there is **no Builders Risk (`covType="BldrRisk"`) branch** here — Personal Property's Broad base rate always uses `covType = "PersProp"` regardless of class code. `LookupBroadFormBaseRate` (line 19428) reads matrix `BroadFormBaseRate` — **the same table Building uses**, filed under bureau rule 71.E.2/71.E.3/71.E.4 — keyed on State\|CW, `ConstructionTypeToUse`, `"PersProp"`. Countrywide `PersProp` values:

| Construction type | Rate |
|---|---|
| Frame | 0.021 |
| Joisted Masonry | 0.021 |
| Non-Combustible | 0.021 |
| Masonry Non-Combustible | 0.021 |
| Modified Fire Resistive | 0.011 |
| Fire Resistive | 0.011 |

(Matches the `PersProp` rows the Building doc already noted existed in this shared table — confirmed here directly against the CSV.)

### Step 3 — Rate
`SetBroadRate` (line 4285), 3 decimals:

```
if CauseOfLossToUse <> "Broad" OR CovType = "Valuable Papers and Records - Other Than Electronic Data":
    BroadRate = 0.0
else:
    BroadRate = BroadBaseRate x LossCostMultiplier
```

Same Valuable-Papers carve-out pattern as Basic Group I/II, applied here directly inside the rate step (rather than a separate COL-adjustment step, since Broad has none — matching Building's Broad, which also has no `SetBroadCauseOfLossAdjustment`).

### Step 4 — Adjusted rate
`SetAdjustedBroadRate` (line 4338):

```
AdjustedBroadRate = BroadLOIFactor x BroadRate x CoinsuranceFactor
```

**No roof-surfacing ACV factor** — Building's `SetAdjustedBroadRate` folds in `LimitationsOnCovForRoofSurfacingACVFactor` at this step; PP has no such factor anywhere in its ruleset.

### Step 5 — Final rate
`SetFinalBroadRate` (line 4360):

```
FinalBroadRate = AdjustedBroadRate x DeductibleByLocationFactor x DeductibleFactorBroad
```

`DeductibleFactorBroad` read directly from four levels up (see above) — no local deductible `Choose` at all, unlike Building's `SetDeductibleFactorBroad` (which has a four-way `Choose` including a "blank deductible → 0.0" fallback).

---

## Broad — premium

`CommercialPropertyPersonalPropertyPrsnlPropBroadCoverageRules.Rule.xml`

Follows the Basic Group I/II premium shape with two added gates specific to Broad:

- `SetCoverageOnPolicyIndicator` (line 32) adds `../CauseOfLossToUse = "Broad"` to the `NotExist` pair.
- Branch A additionally requires `../CauseOfLoss = "Broad"`.
- Branch C (blanket) additionally requires `../BlktCauseOfLossValue = "Broad"`.

### Branch A — scheduled

```
Premium =
  round(
      IRPMFactor x MultiPremiumAndDispersionCreditFactor x PackageModFactor
    x FinalBroadRate x (Limit / 100)
  , 0)
  x CyberIncidentExclusionFactorBroad x CyberIncidentExclusionCOLExcptnsFactorBroad
```

### Branch B — Legal Liability

```
Premium =
      IRPMFactor x PackageModFactor x (Limit / 100)
    x LegalLiabAddlInsurableIntFactor x LegalLiabFactor x BroadRate    (3 dp each)
    x CyberIncidentExclusionFactorBroad x CyberIncidentExclusionCOLExcptnsFactorBroad
```

Uses raw `BroadRate`, not an adjusted/COL rate — consistent with Building's Broad Legal Liability branch (Broad has no COL-adjustment step in either coverage, so there's nothing else to use).

### Branch C — blanket

```
Premium =
  round(
      IRPMFactor x MultiPremiumAndDispersionCreditFactor x PackageModFactor
    x BlktBroadAvgRate x (FullPrsnlPropValue / BlktTotalFullValueAmount) x (BlktLimit / 100)
  , 0)
  x CyberIncidentExclusionFactorBroad x CyberIncidentExclusionCOLExcptnsFactorBroad
```

Zero when `BlktTotalFullValueAmount = 0`. Branch D — otherwise, `Premium = 0.0`.

---

## Special — rate build-up

Executed in order by `SetSpecialRatesAndFactors` (line 4382) — a **14-step chain**, the longest and richest of the four (Building's Special chain has 9 steps):

```
SetOccupCategory
SetOccupCategoryRiskSeverity
SetSpecialDeductibleByLocationFactor
SetDeductibleFactorSpecial
SetSpecialTheftExclusionFactor
SetSpecialBaseRate
SetPrsnlPropTerrMultiplier
SetSpecialRate
SetSpecialCauseOfLossAdjustment
SetWatchmanCreditFactor
SetBurglaryAlarmCreditFactor
SetSpecialLOIFactor
SetAdjustedSpecialRate
SetFinalSpecialRate
```

**Special is structurally the most different of the four PP forms, and the opposite of Building's Special.** Building's Special base rate is a flat statewide constant with no class/territory dimension at all. Personal Property's Special base rate is keyed on **occupancy category + occupancy category risk severity**, and — unlike Building's Special — it carries its **own territory multiplier** (`PrsnlPropTerrMultiplier`), something none of Building's four forms have for Special. PP's Special is also the only PP chain with theft-specific schedule credits (`WatchmanCreditFactor`, `BurglaryAlarmCreditFactor`) sourced directly from user-entered protective-safeguards data rather than a rate-table lookup.

### Prerequisites — occupancy category
`SetOccupCategory` (line 4400) and `SetOccupCategoryRiskSeverity` (line 4405) `Copy` from two levels up (`../../OccupCategory`, `../../OccupCategoryRiskSeverity`) — set once at the Occupancy Class level and shared by every PersonalProperty record under it.

### Step 1 — Deductible by location
`SetSpecialDeductibleByLocationFactor` (line 4410) — a plain `Copy` from four levels up, guarded by `IsNull` — **not** a local computation, unlike Basic Group I/II's deductible-by-location factors which do run local `Lookup`s (`LookupDeductibleByLocationFactor`) elsewhere in this same ruleset. Special's is the one deductible-by-location factor that is externally sourced rather than locally computed.

### Step 2 — Deductible factor
`SetDeductibleFactorSpecial` (line 4426) — the one deductible factor among all four PP chains that **is** computed locally with its own `Lookup`, not copied from an ancestor. A four-branch `Choose`:

```
Branch 1 (separate theft deductible): when TheftDeductible is non-blank / not "Not Applicable" / not "250" /
   not equal to Deductible, AND SpecialTheftExclusionIndicator = 0:
       DeductibleFactorSpecial = LookupDeductibleFactor(ded=TheftDeductible,
           limit=SpecialIncludingTheftTotAmtInsurance, causeOfLossDed="Other Cause Of Loss")

Branch 2 (flat $250): when Deductible = "250" OR TheftDeductible = "250":
       DeductibleFactorSpecial = LookupDeductible250Factor(causeOfLoss="Special")

Branch 3 (none): when Deductible = "Not Applicable":
       DeductibleFactorSpecial = 1.0

Branch 4 (standard): when Deductible is non-blank:
       DeductibleFactorSpecial = LookupDeductibleFactor(ded=Deductible,
           limit=SpecialTotAmtInsurance, causeOfLossDed="Other Cause Of Loss")

Otherwise: DeductibleFactorSpecial = 0.0
```

Same theft-deductible-driven shape as Building's Special deductible factor, keyed the same way (`SpecialIncludingTheftTotAmtInsurance` / `SpecialTotAmtInsurance`).

### Step 3 — Theft exclusion factor
`SetSpecialTheftExclusionFactor` (line 4592)

```
if CauseOfLossToUse = "Special" and SpecialTheftExclusionIndicator = 1:
    if OccupCategory is non-blank:
        SpecialTheftExclusionFactor = LookupSpecialTheftExclusionFactor()   # State|CW, OccupCategory
    else:
        SpecialTheftExclusionFactor = 0.0
else:
    SpecialTheftExclusionFactor = 1.0
```

Unlike Building's flat CW 0.88 theft-exclusion credit, PP's theft-exclusion factor is **keyed on OccupCategory** — a per-occupancy credit, not a single statewide constant. `SpecialPrsnlPropTheftExclusionFactor.RateTable.csv` is **header-only — zero CW data rows filed.**

### Step 4 — Base rate
`SetSpecialBaseRate` (line 4670)

```
if CauseOfLossToUse = "Special":
    if OccupCategory and OccupCategoryRiskSeverity are both non-blank:
        SpecialBaseRate = LookupSpecialBaseRate()   # State|CW, OccupCategory, OccupCategoryRiskSeverity
    else:
        SpecialBaseRate = 0.0
else:
    SpecialBaseRate = 0.0
```

`LookupSpecialBaseRate` (line 19217) reads matrix `SpecialPrsnlPropRate` — **not** the `SpecialBuildingRate`/`SpecialBuildersRiskRate` tables Building's Special uses, a completely separate table specific to Personal Property. **`SpecialPrsnlPropRate.RateTable.csv` is header-only — zero CW data rows filed** (same open-table pattern as Building's `SpecialBuildingRate`, but here affecting all states, not just missing a CW fallback).

### Step 5 — Territory multiplier (PP-only; Building's Special has none)
`SetPrsnlPropTerrMultiplier` (line 4748)

```
if CauseOfLossToUse = "Special":
    if SpecialRatingTerr (6 levels up) is non-blank:
        PrsnlPropTerrMultiplier = LookupTerritoryMultiplier()   # State|CW, SpecialRatingTerr
    else:
        PrsnlPropTerrMultiplier = 0.0
else:
    PrsnlPropTerrMultiplier = 0.0
```

`LookupTerritoryMultiplier` reads matrix `PrsnlPropTerrMultiplier`. **This table is also header-only — zero CW data rows filed.** Building's Special form has no territory dimension whatsoever (flat statewide rate); Personal Property's does, via this multiplier — a genuine structural difference between the two coverages' Special forms.

### Step 6 — Rate
`SetSpecialRate` (line 4787), 3 decimals:

```
if CauseOfLossToUse <> "Special":
    SpecialRate = 0.0
else:
    SpecialRate = PrsnlPropTerrMultiplier x (SpecialBaseRate x LossCostMultiplier)
```

### Step 7 — Cause-of-loss adjustment
`SetSpecialCauseOfLossAdjustment` (line 4837)

```
if CovType = "Valuable Papers and Records - Other Than Electronic Data":
    SpecialCauseOfLossAdjustment = 0.0
else:
    SpecialCauseOfLossAdjustment = SpecialRate x SpecialTheftExclusionFactor
```

No roof-surfacing factor (none exists for PP). Same Valuable-Papers carve-out as the other three PP forms.

### Step 8/9 — Protective-safeguard credits (PP Special-only)
`SetWatchmanCreditFactor` (line 4862) and `SetBurglaryAlarmCreditFactor` (line 4943) — both gated on `SpecialTheftExclusionIndicator = 0` and the existence of a `CommercialPropertyBurglaryAndRobberyProtectiveSafeguards` record (four levels up). When present and valid, the factor is `Copy`'d **directly from the schedule-modifier record itself** (`.../CommercialPropertyBurglaryAndRobberyProtectiveSafeguards[1]/WatchmanCreditFactor` / `.../BurglaryAlarmCreditFactor`) — these are **not rate-table lookups**, they are pre-computed values carried on the user's protective-safeguards schedule entry (itself presumably rated by a separate ruleset not traced here). Defaults to `1.0` otherwise. Building's Special form has no equivalent — these credits are Personal-Property-specific (theft/burglary protection reduces contents theft exposure in a way that has no Building-coverage analogue).

### Step 10 — Limit of insurance
`SetSpecialLOIFactor` (line 5024) — three-way `Choose`, same shape as Broad's LOI rule: blanket copy from `BlktSpecialLOIFactor`; else `LookupBroadSpecialLOIFactor(OccupSpecialTotAmtInsurance)` when `CovType` not in (Legal Liability, Tobacco Sales Warehouses) and `OccupSpecialTotAmtInsurance > 0`; else `1.0`. Matrix `BroadSpecialLOIFactorPrsnlProp` — shared with Broad, exactly as Building's Broad and Special share `BroadSpecialLOIFactorBldg`.

### Step 11 — Adjusted rate
`SetAdjustedSpecialRate` (line 5112):

```
AdjustedSpecialRate =
    SpecialCauseOfLossAdjustment x CoinsuranceFactor x WatchmanCreditFactor
  x BurglaryAlarmCreditFactor x SpecialLOIFactor
```

Two more multiplicands than Building's Special (`WatchmanCreditFactor`, `BurglaryAlarmCreditFactor`) — the protective-safeguard credits from steps 8/9.

### Step 12 — Final rate
`SetFinalSpecialRate` (line 5140):

```
FinalSpecialRate = AdjustedSpecialRate x SpecialDeductibleByLocationFactor x DeductibleFactorSpecial
```

No `MultiResidentialPropSpecialCreditFactor` (consistent with all four PP forms).

---

## Special — premium

`CommercialPropertyPersonalPropertyPrsnlPropSpecialCoverageRules.Rule.xml`

Like Building's Special, this file is **not** a name-swapped copy of the other three PP premium files — it has genuine structural differences, plus one PP-Special-only wrinkle: a dedicated `LimitToUse` computation.

### Gate 0 — Limit-to-use override for alcoholic beverages tax exclusion
`SetLimit` (line 64) copies `Limit` from one level up if not already set. `SetLimitToUse` (line 80) — run only under the same `CovForm`/`IncludedInBlkt = "No"`/`CauseOfLoss = "Special"` conditions as the scheduled premium branch — then does:

```
if a CommercialPropertyAlcoholicBeveragesTaxExclusion record exists:
    LimitToUse = that record's Limit    # the reduced/excluded limit
else:
    LimitToUse = Limit
```

No equivalent exists in Building's Special (or anywhere in Building's ruleset) — this is a Personal-Property-specific sublimit override for the CP 12 11 Alcoholic Beverages Tax Exclusion endorsement, feeding directly into Branch A's premium formula in place of the raw `Limit`.

### Gate 1 — coverage on policy
`SetCoverageOnPolicyIndicator` (line 32):

```
CoverageOnPolicyIndicator = 1  if NotExist(SpecialCoinsuranceProvisions) AND NotExist(ValueReportingForm)
                                 AND CauseOfLossToUse = "Special"
                              else 0
```

Same `NotExist` pair as the other three forms, plus the direct `CauseOfLossToUse = "Special"` equality test — matching Broad's pattern (Basic Group I/II have no such cause-of-loss test at all).

### Branch A — scheduled (line 172)
Requires the `CovForm` exclusions, `IncludedInBlkt = "No"`, and `CauseOfLoss = "Special"` (reads `CauseOfLoss`, not `CauseOfLossToUse` — same subtlety Building's Special premium file has):

```
Premium =
    FinalSpecialRate                    (3 dp)
  x (LimitToUse / 100)
  x PackageModFactor
  x MultiPremiumAndDispersionCreditFactor
  x IRPMFactor
  x CyberIncidentExclusionFactorSpecial
  x CyberIncidentExclusionCOLExcptnsFactorSpecial
```

**Rounding matches Building's Special pattern, not the Basic/Broad pattern**: nested `Product DecimalPlaces="0"` with no `Round` wrapper (each product step rounds to 0 places as it goes), consistent with the Building doc's finding that Special premium calc across CF consistently departs from the triple-nested-`Round` convention used by Basic Group I/II/Broad.

### Branch B — Legal Liability (line 224)
Requires `CovForm = "Legal Liability Coverage Form"`:

```
Premium =
    SpecialCauseOfLossAdjustment          (3 dp)
  x LegalLiabFactor                       (3 dp)
  x LegalLiabAddlInsurableIntFactor       (3 dp)
  x (Limit / 100)
  x PackageModFactor
  x IRPMFactor
  x CyberIncidentExclusionFactorSpecial
  x CyberIncidentExclusionCOLExcptnsFactorSpecial
```

Uses `SpecialCauseOfLossAdjustment` (which already includes the theft-exclusion factor and the Valuable-Papers zero-out) rather than raw `SpecialRate` — a departure from Building's Special Legal Liability branch, which uses the raw, unadjusted `SpecialRate`.

### Branch C — blanket (line 261)
Requires `IncludedInBlkt = "Yes"` **and** `BlktCauseOfLossValue = "Special"`. Requires `BlktTotalFullValueAmount > 0`, else `Premium = 0.0`:

```
Premium =
    BlktSpecialAvgRate
  x (FullPrsnlPropValue / BlktTotalFullValueAmount)
  x (BlktLimit / 100)
  x PackageModFactor
  x MultiPremiumAndDispersionCreditFactor
  x IRPMFactor
  x CyberIncidentExclusionFactorSpecial
  x CyberIncidentExclusionCOLExcptnsFactorSpecial
```

Same nested-`Product`-no-`Round` pattern and reversed factor ordering as Branch A.

### Branch D — otherwise
`Premium = 0.0`.

### Premium indicator
`SetPremiumIndicator` (line 348) and `CalculateTotalPremium` (line 10) are structurally identical to the other three forms. Notably, `ErcProcess` (line 370) for Special runs an **extra** `ErcSetRatesAndFactors` call (the `SetLimit`/`SetLimitToUse` pair) before `ErcRate` — the only one of the four PP premium files with additional per-premium-file rate/factor prep beyond `SetPremium`/`SetPremiumIndicator`.

---

## Four-way comparison

| | Basic Group I | Basic Group II | Broad | Special |
|---|---|---|---|---|
| Chain length | 9 rules | 11 rules | **5 rules** | **14 rules** |
| Base rate keys | BldgClassCode + ConstructionCode + Group | RatingTerr + Symbol | ConstructionType + "PersProp" | **OccupCategory + OccupCategoryRiskSeverity** |
| Base rate table | `BasicGroupIRate` (shared w/ Bldg; **empty CW**) | `BasicGroupIIRate` (shared w/ Bldg; **empty CW**) | `BroadFormBaseRate` (shared w/ Bldg; CW filed: 0.021/0.011) | `SpecialPrsnlPropRate` (PP-only; **empty CW**) |
| Territory | multiplier (`BasicGroupIRatingTerrFactor`) | lookup key | not used | **multiplier (`PrsnlPropTerrMultiplier`, empty CW)** — Building's Special has none |
| Protection class | multiplier | not used | not used | not used |
| PP-only rate factor | `FireSafeVaultFactor` (CW 0.50) | none | none | `WatchmanCreditFactor`, `BurglaryAlarmCreditFactor` (schedule-sourced, not table lookup) |
| COL adjustment step | yes | yes | **none** | yes |
| Valuable-Papers carve-out | zeroes COL adjustment | zeroes COL adjustment | zeroes rate directly | zeroes COL adjustment |
| Coinsurance | shared `SetCoinsuranceFactor` | own rule + flat factor at 50/60/70/None | shared `CoinsuranceFactor` | shared `CoinsuranceFactor` |
| LOI matrix | `BasicGroupILOIFactorPersProp` | `BasicGroupIILOIFactorPersProp` | `BroadSpecialLOIFactorPrsnlProp` | `BroadSpecialLOIFactorPrsnlProp` (shared w/ Broad) |
| Deduct-by-location | **Copy from 4 levels up** | **Copy from 4 levels up** (own datadef name, wind/hail-gated) | shared `DeductibleByLocationFactor` | **local Lookup** (only PP form that computes locally) |
| Deductible factor | **Copy from 4 levels up** (no local Lookup) | **Copy from 4 levels up** (no local Lookup) | **read directly from 4 levels up, no Set-rule at all** | **local Lookup**, theft-deductible-aware |
| Multi-Residential credit | none (doesn't exist in PP ruleset) | none | none | none |
| Coverage gate | `NotExist` special-coins/VRF pair only | `NotExist` pair only | `NotExist` pair + `CauseOfLossToUse="Broad"` | `NotExist` pair + `CauseOfLossToUse="Special"` |
| Premium dispatch key | `CovForm` (not `CovType`) | `CovForm` | `CovForm` + `CauseOfLoss` | `CovForm` + `CauseOfLoss` |
| Blanket branch divisor | plain `Divide(BlktLimit/100)` | **`Truncate(Divide(BlktLimit/100))`** | plain `Divide` | plain `Divide` |
| Premium rounding | nested `Round` x 3 | nested `Round` x 3 | nested `Round` x 3 | **nested `Product`, no `Round`** |
| Legal Liability uses | COL adjustment | COL adjustment | raw `BroadRate` | COL adjustment (`SpecialCauseOfLossAdjustment`) — differs from Building's Special, which uses raw rate |
| Blanket branch tests | `IncludedInBlkt` | `IncludedInBlkt` | + `BlktCauseOfLossValue` | + `BlktCauseOfLossValue` |
| Special sublimit override | — | — | — | **`LimitToUse` swapped for Alcoholic Beverages Tax Exclusion limit** |

---

## Structural differences from Building — summary

1. **Cardinality.** Building rates one Structure per building. Personal Property rates N `CommercialPropertyPersonalProperty` records per Occupancy Class per Location, each running the full four-chain build-up independently (`ForEach`-driven from `CommercialPropertyOccupClassRules.Rule.xml`).
2. **Master orchestration is split across two files** (`CommercialPropertyOccupClassRules.Rule.xml` drives the `ForEach`; `CommercialPropertyPersonalPropertyRules.Rule.xml` holds the actual chain-runner `ErcSetPostRatesAndFactors`) rather than living entirely in one file the way Building's `SetBlanketRatesAndFactors` does.
3. **Deductible factors for Basic Group I, Basic Group II, and Broad are not computed locally** — they are `Copy`'d (or read directly with no Set-rule) from an ancestor context 4 levels up the datadef tree. Only Special computes its own deductible factor locally. Building computes all four locally, each with its own `Choose`.
4. **Basic Group I's base rate table (`BasicGroupIRate`) and Basic Group II's base rate tables (`BasicGroupIIRate`, `LowestBasicGroupIIRate`) are shared with Building** — same matrix, differentiated by `Group`/`CovType` columns — but **filed with zero CW data rows**, confirmed by direct byte-count of the CSVs.
5. **Special is inverted relative to Building.** Building's Special is the simplest chain (flat statewide rate, no territory, no class). Personal Property's Special is the *most* complex chain (14 steps) — keyed on occupancy category + risk severity, carries its own territory multiplier (which Building's Special entirely lacks), and adds two schedule-sourced protective-safeguard credits (Watchman, Burglary Alarm) that have no Building analogue.
6. **PP-only rate concepts:** `FireSafeVaultFactor` (Basic Group I), `WatchmanCreditFactor`/`BurglaryAlarmCreditFactor` (Special), and a recurring **Valuable Papers and Records** carve-out that zeroes the COL adjustment (or rate, for Broad) across all four forms — none of which exist anywhere in Building's ruleset.
7. **No `MultiResidentialPropSpecialCreditFactor`** anywhere in the PP ruleset (confirmed by full-file grep) — a Building-only credit.
8. **No roof-surfacing factors** anywhere in the PP ruleset (contents have no roof) — removes `LimitationsOnCovForRoofSurfacingACVFactor`/`...CosmeticExclFactor` from every rate step that uses them in Building.
9. **Premium-file coverage gates key off `CovForm` and `NotExist(SpecialCoinsuranceProvisions/ValueReportingForm)`**, not `CovType`/`CauseOfLossToUse` the way Building's do (except Broad/Special, which add a `CauseOfLossToUse` test on top). Basic Group I and II do not test cause of loss in their coverage-on-policy gate at all.
10. **Datadef tree is deeper.** Policy-level factors (`IRPMFactor`, `PackageModFactor`) are read **nine** levels up from a PersonalProperty premium record versus **five** levels up from a Structure premium record in Building — consistent with the extra Location→OccupClass→PersonalProperty nesting.

---

## Quick reference — end-to-end, class-rated scheduled Basic Group I

```
BaseRate        = lookup BasicGroupIRate(State|CW, BldgClassCode, ConstructionCode, Group, "PersProp")

Rate            = ((BaseRate x LossCostMultiplier) + SubStdConditionRate)
                  x FireSafeVaultFactor x ProtectionClassFactor x TerritoryFactor

COLAdj          = 0.0                                                     if CovType = Valuable Papers
                | round(Rate - SprinklerLeakageExclNonSprinkleredRate, 3)
                  x SprinklerLeakageExclSprinkleredFactor x VandalismExclFactor
                  x StdPropPolGroupIFactor                                otherwise

AdjustedRate    = LOIFactor x COLAdj x CoinsuranceFactor

FinalRate       = AdjustedRate x DeductibleByLocationFactor x DeductibleFactorBasicGroupI
                  (DeductibleFactorBasicGroupI copied from an ancestor context, not looked up locally)

Premium         = round(IRPM x MultiPremiumDispersion x PackageMod x FinalRate x (Limit/100), 0)
                  x CyberExclFactorBGI x CyberExclCOLExcptnsFactorBGI
```

## Quick reference — end-to-end, Basic Group II scheduled

```
Symbol, Terr    = copied down from ancestor (Structure/Location) context

NumericValue    = 1.0                             if wind/hail excluded
                | lookup(State|CW, BldgClassCode, ConstructionCode)   if class in (0580,0585,1300,1650)
                | lookup(State|CW, ConstructionCode)                  if OpenSides = Yes
                | 1.0

BaseRate        = lookup BasicGroupIIRate(State|CW, Terr, Symbol, "PersProp")
LowestBaseRate  = lookup LowestBasicGroupIIRate(State|CW, Symbol, "PersProp")

Rate            = BaseRate x LossCostMultiplier x NumericValue x BCEGFactor

COLAdj          = 0.0                                          if CauseOfLoss fire-only OR Valuable Papers
                | Rate x StdPropPolGroupIIFactor                if no wind/hail exclusion
                | LowestBaseRate x LossCostMultiplier x WindstormOrHailExclFactor
                    x StdPropPolGroupIIFactor                   if wind/hail excluded

CoinsFactor     = flat lookup(State|CW, "Y")   if Coinsurance in (50%,60%,70%,None)
                | CoinsuranceFactor            (shared factor)

AdjustedRate    = COLAdj x CoinsFactor x BGIILOIFactor

FinalRate       = AdjustedRate x BGIIDeductibleByLocationFactor x DeductibleFactorBasicGroupII
                  (DeductibleFactorBasicGroupII copied from an ancestor context)

Premium         = round(IRPM x MultiPremiumDispersion x PackageMod x FinalRate x Truncate?(Limit/100), 0)
                  x CyberExclFactorBGII x CyberExclCOLExcptnsFactorBGII
                  (Truncate applies only in the blanket branch's BlktLimit/100 term)
```

## Quick reference — end-to-end, Broad scheduled

```
BaseRate        = lookup BroadFormBaseRate(State|CW, ConstructionTypeToUse, "PersProp")   [CW 0.021 / 0.011 FR]
                | 0.0    if CauseOfLossToUse <> "Broad" or ConstructionTypeToUse blank

Rate            = 0.0                                    if CovType = Valuable Papers
                | BaseRate x LossCostMultiplier            otherwise

                  (no cause-of-loss adjustment step for Broad)

LOIFactor       = BlktBroadLOIFactor                      if blanketed
                | lookup BroadSpecialLOIFactorPrsnlProp(State|CW, OccupTotalLOIToUse)
                | 1.0

AdjustedRate    = LOIFactor x Rate x CoinsuranceFactor

FinalRate       = AdjustedRate x DeductibleByLocationFactor x DeductibleFactorBroad
                  (DeductibleFactorBroad read directly from an ancestor context — no local Set-rule)

Premium         = round(IRPM x MultiPremiumDispersion x PackageMod x FinalRate x (Limit/100), 0)
                  x CyberExclFactorBroad x CyberExclCOLExcptnsFactorBroad
```

## Quick reference — end-to-end, Special scheduled

```
TheftExclFactor = lookup SpecialPrsnlPropTheftExclusionFactor(State|CW, OccupCategory)
                     if COL = Special and CP 10 33 attached (empty CW table)
                | 1.0

BaseRate        = lookup SpecialPrsnlPropRate(State|CW, OccupCategory, OccupCategoryRiskSeverity)
                     if COL = Special         (empty CW table)
                | 0.0

TerrMultiplier  = lookup PrsnlPropTerrMultiplier(State|CW, SpecialRatingTerr)   (empty CW table)
                | 0.0    if COL <> Special or SpecialRatingTerr blank

Rate            = TerrMultiplier x (BaseRate x LossCostMultiplier)

COLAdj          = 0.0                                  if CovType = Valuable Papers
                | Rate x TheftExclFactor                otherwise

WatchmanCredit, BurglaryAlarmCredit  = copied directly from the protective-safeguards schedule record,
                                        1.0 if none / theft not excluded

LOIFactor       = BlktSpecialLOIFactor                       if blanketed
                | lookup BroadSpecialLOIFactorPrsnlProp(State|CW, OccupSpecialTotAmtInsurance)
                | 1.0

AdjustedRate    = COLAdj x CoinsuranceFactor x WatchmanCredit x BurglaryAlarmCredit x LOIFactor

FinalRate       = AdjustedRate x SpecialDeductibleByLocationFactor x DeductibleFactorSpecial
                  (both computed: DeductibleByLocationFactor copied from ancestor, DeductibleFactorSpecial
                   looked up locally, theft-deductible-aware)

Premium         = FinalRate x (LimitToUse/100) x PackageMod x MultiPremiumDispersion x IRPM
                  x CyberExclFactorSpecial x CyberExclCOLExcptnsFactorSpecial
                  (nested Product DecimalPlaces=0 — no Round wrappers;
                   LimitToUse swaps in the Alcoholic Beverages Tax Exclusion limit when that
                   endorsement is attached)
```

---
