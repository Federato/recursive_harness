# Group 1 closed: W-16, W-20, W-21, and the payload's sprinkler records

**2026-09-23.** `CFRater1.02.xlsb`. Script: `scripts/cf/124_w16_bi_fixes.py --fix W16 | W20 | W21`
(runs through `120_w11_fixes.main`: Excel-closed guard, 1.01 refused, gates, save, reopen-verify).
Backups: `Backups/CFRater1.02_pre-W16_*`, `_pre-W20_*`, `_pre-W21_*`. **Every fix verified against live ISO**
with `119_payload_three_way.py --without-cyber FL`, on every state ISO rates.

**Premiums: 7525 / 8596 / 2914 / 1506 / 429 / 20970 → 7540 / 8604 / 2935 / 1506 / 431 / 21016.**

## Result

| | before | after |
|---|---|---|
| AK, all 9 lines | 5 match, 4 off (-9, -1, -1, -1) | **9 / 9 match ISO** |
| CA, all 9 lines | 7 match, 2 off (+1, -1) | **9 / 9 match ISO** |
| FL, Cyber off on both sides | 8 of 15 match | **15 / 15 match ISO** |
| FL, rater's Cyber on | 0-1.6% below ISO | still ~0.8% below: only the Cyber factor ISO's FL filing can't apply |

The FL "Cyber off on both sides" check switches `IN - Policy` F3 / F4 to "No" in a read-only, never-saved
Excel session and compares against ISO's FL answers (scratch script, not committed).

---

## In plain English

Four separate small things, each confirmed by ISO moving onto (or away from) the rater's number:

1. **Business Income borrowed the Building's Cyber factor** (W-16). ISO gives Business Income its own, and
   because the rater has no Cyber Business Income limit, it's always the "full limit" row: 1.0 on Group I / II /
   Broad, 0.997 on Special. The rater used the Building's 0.997 / 0.996.
2. **Rounding order** (W-16, W-20, W-21). ISO rounds at more steps than the rater did: the BI Group I rate at
   three steps, the Legal Liability rate before the limit, and the premium after *each* Cyber factor. Every $1
   difference on the Group II lines was this last one (AK Building BGII: 100 → 99.5 → 100 → 100 vs the rater's
   100 × 0.992 = 99).
3. **Payload, not rater: the sprinkler-leakage exclusion on Contents and BI.** The rater applies the building's
   exclusion to Contents and BI. ISO needs its own record on BI, and on Contents it reads the *occupancy's*
   sprinkler system, which the payload never sent. The payload now reproduces the rater's assumption (S-4).

## What changed

| Fix | Rater change | ISO rule |
|---|---|---|
| **W-16** | BI row 10 = `ROUND(ROUND((ROUND(base×LCM,3)+substd+vacant)×terr×PC,3)×adj,3)`. BI rows 24 / 74 and SC BI rows 104 / 125 / 139 / 156 = Business Income's own Cyber exceptions factor (1; Special 0.997/0.998). SC BI premium rounds the base before Cyber | `SetBasicGroupIRate`, `SetCyberIncidentExclusionCOLExcptnsFactorBusnIncome*ToUse`, `SetCyberTypeOfLimitBusinessIncome` |
| **W-20** | Building 32 / 62 / 86 / 112 and Contents 30 / 58 / 81 / 109: rate × LL × AII → `ROUND(ROUND(rate×LL,3)×AII,3)`. No effect off Legal Liability (both factors 1) | Structure and PersonalProperty `SetPremium`, Legal Liability branch |
| **W-21** | All 16 Building / Contents / BI / SC BI premium rows: `ROUND(ROUND(ROUND(base,0)×Cyber,0)×COLExcptns,0)`. SC 22 / 46 / 65 / 86 likewise (they rounded once across everything) | every coverage's `SetPremium`: nested `Product DecimalPlaces="0"` |
| payload | `119`: Occupancy `SprinklerSystem` = the building's; `CommercialPropertySprinklerLeakageExclusionBusnIncome` sent when the building's exclusion is elected | PersonalProperty reads `../../SprinklerSystem` (the Occupancy, past the Table wrapper); BI gates on its own record |

## Verification steps (FL item 1)

| Line | Excel (Cyber off) before | after | ISO |
|---|---|---|---|
| Building BGI / BGII / Special | 525 / 991 / 63 | **527 / 999 / 68** | 527 / 999 / 68 |
| Contents BGI / BGII / Special | 560 / 1078 / 338 | **561 / 1082 / 340** | 561 / 1082 / 340 (BGI was 567 until ISO got the sprinkler record) |
| BI BGI | 490 | **490** | 490 (was 493 until ISO got the BI sprinkler record) |

## Framework fixes (`120_w11_fixes.py`)

- `wb.Save()` raised "'bool' object is not callable" after late-bound COM had **already saved** (it ran the method
  when the attribute was read). The reopen check was skipped. W-20 was re-verified by hand (formulas in every
  column, premiums, no `#REF` names). The call now runs only if it's still callable, and the reopen check is the proof.
- `active_cols` now retries "call rejected by callee" on its sheet lookup. The first W-21 attempt stopped there
  before saving; the file was confirmed byte-identical to its backup.

## Not changed, logged instead

- **S-4 / S-5** (backlog): no occupancy sprinkler input; no per-group sprinkler-leakage inputs; no Cyber
  Business Income / Extra Expense limit inputs.
- **W-22** (backlog): the order ISO rounds IRPM, package mod and multi-premium in differs by coverage, and
  BI / Legal Liability leave multi-premium out entirely. All three are 1.0 on every test risk, so ISO can't
  confirm any change. Left as it is.

**Process check that was missing:** the rater's premium rows had never been diffed against ISO's `SetPremium`
rounding structure. Each coverage's premium formula should be checked once against its `Product DecimalPlaces`
nesting rather than inferred from matching totals. Matching totals hid three rounding differences at $0-$1.

---

## Follow-on: Cyber dropped where ISO files none (user decision, 2026-09-23)

`124_w16_bi_fixes.py --fix CY`. Backup `Backups/CFRater1.02_pre-CY_*`. New **`TBL - Cyber`**: ISO's two Cyber tables,
per state from each state's latest package (352 / 1,408 rows, 44 states). **No rows for FL or NY**: both file the
tables header-only in every package. All 1,600 Cyber factor cells (Building, Contents, BI, Special Class, SC BI ×
4 forms × 2 factors) now look up their own state and group, and a state with no row gets 1. This also fixed Special
Class reading Building 1's Cyber cells (`'CALC - Bldg Rating'!$C$30`) regardless of its own state.

The payload drops the Cyber records automatically for any state with no rows (it reads `TBL - Cyber`), so
**`--without-cyber FL` is no longer needed**.

**Premiums 21016 → 21083** (7561 / 8627 / 2943 / 1519 / 433); only FL and NY moved (gate). **Verified: FL 15 / 15
match ISO with the rater's Cyber on; AK 9 / 9, CA 9 / 9 unchanged: 33 / 33 comparable lines match.**
NY: ISO still refuses (symbol table), which is the engine decision, next.

---

## Follow-on: D-1a, Alaska district from the ISO rating area (user decision, 2026-09-23)

`124_w16_bi_fixes.py --fix AK`. Backup `Backups/CFRater1.02_pre-AK_*`. **No premium moved (gate: must not move).**

- **New Schedule inputs** on the location block: **O `AKRatingArea`** (dropdown: the 10 ISO areas + Not Applicable)
  and **P `AKEastOf141st`** (Yes / No / Not Applicable; ISO's `BasicGroupIDistrictTerritory`, "East of the 141st
  meridian of West longitude", asked for Remainder of State only).
- **New `TBL - AKRatingArea`** (11 rows): area + east-of-141st → ISO code (`RatingTerrGroupICodeAK`) → District
  (`DomainDistrictAlaska`), from the edition the rater rates AK on (`TBL - Editions`: CF AK 20260601 V01;
  identical in 20261101 V02).
- **Column H (District)** for AK now comes from O / P, not the ZIP. The ZIP lookup (`TBL - BGI Territories` K:M) is
  retired for AK and its data left in place, unused. A blank area gives "Select" → $0 and **Diagnostics trap 7
  BLOCKs**; it never guesses.
- **Test location** (Haines 99827, southeast Alaska, east of the meridian): entered as Remainder of State + Yes =
  District I, the same district the ZIP gave. That mapping is my reading of ISO's area names (Haines is none of the
  nine named areas), so confirm it if you know otherwise.
- **Payload** sends O / P as ISO's `City` / `BasicGroupIDistrictTerritory`, and aborts on a blank area.
- Diagnostics D-1 text and the AK edition note (`TBL - Editions` F) are updated.

**Verified against live ISO, both districts:** today's risk (District I) 704 / 611 / 541 = ISO; the same risk as
Greater Anchorage Area (District II, code 030) 843 / 730 / 645 = ISO (the rater's figures from a never-saved
what-if). What-if also confirmed Greater Juneau / Gateway → District I and Remainder of State + No → District II.

Framework: the post-save `wb.Close` hit "call rejected by callee" after the save had gone through, so the reopen
check was run by hand (premiums 21083 unchanged, no `#REF` names, inputs / dropdowns / trap present). It is now
wrapped in `com_retry`.

---

## Follow-on: New York rates after all (D-1b, W-23; user decision, 2026-09-23)

**The NY "refusal" was our payload, not ISO's filing.** NY's state-only `SetCompletedBldrsRiskBaseRate` runs a
Builders Risk lookup unless `CompletedBasicGroupIISymbol` is exactly "Not Applicable". The payload never sent it,
so ISO looked up a Group II rate with a blank symbol and failed (RequestId c0c3ec79…). NY's domain
(`BasicGroupIISymbolNYCompleted`) allows only "Not Applicable" for any symbol but U. The payload now sends it.
The planned "engine refuses NY" was dropped: the engine already matched ISO 9 / 9. The earlier claim that NY files
its construction-symbol table empty was wrong; it was carried from notes without checking ISO's error text.

**Then two rater gaps, both on NY Group I** (`124_w16_bi_fixes.py --fix NY`, backup `Backups/CFRater1.02_pre-NY_*`):

| # | ISO | Rater before | Fix |
|---|---|---|---|
| D-1b | Territory code from (City, County) → (Remainder of State, County); **Bronx 030, Kings 240, New York 310, Queens 410, Richmond 430 → `BasicGroupIRateNYC`**, else `BasicGroupIRate` | No County; NYC from the Group I territory dropdown | New Schedule **Q `County`** (NY's 62 counties, ISO `DomainCountyState`) + `TBL - NYCounty`; H derives NY's district from it; CoreScratchpad 22 reads H; payload sends `County`; Diagnostics trap 8 BLOCKs a blank county |
| W-23 | NY `SetProtectionClassFactor` (Structure; PersonalProperty reads the Structure's territory): **1.0 in the five NYC territories** | PC 0.92 applied in NYC | Bldg Rating 8 = 1 when NY and NYC (Contents / BI borrow row 8) |

Gate note: the TOTAL rows sum every record into column C (FL's column), so a NY-only fix "moved" FL's column. The
gate now skips TOTAL rows; premium totals are still gated separately. Earlier fixes allowed column C and never hit it.

**Premiums 21083 → 21160** (Bldg 7592, Contents 8654, BI 2962): NY Group I 437 → 468, 360 → 387, 224 → 243.
**Verified: 42 / 42 record-forms match Excel = ISO = engine; total 21160 on all three sides.**

---

## RC-1 (hardening), 2026-09-23

`124_w16_bi_fixes.py --fix W24 | CYNY | DV | Z`, each backed up (`Backups/CFRater1.02_pre-<fix>_*`), gated and
reopen-verified. **Final: 42 / 42 Excel = ISO = engine, total 21171; strict column audit clean.**

| Item | What was found | Fix | Premium |
|---|---|---|---|
| **W-24** (was W-7) | New standing check `136_column_consistency_audit.py` (R1C1 compare, per-record Schedule stepping, reader scan). A **clone test** (records 1-4 copied into slots 11-14, never saved) priced Contents Group I, Contents Special and BI Special at **$0** for records 11-40: R-8 widened the sheets to 40 records but 7 live CoreScratchpad rows (140, 173, 180, 181, 208, 210, 211) stayed C..L. W-7's own rows (7, 126) and 9 others are **dead** (no formula reads them); 57 / 216 were already empty | 7 rows filled to AP with column C's formula; Special Class 32 / 50 `'IN - Policy'!C3` made absolute. Clone test now identical for slots 11-14 | none (only empty slots changed) |
| **CY-NY** | NY overrides the Cyber rules: exclusion 1.0, exceptions **1.005** from its own table. CY had given NY no Cyber | NY rows in `TBL - Cyber`; payload now sends NY's Cyber records; ISO agrees | NY +11 (21160 → 21171) |
| **Dropdowns** | 4 Schedule columns had dropdowns only on records 1-4 (Location G / I / J, Building I); **FL had no Group II territory list at all** (45 / 46) | Dropdowns copied down all 40 rows; `FL_bgiiterr` built from ISO's DomainBasicGroupIIRatingTerrFL (6 values = the rate-table keys) | none |
| **Z-2 / Z-3** | ISO's filed zero factors had no visible check | Diagnostics trap 9 (SC BI vandalism factor 0 → BLOCK), trap 10 (educational BI → WARN); both proved by what-if | none |
| ISO write-up | FL only (NY rates Cyber by its own rules) | `ISO_Filing_Gap_FL_Cyber.md`, ready to send | — |
| Stale docs | 23 reference docs used retired sheet names | Dated notice on each; payload generator RESUME brought current | — |

Framework: `wb.Close` also resolves as a property under late binding (like `Save`); both now handled. `Validation.Add`
evaluates the list source on the active cell and refuses an error, so dropdowns are copied with PasteSpecial instead.

---

## RC-4 (prove what's built): "more states", 2026-09-23 (in progress)

**Tools.** `scripts/cf/137_scenario_three_way.py` (what-if runner: rater opened read-only, edits in memory,
119's own payload / ISO / engine comparison; `--none` reproduces 42 / 42 exactly). `138_make_state_scenarios.py`
moves the four risk shapes to 42 new states, 4 per batch, with inputs from the rater's own lists.
`139_state_field_sweep.py` lists fields states add that the payload never sends (358; a map, not defects).
`140_state_run_summary.py` sorts mismatches by who disagrees (all were RATER; **the engine agreed with ISO
everywhere ISO answered**).

**First run: 24 of 42 new states clean, 4 refused, 14 with rater gaps.** Fixed, each gated (no move on today's
4 risks, which stay 42 / 42 at 21171) and verified by scenario re-runs:

| Fix | What | States |
|---|---|---|
| SCDED | Special Class Group I deductible table had no state column; now the per-state table the Building uses | AL CT IA KY MI NC NJ UT WV (-20) |
| payload | Deductibles-by-location record carries Deductible, WindstormOrHailDeductible and TheftDeductible (ISO gives each credit its own field) | SC Group II / Special |
| payload | Arizona Private Fire Department Credit sent as 1.0 (omitted = 0 = $0 Group I) | AZ (+1170) |
| SCSPB | Special Class Special base rates rebuilt from the package **in force** on the effective date (10 were from future-dated packages, e.g. CF AL 20270301) | AK AL CA CT MD NC ND NJ NM NV |
| W-25 | BI Group II rounds per ISO (BCEG before adjustment, 4 rounds); Building Group II rounds after every factor; roof ACV and cosmetic factors split (Paragraph B alone no longer discounts Group I) | MN NE RI VA WV; AL CT MI UT |
| SCFIN | Special Class final rates round after the per-location credit | 9 credit states |
| W-26 | Single-row roof tables (CT / IN / NH "ACV", MA / WY "Y") | CT |
| SCTHEFT | Special Class Special theft factor was hard-coded 0.88; 30 states file 0.91 / 0.94 | CT (-31) + 29 |

**Verified after all fixes (full re-run 2026-09-24, batches 01-11 + standard):** 44 states run, **40 match
Excel = ISO = engine on every line**; 0 mismatched lines (`CF_RC4_State_Results.csv` is header-only). CO / IN / OK
(wind hazard county) and SC (EQ territory) are ISO refusals, already moved to RC-3; Excel = engine there.
Standard run still 42 / 42 at 21171 (`results/cf-payload/20260924-084136`).

**Refusals = missing inputs (RC-3):** CO, IN, OK need a county-driven `GeographicWindHazardLevelTerritory`; SC
needs an earthquake territory (`BCEGEQFactor`). **Edition finding:** tables must be built from the package in
force on the effective date, not the newest on disk (13 states have future-dated packages); today's own tables
were checked and match.
