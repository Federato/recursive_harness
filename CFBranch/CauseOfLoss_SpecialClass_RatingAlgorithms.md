# Cause of Loss — Special Class Rating Algorithms

**Source ERC package:** `C:\Projects\ISO_ERC_Files\CF\20260601\CFCW20260601V01`
**Line:** Commercial Property (CF), Countrywide, edition 06-01-2026, V01
**Documented:** 2026-08-19

Special Class rating lives in the `CommercialPropertySpecialClass` datadef group — ISO's name for scheduled/specialized classes of property (named commodities, agricultural products, signs, antennas, and other classes that get their own filed rate rather than being rated as generic Building or Personal Property). Unlike Building (`CommercialPropertyStructure`), Special Class is driven by a **named class description** (`ClassDescription`), not by construction type or a generic class code.

Four cause-of-loss rate chains are built for every Special Class item, plus a fifth, **Earthquake**, that is native to the Special Class datadef group (Earthquake is not merely an outside endorsement bolted on — its base rate/coinsurance/deductible chain is computed inside `CommercialPropertySpecialClassRules.Rule.xml` itself, alongside BGI/BGII/Broad/Special). This document covers the four core cause-of-loss forms in full; Earthquake is noted only where it illuminates a structural point, per scope.

- **Basic Group I** — fire, lightning, explosion, smoke, aircraft/vehicles
- **Basic Group II** — windstorm/hail, riot/civil commotion, vandalism, sprinkler leakage, sinkhole
- **Broad** — Basic plus falling objects, weight of snow/ice, water damage, collapse
- **Special** — open perils; all risks of direct physical loss except those excluded

---

## Master orchestration

All chains are prepared and run from `SetBlanketRatesAndFactors` (line 1864) in `CommercialPropertySpecialClassRules.Rule.xml`:

```
... shared prep (lines 1866-1887) ...
    SetEQCauseOfLossForm
    SetBasicGroupIIRatingTerr
    SetLossCostMultiplier
    SetEQDeductibleTier / SetEQTerr / SetEQSubLimitBlktIndicator / SetEQClassToUse
    SetProtectionClassToUse
    SetStdPropPolGroupIFactor / SetStdPropPolGroupIIFactor
    SetSpecialClassDescConvertedOption        <- Basic Group I prerequisite (class-description lookup)
    SetBasicGroupIISymbolNum                  <- Basic Group II prerequisite (numeric value, by ClassDescription)
    SetMarginClauseFactor
    SetMultiPremiumAndDispersionCreditFactor
    SetTotalAmountsToUse
    SetVandalismExclFactor
    SetInitializeFloodRatingSpecialClass
    InitializeDeductiblesByLocation / SetDeductibleByLocationFactor
    SetWindstormOrHailExclFactor / SetWindstormHailIndicator / SetWindstormOrHailDeductibleFactor

SetBGIRatesAndFactors        (line 2812)
SetBGIIRatesAndFactors       (line 3184)
SetBroadRatesAndFactors      (line 3713)
SetSpecialRatesAndFactors    (line 3916)
SetEQRatesAndFactors         (line 4315)   <- out of scope for this pass, noted only

SetProtectionClassFactor     (line 5724)   <- computed last; see "Orphaned factor" note below
```

Same pattern as Building: every chain computes a rate regardless of which cause of loss is actually on the policy; each coverage's own `SetCoverageOnPolicyIndicator` decides which one produces premium. **But the gating differs by form** — see "Coverage gate" row in the comparison table below.

---

## File map

| Piece | File | Anchor |
|---|---|---|
| Rate build-up, Basic Group I | `Rules\CommercialPropertySpecialClassRules.Rule.xml` | `SetBGIRatesAndFactors` — line 2812 |
| Rate build-up, Basic Group II | `Rules\CommercialPropertySpecialClassRules.Rule.xml` | `SetBGIIRatesAndFactors` — line 3184 |
| Rate build-up, Broad | `Rules\CommercialPropertySpecialClassRules.Rule.xml` | `SetBroadRatesAndFactors` — line 3713 |
| Rate build-up, Special | `Rules\CommercialPropertySpecialClassRules.Rule.xml` | `SetSpecialRatesAndFactors` — line 3916 |
| Rate build-up, Earthquake (out of scope) | `Rules\CommercialPropertySpecialClassRules.Rule.xml` | `SetEQRatesAndFactors` — line 4315 |
| Premium calc, Basic Group I | `Rules\CommercialPropertySpecialClassBasicGroupICoverageRules.Rule.xml` | `SetPremium` — line 43 |
| Premium calc, Basic Group II | `Rules\CommercialPropertySpecialClassBasicGroupIICoverageRules.Rule.xml` | `SetPremium` — line 43 |
| Premium calc, Broad | `Rules\CommercialPropertySpecialClassBroadCoverageRules.Rule.xml` | `SetPremium` |
| Premium calc, Special | `Rules\CommercialPropertySpecialClassSpecialCoverageRules.Rule.xml` | `SetPremium` — line 60 |
| Base rate tables | `Rate Tables\BasicGroupIRateSpecialClass.RateTable.csv`, `BasicGroupIIRate...` (shared w/ Building), `BroadFormBaseRate...` (shared w/ Building), `SpecialBuildingRate...` (shared w/ Building) | each + a `...Def.RateTableDef.xml` |
| Class-description lookups | `Rate Tables\SpecialClassDescriptionConvertedOption.RateTable.csv`, `SpecialClassBasicGroupIINumber.RateTable.csv` | 71 named classes each |
| Not core — endorsement add-ons excluded from this pass | `CommercialPropertySpecialClassAgreedVal*CoverageRules.Rule.xml`, `CommercialPropertySpecialClassInflationGuard*CoverageRules.Rule.xml`, `CommercialPropertySpecialClassBusnIncome*` | Agreed Value / Inflation Guard / Business Income endorsements layer on top of the core rate chains documented here |

> **Endorsement files excluded per scope.** `CommercialPropertySpecialClass{AgreedVal,InflationGuard}*CoverageRules.Rule.xml` exist for all five cause-of-loss forms but are optional endorsements that adjust `Premium` after the core chains below run; they were not traced.

---

## Basic Group I — rate build-up

Executed in order by `SetBGIRatesAndFactors` (line 2812) — **7 steps**, the shortest of the four core chains and 1 step shorter than Building's 8-step Basic Group I chain (Special Class has **no LOI-factor step at all** — see below):

```
SetCoinsuranceFactor
SetBasicGroupIBaseRate
SetBasicGroupIRate
SetBasicGroupICauseOfLossAdjustment
SetAdjustedBasicGroupIRate
SetDeductibleFactorBasicGroupI
SetFinalBasicGroupIRate
```

### Step 1 — Coinsurance factor
`SetCoinsuranceFactor` (line 2823) — computed **first**, before the base rate, unlike Building where coinsurance is computed after the rate and COL-adjustment steps. Four-way `Choose`:

| Branch | Condition | Result |
|---|---|---|
| 1 | `Coinsurance` in (80%, 90%) OR (`Coinsurance`=100% and `IncludedInBlkt`="No") | `LookupCoinsuranceFactor` |
| 2 | `BlktCoinsurance` in (80%, 90%, 100%) and `IncludedInBlkt`="Yes" | `LookupBlktCoinsuranceFactor` |
| 3 | `Coinsurance` or `BlktCoinsurance` in (50%, 60%, 70%, None) | `LookupLessThan80PctMultiplicativeFactor` |
| 4 | otherwise | 1.0 |

This single `CoinsuranceFactor` is shared downstream by Basic Group I, Broad, and Special (Basic Group II gets its own, see below) — same sharing pattern as Building.

### Step 2 — Base rate
`SetBasicGroupIBaseRate` (line 2979)

```
if SpecialClassDescConvertedOption is non-blank and ProtectionClassToUse is non-blank:
    BasicGroupIBaseRate = LookupBasicGroupIRateSpecialClass(...)
else:
    BasicGroupIBaseRate = 0.0
```

**This is the single biggest structural departure from Building.** `LookupBasicGroupIRateSpecialClass` (line 11436) reads matrix `BasicGroupIRateSpecialClass`, column `Rate`, keyed on:

1. `/*/State/Code` (falls back to `CW`)
2. `SpecialClassDescConvertedOption`
3. `ProtectionClassToUse`

There is **no `ConstructionCode` key at all** — Special Class's Basic Group I base rate does not vary by construction. `SpecialClassDescConvertedOption` is itself a lookup (`LookupSpecialClassDescriptionConvertedOption`, line 11892) that maps the user-entered `ClassDescription` (a named commodity/class, e.g. "Aircraft Stored in the Open") to one of 71 filed "OptionNN" codes via matrix `SpecialClassDescriptionConvertedOption`. And **protection class is folded into the base-rate lookup key itself**, not applied as a separate multiplicative factor the way Building's `ProtectionClassFactor` is (see "Orphaned factor" note below).

CW file `BasicGroupIRateSpecialClass.RateTable.csv` contains 213 data rows (71 class-description options × up to 3 protection-class bands: "1 to 4", "5 to 8", and presumably "9" or similar) — e.g. `CW, Option1a, "1 to 4", 0.044`.

### Step 3 — Rate
`SetBasicGroupIRate` (line 3029), 3 decimals, only when currently null:

```
BasicGroupIRate = BasicGroupIBaseRate x LossCostMultiplier
```

That is the entire rate step — no territory factor, no protection-class factor, no substandard-condition or vacant-building addend, no roof-surfacing ACV factor. Compare Building's Basic Group I rate, which multiplies by `TerritoryFactor x ProtectionClassFactor x RoofSurfacingACVFactor` and adds two rate addends.

### Step 4 — Cause-of-loss adjustment
`SetBasicGroupICauseOfLossAdjustment` (line 3048), 3 decimals, unconditional (no `IsNull` guard):

```
BasicGroupICauseOfLossAdjustment = BasicGroupIRate x VandalismExclFactor x StdPropPolGroupIFactor
```

Building's equivalent also subtracts a sprinkler-leakage-exclusion rate and applies a sprinkler-leakage-exclusion factor; Special Class's Basic Group I has **no sprinkler-leakage dimension** in this step at all — only vandalism and the standard-property-policy factor.

### Step 5 — Adjusted rate
`SetAdjustedBasicGroupIRate` (line 3059)

```
AdjustedBasicGroupIRate = BasicGroupICauseOfLossAdjustment x CoinsuranceFactor
```

**No LOI-factor multiplication here** — confirmed by exhaustively searching `CommercialPropertySpecialClassRules.Rule.xml` for any rule name containing `LOIFactor`: there is none. Building's `AdjustedBasicGroupIRate` is `COLAdj x CoinsuranceFactor x LOIFactor`; Special Class drops the third term entirely. This holds across all four core forms — none of Special Class's rate chains compute a limit-of-insurance factor, and none of the four premium files reference one either (confirmed in premium section below).

### Step 6 — Deductible
`SetDeductibleFactorBasicGroupI` (line 3078), a three-way `Choose` on `Deductible` (250 / non-blank / blank), functionally identical in shape to Building's:

```
DeductibleFactorBasicGroupI = LookupDeductible250Factor("Basic")          if Deductible = "250"
                             | LookupDeductibleFactor(Deductible, TotAmtInsuranceToUse, "Basic Group I")   if Deductible non-blank
                             | 0.0                                        otherwise
```

Note the amount-of-insurance key is `TotAmtInsuranceToUse` (a Special Class-scoped total), not Building's `TotAmtInsurance`.

### Step 7 — Final rate
`SetFinalBasicGroupIRate` (line 3162)

```
FinalBasicGroupIRate = AdjustedBasicGroupIRate x DeductibleByLocationFactor x DeductibleFactorBasicGroupI
```

Three factors, not Building's four — there is no `MultiResidentialPropSpecialCreditFactor` multiplication anywhere in the Special Class chains (that credit is Building/Personal-Property specific; it does not apply to scheduled Special Class items).

---

## Basic Group I — premium

`CommercialPropertySpecialClassBasicGroupICoverageRules.Rule.xml`

### Gate 1 — coverage on policy
`SetCoverageOnPolicyIndicator` (line 32) is **hard-coded to `CoverageOnPolicyIndicator = 1`** — unconditional, no test at all. Contrast Building's Basic Group I gate ("not blank / not Not Applicable") and Special Class's own Broad/Special gates (exact `CauseOfLossToUse` match, below). Basic Group I and Basic Group II premium in Special Class is therefore always computed whenever a Basic-Group-I coverage record exists on the item — cause-of-loss selection is enforced upstream (only the matching coverage record is instantiated), not by a datadef test inside this file.

### Two-branch structure — no Legal Liability, no separate class-rated gate
Unlike Building's four branches (scheduled / Legal Liability / blanket / otherwise), Special Class's `SetPremium` (line 43) has **only two branches**, keyed on a single `IncludedInBlkt = "Yes"` test:

**Branch A — blanket** (`IncludedInBlkt = "Yes"`), zero when `BlktTotalFullValueAmount = 0`:

```
Premium =
  round(
      (BlktLimit / 100)
    x (FullSpecialClassValue / BlktTotalFullValueAmount)
    x BlktBasicGroupIAvgRate
    x PackageModFactor
    x MultiPremiumAndDispersionCreditFactor
    x IRPMFactor
  , 0)
  x CyberIncidentExclusionFactorBGI
  x CyberIncidentExclusionCOLExcptnsFactorBGI
```

**Branch B — scheduled** (`IncludedInBlkt` anything else):

```
Premium =
  round(
      (Limit / 100)
    x FinalBasicGroupIRate
    x PackageModFactor
    x MultiPremiumAndDispersionCreditFactor
    x IRPMFactor
  , 0)
  x CyberIncidentExclusionFactorBGI
  x CyberIncidentExclusionCOLExcptnsFactorBGI
```

No Legal Liability branch, no Builders Risk Reporting Form gate, no `CovType` `Choose` at all — Special Class items don't carry the Building-specific `CovType` taxonomy (Builders Risk / Improvements & Betterments / Condominium Association / Leasehold Interest / Legal Liability). This is consistent with Special Class covering discrete scheduled property, which is always either scheduled individually or folded into a blanket — there is no "leasehold interest in a building" analogue.

Both branches use nested `Round DecimalPlaces="0"` wrappers (matching Building's Basic/Broad rounding convention, not Special-form's `Product`-only convention), applied around six factors instead of Building's five (Special Class has no separate `PackageModFactor`-before-`MultiPremium` ordering distinction worth noting — order here is Limit → Rate → PackageMod → MultiPremium → IRPM, then the two cyber factors outside the round).

### Premium indicator / total
`SetPremiumIndicator` (line 134) and `CalculateTotalPremium` (line 10) are byte-identical in logic to Building's: `PremiumIndicator = 1` iff `Premium <> 0.0`; `CalculateTotalPremium` returns `Premium` only when both the indicator is 1 and `Premium <> 0`.

---

## Basic Group II — differences

Executed in order by `SetBGIIRatesAndFactors` (line 3184) — **10 steps**, one shorter than Building's 11 (no `SetBasicGroupIISymbol` prerequisite rule — see below):

```
SetBasicGroupIINumericValue
SetBasicGroupIIBaseRate
SetLowestBasicGroupIIBaseRate
SetBasicGroupIIRate
SetBasicGroupIICauseOfLossAdjustment
SetBasicGroupIICoinsuranceFactor
SetAdjustedBasicGroupIIRate
SetBGIIDeductibleByLocationFactor
SetDeductibleFactorBasicGroupII
SetFinalBasicGroupIIRate
```

### Prerequisite — construction symbol is a plain input, not derived
Building resolves `BasicGroupIISymbol` from `ConstructionType` + `NumStories` via `SetBasicGroupIISymbol`/`LookupBasicGroupIIConstructionSymbol`. **`CommercialPropertySpecialClassRules.Rule.xml` contains no rule that assigns `BasicGroupIISymbol`** (confirmed by grep — zero `ToDataDef="BasicGroupIISymbol"` matches). It is read directly wherever needed (`LookupBasicGroupIIRate`, `LookupLowestBasicGroupIIRate`), implying it is either a data-entry field on the Special Class item or copied down from elsewhere outside this ruleset — this could not be resolved from `CommercialPropertySpecialClassRules.Rule.xml` alone (open question, see final report).

### Step 1 — Numeric value
`SetBasicGroupIINumericValue` (line 3198)

```
if no CommercialPropertyWindstormOrHailExclusionSpecialClass record exists:
    BasicGroupIINumericValue = BasicGroupIISymbolNum
else:
    BasicGroupIINumericValue = 1.0
```

`BasicGroupIISymbolNum` is set during shared prep (`SetBasicGroupIISymbolNum`, line 2040) via `LookupSpecialClassBasicGroupIINumber` (line 11860), keyed on `State|CW` + `ClassDescription` (the raw class description, not the converted option) against matrix `SpecialClassBasicGroupIINumber` — a **named-class lookup**, not Building's class-code/open-sides logic (`LookupGroupIINumericValue` / `LookupGroupIIOpenSidesNumericValue`). This is the clearest expression of Special Class's core difference: every class-specific hazard factor is looked up by the free-text `ClassDescription`, converted through one of two small per-class option tables (`SpecialClassDescriptionConvertedOption` for Group I, `SpecialClassBasicGroupIINumber` for Group II), rather than by `ClassCode`/`ConstructionCode`/`OpenSides` the way Building does.

### Step 2 — Base rate
`SetBasicGroupIIBaseRate` (line 3215)

Requires `BasicGroupIIRatingTerr` and `BasicGroupIISymbol` both non-blank; else 0.0. `LookupBasicGroupIIRate` (line 11416) keys on State|CW / `BasicGroupIIRatingTerr` / `BasicGroupIISymbol` / `"Bldg"` — reading matrix `BasicGroupIIRate`, the **same table Building uses**. Confirmed present with matching Def at `Rate Tables\BasicGroupIIRate.RateTable.csv`.

### Step 3 — Lowest base rate
`SetLowestBasicGroupIIBaseRate` (line 3265) — same shape as Building, reading the shared `LowestBasicGroupIIRate` matrix keyed on State|CW / Symbol / `"Bldg"` (no territory).

### Step 4 — Rate
`SetBasicGroupIIRate` (line 3309), 3 decimals:

```
BasicGroupIIRate = BasicGroupIIBaseRate x LossCostMultiplier x BasicGroupIINumericValue
```

Three factors, not Building's six — **no roof-surfacing ACV factor, no roof-surfacing cosmetic-exclusion factor, no BCEG factor**. Special Class scheduled items apparently carry no roof-condition or building-code-effectiveness dimension.

### Step 5 — Cause-of-loss adjustment
`SetBasicGroupIICauseOfLossAdjustment` (line 3331)

**Gate.** Fire-only exclusion is narrower than Building's four-way fire-cause test — Special Class checks only `"Fire"` and `"Fire and Vandalism"` (no `"Fire and Sprinkler Leakage"` or `"Fire, Vandalism and Sprinkler Leakage"` variants, consistent with Basic Group I here having no sprinkler-leakage dimension at all):

```
if CauseOfLossToUse in ("Fire", "Fire and Vandalism"):
    BasicGroupIICauseOfLossAdjustment = 0.0
elif no windstorm/hail exclusion:
    BasicGroupIICauseOfLossAdjustment = BasicGroupIIRate x StdPropPolGroupIIFactor
else:
    BasicGroupIICauseOfLossAdjustment =
        LowestBasicGroupIIBaseRate x LossCostMultiplier x WindstormOrHailExclFactor x StdPropPolGroupIIFactor
```

Same two-path shape as Building (rebuild from lowest base rate when wind/hail is excluded), but without the roof-surfacing/cosmetic factors Building applies in that branch (because Special Class never introduced them upstream).

### Step 6 — Coinsurance
`SetBasicGroupIICoinsuranceFactor` (line 3385) — same shape as Building: flat lookup (`LookupBasicGroupIIFlatCoinsuranceFactor`, State|CW + constant `"Y"`) when `Coinsurance` in (50%, 60%, 70%, None), else copy the shared `CoinsuranceFactor`. CW flat value is **1.5** (`BasicGroupIIFlatCoinsuranceFactor.RateTable.csv`, `CW,Y,1.5`) — notably **greater than 1**, a surcharge rather than a credit; worth flagging since Building's equivalent table was not confirmed at that value in the prior pass (open item — no direct comparison was made against Building's copy of the same table in this pass).

### Step 7 — Adjusted rate
`SetAdjustedBasicGroupIIRate` (line 3441) — `COLAdj x CoinsuranceFactor`, same two-factor shape as Basic Group I (no LOI factor, consistent with the chain-wide absence noted above).

### Step 8 — Deductible by location
`SetBGIIDeductibleByLocationFactor` (line 3460) — same conditions as Building (`WindstormHailIndicator = 0` and a location record with a real `WindstormOrHailDeductible`), but reads `CommercialPropertyDeductiblesByLocationSpecialClassTable`, Special Class's own by-location deductible datadef, not Building's.

### Step 9 — Deductible factor
`SetDeductibleFactorBasicGroupII` (line 3515) — same two-level structure as Building (outer test on whether a distinct wind/hail deductible applies, inner `Choose` on `Deductible`/`WindstormOrHailDeductible`).

### Step 10 — Final rate
`SetFinalBasicGroupIIRate` (line 3691)

```
FinalBasicGroupIIRate = AdjustedBasicGroupIIRate x BGIIDeductibleByLocationFactor x DeductibleFactorBasicGroupII
```

Three factors (no `MultiResidentialPropSpecialCreditFactor`, consistent with the whole datadef group).

---

## Basic Group II — premium

`CommercialPropertySpecialClassBasicGroupIICoverageRules.Rule.xml`

Structurally identical to the Basic Group I premium file above (confirmed by direct read): `SetCoverageOnPolicyIndicator` is hard-coded to 1, `SetPremium` has the same two branches (blanket / scheduled) with `BlktBasicGroupIIAvgRate` and `FinalBasicGroupIIRate` substituted for the Group I datadefs, and the same `CyberIncidentExclusionFactorBGII` / `CyberIncidentExclusionCOLExcptnsFactorBGII` pair applied outside the rounded product. No Legal Liability branch exists here either.

```
Premium =
  round((Limit/100) x FinalBasicGroupIIRate x PackageModFactor x MultiPremiumAndDispersionCreditFactor x IRPMFactor, 0)
  x CyberIncidentExclusionFactorBGII x CyberIncidentExclusionCOLExcptnsFactorBGII
```

---

## Broad — rate build-up

Executed in order by `SetBroadRatesAndFactors` (line 3713) — **5 steps**, the shortest chain, one shorter than Building's already-shortest 6-step Broad chain (Special Class's Broad has no deductible-by-location step of its own — it reuses the shared `DeductibleByLocationFactor` directly inside `SetFinalBroadRate`, same as Building):

```
SetBroadBaseRate
SetBroadRate
SetAdjustedBroadRate
SetDeductibleFactorBroad
SetFinalBroadRate
```

Like Building's Broad, there is **no cause-of-loss adjustment step**.

### Step 1 — Base rate
`SetBroadBaseRate` (line 3722)

```
if CauseOfLossToUse = "Broad" and PolicyType = "Commercial Property Policy":
    BroadBaseRate = LookupBroadFormBaseRate(...)
else:
    BroadBaseRate = 0.0
```

**`LookupBroadFormBaseRate` (line 11486) keys on a hard-coded literal `"Frame"` construction type**, not a `ConstructionTypeToUse` datadef value:

```
Keys: /*/State/Code (falls back to CW), Constant "Frame", Constant "Bldg"
```

This is a significant and easily-missed difference from Building, whose `LookupBroadFormBaseRate` keys on the item's actual `ConstructionTypeToUse` and therefore varies the rate by construction (0.015 combustible / 0.010 fire-resistive). **Special Class's Broad base rate is always the `"Frame"` row of `BroadFormBaseRate` — CW value 0.015 — regardless of the scheduled item's actual construction.** Confirmed by reading the rule's literal `<rul:Constant Type="string">Frame</rul:Constant>` key at line 11491, and by the table itself (`BroadFormBaseRate.RateTable.csv`, `CW,Frame,Bldg,0.015`). Whether this is an ERC-package quirk/placeholder or an intentional simplification for scheduled Special Class property could not be determined from the rules file alone — flagged as an open question.

### Step 2 — Rate
`SetBroadRate` (line 3772), 3 decimals:

```
BroadRate = BroadBaseRate x LossCostMultiplier
```

### Step 3 — Adjusted rate
`SetAdjustedBroadRate` (line 3791)

```
AdjustedBroadRate = BroadRate x CoinsuranceFactor
```

No roof-surfacing ACV factor here (Special Class never computes one) and no LOI factor — two fewer terms than Building's `AdjustedBroadRate`.

### Step 4 — Deductible factor
`SetDeductibleFactorBroad` (line 3810) — same three-way shape as Building (250 / non-blank / blank→0.0), using `TotAmtInsuranceToUse` and `causeOfLossDed = "Other Cause Of Loss"`.

### Step 5 — Final rate
`SetFinalBroadRate` (line 3894)

```
FinalBroadRate = AdjustedBroadRate x DeductibleByLocationFactor x DeductibleFactorBroad
```

---

## Broad — premium

`CommercialPropertySpecialClassBroadCoverageRules.Rule.xml`

### Gate — exact cause-of-loss match
`SetCoverageOnPolicyIndicator` tests `CauseOfLossToUse = "Broad"` exactly (confirmed by direct read) — same exact-match pattern Building uses for its Broad gate, and different from Special Class's own Basic Group I/II gates (hard-coded 1).

### Two-branch structure (blanket / scheduled)
Same shape as Basic Group I/II above — `IncludedInBlkt = "Yes"` branches to a blanket formula using `BlktBroadAvgRate` and `FullSpecialClassValue / BlktTotalFullValueAmount`; otherwise a scheduled formula using `FinalBroadRate` and `Limit`. No Legal Liability branch. Same nested-`Round`-to-0 convention as Basic Group I/II, and the `CyberIncidentExclusionFactorBroad` / `CyberIncidentExclusionCOLExcptnsFactorBroad` pair.

```
Premium =
  round((Limit/100) x FinalBroadRate x PackageModFactor x MultiPremiumAndDispersionCreditFactor x IRPMFactor, 0)
  x CyberIncidentExclusionFactorBroad x CyberIncidentExclusionCOLExcptnsFactorBroad
```

---

## Special — rate build-up

Executed in order by `SetSpecialRatesAndFactors` (line 3916) — **8 steps**:

```
SetSpecialTheftExclusionIndicator
SetSpecialTheftExclusionFactor
SetSpecialBaseRate
SetSpecialRate
SetSpecialCauseOfLossAdjustment
SetAdjustedSpecialRate
SetSpecialDeductibleByLocationFactor
SetDeductibleFactorSpecial
SetFinalSpecialRate
```

(9 `RunRule` lines, but `SetSpecialTheftExclusionIndicator` and `SetSpecialTheftExclusionFactor` are two small rules Building runs as a single prerequisite outside its own chain — net rate-build-up depth is comparable to Building's 9-step Special chain.)

### Steps 1-2 — Theft exclusion indicator and factor
`SetSpecialTheftExclusionIndicator` (line 3929): `1` if a `CommercialPropertyTheftExclusionSpecialClassTable` record exists, else `0` — Special Class's own theft-exclusion form attachment, distinct from Building's `CommercialPropertyTheftExclusion` table.

`SetSpecialTheftExclusionFactor` (line 3948):

```
if CauseOfLossToUse = "Special" and SpecialTheftExclusionIndicator = 1:
    SpecialTheftExclusionFactor = LookupSpecialBldgTheftExclusionFactor(State|CW, "Y")
else:
    SpecialTheftExclusionFactor = 1.0
```

CW value **0.88** (`SpecialBldgTheftExclusionFactor.RateTable.csv`, `CW,Y,0.88`) — identical to Building's theft-exclusion credit, and read from a table of the **same name** (`SpecialBldgTheftExclusionFactor`) — this table is shared between Building's Special form and Special Class's Special form.

### Step 3 — Base rate
`SetSpecialBaseRate` (line 3998)

```
if CauseOfLossToUse = "Special" and PolicyType = "Commercial Property Policy":
    if ClassCodeToUse = "1150":
        [this branch is unreachable in the rule as written — see below]
    SpecialBaseRate = LookupSpecialBuildingRate(...)
else:
    SpecialBaseRate = 0.0
```

`LookupSpecialBuildingRate` (line 12125) reads matrix `SpecialBuildingRate`, keyed on `State|CW` + constant `"Y"` — **the identical table name, key shape, and CSV file** Building's Special form uses (`Rate Tables\SpecialBuildingRate.RateTable.csv`). **That file contains only a header row — no `CW` row is filed** (confirmed: `grep` for any data row returns nothing beyond the header `"StateCode","Constant","Rate"`). So exactly as in Building, `SpecialBaseRate` resolves to null/unset at the countrywide level for Special Class too, unless a state files its own row. This is the same open filing gap noted in the Building doc, now confirmed to affect Special Class identically because the two forms share one table.

> Special Class has **no separate Builders Risk base-rate branch** analogous to Building's `ClassCodeToUse = "1150"` → `LookupSpecialBuildersRiskRate` path — `SpecialBaseRate` always resolves through `LookupSpecialBuildingRate` regardless of class code in this ruleset (confirmed by reading the full `SetSpecialBaseRate` rule body; no `LookupSpecialBuildersRiskRate` reference exists anywhere in `CommercialPropertySpecialClassRules.Rule.xml`).

### Step 4 — Rate
`SetSpecialRate` (line 4048), 3 decimals:

```
SpecialRate = SpecialBaseRate x LossCostMultiplier
```

### Step 5 — Cause-of-loss adjustment
`SetSpecialCauseOfLossAdjustment` (line 4067), unconditional:

```
SpecialCauseOfLossAdjustment = SpecialRate x SpecialTheftExclusionFactor
```

Two factors, not Building's three — **no roof-surfacing ACV factor** (Special Class never computes one anywhere in this datadef group).

### Step 6 — Adjusted rate
`SetAdjustedSpecialRate` (line 4075)

```
AdjustedSpecialRate = SpecialCauseOfLossAdjustment x CoinsuranceFactor
```

No LOI factor (consistent chain-wide).

### Step 7 — Deductible by location
`SetSpecialDeductibleByLocationFactor` (line 4094) — same shape as Building (triggered by a by-location theft deductible), reading `CommercialPropertyDeductiblesByLocationSpecialClassTable`.

### Step 8 — Deductible factor
`SetDeductibleFactorSpecial` (line 4145) — same four-branch shape as Building (separate theft deductible / flat $250 / standard / otherwise→0.0), using `SpecialIncludingTheftTotAmtInsuranceToUse` and `SpecialTotAmtInsuranceToUse` (Special-Class-scoped sums, analogous to Building's `SpecialIncludingTheftTotAmtInsurance` / `SpecialTotAmtInsurance`).

### Step 9 — Final rate
`SetFinalSpecialRate` (line 4293)

```
FinalSpecialRate = AdjustedSpecialRate x DeductibleByLocationFactor x DeductibleFactorSpecial
```

---

## Special — premium

`CommercialPropertySpecialClassSpecialCoverageRules.Rule.xml`

### Gate — exact cause-of-loss match
`SetCoverageOnPolicyIndicator` (line 32): `CoverageOnPolicyIndicator = 1` iff `CauseOfLossToUse = "Special"` — same exact-match pattern as Special Class's Broad gate and Building's Special gate.

### Two-branch structure — but NOT Building's nested-`Product`-no-`Round` pattern
Building's Special premium file is the one form whose rounding differs from the Basic/Broad pattern (nested `Product DecimalPlaces="0"` with no `Round` wrappers). **Special Class's Special premium file uses the standard nested-`Round`-to-0 pattern**, matching its own Basic Group I/II/Broad siblings — confirmed by direct read of `SetPremium` (lines 60-150): every branch wraps its factor chain in `Product ToDataDef="Premium" DecimalPlaces="0"` nests, identical in shape to the Basic Group I file above. Special Class does **not** carry forward Building's Special-specific rounding quirk.

```
Premium (scheduled) =
  round((Limit/100) x FinalSpecialRate x PackageModFactor x MultiPremiumAndDispersionCreditFactor x IRPMFactor, 0)
  x CyberIncidentExclusionFactorSpecial x CyberIncidentExclusionCOLExcptnsFactorSpecial

Premium (blanket, IncludedInBlkt = "Yes" and BlktTotalFullValueAmount > 0) =
  round((BlktLimit/100) x (FullSpecialClassValue/BlktTotalFullValueAmount) x BlktSpecialAvgRate
        x PackageModFactor x MultiPremiumAndDispersionCreditFactor x IRPMFactor, 0)
  x CyberIncidentExclusionFactorSpecial x CyberIncidentExclusionCOLExcptnsFactorSpecial
```

No Legal Liability branch (Special Class has no `CovType = "Legal Liability"` concept), no Builders Risk Reporting Form gate.

---

## Orphaned-factor note: `ProtectionClassFactor`

`SetProtectionClassFactor` (line 5724) computes `ProtectionClassFactor` via `LookupProtectionClassFactor` (State|CW + `../../ProtectClass` + constant `1`) whenever `../../ProtectClass` is non-blank. It runs **last** in the shared-prep/chain sequence (after all five `Set*RatesAndFactors` chains in `SetBlanketRatesAndFactors`, line 1893). A full-text search of `CommercialPropertySpecialClassRules.Rule.xml` for `FromDataDef="ProtectionClassFactor"` (as a read, not the write at line 5724 itself) turns up **only the two `IsNull` guard checks inside `SetProtectionClassFactor` itself** — the computed factor is never multiplied into any of Basic Group I/II, Broad, Special, or Earthquake's rate chains. Protection class instead enters Basic Group I's rate as a base-rate-table lookup **key** (`LookupBasicGroupIRateSpecialClass`, via `ProtectionClassToUse`). Whether `ProtectionClassFactor` is consumed by a Special-Class-specific stat/reporting rule not traced in this pass, or is genuinely vestigial in this datadef group, could not be determined from the rate/premium rules alone — flagged as an open question.

---

## Special Class vs. Building — structural comparison

| | Building | Special Class |
|---|---|---|
| Rating driver | ClassCode + ConstructionCode (BGI/BGII), ConstructionType (Broad) | **`ClassDescription`** (free-text/named class) converted via per-form option tables |
| Basic Group I base-rate keys | State\|CW, ClassCode, ConstructionCode, "Not Applicable", "Building" | State\|CW, **`SpecialClassDescConvertedOption`**, **`ProtectionClassToUse`** — no construction key |
| Protection class | applied as a rate **multiplier** (`ProtectionClassFactor`) | folded into the base-rate **lookup key**; the standalone `ProtectionClassFactor` is computed but unused downstream (see note above) |
| LOI (limit-of-insurance) factor | present in every form's rate chain and premium file | **absent from all four core rate chains and all four premium files** — Limit is applied directly, no LOI-factor multiplier anywhere |
| Sprinkler leakage dimension | present (Basic Group I COL adjustment, subline splits) | **absent** — Basic Group I's COL adjustment has no sprinkler-leakage term |
| Roof-surfacing ACV / cosmetic-exclusion factors | present in BGI, BGII, Broad, Special | **absent from all four forms** |
| BCEG factor | present in Basic Group II rate | **absent** |
| Substandard-condition / vacant-building rate addends | present in Basic Group I | **absent** |
| MultiResidentialPropSpecialCreditFactor | applied in every form's final-rate step | **absent from every form** |
| `CovType` taxonomy (Builders Risk / Legal Liability / Leasehold Interest / etc.) | drives 4-branch premium logic per form | **not present** — every Special Class premium file has just 2 branches (blanket / scheduled), no Legal Liability |
| Basic Group I/II coverage gate | "not blank / not Not Applicable" test on `CauseOfLossToUse` | **hard-coded to `1`** (always on) for BGI and BGII; Broad and Special use an exact `CauseOfLossToUse` match |
| Broad base-rate construction key | `ConstructionTypeToUse` (varies 0.015 combustible / 0.010 fire-resistive) | **hard-coded literal `"Frame"`** — always reads the 0.015 row regardless of actual construction |
| Special-form Builders Risk branch | `ClassCodeToUse = "1150"` → separate `SpecialBuildersRiskRate` table (CW 0.015) | **no such branch** — `SpecialBaseRate` always resolves through `LookupSpecialBuildingRate`, which shares Building's unfilled `SpecialBuildingRate` table (no CW row) |
| Special-form premium rounding | nested `Product`, **no** `Round` wrappers (a documented Building-only quirk) | standard nested `Round DecimalPlaces="0"` — same convention as its own BGI/BGII/Broad siblings |
| Earthquake | separate/outside this datadef group (not traced here) | **native fifth chain** (`SetEQRatesAndFactors`) inside the same `CommercialPropertySpecialClassRules.Rule.xml` file — out of scope for this pass but structurally notable |
| Chain length (BGI / BGII / Broad / Special) | 8 / 11 / 6 / 9 | **7 / 10 / 5 / 9** — Special Class is shorter or equal in every form except Special itself |

### Special Class vs. Personal Property (quick note)

A full trace of Personal Property was out of scope for this pass, but the file inventory shows Personal Property is its own datadef group (`CommercialPropertyBusinessPersonalProperty*` or similar, not grepped in this pass) with its own coverage-rules files, separate from both `CommercialPropertyStructure` and `CommercialPropertySpecialClass`. No claim is made here about how Personal Property's rate chains compare beyond noting that Special Class's `BroadFormBaseRate` table (shared with Building) also carries `PersProp` rows per the Building doc's Broad section — meaning Personal Property, Building, and (for the "Frame" row only) Special Class's Broad form all draw from one shared filed table. This was not independently verified against Personal Property's actual rule files in this pass — flagged as an open item if a future pass documents Personal Property.

---

## Four-way comparison (Special Class core forms)

| | Basic Group I | Basic Group II | Broad | Special |
|---|---|---|---|---|
| Chain length | 7 rules | 10 rules | 5 rules | 9 rules (incl. theft prereqs) |
| Base rate keys | `SpecialClassDescConvertedOption` + `ProtectionClassToUse` | `BasicGroupIIRatingTerr` + `BasicGroupIISymbol` (symbol origin unresolved — open question) | literal `"Frame"` + `"Bldg"` (construction-blind) | flat statewide constant (unfilled at CW — open question) |
| Base rate gated on | `SpecialClassDescConvertedOption` & `ProtectionClassToUse` present | `BasicGroupIIRatingTerr` & `BasicGroupIISymbol` present | `CauseOfLossToUse = "Broad"` & `PolicyType = "Commercial Property Policy"` | `CauseOfLossToUse = "Special"` & `PolicyType = "Commercial Property Policy"` |
| Rate formula | BaseRate × LCM | BaseRate × LCM × NumericValue | BaseRate × LCM | BaseRate × LCM |
| COL adjustment step | yes (Vandalism, StdPropPol) | yes (fire-only gate, wind/hail rebuild) | none | yes (theft exclusion) |
| Coinsurance | shared `CoinsuranceFactor` (computed first, in BGI's chain) | own rule + flat 1.5 surcharge | shared `CoinsuranceFactor` | shared `CoinsuranceFactor` |
| LOI factor | **none** | **none** | **none** | **none** |
| Deduct-by-location | shared `DeductibleByLocationFactor` | own `BGIIDeductibleByLocationFactor` (wind/hail ded) | shared `DeductibleByLocationFactor` | own `SpecialDeductibleByLocationFactor` (theft ded) |
| Deductible factor keys | `Deductible` | `WindstormOrHailDeductible` \| `Deductible` | `Deductible` | `TheftDeductible` \| `Deductible` |
| AOI band for deductible | `TotAmtInsuranceToUse` | `TotAmtInsuranceToUse` | `TotAmtInsuranceToUse` | `SpecialTotAmtInsuranceToUse` / `...IncludingTheft...` |
| MultiResidentialPropSpecialCreditFactor | not applied | not applied | not applied | not applied |
| Coverage gate (premium file) | hard-coded 1 | hard-coded 1 | `CauseOfLossToUse = "Broad"` exactly | `CauseOfLossToUse = "Special"` exactly |
| Premium branches | 2 (blanket / scheduled) | 2 (blanket / scheduled) | 2 (blanket / scheduled) | 2 (blanket / scheduled) |
| Legal Liability branch | none | none | none | none |
| Premium rounding | nested `Round` × several | nested `Round` × several | nested `Round` × several | nested `Round` × several (no Building-style Product-only quirk) |

---

## Quick reference — end-to-end, Basic Group I scheduled item

```
ConvertedOption = LookupSpecialClassDescriptionConvertedOption(State|CW, ClassDescription)

BaseRate        = lookup(State|CW, ConvertedOption, ProtectionClassToUse)

Rate            = BaseRate x LossCostMultiplier

COLAdj          = Rate x VandalismExclFactor x StdPropPolGroupIFactor

AdjustedRate    = COLAdj x CoinsuranceFactor           [no LOI factor]

FinalRate       = AdjustedRate x DeductibleByLocationFactor x DeductibleFactor

Premium         = round((Limit/100) x FinalRate x PackageMod x MultiPremiumDispersion x IRPM, 0)
                  x CyberExclFactorBGI x CyberExclCOLExcptnsFactorBGI
```

## Quick reference — end-to-end, Basic Group II scheduled item

```
NumericValue    = 1.0                                     if wind/hail excluded
                | LookupSpecialClassBasicGroupIINumber(State|CW, ClassDescription)   otherwise

BaseRate        = lookup(State|CW, BasicGroupIIRatingTerr, BasicGroupIISymbol, "Bldg")
LowestBaseRate  = lookup(State|CW, BasicGroupIISymbol, "Bldg")

Rate            = BaseRate x LossCostMultiplier x NumericValue

COLAdj          = 0.0                                     if CauseOfLoss in (Fire, Fire and Vandalism)
                | Rate x StdPropPolGroupIIFactor           if no wind/hail exclusion
                | LowestBaseRate x LossCostMultiplier x WindstormOrHailExclFactor x StdPropPolGroupIIFactor

CoinsFactor     = flat lookup(State|CW,"Y") [CW 1.5]      if Coinsurance in (50,60,70,None)
                | CoinsuranceFactor (shared)

AdjustedRate    = COLAdj x CoinsFactor                     [no LOI factor]

FinalRate       = AdjustedRate x BGIIDeductibleByLocationFactor x DeductibleFactorBGII

Premium         = round((Limit/100) x FinalRate x PackageMod x MultiPremiumDispersion x IRPM, 0)
                  x CyberExclFactorBGII x CyberExclCOLExcptnsFactorBGII
```

## Quick reference — end-to-end, Broad scheduled item

```
BaseRate        = lookup BroadFormBaseRate(State|CW, "Frame", "Bldg")   [CW 0.015 — construction-blind]
                | 0.0    if COL <> Broad or PolicyType <> "Commercial Property Policy"

Rate            = BaseRate x LossCostMultiplier          (no COL adjustment step)

AdjustedRate    = Rate x CoinsuranceFactor                [no LOI factor, no roof factor]

DedFactor       = lookup Deductible250Factor("Broad")     if Deductible = 250       [CW 1.05]
                | lookup DeductibleFactor(Deductible, TotAmtInsuranceToUse, "Other Cause Of Loss")
                | 0.0                                     if Deductible blank

FinalRate       = AdjustedRate x DeductibleByLocationFactor x DedFactor

Premium         = round((Limit/100) x FinalRate x PackageMod x MultiPremiumDispersion x IRPM, 0)
                  x CyberExclFactorBroad x CyberExclCOLExcptnsFactorBroad
```

## Quick reference — end-to-end, Special scheduled item

```
TheftExclFactor = lookup(State|CW,"Y")   if COL = Special and CP 10 33-equivalent form attached   [CW 0.88]
                | 1.0

BaseRate        = lookup SpecialBuildingRate(State|CW, "Y")   [CW: unfilled — no CW row in this package]
                | 0.0                                          if COL <> Special

Rate            = BaseRate x LossCostMultiplier

COLAdj          = Rate x TheftExclFactor                       [no roof factor]

AdjustedRate    = COLAdj x CoinsuranceFactor                   [no LOI factor]

FinalRate       = AdjustedRate x SpecialDeductibleByLocationFactor x DeductibleFactorSpecial

Premium         = round((Limit/100) x FinalRate x PackageMod x MultiPremiumDispersion x IRPM, 0)
                  x CyberExclFactorSpecial x CyberExclCOLExcptnsFactorSpecial
                  (standard nested-Round convention — NOT Building's Product-only quirk)
```

All intermediate rate products carry 3 decimal places; the premium product carries 0.

---
