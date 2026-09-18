# Excel Rater Build Guide — Business Income, Basic Group II

**Written:** 2026-09-02.

**Source material:** `CauseOfLoss_BusinessIncome_RatingAlgorithms.md` §"Basic Group II — differences" /
§"Basic Group II — premium" + `BusinessIncome_ERC_Tables.md`, cross-checked against `CFCW20260601V01`.
See `Excel_Rater_BusinessIncome_Overview.md` for the shared shell and `Excel_Rater_BusinessIncome_
BasicGroupI.md` for the sibling form this one is compared against, and `Excel_Rater_BasicGroupII.md` for
the Building form this one depends on.

---

## 1. What changes moving from Basic Group I to Basic Group II

Same relationship as Building's own Basic Group I → II jump, transplanted onto Business Income's simpler
shape: rated off **territory + construction symbol** instead of class + construction code, with a second
"lowest rate" fallback path for the wind/hail-excluded branch. The key difference from Building's version
of this jump: **Business Income's Basic Group II still doesn't compute its own base rate.** It reads
`Calc_Building_BGII`'s already-resolved symbol and territory, and queries the **same `BasicGroupIIRate`
table** Building's own tab reads — this is the one Business Income form where the cross-coverage
dependency is a shared table lookup, not just a borrowed scalar.

| | Business Income Basic Group I | Business Income Basic Group II |
|---|---|---|
| Chain length | 3 steps | **5 steps** |
| Rate source | cross-reference to `Calc_Building_BGI.BaseRate` (a value) | **own `Lookup` into `BasicGroupIIRate`**, keyed on `Calc_Building_BGII`'s resolved symbol/territory (a lookup, not a value copy) |
| Second rate path | none | `LowestBasicGroupIIBaseRate` — wind/hail-excluded floor, same concept as Building's |
| Occupancy hazard load | n/a | `BasicGroupIINumericValue`, read from the Structure (Business Income doesn't recompute this either) |
| BI-specific multiplier | `BGIBaseRateAdjustmentFactor` | `BGIIBaseRateAdjustmentFactor` — same mechanism, `"Basic Group II"` key |
| COL adjustment gate | sprinkler/vandalism | wind/hail-exclusion record present or not |
| Premium file | — | **byte-shape-identical** to Basic Group I's, only datadef names swapped — same relationship Building's own Group I/II premium files have |

---

## 2. `Locations_Buildings` — nothing new for this form specifically

Reuses everything `Excel_Rater_BusinessIncome_Overview.md` §3 and `Excel_Rater_BusinessIncome_
BasicGroupI.md` §2 already define, plus **`Calc_Building_BGII.ConstructionSymbol`** and
**`Locations_Buildings.BasicGroupIIRatingTerr`** — both already on the workbook from
`Excel_Rater_BasicGroupII.md`. No new columns.

## 3. `Rate_Tables` — one new table for this form, reusing two

| Table | Keys | CW rows filed? |
|---|---|---|
| `BaseRateAdjustmentFactor` | State\|CW, `"Basic Group II"` | **No — header-only** (same table as Basic Group I, different key) |
| `BasicGroupIIRate` | State\|CW, `BasicGroupIIRatingTerr`, `ConstructionSymbol`, `"Bldg"` | **No — header-only** — reused from `Excel_Rater_BasicGroupII.md` §3, same table Building's own tab reads |
| `LowestBasicGroupIIRate` | State\|CW, `ConstructionSymbol`, `"Bldg"` | **No — header-only** — reused, same table |

**Three independent empty tables feed this form** — worse than Basic Group I's two. A state filing would
need to cover `BaseRateAdjustmentFactor` *and* both `BasicGroupIIRate` tables before this rate resolves.

---

## 4. `Calc_BusinessIncome_BGII` tab — one row per building

Straight translation of `SetBGIIRatesAndFactors`'s 5-step chain.

1. **`BaseRate`**:
   ```
   if (BI_MaxPeriod = "Y" or BI_MonthlyLimitOfIndemnity <> "Not Applicable" or BI_CovType = "Extra Expense Only")
      and BI_BldgIncludedInOperationalUnit = "Y":
       HighestBusnIncomeBasicGroupIIBaseRate     [blanket/multi-unit aggregate — not built this pass]
   elif BasicGroupIIRatingTerr and Calc_Building_BGII.ConstructionSymbol both non-blank:
       Lookup(BasicGroupIIRate: State|CW, BasicGroupIIRatingTerr, ConstructionSymbol, "Bldg")
   else: 0.0
   ```
2. **`LowestBaseRate`** = `Lookup(LowestBasicGroupIIRate: State|CW, ConstructionSymbol, "Bldg")` — same
   three-way shape, no territory key.
3. **`BGIIBaseRateAdjustmentFactor`** = `Lookup(BaseRateAdjustmentFactor: State|CW, "Basic Group II")`
4. **`Rate`** = `BaseRate × LCM × Calc_Building_BGII.NumericValue × BCEGFactor × BGIIBaseRateAdjustmentFactor`
   — round to 3dp. `NumericValue` is read from Building's own tab, not recomputed.
5. **`COLAdj`**:
   ```
   if no wind/hail-exclusion-for-Business-Income record exists:
       Rate × BuildersRiskFactor
   else:
       LowestBaseRate × LCM × WindstormOrHailExclFactor × BuildersRiskFactor
   ```
6. **`Factor`** — the shared helper, identical mechanism to Basic Group I's.
7. **`FinalRate`** = `COLAdj × Factor`.

---

## 5. `Premium_Summary` formula for this form

**Byte-shape-identical to Basic Group I's** with datadef names swapped — confirmed by the source doc as
a direct rename, same relationship Building's own Basic Group I/II premium files have:

```
BI_BGII_Premium =
    if BI_IncludedInBlkt = "No":
        ROUND(ROUND(IRPMFactor × PackageModFactor × Calc_BusinessIncome_BGII.FinalRate × (BI_Limit/100), 0), 0)
          × CyberIncidentExclusionFactorBGII × CyberIncidentExclusionCOLExcptnsFactorBusnIncomeBGIIToUse
    elif BI_IncludedInBlkt = "Yes" and BlktTotalFullValueAmount > 0:
        [blanket branch — not built this pass, see §7]
    else:
        0.0
```

---

## 6. Inputs → rating output — the full picture

### 6.1 What feeds the loss cost

| Stage | Reads from | Produces | Tab |
|---|---|---|---|
| 0 — the loss cost, looked up against a shared table | `Calc_Building_BGII.ConstructionSymbol`, `BasicGroupIIRatingTerr` → `Rate_Tables.BasicGroupIIRate` | `BaseRate` + `LowestBaseRate` | `Calc_Building_BGII` → `Calc_BusinessIncome_BGII` |
| 1 — the Business-Income-specific adjustment | `Rate_Tables.BaseRateAdjustmentFactor` | `BGIIBaseRateAdjustmentFactor` | `Calc_BusinessIncome_BGII` |
| 2 — turn it into a rate | `BaseRate`, `LCM`, `Calc_Building_BGII.NumericValue`, `BCEGFactor`, `BGIIBaseRateAdjustmentFactor` | `Rate` | `Calc_BusinessIncome_BGII` |
| 3 — adjust for wind/hail exclusion and Builders Risk | `Rate` or `LowestBaseRate`, the wind/hail-for-BI record, `BuildersRiskFactor` | `COLAdj` | `Calc_BusinessIncome_BGII` |
| 4 — apply the shared `Factor` | `COLAdj`, `Factor` | `FinalRate` | `Calc_BusinessIncome_BGII` |
| 5 — turn the rate into a dollar premium | `FinalRate`, `BI_Limit`, `IRPMFactor`, `PackageModFactor` | `BI_BGII_Premium` | `Premium_Summary` |

### 6.2 Full formula with if/then

```
BaseRate =
    HighestBusnIncomeBasicGroupIIBaseRate    if blanket/max-period/EEO gate fires   [not built this pass]
    elif BasicGroupIIRatingTerr <> "" and Calc_Building_BGII.ConstructionSymbol <> "":
        Lookup(BasicGroupIIRate: State|CW, BasicGroupIIRatingTerr, ConstructionSymbol, "Bldg")
    else: 0.0

LowestBaseRate = Lookup(LowestBasicGroupIIRate: State|CW, ConstructionSymbol, "Bldg")

BGIIBaseRateAdjustmentFactor = Lookup(BaseRateAdjustmentFactor: State|CW, "Basic Group II")

Rate = BaseRate × LCM × Calc_Building_BGII.NumericValue × BCEGFactor × BGIIBaseRateAdjustmentFactor
    (round to 3dp)

COLAdj =
    Rate × BuildersRiskFactor                                                    if no wind/hail-for-BI record
    else LowestBaseRate × LCM × WindstormOrHailExclFactor × BuildersRiskFactor

Factor = <same shared helper as Basic Group I>

FinalRate = COLAdj × Factor

BI_BGII_Premium =
    if BI_IncludedInBlkt = "No":
        ROUND(ROUND(IRPM × PackageMod × FinalRate × (BI_Limit/100), 0), 0)
          × CyberExclFactorBGII × CyberExclCOLExcptnsFactorBusnIncomeBGIIToUse
    elif BI_IncludedInBlkt = "Yes" and BlktTotalFullValueAmount > 0:
        [blanket branch — not built this pass, see §7]
    else: 0.0
```

---

## 7. What's deliberately left out of this pass

Same list as `Excel_Rater_BusinessIncome_BasicGroupI.md` §7, applied to this form: the blanket/max-period
base-rate branch, the blanket premium branch, `CoinsuranceToUse`'s real scan (n/a — Basic Group II
doesn't read `Factor` differently), and the `"Combined"` `TypeOfRisk` branch inherited from the shared
`Factor` helper.

## Remaining steps

1. You review this document against `Excel_Rater_BusinessIncome_BasicGroupI.md` — confirm the
   three-stacked-empty-tables gap (worse than Basic Group I's two) reads clearly as its own distinct
   finding, not a restatement.
2. Next is Broad and Special for this coverage, or your call.
3. Nothing gets built until you say go.
