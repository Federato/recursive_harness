# Product Withdrawal / Loss Of Electronic Data / Cyber Incident Liability — Rating Algorithms

**Source:** `C:\Projects\Recursive_Harness_2.0\docs\gates\GATE-365-WITHDRAWAL-LOED-CYBER.md` (as-of date 2026-08-11, addenda through 2026-08-12), derived against **`GL_CW_20231201_V03`**.
**Line:** General Liability (GL), Countrywide, build-order item 6.
**Documented (this port):** 2026-08-20.
**Reformatted from:** the gate doc above, into the CF `RatingAlgorithms` template. This is a reformat, not new research — every fact below is carried over from the source gate; nothing has been re-derived from ERC XML directly, so citations point at the gate doc's own section headings rather than rule-file line numbers except where the gate itself quotes a line-level formula.

This gate covers **three unrelated coverages that share a rule-name skeleton and no implementation**:

- **Product Withdrawal (subline 365)** — Coverage A (Product Withdrawal Expense) and Coverage B (Products Withdrawal Liability), rated separately, each a factor applied to the Products/Completed Operations (Prod/CompOps, subline 336) base rate.
- **Limited Product Withdrawal Expense (endorsement CG 04 36)** — a distinct, narrower coverage living inside the shared `GeneralLiabilityClassification` container rather than its own coverage group; also a factor-on-Prod/CompOps-host coverage.
- **Loss Of Electronic Data (LoED, endorsements CG 04 37 / CG 04 71)** and **Cyber Incident Liability** — new in edition CW 2027, each rated twice (once hosted on Premises/Operations, once on Prod/CompOps), reading their host's *computed* intermediate values, not just its tables.

Per the gate: pairwise rule-body overlap across the six rate-driven groups is **zero identical bodies**, despite 12–25 rules of name overlap per pair. They are documented together because the *questions* are shared (host dependency, factor-on-host, state deviation), not the code.

---

## Master orchestration

The gate doc does not trace a single top-level dispatcher rule (unlike the CF `SetBlanketRatesAndFactors` orchestration) — GL's classification-level rating runs per coverage group, and item 6's groups are scattered across containers rather than sequenced from one place. The dependency structure the gate establishes is:

```
Prod/CompOps (subline 336) rates first
    -> ProdsCompldOpsLossCost, FinalProdsCompldOpsELP, LCM, ProdsCompldOpsTerritory resolved

Prem/Ops (subline 334) rates first (for the Prem/Ops-hosted LoED/Cyber groups)
    -> PremOpsLossCost, PremOpsELP, LCM, ClaimsMadeMultiplier,
       PremOpsSizeOfRiskFinalRelativity resolved
       (PremOpsSizeOfRiskFinalRelativity is Size-Of-Risk rating-plan output,
        build-order item 10 -- item 6 cannot complete before item 10 exists; OI-46)

then, in no fixed documented order:
    Product Withdrawal Coverage A  (…ExclusionCoverageAProductWithdrawalExpenseRules, 27 rules)
    Product Withdrawal Coverage B  (…ExclusionCoverageBProductWithdrawalLiabilityRules, 27 rules)
    Limited Product Withdrawal Expense rating chain (GeneralLiabilityClassification container, 11 rules)
    Limited Product Withdrawal Expense policy-level  (…EndtPolLvl, 24 rules)
    Limited Product Withdrawal Expense coverage premium (…Coverage, 7 rules)
    Limited Product Withdrawal Expense min-premium iterator (…PremiumToReachMinCoveragePolLvl, 8 rules)
    Loss Of Electronic Data, Prem/Ops host   (25 rules)
    Loss Of Electronic Data, Prod/CompOps host (25 rules)
    Cyber Incident Liability, Prem/Ops host   (23 rules)
    Cyber Incident Liability, Prod/CompOps host (23 rules)
```

Every LoED/Cyber group and the Limited Product Withdrawal chain read a **sibling coverage group's already-computed values** (`../GeneralLiabilityClassificationPremOpsCoverage/...` or the Prod/CompOps equivalent) rather than re-deriving them — this is escalation **E18** in the gate, and it means these coverage groups cannot be evaluated independently of their host. (GATE-365 §2, §9.2, Findings.)

`SetCoverageOnPolicyIndicator` gates each group on/off per coverage (e.g. stubbed to a constant `0` in all six California LoED/Cyber groups to withdraw the coverages entirely — GATE-365 §10). No premium is computed for a withdrawn coverage; empty state tables are never reached because the gate short-circuits first.

---

## File map

| Piece | Group / rule set | Rules | Source citation |
|---|---|---|---|
| Product Withdrawal Coverage A rate build-up | `GeneralLiabilityClassificationExclusionCoverageAProductWithdrawalExpenseRules` | 27 | GATE-365 §1 |
| Product Withdrawal Coverage B rate build-up | `GeneralLiabilityClassificationExclusionCoverageBProductWithdrawalLiabilityRules` | 27 | GATE-365 §1 |
| Limited Product Withdrawal Expense — rating chain | `GeneralLiabilityClassification` (shared container — not its own coverage group) | 11 | GATE-365 §6a, §9.1 |
| Limited Product Withdrawal Expense — guards | `GeneralLiability` + `GeneralLiabilityClassification` | 4 | GATE-365 §9.1, §9.4 |
| Limited Product Withdrawal Expense — policy level (limits, deductible, class-premium roll-up, minimum premium) | `…LimitedProductWithdrawalExpenseEndtPolLvl` | 24 | GATE-365 §9.1 |
| Limited Product Withdrawal Expense — coverage premium | `…LimitedProductWithdrawalExpenseCoverage` | 7 | GATE-365 §9.1 |
| Limited Product Withdrawal Expense — premium-to-reach-minimum iterator | `…LimitedProductWithdrawalExpenseEndtPremiumToReachMinCoveragePolLvl` | 8 | GATE-365 §9.1 |
| Loss Of Electronic Data — Prem/Ops host | LoED Prem/Ops group (exact DataDefGroup name not given in source) | 25 | GATE-365 §2 |
| Loss Of Electronic Data — Prod/CompOps host | LoED Prod/CompOps group (exact DataDefGroup name not given in source) | 25 | GATE-365 §2 |
| Cyber Incident Liability — Prem/Ops host | Cyber Prem/Ops group (exact DataDefGroup name not given in source) | 23 | GATE-365 §2 |
| Cyber Incident Liability — Prod/CompOps host | Cyber Prod/CompOps group (exact DataDefGroup name not given in source) | 23 | GATE-365 §2 |
| Host loss-cost / ELP / LCM (Prod/CompOps) | `GeneralLiabilityClassificationProdsCompldOpsCoverage` | — | GATE-365 §1, §9.2 |
| Host loss-cost / ELP / LCM / Size-Of-Risk (Prem/Ops) | `GeneralLiabilityClassificationPremOpsCoverage` | — | GATE-365 §2 |

> Note: unlike the CF source (which was read directly from ERC XML with line numbers), this gate is itself a derived document. Where it does not give exact rule-file paths or line numbers for a table or group, none are asserted here — see "Not resolved" flags below.

---

## Product Withdrawal (365) Coverage A — Product Withdrawal Expense — rate build-up

Chain, from `GeneralLiabilityClassificationExclusionCoverageAProductWithdrawalExpenseRules` (GATE-365 §1, table):

```
SetProductWithdrawalExpenseFactor
SetLCM
SetELP
SetCFLILF / SetDeductibleFactor / SetFinalILF
SetLossCosts
SetBaseRate
SetPremiumDiscountCharge
SetFinalRate
SetPremium
```

### Step 1 — Product Withdrawal Expense factor
`SetProductWithdrawalExpenseFactor`

```
ProductWithdrawalExpenseFactor = LookupProductWithdrawalExpensesFactor(
    FinalProductWithdrawalIncrdLimitTableAssignment)
```

Reads matrix `ProductWithdrawalExpensesFactor` (correctly spelled) — 3 rows, A 0.25 / B 0.19 / C 0.13. (GATE-365 §1, table in "ERC misspells... " section.)

### Step 2 — LCM
`SetLCM`

```
LCM = LookupProductWithdrawalLCM(...)
```

Countrywide, one row, value **1**. (GATE-365 §1, item 2; §3, E15.)

### Step 3 — ELP (borrows the host's rating-basis selector)
`SetELP`

```
if ../ProductWithdrawalELP != "Company":
    ELP = LookupProdsCompldOpsELPFactor(...)     # Prod/CompOps's own ELP table
else:
    ELP = override, else 0.0
```

`ProductWithdrawalELP` itself is populated by `SetProductWithdrawalELP`, which calls `LookupProdsCompldOpsELPText` — there is no Product-Withdrawal-specific rating-basis selector table; Product Withdrawal borrows its host's. (GATE-365 §1, "It borrows its host's rating-basis selector.")

### Step 4 — Increased limits and deductible
`SetCFLILF` / `SetDeductibleFactor` / `SetFinalILF`

```
CFLILF (final ILF component) = LookupProductWithdrawalExpensesAndLiabilityIncrdLimitFactor(...)
DeductibleFactor              = LookupDedFactorProdsCSL(...)     # Prod/CompOps's deductible table
FinalILF                       = combination of the two (gate does not give the exact combining formula for this step)
```

(GATE-365 §1, item 4.)

### Step 5 — Loss costs
`SetLossCosts`

```
LossCost = LookupProdsCompldOpsLossCost(ProdsCompldOpsTerritory)   # Prod/CompOps's own table
         = 0.0 if class code or territory is empty
```

(GATE-365 §1, item 5.)

### Step 6 — Base rate
`SetBaseRate`

```
BaseRate = round(ELP x ProductWithdrawalExpenseFactor x LCM, 3)
        or round(LossCost x ProductWithdrawalExpenseFactor x LCM, 3)
```

Product Withdrawal is the first coverage in this gate whose base rate is **a host subline's rate times a factor** ("factor-on-host") — and the only one of the three coverages here carrying both a loss-cost path *and* an ELP path (unlike Liquor and Railroad). (GATE-365 §1, item 6 and surrounding prose.)

### Step 7 — Premium discount charge
`SetPremiumDiscountCharge` — present in the chain; the gate records only that a Participation Percentage or Cut-off Date on the schedule triggers a manual "refer to company" per manual Rule 44.B.3.b–c, not a computed formula. Not resolved in source docs — the gate does not give the `SetPremiumDiscountCharge` formula itself, only that it and any participation/cut-off handling are a **refer**, not computed, condition (GATE-365 §4, row 3).

### Step 8 — Final rate
`SetFinalRate`

```
FinalRate = round(
    BaseRate
  x FinalILF
  x PackageModFactor
  x ExperienceRatingModificationFactor
  x ExpenseModification
  x ModToUse
  x PremiumDiscountCharge
, 3)
```

(GATE-365 §1, item 8.)

### Step 9 — Premium
`SetPremium`

```
Premium = round(FinalRate x exposure / 1000, 0)     # for the /1000 premium bases
        = FinalRate x exposure                       # otherwise
```

(GATE-365 §1, item 9.)

---

## Product Withdrawal (365) Coverage B — Products Withdrawal Liability — rate build-up

**Structurally identical 9-step chain** to Coverage A, from `GeneralLiabilityClassificationExclusionCoverageBProductWithdrawalLiabilityRules` (also 27 rules) — the gate documents the two coverages together and calls out only the factor difference:

```
ProductWithdrawalLiabilityFactor = LookupProductWithdrawalLiabilityFactor(
    FinalProductWithdrawalIncrdLimitTableAssignment)
```

3 rows, A 0.13 / B 0.10 / C 0.07 — same key axis as Coverage A's factor (`FinalProductWithdrawalIncrdLimitTableAssignment`), different table, different values. (GATE-365 §1, table.) All other steps (LCM, ELP-via-host-selector, CFLILF/DeductibleFactor/FinalILF, loss costs, base rate, premium discount charge, final rate, premium) follow Coverage A's formulas verbatim with `ProductWithdrawalLiabilityFactor` substituted for `ProductWithdrawalExpenseFactor`. Not resolved in source docs — the gate does not spell out Coverage B's steps rule-by-rule the way it does Coverage A's; it states the chains are the same shape "differing only in which factor they apply."

---

## Product Withdrawal (365) — premium

The gate does not give a separate coverage-level `SetPremium`/gate/branch structure for 365 the way the CF source gives Basic Group I/II/Broad/Special premium files (no scheduled/blanket/Legal-Liability branching is described for Product Withdrawal). Step 9 above (`SetPremium`, `round(FinalRate x exposure / 1000, 0)` or `FinalRate x exposure`) **is** the premium step for both coverages A and B. Not applicable to this subline — no multi-branch premium structure (blanket, Legal Liability, scheduled building, etc.) is documented in the source; Product Withdrawal premium is a single formula per coverage.

### Gate — coverage on policy
Each of the six rate-driven groups (the two Product Withdrawal coverages, LoED x2, Cyber x2) is switched by `SetCoverageOnPolicyIndicator`, stubbed to `0` when a jurisdiction withdraws the coverage (documented for California — GATE-365 §10). No branch structure beyond on/off is given in source for 365 itself.

---

## Limited Product Withdrawal Expense (endorsement CG 04 36) — rate build-up

**Not its own subline** — it is a coverage attached to Prod/CompOps (336) via endorsement, rating inside the shared `GeneralLiabilityClassification` container (11 rules) plus four supporting DataDefGroups (43 more rules), 54 total. (GATE-365 §6a, §9.1.)

Executed in order (per GATE-365 §9.2, "The chain, end to end"):

```
SetLmtdProductWithdrawlFactor
SetLmtdLCM
SetLmtdCSLILF
SetLmtdDeductibleFactor
SetLmtdFinalILF
SetHighestLmtdProdsWithdrawalFinalILFFlag
SetLmtdProdsWithdrawalIncreasedLimitsFactor
SetLmtdProdsWithdrawalBaseRate
SetLmtdProdsWithdrawalFinalRate
SetLmtdProdsWithdrawalPremium
SetLimitedProductWithdrawalAggregateAndDeductibleLimits
```

### Step 1 — LCM
`LmtdProdsWithdrawalLCM` — branches on `ProdsWithdrawalCoverage` / `ProdsCompldOpsCov`. (GATE-365 §9.2.)

### Step 2 — Product Withdrawal factor (the misspelled table)
`SetLmtdProductWithdrawlFactor`

```
LmtdProdsWithdrawalProductWithdrawalFactor =
    LookupProductWithdrawlFactor(FinalProdsCompldOpsIncrdLimitTableAssignment)
```

Reads matrix `ProductWithdrawlFactor` — the **misspelled** table (see "Supporting lookups" below): 3 rows, A 0.20 / B 0.15 / C 0.10, keyed on `IncreasedLimitsTableAssignmentProdsCompldOpsFinal` / `FinalProdsCompldOpsIncrdLimitTableAssignment`. This resolves an open question the gate itself carried from §1: the misspelled table has two readers, and `SetLmtdProductWithdrawlFactor` is the second one — it serves Limited Product Withdrawal; the correctly-spelled `…ExpensesFactor` / `…LiabilityFactor` tables serve the full (365) coverage. (GATE-365 §9.2, §9.3, OI-47.)

### Step 3 — Base rate
`SetLmtdProdsWithdrawalBaseRate`

```
LmtdProdsWithdrawalBaseRate =
    (ProdsCompldOpsLossCost | FinalProdsCompldOpsELP)     # from the SIBLING group — E18
  x LmtdProdsWithdrawalLCM
  x LmtdProdsWithdrawalProductWithdrawalFactor
```

Reads `GeneralLiabilityClassificationProdsCompldOpsCoverage/ProdsCompldOpsLossCost` directly from the sibling coverage group — the third instance of E18 in this gate. (GATE-365 §9.2, item 2 under "Three cross-links worth naming.")

### Step 4 — Limits and deductible
```
LmtdProdsWithdrawalAggregateLimit, …Deductible
    <- the policy-level endorsement row [1]

LmtdProdsWithdrawalIncreasedLimitsFactor <-
    LookupProductWithdrawalExpensesAndLiabilityIncrdLimitFactor(
        FinalProdsCompldOpsIncrdLimitTableAssignment, AggregateLimit)

LmtdProdsWithdrawalCSLILF = LmtdProdsWithdrawalIncreasedLimitsFactor

LmtdProdsWithdrawalDeductibleFactorForRating <-
    LookupDedFactorProdsCSL(...) or the supplied Override
```

(GATE-365 §9.2.)

### Step 5 — Final ILF and rate
```
LmtdProdsWithdrawalFinalILF  = CSLILF - DeductibleFactorForRating          # N15: no arithmetic floor
LmtdProdsWithdrawalFinalRate = round(BaseRate x FinalILF x PackageModFactor, 3)
LmtdProdsWithdrawalPremium   = round(FinalRate x ProdsCompldOpsCovExposure [/1000], 0)
```

`FinalILF` has **no arithmetic floor** in the rate formula itself — the only thing preventing a negative rate is a validation guard (`DoMessageProdWithdrawalDedFactorCannotExceedPWILF`), not the arithmetic. This is escalation **N15**: the only negative-premium guard the gate's author found anywhere in the GL corpus. (GATE-365 §9.2, §9.4, N15.)

The `/1000` divide is decided by the same nine-value premium-basis list used by Size-Of-Risk (Admissions, Area, Gallons, Gross Sales, Passenger Days, Payroll, Total Cost, Total Operating Expenses, Vehicles) — third appearance of that filed list in the corpus per the gate. (GATE-365 §9.2, item 1.)

---

## Limited Product Withdrawal Expense — premium

`…LimitedProductWithdrawalExpenseCoverage` (7 rules)

```
Premium (coverage) =
    LimitedProductWithdrawalClassPremium
  x ProductWithdrawalParticipationPercentage
  x PackageModFactor
  - PremiumDiscountCharge
  | or ManualPremium
```

`ProductWithdrawalParticipationPercentage` is a new submission input applied at the coverage level after class premiums are rolled up. (GATE-365 §9.2, item 3.)

### Gate — coverage attachment
`DoMessageLimitedProductWithdrawalEndt` (group `GeneralLiability`) enforces: *"A classification that does not include Products coverage to the premises must be selected to attach the Limited Product Withdrawal Endorsement."* Also gated on `ProdsWithdrawalCoverage == "Yes"`, the policy-level `GeneralLiabilityLimitedProductWithdrawalExpenseEndtPolLvl` row existing, and the risk having a Prod/CompOps coverage. (GATE-365 §6a, §9.4.)

### Guards (4 total — one is the corpus's only negative-premium check)

| Guard | Group | What it enforces |
|---|---|---|
| `DoMessageLimitedProductWithdrawalEndt` | `GeneralLiability` | Products coverage must be selected to attach the endorsement |
| `DoMessageMustEnterLimitedProductWithdrawalDeductibleFactorOverride` | `GeneralLiabilityClassification` | override required when the filed factor is absent |
| `DoMessageProdWithdrawalDedFactorCannotExceedPWILF` | `GeneralLiabilityClassification` | deductible factor cannot exceed the increased limits factor, i.e. `FinalILF >= 0` |
| `DoMessageTheLimitedProductWithdrawalCoveragepremiumCannotBeANegativePremium` | `GeneralLiabilityClassification` | premium may not go negative |

(GATE-365 §9.4.)

### Policy-level and minimum-premium roll-up
`…LimitedProductWithdrawalExpenseEndtPolLvl` (24 rules — limits, deductible, class-premium roll-up, minimum premium) and `…LimitedProductWithdrawalExpenseEndtPremiumToReachMinCoveragePolLvl` (8 rules — the minimum-premium iteration). Not resolved in source docs — the gate names these groups and their role but does not give their internal rule-by-rule formulas.

---

## Loss Of Electronic Data (CG 04 37 / CG 04 71) — rate build-up

Two matched groups (Prem/Ops host, Prod/CompOps host), 25 rules each, step-for-step identical apart from limit setup and the factor lookup (GATE-365 §2, table):

```
SetLossOfElectronicDataLimit
SetILF -> SetDeductibleFactor -> SetFinalILF
SetAdjustedBaseRate
SetHazardGrade
SetLossOfElectronicDataFactor
SetFinalRate -> SetPremium -> SetPremiumIndicator
```

### Step 1 — Limit
`SetLossOfElectronicDataLimit` — LoED carries a single limit (unlike Cyber's occurrence + aggregate pair). ILF is selected at "the Each Occurrence Limit equal to the Loss Of Electronic Data Limit indicated in the Schedule." (GATE-365 §2; 03-SUBLINE-COVERAGE-PLAN.md §3.2.7.)

### Step 2 — ILF and deductible
`SetILF -> SetDeductibleFactor -> SetFinalILF` — same shape as Product Withdrawal's ILF steps; the gate does not give the specific lookup table names for this step beyond the factor tables listed under "Supporting lookups" below.

### Step 3 — Adjusted base rate (reads the host's computed values)
`SetAdjustedBaseRate` (Prem/Ops-hosted group), reading directly into the sibling Prem/Ops coverage group:

```
../GeneralLiabilityClassificationPremOpsCoverage/PremOpsLossCost
../GeneralLiabilityClassificationPremOpsCoverage/PremOpsELP
../GeneralLiabilityClassificationPremOpsCoverage/LCM
../GeneralLiabilityClassificationPremOpsCoverage/ClaimsMadeMultiplier
../GeneralLiabilityClassificationPremOpsCoverage/PremOpsSizeOfRiskFinalRelativity
```

```
AdjustedBaseRate =
    (host loss cost | host ELP)
  x host LCM
  [x host ClaimsMadeMultiplier]
  x host SizeOfRiskFinalRelativity
  x own FinalILF
```

Four branches on `SizeOfRiskRatingApplies` and `PremOpsProdsCoverageForm == "Claims Made"`. This is the architectural finding of the gate (**E18**): LoED reads a sibling's *computed* values, not just its tables, so the two coverage groups cannot be evaluated independently — a data dependency, not a scheduling preference. The Prod/CompOps-hosted LoED group is "identical shape" per the gate's table, reading `GeneralLiabilityClassificationProdsCompldOpsCoverage/...` instead. (GATE-365 §2.)

A host's edition-scoped behavior propagates silently: LoED inherits Prem/Ops's (334's) two-calculator Claims-Made split without expressing it itself. (GATE-365 §2, item 3.)

### Step 4 — Hazard grade
`SetHazardGrade` — looks up a **per-class-code, countrywide-published** hazard grade. `LossOfElectronicDataPremOpsHazardGrade` carries **1,188 rows** (CW 2023/2026 edition) / **1,163 rows** (CW 2027 edition) — the largest countrywide rate tables in the corpus. New York overrides this table (1,190/1,191 rows) and is the only jurisdiction that does. (GATE-365 §2, "The hazard-grade tables are the largest...")

### Step 5 — Coverage factor
`SetLossOfElectronicDataFactor` = lookup against one of `LossOfElectronicData{PremOps,ProdsCompldOps}Factor{CG0437,CG0471}` — four factor tables per coverage, all countrywide, 4 rows each, **keyed by endorsement form number**, so the attached endorsement (CG 04 37 vs CG 04 71) selects which factor table applies. (GATE-365 §2.)

### Step 6 — Final rate, premium, indicator
`SetFinalRate -> SetPremium -> SetPremiumIndicator` — "identical" in shape to Cyber's equivalent steps per the gate's table; the gate does not give the exact final-rate/premium formula for LoED beyond the shared skeleton shown for Product Withdrawal (Base x factors, then premium x exposure / basis). Not resolved in source docs — the gate documents the chain's rule names and the AdjustedBaseRate/HazardGrade steps in formula detail, but not the literal `SetFinalRate`/`SetPremium` arithmetic for LoED/Cyber (unlike Product Withdrawal, where §1 gives it explicitly).

---

## Cyber Incident Liability — rate build-up

Two matched groups (Prem/Ops host, Prod/CompOps host), 23 rules each — same skeleton as LoED, zero shared rule bodies (GATE-365 §2, table):

```
SetEachCyberIncidentOccurrenceLimit
SetCyberIncidentAggregateLimit
SetILF -> SetDeductibleFactor -> SetFinalILF          # identical to LoED
SetAdjustedBaseRate                                    # identical shape to LoED
SetHazardGrade                                         # identical shape to LoED
SetCyberIncidentLiabilityFactor
SetFinalRate -> SetPremium -> SetPremiumIndicator      # identical to LoED
```

### Step 1 — Limits
Cyber carries **two** limit rules — an occurrence limit and an aggregate limit — where LoED carries one; this is the chain's only structural difference from LoED, and it accounts for Cyber's 23 rules vs. LoED's 25 only in the sense that the gate calls out no other content delta besides the factor lookup and hazard-grade table names. (GATE-365 §2.)

### Steps 2–4 — ILF, adjusted base rate, hazard grade
Identical shape to LoED steps 2–4 above, substituting `CyberIncidentLiabilityPremOpsHazardGrade` (1,188 / 1,163 rows, NY override to 1,191) for the LoED hazard-grade table. (GATE-365 §2.)

### Step 5 — Coverage factor
`SetCyberIncidentLiabilityFactor` — reads `CyberIncidentLiability…Factors` and `TypeOfPolicyWithCyberIncidentLiabCoverage`, both countrywide, "follow the same shape" (4 rows) as the LoED CG0437/CG0471 factor tables. (GATE-365 §2.)

### Step 6 — Final rate, premium, indicator
Identical to LoED. Not resolved in source docs — same gap as LoED: the literal final-rate/premium arithmetic is not given, only that the step names and shape are identical to LoED's.

---

## Loss Of Electronic Data / Cyber Incident Liability — premium

No branch structure (scheduled/blanket/Legal-Liability) is documented for these coverages, unlike CF's Building forms. `SetPremiumIndicator` follows `SetPremium` in both chains (shape only given, not formula). Not applicable to this subline in the CF sense of multiple premium branches — the source describes a single linear chain per host per coverage.

### Gate — coverage on policy (California withdraws both coverages)
`SetCoverageOnPolicyIndicator` is stubbed to a constant **`0`** in all six LoED/Cyber-related groups (both classification groups per coverage, plus each `PremiumToReachMinCoverage` iterator) in `GL_CA_20241101_V01`. The rating chain never runs in California, so 13 tables emptied to zero rows in that state package are never reached — this is documented as deliberate ("N3's neutralising-stub idiom"), not a defect. (GATE-365 §10.)

| Coverage | Tables emptied in CA |
|---|---|
| Cyber Incident Liability | `CyberCoverageLimitStatCode`, `CyberIncidentLiabilityMinPremium`, `…PremOpsFactors`, `…PremOpsHazardGrade`, `…ProdsCompldOpsFactors`, `…ProdsCompldOpsHazardGrade`, `TypeOfPolicyWithCyberIncidentLiabCoverage` |
| Loss Of Electronic Data | `LossOfElectronicDataMinPremium`, `…PremOpsFactorCG0437`, `…PremOpsFactorCG0471`, `…PremOpsHazardGrade`, `…ProdsCompldOpsFactorCG0437`, `…ProdsCompldOpsFactorCG0471`, `…ProdsCompldOpsHazardGrade` |

California also stubs `SetSizeOfRiskRatingApplies` to `"No"` — consistent, since Size-Of-Risk is exactly what LoED and Cyber read across the group boundary (E18); a state withdrawing both coverages has no reason to keep the input they need. (GATE-365 §10.)

---

## Comparison — the six rate-driven groups plus Limited Product Withdrawal

| | Product Withdrawal Coverage A | Product Withdrawal Coverage B | Limited Product Withdrawal | LoED (x2 hosts) | Cyber (x2 hosts) |
|---|---|---|---|---|---|
| Own subline | 365 | 365 | none — endorsement CG 04 36 on 336 | none — endorsement CG 04 37/71 | none |
| Rules | 27 | 27 | 11 (+ 43 across 4 more groups) | 25 each | 23 each |
| Host | Prod/CompOps (336) | Prod/CompOps (336) | Prod/CompOps (336) | Prem/Ops (334) or Prod/CompOps (336) | Prem/Ops (334) or Prod/CompOps (336) |
| Reads host's computed values (E18) | via LCM/ELP/loss-cost lookups on host tables | same | yes — `ProdsCompldOpsLossCost` directly | yes — 5 sibling DataDefs incl. Size-Of-Risk | yes — same shape as LoED |
| Rating basis selector | borrowed from host (`ProdsCompldOpsELPText`) | borrowed from host | n/a (uses host loss cost/ELP directly) | n/a | n/a |
| Factor table | `ProductWithdrawalExpensesFactor` (A 0.25/B 0.19/C 0.13) | `ProductWithdrawalLiabilityFactor` (A 0.13/B 0.10/C 0.07) | `ProductWithdrawlFactor` **misspelled** (A 0.20/B 0.15/C 0.10) | 4 CG-form-keyed tables, 4 rows each | hazard-grade + type-of-policy tables |
| Limits | n/a in the given chain | n/a | aggregate + deductible (endorsement row) | one limit | occurrence + aggregate (2 limits) |
| Negative-premium guard | not documented | not documented | yes — the only one in the corpus (N15) | not documented | not documented |
| Manual anchor | Rule 44.B.3.a.(5) / 44.B.3.b, p.93 | Rule 44.B.3.a.(5) / 44.B.3.b, p.93 | Rule 44.B.3.a.(5) / 44.B.3.b, p.93 (same factor table family) | not in Rule 44-49; endorsement-driven, form-keyed | not in Rule 44-49; endorsement-driven, form-keyed |
| California | not documented as withdrawn | not documented as withdrawn | not documented as withdrawn | withdrawn (stubbed to 0) | withdrawn (stubbed to 0) |
| State deviation | 17 rules / 9 jurisdictions (whole gate total) | (included above) | 1 of 51 (Texas — `InitializeRuleSet` + 2 stat-code lookups); 0 of 51 on the 11 rating rules | (included in whole-gate total) | (included in whole-gate total) |

---

## Supporting lookups

| Table | Key | Values (A/B/C or CW) | Reader | Source |
|---|---|---|---|---|
| `ProductWithdrawalExpensesFactor` | `FinalProductWithdrawalIncrdLimitTableAssignment` | 0.25 / 0.19 / 0.13 | Coverage A `SetProductWithdrawalExpenseFactor` | GATE-365 §1 |
| `ProductWithdrawalLiabilityFactor` | `FinalProductWithdrawalIncrdLimitTableAssignment` | 0.13 / 0.10 / 0.07 | Coverage B equivalent | GATE-365 §1 |
| `ProductWithdrawlFactor` **(misspelled)** | `IncreasedLimitsTableAssignmentProdsCompldOpsFinal` / `FinalProdsCompldOpsIncrdLimitTableAssignment` | 0.20 / 0.15 / 0.10 | `SetLmtdProductWithdrawlFactor` (Limited Product Withdrawal) | GATE-365 §1, §9.2, §9.3 |
| `ProductWithdrawalLCM` | — | CW: 1 row = 1 | `SetLCM` | GATE-365 §1, §3 (E15) |
| `ProductWithdrawalMinPremium` | — | CW: 1 row = 0; empty in CW 2027 | not traced in gate | GATE-365 §3 (E16) |
| `ProductWithdrawalExpensesAndLiabilityIncrdLimitFactor` | — | CW: 0 rows; state: 51/51, 36 rows each | `SetCFLILF`, `SetLmtdProdsWithdrawalIncreasedLimitsFactor` | GATE-365 §1, §3, §9.2, §9.5 |
| `LookupProdsCompldOpsLossCost` (host table) | `ProdsCompldOpsTerritory` | — | `SetLossCosts` (365), `SetLmtdProdsWithdrawalBaseRate` | GATE-365 §1, §9.2 |
| `LookupProdsCompldOpsELPFactor` (host table) | — | — | `SetELP` | GATE-365 §1 |
| `LookupProdsCompldOpsELPText` (host table) | — | — | `SetProductWithdrawalELP` | GATE-365 §1 |
| `LookupDedFactorProdsCSL` (host table) | — | — | `SetDeductibleFactor` (365), `SetLmtdDeductibleFactor` | GATE-365 §1, §9.2 |
| `LossOfElectronicDataPremOpsHazardGrade` | class code | 1,188 rows (CW 2023/26) / 1,163 (CW 2027); NY 1,190/1,191 | `SetHazardGrade` (LoED) | GATE-365 §2 |
| `CyberIncidentLiabilityPremOpsHazardGrade` | class code | 1,188 rows (CW 2023/26) / 1,163 (CW 2027); NY 1,191 | `SetHazardGrade` (Cyber) | GATE-365 §2 |
| `LossOfElectronicData{PremOps,ProdsCompldOps}Factor{CG0437,CG0471}` | endorsement form number | CW, 4 rows each | `SetLossOfElectronicDataFactor` | GATE-365 §2 |
| `CyberIncidentLiability…Factors` | endorsement form number (by analogy) | CW, 4 rows | `SetCyberIncidentLiabilityFactor` | GATE-365 §2 |
| `TypeOfPolicyWithCyberIncidentLiabCoverage` | — | CW, similar 4-row shape | Cyber chain | GATE-365 §2 |
| `LossOfElectronicDataMinPremium` | — | CW: 1 row | not traced | GATE-365 §3 |
| `CyberIncidentLiabilityMinPremium` | — | CW: 1 row | not traced | GATE-365 §3 |
| `SublineProductWithdrawal` | — | 0 rows, 0 readers, every edition — orphan table | none | GATE-365 §1, §5 |

Every lookup in this ruleset that the gate traces follows GL's usual pattern of a state-or-CW keyed table; the gate does not restate the CF "two-pass `FirstNonNull`" mechanism explicitly for GL, so it is not asserted here. Not resolved in source docs — whether GL's lookup mechanism is the identical two-pass state-then-CW fallback CF uses.

---

## Quick reference — end-to-end, Product Withdrawal Coverage A

```
ProductWithdrawalExpenseFactor = lookup(FinalProductWithdrawalIncrdLimitTableAssignment)   [CW A 0.25/B 0.19/C 0.13]
LCM                             = lookup ProductWithdrawalLCM(...)                          [CW = 1]
ELP                             = lookup ProdsCompldOpsELPFactor(...)   if host selector != "Company"
                                 | override, else 0.0
FinalILF                        = combine(CFLILF via ProductWithdrawalExpensesAndLiabilityIncrdLimitFactor,
                                           DeductibleFactor via LookupDedFactorProdsCSL)
LossCost                        = lookup ProdsCompldOpsLossCost(ProdsCompldOpsTerritory)    [0.0 if class/territory empty]

BaseRate  = round(ELP x ProductWithdrawalExpenseFactor x LCM, 3)
          | round(LossCost x ProductWithdrawalExpenseFactor x LCM, 3)

FinalRate = round(BaseRate x FinalILF x PackageModFactor x ExperienceRatingModificationFactor
                  x ExpenseModification x ModToUse x PremiumDiscountCharge, 3)

Premium   = round(FinalRate x exposure / 1000, 0)     [/1000 bases]
          | FinalRate x exposure                       [otherwise]
```

Coverage B: identical, substituting `ProductWithdrawalLiabilityFactor` [CW A 0.13/B 0.10/C 0.07] for `ProductWithdrawalExpenseFactor`.

## Quick reference — end-to-end, Limited Product Withdrawal Expense

```
LmtdLCM              = branch on ProdsWithdrawalCoverage / ProdsCompldOpsCov
LmtdProductWithdrawalFactor = lookup ProductWithdrawlFactor(FinalProdsCompldOpsIncrdLimitTableAssignment)
                                                          [CW A 0.20/B 0.15/C 0.10 -- MISSPELLED table]

LmtdBaseRate = (ProdsCompldOpsLossCost | FinalProdsCompldOpsELP)     # SIBLING group's computed value
             x LmtdLCM x LmtdProductWithdrawalFactor

LmtdIncreasedLimitsFactor = lookup ProductWithdrawalExpensesAndLiabilityIncrdLimitFactor(
                                 FinalProdsCompldOpsIncrdLimitTableAssignment, AggregateLimit)
LmtdCSLILF                = LmtdIncreasedLimitsFactor
LmtdDeductibleFactorForRating = lookup DedFactorProdsCSL(...) or Override

LmtdFinalILF   = CSLILF - DeductibleFactorForRating         [no arithmetic floor -- guarded by validation, N15]
LmtdFinalRate  = round(BaseRate x FinalILF x PackageModFactor, 3)
LmtdPremium    = round(FinalRate x ProdsCompldOpsCovExposure [/1000], 0)

CoveragePremium = LimitedProductWithdrawalClassPremium x ProductWithdrawalParticipationPercentage
                  x PackageModFactor - PremiumDiscountCharge
                | ManualPremium
```

## Quick reference — end-to-end, Loss Of Electronic Data (or Cyber, same shape)

```
Limit(s)      = LossOfElectronicDataLimit                                          [LoED: 1 limit]
              | EachCyberIncidentOccurrenceLimit + CyberIncidentAggregateLimit     [Cyber: 2 limits]

ILF -> DeductibleFactor -> FinalILF     [not resolved in source docs -- exact lookup tables not named]

AdjustedBaseRate =
    (host LossCost | host ELP)                          # from sibling PremOps or ProdsCompldOps group
  x host LCM
  [x host ClaimsMadeMultiplier]                          # Prem/Ops host only
  x host SizeOfRiskFinalRelativity
  x own FinalILF

HazardGrade   = lookup {LossOfElectronicData|CyberIncidentLiability}PremOpsHazardGrade(ClassCode)
                                                          [1,188/1,163 rows CW; NY overrides]

CoverageFactor = lookup {LossOfElectronicData{PremOps,ProdsCompldOps}Factor{CG0437,CG0471}
                        | CyberIncidentLiability...Factors}(endorsement form number)

FinalRate, Premium, PremiumIndicator = not resolved in source docs -- gate gives rule names
                                        and "identical" shape only, not the literal formula

Gate: SetCoverageOnPolicyIndicator = 0 in California for all 6 LoED/Cyber groups -- chain never runs
```

---
