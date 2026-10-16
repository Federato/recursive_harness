<!-- COPY. Master: C:\FederatoProjects\ISOComputeGraph\docs\PLAN.md. Do not edit here; edit the master and run tools/sync_plan.py. -->

# ISO compute graph — proof of concept plan

**Status: drafted 2026-10-16, revised the same day (the harness loop; ISO without deviations first). Not
started. Organised in release-candidate groups CG-1 to CG-8 (§6). Needs the user's go to begin CG-1.**
Master copy: `C:\FederatoProjects\ISOComputeGraph\docs\PLAN.md`. Synced copy:
`C:\FederatoProjects\Recursive_Harness_2.0\docs\ISO-COMPUTE-GRAPH-PLAN.md` (`python tools/sync_plan.py`).
Harness backlog item: **B-55** (RC-5).

**In short.** Take ISO's Iowa General Liability rules and rate tables and turn them into one fixed flowchart:
a *compute graph* in the shape Federato's Product Studio uses. No Excel. Then test it the way the harness tests
itself: send the same request to ISO's rating service, to our engine and to the graph, and treat every
difference as a defect to find, judge, fix and re-run. The first passes are ISO's own rating only, with no
carrier deviation; UFG's deviation comes after the plain ISO passes are clean. It answers four questions: can
ISO's rules become a fixed graph, where does that break, does a deviation sit on top cleanly, and what would
Product Studio have to add. About **12 to 20 working days**; stored ISO answers first, live ISO calls only
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
| D8 | Deviations | **ISO without deviation first.** Passes 1 onward rate ISO's technical premium only; DEV-003 starts only when the technical loop is clean (CG-6) |

## 3. What we start from (measured 2026-10-16)

| Fact | Value | Where |
|---|---|---|
| Iowa edition in force on 2026-10-16 | GL_IA_20261001_V01 on GL_CW_20261001_V01 | `gl_engine/resolve/resolver.py:132` (`EditionResolver.resolve`) |
| Rule programs, in force | IA 15 files / 56 rules; CW 563 files / 4,557 rules; **effective 571 files, 4,590 rules** + `Default` (a state rule replaces a countrywide one by name) | `gl_engine/interp/program.py`, `interpreter.py:567-590` |
| Stored ISO answers, Iowa GL | **11**, all rated: 3 on 20240401, 3 on 20250401, 3 on 20260601, 1 on 20261001_V01, 1 on 20270401_V04. Plus 18 premium-only rows on 20260601 | `results/tc/answers/`, index `results/tc/reference_index.json` |
| Package samples | 1 (`STC/STC_GL000201550.json`, IA package) | corpus |
| ISO's rating service | `scripts/raas.py` `RaaS(lane=..., origin=..., override=...)`; ledger cap 250 a day: `active` 150, `refresh` 50, `adhoc` 50 | `console/ledger.py:23-24` |
| Expert reviewers | `gl-authority`, `gl-engine-code-expert`, `iso-circular-expert` (user-level agents, usable from this folder) | `~/.claude/agents/` |
| DEV-003 check (U8), for CG-6 | 3 risks dated 7/15/2025 (edition 20250401): **2,828 / 3,818 / 830**, ISO exact | `tests/verify_deviations_ufg_ia_gl.py`, `docs/deviations/FILINGS-LOG.md:108-118` |
| Engine entry | `Kernel.rate(payload, version=None, *, company=None, with_technical=False, graph=False, ...)`; no `WritingCompany` in the request = technical only | `gl_engine/rating/kernel.py:163, 186` |
| Rating graph (per rating) | `RatingGraph.to_json()`: input / write / table / company nodes; data / control edges | `gl_engine/interp/graph.py:275` |
| Rounding | Half-up by `@DecimalPlaces`; reuse `Interpreter.round_to` | `interpreter.py:444-458` |
| Look-ahead (OI-125) | **Property only**; not in GL | `cf_engine/run_checks.py:162-208` |

## 4. How ISO's rules map to the graph

The graph keeps Product Studio's six kinds and adds what ISO's rules need. Counts are uses in what Iowa's
in-force program can actually run, walked from its entry point as the engine calls rules (C-03,
`docs/INVENTORY.md`). The first draft counted only the state's copy of each rule and missed the countrywide copies
that `ErcProcess`, `InitializeRuleSet` and `CalculateTotalPremium` call after their own part, so loops were
undercounted by half. *Purpose* splits each hard instruction by ISO's rule names: rating, forms (`AttachForm...`),
messages.

| ISO instruction | Uses | Graph piece | Difficulty |
|---|---|---|---|
| `Value`, `Copy`, `Param` / `Arg` / `WithArgs` | 4,022 / 140 / 1,548 | **Input**, or an edge from an earlier step | Easy |
| `Lookup` + `Keys` | 2,306 | **Rate table** (loaded once, shared) + **Lookup** (keys, column, range keys) | Easy: table and column are named in the rule |
| `Sum`, `Product`, `Subtract`, `Divide`, `Max`, `Round`, `Truncate`, `Convert`, dates, text | 1,625 | **Rating step** | Easy |
| `RunRule` | 5,500 (12 of them call the countrywide copy of the same rule) | Inlined: the rule's steps are copied in where it is called | Easy: the rule is named |
| `If` / `Choose` / `When`, comparisons, `And` / `Or` | 3,356 / 124 / 315, 8,404 | **Condition** on the steps the branch decides (any step, not only charges) | Medium |
| `FirstValue`, `FirstNonNull` | 7,447 / 1,706 | A step that takes the first non-empty of its inputs | Medium |
| Fields written more than once | 2,251 fields written; 1,095 at more than one site, mostly one rule's branches; **41 written by two or more rules** (the true overwrites) | **Versions** of a value, as the rating graph keeps them | Medium |
| `ForEach` | 2,227 (rating 2,032, forms 174, messages 21) | **Repeating group**: steps repeated per location, class, coverage | **Hard**: the count isn't known until the request arrives |
| `Locate` with `Append` | 168 of 423 `Locate`: **43 truly add a record** (all rating, in 7 `InitializeRuleSet`-type rules); 125 only make sure row 1 exists (all forms) | **Record created during the rating** | **Hard** for the 43; the 125 are "ensure" |
| `Remove` | 62, **all forms** (a form attached, then taken off) | **Record removed during the rating**: later steps see fewer | **Hard**, but forms only |
| `Exist` / `NotExist` / `Count` | 387 / 226 / 61 (rating 378, forms 164, messages 132) | A test on which records exist **at that point in the order** | Medium-hard |
| `Break` | 4 (rating 1, forms 2, messages 1) | "Stop at the first match" condition | Medium |
| `Guid` | 134 (messages 125, rating 9) | A generated id; must be made repeatable for a comparison | Check |
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

## 6. The work, in release-candidate groups

Groups are named **CG-1 to CG-8** and tasks **C-01 onward**, so they never collide with the harness's RC / B
numbers. Each group ships as a unit and closes at its **release gate**. A gate that fails stops the next
group until fixed or re-scoped with the user. **CG-1 to CG-5 are ISO only, with no deviation (D8).** Each group
needs the user's go to start.

**Order:** CG-1 → CG-2 → CG-3 → CG-4 → CG-5 → CG-6 → CG-7. CG-8 waits on others.

| Group | What it delivers | Tasks | Days |
|---|---|---|---|
| CG-1 | Foundations: harness link, inventory, graph format, tables | C-01 to C-05 | 2-3 |
| CG-2 | Compiler, the straight-line part | C-06 to C-10 | 2-3 |
| CG-3 | Compiler, the hard part | C-11 to C-16 | 2-4 |
| CG-4 | Executor and the three-way loop | C-17 to C-20 | 2-3 |
| CG-5 | ISO technical passes until clean | C-21 to C-25 | 1-3 |
| CG-6 | DEV-003 on the graph | C-26 to C-27 | 1 |
| CG-7 | Product Studio view and findings | C-28 to C-31 | 2-3 |
| CG-8 | Waiting on someone else | — | — |

### CG-1 · Foundations (5 tasks)

**Release gate:** the harness imports cleanly from here; the inventory reproduces §3 and §4's counts for the
in-force edition and covers all 5 editions; every table the Iowa programs name loads; graph lookups equal the
engine's on 200 sampled keys, range keys included.

| # | Task | Size | Needs |
|---|---|---|---|
| ~~C-01~~ | ✅ **DONE 2026-10-16**: folder, local git, `CLAUDE.md`, plan sync, B-55 in the harness backlog | — | — |
| ~~C-02~~ | ✅ **DONE 2026-10-16**: **Harness link** `cg/harness.py`: the harness on the import path in one place; `GL_ERC_ROOT` / `CF_ERC_ROOT` / `CARRIERS_ROOT` set to the C: roots when unset, and refused if on F: (the engine's own defaults still name F:). `tests/verify_harness_link.py` 7 of 7: Iowa's sample (GL_IA_20261001_V01 over GL_CW_20261001_V01) rates $450 here and identically in the harness's own process | Small | — |
| ~~C-03~~ | ✅ **DONE 2026-10-16**: **Inventory** `cg/inventory.py` (`python -m cg.inventory`): all 5 editions walked from the entry point as the engine calls rules, 0 load errors; hard instructions by rule and purpose; writes by resolved field. Gate 18 of 18 (§3's census reproduced). Summary `docs/INVENTORY.md`. Found on the way: harness **OI-136** (477 corpus files past the Windows path limit; fixed in the harness) and the countrywide copies the first census missed (§4 corrected) | Small | — |
| C-04 | **Graph format** `cg/model.py`: input, rate table, lookup, step, condition, repeat group, record create / remove, premium; versions; JSON in and out | Small-medium | — |
| C-05 | **Tables as shared rate tables**, loaded once per edition through `load_table` / `ResolvedBook.table`; lookups with multi-key, range keys and interpolation | Medium | — |

### CG-2 · Compiler, straight-line (5 tasks)

**Release gate:** all 5 editions compile without a crash; every remaining hole is one of CG-3's instructions,
listed by rule.

| # | Task | Size | Needs |
|---|---|---|---|
| C-06 | **Rules inlined** from `Default` down (`RunRule`, `WithArgs` / `Arg` / `Param`); state rule over countrywide by name, as the engine does | Medium | — |
| C-07 | **Steps**: arithmetic, rounding, conversion, dates, text | Small | — |
| C-08 | **Conditions** from `If` / `Choose` / `When` and the tests under them, on every step a branch decides | Medium | — |
| C-09 | **First-of steps** (`FirstValue`, `FirstNonNull`) and **versions** for fields written more than once | Medium | — |
| C-10 | **Holes report**: every instruction not yet compiled, by rule and edition | Small | — |

### CG-3 · Compiler, the hard part (6 tasks)

**Release gate:** holes = 0 on all 5 editions, or each remaining one is a named finding (rule, instruction,
why it resists a fixed graph). This group is where the effort can grow.

| # | Task | Size | Needs |
|---|---|---|---|
| C-11 | **Repeating groups** for `ForEach` (2,227 in force, 2,032 of them rating): steps repeated per location, class, coverage | Medium-large | — |
| C-12 | **Records created** by `Locate` with `Append`: 43 that truly add a record (rating), 125 that only ensure row 1 (forms) | Medium | — |
| C-13 | **Records removed** by `Remove` (62, all forms): later steps see fewer | Medium | — |
| C-14 | **Tests in order**: `Exist` / `NotExist` / `Count` (674) answered as of their point in the run | Medium | — |
| C-15 | **Early exit**: `Break` (4) as "stop at the first match" | Small | — |
| C-16 | **Generated ids**: `Guid` (134) made repeatable so runs compare | Small | — |

### CG-4 · Executor and the loop (4 tasks)

**Release gate:** the IA sample rates end to end on the graph; one free pass runs on the 11 stored requests and
the sample, and writes its record.

| # | Task | Size | Needs |
|---|---|---|---|
| C-17 | **Executor** `cg/run.py`: rates a request on the graph in dependency order; half-up rounding from the harness; refuses where the engine refuses | Medium | — |
| C-18 | **The loop** `cg/loop.py`: the pass of §5: request set, ISO side (stored first), engine, graph, three-way difference field by field | Medium | — |
| C-19 | **Pass records** `results/passes/pass-NN.json` and §5's triage table (where each gap goes) | Small | — |
| C-20 | **Replay**: every plain arithmetic step re-computes from its inputs, as the rating graph's gate does | Small | — |

### CG-5 · ISO technical passes (5 tasks)

**Release gate: a clean pass**: graph = engine = ISO on every request, field for field, or each gap a recorded
finding. Harness defects found are logged in the harness's `docs/OPEN-ITEMS.md`.

| # | Task | Size | Needs |
|---|---|---|---|
| C-21 | **Pass 1, free**: the 11 stored requests on 5 editions + the IA sample | Small | — |
| C-22 | **Pass 2, free side**: Iowa requests generated by `scripts/variants.py` on all 5 editions; engine and graph only, and the list of requests with no stored ISO answer | Small-medium | — |
| C-23 | **Live gap**: ISO for C-22's uncovered requests; answers stored in the harness's answer store | Small | **your go**, ≤ 25 ISO calls a pass (lane `active`) |
| C-24 | **Fix and re-run** until clean; each gap placed by §5's table, expert reviewers where it isn't obvious | Medium | further passes may need calls, a go each |
| C-25 | **Hand-offs**: engine defects or ISO findings written up in the harness (OPEN-ITEMS, backlog) | Small | — |

### CG-6 · Deviations (2 tasks)

**Release gate:** U8's three risks on the graph equal **2,828 / 3,818 / 830**; the technical side and CG-5's
regression still clean. Starts only after CG-5 closes (D8).

| # | Task | Size | Needs |
|---|---|---|---|
| C-26 | **DEV-003 on the graph**: UFG's compiled rows (`Carriers\UFG\{UFC,ADD}\compiled\GL\IA\IA-GL-UNFG-134374972.v2`) as override tables: the loss cost multipliers, the policy minimum and the ELR row, applied as the engine applies them | Medium | — |
| C-27 | **Loop with the carrier side**: U8 through the three-way loop (ISO's U8 answers are stored); technical regression re-run | Small | — |

### CG-7 · Showing it, and what it means (4 tasks)

**Release gate:** findings reviewed with the user.

| # | Task | Size | Needs |
|---|---|---|---|
| C-28 | **Product Studio view** (absorbs harness B-31): export and a page drawing the graph in their six kinds, extras marked; one premium traced input to output, matching the harness worksheet | Medium | — |
| C-29 | **Measurements**: graph size per edition, rating time vs the engine, compile time | Small | — |
| C-30 | **Findings** `docs/FINDINGS.md`: what compiled, what didn't and why, engine defects the graph found, what §9's Federato questions need answered | Small | — |
| C-31 | **Next estimate**: effort to reach 51 GL states, Property (with the look-ahead), and a Product Studio load, replacing the 3-6 month range with measured numbers | Small | — |

### CG-8 · Waiting on someone else (parked until it arrives)

| Item | Waiting on |
|---|---|
| **Load the graph into Product Studio** (harness B-32 / B-34) | Federato: a way to load a graph without Excel (§9 F1), and a business reason |
| **§9's questions F1-F7** put to the Product Studio team | the user's call on when and who |
| **Property proof of concept** (brings in the look-ahead, OI-125) | CG-7's findings and the user's call |
| **More GL states** | CG-7's findings and the user's call |

## 7. Layout

```
ISOComputeGraph/
  CLAUDE.md          how this project relates to the harness
  docs/PLAN.md       this plan (master)
  docs/FINDINGS.md   CG-7
  docs/tracker.html  progress page, built from §6 (tools/tracker.py; sync rebuilds it)
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
| Records created and removed during a rating (§4) may not fit a fixed graph | That is the question being asked. CG-3 records each case as compiled or as a named finding |
| A compiled graph is a second implementation and can drift from ISO | The loop: every request goes to ISO, engine and graph, every pass, and the regression only grows |
| Only 1 stored ISO answer on today's edition | D5 and D7: 5 editions, 11 answers, and live calls for the gaps with a go per pass |
| Live calls share the harness's 250 a day | ≤ 25 a pass, lane `active`, with a go; the ledger refuses a full lane |
| `Guid` makes ids differ run to run | Compare by field, not by generated id; seed if needed |
| 18 countrywide rule-file paths are 260+ characters | Read through the harness's own loader; any script reading files directly uses the `\\?\` prefix |
| 16 GB PC | Passes run one process at a time, 2 workers max |

## 9. Questions for Federato (collected for CG-7, not asked yet)

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
| 2026-10-16 | Plan drafted; D1-D5 taken; setup done (now C-01) |
| 2026-10-16 | Revised by the user: the harness loop three ways (D6), stored answers then live with a go per pass (D7), ISO without deviation first, DEV-003 moved after the technical loop (D8) |
| 2026-10-16 | Re-organised into release-candidate groups CG-1 to CG-8, tasks C-01 to C-31 (C-01 done). About 12-20 days. Waiting for the go on CG-1 |
| 2026-10-16 | C-02 done: `cg/harness.py`; `verify_harness_link.py` 7 of 7 (Iowa sample $450, same as the harness at home). CG-1 left: C-03, C-04, C-05 |
| 2026-10-16 | C-03 done: inventory of 5 editions, gate 18 of 18. §4 corrected (reachable program: 2,227 loops, not 1,030; `Remove` and most `Append` are forms only; 41 true overwrites). Harness OI-136 found and fixed (files past the Windows path limit). CG-1 left: C-04, C-05 |
