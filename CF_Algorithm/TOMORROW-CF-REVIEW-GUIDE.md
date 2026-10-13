# Pick This Back Up — Finishing CF's Full Rating-Specification Review

**Written:** 2026-09-02, as a self-contained continuation guide. Read this file alone tomorrow — it
points at everything else rather than repeating it, but you shouldn't need to open five other files
just to know where to start.

**The goal, stated plainly.** GL's rating specifications are fully reviewed: `GL_Algorithm/` holds a
`RatingAlgorithms.md` + `ERC_Tables.md` pair for every one of its ten coverage/endorsement families
(Building-equivalent core plus Liquor Liability, Railroad Protective, Owners & Contractors Protective,
Products/Completed Operations, Product Withdrawal & Cyber, Stop Gap, Terrorism, Loss of Electronic Data,
Unmanned Aircraft). That completeness is what let `gl_engine/` get built and gated coverage by coverage.
**CF is not there yet.** Five core coverages are fully documented; roughly 90 more endorsement families
are named but not traced, plus Earthquake and Flood — two large standalone clusters — are barely touched.
Finishing that same sweep for CF, the same way it was finished for GL, is what this guide walks through.

---

## 1. Where CF actually stands (as of today, 2026-09-02)

Read `Excel_Rater_FullBuildout_Scope.md` for the full picture — this is the two-sentence version:

- **Fully documented (ERC algorithm doc + tables doc):** Building, Personal Property, Special Class,
  Business Income, Special Class Business Income — 5 of an estimated 243 real coverage/endorsement
  families in the package (`Coverage_Inventory_And_Tracking.md`'s corrected count).
- **Named but not traced:** ~92 endorsement families itemized by name in
  `Coverage_Inventory_And_Tracking.md` Parts B/B11 (Ordinance or Law, Business Income time-element
  extensions, Earthquake and Volcanic Eruption endorsement, Leasehold Interest, Utility Services,
  Builders Risk, Vacancy Permit, Debris Removal, and more), plus **~146 families the corrected sweep
  found but nobody has individually itemized yet** — that itemization gap is itself unfinished work, not
  just the tracing behind it.
- **Separately, this session added:** a spreadsheet-build-guide layer (`Excel_Rater_*.md`) on top of the
  5 documented coverages, plus a rating-paths checklist and the scope document above. That layer is
  downstream of the ERC tracing — it doesn't advance the "full review" this guide is about, it consumes
  it. Don't confuse progress on `Excel_Rater_*.md` with progress on the underlying algorithm-doc sweep;
  they're different tracks, per that scope doc's opening section.

---

## 2. The method — already proven, don't reinvent it

`AGENTS.md` Part 2 documents the exact briefing pattern that produced all five of today's fully-documented
coverages, refined across four dispatched agents. Use it again, verbatim, for whichever family you trace
next:

1. **Read the template first** — `CauseOfLoss_Building_RatingAlgorithms.md` for structure and depth on a
   first pass; for anything structurally close to an already-documented family, also read that sibling
   doc (e.g. an Earthquake pass should read Business Income's own Earthquake section first, since that's
   the one place in this project an EQ chain has already been traced).
2. **Enumerate before assuming** — grep the real `Rules` directory for actual file names before tracing
   anything. This project's own rule #1, and the reason the original 97-family count turned out to be
   less than half the real 243 (see §4 below).
3. **Cite everything** — file name + line number for every rule reference, table name + confirmed file
   path + **row count** (not just existence) for every data claim.
4. **Never guess** — anything genuinely unresolvable from the ERC files alone goes into the report as an
   explicit open question, not smoothed over. (See `SpecificGroupIRate` in
   `Excel_Rater_BasicGroupI.md` §9 for a recent example of doing this correctly — no `Set`/`Lookup` rule
   was found for it anywhere, and that absence was reported as-is rather than papered over.)
5. **Report back structurally** — every dispatched agent should return three things: what files it wrote,
   the biggest structural differences it found versus the closest already-documented sibling, and a
   bullet list of open questions.

**One standing correction to carry forward, learned the hard way twice already in this project:**
"table exists" and "table has a usable data row" are different claims — verify both, every time
(`BUILD-LOG.md` Entry 3). And **when a search returns zero results for something you'd expect to exist,
that's a prompt to widen the search, not a reportable absence** — the original 97-family undercount
happened because one filename pattern (`*CoverageRules.Rule.xml`) was trusted without checking whether
ISO used a second one (`*EndorsementRules.Rule.xml`, which is where Earthquake and Flood turned out to
live). Don't repeat that specific miss on the next unfamiliar family.

---

## 3. Tomorrow's starting order — feature sets, not a flat queue

Pick one, not all — each is independently valuable and none blocks the others.

**A. Finish the itemization gap first, cheaply.** Before tracing anything new, close
`Coverage_Inventory_And_Tracking.md`'s own open item: run the corrected, unrestricted sweep (the command
is already in that doc's "Method" section — grep every `.xml` file for `SetPremium`, no filename
restriction) and individually name the ~146 families the corrected count found but the doc never listed.
This is bookkeeping, not tracing — an hour of work that makes every subsequent "what's left" question
answerable by name instead of by estimate.

**B. Trace Earthquake — the single highest-value cluster.** Up to 20 files (4 endorsement-form variants ×
5 attaching coverages), touches every core coverage, and this project already has a head start: Business
Income's own internal EQ *cause-of-loss chain* is traced (`CauseOfLoss_BusinessIncome_RatingAlgorithms.md`
§"Earthquake"), but the **standalone endorsement** that attaches EQ coverage to a policy in the first
place is explicitly flagged as untraced and possibly-related-but-unconfirmed
(`Coverage_Inventory_And_Tracking.md` Part B11's own scope note). Resolving that relationship is the
single most valuable open question in the whole endorsement backlog.

**C. Trace Flood.** Smaller (5 form variants, `FloodCoverageEndorsement` + `FloodCovEndtBlanketRatingDetail`),
genuinely untouched, and has one adjacent trap already flagged: `DischargeFromSewerDrainOrSumpNotFloodReltd`
looks flood-related by name and explicitly isn't — read Part B11's own note before starting so this
doesn't get merged into the Flood family by mistake.

**D. Trace Ordinance or Law — the largest itemized cluster (18 families).** Coverage A/B/C/B-and-C, each
further split across Basic Group I / Basic Group II / Earthquake for the Tenants' Interest in
Improvements and Betterments variant. Manual rule number not yet confirmed (Part B3's own note) — this
family would also be a good first target for the circular-verification leg, since resolving its manual
rule number is needed either way.

**E. Trace the Business Income time-element extensions (17 families).** Second-largest itemized cluster,
all attach to Business Income, which is already the most thoroughly documented of the five core
coverages — the sibling-doc-to-read-first step in the method above is unusually strong here.

**F. Add Special Class and Special Class Business Income to the `Excel_Rater_*` layer.** Not ERC tracing
at all — both algorithm docs already exist. This is the cheapest thing on this whole list, if you'd
rather advance the spreadsheet-rater track instead of the underlying review. (See
`Excel_Rater_FullBuildout_Scope.md` §6-C for the same item framed from that side.)

If nothing else gets decided by tomorrow morning, **B (Earthquake) is the recommended default** — it's
named explicitly as untraced in two different existing documents, touches every coverage, and has the
clearest immediate payoff (resolving the endorsement-vs-internal-chain relationship question).

---

## 4. What "done" looks like for one family

Mirror the shape every existing `CauseOfLoss_*_RatingAlgorithms.md` already has: master orchestration,
file map, rate build-up per form/branch, premium calc per form/branch, a comparison table against the
closest sibling, supporting-lookups tables, a quick-reference end-to-end block. Pair it with a
`*_ERC_Tables.md` doc listing every required table, each verified for **both** existence and row count,
with header-only tables flagged loudly the way `BasicGroupI_ERC_Tables.md`'s own correction note does.
When finished, update `Coverage_Inventory_And_Tracking.md`'s Part A/B tables to move the family from
"not yet documented" to documented, and this guide's §1 summary the next time it's read.

## Remaining steps

1. Pick a starting family from §3 — B (Earthquake) if nothing else forces a different priority.
2. Dispatch the trace using the §2 method — background agent or direct session work, whichever this
   project's usual pattern favors for a single-family pass (the four original core-coverage passes mixed
   both).
3. Nothing gets built into a workbook or engine from any of this — this guide is about finishing the
   *specification* review, one family at a time, per this project's standing rule.
