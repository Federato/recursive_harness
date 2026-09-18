# Property chunk 3, tasks 17, 19 and 20 — the Special-specific claims

Run 2026-09-18, `scripts/cf/21_chunk3_special_structure.py`. Exit 0, every
figure exact on the first run.

---

## 17 · One header-only table explains two states' rule overrides

Both base-rate paths, priced:

| | Base rate | Source | Coinsurance | Premium |
|---|---|---|---|---|
| class 0951 | 0.047 | `SpecialBuildingRate`, **Oregon's own row** | 0.95 | $54 |
| class 1150 | 0.015 | `SpecialBuildersRiskRate`, **countrywide** | 1.0 | **$18** |

(The coinsurance difference is task 14's finding again — `SetCoinsuranceFactor`
independently hardcodes `1150`.)

Enumerated across every jurisdiction:

| Table | Jurisdictions resolving rows |
|---|---|
| `SpecialBuildingRate` | **45 of 47** |
| `SpecialBuildersRiskRate` | **47 of 47** |

The two missing are FL and PR — **the same two that override
`SetSpecialBaseRate`**. The Builders Risk path needed an override from nobody,
because the countrywide 0.015 is there to fall back on.

So one header-only countrywide table is the entire reason two states file a
rule the other forty-five do not. That is the cleanest available statement of
why "a chunk is not done because the lookup chain resolves" — the chain
resolving in 45 places said nothing about the two where it doesn't.

## 19 · Two sums, and a three-part gate in front of the second

| Case | Deductible factor | Premium |
|---|---|---|
| baseline, no theft deductible | 0.97 | $54 |
| `TheftDeductible` **2,500** (separate) | **0.89** | **$50** |
| `TheftDeductible` **1,000**, equal to `Deductible` | 0.97 | $54 |
| `TheftDeductible` 2,500 **and** CP 10 33 attached | 0.97 | **$47** |

Branch 1 of `SetDeductibleFactorSpecial` keys on
`SpecialIncludingTheftTotAmtInsurance` and uses the **theft** deductible, but
only when all of: the theft exclusion indicator is 0, and `TheftDeductible` is
non-blank, not `"Not Applicable"`, not `"250"`, and **not equal to
`Deductible`**. Each of the last two conditions is a case above.

The fourth case is the interesting one: **excluding theft makes a separate
theft deductible irrelevant.** The 0.88 credit applies instead, and the
deductible reverts to the building one. Two theft-related inputs that look
independent and are not.

**A stated limitation rather than a result:** both sums are written and both
equal the building limit here, because each is `StructureLimitToUse` plus
occupancy and special-class rollups and this submission has neither. They can
only be told *apart* once Contents exists — logged for chunk 4 rather than
faked. What is proven is **which sum each branch reads**, which is the part
that decides the band.

## 20 · The missing guard — and the finding is the reverse of the worry

**Re-entry cannot double-apply.** Running the whole chain twice over one data
tree leaves `SpecialCauseOfLossAdjustment` at 0.047 and the premium at $54. The
rule recomputes from `SpecialRate × theft × roofACV`, none of which is its own
output — and an unguarded rule is only dangerous if it reads what it writes.

**What the missing guard actually changes is the opposite of a risk.**

| Submitted in the payload | Guarded? | Result |
|---|---|---|
| `SpecialCauseOfLossAdjustment = 9.999` | **no** | **overwritten** to 0.047, premium $54 |
| `SpecialBaseRate = 9.999` | yes (`IsNull`) | **honoured**, premium **$11,398** |

Every other rule in the Special chain is `IsNull`-guarded. That guard exists to
stop a rule recomputing a value it already set — but it cannot tell *"already
set by an earlier rule"* from *"arrived in the submission"*. So **a payload can
supply a rate directly and the filed table is never consulted**: `9.999` rides
all the way to an $11,398 premium with nothing raised.

`SetSpecialCauseOfLossAdjustment`, the one rule the task list flagged as
suspicious, is the only step in the chain that **cannot** be overridden that
way. The unguarded rule is the safe one.

### This is a new open item, and it is not the absent-means-zero family

The eight findings so far are all *missing* inputs producing a cheap policy.
This is the mirror image: a **present** input producing whatever premium it
likes, by occupying a derived field before the rule that would have computed
it. It fails *upward* as readily as downward, and no premium comparison against
ISO would catch it — ISO's engine has the same guards and would return the same
$11,398.

The fix is the same input-validation layer already outstanding, but the
requirement is different and needs stating separately: **a submission must not
be allowed to populate a derived field.** Deriving which fields those are is a
schema question the engine currently has no answer to.
