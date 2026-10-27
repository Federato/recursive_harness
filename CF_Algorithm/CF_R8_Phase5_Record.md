# R-8 Phase 5: the old input sheets are retired

**2026-09-22.** `CFRater1.02.xlsb`. `CFRater1.01.xlsb` was never opened.

| | |
|---|---|
| Script | `scripts/cf/116_r8_phase5_retire_inputs.py` (conversion rules: `r8_phase5_schedule.py`) |
| Backup | `Backups/CFRater1.02_pre-R8-P5_20260922-1428.xlsb` |
| Result | **`IN - Location` and `IN - Special Class` deleted.** `IN - Schedule` is the input sheet |
| Premiums | **unchanged**: 7183 / 8022 / 2699 / 1633 / 457 / **19994**, and after reopen |

---

## In plain English

Until now the Schedule was a mirror: its first 10 rows were formulas copying the two old
input sheets, so those sheets were still where a risk was really entered. **Now you enter the risk
on `IN - Schedule`.** One row is one record: location, building, occupancy, contents, BI,
Special Class, SC BI. Each block holds up to 40. The old sheets have been deleted.

## How each Schedule field was converted

| Kind | Examples | Now |
|---|---|---|
| Typed input | zip, class code, limits, construction type, sprinkler, sub-standard | typed value |
| Policy default | cause of loss, deductibles, valuation, coinsurance, exclusions, coverage types | a link to `IN - Policy`, as before. The three exclusion masters (old rows 75-77) had no Schedule home, so their links were inlined |
| Link to another input | BI specific rate = building's; tenant class = building class (items 2-10) | a link to that Schedule cell |
| Derived | city/state from zip; District; BGII territory; class description; construction symbol and description; occupancy severity; contents group; burglary range; SC territory and symbol; every Active flag | **Schedule-native formulas on all 40 rows**, reading only the Schedule and TBL sheets |
| Key | every ID and ParentID | value |

- **Typed overrides were kept:** location 4's District "District I" was typed over its formula and stays typed.
- **New CONTENTS columns M-P** (WatchmanService, BurglaryAlarmType, BurglaryRange,
  BurglaryFactor). These were the only priced inputs the Schedule didn't carry. Contents rows
  92/93 now read them.
- **Dropdowns:** 68 were carried across. The four dependent ones (BGI/BGII/Special territory by
  state, and construction type by construction code) resolve per row. Excel won't attach them to
  **blank** rows whose list doesn't exist yet (36-37 rows each). They need adding once a record is entered.

## What else changed

- **The last live CoreScratchpad rows** that still read `IN - Location` were moved to the
  Schedule with the 4a rule: **139, 141, 142** (the deductible band chain), **155** (Broad rate),
  **183** (Special territory), and **215** (Special Class limit included in a building). Phase 4a
  missed them because they sit outside Building's own chain; Contents reads them through ParentCol.
  **The decoupling proof caught this**: scrambling the old sheets moved Contents 8022 → 8007 on
  the first attempt.
- **135 dead CoreScratchpad rows retired** (formulas cleared, column A marked
  "retired R-8 P5"). These are rows that read the old sheets, or that fed only off such rows, and
  that nothing live reaches: the legacy Contents/BI/Special Class helpers, and the old derivation
  chains for District, BGII territory, severity and contents group.
- **R-3 checks (174)** now mask on each sheet's own Active key row across all 40 columns, not
  `IN_Loc_State` / `IN_SC_State`.
- **Diagnostics**: the traps (rows 13-16) and the edition table (rows 40-49) read the Schedule.
- **The 123 R-1 names** onto the old sheets were deleted.

## Gates

1. **Conversion:** premiums and every active-record calc value unchanged, and the Schedule unchanged on
   all 22 active records. 540 cosmetic changes on blank or inactive rows are listed in the log, for
   example "Construction Symbol" placeholders now filling blank building slots.
2. **Decoupling proof:** the old sheets' limits, class codes, construction codes, protection
   classes and zips were scrambled in memory. **No premium moved.**
3. **Retirement:** after the names and sheets were deleted, premiums and calc values were unchanged,
   Diagnostics traps and editions unchanged, and **no `#REF!` in any formula or name**.
4. **Moving:** a typed Schedule limit +100k moved Building 7183→7364. Zip 10001 re-derived the city
   Brooklyn→New York. Construction type "Frame" re-derived the symbol AB→B.
5. **Reopen:** premiums, sheets gone, no `#REF!`, new headers present.

## What the gates caught along the way

1. The first gate was too strict: it compared inactive Special Class slots whose intermediates
   now resolve their own (empty) location. The fix was to hold active records to "unchanged" and
   **print** every inactive difference. It was not to loosen the check silently.
2. The decoupling proof caught the six live rows above.
3. The retirement gate caught **dead rows left showing errors** because they fed off retired rows.
   The fix was to retire those transitively. The dependency scan also had to learn that CoreScratchpad
   refers to itself **with its own sheet name** (`'CALC - CoreScratchpad'!C172`).

## Now stale, not updated here

- `CF_Payload_Excel_Input_Inventory.*` and the payload generator's step docs describe inputs
  by `IN - Location` row. They now live on `IN - Schedule`. **Phase 6 (collapse Payload
  Export) is the natural place to rewrite them.**
- Backlog **W-9** (the dead SC BI limit row 42) no longer exists, because the sheet is gone.
