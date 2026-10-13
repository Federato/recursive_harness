# Property chunk 4 — gate

**Contents (Personal Property), all four forms.** Opened and gated 2026-09-18.

> **Chunk 4 passes 9 of 9** (point 9 closed 2026-10-02 by chunk 27 RC-2; at the gate it was outstanding here and on chunks 1, 2
> and 3 alike). **No engine code was written** — the fourth coverage in a row on
> chunk 0's foundation, and the first to rate a repeating group.

| | |
|---|---|
| Golden cases | BGI **$223**, BGII **$24**, Broad **$16**, Special **$137** |
| Jurisdictions | **46 of 47**, PR skipped for an enumerated reason |
| ISO calls | **6 this chunk, 6 matches** |
| Building | **unmoved at $263 / $32** in every case |
| Gate-level tasks closed | 9 of 9 (plus C4-10, 11, 12, 30, 31) |

---

## The eight points

### 1 · A golden case rates end to end — **PASS**

Four of them, one per form, each gating on the cause of loss.
[`CF-CHUNK4-GOLDEN-CASE.md`](CF-CHUNK4-GOLDEN-CASE.md) carries the derivation
written before the run and the five corrections it produced.

**Building must not move, and does not** — $263 / $32 in every case in this
chunk. The two coverages share the deductible key, the coinsurance factor and
the protection class, so Contents rating for the first time is exactly the
change that could have disturbed it.

### 2 · Row counts stated; header-only explained — **PASS**

**Every Personal Property base-rate table is header-only countrywide.**

| Table | States filing rows | Never filed by |
|---|---|---|
| `BasicGroupIRate` | 44 of 47 | **AK, CA, PR** |
| `BasicGroupIIRate` | 45 of 47 | FL, PR |
| `SpecialPrsnlPropRate` | 45 of 47 | FL, PR |
| `PrsnlPropTerrMultiplier` | 46 of 47 | PR |
| `SpecialPrsnlPropTheftExclusionFactor` | 46 of 47 | PR |
| `BasicGroupILOIFactorPersProp` · `...IILOIFactorPersProp` · `BroadSpecialLOIFactorPrsnlProp` · `FireSafeVaultFactor` · `BroadFormBaseRate` | 47 of 47, countrywide-filed | — |

### 3 · Every state enumerated, not sampled — **PASS**

**46 of 47** rate Contents Basic Group I exactly as predicted from their own
filed rows. PR skips because `BasicGroupIRatePR` files 83 class codes and
protection classes 8/9/10 only, and **class 0951 is not among them** —
enumerated, not assumed.

**C4-31, which gated this sweep, is the chunk's largest finding.** AK, CA and
PR file `BasicGroupIRate` in **no edition of the corpus** — checked across all
415 copies of that file. Chunk 3's first pass would have skipped them as
unrateable. Chunk 3's *lesson* says look for the overriding rule first, and all
three have one:

| | Reads | District chosen by |
|---|---|---|
| **AK** | `BasicGroupIDistrictIRate` / `...IIRate` | `BasicGroupIRatingTerr` against four literals — `020`, `040`, `050`, `100`. AK's only filed territory is `Entire State`, none of them, so AK is **always District II** here |
| **CA** | the same two tables | a `District` field **six levels up**, `District I` / `District II` |
| **PR** | `BasicGroupIRatePR` | no district — and it is keyed on **`ProtectClass`**, a protection-class dimension in the base rate no other jurisdiction has |

**Three different district mechanisms for two districts.** ISO confirms both
readings: CA $208, AK $224.

### 4 · Every `0` tested against its consuming branch — **PASS**

Seven cases, [`25_chunk4_zero_cases.py`](../scripts/cf/25_chunk4_zero_cases.py).
Five new zero sites, three of them in rules Building does not have.

**The finding is Z2.** Removing the location's `ProtectClass` prices Contents
at **zero** and Building at **$275 — higher than the $263 baseline**. Building's
protection-class factor falls back to 1.0; Contents' falls back to 0.0. **One
blank field, two coverages, opposite directions, no message either way.**

A blank protection class is routine data entry.

### 5 · Every hardcoded literal key listed — **PASS**

Personal Property's literal set is its own — chunk 1's Building census does not
cover it. 31 literals across the PP rules, including:

* **`1150` is EXCLUDED from the class-rate path**, where Building *routes* it to
  the Builders Risk rows. Opposite treatment of the same literal.
* **`1751` / `1752`** gate the protection-class factor out.
* **`YARD`** appears in 5 rules and substitutes construction codes `1` or `3`.
* **`Valuable Papers and Records - Other Than Electronic Data`** appears in 7
  rules, zeroing the rate inside the rate step rather than at a gate.
* **`Legal Liability`** and **`Tobacco Sales Warehouses`** each gate all four
  LOI rules.

### 6 · Shared-name traps diffed, not assumed — **PASS**

**17 ambiguous names on the Contents chain, and chunk 4 executes the PersProp
half of every one chunks 1–3 adjudicated.** The adjudications hold exactly as
written there:

    LookupBasicGroupILOIFactor   -> BasicGroupILOIFactorPersProp
    LookupBroadSpecialLOIFactor  -> BroadSpecialLOIFactorPrsnlProp
    SetSpecialBaseRate           -> SpecialPrsnlPropRate
    SetSpecialTheftExclusionFactor -> SpecialPrsnlPropTheftExclusionFactor

`SetSpecialBaseRate` is the case gate point 6 was written around — 16 datadef
groups, five tables. Chunk 3 took `SpecialBuildingRate`; chunk 4 takes
`SpecialPrsnlPropRate`. **The adjudication written in chunk 3 predicted chunk
4's behaviour correctly**, which is the first time that method has paid forward.

### 7 · Every exclusion's endorsement record identified — **PASS**

The PersProp half of each family:

| Family | Ours | Records / groups |
|---|---|---|
| Theft | `CommercialPropertyTheftExclusionPrsnlProp` | 5 / 7 |
| Vandalism | `...VandalismExclusionPrsnlProp` | 5 / 13 |
| Wind/hail | `...WindstormOrHailExclusionPrsnlProp` | 5 / 19 |
| Sprinkler leakage | `...SprinklerLeakageExclusionPrsnlProp` | 3 / 7 |
| Terrorism (3 families) | policy-level, 1 record each | 1 / 5 |

Confirming chunk 3's correction to the gate's own premise: **not every
exclusion is per-coverage.** The terrorism families and Cyber file one record
at the policy level.

### 8 · The edition basis stated — **PASS**

`OR@20260917` over `CF_CW_20260601_V01`, as chunks 1–3. The sweep resolves each
jurisdiction's own chain; CA lands on `CF_CA_20251201_V01` over an older
countrywide pair and rates correctly there.

### 9 · No unexplained validation message — **DONE 2026-10-02** (chunk 27 C27-03)

`239_chunk27_rc2.py --live`: Basic 3 = 3, Broad 3 = 3, Special 4 = 4 at ISO (the contents cases sent with the building's `WindstormOrHailDeductible`; without it ISO refuses, OI-103); every message in the register (M-001, M-002, M-004, M-005). The refusal below is now located: the lookup reads the **building's** field. The original note, kept:

Owed on all four chunks. Chunk 4 adds one new message — *"Full Value cannot be
lower than the Limit"* — which fires because the Contents record carries a
limit and no full value.

---

## ISO confirmation — and a refusal worth more than the matches

**6 calls, 6 matches:**

| Case | Engine | **ISO** |
|---|---|---|
| OR Basic | Contents 223 / 24, Building 263 / 32 | **all four** |
| OR Broad | Contents 16 | **16** |
| OR Special | Contents 137 | **137** |
| OR, two items 100k + 50k | 209 and 105 | **209 and 105** |
| CA Basic (District split) | 208 | **208** |
| AK Basic (District split) | 224 | **224** |

The two-item call is the important one: **ISO sums a repeating group the way we
do**, and the District calls confirm a reading of a table that does not exist
countrywide.

### ISO refused the first four attempts, and our engine did not

Every Contents payload without a `WindstormOrHailDeductible` was refused:

    Matrix: WindstormOrHailDeductibleAsNumber, Keys: CW, .
    No results have been returned.

**Our engine rates that submission happily.** This is a fresh, concrete
instance of the open `SingleResult`-with-zero-hits question from chunk 2 —
where blanket strictness was measured and *disproven* because it broke Virginia
and Vermont, which ISO rates. Here is the other side: a lookup ISO **does**
refuse on, in a coverage chunk 2 never touched.

That does not settle the distinguishing condition, but it is the first
same-corpus pair of a refusal and a tolerance, and it is the best material yet
for the targeted probes that open item calls for.

---

## What the build found that the plan did not

**Four fields turned out to be inherited, not per-item.** `CovForm` was known.
`BldgClassCode`, `RatingType` and `OccupCategoryRiskSeverity` were not. All
four are `Copy`d from an ancestor, and **a submission that sets them per item is
silently overruled** — the C4-11 test was first written against a per-item class
code and produced a perfect false positive for a `ForEach` leak.

**`OccupCategoryRiskSeverity` is the mirror of chunk 3's derived-field hole.**
There, every `IsNull`-guarded rule honoured a submitted value and let it bypass
the filed table. Here an unguarded rule *discards* one — and with no class code
on the occupancy it writes **blank**, gating Special shut. Same ambiguity, both
directions, neither raises.

**PP rounds once per rate step where Building rounds at every `Product`**, and
**the adjusted rate applies coinsurance before the limit factor**, not after as
the algorithms page records. Two chains, two rounding shapes, in the same
engine.

**The PersProp limit curves run below 1.0 where Building's run above** — 0.898
against 1.172, 0.843 against 1.266, 0.790 against 1.237. A Contents premium is
not a scaled Building premium at any limit.

**The LOI factor is the occupancy's, not the item's.** Two items of 100,000 and
50,000 both take the 0.842 that a 150,000 occupancy total gives, not the 0.898
and 1.000 their own limits would. Two small items do not price as one large one.

---

## What is still owed

1. **Gate point 9**, on all four chunks.
2. **Input validation**, now three requirements: reject a missing input that
   prices at zero; reject a submission that populates a derived field (chunk 3);
   and **reject a submission that sets an inherited field per item**, which is
   accepted and discarded today.
3. **The `SingleResult` probe.** Chunk 4 supplies the refusal half of the pair.
4. **PR has no ISO confirmation and never will**, and it is now also the only
   jurisdiction that cannot rate Contents Basic Group I for the golden case's
   class code.
5. **The state-layer shared-name check** — still nothing looks for it, and
   chunk 4 found three more instances (AK, CA, PR).

## What is deliberately not here

Earthquake (chunk 10; PP has its own EQ chain). Legal Liability (chunk 8).
Blanket (chunk 9, still a stub). Business Income (chunk 5). Theft limitations,
sublimits, agreed value, inflation guard, vacancy — endorsements, chunk 12.
The Special-specific tasks C4-13 and C4-24 through C4-28 are open; they are
form detail, not gate conditions.

---

## Reproducing it

    python scripts/cf/22_chunk4_golden_case.py        # four forms
    python scripts/cf/23_chunk4_foreach.py            # the repeating group
    python scripts/cf/24_chunk4_enumerate_states.py   # 46 of 47
    python scripts/cf/25_chunk4_zero_cases.py         # 7 zero cases
    python scripts/cf/04_shared_names.py              # point 6, all four chunks
    python scripts/cf/05_exclusion_records.py         # point 7 census

All exit 0 as of 2026-09-18.
