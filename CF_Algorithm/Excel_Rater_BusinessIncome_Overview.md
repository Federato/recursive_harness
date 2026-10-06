# Excel Rater Build Guide — Business Income Overview

**Written:** 2026-09-02.

**Source material:** `CauseOfLoss_BusinessIncome_RatingAlgorithms.md` + `BusinessIncome_ERC_Tables.md`,
cross-checked against `CFCW20260601V01`. See `Excel_Rater_Overview.md` for the Building/Contents workbook
shell this document extends, and `Excel_Rater_BasicGroupI.md` / `...BasicGroupII.md` / `...Broad.md` /
`...Special.md` for the Building/Contents forms this coverage's own forms are compared against
throughout.

---

## 1. Why Business Income needs its own overview, not just four more calc tabs

Business Income is a genuinely different shape of coverage from Building or Contents, not just a third
"coverage block" following the same pattern. Three structural facts drive every decision in this
document set:

**It's one coverage, not two.** Building splits into Building and Contents because ISO rates them as
separate coinsured items on the same location. Business Income is a single "time element" coverage,
always attached to a Structure/Building record (confirmed in the schema —
`CommercialPropertyBusinessIncomeTable` is declared inside `CommercialPropertyStructure`). There is no
Business-Income equivalent of the Contents split — **each form gets one calc tab, not two.**

**Three of its five forms don't compute their own base rate at all.** Basic Group I, Basic Group II, and
Earthquake read the coinsured Building's *already-computed* rate datadefs
(`BasicGroupIBaseRate`, `BasicGroupIISymbolToUse`/`BasicGroupIIRatingTerr`, `EQBaseRate`) directly, rather
than running their own class/construction/territory lookup. **Rate the Building first.** This workbook's
`Calc_Building_BGI` and `Calc_Building_BGII` tabs, already built, become upstream dependencies for the
Business Income tabs in this document set — the first time in this workbook that a coverage's calc tab
reads another coverage's calc tab rather than only `Locations_Buildings` and `Rate_Tables`. Only Broad
and Special have their own dedicated Business-Income base-rate tables.

**The premium shape is far simpler and far more uniform than Building's.** Every Business Income premium
file (Basic Group I, II, Broad, Special) has exactly **two** branches — scheduled or blanket — with no
Legal Liability, no Leasehold Interest, no per-form structural divergence the way Building's Special
premium file diverges from the Basic-form pattern. There is also **no Limit-of-Insurance factor, no
deductible factor of any kind, and no `MultiPremiumAndDispersionCreditFactor`** in any Business Income
premium formula — three inputs every Building premium formula reads that Business Income's never does.
This isn't missing data; it's confirmed structurally absent from the rule file.

**Earthquake is scoped out of this pass.** It's a real fifth rate chain (`SetEQRatesAndFactors` runs
unconditionally), but it has no standalone non-Agreed-Value premium coverage file — the only way it
charges premium in this package is through the Agreed Value coverage, using a `(Factor - 1) × Rate ×
(Limit/100)` incremental-surcharge shape that appears nowhere else in Building or Contents rating. That's
a genuinely different premium mechanism, not just a fifth form of the same mechanism, and is left for a
later pass — see `Excel_Rater_BusinessIncome_BasicGroupI.md` §7 and the source doc's own "open question."

---

## 2. Workbook structure — what Business Income adds

| Tab | Grain | New, or extends an existing tab? |
|---|---|---|
| `Policy` | one row per policy | unchanged |
| `Locations_Buildings` | one row per building | extended — new Business-Income-specific block, §3 |
| `Rate_Tables` | one block per ERC table | extended — new Business-Income-specific tables, §4 |
| `Calc_BusinessIncome_BGI` | one row per building | **new** — reads `Calc_Building_BGI.BasicGroupIBaseRate` |
| `Calc_BusinessIncome_BGII` | one row per building | **new** — reads `Calc_Building_BGII`'s symbol/territory |
| `Calc_BusinessIncome_Broad` | one row per building | **new** — self-contained, own base-rate table |
| `Calc_BusinessIncome_Special` | one row per building | **new** — self-contained, own base-rate tables |
| `Premium_Summary` | one row per building | extended — four more premium columns, §6 |

No `Calc_Contents_BusinessIncome*` tabs — see §1. No `Calc_BusinessIncome_Earthquake` tab this pass — see
§1's Earthquake note.

---

## 3. `Locations_Buildings` additions — Business Income block

| Field | Feeds | Notes |
|---|---|---|
| `BI_CovType` | base-rate branch selection (Broad, Special), `Factor` selection (Basic Group I/II) | `"Business Income Without Extra Expense"`, `"Business Income With Extra Expense"`, or `"Extra Expense Only"` — a genuinely different classification from Building's `CovType`, reusing the column name only by convention |
| `BI_TypeOfRisk` | `BusnIncomeFactor` lookup key (Basic Group I/II's shared `Factor`) | e.g. `"Mercantile and Non-manufacturing"`; a `"Combined..."` value triggers the blended two-lookup branch — see §5 |
| `BI_MaxPeriod` (Y/N) | first-priority branch of `SetFactor` | when Y, `Factor` comes from `MaxPeriodOfIndemnityFactor`, not `TypeOfRiskFactor` |
| `BI_MonthlyLimitOfIndemnity` | second-priority branch of `SetFactor` | `"Not Applicable"` or a real value; a real value routes `Factor` through `MonthlyLimitOfIndemnityFactor` instead |
| `BI_Coinsurance` | resolved into `CoinsuranceToUse`, the `BusnIncomeFactor` lookup key | **not** simply `Coinsurance` copied down — see §5's note on `SetCoinsuranceToUse`; for this pass, enter the resolved value directly since the blanket-rating-table scan behind it is out of scope |
| `BI_Limit` | premium formula, all four forms | |
| `BI_IncludedInBlkt` (Y/N) | premium branch gate | Business-Income-specific, distinct from `Bldg_IncludedInBlkt` |
| `BI_ApartmentCondoIndicator` (Y/N) | Special form's theft-classification lookup key | feeds `SpecialIncludingTheftTypeRisk`, no Building equivalent |
| `BI_BldgIncludedInOperationalUnit` (Y/N) | Basic Group I/II's blanket/max-period base-rate branch gate | |
| `BI_TheftExclusionAttached` (Y/N) | Special form's theft-exclusion factor | Business Income's own instance of CP 10 33, tracked separately from `TheftExclusionAttached` on the Building side |

Every Business Income form reuses `ClassCode` (Builders Risk detection), `ConstructionType` (Broad and
Special's own base-rate keys), and `Coinsurance`/`Deductible` are **not** reused — Business Income has no
deductible-factor rating at all (§1).

**Corrected 2026-10-06** (`cf-bgi-chains.html` BI review #33; `cf-broad-chains.html` BI review #31;
`cf-special-chains.html` BI review #30, #31, #37). Four fixes to the table above. `BI_BldgIncludedInOperationalUnit`
gates the **operational-unit** branch, not a blanket branch. `BI_IncludedInBlkt` is not Y/N in effect:
anything but "No", blank included, takes the blanket side, and a blank prices Group I, Group II and
Broad / Special at **$0, "rated"**. A blank `BI_CovType` zeroes BI Special, and Group I and II with it
(Broad reads "All Other" instead). `BI_ApartmentCondoIndicator` is **not an input**: ISO derives it from the
building's class code (0300–0343 → "Yes") and overwrites a submitted value.

---

## 4. `Rate_Tables` additions — Business Income block

**Shared across Basic Group I and II:**

| Table | Keys | CW rows filed? |
|---|---|---|
| `BaseRateAdjustmentFactor` | State\|CW, cause-of-loss string (`"Basic Group I"` / `"Basic Group II"`) | **No — header-only, confirmed empty** |
| `BusnIncomeFactor` | State\|CW, `BI_CovType`, `BI_TypeOfRisk`, `CoinsuranceToUse` | Yes — 131 rows |
| `MaxPeriodOfIndemnityFactor` | State\|CW, ... | Yes — 22 rows |
| `MonthlyLimitOfIndemnityFactor` | State\|CW, ... | Yes — 60 rows |
| `ExtraExpenseFactor` | State\|CW, `ExtraExpnLimitOnLossPymts` | Yes — 4 rows |
| `SprinklerLeakageExclNonSprinkleredRate` (this datadef group's OWN LCM-scaled value — raw filed rate lives in `SprinklerLeakageExclNonSprinkleredBaseRate` instead; do not confuse with Structure's `...BldgRate` naming, see `Excel_Rater_BasicGroupI.md`), `SprinklerLeakageExclSprinkleredFactor`, `VandalismExclFactor` | State\|CW | Yes |
| `WindstormOrHailExclFactor` | State\|CW | Yes — 4 rows (Basic Group II only) |
| `BldrsRiskFactorBusnIncome` | State\|CW, `"Y"` | Yes — 1 row (the `BuildersRiskFactor` that replaces Building's `StdPropPolGroupI/IIFactor` in Business Income's COL adjustments) |

**Broad-only:** reuses `BroadFormBaseRate`, already introduced in `Excel_Rater_Broad.md` — same table,
Business-Income-specific `covType` values (`"Business Income Without Extra Expense"`, `"All Other"`).
Confirmed 30 Business Income rows present, including Frame at 0.011.

**Special-only:**

| Table | Keys | CW rows filed? |
|---|---|---|
| `SpecialFormIncldgTheftTimeElementBaseRate` | State\|CW, `ConstructionType`, `BI_CovType`, `SpecialIncludingTheftTypeRisk` | Yes — 24 rows |
| `SpecialFormBldrsRiskTimeElementBaseRate` | State\|CW, `"Y"` | Yes — 1 row, CW = 0.018 |
| `SpecialLeaseHoldTimeElementTheftExclusionFactor` | State\|CW, `BI_ApartmentCondoIndicator` | Yes — 2 rows |

**Not built this pass (Earthquake-scoped):** `EQSprinklerLeakageOnlyBldgFactor`, `StoryModFactorTimeElement`,
`EarthquakeSubLimitTimeElementFactor`, `AgreedValueFactorBusnIncome`, `ExtendedPeriodFactor` — all real,
row-confirmed tables, held for when Earthquake/Agreed Value/Extended Period of Indemnity get built.

### The one genuinely good and one genuinely bad piece of news

**Good:** unlike Basic Group I/II, **Broad and Special's own base-rate tables both have real CW rows.**
Business Income's Broad and Special forms are resolvable at the countrywide level, same as Building's
Broad already was.

**Bad, and compounding:** Basic Group I and II Business Income are **doubly unresolvable**. Not only is
`BaseRateAdjustmentFactor` header-only, but the Building rate it multiplies —
`BasicGroupIRate`/`BasicGroupIIRate` — is *also* header-only (confirmed independently in both
`Excel_Rater_BasicGroupI.md` and `...BasicGroupII.md`). A state filing has to cover **both** tables before
either Basic form's Business Income rate resolves; filing one without the other still produces a blank.
Flag this in the workbook as a two-part gap, not a single flag — a reviewer checking only
`BaseRateAdjustmentFactor` might miss that the Building-side table is also empty.

**Corrected 2026-10-06** (`cf-bgi-chains.html` BI review #41; `cf-bgii-chains.html` BI review #43). Both
tables are state-filed in practice (adjustment factor: Group I IN 0.85; Group II UT 0.7, IN 0.75), and BI
Group I and II price normally in IN and UT. Header-only CW is the normal state-filed pattern, not a gap.

---

## 5. The shared "Factor" (Basic Group I / II only)

Business Income's functional replacement for Building's flat `CoinsuranceFactor` — folds coinsurance
percentage, type-of-risk classification, coverage type, and two special-case periods into one factor,
applied **only** to Basic Group I and Basic Group II. Broad and Special never multiply by it at all
(confirmed by grepping both forms' rule files for `CoinsuranceToUse`/`TypeOfRiskFactor`/`BusnIncomeFactor`
— no matches).

```
Factor =
    MaxPeriodOfIndemnityFactor      if BI_MaxPeriod = "Y"
    elif BI_MonthlyLimitOfIndemnity <> "Not Applicable":
        MonthlyLimitOfIndemnityFactor
    elif BI_CovType = "Extra Expense Only":
        ExtraExpenseFactor
    else:
        TypeOfRiskFactor = Lookup(BusnIncomeFactor: CoinsuranceToUse, BI_CovType, BI_TypeOfRisk)
```

Build this once, on a helper column (either on `Locations_Buildings` or as a shared column on both
`Calc_BusinessIncome_BGI` and `Calc_BusinessIncome_BGII`, since both read the identical value) — don't
duplicate the four-way `Choose` in two places.

**`CoinsuranceToUse` is not simply `Coinsurance` copied down.** In ISO's own rules it's resolved by
scanning the policy-level blanket rating table for the matching unit, or copying a blanket-level
coinsurance value directly for multi-unit submissions. That scan is out of scope for this pass — enter
`BI_Coinsurance` directly as the resolved value (§3), with a comment noting the simplification.

**`TypeOfRiskFactor`'s "Combined" branch** — when `BI_TypeOfRisk` is a `"Combined..."` value, the lookup
becomes a percentage-weighted blend of two `TypeRiskCombination1Factor`/`TypeRiskCombination2Factor`
lookups rather than a single table hit. Not built this pass — flag as a known simplification in the
`Factor` helper column (treat `"Combined"` risk types as unsupported for now, same as this project treats
any out-of-scope branch).

---

## 6. `Premium_Summary` — shared Business Income premium shape

Every Business Income form's premium formula shares this shape — confirmed structurally identical across
Basic Group I, II, Broad, and Special (Special is **not** a structural outlier here the way it is for
Building):

```
BI_<Form>_Premium =
    if BI_IncludedInBlkt = "No":
        ROUND(ROUND(IRPMFactor × PackageModFactor × Calc_BusinessIncome_<Form>.FinalRate × (BI_Limit/100), 0), 0)
          × CyberIncidentExclusionFactor<Form> × CyberIncidentExclusionCOLExcptnsFactorBusnIncome<Form>To Use
    elif BI_IncludedInBlkt = "Yes" and BlktTotalFullValueAmount > 0:
        ROUND(ROUND(IRPMFactor × PackageModFactor × Blkt<Form>AvgRate
              × (FullBusnIncomeValue/BlktTotalFullValueAmount) × (BlktLimit/100), 0), 0)
          × CyberIncidentExclusionFactor<Form> × CyberIncidentExclusionCOLExcptnsFactorBusnIncome<Form>ToUse
        [blanket branch — not built this pass, see each form's own §7]
    else:
        0.0
```

**Three things every Building premium formula has that this one doesn't, worth stating plainly since
their absence is easy to mistake for an oversight when transcribing from the Building pattern:**

- No `MultiPremiumAndDispersionCreditFactor` — populated during shared prep, never multiplied into the
  coverage-level premium for any of the five forms.
- No Limit-of-Insurance factor step anywhere — the formula multiplies the final rate directly by
  `Limit / 100`.
- No Legal Liability branch, no Leasehold Interest carve-out, no "otherwise zero" fourth branch — only
  scheduled and blanket exist, because Business Income has neither coverage type.

`IRPMFactor`/`PackageModFactor`/both cyber factors are read **seven** levels up the datadef tree here,
versus Building's five — a mechanical consequence of Business Income nesting inside Structure, not a
rating difference.

---

## 7. Documents in this set

| Document | Covers | Status |
|---|---|---|
| `Excel_Rater_BusinessIncome_Overview.md` (this file) | Shared Business Income shell | Current |
| `Excel_Rater_BusinessIncome_BasicGroupI.md` | Basic Group I | Built |
| `Excel_Rater_BusinessIncome_BasicGroupII.md` | Basic Group II | Built |
| `Excel_Rater_BusinessIncome_Broad.md` | Broad | Built |
| `Excel_Rater_BusinessIncome_Special.md` | Special | Built |
| — | Earthquake / Agreed Value / Extended Period of Indemnity | Not started — genuinely different premium mechanism, see §1 |
| — | Special Class Business Income (parallel datadef group, attached to Special Class instead of Structure) | Not started — existence only confirmed in the source doc |
| `Excel_Rater_RatingPaths_Checklist.md` | Every rating path across Building, Contents, and this coverage, checked off at a finer grain than this table | Current |
| `Excel_Rater_FullBuildout_Scope.md` | Whole-line scope — every coverage, blanket rating, Earthquake/Flood, circular verification, jurisdiction/edition breadth | Current |

## Remaining steps

1. You review this overview against `Excel_Rater_Overview.md` — confirm the "one calc tab per form, not
   two" simplification and the cross-tab dependency on `Calc_Building_BGI`/`BGII` read cleanly.
2. All four non-Earthquake forms are built for Business Income. Next is your call — Earthquake/Agreed
   Value, Special Class Business Income, or a different coverage/LOB.
3. Nothing gets built until you say go.
