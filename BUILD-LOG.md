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
| **2** | The interpreter | ⏸ awaiting sign-off |
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

## Entry 2 — Stage 1 built: load and resolve. **NEXT SESSION STARTS HERE.**

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
