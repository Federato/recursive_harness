# Process Log — Recursive Harness 2.0 (GL ERC ↔ Commercial Lines Manual)

Running log of every step directed by the user in this process. Newest steps
are appended at the bottom. Each entry records the date, what was directed,
what was done, and the resulting artifacts.

**Working directory:** `C:\Projects\Recursive_Harness_2.0`

---

## STANDING CRITERIA — build doctrine, set 2026-08-10 (Step 20)

Directed by the user and **binding on all subsequent work** on the rating engine:

> Build the rating engine **based on the ERC files**, with the **PDFs as confirmation of the
> build, and not the source**. There are to be **no assumptions outside of what exists in the
> files**. Where confirmation is needed, **refer to the manuals**; and if that fails, **ask
> directly**.

Operationalised as a three-tier evidence hierarchy:

| Tier | Source | Licensed to | **Not** licensed to |
|---|---|---|---|
| **1 — Source** | ERC packages | Supply every value, table, key, rule, edition, structure | — |
| **2 — Confirmation** | Manual PDFs | *Confirm* the meaning of something present in ERC | **Supply a value or mechanism ERC lacks** |
| **3 — Decision** | The user | Settle what tiers 1 and 2 cannot | — |

**Tier 2 confirms; it never sources.** The manual may tell us ERC's `0` in the drone table means
*Refer To Company* — confirming a value that exists in ERC. It may **not** supply an ILF
interpolation procedure ERC has no machinery for; that is sourcing, and it escalates.

**Nothing is invented at any tier.** If ERC lacks it and the manual does not explain it, the
engine does not do it: it escalates and returns `REFER` until answered. **Where the two disagree,
ERC's value stands but the conflict is never resolved silently** — it is logged, marked
`attested=False`, and escalated.

Enforced in code, not by review: `Cell.erc_source` is mandatory, so a value with no ERC source
cannot be constructed; `confirm/` and `escalate/` are modules whose records carry citations.

---

## STANDING CRITERIA — read, do not assume (set 2026-08-10, Step 21)

Directed by the user after the fourth repetition of the same defect:

> **Make sure you READ what's needed to be read instead of assuming. This keeps happening.**

### The pattern, named

Nine instances to date, all the same shape: **measure structure, then infer content from names.**

| # | Assumed | Reality | What was never opened |
|---|---|---|---|
| 1 | Territory definitions absent from both corpora | In the Rules PDFs all along | The `CG-T` pages |
| 2 | Analysis was reproducible | Scripts were in a temp directory | The scripts' own location |
| 3 | Rating plans unavailable | ERC carries all four, populated | The ERC rate/domain tables |
| 4 | 21 jurisdictions cannot determine territory | 20 are single-territory | Those states' `PremOpsTerr` |
| 5 | ERC's "minimum 4 territories" | Pooled every geographic column | What the column actually held |
| 6 | `ErcCore` blocks rule semantics | Supplies 2 of 28,233 elements — an envelope | The `xs:import` and its usage |
| 7 | Six operator semantics undefined | Each has exactly **one** value corpus-wide | The attribute values |
| 8 | Rounding mode unstated | `rul:Round DecimalPlaces=n`, 648 sites | The rule operators |
| 9 | Three multipliers untraced | All computed by named rules | `ToDataDef=` |

Items 6–9 all occurred **in a single exchange**, after items 1–5 had already been logged and
written up as lessons. Documenting the pattern did not prevent it.

### The rule, operationalised

**Before asserting that something is absent, undefined, untraced or unavailable — open it.**

| Never assert from | Always read |
|---|---|
| A name (`ErcCore` sounds core) | The definition and its usage count |
| A count or a schema shape | The values themselves |
| An attribute's existence | Its distinct values across the corpus |
| "No table for X" | `ToDataDef="X"` — X may be rule-computed |
| One corpus | Both, and name which was searched |
| A prior conclusion | Re-test it against current holdings |

An escalation is only valid if it names **the file opened and the search run** that failed to
answer it. An escalation without that is an assumption wearing a label.

---

## Step 0 — Log established

- **Date:** 2026-08-09
- **Directed:** "Keep an md file log of every step that I direct in this process."
- **Action:** Created this file (`PROCESS_LOG.md`) and back-filled the prior
  steps below from the current state of the working directory.

---

## Step 1 — Download all GL Rules Commercial Lines Manuals

- **Date:** on/before 2026-08-07
- **Directed:** Download every Rules Commercial Lines Manual for General
  Liability.
- **Action:** Manuals downloaded as PDFs.
- **Location:** `Commercial Line Manuals\GL\Rules\`
- **Result:** **503 PDF files**, named `GL-<ST>-<YYYY>-RU-<NNN>-C.pdf`
  (e.g. `GL-AK-2022-RU-001-C.pdf`), spanning all states/jurisdictions and
  edition years ~2021–2027.
- **Known housekeeping item:** at least one duplicate download is present —
  `GL-DE-2022-RU-001-C (1).pdf` alongside `GL-DE-2022-RU-001-C.pdf`.

---

## Step 2 — Download all GL ERC files / build the edition hierarchy

- **Date:** on/before 2026-08-07
- **Directed:** Download every GL ERC file.
- **Action:** ERC circulars collected and consolidated into an edition
  hierarchy workbook.
- **Artifacts:**
  - `GL_ERC_Edition_Hierarchy.xlsx`
  - `GL_ERC_Edition_Hierarchy.html` (HTML rendering of the same)
- **Workbook tabs:** `Read Me`, `Manual Legend`, `CW Parents`,
  `Edition Hierarchy`, `Manual Matrix`, `ERC Circulars`, `Rules PDFs`,
  `PDF to ERC Matches`, `Manual Coverage`, `Gaps`
- **Structure captured:** each state ERC version (`GL <ST> <YYYYMMDD> V<NN>`)
  is tied to its countrywide parent edition (`GL_CW_<YYYYMMDD>_V<NN>`).

---

## Step 3 — Map each ERC version to its associated Commercial Lines Manual

- **Date:** on/before 2026-08-07
- **Directed:** Map every ERC version to an associated Commercial Lines Manual.
- **Action:** Produced a crosswalk workbook joining ERC versions to the
  downloaded Rules manual PDFs.
- **Artifact:** `GL_ERC_to_Manual.xlsx` — sheet `ERC to Manual`
- **Columns:** `State ERC Version` | `CW Parent` | `Commercial Lines Manual`
- **Coverage as of this log:**
  | Metric | Count |
  |---|---|
  | ERC versions (rows) | 570 |
  | Mapped to a manual PDF | 544 |
  | Unmapped / gaps | 26 |
- **Open item:** 26 ERC versions have no manual assigned; the `Gaps` tab of
  `GL_ERC_Edition_Hierarchy.xlsx` is the reference for reconciling these.

---

## Step 4 — Full rating engine strategy, mapping, schema & engineering spec

- **Date:** 2026-08-09
- **Directed:** "Look at the commercial lines manuals, the entire history, and develop a
  full rating engine strategy based solely on these PDF documents. I want a plan for every
  subline and coverage, a CW Base, and specific state deviations. Where do states deviate?
  Which lookups, which rules? I want a full mapping, and a proposed schema based off of this.
  DO NOT MAKE ASSUMPTIONS, everything should be based on documentation, and sourced. Create a
  full engineering spec and schema plan, get us fully ready to build, without actually
  building. I want this document as MD files and visualized fully in html or appropriate
  file types."

### Action

1. **Extracted all 503 manual PDFs to text**, in two modes:
   - reading order (`pdftotext`) — for rule parsing; the exception pages are two-column and
     layout mode interleaves unrelated rules onto one physical line;
   - layout (`pdftotext -layout`) — for factor tables, where column position is the data.
   - 103 files had damaged xref tables and failed `pdftotext` silently; all recovered via
     `pypdf`. **502 of 503 extracted.**
2. **Parsed the countrywide base** (`GL-MU-2027-RU-001-C`, "1st Edition 4-27", filing
   `GL-2024-RRU24`) and the prior edition (`GL-MU-2022/2023`) for rule catalog, premium
   algorithm, sublines, classification structure, and limits mechanics.
3. **Parsed all 490 de-duplicated state notices** for rule-level exceptions, classified into
   typed operations (REPLACE / ADD / DOES-NOT-APPLY / TABLE), with paragraph-level targets.
4. **Extracted concrete state lookup values** — payroll limitations, liquor grades, ILF table
   inventories, territory/Stop Gap/ELP flags — for all 51 jurisdictions.
5. **Wrote the specification** (11 documents + 2 appendices), the **proposed schema**, and an
   **interactive HTML visualization**. Rendered and verified the HTML in a browser.

### Result — `docs\rating-engine\`

| File | Contents |
|---|---|
| `README.md` | Index and headline findings |
| `00-OVERVIEW.md` | Strategy, scope, evidence rule |
| `01-SOURCE-CORPUS.md` | Corpus inventory, extraction method, provenance, defects |
| `02-CW-BASE-RULEBOOK.md` | CW base: rule catalog, premium algorithm, edition renumbering |
| `03-SUBLINE-COVERAGE-PLAN.md` | Rating plan for all 17 coverages / 8 sublines |
| `04-STATE-DEVIATIONS.md` | Full deviation matrix (51 × 33), frequency, A-rules |
| `05-LOOKUP-TABLES.md` | Every lookup with per-jurisdiction values |
| `06-DATA-SCHEMA.md` | Relational DDL + JSON contracts |
| `07-ENGINE-ARCHITECTURE.md` | Resolver, calculation pipeline, rejected designs |
| `08-INGESTION-SPEC.md` | PDF → data pipeline, 11 validation assertions |
| `09-GAPS-AND-OPEN-QUESTIONS.md` | What the corpus cannot answer |
| `10-BUILD-BACKLOG.md` | Phased plan, ~13–17 weeks |
| `A1-STATE-PROFILES.md` | Per-jurisdiction appendix |
| `A2-CW-RULE-CATALOG.md` | CW rule catalog + 2022↔2027 renumbering |
| `index.html` | Self-contained interactive visualization |
| `dataset.json` | Machine-readable form of every table |

### Key findings

- **The CW layer cannot rate alone.** CW Rule 56.B: *"The increased limits tables are
  displayed in the state exceptions."* There is no countrywide ILF table.
- **Rule numbers are edition-scoped labels, not identifiers.** CW 2027 renumbers 21 rules
  (Premium Determination 35 → 21; Rule 22 changes meaning entirely). Highest-severity
  correctness risk; the schema keys rules semantically.
- **The ILTA code is composite** — `2B` = Premises/Operations Table 2 + Products/Completed
  Operations Table B (Rule 15.D.2 joined with the state ILTA pages).
- **Deviation concentrates in coverage/limits, not classification.** Rules 24, 45, 56 deviated
  by all 51 jurisdictions; the whole classification apparatus (25, 26, 27, 29, 31, 32)
  deviated by none.
- **Payroll limitation has three structural shapes**, not one number — 5 jurisdictions use a
  weekly min/max band with no annual executive cap.
- **Five coverages are explicitly refer-to-company** (Rules 41, 42, 43, 47, 53) — they need a
  referral workflow, not an invented formula.

### Open items raised (not resolved in this step)

- Rates/loss costs, Territory Definitions, ELP Supplement and Terrorism Supplement are
  referenced by the manual but **outside this corpus** — the engine is buildable and testable
  without them, but not priceable.
- `GL-MO-2027-RU-003-C.pdf` is truncated and needs re-download.
- 264 of 503 PDFs were dated by edition-date proximity only ("low confidence") in the earlier
  ERC mapping; effective dating drives edition selection, so this propagates into premium.
- Hawaii is absent from the corpus — scope decision needed.

---

## Step 5 — Full rating architecture, endorsements, and the versioned instance

- **Date:** 2026-08-09
- **Directed:** "Include in all documentation, the full rating architecture, including
  algorithms, steps, deviations, exceptions, etc., for every subline, coverage, sub-coverage,
  endorsements etc... Highlight how this would be implemented in a versioned instance, meaning
  using Countrywide Manuals as a base, how would this evolve over time. Log that we are doing
  this work, and how you accomplished it, and the thought process behind this."

### Thought process — why the work was scoped this way

Step 4 produced a *plan*: one row per coverage, naming the governing rule and the deviation
count. That is enough to scope a build and not enough to write one. The gap between "Rule 45
governs Liquor Liability" and "here are the nine ordered steps, the two paragraphs of Rule 15
that Rule 45 switches off, and the table the deductible discount comes from" is the entire
implementation.

Three judgements shaped the approach:

1. **Read the manual's own structure rather than impose one.** Before writing anything, the
   coverage rules were dumped and compared side by side. They turned out to be written to a
   single repeating skeleton — Description → Exceptions To Section I General Rules → Mandatory
   Endorsements → Optional Endorsements → Rates → Classifications → Premium Determination →
   Deductibles → Claims-made. That discovery is what made the work tractable: one parser and
   one schema shape serve all seventeen coverages, and a **missing** paragraph is itself
   information. Rules 46 and 49 have no deductible paragraph at all, which is why the spec now
   says a deductible on those coverages must be *rejected*, not ignored.

2. **Classify before enumerating.** Rather than write seventeen bespoke algorithm sections,
   the coverages were sorted into five archetypes (full nine-step, eight-step without a
   premium-base step, factor-on-a-host-subline, modifier chain, refer-to-company). Five
   executors instead of seventeen is a materially different build.

3. **Refuse to transcribe what cannot be verified.** The Rule 40 hazard-grade tables
   (`CG-60`–`CG-69`) are multi-column with wrapping rows; reading-order extraction interleaves
   the two grade columns. Publishing those values would have looked more complete and been
   less true. They are documented as an ingestion target with a dedicated validation assertion
   (V14) instead, and the reason is stated: a mis-aligned hazard grade moves premium by up to
   7×. The published factor tables that *were* verifiable (40.C, 40.D, 40.E, 44.A.5.a.(5))
   are transcribed in full.

On versioning, the initial instinct — "countrywide base, apply state overrides" — was tested
against the corpus and abandoned. It fails on three documented facts: the base has no ILF
table at all (Rule 56.B), printed rule numbers are reused across editions with different
meanings (Rule 22), and 48 jurisdictions carry Terrorism A-rules with no countrywide
counterpart to override. The model in doc 12 is therefore **composition of three streams**,
not inheritance.

### Action

1. **Recovered the prior session's extracted corpus** — 502 reading-order and 502 layout-mode
   text files from Step 4 were still on disk, so no PDF re-extraction was needed.
2. **Extracted the anatomy of every coverage rule** (`anatomy.py`): lettered paragraph
   headings, premium-determination step lists, and every endorsement form reference with the
   paragraph that governs it. Verified paragraph letters per rule against the source text
   rather than assuming the sequence.
3. **Read the premium-determination text verbatim** for Rules 21, 37, 40, 44, 45, 46, 48, 49
   and 55, and transcribed the ordered steps with citations.
4. **Built the endorsement catalog** (`catalog.py`, `gen_a3.py`): 328 distinct forms across
   **447 (coverage part, form) placements**, each tagged with one of six roles read off the
   manual's own headings. Two extraction defects were found and fixed on inspection — Rule 16
   additional-insured forms losing their role, and endorsement names bleeding from preceding
   sentences.
5. **Diffed the CW 2022 and CW 2027 form sets** — 40 forms added, 21 dropped.
6. **Computed the edition-churn profile** — 4 distinct countrywide editions against 490 state
   notices, 5–17 per jurisdiction, which is the evidence behind the two-stream versioning model.
7. **Wrote the two new specification documents**, extended the schema, ingestion, architecture
   and backlog documents, regenerated `dataset.json` and `index.html`, and verified the
   visualization's render logic executes without error under a DOM shim (browser `file://`
   access was unavailable in this session, so the JavaScript was syntax-checked and executed
   headlessly instead).

### Result

| File | Change |
|---|---|
| `11-RATING-ARCHITECTURE.md` | **New.** Canonical rule anatomy; five algorithm archetypes; ordered steps for every coverage with citations; endorsements as rating objects; whole-policy order of operations; where the state layer intervenes per pipeline step |
| `12-VERSIONING-AND-EDITIONS.md` | **New.** Two-stream version model, semantic rule keys with two invariants, three-part composition, bitemporal resolution with snapshot hashes, seven edition-change types, three release gates |
| `A3-ENDORSEMENT-CATALOG.md` | **New.** 328 forms × 447 placements by coverage part and role; per-jurisdiction mandated forms; CW 2022↔2027 form diff |
| `06-DATA-SCHEMA.md` | §6.11 coverage parts / archetypes / rule suspension · §6.12 endorsement catalog + constraints · §6.13 referral predicates |
| `07-ENGINE-ARCHITECTURE.md` | Kernel scoped as the A1 archetype; A3 host ordering and suspension pass called out; three new referral sources |
| `08-INGESTION-SPEC.md` | Assertions V12–V15 (edition attribution, form syntax, hazard-grade rows, constraint integrity) |
| `10-BUILD-BACKLOG.md` | Tasks 5.10–5.15 and 7.6–7.8; re-estimate **13–17 → 16–21 weeks** |
| `03-SUBLINE-COVERAGE-PLAN.md` | Corrected: Rule 46 carries **three** sub-coverages; Rule 46.J is 8 steps, not 7 |
| `00-OVERVIEW.md`, `README.md` | Document set, headline numbers, index |
| `index.html`, `dataset.json` | Three new sections (architecture table, published factor tables, endorsement roles, edition churn) and the backing data |

### Findings new to this step

- **Every coverage rule shares one skeleton**, and its *absent* paragraphs are meaningful —
  Rules 46 and 49 provide no deductible mechanism at all.
- **Paragraph B is a rule-suspension list.** Rule 45.B switches off Rule 15.A–D and F for
  Liquor; Rule 44.A.4 switches off Rule 16 entirely, so **additional insureds are unavailable
  on Product Withdrawal**.
- **Rule 46 has three sub-coverages, not two.** Principals Protective (`CG 28 07`) and
  Construction Project Management Protective (`CG 31 15`) are described as endorsements that
  *"convert"* the OCP coverage form — they are coverage-part transforms, and modelling them as
  additive endorsements would double-count.
- **Referral is input-conditional, not static.** A Product Withdrawal Participation Percentage
  or Cut-off Date on the Declarations flips an otherwise algorithmic coverage to refer-to-company.
- **Endorsements inside the loss cost invert the sign.** Removing a conditional-mandatory form
  is a refer-to-company *credit*, which an additive-charge model cannot express.
- **Rule 40 factor tables recovered in full** — hazard grades 1–4 at 0.0010/0.0030/0.0050/0.0070
  (`CG 04 37`), 0.0008/0.0024/0.0040/0.0056 (`CG 04 71`), 0.0010/0.0040/0.0070/0.0100 (Cyber).
- **The two version streams move at different rates** — 4 countrywide editions against 490
  state notices. Any single "manual version" field is wrong on day one.

### Open items raised (not resolved in this step)

- **The edition each state notice was authored against is not yet captured as a field.** It is
  present in the notice text but unextracted. Invariant I1 in doc 12 depends on it; this is now
  the highest-value remaining ingestion task.
- **Tables 40.F / 40.G hazard-grade values remain unextracted** — extractable from this corpus,
  but they require layout-aware parsing with assertion V14 before they can be trusted.
- Prior open items from Step 4 (264 low-confidence PDF dates, 26 unmapped ERC versions,
  truncated `GL-MO-2027-RU-003-C.pdf`, absent Hawaii, missing rate/territory/terrorism sources)
  are unchanged and now restated in doc 12 §12.8 in terms of what they break at resolution time.

---

## Step 6 — Match Loss Cost notices to ERC editions

- **Date:** 2026-08-10
- **Directed:** "Review the files in `Commercial Line Manuals\GL\LossCosts`, there are
  circular editions cited, similar to the Rules Manuals, attempt to match Loss Cost
  circulars to ERC editions, in a simple excel spreadsheet."

### Action

1. **Confirmed the loss cost notices carry the same page-1 header** as the rules notices —
   `NOTICE GL-<ST>-<YYYY>-LC-<NNN>` followed by `REFERENCE INFORMATION` with
   `Circular Reference(s)` (dated) and `Filing Reference(s)`. Only pages 1–2 were extracted.
2. **Extracted 472 loss cost PDFs** via `pdftotext`, with a `pypdf` fallback for damaged
   xref tables. **471 of 472 extracted**; `GL-MI-2027-LC-003-C.pdf` is truncated with no
   readable page 1.
3. **Matched against the existing ERC circular index** (`GL_ERC_Edition_Hierarchy.xlsx`,
   sheets `ERC Circulars` and `Edition Hierarchy`) using three ordered tiers:
   circular reference → filing reference → effective-date proximity. The matched edition is
   the **earliest** state ERC edition carrying the key, i.e. where the notice was first
   implemented; every later edition it stays live in is listed alongside.

### Result — `GL_LossCost_to_ERC.xlsx`

| Sheet | Contents |
|---|---|
| `Read Me` | Method, tier definitions, counts, known limits |
| `LC to ERC` | 472 rows — one per PDF, with circular/filing keys, match method, confidence, matched ERC edition, CW parent, and all editions carrying the circular |
| `ERC to LC` | Reverse view — all 580 ERC editions with the loss cost notices attached to each |
| `Gaps` | The 58 low-confidence and unmatched rows |

| Confidence | Count | Basis |
|---|---|---|
| High | 410 | Circular reference found in the state's own ERC circular list |
| Medium | 4 | Filing reference found for the state |
| Low | 57 | Effective-date proximity only |
| Unmatched | 1 | Truncated PDF |

- **317 of 580 ERC editions** have at least one loss cost notice attached.

### Findings

- **Loss cost circulars are indexed by ERC the same way rules circulars are** — 87% match on
  the cited circular alone, so no new matching method was needed.
- **The 57 low-confidence rows are a corpus-boundary artifact, not a parsing failure.** They
  split into two clean groups: notices citing **2019–2020** circulars, which predate the
  earliest ERC edition on disk (12/01/2020), and **mid-2026** state loss cost circulars that
  postdate the newest ERC edition downloaded for that state. Their *filing* references
  (`GL-2019-BGL1`, `GL-2020-BGL1`, `GL-2026-RLC26`) are present in the ERC corpus but under
  other states, so a state-scoped filing match was not available.
- **A circular number contains a filing-shaped substring** (`LI-GL-2020-100` → `GL-2020-100`),
  which produces phantom filing references if not suppressed. Filtered in extraction.

### Open items raised (not resolved in this step)

- `GL-MI-2027-LC-003-C.pdf` needs re-download (joins `GL-MO-2027-RU-003-C.pdf`).
- The 57 proximity-dated rows would resolve to citations if the 2026-2027 ERC editions for
  those states were downloaded; the pre-2021 group needs pre-12/2020 ERC editions that may
  not be obtainable.
- **263 ERC editions carry no loss cost notice** — expected for forms/rules-only editions,
  but not yet distinguished from download gaps.

---

## Step 7 — Fold the loss cost corpus into the rating-engine specification

- **Date:** 2026-08-10
- **Directed:** "Update or create new, appropriate docs in
  `C:\Projects\Recursive_Harness_2.0\docs\rating-engine`."

### Thought process — why this was more than an addendum

Step 6 matched loss cost notices to ERC editions by reading page 1 of each PDF. That was
enough to build a crosswalk and not enough to write specification. The documents in
`docs\rating-engine` carried a load-bearing claim — *"the corpus gives you the complete rating
algorithm but not the rate tables themselves… it cannot be priced"* — repeated across the
README, the overview, the gaps register, the architecture and the backlog. The loss cost corpus
falsifies that claim. Adding a new document and leaving the old ones asserting the opposite
would have been worse than not writing it.

So the work was scoped as: **read the whole corpus properly, then correct every document the
new evidence touches** — including where the new evidence contradicts an earlier finding.

Two judgements shaped it:

1. **Do not write about content read only at the header level.** All 472 PDFs were extracted in
   full (both `pdftotext -layout` and `pypdf`, ~1.5 hours wall clock, parallelised) before any
   claim was made about structure. This immediately paid for itself — see the extraction finding
   below, which is invisible from page 1.
2. **Verify counts arithmetically, not by eye.** Every per-jurisdiction figure was reconciled
   against the grid geometry before publication. Three separate claims were withdrawn during
   the work because they turned out to be extraction artefacts rather than facts (§ below).

### Action

1. **Extracted all 472 loss cost PDFs in full**, twice — `pdftotext -layout` and `pypdf` —
   parallelised across 10 workers. 471 of 472 succeeded; `GL-MI-2027-LC-003-C.pdf` is truncated.
2. **Probed every file for extractor capability**: 389 readable by `pdftotext`, **83 with
   damaged xref tables**, including **41 of the 51 current notices**.
3. **Analysed structure across all 471 documents** — page families, page-count invariants,
   subline inventory, territory keys, basic limits, cell vocabularies, class-code sets,
   ELP entries, and content presence per jurisdiction.
4. **Cross-checked against the Rules corpus**, which produced a correction to
   `05-LOOKUP-TABLES.md` §5.4 and resolved open question Q4.
5. **Wrote two new documents and revised twelve**, then regenerated `dataset.json` and
   `index.html` and executed the visualization's render logic headlessly under a DOM shim.

### Result

**New**

| File | Contents |
|---|---|
| `docs\rating-engine\13-LOSS-COSTS-AND-ELP.md` | The rate layer — corpus shape, document anatomy, loss cost grid and its three-token vocabulary, the ELP Supplement and its four-token vocabulary, the five-way rate resolution procedure, derived rates, the 15/36 vintage split, the territory model, the extraction inversion, and what remains open |
| `docs\rating-engine\A4-LOSS-COST-INVENTORY.md` | Per-jurisdiction inventory — latest notice, notices held, territory count and exact territory numbers, page counts, class and ELP counts, vintage, extractor, ERC edition — plus roll-ups |

**Revised**

| File | Change |
|---|---|
| `README.md` | Two-corpus framing; scope boundary rewritten (priceable, blocked only on ZIP→territory); a **fourth** headline finding; three-mode method note; nine new headline numbers |
| `00-OVERVIEW.md` | §0.1 third layer; §0.2 in/out-of-scope table rewritten; document set; ten new headline numbers; build posture |
| `01-SOURCE-CORPUS.md` | New **§1.6** — the Loss Costs corpus, the extraction inversion with evidence, and the two extra mandatory provenance fields |
| `03-SUBLINE-COVERAGE-PLAN.md` | New **§3.1.1** rate-source-per-coverage table; Prod/COps statewide-territory fact; the `(−)` marker now readable |
| `05-LOOKUP-TABLES.md` | §5.4 **corrected** (31 territory-rated, not 27); §5.6 **superseded** (ELP Supplement present 51/51); new **§5.7** published loss costs |
| `06-DATA-SCHEMA.md` | §6.10 two entries superseded; new **§6.14** — `lc_edition`, `loss_cost`, `elp`, `loss_cost_mapping`, `territory`, countrywide rate tables, and two corrections this forces elsewhere |
| `07-ENGINE-ARCHITECTURE.md` | STEP C rewritten from an external stub into the real five-way resolution |
| `08-INGESTION-SPEC.md` | §8.2 filename grammar extended to `KIND ∈ {RU, LC}`; §8.3 rewritten as **three modes selected by page family** with the misalignment evidence; four new segment types; new §8.5.5–8.5.7 parsers; assertions **V16–V21** |
| `09-GAPS-AND-OPEN-QUESTIONS.md` | **G1 and G3 closed**, G2 narrowed, **G9 added**; defects D5–D7 added; **Q4 resolved** (with a correction); Q7, Q8 added; two new deliberate-omission entries |
| `10-BUILD-BACKLOG.md` | New **Phase 3A** (8 tasks); Phase 6 stubs reduced from four to three; tasks 7.9, 7.10; critical path redrawn; re-estimate **16–21 → 18–24 weeks** |
| `11-RATING-ARCHITECTURE.md` | §11.11 substantially rewritten, including **three coverages that rate differently than assumed**; step-3 source corrected in two algorithms |
| `12-VERSIONING-AND-EDITIONS.md` | Two streams → **three**; composition gains a fourth term; new **§12.5.1** rate-stream change types with the live migration |
| `dataset.json` | New `loss_costs` block — corpus, vocabularies, vintage split, OCP timeline, class-code counts, subline rate sources, territory analysis, 51 state records |
| `index.html` | Three new sections (11 cell vocabulary, 12 the 15/36 migration, 13 per-jurisdiction rate inventory with the A-rule mismatch highlighted); dataset refreshed; render verified headlessly |

### Key findings

- **The rate layer has no countrywide document at all** — 471 state-only notices. It is the
  mirror image of the Rules corpus, where the countrywide layer holds the algorithm and no
  numbers. This makes it a **third independently versioned stream**, not an overlay.
- **`pdftotext -layout` silently corrupts every loss cost grid**, and `pypdf` — previously
  treated as a damaged-file fallback — is the correct parser. Values detach from their class
  code and reattach to the neighbouring one; every resulting number is a plausible loss cost.
  Confirmed arithmetically (Indiana: 4 × 1,188 × 2 = 9,504 cells, and the `pypdf` parse returns
  exactly 9,504). This inverts the guidance in `08-INGESTION-SPEC.md` §8.3 for these pages.
- **The corpus is mid-migration, and the split is a clean 15 / 36.** The 2027 filing retires 229
  class codes, introduces 204, and withdraws the OCP/Principals Protective loss cost table.
  Three independent tests select **identical** jurisdiction sets. Every notice through 2026
  published the OCP table (390 of 390); only 22 of 58 2027 notices do.
- **The loss cost cell alphabet is closed and three-valued** — numeric 64.3%, `–` not offered
  18.6%, `(a)` refer 17.1%, over ~429,700 cells. Coercing either non-numeric token to zero
  produces a free policy or sells coverage the manual declines.
- **Liquor Liability and Railroad Protective have no published loss cost in any jurisdiction** —
  only ELPs — despite Rules 45 and 49 specifying full step-by-step algorithms around a "basic
  limits rate". A rating-mode correction, not a data gap.
- **Rate resolution is recursive.** The `CG-LCADD` pages express a class's loss cost as a
  percentage of *another class's* (*"Use 116% of premises/operations loss cost of class 12373"*),
  so the rate layer is a small graph needing cycle detection.
- **One ELP crosses lines of business** — OCP class `15191` is *"Percentage of otherwise
  applicable Workers Compensation loss costs: 75%"*, in 51 of 51 jurisdictions. A GL engine
  cannot resolve it from GL data at all.
- **Territory applies to Premises/Operations only**; Products/Completed Operations is always
  written to statewide territory `999`. `CG-LC` page count is exactly `8·T + 1` in all 51.
- **31 jurisdictions are territory-rated, not the 27** implied by the Rules A-rule — CA, FL, NY
  and TX rate by territory with no A-rule, and are among the most territorialised in the
  program (NY 20, CA 11, TX 8, FL 5).
- **Unmanned Aircraft loss costs are flat dollar charges**, identical in all 51 jurisdictions —
  premiums, not rates. Multiplying them by an exposure count is a defect.

### Claims withdrawn during the work

Recorded because each looked like a finding and was not:

- *"The OCP table is missing from 36 jurisdictions' page set"* — first measured as 15/51 by a
  page-scoped search and 17/51 by a document-scoped one. The document-scoped extras (LA, PA)
  were digit-sequence false positives from adjacent grid cells. Re-measured with an anchored
  four-class pattern: **15**, all with identical values.
- *"Four jurisdictions do not publish the Unmanned Aircraft table"* — a `pypdf` artefact.
  It renders `UNMANNED AIRCRAFT LI MITED LIABILITY`. All 51 carry it.
- *"The `8·T+1` page invariant holds in 47 of 51"* — the four exceptions were `CG -LC -89`
  style markers with injected spaces. It holds in **51 of 51**.

All caption and marker matching in the published analysis is whitespace-normalised as a result,
and that requirement is now specified in `08-INGESTION-SPEC.md` §8.3.1.

### Open items raised (not resolved in this step)

- **G2 (ZIP → territory) is now the single blocking gap for pricing** — it stops 31 of 51
  jurisdictions, including the four largest by territory count. Nothing else does.
- **Q7** — no class-code crosswalk exists for the 229-retired / 204-introduced 2027 revision,
  so re-rating a pre-2027 risk under a 2027 edition has no defined mapping.
- **Q8** — whether the OCP loss cost withdrawal is permanent or transitional determines which
  rate path the OCP executor should treat as primary.
- **G9** — Workers Compensation loss costs, needed for OCP class `15191` in all 51.
- **L4** — the ~429,700 grid cells and ~20,600 ELP entries are specified but not extracted to
  storage. That is Phase 3A, and it is the gate on any dollar amount.
- `GL-MI-2027-LC-003-C.pdf` needs re-download (joins `GL-MO-2027-RU-003-C.pdf`).

---

## Step 8 — Correction: the Territory Definitions were in the corpus all along

- **Date:** 2026-08-10
- **Directed:** "Territories exist in the Rules Pages, for example,
  `Commercial Line Manuals\GL\Rules\GL-NJ-2026-RU-001-C.pdf`, starting on page 27."

### The error

Step 7 recorded gap **G2** — the ZIP→territory mapping — as the single blocking dependency for
pricing, stopping 31 of 51 jurisdictions. That was wrong. Every Rules notice carries
**Territory Pages** (`CG-T-1` … `CG-T-n`) after the exception pages, and in the 27
ZIP-scheme jurisdictions those pages hold the complete ZIP→territory table.
`GL-NJ-2026-RU-001-C.pdf` pages 27–37 carry `CG-T-1` (definitions) plus ten ZIP tables —
**721 ZIP rows** for New Jersey alone.

**How it happened — two compounding failures:**

1. `05-LOOKUP-TABLES.md` §5.4 had asserted since Step 4 that the definitions were *"held
   outside the Rules manual in ISO Territory Definitions."* That claim was carried forward
   into the gaps register without ever being tested against a PDF.
2. At Step 7 the **loss cost** corpus was searched for the string `ZIP`, correctly returned
   zero — and that result was generalised to *"absent from both corpora."* **The Rules corpus
   was never searched.** A negative result was reported at a scope wider than the search that
   produced it.

The second failure is the more serious one, because it dressed an unchecked assumption in the
appearance of evidence.

### Action

1. **Scanned all 503 Rules PDFs** for Territory Pages (parallel `pypdf`, page-level), capturing
   `CG-T` markers, territory definitions, ZIP rows and city/county rows.
2. **Classified the resolution scheme** per jurisdiction and reconciled the territory codes on
   the `CG-T` pages against the territories published on the loss cost grids.
3. **Corrected every document** carrying the G2 claim, and added a standing correction section
   to the gaps register so the failure mode is recorded rather than quietly patched.
4. Re-tested the remaining ❌ gaps (G4, G5, G6, G9) against **both** corpora by
   whitespace-normalised full-text search, so no other entry rests on a single-corpus search.

### Result

| File | Change |
|---|---|
| `05-LOOKUP-TABLES.md` | §5.4 corrected with the NJ evidence quoted; new **§5.4.1** — Territory Pages, the three resolution schemes, volumes, why the A-rule marks the ZIP scheme, and why the county/city scheme is the harder resolver |
| `09-GAPS-AND-OPEN-QUESTIONS.md` | **G2 → CLOSED**; new **§9.6** recording the correction, how the error happened, and the re-verification of the remaining gaps |
| `06-DATA-SCHEMA.md` | `territory_definition` stub replaced by `territory_definition_set` + `territory_zip` + `territory_place`, keyed on `manual_edition` (Rules) not `lc_edition`; `TERRITORY.SCHEME` state variable |
| `07-ENGINE-ARCHITECTURE.md` | STEP C territory resolution expanded to the three schemes with an explicit unmatched→referral path |
| `08-INGESTION-SPEC.md` | New `Territory pages` segment; new **§8.5.8** parser (scheme detection, ZIP grammar, leader-dot city grammar); assertions **V22, V23** |
| `10-BUILD-BACKLOG.md` | New task **3A.9**; task 6.2 de-stubbed; sizing note corrected |
| `11-RATING-ARCHITECTURE.md` | §11.11 — territory now supplied; posture upgraded to priceable in all 51 |
| `13-LOSS-COSTS-AND-ELP.md` | §13.1 G2 row, §13.8 territory model (332 included; three schemes; cross-validation), §13.11 |
| `00-OVERVIEW.md`, `README.md` | Scope tables, scope boundary, headline numbers |
| `A4-LOSS-COST-INVENTORY.md` | New **§A4.3** — per-jurisdiction territory scheme, `CG-T` page count, row counts, match result |
| `dataset.json`, `index.html` | New `territory_definitions` block; new visualization section 14 (three schemes); render re-verified headlessly |

### Findings

- **All 51 jurisdictions carry Territory Pages.** `CG-T-1` always assigns OCP/Railroad
  Protective (335), Pollution (350) and Products/Completed Operations (336) to
  `ENTIRE STATE … 999`, then defines territories for **Premises and Operations (334) and
  Liquor Liability (332)**.
- **Three resolution schemes, not one:** ZIP table (**27** jurisdictions, 23,719 rows),
  county/city (**4** — CA, FL, NY, TX, 432 rows), entire state (**20**).
- **The A-rule marks the ZIP scheme, not territory rating.** The 27 A-rule jurisdictions are
  *exactly* the 27 with ZIP tables. That explains the Step 7 anomaly — CA, FL, NY and TX are
  territory-rated with no A-rule because they use the older county/city scheme.
- **Territory applies to Liquor Liability (332) as well as 334.** The rate pages could not show
  this, because there are no liquor loss cost pages; it is visible only on the `CG-T` pages.
- **Cross-corpus agreement is exact: 51 of 51, zero mismatches** between the `CG-T` territory
  codes and the territories published on the loss cost grids. Two corpora on separate release
  cycles, parsed by different code paths — the only external oracle in the project, now
  captured as assertion V22.
- **The county/city scheme is the harder engineering problem** despite being 55× smaller: its
  key is `(county, place_name)` against 1996–2008 vintage place lists, so it needs a distinct
  resolver with an explicit referral path rather than a silent nearest-name match.

### Consequence for the build

**G1, G2 and G3 are all closed.** For Premises/Operations and Products/Completed Operations the
engine is priceable in **all 51 jurisdictions** with nothing external required but the carrier's
own loss cost multiplier. The backlog's Phase 6 drops from four stubs to three.

### Open items raised (not resolved in this step)

- The county/city place lists carry edition dates as old as `1st Edition 5-97`. Whether ISO
  still maintains them, and how a modern address geocodes onto a 1997 place list, is a question
  for the business rather than the documents.
- **Q7** (no class-code crosswalk for the 2027 revision), **Q8** (OCP withdrawal permanent or
  transitional), **G4**, **G6**, **G9** and **L4** are unchanged from Step 7.

---

## Step 9 — Build the ISO Circular Expert agent

- **Date:** 2026-08-10
- **Directed:** "Take all of these ingested files, from `Commercial Line Manuals\GL` and create
  an agent in `C:\Projects\Recursive_Harness_2.0\Agentic` that is an ISO circular expert. This
  will be used as part of our recursive reviews when testing the rating engine that we are
  creating and implementing fixes in an automated manner."

### Thought process

An agent that only holds a system prompt would have to re-read 975 PDFs to answer anything,
and at ~1 minute per large PDF that is not usable inside a review loop. The expertise had to
be made **resident and queryable**, so the build has three layers:

1. **Corpus text**, page-tagged, extracted once — so the agent can quote the manual verbatim
   with a page citation rather than paraphrase it.
2. **A structured knowledge base** — the facts that took hours to compute across Steps 4–8
   (territory schemes, rate vintages, circular graph, date confidence), so they are looked up
   in milliseconds rather than rediscovered.
3. **A retrieval CLI**, because a prompt telling an agent to "grep the corpus" produces
   inconsistent searches. A subcommand produces the same answer every time and is testable.

Two design decisions worth recording:

- **`pypdf` for everything, not `pdftotext`.** Established at Step 7: on the loss cost grids
  `-layout` silently misaligns rows, and every resulting number is a plausible loss cost. An
  agent quoting a corrupted rate with a confident citation is worse than one that cannot
  answer, so the extractor choice is baked in rather than left to the agent.
- **The output contract admits `UNVERIFIABLE`.** Downstream automation acts on this agent's
  findings. Four inputs are genuinely outside both corpora, and an agent that guesses at them
  produces a wrong code change rather than an open question.

The agent's operating protocol also carries the **Step 8 error** as a standing correction —
a negative result must name the corpus and pattern searched. That failure survived a full
specification pass and was caught by a human pointing at a page number; encoding it as a rule
is cheaper than re-learning it.

### Action

1. **Extracted the Rules corpus to page-tagged text** with `pypdf` (503 PDFs, parallel;
   502 succeeded, `GL-MO-2027-RU-003-C` truncated) and copied the loss cost text from Step 7.
2. **Built the knowledge base** from the verified analyses of Steps 4–8 plus the ERC workbook.
3. **Hand-authored `invariants.json`** — 32 invariants, each with severity, corpus evidence,
   a concrete check and a spec reference. This is the review checklist, not style guidance.
4. **Wrote `tools/iso.py`** — 11 subcommands over the corpus and knowledge base.
5. **Wrote `AGENT.md`** — role, the four epistemic states, the failure modes that actually
   occur in this program, and the JSON output contract.
6. **Registered it** as a Claude Code subagent with repo-root-relative paths.
7. **Wrote and ran `smoke_test.py`** — 15 cases, each asserting a fact independently verified
   against the source PDFs. **15/15 pass.**

### Result — `Agentic\iso-circular-expert\`

| Path | Contents |
|---|---|
| `AGENT.md` | Agent definition: corpora, tool usage, evidence discipline, review order, failure modes, JSON output contract, boundaries |
| `README.md` | Quick start, worked examples, why the invariants matter, known limits |
| `knowledge/invariants.json` | **32 invariants** — 17 BLOCKER, 10 MAJOR, 5 MINOR |
| `knowledge/jurisdictions.json` | 51 profiles: latest notices, territory scheme + domain, rate vintage, payroll shape, liquor grade, ILF inventory, deviation map |
| `knowledge/circulars.json` | 727 circulars → description, type, filings, ERC editions, states |
| `knowledge/notices.json` | 974 notices → circulars, filings, ERC edition, effective date, date confidence |
| `text/rules/` | 503 page-tagged notices (502 readable; `GL-MO-2027-RU-003` truncated) |
| `text/losscosts/` | 472 page-tagged notices (471 readable; `GL-MI-2027-LC-003` truncated) |
| `tools/iso.py` | `circular · notice · state · rule · grep · page · territory · rate · invariant · effective` |
| `tools/smoke_test.py` | 15 regression cases |
| `.claude/agents/iso-circular-expert.md` | Registered subagent (repo-root paths) |

**98 MB total**, no third-party dependencies at query time.

### Verified capabilities

| Query | Result |
|---|---|
| `territory NJ --zip 07030` | HOBOKEN → territory **504**, cited `GL-NJ-2027-RU-001 p.28` |
| `territory CA --zip 90001` | Correctly **refuses** — CA is `COUNTY_CITY`, needs county + place |
| `rate TX --class 10010` | 8 territory rows; terr 001 = `.188` / `.142`, flagged pre-LCM |
| `rate TX --class 91581` | `(a)` decoded as **REFER**, never zero |
| `grep "increased limits tables are displayed"` | `GL-MU-2022-RU-001 p.79`, verbatim |
| `rule 45 --st TX` | Texas Liquor exception text with mandatory endorsements |
| `effective NJ --date 2026-06-01` | Both streams resolved independently, with a three-streams warning |

### Findings from building it

- **The knowledge base is only as good as its provenance fields.** `date_confidence` had to be
  surfaced on every notice lookup, because 264 rules and 57 loss cost notices are dated by
  proximity — an agent that cites an effective date without that qualifier is overstating.
- **Refusal has to be a first-class result.** The `COUNTY_CITY` ZIP case is the clearest
  example: the honest answer is "this jurisdiction does not resolve by ZIP", and a helpful-
  seeming fallback would silently mis-rate CA, FL, NY and TX.
- **Whitespace normalisation had to be pushed into the tool contract** (`--squash`), not left
  to the agent's discretion. `pypdf` splits words, and in this domain a false negative reads as
  *"the manual is silent"* — the exact error class the agent exists to prevent.

### Open items raised (not resolved in this step)

- The agent reads rate cells out of page text on demand. The ~429,700 grid cells are still not
  loaded into a database — **Phase 3A** of the backlog — so bulk rate queries are slow.
- No adversarial evaluation set yet: the smoke test proves retrieval works, not that the agent
  reaches the right verdict on a deliberately wrong premium. A fixture set of known-bad engine
  outputs with expected findings is the natural next step for the recursive loop.
- `invariants.json` is hand-maintained. It should gain a test that re-derives each invariant's
  evidence from the corpora, so drift fails loudly rather than silently.

---

## Step 10 — Plain-English build plan (PDF-only scope)

- **Date:** 2026-08-10
- **Directed:** "Create a document that is plain english, and explain how you will take all of
  these learnings and apply them to the build an ISO GL Rating Engine, that can be scaled to
  include additional lines of business. This should be focused on the PDF manuals only, with no
  ERC context. Without an ERC review, include expectations on how you anticipate building off
  of ERC will differ."

### Thought process

The PDF-only constraint was not cosmetic. The specification written in Steps 4–8 takes
effective dates **from the ERC circular metadata** — that is stated as a hard requirement in
`01-SOURCE-CORPUS.md` §1.4 and enforced as assertion V12. Strip ERC out and the plan has a hole
exactly where dating sits. So before writing a word, the question had to be settled: *can a
notice be dated from the PDF alone?*

It can, mostly. The cover page prints `Circular Reference(s): LI-GL-2026-135 (05/22/2026)`.
Measured across the corpus: **485 of 502** rules notices and **452 of 471** loss cost notices
carry a dated circular — about **96%**. Combined with sortable notice numbers and the
already-established fact that notices are full reissues, that supports a defensible per-
jurisdiction timeline with no ERC at all.

The honest qualifier, which the document leads with rather than buries: the printed date is the
circular's **issue** date, not the manual's **effective** date. PDF-only dating therefore gives
reliable *ordering* and a *lower bound*, not the exact boundary. That is the single largest
quality gap in a PDF-only build, and it is narrow and well understood rather than blocking.

### Action

1. **Tested the PDF-only dating hypothesis** before drafting — the document's central claim
   depended on it.
2. **Found and fixed two real bugs** in the agent's tooling while measuring (below).
3. **Added `iso.py dating`** so the PDF-only path is executable, not theoretical.
4. **Wrote the document** in plain English — no jargon without definition, every number
   measured rather than asserted.
5. **Contained ERC to §8**, explicitly labelled as expectation, and verified containment: the
   only ERC mentions outside it are the scope statement itself and the §4.5 heading.

### Result — `docs\BUILD-PLAN-PLAIN-ENGLISH.md`

~3,900 words, ten sections:

| § | Contents |
|---|---|
| 1–2 | What a rating engine is, what we hold, why this manual is harder than it looks |
| 3 | **The five learnings that changed the plan** — no national rates, rule numbers aren't identities, a third of cells aren't numbers, the live 15/36 migration, coverages with no published rate |
| 4 | **How we build** — compose don't inherit; numbers in data; the extraction lesson; import validation; **dating without ERC**; differential testing |
| 5 | What already exists (spec, corpus, agent, 32 invariants) |
| 6 | **Scaling to other lines** — what transfers, what differs, sequencing, and a cost expectation |
| 7 | The four genuine external dependencies, stated plainly |
| 8 | **How an ERC build would differ** — labelled expectation, not finding |
| 9 | Risk table, ranked by consequence |
| 10 | One-paragraph summary |

Linked from `docs/rating-engine/README.md`.

### Findings

- **PDF-only dating is viable at ~96% coverage**, and its weakness is precise: ordering is
  reliable, the exact effective date is not. This reframes ERC from "needed to build" to
  "would close a known, narrow gap" — a materially different procurement question.
- **Two tooling bugs surfaced while measuring**, both instances of defects already documented
  in this project:
  - `pypdf` renders `LI -GL -2019 -216` with injected spaces, so a literal circular pattern
    missed **189 loss cost notices** — the exact failure mode recorded as `INV-WHITESPACE-NORM`,
    reappearing in new code. Fixed with space-tolerant patterns.
  - The filing-reference extractor matched the filing-shaped substring *inside* a circular
    number (`LI-GL-2019-216` → `GL-2019-216`) — the same false positive found and fixed at
    Step 6, reintroduced. Fixed by anchoring to the `Filing Reference(s)` label.
- **Both bugs were in code I wrote one step earlier, with the defect documented.** Written
  guidance did not prevent recurrence; the arithmetic check did. That is an argument for
  automated gates over documentation, and it is now the closing point of §9.
- **Most learnings are about how ISO publishes, not about GL.** The architecture, failure modes
  and validation strategy transfer to other lines; the class lists, coverages and rating shapes
  do not. Hence the estimate that line two costs ~40–50% of line one, and the caution against
  generalising the framework before a second real line exists.

### Open items raised (not resolved in this step)

- The 40–50% figure for line two is an **estimate from structural similarity**, not from
  having ported a line. It should be revisited once one has been.
- No ERC evaluation has been done. §8 is expectation throughout and is labelled as such; the
  recommendation is to evaluate ERC in parallel against dating and rate-table delivery
  specifically, without delaying the PDF-based build.
- `iso.py dating` reports the circular issue date but does not yet attempt to derive an
  effective-date *range* per notice. That is the natural next increment if the PDF-only path
  is chosen.

---

## Step 11 — Log audit, and preserving the work that produced the numbers

- **Date:** 2026-08-10
- **Directed:** "Ok, make sure we log all of this."

### What the audit found

Steps 6–10 were each logged as they were completed, so the narrative was intact. Auditing the
log **against the artifacts on disk** surfaced one real problem and one honest gap.

**The problem: none of the analysis was reproducible.** Every number in
`docs/rating-engine/`, every row of `GL_LossCost_to_ERC.xlsx` and every file in the agent's
knowledge base was produced by scripts living in a **session-specific temporary directory**
that is deleted when the session ends. The log named the outputs but not the means of
regenerating them. Worse, `Agentic/iso-circular-expert/README.md` asserted the build scripts
*"live with the analysis in `docs/rating-engine/`"* — which was simply false.

That combination is the failure this project has already been bitten by twice: a confident
statement that nobody checked. Left alone, the next person to touch this would find 98 MB of
knowledge base, ~4,000 words of build plan and a 14-document specification, with no way to
re-derive any of it or to verify a single figure.

### Action

1. **Preserved 13 scripts** into `scripts\`, renumbered in pipeline order, covering extraction
   → analysis → crosswalk → reporting → dataset → agent knowledge base.
2. **Wrote `scripts\README.md`** — the pipeline order, what each script produces, the two
   silent extraction defects the scripts exist to prevent, which intermediates are large and
   regenerable, and the dependency list.
3. **Corrected the false claim** in the agent README and replaced it with the actual rebuild
   sequence, ending in the smoke test.
4. **Audited every artifact named in this log** for existence, and every headline number
   against the files that hold it.

### Result

| Path | Contents |
|---|---|
| `scripts\01_probe_extractor.py` | Which loss cost PDFs `pdftotext` can read — the evidence for the 389/83 split |
| `scripts\02_extract_dualmode_losscosts.py` | Both `pdftotext` modes; kept solely to reproduce the misalignment comparison |
| `scripts\03_extract_pypdf_losscosts.py` · `04_extract_pypdf_rules.py` | The authoritative page-tagged text for both corpora |
| `scripts\05_analyze_losscosts.py` | Per-notice structure, cell vocabulary, territories, class codes |
| `scripts\06_scan_territory.py` | Territory Pages across all 503 rules PDFs |
| `scripts\07_match_losscost_to_erc.py` · `08_build_losscost_workbook.py` | The Step 6 crosswalk and workbook |
| `scripts\09_report_losscosts.py` · `10_report_territory.py` | The roll-ups behind docs 13 and 05 |
| `scripts\11_build_dataset.py` · `12_build_agent_kb.py` | `dataset.json` and the agent knowledge base |
| `scripts\verify_index_html.js` | Headless render check for the visualization |
| `scripts\README.md` | Pipeline documentation |

### Audit results — every headline number re-verified against the files

| Claim in this log | On disk | ✔ |
|---|---|---|
| 32 invariants — 17 BLOCKER, 10 MAJOR, 5 MINOR | 32 — 17/10/5 | ✔ |
| 51 jurisdictions · 974 notices · 727 circulars | 51 · 974 · 727 | ✔ |
| 503 rules + 472 loss cost text files | 503 + 472 | ✔ |
| Rate vintage split 15 pre-2027 / 36 on the 2027 basis | 15 / 36 | ✔ |
| Territory schemes 27 ZIP / 4 county-city / 20 statewide | 27 / 4 / 20 | ✔ |
| Agent smoke test 15/15 | 15/15 passing | ✔ |
| Every artifact named in Steps 6–11 exists | all present | ✔ |

### The honest gap

**Three Step 5 scripts are gone.** `anatomy.py`, `catalog.py` and `gen_a3.py` produced
`A3-ENDORSEMENT-CATALOG.md` — 328 forms across 447 placements — in a prior session, and were
never persisted. The catalog itself is intact and sourced, but **it cannot currently be
regenerated**, and its figures cannot be independently re-derived without rewriting the
extraction.

This is recorded rather than quietly dropped. It is also the clearest possible argument for
Step 11 existing at all: the same thing would have happened to Steps 6–10 had the temporary
directory been cleared first.

### Findings

- **A log that records outputs is not the same as a reproducible record.** Steps 6–10 were
  logged in detail — actions, results, findings, open items — and were still not reproducible,
  because the means of production lived outside the repository. Provenance has to include the
  code, not just the conclusions.
- **The README error was the same class of defect as the Step 8 territory error**: an assertion
  about where something lives, written from assumption, never checked. Both were cheap to
  verify and neither was verified until something forced it.
- **The endorsement-catalog gap was invisible until the artifacts were checked against the
  log.** Reading the log alone gives no hint those scripts are missing.

### Open items raised (not resolved in this step)

- `A3-ENDORSEMENT-CATALOG.md` cannot be regenerated. If its numbers ever need re-verification,
  the extraction must be rewritten from the CW notices.
- The `scripts\` intermediates (`lc_pypdf/`, `lc_text/`, `lc_layout/`, ~200 MB) are regenerable
  and should be excluded from version control; no `.gitignore` exists yet because the project
  is not a git repository.
- Scripts 01–12 resolve paths relative to their own location, so running them in place writes
  intermediates into `scripts\`. Functional, and documented, but a working-directory argument
  would be cleaner if they are run regularly.

---

## Step 12 — Root README

- **Date:** 2026-08-10
- **Directed:** "yes, create one" — a root `README.md` orienting a newcomer to the repository,
  offered at the end of Step 11.

### Thought process

`PROCESS_LOG.md` is a complete record but reads **chronologically**, which is the wrong shape
for someone arriving cold: they have to read eleven steps to learn what the project is. The
README is a **map**, not a re-telling — it routes by *what the reader needs*, states the four
findings that determine the build, and is explicit about what is absent.

Two judgements:

- **Lead with what is not here.** Four external dependencies, Hawaii, two corrupt files, and
  unloaded rate cells all belong above the fold, not in an appendix. A reader who takes this
  project as complete and finds those later has been misled by omission.
- **Carry the two corrections forward.** The Step 8 territory error and the Step 11
  reproducibility gap are in the README, not buried in the log. They are the evidence for why
  the validation strategy is built on automated gates rather than review.

### Action

1. Wrote `README.md` — routing table, repository map, corpus figures, the four load-bearing
   findings, agent quick start, absences, working notes, and how the work proceeded.
2. **Verified every checkable claim mechanically** rather than transcribing from memory.
3. Corrected one figure caught by that check: the specification is **14 documents + 4
   appendices** (19 files including the index), not 15 + 4.

### Result — `README.md` (~1,270 words)

| Section | Purpose |
|---|---|
| Start here | Routes by reader need — new · building · checking a premium · tracing a number · re-deriving |
| What's here | Annotated tree of corpora, docs, agent, scripts, workbooks |
| The corpora | Counts, jurisdictions, years, the zero countrywide rate notices, the two corrupt files |
| Findings that shape the build | The four that would have broken the engine if assumed otherwise |
| The agent | Quick start with real commands |
| What is not here | Four external dependencies, Hawaii, unloaded rate cells |
| Working notes | Extraction hazards, not a git repo, the known reproducibility gap |
| How the work proceeded | The two corrections, and why validation leans on automated gates |

### Verification

| Claim | Checked against | ✔ |
|---|---|---|
| 503 rules / 472 loss cost PDFs | the corpus directories | ✔ |
| 32 invariants · 51 jurisdictions · 727 circulars · 974 notices | the agent knowledge base | ✔ |
| 15/36 rate vintage split | `jurisdictions.json` | ✔ |
| 14 documents + 4 appendices | `docs/rating-engine/` | ✔ (corrected from 15) |
| 13 scripts | `scripts/` | ✔ |
| All internal links resolve | filesystem | ✔ — none broken |

### Findings

- **Writing the map exposed a stale count.** "15 documents" came from counting files rather
  than documents. Mechanically checking every figure in a summary document is cheap and caught
  it — the same discipline that Steps 8 and 11 established after it was skipped.
- **The chronological log and the map serve different readers, and both are needed.** The log
  answers *"why is this number what it is"*; the README answers *"what is this and where do I
  start"*. Neither substitutes for the other.

### Open items raised (not resolved in this step)

- None new. The open items from Steps 9–11 stand: no adversarial evaluation set for the agent,
  `invariants.json` has no drift test, `A3-ENDORSEMENT-CATALOG.md` is not regenerable, and the
  ~429,700 rate cells are specified but not loaded.

---

## Step 13 — Ingest the GL ERC corpus, clean-room

- **Date:** 2026-08-10
- **Directed:** "Ingest all of the GL ERC Files from `C:\Projects\ISO_ERC_Files\General_Liability`
  and do the same work that was done for the CLM Manuals for ERC, **without using any knowledge
  gained from the PDF files**. Before starting, list back to me the work that you think you
  should be completing for these ERC's."

### Thought process — the clean-room problem

The constraint could not be honoured by promising to be careful. The PDF findings were already
in the assistant's context; deriving ERC personally would mean unconsciously searching for
confirmations, and any agreement between the two would then be worthless as validation.

Presented the scope first, as directed, and surfaced the tension explicitly. The user chose
**isolation via a fresh subagent**, staging at inventory, with a comparison to follow.

That made **the dispatch prompt the contamination vector.** It named no expected finding, and
explicitly fenced off `docs/`, `Agentic/`, the process log, the PDF corpus, and the two
ERC-derived spreadsheets sitting in the ERC folder — the second of which is explicitly a bridge
to the PDFs.

### Action

1. **Unpacked mechanically** (assistant, no interpretation): 508 archives, **zero corrupt**,
   64,070 members. Measured the raw corpus at 87,258 files / 988 MB.
2. **Dispatched an isolated agent** for inventory, schema discovery and extraction.
3. **Staged at inventory**, reported, and agreed scope before proceeding — three further rounds:
   open questions, structural analysis, then specification + agent.

### Result

| Round | Deliverable |
|---|---|
| 1 | `docs\erc\01-CORPUS-AND-SCHEMA.md` — inventory, content model, extraction |
| 2 | `docs\erc\02-EDITIONS-AND-INTEGRITY.md` — edition semantics, `Status`, anomalies, self-description |
| 3 | `docs\erc\03-RATING-STRUCTURE.md` — composition, coverage, rating structure, variation, territory, rule program |
| 4 | `docs\erc\04-BUILD-SCOPE-AND-RESOLVER.md`, `05-DATA-MODEL-AND-INGESTION.md`, `06-VALIDATION-AND-BACKLOG.md` |
| 4 | `Agentic\iso-erc-expert\` — 26 invariants (12 BLOCKER), retrieval CLI, **83/83 smoke checks** |
| — | `scripts\erc\` — 24 numbered scripts, reproducible |

### Key findings

- **Editions are cumulative snapshots**, not deltas — 92.7–98.3% carry-over across 515
  consecutive pairs. And **600 of 600 "dropped" state tables still exist countrywide**: nothing
  is ever retired, only overrides are withdrawn.
- **The composition tag is exact.** 100.0% of 23,404 `Overridden` rules shadow a same-named
  countrywide rule; 0.0% of 23,755 `StateSpecific` do. Zero exceptions either way.
- **`RunRule@ProjectName` must bypass the overlay** or 4,598 call-super rules recurse forever.
- **90.7% of the content does not rate.** 381 of 420 premium-writing tables capture a
  user-entered `ManualPremium`; only 19 compute a premium from rates.
- **The corpus is 100% self-describing** — XSD `targetNamespace` yields the full identity triple
  for 567/567 packages. This closed the PDF build's single largest defect (264 notices dated by
  positional guess).
- **Only 27 of 52 jurisdictions ship a ZIP→territory map**, and `ProdsCompldOpsTerr` has exactly
  one value corpus-wide.

### Corrections the agent made to itself

Both are recorded because they are evidence the isolation worked:

- It **falsified** its own `Status` A/C/D hypotheses rather than confirming them — `D` is
  absorbing but does not remove rows (86.6–98.5% survive). The tombstone risk flagged in round 1
  was real but pointed the wrong way.
- It **overturned** its round-1 conclusion that the corpus was not self-describing, having
  wrongly generalised from `Metadata/` being silent to the package being silent.

### Source-data remediation (performed by the assistant, not the agent)

Two packages were misfiled **including their `.zip`s**, so the defect originated upstream at ISO.
On the user's instruction:

- `GL_PR 20270401 V02` moved `RI/` → `PR/`. This was the only anomaly producing *silent wrong
  answers*: PR's newest edition existed nowhere else.
- The `GL_DE 20260101 V01` stray under `GA/` was **quarantined, not deleted** — `DE/` already
  held a byte-identical copy (independently re-verified, tree hash `7041c4fc…`, 82 files,
  500,672 bytes). Moving it would have collided; deleting is irreversible.

Verified end-to-end afterwards: `erc.py asof PR 2027-06-01` now resolves `GL_PR_20270401_V02`.

---

## Step 14 — Cross-derivation comparison

- **Date:** 2026-08-10
- **Directed:** (agreed at Step 13 outset) compare the ERC findings against the PDF findings once
  the ERC side was frozen. The user chose **a fresh agent given both**, since the comparison
  necessarily sees both sides and so cannot be the isolated agent.

### Action

Dispatched a third agent with no stake in either derivation, told explicitly that the two are
**not symmetrically independent**, that both contain self-documented errors, and that it could
read either corpus to adjudicate. Warned specifically against false agreements — two
similar-sounding claims that are not the same claim.

### Result — `docs\COMPARISON-ERC-VS-PDF.md` (6,476 words)

**Agreements now resting on two independent derivations:** the countrywide layer holds the
algorithm and none of the money; the 27 ZIP-table jurisdictions are set-identical; territory
counts match as a complete histogram; 1,163/1,188 class codes with a 229-retired/204-new
revision; countrywide factor tables match digit-for-digit; Liquor and Railroad Protective have no
base rate anywhere; Hawaii absent from both.

**Corrections in both directions.** Against ERC: its "universally overridden ILF tables" claim
classified by table *name* without measuring *population* — **138 of 272 countrywide rate tables
are empty stubs** (assistant verified: all five key rating tables at 0 rows). Against the PDFs:
the class-code revision is a **countrywide** change states adopt by import, not the
state-by-state filing described; the 15/36 vintage split was a snapshot artifact.

**Found by neither derivation:** ERC encodes refer-to-company as **`0`** — the drone table's
>55 lb band is `0` where the manual says *Refer To Company*, so a naive multiply yields a **$0
premium** on exactly the risks that must be referred (assistant verified directly). Also: ERC's
ILF tables carry **no interpolation machinery**, so an ERC-only build cannot rate an off-table
limit; and CA/NJ/NY/OH shard loss costs per territory, NY shipping an empty shadow table that a
name-based resolver would overlay to nothing.

**Build recommendation:** ERC as execution substrate; the PDFs load-bearing in four defined roles
(semantic dictionary, eligibility, verification, provenance). The cross-checks that agreed should
become CI gates.

---

## Step 15 — Open-items register

- **Date:** 2026-08-10
- **Directed:** "Save these open items, and add Composite Rating, Schedule Rating, and Experience
  Rating. For now, don't fold everything into anything."

### Action

Created a **standalone** register; deliberately did not modify either specification (verified by
mtime). Before writing, tested what each source actually holds for the three named plans rather
than assuming the existing gap register was current.

### Result — `docs\OPEN-ITEMS.md`, 27 items

`OPEN` 16 · `PARTIAL` 5 · `AUDIT` 4 · `BY-DESIGN` 2 · `HYGIENE` 5. Every entry names the
derivation it came from; every verification states the scope it covered.

### The finding that checking produced

**PDF gap G6 — "CGLES / Composite Rating / Size-Of-Risk plans … modification factors
unavailable" — is substantially wrong as a statement about this project's holdings.** ERC carries
populated content for all of them in CW 20270401:

| Plan | Content found |
|---|---|
| Schedule Rating | 8 `DomainScheduleRatingModification*Pct` tables (21/21/21/13/11/11/5/5 rows) + max credit/debit |
| Experience Rating | `ExpectedExperienceRatio` 99 rows; mod factor is a per-risk input, not a table |
| Composite Rating | `GeneralLiabilityCompositeRatingRules.Rule.xml` + exposure indicator 54 rows |
| Size-Of-Risk | `PremOpsSizeOfRiskRelativity` **8,330 rows**; `ProdsCompldOps…` **4,214 rows** |

Also: **terrorism is not absent from both** — 64 files in CW 20270401 — so the comparison's "open
in both" is wrong for ERC (marked `AUDIT`, pending a population sweep). And **LCM is confirmed
by-design rather than missing**: `LCM.RateTable.csv` exists at 0 rows, which is what a
carrier-supplied input looks like structurally.

G6 was accurate about the PDF corpus and was never re-tested once ERC arrived. **This is the third
instance in this project of a gap established against one source and stated as a general fact**,
after the territory error (Step 8) and the reproducibility gap (Step 11). The register carries a
source tag on every entry and a scope statement on every verification specifically to stop a
fourth.

**Scope caveat, recorded prominently:** every check above ran against a **single countrywide
edition** plus one NJ package. Existence proofs, not inventories.

---

## Step 16 — Python build plan for the rating engine

- **Date:** 2026-08-10
- **Directed:** "Create another document which would include this PDF and ERC analysis, and would
  detail a full blown plan to build this GL Rating Engine in Python… no UI required… a fully
  blown out rater, with all sublines and coverages included, but we can build one subline at a
  time, with you presenting to me the algorithms for each subline as it's built, and any state
  specific deviations… must follow the context of Countrywide Bases with State Specific Children,
  hierarchy… so that the effective date of the policy being rated calls the property State and CW
  ERC versions… built as recursive harness, and will eventually be tested against an integrated
  RAaS call."

### Result — `docs\GL-RATING-ENGINE-BUILD-PLAN.md`

Ten sections: source roles · twelve non-negotiables · architecture · the recursive harness ·
subline build order · the per-subline presentation gate · data layer · testing · phasing ·
carried-in limits.

### Design decisions worth recording

- **The typed cell is the load-bearing type.** `Cell` has no path from a `NOT_OFFERED` or
  `REFER` disposition to a number — enforced by type, not discipline. This is what a naive loader
  gets wrong, and it is the difference between a referral and a free policy.
- **`ResolvedBook` keeps both layers addressable** rather than flattening the overlay, because
  `RunRule@ProjectName` must dispatch to the parent. A merged book is not merely lossy — it is
  non-terminating.
- **Rounding becomes a pluggable policy with an `attested` flag on every trace entry**, turning
  the top unresolved blocker into the first thing RAaS testing settles rather than a reason to
  delay.
- **The RAaS seam is built now against a `NullOracle`**, so the eventual integration is
  configuration rather than construction.
- **The harness lands at Phase 5**, after one subline — deliberately early, so there is something
  to audit while the loop is still cheap to change.
- **The honest ceiling is stated in the plan itself:** 90.7% of ERC tables capture rather than
  rate. The engine rates the 19 that rate and refers the rest.

### Open items raised (not resolved in this step)

- Nothing new. The plan carries `OPEN-ITEMS.md` forward by reference and names the specific OI
  numbers that gate individual phases (OI-01…04 and OI-08 gate the terrorism and rating-plan
  phases; OI-09 and OI-14 are deferred to RAaS; OI-15 makes 21 jurisdictions refer rather than
  rate; OI-17 needs a corpus-wide sweep before any `0` multiplier is trusted).

---

## Step 17 — Plain-language PRD

- **Date:** 2026-08-10
- **Directed:** "Create a laymens PRD type document with the steps we have taken to get to this
  point."

### Thought process

Four documents already existed that a stakeholder might be handed, and none did this job.
`BUILD-PLAN-PLAIN-ENGLISH.md` is accessible but was written before the ERC work and is scoped to
the PDFs alone. `GL-RATING-ENGINE-BUILD-PLAN.md` is the technical plan. `PROCESS_LOG.md` is
chronological but dense. `README.md` is a map. What was missing was **the narrative plus the
product definition, for someone with no insurance and no technical background.**

Two judgements shaped it:

- **Lead the journey with the corrections, not around them.** Three assertions in this project
  turned out to be wrong, and two were caught by the user pointing at a specific page or file. A
  progress document that omits those reads as marketing. Stage three of the narrative is the
  territory error, and §9 is about the pattern itself.
- **Put the ceiling in its own section.** 90.7% of the ERC pricing tables capture rather than
  calculate. A sponsor reading a document titled "rating engine" will assume end-to-end
  automation. Better to state the constraint plainly under its own heading than to let it surface
  at phase 14.

### Result — `docs\PRD-GL-RATING-ENGINE.md` (~2,700 words)

Nine sections: what we're building · why it's hard · **how we got here** (16 steps in five
narrative stages) · requirements, non-goals and the honest ceiling · how we'll know it works ·
delivery plan with the per-coverage review gate · risks in plain terms · where we stand · a note
on how the project has worked.

Written for a reader with no prior knowledge: ISO, loss cost, refer-to-company, the three-layer
structure and the edition problem are all defined on first use.

The `0`-means-refer finding is used as the concrete illustration of why two sources were worth
the effort — a data file that says `0` where the manual says *refer* would price those drone
policies at $0.00, and neither source reveals it alone.

`README.md` re-routed: the PRD is now the entry point for a new reader, with the earlier
plain-English document retained and labelled as the pre-ERC overview.

### Findings

- **The document set had grown past the point where one "plain English" entry point served.**
  Adding the PRD meant demoting `BUILD-PLAN-PLAIN-ENGLISH.md` to "the earlier overview" rather
  than deleting it — it is still accurate within its stated PDF-only scope, and the PRD says so.

### Open items raised (not resolved in this step)

- None new. The PRD carries `OPEN-ITEMS.md` forward by reference rather than restating it, so the
  27 items have a single home.

---

## Step 18 — Territory resolved: the gap was never real

- **Date:** 2026-08-10
- **Directed:** "For the territories, many states either default to 001 or 002, with no zip code
  look up. That's probably what's happening. Confirm, and log."

### The hypothesis, and why it mattered

Three documents asserted that jurisdictions lacking a ZIP→territory table could not determine
territory, and the build plan had **21 jurisdictions referring rather than rating** as a result.
The user proposed that those states are simply **single-territory** — everything defaults to `001`
or `002`, so no lookup exists because none is needed.

This also cut across a live divergence: `[PDF]` had found 20 `ENTIRE_STATE` jurisdictions, while
`[ERC]` reported *"all 52 jurisdictions are multi-territory once resolved, minimum 4."* Both could
not be right.

### Action

Tested directly against the corpus — latest package per jurisdiction: ZIP-map presence and row
count; distinct values in every territory-bearing rate-table column; and the territory domain
tables for the jurisdictions with neither.

### Result — hypothesis confirmed, including the "or 002"

**All 51 jurisdictions resolve territory from ERC. Three schemes:**

| Scheme | Count | Mechanism |
|---|---|---|
| ZIP table | **27** | `DomainTerritoryCodeByZipCode`, 93 rows (RI) – 2,174 (PA) |
| **Single territory** | **20** | No lookup exists because none is needed |
| County / place name | **4** — CA, FL, NY, TX | Place-name domain tables |

The 20 single-territory jurisdictions — AK, AR, DC, DE, ID, ME, MS, MT, NC, ND, NH, NM, NV, PR,
SC, SD, UT, VT, WV, WY — carry exactly one Premises/Operations territory across all 1,163–1,188
class codes. **19 use `001`; NC uses `002`** — the single exception, and precisely the "001 or
002" predicted. All use `999` for Products/Completed Operations. AR expresses it through
`DomainPremisesOperationsTerr` (one row, `001`) rather than a column, but resolves identically.

**CA, FL, NY and TX carry their definitions in ERC after all**, as place-name domain tables rather
than ZIP tables — CA 11 codes / 21 place names, FL 5 / 8, NY 20 / 66, TX 8 / 15, with entries like
`Houston Within Harris County` and `Westchester County South`.

### Three claims corrected

- `[ERC]` *"all 52 multi-territory, minimum 4"* — **wrong**; 20 have exactly one.
- `[CMP]` and `OPEN-ITEMS.md` *"21 jurisdictions cannot determine territory"* — **wrong**; zero cannot.
- `[PDF]` the manual supplies CA/FL/NY/TX county/city — true, but ERC has them too, so the
  cross-source dependency assumed here does not exist.

**OI-15 closed.** What remains is not a data gap but an input requirement: those 4 jurisdictions
key on county/place, so the engine must resolve a risk address to a county or place name. Logged
as **OI-34** at far lower severity. An ID collision with a concurrently-added `OI-28` was detected
and my entry renumbered.

### Findings

- **This is the fourth time a gap was asserted and later found not to exist**, after the territory
  definitions (Step 8), reproducibility (Step 11) and the rating plans (Step 15). The shape is
  identical every time: **absence of the expected mechanism read as absence of the capability.**
  "No ZIP table" meant "needs no ZIP table," and nobody checked what those states actually
  contained.
- **Isolation does not protect against this.** The ERC derivation was clean-room, rigorous, and
  still got it wrong — because it measured territory codes wherever they appeared rather than
  asking what a state's *own* Prem/Ops territory domain contained. Independence guards against
  shared assumptions, not against an unasked question.
- **A domain expert saying the obvious thing out loud beat four rounds of automated analysis.**
  Worth remembering when weighting the recursive harness against human review.

### Open items raised (not resolved in this step)

- `docs\GL-RATING-ENGINE-BUILD-PLAN.md` §7 and §10 still state that **21 jurisdictions refer
  rather than rate**. That is now known to be wrong and should read: 51 resolve, 4 of them
  requiring county/place resolution of the address. **Left uncorrected pending direction**, per
  the standing instruction not to fold findings into other documents.

---

## Step 19 — Propagate the territory correction

- **Date:** 2026-08-10
- **Directed:** "update all documents"

### What the sweep found first

Grepping for the claim before editing surfaced something uncomfortable: **the comparison agent
had already caught this at Step 14.** `COMPARISON-ERC-VS-PDF.md` said plainly that 20 of the 25
are single-territory and 4 use county/city definitions.

`OPEN-ITEMS.md` **OI-15 ignored it** — subtracting 4 from 25 to get "21 remain" — and
`GL-RATING-ENGINE-BUILD-PLAN.md` and `PRD-GL-RATING-ENGINE.md` inherited that number from the
register.

So the error was not a failure of analysis. **It was a failure to carry a correction forward**,
introduced by me at Step 15 and propagated into two documents at Steps 16–17. What the user's
hypothesis added was the confirmation, the `NC = 002` detail, and the finding that ERC carries
the county/place tables itself.

### Action — nine files

| File | Change |
|---|---|
| `Agentic\iso-erc-expert\knowledge\invariants.json` | `ERC-TER-001` rewritten; **BLOCKER → MAJOR**; evidence records what the superseded measurement counted |
| `Agentic\iso-erc-expert\knowledge\territory.json` | Per-jurisdiction `scheme`, `rating_territory`, `lookup_required`; `CW` retagged `COUNTRYWIDE_NOT_RATED` |
| `Agentic\iso-erc-expert\tools\erc.py` | **Territory verdicts rewritten** — the tool had the old conclusion hardcoded and was still answering "unverifiable" after the register was fixed |
| `Agentic\iso-erc-expert\tools\smoke_test.py` | The failing assertion **encoded the wrong behaviour**; replaced with six checks of the corrected model |
| `Agentic\iso-erc-expert\AGENT.md` | Territory removed from the mandatory-`unverifiable` list |
| `Agentic\iso-erc-expert\README.md` | CA example and the limits table corrected |
| `docs\erc\03-RATING-STRUCTURE.md` | §5.2 correction block; open question 2 struck |
| `docs\erc\06-VALIDATION-AND-BACKLOG.md` | §3.2 retitled and rewritten; backlog 4.3 🔴 → 🟢/🟠 |
| `docs\GL-RATING-ENGINE-BUILD-PLAN.md` | §1, §7, §9, §10 |
| `docs\PRD-GL-RATING-ENGINE.md` | §7 risk row rewritten as resolved, in plain language |
| `docs\COMPARISON-ERC-VS-PDF.md` | Verified-and-extended block: residue is **zero**, and ERC carries the county/place tables too |

`docs\rating-engine\*` needed **no change** — the PDF derivation had 27 / 4 / 20 correct all along.

### Two things the sweep caught that a documentation-only edit would have missed

- **The agent's tool contradicted its own register.** After `invariants.json` was corrected,
  `erc.py territory AK` still printed *"unverifiable — the engine must be given the territory."*
  The conclusion was hardcoded in the command. A knowledge-base edit alone would have left the
  agent asserting the wrong answer in the one place a consumer actually reads.
- **The smoke test asserted the wrong behaviour and correctly failed.** It required a jurisdiction
  without a ZIP map to report `unverifiable`. That is exactly what a regression test should do
  when a conclusion changes — the failure was the test working, not breaking.

### Result

Both agents green: **iso-circular-expert 15/15**, **iso-erc-expert 88/88** (up from 83 — the
replaced assertion added five). Scheme counts now reconcile exactly: 27 ZIP + 20 single +
4 county/place = 51 rating jurisdictions, plus `CW` tagged as not rated.

Verified live across all three schemes:

```
AK  SINGLE_TERRITORY   001 (entire state)      RESOLVED
NC  SINGLE_TERRITORY   002 (entire state)      RESOLVED  <- the lone exception
CA  COUNTY_PLACE       11 codes / 21 places    INPUT NEEDED: address -> place [OI-34]
NJ  ZIP_TABLE          18 codes / 736 ZIP rows RESOLVED
```

### Findings

- **A correction is not applied until every consumer of it is updated.** The chain here ran
  register → specification → plan → PRD → agent knowledge → agent tool → agent test. Fixing the
  first and last would have left four inconsistent artifacts, and the tool is the one that
  actually answers questions.
- **Regression tests that encode a conclusion will fail when the conclusion changes — and should.**
  The instinct to "fix the failing test" would have restored the wrong answer.
- This was the **fourth** gap-that-wasn't, and the first where the correction already existed in
  writing and simply was not propagated. That is a different failure mode from the previous three,
  and arguably a more preventable one.

### Open items raised (not resolved in this step)

- None new. OI-15 closed at Step 18; OI-34 (address → county/place for CA, FL, NY, TX) remains
  open and is now referenced consistently across all documents.

---

## Step 20 — Build doctrine set; plan rewritten under it

- **Date:** 2026-08-10
- **Directed:** "Build the rating engine, based on the ERC files, with the PDFs as confirmation of
  the build, and not the source. There should be no assumptions outside of what exists in the
  files, where confirmation is needed, refer to the manuals, and if that fails, ask me directly.
  Create the plan based on this criteria, and log this criteria."

### Context — the decision this settles

Step 19 surfaced that the build plan never resolved its own foundational question: **execute
ISO's rule program, or reimplement the algorithm using ERC as data?** The plan called ERC an
"execution substrate" supplying "executable rules" while drawing an architecture that computes
the premium chain in Python — two different builds, one document.

I laid out both paths and recommended the second. The user's answer is **stricter than what I
proposed.** I had suggested ERC's rules as the *specification* with the PDFs supplying semantics
where ERC was silent. The doctrine forbids that second half: the manual may confirm, never
source.

### Evidence found while framing the question

Checking the corpus before answering surfaced a **complete input/output pair** —
`OK/GL_OK 20250601 V01/STC/1. Output.json`, a fully rated policy:

```
BaseRate 0.095  ×  FinalILF 2.05  →  FinalRate 0.195      (0.19475, rounded at 3dp)
AnnualBasicLimitsCoPremiumPremOps    475.00
AnnualBasicLimitsCoPremiumProdCompldOps  4,100.00
ErcCalculatedTotalPremium          7,839.00
```

A **golden test case available today**, without RAaS — one jurisdiction, one policy, but it
corroborates the derived premium chain end to end and is evidence on rounding. 516 further STC
inputs exist without expected outputs, usable as realistic risk shapes.

### Action

1. Recorded the criteria as **standing** at the head of this log, above Step 0 — it binds all
   later work, not just this step.
2. **Rewrote `docs\GL-RATING-ENGINE-BUILD-PLAN.md`** under the doctrine, superseding the prior
   co-equal-sources framing.

### What the doctrine changed in the plan

| Previously | Now |
|---|---|
| A PDF-derived "semantic overlay" module supplying rounding, interpolation, eligibility | A **confirmation register** recording only what the manual *confirmed* about ERC content, with citations |
| Territory: ERC for 27, manual for 4 | **ERC for all 51** — no cross-source dependency exists |
| ILF interpolation taken from Rule 56.A.4 | ERC has no such machinery → **E6, escalated**; off-table limits `REFER` |
| Rounding defaulted to the manual's half-up | **E1, escalated.** The golden case is evidence, not authority |
| Untraced multipliers defaulted to 1 | **E5, escalated.** Affected chains flagged, not silently multiplied |

### The escalation register — the doctrine's real output

Ten items (E1–E10) that are ERC-checked, manual-checked, and unresolved, so each comes to the
user: rounding mode; `ErcCore`; the 6 undefined operators and `MessageHelper`; `Status` A/C/D;
the three untraced multipliers; off-table interpolation; the `0`-sentinel extent;
address→county/place for CA/FL/NY/TX; the company LCM; and the experience mod input.

**E2 and E3 are procurement, not engineering** — `ErcCore` and the engine specification are
obtainable only from ISO, and the lead time starts when asked.

### Findings

- **The strict doctrine produces a shorter build and a longer escalation list**, which is the
  correct trade. Every item on that list is a question the looser framing would have absorbed
  silently as a default.
- **Two things got *better* under the constraint, not worse.** Territory needs no cross-source
  dependency at all (Step 18 proved ERC carries all three schemes), and the untraced multipliers
  become visible flags rather than an invisible `× 1`.
- **The doctrine is enforceable in the type system.** `Cell.erc_source` mandatory means a value
  with no ERC provenance cannot be constructed — the constraint is structural rather than a rule
  reviewers must remember.

### Open items raised (not resolved in this step)

- **The 19-rating-table count was sampled, not verified corpus-wide.** It is load-bearing for the
  effort estimate and is now Phase 1's first task; if materially higher, the calculus changes.
- E1–E10 all await the user. E2/E3 should be requested from ISO regardless of sequencing — I can
  draft the request on request.
- `docs\PRD-GL-RATING-ENGINE.md` and `docs\GL-RATING-ENGINE-DOCS.html` still describe the prior
  co-equal-sources framing. The HTML regenerates from source; the PRD needs a pass.

---

## Step 21 — Rounding confirmed, multipliers traced, LCM deferred

- **Date:** 2026-08-10
- **Directed:** "The ERC rules/algorithm should specify rounding, what are the untraced
  multipliers? If you confirm rounding, log the answer." … then: "log these and for now leave LCM
  at 1.0, that will be a carrier deviation, we are not there yet. Moving forward, make sure you
  READ what's needed to be read instead of assuming, this keeps happening."

### E1 — Rounding: CONFIRMED

The user was right that the rules specify it. I had flagged it unresolved from `@DecimalPlaces`
on **table definitions** — that is column precision, the wrong artifact. The rule program carries
an explicit operator:

```xml
<rul:Round ToDataDef="FinalILF" DecimalPlaces="3">
  <rul:Subtract>…</rul:Subtract>
</rul:Round>
```

**648 `Round`/`Truncate` occurrences corpus-wide.** Only two attributes are ever used:
`DecimalPlaces` (582) and `ToDataDef` (364). Scale by site: **3dp** ×290 (rates, ILFs, factors),
**0dp** ×238 (Premium), **4dp** ×32, **2dp** ×22 (loss costs).

**Verified end-to-end against the ISO golden output** (`OK/GL_OK 20250601 V01/STC`):

```
BaseRate  = 0.095 × LCM 1.0 × ClaimsMade 1.0          = 0.095       ✓ ISO: 0.095
ILF′      = MedPay 1.003 + ILF 2.05 − 1               = 2.053
FinalRate = 0.095 × 2.053 = 0.195035 → 3dp            = 0.195       ✓ ISO: 0.195
Premium   = 0.195 × 5,000 + MedPayCharge 1.0
          = 976.175 → 0dp                              = 976         ✓ ISO: 976
```

This independently confirms the **medpay-additive** rule from ERC's own arithmetic, not only from
the manual.

**Residual:** no mode/midpoint attribute exists on any of the 648 sites, and the golden case does
not land on a midpoint, so **half-up vs half-even is still open**. Worth ≤ $1 per coverage line at
0dp. **E1 downgraded BLOCKER → bounded question**, to be settled by RAaS.

### E5 — The three "untraced" multipliers: all rule-computed

Not external inputs. Each has a named rule, read in full:

| DataDef | Rule | Logic |
|---|---|---|
| `ModToUse` | `SetModToUse` | `Choose`: if `ScheduleRatingModificationApplies = "Yes"` → copy `ScheduleRatingModificationFactor`; else if `CPPIRPMFactor > 0` → copy it; **otherwise 1.0** |
| `ExpenseModification` | `SetExpenseVariationFactor` | If experience rating applies **and** expense variation applies **and** `ERPActualExpectedLossRatio > 0` → `ERPExpectedLossRatio ÷ ERPActualExpectedLossRatio` at 3dp; **else 1.0** |
| `PremiumDiscountCharge` | `SetPremiumDiscountCharge` | If `PremiumDiscountPercentage` is not null → `round(1 − pct × 0.01, 3)`; **else 1.0** |

All three default to **1.0** and are only non-unity when a specific input is supplied. That is why
the golden case closes without them (`ModToUse 1.0`, `ExpenseModification 1.0`,
`PremiumDiscountCharge` absent).

My "direct multipliers with no source table" confused *no rate table* with *no source*. A
modification factor is computed by rule logic — which is exactly where it belongs. **E5 closed.**

### E9 — Company LCM: deferred by decision

User direction: **hold LCM at `1.0`**. It is a carrier deviation and out of current scope. ERC
corroborates the shape — `LCM.RateTable.csv` and `LCMCompany.RateTable.csv` both exist at 0 rows,
and the golden case carries `LCM = 1.0`. **E9 closed as a decision**, not a gap: the engine
multiplies by 1.0 and records the value as a named, overridable carrier parameter.

### Escalation register after this step

Closed: **E2** (bounded schema dependency, not a blocker) · **E3** (single-valued, self-describing)
· **E5** (rule-computed) · **E9** (decision). Reduced: **E1** (tie-break only). Remaining genuine:
**E4** `Status`, **E6** interpolation, **E7** `0`-sentinel extent, **E8** geocoding, **E10**
experience mod input.

**Five of ten escalations dissolved on being read.** That is the measure of the defect below.

### The standing criterion this produced

Recorded at the head of this log. The pattern is nine instances of the same shape — measure
structure, infer content from names — of which **four occurred in one exchange after the first
five had already been written up as lessons.**

The operational rule: **before asserting that something is absent, undefined, untraced or
unavailable, open it.** An escalation is valid only if it names the file opened and the search run
that failed to answer it.

### Findings

- **Documenting a failure pattern does not prevent it.** Items 1–5 were logged with lessons
  attached; items 6–9 followed anyway. What changed the outcome was the user asking a pointed
  question that could only be answered by reading.
- **The cost was asymmetric and invisible.** Every one of these produced an escalation that would
  have gone to ISO or the user as a real question, consuming their time to answer something the
  files already stated.
- **`ToDataDef=` is the single highest-value search in this corpus.** "No table for X" is not
  evidence that X is unsourced; ERC computes a great deal in rules rather than tables.

### Open items raised (not resolved in this step)

- E1's tie-break mode remains, pending RAaS or an ISO answer.
- E4, E6, E7, E8, E10 stand — but each should now be re-tested by reading before being escalated
  further, on the same grounds that dissolved five of the ten.

---

## Step 22 — Re-test the remaining escalations by reading

- **Date:** 2026-08-10
- **Directed:** "yes" — re-test E4, E6, E7, E8, E10 by reading before escalating further, per the
  standing criterion set at Step 21.

### Result — two more dissolved, one reframed, two stand

| # | Was | After reading | Evidence |
|---|---|---|---|
| **E4** `Status` A/C/D | open | **stands** | Searched all six DOC workbook sheets (`Table of Contents`, `Refer to Company`, `Not Supported`, `Special Consideration`, `Full Form Name`, `Base RaaS Overrides`) — **zero hits**. Now confirmed absent rather than assumed |
| **E6** interpolation | open | **✅ dissolved** | `DomainEachOccurrenceLimit` has **13 rows** — the limit input is a **closed enumerated domain**, matching the ILF table's 13 amounts × BI/CSL = 26 keys. An off-table limit cannot be entered. ERC *does* interpolate (`InterpolateMode="Linear"`, 18×) but only on `PremOpsSizeOfRiskRelativity` / `ProdsCompldOpsSizeOfRiskRelativity`, where input is continuous |
| **E7** `0`-sentinel | open | **reframed** | Zeros occur in **31 of 79** tables scanned and are usually legitimate (`DedFactor` 0 = no credit; `MinPremium` 27/27 zero). **A sentinel is indistinguishable from a real zero by inspection.** Decisive: `UnmannedAircraftUsageBIPDRatingModifiers` pairs `1` for aerial photography with **`0` for firefighting, crop spraying, internet access** — and `ErcSetRatesAndFactors`, the rule that reads it, has **no guard**: no `GreaterThan`, no `IsNull`, no zero test |
| **E8** geocoding | open | **stands** | Genuinely external — no ZIP→county/place aid in ERC for CA/FL/NY/TX |
| **E10** experience mod | open | **✅ largely dissolved** | ERC computes the full apparatus in `GeneralLiabilityRules.Rule.xml`: `SetActualExperienceRatio` → `SetExperienceCredibilityFactor` → `SetExperienceModification` → `SetExperienceRatingModificationRatesandFactors`, with an `ERPExperienceModificationOverride` path. Needs loss-history **inputs**, not a missing mechanism |

**Seven of the original ten escalations were answered by opening a file.**

### Two bonus resolutions from the same pass

- **`Base RaaS Overrides` decoded** — listed as undefined in ERC report 1. It is a 363-row register
  of `(TABLE, COLUMN, DATA TYPE)` flagged `STATE` or `COUNTRY WIDE`: **the fields a consumer may
  override when calling RAaS.** Directly useful for the eventual integration.
- **The experience chain has an explicit override input** (`ERPExperienceModificationOverride`),
  which is how a carrier-supplied mod enters.

### E7 promoted from question to build requirement

This is the significant outcome. E7 is **not** something to ask ISO. It is a defect class the
engine must defend against:

> A factor of `0` in an ERC rate table may be a real zero or an unguarded refer-to-company
> sentinel, and **ERC's own rules do not distinguish them**. Any factor must be checked against a
> confirmed-sentinel register before it multiplies.

Left unhandled it produces a **$0 premium on exactly the risks meant for human review** —
firefighting and crop-spraying drone operations, and the >55 lb weight band. Added to the build
plan as non-negotiable **N13**.

### Findings

- **The sweep I proposed would not have worked.** "Find all the zero sentinels" assumes sentinels
  are identifiable from the data. They are not — the discriminator is the manual, and only for
  cases the manual addresses. The correct design response is a register plus a hard stop, not a
  scan.
- **Reading the rule was worth more than reading the table.** The table showed zeros; only
  `ErcSetRatesAndFactors` showed that nothing guards them.
- **The standing criterion held on its first application** — five items re-tested, two dissolved,
  one materially reframed, two confirmed by evidence rather than assumption.

### Open items raised (not resolved in this step)

- Genuinely remaining: **E1** (rounding tie-break), **E4** (`Status`, cosmetic), **E8**
  (geocoding for CA/FL/NY/TX). E7 is now build work, not an escalation.

---

## Step 23 — E8 decided: county is a submission field

- **Date:** 2026-08-10
- **Directed:** "For E8, require county on submission."

**Decision.** In CA, FL, NY and TX the engine requires **county** as a submission field rather
than deriving it from an address. ERC already carries the place-name → territory tables for all
four (CA 11 codes / 21 places, FL 5 / 8, NY 20 / 66, TX 8 / 15); only address resolution was
external, and this removes that dependency entirely.

Behaviour: a missing or unmatched county produces `REFER`. **Never a fuzzy match** — the place
lists are ISO's own vocabulary, and a near-miss silently rates the wrong territory.

**Consequence:** all 51 jurisdictions now resolve territory with no external dependency —
27 by ZIP, 20 by constant, 4 by submitted county. Phase 3's exit criterion updated accordingly.

**E8 closed.** Genuinely remaining: **E1** (rounding tie-break, settled by RAaS) and **E4**
(`Status`, cosmetic). Of the original ten escalations, seven dissolved on reading, one became a
build requirement (N13), one became a submission field, and one awaits RAaS.

---

## Step 24 — Rating-vs-capture split verified corpus-wide

- **Date:** 2026-08-10
- **Directed:** "yes run it" — verify the rating-table count across all packages, the load-bearing
  number behind scope, effort and the stated ceiling.

### Method

`scripts\erc\25_rating_vs_capture.py` — parallel scan of **572 package directories**. Every rule
writing a `*Premium` DataDef is classified by what it reads:

| Class | Test |
|---|---|
| `RATE_DRIVEN` | references `FinalRate` / `BaseRate` / `LossCost` / `ELP` / `AdjustedBaseRate` |
| `CAPTURE` | references `ManualPremium` and no rate |
| `OTHER` | writes a Premium some other way |

Counted by **DataDefGroup** (the coverage unit), not rule instance, since groups repeat across
packages. A group counts as rating if **any** package rates it — so state-specific algorithms are
not masked by countrywide silence.

### Result

**9,509 premium-writing rule instances · 477 distinct coverage groups:**

| Class | Groups |
|---|---|
| **RATE_DRIVEN** | **16** |
| **CAPTURE** | **383** |
| **OTHER (aggregators)** | 78 |

The earlier **19** counted schema tables including minimum-premium top-ups; **the substance is
confirmed** — roughly a dozen-and-a-half coverages genuinely rate and ~380 capture. The ceiling
stated throughout the documentation stands.

`OTHER` was inspected rather than assumed: `ErcCalculateTotalPremium` delegates via `RunRule`;
`CalculateTotalPremium` is `ForEach` + `Sum` over child `Premium` values. **Aggregators, not
missed rating paths.**

### The finding: three state-specific rating coverages

A countrywide-only reading misses these entirely. They have **their own algorithms** — they are
not overrides of a countrywide rule:

| Coverage | Packages |
|---|---|
| `GeneralLiabilityMarylandChangesLiabilityForHazardsOfLeadClassLvl` | 14 |
| `GeneralLiabilityMassachusettsChangesLeadPoisoningEndorsementClassLvl` | 7 |
| `GeneralLiabilityMassachusettsChangesSupplementalCovLeadPoisoningClassLvl` | 7 |

Also surfaced: `GeneralLiabilityClassificationSpecialProtectiveHighwayCoverage` (10 packages),
which the countrywide scan had missed.

Rating-coverage spread, by packages carrying them: Prem/Ops 203 · Prod/CompOps 185 ·
Classification 146 · Liquor 97 · LoED 72+72 · OCP 29 · Railroad 29 · Cyber 11+11 · Product
Withdrawal 10+10 · Special Protective 10.

### Documentation updated

- `docs\GL-RATING-ENGINE-BUILD-PLAN.md` §3 — sampled figure replaced with the verified one and
  the method cited; §8 build order gains **state-specific coverages (11)**, a **capture harness
  (12)** for the 383 groups, and policy assembly renumbered (13); §12 phasing extended to 18
  phases; §13 ceiling restated as 16 / 383 / 78.

### Findings

- **Counting by coverage group rather than by rule instance was the right unit**, and taking "any
  package rates it" as the test is what surfaced the three state coverages. A countrywide-first
  count would have reported 13 and been quietly wrong about Maryland and Massachusetts.
- **The capture harness deserved its own phase.** 383 groups is the largest single body of work in
  the build, and the plan had been treating it as an afterthought to the rating calculators.
- **Item 1 of "what's needed to finalise the plan" is now closed.** Remaining: write the
  Premises/Operations gate, extract the Oklahoma golden case as a fixture, and size the phases.

### Open items raised (not resolved in this step)

- The three state coverages have not been read. Their algorithms are unknown beyond the fact that
  they rate; each needs a §9 gate like any other coverage.
- Phase sizing still absent, now unblocked.

---

## Step 25 — Paused. ~~NEXT SESSION STARTS HERE.~~ *(superseded — resumed at Step 27; the live handoff is **Step 40**)*

- **Date:** 2026-08-10
- **Directed:** "let's pause here, and have this be the first step tomorrow."

### ▶ First task tomorrow

**Write the Premises/Operations (subline 334) gate** — the §9 deliverable in
`docs\GL-RATING-ENGINE-BUILD-PLAN.md`. It is build-order item 1 and the next real deliverable.

It matters beyond 334: **it is the test of whether the gate format is sufficient to build from.**
Ten more coverages follow the same template, so a defect in the format is cheapest to find now.

The gate must contain, per §9:

1. The algorithm as ordered steps, each citing the **ERC file** that sources it
2. Confirmations — where the manual was consulted, what it confirmed, the citation
3. Escalations — anything neither source settles, and what the engine does meanwhile
4. Inputs consumed, and behaviour when one is absent
5. Lookups and their layer — countrywide, state, or overridden
6. State deviations — enumerated and quantified per jurisdiction
7. Refer-to-company triggers
8. Test result — the Oklahoma golden case, plus both agents' findings

### Where to start reading

| Artifact | Why |
|---|---|
| `countrywide/GL CW 20270401 V01/Rules/GeneralLiabilityClassificationPremOpsCoverageRules.Rule.xml` | The rating algorithm itself — `SetPremium`, `SetFinalILF`, `SetAdjustedBaseRate` |
| `countrywide/GL CW 20270401 V01/Rules/GeneralLiabilityRules.Rule.xml` | `SetModToUse`, `SetExpenseVariationFactor`, the experience chain |
| `OK/GL_OK 20250601 V01/STC/1. Input.json` + `1. Output.json` | The golden case — already reconciles end to end |
| `docs\GL-RATING-ENGINE-BUILD-PLAN.md` §4 (N1–N14), §6, §9 | Non-negotiables, the premium chain, the gate spec |

Governed by the standing criteria at the head of this log: **ERC is the source, the manual only
confirms, nothing is assumed — and read the file rather than inferring from its name.**

### State at pause

**Settled:** build doctrine · evidence hierarchy · 14 non-negotiables · architecture · resolver ·
premium chain (verified against ISO's own output) · rounding sites · territory for all 51 ·
rating-vs-capture split verified corpus-wide (16 / 383 / 78) · build order of 13 · 18 phases.

**Escalations:** of the original ten — seven dissolved on reading, E7 became non-negotiable N13,
E8 became a submission field. **Remaining: E1** (rounding tie-break, settled by RAaS) and **E4**
(`Status`, cosmetic).

**Still to do after the 334 gate:** extract the Oklahoma golden case as a runnable fixture; size
the phases; read the three state-specific coverage algorithms (MD, MA lead).

**Not started:** any engine code.

---

## Step 26 — Documentation reconciled

- **Date:** 2026-08-10
- **Directed:** "update all logs."

Reconciliation pass so nothing carries a superseded claim into tomorrow.

### `docs\OPEN-ITEMS.md` — eight entries changed state

| # | Was | Now |
|---|---|---|
| OI-07 | Experience mod input `OPEN` | `CLOSED` — ERC computes the whole chain; loss history is an input |
| OI-09 | Rounding mode `OPEN` | `OPEN`, **scope reduced to the tie-break** — 648 `rul:Round` sites read; the original claim cited the wrong artifact |
| OI-10 | `Status` A/C/D | `OPEN` — now confirmed absent from the DOC workbooks too, not assumed |
| OI-11 | `ErcCore` `OPEN` | `CLOSED` — supplies 2 of 28,233 elements; an envelope, not the core |
| OI-12 | Operator semantics `OPEN` | `CLOSED` — one value each corpus-wide, no branching to misread |
| OI-13 | Three multipliers `OPEN` | `CLOSED` — all rule-computed, each defaulting to `1.0` |
| OI-17 | `0`-sentinel `OPEN` | **`BUILD WORK`** — non-negotiable N13, not a question for anyone |
| OI-34 | Geocoding `OPEN` | `CLOSED` — county becomes a submission field |

Two status values added — `CLOSED` (retained with the evidence that settled it) and `BUILD WORK`
(a requirement, not a question) — plus a header note recording that the pass re-tested every item
**by opening the file**.

Register now: 15 `OPEN` · 7 `CLOSED` · 5 `PARTIAL` · 4 `AUDIT` · 6 `HYGIENE` · 2 `BY-DESIGN` ·
2 `BUILD WORK`.

### Other documents

- **`README.md`** — status line records the doctrine and the seven-of-ten outcome; routing row
  for `OPEN-ITEMS.md` corrected (it had been left at "27 items").
- **`docs\PRD-GL-RATING-ENGINE.md`** §8 — states plainly, in lay terms, that applying the rule
  **shrank** the question list rather than growing it, and that scope was verified (16 / 383)
  rather than estimated, including the three state-specific calculations.
- **`docs\erc\*`** — the agent's "19 tables" measurements annotated with the corpus-wide
  reconciliation rather than overwritten; the two counts measure different units and both stand.
- **`docs\GL-RATING-ENGINE-DOCS.html`** regenerated.

### Verification

Stale-claim sweep across every `.md` and `.json`: the only surviving matches are **annotated or
struck-through** references retained deliberately. **Zero broken links** across all documentation.
Both agents green — **iso-erc-expert 88/88, iso-circular-expert 15/15**.

### Findings

- **The routing row in `README.md` still said "27 items" while the register held 34.** Small, but
  the same defect as Step 19: a correction applied to the artifact and not to the thing pointing
  at it. Worth a standing habit of grepping for the *old number* after any count changes.

---

## Step 27 — The Premises/Operations (334) gate

- **Date:** 2026-08-11
- **Directed:** "continue where we left off" — Step 25's first task.

**Deliverable:** `docs\gates\GATE-334-PREMISES-OPERATIONS.md`. **Gate passed.** The algorithm is
derived end to end from ERC, confirmed at five points by the filed manual, and reproduces the
Oklahoma golden case exactly — **`Premium = 976.00`**, every intermediate traced to a named rule
and a named table row.

### The finding: the 334 algorithm is edition-scoped, not just its rate tables

The premium chain in §6 was written from the countrywide **2027** package. The golden case runs on
`GL_OK 20250601 V01`, whose XSD `xs:import` names **`GL_CW_20231201_V03`** — and that edition
computes medical payments differently:

| | CW 2023 V03 and earlier | CW 2027 V01 |
|---|---|---|
| `FinalILF` | `round(CSLILF − FinalDeductibleFactor, 3)` | `round(CSLILF + MedPayFactor − 1 − FinalDeductibleFactor, 3)` |
| Med-pay | separate `MedicalPaymentsCharge`, added in `SetPremium` | folded into the ILF; **no such rule exists** |

The two are **algebraically identical** — the fold distributes exactly to the separate charge. They
differ only in where rounding lands, and that is enough: the same risk prices at **976 under CW
2023 and 975 under CW 2027.** **10 distinct countrywide parents are in live use** across 562 state
packages, so this is not a tail case. `rating/sublines/` needs one module per *(subline, edition
family)*, not per subline.

**What surfaced it was resolving the golden case's declared parent instead of reading the newest
countrywide package.** That is now a standing habit for the remaining ten gates.

### Second confirmed N13 sentinel — on the primary rating path

Every one of the 15 **"Per Claim"** deductible factors is `0` in the countrywide table
(`"CW",3,"250 Per Claim",0` … `"100,000 Per Claim",0`) while every corresponding **"Per
Occurrence"** row carries a real factor (`0.005`, `0.01`, `0.013`, …). The factors are unpublished,
encoded as `0`, and ERC's only guard is a **validation rule, not a rating rule** —
`DoMessageMustEnterPremOpsBIPDDeductibleFactorOverride`.

It differs from the drone case in direction: `FinalILF = CSLILF − FinalDeductibleFactor`, so an
unguarded `0` withholds the credit and **overcharges** rather than producing a free policy. Equally
silent. Both go in the sentinel register — and the lesson generalises to **new N15: the `DoMessage*`
rules are part of the algorithm.** An implementation porting only the rating chain drops the
defence entirely.

### Also measured

- **State deviations, all 51 jurisdictions** (`scripts\erc_census_334.py`, 572 packages).
  **32 carry no PremOps override at all.** Of the 19 that do, only **8 touch premium** — CA/NJ/NY/OH
  partition the loss-cost table, MA/NY/TX override `SetBaseRate`, KY has an elevator-contractor ILF,
  OK a governmental-subdivision ILF. The other 14 are statistical coding only.
- **Table layers, counted not assumed.** `PremOpsLossCost`, `ILFPremOps` and
  `PremOpsIncrdLimitTableAssignment` are **header-only countrywide** and fully populated per state
  (OK: 3,564 / 432 / 1,196). Deductible factors, med-pay factors, classification type and minimum
  premiums are **countrywide only**. Finding #1 of the README, measured on the primary path.
- **A second inheritance mechanism (new N16).** Every 334 lookup is a `FirstNonNull` of two `Lookup`
  calls on the *same* table — keyed `/*/State/Code`, then the literal `"CW"`. Row-level fallback
  inside one table, distinct from N3's package-layer override-by-name. Both live at once.
- **A `$1` floor in CW 2027.** If the premium computes to `0` while exposure `> 0`, `SetPremium`
  writes `1.0`. So a broken rating path returns a plausible dollar, not a visible zero — an
  assertion keyed on `Premium == 0` would not catch it.

### Corrections

- **`GL-RATING-ENGINE-BUILD-PLAN.md` §6 called the golden case `PremOps 475.00`.** That is
  `AnnualBasicLimitsCoPremiumPremOps`, a basic-limits figure **consumed by no rule**. The 334
  premium is **`976.00`**. Step 21 of this log recorded it correctly under its own field name; the
  build plan's shorthand is what read as the subline premium. Same defect as Steps 19 and 26 — a
  correct value restated loosely somewhere downstream.
- **I claimed mid-work that `0.19475 → 0.195` was a rounding midpoint and therefore evidence for
  `ROUND_HALF_UP`. It is not** — `0.19475 > 0.1945`, so every mode agrees. Caught by re-checking my
  own arithmetic before presenting it. **E1 gains no evidence and stays open**, exactly as the build
  plan already recorded.

### Findings

- **The gate format is sufficient to build from**, which is what Step 25 set it to test. Four of the
  eight items each forced a measurement that changed the plan: item 4 (absent input silently
  reroutes to the ELP path), item 6 (32/19, only 8 premium-affecting), item 7 (the second sentinel),
  item 8 (the 475/976 correction).
- **Reading the rule beat reading the table again.** The three zeros in 334 are indistinguishable in
  the data: one legitimate (size-of-risk, whose branch omits the factor entirely), one an
  unpublished factor, one a degraded referral. Only the consuming branch separates them.
- **The manual confirmed and did not source.** Rule 56.D.2 supplies the med-pay formula with a
  worked example (`1.020 + 1.95 − 1 = 1.97`) matching CW 2027 exactly, and Table 23.D.5.c.#1 gives
  split-limit weights `0.83 / 0.19 / 0.03` for the 50000–59999 band — identical to the golden case
  output, from a source with no access to it. One apparent conflict (`.090` vs `0.095` for
  OK/501/50017) is an edition difference between a 2027 notice and a 2025 package, recorded so it is
  not re-opened as a defect.

### Open items raised

- **E11** — `AdditionalInterestFactor` is computed on every 334 quote and read by no rule.
- **E12** — `PremOpsELP` is compared as both string and decimal within one rule.
- The three state-specific coverages (MD, MA lead) remain unread; phase sizing still absent.

---

## Step 28 — The Products/Completed Operations (336) gate, and the golden case made runnable

- **Date:** 2026-08-11
- **Directed:** "lets keep momentum going."

Two deliverables, taken together because the same golden case carries both sublines.

**`docs\gates\GATE-336-PRODUCTS-COMPLETED-OPERATIONS.md` — gate passed.** `Premium = 6,845.00`,
and with 334 the policy total closes exactly: **976 + 6,845 + 18 (terrorism) = 7,839**.

**`testserify_golden.py` + `testsixtures\golden-ok-2025.json` — 80/80 passing.** The golden
case is now runnable rather than described. Three independent layers: fixture vs ISO's published
output, fixture vs the ERC CSV cells, and the premium chain re-derived from those cells in
`Decimal`. Layer 3 is the specification in executable form; when the engine exists, a fourth layer
drops in beside it.

**The gate was written differentially** — shared machinery cited to gate 334 rather than
re-derived. It cost a fraction of the effort and still surfaced four things 334 could not.

### The finding: a published `0` that switches the rating path — and the column that says so

336 rates off the ELP, not a loss cost, because of one cell:
`ProdsCompldOpsLossCost → "OK","999","50017",0`. The row **exists** and its value is `0`;
`SetBaseRate` tests `== 0.0` and takes the ELP branch. **Read as a rate it gives `BaseRate = 0` →
a free products liability policy on a class ISO prices at $6,845.** That is a *fourth* meaning of
`0` in this corpus.

But this one **has a discriminator, and Step 22's conclusion that none exists is wrong for the
loss-cost tables.** Every subline carries a sibling selector — `PremOpsELPText`,
`ProdsCompldOpsELPText`, `LiquorELPText`, `OwnersContractorsELPText` — over a closed vocabulary:
`Rate/Loss Cost Applies` · `Industry` · `Company` · `Not Applicable`. For the golden case:
Prem/Ops = `Rate/Loss Cost Applies` (→ 0.095), Prod/CompOps = `Industry` (→ ELP 0.82).

Tested corpus-wide (`scripts\erc8_elp_selector.py`, 572 packages): **620,856 agreements between
the selector and the `LossCost != 0` test, zero disagreements.** Now **non-negotiable N17** — read
the basis from the selector and hard-fail on disagreement. This **narrows N13**: two of the four
zero-meanings now have an in-corpus discriminator, and only the drone case still needs the manual.

Same shape as the seven escalations of Step 22 — the discriminator was in the corpus and nobody had
opened the table.

### E12 closed, E11 narrowed — both by the next gate

**E12 dissolves.** I raised it in Step 27: `SetMedicalPaymentsCharge` compares `../PremOpsELP` as a
string and `PremOpsELP` as a decimal. They are **two different DataDefs at two levels**, and the
`../` prefix says so — the classification-level one is the string rating-basis selector above. The
rule is correctly asking *"does this class rate off a loss cost?"* **Eighth escalation to dissolve
on being read.** I raised it from a name without opening the sibling table — the exact failure the
standing criterion warns against, committed one document after restating it.

**E11 narrows.** `AdditionalInterestFactor` is not dead: 336 consumes it in
`MinPremium = round(MinimumPremium × FinalILF × AdditionalInterestFactor, 0)`. The open question
shrinks to whether 334's omission is intended.

### Two more sharpenings of the non-negotiables

- **N3 — an override may be EMPTY.** 13 jurisdictions disable Defense-Within-Limits with a literal
  `<rul:Sequence />`, byte-identical in each. **Empty ≠ absent ≠ inherit.** An engine treating an
  empty body as fall-through applies a factor those states filed away.
- **N4 — and it drifts.** **Six jurisdictions have retired that override: CA, FL, GA, KY, VA, WA.**
  Virginia carried it in 2021 and it is gone from 2023 on. Same state, different premium by
  effective date. 19 jurisdictions across all editions; **13 today.**

Also: 336's increased-limits table assignment is **alphabetic** (`A`/`B`/`C`, no `…Int` conversion)
where 334's is **numeric** (`1`/`2`/`3`, with one). One `TableAssignment` type across both sublines
fails immediately on the golden case's `"B"`. And `Refer To Co.` appears in **all 51 jurisdictions,
2 class codes each** — in OK the catch-all codes `54444` and `94444`. Not an exotic path.

### Corrections — two of my own, caught before filing

- **I wrote up a manual/ERC disagreement on the Prod/CompOps split-limit weights that does not
  exist.** The keyword excerpt truncated two rows above the Manufacturing line and I read the
  Mercantile values as Manufacturing's. Fetching the full page gives `0.87 / 0.17 / 0.01` —
  **matching ISO's rated output exactly.** E13 was deleted before it was filed. *Search to locate a
  page; read the page to make the claim* — in this corpus a partial read looks exactly like an
  answer, which is the whitespace false-negative defect in another costume.
- **My first state-deviation count for 336 was wrong** — 18 current, when it is 13. The ad-hoc scan
  selected, per jurisdiction, the newest package **that contained the rule file**, which is exactly
  the set biased toward states that still have the override. **That is N4's own failure mode,
  committed while documenting N4.** The census script now selects the newest package outright and
  reports both scopes; `scripts\erc9_census_336.py` is generalised so every later gate reuses it.

### Also observed, not adjudicated

**Terrorism rated, and ERC supplied every factor** — exposure-class `0.004`, NBCR `0.58`,
`TerrorismILF 0.94`, none of them in the input, which carried `TerrorismCoverage: "No"`.
`README.md` states the Terrorism Supplement's absence means *"terrorism premium cannot be
computed."* **On this evidence that is too strong.** Terrorism is build-order item 9 with a
population audit already scheduled; the claim is now marked as needing that audit before it is
repeated.

### Findings

- **The differential gate is the right format from gate 2 onward.** Deriving 336 from scratch would
  have re-proved the resolver, the two inheritance mechanisms and the rounding sites for no gain.
  Diffing them is also what exposed the `TableAssignment` typing trap and the absent
  `MedicalPaymentsCharge` — both invisible from inside either subline alone.
- **The edition split is per coverage.** 334's chain differs between CW 2023 and CW 2027; **336's
  does not.** Establishing that per coverage, rather than inheriting Step 27's finding, is now a
  standing habit.
- **Three self-corrections in two steps, all caught by re-checking rather than by review.** The
  midpoint claim (Step 27), the split-limit disagreement, and the census scope. Each was a confident
  statement built on a partial read — which is the defect this project keeps rediscovering.

### Open items raised

- **OI-37** — is 334's omission of `AdditionalInterestFactor` intended? (E11, narrowed)
- Terrorism population audit, ahead of build-order item 9.
- Phase sizing still absent; the three state-specific coverages (MD, MA lead) still unread.

---

## Step 29 — The OCP / Principals Protective (335) gate

- **Date:** 2026-08-11
- **Directed:** "do it" — proceed to build-order item 3.

**`docs\gates\GATE-335-OWNERS-CONTRACTORS-PROTECTIVE.md` — gate passed, with the oracle gap stated
up front.** The corpus holds **one** rated output and it carries no OCP. Of 516 STC submissions,
**8 have a real OCP exposure and none has an expected output.** So this gate rests on derivation,
**six** manual confirmations and **three corpus-wide consistency tests** — not on reproducing a
published premium. Said plainly in the gate rather than worked around.

### The finding: the 2027 program deleted half this coverage

335 is the sharpest edition split yet — structural, not arithmetic:

| | CW 2023 | CW 2027 |
|---|---|---|
| rating steps | **21** | **12** |
| published loss-cost path | 3 rules | **all deleted** |
| marginal tiers | **two** — `$1,000,000` and `100 units` | **one** |
| Workers Compensation input | class `15191` special case | **removed** |
| minimum premium | 2 rules | **deleted** |

And the data moved with the rules. **OCP loss costs are published in 8 jurisdictions and the table is
absent in the other 43 — and those 43 are exactly the jurisdictions on the `2027-04-01` edition.
Zero exceptions either way.** All 51 published them in some earlier edition. The 2027 program also
retires classes `15191`/`15192`/`27111`/`27112` and introduces `27113` — and `27111`/`27112` are
precisely the two hardcoded in the pre-2027 `SetPremium` as using the 100-unit basis.

**So the build plan's "published in 15 jurisdictions, withdrawn in 36" is right that both paths are
needed and wrong about why.** It is not geography, it is **one program change in flight**, currently
8/43 and heading to 0/51. Both paths are needed **by effective date**, not by jurisdiction. New
habit 7: **when a document states a jurisdiction split, test whether it is really an edition split.**
README finding #4's 15/36 class-basis split has the same shape and deserves the same test.

### The premium chain is not universal

Every prior subline computes one rate and multiplies. **OCP is piecewise-linear**: two marginal
tiers, a **class-dependent breakpoint** (`$1,000,000`, or `100 units` for `27111`/`27112`) and a
**class-dependent divisor**, reading **six** rate tables. `Premium = round(FinalRate × min(exp,bp)/div
+ FinalRateOverBp × max(0, exp−bp)/div, 0)`. The premium step must be a per-subline strategy, never a
shared `rate × exposure` helper. §6 of the plan corrected accordingly.

### N17 corroborated a third time — on the hardest subline, and the manual pins the vocabulary

With the loss-cost table absent in 43 of 51, nearly every OCP risk takes the ELP path, where an
unguarded `0` is a **free policy**. Across all 51 jurisdictions, 433 (state, class) rows
(`scripts\erc_ocp_selector_and_refer.py`):

| Test | Result |
|---|---|
| `Rate/Loss Cost Applies` ⟺ non-zero published loss cost | **433 / 433** |
| `Company` ⟺ `ELP == 0` | **147 / 147** |
| `Industry` ⟺ `ELP ≠ 0` | 246 / 246, **plus 8 input-derived** (class `15191`) |

**The selector explains every zero on this subline**, across three different reasons for one.

And the manual settles what `Company` means: its ELP Supplement prints **`RTC`** for exactly the
classes ERC marks `Company` (`GL-AK-2020-LC-001-C` p.9, Table 5.C.). **`Company` = refer to company,
not "look up a company ELP".** 147 refer pairs across all 51 jurisdictions; class `93040` is
refer-to-company everywhere, in every edition.

The same table confirmed four ELP values to the cent ($0.95 · $0.54 · $0.68 · $0.48) against NJ and
AR, and the **75%** for class `15191` against ERC's countrywide `PrincipalsProtvLiabFactor = 0.75`.

### A fifth meaning of zero, and a "missing input" that isn't

`SetELP` branches by class code: `15191` → `ELP = PrincipalsProtvLiabFactor × WorkersCompensationRate`.
So a `0` in the ELP table for that class is a switch to an **input-derived** computation — the fifth
distinct meaning of `0`, and the fourth with an in-corpus discriminator.

**`WorkersCompensationRate` is a declared submission field** (`MasterGLCW.DataDef.xsd`, `xs:decimal`),
and a real STC submission supplies it (`1000.0`). So `README.md`'s fourth "what is not here" entry —
*Workers Compensation loss costs* — **was wrong**: the 75% is in ERC, the rate is an input, and the
whole dependency is retired by the 2027 program. Second "missing input" to dissolve this way, after
geocoding (E8). Struck through in the README with the correction recorded.

### E1 is live, not theoretical

The worked example (AR, real submission, parent `GL_CW_20230501_V01` — a **third** distinct edition,
verified step-for-step against CW 2023 V03 before being relied on) produces class `15192`:
`BaseRate 0.95 × ILF 1.75 = 1.6625` — **an exact 3dp midpoint, the first genuine rounding tie found
in this project.** `HALF_UP → 1.663`, `HALF_EVEN → 1.662`. The premium is `249` either way at this
exposure, so it does not settle E1 — but the golden case had suggested midpoints might not occur in
practice, and they do.

### Also

- **OCP is the most uniform coverage examined: 49 of 51 jurisdictions are pure countrywide.** Only NY
  overrides `SetILF`; AK and NY override `SetMoldStatCode`. All the variation is in the *data*.
- **A third limit vocabulary.** OCP limits are `"1,000,000"`; 334/336 use `"1,000,000 CSL"`. A shared
  limit normaliser returns `0.0` on every OCP ILF lookup.
- **OCP reuses `LookupPremOpsMinPremium`** — there is no OCP-specific minimum-premium table.
- **`SetELP`/`SetILF` gate on the class *description*; `SetLossCost`/`SetPremium` gate on the class
  *code*.** A submission with the code but not the description gets a rate and no ILF — premium `0`,
  silently.

### Findings

- **Habit 1 has now changed the answer in all three gates**: an arithmetic split in 334, a
  no-split confirmation in 336, and here two genuinely different coverages under one name.
- **The gate found more by having no oracle, not less.** Without a premium to reproduce, the checks
  had to be structural — and the three corpus-wide tests are stronger evidence about the *program*
  than any single policy would have been.

### Open items raised

- **E14 / OI-38** — `LookupPrincipalsProtvLiabFactor` survives in CW 2027 with no caller. Same shape
  as E11: an artifact with no consumer, possibly a rule set lagging its program change.
- The 8 OCP submissions are recorded as the seed fixture set for when an oracle exists.
- Phase sizing still absent; the three state-specific coverages (MD, MA lead) still unread.

### OI-39 raised and closed the same day

The habit-7 question was cheap enough to answer immediately. Measured in ERC across the latest
package of all 51 jurisdictions, the **class-basis** split is **8 / 43 on exactly the `2027-04-01`
boundary** — the identical boundary that withdraws the OCP loss costs. 238 Prem/Ops class codes are
pre-2027 only, 204 are 2027-only, 959 are in both (the 204 matches the figure already on record).

So README finding #4's *"15 jurisdictions / 36"* was a snapshot of the **PDF** corpus at an earlier
date, not a contradiction — but the framing was wrong in a way that matters: **it reads as
geography and it is a calendar.** Finding #4 rewritten to lead with the mechanism. **Habit 7 paid
out within the hour of being written down.**

### Prediction recorded for the next gate

`LiquorELPText` carries only **two** values corpus-wide — `Industry` and `Company` — and **no
`Rate/Loss Cost Applies` at all.** N17 therefore predicts Liquor Liability (332) is **entirely
ELP-or-refer**, with no loss-cost path even in principle. Recorded now so the next gate tests a
stated prediction rather than discovering it.

---

## Step 30 — Reconciliation across both specifications, and a correction to Step 29

- **Date:** 2026-08-11
- **Directed:** "what docs have been updated?" then "reconcile it all."

### The correction: my own figures were end-state figures, not current ones

Reconciling `docs/rating-engine/` against gate 335 exposed a defect in **the gate**, not the spec.

Gate 335 reported *"OCP loss costs published in 8 jurisdictions, absent in 43"* as a statement about
now. It was measured over the **latest package per jurisdiction** — and the corpus holds **82 state
packages effective after today**. That is the end state.

Re-measured as-of a date (`scripts\erc_migration_asof.py`):

| As of | Pre-2027 basis | 2027 basis | Publishing OCP loss costs |
|---|---|---|---|
| **2026-08-11 (today)** | **51** | **0** | **51** |
| 2027-04-01 | 8 | 43 | 8 |
| latest filed | 8 | 43 | 8 |

**Nothing has migrated. Forty-three jurisdictions change class basis on one day and lose their OCP
loss-cost tables with it.** It is a **cliff**, not a migration in progress.

Two consequences beyond the numbers:

- **The conclusion on record inverts.** *"A single national class list is wrong today"* — it is
  **right** today and stops being right on 2027-04-01.
- **The gate's actual conclusion is sharper, not weaker.** *Both paths are needed by effective date,
  not by jurisdiction* — and today the loss-cost path is the one always needed.

**I wrote N4 and habit 1 in this same session and then measured with "latest" anyway.** The rule was
stated and not applied to my own arithmetic. Worse, I used the wrong figure to "correct" README
finding #4 in Step 29 — replacing one end-state number with another and calling it current. The
defence is the new script, which takes an as-of date as a **required** input rather than defaulting
to latest.

**Both derivations made the identical error independently** — the PDF one over notices (15/36), the
ERC one over packages (8/43). Neither is a contradiction of the other; both are end-state counts of
the same program change from differently-dated corpora. And the PDF derivation had **already written
the correct reading** — *"the withdrawal is sharply dated"*, *"as their 2027 notices take effect"* —
in the body, while its own headline said "mid-migration". The right answer was on the page.

**OI-40 opened:** *every* "latest edition" count in this project is an end-state figure until
re-tested as-of a date. The known-affected ones are annotated; table population counts, territory
counts and class inventories have **not** been re-tested.

### The reconciliation itself

**`docs\gates\RECONCILIATION.md`** — one authoritative record of what the gates superseded, with
eight numbered items **R1–R8**, the five-way zero taxonomy, the new non-negotiables, and an explicit
list of what is deliberately *not* reconciled.

**Annotation, not rewriting.** The two specifications were derived independently and before any
subline was worked end to end; that independence is the project's main evidence, and overwriting
them would destroy it. So:

- **16 files** carry a dated banner naming the `R` items that touch them.
- **8 inline annotations** at the claims that would actually change a number or a decision —
  `rating-engine/12` and `13` (the migration framing), `09` (the Workers Compensation gap **closed**,
  the terrorism claim narrowed), `erc/03` (the premium chain: med-pay edition-scoping, the ÷1000
  basis, the `$1` floor, and OCP's piecewise structure), `erc/04` (the zero taxonomy).
- Everything else left exactly as each derivation found it.

**`rating-engine/09` G9 — Workers Compensation loss costs — is now `CLOSED`**, the first gap in that
register to close from the ERC side. **G4 Terrorism narrowed** rather than closed, pending the item-9
audit.

### Findings

- **Reconciliation found a defect in the new work, not the old.** The specifications survived the
  pass better than the gates did; the only thing that turned out to be wrong was written today.
- **"Both sources agree" is not the same as "both sources are right."** The 15/36 and 8/43 figures
  agreed on the mechanism and were both mis-framed the same way, because they shared a method, not
  because either checked the other. Cross-derivation evidence is only as good as the difference
  between the derivations.
- **The right answer was already in the corpus and in our own document.** Fourth time this project
  has rediscovered something it had written down — after the territory definitions, the
  reproducibility gap and the rating plans.

### Open items

- **OI-40** (as-of re-testing of every latest-edition count) — `AUDIT`, and it gates any figure used
  for phase sizing.
- **OI-39** corrected and closed. **OI-37** (terrorism audit) unchanged.
- Phase sizing still absent; the three state-specific coverages (MD, MA lead) still unread.

---

## Step 31 — Paused. ~~NEXT SESSION STARTS HERE.~~ *(resumed at Step 32; the live handoff is **Step 40**)*

- **Date:** 2026-08-11
- **Directed:** "i'm going to log in with another account, so please save this, so that when I
  re-join, we can pick up with OI-40."

### ▶ First task next session

**Close OI-40 — re-test every "latest edition" count as-of a date.**

Step 30 established that *"latest package per jurisdiction"* describes a **future** state: the
corpus holds **82 state packages effective after today**. That error survived both independent
derivations *and* my own gate 335. Several load-bearing figures were measured that way and have
**not** been re-tested. Until they are, they cannot size a phase or seed a class list.

**Specific figures to re-test, in priority order:**

| Figure | Where it is stated | Why it matters |
|---|---|---|
| Territory resolution — *"all 51 resolve: 27 ZIP · 20 constant · 4 county/place"* | `README.md`; build plan §12 phase 3 exit criterion; `ERC-TER-001` | It is a **phase exit criterion**. If the scheme mix differs today vs 2027-04-01, phase 3 is mis-specified |
| Table population — *"138 of 272 countrywide rate tables are header-only"* (N7) | build plan §4 N7 | Drives load-time assertions. Also re-check the per-subline layer tables in all three gates |
| Class inventories — 238 pre-2027 only / 204 2027-only / 959 both | `README.md` #4; `31_migration_asof.py` | Already measured as-of; **confirm** the derived counts elsewhere agree |
| Rating-vs-capture — **16 / 383 / 78** | build plan §3, §13; `README.md` #5 | Taken over all **572 package directories** (not "latest"), so probably unaffected — **verify, do not assume.** It is the headline scope number |

**Method:** extend `scripts\erc_migration_asof.py`, which is the pattern — **as-of date as a
required input, never a default.** Report today / 2027-04-01 / end-state for each figure, as it
does. Anything that differs across those columns is a claim that needs its tense fixed.

**Then:** phase sizing, which OI-40 gates and which has now been deferred three sessions.

### After that

Build-order item 4, **Liquor Liability (332)**, with a **prediction already on the record**:
`LiquorELPText` carries only `Industry` and `Company` — **no `Rate/Loss Cost Applies` anywhere** —
so N17 predicts liquor is *entirely* ELP-or-refer, with no loss-cost path even in principle. First
gate that tests a stated prediction rather than discovering its finding. Should be fast on the
differential format.

### The open recommendation, not yet decided

I recommended: **OI-40 → 332 gate → then stop gating and build Phases 0–2** (domain types,
ingestion, resolver), letting gates 5–11 land against working code rather than only describing it.
The argument for building now is that the resolver has been stress-tested hard by three gates —
as-of selection, declared-parent resolution, both inheritance mechanisms, empty overrides — and it
is where the expensive mistakes live. The argument against is that **every gate so far has changed
the architecture** (N15, N16, N17, per-subline premium strategies, edition-scoped calculators).

**The user has not chosen.** Continuing to gate all the way to item 11 before any code is equally
defensible. Ask before assuming.

### Where to start reading

| Artifact | Why |
|---|---|
| `docs\gates\RECONCILIATION.md` **§1** | The as-of defect, in full. Read this before touching any count |
| `scripts\erc_migration_asof.py` | The measurement pattern to extend |
| `docs\OPEN-ITEMS.md` **OI-40** | The item itself, and OI-39 above it for how the error was found |
| `docs\GL-RATING-ENGINE-BUILD-PLAN.md` §4 (N1–N17), §9 (the seven habits) | Non-negotiables and the gate format |
| `docs\gates\GATE-33*.md` | The three passed gates; 336 shows the differential format to copy |

Governed by the standing criteria at the head of this log: **ERC is the source, the manual only
confirms, nothing is assumed — read the file rather than inferring from its name** — plus the seven
habits in build plan §9, of which habit 1 (resolve the declared parent first) has changed the answer
in all three gates.

### State at pause

**Settled:** build doctrine · evidence hierarchy · **17 non-negotiables** · architecture · resolver ·
premium chain (edition-scoped; **not** universal — OCP is piecewise) · rounding sites · territory for
all 51 · rating-vs-capture 16/383/78 · build order of 13 · 18 phases · **three subline gates passed
(334, 336, 335)** · the golden case runnable (`testserify_golden.py`, **80/80**) · both
specifications reconciled by annotation · four agent invariants rescoped.

**Escalations:** **E1** (rounding tie-break — now *live*, a real submission hits an exact midpoint) ·
**E4** (`Status`, cosmetic) · **E11** (is 334's omission of `AdditionalInterestFactor` intended?) ·
**E14** (`LookupPrincipalsProtvLiabFactor` has no caller in CW 2027). **E12 closed** — the eighth to
dissolve on being read.

**Open items:** 40 in the register. Live ones that gate work: **OI-40** (as-of re-testing) ·
**OI-37** (terrorism population audit, before build-order item 9) · **OI-09** (rounding, priority
raised).

**Still to do:** phase sizing (gated by OI-40) · the three state-specific coverages (MD, MA lead)
still unread · gates for build-order items 4–13.

**Not started:** any engine code.

### Verification at pause — all green

`testserify_golden.py` **80/80** · iso-circular-expert **15/15** · iso-erc-expert **88/88** ·
both invariant files valid JSON · **zero broken links** across all documentation ·
`docs\GL-RATING-ENGINE-DOCS.html` regenerated with five tabs.

---

## Step 32 — OI-40 closed, and phase sizing done

- **Date:** 2026-08-11
- **Directed:** "Pick up with OI-40: re-test every 'latest edition' count as-of a date… Then phase
  sizing, which OI-40 gates."

Two artifacts: **[`docs/gates/OI-40-ASOF-RECOUNT.md`](docs/gates/OI-40-ASOF-RECOUNT.md)** and
**[`docs/PHASE-SIZING.md`](docs/PHASE-SIZING.md)**. Two new scripts,
`scripts/erc/32_asof_recount.py` and `33_phase_sizing.py`, both taking the as-of date as a
**required** argument.

### OI-40 — five figures re-measured at today / 2027-04-01 / end state

| Figure | Verdict |
|---|---|
| Territory **27 ZIP · 20 constant · 4 county/place** | ✅ **Survives.** Identical at every date the corpus covers. Phase 3's exit criterion stands |
| The **16** rate-driven groups | ✅ **Survives**, and as a *set*, not just a count — identical at all four measurements |
| N7 *"138 of 272 countrywide tables header-only"* | ❌ **A 2027 number.** Today it is **111 of 266** |
| *"238 pre-only · 204 2027-only · 959 both"* | ⚠️ **True from 2027-04-01.** Today: one list of **1,197** codes, no split |
| *"477 groups: 16 · 383 · 78"* | ⚠️ **A union over every edition ever filed.** In force today: 458 groups. **And separately two short — see the coda below** |

**Two of four survived, which was worth measuring rather than assuming either way.** The audit was
opened on the premise that everything measured with "latest" was suspect; territory and the
rate-driven set were not, and now that is known instead of hoped.

**The as-of defect turned out to be one instance of a wider one.** Three findings in this pass are
not about dates at all:

- **Delaware is filed under a fifth table name.** The first territory classifier returned **19**
  single-territory jurisdictions, not 20, because DE keeps its constant `001` in
  `DomainPremOpsTerritory` and not `DomainPremisesOperationsTerr`. Five distinct names carry the
  premises/operations rating territory across the corpus.
- **There is no date at which "the countrywide parent" is singular.** Three declared parents are in
  force today, three at the cliff, and **for five states today the declared parent is not the
  newest** — habit 1 is the only thing that catches them.
- **The corpus has an as-of floor.** All 51 jurisdictions resolve only from **2022-09-01** onward;
  at 2021-06-01 only 9 do. A resolver that falls back instead of failing would rate a 2021 Wisconsin
  risk on a 2022 filing with no signal. **OI-41.**

**Also closed: OI-19 and OI-20**, both by running the sweep each had recorded as outstanding.
`PremOpsLossCost` is header-only in **CA, NJ, NY and OH**, which file **66,573 rows** under
`PremOpsLossCost<ST>Terr<nnn>` — measured corpus-wide and as-of, which is what OI-20 asked for in
its own text. **It was re-derived from the files before the register was read.**

### Phase sizing — three findings that change the plan

**Three countrywide calculators, not two.** Gate 334 concluded *"both CW 2023 and CW 2027
calculators required"*, from a whole-corpus parent census. Restricted to the parents in force, the
split is **V02 / (V03 = 20260101, byte-identical) / 2027** — and the odd one out is not the newest,
it is **`GL_CW_20231201_V02`, held by California alone**. All 100 Prem/Ops rule *names* match
between V02 and V03; **40 of the 100 bodies do not**, including an `IsNull` guard on
`SetPremOpsLossCost` that decides whether a supplied loss cost gets overwritten. **Gate 334 derived
V03** — the OK golden case declares it — so nothing in the project currently tests V02.

**California is the outlier in three independent ways**: sole holder of V02, one of the four sharded
loss-cost states, and one of the four county/place territory states.

**Build-order item 6 is the second-largest item in the build.** Product Withdrawal / LoED / Cyber
carries **320 countrywide rules across three distinct rule sets** and **178 state rule names in 42
jurisdictions** — more countrywide rules than 334, 336 and 335 combined. It sits at position 6 with
a one-line note about ordering. It should be three sublines.

**Item 11 has a fourth coverage.** **New York's Special Protective and Highway** coverage is
`RATE_DRIVEN`, exists in **no countrywide edition**, and is filed by NY alone — and its DataDefGroup
carries no state name, which is why three gates read it as countrywide. NJ and RI lead coverages
were checked against `rating_vs_capture.csv` and do **not** rate, so item 11 is exactly four
coverages in three states.

### Findings

- **Habit 1's failure mode has a general form: a name was trusted where a file should have been
  read.** N4 ("latest is not now") is a special case of the standing criterion, not a separate rule.
  Every defect in this pass fits it.
- **Equal counts are not equal content, and this nearly shipped.** The first phase-sizing script
  compared *rule counts* across countrywide parents and reported five phases as single-calculator.
  Comparing whitespace-normalised *bodies* showed all five were wrong. One line, five phases.
  Recorded into **N11**, which previously covered only printed rule numbers.
- **The project's fastest source of new findings is its own back-catalogue of unfinished ones.**
  Two of this session's findings — the sharded loss-cost tables (OI-20) and the unswept edition
  counts (OI-19) — were already written down as incomplete, and were re-derived from scratch before
  the register was consulted. **Sixth rediscovery.** A pass over every `AUDIT`-status item asking
  only *"has the sweep this asked for actually been run?"* is likely cheaper than the gate that
  rediscovers each one.
- **`knowledge/territory.json`'s own `_note` said the scheme classification had been "CORRECTED" by
  hand with no script behind it.** That was the warning that a phase-3 exit criterion had no
  reproducible derivation. It is derived in code now, and the hand classification was right — 51/51.

### The open recommendation — **decided**

Step 31 left a question for the user: after OI-40 and the 332 gate, keep gating through
build-order item 11, or stop and build Phases 0–2? My recommendation was to build, and phase
sizing added an argument for it — the three-calculator finding and the untested V02 path are both
resolver-shaped.

**The user chose to keep gating**, on the grounds that no code exists yet — and then made it a
**standing instruction**: *"note that I don't want you to build until I tell you to."* **No engine
code is written until the user says so. That is not a per-session preference and this log is not to
re-open it.** Recorded at the head of the build plan as well, so it does not depend on anyone
reading this entry. Analysis, measurement scripts, gates and documentation all continue. The counter-argument was already the stronger one on the
record: **every gate so far has changed the architecture** — N15, N16, N17, per-subline premium
strategies, edition-scoped calculators — and today's session added N11's extension and a third
calculator. Building a resolver against a spec that has changed at every gate would mean writing it
twice. **Next: build-order item 4, the 332 Liquor gate.**

### Open items

- **OI-40 CLOSED** · **OI-19 CLOSED** · **OI-20 CLOSED** · **OI-41 opened** (as-of floor 2022-09-01).
- Register now has 41 items. Live ones that gate work: **OI-37** (terrorism audit, before build-order
  item 9) · **OI-09** (rounding).
- **Phase sizing is done**, after three deferrals.

### Coda, same session — the headline was 16 and it is 18

Asked *"what remains, and what are the remaining gates?"*, I listed the build order against the
rate-driven groups and **they disagreed**: build-order item 7, **Unmanned Aircraft**, is on the list
as a rating subline and owned **no** rate-driven group. The build order was right.

`25_rating_vs_capture.py` decides *rate-driven* by matching the premium-writing rule body against a
list of rate-shaped source names — `FinalRate`, `BaseRate`, `LossCost`, `ELP`, `AdjustedBaseRate`.
**`AdjustedRate` was not on the list.** Two coverages compute

```
Premium = AdjustedRate × (ILF − DeductibleFactor) × PackageModFactor × ExperienceMod × …
```

and were filed as *aggregators* for that reason alone: `GeneralLiabilityUnmannedAircraftCovABIPDCoverage`
and `…CovBPAICoverage`, 116 packages each. Re-run corpus-wide over the same 572 directories with
`AdjustedRate` added, **exactly two groups move: `18 · 383 · 76`.**
`GeneralLiabilityCompositeRating` also matches a rate-shaped name and **stays** in the aggregators —
`Premium = FinalCompositeRatingPremium − TotalClassificationsPremium` is genuinely a difference. Read,
not pattern-matched.

**This is not an as-of defect and OI-40's date-stability finding is unaffected.** But it is a
finding *about* OI-40's method, and the sharper one:

> **A re-test that reuses the original instrument can only find dating errors, never method
> errors.** The rate-driven set passed every as-of check in the OI-40 document and was still two
> short, because the re-test and the original shared a classifier with an incomplete source list.
> This is `RECONCILIATION.md` §1's *"both sources agree is not both sources are right"* — reproduced
> by agreeing with myself.

**And N13's oldest confirmed sentinel sits on this path.** The drone `0`-above-55-lb refer sentinel
has been on the record since the comparison pass, on a coverage the scope measurement classified as
*not rating*. The sentinel register and the rating inventory were describing the same coverage and
disagreeing about whether it rates. Nobody read them side by side until the gate list was written
out.

Regex corrected in `25_` and `32_`, both re-run; build plan §3/§8/§12/§13, README #5, OI-40 §1/§5/§8,
RECONCILIATION §1 and this log updated. **OI-42** opened and closed.

### Verification

`tests/verify_golden.py` **80/80** · iso-circular-expert **15/15** · iso-erc-expert **88/88** ·
`docs/GL-RATING-ENGINE-DOCS.html` regenerated with **seven** tabs. Neither agent asserts the
rating-split figure, so the 16 → 18 correction touched no smoke test.

Link check across all 44 markdown files reports six hits, all in `docs/erc/01` and `05`, and all
**false positives** — they are regex fragments in prose (`[A-Z]{2}`, `\d{8}`, `V\d+`) that the
checker's link pattern matches. **Zero real broken links**, confirmed by reading them rather than
by trusting the count.

The circular agent's smoke test carries two new comments rather than new assertions: its
*"15 pre-2027 / 36 on the 2027 basis"* case is a fact about the **notice** corpus and stays, now
labelled as the end state; and its territory case notes that the PDF and ERC derivations reach
27/4/20 independently.

---

## Step 33 — The 332 Liquor gate

- **Date:** 2026-08-11
- **Directed:** "move on to liquor, after every gate, show the full list of remaining gates"

**[`docs/gates/GATE-332-LIQUOR-LIABILITY.md`](docs/gates/GATE-332-LIQUOR-LIABILITY.md).** Fourth
subline gate, differential format, **as-of 2026-08-11** stated up front. Derived against
`GL_CW_20231201_V03` — the parent the OK golden case declares, not the newest (habit 1).

### The prediction held, and testing it was still worth the gate

Step 31 predicted from `LiquorELPText`'s vocabulary that liquor is entirely ELP-or-refer. **Confirmed
three ways**, and the third is stronger than what was predicted:

- **The vocabulary** — `Industry` ×251, `Company` ×111, **362 rows, 51 of 51, no
  `Rate/Loss Cost Applies`.** Doubles to 744 rows at the cliff and stays two-valued.
- **The inventory** — no `Liquor*LossCost` table exists in any jurisdiction at any edition.
- **The rule** — **`SetBaseRate` has no loss-cost branch at all.** The prediction was that no class
  would *say* `Rate/Loss Cost Applies`; the finding is that **there is no branch that would consume
  it if one did.** N17's selector is written for liquor and read by no rating rule.

**And the manual settles it in one sentence** — `GL-MU-2027-RU-001-C` p.95, Rule 45.E:
*"For rates, refer to company."* Checked rather than assumed, that sentence appears three times in
the manual (Rules 42, 43, 45), so **"company rates" is a recognised ISO category** and the engine
needs one company-rated strategy, not a liquor special case.

**N17 corroborated a fourth time, 362/362 exact** — `Company` → ELP `0` (111/111), `Industry` → ELP
> 0 (251/251) — and on the subline with no loss-cost path, which is what finally pins `Company` as
*refer to company*.

### Five things nobody predicted

- **E17 — a sentinel is not a constant.** The refer marker is `Refer To Co.` in all nine pre-2027
  countrywide editions and `Refer to Company` in CW 2027, and **on 2027-04-01 both are live in the
  corpus at once**. A global sentinel constant is wrong for 8 or 43 jurisdictions. Now **N18**.
- **OI-43 — and ISO made exactly that mistake.** `SetLiquorExposureStatCode` in CW 2027 still tests
  the pre-2027 strings, so the ÷1000 reporting divisor never selects and **2027 liquor exposure is
  reported 1,000× too large.** Premium correct, statistical report wrong. `SetPremium` was updated in
  the same edition and the same file — an incomplete rename. **The first defect found inside a filed
  ISO artifact rather than inside our own reading of one.** Not patched: the engine implements the
  rules as filed, and a fix would disagree with RAaS.
- **OI-44 — a guard that covers less than half its defect.** All **21** liquor deductible factors are
  `0`; `DoMessageMustEnterLiquorDeductibleFactorOverride` covers **10**. Ten *Per Common Cause*
  options are zero and unguarded, so those insureds are **overcharged** with no message. 334 found
  this pattern with the guard matching the defect exactly; this is the first under-cover.
- **E15 — `LiquorLCM = 1` is a company input wearing a rate table's clothes.** One countrywide row,
  no state override at any edition. `BaseRate = ELP × 1 = ELP` is an ISO expected-loss figure, not a
  price. **Narrower than the closed E9**, which dissolved because the LCM tables were *empty*; here
  the table is populated with a value that looks legitimate.
- **N3 extended — an override need not be empty to neutralise.** New York disables claims-made liquor
  with **constant stubs** (`YearInClaimsMade = 0`, `ClaimsMadeMultiplier = 1.0`) plus an
  occurrence-only `SetBaseRate`. My first pass flagged NY by body length and would have filed it as an
  empty override; reading the body corrected it. A claims-made liquor risk in NY prices at **`0`,
  silently** — a coverage form the state does not offer, returned as a free policy.

### Corrections to the record

- **The build plan's escalation register still showed E12 as open.** Gate 336 closed it and
  `RECONCILIATION.md` records the closure; the register was never updated. Fixed — and **gate 332
  reproduces E12's structure exactly**: `LiquorELP` is a string selector at classification level and
  a decimal rate table at coverage level, the same two-DataDefs-one-name shape that dissolved it.
- **E14 reframed.** Two more uncalled lookups (`LookupNoDedStatCode`, `LookupPremOpsLCM`) make three
  across three sublines. It is a corpus habit, not a deletion defect.
- **Illinois generalises OI-20 beyond loss costs.** IL ships no `ILFLiquor`; it overrides
  `LookupILFLiquor` to read `ILFLiquorStException` — **and that table has a different key arity**,
  `AggregateLimit` alone where countrywide keys on three columns. Resolve the lookup *rule*, never the
  table name.

### The zero taxonomy is now seven, and that is the problem

Two more meanings: a **genuine** zero (`LiquorLiabGrade = 0` = *no cause of action against the liquor
vendor*, manual-confirmed p.101) and a **coverage-not-offered** zero (NY claims-made). **Enumerating
meanings has stopped paying.** The liquor deductible case shows a discriminator can exist and still
miss half the defect, so N13/N15 now say to record **a discriminator's coverage against the defect**
rather than to add an eighth meaning.

### Layer pattern inverted

**The first subline whose rating operands live countrywide.** `DedFactorLiquor` (21), `LiquorLCM` (1),
`ProdsCompldOpsMinPremium` (3) and `ProdsCompldOpsClaimsMadeMultiplier` (5) are countrywide and
**empty in all 51 states** — the exact inverse of 334/336/335. Class-specific numbers stay
state-supplied, so N8 holds, but README #1's *"the countrywide layer holds almost none of the
numbers"* is qualified.

### No oracle

The golden case carries liquor with `CoverageOnPolicyIndicator = 0`, which exercises and **confirms**
exactly one branch. Second subline gated without an oracle, after OCP. `verify_golden.py` stays at
**80/80** — nothing was added, because there is nothing to assert against.

### Open items

**OI-43**, **OI-44** opened. **E15**, **E16**, **E17** raised; **E12** closed in the register (late);
**E14** reframed. **N18** added; **N3**, **N13**, **N15** extended. Register at 44 items.

### Verification

`tests/verify_golden.py` **80/80** · iso-circular-expert **15/15** · iso-erc-expert **88/88** ·
`docs/GL-RATING-ENGINE-DOCS.html` regenerated with **eight** tabs.

---

## Step 34 — The 335 Railroad Protective gate

- **Date:** 2026-08-11
- **Directed:** "log, and continue to rail road protective"

**[`docs/gates/GATE-335-RAILROAD-PROTECTIVE.md`](docs/gates/GATE-335-RAILROAD-PROTECTIVE.md).** Fifth
subline gate, as-of 2026-08-11, derived against `GL_CW_20231201_V03`.

### The strongest evidence this project has produced is eighteen numbers

Alaska's ERC `BaseELPRR` table, from a **2026** package, against Procedure 5.E of
`GL-AK-2020-LC-001-C`, a **2020** filed PDF: **all 18 rate cells identical to the cent** across three
class codes and six train-per-day bands. And `40014` is correctly **absent from both** — the manual
derives it rather than tabulating it, and ERC's `SetBaseELPRR` excludes it for that reason.

Every previous cross-source confirmation was **structural** — a formula shape, a vocabulary, a class
list. **This is the first confirmation of rate *values*, cell by cell**, and it tests the extraction
rather than the reading. Three more matched exactly: the work-trains rate **$56.80**, the supervisors
extension **10%**, and **150% of the loss cost for class 16292** — all hardcoded in ERC, all printed
in the ELP Supplement.

### Habit 6 stopped a confident, wrong finding

I searched the multistate **rules** manual for the work-trains rate across all four editions, found
nothing, and was about to write *"ERC implements rating machinery the filed manual does not
describe"* — the inverse of every disagreement so far, and a striking claim. **It was wrong.** The
whole procedure is in the **ELP Supplement**, a different document in the same corpus. Rule 49 says
*"refer to company"* for basic-limits rates *because* the ELPs live in the loss-cost notices.

**Absence from the document you searched is not absence from the corpus.** Third time habit 6 has
changed an answer.

### N17 has a counterexample

**Railroad has no `RailroadELPText`.** N17 said *"**Every** subline carries a sibling selector"*;
exactly four `*ELPText` tables exist and N17 already named all four — the rule was written from an
enumeration and then stated universally. An engine asserting it at load time would **hard-fail on
railroad**, which N17 says a disagreement must do.

Narrowed to *the sublines publishing both a loss-cost and an ELP path*, with **absence of a selector
as itself the signal that a subline is ELP-only** — and the manual says why: Rule 49.E.1, *"Refer to
company."*

**Three of this project's rules have now over-generalised in the same direction** — *"latest" means
now* (OI-40), *"the" countrywide parent* (singular), and now *"every"* subline. The pattern is
stating a universal from a complete-looking enumeration.

### One gate's subject caused another gate's finding

**Railroad shares subline code 335 with OCP** — Rules 46 and 49 of the same manual — and reads OCP's
loss-cost table via `LookupOwnersContractorsLossCost("16292")`, hardcoded. Gate 335 (OCP) established
that this table is **withdrawn in 43 jurisdictions on 2027-04-01**. So railroad had to move, and CW
2027 **deletes `LookupOwnersContractorsLossCost` and adds `LookupOwnersContractorsELP`.**

Gate 335 found the cause and could not have seen this consequence; this gate found the consequence
and could not have explained it without 335. **That is the argument for gating in a fixed order.**

It also **confirms OI-21 from the manual side**: subline codes **325**, **335** and **350** each
cover two rules. *A coverage is identified by its DataDefGroup, never by its subline code.*

### Also found

- **The largest edition change of any subline: 65 rules → 46.** CW 2027 deletes work trains,
  supervisors/inspectors, the minimum premium and the entire mixed-hazard machinery, and moves the
  base rate to `BaseELPRR × LCM` — **the same shape as liquor**. The 2023 and 2027 railroads are
  close to different coverages.
- **`RailroadLossCost` has no purpose at all** — present in all ten countrywide editions, 0 rows
  everywhere, and **referenced by no rule in the corpus**. N7's third form, after *presence ≠
  population* and *empty ≠ absent data*.
- **N11 at its purest:** `SetBaseELPRR40014` tests class `40011` and writes a DataDef named
  `BaseELPRR40006` — and `40006` is *"Miscellaneous"*. The rule names refer to the rate basis
  applied; the DataDef names refer to nothing.
- **A countrywide dollar rate exists.** `WorkTrainsOrOtherRREquipmtRate = 56.8` per $1,000 is not a
  factor or a placeholder, and the manual confirms it to the cent. README #1's *"no national loss
  cost publication at all"* is qualified.
- **E15 and E16 generalise** — `LCM = 1` and a structurally zero minimum premium appear in both
  liquor and railroad, so they are properties of ELP-rated sublines. And **E14 gets a cheaper
  explanation**: `LookupPremOpsLCM` is the *same* dead lookup copy-pasted into both files.
- **The smallest deviation surface of any subline** — 2 jurisdictions (AK, NY), 3 rules each, and the
  only substantive one is a statistical-coding rule. `BaseELPRR` has **exactly 18 rows in all 51**.

### Open items

**OI-45** opened (non-construction railroad operations are a manual-only referral with no ERC
discriminator). **OI-21 confirmed.** **N17 narrowed**; **N7**, **N11** extended; **E14**, **E15**,
**E16** generalised. Register at 45 items.

### Verification

`tests/verify_golden.py` **80/80** · iso-circular-expert **15/15** · iso-erc-expert **88/88** ·
`docs/GL-RATING-ENGINE-DOCS.html` regenerated with **nine** tabs. **No oracle** — the golden case
carries railroad switched off, the third subline in a row without one.

---

## Step 35 — The item-6 gate, and a correction to my own phase sizing

- **Date:** 2026-08-11
- **Directed:** "save to log, then move on to Gate 6"

**[`docs/gates/GATE-365-WITHDRAWAL-LOED-CYBER.md`](docs/gates/GATE-365-WITHDRAWAL-LOED-CYBER.md).**
Sixth subline gate — three coverages, six rate-driven groups, one document.

### The gate opened by withdrawing my own figure

Phase sizing reported item 6 as **320 countrywide rules / 178 state rules / 42 jurisdictions** and
recommended splitting it into three build-order items on that basis. **The measurement was wrong.**
The sizing script matched DataDefGroups by *substring*, and `ProductWithdrawal` also matches **19
endorsement, coverage-form and minimum-premium groups** carrying 167 further rules — work belonging
to items 8, 12 and 13.

**The real rating core is 150 / 17 / 9.** Item 6 is still the largest single rating item (against
334's 100) but has a *small* deviation surface, not the widest. The script now intersects every
match with the RATE_DRIVEN set. **The split recommendation survives on different grounds:** the six
groups share a rule-name skeleton and **zero identical rule bodies**.

**Third instance this session of the same error**, after Delaware's territory table and the
`AdjustedRate` omission — and the first one that had already reached a plan document.

### And a correction to yesterday's gate, filed hours earlier

While reading Product Withdrawal's selector I found that **the railroad gate's §1 was wrong.** It
reported *"N17 has a counterexample — no `RailroadELPText` exists"*. The table doesn't exist; **the
selector does**, as the `RailroadELP` table whose value column is named after itself, `Industry` in
all 204 rows across 51 jurisdictions at every date. **I searched by name, found nothing, and
reported absence — in the gate that criticises exactly that reasoning twice.**

Re-enumerating selectors **by content** — sweeping every rate-table column for the closed vocabulary
— finds **seven**, not four: the four `*ELPText` tables, plus `RailroadELP`,
`SpecialProtectiveHighwayELPText` (NY only, `Company` in all 3 rows) and `PremOpsELPTextTerr001`
(**NY shards its selector by territory** — OI-20's pattern applied to a selector).

**N17 is restored and widened rather than narrowed**, and the amendment now says *enumerate by the
vocabulary, never by table name*. It also delivered an item-11 finding early: NY's Special
Protective and Highway coverage is **entirely refer-to-company**.

### The architectural finding: factor-on-host is a kernel requirement

`SetAdjustedBaseRate` in the LoED and Cyber groups reads **five computed values out of its host
coverage group** — `PremOpsLossCost`, `PremOpsELP`, `LCM`, `ClaimsMadeMultiplier`,
`PremOpsSizeOfRiskFinalRelativity`. So:

- **Coverage groups are not independently evaluable.** The kernel must expose resolved sibling state
  and evaluation order across groups is part of the algorithm. **E18** — it changes the architecture,
  not the arithmetic, and §5 never said so.
- **Item 6 depends on item 10.** `PremOpsSizeOfRiskFinalRelativity` is Size-Of-Risk output (OI-04,
  build-order item 10). A build order derived from coverage structure has a data dependency running
  four items backwards. **OI-46** — a resequencing decision for the user.
- **A host's edition-scoped behaviour propagates** to its dependants without their expressing it.

### A misspelling that must not be tidied

ERC writes **`ProductWithdrawl`** 16 times against `ProductWithdrawal` 10, and it reaches DataDef
names *and* a rate table name. **`ProductWithdrawlFactor` is not a duplicate** — different key,
different values, and all three factor tables have readers. **And the misspelled one is the one the
filed manual prints**: `GL-MU-2027-RU-001-C` p.93 Table 44.B.3.b, A 0.20 · B 0.15 · C 0.10, exact on
values and key axis. Normalising the spelling would merge three distinct tables. **OI-47.**

### Also

- **Second orphan table**: `SublineProductWithdrawal` — 0 rows every edition, 0 readers — after
  `RailroadLossCost`. Two instances make it a load-time check. **N7 extended to *presence ≠
  population ≠ purpose*.**
- **The hazard-grade tables are the largest countrywide rate tables in the corpus** — 1,188 rows,
  dropping to 1,163 in CW 2027, which is exactly the Prem/Ops class list on each basis. Countrywide
  national class-level data, overridden only by New York.
- **Product Withdrawal borrows its host's selector** — `SetProductWithdrawalELP` calls
  `LookupProdsCompldOpsELPText` — and is the first coverage to read a selector *inside the rating
  chain to branch*, rather than write it to output and ignore it.
- **E15 and E16 hold for a third subline.** `ProductWithdrawalLCM = 1`, `ProductWithdrawalMinPremium
  = 0`.

### Open items

**OI-46**, **OI-47** opened; **E18** raised. **N7** extended; **N17 restored and widened**;
**E15**/**E16** generalised to three sublines. Register at 47 items.

### Verification

`tests/verify_golden.py` **80/80** · iso-circular-expert **15/15** · iso-erc-expert **88/88** ·
`docs/GL-RATING-ENGINE-DOCS.html` regenerated with **ten** tabs. **No oracle** — fourth consecutive
subline without one; the OK policy exercises 334 and 336 only.

---

## Step 36 — The 370 Unmanned Aircraft gate: N13's oldest sentinel, closed

- **Date:** 2026-08-11
- **Directed:** "Ok, log and move on to #7"

**[`docs/gates/GATE-370-UNMANNED-AIRCRAFT.md`](docs/gates/GATE-370-UNMANNED-AIRCRAFT.md).** Seventh
subline gate, as-of 2026-08-11, derived against `GL_CW_20231201_V03`.

### The drone sentinel is decoded, and N13 undercounted it

The drone `0` has been the one entry in the zero taxonomy with **no in-corpus discriminator** since
the cross-derivation comparison first raised it. This gate settles it against
`GL-MU-2027-RU-001-C` p.68, **Table 37.E**:

**12 rows × 2 columns, 24 of 24 cells agree, and the mapping is total in both directions** — every
ERC `0` is an `RTC` and every `RTC` is an ERC `0`. **`0` means refer-to-company, and nothing else.**

Three things the previous three-zero version of N13 could not say:

- **There are five BI/PD zeros, not three** — plus three more on the PAI side. The two N13 missed
  are *"Entertainment, demonstrations, special events, sports"* and — worse — **`Other usage, not
  otherwise classified`**, the catch-all a submission lands on when nothing else fits. **The most
  likely usage value in production is a referral marker that prices at zero.**
- **The same usage means different things in adjacent columns.** Firefighting is `RTC` for bodily
  injury / property damage and **0.90** for personal & advertising injury. So a sentinel register
  keyed on *(table, value)* is wrong; it must be keyed on **(table, column, row)**.
- **There is definitively no in-corpus discriminator** — zero `DoMessage*` rules in either
  rate-driven group, and the subline's only guard is `MaximumTakeoffWeight <= 0`. Verified
  exhaustively rather than sampled, so the register can stop carrying it as unfinished.

**A confirmed-sentinel register is only as good as its last recount.** That entry had been carried
unchanged since the comparison pass and was wrong by two rows the whole time.

### E1 can be closed per-subline

`maximumTakeoffWeightCeiling = round(w + 0.499, 0)` produces an exact midpoint only at
`w = n + 0.001`. Working that against the loss-cost band edges — **1, 5, 15, 55** — both tie-break
candidates land in the same band at every realistic weight; only a **0.001 lb** drone differs.

**So E1 is live globally and provably dead here.** That is a cheaper answer than waiting for RAaS,
and the other sublines deserve the same treatment rather than a blanket "configurable".

### Also

- **Unmanned Aircraft is company-rated in its entirety** — Rule 37.C.2: *"All applicable loss costs
  and modifiers … must be referred to company before using."* Fourth subline after liquor, railroad,
  and Rules 42/43. **E15 and E16 now four for four** (`LCM = 1` via the Prem/Ops lookup;
  `UnmannedAircraftMinPremium = 0`).
- **`LookupPremOpsLCM` is live here** and inert in the liquor and railroad files — which confirms
  the E14 reframing precisely: **boilerplate copied into every subline file**, live where used.
- **A third kind of inert artifact**: `SetmaximumTakeoffWeightCeiling` is a *called* rule with an
  empty body and a developer comment shipped in the filed data — *"Logic … moved to be inline where
  used."* Distinguishable from N3's deliberate empty overrides **only by the comment**, and comments
  are not data.
- **`SetAjustedRate` is misspelled** and its target DataDef `AdjustedRate` is not — which is exactly
  why OI-42's fix worked. Third ERC misspelling after `ProductWithdrawl` and the stale
  `Refer To Co.`
- **Eight states file one deviation.** IN, MO, MT, ND, NH, OK, TN and UT file an *identical*
  governmental-units ILF override. **The phase-sizing state-rule counts count filings, not distinct
  behaviours** — the same conflation as the item-6 substring error, one level down.
- **New York deviates for the third time** (liquor claims-made stubs, a sharded Prem/Ops selector,
  now the drone claims-made multiplier). **NY needs a differential fixture** alongside California's.
- **The least disturbed subline at the 2027 boundary** — 62 → 66 rules, 8 changed, and byte-identical
  rate tables across all three parents in force.

### Open items

**OI-48** opened (no "highest modifier wins" logic — a submission-rule question for the user).
**OI-45 merged into OI-49**, now a single pattern: *manual-only referral conditions with no ERC
discriminator*, two instances. **N13's evidence line rewritten.** Register at 49 items.

### Verification

`tests/verify_golden.py` **80/80** · iso-circular-expert **15/15** · iso-erc-expert **88/88** ·
`docs/GL-RATING-ENGINE-DOCS.html` regenerated with **eleven** tabs. **No oracle** — fifth
consecutive subline without one.

---

## Step 37 — Build order resequenced: Size-Of-Risk to item 8

- **Date:** 2026-08-11
- **Directed:** "make size of risk #8, and move the rest down 1"

**Done. Thirteen build-order items become fourteen**, and **OI-46 is closed by the decision.**

| New | Item | Was |
|---|---|---|
| 1–7 | 334 · 336 · 335 OCP · 332 · 335 Railroad · 365 · 370 — **all gated** | unchanged |
| **8** | **Size-Of-Risk** | *split out of item 10's rating-plans bundle* |
| 9 | Refer-to-company coverages | 8 |
| 10 | Terrorism | 9 |
| 11 | Rating plans — Schedule · Experience · Composite | 10, **minus Size-Of-Risk** |
| 12 | State-specific rating coverages | 11 |
| 13 | Capture harness | 12 |
| 14 | Policy assembly | 13 |

**Why it matters, from gate 365 §2:** item 6's Loss Of Electronic Data and Cyber coverages read
**`PremOpsSizeOfRiskFinalRelativity`** out of their *host* coverage group (E18) — Size-Of-Risk
output. The build order was derived from coverage structure and therefore carried a data dependency
running **four items backwards**. Placing Size-Of-Risk at 8 puts it **first in the build queue**,
ahead of everything not yet gated and ahead of any implementation of item 6. Items 1–7 are already
gated, so nothing that has landed moved.

**Size-Of-Risk is well-supplied in ERC** and was never the gap the PDF register recorded (OI-04):
`PremOpsSizeOfRiskRelativity` **8,330 rows** countrywide, `ProdsCompldOpsSizeOfRiskRelativity`
**4,214**. Its own data already shows a pattern this project has since named twice — the
countrywide `*SizeOfRiskLossCost` tables are **0 rows** while NJ ships
`PremOpsSizeOfRiskLossCostTerr501…517` at 1,187 rows each. **That is OI-20's sharded-table shape
inside item 8's own content**, so the gate has a known trap waiting for it.

**Earlier documents keep the numbering they were filed under** — the gates are dated records, and
rewriting them would break the convention that has protected the two derivations' independence
since Step 30. The crosswalk lives at the head of build plan §8. Live documents — build plan §8 and
§12, `OPEN-ITEMS.md`, `PHASE-SIZING.md`, `README.md` — carry the new numbers.

**Phasing renumbered too:** Size-Of-Risk is phase **6**, and the phase count drops from 18 to
**17** because the seven passed subline gates collapse into `5`–`5f`.

### Open items

**OI-46 closed.** **OI-04** annotated as build-order item 8. **OI-37**'s terrorism audit pointer
moved to item 10. **OI-48** remains open and is the only queued decision.

### Verification

`tests/verify_golden.py` **80/80** · iso-circular-expert **15/15** · iso-erc-expert **88/88** ·
zero real broken links · docs HTML regenerated.

---

## Step 38 — Paused. ~~NEXT SESSION STARTS HERE.~~ *(the live handoff is **Step 40**; this entry still holds the item-8 briefing)*

- **Date:** 2026-08-11
- **Directed:** "we are going to pause here, update all docs, including the PRD Doc. For the PRD
  docs, highlight what has changed since yesterday."

### ▶ First task next session

**Build-order item 8 — Size-Of-Risk.** Moved there today at the user's direction; it is the first
thing in the queue because item 6's Loss Of Electronic Data and Cyber coverages read
`PremOpsSizeOfRiskFinalRelativity` out of their host coverage group and cannot be implemented
without it (E18, OI-46 closed).

**A trap is already visible in its data.** The countrywide `*SizeOfRiskLossCost` tables are **0
rows** while NJ ships `PremOpsSizeOfRiskLossCostTerr501…517` at **1,187 rows each** — OI-20's
sharded-table pattern, inside item 8's own content. Resolve the lookup **rule**, never the table
name. ERC is well supplied here and was never the gap the PDF register recorded (OI-04):
`PremOpsSizeOfRiskRelativity` **8,330 rows**, `ProdsCompldOpsSizeOfRiskRelativity` **4,214**. Open
from OI-04: the `Maximum`/`Minimum` relativity and `TableAssignment` tables are 0 rows countrywide
and their source is unknown.

**Method:** as-of date stated up front, `GL_CW_20231201_V03` as the declared parent unless the case
says otherwise, differential against the seven passed gates. **Habit 1 and habit 6 have each
changed an answer today** — resolve the declared parent, and never conclude absence from a search
by name.

### What was done today — Steps 27 to 38

| | |
|---|---|
| **Seven subline gates passed** | 334 · 336 · 335 OCP · 332 Liquor · 335 Railroad · 365 Withdrawal/LoED/Cyber · 370 Unmanned Aircraft — the entire rating core |
| **OI-40 closed** | Every load-bearing count re-measured as-of a date. Two survived, three needed their tense fixed |
| **Phase sizing done** | Three countrywide calculators, not two; item 6 the largest rating item |
| **Build order resequenced** | 13 items → **14**; Size-Of-Risk to #8 |
| **Scope corrected** | 16/383/78 → **18/383/76** |
| **Register** | 37 → **49** items · escalations E1–E10 → **E1–E18** · non-negotiables 14 → **18** |

### Standing constraints, both from the user

1. **No engine code until told.** Recorded at the head of the build plan and in memory. Analysis,
   measurement scripts, gates and documentation continue.
2. **After every gate, show the full list of remaining gates.**

### The open decision

**OI-48** is the only queued question. For drones, the manual (Rule 37.C.2.d) says that where more
than one usage category applies, **the highest modifier wins**. ERC accepts one value per axis and
cannot express it. Either the submission pre-resolves it — a broker question, like OCP's
`WorkersCompensationRate` — or the engine takes a set and picks the max, which ERC does not
license. **Note the interaction:** if the highest-wins rule ran and any applicable category were
`RTC`, the correct outcome is a **referral, not a number**.

### State at pause

**Settled:** build doctrine · evidence hierarchy · **18 non-negotiables** · architecture · resolver ·
premium chain · rounding sites · territory for all 51, re-verified as-of · rating scope
**18/383/76** · build order of **14** · 17 phases · **seven subline gates passed** · golden case
runnable (`tests/verify_golden.py`, **80/80**) · both specifications reconciled by annotation ·
every count in the project dated.

**Escalations live:** **E1** (rounding tie-break — and gate 370 shows it can be closed *per
subline*: proved it cannot bite on drones) · **E4** (`Status`, cosmetic) · **E11** · **E14**
(reframed: uncalled lookups are copy-pasted boilerplate) · **E15** (`LCM = 1` placeholder, four
sublines) · **E16** (structurally zero minimum premium, four sublines) · **E17** (edition-scoped
sentinel spellings) · **E18** (coverage groups are not independently evaluable). **E12 closed** —
and the register had been stale on it until today.

**Open items that gate work:** **OI-37** (terrorism population audit, before item 10) · **OI-09**
(rounding) · **OI-48** (the decision above) · **OI-43** (an ISO defect to raise upstream, not
patch) · **OI-47** (never normalise ERC's `ProductWithdrawl` misspelling) · **OI-49** (two
manual-only referrals with no in-corpus discriminator).

**Still to do:** build-order items 8–14 · a **California** differential fixture (sole `V02` parent,
untested) and a **New York** one (the most-deviating jurisdiction, three separate deviations found).

**Not started:** any engine code.

### Verification at pause — all green

`tests/verify_golden.py` **80/80** · iso-circular-expert **15/15** · iso-erc-expert **88/88** ·
both invariant files valid JSON · **zero real broken links** across 48 markdown files (the six
reported hits are regex fragments in prose, read and confirmed) ·
`docs/GL-RATING-ENGINE-DOCS.html` regenerated with **eleven** tabs.

### Documentation state

All updated today and mutually consistent: `README.md` · `docs/PRD-GL-RATING-ENGINE.md` (**new §0,
"What changed since yesterday"**, plus new stages seven and eight in §3 and rewritten §8 and §9) ·
`docs/GL-RATING-ENGINE-BUILD-PLAN.md` · `docs/OPEN-ITEMS.md` · `docs/PHASE-SIZING.md` ·
`docs/gates/` (7 gates + `RECONCILIATION.md` + `OI-40-ASOF-RECOUNT.md`) · `scripts/README.md` ·
`Agentic/iso-erc-expert/knowledge/` (territory + invariants).

---

## Step 39 — OI-48 decided, and the decision found a bigger sentinel

- **Date:** 2026-08-11
- **Directed:** "Broker Question"

**OI-48 closed.** The unmanned-aircraft highest-modifier rule is a **broker question**: the
submission arrives with **one resolved category per axis** — Ownership & Operation, Usage, Primary
Place of Operation — and the engine never takes a set and picks a maximum, which ERC does not
license it to do.

**Third input to resolve as a submission requirement**, after county/place for CA-FL-NY-TX (OI-34)
and `WorkersCompensationRate` for OCP. The pattern is now worth naming in its own right: **three
things recorded as missing data turned out to be questions for the broker**, and in every case ERC
already provided the way to say *"unresolved"* rather than forcing a guess.

### Checking the decision was implementable found a bigger sentinel

Before recording it I checked whether a broker who *cannot* resolve the categories has a licensed
way to say so. **They do, and it is filed: `Unknown` and `Not Applicable` are ISO domain values on
all three axes, and both price as `0` — refer to company.** So the decision needs no invention: the
ambiguity the manual's highest-wins rule exists to resolve already has a representation in the data.

**But counting those cells exposed that gate 370, filed an hour earlier, had undercounted the
sentinel.** §0 counted the *usage* table and stopped:

| | Cells | `0` |
|---|---|---|
| Usage BI/PD + PAI | 24 | 8 |
| **Ownership & Operation BI/PD + PAI** | 18 | **6** |
| **Primary Place of Operation BI/PD + PAI** | 18 | **4** |
| | **60** | **18** |

**Nearly a third of the drone rating grid is a referral marker**, all 18 multiplying unguarded into
`AdjustedRate` — not the 8 the gate reported. Three kinds: uses ISO will not price (8), the
*non-owned aircraft* condition (2), and **the submission did not say** — `Unknown` ×4,
`Not Applicable` ×4.

### And it withdrew half of OI-49

Gate 370 §4 recorded *"non-owned unmanned aircraft operated by other parties"* as a **manual-only
referral with no ERC discriminator** (Rule 37.C.2.a). **Wrong.** Both ownership-axis tables carry a
`0` against exactly that row. ERC expresses the referral precisely, in the same sentinel form as the
usage cases. **OI-49 reduces to one instance** — the railroad non-construction case.

**Same error as the undercount, one table over:** I checked the axis the finding was about and not
the neighbouring axes. That is the fifth instance today of *looked in one place, concluded about
all places* — and the second time it has been caught by doing something else entirely rather than
by re-reading the claim.

### Open items

**OI-48 closed. OI-49 reduced.** Gate 370 §0, §4 and §7 corrected in place; §7a added carrying the
decision, the recount and the withdrawal. **N13's evidence line updated to 18 cells.** Build plan §7
now names the three-submission-requirement pattern. Register at 49 items, 2 fewer open.

### Verification

`tests/verify_golden.py` **80/80** · iso-circular-expert **15/15** · iso-erc-expert **88/88** ·
docs HTML regenerated.

### ▶ Next session

**Unchanged from Step 38: build-order item 8, Size-Of-Risk** — read that handoff for the trap
already visible in its data. **No engine code until directed.** No decisions outstanding.

---

## Step 40 — Stopping the counting error. ~~NEXT SESSION STARTS HERE.~~ *(the live handoff is **Step 41**)*

- **Date:** 2026-08-11
- **Directed:** "HOW DO WE STOP THIS" — pointing at *"looked in one place, concluded about all
  places"*, five instances in one day.

### The diagnosis is narrower than "read the file, not the name"

The existing habits already say to read the file, and they were followed. Sharpening it against all
five instances gives something more specific — and **checkable**:

> **A search predicate was allowed to define a population, and then a conclusion was drawn about
> that population.**

A filename, a regex alternation, a substring, one table out of a family. **The denominator came
from the query rather than from the corpus**, so anything the query could not see was reported as
absent.

**The discriminating observation: every error was an aggregate or a negative. Not one was a misread
rule body.** The 18 railroad rate cells, the 24 drone cells, the liquor premium chain, the E18
sibling reads — every positive finding today held. Reading a rule *is* the evidence; counting rules
is a claim about a set, and the set was never enumerated.

That also explains why both catches were accidental. **Nothing in the process ever asked "of how
many?"**, so nothing could fail.

### Two rules, one of them enforceable

| | Rule |
|---|---|
| **Writing** | **Every count is "n of N", with N derived from the corpus and named.** *"8 cells"* survives review; *"8 of ?"* does not — and finding the `?` is exactly what surfaces the neighbours |
| **Measuring** | **Enumerate the population, then classify every member.** A negative claim must state what was enumerated and how |

Words alone would not have stopped this — habit 6 already covers the reading half and was broken
twice today. **The as-of defect was fixed by making the script refuse to run without a date, and it
has not recurred.** So the same treatment: **`scripts/erc/34_crosscheck.py`**, now in the
verification routine, with an as-of date required and every check reporting its denominator.

### It worked, immediately, and then caught itself

**First run, two failures.**

- **A rate-driven coverage with no owner.** `GeneralLiabilityClassification` is `RATE_DRIVEN` and no
  build-order item claimed it. It carries the entire **Limited Product Withdrawal Expense** chain —
  **11 rules** — inside the shared classification container instead of a coverage group of its own.
  **Gate 365 enumerated the six groups matching `…Coverage` and missed a seventh path.** It also
  closes that gate's loose end: `SetLmtdProductWithdrawlFactor` is the reader of the misspelled
  `ProductWithdrawlFactor` table whose values match manual Table 44.B.3.b exactly. **OI-50** filed;
  gate 365 §6a added.
- **"79 orphan tables."** Verified before reporting — **all 79 are 0-row schema stubs, and zero
  populated tables are unread.** So the alarming version was itself an aggregate with no
  denominator. **This demotes two earlier gate findings**: `RailroadLossCost` and
  `SublineProductWithdrawal` were reported as notable orphans and are 2 of 79 unremarkable members
  of a class. The claim worth making is the inverse, and it holds: **no populated countrywide rate
  table is unread.** The load-time assertion was corrected to match.

**Then the check caught its own fix.** Claiming `GeneralLiabilityClassification` for item 6 by
substring matched six *other* rate-driven group names — the same over-matching the check exists to
catch, committed inside the fix for it. And claiming the whole group inflated item 6 from 150 rules
to 270, because the container is shared. **Resolution: once a group is shared, the unit of ownership
is the rule, not the group** — the group is allow-listed with its owner named, and sizing stays at
150.

**Three turns of the same screw in twenty minutes.** That is the argument for the machine check over
the habit: the habit was written in the same hour it was broken, twice.

### Recorded

**Build plan §9 now has an eighth habit** — the first seven are about reading, the eighth about
counting — stating the diagnosis, both rules, and that the check found two defects and one
self-inflicted one on its first run. **N7's orphan claim demoted**; the load-time assertion narrowed
to *populated* tables. `scripts/README.md` carries the denominator rule beside the as-of rule.
**OI-50** opened.

### A closing consistency sweep found the same defect once more

Asked to make sure the logs were updated, I ran the counting discipline over the documents
themselves rather than re-reading them. **Three documents carried three different numbers for the
same set** — the escalation register was *"sixteen"* in the build plan, *"eighteen"* in the README
and *"18 (E1–E18)"* in the PRD.

Enumerated: **17 raised** (E1–E12 and E14–E18 — **E13 was deleted before it was filed**, recorded at
Step 28), **8 struck through as dissolved**, 9 rows remaining, of which E7 became build work as N13.
All three documents corrected to 17, with the gap explained rather than papered over.

**Nobody had counted the register; each document had inferred from the highest number.** Which is
habit 8's failure mode wearing its third costume today — an aggregate asserted without enumerating
the set — and the reason the sweep was worth running on a day that was otherwise finished.

Also corrected: three superseded pause markers (Steps 25, 31, 38) still pointed at earlier handoffs.
All now point at Step 40, so there is exactly one live *NEXT SESSION STARTS HERE* in the file.

### Verification

`34_crosscheck.py` **4/4** · `tests/verify_golden.py` **80/80** · iso-circular-expert **15/15** ·
iso-erc-expert **88/88** · docs HTML regenerated.

**Consistency, enumerated rather than asserted:** open-items register **OI-1 … OI-50, no gaps, 50
distinct** · escalations **17 of 18 numbers issued** · non-negotiables **N1–N18, 18 rows** · gate
documents **9** (7 subline gates + reconciliation + the as-of recount) · ERC scripts **35** · build
order **14 items** · phases **17**. Every one of those is a count someone could check.

### ▶ Next session

**Build-order item 8, Size-Of-Risk** — Step 38 has the handoff. Add **OI-50** (Limited Product
Withdrawal Expense) to the queue; it is a small §9 addendum to gate 365, not a new gate. **No engine
code until directed.**

---

## Step 41 — Size-Of-Risk gated. ~~NEXT SESSION STARTS HERE.~~ *(the live handoff is **Step 42**)*

- **Date:** 2026-08-12
- **Directed:** "continue with size-of-risk. Once done list out remaining gates to be worked on"

**Build-order item 8 passed.** [`docs/gates/GATE-SIZE-OF-RISK.md`](docs/gates/GATE-SIZE-OF-RISK.md)
— the eighth gate and **the first that is not a subline**. Two new scripts:
`35_census_sizeofrisk.py` (5/5) and `36_manual_sweep.py`.

### The manual has nothing to say, and that is the finding

Every earlier gate was differential against a manual rule. This one has no anchor: **0 of 1,030
manual documents mention size-of-risk.** But **187 of them are image-only**, so the claim the
corpus licenses is *"absent from the 843 that can be searched"* — 82%, not 100%. **OI-51** filed;
closing it needs OCR, which this environment lacks.

**So item 8 inverts the evidence hierarchy.** The tier-2 `confirm/` register has nothing to
register, and every sentinel here lands in `escalate/`. That is a first.

### Four findings the handoff did not predict

1. **Size-of-risk swaps the loss cost TABLE, it does not add a factor.** `SetPremOpsLossCost` reads
   `PremOpsSizeOfRiskLossCost` when the flag is `Yes` and `PremOpsLossCost` when it is not — the
   *first* rating step, before LCM and ILF. An engine that computes the ordinary premium and
   multiplies a relativity onto it gets the wrong loss cost. **That is why this is a build-order
   item and not a modifier inside item 6.**
2. **Linear interpolation — a new engine capability.** `InterpolateMode="Linear"` on the relativity
   value range. **16 of 4,551 rate table definitions across all 61 packages declare interpolation,
   and all 16 are size-of-risk.** It is live, not decorative: **8,148 of 8,330** Prem/Ops rows have
   unequal band endpoints. The open-ended top band was checked rather than assumed — **128 of 128**
   are flat, so interpolating across the `2⁶³` sentinel cannot under-rate large risks. If a future
   edition ever files an unequal pair there it will, silently; that is a load-time assertion.
3. **The sentinel is *guarded* — the register's first counterexample.** All ten setters and both
   consumers test `SizeOfRiskRatingApplies == "Yes"` before the relativity is read or multiplied,
   so the not-applicable `0.0` provably cannot reach a premium. **Contrast gate 370, where the drone
   modifiers multiply unguarded.** But the guard is on the **flag**, not the value: a `0` reached
   while the flag is `Yes` still prices at zero, and **0 of 388** `DoMessage*` rules corpus-wide
   would catch it.
4. **A fourth submission requirement, with its domain filed somewhere strange.**
   `SizeOfRiskRatingApplies` has no writer rule and appears in **none** of the 417 domain tables —
   it looked like free text. **It is not: `RatingIdentificationCode.RateTable.csv` is 4 rows keyed
   on it, enumerating 2 of 2 values `{Yes, No}`.** N14 sharpened: *no domain table* is not *no
   domain*.

### The Step 38 trap was real, and sharper than described

The handoff said *"resolve the lookup rule, never the table name."* Measured: **NJ and OH override
neither the table nor the lookup — they override the *setter*.** `SetPremOpsLossCost` is replaced
with a hand-written `Choose` over the territory code dispatching to 15 (NJ) and 10 (OH)
territory-specific lookups. **0 of 35** shipping jurisdictions override a size-of-risk *lookup*
rule. So the only binding that survives is **concept → resolved setter rule**.

**And a structural asymmetry inside NJ's own rule:** the size-of-risk `Choose` has no `Otherwise`;
the ordinary one falls through to `0.0`. Under this project's rules the size-of-risk branch is the
**safer** of the two — a null is loud, `0.0` is N13's silent failure — so it should not be "fixed"
by copying its neighbour.

### Jurisdiction split, and one filed defect

**0 of 3** declared parents carry a size-of-risk loss cost row; **35 of 51** jurisdictions do. In
the other **16** — AR CA DE FL GA IL KY LA MA MN NM NV NY PR SC TX — a `Yes` flag has no loss cost
at all and `PremOpsLossCost` is never assigned. That must become a resolve-time `REFER`.

**E19 raised:** **188 of 1,188** class codes carry a `0` size-of-risk loss cost, and **the same 188
in all 35** — countrywide content filed per-state. Class-not-eligible, genuinely zero, or
placeholder; nothing in the corpus arbitrates and the manual is silent.

**OI-52:** Kansas ships **1,189** distinct classes in a 2,376-row (2 × 1,188) table — territory 501
has `10211`, territory 502 has `10212`, one row each, both loss cost `0`, and `10212` is in no
parent's relativity assignment table. **1 of 70** (jurisdiction, subline) tables; the other 69 are
complete. Raise upstream, do not patch.

**OI-53:** `GL_CW_20270401_V01` keeps the relativity tables and drops assignment/min/max to 0 rows —
a silent zero premium for every size-of-risk risk in any jurisdiction that adopts it. **0 of 51 do
today**, so it is dated rather than live.

### OI-04 was wrong, in the way OI-40 exists to prevent

Its open clause — *"the `Maximum`/`Minimum` relativity and `TableAssignment` tables are 0 rows
countrywide; source unknown"* — is an **undated** count. True of the 2020–2022 editions and of
2027-04-01; **false of all three parents in force**, where each carries 1,188 rows. The rows were
never missing. **Closed, and the genuine forward-dated concern re-filed as OI-53.**

### Habit 8 caught two things inside this gate, and both were caught by a script

- **A `2⁶³` sentinel inflated a band-alignment count** — *"8,245 of 8,330 edges are multiples of
  1,000"*; the 85 exceptions were all the no-upper-bound marker. Re-enumerated excluding it:
  **0 of 8,330** real edges misaligned.
- **A truncated list was read as a population.** The sweep prints only its first 40 unsearchable
  documents, which are alphabetical and therefore all `LossCosts`; I wrote *"every unsearchable
  document is a loss-cost circular."* Actual: **103 of 503 rules manuals** and 83 of 472 loss-cost
  manuals. **Habit 8's failure mode, committed on the output of habit 8's own script.** Fixed by
  making the script print the by-family breakdown every run, not by re-reading.

The first version of `35_census_sizeofrisk.py` also reported **68 unread tables in 33
jurisdictions** — every one of which simply inherits its parent's lookup rule. Same failure, third
instance, caught before it reached a document.

### Verification

`35_census_sizeofrisk.py 20260812` **5/5** · `34_crosscheck.py 20260812` **4/4** ·
`tests/verify_golden.py` **80/80** · `36_manual_sweep.py` classified **1,030 of 1,030**.

**Consistency, enumerated:** open items **OI-1 … OI-53, no gaps, 53 distinct** · escalations **18
raised of 19 numbers issued** (E13 deleted before filing, Step 28) · non-negotiables **N1–N18** ·
gate documents **10** (8 gates + reconciliation + as-of recount) · ERC scripts **37** · build order
**14 items**.

### ▶ Next session

**Build-order item 9 — refer-to-company coverages.** OI-49's remaining instance (non-construction
railroad) belongs there. Before item 10, **OI-37**'s terrorism population audit is still owed. Also
still open from earlier: **OI-50** (Limited Product Withdrawal Expense, a §9 addendum to gate 365,
not a new gate), the **California** differential fixture (sole `GL_CW_20231201_V02` parent, still
untested) and a **New York** one.

**No engine code until directed.** No decisions outstanding.

---

## Step 42 — Terrorism gated, and a same-day correction to Step 41. ~~NEXT SESSION STARTS HERE.~~ *(the live handoff is **Step 43**)*

- **Date:** 2026-08-12
- **Directed:** "move Refer to Company to after state specific rating coverages. For Terrorism, we
  have Terrorism Manuals at `Commercial Line Manuals/GL/Terrorism`, review and save to circular
  expert agent, add to any documents surrounding circulars, and align with ERC to develop the
  build plan"

### First, a correction to Step 41, found by doing this task

Step 41 reported that **187 of 1,030 manual documents have no text layer**, wrote an 82%-of-corpus
bound into the size-of-risk gate, and opened **OI-51** to close the residual with OCR.

**Wrong.** Ingesting the terrorism manuals put a second extractor's output beside the first, and
`GL-CT-2026-LC-001-C` gives **0 bytes from `pdftotext` and 218,978 from `pypdf`**. They are not
image-only. **`scripts/02_extract_dualmode_losscosts.py` has carried that fallback since
2026-08-10 and nothing ever compared the two.** `36_manual_sweep.py` is dual-mode now:
**1,118 of 1,120 readable, 2 fail both.** The size-of-risk conclusion is unchanged and much better
supported — and independently corroborated by the agent's own corpus, extracted months earlier by
a different pipeline: **0 of 975.**

**OI-51 closed as a wrong diagnosis.** The lesson is not *use two extractors*; it is that **a
tool's silence was accepted as the corpus's silence** — habit 8 with the tool, rather than a query,
defining the population. `scripts/README.md` carries it as the third rule.

### The manual was there the whole time and the agent could not see it

The Terrorism Supplement — **3 notices, 113–118 pages** — has been on disk since the corpus was
assembled. The `iso-circular-expert` agent was built over `Rules` (503) and `LossCosts` (472)
**only**. So every terrorism question the agent was ever asked was answered from a corpus that did
not contain the terrorism rules, and its honest answer would have been *"the manual is silent."*

That is OI-51's failure arriving from the other direction, on the same day: **not a tool returning
nothing, but a folder never ingested.** Both manufacture absence out of the pipeline.

**Fixed:** `text/terrorism/` (page-tagged), `knowledge/terrorism.json`, `iso.py --kind TER`, three
notices registered, **2 new smoke tests — 17/17**. **Stated rather than left to be discovered:
142 of the 1,120 documents are still outside the agent** — 52 Schedule & Experience Rating and 90
Composite Rating. **OI-55.**

### OI-37 closed — terrorism premium *can* be computed

`RECONCILIATION.md` R3 forbade repeating *"terrorism premium cannot be computed"* until a
population audit ran. It ran.

Population: the **477** premium-writing groups, classified by whether their **rules** touch one of
the 20 enumerated terrorism tables — never by group name. **20 groups**, and the two framings
disagree in both directions: **2 found by content that the name misses** (`GeneralLiability`,
`GeneralLiabilityClassification`) and **13 matched by name that carry no rating table at all**.

**12 CAPTURE · 7 OTHER · 1 RATE_DRIVEN — and `OTHER` is not a miscellany.** Four of the seven
compute `Premium` from **other groups' finished `Premium`**:

    Premium = round( (PremOps + LossOfElectronicData + Cyber premiums)
                     x ExposureClassFactor [x NBCR 0.58] [x TerrorismILF / FinalILF], 0)

**None of those sources is in `25_rating_vs_capture.RATE_SRC`.** That is the **third** time the
list has been short — `AdjustedRate` was the second, on 2026-08-11, and it had filed both drone
coverages as aggregators. The list encodes an assumption — *a rating path starts from a rate* —
that ERC now breaks in two distinct ways: item 6's factor-on-host, and terrorism's
premium-on-premium.

**E18 widens from coverage-group scope to policy scope.** Terrorism reads four groups' `Premium`
and one group's `FinalILF` across three sublines and unmanned aircraft, so it runs **last**, and
the kernel must expose resolved premium state policy-wide.

### The manual differential is exact

**4 of 4 factor cells** — `.009` above-average, `.004` average, both TRIA and Full (Post-TRIA);
NBCR multiplier `0.58`. Two prose rules turn out to be filed one-row tables, including *"for
sublines other than premises/operations or products/completed operations use the average exposure
category."*

**The class list took four measurements to settle.** The manual prints **142** above-average
classifications; ERC countrywide carries **141**. The missing one is `91600`, and the first reading
was that ERC silently zeroes a class ISO prices — the mechanism was even right. **The premise was
wrong.** `91600` is not in the 1,188-class rating population (it is in the 1,197-class ILF
assignment table), and **0 of 9** such extras carry a loss cost or ELP anywhere, so the path is
unreachable. **New York does rate `91600`, and New York's own terrorism table lists it Above
Average — exactly as the manual says.** Compared as a union across packages: **142 vs 142, zero
either way.**

None of those four measurements was a re-reading of the claim.

### A second load-bearing misspelling

`CertifiedActsofTerrorismExposureClassFactor` — lowercase `of`, **3 occurrences against 6** of the
capitalised name, declared in the XSD, distinct from the rate table. **OI-47's `ProductWithdrawl`
pattern, second instance; the rule generalises.**

And it looked like a deletion defect: **10 writers, all in the two oldest countrywide packages;
0 writers in all three declared parents; 28 readers.** A factor read and never written, multiplied
into a premium with a `0.0` default. **It is not a defect.** The factor became a **user input**,
and its only filed bound lives in a rule that exists solely to raise a message —
`DoMessageWhenNoClassIsAnAboveAverageExposureClassTheExposureClassFactorCanBeFrom0to004`. **N15
exactly: the guard is the algorithm.**

### Build order resequenced, as directed

**Refer-to-company moves from 9 to 12**, after State-specific rating coverages. Items 9–12 are now
**9 Terrorism · 10 Rating plans · 11 State-specific · 12 Refer-to-company**; 13 and 14 unchanged.
The reasoning the gates keep producing: everything ahead of 12 generates referral conditions of its
own — size-of-risk's zero relativity and its 16 loss-cost-less jurisdictions, terrorism's
version-specific referrals, OI-49's railroad case — so the workflow gets built against a measured
population instead of a guessed one.

### Noted, not acted on: the corpus is growing under us

A **`Composite Rating`** folder appeared mid-session and reached **90** documents; the manual corpus
went **1,030 → 1,066 → 1,120** while this step was being written. That is **OI-03's missing corpus**,
which the PDF gap register had recorded as absent. The size-of-risk sweep was re-run at each
observed size — **0 of 1,030, 0 of 1,066, 0 of 1,120** — so the finding is stable under a moving
denominator. **Composite Rating is item 10's material and has not been read.**

### Register

**OI-37 closed** · **OI-51 closed as a wrong diagnosis** · **OI-54** (Hawaii: named by ISO, absent
from every project source — a scope boundary) · **OI-55** (88 of 1,066 documents outside the agent)
· **OI-56** (the two truncated source PDFs are registered inconsistently) · **OI-57**
(conditional-exclusion prorating is manual-only; a policy spanning 2027-12-31 must refer).

**OI-56 was itself corrected on being read.** Filed as *"one loss-cost notice has text but no
metadata"*; the text file is **0 bytes**. The real shape is smaller and more useful: the corpus has
**two** truncated source PDFs, both long known and both named in `README.md` — `GL-MO-2027-RU-003`
and `GL-MI-2027-LC-003` — and the agent registers **one and not the other**, so `iso.py notice`
gives two different wrong answers to the same question. **Those two are exactly the `2 of 1,120`
that fail both extractors**, which independently confirms the dual-mode sweep now reaches
everything the corpus contains.

### Verification

`37_terrorism_align.py 20260812` **4/4** · agent `smoke_test.py` **17/17** ·
`35_census_sizeofrisk.py 20260812` **5/5** · `34_crosscheck.py 20260812` **4/4** ·
`tests/verify_golden.py` **80/80** · docs HTML regenerated with **thirteen** tabs.

**Consistency, enumerated:** open items **OI-01 … OI-57, no gaps, 57 distinct** · escalations **18
raised of 19 numbers issued** · non-negotiables **N1–N18** · gate documents **11** (9 gates +
reconciliation + as-of recount) · ERC scripts **38** · PDF-pipeline scripts **14** · build order
**14 items** · **188 of 194** relative markdown links resolve, the six failures being the same
regex-fragments-in-prose confirmed at Step 38.

### A late correction to Step 41, found while scoping the owed fixtures

Scoping the California and New York differential fixtures turned up a **constant-stub override of
`SetSizeOfRiskRatingApplies`** in New York's package. Step 41's gate §6 says the flag has *"no
writer: 0 rules in the corpus assign it."*

**Measured on the countrywide package only** — the parent package, rather than a query, defining the
population. Re-measured across all **61** packages: **2,160 rules mention the flag and exactly 2
write it — California and New York, identical stubs writing `"No"`.**

**Size-of-risk rating is disabled by rule in CA and NY, whatever the submission says.** That is the
third habit-8 failure this session and the first one that *improves* a finding: it splits the
gate's sixteen loss-cost-less jurisdictions into **2 disabled by rule (safe, no engine work)** and
**14 that inherit the whole chain with no loss costs (silently unpriceable, must refer)**. Gate
§6a added; the engine's obligation narrowed from 16 to 14.

It also explains what the gate had only observed: CA and NY ship no size-of-risk loss costs
**because they do not do size-of-risk rating**, and they say so in a rule.

### ▶ Next session

**Build-order item 10 — Rating plans** (Schedule · Experience · Composite). **Ingest its corpus
first**: 52 Schedule & Experience Rating documents and 90 Composite Rating documents are on disk and
outside the agent (OI-55). That also settles **OI-01/02/03**, whose *"PDF recorded as absent"*
status is now false for Composite Rating.

Still owed from earlier: **OI-50** (a §9 addendum to gate 365), a **California** differential
fixture (sole `GL_CW_20231201_V02` parent) and a **New York** one — and NY is now more interesting,
since it is the only jurisdiction that rates class `91600`.

**No engine code until directed.** No decisions outstanding.

---

## Step 43 — Owed work ordered; California done. ~~NEXT SESSION STARTS HERE.~~ *(the live handoff is **Step 44**)*

- **Date:** 2026-08-12
- **Directed:** "order based on your recommendations"

### The order, and why

**1 California · 2 New York · 3 OI-50.**

**California first** because it is the only one of the three that puts *already-passed* work at
risk, and because it has the cheapest test shape: one hypothesis over 210 named DataDefs,
falsifiable without an engine. **New York second** — largest surface (698 overrides, rank 1 of 51
by 2.6x) and a specific hole in the freshly-filed terrorism gate (178 overrides in
`GeneralLiabilityTerrorismEndorsementCoverage`) — but partly deferred by design, since
`SpecialProtectiveHighwayCoverage` (35) belongs to item 11. **OI-50 last** because **0 of 51**
jurisdictions override any of its 11 rules: no deviation surface, no dependencies, the one item
where lateness costs nothing.

### California — done

[`docs/gates/CALIFORNIA-DIFFERENTIAL.md`](docs/gates/CALIFORNIA-DIFFERENTIAL.md) ·
[`tests/verify_california.py`](tests/verify_california.py) **11/11**.

**The two parents in force ship the same 547 files and the same 4,461 rule names, with 345
different bodies and zero rules added or removed** — N11 in its purest form, and the reason
`PHASE-SIZING.md` §4 once called these editions identical.

**341 of the 345 are one change.** V03 wraps writes in `if (target IsNull)` over 210 further
DataDefs. And V02 already had the idiom on **exactly 3** — `LCM`, `LCMStatCode`,
`LmtdProdsWithdrawalLCM` — so V03 **generalised 3 to 213** rather than inventing anything, and the
three ISO had already protected say what it is for.

### The first reading was wrong, and the second is better

*"V02 overwrites a broker-supplied value"* looked well-evidenced — seven of the 210 are `*Override`
fields and four are keys California's own submission supplies. **It does not survive reading the
rule.** `SetGeneralAggregateLimit` copies from the same policy-level source in **both** editions;
the guard protects the local copy, not the input.

**The right reading: the guard is idempotency under re-evaluation.** V03's 213 DataDefs are
write-once; V02's are recomputed on every evaluation — and nothing else stops recomputation,
because **5,601 of 5,601** `RunRule` calls carry `ClearCache="true"`. **The guard *is* the
memoisation.** Re-evaluation is real and locatable: **14 `PremiumToReachMinCoverage` groups**, and
**three of the four non-guard differences are the iteration totals inside three of them.**

### What it does not license

**Nothing about a California premium.** Recomputation from unchanged inputs is idempotent; it
diverges only if an intermediate is mutated between passes, and establishing which needs the
engine. **Nor can the corpus settle it: 1 of 517 STC payloads is a rated output, and it is
Oklahoma's.** California ships one input-only payload. **OI-58** filed saying exactly that.

### One risk closed on measurement

**All ten size-of-risk setters differ between the parents** — the chain gated the day before, and
the sharpest-looking exposure in the set. **It is unreachable in California**, which stubs
`SetSizeOfRiskRatingApplies` to `"No"`. The size-of-risk gate needs no California caveat, and
CA's own filed submission agrees (`SizeOfRiskRatingApplies: "No"`, `TerrorismCoverage: "No"`).

### The fixture caught two of my own claims

Written as assertions rather than sentences, and **two failed on first run**: *"V02 has no guard
anywhere"* (it has 3) and a rule name derived from its group stem instead of read
(`SetTotalUnmannedAircraftPremium`, not `SetTotalLimitedCovForDesignatedUnmannedAircraftPremium`).
**Both are habit-8 shapes, and both were caught before reaching a document** — which is the whole
argument for writing a differential as a test.

### Verification

`tests/verify_california.py` **11/11** *(new)* · `tests/verify_golden.py` **80/80** ·
`35_census_sizeofrisk.py` 5/5 · `37_terrorism_align.py` 4/4 · `34_crosscheck.py` 4/4 ·
agent `smoke_test.py` 17/17 · docs HTML regenerated with **fourteen** tabs.

### ▶ Next session

**New York** — the second owed item. Two things to separate: the **178 overrides in
`GeneralLiabilityTerrorismEndorsementCoverage`**, which is a hole in the just-filed terrorism gate
and should be closed now; and `SpecialProtectiveHighwayCoverage` (35 rules), which belongs to
**item 11** and should wait for it. NY also carries **151 empty-body and 98 constant-stub
overrides** — the stub form is the one a check for empty bodies misses, and gate 332 found it in
claims-made liquor. **It is not only liquor: `SetYearInClaimsMade` and `SetClaimsMadeMultiplier`
are stubbed in Prem/Ops and Products too**, which no gate has recorded.

Then **OI-50**, then **build-order item 10 — Rating plans**, whose corpus (52 Schedule & Experience
Rating + 90 Composite Rating documents) still needs ingesting (OI-55).

**No engine code until directed.** No decisions outstanding.

---

## Step 44 — New York done. ~~NEXT SESSION STARTS HERE.~~ *(the live handoff is **Step 45**)*

- **Date:** 2026-08-12
- **Directed:** "work on new york"

Second of the three owed items. [`docs/gates/NEW-YORK-DIFFERENTIAL.md`](docs/gates/NEW-YORK-DIFFERENTIAL.md)
· [`tests/verify_new_york.py`](tests/verify_new_york.py) **10/10**.

### The scale, measured

**698 override rules across 134 files — rank 1 of 51, 2.6× Vermont (267) and 5.6× the median
(124).** Three gates had recorded a New York finding in passing. None had measured the surface, and
of the three passing records **one was a third of the truth, one was a false alarm, and one held.**

### One was a third of the truth — New York withdraws claims-made GL entirely

Gate 332 found New York stubbing liquor's `SetYearInClaimsMade` and `SetClaimsMadeMultiplier`.
Measured across the package, that is **one coverage of five**:

- `SetClaimsMadeMultiplier` stubbed to constant `1.0` in **5 groups** — Prem/Ops, Products, Liquor,
  Unmanned Aircraft Cov A and Cov B
- `SetYearInClaimsMade` stubbed to `0` in **3**
- **all 4** claims-made multiplier tables overridden to **0 rows**, against a countrywide
  `PremOpsClaimsMadeMultiplier` of **5,940 rows, values 0.34–0.98**
- **0 of the other 50 jurisdictions do any of it**

**ISO says one thing three ways: New York does not write claims-made General Liability.** Gate 332's
conclusion stands; its scope did not. **OI-59.**

**The engine risk is precise and it is a collision between two non-negotiables.** N16 says lookups
fall back row-wise from the state row to a `"CW"` row *inside one table*; N3 says a package-layer
override replaces the table wholesale. Here N3 wins — there is no countrywide row to fall through
to, because the table itself was replaced with an empty one. An engine that got that backwards
applies a discount of up to 66% that New York has withdrawn.

### One was a false alarm — and checking it was worth more than assuming it

Step 43's handoff flagged **178 overrides in `GeneralLiabilityTerrorismEndorsementCoverage`** as a
hole in a gate filed the day before. It is not a hole.

New York overrides **174 of the countrywide group's 602** rules and adds 4 — **and `SetPremium` is
not among them.** New York inherits

    Premium = round(EndorsementPremium x CertifiedActsofTerrorismExposureClassFactor, 0)

unchanged. The 174 rebuild the *roll-up* that produces `EndorsementPremium`, one
`Set…TotalPremium` per endorsement, because New York's endorsement inventory differs; the 4
additions are two New York forms — **binding and non-binding arbitration**.

**New York changes the input to the terrorism formula, not the formula.** The gate's §1 premium
source table is correct for all 51. Recorded because assuming 174 overrides in a fresh gate must be
a defect would have been wrong in the expensive direction — and because the cheap check
(*is `SetPremium` in the override set?*) settles it in one line.

### The new finding — rating switched off for 83 endorsements

**151 empty-body overrides, of which 83 are `ErcRate`** — an endorsement group's rating entry point
— and **130 of the 151 replace a non-trivial countrywide body**. The endorsement stays attachable
and its premium capturable; it loses the ability to rate. **The largest instance of N3's
*empty ≠ absent ≠ inherit* anywhere in the corpus.** **OI-60**; each of the 83 needs a
capture-not-rate disposition in item 13's harness.

Beside them, **98 constant-stub overrides** — the class a check for empty bodies cannot see. They
include the claims-made pair, `SetSizeOfRiskRatingApplies → "No"` (Step 42's finding) and six
`SetCoverageOnPolicyIndicator` stubs switching whole coverages off.

### Deferred on purpose

**Special Protective and Highway — 36 New York rules, 4 rate tables, 0 countrywide tables.** A
rate-driven coverage in no countrywide edition, with its own N17 selector. Asserted here only far
enough to show it is New York's alone and that it rates. **Deriving it belongs to build-order item
11**, alongside the MD and MA lead coverages.

*(An earlier note put it at "11 tables" — that counted `*Def.RateTableDef.xml` siblings and domain
tables. **4 rate tables.** The fixture asserts the names, not the count, for exactly that reason.)*

### Also pinned

New York shards **loss costs and its rating-basis selector** by territory — 95 tables, **71
populated**, **21** with a `Terr<nnn>` suffix including `PremOpsELPTextTerr001`, with the base
`PremOpsLossCost` present and empty. It is the only jurisdiction of 51 that shards a *selector*
(N17). And **class `91600` is New York's alone** — 106 above-average terrorism classes against
countrywide's 105, matching the manual's 142 where countrywide ERC cannot.

### Verification

`tests/verify_new_york.py` **10/10** *(new)* · `tests/verify_california.py` 11/11 ·
`tests/verify_golden.py` 80/80 · `34_crosscheck.py` 4/4 · `35_census_sizeofrisk.py` 5/5 ·
`37_terrorism_align.py` 4/4 · agent `smoke_test.py` 17/17 · docs HTML regenerated with **fifteen**
tabs.

**Consistency, enumerated:** open items **OI-01 … OI-60, no gaps, 60 distinct** · escalations **18
raised of 19 numbers issued** · non-negotiables **N1–N18** · gate and analysis documents **13** ·
tests **3** · ERC scripts **38**.

### ▶ Next session

**OI-50 — Limited Product Withdrawal Expense**, the last of the three owed items and the smallest:
an 11-rule chain inside the shared `GeneralLiabilityClassification` container, **0 of 51**
jurisdictions overriding any of it, owed as a §9 addendum to gate 365 rather than a gate of its own.
Three `DoMessage*` guards belong to it, including a negative-premium check.

Then **build-order item 10 — Rating plans**, whose corpus still needs ingesting first: **52
Schedule & Experience Rating and 90 Composite Rating documents** are on disk and outside the expert
agent (OI-55). That also settles OI-01/02/03.

**No engine code until directed.** No decisions outstanding.

---

## Step 45 — OI-50 closed. All three owed items done. ~~NEXT SESSION STARTS HERE.~~ *(the live handoff is **Step 46**)*

- **Date:** 2026-08-12
- **Directed:** "do it"

Third and last of the owed items. Filed as **[gate 365 §9](docs/gates/GATE-365-WITHDRAWAL-LOED-CYBER.md)**
— an addendum, as scoped, not a gate — and pinned by
[`tests/verify_oi50.py`](tests/verify_oi50.py) **7/7**.

### The chain, derived end to end

```
LmtdProdsWithdrawalProductWithdrawalFactor ← LookupProductWithdrawlFactor(...)   [MISSPELLED table]
BaseRate  = (ProdsCompldOpsLossCost | FinalProdsCompldOpsELP) × LmtdLCM × ProductWithdrawalFactor
FinalILF  = CSLILF − DeductibleFactorForRating
FinalRate = round(BaseRate × FinalILF × PackageModFactor, 3)
Premium   = round(FinalRate × ProdsCompldOpsCovExposure [÷1000 by the filed nine bases], 0)
Coverage  = ClassPremium × ProductWithdrawalParticipationPercentage × PackageModFactor − Discount
```

The `÷1000` is decided by **the same nine-value premium-basis list** as size-of-risk and
`SetBasicLimitPremium` — third appearance. It must be read once from one place.

### Three findings worth keeping

1. **OI-47's reader is named, and checked on values.** This coverage reads the **misspelled**
   `ProductWithdrawlFactor` — **0.20 / 0.15 / 0.10** — while the full Product Withdrawal coverage
   reads `ProductWithdrawalExpensesFactor` — **0.25 / 0.19 / 0.13**. Two live tables, different
   values, and the misspelled one is what the filed manual prints (Table 44.B.3.b, p.93).
   Normalising the spelling merges them.
2. **E18's third instance.** `SetLmtdProdsWithdrawalBaseRate` reads
   `GeneralLiabilityClassificationProdsCompldOpsCoverage/ProdsCompldOpsLossCost` — a sibling
   group's value. After item 6's factor-on-host and terrorism's premium-on-premium, this is the
   third distinct shape of cross-group dependency.
3. **The corpus's only negative-premium guard lives here** — and it is needed, because
   `FinalILF = CSLILF − DeductibleFactor` has **no arithmetic floor**. Two of the four
   `DoMessage*` guards are the sole thing standing between a large deductible and a negative rate.
   **N15 strengthened**: sometimes the guard is the only statement of a bound anywhere in the
   filing.

### Both counts in the original entry needed correcting — and the second went wrong twice

**"An 11-rule chain."** 11 is the **rating** chain. The coverage is **54 rules across five
DataDefGroups** — 11 in the shared container, 4 guards, and 39 in three properly-named groups
including one of the 14 `PremiumToReachMinCoverage` iterators. §6a's actual point survives: the 11
are the ones hidden inside `GeneralLiabilityClassification`, which is why they were missed.

**"0 of 51 override any of it."** Re-measuring produced three answers:

| Attempt | Answer | Defect |
|---|---|---|
| 1 — the 11-rule chain | 0 of 51 | right, but stated over "any of it" |
| 2 — rule **names** anywhere in the package | **27 of 51** | `ErcProcess` / `InitializeRuleSet` exist in hundreds of groups; a generic name matched everywhere |
| **3 — membership by `DataDefGroup`** | **1 of 51** | **the measurement** |

Only **Texas** touches the coverage groups, with `InitializeRuleSet` and two stat-code lookups.
**0 of 51 touch the arithmetic.** So the original claim was right *and stronger than it looked*:
this is the only rating chain in the project with a countrywide-only derivation and effectively no
state deviation — which is exactly why it was safe to leave until last.

**Attempt 2 is habit 8's failure mode for the fourth time in three sessions, and the first time it
made a finding look *worse* than it is.** Same rule catches it: membership in a population is by
the thing that defines the population — here the `DataDefGroup` — never by a name that happens to
be shared.

### And N8 at its cleanest

`ProductWithdrawalExpensesAndLiabilityIncrdLimitFactor`: **0 rows in all 10 countrywide editions,
36 rows in all 51 jurisdictions.** A deliberate contrast with size-of-risk, where only 35 of 51
ship and the other 16 leave the coverage unpriceable. Here there is no gap at all.

### Verification

`tests/verify_oi50.py` **7/7** *(new)* · `tests/verify_new_york.py` 10/10 ·
`tests/verify_california.py` 11/11 · `tests/verify_golden.py` 80/80 · `34_crosscheck.py` 4/4 ·
`35_census_sizeofrisk.py` 5/5 · `37_terrorism_align.py` 4/4 · agent `smoke_test.py` 17/17 ·
docs HTML regenerated.

**Consistency, enumerated:** open items **OI-01 … OI-60, no gaps, 60 distinct** · escalations **18
raised of 19 numbers issued** · non-negotiables **N1–N18** · gate and analysis documents **13** ·
test suites **4** · ERC scripts **38**.

### State of the owed list

**Empty.** California, New York and OI-50 are all closed, each with a runnable fixture. Nothing is
outstanding outside the build order.

### ▶ Next session

**Build-order item 10 — Rating plans** (Schedule · Experience · Composite).

**Ingest its corpus first.** **52 Schedule & Experience Rating** and **90 Composite Rating**
documents are on disk and outside the expert agent (**OI-55**); the Composite Rating folder arrived
during Step 42 and is **OI-03's missing corpus**, which the PDF gap register had recorded as absent.
`scripts/13_extract_terrorism.py` is the pattern to copy; `iso.py` will need two more `--kind`
routes.

Ingesting them settles **OI-01** (Schedule Rating), **OI-02** (Experience Rating) and **OI-03**
(Composite Rating), all three of which are `PARTIAL` only because the manual side was missing.

**No engine code until directed.** No decisions outstanding.

---

## Step 46 — Build-order item 10 gated. ~~NEXT SESSION STARTS HERE.~~ *(the live handoff is **Step 47**)*

- **Date:** 2026-08-12
- **Directed:** "Schedule & Experience Rating: …, Composite Rating: …, do the pdf analysis along
  ERC analysis, update docs, and then build the plan"

[`docs/gates/GATE-RATING-PLANS.md`](docs/gates/GATE-RATING-PLANS.md) ·
[`scripts/erc/38_rating_plans_align.py`](scripts/erc/38_rating_plans_align.py) **7/7** ·
agent smoke **19/19**. **OI-01, OI-02, OI-03 and OI-55 closed. PDF gap G6 retired.**

### The first gate where the manual is the richer source

Nine gates have run ERC-first with the manual confirming. This one inverts: the three plans were
recorded as **`PARTIAL` — "`[PDF]` recorded as absent"** since 2026-08-10, and **they were on disk
the whole time** — **52 `CGLES` + 90 `CRP` documents, 654 pages**, outside the expert agent's
corpus. All 142 extracted cleanly.

**And there is a specific reason Composite Rating stayed invisible longest: it moved to the
*Interline* manual in 2017.** 39 documents begin `GL-` (2007–2012) and **51 begin `IL-`**
(2017–2024). A sweep that assumes a General Liability document starts `GL-` finds 39 of 90 — and
misses every current one. **Habit 8 wearing a filename.**

**G6 was wrong twice over.** First shown wrong about ERC, which had the apparatus all along; now
shown wrong about **the PDF corpus it was actually a claim about**. All four of its claims are
false. It went uncorrected because **the tool the project asks when it wants to know what the
manual says had been built over two of the five corpora.**

### Schedule rating — 8 of 8, on range *and* row count

Manual Rule 9 Table 9 against ERC's `DomainScheduleRatingModification*Pct`. Every domain is
enumerated in 1% steps, so a ±n% range must be exactly **2n+1** rows — and it is, in all eight:
11 / 11 / 21 / 21 / 21 / 13 / 5 / 5 for ±5 / ±5 / ±10 / ±10 / ±10 / ±6 / ±2 / ±2. **ERC ships
exactly 8 such domains, the manual prints exactly 8.** The ±25% cap is filed as data, one row each.

**Both of OI-01's open questions answered**, including the odd one: the liquor cap tables are 0
rows **because the plan has no liquor provision** — `liquor` appears 0 times in the countrywide
CGLES. N7, not a gap.

### Experience rating — 291 cells, 0 mismatches

Manual Rule 5.G: `((AER − EER) ÷ EER) × Credibility`. ERC's `SetExperienceModification` computes
that expression over those three DataDefs, in that order. **E10 closed on ERC evidence in Step 22
and now has its manual citation.**

**Rule 16 is one printed table and three filed ones** — `CredibilityFactor`,
`ExpectedExperienceRatio`, `MaximumSingleLoss`, 99 rows each on a shared band key. **97 of 97
printed bands agree on all three columns. 291 cells. Zero mismatches.**

The 2 extra ERC rows are the interesting part: a **`[0, 10879) → 0` eligibility floor** — manual
Rule 2 encoded as data. Below $10,879 of subject loss cost, credibility is `0`, so the modification
is `0` and the risk simply is not experience rated. **N13's eighth meaning of `0`, and its second
genuinely-zero one.** It must NOT go in the sentinel register.

**A near-miss worth recording.** The first pass looked for a table called
`ExperienceCredibilityFactor`, found **0 rows**, and was one sentence from filing *"the credibility
table is missing from ERC."* The rule is `LookupExperienceCredibilityFactor`; **the table it reads
is `CredibilityFactor`.** Resolving the lookup rather than guessing the table name — the
size-of-risk gate's lesson — turned a fabricated gap into a 291-cell agreement.

### Composite rating — executable, and it is an audit mechanism

OI-03 said the rule file had never been read. Read: **3 rules.**

    CalcCompositeRate           = round(TotalClassificationsPremium ÷ CompositeExposure, 8)
    FinalCompositeRatingPremium = round(CalcCompositeRate × FinalAdjustedCompositeExposure, 0)

`GL-MU-2007-CRP-001` Rule 3 states exactly that: *"the composite rate determined at the beginning
of each policy year is applied to the risk's composite exposures at the end of the year to produce
the final audited company premium."* **It does not derive a rate from loss costs** — it
re-expresses classification premium as one rate per exposure unit and re-applies it at audit.

### A rounding precision N10 did not list

`CalcCompositeRate` rounds to **8 decimal places**. N10 records the vocabulary as 3 / 0 / 4 / 2.
Enumerated across every package: **3 sites at 8dp, in all 10 countrywide editions and 0 of 51
jurisdictions** — the composite rate, **and two in Railroad** (`SetContractCostFactorWOHzd`,
`SetContractCostFactorWithHzd`). **Gate 335-RR derived Railroad without recording its precision.**
A `Decimal` context configured from the four-value list rounds all three silently. **OI-62**;
N10 corrected in place.

### Deviation surface, and Puerto Rico

**8 of 51 jurisdictions deviate: 7 on schedule rating, 1 on experience (New York, again), 0 on
composite.** Composite rating is the **second countrywide-only chain** in the project after
Limited Product Withdrawal Expense.

**Both plan corpora cover the same 50 jurisdictions plus `MU`.** The absentees are **Hawaii**
(absent from everything, OI-54) and **Puerto Rico** — the inverse and more awkward shape: **ERC
rates PR under the plans**, and it is the **only jurisdiction of 51 to ship its own
`ExpectedExperienceRatio`**, while the manual side has nothing to confirm against. **OI-61.**

### The agent now holds everything on disk

`text/scheduleexperience` (52) and `text/compositerating` (90) added by the generalised
`scripts/15_extract_manual_family.py`. `iso.py` routes **five** corpora — `--kind SE | CR | PLANS`
— `notices.json` registers **1,119** notices in five groups, and two new smoke tests pin it.
**OI-55 closed.**

### The build plan for item 10

Recorded in the gate §6. **Order within the item: schedule → experience → composite**, because
composite consumes `TotalClassificationsPremium` and so runs after every classification is rated —
the same runs-last constraint terrorism has. **The 25% cap is a `REFER`, not a clamp**:
`ScheduleRatingModificationLogic` writes a message id and does not truncate. **Loss history is a
submission input with no oracle** — no STC payload in the corpus carries experience losses.
**Composite needs an audit-time re-entry point**, since `FinalAdjustedCompositeExposure` arrives
after the policy period.

**Item 10 is the first item that adds no rate lookup of its own** — all three plans operate on
premium other items produce.

### Verification

`38_rating_plans_align.py 20260812` **7/7** · agent `smoke_test.py` **19/19** ·
`verify_golden.py` 80/80 · `verify_california.py` 11/11 · `verify_new_york.py` 10/10 ·
`verify_oi50.py` 7/7 · `34_crosscheck.py` 4/4 · `35_census_sizeofrisk.py` 5/5 ·
`37_terrorism_align.py` 4/4 · docs HTML regenerated with **sixteen** tabs.

### ▶ Next session

**Build-order item 11 — State-specific rating coverages.** Four coverages in three states: **MD**
lead-hazard liability, **MA** lead-poisoning endorsement and supplemental cover, and **NY Special
Protective and Highway** — 36 NY rules and 4 rate tables, present in **no** countrywide edition,
already scoped and deliberately deferred by the [New York differential](docs/gates/NEW-YORK-DIFFERENTIAL.md) §6.

Then item 12 (refer-to-company), 13 (capture harness), 14 (policy assembly).

**No engine code until directed.** No decisions outstanding.

---

## Step 47 — Build-order item 11 gated. ~~NEXT SESSION STARTS HERE.~~ *(the live handoff is **Step 48**)*

- **Date:** 2026-08-12
- **Directed:** "Ok, move to step 11"

[`docs/gates/GATE-STATE-SPECIFIC.md`](docs/gates/GATE-STATE-SPECIFIC.md) ·
[`scripts/erc/39_state_specific_align.py`](scripts/erc/39_state_specific_align.py) **4/4**.

### The scope was wrong, and re-deriving it was the point

`PHASE-SIZING.md` §5 scoped this as *"four coverages in three states"*, with a note that *"NJ and RI
lead coverages were checked and do not rate."*

The population was **re-derived rather than taken from the list**: every DataDefGroup appearing in no
countrywide edition, by differencing **582 countrywide groups against 618 jurisdiction groups** →
**449 state-only**, of which 371 write no premium, **58 capture**, **16 are `OTHER`** and **4 are
`RATE_DRIVEN`**.

**The four `RATE_DRIVEN` are exactly the four named — that half held. Rhode Island is a fifth, and
it rates.** 13 rules, a **16,410-character `SetPremium`** branching on classes `67510`/`67511` and
four lead-safety levels, with no `ManualPremium` anywhere in it.

**New Jersey checked and confirmed capture-only** — 3 groups, 2 write a premium, both read
`ManualPremium`, and all five NJ lead tables are `*StatCode`. The note was half right.

**Item 11 is five coverages in four states, 88 rules.**

### Rhode Island hid for a reason worth recording — the fourth time

`RATE_SRC` matches `FinalRate | BaseRate | LossCost | ELP | AdjustedBaseRate | AdjustedRate`.
RI's premium reads **`LeadLiabilityRate`**, which matches none of them.

| Found | Missing term | Cost |
|---|---|---|
| 2026-08-11 | `AdjustedRate` | both drone coverages filed as aggregators |
| 2026-08-12 | a sibling group's `Premium` | four terrorism groups |
| 2026-08-12 | `EndorsementPremium` | the terrorism endorsement group |
| **today** | **`LeadLiabilityRate`** | **a whole state coverage** |

**Four blind spots in one list in two days.** The list encodes *a rating path starts from a rate
whose DataDef is named like one*, and ERC has broken that four different ways. **`18 / 383 / 76` is
a floor, not a measurement** — every "N coverages rate" figure carries an unstated "at least" until
a re-measurement classifies by what the premium rule *reads*. **OI-63.**

### Three lead subjects, three unrelated algorithms

| | Filed rate content |
|---|---|
| **MD** | 1 row, a flat **`15`** per rental dwelling unit |
| **MA** | 1 row, **`0.01`**, plus a `90140` statistical code |
| **RI** | **4 rows keyed on hazard level**: `Lead Safe 0.01` · `Lead MICI 0.05` · `Lead MVI 0.10` · `Lead MPC 0.10` |

**Rhode Island is the only one that prices risk differentiation** — a **tenfold** spread between a
lead-safe unit and an unmitigated one, the largest single-coverage credit spread in the project, on
four separate unit-count inputs.

All four states carry the coverage in the manual as an **`ADDITIONAL RULE(S)`** block in the state
exception pages — the manual-side signature of this item, and the exact analogue of a DataDefGroup
present in no countrywide edition.

### New York Special Protective and Highway prices at zero, by design

The largest of the five — 35 rules, borrowing OCP's ILF and Prem/Ops's LCM and minimum premium —
and **not a rateable coverage**:

- `SpecialProtectiveHighwayLossCost` — **`0`, `0`, `0`**
- `SpecialProtectiveHighwayELP` — **`0`, `0`, `0`**
- **`SpecialProtectiveHighwayELPText` — `Company`, `Company`, `Company`**

**N17 settles it**: `Company` means *refer to company*, and a single-valued selector means one
rating path. `SetBaseRate` branches on `LossCost == 0` to the ELP path — N13's third meaning — and
finds `0` there too, so the chain computes **`0`**.

**Railroad Protective's shape exactly.** Two of the eighteen rate-driven coverages are structurally
elaborate referrals. **NY SPH is item 11 by structure and item 12 by behaviour**: build the 35 rules
(limits, ILF, minimum premium, statistical coding), take the rate from the carrier, and register the
sentinel **on the selector, not the zero** — the selector is the declaration, the zero is the
symptom. **OI-64.**

### Verification

`39_state_specific_align.py 20260812` **4/4** *(new)* · `38_rating_plans_align.py` 7/7 ·
`37_terrorism_align.py` 4/4 · `35_census_sizeofrisk.py` 5/5 · `34_crosscheck.py` 4/4 ·
`verify_golden.py` 80/80 · `verify_california.py` 11/11 · `verify_new_york.py` 10/10 ·
`verify_oi50.py` 7/7 · agent `smoke_test.py` 19/19 · docs HTML regenerated with **seventeen** tabs.

**Consistency, enumerated:** open items **OI-01 … OI-64, no gaps, 64 distinct** · escalations **18
raised of 19 numbers issued** · non-negotiables **N1–N18** · gate and analysis documents **15** ·
test suites **4** · ERC scripts **40** · build order **14 items, 11 gated**.

### ▶ Next session

**Build-order item 12 — refer-to-company coverages.** Its population is now measured rather than
guessed, which was the whole reason for moving it here:

- **OI-49** — non-construction railroad operations, a manual-only referral with no ERC discriminator
- **OI-64** — NY Special Protective and Highway, `Company` on all three classes
- **Railroad Protective** itself — ELP-only, single-valued `Industry`, manual says refer
- **Size-of-risk** — a `0` final relativity while the flag is `Yes`, and the **14** jurisdictions
  that inherit the chain with no loss costs
- **Terrorism** — the version-specific referrals across 16 `PEV` versions
- **The drone sentinel** — 18 of 60 cells across three axes

Then item 13 (capture harness, 383 groups) and item 14 (policy assembly).

**No engine code until directed.** No decisions outstanding.

---

## Step 48 — Item 12, steps 1 and 2: the referral census amended four gates; the register is emitted. ~~NEXT SESSION STARTS HERE.~~ *(the live handoff is **Step 49**)*

- **Date:** 2026-08-12
- **Directed:** walk through the item-12 plan chunk by chunk, then "start with 1", then "yes, and
  then work on the other corrections"

**Scope agreed at chunk 1: the broad reading** — item 12 is the referral *register*, not just the
two coverages that are referrals. Build plan §5 commits `escalate/` as *"modules, not
documentation"*, and nothing had assembled the list that module consumes.

### Step 1 — find referral conditions by scanning, not by re-reading gates

[`scripts/erc/40_referral_census.py`](scripts/erc/40_referral_census.py): six probes over 61
packages, writing `out/referral_census.json`. The point is the **diff** against the population read
out of eleven gate documents — anything in the documents and not the census means the census is
short; anything in the census and not the documents means eleven gates missed it.

**Two probes were wrong on the first run, and both failures were the useful kind:**

- **Probe 6 returned 0** against a case the New York differential had already established. I was
  scanning each jurisdiction's own rule files for readers — **but the reader is usually in the
  parent.** Fixed to scan the jurisdiction's rules *plus its declared parent's*: **0 → 75 triples.**
- **Probe 3 filtered on `Company`**, which finds NY Special Protective and Highway and **misses
  Railroad Protective**, whose selector is single-valued `Industry`. Fixed to flag any
  single-valued selector: **2 of 7**, both referrals.

### What it tightened

The declared sentinel lives in **2 (table, column) sites — both ILF assignment, 204 cells** — and is
tested at **5 (group, rule) sites**. And N18's edition scoping is sharper than recorded:
**`GL_CW_20270401_V01` carries both spellings inside one package**, 49 `Refer To Co.` against 1
`Refer to Company`, the single new one being liquor's `SetPremium`. That is OI-43 measured rather
than described.

### And it amended four filed gates — OI-65

**Probe 6: a jurisdiction empties a table to zero rows while the reading rule stays in force.**
75 triples over 43 tables, split cleanly by a redirect-vs-withdraw test.

**1. Terrorism — corrected the same day it was filed.** **15 of 51 jurisdictions** empty
`CertifiedActsOfTerrorismExposureClassFactor` and redirect all three lookups to a state table
**keyed on Territory**, a column the countrywide table does not have.

| | Countrywide | The 15 |
|---|---|---|
| Distinct factors | **2** — `0.009`/`0.004` | **15**, `0.004`–`0.133` |
| Spread | 2.25x | **33x** |

**New York files a Manhattan-specific table** — fifth key column, factors `0.038`–`0.098`, up to
**10.9x** the countrywide above-average factor. **California** adds `RemainderOfTerritory001`.
The gate's *"4 of 4 factor cells agree"* is true of the countrywide table and **describes 36 of 51
jurisdictions**. Gate §3a added; **check 3a pinned in `37_terrorism_align.py` (5/5)**.

**2. Gate 365 — California withdraws Loss Of Electronic Data and Cyber Incident Liability
entirely.** 13 tables emptied, and **`SetCoverageOnPolicyIndicator` stubbed to `0` in all six
groups** — both classification groups per coverage plus each `PremiumToReachMinCoverage` iterator.
**Guarded, deliberate, not a silent zero**, and coherent: CA also stubs `SetSizeOfRiskRatingApplies`
to `"No"`, and size-of-risk is exactly what those two coverages read across the group boundary
(E18). A state that withdraws both has no reason to keep the input they need. Gate §10.

**3. Rating plans — Nebraska empties both schedule-rating cap tables** *and* overrides
`ScheduleRatingModificationLogic`. The gate said the 7 deviators override rules *rather than* the
caps; NE does both. The ±25% cap is countrywide data **with one state filing its own mechanism**.

**4. Still to characterise:** `LiquorLiabGrade` (IA, MO, OK), `BringYourOwnAlcoholExclusionFactor`
(MA, TX), `Subline` (VA, VT), `PolicyAdjustmentFactorB/C` (NY).

### The shared defect, and the mechanism it exposes

**A gate measured a countrywide table against the manual and did not ask which jurisdictions read
it.** Four gates, one shape. It is habit 8 one level up: the *countrywide package* was allowed to
define the population.

And it named the mechanism: **`SetCoverageOnPolicyIndicator` is how a jurisdiction switches a
coverage off**, and it is now the most load-bearing stub in the corpus. An engine that evaluates a
rating chain without consulting it first reads empty tables in California and hits nulls that mean
nothing.

### Verification

`37_terrorism_align.py 20260812` **5/5** (was 4/4) · `40_referral_census.py` runs clean over 61
packages · all other suites unchanged and green.

### Step 1 finished — the four remaining withdrawals, and the reconciliation

**Three different things, not one:**

| Table | States | Verdict |
|---|---|---|
| `LiquorLiabGrade` | IA, MO, OK | **redirect** — `LookupLiquorLiabGrade` overridden to read `LiquorLiabilityGradeOnOffPremises`, 14 rows each. Safe |
| `PolicyAdjustmentFactorB/C` | NY | **redirect** — six `SetPolicyAdjustmentFactor*` rules overridden. Safe |
| `BringYourOwnAlcoholExclusionFactor` | MA, TX | **withdrawn, narrowly guarded** — the setter fires only for classes `16905`/`16906` with the liquor-exclusion amendment attached |
| `Subline` | VA, VT | **withdrawn, harmless** — **0 rules read the DataDef it feeds**. An output field, not a rating input (E14's shape) |

**The reconciliation now runs inside the script.** Of **20** referral conditions recorded across
eleven gates, **9 are reachable by a probe and 11 are not.** The 11 are not a gap in the census —
they are the cases where **ERC carries no discriminator**, which is chunk 3's third kind, and each
is a decision rather than code:

`LCM = 1` placeholder (E15) · the 18 drone RTC cells · the filed `Unknown`/`Not Applicable` drone
values · a `0` size-of-risk final relativity while the flag is `Yes` · unmatched county or place
(OI-34) · absent `WorkersCompensationRate` (OCP) · an effective date below the corpus floor (OI-41)
· non-construction railroad operations (OI-49) · the 188 zero-loss-cost classes (E19) ·
conditional-exclusion prorating (OI-57) · Puerto Rico's missing plan manual (OI-61).

**That 9-versus-11 split is the most useful thing step 1 produced.** It says the engine can be
provably complete on **under half** the referral population by scanning, and the rest has to be
decided — which is exactly what chunk 3 predicted and is now measured rather than argued.

### Step 2 — the population classified, and the register emitted

[`scripts/erc/41_referral_register.py`](scripts/erc/41_referral_register.py) **4/4**, writing
`out/referral_register.json` — the artifact build plan §5 promises `escalate/` will consume.

**28 entries.** The 20 conditions the gates recorded, plus the 6 the census found, plus two the
classification pass surfaced as distinct (NY's claims-made withdrawal and the OI-20 empty-base-table
pattern, which are declared referrals in their own right rather than footnotes to other entries).

| Kind | | Detection | Count |
|---|---|---|---|
| **1 DECLARED** | the corpus says refer | **load** | **9** |
| **2 MISSING** | the lookup misses | rate (1 at load) | **4** |
| **4 GUARD** | the bound is only in a `DoMessage*` | rate | **4** |
| **3 NONE** | ERC carries no discriminator | **never** | **11** |

**Detection: 11 load · 6 rate · 11 never.** **Failure modes: 11 wrong-number · 7 silent zero ·
5 no-signal · 3 loud null · 2 n/a.**

**The silent zeros outnumber the loud nulls 7 to 3**, which is N13's whole content restated as a
count: *a sentinel is indistinguishable from a real zero by inspection*. The three that fail loudly
are the safe ones.

### The self-check, and its honest limit

Step 2's `NONE` count and step 1's independently-computed *"unreachable by any probe"* count both
come out at **11**, and the script asserts they agree. **That is worth something and less than it
looks**: the classification is a judgement and the reconciliation is a measurement, so agreement
catches transcription and consistency errors — but both were derived from the same eleven gate
documents by the same reader, so it cannot catch a shared misconception. **A kind-3 entry that is
actually detectable would survive both.** The only thing that would catch it is another probe, which
is why the census is the part worth extending rather than the classification.

### ▶ Next session

**Step 3 needs decisions and is blocked on you** — the eleven `NONE` entries, `R18`–`R28`. Each has
exactly three dispositions, all with precedent: **submission requirement** (used four times — county
/place, `WorkersCompensationRate`, the drone axes, `SizeOfRiskRatingApplies`), **accepted unguarded
referral** (OI-49's standing candidate), or **ISO escalation** (E19, OI-57).

Two further decisions, from chunk 4: **does terrorism refer when a classification feeding it
refers** — it consumes a *sum*, so the propagation rule says no and I think that is wrong — and
**does OI-58's California re-evaluation semantics block the propagation rule**.

**Then steps 4–6**: settle propagation, emit the final register, pin it with
`tests/verify_referrals.py`.

### Step 3 begun — decision 1 of 13 taken

**`R18` — an `LCM` of exactly `1`. Disposition A: a required carrier parameter.**

Re-measured before putting it to the user, and it is broader than E15 filed: **10 LCM tables, 6
carrying exactly `1` in every countrywide edition, the 4 `*LCMCompany` tables empty in all 61
packages, 0 of 51 jurisdictions overriding any, and 11 rating paths consuming one.** The empty
company tables are the decisive evidence — **ISO ships a placeholder and leaves the carrier's slot
named and unfilled** — and the manual agrees at Rule 45.E: *"For rates, refer to company."*

**The real question was not "referral or not".** The project had already decided this once: **E9**
closed with *"hold at 1.0, a named overridable parameter"*, and **E15** reopened it with the
opposite proposal. They closed on different tables — E9 on the empty ones, E15 on the populated
`PremOpsLCM = 1` — but they are the same question asked at two different moments.

**The user's decision resolves both, and adds the reason the project did not have:**

> **This is a single-carrier build, and the LCM is configured to `1.0` to match RAaS**, so engine
> output is directly comparable with the oracle.

**That is an oracle-alignment decision, not an actuarial one**, and it is worth recording as such:
holding at `1.0` makes the base rate the ISO expected-loss figure, which is what RAaS returns — so
**a difference against the oracle is a rating defect and never a company deviation.** It is also
consistent with how RAaS already appears in the plan: as E1's answer for the rounding tie-break, and
as the source of the `Payloads/` baseline set.

**The referral moves from rate time to configuration time.** Refuse to rate when the parameter was
never supplied; never refer merely because it resolved to `1`, which is a legitimate carrier filing.
That gets E15's protection without its false positives.

**Recorded:** E15 **closed** onto E9, which stands reaffirmed with a reason · build plan §11 gains
*"This is a single-carrier build, configured for RAaS comparability"*, with the obligation that
**every company parameter is named, required and asserted at configuration time** · `R18`
reclassified NONE → DECLARED with a new detection point, `config`.

**Two things the decision changed in the tooling**, both worth noting because both were checks that
had been passing:

- **The self-check had to learn about decisions.** It asserted that the NONE count equals step 1's
  undetectable count. A decision legitimately breaks that equality — the corpus still carries no
  discriminator, but a decision supplied one from outside it. It now asserts
  `NONE + decided == undetectable`, because **a check that fails on every correct decision teaches
  people to ignore it.**
- **"Every DECLARED entry is detectable before rating starts" failed on `R18`** — its condition
  allowed only `load`, and `config` is *earlier* than load, not later. The check's condition was
  narrower than its own name.

### Decision 2 of 13 — `R19`, the 18 zero drone modifiers

**Refer to company, resolvable by an underwriter-supplied rate.**

Re-measured first, and the measurement made the decision easy: **all 18 zeros across the six drone
modifier tables are referral markers and not one is a legitimate factor** — and the filed values are
**discontinuous**, running `0.4 · 0.6 · 0.8 · 0.9 · 1 · 1.1 · 1.2 · 1.25 · 1.3 · 1.5` with **nothing
between `0` and `0.4`**. The zero is not a small number at the bottom of a range; it is a marker
wearing a number's clothes, and **that is visible in ERC alone**. The manual then confirms it
exactly — 24 of 24 cells on the usage axis, both directions — which keeps the doctrine intact: the
manual confirms, it does not source.

**Registered on (table, row) rather than "any zero in this table."** The difference is not
pedantry: a blanket rule would silently absorb a *new* zero on a new row as a referral, where a
row-level register fails loudly at load time saying it has found a marker it does not recognise —
which is exactly what a change in ISO's filing should do.

### And it introduced a mechanism the register did not have

The user's decision went further than the recommendation: **at the referral, the engine should
require an appropriate rate to be input.** That is *refer to company* taken literally — ISO declines
to price and hands it to the carrier, so the engine's job is not to stop but to **stop, say what it
needs, and resume when given it.**

**So the project now has two classes of company input, and they behave differently:**

| | Supplied | When |
|---|---|---|
| **Carrier parameter** (`R18`, the LCM) | once, per carrier | **configuration time** — the engine refuses to start without it |
| **Risk-level company input** (`R19`, a drone rate) | per submission | **at the referral** — rating resumes |

Build plan §5 gains *"A `REFER` is not always the end of the quote"*, and this **changes the
propagation design in §11**: `REFER` is absorbing under multiplication *until resolved*, and the
trace must record both the raise and the resolution — otherwise an audit cannot distinguish a
premium quoted after a referral from one that never referred.

**9 decisions remain** (`R20`–`R28`), plus terrorism propagation and OI-58.

### Verification at this point

`41_referral_register.py 20260812` **4/4** *(new; R18 decided)* · `40_referral_census.py` runs clean over 61
packages · `37_terrorism_align.py` **5/5** (was 4/4) · `39_state_specific_align.py` 4/4 ·
`38_rating_plans_align.py` 7/7 · `35_census_sizeofrisk.py` 5/5 · `34_crosscheck.py` 4/4 ·
`verify_golden.py` 80/80 · `verify_california.py` 11/11 · `verify_new_york.py` 10/10 ·
`verify_oi50.py` 7/7 · agent `smoke_test.py` 19/19.

### Documentation swept to this point

All updated and mutually consistent: `README.md` (status block, corpus tree, five agent corpora,
four test suites) · `docs/PRD-GL-RATING-ENGINE.md` (**65** items, **E1–E19**, four broker inputs,
and a plain-language account of the referral register) · `docs/GL-RATING-ENGINE-BUILD-PLAN.md`
(item 12 marked in progress with steps 1–2 done) · `docs/OPEN-ITEMS.md` · `docs/PHASE-SIZING.md`
(**§5's item-11 scope corrected** — five coverages in four states, not four in three) ·
`docs/gates/RECONCILIATION.md` (**R3 discharged**; `INV-EXTERNAL-DEPS` down to two genuinely
external inputs — loss history and the company LCM) · `scripts/README.md` · `docs/gates/` (15
documents) · docs HTML regenerated with **seventeen** tabs.

**Consistency, enumerated rather than asserted:** open items **OI-01 … OI-65, no gaps, 65
distinct** · escalations **18 raised of 19 numbers issued** (E13 deleted before filing, Step 28) ·
non-negotiables **N1–N18** · gate and analysis documents **15** · test suites **4** · ERC scripts
**42** · PDF-pipeline scripts **15** · agent corpora **5**, holding **1,120 of 1,120** documents on
disk · build order **14 items, 11 gated, 1 in progress** · referral register **28 entries, 11
awaiting decision**.

**No engine code until directed.**

---

## Step 49 — Item 12 step 3: all thirteen decisions taken. ~~NEXT SESSION STARTS HERE.~~ *(the live handoff is **Step 50**)*

- **Date:** 2026-08-12
- **Directed:** "lets go through decisions, 1 by 1" · "walk me through it" · "give me the TLDR"

**Step 3 of the chunk-5 plan is complete.** Eleven register entries plus two design decisions,
recorded in `41_referral_register.py` with the evidence and reasoning for each, and emitted to
`out/referral_register.json`. **`NONE` is now zero** and the reconciliation still balances.

### The thirteen

| | | Disposition |
|---|---|---|
| `R18` | `LCM = 1` | **A** — carrier parameter, `1.0` **to match RAaS** |
| `R19` | 18 zero drone modifiers | **B+** — refer, **resolvable** by an underwriter rate |
| `R20` | `Unknown` / `Not Applicable` | **B+** — same mechanism, distinct referral reason |
| `R21` | zero size-of-risk relativity | **D** — **not a referral**: assert and bounce |
| `R22` | county unmatched | **already decided** (E8) |
| `R23` | `WorkersCompensationRate` | **already decided** |
| `R24` | below the corpus floor | **already decided** (OI-41) — assert |
| `R25` | railroad class 40014 | **A** — submission field, first without ISO backing |
| `R26` | ten cannabis classes | **B+** — refer, resolvable |
| `R27` | TRIA prorating | **A** — take the filed full-term option |
| `R28` | PR composite rating | **E** — withhold; no escalation |
| `D01` | propagation | downstream of a **resolvable** referral pauses |
| `D02` | stability | a raised referral is **monotonic** |

**Three of the eleven were already decided elsewhere in the project** — the register was asking the
user to re-decide settled questions, because I classified from the gate documents and never checked
against the decisions register. **Four turned out not to be referrals at all.** **Two shrank by an
order of magnitude on measurement**: E19's *"188 classes"* is **ten, all cannabis and hemp**, and
*"non-construction railroad operations"* is **one class of four**.

### Three decisions changed the architecture rather than the register

**`R19` — a `REFER` is not always the end of the quote.** The user's addition — *at that point we
should be required to input an appropriate rate* — is refer-to-company taken literally, and it gave
the project two classes of company input that behave differently: a **carrier parameter** supplied
once at configuration (`R18`'s LCM) and a **risk-level company input** supplied at the referral
(`R19`'s drone rate). Build plan §5 now carries both.

**`R25` — a referral-only input may be sourced from the manual; a rating input may not.** Four
submission requirements had ISO-filed values behind them; this is the fifth and the first without
one. The ground: *the manual confirms and never sources* governs **rating**, and an input that can
only produce a `REFER` takes no price from anywhere. **The limit is recorded more prominently than
the permission**, because it is the kind of principle that gets stretched.

**`D01` — the propagation rule was wrong and terrorism exposed it.** The chunk-4 formulation —
absorbing under multiplication, not under summation — would have let terrorism rate on a partial
base, since its base is a *sum* of sibling premiums. Distributing is mathematically exact and
practically useless: **because `R19` made referrals resolvable, the missing number is coming**, so a
terrorism charge on a partial base is stale the moment the underwriter answers. **The rule turns on
resolvability, not on the operator** — a distinction only derivable after `R19` was decided.

### And the user caught the worst instance of the recurring defect

**Pointing at `Payloads/CA`.** I had claimed throughout that *"the project holds exactly one rated
output — 1 of 517 STC payloads, Oklahoma's."* **That was measured over the ERC corpus and stated
about the project.** `Payloads/` holds **53 rated outputs across 50 states, every one paired with
its input** — the RAaS baseline set, added 2026-08-10 and **documented in section G of the register
I have been maintaining all week.**

**It had reached two passing tests.** `verify_california.py` asserted *"California ships no oracle"*
and `verify_new_york.py` *"New York ships no oracle either"* — both green, because both globbed only
the ERC root. **A test that certifies a false claim is worse than no test**: I built the mechanism
meant to catch this and pointed it at the same wrong place.

Corrected in both fixtures (still 11/11 and 10/10, now asserting the true population), the two
differential documents, the rating-plans gate and the README. **OI-67**, with the standing lesson:
**enumerate the file system, not the one root you were thinking about.**

**What it changes:** California and New York can be **oracle**-tested once the engine exists, and
**OI-58's premium question is provable rather than unprovable**. One narrower claim survived and the
user confirmed it: **the payloads carry no experience-rating loss history**, so loss history remains
the one item-10 input with no oracle at all.

### Verification

`41_referral_register.py 20260812` **5/5, 13 decisions, 0 awaiting** · `40_referral_census.py` clean
· `37_terrorism_align.py` 5/5 · `38_rating_plans_align.py` 6/6 · `39_state_specific_align.py` 4/4 ·
`35_census_sizeofrisk.py` 5/5 · `34_crosscheck.py` 4/4 · `verify_golden.py` 80/80 ·
`verify_california.py` 11/11 · `verify_new_york.py` 10/10 · `verify_oi50.py` 7/7 · agent
`smoke_test.py` 19/19.

**The two new documents are registered**, and the smoke test now pins what they establish: the
Schedule & Experience corpus is **54**, `notices.json` totals **1,121**, `GL-PR-2015-CGLES-001` is
present, and **Composite Rating still has no Puerto Rico document** — which is the whole of what
remains of OI-61. The plan document itself is registered as kind `CGLES-PLAN` with a note: it
carries a plain-English filename, so a name-pattern sweep sees it as unparsed while a `*.pdf` sweep
sees it fine. **Third form of the naming-convention trap this corpus has sprung**, after `IL-` on
Composite Rating and `-TERXV-` on Terrorism.

### Documentation swept to this point

**`docs/PRD-GL-RATING-ENGINE.md` substantially rewritten** — §0 replaced with *"What changed
today"* (four more coverages, the rating plans found, the expert reviewer's two-fifths corpus, the
thirteen decisions, and the 53 priced examples), §8 *"Where we stand"* rebuilt around eleven
coverages and 54 answer keys, §9's correction list extended from three to **sixteen** with the
observation that most are now caught by machine rather than by re-reading, §6 flagging that
**phase 17 is worth bringing forward** because 53 of ISO's answers are already on disk, and the
counts and further-reading table brought current.

Also updated and mutually consistent: `README.md` · `docs/GL-RATING-ENGINE-BUILD-PLAN.md`
(propagation rule, disposition monotonicity, the referral-only-input licence and its limit,
single-carrier RAaS configuration) · `docs/OPEN-ITEMS.md` · `docs/PHASE-SIZING.md` ·
`docs/gates/RECONCILIATION.md` · `scripts/README.md` · `Agentic/iso-circular-expert/AGENT.md` ·
`docs/gates/` (15 documents) · docs HTML regenerated with **seventeen** tabs.

**Consistency, enumerated rather than asserted:** open items **OI-01 … OI-67, no gaps, 67
distinct** · escalations **18 raised of 19 numbers issued** · non-negotiables **N1–N18** · gate and
analysis documents **15** · test suites **4** · ERC scripts **42** · PDF-pipeline scripts **15** ·
agent corpora **5**, holding **1,122 of 1,122** documents on disk with **1,121** registered notices — the one unregistered is `GL-MI-2027-LC-003`, truncated at source (OI-56) ·
build order **14 items, 11 gated, 1 in progress** · referral register **28 entries, 13 decisions,
0 awaiting** · priced example policies **54** (1 ERC + 53 RAaS, 50 states).

## Step 50 — The build is specified. ~~NEXT SESSION STARTS HERE.~~ *(the live handoff is **Step 51**, and from here the build is logged in `BUILD-LOG.md`)*

- **Date:** 2026-08-12
- **Directed:** "create an html document that presents the current plan in plain English" · twelve
  build directives · "re-write this plan to me in layman's terms" · "do not build until I sign off"

### A one-page plain-English summary of the plan

**`docs/THE-PLAN-IN-PLAIN-ENGLISH.html`** — self-contained, no external references, ten sections,
~2,500 words, in the project's house style. Written to be read cold and sat with before deciding
what the build should look like: what we're building · why it is hard · the one rule everything
follows · where we are (with the 14-coverage table) · the four findings that changed the design ·
when the engine stops and asks · the thirteen decisions · how we will know it is right · **what is
not decided** · what happens next.

**The document leads on the open fork rather than burying it**: run ISO's rules directly, or rewrite
them in ordinary code. It is stated in business terms — *"California's 345 differences cost nothing"*
versus *"345 hand-written differences and another pass every ISO edition"* — because it is a
decision about cost and maintenance, not about taste. Testing strategy is explicitly marked as
deferred.

### The build is specified and awaiting sign-off — twelve directives, four decisions

**The fork is decided: EXECUTE ISO's rules, do not transliterate them.** And it was sized before
being accepted. Measured across **6,810 rule files in all 61 packages: 809,088 instruction
occurrences over 58 node types — 4 structural, 54 executable — and the top 20 nodes cover 94.1%.**
**14 node types appear fewer than 500 times each and one appears twice.** That is a small language:
~20 nodes make a working interpreter, 54 make a complete one, against the alternative of
hand-writing 4,461 rules per package plus **345 more for California alone**, repeated every ISO
filing.

**Build plan §5 rewritten.** `rating/sublines/` is gone — it existed only for the transliteration
fork — replaced by `interp/`. **The eleven coverage walkthroughs do not become code; they become the
acceptance tests that prove the interpreter reproduces them.** **E3's residual is now live work**:
that escalation closed with *"the evaluation contract, only if interpreting"*, and we are.

**Four decisions taken with it:**

1. **Two modes, one code path.** `strict-erc` reproduces ISO exactly with referrals recorded but not
   enforced — for proving correctness against RAaS, where a difference is a defect. `underwriting`
   enforces them. **The diff between the modes is itself a report**: every risk where ISO would quote
   and we would not.
2. **Build for all sublines; test on Prem/Ops and Products first.** No coverage-specific shortcuts
   in the engine.
3. **The 53 RAaS payloads are the payload basis**, not the 517 ERC submissions — only the former
   carry ISO's answers.
4. **Write `FROM-PLANNING-TO-BUILD.md` alongside the build, not after it** — recording per stage what
   it *expected* to inherit from the analysis against what it *actually* used, because that
   distinction is the value for a future line of business and is lost if written retrospectively.

**Four smaller corrections folded in:** the module tree assumed the wrong fork · a single class code
across all states is achievable (`10010`, present in at least 48 of 51 directly) **but the loss-cost
tables have different shapes by state** — CA/NJ put the territory in the filename with 3 columns,
OH/TX use 4, NY uses its own column names · CA/FL/NY/TX need a county or place field (E8) · **"all
states" is 51 jurisdictions including DC and PR; Hawaii is not in the corpus and cannot be rated.**

**[`docs/BUILD-STAGES.md`](docs/BUILD-STAGES.md)** — six stages, each gated exactly as the analysis
was: load and resolve · the interpreter · the kernel and the two modes · schemas and payloads · the
enum workbook · the UI. Plus the two diaries running throughout. **RAaS integration is explicitly
not built**, though the 53 examples let most of that comparison happen offline first.

**No code will be written until stage 1 is approved.**

### ▶ Next session

**Item 12, steps 4–6:** settle the remaining propagation detail against the register, emit the final
machine-readable form, and pin it with `tests/verify_referrals.py`. All three are unblocked — no
decisions outstanding anywhere in the project.

**Then item 13 (capture harness, 383 groups) and item 14 (policy assembly).**

**Worth doing early, and newly possible:** the 53 RAaS payloads are a far better testing position
than the plan assumes — §11 still describes RAaS as *"later, the external oracle, seam built now
against `NullOracle`"* while 53 of its answers sit on disk. Sizing what they cover, by jurisdiction
and coverage, would tell us which gated items can be oracle-tested on day one.

**No engine code until directed.**

### The two diaries are open, and empty

Directive 9 asked for a build diary and a file on how the planning was leveraged. **Both now exist
and both are deliberately empty of build content**, because no build content exists:

- **`BUILD-LOG.md`** — the build only. Same rules as this file: `n of N` counts, corrections kept
  rather than tidied away, exactly one live handoff marker. Entry 1 records that nothing has been
  written, and pins **what stage 1 will be measured against** *before* stage 1 — 51 jurisdictions
  resolving against their own declared parents, a pre-2022-09-01 date failing loudly, §10's
  assertions as failures, and the five table shapes typing correctly.
- **`docs/FROM-PLANNING-TO-BUILD.md`** — per stage: **Expected to inherit** (written blind, before
  the stage) · **Actually used** · **Verdict**. The expected sections are already written for all
  six stages and **must not be edited afterwards**; their value is entirely in having been wrong
  sometimes. The strongest claim recorded there, and the one most likely to fail, is that *the
  eleven walkthroughs will serve as interpreter acceptance tests with no coverage-specific code*.

Both are now tabs in `docs/GL-RATING-ENGINE-DOCS.html` (21 tabs). The PRD's "what's next" section
and the plain-English page's open fork were both rewritten to record the architecture decision as
**taken**, with the reasoning — 58 node types, 809,088 occurrences, top 20 = 94.1% — kept in plain
terms.

**Everything re-verified at this save point:** iso-circular-expert 19/19 · iso-erc-expert 88/88 ·
`verify_golden` 80/80 · `verify_california` 11/11 · `verify_new_york` 10/10 · `verify_oi50` 7/7.

---


---

## Step 51 — Analysis closes; the build begins. **NEXT SESSION STARTS HERE.**

- **Date:** 2026-08-12
- **Directed:** *"Build, when done, log, and then present TLDR in laymens term"*
- **Action:** **Stage 1 built** — `gl_engine/`, 1,814 lines, 11 modules, no third-party dependency.
- **Result:** `tests/verify_stage1.py` **18/18**, load-time assertions **13/13**, all prior fixtures
  and both expert agents unchanged.

**This log now hands over.** From this point the build has its own diary at
[`BUILD-LOG.md`](BUILD-LOG.md), with `docs/FROM-PLANNING-TO-BUILD.md` recording what each stage
expected to inherit from these fifty steps against what it actually used. `PROCESS_LOG.md` stays as
the record of the analysis and will only be amended when a build finding corrects one of its claims.

**Two such corrections already, both from stage 1:**

1. **§10's *"five table shapes"* was a conflation.** There are **four read shapes** and **three
   population states**, and they are orthogonal axes — N7 restated. Corrected in the build plan.
2. **`1.00` is used as a factor sentinel** — **E20 / OI-68**, the first escalation this project has
   raised from *running* the content rather than reading it. Three weeks of analysis catalogued
   eight meanings of `0` and never asked what `1` might mean, because nothing multiplies during
   analysis. **That is the recursive-harness premise arriving a stage earlier than planned.**

**A third finding amends an existing item.** **OI-69**: the split loss-cost defect recorded in OI-20
is wider than filed — in CA, NJ and OH the base table is **absent from the state package entirely**,
so the base name resolves upward to a header-only countrywide table and yields a finished premium
from zero rows. The engine's own first assertion for it **passed while blind**, counting 1 family
where there are 6. Fixed by enumerating all **75** loss-cost suffixes rather than the handful the
analysis had named.

### ▶ Next session

**Stage 2 — the interpreter — on your approval.** The largest new piece is the **evaluation
contract**, which E3 closed as *"only if interpreting"* and which was therefore never written.

---

## Step 52 — (next)

- **Date:**
- **Directed:**
- **Action:**
- **Result:**
