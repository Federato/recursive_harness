# Gate — Product Withdrawal (365), Loss Of Electronic Data, Cyber Incident Liability

**Filed 2026-08-11. Build-order item 6. Sixth subline gate**, differential against
[334](GATE-334-PREMISES-OPERATIONS.md), [336](GATE-336-PRODUCTS-COMPLETED-OPERATIONS.md),
[335 OCP](GATE-335-OWNERS-CONTRACTORS-PROTECTIVE.md), [332](GATE-332-LIQUOR-LIABILITY.md) and
[335 Railroad](GATE-335-RAILROAD-PROTECTIVE.md).

**As-of date: 2026-08-11.** Required, not assumed (N4). Derived against **`GL_CW_20231201_V03`**,
the parent the OK golden case declares (habit 1).

> **One gate, three coverages, six rate-driven groups.** The build order lists item 6 as a single
> line. It is three unrelated coverages that share a rule-name skeleton and **no implementation** —
> across the six groups, pairwise name overlap runs 12–25 rules and **identical bodies run to
> exactly zero**. They are derived separately below and gated together because the *questions* are
> shared, not the code.

---

## 0. Item 6 was mis-sized, and this gate opens by withdrawing that figure

[`PHASE-SIZING.md`](../PHASE-SIZING.md) reported item 6 as **320 countrywide rules, 178 state rules,
42 jurisdictions** — *"more countrywide rules than 334, 336 and 335 combined"* — and recommended
splitting it into three build-order items on that basis.

**The measurement was wrong.** The sizing script matched DataDefGroups by **substring**, and
`ProductWithdrawal` also matches **19 endorsement, coverage-form and minimum-premium groups**
carrying 167 further rules — work belonging to items 8, 12 and 13, not to item 6's rating.

| | Reported | Actual rating core |
|---|---|---|
| Countrywide rules | 320 | **150** |
| State rule names | 178 | **17** |
| Jurisdictions | 42 | **9** |

Item 6 **is** the largest single rating item — 150 countrywide rules against 334's 100 — but its
deviation surface is **small**, not the widest. The sizing script now intersects every substring
match with the RATE_DRIVEN set; `SIZE_ALL=1` reproduces the old behaviour.

**Third instance this session of the same error** — after Delaware's territory table and the
`AdjustedRate` omission — and it is the one that had already changed a plan. *A name was matched
where a thing should have been identified.*

The split-into-three recommendation is **withdrawn as argued and re-made on other grounds**: not
size, but that the three coverages share no implementation.

---

## 1. Product Withdrawal (subline 365) — the only coverage here with its own subline

Two rate-driven groups, 27 rules each, differing only in which factor they apply:
`…ExclusionCoverageAProductWithdrawalExpense` and `…ExclusionCoverageBProductWithdrawalLiability`.

**The chain**, from `GeneralLiabilityClassificationExclusionCoverageAProductWithdrawalExpenseRules`:

| # | Rule | What it does |
|---|---|---|
| 1 | `SetProductWithdrawalExpenseFactor` | `LookupProductWithdrawalExpensesFactor`, keyed on `FinalProductWithdrawalIncrdLimitTableAssignment` |
| 2 | `SetLCM` | `LookupProductWithdrawalLCM` — **countrywide, one row, `1`** (E15) |
| 3 | `SetELP` | **Branches on the borrowed selector** — see below |
| 4 | `SetCFLILF` / `SetDeductibleFactor` / `SetFinalILF` | `LookupProductWithdrawalExpensesAndLiabilityIncrdLimitFactor`; deductible via **`LookupDedFactorProdsCSL`** — Prod/CompOps's table |
| 5 | `SetLossCosts` | **`LookupProdsCompldOpsLossCost`** — Prod/CompOps's table, keyed on `ProdsCompldOpsTerritory`. `0.0` if class code or territory is empty |
| 6 | `SetBaseRate` | `round(ELP × ProductWithdrawlExpenseFactor × LCM, 3)` **or** `round(LossCost × ProductWithdrawlExpenseFactor × LCM, 3)` |
| 7 | `SetPremiumDiscountCharge` | |
| 8 | `SetFinalRate` | `round(BaseRate × FinalILF × PackageModFactor × ExperienceRatingModificationFactor × ExpenseModification × ModToUse × PremiumDiscountCharge, 3)` |
| 9 | `SetPremium` | `round(FinalRate × exposure ÷ 1000, 0)` for the ÷1000 bases, else `× exposure` |

**Product Withdrawal has both rating paths** — loss cost *and* ELP — unlike liquor and railroad,
because it inherits them from its host. It is the first coverage gated whose base rate is a **host
subline's rate times a factor**, which is what *factor-on-host* means concretely.

### It borrows its host's rating-basis selector

`SetELP` tests **`../ProductWithdrawalELP != "Company"`** → `LookupProdsCompldOpsELPFactor`, else the
override, else `0.0`. And `ProductWithdrawalELP` is populated by `SetProductWithdrawalELP`, which
calls **`LookupProdsCompldOpsELPText`** — there is no Product Withdrawal selector table.

**So a dependent coverage takes its rating basis from its host's selector.** This is the third
selector shape found (see [335-Railroad §1](GATE-335-RAILROAD-PROTECTIVE.md) for the other two) and
the first where the selector is read **inside the rating chain to branch**, rather than written to
output and ignored.

### ERC misspells "Withdrawal" — consistently, in rules, DataDefs and a table name

| Correctly spelled | Misspelled |
|---|---|
| Rule `SetProductWithdrawalExpenseFactor` | writes DataDef **`ProductWithdrawlExpenseFactor`** |
| Table `ProductWithdrawalExpensesFactor` | Table **`ProductWithdrawlFactor`** |

Counted across the countrywide rule set: **`ProductWithdrawal…` 10 occurrences, `ProductWithdrawl…`
16.** The misspelling is not a stray typo — it is load-bearing in DataDef names, and
**`ProductWithdrawlFactor` is a real, populated, read table**, not a duplicate of the correctly
spelled one:

| Table | Key | A | B | C |
|---|---|---|---|---|
| `ProductWithdrawlFactor` *(misspelled)* | `IncreasedLimitsTableAssignmentProdsCompldOpsFinal` | **0.20** | **0.15** | **0.10** |
| `ProductWithdrawalExpensesFactor` | `FinalProductWithdrawalIncrdLimitTableAssignment` | 0.25 | 0.19 | 0.13 |
| `ProductWithdrawalLiabilityFactor` | `FinalProductWithdrawalIncrdLimitTableAssignment` | 0.13 | 0.10 | 0.07 |

**Different keys, different values, all three read by two rules each.** An engine that
normalises the spelling merges three distinct tables into a name collision.

**And the misspelled one is the manual's.** `GL-MU-2027-RU-001-C` p.93, **Table 44.B.3.b Product
Withdrawal Factors**, keyed on *"Products/Completed Operations Increased Limits Table Assignment"*:
**A 0.20 · B 0.15 · C 0.10** — exact, values and key axis. Rule 44.B.3.a.(5) directs: *"Multiply the
products/completed operations basic limit rate by the Product Withdrawal Factor in Table 44.B.3.b."*

`SublineProductWithdrawal` has 0 rows in every edition and **0 readers**. *(Reported here as a
notable "second orphan". **Demoted 2026-08-11**: `34_crosscheck.py` enumerated the population and
found **237 of 798** countrywide table instances unread, **all of them empty stubs**. It is an
unremarkable member of a large uniform class. The claim worth making is the inverse, and it holds:
**no populated countrywide rate table is unread.**)*

---

## 2. Loss Of Electronic Data and Cyber Incident Liability — one algorithm, two factor tables

Four rate-driven groups, in two matched pairs (Prem/Ops host and Prod/CompOps host). The chains are
step-for-step identical apart from the limit setup and the factor lookup:

| LoED (25 rules) | Cyber (23 rules) |
|---|---|
| `SetLossOfElectronicDataLimit` | `SetEachCyberIncidentOccurrenceLimit` + `SetCyberIncidentAggregateLimit` |
| `SetILF` → `SetDeductibleFactor` → `SetFinalILF` | *identical* |
| `SetAdjustedBaseRate` | *identical shape* |
| `SetHazardGrade` | *identical shape* |
| `SetLossOfElectronicDataFactor` | `SetCyberIncidentLiabilityFactor` |
| `SetFinalRate` → `SetPremium` → `SetPremiumIndicator` | *identical* |

**Same skeleton, zero shared bodies.** Cyber has two limit rules because it carries both an
occurrence and an aggregate limit; LoED has one.

### They read the host's *computed values*, not just its tables

This is the architectural finding of the gate. `SetAdjustedBaseRate` in the LoED Prem/Ops group
reads **directly into a sibling coverage group**:

```
../GeneralLiabilityClassificationPremOpsCoverage/PremOpsLossCost
../GeneralLiabilityClassificationPremOpsCoverage/PremOpsELP
../GeneralLiabilityClassificationPremOpsCoverage/LCM
../GeneralLiabilityClassificationPremOpsCoverage/ClaimsMadeMultiplier
../GeneralLiabilityClassificationPremOpsCoverage/PremOpsSizeOfRiskFinalRelativity
```

`AdjustedBaseRate = host loss cost (or ELP) × host LCM [× host ClaimsMadeMultiplier] × host
SizeOfRiskFinalRelativity × own FinalILF`, with four branches on `SizeOfRiskRatingApplies` and
`PremOpsProdsCoverageForm == "Claims Made"`.

Three consequences the build-order note *"must rate after their host subline"* understates:

1. **It is a data dependency, not an ordering preference.** Coverage groups cannot be evaluated
   independently; the engine needs a resolved sibling's intermediate values in scope. That is an
   architectural requirement for **Phase 4's kernel**, not a scheduling note.
2. **Item 6 depends on build-order item 10.** `PremOpsSizeOfRiskFinalRelativity` is **Size-Of-Risk**
   rating-plan output — OI-04, scheduled at item 10, four items later. Item 6 cannot be *completed*
   before Size-Of-Risk exists, only specified.
3. **A host's edition-scoped behaviour propagates.** The host's `ClaimsMadeMultiplier` and `LCM` are
   whichever the host's resolved countrywide parent computed, so LoED inherits 334's
   two-calculator split without expressing it.

### The hazard-grade tables are the largest countrywide rate tables in the corpus

| Table | CW 2023/2026 | CW 2027 | States (today) |
|---|---|---|---|
| `LossOfElectronicDataPremOpsHazardGrade` | **1,188** | **1,163** | 1 (NY, 1,190) |
| `CyberIncidentLiabilityPremOpsHazardGrade` | **1,188** | **1,163** | 1 (NY, 1,191) |

**1,188 → 1,163 is the Prem/Ops class list**, pre-2027 and 2027 respectively (OI-40 §4 measured
1,197 and 1,163 distinct codes in force). The hazard grade is **per class code, published
countrywide** — so these are countrywide tables carrying a full national class-level dataset, and
the 2027 edition re-issues them on the new class basis. **New York overrides both**, and is the only
jurisdiction that does.

Four factor tables per coverage, all countrywide, 4 rows each:
`LossOfElectronicData{PremOps,ProdsCompldOps}Factor{CG0437,CG0471}` — **keyed by endorsement form
number**, so the applicable endorsement selects the factor table. `CyberIncidentLiability…Factors`
and `TypeOfPolicyWithCyberIncidentLiabCoverage` follow the same shape.

---

## 3. The layer inversion is now the rule, not the exception

Every countrywide operand in this item is countrywide-only, and every state table is empty:

| | Countrywide | States |
|---|---|---|
| `ProductWithdrawalLCM` | **1 row: `1`** | 0/51 |
| `ProductWithdrawalMinPremium` | **1 row: `0`** | 0/51 |
| `ProductWithdrawal{Expenses,Liability}Factor`, `ProductWithdrawlFactor` | 3 rows each | 0/51 |
| `LossOfElectronicDataMinPremium`, `CyberIncidentLiabilityMinPremium` | 1 row each | 0/51 |
| all eight LoED/Cyber factor tables | 4 rows each | 0/51 |
| the two hazard-grade tables | **1,188 rows** | 1/51 (NY) |
| `ProductWithdrawalExpensesAndLiabilityIncrdLimitFactor` | **0 rows** | **51/51 · 1,836** |

Only the ILF is state-supplied. **Four sublines in, the pattern is settled: class-level rate content
is state-supplied; structural factors, minimums and multipliers are countrywide.** README finding #1
describes the loss-cost layer correctly and the rest of the countrywide layer incorrectly.

**E15 and E16 hold for a third subline.** `ProductWithdrawalLCM = 1`; `ProductWithdrawalMinPremium =
0`, and CW 2027 empties the table. Three of three ELP-or-factor-rated sublines now carry the same
two placeholders — they are properties of the corpus, not of any coverage.

---

## 4. Manual confirmations

| # | ERC | Manual | Verdict |
|---|---|---|---|
| 1 | `ProductWithdrawlFactor` = A 0.20 · B 0.15 · C 0.10, keyed on Prod/CompOps ILTA | **Table 44.B.3.b**, p.93 — same values, same key axis | ✅ **Exact** |
| 2 | PW base rate = host Prod/CompOps rate × PW factor | **Rule 44.B.3.a.(5)**, p.93: *"Multiply the products/completed operations basic limit rate by the Product Withdrawal Factor"* | ✅ Confirms factor-on-host |
| 3 | `SetPremiumDiscountCharge`, and participation/cut-off handling absent from the rate chain | **Rule 44.B.3.b–c**, p.93: a Participation Percentage or Cut-off Date on the Schedule → *"refer to company to determine any premium discount"* | ✅ Confirms both are **refer**, not computed |
| 4 | Product Withdrawal is subline **365** | **Rule 44**, p.89 | ✅ Its own subline — unlike LoED and Cyber |

**LoED and Cyber are not in Rule 44–49 of the multistate manual.** They are endorsement-driven
coverages (`CG 04 37`, `CG 04 71`) whose factor tables ERC keys by form number; their manual
treatment sits with the endorsements rather than a numbered coverage rule. Recorded, not chased —
the ERC derivation stands on its own under the doctrine, and **the endorsement-keyed factor tables
are themselves the evidence that the form selects the rate**.

---

## 5. Escalations and open items

| # | Item | Detail |
|---|---|---|
| **E18** *(new)* | **A rating rule reads a sibling coverage group's computed values** | `SetAdjustedBaseRate` reads five DataDefs under `../GeneralLiabilityClassificationPremOpsCoverage/`. The kernel must expose resolved sibling state, and evaluation order across coverage groups becomes part of the algorithm. Not a question for ISO — a design constraint that Phase 4 must satisfy and the build plan did not state |
| **OI-46** *(new)* | **Item 6 cannot complete before item 10** | LoED and Cyber read `PremOpsSizeOfRiskFinalRelativity`, Size-Of-Risk rating-plan output (OI-04, build-order item 10). Either resequence, or accept that item 6 ships specified-but-not-runnable |
| **OI-47** *(new)* | **ERC's "Withdrawl" misspelling is load-bearing** | 16 misspelled against 10 correct occurrences; `ProductWithdrawlFactor` is a **distinct populated table with a different key and different values** from `ProductWithdrawalExpensesFactor`. Normalising the spelling merges three tables. Do not normalise; assert both spellings resolve to distinct artifacts at load time |
| **E15**, **E16** | **Generalised to a third subline** | `ProductWithdrawalLCM = 1`, `ProductWithdrawalMinPremium = 0` |

`SublineProductWithdrawal` — 0 rows, 0 readers, every edition — is the **second orphan table**, after
`RailroadLossCost`. Two instances is enough to make it a load-time check rather than a curiosity:
**report any rate table with no reader.**

---

## 6. Test result

**No oracle.** The golden case carries no Product Withdrawal, LoED or Cyber premium. **Fourth
consecutive subline without one** — the OK policy exercises 334 and 336 only.

| Check | Result |
|---|---|
| `tests/verify_golden.py` | **80/80** (unchanged) |
| `ProductWithdrawlFactor` vs manual Table 44.B.3.b | **3/3 exact**, key axis included |
| Rate-driven groups in item 6 | **7** *(corrected — §6a)*, 150 countrywide rules plus an 11-rule chain in the shared classification group |
| Pairwise identical rule bodies across the 6 groups | **0** |
| Tables with 0 rows and 0 readers | **1** (`SublineProductWithdrawal`) |
| State deviation surface | **17 rules, 9 jurisdictions** (CA IN MO MT ND NH OK TN UT) |

---

## 6a. Addendum, 2026-08-11 — a seventh rate-driven path this gate missed

**Found by `scripts/erc/34_crosscheck.py` on its first run**, asking a question no gate had asked:
*is every rate-driven coverage group claimed by some build-order item?* One was not.

**`GeneralLiabilityClassification` is `RATE_DRIVEN`, and it is item 6's.** It carries the entire
**Limited Product Withdrawal Expense** chain — 11 rules — instead of giving it a coverage group of
its own:

`SetLmtdProductWithdrawlFactor` · `SetLmtdLCM` · `SetLmtdCSLILF` · `SetLmtdDeductibleFactor` ·
`SetLmtdFinalILF` · `SetHighestLmtdProdsWithdrawalFinalILFFlag` ·
`SetLmtdProdsWithdrawalIncreasedLimitsFactor` · `SetLmtdProdsWithdrawalBaseRate` ·
`SetLmtdProdsWithdrawalFinalRate` · `SetLmtdProdsWithdrawalPremium` ·
`SetLimitedProductWithdrawalAggregateAndDeductibleLimits`

plus two guards: `DoMessageMustEnterLimitedProductWithdrawalDeductibleFactorOverride` and
`DoMessageTheLimitedProductWithdrawalCoveragepremiumCannotBeANegativePremium`.

```
LmtdProdsWithdrawalFinalRate = LmtdProdsWithdrawalBaseRate × LmtdProdsWithdrawalFinalILF
                               × PackageModFactor
LmtdProdsWithdrawalPremium   = round(LmtdProdsWithdrawalFinalRate
                                     × ProdsCompldOpsCovExposure [÷ 1000], 0)
```

Gated on `ProdsWithdrawalCoverage == "Yes"`, on the policy-level
`GeneralLiabilityLimitedProductWithdrawalExpenseEndtPolLvl` row existing, and on the risk having a
Prod/CompOps coverage — **it is a factor-on-host of 336, like the rest of item 6**, and it divides
by 1,000 on the same nine Prod/CompOps premium bases.

**And it closes a loose end in §1.** That section found `ProductWithdrawlFactor` — the misspelled
table whose A 0.20 / B 0.15 / C 0.10 matches manual Table 44.B.3.b exactly — had **two readers** and
could not say which coverage used it. **`SetLmtdProductWithdrawlFactor` is the reader.** The
misspelled table serves the *Limited* coverage; the correctly-spelled `…ExpensesFactor` and
`…LiabilityFactor` serve the full one. Three tables, three purposes, one letter apart (OI-47).

### Why the gate missed it, and why that is the interesting part

**The coverage has no coverage group.** Every other rate-driven path in this project lives in a
`GeneralLiabilityClassification<Something>Coverage` group, and this gate enumerated the six that
matched that shape. Limited Product Withdrawal lives in the shared **classification** container, so
**the group name gives no hint that a coverage is inside it.**

Which is the same failure as §0's mis-sizing, inverted. §0 over-matched a substring and swept in 19
groups that were not item 6's. This under-matched a shape and missed a coverage that was.
**Both were the query defining the population** — see build plan §9, habit 8.

**Sizing is unchanged at 150 countrywide rules.** Claiming the whole `GeneralLiabilityClassification`
group for item 6 would inflate it to 270, because that container also holds classification-level
rules for every other subline. **Once a group is shared, the unit of ownership is the rule, not the
group** — recorded in `33_phase_sizing.py` and allow-listed with its owner named in
`34_crosscheck.py`.

**Not derived here:** the eleven rules are named, the premium formula is read, and the manual anchor
is Table 44.B.3.b. A full §9 treatment — inputs, state deviations, referral paths, the two guards —
**remains owed** and is recorded as **OI-50**.

---

## 7. Findings

- **A build-order item was mis-sized by a substring match, and it had already changed the plan.**
  The recommendation to split item 6 into three was argued from 320 rules; the real figure is 150.
  The recommendation survives on different grounds. **Measurements that drive plans need the same
  scrutiny as the claims they support** — this one went into a document and a build-plan row before
  anyone re-derived it.
- **Factor-on-host is a kernel requirement, not a scheduling note.** LoED reads five of its host's
  *computed* values. Until now every gate could be read as "one coverage group, one algorithm"; this
  one cannot, and the architecture section never said so.
- **Item 6 depends on item 10.** A build order that was derived from coverage structure has a data
  dependency running four items backwards.
- **A misspelling can be load-bearing.** `ProductWithdrawlFactor` and `ProductWithdrawalExpensesFactor`
  are different tables with different keys and different values, and the *misspelled* one is the one
  the filed manual prints. Tidying the name would silently merge them.
- **Two orphan tables in two consecutive gates.** `RailroadLossCost` and `SublineProductWithdrawal`
  both exist, are empty everywhere, and are read by nothing. N7 needs its third clause stated as a
  check, not just a caution.

---

## 9. Addendum, 2026-08-12 — OI-50 closed: Limited Product Withdrawal Expense, derived

**The §9 treatment §6a said was owed.** Measured against **`GL_CW_20260101_V01`**, as of
**2026-08-12**, and pinned by [`tests/verify_oi50.py`](../../tests/verify_oi50.py).

### 9.1 The population is 54 rules, not 11 — and the correction matters

§6a called it *"an 11-rule chain inside the shared `GeneralLiabilityClassification` container"*.
That is right about the **rating** chain and wrong about the coverage, which spans **five**
DataDefGroups:

| Group | Rules | Role |
|---|---|---|
| `GeneralLiabilityClassification` | **11** | the rating chain — per classification |
| `GeneralLiability` + `GeneralLiabilityClassification` | **4** | `DoMessage*` guards (§9.4) |
| `…LimitedProductWithdrawalExpenseEndtPolLvl` | **24** | policy level: limits, deductible, class-premium roll-up, minimum premium |
| `…LimitedProductWithdrawalExpenseCoverage` | **7** | the coverage premium |
| `…LimitedProductWithdrawalExpenseEndtPremiumToReachMinCoveragePolLvl` | **8** | the minimum-premium iteration |
| | **54** | of **4,557** countrywide rules |

**The 11 are the part that is shared-container-resident and therefore easy to miss** — that was
§6a's actual finding, and it stands. The other 43 live in properly-named groups and were never
hidden; nobody had counted them.

### 9.2 The chain, end to end

```
LmtdProdsWithdrawalLCM                    ← branch on ProdsWithdrawalCoverage / ProdsCompldOpsCov
LmtdProdsWithdrawalProductWithdrawalFactor ← LookupProductWithdrawlFactor(FinalProdsCompldOpsIncrdLimitTableAssignment)
                                             *** the MISSPELLED table — OI-47 ***
LmtdProdsWithdrawalBaseRate  = (ProdsCompldOpsLossCost | FinalProdsCompldOpsELP)
                             × LmtdProdsWithdrawalLCM
                             × LmtdProdsWithdrawalProductWithdrawalFactor
                               ↑ reads the SIBLING group's loss cost — E18

LmtdProdsWithdrawalAggregateLimit, …Deductible
                             ← the POLICY-LEVEL endorsement row [1]
LmtdProdsWithdrawalIncreasedLimitsFactor
                             ← LookupProductWithdrawalExpensesAndLiabilityIncrdLimitFactor(
                                   FinalProdsCompldOpsIncrdLimitTableAssignment, AggregateLimit)
LmtdProdsWithdrawalCSLILF    = LmtdProdsWithdrawalIncreasedLimitsFactor
LmtdProdsWithdrawalDeductibleFactorForRating
                             ← LookupDedFactorProdsCSL(…) or the supplied Override

LmtdProdsWithdrawalFinalILF  = CSLILF − DeductibleFactorForRating              ← N12
LmtdProdsWithdrawalFinalRate = round(BaseRate × FinalILF × PackageModFactor, 3)
LmtdProdsWithdrawalPremium   = round(FinalRate × ProdsCompldOpsCovExposure [÷1000], 0)

Premium (coverage) = LimitedProductWithdrawalClassPremium
                   × ProductWithdrawalParticipationPercentage
                   × PackageModFactor − PremiumDiscountCharge      | or ManualPremium
```

**Three cross-links worth naming:**

1. **The ÷1000 is decided by the same nine-value premium-basis list** as size-of-risk —
   `Admissions · Area · Gallons · Gross Sales · Passenger Days · Payroll · Total Cost · Total
   Operating Expenses · Vehicles`. Third appearance of that filed list; it must be read once from
   one place ([gate size-of-risk §4](GATE-SIZE-OF-RISK.md)).
2. **`SetLmtdProdsWithdrawalBaseRate` reads `GeneralLiabilityClassificationProdsCompldOpsCoverage/ProdsCompldOpsLossCost`** — E18 again, and the reason this coverage cannot be evaluated
   independently of its host.
3. **`ProductWithdrawalParticipationPercentage` is a new submission input**, applied at the
   coverage level after the class premiums are rolled up.

### 9.3 The misspelling is load-bearing here, confirmed on values

| Table | Rows | Values (A / B / C) | Read by |
|---|---|---|---|
| **`ProductWithdrawlFactor`** *(misspelled)* | **3** | **0.20 / 0.15 / 0.10** | **this** coverage, via `SetLmtdProductWithdrawlFactor` |
| `ProductWithdrawalExpensesFactor` | 3 | 0.25 / 0.19 / 0.13 | the full Product Withdrawal coverage (§1) |

**Different tables, different values, both live, and the misspelled one is what the filed manual
prints** — `GL-MU-2027-RU-001-C` p.93, Table 44.B.3.b. OI-47's *never normalise the spelling* now
has its reader named and its values checked.

### 9.4 Four guards, and one of them is the only negative-premium check in the corpus

| Guard | Group | What it enforces |
|---|---|---|
| `DoMessageLimitedProductWithdrawalEndt` | `GeneralLiability` | *"A classification that does not include Products coverage to the premises must be selected to attach the Limited Product Withdrawal Endorsement"* |
| `DoMessageMustEnterLimitedProductWithdrawalDeductibleFactorOverride` | `GeneralLiabilityClassification` | the override must be supplied when the filed factor is absent — the OI-44 pattern |
| `DoMessageProdWithdrawalDedFactorCannotExceedPWILF` | `GeneralLiabilityClassification` | *"Limited Product Withdrawal Deductible Factor cannot exceed the Limited Product Withdrawal Increased Limits Factor"* — i.e. `FinalILF ≥ 0` |
| `DoMessageTheLimitedProductWithdrawalCoveragepremiumCannotBeANegativePremium` | `GeneralLiabilityClassification` | the premium may not go negative |

**N15 exactly.** `FinalILF = CSLILF − DeductibleFactor` has no arithmetic floor; the only thing
preventing a negative rate is a validation rule. Port the chain without the guards and the engine
will quote negative premiums on a deductible larger than the ILF.

### 9.5 Loss costs are state-supplied — and here, uniformly

`ProductWithdrawalExpensesAndLiabilityIncrdLimitFactor`:

| | |
|---|---|
| Countrywide editions carrying rows | **0 of 10** |
| Jurisdictions carrying rows | **51 of 51**, **36 rows each** |

**N8 in its cleanest form yet** — and a deliberate contrast with size-of-risk, where only **35 of
51** ship and the other 16 leave the coverage unpriceable
([gate size-of-risk §7](GATE-SIZE-OF-RISK.md)). Here there is no gap: the algorithm is countrywide,
the rates are the state's, and every state filed them.

### 9.6 The deviation surface — stated precisely, because the first version of it was wrong

An earlier note recorded *"0 of 51 jurisdictions override any of it."* Re-measuring it went wrong
twice before it went right, and both wrong answers are the same defect:

| Attempt | Answer | What was wrong |
|---|---|---|
| 1 — the 11-rule chain | 0 of 51 | correct, but stated over "any of it" when only the chain was measured |
| 2 — rule **names** anywhere in the package | **27 of 51** | `ErcProcess` and `InitializeRuleSet` exist in *hundreds* of groups. A generic name matched everywhere and the population became the whole package |
| **3 — membership by DataDefGroup** | **1 of 51** | **the measurement** |

| | |
|---|---|
| Jurisdictions overriding any rule **in the three dedicated groups** | **1 of 51 — Texas**, being `InitializeRuleSet` and two stat-code lookups |
| Jurisdictions overriding any of the **11 rating rules** | **0 of 51** |

**The original claim was right, and stronger than it looked.** **This is the only rating chain in
the project with a countrywide-only derivation and effectively no state deviation at all** — which
is exactly why it was safe to leave until last, and why it is an addendum rather than a gate.

*(Attempt 2 is habit 8's failure mode for the fourth time in three sessions, and the first time it
made a finding look **worse** than it is. The rule that catches it is the same one: membership in a
population is by the thing that defines the population — here the `DataDefGroup` — never by a name
that happens to be shared.)*

### 9.7 Register

| | |
|---|---|
| **OI-50** | **CLOSED.** Chain derived, guards named, tables confirmed on values, deviation surface measured |
| **OI-47** | Reader named and values checked: the *misspelled* `ProductWithdrawlFactor` is this coverage's factor table |
| **E18** | Third instance: `SetLmtdProdsWithdrawalBaseRate` reads the sibling group's `ProdsCompldOpsLossCost` |
| **N8** | Cleanest instance: **0 of 10** countrywide, **51 of 51** jurisdictions, 36 rows each |
| **N15** | The only negative-premium guard in the corpus lives here |
| **Owed work** | **All three items closed.** California, New York, OI-50 |


---

## 10. Addendum, 2026-08-12 — California does not write either coverage

**Found by [`40_referral_census.py`](../../scripts/erc/40_referral_census.py) probe 6**, built for
build-order item 12. This gate derived Loss Of Electronic Data and Cyber Incident Liability in
detail — including calling their hazard-grade tables *"the largest countrywide rate tables in the
corpus"* — and **never asked whether a jurisdiction withdraws them. California does.**

**13 tables overridden to zero rows in `GL_CA_20241101_V01`:**

| Coverage | Tables emptied |
|---|---|
| Cyber Incident Liability | `CyberCoverageLimitStatCode` · `CyberIncidentLiabilityMinPremium` · `…PremOpsFactors` · `…PremOpsHazardGrade` · `…ProdsCompldOpsFactors` · `…ProdsCompldOpsHazardGrade` · `TypeOfPolicyWithCyberIncidentLiabCoverage` |
| Loss Of Electronic Data | `LossOfElectronicDataMinPremium` · `…PremOpsFactorCG0437` · `…PremOpsFactorCG0471` · `…PremOpsHazardGrade` · `…ProdsCompldOpsFactorCG0437` · `…ProdsCompldOpsFactorCG0471` · `…ProdsCompldOpsHazardGrade` |

**And it is guarded, deliberately.** `SetCoverageOnPolicyIndicator` is stubbed to a constant **`0`**
in **all six** groups — both classification groups per coverage, plus each
`PremiumToReachMinCoverage` iterator. The rating chain never runs, so the empty tables are never
reached. **This is not a silent zero and not a defect: it is N3's neutralising-stub idiom, the same
one New York uses for claims-made and size-of-risk, applied to withdraw two whole coverages.**

**Three things follow.**

1. **The gate's §2 algorithm is correct and describes 50 of 51 jurisdictions.** California is not
   an exception to it; California does not reach it.
2. **It completes a coherent picture of California** rather than adding a puzzle. CA is the sole
   `GL_CW_20231201_V02` jurisdiction ([California differential](CALIFORNIA-DIFFERENTIAL.md)), it
   stubs `SetSizeOfRiskRatingApplies` to `"No"` ([gate size-of-risk](GATE-SIZE-OF-RISK.md) §6a) —
   and **size-of-risk is precisely what LoED and Cyber read across the group boundary (E18)**. A
   state that withdraws both coverages has no reason to keep the input they need.
3. **`SetCoverageOnPolicyIndicator` is now the single most load-bearing stub in the corpus.** It is
   the mechanism by which a jurisdiction switches a coverage off entirely, and an engine that
   evaluates a rating chain without consulting it first will read empty tables in California and
   hit nulls that mean nothing.

**Recorded as OI-65.**
