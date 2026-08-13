# Where we paused — 12 August 2026

**Plain English. No insurance or programming knowledge assumed.**

This is the whole of what happened on the day the first working software appeared, written so it can
be read cold. Everything here is also recorded in the formal documents; this one exists so you do not
have to go looking.

---

## The short version

**The three weeks of analysis finished, the big architectural question was settled by counting rather
than by opinion, and the first of six stages of the actual engine was built and tested.**

Building it immediately found two things about ISO's own content that three weeks of careful reading
had not — including the answer to a question we had written down as unanswerable.

---

## 1. What we decided, and why it was not a matter of taste

The open question was: **should the engine run ISO's rules, or rewrite them?**

ISO publishes its pricing rules as machine-readable files. You can either **build a machine that
follows those instructions**, or **read them and re-write what they say in code**. The second is the
normal way to build a rating engine and it is what most carriers do.

We settled it by counting. **ISO's instructions turn out to be written in a small language: 58 kinds
of instruction, used 809,088 times, and the twenty most common cover 94% of all uses.**

That number decides it. Build the language once — about twenty instructions for a working version,
all 54 for a complete one — and **every state, every coverage and every future ISO filing comes
free**. The alternative was hand-writing 4,461 rules per rulebook, plus 345 more for California
because it is on a different rulebook, and doing the whole thing again every time ISO files an
update.

**That measurement was only possible because the corpus had already been mapped.** It is the single
clearest return on the analysis phase — and, as noted at the end, it should have been taken on day
one rather than the last day.

---

## 2. What was built

**A component that answers one question: given a state and a date, which rulebook applies?**

It is 1,814 lines of Python in `gl_engine/`, split across eleven files, using nothing but Python
itself. It reads all 567 of ISO's packages in under a second, and **every number it hands back is
tagged with the exact ISO file it came from.**

### Why that unglamorous piece went first

Because **almost every way this project could produce a confidently wrong price starts there.**

Pick the wrong edition of the rules. Pick the wrong national rulebook underneath a state. Read an
empty table as "zero" instead of "we do not sell that here". Each of those produces a **complete,
plausible, wrong premium with nothing at all to flag it** — which is far more dangerous than a crash.

So stage 1 is mostly a machine for refusing to guess. Three examples of it refusing:

**It will not rate before September 2022.** The files do not cover every state that far back. It
could give you an answer for the states it does cover — and that answer would look exactly like a
complete one. So it stops instead.

**California is on an older national rulebook than everyone else, and is the only state on it.** The
engine takes the rulebook each state *names for itself*, never the newest one available. Five states
today would otherwise be priced against rules they never adopted.

**An empty rate table is an answer, not a gap.** If a table has no rows in it, that means "this is
not sold here". The engine will show you the empty table if you ask to look, and will refuse to
calculate a price with it.

### How we know it works

| | |
|---|---|
| Acceptance tests | **20 of 20** |
| Load-time safety checks | **13 of 13**, at two different dates |
| Everything built before today | unchanged — six suites, all green |

The second date matters. **1 April 2027 is the morning 43 states change classification basis at
once.** An engine that quietly caches "the current rules" breaks that day. Running the full check at
that date, not just today's, is what turned up the findings below.

---

## 3. What building it found that reading it could not

Six things needed fixing during the build. **Two of them changed what we know about ISO's content**,
and one closes a question we had filed as unanswerable.

### Finding 1 — Some states hide their rates, and our own test said everything was fine

In **California, New Jersey and Ohio**, the main premises/operations rate table **is not in the
state's package at all.** The rates live in ten to fifteen separate per-territory files with
different names.

An engine that reads the obvious table name gets **zero rows and no error message**, and produces a
finished price from nothing.

We already knew a version of this — it was a filed open item. **The real shape was worse than
recorded, and the first check written to catch it passed anyway** — because it only counted the cases
it could already see. **A test that certifies a false claim is worse than no test at all.**

Fixed by listing **all 75 naming variations in the corpus** rather than the handful anyone had
noticed. That also separated two things that had been confused: some suffixed tables are
per-territory slices, and others (`OverOneHundred`, `OverOneMillion`) are entirely separate tables
for high limits. **66,573 rows of rates recovered** across the four affected states.

### Finding 2 — ISO is withdrawing a whole rating method, and now we can prove it

"Size of risk" is a method that adjusts the price for how big the account is.

We had already recorded that the 2027 national rulebook **empties the size-of-risk tables**, and we
had written down honestly that the files could not tell us whether that was a **deliberate
withdrawal** or an **incomplete filing**. At the time, no state had adopted that rulebook, so there
was nothing more to look at.

At the 2027 date, 43 states have adopted it. Counting the states rather than the rulebook:

| | today | 1 April 2027 |
|---|---|---|
| States carrying premises/operations size-of-risk rates | **35 of 51** | **2 of 51** |

The two survivors are both among the eight states still on an **older** rulebook. **Every single one
of the 43 that adopt the 2027 rulebook empties its own tables as well.** Ohio files 11,880 rows
across ten territory files today, and the same ten files with **zero rows** at the cliff.

**Forty-nine states and the national layer emptying the same thing in step is a coordinated
withdrawal. An incomplete filing does not coordinate.**

**The answer was in *who adopts the rulebook*, not in the rulebook** — which is precisely the question
the engine exists to ask, and one that reading the files could never have answered.

### Finding 3 — A placeholder that looks like a real number

Texas's elevator contractor table shows a factor of **exactly 1.00 on 26 of its 30 rows**, and a real
1.69 to 1.72 on the other four. Taken at face value, **a $20 million limit costs the same as a
$50,000 one**, while a $3 million limit costs 72% more than either.

This project had already catalogued **eight different meanings of zero** in these files — sometimes
zero is a price, more often it means "refer to an underwriter" or "not eligible". **Nobody thought to
ask what *one* might mean.** The reason is instructive: **nothing multiplies when you are only
reading.** You only notice a suspicious 1.00 when something is about to multiply by it.

**Multiply by a fake zero and you get a $0 premium that somebody questions. Multiply by a fake one
and you get a wrong premium that nobody questions.** The second is the worse failure.

It appears in **all seven Texas editions from 2021 through the 2027 filing** — six years of
consecutive filings, which is not a typo. So it most likely means "no increased-limit charge applies
at these combinations". But ISO's files give no way to be certain, so **the engine refers it to a
human rather than guessing.** Recorded as escalation E20.

> **This is the point of the whole exercise, arriving early.** The end goal is a system that checks
> itself against ISO's live service and learns from the differences. Finding 3 is a smaller version
> of exactly that: **running the content found a class of defect that reading it could not.**

---

## 4. A mistake I made, and what it cost

While writing the testing guide, I **typed an expected result into the file before running the
command.** I wrote "13 of 13 at the 2027 date". The real answer was 11 of 13.

It was wrong in the direction that looks fine — **a page full of green numbers, one of which was
fiction.** Anyone reading that page would have had no reason to doubt it.

Running it properly is what produced Findings 2 and 3 above. Checking the *rest* of the page then
turned up four more commands that would not have worked as written.

**Every command in `TESTING.md` has now actually been executed, and every stated output is what it
really produced.** That is now a standing rule for that file.

I also had to reverse something I told you earlier the same day: I said the Texas 1.00 was "almost
certainly a placeholder". Once I checked all seven editions instead of just the current one, that
became the *less* likely reading. **The engine's behaviour does not change — it still refers — but the
reason on file is now the right one.**

---

## 5. The pattern behind almost every mistake in this project

Sixteen corrections are now recorded across the whole project, and **nearly all of them are the same
mistake: something measured in one place, then stated about everything.**

- Measured the manual corpus with one PDF tool, concluded 187 documents had no text. They all did.
- Measured payloads in one folder, concluded the project had one priced example. It has 54.
- Measured one rulebook edition, concluded a 1.00 was probably a typo. All seven editions have it.
- Counted split rate tables only where the base table was visible, concluded there was one such case.
  There are six.

The discipline adopted for this is simple and it keeps earning its place: **every count is stated as
"n of N", and N must be enumerated from the source rather than assumed.**

Today added a second rule, from the two checks that were written wrong:

> **When a new safety check passes on the first run, suspect it.** Twice now a check's *condition* has
> been narrower than its *name*, and the second one passed while blind. **Confirm a check can fail
> before believing it can pass.**

---

## 6. Where things stand

| | |
|---|---|
| **Analysis** | Complete — all 14 rating items, plus three owed side-pieces |
| **Decisions** | All 13 taken with you. Nothing waiting on the business |
| **Architecture** | Decided: run ISO's rules, do not rewrite them |
| **Stage 1 — which rulebook applies** | **Built and tested** |
| Stage 2 — the interpreter | Awaiting your sign-off |
| Stage 3 — producing a premium | Not started |
| Stage 4 — state submission formats | Not started |
| Stage 5 — the field/value workbook | Not started |
| Stage 6 — a simple interface | Not started |
| **ISO's live service (RAaS)** | **Not connected, by your instruction.** The 54 priced examples serve until it is |

**No ISO rule is executed yet.** That is stage 2, and it is the only genuinely new engineering in the
whole build. The largest piece of it — writing down exactly what each of ISO's 54 instructions means
— was deliberately deferred during analysis on the grounds that it was only needed if we chose to run
the rules rather than rewrite them. We chose to run them, so it is now due.

---

## 7. Where to look

| If you want | Read |
|---|---|
| **To run anything yourself** | [`../TESTING.md`](../TESTING.md) — every command, phase by phase, each one verified |
| The plan in plain English | [`THE-PLAN-IN-PLAIN-ENGLISH.html`](THE-PLAN-IN-PLAIN-ENGLISH.html) |
| The full status document | [`PRD-GL-RATING-ENGINE.md`](PRD-GL-RATING-ENGINE.md) — §0 is today |
| The build diary | [`../BUILD-LOG.md`](../BUILD-LOG.md) — what was built, what broke, what it revealed |
| Whether the analysis paid off | [`FROM-PLANNING-TO-BUILD.md`](FROM-PLANNING-TO-BUILD.md) — written *before* each stage, so it can be wrong |
| The six stages | [`BUILD-STAGES.md`](BUILD-STAGES.md) |
| Everything unresolved | [`OPEN-ITEMS.md`](OPEN-ITEMS.md) — 69 items |

**Everything in one page:** `GL-RATING-ENGINE-DOCS.html`, 22 tabs.

---

## 8. The one decision waiting on you

**Whether to start stage 2 — the interpreter.**

Nothing else is blocked, and nothing else needs your input to proceed.
