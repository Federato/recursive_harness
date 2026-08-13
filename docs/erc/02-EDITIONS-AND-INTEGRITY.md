# ISO ERC General Liability — Editions, Status Semantics, Integrity, Self-Description

Follow-on to `01-CORPUS-AND-SCHEMA.md`, settling the open questions raised there.
Same clean-room constraint: everything derives from the ERC packages under
`C:\Projects\ISO_ERC_Files\General_Liability\`. No excluded path was opened.

**`C:\Projects\ISO_ERC_Files\` was treated as strictly read-only.** Nothing was
moved, renamed, deleted or rewritten. `15_integrity.py` opens files for reading
and hashing only. The misfiled packages were left exactly where they are; §3
recommends remediation but does not perform it.

New scripts (continuing the numbered pipeline in `scripts\erc\`):

| Script | Produces |
|---|---|
| `11_fingerprint.py` | `fp_tables.csv`, `fp_rules.csv`, `fp_form_rows.csv` — content hashes for every artefact in every package |
| `12_edition_diff.py` | `edition_pairs.csv`, `edition_series.csv`, `edition_diff.txt` |
| `13_status.py` | `status_transitions.csv`, `status_report.txt` — three falsifiable hypothesis tests |
| `14_status_semantics.py` | `status_semantics.txt` — six co-variation tests |
| `15_integrity.py` | `integrity.txt`, `integrity_packages.csv` |
| `16_self_dating.py` | `self_dating.csv`, `self_dating.txt` |
| `17_status_vs_doc.py` | `status_vs_doc.txt` — Status joined to the DOC exception register |

Fingerprint basis: for tables, a sha1 over the **sorted set of data rows**
(order-insensitive, BOM/CRLF-normalised); for rules, a sha1 over the
whitespace-normalised XML text; for form CSVs, a sha1 over the non-key,
non-Status fields of each row. `fp_tables.csv` covers 30,804 tables,
`fp_rules.csv` 20,802 rule files, `fp_form_rows.csv` 96,865 form rows.

Row-key validity check for the form CSVs: keys collide within a single file
**33 times out of 96,865 rows (0.034%)**, all in `Form Related Fields`. Every
Status conclusion below is therefore drawn on a ≥99.97% unambiguous key.

---

## 1. Are editions cumulative or deltas?

**Answer: cumulative full snapshots, on the time axis — decisively. But the
jurisdiction axis is a sparse overlay, and that distinction is the real answer.**
Confidence: very high.

### 1.1 Method

`12_edition_diff.py` groups packages by the jurisdiction **in the package name**
(not the directory — see §3), orders them by (edition date, version), and diffs
each of the **515 consecutive pairs** across **52 jurisdictions / 567 packages**,
independently for eight categories. Two competing predictions were stated in
advance:

- *delta model* — carry-over ratio near 0, series totals shrinking
- *snapshot model* — carry-over near 100%, drops rare, high unchanged fraction

### 1.2 Result (`out/edition_diff.txt`)

| Category | pairs | prev | added | dropped | carried | identical | **carry %** | **identical %** |
|---|---|---|---|---|---|---|---|---|
| Rate Tables | 515 | 21,696 | 284 | 492 | 21,204 | 18,736 | **97.73%** | 88.36% |
| Domain Tables | 515 | 6,160 | 51 | 108 | 6,052 | 5,811 | **98.25%** | 96.02% |
| Rules | 515 | 18,674 | 382 | 432 | 18,242 | 14,777 | **97.69%** | 81.01% |
| Form Pages | 515 | 23,629 | 1,502 | 1,727 | 21,902 | 21,264 | **92.69%** | 97.09% |
| Form Fields | 515 | 27,436 | 1,286 | 1,168 | 26,268 | 25,524 | **95.74%** | 97.17% |
| Form Related Fields | 283 | 2,870 | 98 | 164 | 2,706 | 2,704 | **94.29%** | 99.93% |
| Ratebook Columns | 515 | 13,933 | 371 | 514 | 13,419 | 10,671 | **96.31%** | 79.52% |
| Ratebook Tables | 515 | 19,137 | 661 | 754 | 18,383 | 17,298 | **96.06%** | 94.10% |

Carry-over is **92.7%–98.3%** in every category. The delta model predicted
near 0%. It is refuted for all eight categories with no exceptions.

Series totals are stable, not shrinking: across all consecutive pairs the rate-table
count **grew 61, shrank 63, stayed flat 391**; rules grew 63 / shrank 29 / flat 423;
form pages grew 67 / shrank 42 / flat 406. A delta series would decline sharply
after the first edition. It does not.

The answer **does not differ by category**. It differs only in *degree of churn*:
Rules and Ratebook Columns churn most (81.0% / 79.5% of carried artefacts are
byte-identical), Form Related Fields least (99.93%).

### 1.3 The drops are not losses — a second, sharper test

492 rate-table and 108 domain-table drops occurred across the 515 pairs. If
editions were cumulative-with-retirement, some content should genuinely vanish.
It does not. For every dropped state table I checked whether it exists in the
countrywide package that the **new** edition's XSD imports:

```
dropped state tables across all consecutive pairs : 600
  present in the CW package the NEW edition imports : 600  (100.0%)
  already present in the CW package the OLD edition imported : 600 (100.0%)
  newly absorbed by countrywide                     :   0  (0.0%)
  genuinely gone from both state and countrywide    :   0  (0.0%)
```

**Not one artefact is ever lost.** A "drop" is always the *withdrawal of a state
override*, after which the jurisdiction falls back to the countrywide table it
was already shadowing. This is why row totals can fall (AK 13,079 → 12,419 rate
rows from first to last edition) while nothing is actually retired.

### 1.4 The orthogonal axis: state packages are overlays, not snapshots

Comparing each of the 557 state packages against the countrywide package its
own XSD imports:

| Measure | Total | Per package (min / median / max) |
|---|---|---|
| Tables in the state package | 21,694 + 3,673 | 27 / **40** / 202 |
| Tables in its countrywide parent | — | 489 / **524** / 537 |
| Tables present **only** in countrywide | 266,932 | 361 / **485** / 511 |
| Tables in **both** (state shadows CW) | 21,694 | 26 / **36** / 129 |
| …of those, **byte-identical** to the CW copy | **36 (0.17%)** | 0 / **0** / 3 |
| Tables **only** in the state package | 3,673 | 0 / **3** / 74 |

So: a state package carries a median of 40 tables against its parent's 524. A
median of **485 tables exist only countrywide**, and where a state does ship a
table the parent also has, it is a genuine override — **only 36 of 21,694
(0.17%) are byte-identical copies**.

**A state package is not independently usable.** Rating a jurisdiction requires
the state package ∪ the specific countrywide edition its XSD names.

### 1.5 What would falsify this

- Finding a state artefact that disappears between consecutive editions and is
  *not* present in the new edition's countrywide parent (currently 0 of 600).
- Finding a jurisdiction whose later editions carry materially fewer artefacts
  in a sustained decline rather than fluctuating (currently 63 shrink vs 61
  grow vs 391 flat).
- Finding a package whose tables are only meaningful when merged with the
  *previous* edition of the same jurisdiction — i.e. a table whose row set is
  visibly partial. Not tested directly at row level for every table; the
  order-insensitive row-set hashes make partiality detectable only via row
  counts, which are stable.

**Caveat I did not eliminate:** carry-over was measured at *artefact* identity
(table name, rule file name, form row key). A table could in principle be a full
snapshot at the name level while shipping only changed *rows*. Against this: the
eleven class-keyed tables carry ~1,176 rows in every one of the 567 packages
(`01-CORPUS-AND-SCHEMA.md` §3.5) and 88.4% of carried rate tables are
byte-identical row sets — a delta would show near-zero identical row sets.

---

## 2. Decoding `Status` = A / C / D

**Answer: the letters do NOT mean Add / Change / Delete. The change-flag reading
is falsified. What Status does mean is still undetermined — but the operationally
important part is settled: a consumer must not discard `D` rows.**
Confidence: high on the falsification; low on any positive interpretation.

### 2.1 Distribution (`out/status_report.txt`)

| Category | rows | A | C | D |
|---|---|---|---|---|
| Form Fields | 30,322 | 81.6% | 9.2% | 9.2% |
| Form Pages | 26,157 | 52.8% | 23.8% | 23.4% |
| Form Related Fields | 3,085 | 67.6% | 32.4% | — |
| Ratebook Columns | 15,444 | 55.2% | 5.2% | 39.6% |
| Ratebook Tables | 21,281 | 61.7% | 38.3% | — |

Two categories have **no `D` at all**. Any interpretation must survive that.

### 2.2 Three hypothesis tests, each against its own base rate

`13_status.py` tests each hypothesis as a *lift* over the base rate for all
rows, so that ordinary churn cannot be mistaken for signal.

**H-delete — "a `D` row is gone next edition":**

| Category | D rows | D gone | D gone % | base gone % | lift |
|---|---|---|---|---|---|
| Form Fields | 2,415 | 37 | 1.53% | 4.26% | **0.36×** |
| Form Pages | 5,583 | 749 | 13.42% | 7.31% | 1.84× |
| Ratebook Columns | 5,532 | 457 | 8.26% | 3.69% | 2.24× |

**86.6%–98.5% of `D` rows survive into the next edition.** In Form Fields they
are *less* likely to disappear than an average row. H-delete is refuted.
(For comparison, `C` rows in Ratebook Tables disappear at 2.51× base — a higher
lift than `D` achieves anywhere.)

**H-added — "an `A` row is new this edition":** lift 0.29×–1.12×; `A` rows are
new only 1.0%–5.7% of the time, at or below the base rate for new rows in four
of five categories. Refuted.

**H-changed — "a `C` row's content changed this edition":** lift 0.36×–3.12×,
inconsistent in direction — `C` rows in Ratebook Columns change at 7.39% against
a 20.48% base (0.36×). Refuted.

### 2.3 The decisive test: Status barely moves

If Status were a per-edition change flag, it would move as a row ages. For rows
carried between consecutive editions:

| Category | carried | Status unchanged |
|---|---|---|
| Form Fields | 26,268 | 26,151 (**99.555%**) |
| Form Pages | 21,902 | 21,873 (**99.868%**) |
| Form Related Fields | 2,706 | 2,706 (**100.000%**) |
| Ratebook Columns | 13,419 | 13,359 (**99.553%**) |

Status is a **static attribute of the row**, not a per-edition annotation. And
the few transitions that do occur are almost perfectly one-way into `D`:
`A→D` 149, `C→D` 54, against `C→A` 2 and `D→C` 1 across the entire corpus.
**`D` is an absorbing state that does not remove the row.**

### 2.4 What Status does co-vary with (`out/status_semantics.txt`)

| Test | A | C | D |
|---|---|---|---|
| Form Pages: TableName is in Ratebook Tables (rateable) | **100.0%** | 45.2% | **99.9%** |
| Form Pages: TableName has a rule (`DataDefGroup`) | 99.8% | **20.4%** | 64.0% |
| Ratebook Tables: TableName has a rule | 100.0% | **48.9%** | n/a |
| Form Pages: TableName present in the XSD data model | 100.0% | 100.0% | 100.0% |
| AttachmentType = Conditional | 48.2% | 4.1% | 6.3% |
| AttachmentType = Optional | 32.7% | 37.4% | **71.4%** |
| AttachmentType = Mandatory | 0.4% | 0.2% | **0.0%** |

`C`, not `D`, is the least-implemented state — only 20.4% of `C` form pages have
a rule behind them, against 64.0% of `D` and 99.8% of `A`. `D` rows are 99.9%
rateable. Whatever `D` marks, it is not "removed".

Three further hypotheses tested and rejected:

- **Tombstone accumulation.** If `D` were a growing pile, its share would rise
  monotonically along each jurisdiction's series. Across 515 pairs the `D` share
  **rose 38, fell 56, stayed flat 421**. NY sits at 65–70% for ten straight
  editions; CA swings 41% → 31% → 8% → 44%; AL sits at 0% for most editions.
- **Superseded form editions.** ISO form numbers embed an edition
  (`CG 22 67 10 93` = Oct 1993). Only **157** package×form-families carry more
  than one edition at all, and within those `D` is **more** common on the newest
  (33%) than the older (15%). Rejected.
- **Absent from the data model.** 100% of `D` rows' TableNames are present as a
  complexType in the package's own or inherited XSD. Rejected.

### 2.5 Does Status track the DOC exception register? (`17_status_vs_doc.py`)

The one remaining lead: `C` might be the row-level counterpart of the DOC
workbook's "Refer to Company" / "Not Supported" sheets. Joining the two within
each package on the ISO form family (first six characters of the normalised form
number; 18,665 of 26,336 form pages have a parseable number, 434 packages have an
exception register):

| Group | n | A | C | D |
|---|---|---|---|---|
| form family cited in **Refer to Company** | 4,136 | 75.2% | **23.9%** | **0.8%** |
| not cited | 14,529 | 56.1% | 11.2% | 32.7% |
| cited in **Not Supported** | 7 | 57.1% | 42.9% | 0.0% |
| cited in **Special Consideration** | 23 | 100.0% | 0.0% | 0.0% |

Lift for "Refer to Company": **A = 1.34×, C = 2.14×, D = 0.03×**.

`C` is roughly **twice** as common among forms the package declines to rate
automatically — a real signal, but weak: 75.2% of cited forms are still `A`, so
`C` is not *the* marker for "refer to company". The far stronger effect is on
`D`, which is **~40× depleted** among flagged forms. That further undermines any
reading of `D` as "withdrawn" or "unsupported". "Not Supported" matches only 7
form numbers — too few for any inference.

**Verdict on this lead: informative, not decisive.** It rules more out than it
rules in.

### 2.6 Verdict, and the quantified ambiguity

**Established:** Status is static per row; largely (but not wholly) a property of
the artefact rather than the jurisdiction — `Form Pages` row keys carry more than
one Status across packages in **15.6%** of cases, `Ratebook Columns` in **42.2%**,
`Form Fields` in **5.8%**; `D` is a terminal state; `D` does not imply removal,
non-rateability or absence from the model.

**Not established:** what the three letters abbreviate. No definition exists
anywhere in the corpus — searched all 2,865 `*.Metadata.xml` for a Status
definition and found only unrelated field names ("Status For Designated
Operations"). No DOC sheet is named for it.

**Exposure — what an interpretation would affect:**

| Category | rows with Status = D |
|---|---|
| Form Pages | 6,168 of 26,336 (**23.4%**) |
| Form Fields | 2,809 of 30,449 (**9.2%**) |
| Ratebook Columns | 6,169 of 15,525 (**39.7%**) |

**Operational conclusion, which is safe even though the semantics are not:**
any consumer that reads `D` as "delete" and drops those rows would discard up
to 39.7% of a file's content, 99.9% of which is rateable and 64% of which is
rule-backed. That is the wrong default. The safe default is to retain all rows
and carry Status as an attribute.

**What would settle it:** an ISO/Verisk data dictionary for the ERC form CSVs;
or a package pair where a `D` row is followed by the artefact's removal *and* the
removal of its rule and ratebook entry (searched all 515 pairs; the pattern does
not occur at a rate above base).

---

## 3. Integrity anomalies (`out/integrity.txt`)

### 3.1 Five duplicate package directories — proven identical

Full recursive tree hashes (sha256 over sorted relative path + size + content of
every file):

| Package id | Locations | Tree hash | Files | Bytes |
|---|---|---|---|---|
| `GL_AL_20260701_V01` | `AL/…V01`, `AL/…V01_MachineReadableContent` | `2eb78569e6f435584c7004cc` | 85 | 606,689 |
| `GL_CA_20241101_V01` | `CA/…V01`, `CA/…V01_MachineReadableContent` | `542791dea1471b6d669a8704` | 192 | 943,077 |
| `GL_LA_20260701_V02` | `LA/…V02`, `LA/…V02_MachineReadableContent` | `a02b880b73eee819e42a2003` | 173 | 2,167,297 |
| `GL_MI_20260501_V01` | `MI/…V01`, `MI/…V01_MachineReadableContent` | `9efedf92c9fd4dad0b2c1aa5` | 115 | 916,964 |
| `GL_OH_20260601_V02` | `OH/…V02`, `OH/…V02_MachineReadableContent` | `80e3701bb17756398fd2f0d4` | 147 | 1,626,791 |

**What breaks if a consumer walks the tree naively:** every one of these
packages is counted, parsed and loaded twice. Aggregate statistics over the
corpus are inflated; a "latest edition per jurisdiction" query returns a tie it
cannot break; row counts double.

**Recommendation (for the user to action, not applied):** deduplicate by the
package identity parsed from the XSD `targetNamespace`, not by path. Keep both
directories on disk; make the *reader* idempotent. If the user does want to prune,
the `_MachineReadableContent`-suffixed copy is the majority convention (554 of 573
directories) and the bare-named copy is the outlier.

### 3.2 Two misfiled packages — three independent witnesses each

| | Case 1 | Case 2 |
|---|---|---|
| Directory | `GA/` | `RI/` |
| Package name | `GL_DE 20260101 V01_MachineReadableContent` | `GL_PR 20270401 V02_MachineReadableContent` |
| XSD `targetNamespace` | `…/erc/GL_DE_20260101_V01/MasterGLDE` | `…/erc/GL_PR_20270401_V02/MasterGLPR` |
| XSD filename | `MasterGLDE.DataDef.xsd` | `MasterGLPR.DataDef.xsd` |
| `StateCode` in its own rate tables | `DE` × 4,744 (only value) | `PR` × 2,280 (only value) |

In both cases **three independent in-package witnesses agree**, and only the
directory disagrees. The `.zip` for each also sits in the wrong directory, so the
misfiling originated upstream of extraction.

Case 1 is harmless in content terms — `DE/GL_DE 20260101 V01_MachineReadableContent`
holds a byte-identical copy (tree hash `7ce3f44e3c6cdba03265d244`), so the DE
series is complete either way. It only inflates GA's apparent package count.

### 3.3 PR's newest edition exists only under `RI/` — confirmed

Exhaustive enumeration of every PR package anywhere in the corpus:

```
20211101 V01   PR/GL_PR 20211101 V01_MachineReadableContent
20220801 V01   PR/GL_PR 20220801 V01_MachineReadableContent
20230401 V02   PR/GL_PR 20230401 V02_MachineReadableContent
20240301 V01   PR/GL_PR 20240301 V01_MachineReadableContent
20250901 V01   PR/GL_PR 20250901 V01_MachineReadableContent
20260101 V01   PR/GL_PR 20260101 V01
20261101 V01   PR/GL_PR 20261101 V01_MachineReadableContent
20270401 V02   RI/GL_PR 20270401 V02_MachineReadableContent   <-- only copy
```

`PR/` contains editions 20211101 … 20261101 and **no 20270401**. Unlike the DE
case there is **no duplicate**: this is the single copy of PR's newest edition.

**What breaks:** a consumer that resolves jurisdiction from the directory gets
Puerto Rico as of 2026-11-01 and silently misses the 2027-04-01 V02 edition —
and simultaneously attributes a PR package to Rhode Island, so RI gains a
spurious extra edition whose `StateCode` values are all `PR`. This is the one
anomaly in the corpus that causes **silent wrong answers** rather than merely
inflated counts.

**Recommendation:** never key jurisdiction off the directory. Parse the XSD
`targetNamespace` (100% coverage — §4). If the user prefers a filesystem fix,
the correct home is `PR/`, but that is the user's decision; the read-side fix is
sufficient and does not touch the source tree.

### 3.4 The STC date disagreement — a single instance

```
GL_CO_20270401_V03   file STC_GL000197200.json
  directory edition      20270401
  STC EffectiveDateTime  2027-04-10T00:00:00
  ProductName            "General Liability CO"
```

One file of the 514 carrying a date. `04` `01` vs `04` `10` is consistent with a
digit transposition in the sample transaction. The STC files are **sample
transactions, not authority** — they are inputs for testing, and their date is a
policy effective date, not a package edition. Three further STC files carry no
`SchemeKeys` at all (`STC_GL000169458.json`, `1. Input.json`, `1. Output.json`).

**What breaks:** nothing, unless a consumer dates packages from STC. It should
not — §4 shows the XSD namespace is the authoritative channel.
**Recommendation:** treat STC as test fixtures; do not use for identity.

### 3.5 The 61 packages with no `STC/` — explained, not an anomaly

Missing-STC rate by edition year:

| Year | missing / total | rate |
|---|---|---|
| 2020 | 2 / 2 | **100.0%** |
| 2021 | 48 / 52 | **92.3%** |
| 2022 | 1 / 25 | 4.0% |
| 2023 | 5 / 162 | 3.1% |
| 2024 | 1 / 86 | 1.2% |
| 2025 | 0 / 63 | 0.0% |
| 2026 | 2 / 117 | 1.7% |
| 2027 | 2 / 66 | 3.0% |

**`STC/` was introduced with the 2022 editions.** 50 of the 61 are 2020–2021
packages. Of the remainder, **all 10 countrywide packages** lack STC in every
year — consistent with §1.4: a countrywide package is not independently
rateable, so there is no transaction to sample. That leaves ~11 genuinely
sporadic omissions across 2022–2027.

**What breaks:** nothing structural. Any consumer requiring an STC fixture per
package will fail on 61 packages.
**Recommendation:** treat `STC/` as optional. Do not use STC presence as a
validity signal.

### 3.6 The 83 future-dated packages — intended, not corrupt

83 of 573 carry an edition date after 2026-08-10, concentrated on **20270401
(61 packages)** and spread over 46 jurisdictions; only CA, FL, GA, MA, NY and WA
have none. **131 of the 766 circulars** carry an effective date in 2026 or later.

Internal consistency check: for all 566 packages that cite a circular, the
**latest cited circular effective date is ≤ the package's own edition date in
566 of 566 (100.0%)**. Not one package cites a circular that takes effect after
the package does. The future-dated packages are future-*effective* filings, and
the corpus is coherent about them.

**What breaks:** a consumer that selects "the current edition" by taking the
maximum edition date per jurisdiction will select a filing that is not yet in
force. Selection must be *as-of a date*, not *latest*.
**Recommendation:** treat edition date as an effective-from date and always
resolve as-of a rating date.

---

## 4. Can a package be identified from its own contents?

**Answer: yes — completely, for 100% of packages, from file content alone. This
overturns the conclusion in `01-CORPUS-AND-SCHEMA.md` that identity "lives only
in the directory name".** Confidence: very high.

The earlier finding was that `Metadata/` carries no date or version. That remains
true. But `Metadata/` is not the only content channel, and the XSD is decisive.

`16_self_dating.py` ran over the **567 distinct packages** using the directory
name **only as the answer key, never as an input**:

| Channel | Kind | Yields | Coverage | Accuracy |
|---|---|---|---|---|
| **C1 XSD `targetNamespace`** | **file content** | **jurisdiction + edition + version** | **567/567 (100%)** | **100%** |
| C2 XSD filename `MasterGL<XX>` | filename | jurisdiction | 567/567 (100%) | 100% |
| C3 DOC filename `DOC-GL-XX-MMDDYYYY-Vnn` | filename | jurisdiction + edition + version | 567/567 (100%) | 100% |
| C4 STC `SchemeKeys` | file content | jurisdiction | 505/567 (89.1%) | 100% |
| C4 STC `SchemeKeys` | file content | edition | 505/567 (89.1%) | 99.8% (1 miss, §3.4) |
| C5 `StateCode` column of own rate tables | file content | jurisdiction | 567/567 (100%) | 100% |
| C6 `GL<XX>.Metadata.xml` filename | filename | jurisdiction | 567/567 (100%) | 100% |
| C7 latest cited circular date | file content | lower bound on edition | 566/567 (99.8%) | see below |

**The XSD `targetNamespace` alone yields the complete (jurisdiction, edition,
version) triple for 567/567 packages and matches the directory name exactly in
567/567.** This is pure file content — no filename, no path.

Corroboration: where both C1 and C3 are available (all 567), they **disagree in
0 cases**. Six channels, five of them 100% accurate, and the one that isn't
(C4, 99.8%) is a test fixture rather than an identity assertion.

**Ordering** requires (edition, version), because **45 (jurisdiction, edition)
pairs carry more than one version, covering 102 packages** — for these the
version token is required to break the tie. Only C1 and C3 emit a version; C4,
C5, C6 and C7 do not. So content-only ordering rests entirely on the XSD
namespace, which supplies it at 100%.

**C7 as an independent semantic anchor.** The latest circular effective date
cited by a package is ≤ its own edition date in **566 of 566 (100%)** — a
reconciliation that holds without exception. It is a valid lower bound but a weak
estimator on its own: the edition date **equals** the latest cited circular in
**228 of 566 (40.3%)** of packages, with a median gap of **126 days** (p25 = 0,
p75 = 188, max = 519). One package, `GL_AL_20231201_V02`, cites no circular at all.

**Verdict: the corpus is fully self-describing.** Identity, edition, version and
ordering are all reconstructible from file content with 100% coverage, and the
filesystem layout is redundant — which is precisely why the two misfiled packages
in §3.2–3.3 are recoverable rather than fatal.

---

## 5. What surprised me

1. **A "drop" never loses anything.** 600 of 600 dropped state tables were still
   present in the countrywide parent, and *already* present before the drop. I
   expected retirements; I found override withdrawals. This makes the state
   layer look like a patch set that shrinks as countrywide absorbs variation.
2. **Only 36 of 21,694 state/countrywide table overlaps (0.17%) are
   byte-identical.** I expected substantial redundant copying. There is almost
   none — when a state ships a table its parent also has, it means it.
3. **Status is static.** I had framed the open question as "if `D` means Delete,
   23% of rows are tombstones". The data says `D` rows are 99.9% rateable and
   survive editions at 86.6–98.5%, and 99.6–100% of rows never change Status at
   all. The risk I flagged in report 1 was real but pointed the wrong way: the
   danger is not that `D` rows are tombstones, it is that someone will *treat*
   them as tombstones.
4. **`C` is the neglected state, not `D`.** Only 20.4% of `C` form pages have a
   rule behind them, against 64% of `D` and 99.8% of `A`. Whatever the letters
   mean, `C` marks the least-implemented content.
5. **I was wrong in report 1** to say identity lives only in the directory name.
   The XSD `targetNamespace` carries the full triple at 100% coverage, and five
   more channels corroborate. I had over-generalised from `Metadata/` being
   silent to the whole package being silent.
6. **The missing-`STC` "anomaly" is a release-date artefact** — 92.3% of 2021
   packages lack it, ~2% of later ones do. It dissolves once you cross-tabulate
   by year, which is a reminder that an anomaly list is only as good as the
   covariate you test it against.
7. **Not one package cites a circular effective after its own edition date**
   (566/566). For a corpus assembled over six years across 52 jurisdictions,
   that is a remarkably clean invariant.
8. **NY carries 65–70% Status=`D`** on Form Pages for ten consecutive editions,
   while AL carries 0% for most of its nineteen. Whatever Status encodes, it is
   applied with wildly different intensity by jurisdiction — which is itself
   evidence against a mechanical change-flag.

---

## 6. What remains unresolved

1. **The meaning of A / C / D.** Falsified: change-flag, delete-marker,
   supersession, tombstone accumulation, model-absence. Established: static,
   terminal-at-`D`, uncorrelated with removal. *Needs:* an ISO/Verisk data
   dictionary. Nothing in the corpus defines it.
2. **Whether `C` marks "not supported".** Tested in §2.5 by joining the DOC
   exception register to Form Pages on the form family. `C` is 2.14x enriched
   among "Refer to Company" forms — a real but weak signal, since 75.2% of those
   forms are still `A`. The join rules `D` out (0.03x) more convincingly than it
   rules `C` in. *Needs:* the "Not Supported" sheet cites only 7 matchable form
   numbers, so the decisive comparison is not available from this corpus.
3. **Row-level delta risk.** Carry-over was measured at artefact identity, not by
   diffing individual table rows across editions. The evidence against partial
   row sets is strong but indirect (§1.5).
4. **`ErcCore`** — still absent, still imported by all ten countrywide schemas.
   Unchanged from report 1.
5. **Why 45 (jurisdiction, edition) pairs carry multiple versions.** V01→V04
   within a single effective date is common enough to matter for "which edition
   applies", and the corpus does not say what distinguishes them or which
   supersedes.
6. **Whether a state package may legally be paired with a countrywide edition
   other than the one its XSD imports.** The import is 100% consistent, but
   consistency is not permission.

## 7. What I did not examine

- The row-level content of individual table CSVs across editions (only
  order-insensitive set hashes and row counts).
- `Base RaaS Overrides` sheet contents (still uninspected, as in report 1).
- The 2 STC files with a `header`/`body` envelope and the single `1. Output.json`,
  beyond confirming their shape.
- Any excluded path.
