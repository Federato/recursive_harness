# Property — build order, by coverage

**Written 2026-09-16.** Item 3 of [`CF-PROPERTY-INTEGRATION-PROPOSAL.md`](CF-PROPERTY-INTEGRATION-PROPOSAL.md)
— *"a coverage-by-coverage gated build order"* — which has been unauthorized since 2026-08-20.
This is the plan, not the authorization. **Nothing here is built until you say so.**

Method copied from GL deliberately: one coverage at a time, each ending at a **gate**, each gate a
document that either passes or does not. What is *not* copied is GL's content — Property's traps are
its own, and the ones already found are listed against the chunk that will hit them.

> **Scope: this is the harness, not the Excel rater.** The deliverable is a `cf_engine/` package in
> `Recursive_Harness_2.0` that executes ISO's ERC rules, alongside `gl_engine/` — golden cases, gates,
> an interpreter. It is **not** a plan for `CFRater1.01.xlsb` in `C:\Projects\Spreadsheet_Rater`.
> The two share evidence and nothing else: the Excel-rater tracing and the extracted Supporting Tables
> are cited below as inputs that save work, because the ERC reading behind them is the same reading the
> engine needs. Where a chunk says "traced", that means the rules are understood — not that any code or
> formula exists.

Companion: [`CF-PROPERTY-BUILD-ORDER.html`](CF-PROPERTY-BUILD-ORDER.html).

---

## What the GL build actually taught us

Five things worth carrying over, and one worth not.

| | Carry over |
|---|---|
| **One subline at a time, gated** | GL ran fourteen items; twelve gates are filed. Each gate is a document with a golden case, not a checkbox |
| **ERC is the source; the manual confirms and never sources** | Held for all twelve GL gates. CF already has an ERC-vs-circular comparison that says the same thing |
| **Differential gates after the first** | Gate 2 cited gate 1's shared machinery instead of re-deriving it — *"a fraction of the effort and still surfaced four things 334 could not show"* |
| **"n of N", never a bare count** | Seven GL gates in one day produced five wrong figures, every one an aggregate or a negative. The denominator must come from the corpus, not from the search |
| **Enumerate the population, then classify every member** | The machine check (`34_crosscheck.py`) caught its own author repeating the substring error an hour after the habit was written |

| | Do not carry over |
|---|---|
| **GL's ZIP-code territory resolver** | CF territory tables are keyed county/place in every state sampled. This is a separate resolver, and it sits in the foundation chunk below |

**One naming trap already known:** CF's multiply operator is `rul:Product`, not GL's `rul:Multiply`.
An interpreter reused unchanged will silently under-count CF's arithmetic.

---

## The shape of the problem

882 countrywide rule files. By family:

| Family | CW rule files | Status today |
|---|---|---|
| Structure / Building | 21 | four forms traced; Legal Liability traced |
| Personal Property (Contents) | 44 | four forms traced; Legal Liability traced |
| Business Income | 96 | four forms + the `Factor` chain traced |
| Special Class | 110 | four forms traced |
| Special Class Business Income | 111 | four forms traced |
| Earthquake | 97 | **untraced** |
| Leasehold Interest | 32 | surveyed only |
| Ordinance or Law | 55 | untraced |
| Terrorism | 16 | untraced |
| Non-Owned Trailers | 6 | surveyed only |

**A testing-breadth number, not an architecture one.** Resolving state over countrywide is already
settled and built (N5; `cf_engine/resolve/resolver.py`), so nothing below changes how a premium is
computed. What it changes is **how much a single-state golden case proves.** 213 CF groups have a
`SetPremium` that some state rewrites — 479 instances across 21 states, led by FL (122), PR (64),
CA (61), KS (46) — against **four groups in GL, all Terrorism**. So a GL coverage proven in one state
is largely proven everywhere; **a CF coverage is not.** Spend state test cases on the contested
formulas first: Spoilage (8 states), Outdoor Trees/Shrubs (7), Radio/TV Antennas (7), PostTRIA (6).
See `CF_Algorithm/CF_Premium_Map.md` §5.

**103 of 460 countrywide rate tables are header-only (22.4%).** That is not a corpus defect — several
of the biggest are state-filed by design — but it means a chunk is not done because the lookup chain
resolves.

---

## The order

Sequenced on **data dependency**, not on size. Each item states what unblocks it and what it unblocks.

### 0 · Foundation — not a coverage, gates every coverage

**Deliver:** a `cf_engine/` that can load, resolve and execute a CF package.

- Interpreter parity: `rul:Product`, `rul:Power` (Leasehold needs it — the only use in the package),
  `rul:FirstNonNull`, `rul:Choose` **first-match semantics** (Legal Liability depends on ordering).
- The resolver: countrywide base, state child, **edition chain**. CF state packages ship only what
  changed, so a table absent from the current edition is still in force from the last edition that
  filed it. Every CF spreadsheet built so far does this scan; the engine must too.
- A **county/place** territory resolver. Not ZIP.
- A header-only-table detector that fails loudly rather than resolving to zero.

**Unblocks:** everything. **No gate of its own** — it is proved by chunk 1's gate.

### 1 · Building — Basic Group I, class-rated, scheduled

The spine. Base rate → territory → protection class → cause-of-loss adjustment → coinsurance → LOI
→ deductible → premium.

**Why first:** every other coverage is described *relative* to this one. Contents, Business Income,
Special Class and SCBI all either copy its rate, borrow its keys, or diff against its formula.

**Traps already known:** `DeductibleFactor` keys on the location total (Building + Contents), not the
building limit. Sprinkler-leakage has two mutually exclusive terms and an LCM rounding quirk.

**Gate needs:** one golden case proven end to end, every intermediate traced to a named rule and a
named table row.

### 2 · Building — Basic Group II

**Why second and not bundled with 1:** it needs machinery chunk 1 does not.

**`BasicGroupIIRate` and `LowestBasicGroupIIRate` have zero countrywide rows.** 45 states file the
first, 39 the second; **FL and PR file neither**, and AR, DC, KS, NY, RI and TX also lack the lowest
table. There is no CW fallback to lean on — the state row is the only row. This is the chunk that
proves the state-table loader for real.

**Traps:** the wind/hail-excluded branch rebuilds from the lowest base rate and silently drops the
class hazard load. `BasicGroupIISymbol` is a **submission input** on Special Class — no rule derives it.

### 3 · Building — Broad and Special

Short chains, and the place two more engine behaviours appear: hardcoded literal lookup keys
(`"Frame"`, `"Bldg"`) and the theft-exclusion factor.

**Trap:** Special's `SpecialBuildingRate` is another zero-CW-row table — 45 states file it, FL and PR
do not.

### 4 · Contents (Personal Property) — all four forms

**Build differentially against chunks 1–3.** Most of the chain is shared; what differs is documented.

**Trap:** `CovForm`, not `CovType`, drives the Contents branch — and it is **inherited from the
occupancy class**, so contents items cannot differ within a class.

### 5 · Business Income — the `Factor` chain and all four forms

**New machinery:** `SetFactor` is a four-way `Choose` that picks **exactly one** of MaxPeriod,
MonthlyLimit, ExtraExpense or TypeOfRisk. Multiplying them would overstate the premium by a large
multiple. Plus the combination blends and the educational branch.

**All seven Factor tables are already extracted** to
`BusinessIncome_FactorAndEnums_Tables.xlsx` — the data side of this chunk is done.

**Traps:** BI has **no deductible, no LOI and no coinsurance factor** — its `Factor` is the
coinsurance analogue. The educational branch defaults to `0.0`, not `1.0`.

### 6 · Special Class — building side

**Confirmed structurally absent:** `RatingType` (no Specific/Tentative) and Legal Liability. Two
fewer paths than Building.

**Trap:** the base rate keys on **class *description*** via `SpecialClassDescConvertedOption`, not
class code — and FL files 11 description strings that do not exist countrywide, so a CW-derived
description list silently misses in Florida.

### 7 · Special Class Business Income

**The most differential chunk in the plan** — a reuse map already exists
(`Excel_Rater_SpecialClassBusinessIncome_ReuseMap.html`) giving a per-value verdict: copy, share the
table, or build own.

**Traps:** BGI *copies* the parent's finished rate while BGII runs its own lookup; Broad reads the
same table as Building at a **different row** (0.015 vs 0.011/0.023); Special reads entirely
different tables despite identical rule and datadef names.

### 8 · Legal Liability — Building and Contents

**Already traced end to end**, both coverages, all four forms, with an eleven-point divergence map.
This chunk is implementation, not derivation.

**The fork is in `SetPremium`, not the rate chain** — it starts three steps earlier and discards
coinsurance, LOI and deductible. Blanket is unreachable on this path.

### 9 · Blanket rating

**The widest remaining gap.** Branch B is a stub in every premium file built in chunks 1–8, across
every coverage. Doing it once, late, is cheaper than doing it five times early — but nothing above
this line is *finished* until it lands.

### 10 · Earthquake — the fifth form, all coverages

**97 rule files, and it gates more than itself:** roughly 29 Special Class files ship an Earthquake
wrapper, the Legal Liability branch has 8 Earthquake endorsement variants, and Non-Owned Trailers has
its own. Its own `EQFactor`, EQ territory, EQ class, sub-limit and flat-dollar-deductible variants.

**This is the single largest unblocking item in the plan.**

### 11 · Leasehold Interest — a sixth coverage, not a fifth path

32 rule files, its own datadef group, four sub-coverages (Tenants Lease, Bonus Payments,
Improvements & Betterments, Prepaid Rent) × five forms.

**Its exposure is computed, not entered** — a present-value annuity
(`AnnuityConstant × (1 − DiscFactor^months)`, averaged inception-to-expiration) driving the **only
`rul:Power` in the package**. No coinsurance, LOI or deductible anywhere in it. **No blanket branch
at all** — confirmed, not assumed.

### 12 · The endorsement families

Sized, not sequenced — take them by family once the core is proved: Ordinance or Law (55),
dependent properties, utility services, green upgrades, debris removal, unmanned aircraft.

### 13 · Terrorism / TRIA

16 rule files. Reads other groups' finished premiums, so — as in GL — it runs **last**.

### 14 · Policy assembly

Aggregation, minimum premium, statistical coding.

---

## The per-coverage gate

Mirrors GL's, with the evidence Property actually needs. A chunk passes when **all nine** hold:

1. **A golden case rates end to end**, every intermediate value traced to a named rule and a named
   table row.
2. **Every table the chain touches has its row count stated**, and any header-only table is explained
   — state-filed, withdrawn, or a real gap.
3. **Every state is enumerated, not sampled.** "n of N", with N from the corpus. A negative claim
   states what was enumerated and how.
4. **Every `0` is tested against its consuming branch.** CF has at least three meanings already —
   a genuine factor, a "no credit" rate, and a **zero that collapses the premium**
   (`LegalLiabAddlInsurableIntFactor`, `VandalismExclFactor` on a blank class code, the educational
   extension factor).
5. **Every hardcoded literal key is listed.** CF branches on literals constantly — `"Frame"`,
   `"Bldg"`, `"Other than Apartments and Condominiums"`, class code `1180`. Each one makes filed rows
   unreachable from that chain, and that has to be a stated decision rather than a surprise.
6. **Shared-name traps are diffed, not assumed.** Same rule name and same datadef name have already
   been found reading *different tables* (`SetSpecialBaseRate`, `SetSpecialTheftExclusionFactor`).
   A shared name is a question.
7. **Every exclusion's endorsement record is identified per datadef group.** Vandalism, wind/hail and
   theft each file a separate record per coverage; sharing one input is a simplification and is
   logged as S-1/S-2/S-3 rather than left implicit.
8. **The edition basis is stated**, and any table pulled from an older edition says so. Several live
   tables exist only in earlier packages.
9. **The golden case comes back with no unexplained validation message.** A CF submission can
   **rate correctly and still return errors** — ISO has one severity (`AddErrorMessage`, no warning
   variant), so a premium and an error arrive together. Every message the chunk's golden case
   produces is either designed out or logged in
   [`CF_Algorithm/CF_Message_Register.md`](../CF_Algorithm/CF_Message_Register.md) with its rule,
   its cause and the check that was missing. A chunk does not pass on the premium alone.

   > Two traps this gate exists for. **States delete messages**: 316 countrywide rules are
   > overridden to an empty `<rul:Sequence />` in some state, so the countrywide set is not the
   > applicable set — effective counts run 400 (PR) to 455 (CA). And **rules come in mirrored
   > pairs**: attaching an endorsement to silence one message can raise its opposite. Diagnose with
   > `python scripts/cf/07_diagnose_message.py --message "…" --table <TableName> --state <ST>
   > --payload <file>` rather than by reading the XML.

---

## What is already done, and worth not redoing

| Asset | What it saves |
|---|---|
| `CauseOfLoss_*_RatingAlgorithms.md` × 5 | the rate chains for all five core coverages, rule-by-rule with line numbers |
| `Excel_Rater_*_HowItWorks.html` + reuse map | per-coverage narrative and a copy/share/build-own verdict per value |
| `CF_RatingPath_Switches.md` / `.html` | every enum and election that selects a path, with the values actually tested |
| `CF_DataDef_Tree.html` | the containment tree, which is what `../` paths walk |
| Supporting Tables `*.xlsx` | ~30 extracted tables, all states expanded, edition-resolved |
| `Rater_Simplifications_Backlog.md` | the accepted divergences, so they do not get rediscovered as bugs |
| **`CF_Payload_ClassRated_Bldg_PP_Alabama.md`** | **the request shape for chunks 1, 2 and 4** — what a submission carries versus what the engine derives, from ISO's own STC payloads, validated across all 7 Alabama cases |
| **`CF_Payload_Completion_Tracker.md` / `.html`** | what remains before the payload spec is complete, by feature set, with status per item |
| **ISO STC corpus** | **921 ISO-authored rating payloads** inside the ERC packages (`<package>/STC/*.json`), indexed in `STC_Corpus_Index.xlsx`. **Inputs only — ISO ships no expected outputs**, so these are request fixtures, not a regression suite |
| **`CF_Validation_Messages.md` / `.xlsx`** | **the `DoMessage` rule set** — 1,621 rules across 48 jurisdictions, with what each checks and which states suppress it. Gate point 9 depends on this |
| **`CF_Message_Register.md`** | **every validation message ISO has actually returned**, its cause, its fix, and the check that was missing |
| **`scripts/cf/07_diagnose_message.py`** | turns a returned message into the rule, the decoded condition, and the payload values that made it fire — a minute instead of an hour |
| **`CF_Premium_Map.md` / `.xlsx` / `CF_Premium_Tree.html`** | **how every premium reaches the account total** — 881 groups, seven levels, and the **213 formulas some state rewrites**. Chunks 1–14 all end in a premium; this is the map of where it goes |

---

## Recommendation

**Chunks 0 → 1 → 2 is the smallest sequence that proves the architecture**, because 0 proves the
loader, 1 proves the interpreter against a full chain, and 2 proves the state-table resolution that
22.4% of the corpus depends on. Everything after that is repetition with known traps.

**If only one thing is authorized, make it chunk 0 plus chunk 1's gate.** A passing gate on Building
Basic Group I answers whether GL's architecture transfers to Property at all — which is still the
open question from the August proposal.
