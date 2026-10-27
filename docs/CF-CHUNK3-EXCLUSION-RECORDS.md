# Property chunk 3, task 6 — exclusion records

**Gate point 7: every exclusion's endorsement record identified per datadef
group.** Run 2026-09-18, `scripts/cf/05_exclusion_records.py` (extended) and
`scripts/cf/18_chunk3_theft_exclusion.py` (new).

| | |
|---|---|
| Chunk 3's exclusion | **theft — CP 10 33** |
| Records in the family | **5 distinct, across 7 datadef groups** |
| Ours | `CommercialPropertyTheftExclusion`, a child of the **structure** |
| Priced | $54 → **$47** with the record attached, exact on the first run |
| Broad | **unmoved at $16**, as predicted |

---

## The census was missing theft entirely

Same shape as yesterday's gate-point-6 defect, one day later, in a different
script.

`05_exclusion_records.py` looked for rules matching `Set|Lookup … Excl …
Factor|Rate` and collected the endorsement record each one tests. Vandalism,
sprinkler leakage and wind/hail all test their record *inside* the rule that
computes the factor, so it found them.

**Theft does not.** `SetSpecialTheftExclusionFactor` tests an integer,
`SpecialTheftExclusionIndicator`, and a **separate** rule
(`SetSpecialTheftExclusionIndicator`) sets that integer from the endorsement
record. The factor rule contains no `Exist` at all — so the census reported
theft as if it did not exist, and **gate point 7 would have passed on a census
that omitted the one family chunk 3 actually needed.**

Adding `Indicator` to the pattern fixes it. The lesson is the same one the
shared-names check taught: *a rule that delegates is invisible to a check that
only reads the rule in front of it.* That is now twice in two days, in two
independent instruments.

---

## The theft family, as filed

| Datadef group | Record |
|---|---|
| **`CommercialPropertyStructure`** | **`CommercialPropertyTheftExclusion`** ← ours |
| `CommercialPropertyPersonalProperty` | `CommercialPropertyTheftExclusionPrsnlProp` |
| `CommercialPropertyBusinessIncome` | `CommercialPropertyTheftExclusionBusnIncome` |
| `CommercialPropertySpecialClass` | `CommercialPropertyTheftExclusionSpecialClass` |
| `CommercialPropertySpecialClassBusnIncome` | `CommercialPropertyTheftExclusionSpclClassBusnIncome` |
| `CommercialPropertyCondominiumCommercialUnitOwnersOptionalCoverages` | `…TheftExclusionPrsnlProp` (reuses the contents record) |
| `CommercialPropertyValueReportingFormGeneralInformation` | `…TheftExclusionPrsnlProp` (same) |

Seven groups, five records: two groups reuse the Personal Property record
rather than filing their own.

## Priced, not just enumerated

A census says which record a rule *tests*. It cannot say the election reaches
the premium. `18_chunk3_theft_exclusion.py` does:

| | Indicator | Factor | Special | Broad |
|---|---|---|---|---|
| no election | 0 | 1.0 | $54 | $16 |
| `CommercialPropertyTheftExclusion` attached | 1 | **0.88** | **$47** | $16 |

Derived by hand first — `r3(r3(0.047 × 0.88) × 1.0) = 0.041`, adjusted
`r3(r3(0.041 × 0.95) × 1.237) = 0.048`, final `r3(0.048 × 0.97) = 0.047`,
premium **$47** — and exact on the first run.

**The record hangs off the structure, not the policy.** A single policy-wide
"theft excluded?" control would attach it in the wrong place, price at $54, and
raise nothing at all. That is the failure gate point 7 exists to make visible.

**Broad does not move**, as predicted: it has no theft dimension, its
deductible rule is the four-way `Choose` without one. The two forms share an
LOI table and not this.

---

## The finding: not every exclusion is per-coverage

Gate point 7 is written on the premise that Property files one exclusion record
*per coverage*, so a single control feeding every coverage is a simplification.
That is true of theft (5 records), vandalism (5 records across 13 groups),
wind/hail (5 across 19) and sprinkler leakage (3 across 7).

**Cyber Incident Exclusion is the opposite.** One record, one datadef group —
and that group is `CommercialProperty`, the **policy**. From that single
election, ten coverage-specific factor rules read a factor:
`…FactorBGI`, `…FactorBGII`, `…FactorBroad`, `…FactorSpecial`, `…FactorEQ`,
`…FactorFlood`, `…FactorSpoilage`, `…FactorEquipmentBreakdown`,
`…FactorMortgageholdersErrorsAndOmissions`. Its sibling family,
`CyberIncidentExclusionWithEnsuingCausesOfLossExceptions`, has 23 such rules.

So for cyber, a **single policy-level control is what ISO filed** — and
building a per-coverage one would be the divergence. Both shapes exist, and
which is which has to be read off the corpus per family rather than assumed
from the gate's wording. Chunk 3's own premium branch multiplies by
`CyberIncidentExclusionFactorBroad` and
`CyberIncidentExclusionCOLExcptnsFactorBroad`, both 1.0 here because nothing is
elected.

## Also counted, and deferred to gate point 9

**59 `DoMessage` rules test an exclusion record**, across 21 families — theft
has 6, vandalism 5, sprinkler leakage 4, wind/hail 2. Those validate rather
than rate, which is why they are counted separately. They are the reason an
exclusion can be elected correctly and the submission still come back with an
error, and they are gate point 9's population when that point is finally done
for chunks 1, 2 and 3.
