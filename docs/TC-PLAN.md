# ISO Rating Test Console: the plan

**Status: IN PROGRESS 2026-10-07, 19 of 38 tasks.** RC-0 and RC-1 done (the data layer: `console/`); RC-2 done and gated: the console at `/console` with the Readiness Matrix, "Still to test" and the Coverage Board, seeded from real evidence (CP 155 of 281 cells Passed, GL 0 of 255). **Next: RC-3, Trace Diff and the Scenario Workbench (TC-20, the worksheet map, first).** **Open from TC-19:** GL 2027-04-01 rates about double what matched ISO on 2026-08-31 (7 of 7 rows); NY GL needs ISO's `V02` package. Progress at a glance: [`TC-TRACKER.html`](TC-TRACKER.html), rebuilt from this file on every edit.
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
| Step-level ISO values | Property responses carry every intermediate field (rates, factors, sub-premiums) | GL too: 276 step fields in a stored NJ response (TC-04) |
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
| D8 | GL "ILF interpolated" (TC-05) | **Renamed "Size of risk"**: the one interpolated GL lookup; n/a in the 16 states that don't offer it |
| D9 | GL minimum premium | **"Filed at $0", testable**: Passed means ours and ISO both apply the $0 minimum; from 2027-04-01 CA GA NJ NY WA file real minimums |
| D10 | GL per-claim deductibles | **"Filed at zero", testable**: Passed means both apply no credit |
| D11 | GL Cov B | **Kept: included / excluded**; passes when both are verified |
| D12 | GL paths the brief misses | **All tracked as paths**: ELP industry / company, split BI/PD limits, company LCM, the "other" bases, claims-made, governmental-units and stop-gap ILF, the 2027 medical-payments change |
| D13 | GL Prod/CO area and units | **Left out**: no state rates on them |
| D14 | Run controls (TC-02 T4, L5) | **Pause, resume, stop-and-keep** on committed plans; a stopped plan keeps its results and lists what it never reached |
| D15 | INERT and pass 3 (T5, T6, T9) | **Keep both**: "exercised nothing" flags a scenario (it counts toward no path); "our refusal vs ISO's narrowing" is a **seventh mismatch category**; pass 3 runs after a plan finishes |
| D16 | Review tools (V2, V3, T9) | **Keep all three in Trace Diff**: "seen before" with the earlier classification, a copy-brief button; the refused-payload list in the Queue & Run Log |
| D17 | Run files (L7, L8, R7) | **Replaced by plan reports**: a shareable read-only report per committed plan, linked from the run log and published with D6's snapshots; existing run files stay browsable from the log |
| D18 | Trends (T10-T13, L9) | **Keep four**: agreement over time, defects first / last seen, response curves, the control × state grid |
| D19 | One config everywhere (T15, T16) | **In the Workbench**: "Check where it applies" (free) and "Run in every state" (shows the calls, then commits a one-config plan) |
| D20 | Plan options (L2, L3) | **Add all**: allowance thinning (never cuts states), reduced grid, basis-first class picker, multi-class, effective date as a dimension |
| D21 | Call ledger (R3, R6) | **Every call, wherever it starts**: one ledger inside the RaaS client (`scripts/raas.py`); the console, `/`, the CLIs and the chunk scripts all count toward 250, tagged by origin; every answer lands in the reference store |
| D22 | `/`'s mode, rounding and free batch (R2, R6) | **Brought to the console**: mode and rounding in the Workbench; the all-samples check as a zero-call Regression Library run |

## Ground rules (every RC)

* **Nothing in the console decides rating.** It reads the engine, the store and ISO; the premium and agreement have
  one owner each (the engine; the comparison function), as `ui/` does today.
* **No screen spends a call by accident.** Only a committed plan, the Workbench's "Send to RaaS", and "Queue refresh"
  spend; each shows the count first and checks the store for a reusable answer.
* **Every RC ends working.** The app starts, rates, and the old pages still work until RC-6.
* **Each RC is gated** by its own tests plus the engine's quick regression (`104_ --quick`); RC-7 runs the full gate.

---

## Milestone 1: the foundations (no screens)

### RC-0 · Decisions and discovery (5 tasks) · 5 of 5 done

| # | Task | Status | Notes |
|---|---|---|---|
| TC-01 | **Decisions D1-D7** recorded, with dates | ✅ 2026-10-06 | The user's, one at a time (above) |
| TC-02 | **Inventory of the old pages**: every job `/tester`, `/tests`, `/review` and `/` do, each mapped to the console screen that will do it (the parity list RC-6 is gated on) | ✅ 2026-10-06 | [`TC-02-PARITY.md`](TC-02-PARITY.md): 36 jobs; 9 the plan doesn't cover yet, each the user's call before RC-6 |
| TC-03 | **The cap in practice** (D2: 250 = 150 / 50 / 50): whether errors are charged (the brief assumes a 504 is) and when the day resets, so the ledger counts calls as ISO does | ✅ 2026-10-06 | The old 60 / 150 (A6) was our own budget, not ISO's; ISO's API console states no quota; the PDF is unreadable here. **Ledger rule: every request sent counts as one call, refusals and errors included** (931 failed calls on record, almost all 400s with a body); the day resets at 00:00 ET. Open for ISO: the real limit, and whether errors are charged |
| TC-04 | **GL step values**: does a GL RaaS response carry intermediate steps the way Property's does? If not, Trace Diff for GL compares only what ISO returns | ✅ 2026-10-06 | **Yes**: a stored NJ GL response carries 1,203 values in 276 fields, every step (`BaseRate`, `ILF`, `FinalILF`, `DeductibleFactor`, `FinalRate`, `BasicLimitPremium`, `CoveragePremium`, the experience-rating factors). Trace Diff goes step by step for both lines |
| TC-05 | **Path catalog census**: every rating path per (line, state, coverage) the engine can walk, from the ERC rules; the denominator the matrix needs | ✅ 2026-10-06 | [`TC-05-PATHS.md`](TC-05-PATHS.md): CP 17 paths in 6 coverages (n/a: BCEG in NY, DC; PR); GL ~35 paths in 5 coverages across 51 jurisdictions (n/a: size of risk in 16, state exceptions where none filed). **Six places the brief's GL columns don't match ISO's content**, the user's calls before TC-09 |

### RC-1 · The data layer (8 tasks) · 8 of 8 done, gated 2026-10-06

| # | Task | Status | Notes |
|---|---|---|---|
| TC-06 | **Reference store**: one index over every stored ISO answer, both lines: request hash, line, state, effective date, package and content version, ISO's outcome, stored date. Built from `results/cf-raas/` and the GL run store; nothing moved on disk; **every new answer from any origin added as it arrives (D21)** | ✅ 2026-10-06 | `console/store.py`: **2,935 references** (2,384 CP rated, 549 CP refused, 2 GL refused) + **1,060 GL premium-level rows** from the run store. The 293 ISO fixtures are 207 distinct requests, each rebuilt from ISO's STC file; 344 more answers kept without their request are indexed by state, date and package (`request_kept: false`). GL has no stored request/response bodies yet: they accrue from now on (D21) |
| TC-07 | **Staleness**: a reference is stale when the package in force for its state and date changes (`book_for`, `iso_packages.json`), so a corpus refresh (C28-20) marks exactly the answers it affects | ✅ 2026-10-06 | `store.staleness`: stale when ISO answered on a package other than the one our corpus resolves now. Today 2,815 fresh, 0 stale, 120 unknown (refusals naming no state package) |
| TC-08 | **Status vocabulary**: the five states (verified, internal, mismatch, stale, untested) with fixed keys, glyphs and colours, one module every screen imports | ✅ 2026-10-06 | `console/status.py`: five states plus n/a, fixed keys, glyphs, colours; §6 priority and needs text |
| TC-09 | **Coverage → path mapping** as versioned configuration (GL 5 coverages, CP 6), per §4 of the spec; states with no such path read "n/a" (D5) | ✅ 2026-10-06 | `console/config/paths.json` (built by `scripts/tc/tc09_build_paths.py` from TC-05 and D8-D13), read through `console/paths.py`: CP 17 paths × 47 states (11 n/a), GL 43 paths × 51 (128 n/a) |
| TC-10 | **Path signature**: which paths one scenario walks, from the engine's own trace (records attached, forms priced, tables reached) | ✅ 2026-10-06 | `console/signature.py`: CP from the rated tree (forms that priced, inputs read), GL from the trace (writes and lookups). Across all 51 GL samples no path is walked where the census says n/a |
| TC-11 | **Mismatch taxonomy and classifications**: rounding ±$1, interpolation ±0.5%, version skew, input mapping, RaaS anomaly, true engine defect (zero), **and our refusal vs ISO's narrowing (D15)**; the **INERT** flag (a scenario that exercised nothing counts toward no path); stored per scenario | ✅ 2026-10-06 | `console/mismatch.py`: 7 categories (D15's refusal vs narrowing added), tolerance bands, the INERT flag, append-only classifications |
| TC-12 | **Call ledger and lanes** (D2, D21): **inside the RaaS client**, so every call counts wherever it starts (console, `/`, CLIs, `scripts/cf`), tagged by origin, with lane, outcome and cost; cap 250, lanes 150 / 50 / 50 enforced in one place, replacing `qa.py`'s budget guard (A6) | ✅ 2026-10-06 | `console/ledger.py` **inside the RaaS client** (`scripts/raas.py`): every call admitted against its lane (250 = 150 / 50 / 50), recorded with origin and outcome, its answer saved to the store; a full lane needs an override with a reason. **Live from 2026-10-06** (first call: OH sample, $5,204 = ISO) |
| TC-13 | **Roll-up**: path → coverage → cell status by §3's order (mismatch, stale, untested, verified, internal), n/a where no path is filed (D5); optional sign-off kept and cleared (D4); estimated calls to finish (§6). Tests for each rule | ✅ 2026-10-06 | `console/rollup.py`: path states from scenarios, cells by §3's order, n/a, descoped, sign-off kept only while Passed, §6 still-to-test order and call estimates |

**Gate RC-1 (passed 2026-10-06: `tests/verify_console_rc1.py` 50 of 50, `104_ --quick` clean, one live call through the ledger):** the store indexes every stored ISO answer and matches today's counts (e.g. CP's 293 fixtures, 46-state
sample); a test per roll-up rule; `104_ --quick` clean.

---

## Milestone 2: the go/no-go views

### RC-2 · Readiness Matrix and Coverage Board (6 tasks) · 6 of 6 done, gated 2026-10-07

| # | Task | Status | Notes |
|---|---|---|---|
| TC-14 | **Console shell**: the seven-tab frame, the call-cap strip (used / left / queued / resets), the shared legend; D7's look | ✅ 2026-10-07 | `ui/console_page.py` at `/console`, mounted through `ui.tester`; the cap strip reads the ledger (`/api/console/cap`, refreshed every 30 s), the legend reads `console.status`; the prototype's palette and type, system-serif fallbacks, nothing fetched. Screens not yet built name the task that builds them. `tests/verify_console_rc2.py` A1-A10 |
| TC-15 | **`GET /api/console/readiness`** per §5: cells, columns, cap; recomputed on store, classification, ingest and build events | ✅ 2026-10-07 | `console/readiness.py`: §5's cells (no wave, D3; n/a, D5; per-path states, open mismatches with category and delta, content version in force, sign-off) plus §8's totals. Evidence is a new append-only `results/tc/evidence.jsonl` (`console/evidence.py`): what each scenario walked and both premiums, with agreement and freshness worked out when the matrix is computed, so a classification or a corpus refresh moves cells without rewriting it. **Recompute = any input file changes** (reference index, classifications, evidence, sign-offs, `config/descoped.json`, `paths.json`, a build marker) or the day turns; otherwise served from `results/tc/readiness.json` (cold 31 s, cached 0.02 s). Today: 536 cells, all untested until TC-19 seeds the evidence. `?lob=`, `?state=`, `?refresh=1`. Tests B1-B22 |
| TC-16 | **Readiness Matrix** screen: every state, alphabetical (D3), both lines, totals strip (§8), cell select / double-click (§7), n/a cells (D5), sign-off (D4), **agreement over time (D18)** | ✅ 2026-10-07 | The Matrix tab of `/console` (`ui/console_page.py`): every state alphabetical, GL then CP, a Passed count per row; §8's totals strip; agreement with ISO over time per line (latest record per scenario as of each day, today's classifications; hover for counts); click opens the side panel (needs, calls, every path's state, open mismatches, descoped, content version), double-click opens the Coverage Board for that line, state and coverage; n/a cells grey. Sign-off (D4) through `POST /api/console/signoff`: only on a Passed cell, an empty name withdraws it. A recompute now carries the day's content versions over (same day, path config and index), so a sign-off or classification is reflected in under 0.1 s. Checked in the browser against synthetic evidence. Tests C1-C11 |
| TC-17 | **"Still to test" list**: §6's sort without the wave key (status priority, then calls), needs text and call estimate; days to finish at the active lane (150/day) | ✅ 2026-10-07 | `readiness.still_to_test`, sent as `stillToTest` and filtered with the cells; shown in the Matrix side panel whenever no cell is selected (first 14, "Show all"), each row selecting its cell. Footer: calls to finish, days at 150/day, stale refreshes apart at 50/day; "Build a test plan from these gaps" opens the Test Plan Builder tab (prefill lands with TC-29). **Estimates corrected to §6**: a stale cell costs one call per stale reference and a mismatched one per open mismatch, not per path (the demo's stale refreshes went from 102 calls to 21). The saved result carries a format version so older shapes are rebuilt. A page-script syntax check (node `--check`) added after a quoting slip blanked the page. Tests D1-D11, A11 |
| TC-18 | **Coverage Board**: one line, state × path, readiness verdict per state (Go / Hold / Not ready), side panel of scenarios per cell; **the control × state grid beside it (D18)** | ✅ 2026-10-07 | The Board tab of `/console` with `console/board.py`: one line at a time, states × every path (GL 43, CP 17) grouped under the most specific coverage they count toward, so GL's deductible paths sit under Deductibles; each cell's number is its scenarios (affected / all for mismatch and stale); n/a and descoped marked. **Verdict per state** (the prototype's rule): Go = every applicable path verified; Hold = a mismatch, a stale reference, or verified part-way; Not ready = nothing verified; pinned beside the state so it never scrolls away. Summary: path coverage, verified share, open mismatches by category, days left, verdict counts. Click a state for its counts, a cell for its scenarios (`/api/console/board/cell`, mismatch first, with Δ and category). Opened from the Matrix with that line, state and coverage highlighted. **Control × state grid**: GL's 23 controls × 51 states from the run store (the `/tester` grid, T11), 18 rated somewhere today; CP's waits for its catalog (TC-26). Path states come from the readiness result, so board and matrix cannot disagree. Tests E1-E18 |
| TC-19 | **Seeded from real evidence**: CP from the chunk 1-28 work and the app's 46-state sample; GL from the QA runs. Every Passed cell traceable to its stored answers | ✅ 2026-10-07 | `scripts/tc/tc19_seed_evidence.py`, **0 calls**: every stored answer re-rated on today's engine (7 workers, ~8 min). **CP**: 2,041 rated answers (incl. ISO's STC fixtures rebuilt as `157_` sends them), every premium field compared: 1,940 of 1,941 agree; the one that differs is OI-116 (FL `chunk21_rc2_FC5`, known, a question to ISO); 100 older probes our engine now refuses by design (no Group II territory, C28-17/18) add no paths; 344 answers kept without a request and 549 refusals add none. **GL**: 956 QA-run rows (latest per config, state, date): 949 agree; **all 7 that differ are 2027-04-01 rows (3 configs, 6 states) that matched ISO on 2026-08-31 and rate about double today** (TX 7,740 vs ISO 895, same packages): a change in GL 2027-04-01 rating since then, not yet traced. GL rows now carry their ISO package, so they get real staleness (22 NY rows stale: ISO answers on `GL_NY_20260801_V02`, our corpus holds V01 only); judged on each row's own date. Records dated with the answer's date, so agreement over time is history. **Today: CP 155 of 281 Passed; GL 0 of 255** (500 of 2,065 GL paths verified, but no coverage has every path: the QA runs vary the common paths, D12 keeps all of them in scope). Every Passed cell traces to answers on disk (F9). Tests F1-F10 |

**Gate RC-2 (passed 2026-10-07: `tests/verify_console_rc2.py` 84 of 84, `verify_console_rc1.py` 50 of 50,
`verify_tester.py` 81 of 81, `104_ --quick` clean, 34 scripts in 5m41s, log `results/tc/rc2_gate_104_quick.log`):** the matrix and board render from real data in both lines; spot-checks (e.g. CP Building in OH) trace to
stored answers; no screen spends a call. (The quick tier runs no GL suites, so it says nothing about TC-19's GL
2027-04-01 finding; the full `104_` at RC-7, or sooner if that finding is opened, does.)

---

## Milestone 3: seeing why

### RC-3 · Trace Diff and Scenario Workbench (6 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| TC-20 | **Worksheet map**: our engine's nodes (data-tree fields and the rules that write them) aligned to ISO's response fields by stable ID, per line; versioned | ⬜ | TC-04 sets GL's depth |
| TC-21 | **Trace Diff**: ours vs ISO row by row, matching subtrees collapsed, the first divergent step marked and downstream rows tagged "flows from"; each row's ERC source (rule, table, circular); **"seen before" with the earlier classification, and a copy-brief button (D16)** | ⬜ | |
| TC-22 | **Classify a mismatch** from Trace Diff (TC-11's taxonomy), with a note; the cell's status follows | ⬜ | |
| TC-23 | **Scenario Workbench**: the inputs per line, **mode and rounding (D22)**, "Rate internally" (free), "Send to RaaS" (one call); the dedupe dialog when a stored answer exists; **"Check where it applies" and "Run in every state" (D19)**; **response curves (D18)** | ⬜ | Supersedes `/`'s job (D1) |
| TC-24 | **Promote to Regression Library** from the Workbench or Trace Diff | ⬜ | |
| TC-25 | **Proof**: a known past mismatch replayed (e.g. OI-133's FL cyber case before its fix) shows its first divergence at the right step | ⬜ | |

**Gate RC-3:** Trace Diff on 10 stored scenarios per line, every row aligned; the Workbench rates and reuses stored
answers without a call.

---

## Milestone 4: planning and spending calls

### RC-4 · Test Plan Builder and Queue & Run Log (7 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| TC-26 | **Dimension catalog** from ISO's own files: GL from `variants.Declared`; CP from its domains and state inputs (`_state_inputs`); **basis-first class picker, multi-class, effective date with the package dates (D20)** | ⬜ | |
| TC-27 | **Test Plan Builder**: line, states (no waves, D3), dimension chips, **allowance thinning (never cuts states) and a reduced grid (D20)**; live counters (cartesian, Tier 0, pairwise, edges, already verified, projected calls and days) | ⬜ | Reuses `qa._allpairs` |
| TC-28 | **Tier 0 invariants** (zero calls): premium rises with limits, deductibles never raise premium, minimum premium floors hold, no null steps, every valid state / class resolves | ⬜ | New work: `qa.py`'s T0 is a live smoke run, not an invariant tier (TC-02) |
| TC-29 | **Commit a plan** → queue, with the confirmation dialog (calls, lane, ETA, dedupe); prefilled from the Matrix's "Build a test plan from these gaps" | ⬜ | |
| TC-30 | **Dispatcher**: ordered by information value (untested path, changed content, edge, stale, pairwise), within lanes and the daily cap; dedupe against the store before every call; **pass 3 after each plan (D15)** | ⬜ | |
| TC-31 | **Queue & Run Log** screen: lanes, dispatch queue, the run log (sent, match, mismatch, dedupe hit, error, override, reset); **pause / resume / stop-and-keep (D14)**; **the refused-payload list (D16)**; **a shareable report per plan, existing run files browsable (D17)** | ⬜ | |
| TC-32 | **Override** of the cap: needs a reason, is logged | ⬜ | |

**Gate RC-4:** a small real plan (e.g. one CP coverage in one state) committed, dispatched within its lane,
every call in the log, results in the store, the matrix updated.

---

## Milestone 5: keeping it true

### RC-5 · Regression Library (3 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| TC-33 | **Regression Library**: every promoted scenario with its reference, content version, verified date, last build result; filters; **defects with first and last seen (D18)** | ⬜ | Seeded with the 293 ISO fixtures and the chunk golden cases |
| TC-34 | **Re-run on build** at zero calls: ours against each stored reference; divergences flagged; **the free all-samples check from `/` (D22)** | ⬜ | Same comparison as `157_` |
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
