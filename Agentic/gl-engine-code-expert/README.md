# gl-engine-code-expert

An expert on **the Python that rates a General Liability submission** — the interpreter, the rating
kernel, edition resolution, table access and the schema. It answers from the source code, not from
the documentation.

Sibling to [`iso-erc-expert`](../iso-erc-expert/), and the division between them is the useful part:

| | Authority on |
|---|---|
| `iso-erc-expert` | **ISO's content** — what the corpus says, what a table holds, which package governs |
| `iso-circular-expert` | **ISO's manuals and circulars** — what the filed rules require |
| **`gl-engine-code-expert`** | **Our code** — what the engine actually does with any of it |

Ask the first two what ISO filed. Ask this one why a rating came out the way it did.

## Quick start

The agent is registered for Claude Code at
[`.claude/agents/gl-engine-code-expert.md`](../../.claude/agents/gl-engine-code-expert.md) — that
file is the live definition and the only location Claude Code discovers. `AGENT.md` here is the same
instruction body, kept in the Agentic tree alongside the other agents so all three read together.

**If you edit one, edit both.** They are copies, not links.

```
Ask: "how is a GL deductible used in Georgia?"
     "why does size-of-risk refuse in Oklahoma?"
     "what would have to change for a carrier to rate on an older edition?"
```

## What it will and won't do

- **Source is evidence.** Markdown, HTML and `docs/` are not. Docstrings are, because they are
  source. Where code and document disagree, **the code wins and the conflict is reported.**
- **Two registers by default** — plain English first, then the mechanism with `file:line` on every
  behavioural claim.
- **The UI is out of scope.** `app.py`, `ui/` and anything serving HTTP.
- **It runs the engine** rather than reasoning about it, for anything empirical. This needs the ERC
  corpus present at `GL_ERC_ROOT`; without it, it reports the failure instead of reasoning around it.

## The trap the definition exists to avoid

**The engine contains no rating concepts.** No deductible module, no territory logic, no per-state
branch — because jurisdictional difference is ISO's content, not our code. Grep `deductible` across
the engine and you get **one hit**, in `rating/referrals.py`, and it is a referral message.

An agent that greps, finds that, and concludes the engine barely handles deductibles is **wrong in a
way that sounds researched**. So rating questions get answered in two halves: the **mechanism**,
which is entirely in the code, and the **boundary**, where the values live in ISO's corpus. §6 of
`AGENT.md` walks that case.

## Verified

Tested 2026-08-14 on *"how is a GL deductible used in Georgia?"*. It found that **Georgia files no
deductible factors of its own** — all fourteen `Ded*` tables are owned by countrywide and every row
is `CW` — rated six variants to show the effect, and proved the state→countrywide retry is **ISO's
filed rule rather than ours** by grepping `'CW'` across `gl_engine/interp/` and getting zero matches.
Both load-bearing claims were independently re-checked before the answer was accepted. Written up in
[`BUILD-LOG.md`](../../BUILD-LOG.md) entry 16.

## No knowledge or tools directory

Deliberate. `iso-erc-expert` and `iso-circular-expert` carry pre-computed `knowledge/*.json` because
their corpora are large, external and slow to measure. **This agent's corpus is the repository it is
already standing in** — about 5,000 lines of engine plus 14 test suites. Pre-computing facts about
code that changes every session is how a knowledge file starts lying. It reads the source each time.
