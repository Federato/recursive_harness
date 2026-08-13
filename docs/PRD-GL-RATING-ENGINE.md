# General Liability Rating Engine — Product Requirements & Progress

**A plain-language document.** What we are building, why it is harder than it sounds, every step
we have taken to get here, what we found along the way, and what remains.

**Last updated 2026-08-12.** If you read this before, **§0 below is the summary of what has
changed** — the analysis is finished, the architecture is decided, and **the first stage of the
engine is built, tested and running.**

No prior knowledge of insurance rating or of this project is assumed. Technical detail lives in
the documents referenced at the end.

---

## 0. What changed today

**Updated 2026-08-12, second update of the day.** The morning's entry recorded that the analysis was
complete and the build specified. **By the end of the day the first stage of the engine exists, runs,
and is tested.** This is the first day of this project on which working software was produced.

### The analysis is finished

All fourteen rating items in the build order are walked through, the last three owed side-pieces are
done, and every outstanding question has an answer. **Thirteen decisions were taken with you, one at
a time.** Nothing is waiting on the business.

### The architecture was decided on a measurement, not a preference

The open question was whether the engine should **run ISO's filed rules** or **rewrite them in
Python**. It was settled by counting: ISO's rules are written in a small instruction language of
**58 kinds of instruction over 809,088 uses, and the twenty commonest cover 94%**.

**So we implement that language once, and every state, every coverage and every future ISO filing
comes free.** The alternative was hand-writing 4,461 rules per rulebook — plus 345 more for
California, which is on a different one — and doing it again each time ISO files. That number was
only measurable because the corpus had already been mapped, which is the clearest single return on
the three weeks of analysis.

### Stage 1 of the engine is built

**`gl_engine/` — 1,814 lines of Python, eleven modules, no third-party libraries.** It answers one
question: *given a state and a date, which rulebook applies?* It reads all 567 ISO packages in under
a second, and every number it returns is tagged with the ISO file it came from.

That sounds modest and it is not. **Almost every way this project could produce a confidently wrong
price starts here** — wrong edition, wrong national rulebook underneath a state, or an empty table
read as "zero" instead of "not sold here". Each produces a complete, plausible, wrong premium with
nothing to flag it. Stage 1 is mostly a machine for refusing to guess:

* **Ask for a date before September 2022** and it stops. The files do not cover every state that far
  back, and a partial answer would look like a real one.
* **California uses an older national rulebook than everyone else** and is the only state on it. The
  engine takes the parent each state names *for itself*, never the newest. **Five states today**
  would otherwise be rated against rules they never adopted.
* **An empty table is an answer, not a gap.** If a rate table has no rows, that means *"we do not
  sell this here"*. The engine will show it to you, and refuses to price with it.

**Verified: 20 of 20 acceptance cases and 13 of 13 load-time safety checks, at two different dates**
— today, and the 2027-04-01 cliff where 43 states change classification basis on one morning. Every
test built before today still passes unchanged.

### Building it found things reading it could not

**Six corrections during the build, two of which change what we know about ISO's content.**

**1. Some states hide their loss costs, and our own test said everything was fine.**
In California, New Jersey and Ohio the main premises/operations rate table **is not in the state's
package at all** — the rates sit in ten to fifteen separate per-territory files. Reading the obvious
name returns zero rows and no error. A version of this was already a filed open item; **the real
shape was wider than recorded, and the first check written for it passed — because it counted only
the cases it could already see.** A green test certifying a false claim is worse than no test. Fixed
by listing all **75** naming variants in the corpus instead of the handful we had noticed. **66,573
rows of rates recovered** across the four states.

**2. ISO is withdrawing size-of-risk rating, and this closes an open question.**
We had recorded that the 2027 national edition empties the size-of-risk tables, and that the files
could not distinguish a **withdrawal** from an **incomplete filing** — noting that no state had
adopted that edition yet. At the cliff, 43 do:

| | today | 2027-04-01 |
|---|---|---|
| states carrying premises/operations size-of-risk rates | **35 of 51** | **2 of 51** |

Both survivors are among the eight still on an older national rulebook, and **every one of the 43
adopting the 2027 edition empties its own tables too**. Ohio files 11,880 rows across ten territory
files today, and the same ten files with **zero rows** at the cliff. **Forty-nine states and the
national layer emptying the same thing in step is a coordinated withdrawal; an incomplete filing does
not coordinate.**

**The answer was in *who adopts the edition*** — a question the engine can ask and three weeks of
reading could not.

**3. A placeholder that looks like a real number.** Texas's elevator contractor table shows a factor
of exactly **1.00 on 26 of its 30 rows**, and a genuine 1.69–1.72 on the other four — so a $20
million limit prices identically to a $50,000 one. The project had already catalogued **eight
different meanings of zero** in these files. **Nobody thought to ask what *one* might mean, because
nothing multiplies when you are only reading.** Multiply by a fake zero and you get a $0 premium
somebody questions; multiply by a fake one and you get a wrong premium nobody questions. It appears
in **all seven Texas editions from 2021 to the 2027 filing**, so it is far more likely to be
deliberate than a typo — but ISO gives no way to be sure, so it refers to a human rather than being
guessed at.

**That the engine found a class of defect the reading could not is the premise of the self-correcting
harness, arriving a stage earlier than planned.**

### One honest process note

While writing the testing guide I **typed an expected result into the file before running the
command.** It was wrong — and wrong in the direction that looks fine: a page of green numbers, one of
which was fiction. Running it for real produced both of the findings above. **Every command in that
guide has now been executed and its stated output is what it actually produced.** That is a standing
rule for the file.

### Where the numbers stand

| | Yesterday | Today |
|---|---|---|
| Coverages walked through | 7 of 14 | **all 14 in the build order, plus the three owed side-pieces** |
| Engine code | none | **stage 1 of 6 built, 1,814 lines** |
| Engine tests | none | **20 acceptance cases, 13 safety checks, green at two dates** |
| Manual documents held | 975 ingested | **1,122 — all of them** |
| Priced example policies known | 1 | **54** |
| Questions for the business | 17 raised | **20 raised, 13 answered, 1 closed by the build** |
| Tracked open items | 50 | **69** |

### What happens next

**Stage 2 — the interpreter — on your sign-off.** It is the heart of the build and the only genuinely
new engineering: the piece that executes ISO's rules. Then the kernel and the two modes, the state
submission formats, the enum workbook, and a simple interface. Six stages, each shown to you before
the next begins.

**Full detail:** [`../TESTING.md`](../TESTING.md) for every command · [`../BUILD-LOG.md`](../BUILD-LOG.md)
for the build diary · [`BUILD-STAGES.md`](BUILD-STAGES.md) for the staged plan.

---

## 1. What we are building, in short

A piece of software that takes a description of a business — what it does, where it is, how big
it is, how much coverage it wants — and returns the **price** for a General Liability insurance
policy, along with a full explanation of how that price was reached.

Today, producing that price requires a person to read a large printed manual and apply dozens of
rules by hand. We are automating it.

**Two things make it more than a calculator.** First, the price must be *defensible* — an
insurance regulator can ask why a policy cost what it cost, and the answer has to point at a
specific page of a filed document. Second, the rules change constantly, and a policy written last
year must still be priceable under last year's rules, not today's.

---

## 2. Why this is hard

The pricing rules come from **ISO** (Insurance Services Office), an organisation that publishes
standardised insurance manuals that most US insurers license and build on. For General Liability
specifically:

**It is not one manual, it is three layers.** There is a national rulebook, a separate set of
exception pages for each of 51 US jurisdictions, and a separate publication of the actual
*prices* for each jurisdiction. All three are revised on different schedules. To price one
policy you need the right version of all three, as of the right date.

**The national layer has the method but almost none of the money.** This surprised us. The
national rulebook explains *how* to calculate, and then says, in its own words, that the actual
factors *"are displayed in the state exceptions."* We later confirmed this in the data: in the
national package, the five key pricing tables contain **zero rows**. Every real number comes from
a state.

**Blank does not mean zero.** The price tables are grids of business types against prices, and
more than a third of the cells contain something other than a number — a dash meaning *"we do not
offer this coverage for this type of business"*, or a marker meaning *"refer this to an
underwriter."* Software that reads those as `0.00` will hand out free policies and sell coverage
the manual explicitly declines.

**It is changing right now.** ISO is part-way through revising the list of business
classifications. Some jurisdictions have adopted it, some have not. There is no single correct
national list today.

---

## 3. How we got here

Sixteen steps, grouped into five stages.

### Stage one — read the rulebooks (Steps 1–5)

We collected **503 rules manuals** covering all 51 jurisdictions from 2021 to 2027, converted
them to searchable text, and worked out how the program is structured: which rules exist, how
each state modifies them, and how the pieces fit together.

The output was a build-ready specification — 14 documents plus appendices, with every claim
traceable to a named page of a named document.

**The most important thing we found:** printed rule numbers are not reliable identifiers. The
2027 national edition renumbered 21 rules *and reused numbers for different concepts* — Rule 22
means one thing before 2027 and something entirely different after. Software that looks rules up
by their printed number will one day apply the wrong rule and produce a wrong price, silently.

### Stage two — find the actual prices (Step 6–7)

The rules tell you how to calculate, but not what to calculate with. We then obtained **472 loss
cost manuals** — the publications carrying the actual prices — and matched them to the rules
manuals.

*"Loss cost"* is the industry term for ISO's estimate of the expected claims cost, before an
insurer adds its own expenses and profit margin. Each insurer applies its own multiplier on top.
So these files get us most of the way to a price, but the final step is always the carrier's own.

We also hit our first real hazard here. The standard tool for extracting tables from PDFs
**silently scrambled the price grids** — numbers detached from their row and reattached to the
one above. Every result looked like a plausible price. A different tool read them correctly. We
proved which was right by arithmetic: Indiana should have 4 territories × 1,188 business types ×
2 columns = 9,504 cells, and the correct tool returns exactly 9,504.

### Stage three — a correction worth recording (Step 8)

We reported that the geographic definitions — the mapping from ZIP code to rating territory —
were missing from our source material entirely.

**That was wrong, and a human caught it.** They were in the rules manuals all along, on pages we
had not looked at. New Jersey alone carries 721 ZIP-code rows.

The cause is worth stating plainly: we had searched *one* set of files, found nothing, and
reported the result as if we had searched *both*. Every subsequent claim of "this is missing" now
has to name what was actually searched. This became a standing rule, and it is the reason later
stages were structured the way they were.

### Stage four — a second, independent source (Steps 13–14)

ISO also publishes the same program as **machine-readable data files** — structured tables and
executable rules rather than printed pages. We obtained **567 of these packages**, about 87,000
files.

Here we did something deliberate. Rather than analyse them ourselves — knowing what we already
believed from the PDFs, and therefore likely to go looking for confirmation — we ran the analysis
**in isolation**. A separate process examined the data files with no access to any of the earlier
work, and no hint about what it might expect to find.

That isolation is what makes the result meaningful. When the two analyses independently reach the
same conclusion, the agreement is evidence rather than an echo. And they did agree, repeatedly:

- The national layer holds the method and none of the money — reached from prose in one, from
  measurement in the other, then confirmed a third way.
- The same 27 jurisdictions use ZIP-code territories — **identical lists**, no differences.
- Territory counts match exactly (New York 20, New Jersey 15, California 11 …).
- The classification revision — 229 codes retired, 204 added — **identical numbers** from both.
- National factor tables match **digit for digit**.

It also corrected each side. The data files closed our single biggest weakness: we had dated 264
manuals by educated guesswork, and the data files state each package's identity and date
exactly — **567 out of 567**.

### Stage five — compare, then plan (Steps 14–16)

A third independent review read both analyses, adjudicated the disagreements, and could go back
to either source to settle them.

**It found three things neither analysis had caught alone.** The most striking:

> The data files encode *"refer to an underwriter"* as the number **`0`**.
>
> For drones over 55 lbs, the manual says *Refer To Company*. The data file says `0`. Software
> reading only the data files would price those policies at **$0.00** — precisely the risks that
> are supposed to get human review.

Neither source revealed this alone. The data file looks like a legitimate zero; the manual has no
machine-readable form. Only holding them side by side shows what `0` actually means.

We then wrote the technical build plan, and a register of everything still unresolved.

### Stage six — the build rule (Step 20)

A plan is only as good as its rule for what counts as evidence, and ours had not been stated. It
has now been set, and it is deliberately strict:

> **Build from the data files. Use the manuals to confirm the build, not to source it. Assume
> nothing that is not in the files. Where confirmation is needed, check the manuals. If that
> fails, ask.**

The distinction that does the work: the manual may tell us what something in the data files
*means* — that a `0` means *refer to an underwriter*, for example. It may **not** supply a
calculation the data files do not contain. That would be inventing a mechanism, and inventing is
what this rule exists to prevent.

The effect is a **shorter build and a longer question list**. Ten questions now go to the
business rather than being quietly answered by a default. That is the trade being made on
purpose: every one of those ten is a real decision that would otherwise have been buried in
code.

### Stage seven — seven coverages, walked through one at a time (Steps 27–37)

**All on 2026-08-11.** With the rule set, each coverage was derived end to end from the data files
and then checked against the filed manuals: **Premises/Operations, Products/Completed Operations,
Owners & Contractors Protective, Liquor, Railroad Protective, the Product Withdrawal / Electronic
Data / Cyber group, and Unmanned Aircraft.**

The point of doing them one at a time, rather than surveying them all, is that **each one changed
the design**. Between them they established that the same coverage is calculated differently
depending on the policy's effective date; that a state can switch a rule off by filing an empty
one, and that treating "empty" as "unchanged" charges a factor the state removed; that validation
messages carry parts of the calculation and cannot be skipped; that a coverage may read another
coverage's *working values*, so they cannot be calculated in isolation; and that the text label
next to a rate tells you which pricing path applies — a check that has now agreed with the data
**over 620,000 times without a single disagreement**.

**Three of the seven had no answer key** and were derived from the files alone with the manual as
confirmation. **Two together reproduce a real ISO-priced Oklahoma policy to the dollar**, and that
check runs as an automated test today.

### Stage eight — re-measuring everything against a date (Steps 30–32)

Midway through, a defect surfaced in a walkthrough filed the same morning: **every count in the
project had been taken over each state's most recent filing**, and the data contain 82 filings that
have not taken effect yet. Every such count described a **future** state of the world.

Re-measuring against an explicit date changed conclusions, not just numbers — see §0. The defence
built afterwards is mechanical rather than procedural: **the measurement scripts now refuse to run
without being told what date to answer for.**

---

## 4. What the product must do

### In scope

| # | Requirement |
|---|---|
| R1 | Price a General Liability policy from a structured description of the risk |
| R2 | Cover **all** sublines and coverages, built and reviewed **one at a time** — *7 of 14 walked through as of 2026-08-11* |
| R3 | Select the correct rules and prices **as of the policy's effective date** — never "the newest" |
| R4 | Resolve the national base and the state-specific overlay together, with the state package selecting its own national parent |
| R5 | Produce a full audit trail: every component of the price cites the document that authorises it |
| R6 | Treat *"refer to an underwriter"* as a normal, expected outcome — never an error, never a zero. **The data files express it *as* a zero in at least eight confirmed places**, so the engine must hold a register of those and never multiply by them |
| R7 | Run as a Python library and command-line tool |
| R8 | Be checkable automatically against both source sets, and repairable from those findings |
| **R9** | **Source every value from the data files.** A price component with no data-file origin cannot be produced — this is enforced by the software's own structure, not by review |
| **R10** | **Escalate rather than assume.** Where the data files are silent and the manuals do not settle it, refer the risk and raise the question |

### Explicitly not in scope

- **No user interface.** Library and command line only.
- **No claims, policy administration, or billing.**
- **No pricing judgement.** The engine applies filed rules; it does not decide whether a price is
  adequate or competitive.
- **No other lines of business yet** — though the approach is designed to extend, and most of what
  we learned is about how ISO publishes rather than about General Liability specifically.
- **No live connection to ISO's own rating service yet.** The connection point is designed in;
  building it is a later phase.
- **No filling of gaps by inference.** Where ISO's data does not say, we do not decide on its
  behalf. Ten such questions are listed in the build plan and come to the business.

### The honest ceiling

This is the single most important expectation to set.

Of the 477 coverage units in the machine-readable data that produce a price, **18 calculate one
from rates. 383 capture a price a human has already decided** and apply a modifier to it, and 76
simply add other prices together. **Under 4% calculate.**

That is not a limitation of our software — it is what the source material contains. ISO's own
data files declare roughly 5,300 situations that must be referred to an underwriter.

**And "calculates a price" is not the same as "produces a final price."** Four of the seven
coverages walked through so far are **company-rated**: the filed manual says, in one sentence,
*"For rates, refer to company."* The data files supply a complete and correct calculation whose
starting multiplier is a placeholder of `1`, waiting for a number only the insurer can provide.
The engine will produce a structurally complete, fully cited figure that is **an ISO
expected-loss value, not a market price**, until that multiplier is supplied.

**So the realistic outcome is: fully automated pricing for the core, high-volume coverages, and a
structured, well-documented referral for the rest.** Anyone expecting end-to-end automation of
every coverage should know now that no amount of engineering on this material produces it.

---

## 5. How we will know it works

There is no external system to check our answers against — yet. So correctness is established
several ways at once:

| Method | What it proves |
|---|---|
| **The manual's own worked examples** | Where ISO publishes a sample calculation, we reproduce it exactly |
| **Same risk, every jurisdiction** | Price one identical business in all 51 jurisdictions; **every difference must name the rule responsible.** An unexplained difference is a bug |
| **Cross-source agreement** | The checks where our two independent analyses agreed become automated tests |
| **Automated review** | Two expert reviewers — one for the manuals, one for the data files — audit each price and cite the authority for every objection |
| **ISO's own worked example** | The data files contain **one fully rated policy** (Oklahoma) — inputs and the answer. We reproduce it exactly. Available today |
| **ISO's own service** *(later)* | The broader external check, across many risks |

**One design point worth understanding.** The dangerous failures here are silent — they produce a
believable number rather than an error message. That is why the plan leans on automated checks
and audit trails rather than on testing and code review alone. A human reviewing a price cannot
tell that a factor came from the wrong state's table; a machine comparing it against the cited
document can.

---

## 6. Delivery plan

| Phase | What happens | Reviewable output |
|---|---|---|
| **0–1** | Foundations: load all 567 data packages, verify every one | Load report; all checks passing |
| **2** | Version resolution: the right national and state versions for any date | Proof that date-based selection is correct |
| **3** | Meanings layer: what the symbols mean, geography, rounding | Territory resolution working |
| **4** | **First coverage — Premises/Operations** | **Algorithm walkthrough + state deviations, presented to you** |
| **5** | Automated review loop live | Findings on the first coverage, and their resolution |
| **6** | **Size-Of-Risk** — moved here 2026-08-11 at your direction | Required before the Electronic Data and Cyber coverages can be built; they read its output |
| **7–13** | Remaining coverages, one per phase | Same presentation for each |
| **14–16** | State-specific coverages · capture handling · whole-policy assembly | End-to-end policy pricing |
| **17** | Connection to ISO's service | *Later — but see below* |

> **Phase 17 is now worth bringing forward.** It was scheduled last because we believed there was
> one priced example to check against. There are **54, covering 50 states**, already on disk. Most of
> the completed coverages can therefore be checked against ISO's own answers **before** any
> connection to their live service — which is the cheapest confidence available and does not depend
> on anyone at ISO. The connection itself is still needed for the two things the examples cannot
> settle: the rounding tie-break, and loss history for experience rating.

**At each coverage phase you will be shown:** the calculation as ordered steps with its source
citations; every input it needs; which lookups come from the national layer and which from the
state; **which jurisdictions deviate and exactly how**; every situation that produces a referral;
and what it cannot price, with the reason.

Nothing is considered finished until that walkthrough is accepted.

---

## 7. Risks and open questions

| Risk | Plain meaning | How we handle it |
|---|---|---|
| **Rounding rules are not written down** | The data declares where to round 7,682 times but never says *how*. Rounding up versus to-even changes the final price | Make it a configurable setting, flag every place we had to choose, and let ISO's service settle it |
| ~~21 jurisdictions have no geographic mapping~~ **Resolved** | We thought a fifth of the country couldn't be priced. In fact 20 of those states have only **one** territory, so there is nothing to look up — 19 use code `001`, North Carolina uses `002`. The other four (CA, FL, NY, TX) organise by county and city name, and those tables exist too | All 51 now resolve. The only remaining need is turning a street address into a county or city name for those four states |
| ~~**`0` may mean "refer" elsewhere too**~~ **Largely resolved, and bigger than we thought** | A `0` in these files has turned out to have **seven distinct meanings** — a real factor, an unpublished one, a degraded referral, a switch to a different pricing path, an input-derived calculation, a genuine "no liability in this state", and a coverage the state does not offer. **Four now have a test inside the data itself**; the drone case provably does not and relies on the manual. **In the drone tables alone, 18 of 60 cells are referral markers** — nearly a third of the grid | A register of confirmed cases, consulted before any factor multiplies — never a scan, because a sentinel is indistinguishable from a real zero by inspection |
| **Some price factors have no known source** | Three multipliers appear in the calculation with no table behind them | Default to no effect, flag as unverified in the audit trail |
| **We cannot yet prove every input produces a price** | We proved nothing is *missing*; we have not proved every path *finishes* | Only a working engine and ISO's service can settle this |
| **Misfiled source files will recur** | Two packages arrived filed under the wrong state — including in the original archives, so the error came from upstream | Identify packages by their internal content, not their folder |

**Eighteen of those questions now go to the business rather than to a default** — the build plan
lists them as E1–E19, one of which was withdrawn before it was filed; up from ten as the
coverage walkthroughs surfaced more. **Eight have dissolved on someone opening a file.** Two are not engineering at all: **`ErcCore` and ISO's
engine specification can only come from ISO**, and the lead time starts when we ask, not when we
need them.

**The last one was decided on 2026-08-11: it is a broker question.** For drones, the manual says
that where more than one usage category applies, the highest modifier wins; the data files accept
only one category. **The submission will arrive with one category already chosen** — we ask the
broker — rather than the engine taking a list and picking the maximum, which the data files do not
authorise.

That decision is safe to implement because **ISO already publishes the answer for "we don't know."**
`Unknown` and `Not Applicable` are filed categories on all three drone rating questions, and both
price as *refer to an underwriter*. So a broker who genuinely cannot tell has a proper way to say
so, and the risk goes to a person instead of getting a wrong price. **Four of the inputs we
thought were missing have now turned out to be questions for the broker rather than gaps in the
data** — the county for four states, a workers' compensation rate for one protective coverage,
this, and whether size-of-risk rating applies at all. In each case ISO already publishes a way to
say *"unresolved"*, so nothing has to be invented.

**Everything unresolved is tracked in a single register** — 65 items, each tagged with which
source it came from and what would settle it.

**And as of 2026-08-12 the referral conditions have a register of their own**, because they were
scattered across eleven coverage walkthroughs and an engine cannot read prose. It holds **28
conditions in four kinds**, and the split that matters to the business is this: **9 can be detected
before rating even starts, 6 during rating, and 11 cannot be detected at all** — for those eleven
the data files carry no test, so each is a decision about how the business wants to behave rather
than something the engine can work out. Building the register **found errors in four completed
walkthroughs**, including one finished the same morning.

---

## 8. Where we stand

**Updated 2026-08-12.**

**The build rule is set** (§3, stage six): data files are the source, manuals confirm, nothing is
assumed, open questions come to the business. **Today it was refined once, deliberately.** Asking
the broker a question that can only ever *stop* a quote — never change a price — is now allowed even
where ISO's data has no field for it, because declining to price takes nothing from the manual. The
limit is written down more prominently than the permission: an input that could move a number still
may not come from the manual.

**All fourteen coverages in the build order are walked through and accepted**, along with the three
owed side-pieces. Two coverages together reproduce a real ISO-priced policy to the dollar, and that
check runs today as an automated test.

**Every question about when to stop and ask a human has been answered.** Thirteen decisions,
recorded with the evidence behind each. Of the eleven that looked open, **three had already been
decided earlier in the project** and were being put to you a second time; **four turned out not to
be referrals at all**; and **two shrank by an order of magnitude once measured** — one from "188
classifications" to ten, all of them cannabis and hemp, and one from "railroad operations" to a
single class out of four.

**We can check far more of this than we thought.** The project holds **54 fully-priced example
policies covering 50 states**, not one. That is the strongest single change in our testing position
and it was found by you, not by us.

**What still has no answer key:** loss history for experience rating. None of the 54 examples
carries it, so that one input can only ever be checked against ISO's live service.

**Done:** both source sets collected, converted and analysed; **all 1,122 manual documents ingested
and searchable**; two independent specifications written and adjudicated; two automated expert
reviewers built, tested and now reading the whole library; every figure re-measured against a date;
eleven coverage walkthroughs; the referral register with thirteen decisions; the technical build
plan; every step reproducible from scripts kept in the repository.

**And, as of this evening, working software.** **Stage 1 of the engine is built** — 1,814 lines
answering *which rulebook applies to this state on this date*, with every value carrying the ISO file
it came from. **20 acceptance cases and 13 load-time safety checks, green at two dates.** Six test
suites now run, not four.

**The instruction to hold has been honoured and is now spent.** No engine code existed until you gave
the word; from here the rule is **stage gates** — each of the six stages is shown to you, with what it
does, what it was checked against and what it cannot yet do, before the next begins.

**Not done: stages 2 through 6.** No ISO rule is executed yet. That is stage 2, the interpreter, and
it is the only genuinely new engineering in the whole build.

### The build is under way, one signed-off stage at a time

**Decided 2026-08-12, after the analysis was done. Stage 1 was built the same day.** The engine will **execute ISO's rules directly**
rather than re-implement them in code. That was chosen on a measurement, not a preference: ISO's
instruction language is **58 kinds of instruction across 809,088 uses, and the twenty commonest
cover 94%**. Implementing that language once means every state, every coverage and every future ISO
filing comes free — against the alternative of hand-writing 4,461 rules per package and **345 more
for California alone**, then repeating it each time ISO files.

**It will run in two modes, sharing one code path.** One reproduces ISO exactly, for proving the
engine correct against ISO's own service, where any difference is our defect. The other enforces the
referral rules you set, which is what would actually be shipped. **The difference between the two
modes is itself a report** — every risk where ISO would quote and we would not.

**Six stages, each signed off before the next**, exactly as the analysis was:
[`BUILD-STAGES.md`](BUILD-STAGES.md). **Load and resolve — built** · the interpreter · the kernel and
the two modes · state schemas and sample payloads · the enum workbook · a simple interface.
**Stage 2 awaits your approval.**

**Worth doing early, and still owed:** measuring what those 54 example policies actually cover, so
we know which coverages can be checked against ISO's own answers and which cannot. That becomes
urgent at stage 3, when the engine first produces a premium to compare.

The standing recommendation held to the end and you ruled on it twice: **finish the walkthroughs
before writing code.** Every one changed the architecture, including three on the last day — and the
measurement that chose the architecture was taken on the final day of analysis.

---

## 9. A note on how this project has worked

**Updated 2026-08-12, and the update is the point.**

Two days ago this section said three things had been asserted confidently and turned out to be
wrong. **Today alone added nine more**, several to work written the same morning.

They are all the same mistake wearing different clothes: **something was measured in one place and
then described as though it were true everywhere.** A folder. A filename pattern. A search term.
The national rulebook instead of the fifty-one state ones. One directory instead of the file system.

The list, in order of discovery: the geographic definitions "missing" when they were not; the
analysis described as reproducible when the scripts lived in a temporary folder; a whole family of
rating plans recorded as unavailable when the data files carry them in full; *"the latest filing"*
taken to mean *"today's rules"*; a coverage's pricing basis reported absent because a search for its
expected name found nothing; a build item measured at double its real size; a scope count two short.

**And today:** a text-reading tool's failure mistaken for documents that could not be read; a
terrorism factor checked nationally and reported as though it were the answer for all fifty-one
states, when **fifteen file their own**; two whole coverages described without noticing California
withdraws them; a cap described as universal when Nebraska replaces it; a state's coverage recorded
as not pricing when it prices; **the same rating plans recorded as absent for a second time, from a
second direction**; and — the one you caught — **fifty-three priced example policies described as
one**, a claim that had reached two passing tests.

**What is different now is that most of them were caught by a machine rather than by re-reading.**
The counting discipline added on 11 August requires every count to name what it counted out of, and
the referral survey built today looks for problems by scanning rather than by re-reading our own
notes. That survey **corrected four completed walkthroughs on its first run**, one of them finished
the same morning. The two mistakes it did not catch were both caught by you.

**The honest summary is not that the project makes fewer mistakes.** It is that the mistakes are now
usually found in hours by something automatic, rather than in months by something expensive.

**The shape is identical every time.** Not carelessness, and not a conclusion drawn from too little
evidence — a conclusion drawn from **the right evidence identified the wrong way**. A name was
matched where a thing should have been named. Twice today the mistake was made *inside a document
that criticises the same mistake elsewhere on the page.*

Two things follow, and they pull in opposite directions.

**The countermeasures work.** Every one of these was caught, none by luck: by re-deriving a figure
instead of citing it, by two independent analyses disagreeing, or by a list contradicting another
list. Nothing was found by review or by careful reading alone.

**The rate has not fallen.** Seven coverage walkthroughs in one day produced four corrections. That
is the argument for keeping the checks in place rather than declaring the material understood —
and it is the honest reason the automated review loop sits at the centre of the build rather than
at the end of it.

**And the pattern was finally named precisely enough to be machine-checked.** "Reading the name
instead of the file" was too vague — the project's own rules already said to read the file, and were
followed. The sharper version: **a search was allowed to decide what the population was, and then a
conclusion was drawn about that population.** Every one of the day's wrong figures was a **count or
an absence**; not one was a misread rule. That distinction is what made a fix possible.

The fix is mechanical rather than a resolution to be careful. **Every count must now be written
"n of N", with N derived from the source rather than from the query** — a bare number hides its
denominator and cannot be checked by a reader. A script enforces it, and on its first run it found a
whole coverage nobody had noticed and corrected two earlier claims. **Then it caught its own fix
making the same mistake**, which is the clearest argument available that the rule needed to be a
machine and not a memo.

**One further observation worth recording.** The single richest source of new findings today was
**this project's own list of unfinished checks.** Two items had been written down as *"verified for
one edition only"* and *"sampled, not corpus-wide"* — and both were re-discovered from scratch,
at full cost, before anyone re-read the register. An audit item that says it is incomplete is a
finding waiting to be collected cheaply.

---

## Further reading

| Document | For |
|---|---|
| `docs/GL-RATING-ENGINE-BUILD-PLAN.md` | The technical build plan — architecture, phases, code structure |
| `docs/COMPARISON-ERC-VS-PDF.md` | The two analyses compared and adjudicated |
| `docs/OPEN-ITEMS.md` | Everything unresolved, 67 items |
| `docs/rating-engine/` | The manual-derived specification (14 documents + appendices) |
| `docs/erc/` | The data-file-derived specification (6 documents) |
| `docs/PHASE-SIZING.md` | What each build item actually contains, measured |
| `docs/gates/` | The eleven coverage walkthroughs, the California and New York differentials, the as-of re-measurement and the reconciliation — 15 documents |
| `PROCESS_LOG.md` | Every step, with reasoning and corrections |
| `scripts/erc/out/referral_register.json` | Every situation that stops and asks a human — 28 of them, with the thirteen decisions taken |
| `Payloads/` | The 53 priced example policies, one per state, each with its input |
