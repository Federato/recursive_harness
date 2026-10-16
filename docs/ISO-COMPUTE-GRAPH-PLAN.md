<!-- COPY. Master: C:\FederatoProjects\ISOComputeGraph\docs\PLAN.md. Do not edit here; edit the master and run tools/sync_plan.py. -->

# ISO compute graph — proof of concept plan

**Status: drafted 2026-10-16, not started. Needs the user's go to begin P1.**
Master copy: `C:\FederatoProjects\ISOComputeGraph\docs\PLAN.md`. Synced copy:
`C:\FederatoProjects\Recursive_Harness_2.0\docs\ISO-COMPUTE-GRAPH-PLAN.md` (`python tools/sync_plan.py`).
Harness backlog item: **B-55** (RC-5).

**In short.** Take ISO's Iowa General Liability rules and rate tables and turn them into one fixed flowchart:
a *compute graph* in the shape Federato's Product Studio uses. No Excel. Then rate policies on that flowchart
and check that every premium is exactly what our engine and ISO give. It answers four questions: can ISO's
rules become a fixed graph, where does that break, does a carrier deviation sit on top cleanly, and what
would Product Studio have to add to run ISO this way. About **10 to 15 working days**, **0 ISO calls**.

## 1. Goal, and what this is not

| Goal | Not in scope |
|---|---|
| A compiler: ISO rule programs + tables → a fixed graph, per Iowa GL edition | Uploading anything to Product Studio (it accepts only Excel today) |
| An executor that rates a request on that graph | Replacing or changing the harness engine |
| Proof: same answer as the engine, field for field, and as ISO's stored answers | Property, other states (later, if this works) |
| DEV-003 (UFG Iowa GL) on top of the graph | Speed tuning beyond measuring it |
| A drawing of the graph in Product Studio's six kinds (absorbs B-31) | Spending ISO calls |
| A findings list: what Product Studio would need | |

## 2. Decisions taken (2026-10-16)

| # | Question | Decision |
|---|---|---|
| D1 | How this project uses the harness | **Imports it in place.** No copies; the harness never imports this project; harness defects are logged and fixed in the harness |
| D2 | Which copy of this plan is edited | **This one.** `tools/sync_plan.py` copies it to the harness and refuses if the copy was edited by hand |
| D3 | First scope | **Iowa GL** |
| D4 | Version control | **Local git** in this folder, no remote for now |
| D5 | What the proof stands on | **Every Iowa GL edition with stored ISO answers** (5 editions, 11 answers) plus DEV-003's U8, and the engine on generated requests. 0 ISO calls |

## 3. What we start from (measured 2026-10-16)

| Fact | Value | Where |
|---|---|---|
| Iowa edition in force on 2026-10-16 | GL_IA_20261001_V01 on GL_CW_20261001_V01 | `gl_engine/resolve/resolver.py:132` (`EditionResolver.resolve`) |
| Rule programs, in force | IA 15 files / 56 rules; CW 563 files / 4,557 rules; **effective 571 files, 4,590 rules** + `Default` (a state rule replaces a countrywide one by name) | `gl_engine/interp/program.py`, `interpreter.py:567-590` |
| Stored ISO answers, Iowa GL | **11**, all rated: 3 on 20240401, 3 on 20250401, 3 on 20260601, 1 on 20261001_V01, 1 on 20270401_V04. Plus 18 premium-only rows on 20260601 | `results/tc/answers/`, index `results/tc/reference_index.json` |
| Package samples | 1 (`STC/STC_GL000201550.json`, IA package) | corpus |
| DEV-003 check (U8) | 3 risks dated 7/15/2025 (edition 20250401): **2,828 / 3,818 / 830**, ISO exact | `tests/verify_deviations_ufg_ia_gl.py`, `docs/deviations/FILINGS-LOG.md:108-118` |
| Engine entry | `Kernel.rate(payload, version=None, *, company=None, with_technical=False, graph=False, ...)` | `gl_engine/rating/kernel.py:163` |
| Rating graph (per rating) | `RatingGraph.to_json()`: input / write / table / company nodes; data / control edges | `gl_engine/interp/graph.py:275` |
| Rounding | Half-up by `@DecimalPlaces`; reuse `Interpreter.round_to` | `interpreter.py:444-458` |
| Look-ahead (OI-125) | **Property only**; not in GL | `cf_engine/run_checks.py:162-208` |

## 4. How ISO's rules map to the graph

The graph keeps Product Studio's six kinds and adds what ISO's rules need. Counts are uses in Iowa's effective
in-force program.

| ISO instruction | Uses | Graph piece | Difficulty |
|---|---|---|---|
| `Value`, `Copy`, `Param` / `Arg` / `WithArgs` | 4,342 / 140 / 1,854 | **Input**, or an edge from an earlier step | Easy |
| `Lookup` + `Keys` | 2,324 | **Rate table** (loaded once, shared) + **Lookup** (keys, column, range keys) | Easy: table and column are named in the rule |
| `Sum`, `Product`, `Subtract`, `Divide`, `Max`, `Round`, `Truncate`, `Convert`, dates, text | ~1,630 | **Rating step** | Easy |
| `RunRule` | 4,010 | Inlined: the rule's steps are copied in where it is called | Easy: the rule is named |
| `If` / `Choose` / `When`, comparisons, `And` / `Or` | 3,333 / 124 / 315, ~8,400 | **Condition** on the steps the branch decides (any step, not only charges) | Medium |
| `FirstValue`, `FirstNonNull` | 7,460 / 1,721 | A step that takes the first non-empty of its inputs | Medium |
| Fields written more than once | 307 of 351 write targets at more than one site (overstated: paths are relative) | **Versions** of a value, as the rating graph keeps them | Medium |
| `ForEach` | 1,030 | **Repeating group**: steps repeated per location, class, coverage | **Hard**: the count isn't known until the request arrives |
| `Locate` with `Append` | 135 (of 319 `Locate`) | **Record created during the rating** | **Hard** |
| `Remove` | 62 | **Record removed during the rating**: later steps see fewer | **Hard** |
| `Exist` / `NotExist` / `Count` | 389 / 193 / 61 | A test on which records exist **at that point in the order** | Medium-hard |
| `Break` | 4 | "Stop at the first match" condition | Medium |
| `Guid` | 134 | A generated id; must be made repeatable for a comparison | Check |
| `Custom`, `FromList`, `LastNonNull`, `Power`, `Null` | 0 | — | — |

## 5. Phases and gates

Each phase ends at its gate. A gate that fails stops the next phase until fixed or re-scoped with the user.

| Phase | Builds | Gate | Days |
|---|---|---|---|
| **P0 · Setup** *(done 2026-10-16)* | Folder, git, `CLAUDE.md`, plan sync, B-55 in the harness backlog | `sync_plan.py --check` says in sync | — |
| **P1 · Inventory** | `cg/inventory.py`: per edition, instruction counts, the rules each hard instruction sits in, write sites by resolved field | Counts for all 5 editions; the hard spots listed by rule; the in-force counts above reproduced | 0.5 |
| **P2 · Graph format + tables** | `cg/model.py` (nodes: input, rate table, lookup, step, condition, repeat group, record create / remove, premium; versions); ISO tables loaded as shared rate tables through the harness's `load_table` / `ResolvedBook.table` | Every table the Iowa program names loads; a lookup on the graph returns the same row as `Interpreter.lookup` on 200 sampled keys, range keys included | 1-2 |
| **P3 · Compiler, straight-line** | `cg/compile.py`: rules inlined, steps, lookups, conditions, versions; loops and record changes left as marked holes | Compiles all 5 editions with no crash; every hole is one of the hard instructions in §4 | 2-3 |
| **P4 · Compiler, the hard part** | Repeating groups, created / removed records, `Exist` / `Count` in order, `Break`, `Guid` | Holes = 0, or each remaining one is a named finding with its rule and why | 2-4 |
| **P5 · Executor** | `cg/run.py`: rates a request on the graph in dependency order, half-up rounding reused from the harness | Rates the IA sample end to end on the in-force edition | 1-2 |
| **P6 · Proof** | `cg/prove.py` | **(a)** All 11 stored ISO answers: every premium exact. **(b)** Engine vs graph, field for field (all output fields), on the 11 stored requests, the package sample and Iowa requests generated by `scripts/variants.py`, on each of the 5 editions. **(c)** Replay: every plain arithmetic step re-computes from its inputs | 1-2 |
| **P7 · DEV-003** | UFG's compiled rows (`Carriers\UFG\{UFC,ADD}\compiled\GL\IA\IA-GL-UNFG-134374972.v2`) as override tables and policy-level steps on the graph | U8's three risks: **2,828 / 3,818 / 830**; technical side unchanged | 1 |
| **P8 · Product Studio view** | Export and a page drawing the graph in their six kinds, extras marked (absorbs B-31) | One premium traced from inputs to output on the page, matching the harness worksheet | 1-2 |
| **P9 · Findings** | `docs/FINDINGS.md`: what compiled, what didn't, graph size, speed vs the engine, what Product Studio would need, effort to reach 51 states | Reviewed with the user | 1 |

**Total: about 10 to 15 working days.** The low end assumes P4 goes cleanly; the high end assumes it doesn't.

## 6. Layout

```
ISOComputeGraph/
  CLAUDE.md          how this project relates to the harness
  docs/PLAN.md       this plan (master)
  docs/FINDINGS.md   P9
  cg/                inventory, model, compile, run, prove, export
  tests/             one verify_ script per gate
  tools/sync_plan.py plan sync
  results/           compiled graphs and proof runs (git-ignored if large)
```

The harness is put on the import path by `cg/harness.py` (one place), with `GL_ERC_ROOT` and `CARRIERS_ROOT`
as the harness sets them. Nothing here writes into the harness folder except the synced plan copy.

## 7. Risks

| Risk | Handling |
|---|---|
| Records created and removed during a rating (§4) may not fit a fixed graph | That is the question being asked. P4 records each case as compiled or as a named finding |
| A compiled graph is a second implementation and can drift from ISO | The engine stays the referee; every graph is proved against it (P6) before anything else |
| Only 1 stored ISO answer on today's edition | D5: 5 editions, 11 answers, plus the engine on generated requests |
| `Guid` makes ids differ run to run | Compare by field, not by generated id; seed if needed |
| 18 countrywide rule-file paths are 260+ characters | Read through the harness's own loader; any script reading files directly uses the `\\?\` prefix |
| 16 GB PC | Proof runs one process at a time, 2 workers max |

## 8. Questions for Federato (collected for P9, not asked yet)

| # | Question |
|---|---|
| F1 | Can a graph be loaded without Excel (API or file), and in what format? |
| F2 | Can a step repeat per item of a list (locations, classes)? |
| F3 | Can rating create or remove records while it runs? |
| F4 | Can a condition switch off any step, not only add a charge? |
| F5 | Can a value be worked out twice, with later steps using the newer version? |
| F6 | Can one rate table be shared by many products and versioned by edition? |
| F7 | Multi-key and range-key lookups with interpolation? |

## 9. Log

| Date | Entry |
|---|---|
| 2026-10-16 | Plan drafted; D1-D5 taken; P0 done. Waiting for the go on P1 |
