# Property chunk 4, task C4-01 — the golden cases

**Contents (Personal Property), all four forms.** Derived 2026-09-18.

**Every number below was read off the filed rows and worked out by hand before
the engine was run.** Where the engine disagrees, the disagreement is the
finding.

---

## The case

The **same Oregon building as chunks 1, 2 and 3**, with contents on it — so
this is chunk 1's case B, which already carried a Personal Property record that
never rated. Now it rates.

| | |
|---|---|
| Building | class 0951, Frame (construction code 1), Protection Class 3, territory Portland, limit 100,000 |
| Group II inputs | symbol B, territory `Entire State`, BCEG 4 |
| Contents | one PP record, limit 100,000, `CovType` "Personal Property" |
| Terms | coinsurance 90%, deductible 1,000, LCM 1.0 |
| Occupancy | category `Offices`, severity `Not Applicable`, Special territory `Multnomah (including entire city of Portland)` |

**Location total = 200,000** (building 100,000 + contents 100,000), which is
what the deductible tables key on — chunk 1's location-total trap, now with a
second coverage actually in the sum.

### The filed rows this case stands on

| Value | Table | Key | Row |
|---|---|---|---|
| 0.548 | `BasicGroupIRate` | OR, 0951, 1, **Not Applicable**, **PersProp** | Building's is 0.498 on the same key with `Building` |
| 0.96 | `ProtectionClassFactor` | CW, 3, 1 | shared with Building |
| 0.499 | `RatingTerritoryGroupIFactor` | OR, Portland | shared |
| 0.898 | `BasicGroupILOIFactorPersProp` | CW, constCode 1, 100,000 | Building's own table gives 1.172 |
| 0.031 | `BasicGroupIIRate` | OR, Entire State, **B**, **PersProp** | Building's is 0.028 |
| 0.96 | `BCEGFactor` | OR, Entire State, grade 4 | shared |
| 0.843 | `BasicGroupIILOIFactorPersProp` | CW, 100,000 | Building's is 1.266 |
| 0.021 | `BroadFormBaseRate` | CW, Frame, **PersProp** | Building's is 0.015 |
| 0.790 | `BroadSpecialLOIFactorPrsnlProp` | CW, 100,000 | Building's is 1.237 |
| 0.153 | `SpecialPrsnlPropRate` | OR, **Offices**, **Not Applicable** | Building's Special is a flat 0.047 with no such key |
| 1.214 | `PrsnlPropTerrMultiplier` | OR, Multnomah | **Building's Special has no territory dimension at all** |
| 0.95 | `CoinsuranceFactor` | CW, 90% | shared |
| 0.99 / 0.98 / 0.98 | `DeductibleFactor` | OR, 1,000, @200,000, per cause of loss | Group I / Group II / Other |

**The PersProp LOI factors are all below 1.0 where Building's are above it.**
0.898 against 1.172, 0.843 against 1.266, 0.790 against 1.237. That is not a
quirk of this limit — it is how the two coverages' limit curves are filed, and
it means a Contents premium is not a scaled Building premium at any limit.

---

## Predictions

| Form | Base | Rate | Adjusted | Final | **Premium** |
|---|---|---|---|---|---|
| Basic Group I | 0.548 | 0.262 | 0.223 | 0.221 | **$221** |
| Basic Group II | 0.031 | 0.030 | 0.024 | 0.024 | **$24** |
| Broad | 0.021 | 0.021 | 0.016 | 0.016 | **$16** |
| Special | 0.153 | 0.186 | 0.140 | 0.137 | **$137** |

And, unchanged from chunk 1 case B and chunk 2:

| Building coverage | Premium |
|---|---|
| Basic Group I | **$263** |
| Basic Group II | **$32** |

**Building must not move.** Contents rating for the first time is exactly the
kind of change that could disturb it — the two coverages share the deductible
key, the coinsurance factor and the protection class — so Building holding at
263/32 is half of what this case proves.

### Basic Group I — 9 steps

    base rate                                                  0.548   [OR, PersProp]
    rate     = r3(r3((0.548 + 0) x 1.0 x FireSafeVault 1.0
                     x ProtClass 0.96) x TerrFactor 0.499)
             = r3(0.526 x 0.499)                             = 0.262
    COL adj  = r3(0.262 - 0) x 1.0 x 1.0 x 1.0                = 0.262
    adjusted = r3(r3(LOI 0.898 x 0.262) x coins 0.95)
             = r3(0.235 x 0.95)                               = 0.223
    final    = r3(r3(0.223 x dedByLoc 1.0) x ded 0.99)        = 0.221
    premium  = 0.221 x 100,000 / 100                          = $221

Three things to watch. **`FireSafeVaultFactor` is 1.0 here and there is no
Building equivalent** — it is 0.5 in a vault and **0.0 when `RatingType` is not
`Class`**, which is C4-14. **There is no `VacantBuildingRate` addend**, which
Building's rate step has. And **the deductible factor is `Copy`d from four
levels up**, not looked up — the algorithms doc flags the exact ancestor as an
open question, so this case resolves it: if 0.99 (the location total of
200,000) appears, the ancestor is the Structure's.

### Basic Group II — 11 steps

    base rate                                                  0.031   [OR, Entire State, B, PersProp]
    rate     = r3(0.031 x 1 x 1 x 1 x 1 x BCEG 0.96)          = 0.030
    COL adj  = r3(0.030 x 1)                                  = 0.030
    adjusted = r3(r3(0.030 x coins 0.95) x LOI 0.843)
             = r3(0.029 x 0.843)                              = 0.024
    final    = r3(r3(0.024 x 1) x ded 0.98)                   = 0.024
    premium  = 0.024 x 1,000                                  = $24

The symbol and territory are **plain `Copy`s from the Structure and Location**,
so this premium existing at all is the evidence for C4-19: a `Copy` from four
and six levels up is exactly the path that silently yields null, and a null
symbol prices Group II at zero.

Note `r3(0.030 x 0.95) = r3(0.0285) = 0.029` — **a half-up tie**. Truncation
gives 0.028 and a $23 premium. Rounding was settled against ISO in chunk 1;
this is a third independent site where the modes disagree.

### Broad — 5 steps, the shortest chain in the project

    LOI      (computed FIRST, unlike Building)                 0.790
    base rate                                                  0.021   [CW, Frame, PersProp]
    rate     = r3(0.021 x 1.0)                                = 0.021
    adjusted = r3(r3(0.790 x 0.021) x coins 0.95)
             = r3(0.017 x 0.95)                               = 0.016
    final    = r3(r3(0.016 x 1.0) x ded 0.98)                 = 0.016
    premium  = 0.016 x 1,000                                  = $16

**$16 is the same figure as Building's Broad**, and that is a coincidence of
two different chains — base 0.021 × LOI 0.790 against base 0.015 × LOI 1.237.
Worth saying out loud so a later reader does not take it for a copied value.

There is **no `SetDeductibleFactorBroad` rule at all** in the PP ruleset:
`SetFinalBroadRate` reads the factor four levels up directly. C4-21 asks what a
null ancestor does; this case only shows the populated path.

### Special — 14 steps, the longest chain in the coverage

    base rate                                                  0.153   [OR, Offices, Not Applicable]
    terr multiplier                                            1.214   [OR, Multnomah]
    rate     = r3(1.214 x (0.153 x 1.0))                      = 0.186
    theft factor (not elected)                                 1.0
    COL adj  = r3(0.186 x 1.0)                                = 0.186
    adjusted = r3(r3(r3(r3(0.186 x coins 0.95) x watchman 1.0)
                     x burglary 1.0) x LOI 0.790)
             = r3(0.177 x 0.790)                              = 0.140
    final    = r3(r3(0.140 x dedByLoc 1.0) x ded 0.98)        = 0.137
    premium  = 0.137 x 1,000                                  = $137

**This is the form that is least like Building's**, and the premium shows it —
$137 against Building's $54 on the same building. Building's Special is a flat
statewide constant; this one is keyed on occupancy category and severity and
then multiplied by a **territory factor of 1.214 that Building's Special has no
equivalent for**.

**One uncertainty, stated rather than hidden.** `DeductibleFactorSpecial` is
the one PP deductible factor computed locally rather than copied, and it keys
on `SpecialTotAmtInsurance`. Whether that sum is 200,000 (the location total,
as the Building side computes it) or 100,000 (the occupancy's own) is not
settled from the schema. **The prediction above assumes 200,000 → 0.98.** If
the engine returns 0.97 the sum is 100,000, the premium is $136, and that is
the answer to half of C4-13 arriving early.

---

## What this case cannot show

* **Two PP records.** One record proves the chain, not the `ForEach`. C4-10.
* **The A/B/C/YARD group letters.** Class 0951 resolves `Group` to
  `Not Applicable` — the letters apply to a documented set of building codes,
  not to this one. C4-15.
* **The two Special sums diverging.** With a single record they may still be
  equal. C4-13.

## Results

`scripts/cf/22_chunk4_golden_case.py`, 2026-09-18. **Exit 0 — all four forms
match and Building is unmoved.** No engine code was written.

| Form | Predicted | Final | **Premium** | |
|---|---|---|---|---|
| Basic Group I | $221 | 0.223 | **$223** | ❌ |
| Basic Group II | $24 | 0.024 | **$24** | ✅ |
| Broad | $16 | 0.016 | **$16** | ✅ |
| Special | $137 | 0.137 | **$137** | ✅ |
| Building Group I | $263 | | **$263** | ✅ unmoved |
| Building Group II | $32 | | **$32** | ✅ unmoved |

Group II landed exactly, including the `r3(0.030 × 0.95) = 0.029` half-up tie.
Building held at 263 / 32 in all three runs, which is half of what the case was
for: Contents and Building share the deductible key, the coinsurance factor and
the protection class, and Contents rating for the first time is exactly the
change that could have disturbed it.

### Five corrections, and each is a finding

**1 · PP's rate step rounds ONCE; Building's rounds at every `Product`.**
Building's Group I goes 0.498 → r3 0.478 → r3 0.239. PP does
`r3(0.548 × 0.96 × 0.499)` in one operation = **0.263**, where per-step
rounding gives 0.262. One dollar on this case, and more wherever the chain is
longer. The two coverages do not share a rounding shape, and nothing in the
algorithms pages said so.

**2 · The adjusted-rate order is coinsurance THEN limit**, not the
`LOI × COLadj × coins` recorded on the algorithms page. `r3(0.263 × 0.95)` =
0.250, `× 0.898` = 0.2245 → **0.225** — another half-up tie. The documented
order gives 0.224 and a $222 premium.

**3 · Each PP form gates on the cause of loss, and it is the PP RECORD's own
field.** `SetCauseOfLossToUse` reads `CauseOfLoss` locally when the item is not
blanketed. Setting it on the building — which is where chunks 1–3 set it —
leaves every Contents form gated shut and pricing at zero. So Contents needs a
submission per form, exactly as chunk 3's Broad and Special did.

**4 · `OccupCategoryRiskSeverity` is DERIVED, not submitted — and the
submission loses silently.** It is looked up from `OccupCategory` plus the
**occupancy class's own `ClassCode`**, and the rule carries no `IsNull` guard,
so a value supplied in the payload is overwritten. With no class code on the
occupancy it is overwritten with **blank**, which gates Special's base rate
shut and prices it at zero.

This is the **mirror of chunk 3's derived-field hole**. There, every
`IsNull`-guarded rule honoured a submitted value and let it bypass the filed
table. Here an unguarded rule discards one. Same ambiguity underneath — the
engine cannot tell "already set by a rule" from "supplied by the submitter" —
and it fails in opposite directions depending on the guard. **Neither direction
raises anything.**

**5 · `SpecialTotAmtInsurance` is the LOCATION total**, the same key Building's
Special uses — 200,000, factor 0.98, premium $137, as first derived. A mid-run
reading of 0.97 came from the *Basic* submission, where the Special sum has not
accrued. **Reading a Special-only datadef out of a run that is not rating
Special is its own trap**, and it briefly produced a "correction" that was
itself wrong.

### What the case showed that was not predicted at all

**The PersProp limit curves run below 1.0 where Building's run above it** —
0.898 against 1.172, 0.843 against 1.266, 0.790 against 1.237. A Contents
premium is not a scaled Building premium at any limit, and a rater that
reuses Building's LOI factor for contents is wrong by 30–60% rather than
slightly.

**Broad's $16 equals Building's Broad $16 by coincidence** — base 0.021 × LOI
0.790 against base 0.015 × LOI 1.237. Recorded so no later reader takes it for
a copied value.

**A new validation message appears:** *"Full Value cannot be lower than the
Limit"*, on all three runs. The PP record carries a limit and no full value.
Gate point 9's population, logged rather than silenced.
