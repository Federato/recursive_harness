# Terrorism (Certified Acts / TRIA) — Rating Algorithms

**Source gate doc:** `docs/gates/GATE-TERRORISM.md`
**Line:** General Liability (GL), Rule 55 *(Terrorism Premium Determination)*, TRIA endorsement options and certified-acts premium
**Derived against:** `GL_CW_20260101_V01`, cross-checked against the other two declared parents (per GATE-TERRORISM.md, header)
**Manual:** `GL-MU-2022-TERXV-001`, *Terrorism Premium Determination*, Table A#.A.1.a, plus the Terrorism Supplement to the CLM (3 notices, PEV001–PEV016, TEV001–TEV008)
**Documented:** 2026-08-20

Terrorism does not fit the shape of the other GL sublines. It has **no base rate, no ELP, and no
loss-cost table of its own.** It is a *premium-on-premium* multiplier: it reads the **finished,
already-rated premiums of sibling coverage groups**, sums them, and applies an exposure-class
factor (plus two optional factors) to produce its own premium. Per GATE-TERRORISM.md § 2, this is
the coverage-group-scope defect pattern "E18" recurring at **policy scope** — terrorism reads four
different groups' final premiums across three sublines and unmanned aircraft, so it must be the
**last thing rated** in a policy (§ 8.1).

Because there is no rate table, this document's "rate build-up" sections are replaced with
**"aggregation and factor application"** — the closest analogue in the terrorism chain to the
CF/GL pattern of base rate → adjustments → final rate.

There are **five** independent premium chains, one per host coverage group (per GATE-TERRORISM.md
§ 1, the `OTHER`-classified population):

- **Prem/Ops** — `GeneralLiabilityTerrorismPremOpsCoverage`
- **Products/Completed Operations** — `GeneralLiabilityTerrorismProdsCompldOpsCoverage`
- **All Other Sublines** — `GeneralLiabilityTerrorismAllOtherSublineCoverage`
- **Unmanned Aircraft** — `GeneralLiabilityUnmannedAircraftTerrorismCoverage`
- **Endorsement-only** — `GeneralLiabilityTerrorismEndorsementCoverage`

This document covers all five.

---

## Master orchestration

Per GATE-TERRORISM.md § 1–2, the 20-table terrorism population in the countrywide package classifies
into **12 CAPTURE · 7 OTHER · 1 RATE_DRIVEN** coverage groups; the 7 `OTHER` groups are the ones that
actually produce a terrorism premium, and none of their premium sources appear in the standard
`RATE_SRC` list (`FinalRate · BaseRate · LossCost · ELP · AdjustedBaseRate · AdjustedRate`) — terrorism
is invisible to a rate-driven scan "by construction, not by measurement" (§ 1).

The worked example, `GeneralLiabilityTerrorismPremOpsCoverage` (per GATE-TERRORISM.md § 2):

```
ClassCoveragePremium = GeneralLiabilityClassificationPremOpsCoverage/Premium
                     + GeneralLiabilityClassificationLossOfElectronicDataPremOpsCoverage/Premium
                     + GeneralLiabilityClassificationCyberIncidentLiabilityPremOpsCoverage/Premium

Premium = round( ClassCoveragePremium
                 x CertifiedActsOfTerrorismExposureClassFactorPremises
                 [x CertifiedActsOfTerrorismNuclBioChemRadioFactor]
                 [x TerrorismILF / GeneralLiabilityClassificationPremOpsCoverage/FinalILF]
               , 0)
```

The bracketed terms are conditional multipliers — see Steps 3 and 4 in each branch below.

Three structural facts follow (per GATE-TERRORISM.md § 2):

1. Terrorism runs **after every other rating item**, including any not yet built, because it
   consumes finished premiums.
2. It reads a sibling's `FinalILF` in addition to its `Premium` — the sub-limit ratio in Step 4
   needs the host's increased-limits factor, not just its dollar answer.
3. Evaluation order is part of the algorithm at **policy** level, not just within a
   classification — the kernel must expose resolved premium state policy-wide.

`SetTerrorismILF` implements the manual's sub-limit selection exactly (PEV001 A.1.c.(1) and (2)):
when the terrorism aggregate limit is ≤ the policy per-occurrence limit, the ILF is taken with the
aggregate limit as **both** occurrence and aggregate; when it is greater, with the **policy
per-occurrence limit** and the terrorism aggregate (per GATE-TERRORISM.md § 2).

---

## File map

| Piece | File / group | Note |
|---|---|---|
| Prem/Ops premium | `GeneralLiabilityTerrorismPremOpsCoverage` | Sums 3 sibling `Premium` values — named explicitly in GATE-TERRORISM.md § 2 |
| Products/Completed Ops premium | `GeneralLiabilityTerrorismProdsCompldOpsCoverage` | Sums 3 sibling `Premium` values — group names not individually cited in the gate doc; see Products/Completed Operations section below |
| All Other Sublines premium | `GeneralLiabilityTerrorismAllOtherSublineCoverage` | Sums 5 sibling `Premium` values; always *Average* exposure class per manual A.1.a |
| Unmanned Aircraft premium | `GeneralLiabilityUnmannedAircraftTerrorismCoverage` | Sums 2 sibling `Premium` values |
| Endorsement-only premium | `GeneralLiabilityTerrorismEndorsementCoverage` | User-entered `EndorsementPremium` x factor — no sibling aggregation |
| Aggregator-only, writes no `Premium` | `GeneralLiabilityTerrorism` | Per GATE-TERRORISM.md § 1 table |
| Policy-level total | `GeneralLiability` | The policy-level total, per GATE-TERRORISM.md § 1 table |
| Sub-limit ILF rule | `SetTerrorismILF` | PEV001 A.1.c.(1)/(2) two-case limit selection |
| Endorsement factor validation | `DoMessageWhenNoClassIsAnAboveAverageExposureClassTheExposureClassFactorCanBeFrom0to004` | Only filed bound on the user-entered endorsement factor |
| Manual corpus | `Commercial Line Manuals/GL/Terrorism/` — 3 notices, 113–118 pages each | Ingested as `text/terrorism/`, `knowledge/terrorism.json` per GATE-TERRORISM.md § 0 |
| Population/verification script | `scripts/erc/37_terrorism_align.py` | 5/5 as of the correction in § 3a |
| 12 `CAPTURE`-classified groups | endorsement capture groups, no rating table | Per GATE-TERRORISM.md § 1, "found by name and not by content" |

> Note: `docs/rating-engine/03-SUBLINE-COVERAGE-PLAN.md` § 3.2.10 independently confirms Rule 55 covers
> TRIA endorsement options and certified-acts premium determination (forms cited there as "CG-120 –
> CG-131"), and that **48 of 51** jurisdictions carry a state A-rule whose entire body just redirects to
> the Terrorism Supplement — consistent with the gate's finding that the supplement, not the base
> corpus, holds the rating rules.

---

## Prem/Ops — rate build-up

**Not applicable to this coverage.** There is no base rate, ELP, or loss-cost step. The "rate" input
to terrorism is the already-computed `Premium` (and `FinalILF`) of three sibling coverage groups —
see Master orchestration above.

---

## Prem/Ops — premium

`GeneralLiabilityTerrorismPremOpsCoverage`

### Step 1 — Aggregate sibling premium
```
ClassCoveragePremium = GeneralLiabilityClassificationPremOpsCoverage/Premium
                     + GeneralLiabilityClassificationLossOfElectronicDataPremOpsCoverage/Premium
                     + GeneralLiabilityClassificationCyberIncidentLiabilityPremOpsCoverage/Premium
```
Per GATE-TERRORISM.md § 2. Three named groups, summed.

### Step 2 — Exposure class factor
```
ExposureClassFactor = lookup CertifiedActsOfTerrorismExposureClassFactorPremises(
    StateCode, PolicyEffectiveWhileTRIAInEffectIndicator, ExposureClass [, Territory in 15 states]
)
```
Countrywide, keyed on `StateCode` / `PolicyEffectiveWhileTRIAInEffectIndicator` / `ExposureClass`:
**Above Average = .009, Average = .004** (per GATE-TERRORISM.md § 3, confirmed against manual Table
A#.A.1.a). The `PolicyEffectiveWhileTRIAInEffectIndicator` key distinguishes the TRIA row from the
"Full (Post-TRIA)" row, but **both currently carry identical values** — a fact worth stating because
an engine that ignored the indicator would still be right today (§ 3).

**15 of 51 jurisdictions** override this to zero countrywide rows and redirect to a state-suffixed
table keyed additionally on `Territory` — see State deviations below (§ 3a).

The exposure class itself is resolved per class code from `TerrorismExposureClassesPremises` in the
resolved package (countrywide plus LA/NJ/NY overrides — see § "The above-average class list" below).

### Step 3 — Nuclear/bio/chem/radio factor (conditional)
```
if applicable:
    Premium_intermediate = Premium_intermediate x CertifiedActsOfTerrorismNuclBioChemRadioFactor
```
CW value **0.58** — manual A.1.b: *"Multiply the additional premium by 0.58"* (per GATE-TERRORISM.md
§ 3). Condition for when this factor applies is not further specified in the gate doc beyond the
manual citation — **not resolved in source docs**: the exact trigger (which endorsement/coverage
selection turns this on) is not traced in GATE-TERRORISM.md.

### Step 4 — Sub-limit ILF ratio (conditional)
```
if applicable:
    Premium_intermediate = Premium_intermediate
        x ( TerrorismILF / GeneralLiabilityClassificationPremOpsCoverage/FinalILF )
```
`TerrorismILF` is set by `SetTerrorismILF` per the manual's two-case limit selection (PEV001
A.1.c.(1)/(2) — see Master orchestration). Divides by the **host group's `FinalILF`**, not a
terrorism-side value — E18 exposure, generalized to policy scope (per GATE-TERRORISM.md § 2).

### Step 5 — Final premium
```
Premium = round(ClassCoveragePremium x ExposureClassFactor
                 [x NuclBioChemRadioFactor] [x TerrorismILF/FinalILF ratio], 0)
```

---

## Products/Completed Operations — differences from Prem/Ops

`GeneralLiabilityTerrorismProdsCompldOpsCoverage`

Structurally identical shape to Prem/Ops — sum three sibling `Premium` values, multiply by an
exposure-class factor, optionally apply the NBCR factor and the sub-limit ILF ratio (per
GATE-TERRORISM.md § 1's "sibling `Premium`, 3 groups summed" entry for this group).

**Not resolved in source docs:** the gate doc names the three Prem/Ops sibling groups explicitly
(§ 2) but does **not** individually name the three Products/Completed Operations siblings. By the
naming convention independently confirmed in `docs/erc/03-RATING-STRUCTURE.md` (§ "class-rated core"
list, which shows parallel `...PremOps / ...ProdsCompldOps` pairs for both
`CyberIncidentLiability` and `LossOfElectronicData` classification groups), the analogous set is
almost certainly:

```
ClassCoveragePremium = GeneralLiabilityClassificationProdsCompldOpsCoverage/Premium
                     + GeneralLiabilityClassificationLossOfElectronicDataProdsCompldOpsCoverage/Premium
                     + GeneralLiabilityClassificationCyberIncidentLiabilityProdsCompldOpsCoverage/Premium
```

but this specific summation is **inferred from naming convention, not directly cited** in
GATE-TERRORISM.md, so it should be verified against the rule file before being treated as filed fact.

Exposure class factor uses `CertifiedActsOfTerrorismExposureClassFactorProducts` and
`TerrorismExposureClassesProducts` (the Products-side counterparts named in GATE-TERRORISM.md § 8.4),
keyed the same way as Prem/Ops.

---

## All Other Sublines — differences from Prem/Ops

`GeneralLiabilityTerrorismAllOtherSublineCoverage`

```
ClassCoveragePremium = sum of 5 sibling Premium values   [not individually named in source docs]
Premium = round(ClassCoveragePremium x ExposureClassFactor
                 [x NuclBioChemRadioFactor] [x TerrorismILF/FinalILF ratio], 0)
```

Per GATE-TERRORISM.md § 1 and § 8.3, this path **always uses the Average exposure category** —
manual A.1.a: *"For sublines other than premises/operations or products/completed operations, use
the average exposure category."* Confirmed in ERC as `TerrorismExposureClassesOtherSublines`, a
**1-row constant table** (per § 3, table row 6): `Average Exposure Class`, always. There is no
per-class-code lookup for this path — it is the one branch where the exposure class is fixed rather
than resolved.

**Not resolved in source docs:** the five specific sibling coverage groups summed into this path are
not individually named in GATE-TERRORISM.md.

---

## Unmanned Aircraft — differences from Prem/Ops

`GeneralLiabilityUnmannedAircraftTerrorismCoverage`

```
ClassCoveragePremium = sum of 2 sibling Premium values   [not individually named in source docs]
Premium = round(ClassCoveragePremium x ExposureClassFactor
                 [x NuclBioChemRadioFactor] [x TerrorismILF/FinalILF ratio], 0)
```

Per GATE-TERRORISM.md § 1. The two summed groups are presumably Unmanned Aircraft's Coverage A and
Coverage B (rated separately per `docs/rating-engine/03-SUBLINE-COVERAGE-PLAN.md` § 3.2.9), but this
pairing is **not resolved in source docs** — the gate doc gives only the count.

---

## Endorsement-only — premium

`GeneralLiabilityTerrorismEndorsementCoverage.SetPremium` (per GATE-TERRORISM.md § 6)

```
Premium = round(EndorsementPremium x CertifiedActsofTerrorismExposureClassFactor, 0)
                                       ^^ lowercase "of" — a distinct DataDef, not a typo
```

No sibling aggregation — `EndorsementPremium` is a **user-entered input**, and
`CertifiedActsofTerrorismExposureClassFactor` (lowercase "of") is a **separate, user-entered
DataDef**, declared in the XSD, distinct from the table-driven capitalized
`CertifiedActsOfTerrorismExposureClassFactor` used in the four aggregation paths above. Countrywide:
3 writers of the lowercase field, all in retired editions (`GL_CW_20201201_V01`,
`GL_CW_20210801_V01`); **0 writers in any edition currently in force** — it is purely user-entered
today, with 28 readers across the corpus (per GATE-TERRORISM.md § 6).

**Its only filed bound** is enforced by a validation message, not a rate table:

```
DoMessageWhenNoClassIsAnAboveAverageExposureClassTheExposureClassFactorCanBeFrom0to004
```

which tests the three `TerrorismExposureClasses{Premises,Products,OtherSublines}` DataDefs and, when
none evaluates to `Above Average Exposure Class`, requires the entered factor to be `> 0` and
`≤ 0.004` (per GATE-TERRORISM.md § 6). "The guard *is* the algorithm" for this branch — there is no
computed value to check it against.

Applicable forms per `docs/rating-engine/03-SUBLINE-COVERAGE-PLAN.md` § 3.2.10 / GATE-TERRORISM.md
§ 8.5: **CG 21 80 / CG 21 89 / CG 21 92**.

---

## Five-way comparison

| | Prem/Ops | Prods/CompldOps | All Other Sublines | Unmanned Aircraft | Endorsement-only |
|---|---|---|---|---|---|
| Premium source | 3 sibling `Premium`, named | 3 sibling `Premium`, not individually named | 5 sibling `Premium`, not named | 2 sibling `Premium`, not named | user-entered `EndorsementPremium` |
| Exposure class | resolved per class code (`...Premises`) | resolved per class code (`...Products`) | **fixed: Average, always** | not resolved in source docs | user-entered factor, validated |
| ILF sub-limit ratio | conditional, per Master orchestration | conditional, same pattern | conditional, same pattern | not resolved in source docs | none — no `FinalILF` input |
| NBCR factor (0.58) | conditional | conditional | conditional | not resolved in source docs | not applicable |
| Group | `GeneralLiabilityTerrorismPremOpsCoverage` | `...ProdsCompldOpsCoverage` | `...AllOtherSublineCoverage` | `GeneralLiabilityUnmannedAircraftTerrorismCoverage` | `...EndorsementCoverage` |

---

## The above-average class list, and jurisdiction overrides

Per GATE-TERRORISM.md § 4: the manual prints **142** above-average classifications; ERC countrywide
carries **141** (105 premises, 54 products, 18 in both). The missing class `91600` exists in ERC (136
of 7,502 csv tables) but is **not in the rating population** countrywide — it appears only in the ILF
assignment table, with 0 of 9 such "extra" classes carrying a loss cost or ELP anywhere countrywide.
**New York** rates `91600` (loss costs in all territory shards, an ELP) and its own
`TerrorismExposureClassesPremises` override (1,191 rows, 106 above-average) lists it as
**Above Average**. Counted as a union across jurisdictions rather than countrywide alone: **142 vs.
142, exact.**

Three jurisdictions override the class tables (per GATE-TERRORISM.md § 4):

| Jurisdiction | Rows | Above-average / Average | vs. countrywide |
|---|---|---|---|
| LA | 1,191 | 105 / 54 | adds `93166 93167 93169` as *average*; no above-average change |
| NJ | 1,187 | 105 / 54 | drops `47469` entirely; no above-average change |
| NY | 1,191 | **106** / 54 | adds `49910 49913 49920 91600`, drops `41620`; `91600` is above-average |

None of the three overrides drops an above-average class — a dropped above-average class would
silently become *average* and under-charge by a factor of 2.25 (`.009 → .004`), which the source's
own verification script now asserts against (per GATE-TERRORISM.md § 4).

---

## State deviations — the countrywide exposure-class factor is not the whole story

Per GATE-TERRORISM.md § 3a: **15 of 51 jurisdictions** override
`CertifiedActsOfTerrorismExposureClassFactor` to zero countrywide rows and redirect all three lookup
rules to a state-suffixed table of their own — **CA, CO, CT, FL, IL, MA, MD, MI, NJ, NY, OR, PA, TX,
VA, WA**.

| | Countrywide | The 15 states |
|---|---|---|
| Keys | `StateCode` · `PolicyEffectiveWhileTRIAInEffectIndicator` · `ExposureClass` | same, **plus `Territory`** |
| Distinct factor values | 2 (`.009` / `.004`) | 15, from `.004` to `.133` |
| Spread | 2.25x | **33x** |

Two go further:

- **New York** files a **Manhattan-specific table** with a fifth key column and factors
  `0.038`–`0.098` — up to 10.9x the countrywide above-average factor — via its own
  `…FactorOtherManhattan` lookup rules.
- **California** adds `…FactorRemainderOfTerritory001` alongside `…FactorCA`.

So terrorism is **territory-rated in 15 states**, applicable across all four aggregation paths (this
is a factor-resolution difference, not a separate premium chain). This was found by
`scripts/erc/40_referral_census.py` probe 6, not by re-reading gate prose, and is pinned as check 3a
in `scripts/erc/37_terrorism_align.py`.

The Terrorism Supplement's rules are organized by version, not by state exception page — **8 `TEV`
endorsement-option versions** (`TEV001` used by 43 of 52), **16 `PEV`** premium-determination versions
(`PEV001` used by 34 of 52), across **52** jurisdiction assignments (50 states + DC + Puerto Rico).
All 16 `PEV` versions carry an identical above-average class list — state versions deviate on *rules*
(disclosure, prorating, conditional-endorsement handling), not on classes (per GATE-TERRORISM.md
§ 5). **Hawaii** is one of the 52 named jurisdictions with no ERC package and no manual documents in
this project's corpus at all — a scope boundary, tracked as OI-54.

---

## Conditional-exclusion prorating — decided, not built

Per GATE-TERRORISM.md § 8.7 (register `R27`, decided 2026-08-12): PEV001 A.2 offers two filed
treatments when a conditional TRIA exclusion is attached — (a) pro-rate by day count and re-rate if
Congress extends the Program, or (b) charge the TRIA factors for the entire policy term and refund if
the Program terminates. **Option (b) is taken**, via a submission field defaulted to *yes*. This needs
no proration arithmetic and is exactly what ERC already does — it detects the condition, computes
`PolicyEffectiveWhileTRIAInEffect` and `PolicyExtendsToPostTRIA`, keys the factor table on the TRIA
indicator, and raises an 18,901-character `TerrorismUnderwritingLogic` message. Two residuals: the
pro-rated refund on actual Program termination is a mid-term change transaction (deferred, out of
scope here), and **whether RAaS can be told to rate the full term is unverified (OI-66)**.

---

## Supporting lookups

| Rule / factor | Table | Keys | CW value |
|---|---|---|---|
| `CertifiedActsOfTerrorismExposureClassFactorPremises` | state-suffixed in 15 states, else countrywide | State, TRIA indicator, ExposureClass [, Territory] | Above Average `.009`, Average `.004` |
| `CertifiedActsOfTerrorismExposureClassFactorProducts` | analogous Products-side table | same shape | not individually re-confirmed in gate doc beyond the Premises example |
| `TerrorismExposureClassesPremises` | class-code lookup, per jurisdiction | ClassCode | CW 105 above-average; LA/NJ/NY override |
| `TerrorismExposureClassesProducts` | class-code lookup, per jurisdiction | ClassCode | CW 54 above-average |
| `TerrorismExposureClassesOtherSublines` | 1-row constant | — | `Average Exposure Class`, always |
| `CertifiedActsOfTerrorismNuclBioChemRadioFactor` | filed value | — | `0.58` |
| `CertifiedActsofTerrorismExposureClassFactor` (lowercase "of") | **not a table** — user-entered input | — | validated `>0` and `≤0.004` when no above-average class present |
| `SetTerrorismILF` / `TerrorismILF` | sub-limit selection per PEV001 A.1.c.(1)/(2) | policy per-occurrence limit, terrorism aggregate limit | — |
| `...FactorOtherManhattan` | NY Manhattan-specific | 5-key, incl. borough | `0.038`–`0.098` |
| `…FactorRemainderOfTerritory001` / `…FactorCA` | CA-specific | Territory | — |

Ten `DomainYear200{3,4,5}Terrorism*Factor*` domain tables exist countrywide at **0 rows each** —
per GATE-TERRORISM.md § 7, obsolete-year stubs the 2022 notice describes as deleted ("referencing
obsolete years and outdated federal share percentages"), not evidence of a rating path.

---

## Quick reference — end-to-end, Prem/Ops path

```
ClassCoveragePremium = PremOps.Premium + LossOfElectronicDataPremOps.Premium
                        + CyberIncidentLiabilityPremOps.Premium

ExposureClass         = lookup TerrorismExposureClassesPremises(ClassCode)   [per-jurisdiction override]

ExposureClassFactor   = lookup CertifiedActsOfTerrorismExposureClassFactorPremises(
                             State, TRIAIndicator, ExposureClass [, Territory in 15 states])
                         [CW: Above Average .009 / Average .004]

TerrorismILF          = PEV001 A.1.c.(1)/(2) two-case limit selection

Premium = round( ClassCoveragePremium
                x ExposureClassFactor
                [x 0.58                                     if NBCR applies]
                [x (TerrorismILF / PremOps.FinalILF)         if sub-limit applies]
              , 0)
```

## Quick reference — end-to-end, endorsement-only path

```
Premium = round(EndorsementPremium x CertifiedActsofTerrorismExposureClassFactor, 0)

# CertifiedActsofTerrorismExposureClassFactor is user-entered (lowercase "of"), validated:
#   if no class on the policy is Above Average Exposure Class:
#       0 < factor <= 0.004
```

All other paths (Products/Completed Operations, All Other Sublines, Unmanned Aircraft) follow the
Prem/Ops shape with the sibling-group substitutions and exposure-class fixing noted in their
respective sections above.

---
