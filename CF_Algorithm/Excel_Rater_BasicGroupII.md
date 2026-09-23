# Excel Rater Build Guide — Basic Group II (Building & Contents)

> <!-- RC-1 stale-name notice --> **Notice (2026-09-23):** Written before the 2026-09-22 restructure. Sheet names have changed: Policy Inputs → IN - Policy; Bldg / Contents / BI Rating Worksheet → CALC - Bldg / Contents / BI Rating; Special Class Worksheet → CALC - Special Class; CoreScratchpad → CALC - CoreScratchpad. **Location Inputs / IN - Location and Special Class Inputs / IN - Special Class no longer exist**: every record is entered on **IN - Schedule** (one row per record, 40 per block), so input-sheet cell addresses here are out of date, and calc-sheet column C is record 1 of 40. Current state: CF_Algorithm/CF_Rater_RESUME.md.


**Written:** 2026-09-02.

**Source material:** `CauseOfLoss_Building_RatingAlgorithms.md` §"Basic Group II — differences" /
§"Basic Group II — premium" + `BasicGroupI_ERC_Tables.md` (Building); `CauseOfLoss_PersonalProperty_
RatingAlgorithms.md` §"Basic Group II — differences" / §"Basic Group II — premium" +
`PersonalProperty_ERC_Tables.md` (Contents), both cross-checked against `CFCW20260601V01`. See
`Excel_Rater_Overview.md` for the shared workbook shell this document builds on top of, and
`Excel_Rater_BasicGroupI.md` for the sibling form this one is compared against throughout.

---

## 1. What changes moving from Basic Group I to Basic Group II

Basic Group I is rated off **class code + construction code**. Basic Group II is rated off **rating
territory + construction symbol** — a structurally different lookup, not a renamed version of the same
one. Both source docs describe Basic Group II as an 11-step chain versus Basic Group I's 8 (Building)
or 9 (Contents), and both flag the same two new mechanics neither Building nor Contents needed for Basic
Group I:

- **A construction symbol** must be resolved before the base rate can be looked up — a multi-step
  process (construction type + number of stories, then class-specific overrides for certain class
  codes, then oil-distributing-station overrides) that lives once, upstream of both coverages.
- **A second, parallel rate path** — `LowestBasicGroupIIBaseRate` / `LowestBasicGroupIIRate` — used only
  when a windstorm/hail exclusion applies. Basic Group I has no equivalent fallback path at all.

Where Building computes both the symbol and its cause-of-loss adjustment locally, Contents' Basic Group
II ruleset **copies the symbol and territory down from an ancestor context** rather than recomputing
them — the actual resolution logic (construction-type/stories lookup, class overrides,
oil-distributing-station overrides) is shared and lives once, in the Structure/Location context, not
duplicated per coverage. Practically: **the Excel workbook only needs to build the symbol-resolution
formula once**, on `Locations_Buildings`, and both `Calc_Building_BGII` and `Calc_Contents_BGII` read
the same resolved symbol column — that mirrors ISO's own rule structure rather than fighting it.

| | Basic Group I (either coverage) | Basic Group II (either coverage) |
|---|---|---|
| Rate keys | ClassCode + ConstructionCode | RatingTerr + ConstructionSymbol |
| Symbol prerequisite | none | resolved once, shared by both coverages |
| Territory | Building: multiplier. Contents: n/a this pass. | lookup key into the base rate table itself, not a multiplier |
| Second rate path | none | `LowestBasicGroupII*Rate` (wind/hail-excluded branch) |
| Peril-specific factor | Building: protection class. Contents: n/a. | numeric value (occupancy/open-sides hazard) + BCEG; Building additionally applies roof-surfacing factors here, Contents does not |
| Deductible-by-location | shared factor | its own factor, keyed on a wind/hail-specific deductible field |

Between the two *coverages* under Basic Group II specifically, the pattern from Basic Group I mostly
repeats: Building's chain applies two roof-surfacing factors and a protection-class-style symbol lookup
Contents doesn't; Contents has no equivalent of Building's `MultiResidentialPropSpecialCreditFactor`;
and — new to this form — **Basic Group II's blanket-rated premium branch truncates the limit ratio
instead of dividing it plainly**, a rounding divergence that doesn't exist in Basic Group I at all (see
§6).

---

## 2. `Locations_Buildings` additions for this form

On top of the shared columns in `Excel_Rater_Overview.md` §4 and the Basic Group I columns in
`Excel_Rater_BasicGroupI.md` §2 (a building can carry both forms' inputs on the same row).

### Shared-block additions (feed both coverages' Basic Group II chains)

| Field | Feeds | Notes |
|---|---|---|
| `NumStories` | construction-symbol resolution | new for this form — Basic Group I never needed story count |
| `OpenSides` (Y/N) | open-sides numeric-value override | genuinely a plain Yes/No dropdown stored directly on the Building record (`CommercialPropertyStructure.OpenSides`, `SELECT`/`YesNo` domain) — no schedule, no derivation rule, every rule reference is a raw field read. Building-level, evaluated independently per building (confirmed 2026-09-08) |
| `BasicGroupIIRatingTerr` | Basic Group II base-rate lookup key | a genuinely different field from the shared `Territory` column — Basic Group II's territory is a lookup key into the rate table itself, not a multiplier applied after. **It's a free-text field in the ERC data model — no rule ever derives it from an address** — but 22 of 47 states file a real territory-derivation domain: 11 ZIP-keyed, 11 county-keyed. Of the rest, 24 need no derivation at all — each has only one territory, confirmed as a constant `"Entire State"` value directly against that state's own `BasicGroupIIRate` table — and 1 (PR) is moot since it files no base rate at all (checked all 47 states, 2026-09-08 — corrects `Excel_Rater_FullBuildout_Scope.md`'s trap #3, which wrongly claimed CF territory is uniformly county-keyed). Full per-state lookup data, including the constant-value list, in `BGII_Territory_Derivation.xlsx` |
| `WindstormOrHailExclusion` (Y/N) | gates the entire wind/hail-excluded branch — both the rate-path swap and the COL-adjustment swap | drives whether `LowestBasicGroupII*Rate` is used at all. **Corrected 2026-09-08: this is not a stored boolean field.** The rule (`SetBasicGroupIINumericValue`, line 8272) actually tests `NotExist AtInputDataDef="CommercialPropertyWindstormOrHailExclusionTable/CommercialPropertyWindstormOrHailExclusion"` — i.e. whether a **scheduled exclusion record exists** for this building. The table is nested inside `CommercialPropertyStructure` (same level as the Building record) and its own fields include a Premises Number and Building Number, confirming it's scheduled per building, not policy-wide. Manual citation: the record's schema annotation cites `BureauRuleNumber74A2aBldg` (**ISO Rule 74.A.2.a, Building**). A `Yes`/`No` column on `Locations_Buildings` is still the right *shape* to build for a simple rater (each building independently gets the flag), it just resolves to "does at least one such record exist," not a literal read of a stored value — evaluated independently per building, confirmed no cross-building effect from one building's exclusion alone |
| `ConstructionSymbol` *(computed, not entered)* | consumed by both `Calc_Building_BGII` and `Calc_Contents_BGII` | resolved once on this tab per §1 — see the formula outline below |

**`ConstructionSymbol` resolution** (build as its own column, not duplicated per coverage):

```
1. LookupBasicGroupIIConstructionSymbol(State|CW, ConstructionType, NumStories)
2. SuperiorRoofingIndicator = "Yes" when ConstructionType is one of the eight
   "Superior Roofing" variants (Joisted Masonry OT Reinforced/Reinforced,
   Non-Combustible Light Steel / OT Light Steel, the four Masonry Non-Combustible combos)
3. Class-specific overrides replace the symbol:
     - LookupBGIISymbolAdditionalClassesRoofConstruction
     - LookupBasicGroupIISymbolAdditionalClasses (class codes 0580/0585 and related)
     - LookupBasicGroupIISymbolOilDistributingStations
4. Otherwise: ConstructionSymbol = the step-1 result unchanged
```

**State variation, checked all 47 states (2026-09-08 session):** `LookupBasicGroupIIConstructionSymbol` and
`LookupBasicGroupIISymbolOilDistributingStations` are genuinely CW-only, zero overrides anywhere.
`LookupBGIISymbolAdditionalClassesRoofConstruction` has one override — **MT**, 6 rows vs. CW's 8, missing
the two Non-Combustible Superior Roofing rows entirely (coarser code universe, not a different price).
`LookupBasicGroupIISymbolAdditionalClasses` has four: **FL/GA/KS** each file 30-row overrides that are
value-identical to the matching CW rows, just missing the same 6 codes (dead-simple coarser filings). **MT**
is the one genuine addition — 42 rows, all 36 CW rows unchanged plus 6 new `"All"`-classification rows CW
doesn't carry at all, a whole extra symbol-assignment path unique to Montana. Full detail in
`BGII_BaseRate_Building.xlsx`'s "ConstructionSymbol Overrides" sheet.

### Building-only additions

| Field | Feeds |
|---|---|
| `Bldg_WindstormOrHailDeductible` | drives the deductible-factor branch — if blank, N/A, or equal to `Deductible`, falls through to the same `Choose` Basic Group I uses; if distinct, branches on this field instead |

### Contents-only additions

| Field | Feeds |
|---|---|
| `PP_WindstormHailIndicator` | Contents' own version of the wind/hail gate for deductible-by-location — the source doc flags this as a distinctly-named datadef (`WindstormHailIndicatorPrsnlProp`) from Building's `WindstormHailIndicator`, kept as a separate column here for the same reason |

No new Contents-only rate-affecting fields beyond these — Basic Group II Contents reuses `PP_Group`
indirectly (it drives which numeric-value override table branch applies, same as Basic Group I) and
otherwise leans on the shared/computed columns above.

---

## 3. `Rate_Tables` additions for this form

**Shared by both Building and Contents:**

| Table | Building keys | Contents keys | CW rows filed? |
|---|---|---|---|
| `BasicGroupIIRate` | State\|CW, RatingTerr, Symbol, `"Bldg"` | State\|CW, RatingTerr, Symbol, `"PersProp"` | **CW: No, header-only. But 45 of 47 states file their own Building data — see corrected finding below, this is not the blocker it first looked like** |
| `LowestBasicGroupIIRate` | State\|CW, Symbol, `"Bldg"` | State\|CW, Symbol, `"PersProp"` | **CW: No. Only 39 of 47 states file Building data — a real, narrower gap, see below** |
| `GroupIINumericValue` | State\|CW, ClassCode, ConstructionCode | same | Yes (30 rows CW). Checked all 47 states: FL/GA/KS file coarser (identical-value, 6-row-short) overrides; **MT genuinely deviates on ConstructionCode=3 for every class code** — see `BGII_NumericValue.xlsx` |
| `GroupIIOpenSidesNumericValue` | State\|CW, ConstructionCode | same | Yes (6 rows CW). Checked all 47 states: only MT overrides, same ConstructionCode=3 deviation as above |
| `BasicGroupIIConstructionSymbol` | State\|CW, ConstructionType, NumStories | shared/copied, not re-looked-up in the PP ruleset | Yes (151 rows) — checked all 47 states: zero overrides, genuinely CW-only |
| `BCEGFactor` | shared | shared | Yes (12 rows CW, but CW is structurally unresolvable — every CW row keys on a placeholder territory value `"001"` that never matches a real `BasicGroupIIRatingTerr`). Checked all 47 states: 44 file their own real territory-keyed table; **DC and NY file nothing, and it's not a gap** — confirmed against the CF Commercial Lines Manual that BCEG is an optional state exception page (Rule A1) neither state has ever adopted, so `BCEGFactor = 1.0` is the correct answer there, not a lookup failure. Full data + live formula in `BGII_BCEGFactor.xlsx` |
| `WindstormOrHailExclFactor` | State\|CW, BasicGroupIISymbol | same | Yes (5 rows) |
| `StdPropPolGroupIIFactor` | State\|CW, `"Y"` | same | Yes |
| `BasicGroupIIFlatCoinsuranceFactor` | State\|CW, `"Y"` | same | Yes |

**Building-only:**

| Table | Notes |
|---|---|
| `LimitationsOnCovForRoofSurfacingCosmeticExclFactor` | Group-II-only roof factor, distinct from the ACV factor Basic Group I also uses |
| `BasicGroupIILOIFactorBldg` (and `...WithArgs`) | Building-specific LOI table for this form |
| `BGIIDeductibleByLocationFactor` source table | Building's own wind/hail-keyed deductible-by-location factor, kept separate from the shared `DeductibleByLocationFactor` |

**Contents-only:**

| Table | Notes |
|---|---|
| `BasicGroupIILOIFactorPersProp` | Contents-specific LOI table (55 rows, confirmed in the source tables doc), distinct from Building's |

### Known data gaps for this form — corrected 2026-09-08

> **Original finding (2026-09-02): both `BasicGroupIIRate` and `LowestBasicGroupIIRate` are header-only
> at CW, for both coverages — treated as a near-total blocker, strictly worse than Basic Group I.** That
> CW row count was correct but never checked against actual state filings, the same trap this project has
> hit before on other "CW header-only" tables (`BasicGroupIRate` included). Pulling every state's own
> **correct in-force edition** (per `State_ERC_CW_Editions.csv` — several states, including CA/FL/IL/MA/
> MO/NC/NJ/RI/VT, resolve to an *earlier* snapshot batch than the current `20260601` folder; using the
> wrong one silently reintroduces the CA-edition trap already flagged in `BasicGroupI_ERC_Tables.md`)
> changes the picture substantially:
>
> - **`BasicGroupIIRate` Building resolves in 45 of 47 states.** Only **FL and PR** file zero Building
>   rows. The base rate is resolvable almost everywhere — it just needs the state filing, same pattern as
>   `BasicGroupIRate`. This is **not** the severe blocker the original finding implied.
> - **`LowestBasicGroupIIRate` is a real, narrower gap: only 39 of 47 states file Building rows.** AR, DC,
>   FL, KS, NY, PR, RI, and TX file zero — those 8 states can rate a normal Basic Group II building fine,
>   they just can't complete the wind/hail-**excluded** branch of `COLAdj`, which is the only place this
>   table is consumed. **These exact same 8 states also file an explicit empty override of
>   `WindstormOrHailExclFactor`** (confirmed 2026-09-08) — the factor that same branch multiplies in.
>   Both pieces of the wind-excluded mechanism are missing together, consistently, suggesting a
>   deliberate choice rather than eight independent filing gaps — plausibly these states don't permit
>   excluding wind/hail from a CPP at all, though that reason is inferred from the correlation, not
>   confirmed against the manual text for these specific states. A rater build needs an eligibility gate
>   before this branch is reachable at all — see
>   `Excel_Rater_BGII_WindHailExclusionEligibility_Walkthrough.html`.
> - Row counts vary widely by state that does file (4 to 60 — NY alone files 60) — not yet checked
>   whether that reflects a genuinely finer symbol/territory grid or the same symbol repeated across more
>   territories.
>
> Full per-state pull (both tables, Building only, all 357 + 155 rows), plus the corrected symbol-table
> variance findings above, live in `BGII_BaseRate_Building.xlsx` (`Spreadsheet_Rater/CF/Supporting
> Tables/`) — Walkthrough, Read Me, State Table Mapping, and the raw data sheets.

---

## 4. `Calc_Building_BGII` tab — one row per building

Straight translation of `CauseOfLoss_Building_RatingAlgorithms.md`'s 11-step chain and its "Quick
reference — end-to-end, Basic Group II scheduled building" block.

1. **`Symbol`** *(pulled from `Locations_Buildings.ConstructionSymbol`, not recomputed here)*
2. **`Terr`** = `Locations_Buildings.BasicGroupIIRatingTerr` (copied down from the location — no local
   territory-factor rule the way Basic Group I has one)
3. **`NumericValue`**:
   ```
   if WindstormOrHailExclusion = Y:            1.0
   elif ClassCode in (0580,0585,1150,1300,1650): LookupGroupIINumericValue(State|CW, ClassCode, ConstructionCode)
   elif OpenSides = Y and ConstructionCode ≠ 0:  LookupGroupIIOpenSidesNumericValue(State|CW, ConstructionCode)
   else:                                          1.0
   ```
4. **`BaseRate`** = `LookupBasicGroupIIRate(State|CW, Terr, Symbol, "Bldg")` — requires both `Symbol`
   and `Terr` non-blank, else `0.0`
5. **`LowestBaseRate`** = `LookupLowestBasicGroupIIRate(State|CW, Symbol, "Bldg")` — requires only
   `Symbol` (no territory); consumed **only** by step 6's wind/hail-excluded branch
6. **`Rate`** = `BaseRate × LCM × NumericValue × RoofSurfacingACVFactor × RoofSurfacingCosmeticExclFactor × BCEGFactor` — round to 3dp
7. **`COLAdj`**:
   ```
   if CauseOfLoss is fire-only (Fire / Fire and Vandalism / Fire and Sprinkler Leakage /
      Fire, Vandalism and Sprinkler Leakage):
       0.0
   elif WindstormOrHailExclusion ≠ Y:
       Rate × StdPropPolGroupIIFactor
   else:
       LowestBaseRate × LCM × RoofSurfacingACVFactor × RoofSurfacingCosmeticExclFactor
         × WindstormOrHailExclFactor × StdPropPolGroupIIFactor
   ```
   **`CauseOfLoss`'s own options are a cascaded domain (confirmed 2026-09-08)**, keyed on `PolicyType`
   (policy-level — set once for the whole policy, under `CommercialProperty`/"Policy Detail") ×
   `CovType` (building-level — under `CommercialPropertyStructure`/"Building Detail", same as
   `ClassCode`/`ConstructionCode`/`OpenSides`). A Commercial Property Policy offers `Basic`/`Broad`/
   `Special` (+ `Blanket Cause of Loss Applies` where applicable); a Standard Property Policy offers 8
   fire-combination options instead. The fire-only zero-out test above only matches 4 of SPP's 8 options
   — the 4 *without* "Allied Lines" (`Fire`, `Fire and Vandalism`, `Fire and Sprinkler Leakage`, `Fire,
   Vandalism and Sprinkler Leakage`). The other 4 SPP options include Allied Lines, which under ISO's
   standard definition already covers windstorm/hail — so those correctly still trigger BGII premium
   rather than zeroing out.
   **The wind/hail-excluded branch is unresolvable in 8 states — not a data gap, a correlated filing
   pattern.** `AR`, `DC`, `FL`, `KS`, `NY`, `PR`, `RI`, and `TX` all file zero rows for *both*
   `LowestBasicGroupIIRate` (§3) *and* `WindstormOrHailExclFactor` — the same 8 states, both tables,
   together. This looks like a deliberate choice (these states may not permit excluding wind/hail from a
   CPP at all — plausible given several are coastal/wind-pool states, but **not confirmed against the
   manual for these specific states**, flagged as inferred not verified). A rater build needs a
   state-eligibility gate before this branch is ever reachable — see
   `Excel_Rater_BGII_WindHailExclusionEligibility_Walkthrough.html` for the full mechanism, input-side UI
   mockup, and worked examples.
8. **`CoinsuranceFactor`**: flat lookup (State\|CW, `"Y"`) when `Coinsurance` in (50%/60%/70%/None), else
   copy the shared `CoinsuranceFactor` from Basic Group I's calc (both forms read the same underlying
   coinsurance selection on `Locations_Buildings`)
9. **`LOIFactor`** — four-way: blanket copy / `LookupBasicGroupIILOIFactorWithArgs` for Builders Risk /
   `LookupBasicGroupIILOIFactorBldg` for other cov types / `1.0` otherwise
10. **`AdjustedRate`** = `COLAdj × CoinsuranceFactor × LOIFactor`
11. **`BGIIDeductibleByLocationFactor`**:
    ```
    if WindstormHailIndicator = 0
       and a wind/hail deductible-by-location record exists with a non-blank value:
           LookupDeductibleByLocationFactor(...)
    else:
        1.0
    ```
12. **`DeductibleFactor`** — outer test: if `Bldg_WindstormOrHailDeductible` is blank, N/A, or equal to
    `Deductible`, fall through to a `Choose`-on-`Deductible` with the **same shape** Basic Group I uses;
    otherwise branch on `Bldg_WindstormOrHailDeductible` instead. **Corrected 2026-09-08: this is not
    the same table Basic Group I reads.** `DeductibleFactor` has a fourth key column,
    `CauseOfLossDeductible`, filed with three distinct values (`Basic Group I`, `Basic Group II`, `Other
    Cause Of Loss`). Basic Group I's rule keys on `"Basic Group I"`; Basic Group II's own rule
    (`SetDeductibleFactorBasicGroupII`, line 8864) keys on `"Basic Group II"` instead.

    **Re-corrected 2026-09-08 (the correction above had the keys backwards):** at CW, `"Basic Group I"`
    and `"Basic Group II"` genuinely differ (70 of 80 rows) — they were never byte-identical. The pair
    that's actually byte-identical at CW is `"Basic Group II"` and `"Other Cause Of Loss"` (0 diffs) — the
    slice Broad and Special read, not Basic Group I's. That CW coincidence doesn't hold per-state, either:
    checked all 46 non-PR states with their own filing, and `"Basic Group II"` vs `"Other Cause Of Loss"`
    diverge on 5,580 rows combined — so Broad cannot reuse BGII's already-built `BGII_DeductibleFactor.xlsx`
    table any more than it could reuse BGI's. None of this changes BGII's own build, which correctly pulled
    its own `"Basic Group II"`-keyed slice — but it does mean **`BldgBGIRating`'s existing deductible table
    was correctly built for Basic Group I all along** (spot-checked directly: its live AL/Deductible=1,000
    values match the `"Basic Group I"` CSV slice, not `"Other Cause Of Loss"`). **Do not reuse
    `BldgBGIRating`'s existing deductible table for this step** — full corrected pull, all 46 non-PR
    states, in `BGII_DeductibleFactor.xlsx`. The `Deductible = "250"` flat sub-branch is the one
    exception that genuinely is shared — it keys on `causeOfLoss = "Basic"` (the manual's group name,
    not form-specific), and Basic Group I is also `"Basic"` there.
    **Percentage wind/hail deductibles (`1%`/`2%`/`5%`) use a third, wholly separate table** —
    `WindstormOrHailDeductibleFactor` (State + the percentage string + Limit band → Factor, 21–24 CW/
    per-state rows), reached through a different rule (`SetWindstormOrHailDeductibleFactor`, line 6444)
    gated on `WindstormHailIndicator = 1`, checked *before* the dollar-amount branch. If a percentage
    value is ever selected while `WindstormHailIndicator ≠ 1`, the dollar-only branch's `Or` list won't
    match any of the eight dollar constants and falls to its `Otherwise` → `0.0`, silently zeroing the
    whole `FinalRate` (per `SetFinalBasicGroupIIRate`'s `Product`). Worth a rater-side input validation:
    percentage options should only ever be paired with `WindstormHailIndicator = 1`.
13. **`FinalRate`** = `AdjustedRate × BGIIDeductibleByLocationFactor × DeductibleFactor × MultiResidentialPropSpecialCreditFactor`

    **Correction, separate from the `CauseOfLossDeductible` key finding above:** the `limit` argument
    `SetDeductibleFactorBasicGroupII` passes into `LookupDeductibleFactor` is `TotAmtInsurance`, confirmed
    directly against the rule XML as `StructureLimitToUse + OccupancyTotAmtInsuranceSum +
    SpecialClassRiskTotAmtInsurance` — the Building's own limit **plus** every Contents item's limit at
    the location **plus** Special Class Risk amounts, not the Building's own limit alone. `CoreScratchpad`
    rows 84-94 (this project's own live build) use `'Location Inputs'!C18`, the Building-only limit — a
    real bug once a location has Contents coverage. Deliberately backlogged until Contents is built (see
    project memory `project_deductiblefactor-uses-location-total-not-building-limit`).

(Numbered 1–13 above to match every distinct value computed; the source doc's own step count of 11
refers to `Set*` rule calls, several of which — like the symbol and territory prerequisites — this
workbook resolves once on `Locations_Buildings` instead of per calc tab.)

---

## 5. `Calc_Contents_BGII` tab — one row per building

Straight translation of `CauseOfLoss_PersonalProperty_RatingAlgorithms.md`'s 11-step chain
(`SetBGIIRatesAndFactors`, line 3600).

1. **`Symbol`**, **`Terr`** — same pulled-not-computed columns as Building's (§4 steps 1–2); the source
   doc confirms these are plain `Copy`s from ancestor datadefs in ISO's own rules, consistent with
   building the resolution once on `Locations_Buildings`
2. **`NumericValue`** — identical three-way logic to Building's step 3, keyed on `BldgClassCode` (same
   value as the shared `ClassCode` column)
3. **`BaseRate`** = `LookupBasicGroupIIRate(State|CW, Terr, Symbol, "PersProp")` — same table Building
   reads, different `covType` constant
4. **`LowestBaseRate`** = `LookupLowestBasicGroupIIRate(State|CW, Symbol, "PersProp")`
5. **`Rate`** = `BaseRate × LCM × NumericValue × BCEGFactor` — round to 3dp. **No roof-surfacing factors
   at all** — Building applies two here (ACV + cosmetic exclusion); Contents applies neither, consistent
   with §1's "contents have no roof" pattern already established for Basic Group I.
6. **`COLAdj`**:
   ```
   if fire-only OR PP_ValuablePapers = Y:
       0.0
   elif WindstormOrHailExclusion ≠ Y:
       Rate × StdPropPolGroupIIFactor
   else:
       LowestBaseRate × LCM × WindstormOrHailExclFactor × StdPropPolGroupIIFactor
   ```
   Note the wind/hail-excluded branch also drops both roof-surfacing factors — Building's equivalent
   branch applies them; Contents' never does, at either the rate step or here.
7. **`CoinsuranceFactor`** — same shape as Building's step 8
8. **`LOIFactor`** — three-way (one fewer branch than Building's four): blanket copy /
    `LookupBasicGroupIILOIFactorPersProp(OccupTotalLOIToUse)` guarded by `CovType` not in Legal
    Liability/Tobacco Sales Warehouses and a positive LOI total / otherwise `1.0`. **No separate
    Builders Risk branch** the way Building has one.
9. **`AdjustedRate`** = `LOIFactor × COLAdj × CoinsuranceFactor` (source doc gives this ordering)
10. **`BGIIDeductibleByLocationFactor`** — same shape as Building's, but the wind/hail gate reads
    `PP_WindstormHailIndicator` (Contents' own distinctly-named field) rather than Building's
    `WindstormHailIndicator`
11. **`DeductibleFactor`** — the source doc flags this, like Basic Group I's Contents deductible factor,
    as `Copy`'d from an ancestor record rather than computed locally. **Build it as the same local
    `Choose` used in `Calc_Building_BGII` step 12** — same documented-deviation treatment as
    `Excel_Rater_BasicGroupI.md` §5 step 9, and worth the same cell comment. Same `CauseOfLossDeductible`
    correction applies here as Building step 12 — this reads the `"Basic Group II"`-keyed slice of
    `DeductibleFactor`, not Basic Group I's `"Other Cause Of Loss"` slice.
12. **`FinalRate`** = `AdjustedRate × BGIIDeductibleByLocationFactor × DeductibleFactor` — **no
    multi-residential credit multiplier**, consistent with Basic Group I Contents.

---

## 6. `Premium_Summary` formulas for this form

Both premium files are structurally near-identical to their Basic Group I counterparts (confirmed by
both source docs as a side-by-side inspection, not just an assumption) — same `CovType`/`CovForm` and
`IncludedInBlkt` gates, same three branches plus otherwise-zero. Datadef names swap to the `II` suffix
throughout (`FinalBasicGroupIIRate`, `BasicGroupIICauseOfLossAdjustment`, `BlktBasicGroupIIAvgRate`,
`CyberIncidentExclusionFactorBGII`, `CyberIncidentExclusionCOLExcptnsFactorBGII`):

```
Bldg_Premium (BGII) =
  ROUND(IRPMFactor × MultiPremiumAndDispersionCreditFactor × PackageModFactor
        × Calc_Building_BGII.FinalRate × (Bldg_Limit / 100), 0)
  × CyberIncidentExclusionFactorBGII × CyberIncidentExclusionCOLExcptnsFactorBGII

PP_Premium (BGII) =
  ROUND(IRPMFactor × MultiPremiumAndDispersionCreditFactor × PackageModFactor
        × Calc_Contents_BGII.FinalRate × (PP_Limit / 100), 0)
  × CyberIncidentExclusionFactorBGII × CyberIncidentExclusionCOLExcptnsFactorBGII
```

Gates mirror Basic Group I's (§`Excel_Rater_BasicGroupI.md` §6) — `Bldg_CovType`/`PP_CovForm` against
the same supported-value lists, since both premium files use identical gate logic to their Basic Group I
counterparts.

**One real divergence, new to this form, not yet built into the summary tab:** the *blanket-rated*
branch (out of scope this pass for both forms — see §7) computes the limit ratio differently between the
two forms. Basic Group I's blanket branch does a plain `BlktLimit / 100` division; **Basic Group II's
truncates it first** — `Truncate(BlktLimit / 100)` — which can shave fractional cents off the result
relative to Basic Group I on the same inputs. Not load-bearing until the blanket branch is actually
built, but worth flagging now so it isn't silently missed when that branch is added — a naive
copy-Basic-Group-I-and-rename approach would get this one column wrong.

---

## 7. What's deliberately left out of this pass

Same list as `Excel_Rater_BasicGroupI.md` §7, plus one addition specific to this form:

- Specific/Tentative rating type — Basic Group II's chain as documented here assumes class-rated
  throughout; the source doc doesn't describe a Specific/Tentative branch for this form the way Basic
  Group I has one, so this isn't just "not built yet," it may not exist as a rated path at all for Basic
  Group II — flagged as unconfirmed rather than assumed either way.
- Legal Liability premium branch (both coverages)
- Blanket-rated premium branch (both coverages) — when built, remember the truncation divergence in §6
- `OperationalUnitWindstormOrHailExclusionFactor` — a **separate mechanism from the per-building
  wind/hail exclusion described above**, found while tracing this form, not yet built or fully resolved.
  `SetOperationalUnitWindstormOrHailExclusionFactor` (line 6622) fires only when a building is flagged
  `BldgIncludedInOperationalUnit = "Yes"` (an "Operational Unit" — a schedule of buildings grouped
  together, the same concept used elsewhere for blanket rating, flood coverage, and business income —
  not automatically every building on the policy) **and** an ancestor-level count,
  `../../OperationalUnitWindstormOrHailExclusionFormCount`, is greater than zero — i.e. *any* building in
  that same Operational Unit has an exclusion form scheduled, not just this one. If both hold, a factor is
  looked up (`LookupWindstormOrHailExclFactor`); otherwise it's `0.0`. **Traced every reference to this
  factor within `CommercialPropertyStructureRules.Rule.xml` and found it's set but never consumed
  anywhere else in that file** — not multiplied into `Rate`, `NumericValue`, or `FinalRate`. Unconfirmed
  whether it's read by a premium/summary rule file not yet checked, or is a genuinely unused field in
  this ruleset (same "computed but never multiplied" pattern already found elsewhere in this project,
  e.g. Business Income's `MultiPremiumAndDispersionCreditFactor`). Not built into this workbook pending
  that answer.

---

## 8. Inputs → rating output — the full picture

Same idea as `Excel_Rater_BasicGroupI.md` §8: sections 4–5 above give the formula one workbook column
at a time; this section gives the same information as an input→output flow and one complete if/then
expression per coverage, so you can trace where a number came from without re-reading every step.

### 8.1 What feeds the loss cost (Building)

Basic Group II's loss cost is a different kind of lookup than Basic Group I's — it isn't keyed on class
and construction code directly, it's keyed on **territory and a resolved construction symbol**, and the
symbol itself has to be derived before the loss cost can even be looked up. That derivation is the one
genuinely new "input stage" this form adds that Basic Group I never needed.

| Stage | Reads from | Produces | Tab |
|---|---|---|---|
| −1 — derive the construction symbol (once, shared by both coverages) | `ConstructionType`, `NumStories` (→ `Rate_Tables.BasicGroupIIConstructionSymbol`), then `ClassCode` (→ additional-classes overrides) | `ConstructionSymbol` | `Locations_Buildings` |
| 0 — the loss cost itself | `ConstructionSymbol`, `BasicGroupIIRatingTerr` (→ `Rate_Tables.BasicGroupIIRate`, `covType="Bldg"`) | `BaseRate`; also, in parallel, `LowestBaseRate` from `ConstructionSymbol` alone | `Calc_Building_BGII` |
| 1 — turn it into a rate | `BaseRate`, `Policy.LossCostMultiplier`, `WindstormOrHailExclusion` + `ClassCode`/`ConstructionCode`/`OpenSides` (→ `NumericValue`), `Bldg_RoofSurfacingFactorInputs` (→ two roof factors this time, not one), `BCEGFactor` | `Rate` | `Calc_Building_BGII` |
| 2 — adjust for cause-of-loss exclusions | `Rate` or, if `WindstormOrHailExclusion = Y`, `LowestBaseRate` instead; plus the selected `CauseOfLoss` (fire-only gate) | `COLAdj` | `Calc_Building_BGII` |
| 3 — apply how the insured chose to insure | `COLAdj`, `Coinsurance`, `Bldg_CovType`, `Bldg_Limit` | `AdjustedRate` | `Calc_Building_BGII` |
| 4 — apply the chosen deductible | `AdjustedRate`, `Bldg_WindstormOrHailDeductible` (or `Deductible` if no separate wind/hail deductible), `WindstormHailIndicator`, `Bldg_MultiResIndicator` | `FinalRate` | `Calc_Building_BGII` |
| 5 — turn the rate into a dollar premium | `FinalRate`, `Bldg_Limit`, the three `Policy` schedule-rating factors | `Bldg_Premium` | `Premium_Summary` |

### 8.2 Full formula with if/then (Building)

```
ConstructionSymbol =
    LookupBasicGroupIIConstructionSymbol(State|CW, ConstructionType, NumStories)
    <then, in order, replaced by whichever override matches first:>
        LookupBGIISymbolAdditionalClassesRoofConstruction(...)
        LookupBasicGroupIISymbolAdditionalClasses(...)              # class codes 0580/0585 and related
        LookupBasicGroupIISymbolOilDistributingStations(...)
    <else unchanged>

BaseRate =
    LookupBasicGroupIIRate(State|CW, BasicGroupIIRatingTerr, ConstructionSymbol, "Bldg")
        if ConstructionSymbol and BasicGroupIIRatingTerr are both non-blank
    else 0.0

LowestBaseRate =
    LookupLowestBasicGroupIIRate(State|CW, ConstructionSymbol, "Bldg")
        if ConstructionSymbol is non-blank
    else 0.0

NumericValue =
    1.0                                                              if WindstormOrHailExclusion = Y
    elif ClassCode in (0580,0585,1150,1300,1650):
        LookupGroupIINumericValue(State|CW, ClassCode, ConstructionCode)
    elif OpenSides = Y and ConstructionCode ≠ 0:
        LookupGroupIIOpenSidesNumericValue(State|CW, ConstructionCode)
    else:
        1.0

Rate =
    BaseRate × LCM × NumericValue × RoofSurfacingACVFactor × RoofSurfacingCosmeticExclFactor × BCEGFactor
    (round to 3 dp)

COLAdj =
    0.0    if CauseOfLoss in ("Fire","Fire and Vandalism","Fire and Sprinkler Leakage",
                               "Fire, Vandalism and Sprinkler Leakage")
    elif WindstormOrHailExclusion ≠ Y:
        Rate × StdPropPolGroupIIFactor
    else:
        LowestBaseRate × LCM × RoofSurfacingACVFactor × RoofSurfacingCosmeticExclFactor
          × WindstormOrHailExclFactor × StdPropPolGroupIIFactor

CoinsuranceFactor =
    LookupBasicGroupIIFlatCoinsuranceFactor(State|CW, "Y")   if Coinsurance in ("50%","60%","70%","None")
    else CoinsuranceFactor   # the same value Basic Group I's chain already computed for this building

LOIFactor =
    <blanket copy>                                            if Bldg_IncludedInBlkt = "Yes"
    elif Bldg_CovType = "Builders Risk":
        LookupBasicGroupIILOIFactorWithArgs(...) or 0.0 if the Builders Risk limit is absent
    elif Bldg_CovType not in ("Leasehold Interest","Legal Liability","No Coverage"):
        LookupBasicGroupIILOIFactorBldg(...) or 0.0 if absent
    else:
        1.0

AdjustedRate = COLAdj × CoinsuranceFactor × LOIFactor

BGIIDeductibleByLocationFactor =
    LookupDeductibleByLocationFactor(...)
        if WindstormHailIndicator = 0
           and a wind/hail-by-location record exists with a non-blank value
    else 1.0

DeductibleFactor =
    <same-shape Deductible-keyed Choose Basic Group I uses, but reads the "Basic Group II"-keyed
     slice of DeductibleFactor, not BGI's "Other Cause Of Loss" slice — see §5 step 12>
        if Bldg_WindstormOrHailDeductible is blank, "Not Applicable", or = Deductible
    else <branch on Bldg_WindstormOrHailDeductible instead — dollar amounts use the same table;
          percentage amounts (1%/2%/5%) use a separate WindstormOrHailDeductibleFactor table entirely>

FinalRate = AdjustedRate × BGIIDeductibleByLocationFactor × DeductibleFactor × MultiResidentialPropSpecialCreditFactor

Bldg_Premium =
    if Bldg_CovType in ("Building","Builders Risk","Improvements and Betterments","Condominium Association")
       and Bldg_IncludedInBlkt = "No":
        round(IRPMFactor × MultiPremiumAndDispersionCreditFactor × PackageModFactor × FinalRate × (Bldg_Limit/100), 0)
          × CyberIncidentExclusionFactorBGII × CyberIncidentExclusionCOLExcptnsFactorBGII
    elif Bldg_CovType = "Legal Liability":
        [not built this pass — see §7]
    elif Bldg_IncludedInBlkt = "Yes":
        [blanket branch — truncates the limit ratio, see §6 — not built this pass]
    else:
        0.0
```

### 8.3 What feeds the loss cost (Contents)

Same symbol-and-territory loss-cost shape as Building, reading the same resolved `ConstructionSymbol`
column rather than re-deriving it — but from `Rate` onward the two coverages diverge the same way they
did under Basic Group I: no roof factors anywhere in Contents' chain, and one fewer LOI branch.

| Stage | Reads from | Produces | Tab |
|---|---|---|---|
| −1 — construction symbol | *(reused from Building's derivation — not recomputed)* | `ConstructionSymbol` | `Locations_Buildings` |
| 0 — the loss cost itself | `ConstructionSymbol`, `BasicGroupIIRatingTerr` (→ `Rate_Tables.BasicGroupIIRate`, `covType="PersProp"`) | `BaseRate`; `LowestBaseRate` in parallel | `Calc_Contents_BGII` |
| 1 — turn it into a rate | `BaseRate`, `Policy.LossCostMultiplier`, `NumericValue` (same three-way logic as Building's, keyed on `BldgClassCode`), `BCEGFactor` — **no roof-surfacing inputs at all** | `Rate` | `Calc_Contents_BGII` |
| 2 — adjust for cause-of-loss exclusions | `Rate` or `LowestBaseRate`, `CauseOfLoss` fire-only gate, `PP_ValuablePapers` (Contents-only zeroing gate, same as Basic Group I) | `COLAdj` | `Calc_Contents_BGII` |
| 3 — apply how the insured chose to insure | `COLAdj`, `Coinsurance`, `PP_CovForm`, `PP_Limit`/`OccupTotalLOIToUse` | `AdjustedRate` | `Calc_Contents_BGII` |
| 4 — apply the chosen deductible | `AdjustedRate`, `Deductible`, `PP_WindstormHailIndicator` | `FinalRate` — no multi-res input | `Calc_Contents_BGII` |
| 5 — turn the rate into a dollar premium | `FinalRate`, `PP_Limit`, the three `Policy` factors | `PP_Premium` | `Premium_Summary` |

### 8.4 Full formula with if/then (Contents)

```
BaseRate = LookupBasicGroupIIRate(State|CW, BasicGroupIIRatingTerr, ConstructionSymbol, "PersProp")
LowestBaseRate = LookupLowestBasicGroupIIRate(State|CW, ConstructionSymbol, "PersProp")

NumericValue =
    1.0                                                              if WindstormOrHailExclusion = Y
    elif BldgClassCode in (0580,0585,1150,1300,1650):
        LookupGroupIINumericValue(State|CW, BldgClassCode, ConstructionCode)
    elif OpenSides = Y and ConstructionCode ≠ 0:
        LookupGroupIIOpenSidesNumericValue(State|CW, ConstructionCode)
    else:
        1.0

Rate = BaseRate × LCM × NumericValue × BCEGFactor
    (round to 3 dp — no roof-surfacing factor of any kind, at any branch)

COLAdj =
    0.0    if fire-only cause of loss OR PP_ValuablePapers = "Y"
    elif WindstormOrHailExclusion ≠ Y:
        Rate × StdPropPolGroupIIFactor
    else:
        LowestBaseRate × LCM × WindstormOrHailExclFactor × StdPropPolGroupIIFactor
        (still no roof factors in this branch either)

CoinsuranceFactor =
    LookupBasicGroupIIFlatCoinsuranceFactor(State|CW, "Y")   if Coinsurance in ("50%","60%","70%","None")
    else CoinsuranceFactor   # shared with Basic Group I's Contents chain

LOIFactor =
    <blanket copy>                                            if PP_IncludedInBlkt = "Yes"
    elif PP_CovForm not in ("Legal Liability Coverage Form","Tobacco Sales Warehouse Coverage Form")
         and OccupTotalLOIToUse > 0:
        LookupBasicGroupIILOIFactorPersProp(OccupTotalLOIToUse)
    else:
        1.0
    (no separate Builders Risk branch, unlike Building)

AdjustedRate = LOIFactor × COLAdj × CoinsuranceFactor

BGIIDeductibleByLocationFactor =
    LookupDeductibleByLocationFactor(...)
        if PP_WindstormHailIndicator = 0
           and a wind/hail-by-location record exists with a non-blank value
    else 1.0

DeductibleFactor =
    <same local Choose used on the Building tab — documented deviation, see §5 step 11>

FinalRate = AdjustedRate × BGIIDeductibleByLocationFactor × DeductibleFactor
    (no multi-residential credit multiplier, at any branch)

PP_Premium =
    if PP_CovForm not in ("Legal Liability Coverage Form","Tobacco Sales Warehouse Coverage Form",
                           "Class Rated Building Only, No Personal Property Coverage")
       and PP_IncludedInBlkt = "No":
        round(IRPMFactor × MultiPremiumAndDispersionCreditFactor × PackageModFactor × FinalRate × (PP_Limit/100), 0)
          × CyberIncidentExclusionFactorBGII × CyberIncidentExclusionCOLExcptnsFactorBGII
    elif PP_CovForm = "Legal Liability Coverage Form":
        [not built this pass — see §7]
    elif PP_IncludedInBlkt = "Yes":
        [blanket branch — truncates the limit ratio, see §6 — not built this pass]
    else:
        0.0
```

---

## Remaining steps

1. You review this document against `Excel_Rater_BasicGroupI.md` — in particular whether resolving
   `ConstructionSymbol` once on `Locations_Buildings` (rather than duplicating it per calc tab) is how
   you want shared prerequisites handled going forward, since that pattern will recur (Broad's
   construction-type dependency, Special's theft-exclusion indicator).
2. Next coverage form is your call — Broad, Special, or the Legal Liability/blanket branches for the
   two forms now built.
3. Nothing gets built until you say go.
