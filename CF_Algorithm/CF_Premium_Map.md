# CF premium map — every premium field, what feeds it, where it ends up

**The question this answers:** for Commercial Property, where does every premium number come
from, and how does it reach the one figure that is the account's premium?

**The answer in one line:**
`CommercialProperty.ErcCalculatedTotalPremium` is the account total, and **every one of the
881 groups that carry a premium reaches it** — through as many as **seven** levels of summation.

**Source:** `CFCW20260601V01`, countrywide, 882 rule files, plus the latest package of all 47
states for the jurisdiction analysis.

**Navigable version:** `CF_Algorithm/CF_Premium_Tree.html` — collapsible, searchable, with a
jurisdiction selector.
**Companion data:** `CF_Algorithm/CF_Premium_Map.xlsx` — `Summary`, `RollUpTree` (881 rows),
`PremiumSources` (546 rows), `PremiumFields` (212 rows).

**Companion for GL:** `GL_Algorithm/GL_Premium_Map.md`. The two lines share a mechanism and
almost nothing else; the differences are the point of this document.

**Written:** 2026-09-17.

---

## 1. The same three mechanisms, at twice the scale

| Rule | CF | GL |
|---|---|---|
| `SetPremium` — rate into dollars on one record | **546** | 322 |
| `SetPremiumIndicator` — did this record produce a premium | **546** | 322 |
| `CalculateTotalPremium` — collect upward one level | **881** | 571 |

Identical architecture. A leaf contributes its `Premium` only when `PremiumIndicator = 1`
**and** `Premium ≠ 0`; an aggregator sums its children into `ErcCalculatedTotalPremium`;
children are reached by `ForEach` over an `<X>Table` when repeating and by `Locate` when
singleton. Nothing about the mechanism is CF-specific.

**`ErcCalculatedTotalPremium` is written 261 times across the corpus and read zero times** —
exactly as in GL. Every stored subtotal is an output for the caller, never an input to the
level above.

---

## 2. Where CF and GL genuinely differ: the shape

**GL is wide and shallow. CF is deep and narrow.**

| Depth below the account total | CF groups | GL groups |
|---|---|---|
| 0 — the account | 1 | 1 |
| 1 | 45 | **419** |
| 2 | 23 | 110 |
| 3 | 167 | 34 |
| 4 | **304** | 7 |
| 5 | 230 | — |
| 6 | 79 | — |
| 7 | 32 | — |

GL puts 419 of 571 groups directly on the policy — endorsements that price at policy level.
**CF puts only 45 there and pushes the mass to depths 4 and 5**, because Property's premium
follows the property: policy → location → building → occupancy class → contents, and
endorsements attach to whichever of those they modify rather than to the policy.

The practical consequence: **a CF premium can be seven summations away from the account
total.** Anything that walks this tree — a UI, a reconciliation, a trace — has to handle
depth it will never see in GL.

---

## 3. CF computes far more premium concepts

**212 distinct premium-named fields are declared; 69 are written by a rule** — against GL's
163 declared and 22 written. CF does three times as much premium arithmetic.

| Field | Writes | What it is |
|---|---|---|
| `Premium` | 1,355 | the record's own premium |
| `PremiumIndicator` | 1,092 | did it produce one |
| `ErcCalculatedTotalPremium` | 130 | a subtotal at each aggregating level |
| `TerrorismPremium` | 30 | |
| `RelatedExpensesPremium` | 18 | |
| `GreenUpgradesPremium` | 18 | |
| `PreTRIAPremium` / `PostTRIAPremium` | 15 each | the TRIA split |
| `AnnualPremiumOfPrecedingReportingPeriod` | 10 | **see §4** |
| `FormAnnualPremium` | 10 | **see §4** |
| `TotalAgreedValuePremium` | 5 | |
| …58 more | 1–9 each | coverage-specific totals |

---

## 4. Interim premium — and where CF differs from GL

For GL the finding was blunt: a fourteen-field pro-rata / written / earned / endorsement block
sits on every record and **nothing reads or writes any of it**, in any of 52 jurisdictions
(`OI-98`). CF was measured the same way, across all **48** jurisdictions, and the answer is
*nearly* the same — with three real exceptions that are worth understanding.

### Still completely inert in CF

| Field | Writes | Reads |
|---|---|---|
| `AnnualPremium` · `PolicyTermPremium` · `PriorPremium` | 0 | 0 |
| `ProRatedPremium` · `ProRatedPriorPremium` · `ProRatedChangePremium` · `TotalProRatedChangePremium` | 0 | 0 |
| `ChangePremium` · `EvaluatedPremium` · `OverridePremium` | 0 | 0 |
| `TermFactorIndicator` · `EarnedInFullIndicator` | 0 | 0 |

**The policy-level administration block is as dead in CF as in GL.** No mid-term endorsement
pricing, no written-vs-earned split, no cancellation return arithmetic.

### But three mechanisms *are* live

Unlike GL, CF files genuine term arithmetic — in exactly the places where a coverage is
**intrinsically part-term or intrinsically reported**:

| Field | Writes / reads | Where | Why it exists |
|---|---|---|---|
| `ProRateFactor` | 4 / 4 | `SetVacancyPermitProRateFactor` on `CommercialPropertyVacancyPermitPrsnlProp` | a Vacancy Permit covers part of a term by definition |
| `ProRateIndicator` | 19 / 19 | `SetProRateIndicator` on `CommercialPropertyPeakSeasonLimitOfInsuranceDetail` | a Peak Season limit applies for part of the year by definition |
| `FormAnnualPremium`, `AnnualPremiumOfPrecedingReportingPeriod` | 10 / 25, 10 / 20 | `CommercialPropertyBuildersRiskPremiumAdjustmentForm` (CW, and FL files its own) | a reporting form adjusts against the prior reporting period |

**This refines OI-98 rather than contradicting it.** ISO still does not administer a policy —
there is no general proration engine, no transaction model, no earned/written split. What it
does file is **coverage-intrinsic term arithmetic**: where the *coverage itself* is defined as
partial-term or as a reporting form, the proration is part of the rating content because it is
part of the rate.

The line to hold: **proration belongs to ISO when it is part of what the coverage *is*, and to
the policy system when it is a consequence of *when the transaction happened*.** CF has the
first. Neither line has the second.

---

## 5. What the state packages do — and CF is nothing like GL here

This is the largest CF/GL divergence in the whole map.

| | CF | GL |
|---|---|---|
| Groups whose `SetPremium` some state rewrites | **213** | 4 |
| Total override instances | **479** | 12 |
| States that rewrite at least one | **21 of 47** | 6 of 51 |
| Premium groups existing only in state packages | 223 | 457 |

**GL states rewrite exactly one thing — Terrorism. CF states rewrite the rating itself, at
scale.**

Heaviest rewriters: **FL 122, PR 64, CA 61, KS 46, NY 43, RI 40, AL 31.** Florida alone
rewrites more premium formulas than every GL state combined, ten times over.

The most contested formulas:

| Group | States |
|---|---|
| `CommercialPropertySpoilageCoverage` | 8 — AL FL GA KS NC RI SC VA |
| `…OutdoorTreesShrubsAndPlantsBasicGroupIICoverage` | 7 — AR DC FL KS NY PR RI |
| `…RadioOrTelevisionAntennasDetailBasicGroupICoverage` | 7 — AR DC FL KS NY PR RI |
| `CommercialPropertyPostTRIACoverage` | 6 — CA DC IL MD NY VA |

**What this does *not* mean.** It is not a finding that CF needs state-over-countrywide
resolution. That was measured long ago — 100.0% of 23,404 `Overridden` rules shadow a
same-named parent — it is non-negotiable **N5**, and `cf_engine/resolve/resolver.py` already
implements it. Any correctly built engine composes the layers regardless of how many rules sit
in each.

**What it does mean is a testing number.** It says how much a single-state proof is worth.
A GL coverage proven in one state is very nearly proven everywhere — only Terrorism varies.
**A CF coverage proven in one state proves much less**, because 213 formulas differ somewhere.
That is a claim about where to spend state test cases, not about architecture: start with the
contested formulas above, because those are where a countrywide-derived expectation is most
likely to be wrong.

**Neither line ever deletes a premium rule.** Zero empty-body premium overrides in CF, as in
GL — the opposite of CF's *validation messages*, where 316 countrywide rules are switched off
by an empty state override. Premium rules are added to or replaced, never silently removed.

---

## 6. Reading this for a specific premium

1. **Find the group in `RollUpTree`** — `Path to account total` is the full chain of
   summations between that record and the account figure. Expect up to seven links.
2. **Check the state first.** Unlike GL, the odds that a CF premium formula is state-rewritten
   are material: 213 groups, 21 states. The tree page's jurisdiction selector flags it.
3. **If it is a leaf**, its `Premium` came from `SetPremium` — `PremiumSources` lists the
   fields that rule reads.
4. **If a premium is missing rather than wrong**, check `PremiumIndicator` before the
   arithmetic. A coverage that rated to zero and a coverage that was never on the policy both
   contribute 0; the indicator is the only discriminator.

---

## 7. Limits of this map

- **The roll-up tree is countrywide.** State overrides of `SetPremium` are counted and
  attributed, but the tree *shape* is CW's. A state adding a premium-bearing group adds a node
  this tree does not draw; the jurisdiction panel lists them instead.
- **Structural, not evaluated.** Read from rule XML. No premium was computed and no path was
  exercised against a live rating.
- **`SetPremium` inputs are flattened** from nested conditions — a rule reading eight fields
  may need only two in any given branch.
- **Rate resolution is out of scope**, as in GL. This map covers rate-to-dollars and the
  aggregation above it; how a rate is built is the rating chain.
