# GL Rating Engine — Python Build Plan

**Governing doctrine, set 2026-08-10. This supersedes the prior framing, in which ERC and the
manual PDFs were treated as co-equal sources in defined roles.**

> Build the rating engine **based on the ERC files**, with the **PDFs as confirmation of the
> build, and not the source**. There are to be **no assumptions outside of what exists in the
> files**. Where confirmation is needed, **refer to the manuals**; and if that fails, **ask
> directly**.

Everything below follows from that. Where the previous plan reached for the manual to supply a
mechanism ERC lacks, this one escalates instead.

> **Standing instruction, 2026-08-11: no engine code is to be written until the user says so.**
> This document is a plan, not a work order. Analysis, measurement scripts, gates and documentation
> continue; `gl_rating_engine/` does not begin. The reason is on the record — **every gate so far
> has changed the architecture** (N15, N16, N17, per-subline premium strategies, edition-scoped
> calculators, a third countrywide calculator), so code written now would be written twice.
> Recommending that it is time to build is welcome. Beginning without being told is not.

---

## 1. The evidence hierarchy

Three tiers, strictly ordered. A tier may only be used for what it is licensed to do.

| Tier | Source | May be used to | May **not** be used to |
|---|---|---|---|
| **1 — Source** | ERC packages | Supply every value, table, key, rule, edition and structure the engine uses | — |
| **2 — Confirmation** | Manual PDFs | *Confirm* the meaning of something present in ERC; disambiguate a sentinel; corroborate a structure | **Supply a value or mechanism ERC does not contain** |
| **3 — Decision** | The user | Settle anything tiers 1 and 2 cannot | — |

**Nothing is invented at any tier.** If ERC does not contain it and the manual does not explain
it, the engine does not do it — it escalates, and until the escalation is answered the affected
path returns `REFER`.

### The rule that does the work

> **Tier 2 confirms; it never sources.**

Concretely: the manual may tell us that ERC's `0` in the drone table means *Refer To Company* —
that is confirming the meaning of a value **that exists in ERC**. The manual may **not** supply
an increased-limits interpolation procedure that ERC has no machinery for; that is sourcing a
mechanism, and it becomes an escalation (E6).

This distinction is the whole doctrine. Applied honestly it produces a shorter, sharper build
with a longer escalation list — which is the correct trade, because every escalation is a real
question that would otherwise have been silently assumed.

### When the two disagree

ERC is the source, so ERC's value stands — **but a disagreement is never resolved silently.**
It is logged, the affected component is marked `attested=False`, and it escalates. A conflict
between ISO's own data and ISO's own filed manual is a finding worth surfacing, not a tie to be
broken by precedence.

---

## 2. What this changes

| Previously | Now |
|---|---|
| A PDF-derived "semantic overlay" module supplying rounding, interpolation, eligibility | A **confirmation layer** that records only what the manual *confirmed* about ERC content, with the citation |
| Territory: ERC for 27, manual for 4 | **ERC for all 51** — proven: 27 ZIP · 20 single-territory · 4 county/place, all in ERC |
| ILF interpolation taken from Rule 56.A.4 | ERC has no interpolation machinery → **E6, escalated**. Off-table limits `REFER` until answered |
| Rounding defaulted to the manual's half-up | **E1, escalated.** The OK golden case is evidence, not authority |
| Manual-sourced corrections applied to the ERC premium chain | Proposed as confirmations; where they add a step ERC does not express, they escalate |

Two things get **better** under the stricter doctrine, not worse: territory needs no cross-source
dependency at all, and the escalation register makes explicit a set of assumptions the previous
plan would have absorbed quietly.

---

## 3. What ERC gives us, measured

| | Finding |
|---|---|
| Packages | 567 across 51 jurisdictions + countrywide, editions 2020-12-01 → 2027-04-01 |
| Identity | XSD `targetNamespace` yields jurisdiction/edition/version, **567/567** |
| Composition | State package names its own countrywide parent; **51,987** rule refs, zero disagreements |
| Override model | By name, wholesale. **100.0%** of 23,404 `Overridden` shadow a same-named parent; **0.0%** of 23,755 `StateSpecific` do |
| **What actually rates** | **18 coverage groups**, verified corpus-wide. **383** capture a user-entered `ManualPremium`; 76 are aggregators. Of 477 groups writing a Premium |
| Premium chain | Derived from 73,990 dataflow edges (§6) |
| Territory | All 51 resolvable — 27 ZIP · 20 single (19×`001`, NC `002`) · 4 county/place. **Re-verified as-of** today, 2027-04-01 and the end state: identical at all three ([`gates/OI-40-ASOF-RECOUNT.md`](gates/OI-40-ASOF-RECOUNT.md) §2) |
| Golden case | `OK/GL_OK 20250601 V01/STC/1. Output.json` — a complete rated policy |

**Verified corpus-wide 2026-08-10** (`scripts/erc/25_rating_vs_capture.py`): 572 package
directories, 9,509 premium-writing rule instances, 477 distinct coverage groups →
**18 RATE_DRIVEN · 383 CAPTURE · 76 aggregators**. The earlier "19 tables" counted schema tables
including minimum-premium top-ups; the substance is unchanged.

> **Corrected 2026-08-11 from 16/383/78.** The classifier decided *rate-driven* by matching the
> premium-writing rule against a list of rate-shaped source names, and **`AdjustedRate` was not on
> the list.** Two coverages compute `Premium = AdjustedRate × ILF × mods` and were filed as
> aggregators for that reason alone: **`GeneralLiabilityUnmannedAircraftCovABIPDCoverage`** and
> **`…CovBPAICoverage`**, both across 116 packages. Re-run corpus-wide over the same 572
> directories, exactly two groups move. **This is not an as-of defect** — OI-40's finding that the
> rate-driven set is stable across dates still holds; the *set itself* was two short.
> Found while listing the remaining gates, by asking why build-order item 7 (Unmanned Aircraft)
> had no rate-driven group despite being on the list as a rating subline.

**Re-tested as-of a date 2026-08-11** (`scripts/erc/32_asof_recount.py`, OI-40). The figure above is
a **union over every edition ever filed** — the right question for *what must the engine ever rate*,
the wrong one for *what is in force*. Restricted to the packages in force:

| | Groups | RATE_DRIVEN | CAPTURE | Aggregators |
|---|---|---|---|---|
| All 572 directories (union) | 477 | **18** | 383 | 76 |
| As of today | 458 | **18** | 356 | 84 |
| As of 2027-04-01 / end state | 476 | **18** | 376 | 82 |

**The rate-driven set is identical at all four measurements**, verified by set comparison rather
than by matching counts. It is the one headline figure the as-of defect did not touch. Phase 16 is
sized 383 deliberately — the harness must handle every group the engine may meet.

**The scan found four state-specific rating coverages a countrywide-only reading misses** —
Maryland lead-hazard liability, two Massachusetts lead-poisoning coverages, and **New York's
Special Protective and Highway coverage**, which exists in no countrywide edition and whose group
name carries no state ([`PHASE-SIZING.md`](PHASE-SIZING.md) §5). They are in the build order below.

---

## 4. Non-negotiables

Each is measured from the files, and each would produce wrong premiums if the architecture
ignored it.

| # | Rule | Evidence |
|---|---|---|
| **N1** | **A cell value is a typed disposition, not a number.** Not-offered and refer markers can never become numbers | Non-numeric markers are a large minority of grid cells. `Decimal` as the cell type is a defect |
| **N2** | **`RunRule@ProjectName` dispatches to the parent, bypassing the overlay** | 4,598 call-super rules recurse forever otherwise. Both layers must stay addressable |
| **N3** | **Override is by name, wholesale — never a row patch, and the replacement may be EMPTY** | 100.0% of 23,404 `Overridden` shadow a same-named parent; 0.0% of 23,755 `StateSpecific` do. 13 jurisdictions disable Defense-Within-Limits with a literal `<rul:Sequence />`. **Empty ≠ absent ≠ inherit** — treating an empty body as fall-through applies a factor those states filed away. **And an override need not be empty to neutralise:** New York disables claims-made liquor by replacing `SetYearInClaimsMade` and `SetClaimsMadeMultiplier` with **constant stubs** (`0` and `1.0`) rather than empty bodies (gate 332 §7). A check that looks only for empty bodies misses it. **Measured whole 2026-08-12 ([`gates/NEW-YORK-DIFFERENTIAL.md`](gates/NEW-YORK-DIFFERENTIAL.md)): New York carries 698 overrides — 151 empty bodies, of which 130 replace a non-trivial parent and 83 are `ErcRate`, switching rating off for 83 endorsements; plus 98 constant stubs, the class an empty-body check cannot see.** And the liquor finding was one coverage of **five**: the claims-made stub runs in Prem/Ops, Products, Liquor and both Unmanned Aircraft groups, with all four multiplier tables overridden to 0 rows against a 5,940-row countrywide original (OI-59) |
| **N4** | **Edition selection is as-of a date, never "latest"** | 83 future-dated packages. Live case: **six jurisdictions (CA FL GA KY VA WA) retired their Defense-Within-Limits override** — VA carried it in 2021, absent from 2023 on. Same state, different premium by effective date. "Latest" must also be defined over the **whole** package population, never over the packages that happen to match — **and never taken to mean "now": 82 state packages are effective after today, so every "latest" count in this project described a future state until it was re-measured as-of a date** ([`gates/RECONCILIATION.md`](gates/RECONCILIATION.md) §1). **Strongest case is 335**: CW 2023 rates it in 21 steps with two marginal tiers, a loss-cost path and a Workers Compensation input; CW 2027 rates it in 12 with none of those. Two coverages, one name, selected by the resolved parent |
| **N5** | **The state package names its countrywide parent** — take that one, not the newest | 51,987 rule references, zero disagreements |
| **N6** | **Identity comes from the XSD `targetNamespace`, not the directory path** | 567/567 accurate; directories were misfiled twice, upstream |
| **N7** | **Presence ≠ population ≠ purpose.** A table may exist and be empty; the rows may be filed under a different **name**; and the table may have **no reader at all** | **Measured as-of** ([`gates/OI-40-ASOF-RECOUNT.md`](gates/OI-40-ASOF-RECOUNT.md)): **111 of 266** countrywide rate tables are header-only in the edition in force **today**; **138 of 272** from 2027-04-01. Header-only in all ten countrywide editions for every rating table the three gates cite. **And `PremOpsLossCost` is header-only in CA, NJ, NY and OH, which file 66,573 loss-cost rows under `PremOpsLossCost<ST>Terr<nnn>` instead** — an assertion of *"no empty table in a rating path"* fires on all four and is wrong every time (OI-20, closed). **Third form, from gate 335-RR: a table may have no purpose at all.** `RailroadLossCost` exists in all ten countrywide editions, has 0 rows in every edition and all 51 jurisdictions, and is **referenced by no rule anywhere in the corpus**. Railroad's loss cost is **OCP's**, read as `LookupOwnersContractorsLossCost("16292")`. Inferring a rating path from a table name builds a branch ERC does not have. **Second orphan, gate 365: `SublineProductWithdrawal`**. *(Both demoted 2026-08-11 by `34_crosscheck.py`: they are **2 of 79** unread countrywide tables, an unremarkable class of empty schema stubs. The assertion worth making is the narrow one, and it passes — **0 of 79 unread tables carry rows**, so no published rate content is orphaned. Reporting the two as notable was itself an aggregate claim with no denominator.)* |
| **N8** | **Loss costs are state-supplied; the algorithm is countrywide** | Confirmed independently by both derivations |
| **N9** | **Refer-to-company is a first-class outcome, not an error** | ~5,300 declared refer situations; a `Refer To Co.` cell sentinel; capture tables with no premium |
| **N10** | **Decimal throughout, never float.** Rounding is `rul:Round DecimalPlaces=n` at 648 sites | 3dp ×290 · 0dp ×238 · 4dp ×32 · 2dp ×22. Only the tie-break mode is unstated (E1). **A fifth precision was missing from this list until 2026-08-12: `8dp`, at 3 sites in every countrywide edition and 0 of 51 jurisdictions** — `GeneralLiabilityCompositeRating::SetCompositeRate` and **two in Railroad**, `SetContractCostFactorWOHzd` / `WithHzd`, which gate 335-RR derived without recording the precision. A `Decimal` context configured from the four-value list rounds all three silently ([`gates/GATE-RATING-PLANS.md`](gates/GATE-RATING-PLANS.md) §4, OI-62) |
| **N11** | **Rules are keyed semantically, never by printed number — not by name-plus-count, and not by numbers embedded in rule or DataDef names** | The 2027 countrywide edition reuses rule numbers for different concepts. **Railroad is the sharpest case (gate 335-RR §2): `SetBaseELPRR40014` tests class `40011` and writes a DataDef called `BaseELPRR40006` — and `40006` is *"Miscellaneous"*, an unrelated classification.** The rule names refer to the *rate basis applied*, the DataDef names to nothing at all. Only `SetILF40014` is consistent end to end. **And two countrywide editions in force today carry the *same 100 rule names* for Prem/Ops with *40 differing bodies*.** **Now measured whole ([`gates/CALIFORNIA-DIFFERENTIAL.md`](gates/CALIFORNIA-DIFFERENTIAL.md)): the two parents ship the same 547 files and the same 4,461 rule names, with 345 different bodies and zero rules added or removed.** **341 of the 345 are a single change** — V03 wraps writes in `if (target IsNull)` over 210 further DataDefs, making them write-once where V02 recomputes; with `ClearCache="true"` on **5,601 of 5,601** `RunRule` calls, that guard *is* the memoisation. *(The first reading of it — "V02 overwrites a broker-supplied value" — did not survive reading the rule: `SetGeneralAggregateLimit` copies from the same policy-level source in both editions.)* A phase-sizing pass that compared names and counts called those editions identical ([`PHASE-SIZING.md`](PHASE-SIZING.md) §4) |
| **N12** | **The deductible factor is subtracted from the ILF; medpay is edition-scoped** | `FinalILF = round(CSLILF [+ medpay − 1] − FinalDeductibleFactor, 3)`. The medpay fold is **CW 2027 only** — earlier editions charge it separately (§6). The manual's own worked example, `1.020 + 1.95 − 1 = 1.97`, confirms the 2027 form: `GL-MU-2027-RU-001-C` p.32, Rule 56.D.2 |
| **N13** | **A factor of `0` must pass a sentinel check before it multiplies** | Zeros occur in **31 of 79** tables and are usually legitimate. **Two confirmed sentinels so far.** (1) **The drone usage modifiers — now fully decoded (gate 370).** `UnmannedAircraftUsageBIPDRatingModifiers` carries `0` in **five** rows, not three: firefighting, crop-spraying, internet access, **entertainment/special events/drone racing**, and **`Other usage, not otherwise classified`** — the catch-all a submission lands on when nothing else fits. `…UsagePAIRatingModifiers` carries **three** more. All eight are read by `SetAjustedRate` and multiplied **with no guard**. **Manual `GL-MU-2027-RU-001-C` p.68 Table 37.E marks exactly those eight `RTC`, and no others: 12 rows × 2 columns, 24/24, exact in both directions.** **And the same usage differs by column** — firefighting is `RTC` for BI/PD and `0.90` for PAI — so a sentinel register must be keyed on *(table, column, row)*, never *(table, value)*. **Verified exhaustively that there is no in-corpus discriminator:** zero `DoMessage*` rules in either rate-driven group; the only guard in the subline is `MaximumTakeoffWeight <= 0`. **And the sentinel is bigger than the usage table: 18 of the 60 cells across all three rating axes × both coverages are `0`** — Usage (5+3), Ownership & Operation (3+3), Primary Place of Operation (2+2). Three kinds: uses ISO will not price (8), the *non-owned aircraft* condition (2), and — **filed as domain values** — **`Unknown` (×4) and `Not Applicable` (×4)**, i.e. *the submission did not say*. **That last group is what makes OI-48 answerable without inventing anything:** a broker who cannot resolve which category applies has a filed way to say so, and it refers. (2) On the **primary 334 path**, all 15 *"Per Claim"* deductible factors are `0` countrywide while every *"Per Occurrence"* row is real; guarded only by a `DoMessage*` validation rule, and an unguarded `0` there **overcharges** by withholding the credit. **A third meaning found in 336: a published `0` loss cost is a documented switch to the ELP path** — read as a rate it yields a free policy. **A fifth found in 335: a `0` ELP that switches to an *input-derived* computation** (class `15191` → `0.75 × WorkersCompensationRate`), discriminated by a hardcoded class branch in `SetELP`. **Four of the seven have an in-corpus discriminator, and gate 370 proved the drone case has none** — that is now measured, not assumed, and the register can stop carrying it as unfinished. **Two more found in 332, taking it to seven** — (6) a **genuine** zero: `LiquorLiabGrade = 0` means *no cause of action against the liquor vendor*, confirmed at `GL-MU-2027-RU-001-C` p.101 Rule 45.H.1; and (7) a **coverage-not-offered** zero: New York replaces `SetBaseRate` with an occurrence-only rule, so a claims-made liquor risk silently prices at `0`. **Stop enumerating meanings and start measuring discriminator coverage** — 332 found a discriminator that exists and still misses half the defect: `DoMessageMustEnterLiquorDeductibleFactorOverride` guards 10 of the 21 zero deductible factors, leaving all ten *Per Common Cause* options unguarded and the insured overcharged (OI-44). **An eighth meaning, from the size-of-risk gate: a `0` that is a class-eligibility statement** — **188 of 1,188** class codes carry a zero size-of-risk loss cost and **the same 188 in all 35 shipping jurisdictions**, so it is countrywide content filed per-state (E19). **Discriminator coverage there is 0 of 388** `DoMessage*` rules corpus-wide. **And the size-of-risk gate supplies the register's first *guarded* counterexample:** all ten setters and both consumers test `SizeOfRiskRatingApplies == "Yes"` before the relativity is read or multiplied, so the not-applicable `0.0` default provably cannot reach a premium — the guard is on the **flag**, not the value, so a `0` reached while the flag is `Yes` still refers |
| **N18** *(new, gate 332)* | **A sentinel is data, not a constant. Every literal an engine compares against is edition-scoped** | The liquor refer marker is spelled **`Refer To Co.`** in all nine pre-2027 countrywide editions and **`Refer to Company`** in CW 2027 — and on `2027-04-01` **both are live in the corpus at once**, the old spelling in the 8 unmigrated jurisdictions and the new one in the 43 migrated. Each edition's `SetPremium` tests only its own spelling, so ERC is internally consistent and a **global sentinel constant is wrong for 8 or 43 jurisdictions whichever value it takes**. ISO's own CW 2027 shows the failure mode: `SetLiquorExposureStatCode` was left testing the pre-2027 strings, so 2027 liquor exposure is **reported 1,000× too large** (OI-43) |
| **N14** | **Validate every enumerated input against its domain table — and when there is no domain table, find where the domain IS filed** | `DomainEachOccurrenceLimit` is a closed 13-row domain. Off-domain input is rejected, never interpolated. **`SizeOfRiskRatingApplies` is the counterexample that sharpens the rule:** a policy-level input with no writer rule and no entry in any of the countrywide package's **417** domain tables, compared literally to `"Yes"` at 28 of its 30 comparison sites. Its filed domain is nonetheless closed and discoverable — `RatingIdentificationCode.RateTable.csv` is **4 rows** keyed on it, enumerating **2 of 2** values `{Yes, No}`. **"No domain table" is not "no domain"; validate against the key column** (gate size-of-risk §6) |
| **N15** | **`DoMessage*` validation rules are part of the algorithm, not commentary — and a guard may be narrower than the defect it guards. Sometimes the guard is the ONLY statement of a bound** | Several of ERC's guards exist **only** there, including the whole defence for N13's second sentinel. Porting the rating chain alone drops them silently. **And porting the guard is not enough either:** in 332 all **21** liquor deductible factors are `0` while `DoMessageMustEnterLiquorDeductibleFactorOverride` covers only the **10** *Per Claim* options, so ten *Per Common Cause* options overcharge with no message. The manual (Rule 45.J.3, p.102) requires a referral for **all** of them. **Measure a guard's coverage against the defect; never assume they are the same set.** **And two 2026-08-12 findings show a guard carrying a bound that exists nowhere else:** the Limited Product Withdrawal chain computes `FinalILF = CSLILF − DeductibleFactor` with **no arithmetic floor**, and the only things preventing a negative rate are `DoMessageProdWithdrawalDedFactorCannotExceedPWILF` and **the corpus's sole negative-premium guard** ([gate 365 §9](gates/GATE-365-WITHDRAWAL-LOED-CYBER.md)); and terrorism's endorsement factor is a user input whose only filed range — `0 < f ≤ 0.004` — lives in `DoMessageWhenNoClassIsAnAboveAverageExposureClassTheExposureClassFactorCanBeFrom0to004` ([gate terrorism §6](gates/GATE-TERRORISM.md)) |
| **N16** | **Lookups fall back row-wise from the state row to a `"CW"` row inside one table** | Every 334 lookup is a `FirstNonNull` of two `Lookup` calls on the same table, keyed `/*/State/Code` then literal `"CW"`. This is a **second** inheritance mechanism, distinct from N3's package-layer override-by-name. Both are live at once |
| **N17** | **The rating basis is declared, not inferred.** Read `*ELPText`; assert it agrees with the `LossCost != 0` branch test | **Every rate-driven coverage carries a rating-basis selector, over a closed 4-value vocabulary** — `Rate/Loss Cost Applies` · `Industry` · `Company` · `Not Applicable`. **Enumerate them by that vocabulary, never by table name.** Sweeping every rate-table column for the vocabulary finds **seven** as of 2026-08-11, where matching `*ELPText` finds four: `PremOpsELPText`, `ProdsCompldOpsELPText`, `OwnersContractorsELPText`, `LiquorELPText`, plus **`RailroadELP`** (value column named after the table, `Industry` in all 204 rows), **`SpecialProtectiveHighwayELPText`** (NY only, `Company` in all 3 rows) and **`PremOpsELPTextTerr001`** (NY shards its selector by territory — OI-20's pattern applied to a selector). **A single-valued selector means the coverage has exactly one rating path** — railroad is ELP-only and the manual agrees (Rule 49.E.1, p.126, *"Refer to company"*). **A dependent coverage may borrow its host's selector**: `SetProductWithdrawalELP` calls `LookupProdsCompldOpsELPText`. *(This rule was briefly narrowed on 2026-08-11 by a search for `RailroadELPText` that found nothing; the selector was there under another name. Corrected in gate 335-RR §1.)* — `Rate/Loss Cost Applies` · `Industry` · `Company` · `Not Applicable`. Tested corpus-wide: **620,856 agreements, 0 disagreements** on Prem/Ops. **Corroborated a third time on OCP, the hardest case** (loss-cost table absent in 43 of 51, so nearly every risk takes the ELP path): 433/433 and 147/147 exact. And the manual pins the vocabulary — its ELP Supplement prints **`RTC` for exactly the classes ERC marks `Company`**, so `Company` means *refer to company*, not *look up a company ELP*. A disagreement is a load-time hard failure |

**N13 is the one with a live failure attached.** Unhandled, it returns a **$0 premium on exactly
the risks meant for human review**. The defence is a confirmed-sentinel register consulted before
any factor multiplies — not a scan, because a sentinel is indistinguishable from a real zero by
inspection.

---

## 5. Architecture

### The fork is decided: EXECUTE ISO's rules, do not transliterate them

**Decided 2026-08-12 by the user.** ERC is not a data format with rules written about it — **it is a
rule language with an interpreter implied.** The engine implements that language once and executes
the filed rules; it does not re-express them in Python.

**The decision is sized, not assumed.** Measured across **6,810 rule files in all 61 packages**:

| | |
|---|---|
| Instruction occurrences | **809,088** |
| Distinct node types | **58** — 4 structural wrappers, **54 executable** |
| Distinct attributes | **26** |
| Coverage by the **top 10** nodes | **74.2%** |
| Coverage by the **top 20** | **94.1%** |
| Coverage by the **top 30** | **98.5%** |
| Nodes appearing fewer than 500 times | **14** — the entire long tail, including `Round`, `Max`, four date operations and `GetList` (**2 occurrences**) |

**That is a small language.** Roughly 20 node types make a working interpreter and 54 make a
complete one — against the alternative of hand-writing 4,461 rules per package and **345 more for
California alone** (see [`CALIFORNIA-DIFFERENTIAL.md`](gates/CALIFORNIA-DIFFERENTIAL.md)), then
repeating it for every future ISO filing.

**E3's residual is now live work.** That escalation closed with *"the evaluation contract, only if
interpreting"*. We are interpreting, so the evaluation contract — what each node means, in what
order children evaluate, how nulls propagate — is a deliverable rather than a footnote.

### Module layout

```
gl_engine/
  domain/          Money, Rate, Disposition, Limit, ClassCode, Territory, Exposure
  erc/             THE SOURCE — package discovery, identity, tables, rules, editions
  interp/          the ERC instruction interpreter: 54 node types, the evaluation
                   contract, DataDef addressing, RunRule dispatch, write-once semantics
  resolve/         edition selection, CW+state composition, parent dispatch
  confirm/         tier-2 register: manual citations that confirm ERC meanings
  escalate/        tier-3 register: the 28 referral conditions and their resolutions
  rating/
    kernel.py      submission -> resolved packages -> execute -> premium + factors
  trace/           provenance-tagged execution trace
  schema/          per-state submission shapes; enum extraction
  cli.py
```

**`rating/sublines/` is gone.** Under the previous fork it held one module per subline per edition
family; there is nothing for it to hold when the rules are executed rather than rewritten. **The
eleven coverage walkthroughs do not become code — they become the acceptance tests that prove the
interpreter reproduces them.**

### Company deviations: not built in phase 1, but the shape is fixed now

**Decided 2026-08-12.** No carrier rates pure ISO. Deviations — the carrier's own loss cost
multiplier, class relativities, ILFs, coverages ISO does not offer, rules ISO does not have — are
**deliberately out of phase 1** and **deliberately designed for from stage 2 onward.**

**Why they are out of phase 1.** RAaS rates ISO content. The instant company content is layered on,
**no oracle can confirm the answer.** Deviating from an unproven foundation means a difference can
never be attributed: is that the deviation working, or the engine failing? **The ISO baseline must be
trusted before anything sits on top of it.**

**Why the design cannot wait.** Three constraints below are cheap now and invasive after the
interpreter is written against a two-layer assumption.

#### C1 — The layer stack is an ORDERED CHAIN, not a pair

`ResolvedBook` today holds `state` and `parent`. That binary must become an ordered chain:

```
company-state        most specific
company-countrywide
ISO-state
ISO-countrywide      least specific
```

`parent_table()` / `parent_rule()` become `next_layer()` over the chain. **The code change is small;
the decision inside it is not.** Does a company *countrywide* deviation outrank an ISO *state*
exception? That is a filing question with no correct default, answered **per carrier**, and it must
be configuration rather than a hardcoded ordering.

**Stage 2 API rule:** nothing in `interp/` may assume exactly two layers, and nothing may name a
layer `parent` where it means *the next one down*.

#### C2 — ISO's `@parent` KEEPS ISO'S MEANING (the dangerous one)

N2's 4,598 call-super rules say *"do what my parent does, then adjust"*. **`@parent` there means the
countrywide package ISO's own filing declares** — a semantic ISO fixed at filing time.

**If a company layer is inserted into the chain and `@parent` resolves through it, we silently
rewrite ISO's rules.** The premium comes out finished, plausible and wrong.

Two ideas, never to be conflated:

| | |
|---|---|
| **ISO's declared parent** | Semantic. Fixed by the filing. Read from the XSD import (N5). **Never reinterpreted by our layering** |
| **Our layer chain** | Compositional. Ours to define and to reorder per carrier |

**Stage 2 must expose them as two distinct operations with two distinct names.** A single `parent()`
serving both is the bug.

#### C3 — Behaviour and content are INDEPENDENT AXES

The two modes are about **referral behaviour**. Deviations are about **which content is loaded**.
They are orthogonal and must not be welded together:

| | ISO content only | ISO + company layers |
|---|---|---|
| **`strict-erc`** | The RAaS comparison baseline. **Must remain permanently runnable** | Company rating with no referral policy |
| **`underwriting`** | ISO rating under the referral register | **What would actually ship** |

**`strict-erc` over ISO-only content must stay runnable forever**, including after deviations exist.
It is the only configuration an external oracle can score, so it is the only thing that keeps the
foundation verified.

#### What deviations get, free, from the interpreter decision

| | A deviation is… |
|---|---|
| Transliterated engine | **A code change** — edit, review, regress, release |
| This design | **Content** — diffable, actuarially reviewable, effective-dated, and inheriting every load-time assertion already built |

The commonest deviation shape — *ISO's answer × our factor* — is already the shape of 4,598 ISO
rules, so the dispatch machinery arrives free.

#### Two questions left open on purpose

**Authoring format.** ERC's own format (best for the engine, verbose for humans) versus a simpler
overlay we convert. **Decide against a real deviation, not in the abstract.**

**Expressiveness ceiling.** ISO's 58 instructions express what ISO needed. A tier factor, a model
score, or a rating step ISO does not have may not be expressible, and would need a vocabulary
extension or an escape hatch to code. **Find this limit on a real deviation rather than reasoning
about it.**

---

### Two modes, one code path

**Decided 2026-08-12 by the user.** ISO's files return `0` where the referral register says stop —
the 18 drone markers, the ten cannabis classes, the fourteen states with no size-of-risk rates. Both
behaviours are wanted, for different reasons:

| Mode | Behaviour | For |
|---|---|---|
| **`strict-erc`** | reproduce ISO exactly; referrals **recorded, not enforced** | proving correctness against RAaS, where a difference is a defect |
| **`underwriting`** | referrals **enforced**; rating pauses and asks | what would actually be shipped |

**One flag, one code path, and the diff between the two modes is itself a report** — it lists every
risk where ISO would quote and we would not.

`confirm/` and `escalate/` are **modules, not documentation**. A confirmation is a data record
with a citation; an escalation is a typed object that forces a `REFER` until answered. Neither
can be satisfied by a developer's judgement at the keyboard.

### A referral-only input may be sourced from the manual; a rating input may not

**Decided 2026-08-12 (register `R25`), and it refines §1's evidence hierarchy rather than bending
it.** Four submission requirements have been added so far — county/place, `WorkersCompensationRate`,
the three drone axes, `SizeOfRiskRatingApplies` — and **every one of them had a filed ISO value
behind it.** The fifth does not.

Railroad class `40014` is *"operations with no work within 50 feet of tracks"*. The ELP Supplement
rates it **at 150% of class 16292 if the operations are construction, and refers everything else**.
ERC implements the first branch only, and the one field that looked like a discriminator —
`RailroadClassDescription` — is tested for **non-emptiness, never for content**. So asking the
broker *"is this construction?"* adds an input ISO's data model does not define.

**The ground for allowing it:** *the manual confirms and never sources* governs **rating**. An input
that can only ever produce a `REFER` takes no price from anywhere — it declines to quote.

**The limit, which matters more than the permission:** this licenses **referral-only inputs and
nothing else**. An input that changes a number still may not be sourced from the manual. If a
proposed field could ever move a premium rather than stop one, it is out of scope and belongs in an
escalation to ISO.

### A `REFER` is not always the end of the quote

**Decided 2026-08-12 (register `R19`).** *Refer to company* means what it says: ISO declines to
price the risk and hands it to the carrier. So the engine's job is not to stop — it is to **stop,
say precisely what it needs, and resume when it is given.**

| | Supplied | When | Example |
|---|---|---|---|
| **Carrier parameter** | once, per carrier | **configuration time** | the `LCM` (`R18`) — engine refuses to start without it |
| **Risk-level company input** | per submission | **at the referral** | a drone rate where ISO files `0` (`R19`) — underwriter supplies it, rating resumes |

**Both are company inputs and they behave completely differently**, so the architecture carries
both: one is configuration, the other is a resolvable escalation. An `escalate/` object therefore
has a **resolution** — the named value that clears it — and a `REFER` with no resolution (a
genuine dead end) is the *narrower* case, not the default one.

### The propagation rule turns on resolvability, not on the operator

**Decided 2026-08-12 (`D01`).** The first formulation — *`REFER` is absorbing under multiplication
but not under summation* — was wrong, and terrorism is what exposed it. Terrorism's base is a **sum**
of three sibling premiums, so an operator-based rule would have let it rate on a partial base when
one component referred. Distributing the multiply is mathematically exact
(`(a+b+c)×f = a×f + b×f + c×f`) and practically useless, because **a referral here is resolvable**:
the missing number is coming, so a terrorism charge computed on a partial base is stale the moment
the underwriter answers.

> **Anything downstream of a RESOLVABLE referral pauses with it and is computed once, after
> resolution. A dead-end referral — one nothing can clear — permits partial results.**

The policy total still behaves as intended: twenty classifications with one referral still quote the
other nineteen, because those are not downstream of the pause.

**Two consequences to accept explicitly:**

- **Terrorism is computed last and possibly twice** — once suppressed, once for real. The trace must
  record that it was **withheld**, not that it was zero.
- **ERC's `IsNotNull → 0` pattern must not be copied.** `SetClassCoveragePremium` carries six guards
  and three zero defaults, so an absent sibling contributes nothing. That is right for a coverage the
  policy does not have and wrong for one an underwriter is still pricing — and **ERC cannot tell them
  apart, so the engine must.**

A resolved referral re-enters the chain at the point it left, and the trace must record both the
raise and the resolution, or an audit cannot tell a quoted-after-referral premium from one that never
referred.

### Dispositions are monotonic

**Decided 2026-08-12 (`D02`).** ERC re-evaluates coverages in the 14 `PremiumToReachMinCoverage`
groups, and California's parent recomputes 213 DataDefs that every other jurisdiction writes once
(OI-58) — so a value can genuinely be produced twice.

> **A raised referral is never cancelled by a recalculation.** A later evaluation may add referrals;
> it may not remove one. Only the named input arriving clears a resolvable referral.

**The premium half of OI-58 is testable and the referral half is not.** `Payloads/CA` is a rated
output, so California's write semantics can be checked against ISO's own answer once the engine
exists. **RAaS returns a premium and has no notion of a referral**, so no oracle can ever say whether
a second pass should be able to un-raise one. That makes it a design choice, and the conservative
direction cannot produce a wrong price: over-caution shows up as referrals a second pass would have
cleared — visible and fixable — while the opposite error is a silent quote on a risk that should
have been seen.

### 4.1 The typed cell

```python
class Disposition(Enum):
    PUBLISHED   = auto()   # a value ERC states
    NOT_OFFERED = auto()   # ERC's not-offered marker
    REFER       = auto()   # ERC's refer marker, a confirmed sentinel, or an open escalation

@dataclass(frozen=True)
class Cell:
    disposition: Disposition
    value: Decimal | None
    erc_source: Citation              # tier 1 - always present
    confirmed_by: Citation | None     # tier 2 - only when the manual confirmed a meaning
    escalation: str | None            # tier 3 - E-number, if this path is blocked

    def require_value(self) -> Decimal:
        if self.disposition is not Disposition.PUBLISHED:
            raise ReferToCompany(self.erc_source, self.confirmed_by, self.escalation)
        return self.value
```

Every cell carries where it came from. `erc_source` is mandatory — **a value with no ERC source
cannot be constructed**, which is the doctrine enforced by the type system rather than by review.

### 4.2 The resolver — countrywide base, state children, effective date

```python
class EditionResolver:
    def resolve(self, juris: str, eff: date) -> Instance:
        # 1. packages for juris; identity from XSD targetNamespace (never the directory path)
        # 2. discard editions effective after `eff`      - as-of, never "latest"
        # 3. latest remaining; tie-break on version token
        # 4. read its xs:import -> THAT countrywide parent, not the newest
        # 5. parent absent -> hard failure, never a fallback
```

Composition keeps **both layers addressable**. `RunRule@ProjectName` must dispatch to the parent
bypassing the overlay, or 4,598 call-super rules recurse forever:

```python
class ResolvedBook:
    def table(self, name) -> Table          # state override wins, else countrywide
    def parent_table(self, name) -> Table   # explicitly the CW copy
    def rule(self, name) -> Rule
    def parent_rule(self, name) -> Rule
```

`table()` raises on an empty table reached in a rating path — 138 of 272 countrywide rate tables
are header-only, and a silent empty read becomes a zero premium.

---

## 6. The premium chain

As ERC expresses it:

```
BaseRate  = round(LossCost | ELP  × LCM  [× ClaimsMadeMultiplier], 3)
FinalILF  = round(CSLILF [+ MedicalPaymentsFactor − 1] − FinalDeductibleFactor, 3)
FinalRate = round(BaseRate × FinalILF × PackageModFactor × ExperienceRatingMod
                     × ExpenseModification × ModToUse  [× SizeOfRiskRelativity], 3)
Premium   = round(FinalRate × Exposure[/1000] [+ MedicalPaymentsCharge], 0)
Total     = Σ Premium, then policy minimum
```

**The two bracketed medical-payments terms are alternatives, and the countrywide edition decides
which.** Editions through `GL_CW_20231201_V03` charge med-pay separately and add it inside
`SetPremium`; `GL_CW_20270401_V01` folds it into `FinalILF` and has no `SetMedicalPaymentsCharge`
rule at all. The two are algebraically identical and **round differently — worth about $1 a line.**
So the *chain itself*, not merely the rate tables, is edition-scoped; **10 distinct countrywide
parents are in live use** across the 562 state packages. Derived and quantified in
[`gates/GATE-334-PREMISES-OPERATIONS.md`](gates/GATE-334-PREMISES-OPERATIONS.md) §0.

**This chain is not universal.** Subline 335 (OCP) is **piecewise-linear** — two marginal tiers with a
class-dependent breakpoint (`$1,000,000`, or `100 units` for the pre-2027 classes `27111`/`27112`)
and a class-dependent divisor, reading **six** rate tables. The premium step is a per-subline
strategy, never a shared `rate × exposure` helper.

`[/1000]` applies to nine premium bases (Admissions, Area, Gallons, Gross Sales, Kilowatt-hours,
Payroll, Total Cost, Total Operating Expenses, Vehicles) — ten before 2027, which dropped
`Passenger Days`. Under CW 2027 a premium that computes to `0` while exposure `> 0` is **floored at
`$1`**, so a broken rating path returns a plausible dollar rather than a visible zero.

Corroborated by the golden case (`GL_OK 20250601 V01`, parent `GL_CW_20231201_V03`):
`BaseRate 0.095 × FinalILF 2.05 → FinalRate 0.195` (0.19475 at 3dp — **not** a tie),
med-pay charge `1`, **334 `Premium` 976.00**, total `7,839.00`. `AnnualBasicLimitsCoPremiumPremOps
475.00` is a basic-limits figure consumed by no rule — not the subline premium.

**All three modification multipliers are rule-computed, not external** (read in full, Step 21):
`SetModToUse` (schedule-rating factor, else CPP IRPM factor, else `1.0`);
`SetExpenseVariationFactor` (`ERPExpectedLossRatio ÷ ERPActualExpectedLossRatio` at 3dp when
experience rating and expense variation both apply, else `1.0`); `SetPremiumDiscountCharge`
(`round(1 − pct × 0.01, 3)`, else `1.0`). Implement the rules; do not treat them as inputs.

**`LCM` is held at `1.0` by decision** — a carrier deviation, out of current scope. Modelled as a
named, overridable parameter so a carrier value drops in without touching the chain.

**Rounding is explicit**: `rul:Round DecimalPlaces=n [ToDataDef=X]`, 648 sites — rates and factors
at 3dp, `Premium` at 0dp, loss costs at 2dp. Only the tie-break mode is unstated (E1).

---

## 7. Escalation register

The doctrine's output. Each is ERC-checked, manual-checked, and unresolved — so each comes to
you. Ordered by how much premium they move.

| # | Question | Status | ERC evidence | Effect |
|---|---|---|---|---|
| **E1** | Rounding **tie-break mode** | 🟡 reduced | `rul:Round DecimalPlaces=n [ToDataDef]` at **648 sites** — 3dp ×290, 0dp ×238, 4dp ×32, 2dp ×22. **No mode attribute anywhere.** The golden case hits no midpoint (re-verified at all four 334 sites and all four 336 sites). **But a real OCP submission does**: AR class `15192`, `0.95 × 1.75 = 1.6625`, an exact 3dp tie — `HALF_UP → 1.663`, `HALF_EVEN → 1.662`. **E1 is live, not theoretical**. **But it can be closed per-subline: gate 370 §3 shows it cannot bite on Unmanned Aircraft** — `maximumTakeoffWeightCeiling = round(w + 0.499, 0)` ties only at `w = n + 0.001`, and the loss-cost band edges (1, 5, 15, 55) mean both candidates land in the same band at every realistic weight. **Do the same analysis per subline rather than waiting for RAaS** | Configurable; sites flagged. ≤ $1/line at 0dp. Settled by RAaS |
| ~~E2~~ | ~~`ErcCore`~~ | ✅ closed | `xs:import erc://ErcCore/CoreRecordEntry` supplies **2 of 28,233** elements (`CoreRecordEntry`, `Scheme`) — a transaction envelope | Affects XSD validation of the envelope only. Does **not** gate rating |
| ~~E3~~ | ~~Operator semantics~~ | ✅ closed | `FirstValue @Order` = `DataDefInputParamConstant` (**1 value**, 18,516×); `@OutputAction` = `Append` (**1 value**); no `MessageHelper` method calls | No branching to misinterpret. Residual: the evaluation contract, only if interpreting |
| **E4** | `Status` A/C/D | 🔴 open | Undefined across 2,865 metadata files **and all six DOC workbook sheets** (searched Step 22) | Store, never act on. Never drop `D` rows (99.9% rateable). Cosmetic |
| ~~E5~~ | ~~Untraced multipliers~~ | ✅ closed | **All three are rule-computed.** `SetModToUse` · `SetExpenseVariationFactor` · `SetPremiumDiscountCharge` — each defaults to **1.0** | Implement the three rules. Not an external dependency |
| ~~E6~~ | ~~Off-table interpolation~~ | ✅ closed | `DomainEachOccurrenceLimit` = **13 rows**; the limit input is a **closed enumerated domain** matching the ILF table's 26 keys. An off-table limit cannot be entered. ERC interpolates only Size-Of-Risk, where input is continuous — **now measured rather than asserted: 16 of 4,551 rate table definitions across all 61 packages declare an `InterpolateMode`, and all 16 are `PremOpsSizeOfRiskRelativity` / `ProdsCompldOpsSizeOfRiskRelativity`** | No interpolation needed **for limits**. Validate the limit against the domain. **Size-Of-Risk does need it, and it is live**: 8,148 of 8,330 Prem/Ops rows have unequal band endpoints (gate size-of-risk §3) |
| **E7** | `0`-as-sentinel | ⚙ **build work, not a question** | Zeros in **31 of 79** tables, usually legitimate. `UnmannedAircraftUsageBIPDRatingModifiers` has `0` for firefighting/crop-spraying/internet; `ErcSetRatesAndFactors` reads it **unguarded** | **N13.** Sentinel register + hard stop. Not escalated to ISO |
| ~~E8~~ | ~~Address → county/place~~ | ✅ **decided** | ERC carries the place tables for CA/FL/NY/TX; only address→place resolution was external | **Decision: county is a required submission field** in those four jurisdictions. No geocoding dependency. Absent or unmatched county → `REFER`, never a fuzzy match |
| ~~E9~~ | ~~Company LCM~~ | ✅ closed, **reaffirmed with a reason 2026-08-12** | `LCM.RateTable.csv` / `LCMCompany.RateTable.csv` exist at 0 rows — **and so do `PremOpsLCMCompany` and `ProdsCompldOpsLCMCompany`, in all 61 packages**; golden case `LCM = 1.0` | **Decision: hold at 1.0** — now for a stated reason. **This is a single-carrier build and `1.0` is chosen to match RAaS**, keeping every diff against the oracle clean; RAaS is already the project's answer for E1's rounding tie-break and the source of the `Payloads/` baseline set. A named, required, overridable parameter, **asserted at configuration time**. E15 closed onto this |
| **E11** | `AdditionalInterestFactor` — is **334's** omission intended? | 🟡 **narrowed** | **336 consumes it**: `MinPremium = round(MinimumPremium × FinalILF × AdditionalInterestFactor, 0)`. So the field is live; 334's chain genuinely does not read it | Implemented exactly where ERC reads it and nowhere else |
| ~~E12~~ | ~~`SetMedicalPaymentsCharge` tests `../PremOpsELP` as both string and decimal~~ | ✅ **closed by gate 336** — *(register was stale here until 2026-08-11; the closure is in `gates/GATE-336` §7 and `RECONCILIATION.md`)* | **Never a type inconsistency: two different DataDefs at two levels.** `GeneralLiabilityClassification/PremOpsELP` is the **string** rating-basis selector; the coverage group's `ELP` is the **decimal** rate. **Gate 332 reproduces the structure exactly** — `LiquorELP` is a string at classification level and a decimal rate table at coverage level, same name, same two levels. Eighth escalation to dissolve on reading | Both read as written, each at its own level |
| **E14** | Lookups that survive with **no caller** | 🟡 **reframed by gate 332 — it is a corpus habit, not a one-off** | Three instances across three sublines: `LookupPrincipalsProtvLiabFactor` (OCP, CW 2027, after `SetPrincipalsProtvLiabFactor` was deleted), and **`LookupNoDedStatCode`** and **`LookupPremOpsLCM`** (both liquor, every edition — `LookupPremOpsLCM` sits in the liquor file while `SetLCM` calls `LookupLiquorLCM`). The original question — *"vestigial, or a deletion defect?"* — is answered by the frequency: ERC routinely ships uncalled lookups | **Cheaper explanation found by gate 335-RR: `LookupPremOpsLCM` is the *same* dead lookup in the liquor and railroad files, copy-pasted — not independent instances.** **Treat an uncalled lookup as inert boilerplate.** Not implemented; zero premium effect. Assert at load time that every `Lookup*` rule either has a caller or is recorded here — a *new* uncalled lookup in a rating path is worth a warning even though these three are not |
| ~~**E15**~~ *(gate 332; generalised by gate 335-RR)* | ~~**An `LCM` of `1` is a placeholder for a company input, not a rate**~~ | ✅ **CLOSED 2026-08-12 by decision** | Re-measured before deciding, and it is broader than first filed: **10 LCM tables in the corpus — 6 carry exactly `1` in every countrywide edition, and the 4 `*LCMCompany` tables are empty in all 61 packages. 0 of 51 jurisdictions override any of them, and 11 rating paths consume one.** The empty company tables are the strongest evidence available: **ISO ships a placeholder of `1` and leaves the carrier's slot named and unfilled.** Manual `GL-MU-2027-RU-001-C` p.95 Rule 45.E: *"For rates, refer to company."* | **Decision: disposition A — a required carrier parameter, and E9's "hold at 1.0" stands with a reason and an assertion.** This is a **single-carrier build and the LCM is configured to `1.0` to match RAaS**, so engine output is directly comparable with the oracle — an *oracle-alignment* decision, not an actuarial one (§11). **The referral moves from rate time to configuration time**: refuse to rate if the parameter was never supplied, and never refer merely because it resolved to `1`, which is a legitimate filing. Register entry `R18`, reclassified NONE → DECLARED |
| **E16** *(gate 332; generalised by gate 335-RR)* | **The minimum premium of an ELP-rated subline is structurally zero** | 🟡 low, **two sublines** — `MinPremiumRR` is a single countrywide row of `0`, no state override, and CW 2027 deletes the rules and empties the table, exactly as liquor does | `ProdsCompldOpsMinPremium` publishes `A/B/C = 0, 0, 0` countrywide, no state overrides, and `SetMinimumPremium` hardcodes ILTA `"C"` — so `MinPremium = 0 × FinalILF = 0` for every liquor risk. CW 2027 **deletes both rules and empties the table**, which is consistent with the value never having been published. The manual's Rule 45.I.9 policywriting minimum (p.102) is a **policy-level** object and is not in ERC's liquor chain | Apply `0` as ERC writes it. **Do not** substitute the manual's policywriting minimum — that would be tier-2 sourcing. Revisit at build-order item 14, policy assembly |
| **E18** *(new, gate 365)* | **A rating rule reads a sibling coverage group's computed values** | 🔴 open, **architectural** | `SetAdjustedBaseRate` in the Loss Of Electronic Data and Cyber groups reads five DataDefs under `../GeneralLiabilityClassificationPremOpsCoverage/` — `PremOpsLossCost`, `PremOpsELP`, `LCM`, `ClaimsMadeMultiplier`, `PremOpsSizeOfRiskFinalRelativity`. Coverage groups are therefore **not independently evaluable**, and a host's edition-scoped behaviour propagates to its dependants without their expressing it. Not a question for ISO — a constraint Phase 4's kernel must satisfy and §5 did not state | **The kernel exposes resolved sibling state, and evaluation order across coverage groups is part of the algorithm.** Escalated because it changes the architecture, not the arithmetic |
| **E17** *(new, gate 332)* | **The refer sentinel's spelling is edition-scoped** | 🔴 open, **architectural** | `SetPremium` tests `"Refer To Co."` in all nine pre-2027 countrywide editions and `"Refer to Company"` in CW 2027. On `2027-04-01` **both strings are live in the corpus simultaneously** — old in the 8 unmigrated jurisdictions, new in the 43 migrated. ERC is internally consistent because rule and domain table resolve from the same package; **an engine with one global constant is wrong for 8 or 43 jurisdictions.** ISO's own CW 2027 demonstrates the failure (OI-43) | **No global sentinel constants.** Every literal an engine compares against is resolved from the same package as the rule that tests it. Now **N18** |
| ~~E10~~ | ~~Experience mod~~ | ✅ closed | ERC computes it: `SetActualExperienceRatio` → `SetExperienceCredibilityFactor` → `SetExperienceModification` → `SetExperienceRatingModificationRatesandFactors`, plus `ERPExperienceModificationOverride` | Implement the chain. Loss history is an **input**, like exposure |

| **E19** *(new, gate size-of-risk)* | **188 of 1,188 class codes carry a `0` size-of-risk loss cost, identically in every state** | 🔴 open | **45,812 of 167,442** size-of-risk loss cost cells across the 35 shipping jurisdictions are `0`; deduplicated, that is **188 of 1,188 class codes, and the same 188 in all 35** — a countrywide statement expressed 35 times. The 188 **do** have relativity table assignments and min/max relativities, so the zero is in the loss cost alone and the premium is `0` rather than a referral. **Nothing can arbitrate it:** the manual is silent (**0 of 843** searchable documents mention size-of-risk), and **0 of 388** `DoMessage*` rules corpus-wide reference it | Class-not-eligible, genuinely-zero, or placeholder — three readings, no discriminator. **Until answered, a `0` size-of-risk loss cost is a `REFER`**, which is the safe direction |

**Four inputs have resolved as submission requirements rather than gaps**, and the pattern is worth
naming: (1) **county or place** for CA, FL, NY and TX (OI-34/E8); (2) **`WorkersCompensationRate`** for
OCP class `15191`, a declared ERC field that real STC submissions supply; (3) **one resolved rating
category per axis for Unmanned Aircraft** — Ownership & Operation, Usage, Primary Place of Operation
— decided 2026-08-11 (OI-48); (4) **`SizeOfRiskRatingApplies`**, a policy-level flag with no writer
rule and no domain table — **its filed domain `{Yes, No}` turns up as a key column of
`RatingIdentificationCode`**, a rate table, which is the only place in the corpus that states it
(gate size-of-risk §6). In each case the engine refuses to infer, and in each case **ERC already
provides the way to say "unresolved"**: `REFER` on an unmatched place, the filed `Unknown` /
`Not Applicable` domain values on the drone axes, and — for size-of-risk — an absent flag that
must refer rather than default to `No`.

**Eight of the eighteen raised have dissolved on being read**, not on being answered — see the
standing criterion in `PROCESS_LOG.md`. Each had been recorded as an open question on the strength
of a name or a missing table, without the underlying artifact being opened. Seven went that way in
Step 22; the eighth (E12) was raised by the 334 gate and closed by the 336 gate one step later,
**by the same failure — a question asked of a name instead of the sibling table.**

**Genuinely remaining: E1** (rounding tie-break, settled by RAaS) and **E4** (`Status`, cosmetic —
store it, never act on it). **E15 closed 2026-08-12** onto E9, by the decision to build for a single
carrier at `LCM = 1.0` for RAaS comparability. E7 became build work (N13); E8 became a submission requirement; the
rest were answered by the files.

**E20 is the first escalation raised by the ENGINE rather than by analysis.** Filed 2026-08-12 by
stage 1's ILF monotonicity assertion, which was looking for something else. **`1.00` is being used as
a factor sentinel** in `GL_TX_20250801_V01/ILFElevatorContractor` — exactly `1.00` at **26 of 30**
rows against a genuine 1.69–1.72 at four, so a `20,000,000` aggregate prices identically to a
`50,000` one. **It is the more dangerous sentinel than zero**, because a nil premium gets questioned
and a plausible one does not. **1 of 19,236 ILF series** corpus-wide at 2026-08-11 — and **all seven Texas editions carry it**,
from 2021-06-01 to the 2027 filing, which halves the table and keeps all four genuine factors.
**Six years of consecutive filings is not a typo**, so *"no load applies at this combination"* is the
stronger reading and *"placeholder"* the weaker one — **but the disposition does not change**, because
the series is still non-monotonic, ERC still has no discriminator, and a wrong guess in the
permissive direction is invisible. Registered by name in `gl_engine/assertions.py` so it passes by
decision, not by silence; anything new fails the load. Full detail: **OI-68**.

**That E20 exists at all is the argument for the two diaries.** Three weeks of analysis catalogued
eight meanings of `0` and never asked what `1` might mean, because nothing multiplies during
analysis. **The engine finds a different class of defect than the reading does** — which is the
premise of the recursive harness, arriving one stage earlier than planned.

**E19 is the first escalation the manual cannot even be asked about.** Every earlier one was
*"ERC says X, the manual says Y or is silent on this rule"*; E19 is *"the manual has no text on this
subject at all"* — measured, 0 of 843 searchable documents — so it cannot be closed by reading
harder, only by an ISO answer or by OCR of the remaining 187 (OI-51).

**E11 and E12 were raised by the 334 gate and both were resolved by the 336 gate one step later.**
E12 closed outright — it was two DataDefs at two levels, not a type inconsistency, and I had raised
it from a name without opening the sibling table: **the exact failure the standing criterion warns
against, committed one document after restating it.** E11 narrowed to a much smaller question once
336 was found to consume the factor. Neither gates the build.

**What still warrants an ISO request:** the rounding tie-break (E1), the `Status` A/C/D definition
(E4), and whether 334's omission of `AdditionalInterestFactor` is intended (E11). `ErcCore` and the engine
specification remain worth having for completeness, but neither gates the build.

---

## 8. Build order

One subline at a time, each gated by §8.

> **Resequenced 2026-08-11, at the user's direction: Size-Of-Risk becomes item 8 and everything
> below moves down one. Thirteen items become fourteen.**
>
> **This closes [OI-46](OPEN-ITEMS.md).** Item 6's Loss Of Electronic Data and Cyber coverages read
> `PremOpsSizeOfRiskFinalRelativity` — Size-Of-Risk output — out of their host coverage group
> (E18, [gate 365](gates/GATE-365-WITHDRAWAL-LOED-CYBER.md) §2), so the build order had a data
> dependency running four items backwards. Pulling Size-Of-Risk out of the rating-plans bundle and
> placing it at 8 puts it **first in the build queue**, ahead of everything not yet gated and ahead
> of any implementation of item 6. Items 1–7 are already gated, so nothing moves that has landed.
>
> **Crosswalk for earlier documents**, which keep the numbering they were filed under:
> old 8 → 9 · old 9 (Terrorism) → 10 · old 10 (Rating plans) → 11, now *without* Size-Of-Risk ·
> old 11 (State-specific) → 12 · old 12 (Capture harness) → **13** · old 13 (Policy assembly) → **14**.
>
> **Resequenced again 2026-08-12, at the user's direction: Refer-to-company moves from 9 to after
> State-specific rating coverages.** Items 9–12 are now **9 Terrorism · 10 Rating plans ·
> 11 State-specific · 12 Refer-to-company**; 13 and 14 are unchanged. The reasoning is the one the
> gates keep producing: every item ahead of 12 generates referral conditions of its own — size-of-risk's
> zero relativity and its 16 loss-cost-less jurisdictions, terrorism's version-specific referrals,
> OI-49's railroad case — so the referral workflow is built against a **measured** population rather
> than a guessed one. **Second crosswalk:** old 9 (Refer-to-company) → **12** · old 10 (Terrorism) →
> **9** · old 11 (Rating plans) → **10** · old 12 (State-specific) → **11**.

| # | Subline / coverage | Code | Note |
|---|---|---|---|
| 1 | Premises/Operations | 334 | Primary path — classification, exposure, ILF, territory, deductible. **✅ Gate passed** — [`gates/GATE-334-PREMISES-OPERATIONS.md`](gates/GATE-334-PREMISES-OPERATIONS.md) |
| 2 | Products/Completed Operations | 336 | Shares exposure base; statewide territory `999`. **✅ Gate passed** — [`gates/GATE-336-PRODUCTS-COMPLETED-OPERATIONS.md`](gates/GATE-336-PRODUCTS-COMPLETED-OPERATIONS.md) |
| 3 | OCP / Principals Protective | 335 | **✅ Gate passed** — [`gates/GATE-335-OWNERS-CONTRACTORS-PROTECTIVE.md`](gates/GATE-335-OWNERS-CONTRACTORS-PROTECTIVE.md). **As of today all 51 publish loss costs; on `2027-04-01` forty-three withdraw them at once.** Both paths needed **by effective date**, not by jurisdiction. **No oracle exists** |
| 4 | Liquor Liability | 332 | **✅ Gate passed** — [`gates/GATE-332-LIQUOR-LIABILITY.md`](gates/GATE-332-LIQUOR-LIABILITY.md). **The Step 31 prediction held**: no `Liquor*LossCost` table exists in any jurisdiction at any edition, `SetBaseRate` has **no loss-cost branch**, and the manual settles it in one line — Rule 45.E, p.95: *"For rates, refer to company."* N17 exact at **362/362**. **No oracle** (the golden case carries liquor switched off). Three escalations: the `LCM = 1` placeholder (**E15**), a structurally zero minimum premium (**E16**), and an **edition-scoped refer sentinel** (**E17**) |
| 5 | Railroad Protective | 335 | **✅ Gate passed** — [`gates/GATE-335-RAILROAD-PROTECTIVE.md`](gates/GATE-335-RAILROAD-PROTECTIVE.md). Confirmed exactly: no base rate (Rule 49.E.1 *"Refer to company"*), banded on trains/day at **$100,000/300,000** basic limits. **Same subline code as OCP** — Rule 46 and Rule 49 share code 335, which is why railroad reads OCP's loss-cost table (class `16292` hardcoded) and why **OCP's 2027 withdrawal forced railroad's rewrite**. **18 rate cells confirmed to the cent** against the ELP Supplement. **Smallest deviation surface of any subline: 2 jurisdictions, 3 rules.** CW 2027 deletes **22 of 65** rules. **No oracle** |
| 6 | Product Withdrawal · LoED · Cyber | 365 / — | **✅ Gate passed** — [`gates/GATE-365-WITHDRAWAL-LOED-CYBER.md`](gates/GATE-365-WITHDRAWAL-LOED-CYBER.md). **Factor-on-host is a kernel requirement, not a scheduling note (E18): `SetAdjustedBaseRate` reads five of its host's *computed* values** under `../GeneralLiabilityClassificationPremOpsCoverage/`. **Item 6 depends on Size-Of-Risk, which is now item 8** — LoED and Cyber read `PremOpsSizeOfRiskFinalRelativity` (OI-46, closed by the resequencing). Product Withdrawal is the only one with its own subline (365) and borrows Prod/CompOps's selector, tables and deductible. **No oracle.** **The largest single rating item: 150 countrywide rules across six coverage groups** (half again as many as 334), but a *small* deviation surface — **17 state rule names in 9 jurisdictions**. *(Corrected from a mis-measured 320/178/42, which matched group-name substrings and swept in 19 endorsement and coverage-form groups belonging to items 9, 13 and 14 — [`PHASE-SIZING.md`](PHASE-SIZING.md) §5.)* **Still three separate derivations**, because the six groups share a rule-name skeleton and **zero identical rule bodies** |
| 7 | Unmanned Aircraft | 370 | **✅ Gate passed** — [`gates/GATE-370-UNMANNED-AIRCRAFT.md`](gates/GATE-370-UNMANNED-AIRCRAFT.md). **Settles N13's oldest sentinel: 24/24 cells against manual Table 37.E, `0` = `RTC` exactly, and no in-corpus discriminator — verified exhaustively.** **Not "flat charges" — it is a rate-driven subline**, and the scope measurement said otherwise until 2026-08-11. Two `RATE_DRIVEN` groups, 116 packages each: `…UnmannedAircraftCovABIPDCoverage` computes `Premium = AdjustedRate × (ILF − DeductibleFactor) × PackageModFactor × ExperienceMod × …`, and `…CovBPAICoverage` the same without the deductible. Both were filed as *aggregators* because the classifier's rate-source list omitted `AdjustedRate` (§3). `0` above 55 lb is a **confirmed refer sentinel** — N13's oldest, and it sits on this path |
| **8** | **Size-Of-Risk** *(was part of item 10)* | — | **✅ Gate passed** — [`gates/GATE-SIZE-OF-RISK.md`](gates/GATE-SIZE-OF-RISK.md). **The first gate with no manual anchor: 0 of 1,030 manual documents mention size-of-risk, and 187 of them cannot be searched at all** (§0, OI-51) — so ERC is the sole authority and every sentinel here lands in `escalate/`, not `confirm/`. **It is a rating *mode*, not a factor: `SetPremOpsLossCost` swaps the loss cost TABLE when the flag is `Yes`**, and the relativity is a second, independent change to the same chain. **Brings a new engine capability — linear interpolation across an exposure band, used by 16 of 4,551 rate table definitions corpus-wide and by nothing else.** Loss costs are the jurisdiction's: **0 of 3** declared parents carry a row, **35 of 51** jurisdictions ship them, and in the other **16** a `Yes` flag has no loss cost at all. **The Step 38 trap confirmed and sharpened: NJ and OH shard by territory, but they override the *setter*, not the lookup — 0 of 35 override a size-of-risk lookup rule**, so binding by table or lookup name is wrong in both. Unblocks item 6 (E18) |
| **9** | **Terrorism** *(was 10)* | — | **✅ Gate passed** — [`gates/GATE-TERRORISM.md`](gates/GATE-TERRORISM.md). **OI-37 closed**: the population is **20 groups of 477**, and the `OTHER` bucket is not a miscellany — four of them compute `Premium` from **other groups' finished Premiums**, a rate source `RATE_SRC` does not list. **So terrorism CAN be computed and R3's prohibition is lifted.** Manual differential exact: **4 of 4** factor cells (`.009`/`.004`, `0.58`), and the above-average class list **142 vs 142** once compared as a union — countrywide ERC carries 141 because it does not rate `91600`, and **New York, which does rate it, supplies the 142nd**. **E18 widens from coverage scope to policy scope**: terrorism reads four groups' `Premium` and one group's `FinalILF` across three sublines and unmanned aircraft, so it runs **last**. **8 `TEV` + 16 `PEV` manual versions over 52 jurisdictions; all 16 PEV class lists are identical**, so the classes are countrywide and only the rules deviate |
| **10** | **Rating plans** — Schedule · Experience · Composite *(was 11)* | — | **✅ Gate passed** — [`gates/GATE-RATING-PLANS.md`](gates/GATE-RATING-PLANS.md). **OI-01, OI-02, OI-03 and OI-55 all closed.** **The first gate where the manual is the richer source**: the three plans were recorded as *"`[PDF]` absent"* and were on disk the whole time — **52 `CGLES` + 90 `CRP` documents, 654 pages**, now ingested. **Composite Rating moved to the *Interline* manual in 2017**, so 51 of its 90 documents start `IL-` and a `GL-*` sweep finds 39. **Schedule: 8 of 8 characteristics agree with manual Rule 9 Table 9 on range AND row count (2n+1 for ±n%), plus the filed ±25% cap. Experience: Rule 16's three columns are three ERC tables — 97 of 97 bands, 291 cells, 0 mismatches**, and the formula `((AER − EER) ÷ EER) × Credibility` matches Rule 5.G. **Composite: 3 rules, executable**, the manual confirming the inception-rate / audited-exposure shape in one sentence. **19 rules, 8 of 51 jurisdictions deviating — 7 of them on schedule rating only, 0 on composite.** **Item 10 adds no rate lookup of its own**; all three plans operate on premium other items produce |
| **11** | **State-specific rating coverages** *(was 12)* | — | **✅ Gate passed** — [`gates/GATE-STATE-SPECIFIC.md`](gates/GATE-STATE-SPECIFIC.md). **Scope corrected: five coverages in four states, 88 rules — not four in three.** Re-derived the population (582 countrywide groups against 618 jurisdiction groups → **449 state-only**, of which 371 do not write a premium, 58 capture, 16 are `OTHER` and 4 are `RATE_DRIVEN`). **Rhode Island's lead coverage is the fifth and rates** — a 13-rule chain with a 16,410-character `SetPremium` — filed `OTHER` because its premium reads `LeadLiabilityRate`, **the fourth term missing from `RATE_SRC`** (OI-63). **New Jersey confirmed capture-only**, as recorded. **Three different lead algorithms**: MD a flat `15` per unit, MA a `0.01` rate, RI four hazard-level factors spanning `0.01`–`0.10` on four unit-count inputs. **And NY Special Protective and Highway — the largest at 35 rules — prices at `0` by design**: loss cost `0`, ELP `0`, and the N17 selector reads `Company` on all three classes. **Railroad's shape exactly; it belongs in item 12's population** (OI-64) |
| **12** | **Refer-to-company coverages** *(was 9)* | — | **🔄 In progress — steps 1 and 2 of 6 done.** Moved here 2026-08-12 at the user's direction, and the move paid: every item ahead of it added referral conditions, so the population is measured rather than guessed. **Scoped broadly**: not the two coverages that are referrals, but the **register `escalate/` consumes** (§5 promises *"an escalation is a typed object that forces a REFER until answered"* and nothing had assembled the list). **Step 1** — [`40_referral_census.py`](../scripts/erc/40_referral_census.py) finds referral conditions by scanning, six probes over 61 packages, **and amended four filed gates on its first run** (OI-65), one of them filed the same morning. **Step 2** — [`41_referral_register.py`](../scripts/erc/41_referral_register.py) (4/4) classifies and emits `out/referral_register.json`: **28 entries · 9 DECLARED (load-time) · 4 MISSING · 4 GUARD · 11 NONE**. **Silent-zero failures outnumber loud nulls 7 to 3.** **Steps 3–6 are blocked on 13 decisions** — the eleven NONE entries (`R18`–`R28`), whether terrorism refers when a classification feeding it refers, and whether OI-58 blocks the propagation rule. **Item 12 cannot be "done" before the engine exists**; what it can deliver is the register and the rules, and that is how its gate will be written |
| 13 | **Capture harness** *(unchanged)* | — | The **383** capture groups: required-input validation, `ManualPremium × PackageModFactor`, referral when the premium is absent |
| 14 | Policy assembly *(unchanged)* | — | Aggregation (**76** aggregator groups — two moved to item 7, §3), minimum premium, statistical coding |

---

## 9. The per-subline gate

**Format validated on sublines 334 and 336.** Gate 2 was written *differentially* — shared
machinery cited to gate 334 rather than re-derived — which cost a fraction of the effort and still
surfaced four things 334 could not show. That is the pattern for the remaining nine.

**Nine habits carry forward.** The first seven are about *reading*. The eighth is about
*counting*, and it exists because seven gates in one day produced five wrong figures — **every one
of them an aggregate or a negative, and not one of them a misread rule body**:

> *"Delaware has no territory table"* · *"no `RailroadELPText` exists"* · *"16 coverage groups
> rate"* · *"item 6 is 320 countrywide rules"* · *"the drone sentinel is 8 cells"*

The cause is not carelessness and **not "reading the name instead of the file"** — habits 1 and 6
already say to read the file, and were followed. It is narrower and it has a name:

> ### **A search predicate was allowed to define a population, and then a conclusion was drawn about that population.**

A filename, a regex alternation, a substring, one table out of a family. **The denominator came
from the query rather than from the corpus**, so anything the query could not see was reported as
absent. Positive findings never failed this way, because reading the rule body *is* the evidence.
Only aggregates and negatives did.

Two rules follow, and only the second is enforceable by a machine:

| | Rule |
|---|---|
| **Writing** | **Every count is "n of N", with N derived from the corpus and named.** A bare count hides its denominator and cannot be checked by a reader. *"8 cells"* passes review; *"8 of ?"* does not, and finding the `?` is exactly what surfaces the neighbours |
| **Measuring** | **Enumerate the population, then classify every member.** Never let the predicate pick the members. A negative claim must state what was enumerated and how — *a search that finds nothing is not evidence of absence* |

`scripts/erc/34_crosscheck.py` enforces the second and joins the verification routine. **It found
two real defects on its first run** (§8 item 6's missing coverage, and that two "orphan tables" were
unremarkable members of a class of 79), and then **caught its own fix committing the same
substring error** — `GeneralLiabilityClassification` matched six other group names. That is the
argument for a machine check over a habit: the habit was written in the same hour it was broken.

The seven reading habits:

- **Resolve the golden case's declared countrywide parent before reading any countrywide rule.**
  Reading the newest package instead of the named one nearly hid the edition split in §6.
- **Read the `DoMessage*` rules alongside the rating rules** — they hold guards the chain does not (N15).
- **Count table rows before trusting a lookup** — three of 334's countrywide tables are header-only
  (N7). **And when the count is zero, check the table's neighbours before concluding the data is
  absent:** CA, NJ, NY and OH leave `PremOpsLossCost` empty and file 66,573 rows under
  `PremOpsLossCost<ST>Terr<nnn>` (OI-20).
- **Test every `0` against its consuming branch.** Four meanings found so far — a genuine factor, an
  unpublished factor, a degraded referral, and a path switch. Indistinguishable in the data; two now
  have an in-corpus discriminator (N13, N17).
- **When two sublines share a mechanism, diff them rather than deriving twice.** The
  `TableAssignment` typing trap (334 numeric with an `…Int` conversion, 336 alphabetic with none) and
  336's absent `MedicalPaymentsCharge` are invisible from inside either subline alone.
- **Search to locate a page; read the page to make the claim.** A truncated keyword excerpt produced
  a confident, wrong disagreement in gate 336 §2. In this corpus a partial read is
  indistinguishable from an answer.
- **When a document states a jurisdiction split, test whether it is really an edition split.**
  335's *"15 published / 36 withdrawn"* reads as geography and is a calendar: **8 / 43**, and the 43
  are exactly the jurisdictions on `2027-04-01`. README finding #4's 15/36 class-basis split had the
  same shape and was measured the same way. **Both re-tested and closed under OI-40**
  ([`gates/OI-40-ASOF-RECOUNT.md`](gates/OI-40-ASOF-RECOUNT.md)): territory and the rate-driven
  group set survived the re-test; N7's table counts and the 238/204/959 class split did not.

**Habit 9, added 2026-08-19 — read the directory before you escalate to a person.**
`OI-95` sat as `OPEN — needs a person` for two days: ISO's manual and ISO's data file disagreed on
178 Texas classes, both sources otherwise agreed everywhere else, and nothing in either corpus said
which of us was supposed to arbitrate that — so it was written up as a genuine judgement call.

**It was not one.** `PremOpsELPText.RateTable.csv` — sitting in the exact same `Rate Tables`
directory as `PremOpsELP.RateTable.csv`, a file already read repeatedly for other items on this
register — declares the discriminator directly: `Rate/Loss Cost Applies` / `Industry` / `Company`,
one value per class per state. Cross-tabulated against the rate file, it resolves the 178 with **zero
exceptions**. The escalation only lifted when a person named where to look; nothing about finding it
required a person, and the file had been sitting there the whole time.

**The instruction this produced, given directly:** *"you are not examining the files enough to have a
full understanding of how the product works."* That is sharper than habit 1's *"read the file, not
the name"* — habit 1 is about not trusting a table's name for what it contains. This is about not
trusting **the set of files already cited** as the set worth reading. A gate, an escalation, or a
`NEEDS A PERSON` label is a claim that the corpus was checked and came up empty. **Before writing that
claim, list the directory the relevant table lives in and read what sits beside it** — not only the
files a previous session already flagged.

Presented to you before a subline is considered done:

1. **The algorithm** — ordered steps, each citing the **ERC file** that sources it.
2. **Confirmations** — every point where the manual was consulted, what it confirmed, and the
   citation. Where the manual disagreed with ERC, that is called out explicitly.
3. **Escalations** — anything neither source settled, and what the engine does meanwhile.
4. **Inputs consumed**, and behaviour when one is absent.
5. **Lookups and their layer** — countrywide, state, or overridden.
6. **State deviations** — enumerated and quantified, per jurisdiction. Not "some states differ."
7. **Refer-to-company triggers** — every path yielding a referral.
8. **Test result** — golden case where applicable, plus both agents' findings.

---

## 10. Ingestion

Discover packages → identity from `targetNamespace` → load Defs, then CSVs typed per Def →
classify table shape → **record row counts and mark empty tables**.

**CORRECTED 2026-08-12, by stage 1.** This said *"the five table shapes"*. Measured, there are
**four read shapes** — `exact` 3,418 · `undeclared` 485 · `banded` 32 · `interpolated` 6 — and
**three population states** — `populated` 2,894 · `empty` 1,046 · `split-family` 1 (deduplicated
over the 54 packages resolved at 2026-08-11). **Shape and population are orthogonal axes**, which is
N7 restated: *presence is not population is not purpose*. "Five" conflated the two. Note
`interpolated`: 6 tables carry `InterpolateMode="Linear"` on the **value** side, so size-of-risk
relativity interpolates between published relativities rather than stepping — read as a step
function it is wrong by up to the width of a band.

**Coverage groups are not independent.** `SetAdjustedBaseRate` in the Loss Of Electronic Data and Cyber groups reads five **computed** values out of its host group — `PremOpsLossCost`, `PremOpsELP`, `LCM`, `ClaimsMadeMultiplier`, `PremOpsSizeOfRiskFinalRelativity` — so the kernel must expose resolved sibling state and **evaluation order across groups is part of the algorithm** (E18, gate 365 §2). A host's edition-scoped behaviour propagates to its dependants without their expressing it.

**Load-time assertions** (fail, never warn): identity resolves for all 567; the countrywide
parent exists; no empty table in a rating path **unless a suffixed table family supplies its rows**
(CA, NJ, NY, OH — OI-20); cell values fall within ERC's own alphabet; ILF factors monotonic in both
axes; declared row counts reconcile; every value carries an `erc_source`; **every *populated* rate table has at least one reader** — 237 of 798 countrywide table instances have no reader and **all are empty stubs**, so the assertion is about populated tables only; **both spellings of `ProductWithdraw(a)l` resolve to distinct artifacts** and are never normalised together (OI-47); **the as-of date is ≥
2022-09-01**, below which the corpus cannot resolve all 51 jurisdictions (OI-41).

**Several countrywide editions are live at once.** Three declared parents are in force today
(`GL_CW_20231201_V02`, `…V03`, `GL_CW_20260101_V01`) and three at the cliff. There is no date at
which one suffices, and for five states today the declared parent is **not** the newest — N5 and
habit 1 are the only things that catch them (OI-40 §3).

The `confirm/` register is small, hand-maintained, and each entry cites a manual page and names
the **ERC artifact it confirms**. An entry that confirms nothing in ERC is rejected — that is the
tier-2 boundary, enforced.

---

## 11. Testing

| Layer | Proves |
|---|---|
| **Unit** | Each step, `Decimal` exactness, disposition handling |
| **Golden — OK case** | The full chain against a real ISO-rated policy. **Runnable today**: `tests/verify_golden.py`, **80/80**, three layers — fixture vs ISO's output, fixture vs the ERC CSVs, arithmetic re-derived in `Decimal`. Covers 334 + 336 + the policy total |
| **Property** | ILF monotonic; premium monotonic in exposure; no `REFER` ever becomes a number |
| **Differential** | Same risk, all 51 jurisdictions — every difference must name the deviation responsible |
| **Manual confirmation** | Structural claims corroborated against the PDFs; disagreements escalate |
| **Recursive harness** | Both agents audit every trace; findings feed back as fixes |
| **RAaS** *(later)* | The external oracle. Seam built now against `NullOracle` |

516 further STC inputs exist without expected outputs — usable as realistic risk shapes even
without answers.

### This is a single-carrier build, configured for RAaS comparability

**Decided 2026-08-12.** The engine is built for **one carrier**, and its company parameters are
chosen so that **its output can be diffed directly against RAaS**. The first and most load-bearing
of them:

| Parameter | Value | Why |
|---|---|---|
| **`LCM`** — the loss cost multiplier, all sublines | **`1.0`** | ISO ships `1` as a placeholder and leaves the four `*LCMCompany` tables empty in all 61 packages. Holding at `1.0` makes the engine's base rate the ISO expected-loss figure, which is what RAaS returns — so a difference against the oracle is **a rating defect and never a company deviation** |

**That is an oracle-alignment decision, not an actuarial one, and the distinction matters when the
build later serves a carrier with a real LCM.** It is also consistent with how RAaS is already used
in this plan: as the answer for **E1**'s rounding tie-break, and as the source of the `Payloads/`
baseline set.

**The obligation it creates:** every company parameter must be **named, required and asserted at
configuration time** — never defaulted silently. An engine that quotes without being told its LCM is
returning ISO's expected losses and calling them a premium. Escalation **E15** closed onto this;
register entry **`R18`**.

---

## 12. Phasing

**Sized 2026-08-11 from the packages in force** — [`PHASE-SIZING.md`](PHASE-SIZING.md),
`scripts/erc/33_phase_sizing.py`. OI-40 gated this and is closed. Three sizing findings change the
table below: **three countrywide calculators rather than two**, **item 6 is the largest single rating
item** (150 CW rules, corrected from a mis-measured 320), and **item 12 has a fourth coverage in a
third state**.

**Resequenced 2026-08-11**: Size-Of-Risk is pulled out of the rating-plans bundle to build-order
item 8 and built at phase 6, ahead of everything not yet gated — it is a hard input to item 6's
Loss Of Electronic Data and Cyber coverages (§8, OI-46). **Phase count drops from 18 to 17** because
the phase list collapses the seven passed subline gates into `5`–`5f`.

| Phase | Work | Exit |
|---|---|---|
| **0** | Skeleton, domain types, `Decimal`, provenance-tagged trace | A value cannot be constructed without an `erc_source` |
| **1** | ERC ingestion, identity, assertions | 567/567 load; all assertions green. *(Rating-count verification complete — **18/383/76**, re-tested as-of; the same set at every date)*. **Plus the as-of floor: an effective date before 2022-09-01 fails loudly** — the corpus cannot resolve all 51 before then (OI-41) |
| **2** | Resolver: as-of selection, CW parent, both layers addressable | Parent dispatch proven non-recursive on all 4,598 call-super rules. **Three countrywide calculators addressable, named: `V02` · `V03`(=`20260101`, byte-identical for 334) · `20270401`.** Not "CW 2023 and CW 2027" — **California alone holds V02, and 40 of its 100 Prem/Ops rule bodies differ from V03 under identical rule names** ([`PHASE-SIZING.md`](PHASE-SIZING.md) §4) |
| **3** | Territory (all three schemes) · `confirm/` · `escalate/` | All 51 resolve — 27 ZIP, 20 constant, 4 by submitted county. **Re-verified as-of** (OI-40 §2): the mix is identical today, at the cliff and in the end state. Scheme is read from **five** possible table names — DE files its constant under `DomainPremOpsTerritory` |
| **4** | Kernel + **subline 1 (334)** | ✅ **Gate §9 passed; golden case reproduced (`Premium 976.00`)** — spec complete, code not yet written. **Three calculators required, not two** (§8 note, [`PHASE-SIZING.md`](PHASE-SIZING.md) §4). **The gate derived V03; nothing yet tests V02, which only California uses** — a CA differential case is needed before this phase closes |
| **5** | Recursive harness live | Both agents review 334 |
| **5a** | **Subline 2 (336)** | ✅ **Gate §9 passed; golden case reproduced (`Premium 6,845.00`)** — spec complete, code not yet written |
| **5b** | **Subline 3 (335)** | ✅ **Gate §9 passed** — derivation + 6 manual confirmations + 3 corpus-wide tests. **No oracle**; 8 OCP submissions exist without outputs, recorded as the seed fixture set |
| **5c** | **Subline 4 (332 Liquor)** | ✅ **Gate §9 passed** — prediction confirmed, 9 manual confirmations, N17 exact at 362/362. **No oracle.** First subline that is *company-rated* rather than loss-cost-rated |
| **5d** | **Subline 5 (335 Railroad Protective)** | ✅ **Gate §9 passed** — **18 rate cells exact** against the ELP Supplement, the project's first cell-by-cell rate confirmation. N17 narrowed on a counterexample. **No oracle.** Cheapest remaining rating subline: 2 deviating jurisdictions |
| **5e** | **Subline 6 (365 Product Withdrawal · LoED · Cyber)** | ✅ **Gate §9 passed** — 6 rate-driven groups, 150 CW rules, **zero shared rule bodies**. **E18: the kernel must expose resolved sibling state.** **No oracle** |
| **5f** | **Subline 7 (370 Unmanned Aircraft)** | ✅ **Gate §9 passed** — **N13's oldest sentinel decoded, 24/24 against manual Table 37.E**, and proved to have no in-corpus discriminator. E1 shown not to bite here. **No oracle** |
| **6** | **Size-Of-Risk** — build-order item 8 | **Moved ahead of the rest 2026-08-11.** `PremOpsSizeOfRiskRelativity` 8,330 rows + `ProdsCompldOpsSizeOfRiskRelativity` 4,214 load and resolve; the NJ sharded `…LossCostTerr501…517` tables resolve by rule, not by name (OI-20). **Exit unblocks item 6's LoED and Cyber implementation** (E18, OI-46) |
| **7** | **Terrorism** — build-order item 9 | ✅ **Gate §9 passed 2026-08-12.** OI-37's population audit ran and discharged `RECONCILIATION.md` R3. **E18 widens to policy scope**: terrorism consumes four groups' finished premiums, so it runs last. **15 of 51 jurisdictions file their own territory-keyed factors** (§3a) |
| **8** | **Rating plans** — Schedule · Experience · Composite — build-order item 10 | ✅ **Gate §9 passed 2026-08-12.** Manual and ERC agree 8 of 8 schedule characteristics and 97 of 97 experience bands. **Adds an 8dp rounding precision N10 did not list** (OI-62) |
| **9** | **State-specific coverages** — build-order item 11 | ✅ **Gate §9 passed 2026-08-12.** **Five coverages in four states, 88 rules** — MD, MA ×2, **RI** (which had been recorded as not rating) and **NY Special Protective & Highway, which prices at `0` by design** and belongs in item 12's population (OI-64) |
| **10** | **Refer-to-company** — build-order item 12 | 🔄 **In progress.** Steps 1–3 of 6 done: the referral census, the register (**28 entries**), and **all 13 decisions taken**. Steps 4–6 remain and are unblocked |
| **11** | Capture harness — 383 groups — build-order item 13 | **Not yet gated.** Validation + aggregation, no invented rates. **383 is a union over every edition ever filed, deliberately** — the harness must handle every group the engine may meet, not the 356 in force today (OI-40 §5) |
| **12** | Policy assembly — build-order item 14 | **Not yet gated.** Full-policy quotes |
| **17** | RAaS | *Out of scope now* |

---

## 13. The honest ceiling

**18 coverage groups rate. 383 capture. 76 aggregate.** And *rate* is not the same as *price*: **Liquor (332) is company-rated** — `GL-MU-2027-RU-001-C` p.95 Rule 45.E says *"For rates, refer to company"*, ERC ships an `LCM` of `1` and deductible factors of `0`, and the same paragraph governs Rules 42 and 43. **Railroad Protective is company-rated too** — Rule 49.E.1, p.126, the same sentence — and it carries the same `LCM = 1` placeholder. So some of the 18 produce a *complete, correctly-structured* premium that is still an ISO expected-loss figure awaiting a company multiplier (E15). ERC declares roughly 5,300
refer-to-company situations of its own. So this engine automates the core rating paths and produces a structured, cited referral for
the rest.

That is not a limitation of the build — it is what the source contains, and under this doctrine
we do not paper over it with assumptions. Anyone expecting end-to-end automation of every
coverage should know it now.
