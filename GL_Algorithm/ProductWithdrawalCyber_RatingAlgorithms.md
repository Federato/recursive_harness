# Product Withdrawal / Loss Of Electronic Data / Cyber Incident Liability — Rating Algorithms

**Source:** `C:\Projects\Recursive_Harness_2.0\docs\gates\GATE-365-WITHDRAWAL-LOED-CYBER.md` (as-of date 2026-08-11, addenda through 2026-08-12), derived against **`GL_CW_20231201_V03`**.
**Line:** General Liability (GL), Countrywide, build-order item 6.
**Documented (this port):** 2026-08-20.
**Reformatted from:** the gate doc above, into the CF `RatingAlgorithms` template. The 2026-08-20 port was a reformat of the gate; on 2026-10-02 every formula below was re-derived from ERC XML and reproduced by offline engine runs, and steps that differed from the gate were corrected in place (each correction is marked *Reconciled*). GATE-365 section citations are kept where the gate's statement still holds.
**Reconciled against the built engine:** 2026-10-02 (commit `630ba2f`) — offline `Kernel().rate` runs with Product Withdrawal (a second GL risk, Subline "Product Withdrawal", coverage type "Both Expense and Liability"), Limited Product Withdrawal (CG 04 36 policy-level record), CG 04 37 and CG 04 95 records added to the engine base submission, at TX@20270401 (`GL_TX_20270401_V01` over CW 20270401 V01), IL@20270401 (`GL_IL_20270401_V05` over CW 20270401 V02), TX@20261002 (`GL_TX_20250801_V01` over CW 20231201 V03), IL@20261002 (`GL_IL_20260901_V01` over CW 20260101 V01) and CA (both dates); plus rule-level XML diffs across CW 20231201 V03 / 20260101 V01 / 20261001 V01 / 20270401 V01 / V02.
**Edition scope (A3 -- the effective date is a variable; `package_version` pins one):** as of 2026-10-02 most states rate on CW 20260101 V01 (TX/NJ/VT on 20231201 V03, OK on 20261001 V01, CA on 20231201 V02); at 2027-04-01, 38 states incl. IL rate on CW 20270401 V02 and 8 incl. TX on V01. The CW 2023/2026/20261001 rule bodies for every group in this document are identical; CW 2027 V01 is where the Product Withdrawal deductible, minimum-premium and premium rules change (see "Edition differences"). **CW 20270401 V02 differs from V01 in three files of this document's scope** -- both Cyber limit-schedule files (`DoMessageCyberIncidentAggregateLimit`) and `GeneralLiabilityProductWithdrawalCoverageFormRules` (`SetLimitsIdentifierStatCode`, `SetRiskIDStatCode`) -- all guards/stat codes, no premium effect.

This gate covers **three unrelated coverages that share a rule-name skeleton and no implementation**:

- **Product Withdrawal (subline 365)** — Coverage A (Product Withdrawal Expense) and Coverage B (Products Withdrawal Liability), rated separately, each a factor applied to a Products/Completed Operations (Prod/CompOps, subline 336) *rate looked up for the class* -- on its own GL risk whose `Subline` is "Product Withdrawal".
- **Limited Product Withdrawal Expense (endorsement CG 04 36)** — a distinct, narrower coverage living inside the shared `GeneralLiabilityClassification` container rather than its own coverage group; also a factor-on-Prod/CompOps-host coverage.
- **Loss Of Electronic Data (LoED, endorsements CG 04 37 / CG 04 71 / CG 04 95)** and **Cyber Incident Liability** — present from edition **CW 20231201** onward (*Reconciled:* not new in CW 2027), each rated twice (once hosted on Premises/Operations, once on Prod/CompOps), reading their host's *computed* intermediate values, not just its tables. **LoED's authoritative trace is [[LossOfElectronicData_RatingAlgorithms.md]]**; the LoED section below is a summary kept consistent with it.

Per the gate: pairwise rule-body overlap across the six rate-driven groups is **zero identical bodies**, despite 12–25 rules of name overlap per pair. They are documented together because the *questions* are shared (host dependency, factor-on-host, state deviation), not the code.

---

## Master orchestration

The classification-level groups are dispatched by `GeneralLiabilityClassificationRules` (`InitializeRuleSet` auto-vivifies one record per group per classification; `ErcProcess` runs each group's `ErcProcess`); the policy-level groups by `GeneralLiabilityRules`. Each group's `ErcProcess` runs its chain only when its `SetCoverageOnPolicyIndicator` wrote 1, otherwise writes `Premium = 0.0`. Engine-observed order within one classification (TX@20270401 / IL@20270401 traces):

```
GeneralLiabilityClassificationRules (pre-rating, per classification)
    SetLimitedProductWithdrawalAggregateAndDeductibleLimits      (CG 04 36 limits copied down)
    SetProductWithdrawalExpensesAndLiabilityIncrdLimitTableAssignment
    SetFinalProductWithdrawalIncrdLimitTableAssignment           ('B' for class 50017)
    SetProductWithdrawalELP                                      ('Industry' for class 50017)
    SetLmtdProdsWithdrawalIncreasedLimitsFactor
Prem/Ops (334) and Prod/CompOps (336) coverage groups rate
    -> PremOpsLossCost/ELP, LCM, ClaimsMadeMultiplier, Size-Of-Risk relativity,
       ProdsCompldOps BaseRate, DeductibleFactor, ... resolved
GeneralLiabilityClassificationRules.ErcRate
    Limited Product Withdrawal Expense rating chain (11 rules, reads the Prod/CompOps group)
then, in this order:
    Cyber Incident Liability, Prem/Ops host      (23 rules)
    Cyber Incident Liability, Prod/CompOps host  (23 rules)
    Product Withdrawal Coverage A  (…ExclusionCoverageAProductWithdrawalExpenseRules, 27 rules)
    Product Withdrawal Coverage B  (…ExclusionCoverageBProductWithdrawalLiabilityRules, 27 rules)
    Loss Of Electronic Data, Prem/Ops host       (25 rules)
    Loss Of Electronic Data, Prod/CompOps host   (25 rules)
policy level (GeneralLiabilityRules):
    Limited Product Withdrawal Expense policy-level  (…EndtPolLvl, 24 rules)
    Limited Product Withdrawal Expense coverage premium (…Coverage, 7 rules)
    Limited Product Withdrawal Expense min-premium iterator (…PremiumToReachMinCoveragePolLvl, 8 rules)
    Product Withdrawal coverage form (…ProductWithdrawalCoverageFormRules; stat codes, + pre-2027 min premium)
    LoED / Cyber / Product Withdrawal PremiumToReachMin toppers
```

The LoED/Cyber groups and the Limited Product Withdrawal chain read a **sibling coverage group's already-computed values** (`../GeneralLiabilityClassificationPremOpsCoverage/...` or the Prod/CompOps equivalent) rather than re-deriving them — escalation **E18** in the gate. *Reconciled:* Product Withdrawal Coverage A/B do **not** read computed host values; they look up the Prod/CompOps loss-cost and ELP **tables** themselves, on a risk whose Subline is "Product Withdrawal". (GATE-365 §2, §9.2, Findings.)

`SetCoverageOnPolicyIndicator` gates each group (e.g. stubbed to a constant `0` in all six California LoED/Cyber groups to withdraw the coverages entirely — GATE-365 §10; engine-confirmed, CA@20261002 and CA@20270401). No premium is computed for a withdrawn coverage; empty state tables are never reached because the gate short-circuits first.

---

## File map

| Piece | Group / rule set | Rules | Source citation |
|---|---|---|---|
| Product Withdrawal Coverage A rate build-up | `GeneralLiabilityClassificationExclusionCoverageAProductWithdrawalExpenseRules` | 27 | GATE-365 §1; XML |
| Product Withdrawal Coverage B rate build-up | `GeneralLiabilityClassificationExclusionCoverageBProductWithdrawalLiabilityRules` | 27 | GATE-365 §1; XML |
| Product Withdrawal coverage form (policy level) | `GeneralLiabilityProductWithdrawalCoverageFormRules` | 20 (CW 2027) / 30 (pre-2027) | XML |
| Product Withdrawal minimum-premium topper | `GeneralLiabilityProductWithdrawalPremiumToReachMinCoverageRules` | 4 (CW 2027) / 9 (pre-2027) | XML |
| Limited Product Withdrawal Expense — rating chain | `GeneralLiabilityClassification` (shared container — not its own coverage group) | 11 (pre-2027; 10 in CW 2027, `SetHighestLmtdProdsWithdrawalFinalILFFlag` removed) | GATE-365 §6a, §9.1 |
| Limited Product Withdrawal Expense — guards | `GeneralLiability` + `GeneralLiabilityClassification` + `…EndtPolLvl` | see Guards | GATE-365 §9.1, §9.4 |
| Limited Product Withdrawal Expense — policy level (limits, deductible, class-premium roll-up, minimum premium) | `…LimitedProductWithdrawalExpenseEndtPolLvl` | 24 | GATE-365 §9.1 |
| Limited Product Withdrawal Expense — coverage premium | `…LimitedProductWithdrawalExpenseCoverage` | 7 | GATE-365 §9.1 |
| Limited Product Withdrawal Expense — premium-to-reach-minimum iterator | `…LimitedProductWithdrawalExpenseEndtPremiumToReachMinCoveragePolLvl` | 8 | GATE-365 §9.1 |
| Loss Of Electronic Data — Prem/Ops host | `GeneralLiabilityClassificationLossOfElectronicDataPremOpsCoverageRules` | 25 | XML; see the LoED doc |
| Loss Of Electronic Data — Prod/CompOps host | `GeneralLiabilityClassificationLossOfElectronicDataProdsCompldOpsCoverageRules` | 25 | XML; see the LoED doc |
| Cyber Incident Liability — Prem/Ops host | `GeneralLiabilityClassificationCyberIncidentLiabilityPremOpsCoverageRules` | 23 | XML |
| Cyber Incident Liability — Prod/CompOps host | `GeneralLiabilityClassificationCyberIncidentLiabilityProdsCompldOpsCoverageRules` | 23 | XML |
| Cyber / LoED limit schedules (policy-level input records) | `GeneralLiabilityCyberIncidentLiabilityCovSubjectToEachCyberIncidentOccurrenceAndAggregateLimits` (Cyber), `…CyberIncidentLiabCovLossOfEDLCovSubjectToLossOfElectronicDataCyberIncidentOccAggLimits` (CG 04 95), `…CyberIncidentLiabCovSubjectToEachCyberIncidentOccAggLimitsOwnrsContrctrsProds` (Prod/CompOps host only) | — | XML |
| Host loss-cost / ELP / LCM (Prod/CompOps) | `GeneralLiabilityClassificationProdsCompldOpsCoverage` | — | GATE-365 §1, §9.2 |
| Host loss-cost / ELP / LCM / Size-Of-Risk (Prem/Ops) | `GeneralLiabilityClassificationPremOpsCoverage` | — | GATE-365 §2 |

> Note: rule-file names are now the actual ERC file stems (all under `…\countrywide\<edition>\Rules\`); line-level detail for LoED lives in the LoED doc.

---

## Product Withdrawal (365) Coverage A — Product Withdrawal Expense — rate build-up

Gate: `SetCoverageOnPolicyIndicator` = 1 iff the risk's `Subline == "Product Withdrawal"` and `ProductWithdrawalCoverageType` is "Expense" or "Both Expense and Liability". Chain, from `ErcSetRatesAndFactors` / `ErcRate` of `GeneralLiabilityClassificationExclusionCoverageAProductWithdrawalExpenseRules`:

```
SetProductWithdrawalExpenseFactor
SetLCM
SetELP
SetCFLILF / SetDeductibleFactor / SetFinalILF
SetLossCosts
SetBaseRate
SetPremiumDiscountCharge
SetFinalRate
SetPremium -> SetPremiumIndicator
(stat codes: SetLCMStatCode, SetExposureStatCode)
```

Every rating rule is guarded on a non-blank `ClassCode`; with none, each value is 0.0.

### Step 1 — Product Withdrawal Expense factor
`SetProductWithdrawalExpenseFactor`

```
ProductWithdrawlExpenseFactor = LookupProductWithdrawalExpensesFactor(
    FinalProductWithdrawalIncrdLimitTableAssignment)      # state, then CW
```

Reads matrix `ProductWithdrawalExpensesFactor` (correctly spelled) — 3 rows, A 0.25 / B 0.19 / C 0.13; the field it writes is the misspelled `ProductWithdrawlExpenseFactor`. The table assignment comes from the classification rules (`SetProductWithdrawalExpensesAndLiabilityIncrdLimitTableAssignment` -> `SetFinalProductWithdrawalIncrdLimitTableAssignment`). Engine: `['CW','B'] -> 0.19`.

### Step 2 — LCM
`SetLCM`

```
LCM = LookupProductWithdrawalLCM('Y')       # ProductWithdrawalLCM, keyed (StateCode, constant 'Y')
```

Countrywide, one row, value **1**. (GATE-365 §1, item 2; §3, E15.)

### Step 3 — ELP (borrows the host's rating-basis selector)
`SetELP`

```
if ../ProductWithdrawalELP is set and != "Company":
    ELP = LookupProdsCompldOpsELPFactor(StateCode, ClassCode)     # Prod/CompOps's own ELP table
else:
    ELP = ../ProductWithdrawalELPOverride, else 0.0
```

`ProductWithdrawalELP` itself is populated by `SetProductWithdrawalELP` in the classification rules, which calls `LookupProdsCompldOpsELPText` — there is no Product-Withdrawal-specific rating-basis selector table; Product Withdrawal borrows its host's. Engine: `ProdsCompldOpsELPFactor ['TX','50017'] -> 0.82`. The shared guard `DoMessageMustEnterEstimatedLossPotentialFactorOverride` reads `ProductWithdrawalELP`/`ProductWithdrawalELPOverride`, so a "Company" class with no override raises the same *"Must enter Estimated Loss Potential Override"* message the referral register's **R29** keys on in `underwriting` mode (structural; not separately run).

### Step 4 — Increased limits and deductible
`SetCFLILF` / `SetDeductibleFactor` / `SetFinalILF` — *Reconciled* (the gate did not give the combining formula):

```
CSLILF           = LookupProductWithdrawalExpensesAndLiabilityIncrdLimitFactor(
                       FinalProductWithdrawalIncrdLimitTableAssignment, ProductsWithdrawalAggregateLimit)
                   # state-filed only (0 CW rows); 0.0 if class/assignment/limit blank
DeductibleFactor = CW 2027:      LookupDedFactorProdsProdWithdrawl(assignment, ProductWithdrawalDeductible)
                                 # new 48-row table, deductible keys "No Deductible", "250" ... "1,000" ...
                   pre-2027:     ProductWithdrawalDeductibleFactorOverride if non-zero, else
                                 LookupDedFactorProdsCSL(assignment, ProductWithdrawalDeductible)
                                 # Prod/CompOps's table, keys "1,000 Per Occurrence" etc.
                   0.0 if assignment or deductible blank
FinalILF         = round(CSLILF - DeductibleFactor, 3)       # no floor (unlike LoED/Cyber)
```

Engine: TX@20270401 `CSLILF ['TX','B','1,000,000'] -> 1.65`, `DedFactorProdsProdWithdrawl ['CW','B','1,000'] -> 0.015`, `FinalILF 1.635`; IL (2026 and 2027) `CSLILF 1.73`, `FinalILF 1.715`. **Edition trap:** a 2027-style deductible value (`"1,000"`) on a pre-2027 edition misses `DedFactorProdsCSL`, the factor is null, and the engine stops the rating INCOMPLETE at `SetFinalILF`'s subtraction (TX@20261002, IL@20261002 reproduced); the pre-2027 key is `"1,000 Per Occurrence"`.

### Step 5 — Loss costs
`SetLossCosts`

```
LossCost = LookupProdsCompldOpsLossCost(StateCode, ../../../ProdsCompldOpsTerritory, ClassCode)   # Prod/CompOps's own table
         = 0.0 if class code or territory is empty
```

Engine: `ProdsCompldOpsLossCost ['TX','999','50017'] -> 0` (class 50017 is ELP-rated). (GATE-365 §1, item 5.)

### Step 6 — Base rate
`SetBaseRate`

```
BaseRate = round(ELP      x ProductWithdrawlExpenseFactor x LCM, 3)   if LossCost == 0
         = round(LossCost x ProductWithdrawlExpenseFactor x LCM, 3)   otherwise
```

Product Withdrawal is the first coverage in this gate whose base rate is **a host subline's rate times a factor** ("factor-on-host") — and the only one of the three coverages here carrying both a loss-cost path *and* an ELP path (unlike Liquor and Railroad). Engine: `round(0.82 x 0.19 x 1, 3) = 0.156`. (GATE-365 §1, item 6.)

### Step 7 — Premium discount charge
`SetPremiumDiscountCharge` — *Reconciled* (the gate gave no formula):

```
PremiumDiscountCharge = round(1 - PremiumDiscountPercentage x 0.01, 3)   if the policy's PremiumDiscountPercentage is present
                      = 1.0                                              otherwise
```

The manual's Participation Percentage / Cut-off Date provisions (Rule 44.B.3.b–c) remain a **refer** for the percentage itself (GATE-365 §4, row 3); the ERC simply applies whatever discount percentage is supplied.

### Step 8 — Final rate
`SetFinalRate` (written only if `FinalRate` is still null)

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

Engine: `round(0.156 x 1.635, 3) = 0.255` (TX); `round(0.156 x 1.715, 3) = 0.268` (IL). (GATE-365 §1, item 8 — confirmed.)

### Step 9 — Premium
`SetPremium`

```
CW 2027:   calculated = round(FinalRate x ProductWithdrawalCovExposure / 1000, 0)   # 9 bases: Admissions, Area, Gallons,
                                                                                  # Gross Sales, Kilowatt-hours, Payroll,
                                                                                  # Total Cost, Total Operating Expenses, Vehicles
                      | round(FinalRate x ProductWithdrawalCovExposure, 0)        # otherwise
           Premium    = 1.0 if calculated == 0 and exposure > 0, else calculated   # $1 minimum
pre-2027:  same two products (both rounded to 0 dp), 7 /1000 bases (no Kilowatt-hours, no Vehicles), no $1 minimum
```

Engine (Gross Sales 5,000,000): Coverage A `round(0.255 x 5,000) = 1,275` (TX@20270401 and TX@20261002), `1,340` (IL@20270401 and IL@20261002).

---

## Product Withdrawal (365) Coverage B — Products Withdrawal Liability — rate build-up

**Structurally identical 9-step chain** to Coverage A, from `GeneralLiabilityClassificationExclusionCoverageBProductWithdrawalLiabilityRules` (also 27 rules), gated on `ProductWithdrawalCoverageType` "Liability" or "Both Expense and Liability":

```
ProductWithdrawlLiabilityFactor = LookupProductWithdrawalLiabilityFactor(
    FinalProductWithdrawalIncrdLimitTableAssignment)
```

3 rows, A 0.13 / B 0.10 / C 0.07 — same key axis as Coverage A's factor, different table, different values. (GATE-365 §1, table.) All other steps follow Coverage A's formulas verbatim with the liability factor substituted -- *Reconciled:* confirmed rule-by-rule by engine trace. Engine: TX@20270401 `BaseRate round(0.82 x 0.10, 3) = 0.082`, `FinalRate round(0.082 x 1.635, 3) = 0.134`, `Premium 670`; IL@20270401 `FinalRate 0.141`, `Premium 705`.

---

## Product Withdrawal (365) — premium

Step 9 above **is** the premium step for both coverages A and B; there is no scheduled/blanket/Legal-Liability branching. Above it sit two policy-level groups:

- **`GeneralLiabilityProductWithdrawalCoverageFormRules`.** Pre-2027 it copies `ExpensePremium` / `LiabilityPremium`, `LCM` and `FinalILF` and computes `MinPremium = round(FinalILF x MinimumPremium, 0)` from `ProductWithdrawalMinPremium` (1 row, $0) -> 0 (engine, IL@20261002). **CW 2027 removes all of that** (`SetExpensePremium`, `SetLiabilityPremium`, `SetLCM`, `SetFinalILF`, `SetMinimumPremium`, `SetMinPremium`, the LCM/min-premium lookups); the group only sets stat codes, and `ProductWithdrawalMinPremium` is emptied to 0 rows.
- **`GeneralLiabilityProductWithdrawalPremiumToReachMinCoverage`.** Pre-2027 its gate requires Subline "Product Withdrawal" and an existing coverage-form record; in engine runs (TX@20261002, IL@20261002) the indicator is written during `InitializeRuleSet`, before `AttachFormProductWithdrawalCoverageForm` creates that record, so it stays 0 and the topper never computes. CW 2027 hard-wires the indicator to 0 and drops `ErcRate` -- inert by filing. No premium effect in either edition while the filed minimum is $0.

### Gate — coverage on policy
Each of the six rate-driven groups (the two Product Withdrawal coverages, LoED x2, Cyber x2) is switched by `SetCoverageOnPolicyIndicator`, stubbed to `0` when a jurisdiction withdraws the coverage (documented for California — GATE-365 §10). For 365 the switch is the Subline + `ProductWithdrawalCoverageType` test above.

---

## Limited Product Withdrawal Expense (endorsement CG 04 36) — rate build-up

**Not its own subline** — it is a coverage attached to Prod/CompOps (336) via endorsement, rating inside the shared `GeneralLiabilityClassification` container plus four supporting DataDefGroups. (GATE-365 §6a, §9.1.) Every step is gated on `ProdsWithdrawalCoverage == "Yes"`, the policy-level `GeneralLiabilityLimitedProductWithdrawalExpenseEndtPolLvl` record existing, and (for LCM/ILF) `ProdsCompldOpsCov == "Products/Completed Operations"`.

Executed in this order (engine trace, IL@20270401):

```
SetLimitedProductWithdrawalAggregateAndDeductibleLimits    (pre-rating: copies AggregateLimit / Deductible)
SetLmtdProdsWithdrawalIncreasedLimitsFactor                (pre-rating)
--- GeneralLiabilityClassificationRules.ErcRate ---
SetLmtdProductWithdrawlFactor
SetLmtdLCM
SetLmtdCSLILF
SetLmtdDeductibleFactor
SetLmtdFinalILF
SetHighestLmtdProdsWithdrawalFinalILFFlag                  (pre-2027 only)
SetLmtdProdsWithdrawalBaseRate
SetLmtdProdsWithdrawalFinalRate
SetLmtdProdsWithdrawalPremium
```

### Step 1 — LCM
`SetLmtdLCM` — `LmtdProdsWithdrawalLCM = LookUpProductWithdrawalLCM()` (the same `ProductWithdrawalLCM` table, = 1) when the gates above hold, else 0.0. *Reconciled:* not a value branch on `ProdsWithdrawalCoverage` / `ProdsCompldOpsCov` -- those are on/off gates.

### Step 2 — Product Withdrawal factor (the misspelled table)
`SetLmtdProductWithdrawlFactor`

```
LmtdProdsWithdrawalProductWithdrawalFactor =
    LookupProductWithdrawlFactor(FinalProdsCompldOpsIncrdLimitTableAssignment)
```

Reads matrix `ProductWithdrawlFactor` — the **misspelled** table (see "Supporting lookups" below): 3 rows, A 0.20 / B 0.15 / C 0.10, keyed on `IncreasedLimitsTableAssignmentProdsCompldOpsFinal` / `FinalProdsCompldOpsIncrdLimitTableAssignment`. This resolves an open question the gate itself carried from §1: the misspelled table has two readers, and `SetLmtdProductWithdrawlFactor` is the second one — it serves Limited Product Withdrawal; the correctly-spelled `…ExpensesFactor` / `…LiabilityFactor` tables serve the full (365) coverage. Engine: `['CW','B'] -> 0.15`. (GATE-365 §9.2, §9.3, OI-47.)

### Step 3 — Base rate
`SetLmtdProdsWithdrawalBaseRate`

```
LmtdProdsWithdrawalBaseRate = round(
    (GeneralLiabilityClassificationProdsCompldOpsCoverage/ProdsCompldOpsLossCost   # SIBLING group — E18
       if non-zero, else the classification's FinalProdsCompldOpsELP)
  x LmtdProdsWithdrawalLCM
  x LmtdProdsWithdrawalProductWithdrawalFactor
, 3)
```

Reads `ProdsCompldOpsLossCost` directly from the sibling coverage group — the third instance of E18 in this gate. Engine: `round(0.82 x 1 x 0.15, 3) = 0.123`. (GATE-365 §9.2, item 2 under "Three cross-links worth naming.")

### Step 4 — Limits and deductible
```
LmtdProdsWithdrawalAggregateLimit, …Deductible
    <- the policy-level endorsement record [1] (AggregateLimit, Deductible)

LmtdProdsWithdrawalIncreasedLimitsFactor <-
    LookupProductWithdrawalExpensesAndLiabilityIncrdLimitFactor(
        FinalProdsCompldOpsIncrdLimitTableAssignment, AggregateLimit)       # state-filed

LmtdProdsWithdrawalCSLILF = LmtdProdsWithdrawalIncreasedLimitsFactor

LmtdProdsWithdrawalDeductibleFactorForRating <-
    CW 2027:   LookupDedFactorProdsProdWithdrawl(assignment, Deductible)   # e.g. "1,000"
    pre-2027:  LookupDedFactorProdsCSL(assignment, Deductible)             # e.g. "1,000 Per Occurrence", or the supplied Override
```

Engine, IL@20270401 (`AggregateLimit 100,000`, `Deductible 1,000`): `IncreasedLimitsFactor ['IL','B','100,000'] -> 0.97`, deductible factor `0.015`. (GATE-365 §9.2.)

### Step 5 — Final ILF and rate
```
LmtdProdsWithdrawalFinalILF  = CSLILF - DeductibleFactorForRating          # N15: no arithmetic floor, not rounded
LmtdProdsWithdrawalFinalRate = round(BaseRate x FinalILF x PackageModFactor, 3)
LmtdProdsWithdrawalPremium   = round(FinalRate x ProdsCompldOpsCovExposure [/1000], 0)
```

Engine, IL@20270401: `FinalILF 0.955`, `FinalRate round(0.123 x 0.955, 3) = 0.117`, `Premium round(0.117 x 5,000) = 585`.

`FinalILF` has **no arithmetic floor** in the rate formula itself — the only thing preventing a negative rate is a validation guard (`DoMessageProdWithdrawalDedFactorCannotExceedPWILF`), not the arithmetic. This is escalation **N15**. (GATE-365 §9.2, §9.4, N15.)

The `/1000` divide is decided by a nine-value premium-basis list: CW 2027 — Admissions, Area, Gallons, Gross Sales, Kilowatt-hours, Payroll, Total Cost, Total Operating Expenses, Vehicles; pre-2027 — the same with **Passenger Days** instead of Kilowatt-hours. (GATE-365 §9.2, item 1.)

**Engine limitation, pre-2027 editions:** the policy-level `…EndtPolLvl.SetMinPremium` (CW 20231201 V03 / 20260101 V01 / 20261001 V01) binds `ErcNodeSublineParam` and then reads it from a sibling `Arg` of the same `WithArgs` (inside `Max(ForEach …)`); the engine refuses (*"parameter 'ErcNodeSublineParam' is not bound here"*) and the rating stops INCOMPLETE (IL@20261002 reproduced, after the classification chain had computed 585). CW 2027 removed that rule, so 2027 editions rate end-to-end.

---

## Limited Product Withdrawal Expense — premium

`…LimitedProductWithdrawalExpenseCoverage` (7 rules) — *Reconciled* (the gate's formula multiplied by participation and package mod and subtracted the discount; the ERC does neither):

```
LimitedProductWithdrawalClassPremium = sum over locations x classifications of LmtdProdsWithdrawalPremium   (…EndtPolLvl)

CW 2027:
  calculated = round(ClassPremium x PremiumDiscountCharge, 0)   if ProductWithdrawalParticipationPercentageInt != 0
                                                                   or ProductsWithdrawalCutOffDateApplies == "Yes"
             = round(ClassPremium, 0)                             otherwise
  Premium    = 1.0 if calculated == 0, else calculated

pre-2027:
  Premium = round(ManualPremium x PackageModFactor x PremiumDiscountCharge, 0)
                                 if ProductWithdrawalParticipationPercentage != "0" and ManualPremium != 0
          = round(ClassPremium, 0) if ProductWithdrawalParticipationPercentage == "0" and ClassPremium != 0
          = 0.0                    otherwise
```

`PremiumDiscountCharge` (…EndtPolLvl) = `round(1 - PremiumDiscountPercentage x 0.01, 3)` when supplied, else **1.0 in CW 2027 / 0.0 pre-2027**. Engine, IL@20270401: class premium 585, coverage `Premium 585`. A participation percentage or cut-off date is still a manual **refer** for its value (Rule 44.B.3.b–c); the 2027 `DoMessageParticipationPercentageCheck` guard validates it.

### Gate — coverage attachment
`DoMessageLimitedProductWithdrawalEndt` (group `GeneralLiability`) enforces: *"A classification that does not include Products coverage to the premises must be selected to attach the Limited Product Withdrawal Endorsement."* Also gated on `ProdsWithdrawalCoverage == "Yes"`, the policy-level `GeneralLiabilityLimitedProductWithdrawalExpenseEndtPolLvl` record existing, and the risk having a Prod/CompOps coverage. (GATE-365 §6a, §9.4.)

### Guards — one is the corpus's only negative-premium check

| Guard | Group | Editions | What it enforces |
|---|---|---|---|
| `DoMessageLimitedProductWithdrawalEndt` | `GeneralLiability` | all | Products coverage must be selected to attach the endorsement |
| `DoMessageMustEnterLimitedProductWithdrawalDeductibleFactorOverride` | `GeneralLiabilityClassification` | pre-2027 only | override required when the filed factor is absent |
| `DoMessageMustEnterProductWithdrawalDeductibleFactorOverride`, `DoMessageProductWithdrawalDedFactCannotExceedILF` | `GeneralLiabilityClassification` | pre-2027 only | Product Withdrawal (365) deductible override / cap |
| `DoMessageProdWithdrawalDedFactorCannotExceedPWILF` | `GeneralLiabilityClassification` | all | deductible factor cannot exceed the increased limits factor, i.e. `FinalILF >= 0` |
| `DoMessageTheLimitedProductWithdrawalCoveragepremiumCannotBeANegativePremium` | `GeneralLiabilityClassification` | all | premium may not go negative |
| `DoMessageParticipationPercentageCheck` | `…EndtPolLvl` | CW 2027 only | participation percentage validity |

(GATE-365 §9.4; edition columns from the 2026->2027 rule diff.)

### Policy-level and minimum-premium roll-up
`…LimitedProductWithdrawalExpenseEndtPolLvl` (limits, deductible stat codes, `SetPremiumDiscountCharge`, `SetLimitedProductWithdrawalExpenseMinPremium` from `LimitedProductWithdrawalExpenseMinPremium` = $0, `SetLimitedProductWithdrawalClassPremium`) and `…LimitedProductWithdrawalExpenseEndtPremiumToReachMinCoveragePolLvl` (8 rules — the minimum-premium top-up; engine IL@20270401: `MinPremium 0`, `Premium 0.0`). Pre-2027 `…EndtPolLvl` also carries `SetMinPremium` (`MinPremium x the highest-FinalILF classification's FinalILF`) and `SetPremiumToBeDisplayed` — the rule the engine cannot evaluate (see Step 5).

---

## Loss Of Electronic Data (CG 04 37 / CG 04 71 / CG 04 95) — rate build-up

**Authoritative trace: [[LossOfElectronicData_RatingAlgorithms.md]]** (re-derived from XML and reconciled against the engine 2026-10-02). Summary, kept consistent with it:

```
SetLossOfElectronicDataLimit                       # from the CG 04 37 / CG 04 71 / CG 04 95 schedule record
SetILF -> SetDeductibleFactor -> SetFinalILF       # host ILF table (ILFPremOps / ILFProds), LoED limit as each-occurrence;
                                                   #   13 refer bands -> ILFOverride; host deductible factor copied into DedFactor;
                                                   #   FinalILF = round(ILF - DedFactor, 3), floored at 0
SetAdjustedBaseRate                                # Prem/Ops: round((LossCost | ELP) x LCM [x ClaimsMade] [x SOR] x FinalILF, 4)
                                                   # Prod/CompOps: round(host BaseRate [x SOR] x FinalILF, 4)
SetHazardGrade                                     # LossOfElectronicData{PremOps,ProdsCompldOps}HazardGrade, by ClassCode
SetLossOfElectronicDataFactor                      # Factor{CG0437 (CG 04 37 or CG 04 95), CG0471}, keyed by HazardGrade
SetFinalRate -> SetPremium -> SetPremiumIndicator  # round(AdjBaseRate x factor x 4 mods, 4); premium x exposure[/1000]; $1 minimum in 2027
```

*Reconciled* against the gate's version of this section: the factor tables are keyed by **hazard grade**, not endorsement form number (the form selects *which* table); the hosts are not step-for-step identical (`SetAdjustedBaseRate`); the hazard-grade tables are 1,188 rows at CW 20231201/20260101/20261001 and 1,163 at CW 2027, and NY does **not** override them (its packages carry 0-row copies that fall through to CW); and the final-rate/premium arithmetic, which the gate left open, is now given. California still withdraws LoED (below). Engine worked numbers (TX@20270401, 200,000 limit, CG 04 37): Prem/Ops premium 1, Prod/CompOps premium 5.

---

## Cyber Incident Liability — rate build-up

Two matched groups (Prem/Ops host, Prod/CompOps host), 23 rules each — same skeleton as LoED, zero shared rule bodies (GATE-365 §2, table). *Reconciled from XML and engine runs (IL@20270401, IL@20261002, CG 04 95 record with occurrence 100,000 / aggregate 200,000):*

```
SetEachCyberIncidentOccurrenceLimit
SetCyberIncidentAggregateLimit
SetILF -> SetDeductibleFactor -> SetFinalILF
SetAdjustedBaseRate
SetHazardGrade
SetCyberIncidentLiabilityFactor
SetFinalRate -> SetPremium -> SetPremiumIndicator
(no ErcRunPostUnderwritingLogic -- Cyber has no refer band and no DoMessageILF)
```

### Gate
`SetCoverageOnPolicyIndicator` = 1 iff a Cyber limit schedule exists (standalone Cyber or the CG 04 95 combined record; the Prod/CompOps host also accepts the Owners/Contractors/Products Cyber schedule) **and** `CyberIncidentLiabilityCoverageApplies == "Yes"`. CW 2027 adds the Prod/CompOps-host Subline test (combined subline with `ProdsCompldOpsExclusion != "Yes"`, or Products-only); the Prem/Ops host has no Subline test.

### Step 1 — Limits
Cyber carries **two** limit rules — `EachCyberIncidentOccurrenceLimit` and `CyberIncidentAggregateLimit`, copied from the schedule record — where LoED carries one. (GATE-365 §2.)

### Steps 2–4 — ILF, adjusted base rate, hazard grade
- **ILF** = `LookupILFPremOps` / `LookupLookupILFProds` (sic) on the host ILF table, keyed by the host table assignment, the **Cyber occurrence limit** and the **Cyber aggregate limit** (not the policy aggregate); pre-2027 both keys carry " CSL". Engine: `ILFPremOps ['IL', 3, '100,000', '200,000'] -> 1` (2027), `['IL', 3, '100,000 CSL', '200,000 CSL'] -> 1` (2026).
- **DedFactor** = the host's `FinalDeductibleFactor` (Prem/Ops) — a different host field from LoED's; `FinalILF = round(ILF - DedFactor, 3)`, floored at 0.
- **AdjustedBaseRate** — same shapes as LoED (Prem/Ops: loss cost/ELP x LCM [x Claims-Made] [x SOR] x FinalILF; Prod/CompOps: host `BaseRate` [x SOR] x FinalILF), rounded to 4. Engine: Prem/Ops 0.0960, Prod/CompOps 0.8200.
- **HazardGrade** from `CyberIncidentLiability{PremOps,ProdsCompldOps}HazardGrade` (1,188 / 1,163 rows; NY 0-row copies fall through to CW).

### Step 5 — Coverage factor
`SetCyberIncidentLiabilityFactor` = `LookupCyberIncidentLiabilityFactor(HazardGrade)` against **`CyberIncidentLiability{PremOps,ProdsCompldOps}Factors`** (4 rows each, CW: 0.001 / 0.004 / 0.007 / 0.01); a blank hazard grade gives 0.0. *Reconciled:* `TypeOfPolicyWithCyberIncidentLiabCoverage` is **not** a rating factor — it is a stat-code table (`C5`–`C8`) read by `GeneralLiabilityRules` for `TypeOfPolicyStatCode` (engine: `C8` for a CG 04 95 policy).

### Step 6 — Final rate, premium, indicator
Identical arithmetic to LoED: `FinalRate = round(AdjustedBaseRate x CyberIncidentLiabilityFactor x PackageModFactor x ExperienceRatingModificationFactor x ExpenseModification x ModToUse, 4)`; `Premium = round(FinalRate x exposure [/1000], 0)`, with the $1 minimum in CW 2027 only. Engine (IL, both editions): Prem/Ops `FinalRate 0.0001`, premium 1; Prod/CompOps `FinalRate 0.0008`, premium 4.

---

## Loss Of Electronic Data / Cyber Incident Liability — premium

No branch structure (scheduled/blanket/Legal-Liability) exists for these coverages. Each has a policy-level `PremiumToReachMinCoverage` topper (`LossOfElectronicDataMinPremium`, `CyberIncidentLiabilityMinPremium`, both 1 row, $0) that **computes in every edition** (2023, 2026 and 2027 — unlike the 2027 Prem/Ops, Prod/CompOps and Product Withdrawal toppers, which are inert) and adds 0. *Engine finding:* both toppers' totals come out as the Prod/CompOps host premium only (`TotalCyberIncidentLiabilityPremium = 4`, `TotalLossOfElectronicDataPremium = 5`, Prem/Ops 1 dropped) because the engine's `ForEach` keeps only the last child's value per iteration; harmless at a $0 minimum.

### Gate — coverage on policy (California withdraws both coverages)
`SetCoverageOnPolicyIndicator` is stubbed to a constant **`0`** in all six LoED/Cyber-related groups (both classification groups per coverage, plus each `PremiumToReachMinCoverage` iterator) in `GL_CA_20241101_V01`. The rating chain never runs in California, so 13 tables emptied to zero rows in that state package are never reached — this is documented as deliberate ("N3's neutralising-stub idiom"), not a defect. (GATE-365 §10.) Engine-confirmed: CA resolves to `GL_CA_20241101_V01` over CW 20231201 V02 at both 2026-10-02 and 2027-04-01, and every LoED/Cyber indicator writes 0 with CG 04 95 attached.

| Coverage | Tables emptied in CA |
|---|---|
| Cyber Incident Liability | `CyberCoverageLimitStatCode`, `CyberIncidentLiabilityMinPremium`, `…PremOpsFactors`, `…PremOpsHazardGrade`, `…ProdsCompldOpsFactors`, `…ProdsCompldOpsHazardGrade`, `TypeOfPolicyWithCyberIncidentLiabCoverage` |
| Loss Of Electronic Data | `LossOfElectronicDataMinPremium`, `…PremOpsFactorCG0437`, `…PremOpsFactorCG0471`, `…PremOpsHazardGrade`, `…ProdsCompldOpsFactorCG0437`, `…ProdsCompldOpsFactorCG0471`, `…ProdsCompldOpsHazardGrade` |

California also stubs `SetSizeOfRiskRatingApplies` to `"No"` — consistent, since Size-Of-Risk is exactly what LoED and Cyber read across the group boundary (E18); a state withdrawing both coverages has no reason to keep the input they need. (GATE-365 §10.)

---

## Edition differences

| Item | CW 20231201 V03 / 20260101 V01 / 20261001 V01 | CW 20270401 V01 | CW 20270401 V02 |
|---|---|---|---|
| PW A/B deductible | `DedFactorProdsCSL` ("1,000 Per Occurrence") or `ProductWithdrawalDeductibleFactorOverride` | `DedFactorProdsProdWithdrawl` ("1,000"), no override | = V01 |
| PW A/B, LoED, Cyber `SetPremium` | no $1 minimum | $1 minimum; /1000 list with Kilowatt-hours | = V01 |
| PW coverage-form min premium / PW topper | computed (min $0) / gate needs coverage-form record | removed / indicator hard 0 | = V01 |
| PW coverage-form `SetLimitsIdentifierStatCode`, `SetRiskIDStatCode` | branch on `ExpensePremium` / `LiabilityPremium` > 0 | same (fields no longer computed) | branch on Subline "Product Withdrawal" + `ProductWithdrawalCoverageType` (Expense / Liability / Both -> "A and B"); otherwise blank |
| Limited PW deductible / class-level min | `DedFactorProdsCSL` or override; `SetHighestLmtdProdsWithdrawalFinalILFFlag`, PolLvl `SetMinPremium` | `DedFactorProdsProdWithdrawl`; flag and PolLvl `SetMinPremium` removed | = V01 |
| Limited PW coverage `SetPremium` | Manual premium x pkg mod x discount, or class premium when participation "0" | class premium [x discount if participation/cut-off], $1 minimum | = V01 |
| LoED/Cyber ILF key | limit + " CSL" | bare limit | = V01 |
| Cyber `DoMessageCyberIncidentAggregateLimit` (both Cyber schedule files) | — | one message, "…shall be less than or equal to the Aggregate Limit applicable to the policy", when the Cyber aggregate exceeds the general aggregate **or** the Prod/CompOps aggregate | split in two: Cyber aggregate > general aggregate (combined subline) -> the same "…Aggregate Limit applicable to the policy" message; Cyber aggregate > Prod/CompOps aggregate (combined subline, `ProdsCompldOpsExclusion` set and != "Yes") -> new "…Products Completed Operation Aggregate Limit applicable to the policy" message. Same change in the CG 04 95 schedule file |

---

## Comparison — the six rate-driven groups plus Limited Product Withdrawal

| | Product Withdrawal Coverage A | Product Withdrawal Coverage B | Limited Product Withdrawal | LoED (x2 hosts) | Cyber (x2 hosts) |
|---|---|---|---|---|---|
| Own subline | 365 | 365 | none — endorsement CG 04 36 on 336 | none — endorsement CG 04 37/71/95 | none |
| Rules | 27 | 27 | 11 (10 in 2027) (+ 43 across 4 more groups) | 25 each | 23 each |
| Host | Prod/CompOps (336) tables | Prod/CompOps (336) tables | Prod/CompOps (336) | Prem/Ops (334) or Prod/CompOps (336) | Prem/Ops (334) or Prod/CompOps (336) |
| Reads host's computed values (E18) | no — looks up host loss-cost / ELP tables | same | yes — `ProdsCompldOpsLossCost` directly | yes — host loss cost/ELP/LCM/Claims-Made/SOR or host `BaseRate` | yes — same shape as LoED |
| Rating basis selector | borrowed from host (`ProdsCompldOpsELPText`) | borrowed from host | n/a (uses host loss cost/ELP directly) | n/a | n/a |
| Factor table | `ProductWithdrawalExpensesFactor` (A 0.25/B 0.19/C 0.13) | `ProductWithdrawalLiabilityFactor` (A 0.13/B 0.10/C 0.07) | `ProductWithdrawlFactor` **misspelled** (A 0.20/B 0.15/C 0.10) | 2 per host, keyed by hazard grade; form selects CG0437 vs CG0471 | 1 per host, keyed by hazard grade |
| Limits | `ProductsWithdrawalAggregateLimit` (ILF key) | same | aggregate + deductible (endorsement record) | one limit | occurrence + aggregate (2 limits) |
| FinalILF floor | none | none | none (N15 guard only) | floored at 0 | floored at 0 |
| Negative-premium guard | not documented | not documented | yes — the only one in the corpus (N15) | not documented | not documented |
| Manual anchor | Rule 44.B.3.a.(5) / 44.B.3.b, p.93 | Rule 44.B.3.a.(5) / 44.B.3.b, p.93 | Rule 44.B.3.a.(5) / 44.B.3.b, p.93 (same factor table family) | Rule 40 | Rule 40 |
| California | not documented as withdrawn | not documented as withdrawn | not documented as withdrawn | withdrawn (stubbed to 0; engine-confirmed) | withdrawn (stubbed to 0; engine-confirmed) |
| State deviation | 17 rules / 9 jurisdictions (whole gate total) | (included above) | 1 of 51 (Texas — `InitializeRuleSet` + 2 stat-code lookups); 0 of 51 on the 11 rating rules | 8 states (IN, MO, MT, ND, NH, OK, TN, UT) override `SetILF` on both hosts — see the LoED doc | (included in whole-gate total) |

---

## Supporting lookups

| Table | Key | Values (A/B/C or CW) | Reader | Source |
|---|---|---|---|---|
| `ProductWithdrawalExpensesFactor` | `FinalProductWithdrawalIncrdLimitTableAssignment` | 0.25 / 0.19 / 0.13 | Coverage A `SetProductWithdrawalExpenseFactor` | GATE-365 §1; engine |
| `ProductWithdrawalLiabilityFactor` | `FinalProductWithdrawalIncrdLimitTableAssignment` | 0.13 / 0.10 / 0.07 | Coverage B `SetProductWithdrawalLiabilityFactor` | GATE-365 §1; engine |
| `ProductWithdrawlFactor` **(misspelled)** | `IncreasedLimitsTableAssignmentProdsCompldOpsFinal` / `FinalProdsCompldOpsIncrdLimitTableAssignment` | 0.20 / 0.15 / 0.10 | `SetLmtdProductWithdrawlFactor` (Limited Product Withdrawal) | GATE-365 §1, §9.2, §9.3; engine |
| `ProductWithdrawalLCM` | constant `'Y'` | CW: 1 row = 1 | `SetLCM` (365), `SetLmtdLCM` | GATE-365 §1, §3 (E15); engine |
| `ProductWithdrawalMinPremium` | constant `'Y'` | CW: 1 row = 0 (pre-2027); 0 rows in CW 2027 | pre-2027 coverage-form `SetMinimumPremium` | GATE-365 §3 (E16); engine IL@20261002 |
| `ProductWithdrawalExpensesAndLiabilityIncrdLimitFactor` | assignment, aggregate limit | CW: 0 rows; state: 51/51, 36 rows each | `SetCFLILF`, `SetLmtdProdsWithdrawalIncreasedLimitsFactor` | GATE-365 §1, §3, §9.2, §9.5; engine (TX B/1,000,000 1.65; IL 1.73; IL B/100,000 0.97) |
| `DedFactorProdsProdWithdrawl` (CW 2027 only) | assignment, `ProductWithdrawalDeductible` | 48 rows CW (B/1,000 = 0.015) | `SetDeductibleFactor` (365), `SetLmtdDeductibleFactor` | XML; engine |
| `LookupProdsCompldOpsLossCost` (host table) | `StateCode`, `ProdsCompldOpsTerritory`, `ClassCode` | — | `SetLossCosts` (365) | GATE-365 §1; engine |
| `LookupProdsCompldOpsELPFactor` (host table) | `StateCode`, `ClassCode` | — | `SetELP` | GATE-365 §1; engine |
| `LookupProdsCompldOpsELPText` (host table) | — | — | `SetProductWithdrawalELP` | GATE-365 §1 |
| `LookupDedFactorProdsCSL` (host table, pre-2027) | assignment, deductible ("… Per Occurrence") | — | `SetDeductibleFactor` (365), `SetLmtdDeductibleFactor` | GATE-365 §1, §9.2; engine |
| `LossOfElectronicData{PremOps,ProdsCompldOps}HazardGrade` | `StateCode`, `ClassCode` | 1,188 rows (CW 2023/26) / 1,163 (CW 2027); NY 0-row copies fall through | `SetHazardGrade` (LoED) | LoED doc; engine |
| `CyberIncidentLiability{PremOps,ProdsCompldOps}HazardGrade` | `StateCode`, `ClassCode` | 1,188 / 1,163; NY 0-row copies fall through | `SetHazardGrade` (Cyber) | XML; engine |
| `LossOfElectronicData{PremOps,ProdsCompldOps}Factor{CG0437,CG0471}` | `StateCode`, `HazardGrade` | CW, 4 rows each | `SetLossOfElectronicDataFactor` | LoED doc; engine |
| `CyberIncidentLiability{PremOps,ProdsCompldOps}Factors` | `StateCode`, `HazardGrade` | CW, 4 rows (0.001/0.004/0.007/0.01) | `SetCyberIncidentLiabilityFactor` | XML; engine |
| `TypeOfPolicyWithCyberIncidentLiabCoverage` | endorsement description | CW, 4 rows (`C5`–`C8`) — stat code, not a factor | `GeneralLiabilityRules` (`TypeOfPolicyStatCode`) | XML; engine |
| `LossOfElectronicDataMinPremium` | constant `'Y'` | CW: 1 row = 0 | LoED topper `SetMinPremium` | engine |
| `CyberIncidentLiabilityMinPremium` | constant `'Y'` | CW: 1 row = 0 | Cyber topper `SetMinPremium` | engine |
| `SublineProductWithdrawal` | — | 0 rows, 0 readers, every edition — orphan table | none | GATE-365 §1, §5 |

Every lookup above follows GL's two-pass pattern — `FirstNonNull(Lookup(StateCode, …) FirstResult, Lookup('CW', …) SingleResult)` — visible in the engine traces as a state `lookup-miss` followed by the CW hit. *Reconciled:* the gate did not assert this; the XML and engine confirm it.

---

## Quick reference — end-to-end, Product Withdrawal Coverage A

```
Gate                           = Subline == "Product Withdrawal" AND CoverageType in (Expense, Both Expense and Liability)
ProductWithdrawlExpenseFactor  = lookup(FinalProductWithdrawalIncrdLimitTableAssignment)   [CW A 0.25/B 0.19/C 0.13]
LCM                            = lookup ProductWithdrawalLCM('Y')                           [CW = 1]
ELP                            = lookup ProdsCompldOpsELPFactor(ClassCode)   if host selector != "Company"
                                 | ProductWithdrawalELPOverride, else 0.0
CSLILF                         = lookup ProductWithdrawalExpensesAndLiabilityIncrdLimitFactor(assignment, ProductsWithdrawalAggregateLimit)   [state-filed]
DeductibleFactor               = 2027: lookup DedFactorProdsProdWithdrawl(assignment, deductible)
                                 | pre-2027: override if non-zero, else lookup DedFactorProdsCSL(assignment, "… Per Occurrence")
FinalILF                       = round(CSLILF - DeductibleFactor, 3)                      [no floor]
LossCost                       = lookup ProdsCompldOpsLossCost(ProdsCompldOpsTerritory, ClassCode)    [0.0 if class/territory empty]

BaseRate  = round(ELP x factor x LCM, 3)        if LossCost == 0
          | round(LossCost x factor x LCM, 3)   otherwise

PremiumDiscountCharge = round(1 - PremiumDiscountPercentage/100, 3) | 1.0

FinalRate = round(BaseRate x FinalILF x PackageModFactor x ExperienceRatingModificationFactor
                  x ExpenseModification x ModToUse x PremiumDiscountCharge, 3)

Premium   = round(FinalRate x exposure / 1000, 0)     [/1000 bases]
          | round(FinalRate x exposure, 0)            [otherwise]
          | 1.0 if 0 and exposure > 0                 [2027 only]

Worked (TX@20270401, class 50017, Gross Sales 5,000,000, agg 1,000,000, ded 1,000):
  0.19 -> BaseRate 0.156 -> FinalILF 1.635 -> FinalRate 0.255 -> Premium 1,275
```

Coverage B: identical, substituting `ProductWithdrawalLiabilityFactor` [CW A 0.13/B 0.10/C 0.07] — worked: 0.10 -> 0.082 -> 0.134 -> 670.

## Quick reference — end-to-end, Limited Product Withdrawal Expense

```
LmtdLCM              = lookup ProductWithdrawalLCM  (= 1)   [gated: ProdsWithdrawalCoverage == Yes, CG 04 36 record, Prod/CompOps coverage]
LmtdProductWithdrawalFactor = lookup ProductWithdrawlFactor(FinalProdsCompldOpsIncrdLimitTableAssignment)
                                                          [CW A 0.20/B 0.15/C 0.10 -- MISSPELLED table]

LmtdBaseRate = round((ProdsCompldOpsLossCost | FinalProdsCompldOpsELP)     # SIBLING group's computed value
             x LmtdLCM x LmtdProductWithdrawalFactor, 3)

LmtdIncreasedLimitsFactor = lookup ProductWithdrawalExpensesAndLiabilityIncrdLimitFactor(
                                 FinalProdsCompldOpsIncrdLimitTableAssignment, AggregateLimit)
LmtdCSLILF                = LmtdIncreasedLimitsFactor
LmtdDeductibleFactorForRating = 2027: lookup DedFactorProdsProdWithdrawl | pre-2027: lookup DedFactorProdsCSL or Override

LmtdFinalILF   = CSLILF - DeductibleFactorForRating         [no arithmetic floor -- guarded by validation, N15]
LmtdFinalRate  = round(BaseRate x FinalILF x PackageModFactor, 3)
LmtdPremium    = round(FinalRate x ProdsCompldOpsCovExposure [/1000], 0)

ClassPremium    = sum of LmtdPremium over classifications
CoveragePremium = 2027: round(ClassPremium [x PremiumDiscountCharge if participation/cut-off], 0), $1 minimum
                | pre-2027: round(ManualPremium x PackageModFactor x PremiumDiscountCharge, 0) if participation != "0"
                            round(ClassPremium, 0) if participation == "0"

Worked (IL@20270401, agg 100,000, ded 1,000): 0.15 -> BaseRate 0.123 -> FinalILF 0.955 -> FinalRate 0.117 -> 585
```

## Quick reference — end-to-end, Loss Of Electronic Data (or Cyber, same shape)

```
Limit(s)      = LossOfElectronicDataLimit                                          [LoED: 1 limit]
              | EachCyberIncidentOccurrenceLimit + CyberIncidentAggregateLimit     [Cyber: 2 limits]

ILF           = host ILF table (ILFPremOps / ILFProds), [+" CSL" pre-2027]
                LoED: (LoED limit, policy/Prods aggregate), 13 refer bands -> ILFOverride
                Cyber: (Cyber occurrence, Cyber aggregate), no refer band
DedFactor     = host deductible factor (LoED: DeductibleFactor | PDDeductibleFactor; Cyber: FinalDeductibleFactor)
FinalILF      = max(round(ILF - DedFactor, 3), 0)

AdjustedBaseRate (Prem/Ops) = round((host LossCost | host ELP) x host LCM [x ClaimsMadeMultiplier] [x SOR] x FinalILF, 4)
AdjustedBaseRate (Prods)    = round(host BaseRate [x SOR] x FinalILF, 4)

HazardGrade   = lookup {LossOfElectronicData|CyberIncidentLiability}{PremOps|ProdsCompldOps}HazardGrade(ClassCode)
                                                          [1,188 (2023/26) / 1,163 (2027) rows CW]

CoverageFactor = lookup LossOfElectronicData{host}Factor{CG0437|CG0471}(HazardGrade)   [CG 04 37 / CG 04 95 -> CG0437]
               | CyberIncidentLiability{host}Factors(HazardGrade)

FinalRate     = round(AdjustedBaseRate x CoverageFactor x PackageMod x ExpRating x ExpenseMod x ModToUse, 4)
Premium       = round(FinalRate x exposure [/1000], 0); $1 minimum in 2027
Indicator     = 1 iff Premium != 0

Gate: SetCoverageOnPolicyIndicator = 0 in California for all 6 LoED/Cyber groups -- chain never runs
```

---
