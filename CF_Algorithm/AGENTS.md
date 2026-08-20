# Agent Roster and Plan — CF Documentation Project

**Opened 2026-08-19.** This is the companion to `BUILD-LOG.md`: where that file is a diary of what
was built, this one is an inventory of *who built it* — every agent dispatched so far, and the plan
for what comes next, including two new specialist roles folded in at the request of 2026-08-19.

---

## Part 1 — Documentation agents dispatched to date

Four background documentation agents have been run this session, each producing one coverage's
rating-algorithm doc and required-tables doc. All four were dispatched through the same briefing
pattern (see Part 2) and all four ran read-only against the ERC corpus — none touched code, none
had write access outside `Spreadsheet_Rater\CF\`.

| # | Task | Traced | Output | Key structural finding |
|---|---|---|---|---|
| 1 | Document PersonalProperty rating algorithms | `CommercialPropertyPersonalPropertyRules.Rule.xml` | `CauseOfLoss_PersonalProperty_RatingAlgorithms.md`, `PersonalProperty_ERC_Tables.md` | Rates *N* records per Occupancy Class per Location (a `ForEach`), not one per building; three of four deductible factors are `Copy`'d from an ancestor record rather than computed locally |
| 2 | Document SpecialClass rating algorithms | `CommercialPropertySpecialClassRules.Rule.xml` | `CauseOfLoss_SpecialClass_RatingAlgorithms.md`, `SpecialClass_ERC_Tables.md` | No limit-of-insurance factor anywhere in any of its four chains; Broad's base-rate lookup uses a hard-coded `"Frame"` construction key regardless of actual construction |
| 3 | Document BusinessIncome rating algorithms | `CommercialPropertyBusinessIncomeRules.Rule.xml` | `CauseOfLoss_BusinessIncome_RatingAlgorithms.md`, `BusinessIncome_ERC_Tables.md` | Basic Group I, Basic Group II, and Earthquake borrow the coinsured Building's *already-computed* rate rather than computing their own; Earthquake is a real fifth chain with no standalone (non-Agreed-Value) premium file |
| 4 | Document SpecialClassBusnIncome rating algorithms | `CommercialPropertySpecialClassBusnIncomeRules.Rule.xml` | `CauseOfLoss_SpecialClassBusinessIncome_RatingAlgorithms.md`, `SpecialClassBusinessIncome_ERC_Tables.md` | Overwhelmingly clones plain Business Income's pattern rather than Special Class Building's; Basic Group I and Earthquake borrow the coinsured item's already-*final* rate, not just its base rate; Broad and Special key off hard-coded literal constants (construction and occupancy dimensions both) |

Agents 1 and 2 ran in parallel (independent files, no shared state). Agents 3 and 4 ran sequentially,
each briefed with the prior agents' documents as required reading, so later passes could correctly
identify what was novel versus what repeated an established pattern.

**Before these four**, the Building/Structure documentation (`CauseOfLoss_Building_RatingAlgorithms.md`
+ `BasicGroupI_ERC_Tables.md`) was produced directly in the main session, not by a dispatched agent —
it predates this project's agent-delegation pattern and served as the template every subsequent agent
was told to read first.

The twelve-and-growing decision-chain diagrams in `cf-rating-chains.html` were authored directly in
the main session in every case, not delegated — each pass reads the finished `.md` doc in full and
hand-builds the mermaid flowcharts, because getting the if/then branching visually right requires the
same close reading a delegated agent would otherwise have to redo.

---

## Part 2 — The documentation agent plan (the briefing pattern)

Every documentation agent above was given the same five-part brief, refined slightly each time based
on what the prior pass learned:

1. **Read the template first.** `CauseOfLoss_Building_RatingAlgorithms.md` for overall structure and
   depth; later agents were also pointed at the most structurally-similar prior pass (e.g. the
   Business Income agent was told to read the Special Class doc for how "structural differences from
   Building" sections get written, since both diverge from Building in different, non-obvious ways).
2. **Enumerate before assuming.** Grep the actual `Rules` directory for the real file names before
   tracing anything — this project's standing rule #1, adopted from `Recursive_Harness_2.0`'s own
   hard-won doctrine (see `BUILD-LOG.md`'s "Standing criteria" section).
3. **Cite everything.** File name + line number for every rule reference; table name + confirmed
   file path + row count for every data claim. Row-count verification (not just file-existence
   verification) became a standing requirement after Entry 3 caught a real gap — see below.
4. **Never guess.** Anything genuinely unresolvable from the ERC files alone gets written down as an
   explicit open question in the agent's final report, not smoothed over or inferred by analogy to
   a similar-looking coverage.
5. **Report back structurally.** Every agent was asked for the same three things in its closing
   summary: what files it wrote, the biggest structural differences it found, and a bullet list of
   open questions — so the orchestrating session could update `BUILD-LOG.md` consistently without
   re-deriving the summary from the raw doc each time.

**One correction propagated across the whole plan mid-stream.** The first two agents (Personal
Property, Special Class) verified tables by file existence only. The Business Income agent's briefing
was the first to explicitly require row-count verification, after a cross-check between the Personal
Property and Building docs found that `BasicGroupIRate.RateTable.csv` was header-only despite being
marked "confirmed present" in the original Building tables doc. Every subsequent agent brief has
carried this requirement forward as a named standing rule, and the original document was corrected in
place with a visible note rather than silently edited — see `BUILD-LOG.md` Entry 3.

---

## Part 3 — New: specialist review agents, modeled on the GL harness's existing four

`Recursive_Harness_2.0` already runs a mature four-agent structure for General Liability, defined in
`Agentic\{gl-authority, iso-erc-expert, iso-circular-expert, gl-engine-code-expert}\AGENT.md`. That
structure separates concerns deliberately: two independent single-source specialists (ERC content vs.
manuals/circulars), one code specialist, and one cross-cutting authority permitted to read all three
but obligated to always say which source backs which claim. Directed 2026-08-19 to fold CF equivalents
of the ERC and circular experts into this project's plan.

| GL agent | Role | CF equivalent | Status |
|---|---|---|---|
| `iso-erc-expert` | Authority on the ERC corpus content — answers questions, reviews an engine's output against the corpus | **`cf-erc-expert`** — `Agentic\cf-erc-expert\AGENT.md` | **Defined 2026-08-19.** Role and boundaries specified, scoped to the real CF corpus (447 directories at depth ≤2, edition-date-first layout, 8 editions). No `knowledge/` base or retrieval CLI yet — every question is answered by reading the corpus or this project's `.md` docs directly. Job 2 (reviewing an engine) is dormant — there is no CF engine yet. |
| `iso-circular-expert` | Authority on the manual/circular corpus — GL has 1,122 documents across five corpus families (Rules, Loss Costs, Terrorism, Schedule & Experience, Composite Rating) | **`cf-circular-expert`** — `Agentic\cf-circular-expert\AGENT.md` | **Defined 2026-08-19, corpus nearly empty.** Only six countrywide Rules PDFs exist at `Commercial Line Manuals\CF\CW\`, none extracted to text, no state-specific notices, no loss-cost corpus, no other plan families confirmed to exist for CF at all. Its own spec names the first real task as determining whether state-specific CF notices exist anywhere before building any tooling. |
| `gl-authority` | Cross-cutting reviewer permitted to read ERC, manuals, *and* code, obligated to never let one source silently fill another's gap | **`cf-authority`** — not started | **Blocked**, by GL's own design logic: `gl-authority`'s value depends on having two independently-built, already-trustworthy specialists to cross-check against each other. Building it before `cf-erc-expert` and `cf-circular-expert` are individually solid would just be one more source of unverified claims. |
| `gl-engine-code-expert` | Authority on the Python that executes GL rating | **`cf-engine-code-expert`** — not started | **Blocked on there being a CF rating engine.** `gl_engine/` is real, tested code; nothing equivalent exists for CF yet. This agent has nothing to be an authority on until that's built. |

**Why define two agents now instead of waiting until their corpora are complete.** GL's own agents
were built incrementally — `iso-circular-expert`'s own file logs corpus families being "added
2026-08-12" well after the agent's core structure existed. Writing `cf-erc-expert` and
`cf-circular-expert`'s role definitions now, honestly marked with their current limits, means:

- Every future session that touches CF documentation has a stable place to look for "what do we
  know, and what's still unverified" instead of re-deriving it from `BUILD-LOG.md`'s prose each time.
- The two agents' own `AGENT.md` files each name their own next-build-step in priority order, so
  picking this project back up doesn't require re-deciding what to build first.
- It makes the corpus gap visible and load-bearing rather than an unstated assumption. `cf-circular-
  expert`'s file states outright that CF's manual corpus is six documents deep against GL's 1,122 —
  that comparison is itself useful information for anyone deciding how much confidence to place in a
  manual-sourced claim about CF.

---

## Part 4 — Sequencing

**Documentation agents (Part 1), next in line:**
1. Finish the in-progress Special Class Business Income pass (agent #4 above).
2. The deferred cross-cutting endorsement cluster pass (Ordinance or Law, Blanket Rating, Value
   Reporting Form, Agreed Value, Inflation Guard, Peak Season, Utility Services, Leasehold Interest,
   Builders Risk) — named in `BUILD-LOG.md` Entry 2 and still outstanding.

**Specialist agents (Part 3), next in line, independent of the documentation track above:**
1. `cf-erc-expert`'s own priority list: build a `tools/cf.py` retrieval CLI, then a `knowledge/`
   base, then a CF-specific `invariants.json` seeded from the six open questions already logged in
   `BUILD-LOG.md`.
2. `cf-circular-expert`'s own priority list: extract the six existing PDFs to searchable text, then —
   the single highest-value open question — determine whether state-specific CF Rules notices exist
   anywhere and should be collected, since that changes the entire scope of what this agent can ever
   answer.
3. `cf-authority` and `cf-engine-code-expert` stay blocked until the above two are individually
   solid and a CF engine exists to review, respectively.

Both tracks can run independently — nothing in the endorsement-cluster documentation pass depends on
either specialist agent existing first, and vice versa.
