# What the harness taught us — 17 August 2026

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
