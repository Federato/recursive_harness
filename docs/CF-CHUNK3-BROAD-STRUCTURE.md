# Property chunk 3, tasks 10–14 — the five things Broad does differently

Run 2026-09-18, `scripts/cf/20_chunk3_broad_structure.py`. Exit 0.

**Three predictions were wrong, and each one is a finding.** The task list's
four structural claims all held; what did not hold were three assumptions made
while testing them.

---

## 10 · No cause-of-loss adjustment step — confirmed, enumerated

`SetBroadCauseOfLossAdjustment` is defined in **0 of 47 jurisdictions plus
countrywide**. Nothing substitutes for it either: the datadef is never written,
and `AdjustedBroadRate` equals `r3(r3(r3(rate × roofACV) × coins) × LOI)`
exactly, with no cause-of-loss term anywhere in it.

Special, for contrast, has the step, and it is where Special's theft and
roof-surfacing factors enter.

## 13 · The two-tier base rate — and `ConstructionType` is not what it looks like

Both tiers confirmed: 0.015 → **$16** for Frame, Joisted Masonry,
Non-Combustible and Masonry Non-Combustible; 0.010 → **$12** for Modified Fire
Resistive and Fire Resistive.

**But the first draft of this test priced five of the six at zero**, and read
that as an engine defect. It was not.

`ConstructionType` is **not** the six-name rating list. It is a **25-value
submission domain** that *maps onto* the six, and `"Frame"` is the only one of
the six that is also a valid input:

| Submitted | Resolves to |
|---|---|
| `Frame` | Frame |
| `Joisted Masonry - Reinforced` (+ 3 more variants) | Joisted Masonry |
| `Non-Combustible - Light Steel` (+ 3 more) | Non-Combustible |
| `Masonry Non-Combustible - Reinforced - Light Steel` (+ 7 more) | Masonry Non-Combustible |
| `Modified Fire Resistive - Reinforced Masonry - Light Steel` (+ 3 more) | Modified Fire Resistive |
| `Fire Resistive - Reinforced Masonry - Light Steel` (+ 3 more) | Fire Resistive |

Submitting `"Joisted Masonry"` — **the name the rate table itself is keyed on** —
misses the domain lookup, leaves `ConstructionTypeToUse` null, and prices the
whole Broad chain at **zero with nothing raised**.

That is the **eighth member of the absent-means-zero family**, and the most
plausible-looking one yet. The other seven are missing inputs. This one is a
*present, spelled-correctly, semantically-right* input that happens not to be in
the domain — and the value that fails is exactly what the rate table calls the
row. Chunk 1's Z2 case ("an unrecognised `ConstructionType` prices at zero")
recorded the behaviour; this explains why five of the six rating types are
unreachable from their own names.

> **Correction note, 2026-10-06** (`CF_Algorithm/cf-broad-chains.html`, Building review #5; probes B2j,
> B2 in the Broad notes). Out of date for the engine. Since the C28-05 `SingleResult` rule, submitting
> `"Joisted Masonry"` is **refused** at the `ConstructionTypeToUse` lookup (ME, both editions), not priced
> at zero. Only a **blank** `ConstructionType` still prices Broad (and Group I) at $0 with outcome "rated".

Also worth noting: the fire-resistive tier is a second rounding site.
`r3(0.010 × 0.95)` is 0.010 half-up and 0.009 truncated, which carries through
to **$12 against $11**. Half-up was already proven against ISO in chunk 1; this
is independent corroboration at a different rate.

## 14 · Class 1150 routes to Builders Risk — and quietly removes coinsurance

Confirmed: class `1150` reads the `BldrRisk` rows at a flat **0.012**, the same
for Frame and Fire Resistive. On the `Bldg` rows construction moves the rate
(0.015 vs 0.010); on the `BldrRisk` rows it does not. Same rule, same submission
field, two behaviours.

**The premium is $15, not the $14 the base rate alone predicts.**
`SetCoinsuranceFactor` *also* tests the literal `1150` and returns **1.0**
instead of the 90% factor 0.95.

Two rules, filed in different places, both hardcoding the same class code. So
`ClassCode = 1150` is a Builders Risk switch with **at least two independent
consequences, and finding one does not find the other**. That is a direct
warning for gate point 5's literal census: listing where a literal appears is
not the same as knowing what electing it does.

## 11 · Roof-surfacing ACV — position confirmed, effect nil, one row dead

The **position** claim holds: the factor is applied inside
`SetAdjustedBroadRate`, and `BroadRate` is unchanged by it.

Two things the test did not expect.

**Paragraph B's filed 0.99 is unreachable.** The rule tests
`Applicability != "Paragraph B"` *before* looking anything up, and its `Else`
branch assigns a flat **1.0**. Only `Paragraph A` and `Paragraph A and B` ever
reach the table. The filed `Paragraph B → 0.99` row cannot be produced by any
submission — a gate-point-5 shape (a hardcoded literal making a filed row
unreachable), now found in chunk 3.

**The factor cannot change a Broad building premium anywhere.** Every Broad base
rate filed in the entire corpus absorbs both surviving factors at three
decimals:

| CovType | Base rate | × 0.98 | × 0.99 |
|---|---|---|---|
| Bldg | 0.006 | 0.006 | 0.006 |
| Bldg | 0.010 | 0.010 | 0.010 |
| Bldg | 0.011 | 0.011 | 0.011 |
| Bldg | 0.015 | 0.015 | 0.015 |
| BldrRisk | 0.009 | 0.009 | 0.009 |
| BldrRisk | 0.012 | 0.012 | 0.012 |

**0 of 6 filed rates can move.** A filed endorsement, with a filed factor, that
no Broad building submission can price differently.

**This is magnitude, not the rule boundary** — and saying so matters, because
the obvious reading is that Broad's unusual position for the factor causes it.
It does not. Special applies the identical factor to a rate of 0.047 and moves
`SpecialCauseOfLossAdjustment` 0.047 → 0.046 and the premium **$54 → $52**.
Broad's rates are simply too small for a 1–2% credit to survive rounding to
three decimals.

Logged as a real divergence between what ISO filed and what any submission can
produce — not as a defect in either.

> **Correction note, 2026-10-06** (`CF_Algorithm/cf-broad-chains.html`, Building review #7; probes B4l,
> B4a, B4b, B4n in the Broad notes). "Cannot change a Broad building premium anywhere" holds only at
> LCM 1.0. The factor applies after the LCM, so a higher LCM lifts the rate past the rounding: at LCM 3.0,
> Paragraph A (0.98) prices **$50 against $51** with no roof record (ME, both editions). Paragraph B and a
> blank `PolicyType` give 1.0 ($51). The by-location 0.995 still rounds away at LCM 3.0 (B7locL, $51).

## 12 · Three deductible-by-location rules, one record, no interference

| Rule | Gate | With a plain by-location deductible attached |
|---|---|---|
| `SetDeductibleByLocationFactor` (shared — **Broad reads this**) | any non-blank `Deductible` | **0.995** |
| `SetBGIIDeductibleByLocationFactor` | a **windstorm/hail** by-location deductible | 1.0 |
| `SetSpecialDeductibleByLocationFactor` | a **theft** by-location deductible | 1.0 |

Broad has no rule of its own and takes the shared one; the other two stay at
1.0 because the record carries neither of their triggers. No interference.

The Broad premium does not move — 0.995 is absorbed at three decimals, the same
way the roof factor is. Two filed factors in the same chain, both of which round
away at Broad's rate magnitudes.

---

## What these five tasks changed about the method

Three wrong predictions, all of the same kind: **the test assumed the corpus
worked the obvious way and the corpus did not.** Submitting a rating-type name
as a construction type, expecting a class-code switch to touch one rule,
expecting a filed factor row to be reachable.

None of the three would have been caught by a premium comparison against ISO,
because all three produce numbers ISO also produces. They were caught by
predicting a specific figure and getting a different one.
