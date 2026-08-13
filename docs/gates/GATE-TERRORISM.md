# Gate — Terrorism (build-order item 9)

**Filed 2026-08-12. Ninth gate.** Differential against
[334](GATE-334-PREMISES-OPERATIONS.md), [336](GATE-336-PRODUCTS-COMPLETED-OPERATIONS.md),
[335 OCP](GATE-335-OWNERS-CONTRACTORS-PROTECTIVE.md), [332](GATE-332-LIQUOR-LIABILITY.md),
[335 Railroad](GATE-335-RAILROAD-PROTECTIVE.md), [365](GATE-365-WITHDRAWAL-LOED-CYBER.md),
[370](GATE-370-UNMANNED-AIRCRAFT.md) and [size-of-risk](GATE-SIZE-OF-RISK.md).

**As-of date: 2026-08-12.** Required, not assumed (N4). Derived against **`GL_CW_20260101_V01`**
and cross-checked against the other two declared parents.

**This gate closes OI-37**, the population audit `RECONCILIATION.md` R3 required before anything
could be said about terrorism.

Measured by [`scripts/erc/37_terrorism_align.py`](../../scripts/erc/37_terrorism_align.py) (4/4).
Manual corpus built by [`scripts/13_extract_terrorism.py`](../../scripts/13_extract_terrorism.py)
and [`scripts/14_build_terrorism_kb.py`](../../scripts/14_build_terrorism_kb.py).

---

## 0. The manual existed and the expert agent could not see it

The Terrorism Supplement to the Commercial Lines Manual — **3 notices, 113 to 118 pages each** —
has been on disk at `Commercial Line Manuals/GL/Terrorism/` throughout. The
`iso-circular-expert` agent's corpus was **`text/rules` (503) and `text/losscosts` (472) — 975
documents**, and the supplement was not among them.

So every terrorism question the agent was ever asked was answered from a corpus that did not
contain the terrorism rules, and its honest answer would have been *"the manual is silent"*. **That
is the exact failure mode OI-51 was opened for one section earlier in this same session**, arriving
from the other direction: there it was a extractor returning nothing, here it is a folder never
ingested.

**Fixed.** `text/terrorism/` now holds the three notices, page-tagged, and `iso.py` routes
`--kind TER`. `knowledge/terrorism.json` carries the decoded supplement. Two smoke tests added
(17/17).

**Still missing, and now stated rather than discovered later: 142 of the 1,120 documents on disk
are not in the agent's corpus** — the **52** `Schedule & Experience Rating` manuals and the **90**
`Composite Rating` manuals. **The Composite Rating folder arrived during this session and was still
being populated as this was written** (36 documents when first counted, 90 at the last count), which
is why the figure is given with its as-of. Those are build-order item 10's corpus, and Composite
Rating is the material **OI-03** recorded as absent. **OI-55.**

---

## 1. The population audit — OI-37 closed

`RECONCILIATION.md` R3: *do not repeat "terrorism premium cannot be computed" until the population
is audited.* Audited.

**The population is the 477 premium-writing coverage groups**, classified by whether their **rules**
touch a terrorism artifact — never by whether `Terror` appears in the group name. The 20 terrorism
tables in the countrywide package were enumerated from the directory first.

| | |
|---|---|
| Groups matching the **name** `Terror` | **18 of 477** |
| Groups whose **rules** touch a terrorism table | **7** |
| Found by content and **not** by name | **2** — `GeneralLiability`, `GeneralLiabilityClassification` |
| Found by name and **not** by content | **13** — the endorsement capture groups, which carry no rating table |
| **Terrorism population** | **20 groups** |

Classified by `25_rating_vs_capture`: **12 CAPTURE · 7 OTHER · 1 RATE_DRIVEN**.

### `OTHER` is not a miscellany — every one has a nameable premium source

| Group | Premium source |
|---|---|
| `GeneralLiabilityTerrorismPremOpsCoverage` | **sibling `Premium`, 3 groups summed** |
| `GeneralLiabilityTerrorismProdsCompldOpsCoverage` | **sibling `Premium`, 3 groups summed** |
| `GeneralLiabilityTerrorismAllOtherSublineCoverage` | **sibling `Premium`, 5 groups summed** |
| `GeneralLiabilityUnmannedAircraftTerrorismCoverage` | **sibling `Premium`, 2 groups summed** |
| `GeneralLiabilityTerrorismEndorsementCoverage` | user-entered `EndorsementPremium` × factor |
| `GeneralLiability` | the policy-level total |
| `GeneralLiabilityTerrorism` | writes no `Premium` in this parent |

**None of those sources is in `25_rating_vs_capture.RATE_SRC`**, which lists
`FinalRate · BaseRate · LossCost · ELP · AdjustedBaseRate · AdjustedRate`. So terrorism is absent
from the **18 RATE_DRIVEN** headline **by construction**, not by measurement.

**This is the third instance of that list being short.** `AdjustedRate` was missing until
2026-08-11 and filed both Unmanned Aircraft coverages as aggregators (README finding 5). The list
is not wrong so much as it encodes an assumption — *a rating path starts from a rate* — that ERC
breaks in two distinct ways now: item 6's factor-on-host (E18) and terrorism's premium-on-premium.

**The answer to the question R3 was guarding: terrorism premium CAN be computed, and the algorithm
is complete in ERC.** What it cannot do is start from a rate, because it does not have one.

---

## 2. The algorithm — and it is E18 at policy scale

`GeneralLiabilityTerrorismPremOpsCoverage`:

```
ClassCoveragePremium = GeneralLiabilityClassificationPremOpsCoverage/Premium
                     + GeneralLiabilityClassificationLossOfElectronicDataPremOpsCoverage/Premium
                     + GeneralLiabilityClassificationCyberIncidentLiabilityPremOpsCoverage/Premium

Premium = round( ClassCoveragePremium
                 × CertifiedActsOfTerrorismExposureClassFactorPremises
                 [× CertifiedActsOfTerrorismNuclBioChemRadioFactor]
                 [× TerrorismILF ÷ GeneralLiabilityClassificationPremOpsCoverage/FinalILF] , 0)
```

Three things follow, and the third is the architectural one:

1. **Terrorism is the last thing rated.** It consumes *finished* premiums, so it must run after
   every rating item, including the ones not yet built.
2. **It reads a sibling's `FinalILF` as well as its `Premium`** — the sub-limit ratio needs the
   host's increased-limit factor, not just its answer.
3. **E18 said coverage groups are not independently evaluable. Terrorism says the same of the
   whole policy.** Item 6 reads a host group's computed values; terrorism reads *four different
   groups' final premiums* across three sublines and unmanned aircraft. **The kernel must expose
   resolved premium state policy-wide, and evaluation order is part of the algorithm at policy
   level, not just within a classification.**

`SetTerrorismILF` implements the manual's sub-limit steps exactly: when the terrorism aggregate
limit ≤ the policy per-occurrence limit, the ILF is taken with the aggregate limit as **both**
occurrence and aggregate; when it is greater, with the **policy per-occurrence limit** and the
terrorism aggregate. That is PEV001 A.1.c.(1) and (2), step for step.

---

## 3. Manual against ERC — exact on every number

Manual: `GL-MU-2022-TERXV-001`, *Terrorism Premium Determination*, Table A#.A.1.a.

| Manual | Value | ERC | Value |
|---|---|---|---|
| Above Average Exposure Classes, TRIA | `.009` | `CertifiedActsOfTerrorismExposureClassFactor` (`TRIA=1`) | `0.009` |
| Average Exposure Classes, TRIA | `.004` | same, `TRIA=1` | `0.004` |
| Above Average, **Full (Post-TRIA)** | `.009` | same, `TRIA=0` | `0.009` |
| Average, **Full (Post-TRIA)** | `.004` | same, `TRIA=0` | `0.004` |
| A.1.b *"Multiply the additional premium by 0.58"* | `0.58` | `CertifiedActsOfTerrorismNuclBioChemRadioFactor` | `0.58` |
| A.1.a *"For sublines other than premises/operations or products/completed operations, use the average exposure category"* | — | `TerrorismExposureClassesOtherSublines`, **1 row, constant** | `Average Exposure Class` |

**4 of 4 factor cells agree, and the two prose rules are each a filed one-row table.** The
`PolicyEffectiveWhileTRIAInEffectIndicator` key is ERC's encoding of the manual's TRIA / Full
(Post-TRIA) row split — and the values are identical across it, which is worth stating because an
engine that ignored the indicator would still be right today and wrong the moment ISO differentiates
them.

### 3a. Correction — the countrywide pair describes 36 of 51 jurisdictions, not the corpus

**Filed 2026-08-12, corrected the same day.** The table above is right about the countrywide
package and was written as though that settled the factors. It does not.

**15 of 51 jurisdictions override `CertifiedActsOfTerrorismExposureClassFactor` to zero rows and
redirect all three lookup rules to a state-suffixed table of their own** — CA, CO, CT, FL, IL, MA,
MD, MI, NJ, NY, OR, PA, TX, VA, WA.

| | Countrywide | The 15 |
|---|---|---|
| Keys | `StateCode` · `PolicyEffectiveWhileTRIAInEffectIndicator` · `ExposureClass` | **the same, plus `Territory`** |
| Distinct factor values | **2** — `0.009` / `0.004` | **15**, from `0.004` to `0.133` |
| Spread | 2.25× | **33×** |

**So terrorism is territory-rated in 15 states**, and the countrywide above-average/average pair is
simply the wrong number for them. Two go further still:

- **New York** files a **Manhattan-specific table** with a fifth key column and factors
  `0.038`–`0.098` — up to **10.9× the countrywide above-average factor** — plus its own
  `…FactorOtherManhattan` lookup rules.
- **California** adds `…FactorRemainderOfTerritory001` alongside `…FactorCA`.

**Nothing here is an ERC defect.** It is N3 doing exactly what N3 says: a wholesale override to an
empty table, with the lookup re-pointed. The defect was in this gate — **it checked the countrywide
table against the manual and did not ask who reads it.**

**Found by [`40_referral_census.py`](../../scripts/erc/40_referral_census.py) probe 6**, built for
build-order item 12, whose entire purpose is to find referral conditions by scanning rather than by
re-reading gate prose. It found this on its first run. **Now pinned as check 3a in
[`37_terrorism_align.py`](../../scripts/erc/37_terrorism_align.py) (5/5).**

**The engine's obligation changes with it:** the terrorism factor is a **territory** lookup resolved
from the jurisdiction package, not a countrywide constant pair, and New York needs a Manhattan
discriminator that exists in no other coverage in the corpus.

---

## 4. The above-average class list — 142 = 142, once the right comparand is used

The manual prints **142** above-average classifications. ERC countrywide carries **141**
(105 premises, 54 products, 18 in both). The missing one is `91600`, and **the discrepancy is not
a defect — it is ERC scoping a countrywide list per package.**

| Step | Finding |
|---|---|
| Is `91600` in ERC at all? | Yes — **136 of 7,502** csv tables across 61 packages, including every jurisdiction's `PremOpsIncrdLimitTableAssignment` |
| Is it in the **rating** population? | **No.** `PremOpsIncrdLimitTableAssignment` carries **1,197** classes; the terrorism and size-of-risk tables carry **1,188**, and those two 1,188-class sets are **identical** |
| Do the 9 extras carry a loss cost or ELP anywhere? | **0 of 9.** They exist only in the ILF assignment table, so countrywide they cannot be rated at all |
| Does anyone rate `91600`? | **New York does** — loss costs in all its territory shards, an ELP, split-limit weights |
| Does New York's terrorism table list it? | **Yes, `Above Average Exposure Class`** — NY overrides `TerrorismExposureClassesPremises` with 1,191 rows and **106** above-average |

**So the manual's 142 is the union across jurisdictions, ERC's 141 is the countrywide-rateable
subset, and New York supplies the 142nd exactly where it is rateable.** Checked as a union:
**142 vs 142, zero either way.**

**The first draft of this section called `91600` a premium defect** — the reasoning was correct
(no exposure class → null factor → guarded to `0` → zero terrorism premium) and the premise was
wrong, because the class is not rateable countrywide, so that path is unreachable. It took four
measurements to establish that, and none of them was re-reading the claim.

### The three jurisdictions that override the class tables

| | Rows | Above-average | vs countrywide |
|---|---|---|---|
| **LA** | 1,191 | 105 / 54 | adds classes `93166 93167 93169` as *average*; no above-average change |
| **NJ** | 1,187 | 105 / 54 | drops class `47469` entirely; no above-average change |
| **NY** | 1,191 | **106** / 54 | adds `49910 49913 49920 91600`, drops `41620`; **`91600` above-average** |

**3 of 3 overrides add above-average classes without dropping any**, which matters under N3:
an override is wholesale, so a dropped above-average class would silently become *average* and
under-charge by a factor of 2.25 (`.009 → .004`). That is now an assertion in the script.

---

## 5. The state version surface — 8 endorsement versions, 16 premium versions, 52 assignments

The supplement is organised as versions, not as state exception pages:

| | |
|---|---|
| `TEV` — Rule 55 Terrorism Endorsement Options | **8** versions · `TEV001` used by **43 of 52** |
| `PEV` — Terrorism Premium Determination | **16** versions · `PEV001` used by **34 of 52** |
| Jurisdictions with an explicit assignment | **52** — 50 states + DC + Puerto Rico |

**All 16 PEV versions carry an identical above-average class list.** The state versions deviate on
**rules** — disclosure requirements, prorating, conditional endorsement handling — **not on
classes**. That is a useful build fact: the class table is countrywide plus three ERC overrides,
while the *rules* need sixteen readings.

**Hawaii is one of the 52 and this project holds nothing for it** — no ERC package (51
jurisdictions) and **0 of 1,066** manual documents. Consistently absent from every source, so it is
a scope boundary rather than a gap. **OI-54.**

---

## 6. A second load-bearing misspelling, and it is an input rather than a table

`GeneralLiabilityTerrorismEndorsementCoverage.SetPremium`:

```
Premium = round(EndorsementPremium × CertifiedActsofTerrorismExposureClassFactor, 0)
                                                    ^^ lowercase "of"
```

Counted in the countrywide rule set: **3 occurrences of `CertifiedActsofTerrorismExposureClassFactor`
against 6 of `CertifiedActsOfTerrorismExposureClassFactor`**, and the lowercase form is declared in
the XSD. It is a **distinct DataDef**, not a typo'd reference — exactly OI-47's `ProductWithdrawl`
pattern, and the second instance. **Never normalise it**: normalising would collide it with the
table-driven capitalised name and silently change which value is read.

**And it is read, never written, in every edition in force.** Across all 61 packages: **10 writers,
all of them in `GL_CW_20201201_V01` and `GL_CW_20210801_V01`; 0 writers in all three declared
parents and in `GL_CW_20270401_V01`; 28 readers.**

**That reads like a deletion defect zeroing a premium, and it is not.** The factor became a
**user-entered input**, and ERC validates it with a rule that exists only as a message:

> `DoMessageWhenNoClassIsAnAboveAverageExposureClassTheExposureClassFactorCanBeFrom0to004`

which tests all three exposure-class DataDefs for `Above Average Exposure Class` and, when none is,
requires the entered factor to be **> 0 and ≤ 0.004**. **N15 exactly: the guard *is* the algorithm,
and it is the only statement anywhere of what the endorsement factor may be.**

---

## 7. Obsolete-year tables, and what they are not

Ten `DomainYear200{3,4,5}Terrorism*Factor*` domain tables exist in the countrywide package at
**0 rows each**. The 2022 notice says ISO *"deleted tables referencing obsolete years and outdated
federal share percentages."*

**Under N7 these are 10 more empty schema stubs, not evidence of a rating path.** They join the 79
counted by `34_crosscheck.py`; the assertion that holds is the narrow one — no *populated*
countrywide table is unread.

---

## 8. What the engine owes

1. **A terrorism stage that runs last**, after every rating item, consuming finished premiums.
2. **Policy-wide resolved premium state in the kernel** — E18 generalised. Terrorism reads four
   groups' `Premium` and one group's `FinalILF` across three sublines and unmanned aircraft.
3. **Four rating paths, one per host**: Prem/Ops, Products/Completed Operations, All Other
   Sublines (5 groups summed, always *average* exposure per A.1.a), and Unmanned Aircraft.
4. **The exposure class resolved per class code and per subline**, from
   `TerrorismExposureClasses{Premises,Products,OtherSublines}` in the **resolved package** — LA, NJ
   and NY override them.
5. **The sub-limit ILF ratio** with the manual's two-case limit selection, keyed by endorsement
   form (`CG2180` / `CG2189` / `CG2192`).
6. **`CertifiedActsofTerrorismExposureClassFactor` as an input**, spelled as filed, validated
   `0 < f ≤ 0.004` when no class on the policy is above-average.
7. ~~**Prorating when a conditional exclusion is attached**~~ — **DECIDED 2026-08-12 (register
   `R27`).** PEV001 A.2 offers the insurer **two filed treatments**: (a) pro-rate by day count now
   and re-rate if Congress extends, or (b) **charge the TRIA factors for the entire term** and
   refund if the Program terminates. **Option (b) is taken**, via a submission field defaulted to
   *yes*. It needs no proration arithmetic — **and it is exactly what ERC already does.** ERC
   detects the condition, computes `PolicyEffectiveWhileTRIAInEffect` and `PolicyExtendsToPostTRIA`,
   keys the factor table on the TRIA indicator and raises an 18,901-character
   `TerrorismUnderwritingLogic` message, while **declaring 9 pro-rate / day-count fields that no
   rule writes.** Choosing (b) makes that gap correct rather than missing, and **no rating
   calculation is sourced from the manual** — the R25 line holds. **Two residuals:** option (b)'s
   pro-rated refund on actual termination is a mid-term change transaction, deferred; and **whether
   RAaS can be told to rate the full term is unverified (OI-66)** — if it cannot, every
   2027-inception policy running past year-end differs from the oracle by design.
8. **`SizeOfRiskRatingApplies` interaction is nil** — terrorism multiplies the finished premium,
   whatever produced it.
9. **The 16 PEV versions must be read before the referral and disclosure behaviour is settled.**
   The classes are countrywide; the rules are not.

---

## 9. Register changes

| | |
|---|---|
| **OI-37** | **CLOSED.** The population audit ran: 20 groups, classified, with the `OTHER` bucket explained. R3's prohibition is lifted |
| **OI-51** | **Corrected** — the "187 image-only documents" diagnosis was a `pdftotext` failure, not missing text (§0 of this gate and the size-of-risk gate §0) |
| **OI-54** *(new)* | Hawaii: named by the terrorism supplement, absent from every project source |
| **OI-55** *(new)* | 88 of 1,066 manual documents not in the expert agent's corpus — 52 Schedule & Experience Rating, 36 Composite Rating |
| **OI-56** *(new)* | The two truncated source PDFs are registered inconsistently — the rules one is in `notices.json`, the loss-cost one is not. Both have 0-byte text placeholders, and both are exactly the 2 documents that fail both extractors |
| **OI-57** *(new)* | Conditional-exclusion prorating is a manual-only procedure with no ERC rule |
| **OI-47** | Second instance: `CertifiedActsofTerrorismExposureClassFactor`. **The rule generalises** — ERC spelling variants are load-bearing, plural |
| **E18** | **Widened from coverage-group scope to policy scope** (§2) |
| **N15** | Strengthened: the endorsement factor's only filed bound lives in a `DoMessage*` rule (§6) |
| **README finding 5** | The `18/383/76` split stands as measured, but `RATE_SRC` now has two known blind spots, both real rating paths |

---

## 10. Verification

| | |
|---|---|
| `scripts/erc/37_terrorism_align.py 20260812` | **5/5** (was 4/4; check 3a added by the correction above) |
| `Agentic/iso-circular-expert/tools/smoke_test.py` | **17/17** (15 + 2 new) |
| `scripts/erc/35_census_sizeofrisk.py 20260812` | 5/5 |
| `scripts/erc/34_crosscheck.py 20260812` | 4/4 |
| `tests/verify_golden.py` | 80/80 |
