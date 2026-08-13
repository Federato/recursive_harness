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
| **3** | Kernel and the two modes | ✅ **built 2026-08-13** — 31/31 acceptance. **Oklahoma golden case reproduces 7,839 exactly**; 50 of 50 payloads rate, 22 match ISO to the penny |
| **4** | Schemas and payloads | — |
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

## Entry 5 — Stage 3 built: the kernel. A premium comes out. **NEXT SESSION STARTS HERE.**

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
