# Property chunk 2 — the golden case

**Written 2026-09-17**, before any chunk 2 code ran. Building, **Basic Group II**, class-rated,
scheduled — Oregon.

Built **differentially against chunk 1**: the same Oregon building, with the three inputs Group II
needs that Group I does not. So one submission produces two premiums, and chunk 2 re-proves chunk 1
rather than replacing it.

Companions: [`CF-CHUNK1-GOLDEN-CASE.md`](CF-CHUNK1-GOLDEN-CASE.md),
[`CF-CHUNK1-GATE.md`](CF-CHUNK1-GATE.md).

---

## 1 · What Group II is, and is not

Group I is rated off **class code + construction code**. Group II is rated off **rating territory +
construction symbol** — a different key entirely, from a different table, with its own territory
field. It is an 11-step chain against Group I's 8.

Shared with Group I, and so already proved: the coinsurance factor (copied outright when coinsurance
is 80/90/100%), the deductible table, the cyber factors, the premium branch, and the rounding.

**Group II-only machinery**, none of which chunk 1 touched:

| | |
|---|---|
| `BasicGroupIISymbol` | from `ConstructionType` + `NumStories`, then up to four class-specific overrides |
| `BasicGroupIIRatingTerr` | its **own** territory field, separate from Group I's, and a **lookup key** rather than a multiplier — there is no Group II territory *factor* |
| `BasicGroupIINumericValue` | Group II's analogue of the protection-class factor: occupancy/open-sides hazard |
| `BCEGFactor` | Building Code Effectiveness Grading |
| `LimitationsOnCovForRoofSurfacingCosmeticExclFactor` | a wind/hail concept, absent from Group I |
| `LowestBasicGroupIIRate` | a second, parallel rate path used **only** when wind/hail is excluded |
| `BGIIDeductibleByLocationFactor` | its own datadef, because the wind/hail deductible can differ from the all-other-perils one on the same building |

Group II has **no** substandard-condition or vacant-building addend, and no territory multiplier.

---

## 2 · The state-only tables — the reason this chunk exists

Enumerated across all 47 jurisdictions, confirming the build order exactly:

| Table | Countrywide | Resolves non-empty in |
|---|---|---|
| `BasicGroupIIRate` | **0 rows** | 45 of 47 — **not FL, not PR** |
| `LowestBasicGroupIIRate` | **0 rows** | 39 of 47 — not AR, DC, FL, KS, NY, PR, RI, TX |
| `WindstormOrHailExclFactor` | 4 rows | 39 of 47 — **the same 8 states** |

**The two tables the wind/hail branch depends on are missing in exactly the same 8 states**, which
the algorithms doc had already spotted. What is new here is that **they are missing by two different
mechanisms**, and the difference is the whole point of N3:

* `WindstormOrHailExclFactor` — those 8 states file the table themselves **with zero rows**. That is
  an *explicit empty override* of countrywide's 4 rows, and an empty state override means **"not
  offered here"**, not "look upstairs". ISO is switching the coverage off.
* `LowestBasicGroupIIRate` — those states simply never file it, and inherit a header-only
  countrywide table.

So it is not a coincidence and not an omission: the exclusion is deliberately unavailable, and the
rate path that only the exclusion uses was never filed because nothing would read it. Chunk 2 must
treat those 8 states as *wind/hail-exclusion ineligible* rather than as a data gap.

**Oregon files both**, which is why the golden case stays in Oregon.

---

## 3 · A correction to chunk 1's golden case

Chunk 1 set `CauseOfLoss = "Basic Group I"`. **That value is not in ISO's domain.** The filed options
for a Commercial Property Policy building are `Basic`, `Broad`, `Special` — and
`Blanket Cause of Loss Applies` when blanketed (`DomainCauseOfLossByPolicyOptionalForms`).

It did no harm: the only gate is that the value be non-blank and not `"Not Applicable"`, Group I's
rate chain never reads it, and the cyber lookup keys on a hardcoded `"Basic Group I"` constant rather
than this field. ISO accepted the submission and returned $261, matching. But it is an off-domain
value in a golden case, and chunk 2 uses the filed one.

**Why Group II priced at zero in chunk 1 and does not here:** not the cause of loss —
`BasicGroupIIRatingTerr` was never supplied, so the base rate gate failed and the rate was `0.0`.
Another instance of gate point 4's "absent means zero, silently".

---

## 4 · The case

Identical to chunk 1's case A, plus three inputs.

| Field | Value | Note |
|---|---|---|
| *(everything from chunk 1 case A)* | | class 0951, Frame, Portland, protection class 3, 90%, limit 100,000, deductible 1,000 |
| **`CauseOfLoss`** | `Basic` | the filed domain value, replacing `"Basic Group I"` |
| **`BasicGroupIIRatingTerr`** (Location) | `Entire State` | Group II's own territory field. Oregon files one territory for Group II and three for Group I — the two schemes are unrelated |
| **`NumStories`** | `1-3` | with `ConstructionType = Frame`, resolves symbol **`B`** |
| **`BCEG`** | `4` | chosen so the factor is **0.96**, not 1.0 — a failed lookup has to be visible |

---

## 5 · The derivation

Rules from `CommercialPropertyStructureRules.Rule.xml`, countrywide.

| Step | Rule | Source | Value |
|---|---|---|---|
| Symbol | `LookupBasicGroupIIConstructionSymbol` | `BasicGroupIIConstructionSymbol` **[CW]** `"CW","Frame","1-3"` | **B** |
| 1 · Numeric value | `SetBasicGroupIINumericValue` (8272) | class 0951 not in the five-code list; `OpenSides` not `Yes` | **1.0** |
| 2 · Base rate | `SetBasicGroupIIBaseRate` (8347) | `BasicGroupIIRate` **[OR]** `"OR","Entire State","B","Bldg"` | **0.028** |
| 3 · Lowest base rate | `SetLowestBasicGroupIIBaseRate` (8397) | `LowestBasicGroupIIRate` **[OR]** `"OR","B","Bldg"` | 0.028, **unused** |
| — · BCEG | `LookupBCEGFactor` | `BCEGFactor` **[OR]** `"OR","Entire State","4"` | **0.96** |
| 4 · Rate | `SetBasicGroupIIRate` (8441) | — | **0.027** |
| 5 · COL adjustment | `SetBasicGroupIICauseOfLossAdjustment` (8472) | × `StdPropPolGroupIIFactor` = 1.0 (not an SPP) | **0.027** |
| 6 · Coinsurance | `SetBasicGroupIICoinsuranceFactor` (8540) | 90% ⇒ **copy Group I's** factor | **0.95** |
| 7 · LOI | `SetBasicGroupIILOIFactor` (8596) | `BasicGroupIILOIFactorBldg` **[CW]** band `[100000,125000)` | **1.266** |
| 8 · Adjusted rate | `SetAdjustedBasicGroupIIRate` (8787) | — | **0.033** |
| 9 · Deductible by location | `SetBGIIDeductibleByLocationFactor` (8809) | no wind/hail deductible record | **1.0** |
| 10 · Deductible | `SetDeductibleFactorBasicGroupII` (8864) | `DeductibleFactor` **[OR]** `"OR","1,000",…,"Basic Group II"` | **0.98** |
| 11 · Final rate | `SetFinalBasicGroupIIRate` (9040) | — | **0.032** |
| Premium | Branch A | × cyber 0.995 × 1.0 | **$32** |

### The arithmetic, and the difference from Group I

**Step 4's nesting is not step 2 of Group I's.** Group I multiplies territory and protection class
in a *single* `Product` with three children, so they round together. Group II is a **five-deep
left-fold, rounding to 3 dp after every single factor**:

```
r3(0.028 × 1.0)   = 0.028     base × LCM
r3(0.028 × 1.0)   = 0.028     × numeric value
r3(0.028 × 1.0)   = 0.028     × roof surfacing ACV
r3(0.028 × 1.0)   = 0.028     × roof surfacing cosmetic exclusion
r3(0.028 × 0.96)  = 0.027     × BCEG            <-- the only factor that moves it
step 5   r3(0.027 × 1.0)                        = 0.027
step 8   r3(r3(0.027 × 0.95) × 1.266)
         r3(0.02565) = 0.026 ; r3(0.032916)     = 0.033
step 11  r3(r3(0.033 × 1.0) × 0.98 × 1.0)       = 0.032
premium  round(1 × 1 × 1 × 0.032 × 1000, 0)     = 32
         round(32 × 0.995, 0) × 1.0             = 32
```

**Expected: Group II $32, and Group I unchanged at $261, from one submission.**

Group I's premium must not move: its chain never reads `CauseOfLoss`, and the three new inputs are
Group II's alone. If it moves, the two chains are coupled somewhere neither document says they are —
which is itself the most valuable thing this case could find.

---

## 6 · What this case deliberately does not test

- **The wind/hail-excluded branch** — the second rate path, `WindstormOrHailExclFactor`, and the
  documented dropping of the class hazard load. It needs its own case, and it is ineligible in 8
  states.
- **The class-specific symbol overrides** — `LookupBGIISymbolAdditionalClassesRoofConstruction`,
  the 0580/0585 classes, oil distributing stations. Class 0951 reaches none of them.
- **`BasicGroupIINumericValue` doing anything** — it is 1.0 here. The five-code list
  (0580, 0585, 1150, 1300, 1650) and the open-sides branch are untested.
- **The fire-only cause-of-loss gate**, which zeroes Group II entirely on four of a Standard
  Property Policy's eight options.
- **A separate wind/hail deductible**, which is the whole reason `BGIIDeductibleByLocationFactor`
  exists as its own datadef.

Each is a case in chunk 2's own gate, not a silence to be discovered later.
