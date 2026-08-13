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
| **2** | The interpreter | 🔵 **started 2026-08-13** on branch `stage2-interpreter`. The evaluation contract is written; no interpreter code yet |
| **3** | Kernel and the two modes | — |
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

## Entry 3 — Stage 2 opened: the evaluation contract. **NEXT SESSION STARTS HERE.**

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
