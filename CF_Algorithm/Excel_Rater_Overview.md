# Excel Rater Build Guide — Overview & Shared Workbook Structure

**Written:** 2026-09-02. **Restructured:** 2026-09-02 — split out of the original single-file
`Excel_Rater_BuildGuide.md` at direction, so each cause-of-loss form gets its own document
(`Excel_Rater_BasicGroupI.md`, `Excel_Rater_BasicGroupII.md`, and Broad/Special/etc. as they're built)
instead of one growing file. This document holds only what's genuinely shared across every form: the
workbook shell, the Policy tab, the parts of Locations_Buildings and Rate_Tables that don't vary by
cause-of-loss form, and the premium-formula shape every form's premium branch follows.

**Source material.** Every fact below traces back to this project's already-verified rating-algorithm
docs, checked against the ERC package (`C:\Projects\ISO_ERC_Files\CF\20260601\CFCW20260601V01`):

- `CauseOfLoss_Building_RatingAlgorithms.md` + `BasicGroupI_ERC_Tables.md` — Building
- `CauseOfLoss_PersonalProperty_RatingAlgorithms.md` + `PersonalProperty_ERC_Tables.md` — Contents

This guide set does not re-derive anything from the ERC files directly — it only re-sequences what
those docs already established into a workbook layout. If a formula looks wrong, fix the source `.md`
doc first, then the guide.

**This is a set of guides, not a built file.** No `.xlsx` exists yet. Nothing is built until you say so.

---

## 1. Why each cause-of-loss form gets its own document

Building and Personal Property (Contents) rate the same building under up to four independent
cause-of-loss forms — Basic Group I, Basic Group II, Broad, Special — each with its own base-rate
lookup, its own factor chain, and in some cases its own premium-formula quirks. The forms are *not*
variations on one formula; `CauseOfLoss_Building_RatingAlgorithms.md`'s own four-way comparison table
shows chain lengths ranging from 6 steps (Broad) to 11 (Basic Group II), different rate keys, different
COL-adjustment shapes, and one form (Special) with a premium file that isn't even structurally similar
to the others.

Folding all four into one document made the earlier draft hard to extend safely — a change to Broad's
section risked drifting the Basic Group I section nearby without anyone intending it. Splitting means:

- Each form's document is self-contained: read `Excel_Rater_BasicGroupII.md` and you have everything
  needed to build that pair of calc tabs, without also holding Broad and Special in your head.
- Adding Broad or Special later means writing a new file in the same shape, not editing three others.
- This overview stays short and stable — it only changes when the *shared* workbook shell changes
  (a new tab category, a new Policy-level field), not every time a coverage form is added.

---

## 2. Workbook structure

The workbook grows by two calc tabs per cause-of-loss form added (one for Building, one for Contents),
plus form-specific columns on `Locations_Buildings` and form-specific table blocks on `Rate_Tables`. The
tabs that don't grow this way are listed here; each form's own document lists its two calc tabs and its
additions to the shared tabs.

| # | Tab name | Grain | Purpose | Defined in |
|---|---|---|---|---|
| 1 | `Policy` | one row per policy | Policy-level inputs every location/building/coverage reads | this document, §3 |
| 2 | `Locations_Buildings` | one row per building | Building-level rating inputs — shared columns here, form-specific columns in each form's own doc | this document (§4) + each form's doc |
| 3 | `Rate_Tables` | one block per ERC table | Flat reference tables, pasted from the ERC `.csv` files — shared tables here, form-specific tables in each form's own doc | this document (§5) + each form's doc |
| 4+ | `Calc_Building_<Form>`, `Calc_Contents_<Form>` | one row per building | Step-by-step rate build-up for that form and coverage | each form's own doc |
| last | `Premium_Summary` | one row per building | Pulls `FinalRate` from every calc tab into the premium formula, totals by policy | this document, §6 |

**Tabs built so far:** `Calc_Building_BGI`, `Calc_Contents_BGI` (`Excel_Rater_BasicGroupI.md`),
`Calc_Building_BGII`, `Calc_Contents_BGII` (`Excel_Rater_BasicGroupII.md`), `Calc_Building_Broad`,
`Calc_Contents_Broad` (`Excel_Rater_Broad.md`), `Calc_Building_Special`, `Calc_Contents_Special`
(`Excel_Rater_Special.md`). All four cause-of-loss forms for Building and Contents are now built.

---

## 3. `Policy` tab

One row per policy. These fields are read from "up the tree" by *every* coverage form's premium
formula, confirmed by both source docs as **not ERC rate tables** — supplied or schedule-rated inputs,
not lookups:

| Field | Used by | Notes |
|---|---|---|
| `PolicyNumber` | key, joins to `Locations_Buildings` | |
| `State` | every table lookup (state-or-CW key) | |
| `EffectiveDate` | picks which LCM / rate edition applies | out of scope for this pass — assume one edition |
| `LossCostMultiplier` (LCM) | every rate step, every form | one value per line of business per state; this pass assumes one LCM applies to Building and Contents alike across all forms — confirm against your state's actual ISO filing before using this for real business |
| `IRPMFactor` | every coverage form's premium formula | Individual Risk Premium Modification — user/schedule-rated, not looked up |
| `PackageModFactor` | every coverage form's premium formula | user/schedule-rated |
| `MultiPremiumAndDispersionCreditFactor` | Building forms directly; Contents forms via a `Copy` of the same value per the source docs | user/schedule-rated |

---

## 4. `Locations_Buildings` tab — shared columns

One row per building. Laid out as a shared block, then one Building block and one Contents block **per
cause-of-loss form** — each form's own document specifies its own form-specific columns, since a
building rated Basic Group I and Basic Group II simultaneously needs both forms' inputs on the same row
(e.g. `Bldg_CovType` is shared across forms, but `Bldg_ConstructionSymbol` only means something once
Basic Group II is in play).

### Shared / building-physical columns (every form reads these)

| Field | Feeds | Notes |
|---|---|---|
| `LocationID`, `BuildingID` | keys | |
| `ClassCode` | base-rate lookups (Basic Group I; also feeds Basic Group II's numeric-value override table) | Building calls it `ClassCodeToUse`; Contents calls it `BldgClassCode` — same value, different name in the source rules |
| `ConstructionCode` | base-rate and numeric-value lookups | numeric construction code |
| `ConstructionType` | Broad's base-rate lookup, Basic Group II's symbol resolution | out of scope until Broad/Basic Group II are built — reserved here so the column exists once needed |
| `Territory` | territory factor / territory-keyed base rate lookups | Basic Group I reads this as a multiplier key; Basic Group II reads a *different* territory field (`BasicGroupIIRatingTerr`) as part of its base-rate lookup key itself — see `Excel_Rater_BasicGroupII.md` |
| `ProtectionClass` | Basic Group I's protection class factor | Basic Group II has no protection-class concept at all |
| `Coinsurance` | coinsurance factor lookup (80/90/100/50/60/70/None) — shared table across every form | |
| `Deductible` | deductible factor lookup | |
| `ValuationType` | gates coinsurance-skip/force logic | e.g. blank vs. `"Functional Valuation"` |
| `RatingType` | `"Class"` for most forms | Basic Group I also supports `"Specific"`/`"Tentative"` — see `Excel_Rater_BasicGroupI.md` §9. Basic Group II, Broad, and Special have no rating-type branch at all (confirmed absent, not just unbuilt) — `RatingType` is meaningless to those three forms' rate build-up. |

Each form's own document lists the additional shared-block columns it needs (e.g. Basic Group II adds
`Bldg_ConstructionSymbol`, `NumStories`, `OpenSides`), plus its own Building- and Contents-block columns.

---

## 5. `Rate_Tables` tab — shared pattern

One named range per table, pasted directly from the `.csv` files in
`CFCW20260601V01\Rate Tables\`. Column layout: `State|CW`, then whatever key columns the table needs,
then the value column. Every table follows the same two-pass lookup pattern documented across both
source docs: try the state row first, fall back to the `CW` row —
`=IFERROR(XLOOKUP(state-key-combo, ...), XLOOKUP(CW-key-combo, ...))` is the natural Excel translation
of ERC's `FirstNonNull(state row, CW row)`.

**Tables genuinely shared across forms** (built once, read by more than one form's calc tabs):

| Table | Shared by |
|---|---|
| `CoinsuranceFactor` | every form, every coverage |
| `LessThan80PctMultiplicativeFactor` | every form |
| `DeductibleByLocationFactor` | every form (Basic Group II keeps its own variant — see its doc) |
| `DeductibleFactor` | every form's standard deductible branch |
| `Deductible250Factor` | every form's flat-$250 deductible branch |
| `SubStdConditionRate` | Basic Group I today; check before assuming Basic Group II/Broad/Special use it the same way |
| `VandalismExclFactor` | Basic Group I and II |
| `StdPropPolGroupIFactor` / `StdPropPolGroupIIFactor` | one per group, both COL-adjustment inputs |
| `CyberIncidentExclusionFactors`, `...WithEnsuingCauseOfLossExceptionsFactors` | every form, keyed by that form's cause-of-loss group name |

Each form's own document lists the tables that belong to it alone (e.g. `FireSafeVaultFactor` is
Contents-Basic-Group-I-only; `BasicGroupIIConstructionSymbol` and `GroupIINumericValue` are
Basic-Group-II-only).

### Known data gaps — a standing discipline, not a one-time note

Every ERC-tables doc this project has produced so far has independently confirmed that **checking a
table exists is not the same as checking it has usable countrywide rows** — `BUILD-LOG.md` Entry 3
records the original miss. Build every `Rate_Tables` lookup, for every form, so a missing result renders
a visible flag (e.g. `"NO CW RATE FILED — STATE ROW REQUIRED"`) rather than a silent 0. This applies
across forms — Basic Group I's `BasicGroupIRate` and Basic Group II's `BasicGroupIIRate`/
`LowestBasicGroupIIRate` are all independently confirmed header-only at the CW level; treat every new
form's tables with the same suspicion until row-counted.

---

## 6. `Premium_Summary` tab — shared premium shape

Every cause-of-loss form's "scheduled, non-blanket, non-Legal-Liability" premium branch follows this
same shape, for both Building and Contents — confirmed identical in structure across Basic Group I and
Basic Group II by both source docs, with only the input `FinalRate` and the cyber-factor suffix
(`BGI`/`BGII`/etc.) changing:

```
<Coverage>_Premium =
  ROUND(IRPMFactor × MultiPremiumAndDispersionCreditFactor × PackageModFactor
        × Calc_<Coverage>_<Form>.FinalRate × (<Coverage>_Limit / 100), 0)
  × CyberIncidentExclusionFactor<Form> × CyberIncidentExclusionCOLExcptnsFactor<Form>
```

One column pair (`<Form>_Premium`) per cause-of-loss form built so far, per coverage — gated so it only
fires when that building's `Bldg_CovType`/`PP_CovForm` matches that form's supported values, and the
building's selected cause of loss actually is that form (a building only pays premium under the cause of
loss it selected, even though every form's chain computes a rate regardless — see each form's own doc
for its specific coverage-on-policy gate). Everything outside a built form's supported values should
render `0` with a visible note, not a silent wrong number.

`Total_Building_Premium` and `Total_Contents_Premium` sum whichever form-column actually applies per
row; grand total is the sum of both, across every building on the policy.

**Not yet built into the summary tab:** the Legal Liability and blanket-rated premium branches for any
form — see each form's own document's "left out of this pass" section.

---

## 7. Documents in this set

| Document | Covers | Status |
|---|---|---|
| `Excel_Rater_Overview.md` (this file) | Shared workbook shell | Current |
| `Excel_Rater_BasicGroupI.md` | Basic Group I, Building & Contents | Built |
| `Excel_Rater_BasicGroupII.md` | Basic Group II, Building & Contents | Built |
| `Excel_Rater_Broad.md` | Broad, Building & Contents | Built |
| `Excel_Rater_Special.md` | Special, Building & Contents | Built |
| `Excel_Rater_BusinessIncome_Overview.md` + `..._BasicGroupI/II/Broad/Special.md` | Business Income, all four non-Earthquake forms — its own document set, since Business Income is one coverage (not a Building/Contents split) and three of its five forms borrow the Building's own already-computed rate | Built — see that overview for its own document index |
| — | Legal Liability / blanket-rated branches, any form | Not started |
| — | Special Class, Special Class Business Income, Business Income's Earthquake/Agreed Value/Extended Period of Indemnity (already documented in `CauseOfLoss_*` docs) | Not started |
| — | The 92+ endorsement families in `Coverage_Inventory_And_Tracking.md` | Not started — each needs its own algorithm doc traced first |
| `Excel_Rater_RatingPaths_Checklist.md` | Every rating path (coverage × form × rating type × premium branch) across the documents above, checked off | Current — the fastest way to see what's actually built vs. only formula-noted |
| `Excel_Rater_FullBuildout_Scope.md` | Every coverage (incl. Special Class, Earthquake, Flood, the 92 endorsement families), plus blanket rating, circular verification, and jurisdiction/edition breadth — the whole-line scope this workbook sits inside | Current |

## Remaining steps

1. You review this restructuring — confirm splitting by cause-of-loss form (rather than, say, by
   coverage, or by workbook tab) is the grouping you want going forward.
2. Basic Group II is built (`Excel_Rater_BasicGroupII.md`) — next is your call: Broad, Special, the
   Legal Liability/blanket branches for the two forms already built, or something else entirely.
3. Nothing gets built into an actual `.xlsx` until you say go.
