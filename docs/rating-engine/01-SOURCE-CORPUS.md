# 01 — Source Corpus, Extraction Method & Provenance

Everything in this specification derives from **two** folders. This document establishes
exactly what they contain, how they were read, and where they are defective — so that any
claim downstream can be re-verified.

| Corpus | Folder | Files | Supplies |
|---|---|---|---|
| **Rules** | `Commercial Line Manuals\GL\Rules\` | 503 | The algorithm, the classification structure, the state-variation surface, the ILF tables, **and the Territory Definitions** (`CG-T` pages) |
| **Loss Costs** | `Commercial Line Manuals\GL\LossCosts\` | 472 | The operands — published loss costs and ELPs |

§1.1–1.5 cover the Rules corpus. **§1.6 covers the Loss Costs corpus**; its structure,
vocabulary and rating semantics are specified in
[`13-LOSS-COSTS-AND-ELP.md`](13-LOSS-COSTS-AND-ELP.md) and inventoried per jurisdiction in
[`A4-LOSS-COST-INVENTORY.md`](A4-LOSS-COST-INVENTORY.md).

---

## 1.1 Corpus location and shape

```
C:\Projects\Recursive_Harness_2.0\Commercial Line Manuals\GL\Rules\
    503 files, ~1.5 GB
    Naming: GL-<JURIS>-<YYYY>-RU-<NNN>-C.pdf
    e.g.   GL-AK-2025-RU-001-C.pdf
           GL-MU-2027-RU-001-C.pdf   (MU = MULTISTATE / countrywide)
```

Every file's cover page reads:

> `COMMERCIAL LINES MANUAL` / `DIVISION SIX — GENERAL LIABILITY — <JURISDICTION> RULES`
> `NOTICE GL-<ST>-<YYYY>-RU-<NNN>`

followed by `REFERENCE INFORMATION (FOR COMPANY USE ONLY)` carrying **Circular Reference(s)**
and **Filing Reference(s)** — the two identifiers that tie a notice back to an ERC edition
(already mapped in `GL_ERC_to_Manual.xlsx`).

### Distribution by year

| Year | Notices |
|---|---|
| 2021 | 33 |
| 2022 | 103 |
| 2023 | 168 |
| 2024 | 39 |
| 2025 | 56 |
| 2026 | 63 |
| 2027 | 41 |

### Jurisdictions

51 jurisdictions are present: all 50 states **except Hawaii**, plus **DC** and **PR**.
Notice counts range from 5 (CA) to 18 (IL). Hawaii's absence is a **corpus fact**, not a
statement about ISO filings — see `09-GAPS-AND-OPEN-QUESTIONS.md` §9.1.

### The countrywide layer

Only **5** files carry the `MU` (multistate) code, and they are an order of magnitude larger
than state notices (15–30 MB vs ~2 MB):

| File | Size | Role |
|---|---|---|
| `GL-MU-2022-RU-001-C.pdf` | 15.7 MB | CW base, prior numbering |
| `GL-MU-2023-RU-001-C.pdf` | 15.7 MB | CW base, prior numbering |
| `GL-MU-2023-RU-002-C.pdf` | 16.3 MB | CW base, prior numbering |
| `GL-MU-2027-RU-001-C.pdf` | 30.1 MB | **CW base, "1st Edition 4-27", filing GL-2024-RRU24** |

`GL-MU-2027-RU-001-C.pdf` is the authoritative current countrywide rulebook and the source
for §2 of this spec. Its stated change is narrow (*"The General Liability Multistate
Classification Table is updated to reflect Payroll as the Premium Base for 98312 Painting…"*),
but the document itself is a **full reissue** carrying a renumbered rule set.

---

## 1.2 Extraction method

Two passes, because the corpus is not uniformly well-formed.

**Pass 1 — `pdftotext -layout`.** Preserves visual geometry. Used for reading **tables**
(increased-limits matrices, ILTA class-code grids), where column position carries meaning.
Succeeded on 400/503.

**Pass 2 — `pdftotext` (raw reading order), with `pypdf` fallback.** Emits one logical line
per heading and collapses the two-column page layout into document order. Used for **rule
parsing**, because the exception pages are set in two columns and `-layout` interleaves
left-column and right-column rules on the same physical line, which corrupts any
`^RULE n.` anchor. Succeeded on 502/503.

> **Why this matters for the build:** the same distinction applies to the production
> ingestion pipeline. Rule text must be parsed in reading order; rate/factor tables must be
> parsed with geometry. A single extraction mode will not serve both. See `08-INGESTION-SPEC.md`.

### Extraction defects encountered

| Defect | Count | Handling |
|---|---|---|
| Damaged xref table (`Couldn't read xref table`) | 103 | Recovered in full via `pypdf` |
| Truncated file, unrecoverable | 1 | `GL-MO-2027-RU-003-C.pdf` — excluded |
| Duplicate downloads | 3 | `GL-DE-2022-RU-001-C (1)`, `GL-MU-2023-RU-002-C (1)`, `GL-IA-2023-RU-002-C (2)` — excluded from parsing |

Net parsed corpus: **502 of 503**, **490** after excluding duplicate filenames.

---

## 1.3 Notices are full reissues, not patches

This was tested rather than assumed. For Illinois, all 17 notices from 2021→2027 were parsed
for their distinct rule set:

| Notice | Chars | Distinct rules present |
|---|---|---|
| `GL-IL-2021-RU-003-C` | 90,507 | 18 |
| `GL-IL-2023-RU-001-C` | 92,210 | 18 |
| `GL-IL-2026-RU-001-C` | 102,703 | 19 |
| `GL-IL-2027-RU-004-C` | 100,065 | 19 |

Every notice carries the **same complete rule set** (13, 22, 24, 36, 42, 44–49, 53, 56, A1…),
not a delta. **Therefore: the latest notice per jurisdiction is a complete statement of that
jurisdiction's current exception pages.** This is what makes a single-notice state overlay a
valid unit of storage (see `06-DATA-SCHEMA.md`).

It also means historical rating is tractable: to rate as of an arbitrary date you select the
notice in force at that date, not a chain of accumulated patches.

---

## 1.4 Provenance model

Every extracted fact carries, and must continue to carry, four provenance fields:

| Field | Example | Purpose |
|---|---|---|
| `source_pdf` | `GL-TX-2025-RU-001-C.pdf` | The document |
| `notice_id` | `GL-TX-2025-RU-001` | The notice as printed on the cover |
| `page_marker` | `CG-E-2`, `CG-CT-1` | The manual page, from the page footer |
| `edition_marker` | `16th Edition 4-23` | The edition stamp in the footer |

Cover-page **Circular Reference(s)** and **Filing Reference(s)** are additionally captured to
join to the ERC hierarchy already built in `GL_ERC_Edition_Hierarchy.xlsx`.

> **Dating caveat carried forward from the ERC workbook:** page-footer edition markers record
> *when a page was last changed*, not the notice's effective date, and were explicitly rejected
> as a dating basis during the ERC mapping. Effective dates must come from the ERC circular
> metadata, not from the PDF footer. This constraint is inherited by this spec.

---

## 1.5 Scope limit on every "no deviation" claim

The deviation matrix in `04-STATE-DEVIATIONS.md` is computed from the **latest notice per
jurisdiction**. A statement that "Rule 25 has no state exception" is therefore precisely:

> *No jurisdiction's current (latest-in-corpus) exception pages contain an exception to Rule 25.*

It is **not** a claim about every historical edition. For historical rating, the same parse
must be re-run per effective date across all 490 notices. The pipeline supports this — the
per-notice deviation records already exist for all 490 files — but the summary tables in this
document set are current-state only, and are labelled as such.

---

## 1.6 The Loss Costs corpus

```
C:\Projects\Recursive_Harness_2.0\Commercial Line Manuals\GL\LossCosts\
    472 files
    Naming: GL-<ST>-<YYYY>-LC-<NNN>-C.pdf     e.g. GL-AK-2023-LC-001-C.pdf
```

Same cover-page grammar as the Rules notices — `NOTICE GL-<ST>-<YYYY>-LC-<NNN>` followed by
`REFERENCE INFORMATION (FOR COMPANY USE ONLY)` with dated **Circular Reference(s)** and
**Filing Reference(s)** — which is what allows the same ERC join
(`GL_LossCost_to_ERC.xlsx`: 415 of 472 matched on a cited identifier).

| | Rules | Loss Costs |
|---|---|---|
| Files | 503 | 472 |
| Extracted | 502 | **471** (`GL-MI-2027-LC-003-C.pdf` truncated) |
| Jurisdictions | 51 (no HI) | **51 (no HI)** — identical set |
| Countrywide (`MU`) notices | 5 | **0** |
| Notices per jurisdiction | 5–17, median 9 | 4–11, median 10 |
| Edition years | 2021–2027 | 2020–2027 |

**There is no countrywide loss cost document.** The rate corpus is 51 independent state
documents with no base layer — the exact inverse of the Rules corpus, where the countrywide
layer holds the algorithm and no numbers.

### 1.6.1 The extraction rule inverts for rate pages

§1.2 establishes `-layout` for tables and reading order for prose. **On the `CG-LC` and
`CG-ELP` grid pages that rule is wrong**, and wrong in the most dangerous way — it produces
plausible output.

| Mode | Result on a loss cost grid |
|---|---|
| `pdftotext -layout` | **Rows interleave.** Class codes drift onto their own lines and values shift up onto the preceding code. Every number is a valid loss cost, attached to the wrong class |
| `pypdf` | Correctly paired rows: `10010 .199 .156 10150 .78 (a) 11204 .49 1.33 13111 2.99 .069` |

Verified on GA, TX and NY (where `pdftotext` succeeds) and on AK and AL (xref-damaged).
Confirmed arithmetically: Indiana's 4 territories × 1,188 classes × 2 columns = 9,504 cells,
and the `pypdf` parse returns exactly 9,504 (5,828 numeric + 1,780 `(a)` + 1,896 `–`). A
misaligned parse does not reconcile.

**83 of 472** loss cost files have damaged xref tables and fail `pdftotext` outright —
including **41 of the 51 current notices**. So for the editions actually in force, `pypdf` is
both the only available path and the correct one.

Cost of the choice: `pypdf` injects spaces inside words (`UNMANNED AIRCRAFT LI MITED
LIABILITY`, `CG -LC -89`). All caption and page-marker matching must be whitespace-normalised.
A literal match initially under-reported the Unmanned Aircraft table as present in 47 of 51
jurisdictions when it is present in all 51.

### 1.6.2 Provenance

The four provenance fields of §1.4 carry over unchanged, with `page_marker` drawn from the
`CG-LC-n` / `CG-ELP-n` / `CG-LCADD-n` families. Two additional keys are mandatory for a rate
fact and have no analogue in the Rules corpus:

| Field | Example | Why |
|---|---|---|
| `territory` | `501`, or `999` for Prod/COps | The grid is keyed on it; a rate without it is ambiguous in 31 jurisdictions |
| `subline_code` | `334`, `336`, `335`, `370` | Prem/Ops and Prod/COps share a row but are different facts |

---
