# Cause of Loss — Business Income Rating Algorithms

**Source ERC package:** `C:\Projects\ISO_ERC_Files\CF\20260601\CFCW20260601V01`
**Line:** Commercial Property (CF), Countrywide, edition 06-01-2026, V01
**Documented:** 2026-08-19

Business Income rating lives in the `CommercialPropertyBusinessIncome` datadef group. Structurally this
group is nested **inside** `CommercialPropertyStructure` — confirmed in the schema
(`DataDefs\MasterCFCW.DataDef.xsd`): the element `CommercialPropertyBusinessIncomeTable` (line 71715) is
declared inside `xs:complexType name="CommercialPropertyStructure"` (line 66764). Business Income is
always a child record of a Building/Structure record — it is the "time element" coverage that follows a
covered building.

Business Income rates **five** cause-of-loss chains, not four: Basic Group I, Basic Group II, Broad,
Special, **and Earthquake**. This is confirmed directly from the master orchestration rule
(`SetBlanketRatesAndFactors`, line 2201, `CommercialPropertyBusinessIncomeRules.Rule.xml`), which calls
`SetBGIRatesAndFactors`, `SetBGIIRatesAndFactors`, `SetBroadRatesAndFactors`, `SetSpecialRatesAndFactors`
**and** `SetEQRatesAndFactors` (line 2254) as a real fifth rate chain — this mirrors what the Special Class
pass found for its own Business Income variant. Earthquake premium, however, is **not** charged through a
standalone non-agreed-value coverage record (see "Earthquake" section below) — that is the one wrinkle
that keeps it from being a full sixth peer of the other four in the premium layer.

This document covers the **plain** `CommercialPropertyBusinessIncome` group (attached to a Building /
Structure). A second, structurally parallel datadef group — `CommercialPropertySpecialClassBusnIncome`,
attached to a Special Class item instead of a Building — exists in the same package with its own master
rule file (`CommercialPropertySpecialClassBusnIncomeRules.Rule.xml`) and its own full set of
`*SpclClassBusnIncome*CoverageRules.Rule.xml` files, one per cause-of-loss form, mirroring the plain
group's file layout exactly (e.g. `CommercialPropertyBusinessIncomeBasicGroupICoverageRules.Rule.xml` ↔
`CommercialPropertySpecialClassBusnIncomeBasicGroupICoverageRules.Rule.xml`). It is **not** traced in
depth here per scope — see "Special Class Business Income" at the end of this document for what was
confirmed about it.

---

## Master orchestration

All five rate chains are prepared and run in sequence from `SetBlanketRatesAndFactors` (line 2201) in
`CommercialPropertyBusinessIncomeRules.Rule.xml`:

```
... shared prep (lines 2203-2235) ...
    AttachFormCommercialPropertyExpandedLimitsOnLossPayment
    SetEQCauseOfLossForm / AttachForm...EarthquakeAndVolcanicEruption... (4 EQ-endorsement attach rules)
    SetBlanketValues, SetCauseOfLossToUse
    SetMultiPremiumAndDispersionCreditFactor, SetLossCostMultiplier
    SetBasicGroupIIRatingTerr, SetBCEGFactor, SetBCEGEQFactor
    SetPolicyType, SetBlanketRated, SetSprinklerSystem, SetConstructionCode
    SetLocNumber, SetBldgNumber, SetEQSubLimitBlktIndicator
    SetFungusWetRotDryRotBacteriaCov, SetEQDeductibleTier, SetEQClass, SetEQTerr
    SetProtectionClassToUse, SetWatercraftExclBuybackConstrctnOptionConverted
    SetFungusWetRotDryRotBacteriaIncrdPeriodRestoration, SetBuildersRiskFactor
    SetSprinklerLeakageRatesAndFactors, SetVandalismExclFactor, SetWindstormOrHailExclFactor
    SetStoryModFactor, SetEQSprinklerLeakageOnlyBldgFactor

SetBGIRatesAndFactors        (line 3500)
SetBGIIRatesAndFactors       (line 3694)
SetBroadRatesAndFactors      (line 3956)
SetSpecialRatesAndFactors    (line 4089)

    SetCoinsuranceToUse (line 2240)
    SetTuitionAndFeesFactor, SetChangesEducationalInstitutionsExtensionOfRecoveryFactor
    SetTypeRiskCombination1Factor, SetTypeRiskCombination2Factor, SetTypeOfRiskFactor
    SetMaxPeriodOfIndemnityCombination1/2Factor, SetMaxPeriodOfIndemnityFactor
    SetMonthlyLimitOfIndemnityCombination1/2Factor, SetMonthlyLimitOfIndemnityFactor
    SetExtraExpenseFactor
    SetFactor                    (line 6865)  <- picks ONE of the above as the shared "Factor"

SetEQRatesAndFactors         (line 6951)

SetFinalRates                 (line 8017)
SetInitializeFloodRatingBusinessIncome
```

Every chain computes a rate regardless of which cause of loss is actually selected on the record — same
pattern as Building. Unlike Building, there is no `SetCoverageOnPolicyIndicator` gate keyed to
`CauseOfLossToUse` at this master-rule level; the gating for "does this cause-of-loss form actually charge
premium" happens per-coverage in the individual `*CoverageRules.Rule.xml` files (see below), and for Basic
Group I / Basic Group II it doesn't happen at all — those two coverage records are **always** on the
policy (`CoverageOnPolicyIndicator` is a hardcoded `1`, not a test).

`SetFinalRates` (line 8017) is the terminal step for all five chains in one place:

```
SetFinalBasicGroupIRate    (line 8026)  -> FinalBasicGroupIRate  = BasicGroupICauseOfLossAdjustment x Factor
SetFinalBasicGroupIIRate   (line 8045)  -> FinalBasicGroupIIRate = BasicGroupIICauseOfLossAdjustment x Factor
SetFinalBroadRate          (line 8064)  -> FinalBroadRate        = BroadRate                (straight copy)
SetFinalSpecialRate        (line 8080)  -> FinalSpecialRate      = SpecialCauseOfLossAdjustment (straight copy)
SetFinalEQRate             (line 8096)  -> FinalEQRate           = EQCauseOfLossAdjustment x EQFactor
```

**This is the single most important structural fact about Business Income rating**: the shared
coinsurance/type-of-risk/period-of-indemnity multiplier called `Factor` (built by `SetFactor`, line 6865)
is applied **only** to Basic Group I and Basic Group II. Broad and Special are finalized as straight
copies of their own cause-of-loss-adjusted rates, with no `Factor` multiplication anywhere in either their
rate build-up or their premium files — confirmed by grepping
`CommercialPropertyBusinessIncomeBroadCoverageRules.Rule.xml` and
`CommercialPropertyBusinessIncomeSpecialCoverageRules.Rule.xml` for `CoinsuranceToUse` /
`TypeOfRiskFactor` / `BusnIncomeFactor`: no matches in either file. Broad's and Special's own base-rate
tables (`BroadFormBaseRate`, `SpecialFormIncldgTheftTimeElementBaseRate`) carry no coinsurance-percentage
key at all — coinsurance is not a separate rating dimension for those two forms in this package.

---

## File map

| Piece | File | Anchor |
|---|---|---|
| Master orchestration | `Rules\CommercialPropertyBusinessIncomeRules.Rule.xml` | `SetBlanketRatesAndFactors` — line 2201 |
| Rate build-up, Basic Group I | same file | `SetBGIRatesAndFactors` — line 3500 |
| Rate build-up, Basic Group II | same file | `SetBGIIRatesAndFactors` — line 3694 |
| Rate build-up, Broad | same file | `SetBroadRatesAndFactors` — line 3956 |
| Rate build-up, Special | same file | `SetSpecialRatesAndFactors` — line 4089 |
| Rate build-up, Earthquake | same file | `SetEQRatesAndFactors` — line 6951 |
| Shared "Factor" (coinsurance/type-of-risk) | same file | `SetFactor` — line 6865 |
| Final-rate consolidation | same file | `SetFinalRates` — line 8017 |
| Total-premium roll-up | same file | `ErcRate` — line 8122 (`SetTotalBusinessIncomeCoveragePremium`, `SetTotalAgreedValuePremium`, `SetTotalExtendedPeriodOfIndemnityCoveragePremium`, TRIA/terrorism) |
| Premium calc, Basic Group I | `Rules\CommercialPropertyBusinessIncomeBasicGroupICoverageRules.Rule.xml` | `SetPremium` — line 43 |
| Premium calc, Basic Group II | `Rules\CommercialPropertyBusinessIncomeBasicGroupIICoverageRules.Rule.xml` | `SetPremium` — line 43 |
| Premium calc, Broad | `Rules\CommercialPropertyBusinessIncomeBroadCoverageRules.Rule.xml` | `SetPremium` — line 60 |
| Premium calc, Special | `Rules\CommercialPropertyBusinessIncomeSpecialCoverageRules.Rule.xml` | `SetPremium` — line 60 |
| Premium calc, Earthquake (Agreed Value only) | `Rules\CommercialPropertyBusinessIncomeAgreedValEarthquakeCoverageRules.Rule.xml` | `SetPremium` — line 101 |
| Extended Period of Indemnity add-on (x5 forms) | `Rules\CommercialPropertyBusinessIncomeExtendedPeriodOfIndemnityCoverage*CoverageRules.Rule.xml` | `SetPremium` — line 87 (BGI file, pattern shared) |
| Special Class Business Income variant (not traced in depth) | `Rules\CommercialPropertySpecialClassBusnIncomeRules.Rule.xml` + `*SpclClassBusnIncome*CoverageRules.Rule.xml` | master rule; mirrors plain BI file layout |

---

## Basic Group I — rate build-up

Executed by `SetBGIRatesAndFactors` (line 3500), a 3-step chain — the shortest of the "keyed to the
building" forms:

```
SetBGIBaseRateAdjustmentFactor
SetBasicGroupIRate
SetBasicGroupICauseOfLossAdjustment
```

### Step 1 — Base-rate adjustment factor
`SetBGIBaseRateAdjustmentFactor` (line 3507): looked up once via `LookupBaseRateAdjustmentFactor` (line
13433) with `baseRateAdjustmentFactorCauseOfLoss = "Basic Group I"`, keyed on State|CW +
cause-of-loss-string against matrix `BaseRateAdjustmentFactor`. Guarded by `IsNull`.

### Step 2 — Rate
`SetBasicGroupIRate` (line 3527). **This is the key cross-coverage dependency in the whole package**: the
rate is not built from a Business-Income-specific class/construction lookup. It reads
`../../BasicGroupIBaseRate` — two levels up from the Business Income record, which (per the schema
nesting confirmed above) resolves to the **coinsured Building/Structure's own** `BasicGroupIBaseRate`
datadef, the same value Building's own `SetBasicGroupIBaseRate` rule computes for the Building coverage.

Three branches:

**Blanket / max-period / extra-expense-only branch** (gated on `MaxPeriod = Yes` OR `MonthlyLimitOfIndemnity
<> Not Applicable` OR `CovType = Extra Expense Only`, AND `BldgIncludedInOperationalUnit = Yes`):

```
BasicGroupIRate = HighestBusnIncomeBasicGroupIBaseRate x BGIBaseRateAdjustmentFactor
```

(`HighestBusnIncomeBasicGroupIBaseRate` is read four levels up — a multi-unit/blanket-level aggregate, not
traced further here.)

**Class rated** (`RatingType = "Class"`, the `../../RatingType` on the Structure):

```
BasicGroupIRate =
    ( (../../BasicGroupIBaseRate x LossCostMultiplier) + SubStdConditionRate + VacantBuildingRate )
  x BasicGroupIRatingTerrFactor
  x ProtectionClassFactor
  x BGIBaseRateAdjustmentFactor
```

This is **structurally identical to Building's own Class-rated Basic Group I rate formula** — same
addends, same territory and protection-class factors, sourced from the same Structure-level datadefs —
with one extra multiplier (`BGIBaseRateAdjustmentFactor`) tacked on at the end. Business Income does not
recompute a base rate; it reuses the Building's.

**Specific or Tentative rated**:

```
BasicGroupIRate = SpecificGroupIRate x LossCostMultiplier x SprinklerLeakageNotExcludedFactor
                 x BGIBaseRateAdjustmentFactor
```

All three branches round to 3 decimals and are guarded by `IsNull` on `BasicGroupIRate`.

### Step 3 — Cause-of-loss adjustment
`SetBasicGroupICauseOfLossAdjustment` (line 3675), 3 decimals, unconditional (no `IsNull` guard):

```
BasicGroupICauseOfLossAdjustment =
    round(BasicGroupIRate - SprinklerLeakageExclNonSprinkleredRate, 3)
  x SprinklerLeakageExclSprinkleredFactor
  x VandalismExclFactor
  x BuildersRiskFactor
```

Same shape as Building's Basic Group I COL adjustment (subtract-then-round, then two exclusion factors),
with `StdPropPolGroupIFactor` replaced by `BuildersRiskFactor` — Business Income has no "standard property
policy" concept but does have a Builders Risk rate modifier.

### Final rate
Per `SetFinalRates` (line 8026): `FinalBasicGroupIRate = BasicGroupICauseOfLossAdjustment x Factor`, where
`Factor` is the shared coinsurance/type-of-risk/period-of-indemnity multiplier (see "The shared Factor"
section below). **There is no separate coinsurance factor, LOI factor, or deductible factor step anywhere
in the Basic Group I Business Income chain** — those three Building-style steps collapse into the single
`Factor` multiplication (for coinsurance/type-of-risk) plus nothing at all for LOI or deductible. Business
Income has no per-dollar-deductible rating table in this package outside of the Earthquake sub-forms (see
"Structural differences" below).

---

## Basic Group I — premium

`CommercialPropertyBusinessIncomeBasicGroupICoverageRules.Rule.xml`

### Gate — coverage on policy
`SetCoverageOnPolicyIndicator` (line 32) is a **hardcoded constant `1`** — no test at all. Basic Group I
Business Income premium is always computed if the coverage record exists; there is no cause-of-loss gate
the way Building has one.

### Branch A — scheduled (not blanketed)
Applies when `../IncludedInBlkt = "No"`:

```
Premium =
  round(
    round(
      IRPMFactor x PackageModFactor x FinalBasicGroupIRate x (Limit / 100)
    , 0)
  , 0)
  x CyberIncidentExclusionFactorBGI
  x CyberIncidentExclusionCOLExcptnsFactorBusnIncomeBGIToUse
```

`IRPMFactor`, `PackageModFactor`, and both cyber factors are read **seven** levels up the tree (policy
level) — deeper than Building's five levels, reflecting Business Income's extra nesting under Structure.
**`MultiPremiumAndDispersionCreditFactor` does not appear in this formula at all** — Building's scheduled
Basic Group I premium includes it; Business Income's does not, even though
`SetMultiPremiumAndDispersionCreditFactor` runs during shared prep (line 2211) and populates the
datadef — it's simply never multiplied into the coverage-level premium.

### Branch B — blanket
Applies when `../IncludedInBlkt <> "No"` (i.e. `"Yes"`) and `BlktTotalFullValueAmount > 0`, else `Premium =
0.0`:

```
Premium =
  round(
    round(
      IRPMFactor x PackageModFactor x BlktBasicGroupIAvgRate
        x (FullBusnIncomeValue / BlktTotalFullValueAmount)
        x (BlktLimit / 100)
    , 0)
  , 0)
  x CyberIncidentExclusionFactorBGI
  x CyberIncidentExclusionCOLExcptnsFactorBusnIncomeBGIToUse
```

Same shape as Building's blanket branch, substituting `FullBusnIncomeValue` for `FullBldgValue`. **There is
no Branch C (Legal Liability) and no Branch D (otherwise-zero) — only these two branches exist.** Business
Income has no Legal Liability coverage type; the CovType-driven branching Building needs (Builders Risk /
Building / Improvements and Betterments / Condominium Association / Legal Liability / Leasehold Interest)
does not apply here because CovType only ever affects the *rate build-up* (Extra Expense Only branch,
Broad-form covType key) — never the premium branch selection.

### Premium indicator
`SetPremiumIndicator` (line 128): `PremiumIndicator = 1` when `Premium <> 0.0`. `CalculateTotalPremium`
(line 10) mirrors Building's pattern exactly.

---

## Basic Group II — differences from Basic Group I

`SetBGIIRatesAndFactors` (line 3694), a 5-step chain:

```
SetBasicGroupIIBaseRate
SetLowestBasicGroupIIBaseRate
SetBGIIBaseRateAdjustmentFactor
SetBasicGroupIIRate
SetBasicGroupIICauseOfLossAdjustment
```

### Step 1 — Base rate
`SetBasicGroupIIBaseRate` (line 3703), a three-way `Choose`:

1. Blanket/max-period branch (same gate as BGI step 2): copy `../../../../HighestBusnIncomeBasicGroupIIBaseRate`.
2. `BasicGroupIIRatingTerr` and `../../BasicGroupIISymbolToUse` both non-blank: `LookupBasicGroupIIRate`
   (line 13482) against matrix **`BasicGroupIIRate`** — keyed State|CW, `BasicGroupIIRatingTerr`,
   `../../BasicGroupIISymbolToUse`, `"Bldg"`. **This is the exact same matrix Building's own
   `LookupBasicGroupIIRate` reads**, with the same key shape, and the territory/symbol values are read
   from the Structure (`BasicGroupIIRatingTerr` is copied down at line 2213 via
   `SetBasicGroupIIRatingTerr`; `BasicGroupIISymbolToUse` is a direct cross-reference two levels up).
3. Otherwise: `0.0`.

### Step 2 — Lowest base rate
`SetLowestBasicGroupIIBaseRate` (line 3793): same three-way shape, using
`LookupLowestBasicGroupIIRate` against matrix `LowestBasicGroupIIRate` (State|CW, Symbol, "Bldg" — no
territory key, same statewide-floor concept as Building's version). Feeds the wind/hail-excluded branch of
step 5 below.

### Step 3 — Base-rate adjustment factor
`SetBGIIBaseRateAdjustmentFactor` (line 3877): identical mechanism to BGI's, with
`baseRateAdjustmentFactorCauseOfLoss = "Basic Group II"`.

### Step 4 — Rate
`SetBasicGroupIIRate` (line 3897), 3 decimals:

```
BasicGroupIIRate = BasicGroupIIBaseRate x LossCostMultiplier x ../../BasicGroupIINumericValue
                   x BCEGFactor x BGIIBaseRateAdjustmentFactor
```

`BasicGroupIINumericValue` is read from the Structure (two levels up) — Business Income does not
recompute the occupancy/open-sides hazard load; it reuses Building's.

### Step 5 — Cause-of-loss adjustment
`SetBasicGroupIICauseOfLossAdjustment` (line 3925):

```
if no CommercialPropertyWindstormOrHailExclusionBusnIncome record:
    BasicGroupIICauseOfLossAdjustment = BasicGroupIIRate x BuildersRiskFactor
else:
    BasicGroupIICauseOfLossAdjustment =
        LowestBasicGroupIIBaseRate x LossCostMultiplier x WindstormOrHailExclFactor x BuildersRiskFactor
```

Same two-path shape as Building's Group II COL adjustment (wind/hail-excluded rebuilds from the lowest
base rate), with `StdPropPolGroupIIFactor` replaced by `BuildersRiskFactor` — consistent with the Basic
Group I substitution.

### Final rate
`FinalBasicGroupIIRate = BasicGroupIICauseOfLossAdjustment x Factor` (same shared `Factor` as Group I).

---

## Basic Group II — premium

`CommercialPropertyBusinessIncomeBasicGroupIICoverageRules.Rule.xml` is **byte-shape-identical** to the
Basic Group I premium file (confirmed lines 32-54: hardcoded `CoverageOnPolicyIndicator = 1`, same two
branches), with only the datadef names swapped (`FinalBasicGroupIIRate`, `BlktBasicGroupIIAvgRate`,
`CyberIncidentExclusionFactorBGII`, `CyberIncidentExclusionCOLExcptnsFactorBusnIncomeBGIIToUse`) — same
relationship Building's Group I/II premium files have to each other.

---

## Broad — rate build-up

`SetBroadRatesAndFactors` (line 3956), a 2-step chain — the shortest of all five Business Income forms:

```
SetBroadBaseRate
SetBroadRate
```

### Step 1 — Base rate
`SetBroadBaseRate` (line 3962), gated on `CauseOfLossToUse = "Broad"`:

```
if CovType = "Business Income Without Extra Expense":
    BroadBaseRate = LookupBroadFormBaseRate(covTypeBroadForm = "Business Income Without Extra Expense")
else:
    BroadBaseRate = LookupBroadFormBaseRate(covTypeBroadForm = "All Other")
else (COL <> Broad):
    BroadBaseRate = 0.0
```

`LookupBroadFormBaseRate` reads matrix **`BroadFormBaseRate`** — the **same table Building's Broad rate
uses** (confirmed: Building's doc notes this table "is shared across coverage types via its `CovType` key
— `Bldg`, `BldrRisk`, `PersProp`, and Business Income variants all live in the one table"), keyed
State|CW, `ConstructionTypeToUse` (read from the Structure), and the `covType` param. Confirmed CW rows
exist for both Business Income keys: `"Business Income Without Extra Expense"` (e.g. 0.011 for Frame /
Joisted Masonry / Non-Combustible / Masonry Non-Combustible, 0.007 for Modified Fire Resistive — two-tier
by construction, same pattern as the Building rows) and (by elimination) `"All Other"` for the
With-Extra-Expense case.

Unlike Basic Group I/II, **Broad's base rate is its own dedicated table row, not a cross-reference into
the Building's computed rate** — it shares the *table* with Building but keys into a distinct
covType-partitioned set of rows, not the Building's already-resolved `BroadBaseRate` datadef.

### Step 2 — Rate
`SetBroadRate` (line 4042), 3 decimals, same gate:

```
BroadRate = BroadBaseRate x LossCostMultiplier
```

That is the entire chain — no cause-of-loss adjustment, no LOI factor, no coinsurance-linked `Factor`, no
deductible factor. `FinalBroadRate` is a straight copy of `BroadRate` (`SetFinalBroadRate`, line 8064).

---

## Broad — premium

`CommercialPropertyBusinessIncomeBroadCoverageRules.Rule.xml`

### Gate — coverage on policy
`SetCoverageOnPolicyIndicator` (line 32): `CoverageOnPolicyIndicator = 1` only when
`../CauseOfLossToUse = "Broad"` — an exact-equality test, unlike Basic Group I/II's hardcoded 1. This
matches the *shape* of Building's Special-form gate (exact COL equality) rather than Building's Basic
Group I/II gate (blank/Not-Applicable test).

### Branch A — scheduled / Branch B — blanket
Structurally identical to Basic Group I's premium file, substituting `FinalBroadRate` /
`BlktBroadAvgRate` / `CyberIncidentExclusionFactorBroad` /
`CyberIncidentExclusionCOLExcptnsFactorBusnIncomeBroadToUse`. Same two-branch-only shape (no Legal
Liability, no Leasehold Interest carve-out) — see Basic Group I premium section above for the full
formula.

---

## Special — rate build-up

`SetSpecialRatesAndFactors` (line 4089), a 6-step chain:

```
SetSpecialTheftExclusionIndicator
SetSpecialIncludingTheftTypeRisk
SetSpecialTheftExclusionFactor
SetSpecialBaseRate
SetSpecialRate
SetSpecialCOLAdjustment
```

**This is the one form where Business Income and Building genuinely diverge in shape.** Building's Special
building rate is a *flat statewide constant* with no construction dependency at all (and its
`SpecialBuildingRate` table is header-only / unfiled at CW — see `BasicGroupI_ERC_Tables.md`). Business
Income's Special form, by contrast, **does** vary by construction type and by a theft/apartment-condo type
classification.

### Prerequisite — theft exclusion indicator
`SetSpecialTheftExclusionIndicator` (line 4099): `1` if a `CommercialPropertyTheftExclusionBusnIncome`
record exists, else `0` — the Business-Income-specific instance of form CP 10 33, tracked separately from
the Building's own theft-exclusion indicator.

### Prerequisite — including-theft type of risk
`SetSpecialIncludingTheftTypeRisk` (line 4118), gated on `CauseOfLossToUse = "Special"`:

```
"Apartments and Condominiums"              if ../../ApartmentCondoIndicator = "Yes"
"Other than Apartments and Condominiums"   if ../../ApartmentCondoIndicator = "No"
"" (blank)                                  otherwise
```

This becomes a lookup key for the base rate (step 2) — a dimension Building's Special form has no
analogue for.

### Step 1 — Theft exclusion factor
`SetSpecialTheftExclusionFactor` (line 4167), gated on `CauseOfLossToUse = "Special"` AND
`SpecialTheftExclusionIndicator = 1` AND `ApartmentCondoIndicator` non-blank:

```
SpecialTheftExclusionFactor = LookupSpecialLeaseHoldTimeElementTheftExclusionFactor(State|CW, ApartmentCondoIndicator)
else: 1.0
```

Matrix `SpecialLeaseHoldTimeElementTheftExclusionFactor` — confirmed to carry CW rows (3 total lines
including header: 2 data rows, one per `ApartmentCondoIndicator` value).

### Step 2 — Base rate
`SetSpecialBaseRate` (line 4221), a nested branch structure:

```
if CauseOfLossToUse = "Special" and ClassCodeToUse = "1150" (Builders Risk):
    SpecialBaseRate = LookupSpecialFormBldrsRiskTimeElementBaseRate(State|CW, "Y")
elif SpecialIncludingTheftTypeRisk is non-blank:
    if CovType = "Business Income Without Extra Expense":
        SpecialBaseRate = LookupSpecialFormIncldgTheftTimeElementBaseRate(
            State|CW, ConstructionTypeToUse, "Business Income Without Extra Expense", SpecialIncludingTheftTypeRisk)
    else (CovType <> "Business Income Without Extra Expense"):
        [same lookup with an "All Other" covType — continuation not fully traced, pattern consistent with Broad's covType split]
```

`LookupSpecialFormBldrsRiskTimeElementBaseRate` reads matrix `SpecialFormBldrsRiskTimeElementBaseRate` —
confirmed **CW row present: 0.018** (State|CW, constant "Y" — a flat statewide Builders Risk time-element
rate, same single-value-table shape as Building's `SpecialBuildersRiskRate`).

`LookupSpecialFormIncldgTheftTimeElementBaseRate` (line 13918) reads matrix
`SpecialFormIncldgTheftTimeElementBaseRate`, keyed State|CW, `../../ConstructionTypeToUse` (from the
Structure), the `covType` param, `SpecialIncludingTheftTypeRisk`. Confirmed CW rows exist, e.g. `("CW",
"Frame", "Business Income Without Extra Expense", "Apartments and Condominiums", 0.016)` — 24 data rows
total in the table (25 lines including header).

### Step 3 — Rate
`SetSpecialRate` — not shown in excerpt but follows the same `BaseRate x LossCostMultiplier` pattern used
by every other form in this ruleset (confirmed by the presence of `SpecialRate` as an input to
`SetSpecialCOLAdjustment` immediately after, with no intervening territory/protection-class step).

### Step 4 — Cause-of-loss adjustment
`SetSpecialCOLAdjustment` (line 4408), 3 decimals, unconditional:

```
SpecialCauseOfLossAdjustment = SpecialRate x SpecialTheftExclusionFactor
```

Notably simpler than Building's Special COL adjustment (which also multiplies in the roof-surfacing ACV
factor) — Business Income has no roof-surfacing concept.

### Final rate
`FinalSpecialRate = SpecialCauseOfLossAdjustment` — a straight copy (`SetFinalSpecialRate`, line 8080), no
`Factor` multiplication, matching Broad.

---

## Special — premium

`CommercialPropertyBusinessIncomeSpecialCoverageRules.Rule.xml` is **structurally identical to the Broad
premium file** (confirmed line-by-line: same `CoverageOnPolicyIndicator` shape testing
`../CauseOfLossToUse = "Special"`, same two branches, same rounding). This is a genuine departure from
Building, where Special's premium file has real structural differences from the Basic-form pattern
(different rounding — nested `Product` with no `Round` wrappers, extra `CauseOfLoss = "Special"` guards
inside each branch, Legal Liability and blanket-cause-of-loss-value tests). None of that applies here:
Business Income's Special premium file uses the same nested-`Round`-then-`Product`-by-cyber-factors
pattern as every other Business Income form, substituting `FinalSpecialRate` /
`BlktSpecialAvgRate` / `CyberIncidentExclusionFactorSpecial` /
`CyberIncidentExclusionCOLExcptnsFactorBusnIncomeSpecialToUse`.

---

## Earthquake — rate build-up

`SetEQRatesAndFactors` (line 6951), an 8-step chain — the longest of the five:

```
SetEQSubLimitPercent
SetEQSubLimitCoinsurance
SetEQSubLimitTypeRiskCombination1Factor
SetEQSubLimitTypeRiskCombination2Factor
SetEQSubLimitTypeOfRiskFactor
SetEarthquakeSubLimitTimeElementFactor
SetEQFactor
SetEQRate
SetEQCauseOfLossAdjustment
```

The first six steps build **sub-limit** machinery specific to two EQ endorsement forms (CP 10 45 / CP 10
29 sub-limit forms, attached via the four `AttachFormCommercialPropertyEarthquakeAndVolcanicEruption...`
rules run during shared prep, lines 2205-2208) — a layer with no Building-side or Broad/Special-side
analogue, since sub-limited earthquake coverage is a time-element-specific concept.

### Step 7 — Rate
`SetEQRate` (line 7923), 3 decimals, same blanket/max-period gate used throughout this ruleset:

```
blanket/max-period branch:
    EQRate = ../../../../HighestBusnIncomeEQBaseRate x LossCostMultiplier
           x SoftStoryModificationFactor x EQSprinkleredRiskFactor x BldgHeightFactor
           x BCEGEQFactor x BuildersRiskEQFactor
else:
    EQRate = ../../EQBaseRate x LossCostMultiplier
           x SoftStoryModificationFactor x EQSprinkleredRiskFactor x BldgHeightFactor
           x BCEGEQFactor x BuildersRiskEQFactor
```

**`EQBaseRate` is read two levels up from the Structure and is never computed anywhere in
`CommercialPropertyBusinessIncomeRules.Rule.xml`** — no `SetEQBaseRate` rule and no `LookupEQBaseRate` rule
exist in this file. Like Basic Group I/II, Business Income's Earthquake rate is built entirely on top of
the coinsured **Building's own** computed earthquake base rate (and its soft-story, sprinklered-risk,
building-height, and Builders-Risk-EQ factors) — Business Income supplies only the loss cost multiplier
and the BCEG-EQ factor as its own contribution.

### Step 8 — Cause-of-loss adjustment
`SetEQCauseOfLossAdjustment` (line 8003), 3 decimals, unconditional:

```
EQCauseOfLossAdjustment = StoryModFactor x BuildersRiskFactor x EQRate x EQSprinklerLeakageOnlyBldgFactor
```

### Final rate
`FinalEQRate = EQCauseOfLossAdjustment x EQFactor` (`SetFinalEQRate`, line 8096) — `EQFactor` here is a
distinct datadef from the shared `Factor` used by Basic Group I/II (built by `SetEQFactor`, line 7745, not
traced in full here — a sub-limit-percent-driven factor separate from the type-of-risk/coinsurance
`Factor`).

---

## Earthquake — premium: the Agreed Value asymmetry

**There is no `CommercialPropertyBusinessIncomeEarthquakeCoverageRules.Rule.xml` file in this package** —
confirmed by directory listing: the only Earthquake premium coverage file for plain Business Income is
`CommercialPropertyBusinessIncomeAgreedValEarthquakeCoverageRules.Rule.xml`. `FinalEQRate` is computed
unconditionally by the master rate chain, but it is only ever converted into a standalone chargeable
premium through the **Agreed Value** coverage record. This is confirmed by
`SetTotalBusinessIncomeCoveragePremium` (line 8133), which sums only
`CommercialPropertyBusinessIncomeBasicGroupICoverage/Premium`,
`...BasicGroupIICoverage/Premium`, `...BroadCoverage/Premium`, `...SpecialCoverage/Premium` — **no
Earthquake term at all** — while `SetTotalAgreedValuePremium` (line 8143) sums the five Agreed Value
coverages (Basic Group I, II, Broad, Special, **and Earthquake**).

Practical effect: a non-agreed-value Business Income policy with an earthquake endorsement gets its EQ
rate baked into the *blanket* average rate (`ErcSetBlanketRatesAndFactors`, line 12888, calls
`SetNonEQBlanketRatesAndFactors` and `SetEQBlanketRatesAndFactors` separately — not traced further here)
when the coverage is blanketed, but has **no standalone scheduled EQ premium path** outside of Agreed
Value. This should be treated as an open question for anyone building a rater off this document — see
"Open questions" at the end.

### Agreed Value Earthquake premium mechanics
`CommercialPropertyBusinessIncomeAgreedValEarthquakeCoverageRules.Rule.xml`, `SetPremium` (line 101):

```
if BlktEQAgreedVal = "Yes" and EQCovIndicator = "Yes, Included in Blanket":
    Premium =
      round(round(
        BlktEQAvgRate x round(Factor - 1, 3) x (EQLimitToUse / 100)
      , 0), 0)
      x CyberIncidentExclusionFactorEQ x CyberIncidentExclusionCOLExcptnsFactorBusnIncomeEQToUse

elif AgreedValueOption = "Yes" and EQCovIndicator = "Yes, Not Included in Blanket":
    Premium =
      round(round(
        FinalEQRate x round(Factor - 1, 3) x (AgreedValueLimit / 100)
      , 0), 0)
      x CyberIncidentExclusionFactorEQ x CyberIncidentExclusionCOLExcptnsFactorBusnIncomeEQToUse

else:
    Premium = 0.0
```

`Factor` here comes from `LookupAgreedValueFactor` (line 232), matrix `AgreedValueFactorBusnIncome`,
State|CW + constant `"Y"` — confirmed a single CW data row exists (2 lines total including header).

**This is a genuinely different premium mechanism from every other Business Income form**: it charges
`(Factor - 1)` — i.e., only the *incremental* load for waiving the coinsurance requirement — against the
base rate, not the full rate. The same `(Factor - 1) x Rate x (Limit/100)` shape recurs in the Extended
Period of Indemnity add-on coverages (e.g.
`CommercialPropertyBusinessIncomeExtendedPeriodOfIndemnityCoverageBasicGroupICoverageRules.Rule.xml`,
`SetPremium`, line 87 — same incremental-charge pattern, `Factor` sourced from `LookupExtendedPeriodFactor`
against matrix `ExtendedPeriodFactor`, confirmed CW rows present e.g. `("CW","90",1.05)` through longer
extension periods). This "surcharge = (factor - 1) x base" pattern for optional add-on coverages appears
nowhere in the Building or Personal Property rating chains, which always multiply the *full* factor
into the base premium rather than charging only its increment.

---

## The shared "Factor" (Basic Group I / II only)

`SetFactor` (line 6865) picks exactly one of four possible values, in priority order:

```
Factor = MaxPeriodOfIndemnityFactor        if MaxPeriod = "Yes"
       | MonthlyLimitOfIndemnityFactor     elif MonthlyLimitOfIndemnity <> "Not Applicable"
       | ExtraExpenseFactor                elif CovType = "Extra Expense Only"
       | TypeOfRiskFactor                  otherwise
```

`TypeOfRiskFactor` (`SetTypeOfRiskFactor`, line 5000) is itself built from `LookupBusnIncomeFactor` (line
13635) against matrix **`BusnIncomeFactor`**, keyed on State|CW, `CovType`, `TypeOfRisk`,
`CoinsuranceToUse` — confirmed 131 CW data rows present, e.g. `("CW","Business Income With Extra
Expense","Mercantile and Non-manufacturing","50%",0.76)` down through the 100% coinsurance rows. This
table is Business Income's functional replacement for Building's flat `CoinsuranceFactor` table — it folds
coinsurance percentage together with type-of-risk classification and coverage type into one factor, rather
than treating coinsurance as an independent multiplier. When `TypeOfRisk` is a "Combined" risk (e.g.
"Combined Manufacturing and Mercantile Operations"), `TypeOfRiskFactor` is a percentage-weighted blend of
two `TypeRiskCombination1Factor` / `TypeRiskCombination2Factor` lookups (lines 5038-5070) rather than a
single table hit.

`CoinsuranceToUse` (`SetCoinsuranceToUse`, line 4416) is **not** simply `Coinsurance` copied down — when
the coverage is blanketed (`BlktIDNum <> 0`), it is resolved by scanning the policy-level
`CommercialPropertyBlanketRatingTable` for the matching `UnitNumber` and copying that unit's `Coinsurance`,
or (if the whole submission is multi-unit-blanket-rated) copying `BlktCoinsurance` directly.

---

## Five-way comparison

| | Basic Group I | Basic Group II | Broad | Special | Earthquake |
|---|---|---|---|---|---|
| Chain length | 3 rules | 5 rules | **2 rules** | 6 rules | 8 rules |
| Base rate source | **Building's own `BasicGroupIBaseRate`** (cross-ref) | **Building's own symbol/terr lookup** (shared `BasicGroupIIRate` table) | own table, own covType key (`BroadFormBaseRate`, shared table w/ Building) | own table, own covType+risk-type key | **Building's own `EQBaseRate`** (cross-ref) |
| BI-specific multiplier | `BGIBaseRateAdjustmentFactor` | `BGIIBaseRateAdjustmentFactor` | none | none | `BCEGEQFactor` (own), rest from Structure |
| COL adjustment step | yes (sprinkler/vandalism/BuildersRisk) | yes (wind/hail excl / BuildersRisk) | **none** | yes (theft only) | yes (StoryMod/BuildersRisk/SprinklerLeakageOnly) |
| Shared coinsurance `Factor` applied | **yes** | **yes** | **no** | **no** | no (own `EQFactor` instead) |
| Construction dependency | via Building's rate | via Building's symbol | own (`ConstructionTypeToUse` key) | own (`ConstructionTypeToUse` key) | via Building's rate |
| Territory dependency | via Building's terr factor | via Building's terr key | none | none | via Building's rate |
| Deductible factor | **none** | **none** | **none** | **none** | flat-dollar EQ deductible endorsements only, separate mechanism |
| Final-rate formula | COLAdj x Factor | COLAdj x Factor | straight copy of `BroadRate` | straight copy of `SpecialCauseOfLossAdjustment` | COLAdj x EQFactor |
| Standalone (non-Agreed-Value) premium coverage file | yes | yes | yes | yes | **no — Agreed Value only** |
| Coverage-on-policy gate | hardcoded `1` | hardcoded `1` | `CauseOfLossToUse = "Broad"` | `CauseOfLossToUse = "Special"` | compound EQCovIndicator/AgreedValueOption/BlktEQAgreedVal test |

---

## Structural differences from Building (and Personal Property)

Business Income is income-based, not value-based, and that shows up everywhere in the rule shapes, not
just in the exposure basis:

1. **No independent class/construction rating for two of five forms.** Basic Group I, Basic Group II, and
   Earthquake do not look up their own base rates from class/construction/territory tables the way Building
   does. They read the **already-computed** `BasicGroupIBaseRate`, `BasicGroupIISymbolToUse` /
   `BasicGroupIIRatingTerr`, and `EQBaseRate` datadefs two (or four) levels up from the coinsured
   Structure record and apply a small Business-Income-specific adjustment factor on top. Rate the Building
   first; Business Income for these three forms is arithmetically downstream of it. Only Broad and Special
   have their own dedicated Business-Income base-rate tables.

2. **Coinsurance is not an independent multiplier — it's folded into a combined factor, and only for two
   of five forms.** Building's `CoinsuranceFactor` is a flat, cause-of-loss-agnostic table applied uniformly
   across all four Building forms. Business Income's analogue, `BusnIncomeFactor`, is a three-dimensional
   table (CovType x TypeOfRisk x CoinsuranceToUse) that also absorbs the "period of indemnity" and
   "extra-expense-only" special cases — `SetFactor` picks exactly one of `MaxPeriodOfIndemnityFactor`,
   `MonthlyLimitOfIndemnityFactor`, `ExtraExpenseFactor`, or `TypeOfRiskFactor` as a single mutually-
   exclusive "Factor" — and it is applied **only** to Basic Group I and Basic Group II. Broad and Special
   never multiply by it.

3. **No deductible-factor rating at all**, outside of flat-dollar Earthquake sub-forms. Grepping the whole
   `CommercialPropertyBusinessIncomeRules.Rule.xml` master file for `Deductible` turns up only Earthquake
   sub-limit/flat-dollar-deductible endorsement plumbing — there is no `SetDeductibleFactor`,
   `SetDeductibleByLocationFactor`, or per-dollar deductible table anywhere in the base Business Income
   chain. This tracks with how Business Income is actually written: the "deductible" concept is a waiting
   period (typically 72 hours) built into the base rate itself, not a scheduled dollar amount the way
   Building's peril deductibles are rated.

4. **No Limit-of-Insurance factor.** Building applies a distinct LOI factor (`BasicGroupILOIFactorBldg`,
   `BroadSpecialLOIFactorBldg`, etc.) between the cause-of-loss adjustment and the final rate for every
   form. Business Income has no LOI factor step anywhere — the premium formula multiplies the final rate
   directly by `Limit / 100` with nothing else standing in between.

5. **No `MultiPremiumAndDispersionCreditFactor` in the coverage-level premium**, even though the datadef is
   populated during shared prep. Building's scheduled-building premium branch multiplies it in; Business
   Income's does not, for any of the five forms.

6. **Premium files are radically simpler and far more uniform across forms.** Building's four premium
   files diverge substantially — Special is a structurally different file from the Basic-form pattern
   (different rounding, extra guards, raw-rate use in Legal Liability, blanket-cause-of-loss-value tests),
   and each Basic form supports up to four branches (scheduled / Legal Liability / blanket / otherwise-
   zero). Every Business Income premium file (Basic Group I, II, Broad, Special) has exactly **two**
   branches — scheduled or blanket — with no Legal Liability and no Leasehold Interest carve-out, because
   Business Income has neither of those coverage types. Special's premium file is not a structural outlier
   here the way it is for Building; it is byte-shape-identical to Broad's.

7. **Add-on coverages charge only an incremental factor, not the full rate.** Agreed Value (waiving
   coinsurance) and Extended Period of Indemnity both compute premium as `(Factor - 1) x Rate x
   (Limit/100)` — charging only the extra load the endorsement adds over the base rate, never the full
   rate again. Nothing in the Building or Personal Property rating chains uses this "surcharge on top of
   an already-rated base" shape; their endorsement premiums (e.g. cyber exclusion factors) are always
   full multipliers applied to the whole rate.

8. **Earthquake is a real fifth rate chain but not a real fifth premium coverage** (for the plain,
   non-agreed-value form). `SetEQRatesAndFactors` runs unconditionally alongside the other four chains and
   produces `FinalEQRate`, but there is no `CommercialPropertyBusinessIncomeEarthquakeCoverageRules.Rule.xml`
   file — only the Agreed Value variant charges standalone EQ premium. This is a closer parallel to what
   the Special Class Business Income pass found (Earthquake present as a real chain, not just a footnote)
   than to Building, which has no Earthquake chain in its four-form CommercialPropertyStructure ruleset at
   all.

9. **Deeper datadef nesting.** Because `CommercialPropertyBusinessIncome` sits inside
   `CommercialPropertyStructure`, every reference to policy-level factors (`IRPMFactor`,
   `PackageModFactor`, cyber factors) climbs **seven** `../` levels in the Business Income premium files
   versus **five** in Building's — a mechanical consequence of the extra nesting, not a rating difference,
   but worth knowing when reading the raw XML.

---

## Special Class Business Income (existence only — not traced in depth)

Confirmed via directory listing (`Rules\`): a second, file-name-parallel datadef group exists —
`CommercialPropertySpecialClassBusnIncome*` — attached to a Special Class item rather than a Building. It
has its own master rule file, `CommercialPropertySpecialClassBusnIncomeRules.Rule.xml`, and its own
complete set of per-cause-of-loss coverage rule files that mirror the plain group's naming exactly, one
for one:

| Plain Business Income | Special Class Business Income |
|---|---|
| `CommercialPropertyBusinessIncomeBasicGroupICoverageRules.Rule.xml` | `CommercialPropertySpecialClassBusnIncomeBasicGroupICoverageRules.Rule.xml` |
| `CommercialPropertyBusinessIncomeBasicGroupIICoverageRules.Rule.xml` | `CommercialPropertySpecialClassBusnIncomeBasicGroupIICoverageRules.Rule.xml` |
| `CommercialPropertyBusinessIncomeBroadCoverageRules.Rule.xml` | `CommercialPropertySpecialClassBusnIncomeBroadCoverageRules.Rule.xml` |
| `CommercialPropertyBusinessIncomeSpecialCoverageRules.Rule.xml` | `CommercialPropertySpecialClassBusnIncomeSpecialCoverageRules.Rule.xml` |
| `CommercialPropertyBusinessIncomeAgreedValEarthquakeCoverageRules.Rule.xml` | `CommercialPropertySpecialClassBusnIncomeAgreedValEarthquakeCoverageRules.Rule.xml` |
| *(no plain Earthquake file for either group — Agreed Value only, both sides)* | — |
| `CommercialPropertyBusinessIncomeExtendedPeriodOfIndemnityCoverage*Rules.Rule.xml` (x5 forms) | `CommercialPropertySpecialClassBusnIncomeExtendedPeriodOfIndemnityCoverage*Rules.Rule.xml` (x4 forms — no Basic Group II variant confirmed present by name; not verified further) |

The naming convention swaps `BusinessIncome` for `SpecialClassBusnIncome` throughout, and the
"attached-to" parent is a Special Class item rather than a Structure — consistent with how the earlier
Special Class Building pass distinguished Special Class rating from plain Building rating. Full tracing of
this group's rate build-up and premium mechanics was out of scope for this pass.

---

## Quick reference — end-to-end, Basic Group I (scheduled, Class rated)

```
BGIBaseRateAdjustmentFactor = lookup BaseRateAdjustmentFactor(State|CW, "Basic Group I")

BasicGroupIRate = ((Structure.BasicGroupIBaseRate x LossCostMultiplier) + SubStdConditionRate + VacantBuildingRate)
                  x BasicGroupIRatingTerrFactor x ProtectionClassFactor x BGIBaseRateAdjustmentFactor

COLAdj = round(BasicGroupIRate - SprinklerLeakageExclNonSprinkleredRate, 3)
         x SprinklerLeakageExclSprinkleredFactor x VandalismExclFactor x BuildersRiskFactor

Factor = MaxPeriodOfIndemnityFactor | MonthlyLimitOfIndemnityFactor | ExtraExpenseFactor | TypeOfRiskFactor
         (TypeOfRiskFactor = lookup BusnIncomeFactor(State|CW, CovType, TypeOfRisk, CoinsuranceToUse))

FinalBasicGroupIRate = COLAdj x Factor

Premium = round(round(IRPM x PackageMod x FinalBasicGroupIRate x (Limit/100), 0), 0)
          x CyberExclFactorBGI x CyberExclCOLExcptnsFactorBusnIncomeBGIToUse
```

## Quick reference — end-to-end, Broad (scheduled)

```
BroadBaseRate = lookup BroadFormBaseRate(State|CW, ConstructionTypeToUse,
                    "Business Income Without Extra Expense" | "All Other")     if COL = Broad
              | 0.0                                                            otherwise

BroadRate = BroadBaseRate x LossCostMultiplier
FinalBroadRate = BroadRate                       (straight copy — no COL adjustment, no Factor)

Premium = round(round(IRPM x PackageMod x FinalBroadRate x (Limit/100), 0), 0)
          x CyberExclFactorBroad x CyberExclCOLExcptnsFactorBusnIncomeBroadToUse
```

## Quick reference — end-to-end, Special (scheduled)

```
SpecialIncludingTheftTypeRisk = "Apartments and Condominiums" | "Other than Apartments and Condominiums"
                                  (from ApartmentCondoIndicator, if COL = Special)

SpecialTheftExclusionFactor = lookup SpecialLeaseHoldTimeElementTheftExclusionFactor(State|CW, ApartmentCondoIndicator)
                               if theft excluded, else 1.0

SpecialBaseRate = lookup SpecialFormBldrsRiskTimeElementBaseRate(State|CW, "Y")       [CW 0.018]  if ClassCode=1150
                 | lookup SpecialFormIncldgTheftTimeElementBaseRate(
                       State|CW, ConstructionTypeToUse, CovType, SpecialIncludingTheftTypeRisk)   otherwise

SpecialRate = SpecialBaseRate x LossCostMultiplier
SpecialCauseOfLossAdjustment = SpecialRate x SpecialTheftExclusionFactor
FinalSpecialRate = SpecialCauseOfLossAdjustment      (straight copy — no Factor)

Premium = round(round(IRPM x PackageMod x FinalSpecialRate x (Limit/100), 0), 0)
          x CyberExclFactorSpecial x CyberExclCOLExcptnsFactorBusnIncomeSpecialToUse
```

## Quick reference — end-to-end, Earthquake (Agreed Value, not-in-blanket)

```
EQRate = Structure.EQBaseRate x LossCostMultiplier x SoftStoryModificationFactor
         x EQSprinkleredRiskFactor x BldgHeightFactor x BCEGEQFactor x BuildersRiskEQFactor

EQCauseOfLossAdjustment = StoryModFactor x BuildersRiskFactor x EQRate x EQSprinklerLeakageOnlyBldgFactor
FinalEQRate = EQCauseOfLossAdjustment x EQFactor

AgreedValueFactor = lookup AgreedValueFactorBusnIncome(State|CW, "Y")

Premium = round(round(FinalEQRate x round(AgreedValueFactor - 1, 3) x (AgreedValueLimit/100), 0), 0)
          x CyberExclFactorEQ x CyberExclCOLExcptnsFactorBusnIncomeEQToUse

(non-Agreed-Value, non-blanket scheduled Earthquake premium: no coverage file exists for this case)
```

---
