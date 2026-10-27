# Property chunk 3, task 5 — shared-name adjudication

**Gate point 6: a shared name is a question.** Run 2026-09-18,
`scripts/cf/04_shared_names.py` (extended, not replaced).

| | |
|---|---|
| Ambiguous names on chunk 3's chain | **9** |
| Adjudicated, and matching the corpus | **9 of 9** |
| Also re-opened and re-closed | chunk 1 (**6**), chunk 2 (**4**) |
| Exit | 0 |

---

## The check itself was broken, and that is the finding

Chunk 3 is where point 6 was supposed to earn its keep: `SetSpecialBaseRate`
and `SetSpecialTheftExclusionFactor` are the corpus's *documented*
same-name-different-table cases, and both live on this chain. The script
reported neither.

**Because it could not see them.** It collected the rate tables named directly
inside each rule — and ISO's `Set*` rules almost never contain a lookup. They
delegate to a `Lookup*` rule by name. So the two documented traps, defined in
**16** and **6** datadef groups respectively, each reported **zero** tables and
could never have been flagged.

The fix is to follow `RunRule` transitively within the datadef group and
collect what the rule actually *reaches*. The difference:

| | Direct only (as it ran) | Transitive (as it should have) |
|---|---|---|
| Chunk 1 chain | 1 ambiguous name | **6** |
| Chunk 2 chain | 1 | **4** |
| Chunk 3 chain | 1 | **9** |
| Whole corpus | 9 | **83** |

**Chunks 1 and 2 passed gate point 6 under that blindness.** Nine of their
combined ten ambiguities were invisible. They are re-run and re-closed here —
all ten adjudicated and matching — but the honest statement is that those two
gates were passed on a weaker check than the one they now stand on.

This is the third time the project has found a defect in its own instrument
rather than in the corpus, and the pattern is worth naming: **a check that
reports "nothing found" needs its denominator tested as hard as its findings.**
Point 6 was returning "1 name, benign" on every chunk, which read as a clean
bill of health and was really a near-empty search.

---

## The chunk 3 adjudications

All nine, and what each answer is.

### The two documented traps — both real, one wider than documented

**`SetSpecialBaseRate` → `SpecialBuildingRate` + `SpecialBuildersRiskRate`**

Sixteen datadef groups define this single rule name, reading **five** different
tables:

| Table | Groups |
|---|---|
| `SpecialBuildingRate` | 6 — including ours |
| `SpecialFormIncldgTheftTimeElementBaseRate` | 6 |
| `SpecialPrsnlPropRate` | 2 |
| `SpecialFormBldrsRiskTimeElementBaseRate` | 1 |
| `SpecialBuildersRiskRate` | ours, on the class 1150 branch |

Ours reads the building rate *and* the Builders Risk rate, because the rule
branches on class code 1150 before it looks anything up. Nothing in the rule
name, the datadef name or the returned value tells these five apart — only the
datadef group does. **Chunks 4, 5, 6 and 7 each execute a different one.**

**`SetSpecialTheftExclusionFactor` → `SpecialBldgTheftExclusionFactor`**

A cleaner three-way split: Structure and SpecialClass read the building table,
PersonalProperty reads `SpecialPrsnlPropTheftExclusionFactor`, and the three
time-element groups read `SpecialLeaseHoldTimeElementTheftExclusionFactor`.
Against yesterday's sweep finding: **Puerto Rico overrides this rule** and folds
the theft decision into its cause-of-loss values, so PR reaches no theft factor
at all.

### The shared LOI table — three names, one answer

`LookupBroadSpecialLOIFactor`, `SetBroadLOIFactor` and `SetSpecialLOIFactor`
all split Building-side / Personal-Property-side, exactly as Group I's and
Group II's equivalents do. Ours reads `BroadSpecialLOIFactorBldg` in all three.
Scoped by datadef group, dispatched correctly — and chunk 4 executes the other
half of every one of them.

### Two silences, now deliberate

`SetBroadRate` and `SetSpecialRate` are each defined in five datadef groups and
**ours is not among them**: Debris Removal reads `DebrisRemovalRate`, Leasehold
Interest reads `LeaseholdInterestBroadSpecialRate`, Pollutant Clean-Up reads
`PollutantCleanUpAndRemovalRate`. Chunk 3's rate step is a pure `Product` of
base rate × loss cost multiplier with no lookup of its own, so reading *nothing*
is the correct answer — and it is now asserted rather than assumed. A lookup
appearing there later fails the script.

### The two orchestrators, asserted as sets

`SetBroadRatesAndFactors` reaches **4** tables; `SetSpecialRatesAndFactors`
reaches **7**. The difference is exactly the three steps Special has that Broad
does not — the theft exclusion factor, its own deductible-by-location rule, and
the Builders Risk base-rate branch. Asserting the whole set means a table
silently entering or leaving either chain fails the check.

---

## What the re-run turned up on chunks 1 and 2

Two entries worth carrying forward rather than filing:

**`SetBasicGroupIBaseRate` is the trap shape sitting on the spine of the
build.** Structure and PersonalProperty read `BasicGroupIRate`; SpecialClass
and OutdoorTreesShrubsAndPlants read `BasicGroupIRateSpecialClass`. Chunk 1 is
correct because of the group it executes in. **Chunk 6 executes the other
half**, and the build order already warns that Special Class keys on class
*description* rather than class code — so that chunk now starts from a written
answer instead of a rediscovery.

**`SetCoinsuranceFactor` gives the first concrete fact about blanket rating.**
Fourteen groups, three tables: ours reads `CoinsuranceFactor` plus
`LessThan80PctMultiplicativeFactor`, but **BlanketRatingDetail and
PeakSeasonGeneralInformation read `CoinsuranceFactorBlkt`** — a different table
entirely. Blanket is chunk 9 and is a stub in every premium file built so far;
this is the first thing known about what it will actually need.

Also recorded: `SetBGIIRatesAndFactors` reaches `GroupIIOpenSidesNumericValue`,
which chunk 2's golden case never exercises. Reachable but untested, which is a
statement worth having in writing.

---

## Not covered here

The sweep found a same-name-different-table case in the **state** layer — FL
and PR overriding `SetSpecialBaseRate` to read `SpecialBuildingRateNonResidential`
and `SpecialBldgRate`. This script scans one package and compares across datadef
groups, so it does not see that dimension. It is written up in
[`CF-CHUNK3-STATE-SWEEP.md`](CF-CHUNK3-STATE-SWEEP.md), and extending the check
across states is logged as an open item rather than done here.
