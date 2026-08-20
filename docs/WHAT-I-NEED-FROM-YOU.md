# What I need from you to unblock the untestable — 17 August 2026

> **Updated 2026-08-19 — four more answers, and one of them reframes an escalation into a build.**
> **B1** is settled at `1.0` · **C1** is declined · **C2** is held pending more testing of our own ·
> **A3's open half is answered** — ISO does rate a future effective date, so the effective date
> becomes a test variable rather than a question. Separately, **OI-95 stops being a judgement call**:
> the direction given names the discriminator, and the table that carries it exists and was measured
> the same day. See each item below, and `OPEN-ITEMS.md` OI-95.

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

> ### ✅ The open half is answered — 2026-08-19
>
> **ISO will rate a future effective date.** So the 2027 tier has an oracle, and the question of
> *whether* to build it is no longer gated on a probe.
>
> **What replaces it is smaller and better shaped: the effective date becomes a test variable.**
> Not a separate tier run at a second date, but an axis alongside class, limit and deductible —
> one control, set per scenario, carried into the payload and into the as-of resolution together so
> the two cannot disagree. That is the same fix the axis defect needed anyway; making it a *variable*
> rather than a *mode* means the 2027 cliff gets exercised by ordinary test cases instead of by a
> parallel programme.
>
> **This unblocks the as-of date selector** in `START-HERE-TOMORROW.md` §1, which was held back
> because a dropdown offering dates the rating ignores is worse than no dropdown.
>
> **Not built. Backlog only.**

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

## B1 · ~~A loss cost multiplier~~ ✅ **DECIDED 2026-08-19**

> **Decision: hold the LCM at `1.0`.** What we are testing right now is **ISO's RAaS service against
> our engine** — and every number on both sides of that comparison is a loss cost. **This is not a
> client-facing application**, so there is no policyholder premium to be wrong about yet.

**Why `1.0` is the right placeholder and not a fudge.** At `1.0` the multiplier is present in the
chain, positioned correctly, and provably inert — so the day a real LCM arrives it is a value change,
not a structural one. Picking an invented number like `1.55` instead would make every stored result
carry a fabricated figure that looks like a rate, and comparisons against ISO would have to divide it
back out. **The comparison stays exact at `1.0` and stops being exact at anything else.**

**What this leaves open, stated on results rather than buried:** we can prove the loss cost is right
and say nothing about the premium on a policy. That limitation is now a **decision**, not a gap —
revisit it when there is a client application or a carrier filing to test against, and at that point
the *shape* question still needs answering: single number, or varying by state / subline / class.

<details><summary>The original ask, kept for the record</summary>

**What's blocked:** testing the premium a policyholder actually pays.

**The situation.** **Everything ISO files is pre-multiplier.** Every number we've ever compared is a
loss cost, not a rate. The carrier's LCM converts one to the other, and it is an input by design —
ISO does not and will not supply it.

**What I need:** one representative LCM (even a placeholder like 1.55) — and ideally the *shape*:
is it a single number, or does it vary by state, by subline, by class?

**What it unblocks:** end-to-end premium testing. Without it we can prove the loss cost is right and
say nothing about the premium on the policy.

**If you don't answer:** I keep testing at loss-cost level and state that limitation on every result.

</details>

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

## C1 · ~~Tell ISO we're running a validation programme~~ ❌ **DECLINED 2026-08-19**

> **Decision: not sending it. Our usage is within what a subscriber does.**

**What changes as a result: nothing operationally, and one thing in how I report.** The pacing rules
stay exactly as they are — strictly serial, business hours, inside the daily standing budget — because
those were adopted to keep the traffic unremarkable, and that reasoning is unaffected by whether a
note went out. **What I stop doing is treating this as an open item**; it is closed by decision, not
parked.

**The residual risk, stated once and not repeated:** if ISO ever does query the volume, the answer is
the run history, which is complete and timestamped. That is a good answer. It is simply arriving
after the question rather than before it, which is the trade being made here deliberately.

<details><summary>The original ask, kept for the record</summary>

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

</details>

---

## C2 · Report the size-of-risk data gap to ISO — ⏸ **HELD 2026-08-19, pending more testing of our own**

> **Decision: not yet. More testing first.** The finding stands; what is not yet established is its
> full shape, and a report that has to be corrected afterwards is worse than one sent a week later.

**The finding, as it actually stands.** In **13 jurisdictions**, ISO's own rating service returns a
400 on a valid size-of-risk submission. Not a validation error — **ISO's rule engine failing to find
a row in ISO's own table**: `Matrix: PremOpsSizeOfRiskLossCost, Keys: CW, 502, 50017. No results have
been found.` All 13 were confirmed by direct call, each bypassing our own refusal.

**Corrected 2026-08-19 — this section previously overstated the agreement.** It used to read *"our
engine now refuses the same submissions for the same reason, so we agree with ISO's behaviour."*
**OI-94's adversarial review refuted the "same reason" half:** the captured 400 body is the **Georgia**
call (`502` is a Georgia territory) and names `PremOpsSizeOfRiskLossCost`, a *rating-plan* matrix,
while our own refusal originally blamed `PremOpsLossCost` — which in Texas is a healthy 9,504-row
table that resolved correctly. **We agree with ISO on the outcome. Whether we agree on the cause is
proven for Georgia and inferred elsewhere.** Any report sent to ISO must claim only the former.

### What the additional testing needs to establish before this goes out

| | |
|---|---|
| **The TX refused payload** | `results/refused-payloads/TX-714439816b85/request.json` — one call. It is the cheapest way to turn *"ISO refuses for the same reason"* from inference into measurement in a second state, and it settles 36 payloads across 4 states besides |
| **Capture the full 400 body per jurisdiction** | We have 13 confirmations that ISO returns a 400 and one body quoted in full. A report naming a table should quote that table from more than one state's response |
| **Whether it is the class or the state** | Every confirmed call used class `50017`. Whether the gap is *"this plan is unfiled in these 13 states"* or *"this class is missing from the plan"* changes what ISO is being told, and no test has separated them |
| **The corroboration we already have, and should lead with** | The 35 jurisdictions whose ERC size-of-risk table is populated are **exactly** the 35 with a *Size Of Risk Rating Supplement* circular — no difference in either direction, ERC measured first. **Two independent ISO sources agreeing is a stronger opening than a stack trace** |

**Still not blocked on you.** When the testing above is done I will draft it and bring it back with
the evidence attached, rather than leaving it as a standing ask.

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

**As of 2026-08-19 the A and B lists are answered, and nothing on this page is waiting on you.**

| | |
|---|---|
| **A1–A6** | All decided 2026-08-17 |
| **A3's open half** | Answered 2026-08-19 — ISO rates a future date; the effective date becomes a test variable |
| **B1** | Decided 2026-08-19 — LCM held at `1.0`, because RAaS comparison is loss-cost against loss-cost |
| **C1** | Declined 2026-08-19 |
| **C2** | Held 2026-08-19 — the finding stands, the report waits on our own testing, and I bring it back drafted |
| **B2 · B3 · C3–C6 · D1 · D2** | Unchanged, all with working defaults |
| **OI-95** | No longer a question for you — the direction given on 2026-08-19 names the discriminator, and it is a build item now. See `OPEN-ITEMS.md` |

**Everything else has a working default**, and none of it is blocked waiting for you. Where I proceed
on a default, the assumption is stated on the results rather than buried.

<details><summary>The original four-item ask, kept for the record</summary>

1. **A1** — say yes or no to using ISO's shipped sample submissions. *Unblocks seven sublines and form attachment.*
2. **C1** — tell ISO we're running a validation programme. *Removes a risk that costs nothing to remove.*
3. **A6** — give me a standing call budget or keep approving per run. *Sets the pace of everything.*
4. **B1** — one loss cost multiplier. *Turns loss-cost testing into premium testing.*

</details>
