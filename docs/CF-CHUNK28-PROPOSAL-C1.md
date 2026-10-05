# Property chunk 28, C28-07: proposal for OI-126 and OI-123 (Set C, messages match ISO)

**Status: PROPOSED 2026-10-05, awaiting the user's go.** No engine code changed. Both items are messages only: no
premium moves under either change (measured on every stored request ISO rated).

## In plain English

Two places where our engine raises a different message from ISO's while every premium agrees.

* **OI-126.** A location asks "do its special class items carry different deductibles?" With one item and no
  deductible, ISO answers "No"; ours answers "Yes" and adds a CP 03 20 message ISO doesn't. The cause: ISO's rule falls
  back to a filed empty value, and ours skips an empty value as if it were nothing.
* **OI-123.** A few of ISO's built rules contain an "is there nothing here?" test with the path stripped out. ISO reads
  it as "nothing is there" (true); ours reads it as "this record is here" (false). So ISO fires a flood message in
  Missouri, and a CP 10 53 message in Georgia, that ours never does.

## Evidence

**OI-126, two readings fit ISO, and nothing ISO files can tell them apart.**

| Reading | Rule | Census | Measured (`249_`, 1,690 stored requests ISO rated) |
|---|---|---|---|
| **A** | `FirstNonNull` returns a filed `<Constant></Constant>` as "" (ours skips "" from every branch) | 14 rules in CW 2026 V01 end a `FirstNonNull` in an empty Constant | message sets equal to ISO 1,677 → **1,679**; fixed C7nd and `OR_chunk7_Basic_noded`; broke 0; premiums moved 0 |
| **B** | `Equal` treats null and "" as the same | every `Equal` / `NotEqual` in Property | **identical to A**: the same 2 fixed, 0 broken, 0 moved |

A census of all 24,028 rule files in the Property corpus found **no rule that compares a bare field to ""**: ISO always
supplies the "" itself (`FirstValue FromConstant=""`, 893 sites in CW 2026, or a parameter bound to "" in an `Else`).
So no filed rule can separate A from B, and on everything ISO has rated they agree. **Proposed: A**, the smaller
change (only a `FirstNonNull` branch that is literally an empty Constant; B would change every equality test).

**OI-123, confirmed live on an in-force package** (`250_`, 2026-10-05). GA 2026-06-01 V01's
`Structure.DoMessageCP1053ShouldBeUsedRatherThanCP1054WhenWindstormOrHailIsExcludedOnlyForDirectDamage` tests
`And(…, Exist(WindstormOrHailExclusion), NotExist())`, the last with no path. A GA building with the exclusion record:
**ISO fires the message** (reading C); without it, ISO does not; 123 of 123 premiums equal on both. Measured (`249_`):

| Reading | Message sets equal to ISO | Fixed | Broke | Premiums moved |
|---|---|---|---|---|
| **C**: an `Exist` / `NotExist` with no path selects nothing (Exist false, NotExist true) | 1,677 → **1,682** | the four MO flood cases (`232_` S / EX / ED / ET-MO) and chunk 25 D5 | 0 | 0 |

## The change (Property only; GL untouched)

1. **OI-126 (reading A).** In `nodes._first_non_null`, a branch that is a `Constant` with empty text returns "" instead
   of being skipped, under `product_skips_null` (Property's existing switch). Every other branch keeps today's rule (a
   "" from data is still skipped).
2. **OI-123 (reading C).** `nodes._exist` / `_not_exist`: no `AtInputDataDef` selects nothing (Exist false, NotExist
   true), under the same switch.

## After the build (C28-11)

`206_ --check` (predicted: messages move on exactly the 7 requests above, no premium), `157_ --all` 293 of 293, the full
`104_ --gate`, `249_` re-run with the change built in (every variant then equal to "now"), and `250_` G0 / G1 from ours.
Registers: OI-126 and OI-123 closed; the CP 03 20 pin in `239_` (C7nd's "known difference") removed.
