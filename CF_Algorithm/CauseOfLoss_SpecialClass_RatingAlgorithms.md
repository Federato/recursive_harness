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

> **Corrected 2026-10-06** (`cf-bgi-chains.html` SC review #23; `cf-bgii-chains.html` SC review #31;
> `cf-special-chains.html` SC review #29; probes "COL Broad / Special" in the Group I notes, SC-33 / SC-34
> in the Group II notes, S-1 in the Special notes). **Basic Group I and II price on every Special Class
> item, whatever its cause of loss.** Every coverage record is always appended by `InitializeRuleSet`, and
> the Group I / II gates are the constant 1. So Broad and Special are **extra premiums on top of** Group I
> and II, not replacements. OH, 2026-01-01: a Special item pays Group I $66 + Group II $544 + Special $42;
> Group I is $66 and Group II $544 under Basic, Broad and Special alike. The only cause-of-loss zero inside
> Group I / II is Group II's Fire / Fire and Vandalism test (SC-35).
>
> **Silent zeros on this item after the engine's C28-17 layer (542f0e1).** `SILENT_ZERO_INPUTS` names only
> building coverages, so none of these is refused; each prices $0 with outcome "rated":
> Group I — blank `Deductible`, blank `ClassDescription`, blanket item with no policy blanket record
> (Group I notes SC-4, SC-5, SC-11). Group II — blank `BasicGroupIISymbol`, blank `ClassDescription`, blank
> `Deductible`, a percentage wind/hail deductible below its limit floor, blanket with no blanket record, and
> a blank location territory when the location has no building (Group II notes SC-4, SC-10, SC-20, SC-25,
> SC-36, SC-7). Broad — blank `Deductible`, blank or Standard Property `PolicyType`, blanket item with a blank
> `FullSpecialClassValue` (Broad notes B-18, B-11, B-12, X-4). Special — blank `Deductible` with no usable
> theft deductible, blank or Standard Property `PolicyType`, blank `FullSpecialClassValue` on a blanket
> (Special notes S-18, S-27, S-11, S-12, S-38). The refusals on these chains are `SingleResult` misses
> (C28-05): an unfiled class description, territory or symbol, an unlisted deductible or "Not Applicable"
> (caught on Group I's lookup first), an unlisted flat wind/hail deductible, and an unlisted theft deductible.

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

**Corrected 2026-10-06** (`cf-bgi-chains.html`, SC review #27, #28; Group I notes SC-5, SC-6, SC-7). The
band can't really be blank. The location always writes "1 to 4", "5 to 8" or "9 to 10", and a missing
`ProtectClass` becomes "9 to 10" (still $66, SC-7). So only a blank `ClassDescription` reaches the 0.0:
$0, outcome "rated" (SC-5). A class description with no row in `SpecialClassDescriptionConvertedOption`
(for example Florida's spelling sent in OH) is **refused**, as ISO refuses it (SC-6).

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

A blank `Deductible` gives 0.0, so $0 with outcome "rated"; the engine does not refuse it (2026-10-06,
`cf-bgi-chains.html`; Group I notes SC-4). 250 gives 1.05 ($70), 2,500 gives $63 (SC-2, SC-3).

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
`SetCoverageOnPolicyIndicator` (line 32) is **hard-coded to `CoverageOnPolicyIndicator = 1`** — unconditional, no test at all. Contrast Building's Basic Group I gate ("not blank / not Not Applicable") and Special Class's own Broad/Special gates (exact `CauseOfLossToUse` match, below). Basic Group I and Basic Group II premium in Special Class is therefore always computed whenever a Basic-Group-I coverage record exists on the item — cause-of-loss selection is enforced upstream (only the matching coverage record is instantiated), not by a datadef test inside this file. **Corrected 2026-10-06** (`cf-bgi-chains.html` SC review #23; `cf-bgii-chains.html` SC review #31): there is no upstream selection. The item's `InitializeRuleSet` appends the Group I and Group II records whenever they are absent, with no cause-of-loss test (Group II: :199–207). So both price on Basic, Broad and Special items alike ($66 and $544 in OH; Group I notes "COL Broad / Special", Group II notes SC-33 / SC-34).

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

**Added 2026-10-06** (`cf-bgi-chains.html`, SC review #24, #25, #31, #32; Group I notes SC-11, SC-12, SC-13, MOD-1, MOD-2). A blank `IncludedInBlkt` takes Branch B, the scheduled branch ($66, SC-13). `BlktTotalFullValueAmount` is overwritten from the policy's blanket record: a blanket item with no such record prices **$0, outcome "rated"** (SC-11); a real two-item blanket prices $69 / $138 (SC-12). The multi-premium credit applies (0.9 gives $59, MOD-2). Rounding after every factor (see the C6-27 note below) matters: PackageMod 0.75 with IRPM 0.99 gives $50, where one rounding would give $49 (MOD-1).

No Legal Liability branch, no Builders Risk Reporting Form gate, no `CovType` `Choose` at all — Special Class items don't carry the Building-specific `CovType` taxonomy (Builders Risk / Improvements & Betterments / Condominium Association / Leasehold Interest / Legal Liability). This is consistent with Special Class covering discrete scheduled property, which is always either scheduled individually or folded into a blanket — there is no "leasehold interest in a building" analogue.

Both branches are nested `Product DecimalPlaces="0"` with **zero `rul:Round` wrappers** — Building's *Special-form* convention, not its Basic/Broad one. **Corrected 2026-09-18 by chunk 6 task C6-27** — this page had it backwards. Counted directly: all four Special Class premium files carry 0 `rul:Round` and 12 `DecimalPlaces="0"`; Building's Basic Group I, Basic Group II and Broad files carry **6 `rul:Round` each**. The premium therefore **rounds to 0 decimal places at six nested levels**, and PackageMod, the multi-premium credit, IRPM and both cyber factors each multiply an already-rounded dollar figure. All five are read from the **policy** record, five levels up, through `FromConstant="0.0"`. Applied around six factors instead of Building's five (Special Class has no separate `PackageModFactor`-before-`MultiPremium` ordering distinction worth noting — order here is Limit → Rate → PackageMod → MultiPremium → IRPM, then the two cyber factors outside the round).

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

**Corrected 2026-10-06** (`cf-bgii-chains.html`, SC review #27, #32; Group II notes SC-4, SC-5, SC-7, SC-8, SC-9). The territory is **copied from the location** (`SetBasicGroupIIRatingTerr` :1901); a territory sent on the item is ignored (SC-8, still $544). A blank symbol, or a blank location territory on a location with no building, gives **$0, outcome "rated"** (SC-4, SC-7). A territory or symbol with no filed row is **refused** (SC-5, SC-9). The CW table is header-only, but every state files rows (OH 8); that is the normal pattern, not a gap. The symbol is a submitted input, as the open question above suspected (C6-18, ISO-confirmed).

### Step 3 — Lowest base rate
`SetLowestBasicGroupIIBaseRate` (line 3265) — same shape as Building, reading the shared `LowestBasicGroupIIRate` matrix keyed on State|CW / Symbol / `"Bldg"` (no territory). **Added 2026-10-06** (`cf-bgii-chains.html`, SC review #30): it runs on every item but feeds only the wind/hail-excluded branch. It is 0.0 when the symbol is blank.

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

**Corrected 2026-10-06** (`cf-bgii-chains.html`, SC review #28, #33; Group II notes SC-12, SC-13, SC-35). The excluded branch also **drops the class multiplier** (the numeric value is 1.0 when excluded): $544 falls to $22 (SC-12). It also sets the multiplier the SCBI child borrows to 1.0, so the child falls from $321 to $40. `WindstormOrHailExclFactor` is 0.0 when the symbol is blank, so $0 (SC-13). The Fire / Fire and Vandalism zero is intended: those are Standard Property Policy causes of loss with no windstorm (SC-35, $0).

### Step 6 — Coinsurance
`SetBasicGroupIICoinsuranceFactor` (line 3385) — same shape as Building: flat lookup (`LookupBasicGroupIIFlatCoinsuranceFactor`, State|CW + constant `"Y"`) when `Coinsurance` in (50%, 60%, 70%, None), else copy the shared `CoinsuranceFactor`. CW flat value is **1.5** (`BasicGroupIIFlatCoinsuranceFactor.RateTable.csv`, `CW,Y,1.5`) — notably **greater than 1**, a surcharge rather than a credit; worth flagging since Building's equivalent table was not confirmed at that value in the prior pass (open item — no direct comparison was made against Building's copy of the same table in this pass). **Corrected 2026-10-06** (`cf-bgii-chains.html`, SC review #24, #34; Group II notes SC-14 to SC-17; Group I notes SC-8). Confirmed 1.5 ($858 at 70% and at None); otherwise the item's shared factor (100% $515, blank 1.0 $572). But this is **not the only place coinsurance raises the rate**: Basic Group I applies `LessThan80PctMultiplicativeFactor` 1.5 to the same four values (70% gives $103 against $66). Building's Group II uses the same flat 1.5 too (`cf-bgii-chains.html` Building probes B7c70, B7c50).

### Step 7 — Adjusted rate
`SetAdjustedBasicGroupIIRate` (line 3441) — `COLAdj x CoinsuranceFactor`, same two-factor shape as Basic Group I (no LOI factor, consistent with the chain-wide absence noted above).

### Step 8 — Deductible by location
`SetBGIIDeductibleByLocationFactor` (line 3460) — same conditions as Building (`WindstormHailIndicator = 0` and a location record with a real `WindstormOrHailDeductible`), but reads `CommercialPropertyDeductiblesByLocationSpecialClassTable`, Special Class's own by-location deductible datadef, not Building's. **Corrected 2026-10-06** (`cf-bgii-chains.html`, SC review #25; Group II notes SC-32): the **record** is the item's own, but the **factor** is the shared one-row `DeductibleByLocationFactor` (CW 0.995). There is no Special Class by-location table. Otherwise 1.0. A by-location wind/hail deductible of 5,000 gives $541 against $544.

### Step 9 — Deductible factor
`SetDeductibleFactorBasicGroupII` (line 3515) — same two-level structure as Building (outer test on whether a distinct wind/hail deductible applies, inner `Choose` on `Deductible`/`WindstormOrHailDeductible`). **Added 2026-10-06** (`cf-bgii-chains.html`, SC review #29; Group II notes SC-18 to SC-31). The two layers in OH: a blank or same wind/hail deductible uses the ordinary one (250 → 1.05 $583; 2,500 $505; **blank → 0.0, $0 "rated"**, SC-20). A distinct one uses the 1/2/5% table ($533 / $505 / $438) or the flat list (5,000 $438; OH's added 100,000 $183). A percentage below its limit floor (1% needs 100k, 2% 50k, 5% 20k) gives **0.0, $0 "rated"** (SC-25). An unlisted flat amount is refused (SC-31). A "Not Applicable" ordinary deductible is refused on Group I's lookup, which runs first (SC-21).

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

**Added 2026-10-06** (`cf-bgii-chains.html`, SC review #35; Group II notes MOD-1, MOD-2, SC-36, SC-37, SC-38). Rounded to $1 after every factor (PackageMod 0.75 with IRPM 0.99 gives $453 at 2026-07-01, where one rounding gives $454). The multi-premium credit applies (0.9 gives $490). A blank `IncludedInBlkt` goes scheduled ($544). A blanket item with no policy blanket record prices **$0, "rated"**; a real two-item blanket averages 0.572 and prices $572.

**State note, NY / PR (added 2026-10-06**, `cf-bgii-chains.html` SC review #26, which corrects the old chain page). PR's chain never reads `BasicGroupIISymbol`. **NY does read it**: its base rate tests the symbol (including a "Not Applicable" value), drops the numeric value, and adds a pier/ocean/lake loss cost to the base. FL, TX, DC, AR, AL, GA, KS, RI, NC and VT rewrite other parts of the chain, and nearly every state extends the flat wind/hail deductible list.

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

**Corrected 2026-10-06** (`cf-broad-chains.html`, SC review #16, #17, #18; Broad notes B-2 to B-6, B-11, B-12). The open question is closed: ISO prices the pin too (chunk 6 C6-08, Fire Resistive re-sent, $14). Frame, Fire Resistive, Joisted Masonry, blank and "Brick" all give $14 (B-2 to B-5). The third key is the literal `"Bldg"` as well, so the item's `CovType` is ignored too (B-6). State rows win (PR 0.011). This is **not the only construction-blind chain**: Special Class Business Income's Broad has its own `"Frame"` literal. The base gate's `PolicyType` is the **policy's**, copied with no blank guard (`SetPolicyType` :1027). A blank or Standard Property `PolicyType` leaves the coverage on and prices **$0, outcome "rated"** (B-11, B-12). KS and NY drop the `PolicyType` test.

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

**Added 2026-10-06** (`cf-broad-chains.html`, SC review #20, #21, #23; Broad notes B-14 to B-22, B-25 to B-29). Coinsurance is the item's shared factor: 80% $15, 90% $14, 100% $14, 50–70% / None 1.5 $22, blank 1.0 $15. OH files its own deductible rows: 250 → 1.05 $15, 2,500 $12, 5,000 $11. A blank `Deductible` gives **$0 with the coverage on, outcome "rated"**; the engine does not refuse it (B-18). An unlisted deductible or "Not Applicable" is refused on Group I's lookup, which runs first (B-19, B-20). No wind/hail deductible or exclusion reaches Broad ($14, B-21, B-22).

### Step 5 — Final rate
`SetFinalBroadRate` (line 3894)

```
FinalBroadRate = AdjustedBroadRate x DeductibleByLocationFactor x DeductibleFactorBroad
```

**Added 2026-10-06** (`cf-broad-chains.html`, SC review #22; Broad notes B-23, B-24, X-2, X-3). `DeductibleByLocationFactor` is 0.995 only when the item's by-location record has a non-blank, non-"N/A" ordinary `Deductible` (:2464); a wind/hail deductible alone leaves 1.0. It is invisible at 0.014 but shows at a higher rate ($461 → $459, X-2).

---

## Broad — premium

`CommercialPropertySpecialClassBroadCoverageRules.Rule.xml`

### Gate — exact cause-of-loss match
`SetCoverageOnPolicyIndicator` tests `CauseOfLossToUse = "Broad"` exactly (confirmed by direct read) — same exact-match pattern Building uses for its Broad gate, and different from Special Class's own Basic Group I/II gates (hard-coded 1).

### Two-branch structure (blanket / scheduled)
Same shape as Basic Group I/II above — `IncludedInBlkt = "Yes"` branches to a blanket formula using `BlktBroadAvgRate` and `FullSpecialClassValue / BlktTotalFullValueAmount`; otherwise a scheduled formula using `FinalBroadRate` and `Limit`. No Legal Liability branch. Same nested-`Product DecimalPlaces="0"` convention as Basic Group I/II (**no `rul:Round` anywhere** — corrected 2026-09-18, C6-27), and the `CyberIncidentExclusionFactorBroad` / `CyberIncidentExclusionCOLExcptnsFactorBroad` pair.

```
Premium =
  round((Limit/100) x FinalBroadRate x PackageModFactor x MultiPremiumAndDispersionCreditFactor x IRPMFactor, 0)
  x CyberIncidentExclusionFactorBroad x CyberIncidentExclusionCOLExcptnsFactorBroad
```

**Added 2026-10-06** (`cf-broad-chains.html`, SC review #19, #24; Broad notes B-7 to B-10, B-30 to B-35, X-4). The gate is case-sensitive ("broad" gives indicator 0, B-10) and is the record's on/off switch; the record is always appended. The blanket branch needs `BlktTotalFullValueAmount > 0`. Its rate is the Detail's average of each item's **raw `BroadRate`**, before the item's coinsurance, times the Detail's own coinsurance (two items average 0.014, $14, B-31). A blank `FullSpecialClassValue` on a blanket prices **$0 with the coverage on, "rated"** (X-4). A blanket election with no policy blanket record turns the coverage off (B-30). A blank `IncludedInBlkt` goes scheduled ($14, B-32). The multi-premium credit applies (0.9 gives $13, B-35); PackageMod 0.75 with IRPM 0.99 gives $11 (B-34).

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

CW value **0.88** (`SpecialBldgTheftExclusionFactor.RateTable.csv`, `CW,Y,0.88`) — identical to Building's theft-exclusion credit, and read from a table of the **same name** (`SpecialBldgTheftExclusionFactor`) — this table is shared between Building's Special form and Special Class's Special form. **Corrected 2026-10-06** (`cf-special-chains.html`, SC review #22; Special notes S-2): 0.88 is only the CW row. **29 of 47 states file their own** (0.91 or 0.94). OH's is 0.91: the theft exclusion gives $38 against $42.

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

**Corrected 2026-10-06** (`cf-special-chains.html`, SC review #23, #24; Special notes S-1, S-3 to S-6, S-11, S-12). Not an open gap. **45 of 47 states file one flat row** (OH 0.045, then 0.046 from 2026-07-01). FL overrides the lookup and PR the base-rate rule, so the empty CW table is never reached in a filed state. Construction, `CovType` and an apartment indicator change nothing ($42, S-3 to S-6). The gate's `PolicyType` is the **policy's**: a blank or Standard Property `PolicyType` leaves the coverage on and prices **$0, outcome "rated"** (S-11, S-12). KS drops the `PolicyType` test.

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
`SetSpecialDeductibleByLocationFactor` (line 4094) — same shape as Building (triggered by a by-location theft deductible), reading `CommercialPropertyDeductiblesByLocationSpecialClassTable`. **Corrected 2026-10-06** (`cf-special-chains.html`, SC review #27; Special notes S-30, S-31, S-39): this factor is computed but **not used on the scheduled path**. `SetFinalSpecialRate` multiplies the **shared** `DeductibleByLocationFactor`, keyed on the by-location record's ordinary `Deductible` (with base 0.5: by-location `Deductible` 5,000 gives $459, by-location `TheftDeductible` 5,000 leaves $461). The Special factor is read only by the blanket average.

### Step 8 — Deductible factor
`SetDeductibleFactorSpecial` (line 4145) — same four-branch shape as Building (separate theft deductible / flat $250 / standard / otherwise→0.0), using `SpecialIncludingTheftTotAmtInsuranceToUse` and `SpecialTotAmtInsuranceToUse` (Special-Class-scoped sums, analogous to Building's `SpecialIncludingTheftTotAmtInsurance` / `SpecialTotAmtInsurance`). **Added 2026-10-06** (`cf-special-chains.html`, SC review #26; Special notes S-14 to S-28). Branch 1 uses the **theft deductible** and the including-theft band, when theft is covered (5,000 → 0.77, $33, S-21). The 250 branch fires on either deductible and **ignores the theft exclusion** (still 1.1, $43, S-24). A blank `Deductible` with no usable theft deductible falls to 0.0: **$0 with the coverage on, outcome "rated"** (S-18, S-27); with a theft deductible of 5,000 it prices $33 while Group I and II go to $0 (S-26). An unlisted deductible or "Not Applicable" refuses on Group I's lookup (S-19, S-20); an unlisted **theft** deductible refuses on Special's own lookup (S-28).

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

### Two-branch structure — and it IS Building's nested-`Product`-no-`Round` pattern
Building's Special premium file is the one form whose rounding differs from the Basic/Broad pattern (nested `Product DecimalPlaces="0"` with no `Round` wrappers). **Special Class carries that same pattern on ALL FOUR forms.** **Corrected 2026-09-18 by chunk 6 task C6-27** — this page had it backwards. Every Special Class premium file is `Product ToDataDef="Premium" DecimalPlaces="0"` nests with **zero `rul:Round` wrappers**. The earlier text read the `Product DecimalPlaces="0"` nests as "nested Round" and drew the opposite conclusion. **What is actually Building-specific is the Basic/Broad use of `rul:Round`**, which Special Class does not share anywhere.

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

**Added 2026-10-06** (`cf-special-chains.html`, SC review #21, #25, #28; Special notes S-10, S-37, S-38, S-40 to S-43). Confirmed: no `Round` element; $1 rounding at each of six steps (PackageMod 0.75 with IRPM 0.99 gives $32, S-42); the multi-premium credit applies (0.9 gives $38, S-43). The gate is case-sensitive ("special" is off, S-10); a blanket item takes the blanket's cause of loss, and with no policy blanket record the coverage is off (S-40). A blank `IncludedInBlkt` goes scheduled ($42, S-41). A real blanket averages 0.042 ($42, S-37); a blank `FullSpecialClassValue` on it prices **$0 with the coverage on, "rated"** (S-38).

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
| Premium rounding | Basic/Broad use `rul:Round` (6 each); **Special uses nested `Product` only** | **nested `Product DecimalPlaces="0"` on ALL FOUR forms, zero `rul:Round`** — Building's Special-form convention everywhere (corrected 2026-09-18, C6-27) |
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
| Premium rounding | nested `Product DecimalPlaces="0"` × 6 | same | same | same — **no `rul:Round` on any form** (corrected 2026-09-18, C6-27) |

**Corrected 2026-10-06** (`cf-bgii-chains.html` SC #25, #32; `cf-special-chains.html` SC #24, #27; `cf-bgi-chains.html`
SC #23). Read the two tables above with these changes. Group II's "own `BGIIDeductibleByLocationFactor`" uses the
item's own by-location record but the shared one-row `DeductibleByLocationFactor` (0.995). Special's final rate uses
the **shared** `DeductibleByLocationFactor`; `SpecialDeductibleByLocationFactor` feeds only the blanket average.
Special's "flat statewide constant" is filed by 45 of 47 states, so it is not an open question. Group II's symbol is
a submitted input (C6-18). The hard-coded-1 gates mean Group I and II price on every item, whatever its cause of loss.

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
TheftExclFactor = lookup(State|CW,"Y")   if COL = Special and CP 10 33-equivalent form attached   [CW 0.88; 29 states file their own, OH 0.91]
                | 1.0

BaseRate        = lookup SpecialBuildingRate(State|CW, "Y")   [CW: unfilled — no CW row in this package]
                | 0.0                                          if COL <> Special
                [corrected 2026-10-06: 45 of 47 states file the row; also 0.0 if the policy's
                 PolicyType is not "Commercial Property Policy", blank included — $0 "rated"]

Rate            = BaseRate x LossCostMultiplier

COLAdj          = Rate x TheftExclFactor                       [no roof factor]

AdjustedRate    = COLAdj x CoinsuranceFactor                   [no LOI factor]

FinalRate       = AdjustedRate x SpecialDeductibleByLocationFactor x DeductibleFactorSpecial
                  [corrected 2026-10-06, cf-special-chains.html SC #27: the factor used is the
                   shared DeductibleByLocationFactor, as in Step 9 above; the Special one feeds
                   only the blanket average]

Premium         = round((Limit/100) x FinalRate x PackageMod x MultiPremiumDispersion x IRPM, 0)
                  x CyberExclFactorSpecial x CyberExclCOLExcptnsFactorSpecial
                  (nested Product DecimalPlaces="0" x6 — the SAME convention as
                   Building's Special form; corrected 2026-09-18, C6-27)
```

All intermediate rate products carry 3 decimal places; the premium product carries 0.

---
