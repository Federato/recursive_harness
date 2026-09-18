# Excel Rater Build Guide — Special (Building & Contents)

**Written:** 2026-09-02.

**Source material:** `CauseOfLoss_Building_RatingAlgorithms.md` §"Special — rate build-up" /
§"Special — premium" + `BasicGroupI_ERC_Tables.md` (Building); `CauseOfLoss_PersonalProperty_
RatingAlgorithms.md` §"Special — rate build-up" / §"Special — premium" +
`PersonalProperty_ERC_Tables.md` (Contents), both cross-checked against `CFCW20260601V01`. See
`Excel_Rater_Overview.md` for the shared workbook shell, and the three forms already built for
comparison throughout.

---

## 0. Live rater build status — Building (updated 2026-09-09)

Building's full 9-step chain (§4 below) is now wired live in `CFRater1.01.xlsb`, `Bldg Rating
Worksheet` rows 79–92 under the `Special` header, fed by `CoreScratchpad` rows 111–125 and four new
data tables on the `BldgSpecialRating` tab (columns A–AE). Four standalone Supporting Tables
workbooks were built to source this: `Special_BaseRate_Building.xlsx`, `Special_TheftExclusionFactor_
Building.xlsx`, `Special_LOIFactor_Bldg.xlsx`, `Special_DeductibleFactor.xlsx`.

**Audited 2026-09-09** — every live value for the three populated non-Broad test buildings (NY, AK,
CA) was independently recomputed from the raw ISO CSVs and matched exactly (`BaseRate`,
`TheftExclusionFactor`, `LOIFactor`'s interpolation, `DeductibleFactor`), including correct Y/N gating
on `TheftExclusionAttached`. `FINAL RATE` was correct for every tested building.

**One real gap the audit found, fixed for one of three cells:** `TheftExclusionFactor`, `LOIFactor`,
and `DeductibleFactor` were all wired without the `CauseOfLoss = "Special"` gate the source rules
(`SetSpecialTheftExclusionFactor`, `SetSpecialLOIFactor`, `SetDeductibleFactorSpecial`) explicitly
require — confirmed by a Broad-cause-of-loss test building (AL) showing live non-1.0 "Special" values
on those three rows even though `BaseRate` correctly zeroed out for it. `FINAL RATE` was still correct
in every case, because `BaseRate`'s zero cascades through the entire multiplication chain regardless —
but the intermediate cells were misleading. `TheftExclusionFactor` (row 83) has been fixed with an
outer `IF('Location Inputs'!C18<>"Special",1,...)` gate. **`LOIFactor` (row 87) and `DeductibleFactor`
(row 90) still need the same gate applied** — see §4 steps 5 and 8 below for the exact wording.

Not yet built for Building: the Builders Risk branch of `LOIFactor` (needs a reporting-form limit
field that doesn't exist on `Location Inputs`), the blanket branches of `LOIFactor`/`DeductibleFactor`,
and Legal Liability/blanket premium (§7).

## 0.5. Live rater build status — Contents (updated 2026-09-10)

Substantial progress this session, worked out live-formula-first (read via Excel COM, read-only)
rather than doc-first — this section is catching the doc up to what's actually in `CFRater1.01.xlsb`.

**Live and confirmed working:**
- `Location Inputs!C20` (Occupancy Category) — real dropdown, 8 fixed values, confirmed against
  `DomainOccupancyCategory` (countrywide, no state variation): Residential Apartments and
  Condominiums, Offices, Mercantile, Motels and Hotels, Institutional, Industrial and Processing,
  Service, Contractors.
- `Location Inputs!C21` (Occupancy Severity) — **not a second dropdown**, derived live via
  `=IFERROR(VLOOKUP(CoreScratchpad!C171,ContentsTables!$CI$2:$CM$56857,5,FALSE),"Severity")`, keyed on
  State+OccupCategory+ClassCode against the full `OccupCategoryRiskSeverity` table (56,856 rows, 46
  states × 1,236 base combos), already pasted into `ContentsTables!CI:CM` with a concatenated `Code`
  column. Resolving correctly for the AL/0321 test case ("Not Applicable").
- `CoreScratchpad!C144:C154` — BGII Contents LOI Factor, live, resolving.
- `CoreScratchpad!C156:C166` — Broad Contents LOI Factor, live, resolving.
- `CoreScratchpad!C171:C172` — composite-key aliases (`SeverityMix`, `RateLookup`) for the
  OccupCategory/Severity and SpecialBaseRate lookups, following a VLOOKUP+concatenated-key convention
  (not the SUMPRODUCT-array convention used in the BGII/Broad blocks above) — this is the convention to
  follow for any further Special-section lookups.

**Tables built this session, ready to paste in (not yet confirmed pasted for all of these):**
- `SpecialBaseRate_Contents_withCode.xlsx` — `SpecialPrsnlPropRate` (585 rows, 45 states × 13
  OccupCategory/Severity combos, `Code` column added) + `SpecialPrsnlPropRate_FL` (13 rows, FL's own
  Residential/Non-Residential split — see the FL correction in §3 below).
- `OccupCategoryRiskSeverity_Contents.xlsx` — superseded by the fully-pasted, working `ContentsTables!
  CI:CM` version above; kept for reference.
- `SpecialTheftExclusionFactor_Contents.xlsx` — 368 rows (46 states × 8 OccupCategory rows, `Code`
  column), not yet confirmed pasted into `ContentsTables`.
- `Broad_LOIFactor_Contents.xlsx` — already pasted (`ContentsTables!BR:BV`), reused by Special's own
  LOI factor (`LookupBroadSpecialLOIFactor` is the exact same rule/table Broad uses — no separate
  Special LOI table exists at all, confirmed against the rule XML).

**Not yet built:** `PrsnlPropTerrMultiplier` (own lookup, `SpecialRatingTerr` not yet confirmed as an
input field), `DeductibleFactorSpecial`'s CoreScratchpad wiring (table already exists —
`Special_DeductibleFactor.xlsx`, built in an earlier session, confirmed reusable for Contents since the
lookup rule/table is identical, just Contents' own limit fields — see the correction below), and the
worksheet row wiring for most of the Contents Special block (`Contents Rating Worksheet` rows 74–95,
skeleton exists, mostly blank).

**Corrected this session — do not assume Building's and Contents' `SpecialTotAmtInsurance` share a
value.** They don't, despite having the identical field name and both ultimately feeding
`DeductibleFactorSpecial`. `CommercialPropertyStructureRules.Rule.xml` and
`CommercialPropertyPersonalPropertyRules.Rule.xml` each define their **own separate**
`SetSpecialTotAmtInsurance` rule (confirmed by grepping both files, not assuming from one). Building's
version sums `StructureLimitToUse + OccupancyTotSpecialAmtInsuranceSum +
SpecialClassRiskSpecialTotAmtInsurance` (a combined location total — see §4's correction). Contents'
version sums only its own `CommercialPropertyPersonalProperty` items under Special (confirmed by reading
the full rule end-to-end, not just the opening `ForEach` — no Building term anywhere in it). Same
field name, two genuinely different values — **do not point Contents' `DeductibleFactorSpecial` at
Building's cell**, they will not match. Same is true of `SpecialIncludingTheftTotAmtInsurance` (also
separately defined per `DataDefGroup`, confirmed both rules exist independently).

**Watchman vs. Burglary Alarm — genuinely different mechanisms, correcting §2/§3 below.** Watchman
Credit Factor **is** a real table lookup (`WatchmanCreditFactorDef`, keyed State+converted-service-code,
CW-only 4 rows, zero state overrides) fed by a description→code domain table
(`DomainBurgRobbery3ConvertedCode`). Burglary Alarm Credit Factor **is not** a lookup at all — no
`SetBurglaryAlarmCreditFactor` rule exists anywhere in the CW package; `BurglaryAlarmSystemType` only
sets a **min/max validation range** (`DomainBurglaryAlarmCreditFactorRange`, e.g. 0.73–0.92 for "Central
Station With Keys"), and the actual factor is a value the underwriter enters directly within that range.
Built `WatchmanBurglaryAlarmCreditFactors.xlsx` (both sheets) to reflect this correctly.

---

## 1. What changes moving to Special — the pattern inverts

Every form built so far has been *roughly* the same complexity for Building and Contents, with Contents
usually the slightly simpler of the two (no roof factor, no vacancy addend, no multi-residential
credit). Special breaks that pattern entirely: **Building's Special chain is the shortest flat-rate form
in this whole document set (9 steps, no class/construction/territory dimension at all); Contents' Special
chain is the longest and richest of any form built so far — 14 steps**, with its own territory
multiplier, its own occupancy-based base-rate keys, and two protective-safeguard credits that don't
exist anywhere in Building's ruleset. The source doc states this outright: Personal Property's Special is
"structurally the most different of the four PP forms, and the opposite of Building's Special."

| | Building | Personal Property (Contents) |
|---|---|---|
| Chain length | 9 steps | **14 steps** |
| Base rate | flat statewide constant (`SpecialBuildingRate`/`SpecialBuildersRiskRate`, keyed only on `"Y"`) | keyed on **OccupCategory + OccupCategoryRiskSeverity** (`SpecialPrsnlPropRate`) — a real class-like dimension Building's Special never has |
| Territory | **none at all** — the only form/coverage combination in this document set with zero territory dependency | its own multiplier, `PrsnlPropTerrMultiplier` — a dimension unique to Contents' Special, absent from every other Contents form too |
| Theft-exclusion credit | flat CW constant, 0.88 | keyed on `OccupCategory` — a per-occupancy factor, not a single number |
| Protective-safeguard credits | none | `WatchmanCreditFactor`, `BurglaryAlarmCreditFactor` — schedule-sourced values copied directly from the insured's protective-safeguards record, not rate-table lookups; no Building equivalent |
| Deductible-by-location | own local `Lookup`, theft-keyed | `Copy`'d from an ancestor record — the one PP deductible-by-location factor across every form that is externally sourced rather than computed |
| Deductible factor | own local `Choose`, theft-keyed | **also** computed locally with its own `Lookup` — the one deductible factor among all four PP forms that is *not* copied from an ancestor |
| Legal Liability premium uses | raw, unadjusted `SpecialRate` | `SpecialCauseOfLossAdjustment` (already includes the theft-exclusion factor) — a genuine Building/Contents premium-formula divergence, not just a naming difference |
| Premium rounding | nested `Product`, no `Round` wrapper | same nested-`Product` pattern |
| Premium file vs. other three forms | **not** a renamed copy — real structural differences | **not** a renamed copy — real structural differences, plus a Contents-only sublimit override (see §6) |

**Three known data gaps for Contents' Special — the worst of any form/coverage combination documented
so far.** `SpecialPrsnlPropRate`, `SpecialPrsnlPropTheftExclusionFactor`, and `PrsnlPropTerrMultiplier`
are **all three** confirmed header-only at the countrywide level. Building's Special has one such gap
(`SpecialBuildingRate`; `SpecialBuildersRiskRate` does resolve, CW 0.015). Every other form built so far
had at most two gapped tables for a given coverage; Contents' Special has three, on top of the same
`BroadSpecialLOIFactorPrsnlProp` this project already flagged as unverified in `Excel_Rater_Broad.md`.

---

## 2. `Locations_Buildings` additions for this form

### Shared additions

| Field | Feeds | Notes |
|---|---|---|
| `TheftExclusionAttached` (Y/N) | drives `SpecialTheftExclusionIndicator` for both coverages | represents whether form CP 10 33 (Theft Exclusion) is attached — a real ISO form, not a synthetic flag |
| `TheftDeductible` | Special's deductible-by-location and deductible-factor branches, both coverages | the by-location and standard deductible logic both key off this separately from the plain `Deductible` column when a distinct theft deductible applies |

### Building-only additions

None beyond what Basic Group I already defined — Special reuses `Bldg_RoofSurfacingFactorInputs`,
`Bldg_CovType`, `Bldg_Limit`, `Bldg_IncludedInBlkt`, `ClassCode` (only to detect Builders Risk class
1150), and `Deductible`/`TheftDeductible` above.

### Contents-only additions

| Field | Feeds | Notes |
|---|---|---|
| `PP_OccupCategory` | base-rate lookup key, theft-exclusion-factor lookup key, severity-derivation key | Contents' Special-only class-like dimension; in ISO's own rules this is `Copy`'d down from the Occupancy Class level, shared by every PersonalProperty record under it — modeled here as a per-building column for this pass. **Real dropdown, exactly 8 values, confirmed live** (`DomainOccupancyCategory`, countrywide, no state variation): Residential Apartments and Condominiums, Offices, Mercantile, Motels and Hotels, Institutional, Industrial and Processing, Service, Contractors. |
| `PP_OccupCategoryRiskSeverity` | base-rate lookup key (second key, alongside `PP_OccupCategory`) | **Corrected 2026-09-10 — not a second dropdown.** Derived from `PP_OccupCategory` + `ClassCode` via `LookupOccupCategoryRiskSeverity` against `OccupCategoryRiskSeverityDef` (46 states × 1,236 base combos — 154–158 class codes × 8 categories). Confirmed live and working in `CFRater1.01.xlsb`. There is no ClassCode→OccupCategory derivation the other direction — checked directly, 154 of 158 class codes appear under all 8 categories, so OccupCategory has to stay a genuine manual selection. |
| `PP_SpecialRatingTerr` | territory-multiplier lookup key | a genuinely different territory field from the shared `Territory` column Basic Group I uses and the `BasicGroupIIRatingTerr` Basic Group II uses — Special's own territory concept |
| `PP_ProtectiveSafeguardsOnFile` (Y/N) | gates whether the two credit factors below apply | represents whether a `CommercialPropertyBurglaryAndRobberyProtectiveSafeguards` schedule record exists |
| `PP_WatchmanCreditFactor` | `AdjustedRate` multiplicand | **Corrected 2026-09-10 — this one IS a real table lookup**, not a schedule copy. `TypeOfWatchmanSrvc` (a service-description dropdown) → `DomainBurgRobbery3ConvertedCode` → a short code (`Option75`/`Option85`/`Option95`/`Null Option`) → `LookupWatchmanCreditFactor(State\|CW, code)` against `WatchmanCreditFactorDef` (CW-only, 4 rows, zero state overrides: 0.86/0.92/0.97/1.0). |
| `PP_BurglaryAlarmCreditFactor` | `AdjustedRate` multiplicand | **Confirmed genuinely not a lookup** — no `SetBurglaryAlarmCreditFactor` rule exists anywhere in the CW rule package (grepped every rule file). `BurglaryAlarmSystemType` only sets a min/max validation range (`DomainBurglaryAlarmCreditFactorRange` — e.g. 0.73–0.92 for "Central Station With Keys," 0.89–0.97 for "Local Alarm"); the actual value is entered directly by the underwriter within that range and copied through as-is. Enter the schedule's own value here, don't try to derive it. |
| `PP_AlcoholicBeveragesTaxExclusion` (Y/N) + `PP_AlcoholicBeveragesTaxExclusionLimit` | Contents' premium formula only — see §6 | Contents-only sublimit override, no Building equivalent |

---

## 3. `Rate_Tables` additions for this form

**Reused from `Excel_Rater_Broad.md` (same tables, no new introduction needed):**

`BroadSpecialLOIFactorBldg` (Building) / `BroadSpecialLOIFactorPrsnlProp` (Contents) — Special shares
its LOI table with Broad in both coverages, exactly the pairing `Excel_Rater_Broad.md` §1 already noted.
Still flagged as not independently row-counted.

**Shared, new key value on an existing table:**

| Table | New key |
|---|---|
| `Deductible250Factor` | `causeOfLoss = "Special"` — same table Broad and Basic Group I already use, different constant |
| `DeductibleFactor` | Special is the only PP form that reads this locally rather than via an ancestor `Copy` — same table, real local use this time |

**Building-only:**

| Table | Keys | CW rows filed? |
|---|---|---|
| `SpecialBuildingRate` | State\|CW, `"Y"` | CW header-only, but **45 of the 46 non-FL states file their own row** (own-edition pull, not the CW snapshot). FL doesn't use this table at all — own rule mechanism, see the correction below. |
| `SpecialBuildersRiskRate` | State\|CW, `"Y"` | Yes — CW 0.015, resolves all 47 states, zero state overrides |
| `SpecialBldgTheftExclusionFactor` | State\|CW, `"Y"` | Yes — CW 0.88 |
| `SpecialBuildingRateResidential` / `...NonResidential` (FL-only) | State="FL", `ClassCode` (21-code residential list vs. everything else) | FL-only tables, no CW/other-state equivalent — 0.03 / 0.035, both confirmed resolvable |

**Contents-only:**

| Table | Keys | CW rows filed? |
|---|---|---|
| `SpecialPrsnlPropRate` | State\|CW, `PP_OccupCategory`, `PP_OccupCategoryRiskSeverity` | CW header-only, **but 45 of 46 non-FL states file their own 13-row set** — same "CW header-only ≠ unresolvable" pattern as Building's `SpecialBuildingRate` (§3 correction below). Built as `SpecialBaseRate_Contents_withCode.xlsx`. **FL doesn't file this table at all** — same kind of mechanism override Building's FL has, but a different split: FL files `SpecialPrsnlPropRateResidential` (1 row, flat 0.125, no OccupCategory/Severity key) and `SpecialPrsnlPropRateNonResidential` (12 rows, everything except Residential). Resolve FL by testing `PP_OccupCategory = "Residential Apartments and Condominiums"` first (mapped to FL's own bare `"Residential"` label internally — a judgment call, not something read off a rule, since FL never exposes a different dropdown value) before falling through to the 12-row non-residential lookup. |
| `SpecialPrsnlPropTheftExclusionFactor` | State\|CW, `PP_OccupCategory` | CW header-only, **but all 46 states file their own 8-row set** (one per OccupCategory), including FL under the standard table name (no split for this one). Built as `SpecialTheftExclusionFactor_Contents.xlsx`. |
| `PrsnlPropTerrMultiplier` | State\|CW, `PP_SpecialRatingTerr` | **Not yet checked this session — still the doc's original "header-only, confirmed empty" status.** Check per-state filings the same way the two tables above were before assuming it's unresolvable. |

**Genuinely not rate tables — `PP_BurglaryAlarmCreditFactor` only.** No `SetBurglaryAlarmCreditFactor`
rule exists anywhere in the CW package; it's a schedule value entered directly within a min/max range
(§2). **Correction:** `PP_WatchmanCreditFactor` **is** a real table lookup after all — see §2's
correction — don't treat it the same way as Burglary Alarm.

**Correction (2026-09-09) — `SpecialBuildingRate` is not the blocker this doc originally described, and
Florida turned out to be a real mechanism, not a gap.** Built out in `Special_BaseRate_Building.xlsx`
(`.scratch/build_special_baserate.py`), pulling `SpecialBuildingRate`/`SpecialBuildersRiskRate` from
every state's own correct edition per `State_ERC_CW_Editions.csv`, not the CW snapshot alone. CW
genuinely has zero rows for `SpecialBuildingRate`, exactly as flagged above — but **45 of the 46 non-PR,
non-FL states file their own row**, each pulled and stamped with its own state code (no CW placeholder
rows, per project convention). `SpecialBuildersRiskRate` resolves everywhere: CW is 0.015 and no state
files an override.

**Florida is the one true exception, and it is not a coverage gap.** FL doesn't file the flat
`SpecialBuildingRate` table at all — checked directly against `CommercialPropertyStructureRules.Rule.xml`
in FL's own edition (`CF FL 20241201 V01`, snapshot `20230801v1`), FL has a `RuleTypeStateSpecific` rule
override (confirmed the *only* one of the 47 states with this override) that branches the `BaseRate` step
on `ClassCode` into two separate tables instead: `SpecialBuildingRateResidential` (**0.03**) for 21 named
residential class codes (`0074–0079, 0196–0198, 0311–0313, 0321–0323, 0331–0333, 0341–0343`), and
`SpecialBuildingRateNonResidential` (**0.035**) for everything else. FL Special Building coverage rates
just fine — it just needs a ClassCode-branched lookup instead of the flat `State|"Y"` lookup every other
state uses. Modeled as its own "FL Residential Split" sheet in the workbook, with the branch folded into
`Calc_Building_Special`'s `BaseRate` formula (see the corrected step 2 below).

This "CW header-only ≠ unresolvable" trap is the same one this project already hit and corrected for
Basic Group II's base rate (`build_bgii_baserate.py`) and confirmed clean for Broad's
(`build_broad_baserate.py`) — but FL's residential/non-residential split is a new wrinkle even within that
pattern: it's the first state found in this project overriding the *lookup mechanism itself*, not just
supplying its own row of the same shape.

---

## 4. `Calc_Building_Special` tab — one row per building

Straight translation of `CauseOfLoss_Building_RatingAlgorithms.md`'s 9-step chain
(`SetSpecialRatesAndFactors`, line 9529).

1. **`TheftExclusionFactor`** — **live, `Bldg Rating Worksheet!C83`, audited 2026-09-09**:
   ```
   if CauseOfLoss = "Special" and TheftExclusionAttached = "Y":
       LookupSpecialBldgTheftExclusionFactor(State|CW, "Y")     # CW 0.88
   else:
       1.0
   ```
   Live formula: `=IF('Location Inputs'!C18<>"Special",1,IFERROR(IF('Location Inputs'!C36="Yes",
   VLOOKUP('Location Inputs'!C7,BldgSpecialRating!$M$2:$O$47,3,FALSE),1),1))`. Table on
   `BldgSpecialRating!M:O` (from `Special_TheftExclusionFactor_Building.xlsx`).
2. **`BaseRate`** — **live, `Bldg Rating Worksheet!C80`**, fed by `CoreScratchpad!C111:C114`:
   ```
   if CauseOfLoss = "Special":
       if ClassCode = "1150": LookupSpecialBuildersRiskRate(State|CW, "Y")      # CW 0.015, resolves all 47 states
       elif State = "FL":     LookupFLSpecialBuildingRateResidentialOrNonRes(ClassCode)
                                   # FL-only state-specific rule -- 0.03 for 21 named residential class
                                   # codes, 0.035 for every other class code. Corrected 2026-09-09; see §3.
       else:                  LookupSpecialBuildingRate(State|CW, "Y")          # CW header-only, but 45 of
                                                                                  # 46 non-FL states file their
                                                                                  # own row -- see §3 correction
   else: 0.0
   ```
3. **`Rate`** — **live, `Bldg Rating Worksheet!C82`** = `BaseRate × LCM` — round to 3dp. No addends, no
   territory, no protection class, no construction — the entire rate step.
4. **`COLAdj`** — **live, `Bldg Rating Worksheet!C85`** = `Rate × TheftExclusionFactor ×
   RoofSurfacingACVFactor` — round to 3dp. Unlike the Basic forms' COL-adjustment rules, this one has
   no null-guard: it always recomputes. `RoofSurfacingACVFactor` (row 84) is wired as `=C9`, a direct
   copy of BGI's cell — confirmed via the rule XML that this factor is a single Structure-level
   computation with no CauseOfLoss dependency at all (same table Broad's `=C9` already uses), so no
   gate needed on this one either.
5. **`LOIFactor`** — **live, `Bldg Rating Worksheet!C87`**, fed by `CoreScratchpad!C115:C121`, table on
   `BldgSpecialRating!Q:U` (from `Special_LOIFactor_Bldg.xlsx`, same table Broad uses) — four-way:
   blanket copy from `BlktSpecialLOIFactor`; Builders Risk → `LookupBroadSpecialLOIFactorWithArgs`;
   other cov types not in (Leasehold Interest, Legal Liability, No Coverage) →
   `LookupBroadSpecialLOIFactorBldg(Limit)`; else `1.0`. **Live version only builds the last branch**
   (Builders Risk and blanket not built — no reporting-form/blanket fields exist yet on
   `Location Inputs`), and per the 2026-09-09 audit **still needs the `CauseOfLoss = "Special"` gate**
   applied: `C87` should become `=IF('Location Inputs'!C18<>"Special",1,CoreScratchpad!C121)`.
6. **`AdjustedRate`** — **live, `Bldg Rating Worksheet!C88`** = `COLAdj × CoinsuranceFactor × LOIFactor`
   — the shared `CoinsuranceFactor`, no Special-specific coinsurance rule.
7. **`DeductibleByLocationFactor`** — **live, `Bldg Rating Worksheet!C89`**:
   ```
   LookupDeductibleByLocationFactor(...)
       if a deductible-by-location record exists and its TheftDeductible is neither blank nor "Not Applicable"
   else 1.0
   ```
   Theft-driven, not the wind/hail-driven version Basic Group II uses. **Simplified in the live
   build**: wired as `=C19` (a direct copy of BGI's already-computed cell), since the underlying table
   (`DeductibleByLocationFactor`, State|CW,"Y", flat 0.995, zero state variation) and BGI's gate
   (`Per Location Deductible` flag) are the same either way — the real theft-specific gate
   (`TheftDeductible` non-blank/non-N/A) can't be modeled until that field exists on `Location Inputs`.
8. **`DeductibleFactor`** — **live, `Bldg Rating Worksheet!C90`**, fed by `CoreScratchpad!C122:C125`,
   tables on `BldgSpecialRating!W:AA` (`DeductibleFactor Special`, "Other Cause Of Loss" slice) and
   `!AC:AE` (`Deductible250Factor Special`, CW=1.1 — confirmed distinct from Broad's 1.05) — both from
   `Special_DeductibleFactor.xlsx`:
   ```
   Branch 1 (separate theft deductible): SpecialTheftExclusionIndicator = 0 and TheftDeductible not in ("", "Not Applicable", "250") and TheftDeductible <> Deductible:
       LookupDeductibleFactor(TheftDeductible, SpecialIncludingTheftTotAmtInsurance, "Other Cause Of Loss")
   Branch 2 (flat $250): Deductible = "250" and TheftDeductible = "250":
       LookupDeductible250Factor("Special", ...)
   Branch 3 (none): Deductible = "Not Applicable": 1.0
   Branch 4 (standard): Deductible <> "":
       LookupDeductibleFactor(Deductible, SpecialTotAmtInsurance, "Other Cause Of Loss")
   ```
   **Corrected 2026-09-09**: Branch 1's gate is `SpecialTheftExclusionIndicator = 0`, confirmed directly
   against `SetDeductibleFactorSpecial` in the rule XML — not `TheftExclusionAttached <> "Y"` as
   previously documented here (an assumption from before this session's rule-XML verification pass).
   **Live version only builds branches 2–4** (Branch 1, the separate-theft-deductible override, needs
   `TheftDeductible` as its own field, which doesn't exist on `Location Inputs` yet — same category of
   gap as the LOI Builders Risk branch above). Confirmed correct against `SetDeductibleFactorSpecial`
   in the rule XML, including the blank-deductible-zeroes-the-rate `Otherwise → 0.0` branch, which the
   live formula reproduces. Per the 2026-09-09 audit, **still needs the `CauseOfLoss = "Special"` gate**:
   `C90` should become `=IF('Location Inputs'!C18<>"Special",1,CoreScratchpad!C125)`.
9. **`FinalRate`** — **live, `Bldg Rating Worksheet!C92`** = `AdjustedRate × DeductibleByLocationFactor
   × DeductibleFactor × MultiResidentialPropSpecialCreditFactor`. `MultiResidentialPropSpecialCreditFactor`
   (row 91) is wired as `=C21`, a direct copy of BGI's cell — confirmed via the rule XML that this factor
   is genuinely CauseOfLoss-agnostic by construction (one shared Structure-level rule feeds every form
   identically), so no gate or caveat needed on this one, unlike rows 87/89/90.

**Correction:** `SpecialTotAmtInsurance` is NOT the Building's own limit — confirmed directly against the
rule XML (`SetSpecialTotAmtInsurance`) as
`SpecialTotAmtInsurance = StructureLimitToUse + OccupancyTotSpecialAmtInsuranceSum + SpecialClassRiskSpecialTotAmtInsurance`,
the same combined-location-total pattern as plain `TotAmtInsurance` (Building's own limit **plus** every
Contents item's limit at the location **plus** Special Class Risk amounts), just using the Special-scoped
rollup fields instead of the general ones. `SpecialIncludingTheftTotAmtInsurance` **confirmed 2026-09-10**
to follow the same shape — Building's own local `SetSpecialIncludingTheftTotAmtInsurance` rule exists
(`CommercialPropertyStructureRules.Rule.xml`), gated the same way (`CauseOfLossToUse = "Special"` and
`SpecialTheftExclusionIndicator = 0`), same combined-location-total pattern. This was previously documented here as
`Bldg_Limit`, matching the same wrong simplification made throughout Basic Group I's, Basic Group II's, and
Broad's building tabs — deliberately backlogged until Contents is built (see project memory
`project_deductiblefactor-uses-location-total-not-building-limit`).

---

## 5. `Calc_Contents_Special` tab — one row per building

Straight translation of `CauseOfLoss_PersonalProperty_RatingAlgorithms.md`'s 14-step chain
(`SetSpecialRatesAndFactors`, line 4382) — the longest chain of any form/coverage combination built so
far.

1. **`DeductibleByLocationFactor`** — **confirmed 2026-09-09 against the rule XML**: not computed at
   all in Contents' own rules, literally a `Copy` from `../../../../SpecialDeductibleByLocationFactor`
   — i.e. Contents just inherits Building's already-computed value directly. Build as a copy of
   whatever cell holds Building's Special `DeductibleByLocationFactor` result.
2. **`DeductibleFactor`** — **this one is genuinely computed locally in ISO's own rules**, the only
   deductible factor of any Contents form that is. **Confirmed 2026-09-09, branch-for-branch identical
   to Building's step 8** — same five-condition Branch 1 gate (`SpecialTheftExclusionIndicator = 0`
   AND `TheftDeductible` not in `("","Not Applicable","250")` AND `TheftDeductible <> Deductible`),
   same Branch 2/3/4/Otherwise, and the underlying `LookupDeductibleFactor`/`LookupDeductible250Factor`
   rule bodies are byte-for-byte identical in their key structure (same table, same key order), just
   duplicated per `DataDefGroup` as ISO does for every rule. **Correction to this doc's earlier text**:
   Building does *not* read `TheftExclusionAttached` directly in this step — both Building's and
   Contents' rules key Branch 1 on `SpecialTheftExclusionIndicator = 0` identically. Uses
   `SpecialIncludingTheftTotAmtInsurance`/`SpecialTotAmtInsurance` by the same field names and branch
   logic as Building — but NOT the same underlying values. Corrected 2026-09-10: each `DataDefGroup`
   (`CommercialPropertyStructure` vs `CommercialPropertyPersonalProperty`) defines its own separate
   `SetSpecialTotAmtInsurance`/`SetSpecialIncludingTheftTotAmtInsurance` rule — confirmed by grepping
   both rule files independently, not assumed from finding one. Building's versions roll up a combined
   location total (its own limit + Special-scoped Contents/Occupancy sums + Special Class Risk);
   Contents' versions sum only its own `CommercialPropertyPersonalProperty` items. Do not wire Contents'
   `DeductibleFactor` as a copy of Building's cell for this factor — they will diverge whenever Building
   carries any insured value of its own, which is the normal case.
3. **`TheftExclusionFactor`**:
   ```
   if CauseOfLoss = "Special" and TheftExclusionAttached = "Y":
       if PP_OccupCategory <> "": LookupSpecialPrsnlPropTheftExclusionFactor(State|CW, PP_OccupCategory)   # no CW row filed
       else: 0.0
   else: 1.0
   ```
4. **`BaseRate`**:
   ```
   if CauseOfLoss = "Special" and PP_OccupCategory <> "" and PP_OccupCategoryRiskSeverity <> "":
       LookupSpecialPrsnlPropRate(State|CW, PP_OccupCategory, PP_OccupCategoryRiskSeverity)   # no CW row filed
   else: 0.0
   ```
5. **`TerrMultiplier`** *(no Building equivalent at all)*:
   ```
   if CauseOfLoss = "Special" and PP_SpecialRatingTerr <> "":
       LookupTerritoryMultiplier(State|CW, PP_SpecialRatingTerr)   # no CW row filed
   else: 0.0
   ```
6. **`Rate`**:
   ```
   0.0   if CauseOfLoss <> "Special"
   else TerrMultiplier × (BaseRate × LCM)
   ```
   round to 3dp. Note the multiplier applies to the whole `BaseRate × LCM` product, not to `BaseRate`
   alone.
7. **`COLAdj`**:
   ```
   0.0   if PP_CovType = "Valuable Papers and Records - Other Than Electronic Data"
   else Rate × TheftExclusionFactor
   ```
   No roof-surfacing factor — none exists anywhere in the Contents ruleset.
8. **`WatchmanCreditFactor`** *(Contents-only, no Building equivalent)*:
   ```
   PP_WatchmanCreditFactor    if SpecialTheftExclusionIndicator = 0 and PP_ProtectiveSafeguardsOnFile = "Y"
   else 1.0
   ```
9. **`BurglaryAlarmCreditFactor`** *(Contents-only)*: same gate and shape as step 8, reading
   `PP_BurglaryAlarmCreditFactor`.
10. **`LOIFactor`** — three-way: blanket copy from `BlktSpecialLOIFactor`; else
    `LookupBroadSpecialLOIFactorPrsnlProp(OccupSpecialTotAmtInsurance)` when `PP_CovForm` not in (Legal
    Liability, Tobacco Sales Warehouses) and the amount is positive; else `1.0`.
11. **`AdjustedRate`** = `COLAdj × CoinsuranceFactor × WatchmanCreditFactor × BurglaryAlarmCreditFactor × LOIFactor`
    — two more multiplicands than Building's equivalent step, the two protective-safeguard credits.
12. **`FinalRate`** = `AdjustedRate × DeductibleByLocationFactor × DeductibleFactor` — no
    multi-residential credit, consistent with every Contents form.

(Numbered 1–12 above to match every distinct value computed; ISO's own step count of 14 includes the two
occupancy-category prerequisite steps this workbook treats as entered directly on `Locations_Buildings`
rather than derived — `PP_OccupCategory`/`PP_OccupCategoryRiskSeverity` are plain `Copy`s from the
Occupancy Class level in ISO's rules, so there's nothing to compute here beyond reading the column.)

---

## 6. `Premium_Summary` formulas for this form

Both premium files are, like Broad's, **not** renamed copies of the other forms — both source docs
confirm real structural differences, and this form adds one Contents-only wrinkle neither Building nor
any prior form has: a sublimit override for the Alcoholic Beverages Tax Exclusion endorsement (CP 12 11).

```
PP_LimitToUse =
    PP_AlcoholicBeveragesTaxExclusionLimit    if PP_AlcoholicBeveragesTaxExclusion = "Y"
    else PP_Limit
```

Compute this once, feed it into Branch A below in place of the raw `PP_Limit` — Building has no
equivalent column or override at all.

```
Bldg_Premium (Special) =
    if Bldg_CovType in ("Building","Builders Risk","Improvements and Betterments","Condominium Association")
       and CauseOfLoss = "Special" and Bldg_IncludedInBlkt = "No":
        Calc_Building_Special.FinalRate × (Bldg_Limit / 100) × PackageModFactor
          × MultiPremiumAndDispersionCreditFactor × IRPMFactor
          × CyberIncidentExclusionFactorSpecial × CyberIncidentExclusionCOLExcptnsFactorSpecial
        [nested Product, DecimalPlaces=0 at each step — no outer ROUND(), unlike Basic Group I/II/Broad]
    elif Bldg_CovType = "Legal Liability" and CauseOfLoss = "Special":
        Calc_Building_Special.Rate × LegalLiabilityFactor × LegalLiabAddlInsurableIntFactor × (Bldg_Limit/100)
          × PackageModFactor × IRPMFactor × CyberIncidentExclusionFactorSpecial × CyberIncidentExclusionCOLExcptnsFactorSpecial
        [not built this pass — see §7; uses the RAW rate, not COLAdj]
    elif Bldg_IncludedInBlkt = "Yes" and BlktCauseOfLossValue = "Special":
        [blanket branch — not built this pass, see §7]
    else: 0.0

PP_Premium (Special) =
    if PP_CovForm not in ("Legal Liability Coverage Form","Tobacco Sales Warehouse Coverage Form")
       and CauseOfLoss = "Special" and PP_IncludedInBlkt = "No":
        Calc_Contents_Special.FinalRate × (PP_LimitToUse / 100) × PackageModFactor
          × MultiPremiumAndDispersionCreditFactor × IRPMFactor
          × CyberIncidentExclusionFactorSpecial × CyberIncidentExclusionCOLExcptnsFactorSpecial
        [same nested-Product rounding as Building]
    elif PP_CovForm = "Legal Liability Coverage Form" and CauseOfLoss = "Special":
        Calc_Contents_Special.COLAdj × LegalLiabFactor × LegalLiabAddlInsurableIntFactor × (PP_Limit/100)
          × PackageModFactor × IRPMFactor × CyberIncidentExclusionFactorSpecial × CyberIncidentExclusionCOLExcptnsFactorSpecial
        [not built this pass — see §7; uses COLAdj, NOT the raw rate — see the callout below]
    elif PP_IncludedInBlkt = "Yes" and BlktCauseOfLossValue = "Special":
        [blanket branch — not built this pass, see §7]
    else: 0.0
```

**Worth flagging even though neither Legal Liability branch is built this pass:** when it is built, don't
copy Building's formula onto Contents. Building's Legal Liability branch uses the raw, unadjusted
`SpecialRate` — the theft-exclusion factor and roof-surfacing factor never reach Legal Liability premium.
Contents' equivalent branch uses `SpecialCauseOfLossAdjustment`, which **already includes** the
theft-exclusion factor. This is a real formula difference between the two coverages under the same form,
not a naming difference — the kind of thing a naive copy-and-rename would silently get wrong.

---

## 7. What's deliberately left out of this pass

Same shape as the prior three forms, plus this form's own wrinkle:

- Legal Liability premium branch (both coverages) — remember the raw-rate-vs-COLAdj divergence above
  when this gets built
- Blanket-rated premium branch (both coverages)
- Row-count verification of `BroadSpecialLOIFactorBldg`/`...Prsnlprop`, still unverified since
  `Excel_Rater_Broad.md`

---

## 8. Inputs → rating output — the full picture

### 8.1 What feeds the loss cost (Building)

Special's loss cost has the fewest inputs of any form built so far — one flag (`ClassCode = "1150"`),
no other rating dimension.

| Stage | Reads from | Produces | Tab |
|---|---|---|---|
| 0 — the loss cost itself | `CauseOfLoss = "Special"`, `ClassCode` | `BaseRate` | `Locations_Buildings` → `Calc_Building_Special` |
| 1 — turn it into a rate | `BaseRate`, `Policy.LossCostMultiplier` | `Rate` | `Calc_Building_Special` |
| 2 — adjust for theft exclusion and roof | `Rate`, `TheftExclusionAttached`, `Bldg_RoofSurfacingFactorInputs` | `COLAdj` | `Calc_Building_Special` |
| 3 — apply how the insured chose to insure | `COLAdj`, `Coinsurance`, `Bldg_CovType`, `Bldg_Limit` | `AdjustedRate` | `Calc_Building_Special` |
| 4 — apply the chosen deductible | `AdjustedRate`, `Deductible`, `TheftDeductible`, `Bldg_MultiResIndicator` | `FinalRate` | `Calc_Building_Special` |
| 5 — turn the rate into a dollar premium | `FinalRate`, `Bldg_Limit`, the three `Policy` factors | `Bldg_Premium` | `Premium_Summary` |

### 8.2 Full formula with if/then (Building)

```
TheftExclusionFactor =
    LookupSpecialBldgTheftExclusionFactor(State|CW, "Y")   if CauseOfLoss = "Special" and TheftExclusionAttached = "Y"
    else 1.0

BaseRate =
    if CauseOfLoss = "Special":
        LookupSpecialBuildersRiskRate(State|CW, "Y")    if ClassCode = "1150"
        elif State = "FL": LookupFLSpecialBuildingRateResidentialOrNonRes(ClassCode)   # 0.03/0.035, see §3
        else LookupSpecialBuildingRate(State|CW, "Y")
    else: 0.0

Rate = BaseRate × LCM                                        (round to 3dp — no addends, no other factors)

COLAdj = Rate × TheftExclusionFactor × RoofSurfacingACVFactor    (round to 3dp; always recomputes, no null-guard)

LOIFactor =
    <blanket copy>                                           if Bldg_IncludedInBlkt = "Yes" and BlktIDNum > 0
    elif Bldg_CovType = "Builders Risk":  LookupBroadSpecialLOIFactorWithArgs(...) or 0.0 if limit absent
    elif Bldg_CovType not in ("Leasehold Interest","Legal Liability","No Coverage"):
        LookupBroadSpecialLOIFactorBldg(State|CW, Bldg_Limit)
    else: 1.0

AdjustedRate = COLAdj × CoinsuranceFactor × LOIFactor

DeductibleByLocationFactor =
    LookupDeductibleByLocationFactor(...)   if a by-location record exists and TheftDeductible is non-blank/non-N-A
    else 1.0

DeductibleFactor =
    LookupDeductibleFactor(TheftDeductible, SpecialIncludingTheftTotAmtInsurance, "Other Cause Of Loss")
        if SpecialTheftExclusionIndicator = 0 and TheftDeductible not in ("","Not Applicable","250") and TheftDeductible <> Deductible
    elif Deductible = "250" and TheftDeductible = "250":
        LookupDeductible250Factor("Special", ...)
    elif Deductible = "Not Applicable": 1.0
    elif Deductible <> "":
        LookupDeductibleFactor(Deductible, SpecialTotAmtInsurance, "Other Cause Of Loss")

FinalRate = AdjustedRate × DeductibleByLocationFactor × DeductibleFactor × MultiResidentialPropSpecialCreditFactor

Bldg_Premium =
    if Bldg_CovType in ("Building","Builders Risk","Improvements and Betterments","Condominium Association")
       and CauseOfLoss = "Special" and Bldg_IncludedInBlkt = "No":
        FinalRate × (Bldg_Limit/100) × PackageMod × MultiPremiumDispersion × IRPM
          × CyberExclFactorSpecial × CyberExclCOLExcptnsFactorSpecial      (nested Product, no outer Round)
    elif Bldg_CovType = "Legal Liability" and CauseOfLoss = "Special":  [not built this pass — uses raw Rate, not COLAdj]
    elif Bldg_IncludedInBlkt = "Yes" and BlktCauseOfLossValue = "Special": [blanket — not built this pass]
    else: 0.0
```

### 8.3 What feeds the loss cost (Contents)

Special's Contents loss cost has the richest input set of any form built so far — two base-rate keys
plus its own territory multiplier, none of which Building's Special has any equivalent for.

| Stage | Reads from | Produces | Tab |
|---|---|---|---|
| 0 — the loss cost itself | `CauseOfLoss = "Special"`, `PP_OccupCategory`, `PP_OccupCategoryRiskSeverity` | `BaseRate` | `Locations_Buildings` → `Calc_Contents_Special` |
| 0.5 — the territory multiplier (Contents-only) | `PP_SpecialRatingTerr` | `TerrMultiplier` | `Calc_Contents_Special` |
| 1 — turn it into a rate | `BaseRate`, `TerrMultiplier`, `Policy.LossCostMultiplier` | `Rate` | `Calc_Contents_Special` |
| 2 — adjust for theft exclusion | `Rate`, `TheftExclusionAttached`, `PP_OccupCategory`, `PP_CovType` (Valuable Papers gate) | `COLAdj` | `Calc_Contents_Special` |
| 3 — apply protective-safeguard credits and how the insured chose to insure | `COLAdj`, `Coinsurance`, `PP_WatchmanCreditFactor`, `PP_BurglaryAlarmCreditFactor`, `PP_CovForm`, `PP_Limit` | `AdjustedRate` | `Calc_Contents_Special` |
| 4 — apply the chosen deductible | `AdjustedRate`, `Deductible`, `TheftDeductible` | `FinalRate` | `Calc_Contents_Special` |
| 5 — turn the rate into a dollar premium | `FinalRate`, `PP_LimitToUse` (not plain `PP_Limit` — see §6), the three `Policy` factors | `PP_Premium` | `Premium_Summary` |

### 8.4 Full formula with if/then (Contents)

```
DeductibleFactor =
    LookupDeductibleFactor(TheftDeductible, SpecialIncludingTheftTotAmtInsurance, "Other Cause Of Loss")
        if SpecialTheftExclusionIndicator = 0 and TheftDeductible not in ("","Not Applicable","250") and TheftDeductible <> Deductible
    elif Deductible = "250" and TheftDeductible = "250": LookupDeductible250Factor("Special", ...)
    elif Deductible = "Not Applicable": 1.0
    elif Deductible <> "": LookupDeductibleFactor(Deductible, SpecialTotAmtInsurance, "Other Cause Of Loss")
    (the one Contents deductible factor computed locally, not copied — see §5 step 2)

TheftExclusionFactor =
    if CauseOfLoss = "Special" and TheftExclusionAttached = "Y":
        LookupSpecialPrsnlPropTheftExclusionFactor(State|CW, PP_OccupCategory)   if PP_OccupCategory <> ""
        else: 0.0
    else: 1.0

BaseRate =
    LookupSpecialPrsnlPropRate(State|CW, PP_OccupCategory, PP_OccupCategoryRiskSeverity)
        if CauseOfLoss = "Special" and PP_OccupCategory <> "" and PP_OccupCategoryRiskSeverity <> ""
    else: 0.0

TerrMultiplier =
    LookupTerritoryMultiplier(State|CW, PP_SpecialRatingTerr)   if CauseOfLoss = "Special" and PP_SpecialRatingTerr <> ""
    else: 0.0

Rate = 0.0   if CauseOfLoss <> "Special"
       else TerrMultiplier × (BaseRate × LCM)                        (round to 3dp)

COLAdj = 0.0   if PP_CovType = "Valuable Papers and Records - Other Than Electronic Data"
         else Rate × TheftExclusionFactor                            (no roof factor, ever)

WatchmanCreditFactor = PP_WatchmanCreditFactor   if SpecialTheftExclusionIndicator = 0 and PP_ProtectiveSafeguardsOnFile = "Y"   else 1.0
BurglaryAlarmCreditFactor = PP_BurglaryAlarmCreditFactor   (same gate as above)

LOIFactor =
    <blanket copy>   if PP_IncludedInBlkt = "Yes"
    elif PP_CovForm not in ("Legal Liability Coverage Form","Tobacco Sales Warehouse Coverage Form") and OccupSpecialTotAmtInsurance > 0:
        LookupBroadSpecialLOIFactorPrsnlProp(State|CW, OccupSpecialTotAmtInsurance)
    else: 1.0

AdjustedRate = COLAdj × CoinsuranceFactor × WatchmanCreditFactor × BurglaryAlarmCreditFactor × LOIFactor

FinalRate = AdjustedRate × DeductibleByLocationFactor × DeductibleFactor   (no multi-res multiplier)

PP_LimitToUse = PP_AlcoholicBeveragesTaxExclusionLimit   if PP_AlcoholicBeveragesTaxExclusion = "Y"   else PP_Limit

PP_Premium =
    if PP_CovForm not in ("Legal Liability Coverage Form","Tobacco Sales Warehouse Coverage Form")
       and CauseOfLoss = "Special" and PP_IncludedInBlkt = "No":
        FinalRate × (PP_LimitToUse/100) × PackageMod × MultiPremiumDispersion × IRPM
          × CyberExclFactorSpecial × CyberExclCOLExcptnsFactorSpecial
    elif PP_CovForm = "Legal Liability Coverage Form" and CauseOfLoss = "Special":
        [not built this pass — uses COLAdj, NOT the raw rate, unlike Building's Legal Liability branch]
    elif PP_IncludedInBlkt = "Yes" and BlktCauseOfLossValue = "Special": [blanket — not built this pass]
    else: 0.0
```

---

## 0.6. Live Contents rating audit (2026-09-10)

Full read-only audit of `Contents Rating Worksheet` — every factor and premium row across BGI, BGII,
Broad, and Special, cross-checked against the mechanics established throughout this project. Four real
findings, two now resolved:

1. **BGII `DeductibleFactor` used Building's limit alone instead of the combined total — fixed.**
   `CoreScratchpad!C87` (Building's BGII deductible range-match) still read `'Location Inputs'!C23`
   (Building Limit alone) instead of `C138` (the Building+Contents combined total the BGI/Broad fix
   already established — see the correction note in §4 above). Since Contents' own BGII
   `DeductibleFactor` (`Contents Rating Worksheet!C43`) is a straight copy of Building's cell, it
   inherited the same bug. Fixed by repointing `C87` to `C138`. **One real sub-bug surfaced while fixing
   this**: the original formula's range end (`BldgBGIIRating!$AP$2:AP$6669`) was missing a `$` anchor on
   the second `AP`, so filling right walked the column (AP→AQ→AR→AS...) across buildings instead of
   staying pinned to the `Limit_To` column — caught and corrected in the same pass. Confirmed inert for
   the test case that surfaced it (a percentage deductible routes through a completely different branch,
   `CoreScratchpad!C92`, not the dollar-amount branch this fix touches) — but the fix is correct and will
   matter for any dollar-deductible risk.
2. **Special Contents `RATE` (row 77) was missing the territory multiplier — now closed.**
   `SetSpecialRate` requires `PrsnlPropTerrMultiplier × SpecialBaseRate × LossCostMultiplier`; the table
   (`SpecialContents_Factors.xlsx` / `SpecialContents_Territory.xlsx`, 155 rows, all 46 states file their
   own territory list, 1–14 per state) and the `Special Rating Terr` input field (cascading dropdown via
   `INDIRECT`, named ranges `AK_Special`…`WY_Special` on `PolicyDropdowns!T2:T156`, suffixed `_Special`
   to avoid colliding with the existing plain-state-code named ranges already used by BGI/BGII Territory)
   are both built and wired.
3. **Special Contents `CAUSE OF LOSS ADJUSTMENT` (row 79) is missing the Valuable Papers zero-out —
   open, backlog.** Rule: `0.0 if CovType="Valuable Papers..." else Rate × TheftExclusionFactor`. Live
   formula is just `Rate × TheftExclusionFactor`, no gate. Edge case — only wrong if a Valuable Papers
   Contents item is ever rated under Special.
4. **BGI `ProtClassFactor` (row 8) was a straight copy of Building's, missing Contents' own exclusions —
   now closed.** Confirmed against `SetProtectionClassFactor`
   (`CommercialPropertyPersonalPropertyRules.Rule.xml`, line 3320): Contents excludes
   `ProtectionClassFactor` (forces it to 1.0) under two *unrelated* conditions bundled into the same
   OR-gate — `Group="YARD"` and combustible (unless `YardPropertyIndicator="Yard Property - Non
   Combustible"`), **or** `BldgClassCode` (really the tenant's own class code, field name is
   historical) is 1751 or 1752. These two conditions have nothing to do with each other: 1400/1650/1700
   are the occupancies where property can genuinely sit outdoors (Auto Dismantling, Building Material
   Dealers, Saw/Planing Mills — confirmed against the live `ClassCodes` sheet), so protection class
   (fire department response) is irrelevant to combustible material exposed in a yard; 1751/1752 (Oil
   Distributing – Oil Terminals/LPG Tank Farms, with/without stock) are excluded because they're already
   separately rated on their own specialized hazard basis, unrelated to yard storage at all. Fix:
   ```
   =IF(OR(AND('Location Inputs'!C23="YARD",'Location Inputs'!C_YARD<>"Yard Property - Non Combustible"),
          'Location Inputs'!C17="1751", 'Location Inputs'!C17="1752"),
      1,
      'Bldg Rating Worksheet'!C8)
   ```
   `'Location Inputs'!C23` = Contents Group, `C17` = Tenants Class Code (both pre-existing).
   `YardPropertyIndicator` needed a new field — cascading dropdown, "Not Applicable" for every class
   code except 1400/1650/1700, which get three real choices (Yard Property - Combustible / Yard Property
   - Non Combustible / Personal Property Inside Building), confirmed against
   `DomainYardPropertyIndicator`.

---

## Remaining steps

1. Building's live chain is wired and audited (§0 above) with two small fixes still open: add the
   `CauseOfLoss = "Special"` gate to `LOIFactor` (row 87) and `DeductibleFactor` (row 90), same shape
   as the fix already applied to `TheftExclusionFactor` (row 83).
2. **Contents is now fully live and wired end-to-end** (§0.5, §0.6, §5) — BGI, BGII, Broad, and Special
   all have real formulas in every row, not just placeholders. Live audit (§0.6) found four issues;
   three are resolved (BGII deductible limit, Special territory multiplier, BGI ProtClassFactor's YARD/
   1751/1752 exclusions). **One open item, backlogged:**
   - Special Contents `CAUSE OF LOSS ADJUSTMENT` (`Contents Rating Worksheet!C79`) is missing the
     Valuable Papers zero-out gate (`0.0 if CovType="Valuable Papers..." else Rate ×
     TheftExclusionFactor` — live formula skips the gate entirely). Edge case, only wrong if a Valuable
     Papers Contents item is ever rated under Special.
3. Builders Risk and blanket branches remain out of scope for both `LOIFactor` and `DeductibleFactor`
   (Building and Contents alike) until the underlying `Location Inputs` fields (reporting-form limit,
   blanket total) exist.
4. Legal Liability premium branches (both coverages, both forms) remain unbuilt — remember the
   raw-rate-vs-COLAdj divergence flagged in §6 when this gets picked up.
5. Next is your call — the Valuable Papers backlog item above, Legal Liability/blanket branches across
   all four forms, Special Class, Business Income, a specific endorsement family, or a different
   coverage/LOB entirely. Nothing gets built until you say go.
