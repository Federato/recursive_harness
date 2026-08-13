# Building the ISO GL Rating Engine — In Plain English

> **Reconciliation note, 2026-08-11.** This document was derived before the ERC work and **before any subline
> was derived end to end**. The per-subline gates have since superseded or sharpened some claims
> here — see [`../gates/RECONCILIATION.md`](gates/RECONCILIATION.md) (items R1, R2, R3). The text below is
> left as the record of what this derivation found on its own; that independence is what makes
> agreement between the two derivations evidence.

**What this document is.** A non-technical explanation of how we intend to build a General
Liability rating engine from the ISO manual PDFs we hold, what we learned that changed the
plan, and how the same approach extends to other lines of business.

**Scope.** This describes a build from **the PDF manuals only**. We hold 975 of them. We are
deliberately not assuming access to ISO's ERC (Electronic Rating Content) data feed. Section 8
sets out what we expect would change if we later built on ERC instead — clearly labelled as
expectation, since we have not evaluated ERC.

**Audience.** Anyone who needs to understand the shape and risk of this build. No prior
knowledge of the ISO manual is assumed. The engineering detail sits in
[`docs/rating-engine/`](rating-engine/) — 14 documents and 4 appendices, all sourced to named
PDFs.

---

## 1. What we are actually building

A rating engine takes a description of a business — what it does, where it is, how big it is,
what limits it wants — and returns a premium, along with an auditable explanation of how that
premium was reached.

ISO publishes the rules and the rates for General Liability as a set of filed manuals. Insurers
license them and build systems that apply them. Our job is to turn a shelf of PDFs into
software that produces the same answer a careful human would, every time, and can prove why.

Two things make that harder than it sounds:

- **The manual is not one document.** It is a countrywide rulebook, plus a separate set of
  exception pages for each of 51 jurisdictions, plus a separate rate publication per
  jurisdiction — all revised on different schedules.
- **It changes constantly.** Our corpus alone spans 2020–2027 and contains 975 notices. A
  policy written today and endorsed next year must be rated against the manual **as it stood**
  at the right moment, not as it stands now.

---

## 2. What we hold

| | Rules manuals | Loss cost manuals |
|---|---|---|
| Files | 503 | 472 |
| Readable | 502 | 471 |
| Jurisdictions | 51 — 50 states less Hawaii, plus DC and Puerto Rico | 51 |
| Years | 2021–2027 | 2020–2027 |
| What they give us | How to rate: the rules, the classification system, the state exceptions, the increased-limit factors, and the territory definitions | What to rate with: the actual published loss costs by class, territory and coverage, plus the estimated loss potentials |

Between them, these two shelves contain **everything needed to price the two main General
Liability coverages in all 51 jurisdictions** — with one exception noted in §7.

---

## 3. The five things we learned that changed the plan

These are not opinions. Each was measured across the full corpus, and each one would have
produced a broken engine if we had assumed otherwise.

### 3.1 The countrywide manual cannot produce a price on its own

The natural design is "load the national rulebook, apply state tweaks." That fails
immediately. The national rulebook says, in its own words:

> *"The increased limits tables are displayed in the state exceptions."*

There is no national table of increased-limit factors anywhere. Every single one lives in a
state document. And there is **no national loss cost publication at all** — zero of our 472
rate files are countrywide.

So the national layer holds the *method* and almost none of the *numbers*. The engine has to
**compose** three sources rather than start from one and patch it.

### 3.2 Rule numbers are labels, not identities

The 2027 countrywide edition renumbered 21 of about 50 rules. The dangerous part is not that
things moved — it is that numbers were **reused**:

| Rule | Meant, before 2027 | Means, from 2027 |
|---|---|---|
| 22 | Description Of CGL Coverage | **Mandatory Endorsements** |
| 35 | Premium Determination | *Reserved for future use* |
| 21 | *(did not exist)* | **Premium Determination** |

A state document saying *"Rule 22 is replaced"* means something completely different depending
on which edition it was written against. If the engine looks rules up by their printed number,
it will one day attach a state exception to the wrong rule and produce a wrong premium **with
no error message**. This is the single highest-severity risk in the build, and the fix is
structural: every rule gets a permanent internal identity, and the printed number becomes just
a label attached to a particular edition.

### 3.3 Blank is not zero, and "refer" is not zero

The rate pages are grids of class codes against loss costs. A cell contains one of exactly
three things, and we counted every one across the current notices — 429,748 cells:

| What is printed | How often | What it means |
|---|---|---|
| A number | 64.3% | The published loss cost |
| `–` (a dash) | 18.6% | **This coverage is not offered for this class.** Decline it |
| `(a)` | 17.1% | **Refer to the company.** Look up the estimated loss potential instead |

**More than a third of all cells are not numbers.** A naive import that reads them as `0.00`
produces free policies and sells coverage the manual explicitly declines. This is the most
likely single cause of a catastrophic, silent pricing failure, and it is entirely preventable.

### 3.4 The rates are mid-migration, right now

ISO is part-way through a revision of the General Liability class list. As of our corpus:

- **15 jurisdictions** are still on the old basis
- **36 jurisdictions** have moved to the 2027 basis, which retires 229 class codes, introduces
  204 new ones, and **withdraws the published loss costs for Owners & Contractors Protective**

We confirmed the split three independent ways and got the identical 15/36 list each time — so
this is one filing rolling out state by state, not three unrelated changes.

The practical consequence: **a single national class list is wrong today.** Rate lookups must
be keyed to a jurisdiction *and a date*. An engine that hardcodes the current list will quietly
start mis-rating as the remaining states convert.

### 3.5 Some coverages have no published rate at all

We assumed the manual gives an ordered procedure and a rate for each coverage. For two, it
gives the procedure and no rate:

- **Liquor Liability** — a full nine-step rating procedure built around "the basic limits
  rate", and **no published basic-limits loss cost in any of the 51 jurisdictions**
- **Railroad Protective** — same, and it also uses a different basic limit from every other
  coverage, and is rated on *number of trains per day*

Both are priced off estimated loss potentials or referred to the company. An engine built
expecting a rate lookup for these will always come up empty.

---

## 4. How we will build it

### 4.1 The shape: compose, don't inherit

The engine assembles a rating instance from four sources, resolved for a specific jurisdiction
and a specific date:

```
   National rulebook            the method: rules, classification, algorithms
 + State exception pages        the jurisdiction's changes to the method
 + State-only rules             things only that state has, with no national counterpart
 + State rate publication       the loss costs, ELPs and territories
 ─────────────────────────
   what governs this risk, on this date
```

The fourth item is not a modification of anything. There is nothing national for it to
override, and it arrives on its own release schedule.

### 4.2 Everything numeric lives in data, never in code

Loss costs, increased-limit factors, payroll caps, liquor grades, territory maps — all of it
sits in tables that can be reloaded when a new notice arrives. Nothing that ISO can revise
should require a developer to change code.

The alternative — 51 branches of state-specific logic — is contradicted by what we found. The
states do not implement different algorithms. They supply different **numbers** to one
algorithm, plus a small, well-defined set of rule modifications.

### 4.3 Read the PDFs once, carefully, and correctly

Here we learned an expensive lesson worth repeating.

The standard tool for pulling text out of PDFs has a "preserve layout" mode, which is the
obvious choice for reading tables. On the rate grids, **it silently scrambles them** — values
detach from their class code and reattach to the row above. Every number that comes out is a
plausible loss cost. Nothing errors. Nothing looks wrong.

A different library reads the same pages correctly. We proved it arithmetically: Indiana has 4
territories × 1,188 classes × 2 columns = 9,504 cells, and the correct reader returns exactly
9,504.

So: **the correct extraction tool is fixed as part of the build, not left to whoever writes the
importer**, and every import is checked against that arithmetic before it is accepted.

### 4.4 Prove the import before trusting it

We built 23 automated checks that run on every load. The ones that matter most catch problems
no human review would spot:

| Check | Catches |
|---|---|
| Cell values are only ever a number, a dash, or `(a)` | A scrambled or mis-parsed grid |
| Cell count = territories × classes × 2 | Rows lost to misalignment |
| Increased-limit factors never decrease as limits rise | A shifted column in a factor table |
| The territory list in the rules manual matches the territory list in the rate manual | Either file being parsed wrong, or a mismatched edition |

That last one is the most valuable thing we have. The rules manual and the rate manual are
separate publications on separate schedules, produced years apart. We checked all 51
jurisdictions and got **exact agreement, zero mismatches**. Nothing else in this project gives
us an independent second opinion — everywhere else, if our parser is wrong, we have no way to
know.

### 4.5 Dating, without the ERC feed

This is the piece most affected by working from PDFs alone, so it deserves plain treatment.

To rate a policy as of a date, we must know which notice was in force then. The PDFs give us
three things:

1. **A cover page citing a circular, with the circular's issue date** — present on **485 of 502**
   rules notices and **452 of 471** rate notices, about **96%** of the corpus.
2. **A notice number that sorts** — `GL-NJ-2027-LC-002` follows `GL-NJ-2027-LC-001`.
3. **The fact that each notice is a complete reissue**, not a patch. We verified this: all 17
   Illinois rules notices carry the same complete rule set, and all 10 Alabama rate notices
   carry the full page set. So to rate as of a date you pick *one* notice, not a chain of
   accumulated changes.

Together these let us build a defensible timeline per jurisdiction, from the PDFs alone.

**But be clear about what the circular date is.** It is the date ISO *issued* the circular, not
the date the manual change *took effect*. Those differ, usually by months. So a PDF-only build
gives us:

- **Reliable ordering** — which notice supersedes which. High confidence.
- **A lower bound on the effective date** — it took effect on or after the circular issued.
- **Not the exact effective date.** For that, we would need ISO's own effective-date metadata.

**How we handle it honestly:** every notice carries a confidence flag. Where dating is derived
rather than stated, the engine records that, and any premium resting on it is marked
accordingly. We do not present an inferred date as a known one.

This is the single largest quality gap in a PDF-only build, and it is a **narrow, well-understood
gap** — not a blocker. The engine rates correctly; the risk is in edge cases where a policy
incepts within weeks of an edition boundary.

### 4.6 Prove the engine against itself

There is no external oracle telling us the right premium. So the strongest available test is a
comparison: rate the *same* risk in all 51 jurisdictions, and require the engine to **name the
document** responsible for every difference. An unexplained difference is a bug. Combined with
reproducing the manual's own worked examples, this gives real coverage without a reference
system to check against.

---

## 5. What we already have in hand

This is not a standing start.

| Already built | What it is |
|---|---|
| **The specification** | 14 documents + 4 appendices, every claim sourced to a named PDF, with gaps recorded rather than guessed |
| **The extracted corpus** | All 975 notices as searchable, page-referenced text |
| **The ISO Circular Expert agent** | A working assistant that answers manual questions with citations, and checks engine output against 32 verified rules. Type a ZIP code, get the territory and the page it came from |
| **The review checklist** | 32 invariants — 17 of them "must fix before release" — each derived from the corpus, each describing a specific way this program breaks a rating engine |

The agent matters for how the build runs day to day: when the engine produces a premium we
doubt, we can ask an assistant that has read the whole manual and will cite the page — or
answer *"the corpus does not settle this"*, which is often the honest answer.

*One caveat for accuracy:* the agent's stored effective dates came from earlier ERC-based work
in this project. Its `dating` command is the PDF-only equivalent, reading the circular
reference straight off the cover page — that is the path a PDF-only build uses, and the
coverage figures in §4.5 were measured with it.

---

## 6. Extending to other lines of business

The corpus we studied is General Liability, but almost nothing we learned is specific to it.

### What we expect to transfer directly

**The structure.** ISO publishes every line of the Commercial Lines Manual the same way: a
division of the manual, a countrywide rulebook, per-state exception pages, per-state rate
pages, territory pages, notices as complete reissues, page markers in the footer, and a cover
page citing circular and filing references. Commercial Auto, Property, Crime, Inland Marine and
Businessowners all follow this pattern.

**Every architectural decision in §4.** Composing rather than inheriting; permanent rule
identities; numbers in data; verifying imports arithmetically; date-aware resolution — none of
these are GL-specific. They are responses to how ISO publishes, not to what GL covers.

**Most of the failure modes.** Non-numeric cells carrying meaning, renumbering across editions,
independent release schedules — these are properties of the publication format.

### What will differ per line

**The vocabulary, not the grammar.** Each line has its own coverage names, class code ranges,
exposure bases and page-marker prefixes. This is configuration and reference data, not new
architecture.

**The rating shapes.** GL needed five distinct algorithm patterns to cover 17 coverages. Auto
will need its own — vehicle-based rather than payroll-and-sales-based. The *framework* for
declaring a rating procedure carries over; the procedures themselves are new content.

**The specifics of territory and rate structure.** GL taught us not to assume. GL turned out to
have three different territory schemes; another line may have one, or four.

### How we would sequence it

1. **Build GL properly first.** It is the hardest common line — 51 jurisdictions, three
   territory schemes, a live mid-migration, coverages with no published rate.
2. **Then take the second line as a deliberate generalisation exercise.** The first port is
   where line-specific assumptions surface. Budget for refactoring, not just addition.
3. **From the third line on, expect it to be mostly reference-data work** — new class lists,
   new rating procedures, new tables, against a framework that already exists.

The honest expectation: **line two costs perhaps 40–50% of line one; lines three and beyond,
considerably less.** The expensive part of GL was not writing code — it was discovering how the
manuals actually behave, and that discovery mostly transfers.

**One caution.** Do not generalise the framework based on GL alone. A framework built to fit one
line's quirks fits the second badly. The right moment to fix the abstractions is *during* line
two, with two real examples in hand.

---

## 7. What we cannot do, and will not pretend to

Four inputs are genuinely not in these PDFs. Each is referenced by the manual as a separate
document.

| Missing | Effect | Where it comes from |
|---|---|---|
| **Terrorism Supplement** | Terrorism premium cannot be computed at all | A separate ISO publication |
| **Company loss cost multiplier** | Every stored value is a *pre-multiplier* ISO loss cost. Applying the carrier's own multiplier is the last step to a final price | The carrier — this is by design, not a gap |
| **Experience / schedule / composite rating plans** | Credits and debits for individual risk characteristics | Separate ISO manuals |
| **Workers Compensation loss costs** | One Owners & Contractors Protective class is priced as "75% of the otherwise applicable Workers Compensation loss costs" | A different line of business |

Also worth stating plainly:

- **Hawaii is not in the corpus** — no GL notice of any kind exists for it in either shelf. We
  do not know whether that is a download gap or a filing fact.
- **Two files are corrupt and unreadable** (one rules notice, one rate notice). Both have a
  usable prior notice; both should be re-downloaded.
- **Rate cell data is specified but not yet loaded.** We know exactly how to read the ~429,700
  cells and how to prove the read is correct. Doing it is the largest remaining task.

The engine will treat every one of these as a declared external dependency that produces a
**referral**, not a guess. Where the manual does not say, the engine says so.

---

## 8. How building on ERC would likely differ

**This section is expectation, not finding.** We have not evaluated ISO's ERC feed. We do hold
an ERC-derived edition workbook from earlier work in this project, which is where these
expectations come from — but we have not assessed ERC as a build foundation.

### What we would expect to get materially easier

**Effective dating.** This is the big one, and it maps exactly onto the weakness in §4.5. ERC
is understood to carry effective dates as structured metadata rather than as a circular
reference to be interpreted. If so, the largest quality gap in a PDF-only build closes
outright, and the confidence flags in §4.5 largely go away.

**Extraction disappears as a risk category.** Sections 4.3 and 4.4 exist because we are reading
tables out of page images. Structured content removes that entire class of problem — along with
the scrambled-grid failure, the arithmetic reconciliation, and much of the import validation.
We would expect this to remove a substantial share of the build's total risk.

**Change detection becomes cheap.** Today, spotting what changed between two editions means
parsing both and diffing the results. Structured, versioned content should make "what changed"
a direct query.

**Coverage of what the PDFs omit.** ERC may carry content our PDF shelves do not, which could
narrow the §7 list.

### What we do not expect to change

**None of the architecture in §4.1, §4.2 or §4.6.** Composition over inheritance, permanent
rule identities, data-driven numbers, date-aware resolution, differential testing — these
follow from how the *program* is structured, not from how the content is delivered. The
countrywide layer still holds no increased-limit tables. Rule 22 still meant two different
things. Liquor Liability still has no published rate.

**The domain knowledge.** Everything in §3 is a fact about the ISO GL program. A better data
feed delivers those facts more reliably; it does not change them.

**The need to check the work.** A structured feed shifts *what* you validate — from "did we
read the page correctly" to "did we interpret the field correctly" — but not *whether*.

### What we would expect to get harder, or at least different

**Licensing and access.** A data feed is a commercial dependency with its own terms, delivery
schedule and failure modes. PDFs, once downloaded, are yours.

**Auditability.** Today every number traces to a page of a filed document — the thing a
regulator recognises. A feed-based system should keep that trace, which may mean holding both.

**Verification loses its independence.** The cross-check in §4.4 works precisely *because* the
rules and rate manuals are separately produced documents. If both come from one feed, that
independence is gone — an error in the feed would appear consistent.

### The pragmatic view

If ERC is available and licensable, we would expect it to be the better foundation, mainly
because it fixes dating and removes extraction risk. But **the work already done is not wasted
either way.** The specification, the invariants, the review agent and the domain understanding
in §3 are about the *program*, not the file format. They apply to any build.

And there is a real argument for keeping the PDF path working regardless: it is the filed,
regulator-facing artifact, and it is the only independent check on whether a feed-based system
is telling the truth.

**Recommendation:** proceed on the PDFs now, since the corpus is complete enough to build and
price. Evaluate ERC in parallel, specifically against dating and rate-table delivery — the two
places it would most change the plan. Do not delay the build waiting for that evaluation.

---

## 9. Where the risk actually is

Ranked by what would hurt most, with the honest mitigation:

| Risk | Why it matters | What we do about it |
|---|---|---|
| **Non-numeric cells read as zero** | Free policies; coverage sold that the manual declines. Affects a third of all cells | Import validation rejects any value outside the three-token alphabet. Not a code review item — an automated gate |
| **Rules resolved by printed number** | Wrong exception applied, silently, with no error | Permanent rule identities from day one. Retrofitting this later means re-verifying every state document |
| **Rate basis drifting** | 36 jurisdictions have converted, 15 have not; more will convert | Rate lookups keyed to jurisdiction and date. Never a global class list |
| **Effective dating inferred, not stated** | Wrong edition selected near an edition boundary | Confidence flags on every notice; evaluate ERC as the durable fix |
| **Table extraction errors** | Plausible-looking wrong numbers | Fixed extraction tooling plus arithmetic reconciliation on every load |
| **A coverage assumed rateable that is not** | Engine returns nothing for Liquor or Railroad Protective | Already identified and specified; referral paths built deliberately |

The pattern across all six: **the dangerous failures in this domain are silent.** They do not
throw errors — they produce a plausible number that is wrong. That is why the plan leans so
heavily on automated validation and provenance rather than on testing and code review alone.

---

## 10. In one paragraph

We hold enough of the ISO General Liability manual to build a working rating engine and to
price the two main coverages in all 51 jurisdictions — subject to the carrier supplying its own
loss cost multiplier, which is by design. The work of understanding the manuals is largely done
and written down. The architecture is settled and driven by evidence rather than convention:
compose the national, state and rate layers rather than inheriting; give rules permanent
identities because their printed numbers are not stable; keep every number in data; and prove
every import arithmetically, because the failures in this domain are silent rather than loud.
The main quality gap in a PDF-only build is effective dating, which we can approximate well and
flag honestly, and which a structured feed would likely close. Nearly all of it extends to
other lines of business, because what we learned is about how ISO publishes, not about General
Liability.
