# ERC Build Specification — Part 3: Validation, Blockers and Backlog

> **Reconciliation note, 2026-08-11.** This document was derived clean-room from the ERC packages, in isolation from the PDF derivation and **before any subline
> was derived end to end**. The per-subline gates have since superseded or sharpened some claims
> here — see [`../gates/RECONCILIATION.md`](../gates/RECONCILIATION.md) (items R6, R7). The text below is
> left as the record of what this derivation found on its own; that independence is what makes
> agreement between the two derivations evidence.

Parts 1 and 2: `04-BUILD-SCOPE-AND-RESOLVER.md`,
`05-DATA-MODEL-AND-INGESTION.md`.

---

## 1. Validation assertions

Every assertion below was **actually run** during reports 01–03 and the
expected value is the measured result on the current (post-remediation) tree.
Severities: **BLOCKER** refuses the load; **MAJOR** loads with a recorded
defect; **MINOR** is informational.

### 1.1 Identity and structure

| id | severity | assertion | measured |
|---|---|---|---|
| `A-ID-01` | BLOCKER | every package has exactly one `DataDefs/*.xsd` | 567/567 |
| `A-ID-02` | BLOCKER | `targetNamespace` matches `erc/GL_<JJ>_<YYYYMMDD>_<Vnn>/MasterGL<JJ>` and yields a complete identity triple | 567/567 |
| `A-ID-03` | MAJOR | the XSD-derived identity equals the directory-derived identity | 567/567 |
| `A-ID-04` | BLOCKER | `(jurisdiction, edition_date, version)` is unique after dedup | 567 distinct from 572 directories |
| `A-ID-05` | MAJOR | package ids occupying >1 directory have byte-identical trees | 5 ids, all identical (sha256 tree hash) |
| `A-ID-06` | BLOCKER | directory jurisdiction == package jurisdiction | **0 violations** (was 2 pre-remediation) |
| `A-ID-07` | BLOCKER | every package has exactly one `xs:import` | 567/567 |
| `A-ID-08` | BLOCKER | every state package's imported countrywide package is present | 10 referenced, 10 present, 0 missing, 0 orphaned |
| `A-ID-09` | MINOR | countrywide packages import `ErcCore`, which is absent | 10/10 dangle — see §3.1 |

### 1.2 Tables

| id | severity | assertion | measured |
|---|---|---|---|
| `A-TB-01` | BLOCKER | every `*.RateTable.csv` has a paired `*Def.RateTableDef.xml` | 23,945 / 23,945 |
| `A-TB-02` | MAJOR | domain CSVs without a Def all have header `StateCode,DisplayValue,DataValue` | 3,056 / 3,056 |
| `A-TB-03` | BLOCKER | every domain table without a Def is declared in `DomainTables.Metadata.xml` | 3,056 / 3,056 |
| `A-TB-04` | MAJOR | CSV header == `KeyCols + ValueCols` in declared order | 27,729 of 27,747; the 18 failures are a trailing empty column, confined to 2 table names in 9 packages |
| `A-TB-05` | BLOCKER | every table named in `RateTables`/`DomainTables` metadata has a CSV, and vice versa | 0 missing, 0 extra, both directions |
| `A-TB-06` | MINOR | declared key is unique within the table | 26,695 of 27,747 (96.21%); 1,052 violations — 1,051 domain, 1 rate (`GL_NY_20240701_V01`/`ElectronicDataLiabilityClassCode`) |
| `A-TB-07` | BLOCKER | declared types are within {string, integer, decimal, long} | 100% |
| `A-TB-08` | MINOR | `CaseInsensitive` is `false` everywhere | 67,734 / 67,734 |
| `A-TB-09` | MAJOR | every `<Range>` in `ValueCols` names a `RangeKeyCol` that exists in `KeyCols` | 18 / 18 |

`A-TB-06` is MINOR, not MAJOR, because non-uniqueness is *expected* — 86% of
lookups use `ResultMode="FirstResult"`. But the count must be tracked: if it
rises, row order has become more load-bearing.

### 1.3 Rules and references

| id | severity | assertion | measured |
|---|---|---|---|
| `A-RL-01` | BLOCKER | every rule carries exactly one `RuleType*` provenance code | 114,726 / 114,726 |
| `A-RL-02` | BLOCKER | every `RuleTypeOverridden` rule shadows a rule of the same (file, name) in its parent | **23,404 / 23,404 = 100.0%** |
| `A-RL-03` | BLOCKER | no `RuleTypeStateSpecific` rule shadows a parent rule | **23,755 / 23,755 = 0.0% shadow** |
| `A-RL-04` | BLOCKER | `RuleTypeCountrywide` appears only in countrywide packages | 32,517, zero in state packages |
| `A-RL-05` | BLOCKER | `RuleTypeOverridden`/`StateSpecific` appear only in state packages | zero in countrywide |
| `A-RL-06` | BLOCKER | every `RunRule` resolves to a rule in the same package, its parent, or its named `ProjectName` package | 100.000% excluding `MessageHelper.AddErrorMessage` (4,375) |
| `A-RL-07` | BLOCKER | every `Lookup` resolves to a table in the same package or its parent | 100.000% excluding `Pages` (45,592) |
| `A-RL-08` | BLOCKER | every `RunRule@ProjectName` equals the package's `xs:import` | **0 disagreements across 51,983** |
| `A-RL-09` | BLOCKER | the `RunRule` call graph is acyclic | 0 back-edges on `GL_CW_20270401_V01` |
| `A-RL-10` | BLOCKER | both entry points exist in every package | `(GeneralLiabilityRules, ErcProcess)` 567/567; `(…, ErcCalculateTotalPremium)` 567/567 |
| `A-RL-11` | MAJOR | rule file ↔ DataDefGroup is 1:1 and the filename is `<group>Rules` | 1,032 / 1,032 |
| `A-RL-12` | MINOR | only ten `Erc*` rule names exist | 10 |

`A-RL-02`/`A-RL-03` are the highest-value checks in the set: they are the only
assertions that prove the resolver's override semantics match the corpus's own
declaration, and they hold with **zero exceptions in either direction**.

### 1.4 Metadata and forms

| id | severity | assertion | measured |
|---|---|---|---|
| `A-MD-01` | BLOCKER | exactly five `*.Metadata.xml` per package | 567 × 5 |
| `A-MD-02` | BLOCKER | every `MetaDataCode` cited by a table Def resolves to a `MetadataEntry Code` in the same package | **0 unresolved of 72,135** |
| `A-MD-03` | MAJOR | every circular `Name` parses into (no, effective date, filing ref, type) | 766 / 766 |
| `A-MD-04` | MAJOR | the latest circular a package cites is effective on or before the package's edition date | **566 / 566** |
| `A-MD-05` | BLOCKER | every `DataDefInfo` entry resolves to a complexType in the package's own or inherited XSD | 0 unresolved of 19,325 |
| `A-FM-01` | BLOCKER | each of the five form CSVs has exactly one header shape across all packages | 1 distinct header each, 5 of 5 |
| `A-FM-02` | MAJOR | form row keys are unique within a file | 33 collisions of 96,828 (0.034%), all in Form Related Fields |
| `A-FM-03` | MINOR | `Status` ∈ {A, C, D} | yes; **do not act on it** (report 02 §2) |

### 1.5 Post-resolution assertions

These run after the resolver, not on the raw load.

| id | severity | assertion | measured / expected |
|---|---|---|---|
| `A-RS-01` | BLOCKER | the resolved subline list is non-empty for every jurisdiction | 52/52 (unresolved: only 6) |
| `A-RS-02` | MAJOR | the resolved coverage set has ≥ 215 coverages per jurisdiction | min 215, median 219, max 250 |
| `A-RS-03` | BLOCKER | for a shadowed table, the state copy is used and never merged with the parent's | 21,694 shadowed; 0.17% identical, so a merge would corrupt 99.83% |
| `A-RS-04` | BLOCKER | `ProjectName`-qualified dispatch reaches the parent, not the overlay | 51,983 refs; failure ⇒ infinite recursion on 4,598 call-super rules |
| `A-RS-05` | MAJOR | every jurisdiction resolves to ≥1 package as of any date ≥ its first edition | first editions 2020-12-01 … 2022-09-01 |

### 1.6 Regression fixtures

The 517 `STC/*.json` files are sample transactions covering 506 packages
(29,723 leaf fields). `OK/GL_OK 20250601 V01` uniquely ships both
`1. Input.json` and `1. Output.json` (35 KB) — **the only rated output example
in the corpus**. It is the single most valuable artefact for validating an
engine and should be the first regression test attempted.

---

## 2. Reconciliations that already hold (do not re-litigate)

For anyone extending this work: these were run to completion and passed. They
are cheap to re-run and should be part of CI.

- Corpus file accounting closes exactly: 86,664 in packages + 507 zips + 3 root
  spreadsheets + 1 tooling file = 87,258 minus the quarantined package.
- Editions are cumulative snapshots (92.7–98.3% carry-over over 515 pairs).
- 600 of 600 dropped state tables remain in the new edition's countrywide
  parent — nothing is ever lost.
- Identity is reconstructible from content alone at 100% coverage.
- Reference closure is 100.000% excluding two engine primitives.

---

## 3. What blocks a correct premium

Ranked by how much premium error each can cause.

### 3.1 Rounding mode — unspecified, and material

`@DecimalPlaces` is declared **7,682 times** across the corpus
(`Product@DecimalPlaces`, `Round@DecimalPlaces`). **The rounding rule is stated
nowhere** — not in the XSD, not in the metadata, not in any DOC sheet. Searched
all 2,865 metadata files and the DOC sheet inventory.

The premium chain compounds it: `BaseRate` rounds to 3 places, `FinalILF`
rounds, `FinalRate` rounds to 3, `Premium` rounds to 0. Half-up vs half-even vs
truncate at four stages will disagree on real policies.

**Resolution paths, in order of preference:** (a) obtain the ERC engine
specification; (b) infer it by executing `OK/GL_OK 20250601 V01`'s
`1. Input.json` and matching `1. Output.json` — feasible but gives one data
point, not a proof; (c) parameterise and let the user choose, which is an
admission of defeat and must be labelled as such in output.

**Until resolved, no premium this engine produces can be asserted as correct to
the cent.** State that explicitly in the output contract.

### 3.2 Territory — always derivable, by one of three schemes

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

2,969 of 30,773 table defs are keyed on a geographic column, and `PremOpsTerr`
alone keys 1,137 of them.

This is **not a blocker**. The only outstanding need is address→county/place
resolution for CA, FL, NY and TX. Where a mapping does exist, the
chain is: domain table maps ZIP → code (23,782 distinct ZIPs plus the sentinel
`Other`), `Form Related Fields` wires it into the UI, rate tables key on the
code.

One quirk to encode: **`ProdsCompldOpsTerr` has exactly one value corpus-wide,
`999`.** Products/completed-operations rating is keyed on territory but the key
is degenerate everywhere. Do not build a territory-resolution path for it.

### 3.3 Untraced factors in the `FinalRate` product

`FinalRate = Product(BaseRate, FinalILF, PackageModFactor,
ExperienceRatingModificationFactor, ExpenseModification, ModToUse
[, SizeOfRiskFinalRelativity] [, PremiumDiscountCharge])`.

`ModToUse`, `ExpenseModification` and `PremiumDiscountCharge` appear as factors
but **I did not trace where they are set** — they may be inputs, may be derived,
may default to 1.0. Each is a direct multiplier on every class-rated premium, so
an error in any of them scales the whole answer. This must be closed before any
premium is trusted. Tractable: walk `out/dataflow_edges.csv` for those targets.

### 3.4 Referential completeness ≠ semantic sufficiency

100.000% reference closure proves no dangling pointer. It does **not** prove a
rating terminates with a premium for every valid input. Untested, and untestable
without an engine. Treat "the content resolves" and "the content rates" as
separate claims; only the first is established.

### 3.5 Two engine primitives are not in the corpus

- **`ErcCore`** — imported by all 10 countrywide XSDs, absent from the tree
  (searched by filename, 0 hits). The base types of `MasterGLCW` are unknown.
- **`MessageHelper.AddErrorMessage`** — 4,375 `RunRule` references, not shipped.
  Its parameters (`Message`, `TableName`, `ErcMessageTableId`) are visible; its
  behaviour is not. This is the error/diagnostic channel, so an engine must
  invent one and the messages will not match ISO's.

### 3.6 Operator semantics that are named but not defined

Each of these is declared in the data and unspecified anywhere:

- `FirstValue@Order="DataDefInputParamConstant"` — the precedence between a
  DataDef value, an input, a parameter and a constant. Appears on 171,865 nodes.
- `Lookup@ResultMode` `FirstResult` (86%) vs `SingleResult` — what "first" means
  against the 3.79% of tables with non-unique keys.
- `Range@RangeType` boundary handling **combined with** `InterpolateMode`
  at an exact boundary.
- `RunRule@ClearCache` — what is cached and for how long.
- `Locate@OutputAction` / `@AtOutputDataDef` — output-tree creation semantics.
- `Remove@RemoveMultiple`, `Copy`, `Guid` — side effects on the output tree.
- The XPath dialect in `FormField.Condition` (10,581 rows) and
  `RatebookColumn.RatingRequiredCondition` (4,977 rows) — full XPath 1.0, or a
  subset? The corpus uses `count()`, predicates, `and`/`or`, `..` navigation.

### 3.7 Known-unknown content

- **`Status` A/C/D** — falsified as Add/Change/Delete (report 02 §2). Store,
  do not act. Affects 23.4% of Form Pages and 39.7% of Ratebook Columns.
- **`Base RaaS Overrides`** — a DOC sheet in 217 packages, never characterised.
- **454 unclassified rate tables and 518 unclassified DataDefGroups** — not
  attributed to a coverage family.
- The **~380 capture tables**: whether their premiums are expected from another
  system or are simply "refer to company" is implied by the DOC register but
  never stated.

---

## 4. Build backlog

Phased. **Risk flags: 🔴 blocked on information the corpus does not contain ·
🟠 large or novel · 🟢 routine.**

### Phase 1 — Ingest and prove the load (no rating)

| # | Work | Risk |
|---|---|---|
| 1.1 | Package enumerator; identity from XSD `targetNamespace`; dedup by id | 🟢 |
| 1.2 | Table loader: Def + CSV, five shapes, synthesised domain Defs, BOM, trailing-comma tolerance, text-preserving cells | 🟢 |
| 1.3 | Rule parser to AST preserving all behavioural attributes, incl. `ProjectName` | 🟠 |
| 1.4 | Metadata, circulars, five form CSVs, DOC exception sheets | 🟢 |
| 1.5 | Assertion harness — all of §1.1–1.4; refuse on BLOCKER | 🟢 |
| 1.6 | Query surface: table catalogue, package/edition index, coverage inventory | 🟢 |

Exit criterion: all 33 assertions in §1.1–1.4 pass on 567 packages.

### Phase 2 — The resolver

| # | Work | Risk |
|---|---|---|
| 2.1 | As-of edition selection with `(edition_date, version)` ordering | 🟢 |
| 2.2 | Parent resolution from the single `xs:import` | 🟢 |
| 2.3 | Name-wise overlay across all eight categories, **both layers retained** | 🟠 |
| 2.4 | `ProjectName`-qualified dispatch bypassing the overlay | 🟠 — get this wrong and you get infinite recursion |
| 2.5 | Post-resolution assertions §1.5 | 🟢 |
| 2.6 | Resolved coverage / subline inventory per jurisdiction as-of a date | 🟢 |

Exit criterion: resolved subline count is 11 corpus-wide with the documented
per-jurisdiction exceptions; resolved coverages ≥215 per jurisdiction.

### Phase 3 — The rule interpreter

| # | Work | Risk |
|---|---|---|
| 3.1 | DataDef tree with parent links; XPath-like addressing (`../`, `/*/`, 5-level ascent) | 🟠 |
| 3.2 | The 52 operators: control flow, predicates, arithmetic, date, text | 🟠 |
| 3.3 | Keyed matrix lookup incl. banded, interpolated and `Pages` | 🟠 |
| 3.4 | `WithArgs` lexical parameter scope | 🟢 |
| 3.5 | Output-tree mutation (`Locate`, `Copy`, `Remove`, `Guid`) | 🔴 semantics undefined (§3.6) |
| 3.6 | `MessageHelper` substitute | 🔴 not shipped |
| 3.7 | **Rounding policy** | 🔴 **unspecified — see §3.1** |
| 3.8 | `FirstValue@Order` precedence | 🔴 named, undefined |

### Phase 4 — Rating the core

| # | Work | Risk |
|---|---|---|
| 4.1 | The 19 rating tables end to end | 🟠 |
| 4.2 | Close out `ModToUse` / `ExpenseModification` / `PremiumDiscountCharge` | 🟠 tractable, must be done |
| 4.3 | Territory: ZIP table (27), single-territory constant (20), county/place (4) | 🟢 for 47 · 🟠 4 need address→place |
| 4.4 | The 381 capture tables (383 groups): `ManualPremium × PackageModFactor` + required-input validation | 🟢 |
| 4.5 | Aggregation via `ErcCalculateTotalPremium` | 🟢 |
| 4.6 | "Refer to company" as a first-class outcome, all three triggers (part 1 §1.3) | 🟢 |
| 4.7 | Statistical coding (1,490 code tables) | 🟢 |

### Phase 5 — Validation against ISO

| # | Work | Risk |
|---|---|---|
| 5.1 | Replay `OK/GL_OK 20250601 V01` input → output; infer rounding | 🔴 one data point only |
| 5.2 | Use the other 516 STC inputs as structural regression fixtures | 🟢 |
| 5.3 | Obtain the ERC engine spec and `ErcCore` from the distributor | 🔴 **external dependency; the honest unblock for 3.5–3.8 and 5.1** |

**The critical path runs through 5.3, not through code.** Phases 1, 2 and 4.4–4.7
can be built and proven correct today. Phase 3's undefined semantics and Phase
4's rounding cannot be settled from this corpus — only bounded and disclosed.
