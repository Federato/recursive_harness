<!-- COPY. Master: C:\FederatoProjects\ISOComputeGraph\docs\PLAN.md. Do not edit here; edit the master and run tools/sync_plan.py. -->

# ISO compute graph — proof of concept plan

**Status (2026-10-19): CG-1 to CG-7 complete; GL in every jurisdiction planned as CG-9 to CG-12 (§11; decisions D9-D12 and the go for CG-9 needed; D13, the graph as a rating engine, in CG-12) (C-01 to C-31 done; 31 of 31
tasks); CG-7 signed off by the user (findings and estimate reviewed; C-31: `docs/ESTIMATE.md`, all 51 GL jurisdictions compile with 0 holes; C-28: the graph drawn in Product Studio's kinds, `docs/studio.html`; C-29: `docs/MEASUREMENTS.md`, 2 to 3 s to compile an edition, rating 1.13x the engine; C-30: `docs/FINDINGS.md`). **DEV-003 sits on the graph as data** (CG-6): UFG's LCMs, its ELR
override table and its policy minimum in front of the edition's graph, nothing recompiled; U8 three ways 2,828 / 3,818
/ 830. Every instruction in ISO's Iowa GL programs compiles into the graph (0 holes in all 5 editions); whole requests
rate on it equal to the engine, field for field. **Pass 12** (`results/passes/pass-12.json`, C-27's technical regression): 362 requests on all 5
editions, graph = engine on every one, **every one with ISO's answer** (339 live, C-23): 356 premiums equal three ways
with every published field and message, 5 refused by ISO where ours refuses, exit clean. Two gaps with ISO, both the
engine's, written up in the harness (C-25): the GL form labels (harness **OI-137**, OI-106 not carried to GL) and **one request ISO refuses that ours rates**
(aggregate 200,000: a missed ILFPremOps lookup goes on as a null, harness **OI-96**, ISO's answer added). Organised in release-candidate groups CG-1 to CG-8 (§6).**
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
| D7 | ISO calls | **Stored answers first, then live**: each pass runs free on the stored answers; live calls only for requests the stored set doesn't cover, through the harness's call ledger (lane `active`, shown as *Planned work*, origin `iso-compute-graph`), **up to 25 a pass, with the user's go per pass**. *2026-10-18, the user:* live calls in fixed groups of **50**, one group per go (`cg/live.py`) |
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

**Order:** CG-1 → CG-2 → CG-3 → CG-4 → CG-5 → CG-6 → CG-7. CG-8 waits on others. **Then GL in every
jurisdiction (added 2026-10-19, §11):** CG-9 → CG-10 → CG-11 → CG-12.

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
| CG-9 | GL everywhere: the ground work (leak fixed, state as a parameter, every edition compiled) | C-32 to C-35 | 2-3 |
| CG-10 | GL everywhere: free passes (stored answers and generated requests, no calls) | C-36 to C-38 | 1.5-2.5 |
| CG-11 | GL everywhere: ISO live, in waves | C-39 to C-40 | 1-2, over 3-5 weeks of calls |
| CG-12 | GL everywhere: findings, **the graph as a rating engine of its own**, and close | C-41 to C-46 | 3.5-5 |

### CG-1 · Foundations (5 tasks) — ✅ COMPLETE 2026-10-16

**Release gate:** the harness imports cleanly from here; the inventory reproduces §3 and §4's counts for the
in-force edition and covers all 5 editions; every table the Iowa programs name loads; graph lookups equal the
engine's on 200 sampled keys, range keys included.

| # | Task | Size | Needs |
|---|---|---|---|
| ~~C-01~~ | ✅ **DONE 2026-10-16**: folder, local git, `CLAUDE.md`, plan sync, B-55 in the harness backlog | — | — |
| ~~C-02~~ | ✅ **DONE 2026-10-16**: **Harness link** `cg/harness.py`: the harness on the import path in one place; `GL_ERC_ROOT` / `CF_ERC_ROOT` / `CARRIERS_ROOT` set to the C: roots when unset, and refused if on F: (the engine's own defaults still name F:). `tests/verify_harness_link.py` 7 of 7: Iowa's sample (GL_IA_20261001_V01 over GL_CW_20261001_V01) rates $450 here and identically in the harness's own process | Small | — |
| ~~C-03~~ | ✅ **DONE 2026-10-16**: **Inventory** `cg/inventory.py` (`python -m cg.inventory`): all 5 editions walked from the entry point as the engine calls rules, 0 load errors; hard instructions by rule and purpose; writes by resolved field. Gate 18 of 18 (§3's census reproduced). Summary `docs/INVENTORY.md`. Found on the way: harness **OI-136** (477 corpus files past the Windows path limit; fixed in the harness) and the countrywide copies the first census missed (§4 corrected) | Small | — |
| ~~C-04~~ | ✅ **DONE 2026-10-16**: **Graph format** `cg/model.py` (`iso-compute-graph/1`): Product Studio's six kinds (input, rate table, lookup, step, condition, write / premium) plus marked extras (constant, group, aggregate, create, ensure, remove, message); guards for branches, `seq` for ISO's run order, versions per field (a later step names the write it saw), `src` back to ISO's rule; validation, dependency order, JSON. `tests/verify_model.py` 23 of 23: Product Studio's own example, an ISO-shaped graph with every extra, byte-exact round trip, 13 malformed shapes refused | Small-medium | — |
| ~~C-05~~ | ✅ **DONE 2026-10-16**: **Tables as shared rate tables** `cg/tables.py`: one object per (package, kind, name), parsed by the harness; the graph's own `lookup` (equality, undeclared, banded, linear interpolation, FirstResult / SingleResult) written from contract §7. `tests/verify_tables.py` 12 of 12: every table the 5 editions' reachable programs name loads (188, 168 in 2027); **1,000 of 1,000** sampled lookups equal the engine's `Interpreter.lookup` (249 banded, 39 interpolated, 100 misses); two editions on one parent share its 154 tables. None of the 5 editions shares a parent with another, so sharing was proved on 20260401 / 20260601 | Medium | — |

### CG-2 · Compiler, straight-line (5 tasks) — ✅ COMPLETE 2026-10-16

**Release gate:** all 5 editions compile without a crash; every remaining hole is one of CG-3's instructions,
listed by rule.

| # | Task | Size | Needs |
|---|---|---|---|
| ~~C-06~~ | ✅ **DONE 2026-10-16**: **Rules inlined** `cg/inline.py`: every `RunRule` replaced by a copy of the rule it reaches (state first, countrywide when the state has none, `@ProjectName` to the countrywide copy; `MessageHelper` kept as a builtin), every `@FromParam` read linked to the `Arg` that binds it, data path and write record carried on each op. In force: 92,014 ops, 5,732 inlined calls of 4,575 rules. `tests/verify_inline.py` 15 of 15: 5 editions, 0 missing rules, 0 unbound parameters, 0 recursion; every one of 14,369 rule calls the engine made rating the 11 stored Iowa ISO requests and the 5 package samples is in the inlined program, from the same package | Medium | — |
| ~~C-07~~ | ✅ **DONE 2026-10-16**: **Steps** `cg/ops.py` (what each step computes, written from the contract for GL's settings: a null in arithmetic is refused, not zero; `Sum` / `Max` skip nulls and spread a loop's values) and `cg/lower.py` (lowering begins: steps and constants become nodes, anything not lowered yet a `hole`). `tests/verify_steps.py` 7 of 7: **3,780 of 3,780** trials over all 63 step shapes the 5 editions file (15 instructions) equal the engine's own evaluators, nulls, bad text, zero divisors, leap days and loop values included; every step instruction in the 5 inlined programs is a step node with operands in filed order | Small | — |
| ~~C-08~~ | ✅ **DONE 2026-10-16**: **Conditions** in `cg/lower.py`: each `If` / `When` test a `condition`; everything inside a branch guarded by it on top of the guards around it; a `When`'s test guarded by every earlier `When` failing; the branch value out through `Choose`. Tests (comparisons, null tests, `And` / `Or`, ISO's 01/01/0001 date sentinel) in `cg/ops.py`; `cg/evalexpr.py` is a lazy, guard-aware reference evaluator that grows into the executor. **Laziness is part of the meaning:** ISO evaluates only the branch it takes, stops a `Choose` at the first true test, short-circuits `And` / `Or`, and inside a step stops at the first operand that refuses; the graph does the same. `tests/verify_conditions.py` 8 of 8: 59,775 test trials, 990 branch trials, and **15,243 trials over every non-constant expression of the in-force edition** (3,316 `If`) equal the engine, **with the same parts reached in the same order**; 3,853 conditions in force = 3,538 `If` + 315 `When`, every node in a branch guarded by it. Found and fixed on the way: constants typed as text in the evaluator; steps evaluating every operand where ISO stops at the first refusal; dependency ordering quadratic (now a heap) | Medium | — |
| ~~C-09~~ | ✅ **DONE 2026-10-16**: **Data, calls and versions** in `cg/lower.py` / `cg/paths.py` / `cg/evalexpr.py`: every `ToDataDef` a `write` (run order, version per field), paths resolved to the exact field (a loop's current record marked); a read takes **the newest earlier write that actually happened**, else the request's value; `FirstValue`, `FirstNonNull` (a null-arithmetic branch abandoned, OI-88), parameters, `Call` (arguments first, then the body, typed by the rule), `Seq`, lookups on shared rate tables, ISO's messages, the null-premium refusal. `tests/verify_calls.py` 10 of 10 on all 5 editions: **22,500 of 22,500 trials over 7,500 rule calls** run by the graph and by ISO's real rule in the engine, on real Iowa request values: same value or refusal, same number of writes, same final text in every field written (about 2,100 trials with writes, 4,700 lookups, 320 reads of an earlier write per edition); a mutant whose reads ignore earlier writes fails 165 trials. Messages not yet exercised: every message rule in force also uses a `Guid` (CG-3) | Medium | — |
| ~~C-10~~ | ✅ **DONE 2026-10-16**: **Holes report** `cg/holes.py` → `docs/HOLES.md`; `tests/verify_holes.py` (CG-2's gate) 5 of 5: every edition valid, 0 unresolved paths, **only CG-3 instructions left** (in force 4,157 holes: `ForEach` 2,429, `Exist` 580, `Locate` 581, `NotExist` 305, `Guid` 134, `Remove` 62, `Count` 61, `Break` 4, `GetList` 1). **4,960 of 4,964 writes sit inside one**, so no whole policy rates on the graph before CG-3 | Small | — |

### CG-3 · Compiler, the hard part (6 tasks) — ✅ COMPLETE 2026-10-16

**Release gate:** holes = 0 on all 5 editions, or each remaining one is a named finding (rule, instruction,
why it resists a fixed graph). This group is where the effort can grow.

| # | Task | Size | Needs |
|---|---|---|---|
| ~~C-11~~ | ✅ **DONE 2026-10-16**: **Loops as repeating groups** in `cg/lower.py` / `cg/evalexpr.py` / `cg/paths.py`: each `ForEach` is a `group` (`over` = the records it walks, its own current record marked `@g<id>`) and a `Collect` aggregate that runs it once per record present **when the loop is reached**, yielding what ISO's loop yields (several values per pass, OI-127). In force **2,429 loops, 0 left as holes**; every node from a loop's body sits in its group. A read's possible writes now include writes made inside another loop, brought out by a `Last` aggregate (972 in force), and, inside a loop, a write from an earlier pass (`carried`, a link back to the previous record, kept out of the inputs so the graph has no cycle: 1 read in force, in a message rule). Which write a read saw is decided when the rating runs, by exact field. `tests/verify_loops.py` 28 of 28: all 5 editions; **11,772 of 11,772 trials over 3,924 rule calls with loops** equal ISO's real rules in the engine on requests with 0 to 3 records at each loop step (value or refusal, writes, final text of every field, messages); a mutant that runs each loop over its first record only fails 1,819 of the 4,339 trials where a loop met several records; **8 built shapes, 2,400 of 2,400** (a loop's write read later, sibling and nested loops, a running total carried record to record, a loop reading one record and writing the one around it, several values per pass, a loop's values refused in arithmetic); without the carried link 127 of 300 running-total trials fail. Not yet reachable on real rules: all 2,230 reads of another loop's write in force sit in rule calls that also hold a record instruction (C-12 to C-14). **Findings for Product Studio:** a repeating group needs (1) a way to read a value a group wrote, after it, by record; (2) a value carried from one record to the next | Medium-large | — |
| ~~C-12~~ | ✅ **DONE 2026-10-16**: **Records** in `cg/lower.py` (`_locate`) / `cg/evalexpr.py`: an unindexed `Locate Append` is a `create` and a group of one new record (row one past those present when the run reaches it; its body fills it, and a read of it from outside comes through a `Last` aggregate, as from a loop); any other `Locate` is an `ensure` (the record made to exist with the rows before it, as the engine's `tree.ensure`) with its body run there. In force **581 `Locate`: 122 records added (the 43 filed sites, all rating) + 459 made sure of, 0 left as holes**. `tests/verify_records.py` 33 of 33, now also comparing **every record and field present afterwards**: all 5 editions; **7,335 of 7,335 trials over 2,445 single `Locate`s** (all 122 that add a record, 1,827 records added) equal the engine, and a mutant that adds no record and makes sure of nothing fails (390 trials in force); 270 of 270 trials over the 90 whole rule calls whose only CG-3 instructions are loops and records; **8 built shapes, 2,400 of 2,400** (a record added per location and summed, two added and the second read back, one added inside another, `[1]` appends that must not repeat, a missing record made to exist and looped over, moving to a record inside a loop). The rest of the real `Locate`s sit in rule calls that also test for records (C-14) | Medium | — |
| ~~C-13~~ | ✅ **DONE 2026-10-16**: **Records removed** in `cg/lower.py` (`_remove`) / `cg/evalexpr.py`: a `Remove` is a `remove` effect that takes away every row of its last step's name under each parent its path finds when the run reaches it; afterwards the request's values and earlier writes there are gone (a read sees null), loops skip those rows, and a later attach starts a fresh record. All 62 in force (61 form lists, all forms) remove a whole list, so no row that stays is renumbered; a `Remove` naming one row would stay a hole (none filed in Iowa). `tests/verify_removes.py` 21 of 21: all 5 editions, 0 left as holes; every rule that removes also tests for records (C-14), so each real `Remove` runs on its own at the record it runs at: **1,770 of 1,770 trials over 295 real `Remove`s** (2,306 records removed) equal the engine, records present after included, and a mutant that removes nothing fails all 1,420 trials where something was removed; **6 built shapes, 1,800 of 1,800** (remove then read, a write before the remove read after it, remove then attach again, a loop after a remove, a remove inside a loop over the parents, a remove of nothing). Comparisons now use the fields as they stand after the run (`Evaluator.final`) | Medium | — |
| ~~C-14~~ | ✅ **DONE 2026-10-16**: **Tests in order** in `cg/lower.py` / `cg/evalexpr.py`: `Exist` / `NotExist` / `Count` are steps on the records present **when the run reaches them** (rows added, made sure of, removed, written so far); each lists the effects that can have changed its answer (`sees`; `sees_carried` from an earlier pass of a loop, none in Iowa). In force **946 tests, 0 left as holes; 866 can be changed by an earlier effect**. Only 139 holes remain in force: 134 `Guid`, 4 `Break`, 1 `GetList` (C-15, C-16). `tests/verify_tests.py` 23 of 23: all 5 editions; **6,432 of 6,432 trials over 2,144 whole rule calls** (every call with a test and nothing left unlowered) equal ISO's real rules in the engine, fields and records present after included; these whole calls also run the real record instructions deferred from C-12 / C-13 (1,723 records added, 2,539 removed); no test answer ever changed without an effect it lists having happened first. Inside one testable call a test's answer never changed: the test / effect pairs that can change one sit in calls that also make message ids (C-16) or meet only across the whole program (CG-4), where this check runs again. **6 built shapes, 1,800 of 1,800** (a test after an append, after a remove, a count of records added in a loop, before and after an add, attach-once inside a loop, `ancestor::`): 1,296 answers changed during the run, each after an effect the test lists; a mutant answering tests from the request alone fails 301 of 600 | Medium | — |
| ~~C-15~~ | ✅ **DONE 2026-10-16**: **Early exit** in `cg/lower.py` / `cg/evalexpr.py` / `cg/ops.py`: a `Break` is a step naming the loop or `GetList` it leaves (`exits`); when reached it raises the engine's own stop signal, which travels up exactly as in ISO to the nearest loop (that pass yields, the loop stops) or `GetList`; a `Sum` it passes through hands up its total so far (OI-108). In force 4 `Break` + 1 `GetList` (2 college-school form rules, the highest limited-products-withdrawal ILF flag, a workers-compensation message), **0 left as holes; only the 134 `Guid` remain**. `tests/verify_breaks.py` 17 of 17: 4 editions file them (2027 none); **4,000 of 4,000 trials** over the rule calls and loops holding them equal the engine (166 breaks taken); a mutant whose `Break` does nothing fails 37 of the 122 real trials that broke; the message rule's loop also makes a message id and waits for C-16. **6 built shapes, 1,800 of 1,800** (stop at the first match, `Sum(x, Break)`, an inner loop's break, a `GetList` stopped part way, several values in a pass that breaks, a break never reached); the do-nothing mutant fails 112 of 600 | Small | — |
| ~~C-16~~ | ✅ **DONE 2026-10-16**: **Generated ids** in `cg/lower.py` / `cg/evalexpr.py`: a `Guid` is a step giving the run's next id in run order, in the engine's seeded form (`{n:08x}-0000-0000-0000-000000000000`), so two runs of one request compare exactly (ISO's own ids are random: a comparison with ISO must not compare them, C-18). All 134 in force number ISO's message rows (`ErcMessageTableId`). **CG-3's release gate met: 0 holes in all 5 editions** (in force 98,185 nodes). `tests/verify_ids.py` 23 of 23: **30,640 of 30,640 trials over the 766 rule calls that make ids** (ISO's message rules; 1,446 ids made, 13,035 messages raised) and **22,500 of 22,500 trials over 7,500 rule calls sampled from all** equal ISO's real rules in the engine; a mutant giving every id the same value fails all 8 real trials that made two, and 63 of 100 on a built shape (an id per message row in a loop, 300 of 300). Still not seen on real rules, because it happens only across a whole policy (CG-4): a test answer changed by an earlier effect, and a value carried from one record to the next | Small | — |

### CG-4 · Executor and the loop (4 tasks) — ✅ COMPLETE 2026-10-18

**Release gate:** the IA sample rates end to end on the graph; one free pass runs on the 11 stored requests and
the sample, and writes its record.

| # | Task | Size | Needs |
|---|---|---|---|
| ~~C-17~~ | ✅ **DONE 2026-10-18**: **Executor** `cg/run.py` (`GraphRater().rate(request)`): the engine's own steps with the rules replaced by the graph. The request becomes the engine's tree and edition (a writing company refused until CG-6); the engine's request checks run in place (OI-134, OI-130); the edition's graph (compiled once, kept; 2-4 s, about 240 MB) runs from its top node in ISO's run order, each node after the inputs it asks for; the rated tree is rebuilt from what the run left and the engine's after-checks read it in place (OI-129, OI-94, total and check figure, coverages). Half-up rounding, checked against the engine's mode at import. A rating takes 0.2-0.8 s. `tests/verify_run.py` 28 of 28: all 5 editions compile whole; **5 package samples and 11 stored ISO requests** (3 / 3 / 3 / 1 / 1 by edition) equal the engine: premium, coverages, messages and **every field of the rated tree**, message ids included (12,260 / 452 / 450 / 450 / 648; 785 / 3,500 / 2,592 / 2,828 / 3,818 / 830 / 782 / 3,597 / 8,016 / 8,016 / 7,970); **240 of 240 variants** (a field dropped, changed or junk, a record repeated) equal the engine, refusals at the same point: 158 rated, 48 refused before the rules, 27 while they ran, 6 after them, 1 with no edition; a mutant rounding half-even differs on 11 of the 158 rated. Only the OI-94 explanation is shorter (it names the empty table from the engine's trace, which the graph does not keep) | Medium | — |
| ~~C-18~~ | ✅ **DONE 2026-10-18**: **The loop** `cg/loop.py` (`Loop().run(request_set())`, `python -m cg.loop`): the request set (every stored Iowa GL request in the harness's answer store, each edition's package sample); ISO's side found as the harness finds it (`console.store.lookup`, by request hash), no live call (a request with no stored answer is listed, the list for C-23); engine and graph; the difference three ways: outcome and premium, edition, every field ISO publishes (aligned by the harness's worksheet map, `console.worksheet`: numbers by value, dates in either format, generated ids never differ), ISO's messages as a set, and graph against engine on every field of the rated tree. Each difference keeps the three values and which pairs agree, labelled `G=E=I` / `G!=E=I` / `G=I!=E` / `G=E!=I` / `G!=E!=I` for §5's table (C-19). `tests/verify_loop.py` 20 of 20: **16 requests (11 with ISO's answer, ISO's edition = ours on all 11)**; graph = engine on all 16 (7,626 tree fields); **the three premiums agree on all 11**; 3,959 published fields compared; **156 differences left, all `G=E!=I`, all form labels**: `ErcFormName` / `ErcFormNumber` read "Value Not Found" in the engine (and so the graph) where ISO prints the form (harness **OI-106**, closed for Property on 2026-10-05 by `CFResolvedBook._form_pages`; GL's book still resolves `FormPage` wholesale; no premium or message effect; for C-25). 12 built cases on one stored request's real ratings: each change found with the right label (graph wrong, engine wrong, both off ISO, all three apart, a field left out, a premium, a refusal on either side, a message), and 785.0 / 785, two date formats, ids, an ISO-only zero not counted | Medium | — |
| ~~C-19~~ | ✅ **DONE 2026-10-18**: **Pass records** `cg/passes.py` (`python -m cg.passes`): every difference placed by §5's table (`G!=E=I` here, `G=I!=E` harness, `G=E!=I` harness or ISO, `G!=E!=I` judge first, graph against engine with no ISO answer here) and matched against the **recorded findings** `docs/KNOWN-GAPS.json` (one so far: OI-106 on GL, the form labels); a pass **exits clean** when every difference is a recorded finding. `results/passes/pass-NN.json`, numbered from 00, never rewritten: kind, when, both commits, editions, the triage table, the findings in force, every request's three outcomes and every difference with its values, label, destination and finding; the summary lists the requests with no stored ISO answer (C-23's live gap). `tests/verify_passes.py` 11 of 11. **CG-4's record `pass-00.json`**: 16 requests (11 with ISO's answer), 5 clean, 156 differences all `OI-106-GL`, **exit clean**; 5 with no ISO answer (the package samples) | Small | — |
| ~~C-20~~ | ✅ **DONE 2026-10-18**: **Replay** `cg/replay.py`: after a run, every `Sum`, `Product`, `Subtract`, `Divide`, `Max` and `Round` step that gave a number, at every record it ran at, is re-computed from the values on its input edges with arithmetic written apart from the executor's (loops' values spread, nulls skipped where ISO skips them, half-up to `@DecimalPlaces`); a step that gave a number with an input never asked for is wrong, not skipped. `tests/verify_replay.py` 4 of 4: **5,916 of 5,916 steps replay** over 32 runs (the 16 requests, and each with a record repeated so loops walk several), 3 skipped (a `Round` that gave nothing); a `Product` that forgets to round is caught on 12 of 12 requests, a `Sum` that leaves out an operand on all 10 it changes | Small | — |

### CG-5 · ISO technical passes (5 tasks)

**Release gate: a clean pass**: graph = engine = ISO on every request, field for field, or each gap a recorded
finding. Harness defects found are logged in the harness's `docs/OPEN-ITEMS.md`.

| # | Task | Size | Needs |
|---|---|---|---|
| ~~C-21~~ | ✅ **DONE 2026-10-18**: **Pass 1, free** (`results/passes/pass-01.json`): the 11 stored requests on 5 editions, the 5 package samples, and the harness's **premium-only ISO rows** for Iowa rebuilt (`cg/requests.py`): of 18, 5 are a stored request already, 1 a repeat, **12 rebuilt** by the harness's own builder (`scripts/variants.py`, as `sweep.py` built them) and kept only because the engine prices each today as it did when ISO was asked (0 moved). 28 requests, **graph = engine on all 28, the 23 ISO premiums (12 premium only) equal three ways**, exit clean (156 form-label gaps, OI-106-GL). `tests/verify_pass1.py` 5 of 5 | Small | — |
| ~~C-22~~ | ✅ **DONE 2026-10-18**: **Pass 2, free side** (`pass-02.json`, re-run as `pass-03.json`): pass 1's requests and **334 Iowa requests generated** by `scripts/variants.py` on all 5 editions (65 / 63 / 67 / 69 / 70: every control's declared options one at a time, up to 3 each and 6 class codes, prerequisites set; then 15 mixes of 2 to 4 controls an edition; 77 configurations an edition cannot express, 78 repeats; seeded, rebuilt to the same requests by hash, each request keeps its config). Pass 2 left **5 gaps, placed here**: the same refusals (3 null in arithmetic, 2 OI-94) worded differently, the engine naming the instruction or the empty table from its trace; **fixed here** (the loop compares a refusal by kind and code, as C-17 does). **Pass 3**: 362 requests, **graph = engine on all 362** (357 rated, 5 refused; 174,891 tree fields), the 23 ISO premiums equal three ways, exit clean. **Live gap: 339 requests with no stored ISO answer** (334 generated, 5 samples), 14 passes at 25. `tests/verify_pass2.py` 7 of 7 | Small-medium | — |
| ~~C-23~~ | ✅ **DONE 2026-10-19**: **Live gap** `cg/live.py`: pass 3's 339 requests with no stored ISO answer in **7 fixed groups of 50** (the user's size; 50 x 6 + 39; `results/passes/live-groups.json`; group 1 leads with the 5 package samples and the 5 requests our side refuses, then each group takes the editions in turn); each request rebuilt and checked by hash before it is sent, stored answers first, every call through the harness's client (lane `active`, origin `iso-compute-graph`), answers in the harness's answer store. **Group 1 sent 2026-10-18 (50 calls): 45 rated, every premium equal; 5 refused by ISO at the same lookup ours refuses** (ILFPremOps for aggregates 50,000 / 20,000,000 / 300,000; the size-of-risk loss cost, OI-94). Pass 4 counted the 5 samples twice (as stored too), fixed here: a request this project sent keeps its own source. **Pass 5**: the same 362 requests, graph = engine on all, 73 ISO answers equal three ways (16,793 published fields of the 50 new compared), exit clean (860 form-label gaps, OI-106-GL). **Group 2 sent 2026-10-19 (50 calls): 50 rated, every premium equal.** **Pass 6**: the same 362 requests, graph = engine on all, 123 ISO answers equal three ways (35,009 published fields of the 100 live compared), exit clean (1,610 form-label gaps, OI-106-GL). **Groups 3 and 4 sent 2026-10-19 (100 calls, one go for both): 100 rated, every premium equal.** **Pass 7**: the same 362 requests, graph = engine on all, 223 ISO answers equal three ways (77,481 published fields of the 200 live compared), exit clean (3,082 form-label gaps, OI-106-GL). `tests/verify_live.py` 10 of 10. **Groups 5-7 sent 2026-10-19 (139 calls; the user waived the day's cap, logged as an override on each call; 289 calls that day): 138 rated, every premium equal; 1 refused by ISO where ours rates 5,001** (`20270401:2ae2de039bc7`, aggregate 200,000, basis Each Scout: ISO stops at the ILFPremOps lookup; the engine's lookup misses too but its null never reaches arithmetic, so Prem/Ops goes on, `FinalILF` 0.007, as harness **OI-96** describes; graph = engine). **Pass 8** exit open on that one; placed `G=E!=I`, harness, recorded as **OI-96-GL** (`docs/KNOWN-GAPS.json`, matched by ISO's refusal text, new key `iso_says`). **Pass 9**: 362 requests, all with ISO's answer, graph = engine on all, 131,548 published fields of the 339 live compared, exit clean (5,102 form labels OI-106-GL, 1 refusal OI-96-GL). `tests/verify_live.py` 13 of 13, `tests/verify_passes.py` 12 of 12 (the live-gap check now follows the store) | Small | — |
| ~~C-24~~ | ✅ **DONE 2026-10-19**: **Fix and re-run** until clean; each gap placed by §5's table, expert reviewers where it isn't obvious. **Nothing left to fix here:** pass 9 had no open difference; its two gaps were placed by trace, not judgement (graph = engine on the rated tree, ISO's refusal names the table and line), so no reviewer was needed, and written up in the harness (C-25: OI-137, OI-96). **Re-run:** the whole regression, 22 tests one at a time, every one passing; `verify_run` brought back to C-17's scope first (with C-23's 339 answers in the store it rated 350 requests and their variants and reached 8 GB on this PC; the live answers are the passes' and `verify_live`'s), 28 of 28 again. **Pass 10** at `13528eb`: 362 requests, all with ISO's answer, graph = engine on all, exit clean (5,102 OI-106-GL, 1 OI-96-GL), `verify_live` 13 of 13. No ISO calls | Medium | — |
| ~~C-25~~ | ✅ **DONE 2026-10-19**: **Hand-offs**: engine defects or ISO findings written up in the harness (OPEN-ITEMS, backlog). Harness `cba394d`, docs only: **OI-137** raised (GL form names and numbers "Value Not Found": 5,102 fields on 344 of 362 Iowa requests; OI-106's `FormPage` merge is in `cf_engine` only, `gl_engine/resolve/book.py` unchanged since `8d9bd9b`); **OI-96** gets ISO's live answer to its engine-side question (a missed `ILFPremOps` lookup refuses at the lookup; ours prices $5,001). Backlog B-55 note added. `docs/KNOWN-GAPS.json` points at both. Each fix is the harness's, with its own go | Small | — |

### CG-6 · Deviations (2 tasks)

**Release gate:** U8's three risks on the graph equal **2,828 / 3,818 / 830**; the technical side and CG-5's
regression still clean. Starts only after CG-5 closes (D8).

| # | Task | Size | Needs |
|---|---|---|---|
| ~~C-26~~ | ✅ **DONE 2026-10-19**: **DEV-003 on the graph**: UFG's compiled rows (`Carriers\UFG\{UFC,ADD}\compiled\GL\IA\IA-GL-UNFG-134374972.v2`) as override tables: the loss cost multipliers, the policy minimum and the ELR row, applied as the engine applies them. `cg/carrier.py`; `GraphRater.rate` rates a request naming a writing company twice, technical and carrier, as `Kernel._rate_company` does. The filing is read by the harness's reader (`plan_for`); its rows become three pieces in front of the edition's graph, which is **not touched or recompiled** (the same object before and after): **LCM inputs** (2,376 rows by coverage and class, plus the "all other classes" row, written into each Prem/Ops and Products record's `LCM` before the rules), **override tables** (`CarrierTables`: `ExpectedLossRatio` CW/Y `Factor` 0.686 in front of ISO's 1; ISO's shared table untouched; a key the edition lacks refuses up front) and the **policy minimum** after the rules ($500 UFC, $625 Addison, the top-up its own line). Submitted LCMs removed and named (D13). The waterfall and changed paths are the harness's report, built from the graph's own re-ratings. `tests/verify_carrier.py` 14 of 14: U8's three on the graph **2,828 / 3,818 / 830** (= engine = ISO); 38 cases (both companies; ordinary, "a"-rated, experience-rated, small, either side of both effective dates, no policy type, a submitted LCM, the 2026-10 and 2027-04 editions, 16 filed classes at random) equal the engine's carrier and technical on every field, message and part, and the whole deviation report; refusals equal (a policy type that is neither, an override the edition lacks); each piece left out is caught (2,987 / 110,687 / 77 against 2,828 / 117,775 / 625) | Medium | — |
| ~~C-27~~ | ✅ **DONE 2026-10-19**: **Loop with the carrier side**: U8 through the three-way loop (ISO's U8 answers are stored); technical regression re-run. Request kind `carrier` (`cg.requests.carrier`, `--kinds carrier`): ours is a request naming the company with no LCMs, rated technical and carrier; ISO's side is its stored answer to the request it was asked (UFG's LCMs written in, the harness's `gl_carrier_request`), found by hash; no ISO call. **Pass 11** (`pass-11.json`; run just before its code was committed, so stamped `de3c42b+dirty`; the code is `adbca70`): U8's three risks, ISO = engine = graph **2,828 / 3,818 / 830**, graph = engine on all 1,370 tree fields, 1,104 published fields compared with ISO, exit clean: 44 form labels (OI-106-GL) and 3 `ERPExpectedLossRatio` fields judged **by design** (ours reads UFG's filed ELR 0.686, ISO asked without it reads 1: the filing's v2 items never go to ISO, harness D21; not experience-rated, so no premium moves), recorded as `DEV-003-ELR` (matches only the filed 0.686). `tests/verify_carrier_loop.py` 6 of 6. **Technical regression:** pass 12 clean (362 requests, the same findings as pass 10: the carrier layer moved nothing technical); all 24 tests pass, one at a time | Small | — |

### CG-7 · Showing it, and what it means (4 tasks) — ✅ COMPLETE 2026-10-19

**Release gate:** findings reviewed with the user.

| # | Task | Size | Needs |
|---|---|---|---|
| ~~C-28~~ | ✅ **DONE 2026-10-19**: **Product Studio view** (absorbs harness B-31): export and a page drawing the graph in their six kinds, extras marked; one premium traced input to output, matching the harness worksheet. `cg/studio.py` (`python -m cg.studio`): **export** of every edition's graph with each node in Product Studio's kinds or marked extra (`results/studio/<edition>.json`, ~35 MB each, rebuilt on demand) and a census: e.g. 2025-04-01 has 96,319 nodes, 68,407 in the six kinds (3,005 policy inputs, 188 rate tables, 4,760 lookups, 56,100 rating steps, 3,814 conditions, 540 premiums) and 27,912 extras (20,912 constants, 2,496 loop groups, 3,751 aggregates, 619 record changes, 134 messages). **A premium traced** from the run itself: of a full upstream of ~6,500 nodes (mostly plumbing and branches that never ran) only the named values are kept (inputs, tables, lookups with their keys, each written field with its value and formula, the conditions that let each happen); a read is followed to the write it actually saw, matched by the value it got. E.g. UFC 18501 Prem/Ops **$2,798** = round(FinalRate 2.763 × exposure 1,000,000 ÷ 1000 + MedicalPaymentsCharge 35), FinalRate = BaseRate × FinalILF × mods, BaseRate = PremOpsLossCost (lookup by state, territory, class) × LCM. **The page** `docs/studio.html` (published as a private artifact, https://claude.ai/artifact/KN4qMUYDy1pZB1WPGfdBLy): census per edition, four premiums drawn left to right like Federato's illustration (hover shows what feeds a value and what it feeds; conditions on a toggle), and each traced field beside the harness worksheet. `tests/verify_studio.py` 26 of 26: every node of all 5 editions in a kind, no holes, export reads back; four premiums (UFC and Addison 18501 Prem/Ops, UFC 18501 Products, UFC "a"-rated 10119) end at the rating's premium, every lookup has its table, the premium recomputes from its traced values; **every traced field the worksheet holds (23 to 27 a premium) equals the engine's value there and ISO's, written by the same rule file**; only ISO's `/State/Code` lies outside it; a changed value is caught | Medium | — |
| ~~C-29~~ | ✅ **DONE 2026-10-19**: **Measurements**: graph size per edition, rating time vs the engine, compile time. `cg/measure.py` (`python -m cg.measure`, one fresh process; `--memory`; `--report`), `docs/MEASUREMENTS.md`, data `results/measure.json`. **Size:** 92k to 98k nodes and 187k to 209k links an edition, ~70% in the six kinds, no holes; 188 rate tables (70,166 rows; 2027: 168, 37,002); JSON 32 to 35 MB; ~150 MB of memory per compiled edition. **Compile:** 2.0 to 2.7 s an edition, once (inlining ~1 s, lowering with the tables ~1 s). **Rating** (the 362 pass requests, end to end, best of two, all rated alike): graph median 0.158 s, engine 0.181 s, **1.13x** (1.11x on the total; refusals 1.41x; 2027 edition 1.06x); the carrier U8 rows are slower on the graph (0.82x: technical, carrier and each waterfall step are full runs). Both are Python and the graph's evaluator is a checking executor, so this is a floor; Federato's ~100x is against Excel, not measured. **Found on the way, a harness defect:** the engine's memory grows ~7 MB a rating and is never freed (174 to 1,113 MB over 120 ratings; the graph stays flat at 964 MB): `gl_engine/resolve/book.py` `Layer.names` / `Layer.families` are `@lru_cache(maxsize=None)` methods, which keep every `Layer` (a package's book with its parsed tables) alive, 2 per rating, and every rating parses its tables again. It is what took `verify_run` to 8 GB (C-24) and this run to a 5.8 GB peak. No premium effect; to be written up in the harness with the user's go | Small | — |
| ~~C-30~~ | ✅ **DONE 2026-10-19**: **Findings** `docs/FINDINGS.md`: what compiled, what didn't and why, engine defects the graph found, what §9's Federato questions need answered. **All of Iowa GL compiles** (0 holes, 5 editions), graph = engine on all 362 requests and = ISO on all but the engine's own two gaps; about 70% of nodes in the six kinds, the rest **7 extras** (repeating group, aggregate, create / ensure, remove, message, constant), several decided per request; and what a drawing does not show (run order for 866 record tests, only the branch taken runs, a missing value refuses, which write a read sees). DEV-003 sits on top as data. Engine items: OI-137, OI-96, the memory leak (fix drafted in the harness, not yet tested or committed), OI-136. §9 gains **F8-F10**; each question says what needs it and what a no would cost | Small | — |
| ~~C-31~~ | ✅ **DONE 2026-10-19**: **Next estimate** `docs/ESTIMATE.md`: effort to reach 51 GL states, Property (with the look-ahead), and a Product Studio load, replacing the 3-6 month range with measured numbers. `cg/survey.py` (`python -m cg.survey`, `results/survey.json`): **every GL jurisdiction's edition in force compiles today, 51 of 51, 0 holes**, all valid (91k-102k nodes, 2.5-3.2 s each, 2.4 min for all); Property census of 47: programs ~2.7x Iowa GL's, ~3x the record work, `Custom` / `Power` / `LastNonNull` new, 2,455 stored ISO answers. Iowa took 3 sessions against a planned 12-20 days. **Estimate:** GL 51 jurisdictions 4-6 working days over 3-5 weeks of ISO calls (~3,600, 72 groups of 50; the engine's leak fixed first); Property 8-12 working days (null handling, the look-ahead); a Product Studio load not estimable before Federato answers F1-F10 (Excel spike B-32 2-3 days, then weeks to months or not feasible) | Small | — |

### CG-8 · Waiting on someone else (parked until it arrives)

| Item | Waiting on |
|---|---|
| **Load the graph into Product Studio** (harness B-32 / B-34) | Federato: a way to load a graph without Excel (§9 F1), and a business reason |
| **§9's questions F1-F7** put to the Product Studio team | the user's call on when and who |
| **Property proof of concept** (brings in the look-ahead, OI-125) | CG-7's findings and the user's call |
| **More GL states** | CG-7's findings and the user's call. **Planned as CG-9 to CG-12** (2026-10-19) |

### CG-9 · GL everywhere, the ground work (4 tasks)

**Release gate:** the engine's memory stays flat over 1,000 ratings; Iowa's pass re-run through the new state
parameter is identical to pass 12; every edition in scope (D10) compiles with 0 holes and validates.

| # | Task | Size | Needs |
|---|---|---|---|
| C-32 | **The engine's memory leak, fixed in the harness** (to be OI-138): `gl_engine/resolve/book.py` per-book caches (drafted 2026-10-19, in the harness working tree). Measured before and after (`cg.measure --memory`), the harness's own gates, the stored-answer snapshot showing no premium moved; logged and committed in the harness, `book.py` only. Without it a pass of thousands of requests needs far more than 16 GB | Small | the user's go (a harness change) |
| C-33 | **State as a parameter**: Iowa is fixed in `cg/inventory.py` (`EDITIONS`), `cg/requests.py` (`"IA"`), `cg/live.py`, the passes and the tests. A new `cg/scope.py` holds the jurisdictions and, per jurisdiction, the editions in scope (D10); everything else takes them from there. `docs/KNOWN-GAPS.json` findings gain a state field (`OI-106-GL` and `OI-96-GL` are not Iowa's alone). Gate: Iowa through the new code gives pass 12's record again, every request and difference | Medium | — |
| C-34 | **Graphs on demand, memory bounded**: the executor keeps at most a few compiled editions (about 150 MB each; 51 x 2-5 editions will not all fit) and compiles the rest when asked (2.5-3.2 s); passes run one jurisdiction at a time, 2 workers at most | Small | — |
| C-35 | **Every edition in scope compiled**: `cg.survey` widened from the edition in force to D10's set (about 51 x 4 to 6 editions); 0 holes, all valid, and a census by Product Studio kind per jurisdiction. A hole here is the first new instruction shape outside Iowa: placed and compiled before CG-10 | Small | — |

### CG-10 · GL everywhere, free passes (3 tasks)

**Release gate:** graph = engine on every request in every jurisdiction, field for field; the 516 stored ISO
answers compared three ways, each gap placed and every open one a recorded finding.

| # | Task | Size | Needs |
|---|---|---|---|
| C-36 | **Request sets per jurisdiction**: stored ISO answers (516 rated, all but Puerto Rico), premium-only rows rebuilt, package samples, and requests generated by the harness's builder (`scripts/variants.py`) at D11's sizes; configurations a state cannot express counted, not sent (Iowa: 77). State rules the builder must meet are listed per state (e.g. NY terrorism needs the Manhattan input, OI-130) | Small-medium | — |
| C-37 | **Free pass, graph against engine**: every request in every jurisdiction (about 5,000 to 6,000, about 35 minutes a pass); every difference is the graph's and is fixed here, then re-run until graph = engine everywhere. One pass record per wave of jurisdictions (D12) | Medium | — |
| C-38 | **Stored-answer pass, three ways**: the 516 stored ISO answers (3 to 5 dates a jurisdiction, so older editions too). Gaps placed by §5's table; the two known engine gaps matched by state; new engine gaps written up in the harness (as C-25) | Small-medium | — |

### CG-11 · GL everywhere, ISO live (2 tasks)

**Release gate:** every request in scope has ISO's answer; a clean pass in every jurisdiction (graph = engine =
ISO, or each gap a recorded finding).

| # | Task | Size | Needs |
|---|---|---|---|
| C-39 | **Live waves**: the requests with no stored answer, about **3,600 calls** at D11's sizes, in fixed groups of 50 (`cg/live.py`, lane `active`, origin `iso-compute-graph`), **each group only with the user's go**; groups follow the waves (D12), each wave followed by its pass. At 150 a day (the `active` lane, shared with the harness's own work) about 24 days of calls; faster only by the user's instruction, logged as an override | Small effort, 3-5 weeks elapsed | the user's go per group |
| C-40 | **Fix and re-run** after each wave: each gap placed by §5's table, expert reviewers where it isn't obvious; graph gaps fixed here, engine gaps logged in the harness (each fix the harness's, with its own go); the whole regression re-run, Iowa included | Medium | — |

### CG-12 · GL everywhere, a rating engine of its own, findings and close (6 tasks)

**Release gate:** **the graph rates through its own entry point and endpoint without the engine's `Kernel`**,
equal to the engine on every request of the regression (all 51 jurisdictions) and U8, and its lean executor equals
the checking one field for field (D13); the findings reviewed with the user.

| # | Task | Size | Needs |
|---|---|---|---|
| C-41 | **Measurements and the Product Studio view, everywhere**: `cg.measure` and `cg.studio` census per jurisdiction (sizes, compile, rating time); one premium traced in a second state beside the harness worksheet | Small | — |
| C-42 | **Its own rating entry point** (D13): `cg.rate(request)` chooses the edition (the harness's resolver), runs the request checks, the graph and the after-checks (refusals, referrals, total and check figure, coverages) and returns the rating, **with no engine `Kernel` made**. Today `GraphRater` holds a `Kernel` and calls its private checks in place (`_refuse_missing_rating_inputs`, `_ilf_override_needed`, `_refuse_null_loss_cost`, `_collect`); under D1 they are not copied, so the harness exposes them as plain functions, a small harness change with its own go. Gate: the whole regression and U8 equal the engine through it, and no `Kernel` exists in the process | Medium | the user's go for the harness part |
| C-43 | **A way in**: a local endpoint, `POST /rate`, taking and returning the harness's `/api/rate` shapes, so the console or a client can point at either engine; plus a command line (`python -m cg.rate request.json`). Refusals and referrals in the same form as the engine's. Gate: the regression and U8 through the endpoint equal the engine | Small-medium | — |
| C-44 | **A lean executor**: the same compiled graph run without recording every value for the trace (the checking executor keeps a value per node and binding, which is what C-28's trace and C-20's replay read). Only what the rating's output needs is kept; the checking executor stays as the referee and for traces. Gate: lean = checking on every request, field for field; speed and memory measured against the engine (C-29 measured the checking one at 1.13x) | Medium | — |
| C-45 | **Rating-engine gate**: through the endpoint, the regression, U8 and 1,000 repeated ratings: equal to the engine, memory flat, timings added to `docs/MEASUREMENTS.md` | Small | — |
| C-46 | **Findings for all GL**: `docs/FINDINGS.md` updated: what differs by state (new instruction shapes, state-only rules, editions on another countrywide parent), engine defects found per state, F1-F10 restated with 51 jurisdictions' counts; `docs/ESTIMATE.md` updated for Property and a Product Studio load | Small | — |

## 7. Layout

```
ISOComputeGraph/
  CLAUDE.md          how this project relates to the harness
  docs/PLAN.md       this plan (master)
  docs/FINDINGS.md   CG-7
  docs/ESTIMATE.md   CG-7, the next estimate
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
| F8 | Can a later step read a value a repeating group wrote, by record or as a total? (C-30: 972 reads in force) |
| F9 | Does it run only the branch taken, and stop at a missing value instead of treating it as zero? (C-30) |
| F10 | Can a deviation be a layer of data over the filed graph (override tables, input multipliers, a minimum after)? (C-30, from CG-6) |

## 10. Log

| Date | Entry |
|---|---|
| 2026-10-16 | Plan drafted; D1-D5 taken; setup done (now C-01) |
| 2026-10-16 | Revised by the user: the harness loop three ways (D6), stored answers then live with a go per pass (D7), ISO without deviation first, DEV-003 moved after the technical loop (D8) |
| 2026-10-16 | Re-organised into release-candidate groups CG-1 to CG-8, tasks C-01 to C-31 (C-01 done). About 12-20 days. Waiting for the go on CG-1 |
| 2026-10-16 | C-02 done: `cg/harness.py`; `verify_harness_link.py` 7 of 7 (Iowa sample $450, same as the harness at home). CG-1 left: C-03, C-04, C-05 |
| 2026-10-16 | C-03 done: inventory of 5 editions, gate 18 of 18. §4 corrected (reachable program: 2,227 loops, not 1,030; `Remove` and most `Append` are forms only; 41 true overwrites). Harness OI-136 found and fixed (files past the Windows path limit). CG-1 left: C-04, C-05 |
| 2026-10-16 | C-04 done: graph format `iso-compute-graph/1`, `verify_model.py` 23 of 23. CG-1 left: C-05 |
| 2026-10-16 | C-05 done: shared table store and the graph's own lookup, 1,000 of 1,000 equal to the engine. **CG-1 COMPLETE**: harness link 7/7, inventory 18/18, format 23/23, tables 12/12. Next: CG-2 (needs the go) |
| 2026-10-16 | C-06 done: rules inlined, `verify_inline.py` 15 of 15 (14,369 engine calls on 16 requests all present). Note for C-21: the 3 stored answers on 20250401 are DEV-003's U8 requests, stored as sent to ISO (technical only). CG-2 left: C-07 to C-10 |
| 2026-10-16 | C-07 done: steps, 3,780 of 3,780 trials equal to the engine's evaluators; lowering started (`cg/lower.py`, `hole` kind for what is not lowered yet). CG-2 left: C-08, C-09, C-10 |
| 2026-10-16 | C-08 done: branches and tests, `verify_conditions.py` 8 of 8 (same answers and the same parts evaluated as the engine, over every non-constant expression in force). CG-2 left: C-09, C-10 |
| 2026-10-16 | C-09 and C-10 done. **CG-2 COMPLETE**: inline 15/15, steps 7/7, conditions 8/8, calls 10/10 (22,500 trials equal to ISO's real rules in the engine), holes 5/5 (only CG-3 instructions left; 4,960 of 4,964 writes are inside one). Next: CG-3 (needs the go) |
| 2026-10-16 | C-11 done: loops are repeating groups. verify_loops 28/28 (11,772 trials over 3,924 rule calls with loops equal the engine; 8 built shapes 2,400/2,400); every earlier gate passes. Next: C-12 |
| 2026-10-16 | C-12 done: records added and made sure of. verify_records 33/33 (7,335 trials over 2,445 single Locates, all 122 record-adding ones, equal the engine, records present after included); every earlier gate passes. Next: C-13 |
| 2026-10-16 | C-13 done: records removed. verify_removes 21/21 (1,770 trials over 295 real Removes equal the engine; 6 built shapes 1,800/1,800); every earlier gate passes. Next: C-14 |
| 2026-10-16 | C-14 done: tests in order. verify_tests 23/23 (6,432 trials over 2,144 whole rule calls equal the engine; shapes 1,800/1,800); every earlier gate passes. 139 holes left in force (Guid, Break, GetList). Next: C-15 |
| 2026-10-16 | C-15 done: early exit. verify_breaks 17/17 (4,000 real trials, 6 shapes 1,800/1,800); every earlier gate passes. Only Guid (134 in force) remains. Next: C-16 |
| 2026-10-16 | C-16 done. **CG-3 COMPLETE**: 0 holes in all 5 editions; verify_ids 23/23 (30,640 trials over the 766 id-making rule calls and 22,500 over 7,500 sampled calls equal the engine); all 15 gates pass. Next: CG-4 (needs the go) |
| 2026-10-18 | Go for CG-4. C-17 done: executor `cg/run.py`; verify_run 28/28 (5 samples + 11 stored ISO requests equal the engine field for field; 240 of 240 variants, refusals included). Next: C-18 |
| 2026-10-18 | C-18 done: the three-way loop, verify_loop 20/20. Free pass on 16 requests: graph = engine everywhere, the 11 ISO premiums equal three ways; 156 form-label differences G=E!=I (OI-106 on GL, for C-25). Next: C-19 |
| 2026-10-18 | C-19 and C-20 done. **CG-4 COMPLETE**: run 28/28, loop 20/20, passes 11/11, replay 4/4. `results/passes/pass-00.json` (16 requests, exit clean; 156 form-label gaps, recorded finding OI-106-GL). Next: CG-5 (needs the go) |
| 2026-10-18 | Go for C-21 and C-22. C-21 done: pass 1 (28 requests incl. 12 premium-only ISO rows rebuilt), clean. C-22 done: pass 2 with 334 generated requests left 5 gaps placed here (refusal wording), fixed in the comparison; pass 3 clean, graph = engine on all 362. Live gap 339 requests. Next: C-23 (needs the go and a choice of 25) |
| 2026-10-18 | The user: live calls in groups of 50; go for group 1. C-23 group 1 sent (50 calls, lane active): 45 premiums equal, 5 refused alike. Pass 4 (samples counted twice, fixed), pass 5 clean: 73 ISO answers three ways. Left: groups 2-7 (289 calls) |
| 2026-10-19 | Go for group 2. C-23 group 2 sent (50 calls, lane active): 50 premiums equal. Pass 6 clean: 123 ISO answers three ways, graph = engine on all 362; verify_live 8/8. Left: groups 3-7 (239 calls) |
| 2026-10-19 | The user: do all 139, ignore the cap. Groups 5-7 sent (override logged): 138 premiums equal, 1 refused by ISO where ours rates (ILFPremOps, harness OI-96). Pass 8 open on it; recorded OI-96-GL; pass 9 clean, all 362 with ISO's answer. **C-23 DONE.** Next: C-24 (nothing open) and C-25 (write up OI-106-GL and OI-96-GL in the harness) |
| 2026-10-19 | Go for C-25. Written up in the harness (`cba394d`, OPEN-ITEMS and backlog only): OI-137 raised (GL form labels), OI-96 evidence row (ISO refuses a missed ILFPremOps lookup). **C-25 DONE.** |
| 2026-10-19 | Go for C-24. Nothing open to fix; regression 22 of 22 (`verify_run` back to its C-17 scope after reaching 8 GB); pass 10 clean at `13528eb`. **C-24 DONE. CG-5 COMPLETE.** Next: CG-6 (DEV-003 on the graph, needs the go) |
| 2026-10-19 | Go for C-26 then C-27. C-26 done: `cg/carrier.py`, DEV-003 on the graph (LCM inputs, override table, policy minimum), verify_carrier 14/14, U8 on the graph 2,828 / 3,818 / 830. C-27 done: U8 three ways (pass 11 clean; the filed ELR vs ISO's 1 judged by design, DEV-003-ELR), pass 12 technical clean, 24 of 24 tests. **CG-6 COMPLETE.** Next: CG-7 (C-28 to C-31) |
| 2026-10-19 | Go for C-28. Done: `cg/studio.py` export and census in Product Studio's kinds, four premiums traced input to output, `docs/studio.html` (private artifact); verify_studio 26/26, every traced field equal to the harness worksheet and ISO. Next: C-29 |
| 2026-10-19 | Go for C-29. Done: `cg/measure.py`, `docs/MEASUREMENTS.md`: 92k-98k nodes an edition, compile 2-3 s, rating 1.13x the engine (median). Found: the engine leaks ~7 MB a rating (`Layer` lru_cache methods), a harness defect, write-up awaits the user's go. Next: C-30 |
| 2026-10-19 | Go for C-30. Done: `docs/FINDINGS.md` (what compiled, the 7 extras and why, engine items, F1-F10 with what each needs; §9 gains F8-F10). The user asked for the harness leak fixed: per-book caches in `gl_engine/resolve/book.py`, drafted in the harness working tree; testing and committing it was blocked by permissions in this session. Next: C-31 |
| 2026-10-19 | Go for C-31. Done: `cg/survey.py`, `docs/ESTIMATE.md`: all 51 GL jurisdictions compile (0 holes), Property census of 47; GL 51 is 4-6 days over 3-5 weeks of calls, Property 8-12 days, a Product Studio load waits on F1-F10. All 31 tasks done; **CG-7's gate (the findings reviewed with the user) is open** |
| 2026-10-19 | The user signed off CG-7 (findings and estimate reviewed). **CG-7 COMPLETE; the proof of concept's planned work is done.** Left: CG-8 (waiting on others) and the harness leak fix (drafted, to be tested and committed in the harness) |
| 2026-10-19 | The user asked for the plan to finish GL in every state. Added CG-9 to CG-12 (C-32 to C-46) and §11 (scope, waves, D9-D12 proposed). The user then added the graph as a rating engine of its own (D13, CG-12, C-42 to C-45). About 8-12 working days over 3-5 weeks of ISO calls. Waiting for the user's decisions D9-D12 and the go for CG-9 |
| 2026-10-19 | The user: go for the next 100 (groups 3 and 4). Sent (100 calls, lane active, now 150 of 150 today): 100 premiums equal. Pass 7 clean: 223 ISO answers three ways, graph = engine on all 362; verify_live 10/10. Left: groups 5-7 (139 calls) |

## 11. GL in every jurisdiction (CG-9 to CG-12, added 2026-10-19)

**In short.** The compiler already handles every GL jurisdiction: all 51 editions in force compile with 0 holes
(C-31, `docs/ESTIMATE.md`). What is left is Iowa's loop run 51 times: the same requests to ISO, the engine and the
graph, every difference judged and fixed. The work is small; **ISO's calls set the pace**.

**Scope, measured 2026-10-19** (`results/survey.json`): 51 jurisdictions (49 states, DC, Puerto Rico; no Hawaii);
552 GL editions on disk, 5 to 10 a jurisdiction since 2024; one edition still to come in 35 jurisdictions and two in
14 (46 file 2027-04-01); stored ISO answers on 3 to 5 dates in 50 of them (516 rated), none in Puerto Rico.

**Decisions needed (proposed; the user's to take):**

| # | Question | Proposed |
|---|---|---|
| D9 | Order | GL everywhere before Property; the leak fixed first (C-32) |
| D10 | Which editions | Per jurisdiction: **the edition in force**, **every edition with a stored ISO answer** (free), and **the next edition filed** (free passes only; live calls only if its pass shows a gap). About 4 to 6 editions each, ~250 graphs, ~13 minutes to compile them all |
| D11 | How many requests | Edition in force: **about 70**, as Iowa (each control's options one at a time, 15 mixes); next edition: about 25, free only. About 3,600 requests need a live call |
| D13 | The graph as a rating engine | **Yes** (the user, 2026-10-19): its own entry point, endpoint and a lean executor, in CG-12 (C-42 to C-45), once every jurisdiction is proven. Still on the harness's file reading, tables, resolver and carrier reader (D1: imported, not copied). Property stays after GL (D9) |
| D12 | Waves | Jurisdictions in **5 waves**, lowest risk first, a pass after each: **W1** 10 on Iowa's countrywide parent (GL_CW_20261001_V01), **W2-W4** the other 33 on it (Iowa, done, is the 44th), **W5** the 7 on another edition or version (CA 2024-11-01, NY 2026-08-01, DC 2026-06-01, CO / ND / NM / SD V03) and Puerto Rico (no stored answers) |

**ISO calls.** About 3,600 calls, 72 groups of 50, each with the user's go (several groups can share one go, as
groups 3-4 did). At the `active` lane's 150 a day that is about 24 days of calls; at the full 250, 15. These lanes
are the harness's too.

**Effort.**

| Group | Working days | Elapsed |
|---|---|---|
| CG-9 ground work | 2-3 | — |
| CG-10 free passes | 1.5-2.5 | — |
| CG-11 live and fixing | 1-2 | 3-5 weeks of calls |
| CG-12 rating engine, findings | 3.5-5 | — |
| **Total** | **8-12** | **about 4-6 weeks** |

Above C-31's 4-6 days: this plan also prices the leak fix, the state parameter, the wider set of editions and
(3-4 days) the graph as a rating engine of its own (D13).

**Risks.**

| Risk | Handling |
|---|---|
| A state's rules use a shape Iowa does not | C-35 compiles every edition in scope first; a hole stops CG-10 until placed |
| The engine's known gaps recur in every state (OI-137 form labels, OI-96) | Findings matched by state; fixing them is the harness's, with its own go. OI-137 alone would put thousands of form-label differences in each pass until fixed |
| Memory on 16 GB | C-32 (the leak) and C-34 (graphs on demand), one jurisdiction at a time, 2 workers |
| Calls compete with the harness's own work | Lane `active` at 150 a day; going past it only by the user's instruction, logged |
| A state rule the builder cannot express | Counted and listed per state (C-36), not sent |
