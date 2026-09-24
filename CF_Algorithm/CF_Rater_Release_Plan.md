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

## RC-2 · Separate choices per coverage (medium; moves premium only when elections differ)

What it buys: Building, Contents and BI can each carry their own exclusions and settings, as ISO files them.
One pattern throughout: **one input drives several coverage groups**.

| Item | What |
|---|---|
| W-4 | BI follows the **Building's** wind/hail exclusion, not its own (R-8 test: 2699 → 1890 when only the building excludes) |
| W-5 | Contents Group II coinsurance reads the **Building's** factor |
| W-3 | Contents Group II deductible-by-location credit gates on the **Building's** wind/hail election |
| R-5 remainder (S-1..S-3) | 6 consumers still read the master exclusion input via shared CoreScratchpad helpers (Building / Contents / BI) |
| S-4 | One sprinkler system and one sprinkler-leakage exclusion for all groups; ISO reads the occupancy's own sprinkler system and a record per group |
| Sweep | Grep every `Exist AtInputDataDef=` gate for other one-input-many-records pairs before calling the set complete |

Needs: a test risk whose elections **differ** between coverages. Today's four all agree, so nothing here is
visible in the 42 / 42.

## RC-3 · Inputs the rater doesn't have (medium; new Schedule / Policy fields, payload follows)

What it buys: submissions that carry these facts get rated on them instead of an assumption.

| Item | What |
|---|---|
| D-2 | **Full insurable value** (building, special class). The rater assumes value = limit |
| S-5 | **Cyber Business Income / Extra Expense sublimits**. BI is hard-wired to "Full Limit" |
| D-1c | **NY territory factor** from City + County (ISO's code), not the Group I dropdown |
| WH-CO / EQT-SC / AZ-PFD | **CO / IN / OK wind hazard county; SC earthquake territory; AZ fire-department credit** (ISO refuses or zeroes without them) |
| FL-BGII | **FL county input**, so the Group II territory dropdown narrows by county as ISO's does |
| Linked Special Class | Special Class "included in building" / linked item: never populated, untested |

## RC-4 · Prove what's built: IN PROGRESS (2026-09-23)

"More states" done once: 42 new states run against live ISO; 8 rater fixes and 2 payload fixes (see record).
**Full re-run 2026-09-24: 40 of 40 rated states match on every line** (0 mismatches); standard run 42 / 42 at 21171.
Refusals (CO / IN / OK wind hazard county, SC EQ territory) moved to RC-3 as missing inputs.

Still open in RC-4: W-22 (IRPM ≠ 1), Specific / Tentative rating, CA District II, Special Class in NYC,
Contents theft deductible, NH cosmetic roof factor, and the edition audit of older TBL sheets (ED-ALL).

## RC-5 · Not built (large; each is its own project)

| Item | What |
|---|---|
| Blanket rating | Every blanket branch is inert line-wide |
| Earthquake | Untraced on both the rater and the harness side |
| Edition transitions | One ERC edition per state, resolved outside the workbook; FL's filing is 21 months old (R-6) |
| ED-FL | Live ISO runs CF FL 20241201 **V02**; only V01 is on disk |

---

**Suggested order:** RC-1 (short, protects what's proven) → RC-4's "more states" run (cheap, and it may
reorder everything else) → RC-2 → RC-3 → RC-5 as separate projects.
