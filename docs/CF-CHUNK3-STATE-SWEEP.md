# Property chunk 3, task 4 — the 47-jurisdiction sweep

**Gate point 3: every state enumerated, not sampled.** Run 2026-09-18,
`scripts/cf/17_chunk3_enumerate_states.py`.

| | |
|---|---|
| **Broad** | **47 of 47** exact |
| **Special** | **47 of 47** exact |
| Skipped | none |
| Engine code written | none |

Same building in every jurisdiction — Frame, class 0951, limit 100,000,
deductible 1,000, coinsurance 90% — with each premium predicted from that
jurisdiction's own filed rows before the engine ran.

---

## The finding: two jurisdictions rate Special by their own rule

**The first pass skipped FL and PR as "no `SpecialBuildingRate` filed", and
that was wrong.** Both rate Special. Both do it through an overriding rule that
reads a **differently named table**, which a search on the countrywide table
name cannot see — the engine rated Florida at $38 while the prediction said the
state had no rate at all, and that disagreement is what exposed it.

This is gate point 6's same-name-different-table trap appearing in the *state*
layer rather than between forms, and it is the reason the gate asks for a
prediction per jurisdiction instead of a sample.

### Florida — a residential / non-residential split no other state has

`SetSpecialBaseRate` is overridden to choose between
`SpecialBuildingRateNonResidential` and `SpecialBuildingRateResidential` on a
**hardcoded list of 21 class codes written into the rule**:

    0074 0075 0076 0077 0078 0079   0196 0197 0198
    0311 0312 0313   0321 0322 0323   0331 0332 0333   0341 0342 0343

Class 0951 is not among them, so the golden building takes the non-residential
rate of 0.035 → **$38**. The script parses this list out of the filed rule
rather than transcribing it, so it cannot drift from the corpus.

### Puerto Rico — a cause-of-loss domain that does not exist countrywide

PR's rule **never tests the value `"Special"`**. It gates on
`"Special Including Theft"` and `"Special Excluding Theft"`, and reads
`SpecialBldgRate`, which is keyed on **construction type** — a dimension
countrywide Special does not have:

| | Frame / JM / NC / MNC | Modified FR / FR |
|---|---|---|
| Special Including Theft | 0.023 | 0.011 |
| Special Excluding Theft | 0.021 | 0.009 |

So Puerto Rico folds the theft decision into the *selection* where countrywide
applies a 0.88 *factor*. A submission carrying `CauseOfLoss = "Special"` is
off-domain there and prices at zero in silence — which is exactly what the
first pass saw and misread as an absent filing. Rated on PR's own value,
`Special Including Theft` at 0.023 → **$20**, predicted and matched.

PR also files its own `BroadFormBaseRate` (0.011 Frame, against countrywide
0.015) and its own LOI table at 1.0, giving Broad **$9**.

---

## The override census — task 24 answered

Re-asked per chunk, never inherited. **Chunk 3 is the opposite of chunk 2.**

| Rule | States overriding |
|---|---|
| `SetSpecialBaseRate` | **3 of 47** — AL, FL, PR |
| `SetSpecialRate` · `SetBroadRate` | 3 of 47 — AL, KS, RI |
| `SetSpecialCauseOfLossAdjustment` | 3 of 47 — FL, PR, WV |
| `SetAdjustedBroadRate` | 2 of 47 — FL, WV |
| `SetBroadBaseRate` | 1 of 47 — AL |
| `SetFinalBroadRate` · `SetFinalSpecialRate` | 1 of 47 — FL |
| `SetDeductibleFactorBroad` · `SetDeductibleFactorSpecial` | 1 of 47 — FL |
| `SetSpecialTheftExclusionFactor` | 1 of 47 — PR |
| `SetBroadLOIFactor` · `SetSpecialLOIFactor` · `SetAdjustedSpecialRate` | **0 of 47** |

Against chunk 2, where **39 of 47** override `SetBasicGroupIIRate`. The
countrywide chain was the minority behaviour there and is the overwhelming
majority here — which is the whole argument for re-asking rather than
inheriting the answer.

Note that AL, KS and RI override rules and still match a countrywide-shaped
prediction: an override is not automatically a divergence. Only FL and PR
change the arithmetic.

## The table census

| Table | Countrywide | State-filed |
|---|---|---|
| `BroadFormBaseRate` | 46 of 47 | **1** — PR |
| `SpecialBuildingRate` | 2 of 47 | **45** |
| `SpecialBuildersRiskRate` | 46 of 47 | 1 — PR |
| `BroadSpecialLOIFactorBldg` | 46 of 47 | 1 — PR |
| `DeductibleFactor` | 2 of 47 | 45 |
| `CoinsuranceFactor` | 46 of 47 | 1 — FL |

The two jurisdictions falling back to countrywide `SpecialBuildingRate` are FL
and PR — and the header-only countrywide table is why neither finds a row
there. They are the two that override the rule instead.

**The shared LOI table held.** Broad and Special read `BroadSpecialLOIFactorBldg`
in all 47, and the one jurisdiction that files its own (PR, at 1.0) moves both
forms together. A shared table was a question; it is now answered for chunk 3.

## Deferred

`SpecialBuildersRiskRate`'s countrywide 0.015 against `SpecialBuildingRate`'s
header-only row — the two base-rate paths diverging when a state is silent — is
**task 17**, and needs a class-1150 case rather than a sweep.
