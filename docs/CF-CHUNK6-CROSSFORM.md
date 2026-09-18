# Property chunk 6, tasks C6-24 to C6-29 — the cross-form claims

2026-09-18. Script:
[`scripts/cf/48_chunk6_crossform.py`](../scripts/cf/48_chunk6_crossform.py).

---

## C6-24 / C6-25 · Two absences, enumerated rather than asserted

A negative claim has to state what was searched. Both were scanned across the
`CommercialPropertySpecialClassRules` file **and** all four premium files,
countrywide **and** in every one of the 47 jurisdictions' own packages.

| | Special Class files naming it | Building files naming it |
|---|---|---|
| A limit-of-insurance factor (`*LOIFactor`) | **0 countrywide, 0 across 47** | 1 of 5 |
| `MultiResidentialPropSpecialCreditFactor` | **0 countrywide, 0 across 47** | 1 of 5 |

**Special Class multiplies the final rate by `Limit / 100` with nothing standing
in between.** Building applies an LOI factor in every form's rate chain, and
Contents applies one whose curves run *below* 1.0 — so nothing about limit
banding carries over from chunks 1–4.

The multi-residential credit is the same shape: Building multiplies it into
every form's **final** rate; scheduled Special Class property does not get it at
all.

---

## C6-26 · Basic Group I and II are not gated on the cause of loss

| Premium file | `SetCoverageOnPolicyIndicator` has a `Test` |
|---|---|
| Basic Group I | **no — hard-coded to 1** |
| Basic Group II | **no — hard-coded to 1** |
| Broad | yes |
| Special | yes |

| Submission | Basic Group I | Basic Group II |
|---|---|---|
| `CauseOfLoss = Basic` | $66 | $209 |
| `CauseOfLoss = Broad` | **$66** | **$209** |
| `CauseOfLoss = Special` | **$66** | **$209** |

**Three chunks established that each form gates on the cause of loss. Here half
of it is false.** ISO confirmed it independently in C6-08: the Broad call's
total was **$289** — the Basic pair's $275 *plus* Broad's $14 — and the Special
call's was $319 on the same arithmetic.

This is exactly the kind of inherited assumption that survives a chunk because
nobody re-asks it.

---

## C6-27 · The rounding convention — and the algorithms page had it backwards

| File | `rul:Round` | `Product DecimalPlaces="0"` |
|---|---|---|
| Special Class — Basic Group I | **0** | 12 |
| Special Class — Basic Group II | **0** | 12 |
| Special Class — Broad | **0** | 12 |
| Special Class — Special | **0** | 12 |
| Building — Basic Group I | **6** | 17 |
| Building — Basic Group II | **6** | 17 |
| Building — Broad | **6** | 17 |
| Building — Special | **0** | 17 |

**The algorithms page said Special Class uses "the standard nested `Round`" and
does *not* carry Building's Special-form quirk. It is the other way round.**

All four Special Class premium files are nested `Product DecimalPlaces="0"` with
**zero `rul:Round` wrappers** — Building's *Special-form* convention, applied to
every form. What is actually Building-specific is the Basic/Broad use of
`rul:Round`, which Special Class does not share anywhere.

The earlier reading counted the `Product DecimalPlaces="0"` nests and called
them "nested Round". **Corrected on the algorithms page** in all six places it
appeared.

### And the shape matters more than the name

The premium **rounds to 0 decimal places at six nested levels**:

    round(round(round(round(round(round(Limit/100 x FinalRate)
        x PackageModFactor) x MultiPremiumAndDispersionCreditFactor)
        x IRPMFactor) x CyberIncidentExclusionFactor) x CyberExclCOLExcptnsFactor)

So **every factor after the first multiplies an already-rounded dollar figure**,
and the two cyber factors are *inside* the nest, not outside it as the page also
claimed. All five are read from the **policy** record — five levels up — through
`FromConstant="0.0"`, so a policy that omits them prices at zero.

---

## C6-28 · The blanket branch — run for the first time in the project, and it cannot be priced from the item

| | Basic Group I | Basic Group II |
|---|---|---|
| `IncludedInBlkt = No` (scheduled) | **$66** | **$209** |
| `IncludedInBlkt = Yes` (blanket) | **$0** | **$0** |

**Predicted $100 and got $0 — and the reason is the finding.**

The branch *is* taken: the same item, the same rate chain, a different premium
formula. The proof that it is the blanket arm rather than a gate is that
`FinalBasicGroupIRate` is still **0.066** on the blanketed item — computed in
full and **never read**.

### Two of the four blanket inputs are discarded

| Field supplied on the item | Comes back as | |
|---|---|---|
| `BlktLimit` = 1,000,000 | `'1000000'` | kept |
| `BlktBasicGroupIAvgRate` = 0.05 | `'0.05'` | kept |
| `BlktTotalFullValueAmount` = 500,000 | **`'0'`** | **overwritten** |
| `BlktCauseOfLossValue` = "Basic" | **`''`** | **overwritten** |

`SetNonEQBlanketValues` writes the denominator and the cause of loss from
blanket records at the **policy** level. **The two fields it overwrites are
exactly the two the formula cannot do without** — so a caller who supplies all
four blanket values on the item gets a silent **$0**, with half its inputs
discarded and no message.

That is the **sixth derived-field trap in this chunk**, and the first that
discards *half a submitted formula* rather than a single value.

**Chunks 1–5 only ever ran scheduled items.** Every premium file in the project
carries this branch and none had executed it until now. Pricing it is chunk 9's
job — and chunk 9 now has a named starting point: `SetNonEQBlanketValues`.

---

## C6-29 · Four coverages on one submission, none of them moving

| | |
|---|---|
| Building Group I / II | **263 / 32** |
| Contents Group I / II | **223 / 24** |
| Business Income Group I / II | **112 / 13** |
| **Special Class Group I / II** | **66 / 209** |

Every figure unchanged from its own chunk.

**Special Class is a sibling of the Structure, not a child of it**, so its
100,000 limit never reaches Building's `TotAmtInsurance` — the location total
that drives three other coverages' deductible band is unchanged, and the only
new number on the submission is Special Class's own.

This is the cross-coverage isolation check at **four coverages**. Chunk 5 ran it
at three.
