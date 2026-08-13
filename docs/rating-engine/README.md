# GL Rating Engine — Engineering Specification & Schema Plan

> **Reconciliation note, 2026-08-11.** This document was derived from the filed manual PDFs and **before any subline
> was derived end to end**. The per-subline gates have since superseded or sharpened some claims
> here — see [`../gates/RECONCILIATION.md`](../gates/RECONCILIATION.md) (items R1, R2, R3). The text below is
> left as the record of what this derivation found on its own; that independence is what makes
> agreement between the two derivations evidence.

Build-ready specification for a General Liability rating engine, derived **solely** from the
ISO *Commercial Lines Manual, Division Six — General Liability* notices in this project:

| Corpus | Folder | Files | Jurisdictions | Years |
|---|---|---|---|---|
| **Rules** | `Commercial Line Manuals\GL\Rules\` | 503 | 51 | 2021–2027 |
| **Loss Costs** | `Commercial Line Manuals\GL\LossCosts\` | 472 | 51 | 2020–2027 |

**Status: specification only. Nothing has been built.**

Every structural claim, code, factor and jurisdiction value in these documents is traceable to
a named PDF. Where the corpora do not answer a question, it is recorded as a gap in
`09-GAPS-AND-OPEN-QUESTIONS.md` rather than filled by assumption.

---

## Start here

| Order | Document | Read it for |
|---|---|---|
| 1 | **[00-OVERVIEW.md](00-OVERVIEW.md)** | The strategy and the three findings that drive the whole design |
| 2 | [01-SOURCE-CORPUS.md](01-SOURCE-CORPUS.md) | What the corpus contains, how it was read, where it's defective |
| 3 | [02-CW-BASE-RULEBOOK.md](02-CW-BASE-RULEBOOK.md) | The countrywide base: rule catalog, premium algorithm, edition renumbering |
| 4 | [03-SUBLINE-COVERAGE-PLAN.md](03-SUBLINE-COVERAGE-PLAN.md) | Rating plan for every subline and coverage |
| 5 | **[04-STATE-DEVIATIONS.md](04-STATE-DEVIATIONS.md)** | The full deviation mapping — matrix, frequency, A-rules |
| 6 | **[05-LOOKUP-TABLES.md](05-LOOKUP-TABLES.md)** | Every lookup, with per-jurisdiction values |
| 7 | **[06-DATA-SCHEMA.md](06-DATA-SCHEMA.md)** | Proposed schema — relational DDL + JSON contracts |
| 8 | [07-ENGINE-ARCHITECTURE.md](07-ENGINE-ARCHITECTURE.md) | Calculation pipeline, resolver, versioning |
| 9 | [08-INGESTION-SPEC.md](08-INGESTION-SPEC.md) | PDF → structured data pipeline |
| 10 | [09-GAPS-AND-OPEN-QUESTIONS.md](09-GAPS-AND-OPEN-QUESTIONS.md) | What the corpus cannot answer |
| 11 | [10-BUILD-BACKLOG.md](10-BUILD-BACKLOG.md) | Phased delivery plan (~16–21 weeks) |
| 12 | **[11-RATING-ARCHITECTURE.md](11-RATING-ARCHITECTURE.md)** | **Full calculation architecture** — ordered algorithms, exceptions and endorsement treatment for every subline, coverage and sub-coverage |
| 13 | **[12-VERSIONING-AND-EDITIONS.md](12-VERSIONING-AND-EDITIONS.md)** | **The versioned instance** — CW base over time, edition migration, bitemporal resolution |
| 14 | **[13-LOSS-COSTS-AND-ELP.md](13-LOSS-COSTS-AND-ELP.md)** | **The rate layer** — published loss costs, the ELP Supplement, rate resolution, the 15/36 vintage split |

**Appendices:** [A1-STATE-PROFILES.md](A1-STATE-PROFILES.md) ·
[A2-CW-RULE-CATALOG.md](A2-CW-RULE-CATALOG.md) ·
[A3-ENDORSEMENT-CATALOG.md](A3-ENDORSEMENT-CATALOG.md) ·
[A4-LOSS-COST-INVENTORY.md](A4-LOSS-COST-INVENTORY.md)

**Plain-English overview:** [`../BUILD-PLAN-PLAIN-ENGLISH.md`](../BUILD-PLAN-PLAIN-ENGLISH.md)
— how these findings become a build, written for a non-technical reader. Scoped to the PDF
manuals only, with expectations on how an ERC-based build would differ.

**Visualization:** [`index.html`](index.html) — self-contained interactive view of the
deviation surface (open in a browser). **Data:** [`dataset.json`](dataset.json) —
machine-readable form of every table in these documents.

---

## The four findings that shape the design

**1. The manual is a two-layer overlay, and the countrywide layer cannot rate alone.**
CW Rule 56.B states verbatim: *"The increased limits tables are displayed in the state
exceptions."* There is no countrywide ILF table. Every increased-limits factor in the program
is a state lookup.

**2. Printed rule numbers are not identifiers.** The CW 2027 edition renumbers 21 of ~50
rules — Premium Determination moves from Rule 35 to Rule 21; Rule 22 changes meaning entirely
from *Description Of CGL Coverage* to *Mandatory Endorsements*. A state overlay authored
against the old numbering, resolved against the new, silently applies the wrong exception.
This is the project's highest-severity correctness risk.

**3. Deviation concentrates in coverage and limits, not in classification.** Rules 24, 45 and
56 are deviated by **all 51** jurisdictions. Meanwhile the entire classification apparatus
(Rules 25, 26, 27, 29, 31, 32) carries **no** state exception in any current notice — it can be
hard-bound to the countrywide base.

**4. The rate layer is a third version stream, and it is mid-migration right now.** Loss costs
arrive as 471 state-only notices with **no countrywide counterpart**, moving on their own
cadence. As of this corpus, **15** jurisdictions are on the pre-2027 rate basis and **36** have
moved to the 2027 basis — which retires 229 class codes, introduces 204, and **withdraws the
Owners & Contractors Protective loss cost table**. Three independent tests select the same
15/36 split, so this is one filing rolling out state by state. Any engine keying rates on a
single national class list is wrong today.

---

## Headline numbers

| Metric | Value |
|---|---|
| Rules notices in corpus | 503 (502 extracted; 1 truncated) |
| Jurisdictions | 51 — 50 states less Hawaii, plus DC and PR |
| Countrywide (multistate) notices | 5 files → **4 distinct editions** (`GL-MU-2023-RU-002-C` is a duplicate download) |
| CW rules with ≥1 state exception | 33 |
| CW rules with no state exception | 13 |
| CW rules renumbered in the 2027 edition | 21 |
| Sublines | 8 |
| Deviations per jurisdiction | 4 (min) – 26 (max) |
| Payroll-limitation structural shapes | 3 |
| Liquor grades in force | 0–8 across 51 jurisdictions |
| Distinct endorsement forms in the CW manual | 328 |
| (coverage part, form) placements | 447 |
| Forms added / dropped between CW 2022 and CW 2027 | 40 added · 21 dropped |
| Countrywide editions in corpus | 4 (MU 2022-001, 2023-001, 2023-002, 2027-001) |
| Algorithm archetypes covering all 17 coverages | 5 |
| **Loss cost notices in corpus** | **472** (471 extracted; 1 truncated) |
| **Countrywide loss cost notices** | **0** — the rate layer is purely state-level |
| **Loss cost grid cells, current notices** | ~429,700 (64.3% numeric · 18.6% not offered · 17.1% refer) |
| **ELP classes per jurisdiction** | 404 in 49 of 51 |
| **Premises/Operations territories** | 1 – 20; 20 jurisdictions have exactly 1 |
| **Jurisdictions actually territory-rated** | **31** (the Rules A-rule implies only 27) |
| **Territory resolution schemes** | 3 — ZIP table (27) · county/city (4) · entire state (20) |
| **ZIP → territory rows, current notices** | **23,719** (plus 432 county/city rows) |
| **Cross-corpus territory agreement** | **51 / 51 exact**, zero mismatches |
| **Rate-basis vintage split** | **15 pre-2027 / 36 on the 2027 basis** |

---

## Critical scope boundary

The Rules corpus gives the complete rating *algorithm*, the complete *state-variation
surface*, **and the Territory Definitions**. The Loss Costs corpus gives the **operands** —
published ISO loss costs and the ELP Supplement — for all 51 jurisdictions.

**Still absent from both:**

| Missing | Blocks |
|---|---|
| **Terrorism Supplement** (Rule 55 + 48 A-rules) | Terrorism premium entirely |
| **Company loss cost multiplier** | Carrier input by design — every stored value is a pre-LCM ISO loss cost |
| **CGLES / Composite / Size-Of-Risk plans** | Rating-plan modification factors |
| **Workers Compensation loss costs** | OCP class `15191` only |

The **Territory Definitions** are also in the Rules corpus, on the Territory Pages (`CG-T-n`)
of every notice — 27 jurisdictions with full ZIP→territory tables (23,719 rows), 4 with
county/city definitions, 20 statewide.

The engine is therefore **priceable for Premises/Operations and Products/Completed Operations
in all 51 jurisdictions**, with no external dependency but the carrier's own loss cost
multiplier. See `09-GAPS-AND-OPEN-QUESTIONS.md` §9.1 and `13-LOSS-COSTS-AND-ELP.md` §13.11.

---

## Method note

Text extraction is **three-moded, selected by page family** — the right tool differs not just
between the two corpora but between page families inside one document:

| Page family | Extractor | Why |
|---|---|---|
| Rule bodies, exception pages | `pdftotext` (reading order) | The pages are two-column; layout mode interleaves unrelated rules onto one line and destroys `^RULE n.` anchoring |
| ILF matrices, ILTA grids | `pdftotext -layout` | Column position carries the data |
| **Loss cost & ELP grids (`CG-LC`, `CG-ELP`)** | **`pypdf`** | `-layout` **silently misaligns** these rows — values detach from their class code and reattach to the neighbouring one. Every resulting number is a plausible loss cost |

186 files across the two corpora have damaged xref tables and require `pypdf` regardless —
including **41 of the 51 current loss cost notices**. Two files are unrecoverable
(`GL-MO-2027-RU-003-C.pdf`, `GL-MI-2027-LC-003-C.pdf`).

The `-layout` misalignment is the highest-risk extraction defect in the project because it
fails silently and produces valid-looking output. It is specified, evidenced and guarded by
assertions V17/V18 in `08-INGESTION-SPEC.md` §8.3.1.
