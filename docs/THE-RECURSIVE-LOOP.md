# The Recursive Loop — Validating Against ISO RAaS and Making Fixes

**A plain-language explainer.** What "the loop" actually is, what of it is built today versus
aspirational, and what it has found so far. No insurance or engineering background assumed.

---

## 1. The idea in one picture

```
   submission ──┬──→  ISO RAaS (live)   ──→  ISO's premium
                │
                └──→  our engine        ──→  our premium
                       (strict mode)
                                              │
                                              ▼
                                    DIFFERENCE?  →  our defect,
                                                    until proven otherwise
```

**RAaS — Rating as a Service — is ISO executing its own rules, live, over the network.** Send it a
description of a business (a "submission"), get back a premium. We send the *same* submission
through our own engine, running in **strict mode** — reproduce ISO exactly, no carrier opinions
layered on — and compare the two answers field by field, not just the total.

Any difference is treated as **our defect until proven otherwise.** That's a deliberate stance: it
puts the burden of proof on our engine, not on ISO's live service.

---

## 2. The full loop — four stages

```
ISO's live service (RAaS)
        │ same submission
        ▼
our engine, strict mode
        │
        ▼
DIFFERENCE → either our defect, or a finding about ISO's own content
        │
        ▼
two automated expert reviewers adjudicate against the manual and the data files
        │
        └──→ fix, re-run, record. Repeat.
```

**Why two reviewers, not an auto-patcher.** Not every difference is our bug — some are genuine
findings about ISO's own filed content (three turned up on the very first day of coding). The loop
has to be able to conclude *"we are right and this needs escalating to ISO or the business"*,
which is why adjudication sits in the loop rather than a script that blindly patches whatever
disagrees.

---

## 3. What's actually built today, concretely

This isn't just a diagram — the pieces exist and run:

| Piece | What it does |
|---|---|
| `scripts/qa.py` | Runs a **tier** of test scenarios (a pairwise-generated matrix of variables, not every combination), with a cost estimate shown **before** any ISO call is spent, and a budget that refuses to overspend |
| **Offline-first pattern** | `python scripts/qa.py --tier T1 --offline` costs nothing and catches build errors and refusals before a single live call is made |
| **Daily call budget** | A ticker, not a hard gate — currently 60 calls/day, two sittings, business hours, kept deliberately unremarkable traffic |
| `scripts/qa_review.py` | The adjudication pass — three verdicts, reading ISO's own CSVs rather than trusting our own code's opinion of itself |
| `runstore.py` | An **append-only** store of every run, so history is never silently overwritten |
| `/tests` page | The layered test programme — four layers (smoke → classification → limits → deductibles), pause/resume/stop, one standalone HTML report per run, an aggregate table, a verdict card per layer, and a trend chart |
| `/review/<run>` page | A run can be reviewed **without an API key** — a mechanical pattern match for the easy cases, a markdown brief for what it can't explain on its own, and a place to paste back a human verdict |
| Defect register | Every finding is tracked with **first-seen** and **last-seen**, not deleted once fixed |

**The two expert reviewers referenced in the loop diagram** are separate agents that read the
filed ISO manuals and the machine-readable data files independently, and adjudicate a
disagreement against both.

---

## 4. The four levels of "self-X" — and which are real

"Self-learning" and "self-fixing" get used loosely. Here's what each level actually means, and how
realistic it is:

| Level | What it does | Realistic? |
|---|---|---|
| **1 · Self-checking** | Notices our answer differs from ISO's, records it with full provenance (which file, which rule, produced the number) | **Yes — built, ordinary engineering.** |
| **2 · Self-diagnosing** | Localizes *which rule, which table, which instruction* produced the difference, not just that the total is wrong | **Yes — this is where the interpreter earns its keep.** Every number knows what computed it |
| **3 · Self-fixing** | Proposes — and for a bounded class, applies — a correction: an instruction's meaning, a sentinel value, a rounding rule | **Yes, for a bounded class.** Because the engine executes ISO's content rather than hand-written code, a fix is usually a change to a semantics table, not logic scattered across the codebase |
| **4 · Self-learning** | Generalizes a correction into a rule that prevents the whole class of error — e.g. *"any factor that breaks monotonicity is a placeholder until proven otherwise"* | **Aspirational, but already happening by hand.** That exact rule was written from one Texas table this pass |

**Two honest limits, stated plainly:**

- **It can only ever self-correct against ISO content.** The oracle is ISO's own live service,
  which rates ISO's own rules. Nothing external can score a carrier's own deviations from ISO —
  that's why carrier-specific rating is deliberately built last (see §6).
- **Not every difference is our defect.** The loop has to be able to say *"ISO's content itself
  looks wrong here"* and escalate, rather than silently forcing agreement.

---

## 5. Where the loop stands right now

| Check | Result |
|---|---|
| Standard risk, all entitled jurisdictions | **50 of 50** agree on the premium and every field ISO publishes |
| Varied risks, 11 jurisdictions | **184 of 184** comparable outcomes agree |
| Rulebook edition selection | ISO's own response header confirms the correct edition was picked, in all 50 |
| Validation messages | Our reading of ISO's rules produces ISO's own wording |
| ISO's own worked example (Oklahoma) | Reproduced exactly |

**The honest caveat that belongs next to every one of those numbers:** all of this has tested one
narrow slice of *what a risk looks like* (largely one class family), proven broadly across
*geography*. Widening geography has stopped finding new defects — the last several states added
found nothing. What hasn't started yet is varying **what kind of business** is being rated.

---

## 6. What the loop doesn't do (yet, or ever, by design)

- **It doesn't run unattended.** Live ISO calls are made deliberately, in business hours, inside a
  daily budget — not on a schedule, by design, until that's an explicit decision.
- **It can't validate carrier-specific rates.** The moment a carrier's own deviations are layered
  on top of ISO's content, no external service can confirm the answer independently anymore. That's
  exactly why carrier deviations are the last thing built, not an oversight.
- **It doesn't auto-apply every fix.** Reviewer adjudication stays in the loop for anything outside
  the bounded "self-fixing" class in §4.

---

## 7. Where to read more

| For | Document |
|---|---|
| Full technical status of the GL engine | `docs/PRD-GL-RATING-ENGINE.md` |
| The layered `/tests` programme, design and rationale | `docs/UI-STRATEGY.md` |
| Day-by-day record of what the loop has found and fixed | `BUILD-LOG.md` |
| What's still open | `docs/OPEN-ITEMS.md` |

---

**Document history:** written 2026-08-21, drawn from the current state of `docs/PRD-GL-RATING-ENGINE.md`,
`docs/EXECUTIVE-SUMMARY.md`, and `docs/START-HERE-TOMORROW.md`. Kept separate from those so this page
answers one question — *what is the recursive loop and how far along is it* — without carrying
their day-by-day history.
