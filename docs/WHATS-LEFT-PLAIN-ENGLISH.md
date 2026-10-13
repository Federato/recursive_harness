# What's left, in plain English — 17 August 2026

**Who this is for:** anyone who needs to decide what we do next without reading code. No jargon that
isn't explained the first time it appears.

The technical version is [`BACKLOG-FEATURE-SETS.md`](BACKLOG-FEATURE-SETS.md); the register of every
open question is [`OPEN-ITEMS.md`](OPEN-ITEMS.md). Nothing here contradicts them — this is the same
work, said differently and at more length.

**Two companion documents, added 2026-08-17.** The
[QA programme proposal](qa-plan-proposal_20260817.html) sizes item 1 properly — how many tests, how
many hits on ISO, and what can and cannot be proven at all.
[`WHAT-I-NEED-FROM-YOU.md`](WHAT-I-NEED-FROM-YOU.md) lists what only you can supply to unblock the
rest; **section A of it was decided on 17 August.**

---

## First, what we actually have

**We built a rating engine for General Liability that doesn't contain any rating rules.**

That sounds like a contradiction, so it's worth a paragraph. ISO — the bureau that most carriers
licence their rates from — publishes its rules as *machine-readable files*, not just as manuals for
humans. Rates, factors, territories, the arithmetic, the order of operations: it's all in there, per
state, per edition.

Most engines read those manuals and then **re-implement** the rules in code. We don't. **Ours reads
ISO's files and executes them.** Search our whole engine for the word "deductible" and you get one
result, and it isn't arithmetic — it's a message.

**Why that matters commercially:** about 5,000 lines of code cover all 51 jurisdictions, and when ISO
files an update, it's a file drop rather than a development project.

**How we know it's right:** ISO also sells a live rating service. We send the same submission to both
and compare — not just the final premium, but **every single figure ISO publishes back**.

### Where that stands today

| | |
|---|---|
| Jurisdictions where we agree with ISO on a standard risk | **50 of 50** we're entitled to test |
| Jurisdictions tested with *varied* risks (deductibles, limits, coverages…) | **11**, and **184 of 184 comparisons agree** |
| Known things that are wrong | **1** |
| Defects found and fixed today | **5** |

**The one number to be sceptical about:** every one of those comparisons uses **the same kind of
business** — a single class of risk, at one or two locations. We've proven the engine across
*geography*. We have **not** proven it across *the variety of businesses a carrier actually writes*.
That is the honest headline, and it drives most of what follows.

---

# The work, in order of what I'd do

## 1 · Test more kinds of business, not more states — **the big one**

### What it means

Every test we've run prices roughly the same thing: an abrasives manufacturer, general liability,
premises and products. We've now run that same business through eleven states and it agrees with ISO
everywhere.

But a general liability policy can cover **liquor liability, contractors, pollution, product
withdrawal, railroads, underground storage tanks, electronic data** and more. Each has its own rates,
its own rules, and its own arithmetic. **We have never priced most of them.**

We track this internally as a coverage grid, and **it currently reads 1 of 19**.

### Why it matters

This is the difference between *"the engine works"* and *"the engine works for the business we
write."* Today we can honestly claim the first. **We cannot yet claim the second**, and a carrier
will ask.

Everything we found today came from varying something nobody had varied before. The last four states
we tested found nothing new — **geography has stopped teaching us things.** Business type hasn't
started.

### What's involved

Each new business type needs a realistic sample submission built from ISO's own declared list of
legal values, then run through both engines and compared. Some can be adapted from what we have;
others need a submission built from scratch because the shape of the risk is different.

### Size and risk

**The largest remaining piece of proving work.** Expect it to find defects — that's the point, and
every defect it finds is one a carrier doesn't find later.

---

## 2 · The last known defect: a rating credit that silently doesn't apply

### What it means

**Schedule rating** is where an underwriter adjusts the premium up or down for things about the risk
that the standard rates don't capture — good housekeeping, a poor claims history, that sort of
judgement.

We turn it on with a perfectly legal credit, and **the premium doesn't change.** Nothing errors.
It just quietly does nothing.

**This is not our bug.** ISO's own rules only apply schedule rating when a separate measure — how
credible the account's own claims experience is — passes a threshold. With experience rating switched
off, that measure is zero, so the credit is filed away and never used. **ISO's live service agrees
with us to the penny.**

We've now measured exactly how far this reaches: with the credit properly set, it moves the premium
in **three states — Florida, New York and Rhode Island — and in the other 48 it does nothing.** Those
three file their own version of the rule that overrides the national one.

### Why it matters

**An underwriter can apply a credit, see it accepted, and never learn it wasn't used.** The number
is right; the silence is the problem.

### What's involved

Two parts. First, build out experience rating so the other side of the condition can actually be
exercised — that needs about twenty pieces of claims history with dates. Second, a decision: **should
the engine say *"you asked for this, it wasn't applied, and here's why"*** rather than staying quiet?

I'd argue yes. It costs little and it removes a class of surprise that is very hard to explain after
the fact.

### Size

Medium. The decision is small; the experience-rating data is the work.

---

## 3 · Check our list of referral reasons against ISO's actual list

### What it means

A **referral** is when the rules say *"don't price this automatically — send it to a human."*

We carry a list of **28** such conditions, worked out by hand from the rules and manuals. **ISO ships
a spreadsheet inside every one of its packages listing 838 of them.**

Those aren't the same kind of list — ours are *"the arithmetic can't complete"*, ISO's are *"the
manual instructs a referral"* — so the gap isn't 810 missing items. But **we've never held the two
side by side**, and **five of the conditions we carry but don't yet detect could produce a wrong
number.**

### Why it matters

A missed referral means a policy gets priced automatically that should have gone to an underwriter.
That's a leakage and compliance question, not a technical one.

### Size

Medium, and it's mostly reading and reconciliation rather than building.

---

## 4 · Test which policy forms get attached

### What it means

Pricing is half the job. The other half is **which endorsements and forms end up on the policy** —
the documents that define what's actually covered.

**Nothing we have tests this at all.**

The useful part: **508 of ISO's 570 packages ship real sample submissions** — 510 files in total —
and we've been testing against about 50. They're the natural material for this.

### Why it matters

Right premium, wrong forms is still a wrong policy — and it's the half that shows up in a coverage
dispute rather than an audit.

### Size

Medium to large, but with a lot of ready-made material.

---

## 5 · Let carriers use their own rates — **the commercial unlock**

### What it means

So far everything is ISO's filed rates. Real carriers **deviate**: they file their own version —
*"ISO's rate times 0.9 in Texas"*, their own factors, their own rules.

Two related pieces:

**(a) Letting a carrier author its own deviations.** They'd write them in a readable format that the
engine compiles down into the same shape ISO's own content uses. That's safe because *"ISO's answer,
times our factor"* **is already the shape of 4,598 rules in ISO's own files** — we're not inventing a
representation, just giving a friendlier front end to one the engine already runs.

**(b) Pinning a carrier to an older edition.** Carriers don't all adopt every ISO update. One may
still be filed on a 2023 edition in New Jersey while current in Texas. **Most of this already exists**
— we built it for backdating, and it turns out to be the same machinery. What's missing is being able
to say *"this carrier, this state, this date"* instead of just *"this state, this date."*

Both are stored **per state, always** — because that's how carriers actually file, even a national
deviation.

### Why it matters

**This is the difference between a demonstration and a product.** No carrier rates purely on ISO.

### The catch, and it's worth knowing before starting

**Once you layer a carrier's own content on top, ISO's service can no longer tell you whether the
answer is right.** The independent check we've relied on all along stops working. There's also an
open question whether ISO's service will even price an old edition — if it won't, pinned
configurations can't be externally verified at all.

**That's the argument for finishing the proving work first.** The ISO baseline has to be trustworthy
on its own before we build on top of it.

### Size

The largest build. The resolver change is small; the configuration, storage and the *refuse rather
than guess* cases are the real work.

---

## 6 · Tighten the checking of what customers send us

### What it means

When a submission arrives, we check every field against ISO's list of legal values for that state.

For **29 of 90** fields where the legal values depend on another answer, we get this exactly right.
For the other **61**, we fall back to a broader list. That list **never rejects something legal** —
it just might accept something that isn't, and ISO would then reject it.

Every finding already says which of the two it is, so nothing is misleading.

### Why it matters

It's a politeness issue more than a correctness one: we'd rather tell someone their submission is
wrong immediately than have ISO tell them later.

### Size

Medium, and slow rather than hard — each field has to be worked out and verified individually. We
tried an automatic shortcut and it failed on evidence, so it's one at a time.

---

## 7 · Commercial Property — the next line of business

### What it means

Everything above is General Liability. The same approach should work for Commercial Property, and
we've read one of ISO's Property packages and written up how building rating works across all four
cause-of-loss forms.

**Your instruction stands: read further, build nothing.**

### Why that's right

The GL build is the argument. **Fifty-one steps of analysis came before a line of engine code**, and
the two findings that most changed the engine came from *running* ISO's content, not reading it. A
Property build started from one document would be starting where GL started, minus the fifty-one
steps.

### What next

Read a **state** Property package and see what it changes against the national one — and whether the
four-form structure survives contact with a second jurisdiction. Small, and it's reading.

---

## 8 · Housekeeping — small, and one of them actually matters

- **We have two testing harnesses that should behave the same and don't.** One got today's
  improvement — the ability to tell *"this option genuinely does nothing"* apart from *"we picked an
  option that does nothing"* — and the other didn't. **Two tools with one behaviour between them is
  how the next silent problem gets through.** Worth an hour.
- **A test that reads yesterday's saved answers instead of re-measuring.** It passed today against
  stale numbers. A test that can't fail when it should is worse than the thing it guards.
- **A package count quoted as 567 in several places when it's now 570.** Cosmetic.

---

## Deliberately not doing yet

**A browser for ISO's rate tables** — *"what rates exist here, and how do ours differ?"* Genuinely
wanted, and not speculative. But **what a given carrier is allowed to see depends on their ISO
subscription**, so it's a licensing question before it's a technical one. And the engine already
answers the question underwriters actually ask — *"what rated this policy, and why"* — because every
rating returns the full chain of factors with the source of each.

**The self-correcting loop** — the comparison running continuously with the expert agents
adjudicating each difference. Worth building **once there are differences to adjudicate.** On one
kind of business there mostly aren't.

---

# If you want a one-line recommendation

**Do item 1.** Geography has stopped teaching us anything — the last four states we tested found
nothing. The coverage grid reading *1 of 19* is now the most honest statement of what we haven't
proven, and it's the first thing a carrier will press on.

**Then item 2**, because it's the last known defect and it's half-solved already.

**Item 5 is the commercial prize**, and it's the one I'd hold back longest — the moment we build it,
we lose the independent check that has found every defect so far.
