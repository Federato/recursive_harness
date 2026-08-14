# Backlog — 14 August 2026

**Written 2026-08-13, at the end of the day all six stages were completed and the engine was first
compared against ISO's live service.**

Ordered by what I would do first and why. Every item names the open item it closes, so nothing here
is a new idea invented overnight — each is something today's work surfaced and recorded.

**Two sections.** *Defects* — three things known to be wrong, added 2026-08-14 — come first. *The
numbered work* follows, unrenumbered so references elsewhere still resolve.

---

# Defects — ahead of the numbered work

**Added 2026-08-14.** Three things breadth and the variable tester found. They sit above the
numbered items because these are *known wrong*, where everything below is *not yet known*. The
numbered items keep their numbers so references elsewhere still resolve.

## D1 · A state that has no value never falls back to the national one — **OI-88** `HIGH`

**In English.** ISO's rules constantly say *"use the state's number, and if the state hasn't filed
one, use the national number."* We handle that fine most of the time. But when the answer has to be
worked out through a calculation first, the engine treats *"the state has nothing"* as an error and
stops, instead of shrugging and going to look for the national number. A whole class of ordinary
fallbacks therefore never happens.

**Why it is first.** Falling back from state to national is how most of ISO's content actually
works — Georgia, for one, files **no deductible factors of its own** and takes all fourteen tables
from countrywide. A defect in the fallback path is a defect in the mechanism the layering depends
on, and it is not visible on any risk simple enough to avoid the arithmetic.

**Evidence.** The first defect an external oracle has found. Turning `SizeOfRiskRatingApplies` to
`Yes` in Oklahoma makes our engine refuse; **ISO rates it at 8816**. A null inside a `FirstNonNull`
branch refuses instead of yielding null, so every countrywide fallback arriving through arithmetic
is unreachable.

**To close:** fix the null-through-arithmetic behaviour, then re-run the size-of-risk variants in OK
and NY against the live service. Expect it to unblock more than the one case that exposed it.

## D2 · Two counts of how a jurisdiction locates a risk, and they do not reconcile — **OI-91** `HIGH`

**In English.** For terrorism, the engine has to tell ISO where the risk is — but states don't agree
on how to say it. Some want a terrorism territory code, some want a ZIP code. We have two counts of
which states want which, taken two different ways, and they don't line up. Nobody has written down
which count a caller should trust, so anything filling in a submission is guessing.

**The two measurements.** By *which domain table the field names*: **4** jurisdictions declare
`TerrorismTerritory` (CA, FL, NY, TX) and **11** use `TerritoryCodeByZipCode`. By *does the
jurisdiction resolve any legal value for the field as of 2026-08-01*: **15** with an explicit
`TerrorismTerritory`, **16** with a ZIP domain, **20** with neither.

**They may both be right.** Naming a domain table and that table resolving to a non-empty set for a
date are different questions, and the 20 may simply not offer the coverage. That is exactly why it
needs settling rather than picking.

**Why it is high.** A tester that guesses sends the wrong field to **20 jurisdictions**, and the
figures are quoted in three places — `validate.PLACE_CODED`, the E8 escalation and R22 — so
whichever reading wins, more than one document moves. Today `variants.Declared.terrorism_place`
returns `None` rather than guessing, and the tester reports terrorism `NOT APPLICABLE` there with
the reason attached. Correct, and it means terrorism breadth is blocked in those 20.

**To close:** run the two measurements side by side over the same packages and dates.

## D3 · Schedule rating is gated on something no field declaration can show — **OI-89** `MEDIUM`

**In English.** Schedule rating is where an underwriter moves the premium up or down for features of
the risk. We sent a submission turning it on with a legal credit, and the premium didn't move —
nothing failed, it simply did nothing. ISO only applies it when a separate experience-rating measure
is credible enough, and that condition lives inside a rule where no field declaration can reveal it.

**How it was found.** By a variant that *did nothing* rather than one that failed —
`ScheduleRatingModificationApplies=Yes` with `SRPClassificationPct=10%`, both values from ISO's own
declared domains.

**Why medium, not high.** Nothing is wrong with the engine here — it is doing what ISO filed. What
is missing is that the condition is invisible to anyone constructing a submission, so a rating plan
can be requested and silently not applied. That is a documentation and validation gap, not a wrong
number.

**To close:** characterise the gate, then decide whether the engine should say *"requested, not
applied, because…"* rather than staying silent.

---

# The numbered work

## 1. Breadth against the live service — **OI-87**

**The single most valuable thing available.** Our engine agrees with ISO on 50 of 50 jurisdictions,
on every published field — but **every one of those 51 submissions is the same risk**: one location,
one classification, class `50017`, gross sales, no deductible, no rating plans, terrorism off.

Stage 4 chose that deliberately so differences between states would be attributable, and it did its
job. It is now the limiting factor. **Fifty matches on one risk shape is a narrower claim than it
sounds**, and ISO's service will rate anything we send it.

**What to vary, roughly in order of how much of the engine it exercises:**

| | Exercises |
|---|---|
| Deductibles (six kinds, BI/PD/BIPD × prem-ops/products) | a whole factor chain currently always zero |
| Multi-location and multi-classification | allocation, and the `ForEach` aggregation that was silently wrong once |
| Size-of-risk rating | the interpolated banded lookups, built but never exercised by a real submission |
| Claims-made form | a coverage form no sample uses |
| Experience and schedule rating | the rating plans, and the ±25% cap (R15) |
| Terrorism on | the coverage that cost 18 and was missing for a week |
| The other sublines — liquor, owners & contractors, pollution, railroad, product withdrawal | coverages no sample has ever priced |

`scripts/phase2_compare.py` already takes any submission; the work is generating the submissions,
and stage 4's `Schema.legal_values()` says what each field may contain.

**Expect this to find defects.** It should — that is the point. The offline and live comparisons have
both been clean precisely because the population is narrow.

---

## 2. Close the rounding question — **OI-70**

**The oldest open question in the project, now half answered and cheap to finish.**

Today proved against the live service that **ISO rounds rather than truncates** — `ROUND_DOWN`
changes the premium in 37 of 51 jurisdictions and ISO agrees with rounding in all 50. Arkansas
supplied a genuine tie (a product of exactly `1.5000`) where truncation gives 7,871 and ISO gives
7,872.

**What is left is one experiment.** Half-up and half-even differ on **0 of 51** submissions, because
the only tie in the whole population is `1.5`, where both give 2. Of 1,529 rounding operations across
every sample, exactly one is a true tie.

**Build a submission that produces `x.5` with `x` even** — where half-up gives `x+1` and half-even
gives `x` — and send it to ISO. One call settles it.

The medical-payments charge is the most promising site: it is `loss cost × 0.003 × exposure ÷ 1000`
rounded to whole pounds, and the exposure is ours to choose. Solve for an exposure that lands the
product on `2.5`.

---

## ~~3. Puerto Rico~~ — **decided, not backlog (OI-86)**

**Closed the same day it was written.** The subscription does not cover GL PR and the entitlement is
not available, so **Puerto Rico is disregarded going forward** — the user's decision, 2026-08-13.

It is implemented rather than noted: `NO_ISO` in `scripts/raas.py` is the one definition, and the
comparison script, the batch runner and the single-submission comparison all leave PR out and say
why. Naming PR explicitly still runs it, so this reverses in one command.

**The consequence stays live and is not to be dropped quietly.** PR still rates offline, and it is
the one jurisdiction with **no external confirmation of any kind** — no entitlement and no stored
priced example (OI-79). Every live-agreement count is therefore **`n of 50`**, and a PR premium
should be presented with that said out loud rather than left for a reader to find.

---

## 4. The referral register against ISO's own — **OI-81, OI-82**

Our register is **28 conditions derived by hand** from the rules and the manuals; **ISO declares 838**
in a workbook shipped inside every package (`DOC/*.xlsx` → `Refer to Company`), each with the manual
rule number, the form number and *Customer Implementation Guidelines*.

They are not the same population — ours are rating failure modes, ISO's are manual-level refer
instructions — but **the 14 conditions we carry and do not detect should be checked against ISO's
declaration before another one is derived.** Five of the fourteen can produce a wrong number:
`R12, R15, R17, R25, R26`.

---

## 5. Make dependent-domain validation exact — **OI-84**

29 of 90 dependent domains resolve exactly; the other 61 fall back to a superset that can accept an
illegal value but never reject a legal one. Every finding already says which of the two it is.

Closing it needs either ISO declaring the rest, or a per-field mapping derived and **verified one at
a time** — name-based resolution was tried and rejected on evidence today, because
`GeneralAggregateLimit` is keyed by a field name that does not exist.

---

## 6. Form attachment, using the 508 STC submissions — **OI-83**

**508 of 570 packages ship sample submissions** — 510 JSON files — and we have been testing breadth
against 50. They were set aside today as the right tool for **form attachment** testing specifically,
which nothing currently exercises.

---

## 7. Phase 4 authoring — **three decisions taken 2026-08-14**

Taken in conversation on 2026-08-14, when the multi-carrier question was put directly: *would
carriers see the tables, and could they add their own rate factor?* Two of the three were the
questions `EXECUTIVE-SUMMARY.md` §6 left explicitly open. They are answered here; none is built.

### 7a. Deviations are authored in a friendlier format that **compiles** to ISO's

**Decided.** Not raw ERC. Carriers author in a human-legible form and the engine compiles it down to
the shape ISO's own content already has.

The reason the compile target is safe: *"ISO's answer, times our factor"* — the commonest deviation
there is — is **already the shape of 4,598 rules in ISO's own content**. We are not inventing a
representation, we are giving a readable front end to one the interpreter already executes.

**What this makes a build item:** a source format, a compiler, and — the part that must not be
skipped — **the compiled output has to be readable back**, because the compiled form is what actually
rates and therefore what has to be reviewable when a premium is disputed.

### 7b. Deviations are built and stored **per jurisdiction**, always

**Decided, and it follows the filing, not the convenience.** A carrier with a national deviation
still files it state by state. The build must mirror that: **a deviation is a jurisdiction-level
object, every time.** The national case is an authoring affordance — *"applies to all
jurisdictions"* — that fans out to per-jurisdiction content. It is never a distinct kind of thing
with its own storage or its own resolution path.

**This appears to dissolve the precedence question** that §6's decision 1 left open — *does a company
national deviation beat an ISO state exception?* If a national deviation simply **is** 51
jurisdiction filings, there is no national layer for a state exception to be weighed against, and the
four-deep chain flattens to three: company-state, ISO-state, ISO-countrywide. Recorded as a
consequence to confirm when Phase 4 opens, not as a decision already taken — the chain is C1 and
changing it deserves its own look.

The affordance carries its own obligations, all of them build work:

| | |
|---|---|
| **Fan-out is authored once, stored 51 times** | so a later single-state amendment is an ordinary edit, not a special case |
| **A jurisdiction may opt out after the fact** | a carrier files nationally, then withdraws in one state. That must not require re-authoring the other 50 |
| **Effective dates are per jurisdiction** | states approve on their own schedule; the same deviation will be live in 30 states and pending in 21 |
| **"Applies to all" must mean *all as of when it was authored*** | when a 52nd jurisdiction is added, an old national deviation must not silently acquire it |

The last row is the one that will bite. It is the same class of error as C2 — nothing looks broken,
the number is just wrong.

### 7c. Carrier visibility into the tables — **parking lot**, see below

Wanted, acknowledged, explicitly **not** near-term. Moved to the parking lot on 2026-08-14.

---

## 8. Carrier edition pinning — **raised 2026-08-14**

**The question:** carriers do not all adopt every ERC edition. A carrier may be filed to use an
edition from years ago. Can the engine be configured so that carrier rates on the edition it is
actually filed for, and never on a newer one?

**Yes, and most of it already exists** — built for backdating rather than for this, but the same
machinery.

| Already built | Where |
|---|---|
| Every edition ISO ever filed is retained, and running a non-current one is a first-class operation | `EditionResolver.editions()` returns all editions in force on or before a date, oldest first |
| *"Latest" is never "now"* — the resolver never assumes the newest edition | `resolve/resolver.py`, rule 2. The corpus holds 82 state packages effective **after** today |
| **The countrywide parent is the one the state package declares**, not the newest countrywide edition — and a missing parent is a hard failure, never a fallback | `resolve/resolver.py`, rule 4/5 (N5). For five states today the declared parent is not the newest |

**What is missing is one input.** Selection is keyed on `(jurisdiction, as-of)`; carrier pinning
needs `(carrier, jurisdiction, as-of)`, with the pin overriding the date-based pick at
`resolver.py:105`. Everything downstream already handles a non-current edition.

### Four things this must get right

1. **Pin per jurisdiction, not per carrier.** A carrier can be on a 2023 edition in NJ and current
   in TX. `(carrier, jurisdiction) → edition` — the same shape as item 7b, which is convenient.
2. **The parent follows the pinned state package, not the date.** Already enforced (N5), and it is
   the rule that makes pinning safe: without it, a pin would pair an old state package with a
   current countrywide one. Complete, plausible, wrong.
3. **Policy effective date and carrier adoption are separate axes.** A carrier on a 2023 edition
   writing a policy effective today uses the 2023 edition. Conflating *what was in force* with
   *what this carrier filed to use* is the failure mode.
4. **Refuse when the pin cannot be honoured.** A filed edition older than the corpus, or before
   `MIN_ASOF` (`20220901`, below which not all 51 jurisdictions resolve), must fail loudly rather
   than substitute the nearest. Consistent with how a missing parent is already handled.

### Two limits that are not engine problems

- **We can only serve editions ISO delivered.** A carrier filed on something older than the corpus
  reaches is a data-acquisition question.
- **Pinned configurations may not be externally verifiable.** ISO's service rates on the edition it
  selects — its response header currently confirms it used the same edition we resolved, in all 50.
  If the service will not rate an old edition, those configurations cannot be checked against the
  oracle. Worth establishing before anyone assumes every carrier configuration is provable.

**Sizing:** the resolver change is small. The configuration surface, the per-jurisdiction pin store
and the refusal cases are the actual work, and they overlap item 7b almost exactly — do them
together.

---

## Parking lot

Real work, wanted, deliberately not scheduled. Distinct from the numbered items above, which are
things to pick up; these are things to *not* pick up until something changes.

**The table browser.** *"What rate exists here, and how does ours differ?"* — browsing ISO's filed
content and diffing a carrier's deviations against it. Nothing about it is speculative: the tables
are already typed from ISO's own definitions (`gl_engine/erc/tables.py`) and already loaded by the
resolver, so this is a reader over content the engine holds, not new engine work.

Two things are worth knowing before it starts:

- **Per-rating visibility already exists.** The trace returns every factor that applied, in order,
  with its ERC source. The browser answers *"what rates exist"*; the trace already answers *"what
  rated this policy, and why."* The second is the question underwriters actually ask.
- **What a carrier may see is a licensing question, not an engine one.** Visibility into ISO's filed
  content depends on that carrier's ISO subscription, and it will constrain the browser per tenant.
  Puerto Rico is the precedent already in the build: it rates, and is never compared, because the
  entitlement is not there.

---

## Not tomorrow, but next

**Phase 3 — the self-correcting loop.** The comparison running continuously, with the two expert
agents adjudicating each difference against the manual and the data, and findings fed back as fixes.

**The argument for doing item 1 first:** a harness that adjudicates differences is worth building
once there are differences to adjudicate. On one risk shape there are none.

**Phase 4 — company deviations.** Deliberately last: the moment company content is layered on, no
external service can confirm the answer, so the ISO baseline has to be trusted first. **Item 7 now
carries its authoring decisions** — a friendlier format that compiles, and per-jurisdiction storage
always. Still last; better specified.

---

## Standing rules, carried forward

1. **Before deriving anything from examples, enumerate the directories and ask what each one is
   for.** Adopted today as rule #1, after it paid for itself four times.
2. **Every count is `n of N`, with `N` enumerated from the source.**
3. **When a new check passes on its first run, suspect it.** Confirm it can fail before believing it
   can pass.
4. **No engine code is written without an explicit go.**
