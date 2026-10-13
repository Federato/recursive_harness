# Property chunk 11 — task list and status

**Leasehold Interest — a sixth coverage, not a fifth path.** Opened 2026-09-22.

Derived from [`CF-PROPERTY-BUILD-ORDER.md`](CF-PROPERTY-BUILD-ORDER.md) item 11
and from the opening census
([`106_chunk11_census.py`](../scripts/cf/106_chunk11_census.py)).

**No engine code is expected.** Analysis and gates only, same standing rule as
every chunk before it — nothing is built until the user says so. Chunk 11 is
the first chunk whose build-order entry names a specific interpreter node
(`rul:Power`), and the census confirms it is **already implemented**, along
with every other node the coverage's 32 files use.

**Status: CLOSED 2026-09-22: 24 of 24 tasks, gated 9 of 9** ([`CF-CHUNK11-GATE.md`](CF-CHUNK11-GATE.md)). Four engine fixes, all user-authorized and confirmed against ISO live. Regression clean, 69 of 69. Group C ran the zero cases and asked ISO live: 11 agree, 3 predicted divergences (OI-102/103/104), plus OI-105 (ISO holds a newer 2027 Oregon edition). Group B's write-up is `CF-CHUNK11-GROUP-B.md`; it opened OI-101. One engine fix, user-authorized: `CF-ENGINE-FIX-DATE-COMPARE.md`. The regression is clean.

---

## What is structurally new, before any task runs

**1 · All seven of the build order's claims are TRUE — and the file count
overstates the rating surface by a third.** 32 files named
`*LeaseholdInterest*`, exactly as stated. But **11 of them do no rating at
all**: each `CommercialPropertyLeaseholdInterestFactorsFor<N>PercentRules`
file (5% through 15%) declares exactly `InitializeRuleSet`,
`CalculateTotalPremium` and `ErcProcess` and nothing else — pure
form-attachment markers that put a printed rate-table page on the policy, one
per interest rate. No `Lookup`, no `Premium`, no factor. **The real rating
surface is 21 files**: 1 parent + the 4 × 5 grid.

**2 · "Its own datadef group" is 32 groups, not 1** — one per file, exactly.
21 of them rating-bearing. Gate points 6 (shared names) and 7 (exclusion
records) are *per-DataDefGroup* questions, so chunk 11 asks them across 32
groups against the 5 that chunks 6–10 worked with. **That is the largest
structural jump in the plan so far, and it is a counting fact rather than a
difficulty estimate.**

**3 · The fifth form is EARTHQUAKE.** All 20 cells of the 4 × 5 grid are
filed, and the five forms are Basic Group I, Basic Group II, Broad, Special
and **Earthquake**. Chunk 10's work is therefore a direct input to chunk 11,
not a parallel track — **the first time in this project that a coverage has
been opened after the form it depends on was already built.**

**4 · The `rul:Power` is real, unique, and guarded.** Exactly **1 of 882**
countrywide rule files contains `rul:Power`, and it is Leasehold Interest's
own parent file — the build order's claim confirmed by direct scan. But it
sits behind an `IsNull` guard on
`DiscFactorRaisedToNumOfMonthsRemainingAtInception`, which is this project's
standing **"a submission can populate a derived field"** shape: a payload
supplying the raised power directly bypasses the annuity entirely, and **no
ISO comparison would catch it, because ISO has the same guard.**

**5 · Leasehold Interest is the exact inverse of Earthquake on shared
machinery.** C10-14 confirmed EQ reads `IRPMFactor`/`PackageModFactor` at
**no** depth in **any** of its 5 groups. Leasehold Interest reads **both, in
16 of its 32 files**. Meanwhile coinsurance, LOI, deductible and blanket are
**absent from all 32** — confirmed by direct scan, exactly as the build order
claims. Two coverages opened back to back, opposite answers to the same
question: C9-19's warning that this must be re-asked per chunk, demonstrated
twice in a row.

**6 · One table is dead on arrival.**
`SpecialFormExclgTheftLeaseHoldBaseRate` has **0 rows and is read by no
`Lookup` anywhere in the corpus**, while its near-namesake
`SpecialFormIncldgTheftLeaseHoldBaseRate` has 12 rows and is live. The
project's standing "check all tables before calling a factor blank" rule is
being run at *opening* here rather than at task 13, because this is precisely
the shared-name-adjacent shape that has cost time in three prior chunks.

**7 · ZERO ISO fixtures. This is chunk 9's situation, not chunk 10's.** Of the
**364** Commercial Property STC payloads, **0 mention Leasehold Interest at
all.** There is no regression or confirmation set for this coverage. Chunk 9
closed at 9 of 9 without one by confirming its golden case against a **live
ISO call** instead — that is the route chunk 11 will have to take, and it is
recorded here at opening rather than discovered at task 20, which is what
happened to chunk 10.

> **The denominator is 364, not 924.** C10-20 found chunk 10's own census had
> summed 560 General Liability payloads into that figure. That error is not
> repeated here.

**8 · The state layer is the thinnest of any chunk so far.** Of 47
jurisdictions, only **FL and PR** file any Leasehold Interest file in their
own package, and both carry a `Set`/`Lookup` rule. Every other state runs
countrywide unmodified. FL and PR appearing together, and alone, matches the
standing edition/filing quirks both jurisdictions have shown in every chunk
since 6 — but per the overlay rule, *file presence is not rule override*, and
both layers still get enumerated separately.

---

## Gate-level tasks

Mirrors the nine-point gate in `CF-PROPERTY-BUILD-ORDER.md`.

| # | Task | Status | What it needs |
|---|---|---|---|
| C11-01 | Golden case, hand-derived before code — one Leasehold Interest submission rated end to end. One sub-coverage (Tenants Lease), one form (Basic Group I), every intermediate (`AnnuityConstant`, `DiscFactor`, `NumberOfMonths`, both `ComplimentOfDiscFactor` values, both `NetLeaseholdInterestFactor` values, `TenantsNetLeaseholdInt`) traced to a named rule and table row. **Derive the annuity by hand FIRST** — this is the one chunk where the exposure is computed rather than entered, so a prediction that disagrees is the whole point | ✅ | **Done 2026-09-22: $268 BGI + $30 BGII, every one of 20 hand-derived values matched** (`114_chunk11_golden_case.py`, `CF-CHUNK11-GOLDEN-CASE.md`). It took one authorized engine fix (date comparison, `CF-ENGINE-FIX-DATE-COMPARE.md`) and two submission corrections: LI must be the Structure's own `CovType`, or the record is silently deleted; and a blank `EQCovIndicator` switches the EQ cell ON. 1 validation message is left for C11-09 |
| C11-02 | Every table the chain touches has its row count stated — the 6 LI-named Rate Tables, with `SpecialFormExclgTheftLeaseHoldBaseRate`'s 0-row/no-consumer status adjudicated rather than assumed (census §6) | ✅ | **Done 2026-09-22** (`120_chunk11_groupsEF_inventory_states.py`). All six tables' row counts confirmed (countrywide 2026 and 2023 identical). `ExclgTheft` is dead: 0 rows, no reader. None of the 46 states files any of the six |
| C11-03 | Every state enumerated — both layers, per the overlay rule: which of the 47 file an LI file at all (census says FL, PR), and which actually override a rule | ✅ | **Done 2026-09-22** (`120_chunk11_groupsEF_inventory_states.py`). **Of 46 states, only Florida files LI rules** (4 files): it overrides the BGII premium, adding a sinkhole rate and dropping the cyber factors. This group also exposed **OI-107** (`DateDifference` sign, confirmed live on Oregon's TRIA field, ISO 257 vs ours −257), **fixed the same day with authorization** |
| C11-04 | Every `0` tested against its consuming branch — no lease term, no `InterestRate`, a term that expires before inception, an unmatched interest rate (the table holds only 5%–15% in whole points), and each of the 4 sub-coverage exposure fields absent. Confirm these are DIFFERENT causes, not one zero mistaken for several | ✅ | **Done 2026-09-22** (`117_chunk11_c11-04_zero_cases.py`, `CF-CHUNK11-ZERO-CASES.md`). **Seven distinct tiers**: record deleted, all cells off, months = 0 (reached 3 different ways), annuity = 0, amount ≤ 0, rate = 0, and an engine refusal (0^0). 13 of 14 predictions held. **One miss: `ExpDate` isn't an input at all**; ISO's `Default` block always sets it to EffDate + 1 year |
| C11-05 | Every hardcoded literal key listed — the `CovType`/`CovForm` literals the 20 grid files branch on, checked against the Domain Tables folder per this project's standing rule, not inferred from example rows | ✅ | **Done 2026-09-22** (`120_chunk11_groupsEF_inventory_states.py`). 8 compared literals, all with a source (Domain tables, rate keys, a Structure-derived value) |
| C11-06 | Shared-name adjudication across **32 DataDefGroups** — the largest surface any chunk has faced (5 was the previous maximum). Do the 20 grid cells declare the same rule names with different bodies, and does `04_shared_names.py` still hold when extended to them? | ✅ | **Done 2026-09-22** (`119_chunk11_groupD_shared_machinery.py`). Six names are shared with the Structure file, all with different bodies. No execution collision is possible (every `RunRule` names its file). The Structure's fields equal ISO's. Also found **OI-106** (form names don't resolve, project-wide, no premium impact) |
| C11-07 | Every exclusion's endorsement record identified per datadef group — including whether `SpecialLeaseHoldTimeElementTheftExclusionFactor` (2 rows, live) is a per-group record or a policy-level one, the C10-07 question re-asked | ✅ | **Done 2026-09-22** (`119_chunk11_groupD_shared_machinery.py`). The cyber exclusion is **policy-level and shared** ($268 → $267); the theft exclusion is **structure-level**. No LI group files its own |
| C11-08 | The edition basis stated — FL and PR are the only two overriding states and **both are known to sit on older declared parents** (C10-08 found FL at `CF_CW_20230801_V01`). Confirm what edition each resolves to here | ✅ | **Done 2026-09-22** (`120_chunk11_groupsEF_inventory_states.py`). Florida runs on **CW 2023-08**: the same arithmetic, but without the 2026 injection guards, so C11-12's trap doesn't exist there |
| C11-09 | The golden case comes back with no unexplained validation message, and every `DoMessage` rule that references a Leasehold Interest field is surveyed against the golden case's own field values — not merely absent from the output | ✅ | **Done 2026-09-22** (`121_…`, `122_…`). The golden case gives one message, **M-002** (designed out). **Our message set equals ISO's on 16 of 16 cases compared**, including every LI-specific message (the limit-required message, both CP 00 60 date messages, terrorism sub-limit, theft deductible) |

## Additional structural tasks the census surfaced

| # | Task | Status | What it needs |
|---|---|---|---|
| C11-10 | Confirm the 11 `FactorsFor<N>Percent` files really are inert form markers by reading each one in full, not by rule-name set alone — the C10-10 lesson, where 9 of 19 files the census called "thin wrappers" turned out to do real arithmetic | ✅ | **Done 2026-09-22** (`120_chunk11_groupsEF_inventory_states.py`). Confirmed inert by reading all 11 in full **and** by running all 11 rates: each attaches exactly its own marker, no premium |
| C11-11 | Trace the annuity end to end and prove it by hand: `AnnuityConstant × (1 − DiscFactor^months)`, averaged inception-to-expiration. Confirm the averaging is what the rules actually do, not what the build order's one-line summary says | ✅ | **Done 2026-09-22** (`115_chunk11_groupA_annuity.py`). Averaging confirmed: the mean of the two whole-dollar nets. The day-of-month adjustment was exercised (122/110 → $270/$31). Both tables match the closed form: v = (1+i)^(−1/12) within 4.3e-9, A = v/(1−v) within 1.9e-5 |
| C11-12 | Prove the `rul:Power` `IsNull` guard is the "submission populates a derived field" trap it looks like — a payload supplying `DiscFactorRaisedToNumOfMonthsRemainingAtInception` directly, confirming it bypasses the annuity and that the premium moves | ✅ | **Done 2026-09-22. Confirmed, and wider than the census said: 7 guarded fields, not 1.** Injecting the `rul:Power` output (0.5 → $242/$27), `DiscFactor` (0.99 → $306/$35) or a net factor (100 → $309/$35) each moves the premium. `AnnuityConstant` is the one unguarded input, and injecting it changes nothing ($268/$30) |
| C11-13 | Prove `InterestRate` and lease term are live submission inputs — change only the interest rate, confirm `AnnuityConstant`/`DiscFactor` both move and the premium with them (the C10-12 shape) | ✅ | **Done 2026-09-22.** 13% → $240/$27; lease ending 2032 (60/48 months) → $156/$18. Both are live |
| C11-14 | Confirm coinsurance / LOI / deductible / blanket really are absent at RUN time, not just absent from the XML text — a submission that populates all four and produces an unchanged premium | ✅ | **Done 2026-09-22** (`119_chunk11_groupD_shared_machinery.py`). Coinsurance, limit, deductible and blanket are all inert at run time, even out of domain: $268 / $30 every time |
| C11-15 | Confirm `IRPMFactor`/`PackageModFactor` are read at the depth the census found (16 of 32 files) and that they actually move the premium — the C9-19/C10-14 question, whose answer here is the opposite of Earthquake's | ✅ | **Done 2026-09-22** (`119_chunk11_groupD_shared_machinery.py`). IRPM 1.10 → $295; PackageMod 0.90 → $241; both → $265. Read from the **policy** (a Structure-level PackageMod is ignored), and the EQ cell doesn't move ($10) |

## The reachability map, sub-coverage by sub-coverage

| # | Task | Status | What it needs |
|---|---|---|---|
| C11-16 | Tenants Lease — reaches a nonzero premium on a real submission, all 5 forms | ✅ | **Done 2026-09-22** (`116_chunk11_groupB_subcoverages.py`). Nonzero on BGI $268 / BGII $30 / Broad $26 / Special $45 (with a Theft Exclusion) / EQ $10. **Special without a Theft Exclusion is $0 by ISO's own rule** (factor falls back to 0.0, not 1.0), logged as **OI-101** for the live ISO call. Broad never layers onto Special |
| C11-17 | Bonus Payments — same, and confirm it is genuinely separate machinery from Tenants Lease rather than a renamed copy | ✅ | **Done 2026-09-22. Separate where it matters, a copy where it doesn't.** The grid files are byte-identical to Tenants Lease's after renaming. But its net is **undiscounted**: monthly × months (200 × 114 = 22,800), with no annuity. So it prices with **no interest rate at all** ($54/$6) |
| C11-18 | Improvements & Betterments — same. Note this name collides conceptually with Building's own `Improvements and Betterments` `CovType` (a C10-05 literal); confirm they are unrelated | ✅ | **Done 2026-09-22.** Undiscounted, 300 × 114 = 34,200 → $82/$9. **Unrelated to Building's `Improvements and Betterments` CovType**: no LI file contains that literal, and a structure of that type **deletes** a submitted LI record (the attach gate needs `CovType = Leasehold Interest`) |
| C11-19 | Prepaid Rent — same | ✅ | **Done 2026-09-22.** Undiscounted, 400 × 114 = 45,600 → $109/$12 |
| C11-20 | `SetTotCoveredLeaseholdIntNet` — confirm how the 4 sub-coverages combine into one total, and whether it is a sum or a selection. **Chunk 5's `SetFactor` picked exactly one of four values and multiplying them would have overstated the premium by a large multiple**; this is the same shape and must not be assumed | ✅ | **Done 2026-09-22. A sum, and nothing rates off it.** `TotCoveredLeaseholdIntNet` = 214,558 = the four nets added, but every premium reads its own sub-coverage's net. Rating off the total would make Tenants BGI $513, not $268. So it's not chunk 5's selection shape |

## Cross-cutting claims

| # | Task | Status | What it needs |
|---|---|---|---|
| C11-21 | The Earthquake form cell — confirm LI's EQ column actually reads chunk 10's own `EQCauseOfLossAdjustment`/`FinalEQRate` chain rather than computing its own, and that the two never collide (the C10-16 shape, in the opposite direction) | ✅ | **Done 2026-09-22** (`119_chunk11_groupD_shared_machinery.py`). Copies the Structure's EQ rate (0.009) and changes nothing: 21 EQ fields identical. **Found: an LI structure with no LI record auto-creates an empty one and crashes our engine on 0^0**, which raises OI-104's severity |
| C11-22 | ISO confirmation — with **zero fixtures** available (census §7), the golden case must be confirmed against a **live ISO call**, the way chunk 9 did. Plan it at task 1, not at task 20 | ✅ | **Done 2026-09-22, live** (`122_chunk11_c11-22_raas_confirmation.py`). Golden case at the like-for-like date: **$272 / $31 on both sides**, net 113,751. At 2027-01-01 every annuity value matched ISO to the digit (only the BGI base rate differed, OI-105). **Rounding tie**: average 75,834.5 → **ISO 75,835, half-up**, same as ours (corroborates OI-70) |
| C11-23 | OI-99 re-asked — does ISO refuse where this coverage returns $0? Chunk 11's zero cases (C11-04) are the input | ✅ | **Done 2026-09-22, live** (`118_chunk11_c11-23_raas.py`). **11 agree, 3 diverge, all 3 predicted**: a missing `LeaseEffDate` was $0 here and $272 at ISO (**OI-102, fixed the same day with authorization, now matching ISO live**); an interest rate not in the table is $0 here and **refused** by ISO (**OI-103**); 0^0 was refused here and $0 at ISO (**OI-104, fixed the same day with authorization; now $0 on both sides**). OI-101 is **confirmed as ISO's own behaviour**. Also found that ISO serves a newer 2027 Oregon edition than we hold (**OI-105**), so comparisons run at 2026-09-17 |
| C11-24 | Regression — confirm chunks 1–10's golden cases are unmoved by anything chunk 11 touches. **Run `104_chunk10_c10-21_regression.py`**, extended with chunk 10's own golden case | ✅ | **Done 2026-09-22.** The one-command regression covers **chunks 0–11**. **Close-out run: CLEAN, 69 of 69**, including all 16 GL suites, after four authorized engine fixes (gap 1, OI-102, OI-104, OI-107) |

---

## What chunk 11 inherits and must re-ask

* **C10-20's denominator lesson** — the ISO fixture corpus is **364 CF
  payloads**, not 924. Any fixture claim in this chunk states 364.
* **C10-20's "count records, not files" lesson** — a single-match regex over
  a payload finds the first record of a repeating type and silently misses
  the rest. Chunk 11 has 4 sub-coverages × 5 forms per submission, so this
  chunk is *more* exposed to that error than chunk 10 was, not less.
* **C9-19 / C10-14** — `IRPMFactor`/`PackageModFactor` depth. Already
  answered in outline by the census (16 of 32 files, the inverse of EQ) and
  owed a run by C11-15.
* **C8-23** — operand order is premium-bearing. Untested here, and the
  annuity is the most nested arithmetic in the project so far.
* **The "absent means zero, nothing raises" shape** — this project's
  recurring failure mode, and C11-04's whole reason for existing. An
  unmatched interest rate is the sharpest candidate: the table holds only
  whole percentage points 5 through 15.
* **Gate point 9** — the project-wide validation-message backlog remains open
  from chunks 1–10 regardless of what chunk 11 finds.
