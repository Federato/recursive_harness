# 08 — Ingestion Specification (PDF → Structured Data)

The ingestion pipeline is not a one-off script. It is a versioned, re-runnable component,
because new notices arrive continuously (the corpus already spans 2021→2027 with 41 notices
dated 2027).

---

## 8.1 Pipeline stages

```
 [1] ACQUIRE      file + sha256 + filename parse
 [2] EXTRACT      dual-mode text extraction, with fallback
 [3] SEGMENT      cover page / TOC / rule body / tables / classification / ILTA
 [4] PARSE        typed extractors per segment class
 [5] VALIDATE     structural + cross-document assertions
 [6] STAGE        write to staging tables with provenance
 [7] PROMOTE      diff vs current edition, assign effective dates, publish
```

Stages 1–5 are idempotent and side-effect-free. Only stage 7 mutates live data.

---

## 8.2 Stage 1 — Acquire

Filename grammar (validated across all 503 rules files and all 472 loss cost files):

```
GL-<JURIS>-<YYYY>-<KIND>-<NNN>-C.pdf
   JURIS ∈ {50 states} ∪ {DC, PR, MU}      MU = multistate/countrywide
   KIND  ∈ {RU, LC}                        RU = Rules,  LC = Loss Costs
   YYYY  ∈ 2020..2027
   NNN   = zero-padded notice sequence within (JURIS, YYYY, KIND)
```

`KIND` selects the whole downstream pipeline: `RU` documents are prose with embedded factor
tables; `LC` documents are almost entirely numeric grids and take a **different extractor**
(§8.3). No `MU` file exists with `KIND = LC` — there is no countrywide loss cost document.

Reject or quarantine anything that does not match. **Handle the duplicate-download pattern
explicitly:** three files in the corpus carry a `" (1)"` / `" (2)"` suffix
(`GL-DE-2022-RU-001-C (1)`, `GL-MU-2023-RU-002-C (1)`, `GL-IA-2023-RU-002-C (2)`). Deduplicate
by `sha256`, not by filename.

---

## 8.3 Stage 2 — Extract (three modes, selected by page family)

This is the stage most likely to be got wrong, so it is specified precisely. **The correct mode
depends on the page family, not on the document**, and the rule that serves the Rules corpus is
actively wrong for the loss cost grids.

| Mode | Command | Used for | Why |
|---|---|---|---|
| **Reading order** | `pdftotext <in> <out>` | Rule headings, deviation verbs, rule bodies | The exception pages are **two-column**. In layout mode a left-column heading and an unrelated right-column heading land on the same physical line, destroying `^RULE n.` anchoring. Reading order emits `RULE 11. POLICY CANCELLATIONS` as one clean line. |
| **Layout** | `pdftotext -layout <in> <out>` | ILF matrices (Rule 56.B), ILTA class grids, medpay/split-limit tables | Column position **is** the data. Reading order collapses a 7-column factor matrix into unordered numbers. |
| **`pypdf`** | `pypdf.PdfReader(..., strict=False)` | **All `CG-LC`, `CG-ELP` and `CG-LCADD` pages**, plus any file with a damaged xref | Alone among the three, it preserves row pairing on the loss cost grids. See below. |

### 8.3.1 The loss cost grids require `pypdf`, not `-layout`

On a `CG-LC` grid page, `pdftotext -layout` **interleaves rows**: class codes drift onto their
own lines and values shift up onto the preceding code.

```
pdftotext -layout  (Georgia, CG-LC-1)                     <-- WRONG
  10010
  10011      .199   .156  10150     .78   (a) 11204  .49   1.33 13111  2.99  .069
  10012      .048  (a)    10151  19.60      – 11205  (a)      – 13112   .084  .044

pypdf              (same page)                             <-- CORRECT
  10010 .199 .156 10150 .78 (a) 11204 .49 1.33 13111 2.99 .069
  10011 .048 (a)  10151 19.60 – 11205 (a)  –   13112 .084 .044
  10012 .054 (a)  10160 3.51  – 11206 .76  –   13201 .93  .097
```

Class `10010` loses its values entirely and `10011`'s shift onto it. **The failure is silent
and every resulting number is a plausible loss cost.** There is no downstream assertion that
catches a rate attached to the wrong class code, which is why this is specified at the
extraction stage rather than caught at validation.

Verified on GA, TX and NY (where `pdftotext` succeeds) and on AK and AL (xref-damaged);
`pypdf` paired correctly in every case. Arithmetic confirmation: Indiana at 4 territories ×
1,188 classes × 2 columns = **9,504** cells, and the `pypdf` parse returns exactly 9,504
(5,828 numeric + 1,780 `(a)` + 1,896 `–`).

**Cost of using `pypdf`:** it injects spaces inside words — `UNMANNED AIRCRAFT LI MITED
LIABILITY`, `SUB LINE`, `CG -LC -89`. **Every caption match, page-marker match and section
detector on `pypdf` output must be whitespace-normalised** (`re.sub(r"\s+", "", s).upper()`)
before comparison, and page-marker regexes must tolerate internal spaces
(`CG\s*-\s*LC\s*-\s*(\d{1,3})`). A literal match under-reports rather than errors.

### 8.3.2 Fallback and failure

103 of 503 rules files and **83 of 472** loss cost files have a damaged xref table and fail
`pdftotext` silently (exit 0, empty output). All were recovered with `pypdf`. The pipeline
must:

1. Select the mode from the page family (§8.3, §8.4).
2. If a `pdftotext` mode is selected and output is `< 2 KB`, retry with `pypdf`.
3. If both fail, mark `extraction_status='FAILED'` and quarantine.

Two files are unrecoverable: `GL-MO-2027-RU-003-C.pdf` and `GL-MI-2027-LC-003-C.pdf` (both
truncated, no xref/EOF).

> Never treat `pdftotext` exit code 0 as success. It returns 0 while emitting syntax errors to
> stderr and producing nothing.

---

## 8.4 Stage 3 — Segment

| Segment | Detection |
|---|---|
| Cover page | `NOTICE GL-<ST>-<YYYY>-RU-<NNN>` + `REFERENCE INFORMATION (FOR COMPANY USE ONLY)` |
| Table of contents / Index | `TABLE OF CONTENTS` / `INDEX`, page markers `CG-i` … `CG-vi`; **dotted leaders (`....`) reliably distinguish TOC lines from body lines** |
| Rule body | `^RULE (A?\d{1,3}[A-Z]?)\.` at line start, in reading-order text |
| Section header | `^SECTION ([IVX]+)` |
| Exception pages | header band `GENERAL LIABILITY / EXCEPTION PAGES`, page markers `CG-E-n` |
| ILF tables | caption `Table 56.B.<n>. <family> (Subline Code <ccc>)` |
| ILTA pages | header `INCREASED LIMITS TABLE ASSIGNMENTS`, page markers `CG-ILADD-n` |
| Classification table | header `CLASSIFICATION TABLE PAGES`, page markers `CG-CT-n` |
| **Loss cost grid** | header `LOSS COST PAGES`, page markers `CG-LC-n`; territory from `PREM/OPS TERR. <nnn>` in the header band |
| **Loss cost misc page** | the single `CG-LC-<8T+1>` page — flat all-territory tables (Unmanned Aircraft, OCP/PP), no class grid |
| **ELP pages** | header `ESTIMATED LOSS POTENTIAL PAGES`, page markers `CG-ELP-n`, body anchored on `PROCEDURE <n>.` |
| **Loss cost addendum** | header `LOSS COST ADDENDUM PAGES`, page marker `CG-LCADD-n`, caption `Table #n(LCADD) Loss Cost Mapping By Class` |
| **Territory pages** | header `TERRITORY PAGES`, page markers `CG-T-n` — **in the Rules notice**, after the exception pages. `CG-T-1` is the definitions page; `CG-T-2…n` carry either the ZIP table or the `LIST OF IMPORTANT CITIES AND TOWNS` |

**TOC-vs-body disambiguation matters.** Rule titles appear in the TOC, the Index *and* the
body. Parsing without excluding leader-dot lines double-counts every rule. The rule is: a body
heading is followed within ~12 lines by an operative verb phrase; a TOC line is followed by
dots and a page number.

---

## 8.5 Stage 4 — Parse

### 8.5.1 Rule headings

```
^RULE\s+(A?\d{1,3}[A-Z]?)\.\s*(.*)$
```
Title may be on the same line (reading order) or the next line. Strip a trailing `(Cont'd)`
and **do not** emit a new rule record for continuation headings — the same rule spans pages
and would otherwise be counted many times.

### 8.5.2 Deviation operations

Classify from the ~12 lines following the heading:

| Pattern | `op` |
|---|---|
| `(is\|are) replaced by the following` | `REPLACE` |
| `[Tt]he following (is\|are) added` · `(is\|are) added to` | `ADD` |
| `does not apply` · `do not apply` · `(is\|are) deleted` | `DELETE` |
| `(is\|are) amended` | `AMEND` |
| `[Tt]he following (table\|tables\|factors)` · `tables follow` | `TABLE` |

Extract `target_path` from:
```
(Paragraphs?|Subparagraphs?|Table|Rule)\s+([A-Z0-9][A-Za-z0-9.,\s]{0,40}?)\s+(?:is|are)\s+(replaced|added|amended|deleted)
```
Note that multi-target forms occur (*"Paragraphs C.2. and C.3. are replaced"*) — store as a
list, not a scalar.

A rule may carry **more than one** operation (e.g. Rule 24 in a jurisdiction that both replaces
`E.2.m.` and adds to `E.2.`). The model is many-to-one deviation→rule; do not collapse.

### 8.5.3 ILF matrices (layout mode)

The hardest parse in the corpus. Structure per table:

- Caption above: `Table <n> — $<basic limit> Basic Limit`
- Column header row: `Per Occurrence` spanning; then limits in $000s
- Row stub: `Aggregate $ <limit>`
- A mid-table sentinel: **`The following factors MUST be referred to company before using.`**
  — everything after it in that table sets `refer_to_company = true`
- Caption below: `Table 56.B.<n>. <family> (Subline Code <ccc>)`

Cells are sparse — the upper-right/lower-left of the matrix is legitimately empty (an
aggregate below the occurrence limit is not offered). **Empty ≠ zero.** Do not densify.

Recommended approach: extract with word-level coordinates (`pdftotext -bbox-layout` or
`pdfplumber`) and cluster on x-position rather than parsing whitespace-aligned text. The
whitespace form is readable by eye but ragged enough that column inference from spaces alone
will misalign on the wider tables.

### 8.5.4 ILTA grids

Six repeating `Class Code | Table` column pairs per page, under headers like
`Class Codes 10010 – 15699`. Values are composite (`1A`, `2B`, `3C`); store `raw_code` and the
decomposed digit/letter (see `06-DATA-SCHEMA.md` §6.6).

Also parse the **addendum** form observed in Illinois — `Table #1(ILADD) Increased Limits Table
Assignments Mapping By Class` — which assigns tables to classes newly introduced by a
multistate filing (e.g. `GL-2020-RMJRU`). These are additive to the main ILTA grid, not a
replacement.

### 8.5.5 Loss cost grids (`pypdf` mode)

Four repeating column groups of `Class Code | Prem/Ops | Prod/COps`, 40 rows per group, 160
class codes per page. On `pypdf` output a data row is one physical line:

```
^\s*((?:\d{5}\s+(?:\(a\)|–|[\d,]*\.?\d+)\s+(?:\(a\)|–|[\d,]*\.?\d+)\s*){1,4})$
```

The cell alphabet is **closed** — exactly three tokens, and anything else is a parse failure,
not a new value:

| Token | Meaning | Storage |
|---|---|---|
| numeric | Published ISO loss cost, pre-LCM | `loss_cost` |
| `–` (en dash, U+2013) | Coverage not offered for this class/subline (Rule 48.F.1's `(−)`) | `disposition = 'NOT_OFFERED'` |
| `(a)` | Refer to company; consult the ELP | `disposition = 'REFER'` |

**Never coerce `–` or `(a)` to zero.** Zero is a free policy; `–` is a declination.

Territory comes from the page header band (`PREM/OPS TERR. 501`), Prod/COps is always
statewide `999` — take it from the header line
`Products/Completed Operations (Prod/COps)(Subline Code 336) Entire State Territory 999`
rather than assuming.

### 8.5.6 ELP pages (`pypdf` mode)

Two column groups per line, each `Class Code | Prem/Ops ELP [H/R] | Prod/COps ELP [H/R]`.
The alphabet is **four**-valued and side-dependent:

| Token | Side | Meaning |
|---|---|---|
| `Manual` + `–` | either | A loss cost exists on the grid — do not use an ELP |
| `$n.nn` + `d/L` | either | Published ELP with Homogeneity/Reliability index, `d ∈ 1..5`, `L ∈ A..E` |
| `RTC` | either | Refer to company; no ELP reference exists |
| `Incl.` + `–` | Prod/COps only | Products/Completed Operations is included in Premises/Operations **at no additional charge** — a rating instruction, not a value |

Parse the H/R index as a **pair**, never as a single token: `4/A` is homogeneity 4 and
reliability A. It is absent for `RTC` and `Incl.` rows.

Table 5.C additionally contains one free-text ELP that is not a number —
`15191 Percentage of otherwise applicable Workers Compensation loss costs: 75%` — present in
all 51 jurisdictions. Store it as a typed external-reference ELP, not as `NULL`.

### 8.5.7 Loss cost addendum (`CG-LCADD`)

Derived-rate mappings for classes introduced by a multistate filing:

```
Use <n>% of premises/operations loss cost of class <ccccc>
```

Store as `(new_class, pct, source_class, source_subline)` and resolve **recursively** at rate
time with cycle detection — the target may itself be `(a)`. Present in only 2 of the 51
current notices (NY, PR) but in 69 notices historically, so a historical re-rate needs it.

### 8.5.8 Territory pages (`CG-T`, in the Rules notices)

`CG-T-1` first assigns the non-territorial sublines, and this assignment is explicit — do not
infer it:

```
Owners or Contractors Protective Liability (Subline Code 335)
Pollution Liability (Subline Code 350)
Railroad Protective Liability (Subline Code 335)
  ENTIRE STATE ......... 999
Products and Completed Operations (Subline Code 336)
  ENTIRE STATE ......... 999
Premises and Operations (Subline Code 334)
Liquor Liability (Subline Code 332)
  <territory definitions follow>
```

Then one of **three** schemes, which the parser must detect rather than assume:

| Scheme | Detect on | Row grammar |
|---|---|---|
| **Entire state** (20) | `CG-T-1` is the only `CG-T` page and reads `ENTIRE STATE … 001` | none |
| **ZIP table** (27) | caption `ZIP Codes/Territories In Numerical Order By ZIP Code`, tables `Table #n(T)` | `^(\d{5})\s+(<USPS name>)\s+(\d{3})$`, four column groups per page, ~80 rows/page |
| **County / city** (CA, FL, NY, TX) | `CG-T-1` lists counties, followed by `LIST OF IMPORTANT CITIES AND TOWNS` | `^(<City>),\s*(<County>)\s*\.{2,}\s*(\d{3})$` |

Volume: **23,719 ZIP rows** and **432 city/county rows** across the latest notice per
jurisdiction.

Two parser requirements specific to these pages:

1. **The county/city scheme is not a degraded ZIP scheme.** Its key is `(county, place_name)`,
   both required, and the place lists date from 1996–2008 editions. Resolution failures must
   surface as referrals; never fall back to a nearest-name match.
2. **Leader dots are the field separator**, not whitespace — `Ardsley, Westchester ......... 009`.
   Parse on the dot run, because both the place name and the county contain spaces.

### 8.5.9 Classification table

Record delimiter: `^(\d{5}) (.+)$` followed by an indented `Class Code:` line. Fields:
`Class Code`, `Premium Base`, `Application`, `Application Exception`,
`For Premium Computation Purposes`, `Separately Classify And Rate`.

---

## 8.6 Stage 5 — Validation assertions

Fail the load, don't warn, on any of these:

| # | Assertion |
|---|---|
| V1 | Every `state_deviation.printed_number` resolves in `rule_number_map` for the notice's numbering scheme |
| V2 | `state_deviation.printed_title` equals `rule_number_map.printed_title` for the resolved key (catches wrong-scheme resolution — see `07` §7.4) |
| V3 | Every `ilta_assignment.class_code` exists in the CW `classification` table for the same period |
| V4 | Every ILTA `prem_ops_table` ∈ {1,2,3} and `prod_compops_table` ∈ {A,B,C} |
| V5 | Every ILF table referenced by an ILTA exists in that jurisdiction's `ilf_table` |
| V6 | ILF factors are monotonically non-decreasing along both the occurrence and aggregate axes |
| V7 | Every jurisdiction has ≥1 Prem-Ops, ≥1 Prod/CompOps and ≥1 Railroad-Protective ILF table (observed true for all 51) |
| V8 | `PAYROLL.SHAPE` resolves for all 51 jurisdictions (observed: no `NOT_FOUND`) |
| V9 | `LIQUOR.NUMERICAL_GRADE` ∈ 0..10 per Rule 45.H (observed range 0–8) |
| V10 | No two live editions for the same jurisdiction have overlapping effective ranges |
| V11 | Notice rule-set size is within tolerance of the prior notice for that jurisdiction (guards against a partial extraction being promoted — the IL series is stable at 18–19 rules across 17 notices) |
| V12 | Every notice records **the countrywide edition it was authored against**, captured from the notice itself and never inferred from dates (`12-VERSIONING-AND-EDITIONS.md` invariant I1) |
| V13 | Every `endorsement.form_number` matches `^(CG\|IL) \d{2} \d{2}$`, and every form in a `MANDATORY_*` role resolves to a governing paragraph |
| V14 | Hazard-grade rows (Tables 40.F / 40.G) parse to exactly one Prem-Ops and one Prod/CompOps grade in `{1,2,3,4}` per class code; a row yielding a different count is rejected, not defaulted |
| V15 | Every `endorsement_constraint` names two forms that both exist in the same edition's catalog |
| V16 | A loss cost notice's `CG-LC` page count equals **`8·T + 1`**, where `T` is the number of distinct Premises/Operations territories on its grid pages (observed true for all 51 current notices) |
| V17 | Every loss cost cell is exactly one of `numeric`, `–`, `(a)`. Any fourth token fails the load — it means the row split wrongly, not that a new value exists |
| V18 | Per territory, the parsed cell count equals `class_codes × 2`. Indiana: 1,188 × 2 × 4 territories = 9,504. This is the alignment net for the grid parse, the counterpart of V6 for the ILF matrices |
| V19 | No class code resolves to `Manual` in the ELP **and** `(a)` on the loss cost grid for the same `(jurisdiction, edition, subline)` — the two sources contradict each other |
| V20 | Every `CG-LCADD` mapping resolves to a source class that exists on the same notice's grid, and the mapping graph is **acyclic** |
| V21 | Every Prod/COps loss cost row is written to territory `999`; every Prem/Ops row to a territory in that jurisdiction's enumerated domain (`A4-LOSS-COST-INVENTORY.md` §A4.1) |
| V22 | **Cross-corpus territory agreement** — the territory codes on the Rules notice's `CG-T` pages equal the territories published on the loss cost grids, for every jurisdiction (observed: **51/51 exact, zero mismatches**) |
| V23 | Every jurisdiction resolves to exactly one territory scheme ∈ {`ENTIRE_STATE`, `ZIP_TABLE`, `COUNTY_CITY`}, and a `ZIP_TABLE` jurisdiction has ≥1 `CG-T-2+` page |

**V22 is the highest-value assertion in this section** because it is a genuine *independent*
check. The Rules territory pages and the loss cost grids are separate documents on separate
release cycles, parsed by different code paths; agreement on all 51 domains cannot happen by
accident, and disagreement means one of the two parses — or one of the two editions — is
wrong. It is the only place in the pipeline where an external oracle exists.

**V18 is to the loss cost grids what V6 is to the ILF matrices**, and it is the only cheap
defence against the `-layout` misalignment described in §8.3.1. A misaligned parse drops cells
and therefore fails the count; a correctly aligned one reconciles exactly. Run it per
territory, not per document — a document-level total can net out a shortfall in one territory
against an over-read in another.

**V17 exists because the cell alphabet is closed and small.** In a corpus of ~430,000 cells
across 51 jurisdictions, exactly three tokens occur. A fourth is always a parse defect, and
tolerating it silently admits a wrong rate.

V6 is a genuine data-quality net for the matrix parse: a misaligned column produces a factor
that decreases as the limit rises, which is detectable without a second source.

**V12 is the highest-value new assertion.** Edition attribution drives overlay resolution
(`07` §7.4), and `01-SOURCE-CORPUS.md` records that 264 of 503 PDFs currently carry
low-confidence dates. A wrong edition attribution is invisible at runtime — it produces a
plausible premium.

**V14 exists because Tables 40.F and 40.G are the corpus's hardest extraction.** They are
multi-column tables with wrapping rows spanning manual pages `CG-60`–`CG-69`; reading-order
extraction interleaves the two grade columns. A silently mis-aligned hazard grade moves the
Loss Of Electronic Data or Cyber premium by up to 7× (Tables 40.C–40.E,
`11-RATING-ARCHITECTURE.md` §11.5.2). The manual's own default — unlisted classes are Hazard
Grade 1 — applies only to classes genuinely absent from the table, never to rows that failed
to parse.

---

## 8.7 Stage 7 — Promote

1. Compute the diff of the incoming notice against the current live edition for that
   jurisdiction (rule set, variable values, ILF cells, ILTA rows).
2. Assign `effective_from` from the **ERC circular metadata**, joined via the cover-page
   circular/filing references — **not** from the page-footer edition marker.
3. Close the prior edition (`effective_to = new.effective_from - 1 day`).
4. Publish; invalidate the resolver cache for that jurisdiction.

The diff in step 1 is also the human review artefact: a reviewer should see "TX executive
officer payroll 31,900 → 39,800; Liquor grade unchanged; 4 ILF cells changed" rather than a
wall of text.

---

## 8.8 Re-runnability and historical backfill

The full corpus (490 de-duplicated notices) should be ingested, not just the latest per
jurisdiction. All summary tables in this document set are computed from latest-per-jurisdiction
and are labelled as such; historical rating requires the full set, which the pipeline produces
at no extra design cost. Reprocessing is safe because stages 1–5 are pure and every fact is
keyed by `(edition_id, …)`.
