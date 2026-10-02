# Property chunk 2 — gate

**2026-09-17. Building, Basic Group II, class-rated, scheduled — Oregon.**

> **Point 9 closed 2026-10-02 (chunk 27 RC-2, `239_chunk27_rc2.py --live`).** The golden case sent to ISO as the engine rates it: (level, message) 2 = 2, both in the register (M-001, M-002). Nothing unexplained.


Assessed against the eight-point gate in [`CF-PROPERTY-BUILD-ORDER.md`](CF-PROPERTY-BUILD-ORDER.md).
Task list and open items: [`CF-CHUNK2-TASKS.md`](CF-CHUNK2-TASKS.md).

> ## Verdict: **PASS on 8 of 8.**
>
> **No engine code was written for this chunk.** Eleven steps, a second territory scheme, four
> symbol-override branches, a parallel rate path and four new factors all executed on chunk 0's
> foundation as-is. That is the build order's claim about differential gates, tested.
>
> One submission produces **Group I $261 and Group II $32**, and ISO returns both. Fifteen ISO calls
> across chunks 1 and 2 have now matched the engine every time.
>
> **Four findings are worth more than the pass:**
>
> * **39 of 47 jurisdictions override `SetBasicGroupIIRate`**, 36 of them gating on a field
>   countrywide does not have. The documented countrywide chain is the *minority* behaviour.
> * **An absent Building Code Effectiveness Grade prices Group II at zero** — confirmed at ISO.
> * **The wind/hail "ineligible in 8 states" reading is wrong for half of them.**
> * **`ConstructionType` has one submittable vocabulary**, and `Frame` is the only value that works
>   for both coverage groups — which is the sole reason this chunk's one-building-two-premiums
>   design works at all.

Reproduce:

    python scripts/cf/09_chunk2_golden_case.py       # points 1, 2, 8
    python scripts/cf/10_chunk2_zero_cases.py        # point 4
    python scripts/cf/11_chunk2_enumerate_states.py  # point 3
    python scripts/cf/12_chunk2_windhail.py          # the flagged trap
    python scripts/cf/13_chunk2_symbol_and_numeric.py
    python scripts/cf/14_chunk2_fire_only_gate.py
    python scripts/cf/04_shared_names.py             # point 6, both chains
    python scripts/cf/08_hardcoded_literals.py       # point 5, whole coverage

---

## The eight points

### 1 · A golden case rates end to end, every intermediate traced — **PASS**

`09_chunk2_golden_case.py`, derived by hand before the code ran. Symbol `B`, base rate 0.028,
BCEG 0.96, rate 0.027, adjusted 0.033, final 0.032, **$32** — every value matched on the first run,
and **Group I stayed at $261**, which was the case's real test: the two chains are independent.

Plus 21 further cases across zeros, wind/hail, symbols and the fire-only gate.

### 2 · Row counts stated; header-only explained — **PASS**

**`BasicGroupIIRate` and `LowestBasicGroupIIRate` are both header-only countrywide.** Every Group II
rate in existence comes from a state filing.

| Table | CW | resolves non-empty in |
|---|---|---|
| `BasicGroupIIRate` | **0** | 45 of 47 — not FL, not PR |
| `LowestBasicGroupIIRate` | **0** | 39 of 47 |
| `WindstormOrHailExclFactor` | 4 | 39 of 47 — **the same 8 missing** |

The two tables the wind/hail branch needs are missing in exactly the same 8 jurisdictions — **by two
different mechanisms**, which is the N3 distinction. `WindstormOrHailExclFactor` is filed *by those
states themselves with zero rows*: an explicit empty override meaning "not offered here".
`LowestBasicGroupIIRate` is simply never filed.

### 3 · Every state enumerated, not sampled — **PASS**

`11_chunk2_enumerate_states.py`. Each jurisdiction gets its own case from its own rows, predicted
before the engine runs. **41 of 47 exact, 0 failures.** Six skipped with stated reasons: FL has no
Group II rate at all; MT, NY and PR resolve to an empty symbol table; DC and IL have no `BCEGFactor`
row for their own Group II territory.

**The finding that nearly hid:** almost every state returned $0 on the first run.

> **39 of 47 jurisdictions override `SetBasicGroupIIRate`, and 36 of those gate it on
> `RatingTypeBasicGroupII`** — a Group II-specific rating type the countrywide rule has no concept
> of. Omit it and 36 states price Group II at zero: base rate resolves, every factor resolves, and
> the rate is 0 because the state's `Choose` matched no branch.
>
> So the chain documented in `CauseOfLoss_Building_RatingAlgorithms.md` is run by **8 of 47**. The
> countrywide chain is the exception, not the rule, and every later chunk has to re-ask this.

### 4 · Every `0` tested against its consuming branch — **PASS**

`10_chunk2_zero_cases.py`. Group II's zeros enter at more places than Group I's.

| Case | symbol | base | rate | coladj | GII | GI |
|---|---|---|---|---|---|---|
| baseline | B | 0.028 | 0.027 | 0.027 | **32** | 261 |
| Z1 blank Group II territory | B | **0** | 0 | 0 | **0** | 261 |
| Z2 blank `NumStories` | **(none)** | 0 | 0 | 0 | **0** | 261 |
| Z3 fire-only cause of loss | B | 0.028 | 0.027 | **0** | **0** | 242 |
| Z4 **BCEG absent** | B | 0.028 | **0** | 0 | **0** | 261 |

**Z1 is what chunk 1 did by accident.** Its submission supplied Group I's territory and not Group
II's, so Group II priced at zero and nothing said so.

**Z4 was written expecting the opposite.** An absent Building Code Effectiveness Grade does *not*
default the factor to 1.0: `SetBCEGFactor` assigns only when territory and grade are both non-blank,
and `SetBasicGroupIIRate` reads it through `FirstValue FromConstant="0.0"`. The base rate still
resolves, which is what makes it look healthy. **ISO confirms: with BCEG $32, without $0.**

**Z3's Group I figure was also predicted wrong** — 255 rather than 242, because the derivation forgot
that `VandalismExclFactor` fires automatically on a Standard Property Policy fire-only form. The
behaviour was already documented; the engine had it and the prediction did not.

### 5 · Every hardcoded literal key listed — **PASS**

`08_hardcoded_literals.py` already covers Group II: it scans the whole Building coverage, not one
chain. The Group II pins:

| Table . column | pinned to | unreachable | scope |
|---|---|---|---|
| `BasicGroupIISymbolAdditionalClasses.ClassificationCode` | `OpenSides` | 5 of 6 | pinned site only |
| `BasicGroupIISymbolAdditionalClasses.ConstructionCode` | `1` | 5 of 6 | pinned site only |
| `BasicGroupIIRate.CovType` | `Bldg` | 1 of 2 | **every site** |
| `LowestBasicGroupIIRate.CovType` | `Bldg` | 1 of 2 | **every site** |

The `CovType` pins are the Building/Contents split — expected, and now recorded rather than assumed.

### 6 · Shared-name traps diffed, not assumed — **PASS**

`04_shared_names.py`, now run over the Group II chain as well. Of 28 chain names living in more than
one datadef group, **one** reads different tables: `LookupBasicGroupIILOIFactor`, splitting the same
nine groups the same way as Group I's — five Building-side, four Personal-Property-side. Adjudicated
and asserted, so it fails if the answer stops matching the corpus.

**One real difference found while checking:** `BasicGroupIILOIFactorBldg` is keyed on
`(StateCode, Limit)` **only**. Group I's is keyed on `(StateCode, Limit, ConstructionCode)`. Same
name shape, same table shape, one fewer key.

### 7 · Every exclusion's endorsement record identified — **PASS**

From `05_exclusion_records.py`, the families Group II touches: **Windstorm or Hail** — 17 datadef
groups, **5 distinct endorsement records**, one per coverage; **Cyber Incident** — one record, read
at policy level through the Group II-specific `CyberIncidentExclusionFactorBGII`.

Chunk 2 elects the wind/hail exclusion for real (see below) rather than only enumerating it.

### 8 · The edition basis stated — **PASS**

`CF_OR_20260601_V01` over its declared parent `CF_CW_20260601_V01`, as-of 20260917. No table came
from an older edition and none needed to.

---

## The wind/hail branch — the trap the build order flagged

`12_chunk2_windhail.py`. When the exclusion is scheduled, Group II **discards** the rate it just
built and rebuilds from the statewide *lowest* rate — keyed on symbol alone, no territory:

| | coladj | final | premium |
|---|---|---|---|
| normal | 0.027 | 0.032 | **$32** |
| wind/hail excluded | 0.009 | 0.011 | **$11** |
| ...and BCEG removed | 0.009 | 0.011 | **$11** |

**The third row is the structural proof.** Removing BCEG changes nothing here, while on the normal
branch it takes the premium to zero. The rebuilt form genuinely drops `BCEGFactor` and
`BasicGroupIINumericValue` — the build order's "silently drops the class hazard load".

### "Ineligible in 8 states" is wrong for half of them

All 8 override `SetBasicGroupIICauseOfLossAdjustment`, and the overrides split three ways:

| | |
|---|---|
| **FL, KS, PR** | their **own** mechanism — a direct `BasicGroupIIWindstormOrHailExclRate` (a rate, not a factor on the lowest rate), plus a `PublicInstitutionalPlanFactor` branch countrywide has no concept of. Kansas goes **$470 → $27**: priced, not ignored |
| **AR, DC, NY, RI** | never test for the exclusion record — genuinely ignored |
| **TX** | a fourth shape, not yet traced |

So an empty `WindstormOrHailExclFactor` override is **not** evidence of ineligibility. It means the
state does not use the *countrywide* mechanism — for three of them because they have their own.

The Kansas case was written twice and wrong both times: first "collapses to zero", then "ignored".
Asserting rather than observing is what caught it.

---

## The symbol overrides and the numeric value

`13_chunk2_symbol_and_numeric.py`. Oregon files four symbols at distinct rates, so an override moves
the rate row.

| Case | symbol | numeric | Group II | Group I |
|---|---|---|---|---|
| baseline, Frame | B | 1 | 32 | 261 |
| `OpenSides = Yes` | B | **4** | **127** | 261 |
| class 0580 | B | **4** | **127** | 108 |
| bare `Masonry Non-Combustible` | — | 1 | **0** | **0** |
| oil distributing station (1751) | **AB** | 1 | 27 | 69 |
| detailed construction type | **A** | 1 | 18 | 183 |
| superior roofing variant | AA | 1 | 16 | 183 |

**`OpenSides` nearly quadruples the premium** — 32 to 127 — and not through the symbol. The symbol
override fires but resolves to the same `B`; it is the *numeric value* going to 4 that moves it.
**ISO confirms $127.**

**The roof-construction override is not a peer of the class overrides, it is a child of them.** The
algorithms doc lists it as one of four alternatives. It sits inside an outer `Choose` requiring
`OpenSides = Yes` or one of five class codes, so for an ordinary class it is unreachable — even
though `SuperiorRoofingIndicator` correctly derives to `Yes` and the roof table has a row.

**`ConstructionType` has one submittable vocabulary.** The 25 detailed names are what may be sent;
the six bare names are what `ConstructionTypeToUse` *resolves to*. Send a bare one and both coverage
groups price at zero. `Frame` is the only string spelled identically in both, which is the single
reason this chunk's one-building-two-premiums design works.

**And ISO does not return zero there — it rejects the submission** (`400 … Matrix:
ConstructionTypeToUse … No results have been returned`). That difference is open item 8.

---

## The fire-only gate — a clean 2×2

`14_chunk2_fire_only_gate.py`, all eight Standard Property Policy options enumerated from ISO's own
domain table. Two independent dimensions, each hitting a different coverage group:

| | Group II | Group I |
|---|---|---|
| **"Allied Lines" in the name** | decides it — **$0** without, **$31** with | no effect |
| **"Vandalism" in the name** | no effect | `VandalismExclFactor` 0.95 / 1.0 → **$242 / $255** |

Asserted rather than eyeballed: the four options the rule names, the four without Allied Lines, and
the four that zero Group II are the same four. ISO confirms both corners.

---

## What is still owed

1. **Open item 8** — `SingleResult` with zero hits: ISO errors, we return null. Needs its own
   measured pass, because it changes shared code General Liability runs.
2. **Input validation.** Five inputs now price at zero rather than raising: Arizona's
   `BasicGroupIReductionCredit`, an unrecognised `ConstructionType`, an absent `BCEG`, a missing
   `RatingTypeBasicGroupII`, a missing Group II territory. Item 8 is the engine-side half.
3. **TX's wind/hail shape**, untraced.
4. **DC and IL** have no `BCEGFactor` row for their own Group II territory, so Group II may be
   unrateable there. Not diagnosed.
5. **MT, NY, PR** resolve to an empty `BasicGroupIIConstructionSymbol`. NY files 120
   `BasicGroupIIRate` rows, so it clearly rates Group II by some other symbol route.

## What is deliberately not here

No blanket branch (chunk 9, still a stub everywhere). No Legal Liability (chunk 8). No Specific or
Tentative rating. No comparison against `CFRater1.01.xlsb`.
