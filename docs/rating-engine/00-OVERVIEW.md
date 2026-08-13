# 00 — GL Rating Engine Strategy: Overview

> **Reconciliation note, 2026-08-11.** This document was derived from the filed manual PDFs and **before any subline
> was derived end to end**. The per-subline gates have since superseded or sharpened some claims
> here — see [`../gates/RECONCILIATION.md`](../gates/RECONCILIATION.md) (items R1, R2, R3). The text below is
> left as the record of what this derivation found on its own; that independence is what makes
> agreement between the two derivations evidence.

**Scope:** A build-ready engineering strategy for a General Liability rating engine derived
**solely** from the ISO *Commercial Lines Manual, Division Six — General Liability* notices
held in this project:

| Corpus | Folder | Files | Supplies |
|---|---|---|---|
| **Rules** | `Commercial Line Manuals\GL\Rules\` | 503 | The algorithm, the state-variation surface, and the Territory Definitions |
| **Loss Costs** | `Commercial Line Manuals\GL\LossCosts\` | 472 | The operands — published loss costs and ELPs |

**Status:** Specification only. Nothing has been built.

**Evidence rule for this document set:** every structural claim, rule number, code, factor
name, and jurisdiction value is traceable to a named PDF in the corpus. Where the corpus does
*not* answer a question, that is stated explicitly as a **GAP** rather than filled by
assumption. See `09-GAPS-AND-OPEN-QUESTIONS.md` for the consolidated list.

---

## 0.1 The central architectural finding

The manual is not a flat rulebook. It is a **two-layer overlay system**, and the engine must
be built to mirror that shape rather than flatten it:

```
  COUNTRYWIDE BASE  (GL-MU-*.pdf — "MULTISTATE RULES")
        Rules 1–56, Classification Table, premium algorithm, coverage definitions
                              │
                              ▼  overlaid by
  STATE EXCEPTION PAGES  (GL-<ST>-*.pdf — "EXCEPTION PAGES")
        Per-rule operations: REPLACE / ADD / DOES-NOT-APPLY
        Plus state-only "A-rules" with no CW counterpart
        Plus ALL increased-limits tables and table assignments
```

**A third layer sits beside these two — the rate layer** (`GL-<ST>-*-LC-*.pdf`), which is
**purely state-level with no countrywide counterpart at all**. It is the mirror image of the
countrywide base: the CW layer holds the algorithm and no numbers; the rate layer holds the
numbers and no algorithm. See `13-LOSS-COSTS-AND-ELP.md`.

Three consequences drive the whole design:

1. **The countrywide layer is not self-sufficient for rating.** CW Rule 56.B says verbatim:
   *"The increased limits tables are displayed in the state exceptions."* There is no
   countrywide ILF table anywhere in `GL-MU-2027-RU-001-C.pdf`. A CW-only engine cannot
   produce a premium above basic limits for any jurisdiction.

2. **Rule numbers are not stable identifiers.** The 2027 countrywide edition renumbers 21 of
   the ~50 rules (e.g. Premium Determination moves from Rule 35 → Rule 21; Rule 16 changes
   from *Additional Interests* to *Additional Insured Endorsements*). Keying anything on the
   printed rule number will silently break across editions. See §2.3 and `A2-CW-RULE-CATALOG.md`.

3. **Deviation is the norm, not the exception, for the miscellaneous coverages.** Rules 24,
   45 and 56 are deviated by **all 51** jurisdictions; Rules 22, 44, 46, 47, 48, 49 and 53 by
   47–49 of 51. Meanwhile 13 rules — including the entire classification-assignment
   apparatus (Rules 25, 26, 27, 29, 31, 32) — carry **no** state exception in any current
   notice. The engine should therefore treat classification logic as countrywide-fixed and
   coverage/limit logic as state-resolved.

---

## 0.2 What is in the corpus, and what is not

| In scope (the corpora prove it) | Out of scope (referenced but absent) |
|---|---|
| Rules 1–56 countrywide, all editions 2021–2027 | **Terrorism Supplement** — most states' Rule A1/A2 says "Refer to the Terrorism Supplement to the CLM" |
| Classification Table (class code, premium base, application, separately-classify) | **Experience/Schedule Rating Plan (CGLES), Composite Rating, Size-Of-Risk** |
| All state exception pages for 51 jurisdictions | **Company loss cost multiplier** — carrier input by design (Rule 23.B) |
| Increased Limits Tables (Rule 56.B) and ILTAs (Rule 56.C) | **Workers Compensation loss costs** — needed only for OCP class `15191` |
| Liquor grades, payroll limitations, deductible rules | |
| **Territory Definitions** — `CG-T` pages, 51/51: ZIP tables (27), county/city (4), statewide (20) | |
| **Published ISO loss costs** — sublines 334, 336, 335, 370, by class and territory, 51/51 | |
| **ELP Supplement** — Procedures 1–5, Tables 5.B–5.E, 51/51 | |

**Updated at Steps 7–8.** The earlier statement of this split — *"the corpus gives you the
algorithm but not the rate tables"* — no longer holds. The loss cost corpus supplies the rate
tables and the ELP Supplement, and the Territory Definitions turned out to be in the Rules
corpus all along, on the `CG-T` pages. **The engine is priceable in all 51 jurisdictions** for
Premises/Operations and Products/Completed Operations; what is still missing — terrorism, the
rating plans, the carrier LCM — is genuinely external to Division Six.

---

## 0.3 Document set

| File | Contents |
|---|---|
| `00-OVERVIEW.md` | This document |
| `01-SOURCE-CORPUS.md` | Corpus inventory, extraction method, provenance, known defects |
| `02-CW-BASE-RULEBOOK.md` | The countrywide base: rule catalog, premium algorithm, edition renumbering |
| `03-SUBLINE-COVERAGE-PLAN.md` | Rating plan for every subline and coverage |
| `04-STATE-DEVIATIONS.md` | **Full deviation mapping** — matrix, frequency, A-rules |
| `05-LOOKUP-TABLES.md` | **Every lookup**, with per-jurisdiction values |
| `06-DATA-SCHEMA.md` | Proposed schema — relational DDL + JSON contracts |
| `07-ENGINE-ARCHITECTURE.md` | Calculation pipeline, resolution order, versioning |
| `08-INGESTION-SPEC.md` | PDF → structured data pipeline |
| `09-GAPS-AND-OPEN-QUESTIONS.md` | What the corpus cannot answer |
| `10-BUILD-BACKLOG.md` | Phased delivery plan |
| `11-RATING-ARCHITECTURE.md` | **Full calculation architecture** — ordered algorithm, exceptions and endorsement treatment for every subline, coverage and sub-coverage |
| `12-VERSIONING-AND-EDITIONS.md` | **The versioned instance** — CW base over time, edition migration, bitemporal resolution |
| `13-LOSS-COSTS-AND-ELP.md` | **The rate layer** — published loss costs, the ELP Supplement, rate resolution, the 15/36 vintage split |
| `A1-STATE-PROFILES.md` | Per-jurisdiction profile appendix |
| `A2-CW-RULE-CATALOG.md` | CW rule catalog + 2022↔2027 renumbering appendix |
| `A3-ENDORSEMENT-CATALOG.md` | Every endorsement form, its role and premium treatment, per coverage part |
| `A4-LOSS-COST-INVENTORY.md` | Per-jurisdiction rate inventory — territories, class counts, vintage, extractor |
| `index.html` | Interactive visualization of the deviation surface |
| `dataset.json` | Machine-readable form of every table in these documents |

---

## 0.4 Headline numbers

| Metric | Value | Source |
|---|---|---|
| Rules PDFs in corpus | 503 | `Commercial Line Manuals\GL\Rules\` |
| Successfully text-extracted | 502 | 1 truncated: `GL-MO-2027-RU-003-C.pdf` |
| Jurisdictions | 51 (50 states + DC + PR, no HI) | filename state codes |
| Countrywide (multistate) notices | 5 | `GL-MU-2022/2023×2/2027` |
| Edition years spanned | 2021–2027 | filename year segment |
| CW rules with ≥1 state exception | 33 | parsed exception pages |
| CW rules with **no** state exception | 13 | parsed exception pages |
| CW rules renumbered in the 2027 edition | 21 | CW 2022 vs CW 2027 diff |
| Distinct sublines | 8 | subline codes in CW manual |
| Deviations per jurisdiction | 4 (min) – 26 (max) | deviation matrix |
| Distinct endorsement forms | 328 | CW 2027 rule sections |
| (coverage part, form) placements | 447 | CW 2027 rule sections |
| Forms added / dropped, CW 2022 → 2027 | 40 / 21 | CW edition diff |
| Algorithm archetypes covering all coverages | 5 | `11-RATING-ARCHITECTURE.md` §11.2 |
| State notices per jurisdiction | 5 (min) – 17 (IL) | filename edition segment |
| **Loss cost PDFs in corpus** | **472** (471 extracted) | `Commercial Line Manuals\GL\LossCosts\` |
| **Countrywide loss cost notices** | **0** — the rate layer is purely state-level | filename state codes |
| **Jurisdictions with published loss costs** | **51 / 51** | loss cost grid pages |
| **Loss cost grid cells, current notices** | ~429,700 | class × territory × 2 sublines |
| **Cell alphabet** | 3 — numeric (64.3%), `–` not offered (18.6%), `(a)` refer (17.1%) | `13-LOSS-COSTS-AND-ELP.md` §13.4 |
| **ELP classes per jurisdiction** | 404 in 49 of 51 | ELP Supplement Table 5.B–5.E |
| **Premises/Operations territories** | 1 – 20 (20 jurisdictions have exactly 1) | `A4-LOSS-COST-INVENTORY.md` |
| **Jurisdictions actually territory-rated** | **31**, not the 27 implied by the Rules A-rule | `05-LOOKUP-TABLES.md` §5.4 |
| **Territory resolution schemes** | 3 — ZIP table (27), county/city (4), entire state (20) | `05-LOOKUP-TABLES.md` §5.4.1 |
| **ZIP → territory rows, current notices** | **23,719** (+432 county/city) | Rules `CG-T` pages |
| **Cross-corpus territory agreement** | **51 / 51 exact** | Rules `CG-T` vs loss cost grids |
| **Rate-basis vintage split** | **15 pre-2027 / 36 on the 2027 basis** | `13-LOSS-COSTS-AND-ELP.md` §13.7 |

---

## 0.5 Recommended build posture

Build the engine as a **versioned, overlay-resolving rules interpreter**, not as a
per-state codebase:

- One countrywide rulebook per **CW edition**, addressed by a stable semantic rule key.
- One state overlay per **(jurisdiction, notice)**, expressed as typed operations against
  that key.
- One **rate layer** per `(jurisdiction, loss cost notice)`, resolved on its **own** effective
  date — it is not an overlay on anything and has no countrywide parent.
- A resolver that materialises an *effective rulebook* for a
  `(jurisdiction, coverage, effective_date)` triple and caches it.
- All numeric content (ILFs, ILTAs, grades, payroll caps, loss costs, ELPs) in data tables,
  never in code — and non-numeric dispositions (`–`, `(a)`, `Incl.`, `RTC`) preserved as typed
  values, never coerced to zero.

The alternative — 51 branches of state logic — is directly contradicted by the evidence:
the states do not implement different algorithms, they supply different **operands** to one
algorithm, plus a bounded set of typed rule operations. See `07-ENGINE-ARCHITECTURE.md`.
