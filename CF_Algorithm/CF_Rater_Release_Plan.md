# CF rater: open items grouped by release candidate

**2026-09-23.** Baseline `CFRater1.02.xlsb`: 21160, **42 / 42 lines match Excel = ISO = engine** (FL, NY, AK, CA).
Proposed grouping only, not a commitment. Every open item from `Rater_Simplifications_Backlog.md`,
`CF_Rater_RESUME.md`, the Diagnostics sheet (sections 2 and 4) and the payload records is placed exactly once.
Closed items (W-1, W-6, W-8..W-21, W-23, T-1, M-1, CY, D-1a, D-1b, W-9) are left out.

**Release rule for every RC:** the three-way run stays 42 / 42, every gate is premium-neutral except where a fix is
meant to move a line, and each move is confirmed by live ISO moving onto the rater's number.

---

## RC-1 · Hardening: ✅ DONE 2026-09-23

42 / 42 Excel = ISO = engine at **21171**; strict column audit clean. Details: `CF_W16_W20_W21_Record.md` (RC-1).
ISO write-up drafted (FL only), CY-NY fixed, W-7 closed as W-24 (records 11-40 no longer price $0), dropdowns on all
40 rows plus FL's missing list, Z-2 / Z-3 traps, 23 stale docs flagged. **Your action:** send `ISO_Filing_Gap_FL_Cyber.md`.

## RC-2 · Separate choices per coverage: ✅ DONE 2026-09-24

Each coverage now follows its own elections, and an excluded wind/hail follows the state's own family (TBL - WHExclMode).
Fixed: W-3, W-4, W-5, S-2, ED-WHX, final-rate rounding. Closed as already right: S-1, S-3. Moved to RC-3: S-4 (needs an
occupancy sprinkler input). 14 probes in `scenarios/rc2/`, all Excel = ISO; regression 40 / 40, standard 42 / 42 at 21171.
Details: `Rater_Simplifications_Backlog.md` (RC-2 probes).

## RC-3 · Inputs the rater didn't have: ✅ DONE 2026-09-24 (incl. FL-BGII dropdowns)

New inputs: wind hazard county (CO / IN / OK) and SC EQ territory (all states now rate, 0 refused), AZ fire department
credit, Cyber BI / EE sublimits, sprinkler facts per occupancy / group, linked Special Class. D-1c and D-2 closed with
no change (ISO already agrees / blanket-only). Regression: 44 / 44 states, standard 42 / 42 at 21171. Details:
`Rater_Simplifications_Backlog.md` (RC-3). FL-BGII done: county dropdown per state, FL Group II territory narrowed by county.

## RC-4 · Prove what's built: ✅ DONE 2026-09-24 (final regression: 40 / 40 rated states, 0 mismatches; standard 42 / 42 at 21171)

42-state run clean (40 / 40 rated states). Then every open item traced, fixed where needed and verified on live ISO with a
probe built so the competing readings disagree (`scenarios/rc4/`): **ED-CA-SC** (CA Special Class tables from a future
filing + two SC wiring bugs), **NH-COS** (reading confirmed; found **ROOFRND**, roof-factor rounding), **TH-DED** (theft
deductible built; payload CP 03 20), **W-22** (modifier order / rounding / MPD scope, 800 cells; payload sent PM / MPD at
the wrong level), **CA-D2** (verified), **SC-GI-ST** (NY / PR Special Class rates; NY option must be sent; FL stays CW
until V02). ED-ALL audited. Baseline 21171 unchanged throughout. Details: `Rater_Simplifications_Backlog.md`.
New, carried forward: ED-WHX (-> RC-2), ENG-FL-MOD and ED-FL (harness engine / FL V02).

## RC-5 · Not built (large; each is its own project)

| Item | What |
|---|---|
| Blanket rating | Every blanket branch is inert line-wide |
| Specific Group II | Specific / Tentative **Group I** is built (input rate; ISO rates Tentative = Specific, verified 2026-09-24). Missing: ISO's Specific **Group II** rate (`RatingTypeBasicGroupII` = Specific, `SpecificGroupIIRate`, wind-hazard eligibility); the rater always rates Group II by class |
| Earthquake | Untraced on both the rater and the harness side |
| Edition transitions | One ERC edition per state, resolved outside the workbook; FL's filing is 21 months old (R-6) |
| ED-FL | ✅ **DONE 2026-09-24**: FL V02 on disk (on CW 20230801 V04); FL Special Class rates, vacancy codes, substandard table (8 states), FL residential basis fixed; engine FL gap closed |

---

**Suggested order:** RC-1 (short, protects what's proven) → RC-4's "more states" run (cheap, and it may
reorder everything else) → RC-2 → RC-3 → RC-5 as separate projects.
