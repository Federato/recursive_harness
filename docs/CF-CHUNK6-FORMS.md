# Property chunk 6, tasks C6-20 to C6-23 — four claims about three forms

2026-09-18. Script:
[`scripts/cf/47_chunk6_forms.py`](../scripts/cf/47_chunk6_forms.py).

---

## C6-20 · The fire-only gate is narrower than Building's — two strings, not four

`SetBasicGroupIICauseOfLossAdjustment` zeroes the Group II rate when
`CauseOfLossToUse` is one of:

| | Building tests | Special Class tests |
|---|---|---|
| `Fire` | ✔ | ✔ |
| `Fire and Vandalism` | ✔ | ✔ |
| `Fire and Sprinkler Leakage` | ✔ | **✘** |
| `Fire, Vandalism and Sprinkler Leakage` | ✔ | **✘** |

| Cause of loss | Special Class Group II | Building Group II |
|---|---|---|
| Basic | $209 | $32 |
| `Fire` | **$0** | — |
| `Fire and Vandalism` | **$0** | — |
| `Fire and Sprinkler Leakage` | **$209** | **$0** |
| `Fire, Vandalism and Sprinkler Leakage` | **$209** | **$0** |

**The same submission field zeroes a Building's Group II and leaves a Special
Class item's alone.** Two coverages, one value, opposite answers — and the
reason is structural rather than arbitrary: **Special Class has no sprinkler-
leakage term anywhere in its chains**, so a cause of loss that names sprinkler
leakage has nothing here to switch off.

The starker of the two is `"Fire, Vandalism and Sprinkler Leakage"`. Vandalism
*is* a Special Class concept — the vandalism exclusion factor is in the Group I
adjustment — so the combined string falls outside a gate that catches plain
`"Fire and Vandalism"`.

**Basic Group I is $66 throughout**, because it is not gated on the cause of
loss at all (C6-26).

---

## C6-21 · Group II's coinsurance surcharge comes from a different table

| | Group I factor | Group II factor | Group II premium |
|---|---|---|---|
| OR, 90% | 0.95 | 0.95 (copied) | **$209** |
| OR, 50% | **1.5** `LessThan80Pct…` | **1.5** `…FlatCoinsuranceFactor` | **$329** |
| **FL, 50%** | **1.5** | **1.42** | — |

**Countrywide the two tables file the same 1.5, so nothing in an Oregon premium
could tell them apart.** Florida files its own
`BasicGroupIIFlatCoinsuranceFactor` at **1.42** and leaves
`LessThan80PctMultiplicativeFactor` countrywide — so **in Florida the two Basic
forms take different coinsurance surcharges from what looks like one concept.**

That is the discriminating case C6-15 could not produce, and it needed a second
jurisdiction to exist at all.

Direction, again: **Group II at 50% costs $329 against 90%'s $209.** A lower
coinsurance percentage is a higher premium in both Basic forms.

**Puerto Rico declares both tables header-only** — 0 rows each. A state with no
coinsurance surcharge of any kind, expressed by filing two empty tables rather
than by changing a rule.

*(Florida's Group II premium is $0 on this case for an unrelated reason — the
golden case's class description is not in Florida's converter, C6-11. The
factors are still computed, which is itself worth noting: the coinsurance
factor is produced before and independently of any base rate.)*

---

## C6-22 · Broad is construction-blind

| Construction (both legal values) | Special Class Broad | Building Broad |
|---|---|---|
| `Frame` | **$14** | **$16** |
| `Fire Resistive - Reinforced Masonry - Light Steel` | **$14** | **$12** |

`LookupBroadFormBaseRate` keys on the hardcoded literal `"Frame"`. The table's
two Fire Resistive rows at 0.010 are filed, published and **unreachable on this
path**. ISO confirmed this independently in C6-08 — the same item re-sent as
Fire Resistive came back at $14 again.

### The first draft of this test proved nothing, and that is the lesson

It sent all six construction values copied out of `BroadFormBaseRate`'s key
column and reported Special Class holding at $14 for every one. **Four of those
six are not values `ConstructionTypeToUse` ever resolves to.** On a Building,
plain `"Fire Resistive"` resolves to *nothing* — construction code 0, base rate
0, premium 0.

**A test that sends an unrecognised string and reports "unchanged" cannot tell
construction-blindness from a bad input.** Both strings in the table above are
pinned by Building *moving* on the identical change. That is what makes the
Special Class result mean something.

### And a prediction that was wrong by a dollar

Building's Fire Resistive Broad was predicted at **$11** — Frame's $16 scaled by
the base-rate ratio 0.010 / 0.015. **It is $12.** The chain rounds to three
decimals at *every* step, and at rates this small the rounding dominates the
ratio: Frame's final rate is 0.016 and Fire Resistive's is 0.012, a ratio of
0.75 where the base rates are 0.667 apart.

**A two-thirds rate does not produce a two-thirds premium.** Worth recording
next to the project's still-open per-step-versus-once rounding question.

---

## C6-23 · Special reads Building's unfilled table, and has no Builders Risk branch

| | |
|---|---|
| `SpecialBuildersRiskRate` named in the **Structure** ruleset | **6** |
| …in the **SpecialClass** ruleset | **0** |

| Class code | `SpecialBaseRate` | Premium |
|---|---|---|
| 0951 | 0.047 | **$44** |
| **1150** | **0.047** | **$44** |

**Class 1150 is Building's Builders Risk trigger and it does nothing here.**
Building branches to its own `SpecialBuildersRiskRate` on that code; Special
Class always resolves through `LookupSpecialBuildingRate`, whatever the class.

### The same countrywide gap, with a second consumer

`SpecialBuildingRate` is **header-only countrywide** — the gap chunk 3 found on
Building. 45 jurisdictions file their own rows; **FL and PR do not**, and both
therefore read the empty countrywide table and cannot price the Special form at
all.

It is the same two states, the same table and the same silence as chunk 3 — now
reached through a second coverage. A fix to the Building side would not touch
it, because nothing is broken in either place: the rows are simply not filed.
