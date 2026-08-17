# How to use the tester — a walkthrough

**Who this is for:** anyone who wants to run the tests and read the results. No coding, no jargon
that isn't explained.

**What the tool is.** A rating engine has one job: work out the premium for an insurance submission.
Ours does it by reading ISO's own rulebook files. This tool checks whether it got the answer right —
by sending the same submission to ISO's own service and comparing, figure by figure.

---

# Opening it

Double-click **`start.bat`** (Windows) or **`start.command`** (Mac). A browser window opens.

Click **Tester** — or go to `http://localhost:8000/tester`.

You'll see two columns. **Left is what you're testing. Right is what happened.**

---

# The five minute version

1. Left column, top box: pick **T0 · Smoke**.
2. Untick **Compare each against ISO**. *(This makes it free — see "What things cost" below.)*
3. Click **Start**.
4. Wait about a minute. Watch the right column.
5. Click the **QA summary** tab underneath.

That's a complete test run of all 51 US jurisdictions.

---

# The left column — what you're testing

## The QA programme box (top)

**This runs whole pre-built test plans.** Five of them, called tiers:

| | What it does | Roughly |
|---|---|---|
| **T0 · Smoke** | One standard risk, priced in every jurisdiction | 1 minute |
| **T1 · Core logic** | 22 different risks across 12 carefully chosen states | 3 minutes offline |
| **T2 · Full logic** | The same 22 risks across all 51 | 10 minutes offline |
| **T3 · Value sweep** | *Greyed out.* Not built yet, and it says so |
| **T4 · Edition cliff** | *Greyed out.* Blocked, and it says why |

**A greyed-out tier is deliberate.** It tells you what it needs rather than pretending to work.

**Before you press Start, read the line under the buttons.** It tells you how many calls to ISO the
run will make and how many you have left today.

**If it would go over budget, it warns you — and lets you decide.** Nothing is sent on the first
click. The button turns red and says *"Run anyway — N over budget"*, and the numbers stay on screen
while you make up your mind. **Press it again and it runs.** Change anything — the tier, the offline
tick — and it disarms, so an override can never carry over into a run you didn't mean.

**Why there's a budget at all.** It is **our own policy, not a limit ISO publishes.** There is no
documented rate limit. The number exists so our traffic keeps looking like ordinary use rather than
like a script — 60 calls a day is comparable to what this account already does, and a thousand in an
afternoon is the pattern that earns a phone call. **You are better placed than a constant in a file
to judge whether a particular run is worth it**, which is why it warns rather than refuses.

**Every override is recorded.** A run made over budget is labelled as such, so a heavy day shows up
in the weekly report rather than on an invoice.

**"Show the matrix first"** prints the list of risks the tier would test, without testing anything.
Useful when you want to know what you're about to spend money on.

## The risk box (below it)

**This is for testing one thing at a time.** Every dropdown is read live from ISO's own files, per
state — so **you cannot pick something illegal.** If a value only exists in some states, the dropdown
says so: *"— 31/51 states."*

Set what you want, click **Run all states**.

**"Check where it applies"** answers *"which states even allow this?"* without pricing anything. Free
and instant.

---

# The right column — what happened

## "This run"

A coloured bar and a table, one row per jurisdiction. The four outcomes:

| | What it means |
|---|---|
| **Agrees** | Our premium matches ISO's — **and so does every other figure**, not just the total |
| **Disagrees** | They differ. **Treated as our fault until proven otherwise** |
| **Not applicable** | ISO doesn't offer this combination in that state. **Never a failure** — grey, always |
| **Engine refused** | We declined to price it. Sometimes right, sometimes not — see the review tab |

**"Not applicable" being grey matters.** Twenty states can't host a two-location test because they
only have one rating territory. That's ISO's filing, not our bug, and counting it as a failure would
make the tool lie to you.

## The tabs underneath

### QA summary
**The one screen to look at first.** A big percentage, and a **map of the US**.

Every state is the same size square. That's on purpose: Rhode Island and Texas carry one test each,
and drawing Texas 200 times bigger would suggest we tested it 200 times harder.

**Hawaii is always blank.** ISO doesn't publish rules for it. Leaving it off the map would hide that.

### What the review found
**The harness checking its own work.** Three sections — explained in detail below.

### Agreement over time
One bar per run. Lets you see whether something that used to work stopped working.

### Coverage
**The honest picture of what we've never tested.** Filled squares are tested, grey is *ISO doesn't
offer it there*, empty is **never tried**. Expect a lot of empty. That's the point of showing it.

### Premium response
Lines showing how the premium moves as you change one thing. **The premium should rise smoothly as
the coverage limit rises, in every state.** A kink or a flat stretch usually means something failed
to look up and quietly fell back — visible before it's explainable.

### Defects
Problems seen before, with when they first appeared and when they were last seen.

---

# "What the review found" — the important tab

This is the harness checking **itself**. Three sections, and they're different in kind.

## 1. Settled

When we report *"not applicable"*, that's the one result never counted as a failure — **so it's where
a mistake could hide forever.** This section re-checks every one of them against ISO's files, using
different code.

- **Confirmed** — ISO's files agree. Genuinely not offered there.
- **Contradicted** — **ISO does offer it. The refusal is ours.** This is a defect.
- **Unverified** — couldn't be settled, and says so rather than guessing.

**This exists because of a real mistake.** For three days the tool reported twenty states as unable
to do terrorism cover, with a perfectly reasonable explanation attached. **The explanation was wrong
and it was our own code.** Nothing was checking the explanations.

## 2. Needs a person

**Claims we are making that someone should try to disprove.** Each one gets sent to three specialists
— one reads ISO's data files, one reads ISO's printed manuals, one reads our code — and each is told
*"assume this is wrong and prove it."*

**They're dispatched by hand, not from this page.** The screen shows what's worth attacking; it never
claims a review has happened.

**Why "prove it wrong" rather than "check it".** Asked *"is this right?"*, a reviewer tends to agree.
Asked *"find what's wrong with this"*, it does real work. On its first use this refuted a fix we'd
made eight hours earlier.

## 3. The calls we did not make

When our engine refuses to price something, **ISO never sees it** — so *"ISO would refuse it too"* is
a guess.

This lists the submissions we refused, exported as files ready to send by hand. Each folder has the
exact request and a note explaining what to look for in the answer.

To produce them: `python scripts/qa_review.py --payloads`

---

# What things cost

**Anything offline is free and unlimited.** Our engine runs on your machine.

**Every comparison against ISO is a paid call**, about 8 seconds each. So:

- **Untick "Compare each against ISO"** and you can run anything, as often as you like, for nothing.
- **Tick it** and you're spending. The budget is **60 calls a day**, and the tool enforces it.

**Always run offline first.** It finds the broken and inapplicable cases for free, before you spend
anything on them. Yesterday that identified a defect across fourteen states for zero cost.

---

# Running it from the command line

Same thing without the browser:

```
python scripts/qa.py --tiers                  what the tiers are
python scripts/qa.py --estimate               what each costs, and today's budget
python scripts/qa.py --tier T1 --plan         the list of risks, runs nothing
python scripts/qa.py --tier T1 --offline      run it, free
python scripts/qa.py --tier T1                run it against ISO
python scripts/qa_review.py --tier T1         the review, section 1
python scripts/qa_review.py --pass4           the claims worth attacking
python scripts/qa_review.py --payloads        export the refused submissions
```

---

# Reading a result honestly

**Four things worth knowing so the numbers don't mislead you.**

**1. "Agrees" means every figure, not just the premium.** ISO publishes hundreds of intermediate
values back and all of them are compared.

**2. Puerto Rico is never compared.** No subscription entitlement. **Every count is out of 50, not
51**, and the tool says so rather than quietly rounding up.

**3. "Rated" is not "tested".** A test can run, report success, and exercise nothing — if the value
we picked happens to have no effect. The tool now spots this and reports it, but it's worth knowing
the difference exists.

**4. Breadth is still narrow.** Every test uses broadly one kind of business. The Coverage tab reads
**1 of 19**. We've proven the engine across *geography*, not across *the variety of business a
carrier writes*. That's the next piece of work, and it's the honest caveat on everything else here.
