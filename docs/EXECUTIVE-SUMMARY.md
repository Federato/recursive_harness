# General Liability Rating Engine — Executive Summary

**Progress briefing. 12 August 2026.** Plain language; no insurance or engineering background
assumed.

> **This is the canonical document and it renders here on GitHub.** There is a formatted HTML
> version of the same content — [`THE-BUILD-END-TO-END.html`](THE-BUILD-END-TO-END.html) — which must
> be downloaded and opened in a browser, because GitHub shows HTML as source rather than rendering
> it.

---

## Why you are reading this

**This is a progress update and a sanity check, not a request for anything.** No approval, budget or
decision is being sought.

What it is for: **to make the reasoning visible early enough to be challenged.** If the direction is
wrong, or the effort is aimed at the wrong problem, that is much cheaper to find out now than after
the remaining five stages are built. Section 8 lists the specific places I would most want to be told
I am wrong.

### In one paragraph

We are turning ISO's General Liability pricing rules — the industry-standard rulebook every carrier
licenses — into something a machine can execute, with proof at every step that it matches what ISO
actually filed. **This is not the production system.** It is a working reference implementation plus
a complete, evidenced specification, so that when engineering builds the real thing they are
implementing a known answer rather than discovering one. The end state is a **self-checking harness**
that compares itself against ISO's own live rating service and reports its own defects.

**Three weeks of analysis are complete. The first of six build stages is working.**

---

## 1. What we are building, and why it is harder than it sounds

ISO publishes commercial insurance pricing rules two ways: **manuals** written for people, and
**data files** written for machines. We hold both — roughly 87,000 data files covering all 51
jurisdictions, and 1,122 manual documents.

The arithmetic of rating is trivial. It is multiplication. **The difficulty is that almost nothing in
these files means what its name suggests**, and the failure mode is not a crash — it is a complete,
plausible, wrong price with nothing to flag it.

Four examples, all measured, all real:

| The trap | What it costs if missed |
|---|---|
| **A zero is usually not a number.** Zeros in these files have **eight** distinct meanings. Sometimes zero is a price. More often it means *refer to an underwriter*, *not eligible*, or *price this another way* | Multiply by it and you write a **free policy** on exactly the risks meant for human review |
| **States rewrite national rules, and "empty" is a decision.** A state can replace a national rule with nothing at all, meaning *"we don't do this here"* — not *"use the national one"*. New York does it 151 times | Falling back to the national rule applies coverage the state has withdrawn |
| **The rules change by date, and one date changes almost everything.** On **1 April 2027**, 43 states change classification basis on the same morning | An engine that caches "the current rules" breaks that day |
| **Names lie, consistently.** One rule is named for one classification, tests a second, and writes to a field named after a third | Any logic keyed on names is wrong in ways testing does not surface |

**This is why the work has been analysis-first.** Every one of those was discovered by measurement,
not anticipated.

---

## 2. Where we are

```
ANALYSIS                                          BUILD
├─ Source collection & conversion       ████ done  ├─ 1. Load & resolve      ████ DONE
├─ Two independent specifications       ████ done  ├─ 2. The interpreter     ░░░░ next
├─ 14 coverage walkthroughs             ████ done  ├─ 3. Produce a premium   ░░░░
├─ Every count re-measured by date      ████ done  ├─ 4. State input formats ░░░░
├─ Referral rules + 13 decisions        ████ done  ├─ 5. Field/value catalog ░░░░
└─ Architecture decision                ████ done  └─ 6. Simple interface    ░░░░
```

**Three weeks. Zero production code until the specification was finished and signed off** — a
deliberate constraint set by the project sponsor and held to.

### What exists today

| Asset | Size |
|---|---|
| ISO data corpus, mapped and indexed | **567 packages**, 51 jurisdictions + national layer |
| ISO manual corpus, searchable | **1,122 documents**, 5 families, fully text-extracted |
| Coverage specifications ("walkthroughs") | **14**, one per rating item, each independently evidenced |
| Design rules that cannot be violated | **18**, each measured rather than asserted |
| Questions escalated to the business | **20** raised, 13 decided, rest tracked |
| Tracked open items | **69** |
| **Real ISO-priced example policies to test against** | **54**, covering 50 states |
| Automated expert reviewers (manual + data) | **2**, 107 self-checks between them |
| Reproducible analysis scripts | **57** |
| **Working engine code** | **1,814 lines** — stage 1 |
| **Engine tests** | 20 acceptance cases, 13 safety checks, green at two dates |

---

## 3. What stage 1 does, and why that piece went first

**It answers one question: given a state and a date, which rulebook applies?**

That sounds administrative. It is where **almost every catastrophic pricing error originates** — wrong
edition, wrong national rulebook underneath a state, or an empty table read as zero. Each produces a
finished, confident, wrong number.

So stage 1 is mostly a machine for refusing to guess:

- **It will not price before September 2022.** The files do not cover every state that far back, and a
  partial answer would look like a complete one.
- **It takes the national rulebook each state names for itself, never the newest.** California is on
  an older one and is the only state there; **five states today** would otherwise be priced against
  rules they never adopted.
- **An empty rate table is treated as an answer, not a gap.** It will show you the empty table; it
  refuses to calculate with it.

Every number it returns is tagged with the exact ISO file it came from.

### Building it immediately found things three weeks of reading had not

| Finding | Why it matters |
|---|---|
| **Three states hide their rates in per-territory files** with different names, and the obvious table is empty. **66,573 rows of rates** were being missed | An engine reading the obvious name prices from nothing, silently |
| **ISO is withdrawing an entire rating method.** We had filed this as unanswerable. At the 2027 date, states carrying it drop from **35 of 51 to 2 of 51**, and every state adopting the new national rulebook empties its own tables in step | Coordinated withdrawal, not an incomplete filing. **The answer was in *who adopts the rulebook*** — a question only the engine could ask |
| **`1.00` is being used as a placeholder** in a Texas table — 26 of 30 rows — so a $20m limit prices identically to a $50,000 one | We had catalogued **eight meanings of zero** and never asked what *one* meant, because **nothing multiplies when you are only reading** |

**That last row is the entire thesis of this project in miniature.** Running the content finds a
class of defect that reading it cannot. That is what the harness is for, and it showed up a stage
early.

---

## 4. The architecture decision, and the honest case for it

**The question:** should the engine *run* ISO's filed rules, or should engineers *read them and
rewrite them* in code?

Rewriting is how most rating engines get built. We chose to run them.

### The measurement

ISO's rules are written in a small instruction language:

```
58 kinds of instruction · 809,088 uses across the corpus
top 20 instructions ........ 94% of all uses
top 30 instructions ........ 98.5%
```

Implement that language once and **every state, every coverage and every future ISO filing comes
free.** The alternative is hand-writing roughly **4,461 rules per rulebook** — plus 345 more for
California, which is on a different one — and repeating the exercise each time ISO files an update.

### But that measurement is weaker than it looks, and we should say so

**It measures how *broad* the language is, not how *hard* it is.** Frequency is not difficulty. The
14 instruction types appearing fewer than 500 times could easily be the majority of the work — rare
constructs exist precisely because they do unusual things.

**The honest statement: the language is small enough that implementing it is tractable. Whether it is
cheap is not yet proven.** The decision rests better on maintenance economics than on the 94%.

### The three arguments that actually hold

**1. The maintenance treadmill is the whole game.** ISO files continuously — this corpus already
holds filings dated into 2027. With hand-written rules, **every filing is a development project, a
regression cycle and a release.** With an interpreter, a filing is a **file drop.** Over a five-year
life that difference dwarfs the build cost.

**2. The precedent runs this way — with one honest caveat.**

| | |
|---|---|
| **ISO's own RAaS** | ISO executes ERC as a service. **This is the existence proof, from the party that authored the format** |
| **Duck Creek** | Manuscript-driven: business logic including rating lives in XML the platform executes at runtime. The closest analogue |
| **Guidewire** | Rating *specifically* is configured metadata — rate tables and rating routines — executed by a rating engine. The wider platform is code (Gosu), so this is a hybrid, not a pure evaluator |
| **Tax, for comparison** | Nobody hard-codes sales tax. Vertex and Avalara are data-driven for the same reason: high-churn, externally authored, regulator-filed content |

**The caveat, stated plainly: none of the commercial platforms interprets ISO's ERC format natively.**
They interpret **their own** format, and ISO content is imported and converted into it — a conversion
that is itself a product or a project someone pays for. We should not assume that is an oversight.
A vendor format designed for execution is probably more tractable than a filing format designed for
distribution.

**That gives us a cheaper fallback than the one described below.** If ERC turns out to be painful to
evaluate directly, the retreat is not "rewrite everything in code" — it is **normalise ISO's content
into a simpler internal form first, then execute that**, which is what the vendors effectively do.

*(These are public architectural descriptions, not verified internals — unlike every other number in
this document, which is measured.)*

**3. It is the only version that reaches the stated end goal.** A self-correcting harness can adjust
an interpreter's semantics. It cannot meaningfully self-correct 100,000 lines of hand-written
business logic. **If the destination is self-checking, rewriting is a dead end you would have to
walk back out of.**

### The costs, stated as costs

| Cost | Severity | Where we stand |
|---|---|---|
| **Correlated failure.** One instruction's semantics wrong = wrong **everywhere**, silently. Hand-written rules fail locally and independently | **Serious** | Mitigated by 54 real ISO-priced policies — a systemic error shows up across many at once. **But we have not yet measured what those 54 exercise.** Owed before stage 2 ships |
| **Debugging inverts.** A wrong premium points into *data*, not code | Moderate | The provenance trace is designed for exactly this |
| **Business logic is not readable in the codebase.** An engineer sees `evaluate(node)`; the pricing lives in ISO's files | Moderate | Real tension with "a template for engineers". Answered by the specification being written down first, in English |
| **Performance.** Tree-walking is slower than compiled logic | Low | Irrelevant at quote volume; possibly relevant for batch re-rating |

### How this would be challenged, and the answers

| Challenge | Response |
|---|---|
| *"You're building a compiler. That's where projects die."* | It is not a compiler. It is a tree-walking evaluator over a fixed vocabulary — closer to a spreadsheet formula engine than a language runtime |
| *"Can we hire for this?"* | Yes. Once the semantics are written down it is mid-level work. **Writing them down is the senior work, and that is exactly what stage 2 produces** — which is the deliverable engineering needs |
| *"What's the bus factor?"* | Genuinely worse than rewriting. Mitigated only by specifying before coding, which is the standing rule here |
| *"Can we explain a price to a regulator?"* | Better than the alternative. Every number carries the ISO file it came from — a stronger audit story than "here is our Python" |
| *"What if it doesn't work?"* | **It is not a one-way door.** An interpreter that works can emit compiled code, and the semantics you had to write down become that code's specification. Rewriting first and interpreting later is far harder |

**The argument for a board is not the 94%.** It is: **vendor content updates become a configuration
change instead of a release.** That is a margin and time-to-market statement.

**The argument a sponsor should hear plainly:** we are taking **correlated risk** to buy
**maintenance leverage.** That is a defensible trade. It is not a free win, and it has not been
presented as one.

---

## 5. What remains

| Stage | What it delivers | Status |
|---|---|---|
| **1 · Load and resolve** | Which rulebook applies, for any state and date | **✅ Built and tested** |
| **2 · The interpreter** | Executes ISO's rules. **The only genuinely new engineering** | ▶ Next |
| **3 · Premium and referrals** | A submission goes in, a price and its components come out — in two modes | — |
| **4 · State input formats** | One sample submission per state, so differences are visible and attributable | — |
| **5 · Field and value catalogue** | Every field a submission can carry and its legal values, from ISO's own tables | — |
| **6 · Simple interface** | Paste a submission, price it, read every factor | — |

**Then, and only then:**

| Phase | What it delivers | When |
|---|---|---|
| **Proof against RAaS** | The engine's answer compared against ISO's own live service, risk by risk. Any difference is our defect until proven otherwise | After stage 6 |
| **The self-correcting harness** | That comparison run continuously and automatically, with findings fed back as fixes | After proof |
| **Company deviations** | The carrier's own loss costs, factors, rules and coverages layered on top of ISO's | **Only once the ISO baseline is trusted** |

**Stage 2 is the critical path.** Its largest single piece is writing down what each of ISO's 54
instructions means — deferred deliberately during analysis because it was only needed if we chose to
run the rules. We chose to run them, so it is now due. **That written-down specification is the main
thing engineering inherits**, and it is worth more than the code around it.

**Two modes, one code path**, from stage 3 onward:

- **Strict** — reproduce ISO exactly. Any difference from ISO's live service is our defect.
- **Underwriting** — enforce the carrier's own referral rules. This is what would ship.

**The difference between the two modes is itself a report:** every risk where ISO would quote and we
would stop and ask a human.

---

## 6. Company deviations — built later, designed for now

**No carrier rates pure ISO.** Every one files deviations: its own loss cost multiplier, its own
class relativities, its own increased-limit factors, coverages ISO does not offer, and rules ISO does
not have. **A rating engine that cannot express those is a demonstration, not a system.**

**They are deliberately not in the first phase.** The first phase builds ISO's content and proves it
against ISO's own service. Deviations come after that, for one reason:

> **Deviations break the oracle.** ISO's RAaS rates *ISO content*. The moment company content is
> layered on, no external service can confirm the answer is right. **Deviating from a foundation you
> have not yet proven means you can never tell whether a difference is your deviation working or your
> engine failing.**

### But the design has to anticipate them now

**This is where the architecture pays off.** Layering is already how the engine works — a state's
rules override the national rulebook today, by name, wholesale, and an override may deliberately be
empty. **A company layer is the same mechanism with one more level, not a new concept.**

And because the engine executes content rather than code:

| | A company deviation is… |
|---|---|
| Hand-written rating code | **A code change.** Edited, reviewed, regression-tested, released |
| This design | **Content.** Same shape as ISO's own — diffable, reviewable by actuaries, versioned by effective date, and it inherits every safety check already built |

The commonest deviation shape — *"ISO's answer, times our factor"* — is already the shape of 4,598
rules in ISO's own content, so the machinery arrives free.

### Three design decisions being taken now, before stage 2

**1. Two layers become an ordered chain.** The real stack is four deep — company-state,
company-countrywide, ISO-state, ISO-countrywide. Cheap to build in now; expensive once stage 2 is
written against a two-layer assumption. **The non-obvious part is not the code, it is the precedence
question:** does a company *national* deviation beat an ISO *state* exception? That is a filing
decision, not a default, and it must be answered per carrier.

**2. ISO's own rules keep ISO's meaning.** When an ISO rule says *"do what my parent does, then
adjust"*, it means **ISO's national package** — a meaning ISO fixed when it filed. If a company layer
were inserted in the middle and that instruction resolved through it, **we would silently rewrite
ISO's rules.** Two ideas that must never be conflated: *ISO's declared parent* (fixed, semantic) and
*our layer chain* (ours, compositional). Conflating them produces wrong prices that look entirely
reasonable.

**3. Behaviour and content are independent axes.**

|  | ISO content only | ISO + company |
|---|---|---|
| **Strict** | The RAaS comparison baseline — **must stay permanently runnable** | Company rating, no referral policy |
| **Underwriting** | ISO rating with the carrier's referral rules | **What would actually ship** |

Keeping strict/ISO-only permanently runnable is what allows the ISO foundation to go on being
verified against RAaS forever, even after deviations exist on top of it.

### Two questions deliberately left open

**How deviations get authored.** In ISO's own format — best for the engine, verbose for humans — or
in a simpler overlay we convert. Worth deciding against a real deviation, not in the abstract.

**Whether ISO's vocabulary can express everything a carrier wants.** ISO's 58 instructions express
what ISO needed. A tier factor, a model score, or a rating step ISO does not have may not be
expressible, and would need a vocabulary extension or an escape hatch to code. **That limit is real
and should be found on a real deviation rather than guessed at.**

---

## 7. Proving it against ISO's own service

**RAaS — Rating as a Service — is ISO executing its own content.** Send it a submission, get back a
premium. Run the same submission through our engine in strict mode, and compare.

```
   submission ──┬──→  ISO RAaS          ──→  ISO's premium
                │
                └──→  our engine        ──→  our premium
                       (strict mode)
                                              │
                                              ▼
                                    DIFFERENCE?  →  our defect,
                                                    until proven otherwise
```

**Most of this can start before the connection exists.** The 54 ISO-priced example policies covering
50 jurisdictions are already on disk — enough to find systemic errors offline.

### The honest gap in the test set

**None of the 54 carries loss history**, so experience rating — the part that prices on a customer's
own claims record — **has no offline answer key at all.** It can only ever be checked against the
live service.

And a measurement owed before stage 2 ships: **which instructions and coverages do those 54 actually
exercise?** They are the safety net under the biggest architectural risk in section 4, and we have
not yet measured how wide the net is.

---

## 8. The ultimate goal — the recursive harness

```
        ┌──────────────────────────┐
        │   ISO's live service     │  ← the gold standard
        │        (RAaS)            │
        └───────────┬──────────────┘
                    │ same submission
                    ▼
   ┌────────────────────────────────────┐
   │   our engine, in STRICT mode       │
   └───────────┬────────────────────────┘
               │
               ▼
   ┌────────────────────────────────────┐
   │  DIFFERENCE  →  every gap is       │
   │  either our defect or a finding    │
   │  about ISO's own content           │
   └───────────┬────────────────────────┘
               │
               ▼
   ┌────────────────────────────────────┐
   │  two automated expert reviewers    │
   │  adjudicate against the manual     │
   │  and the data files                │
   └───────────┬────────────────────────┘
               │
               └──→ fix, re-run, record. Repeat.
```

**Not connected yet, by instruction.** The 54 ISO-priced example policies do most of this offline
first, and **strict mode exists precisely so the comparison is meaningful when the connection is
made.**

### "Self-learning" and "self-fixing" — what those honestly mean

The phrase covers four different things with very different difficulty. Being precise matters,
because **only the first two are ordinary engineering.**

| Level | What it does | Realistic? |
|---|---|---|
| **1 · Self-checking** | Notices that our answer differs from ISO's, and records it with full provenance | **Yes.** Ordinary engineering. The trace layer is already designed for it |
| **2 · Self-diagnosing** | Localises *which rule, which table, which instruction* produced the difference — not just that the total is wrong | **Yes**, and this is where the interpreter earns its keep: every number knows what computed it |
| **3 · Self-fixing** | Proposes — and for a bounded class, applies — a correction: an instruction's semantics, a sentinel's meaning, a rounding rule | **Yes, for a bounded class.** Because the engine executes content, a fix is usually a change to a semantics table rather than to logic scattered across a codebase |
| **4 · Self-learning** | Generalises a correction into a rule that prevents the whole class — e.g. *"any factor that breaks monotonicity is a sentinel until proven otherwise"* | **Aspirational, but already happening by hand.** That exact rule was written this week, from one Texas table |

**Two limits to state before anyone assumes otherwise:**

- **It can only ever self-correct against ISO content.** The oracle is ISO's service, which rates
  ISO's rules. **Nothing external can score a carrier deviation** — see section 6.
- **Not every difference is our defect.** Some are findings about ISO's own content; three turned up
  on the first day of coding. The harness must be able to conclude *"we are right and this needs
  escalating"*, which is why the two expert reviewers sit in the loop rather than an automatic
  patcher.

### Why this matters more than the rating engine itself

The rating engine is the **first** line of business. The harness is the **method**, and it is
transferable:

1. **It finds defects reading cannot.** Already demonstrated — three findings on the first day of
   coding, one of which closed a question we had filed as unanswerable.
2. **It produces a specification, not just software.** Every finding is written up with its evidence.
   Engineering inherits *decisions with reasons*, not code to reverse-engineer.
3. **It generalises.** A companion document records, for each stage, what the analysis was *expected*
   to supply versus what it *actually* supplied — written **before** each stage so it can be wrong.
   That is what tells a future team which of these steps to repeat for Commercial Property or
   Business Owners, and which to skip.

---

## 9. Risks, stated honestly

| Risk | Mitigation | Residual |
|---|---|---|
| **Correlated semantic error** in the interpreter | 54 real ISO-priced policies; strict mode; two expert reviewers | **Real.** We must first measure what those 54 actually exercise |
| **The rare instructions cost more than the common ones** | Spike the hardest ten first, not the commonest twenty | Unproven either way |
| **ISO content we cannot interpret at all** | 20 escalations raised so far; the engine **refers to a human** rather than guessing | By design, not eliminated |
| **Key-person concentration** | Specification written in English before code; everything reproducible from scripts | Higher than a rewrite. Accepted knowingly |
| **Hawaii is absent from every source** | Documented scope boundary; the engine must fail loudly if asked | Out of scope, stated |

**One discipline is doing most of the risk work.** Sixteen corrections are recorded across this
project and **nearly all are the same mistake: something measured in one place, then stated about
everything.** The standing rule is now that **every count is stated as "n of N", and N must be
enumerated from the source rather than assumed.** A second rule was added this week: **when a new
safety check passes on the first run, suspect it** — twice a check's condition has been narrower than
its name, and the second one passed while blind.

---

## 10. Where I would most want to be told I am wrong

**Nothing here is blocked and nothing needs a decision.** These are the four places where an outside
view is worth more than another week of my own work.

**1. Is the destination right?** This is aimed at a **self-checking harness that produces a
specification**, on the premise that engineering's expensive problem is not writing rating code —
it is knowing exactly what to write, and knowing when it is wrong. If the real constraint sits
somewhere else entirely, the shape of this is wrong regardless of how well it is executed.

**2. Is the architecture trade acceptable?** Section 4 states it plainly: **correlated risk bought in
exchange for maintenance leverage.** I believe the trade is right and the reasoning is laid out
including the parts that weaken it. It is the single most consequential decision made so far and the
one most worth a second opinion.

**3. Is "not the production system" being taken seriously enough?** The value here is the
specification and the evidence, not the code. If sponsors are reading this as an attempt to build a
shadow production system, that expectation needs correcting now.

**4. Is the pace of escalation right?** 20 questions have been raised for the business, 13 answered.
The standing rule is that anything ISO's files cannot settle **stops and asks a human** rather than
being guessed at. That is deliberately conservative. If it is too conservative for how this would
actually be used, that is worth knowing before the referral logic is built into stage 3.

### What happens next regardless

Two low-cost items before stage 2 commits, both measurable against files already held:

1. **Measure what the 54 priced policies actually exercise** — which instructions, coverages and
   states. It is the missing safety net under the biggest risk in section 9.
2. **Spike the ten hardest instructions first, not the twenty commonest.** The common ones are almost
   certainly fine. This either validates the architecture in a week or kills it cheaply.

Then stage 2, on the same terms as everything so far: **each stage is shown before the next begins** —
what it does, what it was checked against, and what it cannot yet do.

---

## Where to read more

| For | Document |
|---|---|
| The same content as formatted HTML *(download to view)* | `docs/THE-BUILD-END-TO-END.html` |
| Plain-English account of the current state | `docs/WHERE-WE-PAUSED-2026-08-12.md` |
| Full status and history | `docs/PRD-GL-RATING-ENGINE.md` |
| The six stages in detail | `docs/BUILD-STAGES.md` |
| Every command, to run any of it yourself | `TESTING.md` |
| What was built, what broke, what it revealed | `BUILD-LOG.md` |
| Did the analysis pay off? (written before each stage) | `docs/FROM-PLANNING-TO-BUILD.md` |
| Everything unresolved | `docs/OPEN-ITEMS.md` |

Everything in one page: `docs/GL-RATING-ENGINE-DOCS.html`.
