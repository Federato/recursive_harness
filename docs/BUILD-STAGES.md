# The Build — staged plan, for sign-off

**Written 2026-08-12. No code exists. Nothing below is built until you approve the stage.**

This is the plan for the engine itself. It follows the twelve directives of 2026-08-12 and the
architecture decided with them: **execute ISO's filed rules rather than re-implement them**, two
behavioural modes, all sublines in scope, tested first on Premises/Operations and
Products/Completed Operations.

---

## 0. What we already have, and what it is worth

Three weeks of analysis is not preamble to this build — it is most of its specification.

| Asset | What the build uses it for |
|---|---|
| **11 coverage walkthroughs** | **Acceptance tests**, not code. Each states the rule order, the arithmetic and the deviations, so the interpreter can be checked against a known-correct reading |
| **18 non-negotiables (N1–N18)** | Load-time assertions and design constraints, each already measured |
| **The referral register** — 28 conditions, 13 decisions | `escalate/` is populated on day one rather than discovered during build |
| **54 priced example policies** | Real answers to rate against, covering 50 jurisdictions |
| **42 analysis scripts** | Package discovery, edition resolution and table loading already exist and are proven over 61 packages |
| **Two expert agents** | Available to review the engine's output against the manual and the data |

**The single most important number for this build:** ERC's instruction language is **58 node types
(54 executable) over 809,088 occurrences**, and **the top 20 cover 94.1%**. That is what makes the
interpreter approach cheaper than transliteration, and it was measurable only because the corpus had
already been mapped.

---

## Stage 1 — Load and resolve  ✅ BUILT 2026-08-12

**Deliverable:** `gl_engine/erc/` and `gl_engine/resolve/`. Given a state and an effective date,
return the exact rule set and tables that apply.

- Package discovery and identity from the XSD namespace, never the folder name (N6)
- Edition selection **as of a date**, and the declared countrywide parent — not the newest (N4, N5)
- Table loading, typed from the table definitions, with the five table shapes
- **The load-time assertions** already specified in §10 of the build plan, as hard failures

**How you check it:** point it at all 51 jurisdictions for a date and confirm it resolves the parents
we measured — including the three live parents and California's lone `V02`. It should refuse a date
before 2022-09-01 rather than silently falling back.

**Why first:** everything else is downstream, and it is the part most thoroughly proven by existing
scripts.

**Built and verified.** `gl_engine/` — 1,814 lines, 11 modules, no third-party dependency.
`tests/verify_stage1.py` **18/18**; `python -m gl_engine.cli check 20260811 --deep` **13/13**. All
51 jurisdictions resolve, each against its own declared parent; 3 countrywide editions live today
and 3 at the cliff; a pre-2022-09-01 date is refused. **Four corrections and two new escalations
along the way — E20/OI-68 (`1.00` as a sentinel) and OI-69 (the split loss-cost defect is wider than
recorded).** See [`BUILD-LOG.md`](../BUILD-LOG.md) Entry 2.

---

## Stage 2 — The interpreter  ✅ BUILT 2026-08-13

**Deliverable:** `gl_engine/interp/`. Executes ERC rules.

This is the heart of the build and the only genuinely new engineering.

- **The evaluation contract**, written down first: what each node means, child evaluation order, how
  nulls propagate, what `FirstNonNull` does when everything is null. E3's residual, now live
- **~20 node types** to start — `Sequence`, `If`/`Test`/`Then`/`Else`, `Choose`/`When`/`Otherwise`,
  `Equal`/`NotEqual`, `And`/`Or`, `IsNull`/`IsNotNull`, `Constant`, `Value`, `FirstValue`,
  `FirstNonNull`, `Lookup`/`Keys`, `RunRule`, `ForEach`, `Product`/`Sum`
- **DataDef addressing** — the `../../../` paths that reach across coverage groups (E18)
- **`RunRule` dispatch**, including parent dispatch that must not recurse (N2, 4,598 call-super rules)
- **Write-once semantics as a property of the resolved edition** — 213 guarded values in the newer
  parent, 3 in California's (OI-58)
- **`Decimal` throughout, never float** (N10), with the five rounding precisions including the 8dp
  one found on 12 August

**How you check it:** run it against the eleven walkthroughs. Each states its expected rule order and
arithmetic; the interpreter should reproduce them without any coverage-specific code.

**The honest risk:** the long tail. 14 node types appear fewer than 500 times each and one appears
twice. They are cheap individually but they are where surprises live.

**Built and verified.** `gl_engine/interp/` — 6 modules, no third-party dependency. All **54**
language nodes have an evaluator, and `tests/verify_interp.py` reads the list of 54 from the corpus
census rather than from the test, so a 55th node in a future filing fails the suite. **52/52.**

**The long-tail risk did not materialise; the risk was elsewhere.** The tail is **9** nodes, not 14,
and none was reached. What actually cost the time was the **entry point** (the `Default` block, which
every prior census was structurally unable to see), **`ForEach` yielding a collection**, and
**positional predicates**. See [`14-EVALUATION-CONTRACT.md`](../rating-engine/14-EVALUATION-CONTRACT.md)
and `BUILD-LOG.md` Entries 3 and 4.

---

## Stage 3 — The kernel and the two modes  ✅ COMPLETE 2026-08-13

**Deliverable:** `gl_engine/rating/kernel.py`, `escalate/`, `trace/`. A submission goes in, a premium
and its factors come out.

- Submission → resolved packages → execute → premium
- **Evaluation order across coverage groups**, because coverages are not independent (E18) and
  terrorism runs last
- **The referral register wired in**, with `strict-erc` and `underwriting` modes
- **Resolvable referrals** — a referral names the value it needs and rating resumes when supplied
- **Dispositions are monotonic** — a recalculation never cancels a referral
- **The trace**: every number carries where it came from, and records referrals raised *and* resolved

**How you check it:** rate Oklahoma's golden case and reproduce `976 + 6,845 + 18 = 7,839` exactly.

**Built and verified.** `gl_engine/rating/` — `submission.py` and `kernel.py`. **31/31.**

**The golden case reproduces exactly**, and every one of the **83 policy-level numbers ISO
published** agrees field by field — a total can be right for the wrong reasons, so the total alone
was never going to be the test.

**Breadth, against ISO's own 50 priced examples: 50 of 50 rate end to end, 22 agree to the penny.**
Both figures are frozen in `verify_stage3.py` group F as a **ratchet, not a target**.
`python scripts/rate_all_payloads.py` is the report. **Every one of the 28 differences is our defect
until proven otherwise** — that is what strict mode is for, and it is the next work.

**Both owed items are now done.**

**Banded and interpolated lookups.** The population was measured before it was built
(`scripts/erc/46_banded_lookups.py`): **11 table names, every one reachable, each with exactly one
key range**, two boundary types, and **two interpolated tables**, both size-of-risk relativity, both
`Linear`. Boundaries and linear interpolation are pinned by `verify_interp` group F.

**The referral register.** All **28** entries now carry an explicit disposition — **9 DETECTED,
4 NOT_REFERRAL, 1 CONFIG, 14 PENDING** — and `Kernel.unenforced` names the pending ones
individually. On the 50 payloads the two modes return **identical premiums**, detectors fire on
**exactly one** submission, and that one is real: Alaska's attorney's-fee limit is below the subline
limit, the endorsement prices at **−70**, and **ISO's own response carries the same −70 and an
error message we reproduce verbatim**.

---

## Stage 4 — Schemas and payloads  ✅ COMPLETE 2026-08-13

**Deliverable:** `gl_engine/schema/`, and `Engine_Payloads/` with one sample per jurisdiction.

- A **baseline submission schema per state**, supporting multi-state, multi-location, multi-subline
  and multi-coverage in one request
- **Sample payloads built from the 53 RAaS inputs**, same class code and exposure everywhere so
  state differences are visible and attributable
- **Four states carry an extra field** — California, Florida, New York and Texas resolve territory
  by county or place (E8)
- **51 jurisdictions**, including DC and Puerto Rico. **Hawaii is not in the corpus and cannot be
  rated**

**A wrinkle worth knowing before it surprises you:** the loss-cost tables have different *shapes* by
state — California and New Jersey put the territory in the filename with three columns, Ohio and
Texas use four columns, New York uses its own column names. **The interpreter handles this by
construction**, which makes stage 4 an early proof that stage 2 was built right.

**Built and verified. 23/23.**

**The schema is read, not designed.** `Form Fields/Fields.FormField.csv` is ISO's own declaration of
every field per jurisdiction — control, requiredness, default, bounds, condition, and the domain
table naming its legal values. Countrywide declares **1,381 fields over 429 tables**; each
jurisdiction resolves to **1,252–1,321**. `gl_engine/schema/` loads it; `validate()` reports findings
rather than raising, and **ISO's own 50 submissions validate with zero errors**.

**One sample submission per jurisdiction, the same risk in every one** — class `50017`, £5m gross
sales, 1M/2M CSL — so a price difference is attributable to the jurisdiction and nothing else.
**All 51 rate end to end**, and the spread on identical risk is **GA 6,845 to NY 12,141**.
Puerto Rico has no ISO payload of its own, so **its sample is built from ISO's domain tables** rather
than invented. `python scripts/build_sample_payloads.py`.

**E8 restated from measurement.** There is no county field. **Exactly four jurisdictions — CA, FL,
NY, TX — code terrorism territory explicitly (`TerrorismTerritoryCode`)**; 11 others derive it from
a ZIP, and NY alone adds a Manhattan flag. The four are warned about when the field is absent,
because it cannot be derived and an unmatched one refers (R22).

**Hawaii is confirmed absent from the corpus** and stated as a test rather than a footnote.

---

## Stage 5 — The enum workbook  ✅ COMPLETE 2026-08-13

**Deliverable:** an Excel workbook listing every field a payload can carry and its legal values.

Sourced from ISO's own domain tables — 417 countrywide plus state overrides — so *"how do I express
a limit"* is answered by ISO's filing rather than by us. Cross-referenced against the **1,906 input
fields** measured in the corpus, and against the 53 real submissions, so the workbook covers what is
actually used rather than everything conceivable.

**Built and verified. 18/18.** `GL-Submission-Fields.xlsx`, seven sheets, written with the
**standard library only** — the engine has no third-party dependency and a deliverable should not
introduce one (`scripts/xlsx.py`).

**The plan predicted the hard part correctly, and it was scope.** ISO declares **1,259 fields**
countrywide; the 50 real submissions between them use **77 — 6.1%** — of which **41 are used by all
50**, and a single submission carries **43–54**. The `Used in practice` sheet is ordered by how often
a field is actually sent, so the workbook opens on what matters rather than on an alphabet.

**Every column names the ISO file it came from**, and the `Read me` sheet lists them: fields and
requiredness from `Form Fields`, legal values from `Domain Tables` (`DataValue`), declared
dependencies from `Form Related Fields`, required-to-rate from `Ratebook Columns`, and — found by
Rule #1 during this stage — **data types and 2,489 class codes from ISO's own `DOC` workbook**.

**A large domain is summarised, never silently truncated:** `ZipCode` at 765 values is a lookup, not
a choice, and the sheet says so rather than listing it.

The workbook is **gitignored with the rest of the ISO-derived content**; the generator is committed
and rebuilds it in seconds.

---

## Stage 6 — The UI  ✅ COMPLETE 2026-08-13

**Deliverable:** a separate application file. Paste a payload, rate it, read the result.

- Every rating factor, in order, with its source
- **Premiums per coverage and per subline, in their own arrays**
- Referrals shown as referrals, with what would clear them
- Mode switch between `strict-erc` and `underwriting`

**Strictly separate from the engine.** The engine must never import the UI, and must be fully usable
from a notebook — which is the secondary integration you asked for, and comes free if the separation
holds.

**Built and verified. 23/23.** `app.py` — one file, **standard library only**, no framework and no
build step. `python app.py`, then open `http://127.0.0.1:8765`.

**The separation held.** No engine change was needed to build it: the whole UI is assembled from
`premium`, `by_coverage`, `referrals`, `messages`, `trace`, `tree` and `packages`. The test suite
checks this by **reading the engine's source** for an import of the UI rather than trusting that
nobody added one, and confirms `Kernel().rate(path).premium` works with the UI never imported.

**But asking for one item on this list found a real engine defect.** *Premiums per subline* needs the
subline statistical code ISO writes on each coverage — and we were writing **none of the statistical
codes**, because `ErcSetStatisticalCodes` is guarded by `Exist ancestor::MasterGLCW/Policy` and the
**`ancestor::` axis was not implemented**. An unimplemented axis matches nothing, the guard reads
false, and the block was skipped **with the premium still exactly right**. Measured before fixing:
**942 paths, one axis, 34 forms, no other axis anywhere in the corpus.** With it implemented, every
statistical code matches ISO's golden output — **0 mismatches**.

> **A deliverable that renders everything finds things a deliverable that asserts something specific
> never will.** Four stages of tests and 49 of 49 exact premiums had not noticed, because every check
> so far compared numbers and a statistical code is a string.

---

## After the six stages — the phases that follow

The six stages above build **the ISO engine**. Three phases follow, in this order and for a reason.

### Phase 2 — Proof against RAaS

Run the same submission through the engine in `strict-erc` mode and through ISO's own service, and
compare. **Any difference is our defect until proven otherwise.** This is the whole point of strict
mode existing.

Doable partly offline first: **54 ISO-priced example policies covering 50 jurisdictions** are already
on disk, which is enough to find systemic errors before the connection exists.

### Phase 3 — The harness closes the loop

The comparison run continuously and automatically, with the two expert agents adjudicating each
difference against the manual and the data, and findings fed back as fixes. **Detection first,
diagnosis second, correction third** — see the plain-English walkthrough for what each of those
honestly means and where the limits are.

### Phase 4 — Company deviations

**Only once the ISO baseline is trusted.** The reason is the oracle: RAaS rates ISO content, so the
moment company content is layered on, **no external service can confirm the answer**. Deviating from
an unproven foundation makes every difference unattributable.

**But the design anticipates them from stage 2**, under three constraints now recorded in build plan
§5 as **C1 (ordered layer chain), C2 (ISO's `@parent` keeps ISO's meaning), and C3 (behaviour and
content are independent axes)**. All three are cheap now and invasive later.

---

## Running throughout — the two diaries

**`BUILD-LOG.md`** — the build as it happens, in the style of `PROCESS_LOG.md` but about code only:
what was built, what broke, what was corrected. **Corrections are kept, not tidied away** — they are
the raw material for the self-correcting harness.

**`FROM-PLANNING-TO-BUILD.md`** — **skeleton written before stage 1, filled in as we go.** For each
stage: what it *expected* to inherit from the analysis, and what it *actually* used. Written
afterwards this becomes a tidy story; written alongside it records where three weeks of analysis was
genuinely load-bearing and where we would have got there anyway. That distinction is the whole value
for a future line of business.

---

## Not now, by instruction

**RAaS integration.** The end goal is to diff against ISO's service as the gold standard and feed
the difference into a self-correcting loop. **Nothing is built toward it yet** — but the 54 priced
examples let us do most of that offline first, and `strict-erc` mode exists precisely so the
comparison is meaningful when it comes.

**Company deviations.** Phase 4, after the ISO baseline is proven. **Not built, but designed for** —
constraints C1, C2 and C3 in build plan §5 apply from stage 2 onward, because retrofitting a layer
chain into a written interpreter is expensive and retrofitting `@parent` semantics is dangerous.

---

## What sign-off means

Each stage is presented before the next begins, exactly as the analysis gates were: **what it does,
what it was checked against, and what it cannot yet do.** You run tests, corrections get recorded,
and we move on.

**Stage 1 is built. Awaiting your approval of stage 2.**
