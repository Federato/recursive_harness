# Property chunk 28, C28-04: proposal for Set A, refuse where ISO refuses

**Status: PROPOSED 2026-10-02, awaiting the user's go.** No engine code changed. Evidence:
[`CF-CHUNK28-REFUSALS.md`](CF-CHUNK28-REFUSALS.md) (C28-02, C28-03); impact measured with the engine's own measurement
switch by `scripts/cf/247_chunk28_c28-04_strict_impact.py` and `104_ --quick --no-gl` under `ERC_STRICT_SINGLE_RESULT=1`.

## In plain English

When ISO's rules look up a row that must exist and it doesn't, ISO refuses the whole policy. Ours carries on with a
blank and prices something, often $0: a policy ISO would reject comes back from us as a quiet, plausible premium. The
proposal makes ours refuse at exactly those points, with an error naming the table and keys, the way ISO's does. One
exception is carried over from the evidence: when a state files an **empty** table, ours keeps using countrywide's rows
(ISO does, twice), except for the one table where ISO refuses instead (the earthquake sub-limit tier stub, three states
out of three).

## The change (Property only; GL untouched)

1. **A `SingleResult` lookup that matches no row refuses the policy.** The interpreter already implements this as a
   measurement switch (`strict_single_result`, `gl_engine/interp/interpreter.py`). Proposed: it defaults ON when the book
   is a Property book (`CFResolvedBook`), and stays OFF for General Liability (whose ISO behaviour is not measured).
   The refusal is an `InterpretError` naming the table and keys, as ISO's 400 does.
2. **The empty-table fallback keeps its one known exception.** `CFResolvedBook.table` stops falling back to countrywide's
   rows for `EQSubLimitDeductibleTierCWTable` (refused at ISO in MA, TN and VT, 2026-10-02). Every other empty state
   table keeps the fallback (ISO used countrywide's rows for VT `VacancyPermitFactors` and NY
   `OffPremEndtsModifyingCovdCOLFactor`).
   * *Option, not proposed:* generalise to "any lookup whose keys are all constants reads the state's table as filed".
     It fits all five data points but no second case has been probed (C28-03); it would touch more lookups on less
     evidence.

## What it would change, measured (no code changed)

| Population | Today | Under the change | Predicted |
|---|---|---|---|
| C28-02's 66 live ISO refusals | ours prices all 66 | **refuses 65 at ISO's own table**; VT E7 prices (empty-table fallback) | 65 + E7 |
| …with part 2 (the EQ stub exception) | | *predicted, not measurable without the code*: E7 refuses too, 66 of 66 | 66 |
| The 1,690 stored requests ISO **rated** | rated | **0 new refusals** (the 4 old-edition probes that already raise today are OI-114, not a lookup) | 0 new refusals |
| `104_ --quick --no-gl` (31 CF scripts) | clean | **4 scripts fail, every one on a case ISO itself refuses**: golden cases 1 (case B), 4 and 8 (contents without the building's `WindstormOrHailDeductible`: OI-103, chunk 27) and `208_` MRZ (pinned "ISO refuses; ours $0") | only ISO-refused cases |

## What the build (C28-05) would also update

* **Golden cases 1, 4, 8**: send the building's `WindstormOrHailDeductible` "1,000", as ISO requires. Measured
  2026-10-02: every pinned figure unchanged ($223 / $24 / $16 / $137, building $263 / $32).
* **Scripts that pin "ISO refuses; ours $0"** (`208_` MRZ, `195_` E7, `230_`–`233_` and others recording an OI-103 case):
  each now expects ours to refuse, with ISO's table.
* **OI-99, OI-103**: closed by the change, each case listed; **OI-117** (`Convert` of a blank, not a lookup) stays open.

## Regression after the build (C28-06)

`206_ --check` (the snapshot will move only where a stored request was refused: predicted none, since every snapshot
request rated at ISO), `157_ --all` (293 of 293), the full `104_ --gate` (the engine changed), then `245_ --refused`
re-run: **ours refuses exactly where ISO does**.
