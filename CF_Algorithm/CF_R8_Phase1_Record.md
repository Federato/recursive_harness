# R-8 Phase 1 — `IN - Schedule` built, wired to nothing

**2026-09-22.** `CFRater1.02.xlsb`. `CFRater1.01.xlsb` never opened.

| | |
|---|---|
| New sheet | **`IN - Schedule`**, position 4 |
| Blocks | **7**, in ISO's hierarchy |
| Capacity | 40 records per block; first 10 mirrored from the old model |
| Premiums | **unchanged** — 7183 / 8022 / 2699 / 1434 / 406 / **19744** |

---

## What it holds

| Block | Cols | Rows | Active now |
|---|---|---|---|
| LOCATION | 14 | 5–44 | **4** — FL, NY, AK, CA |
| BUILDING | 34 | 48–87 | **4** |
| OCCUPANCY CLASS | 9 | 91–130 | **4** |
| CONTENTS | 11 | 134–173 | **4** |
| BUSINESS INCOME | 16 | 177–216 | **4** |
| SPECIAL CLASS | 23 | 220–259 | **1** — Artificial Turf |
| SC BUSINESS INCOME | 15 | 263–302 | **1** |

The hierarchy resolves: building `2 - 1` parents to location `2`, occupancy
`2 - 1 - 1` to building `2 - 1`, contents `2 - 1 - 1 - 1` to that occupancy.

**Populated by formula, not by value.** Every cell reads its counterpart on
`IN - Location` / `IN - Special Class`, so both models describe the same policy and
stay in lockstep during migration. A typed copy could drift, and then Phase 2's
"premium unchanged" gate would be measuring nothing.

**Nothing reads this sheet.** No calc sheet is repointed. The gate is that premiums
cannot have moved — verified anyway, because "that should be impossible" is how
several of this week's bugs got in.

---

## A caught defect: ID type mismatch

`LOCATION.ID` was emitted as a literal — the **text** `"1"` — while
`BUILDING.ParentLoc` read the Location# cell and resolved to the **number** `1.0`.

**A `SUMIFS` across a text/number pair matches nothing and returns zero, not an
error.** Phase 2's per-building `TOTAL LIMIT` roll-up is exactly that join, so this
would have produced a silently wrong deductible band — the precise failure R-8 exists
to remove.

Fixed by having `LOCATION.ID` read the same cell `ParentLoc` reads, so both sides are
the same type by construction rather than by coincidence.

---

## The bigger find — 133 defined names were broken, and my R-2 check missed it

Phase 1 failed on its first run: `OUT_Prem_Building` would not resolve. Auditing
found **133 names still pointing at `'Policy Inputs'`, `'Location Inputs'` and
`'Special Class Inputs'`** — the pre-R-2 sheet names. Every name R-1 created.

**R-2's verification said this had not happened.** It compared the set of
unresolvable names before and after the rename and found no growth. That check
passed, and it was wrong.

**Why it was wrong:** it ran *in the same session as the rename*. Excel kept
resolving the names from in-memory sheet identity while persisting the stale
sheet-name string. The names worked for the rest of that session — and for the
R-3, R-6, R-7 and R-5 sessions after it, which is why the premiums those runs
reported were correct. The breakage only surfaced on a later open.

**The lesson, stated for reuse: a verification that runs before a save / close /
reopen cycle is testing the in-memory state, not the artefact.** For anything that
changes structure rather than values — renames, defined names, sheet adds and
deletes — the check has to reopen the file.

`scripts/cf/104_fix_stale_names_after_rename.py` repairs all 133 and then does
exactly that: saves, closes, reopens, and only then audits. Result: **301
resolvable, 0 stale**, premiums intact through the names.

*Worth noting what saved this:* Phase 1 read the premiums through the names as its
first act. Had it read them by cell address, the names would have stayed broken and
surfaced later, further from their cause.

---

## Next — Phase 2

Three jobs, all the same underlying work (re-keying machinery away from
"one column = one fused item"):

1. Migrate `CALC - Contents Rating` to the new blocks; widen to one column per
   contents record; rebuild `TOTAL LIMIT` as a per-building `SUMIFS`.
2. Trace and split the five `CoreScratchpad` exclusion helpers — the agreed
   rehearsal for the harder re-key, and it closes R-5.
3. Resolve `CALC - Special Class` row 26 against ISO's filed rules.

**Gate: Contents premium still 8,022.**

---

## Scripts

| | |
|---|---|
| `scripts/cf/103_r8_phase1_schedule.py` | builds the sheet; idempotent (deletes and rebuilds) |
| `scripts/cf/104_fix_stale_names_after_rename.py` | the name repair, with reopen-based verification |
