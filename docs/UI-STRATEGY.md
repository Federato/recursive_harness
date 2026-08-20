# The test page and the layered programme

**Decided and built 18 August 2026.** This records what we settled and why, what was built, where the
build departed from the plan, and what measuring the data changed about the design.

The short version: **a new `/tests` page, a four-layer ladder of test cases, every run covering every
state, and one standalone HTML file per run that you can open, keep and send.** It runs.

---

# 1 · The ladder, and why that order

The programme covers the **Premises/Operations and Products/Completed Operations** sublines. Each
layer adds exactly one kind of variation, so a difference found at layer *n* is attributable to what
layer *n* introduced.

| | Layer | What varies | What a failure means |
|---|---|---|---|
| **L1** | **Smoke** | nothing — the base risk, unvaried | the engine is wrong before any variation is involved |
| **L2** | **Classification** | one class code and its exposure, in every state | we price a kind of business wrongly, everywhere or somewhere |
| **L3** | **Limits** | occurrence limit × general aggregate | the increased-limit factor table, or the key we read it with |
| **L4** | **Deductibles** | one amount, applied to each of the six slots in turn | a deductible slot that never reaches the calculation |

**L3 varies two things, not one, and that is deliberate.** ILF keying is one of the two top-ranked
failure modes in the backlog, and the aggregate is half of that key. Before this build the aggregate
was not an axis at all — it was derived from the occurrence limit and took whatever value ISO
declared first.

**L4 asks the cheapest question first: is any slot ignored?** One amount, six slots. Mapping a credit
curve before knowing every slot reaches the calculation is work in the wrong order. The amount ladder
and the combined-versus-separate exclusion are **L5** and **L6** when this ladder has been walked.

Run them:

```
python scripts/layers.py --layers
python scripts/layers.py --layer L2 --class 91340 --exposure 1500000 --plan
python scripts/layers.py --layer L2 --class 91340 --exposure 1500000 --offline
python scripts/layers.py --layer L3 --allowance 200
```

---

# 2 · What a run is

**Every run covers every state, offline and then live.** No sampling of geography, no promotion step,
no cleverness deciding which states deserve a call. 50 jurisdictions are compared; Puerto Rico rates
but is never compared, because there is no RAaS entitlement for it.

**The offline pass is a pre-flight, not a decision point.** It runs first, costs nothing, and its only
job is to keep a payload that cannot be built — or that our own engine refuses — from ever spending a
live call. **It cannot tell you who is right:** agreement is defined by
`phase2_compare.compare_payload` and needs ISO's actual response. A state excluded by the pre-flight
is carried into the result as `preflight_excluded` rather than dropped, so a run never reports
coverage it did not have.

## The allowance, and how it is spent

**The daily budget is a ticker, not a gate.** It shows what today has spent and stops nothing. The
real control is per run: **you set an allowance**, and the harness fits the largest useful slice of
the matrix inside it.

**When the matrix does not fit, states are never what gets cut.** The configuration list is thinned
instead — keeping the ends and an even spread between them, because the ends of a filed table are
where a keying error shows. Every state appears in every run, so results stay comparable.

**Which configurations survived the thinning is written into the run.** Two runs of the same layer at
different allowances are different matrices, and one that does not say so invites a comparison that
is not valid.

## Long runs

A layer-3 run at the full matrix is around 600 calls, so a run can outlive a sitting. **A run can be
paused, resumed from exactly where it stopped, or stopped outright and kept as a partial** — which
names the scenarios and states it never reached. Losing two hundred calls' worth of answers to change
your mind about the last hundred is not acceptable.

---

# 3 · The `/tests` page

**A new page, alongside the existing QA tab, which is untouched.** Both write to the same run store.
The tier runner is working and being used; putting the new work beside it risked nothing.

**The class is chosen basis-first.** ISO declares **59 distinct premium bases** and about **1,190
class codes**. Picking the basis first narrows the class list and means the exposure box knows its own
unit before you type in it — most bases are counts (*Number of Zoos*, *Each Pier*, *Passenger Days*)
with no divisor at all, so one default exposure figure is meaningless across the set.

```
Layer          [2 · classification            ▾]

Premium basis  [Payroll                       ▾]   59 bases
                 → 268 classes

Class code     [carpentry                      ]   4 of 268 classes
                 91340  Carpentry-construction of residential property
                 91341  Carpentry – interior

Exposure amount (Payroll)  [1500000]

3 · ALLOWANCE
  ┌────────────────────────────────────────────┐
  │ 204 tests                                  │
  │ 4 configurations × 51 jurisdictions ·      │
  │ 200 against ISO                            │
  │ Thinned to fit 200 calls: 4 of 12          │
  │ configurations. Every jurisdiction kept.   │
  └────────────────────────────────────────────┘
Allowance      [200] live calls                    Today: 0 live calls

               [Plan it]   [Run]
```

**The test count is live**, not something you get after pressing a button. It is local arithmetic
from the layer's configuration count and the jurisdiction list, so it moves as you type and never
lags. It says *about N against ISO* because it assumes the class is filed everywhere — **`Plan it`
reads the declaration in all 51 and replaces the estimate with the counted figure**, which is smaller
wherever ISO does not file the class.

**An allowance cuts nothing offline.** It is denominated in live calls, and an offline run spends
none; thinning it to fit a call budget would give up coverage to save something it was never going to
spend.

While it runs: progress, results as they land, and **pause · resume · stop**. The run lives
server-side, so closing the tab does not kill it.

## Aggregate, verdict, trend — reusing the charts the QA tab already had

Added 18 August, after the run-page matrix and its pagination and filter. `ui/charts.py` has eight
chart functions, built for the QA tab (`ui/tester.py`), and none of them had ever been called from
this page. Four now are — the pattern is the one `tester.py` already established: the server renders
an SVG string and ships it in the JSON, the client does `el.innerHTML = svg`. Nothing is drawn twice.

**Aggregate** is a table, one row per layer, summed across every stored scenario for that layer —
not just the page of Run files below it. `layers.stored_rollup()` reads the store once and groups by
the same label the Run column already shows. A small colored dot per row reads the worst outcome at
a glance — blue agrees, red differed or was refused, amber is partial (some not-applicable, nothing
wrong), grey is either entirely not-applicable or nothing stored yet. Clicking a row sets the same
run-type filter Run files uses, and the two stay in sync in both directions.

**Verdict by layer** is four cards, not one combined card — `charts.verdict()` run once per layer
rather than summed across all of them, so a bad layer cannot hide behind three good ones the way a
single blended percentage would let it.

**Aggregate trend** is `charts.agreement_over_time()` across every live-compared scenario stamped
with one of the four layer labels, oldest first. Not filterable by layer yet — flagged as a
follow-on during design rather than built on a guess about whether it is wanted.

**The Result card** gained `status_bars()` (the outcome bar) and `usa_map()` (which states this run
touched, and which of those agreed), both scoped to the run that just finished, not the all-time
aggregate above them. `layers.run_map()` folds every scenario's rows in one job into a worst-first
per-jurisdiction status, the same rule `runstore.qa_rollup` uses for the QA tab's map, computed from
the job's in-memory results because the Result card needs an answer before anything reaches the
store.

**Two things approximated, and named as approximations.** `status_bars` calls `len()` on lists of
jurisdiction codes; a summed rollup only has counts, so `_bars_summary()` bridges the two with
placeholder lists (`["x"] * n`) — exact, since the chart never reads an element. And a rendered run
file's index entry (`runfile.entries()`) never stored a not-applicable count, so the Run files
table's dot (`histDot()`) infers it from what *is* stored — offline reads grey, any differ or
refusal reads red, `agree === rated` reads blue, anything else live is read as not-applicable
softening an otherwise clean run. Worth widening the index if the dot needs to stop approximating.

---

# 4 · The run file

**Every run writes a standalone HTML file** to `results/runs/`, self-contained, opening by
double-click with no server running. `results/runs/index.html` links them all, newest first.

**These files are git-ignored**, and `.gitignore` now says why: a run holds ISO's licensed premium
values, which is the same reason notebook outputs are stripped before commit.

**What the file says**, in this order:

1. **The headline** — *47 rated · 41 match · 6 differ*, with the scenario, call and refusal counts.
2. **What actually ran** — the basis groups, anything not filed, which configurations survived
   thinning, and whether the run was stopped early and where.
3. **Every state, sorted by size of difference**, each expanding to the fields that differ.

`compare_payload` distinguishes the four outcomes that matter — **MATCH**, **PREMIUM ONLY** (the
premium agrees but underlying fields do not), **DIFF**, and an `edition_agrees` flag so a difference
caused by ISO using a different edition is never mistaken for arithmetic.

## The matrix is a grid of buttons, not a table of numbers

Built after the rest of this document, once a run had enough cells to make the plain table hard to
scan: **state × configuration**, one button per cell, coloured by outcome. Hovering a cell opens a
panel beside the cursor with that cell's status, our premium, ISO's, the delta, and — offline — which
resolved values it used and whether the premium moved from the base at all. Clicking a cell filters
the state-by-state list below to that configuration and scrolls to the row, so a colour you notice in
the grid gets you to the fields that explain it in one click.

**It is still a self-contained file.** The grid, the panel and the click-filter are one inline
`<script>` block operating on the run's own data, embedded in the page — no network request, no
external file, nothing that stops working when the file is emailed or opened with no server running.
`tests/verify_layers.py` E3 checks for that directly: no `http://`/`https://`, no `<script src`, no
`fetch`/`XMLHttpRequest` — an inline script reading data already in the page is not a network load,
and the check was loosened from a blanket "no `<script>` tag at all" to say that.

## The review page — a second store, keyed to the run file, no API key anywhere

Added 18 August, after a planning conversation before a line of code was written. The question
was: can a run's failures get analysis, without an API key. The answer is the same shape
`qa_review.py`'s pass 4 already committed to for a different reason — the harness cannot invoke an
agent from the server, so it assembles evidence and a person dispatches it. This applies that split
per run instead of per review pass, and adds the piece pass 4 left open: somewhere for the answer
to live once it comes back.

**The run file is never touched.** It gains exactly one link, `Review this run →`, to a new page —
`/review/<run-file>` — that does not exist as a static artifact and needs the app running. Opening
a run file with no server running just makes that one link go nowhere; nothing about the file's own
promise (self-contained, opens by double-click) changes.

**`results/reviews/<run-file-stem>.json` sits beside `results/runs/<run-file>`.** Same stem, so the
pairing is visible from a directory listing without an index lookup. Git-ignored for the same reason
the run file is — it holds the same licensed premiums, quoted back into evidence.

**Only what a person wrote is ever persisted.** A finding's status, its pattern match, the row data
behind it are recomputed from the store on every read — never stored. Storing them would risk the
same drift `runstore.spent_today` was unified to prevent (Entry 29): two numbers about the same run,
free to disagree. What *is* persisted is a generated brief (so it doesn't change under someone
already answering it) and a posted analysis, verbatim.

**Two layers, and only the first is free.** `reviews.pattern_match` is mechanical — a refusal is
sorted into a question for ISO or a problem in our own environment by reusing `qa_review.classify`;
an inert-value pick already caught by `probe_no_op` is named as such; and a finding with the same
jurisdiction, status and differing fields as one already explained in a *different* run's review is
surfaced as "seen before" rather than re-asked. Nothing here guesses at *why* a number differs.
Anything left over gets `Generate a review brief` — the evidence, formatted as one markdown document,
meant to be pasted into a conversation a person is already having. What comes back is pasted in by
hand and stored as free text: not re-parsed, not treated as a verdict.

**The Run files table gained a second, independent tag.** Blue "has notes" or amber "review
started," separate from the existing outcome dot — a run can disagree and already have a posted
explanation, or agree cleanly and never need a review record at all. **It deliberately never claims
"fully reviewed"** — `reviews.quick_status` only reads the saved record (cheap, no store round-trip
for a table of forty runs), and the saved record only ever holds findings someone actually opened a
brief or posted an analysis for. A pattern-matched finding nobody clicked into is invisible to it,
so a run with one posted analysis and one untouched pattern match reads as "has notes," not
"reviewed" — the review page's own header, which does pay for the store round-trip, is the one place
that can honestly say a run is fully accounted for.

---

# 5 · What measuring the data changed

Three things were designed one way, measured, and then designed differently. All three are in the
code because of the measurement, not the plan.

**The basis-group split is a guard, not a routine event.** We decided a class filed on different
premium bases in different states must be split into separate sweeps and never compared across them.
Then we measured it: across TX, CA, NY, FL, OK and MT there are **1,188 class codes each, 1,187 common
to all six, and the basis differed for exactly one — which was simply undeclared in one state.** The
rule is right and will almost never fire. Layer 2 is simpler than it first looked.

**ISO files no class families.** Codes cluster by leading digit (63 at `10…`, 95 at `51…`) but the
data declares only codes, descriptions and bases. Any family taxonomy would be ours, not ISO's, which
is why the picker filters by **basis** — which *is* declared.

**The aggregate cannot be named as a figure.** The legal set is keyed on the occurrence limit and
differs by state — four legal aggregates at 25,000 in Texas, eight at 1,000,000. A plan naming
`5,000,000` would be undeliverable wherever that is not filed. So L3 carries **positions** —
`@lowest`, `@middle`, `@highest` — resolved per state, and **each row records the figure that state
actually received.** A run that stores the request and not the answer cannot be read back.

---

# 6 · What was built, and where it departed from the plan

| | What | Where |
|---|---|---|
| **New** | `general_aggregate` control, keyed off the occurrence limit; sets both aggregates and refuses a pair ISO does not declare | `scripts/variants.py` |
| **New** | `Declared.aggregates_for()` — the legal aggregates for an occurrence limit in that state | `scripts/variants.py` |
| **New** | The whole layered programme: layers, plan, thinning, per-state resolution, the runner and a CLI | `scripts/layers.py` |
| **New** | The `/tests` page, its routes, and the pause/resume/stop job | `ui/tests_page.py` |
| **New** | The standalone run file and the index | `ui/runfile.py` |
| **New** | 30 offline checks over all of it | `tests/verify_layers.py` |
| Changed | `run_config` gained `resolve` (per-state values) and `stop_check` (pause and stop), and now records `stopped_early` / `not_reached` | `scripts/sweep.py` |
| Changed | `compare_payload` returns **every** differing field, not the first three | `scripts/phase2_compare.py` |
| Changed | `spent_today()` moved into the store so the ticker and the tier budget count the same number once | `scripts/runstore.py`, `scripts/qa.py` |
| Changed | `.gitignore` now says why run files are excluded | `.gitignore` |

**Two departures from the plan, both deliberate:**

1. **The ladder went into `scripts/layers.py`, not `scripts/qa.py`.** The plan said qa.py. But the
   decision was that the QA tab stays untouched, and the tier runner is a different programme with a
   different unit of work. Merging them would have meant editing the one thing nobody asked to
   change. They share the run store, the variant definitions and the sweep.
2. **The tier runner keeps its budget gate.** The plan said demote the guard. Demoting it inside
   `qa.py` would change how the existing QA tab behaves, which contradicts leaving it alone. So the
   gate stays where it already was, the layered programme never gates, and **both read the same count
   from the store** — which was the real point.

---

# 7 · Verification

```
python tests/verify_layers.py        30/30   offline, no ISO calls
```

Groups A–F: the aggregate axis and its refusals · the allowance thinning configs and never states ·
basis grouping and *not filed* reported rather than filtered · the comparison returning every
differing field · a run writing one self-contained file that loads nothing from the network · the
ticker counted in one place.

Every other suite still passes, including `verify_tester` — the QA tab is genuinely untouched.

---

# 8 · Still open

**The index over the run files is deliberately plain.** It lists every run newest-first with its
layer, class and counts. It does not yet answer *"show me every run of class 91340"* by filtering,
which is worth adding once there are enough files to need it.

**L5 and L6** — the deductible amount ladder and the combined-versus-separate exclusion — are
designed but not built, by the ordering decision in §1.

**A products-only aggregate axis.** The aggregate control sets both aggregates together, because ISO
keys both on the occurrence limit and declares the same legal set for each. Varying the two against
each other is a further axis and is not this one.

---

# 9 · What this does not cover

This is the **test programme and its page**. It does not address the other UI gaps in
`START-HERE-TOMORROW.md` — the as-of date selector (blocked on D-1), the W6 reviewer-verdict
decision, scheduling, or *"what changed since last run"*. Those remain where they were.
