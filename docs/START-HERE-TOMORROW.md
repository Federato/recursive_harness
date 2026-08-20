# Start here tomorrow — Tuesday 18 August 2026

**Yesterday closed six defects, raised one question for you, and built the QA programme.** Nothing is
blocked. This is what to pick up, in the order I would pick it up.

The full diary is [`BUILD-LOG.md`](../BUILD-LOG.md) Entry 28. The plain-English version of what the
day taught is [`what-the-harness-taught-us_20260817.html`](what-the-harness-taught-us_20260817.html).

---

> ## Written later the same day — a new page exists
>
> **18 August: the layered test programme and its page were built.** A four-layer ladder — smoke,
> classification, limits, deductibles — with a `/tests` page to run it from, an allowance per run
> that thins configurations and never states, a daily ticker instead of a budget gate, and one
> standalone HTML file per run. The design and what measuring the data changed about it are in
> [`UI-STRATEGY.md`](UI-STRATEGY.md); the diary is [`BUILD-LOG.md`](../BUILD-LOG.md) **Entry 29**.
>
> **The gap list below still stands** — it covers the *existing* tester and QA tab, which were left
> untouched deliberately. One item did move: **the aggregate limit is now a real axis**, which was
> not a gap anyone had listed and turned out to mean half the increased-limit key had never been
> tested.

---

> ## Written even later the same day — the `/tests` page grew a lot, and Section 2 below is answered
>
> **Four more entries landed on top of Entry 29**, all in `ui/`, `scripts/` and `notebooks/` —
> nothing in the priority list below (§3–§8) was touched, and nothing in it changed as a result.
>
> - **Entry 30** — the run-page matrix from Entry 29 got a hover panel and click-to-filter; one test
>   (`verify_layers.py` E3) had been written before that existed and needed loosening, not the
>   feature.
> - **Entry 31** — **§2's question below is answered.** The harness got its own notebook set,
>   `notebooks/harness/00-index.ipynb` onward, seven notebooks — the recommendation in §2
>   ("a second set") is what got built.
> - **Entry 32** — the `/tests` page gained an **Aggregate** table, a **verdict card per layer**, a
>   **trend chart**, and the Result card gained the outcome bar and coverage map — all reusing
>   `ui/charts.py` chart functions the QA tab had and `/tests` never called. Two real bugs caught by
>   testing against an empty store rather than assumed away: an offline (never-compared) scenario
>   defaulting to a blue "agrees" dot, and `runfile.entries()` not carrying enough data for the Run
>   files table's own outcome dot to be exact rather than approximated.
> - **Entry 33** — **a run can be reviewed now, without an API key.** `/review/<run-file>`: a
>   mechanical pattern match for free (reuses `qa_review.classify`, `probe_no_op`'s INERT VALUE, and
>   dedup against prior reviews), a markdown brief for what it can't explain, and a place to paste
>   back what a person said. Planned with a wireframe and named risks *before* any code, per explicit
>   instruction. One scope cut from the wireframe on purpose: named defects (OI-88, OI-89) are not
>   auto-detected, because that would mean inventing detection logic from memory rather than a
>   re-derivable check — the same mistake OI-91's false count already taught this project not to make.
>
> **§7 below ("how far are we from a UI?") is the one section whose facts changed** — the "what
> exists today" table didn't have a row for the aggregate/verdict/review work because it didn't exist
> yet. See the amended row inline.
>
> Full diary: `BUILD-LOG.md` Entries 30–33. Design write-ups: `UI-STRATEGY.md` §3 (aggregate,
> verdict, trend, the review page) and §4 (the matrix).

---

> ## Written 19 August — the five open asks are all answered, and one of them was checkable
>
> **No code was written; this was a backlog-only instruction.** Four decisions and one direction:
>
> - **B1 — the LCM stays at `1.0`**, because what we are testing is RAaS against our engine and both
>   sides are loss costs. **Not a client application.** An invented multiplier would have to be
>   divided back out of every comparison.
> - **C1 — not sending it.** Closed by decision. Pacing rules unchanged.
> - **C2 — held for more testing of our own.** This **raises the priority of the TX refused-payload
>   call** in §3, because it is the cheapest way to confirm ISO's *reason* in a second state.
> - **A3 — ISO rates future effective dates**, so the 2027 tier has an oracle, and the effective date
>   becomes a **test variable** rather than a mode. **The as-of selector in §1 is unblocked.**
> - **OI-95 — the direction named a table, and the table is real.** `PremOpsELPText.RateTable.csv`
>   declares `Rate/Loss Cost Applies` / `Industry` / `Company` per class per state, and in Texas
>   **68 Company + 110 Industry = the exact 178 `(a)` classes the item was raised about.** So one
>   manual symbol has been hiding two different regimes, and **the engine reads neither table.**
>   OI-95 is no longer a judgement call — it is build work with a declared source.
>
> **§5 is rewritten** (it was *"waiting on you"*; nothing is now), **§1's as-of row is unblocked**, and
> **§6 gained two items**. Also recorded: **`D-1` was a label pointing at nothing** — see the note in
> §1. Registers updated: [`WHAT-I-NEED-FROM-YOU.md`](WHAT-I-NEED-FROM-YOU.md),
> [`OPEN-ITEMS.md`](OPEN-ITEMS.md) OI-95, [`BUILD-LOG.md`](../BUILD-LOG.md) Entry 34.

---

# The two things you named, first

## 1 · Finish the UI the proposal promised

**The proposal has six wireframes. All six exist. Twelve of the eighteen named features are built,
six are not** — measured against the wireframes rather than remembered.

### What is missing, with sizes

| | Gap | Size | Gated on |
|---|---|---|---|
| **W1** | **"Run the harness review afterwards"** checkbox — pass 3 should run when a tier finishes, not only when someone types a command | **Small** | nothing |
| **W1** | **As-of date selector** | **Small to wire, and now unblocked** | ~~Blocked on D-1.~~ **The blocker is real and the label was not — see the note below.** The engine has no effective-date axis: the options offered come from one date while rating uses the payload's, so the control would offer a choice that does not work. **2026-08-19 turned this into build work:** ISO rates future effective dates, and the direction given is *"we should have an effective-date variable."* Fix the axis as a variable and the selector is the same fix's user interface. §5 |
| **W1** | **Schedule** — nightly T0, weekly T1 | **Medium** | nothing, but it needs a scheduler and a decision about unattended live calls |
| **W2** | **Pause / stop a running tier** | **Small–medium** | needs a cancel flag the worker checks between scenarios |
| **W3** | **"What changed since last run"** — new problems, fixed problems, newly covered ground | **Small** | nothing; both rollups already exist |
| **W6** | **Reviewer verdicts recorded** — the wireframe shows *"confirmed by 3 of 3 reviewers"* | **Medium** | **A decision.** The agents cannot be invoked from the server, so a verdict has to be pasted back. That makes W6 a *workflow*, not a *reader*, and needs somewhere to store them |

> **A label that pointed at nothing — recorded 2026-08-19.** The as-of row above cited **"D-1"** as
> its blocker, and **`D-1` is not defined anywhere in this repository.** It appears in exactly two
> places, both of them uses: this table, and one back-reference in `UI-STRATEGY.md`. It is **not**
> `D1` in `WHAT-I-NEED-FROM-YOU.md` (that is *minimum premium amounts*, needing a carrier) and it is
> **not** the old defect `D1` in the build log (the OI-88 null-in-`FirstNonNull` decision, closed
> 2026-08-17). The underlying blocker is real and is listed in the PRD as *"no effective-date axis"*;
> only the identifier was invented. **The lesson is the register's own rule turned on this document:
> a code that has no entry is worse than prose, because prose cannot look authoritative while being
> empty.** The row now names the gap instead of pointing at a number.

### Where I would start, and the one decision to take first

**Take the W6 decision before writing anything.** Today's W6 is a **reader** — it shows what is worth
attacking and says plainly that dispatch happens by hand. The wireframe implies a **workflow** where
verdicts come back and are stored. Both are defensible; they are different products:

- **Reader** *(what exists)* — honest, no state to maintain, and it never claims a review happened
  that did not.
- **Workflow** — more useful over time, and it needs a store for verdicts, a way to mark a finding
  resolved, and care that a stale verdict is never shown as current.

**Then, in this order:** *"what changed since last run"* (small, and the most-read screen) → *"run the
review afterwards"* (small, closes the loop) → pause/stop → schedule. ~~**Leave the as-of selector
until D-1 is fixed.**~~ **Amended 2026-08-19: the as-of selector now has a place in the queue** — it
ships with the effective-date variable (§5), because they are one fix seen from two sides.

---

## 2 · Put the harness into the notebook set — ✅ done, Entry 31

**Built as `notebooks/harness/`, the recommendation below.** Seven notebooks —
`01-variants` … `07-layers` — plus its own `00-index.ipynb`, same six-cell shape as the engine set,
`tests/verify_notebooks.py` now finds both sets (28/28). What follows is left as the record of the
decision, not an open question anymore.

**Twenty notebooks exist, one per file in `gl_engine/`, and `tests/verify_notebooks.py` executes
every cell of every one.** The new work is in `scripts/`, which the set does not currently cover.

### The design question to settle first

The set's premise is *"one per Python file in `gl_engine/`"* — the **engine**. The harness is a
different thing: `qa.py`, `qa_review.py`, `runstore.py`, `variants.py`, `sweep.py`, `charts.py`.
Three options:

| | | |
|---|---|---|
| **Extend the set** | 20 → ~26, and the index's premise changes from *the engine* to *the engine and the harness* | Simplest to find; blurs a distinction the project has been careful about |
| **A second set** | `notebooks/harness/` with its own index | Keeps *"the engine contains no rating concepts"* clean, which is the point notebook 00 opens with |
| **Only the QA pair** | `qa.py` and `qa_review.py` as two additions | Smallest; leaves `variants`/`sweep` undocumented, and those are the ones people actually need to read |

**My recommendation: a second set.** The engine notebooks make a specific claim — *search it for
"deductible" and you get one result, and it isn't arithmetic* — and mixing the harness in weakens it.
A harness set can make its own claim: **every defect found today came from something in these files.**

### What each notebook has to do

Same six cells as the existing twenty, because the twentieth reads like the first: what the file is
for · its public surface, generated from the module so it cannot drift · the smallest thing that
works · the interesting case · what it refuses · try it yourself.

**Two constraints that will bite:**

1. **`verify_notebooks.py` runs every cell and fails on any exception.** A notebook that calls ISO,
   or that needs a run in the store, will fail on a clean machine. **Everything must work offline
   and with an empty `results/`.**
2. **Outputs are stripped before commit** and `.gitattributes` enforces it, because a run notebook
   holds ISO's licensed values in its JSON.

### Candidates, in the order I would write them

| | Why it earns a notebook |
|---|---|
| `variants.py` | The 20 controls and where their values come from. **The most-read file in the harness** |
| `qa.py` | Tiers, the pairwise generator, the budget. Explains why 22 scenarios and not 600 |
| `qa_review.py` | The three verdicts, and why the pass reads ISO's CSVs rather than asking our own code |
| `sweep.py` | One configuration across 51, and the four outcomes |
| `runstore.py` | Why the store is append-only, and what a run record holds |
| `charts.py` | Why the map is a tile grid and Hawaii is drawn blank |

---

# 3 · The one call that settles the most

**`results/refused-payloads/TX-714439816b85/request.json`**

Send it. That single call settles **36 payloads across 4 states**, and it closes the half of OI-94
that is currently *unproven*.

**Why it matters.** We refuse this submission before calling ISO. That is correct and it saves money
— but it means **we have never actually asked ISO what it would do with it.** Yesterday's adversarial
review found that the evidence I had cited for "ISO refuses this too" was **captured in Georgia, not
Texas, and describes a different lookup.** So the claim is an inference.

**The three possible answers, and what each means:**

| ISO's response | What it means |
|---|---|
| **It rates it** | Our refusal is wrong. That is OI-88's shape again, and it is a defect |
| **It refuses, naming `PremOpsSizeOfRiskLossCost`** | Confirmed — cause and all. OI-94 closes properly |
| **It refuses, naming something else** | We agree on the outcome, not the reason. Exactly what the review found |

`what-to-ask.md` sits beside it. The payload validates against ISO's own schema with **zero errors**,
so it posts unchanged.

---

# 4 · The day's 60 calls, in order

The standing budget is **60 a day** (your decision A6), two sittings, business hours.

| Order | Calls | What | Why this order |
|---|---|---|---|
| **1** | 1 | **The TX refused payload above** | Cheapest, settles the most |
| **2** | 1 | **The 2027 probe** — will ISO rate a future effective date? | Decides whether the 2027 tier has an oracle at all, or is a self-consistency exercise. **Building it before knowing would be guessing** |
| **3** | ~48 | **`python scripts/qa.py --tier T1 --juris CA --juris NY --juris TX --juris FL`** | The mechanism matrix in four structurally different states. Deductible ordering × ILF keying — **the two top-ranked failure modes, both invisible one variable at a time**. First live exercise of multi-class |
| **4** | ~10 | Whatever step 3 turns up | Leave room. A clean run is not the expected outcome |

**Run offline first, always:** `python scripts/qa.py --tier T1 --offline` costs nothing, takes three
minutes, and removes build errors and refusals from the live set before a call is spent.

---

# 5 · ~~Waiting on you — five things~~ ✅ **All five answered, 2026-08-19. Nothing is waiting on you.**

| | What you decided | What it means for the work |
|---|---|---|
| **B1** | **Hold the LCM at `1.0`.** We are testing ISO's RAaS against our engine, both sides are loss costs, and **this is not a client application** | The comparison stays exact — an invented multiplier would have to be divided back out of every result. Premium-level testing is now a **decision to defer**, not a gap. Revisit when there is a client app or a carrier filing, and answer the *shape* question then |
| **C1** | **Not sending it. Our usage is fine** | Closed by decision, not parked. Pacing rules stay as they are — serial, business hours, inside the standing budget — because they were adopted to keep the traffic unremarkable and that reasoning is unchanged |
| **C2** | **More testing first, then report** | The finding stands; its shape does not. **This raises the priority of the TX refused-payload call** (§3), which is the cheapest way to confirm ISO's *reason* in a second state. I bring C2 back drafted with the evidence attached rather than leaving it a standing ask. Three things the testing must settle are listed in `WHAT-I-NEED-FROM-YOU.md` C2 |
| **OI-95** | **There is a table for this.** Loss cost / company / industry — **company is A-rated, a refer-to-company, and takes a carrier rate; industry means an ELP is being used** | **Checked the same day, and it is exactly right.** `PremOpsELPText.RateTable.csv` declares one of three values per class per state: `Rate/Loss Cost Applies` 1,010 · `Industry` 110 · `Company` 68 in Texas — and **68 + 110 = 178, the exact count of `(a)` classes this item was raised about.** So the manual's one symbol has been hiding two different regimes. **The engine reads none of it** — `grep ELP gl_engine/*.py` returns nothing. **No longer a judgement call; it is a build item with a declared source** |
| **A3** | **ISO will rate a future effective date** — so put it in the test cases: **we should have an effective-date variable** | The 2027 tier has an oracle, so the *whether* question is closed. And the shape is better than a second tier: **one control, set per scenario**, carried into the payload and the as-of resolution together so they cannot disagree. **This unblocks the as-of date selector** in §1 |

**Nothing was built for any of this — 2026-08-19 was an explicit backlog-only instruction.** The
detail sits in [`WHAT-I-NEED-FROM-YOU.md`](WHAT-I-NEED-FROM-YOU.md) and, for OI-95, in
[`OPEN-ITEMS.md`](OPEN-ITEMS.md).

### What the five answers add to the build queue

| | | Size |
|---|---|---|
| **An effective-date variable** | A control in `variants.py`, an axis in the layer ladder, and **one date threaded through both the payload and the as-of resolution** — the disagreement between those two is the whole defect. Unblocks the as-of selector and makes the 2027 cliff testable by ordinary scenarios | **Medium** |
| **The three ELP regimes** | Read `*ELPText`, branch three ways: leave `Rate/Loss Cost Applies` alone · use the published ELP for `Industry` instead of the zero we multiply by today · **refer** on `Company`, and accept a carrier rate as the input | **Medium**, and see the four unmeasured things below |
| **Measure the ELP split properly first** | The three-way count is from **one state, one edition**. Generalising that is the exact error OI-68 and OI-04 both were. Needs all 51 and multiple editions before any branch is written | **Small, read-only** |
| **Ask ISO one question about `Industry`** | Does the live service use the published ELP, or return zero like we do? Directly testable, one call, and it decides whether the `Industry` branch is a fix or a deviation | **One call** |
| **The C2 evidence pack** | The TX call, a full 400 body from more than one state, and whether the gap is the class or the state | **A few calls** |

---

# 6 · What is left in the backlog

## The one known defect

**OI-89 — schedule rating can be requested, accepted, and silently not applied.** Not our bug: ISO
only applies it when the account's claims experience is credible enough. We now know it moves the
premium in exactly **three states — FL, NY, RI — and does nothing in the other 48.**
**Unblocked yesterday:** you approved synthetic loss histories spanning the credibility threshold, so
this can be exercised whenever it comes up the list.

## The proving work — the big one

**Test more kinds of business, not more states.** Our coverage measure reads **1 of 19**. Every test
still prices broadly one kind of risk. **Geography has stopped teaching us anything** — the last four
states we added found nothing. Business type has not started.

Blocking it: **7 of 11 sublines have no starting payload.** Decision A1 lets us model them on ISO's
own examples, which covers four of the seven; **Pollution, Electronic Data, Storage Tanks and Special
Protective have no example at all** and must be built from the declaration.

## Also open, in rough order of value

| | |
|---|---|
| **The three ELP regimes (OI-95)** | **New 2026-08-19, and the highest-value one on this table. Measured across the whole corpus the same day** — `scripts/erc/53_oi95_elp_regimes.py`, 575 packages, 52 jurisdictions, zero calls. **The pattern holds almost everywhere**: prem/ops side, zero exceptions across 668,303 rows. **One narrow real exception** on the products side — two class codes, `10012` and `10027`, in Idaho and Virginia only, carry a non-zero ELP despite being labelled the zero-expected category — flagged, not explained yet. **The classification drifts across editions** (the same ~2 dozen classes move in lockstep in nearly every state), which is a calendar effect, not a jurisdiction one, and means the fix must read the resolved edition live rather than cache one snapshot — which the engine already does for every other rate table. **Ready to build** once you say go |
| **An effective-date variable** | **New 2026-08-19.** One control threaded through payload *and* as-of resolution. Unblocks the as-of selector and makes the 2027 cliff — 43 jurisdictions changing basis in one morning — testable by ordinary scenarios rather than a parallel tier |
| **Widen breadth live** | 11 jurisdictions done, 40 remain. **Consider varying class family instead** — the discovery rate per state is falling |
| **Referral list** | Ours is 28 hand-derived conditions; **ISO ships a spreadsheet listing 838.** Five we carry but do not detect could produce a wrong number |
| **Form attachment** | Which endorsements land on the policy. **Nothing tests this at all.** 510 ISO sample submissions are the material |
| **Carrier deviations** | The commercial unlock, and deliberately last: **once carrier content is layered on, no external service can confirm the answer** |
| **Dependent-domain validation** | 61 of 90 fields fall back to a broader legal list. Politeness, not correctness |
| **Commercial Property** | Reading only, by your decision. Next step: what a CF *state* package changes against the national one |

## Raised while building, deferred deliberately

| | |
|---|---|
| **UA-1** | Per-location variation. A second location is a **deep copy differing only by territory** — class and exposure cannot vary per location |
| **UA-2** | ISO's **three** territory-assignment rules. We only ever exercise one |
| **UA-3** | `Each` and `Units` premium bases — **no divisor at all**, the sharpest test of the per-basis divisor |
| **Two code findings** | The null-loss-cost refusal walks the whole tree with evidence for only part of it; and it fires **before** the referral register, so the precise pre-written diagnosis for that exact case can never appear. Both message-quality, neither premium-affecting |
| **Housekeeping** | `verify_contract_figures` reads cached output instead of re-measuring — **a test that cannot fail when it should.** Second stale-cache problem in two days |

---

# 7 · How far are we from a UI?

**Further than "there is no UI" and closer than "it is ready." There is a working one — the honest
question is what kind you mean.**

## What exists today, and works

| | |
|---|---|
| `/` | Rate one submission. Every factor in the order used, with the ISO file each came from. Referrals. Per-coverage breakdown |
| `/tester` | **19 controls**, every option read live from ISO's own tables per state. Run across all 51. Our premium, ISO's premium, the difference |
| **QA tab** | Whole test tiers behind a button, **with the cost shown before you press it** and a budget that refuses to overspend |
| `/tests` | **The layered programme** (Entry 29) — four layers, an allowance, pause/resume/stop, one standalone HTML file per run. Now also an **Aggregate** table, a **verdict card per layer**, a **trend chart**, all-time-summed and click-to-filter (Entry 32) |
| `/review/<run>` | **A run can be reviewed without an API key** (Entry 33) — a mechanical pattern match for free, a markdown brief for what it can't explain, a place to paste back what a person said |
| **Charts** | Agreement over time · coverage grid · premium response curves · **a US map** · a one-screen verdict — used on both the QA tab and, as of Entry 32, `/tests` |
| **History** | Every run kept permanently, with a defect register that tracks first-seen and last-seen |

**That is a real internal tool and it is being used.** The 17th's work was driven through it; the
18th added a second page (`/tests`) on top, then a third (`/review`) on top of that.

## What it is not

**It is an engineer's instrument, not a product.** Specifically:

| Gap | Size |
|---|---|
| **No accounts, no login, no permissions.** It runs on your machine and assumes one trusted user | Medium |
| **No concurrency.** One rating at a time, one background job. Two people would collide | Medium |
| **No underwriter's workflow** — no submission list, no saving a quote, no comparing two quotes side by side, no audit trail per policy | **Large** |
| **No carrier deviations**, so it can only ever show ISO's answer, not yours | **Large — and gated on the proving work** |
| **Styling is functional.** It looks like what it is | Small |
| **Runs from a script**, not deployed anywhere | Medium |

## The honest answer

**For internal QA and demonstration: it is there now.** Nothing more is needed to run the programme,
show a carrier how a premium was built, or prove agreement with ISO.

**For an underwriter to use daily: the UI is not the constraint.** The constraint is **carrier
deviations** — until the engine can price *your* rates rather than ISO's, a beautiful interface shows
the wrong number beautifully. That work is deliberately last, for the reason above: the moment it
lands, **the independent check that found every defect so far stops working.**

**So the sequencing I would argue for:** finish the proving work → build deviations → then invest in
the interface. Building the interface first would mean polishing a tool whose underlying answer is
not yet the one a carrier needs.

---

# 8 · If you only do three things tomorrow

1. **Send `results/refused-payloads/TX-714439816b85/request.json`.** One call, settles 36 payloads
   and closes an open question about our own fix. **Now doubly worth it** — C2's report waits on
   exactly this evidence.
2. ~~**Email ISO** (C1 and C2 together).~~ **Superseded 2026-08-19.** C1 is declined and C2 is held
   for more testing. **Replaced by: measure the ELP regime split across all 51 jurisdictions** —
   read-only, no calls, and it is the prerequisite for the highest-value item now on the backlog.
3. **Run `python scripts/qa.py --tier T1 --offline`.** Three minutes, free, and it tells you what
   tomorrow's live calls should be aimed at.
