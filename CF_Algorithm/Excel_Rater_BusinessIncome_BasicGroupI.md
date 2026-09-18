# Excel Rater Build Guide — Business Income, Basic Group I

**Written:** 2026-09-02.

**Source material:** `CauseOfLoss_BusinessIncome_RatingAlgorithms.md` §"Basic Group I — rate build-up" /
§"Basic Group I — premium" + `BusinessIncome_ERC_Tables.md`, cross-checked against `CFCW20260601V01`.
See `Excel_Rater_BusinessIncome_Overview.md` for the shared Business Income shell this document builds
on top of, and `Excel_Rater_BasicGroupI.md` for the Building form whose already-computed rate this one
depends on.

---

## 1. What makes this form different from Building's Basic Group I

The single most important fact: **this form does not compute its own base rate.** It reads
`Calc_Building_BGI.BaseRate` — two datadef levels up from the Business Income record, resolving to the
same value Building's own `SetBasicGroupIBaseRate` rule computes for the Building coverage on the same
structure. Rate the Building first; this tab is arithmetically downstream of it.

| | Building's Basic Group I | Business Income's Basic Group I |
|---|---|---|
| Chain length | 8 steps | **3 steps** |
| Base rate | own class/construction lookup | **cross-reference to `Calc_Building_BGI.BaseRate`** |
| Extra multiplier on the rate | none | `BGIBaseRateAdjustmentFactor` (header-only CW table — see §3) |
| COL adjustment | sprinkler/vandalism/`StdPropPolGroupIFactor` | sprinkler/vandalism/**`BuildersRiskFactor`** — the "standard property policy" concept doesn't exist for Business Income |
| Coinsurance/LOI/deductible | three separate steps | **collapsed into the single shared `Factor`** (Basic Group I/II only — see `Excel_Rater_BusinessIncome_Overview.md` §5); no LOI factor, no deductible factor at all |
| Coverage-on-policy gate | tests `CauseOfLossToUse` | **hardcoded `1`** — always computed, no gate |
| Premium branches | scheduled / Legal Liability / blanket / otherwise-zero (4) | **scheduled / blanket only (2)** |
| `MultiPremiumAndDispersionCreditFactor` in premium | yes | **no** — populated during shared prep, never multiplied in |

---

## 2. `Locations_Buildings` — nothing new for this form specifically

This form reads only what `Excel_Rater_BusinessIncome_Overview.md` §3 already defines
(`BI_CovType`, `BI_TypeOfRisk`, `BI_MaxPeriod`, `BI_MonthlyLimitOfIndemnity`, `BI_Coinsurance`,
`BI_Limit`, `BI_IncludedInBlkt`, `BI_BldgIncludedInOperationalUnit`) plus the shared `ClassCode`,
`SubStdConditionRate`/`VacantBuildingRate` inputs already on the tab from Basic Group I Building, and —
critically — **`Calc_Building_BGI.BaseRate`** from a tab this workbook already has.

## 3. `Rate_Tables` — one new table for this form

| Table | Keys | CW rows filed? |
|---|---|---|
| `BaseRateAdjustmentFactor` | State\|CW, `"Basic Group I"` | **No — header-only, confirmed empty** |

Combined with `BasicGroupIRate` also being header-only (the table `Calc_Building_BGI.BaseRate` itself
depends on — see `Excel_Rater_BasicGroupI.md` §3), this form is **doubly unresolvable** at CW level: two
independent empty tables, not one. A state filing has to cover both before this rate produces anything.

---

## 4. `Calc_BusinessIncome_BGI` tab — one row per building

Straight translation of `SetBGIRatesAndFactors`'s 3-step chain, plus the shared `Factor` finalization.

1. **`BGIBaseRateAdjustmentFactor`** = `Lookup(BaseRateAdjustmentFactor: State|CW, "Basic Group I")`
2. **`Rate`**:
   ```
   if BI_MaxPeriod = "Y" or BI_MonthlyLimitOfIndemnity <> "Not Applicable" or BI_CovType = "Extra Expense Only",
      and BI_BldgIncludedInOperationalUnit = "Y":
       HighestBusnIncomeBasicGroupIBaseRate × BGIBaseRateAdjustmentFactor    [blanket/multi-unit aggregate — not built this pass]
   elif RatingType = "Class":
       ((Calc_Building_BGI.BaseRate × LCM) + SubStdConditionRate + VacantBuildingRate)
         × BasicGroupIRatingTerrFactor × ProtectionClassFactor × BGIBaseRateAdjustmentFactor
   elif RatingType in ("Specific","Tentative"):
       SpecificGroupIRate × LCM × SprinklerLeakageNotExcludedFactor × BGIBaseRateAdjustmentFactor
   ```
   round to 3dp. Note this is Building's own class-rated Basic Group I rate formula with one extra
   multiplier tacked on — same addends, same territory/protection-class factors, sourced from the same
   `Locations_Buildings` columns Building's own tab already reads.
3. **`COLAdj`** = `ROUND(Rate − SprinklerLeakageExclNonSprinkleredRate, 3) × SprinklerLeakageExclSprinkleredFactor × VandalismExclFactor × BuildersRiskFactor`
   — round to 3dp, **no null-guard, always recomputes** (unlike Building's version, which has one).
   **Note, 2026-09-04:** Business Income is a separate ERC datadef group from Structure — its own
   `SprinklerLeakageExclNonSprinkleredRate` is already the LCM-scaled value (computed from a separate
   raw datadef, `SprinklerLeakageExclNonSprinkleredBaseRate × LossCostMultiplier`); this file's
   original naming was correct. Structure's own datadef group names the equivalent concept
   `SprinklerLeakageExclNonSprinkleredBldgRate` instead — don't cross-apply that naming here. At
   LCM = 1.0 either way, the filed CW rate (0.0006) rounds up to 0.001, a ~67% jump — see
   `Excel_Rater_BasicGroupI.md`'s correction section for the full writeup on that rounding behavior.
4. **`Factor`** — the shared helper from `Excel_Rater_BusinessIncome_Overview.md` §5; reused, not
   recomputed here if already built as a shared column. Its "otherwise" branch (plain, non-blanket
   `BI_TypeOfRisk`) is not a single uniform `BusnIncomeFactor` lookup — two more branches sit inside it,
   both traced and filed, not left out. See §9.
5. **`FinalRate`** = `COLAdj × Factor`. **Nothing else** — no coinsurance factor, no LOI factor, no
   deductible factor of any kind. This is the entire final-rate step.

---

## 5. `Premium_Summary` formula for this form

```
BI_BGI_Premium =
    if BI_IncludedInBlkt = "No":
        ROUND(ROUND(IRPMFactor × PackageModFactor × Calc_BusinessIncome_BGI.FinalRate × (BI_Limit/100), 0), 0)
          × CyberIncidentExclusionFactorBGI × CyberIncidentExclusionCOLExcptnsFactorBusnIncomeBGIToUse
    elif BI_IncludedInBlkt = "Yes" and BlktTotalFullValueAmount > 0:
        ROUND(ROUND(IRPMFactor × PackageModFactor × BlktBasicGroupIAvgRate
              × (FullBusnIncomeValue/BlktTotalFullValueAmount) × (BlktLimit/100), 0), 0)
          × CyberIncidentExclusionFactorBGI × CyberIncidentExclusionCOLExcptnsFactorBusnIncomeBGIToUse
        [not built this pass — see §7]
    else:
        0.0
```

There is no gate on coverage type or cause of loss the way Building's Basic Group I premium has — this
branch always fires as long as the coverage isn't blanketed, since `SetCoverageOnPolicyIndicator` is a
hardcoded `1` in ISO's own rule.

---

## 6. Inputs → rating output — the full picture

### 6.1 What feeds the loss cost

| Stage | Reads from | Produces | Tab |
|---|---|---|---|
| 0 — the loss cost, borrowed | `Calc_Building_BGI.BaseRate` | *(not recomputed — cross-referenced)* | `Calc_Building_BGI` → `Calc_BusinessIncome_BGI` |
| 1 — the Business-Income-specific adjustment | `Rate_Tables.BaseRateAdjustmentFactor` | `BGIBaseRateAdjustmentFactor` | `Calc_BusinessIncome_BGI` |
| 2 — turn it into a rate | Building's `BaseRate`, `LCM`, `SubStdConditionRate`, `VacantBuildingRate`, `BasicGroupIRatingTerrFactor`, `ProtectionClassFactor`, `BGIBaseRateAdjustmentFactor` | `Rate` | `Calc_BusinessIncome_BGI` |
| 3 — adjust for sprinkler/vandalism/Builders-Risk | `Rate`, sprinkler and vandalism factors, `BuildersRiskFactor` | `COLAdj` | `Calc_BusinessIncome_BGI` |
| 4 — apply the shared coinsurance/type-of-risk `Factor` | `COLAdj`, `Factor` (§4 of the overview) | `FinalRate` | `Calc_BusinessIncome_BGI` |
| 5 — turn the rate into a dollar premium | `FinalRate`, `BI_Limit`, `IRPMFactor`, `PackageModFactor` | `BI_BGI_Premium` | `Premium_Summary` |

No coinsurance-factor stage, no LOI-factor stage, no deductible stage — stage 4 does the entire job those
three separate Building stages do, and only for this and one other form.

### 6.2 Full formula with if/then

```
BGIBaseRateAdjustmentFactor = Lookup(BaseRateAdjustmentFactor: State|CW, "Basic Group I")

Rate =
    if (BI_MaxPeriod = "Y" or BI_MonthlyLimitOfIndemnity <> "Not Applicable" or BI_CovType = "Extra Expense Only")
       and BI_BldgIncludedInOperationalUnit = "Y":
        HighestBusnIncomeBasicGroupIBaseRate × BGIBaseRateAdjustmentFactor     [not built this pass]
    elif RatingType = "Class":
        ((Calc_Building_BGI.BaseRate × LCM) + SubStdConditionRate + VacantBuildingRate)
          × BasicGroupIRatingTerrFactor × ProtectionClassFactor × BGIBaseRateAdjustmentFactor
    elif RatingType in ("Specific","Tentative"):
        SpecificGroupIRate × LCM × SprinklerLeakageNotExcludedFactor × BGIBaseRateAdjustmentFactor
    (round to 3dp)

COLAdj = ROUND(Rate - SprinklerLeakageExclNonSprinkleredRate, 3)
           × SprinklerLeakageExclSprinkleredFactor × VandalismExclFactor × BuildersRiskFactor
    (round to 3dp; always recomputes, no null-guard)

Factor = MaxPeriodOfIndemnityFactor    if BI_MaxPeriod = "Y"
       | MonthlyLimitOfIndemnityFactor elif BI_MonthlyLimitOfIndemnity <> "Not Applicable"
       | ExtraExpenseFactor            elif BI_CovType = "Extra Expense Only"
       | <blended TypeOfRiskFactor>    elif BI_TypeOfRisk is one of the four "Combined..." values (§9.1)
       | TuitionAndFeesFactor ×
         ChangesEducationalInstitutionsExtensionOfRecoveryFactor
                                        elif BI_TypeOfRisk = "Educational Institutions" (§9.2)
       | Lookup(BusnIncomeFactor: CoinsuranceToUse, BI_CovType, BI_TypeOfRisk)   otherwise

FinalRate = COLAdj × Factor

BI_BGI_Premium =
    if BI_IncludedInBlkt = "No":
        ROUND(ROUND(IRPM × PackageMod × FinalRate × (BI_Limit/100), 0), 0)
          × CyberExclFactorBGI × CyberExclCOLExcptnsFactorBusnIncomeBGIToUse
    elif BI_IncludedInBlkt = "Yes" and BlktTotalFullValueAmount > 0:
        [blanket branch — not built this pass, see §7]
    else: 0.0
```

---

## 7. What's deliberately left out of this pass

- The blanket/max-period/multi-unit base-rate branch (step 2 of §4) — needs
  `HighestBusnIncomeBasicGroupIBaseRate`, a multi-unit aggregate not traced in the source doc
- The blanket premium branch — needs `BlktBasicGroupIAvgRate`, `FullBusnIncomeValue`,
  `BlktTotalFullValueAmount`
- `CoinsuranceToUse`'s real blanket-rating-table scan — this pass enters it directly as a simplification
  (`Excel_Rater_BusinessIncome_Overview.md` §5)

Specific/Tentative rating is **not** left out — see §8. The `"Combined..."` `TypeOfRisk` blended-factor
branch is **not** left out either, and neither is plain `"Educational Institutions"`'s own factor path —
both traced and confirmed filed, no missing tables. See §9.

---

## 8. The Specific/Tentative rating path

Same `RatingType` branch as Building's own Basic Group I (`Excel_Rater_BasicGroupI.md` §9), transplanted
onto Business Income's borrowed-rate shape. **Confirmed present in the source doc's own Basic Group I
formula** (the "Specific or Tentative rated" branch appears immediately after the Class-rated branch in
`CauseOfLoss_BusinessIncome_RatingAlgorithms.md`), with Business Income's usual extra
`BGIBaseRateAdjustmentFactor` multiplier tacked on — the same pattern the Class-rated branch already
carries.

```
Rate =
    ... [blanket/max-period branch, not built this pass] ...
    elif RatingType = "Class":
        <the Class-rated formula already built in §4>
    elif RatingType in ("Specific","Tentative"):
        SpecificGroupIRate × LCM × SprinklerLeakageNotExcludedFactor × BGIBaseRateAdjustmentFactor
```

**Note what this branch does *not* read: `Calc_Building_BGI.BaseRate`.** Basic Group I's defining trait —
borrowing the Building's own computed rate — only applies to the Class-rated path. Under Specific/
Tentative rating, Business Income (like Building) substitutes the same `SpecificGroupIRate` input
directly; there is no cross-tab dependency for this branch. Everything downstream — `COLAdj`, `Factor`,
`FinalRate`, the premium formula — is unchanged.

**`SpecificGroupIRate` carries the same open question here as it does under Building.** No `Set` or
`Lookup` rule populates it anywhere in the Business Income rating-algorithm doc either — see
`Excel_Rater_BasicGroupI.md` §9 for the full discussion; the likely-but-unconfirmed answer is a user- or
schedule-entered value. Build a `BI_SpecificGroupIRate` column on `Locations_Buildings` with the same
open-question comment, separate from Building's and Contents' own `SpecificGroupIRate` columns — there's
no reason to assume all three would carry the same value for the same building.

The `SprinklerLeakageNotExcludedFactor` table this branch reads is the same one Building's own Basic
Group I chain reads (per `Excel_Rater_BasicGroupI.md` §9) — no separate Business-Income instance was
found in the source doc, and no new `Rate_Tables` block is needed for this form.

## 9. The Combined Type of Risk / plain Educational Institutions paths — traced, not left out

Confirmed 2026-09-11 by reading `SetTypeOfRiskFactor` (line 5000), `SetTypeRiskCombination1Factor` (line
4588), and `SetTypeRiskCombination2Factor` directly in `CommercialPropertyBusinessIncomeRules.Rule.xml`:
the `"Combined..."` `BI_TypeOfRisk` values §7 originally flagged as unsupported are fully filed and
traceable — no missing table, just a second branch layered on top of the one already built. Tracing it
also surfaced a correction to §4/§6: plain `"Educational Institutions"` (not a Combined value) *also*
bypasses `BusnIncomeFactor` entirely, which neither section previously called out.

### 9.1 The four Combined values

`BI_TypeOfRisk` supports four `"Combined..."` values. Each blends two separate lookups by a pair of
user-entered percentages rather than doing one `BusnIncomeFactor` lookup:

| `BI_TypeOfRisk` value | Component 1 | Component 2 |
|---|---|---|
| Combined Manufacturing and Mercantile Operations | Manufacturing | Mercantile and Non-manufacturing |
| Combined Manufacturing and Rental Operations | Manufacturing | Rental Properties |
| Combined Mercantile and Rental Operations | Mercantile and Non-manufacturing | Rental Properties |
| Combined Educational Institutes and Rental Operations | Educational Institutions (via `TuitionAndFeesFactor`, **not** `BusnIncomeFactor` — see 9.2) | Rental Properties |

Two new user-entered percentage inputs per combo — `CombinedTypeOfRiskManufacturingPct`,
`CombinedTypeOfRiskMercantilePct`, `CombinedTypeOfRiskRentalPct`, `CombinedTypeOfRiskEducationalPct` (one
field per component, not derived as each other's complement). Each is range-validated 1–99 against a
confirmed-filed CW domain table (`DomainCombinedTypeOfRisk{Component}Pct`) — build as user-entered
columns with that same range check; there's no enforcement anywhere in the rule that the two percentages
for a given combo sum to 100.

```
TypeRiskCombination1Factor = Lookup(BusnIncomeFactor: CoinsuranceToUse, CovType, <Component 1>)
    [Educational component uses LookupTuitionAndFeesFactor instead — see 9.2, no CoinsuranceToUse/CovType key]
TypeRiskCombination2Factor = Lookup(BusnIncomeFactor: CoinsuranceToUse, CovType, <Component 2>)

TypeOfRiskFactor =
    ROUND(
      ROUND( (CombinedTypeOfRisk<Component1>Pct / 100) × TypeRiskCombination1Factor, 3)
      + (CombinedTypeOfRisk<Component2>Pct / 100) × TypeRiskCombination2Factor
    , 3)

Factor = TypeOfRiskFactor   [Copy, confirmed line 6943]
```

No new rate table — this reuses `BusnIncomeFactor` entirely (same table §3 already lists, 131 CW rows),
just called twice per combo and blended. Both `TypeRiskCombination1Factor` and `2Factor` are populated by
their own `Set*` rules (`SetTypeRiskCombination1Factor` / `2Factor`), not inline in `SetTypeOfRiskFactor` —
build as two intermediate columns, not one combined formula.

### 9.2 Plain "Educational Institutions" — a correction to §4/§6

Confirmed: plain `BI_TypeOfRisk = "Educational Institutions"` (not a Combined value) does **not** go
through `BusnIncomeFactor` at all, contrary to how §4 step 4 and §6.2's pseudocode previously described
the "otherwise" branch as a single uniform `Lookup(BusnIncomeFactor: ...)`. Its own branch inside
`SetTypeOfRiskFactor`:

```
TypeOfRiskFactor = TuitionAndFeesFactor × ChangesEducationalInstitutionsExtensionOfRecoveryFactor
```

Both tables already confirmed filed and already listed in §3 (`TuitionAndFeesFactor`, 16 CW rows;
`BusnIncomeEducationalInstitutionsExtOfRecoveryFactor`, 13 CW rows) — no new table needed, just a
different formula shape than the rest of the "otherwise" branch.

**Note the asymmetry with 9.1's Combined-Educational branch:** the Educational half of "Combined
Educational Institutes and Rental Operations" uses *only* `TuitionAndFeesFactor` — it does **not** also
multiply by `ChangesEducationalInstitutionsExtensionOfRecoveryFactor`. Confirmed by reading
`SetTypeRiskCombination1Factor`'s Educational branch directly (calls `LookupTuitionAndFeesFactor` alone).
That's a genuine divergence between the plain and Combined Educational paths, not an oversight to fix —
build them as two different formulas, not one shared helper.

### 9.3 Step 4 / §6.2, corrected reading

`Factor`'s "otherwise" territory is six branches deep, not one:

1. `BI_MaxPeriod = "Y"` → `MaxPeriodOfIndemnityFactor`
2. `BI_MonthlyLimitOfIndemnity <> "Not Applicable"` → `MonthlyLimitOfIndemnityFactor`
3. `BI_CovType = "Extra Expense Only"` → `ExtraExpenseFactor`
4. `BI_TypeOfRisk` is one of the four `"Combined..."` values → blended `TypeOfRiskFactor` (§9.1)
5. `BI_TypeOfRisk = "Educational Institutions"` → `TuitionAndFeesFactor ×
   ChangesEducationalInstitutionsExtensionOfRecoveryFactor` (§9.2)
6. otherwise → `Lookup(BusnIncomeFactor: CoinsuranceToUse, BI_CovType, BI_TypeOfRisk)`

## Remaining steps

1. You review this document against `Excel_Rater_BasicGroupI.md` — confirm the cross-tab dependency on
   `Calc_Building_BGI.BaseRate` reads clearly as "the same value, borrowed" rather than a new lookup,
   and that §8 reads clearly as the one branch where that dependency doesn't apply.
2. §9 (added 2026-09-11) traced the Combined Type of Risk / plain Educational Institutions paths that
   §7 previously flagged as unsupported — confirm nothing else in §7's remaining out-of-scope list
   deserves the same re-check before Basic Group II reuses this doc as its template.
3. Next is Basic Group II, Broad, and Special for this coverage, or your call on what comes after.
4. Nothing gets built until you say go.
