# Gate -- Stop Gap - Employers Liability Coverage (state A-rule, no ISO subline code)

**Filed 2026-09-02.** New gate -- no ISO subline number exists for this coverage; it is filed as a
**state-only Additional Rule (A-rule), not a numbered CW rule.** Differential against
[370](GATE-370-UNMANNED-AIRCRAFT.md) (another small, mostly-referred, state-scoped coverage) and
[335 Railroad](GATE-335-RAILROAD-PROTECTIVE.md) (another ELP-style factor-on-host coverage).

**As-of date: 2026-09-02.** Derived against the newest 2027-04-01 packages on disk for each of the
five jurisdictions (ND V04, OH V04, WA V02 -- no 2027 edition filed yet, see Section 5 -- WY V03,
PR V04).

> **Scope, stated plainly first.** Stop Gap - Employers Liability Coverage exists **only** in the
> five monopolistic state-fund jurisdictions -- **ND, OH, PR, WA, WY** -- where the state workers'
> compensation fund does not itself provide employers liability coverage alongside workers' comp.
> `docs/rating-engine/03-SUBLINE-COVERAGE-PLAN.md` row 17 and `docs/rating-engine/04-STATE-DEVIATIONS.md`
> both record this as each state's **Rule A2**. Confirmed independently below, both in the manual
> text and in the raw ERC package tree.

---

## 0. Headline -- the opposite finding from what the assignment expected

**Both tier-2 leads (the "A2 - Stop Gap" state-deviation table and the 04-STATE-DEVIATIONS.md
row) turned out to be correct, and so did the manual's factors.** But the ERC side needed a second
look: the project's own **precomputed knowledge base does not list Stop Gap** in any of the five
states' `resolved_sublines` (`Agentic/iso-erc-expert/knowledge/jurisdictions.json`), which might
suggest ERC never derived this coverage.

**That reading is wrong, and it is wrong for a specific, mechanical reason.** ERC implements Stop
Gap completely, in all five states, at every edition on disk back to 2021 -- a full rule chain, a
dedicated rate table, statistical codes, and a policy-level premium aggregator wired into the
top-level `GeneralLiabilityRules.ErcCalculateTotalPremium` entry point. The precomputed
`resolved_sublines` list simply does not surface it, because Stop Gap's rule file is named
`GeneralLiabilityStopGapEmployersLiabilityCoverageEndorsementPolLvlRules` -- a **policy-level
("PolLvl") endorsement rule group**, not a `GeneralLiabilityClassification<Name>CoverageRules`
file in the shape the knowledge extraction pattern-matches on. **Presence was there; the
extraction's naming pattern did not reach it.** This is the same shape of miss as N7/OI-20
elsewhere in this project (`GATE-335-RAILROAD-PROTECTIVE.md` Section 3) and Habit 6
(`GATE-335-RAILROAD-PROTECTIVE.md` Section 4): absence from one derived index is not absence from
the corpus, and the raw package tree is the only thing that actually answers the question.

**The strongest result of this gate: 25 rate cells (5 classification types x 5 states) match the
manual's two-bucket factor table exactly, independently filed and independently extracted.**

| | |
|---|---|
| States rating this coverage | **5** -- ND, OH, PR, WA, WY (confirmed both in the manual and in the raw ERC tree) |
| States carrying only a stat-code placeholder, no rating | **WV** -- `StopGapStatCodeDef` exists, 0 rows, no Rules file, no rate table. Corroborates the 5-state scope rather than widening it |
| Countrywide `StopGapRate` table | **Header-only, 0 rows, at every edition checked** (20261001, 20270401 V01/V02) -- the CW fallback in `LookupStopGapRate` can never resolve; every state must supply its own factors |
| Rate factors | **Exactly two values, `.03` and `.02`**, identical in all five states, at every classification type |
| Manual vs ERC on the factor table | **25/25 cells match** (see Section 4) |
| Oracle | **None found** -- no golden-case payload in this repo carries a populated Stop Gap block |

---

## 1. The manual's algorithm -- Rule A2, identical text in all five states

Read directly from `Agentic/iso-circular-expert/text/rules/` -- the latest Rules notice per state:
`GL-ND-2027-RU-003-C`, `GL-OH-2027-RU-004-C`, `GL-WA-2026-RU-001-C`, `GL-WY-2026-RU-002-C`,
`GL-PR-2027-RU-003-C`.

**All five states file the identical five-step algorithm, word for word**, differing only in the
attaching endorsement form number:

> **A. Coverage.** *"The state insurance fund does not provide employers liability coverage with
> its workers' compensation insurance. To provide employers liability coverage for situations in
> which an employer can be held liable for injuries to employees, attach [state] Stop Gap -
> Employers Liability Coverage Endorsement ..."*
>
> **B. Premium Determination.**
> 1. *If the limits for Bodily Injury By Accident - Each Accident and Bodily Injury By Disease -
>    Each Employee are the same*, the premium is:
>    a. Determine the applicable classification(s) and exposure base.
>    b. Select the **premises/operations basic limit rate(s)**.
>    c. Multiply by the factor in **Table A2.B.1.c**:
>       | Type Of Risk | Factor |
>       |---|---|
>       | Manufacturing, Processing, Contracting or Servicing Risks | **.03** |
>       | All Other Risks | **.02** |
>    d. Apply the appropriate **premises/operations Increased Limits Factor** (using the Bodily
>       Injury By Accident limit as the Each Occurrence Limit and the Bodily Injury By Disease
>       Aggregate limit as the General Aggregate Limit) per **Rule 23.D**.
>    e. Multiply the number of units of exposure per classification by the adjusted rate.
> 2. *If the two limits differ*, **refer to company for rating.**

| State | Endorsement form | Notice | Notes |
|---|---|---|---|
| ND | CG 04 40 | `GL-ND-2027-RU-003-C` | -- |
| OH | CG 04 41 | `GL-OH-2027-RU-004-C` | text specifies "third party over actions" |
| WA | CG 04 42 | `GL-WA-2026-RU-001-C` | also requires attaching Washington Changes - Who Is An Insured CG 04 50 |
| WY | CG 04 44 | `GL-WY-2026-RU-002-C` | -- |
| PR | CG 04 51 | `GL-PR-2027-RU-003-C` | PR's Rule A1 (Co-Employee coverage) is a separate, unrelated, fully refer-to-company endorsement -- not part of Stop Gap |

**Manual-only, no ERC test possible from the manual alone:** the refer-to-company branch (B.2,
limits differ) is a condition on two *submitted* values being unequal -- see Section 3 for how ERC
actually implements this branch, which is more concrete than "refer to company" reads on its own.

---

## 2. The ERC rule chain -- present, complete, and wired in, in all five states

Located directly in `C:\Projects\ISO_ERC_Files\General_Liability\{ND,OH,PR,WA,WY}\...\Rules\`.
Every state carries:

- `GeneralLiabilityStopGapEmployersLiabilityCoverageEndorsementPolLvlRules.Rule.xml` -- the
  **policy-level** endorsement rule group (one instance per attached endorsement)
- Four rating rules added to `GeneralLiabilityClassificationRules.Rule.xml`'s `ErcRate` override,
  identical rule names and identical call order in **all five states**:

```
ErcRate (GeneralLiabilityClassification, overridden):
    <run CW ErcRate first>
    SetStopGapIncrdLimitFactor
    SetStopGapFactor
    SetStopGapFinalRate
    SetStopGapPremium
```

Traced from ND's `GL_ND 20270401 V04` (identical rule bodies confirmed present by name and call
order in OH V04, WY V03, PR V04; WA V02, which has no 2027 edition on disk -- see Section 5):

| Rule | What it does | Manual step |
|---|---|---|
| `SetStopGapIncrdLimitFactor` | `LookupILFPremOpsWithArgs(assignment, accidentLimit, diseaseLimit)` -- the Premises/Operations Increased Limits Factor, reused directly, keyed on the submitted BI-by-accident and BI-by-disease-aggregate limits | B.1.d, and names Rule 23.D exactly |
| `SetStopGapFactor` | `LookupStopGapRate(StateCode, ClassificationType)` -> the `.03`/`.02` table (Section 4) | B.1.c |
| `SetStopGapFinalRate` | `StopGapFinalRate = round(StopGapIncrdLimitFactor x (StopGapFactor x PremOpsCoverage.BaseRate) x PackageModFactor x ExperienceRatingModificationFactor x ModToUse, 3)` | B.1.b-d, with the usual premium-level multipliers folded in |
| `SetStopGapPremium` | `StopGapPremium = round(StopGapFinalRate x PremOpsExposureCalc, 0)` | B.1.e |

**This is not a factor-on-host coverage that borrows tables -- it borrows the host's own
already-computed values.** `GeneralLiabilityClassificationPremOpsCoverage/BaseRate` and
`PremOpsExposureCalc` are Premises/Operations' own computed base rate and exposure count, not
independent lookup tables. That is the opposite of drone's pattern
(`GATE-370-UNMANNED-AIRCRAFT.md` Section 1: "it borrows the tables, not Prem/Ops's already-computed
values, so it carries no cross-coverage (E18) dependency"). **Stop Gap does carry an E18
dependency** -- its premium cannot be computed until Premises/Operations' classification-level rate
and exposure have already been set for the same classification.

---

### The refer-to-company branch is implemented as a submission requirement, not a message

The policy-level rule group's `SetPremium` (in the `...PolLvlRules` file) is the actual premium
gate, and it reproduces manual paragraph B exactly as a branch on the two BI limits:

```
if LimitBodilyInjuryByAccident == LimitBodilyInjuryByDiseaseEachEmployee:
    Premium = sum(StopGapPremium across every classification, every location)
else:
    Premium = round(ManualPremium x PackageModFactor, 0)
```

**When the two limits differ, ERC does not refuse or leave the field blank -- it multiplies a
submission-supplied `ManualPremium` field by the package modification factor.** `ManualPremium`
is not computed anywhere in the Stop Gap rule chain; it must arrive already priced, which is
exactly what "refer to company for rating" means operationally: the company (or its rater) prices
the risk outside ERC and the submission carries the answer in. This is the same shape as OCP's
`WorkersCompensationRate` submission requirement, noted in `GATE-370-UNMANNED-AIRCRAFT.md`
Sections 6/7a as the general pattern for `REFER_TO_COMPANY` mechanics that still need a field to
carry the answer through.

**Fully wired at the top level**, confirmed by tracing `GeneralLiabilityRules.Rule.xml` (ND, lines
53-55, 108-113, 1332-1339, 1401-1409): the state's `InitializeRuleSet`, `CalculateTotalPremium`,
and both `ErcProcess` variants each `ForEach` over
`GeneralLiabilityStopGapEmployersLiabilityCoverageEndorsementPolLvlTable`, so an attached Stop Gap
endorsement's premium reaches the policy total the same way every other coverage's does. **This is
not an orphan rule and not dead code** -- the opposite finding from the assignment's initial worry
that Stop Gap might turn out to be unimplemented in ERC.

---

## 3. The classification-type collapse -- five ERC keys, two manual buckets, confirmed by mapping

ERC's `StopGapRate` table is keyed on **five** `ClassificationType` values -- the same countrywide
five-way split used throughout Rule 24/27/29/31/32 (Buildings Or Premises, Contracting Or
Servicing, Manufacturing Or Processing, Mercantile, Miscellaneous) -- not the manual's prose
two-bucket split. They collapse onto the manual's two buckets exactly:

| ERC `ClassificationType` | Factor | Manual bucket |
|---|---|---|
| Manufacturing Or Processing | .03 | Manufacturing, Processing, Contracting or Servicing Risks |
| Contracting Or Servicing | .03 | Manufacturing, Processing, Contracting or Servicing Risks |
| Buildings Or Premises | .02 | All Other Risks |
| Mercantile | .02 | All Other Risks |
| Miscellaneous | .02 | All Other Risks |

**Confirmed independently a second way**, from `StopGapStatCode.RateTable.csv` (ND): the same
five-way split maps to exactly **two** statistical codes -- `92400` (Manufacturing Or Processing,
Contracting Or Servicing) and `92405` (the other three) -- matching the `.03`/`.02` boundary
exactly. Two independently-filed ERC tables (a rate factor table and a statistical-code table)
draw the line in the same place the manual's prose does.

**Two orphan stat-code tables**, confirmed empty in ND at 20270401 V04:
`StopGapManProcContServRiskStatCode.RateTable.csv` and
`StopGapRisksOtherThanManProcContServRiskStatCode.RateTable.csv` -- both header-only, 0 rows, no
values to trace. Same shape as `RailroadLossCost` in `GATE-335-RAILROAD-PROTECTIVE.md` Section 3:
a table that exists and has no reader worth tracing (`StopGapStatCode` is the one actually read,
via `LookupStopGapStatCode`).

---

## 4. The 25-cell manual/ERC match

Manual `Table A2.B.1.c` (2 values, identical text in all five states, Section 1) against ERC's
`StopGapRate.RateTable.csv` (5 rows x 5 states = 25 cells), read directly from the newest package
on disk per state:

| State | Buildings/Premises | Contracting/Servicing | Manufacturing/Processing | Mercantile | Miscellaneous |
|---|---|---|---|---|---|
| ND | 0.02 | 0.03 | 0.03 | 0.02 | 0.02 |
| OH | 0.02 | 0.03 | 0.03 | 0.02 | 0.02 |
| WA | 0.02 | 0.03 | 0.03 | 0.02 | 0.02 |
| WY | 0.02 | 0.03 | 0.03 | 0.02 | 0.02 |
| PR | 0.02 | 0.03 | 0.03 | 0.02 | 0.02 |

**25/25 cells identical**, across five independently-filed state rate tables, and every one of
them collapses onto the manual's two-value table exactly as Section 3 describes. WA's row labels
are worded slightly differently in its own CSV ("Buildings or Premises - Office or Residential
Occupancy or Leased to Others" rather than the bare "Buildings Or Premises") but the value and the
classification are the same category -- confirmed by reading WA's own `ClassificationType`
values directly, not assumed.

---

## 5. Layer pattern and edition coverage

| Table | Countrywide | State (latest edition each) |
|---|---|---|
| `StopGapRate` | **0 rows**, at every CW edition checked (20261001 V01, 20270401 V01, 20270401 V02) | 5 rows in **each of the 5 states** |
| `StopGapStatCode` | not checked at CW (state-keyed lookup, no CW fallback path in `LookupStopGapStatCode`) | 5 rows in ND (not re-checked for OH/WA/WY/PR -- **not resolved in source docs**) |
| `StopGapManProcContServRiskStatCode`, `StopGapRisksOtherThanManProcContServRiskStatCode` | not checked | **0 rows** in ND -- orphan (Section 3) |
| `DomainStopGapBIByAccidentOrByDisease` | not checked | 13 whole-dollar bands, $25,000-$10,000,000 (ND) -- the legal domain for the two BI limit fields |

**Because the CW `StopGapRate` table is permanently empty, `LookupStopGapRate`'s `FirstNonNull`
fallback to `CW` can never succeed for this table** -- every one of the five states must file its
own factor row for every classification type it wants to rate, or `SetStopGapFactor`'s null-guard
writes `0.0` (a silent, unguarded zero-rate path, structurally similar to E15/E16's pattern
elsewhere in this corpus).

**Edition currency is uneven across the five states**, checked directly against the package tree
rather than assumed:

| State | Newest package on disk | Has a 2027-04-01 edition? |
|---|---|---|
| ND | `GL_ND_20270401_V04` | Yes |
| OH | `GL_OH_20270401_V04` | Yes |
| WY | `GL_WY_20270401_V03` | Yes |
| PR | `GL_PR_20270401_V04` | Yes |
| WA | `GL_WA_20260101_V02` | **No -- newest on disk is 2026-01-01** |

WA's Stop Gap rule chain and rate table were therefore read from its 2026-01-01 package, not a
2027-04-01 one. **Not resolved in source docs -- whether WA has since filed a 2027-04-01 edition
that simply is not present in this corpus pull**, the same open-ended caveat this project has
already logged for other states at the 2027 cliff (OI-97, `BUILD-LOG.md` entries 56-58).

---

## 6. WV is not a sixth state, and that is itself evidence

**West Virginia carries a `StopGapStatCodeDef`/`StopGapStatCode` rate-table pair at every edition
checked (2021-08-01 through 2027-04-01), and nothing else** -- no
`GeneralLiabilityStopGapEmployersLiabilityCoverageEndorsementPolLvlRules.Rule.xml`, no
`StopGapRateDef`/`StopGapRate` factor table, no `SetStopGap*` rules added to WV's classification
rules. A boilerplate statistical placeholder with no rating machinery behind it -- the same
"populated-looking name may have no purpose at all" shape `GATE-335-RAILROAD-PROTECTIVE.md`
Section 3 describes for `RailroadLossCost`.

**This corroborates the five-state scope rather than narrowing or widening it.** WV is not one of
the five monopolistic-fund states named in the task, and ERC's own file layout agrees: the
statistical code exists everywhere ISO's class-code taxonomy is filed, but the rating machinery --
the endorsement, the factor table, the four `SetStopGap*` rules -- exists only where the coverage
is actually offered.

---

## 7. State deviations within the five -- the smallest surface measured, other than the form number

Beyond the endorsement form number itself (Section 1), **no rating-mechanism deviation was found
among the five states.** Same four rule names, same call order, same table structure, same two
factor values, same ILF borrow (`LookupILFPremOpsWithArgs`), same refer-to-company submission
mechanism (`ManualPremium`). The only per-state differences located:

| State | Deviation | Rating effect |
|---|---|---|
| WA | Companion form CG 04 50 (Washington Changes - Who Is An Insured) required when Stop Gap attaches, per the manual text (Section 1) | **None found in ERC** -- CG 04 50 exists as its own `Conditional` form-page entry in WA's Form Pages CSV, but no rule was located that ties its attachment to the Stop Gap endorsement being present. **Not resolved in source docs** -- whether this linkage is enforced anywhere in ERC or is a forms-issuance step outside the rating engine's scope entirely |
| ND | Calls the stat-code lookup as `LookupStopGapStatCode` (a callable rule) rather than a `SetStopGapStatCode` rule wired into `ErcRate` the way OH/WA/WY/PR do | Statistical reporting only -- no premium effect either way |
| PR | Carries an unrelated Rule A1 (Coverage For Injury To Co-Employee(s), refer-to-company) immediately before its Stop Gap Rule A2 | Different coverage, not a Stop Gap deviation -- noted only so the two are not conflated |

---

## 8. What the code (gl_engine) does -- nothing, by design, and correctly so

`grep -ri "StopGap" gl_engine/` returns **zero hits.** No Stop Gap schema field, no Stop Gap
branch, no Stop Gap referral message anywhere in `gl_engine/`. Per the project's own architecture
(confirmed true again here): **the engine contains no rating concepts** -- no per-coverage
modules -- and jurisdictional coverages like this one are content, not code, executed by the
generic ERC interpreter. There is nothing wrong to report here; an engine that special-cased Stop
Gap in Python would be the actual defect, given the architecture every other subline gate in this
project has already confirmed.

**What that means concretely for this coverage:** as long as the submission schema
(`gl_engine/schema/fields.py` or its ERC-declared equivalent) accepts a
`GeneralLiabilityStopGapEmployersLiabilityCoverageEndorsementPolLvl` block with
`LimitBodilyInjuryByAccident`, `LimitBodilyInjuryByDiseaseEachEmployee`,
`LimitBodilyInjuryByDiseaseAggregate`, `ClassificationType`, and (for the refer-to-company branch)
`ManualPremium`, the interpreter should in principle be able to rate this coverage with no new
Python. **Not resolved in source docs, and out of scope for this gate to check** -- whether the
schema layer currently declares these fields; that is a question for the engine's
field-declaration surface, not for ERC or the manual, and this gate does not touch code.

---

## 9. Endorsement forms

Per `docs/rating-engine/A3-ENDORSEMENT-CATALOG.md`, only **WA's `CG 04 42`** appears in that
catalog's state-mandatory-endorsement listing (line 629, WA row). **ND's `CG 04 40`, OH's
`CG 04 41`, WY's `CG 04 44`, and PR's `CG 04 51` are not separately catalogued there -- not
resolved in source docs** whether that is an omission in the endorsement catalog or a scope choice
(the catalog may only list forms captured from a specific notice section). WA's companion form
CG 04 50 is also not listed in that catalog.

---

## 10. Test result

**No oracle.** No payload in this repository's `Engine_Payloads/` or `Payloads/` directories was
found (not exhaustively searched -- out of scope for a documentation-only gate) carrying a
populated Stop Gap block. **Consistent with every other thin, jurisdiction-scoped coverage gated
so far** (drone, railroad, OCP) -- none has a golden-case oracle either.

| Check | Result |
|---|---|
| Manual text, all 5 states | Identical five-step algorithm, differing only in form number (Section 1) |
| ERC rule presence, all 5 states | Present -- full chain, all 5 states, all editions checked back to 2021 (Section 2) |
| ERC vs precomputed knowledge base | Knowledge base omits it; raw package tree does not (Section 0) -- a naming-pattern miss in the extraction, not a corpus gap |
| Rate-factor cells, manual vs ERC | 25/25 match (Section 4) |
| Classification-type collapse, confirmed two ways | 5-way ERC table and 2-way stat-code table agree on the same boundary (Section 3) |
| Countrywide `StopGapRate` fallback | 0 rows, at every edition checked -- the CW layer can never supply this factor |
| WV (control) | Stat-code placeholder only, no rating machinery -- corroborates the 5-state scope (Section 6) |
| `gl_engine` code references | 0 -- by design, per this project's architecture |
| Refer-to-company branch (limits differ) | Implemented as a `ManualPremium` submission field, not a message or a hard stop (Section 2) |

---

## 11. Open items

| # | Item | Detail |
|---|---|---|
| OI-STOPGAP-1 | Precomputed knowledge base (`Agentic/iso-erc-expert/knowledge/jurisdictions.json`) omits Stop Gap from `resolved_sublines` in all five states | Not a corpus gap -- a naming-pattern miss in whatever script built `resolved_sublines` (it appears to key on `GeneralLiabilityClassification<Name>CoverageRules`-shaped files and does not match the `...EndorsementPolLvlRules` shape Stop Gap uses). Fixing the knowledge extraction is out of scope for this gate (documentation-only); flagged for whoever owns that build step |
| OI-STOPGAP-2 | WA's companion-form requirement (CG 04 50 when CG 04 42 attaches) has no located ERC enforcement rule | Not resolved in source docs -- may be outside rating-engine scope entirely (a forms/issuance rule, not a premium rule) |
| OI-STOPGAP-3 | WA's newest package on disk (`20260101 V02`) predates the 2027-04-01 edition the other four states carry | Not resolved whether a newer WA package exists and simply was not pulled into this corpus, the same open-ended caveat OI-97 already logs for other states |
| OI-STOPGAP-4 | `gl_engine` schema declaration for the Stop Gap fields (`LimitBodilyInjuryByAccident`, `ManualPremium`, etc.) was not checked | Out of scope for this documentation-only gate; a code-side follow-up, not an ERC or manual question |

---

## 12. Findings

- **The knowledge base's absence was not the corpus's absence.** The precomputed
  `resolved_sublines` index -- built to make exactly this kind of question fast -- missed Stop Gap
  entirely because the extraction pattern-matches on a file-naming convention Stop Gap does not
  follow. The same lesson `GATE-335-RAILROAD-PROTECTIVE.md` recorded about searching one document
  and reporting absence from the corpus applies one layer down, to a derived index rather than a
  raw document.
- **This is the strongest per-cell manual/ERC agreement measured for a state-only coverage in this
  project.** 25 rate cells, five independently-filed state packages, one manual rule filed
  identically five times -- all agreeing to two decimal places, confirmed by direct extraction
  rather than by trusting either source's summary of the other.
- **Stop Gap is a genuine cross-coverage (E18) dependency, unlike drone's table-borrowing
  pattern.** It reads Premises/Operations' own already-computed `BaseRate` and exposure, not an
  independent lookup table -- the opposite of the pattern `GATE-370-UNMANNED-AIRCRAFT.md` found
  for the LCM/ILF/deductible tables drone borrows.
- **"Refer to company" resolved into a concrete mechanism, not a dead end.** ERC's
  `ManualPremium x PackageModFactor` branch is the same class of submission-side answer this
  project has already found for OCP's `WorkersCompensationRate` -- the manual's refer-to-company
  language does not mean ERC has nothing to say; it means the answer arrives as a field rather
  than a formula.
- **A negative control (WV) strengthened the positive finding rather than complicating it.** WV
  carries the taxonomy placeholder every state gets but none of the rating machinery -- exactly the
  shape that would exist if ISO ships the statistical-code vocabulary everywhere but only files
  the endorsement, factors, and rules in the states where the coverage is actually sold.
