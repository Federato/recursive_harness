# Build Log — the GL Rating Engine

**Opened 2026-08-12. No code has been written.**

This is the diary of the **build**, and only the build. Everything before it — three weeks of
corpus analysis, eleven coverage walkthroughs, the referral register and thirteen decisions — lives
in [`PROCESS_LOG.md`](PROCESS_LOG.md), which closed at Step 50 with the build specified and awaiting
sign-off.

**Its companion is [`docs/FROM-PLANNING-TO-BUILD.md`](docs/FROM-PLANNING-TO-BUILD.md)**, which
records what each stage *expected* to inherit from that analysis against what it *actually* used.
That file's "expected" sections were written **before** stage 1 and must not be edited afterwards.

---

## How this log works

One entry per working session, in the style of `PROCESS_LOG.md` and with the same rules:

- **What was directed**, in the user's words
- **What was built**, and what it was checked against
- **What broke, and what the fix revealed** — corrections are kept, never tidied away. They are the
  raw material for the self-correcting harness that RAaS integration is meant to feed
- **Every count is `n of N`**, with `N` enumerated rather than assumed. This project has recorded
  **sixteen** corrections and nearly all were the same mistake — something measured in one place and
  stated about everything
- **Exactly one live `NEXT SESSION STARTS HERE` marker** in the file at any time

---

## The standing constraints

| | |
|---|---|
| **Stage gates** | Each stage is presented and signed off before the next begins |
| **Two modes** | `strict-erc` reproduces ISO exactly; `underwriting` enforces the referral register. One code path |
| **Execute, never transliterate** | The engine runs ISO's filed rules. It does not re-express them in Python |
| **Separation** | The engine never imports the UI. Notebook use must come free from that |
| **No RAaS connection** | Not built. The 53 priced examples serve until it is |
| **Doctrine unchanged** | ERC is the source; manuals confirm and never source; a referral-only input may be sourced from the manual, a rating input may not |
| **Built for deviations, not with them** | Company content is **phase 4**, after the ISO baseline is proven against RAaS. But **C1 (ordered layer chain), C2 (ISO's `@parent` keeps ISO's meaning) and C3 (behaviour and content are independent axes)** apply from stage 2 — build plan §5. C2 is the dangerous one: resolving ISO's own call-super through an inserted company layer silently rewrites ISO's rules |

---

## Stage status

| Stage | | |
|---|---|---|
| **1** | Load and resolve | ✅ **built 2026-08-12** — 20/20 acceptance, 13/13 assertions at **two** dates |
| **2** | The interpreter | ✅ **built 2026-08-13** — 52/52 acceptance, all 54 nodes |
| **3** | Kernel and the two modes | ✅ **COMPLETE 2026-08-13** — 37/37 acceptance. Golden case exact; **49 of 49 usable oracles agree to the penny**. Banded and interpolated lookups built; every register entry has an explicit disposition |
| **4** | Schemas and payloads | ✅ **COMPLETE 2026-08-13** — 23/23 acceptance. The schema is **read from ISO**, not designed; **51 of 51 jurisdictions rate the same risk**, GA 6,845 to NY 12,141 |
| **5** | The enum workbook | — |
| **6** | The UI | — |

Full detail: [`docs/BUILD-STAGES.md`](docs/BUILD-STAGES.md). Every command that exercises a stage: [`TESTING.md`](TESTING.md). The plain-English account of the day stage 1 was built: [`docs/WHERE-WE-PAUSED-2026-08-12.md`](docs/WHERE-WE-PAUSED-2026-08-12.md).

---

## Entry 1 — Log opened. ~~NEXT SESSION STARTS HERE.~~ *(the live handoff is **Entry 2**)*

- **Date:** 2026-08-12
- **Directed:** "keep a diary of the build" · "do not build until I sign off"
- **Action:** This file created, alongside the skeleton of `FROM-PLANNING-TO-BUILD.md`. Nothing
  else.
- **Result:** No code exists.

### What stage 1 will be measured against

Recorded now so it cannot be adjusted later to match whatever gets built:

- All **51 jurisdictions** resolve for a given date, each against **its own declared parent** —
  including California's lone `GL_CW_20231201_V02`, which no other state uses
- A date **before 2022-09-01** fails loudly rather than falling back to the earliest edition
- Every load-time assertion in build plan §10 fires as a **failure**, never a warning
- The **five table shapes** load and type correctly — including the state loss-cost variants, where
  CA and NJ put the territory in the filename with three columns, OH and TX use four, and NY uses
  its own column names

### ▶ Next session

**Stage 1, on approval.** Nothing is built before that.

---

## Entry 2 — Stage 1 built: load and resolve. ~~NEXT SESSION STARTS HERE.~~ *(the live handoff is **Entry 3**)*

- **Date:** 2026-08-12
- **Directed:** *"Build, when done, log, and then present TLDR in laymens term"*
- **Built:** `gl_engine/` — 1,814 lines across 11 modules. No third-party dependency.
- **Verified:** `tests/verify_stage1.py` **20/20** · `check 20260811 --deep` **13/13** ·
  `check 20270401 --deep` **13/13** · four pre-existing fixtures and both expert agents unchanged
  (80/80, 11/11, 10/10, 7/7, 19/19, 88/88).

### What it does

Given a jurisdiction and a date, it returns the exact rule set and tables ISO says apply, with
every value carrying the package that produced it.

| Module | |
|---|---|
| `config.py` | Corpus root, the `20220901` floor, the 2027 cliff date |
| `errors.py` | Every allowed failure. **No warning tier.** `ReferToCompany` is deliberately not a `LoadError` |
| `domain/cell.py` | The typed cell. `erc_source` has **no default** — a value with no ERC source cannot be constructed |
| `erc/discovery.py` | 567 packages found by directory listing, identity from XSD `targetNamespace` (N6) |
| `erc/tables.py` | Table definitions, typing, shape classification, split-family grouping |
| `resolve/resolver.py` | As-of selection (N4), declared parent (N5), hard failure on both |
| `resolve/book.py` | Two-layer composition; `parent_table` reachable explicitly for N2 |
| `assertions.py` | 13 load-time assertions. They fail; none warns |
| `cli.py` | `resolve` · `parents` · `table` · `check` · `census` |

**Measured, at 2026-08-11:** 567 packages · 51 jurisdictions + countrywide · **3 countrywide parents
live**, and 3 again at the 2027 cliff · **5 states declare a parent that is not the newest** (CA
alone on `V02`; NJ, OK, TX, VT on `V03`) · discovery **0.9s**, deep assertion sweep **51s** ·
**5,364,957** numeric cells type-checked.

### Four corrections, and what each one revealed

**1. The ILF monotonicity check matched its axis by name.** `IncreasedLimitsTableAssignmentPremOpsFinal`
contains the word `Limit`, is not a limit, and the first version asserted that factors rise with the
*table-assignment number*. It reported 1,396 of 7,344 series failing. Worse, no type test would have
caught it either — **the same selector is an integer `1/2/3` in `ILFPremOps` and the letters `A/B/C`
in `ILFProds`.** Fixed by identifying limit axes *behaviourally*: a column is a limit only if every
value in it parses as an amount. **The predicate may not define the population — this time applied to
columns.**

**2. Zero is a factor sentinel, and A11 found it while looking for something else.** **60 of 53,241**
ILF factor cells are zero, in **3 of 54** packages, confined to Liquor-with-sublimit and Elevator
Contractors. A zero increased-limit factor prices the top limits at nil. Now assertion **A13**, which
pins the *set of tables* rather than the count — a zero appearing somewhere new fails the load.

**3. ONE is also a sentinel, and it is worse.** Texas's `ILFElevatorContractor` publishes exactly
`1.00` at **26 of 30** rows and a genuine 1.69–1.72 at four, so a 20,000,000 aggregate prices
identically to a 50,000 one. **Multiplying by a sentinel zero produces a visible nil premium;
multiplying by a sentinel one produces a plausible wrong one.** ERC cannot say which reading is
right — raised as **E20 / OI-68** and allowed past by name, not by silence. **1 of 19,236** series.

**4. The split-family detector had two bugs, and one of them passed.** `split_families` required the
base table to exist in the same package. In **CA, NJ and OH the state files only the slices**, so
`PremOpsLossCost` resolved *upward* to a header-only countrywide table — **zero rows, no error, a
finished premium**. This is precisely the OI-20 failure mode, and my A9 gave it a **PASS** because it
counted only the families it could see. Enumerating all **75** loss-cost suffixes in the corpus split
them cleanly: `Terr<n>`, `<ST>Terr<n>`, `<n>`, `<ST>` are slices; `OverOneHundred` and
`OverOneMillion` (54 packages each) are **separate tables**. Sibling lookup now searches the state
layer independently of which layer owns the base name. **13,068 · 17,805 · 23,820 · 11,880 rows**
recovered in CA, NJ, NY and OH.

> **The lesson is the project's oldest one, and it landed twice in one file.** A9 and A11 both had a
> check whose *condition* was narrower than its *name*. A9 passed while blind. That is the more
> dangerous of the two failure modes, and it is now the thing to look for first when a new assertion
> goes green on the first run.

### One planning claim did not survive contact

§10 of the build plan says *"classify the five table shapes"*. Measured, there are **four read
shapes** — `exact` 3,418 · `undeclared` 485 · `banded` 32 · `interpolated` 6 — and **three
population states** — `populated` 2,894 · `empty` 1,046 · `split-family` 1 (deduplicated over 54
resolved packages). Shape and population are **orthogonal axes**, which is N7 restated: *presence is
not population is not purpose*. Five was a conflation of the two. `docs/GL-RATING-ENGINE-BUILD-PLAN.md`
§10 has been corrected.

### What stage 1 does not do

No rule is executed. `interp/` does not exist. `RunRule`, parent dispatch and the evaluation contract
are stage 2, and the `parent_table` / `parent_rule` split exists now only so that stage 2's 4,598
call-super rules have somewhere to dispatch to.

### Two more findings, from running the suite at a SECOND date

Writing `TESTING.md` meant documenting `check 20270401 --deep` — the 2027 cliff. I wrote *"also
13/13"* from expectation rather than from output. **It was 11/13.** Both failures were real content,
and one of them closes a filed open item.

**5. Size-of-risk is being withdrawn wholesale, and the states prove it (OI-53 answered).**
OI-53 recorded that `GL_CW_20270401_V01` keeps the relativity table and zeroes the assignment,
minimum and maximum tables, and said the corpus could not distinguish **withdrawal** from
**incomplete filing** — noting it binds when the first jurisdiction adopts that parent, and that
*none did yet*. At the cliff, 43 do. Counted across all 51 jurisdictions at both dates:

| | today | 2027-04-01 |
|---|---|---|
| jurisdictions carrying Prem/Ops size-of-risk loss costs | **35 of 51** | **2 of 51** |

**Both survivors — NJ and WA — are among the eight still on an older parent.** Every one of the 43
adopting the 2027 edition empties its own size-of-risk loss costs too. Ohio files **11,880 rows
across 10 per-territory slices** today and **the same 10 slices with 0 rows** at the cliff. **The
withdrawal tracks the declared parent exactly.** Forty-nine jurisdictions and the countrywide layer
emptying the same apparatus in step is coordinated; an incomplete filing is not.

**The reason the countrywide-only reading could not see this** is that OI-53 examined the parent
package. The answer is in **who adopts it** — which is the resolver's whole job, and the first
question stage 1 was able to ask that the analysis could not.

*A9 was also wrong here, in the safe direction.* It failed on families that are empty **everywhere**,
which at the cliff is normal rather than exceptional. Rewritten to assert the property that actually
matters: **a split family must carry rows, or read as unavailable so a rating attempt fails loudly.**
The dangerous state is narrow — slices carrying rows that the reader cannot find — and only that
state is a defect.

**6. E20 is not a one-off, and the amendment reverses the reading.** `ILFElevatorContractor` carries
`1.00` at **26 of 30** rows in **all six** Texas editions from 2021-06-01 to 2025-08-01, and **11 of
15** in the 2027 edition — which halves the table and preserves **all four** genuine factors. **Six
years of consecutive filings is not a typo.** *"No increased-limit load applies at this combination"*
is now the stronger reading and *"placeholder"* the weaker one.

**The disposition does not change, and that is the point.** The series is still non-monotonic, ERC
still carries no discriminator, and a wrong guess in the permissive direction is invisible. It
refers either way — but the register now records the right reason.

> **The methodological error was mine and it is the project's signature one, rotated ninety degrees.**
> The first measurement asked **one edition** and generalised across the corpus. OI-67 was the same
> mistake on the directory axis. **Measuring "the resolved edition" is measuring one column of a
> table that has seven.**

### And a process note worth keeping

**I wrote an expected output into `TESTING.md` before running the command.** It was wrong, and it
was wrong in the direction that would have looked fine — a page full of green numbers, one of which
was fiction. **Every command in `TESTING.md` has now been executed and its stated output is what it
actually produced.** That is now a rule for that file. Verifying the rest of it turned up four more
documented commands that would not have run — the ERC agent takes `2026-08-11` where the engine
takes `20260811`, and six analysis scripts require an as-of date that the draft omitted. All
corrected against actual output.

### ▶ Next session

**Stage 2 — the interpreter — on approval.** The largest single piece of new specification work in
the build is the **evaluation contract**, which E3 closed as *"only if interpreting"* and which was
therefore never written.

---

## Entry 3 — Stage 2 opened: the evaluation contract. ~~NEXT SESSION STARTS HERE.~~ *(the live handoff is **Entry 4**)*

- **Date:** 2026-08-13
- **Directed:** *"can we create a branch, so that if we want to do a full code build instead of
  interpreter, we can compare the two? And then start working on stage 2"*
- **Branch:** `stage2-interpreter`, cut from `883d9a1` — the same commit a transliteration branch
  would fork from, so the two remain comparable. `main` is untouched.
- **Built:** no interpreter code. Three measurement scripts, one specification, one check.

### What was directed, and what it means for the branch

The comparison the branch exists for is **interpret vs transliterate**, and the honest way to hold
it open is for both to fork from the same commit rather than for the second to be cut later from a
`main` that has drifted. That is done. **Nothing in this entry is interpreter-specific** — the
evaluation contract specifies what ISO's language *means*, and a transliteration branch would need
exactly the same document to know what it was transliterating.

### The deliverable

**[`docs/rating-engine/14-EVALUATION-CONTRACT.md`](docs/rating-engine/14-EVALUATION-CONTRACT.md)** —
E3's residual, closed. 54 language nodes, each with its arity, attribute domains, legal parents and
evaluation rule; twelve decisions marked **ANSWERED**, **CONSTRAINED** or **OPEN**; six things the
engine refuses to do rather than guess.

New scripts, all reading the whole corpus rather than a sample:

| | |
|---|---|
| `scripts/erc/42_node_surface.py` | every element, attribute, value domain, child and parent. 567 packages, 20,673 rule files, 2,041,679 elements, 21s |
| `scripts/erc/43_default_block.py` | the entry point, across all 567 packages |
| `scripts/erc/44_contract_questions.py` | the named open semantics, answered or declared open |
| `tests/verify_contract_figures.py` | every figure quoted in the contract must be one the corpus produced |

### 1. The entry point is not where every previous analysis said it was

`23_rule_program.py` P3 derived the program's entry as `(GeneralLiabilityRules, ErcProcess)`, by
taking the rules no `RunRule` targets. That is a true statement about **rules**, and it is not the
top of the program.

**Every package carries a `Default` block, a child of the document root `Rules` rather than of any
`Rule`, and `ErcProcess` is the third thing it calls.** Before it: `Renewal` defaults to 0, the
state code and name are seeded, **`ExpDate` is computed as `EffDate` + 1 year** — nothing else in
the corpus computes it — and a `Policy` node is appended, ISO's own comment saying this assumes a
policy rather than a quote **for a Rating as a Service request**. After it:
`ErcCalculateTotalPremium`, a separate top-level call. All three run **once per `GeneralLiability`
row**, which is where multi-risk submissions are actually iterated.

**An interpreter entered at `ErcProcess` would have produced a complete, plausible premium with no
expiry date and no total.** It is the stage-1 failure mode exactly, one layer up.

**Why every census missed it: they all walked `Rule` elements, and this is not inside one.** So the
prior operator census reported **52** of the **54** language nodes and looked complete — `Default`
and `DateAdd` are the two, and both are in all 567 packages. **This is the project's signature error
for the third recorded time**, so the rule is promoted: *a census states the element it walked and
the population it walked over, or it does not get quoted.*

Uniformity is what makes it a contract: **567 of 567 packages, one block each, one file, one call
sequence, one iteration target, and zero variation across editions within a jurisdiction.**

### 2. Four "unspecified" semantics turned out to have one answer in the content

P5 listed these as things an implementer must pin down. They are unspecified in ISO's *schema*; they
are not unspecified in ISO's *content*.

| | |
|---|---|
| `FirstValue` four-way precedence | **`FromInput` and `FromParam` are never filed. Not once.** All 171,189 nodes carry exactly `(FromDataDef, FromConstant)`. The four-way collapses to two |
| `RunRule@ClearCache` | **`true` on all 173,204.** There is nothing to specify: the corpus never asks for a cached call, so the interpreter never memoises |
| Empty `Constant` — null or empty string? | **All 20,520 are `Type="string"`.** No numeric or date constant is ever empty. It is the empty string |
| `Remove@RemoveMultiple` | **`true` on all 7,304.** Removal is always all-matching |

**The language ISO declares is materially larger than the language ISO uses, and the difference is
exactly where an interpreter would have had to guess.** Each of these is now a hard failure if a
future filing exercises it, rather than a silently invented behaviour.

### 3. What stays open, and why that is the right answer

**The rounding mode (OI-70).** Places in use are {0, 2, 3, 4, 8} — the 8dp found on 12 August is on
`Divide` — but **no node anywhere declares half-up, half-even or truncate.** They differ on exactly
the input a rating engine hits constantly, a half-cent. Contract: one engine-wide setting defaulting
to `ROUND_HALF_UP`, **recorded in the trace on every rounded value**, and **the first thing the
Phase 2 RAaS diff should be pointed at** — a mode mismatch is small, systematic and everywhere,
which is what that comparison is good at and what reading the files never will be.

**`FirstNonNull` exhaustion is real, not hypothetical.** 32,601 of 36,605 end in a `Constant` and
cannot exhaust; **4,004 can, across 327 of 567 packages.** It returns null and is traced, because
ISO's own idiom is to append a total fallback when it wants a guaranteed value.

**`Break` (OI-74).** 68 of its 84 occurrences are inside `Sum`, not inside a loop, which the name
does not explain. Hard failure until something needs it.

### 4. A correction, caught by machine and not by eye

**I drafted the contract quoting a mixture of the superseded P5 census and the new de-duplicated
enumeration.** On the page every number looked equally plausible — the same failure as writing an
expected test output before running the command, which is Entry 2's process note.

`tests/verify_contract_figures.py` caught **five** wrong figures. It also proves it can fail, which
is the standing rule for a new check here: it failed on its first run, was corrected, and passes
now. **It does not catch a figure that is valid for a node but quoted in the wrong context, and its
docstring says so** rather than letting a green run read as more than it is.

### 5. And a smaller one, upstream

The corpus holds **572 package directories but 567 packages**: five are unpacked twice, once bare
and once under a `_MachineReadableContent` wrapper. **Verified byte-identical, all five.** Stage 1
already de-duplicates and documents it; the new scripts now do it the same way, so the analysis
population and the engine's population agree by construction. Recorded as OI-73 so no future count
reports 572.

### Also corrected

- The plan's *"14 node types under 500 occurrences"* is **9** (OI-72). *"One appears twice"* is
  right — `GetList`
- Top-20 coverage re-measured at **94.03%**, against the plan's 94.1%. The architectural decision it
  justified stands

### Verification

Six suites green — `verify_stage1`, `verify_golden`, `verify_california`, `verify_new_york`,
`verify_oi50`, `verify_contract_figures` — and `check 20260811 --deep` still **13/13**. Stage 1 was
not touched.

### ▶ Next session

**`gl_engine/interp/` — the node evaluators, written against the contract, top 20 first** (94.03% of
the corpus), then the 30 that follow, then the 9-node tail. The eleven coverage walkthroughs are the
acceptance target.

**The open question for you:** whether to cut `stage2-transliteration` from `883d9a1` now and build
the comparison in parallel, or to finish the interpreter first and fork the comparison only if it
disappoints. Nothing about the contract favours either — it is the shared input to both.

---

## Entry 4 — Stage 2 built: the interpreter. ~~NEXT SESSION STARTS HERE.~~ *(the live handoff is **Entry 5**)*

- **Date:** 2026-08-13
- **Directed:** *"finish the interpreter first and only fork if it disappoints"* — so no
  transliteration branch is cut. `main` and `stage2-interpreter` still share `883d9a1` if that
  changes.
- **Built:** `gl_engine/interp/` — 6 modules. No third-party dependency.
- **Verified:** `tests/verify_interp.py` **52/52** · six prior suites unchanged ·
  `check 20260811 --deep` **13/13**, 35.6s (unchanged; a 118s reading mid-session was a cold cache,
  re-timed twice to be sure rather than assumed).

### What it does

Executes ISO's filed rule language. **All 54 nodes have an evaluator** — the list is read from
`out/node_surface.csv` by the test rather than typed into it, so a 55th node in a future filing
fails the suite rather than passing unnoticed.

| Module | |
|---|---|
| `values.py` | five types, `Decimal` never float (N10), and a null that is neither zero nor the empty string |
| `tree.py` | the data tree and its path dialect, including the `../../../` forms (E18). Reads never create; writes do |
| `program.py` | rule files indexed lazily, and `entry()` — the `Default` block, hard failure if absent |
| `nodes.py` | the 54 evaluators, each naming the contract clause it implements |
| `interpreter.py` | frames, dispatch, lookup, rounding, trace |

### It runs real ISO content, not just fixtures

Against **Alaska's real RAaS input** (`Payloads/AK/1. Input.json`) resolved to
`GL_AK_20260801_V02` over `GL_CW_20260101_V01`:

| | |
|---|---|
| Rule calls executed | **269** |
| Writes onto the tree | **125** |
| Table lookups | **12 hits, 28 misses** |
| Cross-package dispatch to the countrywide parent (N2) | **yes** |

The misses are not defects — they are ISO's own state-then-countrywide idiom, visible in the trace
as a miss on `['AK', 'Yes']` followed by a hit on `['CW', 'Yes']`.

**It then stops, on `§12.3 null reached arithmetic`, and stopping is the correct outcome.** Stage 2
is the interpreter, not the kernel: mapping a submission onto the ERC data tree is stage 4 and
orchestrating a rating is stage 3, so a required value is genuinely absent. **What matters is that
it stopped on a named contract clause instead of multiplying by a zero it invented.** That is
recorded as test E5, phrased so that running to completion *fails* the test until stages 3 and 4
make completion meaningful.

### The correction that matters, and it came from a real payload

**The contract's `Value` clause was wrong, and only executing real content exposed it.**

The first draft said: a `Value` without `@AllowNullReturn` that resolves to nothing is an error.
**I inferred that from the attribute's name and never measured it.** It stopped Alaska dead on
`TRIAExpirationDate` — which ISO's own rules read with a bare `Value`, and which the schema declares
`nillable="true"`.

`scripts/erc/45_nillable_vs_allownull.py`, over all 567 packages:

| | |
|---|---|
| Element declarations across all DataDefs | 64,788 |
| Declared `nillable="true"` | **48,785 — 75.30%** |
| `Value` reads targeting a **non-nillable** element | **0. Not one, bare or otherwise** |
| Bare reads targeting an explicitly nillable element | **28,347** |

Nullability is close to universal in this schema, so it cannot be what `@AllowNullReturn` gates, and
raising on a bare read breaks 28,347 legitimate ones.

**Corrected contract: a `Value` that resolves to nothing returns null and does not raise. The guard
against nulls sits at the arithmetic boundary (§12.3) instead** — which is the better place on the
merits, not merely the workable one. A null that is read and then tested by `IsNull` is ISO working
as designed; a null that reaches a multiplication is a wrong premium. **Guarding the read protects
nothing and breaks the common case; guarding the arithmetic catches the damage where it happens.**

> **This is the clearest evidence yet for the harness thesis.** Three weeks of reading produced a
> plausible clause. **One real payload falsified it in seconds.** That is the same lesson as the
> stage-1 findings and the same lesson Phase 3 is built on — running the content finds a class of
> defect that reading it cannot.

### Two smaller findings from execution

**`Break` was answered the same day it was raised, by measuring the right relation.** By *direct
parent* it looks incoherent — `Sum` 68, `Sequence` 14, `GetList` 2 — and was filed as OI-74. By
*nearest enclosing loop* it is **84 of 84** (`ForEach` 82, `GetList` 2). The `Sum` cases are
aggregations that themselves sit inside a `ForEach`. **OI-74 closed.** The error was mine and it is
the signature one rotated once more: *a census measures the relation it was asked for, not the
relation that matters.*

**Undeclared tables needed an explicit decision.** 3,056 CSVs in the corpus have no definition file,
including `Pages` — **the single most common lookup target in the language**, 45,388 of 54,716
lookups. Stage 1 honestly marks every column a key when it cannot know. The interpreter matches the
leading columns in filed order, which is the only reading the data supports, **and writes
`lookup-undeclared` into the trace so the inference is attributable rather than silent.**

**One stage-1 change:** `Form Pages` added as a third table kind. `Pages` lives there and neither
table directory holds it, so without it the dominant lookup in the language cannot resolve.

### Also recorded

- **C13** added to the contract. C2's finding — `FromInput`/`FromParam` never filed — is about
  **`FirstValue` only**. `Value` carries `@FromParam` on **47.81%** of its nodes. Read carelessly C2
  says "params don't exist" and an implementer skips half the reads in the language. The two claims
  are now separated on the page, because the first draft did not separate them.
- Banded lookups (`Range` key columns) are **not built** and raise rather than stepping a range,
  which would be wrong by up to the band width. Needed before a premium comes out.

### ▶ Next session

**Stage 3 — the kernel and the two modes.** A submission goes in, a premium comes out. The first
target is Oklahoma's golden case, `976 + 6,845 + 18 = 7,839`.

Three things stage 2 leaves on the table for it, all named above: **the submission-to-tree mapping**
(formally stage 4, but stage 3 needs enough of it to rate), **banded lookups**, and **the referral
register wired into `strict-erc` and `underwriting` modes**.

---

## Entry 5 — Stage 3 built: the kernel. A premium comes out. ~~NEXT SESSION STARTS HERE.~~ *(the live handoff is **Entry 6**)*

- **Date:** 2026-08-13
- **Directed:** *"move on to stage 3"*
- **Built:** `gl_engine/rating/` — `submission.py`, `kernel.py`.
- **Verified:** `tests/verify_stage3.py` **31/31** · `verify_interp` **52/52** · six prior suites
  unchanged · `check 20260811 --deep` **13/13**.

### The headline

**The Oklahoma golden case reproduces exactly: 976 + 6,845 + 2 + 16 = 7,839.**

And not only the total. Compared field by field against ISO's own `1. Output.json`, **all 83
policy-level numbers ISO published agree, and none is missing from our tree.** That distinction
matters: a total can be right for the wrong reasons, and checking only the total would not have
noticed.

Then the breadth question, which is the one that actually tests an engine:

| Against ISO's 50 priced examples | |
|---|---|
| Rate end to end | **50 of 50** |
| Agree with ISO **to the penny** | **22 of 50** |
| Disagree | 28 |

`python scripts/rate_all_payloads.py` is the report, and it writes
`out/reconciliation.csv` so runs can be diffed. **This is the offline half of Phase 2, running
now** — the plan always said it could start before the RAaS connection exists, and it has.

**Every one of those 28 differences is our defect until proven otherwise.** That is not modesty, it
is the doctrine that makes strict mode worth having. They are the next session's work. Both
thresholds are frozen into `verify_stage3.py` group F as a **ratchet, not a target**: 50 must still
rate and 22 must still match, so a change that quietly breaks half the country fails the suite.

### Four things had to be true, and three of them were wrong

**1. The submission-to-tree mapping is one rule.** ISO's rules address repeated elements through a
container — `GeneralLiabilityTable/GeneralLiability` — and a RAaS request has a bare list. **Every
JSON list `X` becomes `XTable` holding repeated `X`.** That is not a convention we chose; it is what
ISO's own paths require.

**2. `ForEach` in a value position yields a collection, not a scalar — and stage 2 had this
wrong.** `Sum` takes a `ForEach` child **18,918 times**; my evaluator returned only the last
iteration, so a `Sum` over five locations would have quietly totalled one of them. **A silent wrong
answer, not an error.** Now `ForEach` yields a `Multi` and the three aggregators — `Sum`, `Max`,
`FirstNonNull` — flatten it, recursively, because `ForEach` nests 3,494 times. A `Multi` reaching a
scalar position is a hard failure.

**3. The path dialect has a predicate, and missing it cost exactly 18.** Paths carry `[1]`:
**18,796 occurrences across all 567 packages, and not one other form** — it is on 88.9% of
`AtOutputDataDef`. Unparsed, `X[1]` looks for a child literally named `X[1]`, matches nothing, and a
`Locate` onto nothing does nothing at all.

> **The failure mode is the one this whole project is built to fear.** No error, no warning — the
> terrorism rows were simply never created, and the premium came out **7,821 against 7,839**. A
> plausible number, short by 18, with nothing anywhere to say so. It was found only because we had
> an oracle to compare against, which is the entire argument for Phase 2.

**4. Rule files are inherited from the parent, and they were not.** 29 `GeneralLiability*Rules`
files are called by state packages that do not hold them — `InitializeRuleSet` on a coverage the
state does not deviate on. They live in the countrywide parent, and the same wholesale-by-name
inheritance N3 gives tables applies to rules. **Without it, 32 of 50 payloads stopped dead.**

### The corpus is not self-contained, and now we can prove it

**`MessageHelper` is called 4,347 times and exists in no package anywhere.** Always
`AddErrorMessage`, always with a message string. ISO's rating service provides it: what it collects
is the `RatingMessages` object in a RAaS response.

So the engine provides it as a declared builtin rather than failing on a missing file, and the
messages are surfaced on the rating. **This is a real limit on the "ERC is the source" doctrine** —
not a large one, but it is the first thing found that ISO's machine-readable content genuinely does
not contain, and it was invisible until something tried to execute the content rather than read it.

Measured properly: **30 rule files are referenced but not filed. 29 of them are ordinary parent
inheritance. Exactly one is host-provided.**

### The two modes, and a register that does not overstate itself

`strict-erc` and `underwriting` are **one code path**; a second implementation would be a second
thing to be wrong. On a clean risk both return 7,839.

The referral register loads all 28 entries. **This build detects exactly one of them (R03, the refer
sentinel), and `Kernel.unenforced` names the other 27.** That is deliberate and it is tested: a
register that claims 28 conditions and silently checks 1 reads as coverage it does not have, which
is the same defect as the stage-1 check that passed while blind. The remaining 27 need load-time
table inspection or hooks inside the rating path — stage 3 work still to do, recorded as such rather
than declared done.

Dispositions are monotonic (D02) and tested: a referral, once raised, is not removed or duplicated.

### A test that was written to fail, and did

`verify_interp` E5 asserted the interpreter **stops** on a named contract clause, phrased so that
running to completion would fail *"update this test"*. Stage 3 made completion meaningful and it
duly failed. The assertion is **inverted rather than deleted**, so the transition from "executes but
cannot rate" to "rates" is on the record rather than tidied away.

### ▶ Next session

**The 28 differences.** Each is our defect until proven otherwise, and they cluster suspiciously:
most are small and positive (+27 to +40 — AL, GA, IA, IN, KY, MN, WY), which reads like one coverage
being added that ISO does not add. A handful are large and mixed (AZ +542, CA −741, IL −419, CO
−158) and are probably distinct causes.

Also still open from stage 3: **banded lookups** (`Range` key columns) still raise rather than step a
range, and the **27 un-enforced register entries**.

---

## Entry 6 — The 28 differences: 25 explained, 3 left. ~~NEXT SESSION STARTS HERE.~~ *(the live handoff is **Entry 7**)*

- **Date:** 2026-08-13
- **Directed:** *"make sure we are logging all of these, and then chase the 28 differences"*
- **Verified:** eight suites green · `verify_stage3` now **32/32** · `check 20260811 --deep` **13/13**.

### The result

| | as filed | with ISO's own `TerrorismCoverage` |
|---|---|---|
| Agree with ISO to the penny | **28 of 50** | **47 of 50** |

**Two were our defects. One was the oracle's.**

### Defect 1 — state overrides were unreachable from parent code (CA, NJ, NY, OH)

Three jurisdictions produced **exactly the products premium and nothing else** — premises/operations
came out **zero**, silently.

Stage 2's dispatch rule said: once a call carries `@ProjectName`, everything downstream stays in the
parent package. That was written to stop the 4,598 call-super rules recursing, and it is **too
strong**. The countrywide `ErcProcess` bare-calls `SetPremOpsLossCost`; **NJ, CA, NY and OH override
exactly that rule**, because their loss costs live in per-territory sliced tables and the override
names each slice explicitly. Keeping a parent-scope caller inside the parent makes **every state
override unreachable from countrywide code** — the countrywide rule runs, its lookup misses a
header-only table, and the premium is short by a whole subline.

**Corrected rule: a bare call always resolves state-first, per RULE, whichever package the caller is
in. `@ProjectName` targets the parent's copy of that one rule and nothing else.** That is what makes
call-super terminate *and* overrides reachable; the two are the same mechanism seen from both ends.
Resolution is also **per rule, not per file** — NJ's coverage file defines the one rule it deviates
on and inherits the rest, so asking whether the *file* exists lands in a package that does not have
the *rule*.

**22 → 28 matches.**

> **This is OI-69's lesson arriving in a new place.** The sliced loss-cost tables were found in stage
> 1 and pinned by an assertion; the rows were reachable the whole time. **What was unreachable was
> the rule that reads them** — and no table-level test could see that.

### Defect 2 — the diff tool buried the answer under its own noise

The first field-level differ reported **130 fields ISO published that we never wrote** and 61 we
wrote that ISO did not. Almost all of it was an artefact: **our tree carries the `XTable` containers
ISO's rule paths require and ISO's response does not.** Normalising them away left **5 differing
fields**, of which one mattered. A diagnostic that reports 130 findings where there is 1 is worse
than none, because nobody reads the 131st line.

### The oracle defect — OI-77

The remaining 20 states clustered at **+16 to +40**, which reads like one coverage being added that
ISO does not add. It was: we created a classification-level `GeneralLiabilityTerrorism` row where
ISO created none.

Chasing the guard led somewhere unexpected. **34 of 50 `Payloads/` pairs carry
`TerrorismCoverage="Yes"` on the input and `"No"` on ISO's own output** — and **every other echoed
field agrees**: subline, limits, coverage form, class code, exposure, the rating-plan flags. No rule
in any package writes that field, so the output is an echo rather than a computation.

Three lines of evidence, and they agree:

1. **Taking ISO's echoed value lifts agreement from 28 of 50 to 47 of 50.** Nothing an engine gets
   wrong produces that.
2. The untouched **STC** pair inside the corpus carries `"No"` on the input and reproduces to the
   penny.
3. `Payloads/OK`, reconciled, prices to **7,839 — the golden answer derived independently three
   weeks ago** — against a filed output of **8,229**. That pair is mismatched beyond this one field.

**Conclusion: the `Payloads/` inputs were altered after the outputs were generated.**

**The tooling reports both runs and never substitutes ISO's answer silently.** That restraint is the
point: quietly copying the oracle's input into our own would raise the headline number and **hide the
first real defect that appears there**. `verify_stage3` group F now ratchets *both* figures — 28 as
filed, 47 reconciled — and neither may fall.

> **Second time this project's oracle has been wrong about itself** (OI-67 was the first). **A
> comparison run is only as good as the pairing, and the pairing is now something to check rather
> than assume.**

### What is left — OI-78

**AK +1, AZ +511, and OK unusable.** Both survivors are ours until proven otherwise.

**AK is not the rounding mode.** It is +1 under `ROUND_HALF_UP`, `ROUND_HALF_EVEN` **and**
`ROUND_DOWN` — so OI-70 is untouched by this evidence and remains open on its own terms. The
difference localises to `GeneralLiabilityPremOpsPremiumToReachMinCoverage/CoveragePremium`, 611
against 610.

### Logging brought current

The user asked for this first, and it was owed. **`docs/FROM-PLANNING-TO-BUILD.md` had been
neglected for two whole stages** — the one file whose entire value is being written *alongside* the
build rather than after it. Stages 2 and 3 are now filled in, including where the *Expected* column
was wrong, which is what it is for:

- **Stage 2:** the node census was right and chose the architecture; **N2's parent dispatch, predicted
  as the hardest mechanism, was one boolean**, while the three things that actually cost the time —
  the entry point, `ForEach` as a collection, positional predicates — **were not on the list at all**.
  *Verdict: an analysis phase can size a language reliably and cannot specify it.*
- **Stage 3:** half the inherited analysis was **made moot by the architecture** (coverage ordering
  never became a decision), and the golden case, predicted to *"pass early"*, **passed last** — it was
  the instrument that found every stage-3 defect. *Verdict: the value of the analysis was not that it
  told the build what to do, but that it could tell the build it was wrong.*

Also brought current: `docs/BUILD-STAGES.md` (stages 2 and 3 marked built, with what each actually
cost), `docs/OPEN-ITEMS.md` (**OI-70 through OI-78**), and `TESTING.md` — where the golden-case
command in the first draft **pointed at the wrong file** and would have printed `7852`, a number that
looks like a failure. Corrected against actual output, per that file's standing rule.

### ▶ Next session

**OI-78: AK's +1 and AZ's +511.** `python scripts/diff_payload.py AK` localises in seconds now.

Then the rest of stage 3's remainder: **banded (`Range`) lookups**, still refusing rather than
stepping a range, and the **27 referral conditions** carried but not enforced.

---

## Entry 7 — OI-78 closed: 48 of 48 usable oracles agree. ~~NEXT SESSION STARTS HERE.~~ *(the live handoff is **Entry 8**)*

- **Date:** 2026-08-13
- **Directed:** *"Log, and move on to OI-78"*
- **Verified:** eight suites green · `verify_stage3` **33/33** · `check 20260811 --deep` **13/13**.

### The result

| | |
|---|---|
| As filed | 28 of 50 |
| With ISO's own `TerrorismCoverage` (OI-77) | 47 of 50 |
| **Against the oracle that actually corresponds to each input** | **48 of 48** |

**Zero surviving differences. All three were the oracle, and not one needed a change to the
engine.**

### Each one, and how it was established

**Every one was found from the files, never from the premium.** That distinction is the whole
discipline here: an explanation reached by working backwards from a number we wanted is not
evidence, it is fitting. `scripts/check_payload_pairs.py` finds all three without looking at a
premium at all — it compares the fields ISO **echoes** rather than computes, on the principle that
if the engine cannot change a field then the input and the output must agree on it.

**AZ — there is no Arizona output.** `Payloads/AZ/1. Output.json` carries **`State: AK`**. It is
Alaska's output, mis-filed. Arizona therefore cannot be evaluated at all, and the +511 was never a
defect: we were comparing Arizona's rates against Alaska's answer.

**AK — two conflicting Alaska outputs, and we match the right one.** With the mis-filed copy
identified, Alaska has two. They are **identical in 403 of 412 fields.** The whole difference:
the AK-folder copy lacks `GeneralLiabilityMedPayCoverage/Limit`, which Alaska's **input supplies**.
That one field decides a branch in `SetMedicalPaymentsCharge`, which turns `0.945` into a charge of
1 rather than 0, and the premium into 7,386 rather than 7,385. **The correctly-paired output — the
one mis-filed under AZ — is 7,386, exactly what the engine produces.**

**OK — ISO rated it against content we do not have.** Base rate `0.093` and ILF `2.14`. We hold two
candidate editions, `GL_OK_20250601_V01` and `GL_OK_20270401_V02`, and **both file `0.095`.** The
payload's effective date is 2026-08-01 and the newest applicable edition in the corpus is dated
2025-06-01, so ISO almost certainly rated it against a 2026 Oklahoma filing we have not been given.
Not reconcilable, and not a defect.

### What was ruled out, and why that matters

**The rounding mode is not the cause, and OI-70 is untouched.** Alaska's difference was exactly 1
and looked like the tie-break question finally surfacing. It is not:

- AK is +1 under `ROUND_HALF_UP`, `ROUND_HALF_EVEN` **and** `ROUND_DOWN` — `0.945` at 0dp is not a
  tie, so every half-rule gives 1 and only truncation gives 0
- Truncating **all** `Product`/`Divide` sites scored **11 of 50**; truncating only at 0 decimal
  places scored **18**. Against **47** for round-half-up. **ISO rounds.**

> **This is the more useful half of the result.** A cheap explanation was available — *"ISO
> truncates"* — and it fitted the one case in front of me perfectly. Measuring it across all 50
> killed it in one run. **A hypothesis that explains the case you are looking at and nothing else is
> the most expensive kind of wrong**, because it gets written into an engine and quietly moves every
> premium.

### The tooling this produced

| | |
|---|---|
| `scripts/check_payload_pairs.py` | **validates the pairing before any premium is compared.** Identity (`State` on folder, input and output) and every echoed scalar. Finds AK, AZ and GA |
| `scripts/diff_payload.py` | field-level differ, deepest-first; applies the OI-77 correction by default so the artefact does not mask the cause |
| `scripts/rate_all_payloads.py` | now reports **three** views — as filed, terrorism-corrected, and against usable oracles — and names the exclusions with reasons |

**Three views, always, and the headline is never the best one alone.** The exclusions are declared
on the same line as the number they improve.

### Ratchets

`verify_stage3` group F now pins all four: **50 rate**, **28 as filed**, **47 terrorism-corrected**,
**48 of 48 comparable**. F4 additionally requires that comparable matches *equal* comparable pairs —
it fails if a difference appears at all, not merely if the count drops.

> **Third time this project's oracle has been wrong about itself** — OI-67, OI-77, and now OI-78.
> The lesson has earned permanent status: **validate the pairing before comparing the answer.** A
> reconciliation harness that assumes its own inputs are matched will report the engine as broken and
> be believed.

### ▶ Next session

**Stage 3's remainder, now that nothing is disagreeing.** Two named items: **banded (`Range`)
lookups**, which still refuse rather than stepping a range, and the **27 referral conditions**
carried but not enforced (`Kernel.unenforced` names them).

Then **stage 4 — schemas and payloads**, where the submission mapping written for stage 3 becomes a
documented format per jurisdiction.

**`OI-70` (the rounding mode) is now the oldest open question the corpus cannot answer**, and it
needs RAaS or an ISO clarification. Everything offline agrees with `ROUND_HALF_UP`.

---

## Entry 8 — Stage 3 complete, and three filings arrive. ~~NEXT SESSION STARTS HERE.~~ *(the live handoff is **Entry 9**)*

- **Date:** 2026-08-13
- **Directed:** *"Added the files"* · *"Finish stage 3"*
- **Verified:** eight suites green — `verify_interp` **58/58**, `verify_stage3` **37/37** — both deep
  checks **13/13**, reconciliation **49 of 49 usable oracles**.

### Part 1 — the corpus grew, and the engine got louder before it got righter

Three Oklahoma-related packages were supplied: `GL_OK_20261001_V01`, then on request
`GL_CW_20261001_V01` and `GL_OK_20260801_V01`. **Corpus 567 → 570.**

**The middle step is the one worth recording.** Unpacking the October filing alone made the engine
**refuse Oklahoma for 2026-10-01 through 2027-03-31**, because that filing declares a countrywide
parent the corpus did not yet hold and N5 forbids substituting the newest. **Before it was unpacked
that window had been silently priced against the June 2025 rulebook.** Adding content made the
engine visibly *less* capable for a day, and that was the correct direction: a loud refusal
replaced a quiet wrong answer.

With all three present, `Payloads/OK` resolves to **`GL_OK_20260801_V01 over GL_CW_20260101_V01` —
exactly the package ISO's own response header names — and reconciles to 8,229 with zero differing
fields.**

**The coordinated change was done in full, and mechanically.** All four censuses re-run; the
evaluation contract's figures **remapped from the old census to the new by program** — a number is
rewritten only when it equals the old value for that node in a specific role, and only to the new
value for the same role, with anything ambiguous reported and left alone. **Doing it by eye is how
seven wrong edge counts got in the previous round.** Five pins updated and *kept* rather than
relaxed: packages `567→570`, STC files `517→519`, countrywide editions `10→11`, and the N5 parent
groups — **Oklahoma left the `GL_CW_20231201_V03` group**, now `NJ/TX/VT`.

> **A pin that fires on a legitimate change has not failed; it has worked.** Each of these was a
> real fact about the corpus changing under the engine, and each was seen because something asserted
> it.

### Part 2 — banded and interpolated lookups

Measured before built (`scripts/erc/46_banded_lookups.py`). The population is **11 table names,
every one reachable**, each with **exactly one key range** alongside plain equality columns, **two
boundary types** — `FromInclusiveToExclusive` (115 definitions) and `FromExclusiveToInclusive` (78)
— and **two interpolated tables**, both size-of-risk relativity, both `Linear`.

- Boundaries are exact: `10878 → 0`, `10879 → 0.03` on a `FromInclusive` band
- Interpolation is linear along the key band **and traced**, so a factor can be re-derived
- A value outside every band returns **null**, never the nearest

**P5's open question is closed by the corpus, not by a decision.** It asked how `RangeType` and
`InterpolateMode="Linear"` combine at an exact boundary. **Interpolation only ever occurs on
`FromInclusiveToExclusive` ranges**, where `x == lo` gives position 0 and `x == hi` belongs to the
next band. The awkward combination does not exist in the filed content.

### Part 3 — the referral register, with no silent middle

Loading the register was never the hard half. **The conditions are prose written for a human**, and
the previous build detected **one** of 28 while reporting all 28 as loaded.

Every entry now carries an explicit disposition:

| | | |
|---|---|---|
| **DETECTED** | **9** | a detector runs on every rating in `underwriting` mode |
| **NOT_REFERRAL** | **4** | decided not to be referrals — the engine's silence is a *behaviour* |
| **CONFIG** | **1** | answered when the engine is configured, not per rating |
| **PENDING** | **14** | genuinely not built, **named individually** |

`Kernel.coverage()` returns the four buckets and `verify_stage3` **D6 fails if `unenforced` ever
returns a bare count instead of names**.

**Detectors observe; they never re-derive.** Each reads the rated tree, the trace or the resolved
book. A detector that recomputes a premium is a second implementation and therefore a second thing
to be wrong.

**The one that fired is real, and ISO agrees with it.** Across all 50 payloads both modes return
**identical premiums** and detectors fire on **exactly one** submission. Alaska's attorney's-fee
limit is below its subline limit; the endorsement prices at **−70**; **ISO's own response carries
the same −70 and an error message our `MessageHelper` builtin reproduces verbatim.** The detector
found a negative factor without being told anything about attorney's fees.

> **That is three independent confirmations in one case** — we reproduce ISO's premium, ISO's
> validation text, and we flag it for a human. It is the clearest single demonstration so far that
> the interpreter is executing ISO's content rather than approximating it.

### What is honestly still missing

**OI-81: 14 conditions carried and not detected.** Recorded as a number that can be read rather than
left implicit. **Most are load-time statements about deviations the engine already handles
correctly** (R05, R07 — CA/NY disable a coverage by rule; R06 — NY withdraws claims-made); they are
`fail=n/a` and a detector would report a condition rather than prevent a wrong number. **Five can
produce a wrong number and need specific rating-path hooks: R12, R15, R17, R25, R26.**

### ▶ Next session

**Stage 4 — schemas and payloads.** The submission mapping written for stage 3 becomes a documented
request format per jurisdiction, with a worked example each. Four states carry a county-or-place
field (E8); **Hawaii is not in the corpus and cannot be rated**.

Also open: OI-81's five substantive conditions, and Arizona's missing output file (OI-78).

---

## Entry 9 — Stage 4 complete: the schema was filed, not ours to design. **NEXT SESSION STARTS HERE.**

- **Date:** 2026-08-13
- **Directed:** *"Move on to Stage 4"*
- **Built:** `gl_engine/schema/` and `scripts/build_sample_payloads.py`.
- **Verified:** `tests/verify_stage4.py` **23/23**; nine suites green; deep check **13/13**.

### The finding that made the stage smaller

The plan expected stage 4 to **derive** a submission format from the 53 RAaS payloads. It did not
have to. **ISO files the schema**, in a directory no analysis step had opened:

`Form Fields/Fields.FormField.csv` declares, per jurisdiction and per field, its control, its label,
whether it is required on a policy or a quote, its default, its minimum and maximum, the condition
under which it applies at all, and **the domain table naming its legal values**.
`Ratebook Columns/RatebookColumns.FormPage.csv` adds `RatingRequiredCondition` — required *to rate*,
which is a stricter and different question from required on a form.

**Countrywide declares 1,381 fields over 429 tables**; each jurisdiction resolves to **1,252–1,321**.
**No field is required in every jurisdiction**, which is why the schema is per-jurisdiction rather
than one shape with exceptions.

> **Third time this build has found the answer already in the corpus** — the `Default` block, the
> response header naming the edition, and now the field schema. Each was in a file nobody had a
> reason to open until something needed it. **The transferable instruction is blunt: before deriving
> anything from examples, enumerate the directories in the package and ask what each is for.**

### Two things the field data itself corrected

**`Type` is a form control, not a data type.** `TEXT`, `SELECT`, `CHECKBOX`, `HIDDEN`, `TEXTAREA`,
`BUTTON`, `ANCHOR` — it says how ISO's screen renders the field. **A validator reading `TEXT` as
"string" would accept an exposure of `"banana"`.** Data types come from the DataDefs and legal
values from the domain table; the module says so where it would otherwise be assumed.

**`DataValue` is the stored value; `DisplayValue` is what the screen shows.** The obvious
implementation — *"take the first column that is not the state"* — was written first and was wrong:
on a ZIP-to-territory table it returns the **ZIP**, so **every real territory came back illegal**.
It reported 8 errors on a submission ISO itself priced without complaint. Reading `DataValue`
cleared all 8. Domains with leading dependency columns are unioned rather than resolved, which makes
the answer a **safe superset** — stated in the code, because a superset presented as exact is a lie
about coverage.

### E8 restated from measurement

The plan says *"four states resolve territory by county or place"*. **The count is right and the
mechanism was not. There is no county field anywhere in the corpus** — the first search for one
matched `PremiumPlaceHolder`.

What is actually filed: **exactly four jurisdictions — CA, FL, NY, TX — declare `TerrorismTerritory`
against a state-specific `TerrorismTerritoryCode` domain**, while **11 others derive it from a ZIP**
(`TerritoryCodeByZipCode`), and **NY alone** adds a Manhattan flag and a territory indicator. E8's
"by county or place" is better read as **"by a code that cannot be derived"** — which is exactly why
R22 refers on an unmatched one and forbids a fuzzy match.

### The deliverable

**One sample submission per jurisdiction, carrying the identical risk** — class `50017`, 5,000,000
of gross sales, 1M/2M CSL, no deductibles, no rating plans — so a price difference is attributable to
the jurisdiction and nothing else. Only what *must* vary does: the jurisdiction, and the territory
codes, which are a state's own and cannot be held constant.

| | |
|---|---|
| Jurisdictions with a sample | **51 of 51** |
| Rate end to end | **51 of 51** |
| Schema errors across all of them | **0** |
| Same risk, cheapest | **GA 6,845** |
| Same risk, dearest | **NY 12,141** |

**Puerto Rico has no RAaS payload of its own** — the plan records it as the only such jurisdiction —
so **its sample is built from ISO's own domain tables**, which file exactly one premises/operations
territory and one products territory. Nothing about it is invented.

**ISO's own 50 submissions validate with zero errors** and 225 warnings, all of them envelope fields
ISO's form does not declare. Validation returns **findings, not exceptions**: a submission with three
problems reports three, and validation never decides whether a rating happens — the engine's own
refusals are stricter and better placed.

### The quiet success

**All 51 jurisdictions rate the same risk with no jurisdiction-specific code anywhere**, including
the four sliced loss-cost states. Stage 4's `Expected` column predicted that state table-shape
differences would be absorbed by the interpreter *or* would surface as a late stage-2 defect.
**They were absorbed. No stage-2 defect surfaced.**

### ▶ Next session

**Stage 5 — the enum workbook.** An Excel listing every field a payload can carry and its legal
values. **Most of it now exists as data**: `Schema.legal_values()` reads ISO's domain tables and
`scripts/erc/47_input_schema.py` has already emitted the field surface as CSV. The remaining work is
the workbook itself and cross-referencing against what the 50 real submissions actually use, so it
covers what is used rather than everything conceivable.

Then **stage 6 — the UI**, and **Phase 2** against live RAaS.
