# TC-36: parity check before retiring `/tester`, `/tests` and `/review`

**Done 2026-10-07.** Every job in TC-02's list (`TC-02-PARITY.md`, 36 jobs), checked against the console as built, not
as planned. RC-6 removes the pages only when each row is **done** in the console or **kept** where it is by the user's
decision (D1 keeps `/`). Six gaps were found by this check and closed in it (marked **closed in TC-36**).

Screens: **RM** Readiness Matrix · **CB** Coverage Board · **TD** Trace Diff · **SW** Scenario Workbench ·
**TPB** Test Plan Builder · **RL** Regression Library · **Q&L** Queue & Run Log.

## `/` (stays, D1: folded into the Workbench only when it does all of `/`'s job)

| # | Job | Status | Where now |
|---|---|---|---|
| R1 | Pick a line and a state, load the sample, paste or edit the submission | kept on `/`; **partly in SW** | SW: GL from ISO's dropdowns, CP's request editable. Pasting an arbitrary GL submission is still `/`'s alone: why `/` stays |
| R2 | Rate one submission with mode and rounding | done | SW "Rate internally", mode and rounding (D22) |
| R3 | Compare with ISO live | done | SW "Send to RaaS" through the ledger (D21), dedupe first; `/`'s own calls are ledgered too (TC-12) |
| R4 | Result views: chain, steps with sources, premiums, CP grid with ISO cells | done | TD (every field, its rule file and package), SW |
| R5 | Deep links | done | console hashes: `#trace?scenario=`, `#board?lob&state&coverage`, `#plan?lob&states&coverages`, `#queue?plan=` |
| R6 | "Test every jurisdiction": all samples, engine-only or vs ISO | done | RL: the 97 samples, re-run free (D22); live through TPB + Q&L |
| R7 | "Run files" link to `/runs/index.html` | **closed in TC-36** | the console now serves `/runs/...` (read-only), so `/`'s link keeps working after `/tests` goes; linked from Q&L |

## `/tester`

| # | Job | Status | Where now |
|---|---|---|---|
| T1 | QA tiers T0-T4 with cost, core states, budget | **closed in TC-36** | TPB "Start from": QA T0, T1, T2, T4 from `qa.py` (its core states and pairwise + paired configs); cost in the counters; budget in the cap strip |
| T2 | Preview a tier without running it | done | TPB counters |
| T3 | Run a tier live or offline; force over budget, labelled | done | Commit rates every scenario on our engine (offline); start dispatches live; override (TC-32) |
| T4 | Pause, resume, stop and keep | done | Q&L (D14) |
| T5 | Live findings: disagrees, INERT VALUE, run failed | **closed in TC-36** | Q&L run log; a scenario that rates as the base risk through the same paths is flagged at commit, logged `inert`, and its evidence counts toward no path (D15) |
| T6 | Pass 3 automatically after a tier | done | dispatcher, after every GL plan (D15) |
| T7 | QA summary: verdict bar and map | done | RM totals and rows, CB verdicts per state |
| T8 | What changed since the last run | **closed in TC-36** | RL "Since the previous run": fixed, newly failing, still failing, newly refusing, our premium moved |
| T9 | Review findings: pass 3, pass-4 briefs, refused payloads | done | plan report (pass 3), TD copy brief, Q&L refused payloads (D16) |
| T10 | Agreement over time | done | RM trend (D18) |
| T11 | Control × jurisdiction coverage grid | done | CB, beside the board (D18) |
| T12 | Response curve per control | done | SW (D18) |
| T13 | Defects first and last seen | done | RL (D18) |
| T14 | A risk from ISO's dropdowns (keyed domains, date, multi-class) | done | SW + TPB catalog (TC-26, D20) |
| T15 | Check where one config applies | done | SW (D19) |
| T16 | One config across all 51 states, cost first | **closed in TC-36** | SW "Run in every state" (free) → "Build a plan from this" prefills TPB with that config in every state it applies → commit (D19) |

## `/tests`

| # | Job | Status | Where now |
|---|---|---|---|
| L1 | Pick a layer | **closed in TC-36** | TPB "Start from": layers L1 smoke, L3 limits (full and reduced, positions resolved per state as `/tests` did), L4 deductibles; L2's class layer is TPB's basis-first class dimension |
| L2 | Class basis-first, exposure | done | TPB / SW (D20) |
| L3 | Allowance thinning, full or reduced grid | done | TPB (D20) |
| L4 | Run, live rows, spend | done | TPB commit → Q&L (refreshes every 5 s), cap strip |
| L5 | Pause, resume, stop and keep | done | Q&L (D14) |
| L6 | Result bars, map, what changed | done | Q&L plan bars, RM / CB, RL changes |
| L7 | A shareable HTML run file plus index | done | plan reports `/console/report/<plan>` (D17); the old files still served |
| L8 | Open, filter, page through run files | **closed in TC-36** | Q&L: the standalone files (`/runs/index.html`) and every run in the run store, click for its rows |
| L9 | All-time aggregate per layer, trend | done | RM totals and agreement trend; CB |

## `/review/<run-file>`

| # | Job | Status | Where now |
|---|---|---|---|
| V1 | One run's findings and status | done | Q&L run rows, plan report; TD per scenario |
| V2 | "Seen before" with the earlier analysis | done | TD (D16) |
| V3 | Copy a markdown review brief | done | TD "Copy brief" (D16) |
| V4 | A reviewer's note | done | TD classify with a note (TC-22) |

## Result

**36 of 36 have a home:** 35 in the console, R1 kept on `/` (D1), with the Workbench covering it except pasting an
arbitrary GL submission. Nothing in the three pages is left without a place. TC-37 may remove them.

What goes in TC-37 (from TC-02, re-checked against the code today):

* **Pages and their modules:** `ui/tester.py`, `ui/tests_page.py`, `ui/review_page.py`, `ui/runfile.py`,
  `scripts/reviews.py`. **Kept:** `ui/variables.py` (the Workbench and the GL catalog use it), `ui/charts.py`
  (notebook 06 and a test), `ui/cache/`.
* **The mount:** `app.py` hands requests to `ui.tester.dispatch`, which also carries the console's routes today; the
  console gets its own mount, and `/`'s nav points at `/console`.
* **Tests:** `tests/verify_tester.py` (the pages) retires; its checks of what survives (the `ui → engine` direction,
  `variants`, `runstore`) move to a console test. `verify_layers.py` E (the run-file writer) retires with `runfile`.
* **Kept on disk:** the run store (`results/runs-*.jsonl`) and the 80 standalone run files (`results/runs/`), served
  read-only by the console.
