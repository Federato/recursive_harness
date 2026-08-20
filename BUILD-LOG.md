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

### Rule #1 — enumerate the directories before deriving anything from examples

**Designated by the user on 2026-08-13 as this project's first rule.** Before deriving a format, a
schema or a behaviour from examples, **list every directory in the source and write one line on what
each is for — including the ones that look irrelevant.**

It is rule #1 because this build hit it three times, and every time the answer was already filed in
a directory nobody had opened:

| | |
|---|---|
| **The entry point** | every census walked `Rule` elements, so none could see the `Default` block — a child of the document root. An interpreter started where the analysis said would have returned a complete premium with no expiry date and no total |
| **The edition ISO rated with** | the response header says so outright: `"Scheme": "GL OK 20260801 V01"`. It went unread for a day while the same question was answered indirectly and, twice, wrongly |
| **The submission schema** | stage 4 was planned as *derive the format from 53 example payloads*. `Form Fields/Fields.FormField.csv` declares it — every field, per jurisdiction, with requiredness, bounds, conditions and its legal values |

**Deriving from examples produces something that fits the examples.** Reading the declaration
produces the thing itself, and the difference only ever shows up on the case the examples did not
cover — which is exactly the case nobody checks. An unopened directory is an unmeasured population,
and that is this project's signature failure wearing a different coat.

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
| **5** | The enum workbook | ✅ **COMPLETE 2026-08-13** — 18/18. `GL-Submission-Fields.xlsx`, standard library only. ISO declares 1,259 fields; real submissions use **77** |
| **6** | The UI | ✅ **COMPLETE 2026-08-13** — 23/23. `app.py`, one file, standard library only. The separation held; asking for per-subline premiums found a real engine defect (OI-85) |

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

## Entry 9 — Stage 4 complete: the schema was filed, not ours to design. ~~NEXT SESSION STARTS HERE.~~ *(the live handoff is **Entry 10**)*

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

---

## Entry 10 — Rule #1, then stages 4 and 5 finished. ~~NEXT SESSION STARTS HERE.~~ *(the live handoff is **Entry 11**)*

- **Date:** 2026-08-13
- **Directed:** *"this should be the #1 rule moving forward"* · *"lets resolve form related fields
  first"* · *"move on to Stage 5"*
- **Verified:** ten suites green — `verify_stage4` **28/28**, `verify_stage5` **18/18** — deep check
  **13/13**.

### Rule #1

**Before deriving anything from examples, enumerate the directories and ask what each one is for.**
Recorded in the standing constraints **above the stage gates**, because it outranks them: a gate
checks that the work was done, this checks that the right work was started.

It earned the place three times before being written down — the `Default` block, the response header
naming the edition, and the submission schema. **Applied immediately, it earned it a fourth time.**

`48_directory_census.py` enumerates all 12 directories in an ISO package. **The engine reads 7 and
had never opened 5.** `49_doc_workbook.py` then read the largest of them:

| In `DOC/*.xlsx`, one workbook per package | |
|---|---|
| `Refer to Company` | **5,642 rows, 838 distinct conditions, 38 jurisdictions**, each with the manual rule number and *Customer Implementation Guidelines* |
| `Base RaaS Overrides` | **63,327 rows over 435 fields, carrying the DATA TYPE** — which stage 4 had recorded as needing to come from the DataDefs |
| `Class Description` | **2,489 class codes** with descriptions |
| `Not Supported` | 428 rows naming what ERC does not do |
| `Special Consideration` | 1,126 rows across 47 jurisdictions |

**Our referral register is 28 conditions derived by hand. ISO declares 838.** Different populations
— ours are rating failure modes — but OI-81's 14 pending conditions must be checked against ISO's
declaration before another is derived. Recorded as OI-82 and OI-83.

### Form related fields, resolved — and the coverage measured first

A field's legal values can depend on another field's value. ISO files that dependency; we had never
read it, so stage 4 validated against the **union** of every possibility.

**The coverage measurement came before the implementation, and it changed what got built.** Of 319
fields naming a domain table, **90 are dependent, and ISO declares the relationship for 29 (32.2%)**
— not all. Had it been built first and measured after, it would have shipped looking complete.

- **The 29 resolve exactly.** The declared path is evaluated against the submission using the same
  `../../` dialect stage 2 already implements. On a 1,000,000 CSL policy the terrorism aggregate
  narrows from 15 values to 13; on a 25,000 CSL policy the drone aggregate narrows from 15 to **4**.
- **The other 61 stay on the union** — a safe superset, which can never reject a legal value, only
  accept an illegal one — **and every finding now says which of the two it is.** *A validator that is
  exact for some fields and a superset for others, without saying which, is worse than one that is
  always a superset.*
- Measured over ISO's 50 submissions: **100 checks exact, 637 superset.**

**A shortcut was available and was rejected on evidence.** The dependency column usually looks like a
field name — `PremOpsBIPDDeductible` is keyed by `PremOpsBIDeductible`, a sibling — so resolving by
name would have claimed all 90. But **`GeneralAggregateLimit` is keyed by `EachOccurrenceLimit` and
no such field exists**; the real one is `PremOpsProdsEachOccurrenceLimit`. A name lookup would have
failed silently on a subset while appearing to work. Four cases were checked before deciding and one
of the four broke it. Recorded as OI-84.

### Stage 5 — the workbook, and the number that justifies it

`GL-Submission-Fields.xlsx`, seven sheets, **written with the standard library only**
(`scripts/xlsx.py`) — the engine has no third-party dependency and a deliverable should not
introduce one.

**The plan predicted the hard part would be scope rather than extraction, and it was right.** That
is the only stage in this build whose `Expected` column named the real difficulty in advance.

| | |
|---|---|
| Fields ISO declares, countrywide | **1,259** |
| Used by the 50 real submissions between them | **77 — 6.1%** |
| Used by all 50 | **41** |
| Carried by any single submission | **43–54** |

The `Used in practice` sheet is ordered by how often a field is actually sent, so it opens on what
matters rather than on an alphabet. **The corpus says what is possible; only the submissions say what
is sent.**

Every column names the ISO file it came from, and a domain over 60 values is **summarised rather than
silently truncated** — `ZipCode` at 765 is a lookup, not a choice.

### One correction

The read-me first said a real submission uses *"about 4%"* of the declared surface. The measured
figure is **77 of 1,259 = 6.1%**, and any single submission about 3%. Corrected before commit —
a rounded number that nobody would have checked is exactly the kind that survives into a slide.

### ▶ Next session

**Stage 6 — the UI.** Paste a submission, rate it, read the result: every factor in order with its
source, premiums per coverage and per subline, referrals shown as referrals with what would clear
them, and a mode switch. **Strictly separate from the engine** — the engine must never import it, and
notebook use comes free if that separation holds.

Also open: **OI-81's 14 pending referral conditions, now checkable against ISO's 838 declared ones**;
OI-84's 61 undeclared dependencies; and **the 508 STC submissions**, reserved for form-attachment
testing.

---

## Entry 11 — Stage 6 built. **All six stages are complete.** ~~NEXT SESSION STARTS HERE.~~ *(the live handoff is **Entry 12**)*

- **Date:** 2026-08-13
- **Directed:** *"On to Stage 6"*
- **Built:** `app.py` — one file, standard library only, no framework, no build step.
- **Verified:** `tests/verify_stage6.py` **23/23** · **eleven suites green** · deep check **13/13** ·
  reconciliation unchanged at **49 of 49**.

### The interface

`python app.py`, then `http://127.0.0.1:8765`. Load a sample or paste a submission, pick a mode and a
rounding rule, rate it. The result shows the premium, **premiums per subline and per coverage in
their own arrays**, every rating factor in the order it was used **with the ISO file it came from**,
referrals with what would clear them, ISO's own validation messages, and the submission check.

### The claim the plan made, and how it turned out

The plan wrote this before any of it existed:

> *"We expect it to prove the separation rather than build anything: if the UI needs the engine to
> change, the engine's interface was wrong."*

**The interface held.** No engine change was needed — the whole UI is assembled from `premium`,
`by_coverage`, `referrals`, `messages`, `trace`, `tree` and `packages`. The suite checks the
separation by **reading the engine's source for an import of the UI** rather than trusting that
nobody added one, and confirms `Kernel().rate(path).premium` works with the UI never imported.

**The implementation did not hold, and that is the finding.**

### A whole class of ISO output was missing, and nothing had noticed

The deliverable asks for *premiums per subline*. The subline is a statistical code — `334` for
premises/operations, `336` for products — that ISO writes on every coverage. **We were writing none
of the statistical codes at all.**

`ErcSetStatisticalCodes` is guarded by:

```xml
<rul:Exist AtInputDataDef="ancestor::MasterGLCW/Policy" />
```

`interp/tree.py` implemented `..`, `.`, `*`, `name` and `name[n]` — **not the `ancestor::` axis**. An
unimplemented axis matches nothing, `Exist` reads false, and the entire block was skipped **with the
premium still exactly right**.

Measured before fixing anything (`scripts/erc/51_path_axes.py`): **942 paths carry an axis, every one
of them `ancestor::`, in 34 forms, targeting `Policy`, `EffDate` or `ExpDate`. There is no other axis
anywhere in the corpus.**

**The name after `::` identifies the schema, not a node to match.** Countrywide rules say
`ancestor::MasterGLCW` while executing inside Oklahoma, whose own master is `MasterGLOK`; a name
match would fail for all 50 states, so it cannot be what ISO does. It means *at the document root*.

With it implemented, **every statistical code matches ISO's golden output exactly — 0 mismatches** —
and not one premium moved.

> **Four stages of tests and 49 of 49 exact premiums had not caught it, because every check so far
> compared numbers and a statistical code is a string.** A deliverable that renders *everything*
> finds things a deliverable that asserts something *specific* never will. The UI was the first
> consumer that wanted all of the output rather than the parts we knew to check.

### All six stages are complete

| | | |
|---|---|---|
| 1 | Load and resolve | 20/20 |
| 2 | The interpreter | 58/58 |
| 3 | Kernel and the two modes | 37/37 |
| 4 | Schemas and payloads | 28/28 |
| 5 | The enum workbook | 18/18 |
| 6 | The UI | 23/23 |

**Eleven suites, 13/13 load-time assertions at two dates, and 49 of 49 usable oracles agreeing with
ISO to the penny.**

### `FROM-PLANNING-TO-BUILD.md` is finished

Its last section — *"of the twenty-odd analysis steps that preceded this build, which would you
repeat for Commercial Property, which would you do differently, and which would you skip?"* — was
written from the six verdicts, as the file required. In short: **repeat** the counting discipline,
finding the oracle first, and the doctrine work; **do differently** by taking the
instruction-language measurement on day one, enumerating package directories before deriving
anything, and budgeting specification separately from sizing; **skip** deriving control flow
entirely, and read ISO's 838 declared refer conditions before hand-deriving a register.

Its closing observation is the one worth carrying:

> **Every significant defect in this build was the same shape — something measured in one place and
> stated about everything.** It appears in the analysis phase, in stage 1's assertions, in stage 2's
> contract, in stage 3's dispatch and in stage 6's path dialect. **It is not a knowledge problem and
> more analysis does not fix it.** What fixes it is enumerating the population before making the
> claim.

### ▶ Next session

**Phase 2 — proof against ISO's live service.** The offline half is clean at 49 of 49; connecting
RAaS extends it past these examples and is the only thing that can settle **OI-70, the rounding
mode**, which the filed content genuinely cannot answer.

Before or alongside it, three known pieces of work: **OI-81's 14 pending referral conditions**, now
checkable against ISO's **838 declared** ones (OI-82); **OI-84's 61 dependent domains** ISO does not
declare; and **the 508 STC submissions**, reserved for form-attachment testing.

---

## Entry 12 — Phase 2 is live. 50 of 50 agree with ISO. ~~NEXT SESSION STARTS HERE.~~ *(the live handoff is **Entry 13**)*

- **Date:** 2026-08-13
- **Directed:** *"lets do phase 2, we should be able to see a prior build that worked for ISO RAAS
  here C:\\Projects\\Will_Dan_Collab_dev"*
- **Verified:** `tests/verify_phase2.py` **11/11** · twelve suites green.

### The result

| | |
|---|---|
| Jurisdictions sent to ISO's live service | **51 attempted, 50 answered** |
| Premium **and every published field** agree | **50 of 50** |
| ISO used the edition we resolved | **50 of 50**, from its own response header |
| Not answered | **PR** — entitlement, not a defect (OI-86) |

**Our engine and ISO's own rating service now agree on fifty jurisdictions, on every number ISO
publishes, not merely on the total.**

### Rule #1, again, and it saved the whole stage

The prior build was enumerated before anything was written: 12 top-level entries, `iso_rater_harness/`
with twelve modules, `Sample Payloads/`, a Postman collection. **The protocol turned out to be OAuth
2.0 client credentials and a JSON POST** — and the sample request/response shapes are **exactly** what
this project already produces and diffs.

So Phase 2 was not an integration. It was a client and a comparison:

* `scripts/raas.py` — **standard library only.** The prior client uses `httpx`; the protocol does not
  require it, and this project has no third-party dependency to spend. Credentials come from the
  environment, never from a file in this repository.
* `scripts/phase2_compare.py` — rate locally, rate live, diff **every published field**, and report
  the edition ISO used alongside the one we resolved so a resolution difference can never be mistaken
  for an arithmetic one.

**Our samples needed no reshaping at all.** Stage 4's generated submissions go to ISO as filed, with
only the authorisation block added.

### What Phase 2 settled about the rounding mode — and what it did not

OI-70 has been the oldest question the filed content cannot answer. **Phase 2 answered half of it,
and the half it could not answer is stated rather than glossed.**

**Truncation is ruled out.** `ROUND_DOWN` changes the premium in **37 of 51** jurisdictions, and ISO
agrees with rounding in all 50 answered. Arkansas exercises a genuine tie — a `Product` of exactly
`1.5000` at 0dp — where truncation gives **7,871** and ISO gives **7,872**.

**Half-up versus half-even is still open.** They differ on **0 of 51** submissions. Searching all
1,529 rounding operations across every sample found **exactly one** true tie, and it is `1.5`, where
both modes give 2. **No submission we hold can separate them.** Settling it needs one engineered to
produce `x.5` with `x` even.

> **It would have been easy to write "Phase 2 confirms ROUND_HALF_UP".** Fifty of fifty match and the
> default is half-up. The honest statement is narrower: *ISO rounds rather than truncates, and the
> tie-break between the two rounding modes remains unevidenced.* The mode is recorded on every
> rounded value in the trace, so whichever it turns out to be, every answer stays attributable.

### Two things the live run exposed

**Puerto Rico has no external confirmation of any kind (OI-86).** RAaS returns
`401 "Permission is not granted to GL PR for rating. Please check subscription."` PR also has no
stored priced example (OI-79), and its sample had to be built from ISO's own domain tables. **It is
the one jurisdiction shipping wholly unverified**, and that should be an explicit decision rather
than a gap nobody names.

**The population is now the limit, not the engine (OI-87).** All 51 submissions are the *same risk* —
one location, one classification, class `50017`, gross sales, no deductible, no rating plans,
terrorism off. Stage 4 chose that deliberately so state differences would be attributable, and it
did its job. But **50 of 50 on one risk shape is a narrower claim than it sounds**, and the live
service will rate anything. Breadth — deductibles, claims-made, size-of-risk, multi-location,
multi-class, the rating plans — is the next work, and `phase2_compare.py` already takes any
submission.

### A note on the tests

`verify_phase2.py` **skips cleanly without credentials**, because a suite that needs a paid external
service to pass is a suite people stop running. Its offline group checks the client by **parsing the
source**, not grepping it — the first two versions failed on their own naivety, flagging the
docstring that explains why `httpx` is *not* used, and then a hostname and the literal string
*"(token withheld)"*. Both were the test reading prose as code.

### ▶ Next session

**Phase 3 — the self-correcting loop**, or **breadth first (OI-87)**. The argument for breadth first:
a harness that adjudicates differences is worth building once there are differences to adjudicate,
and on one risk shape there are none.

Also open: **OI-70's remaining tie-break**, which needs one engineered submission and would close the
oldest question in the project; **OI-86**, Puerto Rico's entitlement; **OI-81's 14 referral
conditions** against ISO's 838 declared; and the **508 STC submissions** for form attachment.

---

## Entry 13 — ISO comparison in the interface, and a full test run anyone can read. ~~NEXT SESSION STARTS HERE.~~ *(the live handoff is **Entry 14**)*

- **Date:** 2026-08-13
- **Directed:** *"I want to be able to rate a submission with the engine, and get RAAS results back
  as well from within the UI. I also want to be able to kick off a large run of tests (engine and
  raas) from the UI, and get a clear UI return of all results (Test #, Engine Premium, RAAS Premium,
  Pass or Fail), in a visualization that will make sense to a layman."*
- **Verified:** `verify_stage6` **30/30** · twelve suites green.

### One submission, both answers

A **Compare with ISO** checkbox next to `Rate`. The premium card then reads:

> Our engine **8229** ISO **8229.0** — **They agree**

and, when they do not, *"They differ by ..."* with the delta. If ISO named a different rulebook
edition from the one we resolved, that is shown too — **a resolution difference must never be
mistaken for an arithmetic one.**

**ISO being unreachable degrades the page to engine-only rather than breaking it.** The engine is
the product; the comparison is the check. A missing credential or a dead gateway shows a reason, not
a stack trace.

### A full run, in language that does not assume the reader knows any of this

**Test every jurisdiction** → *Run the full test*. 51 submissions, each rated by the engine and then
by ISO. It reports, in this order:

1. **`50 of 51 match ISO exactly`** — the headline, before any detail
2. a **green / red / grey bar**, labelled *agree · differ · not yet run*
3. a table: **# · State · Our engine · ISO · Difference · Result**, with a green **Match** or a red
   **Differs** badge and failing rows tinted

**It runs in a thread and the page polls it.** 51 live calls at roughly ten seconds each is nine
minutes; a request that takes nine minutes to answer is a request that times out. Rows appear as
they finish, so the table fills in front of you rather than arriving at the end.

> **The wording is deliberate.** Not `PASS`/`FAIL` in the abstract but *"50 of 51 match ISO
> exactly"*, and under a failure, *"every difference is our defect until proven otherwise"* — the
> project's doctrine, said where someone reading a red row will actually see it.

**The result of record remains the command-line run** — `scripts/phase2_compare.py --all`, 50 of 51,
PR refused on entitlement (OI-86). **The page ran all 51 through the live service itself and landed on
the same place** — `50 of 51 match ISO exactly`, *No differences*. **A full live run through the page takes twenty
minutes or so**, because each jurisdiction is a real call; the command line stays the faster route,
and the page exists so the answer can be read by someone who would never run either.

### Then Puerto Rico was ruled out, and it is implemented rather than noted

*"disregard Puerto Rico moving forward, we don't have access."* **OI-86 is a decision now, not an
open question.** The subscription does not cover GL PR and the entitlement is not obtainable.

`NO_ISO` in **`scripts/raas.py`** is the single definition — it belongs next to the client that hits
the boundary, not copied into each caller. `phase2_compare.py --all`, the batch runner and the
single-submission comparison all read it, leave PR out of a comparison, and **say which jurisdiction
and why** rather than dropping it silently. The single-submission path refuses *before* the call:
spending a request to produce a `401` renders a subscription boundary as a fault.

**Naming PR explicitly still runs it**, so the day the subscription changes this reverses in one
command. And **PR still rates** — being disregarded means *not compared*, not *not supported*.

> **The consequence outlives the decision and must not go quiet.** PR is the one jurisdiction with
> **no external confirmation of any kind** — no entitlement, and no stored priced example either
> (OI-79). Its number comes entirely from ISO's own tables and nothing independent has ever checked
> it. Every count of live agreement is now **`n of 50`**, never `of 51`, and a PR premium has to
> carry that caveat where a reader will see it. **The easy version of this change was to delete the
> red row.** That would have made the gap invisible, which is the opposite of the point.

### Also

`?sample=OK&compare=1&rate=1` preloads, ticks the comparison and rates, so a specific view can be
linked to — and, incidentally, so browser automation stops depending on a native `<select>` that
would not take keystrokes reliably. **That should have been the first move rather than the fifth.**

### Documentation brought current

**`docs/PRD-GL-RATING-ENGINE.md`** — §0 rewritten for today and §8 *Where we stand* replaced. It now
opens on the fact that matters: **all six stages exist, and ISO's own service agrees on fifty
jurisdictions on every published field.** It states plainly what the engine cannot do, and that
**fifty matches on one risk shape is a narrower claim than it sounds.**

**`docs/BACKLOG-2026-08-14.md`** — tomorrow's work, ordered, with the open item each closes:

1. **Breadth against the live service (OI-87)** — deductibles, multi-location, size-of-risk,
   claims-made, the rating plans, the other sublines. *Expect it to find defects; that is the point.*
2. **Close the rounding question (OI-70)** — one engineered submission producing `x.5` with `x` even,
   one call, and the oldest question in the project is answered
3. ~~Puerto Rico's entitlement (OI-86)~~ — *decided the same day, see above*
4. **Our 28 referral conditions against ISO's 838 declared (OI-81, OI-82)**
5. **Dependent-domain validation, the remaining 61 (OI-84)**
6. **Form attachment, using the 508 STC submissions (OI-83)**

Phase 3 is explicitly *not* first, and the reason is recorded: **a harness that adjudicates
differences is worth building once there are differences to adjudicate.** On one risk shape there
are none.

### ▶ Next session

**Item 1 of the backlog — breadth.** Everything needed is already there:
`scripts/phase2_compare.py` takes any submission, `Schema.legal_values()` says what each field may
contain, and the interface will run and display whatever is generated.

---

## Entry 14 — Breadth: the risk varies now, and it found a defect. ~~NEXT SESSION STARTS HERE.~~ *(the live handoff is **Entry 15**)*

- **Date:** 2026-08-14
- **Directed:** *"leave it be, it's unrelated for now. Start with breadth against live service"*
- **Verified:** OK **16 of 16** buildable variants agree with ISO · NY **15 of 15** · one engine
  defect raised (**OI-88**), one filed gate found (**OI-89**), one harness defect closed (**OI-90**).

### Rule #1 first, and it paid immediately

**Enumerate the declaration before deriving anything.** Before a single variant was written, three
enumerations were run against ISO's own field and domain files: what each breadth-relevant field
legally holds, what each *combination* holds, and what turning a switch on **drags in with it**.

Two constraints came out that a plausible-looking variant would have got wrong:

* **The split and combined deductibles are mutually exclusive.** `PremOpsBIPDDeductible` is keyed on
  the BI/PD pair across **961 dependency keys**, and they say: with BI and PD both `No Deductible`
  the combined value may be any of 31; with **either** one set, the only legal combined value is
  `No Deductible`. A variant setting all three would have been rejected, **and the rejection would
  have looked like an engine defect.**
* **Terrorism drags in a place.** ISO declares `ZipCode` to apply when `TerrorismCoverage='Yes'`,
  and the base submissions carry no ZIP because they never turn terrorism on. **NY and CA declare no
  `ZipCode` domain at all** — they take an explicit `TerrorismTerritory`, which is E8/R22 arriving as
  a build-time fact rather than a note. The harness asks the declaration which of the two a
  jurisdiction uses; it does not consult a list of state codes.

### `scripts/breadth.py` — 17 variants over 7 groups

Every value comes from a domain table, a declared minimum or ISO's own default, and
**`Declared.require` refuses to build a variant whose value is not in the declared set.** That is
the point: a submission ISO would reject teaches nothing about our arithmetic, and sending one
spends a call to learn something the filing already said.

**Live calls are opt-in.** Without `--live` the harness builds, checks each variant against ISO's own
schema and rates it through our engine — enough to find a variant we cannot rate at all, at no cost.

> **A variant whose premium equals the base is a finding, not a pass.** It means the chain the
> variant exists to exercise did not move the number. The report has a column for it, and on the
> first run that column was the most informative thing on the page.

### The result

**OK: 16 of 16. NY: 15 of 15.** Premium *and* every published field, through the same
`compare_payload` phase 2 uses — split out rather than copied, because a second comparison would be
a second definition of *agreement* and the two would drift.

What now has an external answer that never did: **six deductible shapes** (BI, PD and combined, on
both the prem/ops and the products side, and both at once), **two locations** in different
territories, **two classifications** in one location, a **premium basis that is not Gross Sales**,
**both directions of the ILF table**, **claims-made at two maturities**, the **schedule rating
plan**, and **terrorism on**.

**NY is not OK with different rates.** It declares **`Occurrence` as the only legal coverage form**,
so the claims-made variants are unbuildable there and the harness says so from the declaration
rather than discovering it from a 400. Its schedule rating moves the premium where OK's does not
(OI-89). This is why the same 17 variants have to run in every jurisdiction, not one.

### The defect — OI-88

`SizeOfRiskRatingApplies='Yes'` in OK: **ISO rates it at `8816`; our engine refuses.**

The cause is exact, and it is in ISO's own rule. `LookupPremOpsSizeOfRiskRelativity` is a
`FirstNonNull` of two `Round(Lookup)` branches — the first keyed on the state, the second on a
literal `CW`. The table holds **8,330 rows, every one `CW`**, so branch one *must* miss and ISO's
design is that **branch two answers**. Our `Round` raises on the null under contract §12.3, and the
exception escapes the `FirstNonNull` before branch two is evaluated.

**§12.3 is not wrong. C6 already says an exhausted `FirstNonNull` returns null rather than raising
— the gap is that a branch cannot *become* null through arithmetic.** And the engine must not grow
a `CW` fallback of its own: **ISO files the fallback; the only bug is that we cannot reach it.**

Not fixed on sight, deliberately: `Round` is everywhere, and the narrow reading needs measuring over
the corpus before it is chosen. **Left as a decision to take, not a patch to apply.**

### The gate nothing had noticed — OI-89

Schedule rating at `10%` in OK moved the premium **not at all, and ISO agreed to the cent.** The
trace shows the plan running correctly and then writing `ScheduleRatingModificationFactor = 1.0`.
`SetScheduleRatingModificationFactor` says why: on the three prem/ops-and-products sublines the
modification applies **only when `ERPCredibilityFactor >= 0.03`** — schedule rating on prem/ops
requires experience credibility. **So the experience-rating variant is a prerequisite, not a peer.**

And the dependency is **invisible to stage 4**: the field file declares `SRPClassificationPct` as
applying whenever the switch is `Yes`, while the real precondition lives in a rule the schema never
reads. `1.0` as the no-op factor is **E20/OI-68 in a third place**.

### The harness's own defect — OI-90

ISO returned **400**: *"Element value 'YearInClaimsMade' has unexpected type of 'String' (was
expecting 'Int32')"*. `fields.py` opens with that exact warning — **`Type` is a form control, not a
data type** — written the day before from the field data and never yet tested against the service.
**Our engine rated the string version happily**, so on that field we are more permissive than ISO,
which neither side shows alone.

### ▶ Next session

**Three things, in this order.**

1. **OI-88 — decide the null-in-`FirstNonNull` semantics and fix it.** Measure first: how many
   `FirstNonNull` branches in the corpus wrap a nullable `Lookup` in arithmetic. That number decides
   whether the fix is *`Round` propagates null* or *arithmetic inside a `FirstNonNull` branch
   propagates null*. **This is a rating-semantics change affecting all 51 jurisdictions and it needs
   an explicit go.**
2. **Experience rating as a variant**, which OI-89 makes a prerequisite for exercising schedule
   rating properly, and which needs about twenty dated fields ISO declares.
3. **The other 48 entitled jurisdictions**, one run each — `python scripts/breadth.py --juris XX
   --live`. NY already proved the variants are not OK-specific and that the declaration catches
   state narrowing before a call is spent.

---

## Entry 15 — The variable tester: dropdowns, all 51 states, and a memory. ~~NEXT SESSION STARTS HERE.~~ *(the live handoff is **Entry 16**)*

- **Date:** 2026-08-14
- **Directed:** *"be able to select, from dropdowns, from things like deductibles, classifications,
  limits, etc., core things, and then run tests on all available states... Need read results for all
  tests, and some of long term visualization capabilities as well. Code for UI should live outside
  code used for the actual rating engines."*
- **Chosen, from three offered forks:** all 10 controls · engine-only default with ISO opt-in · show
  the union of legal values and flag per state.
- **Verified:** `verify_tester` **30/30** · `verify_breadth` 18/18 · `verify_stage6` 30/30 · every
  prior suite green · one 51-jurisdiction run and one ISO-compared run driven through the page.

### What it is

`python app.py` → **`/tester`**. **19 controls in 8 groups**, and every option in every dropdown is
read from **ISO's declared domain for that jurisdiction** — six deductibles, the occurrence limit,
premium basis, class code, exposure, coverage form, claims-made year, subline, locations,
size-of-risk, experience rating, schedule rating, the scheduled percentage, terrorism.

**The dropdowns are not a list somebody typed.** `Declared.require` refuses a value ISO does not
declare, before anything is sent. That is the same rule breadth already ran on, moved to where a
person can drive it.

### Three behaviours worth the build

**A keyed domain collapses when its key is answered.** Choose a PD deductible and the combined BI/PD
dropdown drops from **31 options to one** — `No Deductible` — because ISO declares them mutually
exclusive across 961 dependency keys. Driven in the browser and confirmed: `31 -> ['No Deductible']`.
Without it the page would offer thirty illegal values and the rejections would read as engine faults.

**`NOT APPLICABLE` is a third outcome, and it is grey.** Answered from the declaration **without
rating anything**: claims-made applies in **50 of 51** (NY declares `Occurrence` only), two locations
in **31 of 51** (20 jurisdictions declare a single prem/ops territory). Merging that into *disagrees*
would report twenty failures for a risk ISO never permitted.

**A run that does not move the premium is called out.** Agreement on an unchanged number proves both
engines can do nothing.

### It found something on its first real run

A 5,000 per-occurrence PD deductible across all 51, engine-only, 157 seconds: **every jurisdiction
rated, and Georgia alone did not move.** Three live calls settled it — **ISO agrees GA does not
move** (6845 both sides, against 8209/8209 in OK and 12051/12051 in NY). An ISO-confirmed no-op, not
a defect, and the tester surfaced it without being asked to look.

### The long view, and why the store is append-only

Every run appends one line to `results/runs-YYYY-MM.jsonl` with the configuration, the summary, every
jurisdiction row, the engine version and the resolved packages. Four views, drawn as **inline SVG
with no chart library** — the engine has no third-party dependency and a chart is not a good enough
reason to acquire one:

* **Coverage** — controls × jurisdictions ever exercised. **The honest answer to *how narrow is the
  claim*, and it is the one chart that is interesting when empty.** It currently reads *1 of 19*.
* **Agreement over time** · **Premium response** (premium against the varied value, every
  jurisdiction overlaid; a curve that kinks alone is a defect you can see before you can explain) ·
  **Defects** with first-seen, last-seen and run count.

**A results file that is rewritten cannot answer *when did this start disagreeing*** — which is the
question the charts exist for. Nothing updates or deletes a line.

### Where the code lives, and the test that keeps it there

    ui/  ->  scripts/variants.py, scripts/sweep.py  ->  gl_engine

* **`scripts/variants.py`** — what may be varied, what each option legally holds, how to apply it.
  No UI, no HTML. `breadth.py`, `sweep.py` and the page all read this one definition, because a
  second list of legal values would drift and the drift would look like a rating defect.
* **`scripts/sweep.py`** — one configuration across jurisdictions. **It does not define agreement**;
  it calls `phase2_compare.compare_payload`, the same function the phase 2 command line uses.
* **`ui/`** — `variables.py`, `tester.py`, `store.py`, `charts.py`. Presentation and history.
* **`app.py`** — mounts it in four lines and knows nothing about variables or premiums.

**`verify_tester` asserts the direction by parsing the imports rather than trusting a docstring —
and it immediately caught a leak I had written**: `ui/tester.py` imported `gl_engine` to stamp a
version string onto a stored run. A version string is a small thing to reach across a boundary for,
and reaching for small things is how a boundary stops meaning anything. Moved to
`sweep.engine_version()`; the assertion now passes on the code rather than on the intention.

### Also raised

**OI-91.** Building the tester forced the question *what do I send to locate this risk for terrorism*
in all 51, and it could not be answered from the record. **E8/R22 says four jurisdictions code it
explicitly and eleven derive it from a ZIP; measured as "resolves a legal value as of 2026-08-01" it
is 15, 16 and 20-with-neither.** The two readings have not been run side by side. The tester declines
to guess — `terrorism_place` returns nothing and the run reports `NOT APPLICABLE` with the reason.

### The tester's first question back — OI-92

*"Any explanation why GA's deductible didn't have a price impact?"* Traced rather than guessed, and
the answer was not in the deductible chain at all.

**ISO's own example input for Georgia omits `PremisesOperationsTerritory`** — GA is the only one of
51 — and `build_sample_payloads.py` carries the territory fields over from that input, so our base
inherited the hole. GA declares the field **rating-required with two legal values**. Without it
`SetPremOpsLossCost` never looks anything up and writes `0.0`, so **the prem/ops basic limit premium
is zero and GA's whole premium is the products side.** The deductible worked perfectly the entire
time: factor `0.044`, prem/ops ILF cut from `1.920` to `1.876`. **4.4% of nothing is nothing.**

Supply a declared territory and every step comes back: loss cost `0.054`, premium **7366**, the same
deductible taking **−15** — and **ISO agrees at every point** (6845 deficient, 7366 and 7351
corrected). **Not an engine defect; the oracle's input, the OI-77/OI-78 family again.**

> **What it costs is scope, and it cost it silently.** GA counts toward *50 of 50 agree*, and what
> GA proves is agreement on a **products-only risk**. Its prem/ops loss cost and territory factor
> have never been checked against ISO. **The tester found this on its first cross-state run, from
> the one row that did not move** — which is the entire argument for reporting an unmoved premium
> as a finding rather than a pass.

### OI-92 closed the same day, at the generator

*"Lets make sure the ISO test cases also include the territory, as this led to a false fail."*

**One correction to the framing, because it changes what to hunt for: it was a false _pass_, not a
false fail.** GA reported `MATCH` throughout — nothing was ever red. The test agreed with ISO on a
number the deductible could not move. Red rows announce themselves; this had to be found by asking
why something *didn't* change.

Fixed in `build_sample_payloads.fill_required_territories`, **not by editing the file**: a
rating-required territory ISO's own example omits is now supplied from that jurisdiction's own
declared domain, so the next example shipped with a hole is closed on generation.

> **The first version of the fix was wrong, and the measurement caught it.** Filling *every*
> rating-required territory also supplies `LiquorLiabTerritory` and `TerrorismTerritory`, and
> **Oregon's premium moved by 14** — a terrorism charge on a sample whose `TerrorismCoverage` is
> `No`. Supplying a Liquor territory to a risk with no Liquor subline is inventing input, which is
> the one thing this module exists not to do. Narrowed to the territories of the sublines these
> samples actually rate, and re-measured: **exactly two files change and exactly one premium moves.**

**GA `6845 → 7366`** — its prem/ops loss cost resolves at `0.054` — and **PR** gains a
rating-required `PremisesOperationsTerr` with no price effect. Re-verified live: **GA `MATCH` at
7366**, and the deductible that started all this now takes `−15` there as it does everywhere else.
GA's baseline of record is 7366; the cached baselines were cleared. Runs recorded before this keep
the old number, by design — the store is append-only.

**Guarded, as a property rather than as a jurisdiction.** `verify_stage4` group **G** asserts that
no sample omits a rating-required territory it could supply (51 checked), and that Georgia resolves
a prem/ops loss cost and prices both sides.

### ▶ Next session

1. **OI-88 — the null-in-`FirstNonNull` decision**, unchanged and still first. Measure how many
   `FirstNonNull` branches wrap a nullable `Lookup` in arithmetic, then fix. **It changes rating
   semantics for all 51 and needs an explicit go.** The tester makes it a one-click reproduction:
   set `Size-of-risk = Yes`, run all states.
2. **Fill the coverage grid.** It reads *1 of 19*. Each control run at two or three values across
   all 51, engine-only, is about ninety seconds a configuration — and the response curves need at
   least two values per control before they draw anything.
3. **OI-89's prerequisite** — experience rating needs about twenty dated fields before schedule
   rating can be exercised on prem/ops.
4. **The seven sublines that need their own base submission** — Liquor, OCP, Pollution, Product
   Withdrawal, Railroad, UST, EDL. The tester offers them and says plainly that this base cannot
   express them, which is the honest version of *1 of 10 sublines tested*.

---

## Entry 16 — Answering for it: a walkthrough, two carrier questions, and an agent that reads the code. ~~NEXT SESSION STARTS HERE.~~ *(the live handoff is **Entry 17**)*

- **Date:** 2026-08-14
- **Directed:** a launcher for the UI · a plain-English case for the interpreter · a walkthrough
  script to record · *"has a carrier adopted every ERC version?"* · *"create an agent that is an
  expert in the code"*
- **Built:** no engine code. Two launchers, four documents, one agent definition, three backlog
  items and one defects section.
- **Verified:** `start.bat` smoke-tested on a spare port (HTTP 200, 17,442 bytes) · warm and cold
  rating latency measured for the first time · the agent tested on a real question and its two
  load-bearing claims independently re-checked.

### The session's subject was explaining the build, not extending it

Nothing here changes a premium. That is the point of the entry: **the build reached the stage where
what it needs is to be answerable**, and answering it surfaced two design questions that had never
been asked, plus one measurement nobody had taken.

### 1. Performance, measured — and a number in the docs was wrong

Nothing had ever timed a rating. **Warm: ~1.2 seconds** (0.97, 1.32, 1.15, 1.42, 1.58s across five
runs). **Cold, one jurisdiction: ~2 seconds.** It does *not* speed up when warm, so **interpretation
is the cost, not file I/O** — the tables are already cached per `Layer` after first read.

**A figure quoted in conversation earlier the same day — "95 second cold start" — was wrong.** That
is `cli check --deep` scanning all 567 packages; a single rating loads only what it resolves.
Corrected wherever it had been repeated.

### 2. Two carrier questions, both answered into the backlog

Asked in conversation, and neither had a written answer anywhere:

**How deviations get authored** — §6 of the executive summary had left this explicitly open. Closed:
a **friendlier format that compiles** to ISO's shape, and **stored per jurisdiction, always**,
because a carrier files a national deviation state by state and the build should mirror the filing.
*"Applies to all jurisdictions"* is an authoring affordance that fans out to 51, never a distinct
kind of object. **This may dissolve C1's precedence question** — if a national deviation *is* 51
state filings, there is no national layer for a state exception to be weighed against and the
four-deep chain flattens to three. Recorded to confirm when Phase 4 opens rather than decided.

**Whether a carrier can be pinned to an older ERC edition** — backlog item 8, and the answer is
*yes, and most of it already exists*. Editions are all retained, `editions()` already returns
non-current ones, and **the countrywide parent already follows the state package's own declaration
rather than the newest (N5)** — which is precisely the rule that makes pinning safe rather than
plausible-and-wrong. What is missing is one input: `(carrier, jurisdiction, as-of)` instead of
`(jurisdiction, as-of)`. **Built for backdating, and it turns out to be the same machinery.**

### 3. The three known defects moved above the numbered backlog

`OI-88`, `OI-91` **HIGH**; `OI-89` **MEDIUM**. The distinction the section makes: these are **known
wrong**, where everything numbered is **not yet known**. Items 1–8 keep their numbers, because
`EXECUTIVE-SUMMARY.md:333` points at item 7 and renumbering would have broken it silently.

### 4. `gl-engine-code-expert` — an agent whose evidence is the source

`.claude/agents/gl-engine-code-expert.md`. Answers from the Python only: **markdown and docs are
explicitly not evidence**, docstrings are, and where code and document disagree **the code wins and
the conflict is reported**. Two registers by default — plain English, then the mechanism with
`file:line` on every behavioural claim.

**The definition spends its length on one trap.** The engine contains no rating concepts. Grep
`deductible` across it and you get **one hit, in `referrals.py`, and it is a referral message**. An
agent that greps, finds that, and concludes the engine barely handles deductibles is **wrong in a
way that sounds researched**. So rating questions are answered in two halves: the mechanism, which
is entirely in the code, and the boundary, where the values live in ISO's corpus.

**Tested on *"how is a GL deductible used in Georgia?"*** It found that **Georgia files no
deductible factors of its own** — all fourteen `Ded*` tables are owned by countrywide and every row
is `CW` — rated six variants to show the effect, and proved the state→countrywide retry is **ISO's
filed rule and not ours** by grepping `'CW'` across `gl_engine/interp/` and getting **zero matches**.
Both load-bearing claims were independently re-verified before the answer was accepted.

**It also found what its own inputs had done to it:** two early runs returned 6,845 because
`Engine_Payloads/GA/submission.json` was rewritten underneath it mid-session. It reported the
contamination rather than averaging it away.

**And it corroborated D1 from a second direction.** Georgia reaching countrywide for *every*
deductible factor is exactly the path OI-88 breaks. The defect is in the mechanism the layering
depends on.

### 5. Concurrent writes to this working tree

Three incidents in one session: the GA payload rewritten at 15:35:50, two files vanishing from
`Loom-Share/` between commands, and `README.md` gaining edits mid-session. All explained by a second
session working in the same tree. **Recorded because it corrupted an agent's measurements once
already**, and because anything staged blindly while it happens can pick up half-finished work. The
tester work was committed only after `verify_tester` 30/30 and `verify_stage4` 30/30 were re-run.

### What was written

| | |
|---|---|
| `start.bat` · `start.command` | Windows and macOS launchers. Python 3 only; `app.py` is standard library |
| `docs/WHY-AN-INTERPRETER.md` | The interpreter case in under 200 words, in the user's own voice |
| `docs/LOOM-WALKTHROUGH-SCRIPT.md` · `.html` | The recording script. The HTML separates what you do on screen from what you say |
| `Loom-Share/` | Twelve files numbered in reading order, for an audience. ISO's corpus deliberately not included — licensed |
| `README.md` §Running the app | Both platforms, the port and `--no-browser` flags, `GL_ERC_ROOT` |
| `.claude/agents/gl-engine-code-expert.md` | The agent |

### ▶ Next session

**Unchanged from Entry 15, and now corroborated twice.**

1. **OI-88 / D1 — the null-in-`FirstNonNull` decision.** Still first. **It changes rating semantics
   for all 51 and needs an explicit go.** One-click reproduction in the tester: size-of-risk = Yes,
   run all states.
2. **OI-91 / D2** — run the two terrorism-location measurements side by side over the same packages
   and dates. Terrorism breadth is blocked in 20 jurisdictions until it is settled.
3. **Fill the coverage grid** — it still reads *1 of 19*.
4. **OI-89 / D3** — experience rating needs about twenty dated fields before schedule rating can be
   exercised on prem/ops.

---

## Entry 17 — Twenty notebooks, an agent that crosses the walls, and Property opened as exploration. ~~NEXT SESSION STARTS HERE.~~ *(the live handoff is **Entry 18**)*

- **Date:** work done 2026-08-14, **logged 2026-08-17**
- **Directed:** *"create an agent that spans the content, the manuals and the code"* · notebooks
  explaining the engine one file at a time · then, on 2026-08-17: *"Property will be a next
  direction, but I don't want to build anything there until more exploration"*
- **Built:** no engine code, for the second entry running. One agent definition, twenty notebooks,
  one test, one entry-point document.
- **Verified:** `tests/verify_notebooks.py` executes **every code cell of all twenty notebooks** and
  fails on any exception. It caught **eight errors** on its first run.

### Why this entry is late

**Two commits landed on 2026-08-14 and were never logged** — `a0782bd` (the `gl-authority` agent)
and `07e1519` (the notebooks). Entry 16 was written before them and kept the *NEXT SESSION STARTS
HERE* marker for three days while two substantial pieces of work sat below it unrecorded. Recorded
now rather than folded silently into a later entry, because **the handoff marker pointing at work
that has already been superseded is exactly the failure this log exists to prevent.**

### 1. `gl-authority` — one agent across all three sources

`.claude/agents/gl-authority.md`, 198 lines. Three specialists already existed and **each is walled
off on purpose** — ERC content, ISO's manuals, our Python. **Real questions do not respect the
walls.** *"Is a deductible used in Georgia"*, *"which form attaches here"*, *"why is this premium
what it is"* touch two or three at once, and asking a single specialist gets **a third of an answer
delivered confidently** — which is worse than no answer.

**The design constraint came from the existing definitions, not from convenience.** `iso-erc-expert`
is forbidden from reading `iso-circular-expert` — *"a parallel product built from a different
source; consulting it destroys the independence of this one."* **That independence is what makes
agreement between the two corpora evidence at all**, and an agent holding both in one head can
destroy it by accident. So the definition spends a section on preserving it: never reason from one
source into the other, **measure ERC first and check the manual second** rather than the reverse,
and **report disagreement rather than tidying it**.

Otherwise it is the project's standing evidence criteria made operational — **tier 1 ERC supplies,
tier 2 manuals confirm and may never source, tier 3 is a person, and the code is none of them: it is
the thing being checked.** Every claim names its source, as an ERC path, a notice and page, or
`file.py:line`.

**It does not delegate.** Nesting risks a specialist's refusal being flattened into a summary, and
**"unverifiable" surviving intact matters more here than convenience.**

`Agentic/` folders were added for both new agents, matching how the two ISO experts are laid out.
**Neither carries a `knowledge/` directory, deliberately** — the ISO experts pre-compute JSON
because their corpora are large, external and slow to measure, whereas **pre-computing facts about
code that changes every session is how a knowledge file starts lying.**

### 2. Twenty notebooks — the engine explained one file at a time

`notebooks/`, one per Python file in `gl_engine/`, plus an index. **They import the engine and run
it; nothing imports them**, and nothing there is needed to rate a submission.

**Same six cells every time, so the twentieth reads like the first:** what the file is for, its
public surface *(generated from the module, so it cannot drift)*, the smallest thing that works, the
interesting case, what it refuses, and try it yourself. **The refusals cell is not filler** — this
engine stops rather than guessing in a great many places, and **the exception text is usually the
clearest statement of a module's contract available.**

Read in dependency order: where the content lives, how failures work, the typed cell, discovery and
resolution, tables, then the interpreter's value model, tree, program, 54 instructions and machine,
then schema, submission, kernel, referrals, assertions and the CLI.

### 3. The notebook test, and what it caught immediately

`tests/verify_notebooks.py` executes every code cell of every notebook and fails on any exception —
so **a notebook that stops matching the code becomes a red suite rather than quietly wrong
documentation.**

**It does not compare outputs**, and that is a decision rather than an omission: pinning the prose
to one corpus edition would turn the suite red **every time ISO files anything.**

**It earned its keep on the first run, catching eight errors that read as plausible prose and did
not run:** `Package.dir` is a method, `key_cols` holds `Column` objects, `"date"` is not one of
ISO's four declared types, `Node.root` is a property, `Value` reads via `@FromDataDef`,
`gl_engine.schema.validate` resolves to the *function* because the package re-exports it under the
module's name, `Report.add` builds its own `Check`, and **the index misreported how many notebooks
run without a corpus — six, not four**, measured by pointing `GL_ERC_ROOT` at nothing.

**Outputs are stripped before commit and `.gitattributes` enforces it with `nbstripout`.** A
notebook that has run holds **ISO's licensed values inside its JSON**, and this repository
deliberately excludes ISO content. One stray error output was caught and cleared during the commit
itself, which is why the filter is **configured rather than left to discipline.**

### 4. Notebook churn found in the tree and reverted

Twelve notebooks were modified in the working tree with **no content change** — cell `id` fields
added and key order rewritten by an nbformat writer that had opened them. **Reverted, not
committed.** Worth a line because it is the third recorded instance of this tree changing underneath
a session *(Entry 16 §5)*, and because a diffstat reading `566 insertions` is easy to stage blindly.

### 5. Property opened — as exploration, explicitly not as a build

`CF_Algorithm/CauseOfLoss_Building_RatingAlgorithms.md`, 1,120 lines, written 2026-08-13 from
`CFCW20260601V01` — **Commercial Property, countrywide, edition 06-01-2026.** It documents building
rating across **all four cause-of-loss forms** (Basic Group I, Basic Group II, Broad, Special) as
they run from `SetBlanketRatesAndFactors`: the rate build-up step by step, the premium branches
*(scheduled, Legal Liability, blanket)*, and an end-to-end quick reference per form.

**It had been sitting untracked and unmentioned in either log for four days.** Recorded now.

**The direction is confirmed and the scope is not.** Property is a next direction. **Nothing is to
be built there until exploration is further along** — no engine code, no schema work, no package
resolution against CF. What exists is a reading of one countrywide package, and **the GL build's own
history is the argument for waiting**: fifty-one process-log steps of analysis preceded stage 1, and
the two findings that most changed the engine *(E20/OI-68's `1.00` sentinel, OI-69's split loss
costs)* came from **running** the content, not reading it. **A Property build started off one
document would be starting where GL started, minus the fifty-one steps.**

### What was written

| | |
|---|---|
| `.claude/agents/gl-authority.md` | The cross-source agent. `Agentic/gl-authority/` carries a copy and a README; `.claude/agents/` stays the live definition |
| `Agentic/gl-engine-code-expert/` | The same two files for Entry 16's agent, which had shipped without them |
| `notebooks/00-index.ipynb` … `19-cli.ipynb` | Twenty notebooks, one per engine file, plus the index |
| `notebooks/START-HERE.md` | The one-page entry point: how to open them, which three to read when short on time, and why the cells are blank until you run them |
| `tests/verify_notebooks.py` | Executes every cell of every notebook; no output comparison, by design |
| `start-notebooks.bat` · `.command` | Windows and macOS launchers for Jupyter |
| `CF_Algorithm/…md` | Commercial Property building rating, all four cause-of-loss forms. **Exploration — nothing builds on it yet** |

### ▶ Next session

**Items 1–4 are unchanged from Entry 16 and are now three entries old.** Two consecutive entries
have been about explaining the build rather than extending it; **the defects have not moved.**

1. **OI-88 / D1 — the null-in-`FirstNonNull` decision.** Still first, still **needs an explicit go**,
   because it changes rating semantics for all 51. **The measuring pass does not need the go** —
   the blast radius of `Round(null) → null` can be counted over the corpus before anything is
   decided, and that count is what the decision is currently missing.
2. **OI-91 / D2** — run the two terrorism-location measurements side by side over the same packages
   and dates. Terrorism breadth is blocked in 20 jurisdictions until it is settled.
3. **Fill the coverage grid** — it still reads *1 of 19*.
4. **OI-89 / D3** — experience rating needs about twenty dated fields before schedule rating can be
   exercised on prem/ops.
5. **Property exploration, at reading pace and no further.** The next honest step is **breadth of
   reading, not code**: what a CF *state* package changes against the countrywide one already
   documented, and whether the four-form structure survives contact with a second jurisdiction.
   **No build until that is answered.**

---

## Entry 18 — OI-88 measured, then closed. Size-of-risk goes from 2 jurisdictions to 51. ~~NEXT SESSION STARTS HERE.~~ *(the live handoff is **Entry 19**)*

- **Date:** 2026-08-17
- **Directed:** *"explain OI-88 decision to me"* → *"run the measuring pass"* → **the go**
- **Built:** one analysis script, one new error type, one trace method, ~15 lines of interpreter
  change, four tests.
- **Verified:** **51 of 51 jurisdictions rate**, up from 2. **OK = 8816 offline and `MATCH` against
  ISO live on the premium and every published field.** interp 61/61 · breadth 19/19 · golden 80/80 ·
  stage1 20/20 · stage3 38/38 · stage4 30/30 · stage5 18/18 · stage6 30/30 · phase2 11/11 ·
  notebooks 20/20 · tester 30/30 · CA 11/11 · NY 10/10 · oi50 7/7.

### The measurement changed the fix, which is the whole point of taking it first

**OI-88 had been first on the list for three entries and had never been touched**, because the
backlog said it changes rating semantics for all 51 and needs an explicit go. What it was actually
missing was **a number**. The measuring pass is read-only and never needed the go; nobody had run
it.

### 1. What the corpus said

`scripts/erc/45_oi88_blast_radius.py`. Three questions, asked of all **570 packages**:

| | |
|---|---|
| `FirstNonNull` sites in the corpus | **38,378** |
| ...with refusing arithmetic inside a branch *(upper bound)* | **276** — 0.72%, in 72 packages |
| ...narrowed to arithmetic over a **plausibly-null** operand | **69** — 0.18%, in 29 packages |
| of those 69, **carrying a trailing `Constant`** | **51 — 73.9%** |

By node, in the at-risk branches: **`Round` 60, `Product` 23, `Divide` 20, `Subtract` 19,
`GreaterThan` 3.**

**The first two rows argued for the fix and the third argued against the obvious version of it.**
Under 1% of sites is surgical, not sweeping — that killed the reason for hesitating. But **three
at-risk sites in four have a constant standing by to answer**, so a blunt `Round(null) → null` would
have turned a genuinely missing value into a plausible premium **with nothing recorded**. The blast
radius is not wide, it is **deep** — concentrated exactly where a swallowed defect is invisible.

### 2. And what the engine said

`sweep.py --set size_of_risk=Yes`, engine-only, 29 seconds: **49 of 51 refused.** The two that rated,
**CA and NY, came back *unchanged from base***, because their state rule sets override countrywide
wholesale (N3).

**So it was not 49 broken and 2 working. Size-of-risk was exercised correctly in zero of 51.**

### 3. The fix, and the condition attached to it

`NullInArithmetic`, an `InterpretError` subclass raised **only** for the null case in `to_decimal`.
`FirstNonNull` catches **only that type**, per branch, and treats it as a null argument.

**Every other refusal still escapes** — a `Multi` in a scalar position, a non-numeric string, a
missing table. A bare `except InterpretError` around the branch would have been three characters
shorter and would have **gutted the property the whole engine is built on.**

**The 51 masking sites made tracing a condition of the fix rather than a nicety.**
`Interpreter.trace_branch_abandoned` mirrors `trace_exhausted`, which already does exactly this for
C6 exhaustion — **there was already a facility for "this `FirstNonNull` produced nothing, and it is
recorded."** Rating OK with size-of-risk on emits **two** such entries, both `argument 0`: the state
branch missing, exactly as ISO designed it to.

### 4. The test that was built to fail

`verify_breadth` E4 read *"OI-88 is still open: size-of-risk refuses in OK"*, with the detail
*"ISO rates it at 8816 — **when this FAILS, OI-88 is fixed and the assertion becomes a
comparison**."* It failed on the first run after the fix, exactly as written, and is now that
comparison: **E4b, ours=8816 ISO=8816.**

**Pinning a known defect as a passing assertion, with its own closure instructions in the failure
message, is worth repeating.** It cost nothing while the defect was open, made silent regression
impossible, and told the person who closed it what to do next.

`verify_interp` gains **B6a** (the branch is abandoned), **B6b** (the abandonment is traced) and
**B6c** — the load-bearing negative: **a branch that fails for any other reason must still refuse.**
If B6c ever passes by absorbing the refusal, the fix has become the defect it was meant to close.

### 5. What closing it made visible

**CA and NY still rate unchanged from base.** The refusal had been hiding that. Their state rule
sets override countrywide wholesale, so *"does size-of-risk apply"* is a per-jurisdiction question —
**the same shape as OI-89**, and it belongs to D3 now rather than here.

**A stale census, found in passing.** `nodes.py`'s `FirstNonNull` docstring quoted **36,605 sites and
4,004 exhaustible across 327 packages**; the corpus now reads **38,378 and 4,327 over 570 packages,
not the 567 quoted throughout the docs.** Three packages have arrived since. The docstring is
corrected; **the wider `567` is not chased**, and `verify_contract_figures` passes against cached
output in `scripts/erc/out/`, so it would not have caught this.

### What was written

| | |
|---|---|
| `scripts/erc/45_oi88_blast_radius.py` | The measuring pass. Read-only, decides nothing, emits to gitignored `out/` |
| `gl_engine/interp/values.py` | `NullInArithmetic`; `to_decimal` raises it for the null case |
| `gl_engine/interp/nodes.py` | `FirstNonNull` catches only that type, per branch; docstring census corrected |
| `gl_engine/interp/interpreter.py` | `trace_branch_abandoned` |
| `tests/verify_interp.py` | B6a, B6b, B6c |
| `tests/verify_breadth.py` | E4 becomes the comparison it predicted; E4b checks ISO's number |
| `docs/OPEN-ITEMS.md` · `docs/BACKLOG-2026-08-14.md` | OI-88 and D1 closed with the evidence |

### ▶ Next session

**The defect list is down to two.** D1 is closed; D2 and D3 are unchanged.

1. **OI-91 / D2** `HIGH` — run the two terrorism-location measurements side by side over the same
   packages and dates. **Terrorism breadth is still blocked in 20 jurisdictions.** Now the top item.
2. **OI-89 / D3** `MEDIUM` — experience rating needs about twenty dated fields before schedule
   rating can be exercised on prem/ops. **Closing OI-88 sharpened this**: CA and NY rating unchanged
   is the same per-jurisdiction question in a second place.
3. **Fill the coverage grid** — it still reads *1 of 19*.
4. **Re-run breadth in OK and NY against ISO live.** Size-of-risk now rates in 51 jurisdictions and
   **only OK has been compared live**. The 31-of-31 figure predates the fix.
5. **Property exploration, at reading pace and no further.** Unchanged from Entry 17: what a CF
   *state* package changes against the countrywide one, and whether the four-form structure survives
   a second jurisdiction. **No build until that is answered.**
6. **Optional, cheap:** chase `567 → 570` through the docs, and make `verify_contract_figures`
   re-measure rather than read cached output — it passed against stale numbers this session.

---

## Entry 19 — OI-91 closed: the two counts never disagreed, and the blocking was ours. ~~NEXT SESSION STARTS HERE.~~ *(the live handoff is **Entry 20**)*

- **Date:** 2026-08-17 *(same session as Entry 18)*
- **Directed:** *"save this backlog, and then let's start with B"* → **the go**
- **Built:** one analysis script, one deleted fallback, two docstrings that were wrong, two tests.
- **Verified:** **terrorism rates in 51 of 51**, up from 31. **AK 7415 · VT 7400 · WY 8501 · MT 7908
  — all `MATCH` against ISO live** on the premium and every published field, and all four had been
  refused outright that morning. Every suite green: interp 61/61 · breadth 20/20 · tester 30/30 ·
  golden 80/80 · stage1 20/20 · stage3 38/38 · stage4 30/30 · stage5 18/18 · stage6 30/30 ·
  phase2 11/11 · CA 11/11 · NY 10/10 · oi50 7/7 · notebooks 20/20.

### Two defects closed in one day, and both by measuring rather than deciding

**Entry 18's lesson repeated immediately.** OI-88 sat untouched for three entries waiting for a
decision it did not need; OI-91 had sat since 2026-08-14 described as *"they do not obviously
reconcile"*. **Run side by side, they reconcile exactly.**

### 1. `4 + 11 = 15`

`scripts/erc/52_oi91_terrorism_place.py`. One edition per jurisdiction, as-of `20260801` for **both**
measurements, so a difference between them could not be a difference of edition.

| M1 (which domain table the field names) | M2 (does a legal value resolve) | Count |
|---|---|---|
| `TerrorismTerritoryCode` | resolves | **4** — CA, FL, NY, TX |
| `TerritoryCodeByZipCode` | resolves | **11** — CO, CT, IL, MA, MD, MI, NJ, OR, PA, VA, WA |
| neither | ZIP present | 16 |
| neither | neither | 20 |

**The four and the eleven are not two camps plus a remainder. They are one population of fifteen,
and M2's fifteen is the same fifteen** — jurisdiction for jurisdiction, no off-diagonal at all in
those rows. **All fifteen declare the same field**, `GeneralLiabilityLocation.TerrorismTerritory`;
the split is only which domain table supplies its legal values.

**Nobody had lined them up, so a subdivision read as a contradiction for three days.**

### 2. And then the part that mattered more

Reconciling the counts said the numbers agreed. **Two further checks said what a caller should
actually send**, and this is where the real finding was:

**Countrywide references `TerrorismTerritory` in zero of its rule files.** Terrorism territory is a
**state-level concept only**. The 36 jurisdictions that file none are not missing an input — *there
is no input to miss.*

**The `ZipCode` fallback was inert.** `Declared.terrorism_place` fell back to any ZIP in the
location; AL, OK, GA, IA, MO and TN rate terrorism **identically** with it and without it. It was
the general premises/operations ZIP, never a terrorism input.

**So the 16/20 split described our own code, not ISO's content** — and the refusal built on it was
refusing for no reason.

### 3. Terrorism was blocked in zero jurisdictions, not twenty

The backlog had said *"terrorism breadth is blocked in 20 jurisdictions"* since 2026-08-14, and the
harness reported `NOT APPLICABLE` there **with a reason attached, which is why it looked correct.**

Rating proves otherwise: **AK, VT, WY and MT rate terrorism with no location field at all, and the
premium moves** — 7386→7415, 7371→7400, 8467→8501, 7892→7908. **ISO agrees with all four to the
cent.**

**A refusal with a well-written reason is still a refusal, and this one had been believed because it
explained itself.**

### 4. A citation that pointed at the wrong measurement

`validate.PLACE_CODED` cited `scripts/erc/47_input_schema.py` S7 as its source. **S7 does not
produce four and eleven.** It is a substring search for County/Place/Town/Borough/Parish in column
names, and its own three hits are `PremiumPlaceHolder` — **matching on "Place".**

**The four are right; the source was not.** M1 is re-measured from `DomainTableName` directly, and
the constant now cites the measurement that produces it.

### 5. What it raised — OI-93

**NY rates terrorism unchanged from base, 12141, and ISO agrees to the cent.** Not a rating defect.
**NY territory `001` genuinely carries no terrorism charge**, while `002`–`006` all charge 110.
Compare **CA, where `001` is the most expensive of the eleven** (+379).

`Declared.values()[0]` returns the lowest-numbered code, so **on NY the terrorism variant exercises
nothing while reporting as rated.** The sweep's *"premium unchanged from base"* line catches it per
run; **no test does.**

**Deliberately not fixed by choosing a value that moves the premium** — that is picking a value to
make a test pass. Raised instead. **Same kind as E20/OI-68: a legal value that does nothing looks
exactly like a working one.**

### What was written

| | |
|---|---|
| `scripts/erc/52_oi91_terrorism_place.py` | Both measurements side by side, plus the two checks that decided what to send |
| `scripts/variants.py` · `scripts/breadth.py` | `terrorism_place` returns the field for 15 and `None` for 36; `None` means send nothing, not refuse. ZIP fallback deleted |
| `gl_engine/schema/validate.py` | `PLACE_CODED`'s citation corrected, and what it actually means stated |
| `tests/verify_breadth.py` | C2 rewritten to the corrected truth; **C2b** rates terrorism with no place in four jurisdictions and requires the premium to move |
| `docs/OPEN-ITEMS.md` · both backlogs | OI-91 closed with its evidence; **OI-93** raised |
| `docs/BACKLOG-FEATURE-SETS.md` | The backlog regrouped into seven sets — the standing format from here |

### ▶ Next session

**One defect left, and set A is now the largest block of unverified work in the project.**

1. **Re-run breadth in OK and NY against ISO live — and widen it.** **This is now the top item, and
   it is no longer tidying.** Size-of-risk rates in 51 jurisdictions where it rated in 2; terrorism
   rates in 51 where it rated in 31. **Only OK and five terrorism jurisdictions have been checked
   live.** The 31-of-31 figure predates both closures.
2. **OI-93** — the variant generator's `values()[0]` no-op. Cheap, and it undermines every breadth
   figure until it is settled: *rated* and *exercised* are not the same claim.
3. **OI-89 / D3** `MEDIUM` — the last known defect. Needs ~20 dated experience-rating fields.
   **Three jurisdictions now show the same per-jurisdiction override** (CA/NY size-of-risk, NY
   terrorism), which is more evidence than it had.
4. **Fill the coverage grid** — still *1 of 19*, and two coverages moved today.
5. **Property exploration, reading pace only.** Unchanged from Entry 17.
6. **Cheap:** the rounding experiment (one live call, oldest open question); `567 → 570` through the
   docs; `verify_contract_figures` re-measuring instead of reading cached output.

---

## Entry 20 — OI-70 closed. The oldest question in the project, settled in four calls. ~~NEXT SESSION STARTS HERE.~~ *(the live handoff is **Entry 21**)*

- **Date:** 2026-08-17 *(third closure of the same session)*
- **Directed:** *"let's do OI-70. I believe 5 rounds up. It's possible it truncates to four digits
  and then rounds"* — **a belief and a competing hypothesis, both testable**
- **Built:** no engine change. The default was already right. Three tests.
- **Verified:** **four engineered ties, four live calls, four agreements.** `verify_phase2` 14/14.

### The belief was right, and the hypothesis was worth raising

**Both halves of the instruction were load-bearing.** *"5 rounds up"* named the answer, and *"possible
it truncates to four digits then rounds"* named a **third behaviour that would have looked like
half-even if it had been true.** Testing only the binary would have produced a defensible wrong
answer.

### 1. The engineered tie was one line of arithmetic, not the med-pay chain

The backlog had proposed solving the medical-payments charge — `loss cost × 0.003 × exposure ÷ 1000`
— for an exposure landing the product on `2.5`. **Not needed.**

**`exposure / 1000` is itself rounded at 0dp.** So the tie is available directly, and the only
constraint is that the integer part be **even** — half-up gives `x+1`, half-even gives `x`, and they
agree whenever `x` is odd.

Derived exactly rather than by search: every 0dp site's value was taken as an exact `Fraction` of
exposure across two ratings, which gives `1443·E / 10⁶` for the premium-driving product. **`E =
1,500,000` puts it on `2164.5`.**

**The first attempt failed instructively.** `E = 2,500` also ties — `2.5` at the same site, five
times — and **half-up and half-even still give the same premium**, because that tie does not reach
the total. *A tie that fires is not a tie that separates*, and the test had to be the premium rather
than the trace.

### 2. Four ties, four calls

| Exposure | Half-up | Half-even | **ISO** |
|---|---|---|---|
| 1,500,000 | **2469** | 2467 | **2469** |
| 2,500,000 | **4116** | 4115 | **4116** |
| 3,500,000 | **5761** | 5760 | **5761** |
| 5,500,000 | **9054** | 9052 | **9054** |

**Four of four. ISO rounds half-up.** The engine's `ROUND_HALF_UP` default has been correct since
stage 2 and is now **evidenced rather than assumed** — which was the entire content of OI-70's open
half.

### 3. The truncation hypothesis, tested rather than argued

*"Truncate to four digits, then round."* **It changes 0 of 432 rounding operations** across five
jurisdictions and three configurations — **including the 30 whose input carries more than four
decimals.**

**And there is a structural reason, which matters more than the count.** The threshold for rounding
at `n` decimal places is a `5` at position `n+1`. For `n ≤ 3` that threshold is **exactly
representable at 4dp**, so truncating to four digits *cannot* move a value across it. **Every
rounding operation in these ratings is at 0dp or 3dp** — 306 and 126 respectively.

Where it could bite:

- **At 4dp**, truncate-then-round *is* plain truncation — **already ruled out 2026-08-13**, where
  `ROUND_DOWN` changes the premium in 38 of 51 jurisdictions and Arkansas supplies a genuine
  `1.5000` tie that ISO rates at `7,872` rather than `7,871`.
- **At 8dp**, it would matter, and **no rating in hand exercises an 8dp site.** 33 `Divide` nodes
  corpus-wide. Recorded as the one untested corner rather than swept in with the rest.

### 4. The tests, and why C4 exists

`verify_phase2` C3 stays — the stored population still cannot separate the two modes, which was never
the defect and is exactly why an *engineered* submission was needed rather than a wider sweep.

**C4 asserts the two modes DO separate at the engineered ties, and it exists so that C5 cannot pass
vacuously.** Without it, a future change that made the modes agree everywhere would leave C5 green
while proving nothing. C6 pins the truncation result.

### What was written

| | |
|---|---|
| `tests/verify_phase2.py` | C4 the ties separate · C5 ISO rounds half-up on all four · C6 four-digit truncation changes nothing |
| `docs/OPEN-ITEMS.md` | OI-70 `PARTLY CLOSED` → **`CLOSED`**, with both hypotheses and the 8dp corner recorded |
| both backlogs | Item 2, and set A's rounding row |

### ▶ Next session

**Three items closed in one session — OI-88, OI-91, OI-70 — and not one of them needed a decision.
All three needed a measurement.** That is the pattern worth naming.

1. **Re-run and widen breadth against ISO live. Still the top item, and now more so.** Size-of-risk
   rates in 51 jurisdictions where it rated in 2; terrorism in 51 where it rated in 31. **Only OK and
   five terrorism jurisdictions have been checked live.** The 31-of-31 figure predates all of it.
2. **OI-93** — the variant generator's `values()[0]` no-op. Cheap, and until it is settled *rated* and
   *exercised* are different claims that read identically in every report.
3. **OI-89 / D3** — the last known defect. Needs ~20 dated experience-rating fields.
4. **Fill the coverage grid** — still *1 of 19*, and three coverages moved today.
5. **Property exploration, reading pace only.** Unchanged since Entry 17.
6. **Cheap:** `567 → 570` through the docs; `verify_contract_figures` re-measuring rather than
   reading cached output. **An 8dp rounding site would close OI-70's last corner** if one turns up.

---

## Entry 21 — OI-93 closed, and breadth re-run: 32 of 32 against ISO. ~~NEXT SESSION STARTS HERE.~~ *(the live handoff is **Entry 22**)*

- **Date:** 2026-08-17 *(fourth closure of the same session)*
- **Directed:** *"do as you suggest"* — OI-93 first, then the breadth re-run, in that order and for
  that reason
- **Built:** `Declared.pick`, `probe_no_op`, the sweep's verdict line, three tests.
- **Verified:** **32 of 32 comparable variants agree with ISO across OK and NY** · **41 live calls**,
  all `MATCH` on the premium and every published field · tester 33/33, and every other suite green.

### Why OI-93 came first, and it was the right order

**A breadth run would have reported 51 rated where several exercised nothing.** *Rated* and
*exercised* are different claims that read identically in every report, and the run was about to
produce the largest set of those claims the project has made.

### 1. `Declared.pick` — the choice is recorded, and it is pinnable

Four bare `[0]` picks — premium basis, prods basis, the aggregate limits, the terrorism territory —
now go through one place that **records that a choice was made** and takes a **pin** so a caller can
ask what a different legal value would have done.

**The first value is not a neutral default.** NY's `TerrorismTerritory` `001` carries no terrorism
charge; `002`–`006` each charge 110. In CA, `001` is the *most* expensive of eleven.

### 2. `probe_no_op` — three verdicts, and the middle one is the point

| | |
|---|---|
| **`INERT CONTROL`** | no declared value moves the premium. **A fact about ISO's filing**, and a real finding |
| **`INERT VALUE`** | this value does nothing; another would have moved it. **A fact about our harness**, and it silently weakens every breadth figure it appears in |
| **`MOVED`** | it moved after all |

**Nothing distinguished the first two before today.** The sweep now runs the probe on every unmoved
row, so the diagnosis arrives *with* the finding:

> `INERT VALUE -- NY: TerrorismTerritory=001 does nothing; 002 gives 12251 (of 19 alternatives)`

**It costs nothing on the ISO-side answers** — those configurations record no choice sites at all, so
`INERT CONTROL` is reached having rated exactly once.

`verify_tester` D4/D5/D6. **D6 matters as much as the other two:** a variant that *does* move must
not be reported as either.

### 3. Breadth re-run — 32 of 32

| | Result |
|---|---|
| **OK** | **17 of 17 MATCH**, including `size-of-risk` at **8816** — which *refused outright* this morning |
| **NY** | **15 of 15 MATCH**; the two claims-made variants are `NOT BUILT` because NY declares `Occurrence` as its only coverage form, which is the third outcome and not a disagreement |

**The previous figure was 31 of 31 and it predated three closures.** The population now includes
size-of-risk, which could not rate anywhere, and terrorism, which was refused in 20 jurisdictions.

### 4. Widening it, and a measurement that advances OI-89

Five configurations swept across all 51 offline, which costs nothing and finds refusals:

| Configuration | Rated |
|---|---|
| prem/ops PD deductible 5,000 | **51 of 51** |
| occurrence limit 500,000 CSL | **51 of 51** |
| two locations | **31 of 51** — the other 20 declare one prem/ops territory |
| claims-made | **50 of 51** — NY declares `Occurrence` only |
| schedule rating | **51 of 51** |

**And the last one produced the session's best new fact.** `schedule_rating=Yes` **with**
`schedule_pct=10%` moves the premium in exactly **three jurisdictions — FL, NY and RI — and in 48 of
51 it does not.** Verified live: **FL 9542, NY 13357, RI 8807, all `MATCH`**, with OK confirming the
no-op at 8229.

**OI-89 had this as a New York curiosity. It is three jurisdictions filing a state rule set that
overrides countrywide wholesale (N3), against 48 holding the countrywide credibility condition.** The
item stays open — the ~20 dated experience-rating fields are still needed to exercise the *other*
side of the gate — but **the size of the effect is no longer unknown.**

### 5. A limit of the probe, stated now rather than discovered later

**The probe varies pick sites, not other controls.** So a configuration that is inert because it is
**incomplete** reads as `INERT CONTROL`.

`schedule_rating=Yes` *without* `schedule_pct` is exactly that: inert in all 51, and the probe says
`INERT CONTROL` in all 51 — **correct by its own definition and misleading if read as "ISO never
applies schedule rating."** It is why the real measurement was taken with both set. Recorded here
because a verdict that is right and misleading is worse than one that is simply absent.

**A second gap:** `scripts/breadth.py` carries its own `Declared` and **does not get the probe**. Two
parallel harnesses is pre-existing, and breadth still reports *unchanged from base* without the
verdict.

### What was written

| | |
|---|---|
| `scripts/variants.py` | `Declared.pick`, `Declared.pins`/`picks`, `probe_no_op`, the three verdicts |
| `scripts/sweep.py` | probes every unmoved row; `inert_control` / `inert_value` in the summary and the CLI |
| `tests/verify_tester.py` | D4 inert value · D5 inert control · D6 moved |
| `docs/OPEN-ITEMS.md` | OI-93 closed with its limit stated; **OI-89 gains the 3-of-51 measurement** |

### ▶ Next session

**Four items closed in one session — OI-88, OI-91, OI-70, OI-93 — and one measured further.**

1. **Widen breadth live beyond two jurisdictions.** OK and NY are 32 of 32, and **that is still one
   class family in two states.** The offline sweeps say 51 of 51 build and rate for the deductible
   and limit groups; **live confirmation is the missing half**, and it is ~17 calls per jurisdiction.
2. **OI-89 / D3** — now the only known defect, and better specified than it was. Needs the ~20 dated
   experience-rating fields to exercise the other side of the gate.
3. **Give `breadth.py` the OI-93 probe**, or retire its `Declared` in favour of `variants.Declared`.
   Two harnesses with one behaviour between them is how the next silent no-op gets through.
4. **Fill the coverage grid** — still *1 of 19*, and four coverages moved today.
5. **Property exploration, reading pace only.** Unchanged since Entry 17.
6. **Cheap:** `567 → 570` through the docs; `verify_contract_figures` re-measuring rather than
   reading cached output; an 8dp rounding site would close OI-70's last corner.

---

## Entry 22 — Breadth widened to seven jurisdictions, and it found what it was for. ~~NEXT SESSION STARTS HERE.~~ *(the live handoff is **Entry 23**)*

- **Date:** 2026-08-17
- **Directed:** *"do it"* — widen breadth live beyond two jurisdictions
- **Built:** nothing. **The session's most valuable output is a defect, not a fix.**
- **Verified:** **112 of 115 comparable variants agree with ISO across seven jurisdictions**, on the
  premium and every published field. **83 live calls.** The three that did not agree are all the same
  defect, and it is ours.

### The widening was worth it on the first day

| | Result |
|---|---|
| **OK** | **17 of 17 MATCH** |
| **CA** | **17 of 17 MATCH** |
| **RI** | **17 of 17 MATCH** |
| **NY** | **15 of 15 MATCH** — the two claims-made variants are `NOT BUILT`, NY declaring `Occurrence` as its only coverage form |
| **TX** | 16 of 17 — **ISO refused `size-of-risk`** |
| **GA** | 16 of 17 — **ISO refused `size-of-risk`** |
| **FL** | 16 of 17 — **ISO refused `size-of-risk`** |

**Two states in the morning, seven by the evening**, and the jurisdictions were chosen to differ
structurally rather than to be easy: CA and TX file their own rule sets, GA takes all fourteen
deductible tables from countrywide, FL and RI are two of the three where schedule rating applies.

### 1. The 400 was not a validation complaint

**ISO's own rule engine failed**, and said so:

> `Error running Lookup Rule at line 5411 in RuleSet
> GeneralLiabilityClassificationPremOpsCoverageRules: Matrix: PremOpsSizeOfRiskLossCost, Keys: CW,
> 502, 50017. No results have been found`

**Our engine hits precisely the same miss** — `['GA','502','50017']`, then the countrywide retry
`['CW','502','50017']`, both `lookup-miss`.

**And then we diverge.** The `FirstNonNull` exhausts, **C6 returns null rather than raising**,
`PremOpsLossCost = None` is written, and the rating **continues to a finished premium.**

### 2. It is not OI-88's fix, and checking that was the first thing done

OI-88's fix emits `first-non-null-branch-abandoned`. **This is `first-non-null-exhausted` — C6, and
the behaviour since stage 2.** Both appear in the same trace, and the divergence is at the second.

**What OI-88 did was make the path reachable.** Size-of-risk refused in 49 of 51 jurisdictions until
this morning, so this code had never run. **Closing one defect exposed another that had been
unreachable behind it** — which is an argument for closing defects, not against.

### 3. The blast radius, measured before anything was decided

**14 of 51 jurisdictions write a null `PremOpsLossCost` and return a premium anyway** with
size-of-risk on: **AR, DE, FL, GA, IL, KY, LA, MA, MN, NM, NV, PR, SC, TX.** **0 of 51 in the base
configuration** — which is why nothing had ever seen it.

**The premiums are the tell:**

| Premium | Jurisdictions |
|---|---|
| **`6845`** | AR, DE, GA, MA, NM, NV, SC, TX |
| **`7215`** | FL, IL, LA, MN |
| `6560` · `6861` | KY · PR |

**Eight states return the identical premium** on different base premiums — GA's base is 7366, TX's is
7821. **A premium that does not depend on the state's loss cost is complete, plausible and wrong**,
which is the exact failure mode this engine exists to refuse.

Three of the fourteen are **confirmed** against ISO. The other eleven are **inferred** from an
identical trace, and are labelled that way rather than counted as confirmed.

### 4. Where the fix does not go

**Not in `FirstNonNull`, and not in C6.** An exhausted `FirstNonNull` returning null is correct, ISO
relies on it, and 4,327 sites in the corpus can exhaust. Changing a language rule to catch one
rating-level mistake would be the blunt instrument OI-88's measurement already rejected once.

**A missing loss cost is not a zero-rated risk. It is an unratable one.** That belongs in the rating
layer, as a refusal on a null loss cost.

**It needs an explicit go: it turns 14 jurisdictions from rating to refusing.**

### What was written

| | |
|---|---|
| `docs/OPEN-ITEMS.md` | **OI-94** raised `HIGH`, with the measurement, the three confirmations and the eleven inferences kept apart |
| `scripts/erc/out/breadth.csv` | The seven-jurisdiction run |

### ▶ Next session

1. **OI-94 — needs your go.** The measurement is done. The fix is a refusal in the rating layer on a
   null loss cost, **not** a change to `FirstNonNull`. Expect it to turn 14 jurisdictions from
   *rating* to *refusing*, which is the correct direction and still a semantic change.
2. **Keep widening breadth.** Seven jurisdictions found one defect on day one; **44 remain**, at ~17
   calls each. The offline sweeps already say which configurations build everywhere, so the live
   calls can be aimed rather than sprayed.
3. **OI-89 / D3** — needs the ~20 dated experience-rating fields.
4. **Give `breadth.py` the OI-93 probe**, or retire its `Declared`. Two harnesses, one behaviour
   between them.
5. **Fill the coverage grid** — still *1 of 19*.
6. **Property exploration, reading pace only.** Unchanged since Entry 17.


---

## Entry 23 — OI-94 closed, and the day's findings written up as what they are. ~~NEXT SESSION STARTS HERE.~~ *(the live handoff is **Entry 24**)*

- **Date:** 2026-08-17
- **Directed:** *"do it, log what we have discovered so far, highlight that you, as the harness, are
  discovering and resolving this"*
- **Built:** `Kernel._refuse_null_loss_cost`, two tests, and `docs/THE-HARNESS-FOUND-THESE.md`.
- **Verified:** **37 of 51 rate, 14 refuse — exactly the fourteen measured.** Every suite green:
  breadth 22/22 · interp 61/61 · golden 80/80 · tester 33/33 · stages 1/3/4/5/6 · phase2 14/14 ·
  CA 11/11 · NY 10/10 · oi50 7/7 · notebooks 20/20.

### 1. The refusal, and where it deliberately does not go

**Not in `FirstNonNull`. Not in C6.** An exhausted `FirstNonNull` yielding null is correct, ISO
relies on it, and **4,327 corpus sites can exhaust**. Changing a language rule to catch a
rating-level mistake is the blunt instrument OI-88's measurement rejected once already, eight hours
earlier.

**Only the rating layer knows that *this* null makes the risk unratable.** A missing loss cost is not
a zero-rated risk.

**Zero is left alone, and that is the part most likely to be got wrong later.** OK writes
`ProdsCompldOpsLossCost = 0` on a risk that rates and matches ISO. So the refusal is on **null**,
never on falsy — and `verify_breadth` **E7** exists because *"refuse when the loss cost is falsy"* is
the obvious wrong fix, and it would pass E6.

**A side effect worth having:** GA now refuses **without making the call at all**. The engine reaches
ISO's conclusion independently rather than spending a request to be told it.

### 2. `docs/THE-HARNESS-FOUND-THESE.md`

The day written up as what it was. **Five defects closed, one raised and closed the same day, one
question settled — and not one of them found by reading code.**

Five things they have in common, recorded because the pattern is more reusable than the fixes:

1. **Every one was found by running something against something else.** ISO against us (OI-88,
   OI-94), one measurement against another (OI-91), an engineered input against a prediction (OI-70),
   **the harness against itself** (OI-93).
2. **Not one needed a decision. Every one needed a measurement.** OI-88 waited three entries for a go
   it never needed — the read-only pass was always available.
3. **Closing a defect exposes the next.** OI-88 made size-of-risk reachable, which made OI-94
   reachable. OI-91 unblocked terrorism, which produced OI-93 within minutes. **The queue was a
   stack, and the top item was hiding the rest.**
4. **The measurement changed the fix twice.** Fixing on sight would have been wrong both times.
5. **The harness's own defects count.** OI-93 was in the measuring apparatus, and OI-91's twenty
   `NOT APPLICABLE` verdicts were our own refusal wearing a good explanation. **A harness never
   suspected of being wrong is not a harness; it is an assumption with tests.**

The document also states what the day does **not** claim: seven jurisdictions is not fifty-one,
eleven of OI-94's fourteen are **inferred** rather than confirmed, and the coverage grid still reads
*1 of 19*.

### Where the numbers stand

| | Before today | After |
|---|---|---|
| Size-of-risk rating correctly | **0 of 51** | 37 of 51, **14 refusing as ISO does** |
| Terrorism | 31 of 51 | **51 of 51** |
| Breadth against ISO | 31 of 31, two jurisdictions | **112 of 115, seven** |
| Rounding | evidenced against truncation only | **half-up, four engineered ties** |
| Known defects | 3 | **1** |

**92 live calls, every one aimed by an offline measurement that cost nothing.**

### ▶ Next session

1. **Keep widening breadth. 44 jurisdictions remain**, ~17 calls each. Seven found a `HIGH` defect on
   day one. **The eleven inferred OI-94 jurisdictions are the cheapest confirmations available** —
   they now refuse before calling, so confirming them costs nothing but a payload ISO will reject.
2. **OI-89 / D3** — the last known defect. Needs the ~20 dated experience-rating fields.
3. **Give `breadth.py` the OI-93 probe, or retire its `Declared`.** Two harnesses with one behaviour
   between them is how the next silent no-op gets through.
4. **Fill the coverage grid** — still *1 of 19*.
5. **Property exploration, reading pace only.** Unchanged since Entry 17.
6. **Cheap:** `567 → 570`; `verify_contract_figures` re-measuring rather than reading cached output;
   an 8dp rounding site closes OI-70's last corner.


---

## Entry 24 — Eleven jurisdictions live: 184 of 184, and OI-94 goes from inferred to confirmed. ~~NEXT SESSION STARTS HERE.~~ *(the live handoff is **Entry 25**)*

- **Date:** 2026-08-17
- **Directed:** *"keep widening breadth"*
- **Built:** nothing. **A widening run should mostly produce evidence, and this one did.**
- **Verified:** **184 of 184 comparable outcomes agree across 11 jurisdictions**, and **OI-94's blast
  radius went from 3 confirmed and 11 inferred to 13 confirmed and 1 unconfirmable.**

### 1. The cheapest calls available were the inferences

**OI-94's fix created a problem for its own evidence.** Eleven jurisdictions were *inferred* to be in
the blast radius from an identical trace. After the fix, our engine refuses those before calling —
so **breadth would never confirm them.** The refusal hides the evidence for the refusal.

So the payloads were sent to ISO **directly, bypassing our own refusal**, which is the only way to
ask the question:

> **AR, DE, IL, KY, LA, MA, MN, NM, NV, SC — all ten returned the identical 400**, same matrix, same
> *"No results have been found."*

**13 of OI-94's 14 are now confirmed against ISO.** The fourteenth is **PR, and it cannot be
confirmed by design** — no entitlement (OI-86). It stays labelled as the one remaining inference
rather than quietly counted.

### 2. Four new jurisdictions, chosen to be awkward

| | Chosen because | Result |
|---|---|---|
| **NJ** | OI-69 — the base loss-cost table is **absent from the state package entirely** | **17 of 17** |
| **OH** | the same | **17 of 17** |
| **WA** | a ZIP-domain terrorism state, and a different region | **17 of 17** |
| **MT** | single prem/ops territory, **files no terrorism location at all** | **16 of 16** comparable; `two-locations` `NOT BUILT` |

**The two OI-69 states were the ones most likely to break** — a base table resolving upward to a
header-only countrywide table is exactly the shape that once yielded a finished premium from zero
rows. Both clean.

### 3. The tally, with the categories kept apart

| | |
|---|---|
| Jurisdictions live-compared | **11** |
| `MATCH` on the premium **and every published field** | **181** |
| **Both refuse, same reason** (OI-94, TX/GA/FL) | **3** |
| `NOT BUILT` — undeclarable there (NY ×2, MT ×1) | 3 |
| **Comparable outcomes agreeing** | **184 of 184** |

**The three mutual refusals are counted separately and not folded into `MATCH`.** They *are*
agreement — both sides refuse the same submission for the same reason — but calling a refusal a match
would inflate the number that matters, and this project has spent two entries on the difference
between *rated* and *exercised*.

**`NOT BUILT` is the third outcome, not a failure:** NY declares `Occurrence` as its only coverage
form, MT declares one prem/ops territory.

### Where breadth stands

**Two jurisdictions this morning. Eleven tonight.** 40 remain, at ~17 calls each. The population is
still **one class family**, and that is now the honest limit rather than the jurisdiction count.

### ▶ Next session

1. **Keep widening — 40 jurisdictions remain.** Eleven have found one `HIGH` defect; the rate of
   discovery is falling, which is itself information. **Consider whether the next tranche should vary
   the class family instead**, since jurisdiction breadth is no longer the narrowest axis.
2. **OI-89 / D3** — the last known defect. Needs the ~20 dated experience-rating fields.
3. **Give `breadth.py` the OI-93 probe, or retire its `Declared`.** Two harnesses, one behaviour.
4. **Fill the coverage grid** — still *1 of 19*.
5. **Property exploration, reading pace only.** Unchanged since Entry 17.
6. **Cheap:** `567 → 570`; `verify_contract_figures` re-measuring; an 8dp rounding site closes
   OI-70's last corner.

---

## Entry 25 — A QA programme proposed, six decisions taken, and every document brought current. ~~NEXT SESSION STARTS HERE.~~ *(the live handoff is **Entry 26**)*

- **Date:** 2026-08-17 *(same session as Entries 18–24)*
- **Directed:** design a full QA plan using the agents · answer the volume and ISO-budget questions ·
  list what is needed from a person · work through those decisions one at a time · update all docs
- **Built:** **no engine code and no test machinery.** Four documents, six recorded decisions, and
  every existing document brought current.
- **Verified:** nothing new rated. This entry is planning and record-keeping, and says so.

### 1. The proposal, and the three agents that sized it

`docs/qa-plan-proposal_20260817.html` — 14 sections, six wireframes, self-contained.

**Three specialist agents measured the ground first, each from a different source**, and every figure
in the document is measured rather than estimated:

| Agent | Source | Supplied |
|---|---|---|
| `gl-engine-code-expert` | our Python | entry points, the 19-control surface, result schema, UI routes, measured timings, what blocks a 51-state matrix |
| `gl-authority` | ISO's machine-readable content | class codes, premium bases, territories, limit and deductible domains, sublines, exposure banding, axis independence |
| `iso-circular-expert` | ISO's filed manuals | which rules vary most by state, which are combination-sensitive, and the ten most likely to be implemented wrongly |

**Note for next time:** `iso-erc-expert` exists in `Agentic/` but is **not registered as a runnable
subagent** — only `gl-authority`, `gl-engine-code-expert` and `iso-circular-expert` are. Worth fixing
or worth deleting the folder; carrying a definition nobody can invoke is how the next person loses an
afternoon.

### 2. The central finding — two matrices, not one

**~282,000 tests, ~4,350 hits on ISO for a complete cycle**, and the gap between those numbers is the
whole design.

- **Value coverage** — every filed rate cell, **278,054** of them, **offline, zero ISO calls**,
  because ISO's own files are the source of truth for a rate.
- **Logic coverage** — **~2,500 scenarios**, small *because the axes were measured*: premium basis is
  a function of class code, both aggregates are keyed on the occurrence limit so 11,700 naive limit
  combinations are really **464**, and the deductible factor is keyed on the class's ILF assignment.

**The naive cross product is 1.94 × 10¹⁶** and is quoted only as the argument against itself. The
class axis collapses from **1,188 codes to 558 distinct rating behaviours**, 376 of them singletons,
so the sample is stratified by behaviour — **49 of the 59 premium bases carry five class codes or
fewer** and would otherwise never be touched.

### 3. Three findings that change the schedule rather than the design

1. **No effective-date axis exists**, and **43 jurisdictions change basis on 1 April 2027** with
   Rule 14 minimum premiums deleted outright and the class list dropping 1,188 → 1,163.
2. **Multi-class is not a control at all** — the applier sets every classification in every location
   to the same code.
3. **All 51 stored payloads are one location, one classification**, so two of the four headline goals
   have no starting payload.

### 4. The economics, and a paced week

**Live calls buy new truth; offline runs defend it.** A call is needed once per fact; the answer then
becomes a stored golden checked free forever. So the real budget is **~1,050 calls once, then ~220 a
week** — not 4,350 per cycle.

**The constraint on pacing is not cost, it is traffic pattern.** A thousand calls in an afternoon is
worth a phone call from ISO; the same thousand over weeks in blocks the size of a normal comparison
run is indistinguishable from ordinary use, because that is what it is.

### 5. Six decisions, taken one at a time

Recorded in `docs/WHAT-I-NEED-FROM-YOU.md`, which lists what only a person can supply — **and a
default for every item, so nothing is blocked waiting on an answer.**

| | Decision |
|---|---|
| **A1** | Read ISO's shipped sample submissions **as reference**, rebuild our own payloads. Nothing of ISO's enters this repository |
| **A2** | Anchor test shapes on **ISO's own 116 multi-class worked examples**, then extend to multi-location |
| **A3** | Fix the effective-date axis now; **probe with one call** whether ISO will rate a future date before committing to any 2027 tier |
| **A4** | **Exclude New York's ten disputed class codes** from testing |
| **A5** | **Synthetic loss histories spanning the credibility threshold**, not sitting at one point |
| **A6** | **Standing budget of 60 live calls a day**, weekly report |

**A1 corrected a claim I had made before measuring.** The first draft said the sample submissions
would unblock "seven sublines". **They unblock four of eight, thinly** — Owners & Contractors and
Railroad at 8 examples, Liquor at 3, Product Withdrawal at 2 — and **Pollution, Electronic Data,
Underground Storage Tank and Special Protective have no example at all.** They also do **not** unblock
multi-location (508 of 510 are single-location), though they are better than claimed for multi-class
(**116 files carry 2–4 classifications**).

**A4 carries a consequence worth restating:** excluding those ten codes from *testing* does not remove
them from the *engine*, which still rates on ISO's machine-readable 1,191. They are **reachable and
unverified**, so New York results must read *"agrees on the 1,181 codes both ISO sources confirm"* and
never as an unqualified pass.

**A6 re-paced the week** from the 110/day the first draft assumed to **60/day — 240 new calls this
week**, Tuesday opening with the 2027 probe. Calibration now spreads over four to five weeks rather
than two and a half. Today's 92 calls **predate** the standing budget and are recorded as such rather
than retrofitted.

### 6. Every document brought current

| | |
|---|---|
| `docs/PRD-GL-RATING-ENGINE.md` | §0 rewritten for 17 Aug; **§5 rewritten because it still said there was no external oracle** — there is, and the four-outcome reporting standard is now stated there; §8 rewritten with what is confirmed by someone else and what is not |
| `TESTING.md` | Dated forward; a new **live call budget** section before the failure section; records that several suites now assert the opposite of the day before |
| `docs/EXECUTIVE-SUMMARY.md` | Status note at the top with the day's figures and the standing caveat |
| `README.md` · `docs/index.html` | The four new documents listed and linked |
| `docs/WHATS-LEFT-PLAIN-ENGLISH.md` · `backlog_20260817.html` | Cross-referenced and re-rendered |
| `docs/OPEN-ITEMS.md` · both backlogs | OI-88, 91, 70, 93, 94 closed; OI-89 measured at 3 of 51 |

### ▶ Next session

**Tuesday 18 August, 60 live calls.**

1. **First call: the 2027 probe** (A3) — will ISO rate a future effective date? The answer decides
   whether the 2027 tier has an oracle or is a self-consistency exercise.
2. **Mechanism matrix, group 1** — CA, NY, TX, FL. Deductible ordering × ILF keying, the two
   top-ranked failure modes, both invisible at one variable at a time.
3. **Offline all week, unlimited:** the T1 matrix rated and triaged before any call is spent.
4. **Still owed from section B and C** — a loss cost multiplier, and **telling ISO about the
   validation programme before the week's calls start.** C1 is one email and removes a risk that
   costs nothing to remove.
5. **Unchanged:** OI-89 needs the synthetic loss histories now authorised; `breadth.py` still lacks
   the OI-93 probe; the coverage grid still reads *1 of 19*.

---

## Entry 26 — The QA programme built: tiers on the command line, a launcher in the browser. ~~NEXT SESSION STARTS HERE.~~ *(the live handoff is **Entry 27**)*

- **Date:** 2026-08-17
- **Directed:** *"yes, build according to the plan"*
- **Built:** `scripts/qa.py`, three QA routes and a QA card on `/tester`, and one file moved.
- **Verified:** every suite green — tester **33/33** · interp 61/61 · golden 80/80 · breadth 22/22 ·
  stages 1/3/4/5/6 · phase2 14/14 · CA 11/11 · NY 10/10 · oi50 7/7 · notebooks 20/20. **T1 run
  offline end to end: 22 scenarios, 264 ratings, two minutes, no cost.**

### 1. Phase 1 — the tiers are real, and two of them refuse

`scripts/qa.py`. Five tiers, and **T3 and T4 decline to run while naming what they need** — the
per-class payload builder, and the as-of probe from decision A3 — rather than pretending to exist.

| Tier | Scenarios | ISO calls | Live time |
|---|---|---|---|
| T0 Smoke | 1 | 50 | 7 min |
| **T1 Core logic** | **22** | **264** | **36 min** |
| T2 Full logic | 22 | 1,100 | 2h 34m |
| T3 Value sweep | — | — | **not built** |
| T4 Edition cliff | 22 | 264 | **blocked on A3** |

**T1 came out at 22 scenarios against the proposal's ~600.** Pairwise beat the design target, and the
proposal's figure should be read as the estimate it was rather than a measurement.

**Pairwise, not every combination, and the reason is empirical:** every measured defect so far needed
**two** things set at once to appear — a deductible *and* a limit, size-of-risk *and* a state whose
table is countrywide. **None needed three.** `_allpairs` is a plain greedy covering algorithm, not
minimal, deterministic, and short enough to read.

### 2. The budget guard, and the gap that writing it exposed

Decision A6 sets **60 live calls a day standing, 150 absolute**. A tier over the standing budget
**refuses to start** rather than warning; `--force` reaches the ceiling and nothing reaches past it.

**Then the guard reported zero on a day that had spent ninety-two.** Neither `sweep.py`'s CLI nor
`breadth.py` had *ever* written to the run store — only the browser did. **A budget that counts from a
store the command line never writes to is not a budget.** `sweep.py` now records every run. Today's
92 predate the fix and stay invisible, which is stated rather than backfilled.

### 3. Phase 2 — the same thing behind a button

Three routes: `GET /api/tester/qa` for tiers, costs and budget; `POST /api/tester/qa/plan` for the
matrix without running it; `POST /api/tester/qa/run` to start a tier. **All three compute from
`scripts/qa.py`** — a second list of tiers maintained next to the first would drift, and the drift
would look like a rating defect.

**The guard is enforced on the button too, and that was deliberate.** A tier over budget returns
**429** with what it needs and what remains; offline is always allowed. **A guard that held on only
one door would make the budget a matter of which door you came in by.** Verified both ways.

The card shows cost **before** the button, marks a tier red when it would be refused, and lists
findings as the run goes — disagreements *and* inert values — so a long tier is useful before it
finishes.

### 4. A test caught me, and it was right

`verify_tester` **A5 — "no script imports the UI"** — failed, because recording a CLI run had made
`scripts/sweep.py` import `ui`. That inverts the one-way dependency the project enforces.

**The fix was the code, not the assertion.** `ui/store.py` → `scripts/runstore.py`, because **a run
store is a results store and not an interface concern**: the command line writes to it, the browser
writes to it, and the live-call budget counts from it. `ui/__init__` no longer re-exports it, and the
UI imports it exactly as it already imports `variants` and `sweep`.

**Second time today an assertion written to hold a boundary caught the boundary being crossed** —
`verify_breadth` E7 was the other, pinning that a loss cost of **zero** still rates while only a
**null** refuses. Both times the assertion was right and the code was wrong.

### 5. The offline run earned its keep immediately

**264 ratings, two minutes, nothing spent. 17 engine refusals — every one the known OI-94 null loss
cost**, in TX, FL, GA and DE, all four inside the confirmed fourteen. **Nothing new, and not one of
them would have been worth a live call.** That is the *offline first* rule made concrete rather than
asserted.

### What was written

| | |
|---|---|
| `scripts/qa.py` | Tiers, the pairwise generator, cost estimation, the budget guard |
| `scripts/runstore.py` | Moved from `ui/store.py`; the docstring says why it moved and which test caught it |
| `ui/tester.py` | Three QA routes, a multi-scenario worker, the QA card and its script |
| `scripts/sweep.py` | Records every CLI run, so the budget can see it |
| `ui/__init__.py` · `tests/verify_tester.py` | Follow the move |

### ▶ Next session

**Phase 3 next — the summary verdict and the map.** Then the one that matters:

1. **Phase 3** — one-screen verdict and a US map. Cosmetic in the sense that the data already
   exists; valuable because it is what a non-technical reader can act on.
2. **Phase 4 — multi-location and multi-class payloads and controls.** **The largest piece, and
   engine-side rather than UI.** Two of the four stated coverage goals depend on it and on nothing
   else. Decisions A1 and A2 have already settled how the shapes are chosen.
3. **Phase 5** — harness review passes 2–4, including the adversarial agent read.
4. **Tuesday's 60 calls:** the 2027 probe first (A3), then the mechanism matrix in CA, NY, TX, FL.
5. **Still owed:** a loss cost multiplier (B1), and **telling ISO about the programme before the
   week's calls start** (C1).

---

## Entry 27 — Phase 3 and multi-class: the verdict, the map, and the class array twice. ~~NEXT SESSION STARTS HERE.~~ *(the live handoff is **Entry 28**)*

- **Date:** 2026-08-17
- **Directed:** *"log details, move on to phase 3"* → *"lets focus on multi-class for now, it's just
  the class array twice. We can make multi-location a backlog ua item"*
- **Built:** two charts, a per-jurisdiction rollup, the `classifications` control, and a cache that
  can no longer go stale.
- **Verified:** `verify_tester` **48/48** — Q1–Q8 for the QA programme, M1–M7 for multi-class. Every
  other suite green.

### 1. Phase 3 — a map that does not lie about size

`charts.usa_map` is a **tile grid, not a projection.** Every jurisdiction gets the same square,
because Rhode Island and Texas carry **one submission each** and drawing Texas two hundred times
larger would say something untrue about where the testing went.

**Hawaii is drawn and permanently blank.** It is not in ISO's corpus at all, and leaving it off the
map would hide that. **Q7 asserts every jurisdiction we can rate has a tile**, because a missing tile
silently drops a state from the picture.

`charts.verdict` computes its percentage over **comparable outcomes only**, and `runstore.qa_rollup`
carries the same rule further: a *not applicable* result can only soften a jurisdiction to `partial`
and **can never colour it as failing**. The rollup is worst-first — a state that disagreed anywhere
reads as disagreeing however much else agreed, because a summary exists to surface the worst thing
rather than average it away.

### 2. Multi-class — the array twice was right, and ISO's files said what goes in it

**The instruction was correct: it is the class array twice.** What ISO's own sample submissions
settled is what has to differ inside it.

| | |
|---|---|
| Multi-class locations in ISO's samples using **different** class codes | **99 of 114** |
| Their four-class Alaska example | mixes **Payroll with Gross Sales in one location** |
| Exposure | reused across bases in 93 of 114 |

**Two identical classifications exercise the loop and nothing else** — precisely the variant OI-93
exists to catch. So each extra classification takes a different declared code and, where one exists,
a **different premium basis**: the divisor is per basis, **per $1,000 for Gross Sales and Payroll but
no divisor at all for `Each` and `Units`**, so one divisor across a location is wrong the moment the
bases differ.

### 3. The pick took three attempts, and the failures are the useful part

| Attempt | Chose | What went wrong |
|---|---|---|
| Scan every class code | **Gallons** | Stopped at the first different basis it happened to meet — an 11-class exotic |
| Add a preference list | **Area** | *Membership is not ordering.* And **5,000,000 square feet is a hundred city blocks**: premium went **8,229 → 288,894** |
| Ask the declaration **by basis, in preference order** | **41675 Computer Consulting, Payroll** | Money like Gross Sales, so the inherited exposure stays plausible: **8,229 → 9,478** |

**The second failure is the one worth keeping.** The variant was *legal* and ISO would have priced
it — nothing was broken. It was simply not a risk anyone writes, and a coverage grid full of those
reads as more assurance than it is. That is decision A2 doing work rather than sitting in a document.

### 4. A near-miss on a finding that was not there

T1 offline went from **17 refusals to 19**, and the run store appeared to show a scenario with **no
size-of-risk** hitting a null loss cost — which would have been a new manifestation of OI-94.

**It was not.** The store held both the pre-axis and post-axis T1 runs under the same label, and I
was reading across them. Rating the configurations directly proved **all 19 come from the five
size-of-risk scenarios**, the known defect, and that multi-class alone rates cleanly everywhere.

**Recorded because reading a label nearly produced a false finding**, and the thing that prevented it
was re-deriving the result rather than trusting the summary.

### 5. A cache that survived a change to the thing it caches

`verify_tester` **G2 failed**: `ui/cache/` was serving a spec built from **19 controls while the code
declared 20**.

Deleting the file would have fixed the symptom. **The cache now carries a fingerprint of the control
set and rebuilds when it changes.** G2 only caught this because it compares the served spec against
`V.CONTROLS` rather than against a number — the same reason `verify_contract_figures` reading cached
output is on the housekeeping list, and the second stale-cache problem found in two days.

### 6. Multi-location deferred, with its consequences named

| | |
|---|---|
| **UA-1** | Per-location variation. A second location is a **deep copy differing only by territory**, so class, exposure and deductible cannot vary per location. Allocation, the miscellaneous-employee assignment to the largest-payroll class, and the 90%-owner-occupied split stay untested |
| **UA-2** | ISO's **three** territory-assignment rules — production site, **headquarters**, each location. We only ever exercise the third |
| **UA-3** | `Each` and `Units` — **no divisor at all**, the sharpest test of the per-basis divisor. Needs an exposure chosen per basis rather than inherited |

### What was written

| | |
|---|---|
| `ui/charts.py` | `usa_map`, `verdict` |
| `scripts/runstore.py` | `qa_rollup` — worst-first, and not-applicable can never fail a tile |
| `ui/tester.py` | `/api/tester/qa/summary`, the QA summary view, made the default tab |
| `scripts/variants.py` | The `classifications` control, its applier, `PREFERRED_SECOND_BASIS` |
| `scripts/qa.py` | `classifications` in the pairwise axes — **absorbed with no extra scenario** |
| `ui/variables.py` | The spec cache self-invalidates on a control change |
| `tests/verify_tester.py` | Q1–Q8, M1–M7 |
| `docs/BACKLOG-FEATURE-SETS.md` | The UA backlog |

### ▶ Next session

**Tuesday 18 August, 60 live calls, and multi-class gets its first live exercise.**

1. **First call: the 2027 probe** (A3).
2. **Mechanism matrix group 1** — CA, NY, TX, FL, now including the multi-class scenarios.
3. **Phase 5 — the harness review passes.** Pass 1 exists; passes 2, 3 and 4 do not. **Pass 3 is the
   one with a real failure behind it**: twenty jurisdictions were refused for three days by our own
   rule wearing a good explanation (OI-91).
4. **Still owed:** a loss cost multiplier (B1); **telling ISO about the programme before the week's
   calls start** (C1).

---

## Entry 28 — Phase 5 passes 3 and 4. The review refuted the fix I had written that morning. ~~NEXT SESSION STARTS HERE.~~ *(the live handoff is **Entry 29**)*

- **Date:** 2026-08-17
- **Directed:** *"work in order"* — pass 3, then pass 4
- **Built:** `scripts/qa_review.py` — pass 3 in full, pass 4's brief half — and the corrections its
  first real use produced.
- **Verified:** `verify_tester` **58/58** (R1–R10 new). Every other suite green.

### 1. Pass 3 — is a `NOT APPLICABLE` real, or is it ours?

**`NOT APPLICABLE` is the only outcome never counted as a failure**, which makes it the one place a
defect can sit indefinitely without moving a number anyone watches. **It already did**: OI-91, where
twenty jurisdictions were refused for three days by our own inert fallback **wearing a readable
reason** — and the reason is exactly why nobody questioned it.

So the pass re-derives every `NOT APPLICABLE` **without calling `variants.build`,
`Control.options`, `Declared.values` or `gl_engine.schema`**. It reads ISO's own CSVs out of the
resolved package. **R5 asserts that independence by reading this file's source**, because a docstring
claiming independence is not evidence.

**Three verdicts, and the third is the point:** `CONFIRMED` · `CONTRADICTED` · **`UNVERIFIED`, which
names what would settle it** rather than saying `CONFIRMED` and meaning *"I did not check"*.

**The first run produced twenty-plus false findings and they were mine.** A configuration is refused
when **one** control cannot be expressed; every other control in it being legal is the normal case.
Aggregating worst-first reported Montana as wrongly refusing a `100,000 CSL` limit it declares
perfectly well, when the cause was `locations=2` against its single territory. **A review pass that
cries wolf is worse than no review pass**, because the next real finding reads as noise.

**Verified the detector detects.** Fed the exact OI-91 configuration it returns `CONTRADICTED`; fed
NY's genuine claims-made narrowing it returns `CONFIRMED`. All **40** `NOT APPLICABLE` results on
record are ISO's narrowing, none ours.

### 2. Pass 4 — and the line the file will not cross

**A Python script cannot invoke the specialist agents.** So pass 4 splits honestly: the script
assembles the brief, the operator dispatches it. Three rules live in the prompts:

| | |
|---|---|
| **Refute, never confirm** | An agent asked *"is this right?"* tends to agree |
| **Each reviewer forbidden the other's corpus** | Agreement between independently-built sources is evidence **only while they stay independent** |
| **`CANNOT TELL` allowed** | A forced verdict is a guess wearing a citation |

**A clean agreement never becomes a brief** — there is no claim to break, and a review queue full of
confirmations is one nobody reads.

### 3. Its first real use refuted OI-94, which I had built that morning

Dispatched deliberately at **my own most recent fix**, on the claim most likely to be wrong.

**UPHELD, and better evidenced than when I wrote it.** Texas never filed ISO's size-of-risk plan at
all. **The two corpora agree independently:** the **35** jurisdictions whose ERC size-of-risk table
is populated are **exactly** the 35 states with a *Size Of Risk Rating Supplement* circular — no
difference in either direction, ERC measured first. **No engine change can rate size-of-risk in
Texas, and none should try.** Nor does the rule over-refuse: base, multi-class, deductible, limit and
terrorism configurations all rate **51 of 51**.

**REFUTED, and this half is mine.**

> I wrote that ISO's 400 shows ISO *"refuses the same submission for the same reason."* **It does
> not.** ISO's error is a miss on `PremOpsSizeOfRiskLossCost` with keys `CW, 502, 50017` — and
> **`502` is Georgia's territory.** The body I quoted is the **GA** call; TX and FL were never
> captured in full. The 400 confirms ISO **also fails** on size-of-risk, not that its reason matches
> ours. **That claim was repeated in OI-94, the build log and a commit message.**

**And the refusal message named the wrong table.** It blamed `PremOpsLossCost` — in Texas a healthy
**9,504-row** table that had resolved `0.095` perfectly well. The empty table is
`PremOpsSizeOfRiskLossCost`, **a 53-byte header-only file**. Anyone following that message went to
the wrong file. Now fixed to name the lookup that actually came back empty.

**Neither would have been caught by a test**, because the engine's *behaviour* is right and its
*explanation* was wrong. Tests check behaviour.

### 4. Two code findings recorded, deliberately not acted on

- **`_refuse_null_loss_cost` walks the whole tree** and would refuse on
  `ERPTotalBasicLimitsCoSubjectLossCost`, for which there is **no evidence**. It does not over-fire
  in any of the 51 today; **nothing constrains it not to.**
- **It raises at `kernel.py:163` before the referral register runs at `:170`**, so
  `d_size_of_risk_without_costs` (R10/R11) — **the precise pre-written diagnosis for exactly this
  case** — can never fire. The engine emits the general message and discards the accurate one.

### 5. OI-95 — the first escalation the two corpora produced together

**ISO's content files `0` where ISO's manual files `(a) — refer to company`.** In Texas, **1,188 of
1,188 classes agree** between the two sources, including **178 `(a)`↔`0` correspondences with zero
mismatches**. We price those as zero and **raise no referral**: adding class 41675 moved Texas
**7,821 → 8,973 with 0 referrals and 0 messages**.

**The countervailing evidence is strong and is recorded first.** The Texas base risk — whose products
side is itself an `(a)` — rates **7,821 and is a recorded live `MATCH` against ISO**. So **ISO's own
service also computes zero for an `(a)`.** Whether that is intended or a known industry seam is **not
a question either corpus settles. It needs a person.**

### What was written

| | |
|---|---|
| `scripts/qa_review.py` | Pass 3 in full; pass 4's brief generator and prompts |
| `gl_engine/rating/kernel.py` | The refusal message names the lookup that actually came back empty |
| `tests/verify_tester.py` | R1–R5 (pass 3, including *the detector detects*), R6–R10 (pass 4's prompt rules) |
| `docs/OPEN-ITEMS.md` | **OI-94 corrected** with all three findings; **OI-95 raised** |

### ▶ Next session

1. **Pass 2 — is a refusal correct?** The last of the four, and the one that spends calls re-asking
   questions we have already decided. It is also the only way to settle *"would ISO refuse **this**
   submission, and with which error"* — the half of the OI-94 claim that remains `CANNOT TELL`.
2. **The two open code findings** above — both message-quality, neither premium-affecting.
3. **OI-95 needs a decision**, not a fix.
4. **Tuesday's 60 calls:** the 2027 probe (A3), then the mechanism matrix in CA, NY, TX, FL — now
   with multi-class in the pairwise set.
5. **Still owed:** a loss cost multiplier (B1); **telling ISO about the programme before the week's
   calls start** (C1).

---

## Entry 29 — A layered test programme, and a page to run it from. ~~NEXT SESSION STARTS HERE.~~ *(the live handoff is **Entry 30**)*

- **Date:** 2026-08-18
- **Directed:** a back-and-forth on UI strategy — *"a separate, new page for kicking off and tracking
  results"*, starting from the order of test cases; then *"make the changes"*.
- **Built:** `scripts/layers.py`, `ui/tests_page.py`, `ui/runfile.py`, a real aggregate-limit control,
  and 30 offline checks over the lot.
- **Verified:** `tests/verify_layers.py` **30/30**. Every other suite green, `verify_tester` included
  — the QA tab was not touched.

The whole design is written up in [`docs/UI-STRATEGY.md`](docs/UI-STRATEGY.md). What follows is what
the build taught, which is not the same thing.

### 1. The aggregate limit was never an axis, and half the ILF key was untested

`_apply_occurrence_limit` set the occurrence limit and then **derived** both aggregates, taking the
first value ISO declared legal with it. Every limit test ever run therefore varied one half of a
two-part key and left the other on whatever came first in a table.

ILF keying is one of the two top-ranked failure modes in the backlog. It has been half-tested the
whole time, and nothing said so — the runs all passed, because passing was never the question.

`general_aggregate` is now a control of its own, keyed on the occurrence limit, setting both
aggregates and refusing a pair ISO does not declare. The old derivation still runs when the aggregate
is left alone, and **stands aside when it is set** rather than writing a value that would be
overwritten — a `pick` recorded for a value that never reached the payload would have shown up in
`probe_no_op` as a choice site nobody chose.

### 2. You cannot name an aggregate as a figure and run it in 51 states

The obvious plan was *"1,000,000 occurrence against 2,000,000 aggregate"*. Measuring killed it: the
legal aggregate set is keyed on the occurrence limit **and differs by state** — four legal values at
25,000 in Texas, eight at 1,000,000. A figure legal in one state is undeliverable in another, and a
run that reported `NOT APPLICABLE` for half the country would have said nothing about limits.

So the plan carries **positions** — `@lowest`, `@middle`, `@highest` — and `sweep.run_config` gained a
`resolve` hook that turns a position into that state's declared value before the payload is built.

**Each row records the figure it actually got.** A run that stores the request and not the answer
cannot be read back a week later, and *"the highest aggregate"* is a different number in every state.

### 3. Three measurements changed the design mid-conversation

Each of these was decided one way, measured, and then decided differently.

- **The basis split is a guard, not a routine event.** We agreed a class filed on different premium
  bases in different states must be split into separate sweeps and never compared across them. Then
  we counted: **1,188 class codes declared in each of TX, CA, NY, FL, OK and MT; 1,187 common to all
  six; the basis differed for exactly one, and that one was simply undeclared in a state.** The rule
  is right and will almost never fire. It stays, because when it fires it matters.
- **ISO files no class families.** Codes cluster by leading digit, but the data declares only codes,
  descriptions and bases. A family picker would have been our taxonomy dressed as ISO's — so the
  picker filters by **basis**, which is declared. (RULE #1 again: read the declaration.)
- **There are 59 premium bases and most are counts.** *Number of Zoos*, *Each Pier*, *Number of
  Drawbridges*, *Passenger Days* — no divisor at all. One default exposure figure across that set is
  meaningless, which is the whole argument for choosing the basis before the class rather than after.

### 4. The budget stopped deciding and started reporting

Decision A6's gate refused a tier that went over 60 calls a day. That was right for one-day tiers and
wrong for this: a layer-3 run at the full matrix is about 600 calls, and a gate set for the old shape
would refuse most useful runs of the new one.

So the layered programme **shows a ticker and runs what you asked for**, with an allowance set per
run. The tier runner keeps its gate, because leaving the QA tab alone was the point. **Both read the
same count**, which moved into `runstore.spent_today` — two counts of the same number drift, and the
one on screen becomes the one nobody trusts.

### 5. What an allowance is allowed to cut

When the matrix does not fit the allowance, **the configuration list is thinned and the state list
never is.** Every state appears in every run, so two runs stay comparable and no coverage figure is
quietly built on a smaller country.

The thinning keeps **the ends and an even spread between them**, because the ends of a filed table are
where a keying error shows; a thinning that kept the middle would drop exactly the rows worth having.
**What it dropped is written into the run file**, because two runs of the same layer at different
allowances are different matrices, and one that does not say so invites a comparison that is not
valid.

### 6. A stopped run is not a failed run

Pause holds between states; stop ends after the current one. Either way the run is **stored as a
partial that names the scenarios and states it never reached** (`stopped_early`, `not_reached`), and
the run file says so at the top.

The alternative — discarding a run because it did not finish — throws away two hundred calls' worth of
answers to punish a change of mind about the last hundred.

The same principle covers the offline pre-flight: a state whose payload cannot be built never reaches
ISO, and it is carried into the result as `preflight_excluded` rather than dropped. **A run that shows
only what it called reports coverage it never had.**

### 7. `compare_payload` had been keeping three differences out of eleven

It computed every differing field and returned `first_differences` — the first three, joined into a
string for a terminal that has a width. Fine for a console line, useless for a page you review. It now
returns the whole list, and the console still prints three.

### 8. What is on the page

`/tests`, beside the QA tab, both writing to the same store. Layer picker · basis-first class picker
with a filter · exposure labelled with its own unit · allowance · ticker · plan-before-you-run ·
progress with pause, resume and stop · and every finished run listed as a standalone HTML file.

Each run writes `results/runs/<layer>-<class>-<stamp>.html`: headline counts, what actually ran
(groups, not-filed, thinning, early stop), then every state sorted by size of difference and
expanding to the fields that differ. **Git-ignored, and `.gitignore` now says why** — a run file is a
rendering of ISO's licensed premiums.

### 9. The test count, and the inconsistency it exposed

The allowance section shows **how many tests the run would be** before you press anything — *"204
tests · 4 configurations × 51 jurisdictions · 200 against ISO"*, updating as you type. It is local
arithmetic from the layer's configuration count and the jurisdiction list, so it costs nothing and
never lags; it says **about** N against ISO because it assumes the class is filed everywhere.
**`Plan it` reads the declaration in all 51 and replaces the estimate with the counted figure**,
which is smaller wherever ISO does not file the class.

Writing it surfaced a real disagreement. The page said an allowance cuts nothing offline; the server
thinned anyway. **An allowance is denominated in live calls and an offline run spends none**, so
thinning one gives up coverage to save something it was never going to spend. `plan()` now takes
`offline`, and the page, the HTTP route and the CLI all pass it — B7 and B8 assert it.

A counter is a cheap thing to add and it made two implementations of the same rule state their
answer side by side. That is worth remembering the next time a number is only visible after a
button.

### ▶ Next session

1. **Run L2 live on one class.** 50 calls, one class, and the first real use of the whole thing.
   `--offline` first, always.
2. **L5 and L6** — the deductible amount ladder and combined-versus-separate — are designed in
   §1 of the strategy document and not built.
3. **Pass 2 — is a refusal correct?** Still the last of the four, and still the only way to settle the
   half of OI-94 that reads `CANNOT TELL`.
4. **The index over run files** lists everything newest-first but cannot filter to one class yet.
5. **Still owed:** a loss cost multiplier (B1); telling ISO about the programme before the week's
   calls start (C1); OI-95 needs a decision, not a fix.

---

## Entry 30 — The matrix got a hover panel and a click filter; one check hadn't caught up. ~~NEXT SESSION STARTS HERE.~~ *(the live handoff is **Entry 33**)*

- **Date:** 2026-08-18
- **Directed:** pick up the live browser verification of the interactive run-page matrix that Entry 29
  left mid-check, then document it.
- **Found:** `tests/verify_layers.py` **E3** failing — 29/30. The matrix grid gained a hover panel
  (status, our premium, ISO's, delta, resolved values) and a click-to-filter into the state table,
  built as one inline `<script>` block reading the run's own embedded data. E3 had been written before
  that existed and banned any `<script>` tag outright, on the theory that a run file loads nothing.
- **Fixed:** the theory was still right, the check was just testing the wrong thing. An inline script
  with no `src`, no `fetch`, no `XMLHttpRequest` loads nothing from the network regardless of whether
  a `<script>` tag is present. E3 now checks for those specifically instead of banning the tag.
  30/30. `verify_tester` (63/63) and `verify_phase2` (14/14, 1 skipped — needs `--live`) both still
  green, confirming nothing else moved.
- **Documented:** `docs/UI-STRATEGY.md` §4 gained a subsection on the matrix — what hovering and
  clicking a cell do, and why it is still a self-contained file.

### ▶ Next session

Entry 29's list still stands: run L2 live on one class, then L5/L6, then the TX refused-payload call
that settles OI-94. The `docs/run-page-*.html` files in the working tree are exploratory prototypes
for the matrix design, now superseded by the real thing in `ui/runfile.py` — worth a decision on
whether to delete them or keep them as reference before they get committed by accident.

---

## Entry 31 — The harness gets its own notebook set. Seven files, one per, and a second index. ~~NEXT SESSION STARTS HERE.~~ *(the live handoff is **Entry 33**)*

- **Date:** 2026-08-18
- **Directed:** *"start the harness notebook set"* — the second of START-HERE-TOMORROW's two
  named things, settled in favour of **a second set** (the doc's own recommendation) rather than
  folding harness code into the twenty engine notebooks or covering only the QA pair.
- **Built:** `notebooks/harness/`, seven notebooks — `01-variants`, `02-qa`, `03-qa_review`,
  `04-sweep`, `05-runstore`, `06-charts` (`ui/charts.py`, not `scripts/`), `07-layers` — plus its own
  `00-index.ipynb`. Same six-cell shape as the engine set, generated public surface included.
  `notebooks/00-index.ipynb` and `notebooks/README.md` both gained a pointer to it.
- **Verified:** `tests/verify_notebooks.py` **28/28** (20 engine + 8 harness).

### What building it turned up

**`verify_notebooks.py` assumed one flat directory.** It globbed `NOTEBOOKS/*.ipynb` and chdir'd to
that one directory for every notebook, which is exactly wrong for a subdirectory: a harness notebook
run from `notebooks/` (not `notebooks/harness/`) would resolve `Path.cwd().parent` one level short
of the repo root. Fixed by chdir'ing to **each notebook's own parent** instead of a constant —
which is also just a more honest match for what actually happens when a person opens the file
directly in Jupyter Lab, cwd = the file's own directory. Switching `glob` to `rglob` to find the
subdirectory surfaced a second thing: **`.ipynb_checkpoints/` was never excluded, because a flat
glob never walked into it.** Jupyter's autosave copies started failing the moment they were
discovered, for the same off-by-one-directory reason. Excluded explicitly; they were always
gitignored, never meant to be run.

**Two notebooks would have written into the real results store on every run, and didn't get to.**
`H5 runstore.py` and `H7 layers.py` both demonstrate functions that append a run. A notebook that
appends a demo run to `results/runs-*.jsonl` every time someone opens it corrupts the exact thing
the append-only store exists to keep honest — the append count would include a run that rated
nothing real. Both point `runstore.RESULTS` at a temporary directory before calling `append()` or
`run()`, and restore it after; verified by hand that the real store's run count is unchanged before
and after executing every cell.

**The order confirmed something Entry 29 only asserted in prose.** Writing `H7`'s thinning cell
against a live `plan()` call reproduced the exact claim from Entry 29 §5 — an allowance of 6 against
L3's 12 configurations keeps the lowest and highest occurrence limit and drops the ten in between,
never touching the state list. Nice to have that as a runnable cell rather than a described one.

### ▶ Next session

Same as Entry 30's: L2 live on one class, then L5/L6, then the TX refused-payload call for OI-94.
Nothing about the notebook build changes that list — it documents work already done, it doesn't
open new work.

---

## Entry 32 — The `/tests` page gets an aggregate: a table, a verdict per layer, a trend, and the
## charts already built for the QA tab finally get used somewhere else. ~~NEXT SESSION STARTS HERE.~~
## *(the live handoff is **Entry 33**)*

- **Date:** 2026-08-18
- **Directed:** design conversation over several rounds — an aggregate view, a placement decision
  (mockups compared, a separate card chosen over folding into Run files), a grid style decision
  (mockups compared, the ruled/boxed style chosen over zebra rows and a borderless style), then a
  set of visualization options (mockups again — status dots, `status_bars`, `verdict`, `usa_map`,
  `agreement_over_time`, all real `ui/charts.py` output, not hand-drawn approximations), and a final
  composition: dots on the existing tables, one `verdict` card per layer instead of one combined
  card, the trend chart, and `status_bars` + `usa_map` moved into the Result card. Then: *"let's
  build, then log, and update all relevant docs."*
- **Built:** `layers.stored_rollup()`, `layers.stored_history()`, `layers.run_map()`; a `charts`
  import into `ui/tests_page.py`; an Aggregate card (status dots, click-to-filter, already built
  last session); a Verdict-by-layer card (one `verdict()` chart per layer, 2-up grid); an Aggregate
  trend card (`agreement_over_time()` across every stored layer scenario); `status_bars()` and
  `usa_map()` wired into the Result card, scoped to the run that just finished.
- **Verified:** `verify_layers.py` 30/30, `verify_tester.py` 63/63. Exercised live in the browser —
  seeded real (offline) scenarios, watched the Aggregate table, four verdict cards and the trend
  render from the real store, ran an actual offline scenario through the UI end to end and watched
  the Result card's outcome bar and coverage map populate from that run's own rows.

### The `/tests` page had never used a single chart from `ui/charts.py`

All eight chart functions — `verdict`, `usa_map`, `status_bars`, `agreement_over_time`,
`coverage_grid`, `response_curve`, `premium_spread`, `slot_bars` — were built for the QA tab
(`ui/tester.py`) and none of them had ever been called from `tests_page.py`. Four of the eight are
now in use on `/tests`; the pattern from `tester.py` carried over exactly — the server renders the
SVG string and ships it in the JSON, the client does `el.innerHTML = svg`, nothing is drawn twice.

### A run-file entry doesn't carry a `not_applicable` count, and the dot logic had to work around it

The Aggregate table's dot is trivial: the store's per-layer totals already separate differ, refused
and not-applicable, so the worst-first rule reads straight off them. The Run files table's dot is
not, because `runfile.entries()` — the index a rendered run file writes to `results/runs/index.json`
— only ever stored `rated`, `agree`, `differ` and a `refusing` list; nothing about not-applicable
rows survived into the index. `histDot()` approximates: an offline run reads grey outright, a
live run with any differ or refusal reads red, `agree === rated` reads blue, and everything else
(live, no differ, not fully agreeing) is read as not-applicable softening an otherwise clean run.
It is an approximation stated as one, not a silent guess dressed as data — worth widening
`runfile.entries()`'s stored fields if the dot needs to be exact later.

### The dot logic almost shipped a wrong default, and offline data caught it in the first screenshot

The first version of `aggDot()` fell through to `'agree'` (blue) whenever nothing else matched —
which is correct when a scenario actually agreed, and wrong when it was never compared at all.
Every seeded scenario today was offline (no live ISO calls spent on a UI polish session), so every
layer showed a confident blue dot for data that had agreed with nothing. Fixed by computing the same
`uncompared = rated - agree - differ - not_applicable - refused` the verdict chart already computes,
and reading a `rated`-but-`agree === 0` layer as grey, not blue. The empty store from Entry 30's
clear-out is what made this visible immediately instead of after real data papered over it.

### `status_bars` wants lists; a summed rollup only has counts

`charts.status_bars` calls `len()` on `differ`, `premium_only`, `engine_stopped`, `not_applicable`
and `errors` — it was written for a single scenario's summary, where those are lists of jurisdiction
codes. `layers.rollup()` already reduces a whole run's scenarios to counts. `_bars_summary()` bridges
the two with placeholder lists (`["x"] * n`) rather than widening `rollup()` to keep both shapes —
`status_bars` never reads an element, only the length, so the placeholder is exact and nothing about
`rollup()`'s existing callers had to change.

### Every live server test ran with the store emptied first, and emptied again after

Same discipline as Entry 30/31: nothing in this session's testing was allowed to land in the real
`results/` store. Seeded scenarios were offline only — a live comparison costs a real ISO call, and
spending one to check whether a chart renders is not what the budget is for. The store was reset to
empty at the end, same as it was at the start of the day.

### ▶ Next session

Untouched by any of this: L2 live on one class, then L5/L6, then the TX refused-payload call for
OI-94. Two small things worth a decision if the aggregate view gets used for real: whether
`runfile.entries()` should carry a `not_applicable` count so `histDot()` stops approximating, and
whether the trend chart should be filterable by layer the way Run files already is — flagged during
design and deliberately left as a follow-on rather than built blind.

---

## Entry 33 — A run can be reviewed now: a mechanical pass for free, a brief for what it can't
## explain, and a place to paste back what a person said. No API key anywhere in it.
## **NEXT SESSION STARTS HERE.**

- **Date:** 2026-08-18
- **Directed:** a planning conversation, explicitly *not* a build request — "I want to be able to go
  into an individual run and get analysis... without an API key. Otherwise, could we generate an md
  file... and I share it here." Landed on the same split `qa_review.py`'s pass 4 already committed to
  (the harness assembles evidence, a person dispatches it), applied per run, with the one piece pass
  4 left open — where the answer lives — resolved as a second store keyed to the run file's name.
  Wireframed first (`docs/run-review-wireframe.html`, five states), risks named before a line of code:
  unverified pasted text read as fact, a stale analysis shown as current, an XSS surface in the
  posted-text render, licensed content formatted for easy copy-paste. Then: *"let's build this, make
  sure we are logging and updating docs along the way."*
- **Built:** `scripts/reviews.py` (storage, pattern match, brief generation, dedup against prior
  reviews) and `ui/review_page.py` (`/review/<run-file>`, four API routes), mounted ahead of
  `tests_page`'s own routes the same way `tests_page` is mounted ahead of `tester`'s. `runfile.py`
  gained one outbound link, `Review this run →`, in the run file's header — nothing else about the
  run file changed. `tests_page.py`'s Run files table gained a second, independent tag.
- **Verified:** `verify_layers.py` 30/30, `verify_tester.py` 63/63, `verify_notebooks.py` 2/2 (index
  pair). Exercised live in the browser end to end — a synthetic run with one genuinely novel DIFF and
  one refusal matching a known local-problem signature, generated a brief, posted a paste-back
  analysis, watched the run file's link, the review page's per-finding state, and the Run files
  table's tag all update and agree with each other.

### The scope that got cut, and why cutting it was the honest call

The wireframe showed named defects — "OI-88," "OI-89" — tagged directly onto failing rows. Building
that for real would have meant inventing detection logic for each one right now, much of it from
memory of what the defect *was* rather than a re-derivable check against the row in front of it —
exactly the shape of mistake this project has been burned by before (OI-91's false 20-state count,
the review pass that cried wolf on Montana before worst-first aggregation fixed it). So the pattern
match layer that got built is narrower and more honest: reuse `qa_review.classify` on a refusal
(already mechanical, already in the codebase), recognize an `INERT VALUE` pick `probe_no_op` already
computed, and check whether the *exact* same finding — jurisdiction, status, differing fields — was
explained in a different run's review before. Everything else says `no known pattern` rather than a
guess dressed as one. `UNVERIFIED` beats a guess is `qa_review.py`'s own rule; this just applies it
to itself before it applies it to anything else.

### The dedup signature broke on its first real test, and JSON is why

`_signature(row)` returns `(juris, status, tuple(differing_fields))` — a tuple nested inside a tuple,
perfectly hashable in memory. Round-tripped through `json.dumps`/`json.loads` once, the inner tuple
comes back as a list, and `list` is not hashable — `_prior_by_signature` crashed the moment a second
run actually tried to dedup against a first one's posted analysis, which only a real two-run test
caught. Fixed by rebuilding the signature's inner element back into a tuple explicitly on read,
rather than trusting a round-trip to preserve a type JSON doesn't have.

### `quick_status` almost shipped a claim it couldn't back up, in the very first screenshot

The Run files table needs a status per run without a store round-trip per row — forty runs, each a
full JSONL scan, on every page load, was the cost being avoided. The first version read the saved
review record and called it `reviewed` when every finding *in the record* had a posted analysis. The
gap: a pattern-matched finding nobody ever clicked into is never written to the record at all, so a
run with one real answer and one silently-explained refusal read as fully reviewed on the table while
the review page itself — which does pay for the round-trip — correctly said `explained`, not
`reviewed`. Caught by comparing the two pages side by side in the first live test, same as the
Aggregate dot's offline-defaults-to-blue bug in Entry 32. Fixed by renaming the claim to what the
cheap check can actually support: `has_notes`, not `reviewed` — a run can have a real answer sitting
on it and still be understated by the table, on purpose, because overstating it the other way is the
worse failure.

### Every live test ran against a synthetic run, and the store was reset after

Same discipline as every session today. The DIFF and the refusal used to exercise the review flow
were injected into a real offline run's rows by hand, not produced by an actual disagreement with
ISO — no live call was spent manufacturing something to review. `results/runs-*.jsonl`,
`results/runs/` and `results/reviews/` were all cleared at the end.

### ▶ Next session

Unchanged: L2 live on one class, then L5/L6, then the TX refused-payload call for OI-94, plus
Entry 32's two follow-ons. Nothing about the review page opens new priority work — it is there for
whenever the backlog above actually produces a finding worth reviewing.

---

## Entry 34 — Four decisions, one direction, and the direction turned out to be measurable in ten
## minutes. No code. **NEXT SESSION STARTS HERE.**

- **Date:** 2026-08-19
- **Directed:** an explicit backlog-only instruction — *"Don't build, update backlog."* Four answers
  to the five standing asks (B1, C1, C2, A3) plus a direction on OI-95.
- **Changed:** `docs/WHAT-I-NEED-FROM-YOU.md` (B1 decided, C1 declined, C2 held, A3's open half
  answered, the short version rewritten), `docs/OPEN-ITEMS.md` (OI-95 amended and reclassified
  `OPEN` → `BUILD WORK`), `docs/START-HERE-TOMORROW.md` (§5 rewritten, §1's as-of row unblocked, §6
  gained two items, §8's second item superseded).
- **Not changed:** any Python. No engine, no UI, no scripts, no tests.

### The four decisions, and why each is the right shape rather than just an answer

**B1 — the loss cost multiplier stays at `1.0`.** The reasoning given is the part worth keeping:
*"we want to test ISO RAaS right now, this isn't a client app."* Both sides of that comparison are
loss costs, so a multiplier has nothing to do. **`1.0` is better than a plausible placeholder like
`1.55` precisely because it is inert** — the factor sits in the chain, positioned correctly, and every
stored result stays exactly comparable against ISO. An invented number would have to be divided back
out of every comparison, and would leave figures on disk that look like rates and are not.
Premium-level testing becomes a **deferred decision** rather than an open gap.

**C1 — the note to ISO is not being sent.** Closed by decision, not parked. Nothing operational
changes: the pacing rules were adopted to keep the traffic unremarkable and that reasoning does not
depend on whether a note went out.

**C2 — the size-of-risk report is held for more testing of our own.** This one changes priorities
rather than just status: **the TX refused-payload call is now the cheapest thing on the board**,
because it is what turns *"ISO refuses for the same reason"* from an inference into a measurement in a
second state. **And it forced a stale claim out of a document.** C2's section still read *"our engine
now refuses the same submissions for the same reason, so we agree with ISO's behaviour"* — the exact
sentence OI-94's adversarial review refuted two days earlier. The refutation had been written into
the register and never propagated to the page a person would actually send from. **A correction that
lives in one document is half a correction.**

**A3 — ISO rates future effective dates, so the effective date becomes a variable.** The probe
question is answered without spending the probe. What matters is the shape the direction gave it:
*"we should have an effective date variable"* — **an axis, not a mode.** A second tier run at a second
date would have doubled the programme; a control set per scenario means the 2027 cliff gets exercised
by ordinary test cases. And it is the same fix the axis defect needed anyway, which **unblocks the
as-of date selector** that had been held back because a dropdown offering dates the rating ignores is
worse than no dropdown.

### OI-95 stops being a judgement call, and the file was sitting in the corpus the whole time

The direction: *"there should be a table that indicates classcodes use loss costs, company, or
industry. Company is equivalent to A Rated, which is a refer to company, in those cases, we should
input a company rate. If it's industry, that's an ELP being used."*

**Checked before writing it down, and it is exactly right.** `PremOpsELPText.RateTable.csv`, in every
package, declares one of three values per class per state. Measured in `GL_TX 20250801 V01`, all 1,188
classes, cross-tabulated against `PremOpsELP.RateTable.csv`, **zero exceptions**:

| `PremOpsELPText` | count | its ELP rate |
|---|---|---|
| `Rate/Loss Cost Applies` | 1,010 | `0`, every one |
| `Industry` | 110 | **non-zero, every one** |
| `Company` | 68 | `0`, every one |

**68 + 110 = 178 — the exact count of `(a)` classes this item was raised about.** So ISO's manual has
been using one symbol for two structurally different regimes, and the register entry could not tell
them apart **because it only ever compared the manual against the rate, and never against the text
table sitting in the same directory.** The products side declares a fourth value, `Not Applicable`,
on 474 of 1,188.

**The engine reads none of it.** `grep -rn "ELP" gl_engine/*.py` returns nothing; the only mention in
our Python is a docstring in `scripts/variants.py:426`. So the correct behaviour per regime is now
*specified* rather than guessed: leave `Rate/Loss Cost Applies` alone · use the published ELP for
`Industry` instead of the zero we currently multiply by · **refer** on `Company` and take a carrier
rate as input. **`Company` is where B1's `1.0` is load-bearing** — a company rate is exactly the
carrier input B1 defers, so those classes stay unrateable-without-input by design and the engine's job
is to say so out loud.

**What must be measured before any of it is written:** the three-way split is from **one state, one
edition**. Generalising from that is the precise error OI-68 and OI-04 both were, and this project has
paid for it twice. All 51 jurisdictions and multiple editions first, read-only.

### A label that pointed at nothing

The as-of selector had been marked *"blocked on D-1"* since 2026-08-17. **`D-1` is defined nowhere in
this repository** — two occurrences, both uses, no entry. It is not `D1` in `WHAT-I-NEED-FROM-YOU.md`
(minimum premium amounts, needs a carrier) and not the closed defect `D1` in this log (the OI-88
decision). **The blocker was real; only the identifier was invented.** The row now names the gap. The
transferable point is that **a code with no entry is worse than prose**, because prose cannot look
authoritative while being empty — which is the counting discipline of the register turned on the
planning documents, where it had not been applied.

### ▶ Next session

**Reordered by today's decisions.** The TX refused-payload call moves up — it now serves OI-94 *and*
C2's evidence pack. Then: **measure the ELP regime split across all 51** (read-only, no calls, and the
prerequisite for the highest-value backlog item there now is), then L2 live on one class, then L5/L6.
The effective-date variable and the three ELP regimes are the two new build items, both medium, both
in `START-HERE-TOMORROW.md` §5 with their unmeasured preconditions named. Entry 32's two follow-ons
are unchanged and still small.

---

## Entry 35 — OI-95 measured across the whole corpus: the pattern holds, with one narrow real
## exception, and the drift itself turned out to matter for how the fix must be built.

- **Date:** 2026-08-19
- **Directed:** "Let's do OI-95." Per the backlog's own precondition ("measure across all 51 first")
  and yesterday's habit-9 finding, treated as a go for the read-only measurement, not the engine
  fix — no code path in `gl_engine` was touched.
- **Built:** `scripts/erc/53_oi95_elp_regimes.py`, matching the shape of `45_oi88_blast_radius.py` —
  measures and decides nothing. Enumerates every package `find_packages()` returns (575, across 52
  jurisdictions including the countrywide parent), reads `PremOpsELPText`/`PremOpsELP` and
  `ProdsCompldOpsELPText`/`ProdsCompldOpsELPFactor` where both exist, and checks three things: does
  the zero/nonzero pairing hold everywhere, does a class's category stay stable across editions of
  the same jurisdiction, and are there categories in the data the Texas reading never saw.

### What held

**The pairing is essentially exact.** Prem/ops side: **zero exceptions across 668,303 rows** —
`Rate/Loss Cost Applies` and `Company` are zero every time, `Industry` is non-zero every time, in
every jurisdiction and every edition that files the table (52 of 52). This is the number OI-95's
build-work reclassification was resting on, and it holds at full scale, not just in one state's one
edition.

### What didn't, narrowly, and what it might mean

**28 rows out of the same 668,303, on the products-completed-operations side only, and they reduce to
exactly two class codes** — `10012` (rate `0.078`) and `10027` (rate `0.043`) — carrying a non-zero
ELP while labelled `Rate/Loss Cost Applies`, and **only in Idaho and Virginia**, stable across every
edition either files. Small, real, and not explained by anything read so far — logged rather than
folded silently into the branch logic the fix will need. Also: **`Not Applicable` exists on the
prem/ops side too**, not only products as the Texas reading suggested — 2 rows total, both zero,
negligible in size but worth the branch logic covering all four observed values rather than three.

### The finding that changes the shape of the fix, not whether to build it

**The classification is not static across time**, and the drift is large: 1,171 prem/ops classes and
4,110 products classes change category across editions of the same jurisdiction. **But it is not
jurisdiction noise — the same roughly two dozen class codes move in lockstep in nearly every state**,
which is the exact shape habit 7 names: what looks like a jurisdiction split is really a calendar
split, in this case ISO adding or withdrawing a published rate for specific classes at a point in
time, countrywide. **Consequence for the build:** the ELP tables have to be read from whichever
edition the engine resolves for the rating's as-of date, the same as every other loss-cost lookup —
never cached from one snapshot taken during design. The engine already does this for every other
rate table, so this is a confirmed constraint, not a new one, but it would have been a real defect if
the fix had read the tables once and reused the classification.

### ▶ Next session

**OI-95 is now measured, not inferred, and ready to build on your go.** The two-class exception (ID,
VA, `10012`/`10027`) is worth a closer read before the fix ships, if only to decide whether the
branch logic should special-case it or simply use whichever value each table actually publishes
regardless of the category label — the safer default, and probably the right one, since it makes the
exception irrelevant rather than requiring it to be understood first. Unchanged otherwise: the TX
refused-payload call, the effective-date variable, L2 live, L5/L6.
