# R-5 implemented — one exclusion input per coverage group

**2026-09-22.** Applied to `CFRater1.02.xlsb`. `CFRater1.01.xlsb` never opened.

| | |
|---|---|
| New inputs | **15** — 9 on `IN - Location` (rows 96–104), 6 on `IN - Special Class` (rows 49–54) |
| Consumers rewired | **161 cells** across **17** rows |
| Left on the master, deliberately | **6** rows |
| Defaults | unchanged — 7183 / 8022 / 2699 / 1434 / 406 / **19744** |
| Split test | Theft-Building = No → Building **7183 → 7334**, everything else static |

---

## The backlog understated this by more than half

S-1/S-2/S-3 describe **two** records per exclusion — the item and its Business
Income group. Checking `CFCW20260601V01\Rules` directly, ISO files **five**:

```
CommercialPropertyVandalismExclusion                     Structure
CommercialPropertyVandalismExclusionPrsnlProp            Personal Property
CommercialPropertyVandalismExclusionBusnIncome           Business Income
CommercialPropertyVandalismExclusionSpecialClass         Special Class
CommercialPropertyVandalismExclusionSpclClassBusnIncome  SC Business Income
```

Identical five-way split for windstorm/hail and theft. **15 records, driven by 6
inputs.** The backlog rows are corrected.

---

## The design, per the instruction "default all coverages to yes if the record exists"

Each new per-group cell is a **formula pointing at its master** (`=C77`). So
electing an exclusion turns it on for every coverage group exactly as before, and a
single group is split off by typing `No` over one cell.

```
IN - Location
  75  Windstorm or Hail Exclusion:            Yes        <- master, unchanged
  ...
  95  Exclusions by Coverage
  96  Windstorm or Hail - Building:           =C75
  97  Windstorm or Hail - Contents:           =C75
  98  Windstorm or Hail - Business Income:    =C75
  99  Vandalism - Building:                   =C76
 ...
 102  Theft - Building:                       =C77
```

**Rows are appended, never inserted.** Inserting mid-sheet would shift every row
number recorded in this project's docs and wireframes. The new blocks sit below the
existing content, so nothing moves.

All 15 are named — `IN_Loc_TheftExcl_Bldg`, `IN_SC_VandalismExcl_SCBI`, and so on.

---

## Six consumers were NOT rewired, on purpose

Of the 23 formulas that read an exclusion input, 17 sit unambiguously on one
coverage's sheet and were repointed. The other six were left on the master and are
reported rather than assigned to a group on a guess:

| Where | Why it was left |
|---|---|
| `CALC - Special Class` row 26 | Reads **`'IN - Location'!C75`** — the *Location* wind/hail input — for the Special Class BGII base rate, while rows 27/29/31 in the same block read the *Special Class* input. **This looks like a defect**, but confirming it needs ISO's rules, and changing it is a behaviour change rather than a split |
| `CALC - CoreScratchpad` rows 26, 60, 175, 182, 205 | Shared helpers — a vandalism lookup key, a windstorm copy, a theft key, a deductible factor, a windstorm-exclusion key. Each may feed more than one coverage; splitting them needs a trace of who consumes each |

**Consequence, stated plainly:** the split is **fully live for Special Class and SC
Business Income**, and **partial for Building / Contents / Business Income** —
because some of their exclusion logic routes through those shared helpers. Electing
a split on the Location side will move the coverages wired in step 2 and leave the
helper-routed paths on the shared value.

---

## Two bugs found by the guard, neither saved

**`IN - Special Class` is wider than its header suggests.** Its item header shows
three slots (C:E), but the exclusion rows are populated to at least column H, and
`CALC - Special Class` reads C:L. Writing the new rows C:E left F:L pointing at empty
cells and took the Special Class premium to **`#VALUE!`**. Fixed by mirroring the
master across the full C:L width. *The lesson: a sheet's header is a claim about its
shape, not a measurement of it.*

**The split test picked the one item where the factor cannot matter.** Setting
Theft-Building to `No` on item 1 moved the factor 0.88 → 1.0 and the rate
0.026 → 0.029, but left the premium at 7183 — which reads exactly like an inert
split. **Item 1 is a Legal Liability risk**, and Legal Liability picks the rate up
three steps earlier in the chain, dropping the theft exclusion factor entirely
(harness chunk 8). The test now splits across every item; Building moves
**7183 → 7334**.

*That near-miss is worth keeping:* a verification that exercises one sample row can
report a working change as broken, or a broken one as working, depending on which row
it happens to pick.

---

## Verification

1. **Unchanged with everything defaulted** — proves the 161 rewired cells resolve to
   exactly what they replaced.
2. **Theft-Building = No moves Building to 7334** — proves the split is live.
3. **Contents, BI, Special Class and SCBI all static in that same run** — proves it is
   *isolated*, which is the whole point. A split that moved every coverage would be
   the bug it was meant to fix.
4. **Restored exactly** to baseline.

The script aborts without saving on any failure.

---

## Scripts

| | |
|---|---|
| `scripts/cf/101_r5_survey_exclusions.py` | read-only — finds all 23 consumers before anything is written |
| `scripts/cf/102_r5_split_exclusions.py` | appends the 15 inputs, rewires 17 rows, three-way verification |

---

## Streamlining status

**R-1 · R-2 · R-3 · R-4 · R-5 · R-6 · R-7 done.** M-1 and T-1 fixed along the way.

**R-8 is the only one left** — row-per-item inputs, removing the 10 locations × 1
building × 1 occupancy class ceiling. It also overlaps the payload generator's
`Payload Export` sheet, which exists largely to transpose column-per-item into
row-per-item; doing R-8 first would shrink that sheet to mostly direct references.

**Two findings owed a decision:**
- `CALC - Special Class` row 26 reading the Location wind/hail input (above).
- The five CoreScratchpad helpers, which need a consumer trace before their
  exclusions can be split.
