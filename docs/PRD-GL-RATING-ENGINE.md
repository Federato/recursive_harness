# General Liability Rating Engine — Product Requirements & Current Build

**A plain-language document, written for a third party picking this project up.** What this
software does, why the problem is harder than it looks, how it was built and independently
verified, exactly what is built and confirmed today, and how to reproduce that verification
yourself.

**This document describes the built system, not the backlog.** For what remains, see
[`OPEN-ITEMS.md`](OPEN-ITEMS.md) and [`START-HERE-TOMORROW.md`](START-HERE-TOMORROW.md). For the
day-by-day build history, see [`BUILD-LOG.md`](../BUILD-LOG.md).

No prior knowledge of insurance rating or of this project is assumed.

---

## 1. What this is

A piece of software that takes a description of a business — what it does, where it is, how big
it is, how much coverage it wants — and returns the **price** for a General Liability insurance
policy, along with a full explanation of how that price was reached.

Producing that price has historically required a person to read a large printed manual and apply
dozens of rules by hand. This automates it.

**Two things make it more than a calculator.** First, the price must be *defensible* — an
insurance regulator can ask why a policy cost what it cost, and the answer has to point at a
specific page of a filed document. Second, the rules change constantly, and a policy written last
year must still be priceable under last year's rules, not today's.

---

## 2. Why this is hard

The pricing rules come from **ISO** (Insurance Services Office), an organisation that publishes
standardised insurance manuals that most US insurers license and build on. For General Liability
specifically:

**It is not one manual, it is three layers.** There is a national rulebook, a separate set of
exception pages for each of 51 US jurisdictions, and a separate publication of the actual
*prices* for each jurisdiction. All three are revised on different schedules. To price one
policy you need the right version of all three, as of the right date.

**The national layer has the method but almost none of the money.** The national rulebook
explains *how* to calculate, and then says, in its own words, that the actual factors *"are
displayed in the state exceptions."* This is confirmed in the data: in the national package, the
five key pricing tables contain **zero rows**. Every real number comes from a state.

**Blank does not mean zero.** The price tables are grids of business types against prices, and
more than a third of the cells contain something other than a number — a dash meaning *"we do not
offer this coverage for this type of business"*, or a marker meaning *"refer this to an
underwriter."* Software that reads those as `0.00` will hand out free policies and sell coverage
the manual explicitly declines.

**It is changing right now.** ISO is part-way through revising the list of business
classifications. Some jurisdictions have adopted it, some have not. There is no single correct
national list today.

---

## 3. How it was built — the method

The engine was built from two independent sources of ISO's content, cross-checked against each
other and then against ISO's own live rating service. Anyone replicating this approach should
expect to encounter the same structural traps; they are recorded here because each one changes
how the software has to be written, not just what it computes.

### Two sources, read independently, then compared

ISO publishes the same rating program twice: as **printed manuals** (PDF, ~503 rules documents
and ~472 loss-cost documents across 51 jurisdictions) and as **machine-readable data files**
(567 packages, ~87,000 files — structured tables and executable rule definitions). Both were
obtained and analysed **in isolation from each other** — the team reading the data files had no
access to conclusions already drawn from the PDFs, and vice versa. Where the two independently
reached the same conclusion, that agreement is real evidence rather than an echo: identical
territory counts and lists, identical classification-revision numbers (229 codes retired, 204
added), national factor tables matching digit for digit.

Each source also corrected the other. The data files supply exact package identity and filing
dates, closing a dating gap in the PDF-only analysis. The PDF manuals supply *meaning* the data
files don't carry on their own — most importantly, that the data files encode **"refer to an
underwriter" as the literal number `0`** in places (confirmed in at least eight places; for
drones over 55 lbs specifically, the data file says `0` where the manual says *Refer To
Company*). Software that trusts the data files alone will price those risks at $0.00 — precisely
the risks meant to get human review.

### The build rule

> **Build from the data files. Use the manuals to confirm the build, not to source it. Assume
> nothing that is not in the files. Where confirmation is needed, check the manuals. If that
> fails, ask.**

The manuals may tell you what something in the data files *means*. They may not supply a
calculation the data files don't contain — that would be inventing a mechanism. Following this
rule produces a shorter build and a longer list of questions that go to the business rather than
being answered by a silent default; that is a deliberate trade, not a shortfall.

### Coverage-by-coverage derivation

Each coverage (subline) is derived end-to-end from the data files, one at a time, and checked
against the filed manual before moving to the next — never surveyed in bulk. Doing it this way
surfaced traps that a bulk survey would have missed: the same coverage calculates differently
depending on the policy's effective date; a state can switch a rule off by filing an *empty* one,
and treating "empty" as "unchanged" charges a factor the state removed; validation messages carry
parts of the calculation and cannot be skipped; a coverage may read another coverage's *working
values*, so coverages cannot always be calculated in isolation; and the text label next to a rate
tells you which pricing path applies — a check that has agreed with the data over 620,000 times
without a single disagreement.

### Effective-date discipline

Every measurement of "what the data contains" must be taken **as of an explicit date** — the
corpus holds filings that have not taken effect yet, and counting them as current silently
describes a future state of the world as the present one. The defence is mechanical: the
project's own measurement scripts refuse to run without being told what date to answer for.

---

## 4. What's built and verified today

**All six build stages are complete and tested** — fifteen test suites. The engine has no
third-party dependency, and neither does the interface or the ISO comparison client.

**What it can do today:**

- Price a General Liability submission in any of 51 jurisdictions, for policies effective from
  September 2022 onward.
- Show every factor in the order it was used, with the ISO source file it came from.
- Refuse rather than invent a number when ISO's content cannot answer.
- Reproduce ISO's own validation messages.
- Compare itself against ISO's live rating service, from a browser or the command line.

**Seven sublines have been fully walked through, derived from the data files, and checked against
the filed manuals:** Premises/Operations (334), Products/Completed Operations (336), Owners &
Contractors Protective (335), Liquor Liability (332), Railroad Protective (335), the Product
Withdrawal / Electronic Data / Cyber group (365), and Unmanned Aircraft (370). Three of the seven
had no independent answer key and were derived from the files alone with the manual as
confirmation; two together reproduce a real ISO-priced Oklahoma policy to the dollar, as an
automated test.

**Confirmed by ISO's own service, not just internally:**

| Check | Result |
|---|---|
| Standard risk, all entitled jurisdictions | **50 of 50** agree on the premium and every published field |
| Varied risks, 11 jurisdictions | **184 of 184** comparable outcomes agree |
| Rulebook edition selection | ISO's own response header confirms the correct edition was picked, in all 50 |
| Validation messages | Our reading of ISO's rules produces ISO's own wording |
| ISO's own worked example (Oklahoma) | Reproduced exactly |
| Puerto Rico | **No external confirmation of any kind** — no entitlement, no published example; every PR count is honestly *n of 50*, not *n of 51* |

Outcomes are reported across four categories, kept separate on purpose: **agrees** · **differs**
· **not applicable** (ISO does not offer this coverage here — never counted as a failure) ·
**both refuse** (agreement, but counted separately, since calling a mutual refusal a "match"
would inflate the number that matters).

---

## 5. Scope

### In scope

| # | Requirement |
|---|---|
| R1 | Price a General Liability policy from a structured description of the risk |
| R2 | Cover sublines and coverages, built and reviewed **one at a time** — 7 walked through so far |
| R3 | Select the correct rules and prices **as of the policy's effective date** — never "the newest" |
| R4 | Resolve the national base and the state-specific overlay together, with the state package selecting its own national parent |
| R5 | Produce a full audit trail: every component of the price cites the document that authorises it |
| R6 | Treat *"refer to an underwriter"* as a normal, expected outcome — never an error, never a zero. The engine holds a register of confirmed places the data files express this as a `0`, and never multiplies by them |
| R7 | Run as a Python library and command-line tool |
| R8 | Be checkable automatically against both source sets, and repairable from those findings |
| R9 | **Source every value from the data files.** A price component with no data-file origin cannot be produced — enforced by the software's structure, not by review |
| R10 | **Escalate rather than assume.** Where the data files are silent and the manuals do not settle it, refer the risk and raise the question |

### Explicitly not in scope

- **No user interface.** Library and command line only.
- **No claims, policy administration, or billing.**
- **No pricing judgement.** The engine applies filed rules; it does not decide whether a price is
  adequate or competitive.
- **No other lines of business yet** — the approach is designed to extend, and most of what was
  learned is about how ISO publishes rather than about General Liability specifically. (This is
  the same approach the sister Commercial Fire project, `CF_Algorithm/`, was ported to.)
- **No live connection to ISO's own rating service for production pricing** — the connection
  point used for verification exists; a production integration is a separate, later effort.
- **No filling of gaps by inference.** Where ISO's data does not say, the engine does not decide
  on its behalf.

### The honest ceiling

This is the single most important expectation to set for anyone evaluating or extending this
system.

Of the 477 coverage units in the machine-readable data that produce a price, **18 calculate one
from rates. 383 capture a price a human has already decided** and apply a modifier to it, and 76
simply add other prices together. **Under 4% calculate.** That is not a limitation of this
software — it is what the source material contains. ISO's own data files declare roughly 5,300
situations that must be referred to an underwriter.

**"Calculates a price" is also not the same as "produces a final price."** Four of the seven
sublines walked through so far are **company-rated**: the filed manual says, in one sentence,
*"For rates, refer to company."* The data files supply a complete and correct calculation whose
starting multiplier is a placeholder of `1`, waiting for a number only the insurer can provide.
The engine produces a structurally complete, fully cited figure that is **an ISO expected-loss
value, not a market price**, until that multiplier is supplied.

**The realistic outcome is fully automated pricing for the core, high-volume coverages, and a
structured, well-documented referral for the rest.** No amount of engineering on this material
produces end-to-end automation of every coverage — the source content itself doesn't allow it.

---

## 6. Verification methodology — how to reproduce these checks

| Method | What it proves | How to run it |
|---|---|---|
| **ISO's own live service** | The broadest external check — same submission through both, compared on the premium *and every published field* | See `TESTING.md`; the ISO comparison client is in the CLI tooling |
| **ISO's own worked examples** | Fully rated real policies (54 across 50 states, one per state) with inputs and answer | `Payloads/` holds the input for each; the Oklahoma case runs as an automated test |
| **The manual's own worked examples** | Where ISO publishes a sample calculation, it's reproduced | Used as evidence, with a caveat: the manual's own examples are sometimes internally inconsistent with its own tables |
| **Cross-source agreement** | Where ISO's machine-readable content and its filed manuals agree independently | Documented per-subline in `docs/gates/` and `GL_Algorithm/` |
| **Same risk, every jurisdiction** | Every difference between the engine and ISO must name the rule responsible | Run via the test harness; see `docs/UI-STRATEGY.md` for the layered test programme and its review page |
| **The harness reviewing itself** | That a test *exercised* something, rather than merely rating | Structural markers `INERT CONTROL` / `INERT VALUE` / `MOVED` flag tests that ran but proved nothing |

To set up an environment to run these checks yourself, see the **Environment** section of
`README.md` — the engine reads the ERC data corpus from outside the repository (ISO's licensed
content is never committed; see `.gitignore`), at a path set by the `GL_ERC_ROOT` environment
variable.

---

## 7. Documentation map

**Technical specification, derived from the source material:**

| Document | Contents |
|---|---|
| `docs/GL-RATING-ENGINE-BUILD-PLAN.md` | Architecture, phases, code structure, the 18 non-negotiables |
| `docs/rating-engine/` | The manual-derived specification — 14 documents plus appendices |
| `docs/erc/` | The data-file-derived specification — 6 documents |
| `docs/COMPARISON-ERC-VS-PDF.md` | The two independent analyses, compared and adjudicated |
| `docs/gates/` | The per-subline walkthroughs — 15 documents, including the California and New York differentials and the as-of re-measurement |

**Rate-build-up documentation, one pair of documents per subline:**

| Document | Contents |
|---|---|
| `GL_Algorithm/` | The seven rated GL sublines (334, 336, 335 OCP, 335 Railroad, 332, 365, 370) plus Terrorism/TRIA, each as a `RatingAlgorithms.md` + `ERC_Tables.md` pair, reformatted from `docs/gates/` into a rate-build-up-and-premium shape, plus `gl-rating-chains.html` — 23 interactive mermaid flowcharts. A reformat of the gates, not a re-derivation: every gap the gates hadn't settled is carried forward as a flagged node, not resolved by guessing |
| `CF_Algorithm/` | The same documentation shape for the sister Commercial Fire project — `GL_Algorithm`'s template |
| `docs/GL-ALGORITHM-WRAPUP.html` | A single index page linking this PRD, the build plan, hand-off docs, and both documentation corpora |

**Everything else that's built:**

| Document | Contents |
|---|---|
| `TESTING.md` | Every command, stage by stage — each one run and its stated output verified |
| `PROCESS_LOG.md` | The full analysis record, 51 steps |
| `scripts/erc/out/referral_register.json` | Every situation that stops and asks a human — 28, with the decisions taken |
| `Payloads/` | The 53 priced example policies, one per state, each with its input |

**What remains, kept separately so this document stays about what's built:**
[`OPEN-ITEMS.md`](OPEN-ITEMS.md) (the item register, OI-1 onward), [`START-HERE-TOMORROW.md`](START-HERE-TOMORROW.md)
(pickup point and backlog), and [`WHAT-I-NEED-FROM-YOU.md`](WHAT-I-NEED-FROM-YOU.md) (decisions
only a person can make).

---

## 8. Known limits of the current build

Stated plainly, for anyone deciding whether this is ready for their purpose:

- **Rounding is not fully settled.** The data declares *where* to round 7,682 times but not
  always *how*; it's a configurable setting today, with every forced choice flagged in the audit
  trail.
- **A `0` in the data files has seven distinct meanings** — a real factor, an unpublished one, a
  degraded referral, a switch to a different pricing path, an input-derived calculation, a
  genuine "no liability in this state," and a coverage the state doesn't offer. Four of the seven
  now have a test inside the data itself; not all do — see the register in `scripts/erc/`.
- **Hawaii is absent from the corpus entirely** — not empty, absent. Whether ISO doesn't file GL
  there or the licensed subscription excludes it is not yet known.
- **The verified population is still narrow.** Eleven jurisdictions have been checked broadly, but
  on one class family; seven sublines are documented in depth, out of the fuller subline list.
  Multi-location and multi-class submissions have no starting payload yet, and 20 jurisdictions
  declare only a single rating territory, so a two-location test can't be constructed there.
- **No effective-date axis has been tested across an edition change** — 43 jurisdictions change
  basis on 1 April 2027.
- **Carrier-specific rating (your own rates instead of ISO's) is not built.** This is deliberate:
  once carrier content is layered on top, no external service can confirm the answer independently
  anymore, so it's the right thing to build last.

None of these are hidden — each is enforced or flagged in the audit trail rather than silently
absorbed, per R9 and R10 above.

---

**Document history:** originally written as a running progress log; restructured 2026-08-20 to
describe the current build for a third party getting up to speed, rather than day-by-day change
history. That history is preserved in full in `BUILD-LOG.md` and `PROCESS_LOG.md`.
