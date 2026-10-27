# Excel Rater Build Guide — Basic Group I (Building & Contents)

> <!-- RC-1 stale-name notice --> **Notice (2026-09-23):** Written before the 2026-09-22 restructure. Sheet names have changed: Policy Inputs → IN - Policy; Bldg / Contents / BI Rating Worksheet → CALC - Bldg / Contents / BI Rating; Special Class Worksheet → CALC - Special Class; CoreScratchpad → CALC - CoreScratchpad. **Location Inputs / IN - Location and Special Class Inputs / IN - Special Class no longer exist**: every record is entered on **IN - Schedule** (one row per record, 40 per block), so input-sheet cell addresses here are out of date, and calc-sheet column C is record 1 of 40. Current state: CF_Algorithm/CF_Rater_RESUME.md.


**Written:** 2026-09-02. **Restructured:** 2026-09-02 — split out of the original
`Excel_Rater_BuildGuide.md` into its own document; see `Excel_Rater_Overview.md` for the shared
workbook shell (Policy tab, shared Locations_Buildings columns, Rate_Tables discipline, Premium_Summary
shape) this document builds on top of.

**Source material:** `CauseOfLoss_Building_RatingAlgorithms.md` + `BasicGroupI_ERC_Tables.md`
(Building); `CauseOfLoss_PersonalProperty_RatingAlgorithms.md` + `PersonalProperty_ERC_Tables.md`
(Contents), both cross-checked against `CFCW20260601V01`.

---

## 1. Why Building and Contents can't share a formula here

Basic Group I for Building and Basic Group I for Contents look similar — both are class-rated, both
multiply a base rate by a chain of factors, both end in the same premium shape (see
`Excel_Rater_Overview.md` §6). But the rate build-up underneath is genuinely different, not a renamed
copy (Basic Group II's premium file *is* a byte-identical rename of Building's; Basic Group I is not
that lucky for Building vs. Contents):

| | Building | Personal Property (Contents) |
|---|---|---|
| Base rate lookup key | `ClassCode, ConstructionCode, "Not Applicable", "Building"` | `ClassCode, ConstructionCode, Group (A/B/C/YARD), "PersProp"` |
| Rate addends | `SubStdConditionRate + VacantBuildingRate` | `SubStdConditionRate` only — **no vacancy addend** |
| Contents-only credit | — | `FireSafeVaultFactor` (CW 0.50) |
| Roof-surfacing factor | applied in the rate step | **does not exist** — contents have no roof |
| Coverage-on-policy gate | `CauseOfLossToUse` not blank / not "Not Applicable" | `NOT Exist(SpecialCoinsuranceProvisions) AND NOT Exist(ValueReportingForm)` — has nothing to do with cause of loss |
| Multi-residential credit | applies | does not exist in the PP ruleset at all |
| Deductible factor | computed locally | `Copy`'d from an ancestor record — flagged as an open question in the source doc; **build the local `Choose` in Excel anyway**, per §5 |

Practical consequence: one calc tab per coverage (`Calc_Building_BGI`, `Calc_Contents_BGI`), both
reading from the shared `Locations_Buildings` and `Rate_Tables` tabs described in the overview plus the
form-specific additions below.

---

## 2. `Locations_Buildings` additions for this form

On top of the shared columns in `Excel_Rater_Overview.md` §4:

### Building-only columns

| Field | Feeds |
|---|---|
| `Bldg_CovType` | premium branch gate (`Building`/`Builders Risk`/`Improvements and Betterments`/`Condominium Association`/`Legal Liability`/`Leasehold Interest`) |
| `Bldg_Limit` | premium formula |
| `Bldg_SubStdConditionArgs` | drives `SubStdConditionRate` lookup — leave blank/0 if not substandard |
| `Bldg_VacantIndicator` / `Bldg_VacantOccupancy` | drives `VacantBuildingRate` lookup — blank if not vacant |
| `Bldg_IncludedInBlkt` | `"No"` for this pass — blanket rating out of scope |
| `Bldg_RoofSurfacingFactorInputs` | drives `LimitationsOnCovForRoofSurfacingFactor` lookup |
| `Bldg_SprinklerLeakageExcluded` (Y/N) | drives which sprinkler-leakage factor branch applies |
| `Bldg_VandalismExcluded` (Y/N) | drives `VandalismExclFactor` |
| `Bldg_StdPropertyPolicy` (Y/N) | drives `StdPropPolGroupIFactor` |
| `Bldg_MultiResIndicator` | drives `MultiResidentialPropSpecialCreditFactor` — leave blank if N/A |

### Contents-only columns

| Field | Feeds |
|---|---|
| `PP_CovForm` | premium branch gate — *this is `CovForm`, not `CovType`*, the flagged Building/Contents naming split |
| `PP_Limit` | premium formula |
| `PP_Group` (A/B/C/YARD) | base-rate lookup key — Contents-only occupancy grouping, no Building equivalent |
| `PP_YardPropertyIndicator` | only relevant when `PP_Group = "YARD"` |
| `PP_CovType = "Personal Property in a Vault with an Approved Fire Rating"` | drives `FireSafeVaultFactor` — Contents-only concept; **corrected 2026-09-10**, this is one value on the `CovType` domain, not a separate Y/N field |
| `PP_ValuablePapers` (Y/N) | when Y, `BasicGroupICauseOfLossAdjustment = 0` — Contents-only carve-out |
| `PP_SubStdConditionArgs` | drives `SubStdConditionRate` — same table Building uses, separate input in case Contents and Building differ on the same building |
| `PP_SprinklerLeakageExcluded`, `PP_VandalismExcluded`, `PP_StdPropertyPolicy` | same shape as Building's, kept separate |
| `PP_IncludedInBlkt` | `"No"` for this pass |

---

## 3. `Rate_Tables` additions for this form

**Shared by both Building and Contents, Basic Group I-specific:**

| Table | Building keys | Contents keys |
|---|---|---|
| `BasicGroupIRate` | ClassCode, ConstructionCode, `"Not Applicable"`, `"Building"` | ClassCode, ConstructionCode, Group, `"PersProp"` |
| `ProtectionClassFactor` | State\|CW, ProtectionClass | State\|CW, ProtectionClass, ConstructionCode |
| `SprinklerLeakageExclNonSprinkleredRate` | State\|CW — Building's LCM-scaled value is named `SprinklerLeakageExclNonSprinkleredBldgRate`, see correction below | State\|CW — **Contents is sourced from the separate `CommercialPropertyPersonalProperty` ERC datadef group, not Structure — its own `SprinklerLeakageExclNonSprinkleredRate` (no suffix) is already the LCM-scaled value, don't rename it, see correction below** |
| `SprinklerLeakageExclSprinkleredFactor` | State\|CW | State\|CW, ConstructionCode, `"PrsnlProp"` |
| `RatingTerritoryGroupIFactor` (Building's territory factor) | State\|CW, Territory | not used as-is — Contents reuses the underlying territory value via a differently-named table; **verify the exact PP territory-factor table name against the ERC package before filling this in** — flagged unresolved in the source doc |

**Building-only:**

| Table | Notes |
|---|---|
| `VacantBldgPreviousOrIntendedOccup` | feeds `VacantBuildingRate` |
| `SprinklerLeakageNotExcluded` | Specific/Tentative only — leave unused this pass (class-rated only) |
| `LimitationsOnCovForRoofSurfacingFactor` | |
| `BasicGroupILOIFactorBldg` | Building-specific LOI table |
| `MultiResidentialPropSpecialCreditHeatFactor`, `...ControlFactor` | gated on `MultipleResidentialPropSpecialCredit ≠ "No"` + one of 12 apartment class codes; combined factor = `Round(Heat × Control, 3)`; **CT overrides Control (0.50 vs. CW 0.70); MA/ME disable the credit via a restricted dropdown domain, not a rate override** — see `BasicGroupI_ERC_Tables.md` session findings 2026-09-08 and `Excel_Rater_MultiResCredit_Walkthrough.html` |

**Contents-only:**

| Table | Notes |
|---|---|
| `FireSafeVaultFactor` | State\|CW, `"Y"` — CW value confirmed 0.50 |
| `BasicGroupILOIFactorPersProp` | Contents-specific LOI table, distinct from Building's |
| `LegalLiabilityFactor` | keyed `CovType="PersProp"` — only needed if you build the Legal Liability premium branch |

### Known data gap for this form

> **`BasicGroupIRate.RateTable.csv` is header-only — zero data rows at the countrywide level**, for
> both the Building rows and the Personal Property rows, confirmed by direct row-count check. Any state
> without its own filed base rate resolves to blank/0, and the whole chain collapses to zero from that
> point forward. Build the lookup so a missing result renders a visible flag, per
> `Excel_Rater_Overview.md` §5.

---

## 4. `Calc_Building_BGI` tab — one row per building

Straight translation of `CauseOfLoss_Building_RatingAlgorithms.md`'s 8-step chain and its "Quick
reference — end-to-end, class-rated scheduled building" block.

1. **`BaseRate`** = `LookupBasicGroupIRate(State|CW, ClassCode, ConstructionCode, "Not Applicable", "Building")`
2. **`Rate`** = `((BaseRate × LCM) + SubStdConditionRate + VacantBuildingRate) × TerritoryFactor × ProtectionClassFactor × RoofSurfacingACVFactor` — round to 3dp
3. **`COLAdj`** = `ROUND(Rate − SprinklerLeakageExclNonSprinkleredBldgRate, 3) × SprinklerLeakageExclSprinkleredFactor × VandalismExclFactor × StdPropPolGroupIFactor`
4. **`CoinsuranceFactor`** — lookup, skipped (left unchanged) when `ClassCode = "1150"` or `ValuationType = "Functional Valuation"`
5. **`LOIFactor`** = `LookupBasicGroupILOIFactorBldg(Limit, ...)`
6. **`AdjustedRate`** = `COLAdj × CoinsuranceFactor × LOIFactor`
7. **`DeductibleFactor`** = `Choose` on `Deductible` (250 → `Deductible250Factor`; else `LookupDeductibleFactor(Deductible, TotAmtInsurance, "Other Cause Of Loss")`)
8. **`FinalRate`** = `AdjustedRate × DeductibleByLocationFactor × DeductibleFactor × MultiResidentialPropSpecialCreditFactor`

**Correction:** `TotAmtInsurance` is NOT the Building's own limit — this doc previously said it was, and
that was wrong. Confirmed directly against the rule XML —
`TotAmtInsurance = StructureLimitToUse + OccupancyTotAmtInsuranceSum + SpecialClassRiskTotAmtInsurance`,
i.e. the Building's own limit **plus** every Contents/Personal Property item's limit at that location
**plus** any Special Class Risk amount. Matches CLM manual language ("total amount of insurance at each
location by adding the limits of insurance for all covered property at that location").

**Fix status, 2026-09-10:** no longer just a backlog note — now that Contents Limit exists on `Location
Inputs` (row 22), the fix is buildable and has been designed: `CoreScratchpad!C138` computes the combined
total (Building Limit + Contents Limit), and row 41 — the cell BGI's own `DeductibleFactor` reads its
Limit argument from — gets repointed to `=CoreScratchpad!C138`. Confirmed by reading the live formulas
directly (not inferred) that `C41` is *also* Broad's `DeductibleFactor` input (row 107), so this one change
fixes both forms' identical bug at once. Special Class Risk amounts are still out of scope (not built
anywhere in this project), so the combined total is Building + Contents only, not the full three-way sum.
Not yet confirmed applied in the live rater — see project memory
`project_deductiblefactor-uses-location-total-not-building-limit` for current status.

---

## 5. `Calc_Contents_BGI` tab — one row per building

Straight translation of `CauseOfLoss_PersonalProperty_RatingAlgorithms.md`'s 9-step chain
(`SetBGIRatesAndFactors`, line 2771). Note the source rules compute LOI and coinsurance *before* the
base rate — the workbook can compute columns in whatever order Excel's dependency graph wants, since no
step depends on its own sibling's column position, only on the referenced values existing in the row.

1. **`BaseRate`** — branches on `PP_Group`:
   - `Group = "YARD"` → `LookupBasicGroupIRate(constCode = 1 or 3 by YardPropertyIndicator, group="YARD", covType="PersProp")`
   - else → `LookupBasicGroupIRate(ClassCode, ConstructionCode, Group, "PersProp")`
   - gate: `RatingType = "Class"` and `ClassCode ≠ "1150"` (Builders Risk is excluded from this path for Contents), else `0`
2. **`FireSafeVaultFactor`** = `0.50` if `CovType = "Personal Property in a Vault with an Approved Fire Rating"`, else `1.0` (only when `RatingType = "Class"`; else `0.0`) — **corrected 2026-09-10**, previously documented as a `PP_FireSafeVault="Y"` checkbox, which doesn't exist; the real gate is one value on the `CovType` domain
3. **`ProtectionClassFactor`** — same table Building uses, keyed additionally on `ConstructionCode`; gate excludes `Group = "YARD"` (unless non-combustible yard property) and class codes 1751/1752
4. **`Rate`** = `((BaseRate × LCM) + SubStdConditionRate) × FireSafeVaultFactor × ProtectionClassFactor × TerritoryFactor` — round to 3dp. **No vacancy addend, no roof factor** — both intentional per §1.
5. **`COLAdj`** — if `PP_ValuablePapers = "Y"`, force `0`; else `ROUND(Rate − SprinklerLeakageExclNonSprinkleredRate, 3) × SprinklerLeakageExclSprinkleredFactor × VandalismExclFactor × StdPropPolGroupIFactor` — **note the plain `Rate` name here, not Building's `...BldgRate`** — Contents is sourced from the separate `CommercialPropertyPersonalProperty` ERC datadef group (confirmed via `FireSafeVaultFactor` two lines up, which only exists there), and that group's own `SprinklerLeakageExclNonSprinkleredRate` is already the LCM-scaled value
6. **`CoinsuranceFactor`** — forced to the 100% lookup value (not just left unchanged, unlike Building) when `AdditionalLocationsSpecialCoinsuranceProvisions` exists, `ValueReportingForm` exists, or `Coinsurance` is a reporting-form value (`Daily`/`Weekly`/`Monthly`/`Quarterly`/`Policy Year Reporting`); both gated on `ValuationType ≠ "Functional Valuation"`
7. **`LOIFactor`** = `LookupBasicGroupILOIFactorPersProp(Limit)`, unless `CovForm` is `"Legal Liability Coverage Form"` or `"Tobacco Sales Warehouse Coverage Form"` (then `1.0`)
8. **`AdjustedRate`** = `LOIFactor × COLAdj × CoinsuranceFactor`
9. **`DeductibleFactor`** — the source doc flags this as `Copy`'d from an ancestor record in ISO's rule engine rather than computed locally, with the real `Choose`-on-`Deductible` logic living in a *different* ruleset (`CommercialPropertySpecialClassRules.Rule.xml`). **Build it in Excel as the same local `Choose` used in `Calc_Building_BGI` step 7** — same table, same shape — and leave a cell comment noting this is a documented deviation from ISO's own rule-file organization, not from its math. If a real ISO engine test ever disagrees with this workbook on a Contents deductible factor, this is the first place to check.
10. **`FinalRate`** = `AdjustedRate × DeductibleByLocationFactor × DeductibleFactor` — **no multi-residential credit multiplier** (doesn't exist for Contents).

---

## 6. `Premium_Summary` formulas for this form

Following `Excel_Rater_Overview.md` §6's shared shape, for the class-rated, non-blanket,
non-Legal-Liability branch:

```
Bldg_Premium =
  ROUND(IRPMFactor × MultiPremiumAndDispersionCreditFactor × PackageModFactor
        × Calc_Building_BGI.FinalRate × (Bldg_Limit / 100), 0)
  × CyberIncidentExclusionFactorBGI × CyberIncidentExclusionCOLExcptnsFactorBGI

PP_Premium =
  ROUND(IRPMFactor × MultiPremiumAndDispersionCreditFactor × PackageModFactor
        × Calc_Contents_BGI.FinalRate × (PP_Limit / 100), 0)
  × CyberIncidentExclusionFactorBGI × CyberIncidentExclusionCOLExcptnsFactorBGI
```

Gate each formula so it only fires when the coverage-type field matches this form's supported values —
`Bldg_CovType` in (`Building`, `Builders Risk`, `Improvements and Betterments`, `Condominium
Association`) and `PP_CovForm` **not in** (`Legal Liability Coverage Form`, `Tobacco Sales Warehouse
Coverage Form`, `Class Rated Building Only, No Personal Property Coverage`) — everything else should
render `0` with a visible note, not a silent wrong number.

---

## 7. What's deliberately left out of this pass

- Legal Liability premium branch (both coverages)
- Blanket-rated premium branch (both coverages) — needs `BlktTotalFullValueAmount`,
  `FullBldgValue`/`FullPrsnlPropValue`, and the various `Blkt*` factor columns this pass left out of
  `Locations_Buildings`

Specific/Tentative rating (the only other `RatingType` value Basic Group I supports) is **not** left out
— see §9.

---

## 8. Inputs → rating output — the full picture

Sections 4–5 give you the formula one workbook column at a time. This section gives you the same
information read the other way: starting from a blank building, which inputs get touched at each stage,
and what the complete formula looks like as one if/then expression rather than a numbered list of
columns. Read this section when you want to trace *where a number came from*; read §§4–5 when you're
actually building the columns.

### 8.1 What feeds the loss cost (Building)

"Loss cost" is ISO's own term for the unloaded, company-neutral number the bureau files before any
carrier applies its own pricing — that's `BaseRate`, before the Loss Cost Multiplier ever touches it.
Everything downstream of `BaseRate` is turning that bureau number into *this policy's* rate.

| Stage | Reads from | Produces | Tab |
|---|---|---|---|
| 0 — the loss cost itself | `ClassCode`, `ConstructionCode` (→ `Rate_Tables.BasicGroupIRate`, keyed also on `"Not Applicable"`/`"Building"`) | `BaseRate` | `Locations_Buildings` → `Calc_Building_BGI` |
| 1 — turn it into a rate | `BaseRate`, `Policy.LossCostMultiplier`, `Bldg_SubStdConditionArgs` (→ `SubStdConditionRate`), `Bldg_VacantIndicator` (→ `VacantBuildingRate`), `Territory` (→ territory factor), `ProtectionClass` (→ protection class factor), `Bldg_RoofSurfacingFactorInputs` (→ roof ACV factor) | `Rate` | `Calc_Building_BGI` |
| 2 — adjust for cause-of-loss exclusions actually on the policy | `Rate`, `Bldg_SprinklerLeakageExcluded`, `Bldg_VandalismExcluded`, `Bldg_StdPropertyPolicy` (each → its own factor table) | `COLAdj` | `Calc_Building_BGI` |
| 3 — apply how the insured chose to insure | `COLAdj`, `Coinsurance`, `ClassCode`, `ValuationType`, `Bldg_Limit` (→ LOI factor) | `AdjustedRate` | `Calc_Building_BGI` |
| 4 — apply the chosen deductible | `AdjustedRate`, `Deductible`, `Bldg_Limit` (as the amount-of-insurance band), `Bldg_MultiResIndicator` | `FinalRate` | `Calc_Building_BGI` |
| 5 — turn the rate into a dollar premium | `FinalRate`, `Bldg_Limit`, `Policy.IRPMFactor`/`PackageModFactor`/`MultiPremiumAndDispersionCreditFactor` | `Bldg_Premium` | `Premium_Summary` |

### 8.2 Full formula with if/then (Building)

```
BaseRate =
    LookupBasicGroupIRate(State|CW, ClassCode, ConstructionCode, "Not Applicable", "Building")
        if RatingType = "Class" and ClassCode is non-blank and ConstructionCode ≠ 0
    else 0.0

Rate =
    if RatingType = "Class":
        ( (BaseRate × LCM) + SubStdConditionRate + VacantBuildingRate )
          × TerritoryFactor × ProtectionClassFactor × RoofSurfacingACVFactor
    elif RatingType in ("Specific", "Tentative"):
        SpecificGroupIRate × LCM × SprinklerLeakageNotExcludedFactor
    else:
        1.0
    (round to 3 dp)

COLAdj =
    round(Rate − SprinklerLeakageExclNonSprinkleredBldgRate, 3)
      × SprinklerLeakageExclSprinkleredFactor × VandalismExclFactor × StdPropPolGroupIFactor

CoinsuranceFactor =
    <left unchanged from prior value>   if ClassCode = "1150" OR ValuationType = "Functional Valuation"
    else <standard 80/90/100% lookup, or LessThan80PctMultiplicativeFactor branch>

AdjustedRate = COLAdj × CoinsuranceFactor × LOIFactor

DeductibleFactor =
    LookupDeductible250Factor("Basic Group I")   if Deductible = "250"
    else LookupDeductibleFactor(Deductible, TotAmtInsurance, "Other Cause Of Loss")
    # TotAmtInsurance = StructureLimitToUse + OccupancyTotAmtInsuranceSum + SpecialClassRiskTotAmtInsurance --
    # NOT Bldg_Limit alone -- see the correction note above. Backlogged until Contents is built.

FinalRate = AdjustedRate × DeductibleByLocationFactor × DeductibleFactor × MultiResidentialPropSpecialCreditFactor

Bldg_Premium =
    if Bldg_CovType in ("Building","Builders Risk","Improvements and Betterments","Condominium Association")
       and Bldg_IncludedInBlkt = "No":
        round(IRPMFactor × MultiPremiumAndDispersionCreditFactor × PackageModFactor × FinalRate × (Bldg_Limit/100), 0)
          × CyberIncidentExclusionFactorBGI × CyberIncidentExclusionCOLExcptnsFactorBGI
    elif Bldg_CovType = "Legal Liability":
        COLAdj × LegalLiabilityFactor × LegalLiabAddlInsurableIntFactor × (Bldg_Limit/100)
          × PackageModFactor × IRPMFactor × CyberIncidentExclusionFactorBGI × CyberIncidentExclusionCOLExcptnsFactorBGI
        [not built this pass — listed for completeness, see §7]
    elif Bldg_IncludedInBlkt = "Yes":
        [blanket branch — not built this pass, see §7]
    else:
        0.0
```

### 8.3 What feeds the loss cost (Contents)

Same five-stage shape, different inputs at almost every stage — this is the fastest way to see exactly
where Building and Contents diverge, beyond the prose in §1.

| Stage | Reads from | Produces | Tab |
|---|---|---|---|
| 0 — the loss cost itself | `ClassCode`, `ConstructionCode`, `PP_Group` (→ `Rate_Tables.BasicGroupIRate`, keyed on `Group`/`"PersProp"` instead of `"Not Applicable"`/`"Building"`), `PP_YardPropertyIndicator` (only if `PP_Group = "YARD"`) | `BaseRate` | `Locations_Buildings` → `Calc_Contents_BGI` |
| 1 — turn it into a rate | `BaseRate`, `Policy.LossCostMultiplier`, `PP_SubStdConditionArgs` (**corrected 2026-09-10: literal `Copy` of Building's own `SubStdConditionRate`, not independently computed**), `PP_CovType` (→ `FireSafeVaultFactor` — **no Building equivalent**), `ProtectionClass` + `ConstructionCode`, `Territory` (**literal `Copy` of Building's own `TerritoryFactor`**) | `Rate` | `Calc_Contents_BGI` |
| 2 — adjust for cause-of-loss exclusions | `Rate`, `PP_ValuablePapers` (zeroes the whole adjustment — **no Building equivalent**), `PP_SprinklerLeakageExcluded`, `PP_VandalismExcluded`, `PP_StdPropertyPolicy` | `COLAdj` | `Calc_Contents_BGI` |
| 3 — apply how the insured chose to insure | `COLAdj`, `Coinsurance`, presence of a Special Coinsurance or Value Reporting record (forces 100% coinsurance — stricter than Building's "leave unchanged"), `PP_CovForm`, `PP_Limit` | `AdjustedRate` | `Calc_Contents_BGI` |
| 4 — apply the chosen deductible | `AdjustedRate`, `Deductible`, `PP_Limit` | `FinalRate` — **no multi-res credit input at all** | `Calc_Contents_BGI` |
| 5 — turn the rate into a dollar premium | `FinalRate`, `PP_Limit`, the same three `Policy` factors Building reads | `PP_Premium` | `Premium_Summary` |

### 8.4 Full formula with if/then (Contents)

```
BaseRate =
    if RatingType = "Class" and ClassCode ≠ "1150":
        if PP_Group = "YARD":
            LookupBasicGroupIRate(constCode = 1 if PP_YardPropertyIndicator = "Combustible" else 3,
                                   group="YARD", covType="PersProp")
        elif ConstructionCode ≠ 0 and PP_Group is non-blank:
            LookupBasicGroupIRate(State|CW, ClassCode, ConstructionCode, PP_Group, "PersProp")
        else:
            0.0
    else:
        0.0

FireSafeVaultFactor =
    if RatingType = "Class":
        0.50   if CovType = "Personal Property in a Vault with an Approved Fire Rating"
        else 1.0
    else:
        0.0
    # corrected 2026-09-10 -- gated on this CovType value, not a PP_FireSafeVault="Y" checkbox

Rate =
    if RatingType = "Class":
        ( (BaseRate × LCM) + SubStdConditionRate ) × FireSafeVaultFactor × ProtectionClassFactor × TerritoryFactor
    elif RatingType in ("Specific", "Tentative"):
        SpecificGroupIRate × LCM × SprinklerLeakageNotExcludedFactor
    (round to 3 dp; no vacancy addend, no roof factor at any branch)

COLAdj =
    0.0   if PP_CovType = "Valuable Papers and Records - Other Than Electronic Data"
    else round(Rate − SprinklerLeakageExclNonSprinkleredRate, 3)
           × SprinklerLeakageExclSprinkleredFactor × VandalismExclFactor × StdPropPolGroupIFactor

CoinsuranceFactor =
    <forced to the 100% lookup value>
        if (a SpecialCoinsuranceProvisions or ValueReportingForm record exists
            OR Coinsurance in ("Daily","Weekly","Monthly","Quarterly","Policy Year Reporting"))
           and ValuationType ≠ "Functional Valuation"
    else <standard lookup>

LOIFactor =
    <blanket copy>                                   if PP_IncludedInBlkt = "Yes" and BlktIDNum > 0
    elif PP_CovForm not in ("Legal Liability Coverage Form","Tobacco Sales Warehouse Coverage Form")
         and ConstructionCode ≠ 0:
        LookupBasicGroupILOIFactorPersProp(PP_Limit)
    else:
        1.0

AdjustedRate = LOIFactor × COLAdj × CoinsuranceFactor

DeductibleFactor =
    <same local Choose as Building's — see §5 step 9 for why this deviates from ISO's own file layout>

FinalRate = AdjustedRate × DeductibleByLocationFactor × DeductibleFactor
    (no multi-residential credit multiplier at any branch)

PP_Premium =
    if PP_CovForm not in ("Legal Liability Coverage Form","Tobacco Sales Warehouse Coverage Form",
                           "Class Rated Building Only, No Personal Property Coverage")
       and PP_IncludedInBlkt = "No":
        round(IRPMFactor × MultiPremiumAndDispersionCreditFactor × PackageModFactor × FinalRate × (PP_Limit/100), 0)
          × CyberIncidentExclusionFactorBGI × CyberIncidentExclusionCOLExcptnsFactorBGI
    elif PP_CovForm = "Legal Liability Coverage Form":
        IRPMFactor × PackageModFactor × (PP_Limit/100) × LegalLiabAddlInsurableIntFactor × LegalLiabFactor
          × COLAdj × CyberIncidentExclusionFactorBGI × CyberIncidentExclusionCOLExcptnsFactorBGI
        [not built this pass — listed for completeness, see §7]
    elif PP_IncludedInBlkt = "Yes":
        [blanket branch — not built this pass, see §7]
    else:
        0.0
```

---

## 9. The Specific/Tentative rating path

**Basic Group I is the only form, in any coverage, with a `RatingType` branch at all.** Confirmed
directly in the source doc's own four-way comparison table: Basic Group II, Broad, and Special each show
"none — single path" for this row. Nothing needs building for those three forms — there's no gate to add,
because ISO's own rules never test `RatingType` inside them.

### What Class-rated skips, and what Specific/Tentative-rated skips instead

Class rating is the path this document has built end-to-end so far: a class/construction lookup into
`BasicGroupIRate`, territory and protection-class multipliers, the substandard-condition and
vacant-building addends. **Specific/Tentative rating skips all of that** — no class lookup runs at all
(Building's `SetBasicGroupIBaseRate` only executes `if RatingType = "Class"`) — and substitutes a single
pre-determined rate, `SpecificGroupIRate`, multiplied by the loss cost multiplier and a sprinkler-leakage
factor.

| | Building | Contents |
|---|---|---|
| Formula | `SpecificGroupIRate × LCM × SprinklerLeakageNotExcludedFactor × RoofSurfacingACVFactor` | `SpecificGroupIRate × LCM × SprinklerLeakageNotExcludedFactor` — **no roof factor**, consistent with every other Contents formula in this document |
| Gate | explicit `RatingType = "Specific"` or `RatingType = "Tentative"` test, **plus a third `Otherwise` branch** that sets the rate to a flat `1.0` for any other value | `RatingType ≠ "Class"` — a broader gate than Building's; any non-Class value routes here, not just the two named ones |
| Downstream steps | unchanged — COL adjustment, coinsurance/LOI, deductible all run exactly as they do for Class-rated buildings, reading whichever `Rate` this branch produced | unchanged |

### `SpecificGroupIRate` — a genuinely open question, not a filed lookup

**No `Set` rule and no `Lookup` rule populates `SpecificGroupIRate` anywhere in either coverage's traced
rating-algorithm document.** This isn't a case of "confirmed present but not row-counted" the way several
other tables in this project turned out to be — it's a value the source docs never trace the origin of at
all. The most likely explanation, by the shape of the concept (a "specific" or "tentative" rate is an
insurance-industry term for an individually-computed or provisional rate an underwriter assigns outside
the standard class tables), is that it's a **user- or schedule-entered value**, not an ERC rate-table
lookup — but that is inference from the name and rating-industry convention, not a confirmed fact from
either source doc. **Treat this as an open question requiring verification against the actual rule XML
before real business use**, the same standing this project gives every other unresolved claim.

Build it in the workbook as a user-entered column (`Bldg_SpecificGroupIRate` / `PP_SpecificGroupIRate`)
with a visible comment flagging the open question, rather than a `Rate_Tables` lookup — that's the
better-supported guess, but it is still a guess.

### `Locations_Buildings` additions for this path

| Field | Feeds | Notes |
|---|---|---|
| `RatingType` | already on the tab (`Excel_Rater_Overview.md` §4) — now genuinely used as an enum: `"Class"`, `"Specific"`, `"Tentative"`, or (Building only) anything else, which falls to the `1.0` catch-all | |
| `Bldg_SpecificGroupIRate` | Building's Specific/Tentative `Rate` formula | user-entered — see the open question above |
| `PP_SpecificGroupIRate` | Contents' Specific/Tentative `Rate` formula | same open question, separate column since a building's Building and Contents specific rates need not match |

### `Rate_Tables` addition for this path

| Table | Keys | CW rows filed? |
|---|---|---|
| `SprinklerLeakageNotExcluded` (Building) / `SprinklerLeakageNotExcludedFactor` (Contents) | State\|CW, `"Y"` | **Building: confirmed present by the original sweep, but not independently row-counted** — flag per the standing discipline (`Excel_Rater_Overview.md` §5) until checked. **Contents: confirmed with a real CW row** in `PersonalProperty_ERC_Tables.md` — the more reliable of the two confirmations, since it was checked directly rather than swept. |

### `Calc_Building_BGI` / `Calc_Contents_BGI` — the Specific/Tentative branch

Add this as an explicit second branch on each tab's `Rate` column (step 2 for Building, step 4 for
Contents), rather than only documenting it in the quick-reference formula:

```
Rate =
    if RatingType = "Class":
        <the Class-rated formula already built>
    elif RatingType in ("Specific","Tentative"):     # Building; Contents uses RatingType <> "Class"
        SpecificGroupIRate × LCM × SprinklerLeakageNotExcludedFactor  [× RoofSurfacingACVFactor, Building only]
    else:
        1.0    # Building only — Contents' source doc states no equivalent catch-all
```

Everything downstream of `Rate` — `COLAdj`, `AdjustedRate`, `FinalRate`, and the premium formula — is
**unchanged** for this path; a Specific/Tentative-rated building's `COLAdj` reads the same
`SprinklerLeakageExclNonSprinkleredBldgRate`/`...SprinkleredFactor`/`VandalismExclFactor` inputs a Class-rated
building's does, just starting from a different `Rate`.

---

## Correction, 2026-09-04 — the sprinkler-exclusion rate name differs between Building and Contents

**Building's** `COLAdj` subtracts `SprinklerLeakageExclNonSprinkleredBldgRate`, not the raw filed
`SprinklerLeakageExclNonSprinkleredRate`. Verified directly against
`CommercialPropertyStructureRules.Rule.xml`: `SetSprinklerLeakageExclNonSprinkleredBldgRate`
computes `ROUND(SprinklerLeakageExclNonSprinkleredRate × LossCostMultiplier, 3)` — the same
raw-rate-times-LCM-then-round pattern `VacantBuildingRate` uses two lines up in the `Rate` formula —
and it's that scaled, rounded value that `SetBasicGroupICauseOfLossAdjustment` actually subtracts.

**Contents does NOT follow Building's naming — an earlier pass over this file wrongly applied
Building's `...BldgRate` rename to Contents too, since it was confirmed the source for §5/§8.4 is a
different rule file entirely.** `FireSafeVaultFactor` (used throughout Contents' formulas above)
doesn't exist anywhere in `CommercialPropertyStructureRules.Rule.xml` — it lives only in
`CommercialPropertyPersonalPropertyRules.Rule.xml`, confirming Contents here is sourced from the
**separate `CommercialPropertyPersonalProperty` ERC datadef group**, not a sub-branch of Structure.
That datadef group names its own raw filed value `SprinklerLeakageExclNonSprinkleredBaseRate`, and
`SprinklerLeakageExclNonSprinkleredRate` (no suffix) is already the LCM-scaled result — so Contents'
formulas correctly keep the plain `Rate` name; don't rename it to match Building's.

Both datadef groups read the identical filed CW rate (0.0006) and both scale it by LCM exactly once
before subtracting — the *mechanism* is the same, only the local datadef naming differs between the
two rule files. Worth building in deliberately either way, not glossing over: at LCM = 1.0 this
rounding step inflates the filed rate (0.0006) up to 0.001 — a ~67% jump, purely from a
sub-thousandth rate crossing the 3-decimal rounding boundary. That's the filed rule's own math, not
a data error to fix.

Also confirmed while tracing this: `SprinklerLeakageExclSprinkleredFactor` (the term that multiplies
right after) is **not** a general modifier that always applies alongside the rate subtraction — it's
gated on the *opposite* `SprinklerSystem` selection (`Rated as Sprinklered; <50%/>50% of Value
Exposed to Sprinklers`, vs. the rate subtraction's `Sprinklered Building, but Not Rated as
Sprinklered`), both additionally requiring a Sprinkler Leakage Exclusion schedule entry to exist. The
two are mutually exclusive alternatives — only one is ever actually "live" for a given risk, the
other sits at its no-op default (`0.0` / `1.0`).

**`SprinklerLeakageExclSprinkleredFactor` can never actually be live for a Class-rated building.**
Checked the `SprinklerSystem` field's own domain list directly: under `RatingType = "Class"` the
only options are `None` and `Sprinklered Building, but Not Rated as Sprinklered` — the "Rated as
Sprinklered; <50%/>50%" options that trigger this factor only exist under `RatingType = "Specific"`
or `"Tentative"`. Confirmed universal, not Building-specific — a second, broader domain table
(covering Building and PP, Condo, Legal Liability, SPP, Tobacco Warehouse CovForms) shows the
identical restriction across every one of them. Worth building this into the dropdown/input logic
directly: this factor only ever has a chance to multiply to something other than `1.0` on a
Specific/Tentative-rated risk.

Separately, confirmed against the CW manual (`CF-MU-2026-RU-001-C.pdf`, Rule 74.A.3.c, page 133 —
Section VI Causes of Loss Form Rules, squarely Basic Group I, not Earthquake — see the "Sprinkler
Leakage – Earthquake Extension" on the next page for a genuinely different, unrelated provision):
"Subtract the rate shown in the multistate rates from the Basic Group I rate." This is a **flat**
subtraction from the fully-loaded rate (post Territory/Protection Class/Roof), not a proportional
one — the filed rule doesn't scale this credit by those factors, unlike `VacantBuildingRate`, which
sits *inside* the base build-up and does get scaled by them. That asymmetry is real and by design,
not an engine quirk.

---

## Correction, 2026-09-10 — how much of Contents is actually independent of Building, factor by factor

A close pass over every non-`BaseRate` input to Contents' `Rate` and `COLAdj` steps, verified against
`CommercialPropertyPersonalPropertyRules.Rule.xml` directly. The honest picture is a genuine mix — some
factors are literal copies of Building's value, some are independently computed but read the same
underlying data (so usually land on the same number anyway), and some are Contents-only with no Building
equivalent at all. Don't assume any one pattern applies uniformly across the chain.

**Literal ancestor copies — Contents computes nothing, just inherits Building's already-computed value:**
- `TerritoryFactor` (`BasicGroupIRatingTerrFactor`) — neither coverage computes this independently;
  both `Copy` the same field from a shared ancestor higher in the hierarchy (Building 2 levels up,
  Contents 4). Genuinely the same value, not just the same calculation.
- `SubStdConditionRate` — Building sums five separate sub-condition rates (A–E: Heating & Cooking,
  Wiring, Conversion, Physical Condition & Housekeeping, Exposure), each with its own `BaseRate`
  lookup. Contents' `SetSubStdConditionRate` is a single unconditional `Copy` from
  `../../../../SubStdConditionRate` — Building's already-summed result, no independent A–E logic at all.
- `StdPropPolGroupIFactor` — a pure `Copy` from eight levels up the ancestor chain
  (`../../../../../../../../StdPropPolBasicGroupIFactor`), the one true copy among `COLAdj`'s four inputs.

**Independently computed by Contents, but reading the same underlying CW data — usually equal, not
because they're copied, but because there's no coverage-type key differentiating them:**
- `SprinklerLeakageExclNonSprinkleredRate`/`...BaseRate` and `SprinklerLeakageExclSprinkleredFactor` —
  Contents has its own `Set`/`Lookup` rules, its own schedule-existence gate
  (`CommercialPropertySprinklerLeakageExclusionPrsnlPropTable`, distinct from Building's own
  `...Table`), but the actual rate `Lookup` is byte-for-byte identical to Building's (same
  `SprinklerLeakageExclNonSprinkleredRateDef` table, same `State|CW,"Y"` keys, no `CovType` dimension).
- `VandalismExclFactor` — same story, its own rule and its own `...PrsnlProp` schedule table.

**Genuinely Contents-only, no Building equivalent:**
- `FireSafeVaultFactor` — **correction to this doc's own earlier text**: not gated on a
  `PP_FireSafeVault="Y"` checkbox as previously documented. The real gate is
  `CovType = "Personal Property in a Vault with an Approved Fire Rating"`, one specific value out of
  Contents' `CovType` domain (see the Domain Tables note below). Flat CW lookup = 0.50. Defaults to
  `0.0` (not `1.0`) when `RatingType≠"Class"` — inert today since the Specific/Tentative `Rate` branch
  never multiplies by it, but the same zero-default trap flagged elsewhere in this project.
- `ProtectionClassFactor` — shares Building's exact lookup table and keys (`State|CW, ProtectClass,
  ConstructionCode`), so the number matches when both apply, but Contents' gate has one condition
  Building has no equivalent for: excluded when `Group="YARD"` *unless*
  `YardPropertyIndicator="Yard Property - Non Combustible"` — non-combustible yard-stored property
  still gets normal protection-class treatment, combustible yard property doesn't.

**A related correction on the Sprinkler/Vandalism Exclusion schedule entries themselves — don't
over-read "separate rule file" as "separately electable per coverage."** Checked the actual form
fields (`Form Fields/Fields.FormField.csv`), not just the rule XML: the "Sprinkler Leakage Exclusion"
and "Vandalism Exclusion" endorsement pages are **identical across all their Structure/PersonalProperty/
BusnIncome/SpecialClass variants** — every one has only `Premises Number` and `Building Number`, no
coverage-type selector at all. This is almost certainly **one election per building**, mirrored
internally into each `DataDefGroup`'s own schedule table for the rule engine's benefit, not something a
user can genuinely elect independently for Building vs. Contents. An earlier pass in this same session
over-claimed real-world per-coverage divergence from the existence of separate rule files alone —
correcting that here.

**The `Vacancy Permit` schedule is a real exception to that correction — it genuinely IS separately
electable per coverage.** Unlike the two Exclusion endorsements above, `CommercialPropertyVacancyPermit`
(Building) and `CommercialPropertyVacancyPermitPrsnlProp` (Contents) are full, independent schedule
pages — each with its own `Vandalism`/`SprinklerLeakage` Excepted-Causes-of-Loss Yes/No selectors, its
own Permit Period dates, and its own `Premium` field. A real insured can elect different excepted
causes of loss for a vacant building's Building coverage versus its Contents coverage.

**Where the `CovType`/`CovForm` domain values referenced above actually come from:** a `Domain Tables`
folder in the ERC package (sibling of `Rate Tables` and `Rules`) — `DomainCovTypeBldg`, `DomainCovForm`,
`DomainCovTypePrsnlProp` — the real, cascading dropdown lists (Contents' `CovType` domain depends on
both `PolicyType` and `CovForm`). This is the authoritative source, not a rule-XML grep of literal
comparisons, which only surfaces the subset of values that happen to trigger distinct rating treatment.
Built out in `CF_Eligible_CoverageTypes.xlsx` (`Supporting Tables\`).

---

## Correction, 2026-09-10 (cont'd) — Deductible chain, LOI gate asymmetry, MultiRes, and Cyber

More factors run down from the same "is this a copy, a shared-table independent computation, or genuinely
distinct" question, verified against the rule XML the same way as everything above.

**More literal ancestor copies — added to the running list:**
- `DeductibleByLocationFactor` — Contents' `Set` rule is an unconditional `Copy` from Building's
  already-computed value, same pattern as `TerritoryFactor`/`SubStdConditionRate`/`StdPropPolGroupIFactor`.
- `DeductibleFactorBasicGroupI` — same story: Contents' `SetDeductibleFactorBasicGroupI` is a literal
  `Copy` from `../../../../DeductibleFactorBasicGroupI`, Building's own result, four ancestor levels up.
  Building does the real computation (`LookupDeductibleFactor` against the `"Basic Group I"` slice of
  `DeductibleFactor.RateTable.csv`, plus `LookupDeductible250Factor` against the `"Basic"` key of
  `Deductible250Factor.RateTable.csv` for the 250-deductible branch); Contents never computes this itself.
  Built out in `BGI_DeductibleFactor_TotAmtInsuranceFix.xlsx` (`Supporting Tables\`).

**`LOIFactor`'s gate has a genuine asymmetry worth flagging on its own** (`SetBasicGroupILOIFactor`):
excluded (falls to `1.0`) when `../../../../CovType = "Legal Liability"` **(Building's own `CovType`, an
ancestor field, not Contents')** OR `CovType = "Tobacco Sales Warehouses"` **(Contents' own `CovType`)** OR
`ConstructionCode = 0`. Two conditions in the same `And`, reading from two different `DataDefGroup`s — easy
to misread as both checking the same field. Confirmed via the ERC rule XML directly, not inferred. Table
itself (`BasicGroupILOIFactorPersProp`) is genuinely 3-key (State + Limit + ConstructionCode) and CW-only —
zero states file their own rows. Built out in `BGI_Contents_LOIFactor.xlsx`.

**`MultiResidentialPropSpecialCreditFactor` — confirmed Building-only, no Contents equivalent at all.**
Searched `CommercialPropertyPersonalPropertyRules.Rule.xml` directly for any `Set`/`Copy`/reference —
zero hits. Building's `FinalRate` multiplies by it (line 125 above); Contents' `FinalRate` doesn't include
it in the chain at all (line 158) — not a zeroed-out or defaulted factor, it's simply absent from
Contents' formula. Matches the existing line-158 note; recorded here as a confirmed finding, not new
information, so the "Building-only, no Contents mirror" pattern for this factor is settled.

**Cyber Incident Exclusion Factors (`CyberIncidentExclusionFactorBGI` /
`CyberIncidentExclusionCOLExcptnsFactorBGI`) — a genuinely different pattern from everything else on this
list: one shared value, computed once, not copied.** Unlike the ancestor-copy factors above (where Contents
copies Building's *already-computed* result), this pair is computed exactly once, at the **policy level**
(`DataDefGroup="CommercialProperty"` in the master `CommercialPropertyRules.Rule.xml`, not the per-coverage
Structure/PersonalProperty files). Both Building's and Contents' premium formulas separately reach up their
own ancestor chain (different path depths — Building's `../../../../../CyberIncidentExclusionFactorBGI` vs.
Contents' `../../../../../../../../../CyberIncidentExclusionFactorBGI` — same field, same single value) to
multiply it into their own premium. There is no Building-vs-Contents comparison to make here because there
is only ever one number.
- `CyberIncidentExclusionFactorBGI`: only runs the real lookup if the Cyber Incident Exclusion endorsement
  table exists on the risk; otherwise defaults to `1.0` (no-op). When it runs: keyed on
  `State + "Basic Group I"`, CW = `0.995`.
- `CyberIncidentExclusionCOLExcptnsFactorBGI`: narrower gate — needs the "With Ensuing Causes of Loss
  Exceptions" table to exist AND both `CyberTypeOfLimitPropertyDamage` and `CyberIsAggregateLimit`
  non-blank; else `1.0`. When it runs: keyed on `State + "Basic Group I" + TypeOfLimit + IsAggregateLimit`,
  CW mostly `1.0` except Sublimit/Non-Aggregate = `0.998`.
- Neither factor is built anywhere in this project — the Cyber Incident Exclusion endorsement election
  itself doesn't exist yet on `Location Inputs`. If/when it's wired in, Contents should point at the exact
  same `CoreScratchpad` cell Building uses, not a separate lookup — there's nothing to independently
  compute.

---

## Remaining steps

1. You review this document against `Excel_Rater_BasicGroupII.md` — confirm the split reads cleanly
   and nothing from the original combined guide got lost or duplicated.
2. Flag whether `SpecificGroupIRate`'s open question (§9) needs resolving against the actual ERC rule
   XML before you treat it as safely user-entered, or whether the inference is good enough for now.
3. Next coverage form is your call — Broad, Special, or the Legal Liability/blanket branches for the
   two forms now built.
4. Nothing gets built until you say go.
