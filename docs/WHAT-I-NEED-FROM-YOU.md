# What I need from you to unblock the untestable — 17 August 2026

**Purpose.** Section 12.4 of the [QA proposal](qa-plan-proposal_20260817.html) lists what we cannot
test today. This is the other side of that list: **the specific things only you can supply**, what
each one unblocks, and — importantly — **what I will do by default if you never answer**, so nothing
sits blocked waiting on a decision.

**How to read it.** Items are ordered by *how much they unblock per unit of your effort*, not by
size. Several take a single sentence from you.

| | |
|---|---|
| **A** | Decisions only you can make — minutes each, no cost |
| **B** | Data or documents I need supplied |
| **C** | Things that need ISO — subscription, clarification or permission |
| **D** | Things that need a carrier |

---

# A · Decisions only you can make

*These cost nothing but a sentence, and five of them unblock the largest items on the list.*

## A1 · ~~May I use ISO's own shipped sample submissions?~~ ✅ **DECIDED 2026-08-17**

> **Decision: read them as reference, rebuild our own payloads from ISO's declared domains.**
> Nothing of ISO's is copied into this repository.

**Why that shape of answer.** This repo deliberately excludes ISO content — notebook outputs are
stripped precisely because they would embed ISO's licensed values. Copying 513 ISO files into
`Engine_Payloads/` would have reversed a principle the project already committed to. Reading them to
learn what a real Liquor or Railroad risk *looks like*, then generating our own payload from ISO's
declared legal values, keeps both the benefit and the principle.

### What they actually contain — measured 2026-08-17, and it is less than first claimed

**513 files across 508 packages, inputs only — no priced outputs, so they are not oracles.**
Every case built from them still needs a live call to establish truth.

| Subline | Files | Buildable today? |
|---|---|---|
| Premises/Operations **and** Products/Completed Operations | **473** | already buildable |
| Premises/Operations · Products/Completed Operations | 8 each | already buildable |
| Owners and Contractors · Railroad | 8 each | **no — this helps** |
| Liquor | 3 | **no — this helps, thinly** |
| Product Withdrawal | 2 | **no — this helps, very thinly** |
| **Pollution · Electronic Data · Underground Storage Tank · Special Protective** | **0** | **no — and this does not help at all** |

**Correction to the first draft of this document.** It claimed A1 would unblock "seven sublines".
**It unblocks four of the eight, thinly, and leaves four with no example at all.** The figure was
written before the files were measured.

**Two further corrections:**

- **Multi-location: this does *not* unblock it.** 508 of 510 submissions are single-location; exactly
  **2** carry two locations.
- **Multi-class: better than claimed.** **116 files carry more than one classification** — 84 with
  two, 14 with three, 18 with four. Real evidence of how ISO shapes a multi-class risk, and the most
  useful thing in the whole set.

### What this decision unblocks

| | |
|---|---|
| **Multi-class shapes** | 116 worked examples to model our generated payloads on |
| **Four sublines** | Owners & Contractors, Railroad, Liquor, Product Withdrawal |
| **Still blocked** | Pollution, Electronic Data, Underground Storage Tank, Special Protective — no example exists; these must be built from the declaration alone, or left until ISO supplies one |

## A2 · ~~Is an invented-but-legal risk acceptable?~~ ✅ **DECIDED 2026-08-17**

> **Decision: anchor on ISO's own worked examples, then extend them.**
> Multi-class shapes follow the pattern of the **116 STC submissions carrying 2–4 classifications**;
> multi-location is built by extending those into a second declared territory.

**What this means in practice.** Not real business, but **not arbitrary either** — shaped the way ISO
shapes its own examples. Every value still comes from ISO's declared legal set, so the submission is
one ISO will price and the comparison stays valid.

**How results must be labelled.** *ISO-derived synthetic.* Strong enough to say *"the arithmetic is
correct on shapes ISO itself considers representative"*; **not** strong enough to say *"we tested
business like yours"* to a carrier. That second claim needs real profiles (see A2-follow-up below).

**Why not free invention.** A defect in deductible ordering is wrong on an invented risk and a real
one identically, so free invention would find defects just as well. It is the *reporting* that
differs: a coverage grid full of arbitrary shapes reads as more assurance than it is.

**Left open, deliberately.** If a carrier later asks *"have you tested what I write?"*, the answer is
still no. Re-running the same matrix against real profiles is a **second pass**, not a redesign —
the matrix is the same, only the shapes change. Cost is roughly the live calls on the overlap.

---

## A3 · ~~Do we test the 2027 basis now, or wait?~~ ✅ **DECIDED 2026-08-17**

> **Decision: fix the effective-date axis now; probe ISO with one call before committing to any
> 2027 testing.**

**Two things were separated, because they had different answers.**

**The axis is not optional and is being fixed regardless.** Today's behaviour is inconsistent — the
legal values offered come from one date while the engine rates at another. That is a defect whether
or not 2027 is ever tested.

**Whether we then run tests at the 2027 date is deferred until one fact is known:**
**will ISO's live service rate a future effective date at all?** If it will not, the 2027 tier has
**no oracle** and becomes a self-consistency exercise — a completely different piece of work, and one
that should be scoped differently. Building the tier before knowing that would be guessing.

**Scheduled as Tuesday 18 August's first live call.** Today's budget is spent (92 of 150), and the
pacing rule in §13 of the proposal says zero more today. Making an exception an hour after writing
the rule would make the rule decorative, and waiting a day costs nothing while decisions are still
being taken.

**What is at stake, for context.** On 1 April 2027, **43 of 51 jurisdictions change basis on the same
morning.** Rule 14 is deleted outright — classification-level minimum premiums, the per-subline
highest-of rule, the "if any" provision and ~25 special combined mercantile classes all vanish, which
**changes the premium on small risks.** The class list drops from **1,188 to 1,163**. Rules renumber,
with Rule 22 and Rule 35 changing meaning entirely.

---

## A4 · ~~New York: whose class count wins?~~ ✅ **DECIDED 2026-08-17**

> **Decision: exclude the ten disputed class codes from testing.**
> New York is tested on the **1,181 codes both ISO sources confirm**.

**The disagreement.** ISO's machine-readable content declares **1,191** GL class codes for New York;
ISO's own filed manual profile says **1,181**. Same vintage — not an edition artefact, and not our
misreading. All 20 NY territory tables carry the identical 1,191 set, so it is not a partial-table
problem either. **This is the first case where ISO's two publications contradict each other on a
matter of fact.**

**The consequence, stated because it is easy to miss.** Excluding the ten from the *test set* does
not remove them from the *engine* — **our engine still rates on 1,191**, because the standing rule is
that the machine-readable content governs. A real submission using one of those ten codes **will
price, and will be untested.**

**So New York results must say:** *"agrees on the 1,181 codes both ISO sources confirm"* — never an
unqualified pass. The ten are **reachable but unverified**, and that phrasing is required on any
New York coverage claim.

**Still available later, cheaply.** The ten are testable directly: if ISO's live service prices them,
the machine-readable content is vindicated and the manual profile is stale. About ten calls whenever
someone wants the question closed rather than bounded.

---

## A5 · ~~How real does a loss history need to be?~~ ✅ **DECIDED 2026-08-17**

> **Decision: synthetic, built from ISO's declared field rules, and constructed to span the
> credibility threshold** — one history just below, one just above, one comfortably above.

**Why spanning matters more than realism.** Experience rating is *statistical*: credibility depends
on the size and volatility of the loss history relative to expected losses. **A single synthetic
history could be constructed to produce whichever answer was wanted** — too clean and it sails past
the threshold, too thin and it never reaches it. Testing at one point would prove nothing.

Testing *across* the threshold tests the gate, which is what OI-89 is actually about: the condition
is invisible to anyone building a submission, so a rating plan can be requested and silently not
applied.

**What this unblocks.** OI-89, the last item on the known-defect list, and with it the other side of
the schedule-rating gate. Measured today: with the switch and a percentage set, schedule rating moves
the premium in exactly **three jurisdictions — FL, NY and RI — and does nothing in the other 48**,
all three confirmed against ISO's live service.

**What it does not tell us.** Whether real accounts typically clear the credibility threshold. That is
a different question, answerable only with real histories, and it is not what the defect is about.

**Labelled synthetic on every result.**

---

## A6 · ~~Am I authorised to spend the ISO call budget without asking?~~ ✅ **DECIDED 2026-08-17**

> **Decision: a standing budget of 60 live calls per day, with a weekly report.**
> Above 60 in a day, or any new tier, needs an explicit go.

**Why 60 rather than the plan's 150.** The pacing rules in §13 of the proposal set 150/day as the
*ceiling* — the point above which traffic stops looking like ordinary use. 60 is the *working*
budget. The constraint that matters is total spend, not per-batch permission, and a lower standing
number preserves a real checkpoint without stalling work every time an approval is needed.

**What I decide alone:** which jurisdictions, which combinations, and when within the day.
**What I never decide:** how many. The ceiling is fixed.

**What I report weekly:** calls spent, what they bought — defects found, coverage gained, questions
settled — and a flag the moment a week runs over budget, rather than at the end of a month.

**Consequence for the schedule.** The one-time calibration of ~1,050 calls now spreads over roughly
**four to five weeks** instead of two and a half. Slower, and the pace is sustainable without anyone
watching it.

---

# B · Data or documents I need supplied

## B1 · A loss cost multiplier

**What's blocked:** testing the premium a policyholder actually pays.

**The situation.** **Everything ISO files is pre-multiplier.** Every number we've ever compared is a
loss cost, not a rate. The carrier's LCM converts one to the other, and it is an input by design —
ISO does not and will not supply it.

**What I need:** one representative LCM (even a placeholder like 1.55) — and ideally the *shape*:
is it a single number, or does it vary by state, by subline, by class?

**What it unblocks:** end-to-end premium testing. Without it we can prove the loss cost is right and
say nothing about the premium on the policy.

**If you don't answer:** I keep testing at loss-cost level and state that limitation on every result.

---

## B2 · A real carrier deviation filing, if one is available

**What's blocked:** the design of Phase 4 authoring — the commercial unlock.

**The situation.** We've decided deviations are authored in a friendlier format that compiles to
ISO's shape, and stored per jurisdiction. Both decisions were made from first principles. **Neither
has been checked against a filing anyone has actually made.**

**What I need:** one real example — even redacted, even from a public filing — showing how a carrier
actually expresses a deviation.

**What it unblocks:** confidence that the authoring format matches how carriers think, before we
build it. Cheap now, expensive later.

**If you don't answer:** I design from ISO's own content shape, which we know is
*"ISO's answer × our factor"* in 4,598 rules. Defensible, unvalidated against practice.

---

## B3 · Which carriers pin which editions, if any

**What's blocked:** prioritising carrier edition pinning, and knowing whether it's testable at all.

**The situation.** The machinery mostly exists. What I don't know is whether this is a real
requirement with real examples, or an anticipated one.

**What I need:** any known case of a carrier filed on an older edition — carrier, state, edition.

**If you don't answer:** treated as anticipated, built last, and tested with synthetic pins.

---

# C · Things that need ISO

*These need someone with the ISO relationship. I can draft the message for any of them.*

## C1 · Tell ISO we're running a validation programme **← do this first**

**What's blocked:** nothing yet. **This is insurance against a problem.**

**Why now.** We spent 92 calls today and the plan is ~220/week ongoing. That's a change in pattern.
A short note describing the programme — licensed subscriber, validating against your own filed
content, strictly serial, under 150 requests a day, business hours — **turns unusual traffic into an
expected activity.**

**And it gives us a reason to be in touch that isn't a complaint.** We found a genuine defect in
ISO's data today (C2). Leading with *"here's what we're doing, and here's something we found for
you"* is a better first contact than a support ticket after someone notices our traffic.

**If you don't answer:** I stay within the pacing rules, which should keep us unremarkable. But the
risk isn't zero and it's cheap to remove.

---

## C2 · Report the size-of-risk data gap to ISO

**What's blocked:** nothing of ours — this is us being a good subscriber, and it's leverage.

**The finding.** In **13 jurisdictions**, ISO's own rating service returns a 400 on a valid
size-of-risk submission. Not a validation error — **ISO's rule engine failing to find a row in ISO's
own table**: `Matrix: PremOpsSizeOfRiskLossCost, Keys: CW, 502, 50017. No results have been found.`

Our engine now refuses the same submissions for the same reason, so we agree with ISO's behaviour.
But **ISO probably doesn't know**, and it means size-of-risk cannot be rated at all for that class in
those states.

**What I need:** someone to send it. I'll supply the exact request, the response, and the list of
affected jurisdictions.

---

## C3 · Puerto Rico entitlement — get it, or close it

**What's blocked:** PR can be rated but **never verified**. It is the one jurisdiction with no
external check of any kind.

**The question:** is PR in scope commercially? If yes, we need the entitlement added. If no, let's
record that decision permanently so every future report says *n of 50* without re-litigating it.

**If you don't answer:** current behaviour — PR rates offline, is excluded from comparison, and every
count is stated as *n of 50*.

---

## C4 · Hawaii — does GL exist there?

**What's blocked:** whether "all 50 states" is even the right goal.

**The situation.** **Hawaii is not in ISO's corpus at all.** Not empty — absent. I don't know whether
ISO doesn't file GL in Hawaii, or whether our subscription excludes it.

**What I need:** one question to ISO. The answer changes what we can claim: *"all 51 jurisdictions
ISO files"* is very different from *"all except Hawaii, which we can't explain."*

---

## C5 · Three factual questions only ISO can settle

Small, and each removes an asterisk:

| Question | Why it matters |
|---|---|
| Does ISO accept an exposure above **9,999,999,999**? | ISO declares that ceiling; our engine ignores it. We don't know if the service enforces it |
| Is **PA territory 506** a data defect or an unreachable placeholder? | It's selectable, no ZIP maps to it, and no rate is filed for it |
| Is there a **maximum number of locations or classifications** per submission? | Nothing in ISO's content declares one. We'd be guessing at the ceiling |

**If you don't answer:** the first two can be settled with **one live call each** — I'd rather ask
ISO than probe their service to find a limit, but probing is available.

---

## C6 · May we make parallel calls?

**What's blocked:** wall-clock on the larger tiers, not the tiers themselves.

**The situation.** Our client is **strictly serial** — no concurrency, no rate limiting. The full
logic tier takes ~5h 50m purely because calls queue. Two or three in parallel would cut that
proportionally.

**Why I won't just do it:** going from one connection to several without telling them is exactly the
change that gets noticed, and §13's whole argument is that we look like ordinary use.

**If you don't answer:** stay serial. Everything still runs; slower.

---

# D · Things that need a carrier

## D1 · Minimum premium amounts

ISO files the *rule* and leaves the *amount* to the carrier — "refer to company." The same is true of
policywriting minimums and the classification-level minimums that Rule 14 governs until April 2027.

**Without them we can test that we refer, and never that the number is right.** If a carrier will
share a filed schedule, minimum-premium behaviour becomes testable.

## D2 · Rating plan parameters

**Schedule rating, experience credibility and size-of-risk are not in ISO's manual corpus at all** —
Rule 2.A.1 says only *"refer to company for any applicable rating plan modification."* They exist in
ISO's machine-readable content, which we execute, so ISO's live service is the **only** oracle for
them. There is no second source and no cross-check.

**A carrier's own plan filing would give us one.** Worth asking for if the relationship allows.

---

# The short version

**If you only do four things:**

1. **A1** — say yes or no to using ISO's shipped sample submissions. *Unblocks seven sublines and form attachment.*
2. **C1** — tell ISO we're running a validation programme. *Removes a risk that costs nothing to remove.*
3. **A6** — give me a standing call budget or keep approving per run. *Sets the pace of everything.*
4. **B1** — one loss cost multiplier. *Turns loss-cost testing into premium testing.*

**Everything else has a working default**, and none of it is blocked waiting for you. Where I proceed
on a default, the assumption is stated on the results rather than buried.
