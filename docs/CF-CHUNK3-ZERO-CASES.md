# Property chunk 3, task 3 — zero cases

**Gate point 4: every `0` tested against its consuming branch.** Opened 2026-09-18.

**The predictions below were written before the script ran.** Where the engine
disagrees, the disagreement is recorded as the finding rather than edited away.

---

## The zeros Broad and Special actually file

Read off the rules, not off a run. Four distinct sites, and they do **not** all
behave the same way — which is the point of the exercise.

| Site | Rule | What it does when it misses |
|---|---|---|
| Broad base rate | `SetBroadBaseRate` (9073) | gate is `CauseOfLossToUse = "Broad"` **and** `ConstructionTypeToUse` non-blank → else **`0.0`** |
| Special base rate | `SetSpecialBaseRate` (9611) | gate is `CauseOfLossToUse = "Special"` → else **`0.0`**. No construction dependency |
| LOI factor, both forms | `SetBroadLOIFactor` (9178) · `SetSpecialLOIFactor` (9713) | branch 3 yields **`0.0`** when `Limit` is absent. One shared matrix, `BroadSpecialLOIFactorBldg` |
| Broad deductible | `SetDeductibleFactorBroad` (9398) | `Otherwise` → **`0.0`**. A blank `Deductible` zeroes the Broad rate entirely |
| Special deductible | `SetDeductibleFactorSpecial` (9977) | **there is no `Otherwise` branch.** Four conditions, none of which a blank `Deductible` satisfies |

That last row is the one to watch. **The same mutation should fail two different
ways**: Broad writes a `0.0` and prices at zero; Special writes nothing at all,
so `DeductibleFactorSpecial` stays null, `SetFinalSpecialRate` multiplies by
null, and under `propagate` the premium is null — which the null-premium guard
should refuse rather than store.

---

## The cases

Same Oregon building as chunks 1, 2 and 3's golden cases — Frame, class 0951,
limit 100,000, deductible 1,000, coinsurance 90%, LCM 1.0. One submission per
form, as chunk 3 requires, and **every case reports all four coverages** so that
a chain moving when it should not is visible.

Baseline: Broad **$16**, Special **$54**, Basic Group I **$261**, Group II **$32**.

### Predictions

| Case | Mutation | Broad | Special | Group I | Group II |
|---|---|---|---|---|---|
| baseline | — | 16 | 54 | 261 | 32 |
| **Z1** | `ConstructionType` removed | **0** | **54** | **0** | **0** |
| **Z2** | `Deductible` removed | **0** | **null** | 0 | 0 |
| **Z3** | `Limit` removed | **0** | **0** | 0 | 0 |
| **Z4** | `CauseOfLoss` = `Basic` | **0** | **0** | 261 | 32 |

### Why each number

**Z1 — a blank construction type kills three chains and leaves Special
untouched.** Broad's base-rate gate names `ConstructionTypeToUse` explicitly;
Group I looks its base rate up by construction; Group II derives its symbol from
construction plus stories. Special's base rate is a flat statewide constant with
no class, construction, territory or symbol — so it is the one form that should
still price. If Special moves, the "flat constant" reading is wrong.

**Z2 — the same mutation, two failure shapes.** Broad's `Otherwise` yields
`0.0`, so it prices at zero *with a healthy-looking base rate of 0.015 and an
adjusted rate of 0.017 above it* — the chunk-2 BCEG shape again. Special has no
`Otherwise`, so the factor is never written and the premium should be null, not
zero. Group I and Group II are predicted to zero as well, on the assumption
their deductible rules behave like Broad's; if either survives, its rule has a
fall-through Broad does not and that is worth knowing.

**Z3 — compound, and stated as such.** An absent `Limit` zeroes the LOI factor
by branch 3 *and* removes the premium's own exposure base (`Limit / 100 × final
rate`). Two mechanisms, one observable zero — so this case proves the LOI branch
only in combination. It is included because gate point 4 asks for every filed
`0` against its consuming branch, not because it isolates one.

**Z4 — the control.** Both base-rate gates test the cause of loss, so selecting
`Basic` must leave Broad and Special at zero while Basic Group I and II price
normally. ISO already confirmed this shape in task 23; it is here so that a
regression in the gate shows up in this script rather than in the sweep.

### Deferred, deliberately

**FL and PR file no `SpecialBuildingRate` row** — the countrywide table is
header-only, so Special's base rate has no row to find. That is a genuine zero
and it belongs to this gate point, but it needs a different jurisdiction's book
and so is carried to task 4 (the 47-state sweep) and task 16, not forced into an
Oregon script.

**`SpecialBuildersRiskRate` does carry a countrywide row (0.015)**, so the two
base-rate paths diverge when a state is silent. Task 17.

---

## Results

`scripts/cf/16_chunk3_zero_cases.py`, run 2026-09-18. **Three of five cases
matched the prediction; two did not, and both disagreements are the value.**

| Case | Predicted | Actual | |
|---|---|---|---|
| baseline | 16 / 54 / 261 / 32 | 16 / 54 / 261 / 32 | ✅ |
| Z1 construction removed | Broad 0, **Special 54**, GI 0, GII 0 | as predicted | ✅ |
| Z2 deductible removed | Broad 0, **Special null** | Broad 0, **Special 0** | ❌ |
| Z3 limit removed | both 0 | both **RAISE** | ❌ |
| Z4 cause of loss Basic | 0 / 0 / 261 / 32 | as predicted | ✅ |

### Z1 held — Special's base rate really is flat

One mutation, three chains down and one standing. Removing `ConstructionType`
zeroes Broad (its gate names it), Group I (it looks its base rate up by
construction) and Group II (it derives its symbol from construction plus
stories) — and leaves Special at **$54**, untouched. That is the strongest
single statement available that Special's base rate carries no class,
construction, territory or symbol dimension.

### Z2 — the prediction was wrong, and the source was a document

Special was predicted to leave `DeductibleFactorSpecial` null and have the
premium refused, because `CauseOfLoss_Building_RatingAlgorithms.md` documents
four branches and says in as many words that Special's fall-through "behaves
differently" from Broad's. **The filed XML has an `<rul:Otherwise>` assigning
`0.0`, identical in shape to Broad's.** Both forms price at zero.

Two errors on that page, both now corrected there:

1. the missing `Otherwise` branch;
2. branch 2's test written as an `And` where the filed rule is an **`Or`**
   (`Deductible = "250"` **or** `TheftDeductible = "250"`).

**The engine was right and the derivation was wrong** — the first time in the
project that the disagreement has resolved that way. Worth noting what that
does and does not mean: the method still worked. The prediction was written
from a document, the document was wrong, and asking the question is what
exposed it. A finding against the corpus and a finding against our own notes
are equally useful; only one of them is a rating defect.

What survives is the shape that matters, and it is the chunk-2 BCEG shape
again: **both forms price at zero underneath a perfectly healthy base rate**
(0.015 and 0.047) and adjusted rate (0.017 and 0.056). Nothing in the chain
above the deductible looks wrong.

### Z3 — an absent limit is the one input that is LOUD

Predicted to price at zero through the LOI branch. It does not: the
null-premium guard **raises**, on both forms —

    Product wrote a NULL to 'Premium'. A premium is money: absent is not zero.

The prediction read branch 3 of the LOI rules and stopped there. The premium's
own exposure base is `Limit / 100 × final rate`, so an absent limit makes the
premium *itself* null rather than making a factor zero, and the guard catches
nulls.

**This is the distinguishing line in the whole "absent means zero" family.**
Seven missing inputs are now known across chunks 1–3:

| Missing input | Behaviour |
|---|---|
| Arizona's `BasicGroupIReductionCredit` | silent zero |
| an unrecognised `ConstructionType` | silent zero |
| an absent `BCEG` | silent zero |
| a missing `RatingTypeBasicGroupII` | silent zero |
| a missing Group II territory | silent zero |
| a blank `Deductible` (Broad **and** Special) | silent zero |
| **a missing `Limit`** | **raises** |

Six of seven are silent. The one that raises does so because it reaches the
premium as a null instead of as a factor of zero — which is an argument *for*
the input-validation layer, not against it. The guard already catches
everything that arrives as a null; the problem is that ISO's rules convert
missing inputs into zeros long before they could become one.

### Gate point 4 for chunk 3

**Satisfied.** Every `0` the Broad and Special chains can produce has been run
against its consuming branch, with the two state-dependent zeros (FL/PR's
absent `SpecialBuildingRate`, and `SpecialBuildersRiskRate`'s countrywide
0.015) carried to tasks 4, 16 and 17 where a second jurisdiction's book is
available.
