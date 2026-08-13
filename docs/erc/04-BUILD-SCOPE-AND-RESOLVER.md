# ERC Build Specification — Part 1: Scope and the Resolver

> **Reconciliation note, 2026-08-11.** This document was derived clean-room from the ERC packages, in isolation from the PDF derivation and **before any subline
> was derived end to end**. The per-subline gates have since superseded or sharpened some claims
> here — see [`../gates/RECONCILIATION.md`](../gates/RECONCILIATION.md) (items R4, R6, R7). The text below is
> left as the record of what this derivation found on its own; that independence is what makes
> agreement between the two derivations evidence.

Specification for building a rating engine on the ISO ERC General Liability
corpus. Grounded entirely in what reports 01–03 established by measurement.
Every number here traces to a script in `scripts\erc\` and an intermediate in
`scripts\erc\out\`.

Parts: **04 (this) scope and resolver** · **05 data model and ingestion** ·
**06 validation, blockers and backlog**.

---

## 1. What a build on ERC gets, and what it does not

### 1.1 The headline: 4.5% of the content rates, 90.7% captures

Of the **420 distinct schema tables that write a `Premium`**
(`20_rating_structure.py`, `out/dataflow_edges.csv`):

| Behaviour | tables | share |
|---|---|---|
| `Premium = Product(ManualPremium, PackageModFactor)` — premium supplied by the user | **381** | **90.7%** |
| Premium computed from rates (`FinalRate` / `BaseRate` / exposure) | **19** | **4.5%** |
| other / mixed | 20 | 4.8% |

`ManualPremium` is **never written by any rule** — 0 of 73,990 dataflow edges
target it — and it *is* a declared input in both `Form Fields` and
`Ratebook Columns`. It is user-entered.

**An engine built on ERC can price these 19 things and no others:**

```
GeneralLiabilityClassificationPremOpsCoverage
GeneralLiabilityClassificationProdsCompldOpsCoverage
GeneralLiabilityClassificationLiquorCoverage
GeneralLiabilityClassificationOwnersContractorsCoverage
GeneralLiabilityClassificationSpecialProtectiveHighwayCoverage
GeneralLiabilityClassificationCyberIncidentLiabilityPremOpsCoverage
GeneralLiabilityClassificationCyberIncidentLiabilityProdsCompldOpsCoverage
GeneralLiabilityClassificationLossOfElectronicDataPremOpsCoverage
GeneralLiabilityClassificationLossOfElectronicDataProdsCompldOpsCoverage
GeneralLiabilityClassificationExclusionCoverageAProductWithdrawalExpense
GeneralLiabilityClassificationExclusionCoverageBProductWithdrawalLiability
GeneralLiabilityUnmannedAircraftTerrorismCoverage
GeneralLiabilityPremOpsPremiumToReachMinCoverage
GeneralLiabilityProdsCompldOpsPremiumToReachMinCoverage
GeneralLiabilityLiquorPremiumToReachMinCoverage
GeneralLiabilityOwnersContractorsPremiumToReachMinCoverage
GeneralLiabilityRailroadPremiumToReachMinCoverage
GeneralLiabilitySpecialProtectiveHighwayPremiumToReachMinCoverage
GeneralLiabilitySpecialCombinedPremiumToReachMinCoverage
```

That is the **class-rated core** (the seven rateable sublines plus cyber,
electronic-data, product-withdrawal and drone-terrorism riders) and the
minimum-premium top-ups. Everything else — every additional-insured
endorsement, every exclusion, every state-changes form — is a **premium
capture surface**: ERC supplies the form definition, the field layout, the
applicability condition and the statistical coding, and then multiplies a
number the user typed by `PackageModFactor`.

### 1.2 What this means for a build

**It is not a "GL rating engine" in the sense a business sponsor will assume.**
It is:

1. a **complete policy data model** — 1,032 schema tables, 1,877 distinct input
   fields, 486 coverages, 720 ISO form numbers, with applicability conditions;
2. a **class-rating calculator** for the 19 tables above (16 coverage groups when counted by group — see report 3 §note);
3. a **premium aggregator** that sums whatever premiums exist, however obtained;
4. a **statistical-coding engine** — 1,490 rate tables return reporting codes;
5. a **large body of jurisdictional loss-cost data** — the 24 universally
   state-overridden tables (`ProdsCompldOpsLossCost` alone has 334 distinct
   contents across 51 jurisdictions).

If the goal is "quote a full GL policy end to end without human input", ERC
does not deliver it and no amount of engineering on this corpus will. If the
goal is "rate the class-rated core correctly, model the whole policy, and route
everything else to an underwriter", ERC delivers that well.

### 1.3 The "Refer to Company" surface is the corpus telling you its own scope

The DOC workbook (`08_doc_stc_forms.py`, `out/doc_exceptions.csv`) is the only
place ERC states its limits, and it is **not machine-readable** — it is an
`.xlsx` with free-text columns:

| Sheet | rows | packages |
|---|---|---|
| `Refer to Company` | **5,300** (590 distinct form numbers) | 390 of 567 |
| `Special Consideration` | 1,113 | 532 |
| `Not Supported` | **395** | 35 |

`Not Supported` names whole capabilities, e.g. from
`countrywide/GL CW 20201201 V01`: *"Declaration Page and Policy Writing forms
are not supported"*, *"Eligibility is not supported."*, *"Split Limits are not
supported."*, and `Rule 15.D.7`: *"Interpolation procedure to be used in
determining deductible discount…"*.

> **[R7] Extended 2026-08-11.** `Refer To Co.` is one of **five** distinct meanings a `0` or a
> marker can carry, and **four now have an in-corpus discriminator** — most importantly the
> rating-basis selector `*ELPText` (**N17**), whose `Company` value is the manual's `RTC`.
> Corpus-wide agreement with the rules' own `LossCost != 0` branch test: **620,856 / 620,856** on
> Prem/Ops and **433/433 + 147/147** on OCP. Table in
> [`../gates/RECONCILIATION.md`](../gates/RECONCILIATION.md) §3.

There is also a **row-level** counterpart: the literal sentinel `Refer To Co.`
appears in **1,153 rate cells** in `PremOpsIncrdLimitTableAssignment.Assignment`
and `DomainIncreasedLimitsTableAssignmentPremOpsOverride`. A rating attempt that
lands on one of those cells has no answer.

**Requirement.** The engine must treat "refer to company" as a first-class
outcome, not an error. Three distinct triggers, all of which must surface:
(a) the form is listed in the DOC `Refer to Company` sheet;
(b) a lookup returns the `Refer To Co.` sentinel;
(c) the coverage's schema table is one of the 381 capture tables and no
`ManualPremium` was supplied.

### 1.4 Coverage of the product

11 sublines, resolved (`19_coverage_inventory.py`). Six are universal across all
52 jurisdictions; `Pollution` is absent in NY; `Electronic Data Liability`
absent in IL and NY; `Underground Storage Tank` absent in NY, TX, VA, VT;
standalone `Premises/Operations` exists in only 9 jurisdictions
(CA FL GA IL MA NJ NV NY WA); `Special Protective And Highway` is **NY only**.

**Critical ingestion consequence:** only **60 of 567 packages ship their own
subline list**; **507 inherit it from the countrywide parent**. Read a state
package alone and you see 6 jurisdictions with sublines; resolve through the
parent and you see all 52. The same effect governs coverages: a jurisdiction
declares a **median of 5** coverage pages itself but **219** resolved. Any
inventory built without the resolver is wrong by a factor of ~40.

---

## 2. The resolver

This section specifies the only correct way to materialise the effective
content for one jurisdiction as of one date. All mechanics were measured in
`18_composition.py` / `out/composition.txt`.

### 2.1 Package identity — from content, never from path

**Rule R1.** A package's identity is the `targetNamespace` of its single
`DataDefs/*.xsd`:

```
http://www.verisk.com/iso/erc/GL_<JJ>_<YYYYMMDD>_<Vnn>/MasterGL<JJ>
```

`16_self_dating.py` verified this yields the complete
(jurisdiction, edition, version) triple for **567 of 567** packages and matches
the directory name in **567 of 567**. Five corroborating channels agree (XSD
filename, DOC filename, STC `SchemeKeys`, the `StateCode` column, the
`GL<JJ>.Metadata.xml` filename); where two are available they disagree in
**0** cases.

**Do not key on the directory.** Before remediation, two packages were filed
under the wrong jurisdiction (a DE package under `GA/`, a PR package under
`RI/` — and PR's newest edition existed *only* under `RI/`). Those are fixed in
the current tree, but the rule stands: the filesystem is redundant metadata and
has been wrong.

**Rule R2.** Deduplicate by package id, not by path. **5 package ids still
occupy two directories each** (`GL_AL_20260701_V01`, `GL_CA_20241101_V01`,
`GL_LA_20260701_V02`, `GL_MI_20260501_V01`, `GL_OH_20260601_V02`), each pair
proven byte-identical by recursive tree hash (`15_integrity.py`).

### 2.2 Edition selection — as-of, never "latest"

**Rule R3.** Order a jurisdiction's packages by `(edition_date, version)`.
**45 (jurisdiction, edition) pairs carry more than one version, covering 102
packages** — the version token is required to break the tie, and only the XSD
namespace and DOC filename supply it.

**Rule R4.** Select the newest package whose `edition_date <= rating_date`.
**Never take the maximum.** 83 of 572 package directories carry an edition date
after 2026-08-10, concentrated on 20270401 (61 packages). These are
future-*effective* filings and the corpus is internally coherent about them:
for all 566 packages citing a circular, **the latest cited circular effective
date is ≤ the package's own edition date in 566 of 566 cases**.

**Rule R5.** Editions are **cumulative full snapshots**, not deltas
(`12_edition_diff.py`): carry-over between consecutive editions is 92.7%–98.3%
in every category across 515 pairs. Load exactly one edition. Never merge two
editions of the same jurisdiction.

Corollary, and the reason R5 is safe: across all 515 consecutive pairs, **600
of 600 "dropped" state tables were still present in the countrywide package the
new edition imports, and were already present before the drop**. Nothing is
ever lost; a drop is the withdrawal of a state override.

### 2.3 Parent resolution

**Rule R6.** Every package has **exactly one** `xs:import`. A state package
imports one specific countrywide package by namespace:

```xml
<xs:import schemaLocation="erc://GL_CW_20231201_V02/MasterGLCW"
           namespace="http://www.verisk.com/iso/erc/GL_CW_20231201_V02/MasterGLCW" />
```
(`NJ/GL_NJ 20250301 V01_MachineReadableContent/GL NJ 20250301 V01/DataDefs/MasterGLNJ.DataDef.xsd`)

Resolve that exact package. **Never substitute a different countrywide
edition.** The graph is exactly closed — 10 countrywide packages referenced, 10
present, 0 missing, 0 orphaned — and across **51,983 rule-level `ProjectName`
references there are 0 disagreements with the XSD import**
(`06_resolve_refs.py`, re-verified post-remediation).

The 10 countrywide packages import a namespace called **`ErcCore`**, which is
**not in the corpus** (searched by filename across the whole tree: 0 hits). See
part 06 §3.

### 2.4 Overlay — by name, wholesale

**Rule R7.** Load the countrywide package first, then overlay the state package
name by name, independently for: rate tables, domain tables, rule files/rules,
form pages, form fields, related fields, ratebook columns, ratebook tables.
State wins on collision.

**Rule R8.** A shadowed table is **replaced entirely**. Never merge rows from
both copies. Evidence: of 21,694 tables present in both layers, only **36
(0.17%)** are byte-identical — a shadow is always a real, different table.

**Rule R9.** The overlay matters and is not optional. Of the lookups issued by
state-package rules (excluding the engine-provided `Pages` matrix), **10.88%
name a table that exists in both layers, and in every one of those cases the two
copies differ** (374 lookups; 0 identical). Picking the wrong layer changes the
answer every time.

Typical shape of the result, per state package: ~485 tables inherited only from
countrywide, ~36 shadowed, ~3 state-only.

### 2.5 Rule dispatch — the call-super trap

**Rule R10.** The `RuleType*` MetadataCode on every `<Rule>` is an exact,
machine-checkable declaration (`18_composition.py`, zero exceptions in either
direction over 557 state packages):

| Tag | meaning | occurrences | shadows a parent rule |
|---|---|---|---|
| `RuleTypeOverridden` | replaces a rule of the same (file, name) in the parent | 23,404 | **100.0%** |
| `RuleTypeStateSpecific` | novel; no parent counterpart | 23,755 | **0.0%** |
| `RuleTypeSystem` | plumbing | 23,743 | 34.6% |
| `RuleTypeCountrywide` | base logic; **only ever in countrywide packages** | 32,517 | n/a |

`RuleTypeCountrywide` never appears in a state package;
`RuleTypeOverridden` / `RuleTypeStateSpecific` never appear in a countrywide
package.

**Rule R11 — the single most dangerous mechanic in the corpus.** A `RunRule`
carrying a `ProjectName` attribute must be dispatched **to that named package's
copy, bypassing the overlay**. It is an explicit call-super.

Of the 23,404 `RuleTypeOverridden` rules: **17,556 (75.0%) replace outright**,
**4,598 (19.6%) call back into the parent's rule of the same name**, and 1,250
(5.3%) call a different parent rule. `RuleTypeSystem` inverts this: 7,648 of its
8,205 shadowing rules (93.2%) are call-super.

The canonical form:

```xml
<rul:Rule Name="InitializeRuleSet" DataDefGroup="GeneralLiabilityClassificationPremOpsCoverage"
          MetadataCodes="RuleTypeSystem">
  <rul:Sequence>
    <rul:RunRule Type="none" FileName="GeneralLiabilityClassificationPremOpsCoverageRules"
                 Rule="InitializeRuleSet" ProjectName="GL CW 20231201 V02" ClearCache="true" />
```
(`NJ/GL_NJ 20250301 V01_MachineReadableContent/GL NJ 20250301 V01/Rules/GeneralLiabilityClassificationPremOpsCoverageRules.Rule.xml`)

**If a resolver treats this as a normal call and re-enters the overlay, it
re-enters the state rule and recurses forever.** This affects 12,246 rules
(4,598 + 1,250 + 7,648 minus the 557 top-level replacements' siblings — see
`out/composition.txt` for the exact split). `ProjectName` is present on 51,983
of 172,712 `RunRule` nodes.

**Rule R12.** A `RunRule` **without** `ProjectName` resolves against the
overlay: state copy first, then parent.

**Rule R13.** `<Lookup>` never carries a package qualifier in the corpus.
Resolve `MatrixFromConstant` against the overlay (state first, then parent),
with one exception: `MatrixFromConstant="Pages"` (45,592 lookups) is not a
shipped table — it is the `Form Pages/Pages.FormPage.csv` content, which the
rule engine reads as a matrix on the `Name` and `Number` columns.

### 2.6 Entry points and execution order

**Rule R14.** There are exactly two roots, both present in all 567 packages
(`23_rule_program.py`):

- `GeneralLiabilityRules / ErcProcess` — the rating pass
- `GeneralLiabilityRules / ErcCalculateTotalPremium` — the aggregation pass

The call graph is a **DAG — 0 back-edges** measured on `GL_CW_20270401_V01` —
with **max depth 8**, 3,888 of 4,528 rules reachable from `ErcProcess`, and
fan-out up to 828.

Top-level `ErcProcess` sequence
(`countrywide/GL CW 20260101 V01/Rules/GeneralLiabilityRules.Rule.xml`):

```
ErcSetRatesAndFactors
ForEach location: InitializeRuleSet, CallErcSetRatesAndFactors
ErcDoConditionalMandatoryLogic
ErcDoOptionalConditionalLogic
ErcSetPostRatesAndFactors
SetModFactors
ForEach <every child table>: InitializeRuleSet, ErcProcess   (recursive descent)
```

Leaf `ErcRate` sequence
(`…/GeneralLiabilityClassificationPremOpsCoverageRules.Rule.xml`):

```
SetFinalRate → SetMedicalPaymentsCharge → SetAdditionalInterestFactor
→ SetMinimumPremium → SetMinPremium → SetSpecialCombinedMinimumPremium
→ SetSpecialCombinedMinPremium → SetPremium → SetPremiumIndicator
```

Then `ErcCalculateTotalPremium` runs `CalculateTotalPremium`, which is a
`Sum ToDataDef="ErcCalculatedTotalPremium"` over a `ForEach` of every child
table's own `CalculateTotalPremium`.

There are exactly **ten** `Erc*` rule names corpus-wide: `ErcProcess`,
`ErcRate`, `ErcSetRatesAndFactors`, `ErcSetPostRatesAndFactors`,
`ErcDoConditionalMandatoryLogic`, `ErcDoOptionalConditionalLogic`,
`ErcRunUnderwritingLogic`, `ErcRunPostUnderwritingLogic`,
`ErcSetStatisticalCodes`, `ErcCalculateTotalPremium`.

### 2.7 The resolver in sequence

```
resolve(jurisdiction J, rating_date D) -> EffectiveContent

 1. candidates = packages where identity.jurisdiction == J        # from XSD ns
 2. dedupe candidates by identity (5 ids have two directories)
 3. candidates = [p for p in candidates if p.edition_date <= D]
    if empty -> ERROR "no package in force for J as of D"
 4. state = max(candidates, key=(edition_date, version))
 5. parent = resolve_package(state.xsd_import)                    # exactly one
    if parent missing -> ERROR (should never happen: graph is closed)
 6. for each category in {RateTables, DomainTables, Rules, FormPages,
                          FormFields, RelatedFields, RatebookColumns,
                          RatebookTables}:
        effective[category] = parent[category] overlaid by state[category],
                              keyed by name, state wins, NO row merging
 7. retain both layers addressable by package id — required for R11 dispatch
 8. entry points: (GeneralLiabilityRules, ErcProcess) then
                  (GeneralLiabilityRules, ErcCalculateTotalPremium)
```

Step 7 is not optional. The overlay alone is insufficient because
`ProjectName`-qualified dispatch must reach the parent's copy of a rule that the
overlay has shadowed.

### 2.8 What the resolver does *not* establish

Referential completeness is not semantic sufficiency. `06_resolve_refs.py`
proves that of 227,685 references, the only unresolved targets are two
engine primitives (`Pages` ×45,592, `MessageHelper.AddErrorMessage` ×4,375) —
so excluding those, **closure is 100.000%**: every `Lookup` and `RunRule`
resolves inside the state package or its imported parent.

That proves no dangling reference. It does **not** prove that a rating
terminates with a premium for every valid input. That has not been tested and
cannot be without an engine. See part 06 §3.6.
