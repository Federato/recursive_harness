# R-1 implemented — every input named

**2026-09-22.** First of the eight streamlining changes. Applied to a **copy**;
`CFRater1.01.xlsb` was never opened for writing and is byte-identical to before.

| | |
|---|---|
| Source | `CFRater1.01.xlsb` — 5,387,411 bytes, unchanged, last written 2026-09-16 |
| Target | **`CFRater1.02.xlsb`** — 5,436,472 bytes, written 2026-09-22 |
| Names added | **133**, 0 failed, 0 replaced |
| Verification | 133 of 133 resolve to the correct cell, checked two independent ways |

---

## What was added

| Prefix | Count | Points at | Shape |
|---|---|---|---|
| `IN_Pol_*` | 19 | `Policy Inputs` | single cell |
| `IN_Loc_*` | 71 | `Location Inputs` | **row range `$C:$L`** — all 10 item columns |
| `IN_SC_*` | 37 | `Special Class Inputs` | **row range `$C:$E`** — all 3 item columns |
| `OUT_Prem_*` | 6 | `Policy Inputs!I3:I9` | single cell — the premium summary |

**Item tabs got a name per input _row_, not per cell**, because every formula that
reads them is an `INDEX(range, 1, ordinal)`. Naming the row is what makes that
formula survive a row moving — which is the entire point of R-1.

```
Before   =INDEX('Location Inputs'!$C$26:$L$26, 1, $A20)
After    =INDEX(IN_Loc_BuildingClassCode,      1, $A20)

Before   ='Policy Inputs'!C3
After    =IN_Pol_PolicyType
```

---

## Verification, and why it was done this way

Counting names proves nothing — **a name that exists but points somewhere wrong is
worse than no name**, because it looks correct in every formula that uses it. So
`88_r1_verify_names.py` reads each value *through the name* via COM, and separately
reads the raw cell the plan claimed via `pyxlsb`, then compares. Two independent
paths to the same number, 133 times.

Result: **133 match, 0 mismatched, 0 unresolvable.**

---

## Findings

- **The workbook already had 170 defined names** before this ran — Excel-generated
  ones (print areas, table ranges) plus whatever accumulated during the build. Total
  is now 303. Nothing was overwritten (0 replaced), but that pre-existing set has
  never been audited and is worth a look; a stale name pointing at a moved range is
  exactly the failure R-1 exists to prevent.
- **Four derived names needed hand-overriding** because the mechanical rule produced
  something unreadable: `IN_Loc_BCEGBCEG` → `IN_Loc_BCEG`,
  `IN_Loc_DistrictAlaskaCaliforniaNewYork` → `IN_Loc_District`, and the two bare
  `Description` rows → `IN_Loc_ConstrDesc` / `IN_Loc_AddlInsurableIntDesc`.
- **Nothing but names changed.** No cell value, formula, sheet, or format was
  touched. The +49 KB is the name table.

---

## The COM protocol that worked — reusable

Two attempts stranded a headless Excel process before this landed. What the working
version does, and why each rule is there:

1. **Refuse to run if any Excel process is alive.** A prior session lost unsaved work
   by driving an instance the user had open.
2. **Refuse to write to `CFRater1.01.xlsb` by name.** The live rater is never a target.
3. **`DispatchEx`, never `Dispatch`.** `Dispatch` *attaches* to a running instance;
   `DispatchEx` always creates a fresh one. That single distinction is the difference
   between safe and destructive.
4. **Set `Application.Calculation = xlCalculationManual` _after_ opening**, never
   before — Excel raises *"Unable to set the Calculation property"* when no workbook
   exists. Without it, 133 `Names.Add` calls each trigger a recalc of a 5.4 MB formula
   tree, which is what timed out the first two attempts.
5. **Quit in a `finally` block**, and afterwards **check for and reap orphans** —
   `app.Quit()` does not always end the process while Python holds references. Match
   orphans on an empty `MainWindowTitle` and kill by **PID**, never
   `Stop-Process -Name EXCEL`.

Diagnosing an orphan safely: a headless COM instance has **no `MainWindowTitle`** and
**is not in the Running Object Table** (`GetObject` fails with *"Operation
unavailable"*). A user's real Excel with a workbook open has both. That pair of checks
tells you whether a process is yours to kill without ever touching it.

---

## Scripts

| | |
|---|---|
| `scripts/cf/86_r1_generate_names.py` | derives the plan from the Step 1 inventory → `CF_R1_Name_Plan.csv`. Writes to no workbook |
| `scripts/cf/87_r1_apply_names.py` | applies the plan to the copy |
| `scripts/cf/88_r1_verify_names.py` | read-only two-path verification |

The plan is a reviewable CSV precisely so the naming could be checked before anything
was written — and four bad names were caught that way.

---

## What this unblocks

- **Every future doc stops rotting.** The "re-read the workbook before trusting any
  cell reference" caveat that opens every handoff in this project can go.
- **The `Payload Export` sheet gets simpler** — its formulas become
  `=INDEX(IN_Loc_ClassCode, 1, $A20)` instead of a positional range.
- **R-3, R-4, R-6 all get cheaper**, since each needs to reference inputs.

## Next

Nothing else has been changed. The remaining seven suggestions are still proposals in
`CF_Rater_Streamline_Wireframes.html`. **R-4 (policy-level factor block, ~1 hr)** is
the cheapest real fix left; **R-3 (guard + provenance columns)** has the highest payoff.

**Settled 2026-09-22, by the user:** *"1.02 is essentially a prototype, never touch
1.01."* `CFRater1.02.xlsb` is the prototype and is where R-2 onwards get built.
`CFRater1.01.xlsb` is **frozen permanently** — no reads, no writes, and **no
fold-back plan**. Every write script must keep refusing it by filename, as
`87_r1_apply_names.py` does: a guard in code, not a rule held in attention.
