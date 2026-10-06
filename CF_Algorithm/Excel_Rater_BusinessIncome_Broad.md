# Excel Rater Build Guide — Business Income, Broad

**Written:** 2026-09-02.

**Source material:** `CauseOfLoss_BusinessIncome_RatingAlgorithms.md` §"Broad — rate build-up" /
§"Broad — premium" + `BusinessIncome_ERC_Tables.md`, cross-checked against `CFCW20260601V01`. See
`Excel_Rater_BusinessIncome_Overview.md` for the shared shell and `Excel_Rater_Broad.md` for the
Building form sharing this form's base-rate table.

---

## 1. The shortest chain in the entire workbook

Two steps. No cause-of-loss adjustment, no `Factor` multiplication, no cross-reference to the Building's
own rate — this is the one Business Income form (alongside Special) with its own dedicated base-rate
table, and it is the simplest rate build-up documented anywhere in this project so far, Building or
Business Income.

| | Business Income Broad | Building's Broad (`Excel_Rater_Broad.md`) |
|---|---|---|
| Chain length | **2 steps** | 6 steps |
| Base rate table | `BroadFormBaseRate` — **same table Building uses**, different `covType` values | `BroadFormBaseRate` |
| COL adjustment | **none** | none (both forms lack this step) |
| Shared `Factor` (coinsurance) | **not applied** — confirmed no reference in the rule file | n/a (Building has no `Factor` concept) |
| LOI factor | **none** | own 4-way `Choose` |
| Deductible factor | **none** | own 4-way `Choose` |
| Final rate | straight copy of `Rate` | `AdjustedRate × DeductibleByLocationFactor × DeductibleFactor × MultiResCredit` |
| CW data | **resolves** — real rows for both Business Income `covType` keys | resolves — real rows |

Business Income's Broad reuses the exact table Building's Broad already put on `Rate_Tables` — no new
table block needed, just two new `covType` key values.

---

## 2. `Locations_Buildings` — nothing new for this form specifically

Reuses `BI_CovType` (drives the `covType` branch below), `ConstructionType` (already on the tab from
`Excel_Rater_Broad.md`), `BI_Limit`, `BI_IncludedInBlkt`.

## 3. `Rate_Tables` — no new table

`BroadFormBaseRate` is already on the workbook (`Excel_Rater_Broad.md` §3). Confirmed **30 Business
Income CW data rows present** — this table's Business Income keys resolve, e.g. Frame at 0.011.

| covType key | Meaning |
|---|---|
| `"Business Income Without Extra Expense"` | `BI_CovType = "Business Income Without Extra Expense"` |
| `"All Other"` | every other `BI_CovType` value |

---

## 4. `Calc_BusinessIncome_Broad` tab — one row per building

Straight translation of `SetBroadRatesAndFactors`'s 2-step chain.

1. **`BaseRate`**:
   ```
   if CauseOfLoss = "Broad":
       if BI_CovType = "Business Income Without Extra Expense":
           Lookup(BroadFormBaseRate: State|CW, ConstructionType, "Business Income Without Extra Expense")
       else:
           Lookup(BroadFormBaseRate: State|CW, ConstructionType, "All Other")
   else: 0.0
   ```
2. **`Rate`** = `BaseRate × LCM` — round to 3dp, same gate as step 1.
3. **`FinalRate`** = `Rate` — a straight copy, no further computation. That's the entire chain.

---

## 5. `Premium_Summary` formula for this form

```
BI_Broad_Premium =
    if CauseOfLoss = "Broad" and BI_IncludedInBlkt = "No":
        ROUND(ROUND(IRPMFactor × PackageModFactor × Calc_BusinessIncome_Broad.FinalRate × (BI_Limit/100), 0), 0)
          × CyberIncidentExclusionFactorBroad × CyberIncidentExclusionCOLExcptnsFactorBusnIncomeBroadToUse
    elif CauseOfLoss = "Broad" and BI_IncludedInBlkt = "Yes" and BlktTotalFullValueAmount > 0:
        [blanket branch — not built this pass, see §7]
    else: 0.0
```

Unlike Basic Group I/II's hardcoded coverage gate, this form's premium tests
`../CauseOfLossToUse = "Broad"` directly — the same shape as Building's Special-form gate (exact
equality), not Building's Basic Group I/II gate (blank/not-applicable test).

---

## 6. Inputs → rating output — the full picture

### 6.1 What feeds the loss cost

| Stage | Reads from | Produces | Tab |
|---|---|---|---|
| 0 — the loss cost itself | `CauseOfLoss = "Broad"`, `ConstructionType`, `BI_CovType` | `BaseRate` | `Locations_Buildings` → `Calc_BusinessIncome_Broad` |
| 1 — turn it into a rate, and stop | `BaseRate`, `Policy.LossCostMultiplier` | `FinalRate` (straight copy of `Rate`) | `Calc_BusinessIncome_Broad` |
| 2 — turn the rate into a dollar premium | `FinalRate`, `BI_Limit`, `IRPMFactor`, `PackageModFactor` | `BI_Broad_Premium` | `Premium_Summary` |

Two stages between input and premium — the fewest of any form/coverage combination in this project.

### 6.2 Full formula with if/then

```
BaseRate =
    if CauseOfLoss = "Broad":
        Lookup(BroadFormBaseRate: State|CW, ConstructionType, "Business Income Without Extra Expense")
            if BI_CovType = "Business Income Without Extra Expense"
        else Lookup(BroadFormBaseRate: State|CW, ConstructionType, "All Other")
    else: 0.0

Rate = BaseRate × LCM                          (round to 3dp)
FinalRate = Rate                               (straight copy — no COL adjustment, no Factor, no LOI, no deductible)

BI_Broad_Premium =
    if CauseOfLoss = "Broad" and BI_IncludedInBlkt = "No":
        ROUND(ROUND(IRPM × PackageMod × FinalRate × (BI_Limit/100), 0), 0)
          × CyberExclFactorBroad × CyberExclCOLExcptnsFactorBusnIncomeBroadToUse
    elif CauseOfLoss = "Broad" and BI_IncludedInBlkt = "Yes" and BlktTotalFullValueAmount > 0:
        [blanket branch — not built this pass, see §7]
    else: 0.0
```

---

## 7. What's deliberately left out of this pass

- The blanket premium branch — needs `BlktBroadAvgRate`, `FullBusnIncomeValue`, `BlktTotalFullValueAmount`

**Added 2026-10-06** (`cf-broad-chains.html` BI review #26, #27, #31; probes HAPPY, BLKT_BASIC, INCBLANK).
Broad is charged **on top of** Group I and II (UT $1,390 + $70 + $230), not instead of them. Only
`BI_IncludedInBlkt = "No"` reaches the scheduled formula: a blank value falls to the blanket side and
prices Broad, Group I and II at $0 "rated". On a blanket the cause of loss is the blanket Detail's, so a
Broad BI in a Basic blanket gets no Broad premium. A blank `BI_CovType` reads "All Other" ($230), as the
table above says.

## Remaining steps

1. You review this document — it's short by design, not by omission; the source doc confirms this is
   genuinely the entire rate build-up.
2. Next is Special for this coverage, or your call.
3. Nothing gets built until you say go.
