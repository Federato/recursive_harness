# gl-authority

The agent that reads **all** of it — ISO's content, ISO's manuals, and our code — and answers the
questions that don't respect the boundaries between them.

## Why it exists

The other three are each walled off on purpose:

| | Sees | Cannot see |
|---|---|---|
| `iso-erc-expert` | ISO's ERC corpus | the manuals, the code |
| `iso-circular-expert` | ISO's manuals and circulars | the ERC corpus |
| `gl-engine-code-expert` | our Python | anything that isn't source |

Those walls are what make each one trustworthy. But a real question — *"is a deductible used in
Georgia?"*, *"which form attaches here?"*, *"why is this premium what it is?"* — touches two or three
at once. Ask a specialist and you get a third of an answer, delivered confidently.

`gl-authority` is allowed to look at everything. **The obligation that makes that safe is that every
claim names the source it came from.**

## The one thing to understand before using it

**The two ISO corpora were built independently, and `iso-erc-expert` is explicitly forbidden from
reading `iso-circular-expert`** — *"consulting it destroys the independence of this one."*

That independence is the point. When two separately-built corpora agree, the agreement is evidence.
An agent holding both in one head **can destroy that**, which is why the definition spends a whole
section on it:

- Never reason from one source into the other. A manual describing a mechanism does not put that
  mechanism in ERC.
- Agreement counts only when it was independent — measure ERC first, *then* check the manual, never
  the reverse.
- Disagreement is the finding. ERC's value stands, the conflict is named, never resolved silently.

That is the project's own evidence doctrine (`PROCESS_LOG.md`, standing criteria, 2026-08-10) made
operational: **tier 1 sources, tier 2 confirms, tier 3 is a person, and the code is the thing being
checked** rather than an authority in its own right.

## What to ask it

```
"is a GL deductible used in Georgia?"
"which form attaches for liquor liability in Texas, and when?"
"does our engine do what ISO filed for size-of-risk in Oklahoma?"
"what does PremOpsBIPDDeductible mean, and what do we do with it?"
"which edition governs a policy effective last March in New Jersey?"
```

Anything where you don't know which of the three holds the answer — that's the case it's for.

## What it will not do

- **Supply from the manuals what ISO's content lacks.** The single failure mode the doctrine exists
  to prevent.
- **Smooth over a conflict between sources.** It names both sides and escalates.
- **Opine on whether a rate is appropriate** or what a policy should cost.
- **Cite a document for behaviour.** `BUILD-LOG.md` records intent; the code records what happens.
  Where they differ, that's a finding.

It answers in plain English first, then technically with a source on every claim. `unverifiable` is a
first-class answer here.

## Not a router

It reads the sources itself rather than delegating to the other three. Their `AGENT.md` files are
worth reading for their exact conventions, but they are **definitions of discipline, not services to
call.** No nesting, no orchestration, no chance of a specialist's refusal being lost in a summary.

## Where it lives

Registered at [`.claude/agents/gl-authority.md`](../../.claude/agents/gl-authority.md) — the only
location Claude Code discovers. `AGENT.md` here is the same instruction body, kept alongside the
other agents so all four read together. **They are copies, not links — edit one, edit both.**
