# From Planning to Build

**Skeleton written 2026-08-12, before stage 1. Filled in as each stage completes.**

This document exists because of a decision made on 2026-08-12: **write it alongside the build, not
after it.** Written retrospectively it becomes a tidy story in which every piece of analysis turned
out to be essential. Written alongside, it records the thing that is actually useful — **where three
weeks of analysis was load-bearing, and where we would have got there anyway.**

That distinction is the whole value of this file for a future line of business. A team pointing this
method at Commercial Property or Business Owners needs to know which of the twenty-odd analysis
steps to repeat and which to skip.

---

## How to use this file

Each stage has three sections, filled at three different times:

| Section | Written | Purpose |
|---|---|---|
| **Expected to inherit** | **before** the stage starts | What the analysis is supposed to have already answered. Written blind, so it cannot be retro-fitted |
| **Actually used** | **after** the stage completes | What was really consulted, and what turned out to be missing |
| **Verdict** | after | Was the analysis load-bearing, partially useful, or would we have got there anyway? |

**The `Expected` column must never be edited after the stage begins.** Its value is entirely in
having been wrong sometimes.

---

## What the build inherits, in total

Recorded once, here, so each stage can point at it rather than restate it.

| Asset | Size | Produced by |
|---|---|---|
| Coverage walkthroughs | **11**, one per rating item | Steps 27–47 |
| Non-negotiables | **N1–N18**, each measured | Throughout |
| Referral register | **28 conditions, 13 decisions** | Step 48–49 |
| Escalations | **18 raised, 8 dissolved on reading a file** | Throughout |
| Open items | **67 tracked** | Throughout |
| Priced example policies | **54**, covering 50 jurisdictions | Pre-existing; *found* Step 49 |
| Analysis scripts | **42 ERC + 15 PDF**, all re-runnable | Steps 6–49 |
| Manual corpus, searchable | **1,122 documents, 5 families** | Steps 42, 46 |
| Expert agents | **2**, 19 and 88 smoke checks | Steps 12–24 |
| **The instruction-language measurement** | **58 node types, 809,088 occurrences, top 20 = 94.1%** | Step 50 — *the number that chose the architecture* |

---

## Stage 1 — Load and resolve

### Expected to inherit
*Written 2026-08-12, before any code.*

- **Package discovery and identity** should be solved. `scripts/erc/32_asof_recount.py` already
  discovers all 61 packages, reads identity from the XSD namespace rather than the folder name (N6),
  and resolves editions as of a date (N4). We expect to port this almost unchanged.
- **The declared-parent rule** should be solved — take the parent the state names, never the newest
  (N5). We expect the three live parents and California's lone `V02` to fall out without special
  handling.
- **Table loading** should be mostly solved: five table shapes, typed from the definitions.
- **The load-time assertions** should be a transcription job — §10 of the build plan lists them and
  each was measured when it was written.
- **We expect one surprise**: the loss-cost tables have different column shapes by state, and it is
  not yet certain that all five shapes were enumerated rather than the four we happened to look at.

### Actually used
*Written 2026-08-12, after stage 1.*

| Expected | What happened |
|---|---|
| Port `32_asof_recount.py` almost unchanged | **Held.** Discovery, the namespace regexes and the as-of rule transferred directly. The engine version is faster — explicit directory iteration instead of `os.walk` over 87,000 files — but the logic is the same |
| Declared parents fall out without special handling | **Held exactly.** 3 live parents, CA alone on `V02`, 5 states on something older than the newest. No special cases |
| Table loading mostly solved | **Half held.** Typing from the definitions was straightforward. **Split loss-cost families were not solved at all** and the analysis's own description of them was too narrow |
| Load-time assertions are a transcription job | **Did not hold, and this was the useful failure.** Two of the twelve had a *condition narrower than their name* — see below |
| One surprise expected: loss-cost column shapes | **Wrong surprise.** Column shapes loaded without incident. The surprise was that in **CA, NJ and OH the base table is absent from the state package entirely**, so the base name resolves upward to a header-only countrywide table |

**What was genuinely missing from three weeks of analysis, and had to be measured during the build:**

1. **The full loss-cost suffix vocabulary.** The analysis named four states and the `<ST>Terr<nnn>`
   pattern. The corpus has **75 distinct suffixes in two classes** — territory slices, and
   `OverOneHundred`/`OverOneMillion` high-limit tables that are *not* slices at all.
2. **Zero and one as factor sentinels.** N13 catalogues eight meanings of zero, but not *"a zero in
   an ILF factor column"* — 60 cells — and nothing anywhere anticipated **`1.00` as a placeholder**,
   which is the more dangerous of the two. Raised as E20 / OI-68.
3. **The ILF limit-column alphabet.** `'1,000,000 CSL'`, `'500,000 BI'`, bare `'300,000'` — and the
   fact that two columns containing the word `Limit` are not limits.

### Verdict

**Load-bearing.** Stage 1 took one session because the analysis had already answered the questions
that would otherwise have taken days: which package is authoritative, what a parent is, why "latest"
is a trap, and why an empty table is a statement. **N4, N5, N6 and N7 went in as code with no
rediscovery at all.**

**But the analysis under-specified exactly where it had already been surprised once.** OI-20 was
*known* — it is a filed open item — and the build still found the real version of it wider than
recorded. **A finding that arrives as an anecdote (`four states do this`) does not survive into code;
only an enumerated population does.** That is the sharpest transferable lesson from this stage.

**Would we have got there anyway?** The mechanics, yes — slowly. The *doctrine*, no. Nothing in the
ERC files tells a reader that an empty table means "not offered here" rather than "inherit". A team
starting from the corpus would have written the fallback, and it would have looked like it worked.

---

## Stage 2 — The interpreter

### Expected to inherit
*Written 2026-08-12, before any code.*

- **The node vocabulary is known and sized** — 58 types, 54 executable, top 20 covering 94.1%. This
  is the single measurement that chose the architecture, and without it the fork would have been
  decided on taste.
- **We expect the walkthroughs to serve as acceptance tests without modification.** Each states the
  rule order and arithmetic for one coverage; if the interpreter is right, they should pass with no
  coverage-specific code. **This is the strongest claim in this document and the one most likely to
  be wrong.**
- **The evaluation contract is NOT inherited.** E3 closed with *"the evaluation contract, only if
  interpreting"* — it was never written. We expect this to be the largest single piece of new
  specification work in the whole build.
- **We expect the 14 rare node types to cost more than their frequency suggests**, and `GetList`
  (2 occurrences in 809,088) to be doing something unusual in exactly one place.
- **We expect N2's parent dispatch to be the hardest single mechanism** — 4,598 call-super rules
  that must not recurse.

### Actually used
*Written 2026-08-13, after stage 2.*

| Expected | What happened |
|---|---|
| 58 types, 54 executable, top 20 = 94.1% | **Right, and it was the one thing that held.** Re-measured from the XML: 58 elements, 4 structural, **54 language nodes**, top 20 = **94.03%**. The architecture decision stands |
| The 14 rare types will cost more than their frequency suggests | **The count was wrong — it is 9, not 14** — and the prediction was untestable because none of them was reached. `GetList` (2 occurrences) is a `Constant` and a `Break`; nothing unusual, and nothing exercises it |
| The walkthroughs serve as acceptance tests without modification | **Not used at all.** This was flagged as *"the strongest claim in this document and the one most likely to be wrong"*, and it was not so much wrong as bypassed: acceptance came from the corpus census, the refusal set and **real ISO payloads**. The claim remains untested |
| The evaluation contract is not inherited | **Right, and it was the largest single piece of new work**, exactly as predicted |
| N2's parent dispatch will be the hardest mechanism | **Wrong.** It was one boolean on the frame. It took an afternoon and never misbehaved |

**What actually cost the time was not on the list at all:**

1. **The entry point.** Every prior census walked `Rule` elements and so could not see the `Default`
   block. The analysis had the entry point wrong, and nothing in the *Expected* column suspected it.
2. **`ForEach` in a value position yields a collection.** Not anticipated; it made `Sum` silently
   total one iteration of five.
3. **Positional predicates** — `[1]`, 18,796 occurrences. Not anticipated, and it cost exactly 18 on
   the golden case with no error anywhere.
4. **The `Value` nullability clause**, which the contract got wrong from the attribute's name and
   only a real payload falsified.

### Verdict
**Load-bearing for the decision, not for the semantics.**

The node census chose the architecture and was worth every hour — **without it the interpret-vs-
transliterate fork would have been decided on taste.** Nothing else the analysis produced told us
what the language *means*.

**The semantics had to be measured from the XML, and three of the four hardest problems were
invisible to every prior analysis because each had asked a slightly wrong question** — walk `Rule`
elements, count direct parents, read attributes by name. **The pattern is consistent enough to be a
rule for the next line of business: an analysis phase can size a language reliably and cannot
specify it.** Budget for the specification separately, and write it against the source.

---

## Stage 3 — Kernel and the two modes

### Expected to inherit

- **The referral register should be usable as data**, not as prose — that is why it was emitted as
  JSON with 13 decisions attached.
- **Evaluation order across coverage groups** should be specified by E18 and the terrorism gate:
  coverages are not independent, terrorism runs last.
- **The propagation rule** (`D01`) and **disposition monotonicity** (`D02`) should need no further
  thought.
- **We expect the golden case to pass early**, because 334 and 336 are the two most thoroughly
  derived coverages and the arithmetic has already been re-derived in `Decimal` by
  `tests/verify_golden.py`.

### Actually used
*Written 2026-08-13, after stage 3.*

| Expected | What happened |
|---|---|
| The referral register is usable as data, not prose | **True and insufficient.** It loads as JSON and all 28 entries are addressable — but the *conditions* are prose written for a human, and the engine can currently detect **1 of 28**. Emitting it as JSON solved the wrong half of the problem |
| E18 and the terrorism gate specify evaluation order across coverage groups | **Not needed.** ISO's own rules encode the order, and the architecture executes them. Ordering never became a decision we had to make |
| D01 propagation and D02 monotonicity need no further thought | **Right.** Implemented straight from the decisions, no re-litigation |
| The golden case passes early, because 334 and 336 are the most thoroughly derived coverages | **Wrong, and instructively so.** It did not pass early — it passed *last*. It was the instrument that found all three stage-3 defects, and the depth of the prior derivation is exactly why: because 7,839 was known to the penny, a result of **7,821** was a defect rather than a plausible answer |

### Verdict
**Half the inherited analysis was made moot by the architecture, and the half that mattered mattered
enormously.**

The coverage-order work (E18, terrorism-last) was **genuinely not needed** — a consequence of
choosing to execute ISO's rules rather than re-implement them, and a real saving to record for the
next line of business: *if you interpret, you do not need to derive the control flow.*

But **the golden case earned the entire analysis phase back on its own.** Three defects — a silent
one-of-five sum, an unparsed path predicate, and missing rule inheritance — produced complete,
plausible premiums. **Two of the three were invisible without an oracle**, and the oracle existed
only because Steps 27–47 had derived 976 and 6,845 and 7,839 independently, in advance, to the
penny.

> **That is the strongest argument in this document for doing the analysis at all**, and it is not
> the argument we expected to be making. The value was not that the analysis told the build what to
> do. It was that the analysis could tell the build it was **wrong**.

---

## Stage 4 — Schemas and payloads

### Expected to inherit

- **The 53 RAaS payloads** give the submission shape; we expect to derive rather than design it.
- **The input surface measurement** (1,906 fields) should bound what the schema must express.
- **Four states need a county or place field** (E8) and **Hawaii cannot be rated** — both known.
- **We expect the state table-shape differences to be handled by the interpreter without special
  cases**, and if they are not, that is a stage 2 defect surfacing late.

### Actually used
*Written 2026-08-13, after stage 4.*

| Expected | What happened |
|---|---|
| The 53 RAaS payloads give the submission shape; derive rather than design | **Neither.** **ISO *files* the schema** — `Form Fields/Fields.FormField.csv` declares every field per jurisdiction with its control, requiredness, default, bounds, condition and **the domain table naming its legal values**. The payloads were used only as territory sources and as subjects to validate. **The decisive asset was in the corpus the whole time and was not on this list** |
| The 1,906-field input surface bounds what the schema must express | **A different measurement, both true.** 1,906 counts the *rating* input surface; the form schema is **1,381 countrywide fields over 429 tables**, plus a state delta, giving **1,252–1,321 per jurisdiction**. Neither bounds the other |
| Four states need a county or place field (E8) | **The count is right and the mechanism was not.** There is no county field anywhere — a first search for one matched `PremiumPlaceHolder`. **Exactly four (CA, FL, NY, TX) declare `TerrorismTerritory` against a state-specific `TerrorismTerritoryCode`**, while **11 others derive it from a ZIP** and NY alone adds a Manhattan flag. E8's *"by county or place"* is better read as *"by a code that cannot be derived"* |
| Hawaii cannot be rated | **Right.** Not in the corpus; 51 jurisdictions and no HI |
| State table-shape differences handled by the interpreter without special cases, or it is a late stage-2 defect | **Right, and it is the quiet success of this stage.** All **51 jurisdictions rate the same risk** with no jurisdiction-specific code anywhere — including the four sliced loss-cost states. **No stage-2 defect surfaced late** |

### Verdict
**Partially load-bearing, and the most useful thing was not inherited at all.**

The analysis correctly predicted **what the hard parts would be** — the four special jurisdictions,
Hawaii's absence, and that the interpreter should absorb state shape differences — and the last of
those is a real prediction that held under test.

But **the schema itself was never going to come from the payloads**, and the plan assumed it would.
It is filed content, sitting in a directory no analysis step had opened. **That is the third time
this project has found the answer already in the corpus** (the `Default` block, the response header
naming the edition, and now `Form Fields`) — each time in a file that no one had a reason to open
until something needed it.

> **The lesson for the next line of business is specific: before deriving anything from examples,
> enumerate the directories in the package and ask what each one is for.** Three of this build's
> largest shortcuts were sitting in one.

---

## Stage 5 — The enum workbook

### Expected to inherit

- **417 countrywide domain tables plus state overrides** should supply the legal values directly.
- **We expect the hard part not to be extraction but scope** — which of 1,906 fields a payload
  actually needs — and we expect the 53 real submissions to answer that better than the corpus does.

### Actually used
*To be written after stage 5.*

### Verdict
*To be written after stage 5.*

---

## Stage 6 — The UI

### Expected to inherit

- **Nothing from the analysis.** This is the one stage we expect to inherit no domain knowledge at
  all — it should be a thin shell over an engine that already works.
- **We expect it to prove the separation** rather than build anything: if the UI needs the engine to
  change, the engine's interface was wrong.

### Actually used
*To be written after stage 6.*

### Verdict
*To be written after stage 6.*

---

## For a future line of business

*To be written at the end, from the six verdicts above. The question it must answer:*

> **Of the twenty-odd analysis steps that preceded this build, which would you repeat for Commercial
> Property, which would you do differently, and which would you skip?**

Two candidate answers are already visible and are recorded here so they can be tested rather than
invented later:

1. **The instruction-language measurement should come first, not last.** It was taken on the final
   day of analysis and it chose the architecture. Taken on day one it would have shaped every
   walkthrough — because if the rules are going to be executed rather than transliterated, a
   walkthrough's job is to be an *acceptance test*, not a *specification*, and that changes how you
   write it.
2. **The counting discipline paid for itself and should be day-one policy.** *Every count is "n of
   N", with N enumerated from the corpus.* It was adopted on 2026-08-11 after five wrong figures in
   a single day, and it caught defects in four completed walkthroughs within hours of being
   automated. **Sixteen corrections are recorded across this project and almost all are the same
   mistake: something measured in one place and stated about everything.**
