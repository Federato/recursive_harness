# ISO ERC General Liability — Corpus Inventory, Content Model, Extraction

**Scope of this document.** Clean-room analysis derived solely from the raw
ERC packages under `C:\Projects\ISO_ERC_Files\General_Liability\`. No prior
work product, manual PDF, or bridge spreadsheet was opened. Every number
below was produced by a script in `C:\Projects\Recursive_Harness_2.0\scripts\erc\`
and is reproducible by re-running it; intermediates are in
`scripts\erc\out\` (266 MB).

Pipeline:

| Script | Produces |
|---|---|
| `00_common.py` | package enumeration, BOM-tolerant readers |
| `01_inventory.py` | `packages.csv`, `files.csv`, `inventory_summary.txt` |
| `02_table_defs.py` | `table_defs.csv`, `table_catalogue.csv`, `table_defs_report.txt` |
| `03_metadata.py` | `metadata_entries.csv`, `circulars.csv`, `metadata_report.txt` |
| `04_datadefs.py` | `xsd_packages.csv`, `xsd_types.csv`, `xsd_enums.csv`, `xsd_report.txt` |
| `05_rules.py` | `rules_index.csv`, `rule_refs.csv`, `rules_report.txt` |
| `06_resolve_refs.py` | `ref_resolution.csv/.txt` — rule→table/rule reference closure |
| `07_csv_values.py` | `column_profile.csv`, `value_vocab.csv`, `csv_values_report.txt` |
| `08_doc_stc_forms.py` | `doc_sheets.csv`, `doc_exceptions.csv`, `stc_index.csv`, `form_csv_schema.csv`, `form_pages.csv`, `doc_stc_report.txt` |
| `09_reconcile.py` | `reconciliation.txt` — nine cross-artifact checks |
| `10_key_uniqueness.py` | `key_uniqueness.csv/.txt` — empirical key test |

---

## 1. Corpus inventory

### 1.1 Headline numbers (`out/inventory_summary.txt`, `out/reconciliation.txt`)

| Measure | Value |
|---|---|
| Files anywhere under the corpus root | **87,258** |
| Bytes anywhere under the root | **802,434,630** (765.3 MiB) |
| `.zip` archives (redundant, ignored) | **508** (95,365,904 B) |
| Loose files at root | 3 (the two `GL_ERC_*` spreadsheets and one `.html` — **excluded by instruction, not opened**) |
| Files inside package directories | **86,746** |
| Bytes inside package directories | **705,016,342** (672.4 MiB) |
| Package **directories** | **573** |
| **Distinct** packages after de-duplication | **567** |
| Countrywide packages | **10** |
| State/territory packages (distinct) | **557** |
| Jurisdiction codes appearing in package names | **52** (51 states/DC/PR + `CW`) |

**Reconciliation of the file total — closes exactly.** The 512-file
difference between the 87,258 files under the root and the 86,746 inside
package category directories was enumerated by set difference:

```
87,258 = 86,746 (inside packages)
       +    508 (.zip archives)
       +      3 (GL_ERC_Edition_Hierarchy.html/.xlsx, GL_ERC_to_Manual.xlsx — not opened)
       +      1 (.claude\settings.local.json — a tooling artefact, not corpus content)
```

Nothing else exists under the root. Every file is accounted for.

**Against your stated totals:** files (~87,258) and size (~988 MB) match on
the file count; the byte total is 765.3 MiB / 802 MB by `st_size`, which
differs from ~988 MB — the gap is on-disk allocation vs. logical size, not
missing content. Your "~530 state package directories" is **low**: the
measured figure is **563 state directories / 557 distinct packages**. The
countrywide count of 10 matches exactly.

### 1.2 File kinds (`out/inventory_summary.txt`)

| Kind | Count |
|---|---|
| `*.RateTable.csv` | 23,975 |
| `*Def.RateTableDef.xml` | 23,975 |
| `*.Rule.xml` | 20,802 |
| `*.DomainTable.csv` | 6,829 |
| `*Def.DomainTableDef.xml` | 3,772 |
| `*.Metadata.xml` | 2,865 (= 5 × 573) |
| `*.FormPage.csv` | 1,719 (= 3 × 573) |
| `*.FormField.csv` | 1,146 (= 2 × 573) |
| `*.DataDef.xsd` | 573 (exactly 1 per package) |
| `DOC/*.xlsx` | 573 (exactly 1 per package) |
| `STC/*.json` | 517 |

### 1.3 Package anatomy

A package is a directory of up to twelve category sub-directories:

```
DataDefs/            exactly one *.DataDef.xsd
DOC/                 exactly one *.xlsx documentation workbook
Metadata/            exactly five *.Metadata.xml
Rules/               *.Rule.xml            (min 3, median 23, max 572)
Rate Tables/         *.RateTable.csv + *Def.RateTableDef.xml (always paired)
Domain Tables/       *.DomainTable.csv, *Def.DomainTableDef.xml (often absent)
Form Fields/         Fields.FormField.csv
Form Pages/          Pages.FormPage.csv
Form Related Fields/ RelatedFields.FormField.csv
Ratebook Columns/    RatebookColumns.FormPage.csv
Ratebook Tables/     RatebookTables.FormPage.csv
STC/                 *.json  (absent in 61 packages)
```

**Two directory layouts.** 554 of 573 packages nest the content one level
deeper: `GL_NJ 20250301 V01_MachineReadableContent/GL NJ 20250301 V01/…`.
The other 19 place the categories directly under the package directory.
`00_common.py` detects and normalises both.

**Two naming conventions.** The outer directory is either
`GL_<XX> <YYYYMMDD> V<nn>_MachineReadableContent` or
`GL <XX> <YYYYMMDD> V<nn>` (underscore vs. space after `GL`; suffix present
or not). Every one of the 573 directories matched the pattern
`^GL[ _]([A-Z]{2})[ _](\d{8})[ _](V\d+)` — **zero name-pattern failures**.

### 1.4 Anomalies (all of them)

`01_inventory.py` recorded **640** anomaly lines. Grouped:

1. **`MISSINGCAT` × 61** — 61 packages have no `STC/` directory. No other
   category is ever missing from any package.
2. **`PAIR` × 573** — every package reports a Domain-table CSV/Def count
   mismatch. **This is not a defect** — see §2.3; it is the normal encoding
   for simple domain tables. Rate tables are paired 23,975 : 23,975 with
   **zero** exceptions.
3. **`DUPKEY` × 6** — six package identities appear twice:
   - Five are the *same package extracted under two directory names*:
     `AL/GL_AL 20260701 V01` and `AL/GL_AL 20260701 V01_MachineReadableContent`
     (likewise CA 20241101 V01, LA 20260701 V02, MI 20260501 V01,
     OH 20260601 V02). `diff -rq` on each pair returned **no differences** —
     byte-identical duplicates.
   - One is a **misfiled package**: `GA/GL_DE 20260101 V01_MachineReadableContent`
     is a Delaware package sitting in the Georgia directory, byte-identical
     to `DE/GL_DE 20260101 V01_MachineReadableContent`. Its `.zip` is also in
     `GA/`, so the misfiling predates extraction.
4. **A seventh misfiling, not caught by the dup check**:
   `RI/GL_PR 20270401 V02_MachineReadableContent` is a Puerto Rico package
   under `RI/`, and `PR/` contains **no** 20270401 edition. So PR's newest
   edition is only reachable via the RI directory. Detected by R1 in
   `09_reconcile.py` (`juris_dir` ≠ package-name jurisdiction).
5. **65 package directories have no sibling `.zip`** and **0 zips lack an
   extracted directory** — full list in `out/inventory_summary.txt`.
6. **Zero empty (0-byte) files. Zero unreadable files.** All 51,987
   XML/XSD files (23,975 RateTableDef + 3,772 DomainTableDef + 20,802 Rule +
   2,865 Metadata + 573 xsd) parsed, and all 33,669 CSVs (30,804 table +
   2,865 form/ratebook) read, without a single error across scripts 02–08
   and 10 (`PROBLEMS: 0` in every report). All 573 `.xlsx` opened cleanly and
   514 of 517 `.json` parsed to the expected shape (the other 3 parsed but
   are a different envelope — see §2.6).
7. **Zero loose files outside a category directory** in any package.

### 1.5 Edition timeline (`out/reconciliation.txt` R9)

- Edition dates span **20201201 … 20270401**.
- **83 of 573 packages carry an edition date later than today (2026-08-10)** —
  the corpus ships future-effective filings.
- Version tokens: `V01` ×411, `V02` ×134, `V03` ×24, `V04` ×4.
- Packages per jurisdiction: minimum 7 (CA, MA, TX, VA), maximum 20 (AL);
  the countrywide directory holds 10.
- Per-package size: files min 73 / median 117 / max 1,554; rate tables
  min 26 / median 35 / max 272; domain tables min 1 / median 5 / max 265.

---

## 2. The content model

### 2.1 The DataDef XSD (`04_datadefs.py`, `out/xsd_report.txt`)

Every package contains **exactly one** `.xsd`, named `Master GL<XX>` /
`MasterGLCW`. Findings:

- `targetNamespace` is always
  `http://www.verisk.com/iso/erc/<PKG_ID>/MasterGL<XX>`, e.g.
  `.../GL_NJ_20250301_V01/MasterGLNJ`. **The namespace-encoded package id
  matched the directory-derived id in 573 of 573 packages** — the strongest
  identity reconciliation in the corpus.
- **Every package has exactly one `xs:import`.** State schemas import a
  *specific countrywide package's* namespace:
  ```
  <xs:import schemaLocation="erc://GL_CW_20231201_V02/MasterGLCW"
             namespace="http://www.verisk.com/iso/erc/GL_CW_20231201_V02/MasterGLCW" />
  ```
  (`NJ/GL_NJ 20250301 V01_MachineReadableContent/GL NJ 20250301 V01/DataDefs/MasterGLNJ.DataDef.xsd`)
  This makes the **state→countrywide edition dependency explicit and
  machine-readable**. All ten distinct CW packages referenced are present in
  the corpus, and all ten CW packages present are referenced — the graph is
  **exactly closed**.
- The ten countrywide schemas instead import a namespace called **`ErcCore`**.
  Searched the entire corpus by filename (`find -iname "*ErcCore*"`) and found
  **nothing**. `ErcCore` is a base schema the corpus references but does not
  ship. This is the corpus's one genuinely dangling schema dependency.
- The state schema *extends* the countrywide one:
  `<xs:extension base="a:MasterGLCW">`. State XSDs redeclare only what they
  override (median 43 complexTypes, 648 elements) against the countrywide
  schema's ~1,000+ complexTypes and ~27,000 elements.
- The CW schema **grows monotonically across editions**: 981 complexTypes /
  25,083 elements (`GL_CW_20201201_V01`) → 1,105 / 28,233 (`GL_CW_20270401_V01`).
- **There are no named simpleTypes and no `xs:enumeration` anywhere**
  (`xsd_enums.csv` is empty; `enum=0` for all 573). The 252,519 `xs:restriction`
  elements are all inline and only ever constrain **precision** (203,489
  `xs:decimal` with `fractionDigits`/`totalDigits`) or **length** (49,030
  `xs:string` with `length`). *The value vocabulary is not in the schema; it is
  in the Domain Tables.*
- 19,325 complexTypes carry an `xs:annotation/xs:documentation` block of the
  literal form `Metadata codes:` followed by codes — the join key back to the
  Metadata files.

### 2.2 The metadata model (`03_metadata.py`, `out/metadata_report.txt`)

Every package has **exactly five** metadata files: `Circulars.Metadata.xml`,
`DataDefInfo.Metadata.xml`, `DomainTables.Metadata.xml`,
`RateTables.Metadata.xml`, and `GL<XX>.Metadata.xml`. All 2,865 files use the
single namespace `http://www.verisk.com/iso/erc/Metadata`.

The model is **flat and uniform — a code registry, maximum nesting depth 1**:

```
Metadata
  MetadataEntry @Code @Name           (the group: Circulars | DataDefInfo |
                                       DomainTables | RateTables | BureauRuleNumbers)
    MetadataEntry @Code @Name         (the item)
      Description?                    (free text)
      Property @Name @Type            (only "Comment"/string and "Type"/string exist)
```

89,630 entries parsed: BureauRuleNumbers 31,444 · RateTables 24,548 ·
DataDefInfo 19,968 · DomainTables 7,402 · Circulars 6,268.
Only two `Property` names exist corpus-wide: `Comment` (21,297) and `Type`
(19,395). `Type` takes six values: **Policy, Form, Coverage, Schedule, Risk**
(and blank) — this is the level at which each data table sits.

**Critical negative finding.** The metadata declares **no dates, no version,
no product identity, no provenance**. Searched all 2,865 metadata files for
`EffectiveDate|ReleaseDate` as file-level elements: **0 files**. A package's
identity, edition and version exist **only** in (a) the directory name, (b)
the XSD `targetNamespace`, (c) the DOC workbook's filename
(`DOC-GL-NJ-03012025-V01.xlsx`), and (d) the STC JSON's `SchemeKeys`. There
is no self-describing manifest.

**Circulars.** 766 distinct circular codes across the corpus. The `Name`
attribute packs four fields in a fixed literal form; a single regex parsed
**766 of 766 with zero failures**:
`Circular LI-GL-2020-209 (Circular Effective Date: 12/01/2020 | Filing Reference: GL-2020-RELP1 | Type: LOSS COST)`.
Type vocabulary: LOSS COST 358 · RULES 265 · FORMS 71 · FORMS & RULES 33 ·
FORMS & RULES & LOSS COSTS 31 · STATISTICAL PLAN 6 · LOSS COSTS & RULES 2.
Circular effective dates run **2015 → 2027**. Extracted in full to
`out/circulars.csv`.

### 2.3 The table model (`02_table_defs.py`, `out/table_defs_report.txt`)

30,804 (package × table) rows: **23,975 Rate** and **6,829 Domain**.
**450 distinct rate-table names, 375 distinct domain-table names, 836
distinct signatures** (`table_catalogue.csv`). Only 9 table names carry more
than one column signature across the corpus — the schema is remarkably stable.

Def element model (namespaces `.../erc/RateTable`, `.../erc/DomainTable`):

```
RateTable | DomainTable
  MetaData
    MetaDataCode*                    (72,135 citations)
  KeyCols
    KeyCol   @Name @Type @CaseInsensitive
    Range    @Name @Type @RangeType [nested KeyCol ×2: _From, _ToLessThan]
  ValueCols
    ValueCol @Name @Type
    Range    @Name @Type @RangeKeyCol @InterpolateMode [nested ValueCol ×2]
```

- Declared types are only: key `string` (66,444) / `integer` (1,290); value
  `string` (16,244) / `decimal` (14,505) / `integer` (836) / `long` (20).
- **`CaseInsensitive` is `"false"` in all 67,734 occurrences** — no variation.
- **`<Range>` appears 200 times corpus-wide** (182 in KeyCols, 18 in ValueCols)
  across 8 distinct range names. `RangeType` ∈ {`FromInclusiveToExclusive` (108),
  `FromExclusiveToInclusive` (74)}. `InterpolateMode="Linear"` appears **18
  times**, always on a ValueCol Range bound to a KeyCol Range via
  `@RangeKeyCol`. **This is the corpus's one declared case where a cell's
  meaning is not its literal value**: in
  `PremOpsSizeOfRiskRelativity` / `ProdsCompldOpsSizeOfRiskRelativity`,
  `Relativity_From`/`Relativity_ToLessThan` are the endpoints of a **linear
  interpolation** over `PremOpsExposureTimesThousand_From/_ToLessThan`, not
  two independent numbers.
  (`countrywide/GL CW 20260101 V01/Rate Tables/PremOpsSizeOfRiskRelativityDef.RateTableDef.xml`)

**Rate tables are always paired; Domain tables are not, by design.**
3,057 of 6,829 Domain CSVs ship with **no** Def XML. All 3,057 have the
**identical** header `StateCode,DisplayValue,DataValue`, and **all 3,057 are
declared in `DomainTables.Metadata.xml`** (verified in `09_reconcile.py`).
The Def file is emitted only when a domain table deviates from that default
two-key/one-value shape. Zero rate CSVs lack a Def.

### 2.4 The rule model (`05_rules.py`, `out/rules_report.txt`)

**114,757 `<Rule>` elements** in 20,802 rule files; 2,323 distinct rule
names; 1,032 distinct rule-file names, matching 1,032 distinct
`DataDefGroup` values one-to-one.

**These are executable logic, not prose.** 2,052,818 XML elements carry only
5,627,878 non-whitespace text characters — **2.74 characters per element**,
and virtually all of that text is `<Constant>` payload. The element
vocabulary is a complete expression language (58 tags):

- control flow — `Sequence`, `If`/`Test`/`Then`/`Else`, `Choose`/`When`/`Otherwise`, `ForEach`, `Break`
- data access — `Value @FromDataDef @FromParam`, `FirstValue @FromConstant @FromDataDef @Order`, `FirstNonNull`, `Constant @Type @ToDataDef`, `Param`, `Arg`
- table access — `Lookup @Type @MatrixDef @MatrixFromConstant @MatrixCol @ResultMode` + `<Keys>`
- predicates — `Equal`, `NotEqual`, `And`, `Or`, `GreaterThan(OrEqual)`, `LessThan(OrEqual)`, `IsNull`, `IsNotNull`, `Exist`, `NotExist`
- arithmetic/text/date — `Sum`, `Product @DecimalPlaces`, `Subtract`, `Divide`, `Round`, `Truncate`, `Max`, `Count`, `Concat`, `Length`, `PadLeft`, `Convert`, `DatePart`, `DateAdd`, `DateCreate`, `DateDifference`
- structural — `RunRule`, `Locate @AtInputDataDef @AtOutputDataDef @OutputAction`, `Copy`, `Remove @RemoveMultiple`, `Guid`, `GetList`

Median rule body depth 4, maximum **26**.

**Rule provenance taxonomy.** Every `<Rule>` carries `MetadataCodes`, and
exactly four values occur across all 114,757:
`RuleTypeSystem` 34,673 · `RuleTypeCountrywide` 32,517 ·
`RuleTypeStateSpecific` 23,975 · `RuleTypeOverridden` 23,592. The corpus
therefore states, per rule, whether it is plumbing, inherited countrywide
logic, a state addition, or a state override of countrywide logic.

**Rate-table binding.** `<Lookup>` is the only mechanism by which rules read
tables. `@MatrixFromConstant` is the table name, `@MatrixDef` is
`<table>Def`, `@MatrixCol` is the column read, `@ResultMode` ∈
{`FirstResult` 20,188, `SingleResult` 3,330}, `<Keys>` supplies the key
tuple positionally. `<Lookup Type>` ∈ {string 19,520, decimal 2,708,
integer 278}.

### 2.5 Form / Ratebook CSVs (`08_doc_stc_forms.py`)

Five CSVs per package, **each with exactly one distinct header across all
567 packages** — perfect schema uniformity:

| File | Rows (corpus) | Notable columns |
|---|---|---|
| `Form Fields/Fields.FormField.csv` | 30,449 | 27 cols: `Type`, `Label`, `Quote*`/`Policy*` Read-only/Required/Display, `Default`, `Min`, `Max`, `Condition` **(XPath)**, `RequiredCondition`, `Audit*`, `DomainTableName`, `Sequence`, `Status` |
| `Form Pages/Pages.FormPage.csv` | 26,336 | `TableName`, `Type`, `Name`, `ParentName`, `AttachmentType`, `Condition`, `Number` (**ISO form number, e.g. `CG 22 67 10 93`**), `Min/MaxOccurs`, `Scheduled`, `Sequence`, `Status`, `MetadataCodes` |
| `Form Related Fields/RelatedFields.FormField.csv` | 3,122 | `DomainTableName`, `RelatedField`, `RelatedXPath` — cascading-dropdown wiring |
| `Ratebook Columns/RatebookColumns.FormPage.csv` | 15,525 | `RatingRequiredCondition` (XPath) |
| `Ratebook Tables/RatebookTables.FormPage.csv` | 21,433 | `Comment`, `BureauRuleNumber` |

`Form Pages` extracted in full to `out/form_pages.csv`:
Type ∈ {Form 9,535 · Coverage 9,156 · Detail 4,530 · Summary 3,115};
AttachmentType ∈ {Optional 11,292 · *(blank)* 7,645 · Conditional 7,333 ·
Mandatory 66}; Status ∈ {A 13,878 · C 6,290 · D 6,168}.
**1,443 distinct page names, 1,596 distinct ISO form numbers**, and 10,581
rows carrying a non-empty XPath `Condition`.

The `Condition` values are **XPath over the DataDef tree**, e.g.
`../../../../Subline[.='Products/Completed Operations'] and count(.../GeneralLiabilityDefenseWithinLimitsProdsCompldOps)> 0`
(`NJ/.../Form Fields/Fields.FormField.csv`). The corpus therefore carries UI
and applicability logic in a *second, different* language from the Rules.

### 2.6 STC (`out/stc_index.csv`)

517 JSON files in 506 distinct packages, 2.41 MB, 29,723 leaf fields.
**Sample transactions**, not schema. 514 have top-level keys
`GeneralLiability|SchemeKeys`; the input payload is a nested JSON mirror of
the DataDef tree (see `NJ/.../STC/1. Input.json`). Three files are a
different shape (`header|body` / `Header|Body` — an API envelope), and
`OK/GL_OK 20250601 V01` uniquely ships both `1. Input.json` **and**
`1. Output.json` (35 KB) — the only rated *output* example in the corpus.

`SchemeKeys.EffectiveDateTime` **agrees with the directory edition date in
513 of the 514 files that carry one**. The single disagreement is
`GL_CO_20270401_V03`: directory says `20270401`, STC says `2027-04-10`.

### 2.7 DOC workbooks (`out/doc_sheets.csv`, `out/doc_exceptions.csv`)

One `.xlsx` per package (573 workbooks, 2,900 sheets). Sheet vocabulary:
`Table of Contents` 573 · **`Refer to Company` 573** · **`Not Supported` 564** ·
`Special Consideration` 532 · `Full Form Name` 325 · `Base RaaS Overrides` 217,
plus 13 rarer sheets (class-description tables, `Stat Assignment`,
`Policy Adm Functionality`, and one bare `Sheet1`).

**This is the most consequential category and its name gives no hint of it.**
The workbook is the register of *what the ERC content does not automate*.
6,809 exception rows extracted:

- **`Refer to Company` — 5,300 rows in 390 packages, 591 distinct form
  numbers.** Each names a Rule number, rule name, ISO form number and the
  reason, e.g. `GL_AK_20240701_V01 | Rule 36.C.14.a | Description Of Additional Optional… | CG 32 67 | Refer To Company for rating Alaska Total Pollution Exclusion`.
- **`Not Supported` — 395 rows in 35 packages**, e.g. `GL_CW_20201201_V01`:
  "Declaration Page and Policy Writing forms are not supported",
  "Eligibility is not supported.", "Split Limits are not supported.",
  and `Rule 15.D.7 Deductible Discount Factors`: "Interpolation procedure to
  be used in determining deductible discount…".
- **`Special Consideration` — 1,114 rows in 532 packages.**

---

## 3. Extraction results and how they were verified

`07_csv_values.py` performed a **full pass over all 30,804 table CSVs** —
nothing sampled — reading **45,195,864 cells** across **12,866,232 data
rows** and **3,097 distinct (kind, table, column) combinations** built from
**260 distinct column names**. For 2,885 of the 3,097 columns the complete
value vocabulary (≤400 distinct) was materialised into `value_vocab.csv`
(19,376 rows).

### 3.1 Reconciliations that hold (`out/reconciliation.txt`)

| Check | Result |
|---|---|
| R1 XSD `targetNamespace` package id == directory-derived id | **573 / 573** |
| R2 RateTables declared in metadata ↔ CSVs shipped | **0 missing, 0 extra** |
| R2 DomainTables declared in metadata ↔ CSVs shipped | **0 missing, 0 extra** |
| R3 Def `KeyCols+ValueCols`, in order, == CSV header | **27,729 / 27,747** (see §3.2) |
| R3 Def-less Domain CSVs all `StateCode\|DisplayValue\|DataValue` | **3,057 / 3,057** |
| R4 19,325 `DataDefInfo` entries resolve to a complexType in the package's own XSD or its imported CW XSD | **0 unresolved** |
| R5/R6 Form/Ratebook CSV headers identical across packages | **1 distinct header each, 5/5 files** |
| R7/R8 72,135 `MetaDataCode` citations in table Defs resolve to a `MetadataEntry Code` in the same package | **0 unresolved** |
| R9 CW packages referenced by `xs:import` vs. present | **10 referenced, 10 present, 0 missing, 0 orphaned** |
| Rule `ProjectName` attributes vs. the package's `xs:import` | **0 disagreements** across 51,987 named references |

### 3.2 Reconciliations that fail

- **18 CSV header mismatches** (`table_defs_report.txt`). Every one is the
  *same defect*: a **trailing comma on the header line** producing a
  seventh, unnamed, always-blank column. Confined to two tables
  (`PremOpsSizeOfRiskRelativity`, `ProdsCompldOpsSizeOfRiskRelativity`)
  across 9 packages. Verified programmatically: `all mismatches are a
  trailing empty CSV column: True`. These are exactly the two tables that
  declare `InterpolateMode="Linear"`.

### 3.3 Rule reference closure (`06_resolve_refs.py`)

All **227,752** rule cross-references (172,755 `RunRule` + 54,997 `Lookup`)
were resolved against the tables and rules actually present, using the
package itself, the CW package named by `@ProjectName`, or the CW package
named by the XSD `xs:import`:

```
Lookup   local  8,905   parent 476    UNRESOLVED 45,616
RunRule  local 111,210  parent 5,181  named 51,987  UNRESOLVED 4,377
```

**The 49,993 unresolved references reduce to exactly THREE distinct
targets:**

| Target | Count | Interpretation |
|---|---|---|
| `Lookup MatrixFromConstant="Pages" MatrixCol="Name"` | 22,808 | reads `Form Pages/Pages.FormPage.csv` — which does have `Name` and `Number` columns |
| `Lookup MatrixFromConstant="Pages" MatrixCol="Number"` | 22,808 | same |
| `RunRule FileName="MessageHelper" Rule="AddErrorMessage"` | 4,377 | an engine-provided rule library, not shipped |

Excluding those two engine primitives, **reference closure is 100.000%**.
The `Pages` finding is itself a discovery: `Form Pages` is not merely UI
metadata — the rule engine performs table lookups against it.

### 3.4 Empirical key-uniqueness test (`10_key_uniqueness.py`)

Nothing in the corpus states that `<KeyCols>` is a *unique* key, so it was
tested. Across **27,747 tables / 12,557,200 rows**:

- **26,695 tables (96.21%) have a genuinely unique declared key.**
- **1,052 tables (3.79%) do not**, accounting for 171,772 duplicate rows,
  spanning **34 distinct table names**.
- **1,051 of the 1,052 are Domain tables.** Exactly **one** rate table in
  the entire corpus violates it: `GL_NY_20240701_V01` /
  `ElectronicDataLiabilityClassCode`, 4 rows, key `NY|Payroll` duplicated.
- **None of the 1,052 declares a `<Range>`** — interval semantics are not
  the cause.

The worst offender is `DomainTerritoryCodeByZipCode` (323 packages), where
the duplicate key is always the literal sentinel `Other` — consistent with
the `ResultMode="FirstResult"` mode that 86% of Lookups use.

### 3.5 Values that are not what they look like (`out/csv_values_report.txt`)

- **Only 80 blank cells in 45,195,864.** The corpus is essentially
  fully populated.
- **Limits are strings with a coverage-basis suffix, not numbers.**
  390,852 cells hold comma-formatted numerals (`1,000,000`, `500,000`, …, 77
  distinct amounts). Worse, columns such as `EachOccurrenceLimit` and
  `GeneralAggregateLimit` have a **40-value vocabulary** that is the cross
  product of amount × basis:
  `100,000` / `100,000 BI` / `100,000 CSL`, `1,000,000` / `1,000,000 BI` /
  `1,000,000 CSL`, … `CSL` = combined single limit, `BI` = bodily-injury
  only, bare = neither stated. **`"1,000,000"` and `"1,000,000 CSL"` are
  distinct key values.** Any numeric parse of these columns destroys
  information and any naive `int()` fails outright.
- **Sentinel tokens in otherwise-numeric columns — 16 distinct:**

| Token | Cells | Where |
|---|---|---|
| `NA` | 13,398 | `CyberIncidentLiabilityProdsCompldOpsHazardGrade.Grade`, `LossOfElectronicDataProdsCompldOpsHazardGrade.Grade` |
| `Other` | 1,846 | `DomainTerritoryCodeByZipCode.ZipCode`, `DomainZipCode.DataValue` — the catch-all territory |
| **`Refer To Co.`** | 1,153 | `PremOpsIncrdLimitTableAssignment.Assignment`, `DomainIncreasedLimitsTableAssignmentPremOpsOverride.*` — **a rate cell whose value is "this cannot be rated automatically"**, the row-level counterpart of the DOC `Refer to Company` sheet |
| `N/A` | 54 | `DomainIncreasedLimitsTableAssignmentPremOpsOverride.*` |
| `<1 (Yr)`, `9+`, `Unknown` | 30 each | `DomainUnmannedAircraftOperatorYearsOfExperience` — open-ended bucket labels |
| `A`–`F`, `N`, `U`, `Z` | 10–60 each | `UnmannedAircraft*Code.Code` — single-letter code alphabets |

- Range-typed CSVs express intervals as **two adjacent columns** named
  `<X>_From` / `<X>_ToLessThan`; the interval convention lives only in the
  Def's `@RangeType`, never in the CSV.
- Densest tables: `PremOpsLossCost` (541 packages, **1,678,712 rows**,
  key `StateCode|PremOpsTerr|ClassCodeCGLProds`), `PremOpsSizeOfRiskLossCost`
  (743,368), and a family of eleven class-keyed tables at ~667,115 rows each
  that appear in **all 567 packages** (`PremOpsELP`, `PremOpsELPText`,
  `PremOpsHomogeneityIndex`, `ProdsCompldOpsELPFactor`,
  `ProdsCompldOpsLossCost`, …). 24 table names are present in all 567
  packages.

---

## 4. What surprised me / ran counter to the file names

1. **`DOC/` is not documentation-in-the-throwaway-sense.** The name suggests
   a readme. It is in fact the corpus's own declaration of its limits — 5,300
   "Refer to Company" rows and 395 "Not Supported" rows naming specific ISO
   rules and forms. If you want to know what ERC *cannot* do, this
   spreadsheet is the only place it is written down, and it is the only
   category not in a machine-readable format.
2. **`Metadata/` contains no metadata about the package.** No date, no
   version, no product name, no provenance, no manifest. It is a code
   dictionary for join keys. Package identity is inferable only from the
   directory name and the XSD namespace.
3. **`Form Pages` is a rate-engine lookup table.** 45,616 `<Lookup>` calls
   target `MatrixFromConstant="Pages"`. The category name implies a UI
   artefact; the rules read it during rating.
4. **The XSD has no enumerations at all.** I expected a schema for an
   insurance rating product to enumerate limits, deductibles and coverage
   codes. It enumerates nothing — it only bounds decimal precision and string
   length. All controlled vocabularies live in 6,829 Domain Table CSVs, half
   of which have no formal declaration.
5. **Missing Domain Table Defs are a convention, not a defect.** My first
   inventory pass flagged all 573 packages as broken. They aren't: the
   absence of a Def *is* the declaration that the table has the default
   `StateCode / DisplayValue / DataValue` shape — verified for all 3,057.
6. **The rules are a real programming language**, 58 operators deep, with
   recursion (`RunRule`), iteration (`ForEach`), GUIDs, date arithmetic and
   explicit decimal-place control on `Product`. 2.74 characters of text per
   XML element. I had expected structured prose.
7. **The state→countrywide dependency graph is exactly closed** — ten CW
   editions referenced, ten present, zero orphans, and 51,987 rule-level
   `ProjectName` references that never once disagree with the XSD import.
   Corpus integrity is far higher than the directory-naming chaos suggests.
8. **Limit values are compound strings.** `"200,000 CSL"` is a single
   atomic key value. This is invisible in the Def (`Type="string"`) and only
   appears in the data.
9. **Two packages are filed under the wrong jurisdiction** (`DE` under `GA`,
   `PR` under `RI`), and PR's newest edition exists *only* in RI's directory.
   File-system location is not a reliable jurisdiction key; the package name
   is.

---

## 5. Open questions — what the corpus does not settle

1. **`ErcCore` is not in the corpus.** All ten countrywide XSDs import it.
   Without it the schemas are not resolvable and the base types of
   `MasterGLCW` are unknown. *To settle:* obtain the ErcCore schema package
   from the distributor.
2. **The rule execution semantics are undocumented.** I have the complete
   operator vocabulary but not its contract: what `FirstValue @Order="DataDefInputParamConstant"`
   precisely means, what `Locate @OutputAction` does, how `ClearCache` affects
   evaluation, or the order of `<Keys>` binding. *To settle:* the ERC engine
   specification, or the `1. Output.json` from
   `OK/GL_OK 20250601 V01` executed against `1. Input.json`.
3. **`MessageHelper.AddErrorMessage`** (4,377 references) is engine-provided
   and its behaviour is unstated.
4. **The `Status` code vocabulary `A` / `C` / `D`** appears on every Form and
   Ratebook CSV row (13,878 / 6,290 / 6,168 in Form Pages alone). Nothing in
   the corpus defines it. "Add / Change / Delete" is the obvious reading but
   **it is a guess, and if `D` means Delete then 23% of Form Pages rows are
   tombstones that must not be applied.** *To settle:* a data dictionary, or
   a diff of consecutive editions to see whether `D`-rows disappear next
   edition. I did not run that diff.
5. **Whether an edition is cumulative or a delta.** Each package appears
   self-contained (it re-ships all its tables), but I did not diff
   consecutive editions of one jurisdiction to confirm that a later edition
   is a full replacement rather than an overlay. *To settle:* a row-level
   diff of e.g. `GL_NJ 20240601 V01` vs `GL_NJ 20250301 V01`.
6. **The 83 future-dated packages** — are these approved filings or
   provisional? Circular effective dates run to 2027 and are internally
   consistent, but the corpus does not state filing status.
7. **`Base RaaS Overrides`** appears as a DOC sheet in 217 packages. Its
   meaning is not defined anywhere in the machine-readable content. I read
   the sheet inventory but did not extract its rows.
8. **The one non-unique rate table** (`GL_NY_20240701_V01` /
   `ElectronicDataLiabilityClassCode`) is either a data defect or evidence
   that `ResultMode="FirstResult"` is load-bearing for rate tables too.
   Not resolvable from the files.
9. **Interpolation is declared but its arithmetic is not.** `InterpolateMode="Linear"`
   tells you *that* to interpolate, not the rounding or the endpoint
   convention when the exposure falls exactly on a boundary.
10. **Nothing states which countrywide edition a state package is
    *supposed* to pair with** beyond the `xs:import`. The import is
    consistent, but whether ISO intends a state package to be usable against
    a *newer* CW edition is not expressed.

## 6. What I did not examine

- The three root-level files (`GL_ERC_Edition_Hierarchy.html/.xlsx`,
  `GL_ERC_to_Manual.xlsx`) — excluded by instruction.
- The 508 `.zip` archives (redundant with the extracted directories).
- Row-level content of the `Base RaaS Overrides` and `Full Form Name` DOC
  sheets, and the class-description sheets (inventoried in `doc_sheets.csv`,
  not extracted).
- Full row materialisation of the 212 columns with >400 distinct values
  (profiled with min/max/type/top-12 in `column_profile.csv`, but their
  complete vocabularies were not written out).
- Cross-edition diffs of any kind.
- The `xsd_types.csv` output (135 MB, 1.4M rows) was produced but only
  aggregate-analysed, not read row by row.
