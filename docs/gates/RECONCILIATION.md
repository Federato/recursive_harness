# Reconciliation — what the subline gates changed

**Updated 2026-08-11, after gates 334, 336 and 335.**

The two specifications — [`docs/rating-engine/`](../rating-engine/) (PDF-derived) and
[`docs/erc/`](../erc/) (ERC-derived, clean-room) — were produced **independently and before any
subline was derived end to end**. That independence is the project's main piece of evidence: where
they agree, the agreement means something. **So they are annotated here, not rewritten.** Each
affected file carries a dated banner pointing at this document; the original claims stand as the
record of what each derivation found on its own.

This file is the single authoritative list of what the gates superseded. It is the one place to
update when a gate lands.

---

## 1. The correction that matters most — and it is a correction to my own gate

**Every count of the "2027 migration" in this project, including the one gate 335 filed this
morning, was taken over the *latest* package per jurisdiction. The corpus holds 82 state packages
effective *after today*. So all of them describe a future state, and none describes now.**

Measured as-of a date, which is the only method N4 permits
(`scripts/erc/31_migration_asof.py`):

| As of | Pre-2027 basis | 2027 basis | Publishing OCP loss costs |
|---|---|---|---|
| **2026-08-11 (today)** | **51** | **0** | **51** |
| 2027-04-01 | 8 | 43 | 8 |
| latest filed | 8 | 43 | 8 |

**Nothing has migrated. Forty-three jurisdictions change class basis on a single day —
2027-04-01 — and the same date withdraws their OCP loss-cost tables.**

### What this changes

| Claim on record | Status |
|---|---|
| *"The rates are mid-migration. 15 jurisdictions are on the pre-2027 class basis, 36 have moved."* (`README.md` #4; `rating-engine/12`, `13`) | **Not current.** It describes the end state. Today the split is 51/0 |
| *"A single national class list is wrong today."* | **Inverted.** Today a single list is *right*; it stops being right on 2027-04-01 |
| *"OCP loss costs published in 8 jurisdictions, absent in 43"* (gate 335 §0, filed 2026-08-11) | **Mine, and wrong as stated.** True of 2027-04-01 onward. Today **all 51 publish them** |
| *"Both paths are needed by effective date, not by jurisdiction"* (gate 335) | **Stands, and is sharper than when written** — today *every* jurisdiction needs the loss-cost path |

### Why it happened, twice, to two independent derivations

The PDF derivation counted the latest *notice* per jurisdiction; the ERC derivation counted the
latest *package*. Different corpora, different units, same defect: **both took "latest" to mean
"current", and in a corpus with future-dated filings it does not.** The two figures differ (15/36
vs 8/43) only because the corpora were captured at different times and hold different numbers of
2027 filings.

I wrote **N4** and **habit 1** into the build plan in this same session, and then measured with
"latest" anyway. The rule was known and stated; it was not applied to my own arithmetic. The
defence is the script above, which takes an as-of date as a required parameter rather than a
convenience.

### Every other count taken the same way has now been re-tested

**OI-40 closed 2026-08-11** — [`OI-40-ASOF-RECOUNT.md`](OI-40-ASOF-RECOUNT.md),
`scripts/erc/32_asof_recount.py`. Of the five load-bearing figures re-measured at today /
2027-04-01 / end state, **two survived and three needed their tense fixed**:

| Figure | Verdict |
|---|---|
| Territory 27 ZIP · 20 constant · 4 county/place | ✅ identical at every date the corpus covers — phase 3's exit criterion stands |
| The **16** rate-driven coverage groups | ✅ identical **set** at all four measurements, verified as a set |
| N7 *"138 of 272 countrywide tables header-only"* | ❌ that is the 2027 edition. **111 of 266** today |
| *"238 pre-only · 204 2027-only · 959 both"* | ⚠️ correct from 2027-04-01. Today: **one list of 1,197** |
| *"477 groups: 16 · 383 · 78"* | ⚠️ a union over every edition ever filed. In force today: 458 groups. **And separately two short: the count is 18 · 383 · 76**, corrected 2026-08-11 — the classifier's rate-source list omitted `AdjustedRate` and filed both Unmanned Aircraft coverages as aggregators |

And the audit found the same error wearing two other costumes, neither of them about dates: **DE's
territory constant is filed under a fifth table name** (a hand-written classifier that knew only the
commonest name dropped a state), and **three declared countrywide parents are in force on any single
day** — for five states today the declared parent is not the newest. *"Latest ≠ now"* is one case of
*read the file, not the name.*

**It is also not a "migration in progress" at all — it is a cliff.** A rolling migration would let
an engine treat the class basis as a slowly-changing per-state attribute. A single-date cliff means
the class list, the OCP rating path and the OCP class codes all switch together for 43
jurisdictions at once, and an engine that resolves editions correctly gets this free while one that
caches "the current class list" gets it catastrophically wrong on one day.

---

## 2. Corrections to the specifications

Neither specification is *wrong on its own corpus*. These are places where a later, deeper reading
supersedes or sharpens what a single-pass survey found.

| # | Claim | Where | Superseded by |
|---|---|---|---|
| **R1** | 15/36 migration split, stated as current | `rating-engine/00`, `09`, `10`, `12`, `13`, `README`; `COMPARISON`; `BUILD-PLAN-PLAIN-ENGLISH` | §1 above. The mechanism the PDF derivation found — *"the withdrawal is sharply dated"* (`13` §13.7) — was **right**; only the framing as a present-tense jurisdiction split was wrong |
| **R2** | Workers Compensation loss costs listed as a missing external input | `rating-engine/00`, `09`, `13`, `README`; `COMPARISON`; `BUILD-PLAN-PLAIN-ENGLISH` | **Gate 335 §1.** Not a gap: the 75% is in ERC (`PrincipalsProtvLiabFactor`, countrywide `0.75`) and `WorkersCompensationRate` is a **declared submission field** that real STC submissions supply. Retired outright by the 2027 program |
| ~~**R3**~~ | ~~*"Terrorism premium cannot be computed"*~~ | `rating-engine/00`, `09`, `11`, `13`, `README` | **DISCHARGED 2026-08-12 by [gate terrorism](GATE-TERRORISM.md).** The audit ran: the population is **20 of 477** coverage groups, classified by rule content — and the `OTHER` bucket is not a miscellany, since four of them compute `Premium` from **other groups' finished premiums**, a rate source the classifier does not list. Manual against ERC is exact: **4 of 4** factor cells and **142 of 142** above-average classes. ***The claim is retired: terrorism premium CAN be computed.*** **And a correction the same day** (§3a): the countrywide `0.009`/`0.004` pair describes **36 of 51** jurisdictions — the other **15 file their own territory-keyed factors**, spanning `0.004`–`0.133`, New York adding a Manhattan table. OI-37 closed |
| **R4** | Medical payments folds into the ILF: `ILF' = medpay + ILF − 1` | `rating-engine/02`, `03`, `06`, `07`, `11`; `erc/03`; `COMPARISON` | **Gate 334 §0.** True of **CW 2027 only**. Editions through CW 2023 V03 charge it separately inside `SetPremium`. Algebraically identical, **rounds differently — ~$1 a line** |
| **R5** | `Premium = round(FinalRate × Exposure …)` treated as the general chain | `erc/03`; `rating-engine/11` | **Gate 335 §1.** OCP is **piecewise-linear** — two marginal tiers, a class-dependent breakpoint and divisor, six rate tables. The premium step is a per-subline strategy |
| **R6** | Override is by name, wholesale | `erc/03`, `04`; `COMPARISON` | **Gate 336 §6.** Correct, and incomplete: **the replacement may be empty.** 13 jurisdictions disable Defense-Within-Limits with a literal `<rul:Sequence />`. Empty ≠ absent ≠ inherit |
| **R7** | A `0` cannot be distinguished from a sentinel | `erc/04`, `06`; `COMPARISON` | **Gates 336 §0 and 335 §7.** Five meanings now identified, **four with an in-corpus discriminator** — see §3 |
| **R8** | Golden case reported as `PremOps 475.00` | build plan §6 *(already fixed)* | **Gate 334 §8.** `475.00` is a basic-limits figure consumed by no rule. The 334 premium is **`976.00`** |

---

## 3. The zero taxonomy — the single most reusable result

| Meaning of `0` | Example | Discriminator |
|---|---|---|
| a genuine factor | `DedFactorPremOpsCSL` "No Deductible" | the value is correct as read |
| an **unpublished** factor | the 15 "Per Claim" deductible factors | a `DoMessage*` validation rule (**N15**) |
| an **unguarded refer** | drone `>55 lb` band | **none in ERC** — the manual, plus the sentinel register |
| a **path switch to a table** | `ProdsCompldOpsLossCost = 0` → the ELP | the `*ELPText` selector (**N17**) |
| a **path switch to an input** | OCP `15191` → `0.75 × WorkersCompensationRate` | a hardcoded class branch in `SetELP` |

**The rating-basis selector (N17) is the load-bearing discovery.** Every subline carries a sibling
`*ELPText` table over a closed vocabulary — `Rate/Loss Cost Applies` · `Industry` · `Company` ·
`Not Applicable` — and the manual's ELP Supplement prints **`RTC`** for exactly the classes ERC
marks `Company`, so **`Company` means refer-to-company**, not "look up a company ELP".

Agreement with the `LossCost != 0` test the rules actually branch on:

| Test | Result |
|---|---|
| Prem/Ops, corpus-wide (`28_elp_selector.py`) | **620,856 agree · 0 disagree** |
| OCP, all 51 jurisdictions (`30_ocp_selector_and_refer.py`) | **433/433** and **147/147** exact; 8 input-derived |

---

## 4. New non-negotiables

Added to build plan §4 by the gates: **N15** (`DoMessage*` rules are part of the algorithm) ·
**N16** (row-level `state → "CW"` fallback inside one table, a *second* inheritance mechanism
alongside N3) · **N17** (read the rating basis from the selector; hard-fail on disagreement).

Sharpened: **N3** (empty override) · **N4** (as-of, and "latest" must be defined over the whole
population — §1) · **N12** (deductible subtracted from the ILF; med-pay edition-scoped) ·
**N13** (five meanings of zero, four discriminated).

---

## 5. Escalations

**Raised by the gates:** E11 (`AdditionalInterestFactor` — 334 does not read it, 336 does) ·
E12 (**closed**, dissolved on reading — two DataDefs at two levels) ·
E14 (`LookupPrincipalsProtvLiabFactor` has no caller in CW 2027).

**E1 is live, not theoretical.** The golden case hits no rounding midpoint, but a real OCP
submission does: `0.95 × 1.75 = 1.6625`, an exact 3dp tie.

---

## 6. What is deliberately *not* reconciled

- **The two specifications' independent counts.** Where they measure different units — rule
  instances vs coverage groups, notices vs packages — both stand, annotated. Collapsing them would
  destroy the cross-derivation evidence.
- **`rating-engine/` claims about the PDF corpus.** They describe that corpus accurately. Only
  claims that read as *general* facts about the program are annotated here.
- **The agents' knowledge bases.** Checked (§7); no invariant is contradicted.

---

## 7. Agent invariants — four were contradicted, and are now scoped

**This section originally said "no gate finding contradicts a published invariant." That was
asserted without checking, and it was wrong** — the same defect the rest of this document exists to
correct. Checked properly, **four** invariants in `iso-circular-expert` were affected, **three of
them `BLOCKER`**:

| Invariant | Was | Now |
|---|---|---|
| **`INV-VINTAGE-SPLIT`** `BLOCKER` | *"The rate corpus is mid-migration on a clean 15/36 split."* | Restated as **a single dated program change**. The 15/36 census is kept as a **PDF-notice vintage** fact with an explicit `scope`, plus an `as_of_correction`: 51/0 today, 43 migrating on 2027-04-01 |
| **`INV-OCP-WITHDRAWAL`** `BLOCKER` | *"15 jurisdictions still publish it; 36 have moved to ELP-only."* | Withdrawal is **on a single effective date**. Today **all 51 publish it and none has moved**; 43 withdraw on 2027-04-01 |
| **`INV-MEDPAY-ADDITIVE`** `BLOCKER` | *"Medical payments folds into the ILF additively."* | **Edition-scoped.** True of the 2027 manual and CW 2027. Editions through CW 2023 V03 charge separately — the golden case runs on that form and gives `976.00`, where the fold gives `975.00`. `check` now warns against flagging a premium before resolving the parent edition |
| **`INV-EXTERNAL-DEPS`** `MAJOR` | *"**Four** inputs are genuinely outside both corpora."* | **Three, then two.** Workers Compensation closed (R2); **Terrorism closed 2026-08-12** when the audit discharged R3. What remains genuinely external is **loss history** for experience rating (OI-02, confirmed against manual Rule 5.G) and **the company LCM** (E9/E15) |

**Method:** the *statements* were rescoped and the *measurements* preserved. The 15/36 count is
accurate for the PDF notice corpus and remains in `evidence`; what changed is that it no longer
reads as a claim about what is in force. Each entry gained a `scope` and, where relevant, an
`as_of_correction` field, and each now cites the gate alongside its original document.

Smoke tests re-run after the edit: **iso-circular-expert 15/15**, **iso-erc-expert 88/88**. The
circular agent's `jurisdictions.json` vintage census is untouched — it measures the PDF corpus and
is correct there, which is why the suite still passes.

`iso-erc-expert`'s invariants were checked and **none required a change**. `ERC-ED-001` already
states the as-of rule correctly (*"select the newest package whose edition_date <= the rating
date. 83 of 572 package directories are future-effective"*) — **the ERC agent had the rule that
would have prevented §1, stated plainly, the whole time.**

**Candidate invariants the gates add** — the selector agreement (N17), the empty-override rule
(N3), and the as-of cliff (§1) — are recorded here rather than injected, since adding an invariant
changes an authority and is a decision to take deliberately.
