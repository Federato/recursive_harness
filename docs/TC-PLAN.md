# ISO Rating Test Console: the plan

**Status: PLANNED 2026-10-06, 1 of 38 tasks** (TC-01, the decisions, done). Source: the design package `Design brief questionnaire.zip` (6 Oct 2026):
the hi-fi prototype `ISO-Rating-Test-Console.html`, seven wireframes, and `readiness-matrix-integration.md`. The
user's ask: build the console into the app, and **remove the current testing pages**. Nothing here is built yet.

## In plain English

Today the app has one page that rates a submission and three testing pages that grew up over August
(`/tester`, `/tests`, `/review`). The design brief replaces the testing pages with **one console of seven screens**
that answers the question the old pages never did: *for each state and coverage, is it ready, and if not, what will
it take?* It does that by keeping every ISO answer we ever paid for in one store, tying each one to the rating path
it proves, noticing when ISO content changes underneath it, and spending the daily RaaS calls where they buy the most.

The plan builds it **data first, screens second, removal last**. The old pages stay until every job they do has a
home in the console, so the app never loses a capability in between.

| The seven screens (from the brief) | The question it answers |
|---|---|
| **Readiness Matrix** | State × coverage, both lines: passed, and if not, what's left and how many calls (no waves, D3) |
| **Coverage Board** | One line, state × rating path: which paths are verified, internal-only, mismatched, stale, untested |
| **Trace Diff** | One scenario, ours vs ISO step by step: the first step where they part, classified |
| **Scenario Workbench** | Rate one scenario free, or spend one call (reusing a stored answer when one exists) |
| **Test Plan Builder** | Choose dimensions from ISO's catalog; pairwise + edges; projected calls before committing |
| **Regression Library** | Every verified scenario re-run on each build at no call cost; stale ones queued for refresh |
| **Queue & Run Log** | The daily call cap split into lanes, the dispatch order, every call logged |

## What we already have (and reuse rather than rebuild)

| Brief needs | Exists today | Gap |
|---|---|---|
| A store of ISO answers | `results/cf-raas/` (Property, 4,817 files: requests, responses, refusals), `results/runs-*.jsonl` (`scripts/runstore.py`, GL runs) | Two shapes, no index, no request hash, no content version, no staleness |
| Step-level ISO values | Property responses carry every intermediate field (rates, factors, sub-premiums) | GL: unconfirmed (TC-04) |
| Our step trace | `Interpreter.trace` + every data-tree field the rules write | A **worksheet map** aligning our nodes to ISO's fields by stable ID |
| Dimensions from ISO's catalog | `scripts/variants.py` (`Declared`, GL), `_state_inputs.py` (CP territories) | CP dimension catalog |
| Pairwise + edges | `scripts/qa.py` (`_allpairs`, tiers T0-T3, cost estimate) | Wired to the builder and queue |
| Call budget | `qa.py` decision A6: 60 standing / 150 ceiling per day | **D2: cap 250, lanes 150 / 50 / 50**, replacing A6 |
| Content versions | Package ids per state and date (`book_for`), `iso_packages.json` (C28-19) | Stamp every stored answer; mark stale on ingest |
| Reference results by state | CP: 293 ISO fixtures, the app sample in 46 states, chunk 1-28 probes; GL: QA tiers and runs | Rolled up into paths and coverages |

## The user's decisions (2026-10-06, TC-01)

| # | Decision | The user's answer |
|---|---|---|
| D1 | Which pages go | **Remove `/tester`, `/tests` and `/review`** (RC-6, after the parity check); **keep `/`** until the Scenario Workbench does everything it does, then fold it in |
| D2 | RaaS budget | **The brief's numbers: cap 250 calls a day, lanes 150 active plans / 50 change & stale refresh / 50 ad hoc & triage.** Replaces decision A6 (60 standing / 150 ceiling) |
| D3 | Waves | **No waves**: every state in one flat list, alphabetical; the brief's wave grouping, wave filters and wave sort keys are dropped |
| D4 | Sign-off | **Optional**: Passed is derived; a person may sign a cell off (name, date); the sign-off clears itself if the cell leaves Passed; go/no-go shows both |
| D5 | Cells that don't apply | **"n/a" cell** (grey, its own glyph) where the state files no such path, never counted as a gap; **descoped** paths listed with their reason in the cell's side panel |
| D6 | Where it lives | **The local app** (`start.bat`, the packaged Windows app), **plus read-only snapshots of every screen on Ideation** (Matrix, Board, Library, Run Log; Trace Diffs as static pages per scenario) |
| D7 | Look | **The prototype's design, offline**: its layout, colours and type in one stylesheet, fonts bundled or replaced by system fonts, no external libraries |

## Ground rules (every RC)

* **Nothing in the console decides rating.** It reads the engine, the store and ISO; the premium and agreement have
  one owner each (the engine; the comparison function), as `ui/` does today.
* **No screen spends a call by accident.** Only a committed plan, the Workbench's "Send to RaaS", and "Queue refresh"
  spend; each shows the count first and checks the store for a reusable answer.
* **Every RC ends working.** The app starts, rates, and the old pages still work until RC-6.
* **Each RC is gated** by its own tests plus the engine's quick regression (`104_ --quick`); RC-7 runs the full gate.

---

## Milestone 1: the foundations (no screens)

### RC-0 · Decisions and discovery (5 tasks) · 1 of 5 done

| # | Task | Status | Notes |
|---|---|---|---|
| TC-01 | **Decisions D1-D7** recorded, with dates | ✅ 2026-10-06 | The user's, one at a time (above) |
| TC-02 | **Inventory of the old pages**: every job `/tester`, `/tests`, `/review` and `/` do, each mapped to the console screen that will do it (the parity list RC-6 is gated on) | ⬜ | |
| TC-03 | **The cap in practice** (D2: 250 = 150 / 50 / 50): whether errors are charged (the brief assumes a 504 is) and when the day resets, so the ledger counts calls as ISO does | ⬜ | |
| TC-04 | **GL step values**: does a GL RaaS response carry intermediate steps the way Property's does? If not, Trace Diff for GL compares only what ISO returns | ⬜ | Decides Trace Diff's GL scope |
| TC-05 | **Path catalog census**: every rating path per (line, state, coverage) the engine can walk, from the ERC rules; the denominator the matrix needs | ⬜ | Like the chunk censuses |

### RC-1 · The data layer (8 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| TC-06 | **Reference store**: one index over every stored ISO answer, both lines: request hash, line, state, effective date, package and content version, ISO's outcome, stored date. Built from `results/cf-raas/` and the GL run store; nothing moved on disk | ⬜ | Dedupe key = request hash |
| TC-07 | **Staleness**: a reference is stale when the package in force for its state and date changes (`book_for`, `iso_packages.json`), so a corpus refresh (C28-20) marks exactly the answers it affects | ⬜ | |
| TC-08 | **Status vocabulary**: the five states (verified, internal, mismatch, stale, untested) with fixed keys, glyphs and colours, one module every screen imports | ⬜ | |
| TC-09 | **Coverage → path mapping** as versioned configuration (GL 5 coverages, CP 6), per §4 of the spec; states with no such path read "n/a" (D5) | ⬜ | |
| TC-10 | **Path signature**: which paths one scenario walks, from the engine's own trace (records attached, forms priced, tables reached) | ⬜ | Ties a stored answer to the paths it proves |
| TC-11 | **Mismatch taxonomy and classifications**: rounding ±$1, interpolation ±0.5%, version skew, input mapping, RaaS anomaly, true engine defect (zero); stored per scenario | ⬜ | |
| TC-12 | **Call ledger and lanes** (D2): every call logged with lane, outcome and cost; cap 250, lanes 150 / 50 / 50 enforced in one place, replacing `qa.py`'s budget guard (A6) | ⬜ | |
| TC-13 | **Roll-up**: path → coverage → cell status by §3's order (mismatch, stale, untested, verified, internal), n/a where no path is filed (D5); optional sign-off kept and cleared (D4); estimated calls to finish (§6). Tests for each rule | ⬜ | |

**Gate RC-1:** the store indexes every stored ISO answer and matches today's counts (e.g. CP's 293 fixtures, 46-state
sample); a test per roll-up rule; `104_ --quick` clean.

---

## Milestone 2: the go/no-go views

### RC-2 · Readiness Matrix and Coverage Board (6 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| TC-14 | **Console shell**: the seven-tab frame, the call-cap strip (used / left / queued / resets), the shared legend; D7's look | ⬜ | |
| TC-15 | **`GET /api/console/readiness`** per §5: cells, columns, cap; recomputed on store, classification, ingest and build events | ⬜ | |
| TC-16 | **Readiness Matrix** screen: every state, alphabetical (D3), both lines, totals strip (§8), cell select / double-click (§7), n/a cells (D5), sign-off (D4) | ⬜ | |
| TC-17 | **"Still to test" list**: §6's sort without the wave key (status priority, then calls), needs text and call estimate; days to finish at the active lane (150/day) | ⬜ | |
| TC-18 | **Coverage Board**: one line, state × path, readiness verdict per state (Go / Hold / Not ready), side panel of scenarios per cell | ⬜ | |
| TC-19 | **Seeded from real evidence**: CP from the chunk 1-28 work and the app's 46-state sample; GL from the QA runs. Every Passed cell traceable to its stored answers | ⬜ | No new calls |

**Gate RC-2:** the matrix and board render from real data in both lines; spot-checks (e.g. CP Building in OH) trace to
stored answers; no screen spends a call.

---

## Milestone 3: seeing why

### RC-3 · Trace Diff and Scenario Workbench (6 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| TC-20 | **Worksheet map**: our engine's nodes (data-tree fields and the rules that write them) aligned to ISO's response fields by stable ID, per line; versioned | ⬜ | TC-04 sets GL's depth |
| TC-21 | **Trace Diff**: ours vs ISO row by row, matching subtrees collapsed, the first divergent step marked and downstream rows tagged "flows from"; each row's ERC source (rule, table, circular) | ⬜ | |
| TC-22 | **Classify a mismatch** from Trace Diff (TC-11's taxonomy), with a note; the cell's status follows | ⬜ | |
| TC-23 | **Scenario Workbench**: the inputs per line, "Rate internally" (free), "Send to RaaS" (one call); the dedupe dialog when a stored answer exists | ⬜ | Supersedes `/`'s job (D1) |
| TC-24 | **Promote to Regression Library** from the Workbench or Trace Diff | ⬜ | |
| TC-25 | **Proof**: a known past mismatch replayed (e.g. OI-133's FL cyber case before its fix) shows its first divergence at the right step | ⬜ | |

**Gate RC-3:** Trace Diff on 10 stored scenarios per line, every row aligned; the Workbench rates and reuses stored
answers without a call.

---

## Milestone 4: planning and spending calls

### RC-4 · Test Plan Builder and Queue & Run Log (7 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| TC-26 | **Dimension catalog** from ISO's own files: GL from `variants.Declared`; CP from its domains and state inputs (`_state_inputs`) | ⬜ | |
| TC-27 | **Test Plan Builder**: line, states (no waves, D3), dimension chips; live counters (cartesian, Tier 0, pairwise, edges, already verified, projected calls and days) | ⬜ | Reuses `qa._allpairs` |
| TC-28 | **Tier 0 invariants** (zero calls): premium rises with limits, deductibles never raise premium, minimum premium floors hold, no null steps, every valid state / class resolves | ⬜ | From `qa.py` T0 |
| TC-29 | **Commit a plan** → queue, with the confirmation dialog (calls, lane, ETA, dedupe); prefilled from the Matrix's "Build a test plan from these gaps" | ⬜ | |
| TC-30 | **Dispatcher**: ordered by information value (untested path, changed content, edge, stale, pairwise), within lanes and the daily cap; dedupe against the store before every call | ⬜ | |
| TC-31 | **Queue & Run Log** screen: lanes, dispatch queue, the run log (sent, match, mismatch, dedupe hit, error, override, reset) | ⬜ | |
| TC-32 | **Override** of the cap: needs a reason, is logged | ⬜ | |

**Gate RC-4:** a small real plan (e.g. one CP coverage in one state) committed, dispatched within its lane,
every call in the log, results in the store, the matrix updated.

---

## Milestone 5: keeping it true

### RC-5 · Regression Library (3 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| TC-33 | **Regression Library**: every promoted scenario with its reference, content version, verified date, last build result; filters | ⬜ | Seeded with the 293 ISO fixtures and the chunk golden cases |
| TC-34 | **Re-run on build** at zero calls: ours against each stored reference; divergences flagged | ⬜ | Same comparison as `157_` |
| TC-35 | **Stale refresh**: stale references listed and queued into the refresh lane | ⬜ | |

**Gate RC-5:** the library re-runs at zero calls with today's results (e.g. 293 of 293 CP fixtures pass); a corpus
change marks exactly the affected references stale.

---

## Milestone 6: the switch-over

### RC-6 · Retire the old testing pages (2 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| TC-36 | **Parity check** against TC-02's list: every job the old pages did, done in the console (or dropped by the user's decision, recorded) | ⬜ | |
| TC-37 | **Remove** `/tester`, `/tests`, `/review` and their modules (`ui/tester.py`, `ui/tests_page.py`, `ui/review_page.py`, `ui/runfile.py` and what only they use); their tests retired or moved; the app's nav and `start.bat` point at the console; `/` per D1 | ⬜ | Run history kept on disk |

### RC-7 · Release (1 task)

| # | Task | Status | Notes |
|---|---|---|---|
| TC-38 | **Release gate**: full `104_ --gate`, the console's own tests, the packaged Windows app rebuilt and started clean, the status page, and **read-only snapshots of every screen published to Ideation** (D6), refreshed by the same push the status page uses | ⬜ | |

---

## Size and order

| Milestone | RCs | Tasks | Rough size |
|---|---|---|---|
| 1 Foundations | RC-0, RC-1 | 13 | L (the store and roll-up carry everything after) |
| 2 Go/no-go views | RC-2 | 6 | M |
| 3 Seeing why | RC-3 | 6 | L (the worksheet map) |
| 4 Planning and spending | RC-4 | 7 | M |
| 5 Keeping it true | RC-5 | 3 | S |
| 6 Switch-over | RC-6, RC-7 | 3 | S |

**Why this order.** The Readiness Matrix is only as honest as the store under it, so the store comes first; the views
that spend nothing (Matrix, Board) come before the ones that spend calls (Builder, Queue); the old pages go last,
after a parity check, so nothing is lost in between.

**Not in this plan:** blanket / multi-location property (the brief's "Phase 5"), GL endorsements (off in
the brief), and anything that changes a premium. An engine defect found through the console goes through the usual
route: an open item, a proposal, the user's go.
