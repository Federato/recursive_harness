# TC-02: what the old testing pages do (the parity list RC-6 is gated on)

**Done 2026-10-06.** Every user-visible job on the three pages being retired (D1: `/tester`, `/tests`, `/review`) and
on `/` (which stays for now), each mapped to the console screen that takes it over. RC-6 removes the pages only when
every row here has a home or the user has dropped it (TC-36). Read from the code, no change made.

Screens: **RM** Readiness Matrix · **CB** Coverage Board · **TD** Trace Diff · **SW** Scenario Workbench ·
**TPB** Test Plan Builder · **RL** Regression Library · **Q&L** Queue & Run Log.

**How they are wired.** `app.py` (`Handler._tester`) hands every request to `ui.tester.dispatch`, which tries
`tests_page.dispatch`, which tries `review_page.dispatch`. **All three pages are General Liability only**; Property
testing exists only on `/`.

## `/` (stays, D1)

| # | Job | Where | Console home |
|---|---|---|---|
| R1 | Pick a line and a state, load the sample, paste or edit the submission | `/api/samples`, `/api/sample/<j>` | SW |
| R2 | Rate one submission, choosing mode (strict-erc / underwriting) and rounding | POST `/api/rate` | SW "Rate internally" (**mode and rounding not yet in TC-23**) |
| R3 | Compare with ISO live (premium, delta, edition, messages) | `compare_with_iso` | SW "Send to RaaS" (**its calls are not logged to the run store today**) |
| R4 | Result views: chain, all steps with sources, premiums, referrals, everything; CP coverage grid with ISO cells | page script | SW + TD |
| R5 | Deep links `?line&sample&mode&compare&rate` | page script | SW |
| R6 | "Test every jurisdiction": all samples, engine-only or vs ISO, PASS / FAIL table | `/api/batch` | RL (free re-run) / TPB + Q&L (live) (**live calls not logged**) |
| R7 | "Run files" link to `/runs/index.html` | served by `tests_page` | **breaks when `/tests` goes** |

## `/tester` (variable tester and QA tab)

| # | Job | Console home |
|---|---|---|
| T1 | QA tiers T0-T4 with cost, core states, today's budget | TPB (tiers) + cap strip (TC-14) |
| T2 | Preview a tier's scenario matrix without running it | TPB counters (TC-27) |
| T3 | Run a tier live or offline with a budget check; force over budget, labelled | TPB commit (TC-29) + dispatcher (TC-30) + override (TC-32) |
| T4 | Pause, resume, or stop a run and keep the partial | Q&L (**not in TC-31**) |
| T5 | Live findings: disagrees, "exercised nothing" (INERT VALUE), run failed | Q&L log (partial; **INERT not in TC-11**) |
| T6 | Run the pass-3 review automatically after a tier | **no home** |
| T7 | QA summary: verdict bar and US tile map per tier | RM / CB |
| T8 | What changed since the last run: new, fixed, still failing, newly refusing, premium changed, newly covered | RL (TC-34, partial) |
| T9 | What the review found: pass-3 confirmed / contradicted not-applicables, pass-4 briefs, refused payloads | TD classify (partial) / **no home** |
| T10 | Agreement over time | **no home** |
| T11 | Coverage grid of control × jurisdiction | CB (by path, not by control) |
| T12 | Premium response curve per control | **no home** |
| T13 | Defect list with first and last seen | RL / CB mismatch (partial) |
| T14 | Build a risk from ISO-declared dropdowns (keyed domains, effective date, multi-class) | SW inputs (TC-23) + catalog (TC-26) |
| T15 | "Check where it applies": legality of one config per state | SW / TPB (**D5's n/a is per path, not per config**) |
| T16 | Run one config across all 51 states, cost warned first | TPB → Q&L (SW is single-scenario) |

## `/tests` (layered tests)

| # | Job | Console home |
|---|---|---|
| L1 | Pick a layer (smoke, class, limits, deductibles) | TPB dimensions |
| L2 | Pick a class basis-first, filter class codes, enter an exposure | TPB / SW |
| L3 | A call allowance that thins configurations (never states); full or reduced grid; offline only | TPB counters (**allowance and reduced grid not named**) |
| L4 | Run a layer, watch live rows, see the spend ticker | TPB commit → Q&L |
| L5 | Pause, resume, "stop and keep" (a partial naming the states never reached) | Q&L (**not in TC-31**) |
| L6 | Result bars, map, what changed since the last run of the layer and class | RL / RM |
| L7 | Write a standalone shareable HTML run file plus an index | **no home** (D6 snapshots are per screen) |
| L8 | Open, filter and page through run files with review tags | Q&L run log (partial) |
| L9 | All-time aggregate and verdict per layer, an aggregate trend | RM / CB (partial); trend **no home** |

## `/review/<run-file>`

| # | Job | Console home |
|---|---|---|
| V1 | One run's findings (differences, premium-only, refusals) and review status | TD |
| V2 | Pattern match: "seen before" with the earlier analysis, or ISO question vs local problem | TD / TC-11 (partial) |
| V3 | Generate and copy a markdown review brief | **no home** |
| V4 | Paste back a reviewer's note; clear it | TD classify + note (TC-22) |

## What retiring the pages touches

* **Dead with the pages:** `ui/tester.py`, `ui/tests_page.py`, `ui/review_page.py`, `ui/runfile.py`, `ui/variables.py`
  (and `ui/cache/`), `scripts/reviews.py`; `ui/charts.py` is dead in the app but used by notebook 06 and a test;
  `ui/__init__.py` and `app.py`'s mount need editing.
* **Survive** (command line, notebooks, tests, the console): `scripts/qa.py`, `qa_review.py`, `layers.py`, `sweep.py`,
  `runstore.py` (the source for TC-06), `variants.py` (TC-26).
* **Tests:** `tests/verify_tester.py` (751 lines, almost all about these pages) retires or moves with them;
  `verify_layers.py` E uses `runfile`; `verify_stage6.py` (the `/` page) degrades safely without `ui.tester`;
  `verify_notebooks.py` runs notebooks that import `ui.charts`. The full gate runs every `tests/verify_*.py`.
* None of these are imported by `gl_engine`, `scripts/cf`, `property_rating` or `/`.

## Not covered by the plan yet (the user's call per item, before RC-6)

1. **Pause / resume and stop-and-keep** on runs (T4, L5): add to TC-31?
2. **INERT VALUE** ("a control that changed nothing") and **pass 3's "our refusal vs ISO's narrowing"** (T5, T6, T9): a
   mismatch category for TC-11?
3. **Review briefs, "seen before" pattern match, the refused-payloads list** (V2, V3, T9): into Trace Diff, or drop?
4. **Standalone run files and their index** (L7, L8, and `/`'s "Run files" link R7): keep serving them, or drop?
5. **Agreement over time, response curves, control × state coverage, defects first / last seen, per-layer trend**
   (T10-T13, L9): which, if any, the console should show.
6. **One config across every state** (T16) and **legality per config** (T15).
7. **Allowance thinning, the reduced grid, class basis-first, multi-class and effective-date dimensions** (L2, L3): name
   them in TC-26 / TC-27.
8. **`/`'s live calls and `scripts/cf`'s never reach the run store** (R3, R6): TC-12's ledger must log every call path,
   not only the console's.
9. **`/`'s mode and rounding choice** (R2) and the free all-states batch (R6): add to TC-23.

Correction to the plan found here: TC-28's zero-call invariants are new work. `qa.py`'s T0 is a *live* smoke run of the
base risk in every state, not an invariant tier.
