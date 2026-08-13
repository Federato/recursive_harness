# 13 — Loss Costs, ELPs & the Rate Layer

> **Reconciliation note, 2026-08-11.** This document was derived from the filed manual PDFs and **before any subline
> was derived end to end**. The per-subline gates have since superseded or sharpened some claims
> here — see [`../gates/RECONCILIATION.md`](../gates/RECONCILIATION.md) (items R1, R2, R3). The text below is
> left as the record of what this derivation found on its own; that independence is what makes
> agreement between the two derivations evidence.

The Rules corpus gives the algorithm. This document covers the corpus that gives the
**operands** — the ISO advisory prospective loss costs and the Estimated Loss Potentials that
Rule 21 step C, Rule 48.I step 2 and Rule 46.J step 2 consume and that
`09-GAPS-AND-OPEN-QUESTIONS.md` previously recorded as gaps **G1** and **G3**.

> **Source:** `Commercial Line Manuals\GL\LossCosts\` — 472 PDFs, 51 jurisdictions, notice
> years 2020–2027. Every claim below is computed over that folder; the per-jurisdiction
> figures are from the **latest notice per jurisdiction** and are labelled as such.

---

## 13.1 What arrived, and what it changes

| Gap | Was | Now |
|---|---|---|
| **G1** State rates / ISO loss costs | Blocking for pricing | **Closed.** Published loss costs for sublines 334, 336, 335 (OCP/PP) and 370, by class code and territory, for all 51 jurisdictions |
| **G3** Estimated Loss Potentials Supplement | Absent from corpus | **Closed.** The full ELP Supplement (Procedures 1–5, Tables 5.B–5.E) is in every one of the 471 readable notices |
| **G2** Territory Definitions | Blocking for 27 jurisdictions | **Closed — but by the *Rules* corpus, not this one.** The ZIP→territory tables are on the Territory Pages (`CG-T-n`) of the Rules notices; see `05-LOOKUP-TABLES.md` §5.4.1. This corpus contributes the independent confirmation: the territory domains published on the loss cost grids match the `CG-T` pages in **all 51** jurisdictions |
| **G4** Terrorism Supplement | Absent | **Unchanged.** The string `TERRORISM` does not occur anywhere in the corpus |
| **G5** Company LCM | Carrier input by design | **Unchanged.** `LOSS COST MULTIPLIER` does not occur; these are ISO loss costs, pre-LCM, exactly as Rule 23.B describes |

The engine moves from *"testable but not priceable"* to **priceable for the Premises/Operations
and Products/Completed Operations sublines in all 51 jurisdictions** — with no external rate
dependency remaining except the carrier's own loss cost multiplier.

---

## 13.2 Corpus shape

```
C:\Projects\Recursive_Harness_2.0\Commercial Line Manuals\GL\LossCosts\
    472 files
    Naming: GL-<ST>-<YYYY>-LC-<NNN>-C.pdf     e.g. GL-AK-2023-LC-001-C.pdf
```

Cover page is identical in form to the Rules notices —
`COMMERCIAL LINES MANUAL / DIVISION SIX – GENERAL LIABILITY – <JURISDICTION> LOSS COSTS`,
`NOTICE GL-<ST>-<YYYY>-LC-<NNN>`, then `REFERENCE INFORMATION (FOR COMPANY USE ONLY)` carrying
dated **Circular Reference(s)** and **Filing Reference(s)**. That is what makes the ERC join in
`GL_LossCost_to_ERC.xlsx` possible (415 of 472 matched on a cited circular or filing).

| Metric | Value |
|---|---|
| PDFs | 472 |
| Text-extracted | **471** — `GL-MI-2027-LC-003-C.pdf` is truncated (no xref/EOF), unrecoverable |
| Jurisdictions | **51** — 50 states less Hawaii, plus DC and PR (identical to the Rules corpus) |
| Notices per jurisdiction | 4 (CA) – 11 (FL, VT), median **10** |
| Multistate (`MU`) notices | **0** — there is no countrywide loss cost document |

Notices by year:

| 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 | 2027 |
|---|---|---|---|---|---|---|---|
| 54 | 141 | 37 | 57 | 49 | 48 | 27 | 58 |

> **There is no countrywide loss cost layer at all.** Unlike the Rules corpus, which has a CW
> base overlaid by state exceptions, the rate corpus is **51 independent state documents**. This
> is the mirror image of the Rule 56.B finding: the countrywide layer owns the algorithm and
> owns no numbers; the state layer owns every number.

---

## 13.3 Document anatomy — one skeleton, 471 instances

Every readable notice carries the same two page families, in this order:

| Page family | Marker | Count | Contents |
|---|---|---|---|
| **ELP pages** | `CG-ELP-1` … `CG-ELP-9` | 9 (10 in NY) | Estimated Loss Potentials Supplement, Procedures 1–5 |
| **Loss cost pages** | `CG-LC-1` … `CG-LC-<8T+1>` | `8·T + 1` | Published loss costs, `T` = number of Premises/Operations territories |
| **Loss cost addendum** | `CG-LCADD-n` | 0 or 1 | Loss Cost Mapping By Class (§13.6) |

**`CG-LC` page count = 8·T + 1 holds for all 51 jurisdictions.** Eight pages carry the
class-code grid for one territory; the final page carries the flat, all-territories tables.
This is a hard structural invariant and belongs in ingestion validation.

Content presence across the 51 latest notices:

| Section | Present |
|---|---|
| ELP Supplement, Procedures 1–5 (incl. Homogeneity & Reliability Indices) | **51/51** |
| Table 5.B — Premises/Operations and Products/Completed Operations ELPs | **51/51** |
| Table 5.C — OCP & Principals Protective ELPs | **51/51** |
| Table 5.D — Liquor Liability ELPs | **51/51** |
| Table 5.E — Railroad Protective ELPs (banded on trains per day) | **51/51** |
| Loss cost grid — Prem/Ops (334) and Prod/COps (336) | **51/51** |
| Unmanned Aircraft (370) loss costs | **51/51** |
| OCP / Principals Protective (335) **loss costs** | **15/51** — see §13.7 |
| Liquor Liability (332) **loss costs** | **0/51** |
| Railroad Protective (335) **loss costs** | **0/51** |

Two basic-limit bases appear, and only two: **$100,000/$200,000** for sublines 334, 336, 332,
370 and OCP/PP; **$100,000/$300,000** for Railroad Protective. Both occur in all 471 notices.

> **Liquor Liability and Railroad Protective have no published loss cost anywhere in this
> corpus — only ELPs.** Rule 45 specifies a full nine-step algorithm for Liquor
> (`11-RATING-ARCHITECTURE.md` §11.3.3) whose step 2 selects "the basic limits rate", and no
> such rate exists. Liquor rating is therefore ELP-driven or refer-to-company in every
> jurisdiction, not manually rated. This is a rating-mode correction to
> `03-SUBLINE-COVERAGE-PLAN.md` §3.1, not a data gap.

---

## 13.4 The loss cost grid and its cell vocabulary

Each `CG-LC` grid page carries four repeating column groups of
`Class Code | Prem/Ops | Prod/COps`, 40 rows per group — 160 class codes per page, ~1,170 per
territory. Page header states the keys explicitly:

> `$100,000/200,000 BASIC LIMIT OCCURRENCE`
> `Premises/Operations (Prem/Ops) (Subline Code 334) Territory 501`
> `Products/Completed Operations (Prod/COps)(Subline Code 336) Entire State Territory 999`

A cell is one of exactly **three** things. Over all territories of the 51 latest notices —
429,748 cells:

| Cell | Share | Meaning | Engine behaviour |
|---|---|---|---|
| numeric (e.g. `.084`, `12.60`) | **64.3%** | Published ISO loss cost per unit of exposure | `rate = loss_cost × company LCM` (Rule 23.B) |
| `–` (en dash) | **18.6%** | Coverage not offered for this class/subline | **Reject the line.** This is the `(−)` marker Rule 48.F.1 names |
| `(a)` | **17.1%** | Refer to company; an ELP may exist | Look up the ELP; if none, emit a referral |

**This closes open question Q4.** `09-GAPS-AND-OPEN-QUESTIONS.md` asked whether
`has_prodcompops` was derivable without the rate pages, because Rule 48.F.1 keys the exclusion
to *"a (−) on the state loss cost page"*. It is now directly derivable — but note it is
**per jurisdiction**, not countrywide: `has_prodcompops` is a property of
`(class_code, jurisdiction, edition)`, and modelling it as a column on the countrywide
`classification` table (`06-DATA-SCHEMA.md` §6.5) would be wrong.

**Empty is not zero and `(a)` is not zero.** A `(a)` cell that is silently read as `0.00`
produces a free policy; a `–` read as `0.00` produces coverage the manual does not offer.

### The class-code universe

| | Codes |
|---|---|
| Present in all 51 jurisdictions | **947** |
| Present in exactly 15 jurisdictions (pre-2027 vintage only) | 229 |
| Present in exactly 36 jurisdictions (2027 vintage only) | 204 |
| Per-jurisdiction total | 1,163 or 1,188 (NJ 1,187; NY 1,181) |
| Union across all jurisdictions | **1,396** |

The 229/204 split is not state-by-state idiosyncrasy — it is the two-vintage split of §13.7.

---

## 13.5 The ELP Supplement

Procedure 5 supplies an ELP for classes with no manual loss cost. **404 classes** carry an ELP
in 49 of 51 jurisdictions (KS 388, MI 408). Each entry pairs a value with a
**Homogeneity/Reliability index** — `1`–`5` (heterogeneity → homogeneity) over `A`–`E`
(extremely low → high reliability), defined verbatim in Procedures 3 and 4.

Unlike the loss cost grid, an ELP cell is **four**-valued, and the vocabulary differs by side:

| Token | Prem/Ops side | Prod/COps side | Meaning (Procedure 5 legend, verbatim) |
|---|---|---|---|
| `Manual –` | 26.5% | 0.4% | *"a rate or loss cost for this classification is displayed in the state company rates/ISO loss costs"* — go back to the grid |
| `$n.nn` + `H/R` | 15.3% | 21.3% | An ELP is published |
| `RTC` | 9.2% | 12.4% | *"a company must develop its own rates for this classification without an ELP for reference"* |
| `Incl. –` | — | 14.9% | *"Products/Completed Operations is included in the Premises/Operations coverage at no additional premium charge"* |

`Incl.` is a **rating instruction, not a value**: charging a separate Prod/COps premium for
those classes double-counts. It occurs only on the Prod/COps side.

The ELP is *not* a rate. Procedure 1 states it plainly:

> *"An ELP does NOT contain a provision for company expenses or profits."*

and

> *"ELPs were established based on a review of experience mostly from occurrence policies. If
> claims-made is applicable in a jurisdiction, ELPs used in developing premiums for a
> claims-made policy must be adjusted using the claims-made multipliers in Rule 23."*

So an ELP feeds the same pipeline as a loss cost but carries a **mandatory claims-made
adjustment** the loss cost path does not, and still requires the carrier's own loading.

---

## 13.6 Rate resolution — the decision procedure

Step C of Rule 21 is not a table lookup. It is a five-way resolution that the engine must
implement explicitly, in this order:

```
resolve_rate(jurisdiction, class_code, subline, territory, effective_date):

  1. grid := loss_cost_cell(jurisdiction, edition, territory, class_code, subline)

     numeric  → rate := grid × LCM                               [Rule 23.B]      DONE
     '–'      → REJECT: coverage not offered for this class      [Rule 48.F.1]    DONE
     '(a)'    → fall through to 2

  2. elp := elp_cell(jurisdiction, edition, class_code, subline)

     '$n.nn'  → rate := elp × LCM, adjusted for claims-made      [Procedure 1.E]  DONE
     'Incl.'  → premium := 0 for this subline; already in host   [Procedure 5]    DONE
     'Manual' → contradiction with step 1 → VALIDATION FAILURE
     'RTC'    → REFERRAL, no ELP reference available
     absent   → fall through to 3

  3. mapping := loss_cost_mapping(jurisdiction, edition, class_code)   [CG-LCADD]

     'Use n% of premises/operations loss cost of class X'
              → rate := n% × resolve_rate(..., X, PREM_OPS, ...)                  DONE
     'Percentage of otherwise applicable Workers Compensation loss costs: n%'
              → EXTERNAL: requires the WC rate for the same risk

  4. no entry anywhere → REFERRAL
```

Three consequences for the schema and the kernel:

1. **Rate resolution is recursive.** The `CG-LCADD` mapping pages express a new class's loss
   cost as a percentage of *another class's* loss cost (*"Use 116% of premises/operations loss
   cost of class 12373"*). Cycle detection is required; the resolver must not assume the grid
   is a flat lookup.
> **[R2] Superseded 2026-08-11.** The Workers Compensation linkage below is **not an external
> dependency**. ERC carries the 75% as a countrywide cell (`PrincipalsProtvLiabFactor = 0.75`) and
> declares `WorkersCompensationRate` as a **submission input field** that real ISO submissions
> supply. It is a submission requirement, and the 2027 program retires class `15191` outright.
> See [`../gates/GATE-335-OWNERS-CONTRACTORS-PROTECTIVE.md`](../gates/GATE-335-OWNERS-CONTRACTORS-PROTECTIVE.md) §1.

2. **One ELP crosses lines of business.** Table 5.C prices OCP class `15191` as
   *"Percentage of otherwise applicable Workers Compensation loss costs: 75%"* — present in
   **51/51** jurisdictions. A GL engine cannot resolve it from GL data at all; it is a typed
   external dependency, not a referral.
3. **Railroad Protective is doubly derived.** Table 5.E.1 rates class `40014` as *"150% of the
   loss cost for Class Code 16292 Construction Operations – Owner"*, with a further *"charge an
   additional premium of 10%"* extension, and *"for operations other than construction, refer to
   company"*. Class `40013` is instead banded on **number of passenger and freight trains per
   day** at $100,000/$300,000 basic limits — a rating dimension that exists nowhere else in the
   program.

---

## 13.7 The corpus is mid-migration: a clean 15 / 36 split

> **[R1] Superseded 2026-08-11 — the framing, not the measurement.** The three tests below agree
> and the vintage division is real; what is wrong is reading it as a *present* state. These are the
> latest notices per jurisdiction and some are future-dated. Measured as-of a date over ERC
> (`scripts/erc/31_migration_asof.py`): **today 51 jurisdictions are pre-2027 and 0 have migrated;
> on 2027-04-01, 43 migrate at once.** The corpus is not mid-migration — it is entirely pre-migration,
> with a cliff ahead. §13.7's own observation that the withdrawal is *"sharply dated"* is the
> correct reading and was right before the ERC derivation reached it.
> See [`../gates/RECONCILIATION.md`](../gates/RECONCILIATION.md) §1.

The single most consequential finding. The 51 current notices divide into exactly two
vintages, and the division is the same under three independent tests:

| Test | Pre-2027 vintage | 2027 vintage |
|---|---|---|
| Carries the 229 retired class codes | **15** | 0 |
| Carries the 204 new class codes | 0 | **36** |
| Publishes the OCP/PP loss cost table | **15** | 0 |

**Pre-2027 (15):** AK, CA, CT, DC, GA, KS, MA, MI, NC, NJ, NY, RI, TX, VT, WA
**2027 (36):** all others

The three tests select **identical** jurisdiction sets. This is one filing rolling out
state by state, not three unrelated changes.

The withdrawal of the OCP/PP published loss costs is sharply dated:

| Notice year | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 | 2027 |
|---|---|---|---|---|---|---|---|---|
| Notices publishing OCP/PP loss costs | 54/54 | 141/141 | 37/37 | 57/57 | 49/49 | 48/48 | 27/27 | **22/58** |

Every notice through 2026 carries it. The change lands entirely inside the 2027 notices, and
for 30 of the 36 migrated jurisdictions the *immediately preceding* notice still carried it
(e.g. `GL-AL-2027-LC-002` has it, `GL-AL-2027-LC-003` does not).

> **Operational consequence.** An engine that binds the OCP/PP loss cost table at build time
> will silently lose Owners & Contractors Protective rating in 36 jurisdictions as their 2027
> notices take effect, and must fall back to the Table 5.C ELPs. This is exactly the failure
> mode `12-VERSIONING-AND-EDITIONS.md` §12.6 requires the edition-change replay harness to
> catch: the premium does not error, it changes.

**This is the third version stream.** `12-VERSIONING-AND-EDITIONS.md` §12.1 models two
independently versioned streams (countrywide base, state exception overlay). The loss cost
notices are a **third**, moving on its own cadence — 4–11 notices per jurisdiction against
5–17 rules notices — and a rating instance is not resolvable without it.

---

## 13.8 The territory model

Territory applies to **Premises/Operations (334) and Liquor Liability (332)** — the `CG-T-1`
definitions page of the Rules notice names both. On the *rate* pages only the 334 half is
visible, because there are no liquor loss cost pages at all (§13.3). Every grid page states
the key explicitly:

> `Premises/Operations (Prem/Ops) (Subline Code 334) Territory 501`
> `Products/Completed Operations (Prod/COps)(Subline Code 336) Entire State Territory 999`

Products/Completed Operations is written to the reserved statewide territory **999** in all 51
jurisdictions. So the loss cost key is `(class_code, 334, territory)` but
`(class_code, 336, 999)` — a single composite key with a constant would be wrong.

Territory counts (latest notice per jurisdiction):

| Territories | 1 | 2 | 3 | 4 | 5 | 7 | 8 | 9 | 10 | 11 | 15 | 20 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Jurisdictions | **20** | 9 | 7 | 5 | 1 | 1 | 2 | 1 | 1 | 2 | 1 | 1 |

Largest: NY 20, NJ 15, CA 11, PA 11, OH 10, MA 9. Territory numbers run in two disjoint
families — `001`–`024` and `501`–`517` — never mixed within a jurisdiction.

### A correction to `05-LOOKUP-TABLES.md` §5.4

That section reports 27 jurisdictions as territory-rated, on the basis of the *"Rating
Territories For Premises And Operations"* A-rule in the Rules exception pages. Against the
loss cost pages:

- All **27** A-rule jurisdictions are multi-territory. ✔
- **31** jurisdictions are multi-territory. **CA, FL, NY and TX are territory-rated with no
  territory A-rule** — and they are among the most heavily territorialised in the program
  (NY 20, CA 11, TX 8, FL 5).

**The A-rule is not the test for territory rating.** An engine that gates territory lookup on
its presence mis-rates the four largest of them.

The Rules corpus explains *why*, and the explanation is not an oversight. The A-rule is the
**ZIP-based** territory rule, and those four jurisdictions define territory by **county and
city name** instead — an older scheme with no ZIP table to point at
(`05-LOOKUP-TABLES.md` §5.4.1). Three resolution schemes exist: ZIP table (27), county/city
(4), entire state (20).

### Cross-validation against the Territory Pages

The territory codes printed on the Rules notices' `CG-T` pages were compared with the
territories published on the loss cost grids, jurisdiction by jurisdiction:

**51 of 51 match exactly. Zero mismatches** — including NJ 15, NY 20, CA 11, PA 11, OH 10,
MA 9, CT 8, TX 8, IL 7, FL 5.

Two corpora, parsed by different code paths, agreeing exactly on 51 territory domains is the
strongest available evidence that both parses are correct. It is also a reusable ingestion
assertion — see `08-INGESTION-SPEC.md` V22.

---

## 13.9 Extraction: the mode guidance inverts

`08-INGESTION-SPEC.md` §8.3 specifies `pdftotext -layout` for tables and reading-order text for
prose, and treats `pypdf` purely as a damaged-file fallback. **That guidance is correct for the
Rules corpus and wrong for this one.**

| | Rules corpus | Loss cost corpus |
|---|---|---|
| `pdftotext` succeeds | 400/503 layout, 502/503 reading order | 389/472 |
| `pdftotext` fails (`Couldn't read xref table`) | 103 | **83** |
| Right tool for the tables | `-layout` | **`pypdf`** |

On the `CG-LC` and `CG-ELP` grids, `pdftotext -layout` **interleaves and misaligns rows**. The
same page rendered both ways:

```
pdftotext -layout  (Georgia, CG-LC-1)          <- WRONG
  10010
  10011      .199   .156  10150     .78   (a) 11204  .49   1.33 13111  2.99  .069
  10012      .048  (a)    10151  19.60      – 11205  (a)      – 13112   .084  .044
  ...
  10025
          .048    (a) 10210     .62     (a) 11209    7.70      – 13206   (a)   (a)

pypdf              (same page)                  <- CORRECT
  10010 .199 .156 10150 .78 (a) 11204 .49 1.33 13111 2.99 .069
  10011 .048 (a)  10151 19.60 – 11205 (a)  –   13112 .084 .044
  10012 .054 (a)  10160 3.51  – 11206 .76  –   13201 .93  .097
```

Class code `10010` loses its values entirely and `10011`'s values shift up onto it. The failure
is **silent and plausible** — every number is a valid loss cost, just attached to the wrong
class. Verified on GA, TX and NY (all `pdftotext`-capable) and on AK and AL (xref-damaged):
`pypdf` produced correctly paired rows in every case, `-layout` did not.

Independent confirmation from the parse: symbol counts reconcile exactly against the grid
geometry. Indiana, 4 territories × 1,188 classes × 2 columns = **9,504** cells; the parser
returns 5,828 numeric + 1,780 `(a)` + 1,896 `–` = **9,504**. A misaligned parse does not
reconcile.

> **41 of the 51 current notices are `pdftotext`-unreadable** (xref damage) and must go through
> `pypdf` regardless. So for the jurisdictions that matter most — the ones in force — the
> "fallback" is the primary path, and it is also the more accurate one.

Caveat carried into ingestion: `pypdf` injects spaces inside words
(`UNMANNED AIRCRAFT LI MITED LIABILITY`, `CG -LC -89`). Every caption and page-marker match in
this document set is therefore whitespace-normalised before comparison. A naive literal match
under-reports — it initially showed 4 jurisdictions missing the Unmanned Aircraft table when
all 51 carry it.

---

## 13.10 Countrywide values published on state pages

Two tables carry **identical values in every jurisdiction that publishes them**, despite living
in state documents:

**Unmanned Aircraft Limited Liability (Subline 370)** — 51/51, `$100,000/200,000` basic limit,
all territories, by maximum take-off weight × endorsement:

| Maximum take-off weight | `CG 24 50` BI/PD | PAI | `CG 24 51` BI/PD | PAI |
|---|---|---|---|---|
| 1 lb. or less | $66.11 | $87.63 | $66.11 | $87.63 |
| More than 1 lb. to 5 lbs. | 110.19 | 87.63 | 110.19 | 87.63 |
| More than 5 lbs. to 15 lbs. | 154.26 | 87.63 | 154.26 | 87.63 |
| More than 15 lbs. to 55 lbs. | 220.37 | 87.63 | 220.37 | 87.63 |
| More than 55 lbs. | RTC | RTC | RTC | RTC |

These are **flat dollar amounts, not rates** — no exposure multiplication. This confirms the A4
modifier-chain archetype in `11-RATING-ARCHITECTURE.md` §11.6 starts from a published base.

**OCP & Principals Protective (Subline 335)** — 15/15 of the jurisdictions still publishing it,
all territories, per $1,000 of total cost:

| Code | All territories |
|---|---|
| 16291 | .24 |
| 16292 | .24 |
| 27111 | .18 |
| 27112 | .16 |

Store both as countrywide-scoped with a jurisdiction-availability flag, not as 51 copies —
otherwise a countrywide revision requires 51 edits and will drift.

---

## 13.11 What remains open

| # | Item | Impact |
|---|---|---|
| ~~**G2**~~ | ~~ZIP → territory mapping~~ | **Closed at Step 8** — the Territory Pages of the Rules notices carry it, 51/51 (§13.8). What remains is engineering, not acquisition: the 4 county/city jurisdictions need a different resolver from the 27 ZIP ones |
| **G4** | Terrorism Supplement | Unchanged — absent from both corpora |
| **G5** | Company LCM | Carrier input by design; every value here is a pre-LCM ISO loss cost |
| **L1** | Workers Compensation loss costs | Required to resolve OCP class `15191` (51/51 jurisdictions) — an external line of business |
| **L2** | `GL-MI-2027-LC-003-C.pdf` truncated | Michigan's current loss costs must come from `GL-MI-2027-LC-002-C`; re-download needed |
| **L3** | Liquor (332) and Railroad Protective (335) have no published loss costs | ELP-driven or refer-to-company in all 51; not a download gap |
| **L4** | Cell values not yet extracted to storage | This document establishes the structure, vocabulary, invariants and correct extractor. The ~430,000 grid cells and ~20,600 ELP entries are volume work — see `10-BUILD-BACKLOG.md` Phase 3A |
| **L5** | 57 loss cost notices dated by proximity | `GL_LossCost_to_ERC.xlsx` matched 415 of 472 on a cited circular; the remainder are corpus-boundary cases whose effective dates are provisional |

**Not a gap:** there is no countrywide loss cost document to look for. Its absence is a
structural fact of the program (§13.2), not a hole in the download.
