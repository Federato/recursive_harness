# Excel Rater Build Guide — Broad (Building & Contents)

> <!-- RC-1 stale-name notice --> **Notice (2026-09-23):** Written before the 2026-09-22 restructure. Sheet names have changed: Policy Inputs → IN - Policy; Bldg / Contents / BI Rating Worksheet → CALC - Bldg / Contents / BI Rating; Special Class Worksheet → CALC - Special Class; CoreScratchpad → CALC - CoreScratchpad. **Location Inputs / IN - Location and Special Class Inputs / IN - Special Class no longer exist**: every record is entered on **IN - Schedule** (one row per record, 40 per block), so input-sheet cell addresses here are out of date, and calc-sheet column C is record 1 of 40. Current state: CF_Algorithm/CF_Rater_RESUME.md.


**Written:** 2026-09-02.

**Source material:** `CauseOfLoss_Building_RatingAlgorithms.md` §"Broad — rate build-up" /
§"Broad — premium" + `BasicGroupI_ERC_Tables.md` (Building); `CauseOfLoss_PersonalProperty_
RatingAlgorithms.md` §"Broad — rate build-up" / §"Broad — premium" + `PersonalProperty_ERC_Tables.md`
(Contents), both cross-checked against `CFCW20260601V01`. See `Excel_Rater_Overview.md` for the shared
workbook shell, and `Excel_Rater_BasicGroupI.md` / `Excel_Rater_BasicGroupII.md` for the two forms this
one is compared against throughout.

---

## 1. What changes moving to Broad

Broad is the shortest chain of any form documented so far — **6 steps for Building, 5 for Contents**,
versus Basic Group I's 8–9 and Basic Group II's 11–12. The simplicity comes from one real structural
fact: **Broad has no cause-of-loss-adjustment step at all**, in either coverage. Where Basic Group I and
II each insert a `COLAdj` stage between the rate and the coinsurance/LOI stage, Broad goes straight from
`Rate` to `AdjustedRate`. There is nothing here that plays the role Basic Group I's sprinkler-leakage/
vandalism adjustment or Basic Group II's fire-only gate play — Broad's peril set doesn't get a dedicated
credit-and-exclusion step the way the two Basic forms do.

Broad is rated off **construction type** alone (no class code, no territory, no protection class, no
construction symbol) — closer to Special's flat-rate simplicity than to either Basic form's multi-key
lookup, but unlike Special it still varies by construction. It reads the **same `BroadFormBaseRate`
table** for both coverages, differentiated only by a `covType` argument (`"Bldg"`, `"BldrRisk"`, or
`"PersProp"`) — already visible in `Excel_Rater_BasicGroupI.md` §3 as a table this project flagged for
later use.

**Genuinely good news, for once.** Every prior form built so far (`BasicGroupIRate`,
`BasicGroupIIRate`, `LowestBasicGroupIIRate`) turned out to be header-only at the countrywide level.
`BroadFormBaseRate` is not — both source docs confirm real CW rows filed:

| Construction type | Bldg | BldrRisk | PersProp |
|---|---|---|---|
| Frame | 0.015 | 0.012 | 0.021 |
| Joisted Masonry | 0.015 | 0.012 | 0.021 |
| Non-Combustible | 0.015 | 0.012 | 0.021 |
| Masonry Non-Combustible | 0.015 | 0.012 | 0.021 |
| Modified Fire Resistive | 0.010 | 0.012 | 0.011 |
| Fire Resistive | 0.010 | 0.012 | 0.011 |

Broad is the first form in this document set where the loss cost actually resolves at the countrywide
level for every construction type, with no state filing required. Don't let that create a false sense
of security about the rest of the chain, though — the LOI table this form needs (`BroadSpecialLOIFactorBldg`
/ `...Prsnlprop`) has **not** been independently row-counted the way `BasicGroupIRate` and its siblings
were; treat it as unverified until checked, not as safe by association with this table's good news.

| | Building | Contents |
|---|---|---|
| Chain length | 6 steps | 5 steps |
| Base rate branch | Builders Risk (class 1150) gets its own `covType="BldrRisk"` lookup | **no Builders Risk branch at all** — always `covType="PersProp"` regardless of class code |
| Cause-of-loss zeroing | none — COL isn't a gate on the rate itself beyond the coverage-on-policy test | `Rate` zeroes when `CovType = "Valuable Papers and Records - Other Than Electronic Data"` — same carve-out pattern seen in both Basic forms |
| Roof-surfacing factor | applied in `AdjustedRate` | **absent** — consistent with every other Contents chain built so far |
| Deductible factor | own local four-way `Choose`, including a "blank deductible → 0.0" branch | **no local `Set` rule of any kind** — read directly from four levels up the datadef tree; the source doc calls this "the most externally-sourced deductible factor of the four PP forms," more extreme than Basic Group I/II's Contents deductible (which at least has a `Copy`-shaped rule) |
| LOI factor timing | computed after the rate steps | computed **first**, step 1 — reordering only, not a math difference |

---

## 2. `Locations_Buildings` additions for this form

Broad activates two columns that Basic Group II reserved but didn't load-bear on:

| Field | Feeds | Notes |
|---|---|---|
| `ConstructionType` | both coverages' base-rate lookup | reserved in `Excel_Rater_BasicGroupII.md` §2 for the symbol derivation; here it's read directly, not resolved into a symbol first — Broad has no symbol concept |
| `Bldg_RoofSurfacingFactorInputs` | Building's `AdjustedRate` step | reused from Basic Group I — same underlying factor, applied at a different point in the chain (Broad folds it into the adjusted-rate step rather than the rate step) |
| `PP_ValuablePapers` (Y/N) | Contents' `Rate` step — zeroes it entirely when Y | reused from Basic Group I/II's Contents chains; here the zeroing happens one step earlier, inside `Rate` itself, since Broad has no separate COL-adjustment step to put it in |

No other new columns — Broad reuses `ClassCode` (only to detect Builders Risk class 1150 on the
Building side), `Coinsurance`, `Deductible`, `Bldg_CovType`/`PP_CovForm`, `Bldg_Limit`/`PP_Limit`, and
`Bldg_IncludedInBlkt`/`PP_IncludedInBlkt` as already defined.

---

## 3. `Rate_Tables` additions for this form

**Shared by both Building and Contents:**

| Table | Building keys | Contents keys | CW rows filed? |
|---|---|---|---|
| `BroadFormBaseRate` | State\|CW, ConstructionType, `"Bldg"` or `"BldrRisk"` | State\|CW, ConstructionType, `"PersProp"` | **Yes** — confirmed real CW rows for all six construction types, both coverages (see §1 table) |
| `BroadSpecialLOIFactorBldg` (Building) / `BroadSpecialLOIFactorPrsnlProp` (Contents) | State\|CW, Limit | State\|CW, Limit | **Not independently row-counted in this project's tables docs yet** — flag per `Excel_Rater_Overview.md` §5 discipline until checked; shared with Special, which is also not yet built |
| `CoinsuranceFactor` | shared, already on this tab | shared | Yes |
| `DeductibleByLocationFactor` | shared | shared | Yes |
| `Deductible250Factor` | causeOfLoss arg = `"Broad"` | not used — Contents has no local deductible rule at all (see §5) | Yes |
| `DeductibleFactor` | Deductible, TotAmtInsurance, `"Other Cause Of Loss"` | not used locally, see §5 | Yes |
| `CyberIncidentExclusionFactors`, `...WithEnsuingCauseOfLossExceptionsFactors` | cause-of-loss group `"Broad"` | cause-of-loss group `"Broad"` | Yes (shared table, different key) |

No Broad-only tables beyond `BroadFormBaseRate` itself — every other table this form needs was already
introduced by an earlier form, or (LOI, deductible) is the same table Special will also need once built.

---

## 4. `Calc_Building_Broad` tab — one row per building

Straight translation of `CauseOfLoss_Building_RatingAlgorithms.md`'s 6-step chain
(`SetBroadRatesAndFactors`, line 9063).

1. **`BaseRate`**:
   ```
   if CauseOfLoss = "Broad" and ConstructionType <> "":
       if ClassCode = "1150":
           LookupBroadFormBaseRate(State|CW, ConstructionType, "BldrRisk")
       else:
           LookupBroadFormBaseRate(State|CW, ConstructionType, "Bldg")
   else:
       0.0
   ```
2. **`Rate`** = `BaseRate × LCM` — round to 3dp. No addends, no multipliers at this step — the simplest
   `Rate` formula of any form built so far.
3. **`LOIFactor`** — four-way: blanket copy from `BlktBroadLOIFactor` when blanketed and `BlktIDNum > 0`;
   `LookupBroadSpecialLOIFactorWithArgs` for Builders Risk; `LookupBroadSpecialLOIFactorBldg(Limit)` for
   other cov types with a `Limit` present; `1.0` otherwise.
4. **`AdjustedRate`** = `Rate × RoofSurfacingACVFactor × CoinsuranceFactor × LOIFactor`
5. **`DeductibleFactor`**:
   ```
   if Deductible = "250":            LookupDeductible250Factor("Broad")
   elif Deductible = "Not Applicable": 1.0
   elif Deductible <> "":            LookupDeductibleFactor(Deductible, TotAmtInsurance, "Other Cause Of Loss")
   else:                              0.0     # blank deductible zeroes the rate — not 1.0
   ```
6. **`FinalRate`** = `AdjustedRate × DeductibleByLocationFactor × DeductibleFactor × MultiResidentialPropSpecialCreditFactor`

**Correction (was wrong in this doc and in Basic Group I's/Basic Group II's docs):** `TotAmtInsurance` is
NOT the Building's own limit. Confirmed directly against the rule XML —
`TotAmtInsurance = StructureLimitToUse + OccupancyTotAmtInsuranceSum + SpecialClassRiskTotAmtInsurance`,
i.e. the Building's own limit **plus** every Contents/Personal Property item's limit at that location
**plus** any Special Class Risk amount. This is a genuine combined location total, matching CLM manual
language ("total amount of insurance at each location by adding the limits of insurance for all covered
property at that location"). Every build in this project so far (BGI's live formula, BGII's `CoreScratchpad`
rows 84-94, and this doc's own §8 formula block below) used the Building's own limit only — a real bug once
a location has Contents coverage, not just a documentation simplification.

**Fix status, 2026-09-10:** no longer purely backlogged — Contents Limit now exists on `Location Inputs`
(row 22), so the fix is buildable and has been designed. `CoreScratchpad!C138` computes the combined total
(Building Limit + Contents Limit); `CoreScratchpad!C41` — the cell this form's `DeductibleFactor` reads its
Limit argument from — gets repointed to `=CoreScratchpad!C138`. Confirmed by reading the live formulas
directly (not inferred) that `C41` is shared: it's the same cell BGI's own `DeductibleFactor` (row 42)
reads, so this one change fixes both forms' identical bug at once. Special Class Risk amounts are still
out of scope (not built anywhere in this project) — the combined total is Building + Contents only. Not
yet confirmed applied in the live rater — see project memory
`project_deductiblefactor-uses-location-total-not-building-limit` for current status.

---

## 5. `Calc_Contents_Broad` tab — one row per building

Straight translation of `CauseOfLoss_PersonalProperty_RatingAlgorithms.md`'s 5-step chain
(`SetBroadRatesAndFactors`, line 4138).

1. **`LOIFactor`** *(computed first — order doesn't affect the math)*: three-way — blanket copy from
   `BlktBroadLOIFactor`; `LookupBroadSpecialLOIFactorPrsnlProp(OccupTotalLOIToUse)` when `CovForm` not
   in (`Legal Liability Coverage Form`, `Tobacco Sales Warehouse Coverage Form`) and
   `OccupTotalLOIToUse > 0`; else `1.0`. **No separate Builders Risk branch** — unlike Building's four-way
   Broad LOI rule.
2. **`BaseRate`**:
   ```
   if CauseOfLoss = "Broad" and ConstructionType <> "":
       LookupBroadFormBaseRate(State|CW, ConstructionType, "PersProp")
   else:
       0.0
   ```
   **No Builders Risk branch at all** — always `"PersProp"`, regardless of `ClassCode`.
3. **`Rate`**:
   ```
   if CauseOfLoss <> "Broad" or PP_ValuablePapers = "Y":
       0.0
   else:
       BaseRate × LCM
   ```
   round to 3dp. The Valuable-Papers zeroing lives directly inside `Rate` here — Broad has no separate
   COL-adjustment step to carry that carve-out the way Basic Group I/II do.
4. **`AdjustedRate`** = `LOIFactor × Rate × CoinsuranceFactor` — **no roof-surfacing factor**, consistent
   with every Contents chain built so far.
5. **`FinalRate`** = `AdjustedRate × DeductibleByLocationFactor × DeductibleFactor` — `DeductibleFactor`
   here is **not computed anywhere in this workbook's Contents chain** in ISO's own terms; the source
   doc confirms it's read directly from an ancestor context with no local rule at all, the most
   externally-sourced deductible factor of any Contents form documented so far. **Build it as the same
   local `Choose` used on `Calc_Building_Broad`** — same table, same shape — per the documented-deviation
   treatment already established in `Excel_Rater_BasicGroupI.md` §5 step 9 and
   `Excel_Rater_BasicGroupII.md` §5 step 11. Leave the same cell comment.

---

## 6. `Premium_Summary` formulas for this form

Both premium files follow the Basic Group I/II shape with Broad-specific gates layered on top —
confirmed by both source docs as structurally derived from the earlier forms' premium files, not
independent designs:

```
Bldg_Premium (Broad) =
    if Bldg_CovType in ("Building","Builders Risk","Improvements and Betterments","Condominium Association")
       and CauseOfLoss = "Broad" and Bldg_IncludedInBlkt = "No":
        ROUND(IRPMFactor × MultiPremiumAndDispersionCreditFactor × PackageModFactor
              × Calc_Building_Broad.FinalRate × (Bldg_Limit / 100), 0)
          × CyberIncidentExclusionFactorBroad × CyberIncidentExclusionCOLExcptnsFactorBroad
    elif Bldg_CovType = "Legal Liability" and CauseOfLoss = "Broad":
        Calc_Building_Broad.Rate × LegalLiabilityFactor × LegalLiabAddlInsurableIntFactor × (Bldg_Limit/100)
          × PackageModFactor × IRPMFactor × CyberIncidentExclusionFactorBroad × CyberIncidentExclusionCOLExcptnsFactorBroad
        [not built this pass — see §7]
    elif Bldg_IncludedInBlkt = "Yes" and BlktCauseOfLossValue = "Broad":
        [blanket branch — not built this pass, see §7]
    else:
        0.0

PP_Premium (Broad) =
    if PP_CovForm not in ("Legal Liability Coverage Form","Tobacco Sales Warehouse Coverage Form")
       and CauseOfLoss = "Broad" and PP_IncludedInBlkt = "No":
        ROUND(IRPMFactor × MultiPremiumAndDispersionCreditFactor × PackageModFactor
              × Calc_Contents_Broad.FinalRate × (PP_Limit / 100), 0)
          × CyberIncidentExclusionFactorBroad × CyberIncidentExclusionCOLExcptnsFactorBroad
    elif PP_CovForm = "Legal Liability Coverage Form" and CauseOfLoss = "Broad":
        [not built this pass — see §7]
    elif PP_IncludedInBlkt = "Yes" and BlktCauseOfLossValue = "Broad":
        [blanket branch — not built this pass, see §7]
    else:
        0.0
```

**One thing worth flagging before it's built:** both Legal Liability branches use the **raw, un-adjusted
rate** (`Rate`, not `FinalRate` or any coinsurance/LOI/deductible-adjusted value) — consistent with every
other form's Legal Liability branch, but worth restating here since Broad has no COL-adjustment stage to
have skipped in the first place the way Basic Group I/II's Legal Liability branches do.

---

## 7. What's deliberately left out of this pass

Same shape as the prior two forms:

- Legal Liability premium branch (both coverages)
- Blanket-rated premium branch (both coverages) — needs the same `Blkt*` columns flagged as out of
  scope in `Excel_Rater_BasicGroupI.md` §7
- Row-count verification of `BroadSpecialLOIFactorBldg` / `...Prsnlprop` — flagged unverified in §3,
  not yet checked the way `BasicGroupIRate` and its siblings were

---

## 8. Inputs → rating output — the full picture

### 8.1 What feeds the loss cost (Building)

Broad's loss cost is the simplest of the three forms documented so far — one key (`ConstructionType`,
plus a class-code check for Builders Risk), no territory, no protection class, no construction symbol.

| Stage | Reads from | Produces | Tab |
|---|---|---|---|
| 0 — the loss cost itself | `CauseOfLoss = "Broad"`, `ConstructionType`, `ClassCode` (→ Builders Risk branch) | `BaseRate` | `Locations_Buildings` → `Calc_Building_Broad` |
| 1 — turn it into a rate | `BaseRate`, `Policy.LossCostMultiplier` | `Rate` | `Calc_Building_Broad` |
| 2 — apply how the insured chose to insure | `Rate`, `Bldg_RoofSurfacingFactorInputs`, `Coinsurance`, `Bldg_CovType`, `Bldg_Limit` | `AdjustedRate` | `Calc_Building_Broad` |
| 3 — apply the chosen deductible | `AdjustedRate`, `Deductible`, `Bldg_Limit`, `Bldg_MultiResIndicator` | `FinalRate` | `Calc_Building_Broad` |
| 4 — turn the rate into a dollar premium | `FinalRate`, `Bldg_Limit`, the three `Policy` schedule-rating factors | `Bldg_Premium` | `Premium_Summary` |

Notice there's no cause-of-loss-adjustment stage at all — Basic Group I's stage 2 and Basic Group II's
stage 2 both disappear here; Broad goes straight from `Rate` to the coinsurance/LOI stage.

### 8.2 Full formula with if/then (Building)

```
BaseRate =
    if CauseOfLoss = "Broad" and ConstructionType <> "":
        if ClassCode = "1150":
            LookupBroadFormBaseRate(State|CW, ConstructionType, "BldrRisk")
        else:
            LookupBroadFormBaseRate(State|CW, ConstructionType, "Bldg")
    else:
        0.0

Rate = BaseRate × LCM                                             (round to 3dp; no addends, no other factors)

LOIFactor =
    <blanket copy>                                                if Bldg_IncludedInBlkt = "Yes" and BlktIDNum > 0
    elif Bldg_CovType = "Builders Risk":
        LookupBroadSpecialLOIFactorWithArgs(...)                   or 0.0 if the Builders Risk limit is absent
    elif Bldg_CovType not in ("Leasehold Interest","Legal Liability","No Coverage") and Bldg_Limit <> "":
        LookupBroadSpecialLOIFactorBldg(State|CW, Bldg_Limit)
    else:
        1.0

AdjustedRate = Rate × RoofSurfacingACVFactor × CoinsuranceFactor × LOIFactor

DeductibleFactor =
    LookupDeductible250Factor("Broad")                              if Deductible = "250"
    elif Deductible = "Not Applicable":  1.0
    elif Deductible <> "":               LookupDeductibleFactor(Deductible, TotAmtInsurance, "Other Cause Of Loss")
    else:                                0.0                        # blank deductible zeroes the rate, not 1.0
    # TotAmtInsurance = StructureLimitToUse + OccupancyTotAmtInsuranceSum + SpecialClassRiskTotAmtInsurance --
    # the Building's own limit PLUS every Contents item's limit at the location PLUS Special Class Risk.
    # NOT Bldg_Limit alone -- see the correction note in §5 above. Backlogged until Contents is built.

FinalRate = AdjustedRate × DeductibleByLocationFactor × DeductibleFactor × MultiResidentialPropSpecialCreditFactor

Bldg_Premium =
    if Bldg_CovType in ("Building","Builders Risk","Improvements and Betterments","Condominium Association")
       and CauseOfLoss = "Broad" and Bldg_IncludedInBlkt = "No":
        ROUND(IRPM × MultiPremiumDispersion × PackageMod × FinalRate × (Bldg_Limit/100), 0)
          × CyberExclFactorBroad × CyberExclCOLExcptnsFactorBroad
    elif Bldg_CovType = "Legal Liability" and CauseOfLoss = "Broad":  [not built this pass — see §7]
    elif Bldg_IncludedInBlkt = "Yes" and BlktCauseOfLossValue = "Broad": [blanket — not built this pass]
    else: 0.0
```

### 8.3 What feeds the loss cost (Contents)

Same construction-type key as Building, but **no Builders Risk branch** and **the Valuable-Papers
zeroing gate lives inside the rate step itself**, since there's no separate COL-adjustment stage to
carry it — unlike Basic Group I/II, where that same gate sits one stage later.

| Stage | Reads from | Produces | Tab |
|---|---|---|---|
| 0 — the loss cost itself | `CauseOfLoss = "Broad"`, `ConstructionType` — **no `ClassCode` check at all** | `BaseRate` | `Locations_Buildings` → `Calc_Contents_Broad` |
| 1 — turn it into a rate, with the Valuable-Papers gate folded in | `BaseRate`, `Policy.LossCostMultiplier`, `PP_ValuablePapers` | `Rate` | `Calc_Contents_Broad` |
| 2 — apply how the insured chose to insure | `Rate`, `Coinsurance`, `PP_CovForm`, `PP_Limit`/`OccupTotalLOIToUse` — **no roof input** | `AdjustedRate` | `Calc_Contents_Broad` |
| 3 — apply the chosen deductible | `AdjustedRate`, `Deductible` — **no local Contents deductible rule at all**, see §5 | `FinalRate` | `Calc_Contents_Broad` |
| 4 — turn the rate into a dollar premium | `FinalRate`, `PP_Limit`, the three `Policy` factors | `PP_Premium` | `Premium_Summary` |

### 8.4 Full formula with if/then (Contents)

```
LOIFactor =
    <blanket copy>                                                  if PP_IncludedInBlkt = "Yes"
    elif PP_CovForm not in ("Legal Liability Coverage Form","Tobacco Sales Warehouse Coverage Form")
         and OccupTotalLOIToUse > 0:
        LookupBroadSpecialLOIFactorPrsnlProp(State|CW, OccupTotalLOIToUse)
    else:
        1.0                                                          # no Builders Risk branch, unlike Building

BaseRate =
    LookupBroadFormBaseRate(State|CW, ConstructionType, "PersProp")   if CauseOfLoss = "Broad" and ConstructionType <> ""
    else 0.0                                                          # always "PersProp" — no class-code check

Rate =
    0.0    if CauseOfLoss <> "Broad" or PP_ValuablePapers = "Y"
    else BaseRate × LCM                                               (round to 3dp)

AdjustedRate = LOIFactor × Rate × CoinsuranceFactor                   # no roof-surfacing factor, any branch

FinalRate = AdjustedRate × DeductibleByLocationFactor × DeductibleFactor
    # DeductibleFactor: same local Choose as Building's — documented deviation, see §5 step 5

PP_Premium =
    if PP_CovForm not in ("Legal Liability Coverage Form","Tobacco Sales Warehouse Coverage Form")
       and CauseOfLoss = "Broad" and PP_IncludedInBlkt = "No":
        ROUND(IRPM × MultiPremiumDispersion × PackageMod × FinalRate × (PP_Limit/100), 0)
          × CyberExclFactorBroad × CyberExclCOLExcptnsFactorBroad
    elif PP_CovForm = "Legal Liability Coverage Form" and CauseOfLoss = "Broad": [not built this pass — see §7]
    elif PP_IncludedInBlkt = "Yes" and BlktCauseOfLossValue = "Broad": [blanket — not built this pass]
    else: 0.0
```

---

## Remaining steps

1. You review this document against `Excel_Rater_BasicGroupI.md` and `Excel_Rater_BasicGroupII.md` —
   in particular whether the good-news countrywide `BroadFormBaseRate` data changes anything about how
   you want the workbook to present a "resolves at CW level" form differently from the two that don't.
2. Next coverage form is your call — Special, the Legal Liability/blanket branches for any form now
   built, or moving on to a different coverage or LOB entirely.
3. Nothing gets built until you say go.
