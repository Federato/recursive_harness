# The Build — staged plan, for sign-off

**Written 2026-08-12. No code exists. Nothing below is built until you approve the stage.**

This is the plan for the engine itself. It follows the twelve directives of 2026-08-12 and the
architecture decided with them: **execute ISO's filed rules rather than re-implement them**, two
behavioural modes, all sublines in scope, tested first on Premises/Operations and
Products/Completed Operations.

---

## 0. What we already have, and what it is worth

Three weeks of analysis is not preamble to this build — it is most of its specification.

| Asset | What the build uses it for |
|---|---|
| **11 coverage walkthroughs** | **Acceptance tests**, not code. Each states the rule order, the arithmetic and the deviations, so the interpreter can be checked against a known-correct reading |
| **18 non-negotiables (N1–N18)** | Load-time assertions and design constraints, each already measured |
| **The referral register** — 28 conditions, 13 decisions | `escalate/` is populated on day one rather than discovered during build |
| **54 priced example policies** | Real answers to rate against, covering 50 jurisdictions |
| **42 analysis scripts** | Package discovery, edition resolution and table loading already exist and are proven over 61 packages |
| **Two expert agents** | Available to review the engine's output against the manual and the data |

**The single most important number for this build:** ERC's instruction language is **58 node types
(54 executable) over 809,088 occurrences**, and **the top 20 cover 94.1%**. That is what makes the
interpreter approach cheaper than transliteration, and it was measurable only because the corpus had
already been mapped.

---

## Stage 1 — Load and resolve  ✅ BUILT 2026-08-12

**Deliverable:** `gl_engine/erc/` and `gl_engine/resolve/`. Given a state and an effective date,
return the exact rule set and tables that apply.

- Package discovery and identity from the XSD namespace, never the folder name (N6)
- Edition selection **as of a date**, and the declared countrywide parent — not the newest (N4, N5)
- Table loading, typed from the table definitions, with the five table shapes
- **The load-time assertions** already specified in §10 of the build plan, as hard failures

**How you check it:** point it at all 51 jurisdictions for a date and confirm it resolves the parents
we measured — including the three live parents and California's lone `V02`. It should refuse a date
before 2022-09-01 rather than silently falling back.

**Why first:** everything else is downstream, and it is the part most thoroughly proven by existing
scripts.

**Built and verified.** `gl_engine/` — 1,814 lines, 11 modules, no third-party dependency.
`tests/verify_stage1.py` **18/18**; `python -m gl_engine.cli check 20260811 --deep` **13/13**. All
51 jurisdictions resolve, each against its own declared parent; 3 countrywide editions live today
and 3 at the cliff; a pre-2022-09-01 date is refused. **Four corrections and two new escalations
along the way — E20/OI-68 (`1.00` as a sentinel) and OI-69 (the split loss-cost defect is wider than
recorded).** See [`BUILD-LOG.md`](../BUILD-LOG.md) Entry 2.

---

## Stage 2 — The interpreter  ⏸ AWAITING SIGN-OFF

**Deliverable:** `gl_engine/interp/`. Executes ERC rules.

This is the heart of the build and the only genuinely new engineering.

- **The evaluation contract**, written down first: what each node means, child evaluation order, how
  nulls propagate, what `FirstNonNull` does when everything is null. E3's residual, now live
- **~20 node types** to start — `Sequence`, `If`/`Test`/`Then`/`Else`, `Choose`/`When`/`Otherwise`,
  `Equal`/`NotEqual`, `And`/`Or`, `IsNull`/`IsNotNull`, `Constant`, `Value`, `FirstValue`,
  `FirstNonNull`, `Lookup`/`Keys`, `RunRule`, `ForEach`, `Product`/`Sum`
- **DataDef addressing** — the `../../../` paths that reach across coverage groups (E18)
- **`RunRule` dispatch**, including parent dispatch that must not recurse (N2, 4,598 call-super rules)
- **Write-once semantics as a property of the resolved edition** — 213 guarded values in the newer
  parent, 3 in California's (OI-58)
- **`Decimal` throughout, never float** (N10), with the five rounding precisions including the 8dp
  one found on 12 August

**How you check it:** run it against the eleven walkthroughs. Each states its expected rule order and
arithmetic; the interpreter should reproduce them without any coverage-specific code.

**The honest risk:** the long tail. 14 node types appear fewer than 500 times each and one appears
twice. They are cheap individually but they are where surprises live.

---

## Stage 3 — The kernel and the two modes

**Deliverable:** `gl_engine/rating/kernel.py`, `escalate/`, `trace/`. A submission goes in, a premium
and its factors come out.

- Submission → resolved packages → execute → premium
- **Evaluation order across coverage groups**, because coverages are not independent (E18) and
  terrorism runs last
- **The referral register wired in**, with `strict-erc` and `underwriting` modes
- **Resolvable referrals** — a referral names the value it needs and rating resumes when supplied
- **Dispositions are monotonic** — a recalculation never cancels a referral
- **The trace**: every number carries where it came from, and records referrals raised *and* resolved

**How you check it:** rate Oklahoma's golden case and reproduce `976 + 6,845 + 18 = 7,839` exactly.

---

## Stage 4 — Schemas and payloads

**Deliverable:** `gl_engine/schema/`, and `Engine_Payloads/` with one sample per jurisdiction.

- A **baseline submission schema per state**, supporting multi-state, multi-location, multi-subline
  and multi-coverage in one request
- **Sample payloads built from the 53 RAaS inputs**, same class code and exposure everywhere so
  state differences are visible and attributable
- **Four states carry an extra field** — California, Florida, New York and Texas resolve territory
  by county or place (E8)
- **51 jurisdictions**, including DC and Puerto Rico. **Hawaii is not in the corpus and cannot be
  rated**

**A wrinkle worth knowing before it surprises you:** the loss-cost tables have different *shapes* by
state — California and New Jersey put the territory in the filename with three columns, Ohio and
Texas use four columns, New York uses its own column names. **The interpreter handles this by
construction**, which makes stage 4 an early proof that stage 2 was built right.

---

## Stage 5 — The enum workbook

**Deliverable:** an Excel workbook listing every field a payload can carry and its legal values.

Sourced from ISO's own domain tables — 417 countrywide plus state overrides — so *"how do I express
a limit"* is answered by ISO's filing rather than by us. Cross-referenced against the **1,906 input
fields** measured in the corpus, and against the 53 real submissions, so the workbook covers what is
actually used rather than everything conceivable.

---

## Stage 6 — The UI

**Deliverable:** a separate application file. Paste a payload, rate it, read the result.

- Every rating factor, in order, with its source
- **Premiums per coverage and per subline, in their own arrays**
- Referrals shown as referrals, with what would clear them
- Mode switch between `strict-erc` and `underwriting`

**Strictly separate from the engine.** The engine must never import the UI, and must be fully usable
from a notebook — which is the secondary integration you asked for, and comes free if the separation
holds.

---

## After the six stages — the phases that follow

The six stages above build **the ISO engine**. Three phases follow, in this order and for a reason.

### Phase 2 — Proof against RAaS

Run the same submission through the engine in `strict-erc` mode and through ISO's own service, and
compare. **Any difference is our defect until proven otherwise.** This is the whole point of strict
mode existing.

Doable partly offline first: **54 ISO-priced example policies covering 50 jurisdictions** are already
on disk, which is enough to find systemic errors before the connection exists.

### Phase 3 — The harness closes the loop

The comparison run continuously and automatically, with the two expert agents adjudicating each
difference against the manual and the data, and findings fed back as fixes. **Detection first,
diagnosis second, correction third** — see the plain-English walkthrough for what each of those
honestly means and where the limits are.

### Phase 4 — Company deviations

**Only once the ISO baseline is trusted.** The reason is the oracle: RAaS rates ISO content, so the
moment company content is layered on, **no external service can confirm the answer**. Deviating from
an unproven foundation makes every difference unattributable.

**But the design anticipates them from stage 2**, under three constraints now recorded in build plan
§5 as **C1 (ordered layer chain), C2 (ISO's `@parent` keeps ISO's meaning), and C3 (behaviour and
content are independent axes)**. All three are cheap now and invasive later.

---

## Running throughout — the two diaries

**`BUILD-LOG.md`** — the build as it happens, in the style of `PROCESS_LOG.md` but about code only:
what was built, what broke, what was corrected. **Corrections are kept, not tidied away** — they are
the raw material for the self-correcting harness.

**`FROM-PLANNING-TO-BUILD.md`** — **skeleton written before stage 1, filled in as we go.** For each
stage: what it *expected* to inherit from the analysis, and what it *actually* used. Written
afterwards this becomes a tidy story; written alongside it records where three weeks of analysis was
genuinely load-bearing and where we would have got there anyway. That distinction is the whole value
for a future line of business.

---

## Not now, by instruction

**RAaS integration.** The end goal is to diff against ISO's service as the gold standard and feed
the difference into a self-correcting loop. **Nothing is built toward it yet** — but the 54 priced
examples let us do most of that offline first, and `strict-erc` mode exists precisely so the
comparison is meaningful when it comes.

**Company deviations.** Phase 4, after the ISO baseline is proven. **Not built, but designed for** —
constraints C1, C2 and C3 in build plan §5 apply from stage 2 onward, because retrofitting a layer
chain into a written interpreter is expensive and retrofitting `@parent` semantics is dangerous.

---

## What sign-off means

Each stage is presented before the next begins, exactly as the analysis gates were: **what it does,
what it was checked against, and what it cannot yet do.** You run tests, corrections get recorded,
and we move on.

**Stage 1 is built. Awaiting your approval of stage 2.**
