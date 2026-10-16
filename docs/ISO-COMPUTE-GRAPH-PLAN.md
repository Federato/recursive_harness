<!-- COPY. Master: C:\FederatoProjects\ISOComputeGraph\docs\PLAN.md. Do not edit here; edit the master and run tools/sync_plan.py. -->

# ISO compute graph — proof of concept plan

**Status: drafted 2026-10-16, revised the same day (the harness loop; ISO without deviations first). Not
started. Needs the user's go to begin P1.**
Master copy: `C:\FederatoProjects\ISOComputeGraph\docs\PLAN.md`. Synced copy:
`C:\FederatoProjects\Recursive_Harness_2.0\docs\ISO-COMPUTE-GRAPH-PLAN.md` (`python tools/sync_plan.py`).
Harness backlog item: **B-55** (RC-5).

**In short.** Take ISO's Iowa General Liability rules and rate tables and turn them into one fixed flowchart:
a *compute graph* in the shape Federato's Product Studio uses. No Excel. Then test it the way the harness tests
itself: send the same request to ISO's rating service, to our engine and to the graph, and treat every
difference as a defect to find, judge, fix and re-run. The first passes are ISO's own rating only, with no
carrier deviation; UFG's deviation comes after the plain ISO passes are clean. It answers four questions: can
ISO's rules become a fixed graph, where does that break, does a deviation sit on top cleanly, and what would
Product Studio have to add. About **10 to 15 working days**; stored ISO answers first, live ISO calls only
for what the stored set doesn't cover, with a go per pass.

## 1. Goal, and what this is not

| Goal | Not in scope |
|---|---|
| A compiler: ISO rule programs + tables → a fixed graph, per Iowa GL edition | Uploading anything to Product Studio (it accepts only Excel today) |
| An executor that rates a request on that graph | Replacing or changing the harness engine |
| The harness loop, three ways: ISO, engine, graph (§5) | Property, other states (later, if this works) |
| ISO's rating first; DEV-003 (UFG Iowa GL) only after | Speed tuning beyond measuring it |
| A drawing of the graph in Product Studio's six kinds (absorbs B-31) | |
| A findings list: what Product Studio would need | |

## 2. Decisions taken (2026-10-16)

| # | Question | Decision |
|---|---|---|
| D1 | How this project uses the harness | **Imports it in place.** No copies; the harness never imports this project; harness defects are logged and fixed in the harness |
| D2 | Which copy of this plan is edited | **This one.** `tools/sync_plan.py` copies it to the harness and refuses if the copy was edited by hand |
| D3 | First scope | **Iowa GL** |
| D4 | Version control | **Local git** in this folder, no remote for now |
| D5 | What the proof stands on | **Every Iowa GL edition with stored ISO answers** (5 editions, 11 answers), and the engine on generated requests |
| D6 | How it is tested | **The harness's own loop**, with the graph as a third party: same request to ISO, engine and graph; every difference judged, fixed in the right project, re-run, recorded (§5) |
| D7 | ISO calls | **Stored answers first, then live**: each pass runs free on the stored answers; live calls only for requests the stored set doesn't cover, through the harness's call ledger (lane `active`, shown as *Planned work*, origin `iso-compute-graph`), **up to 25 a pass, with the user's go per pass** |
| D8 | Deviations | **ISO without deviation first.** Passes 1 onward rate ISO's technical premium only; DEV-003 starts only when the technical loop is clean (P8) |

## 3. What we start from (measured 2026-10-16)

| Fact | Value | Where |
|---|---|---|
| Iowa edition in force on 2026-10-16 | GL_IA_20261001_V01 on GL_CW_20261001_V01 | `gl_engine/resolve/resolver.py:132` (`EditionResolver.resolve`) |
| Rule programs, in force | IA 15 files / 56 rules; CW 563 files / 4,557 rules; **effective 571 files, 4,590 rules** + `Default` (a state rule replaces a countrywide one by name) | `gl_engine/interp/program.py`, `interpreter.py:567-590` |
| Stored ISO answers, Iowa GL | **11**, all rated: 3 on 20240401, 3 on 20250401, 3 on 20260601, 1 on 20261001_V01, 1 on 20270401_V04. Plus 18 premium-only rows on 20260601 | `results/tc/answers/`, index `results/tc/reference_index.json` |
| Package samples | 1 (`STC/STC_GL000201550.json`, IA package) | corpus |
| ISO's rating service | `scripts/raas.py` `RaaS(lane=..., origin=..., override=...)`; ledger cap 250 a day: `active` 150, `refresh` 50, `adhoc` 50 | `console/ledger.py:23-24` |
| Expert reviewers | `gl-authority`, `gl-engine-code-expert`, `iso-circular-expert` (user-level agents, usable from this folder) | `~/.claude/agents/` |
| DEV-003 check (U8), for P8 | 3 risks dated 7/15/2025 (edition 20250401): **2,828 / 3,818 / 830**, ISO exact | `tests/verify_deviations_ufg_ia_gl.py`, `docs/deviations/FILINGS-LOG.md:108-118` |
| Engine entry | `Kernel.rate(payload, version=None, *, company=None, with_technical=False, graph=False, ...)`; no `WritingCompany` in the request = technical only | `gl_engine/rating/kernel.py:163, 186` |
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

## 5. The loop: ISO, engine and graph

The harness's loop is *same submission to ISO and to our engine → difference → every gap is our defect or a
finding about ISO → expert reviewers judge it against the manual and the files → fix, re-run, record*. Here the
graph joins as a third party, and the engine stays the referee for the graph.

```
  request set (stored, generated, then new)
        │ same request, technical only (no WritingCompany)
        ├──────────────► ISO RaaS   (stored answer first; live only if none, D7)
        ├──────────────► harness engine
        └──────────────► compiled graph
                              │
                    three-way difference, field by field
                              │
              judge each gap (expert reviewers) ──► fix in the right project
                              │
                    re-run everything so far, record the pass
```

**Where each difference goes**

| Graph | Engine | ISO | Means | Goes to |
|---|---|---|---|---|
| = | = | = | Clean | Recorded |
| ≠ | = | = | The compiler or executor is wrong | Fixed here |
| = | ≠ | = | The graph caught an engine defect | Logged and fixed in the harness (`docs/OPEN-ITEMS.md`), then re-run here |
| = | = | ≠ | Both ours differ from ISO the same way | A harness defect or an ISO finding: logged in the harness |
| ≠ | ≠ | any | Unclear | Judged first by `gl-authority`; nothing is fixed until it is placed |
| — | — | refuses | ISO refuses the request | The graph must refuse it too, as the engine does |

**Each pass**

| Step | What happens |
|---|---|
| 1. Request set | Everything from earlier passes plus this pass's new requests (regression grows, never shrinks) |
| 2. Free run | ISO side from stored answers; engine and graph rate everything |
| 3. Live gap | Requests with no stored ISO answer are listed with a call count; **live calls only with the user's go** (≤ 25, lane `active`, origin `iso-compute-graph`). New answers are stored in the harness's answer store (`results/tc/answers/`) so both projects reuse them; the only harness write besides the plan copy |
| 4. Judge | Every gap placed by the table above, using the expert reviewers where it isn't obvious |
| 5. Fix | In the project the table names; a harness fix goes through the harness's own gates |
| 6. Record | `results/passes/pass-NN.json` (requests, three answers, every gap and where it went) and a line in §10's log |
| 7. Exit | A pass is clean when every request is graph = engine = ISO, or each remaining gap is a recorded finding |

## 6. Phases and gates

Each phase ends at its gate. A gate that fails stops the next phase until fixed or re-scoped with the user.
**P1 to P7 are ISO only (no deviation).**

| Phase | Builds | Gate | Days |
|---|---|---|---|
| **P0 · Setup** *(done 2026-10-16)* | Folder, git, `CLAUDE.md`, plan sync, B-55 in the harness backlog | `sync_plan.py --check` says in sync | — |
| **P1 · Inventory** | `cg/inventory.py`: per edition, instruction counts, the rules each hard instruction sits in, write sites by resolved field | Counts for all 5 editions; the hard spots listed by rule; the in-force counts above reproduced | 0.5 |
| **P2 · Graph format + tables** | `cg/model.py` (nodes: input, rate table, lookup, step, condition, repeat group, record create / remove, premium; versions); ISO tables loaded as shared rate tables through the harness's `load_table` / `ResolvedBook.table` | Every table the Iowa program names loads; a lookup on the graph returns the same row as `Interpreter.lookup` on 200 sampled keys, range keys included | 1-2 |
| **P3 · Compiler, straight-line** | `cg/compile.py`: rules inlined, steps, lookups, conditions, versions; loops and record changes left as marked holes | Compiles all 5 editions with no crash; every hole is one of the hard instructions in §4 | 2-3 |
| **P4 · Compiler, the hard part** | Repeating groups, created / removed records, `Exist` / `Count` in order, `Break`, `Guid` | Holes = 0, or each remaining one is a named finding with its rule and why | 2-4 |
| **P5 · Executor** | `cg/run.py`: rates a request on the graph in dependency order, half-up rounding reused from the harness | Rates the IA sample end to end on the in-force edition | 1-2 |
| **P6 · The loop** | `cg/loop.py`: the pass of §5, three-way difference, pass records | Runs a pass on the 11 stored requests and the sample, free | 1 |
| **P7 · Technical passes** | Pass 1: the 11 stored requests + the sample. Pass 2: Iowa requests generated by `scripts/variants.py` on all 5 editions (live gap per D7). More passes until clean. Every plain arithmetic step also replays from its inputs | **Clean pass**: graph = engine = ISO on every request, field for field (all output fields), or each gap a recorded finding | 1-3 |
| **P8 · DEV-003** *(after P7 is clean)* | UFG's compiled rows (`Carriers\UFG\{UFC,ADD}\compiled\GL\IA\IA-GL-UNFG-134374972.v2`) as override tables and policy-level steps; the loop re-run with the carrier side added | U8's three risks: **2,828 / 3,818 / 830**; technical side unchanged; the technical regression still clean | 1 |
| **P9 · Product Studio view** | Export and a page drawing the graph in their six kinds, extras marked (absorbs B-31) | One premium traced from inputs to output on the page, matching the harness worksheet | 1-2 |
| **P10 · Findings** | `docs/FINDINGS.md`: what compiled, what didn't, graph size, speed vs the engine, engine defects the graph found, what Product Studio would need, effort to reach 51 states | Reviewed with the user | 1 |

**Total: about 11 to 17 working days.** The low end assumes P4 goes cleanly and the first technical passes
are close; the high end assumes neither.

## 7. Layout

```
ISOComputeGraph/
  CLAUDE.md          how this project relates to the harness
  docs/PLAN.md       this plan (master)
  docs/FINDINGS.md   P10
  cg/                harness (import), inventory, model, compile, run, loop, export
  tests/             one verify_ script per gate
  tools/sync_plan.py plan sync
  results/passes/    one record per loop pass
  results/           compiled graphs (git-ignored if large)
```

The harness is put on the import path by `cg/harness.py` (one place), with `GL_ERC_ROOT` and `CARRIERS_ROOT`
as the harness sets them. Nothing here writes into the harness folder except the synced plan copy and new ISO
answers in its answer store (§5, step 3).

## 8. Risks

| Risk | Handling |
|---|---|
| Records created and removed during a rating (§4) may not fit a fixed graph | That is the question being asked. P4 records each case as compiled or as a named finding |
| A compiled graph is a second implementation and can drift from ISO | The loop: every request goes to ISO, engine and graph, every pass, and the regression only grows |
| Only 1 stored ISO answer on today's edition | D5 and D7: 5 editions, 11 answers, and live calls for the gaps with a go per pass |
| Live calls share the harness's 250 a day | ≤ 25 a pass, lane `active`, with a go; the ledger refuses a full lane |
| `Guid` makes ids differ run to run | Compare by field, not by generated id; seed if needed |
| 18 countrywide rule-file paths are 260+ characters | Read through the harness's own loader; any script reading files directly uses the `\\?\` prefix |
| 16 GB PC | Passes run one process at a time, 2 workers max |

## 9. Questions for Federato (collected for P10, not asked yet)

| # | Question |
|---|---|
| F1 | Can a graph be loaded without Excel (API or file), and in what format? |
| F2 | Can a step repeat per item of a list (locations, classes)? |
| F3 | Can rating create or remove records while it runs? |
| F4 | Can a condition switch off any step, not only add a charge? |
| F5 | Can a value be worked out twice, with later steps using the newer version? |
| F6 | Can one rate table be shared by many products and versioned by edition? |
| F7 | Multi-key and range-key lookups with interpolation? |

## 10. Log

| Date | Entry |
|---|---|
| 2026-10-16 | Plan drafted; D1-D5 taken; P0 done |
| 2026-10-16 | Revised by the user: the harness loop three ways (D6), stored answers then live with a go per pass (D7), ISO without deviation first, DEV-003 moved to P8 (D8). Waiting for the go on P1 |
