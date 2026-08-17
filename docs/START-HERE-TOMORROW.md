# Start here tomorrow — Tuesday 18 August 2026

**Yesterday closed six defects, raised one question for you, and built the QA programme.** Nothing is
blocked. This is what to pick up, in the order I would pick it up.

The full diary is [`BUILD-LOG.md`](../BUILD-LOG.md) Entry 28. The plain-English version of what the
day taught is [`what-the-harness-taught-us_20260817.html`](what-the-harness-taught-us_20260817.html).

---

# 1 · The first thing, and it takes one call

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

# 2 · Tuesday's 60 calls, in order

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

# 3 · Waiting on you — five things, none blocking

| | | Effort |
|---|---|---|
| **C1** | **Tell ISO we are running a validation programme.** Do this before the week's calls. It removes a risk that costs nothing to remove — and gives you a reason to be in touch that is not a complaint, because **we found a genuine defect in their data** | One email |
| **C2** | **Report that defect.** In 13 jurisdictions ISO's own service returns a 400 whose body is *their* rule engine failing to find a row in *their* own table. They probably do not know. I can draft it | One email |
| **B1** | **A loss cost multiplier.** Everything ISO files is pre-multiplier — every number we have compared is a loss cost, not a rate. One representative LCM turns loss-cost testing into **premium** testing | One number |
| **OI-95** | **A question, not a bug.** ISO's manual says *"refer to an underwriter"* where ISO's data file says **zero** — 178 times in Texas alone. We price those as zero and tell nobody. **But ISO's own service does the same thing**, and we have a verified match proving it. Is that intended, or a seam everyone lives with? Neither ISO document answers it | A judgement |
| **A3 follow-up** | Once the 2027 probe answers, decide whether to run the 2027 tier now or in January | A sentence |

---

# 4 · What is left in the backlog

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

# 5 · How far are we from a UI?

**Further than "there is no UI" and closer than "it is ready." There is a working one — the honest
question is what kind you mean.**

## What exists today, and works

| | |
|---|---|
| `/` | Rate one submission. Every factor in the order used, with the ISO file each came from. Referrals. Per-coverage breakdown |
| `/tester` | **19 controls**, every option read live from ISO's own tables per state. Run across all 51. Our premium, ISO's premium, the difference |
| **QA tab** | Whole test tiers behind a button, **with the cost shown before you press it** and a budget that refuses to overspend |
| **Charts** | Agreement over time · coverage grid · premium response curves · **a US map** · a one-screen verdict |
| **History** | Every run kept permanently, with a defect register that tracks first-seen and last-seen |

**That is a real internal tool and it is being used.** Yesterday's work was driven through it.

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

# 6 · If you only do three things tomorrow

1. **Send `results/refused-payloads/TX-714439816b85/request.json`.** One call, settles 36 payloads
   and closes an open question about our own fix.
2. **Email ISO** (C1 and C2 together). One message: here is what we are doing, and here is a defect
   we found in your data.
3. **Run `python scripts/qa.py --tier T1 --offline`.** Three minutes, free, and it tells you what
   tomorrow's live calls should be aimed at.
