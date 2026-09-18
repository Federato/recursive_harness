# Excel Rater Build Guide — Business Income, Special

**Written:** 2026-09-02.

**Source material:** `CauseOfLoss_BusinessIncome_RatingAlgorithms.md` §"Special — rate build-up" /
§"Special — premium" + `BusinessIncome_ERC_Tables.md`, cross-checked against `CFCW20260601V01`. See
`Excel_Rater_BusinessIncome_Overview.md` for the shared shell and `Excel_Rater_Special.md` for the
Building form this one is compared against.

---

## 1. The one form where Business Income and Building genuinely diverge in shape

Every other Business Income form either borrows the Building's rate outright (Basic Group I/II) or shares
Building's exact table (Broad). Special does neither — it has its **own** dedicated base-rate tables,
**does** vary by construction type (unlike Building's flat statewide Special rate), and adds a dimension
Building's Special has no equivalent for at all: an apartment/condominium classification that feeds the
base-rate lookup directly.

| | Business Income Special | Building's Special (`Excel_Rater_Special.md`) |
|---|---|---|
| Chain length | 6 steps | 9 steps |
| Base rate | **varies by construction type** (`SpecialFormIncldgTheftTimeElementBaseRate`) | flat statewide constant, no construction dependency |
| Extra base-rate dimension | `SpecialIncludingTheftTypeRisk` — `"Apartments and Condominiums"` vs. `"Other than..."`, from `BI_ApartmentCondoIndicator` | none |
| Builders Risk base rate | own table, `SpecialFormBldrsRiskTimeElementBaseRate`, CW = 0.018 | own table, `SpecialBuildersRiskRate`, CW = 0.015 |
| Roof-surfacing factor | **none** — Business Income has no roof concept at all | applied in COL adjustment |
| Theft-exclusion factor | keyed on `BI_ApartmentCondoIndicator` — a 2-value table | flat CW constant, 0.88 |
| Protective-safeguard credits | none (no Watchman/Burglary-Alarm concept — that's a Contents-only thing under Building) | n/a — Building's Special has none either; Contents' does |
| Coinsurance/LOI/deductible | **none of the three** — collapsed to nothing; `Factor` isn't applied here either (Broad/Special never use it) | own coinsurance, LOI, and deductible steps |
| Final rate | straight copy of `SpecialCauseOfLossAdjustment` (like Broad) | `AdjustedRate × DeductByLoc × DeductFactor × MultiResCredit` |
| Premium file | **byte-shape-identical to Broad's** — not a structural outlier | genuinely different structure from the Basic-form pattern |

**The premium-file inversion is worth calling out on its own.** Under Building, Special is the outlier —
different rounding, extra guards, raw-rate-only Legal Liability branch. Under Business Income, Special's
premium file is confirmed structurally identical to Broad's, down to the rounding pattern. The coverage
that stood out under Building blends right in under Business Income.

---

## 2. `Locations_Buildings` — nothing new for this form specifically

Reuses `BI_CovType`, `BI_ApartmentCondoIndicator`, `BI_TheftExclusionAttached`, `ClassCode` (Builders
Risk detection), `ConstructionType`, `BI_Limit`, `BI_IncludedInBlkt` — all already defined in
`Excel_Rater_BusinessIncome_Overview.md` §3.

## 3. `Rate_Tables` — three new tables for this form

| Table | Keys | CW rows filed? |
|---|---|---|
| `SpecialFormIncldgTheftTimeElementBaseRate` | State\|CW, `ConstructionType`, `BI_CovType`, `SpecialIncludingTheftTypeRisk` | Yes — 24 rows |
| `SpecialFormBldrsRiskTimeElementBaseRate` | State\|CW, `"Y"` | Yes — 1 row, CW = 0.018 |
| `SpecialLeaseHoldTimeElementTheftExclusionFactor` | State\|CW, `BI_ApartmentCondoIndicator` | Yes — 2 rows |

**All three resolve at the countrywide level.** Business Income's Special is the second form (after
Broad) that doesn't hit a data gap this pass — a real contrast with Building's Special, where the
equivalent building-rate table (`SpecialBuildingRate`) is empty.

---

## 4. `Calc_BusinessIncome_Special` tab — one row per building

Straight translation of `SetSpecialRatesAndFactors`'s 6-step chain.

1. **`SpecialTheftExclusionIndicator`** = `1` if `BI_TheftExclusionAttached = "Y"` else `0` — Business
   Income's own instance of the theft-exclusion flag, tracked separately from the Building's.
2. **`SpecialIncludingTheftTypeRisk`**:
   ```
   if CauseOfLoss = "Special":
       "Apartments and Condominiums"              if BI_ApartmentCondoIndicator = "Y"
       "Other than Apartments and Condominiums"    if BI_ApartmentCondoIndicator = "N"
       ""                                          otherwise
   else: ""
   ```
3. **`SpecialTheftExclusionFactor`**:
   ```
   if CauseOfLoss = "Special" and SpecialTheftExclusionIndicator = 1 and BI_ApartmentCondoIndicator <> "":
       Lookup(SpecialLeaseHoldTimeElementTheftExclusionFactor: State|CW, BI_ApartmentCondoIndicator)
   else: 1.0
   ```
4. **`BaseRate`**:
   ```
   if CauseOfLoss = "Special" and ClassCode = "1150":
       Lookup(SpecialFormBldrsRiskTimeElementBaseRate: State|CW, "Y")           # CW 0.018
   elif SpecialIncludingTheftTypeRisk <> "":
       Lookup(SpecialFormIncldgTheftTimeElementBaseRate:
           State|CW, ConstructionType, BI_CovType, SpecialIncludingTheftTypeRisk)
   else: 0.0
   ```
5. **`Rate`** = `BaseRate × LCM` — round to 3dp, same gate as step 4.
6. **`COLAdj`** = `Rate × SpecialTheftExclusionFactor` — round to 3dp, unconditional. No roof-surfacing
   factor anywhere — Business Income has no roof concept at all, the same absence Contents already
   established under Building's Special.
7. **`FinalRate`** = `COLAdj` — a straight copy, matching Broad. No `Factor` multiplication for this
   form.

---

## 5. `Premium_Summary` formula for this form

**Structurally identical to Broad's** — confirmed by the source doc as a line-by-line match, not just a
naming convention:

```
BI_Special_Premium =
    if CauseOfLoss = "Special" and BI_IncludedInBlkt = "No":
        ROUND(ROUND(IRPMFactor × PackageModFactor × Calc_BusinessIncome_Special.FinalRate × (BI_Limit/100), 0), 0)
          × CyberIncidentExclusionFactorSpecial × CyberIncidentExclusionCOLExcptnsFactorBusnIncomeSpecialToUse
    elif CauseOfLoss = "Special" and BI_IncludedInBlkt = "Yes" and BlktTotalFullValueAmount > 0:
        [blanket branch — not built this pass, see §7]
    else: 0.0
```

Unlike Building's Special premium file — which uses nested `Product` with no `Round` wrapper and reversed
factor ordering — this one uses the same nested-`Round`-then-cyber-factor pattern every other Business
Income form uses. Don't carry Building's Special-specific rounding quirk over here; it doesn't apply.

---

## 6. Inputs → rating output — the full picture

### 6.1 What feeds the loss cost

| Stage | Reads from | Produces | Tab |
|---|---|---|---|
| 0 — the loss cost itself | `CauseOfLoss = "Special"`, `ClassCode` (Builders Risk gate), `ConstructionType`, `BI_CovType`, `BI_ApartmentCondoIndicator` (via `SpecialIncludingTheftTypeRisk`) | `BaseRate` | `Locations_Buildings` → `Calc_BusinessIncome_Special` |
| 1 — turn it into a rate | `BaseRate`, `Policy.LossCostMultiplier` | `Rate` | `Calc_BusinessIncome_Special` |
| 2 — adjust for theft exclusion, and stop | `Rate`, `BI_TheftExclusionAttached`, `BI_ApartmentCondoIndicator` | `FinalRate` (straight copy of `COLAdj`) | `Calc_BusinessIncome_Special` |
| 3 — turn the rate into a dollar premium | `FinalRate`, `BI_Limit`, `IRPMFactor`, `PackageModFactor` | `BI_Special_Premium` | `Premium_Summary` |

### 6.2 Full formula with if/then

```
SpecialTheftExclusionIndicator = 1 if BI_TheftExclusionAttached = "Y" else 0

SpecialIncludingTheftTypeRisk =
    if CauseOfLoss = "Special":
        "Apartments and Condominiums"            if BI_ApartmentCondoIndicator = "Y"
        "Other than Apartments and Condominiums"  if BI_ApartmentCondoIndicator = "N"
        ""                                        otherwise
    else: ""

SpecialTheftExclusionFactor =
    Lookup(SpecialLeaseHoldTimeElementTheftExclusionFactor: State|CW, BI_ApartmentCondoIndicator)
        if CauseOfLoss = "Special" and SpecialTheftExclusionIndicator = 1 and BI_ApartmentCondoIndicator <> ""
    else: 1.0

BaseRate =
    Lookup(SpecialFormBldrsRiskTimeElementBaseRate: State|CW, "Y")     if CauseOfLoss = "Special" and ClassCode = "1150"
    elif SpecialIncludingTheftTypeRisk <> "":
        Lookup(SpecialFormIncldgTheftTimeElementBaseRate: State|CW, ConstructionType, BI_CovType, SpecialIncludingTheftTypeRisk)
    else: 0.0

Rate = BaseRate × LCM                              (round to 3dp)

COLAdj = Rate × SpecialTheftExclusionFactor        (round to 3dp; no roof factor — none exists)

FinalRate = COLAdj                                 (straight copy — no Factor, matching Broad)

BI_Special_Premium =
    if CauseOfLoss = "Special" and BI_IncludedInBlkt = "No":
        ROUND(ROUND(IRPM × PackageMod × FinalRate × (BI_Limit/100), 0), 0)
          × CyberExclFactorSpecial × CyberExclCOLExcptnsFactorBusnIncomeSpecialToUse
    elif CauseOfLoss = "Special" and BI_IncludedInBlkt = "Yes" and BlktTotalFullValueAmount > 0:
        [blanket branch — not built this pass, see §7]
    else: 0.0
```

---

## 7. What's deliberately left out of this pass

- The blanket premium branch — needs `BlktSpecialAvgRate`, `FullBusnIncomeValue`, `BlktTotalFullValueAmount`

This completes all four non-Earthquake Business Income forms.

## Remaining steps

1. You review this document against `Excel_Rater_Special.md` — the premium-file inversion (Special
   blends in under Business Income, stands out under Building) is worth double-checking since it's easy
   to assume Special always behaves the same way across coverages.
2. All four non-Earthquake Business Income forms are now built. Next is Earthquake/Agreed Value, Special
   Class Business Income, or your call on a different coverage or LOB.
3. Nothing gets built until you say go.
