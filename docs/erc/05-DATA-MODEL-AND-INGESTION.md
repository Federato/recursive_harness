# ERC Build Specification — Part 2: Data Model and Ingestion

Part 1 (`04-BUILD-SCOPE-AND-RESOLVER.md`) established scope and resolution.
This part specifies what must be stored and how to load it. Part 3
(`06-VALIDATION-AND-BACKLOG.md`) gives the assertions and the backlog.

---

## 1. The data model

Sized against the current corpus: **567 distinct packages** (572 directories,
5 duplicated ids), 86,664 files, 704,515,670 bytes.

### 1.1 Identity and edition

```
Package
  package_id        TEXT PK        # 'GL_NJ_20250301_V01' — from XSD targetNamespace
  jurisdiction      CHAR(2)        # 52 values incl. 'CW'
  edition_date      DATE           # 2020-12-01 .. 2027-04-01
  version           TEXT           # V01..V04
  is_countrywide    BOOL           # 10 true, 557 false
  parent_package_id TEXT FK -> Package  # NULL for countrywide
  xsd_target_ns     TEXT           # the authoritative identity string
  xsd_import_ns     TEXT           # 'ErcCore' for countrywide packages
  source_paths      TEXT[]         # 1 or 2; 5 ids have 2 (byte-identical)
  UNIQUE (jurisdiction, edition_date, version)
```

45 `(jurisdiction, edition_date)` pairs carry >1 version across 102 packages,
so `version` is part of the key, not decoration.

### 1.2 Tables

The corpus declares two kinds and five shapes. **30,773 (package × table)
records**: 23,945 Rate, 6,828 Domain. **450 distinct rate-table names, 375
distinct domain-table names, 836 distinct signatures.**

```
TableDef
  package_id     FK
  kind           ENUM('Rate','Domain')
  table_name     TEXT
  shape          ENUM('flat','banded','interpolated','assignment','statistical')
  metadata_codes TEXT[]           # MetaDataCode children; 72,135 citations corpus-wide
  has_def_xml    BOOL             # FALSE for 3,056 domain tables — see §2.4
  PK (package_id, kind, table_name)

TableColumn
  package_id, kind, table_name  FK
  ordinal        INT             # position in the CSV header — significant
  name           TEXT
  role           ENUM('key','value')
  declared_type  ENUM('string','integer','decimal','long')
  case_insensitive BOOL          # 'false' in all 67,734 occurrences
  range_group    TEXT NULL       # <Range Name> if this column is a range bound
  range_bound    ENUM('from','to_less_than') NULL
  range_type     ENUM('FromInclusiveToExclusive','FromExclusiveToInclusive') NULL
  interpolate    ENUM('Linear') NULL
  range_key_col  TEXT NULL       # ValueCol ranges bind to a KeyCol range

TableRow
  package_id, kind, table_name  FK
  row_ordinal    INT             # preserve — ResultMode='FirstResult' depends on it
  key_values     TEXT[]          # store as TEXT; see §2.5
  value_values   TEXT[]
```

**Declared type vocabulary** (the whole of it): key `string` 66,444 /
`integer` 1,290; value `string` 16,244 / `decimal` 14,505 / `integer` 836 /
`long` 20.

**Key arity distribution:** 0 keys → 3,056 tables (the Def-less domain tables);
2 → 18,396; 3 → 6,634; 4 → 2,256; 5 → 319; 6 → 102; 10 → 10.

**`row_ordinal` is load-bearing.** 86% of `<Lookup>` nodes use
`ResultMode="FirstResult"`, and **1,052 of 27,747 tables (3.79%) have a declared
key that is not unique** (1,051 domain, 1 rate: `GL_NY_20240701_V01` /
`ElectronicDataLiabilityClassCode`). "First" is only meaningful against a stable
order, so CSV row order must be preserved.

### 1.3 Rules

**114,726 `<Rule>` elements** in 20,794 files; 1,032 distinct rule-file names
mapping 1:1 to 1,032 DataDefGroups (filename is always `<group>Rules`, 1,032 of
1,032); 2,323 distinct rule names.

```
Rule
  package_id     FK
  rule_file      TEXT            # == datadef_group + 'Rules'
  rule_name      TEXT
  datadef_group  TEXT
  return_type    ENUM('none','decimal','integer','string','long') NULL
  provenance     ENUM('RuleTypeCountrywide','RuleTypeOverridden',
                      'RuleTypeStateSpecific','RuleTypeSystem')
  body           XML/AST         # store the parsed tree; 52 operators
  PK (package_id, rule_file, rule_name)

RuleRef                          # the call/lookup graph, materialised
  package_id, rule_file, rule_name  FK
  kind           ENUM('RunRule','Lookup')
  target_file    TEXT NULL       # RunRule
  target_rule    TEXT NULL       # RunRule
  target_table   TEXT NULL       # Lookup: MatrixFromConstant
  matrix_col     TEXT NULL       # Lookup: the column read
  result_mode    ENUM('FirstResult','SingleResult') NULL
  project_name   TEXT NULL       # ** presence forces parent dispatch (R11) **
```

`project_name` must be stored. It is present on **51,983 of 172,712** `RunRule`
nodes and is the only signal distinguishing call-super from ordinary recursion.

### 1.4 Forms and the input surface

Five CSVs per package, **each with exactly one distinct header across all 567
packages** — the schema is uniform and can be hard-typed.

```
FormPage         26,336 rows   PK (package_id, table_name, name, form_number)
  type            ENUM('Form','Coverage','Detail','Summary')
  parent_name, attachment_type ENUM('Optional','Conditional','Mandatory','')
  condition       XPATH         # 10,581 rows carry one
  form_number     TEXT          # 1,596 distinct ISO numbers
  min_occurs, max_occurs, sequence, status, metadata_codes

FormField        30,449 rows   PK (package_id, page, table_name, column_name)
  widget_type     ENUM('TEXT','SELECT','CHECKBOX','HIDDEN','TEXTAREA','BUTTON','ANCHOR')
  label, default, minimum, maximum, help_text, comment
  quote_readonly/required/display, policy_readonly/required/display  BOOL
  condition, required_condition, audit_condition  XPATH
  domain_table_name TEXT        # binds the field to its value vocabulary
  sequence, status

FormRelatedField  3,122 rows   # cascading lookups; 33 key collisions (1.06%) — see §2.7
  domain_table_name, related_field, related_xpath

RatebookColumn   15,525 rows    # the rating-required subset of FormField
  rating_required_condition  XPATH    # 4,977 rows carry one

RatebookTable    21,433 rows
  comment, bureau_rule_number
```

**`status`** is `A` / `C` / `D`. Store it; **do not act on it**. Report 02 §2
falsified every reading of the letters: it is static (99.55–100% of rows never
change it across editions), `D` rows survive to the next edition 86.6–98.5% of
the time and are **99.9% rateable**. Discarding `D` would drop 23.4% of Form
Pages and 39.7% of Ratebook Columns.

### 1.5 Metadata, circulars and provenance

Exactly five `*.Metadata.xml` per package; **89,630 entries**, max nesting
depth 1 — a flat code registry.

```
MetadataEntry
  package_id, group ENUM('Circulars','DataDefInfo','DomainTables',
                         'RateTables','BureauRuleNumbers')
  code, name, description, properties  # only 'Comment' and 'Type' exist
  # DataDefInfo Type ∈ Policy(572) / Risk(898) / Coverage(3,326)
  #                    / Schedule(1,895) / Form(12,696)

Circular                              # 766 distinct codes
  code, circular_no, effective_date, filing_reference
  type ENUM('LOSS COST','RULES','FORMS','FORMS & RULES',
            'FORMS & RULES & LOSS COSTS','STATISTICAL PLAN','LOSS COSTS & RULES')
  description
PackageCircular (package_id, circular_code)
```

The `Name` attribute packs four fields in a fixed literal form and a single
regex parsed **766 of 766** with zero failures.

**The metadata contains no date, version or provenance for the package itself** —
searched all 2,865 files for `EffectiveDate|ReleaseDate` as file-level elements:
0 hits. Identity comes from the XSD (part 1 §2.1).

### 1.6 The exception register (DOC)

```
DocException
  package_id
  sheet   ENUM('Refer to Company','Not Supported','Special Consideration')
  rule_number, rule_name, form_number, description,
  implementation_guidelines, comments        # all free text
```

5,300 / 395 / 1,113 rows respectively. **Free text, not codes** — the only
joinable key is `form_number`, and matching requires normalising whitespace and
comparing the first six characters (form family), because DOC cites `CG 22 67`
while Form Pages cites the dated edition `CG 22 67 10 93`. 18,665 of 26,336 form
pages have a parseable number.

### 1.7 What need not be stored

- **`STC/*.json`** (517 files, 506 packages) — sample transactions, not schema.
  Useful as regression fixtures. Do not use for identity: one of 514 disagrees
  with its package's edition (`GL_CO_20270401_V03`, STC says 2027-04-10).
- **`.zip` archives** — redundant with the extracted directories.
- **`Base RaaS Overrides`** and the class-description DOC sheets — inventoried,
  never characterised (see part 06 §3.7).

---

## 2. Ingestion

### 2.1 Enumeration

Two directory layouts exist. 553 of 572 package directories nest the content one
level deeper (`GL_NJ 20250301 V01_MachineReadableContent/GL NJ 20250301 V01/…`);
19 place the categories directly under the package directory. Detect by testing
whether any known category name appears among the immediate subdirectories; if
not and there is exactly one subdirectory, descend.

Two naming conventions (`GL_JJ …_MachineReadableContent` and `GL JJ …`) — both
match `^GL[ _]([A-Z]{2})[ _](\d{8})[ _](V\d+)`, 572 of 572. **Use the name only
to find candidates; take identity from the XSD.**

Exclude `_quarantine_misfiled/` and any non-jurisdiction directory.

### 2.2 Encoding

Every text file is UTF-8 **with a BOM**. Strip `\xef\xbb\xbf` before parsing;
an unstripped BOM corrupts the first CSV header cell and the XML declaration.
All 51,987 XML/XSD files and 33,669 CSVs parsed without error once the BOM is
handled (`PROBLEMS: 0` in every report).

### 2.3 The five table shapes

| Shape | detection | count | handling |
|---|---|---|---|
| **flat** | no `<Range>` | ~29,000 | key tuple → value tuple |
| **banded / step** | `<Range>` in `<KeyCols>` | **164** | interval match; `_From` / `_ToLessThan` columns; honour `RangeType` (`FromInclusiveToExclusive` 108, `FromExclusiveToInclusive` 74) |
| **interpolated band** | `<Range>` in `<ValueCols>` with `InterpolateMode="Linear"` | **18** | linearly interpolate the value across the bound key range — **the cell is not its literal value** |
| **assignment (indirection)** | value column named `*Assignment` | **1,174** | the value is the *name of another table* to consult next |
| **statistical** | value column named `*StatCode` / `*Code` / `*Identifier` | **1,490** | returns a reporting code, not a number |

The interpolated shape, in full:

```xml
<rt:Range Name="PremOpsExposureTimesThousand" Type="decimal" RangeType="FromInclusiveToExclusive">
  <rt:KeyCol Name="PremOpsExposureTimesThousand_From" />
  <rt:KeyCol Name="PremOpsExposureTimesThousand_ToLessThan" />
</rt:Range>
...
<rt:Range Name="Relativity" RangeKeyCol="PremOpsExposureTimesThousand"
          InterpolateMode="Linear" Type="decimal">
  <rt:ValueCol Name="Relativity_From" />
  <rt:ValueCol Name="Relativity_ToLessThan" />
</rt:Range>
```
(`countrywide/GL CW 20260101 V01/Rate Tables/PremOpsSizeOfRiskRelativityDef.RateTableDef.xml`)

Only two table names use it: `PremOpsSizeOfRiskRelativity` and
`ProdsCompldOpsSizeOfRiskRelativity`.

### 2.4 Def / CSV pairing

- **Rate tables are always paired**: 23,945 CSVs, 23,945 Defs, zero exceptions.
- **Domain tables often have no Def**: **3,056 of 6,828**. This is a convention,
  not corruption. **All 3,056 have the identical header
  `StateCode,DisplayValue,DataValue`**, and **all 3,056 are declared in
  `DomainTables.Metadata.xml`**. Synthesise the default shape: keys
  `(StateCode)`, values `(DisplayValue, DataValue)`.
- Naming: `Foo.RateTable.csv` pairs with `FooDef.RateTableDef.xml` — strip the
  trailing `Def` from the base name.

**Known defect to tolerate:** 18 CSVs have a trailing comma on the header line,
producing a phantom unnamed always-blank final column. All 18 are the two
interpolated tables across 9 packages. Verified: `all mismatches are a trailing
empty CSV column: True`. Drop a trailing empty header cell; do not fail the load.

### 2.5 Values are strings until proven otherwise

**Store every cell as text. Parse on use, guided by the declared type.**

- **Limits are compound strings.** `EachOccurrenceLimit` has a 40-value
  vocabulary that is amount × basis: `100,000`, `100,000 BI`, `100,000 CSL`,
  `1,000,000`, `1,000,000 BI`, `1,000,000 CSL`, … `"1,000,000"` and
  `"1,000,000 CSL"` are **distinct key values**. 390,852 cells hold
  comma-formatted numerals across 77 distinct amounts. `int()` fails outright;
  stripping commas destroys the basis distinction and corrupts the key.
- **Sentinels in numeric columns** — 16 distinct tokens:

| Token | cells | meaning as far as the data shows |
|---|---|---|
| `NA` | 13,398 | `*HazardGrade.Grade` — no grade |
| `Other` | 1,846 | catch-all territory / ZIP; **the cause of the duplicate-key finding** |
| `Refer To Co.` | **1,153** | **no automated answer exists** — must surface, not fail |
| `N/A` | 54 | increased-limits override |
| `<1 (Yr)`, `9+`, `Unknown` | 30 each | open-ended buckets |
| `A`–`F`, `N`, `U`, `Z` | 10–60 | single-letter code alphabets |

- **Blanks are near-absent**: 80 blank cells in 45,195,864. A blank is
  anomalous, not routine.
- The XSD constrains **precision only** — 203,489 `xs:decimal` restrictions with
  `fractionDigits`/`totalDigits`, 49,030 `xs:string` with `length`. **There are
  no `xs:enumeration` elements anywhere** in the corpus. Value vocabularies live
  in the 6,828 domain tables, not the schema.

### 2.6 Rules

Parse to an AST, preserving element order (`<Sequence>` is ordered) and all
attributes. **52 operators.** Attributes that must survive parsing because they
change behaviour: `RunRule@ProjectName` (dispatch), `Lookup@ResultMode`,
`Lookup@MatrixCol`, `Lookup@MatrixFromConstant`, `FirstValue@Order`,
`Product@DecimalPlaces`, `Round@DecimalPlaces`, `Range@RangeType`,
`ForEach@AtDataDef`, `Locate@OutputAction`, `Remove@RemoveMultiple`,
`Rule@MetadataCodes` (provenance), `Rule@Type` (return type).

Data addressing is XPath-like over the DataDef tree: `../`, `/*/`,
and absolute-ish paths such as `/*/State/Code`. `SetFinalRate` reaches five
levels up (`../../../../../PackageModFactor`) from a classification-coverage row
to the policy. The engine needs a real tree with parent links, not a flat map.

`WithArgs` / `Arg @Param` / `Value @FromParam` is lexically-scoped parameter
passing — observed parameter names include `calculatedPremium`, `limit`,
`coverage`, `eachOccurrenceLimit`, `TableName`, `Message`. Rules invoked this
way appear as graph roots if you only follow `RunRule`; they are not orphans.

### 2.7 Row keys for the form CSVs

If diffing or indexing form rows, these keys were validated across 96,828 rows
with **33 collisions (0.034%), all in Form Related Fields**:

| File | key |
|---|---|
| Form Pages | (TableName, Name, Number) |
| Form Fields | (Page, TableName, ColumnName) |
| Form Related Fields | (Page, TableName, ColumnName, RelatedField) |
| Ratebook Columns | (TableName, ColumnName) |
| Ratebook Tables | (TableName) |

### 2.8 Load order

```
1. enumerate package directories (exclude quarantine)
2. parse DataDefs/*.xsd  -> identity + parent import      # authoritative
3. dedupe by package_id
4. load the 10 countrywide packages first
5. resolve each state package's parent; fail loudly if absent
6. load Metadata/*.xml   -> code registry + circulars
7. load Rate/Domain Tables (Def then CSV; synthesise missing domain Defs)
8. load Rules -> AST + RuleRef edges
9. load the five form CSVs
10. load DOC exception sheets (xlsx)
11. run the part-06 assertions; refuse the load on any BLOCKER
```

Countrywide must load first because state packages reference it and because
step 5 needs it resolvable.

### 2.9 Scale

Full-corpus passes were run repeatedly during analysis with Python's standard
library plus `openpyxl`, multiprocessing over packages: 30,773 table CSVs
(12,853,103 rows, 45.2M cells), 20,794 rule files (2,052,236 XML elements),
567 XSDs (largest 300 KB, ~28,000 elements). Nothing here needs a database
engine to *ingest*; it needs one to *query*.
