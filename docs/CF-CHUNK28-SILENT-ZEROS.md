# Property chunk 28, C28-15: the silent-zero table (Sets B and E)

**Status: DONE 2026-10-05.** `scripts/cf/254_chunk28_c28-15_silent_zeros.py --live`, ISO at 2026-09-17; no engine change.

## In plain English

The inputs on record that let a normal-looking submission come out cheap without a word, each sent to ISO beside a
control that differs only in that input. **Every one either matches ISO exactly or is refused by both.** None is a rating
difference. And ISO raises **no message** on any of the zeros: they are silent at ISO too. So Set B is not about
matching ISO. It is a validation layer of our own, on top of the rating, for answers that are technically valid and
almost certainly a mistake.

## The table

| Case | Input (one moved against its control) | Ours | ISO | Class |
|---|---|---|---|---|
| Z-AZ | Arizona without the location's `BasicGroupIReductionCredit` | Group I $0 (policy 865 vs 1,479) | the same, no message | **ISO also $0** |
| Z-CT | `ConstructionType` "Brick" (not a filed value) | refuses (`ConstructionTypeToUse`) | refuses, same table | **both refuse** (Set A, since C28-05) |
| Z-CTR | `ConstructionType` "Masonry Non-Combustible" (a rating-type name) | refuses (`ConstructionTypeToUse`) | refuses, same table | **both refuse** (Set A) |
| Z-BCEG | no `BCEG` | Group II $0 (261 vs 293) | the same, no message | **ISO also $0** |
| Z-G2T | no `BasicGroupIIRatingTerr` | Group II $0 (261 vs 293) | the same, no message | **ISO also $0** |
| Z-DB | Broad form, blank `Deductible` | the whole building $0: Group I, Group II and Broad (policy $0 vs 309) | the same, no message | **ISO also $0** |
| Z-DS | Special form, blank `Deductible` | the whole building $0: Group I, Group II and Special (policy $0 vs 347) | the same, no message | **ISO also $0** |
| Z-RT2 | no `RatingTypeBasicGroupII` | 293, unchanged | 293 | **no longer a zero** on this policy |
| Z-NY | New York without `BasicGroupIISymbol` | 1,316, unchanged | 1,316 | **no longer a zero** on this policy (chunk 27's NY case was a different policy) |

Controls C-AZ (1,479), C-OR (293), C-B (309), C-S (347), C-NY (1,316): every premium equal to ISO.

## What it means for C28-16 (the design, needs the user's go)

* **Five inputs are a validation gap only:** ISO prices them the same, silently. A caller can't tell a real $0 from a
  missing answer. The design question is how ours says so (a "probably invalid input" outcome beside the premium),
  not how the premium is computed: no premium ISO agrees with may change (C28-17's rule).
* **Two are already refusals** at ISO and in ours (C28-05).
* **Two no longer zero** on the policies tested; they stay listed as watch items, not validation rules.
* **OI-113** (minimum premium: ISO's outcome is "refer to company") belongs in the same outcome layer.
