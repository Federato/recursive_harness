# Cause of Loss — Building Rating Algorithms

**Source ERC package:** `C:\Projects\ISO_ERC_Files\CF\20260601\CFCW20260601V01`
**Line:** Commercial Property (CF), Countrywide, edition 06-01-2026, V01
**Documented:** 2026-08-13

Building rating lives in the `CommercialPropertyStructure` datadef group — "Structure" is the ERC name for the building record. Four cause-of-loss forms rate independently:

- **Basic Group I** — fire, lightning, explosion, smoke, aircraft/vehicles
- **Basic Group II** — windstorm/hail, riot/civil commotion, vandalism, sprinkler leakage, sinkhole
- **Broad** — Basic plus falling objects, weight of snow/ice, water damage, collapse
- **Special** — open perils; all risks of direct physical loss except those excluded

This document covers all four.

---

## Master orchestration

All four chains are prepared and run in sequence from `SetBlanketRatesAndFactors` (line 3094) in `CommercialPropertyStructureRules.Rule.xml`. Shared prep runs first, then the four rate chains back-to-back:

```
... shared prep (lines 3120-3159) ...
    SetCauseOfLossToUse
    SetSpecialTheftExclusionIndicator          <- Special prerequisite
    SetDeductibleByLocationFactor
    SetMultiPremiumAndDispersionCreditFactor
    SetPackageModFactor
    SetBasicGroupIISymbol / SetBGIISymbolToUse <- Group II prerequisite
    SetSuperiorRoofingIndicator
    SetBCEGFactor
    SetSpecialTotAmtInsurance                  <- Special prerequisite
    SetSpecialIncludingTheftTotAmtInsurance    <- Special prerequisite
    SetProtectionClassFactor                   <- Group I prerequisite
    SetSprinklerLeakageRatesAndFactors
    SetVandalismExclFactor
    SetWindstormOrHailFactors
    SetLimitationsOnCovForRoofSurfacingACVFactor
    SetLimitationsOnCovForRoofSurfacingCosmeticExclFactor
    SetBlktLOIFactor

SetBGIRatesAndFactors        (line 3160)
SetBGIIRatesAndFactors       (line 3161)
SetBroadRatesAndFactors      (line 3162)
SetSpecialRatesAndFactors    (line 3163)
```

Every chain computes a rate regardless of which cause of loss is actually selected; the coverage-level `SetCoverageOnPolicyIndicator` gate decides which one produces premium.

---

## File map

| Piece | File | Anchor |
|---|---|---|
| Rate build-up, Basic Group I | `Rules\CommercialPropertyStructureRules.Rule.xml` | `SetBGIRatesAndFactors` — line 7533 |
| Rate build-up, Basic Group II | `Rules\CommercialPropertyStructureRules.Rule.xml` | `SetBGIIRatesAndFactors` — line 8257 |
| Rate build-up, Broad | `Rules\CommercialPropertyStructureRules.Rule.xml` | `SetBroadRatesAndFactors` — line 9063 |
| Rate build-up, Special | `Rules\CommercialPropertyStructureRules.Rule.xml` | `SetSpecialRatesAndFactors` — line 9529 |
| Premium calc, Basic Group I | `Rules\CommercialPropertyStructureBuildingBasicGroupICoverageRules.Rule.xml` | `SetPremium` — line 66 |
| Premium calc, Basic Group II | `Rules\CommercialPropertyStructureBuildingBasicGroupIICoverageRules.Rule.xml` | `SetPremium` — line 66 |
| Premium calc, Broad | `Rules\CommercialPropertyStructureBuildingBroadCoverageRules.Rule.xml` | `SetPremium` |
| Premium calc, Special | `Rules\CommercialPropertyStructureBuildingSpecialCoverageRules.Rule.xml` | `SetPremium` — line 60 |
| Base rate tables | `Rate Tables\BasicGroupIRate.RateTable.csv`, `BasicGroupIIRate...`, `SpecialBuildingRate...` | each + a `...Def.RateTableDef.xml` |
| Coverage dispatch | `Rules\CommercialPropertyStructureRules.Rule.xml` | `ErcProcess` — line 23781 (`Locate` per coverage datadef) |
| Form attachment only — **no rating** | `Rules\CommercialPropertyCauseOfLossBasicFormBldgRules.Rule.xml`, `...CauseOfLossSpecialFormBldg...` | form name/number lookup |

> Note: the `CauseOfLoss*FormBldgRules` files are often mistaken for the rating logic because of their names. They only resolve the endorsement's form name and number from the `Pages` matrix and pass through a premium if one was supplied. All rating happens in the Structure rules.

---

## Basic Group I — rate build-up

Executed in order by `SetBGIRatesAndFactors` (line 7533):

```
SetBasicGroupIBaseRate
SetBasicGroupIRate
SetBasicGroupICauseOfLossAdjustment
SetCoinsuranceFactor
SetBasicGroupILOIFactor
SetAdjustedBasicGroupIRate
SetDeductibleFactorBasicGroupI
SetFinalBasicGroupIRate
```

### Step 1 — Base rate
`SetBasicGroupIBaseRate` (line 7545)

If `RatingType = "Class"` **and** `ClassCodeToUse` is non-blank **and** `ConstructionCode <> 0`, look up the base rate via `LookupBasicGroupIRate`; otherwise `BasicGroupIBaseRate = 0.0`. Only assigned when the datadef is currently null (preserves a user-supplied override).

`LookupBasicGroupIRate` reads matrix `BasicGroupIRate`, column `Rate`, keyed on:

1. `/*/State/Code` (falls back to `CW` on a second lookup)
2. `ClassCodeToUse`
3. `ConstructionCode`
4. `"Not Applicable"`
5. `"Building"`

### Step 2 — Rate
`SetBasicGroupIRate` (line 7599) — all products rounded to 3 decimals.

**Class rated** (`RatingType = "Class"`):

```
BasicGroupIRate =
    ( (BasicGroupIBaseRate x LossCostMultiplier)
      + SubStdConditionRate
      + VacantBuildingRate )
  x BasicGroupIRatingTerrFactor
  x ProtectionClassFactor
  x LimitationsOnCovForRoofSurfacingACVFactor
```

**Specific or Tentative rated**:

```
BasicGroupIRate =
    SpecificGroupIRate
  x LossCostMultiplier
  x SprinklerLeakageNotExcludedFactor
  x LimitationsOnCovForRoofSurfacingACVFactor
```

**Otherwise:** `BasicGroupIRate = 1.0`

### Step 3 — Cause-of-loss adjustment
`SetBasicGroupICauseOfLossAdjustment` (line 7698)

```
BasicGroupICauseOfLossAdjustment =
    round(BasicGroupIRate - SprinklerLeakageExclNonSprinkleredBldgRate, 3)
  x SprinklerLeakageExclSprinkleredFactor
  x VandalismExclFactor
  x StdPropPolGroupIFactor
```

### Step 4 — Coinsurance and limit of insurance
`SetCoinsuranceFactor` (line 7717) and `SetBasicGroupILOIFactor` (line 7907) feed `SetAdjustedBasicGroupIRate` (line 8104):

```
AdjustedBasicGroupIRate =
    BasicGroupICauseOfLossAdjustment
  x CoinsuranceFactor
  x BasicGroupILOIFactor
```

`SetCoinsuranceFactor` is skipped (leaving the factor unchanged) when `ClassCodeToUse = "1150"` or `ValuationType = "Functional Valuation"`; otherwise it branches on `Coinsurance` (80% / 90% / 100% / other) and requires `IncludedInBlkt = "No"` for the standard branch.

### Step 5 — Deductible
`SetDeductibleFactorBasicGroupI` (line 8126) then `SetFinalBasicGroupIRate` (line 8234):

```
FinalBasicGroupIRate =
    AdjustedBasicGroupIRate
  x DeductibleByLocationFactor
  x DeductibleFactorBasicGroupI
  x MultiResidentialPropSpecialCreditFactor
```

`SetDeductibleFactorBasicGroupI` is a `Choose` on the `Deductible` datadef (250, 500, 1000, …).

---

## Basic Group I — premium

`CommercialPropertyStructureBuildingBasicGroupICoverageRules.Rule.xml`

### Gate 1 — coverage on policy
`SetCoverageOnPolicyIndicator` (line 32): `CoverageOnPolicyIndicator = 1` only when `../CauseOfLossToUse` is neither blank nor `"Not Applicable"`.

`ErcProcess` (line 289): if the indicator is 0, `Premium = 0.0` and rating is skipped entirely; otherwise run `ErcRate` → `SetPremium` → `SetPremiumIndicator`.

### Gate 2 — Builders Risk reporting form
`SetPremium` (line 66) returns `Premium = 0.0` when a `CommercialPropertyBuildersRiskReportingForm` record exists **and** `CovType = "Builders Risk"`.

### Branch A — scheduled building (line 111)
Applies when no Builders Risk Reporting Form exists, `IncludedInBlkt = "No"`, and `CovType` is one of *Builders Risk*, *Building*, *Improvements and Betterments*, *Condominium Association*:

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

Result rounded to 0 decimals (whole dollars). `IRPMFactor` and both cyber factors are read five levels up the tree (policy level).

### Branch B — Legal Liability (line 145)
Applies when `CovType = "Legal Liability"`:

```
Premium =
      BasicGroupICauseOfLossAdjustment
    x LegalLiabilityFactor              (3 dp)
    x LegalLiabAddlInsurableIntFactor   (3 dp)
    x (Limit / 100)
    x PackageModFactor
    x IRPMFactor
    x CyberIncidentExclusionFactorBGI
    x CyberIncidentExclusionCOLExcptnsFactorBGI
```

Note this branch uses the **cause-of-loss adjusted rate**, not `FinalBasicGroupIRate` — it bypasses coinsurance, LOI, and deductible factors.

### Branch C — blanket (line 202)
Applies when `CovType <> "Leasehold Interest"` and `IncludedInBlkt = "Yes"`. Requires `BlktTotalFullValueAmount > 0`, else `Premium = 0.0`:

```
Premium =
  round(
      IRPMFactor
    x MultiPremiumAndDispersionCreditFactor
    x PackageModFactor
    x (BlktLimit / 100)
    x (FullBldgValue / BlktTotalFullValueAmount)
    x BlktBasicGroupIAvgRate
  , 0)
  x CyberIncidentExclusionFactorBGI
  x CyberIncidentExclusionCOLExcptnsFactorBGI
```

### Branch D — otherwise
`Premium = 0.0`. This catches `CovType = "Leasehold Interest"` and any non-blanketed cov type not listed in Branch A.

### Premium indicator
`SetPremiumIndicator` (line 267): `PremiumIndicator = 1` when `Premium <> 0.0`, else 0.

`CalculateTotalPremium` (line 10) returns `Premium` only when `PremiumIndicator = 1` **and** `Premium <> 0`; otherwise 0.

---

## Basic Group II — differences

Executed in order by `SetBGIIRatesAndFactors` (line 8257) — an 11-step chain vs. Group I's 8:

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

The key structural difference from Group I: Group I is rated off **class code + construction code**; Group II is rated off **rating territory + construction symbol**. Group II also carries a second, parallel rate path (`LowestBasicGroupIIBaseRate`) used only when windstorm/hail is excluded.

### Prerequisite — construction symbol
`SetBasicGroupIISymbol` (line 4003) resolves `BasicGroupIISymbol`, then `BasicGroupIISymbolToUse` (assigned at lines 4133–4227). Resolution order:

1. `LookupBasicGroupIIConstructionSymbol` — keyed on State|CW / `ConstructionType` / `NumStories`.
2. `SuperiorRoofingIndicator` is set to `Yes` when `ConstructionType` is one of the eight "Superior Roofing" variants (Joisted Masonry OT Reinforced/Reinforced, Non-Combustible Light Steel / OT Light Steel, and the four Masonry Non-Combustible combinations); otherwise `No`.
3. Class-specific overrides replace the symbol:
   - `LookupBGIISymbolAdditionalClassesRoofConstruction` (line 4133)
   - `LookupBasicGroupIISymbolAdditionalClasses` (lines 4146, 4180, 4193) — used for class codes 0580 / 0585 and related
   - `LookupBasicGroupIISymbolOilDistributingStations` (line 4222)
4. Otherwise `BasicGroupIISymbolToUse = BasicGroupIISymbol` (line 4227).

### Prerequisite — rating territory
`SetBasicGroupIIRatingTerr` (line 919) simply copies `BasicGroupIIRatingTerr` down from the location level (`../../BasicGroupIIRatingTerr`). Unlike Group I there is no separate territory *factor* — territory is a **lookup key into the base rate table**, not a multiplier.

### Step 1 — Numeric value
`SetBasicGroupIINumericValue` (line 8272)

```
if a CommercialPropertyWindstormOrHailExclusion record exists:
    BasicGroupIINumericValue = 1.0
else if ClassCodeToUse in (0580, 0585, 1150, 1300, 1650):
    BasicGroupIINumericValue = LookupGroupIINumericValue(State|CW, ClassCodeToUse, ConstructionCode)
else if OpenSides = "Yes" and ConstructionCode <> 0:
    BasicGroupIINumericValue = LookupGroupIIOpenSidesNumericValue(State|CW, ConstructionCode)
else:
    BasicGroupIINumericValue = 1.0
```

This is Group II's analogue to Group I's protection-class factor — it loads occupancy/open-sides hazard into the rate.

### Step 2 — Base rate
`SetBasicGroupIIBaseRate` (line 8347)

Requires **both** `BasicGroupIISymbolToUse` and `BasicGroupIIRatingTerr` to be non-blank; otherwise `BasicGroupIIBaseRate = 0.0`. Only assigned when currently null.

`LookupBasicGroupIIRate` reads matrix `BasicGroupIIRate`, column `Rate`, keyed on:

1. `/*/State/Code` (falls back to `CW`)
2. `BasicGroupIIRatingTerr`
3. `BasicGroupIISymbolToUse`
4. `"Bldg"`

### Step 3 — Lowest base rate
`SetLowestBasicGroupIIBaseRate` (line 8397)

Requires only `BasicGroupIISymbolToUse` (no territory); else 0.0. `LookupLowestBasicGroupIIRate` reads matrix `LowestBasicGroupIIRate` keyed on State|CW / `BasicGroupIISymbolToUse` / `"Bldg"` — note the territory key is absent, so this is the statewide floor rate for the symbol. It is consumed **only** by the windstorm/hail-excluded branch of step 5.

### Step 4 — Rate
`SetBasicGroupIIRate` (line 8441), 3 decimals, only when currently null:

```
BasicGroupIIRate =
    BasicGroupIIBaseRate
  x LossCostMultiplier
  x BasicGroupIINumericValue
  x LimitationsOnCovForRoofSurfacingACVFactor
  x LimitationsOnCovForRoofSurfacingCosmeticExclFactor
  x BCEGFactor
```

Two Group II-only factors here: `LimitationsOnCovForRoofSurfacingCosmeticExclFactor` (cosmetic damage exclusion — a wind/hail concept) and `BCEGFactor` (Building Code Effectiveness Grading). Neither appears in the Group I rate. There is no substandard-condition or vacant-building rate addend, and no territory factor multiplier.

### Step 5 — Cause-of-loss adjustment
`SetBasicGroupIICauseOfLossAdjustment` (line 8472)

**Gate.** If `CauseOfLossToUse` is any of `"Fire"`, `"Fire and Vandalism"`, `"Fire and Sprinkler Leakage"`, `"Fire, Vandalism and Sprinkler Leakage"`, then `BasicGroupIICauseOfLossAdjustment = 0.0` — a fire-only cause of loss buys no Group II perils, so no Group II premium.

**Otherwise, no windstorm/hail exclusion:**

```
BasicGroupIICauseOfLossAdjustment = BasicGroupIIRate x StdPropPolGroupIIFactor
```

**Otherwise, windstorm/hail exclusion present** — the rate is rebuilt from the *lowest* base rate rather than the territory-rated one:

```
BasicGroupIICauseOfLossAdjustment =
    LowestBasicGroupIIBaseRate
  x LossCostMultiplier
  x LimitationsOnCovForRoofSurfacingACVFactor
  x LimitationsOnCovForRoofSurfacingCosmeticExclFactor
  x WindstormOrHailExclFactor
  x StdPropPolGroupIIFactor
```

Note this second form drops `BasicGroupIINumericValue` and `BCEGFactor` entirely — consistent with step 1, which already forces the numeric value to 1.0 when the exclusion is present.

### Step 6 — Coinsurance
`SetBasicGroupIICoinsuranceFactor` (line 8540)

```
if Coinsurance in ("50%", "60%", "70%", "None"):
    BasicGroupIICoinsuranceFactor = LookupBasicGroupIIFlatCoinsuranceFactor(State|CW, "Y")
else:
    BasicGroupIICoinsuranceFactor = CoinsuranceFactor      # copy Group I's shared factor
```

The flat-factor lookup takes a constant `"Y"` as its second key — it is a single statewide value, not coinsurance-percentage-specific. Both branches assign only when currently null.

### Step 7 — Limit of insurance
`SetBasicGroupIILOIFactor` (line 8596), a four-way `Choose`:

| Branch | Condition | Result |
|---|---|---|
| 1 | `IncludedInBlkt = "Yes"` | copy from `BlktBasicGroupIILOIFactor` (set at line 7371) |
| 2 | `CovType = "Builders Risk"` | `LookupBasicGroupIILOIFactorWithArgs` (explicit args), else 0.0 |
| 3 | `CovType` not in (*Leasehold Interest*, *Legal Liability*, *No Coverage*) | `LookupBasicGroupIILOIFactor`, else 0.0 |
| 4 | otherwise | 1.0 |

### Step 8 — Adjusted rate
`SetAdjustedBasicGroupIIRate` (line 8787)

```
AdjustedBasicGroupIIRate =
    BasicGroupIICauseOfLossAdjustment
  x BasicGroupIICoinsuranceFactor
  x BasicGroupIILOIFactor
```

Same shape as Group I, using the Group II-specific coinsurance and LOI factors.

### Step 9 — Deductible by location
`SetBGIIDeductibleByLocationFactor` (line 8809)

```
if WindstormHailIndicator = 0
   and a CommercialPropertyDeductiblesByLocationBldg record exists
   and its [1]/WindstormOrHailDeductible is neither blank nor "Not Applicable":
       BGIIDeductibleByLocationFactor = LookupDeductibleByLocationFactor(...)
else:
       BGIIDeductibleByLocationFactor = 1.0
```

Group II keeps this in its own datadef (`BGIIDeductibleByLocationFactor`) rather than the shared `DeductibleByLocationFactor` Group I uses, because the wind/hail deductible can differ from the all-other-perils deductible on the same building.

### Step 10 — Deductible factor
`SetDeductibleFactorBasicGroupII` (line 8864)

Outer test: when `WindstormOrHailDeductible` is blank, `"Not Applicable"`, or **equal to** `Deductible` (i.e. no separate wind/hail deductible), fall through to a `Choose` on `Deductible` (250, 500, 1000, …) — the same shape as Group I. When a distinct wind/hail deductible *is* present, the rule branches on `WindstormOrHailDeductible` instead. Assignments are guarded by `IsNull` on `DeductibleFactorBasicGroupII`.

### Step 11 — Final rate
`SetFinalBasicGroupIIRate` (line 9040)

```
FinalBasicGroupIIRate =
    AdjustedBasicGroupIIRate
  x BGIIDeductibleByLocationFactor
  x DeductibleFactorBasicGroupII
  x MultiResidentialPropSpecialCreditFactor
```

---

## Basic Group II — premium

`CommercialPropertyStructureBuildingBasicGroupIICoverageRules.Rule.xml`

This file is **structurally identical** to the Group I premium file — a normalized diff of the two (swapping `BasicGroupII`/`BGII` → `BasicGroupI`/`BGI`) produces zero differences. Same gates, same four branches, same rounding. Only the datadef names differ:

| Group I | Group II |
|---|---|
| `FinalBasicGroupIRate` | `FinalBasicGroupIIRate` |
| `BasicGroupICauseOfLossAdjustment` | `BasicGroupIICauseOfLossAdjustment` |
| `BlktBasicGroupIAvgRate` | `BlktBasicGroupIIAvgRate` |
| `CyberIncidentExclusionFactorBGI` | `CyberIncidentExclusionFactorBGII` |
| `CyberIncidentExclusionCOLExcptnsFactorBGI` | `CyberIncidentExclusionCOLExcptnsFactorBGII` |

Everything shared — `IRPMFactor`, `MultiPremiumAndDispersionCreditFactor`, `PackageModFactor`, `Limit`, `BlktLimit`, `FullBldgValue`, `BlktTotalFullValueAmount`, `LegalLiabilityFactor`, `LegalLiabAddlInsurableIntFactor`, `CovType`, `IncludedInBlkt`, `CauseOfLossToUse` — is read from the same paths.

So, for the scheduled-building branch (line 111):

```
Premium =
  round(
      IRPMFactor
    x MultiPremiumAndDispersionCreditFactor
    x PackageModFactor
    x FinalBasicGroupIIRate
    x (Limit / 100)
  , 0)
  x CyberIncidentExclusionFactorBGII
  x CyberIncidentExclusionCOLExcptnsFactorBGII
```

Gates and the Legal Liability / blanket / zero branches follow the Group I section above verbatim, with `ErcProcess` at line 289 and `SetPremium` at line 66 in the Group II file.

---

## Broad — rate build-up

Executed in order by `SetBroadRatesAndFactors` (line 9063) — the **shortest chain at 6 steps**:

```
SetBroadBaseRate
SetBroadRate
SetBroadLOIFactor
SetAdjustedBroadRate
SetDeductibleFactorBroad
SetFinalBroadRate
```

**There is no `SetBroadCauseOfLossAdjustment` rule** — Broad is the only one of the four forms with no cause-of-loss adjustment step. There is also no Broad-specific deductible-by-location rule; it reuses the shared `DeductibleByLocationFactor`. The roof-surfacing ACV factor, which the other forms apply during the rate or COL-adjustment step, is folded into `SetAdjustedBroadRate` instead.

Broad sits between Special and the Basic forms in complexity: like Special it has a small flat-ish rate table and no territory or protection class, but unlike Special it does vary by **construction type**.

### Step 1 — Base rate
`SetBroadBaseRate` (line 9073)

```
if CauseOfLossToUse = "Broad" and ConstructionTypeToUse is non-blank:
    if ClassCodeToUse = "1150":                                    # Builders Risk class
        BroadBaseRate = LookupBroadFormBaseRate(covType = "BldrRisk")
    else:
        BroadBaseRate = LookupBroadFormBaseRate(covType = "Bldg")
else:
    BroadBaseRate = 0.0
```

Note the gate requires `ConstructionTypeToUse` — Broad is the only non-Basic form with a construction dependency. Assigned only when currently null.

`LookupBroadFormBaseRate` (line 24544) takes a `covType` **parameter** and reads matrix `BroadFormBaseRate`, column `Rate`, keyed on:

1. `/*/State/Code` (falls back to `CW`)
2. `ConstructionTypeToUse`
3. the `covType` param — `"Bldg"`, `"BldrRisk"`, `"PersProp"`, or a Business Income variant

Filed under bureau rule **71.E.2 / 71.E.3 / 71.E.4**. Countrywide building values:

| Construction type | Bldg | BldrRisk |
|---|---|---|
| Frame | 0.015 | 0.012 |
| Joisted Masonry | 0.015 | 0.012 |
| Non-Combustible | 0.015 | 0.012 |
| Masonry Non-Combustible | 0.015 | 0.012 |
| Modified Fire Resistive | 0.010 | 0.012 |
| Fire Resistive | 0.010 | 0.012 |

So the building rate is effectively two-tiered — 0.015 for the four combustible/light constructions, 0.010 for the two fire-resistive ones — while Builders Risk is flat 0.012 across all six. (The same table also carries `PersProp` rows at 0.021 / 0.011 and Business Income rows, used by the personal property and time-element rulesets.)

### Step 2 — Rate
`SetBroadRate` (line 9159), 3 decimals, only when currently null:

```
BroadRate = BroadBaseRate x LossCostMultiplier
```

Identical in shape to `SetSpecialRate`.

### Step 3 — Limit of insurance
`SetBroadLOIFactor` (line 9178), a four-way `Choose` — the same structure as the Special LOI rule, and it reads the **same matrix**:

| Branch | Condition | Result |
|---|---|---|
| 1 | `IncludedInBlkt = "Yes"` **and** `BlktIDNum > 0` | copy from `BlktBroadLOIFactor` (set at line 7425) |
| 2 | `CovType = "Builders Risk"` | `LookupBroadSpecialLOIFactorWithArgs`, passing the Builders Risk Reporting Form's `[1]/Limit`; 0.0 if absent |
| 3 | `CovType` not in (*Leasehold Interest*, *Legal Liability*, *No Coverage*) and `Limit` present | `LookupBroadSpecialLOIFactor` keyed on State\|CW + `Limit`; 0.0 if `Limit` is absent |
| 4 | otherwise | 1.0 |

Matrix `BroadSpecialLOIFactorBldg` is shared with Special — one LOI table serves both forms.

### Step 4 — Adjusted rate
`SetAdjustedBroadRate` (line 9373)

```
AdjustedBroadRate =
    BroadRate
  x LimitationsOnCovForRoofSurfacingACVFactor
  x CoinsuranceFactor          # shared with Group I and Special
  x BroadLOIFactor
```

This is where Broad absorbs the roof-surfacing factor that the other three forms apply upstream. Net effect is the same ordering of multiplications; only the rule boundary differs.

### Step 5 — Deductible factor
`SetDeductibleFactorBroad` (line 9398), a four-way `Choose` — simpler than Special's, with no theft dimension:

```
if Deductible = "250":
    DeductibleFactorBroad = LookupDeductible250Factor(causeOfLoss = "Broad")
elif Deductible = "Not Applicable":
    DeductibleFactorBroad = 1.0
elif Deductible is non-blank:
    DeductibleFactorBroad = LookupDeductibleFactor(
        ded            = Deductible,
        limit          = TotAmtInsurance,
        causeOfLossDed = "Other Cause Of Loss")
else:
    DeductibleFactorBroad = 0.0
```

Note the `Otherwise` branch yields **0.0**, not 1.0 — a blank `Deductible` zeroes the Broad rate entirely. Special's equivalent fall-through behaves differently, and it uses `SpecialTotAmtInsurance` where Broad uses the plain `TotAmtInsurance`.

### Step 6 — Final rate
`SetFinalBroadRate` (line 9506)

```
FinalBroadRate =
    AdjustedBroadRate
  x DeductibleByLocationFactor          # shared, not Broad-specific
  x DeductibleFactorBroad
  x MultiResidentialPropSpecialCreditFactor
```

---

## Broad — premium

`CommercialPropertyStructureBuildingBroadCoverageRules.Rule.xml`

Broad follows the **Basic Group I premium structure**, including the triple-nested `Round DecimalPlaces="0"` pattern and the Basic factor ordering — it does *not* share Special's `Product`-only rounding. A normalized diff against the Group I file shows only four deltas, all cause-of-loss guards:

1. **Coverage gate** (`SetCoverageOnPolicyIndicator`) is an exact `CauseOfLossToUse = "Broad"` test rather than "not blank / not Not Applicable".
2. **Branch A** adds `CauseOfLoss = "Broad"` to its condition set.
3. **Branch B (Legal Liability)** adds `CauseOfLoss = "Broad"` and uses raw **`BroadRate`** in place of a cause-of-loss adjustment — which for Broad doesn't exist anyway, so the roof-surfacing ACV factor and coinsurance never reach Legal Liability premium.
4. **Branch C (blanket)** adds `BlktCauseOfLossValue = "Broad"` alongside `IncludedInBlkt = "Yes"`.

The outer `SetPremium` gate keeps the Group I form — `(no Builders Risk Reporting Form OR CovType <> "Builders Risk")` — with Leasehold Interest filtered inside the `Choose` rather than up front the way Special does.

### Branch A — scheduled building

```
Premium =
  round(
      IRPMFactor
    x MultiPremiumAndDispersionCreditFactor
    x PackageModFactor
    x FinalBroadRate
    x (Limit / 100)
  , 0)
  x CyberIncidentExclusionFactorBroad
  x CyberIncidentExclusionCOLExcptnsFactorBroad
```

### Branch B — Legal Liability

```
Premium =
    BroadRate                          (3 dp)
  x LegalLiabilityFactor               (3 dp)
  x LegalLiabAddlInsurableIntFactor    (3 dp)
  x (Limit / 100)
  x PackageModFactor
  x IRPMFactor
  x CyberIncidentExclusionFactorBroad
  x CyberIncidentExclusionCOLExcptnsFactorBroad
```

### Branch C — blanket

```
Premium =
  round(
      IRPMFactor
    x MultiPremiumAndDispersionCreditFactor
    x PackageModFactor
    x (BlktLimit / 100)
    x (FullBldgValue / BlktTotalFullValueAmount)
    x BlktBroadAvgRate
  , 0)
  x CyberIncidentExclusionFactorBroad
  x CyberIncidentExclusionCOLExcptnsFactorBroad
```

Zero when `BlktTotalFullValueAmount` is 0. **Branch D** — otherwise, `Premium = 0.0`.

---

## Special — rate build-up

Executed in order by `SetSpecialRatesAndFactors` (line 9529) — 9 steps:

```
SetSpecialTheftExclusionFactor
SetSpecialBaseRate
SetSpecialRate
SetSpecialCauseOfLossAdjustment
SetSpecialLOIFactor
SetAdjustedSpecialRate
SetSpecialDeductibleByLocationFactor
SetDeductibleFactorSpecial
SetFinalSpecialRate
```

**Special is the simplest of the three chains and structurally the odd one out.** Its base rate is a *flat statewide constant* — not keyed on class code, construction, territory, or symbol. The entire rate build-up is: flat rate × LCM, then theft/roof/coinsurance/LOI/deductible factors. The class and construction dimensions that drive Basic Group I and II are absent.

`SetSpecialRate` and everything downstream run unconditionally, but `SetSpecialBaseRate` gates on `CauseOfLossToUse = "Special"` — so when Special isn't the selected cause of loss, the base rate is 0.0 and the whole chain collapses to zero.

### Prerequisite — theft exclusion indicator
`SetSpecialTheftExclusionIndicator` (line 9542), run during shared prep at line 3129 (**not** part of the Special chain, but consumed by two of its steps):

```
SpecialTheftExclusionIndicator = 1 if a CommercialPropertyTheftExclusion record exists, else 0
```

This corresponds to form **CP 10 33** (Theft Exclusion). Several validation messages key off it — e.g. `DoMessageTheftDeductibleIsInvalidUnlessTheBuildingOrOnePPRecordHasSpecialAsCauseOfLossWOCP1033Attached` (line 19078) and `DoMessageCP1211IsNotValidWhenTheStructureOrAtLeastOnePPRecordsOfTheStructureHasSpecialCOLWithoutCP1033Attached` (line 17463).

### Prerequisite — amount-of-insurance sums
Two sums computed during shared prep, both used only as deductible-table lookup keys:

- `SetSpecialTotAmtInsurance` (line 4731, called at 3146) → `SpecialTotAmtInsurance`
- `SetSpecialIncludingTheftTotAmtInsurance` (line 5175, called at 3148) → `SpecialIncludingTheftTotAmtInsurance`

The "including theft" variant is used when a separate theft deductible applies; the plain variant otherwise.

### Step 1 — Theft exclusion factor
`SetSpecialTheftExclusionFactor` (line 9561)

```
if CauseOfLossToUse = "Special" and SpecialTheftExclusionIndicator = 1:
    SpecialTheftExclusionFactor = LookupSpecialBldgTheftExclusionFactor(State|CW, "Y")
else:
    SpecialTheftExclusionFactor = 1.0
```

Countrywide value is **0.88** — a 12% credit for excluding theft. Assigned only when currently null.

### Step 2 — Base rate
`SetSpecialBaseRate` (line 9611)

```
if CauseOfLossToUse = "Special":
    if ClassCodeToUse = "1150":                      # Builders Risk class
        SpecialBaseRate = LookupSpecialBuildersRiskRate(State|CW, "Y")
    else:
        SpecialBaseRate = LookupSpecialBuildingRate(State|CW, "Y")
else:
    SpecialBaseRate = 0.0
```

Both lookups take a **constant `"Y"`** as their only non-state key — these are single-value statewide tables, filed under bureau rule **72.E.2.b.(1)**.

> **Countrywide data note.** `Rate Tables\SpecialBuildingRate.RateTable.csv` contains only a header row — no `CW` row is filed, so the countrywide lookup returns null and `SpecialBaseRate` is left unset unless a state supplies a row. `SpecialBuildersRiskRate.RateTable.csv` does carry a `CW` row at **0.015**. Any state implementation must file its own `SpecialBuildingRate`.

### Step 3 — Rate
`SetSpecialRate` (line 9683), 3 decimals, only when currently null:

```
SpecialRate = SpecialBaseRate x LossCostMultiplier
```

That is the entire rate step. No territory, no protection class, no construction, no numeric value, no BCEG.

### Step 4 — Cause-of-loss adjustment
`SetSpecialCauseOfLossAdjustment` (line 9702), 3 decimals, unconditional:

```
SpecialCauseOfLossAdjustment =
    SpecialRate
  x SpecialTheftExclusionFactor
  x LimitationsOnCovForRoofSurfacingACVFactor
```

Unlike Groups I and II this rule has no `IsNull` guard and no branching — it always recomputes.

### Step 5 — Limit of insurance
`SetSpecialLOIFactor` (line 9713), a four-way `Choose` — same shape as the Group II LOI rule:

| Branch | Condition | Result |
|---|---|---|
| 1 | `IncludedInBlkt = "Yes"` **and** `BlktIDNum > 0` | copy from `BlktSpecialLOIFactor` (set at line 7479) |
| 2 | `CovType = "Builders Risk"` | `LookupBroadSpecialLOIFactorWithArgs`, passing the Builders Risk Reporting Form's `[1]/Limit`; 0.0 if that limit is absent |
| 3 | `CovType` not in (*Leasehold Interest*, *Legal Liability*, *No Coverage*) | `LookupBroadSpecialLOIFactor` keyed on State\|CW + `Limit`; 0.0 if `Limit` is absent |
| 4 | otherwise | 1.0 |

Note the matrix is **`BroadSpecialLOIFactorBldg`** — Broad and Special share one LOI factor table.

### Step 6 — Adjusted rate
`SetAdjustedSpecialRate` (line 9904)

```
AdjustedSpecialRate =
    SpecialCauseOfLossAdjustment
  x CoinsuranceFactor          # shared with Group I — no Special-specific coinsurance rule
  x SpecialLOIFactor
```

### Step 7 — Deductible by location
`SetSpecialDeductibleByLocationFactor` (line 9926)

```
if a CommercialPropertyDeductiblesByLocationBldg record exists
   and its [1]/TheftDeductible is neither blank nor "Not Applicable":
       SpecialDeductibleByLocationFactor = LookupDeductibleByLocationFactor(...)
else:
       SpecialDeductibleByLocationFactor = 1.0
```

Same shape as the Group II rule, but triggered by a by-location **theft** deductible rather than a wind/hail one. Note there is no `WindstormHailIndicator = 0` precondition here — Group II has one, Special does not.

### Step 8 — Deductible factor
`SetDeductibleFactorSpecial` (line 9977), a multi-branch `Choose`:

**Branch 1 — separate theft deductible applies.** When `SpecialTheftExclusionIndicator = 0` **and** `TheftDeductible` is not blank / not `"Not Applicable"` / not `"250"` / not equal to `Deductible`:

```
DeductibleFactorSpecial = LookupDeductibleFactor(
    deductible      = TheftDeductible,
    amtInsurance    = SpecialIncludingTheftTotAmtInsurance,
    causeOfLossType = "Other Cause Of Loss")
```

**Branch 2 — flat $250.** When `Deductible = "250"` and `TheftDeductible = "250"`:

```
DeductibleFactorSpecial = LookupDeductible250Factor("Special", ...)
```

**Branch 3 — no deductible.** `Deductible = "Not Applicable"` → `1.0`

**Branch 4 — standard.** `Deductible` non-blank:

```
DeductibleFactorSpecial = LookupDeductibleFactor(
    deductible      = Deductible,
    amtInsurance    = SpecialTotAmtInsurance,
    causeOfLossType = "Other Cause Of Loss")
```

All assignments guarded by `IsNull` on `DeductibleFactorSpecial`. The key difference from Groups I and II: the deductible factor can be driven by the **theft** deductible and a **theft-inclusive** amount-of-insurance band.

### Step 9 — Final rate
`SetFinalSpecialRate` (line 10143)

```
FinalSpecialRate =
    AdjustedSpecialRate
  x SpecialDeductibleByLocationFactor
  x DeductibleFactorSpecial
  x MultiResidentialPropSpecialCreditFactor
```

---

## Special — premium

`CommercialPropertyStructureBuildingSpecialCoverageRules.Rule.xml`

Unlike Group II, this file is **not** a name-swapped copy of the Group I file. A normalized diff shows real structural differences — documented below.

### Gate 1 — coverage on policy
`SetCoverageOnPolicyIndicator` (line 32) is a **direct equality test**, not the "neither blank nor Not Applicable" test the Basic files use:

```
CoverageOnPolicyIndicator = 1 if CauseOfLossToUse = "Special", else 0
```

`ErcProcess` then zeroes the premium and skips rating when the indicator is 0.

### Gate 2 — outer test on `SetPremium` (line 62)
Special adds a second condition the Basic files lack:

```
(no BuildersRiskReportingForm record  OR  CovType <> "Builders Risk")
AND CovType <> "Leasehold Interest"
```

In the Basic files, Leasehold Interest is filtered later inside the `Choose`; here it is excluded up front.

### Branch A — scheduled building (line 115)
Requires no Builders Risk Reporting Form, `IncludedInBlkt = "No"`, **`CauseOfLoss = "Special"`** (an extra condition not present in the Basic files — and note it reads `CauseOfLoss`, not `CauseOfLossToUse`), and `CovType` in *Builders Risk* / *Building* / *Improvements and Betterments* / *Condominium Association*:

```
Premium =
    FinalSpecialRate
  x (Limit / 100)
  x PackageModFactor
  x MultiPremiumAndDispersionCreditFactor
  x IRPMFactor
  x CyberIncidentExclusionFactorSpecial
  x CyberIncidentExclusionCOLExcptnsFactorSpecial
```

**Rounding differs from the Basic forms.** The Basic files wrap the core product in three nested `Round DecimalPlaces="0"` elements before applying the cyber factors. Special uses a chain of nested `Product DecimalPlaces="0"` elements with **no `Round` wrappers** — each product truncates/rounds to 0 places as it goes, and the factors are applied in a different order (rate × limit first, then PackageMod, then MultiPremium, then IRPM). Results can differ by a dollar or two from the Basic-form pattern on the same inputs.

### Branch B — Legal Liability (line 155)
Requires `CovType = "Legal Liability"` **and** `CauseOfLoss = "Special"`:

```
Premium =
    SpecialRate                        (3 dp)
  x LegalLiabilityFactor               (3 dp)
  x LegalLiabAddlInsurableIntFactor    (3 dp)
  x (Limit / 100)
  x PackageModFactor
  x IRPMFactor
  x CyberIncidentExclusionFactorSpecial
  x CyberIncidentExclusionCOLExcptnsFactorSpecial
```

The Basic forms use their **cause-of-loss adjustment** here; Special uses the raw **`SpecialRate`** — so the theft exclusion factor and the roof-surfacing ACV factor are *not* applied to Legal Liability premium.

### Branch C — blanket (line 183)
Requires `IncludedInBlkt = "Yes"` **and `BlktCauseOfLossValue = "Special"`** — the Basic files test only `IncludedInBlkt`. Requires `BlktTotalFullValueAmount > 0`, else `Premium = 0.0`:

```
Premium =
    BlktSpecialAvgRate
  x (FullBldgValue / BlktTotalFullValueAmount)
  x (BlktLimit / 100)
  x PackageModFactor
  x MultiPremiumAndDispersionCreditFactor
  x IRPMFactor
  x CyberIncidentExclusionFactorSpecial
  x CyberIncidentExclusionCOLExcptnsFactorSpecial
```

Again nested `Product` rather than `Round`, and factor order reversed relative to the Basic files.

### Branch D — otherwise
`Premium = 0.0`.

### Premium indicator
`SetPremiumIndicator` (line 266) and `CalculateTotalPremium` (line 10) are identical to the Basic forms.

---

## Group I vs Group II — side by side

| | Basic Group I | Basic Group II |
|---|---|---|
| Rate keys | ClassCode + ConstructionCode | RatingTerr + ConstructionSymbol |
| Symbol prerequisite | none | `SetBasicGroupIISymbol` (line 4003) |
| Territory | multiplier (`BasicGroupIRatingTerrFactor`) | lookup key |
| Rating-type branch | Class / Specific / Tentative / other | none — single path |
| Rate addends | `SubStdConditionRate`, `VacantBuildingRate` | none |
| Peril-specific factors | protection class | numeric value, BCEG, cosmetic roof excl |
| Second rate path | none | `LowestBasicGroupIIBaseRate` (wind/hail excluded) |
| COL adjustment inputs | sprinkler leakage, vandalism | wind/hail exclusion, fire-only gate |
| Coinsurance | shared `SetCoinsuranceFactor` | own rule; flat factor at 50/60/70/None |
| Deductible by location | shared `DeductibleByLocationFactor` | own `BGIIDeductibleByLocationFactor` |
| Deductible factor keys | `Deductible` | `WindstormOrHailDeductible` or `Deductible` |
| Premium file | identical structure | identical structure |
| Chain length | 8 rules | 11 rules |

---

## Four-way comparison

| | Basic Group I | Basic Group II | Broad | Special |
|---|---|---|---|---|
| Chain length | 8 rules | 11 rules | **6 rules** | 9 rules |
| Base rate keys | ClassCode + ConstructionCode | RatingTerr + Symbol | **ConstructionType + covType** | flat statewide constant |
| Base rate gated on | `RatingType = Class` | Symbol + Terr present | COL = "Broad" + ConstructionType | COL = "Special" |
| Rating-type branch | Class / Specific / Tentative | none | none | none |
| Rate formula | 3 factors + 2 addends | 5 factors | LCM only | LCM only |
| COL adjustment step | yes | yes | **none** | yes |
| Territory | multiplier | lookup key | not used | not used |
| Protection class | multiplier | not used | not used | not used |
| Construction | rate key | symbol key | **rate key** | not used |
| Peril credit | sprinkler leakage, vandalism | wind/hail exclusion | **none** | theft exclusion (0.88 CW) |
| Coinsurance | `SetCoinsuranceFactor` | own rule + flat factor | shared `CoinsuranceFactor` | shared `CoinsuranceFactor` |
| LOI matrix | BGI LOI table | BGII LOI table | **`BroadSpecialLOIFactorBldg`** | **`BroadSpecialLOIFactorBldg`** |
| Deduct-by-location | shared factor | own (wind/hail ded) | **shared factor** | own (theft ded) |
| Deductible factor keys | `Deductible` | `WindstormOrHailDeductible` \| `Deductible` | `Deductible` | `TheftDeductible` \| `Deductible` |
| AOI band for deductible | `TotAmtInsurance` | `TotAmtInsurance` | `TotAmtInsurance` | `SpecialTotAmtInsurance` / `...IncludingTheft` |
| Blank-deductible fallback | — | — | **0.0** | — |
| Roof-surfacing ACV applied in | rate step | rate step | **adjusted-rate step** | COL adjustment |
| Coverage gate | COL not blank / not N/A | COL not blank / not N/A | **COL = "Broad"** exactly | **COL = "Special"** exactly |
| Premium rounding | nested `Round` × 3 | nested `Round` × 3 | nested `Round` × 3 | **nested `Product`, no `Round`** |
| Legal Liability uses | COL adjustment | COL adjustment | **raw `BroadRate`** | **raw `SpecialRate`** |
| Blanket branch tests | `IncludedInBlkt` | `IncludedInBlkt` | + `BlktCauseOfLossValue` | + `BlktCauseOfLossValue` |
| Premium file vs BGI | — | byte-identical (renamed) | **BGI shape + COL guards** | **structurally different** |

---

## Supporting lookups (Basic Group I)

| Rule | Matrix | Purpose |
|---|---|---|
| `LookupBasicGroupIRate` | `BasicGroupIRate` | Class base rate |
| `LookupBasicGroupILOIFactor` / `...WithArgs` | LOI factor table | Limit-of-insurance factor |
| `LookupSublineBasicGroupI` | subline table | Statistical subline |
| `LookupSublineBasicGroupIExcludingSprinklerLeakage` | subline table | Subline when sprinkler leakage excluded |
| `LookupSublineBasicGroupIExcludingVandalism` | subline table | Subline when vandalism excluded |
| `LookupSublineBasicGroupIExcludingVandalismAndSprinklerLeakage` | subline table | Both exclusions |
| `SetBasicGroupIRatingTerr` / `SetBasicGroupIRatingTerrFactor` | territory table | Territory and its factor (lines 898, 903) |
| `SetBasicGroupIDeductibleStatCode` | stat code table | Statistical reporting |

Every `Lookup` in this ruleset follows the same two-pass pattern: try the state-specific row keyed on `/*/State/Code`, then fall back to a `CW` row, wrapped in `FirstNonNull`.

---

## Supporting lookups (Basic Group II)

| Rule | Matrix | Keys |
|---|---|---|
| `LookupBasicGroupIIRate` | `BasicGroupIIRate` | State\|CW, RatingTerr, SymbolToUse, "Bldg" |
| `LookupLowestBasicGroupIIRate` | `LowestBasicGroupIIRate` | State\|CW, SymbolToUse, "Bldg" |
| `LookupGroupIINumericValue` | `GroupIINumericValue` | State\|CW, ClassCodeToUse, ConstructionCode |
| `LookupGroupIIOpenSidesNumericValue` | `GroupIIOpenSidesNumericValue` | State\|CW, ConstructionCode |
| `LookupBasicGroupIIConstructionSymbol` | `BasicGroupIIConstructionSymbol` | State\|CW, ConstructionType, NumStories |
| `LookupBasicGroupIISymbolAdditionalClasses` | additional-classes symbol table | with explicit args |
| `LookupBGIISymbolAdditionalClassesRoofConstruction` | roof-construction symbol table | — |
| `LookupBasicGroupIISymbolOilDistributingStations` | oil-distributing-stations symbol table | — |
| `LookupBasicGroupIIFlatCoinsuranceFactor` | `BasicGroupIIFlatCoinsuranceFactor` | State\|CW, "Y" |
| `LookupBasicGroupIILOIFactor` / `...WithArgs` | BGII LOI factor table | — |
| `LookupBasicGroupIIConstructionStatCode` | construction stat code table | — |
| `LookupSublineBasicGroupII` | subline table | — |
| `LookupSublineBasicGroupIIExcludingWindstormOrHail` | subline table | — |

Stat-code rules: `SetBasicGroupIIConstructionStatCode` (line 21626), `SetSublineBasicGroupII` (line 21864).

---

## Supporting lookups (Broad)

| Rule | Matrix | Keys | CW value |
|---|---|---|---|
| `LookupBroadFormBaseRate` (line 24544) | `BroadFormBaseRate` | State\|CW, ConstructionTypeToUse, covType param | 0.015 / 0.010 (Bldg), 0.012 (BldrRisk) |
| `LookupBroadSpecialLOIFactor` (line 25727) | `BroadSpecialLOIFactorBldg` | State\|CW, Limit | — |
| `LookupBroadSpecialLOIFactorWithArgs` (line 25749) | `BroadSpecialLOIFactorBldg` | State\|CW, explicit limit arg | — |
| `LookupDeductibleFactor` | deductible factor table | Deductible, `TotAmtInsurance`, "Other Cause Of Loss" | — |
| `LookupDeductible250Factor` | $250 deductible table | causeOfLoss = "Broad" | — |
| `LookupSublineBroadForm` (line 25414) | subline table | — | — |

Stat-code rule: `SetSublineBroadForm` (line 21912). Blanket LOI: `SetBlktBroadLOIFactor` (line 7425).

`BroadFormBaseRate` is filed under bureau rule **71.E.2 / 71.E.3 / 71.E.4** and is shared across coverage types via its `CovType` key — `Bldg`, `BldrRisk`, `PersProp`, and Business Income variants all live in the one table.

---

## Supporting lookups (Special)

| Rule | Matrix | Keys | CW value |
|---|---|---|---|
| `LookupSpecialBuildingRate` (line 25772) | `SpecialBuildingRate` | State\|CW, "Y" | *none filed* |
| `LookupSpecialBuildersRiskRate` (line 25236) | `SpecialBuildersRiskRate` | State\|CW, "Y" | 0.015 |
| `LookupSpecialBldgTheftExclusionFactor` (line 25788) | `SpecialBldgTheftExclusionFactor` | State\|CW, "Y" | 0.88 |
| `LookupBroadSpecialLOIFactor` (line 25727) | `BroadSpecialLOIFactorBldg` | State\|CW, Limit | — |
| `LookupBroadSpecialLOIFactorWithArgs` (line 25749) | `BroadSpecialLOIFactorBldg` | State\|CW, explicit limit arg | — |
| `LookupDeductibleFactor` | deductible factor table | deductible, AOI, "Other Cause Of Loss" | — |
| `LookupDeductible250Factor` | $250 deductible table | "Special", … | — |
| `LookupSublineSpecialFormExcludingTheft` (line 25430) | subline table | — | — |
| `LookupSublineSpecialFormIncludingTheft` (line 25446) | subline table | — | — |

Stat-code rule: `SetSublineSpecialForm` (line 21957) — picks the including-theft or excluding-theft subline based on the theft exclusion indicator.

Related validation messages: `DoMessageFormCP0414CannotBeAttachedWhenCauseOfLossIsDifferentThanSpecial` (line 20064), `DoMessageFormCP1033CannotBeAttachedWhenCauseOfLossIsDifferentThanSpecial` (line 20104).

---

## Quick reference — end-to-end, class-rated scheduled building

```
BaseRate        = lookup(State|CW, ClassCode, ConstructionCode, "Not Applicable", "Building")

Rate            = ((BaseRate x LossCostMultiplier) + SubStdConditionRate + VacantBuildingRate)
                  x TerritoryFactor x ProtectionClassFactor x RoofSurfacingACVFactor

COLAdj          = round(Rate - SprinklerLeakageExclNonSprinkleredBldgRate, 3)
                  x SprinklerLeakageExclSprinkleredFactor x VandalismExclFactor
                  x StdPropPolGroupIFactor

AdjustedRate    = COLAdj x CoinsuranceFactor x LOIFactor

FinalRate       = AdjustedRate x DeductibleByLocationFactor x DeductibleFactor
                  x MultiResidentialPropSpecialCreditFactor

Premium         = round(IRPM x MultiPremiumDispersion x PackageMod x FinalRate x (Limit/100), 0)
                  x CyberExclFactorBGI x CyberExclCOLExcptnsFactorBGI
```

All intermediate rate products carry 3 decimal places; the premium product carries 0.

## Quick reference — end-to-end, Basic Group II scheduled building

```
Symbol          = LookupBasicGroupIIConstructionSymbol(State|CW, ConstructionType, NumStories)
                  ... overridden for additional classes / oil distributing stations
Terr            = BasicGroupIIRatingTerr (copied from location)

NumericValue    = 1.0                             if wind/hail excluded
                | lookup(State|CW, ClassCode, ConstructionCode)   if class in (0580,0585,1150,1300,1650)
                | lookup(State|CW, ConstructionCode)              if OpenSides = Yes
                | 1.0

BaseRate        = lookup(State|CW, Terr, Symbol, "Bldg")
LowestBaseRate  = lookup(State|CW, Symbol, "Bldg")

Rate            = BaseRate x LossCostMultiplier x NumericValue
                  x RoofSurfacingACVFactor x RoofSurfacingCosmeticExclFactor x BCEGFactor

COLAdj          = 0.0                                          if CauseOfLoss is fire-only
                | Rate x StdPropPolGroupIIFactor               if no wind/hail exclusion
                | LowestBaseRate x LossCostMultiplier
                  x RoofSurfacingACVFactor x RoofSurfacingCosmeticExclFactor
                  x WindstormOrHailExclFactor x StdPropPolGroupIIFactor

CoinsFactor     = flat lookup(State|CW, "Y")   if Coinsurance in (50%,60%,70%,None)
                | CoinsuranceFactor            (Group I's shared factor)

AdjustedRate    = COLAdj x CoinsFactor x BGIILOIFactor

FinalRate       = AdjustedRate x BGIIDeductibleByLocationFactor x DeductibleFactorBGII
                  x MultiResidentialPropSpecialCreditFactor

Premium         = round(IRPM x MultiPremiumDispersion x PackageMod x FinalRate x (Limit/100), 0)
                  x CyberExclFactorBGII x CyberExclCOLExcptnsFactorBGII
```

## Quick reference — end-to-end, Broad scheduled building

```
BaseRate        = lookup BroadFormBaseRate(State|CW, ConstructionTypeToUse, "BldrRisk")
                                                          if ClassCode = 1150      [CW 0.012]
                | lookup BroadFormBaseRate(State|CW, ConstructionTypeToUse, "Bldg")
                                                          otherwise    [CW 0.015 / 0.010 FR]
                | 0.0        if COL <> Broad or ConstructionTypeToUse is blank

Rate            = BaseRate x LossCostMultiplier

                  (no cause-of-loss adjustment step for Broad)

LOIFactor       = BlktBroadLOIFactor                      if blanketed and BlktIDNum > 0
                | lookup BroadSpecialLOIFactorBldg(State|CW, BuildersRiskLimit)  if Builders Risk
                | lookup BroadSpecialLOIFactorBldg(State|CW, Limit)              if normal cov type
                | 1.0

AdjustedRate    = Rate x RoofSurfacingACVFactor x CoinsuranceFactor x LOIFactor

DedFactor       = lookup Deductible250Factor("Broad")            if Deductible = 250
                | 1.0                                            if Deductible = Not Applicable
                | lookup DeductibleFactor(Deductible, TotAmtInsurance, "Other Cause Of Loss")
                | 0.0                                            if Deductible blank

FinalRate       = AdjustedRate x DeductibleByLocationFactor x DedFactor
                  x MultiResidentialPropSpecialCreditFactor

Premium         = round(IRPM x MultiPremiumDispersion x PackageMod x FinalRate x (Limit/100), 0)
                  x CyberExclFactorBroad x CyberExclCOLExcptnsFactorBroad
```

## Quick reference — end-to-end, Special scheduled building

```
TheftExclFactor = lookup(State|CW, "Y")   if COL = Special and CP 10 33 attached   [CW 0.88]
                | 1.0

BaseRate        = lookup SpecialBuildersRiskRate(State|CW, "Y")   if ClassCode = 1150  [CW 0.015]
                | lookup SpecialBuildingRate(State|CW, "Y")       otherwise            [CW none]
                | 0.0                                             if COL <> Special

Rate            = BaseRate x LossCostMultiplier

COLAdj          = Rate x TheftExclFactor x RoofSurfacingACVFactor

LOIFactor       = BlktSpecialLOIFactor                       if blanketed and BlktIDNum > 0
                | lookup BroadSpecialLOIFactorBldg(State|CW, BuildersRiskLimit)  if Builders Risk
                | lookup BroadSpecialLOIFactorBldg(State|CW, Limit)              if normal cov type
                | 1.0

AdjustedRate    = COLAdj x CoinsuranceFactor x LOIFactor

FinalRate       = AdjustedRate x SpecialDeductibleByLocationFactor x DeductibleFactorSpecial
                  x MultiResidentialPropSpecialCreditFactor

Premium         = FinalRate x (Limit/100) x PackageMod x MultiPremiumDispersion x IRPM
                  x CyberExclFactorSpecial x CyberExclCOLExcptnsFactorSpecial
                  (nested Product DecimalPlaces=0 — no Round wrappers)
```

---
