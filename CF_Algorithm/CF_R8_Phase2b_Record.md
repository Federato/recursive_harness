# R-8 Phase 2b-ii: Contents migrated to one column per contents record

**2026-09-22.** `CFRater1.02.xlsb`. `CFRater1.01.xlsb` was never opened.
Backup taken first: `Backups/CFRater1.02_pre-R8-2b-ii_20260922-1329.xlsb`.

| | |
|---|---|
| Script | `scripts/cf/109_r8_phase2b_repoint_contents.py` (translator: `r8_contents_translate.py`) |
| Gate 1 | **passed**, and re-verified after save, close and reopen |
| Premiums | **unchanged**: 7183 / 8022 / 2699 / 1434 / 406 / **19744** |
| Gate 2 | **run 2026-09-22 against live ISO**: fails as built (LOI keyed per record); passes to the dollar with two in-memory fixes (see below) |

---

## In plain English

Before this change, a Contents column meant "item k". That was the location, the
building, the occupancy and a single contents record all fused together. Now a
Contents column means **one contents record**. Each record looks up its occupancy,
then its building, and reads building-level facts through that building: protection
class, territory, construction and deductible. Two contents records on the same
building therefore share one deductible band. That band now comes from the
building's limit **plus every contents record under it**, which was the point of R-8.

## What changed

| # | Change | Why |
|---|---|---|
| 1 | R-3 **Source/Check columns moved M:N → AQ:AR** (moved with Cut); the `OUT - Diagnostics` B6/C6 COUNTIFs were repointed by hand | They sat inside the M..AP record range, which the handoff missed. Whole-column references do not follow a partial-column cut |
| 2 | `IN - Schedule` CONTENTS **col L = ParentBldg**, resolved through the occupancy | The join key for the TOTAL LIMIT roll-up |
| 3 | Contents **rows 113-116**: ContentsID, Active, OccIdx, ParentCol | Per-record keys. Both indexes fall back to 1, never 0, because `INDEX(row,1,0)` would spill |
| 4 | Contents **rows 119-168**: per-record copies of **50 CoreScratchpad rows** (col A names the source row) | Those rows read contents- or occupancy-level inputs (limit, coinsurance, contents group, occupancy category, coverage form), so a building-keyed copy would give a second record the first record's values |
| 5 | Contents **rows 1-110 rewritten for C..AP** from the column-C template; premium rows gated on Active | |
| 6 | **CoreScratchpad row 138 TOTAL LIMIT** = building limit + `SUMIFS` over active contents records of that building + C215 | The R-8 formula. Downstream deductible rows (41, 87, 139-142) stay building-level |
| 7 | **CoreScratchpad rows 60/205 → Building election (row 96)**; the Contents copies read the Contents election (row 97) | **Closes R-5** |
| 8 | **`CALC - BI Rating` row 74** now reads `Bldg Rating` row 111 directly, not Contents row 108 | BI read Contents column by column, which stops being valid once Contents columns are records. Same value |

## What was verified

- **Unchanged:** all six premiums (read through the `OUT_Prem_*` names). All 1,100
  Contents values in C1:L110 were compared cell by cell. TOTAL LIMIT and every
  `Bldg Rating` value are also unchanged.
- **Moving, on every active item** (C, D, E, F): adding +100k to the contents limit
  moved that record's premium each time (1632→1949, 776→920, 1170→1274, 4444→4489).
- **R-5 split is live in both directions:** the Contents wind/hail election moves only
  Contents (8022→6796), and the Building election moves Building (7183→6013) but not
  Contents.
- **After reopen:** premiums, AQ/AR headers, the Diagnostics repoint, ParentCol, and 0 `#REF` names.

## Found and deliberately NOT fixed (each would change a premium, so it's your call)

*Logged as backlog items **W-1 to W-6** in `Rater_Simplifications_Backlog.md`, in the order below.*

1. **Contents rows 76 and 104 (LegalLiabAddlInsurableIntFactor, Broad/Special)** test
   `IN - Location` rows 33 (OccupSeverity) and 61 (Construction Description) for
   "Legal Liability Coverage Form". The sibling rows 25/53 test row 10 (CovForm). On
   item C that means the Additional Insurable Interest factor never applies to Broad or
   Special. The migration preserves the current behaviour.
2. **Contents row 24 (LegalLiabFactor) was inconsistent across columns:** C read CovForm
   (row 10), D..L read Building CovType (row 8). Both give the same values on today's risk. All 40
   columns now use column C's CovForm test, which matches rows 52/75/103.
3. **Contents row 46 (BGII DeductibleByLocation) reads `Bldg Rating` row 49**, which
   gates on the *Building* wind/hail election (row 96). It is neutral while Per Location
   Deductible = No.
4. **Business Income follows the Building wind/hail election** (2699→1890 in the test).
   BI borrows the building's computed rate, so BI's own election (row 98) doesn't
   reach it. Before this change BI followed the policy-level election (row 75).
5. **Contents row 43 (BGII coinsurance) reads `Bldg Rating` row 46**, the building's
   coinsurance factor, not the contents one.
6. **Special contents deductible (CS rows 176-182)** bands on the record's own limit,
   not TOTAL LIMIT, unlike BGI/Broad. The migration keeps that behaviour per record.

## Limits of the new model (not defects, but real)

- Watchman / burglary alarm (rows 87/90) and Additional Insurable Interest (row 92)
  aren't in the Schedule CONTENTS block, so they are read from the parent building.
- Occupancy severity and contents group are derived by formula only for the 10
  mirrored occupancy rows. Records 11-40 need those fields typed in.
- A contents record can only parent to buildings 1-10, because CoreScratchpad is 10
  columns wide.
- R-3 Check formulas (now col AR) still cover C:L only.
- CoreScratchpad row 143 no longer has any readers.

## Gate 2: two contents records against ISO (2026-09-22)

`scripts/cf/110_r8_gate2_multi_record.py`. The workbook was opened read-only and
**nothing was saved**. The test risk is chunk 4's Oregon case (0951 Offices, Frame, PC 3,
Portland, Basic, 90%, 1,000 ded), loaded into item 5. The rater was compared with **live ISO
calls**, which matched the stored 2026-09-18 answers exactly.

**The prediction, written before the run:** ISO looks up all four PP LOI factors on
`OccupTotalLOIToUse`, the total PP limit under the occupancy. The build uses each record's own
limit, so the rater should fail with two records and pass with one.

| Case | Rater as built | Rater + LOI fix | + rounding fix | **ISO** |
|---|---|---|---|---|
| 1 record, 100k | 246 | 246 | **247** | **247** |
| 2 records: 100k | 246 (LOI 0.898) | 230 | **231** | **231** (LOI 0.842) |
| 2 records: 50k | 138 (LOI 1.000) | 115 | **116** | **116** (LOI 0.842) |

**Result: Gate 2 fails as built, for exactly the predicted reason. With two in-memory
changes it matches ISO to the dollar on every record.**

- The R-8 structure itself is **confirmed**. Record 2 joins its building (ParentCol 5), and
  TOTAL LIMIT rolls up to **250,000** (building 100k + contents 150k). That is the location total
  ISO keys the deductible band on, and both deductible factors match.
- **Fix A: LOI on the occupancy total.** The per-record copies of CoreScratchpad
  131-137, 144-154 and 156-166 should look up the LOI factor on
  `SUMIFS(Contents.Limit, Contents.ParentOcc = this record's occupancy, Active)`, not the
  record's own limit. With one record per occupancy (every risk the rater holds today) the two
  are identical, so **today's premiums don't move**.
- **Fix B: rounding order, a defect that was already in the rater and isn't R-8.** Contents row 17 is
  `ROUND(COL x Coins x LOI, 3)`. ISO rounds `COL x Coins` first and then applies LOI. This
  is why the one-record control was $1 low. **Fix B changes today's premiums**, because it
  applies to every BGI contents record.

### Harness lessons (the process gaps, not things to watch for by hand)

The first two Gate 2 runs failed because of the harness, not the rater. Writing through COM let
Excel coerce values: "0951" became 951, "1,000" became 1000 (deductible factor 0),
and the ParentOcc "5 - 1 - 1" was parsed as **a date**. The check that was missing: a
test harness that writes inputs should **read them back and compare types** before
calculating. The script now writes text as text. The rater's own input sheets are open to the
same coercion when someone types "5 - 1 - 1" into IN - Schedule by hand.

A second input-mapping gap: ISO takes `WindstormOrHailDeductible "1,000"` as a flat
deductible, but the rater treats any value other than "Not Applicable" as a *percentage*
deductible, so it returns a factor of 0. The equivalent rater input is "Not Applicable". The
payload generator needs to know this.

## Fixes A and B applied (2026-09-22, approved)

`scripts/cf/111_r8_fixA_fixB.py`. Backup: `Backups/CFRater1.02_pre-R8-fixAB_20260922-1346.xlsb`.

- **Fix A:** new key row **117 `OccTotalLOI`** = `SUMIFS` of active contents limits
  sharing this record's occupancy. 240 cells in the LOI-chain copies (6 per record) now
  read it. Premiums unchanged, as required.
- **Fix B:** row 17 for all 40 columns is now `ROUND(ROUND(COL x Coins,3) x LOI,3)`.
  **It moves none of today's four items** (556 / 357 / 611 / 3499), because none of them lands on a
  rounding boundary. The gate required that only BGI rows 17-31 could change and that no other
  coverage moved.
- **After reopen:** premiums 7183 / 8022 / 2699 / 1434 / 406 / 19744. Row 117 and the new row 17
  both persisted, and there are no `#REF` names.
- **Moving check (two-sided):** Gate 2 re-run on the *saved* workbook against **live ISO**,
  with no in-memory patches: **PASS, 247 / 231 / 116, exact.** Fix B is the $1 on the one-record
  case (246 → 247), so it is live, not inert.

**Not checked:** whether BGII (row 45), Broad (67) and Special (95) have the same
rounding-order gap. In the Oregon case BGII matched ISO either way. It needs a case that lands on
a boundary before anyone calls those rows correct.

## Next

Phase 4: Building, BI, Special Class and SC BI, one coverage per gate.
