# Build Log — CF (Commercial Property) ERC Documentation

**Opened 2026-08-19.**

This is the diary of the documentation build for the CF (Commercial Property) ERC package —
the property-line counterpart to `Recursive_Harness_2.0`'s GL `BUILD-LOG.md`. The goal is the same
kind of artifact: a rating-algorithm map and a verified required-tables list per datadef group,
built by reading the ERC source directly, never inferred from examples or filled in from memory.

**Working directory:** `C:\Projects\Spreadsheet_Rater\CF`
**Source ERC package:** `C:\Projects\ISO_ERC_Files\CF\20260601\CFCW20260601V01`
**Companion document, plain-English version:** [`BUILD-LOG-PLAIN-ENGLISH.md`](BUILD-LOG-PLAIN-ENGLISH.md)
**Downstream consumer:** `C:\Projects\Recursive_Harness_2.0\CF_Algorithm\` — the harness project
evaluating whether/how to adopt ISO Property using the same method proven on GL.

---

## Standing criteria — adopted from the GL harness, applied here from the start

Rather than rediscover these the hard way (the GL build hit its own version of each of these before
naming them), they're adopted up front:

1. **Enumerate before deriving.** Before asserting a table, symbol, or rate is "not used" or a
   datadef group has no analog to something Building has, list what's actually in the `Rules`,
   `Rate Tables`, and `DataDefs` directories for that group rather than assuming from naming
   similarity to Building.
2. **Three-tier evidence.** Tier 1 (ERC XML/CSV) supplies every value, key, and rule. Tier 2 (manual
   PDFs, if consulted) may only *confirm* something present in ERC, never supply a mechanism ERC
   lacks. Tier 3 is the user — used to settle what tiers 1–2 cannot, and logged as a question here
   when it comes up, not silently guessed.
3. **Cite everything.** Every rule reference gets a file + line number, the same as the Building
   doc. A claim with no citation doesn't go in the document.
4. **Verify tables exist.** A required-tables doc isn't done until each table name has been checked
   against an actual `<TableName>.RateTable.csv` in `Rate Tables` — not assumed present because a
   `Lookup` rule names it.

---

## Entry 1 — Basic Group I, II, Broad, Special (Building/Structure) — the template

- **Date:** 2026-08-13 to 2026-08-18 (predates this log; recorded retroactively).
- **Directed:** Document how Building rating works in the CF ERC package, well enough that a data
  engineer could rebuild the calculation from the doc alone.
- **Built:**
  - `CauseOfLoss_Building_RatingAlgorithms.md` — traces `SetBlanketRatesAndFactors` (line 3094,
    `CommercialPropertyStructureRules.Rule.xml`) through all four cause-of-loss rate chains (Basic
    Group I, Basic Group II, Broad, Special) and their premium calcs, with a four-way comparison
    table and an end-to-end quick-reference formula per form.
  - `BasicGroupI_ERC_Tables.md` — every ERC rate table Basic Group I rating depends on (26 tables),
    each verified present as a `.RateTable.csv` with a matching `Def.RateTableDef.xml` in
    `CFCW20260601V01\Rate Tables`.
- **Checked against:** line-by-line reading of `CommercialPropertyStructureRules.Rule.xml` and the
  four `CommercialPropertyStructureBuilding*CoverageRules.Rule.xml` files; CW rate values spot-checked
  against the actual `.RateTable.csv` contents (e.g. `BroadFormBaseRate` CW values, `SpecialBldgTheft
  ExclusionFactor` = 0.88).
- **Open finding, not yet resolved:** `SpecialBuildingRate.RateTable.csv` has a header row only — no
  `CW` row filed. `SpecialBaseRate` is null at the countrywide level unless a state supplies its own
  row. Logged in the doc; not yet raised as a question because it may be intentional (state-filed
  line) rather than a gap — **candidate open question, see below.**

## Entry 2 — Scope set for the remaining datadef groups; logging established

- **Date:** 2026-08-19.
- **Directed:** Proceed to the next datadef groups using the same method, starting with
  PersonalProperty and SpecialClass (with BusinessIncome to follow). Record the build with two
  logs — this one, and a plain-English companion — so the process is legible to both a data
  engineer and a non-technical reader, with the explicit goal of feeding
  `Recursive_Harness_2.0`'s evaluation of adopting ISO Property.
- **Reconnaissance done before dispatching any work** (per standing criterion #1):
  - Confirmed `Recursive_Harness_2.0\CF_Algorithm\CauseOfLoss_Building_RatingAlgorithms.md` is
    byte-identical to the copy here — the harness project already treats this file as seed content.
  - Enumerated `CFCW20260601V01\Rules` (~600+ rule files). Confirmed three more top-level datadef
    groups exist with their own master orchestrator, parallel to `CommercialPropertyStructure`:
    `CommercialPropertyPersonalPropertyRules.Rule.xml`, and (grouped by `*CoverageRules.Rule.xml`
    suffix scan) `SpecialClass*` and `BusinessIncome*` / `SpecialClassBusnIncome*` families. Earthquake
    appears as a fifth cause-of-loss variant layered across most groups rather than its own datadef
    group — worth a short note rather than a full document.
  - Also enumerated a large tier of cross-cutting endorsement clusters (Ordinance or Law, Blanket
    Rating, Value Reporting Form, Agreed Value, Inflation Guard, Peak Season, Utility Services,
    Leasehold Interest, Builders Risk) that modify the base four chains rather than introducing new
    ones — deferred to a lighter-weight pass after the core datadef groups are documented.
- **Dispatched:** two parallel documentation passes, PersonalProperty and SpecialClass, same method
  as Entry 1 — see Entry 3 for results.

### Open question queued for the user

- **Q1 (from Entry 1's finding).** `SpecialBuildingRate` has no CW row filed — is that expected
  (Special-form building rating is intentionally state-only at countrywide edition) or a genuine gap
  in this package copy? Doesn't block PersonalProperty/SpecialClass work, so not blocking — flagged
  here rather than interrupting.

---

## Entry 3 — PersonalProperty and SpecialClass documented; a verification-method gap found and corrected

- **Date:** 2026-08-19.
- **Built:**
  - `CauseOfLoss_PersonalProperty_RatingAlgorithms.md` + `PersonalProperty_ERC_Tables.md` — traces
    `CommercialPropertyPersonalPropertyRules.Rule.xml` and `CommercialPropertyOccupClassRules.Rule.xml`
    (the true chain-runner, `ErcSetPostRatesAndFactors`, lives separately from the `ForEach` that
    iterates occupancy classes) through all four cause-of-loss forms.
  - `CauseOfLoss_SpecialClass_RatingAlgorithms.md` + `SpecialClass_ERC_Tables.md` — traces
    `CommercialPropertySpecialClassRules.Rule.xml` and its four core premium files, explicitly scoped
    to exclude endorsement add-ons (`SpecialClassAgreedVal*`, `SpecialClassInflationGuard*`,
    `SpecialClassBusnIncome*`) and the native fifth chain (Earthquake).
- **Checked against:** same method as Entry 1 — line-numbered rule citations, table existence
  verified against `Rate Tables`.

### Structural findings worth carrying forward

- **Personal Property rates N records per location** (a `ForEach` over occupancy classes), not one
  record per building like Structure — the iteration boundary matters for any engine built on this.
- **Personal Property's deductible factors for BGI/BGII/Broad are not computed locally** — they're
  copied from an ancestor context several levels up the datadef tree (traced to a same-named rule in
  the SpecialClass ruleset that sits as a sibling under `CommercialPropertyLocation`, but the exact
  relative-path resolution wasn't conclusively confirmed from the XSD — **open question, see below**).
- **Special Class has no limit-of-insurance factor anywhere** in any of its four chains or four
  premium files (confirmed by exhaustive grep) — a structural absence, not an oversight in reading.
- **Special Class's Broad-form base rate reads a hard-coded `"Frame"` construction key** regardless
  of the actual building's construction type — flagged as a possible package quirk, not resolved.
- Personal Property's Special form is the richest of its four chains (14 steps, own territory
  multiplier, Watchman/Burglary-Alarm credits) — the inverse of Building, where Special is the
  simplest chain. **Don't assume a form's relative complexity carries across datadef groups.**

### Correction — "table verified present" was checking existence, not content

Personal Property's agent, checking `BasicGroupIRate` (shared with Building), found the file has a
header row and **zero data rows** — no `CW` row, no rows at all. Same for `BasicGroupIIRate` and
`LowestBasicGroupIIRate`. Verified directly against the CSVs (not re-derived from the agent's report):

```
BasicGroupIRate.RateTable.csv        — 1 line (header only), 0 CW rows
BasicGroupIIRate.RateTable.csv       — 1 line (header only), 0 CW rows
LowestBasicGroupIIRate.RateTable.csv — 1 line (header only), 0 CW rows
```

`BasicGroupI_ERC_Tables.md`'s original Verification section (Entry 1) claimed all 26 tables
"confirmed present" — true, but that check stopped at file existence and never opened the file to
check for a data row. **Corrected in place in that document** (kept as a visible correction, not
silently edited away) rather than only noted here. Practical consequence: Basic Group I and Basic
Group II base rates are unresolvable at the countrywide level, for both Building and Personal
Property, in this package edition — a state filing is required for either to rate at all.

**Standing check added:** every future required-tables doc must report row counts and confirm at
least one non-empty data row per table, not just file existence.

### Open questions queued for the user

- **Q1 (from Entry 1, still open).** `SpecialBuildingRate` has no CW row — expected (state-only by
  design) or a gap in this package copy?
- **Q2 (new).** `BasicGroupIRate` / `BasicGroupIIRate` / `LowestBasicGroupIIRate` are also header-only
  at CW level — same question as Q1, now affecting the two highest-volume Basic forms across two
  datadef groups. Worth checking whether a state-level package (not the CW one) has been licensed and
  should be the actual source for these three tables.
- **Q3.** The exact ancestor path Personal Property's `../../../../DeductibleFactorBasicGroupI` (etc.)
  resolves to — needs an XSD read the agent didn't complete, or a direct answer if already known.
- **Q4.** Special Class's hard-coded `"Frame"` key in its Broad base-rate lookup — intentional
  simplification, or should it read the actual construction type?

### ▶ Next session

BusinessIncome next (novel rate mechanic — income-based, not value-based; also introduces Earthquake
as a real fifth chain rather than a deferred note). Then the endorsement-cluster pass. Sync new docs
to `Recursive_Harness_2.0\CF_Algorithm\` — done this session for all four files plus the corrected
tables doc.

---

## Entry 4 — decision-chain visualization added as a standing deliverable

- **Date:** 2026-08-19.
- **Directed:** "Can we create visualizations of the different rating paths for each (basically if,
  then, down the chain)" — then, after seeing the result: "For all future calculation steps, we
  need to create and save something like this."
- **Built:** `cf-rating-chains.html` — a single self-contained page with one if/then decision-tree
  flowchart per cause-of-loss form (12 so far: Building × 4, Personal Property × 4, Special Class ×
  4), plus an overview matrix landing view. Published as a Claude Artifact:
  **https://claude.ai/code/artifact/0d304507-9df4-46c7-bdc3-340621569cdc**
- **Source of truth:** `C:\Projects\Spreadsheet_Rater\CF\cf-rating-chains.html`, mirrored to
  `Recursive_Harness_2.0\CF_Algorithm\cf-rating-chains.html` — the artifact is *published from* this
  file, not the other way around; the file is what future sessions edit and re-publish.

### Standing criterion — added

**Every future datadef group or coverage pass documented from here forward gets a decision-chain
diagram added to this same page, not a new one.** Extend, don't fragment:

1. Add the new form(s) to the sidebar nav and the overview matrix in `cf-rating-chains.html`.
2. Build each diagram from the algorithm doc's already-cited gates/branches — collapse pure
   arithmetic into single "computed factor" boxes; only branch the tree where the ERC rules
   themselves branch (gates, `Choose` branches, gated zero-outs). This is what kept a 14-step chain
   (Personal Property's Special form) readable instead of a wall of multiplication.
3. Use the existing node classes (`gate` amber, `zero` rust, `final` green, `step` blueprint,
   `openq` dashed amber-rust for flagged findings) — don't invent a new palette per section.
4. Republish to the **same artifact path** so the URL above stays live and simply grows more
   sections, rather than minting a new link every pass.
5. Sync the updated file to `Recursive_Harness_2.0\CF_Algorithm\` alongside the markdown docs, same
   as every other deliverable in this log.

**Deliverable set per coverage pass is now three things, not two:** the algorithm doc, the
required-tables doc, and a set of sections added to `cf-rating-chains.html`.

---

## Entry 5 — Business Income documented: rates borrowed cross-coverage, and a novel surcharge shape

- **Date:** 2026-08-19.
- **Directed:** "ok, lets continue with Business Income."
- **Built:**
  - `CauseOfLoss_BusinessIncome_RatingAlgorithms.md` + `BusinessIncome_ERC_Tables.md` — traces
    `SetBlanketRatesAndFactors` (line 2201, `CommercialPropertyBusinessIncomeRules.Rule.xml`) through
    five cause-of-loss chains: Basic Group I, Basic Group II, Broad, Special, **and a real
    Earthquake chain** (`SetEQRatesAndFactors`). Row-count verification applied throughout per the
    Entry 3 correction — 45+ tables checked for both existence and actual data.
  - Five new sections added to `cf-rating-chains.html` (same artifact, same URL, extended per the
    Entry 4 standing criterion) — overview matrix grew a fourth column plus an Earthquake row.
- **Checked against:** line-numbered citations throughout; CW row counts confirmed directly against
  the CSVs, not just existence.

### Structural findings worth carrying forward

- **This coverage is nested inside Structure in the schema** (`CommercialPropertyBusinessIncomeTable`
  declared inside `CommercialPropertyStructure` in the XSD) — Business Income is always a child of a
  Building record, not a sibling.
- **Basic Group I, Basic Group II, and Earthquake don't compute their own base rates at all** — they
  read the coinsured Building's *already-computed* `BasicGroupIBaseRate` / `BasicGroupIISymbolToUse`
  / `EQBaseRate` and apply one small Business-Income-specific adjustment factor on top. Only Broad
  and Special have their own dedicated base-rate tables. This is a materially different pattern from
  anything in the first three coverages — none of Building/Personal Property/Special Class reach
  into a *different* coverage's already-computed rate this way.
- **Coinsurance is not an independent factor here.** A single shared `Factor` — one of
  MaxPeriodOfIndemnity / MonthlyLimitOfIndemnity / ExtraExpense / TypeOfRisk, mutually exclusive —
  absorbs what Building splits into separate coinsurance, LOI, and deductible steps. It's applied
  **only** to Basic Group I/II; Broad and Special are straight copies of their cause-of-loss-adjusted
  rate with no Factor at all.
- **No deductible-factor rating anywhere** in the base chain (outside two Earthquake flat-dollar
  endorsement forms) — Business Income's "deductible" is a waiting period baked into the rate, not a
  scheduled dollar table.
- **Add-on coverages (Agreed Value, Extended Period of Indemnity) charge only `(Factor − 1) × Rate ×
  Limit/100`** — an incremental-surcharge shape that appears nowhere in Building or Personal
  Property, where endorsement premiums always multiply the *full* factor into the whole rate.
- **Earthquake is a real fifth rate chain with no standalone premium file** — `FinalEQRate` computes
  unconditionally, but only the Agreed Value coverage record ever converts it into chargeable
  premium. A non-Agreed-Value, non-blanket EQ policy has no scheduled premium path in this package.
- Premium files are far more uniform than Building's — every form has exactly two branches
  (scheduled/blanket), and Special is *not* a structural outlier the way it is in Building (its
  premium file is byte-shape-identical to Broad's here).

### Correction pattern held: row-count verification applied cleanly this pass

No new correction needed — Entry 3's standing check (row count, not just file existence) was applied
throughout by the documenting agent without prompting, and it caught a real, consequential result:
**`BasicGroupIIRate`, `LowestBasicGroupIIRate`, and `BaseRateAdjustmentFactor` are all header-only**,
meaning Basic Group I and Basic Group II Business Income rating is *doubly* unresolvable at
countrywide level — both the underlying Building rate and Business Income's own adjustment factor
return null. Broad and Special's own tables, by contrast, do carry CW data and resolve fine.

### Open questions queued for the user

- **Q1–Q5 (prior entries, still open).** No new information this pass.
- **Q6 (new).** Is the missing standalone (non-Agreed-Value) Earthquake premium file for plain
  Business Income intentional — i.e., earthquake time-element coverage is only ever sold on an
  Agreed Value basis when scheduled — or is there a premium path elsewhere in the package not
  found in this pass? Not resolved from the ERC files alone.

### ▶ Next session

Special Class Business Income exists as a fully parallel datadef group (confirmed by file-name
inventory, not traced) — candidate for a future pass if the harness needs it. Otherwise: the
cross-cutting endorsement-cluster pass (Ordinance or Law, Blanket Rating, Value Reporting Form,
Agreed Value, Inflation Guard, etc.) that was deferred back in Entry 2 is the next thing on the
board, plus following up on the six now-open questions with whoever can answer them.

---

## Entry 6 — agent roster documented; two specialist agents defined and folded into the plan

- **Date:** 2026-08-19.
- **Directed:** "Create a document tnat enumrates all agents, and the agent plan. Add agents for ERC
  and Circular experts/interpreters as well, and fold that into the plan." Issued alongside "do
  special form" (Special Class Business Income — Entry 4's dispatched agent #4, tracked separately).
- **Built:** `AGENTS.md` — full inventory of the four documentation agents dispatched this session
  (see the file for per-agent detail), the briefing pattern all four share, and a new Part 3 folding
  in two specialist agents modeled directly on `Recursive_Harness_2.0`'s existing GL four-agent
  structure (`gl-authority`, `iso-erc-expert`, `iso-circular-expert`, `gl-engine-code-expert`):
  - `Agentic\cf-erc-expert\AGENT.md` — CF's counterpart to `iso-erc-expert`. Corpus measured
    (447 directories at depth ≤2 under `ISO_ERC_Files\CF\`, edition-date-first layout, 8 editions);
    role and evidence discipline specified; no knowledge base or retrieval tooling built yet —
    explicitly marked as the next build step, in priority order, inside the file itself.
  - `Agentic\cf-circular-expert\AGENT.md` — CF's counterpart to `iso-circular-expert`. Corpus
    checked: six countrywide-only Rules PDFs at `Commercial Line Manuals\CF\CW\`, none extracted,
    no state-specific notices, no loss-cost corpus, no other plan family confirmed to exist for CF
    — against GL's 1,122-document, five-corpus-family equivalent. Named its own first task: confirm
    whether state-specific CF notices exist anywhere before building anything else.
- **Not built:** `cf-authority` and `cf-engine-code-expert` CF equivalents — deliberately left
  unstarted. `gl-authority`'s value depends on two already-independently-solid specialists to
  cross-check; building the CF authority agent first would just be another unverified source.
  `gl-engine-code-expert` has nothing to review until a CF rating engine exists, which it does not.
- **Checked against:** directory listings for both corpora (`ISO_ERC_Files\CF\`, `Commercial Line
  Manuals\CF\CW\`), and a full read of all four existing GL `AGENT.md` files before drafting the CF
  equivalents, so the new specs matched GL's actual evidence-tier language and output-contract shape
  rather than a paraphrase of it.

### Why this matters for the harness-adoption question

This is the first artifact in the CF track that explicitly mirrors the GL harness's own agent
architecture rather than just its documentation-doctrine (evidence tiers, row-count verification,
open-question logging). It's a concrete answer to "how does this connect to Recursive_Harness_2.0" —
the two new specialist agents are scaffolding for the same kind of self-checking review loop GL
already has, sized honestly to how much of the CF corpus is actually ingested today (a lot of ERC
content, almost none of the manual/circular side).

### ▶ Next session

Two independent tracks, per `AGENTS.md` Part 4: (1) finish Special Class Business Income
(dispatched, in flight as of this entry) then the deferred endorsement-cluster pass; (2) start
building out `cf-erc-expert`'s retrieval tooling, and separately, resolve `cf-circular-expert`'s
first open question — do state-specific CF Rules notices exist anywhere to collect.

---

## Entry 7 — Special Class Business Income documented; countrywide circular corpus ingested

- **Date:** 2026-08-19.
- **Directed:** "do special form" (Special Class Business Income, dispatched at the end of Entry 6)
  followed by "start with Countrywide Circulars here, I will download state specific versions
  shortly: `Commercial Line Manuals\CF\CW`".

### Special Class Business Income — documented

- **Built:** `CauseOfLoss_SpecialClassBusinessIncome_RatingAlgorithms.md` +
  `SpecialClassBusinessIncome_ERC_Tables.md`, tracing `CommercialPropertySpecialClassBusnIncome
  Rules.Rule.xml`.
- **Biggest finding:** this coverage is overwhelmingly a clone of plain Business Income's pattern,
  not Special Class Building's — but pushes the cross-coverage rate-borrowing pattern further.
  Basic Group I and Earthquake don't just borrow a *base* rate from the coinsured Special Class item
  the way plain Business Income borrows from Building — they borrow the item's **already fully-rated**
  `BasicGroupIRate`/`EQRate` directly, adding at most one trivial multiplier on top. Broad and Special
  key their own dedicated base-rate tables on **hard-coded literal constants** (`"Frame"` for
  construction; `"Other than Apartments and Condominiums"` for the occupancy dimension) — the same
  construction-blind pattern Entry 3 found in Special Class Building's own Broad form, now confirmed
  extending to a second dimension in this coverage.
- **Two corrections to prior-pass uncertainty, resolved rather than left open:** the plain-BI doc's
  question about whether a Basic Group II Extended Period of Indemnity file exists is now answered
  — it does, giving both Business Income groups a full symmetric 5-form set.
- **New open question (Q7):** hard-coding "Other than Apartments and Condominiums" makes the
  "Apartments and Condominiums" rows of the theft-exclusion table permanently unreachable from this
  coverage — intentional ISO simplification, or an authoring inconsistency? Not resolved from ERC
  alone.
- **Not yet done:** decision-chain diagrams for this coverage's five forms — `cf-rating-chains.html`
  has not been extended with a fifth nav group yet. Flagged here so it isn't lost; do it before
  calling this coverage's documentation complete.

### Countrywide circular corpus — ingestion started

First real work on `cf-circular-expert` since it was defined in Entry 6. Built
`scripts/16_extract_cf_manuals.py` (in `Recursive_Harness_2.0`, mirroring GL's
`15_extract_manual_family.py`) and ran it against the six PDFs at `Commercial Line
Manuals\CF\CW\`.

- **All six extracted successfully** — 2,060 pages total, page-tagged (`<<<PAGE n>>>`, same
  convention GL uses). This machine has no `pdfinfo` on PATH, so extraction fell through entirely to
  the `pypdf` path; quality was checked by hand against the raw text and is clean, not garbled.
- **Manual identified:** Commercial Lines Manual, **Division Five** — Fire and Allied Lines —
  Multistate Rules. Resolves the "unverified division number" caveat `cf-circular-expert/AGENT.md`
  carried since Entry 6.
- **A partial rule-number index** written to `Agentic/cf-circular-expert/knowledge/rule_index.json`
  — about 35 of an estimated 85+ rules, built from one direct TOC read and explicitly marked
  incomplete in its own metadata. Rules 23–36 were only visible in appendix fragments, not a clean
  contiguous TOC pass — a real gap to close, not a rounding error.
- **The first genuine cross-corpus agreement point in this whole project.** The ERC-side Building
  documentation (Entry 1, written 2026-08-13/18, well before this manual corpus was ever opened)
  cites "bureau rule 71.E.2 / 71.E.3 / 71.E.4" for the Broad-form base-rate table. The manual's own
  Rule 71 is titled "Causes Of Loss — Broad Form," at pages CF-99–CF-103. Independently derived,
  independently confirmed — exactly the shape of evidence `cf-authority` will eventually be built to
  find systematically. Also checked: **Rule 71 sits at the same number and page range in both the
  2020 and 2026 editions** — one data point toward "CF rule numbers are more stable across editions
  than GL's," not yet generalized.
- Also confirmed by name-matching (not yet formula-level cross-checked): Rule 38 ↔ Building/Personal
  Property, Rule 50/51 ↔ Business Income, Rule 65 ↔ Leasehold Interest, Rule 73 ↔ Earthquake as a
  full standalone cause-of-loss form (matching this project's own finding that Earthquake is a real
  fifth rate chain in three of the four datadef groups documented so far), Rule 75 ↔ the CP 10 45 /
  CP 10 29 earthquake sub-limit machinery found in the Business Income doc.
- **State-specific notices are pending** — the user is adding them to the same source folder
  shortly. `scripts/16_extract_cf_manuals.py` re-extracts everything on each run rather than tracking
  incremental state, so it just needs re-running once they land. The countrywide notices themselves
  say "refer to individual state Notices for the approval/implementation circular references" —
  meaning state exceptions most likely live in those forthcoming documents rather than in a separate
  corpus family, though this is unverified until they're actually here.
- `cf-circular-expert/AGENT.md`'s own status section, "what you have today" table, and
  "known limits" section were all updated in place to reflect this — its build-priority list now
  has item 1 struck through and item 2 (state notices) promoted to the top of what's left.

### Open questions queued for the user

- **Q1–Q6 (prior entries), still open.**
- **Q7 (new).** Is Special Class Business Income's hard-coded "Other than Apartments and
  Condominiums" occupancy key (making the "Apartments and Condominiums" theft-exclusion rows
  permanently unreachable) intentional or an authoring inconsistency?

### ▶ Next session

Build the five Special Class Business Income diagrams into `cf-rating-chains.html` (flagged above as
not yet done). Re-run `16_extract_cf_manuals.py` once state-specific CF notices land, then pursue
`cf-circular-expert`'s next priority: finish the rule-number index from a clean TOC pass. Otherwise
per `AGENTS.md` Part 4: the deferred cross-cutting endorsement cluster documentation pass, and
`cf-erc-expert`'s own build-out (retrieval tooling, knowledge base).

---

## Entry 8 — Special Class Business Income's diagrams added; documentation coverage now complete for all five coverages

- **Date:** 2026-08-19.
- **Directed:** "yes, add to rating-chains." (closing the item flagged as not-yet-done at the end of
  Entry 7).
- **Built:** five new sections in `cf-rating-chains.html` (Basic Group I, Basic Group II, Broad,
  Special, Earthquake) — same artifact, same URL, extended per the Entry 4 standing criterion. The
  overview matrix grew a fifth coverage column. Intro copy updated: "seventeen chains" → "twenty-two
  chains."
- **Diagram-authoring note:** Basic Group I and Earthquake's diagrams are visibly the simplest of
  all twenty-two — a single gate feeding a single "borrow the sibling's finished rate" box, since
  that's structurally all those two chains do. Didn't force extra nodes in to make them look more
  substantial; the diagram is honest about how little work those two chains actually perform.
- **Checked against:** full read of `CauseOfLoss_SpecialClassBusinessIncome_RatingAlgorithms.md`
  before authoring, same discipline as every prior diagram pass.

Documentation is now complete, in both the `.md` and diagram form, for all five coverages
originally scoped: Building, Personal Property, Special Class, Business Income, Special Class
Business Income. Remaining documentation work is the deferred cross-cutting endorsement cluster
(Entry 2) — a lighter-weight pass by design, not a sixth full coverage.

### ▶ Next session

Per `AGENTS.md` Part 4: the endorsement-cluster documentation pass, and continued build-out of
`cf-erc-expert` / `cf-circular-expert`. Re-run `scripts/16_extract_cf_manuals.py` once
state-specific CF notices land — flagged again here since it's easy to lose track of a
"do this later" instruction between sessions.

---

## Entry 9 — full coverage inventory: what still needs rating definition

- **Date:** 2026-08-19.
- **Directed:** "Review circulars and ERC files, and identify coverages that require rating
  definition, similar to what we have done already. Don't do anything other than identify them.
  Include in an MD file, and track whether we have defined rating for them." Explicitly
  identification-only — no tracing, no diagrams, no new algorithm docs this pass.
- **Built:** `Coverage_Inventory_And_Tracking.md` — swept the whole `Rules` directory for
  `*CoverageRules.Rule.xml` files defining a `SetPremium` rule (the same signal every coverage
  documented so far turned out to have), normalized away cause-of-loss-form and coverage-type
  suffixes, and collapsed 369 matching files into **97 distinct coverage/endorsement families**.
- **Result:** confirmed exactly **5** families carry their own master `Set*RatesAndFactors`
  orchestrator (Structure, Personal Property, Special Class, Business Income, Special Class Business
  Income) — the five already fully documented. **91 of the remaining 92 families are not yet
  documented at all**; 3 are partially covered because their surcharge mechanism was described inline
  while documenting a parent coverage (Agreed Value, Extended Period of Indemnity) without being
  independently traced.
- **Biggest undocumented clusters, by file count:** Ordinance or Law (18 families — Coverage A/B/C,
  combined B-and-C, and the Tenants'-Interest-In-Improvements variant split three ways again by cause
  of loss) and the Business Income time-element extensions (17 families — dependent properties,
  computer-operations interruption, civil authority, landlord-as-additional-insured, and more).
- **One find worth flagging:** `LimitedCoverageForUnmannedAircraftScheduledAndOrBlanket` has no
  `SetPremium` in its own dispatch file, which would have made the sweep miss it entirely — but five
  separate `*Detail*Rules.Rule.xml` variants (one per attaching coverage) do carry their own rate
  chains. Caught only because a broader `Set*RatesAndFactors` grep was cross-checked against the
  `SetPremium`-only sweep. A reminder that a single search pattern, however well-chosen, can still
  miss something — cross-checking against a second pattern is what caught this one.
- **Explicitly not done:** no algorithm docs, no tables docs, no diagrams for any of the 91/92. This
  is a map of what's left, not a start on any of it.

### ▶ Next session

The inventory itself names where a next documentation pass would get the most coverage per hour:
Ordinance or Law and the Business Income time-element cluster. Otherwise unchanged from Entry 8:
`cf-erc-expert`/`cf-circular-expert` build-out, and re-running the manual extraction once
state-specific CF notices land.

---

## Entry 10 — correction: Entry 9's sweep undercounted by more than half; Earthquake and Flood found

- **Date:** 2026-08-19.
- **Directed:** "what about earthquake and flood" — a direct question about two families visibly
  absent from Entry 9's inventory.
- **Found:** neither Earthquake nor Flood has a `*CoverageRules.Rule.xml` file — ISO named this whole
  cluster `*EndorsementRules.Rule.xml` / `*Rules.Rule.xml` instead (no `"Coverage"` immediately before
  `"Rules"`). Entry 9's glob (`*CoverageRules.Rule.xml`) silently skipped every file shaped that way.
- **Re-swept with no filename restriction:** `grep -lE '"SetPremium"' *.xml` across the whole `Rules`
  directory returns **546 files, not 369** — 177 more than Entry 9 counted. After the same
  normalization, that's **243 distinct families, not 97.** Entry 9's count was missing more than half
  the package.
- **Corrected in place, visibly** — `Coverage_Inventory_And_Tracking.md` now carries a dated
  correction block at the top of Method (not a silent edit), a new Part B11 itemizing Earthquake (4
  endorsement-form variants × up to 5 attaching coverages) and Flood (2 form families, plus a
  same-name-adjacent-but-distinct sewer/drain coverage flagged so it doesn't get merged in by a future
  pass), a "What's still not itemized" section naming the ~146 newly-surfaced families this correction
  does *not* individually list yet, and a corrected summary table.
- **Scope note preserved, not lost in the correction:** the Earthquake *cause-of-loss chain* inside
  Special Class / Business Income / Special Class Business Income (`SetEQRatesAndFactors`,
  `FinalEQRate`, the Agreed-Value-only premium asymmetry) **is** already documented — what's newly
  identified is a separate thing, the standalone endorsement that attaches earthquake coverage to a
  policy in the first place. The relationship between the two has not been traced.
- **The lesson, stated for reuse:** a single filename pattern is a hypothesis about ISO's naming
  convention, not a guarantee of it — the same shape of miss as Entry 3 (checking existence without
  checking content), here it's checking one naming pattern without checking for a second one. Standing
  habit worth carrying forward: **a search returning zero results for something you'd expect to exist
  is a prompt to widen the search, not a reportable absence.**

### ▶ Next session

Finish itemizing the ~146 not-yet-listed families the corrected sweep surfaced (command to reproduce
is in the doc's correction note). Otherwise unchanged from Entry 9: Ordinance or Law and the Business
Income time-element cluster remain the largest itemized undocumented groups; `cf-erc-expert`/
`cf-circular-expert` build-out and the state-specific manual re-extraction are still outstanding.

---

## Entry 11 — state circulars landed: 5 states extracted, characterized, and tracked to avoid re-review

- **Date:** 2026-08-19.
- **Directed:** "we have added state circulars to `Commercial Line Manuals\CF`, review, and create an
  MD (or a master tracking MD) that lists which circulars have been reviewed, to avoid duplicate
  review in the future."
- **Found:** 40 new state PDFs landed in per-state subfolders — `AK` (6), `AL` (6), `AR` (10), `AZ`
  (8), `CA` (10) — sibling to `CW\`, not inside it. Updated `scripts/16_extract_cf_manuals.py` to
  sweep every subfolder of `Commercial Line Manuals\CF\` instead of hard-coding `CW` (the docstring
  already told a future session to expect this; done now rather than re-discovered later).
- **Built:** `Circular_Review_Tracking.md` — the master ledger the user asked for. Defines four
  review levels (L0 not extracted → L3 deep-read) and is explicit that **every one of the 46 notices
  on disk is currently L2 at best** — front matter and exception-rule-numbers characterized, no rule
  *text* read line-by-line yet for any of them. That distinction is the whole point of the ledger:
  it should stop a future session from either re-doing L2 work that's already done, or assuming L2
  work means something it doesn't.
- **Real finding, not just bookkeeping:** all five states file **exception pages**, not full manual
  reprints (22–80 pages vs the countrywide manual's ~342–346) — this **resolves the open question**
  `cf-circular-expert/AGENT.md` had carried since Entry 6/7 about whether CF varies meaningfully by
  state. A near-universal core set of countrywide rule numbers (2, 14, 38, 50, 72, 73, 75, **81, 82**,
  85) gets exception-paged in nearly every state/edition; each state also files its own numbered
  local rules (`A1`–`A14`, count grows over time within a state). **Rules 81 and 82 are new numbers
  not previously in `rule_index.json`** — identified from California's front matter as "Revision And
  Expansion Of Deductible Insurance Plan" and "Windstorm Or Hail Percentage Deductibles" respectively.
  Not yet added to `rule_index.json` itself — flagged as next-session work in both the ledger and
  here, not done silently.
- **California flagged as the highest-value next L3 target**: broadest exception-rule set of the five
  (18 countrywide rules touched vs. Arizona's 11), unique wildfire-mitigation content, and three
  ZIP-code-territory-definition notices that plausibly interact with ERC-side territory factors
  already documented (`BasicGroupIRatingTerrFactor`, `BasicGroupIIRatingTerr`) — that interaction was
  **not** checked in this pass.
- **Loose ends named, not chased**: several front-matter fields didn't parse (blank filing/circular
  refs on a handful of notices — likely OCR whitespace artifacts, same caveat GL's extractor
  documented); Arkansas's `CL-2025-RRU1` filing-ref prefix is the only non-`CF-` prefix seen and
  wasn't investigated; multi-notice-per-year supersession order (two 2020, two 2025, two 2026
  Arkansas notices; two 2023 Arizona notices at the same page count with a drop from 30→22 pages
  between editions) was not determined — `date_confidence`, the field GL's registry uses for exactly
  this, is not populated in CF's `notices.json` yet.
- **`cf-circular-expert/AGENT.md` updated in place** — status section, corpus table, and build-priority
  list all reflect the new state layer and point at the tracking ledger as the first thing to check.

### ▶ Next session

Per the ledger's own "suggested order": add rules 81/82/83 to `rule_index.json` (cheap, already
half-derived here); take California to L3 (actual rule text, compared against both the countrywide
baseline and the ERC territory-factor documentation); resolve the Arkansas filing-ref anomaly and the
general supersession-order question. Otherwise unchanged: the ~146 not-yet-itemized coverage families
from Entry 10, and Ordinance or Law / Business Income time-element as the largest itemized clusters.

---

## Entry 12 — five more states ingested: Florida overtakes California as the top L3 candidate

- **Date:** 2026-08-19.
- **Directed:** "Circulars for Colorado, Connecticut, DC, Delaware, and Florida have been added for
  review."
- **Built:** re-ran `scripts/16_extract_cf_manuals.py` (no changes needed — already generalized to
  sweep every state subfolder, per Entry 11) — 33 new documents extracted (CO 10, CT 9, DC 6, DE 7,
  FL 1), bringing the corpus to 79 documents, 4,769 pages. Characterized the same way as the first
  five states and extended `Circular_Review_Tracking.md` with five new per-state sections rather than
  a new file.
- **Ten jurisdictions now confirm the exception-page pattern** (thin, 22–80 pages, not full reprints)
  — the open question from Entry 6/7 is settled more firmly than a five-state sample already made it.
- **Florida (currently one notice, 2022) has the broadest exception-rule set of any jurisdiction seen
  — wider than California's**: 23 countrywide rule numbers touched (2/4/9/10/11/13/14/17/21/25/33/36/
  38/50/54/70/72/73/74/75/81/82/85) plus the full state-rule set A1–A14, all from a single notice.
  Four rule numbers (4, 9, 21, 33) appear nowhere else in the corpus. **Florida now displaces
  California as the top-priority L3 target** in the ledger's suggested order.
- **A pattern, not a typo, in the filing-reference anomaly first seen in Arkansas (Entry 11).** Four
  more non-`CF-`-prefixed filing refs turned up: Connecticut's `CL-2022-ORU1`, DC's `CA-2023-REQRU`
  (odd — California's state code appearing on a DC document), Delaware's `CL-2025-ORU1`, and
  Florida's `CL-2021-RRU1`. Five occurrences across four states now — logged as "worth resolving
  before this project relies on filing-ref prefixes for anything," not chased down in this pass.
- **Colorado and DC turned out to be the flattest/most stable jurisdictions** — Colorado's
  exception-rule set doesn't drift at all across ten editions (2020–2026); DC's state-rule count never
  grows past A1–A9, the smallest of any jurisdiction. Useful as a contrast case against Florida/
  California's breadth when this project eventually explains *why* some states accumulate more
  exceptions than others.
- **Two more same-year-multiple-notice cases** (Colorado's two 2024 notices citing the identical
  circular; Delaware's two 2026 notices) — same open supersession-order question Arkansas raised in
  Entry 11, still unresolved, now affecting three states.
- **`cf-circular-expert/AGENT.md` updated in place** — corpus table now reflects 10 jurisdictions, 73
  state-level documents, and points at Florida specifically as the flagged L3 priority.

### ▶ Next session

Ledger's own updated order: rules 81/82/83 into `rule_index.json` (still not done — flagged twice
now); Florida to L3 ahead of California; resolve the filing-ref-prefix pattern and the multi-notice
supersession question generally; look for a second Florida edition, since one notice can't show drift
the way every other state's multi-edition history has. Otherwise unchanged from Entry 10/11: the
~146 not-yet-itemized coverage families, and Ordinance or Law / Business Income time-element as the
largest itemized undocumented clusters.

---

## Entry 13 — note: Idaho access still needs to be secured

- **Date:** 2026-08-19.
- **Directed:** "add note, we need to secure access for Idaho Commercial Lines Manual."
- **Built:** a "Pending acquisition" section at the top of `Circular_Review_Tracking.md` — Idaho
  listed as access-not-yet-secured, explicitly distinguished from "reviewed and found absent." No
  `CF-ID-*` PDFs exist under `Commercial Line Manuals\CF\` as of this entry. Once they land, the
  extraction script already sweeps new subfolders automatically (per Entry 11) — just re-run it and
  extend the ledger the same way CO/CT/DC/DE/FL were added.

---

## Entry 14 — note: Louisiana access also needs to be secured

- **Date:** 2026-08-19.
- **Directed:** "Louisiana needs access as well."
- **Built:** added Louisiana to the same "Pending acquisition" table in
  `Circular_Review_Tracking.md`, same status and next step as Idaho (Entry 13) — no `CF-LA-*` PDFs on
  disk yet.

---

## Entry 15 — nine more states ingested: the `CL-` filing prefix is a real pattern, not an anomaly

- **Date:** 2026-08-19.
- **Directed:** "new states added" — GA, IA, IL, IN, KS, KY, MA, MD, ME landed in
  `Commercial Line Manuals\CF\`.
- **Built:** re-ran `scripts/16_extract_cf_manuals.py` — 79 new documents extracted, bringing the
  corpus to 158 documents, 7,778 pages. Characterized all nine states and extended
  `Circular_Review_Tracking.md` with nine new per-state sections (third ingestion pass this session).
- **The `CL-`-prefixed filing reference, flagged as a possible anomaly in Entries 11–12, is now
  confirmed a real, systematic second filing family** — present in 10 of 19 jurisdictions (AR, CT, DC,
  DE, FL, GA×3, IN×3, KY×4, MA×2, ME), including the corpus's oldest filing-ref timestamp
  (`CL-2019-OMJRU`, Massachusetts) and two directly-sequential refs (`CL-2024-ORU1`/`ORU2`, Kentucky).
  Kentucky carries it most (4 of 10 notices). **Reclassified in the ledger from "anomaly to resolve"
  to "real pattern to explain."** DC's one-off `CA-2023-REQRU` remains the single genuinely odd entry.
- **A new manual rule number found**: Rule **8** ("Policywriting Minimum Premium," per the CW TOC),
  seen only in Maryland so far — every other jurisdiction's exception set starts at rule 2 or higher;
  Maryland is the only one reaching down to 8. Rules 81/82/83/8 are now all flagged for
  `rule_index.json` — three separate entries have now asked for this and it still isn't done.
- **Massachusetts and Florida are the only two jurisdictions with the full A1–A14 state-rule range**,
  and Massachusetts carries it from its very first notice rather than growing into it the way every
  other state does — worth remembering if this project ever tries to model "how state rules
  accumulate" as a general pattern; Massachusetts breaks it.
- **More multi-notice-per-year cases**: Illinois (two 2020 notices), and — the most extreme yet —
  Indiana and Kentucky each with **four notices in 2025 alone**. The supersession-order question first
  raised in Entry 11 (Arkansas) is now open across five states and still unresolved.
- **Kansas has the largest single-notice gap seen** — four years between its 2020 and 2024 notices,
  worth knowing if a future L3 pass wonders why Kansas's exception set changed so much between two
  consecutive documents.
- **`cf-circular-expert/AGENT.md` updated in place** — corpus table now reflects 19 jurisdictions, 152
  state-level documents, and the `CL-` finding's reclassification.

### ▶ Next session

Ledger's updated suggested order: `rule_index.json` gets rules 8/81/82/83 (now flagged three separate
times); Florida to L3, then California; work out what `CL-` actually denotes rather than continuing to
flag individual occurrences; resolve the growing pile of same-year supersession cases; and a small
cluster of unexplained page-count swings (Arizona, Delaware, now Massachusetts) worth a combined look.
Otherwise unchanged: Idaho and Louisiana access still pending (Entries 13–14), the ~146 not-yet-
itemized coverage families from Entry 10, and Ordinance or Law / Business Income time-element as the
largest itemized undocumented clusters.

---

## Entry 16 — note: Mississippi access also needs to be secured

- **Date:** 2026-08-19.
- **Directed:** "add Mississippi to states that need access."
- **Built:** added Mississippi to the "Pending acquisition" table in `Circular_Review_Tracking.md`,
  alongside Idaho (Entry 13) and Louisiana (Entry 14) — no `CF-MS-*` PDFs on disk yet.

---

## Entry 17 — note: Washington (state) access also needs to be secured

- **Date:** 2026-08-19.
- **Directed:** "add washington to need access."
- **Built:** added Washington to the "Pending acquisition" table in `Circular_Review_Tracking.md`,
  alongside Idaho/Louisiana/Mississippi (Entries 13/14/16) — no `CF-WA-*` PDFs on disk yet. Noted
  explicitly that this is Washington State, not the District of Columbia (`DC`), which is already
  ingested — worth being unambiguous given the two share a name.

---

## Entry 18 — the rest of the country: 27 states ingested in one batch; ledger format changed at scale

- **Date:** 2026-08-19.
- **Directed:** "Ok, all remaining available states are in the subfolder."
- **Found:** 27 new state folders (MI, MN, MO, MT, NC, ND, NE, NH, NJ, NM, NV, NY, OH, OK, OR, PA, RI,
  SC, SD, TN, TX, UT, VA, VT, WI, WV, WY) — combined with the 19 already ingested, this is every state
  + DC. Only Idaho, Louisiana, Mississippi, Washington remain pending (Entries 13/14/16/17).
- **Built:** re-ran `scripts/16_extract_cf_manuals.py` — 218 new documents, corpus now **376
  documents, 15,134 pages** across 47 jurisdictions (46 states + CW). All extracted successfully.
- **Ledger format changed, deliberately, and said so in the file.** One-row-per-document stopped
  being maintainable at 376 documents. From this batch forward, `Circular_Review_Tracking.md` tracks
  one row per state (notice count, page range, exception-rule range, state-rule range, notable
  findings) — a real tradeoff, named as such in the ledger itself, not silently applied. Per-document
  detail for the first 19 states is preserved; the underlying `.txt` files and `notices.json` still
  hold per-document data for the rest if it's ever needed.
- **L3 priority list changed**: Texas and Virginia now rival Florida for broadest exception-rule set
  (25–26 countrywide rules vs. Florida's 23) — priority is now "Florida, Texas, and Virginia, roughly
  tied," not "Florida then California." **Virginia's Rule 1 exception is the single most curious
  individual finding in the whole corpus** — Rule 1 is the division's scope/application rule per the
  CW TOC, not the kind of thing a state normally files an exception against. Flagged as the first
  thing to actually read at text level, ahead of everything else.
- **Two real data-hygiene issues found, not fixed** (source-file changes weren't requested): New
  Jersey and New Mexico each have duplicate PDFs on disk (`(1)`/`(2)` suffixes, likely double
  downloads) — 8 NJ files represent 7 distinct notices, 12 NM files represent 10. New Mexico also has
  the corpus's only `-R`-suffixed filename (`CF-NM-2027-RU-001-R.pdf`, vs. every other document's
  `-C`) and its smallest single document (6 pages) — both unexplained, flagged for a direct look.
- **A few new manual rule numbers surfaced**: 1 (Virginia only — see above), 12 (South Dakota only),
  15/20/34/35 (Texas only), 41 (Michigan). `rule_index.json` is now overdue for a real update — this
  is the fourth entry to flag rules needing to be added and none have been added yet.
- **`cf-circular-expert/AGENT.md` updated in place** — corpus table now reflects 370 state-level
  documents across 46 states + DC, the revised L3 priority, and the pending-acquisition summary.

### ▶ Next session

Read Virginia's Rule 1 exception text directly — highest-curiosity item in the ledger. Then Florida
and Texas to L3. Resolve the `CL-` filing-family question (now spanning most of the corpus). Confirm
and clean up the NJ/NM duplicate files and the NM `-R` filename. Populate `rule_index.json` — four
entries running, still not done. Otherwise unchanged: Idaho/Louisiana/Mississippi/Washington access
still pending, the ~146 not-yet-itemized coverage families from Entry 10, and Ordinance or Law /
Business Income time-element as the largest itemized undocumented clusters.

---

## NEXT SESSION STARTS HERE
