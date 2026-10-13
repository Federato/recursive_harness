# Product Withdrawal / Loss Of Electronic Data / Cyber Incident Liability — Required ERC Tables

**Source:** `C:\Projects\Recursive_Harness_2.0\docs\gates\GATE-365-WITHDRAWAL-LOED-CYBER.md` (as-of date 2026-08-11, addenda through 2026-08-12), derived against **`GL_CW_20231201_V03`**.
**Line:** General Liability (GL), Countrywide, build-order item 6.
**Derived from:** `ProductWithdrawalCyber_RatingAlgorithms.md` (this pair). For Loss Of Electronic Data the authoritative table list is `LossOfElectronicData_ERC_Tables.md`; the LoED rows here are kept consistent with it.
**Documented (this port):** 2026-08-20.
**Reconciled against the built engine:** 2026-10-02 (commit `630ba2f`) — table keys, row counts and values re-read from the CSVs in CW 20231201 V03 / 20260101 V01 / 20261001 V01 / 20270401 V01 / V02, and every rating table below hit (or its state-miss/CW-fallback observed) in offline engine traces at TX@20270401, IL@20270401, TX@20261002 and IL@20261002 with Product Withdrawal, CG 04 36, CG 04 37 and CG 04 95 records added to the base submission.

This lists every ERC rate table required to rate Product Withdrawal (365), Limited Product Withdrawal Expense (CG 04 36), Loss Of Electronic Data (CG 04 37 / CG 04 71 / CG 04 95), and Cyber Incident Liability. The 2026-08-20 port carried the gate's figures unverified; the rows below are now checked against the raw ERC files and the engine (corrections marked *Reconciled*).

---

## Rate-build-up tables (state-or-CW keyed)

| Table | Used for | Keys | CW rows |
|---|---|---|---|
| `ProductWithdrawalExpensesFactor` | Product Withdrawal Coverage A base rate factor | `StateCode`, `FinalProductWithdrawalIncrdLimitTableAssignment` | 3 (A 0.25 / B 0.19 / C 0.13) |
| `ProductWithdrawalLiabilityFactor` | Product Withdrawal Coverage B base rate factor | `StateCode`, `FinalProductWithdrawalIncrdLimitTableAssignment` | 3 (A 0.13 / B 0.10 / C 0.07) |
| `ProductWithdrawlFactor` *(misspelled — distinct table, not a duplicate)* | Limited Product Withdrawal Expense base rate factor | `StateCode`, `IncreasedLimitsTableAssignmentProdsCompldOpsFinal` (= `FinalProdsCompldOpsIncrdLimitTableAssignment`) | 3 (A 0.20 / B 0.15 / C 0.10) |
| `ProductWithdrawalLCM` | Product Withdrawal and Limited Product Withdrawal loss-cost multiplier | `StateCode`, constant `'Y'` | 1 (value = 1) |
| `ProductWithdrawalExpensesAndLiabilityIncrdLimitFactor` | Increased limits factor — Product Withdrawal (365) and Limited Product Withdrawal | `StateCode`, assignment (`FinalProductWithdrawalIncrdLimitTableAssignment` for 365 / `FinalProdsCompldOpsIncrdLimitTableAssignment` for Limited), aggregate limit (`ProductsWithdrawalAggregateLimit` / the CG 04 36 `AggregateLimit`) | 0 CW in every edition — state-filed, 36 rows (TX, IL 2027 re-counted); engine: TX B/1,000,000 1.65, IL B/1,000,000 1.73, IL B/100,000 0.97 |
| `DedFactorProdsProdWithdrawl` *(CW 2027 only — Reconciled, new)* | Deductible factor, Product Withdrawal A/B and Limited Product Withdrawal | `StateCode`, `ProductWithdrawalIncrdLimitTableAssignment`, `ProductWithdrawalDeductible` (`"No Deductible"`, `"250"` … `"1,000"` …) | 48 (B/1,000 = 0.015) |
| `LossOfElectronicDataPremOpsHazardGrade` / `…ProdsCompldOpsHazardGrade` | LoED hazard grade, per class code, per host | `StateCode`, `ClassCode` | 1,188 (CW 2023/2026/20261001) / 1,163 (CW 2027). *Reconciled:* NY does not override — its 2024 packages carry 0-row copies that fall through to CW |
| `CyberIncidentLiabilityPremOpsHazardGrade` / `…ProdsCompldOpsHazardGrade` | Cyber hazard grade, per class code, per host | `StateCode`, `ClassCode` | 1,188 / 1,163; same NY 0-row fall-through |
| `LossOfElectronicDataPremOpsFactorCG0437` | LoED coverage factor, Prem/Ops host, CG 04 37 or CG 04 95 | `StateCode`, `HazardGrade` | 4 (0.001 / 0.003 / 0.005 / 0.007) |
| `LossOfElectronicDataPremOpsFactorCG0471` | LoED coverage factor, Prem/Ops host, CG 04 71 | `StateCode`, `HazardGrade` | 4 (0.0008 / 0.0024 / 0.004 / 0.0056) |
| `LossOfElectronicDataProdsCompldOpsFactorCG0437` | LoED coverage factor, Prod/CompOps host, CG 04 37 or CG 04 95 | `StateCode`, `HazardGrade` | 4 |
| `LossOfElectronicDataProdsCompldOpsFactorCG0471` | LoED coverage factor, Prod/CompOps host, CG 04 71 | `StateCode`, `HazardGrade` | 4 |
| `CyberIncidentLiabilityPremOpsFactors` / `CyberIncidentLiabilityProdsCompldOpsFactors` | Cyber coverage factor, per host | `StateCode`, `HazardGrade` | 4 each (0.001 / 0.004 / 0.007 / 0.01) |

*Reconciled:* the LoED and Cyber factor tables are keyed by **hazard grade**, not endorsement form number — the attached form only selects which LoED table is read (CG 04 37 and CG 04 95 -> CG0437; CG 04 71 -> CG0471). `TypeOfPolicyWithCyberIncidentLiabCoverage` is not a rate table at all (see Statistical tables).

Host tables consumed but **not owned by this subline** (documented here because the rate build-up depends on them, per GATE-365 §1 and §9.2 — see the sibling subline's own ERC_Tables doc for their filed status):

| Table | Owner | Consumed by |
|---|---|---|
| `ProdsCompldOpsLossCost` (keyed `StateCode`, `ProdsCompldOpsTerritory`, `ClassCode`) | Prod/CompOps (336) | Product Withdrawal Coverage A/B `SetLossCosts` (direct lookup) |
| `ProdsCompldOpsELPFactor` (keyed `StateCode`, `ClassCode`) | Prod/CompOps (336) | Product Withdrawal Coverage A/B `SetELP` (direct lookup) |
| `LookupProdsCompldOpsELPText` | Prod/CompOps (336) | `SetProductWithdrawalELP` (rating-basis selector, borrowed) |
| `ILFPremOps` / `ILFProds` | Prem/Ops (334) / Prod/CompOps (336) | LoED and Cyber `SetILF` (LoED limit, or Cyber occurrence + aggregate, as keys) |
| `GeneralLiabilityClassificationProdsCompldOpsCoverage/ProdsCompldOpsLossCost` | Prod/CompOps (336) | Limited Product Withdrawal `SetLmtdProdsWithdrawalBaseRate` — E18, computed value |
| `GeneralLiabilityClassificationPremOpsCoverage/{PremOpsLossCost, PremOpsELP, LCM, ClaimsMadeMultiplier, PremOpsSizeOfRiskFinalRelativity}` | Prem/Ops (334) | LoED/Cyber `SetAdjustedBaseRate` (Prem/Ops-hosted groups) — E18, computed values |
| `GeneralLiabilityClassificationProdsCompldOpsCoverage/{BaseRate, ProdsCompldOpsSizeOfRiskFinalRelativity}` | Prod/CompOps (336) | LoED/Cyber `SetAdjustedBaseRate` (Prod/CompOps-hosted groups) — E18 |

---

## Coinsurance / LOI / deductible tables

GL casualty coverages in this gate do not carry a coinsurance or limit-of-insurance (LOI) concept in the CF property sense — this section covers the analogous deductible/increased-limits factor.

| Table | Used for |
|---|---|
| `DedFactorProdsCSL` *(Prod/CompOps's own table, borrowed — not owned by 365; pre-2027 only)* | Product Withdrawal Coverage A/B deductible factor (`SetDeductibleFactor`, unless `ProductWithdrawalDeductibleFactorOverride` is non-zero); Limited Product Withdrawal deductible factor (`SetLmtdDeductibleFactor`), or the supplied override. 93 rows CW; keys are `"… Per Claim"` / `"… Per Occurrence"` strings — a bare `"1,000"` misses and the engine stops INCOMPLETE |
| `DedFactorProdsProdWithdrawl` *(CW 2027)* | Replaces `DedFactorProdsCSL` for both Product Withdrawal and Limited Product Withdrawal; no override path |
| `ProductWithdrawalExpensesAndLiabilityIncrdLimitFactor` | Increased-limits ("CSL ILF") factor — see rate-build-up table above; the closest GL analogue to CF's LOI factor |
| host `DeductibleFactor` / `PDDeductibleFactor` / `FinalDeductibleFactor` | LoED (`DeductibleFactor` or `PDDeductibleFactor`) and Cyber (`FinalDeductibleFactor`) copy the host's computed value into `DedFactor` — no table of their own |

Not applicable to this subline — no coinsurance factor, no limit-of-insurance-percentage table, and no deductible-by-location table exist for any of these coverages.

---

## Premium-level tables

| Table | Used for | CW rows |
|---|---|---|
| `ProductWithdrawalMinPremium` | Product Withdrawal minimum premium (pre-2027 coverage-form `SetMinimumPremium`; `MinPremium = round(FinalILF x MinimumPremium, 0)`) | 1 (value = 0) in CW 2023/2026/20261001; **0 rows in CW 2027**, where the rule that read it is removed |
| `LimitedProductWithdrawalExpenseMinPremium` | Limited Product Withdrawal minimum premium (…EndtPolLvl) | 1 (value = 0) |
| `LossOfElectronicDataMinPremium` | LoED minimum-premium topper (computes in every edition) | 1 (value = 0) |
| `CyberIncidentLiabilityMinPremium` | Cyber minimum-premium topper (computes in every edition) | 1 (value = 0) |

`PackageModFactor`, `ExperienceRatingModificationFactor`, `ExpenseModification`, `ModToUse`, and `PremiumDiscountCharge` appear in the final-rate formulas. *Reconciled:* `PremiumDiscountCharge` is computed, not looked up — `round(1 - PremiumDiscountPercentage x 0.01, 3)` from the policy's `PremiumDiscountPercentage` input, else 1.0 (Product Withdrawal A/B; Limited PW in CW 2027) or 0.0 (Limited PW pre-2027). The four modification factors are read by path from the `GeneralLiability` record (see "Not ERC tables").

---

## Statistical / subline tables

| Table | Used for | Rows | Readers |
|---|---|---|---|
| `SublineProductWithdrawal` | Subline stat code for 365 | 0 in every edition | **0 — orphan table**, the second one found in this project after `RailroadLossCost` (the live subline code comes from `Subline`, `['CW','Product Withdrawal'] -> '365'`) |
| `CyberCoverageLimitStatCode` | LoED and Cyber `SetLimitStatCode`, keyed `(StateCode, EachOccurrenceLimit, AggregateLimit)` | 130 CW | 4 classification groups (LoED x2, Cyber x2); emptied to 0 rows in `GL_CA_20241101_V01` |
| `TypeOfPolicyWithCyberIncidentLiabCoverage` | Policy-level `TypeOfPolicyStatCode` for the attached Cyber/LoED endorsement (`C5` CG 04 37, `C6` CG 04 71, `C7` Cyber, `C8` CG 04 95) | 4 CW | `GeneralLiabilityRules` — *Reconciled:* a stat-code table, not a rating factor |
| `LimitsIdentifierProductWithdrawalStatCode`, `RiskIDProductWithdrawalStatCode`, `PolicyLimitsProductWithdrawalCovStatCode`, `ProductWithdrawalDeductibleStatCode`, `RiskIDProdWithdrawalExpnStatCode`, `DedProdWithdrawlStatCode` | Product Withdrawal / Limited PW stat codes (coverage form, …EndtPolLvl) | small CW tables | CW 20270401 V02 changed when the coverage form reads the first two (keyed on `ProductWithdrawalCoverageType` instead of computed premiums) |

---

## Not ERC tables

`PackageModFactor`, `ExperienceRatingModificationFactor`, `ExpenseModification` and `ModToUse` are read as `FirstValue … FromDataDef=../../../../../<field>` on the `GeneralLiability` record by every rate-driven group here — no `Lookup` in these coverage files. `PackageModFactor` is a submission input; `ExperienceRatingModificationFactor` and `ModToUse` are set by policy-level rules (`SetExperienceRatingModificationFactor`, `SetModToUse` in `GeneralLiabilityRules`).

`ProductWithdrawalParticipationPercentage` (pre-2027, string) / `ProductWithdrawalParticipationPercentageInt` (2027) and `ProductsWithdrawalCutOffDateApplies` are **submission inputs** that select the Limited Product Withdrawal coverage-premium branch — *Reconciled:* they are not multiplied into the premium. `ILFOverride` (LoED), `ProductWithdrawalELPOverride`, `ProductWithdrawalDeductibleFactorOverride` (pre-2027) and `ManualPremium` (Limited PW, pre-2027) are likewise submission inputs.

---

## Verification

| Check | Result |
|---|---|
| Engine runs (2026-10-02) | Product Withdrawal A/B rated end-to-end at TX@20270401 (1,275 / 670), IL@20270401 (1,340 / 705), TX@20261002 (1,275 / 670), IL@20261002 (1,340 / 705); Limited PW at IL@20270401 (585); LoED and Cyber at TX/IL both editions. Limited PW pre-2027 stops INCOMPLETE in the engine at `…EndtPolLvl.SetMinPremium` (unbound `ErcNodeSublineParam`) after the class chain computed 585 |
| `tests/verify_golden.py` | not run in this reconciliation; per the gate, no Product Withdrawal, LoED, or Cyber premium in the golden case (no oracle) |
| `ProductWithdrawlFactor` vs manual Table 44.B.3.b | 3/3 exact, key axis included (GATE-365) |
| `ProductWithdrawalExpensesFactor` / `…LiabilityFactor` | values re-read from CW CSVs (all editions) and hit by the engine |
| Rate-driven groups in item 6 | 7 (2 Product Withdrawal + 4 LoED/Cyber + 1 Limited Product Withdrawal rating chain); 27 / 27 / 25 / 25 / 23 / 23 named rules re-counted from CW 2027 XML |
| Pairwise identical rule bodies across the 6 rate-driven groups | 0 (GATE-365) |
| Tables with 0 rows and 0 readers | 1 (`SublineProductWithdrawal`) |
| State deviation surface (whole gate) | 17 rules, 9 jurisdictions (CA, IN, MO, MT, ND, NH, OK, TN, UT) per GATE-365; the 8 non-CA states' LoED override covers both host files (see the LoED doc) |
| State deviation, Limited Product Withdrawal specifically | 1 of 51 (Texas — `InitializeRuleSet` + 2 stat-code lookups); 0 of 51 on the 11 rating rules themselves |
| `ProductWithdrawalExpensesAndLiabilityIncrdLimitFactor` state coverage | 0 rows in every CW edition; state packages 36 rows (TX, IL re-counted) |
| California LoED/Cyber withdrawal | `SetCoverageOnPolicyIndicator` stubbed to `0` in all 6 groups; engine-confirmed at CA@20261002 and CA@20270401 |
| `verify_oi50.py` | Pins the Limited Product Withdrawal derivation (§9); not run in this reconciliation |

Header-only CW tables, re-checked: `ProductWithdrawalMinPremium` (0 rows in CW 2027 only), `ProductWithdrawalExpensesAndLiabilityIncrdLimitFactor` (0 rows CW by design — always state-filed), `SublineProductWithdrawal` (0 rows always). Every other table listed above has rows at CW in the editions where it is read.
