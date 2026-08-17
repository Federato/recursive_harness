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

## A2 · Is an invented-but-legal risk acceptable as a test subject?

**What's blocked:** multi-location, multi-class, varied exposure — three of your four stated goals.

**The situation.** Every stored submission is one location, one classification. To test multi-location
I must **invent** a risk: two locations in different territories, two classifications, chosen
exposures. Every value would come from ISO's declared legal set, so ISO will price it — but **it
corresponds to no real policy anyone has written.**

**The question:** is "legal but synthetic" acceptable, or do you want these shapes to resemble
business we actually write?

**What it unblocks:** multi-location and multi-class testing, immediately.

**If you don't answer:** I proceed with synthetic-but-legal and label it as such. **This is the
default I'd recommend anyway** — the arithmetic doesn't care whether the risk is real, and waiting
for realistic shapes would block the work for weeks.

---

## A3 · Do we test the 2027 basis now, or wait?

**What's blocked:** the whole effective-date axis.

**The situation.** **43 jurisdictions change basis on 1 April 2027** — minimum premiums deleted
outright, 25 class codes withdrawn. The content is already in the corpus. We could test it today,
seven months early.

**The trade-off.** Testing early finds problems while there's time to fix them. It also spends effort
on rules that may be amended before they take effect.

**What it unblocks:** T4, and the ability to tell a carrier what changes for them next April.

**If you don't answer:** I build the axis (it's needed regardless — the current inconsistency is a
defect either way) but **do not run the 2027 tier** until you say so.

---

## A4 · New York: whose class count wins?

**What's blocked:** nothing today, but every NY figure carries an asterisk.

**The situation.** **ISO's machine-readable content declares 1,191 class codes for New York. ISO's own
filed manual profile says 1,181.** Same vintage, so it isn't an edition artefact. **The two sources
ISO publishes disagree with each other by ten codes.**

Our engine follows the machine-readable content, because that's the standing rule — the content is
what actually rates.

**The question:** do we (a) keep rating on 1,191 and report the gap, (b) exclude the ten disputed
codes from NY testing, or (c) raise it with ISO first?

**If you don't answer:** (a) — continue on 1,191, report the discrepancy on every NY result. It's the
current behaviour and it's honest.

---

## A5 · How real does a loss history need to be?

**What's blocked:** experience rating, and therefore **schedule rating on premises/operations** —
the last known defect (OI-89).

**The situation.** Schedule rating only applies when the account's own claims experience is credible
enough. To exercise that we need about **twenty dated fields of claims history** — losses, dates,
policy periods.

**The question:** may I generate a synthetic loss history that satisfies ISO's declared field rules,
or do you want it based on a real (anonymised) account?

**What it unblocks:** OI-89, the last item on the known-defect list.

**If you don't answer:** synthetic, built from ISO's declared field rules, labelled as synthetic.

---

## A6 · Am I authorised to spend the ISO call budget without asking each time?

**What's blocked:** the pace of everything.

**The situation.** §13 of the proposal sets **150 calls/day, ~220/week recurring**. Today I asked
before each live batch. That's the right instinct for a first day and the wrong pattern for a
programme.

**The question:** a standing budget I work within, or explicit approval per run?

**If you don't answer:** I keep asking before each live batch. Slower, and safe.

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
