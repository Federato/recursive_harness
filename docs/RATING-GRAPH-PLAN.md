# Rating graph — scope for sign-off

**Status: signed off 2026-10-09 (R1–R3 as proposed). G1, G2 and G3 built the same day.**

## 1. What this is

The engine stays an **interpreter**: it runs ISO's rule programs in filed order against a data tree. That is what
keeps it field-for-field equal to ISO (T1, and technical matching ISO in 96 of 96 states), and it does not change.

This adds a **rating graph**: a record, built while one rating runs, of which values each written value was
computed from. Nodes are values; edges say "this was read to compute that". It is a byproduct of a rating, never
an input to one.

**Non-goals.** The graph never computes a value, never changes a rating, and is never the source of truth. No
incremental re-rating in this scope (§7).

## 2. What it is for

| | Today | With the graph |
|---|---|---|
| **"Why is this 0.407?"** | The worksheet shows the rule file and the tables read just before the write | Click the value: its inputs (0.411 × 0.99), and theirs, back to the base rate, the applied LCM, the filing row and the ISO table rows |
| **What a deviation moved** | Field-by-field difference between technical and carrier | The path from each company source (LCM row, table row) to every value it reached, drawn on the worksheet |
| **T4 locality** | Taint tracking over-approximates what a company input can reach | Exact reachability from the company's sources |
| **What drives a premium** | Not shown | Each premium's contributing tables and factors, listed |

## 3. The model

Measured on 2026-10-09 (Iowa sample, one building): **1,161 writes, 144 table lookups, 949 output fields**; GL
Texas: 414 writes, 79 lookups. A graph is a few thousand nodes and edges per rating.

**Nodes**

| Kind | One per | Carries |
|---|---|---|
| `input` | submitted field read during the rating | path, value |
| `table` | table row returned by a lookup | package, table, keys, column, value; `company` when a carrier's layer supplied it |
| `write` | **each** write (a field written twice is two nodes, `#1` and `#2`) | path, value, rule file, the operation that wrote it |
| `company` | carrier source applied | the filing row (`IA-CF-UNFG-134289779.v1#4`), what it applied to (record LCM, group LCM, table override) |
| `constant` | not modelled | constants are part of the rule, shown on the write's operation |

**Edges**

| Kind | From → to | Meaning |
|---|---|---|
| `data` | a value read while a write's expression was evaluated → the write | the arithmetic used it |
| `control` | a value read by an `If` / `Choose` / `When` test, a `ForEach` collection or a `FirstNonNull` fallback that decided whether the write happened → the write | it decided the branch, not the number |
| `lookup` | key values → the table node; the table node → the write that used it | |

A read points at the **latest version** of a field at the moment it is read, so a value overwritten later
(California's recomputed fields, the minimum-premium re-evaluation) is linked to exactly the version that was used.

## 4. How it is captured

The P3 tracker (`gl_engine/interp/taint.py`) already hooks every place the interpreter reads, looks up, writes and
calls a rule. The graph replaces its yes/no flags with sets of node ids:

- each expression being evaluated collects the node ids it read; a write takes them as its `data` edges;
- `If` / `Choose` / `When` / `ForEach` / `FirstNonNull` push their test's reads as a control set while their
  chosen branch runs, and pop them after. Every write inside gets those as `control` edges, including writes in
  rules called from the branch. **This is the one part the tracker only approximated, and the one new hook site.**
- lookups add a `table` node for the row returned (company rows marked); the deviation hooks add `company` nodes;
- the OI-125 look-ahead pass is not captured, as tracking already does.

**Off by default.** `rate(..., graph=True)` and `Kernel.rate(..., graph=True)` attach a `RatingGraph`; nothing else
changes. Tracking cost about 3%; the graph is estimated at 10–30%, paid only when asked.

## 5. Phases and gates

| Phase | Builds | Gate |
|---|---|---|
| **G1 — Capture** · *done* | `gl_engine/interp/graph.py`, the hooks above, JSON export, both entry points | (a) Snapshot regression clean with the graph **off**. (b) With it **on**, every rating in a sample of each state is unchanged, field for field. (c) Completeness: every written field in the tree has a `write` node; every read resolves to a node; no dangling edge. (d) Spot proofs: for 50 arithmetic writes, re-applying the operation to the values on its `data` edges gives the written value. |
| **G2 — Worksheet drill-down** · *done* | Click any value in the rating worksheet: its inputs as a tree (values, rule, table rows), N levels up; for a carrier, the path back to the filing row highlighted; a premium's contributing tables and factors | Checked live on the UFG Iowa risk; `verify_console_deviations` extended |
| **G3 — Exact T4** · *done* | T4 uses graph reachability from company sources instead of the tracker | On every T4 case: graph reach ⊆ tracker reach, and ⊇ every changed field. The tracker is retired once both hold |
| *Later, optional* | Sensitivity (which tables and factors move a premium most); incremental re-rating | Separate scope (§7) |

## 6. Risks

- **Control dependence is where it can be wrong.** A write decided by a test but missing the `control` edge would
  make a drill-down incomplete and G3 unsound. Gate G1(d) checks data edges; G3's "⊇ every changed field" is the
  check on control edges, run over every T4 case and the T2 identity population.
- **Repeated writes.** Handled by versioned nodes; the worksheet shows the final version and can expand earlier ones.
- **Size on big risks.** Multi-location stored requests reach about 2,100 output fields, so tens of thousands of
  edges. Fine in memory; the worksheet asks for one value's ancestry at a time, not the whole graph.
- **The interpreter is shared by both lines.** Every hook is inert when no graph is asked for; G1(a) is the proof.

## 7. Out of scope: incremental re-rating

Re-running only what changed would speed what-ifs and waterfalls, but the rules' order, overwrites and control flow
mean a partial re-run can differ from a full one. That is the drift the interpreter exists to avoid. The waterfall
already re-rates fully in under a second per step. Revisit only if speed becomes the problem.

## 8. Decisions needed

| # | Question | Proposal |
|---|---|---|
| R1 | Build G1–G3? | Yes, in order; each gated |
| R2 | Build the graph for every worksheet automatically, or only on a "Trace this value" click? | On open: a worksheet already re-rates twice, and the cost is small |
| R3 | How far up a drill-down goes by default | 3 levels, expandable to the inputs |

## 9. As built (2026-10-09)

- **G1.** `gl_engine/interp/graph.py`; `rate(..., graph=True)` / `Kernel.rate(..., graph=True)`. Measured on the
  Iowa sample: 1,384 nodes, 1,733 edges, +5% rating time when on. `tests/verify_rating_graph.py`: 52 ratings
  (Property in every state, GL in six) unchanged with it on; one write node per write; no dangling edge; **2,300**
  plain Product/Sum writes replay exactly; a carrier's sources (record LCMs, group LCMs, company table rows) are
  company nodes; control edges present (e.g. the windstorm indicator decides the Group II deductible-by-location
  factor). Rule parameters carry what their argument was computed from; range-keyed lookups are linked too.
- **G2.** Opening a worksheet builds both graphs (R2) and keeps the last 8 by token. Clicking a technical or deviated
  value shows its ancestry 3 levels deep (R3), expandable node by node, then every filing row, table row and input it
  came from; on the deviated side, what the filing reached is highlighted. `verify_console_deviations.py` part G.
- **G3.** On all five T4 cases the graph's reach equals the old tracker's exactly (101, 101, 232, 34 and 31 fields)
  and covers every changed field (67, 67, 153, 31, 26). T4 now uses the graph; `taint.py` and the `track` option are
  gone.

## 10. Beside Product Studio's compute graph (B-30, 2026-10-16)

**In short.** Federato's Product Studio now rates a product on a *compute graph* compiled from the actuary's Excel
workbook (`docs/external/federato-compute-graphs_20261014.md`). It is the same picture as our rating graph, built
the other way round. Theirs **is the program**: built once from the workbook, then run for every policy, and held to
the workbook's answer. Ours **is a record**: written down while ISO's rules run for one risk, never run itself, and
held to ISO's answer. We explain a premium the way their graph does; the answer we are held to is ISO's.

**Their six kinds, in our terms**

| Product Studio | Our graph | Difference |
|---|---|---|
| Policy information (inputs) | `input` node | Same: a submitted value the rating read |
| Rate table | — (no node for a whole table) | We only record the row a lookup returned, inside the `table` node (package, table, keys, column) |
| Lookup | `table` node + `lookup` edges | Their lookup is the entry found; our `table` node is that row, and `lookup` edges join its keys to it and it to the write |
| Rating step | `write` node | Ours is versioned: a field written twice is two nodes (`#1`, `#2`). A workbook cell is written once |
| Coverage condition | a `write` with `control` edges | Theirs is a kind of node; ours is a kind of edge. Any write decided by an `If` / `Choose` / `When` / `ForEach` / `FirstNonNull` test carries its test's reads as `control` edges |
| Premium (outputs) | `write` nodes on premium output fields | No separate kind; a premium is the last write to an output field |
| — | `company` node | Ours only: the carrier filing row a deviated value came from. In Product Studio the carrier's rates are simply the workbook's tables |

**Where they differ in kind**

| | Product Studio | Ours |
|---|---|---|
| Direction | Workbook → graph, ahead of time | ISO's rule programs run; the graph is written down as they run |
| Shape | One graph per product version | One graph per rating: a risk with three locations unrolls `ForEach` into three copies |
| Authority | The actuary's workbook (*"it gets Excel's answer"*) | ISO's rating service (T1; technical exact in 96 of 96 states) |
| Runs | Yes: it is the rating engine (~100x faster than running the workbook) | Never: a byproduct, off unless asked (§1) |

**Why we don't run ours (B-33).** Their speed gain is against running a spreadsheet. Ours would be against an
interpreter that already rates a full risk in under a second, and running the graph means re-running only what
changed, which §7 rules out: rule order, overwrites (California's recompute, the minimum premium re-evaluation) and
control flow mean a partial run can differ from a full one. A graph also captures only the branches one risk took,
so it cannot rate a different risk. Revisit only with a speed problem.

**What a port would take (B-34, parked).** Putting ISO GL into Product Studio means workbooks their extractor
accepts, per state and edition, with our ISO comparison run over them, because a workbook can match itself and
still be wrong against ISO. B-32 (one state, one upload) sizes it first; neither starts without a business ask.
