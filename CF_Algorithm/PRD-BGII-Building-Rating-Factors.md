# PRD — CF Basic Group II Building: Reference Workbooks → Excel Rater

> <!-- RC-1 stale-name notice --> **Notice (2026-09-23):** Written before the 2026-09-22 restructure. Sheet names have changed: Policy Inputs → IN - Policy; Bldg / Contents / BI Rating Worksheet → CALC - Bldg / Contents / BI Rating; Special Class Worksheet → CALC - Special Class; CoreScratchpad → CALC - CoreScratchpad. **Location Inputs / IN - Location and Special Class Inputs / IN - Special Class no longer exist**: every record is entered on **IN - Schedule** (one row per record, 40 per block), so input-sheet cell addresses here are out of date, and calc-sheet column C is record 1 of 40. Current state: CF_Algorithm/CF_Rater_RESUME.md.


**Status:** draft, 2026-09-08. **Owner:** this project (`CF_Algorithm`), consumed by
`Spreadsheet_Rater\CF`. **No build authorized yet** — this PRD scopes what wiring these factors into
`CFRater1.01.xlsb` would require; it does not itself authorize doing so.

Sibling document to `PRD-BGI-Building-Rating-Factors.md` — same convention, same discipline, different
form. Basic Group II is a structurally different rate build-up from Basic Group I (territory+symbol
keyed rather than class+construction keyed — see `Excel_Rater_BasicGroupII.md` §1), so nothing here
should be assumed to share a mechanism with the BGI PRD even where a factor name looks similar.

---

## 1. Problem

`CFRater1.01.xlsb` needs to compute a Basic Group II (BGII) Building premium. Same discipline as BGI:
every factor reverse-engineered from the ISO ERC filing, cross-checked against the CF Commercial Lines
Manual where precision mattered, turned into a standalone workbook before anything touches the live
rater.

## 2. Scope

**In scope:** the BGII Building rate build-up, factor by factor, as documented in
`Excel_Rater_BasicGroupII.md` and `CauseOfLoss_Building_RatingAlgorithms.md`'s Basic Group II section.

**Out of scope:** Contents (Personal Property), Business Income, and every other CF coverage form.
Wiring anything into `CFRater1.01.xlsb` itself, beyond the named territory ranges in §5. Puerto Rico —
excluded from every workbook and finding below per standing project decision (2026-09-08): "we are not
working on PR, stop doing anything related to PR."

## 3. What's been built

Six standalone Excel workbooks (four BGII-specific, two shared/reused from BGI) plus three HTML
walkthroughs, all independently verified against the ERC source across every filed state — using each
state's own correct in-force edition per `State_ERC_CW_Editions.csv`, not the current-edition folder
blindly (the CA-edition trap, first caught in the BGI pass, repeats here for CA/FL/IL/MA/MO/NC/NJ/RI/VT).

| Factor | Workbook / File | Mechanism | State variation |
|---|---|---|---|
| Construction Symbol resolution | `BGII_BaseRate_Building.xlsx` (ConstructionSymbol Base + Overrides sheets) | Base ConstructionType×NumStories lookup, then up to 3 unconditional-overwrite overrides in order (RoofConstruction → AdditionalClasses → OilDistributingStations) | Base table + OilDistributingStations: CW-only, zero overrides. RoofConstruction: MT only (coarser). AdditionalClasses: FL/GA/KS coarser (value-identical), MT genuinely adds 6 new rows |
| Base Rate / Lowest Base Rate | `BGII_BaseRate_Building.xlsx` | `BasicGroupIIRate` (Terr+Symbol keyed) and `LowestBasicGroupIIRate` (Symbol only) | CW header-only for both — **corrected finding**: `BasicGroupIIRate` resolves in 45/47 states once pulled from correct editions (only FL/PR don't file). `LowestBasicGroupIIRate` resolves in 39/47 — 8 states (AR/DC/FL/KS/NY/PR/RI/TX) file nothing, correlated with those same 8 states also filing an empty `WindstormOrHailExclFactor` override (§6) |
| Territory (`BasicGroupIIRatingTerr`) | `BGII_Territory_Derivation.xlsx` | Free-text field, no rule-based derivation — 22 states file a real address-to-territory domain | 11 ZIP-keyed, 11 county-keyed, 24 need none (single territory, constant `"Entire State"`), 1 (PR, excluded) moot. **Corrects** `Excel_Rater_FullBuildout_Scope.md` trap #3's "uniformly county-keyed" claim |
| Territory dropdown (override list) | `BGII_Territory_Derivation.xlsx` ("Territory Dropdown (All States)" sheet) | Every real State+Territory pair sourced from `BasicGroupIIRate`'s own filed keys, not the derivation domains | 78 pairs, 45 states (FL has no base rate to key against; PR excluded) |
| ZIP → County crosswalk | `ZIP_to_County_Lookup.xlsx` | General-purpose reference, not ISO-filed — U.S. Census 2020 ZCTA-to-County relationship file, fills the gap between county-keyed territory states and ZIP-only location data | 33,642 ZIPs, 50 states + DC; ~30% split across multiple counties, resolved to majority land-area share with the full split documented separately |
| NumericValue (class-code / open-sides overrides) | `BGII_NumericValue.xlsx` | 4-way branch: 1.0 if wind/hail excluded; else class-code override (5 fixed codes); else open-sides override; else 1.0 | Rebuilt to explicit all-state rows (46 states, no CW key) per direct request. FL/GA/KS coarser (value-identical); **MT genuinely deviates on ConstructionCode=3, both tables, every class code** |
| BCEG Factor | `BGII_BCEGFactor.xlsx` | Terr+Grade keyed, shared by Building and Contents | CW structurally unresolvable (placeholder `"001"` territory key never matches a real value). 44/46 states file their own real table. **DC and NY confirmed not a gap** — CF Commercial Lines Manual shows BCEG is an optional state exception page (Rule A1) neither state ever adopted; `BCEGFactor = 1.0` is the correct, manual-confirmed answer there |
| Deductible Factor | `BGII_DeductibleFactor.xlsx` | **Corrected 2026-09-08 — NOT reused from BGI.** `DeductibleFactor` has a 4th key column, `CauseOfLossDeductible` (`Basic Group I` / `Basic Group II` / `Other Cause Of Loss`, filed separately). BGI keys `"Other Cause Of Loss"`; BGII keys `"Basic Group II"` — identical at CW, genuinely different in every state that files its own table (130+ differing rows/state). Only the flat `Deductible="250"` branch is genuinely shared (keyed on manual group name `"Basic"`, not the form) | 40 states share BGI's 154-row shape with different values; FL/NV/TX/UT coarser; CA/NY fall back to CW. Percentage wind/hail deductibles (1%/2%/5%) use a third, separate table (`WindstormOrHailDeductibleFactor`), gated on `WindstormHailIndicator=1` — silently zeroes if that gate isn't set correctly. See `Excel_Rater_BGII_DeductibleFactor_Walkthrough.html`, corrected same day |
| MultiResidentialPropSpecialCreditFactor (reused from BGI) | *(BGI's `BGI_MultiResidentialPropSpecialCredit.xlsx`, mechanism identical)* | Same gate, same Heat×Control tables, same CT/MA/ME state variation as BGI | Nothing new to build — wire `Calc_Building_BGII`'s `FinalRate` to the same lookups |

Each BGII-specific workbook follows the same convention as the BGI set: a **Read Me** sheet, a
**Walkthrough** sheet with live cell-anchored formulas, a **State Table Mapping** sheet, and the
underlying table(s).

**HTML walkthroughs** (`CF_Algorithm/`, not `Supporting Tables` — design docs, not data):
- `Excel_Rater_BGII_DeductibleFactor_Walkthrough.html` — the `BGIIDeductibleByLocationFactor` field and the wind/hail-vs-plain-deductible key branch
- `Excel_Rater_BGII_WindHailExclusionEligibility_Walkthrough.html` — the 8-state ineligibility gate (§6), an input-side UI mockup, and the `COLAdj` guard
- `Excel_Rater_BasicGroupII_Scope.html` — full rating scope, all sections, kept current as each factor above gets reviewed

## 4. What's confirmed vs. still open

**Confirmed this session** (previously wrong, overstated, or unverified — now settled):
- `BasicGroupIIRate` Building resolves in 45/47 states, not the near-total CW-level blocker first
  documented — the original finding conflated "CW is header-only" with "unresolvable everywhere."
- Territory derivation is a near-even ZIP/county split (11/11), not uniformly county-keyed as this
  project's own cross-cutting trap list previously claimed.
- 24 of the 25 states originally flagged "no territory derivation, a gap" are actually single-territory
  constants (`"Entire State"`) — not a gap, nothing to derive.
- `WindstormOrHailExclusion` is not a stored boolean — it's a scheduled-record existence test
  (`CommercialPropertyWindstormOrHailExclusionTable`), building-level, ISO Rule 74.A.2.a.
- `OpenSides` genuinely is a plain stored Yes/No field — no schedule, no derivation, confirmed by
  contrast with the above.
- `CauseOfLoss`'s available options are a cascaded domain keyed on `PolicyType` (policy-level) ×
  `CovTypeBldg` (building-level) — CPP gets Basic/Broad/Special, SPP gets 8 fire-combination options.
  The `COLAdj` fire-only zero-out test only matches 4 of SPP's 8 options — the 4 without "Allied Lines,"
  which is consistent with Allied Lines including windstorm/hail under the standard ISO definition.
- BCEG is an optional state exception page, not a standard countrywide rule — confirmed against the
  manual text, resolving the DC/NY "gap" as a correct `1.0`, not missing data.
- The 8 states missing `LowestBasicGroupIIRate` are the same 8 states filing an explicit empty override
  of `WindstormOrHailExclFactor` — a deliberate, correlated pattern, not independent coincidences.
- `DeductibleFactor` is **not** a table shared between Basic Group I and Basic Group II — it has a 4th
  key column (`CauseOfLossDeductible`) filed with distinct `Basic Group I`/`Basic Group II`/`Other Cause
  Of Loss` values, identical only at CW. This overturns every earlier reference in this project's docs
  claiming BGII "reuses" BGI's deductible table — corrected in `Excel_Rater_BasicGroupII.md`, the scope
  page, and `Excel_Rater_BGII_DeductibleFactor_Walkthrough.html`.
- Percentage wind/hail deductibles (`1%`/`2%`/`5%`) resolve through a wholly separate table,
  `WindstormOrHailDeductibleFactor`, gated on `WindstormHailIndicator=1` and checked before the
  dollar-amount branch. A percentage value selected without that gate set correctly falls through to a
  silent `0.0` — a real input-validation need, not just a documentation nuance.
- A CoreScratchpad formula bug (asymmetric `Row Offset`/`Actual Sheet` indexing, copied from BGI's own
  live LOI factor pattern) was found and fixed in both the new BGII LOI build and, separately, in BGI's
  already-live formula — the BGI version was silently wrong only at Construction Code group boundaries,
  masked everywhere else by duplicate adjacent rows. Both fixes applied directly to `CFRater1.01.xlsb`.

**Still open / not yet reviewed:**
- Whether `OperationalUnitWindstormOrHailExclusionFactor` (a separate mechanism from the per-building
  exclusion, found while tracing this form) is consumed anywhere in the ruleset or is genuinely dead —
  traced every reference within `CommercialPropertyStructureRules.Rule.xml` and found none; a
  premium/summary file elsewhere hasn't been checked.
- The regulatory *reason* the 8 wind/hail-exclusion-ineligible states can't exclude the peril — inferred
  from the correlated-empty-tables pattern, not yet confirmed against the manual/circular text for those
  specific 8 states.
- Whether `LimitationsOnCovForRoofSurfacingACVFactor` and `...CosmeticExclFactor` double-count when
  `Applicability = "Paragraph A and B"` — the Cosmetic rule hardcodes `"Paragraph B"` as its lookup key
  regardless of the actual `Applicability` value, which may mean the filed combined-factor row
  (`0.98`) already represents the full limitation and multiplying the Cosmetic factor on top
  double-applies it. Flagged, not resolved.
- `GroupIINumericValue`/`GroupIIOpenSidesNumericValue` and `BCEGFactor` are the only factors with a full
  47-state pass beyond base rate/territory/symbol. `BCEGFactor`, `WindstormOrHailExclFactor`,
  `StdPropPolGroupIIFactor`, `BasicGroupIIFlatCoinsuranceFactor`, both LOI tables, and
  `LimitationsOnCovForRoofSurfacingCosmeticExclFactor` still need the same treatment — see
  `Excel_Rater_BasicGroupII_Scope.html` §5 for the current checked/unchecked table.
- Specific/Tentative rating for BGII — flagged unconfirmed-not-assumed-absent, never directly checked
  against the rule file.

## 5. Production rater changes made to date

**Applied directly to `CFRater1.01.xlsb`:**
- 45 named ranges (`<STATE>_bgiiterr`, PR and FL excluded) on the `BGIITerritory` tab — mirrors the
  existing `<STATE>_bgiterr` convention on `BGI Territories`, for `INDIRECT`-based dependent dropdown use.
- `BldgBGIRating`'s LOI Factor chain (`CoreScratchpad!C73:L83`) — built by the user from the suggested
  formulas, one indexing bug found and fixed twice (first a `Limit_From` off-by-one, then a deeper
  `Actual Sheet`-vs-`Row Offset` asymmetry affecting `Limit_ToLessThan`/`Factor_From`).
- The same asymmetric-indexing bug, found latent in BGI's own already-live LOI formula
  (`CoreScratchpad!C30:L31`) — fixed directly via COM automation, confirmed no regression on the
  existing test case.
- `Location Inputs` row 21 added by the user — `Windstorm or Hail Deductible`, percentage-only
  (`Not Applicable`/`1%`/`2%`/`5%`, domain `PolicyDropdowns!K2:K5`). This shifted every field below it
  down one row: `Per Location Deductible` is now row 22, `Windstorm or Hail Exclusion` is now row 35.

**Live-formula chains specified (by the user, in-progress — not yet confirmed pasted/tested):**
- `DeductibleFactorBasicGroupII`: `BldgBGIIRating!AM:AQ` (dollar table) + `AS:AW` (percentage table, `AR`
  deliberately left blank), `CoreScratchpad!C85:C93`, read by `Bldg Rating Worksheet!C93`. Full detail,
  including the simplification made on the `WindstormHailIndicator` mapping question, in
  `BGII_DeductibleFactor.xlsx`'s `CF Rater - Table Placement` / `CF Rater - CoreScratch85+` sheets.
- `BGIIDeductibleByLocationFactor`: `Bldg Rating Worksheet!C45` =
  `IF(AND('Location Inputs'!C35="No",'Location Inputs'!C22="Yes"),0.995,1)`.

Per this project's standing rule, no further building into the live rater happens without an explicit
go from the user, factor by factor — the two chains above were specified at the user's direction, one
step at a time, same as the territory ranges and LOI chain before them.

## 6. Known gaps — flag, don't hide

- **`BasicGroupIIRate` and `LowestBasicGroupIIRate` don't resolve for FL or PR (Building).** FL is a
  real gap (no known reason found yet); PR is out of scope by standing decision, not investigated
  further.
- **The 8-state wind/hail-exclusion gap (`AR/DC/FL/KS/NY/PR/RI/TX`) needs a UI-level guard, not just a
  data note.** Without the eligibility gate designed in
  `Excel_Rater_BGII_WindHailExclusionEligibility_Walkthrough.html`, a user could configure a wind/hail
  exclusion in one of these states and get an unresolvable or silently wrong calculation. Not yet built
  into any live tab.
- **`BCEGFactor`'s blank-grade default is `0.0`, not `1.0`** — the one factor in this chain that breaks
  the "no election → harmless no-op" pattern every other factor follows. A missing BCEG grade zeroes the
  entire `Rate`. Must be a required field in any real rater build, not an optional one with a sensible
  default.
- **State edition selection remains a recurring trap**, same as the BGI PRD's §6 — every pull in this
  document went through `State_ERC_CW_Editions.csv` specifically to avoid it, and any future factor pull
  needs to do the same.
- **The `Applicability = "Paragraph A and B"` double-counting question (§4) is unresolved** and could
  affect real premium if `LimitationsOnCovForRoofSurfacingACVFactor`/`...CosmeticExclFactor` are ever
  built without checking it first.

## 7. Next steps

1. Continue the factor-by-factor pass — `WindstormOrHailExclFactor`, `StdPropPolGroupIIFactor`,
   `BasicGroupIIFlatCoinsuranceFactor`, and both LOI tables are the next unchecked items.
2. Resolve the `OperationalUnitWindstormOrHailExclusionFactor` dead-or-consumed question before treating
   it as safe to ignore.
3. Resolve the Paragraph A/B roof-surfacing double-counting question before either factor is built.
4. Once a meaningful set of factors is reviewed and stable, get an explicit go to wire Supporting Tables
   workbooks into `CFRater1.01.xlsb` beyond the one territory-range exception in §5.
5. Keep `Excel_Rater_BasicGroupII.md` and `Excel_Rater_BasicGroupII_Scope.html`'s findings current as
   each new factor is reviewed, same discipline as the BGI PRD's own §7 item 4.
