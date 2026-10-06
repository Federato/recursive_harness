# Cause of Loss — Special Class Business Income Rating Algorithms

**Source ERC package:** `C:\Projects\ISO_ERC_Files\CF\20260601\CFCW20260601V01`
**Line:** Commercial Property (CF), Countrywide, edition 06-01-2026, V01
**Documented:** 2026-08-19

Special Class Business Income rating lives in the `CommercialPropertySpecialClassBusnIncome` datadef group —
the time-element (lost-income) coverage attached to a **Special Class scheduled item**
(`CommercialPropertySpecialClass`) instead of to a Building/Structure. It is the direct structural analogue
of plain `CommercialPropertyBusinessIncome` (attached to `CommercialPropertyStructure`), documented in
`CauseOfLoss_BusinessIncome_RatingAlgorithms.md`.

**Bottom line up front, confirmed by tracing every rate-build-up rule below**: Special Class Business Income
follows the **plain-Business-Income pattern almost exactly** — master orchestration, rate-collapse onto
`Factor` for two of five forms, straight-copy finalization for Broad/Special/Earthquake's own logic, 2-branch
premium files, Agreed-Value-only Earthquake premium — not the Special-Class-Building pattern (named
`ClassDescription` base-rate keys, no LOI factor, 2-branch premium *for different reasons*). It borrows rates
from the coinsured Special Class item exactly the way plain Business Income borrows from the coinsured
Building, for the same three forms (Basic Group I, Basic Group II, Earthquake) — and for Basic Group I it
borrows even more directly than plain BI does (see below). Broad and Special still build their own
Business-Income-specific base rates from dedicated tables, exactly as in the plain group — but with a
significant new wrinkle: those two forms' base-rate lookups are keyed on **hard-coded literal constants**
(`"Frame"` for Broad, `"Frame"` + `"Other than Apartments and Condominiums"` for Special), not on any
class-description-derived key. This mirrors what the Special Class Building pass found for its own Broad
form's construction-blind `"Frame"` key — but goes one step further here, because it also blanks out the
theft/apartment-condo classification dimension plain Business Income uses.

> **Corrected 2026-10-06** (`cf-bgi-chains.html`, SCBI review #44–46 and #52; probes BI-7 to BI-9, BI-12).
> Basic Group I does **not** borrow "even more directly" in the sense of a finished rate. It copies the
> item's `BasicGroupIRate`, which is base x LCM only. The item's vandalism, policy-form, coinsurance and
> deductible factors never reach it. The other corrections below are marked the same way: Group II keys
> come partly from this record (`cf-bgii-chains.html` SCBI #47–52), and the Broad / Special premium
> files send a blank `IncludedInBlkt` straight to $0 (`cf-broad-chains.html` #35, `cf-special-chains.html`
> #42). None of the zeros on this coverage is refused by the engine after 542f0e1.

---

## Master orchestration

All five rate chains are prepared and run in sequence from `SetBlanketRatesAndFactors` (line 2127) in
`CommercialPropertySpecialClassBusnIncomeRules.Rule.xml`:

```
... shared prep (lines 2129-2149) ...
    SetEQCauseOfLossForm
    AttachFormEarthquakeAndVolcanicEruption...SpclClassBusnIncome (4 EQ-endorsement attach rules)
    SetBlanketValuesSection, SetPolicyType, SetBlanketRated, SetEQSubLimitBlktIndicator
    SetLocNumber, SetSpecialClassUnitNumber, SetClassCode
    SetEQDeductibleTier, SetEQTerr, SetMultiPremiumAndDispersionCreditFactor
    SetWatercraftExclBuybackConstrctnOptionConverted
    AttachFormExpandedLimitsOnLossPaymentSpclClassBusnIncome
    SetLossCostMultiplier, SetCauseOfLossToUse
    SetVandalismExclFactor, SetWindstormOrHailExclFactor

SetBGIRatesAndFactors        (line 2924)
SetBGIIRatesAndFactors       (line 2954)
SetBroadRatesAndFactors      (line 3101)
SetSpecialRatesAndFactors    (line 3234)

    SetCoinsuranceToUse (line 3447)
    SetTuitionAndFeesFactor, SetChangesEducationalInstitutionsExtensionOfRecoveryFactor
    SetTypeRiskCombination1Factor, SetTypeRiskCombination2Factor, SetTypeOfRiskFactor
    SetMaxPeriodOfIndemnityCombination1/2Factor, SetMaxPeriodOfIndemnityFactor
    SetMonthlyLimitOfIndemnityCombination1/2Factor, SetMonthlyLimitOfIndemnityFactor
    SetExtraExpenseFactor
    SetFactor                    (line 5824)  <- picks ONE of the above as the shared "Factor"

SetEQRatesAndFactors         (line 5910)

SetFinalRates                 (line 6924)
SetInitializeFloodRatingSpecialClassBusinessIncome
```

This sequence is **structurally identical, rule-for-rule, to plain Business Income's
`SetBlanketRatesAndFactors`** (`CommercialPropertyBusinessIncomeRules.Rule.xml`, line 2201) — same five rate
chains run back-to-back, same `SetFactor` step, same `SetFinalRates` terminal step, same
`SetInitializeFlood...` tail call. The only differences are cosmetic/parent-specific: `SetClassCode` /
`SetSpecialClassUnitNumber` replace Building's construction/story prep, and there is no
`SetBasicGroupIIRatingTerr` / `SetBCEGFactor` / `SetSprinklerSystem` / `SetConstructionCode` /
`SetBuildersRiskFactor` block — Special Class Business Income's shared prep is shorter because several of
those Building-side prep steps are not needed (BCEG, sprinkler system, construction code do not apply to a
Special Class item the way they apply to a Structure).

**Earthquake is confirmed a real fifth rate chain here too** — `SetEQRatesAndFactors` (line 5910) runs
unconditionally alongside the other four, exactly as in plain Business Income and in Special Class Building.
Same wrinkle as plain Business Income: Earthquake has no standalone non-Agreed-Value premium coverage file
(see "Earthquake" section below).

`SetFinalRates` (line 6924) is the terminal step for all five chains, byte-identical in shape to plain
Business Income's:

```
SetFinalBasicGroupIRate    (line 6933)  -> FinalBasicGroupIRate  = BasicGroupICauseOfLossAdjustment x Factor
SetFinalBasicGroupIIRate   (line 6952)  -> FinalBasicGroupIIRate = BasicGroupIICauseOfLossAdjustment x Factor
SetFinalBroadRate          (line 6971)  -> FinalBroadRate        = BroadRate                (straight copy)
SetFinalSpecialRate        (line 6987)  -> FinalSpecialRate      = SpecialCauseOfLossAdjustment (straight copy)
SetFinalEQRate             (~line 7003) -> FinalEQRate           = EQCauseOfLossAdjustment x EQFactor
```

The same structural fact holds as in plain Business Income: **`Factor` (the shared
coinsurance/type-of-risk/period-of-indemnity multiplier, `SetFactor`, line 5824) applies only to Basic Group
I and Basic Group II.** Broad and Special finalize as straight copies of their own rates — confirmed by
reading `SetBroadRate` (line 3187) and `SetSpecialCauseOfLossAdjustment` (line 3439): neither references
`CoinsuranceToUse`, `TypeOfRiskFactor`, or `Factor` anywhere in their build-up.

`SetFactor` itself (line 5824) is **byte-identical in shape** to plain Business Income's version: a
priority-ordered `Choose` picking `MaxPeriodOfIndemnityFactor` → `MonthlyLimitOfIndemnityFactor` →
`ExtraExpenseFactor` → `TypeOfRiskFactor`, each populated only if `Factor` is currently null. (Two blank
inputs zero this `Factor`; see "The shared Factor" below, corrected 2026-10-06.)

---

## File map

| Piece | File | Anchor |
|---|---|---|
| Master orchestration | `Rules\CommercialPropertySpecialClassBusnIncomeRules.Rule.xml` | `SetBlanketRatesAndFactors` — line 2127 |
| Rate build-up, Basic Group I | same file | `SetBGIRatesAndFactors` — line 2924 |
| Rate build-up, Basic Group II | same file | `SetBGIIRatesAndFactors` — line 2954 |
| Rate build-up, Broad | same file | `SetBroadRatesAndFactors` — line 3101 |
| Rate build-up, Special | same file | `SetSpecialRatesAndFactors` — line 3234 |
| Rate build-up, Earthquake | same file | `SetEQRatesAndFactors` — line 5910 |
| Shared "Factor" (coinsurance/type-of-risk) | same file | `SetFactor` — line 5824 |
| Final-rate consolidation | same file | `SetFinalRates` — line 6924 |
| Total-premium roll-up | same file | `ErcRate` — line 7029 (`SetSpecialClassBusinessIncomeCoveragePremiumSum`, `SetTotalAgreedValuePremium`, `SetTotalExtendedPeriodOfIndemnityCoveragePremium`, TRIA/terrorism) |
| Premium calc, Basic Group I | `Rules\CommercialPropertySpecialClassBusnIncomeBasicGroupICoverageRules.Rule.xml` | `SetPremium` — line 43 |
| Premium calc, Basic Group II | `Rules\CommercialPropertySpecialClassBusnIncomeBasicGroupIICoverageRules.Rule.xml` | `SetPremium` — line 43 |
| Premium calc, Broad | `Rules\CommercialPropertySpecialClassBusnIncomeBroadCoverageRules.Rule.xml` | `SetPremium` — line 60 |
| Premium calc, Special | `Rules\CommercialPropertySpecialClassBusnIncomeSpecialCoverageRules.Rule.xml` | `SetPremium` — line 60 |
| Premium calc, Earthquake (Agreed Value only) | `Rules\CommercialPropertySpecialClassBusnIncomeAgreedValEarthquakeCoverageRules.Rule.xml` | `SetPremium` — line 101 |
| Agreed Value add-on (x5 forms, all COL) | `Rules\CommercialPropertySpecialClassBusnIncomeAgreedVal{BasicGroupI,BasicGroupII,Broad,Special,Earthquake}CoverageRules.Rule.xml` | mirrors plain-BI Agreed Value file set exactly |
| Extended Period of Indemnity add-on (x5 forms — confirmed, incl. Basic Group II) | `Rules\CommercialPropertySpecialClassBusnIncomeExtendedPeriodOfIndemnityCoverage{BasicGroupI,BasicGroupII,Broad,Special,Earthquake}CoverageRules.Rule.xml` | `SetPremium` — pattern shared |
| Interruption of Computer Operations add-on | `Rules\CommercialPropertySpecialClassBusnIncomeInterruptionOfComputerOperationsCoverageRules.Rule.xml` | not traced in depth — endorsement layer |
| Watercraft Exclusion Buyback add-on | `Rules\CommercialPropertySpecialClassBusnIncomeWatercraftExclusionBuybackCoverageRules.Rule.xml` | not traced in depth — endorsement layer |
| Master coverage-record rule (attach/dispatch) | `Rules\CommercialPropertySpecialClassBusnIncomeCoverageRules.Rule.xml` | not traced in depth |

### File-inventory correction to the plain-BI doc

`CauseOfLoss_BusinessIncome_RatingAlgorithms.md` (its "Special Class Business Income" closing section) states
"no Basic Group II variant confirmed present by name" for the Extended Period of Indemnity family. **This is
incorrect** — a direct directory listing of
`Rules\CommercialPropertySpecialClassBusnIncomeExtendedPeriodOfIndemnityCoverage*CoverageRules.Rule.xml`
confirms all **five** forms exist, including
`CommercialPropertySpecialClassBusnIncomeExtendedPeriodOfIndemnityCoverageBasicGroupIICoverageRules.Rule.xml`
— a full one-for-one match with plain Business Income's five-form Extended Period of Indemnity set. This
correction should be treated as authoritative going forward; it was verified by direct `find` enumeration of
the `Rules\` directory during this pass (2026-08-19).

Also newly confirmed (not mentioned at all in the plain-BI doc's inventory sketch): Special Class Business
Income has a **full Agreed Value family for all five forms**
(`AgreedValBasicGroupICoverageRules`, `AgreedValBasicGroupIICoverageRules`, `AgreedValBroadCoverageRules`,
`AgreedValSpecialCoverageRules`, `AgreedValEarthquakeCoverageRules`, plus a parent
`AgreedValCoverageRules.Rule.xml`) — and cross-checking, **plain Business Income has the identical five-file
Agreed Value set** (confirmed by directory listing of `Rules\CommercialPropertyBusinessIncomeAgreedVal*`).
The plain-BI doc's file map only lists the Earthquake Agreed Value file; the other four Agreed Value forms
exist there too and were simply out of scope for that pass, not absent.

---

## Basic Group I — rate build-up

Executed by `SetBGIRatesAndFactors` (line 2924) — a **2-step chain**, one step shorter than plain Business
Income's 3-step BGI chain:

```
SetBasicGroupIRate
SetBasicGroupICauseOfLossAdjustment
```

### Step 1 — Rate (cross-coverage borrow, no adjustment factor)
`SetBasicGroupIRate` (line 2930):

```
if BasicGroupIRate is null:
    BasicGroupIRate = ../../BasicGroupIRate
```

**This is the single most important structural fact about this pass.** Special Class Business Income's
Basic Group I rate is not built from any Business-Income-specific lookup or adjustment factor at all — it is
a **direct, unconditional copy of the coinsured Special Class item's own already-fully-computed
`BasicGroupIRate`** (two levels up — the same nesting relationship plain Business Income has to its
Building parent). There is no `BGIBaseRateAdjustmentFactor` step, no `LookupBaseRateAdjustmentFactor` call,
and no `BasicGroupIRateSpecialClass`-table lookup anywhere in this file — confirmed by grepping
`CommercialPropertySpecialClassBusnIncomeRules.Rule.xml` for `BaseRateAdjustmentFactor`: **zero matches**.

Contrast plain Business Income, which reads `../../BasicGroupIBaseRate` (the Building's **base** rate, before
territory/protection-class/addend treatment) and then reconstructs a parallel rate formula with its own
`BGIBaseRateAdjustmentFactor` multiplier. Special Class Business Income instead reads
`../../BasicGroupIRate` — the Special Class item's **fully rated** Basic Group I rate (base rate x LCM,
already inclusive of whatever the Special Class chain applied) — and adds nothing on top at the rate step.
This is a *tighter* cross-coverage dependency than plain Business Income has, not merely an equivalent one:
Special Class Business Income's Basic Group I rate is arithmetically nothing more than "the Special Class
item's own rate, passed through."

**Corrected 2026-10-06** (`cf-bgi-chains.html`, SCBI review #44, #45; probes BI-7, BI-8, BI-9, BI-11,
BI-13, BI-14). The paragraph above overstates it. `../../BasicGroupIRate` is the item's step-3 value,
`r3(Base x LCM)` (SC rules :3029). It is taken **before** the item's vandalism, StdPropPol, coinsurance and
deductible factors. It is not the item's final rate. Golden case: the item's `BasicGroupIRate` is 0.07 and its
`FinalBasicGroupIRate` is 0.066; this record uses 0.07. Proof in the engine (OH, both editions): the item's
coinsurance at 100% or deductible at 250 moves the item ($62, $70) but leaves this record at $39 (BI-8,
BI-9). Doubling the item's LCM doubles both ($130, $77; BI-7). This record's own LCM does nothing here
(5.0 still $39; BI-13). So the dependency is looser than "tighter": this record needs only the item's third
step, not its finished chain. Two more facts the paragraph left out: a submitted `BasicGroupIRate` is kept
(0.5 gives $275; BI-14), and a blank item `ClassDescription` (item base 0) zeroes this record too ($0,
outcome "rated"; BI-11).

### Step 2 — Cause-of-loss adjustment
`SetBasicGroupICauseOfLossAdjustment` (line 2946), 3 decimals, unconditional:

```
BasicGroupICauseOfLossAdjustment = BasicGroupIRate x VandalismExclFactor
```

Only one multiplier — no sprinkler-leakage subtraction/factor, no Builders Risk factor, no
`StdPropPolGroupIFactor`. Simpler than **both** plain Business Income's version (subtract-then-round plus
three factors) and Special Class Building's own Basic Group I COL adjustment (`Rate x VandalismExclFactor x
StdPropPolGroupIFactor` — two factors). Special Class Business Income drops the standard-property-policy
factor entirely; grepping the file for `StdPropPolGroupIFactor` and `BuildersRiskFactor` in the BGI/BGII
chains returns no matches in either rate chain.

### Final rate
`FinalBasicGroupIRate = BasicGroupICauseOfLossAdjustment x Factor` (`SetFinalBasicGroupIRate`, line 6933) —
same shared-`Factor` pattern as plain Business Income, same absence of a separate coinsurance, LOI, or
deductible factor step anywhere in the chain.

---

## Basic Group I — premium

`CommercialPropertySpecialClassBusnIncomeBasicGroupICoverageRules.Rule.xml`

### Gate — coverage on policy
`SetCoverageOnPolicyIndicator` (line 32): **hardcoded constant `1`** — same as plain Business Income's Basic
Group I gate, and the same as Special Class Building's own hardcoded-1 BGI gate. All three groups agree here.

### Two branches only (scheduled / blanket) — matches plain Business Income, not Special-Class-Building's reasoning
`SetPremium` (line 43) branches on `../IncludedInBlkt = "No"` (scheduled) vs. the `Yes` / blanket case gated on
`BlktTotalFullValueAmount > 0`:

```
Branch A (../IncludedInBlkt = "No"):
Premium =
  round(round(
    IRPMFactor x PackageModFactor x FinalBasicGroupIRate x (Limit / 100)
  , 0), 0)
  x CyberIncidentExclusionFactorBGI x CyberIncidentExclusionCOLExcptnsFactorBusnIncomeBGIToUse

Branch B (../IncludedInBlkt <> "No", BlktTotalFullValueAmount > 0):
Premium =
  round(round(
    IRPMFactor x PackageModFactor x BlktBasicGroupIAvgRate x (FullBusnIncomeValue / BlktTotalFullValueAmount)
      x (BlktLimit / 100)
  , 0), 0)
  x CyberIncidentExclusionFactorBGI x CyberIncidentExclusionCOLExcptnsFactorBusnIncomeBGIToUse
  (else Premium = 0.0)
```

Byte-shape-identical to plain Business Income's Basic Group I premium file (line-for-line, only the
`IRPMFactor`/`PackageModFactor` `../` depth and datadef names carried over unchanged) — confirmed by direct
read. `IRPMFactor` and `PackageModFactor` are read **seven** levels up, the same depth plain Business Income
uses (Special Class Business Income has the same extra nesting under its parent record as plain Business
Income has under Structure). **`MultiPremiumAndDispersionCreditFactor` does not appear in this formula**,
exactly as in plain Business Income — even though `SetMultiPremiumAndDispersionCreditFactor` runs during
shared prep (line 2143) and populates the datadef.

**Corrected 2026-10-06** (`cf-bgi-chains.html`, SCBI review #46, #51; probes BI-12, MOD-2). Branch B is not
only the "Yes" case. The test is `IncludedInBlkt = "No"`, so **anything but "No", blank included**, goes to
Branch B. A blank `IncludedInBlkt` has no blanket total, so it prices **$0 with outcome "rated"** (BI-12).
MultiPrem 0.9 leaves this record at $39 while the item drops to $59 (MOD-2), as stated above.

This two-branch shape happens to match Special Class Building's own two-branch premium files too, but for a
**different reason**: Special Class Building has only two branches because it has no `CovType` taxonomy at
all (no Legal Liability, no Leasehold Interest). Special Class Business Income has only two branches for the
**same reason plain Business Income does** — Business Income coverage never carries Legal Liability or
Leasehold Interest regardless of what it's attached to. The convergence to "2 branches" happens on both
axes (Special Class parent, Business Income coverage type) independently; this group inherits it from both.

---

## Basic Group II — differences from Basic Group I

`SetBGIIRatesAndFactors` (line 2954), a 4-step chain:

```
SetBasicGroupIIBaseRate
SetLowestBasicGroupIIBaseRate
SetBasicGroupIIRate
SetBasicGroupIICauseOfLossAdjustment
```

### Step 1 — Base rate (independent lookup, not a cross-reference)
`SetBasicGroupIIBaseRate` (line 2962), gated on `../../BasicGroupIIRatingTerr` and `../../BasicGroupIISymbol`
both non-blank:

```
BasicGroupIIBaseRate = LookupBasicGroupIIRate(State|CW, ../../BasicGroupIIRatingTerr, ../../BasicGroupIISymbol, "Bldg")
                        (matrix BasicGroupIIRate)
                      | 0.0   otherwise
```

**Unlike Basic Group I, Basic Group II performs its own matrix lookup** (`LookupBasicGroupIIRate`, line
11438) rather than copying a fully-computed sibling rate — but the lookup **keys entirely on values read
from the coinsured Special Class item** (`BasicGroupIIRatingTerr`, `BasicGroupIISymbol`, both `../../`).
This is exactly the same pattern plain Business Income uses for its own Basic Group II (`LookupBasicGroupIIRate`
against the same `BasicGroupIIRate` matrix, same 4-key shape, territory/symbol read from the parent). The
`CovType` column present in the table header (`BasicGroupIIRate.RateTable.csv`:
`StateCode,BasicGroupIIRatingTerr,BasicGroupIISymbol,CovType,Rate`) is always keyed with the literal constant
`"Bldg"` here too — not a Business-Income-specific covType value.

**`BasicGroupIIRate.RateTable.csv` and `LowestBasicGroupIIRate.RateTable.csv` are both header-only — zero
data rows** (confirmed directly: `wc -l` returns 1 for each, i.e. the header row only). This is the exact
same gap the Building pass's BUILD-LOG Entry 3 correction found for these two tables — they are shared across
Building, plain Business Income, and Special Class Business Income, and **none of the three coverages can
resolve a Basic Group II base rate at the countrywide level in this package edition** without a state-specific
filing layered on top.

**Corrected 2026-10-06** (`cf-bgii-chains.html`, SCBI review #47, #52, #54; probes BI-1, BI-11, BI-12 in the
Group II notes). Two things. First, header-only at countrywide is the **normal state-filed pattern**, not a
gap. Every state files its own rows (OH files 8), and this record rates $321 in OH at 2026-01-01 and $361
at 2026-07-01 (BI-1). A key with no filed row now refuses (C28-05). Second, "keys entirely on values read
from the item" is too strong. The territory, the symbol and the class multiplier come from the item. The
LCM, the wind/hail exclusion, the coinsurance (as a factor key), `CovType`, `TypeOfRisk`, the limits and
`IncludedInBlkt` are this record's own. A blank item symbol, or a blank location territory with no building
on the location, prices both the item and this record at **$0, outcome "rated"** (BI-11, BI-12).

### Step 2 — Lowest base rate
`SetLowestBasicGroupIIBaseRate` (line 3012): same shape, `LookupLowestBasicGroupIIRate` (line 11653) against
matrix `LowestBasicGroupIIRate`, keyed State|CW, `../../BasicGroupIISymbol`, `"Bldg"` (no territory) — same
empty-table gap as step 1. **Corrected 2026-10-06** (`cf-bgii-chains.html`, SCBI review #55): state-filed,
not a gap, as in step 1. It is 0.0 when the item's symbol is blank.

### Step 3 — Rate
`SetBasicGroupIIRate` (line 3056), 3 decimals:

```
BasicGroupIIRate = BasicGroupIIBaseRate x LossCostMultiplier x ../../BasicGroupIINumericValue
```

`BasicGroupIINumericValue` is read from the Special Class item (two levels up) — Special Class Business
Income does not recompute the class-specific hazard load; it reuses the Special Class item's already-resolved
value (which, per the Special Class Building doc, is itself looked up by `ClassDescription` via
`SpecialClassBasicGroupIINumber`, not by `ClassCode`/`OpenSides`). No BCEG factor multiplier here — matches
Special Class Building's own Basic Group II rate (which also has no BCEG term), and differs from plain
Business Income's `BasicGroupIIRate` formula, which does multiply in `BCEGFactor`.

**Corrected 2026-10-06** (`cf-bgii-chains.html`, SCBI review #48, #49; probes BI-7, BI-8, BI-9, BI-13,
BI-14 in the Group II notes). Two gaps in the step above:

- **The item's numeric value is not fixed.** It is 1.0 when the **item** has a wind/hail exclusion, so the
  item's exclusion cuts this record from $321 to $40 though this record has no exclusion of its own (BI-14).
  It is 0 when the item's `ClassDescription` is blank, so this record prices $0, outcome "rated" (BI-13).
- **`LossCostMultiplier` is this record's own.** It is copied from the item only when this record sends none
  (`SetLossCostMultiplier` :2742). Own 5.0 gives $1,606 (BI-7). None sent, with the item at 2.0, gives $642
  (BI-8). A submitted 1.0 holds at $321 while the item goes to 2.0 (BI-9).

### Step 4 — Cause-of-loss adjustment
`SetBasicGroupIICauseOfLossAdjustment` (line 3078):

```
if no CommercialPropertyWindstormOrHailExclusionSpclClassBusnIncome record:
    BasicGroupIICauseOfLossAdjustment = BasicGroupIIRate                       (straight copy)
else:
    BasicGroupIICauseOfLossAdjustment =
        LowestBasicGroupIIBaseRate x LossCostMultiplier x WindstormOrHailExclFactor
```

Same two-path shape as plain Business Income and Building (rebuild from the lowest base rate when wind/hail
is excluded), but **with no `BuildersRiskFactor` or `StdPropPolGroupIIFactor` multiplication in either
branch** — the no-wind/hail-exclusion branch is a bare straight copy of `BasicGroupIIRate`, simpler than both
of its counterparts (plain Business Income multiplies by `BuildersRiskFactor`; Special Class Building
multiplies by `StdPropPolGroupIIFactor`).

### Final rate
`FinalBasicGroupIIRate = BasicGroupIICauseOfLossAdjustment x Factor` (same shared `Factor` as Group I).

---

## Basic Group II — premium

`CommercialPropertySpecialClassBusnIncomeBasicGroupIICoverageRules.Rule.xml` is **byte-shape-identical** to
the Basic Group I premium file (confirmed lines 32-71: hardcoded `CoverageOnPolicyIndicator = 1`, same two
branches), with only the datadef names swapped (`FinalBasicGroupIIRate`, `BlktBasicGroupIIAvgRate`,
`CyberIncidentExclusionFactorBGII`, `CyberIncidentExclusionCOLExcptnsFactorBusnIncomeBGIIToUse`) — the same
Group I/II premium-file relationship every other datadef group in this package has.

**Corrected 2026-10-06** (`cf-bgii-chains.html`, SCBI review #51; probes BI-23, BI-27). Confirmed equal to
this record's Group I file after renaming. The scheduled branch needs `IncludedInBlkt = "No"` exactly;
anything else, blank included, goes to the blanket side and prices **$0, outcome "rated"** (BI-23). There
is no multi-premium credit: 0.9 leaves $321 while the item drops to $490 (BI-27).

---

## Broad — rate build-up

`SetBroadRatesAndFactors` (line 3101), a 2-step chain — the shortest of all five Special Class Business
Income forms, matching plain Business Income's shortest-chain form:

```
SetBroadBaseRate
SetBroadRate
```

### Step 1 — Base rate (own table, hard-coded construction-blind key)
`SetBroadBaseRate` (line 3107), gated on `CauseOfLossToUse = "Broad"`:

```
if CovType = "Business Income Without Extra Expense":
    BroadBaseRate = LookupBroadFormBaseRate(covTypeBroadForm = "Business Income Without Extra Expense")
else:
    BroadBaseRate = LookupBroadFormBaseRate(covTypeBroadForm = "All Other")
else (COL <> Broad):
    BroadBaseRate = 0.0
```

`LookupBroadFormBaseRate` (line 11474) reads matrix `BroadFormBaseRate` — **the same shared table Building,
plain Business Income, and Special Class Building all read** — but keys on a **hard-coded literal
`"Frame"`**, not `ConstructionTypeToUse`:

```
Keys: /*/State/Code (falls back to CW), Constant "Frame", covTypeBroadForm param
```

This is a direct structural match to what the Special Class Building pass found for its own Broad form
(`LookupBroadFormBaseRate` keyed on literal `"Frame"` there too) — **and a genuine departure from plain
Business Income**, whose `LookupBroadFormBaseRate` keys on the item's actual `ConstructionTypeToUse` and
therefore varies by construction. Special Class Business Income's Broad base rate is **always** the
`"Frame"` row of `BroadFormBaseRate`, regardless of the Special Class item's actual construction (Special
Class items don't carry a `ConstructionTypeToUse` in the same sense a Structure does — there is no
construction-code dimension anywhere in this datadef group's rate chains, consistent with Special Class
Building's own construction-blind Basic Group I rating).

Confirmed CW rows exist: `("CW","Frame","Business Income Without Extra Expense",0.011)` and
`("CW","Frame","All Other",0.023)` — `BroadFormBaseRate.RateTable.csv`, 31 lines total (30 data rows,
1 header). Both rows resolve; this lookup is **not** blocked by an empty-table gap the way Basic Group II's
is.

**Corrected 2026-10-06** (`cf-broad-chains.html`, SCBI review #34, #37, #40, #41; probes BI-2, BI-4, BI-5,
BI-7, BI-15, BI-25 in the Broad notes). The "Frame" pin is confirmed (the item at Fire Resistive still $23,
BI-7). But nothing is inherited from the item: this rule has its own literal, set separately. The
comparison with Basic Group II is out of date: Group II is state-filed, not blocked. Also:

- The cause of loss tested is this record's **own**. The item's is never read. Broad here with Basic on the
  item prices $23; the reverse prices $0 with the coverage off (BI-5, BI-4).
- There is **no `PolicyType` test**, unlike the item's Broad. A Standard Property policy zeroes the item's
  Broad but this record still prices $23 (BI-15).
- Without Extra Expense reads 0.011 ($11, BI-2). Everything else, blank `CovType` included, reads "All Other"
  0.023 ($23, BI-25).

### Step 2 — Rate
`SetBroadRate` (line 3187), 3 decimals, same gate:

```
BroadRate = BroadBaseRate x LossCostMultiplier
```

That is the entire chain — no cause-of-loss adjustment, no LOI factor, no coinsurance-linked `Factor`, no
deductible factor. `FinalBroadRate` is a straight copy of `BroadRate` (`SetFinalBroadRate`, line 6971) — same
as plain Business Income.

**Corrected 2026-10-06** (`cf-broad-chains.html`, SCBI review #36, #39; probes BI-8, BI-9, BI-10 in the
Broad notes). `LossCostMultiplier` is this record's own, copied from the item only when blank (:2742). Own
5.0 gives $115; none sent with the item at 2.0 gives $46; own 1.0 with the item at 2.0 holds $23. The rate
step repeats the base step's `CauseOfLossToUse = "Broad"` test and writes 0.0 otherwise; that test is
redundant with the coverage gate.

---

## Broad — premium

`CommercialPropertySpecialClassBusnIncomeBroadCoverageRules.Rule.xml`

### Gate — coverage on policy
`SetCoverageOnPolicyIndicator` (line 32): `CoverageOnPolicyIndicator = 1` only when
`../CauseOfLossToUse = "Broad"` — exact-equality test, matching plain Business Income's Broad gate exactly
(and Special Class Building's own Broad gate, and Building's).

### Branch A — scheduled / Branch B — blanket
Structurally identical to Basic Group I's premium file, substituting `FinalBroadRate` / `BlktBroadAvgRate` /
`CyberIncidentExclusionFactorBroad` / `CyberIncidentExclusionCOLExcptnsFactorBusnIncomeBroadToUse`. Confirmed
by direct read (lines 60-158) — a three-way `Choose` (`IncludedInBlkt = "No"` / `"Yes"` / otherwise-zero),
functionally the same two live branches as Basic Group I's `If`/`Else` shape, just expressed with `Choose`
instead of nested `If`.

**Corrected 2026-10-06** (`cf-broad-chains.html`, SCBI review #35; probes BI-16, BI-17, BI-19, BI-20, X-6 in
the Broad notes). The three-way `Choose` is not the same as Group I's `If`/`Else`. "No" goes scheduled.
"Yes" goes to the `BlktTotalFullValueAmount > 0` test. **Anything else, blank included, goes straight to
0.0.** So a blank `IncludedInBlkt` prices **$0 with the coverage on and outcome "rated"** (BI-16). Group I's
`Else` sends a blank to its blanket test instead; the dollars are the same $0. A blanket record with a blank
`FullBusnIncomeValue` also prices $0 "rated" (X-6). A blanket election with no policy blanket record turns
the coverage off (BI-17). The scheduled branch rounds once, then applies two cyber factors. There is no
multi-premium credit (0.9 leaves $23, BI-20). PackageMod 0.75 with IRPM 0.99 gives $17 (BI-19).

---

## Special — rate build-up

`SetSpecialRatesAndFactors` (line 3234), a 5-step chain (2 fewer than plain Business Income's 6-step Special
chain):

```
SetSpecialTheftExclusionIndicator
SetSpecialTheftExclusionFactor
SetSpecialBaseRate
SetSpecialRate
SetSpecialCauseOfLossAdjustment
```

**No `SetSpecialIncludingTheftTypeRisk` prerequisite rule exists in this file** (confirmed by grep — zero
matches for `SpecialIncludingTheftTypeRisk` anywhere in `CommercialPropertySpecialClassBusnIncomeRules.Rule.xml`).
This is the sharpest divergence from plain Business Income found in this pass.

### Prerequisite — theft exclusion indicator
`SetSpecialTheftExclusionIndicator` (line 3243): `1` if a `CommercialPropertyTheftExclusionSpclClassBusnIncome`
record exists, else `0` — same shape as plain Business Income's version, reading the
Special-Class-Business-Income-specific form-attachment table instead of the plain group's.

### Step 1 — Theft exclusion factor
`SetSpecialTheftExclusionFactor` (line 3262), gated on `CauseOfLossToUse = "Special"` AND
`SpecialTheftExclusionIndicator = 1` (no `ApartmentCondoIndicator`-non-blank test, unlike plain Business
Income):

```
SpecialTheftExclusionFactor = LookupSpecialLeaseHoldTimeElementTheftExclusionFactor(State|CW)
else: 1.0
```

`LookupSpecialLeaseHoldTimeElementTheftExclusionFactor` (line 11974) still keys on
`ApartmentCondoIndicator` internally (matrix `SpecialLeaseHoldTimeElementTheftExclusionFactor`, confirmed
2 CW data rows: `("CW","Yes",0.96)`, `("CW","No",0.86)` — 3 lines total including header) — so the
`ApartmentCondoIndicator` dimension survives at the lookup-key level even though the gating `If` above it
doesn't test it explicitly the way plain Business Income's does. **Note the CW factor values themselves
(0.96 / 0.86) differ from what the plain Business Income pass would need to cross-check** — this document
does not claim they match plain Business Income's own table row-for-row; that comparison was out of scope.
**Corrected 2026-10-06** (`cf-special-chains.html`, SCBI review #44 and confirmed list; probes SB-2, SB-3,
SB-4 in the Special notes; first found by C7-20). The indicator does not survive: the lookup keys on a
constant `"No"`, so the factor is always 0.86 (SB-2 and SB-3 both $40, with "Yes" on the record and the
item). The exclusion record tested is this record's own; the item's theft exclusion does not reach it
(SB-4, $47).

### Step 2 — Base rate (hard-coded literal keys on both dimensions)
`SetSpecialBaseRate` (line 3312), gated on `CauseOfLossToUse = "Special"`:

```
if CovType = "Business Income Without Extra Expense":
    SpecialBaseRate = LookupSpecialFormIncldgTheftTimeElementBaseRate(covType = "Business Income Without Extra Expense")
else:
    SpecialBaseRate = LookupSpecialFormIncldgTheftTimeElementBaseRate(covType = "All Other")
else (COL <> Special):
    SpecialBaseRate = 0.0
```

**There is no `ClassCodeToUse = "1150"` Builders Risk branch** — confirmed absent by reading the full rule
body; unlike plain Business Income (which has a dedicated `SpecialFormBldrsRiskTimeElementBaseRate` lookup
for Builders Risk class code 1150), Special Class Business Income's `SpecialBaseRate` always resolves through
`LookupSpecialFormIncldgTheftTimeElementBaseRate` regardless of class code.

`LookupSpecialFormIncldgTheftTimeElementBaseRate` (line 11711) reads matrix
`SpecialFormIncldgTheftTimeElementBaseRate` — **the same table plain Business Income uses** — but keys on
**two hard-coded literal constants**, not on data-derived values:

```
Keys: /*/State/Code (falls back to CW), Constant "Frame", covType param, Constant "Other than Apartments and Condominiums"
```

Confirmed by reading the literal `<rul:Constant Type="string">Frame</rul:Constant>` and
`<rul:Constant Type="string">Other than Apartments and Condominiums</rul:Constant>` key nodes at lines
11717-11719 and 11726-11728. **This lookup can never resolve an "Apartments and Condominiums" row, no matter
what `ApartmentCondoIndicator` is set to** — the apartment/condo dimension that Step 1's theft-exclusion-
factor lookup still honors is silently dropped at the base-rate step. Confirmed CW rows exist for the
"Other than Apartments and Condominiums" key that this lookup will always hit:
`("CW","Frame","Business Income Without Extra Expense","Other than Apartments and Condominiums",0.033)` and
`("CW","Frame","All Other","Other than Apartments and Condominiums",0.047)` —
`SpecialFormIncldgTheftTimeElementBaseRate.RateTable.csv`, 25 lines total (24 data rows, 1 header; same file
plain Business Income reads). The "Apartments and Condominiums" rows in that same table (e.g.
`("CW","Frame","Business Income Without Extra Expense","Apartments and Condominiums",0.016)`) exist in the
file but are **unreachable from this rule** — they can only ever be hit by plain Business Income's own
`SpecialIncludingTheftTypeRisk`-driven lookup, which does vary the key. Flagged as an open question below:
whether this is an intentional ISO simplification for Special Class scheduled property (which arguably
doesn't have an apartment/condo occupancy concept the way a Building does) or an ERC-authoring oversight
could not be determined from the rules file alone.

### Step 3 — Rate
`SetSpecialRate` (line 3392), 3 decimals, same gate:

```
SpecialRate = SpecialBaseRate x LossCostMultiplier
```

### Step 4 — Cause-of-loss adjustment
`SetSpecialCauseOfLossAdjustment` (line 3439), 3 decimals, unconditional:

```
SpecialCauseOfLossAdjustment = SpecialRate x SpecialTheftExclusionFactor
```

Same two-factor shape as plain Business Income's Special COL adjustment.

### Final rate
`FinalSpecialRate = SpecialCauseOfLossAdjustment` — straight copy (`SetFinalSpecialRate`, line 6987), no
`Factor` multiplication, matching Broad and matching plain Business Income's Special form.

**Corrected 2026-10-06** (`cf-special-chains.html`, SCBI review #41, #43, #45; probes SB-12, SB-15, SB-16,
SB-17 in the Special notes). The base-rate gate tests only this record's own `CauseOfLossToUse`. There is
**no `PolicyType` test**: a Standard Property policy zeroes the item's Special but this record still prices
$47 (SB-15). Special here with Basic on the item prices $47 (SB-12). `LossCostMultiplier` is this record's
own, the item's only when blank: own 2.0 gives $94; none sent with the item at 2.0 also gives $94 (SB-16,
SB-17).

---

## Special — premium

`CommercialPropertySpecialClassBusnIncomeSpecialCoverageRules.Rule.xml` is **structurally identical to the
Broad premium file** (confirmed line-by-line: same `CoverageOnPolicyIndicator` shape testing
`../CauseOfLossToUse = "Special"`, same three-way `Choose` with two live branches, same nested-`Round`-then-
`Product`-by-cyber-factors rounding pattern). Exactly matches the relationship plain Business Income's own
Special/Broad premium files have to each other — and, per the Special Class Building doc, **Special Class
Building's own Special premium file also uses this standard rounding pattern** (not Building's
Product-only-no-Round quirk). All three of Building, Special Class Building, and Special Class Business
Income converge on the standard nested-`Round` pattern for Special premium; only plain **Building**'s Special
premium file is the documented outlier with the no-`Round` shape.

**Corrected 2026-10-06** (`cf-special-chains.html`, SC review #21 and SCBI review #42; probes S-42, SB-22,
SB-26, SB-27 in the Special notes). The comparison with Special Class Building is wrong (C6-27 had already
corrected the Special Class doc). Special Class Building's Special premium file has **no `Round` element**:
nested `Product`s round to $1 at each of six steps, like Building's Special file and Special Class Broad's
(PackageMod 0.75 with IRPM 0.99 gives $32, S-42). This record's own Special file does match its Broad file
word for word. Its `Choose` sends **anything but "No" or "Yes", blank included, straight to 0.0**: a blank
`IncludedInBlkt` prices $0 with the coverage on, outcome "rated" (SB-22). There is no multi-premium credit
(0.9 leaves $47, SB-27); PackageMod 0.75 with IRPM 0.99 gives $35 (SB-26).

---

## Earthquake — rate build-up

`SetEQRatesAndFactors` (line 5910), a 9-step chain:

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

The first six steps build the same sub-limit machinery (CP 10 45 / CP 10 29-style sub-limit forms) that
plain Business Income's Earthquake chain builds — not traced further here, matching that document's own
scope note.

### Step 8 — Rate (pure cross-coverage borrow)
`SetEQRate` (line 6882), 3 decimals:

```
if EQRate is null:
    EQRate = ../../EQRate
```

**Confirmed: `EQRate` is a direct, unconditional copy of the coinsured Special Class item's own
already-fully-computed `EQRate`** (two levels up) — no local lookup, no soft-story/sprinklered-risk/
building-height/BCEG-EQ/Builders-Risk-EQ factor multiplication anywhere in this file (grepped for each: zero
matches in the EQ chain). This is a **tighter** cross-reference than plain Business Income's own Earthquake
rate (`EQRate = ../../EQBaseRate x LossCostMultiplier x SoftStoryModificationFactor x
EQSprinkleredRiskFactor x BldgHeightFactor x BCEGEQFactor x BuildersRiskEQFactor` — a **base** rate cross-
reference plus six of its own multipliers). Special Class Business Income instead borrows the Special Class
item's fully-rated `EQRate` wholesale, exactly the same "arithmetically nothing more than a pass-through"
pattern found for Basic Group I above.

### Step 9 — Cause-of-loss adjustment
`SetEQCauseOfLossAdjustment` (line 6898), unconditional:

```
EQCauseOfLossAdjustment = 0.0                    if EQCovIndicator in ("Not Applicable", "No Coverage")
                         | EQRate                 otherwise (straight copy)
```

Simpler than plain Business Income's version (`StoryModFactor x BuildersRiskFactor x EQRate x
EQSprinklerLeakageOnlyBldgFactor` — four factors) — Special Class Business Income applies **no** additional
multiplier at all once it has borrowed `EQRate`; it only gates whether the borrowed rate counts or is zeroed.

### Final rate
`FinalEQRate = EQCauseOfLossAdjustment x EQFactor` (`SetFinalEQRate`) — `EQFactor` is a distinct datadef from
the shared `Factor`, built by `SetEQFactor` from the sub-limit machinery above, same relationship plain
Business Income has between `EQFactor` and `Factor`.

---

## Earthquake — premium: the same Agreed Value asymmetry as plain Business Income

**There is no `CommercialPropertySpecialClassBusnIncomeEarthquakeCoverageRules.Rule.xml` file** — confirmed
by directory listing: the only Earthquake premium coverage file in the whole
`CommercialPropertySpecialClassBusnIncome*` family is
`CommercialPropertySpecialClassBusnIncomeAgreedValEarthquakeCoverageRules.Rule.xml`. `FinalEQRate` is
computed unconditionally by the master rate chain but is only ever converted into standalone chargeable
premium through the Agreed Value coverage record — exactly the plain-Business-Income asymmetry, confirmed by
`SetSpecialClassBusinessIncomeCoveragePremiumSum` (line 7039), which sums only
`CommercialPropertySpecialClassBusnIncomeBasicGroupICoverage/Premium`, `...BasicGroupIICoverage/Premium`,
`...BroadCoverage/Premium`, `...SpecialCoverage/Premium` — **no Earthquake term** — while
`SetTotalAgreedValuePremium` (line 7049) sums all five Agreed Value coverages (Basic Group I, II, Broad,
Special, **and Earthquake**).

### Agreed Value Earthquake premium mechanics
`CommercialPropertySpecialClassBusnIncomeAgreedValEarthquakeCoverageRules.Rule.xml`, `SetPremium` (line 101)
— **confirmed byte-shape-identical to plain Business Income's** version:

```
if BlktEQAgreedVal = "Yes" and EQCovIndicator = "Yes, Included in Blanket":
    Premium =
      round(round(round(
        BlktEQAvgRate x round(Factor - 1, 3) x (EQLimitToUse / 100)
      , 0), 0), 0)
      x CyberIncidentExclusionFactorEQ x CyberIncidentExclusionCOLExcptnsFactorBusnIncomeEQToUse

elif AgreedValueOption = "Yes" and EQCovIndicator = "Yes, Not Included in Blanket":
    Premium =
      round(round(round(
        FinalEQRate x round(Factor - 1, 3) x (AgreedValueLimit / 100)
      , 0), 0), 0)
      x CyberIncidentExclusionFactorEQ x CyberIncidentExclusionCOLExcptnsFactorBusnIncomeEQToUse

else:
    Premium = 0.0
```

`Factor` here comes from `LookupAgreedValueFactorBusnIncome` (line 232), matrix **`AgreedValueFactorBusnIncome`
— the identical table name plain Business Income uses**, State|CW + constant `"Y"`. Confirmed a single CW
data row exists: `("CW","Y",1.1)` — `AgreedValueFactorBusnIncome.RateTable.csv`, 2 lines total (1 header, 1
data row). This table is shared between the two coverage groups, not duplicated.

Same `(Factor - 1) x Rate x (Limit/100)` incremental-surcharge shape as plain Business Income — charging only
the extra load for waiving coinsurance, not the full rate.

---

## The shared "Factor" (Basic Group I / II only)

`SetFactor` (line 5824) — confirmed byte-identical logic to plain Business Income's version:

```
Factor = MaxPeriodOfIndemnityFactor        if MaxPeriod = "Yes"
       | MonthlyLimitOfIndemnityFactor     elif MonthlyLimitOfIndemnity <> "Not Applicable"
       | ExtraExpenseFactor                elif CovType = "Extra Expense Only"
       | TypeOfRiskFactor                  otherwise
```

`TypeOfRiskFactor` is built from `LookupBusnIncomeFactor` against matrix **`BusnIncomeFactor`** — **the
identical shared table** plain Business Income reads (keyed State|CW, `CovType`, `TypeOfRisk`,
`CoinsuranceToUse`). Confirmed 131 CW data rows present (`BusnIncomeFactor.RateTable.csv`, 132 lines total).
This table is shared between the plain and Special Class Business Income groups — not duplicated or
Special-Class-specific.

**Corrected 2026-10-06** (`cf-bgi-chains.html`, SCBI review #47, #48; `cf-bgii-chains.html`, SCBI review
#50; probes BI-2 to BI-6 in the Group I notes, BI-4 and BI-6 in the Group II notes). The order is right,
but two blanks zero the `Factor`:

- The monthly test is `MonthlyLimitOfIndemnity <> "Not Applicable"`. A **blank** monthly limit matches it,
  finds no factor, and gives `Factor` 0.0. Group I and Group II both price **$0, outcome "rated"** (BI-4).
- `CovType = "Extra Expense Only"` with a blank limit-on-loss gives `ExtraExpenseFactor` 0.0, and **$0,
  outcome "rated"** (BI-6).

The working branches in OH, Group I: MaxPeriod $81, monthly 1/4 $67, Extra Expense Only $119, type of
risk $39. Neither zero is refused by the engine after 542f0e1.

`CoinsuranceToUse` (`SetCoinsuranceToUse`, line 3447) is built with the identical blanket-scan logic plain
Business Income uses: direct copy of `Coinsurance` when not blanketed, else a `ForEach` scan of
`CommercialPropertyBlanketRatingTable` for the matching `UnitNumber`, else `BlktCoinsurance` directly for
multi-unit-blanket-rated submissions.

---

## Five-way comparison

| | Basic Group I | Basic Group II | Broad | Special | Earthquake |
|---|---|---|---|---|---|
| Chain length | **2 rules** (plain BI: 3) | 4 rules (plain BI: 5) | 2 rules (same as plain BI) | 5 rules (plain BI: 6) | 9 rules (plain BI: 8) |
| Base rate source | **Special Class item's own `BasicGroupIRate`, fully rated** (cross-ref, no local adjustment) | Special Class item's own symbol/terr, own `LookupBasicGroupIIRate` (shared table, **0 CW rows**) | own table, hard-coded `"Frame"` key (`BroadFormBaseRate`, shared table, CW rows present) | own table, hard-coded `"Frame"` + `"Other than Apts/Condos"` key (shared table, CW rows present for that key only) | **Special Class item's own `EQRate`, fully rated** (cross-ref, no local adjustment) |
| BI-specific multiplier | **none** | none | none | none | none (EQFactor applies at final-rate step only) |
| COL adjustment step | yes — `x VandalismExclFactor` only | yes (wind/hail rebuild, no BuildersRisk/StdPropPol factor) | none | yes (theft only) | yes (gate-only: 0 or straight copy) |
| Shared coinsurance `Factor` applied | **yes** | **yes** | **no** | **no** | no (own `EQFactor` instead) |
| Construction dependency | via Special Class item's rate (indirect) | via Special Class item's symbol (indirect) | **none — hard-coded "Frame"** | **none — hard-coded "Frame"** | via Special Class item's rate (indirect) |
| ApartmentCondoIndicator dependency | n/a | n/a | n/a | **neither — BOTH lookups are hard-coded** (base rate to "Other than Apartments and Condominiums", theft factor to "No"). Corrected 2026-09-18, C7-20 | n/a |
| Deductible factor | none | none | none | none | flat-dollar EQ deductible/sub-limit endorsements only |
| Final-rate formula | COLAdj x Factor | COLAdj x Factor | straight copy of `BroadRate` | straight copy of `SpecialCauseOfLossAdjustment` | COLAdj x EQFactor |
| Standalone (non-Agreed-Value) premium coverage file | yes | yes | yes | yes | **no — Agreed Value only** *(Corrected 2026-10-06: wrong; four EQ endorsement record files charge it. `cf-earthquake-chains.html` SCBI #13, #21)* |
| Coverage-on-policy gate | hardcoded `1` | hardcoded `1` | `CauseOfLossToUse = "Broad"` | `CauseOfLossToUse = "Special"` | compound EQCovIndicator/AgreedValueOption/BlktEQAgreedVal test |
| Premium branches | 2 | 2 | 2 | 2 | n/a (Agreed Value: 2 live + otherwise-zero) |

**Corrected 2026-10-06** (`cf-bgi-chains.html` SCBI #44; `cf-bgii-chains.html` SCBI #47, #52; `cf-broad-chains.html`
SCBI #35, #41; `cf-special-chains.html` SCBI #42). Read the table above with these changes. Basic Group I's
base rate is the item's `BasicGroupIRate` = base x LCM, **not** fully rated. Basic Group II's "0 CW rows" is
the normal state-filed pattern; every state files rows. Broad and Special have two live branches plus a
third, "otherwise → 0.0", that catches a blank `IncludedInBlkt`. **Earthquake (corrected 2026-10-06, `cf-earthquake-chains.html`
SCBI #13, #15, #21; probes E-2, E-5, E-7, E-9 to E-15):** the rate is the item's EQ base x LCM, not its finished rate;
`EQFactor` is a copy of the shared `Factor` unless a CP 10 45 / 10 29 record exists; the premium is charged by one
EQ endorsement record, not Agreed Value only.

---

## Structural differences from plain Business Income

1. **Basic Group I and Earthquake borrow the coinsured item's *fully rated* rate, not just its base rate.**
   Plain Business Income reads `../../BasicGroupIBaseRate` and `../../EQBaseRate` (pre-territory/protection-
   class/adjustment-factor values) and reconstructs a parallel formula on top. Special Class Business Income
   reads `../../BasicGroupIRate` and `../../EQRate` — the Special Class item's **already-finished** rates —
   and adds only a single COL-adjustment multiplier (Basic Group I: `VandalismExclFactor`; Earthquake: a
   0-or-copy gate, no multiplier at all). This is a materially tighter cross-coverage dependency: for these
   two forms, Special Class Business Income cannot be rated at all until the Special Class item's own Basic
   Group I / Earthquake rate build-up has fully completed, not merely its base-rate step.
   **Corrected 2026-10-06 for Basic Group I** (`cf-bgi-chains.html`, SCBI review #44, #45, #52; probes BI-7
   to BI-9). `../../BasicGroupIRate` is the item's base x LCM, its third step, not its finished rate. Basic
   Group I needs only that step. It then adds its own vandalism factor and a Business Income `Factor`, not
   "only a single COL multiplier". **Corrected 2026-10-06 for Earthquake too** (`cf-earthquake-chains.html` SCBI #13, #14; probes E-2,
E-5, E-7, E-8): `../../EQRate` is written at the item's second step, base x LCM (0.5 against a finished 0.352).
The item's EQ coinsurance and deductible never reach SCBI; the item's LCM does. SCBI then multiplies the
Business Income `Factor`. Neither form needs the item's finished rate.

2. **Broad and Special key their own base-rate tables on hard-coded literal constants, not data-derived
   values.** Plain Business Income's Broad varies by `ConstructionTypeToUse` and its Special varies by
   `ApartmentCondoIndicator` (via `SpecialIncludingTheftTypeRisk`). Special Class Business Income's Broad
   always hits the `"Frame"` row of the shared `BroadFormBaseRate` table, and its Special always hits the
   `"Other than Apartments and Condominiums"` row of the shared `SpecialFormIncldgTheftTimeElementBaseRate`
   table — regardless of the Special Class item's actual attributes. This mirrors Special Class Building's
   own construction-blind `"Frame"` key on Broad, extending the same pattern to a second dimension
   (apartment/condo classification) that Special Class Building's Broad/Special forms don't have at all.

3. **Fewer COL-adjustment multipliers throughout.** Basic Group I drops `BuildersRiskFactor` and the
   sprinkler-leakage subtraction entirely (plain BI keeps both). Basic Group II drops `BuildersRiskFactor`
   in its no-exclusion branch (plain BI keeps it). Earthquake drops all four of `StoryModFactor`,
   `BuildersRiskFactor`, `EQSprinklerLeakageOnlyBldgFactor` (plain BI applies all three plus the base
   `EQRate`) in favor of a bare gate. Special Class scheduled items apparently carry none of the
   Builders-Risk / sprinkler-leakage / story-mod hazard dimensions that a Structure does — consistent with
   Special Class Building's own COL-adjustment steps being simpler than Building's for the same reasons.

4. **`SetSpecialIncludingTheftTypeRisk` does not exist in this ruleset.** Plain Business Income computes an
   "Apartments and Condominiums" / "Other than Apartments and Condominiums" classification from
   `ApartmentCondoIndicator` and threads it into the Special base-rate lookup key. Special Class Business
   Income has no equivalent rule (confirmed by grep — zero matches for `SpecialIncludingTheftTypeRisk`) and
   instead hard-codes the "Other than Apartments and Condominiums" key directly in
   `LookupSpecialFormIncldgTheftTimeElementBaseRate` — meaning the "Apartments and Condominiums" rows of the
   shared base-rate table are permanently unreachable from this coverage group, even though they're
   reachable from plain Business Income against the exact same table.

5. **No Builders Risk class-code (1150) branch in Special's base-rate step**, and no equivalent anywhere in
   this ruleset — plain Business Income has a dedicated `SpecialFormBldrsRiskTimeElementBaseRate` lookup for
   `ClassCodeToUse = "1150"`; Special Class Business Income's `SetSpecialBaseRate` has no such branch at all.

6. **Basic Group II's base rate is independently looked up (not cross-referenced), but on identically-empty
   tables.** Both `BasicGroupIIRate` and `LowestBasicGroupIIRate` are header-only, zero-data-row tables in
   this package edition — the same gap that affects Building's and plain Business Income's Basic Group II
   base rate (per `BasicGroupI_ERC_Tables.md`'s BUILD-LOG Entry 3 correction). All three coverage groups
   share these two empty tables and are equally unresolvable at CW for Basic Group II absent a state filing.
   **Corrected 2026-10-06** (`cf-bgii-chains.html`, SCBI review #52): out of date. This is the normal
   state-filed pattern. Every state files rows; OH rates this record at $321 / $361.

7. **Everything else — master orchestration, `SetFactor`, `SetFinalRates`, premium-file shapes, rounding,
   the Agreed Value asymmetry for Earthquake, the two-branch-only premium pattern, and the lack of a
   Multi-Premium-and-Dispersion-Credit multiplier in coverage-level premium — is structurally identical to
   plain Business Income**, not merely similar. Where this document doesn't call out a difference above, the
   plain-Business-Income doc's description applies verbatim (same rule names, same shapes, different parent
   record).

## Structural differences from Special Class Building

1. **Special Class Business Income is income-based** — Limit is a percentage-of-value-style dollar limit on
   lost income/extra expense, not a building value; the premium formula multiplies `Limit / 100` directly by
   the final rate, matching plain Business Income's mechanics rather than Special Class Building's.

2. **No LOI factor — but for a different structural reason than Special Class Building's.** Special Class
   Building has no LOI factor anywhere in its four core forms (confirmed by the earlier pass: zero
   `LOIFactor` rule-name matches). Special Class Business Income also has no LOI factor — but this is simply
   the **plain-Business-Income-wide** absence of an LOI concept (documented in the plain BI doc's
   "Structural differences" point 4), not a Special-Class-specific trait. Both groups converge on "no LOI"
   independently, for unrelated reasons.

3. **No independent `ClassDescription`-keyed base-rate lookup for Basic Group I.** Special Class Building's
   defining trait is that its Basic Group I base rate is looked up by `SpecialClassDescConvertedOption`
   (itself derived from the free-text `ClassDescription`) crossed with `ProtectionClassToUse` — no
   construction key at all, but a real class-specific lookup. Special Class Business Income's Basic Group I
   has **no lookup of its own whatsoever** — it borrows the Special Class item's fully-computed rate wholesale
   (see point 1 above). Where Special Class Building rates *independently* by named class, Special Class
   Business Income rates *derivatively* from whatever Special Class Building already computed. This is the
   answer to this pass's central question: **Special Class Business Income does not replicate Special Class
   Building's "rate by ClassDescription" pattern for Basic Group I or Earthquake — it borrows the
   already-rated result, the same cross-coverage-dependency shape plain Business Income has on plain
   Building.** Only Broad and Special retain independent base-rate tables, and even those are keyed on
   hard-coded literal constants rather than on `ClassDescription` or any class-specific option code.
   **Corrected 2026-10-06** (`cf-bgi-chains.html`, SCBI review #44): for Basic Group I the borrowed value
   is the item's base x LCM (0.07 in the golden case), not its finished rate (0.066).

4. **Two premium branches for a different reason than Special Class Building's two branches.** Special Class
   Building has two branches because it has no `CovType` taxonomy. Special Class Business Income has two
   branches because Business Income coverage never carries a `CovType` taxonomy with Legal Liability /
   Leasehold Interest regardless of parent — see point 4 under "differences from plain Business Income"
   above.

5. **Earthquake is present in both, but sourced differently.** Special Class Building computes its own native
   `EQRate` inside `CommercialPropertySpecialClassRules.Rule.xml` (`SetEQRatesAndFactors`, per the earlier
   pass, out of scope there). Special Class Business Income does not recompute anything — it copies that
   already-computed `EQRate` wholesale (`../../EQRate`). The Earthquake "chain" in Special Class Business
   Income is nine rules long only because of the sub-limit-percent/coinsurance/type-of-risk-combination
   machinery that has no bearing on the base rate itself; strip that away and the actual rate-borrowing logic
   is a two-line copy-then-gate.
   **Corrected 2026-10-06** (`cf-earthquake-chains.html` SCBI #13, #16, #17; probes E-2, E-9 to E-15, E-41). The copied `EQRate` is
   the item's base x LCM, not its finished rate. It is then multiplied by `EQFactor`, a copy of the shared
   Business Income `Factor` (coinsurance, cover type, type of risk, max period and monthly limit all move it,
   $2,500 to $8,500), and the endorsement record multiplies the limit and two cyber factors. Not a copy-then-gate.

---

## Open questions

- ~~**`SpecialFormIncldgTheftTimeElementBaseRate`'s hard-coded "Other than Apartments and Condominiums"
  key** ... even when a theft-exclusion factor lookup two steps earlier still varies by
  `ApartmentCondoIndicator`~~ — **ANSWERED and half WRONG, 2026-09-18 by chunk 7 task C7-20.**
  The base-rate pin is real: the "Apartments and Condominiums" rows (0.029 / 0.016) are unreachable from
  this coverage group, and the literals census confirms the pin applies *"from the pinned site only — the
  same column is also read live elsewhere"*, which is plain Business Income reading the same physical table.
  **But the theft-exclusion factor does NOT still vary by `ApartmentCondoIndicator`.**
  `LookupSpecialTheftExclusionFactor` keys that column on a hard-coded `"No"`, so
  `SpecialLeaseHoldTimeElementTheftExclusionFactor`'s `Yes` row (0.96) is unreachable too. **Both
  dimensions are dead, not one** — proven by running it: moving the indicator on the record, and the parent's
  class code to an apartments class, moves neither the theft factor (0.86 throughout) nor the base rate
  (0.047 throughout). There is no authoring inconsistency here to explain; the apartment concept is switched
  off in this group at **both** sites. See `docs/CF-CHUNK7-PER-FORM.md`.
- **ANSWERED 2026-09-18 (C7-20/C7-28):** the table files exactly two countrywide rows — `Yes` 0.96 and
  `No` 0.86 — and this group can reach only the `No` row. ~~**`SpecialLeaseHoldTimeElementTheftExclusionFactor`
  CW values (0.96 / 0.86) were not cross-checked against the value(s) the plain Business Income pass would
  read from the same-named table**~~ — the plain-BI doc notes
  "3 total lines including header: 2 data rows" for this table without quoting the values. If the plain-BI
  and Special-Class-BI passes are reading the exact same physical CSV file (same table name, same directory),
  the values should match; this was not independently re-verified against the plain-BI doc's own source read.
- **`BasicGroupIIRate` and `LowestBasicGroupIIRate` are header-only (zero CW data rows)** — Basic Group II
  base rate is unresolvable at the countrywide level for this coverage group (as it is for Building and plain
  Business Income). Any rater built off this document needs a state-specific override for Basic Group II to
  produce a nonzero rate. **ANSWERED 2026-10-06** (`cf-bgii-chains.html`, SCBI review #52, #55): every
  state files these rows (OH 8 each), so this is the normal pattern, not an open gap. OH prices $321 / $361.
- **`CommercialPropertySpecialClassBusnIncomeInterruptionOfComputerOperationsCoverageRules.Rule.xml` and
  `...WatercraftExclusionBuybackCoverageRules.Rule.xml`** were confirmed to exist by directory listing but not
  traced — endorsement add-ons layered on top of the core rate chains, out of scope for this pass, same as
  the Agreed Value / Inflation Guard endorsements the Special Class Building pass excluded.
- **`CommercialPropertySpecialClassBusnIncomeCoverageRules.Rule.xml`** (the coverage-record dispatch/attach
  file, distinct from the master rate-chain file) was not opened in this pass — it likely mirrors
  `CommercialPropertyBusinessIncomeCoverageRules.Rule.xml`'s role but this was not verified.

---

## Quick reference — end-to-end, Basic Group I (scheduled)

```
BasicGroupIRate = SpecialClassItem.BasicGroupIRate                      (direct cross-coverage copy)
                  = item r3(Base x LCM), before the item's vandalism, coinsurance, deductible
                  (corrected 2026-10-06, cf-bgi-chains.html SCBI #44; a submitted value is kept)

COLAdj = BasicGroupIRate x VandalismExclFactor

Factor = MaxPeriodOfIndemnityFactor | MonthlyLimitOfIndemnityFactor | ExtraExpenseFactor | TypeOfRiskFactor
         (TypeOfRiskFactor = lookup BusnIncomeFactor(State|CW, CovType, TypeOfRisk, CoinsuranceToUse))

FinalBasicGroupIRate = COLAdj x Factor

Premium = round(round(IRPM x PackageMod x FinalBasicGroupIRate x (Limit/100), 0), 0)
          x CyberExclFactorBGI x CyberExclCOLExcptnsFactorBusnIncomeBGIToUse
          (only when IncludedInBlkt = "No"; blank goes to the blanket side and prices $0 —
           corrected 2026-10-06, cf-bgi-chains.html SCBI #46)
```

## Quick reference — end-to-end, Basic Group II (scheduled)

```
BasicGroupIIBaseRate = lookup BasicGroupIIRate(State|CW, BasicGroupIIRatingTerr, BasicGroupIISymbol, "Bldg")
                        [CW: table header-only, 0 data rows — unresolvable without state filing]
                        [corrected 2026-10-06: every state files rows; normal pattern, not a gap]

BasicGroupIIRate = BasicGroupIIBaseRate x LossCostMultiplier x SpecialClassItem.BasicGroupIINumericValue
                   (LCM is this record's own, the item's only when blank; the item's numeric value is
                    1.0 when the item has a wind/hail exclusion — corrected 2026-10-06, cf-bgii-chains.html SCBI #48, #49)

COLAdj = BasicGroupIIRate                                        if no wind/hail exclusion
       | LowestBasicGroupIIBaseRate x LossCostMultiplier x WindstormOrHailExclFactor   otherwise

FinalBasicGroupIIRate = COLAdj x Factor

Premium = round(round(IRPM x PackageMod x FinalBasicGroupIIRate x (Limit/100), 0), 0)
          x CyberExclFactorBGII x CyberExclCOLExcptnsFactorBusnIncomeBGIIToUse
```

## Quick reference — end-to-end, Broad (scheduled)

```
BroadBaseRate = lookup BroadFormBaseRate(State|CW, "Frame",
                    "Business Income Without Extra Expense" | "All Other")     if COL = Broad     [CW 0.011 / 0.023]
              | 0.0                                                            otherwise

BroadRate = BroadBaseRate x LossCostMultiplier
FinalBroadRate = BroadRate                       (straight copy — no COL adjustment, no Factor)

Premium = round(round(IRPM x PackageMod x FinalBroadRate x (Limit/100), 0), 0)
          x CyberExclFactorBroad x CyberExclCOLExcptnsFactorBusnIncomeBroadToUse
          ("No" only; a blank IncludedInBlkt goes straight to 0.0 — corrected 2026-10-06)
```

## Quick reference — end-to-end, Special (scheduled)

```
SpecialTheftExclusionFactor = lookup SpecialLeaseHoldTimeElementTheftExclusionFactor(State|CW, ApartmentCondoIndicator)
                               if theft excluded, else 1.0                                [CW 0.96 / 0.86]
                               (corrected 2026-10-06, cf-special-chains.html SCBI: the key is a constant
                                "No", so always 0.86; C7-20)

SpecialBaseRate = lookup SpecialFormIncldgTheftTimeElementBaseRate(
                       State|CW, "Frame", CovType, "Other than Apartments and Condominiums")   [CW 0.033 / 0.047 — always this key]

SpecialRate = SpecialBaseRate x LossCostMultiplier
SpecialCauseOfLossAdjustment = SpecialRate x SpecialTheftExclusionFactor
FinalSpecialRate = SpecialCauseOfLossAdjustment      (straight copy — no Factor)

Premium = round(round(IRPM x PackageMod x FinalSpecialRate x (Limit/100), 0), 0)
          x CyberExclFactorSpecial x CyberExclCOLExcptnsFactorBusnIncomeSpecialToUse
          ("No" only; a blank IncludedInBlkt goes straight to 0.0 — corrected 2026-10-06)
```

## Quick reference — end-to-end, Earthquake (Agreed Value, not-in-blanket)

```
EQRate = SpecialClassItem.EQRate                                        (direct cross-coverage copy)

EQCauseOfLossAdjustment = 0.0    if EQCovIndicator in (Not Applicable, No Coverage)
                         | EQRate  otherwise

FinalEQRate = EQCauseOfLossAdjustment x EQFactor

AgreedValueFactor = lookup AgreedValueFactorBusnIncome(State|CW, "Y")     [CW 1.1]

Premium = round(round(round(FinalEQRate x round(AgreedValueFactor - 1, 3) x (AgreedValueLimit/100), 0), 0), 0)
          x CyberExclFactorEQ x CyberExclCOLExcptnsFactorBusnIncomeEQToUse

(non-Agreed-Value, non-blanket scheduled Earthquake premium: no coverage file exists for this case)
```

**Corrected 2026-10-06** (`cf-earthquake-chains.html` SCBI #13, #20, #21; probes E-29, E-30, E-38, E-41). Four EQ endorsement records
charge the scheduled premium: r0(r0(r0(FinalEQRate x SCBI Limit/100) x CyberEQ) x CyberCOL), or the sub-limit for
CP 10 45 / 10 29. A record attaches only when SCBI's own `EQCovIndicator` is "Yes, ..." and the location's form names
it; the item need not elect earthquake. Agreed Value: CW 1.1 gives $280 on 10,000; a blank limit gives $0 "rated";
it also charges on top of a sub-limit form ($340).

---
