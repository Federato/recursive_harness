# Property chunk 7, tasks C7-22 to C7-27 — the cross-form claims

2026-09-18. Script:
[`scripts/cf/56_chunk7_crossform.py`](../scripts/cf/56_chunk7_crossform.py).

---

## C7-22 · Four absences, enumerated across all 47 jurisdictions

| Term | countrywide | states |
|---|---|---|
| `*LOIFactor` | **0** | **0 of 47** |
| `MultiResidentialPropSpecialCreditFactor` | **0** | **0 of 47** |
| `BaseRateAdjustmentFactor` | **0** | **0 of 47** |
| `StdPropPolGroupIFactor` | **0** | **0 of 47** |

Scanned across the main ruleset **and** all four premium files, countrywide
**and** in every jurisdiction's own package.

**Each absence has a different lineage, and the opening census only drew one
comparison.** C7-15 measured them properly: `StdPropPolGroupIFactor` is absent
from *plain Business Income* too, so it is inherited from the Business Income
side rather than dropped from the Special Class side. A single-comparison census
cannot tell those apart.

---

## C7-23 · Forty-six jurisdictions file a table this coverage never reads

| | |
|---|---|
| `BaseRateAdjustmentFactor` countrywide rows | **0 — header-only** |
| Jurisdictions filing their own | **46 of 47** (all but PR) |
| Times named in **this** coverage's rules | **0** |
| Times named in **plain Business Income's** | **19** |

**A filed table is not evidence of a live path.** Forty-six jurisdictions
maintain rows for a factor this group does not have — it belongs to plain
Business Income, which *rebuilds* a rate the Special Class version simply
*copies*, and therefore needs an adjustment factor this one does not.

C7-21 is the same lesson from the opposite direction: a countrywide row filed,
zero state filings, and no consumer here.

---

## C7-24 · The rounding convention, counted rather than read

`SetPremium`, per form, as `rul:Round` / `DecimalPlaces="0"`:

| | Basic I | Basic II | Broad | Special |
|---|---|---|---|---|
| **Special Class Business Income** | **4** / 10 | **4** / 10 | **4** / 10 | **4** / 10 |
| Special Class *(the parent)* | 0 / 12 | 0 / 12 | 0 / 12 | 0 / 12 |
| plain Business Income | 4 / 10 | **0** / 10 | 4 / 10 | 4 / 10 |

**This group follows plain Business Income, not the parent it hangs off.** Four
`rul:Round` wrappers on every form, where Special Class Building has none on
any — which is the algorithms page's "bottom line up front" confirmed on a
dimension the page never measured.

**And plain Business Income is inconsistent with itself.** Its Basic Group II
carries 0 where its other three carry 4. Special Class Business Income
normalises that back to 4 on all four, so **the copy is tidier than the
original.**

C6-27 caught an algorithms page recording exactly this backwards. **Counting is
the only way to know.**

---

## C7-25 · The blanket branch discards the same two inputs

| Field supplied on the record | Comes back as | |
|---|---|---|
| `BlktLimit` | `'1000000'` | kept |
| `BlktBasicGroupIAvgRate` | `'0.05'` | kept |
| `BlktTotalFullValueAmount` | **`'0'`** | **overwritten** |
| `BlktCauseOfLossValue` | **`''`** | **overwritten** |
| **Premium** | **$0** | |

**The same two fields, on a different coverage.** C6-28 found the denominator
and the cause of loss overwritten on the Special Class item; they are
overwritten here too. A caller supplying all four blanket values gets a silent
**$0 twice over**, once at each level.

Chunk 9 now has the same named starting point in two groups.

*(One structural difference worth keeping: this group's blanket branch reads
`PackageModFactor` and `IRPMFactor` from* seven *levels up against chunk 6's
five, because the nesting is one deeper.)*

---

## C7-26 · Five coverages on one submission, none of them moving

| | |
|---|---|
| Building Group I / II | **263 / 32** |
| Contents Group I / II | **223 / 24** |
| Business Income Group I / II | **112 / 13** |
| Special Class Group I / II | **66 / 209** |
| **Special Class Business Income Group I / II** | **39 / 123** |

**Five coverages, four nesting levels, one submission.** Chunk 5 ran this at
three and chunk 6 at four. The two Special Class premiums are the only new
numbers; everything on the Structure side is unchanged, because Special Class is
a **sibling** of the building record rather than a child of it.

---

## C7-27 · The reuse map, checked rather than trusted — and it was right

`CF_Algorithm/Excel_Rater_SpecialClassBusinessIncome_ReuseMap.html` records a
per-value **COPY / SHARE THE TABLE / BUILD OWN / DO NOT PULL IN** verdict.

| | |
|---|---|
| Value-shaped claims extracted | **30** |
| Consistent with the corpus | **21** |
| **Contradicted** | **0** |
| Not decidable by this check | **9** |

**The nine undecidable ones are stated rather than counted as passes.** They are
names the regex lifted out of prose that are not datadefs at all, and a claim
this check cannot reach is not a claim it verified.

### The map was right where chunk 7's own census was wrong

The values it calls COPY, confirmed read from `../../`:

    BasicGroupIRate · BasicGroupIINumericValue · BasicGroupIISymbol
    BasicGroupIIRatingTerr · LossCostMultiplier

**`BasicGroupIINumericValue` is on that list** — the value C7-12's opening census
filtered out of its own enumeration and the golden case had to rediscover by
hand.

A filed artefact was worth checking. Checking it found **our** error rather than
its own, which is the opposite of what C7-27 was written to expect — and the
reason the task existed was chunk 6's experience of a confidently-wrong internal
document. **Both outcomes are worth the same check.**
