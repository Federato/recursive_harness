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

> **Correction note, 2026-10-06** (`cf-bgi-chains.html`, `cf-bgii-chains.html` reviews). Still true of the
> CW file, but not a gap in practice: header-only CW with state rows is the normal pattern. OK files 1,368
> Group I rows; ME files Group II and Lowest rows; both price (OK $720 building, ME $48 Group II). A key a
> state does not file is now refused by the engine (C28-05). See `BasicGroupI_ERC_Tables.md`.

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

> **Correction note, 2026-10-06** (`cf-bgi-chains.html` BI review #41; `cf-bgii-chains.html` BI review #43).
> All three tables are state-filed (adjustment factor: Group I IN 0.85; Group II UT 0.7, IN 0.75); Business Income Group I
> and II price normally in IN and UT. Also from those reviews: the "blanket/max-period" branch is the
> operational-unit test, not blanket, and BI Group I prices coinsurance inside the type-of-risk factor and
> has no deductible.

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
  `BasicGroupIRate`/`EQRate` directly, adding at most one trivial multiplier on top.
  *(Correction note, 2026-10-06, `cf-bgi-chains.html` SCBI review #44; probes BI-7 to BI-9: for Basic
  Group I the copied value is the item's base x LCM, its third step, not its final rate — 0.07 against
  0.066 in the golden case. The child then adds its own vandalism factor and a BI `Factor`. Earthquake
  not re-checked.)* *(Correction note, 2026-10-06, `cf-earthquake-chains.html` SCBI #13: Earthquake likewise copies the item's
  base x LCM (0.5 against a finished 0.352, probe E-2), then multiplies the BI `Factor`.)*
  Broad and Special
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
  that's structurally all those two chains do. *(Correction note, 2026-10-06: for Basic Group I the
  borrowed value is the item's base x LCM, not its finished rate; `cf-bgi-chains.html` now draws the
  corrected chain, and the old sheets in `cf-rating-chains.html` were replaced.)* Didn't force extra nodes in to make them look more
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

## Entry 19 — checkpoint: plain-English log caught up, full sync verified

- **Date:** 2026-08-19.
- **Directed:** "save here, update all logs where appropriate."
- **Found:** `BUILD-LOG-PLAIN-ENGLISH.md` had fallen behind — its last entry matched technical
  Entry 7; Entries 8 through 18 (SCBI diagrams, the coverage inventory and its earthquake/flood
  correction, all four circular-ingestion batches covering every state but four, and the four
  pending-access notes) had no plain-English counterpart.
- **Built:** one consolidated plain-English catch-up entry covering Entries 8–18, rather than eleven
  separate small entries — matches how the work actually happened (several fast-moving small asks in
  a row) better than artificially splitting it back apart.
- **Verified:** every file in `Spreadsheet_Rater\CF\` diffed byte-for-byte against its mirror in
  `Recursive_Harness_2.0\CF_Algorithm\`. All in sync after this entry, with one deliberate exception:
  `CF_ERC_Latest_Version_Summary.xlsx` is pre-existing ISO source material, not a project deliverable,
  and was never mirrored — correctly so, it isn't ours to mirror.

### State of the project as of this checkpoint

- **Five coverages fully documented** (algorithm doc + tables doc + diagrams): Building, Personal
  Property, Special Class, Business Income, Special Class Business Income.
- **~146 of ~243 coverage/endorsement families identified but not yet documented** (Entry 10's
  corrected count) — Ordinance or Law and the Business Income time-element cluster are the largest
  itemized groups still open.
- **Two specialist agents defined**, one substantially built out: `cf-erc-expert` (role defined,
  no retrieval tooling yet) and `cf-circular-expert` (376 documents extracted and characterized at
  L2 across 46 states + DC + countrywide; no document has reached L3 yet).
- **Four states still pending acquisition**: Idaho, Louisiana, Mississippi, Washington.
- **Highest-priority open items**, in order per the circular ledger and this log: read Virginia's
  Rule 1 exception directly; take Florida and/or Texas to L3; resolve the `CL-` filing-family
  question; populate `rule_index.json` with rules 1/8/12/15/20/34/35/41/81/82/83 (flagged repeatedly,
  never yet done); clean up the NJ/NM duplicate files and the NM `-R` filename anomaly.

---

## Entry 20 — dropdown-table CSVs built for the BGI rating engine; California's two-district split found

- **Date:** 2026-09-03.
- **Directed:** build Excel dropdown source data for a Basic Group I (BGI) building rating algorithm —
  Building Class Code + Description, Construction Code + Description, a derived Class-Code Rating Type
  (Class vs. Specific), and a countrywide Basic Group I Building base-rate table — saved as CSVs in a
  new `dropdown tables\` subfolder, each with a citing README.
- **Built:**
  - `BuildingClassCode_Description.csv` — 882 rows / 154 unique Class Codes, from
    `DomainClassDesc.DomainTable.csv` (`CFCW20260601V01`). Found Description is many-to-one with
    ClassCode (most codes cover several distinct occupancies rated identically — e.g. code `0570`
    alone covers 33), while every Description maps to exactly one ClassCode.
  - `ClassCode_RatingType.csv` + the `RatingType` column above — per code, `Class` if Class rating is
    available for it at all (**directed rule, reversed once mid-build**: an initial pass defaulted to
    `Specific` whenever Specific/Tentative was available, then was corrected to default to `Class`
    whenever the code is Class-eligible). Final: 104 codes `Class`, 50 `Specific`.
  - `ConstructionCode_Description.csv` — the 6 standard construction types (`ConstructionCode.RateTable.csv`,
    Bureau Rule 15B), a clean 1:1 map both directions.
  - `BGI_BuildingRates.csv` — 24,246 rows, `StateCode/ClassCode/ConstructionCode/Rate`, pulled from
    each state's own `BasicGroupIRate.RateTable.csv` (CW's copy is the confirmed-empty one from Entry 3),
    filtered to `CovType = "Building"`, one edition per state selected as whichever is in force as of
    today. 39 states included.
- **Found — California watch-item.** CA has no `BasicGroupIRate.RateTable.csv` at all. It splits Basic
  Group I building rating into two parallel tables, `BasicGroupIDistrictIRate` and
  `BasicGroupIDistrictIIRate`, selected by a CA-only, user-picked Location field `District`
  (`DomainDistrict`: "District I"/"District II", not derived from county/territory).
  `CommercialPropertyStructureRules.Rule.xml` (~line 1216) branches the class-rate lookup on it.
  Documented in `BasicGroupI_ERC_Tables.md` (new watch-item note) and `cf-rating-chains.html` (new
  delta note on the Building·BGI chain view) as a standing thing to check for when building the rating
  engine: **CA needs an extra `District` input field and a two-table lookup**, and any future
  per-state table pull should not assume every state has the single-table shape AL/AR/AZ/etc. use.
  Also excluded from `BGI_BuildingRates.csv` for the same reason. AK and PR were also excluded (no
  `BasicGroupIRate` file found for either) but not investigated further — open question, not
  confirmed to be the same District-style split or something else entirely.
- **Not yet done:** an equivalent Basic Group II class/symbol dropdown pull, and checking whether any
  state besides CA/AK carries a similar per-location rating-district split.

**Follow-up, same date: Alaska confirmed to have the identical two-district split.** Directed to
check after CA was flagged. AK also has no plain `BasicGroupIRate.RateTable.csv` — it carries
`BasicGroupIDistrictIRate`/`BasicGroupIDistrictIIRate` (1,369 lines each, same key shape as CA's
pair), branched on in `CommercialPropertyStructureRules.Rule.xml` the same way CA's is. The
*mechanism* differs, though: CA has the agent pick `District` directly (a Location-level dropdown);
AK derives its equivalent field, `BasicGroupIDistrictTerritory`, from City
(`DomainDistrictAlaska.DomainTable.csv`), with a further Yes/No wrinkle for City = "Remainder of
State" keyed off `BasicGroupIRatingTerr`/`CountyAK` (not fully traced). Updated all three places the
CA finding had already been written down — `BasicGroupI_ERC_Tables.md`, `cf-rating-chains.html`, and
`dropdown tables/README_BGI_BuildingRates.md` — rather than leaving CA looking like the only state
with this issue. Puerto Rico (the third state missing `BasicGroupIRate`) is still unchecked — not
assumed to match.

---

## Entry 21 — edition cutoff formalized at 9/1/2026; State/ERC/CW edition ledger built

- **Date:** 2026-09-03.
- **Directed:** re-derive "current edition" per state using an explicit cutoff — "latest effective
  date that isn't past 9/1/2026" — rather than "today," and build a `State, ERC Edition, CW Edition`
  ledger CSV. The initial phrasing of this request pointed at
  `C:\Projects\ISO_ERC_Files\General_Liability\countrywide` (a different product line, no Basic Group
  I Building rating at all); confirmed via `AskUserQuestion` that this was a typo for the CF directory
  before doing anything with it.
- **Found:** re-running the edition-selection logic against the 9/1/2026 cutoff (vs. the 9/3/2026
  "today" used in Entry 20) picked the **identical edition for every state** — no filing in this
  snapshot is effective in that 2-day window. `BGI_BuildingRates.csv` needed no data changes; only the
  cutoff-date language in `README_BGI_BuildingRates.md` and `State_EffectiveDates.csv`'s
  `InForceAsOf_*` column header were updated to name the directed cutoff explicitly instead of the
  incidental run date.
- **Built:** `State_ERC_CW_Editions.csv` — `State, ERC Edition, CW Edition`, 42 rows. CW Edition is
  `CFCW20260601V01` for every row — the only Commercial Property Countrywide edition present in the
  `20260601` snapshot directory, so there was nothing to select there.
- **Saved to memory:** which ERC edition (per state) and CW edition (`CFCW20260601V01`) this project's
  dropdown tables are built from, and the 9/1/2026 cutoff rule, so a future session doesn't have to
  re-derive it from the CSV/READMEs.

---

## Entry 22 — correction: the edition search only covered one filing batch; rescanned all eight, gained 46 of 51 jurisdictions

- **Date:** 2026-09-03.
- **Directed:** "shouldn't we be able to have all 51 jurisdictions (disregard PR for now)" — prompted
  by only having 39–44 states in `BGI_BuildingRates.csv`/`State_EffectiveDates.csv` so far.
- **Found — the root cause was a scope bug, not missing data.** Every prior pass in Entries 20–21 only
  searched `C:\Projects\ISO_ERC_Files\CF\20260601\`. That directory is **one filing batch**, not a
  complete snapshot of every state — `CF\` has seven other batches
  (`20191201`, `20201201`, `20221001`, `20230801v1`–`v4`), and each state's edition history
  accumulates across batches independently, not by a shared vintage date. Rescanning all eight batches
  for every state:
  - **Corrected four states wrongly believed to have no in-force edition**: CA (`CF CA 20251201 V01`,
    batch `20230801v3`), MA (`CF MA 20260301 V02`, batch `20230801v4`), MO (`CF MO 20251101 V01`,
    batch `20230801v2`), NC (`CF NC 20251101 V01`, batch `20230801v3`) all turned out to have a real
    in-force edition, just not in the `20260601` batch. CA's district-split finding (Entry 20/21) still
    holds — verified directly against this newly-found in-force edition, not just CA's future filings.
  - **Found five states with zero presence in `20260601` at all**, but a real filing elsewhere: FL
    (`20230801v1`), IL, NJ, RI, VT (all `20230801v4`).
  - **Confirmed five states have no CF filing anywhere in this corpus, checked across all eight
    batches**: HI, ID, LA, MS, WA. Four of five (ID/LA/MS/WA) match already-known "pending access"
    states from the circulars-tracking work (Entries 13/14/16/17); HI is a new gap.
- **Rebuilt:** `BGI_BuildingRates.csv` (now 27,336 rows / 44 states, up from 24,246 / 39), and
  `State_EffectiveDates.csv` (now 430 rows / 47 states across all eight batches, with new
  `SnapshotBatch`, `IsCurrentEdition` columns) and `State_ERC_CW_Editions.csv` (47 rows, `SnapshotBatch`
  column added).
- **Net result:** 46 of the 51 U.S. state+DC jurisdictions now have at least one CF edition in this
  corpus (disregarding PR, per direction); 44 of those have a usable single-table `BasicGroupIRate`
  (everything but the CA/AK District pair).
- **Updated:** `BasicGroupI_ERC_Tables.md`'s CA/AK watch-item note, `README_BGI_BuildingRates.md`,
  `README_State_EffectiveDates.md`, `README_State_ERC_CW_Editions.md`, and the two memory files
  (`project_erc_editions_in_use`, `project_cf_bgi_district_states`) to carry the corrected batch/edition
  data forward.
- **Open:** HI, ID, LA, MS, WA still need to be acquired before "all 51" is actually achievable; PR
  intentionally deferred per direction.

---

## Entry 23 — SubStdConditionRate traced and pulled into a dropdown table; Rule 85 citation found to be unverifiable

- **Date:** 2026-09-03.
- **Directed:** investigate `SubStdConditionRate`, then build a spreadsheet-ready lookup from the
  finding (parallel session in `ISO_ERC_Files\CF`, then mirrored into the rater project).
- **Found — the bureau-rule citation could not be confirmed.** Metadata ties this field to
  `BureauRuleNumberLCRule85SubStandardConditionCharges`, but the one CF multistate loss-cost manual on
  hand (`CF-MU-2022-LC-001-C.pdf`) has no "sub-standard"/"substandard" text anywhere in its extracted
  content, and its own Rule 85 is "BASIC GROUP I CLASS RATES" — an unrelated topic. Treated as
  unverified provenance going forward, not a citation to hand to anyone else without caveat.
- **Found — the CW table is a stale-value trap.** `SubStdConditionRate.RateTable.csv` at the CW level
  has shown the identical rate (0.321/0.16/0.076/0.04 by construction tier) in every CW edition on file
  since `CF CW 20191201 V01`. Individual states began filing their own, lower override
  (0.313/0.156/0.074/0.039) starting with CW base cycle `20230801v2` — every state that has data now
  uses the newer rate, none fall back to CW. Reading the CW copy directly would silently return a
  wrong, years-out-of-date number.
- **Found — three coverage buckets, using the canonical per-state edition ledger from Entry 22** (not
  a fresh single-batch scan): no-file states that never adopted the charge (CA, FL, UT — CA's absence
  may be another instance of the District-split pattern from Entry 20, not yet checked), states with
  an empty table (deliberate exclusion, not "fall back to CW"): DC, IL, KY, NJ, NY, and everything else
  (38 states) with real state-keyed data, all sharing one identical rate schedule.
- **Built:** `dropdown tables/SubStdConditionRate.csv` (1,140 rows, 38 states × 5 conditions × 6
  construction codes) + `README_SubStdConditionRate.md`.

---

## Entry 24 — the SubStdCondition A–E labels resolved from a form-field table, not metadata; label→code dropdown built

- **Date:** 2026-09-03.
- **Directed:** "Is there a lookup to reference which substandard condition exists to the substandard
  code?" then "add a table that will enable a use[r] to select a label, and map that to a code."
- **Found.** Neither the DataDef XSD nor `Metadata\RateTables.Metadata.xml` describes what conditions
  A–E mean — `SubStdConditionA`…`E` are plain 3-character Yes/No flags with no description anywhere in
  those two places, which is why Entry 23 originally logged this as unresolved. The actual labels live
  in `Form Fields\Fields.FormField.csv` (a UI form-field table, easy to miss since it isn't a rate
  table or metadata entry): **A** = Heating and Cooking, **B** = Wiring, **C** = Conversion, **D** =
  Physical Condition and Housekeeping, **E** = Exposure — each with a full description. This also
  explains Entry 23's two-tier rate split: A/C/D share one tier, B/E share the other, and the grouping
  reads as legible (structural/occupancy conditions vs. wiring/exposure conditions) now that the
  labels are known.
- **Built:** `dropdown tables/SubStdConditionCode_Label.csv` (5 rows, `SubStandardCondition, Label,
  Description`) + `README_SubStdConditionCode_Dropdown.md`. Genuine 1:1 lookup both directions.
- **Corrected:** `README_SubStdConditionRate.md`'s "what do A–E mean" open question, closed out rather
  than left stale once the answer was found.

---

## Entry 25 — VacantBuildingRate traced: a product, not a sum, with universal state coverage

- **Date:** 2026-09-03.
- **Directed:** "using the same logic we did for this, look into VacantBuildingRate" (same
  investigate-then-build pattern as Entries 23–24).
- **Found — structurally different from SubStdConditionRate.** `VacantBuildingRate` is a PRODUCT, not
  a sum: `VacantBldgPreviousOrIntendedOccup(StateCode, ClassCode) × LossCostMultiplier`
  (`CommercialPropertyStructureRules.Rule.xml`, rule `SetVacantBuildingRate`). The lookup key is
  `ClassCodeToUse` — the vacant building's *previous or intended* occupancy class, not its nominal
  occupancy — and only runs when `VacantBuilding = "Yes"` and that field is populated; otherwise the
  rate is forced to `0.0`. Flagged as needing its own input, distinct from whatever selects the
  building's normal `ClassCode`, before this can be wired into a working dropdown.
- **Found — no exclusion buckets, unlike SubStdConditionRate.** Every state in the ledger has real
  data; the CW table has always been empty (0 rows in every edition since 2019 — "no CW source ever
  existed," not a stale-value trap like Entry 23's). Only two rate values appear across the included
  states: `0.015` (flat, everywhere) and `0` (a genuine per-class-code exclusion, same zero-set across
  41 of the states with data, differing only in FL/GA/KS/NY because they file fewer class codes total —
  the identical footprint already known from `BasicGroupIRate`, Entry 20).
- **Found — a ClassCode not in the existing dropdown.** Alabama's table includes class code `1180`,
  absent from `BuildingClassCode_Description.csv` (Entry 20) entirely. Flagged as an open question,
  not guessed at.
- **Found — the bureau-rule citation is plausible but still unverified**, same caveat pattern as
  Entry 23: `BureauRuleNumber85G5` could be an unreprinted subsection of the manual's real Rule 85
  ("Basic Group I Class Rates"), but there's no "vacant" text anywhere in the one manual on hand to
  confirm it.
- **Built:** `dropdown tables/VacantBldgPreviousOrIntendedOccup.csv` (4,849 rows, 45 states + DC) +
  `README_VacantBldgPreviousOrIntendedOccup.md`. No new label table needed — reuses
  `BuildingClassCode_Description.csv`.

---

## Entry 26 — Puerto Rico exclusion corrected from "defer" to "never include"; both new dropdown tables cleaned

- **Date:** 2026-09-03.
- **Directed:** "stop looking into PR, we've spoken about this" — a second, firmer correction after PR
  had already been told once (during Entry 22, "disregard PR for now") to be out of scope, and still
  reappeared in Entries 23 and 25's output CSVs and README commentary ("PR is the outlier," etc.).
- **Found — the first memory write was too soft.** The initial `project_pr_out_of_scope` memory
  permitted including PR rows "for completeness" even while treating it as not a build target, which
  is exactly the gap that let PR data back into `SubStdConditionRate.csv` and
  `VacantBldgPreviousOrIntendedOccup.csv`. Corrected to a hard rule: PR is excluded from every output
  the same way a state with zero CF filings would be — no rows in CSVs, no "PR differs" commentary in
  READMEs, dropped silently if it surfaces while sweeping all states.
- **Fixed:** stripped PR's 30 rows from `SubStdConditionRate.csv` (1,170 → 1,140) and 85 rows from
  `VacantBldgPreviousOrIntendedOccup.csv` (4,934 → 4,849) in both `Spreadsheet_Rater\CF\dropdown
  tables\` and this mirror; rewrote both READMEs' PR-outlier sections to note the exclusion instead of
  documenting PR's (real, usable, but out-of-scope) rate schedule.
- **Known gap at time of this entry:** `Spreadsheet_Rater\CF\dropdown tables\SubStdConditionRate.csv`
  was locked (likely open in Excel) at correction time and could not be rewritten in place — the harness
  mirror here **is already correct**, but the working-directory original may still carry PR rows until
  that file is closed and re-saved. Check this on next touch of that file.
- **Updated memory:** `project_pr_out_of_scope` reclassified from a `project`-type memory to a
  `feedback`-type memory, recording that this was a repeated correction, not a one-time preference.

---

## Checkpoint — sync status as of Entry 26 (2026-09-03)

`Recursive_Harness_2.0\CF_Algorithm\` now mirrors `Spreadsheet_Rater\CF\` through Entry 26, including
the new `dropdown tables\` folder (BGI + SubStdConditionRate + SubStdConditionCode_Label +
VacantBldgPreviousOrIntendedOccup, all PR-free here) and the CA/AK district-split notes in
`BasicGroupI_ERC_Tables.md` / `cf-rating-chains.html`, carried forward from the last verified sync at
Entry 19. **One known asymmetry**: the new SubStdConditionRate/VacantBuildingRate delta note added to
this copy of `cf-rating-chains.html` (documenting Entries 23–25) was not pushed back to the
`Spreadsheet_Rater\CF\` original, since this session's direction was to update the harness copy only —
worth reconciling next time both are touched. Deliberate non-mirrors unchanged from Entry 19:
`CF_ERC_Latest_Version_Summary.xlsx` and `CFRater1.01.xlsb` (pre-existing/working ISO source material
and the live Excel rater workbook, not project deliverables).

---

## Entry 27 — Territory through Deductible Factor: seven BGI Building rating factors turned into standalone Excel reference workbooks

- **Date:** 2026-09-04.
- **Directed:** a long session working through the BGI Building rate build-up factor by factor, each
  time: pull the ERC mechanism and tables, cross-verify against the CW manual where precision
  mattered, and — for most factors — build a standalone Excel workbook in
  `Spreadsheet_Rater\CF\Supporting Tables\` that could later be wired into `CFRater1.01.xlsb`. No
  building into the actual rater itself was authorized except one narrow, explicit exception (below).
  Standing rule honored throughout: any simplification/constructed data gets logged as a known gap,
  never presented as production-ready (`feedback_surface-level-simplifications-not-production`
  memory).
- **Built, in order worked:**
  - **Territory Factor** — `BGI_Territory_Lookups.xlsx`. Redesigned mid-build: first attempt derived
    dropdowns from City/County, then explicitly redirected ("the dropdowns should be based on the BGI
    Territory Factor") to source directly off the filed factor list per state. Covers all 47 states.
  - **AK/CA/NY Base Rate Table split** — `BGI_LossCost_Tables_AK_CA_NY.xlsx` (Building-only loss costs,
    `StateCode/ClassCode/ConstructionCode/District/Rate`) plus `AK_District_ZIP_Mapping.xlsx`, a
    **constructed, non-ISO-filed** 273-ZIP-to-District mapping built from Alaska Rule 70's actual
    legal definition (District I = First Judicial District, east of the 141st Meridian) since no
    ISO-filed ZIP-level mapping exists for AK beyond an 11-row City→District table.
  - **Protection Class** — `BGI_ProtectionClass_Tables.xlsx`. CW (28 codes) plus North Carolina's
    genuinely different 12-code scale, found only after being asked "are these factors consistent
    across all states?" — the workbook was rebuilt once NC's divergence surfaced.
  - **Roof Surfacing ACV Factor** — reviewed in depth (Rule 74.A.3.b/c), corrected an earlier
    "unreachable filed row" claim after the user supplied the actual manual text; planning-only, no
    workbook built.
  - **Sprinkler Leakage Exclusion** — `BGI_SprinklerLeakageExclSprinkleredFactor.xlsx`. A real
    self-correction cycle: user pushback ("that really feels wrong to me, the LCM applying there")
    led to finding the sprinkler credit sits structurally after Territory/Protection/Roof multiply in
    (unlike `VacantBuildingRate`, baked in earlier), confirmed against Rule 74.A.3.c. Also confirmed
    the sprinklered and non-sprinklered terms are mutually exclusive, gated on opposite
    `SprinklerSystem` selections, not both potentially charged.
  - **Coinsurance Factor** — `BGI_CoinsuranceFactor.xlsx`. Four-branch mechanism (Builders
    Risk/Functional-Valuation bypass; standard 80/90/100%; the same table reused for blanket
    coinsurance; a flat 1.5 sub-80% surcharge). Found FL files a real, unreachable 70% row — same
    "filed but dead" pattern as the earlier roof-surfacing CT/MA/NH quirk.
  - **LOI Factor** — `BGI_LOIFactor_Building.xlsx`. The session's most consequential correction: first
    concluded from the rule logic alone that the ERC engine does *not* interpolate and Rule 70.F.3's
    interpolation procedure was manual-only — wrong. Re-inspecting the rate table's CSV shape and its
    `RateTableDef.xml` showed `InterpolateMode="Linear"` declared on the table definition itself; the
    engine interpolates natively, not via rule logic. Corrected before proceeding. PR carries a fully
    distinct 342-row table, not a dead artifact like most PR overrides seen in this project.
  - **Deductible By Location Factor** — reviewed via Rule 33.D / CP 03 29: flat 0.995, per-building,
    stacks multiplicatively on top of the separate amount-based Deductible Factor. No workbook (simple
    enough to not need one).
  - **Deductible Factor** — `BGI_DeductibleFactor.xlsx`. Both the dropdown *and* the factor table
    genuinely vary by state (7 distinct shapes across 47 states) — the first factor reviewed this
    session where state variation runs that deep. A real mid-build correction: an early CA pull used
    a future, not-yet-in-force edition and wrongly showed CA offering 14 deductibles to $1,000,000;
    redone against `State_ERC_CW_Editions.csv`'s authoritative in-force edition, CA has no override at
    all — the same CA-edition trap flagged once before in this doc. Rebuilt once more at the user's
    request from 7 separate variant sheets into one flat 6,702-row table (`State` as a column) once it
    became clear that was simpler than the sheet-per-state design.
- **One change made to the actual production rater, by explicit, narrow request only:** a
  `BGI Territory Factor` tab was added directly to `CFRater1.01.xlsb` via PowerShell/COM (openpyxl
  cannot write `.xlsb`), containing only the named cells requested, no formulas or other
  functionality. A backup (`Backups\CFRater1.01_backup_pre-BGITerritoryFactor.xlsb`) was taken first.
  Every other deliverable this session lives in the standalone Supporting Tables workbooks, not the
  rater itself — consistent with the project's standing "no building without an explicit go" rule.
- **Checked against:** the same discipline as every prior entry — all 47 states swept per factor
  (never sampled), CW manual text pulled directly for Roof Surfacing/Sprinkler/Deductible-By-Location/
  LOI-interpolation/AK-District where precision mattered, every Excel formula chain
  (`SUMPRODUCT`/`INDEX` band-matching, `INDIRECT`+named-range dynamic dropdowns) independently
  re-verified in Python against the real underlying data since openpyxl can't execute formulas itself.
- **Docs updated to reflect this session's findings**: `BasicGroupI_ERC_Tables.md` — pointer
  annotations added to the `ProtectionClassFactor`/`VandalismExclFactor`/`StdPropPolGroupIFactor`/
  `CoinsuranceFactor`/`BasicGroupILOIFactorBldg`/`DeductibleByLocationFactor`/`DeductibleFactor` table
  rows, plus a consolidated "Session findings, 2026-09-04" block at the end of the file covering all
  seven in the same detail level as this entry.
- **Known gaps, flagged as things to watch, not defects to silently fix:** `AK_District_ZIP_Mapping.xlsx`
  is constructed/best-effort, not ISO-filed — do not treat it as authoritative if AK BGI rating is ever
  wired into the live rater. The Deductible Factor workbook's NV/PA/TX/UT variants file coarser-grained
  bands than the 39-state Common table (same limit coverage, fewer breakpoints) — resolved as
  intentional filing granularity, not missing data, but worth re-confirming if band counts ever look
  short again for those four states.

## Entry 28 — Business Income traced end-to-end (all five forms + shared Factor); live-rater audit found and fixed a real Cyber Incident Exclusion premium bug; ~40 untraced endorsement paths surfaced

- **Date:** 2026-09-11.
- **Directed:** pick up Business Income (separate coverage line from Building/Contents, same
  `CommercialPropertyBusinessIncome` datadef group nested inside Structure) and trace every form the way
  BGI Building was traced in Entry 27 — algorithm, required tables, per-state filing status — then, once
  the shared mechanisms were understood, audit the live implementation in `CFRater1.01.xlsb` itself for
  correctness. This was the first session this project explicitly opened `CFRater1.01.xlsb` — previously
  standing off-limits (`feedback_do-not-touch-live-rater` memory) — done strictly read-only via
  win32com, confirmed closed before and after each open, never saved.
- **Built, in order worked:**
  - **Basic Group I** (`Excel_Rater_BusinessIncome_BasicGroupI_AlgorithmGrid.html`, plus corrections to
    the existing `.md`) — confirmed it borrows Building's already-computed `BaseRate` as a value, not a
    re-derived lookup; traced `BuildersRiskFactor` and confirmed it's computed **once**, shared by both
    BGI and BGII (not per-form).
  - **Basic Group II** (`Excel_Rater_BusinessIncome_BasicGroupII.html`) — four of the five inputs feeding
    `Rate` turned out to be literal `Copy` rules from Building (`BasicGroupIISymbolToUse`,
    `BasicGroupIIRatingTerr`, `BasicGroupIINumericValue`, `BCEGFactor`) — the last two weren't caught
    until a direct request to "include the full rating algorithm" prompted re-tracing every field instead
    of trusting the first pass's summary.
  - **Broad** (`Excel_Rater_BusinessIncome_Broad.html`) — the shortest of the five forms, confirmed no
    COLAdj stage and no `Factor` read at all; confirmed its base rate is genuinely its own (shares the
    table with Building, not the value).
  - **Special** (`Excel_Rater_BusinessIncome_Special.html`,
    `Excel_Rater_BusinessIncome_Special_AlgorithmGrid.html`) — the one form with almost nothing shared
    with Building at all: Building's own Special base rate and theft-exclusion factor are flat statewide
    constants with no construction/occupancy key, while Business Income's version is the richest-keyed
    lookup in the whole coverage (construction type × coverage type × apartment/condo classification).
    Closed two gaps the source `.md` had explicitly flagged as inferred-not-confirmed.
  - **The shared `Factor` step** (`Excel_Rater_BusinessIncome_FactorDecisionTree.html`) — expanded from
    the originally-documented 4 branches to the actual 6: tracing `SetTypeOfRiskFactor` directly surfaced
    a Combined-Type-of-Risk blended-lookup branch and a plain-"Educational Institutions" branch that
    bypasses the main `BusnIncomeFactor` table entirely (uses `TuitionAndFeesFactor ×
    ...ExtensionOfRecoveryFactor` instead) — both previously logged as "unsupported," both confirmed
    filed and traced. Confirmed `Factor` is computed exactly once per building and shared identically by
    BGI and BGII (call-order proof: `SetFactor` runs after both forms' own chains finish).
  - **All-forms comparison grid** (`Excel_Rater_BusinessIncome_AlgorithmGrid_AllForms.html`) —
    consolidates all five forms stage-by-stage, same visual pattern as the Contents grid.
  - **Nine Supporting Tables workbooks**, each checked across all 47 states **and all 8 ERC snapshot
    batches** (not just the current `20260601` batch — see methodology correction below):
    `BGIBaseRateAdjustmentFactor_Tables.xlsx`, `BusinessIncome_CoverageTypes_Tables.xlsx`,
    `BusinessIncome_FactorAndEnums_Tables.xlsx` (5 rate tables + 6 enums, later folded
    `TuitionAndFeesFactor` in as a 6th sheet), `BasicGroupII_WindstormOrHailExclFactor_Tables.xlsx`,
    `BasicGroupII_LowestBaseRate_Tables.xlsx`, `BusinessIncome_Broad_BaseRate_Tables.xlsx`,
    `BusinessIncome_Special_Tables.xlsx`, `ApartmentCondoIndicator_Crosswalk.xlsx`,
    `CyberIncidentExclusionFactors_Tables.xlsx`. All copied into
    `Spreadsheet_Rater\CF\Supporting Tables\`.
- **Methodology correction, project-wide implication:** the first per-state sweep of
  `BaseRateAdjustmentFactor` found only 41 of 47 states filed, scanning just the `CFCW20260601V01` /
  `20260601` batch folder. A direct challenge ("I think Florida may have different tables") revealed CF
  ERC packages span **8 separate snapshot batches** (`20191201` through `20260601`), and a state's
  current-in-force edition is not guaranteed to sit in the newest batch folder — 5 states (FL, IL, NJ,
  RI, VT) had their live edition sitting in an older batch untouched by the `20260601` refresh. Re-scanned
  every table built this session across all 8 batches from that point forward; corrected count went to
  46/47 states filed (PR is the one genuine non-filing). This changes the standing per-state-check
  procedure for the rest of the project, not just this session.
- **Live-rater audit findings, `CFRater1.01.xlsb`, `BI Rating Worksheet`/`Bldg Rating Worksheet`/`Contents
  Rating Worksheet`:**
  - Initial read found BGII's windstorm/hail-exclusion COLAdj branch unwired in both Building and
    Contents — `LowestBaseRate` correctly computed but never consumed, `CAUSE OF LOSS ADJUSTMENT` an
    unconditional product with no branch. Flagged with a full formula spec (what the `IF` branch and the
    new `WindstormOrHailExclFactor` lookup should look like). **User fixed this independently mid-session**
    (file's modified timestamp moved during the conversation); a later re-check confirmed both Building's
    and Contents' BGII COLAdj now correctly branch on the exclusion-record flag and multiply in a real
    `VLOOKUP`-based factor.
  - Separately, a real, still-open-until-fixed bug: **all four Business Income premium formulas
    (BGI/BGII/Broad/Special) were chain-copying BGI's two Cyber Incident Exclusion factor cells** instead
    of each computing its own. Confirmed via the ISO rule XML that each form has its own distinct field
    (`CyberIncidentExclusionFactorBGI/BGII/Broad/Special`,
    `CyberIncidentExclusionCOLExcptnsFactorBusnIncomeBGI/BGII/Broad/SpecialToUse`), and confirmed against
    the actual filed `CyberIncidentExclusionWithEnsuingCauseOfLossExceptionsFactors` table that this
    wasn't a hypothetical future risk — **Special's second factor already differs from BGI/BGII/Broad's
    in every scenario** (0.996 vs. 0.997/0.998/1.000), so Special's premium was already being computed
    with the wrong number, not just exposed to one. Reviewed the user's proposed replacement formula,
    found the branch logic inverted relative to the filed table (treated `Sublimit` as the default
    branch instead of `Full Limit`), supplied a corrected version. **User applied the fix and confirmed.**
- **Newly surfaced, entirely untraced scope for Business Income** (confirmed to exist, not opened this
  session): **Earthquake** — a real 8-step 6th rate chain that runs unconditionally, but has no
  standalone premium file outside the Agreed Value variant (a non-Agreed-Value EQ election has no
  scheduled premium path, only blanket-average exposure — flagged as a genuine open question for anyone
  who builds this); **Agreed Value** and **Extended Period of Indemnity** — both use a `(Factor - 1) ×
  Rate` incremental-surcharge premium shape found nowhere in Building/Contents; **Special Class Business
  Income** — a complete second, parallel datadef group mirroring every plain Business Income form
  one-for-one, confirmed by directory listing only; **Mining Properties Business Income** — a parallel
  rule-file pair not even mentioned in the source `.md`; and **34 separate filed optional endorsements**
  (`Business Income Detail, Optional` in Form Pages) spanning Dependent Properties (5 files), Civil
  Authority, Utility Services – Time Element, Ordinance or Law – Increased Period of Restoration,
  Discharge From Sewer/Drain/Sump, several exclusion toggles, and several premium-adjustment options —
  none traced.
- **Checked against:** same all-47-state, no-sampling discipline as every prior entry, extended this
  session to all 8 ERC batches per state (see methodology correction above); every rule-XML claim traced
  to a specific line number and cross-checked against a second source (the algorithm `.md`, the live
  rater's own formulas, or both) before being reported as confirmed.
- **Known gaps, flagged as things to watch:** Special Class Business Income and Mining Properties
  Business Income are confirmed to exist but have zero tracing behind them — treat any claim about their
  mechanics as unconfirmed until a session actually opens those rule files. `BasicGroupIIRate` and
  `LowestBasicGroupIIRate` (the Building-shared tables BGII's own base rate depends on) have not yet had
  the all-8-batch per-state check applied, unlike every table built fresh this session — worth doing
  before trusting a "header-only at CW" label on either.

### ▶ Next session

Pick one of the five newly-surfaced Business Income paths (Earthquake is the highest-value target —
genuinely different mechanics, not just a smaller repeat of BGI/BGII/Broad/Special) or continue the BGI
Building rate build-up from Entry 27. Run the all-8-batch per-state check on `BasicGroupIIRate` /
`LowestBasicGroupIIRate` before assuming their CW-level "header-only" label is the full picture — every
other table this project has called header-only and then actually checked per-state turned out to have
real filed data somewhere. Otherwise unchanged from Entry 27: the ~146 not-yet-itemized coverage
families from Entry 10, and the four-state pending-manual-access list (Idaho, Louisiana, Mississippi,
Washington).

---

## Entry 29 — full rating-path build-status grid; Specific/Tentative confirmed unbuilt project-wide; a near-miss on live-Excel automation

- **Date:** 2026-09-11 (same day as Entry 28, follow-on request).
- **Directed:** build one consolidated HTML grid enumerating every rating path this project knows about —
  form × rating type × coverage, granular (e.g. "Building BGI Class Rated" as its own row, distinct from
  "Building BGI Specific/Tentative") — each marked against whether it's actually built in
  `CFRater1.01.xlsb`.
- **Built:** `Excel_Rater_AllRatingPaths_BuildStatus.html` — 24 rows across four sections (Building &
  Contents core forms; Business Income main forms; Business Income's untraced paths from Entry 28;
  the 34 endorsements grouped into 5 clusters), each tagged Built / Confirmed not built / Unverified.
  Explicitly did **not** mark unopened paths as "not built" — a large majority of the grid is honestly
  "don't know yet," not "missing."
- **New finding:** checking whether Specific/Tentative rating (an alternate `RatingType` to Class-rated)
  was wired up anywhere required scanning `Bldg Rating Worksheet`, `Contents Rating Worksheet`, `BI
  Rating Worksheet`, and `CoreScratchpad` for any reference to "Specific," "Tentative," or the
  `RatingType` input actually branching a formula. Zero hits anywhere, even though "Rating Type" exists
  as a dropdown on `Location Inputs`. **Specific/Tentative rating is confirmed not built for any form, in
  either Building or Contents** — a single project-wide gap inside the otherwise-complete core paths, not
  a per-form omission.
- **Process incident, handled correctly but worth logging:** mid-check, a `win32com.client.Dispatch`
  call threw `Property 'Excel.Application.Visible' can not be set` — investigating (via `Get-Process
  EXCEL`, then a careful read-only `GetObject` attach, no write/close attempted) found a live Excel
  process holding the user's own open `CyberIncidentExclusionFactors_Tables.xlsx`. Stopped all COM use
  immediately, did not close or touch that process or workbook, and completed the remaining check purely
  via `pyxlsb` (no Excel process interaction at all, zero risk). Flagged directly to the user rather than
  silently working around it. **Lesson for future sessions:** `Dispatch("Excel.Application")` is not
  guaranteed to create an isolated new instance — it can surface errors against an existing running
  instance instead. Prefer `pyxlsb` for anything that's a pure read (no formula text needed); reserve
  `win32com` for when formula text specifically is required, and treat any unexpected COM error as a
  stop signal, not a retry signal.
- **Checked against:** same read-only discipline as Entry 28's live-rater audit, extended with an
  explicit process-safety check before any further COM use once the anomaly appeared.

### ▶ Next session

Unchanged from Entry 28: Earthquake as the highest-value next Business Income target, or the all-8-batch
per-state check on `BasicGroupIIRate`/`LowestBasicGroupIIRate`. Additionally: any of the "Unverified"
rows in `Excel_Rater_AllRatingPaths_BuildStatus.html` can be picked up and actually checked against the
rater the same way the core forms were — that grid should get rows moved from Unverified to
Built/Not-built over time, not stay static.

---

## Entry 30 — zoomed out to the whole Property line; found and reconciled two stale cross-references in existing docs

- **Date:** 2026-09-11 (same day, third follow-on).
- **Directed:** "list EVERY Property Rating element... think beyond this session... property
  holistically, using the manuals and ERC" — Entry 29's grid was Business-Income-only; this asked for
  the whole CF line, coverage × form × rating basis, granular (e.g. "Building BGI Class, Specific" as
  distinct rows).
- **Found before building anything new:** `Coverage_Inventory_And_Tracking.md` already exists
  (2026-08-19, corrected same day) and already does exactly this at the whole-package level — a sweep of
  every `Rule.xml` in the ERC package for a `SetPremium` rule, normalized down to **243 distinct
  coverage/endorsement families** across all of CF, not just Business Income. Updated that document in
  place rather than forking a second, competing source of truth for the same question.
- **Two real corrections surfaced while reconciling this session's work against it:**
  1. `Coverage_Inventory_And_Tracking.md` Part A already lists **Special Class Business Income as fully
     documented** — `CauseOfLoss_SpecialClassBusinessIncome_RatingAlgorithms.md` is a real, complete
     53KB doc. But `CauseOfLoss_BusinessIncome_RatingAlgorithms.md` (read directly this session, both in
     Entry 28 and again today) contains a stale line calling it "existence only — not traced in depth,"
     almost certainly written before the Special Class Business Income doc was finished the same day and
     never looped back to remove. Flagged in place in the inventory doc; not fixed in the Business Income
     doc itself this pass.
  2. Entry 28's own framing overstated a gap: it described Business Income's Earthquake rate chain as
     "not opened in the rater," which is true of the *live-rater* status but implied the *documentation*
     was also missing — it isn't. `CauseOfLoss_BusinessIncome_RatingAlgorithms.md`'s own "Earthquake —
     rate build-up" and "Earthquake — premium: the Agreed Value asymmetry" sections (read directly during
     Entry 28 itself) already trace the full 8-step chain and the Agreed-Value-only premium mechanism.
     What's genuinely still open: the *standalone* Earthquake endorsement that attaches EQ coverage in
     the first place (a different question, tracked separately in the inventory doc's Part B11), and
     whether any of it is checked against `CFRater1.01.xlsb`.
- **Built:** `Excel_Rater_Property_MasterRatingGrid.html` — two layers. A granular top section (22 rows:
  5 core coverages × their cause-of-loss forms, including the 5th "Earthquake" form for Business Income
  and Special Class Business Income, × 4 rating-basis columns) confirming **Specific/Tentative rating
  only ever branches off Basic Group I** — every other form's Specific/Tentative cells are N/A, not a
  gap, per `Excel_Rater_BasicGroupI_AlgorithmGrid.html`'s own earlier finding. A rolled-up bottom section
  summarizing the inventory doc's 243-family count by layer (5 core / 92 itemized endorsements / ~22
  Earthquake+Flood standalone files / 5 Unmanned Aircraft variants / **~146 still not individually
  named**) rather than re-itemizing every family as its own HTML row.
- **Checked against:** cross-referenced every claim in the new grid against `Coverage_Inventory_And_
  Tracking.md`'s own Part A/B/B11 tables before asserting documented-vs-not, rather than re-deriving
  status from memory of this session's own narrower Business Income work.
- **Known gap, unchanged:** the ~146 not-yet-itemized families are still just names, not traced — this
  entry didn't reduce that number, only made its size and position in the whole picture clearer.

### ▶ Next session

Same as Entry 29, plus: the ~146 not-yet-itemized families in `Coverage_Inventory_And_Tracking.md` are
now the largest single unknown surfaced across this whole project (CF or GL) — worth a dedicated pass to
at least name them all, even before tracing any individually. The stale "not traced" line in
`CauseOfLoss_BusinessIncome_RatingAlgorithms.md` §"Special Class Business Income" should get corrected
in place next time that doc is open for any reason.

---

## Entry 31 — the ~146 remainder named: 143 new families identified and grouped, closing Entry 10's oldest open item

- **Date:** 2026-09-11 (same day, fourth follow-on — direct request: "we need to identify those").
- **Directed:** name the ~146 families Entry 10 (2026-08-19) found but never itemized — the oldest
  standing open item in this whole log.
- **Method:** reproduced the original sweep exactly (`grep -lE '"SetPremium"' *.xml` across the whole
  `Rules` directory — **546 files, confirmed identical** to the original count, good sign the underlying
  data hasn't drifted). Wrote an independent normalization script (suffix-stripping cause-of-loss-form
  and coverage-type tokens) without access to the original one — landed on 230 distinct families vs. the
  original's 243, expected drift from a different regex, same "approximate boundaries" caveat the
  document's own Method section already carries. Diffed against every family name already itemized in
  Parts A/B/B11/C (exact match after normalization, not fuzzy substring — an early fuzzy-match attempt
  produced a clearly-wrong result, tightened before trusting it): **145 unmatched, almost exactly the
  original "~146" estimate** — strong cross-validation that both the original count and this pass's
  re-derivation are measuring the same real thing.
- **Found:** 2 of the 145 were normalization artifacts (`Structure`/`StructureBuilding`, over-stripped
  duplicates of the already-documented Building family) — **143 genuinely new family names**, written
  into `Coverage_Inventory_And_Tracking.md` as new **Part D**, 14 subsections grouped by theme the same
  way Parts B1-B10 are. Largest two: Green Upgrades cost-increase endorsement (21 files — one per
  coverage per cause-of-loss form) and Scheduled/Unscheduled Tenants-Policy Building Property, split by
  Glass vs. Other-Than-Glass (20 files) — both bigger by file count than Ordinance or Law (18), the
  largest cluster from the original itemized set.
- **Explicitly not overclaimed:** flagged (not silently merged) a handful of Part D entries that are
  *likely* near-duplicates of existing Part B rows under a slightly different derived name
  (`CivilAuthorityIncreasedCoveragePeriodRadius`, `ExtraExpenseFromDependentPropertiesSpclClassBusnIncomeDetail`),
  and one correction to an existing Part C count (Unmanned Aircraft's "5 variants" is actually 10 — each
  attaching coverage splits into a Drone sub-form and an EQ sub-form). Also flagged the Ordinance-or-Law
  Tenants'-I&B file-level variants (12 files) as a cross-reference to the already-itemized B3, not a
  separate new cluster, since the sweep just failed to collapse those 4 specific filenames the way it
  did elsewhere.
- **Updated the doc's own "What's still not itemized" section and Summary count table in place** rather
  than leaving them contradicting the new Part D.
- **Checked against:** the near-exact match between this session's independent 145 and the original
  document's "~146" (written three weeks earlier, different session, different method in the small
  details) is itself a form of verification — two independent derivations landing on the same number is
  stronger evidence than either alone.
- **Known gap, unchanged:** naming is done; tracing is not. None of the 143 have been opened and read —
  this entry closes "what are they called," not "what do they do."

### ▶ Next session

The oldest open item in this log (Entry 10's ~146 remainder) is now closed as a naming exercise — next
natural step is picking one Part D cluster (Green Upgrades or Scheduled/Unscheduled Tenants Policy, the
two largest) and actually tracing it the way Ordinance or Law's structure was sketched. Otherwise
unchanged from Entry 30.

---

## Entry 32 — categorized/filterable view built on top of the full granular grid

- **Date:** 2026-09-11 (same day, fifth follow-on — direct request: "can we create some sort of
  architecture, which bundles these into larger categories? Like Earthquake for example is the coverage,
  and be able to filter within that, as an example").
- **Directed:** take the 161-endorsement-family existence matrix from Entry 30's
  `Excel_Rater_Property_FullGranularGrid.html` (identical underlying coverage × cause-of-loss-form data,
  Built-status-agnostic per the standing "don't worry about live-rater build status" instruction) and
  organize it into larger thematic buckets a person could click through, the way "Earthquake" reads as
  one coverage even though it's several files underneath.
- **Method:** wrote a mechanical regex classifier (`categorize.py`) matching each of the 161 family names
  against 19 named category patterns (Earthquake & Volcanic Eruption, Flood, Valuation Overlays,
  Business Income Time-Element & Dependent Properties, Ordinance or Law, Builders Risk, Leasehold/Leased
  Property, Utility Services, Green Upgrades, Scheduled/Unscheduled Tenants Policy, Vacancy & Special
  Perils, Cannabis, Unmanned Aircraft/Drone, Special Class Scheduled Valuables, Special
  Coinsurance/Additional Locations, Debris Removal, Terrorism/TRIA, Pier & Wharf, Equipment Breakdown),
  with unmatched names falling to a 20th "Miscellaneous / Single-Purpose" bucket. One regex gap caught
  and fixed before finalizing (`PerOfRestrtn`, an abbreviated form of "Period Of Restoration" that the
  first-pass pattern missed). 135 of 161 matched a named category on the first real pass; 25 fell to
  Miscellaneous.
- **Built:** `Excel_Rater_Property_CategorizedGrid.html` — same 5 core-coverage rows + 161 endorsement
  rows as the full granular grid, each row now tagged with `data-cats` and a small category badge, plus a
  sticky filter bar (21 buttons: All, Core Coverage, and the 19 named categories + Miscellaneous, each
  showing its family count) with vanilla client-side JS — click a category, the table narrows to just
  those rows, no server or rebuild needed. Business Income Time-Element & Dependent Properties is the
  largest bucket by a wide margin (38 families); Earthquake & Volcanic Eruption is 8.
- **Checked against:** row count came out to 166 (161 endorsement + 5 core), matching the full granular
  grid exactly — confirms no families were silently dropped or duplicated going from one file to the
  other.
- **Known gap:** category assignment is regex-on-filename, not read-and-confirmed per family — same
  "approximate boundaries" caveat `Coverage_Inventory_And_Tracking.md` already carries for the underlying
  names themselves. A few families likely span more than one category or are near-duplicates that got
  split by the sweep (flagged inline in Entry 31); not hand-corrected this pass.

### ▶ Next session

Same as Entry 31 — pick one category or Part D cluster and actually trace it. The categorized grid is a
navigation aid for choosing where to start, not a substitute for opening a rule file.

---

## Entry 33 — Special Class traced end-to-end for Basic Group I and II; live rater build started in parallel; three state-filing gaps found (NY, FL, MT); one indexing bug and one process-discipline lapse caught

- **Date:** 2026-09-14 (long single-day session).
- **Directed:** open-ended follow-on to Entry 31/32's Special Class category work — "what is Special
  Class," then progressively: trace it, mock up its input page, decide own-tab-vs-conditions, wire real
  formula suggestions against the live rater, and check state filings before trusting any of it.

### What got traced

- **Special Class Basic Group I** — first-ever read of `CauseOfLoss_SpecialClass_RatingAlgorithms.md` for
  this coverage. Confirmed **no `RatingType`/Specific-Tentative concept exists anywhere in this datadef
  group** (zero matches, full-text search) — resolves the "presumed absent, unverified" status this
  coverage carried since the rating-paths checklist was first written. Confirmed structural absences
  matching Building's own gaps (no LOI factor anywhere, no sprinkler-leakage dimension, no roof/BCEG
  factors, no multi-res credit) plus Special-Class-only quirks (protection class folded into the base-rate
  lookup key instead of a separate factor; an orphaned `ProtectionClassFactor` computed but never
  consumed). Built `Excel_Rater_SpecialClass_HowItWorks.html`.
- **Special Class Basic Group II** — same treatment. Confirmed `BaseRate` and `LowestBaseRate` read the
  **exact same shared tables** Building's own Basic Group II uses (`BasicGroupIIRate`,
  `LowestBasicGroupIIRate`) — anything already built for Building's state coverage carries over directly.
  Confirmed `NumericValue` does **not** carry over — Special Class keys it off the raw `ClassDescription`
  against `SpecialClassBasicGroupIINumber`, a completely different table from Building's
  `ClassCode`/`ConstructionCode`-driven version. One open question surfaced and left unresolved:
  `BasicGroupIISymbol` has no assigning rule anywhere in this ruleset — read directly wherever needed,
  origin unknown. Built `Excel_Rater_SpecialClass_BGII_HowItWorks.html` (first pass caught by direct
  feedback for omitting the full end-to-end formula block every other page in this set has — fixed same
  session).
- **Building's own Basic Group II**, standalone (no comparison framing, per direct instruction) — built
  `Excel_Rater_BGII_Building_HowItWorks.html`. Surfaced two findings while tracing it: the wind/hail-
  excluded rebuild branch is unresolvable in 8 states (correlated zero-filing across two tables, inferred
  not confirmed against manual text) *(correction note, 2026-10-06, `cf-bgii-chains.html` PP review #10:
  all 8 override the cause-of-loss rule, so the countrywide rebuild is never reached there)*, and `OperationalUnitWindstormOrHailExclusionFactor` is computed but
  never consumed anywhere in the rule file — an orphaned factor, same pattern as Special Class's own
  orphaned `ProtectionClassFactor`.

### What got mocked up, then found already half-built live

- Wireframed a "Special Class Item Inputs" own-tab design (`Excel_Rater_SpecialClass_InputWireframe.html`)
  after confirming a single location can carry multiple scheduled Special Class items (the "1-1" style
  composite Item ID scheme was proposed here specifically to disambiguate buildings across locations).
  Separately reasoned through why the rating logic itself belongs on its own `Calc_SpecialClass_BGI`-style
  tab rather than as conditions inside Building's tab (`Excel_Rater_SpecialClass_TabVsConditions.html`) —
  9-factor comparison found only 1 of 9 steps genuinely shareable.
- Mid-session, discovered the user had **already built much of this live** in `CFRater1.01.xlsb`, in
  parallel with the design conversation — new `Special Class Inputs`, `Special Class Worksheet`, and
  `Special Class` (data) tabs, complete with the exact `Item ID` (`Location# - Building#` /
  `Location# - Item#`) scheme independently landed on. From that point the work shifted to reviewing the
  live build read-only and supplying real formula suggestions against actual cells, not more mockups.

### Bugs found and fixed, live-rater formula suggestions only (no writes made by the assistant)

- **A systematic 0-indexing bug in every cell reference given this session** — `pyxlsb` reports both rows
  and columns 0-indexed; every row/column cited was off by one until the user caught it twice (row, then
  column) by comparing against what was actually in the file. Re-read fresh both times; every formula
  after that point verified against direct reads rather than assumed offsets.
- **A live formula bug**, diagnosed via read-only review: `CoreScratchpad`'s new `Deductible Factor` cell
  was returning `0` because the `Deductible` input is stored as text with a comma (`"2,500"`) while the
  lookup table's `Deductible` column stores plain numbers (`2500`) — `SUMPRODUCT`'s equality test never
  matched. Fix: wrap the input in `VALUE(SUBSTITUTE(cell,",",""))` before comparing.
- **A real gap in the AOI figure feeding the deductible factor**, caught by the user's own question ("shouldn't
  it use the total building limit"): an item flagged "Limit Included in Building? = Yes" needs to read its
  *linked building's* combined total (Building + Contents + linked Special Class items), not its own
  scheduled limit. Formula supplied uses `MATCH` against the `Item ID` row to find the right building's
  column, then `INDEX`ing into that building's own combined-total row — same cross-tab lookup mechanism
  used throughout this design (`Excel_Rater_SpecialClass_BuildingIDVerification_Wireframe.html`,
  `Excel_Rater_SpecialClass_TotAmtInsuranceLinking_Walkthrough.html`).
- **Confirmed `MultiPremiumAndDispersionCreditFactor` and both Cyber exclusion factors are policy-level,
  endorsement/schedule-gated values**, not coverage-specific — every coverage tab should reference one
  shared resolved cell, not carry its own independent flat `1.0`. Not yet fixed across Building/Contents/BI's
  existing tabs; flagged, not built.

### State-filing sweep — three real findings, one process failure

- **`BasicGroupIRateSpecialClass` (Special Class's own Basic Group I base rate): NY genuinely deviates.**
  84 value differences from CW on shared keys, swings over 400% in places (`Option7b`/"5 to 8": CW `1.188`
  vs NY `0.150`). PR matches CW exactly. `SpecialClass_BGI_Rates.xlsx` was CW-only; added an
  `NY (deviates from CW)` sheet and a warning on the main sheet.
- **`BasicGroupIIRate`/`LowestBasicGroupIIRate` (Building's and, by the shared-table finding above,
  Special Class's own Basic Group II base rate): confirmed state-only filing pattern**, zero CW rows in
  every edition back to 2019, real data filed in essentially every state. Rebuilt
  `BGII_BaseRate_LowestBaseRate_NumericValue.xlsx` with the full combined per-state dataset instead of
  empty CW placeholder sheets; also swept `NumericValue` and found Montana genuinely deviates (construction
  code 3, four class codes) while GA/KS file harmless CW subsets and NY/PR rely on fallback.
- **Florida is a compounding problem, not just a data gap.** No package exists in the current
  (2026-06-01) ERC batch at all — last available edition is `20241201 V01`, over a year stale. And even on
  that last-available edition, FL doesn't use the generic `BasicGroupIIRate` table — it branches on a
  Residential/Non-Residential occupancy test (`RuleTypeStateSpecific` override rule) into two separate
  tables. Confirmed the two tables are currently byte-identical, so the existing `BGII_BaseRate_Building_FL.xlsx`
  single-sheet pull is accurate data — but the mechanism itself (and the risk that the two branches
  diverge in a future edition) wasn't previously documented.
- **Process failure, called out directly by the user and worth repeating here so it isn't relearned the
  hard way twice:** all three of the above should have started with a check of
  `CF_ERC_Latest_Version_Summary.xlsx` and this project's own existing Supporting Tables files
  (`BGII_BaseRate_Building.xlsx` already had the full 47-state, correct-edition-resolved sweep — including
  the exact FL zero-rows finding — done before this session started). Spent real turns re-deriving from
  raw ERC folders before being pointed at what already existed. **Standing lesson: check state ERCs
  directly (not just CW) and this project's own existing docs/Supporting Tables before re-deriving
  anything from scratch — manuals as a last resort, not a first move, and never skip straight to "CW says
  X" without checking whether the state files something different.**

### Known open items, not closed this session

- `BasicGroupIISymbol`'s origin, for Special Class specifically — no assigning rule found.
- `SpecialClassBasicGroupIINumber` (Special Class's own `NumericValue` source table) hasn't been swept for
  state deviations the way Building's equivalent tables were.
- The blanket-rating mechanism is still unbuilt workbook-wide — blocks `FullSpecialClassValue`,
  `BlktCoinsurance`, `BlktLimit` for every coverage, not just Special Class.
- `MultiPremiumAndDispersionCreditFactor`/Cyber exclusion factors: recommended single-source-of-truth
  pattern, not yet applied to Building/Contents/BI's existing independent `1.0` rows.

### ▶ Next session

Pick up wherever the live build in `CFRater1.01.xlsb` has moved to since — re-read `Special Class Inputs`,
`Special Class Worksheet`, and `CoreScratchpad` fresh before trusting any cell reference from this entry,
since rows and columns shifted multiple times even within this single session. Resolve the
`BasicGroupIISymbol` open question and sweep `SpecialClassBasicGroupIINumber` for state deviations before
treating Special Class's own Basic Group II as done the way Basic Group I now is.

---

## Entry 34 — Special Class Business Income traced through BGII/Broad/Special; Legal Liability's real mechanism found; two Entry-33 open items closed

- **Date:** 2026-09-16.
- **Directed:** continue the Special Class build (Business Income side), then explain how the Legal
  Liability rating path differs from the Class/Specific paths.
- **Built:**
  - `Excel_Rater_SpecialClassBusinessIncome_BGII_HowItWorks.html` — the BGII chain end to end, with a
    single-block full algorithm and dedicated shared-factor / shared-table sections.
  - `Excel_Rater_SpecialClassBusinessIncome_ReuseMap.html` — per-value verdicts (COPY / SHARE THE TABLE /
    BUILD OWN) for BGI, BGII, Broad and Special, built from a rule-by-rule diff of
    `CommercialPropertySpecialClassRules.Rule.xml` against
    `CommercialPropertySpecialClassBusnIncomeRules.Rule.xml` — 68 rule names in both files, 40 only in
    Business Income, 58 only on the building side.
  - `Excel_Rater_LegalLiability_vs_ClassRated_Building.html` and
    `..._PersonalProperty.html` — how the Legal Liability path forks from Class/Specific, one per coverage
    because the two mechanisms genuinely differ.
  - `Rater_Simplifications_Backlog.md` — new standing file for accepted divergences (S-1 vandalism,
    S-2 windstorm/hail).
  - Supporting Tables (single-purpose files, per the user's standing rule): `VandalismExclRate_FL.xlsx`,
    `SpecialClass_VandalismExclRate_FL.xlsx`, `SpecialClass_VandalismExclFactor_AllStates.xlsx`,
    `SpecialClass_VandalismExcl_Gate.xlsx`, `BusinessIncome_VandalismExclFactor_AllStates.xlsx`,
    `BusinessIncome_VandalismExcl_Gate.xlsx`, `BasicGroupII_RateDerivation_Tables.xlsx`,
    `SpecialClass_Broad_BaseRate.xlsx`, `SpecialClassBusinessIncome_Special_BaseRate.xlsx`; plus two
    tables added to `BusinessIncome_FactorAndEnums_Tables.xlsx`.

### Entry 33 open items — closed

- **`BasicGroupIISymbol`'s origin for Special Class: closed, and the answer is "nothing derives it."**
  `ToDataDef="BasicGroupIISymbol"` appears in exactly three rule files across the whole CW package —
  `CommercialPropertyStructureRules`, `CommercialPropertyPersonalPropertyRules`,
  `CommercialPropertyBuildersRiskRenovationsRules` — and none of them is a Special Class file. The field
  *is* declared on the `CommercialPropertySpecialClass` complexType in `MasterCFCW.DataDef.xsd` (nillable
  string, length 16). So for Special Class it is a **submission input, not a derived value**. The search
  for an assigning rule was looking for something that does not exist.
- **`SpecialClassBasicGroupIINumber` swept for state deviations: closed.** CW files 71 rows; **FL is the
  only state filing its own**, at 68 rows. The interesting part is not the count: **11 of FL's
  `SpecialClassDescription` strings do not appear in CW's list at all.** The key itself is state-dependent
  text, so a rater that keys this table on a CW-derived description list silently misses in FL.

### Findings — Special Class Business Income

- **BGII does its own lookup, BGI does not.** BGI is a literal `Copy ../../BasicGroupIRate`. BGII runs
  `LookupBasicGroupIIRate` against the same matrix the building uses, with the same four keys — and all
  three variable keys are read `../../` off the parent item. The two `BasicGroupIIRate` values are
  therefore equal *by construction*, not by coincidence.
- **`BasicGroupIIRate` and `LowestBasicGroupIIRate` have zero CW rows.** 45 states file the first,
  39 the second; **FL and PR file neither**, and AR, DC, KS, NY, RI and TX also lack the lowest-rate table.
  There is no countrywide fallback to lean on — the state row is the only row.
- **The wind/hail-excluded BGII branch drops the class hazard load.** It rebuilds from
  `LowestBasicGroupIIBaseRate × LCM × WindstormOrHailExclFactor` and never references `BasicGroupIIRate`,
  so `../../BasicGroupIINumericValue` silently falls out of the rate.
- **Broad is the clearest "same table, do not copy" case in the group.** Both sides read
  `BroadFormBaseRate` with a hardcoded `"Frame"`; the building passes `"Bldg"` (0.015) and Business Income
  passes `"Business Income Without Extra Expense"` (0.011) or `"All Other"` (0.023). Pointing one at the
  other is 36% high on one CovType and 35% low on the other.
- **Special reads entirely different tables on the two sides** despite identical rule *and* datadef names:
  `SpecialBuildingRate` / `SpecialBldgTheftExclusionFactor` (0.88) on the building,
  `SpecialFormIncldgTheftTimeElementBaseRate` / `SpecialLeaseHoldTimeElementTheftExclusionFactor` (0.86)
  on Business Income.
- **Three of Special's four lookup keys are literals** on the Business Income side — `"Frame"` and
  `"Other than Apartments and Condominiums"` — so exactly two rows per state are reachable (CW 0.033 and
  0.047). An apartment risk gets the non-apartment rate.
- **The vandalism/wind-hail/theft exclusions each file two separate endorsement records**, one on the item
  and one on the Business Income group. Logged as S-1 and S-2; theft is not yet logged.

### Findings — Legal Liability

- **The fork is in the premium, not the rate chain.** Everything through
  `BasicGroupICauseOfLossAdjustment` is shared code that has already run. `SetPremium` is a `Choose`, and
  the Legal Liability branch picks the rate up **three steps earlier** than the Class-rated branch:
  Class-rated starts from `FinalBasicGroupIRate`, Legal Liability from
  `BasicGroupICauseOfLossAdjustment`. Coinsurance, the LOI factor and the deductible factors are computed
  and then ignored, and `MultiPremiumAndDispersionCreditFactor` is not applied at all.
- **Two factors exist only on this path**, both countrywide with no state filings:
  `LegalLiabilityFactor` (State + a CovType literal — `"Bldg"` 0.25, `"PersProp"` 0.50) and
  `AddlInsurableInterestFactor` (Option1/2 = 1.25, Option3/4 = 1.0).
- **A missing additional-insurable-interest option zeroes the premium.**
  `SetLegalLiabAddlInsurableIntFactor` defaults to `0.0`, not `1.0`, and the premium multiplies by it
  unconditionally. Options 3 and 4 are already 1.0, so a neutral value exists in the table and the rule
  simply does not reach for it. Reproduce as filed; do not "fix" without a circular check.
- **Blanket is unreachable for Legal Liability.** `Choose` is first-match and the Legal Liability test sits
  ahead of the blanket test, so a blanketed Legal Liability item still rates as scheduled.
- **Building and Personal Property do not share the mechanism**, only the table. Building gates on
  `CovType = "Legal Liability"`; Contents gates on `CovForm = "Legal Liability Coverage Form"`. The datadef
  is `LegalLiabilityFactor` on one side and `LegalLiabFactor` on the other. Contents sets its factor
  unconditionally; Building gates it to `0.0`. And the additional-insurable-interest record attaches at the
  **item** on Building versus the **occupancy class** on Contents.

### Corrections made during the session

- Claimed the apartment/condo rows of `SpecialFormIncldgTheftTimeElementBaseRate` were unreachable filed
  data and implied a filing gap. **Wrong, and withdrawn in-session.** A sweep of every rule file reading
  that matrix found at least six chains; plain Business Income reads both keys off the risk and hits every
  row. The narrow claim that survives: those rows are unreachable *from the Special Class Business Income
  chain specifically*.
- Reported FL and PR as filing no `SpecialFormIncldgTheftTimeElementBaseRate`. **Backwards** — they are the
  only two states that file their own, with materially different rates. The spreadsheet was built
  correctly; the narration was not.

### Standing lesson — from the correction above

The existing lesson "enumerate before deriving" did not prevent this, because the enumeration *was* done —
just scoped to one rule file. **A claim that filed data is unreachable is a claim about every consumer of
that table, so it requires a package-wide sweep of `MatrixFromConstant="<table>"`, not a read of the chain
you happen to be in.** The missing automated check: before writing "dead", "unreachable" or "never used"
about any matrix, grep the whole `Rules` directory for that matrix name and list every caller with its
keys. Cheap, mechanical, and it would have caught this before it reached the user.

### Findings — Legal Liability, second pass (same session, after the two docs were written)

- **It is 21 premium branches, not 8.** Four families carry a Legal Liability branch:
  Structure/Building (4 forms), PersonalProperty PrsnlProp (4), **Non-Owned Trailers** (5, including its own
  Earthquake), and the **Earthquake and Volcanic Eruption endorsements** (8 files — 4 building-side using
  `LegalLiabilityFactor`, 4 contents-side using `LegalLiabFactor`). The two docs written this session cover
  the first 8. The other 13 are confirmed to exist with their gate field and factor datadef identified;
  their formulas are untraced.
  - *Correction to an in-session statement:* I said there is no Earthquake member for Personal Property
    Legal Liability. True of the `PersonalPropertyPrsnlProp*CoverageRules` family (4 coverage files, no EQ),
    but misleading overall — Earthquake Legal Liability exists in the Earthquake endorsement rulesets.
- **Selection happens at different levels on the two coverages.** Building sets `CovType` on the building
  item. Contents' `SetCovForm` is a plain `Copy ../../CovForm`, and `../../` from
  `CommercialPropertyPersonalProperty` resolves to **`CommercialPropertyOccupClass`** — so the form is chosen
  once per occupancy class and every contents item inherits it. No per-item override, so Legal Liability and
  BPP contents cannot be mixed within one occupancy class. This is also why the additional-insurable-interest
  record sits at occupancy-class level on the Contents side.
- **`DomainCovForm` is keyed State + PolicyType + RatingType.** Legal Liability is offered on a
  **Commercial Property Policy only** — absent from every Standard Property Policy row — and is available
  under **Class, Specific and Tentative** rating types, so it is not confined to class-rated risks.
- **The four additional-insurable-interest options, decoded** (Bureau rule 66.D.1.b):
  Option1 = General Lessees, Mgrs or Operators of Premises (1.25) · Option2 = Employees other than Executive
  Officers or Partners (1.25) · Option3 = Other (1.00) · **Option4 = None (1.00)**.
- **`DomainAddlInsurableIntOption` is header-only from the 20221001 package onward.** The plain-language →
  `OptionN` mapping survives only in the **20191201** edition; the plain-language list itself
  (`DomainAddlInsurableInt`) is still current. Another instance of the standing "check older editions"
  lesson, and the reason the option meanings were not obvious from the current package.
- **Eleven Building-vs-Contents divergences**, now tabulated identically in both docs. The one that moves
  money is Special's rate source: Building reaches for `SpecialRate` and therefore drops **both**
  `SpecialTheftExclusionFactor` and `LimitationsOnCovForRoofSurfacingACVFactor`; Contents reaches for
  `SpecialCauseOfLossAdjustment` and keeps the theft credit. Both factors default to 1.0, so the two agree on
  an unendorsed risk and diverge only when the endorsement is elected — it tests clean and fails on the
  endorsed risk.
- **Neither coverage blankets a Legal Liability item, for different reasons.** Building relies on `Choose`
  being first-match (the LL branch precedes the blanket branch); Contents' blanket branch names and excludes
  the LL CovForm explicitly. Copy Building's structure to Contents and you keep the outcome by accident.
- **Corrected the zero-premium framing.** `Option4` *is* "None" and returns 1.00, so a risk with no
  additional insurable interest is meant to be coded Option4. The `0.0` fires only on a **blank** field or a
  missing endorsement record — the input is **mandatory** once Legal Liability is selected, not optional with
  a bad default. Backlog Z-1 updated accordingly.

### Known open items, not closed this session

- Earthquake is untraced for every coverage — the only remaining form, and it gates ~29 Special Class rule
  files that each ship an Earthquake wrapper.
- Blanket rating is still unbuilt line-wide; Branch B is a stub in every premium file built so far.
- The theft exclusion's split endorsement record is not yet logged in the backlog (would be S-3).
- `AddlOptionsForExtraExpenseExpandedLimitsOnLossPaymentsFactor` and
  `AddlOptionsExtraExpenseExpandedLimitsMaxFactor` are traced but not yet extracted to Supporting Tables —
  blocked mid-session by an Excel file lock, and now due as single-purpose files under the user's standing
  one-table-one-file rule.
- Whether ISO intends Special Class Business Income's hardcoded `"Other than Apartments and Condominiums"`
  key is a manual/circular question the ERC cannot answer.
- Non-Owned Trailers (5 premium branches) and the Earthquake and Volcanic Eruption endorsements (8) both
  carry Legal Liability branches that are unread. Both queue behind the Earthquake trace.
- Whether Building dropping `SpecialTheftExclusionFactor` on a Legal Liability item is intended, or an
  artefact of reaching one line too early, is a manual/circular question.

### ▶ Next session

Earthquake, for Building first — it is the only remaining form and everything else queues behind it. Before
touching it, re-read the live `CFRater1.01.xlsb` tabs rather than trusting any cell reference recorded here.

---

## Entry 35 — CF request payload specified from ISO's own test cases; 924-payload STC corpus found; an ISO filed-data defect in the current AL edition

**2026-09-17.**

**The find that reframed the work.** Many ERC packages ship an `STC/` folder of ISO-authored
rating payloads. Nobody here had opened one. There are **924 across CF and GL — 206 containing
Personal Property, 7 for Alabama.** These are ISO's own regression cases: they rate. They are a
far better specification of the request format than the DataDef schema, which marks *every* one
of the 56,207 CF field rows `nillable="yes"` with no `minOccurs="0"` and so says nothing at all
about what is required.

A first payload spec had been reasoned from the schema plus the GL payload. The STC corrected it
on six counts: no `header`/`body` wrapper, no `StateCode` field (state comes from `ProductName`),
coverage records are `{}` not `[{}]`, `ConstructionType` is sent and `ConstructionCode` derived,
Location uses `ProtectClass` not `ProtectionClass`, and Personal Property carries **none** of
`RatingType` / `ClassCode` / `BldgClassCode` / `Group` / `Deductible` — all inherited.

**Output:** `CF_Payload_ClassRated_Bldg_PP_Alabama.md` (the spec) and
`CF_Payload_Completion_Tracker.md` / `.html` (what remains, by feature set).

**Derivations traced, closing four tracker items.**
- `ConstructionType` -> `ConstructionCode` is a six-row **rate** table, not a domain list —
  which is why `DomainConstructionCode` is empty in all 48 packages. Frame 1 … Fire Resistive 6.
- `Group` is set by **two** rules: OccupClass's `SetGroup` assigns A/B/C, Personal Property's
  assigns `YARD` from `BldgClassCode` + `YardPropertyIndicator`. Only route to YARD rating.
- **Correction to a claim made twice before:** `VacantBuilding = "Yes"` does *not* substitute
  class code `1180` into the rating path. It sets `ClassCodeForStat`, a statistical code.
  `ClassCodeToUse` has no vacancy branch — vacancy enters BGI via the additive
  `VacantBuildingRate`. `CF_RatingPath_Switches.md` carries the same conflation and should be
  corrected when next touched.
- Validated the field set across all 7 AL STC cases: policy (14 fields) and OccupClass (8) are
  fully stable; `ConstructionCode` appears in 1 of 7, so it **can** be supplied as an override.

**An ISO filed-data defect.** `LowestBasicGroupIIRate`, symbol `A`, `PersProp`, in
`CF AL 20270301 V01` is **0.8**. All seven prior AL editions file **0.08**, and every other symbol
still matches its Inland Territory rate exactly. Swept all 48 states' latest packages; only Maine
shows anything comparable, and its gaps are small enough to be a deliberate floor. Alabama's is a
10x jump that breaks its own edition history. *Impact:* a class-rated PP risk with a wind/hail
exclusion at symbol A rates BGII contents ~10x too high, because that branch rebuilds from the
lowest rate. **Raise with ISO; do not code around it.**

**Decisions recorded.** `LossCostMultiplier` defaults to **1.0** — it appears in no STC, and at
1.0 the filed ISO loss cost passes through unchanged, which is the only clean baseline for proving
the engine against ISO. Carrier LCM becomes a configured input **by LOB** (tracker Set 6), never a
submission field, and it must be applied *in-chain* rather than to a finished premium, because the
3-decimal rounding sits after the multiply. **Every rate in the spec is therefore an ISO loss
cost, not a carrier rate.**

**Engine still not started** — parallel work in flight. What this does unblock is
`cf_engine/schema/fields.py`, which `docs/CF-CHUNK0-BUILD-SPEC.md` had deferred "until the field
set is known from more than one coverage". It now is, for Building and Personal Property.

**Also this session:** both data dictionaries rebuilt to include every state package
(`GL_Data_Dictionary.xlsx`, `CF_Data_Dictionary.xlsx`), plus `*_State_Specific_Fields.xlsx` for
each line. A parser defect was fixed in the process — 104 GL and 614 CF child-group references
were being listed as if they were scalar fields. The STC independently confirms the fix:
singleton child refs serialize as `{}`, `Table` children as `[]`.

---

## NEXT SESSION STARTS HERE
