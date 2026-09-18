# Property chunk 7, tasks C7-15 to C7-21 — the per-form specifics

2026-09-18. Script:
[`scripts/cf/55_chunk7_perform.py`](../scripts/cf/55_chunk7_perform.py).

Every figure derived by hand before the run, and **all of them landed**.
Baseline: Basic Group I **$39**, Basic Group II **$123**, Broad **$23**,
Special **$47**.

---

## C7-15 · One multiplier, not four — and it keys on the parent

| | Vandalism factor | COL adjustment | **Group I** |
|---|---|---|---|
| baseline | 1.0 | 0.07 | **$39** |
| vandalism excluded, parent class 0951 | **0.95** | 0.067 | **$37** |
| vandalism excluded, parent class 0311 | **0.98** | 0.069 | **$38** |

**The vandalism factor keys on the *parent's* `ClassCode`** — one of the eleven
borrowed values C7-12 enumerated. So an exclusion elected on the Business Income
record is priced from a field on a record **two levels up**, and the same
exclusion is worth a different amount depending on the Special Class item it
hangs off.

### Each absence has a different contrast, and the census only drew one

| Term | here | plain Business Income | Special Class Building |
|---|---|---|---|
| `StdPropPolGroupIFactor` | **0** | **0** | **5** |
| `BuildersRiskFactor` | **0** | **10** | 0 |
| `SprinklerLeakage` | **0** | **86** | 0 |

The opening census compared this group against **Special Class Building** and
reported `StdPropPolGroupIFactor` 0 against 5. True — but plain Business Income
does not have it either, so that absence is inherited from the *Business Income*
side, not dropped from the *Special Class* side.

`BuildersRiskFactor` and sprinkler leakage are the opposite: **plain Business
Income names them 10 and 86 times and neither Special Class group has the
concept at all.** Two absences, two different lineages, and a single-comparison
census cannot tell them apart.

---

## C7-16 · Group II looks its own base rate up, on empty countrywide tables

| Table | CW rows | States filing their own |
|---|---|---|
| `BasicGroupIIRate` | **0** | 45 |
| `LowestBasicGroupIIRate` | **0** | 39 |

**Unresolvable at countrywide for the third coverage group running.** Building,
plain Business Income and this one all read the same two empty tables, and all
three depend entirely on a state filing.

---

## C7-17 · The lowest-rate biconditional — and it does not hold here

Settled inside the sweep. Six states **delete** `SetLowestBasicGroupIIBaseRate`
(AR, DC, KS, NY, RI, TX) and they are six of the eight filing no table. **FL and
PR go a third way**: they leave the rule alone *and* file no table, so they reach
a read with nothing to read.

Chunk 6's biconditional — every state that can reach the read files the table,
and vice versa — **does not survive contact with a second coverage.** A rule
inferred from chunk 6 would have called Florida and Puerto Rico defects.

---

## C7-18 · Broad — construction pinned and covType live, in one lookup

| | Base | **Premium** |
|---|---|---|
| Frame, With Extra Expense | 0.023 | **$23** |
| **parent construction Fire Resistive** | **0.023 — unmoved** | **$23** |
| `CovType` Without Extra Expense | **0.011** | **$11** |

**Both keys sit in the same `rul:Lookup` and only one of them is a literal.**
Construction is pinned to `"Frame"`, so the table's two Fire Resistive rows at
0.012 are unreachable here — while plain Business Income reads them and prices
the same risk at **$12**.

A test that only moved construction would have concluded "this lookup ignores
its keys". Moving covType in the same lookup is what makes the pin visible as a
*pin* rather than as a broken table.

---

## C7-19 / C7-20 · Special — and **both** dimensions are dead

| | Theft factor | COL adjustment | **Premium** |
|---|---|---|---|
| baseline | 1.0 | 0.047 | **$47** |
| parent `ClassCode` 0311 (apartments) | 1.0 | 0.047 | **$47** |
| `ApartmentCondoIndicator = "Yes"` on the record | 1.0 | 0.047 | **$47** |
| **theft excluded** | **0.86** | 0.04 | **$40** |
| theft excluded **+ apartments** | **0.86 — unmoved** | 0.04 | **$40** |

### The algorithms page's open question, answered — and half of it was wrong

The page records the base rate as pinned to `"Other than Apartments and
Condominiums"` **while the theft factor two steps earlier still varies by
`ApartmentCondoIndicator`** — a live dimension feeding a dead key, and it asked
whether that was an ISO simplification or an authoring inconsistency.

**It does not vary.** `SpecialLeaseHoldTimeElementTheftExclusionFactor` files
two countrywide rows — `Yes` 0.96, `No` 0.86 — and the lookup keys that column
on a hard-coded `"No"` from every site that reads it.

**Both dimensions are dead.** There is no inconsistency to explain: the
apartment concept is switched off in this group at *both* sites. Corrected on
the algorithms page, along with the five-way comparison row that carried the
same claim.

### What is pinned here is live next door

The literals census reports the base-rate pin as applying *"from the pinned site
only — the same column is also read live elsewhere"*. That elsewhere is **plain
Business Income, on the same physical table**, which prices the apartments
version of this risk at **$29** against this group's $47.

Same table, same rows, two coverages — one of which can reach half of it.

---

## C7-21 · No Builders Risk branch, and a filed table with no consumer

| | |
|---|---|
| `SpecialFormBldrsRiskTimeElementBaseRate` named in **this** ruleset | **0** |
| …named in **plain Business Income's** | **6** |
| The table itself | **1 countrywide row, 0 states filing their own** |
| Parent `ClassCode` 1150 → premium | **$47, unchanged** |

**Class 1150 is plain Business Income's Builders Risk trigger and it does
nothing here** — the third coverage group in two chunks where that code is
inert (chunk 6 found the same on Special Class Building).

A countrywide row is filed, no state files its own, and this group never names
it. **A filed table is not evidence of a live path**, which is the same lesson
C7-23 is queued to make about `BaseRateAdjustmentFactor` from the opposite
direction — 46 states filing a table nobody here reads.
