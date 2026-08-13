# ISO ERC General Liability — Composition, Product Inventory, Rating Structure

> **Reconciliation note, 2026-08-11.** This document was derived clean-room from the ERC packages, in isolation from the PDF derivation and **before any subline
> was derived end to end**. The per-subline gates have since superseded or sharpened some claims
> here — see [`../gates/RECONCILIATION.md`](../gates/RECONCILIATION.md) (items R4, R5, R6). The text below is
> left as the record of what this derivation found on its own; that independence is what makes
> agreement between the two derivations evidence.

Third report. Same clean-room constraint: everything below derives from the ERC
packages under `C:\Projects\ISO_ERC_Files\General_Liability\`. No excluded path
was opened, and no outside knowledge of the line of business was used — the
product taxonomy in §2 is read out of the data, not supplied from memory.

`C:\Projects\ISO_ERC_Files\` remains **read-only** to me. Nothing was moved,
renamed or written.

## 0. Corpus re-derived after the remediation

I re-ran the enumerator with `_quarantine_misfiled/` excluded
(`00_common.py: EXCLUDE_DIRS`) rather than carrying prior counts forward.

| Measure | Report 1/2 | Now |
|---|---|---|
| Package **directories** | 573 | **572** |
| Distinct packages | 567 | **567** |
| Countrywide / state directories | 10 / 563 | **10 / 562** |
| Files inside packages | 86,746 | **86,664** |
| Bytes inside packages | 705,016,342 | **704,515,670** |
| `.zip` archives (excluding quarantine) | 508 | **507** |
| Packages whose directory jurisdiction ≠ package-name jurisdiction | **2** | **0** |
| Duplicate `pkg_id` (identical trees) | 6 | **5** |
| PR editions reachable under `PR/` | 7 of 8 | **8 of 8** (incl. 20270401 V02) |
| RI packages under `RI/` | 9 (one was PR) | **8, all RI** |
| GA package directories | 16 (one was DE) | **15** |

The remediation is independently confirmed: **zero misfiled packages remain**,
PR's newest edition is now under `PR/`, and the distinct-package count is
unchanged at 567 — the quarantined DE package was a byte-identical duplicate,
so no content was lost. Table/rule/form counts moved only by the one duplicate
directory (rate tables 23,975 → 23,945; rules 20,802 → 20,794 files;
12,866,232 → 12,853,103 data rows).

New scripts:

| Script | Produces |
|---|---|
| `18_composition.py` | `composition.csv`, `composition.txt` — override mechanics |
| `19_coverage_inventory.py` | `coverage_matrix.csv`, `coverage_pages.csv`, `coverage_inventory.txt` |
| `20_rating_structure.py` | `input_surface.csv`, `table_shapes.csv`, `dataflow_edges.csv`, `rating_structure.txt` |
| `21_variation_surface.py` | `variation_tables.csv`, `variation_rules.csv`, `variation_by_juris.csv`, `variation_surface.txt` |
| `22_territory.py` | `territory_by_juris.csv`, `territory_vocab.csv`, `territory.txt` |
| `23_rule_program.py` | `rule_roots.csv`, `rule_program.txt` |

---

## 1. The composition model in practice

### 1.1 `Overridden` and `StateSpecific` are distinct mechanisms, and the tag is exact

`18_composition.py` cross-tabulates the `RuleType*` MetadataCode on every
`<Rule>` in all 557 state packages against whether a rule of the same
(file, name) exists in the countrywide package that state's `.xsd` imports:

| RuleType tag | shadows a parent rule | novel | total | shadow % |
|---|---|---|---|---|
| `RuleTypeOverridden` | 23,404 | 0 | 23,404 | **100.0%** |
| `RuleTypeStateSpecific` | 0 | 23,755 | 23,755 | **0.0%** |
| `RuleTypeSystem` | 8,205 | 15,538 | 23,743 | 34.6% |

**Zero exceptions in either direction.** `RuleTypeOverridden` means exactly
"a rule of this name exists in my parent and I am replacing it";
`RuleTypeStateSpecific` means exactly "no parent counterpart exists". The tag
is a reliable, machine-checkable declaration, not a comment.

The four tags also partition perfectly by package kind:

```
countrywide packages : RuleTypeCountrywide 32,517  RuleTypeSystem 10,736
state packages       : RuleTypeOverridden 23,588  RuleTypeStateSpecific 23,963
                       RuleTypeSystem     23,922
```

`RuleTypeCountrywide` **never** appears in a state package and
`RuleTypeOverridden`/`RuleTypeStateSpecific` **never** appear in a countrywide
package.

### 1.2 An override is usually a full replacement, not a call-super

For the 23,404 `RuleTypeOverridden` rules:

| Behaviour | count | share |
|---|---|---|
| replaces the parent rule outright (no call back) | **17,556** | 75.0% |
| calls back into the parent's **same** rule (`RunRule ProjectName=<parent>` with the same file+rule) | 4,598 | 19.6% |
| calls a **different** parent rule | 1,250 | 5.3% |

`RuleTypeSystem` behaves oppositely: of its 8,205 shadowing rules, **7,648
(93.2%) are call-super**, and exactly **557 replace** — one per state package.
That 557 is the top-level `GeneralLiabilityRules/InitializeRuleSet`, the only
place a state takes over the bootstrap. The canonical call-super looks like:

```xml
<rul:Rule Name="InitializeRuleSet" DataDefGroup="GeneralLiabilityClassificationPremOpsCoverage" MetadataCodes="RuleTypeSystem">
  <rul:Sequence>
    <rul:RunRule Type="none" FileName="GeneralLiabilityClassificationPremOpsCoverageRules"
                 Rule="InitializeRuleSet" ProjectName="GL CW 20231201 V02" ClearCache="true" />
```
(`NJ/GL_NJ 20250301 V01_MachineReadableContent/GL NJ 20250301 V01/Rules/GeneralLiabilityClassificationPremOpsCoverageRules.Rule.xml`)

Note the mechanism: **delegation is explicit and by name**, carrying the parent
package id in `ProjectName`. There is no implicit "call the base implementation".

### 1.3 Tables override by name; the shadow is always real

| | total |
|---|---|
| tables present only in the countrywide parent (state inherits) | 266,932 |
| tables present in both (state shadows) | 21,694 |
| …of those, **byte-identical** to the parent's copy | **36 (0.17%)** |
| tables present only in the state package | 3,673 |

Override is **by table name**, not by key: a state ships a whole replacement
table, never a partial row-set patch. This is confirmed by §1.4 — no lookup
ever merges two copies.

### 1.4 Resolution order, measured

A `<Lookup>` names a table by `MatrixFromConstant` and carries no package
qualifier in the overwhelming majority of cases. Resolving state-first-then-
parent over all state packages (excluding the 45,592 lookups against the
engine-provided `Pages` matrix):

| Where the named table is found | lookups | share |
|---|---|---|
| state package only | 2,589 | 75.28% |
| countrywide parent only | 476 | 13.84% |
| **both, with different content** | **374** | **10.88%** |
| both, identical content | **0** | 0.00% |

So the local-first choice is not academic: for **10.88%** of lookups both copies
exist and they **always differ** — picking the wrong one changes the answer
every time. There is no case where the choice is moot.

### 1.5 Schema-level inheritance

Of 26,096 state `complexType` declarations: 7,305 use `xs:extension` on a type
in the parent namespace (`base="a:…"`), 7,771 extend a locally-declared type,
and 11,020 declare no base. So the XSD carries genuine type inheritance from
countrywide, in parallel with the rule- and table-level overriding.

### 1.6 What a correct resolver must do, in sequence

Derived from §1.1–1.5 (this is a description of the observed mechanics, not a
design proposal):

1. **Identify the package** from the `.xsd` `targetNamespace` — 100% reliable
   (report 2 §4). Do not key on directory.
2. **Select the edition** *as-of* the rating date, not "latest": 83 packages are
   future-effective (report 2 §3.6). Order by (edition date, version); 45
   (jurisdiction, edition) pairs need the version token to break ties.
3. **Resolve the parent** by reading the single `xs:import` — the state package
   names one specific countrywide package. Never substitute another edition;
   the corpus never does (**0 disagreements across 51,983 `ProjectName` refs**, re-verified on the post-remediation tree by `06_resolve_refs.py`).
4. **Load countrywide first, then overlay the state package**, name by name,
   for each of: rate tables, domain tables, rule files/rules, and form rows.
   State wins on collision.
5. **Do not merge table contents.** A shadowed table is replaced wholesale.

> **[R6] Extended 2026-08-11 by gate 336.** Wholesale replacement includes **replacement by
> nothing**: 13 jurisdictions disable Defense-Within-Limits with a literal
> `<rul:Rule Name="…" MetadataCodes="RuleTypeOverridden"><rul:Sequence /></rul:Rule>`.
> **Empty ≠ absent ≠ inherit** — treating an empty body as fall-through applies a factor those
> states filed away. Six jurisdictions (CA FL GA KY VA WA) have since retired that override, so the
> answer is also edition-dependent.
6. **Honour explicit delegation.** A `RunRule` carrying `ProjectName` must be
   dispatched to that package's copy, *not* to the overlay — otherwise the
   19.6% of overrides that call-super become infinite recursion.
7. **Deduplicate by package id**, not by path: 5 package ids still occupy two
   directories each.

---

## 2. Coverage and product inventory

### 2.1 Sublines — stated by the data, and it demonstrates the composition model

Only **60 of 567** packages ship their own `Subline` domain/rate table. The
other **507 inherit it from their countrywide parent** — so the unresolved view
sees 6 jurisdictions and the resolved view sees all 52. Resolved, the corpus
states **11 sublines**:

| Subline | packages | jurisdictions (latest edition) |
|---|---|---|
| Premises/Operations and Products/Completed Operations | 567 | 52 |
| Products/Completed Operations | 567 | 52 |
| Liquor | 567 | 52 |
| Owners and Contractors | 567 | 52 |
| Railroad | 567 | 52 |
| Product Withdrawal | 567 | 52 |
| Pollution | 557 | 51 (absent: **NY**) |
| Electronic Data Liability | 539 | 50 (absent: **IL, NY**) |
| Underground Storage Tank | 535 | 48 (absent: **NY, TX, VA, VT**) |
| Premises/Operations *(standalone)* | 508 | 9 (**CA FL GA IL MA NJ NV NY WA**) |
| Special Protective And Highway | 10 | **1 (NY only)** |

Six sublines are universal. `Premises/Operations` as a *standalone* subline
exists in only 9 jurisdictions — elsewhere it is only sold combined with
Products/Completed Operations. `Special Protective And Highway` is unique to NY.

### 2.2 Coverages (Form Pages `Type='Coverage'`)

Unresolved, a jurisdiction's own package declares a median of **5** coverages.
Resolved against its countrywide parent, the median is **219**:

| | min | median | max |
|---|---|---|---|
| coverages declared by the state package alone | 0 | 5 | 216 |
| **resolved (state + countrywide parent)** | **215** | **219** | **250** |

486 distinct coverages across the resolved sets; **179 present in all 52
jurisdictions**, **232 present in exactly one**. Seven jurisdictions add no
coverage of their own at all. The single-jurisdiction ones are overwhelmingly
state-named endorsements — e.g. `Alaska Changes - Attorney's Fees`,
`Alaska Changes - Binding Arbitration`, `Alaska Earth Movement - Exclusion For
Designated Operation(s) Or Project(s)`. 9,155 coverage rows carry **720
distinct ISO form numbers**.

### 2.3 The structural level of every artefact (`DataDefInfo` `Type`)

| Type | entries |
|---|---|
| Form | 12,696 |
| Coverage | 3,326 |
| Schedule | 1,895 |
| Risk | 898 |
| Policy | 572 (exactly one per package) |

A five-level tree: **Policy → Risk → Coverage → Schedule**, with **Form** tables
attached at whatever level applies.

### 2.4 Rating weight by coverage family

Scanning the 450 rate-table names, 375 domain-table names and 1,032
DataDefGroups for the subline tokens found in §2.1:

| Family | rate tables | domain tables | datadef groups |
|---|---|---|---|
| Premises/Operations | 128 | 48 | 53 |
| Increased Limits / ILF | 54 | 28 | 0 |
| Products/Completed Operations | 42 | 50 | 120 |
| Terrorism | 25 | 22 | 27 |
| Unmanned Aircraft (drones) | 23 | 11 | 22 |
| Liquor | 17 | 35 | 73 |
| Product Withdrawal | 13 | 3 | 54 |
| Owners and Contractors | 11 | 15 | 54 |
| Electronic Data Liability | 8 | 7 | 40 |
| Pollution | 7 | 10 | 73 |
| Railroad | 6 | 12 | 30 |
| Underground Storage Tank | 4 | 9 | 26 |
| Special Protective And Highway | 4 | 10 | 6 |
| Medical Payments | 3 | 2 | 10 |
| Cannabis | 1 | 0 | 22 |
| Composite rating | 1 | 0 | 1 |
| Deductibles | 2 | 12 | 3 |
| *(unclassified)* | 154 | 132 | 518 |

**Cross-check:** every one of the 11 stated sublines has rating tables behind
it. The reverse does not hold — Terrorism, Unmanned Aircraft, Increased Limits,
Deductibles, Cannabis and Composite Rating carry substantial rating content but
are **not** sublines; they are modifiers and endorsements that attach to a
subline. The 518 unclassified DataDefGroups are dominated by
`GeneralLiabilityAddlInsd*` (additional-insured endorsements) — see §3.4.

---

## 3. The rating structure

### 3.1 The input surface

| Source | measure |
|---|---|
| `Form Fields` rows | 30,322 |
| distinct (TableName, ColumnName) | **1,877** |
| declared widget types | TEXT 19,457 · SELECT 7,656 · CHECKBOX 1,794 · HIDDEN 568 · TEXTAREA 468 · BUTTON 372 · ANCHOR 7 |
| pages carrying input fields | 701 |
| `Ratebook Columns` distinct (TableName, ColumnName) | **765** |
| rows carrying a `RatingRequiredCondition` (XPath) | 4,977 |

The three universal data-entry pages are **Policy Detail** (4,464 fields),
**Location Detail** (2,645) and **Classification Detail** (2,423) — which is
also the risk hierarchy. Everything else is a state-changes page
(`Illinois Policy Changes` 504, `Montana Policy Changes` 435, …) or a coverage
detail page.

**No rating input is present in all 52 jurisdictions** (`Ratebook Columns`
resolved per package), and **428 are present in exactly one**. The rating input
surface is itself heavily state-varying — but note this is the *unresolved*
count; the shared inputs live in the countrywide layer.

### 3.2 Table shapes

Classifying all 30,773 table defs by their declared value-column names and key
structure:

| kind | shape | tables |
|---|---|---|
| Rate | factor / multiplier | 11,343 |
| Rate | loss cost / rate | 8,251 |
| Domain | text / description | 3,720 |
| Domain | *(no Def — the default `StateCode/DisplayValue/DataValue` shape)* | 3,056 |
| Rate | statistical / code | 1,490 |
| Rate | **table assignment (indirection)** | 1,174 |
| Rate | text / description | 623 |
| Rate | *(unclassified)* | 454 |
| Rate | premium / money | 428 |
| Rate | **step / banded** (`<Range>` key) | 164 |
| Domain | premium+text | 52 |
| Rate | **interpolated band** (`InterpolateMode="Linear"`) | 18 |

Five genuinely distinct shapes: **flat keyed lookup** (the bulk),
**banded/step** (a `<Range>` key expressed as `_From`/`_ToLessThan` columns),
**interpolated band** (the 18 size-of-risk relativity tables),
**table assignment** — a table whose *value* is the name of another table to
consult next, i.e. runtime indirection — and **statistical code** tables that
return reporting codes rather than numbers.

**Lookup dimensions** — 221 distinct key-column names, with a very skewed
distribution:

| key column | table defs |
|---|---|
| `StateCode` | 27,717 (present in 90% of all defs) |
| `ClassCodeCGLProds` | 6,691 |
| `ClassCodeOwnersContrctrs` | 4,376 |
| `ClassCodeLiquor` | 2,300 |
| `ClassCodeRailroad` | 1,796 |
| `ClassCode` | 1,754 |
| `EachOccurrenceLimit` | 1,354 |
| `GeneralAggregateLimit` | 1,269 |
| `PremOpsTerr` | 1,137 |
| `ProdsCompldOpsTerr` | 896 |

Key arity: 2 keys 18,396 tables · 3 keys 6,634 · 4 keys 2,256 · 5 keys 319 ·
6 keys 102 · 10 keys 10 · 0 keys 3,056 (the Def-less domain tables).
**Only 2 of the 221 key columns are used by a single table def** — the
dimension vocabulary is highly shared.

So the rating dimensions are, in order of weight: **jurisdiction → class code
(per subline) → limit → territory → deductible → coverage form**.

### 3.3 The premium algorithm, derived mechanically

`20_rating_structure.py` parses every node that writes a value (`ToDataDef`)
into an edge `target ← op(sources)`: **73,990 edges, 418 distinct targets**.
Operators used to write: Constant 23,835 · FirstNonNull 22,694 · RunRule 10,621
· Product 6,476 · Guid 4,347 · Sum 2,837 · Copy 2,122 · Round 364 · Convert 253
· Subtract 203 · PadLeft 150 · Divide 88.

Walking the graph backwards from `Premium` gives the algorithm without
interpretation:

```
BaseRate      = Product(LossCost | ELP, LCM [, ClaimsMadeMultiplier])
FinalILF      = Round(ILF, DeductibleFactor)     or Round(CSLILF, FinalDeductibleFactor)
FinalDeductibleFactor = Sum(BIDeductibleFactor, PDDeductibleFactor)  or Copy(one of them)
FinalRate     = Product(BaseRate, FinalILF, PackageModFactor,
                        ExperienceRatingModificationFactor, ExpenseModification,
                        ModToUse [, SizeOfRiskFinalRelativity] [, PremiumDiscountCharge])
BasicLimitPremium = Product(BaseRate, FinalDeductibleFactor, PackageModFactor,
                            <Subline>CovExposure [, SizeOfRiskFinalRelativity])
Premium       = Round(Product(FinalRate, <Subline>CovExposure) + MedicalPaymentsCharge, 0)
ErcCalculatedTotalPremium = Sum(Premium, PremiumIndicator) over every coverage row
```

> **[R4/R5] Sharpened 2026-08-11 by gates 334, 336 and 335.** This chain is correct for
> Premises/Operations and Products/Completed Operations, and the golden case reproduces on it to
> the dollar. Three qualifications the gates added:
>
> - **`MedicalPaymentsCharge` is edition-scoped.** Editions through `GL_CW_20231201_V03` add it
>   inside `SetPremium`, as written above. **`GL_CW_20270401_V01` has no such rule** — it folds
>   med-pay into the ILF instead, `FinalILF = Round(CSLILF + MedicalPaymentsFactor − 1 −
>   FinalDeductibleFactor, 3)`. Algebraically identical, **rounds differently — about $1 a line.**
>   The chain is therefore edition-scoped, not just the rate tables (gate 334 §0).
> - **`Product(FinalRate, CovExposure)` divides the exposure by 1000** for nine premium bases
>   (Admissions, Area, Gallons, Gross Sales, Kilowatt-hours, Payroll, Total Cost, Total Operating
>   Expenses, Vehicles — ten before 2027, which dropped Passenger Days). Under CW 2027 a premium
>   computing to `0` with exposure `> 0` is **floored at `$1`**.
> - **It is not the general chain.** Subline 335 (OCP) is **piecewise-linear** — two marginal tiers
>   with a class-dependent breakpoint (`$1,000,000`, or `100 units` for the pre-2027 classes
>   `27111`/`27112`) and a class-dependent divisor, reading six rate tables (gate 335 §1). The
>   premium step is a per-subline strategy, never a shared `rate × exposure` helper.
>
> See [`../gates/RECONCILIATION.md`](../gates/RECONCILIATION.md) §2.

Cited: `countrywide/GL CW 20260101 V01/Rules/GeneralLiabilityClassificationPremOpsCoverageRules.Rule.xml`,
rules `SetBaseRate`, `SetFinalRate`, `SetBasicLimitPremium`, `SetPremium`; and
`countrywide/GL CW 20270401 V01/Rules/GeneralLiabilityRules.Rule.xml`, rules
`ErcCalculateTotalPremium`, `CalculateTotalPremium`.

`SetFinalRate` verbatim (the size-of-risk branch):

```xml
<rul:Product ToDataDef="FinalRate" DecimalPlaces="3">
  <rul:FirstValue Type="decimal" FromConstant="0.0" FromDataDef="BaseRate" .../>
  <rul:FirstValue ... FromDataDef="FinalILF" .../>
  <rul:FirstValue ... FromDataDef="PremOpsSizeOfRiskFinalRelativity" .../>
  <rul:FirstValue ... FromDataDef="../../../../../PackageModFactor" .../>
  <rul:FirstValue ... FromDataDef="../../../../../ExperienceRatingModificationFactor" .../>
  <rul:FirstValue ... FromDataDef="../../../../../ExpenseModification" .../>
  <rul:FirstValue ... FromDataDef="../../../../../ModToUse" .../>
</rul:Product>
```

The `../../../../../` navigation shows factors being pulled from the **policy**
level down into a **classification-coverage** row — five levels up the tree.

**Exposure and premium basis.** `PremiumBasis` is copied from the
classification's declared basis; its vocabulary is enumerated inline in
`SetPremium`/`SetBasicLimitPremium` as: **Admissions, Area, Gallons, Gross
Sales, Passenger Days, Payroll, Total Cost, Total Operating Expenses,
Vehicles**. The exposure amount is a per-coverage field
(`PremOpsCovExposure`, `ProdsCompldOpsCovExposure`, …).

### 3.4 Most of the content does not rate — it passes a premium through

This is the single most consequential finding of this report. Of the **420
distinct schema tables that write a `Premium`**:

| | tables | share |
|---|---|---|
| **`Premium = Product(ManualPremium, PackageModFactor)`** — the user supplies the premium | **381** | **90.7%** |
| computes the premium from rates (`FinalRate`/`BaseRate`/exposure) | **19** | 4.5% |
| other / mixed | 20 | 4.8% |

`ManualPremium` is **never written by any rule** (0 of 73,990 edges target it)
and **is a declared `Form Fields` / `Ratebook Columns` input**. It is a
user-entered value.

The 19 tables that genuinely rate are the classification-level coverages: *(Verified corpus-wide 2026-08-10: counting **coverage groups** rather than schema tables gives **16 RATE_DRIVEN / 383 CAPTURE / 78 aggregators** across 477 groups — same substance, different unit. It also surfaced three **state-specific** rating coverages, MD and MA lead, that a countrywide-only reading misses. See `scripts/erc/25_rating_vs_capture.py`.)* *(Amended 2026-08-11: **18 / 383 / 76**. The classifier's rate-source list omitted `AdjustedRate`, filing both Unmanned Aircraft coverages as aggregators; and the state-specific count is **four**, not three — NY Special Protective and Highway was missed because its group name carries no state. `docs/gates/OI-40-ASOF-RECOUNT.md` §5, `docs/PHASE-SIZING.md` §5.)*

```
GeneralLiabilityClassificationPremOpsCoverage
GeneralLiabilityClassificationProdsCompldOpsCoverage
GeneralLiabilityClassificationLiquorCoverage
GeneralLiabilityClassificationOwnersContractorsCoverage
GeneralLiabilityClassificationSpecialProtectiveHighwayCoverage
GeneralLiabilityClassificationCyberIncidentLiabilityPremOps / ProdsCompldOps Coverage
GeneralLiabilityClassificationLossOfElectronicDataPremOps / ProdsCompldOps Coverage
GeneralLiabilityClassificationExclusionCoverageA ProductWithdrawalExpense
GeneralLiabilityClassificationExclusionCoverageB ProductWithdrawalLiability
GeneralLiabilityUnmannedAircraftTerrorismCoverage
+ 7 *PremiumToReachMinCoverage rules (minimum-premium top-ups)
```

So ERC automates the **class-rated core** and treats the ~380 endorsement /
additional-insured tables as premium pass-throughs. This dovetails exactly with
the DOC exception register (report 1 §2.7): 5,300 "Refer to Company" rows across
591 form numbers.

---

## 4. The state-variation surface

### 4.1 Where the jurisdiction axis bites

**Tables** — 825 distinct artefacts:

| class | count | share |
|---|---|---|
| countrywide-only (no state ever ships its own) | **337** | 40.8% |
| state-only (never in countrywide) | 288 | 34.9% |
| sometimes-overridden | 176 | 21.3% |
| universally-overridden (every state ships its own) | **24** | 2.9% |

**Rules** — 7,299 distinct (file, name) artefacts:

| class | count | share |
|---|---|---|
| countrywide-only | **3,682** | 50.4% |
| state-only | 2,436 | 33.4% |
| sometimes-overridden | 1,176 | 16.1% |
| universally-overridden | 5 | 0.1% |

292 tables and 2,337 rules exist in **exactly one jurisdiction**.

### 4.2 The 24 universally-overridden tables — the loss-cost layer

Every one of the 51 state jurisdictions ships its own copy of these, and the
contents differ widely:

| table | jurisdictions | distinct contents |
|---|---|---|
| `ProdsCompldOpsLossCost` | 51 | **334** |
| `ILFProds` | 51 | 178 |
| `ProductWithdrawalExpensesAndLiabilityIncrdLimitFactor` | 51 | 128 |
| `IncreasedLimitsTableAssignmentProdsCompldOps` | 51 | 111 |
| `PremOpsHomogeneityIndex` / `PremOpsELPText` | 51 | 110 |
| `ProdsCompldOpsELPFactor` / `ProdsCompldOpsELPText` | 51 | 109 |
| `OwnersContractorsELP` / `…ELPOverOneMillion` / `LiquorELPText` | 51 | 94 |
| `RailroadELP` / `RailroadHomogeneityIndex` / `OwnersContractorsLossCostOverOneHundred` | 51 | 51 |

The pattern is exact: **loss costs, ELPs, homogeneity indices and increased-limit
factors are always state-supplied; the algorithm that consumes them is always
countrywide.** The 337 countrywide-only tables are never touched by any state.

### 4.3 Override volume by jurisdiction

Per jurisdiction (latest edition), the range is very wide:

| measure | min | median | max |
|---|---|---|---|
| rules overridden (`RuleTypeOverridden`) | 7 | ~23 | 77 |
| state-specific rules | 7 | ~48 | 82 |
| tables shipped only by the state | 0 | ~1 | 22 |
| tables shadowing a countrywide table | 29 | ~34 | 53 |
| tables inherited only from countrywide | 471 | ~507 | 508 |

Examples: **AL** overrides 7 rules and adds 7; **CA** overrides 77, adds 68, and
ships 22 tables of its own; **AK** overrides 62 and adds 82. So a jurisdiction
is between ~1% and ~10% divergent from countrywide by rule count, and
**consistently ~94% inherited by table count**.

---

## 5. Territory and geography

### 5.1 The mechanism is a two-step indirection

Discovered by scanning all 221 key-column names for geographic tokens
(`22_territory.py`), **2,969 of 30,773 table defs (9.6%)** are keyed on a
geographic column:

| geographic key column | table defs | distinct tables |
|---|---|---|
| `PremOpsTerr` | 1,137 | 33 |
| `ProdsCompldOpsTerr` | 896 | 6 |
| `ZipCode` | 333 | 1 |
| `Territory` | 197 | 19 |
| `PremOpsTerrName` | 94 | 2 |
| `PremisesOperationsTerritory` / `TerrorismTerritory` / `TerritoryIndicator` / `TerritoryBorough` | 40 each | 4 each |
| `LiquorLiabTerritory`, `SpecialClassPremOpsTerritory` | 20 each | 2 each |
| `CityTown` | 17 | 2 |
| `County` | 7 | 1 |

The chain is:

1. a domain table maps **postal code → territory code**
   (`DomainTerritoryCodeByZipCode`, `DomainZipCode`);
2. rate tables are keyed on the **territory code**;
3. `Form Related Fields` wires the two together in the UI — **257 of 3,122 rows**
   carry a geographic `DomainTableName`/`RelatedField` pair, e.g.
   the single row in NJ is verbatim
   `"NJ","Location Detail","GeneralLiabilityLocation","TerrorismTerritory","TerritoryCodeByZipCode","ZipCode","","A"`
   (`NJ/GL_NJ 20250301 V01_MachineReadableContent/GL NJ 20250301 V01/Form Related Fields/RelatedFields.FormField.csv`).

### 5.2 Coverage and vocabulary

> ### ⚠ Corrected 2026-08-10 — this section was wrong
>
> These figures pooled distinct values across **every** geographic column
> (`PremOpsTerr` + `ProdsCompldOpsTerr` + terrorism + liquor), which is why no
> jurisdiction appeared flat. Counting **Premises/Operations rating territories**
> instead: **20 jurisdictions have exactly one.** Verified `AK PremOpsTerr={001}`,
> `ProdsCompldOpsTerr={999}` — the "4" reported for AK was `001`+`999`+2 others.
>
> **Three schemes, and all 51 jurisdictions resolve from ERC:**
>
> | Scheme | Count | Mechanism |
> |---|---|---|
> | ZIP table | **27** | `DomainTerritoryCodeByZipCode`, 93 rows (RI) – 2,174 (PA) |
> | Single territory | **20** | AK AR DC DE ID ME MS MT NC ND NH NM NV PR SC SD UT VT WV WY. **19 use `001`, NC uses `002`.** No lookup needed |
> | County / place name | **4** | CA (11 codes/21 places), FL (5/8), NY (20/66), TX (8/15) |
>
> Nothing is undeterminable. The remaining requirement is an **input**: the four
> county/place jurisdictions need the risk's county or place, not its ZIP.

- Territory-code counts pooled across all geographic columns: NY 89, CA 35,
  TX 26, NJ 18, FL 16, PA 14 — retained for reference, but see the correction
  above before using them as rating-territory counts.
- `ZipCode` has **23,782 distinct values** corpus-wide, plus the single
  non-numeric sentinel **`Other`** (the catch-all, and the cause of the
  duplicate-key finding in report 1 §3.4).
- `PremOpsTerrName` carries 100 human-readable names
  (`Remainder of State`, `Miami / Dade County`, `Broward County`, …).
- **`ProdsCompldOpsTerr` has exactly ONE value corpus-wide: `999`.** Products/
  completed operations is keyed on territory but the key is degenerate —
  geography does not vary products rating anywhere in the corpus.

---

## 6. The rule program's shape

### 6.1 Organisation: by data structure, not by coverage

- **1,032 rule files, 1,032 DataDefGroups, and the mapping is 1:1 in all 1,032
  cases.** The filename is always `<DataDefGroup>Rules` — 1,032 of 1,032.
- Rules per file: min 2, median 3, max 609.

So the program is organised **one rule file per schema table**. Coverage
grouping is emergent from the table names, not structural.

### 6.2 Name taxonomy — the lifecycle is in the names

| bucket | `<Rule>` elements | distinct names | dominant operators |
|---|---|---|---|
| `Erc*` | 26,997 | **10** | RunRule, Sequence, ForEach |
| `Set*` | 26,378 | 827 | Constant, FirstValue, Test/Then |
| *(other)* | 21,474 | 1,196 | Constant, Sequence, Arg |
| `Initialize*` | 20,222 | **1** | Constant, Keys, Lookup |
| `Calculate*` | 13,864 | **1** | RunRule, FirstValue |
| `Lookup*` | 5,435 | 286 | Keys, Lookup, Value |
| `Call*` | 356 | 2 | RunRule, ForEach, Locate |

The ten `Erc*` names are the fixed lifecycle:
`ErcProcess`, `ErcRate`, `ErcSetRatesAndFactors`, `ErcSetPostRatesAndFactors`,
`ErcDoConditionalMandatoryLogic`, `ErcDoOptionalConditionalLogic`,
`ErcRunUnderwritingLogic`, `ErcRunPostUnderwritingLogic`,
`ErcSetStatisticalCodes`, `ErcCalculateTotalPremium` — verified as exactly ten
distinct names across all 114,726 `<Rule>` elements. (`InitializeRuleSet` and
`CalculateTotalPremium` are the other two fixed names, one each.)

`Lookup*` rules are a naming convention that binds a rule to a table: **9,325 of
9,381 (99.4%)** `<Lookup>` nodes sit inside a rule named `Lookup*`, and in
**73.8%** the rule name minus the `Lookup` prefix equals the table name exactly.

### 6.3 Entry points and the call graph

There are **two** roots, both present in all 567 packages:

- `GeneralLiabilityRules / ErcProcess` — the rating pass
- `GeneralLiabilityRules / ErcCalculateTotalPremium` — the aggregation pass,
  whose entire body is `RunRule ToDataDef="Premium" Rule="CalculateTotalPremium"`

Measured on `GL_CW_20270401_V01`:

- **3,888 of 4,528 rules reachable** from `ErcProcess`
- **max depth 8**; nodes by depth: 1, 828, 770, 1,145, 586, 315, 215, 27, 1
- fan-out per rule: min 1, median 1, max **828**
- **0 back-edges — the call graph is a DAG**
- 641 rules unreachable from `ErcProcess`; 571 of them are named
  `CalculateTotalPremium` — i.e. they hang off the *second* root.

`ErcProcess` at the top level sequences:
`ErcSetRatesAndFactors` → per-location `InitializeRuleSet` +
`CallErcSetRatesAndFactors` → `ErcDoConditionalMandatoryLogic` →
`ErcDoOptionalConditionalLogic` → `ErcSetPostRatesAndFactors` → `SetModFactors`
→ then a `ForEach` over every child table running `InitializeRuleSet` +
`ErcProcess` recursively
(`countrywide/GL CW 20260101 V01/Rules/GeneralLiabilityRules.Rule.xml`).

At the leaf, `ErcRate` sequences: `SetFinalRate` → `SetMedicalPaymentsCharge`
→ `SetAdditionalInterestFactor` → `SetMinimumPremium` → `SetMinPremium` →
`SetSpecialCombinedMinimumPremium` → `SetSpecialCombinedMinPremium` →
`SetPremium` → `SetPremiumIndicator`.

### 6.4 What an engine would have to implement

**52 operators** (full counts in `out/rule_program.txt`). Structurally:
a tree-walking interpreter over an XML AST with an XPath-like data
addressing scheme (`../`, `/*/`, `AtDataDef` paths), a typed value model
(string / integer / decimal / long), keyed matrix lookup with two result modes,
lexically-scoped parameters (`WithArgs` / `Arg @Param` / `Value @FromParam` —
observed params include `calculatedPremium`, `limit`, `coverage`,
`eachOccurrenceLimit`, `TableName`, `Message`), output-tree mutation
(`Locate`, `Copy`, `Remove`, `Guid`), and cross-package dispatch by
`ProjectName`.

**Declared but unspecified — an implementer must pin these down and the corpus
does not settle them:**

- `FirstValue @Order="DataDefInputParamConstant"` — the precedence between a
  DataDef value, an input, a parameter and a constant is named but not defined.
- `Lookup @ResultMode` `FirstResult` (86%) vs `SingleResult` — what "first"
  means when the declared key is not unique (3.79% of tables; report 1 §3.4).
- `Product @DecimalPlaces` / `Round @DecimalPlaces` — declared **7,682 times**
  across the corpus, but **the rounding mode is never stated** anywhere.
  Half-up vs half-even changes premiums.
- `Range @RangeType` boundary handling combined with `InterpolateMode="Linear"`
  at an exact boundary.
- `RunRule @ClearCache` — what is cached, and its lifetime.
- `Locate @OutputAction` / `@AtOutputDataDef` — creation and positioning
  semantics in the output tree.
- The XPath dialect used in `Form Fields.Condition` and
  `RatebookColumns.RatingRequiredCondition`.
- `MessageHelper.AddErrorMessage` (4,377 references) and `ErcCore` — both
  referenced, neither shipped.

---

## 7. Open questions

1. **Rounding mode.** The most material gap. `DecimalPlaces` is declared 7,682
   times; the rounding rule is never stated. *Needs:* the engine spec, or the
   single `1. Output.json` in `OK/GL_OK 20250601 V01` executed against its
   `1. Input.json` to infer it — I have not attempted that inference.
2. ~~**Where territory comes from in the 25 jurisdictions with no ZIP mapping.**~~
   **Resolved 2026-08-10** — 20 are single-territory (no lookup needed) and 4 use
   county/place tables that ERC does carry. See §5.2.
3. **Why `ProdsCompldOpsTerr` exists at all** when its only value is `999`.
   Vestigial, or a hook for a future filing? Not settled.
4. **What the ~380 pass-through tables are for.** They carry full form/field
   definitions and statistical coding but no rating. Whether a consumer is
   expected to obtain those premiums elsewhere, or whether they are simply
   "refer to company", is implied by the DOC register but never stated.
5. **`ModToUse`, `ExpenseModification`, `PremiumDiscountCharge`** appear in the
   `FinalRate` product but I did not trace where they are set — they may be
   inputs or derived. Untraced.
6. **The 454 unclassified rate tables and 518 unclassified DataDefGroups.**
   I classified by token; a residual third of the content is not attributed to
   a coverage family. Most appear to be additional-insured endorsements, but I
   did not verify that individually.
7. **Whether the resolved overlay is complete.** Re-running `06_resolve_refs.py`
   on the post-remediation tree gives the same result as report 1: of 227,685
   references, the only unresolved targets are the two engine primitives
   (`Pages` x45,592 and `MessageHelper.AddErrorMessage` x4,375). Excluding those,
   **closure is 100.000%** — every `Lookup` and `RunRule` resolves within the
   state package or the countrywide package it imports. So the overlay is
   *referentially* complete. What I still have **not** verified is whether it is
   *semantically* sufficient — i.e. that a rating actually terminates with a
   premium for every valid input. That needs an engine.
8. **`Status` A/C/D** — still undetermined (report 2 §2).

## 8. What I did not examine

- Row-level content of the ~380 pass-through tables' form definitions.
- `Base RaaS Overrides` DOC sheets (uninspected across all three reports).
- The `1. Output.json` sample, beyond confirming its existence and shape.
- Any excluded path, and the `_quarantine_misfiled/` directory.
