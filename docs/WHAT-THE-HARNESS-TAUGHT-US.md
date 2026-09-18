# What the harness taught us

**A running record.** Each session that teaches something reusable gets a dated section.
So far: **17 August 2026** — the GL engine, seven defects found against ISO. **17 September 2026** — reading ISO's corpus for Commercial Property, before any CF engine exists.

---

# 17 August 2026 — the GL engine

**Who this is for:** anyone who wants to know whether this engine can be trusted, without reading
code. No jargon that isn't explained the first time it appears.

**One day. Seven defects found, six fixed, one escalated to a person.** What follows is what each one
taught, and the pattern underneath them — which is more reusable than any of the fixes.

---

## First, the thing that makes this different

**Most rating engines are tested by people who already believe they work.** Someone writes a test,
the test passes, everyone moves on. The trouble is that a rating engine's worst failures don't look
like failures. **They look like a number.**

This project is built the other way round. The engine, ISO's own files, ISO's live service and the
test harness are pointed *at each other* until they disagree — and **the disagreements are the
product.** A day where everything agrees has taught us nothing.

Today they disagreed seven times.

---

## The seven

### 1 · A fallback that could never happen

**In plain English.** ISO's rules constantly say *"use this state's number; if the state hasn't filed
one, use the national number."* We handled that fine — right up until the answer had to be worked out
through a calculation first. Then the engine treated *"the state has nothing"* as an error and
stopped, instead of shrugging and going to look for the national number.

**How bad.** A whole rating feature — size-of-risk — was working correctly in **zero of 51 states.**
Forty-nine refused outright and the other two silently did nothing.

**How it was found.** By varying the *submission* instead of the *state*. Every test before this used
the same risk everywhere.

**What it taught.** *A feature can be completely broken in every state and still pass every test, if
no test ever turns it on.*

---

### 2 · A contradiction that turned out to be arithmetic

**In plain English.** To price terrorism cover, the engine has to tell ISO where the risk is. Some
states want a territory code, some want a ZIP. We had two counts of which states wanted which, taken
two different ways, and they didn't line up. It sat on the record for three days described as
*"they do not obviously reconcile."*

**They reconcile perfectly. 4 + 11 = 15.** They were never two groups plus a remainder — they were
one group of fifteen, counted twice.

**And then the real finding.** The thing actually blocking us was **our own code**. We had a fallback
that did nothing at all, and it was the only reason twenty states looked unsupported.

**How bad.** Terrorism was blocked in **zero** states, not twenty. It now prices in all 51.

**What it taught.** *A refusal with a well-written explanation is still a refusal.* The message said
*"this state declares neither option"* — reasonable, specific, and wrong. Nobody questioned it
**because it explained itself.**

---

### 3 · The oldest open question, settled in four phone calls

**In plain English.** When a premium calculation lands exactly halfway — 2,164.5 — does it round up
or down? Every engine has to decide. We'd never been able to prove which ISO does, because **out of
every submission we held, not one landed exactly on a halfway point.**

**How it was settled.** By building a submission that had to. Four of them, then asking ISO.
**ISO rounds up. Four out of four.**

**A second idea was tested too.** It was suggested ISO might chop numbers to four decimal places
first and then round. Plausible, and it would have looked exactly like rounding down. **It changes
nothing — 0 out of 432 calculations** — and there's a structural reason why it can't.

**What it taught.** *You cannot find a rare case by collecting more ordinary ones.* And one attempt
failed instructively: a submission that hit the halfway point five times still produced the same
premium either way, because those particular halves never reached the total. **A test that fires is
not a test that proves anything.**

---

### 4 · The harness caught itself

**In plain English.** We turned terrorism on in New York. The premium didn't change — **and ISO
agreed with us to the penny.** So nothing was wrong.

Except the test had reported itself as *passed*. The territory we'd picked happens to carry **no
terrorism charge at all**, while five others charge 110. **The test ran, reported success, and
exercised nothing.**

**What it taught, and this is the important one.** *The defect was not in the engine. It was in the
thing measuring the engine.* Every coverage figure that test contributed to was overstated, and
nothing would ever have said so.

The harness now tells two things apart that used to look identical: **"ISO's own rules mean this
genuinely does nothing here"** versus **"we picked a value that does nothing."** The first is a real
finding. The second is our mistake.

---

### 5 · Where we produced a number and ISO refused

**In plain English.** The mirror image of the first defect. There, we refused where ISO priced. Here,
**we produced a premium where ISO's own service returns an error.**

The engine looked for a rate, didn't find one, wrote down "nothing" — and then carried on and
finished the calculation anyway.

**How bad.** Fourteen states. And the giveaway: **eight of them returned the *identical* premium**
despite starting from completely different base premiums. A premium that doesn't depend on the
state's own rate is **complete, plausible and wrong** — which is precisely the failure this engine
exists to prevent.

**What it taught.** *Fixing one defect makes the next one reachable.* This code had never run before
that morning, because defect 1 was stopping everything before it got there. **The backlog wasn't a
queue — it was a stack, and the top item was hiding the rest.**

---

### 6 · The review refuted the fix, eight hours after we made it

**In plain English.** We built a review step whose whole job is to attack our own results — three
independent specialists, each reading a different source, each told *"assume this is wrong and prove
it."*

We pointed it at the fix from defect 5, made that same morning. **It came back split, and both halves
mattered.**

**The fix was right** — and better supported than when we made it. Texas has never filed the
size-of-risk plan at all, and **two completely separate ISO sources agree on exactly which 35 states
did**, with no difference either way. No amount of engineering can price it in Texas, and none
should try.

**But the reason we'd written down was wrong.** We'd claimed ISO's error message proved ISO refused
for the same reason we did. It doesn't — it's an error about a *different* lookup, and the message we
quoted was **captured in Georgia, not Texas.** That wrong claim had been copied into three documents.

**And our error message pointed at the wrong file.** It blamed a table that, in Texas, is perfectly
healthy — 9,504 rows, working correctly. The table that was actually empty is a different one, a file
containing nothing but a header. **Anyone investigating would have gone to the wrong place.**

**What it taught.** *Tests check what the engine does. Nothing was checking what the engine says.*
Both errors were in explanations, not behaviour — so every test passed, and would have kept passing.

---

### 7 · Something we cannot decide ourselves

**In plain English.** ISO publishes the same information twice: as documents for people, and as data
files for computers. On one point they say different things.

Where the printed manual says **"refer this to an underwriter — we're not publishing a price"**, the
data file says **zero**. In Texas alone that happens **178 times**, and the two sources otherwise
agree on all 1,188 classifications with no mismatches at all.

Our engine reads the data files. So it prices those as **zero, and tells nobody.** We added one such
classification to a Texas risk and the premium moved from 7,821 to 8,973 with **no referral and no
warning.**

**But — and this matters — ISO's own live service does the same thing.** We have a recorded, verified
match against it on a risk that contains exactly this situation.

**So this is not a bug report. It's a question for a person:** is *"the service prices a
refer-to-underwriter class as zero"* intended behaviour, or a seam everyone has quietly lived with?
**Neither ISO document answers it, and it isn't ours to decide.**

---

## The pattern underneath all seven

**1 · Not one was found by reading code.** Every single one came from running something against
something else — ISO's service against our engine, one measurement against another, a purpose-built
input against a prediction, and in two cases **the harness against itself.**

**2 · Not one needed a decision. Every one needed a measurement.** The first defect sat at the top of
the list for three sessions waiting for someone to approve a fix. What it was actually waiting for
was a *number* — and the work that produced that number was free, read-only, and available the whole
time.

**3 · The measurement changed the fix, twice.** Both times the obvious one-line change would have
been wrong. In one case the count showed that **51 of 69 affected places had something standing ready
to quietly absorb the mistake** — so the careless fix would have converted a loud failure into a
silent wrong number.

**4 · Closing a defect exposes the next.** Twice in one day.

**5 · The harness's own defects count.** Two of the seven were in the *measuring* apparatus, not the
engine. **A harness nobody suspects of being wrong isn't a harness — it's an assumption with tests
attached.**

**6 · Being right is not the same as being explainable.** Two of the day's findings were correct
behaviour with a wrong explanation attached. No test caught them, because tests check behaviour.
**A review that reads the explanations is a different instrument, and it found things nothing else
could.**

---

## Where that leaves the engine

| | Start of day | End of day |
|---|---|---|
| Size-of-risk working correctly | **0 of 51 states** | 37 rate, 14 correctly refuse |
| Terrorism | 31 of 51 | **51 of 51** |
| Checked against ISO on varied risks | 31 comparisons, 2 states | **184 comparisons, 11 states** |
| Rounding | unproven | **settled, four ways** |
| Known defects | 3 | **1**, plus one question for a person |

**92 calls to ISO all day**, each one aimed by a free offline measurement first.

---

## What we still cannot say

**We have proven this engine across geography. We have not proven it across the variety of business a
carrier actually writes.** Every test still uses broadly one kind of risk. Our internal coverage
measure reads **1 of 19**.

That is the honest headline, and it is the next piece of work.

---

# 17 September 2026 — reading ISO's corpus, before any CF engine exists

**No code was written this session.** The work was documents and data: two data dictionaries
covering countrywide *and* every state package, an index of ISO's own rating payloads, and a
specification of what a Commercial Property rating request actually contains. The CF rating
engine is still unstarted, deliberately.

That makes this a different kind of lesson from August's. August was *the harness disagreeing
with ISO*. September was *us disagreeing with ourselves* — and the pattern underneath is that
**almost every wrong answer came from reading a description of the data instead of the data
itself.**

---

## The one that reframed everything

**ISO ships its own test payloads, and nobody had opened them.** Inside the ERC packages, many
folders contain an `STC/` directory of ISO-authored rating requests. There are **921** of them
across GL and CF.

Before finding them, a payload specification had been reasoned out from the XML schema plus the
existing GL request. The STC files corrected it on **six** counts within minutes: there is no
`header`/`body` wrapper; there is no state field at all (the state comes from the product name);
coverage records are objects, not arrays; construction *type* is sent while construction *code*
is derived; the location field is `ProtectClass`, not `ProtectionClass`; and the contents record
carries none of the rating fields we had listed for it — they are all inherited from its parents.

**The lesson.** When a vendor ships examples, they outrank your reading of their schema. Go
looking for them *first*. The rule now: **before specifying any request format, search the
corpus for a real example of it.**

---

## Why the schema could never have answered it

We checked rather than assumed: across **all 56,207 CF field definitions, every single one is
marked optional-and-nullable.** There is exactly one optionality setting in the entire line of
business.

**The lesson.** The schema describes what is *possible*, never what is *required*. Only the
rules say what is required, and they say it through gates rather than declarations. **A schema
cannot be the source of a required-fields list.** Anyone building a submission form from the
DataDef alone will build the wrong form.

---

## Fixtures are not a test suite — check before you plan around them

The obvious next thought after finding 921 test payloads was "we have a regression suite." We
checked instead of assuming, and the answer is **no**: every STC folder contains inputs only.
Not one ISO file carries a premium.

Worse, the first scan *appeared* to find rated premiums — until they traced back to **three of
our own files** that had been dropped into ISO's directory tree at some point, using this
project's own naming convention.

**Two lessons.** First, **"they gave us test cases" and "they gave us answers" are different
claims** — verify which one you have before building a plan on it. These fixtures tell you what
a valid request looks like; ISO's live service is still the only oracle for whether a premium is
right. Second, **keep your files out of the vendor's corpus.** Ours contaminated a scan of ISO
content within minutes of the question being asked.

---

## Coverage: count what the examples actually exercise

Indexing the payloads was routine. Reading the index was not. Across all **364** Commercial
Property examples:

- **every one** is the same policy type
- **every one** is class-rated — none specific, none tentative
- **every one** is non-blanket
- **357 of 364** use one cause-of-loss form; only **3** use Basic — and all three of those are
  Builders Risk, which rates off a different branch entirely

The three switches previously identified as the most far-reaching in the whole line are each
exercised at exactly **one value**.

**The lesson.** A large corpus is not a broad one. **Measure coverage against the switches that
change behaviour, not against file count.** 364 examples that all take the same branch prove one
branch.

---

## Things that look like inputs and are not

Three separate traps, all the same shape:

- A **dropdown with no options.** Alaska files a district-selection list that is a header row and
  nothing else — in all nine of its editions — for a field Alaska's rules never read.
- A **field no rule consumes.** A district-territory field is declared countrywide and read by
  nothing.
- A **guard against an impossible value.** Three rules test whether a coverage type equals
  "Tobacco Sales Warehouses"; that exact value is offered by **zero rows in all 23 packages**
  that file the list. The test can never fire.

**The lesson.** Existence is not usage, in either direction. **A declared field with no rule
consumer, and a domain table with no rows, should be flagged — not surfaced as an input.** This
is the same lesson as "a table exists ≠ the table is usable", now with three more shapes to
recognise.

---

## Same name, different thing — twice in one session

The location record has both `ProtectClass` and `ProtectionClass`. Only one is used. Send the
other and nothing errors.

Worse: a rate table's key column is `OccupCategorySeverity`, while the field that feeds it is
`OccupCategoryRiskSeverity`. They bind by **position**, not by name. Searching the rules for the
column name returns nothing at all — which reads as *"nothing uses this"*, the exact opposite of
the truth.

**The lesson.** **A name match is not an identity, and a name mismatch is not an absence.** When
a search comes back empty, consider that you searched for the wrong string before concluding the
thing is unused.

---

## When a prior finding disagrees with you, reconcile — do not overwrite

A note on record said New York picks its base-rate table from **county**. The rules plainly
showed it testing **territory codes**. Easy to assume the old note was stale.

Checking showed both were right: the five territory codes map one-to-one to the five New York
City boroughs, via a county-keyed table. County → code → table. The reconciliation produced a
sharper result than either finding alone — and a live warning, because that territory code is
*supplied in the request*, so a Brooklyn risk submitted with the wrong code rates off the wrong
table and nothing errors.

**The lesson.** **A contradiction between a prior finding and fresh evidence is usually a missing
link, not an error.** Spend the ten minutes.

---

## Do not trust a plural

"The District states — AK, CA, NY" had been recorded as a single category. Checking each one
separately showed **three different mechanisms**: California reads a district field from the
request; Alaska and New York each derive it from territory, using different code sets.

The practical payoff was large and reassuring: **only one of the three needs a field the others
do not.** The record shape holds across all of them. That is a much better answer than the
grouping implied — and it was only visible because each was checked on its own.

**The lesson.** **A group name hides variation.** When a note says "these N are the same", that
is a claim to test, not a fact to inherit.

---

---

## The biggest one: ISO prices a policy, it does not administer one

**Mapping GL's premium chain end to end produced one finding that outranks the rest**, and it
only surfaced because someone asked a direct question the map had glossed: *does this include
interim premium fields, like pro-rata, written?*

The map had listed those fields and asserted they were "policy-administration values a policy
system supplies." That assertion had **not been measured**, and it had been checked against
countrywide only. Measuring it properly changed how large the finding was.

**Across all 52 jurisdictions, a fourteen-field block declared on all 1,025 record types is
written zero times and read zero times by any rule.** Ten premium fields — annual, policy-term,
prior, pro-rated, pro-rated prior, pro-rated change, total pro-rated change, change, evaluated,
override — plus four proration controls that only appeared when we searched for the *concept*
rather than the word "premium": pro-rate factor, pro-rate indicator, term-factor indicator,
earned-in-full indicator.

Nothing computes them. Nothing reads them. They are **inert carriers** — a shape shipped inside
ISO's schema so a round-tripped record has somewhere to put values that something *else* is
expected to produce.

### What ISO actually gives you

**One number: the full-term premium at the effective date you asked for.**

Proration, mid-term endorsement pricing, written-versus-earned, cancellation returns — none of
it exists in the filed content. The only transaction mechanism available is to rate twice at two
effective dates and subtract, and **that is our construction, not ISO's**.

### Why this has to be contemplated as we build

**1 · Above the full-term number, there is no oracle.**
Every defect this project has found so far was a *disagreement* — our number against ISO's. The
moment we compute a pro-rata endorsement delta, we leave the oracle behind completely. ISO
cannot confirm or refute it, because ISO does not produce it. That is a different and harder
risk class than anything in the August list, and the harness's whole method — point systems at
each other until they disagree — does not reach it.

**2 · The schema actively misleads anyone generating from it.**
A submission UI or payload builder built off the DataDef would render fourteen fields on every
record that do nothing at all. This is the same trap as the empty dropdown and the
consumer-less field found on the Property side, at roughly a thousand times the scale. **A field
existing in the schema says nothing about whether anything uses it** — and this is now the
third distinct shape that lesson has taken in one session.

**3 · The scope question is a decision, not a discovery.**
Nothing here is broken. The engine is right, the corpus is right, the map is right. What is open
is **how far up the policy lifecycle this project intends to go** — and if the answer is
"further than the full-term premium", then a whole layer has to be built with no reference
implementation to check it against. Better decided deliberately than arrived at.

### The trap inside the finding

`EndorsementPremium` *is* live, and looks like a counter-example to all of the above. It is not.
It sits on the terrorism endorsement coverage and sums the terrorism contributions of about forty
endorsements — *premium for the terrorism endorsement*, not *premium change from an endorsement
transaction*. Same word, unrelated concept, and it would comfortably fool a search.

**The lesson, stated as the missing check:** nothing in this project distinguishes *a field ISO
declares* from *a field ISO populates*. Every artefact built from the schema so far — the data
dictionaries, the payload spec, the submission shape — inherits that blindness. The measurement
is one pass over the rules per field; it had simply never been run until a question forced it.

---

## What this session produced

| | |
|---|---|
| Data dictionaries, GL + CF | countrywide **and** all state packages; 46,650 / 56,207 field rows |
| State-specific field lists | 19,522 GL / 9,915 CF rows, with the jurisdictions for each |
| `STC_Corpus_Index.xlsx` | 921 ISO payloads, with the switches each exercises |
| CF payload specification | class-rated Building + Personal Property, all four forms, Alabama, generalised across the district states |
| Completion tracker | MD + HTML, wired into the README and the CF build docs |

**A parser defect was fixed along the way**: 104 GL and 614 CF child-group references were being
listed as though they were ordinary fields. ISO's own payloads independently confirmed the fix —
the two kinds serialise differently.

**One defect was found in ISO's filed data**: a rate in the current Alabama filing is ten times
its value in all seven prior editions, and the branch that uses it would over-rate the affected
risks by roughly that factor. Raised rather than worked around.

---

## What we still cannot say

**Nothing here has been executed.** There is no CF rating engine, so every claim in the
specification is a careful *reading* of ISO's files, not a tested contract. The August lesson
still stands and now cuts the other way: **a document that agrees with itself has taught us
nothing either.** These findings become real when something runs them.

One question is worth flagging above the rest: a field required by the contents rate in **45 of
47 jurisdictions** has no list of legal values anywhere in the corpus, and appears in **none** of
ISO's 364 examples. We cannot tell from the files whether the engine defaults it or whether ISO's
own examples are underspecified. That one needs an answer from ISO.
