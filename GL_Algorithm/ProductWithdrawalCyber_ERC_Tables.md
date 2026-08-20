# Product Withdrawal / Loss Of Electronic Data / Cyber Incident Liability — Required ERC Tables

**Source:** `C:\Projects\Recursive_Harness_2.0\docs\gates\GATE-365-WITHDRAWAL-LOED-CYBER.md` (as-of date 2026-08-11, addenda through 2026-08-12), derived against **`GL_CW_20231201_V03`**.
**Line:** General Liability (GL), Countrywide, build-order item 6.
**Derived from:** `ProductWithdrawalCyber_RatingAlgorithms.md` (this pair).
**Documented (this port):** 2026-08-20.

This lists every ERC rate table named in GATE-365-WITHDRAWAL-LOED-CYBER.md as required to rate Product Withdrawal (365), Limited Product Withdrawal Expense (CG 04 36), Loss Of Electronic Data (CG 04 37 / CG 04 71), and Cyber Incident Liability. Unlike the CF source, this gate is a derived document, not a direct ERC XML trace — table existence, row counts and key axes below are exactly what the gate reports; no table was independently re-verified against the raw ERC files for this port.

---

## Rate-build-up tables (state-or-CW keyed)

| Table | Used for | Keys | CW rows |
|---|---|---|---|
| `ProductWithdrawalExpensesFactor` | Product Withdrawal Coverage A base rate factor | `FinalProductWithdrawalIncrdLimitTableAssignment` | 3 (A 0.25 / B 0.19 / C 0.13) |
| `ProductWithdrawalLiabilityFactor` | Product Withdrawal Coverage B base rate factor | `FinalProductWithdrawalIncrdLimitTableAssignment` | 3 (A 0.13 / B 0.10 / C 0.07) |
| `ProductWithdrawlFactor` *(misspelled — distinct table, not a duplicate)* | Limited Product Withdrawal Expense base rate factor | `IncreasedLimitsTableAssignmentProdsCompldOpsFinal` / `FinalProdsCompldOpsIncrdLimitTableAssignment` | 3 (A 0.20 / B 0.15 / C 0.10) |
| `ProductWithdrawalLCM` | Product Withdrawal loss-cost multiplier | — | 1 (value = 1) |
| `ProductWithdrawalExpensesAndLiabilityIncrdLimitFactor` | Increased limits factor — Product Withdrawal (365) and Limited Product Withdrawal | `FinalProductWithdrawalIncrdLimitTableAssignment` (365) / `FinalProdsCompldOpsIncrdLimitTableAssignment` + `AggregateLimit` (Limited) | 0 CW — state-filed, 51/51 jurisdictions, 36 rows each |
| `LossOfElectronicDataPremOpsHazardGrade` | LoED hazard grade, per class code | class code | 1,188 (CW 2023/2026) / 1,163 (CW 2027); NY overrides to 1,190/1,191 |
| `CyberIncidentLiabilityPremOpsHazardGrade` | Cyber hazard grade, per class code | class code | 1,188 (CW 2023/2026) / 1,163 (CW 2027); NY overrides to 1,191 |
| `LossOfElectronicDataPremOpsFactorCG0437` | LoED coverage factor, Prem/Ops host, CG 04 37 | endorsement form number | 4 |
| `LossOfElectronicDataPremOpsFactorCG0471` | LoED coverage factor, Prem/Ops host, CG 04 71 | endorsement form number | 4 |
| `LossOfElectronicDataProdsCompldOpsFactorCG0437` | LoED coverage factor, Prod/CompOps host, CG 04 37 | endorsement form number | 4 |
| `LossOfElectronicDataProdsCompldOpsFactorCG0471` | LoED coverage factor, Prod/CompOps host, CG 04 71 | endorsement form number | 4 |
| `CyberIncidentLiability…Factors` (Prem/Ops and Prod/CompOps variants, exact names not itemized in source) | Cyber coverage factor | endorsement form number (by analogy to LoED) | 4 each |
| `TypeOfPolicyWithCyberIncidentLiabCoverage` | Cyber Incident Liability — policy type factor | not given | 4 (gate: "similar shape") |

Host tables consumed but **not owned by this subline** (documented here because the rate build-up depends on them, per GATE-365 §1 and §9.2 — see the sibling subline's own ERC_Tables doc for their filed status):

| Table | Owner | Consumed by |
|---|---|---|
| `LookupProdsCompldOpsLossCost` (state-filed loss cost, keyed on `ProdsCompldOpsTerritory`) | Prod/CompOps (336) | Product Withdrawal Coverage A/B `SetLossCosts`; Limited Product Withdrawal `SetLmtdProdsWithdrawalBaseRate` |
| `LookupProdsCompldOpsELPFactor` | Prod/CompOps (336) | Product Withdrawal Coverage A/B `SetELP` |
| `LookupProdsCompldOpsELPText` | Prod/CompOps (336) | Product Withdrawal `SetProductWithdrawalELP` (rating-basis selector, borrowed) |
| `GeneralLiabilityClassificationPremOpsCoverage/{PremOpsLossCost, PremOpsELP, LCM, ClaimsMadeMultiplier, PremOpsSizeOfRiskFinalRelativity}` | Prem/Ops (334) | LoED/Cyber `SetAdjustedBaseRate` (Prem/Ops-hosted groups) — E18, computed values not just tables |
| `GeneralLiabilityClassificationProdsCompldOpsCoverage` equivalents | Prod/CompOps (336) | LoED/Cyber `SetAdjustedBaseRate` (Prod/CompOps-hosted groups) — E18 |

---

## Coinsurance / LOI / deductible tables

GL casualty coverages in this gate do not carry a coinsurance or limit-of-insurance (LOI) concept in the CF property sense — this section covers the analogous deductible/increased-limits factor.

| Table | Used for |
|---|---|
| `LookupDedFactorProdsCSL` *(Prod/CompOps's own table, borrowed — not owned by 365)* | Product Withdrawal Coverage A/B deductible factor (`SetDeductibleFactor`); Limited Product Withdrawal deductible factor (`SetLmtdDeductibleFactor`), or the supplied override |
| `ProductWithdrawalExpensesAndLiabilityIncrdLimitFactor` | Increased-limits ("CSL ILF") factor — see rate-build-up table above; the closest GL analogue to CF's LOI factor |

Not applicable to this subline — no coinsurance factor, no limit-of-insurance-percentage table, and no deductible-by-location table are documented for any of these coverages; GL deductibles here are increased-limits-table lookups, structurally different from CF's flat deductible-percent tables.

---

## Premium-level tables

| Table | Used for | CW rows |
|---|---|---|
| `ProductWithdrawalMinPremium` | Product Withdrawal minimum premium | 1 (value = 0); table emptied entirely in CW 2027 |
| `LossOfElectronicDataMinPremium` | LoED minimum premium | 1 |
| `CyberIncidentLiabilityMinPremium` | Cyber Incident Liability minimum premium | 1 |

`PackageModFactor`, `ExperienceRatingModificationFactor`, `ExpenseModification`, `ModToUse`, and `PremiumDiscountCharge` all appear in the `SetFinalRate` / `SetLmtdProdsWithdrawalFinalRate` formulas — see "Not ERC tables" below for which of these are policy-level copies rather than filed rate tables. Not resolved in source docs — the gate does not state whether `PremiumDiscountCharge` itself resolves from a filed table or is a manual "refer to company" value; GATE-365 §4 row 3 says only that the participation/cut-off scenario that would set it is a **refer**, not a computed lookup.

---

## Statistical / subline tables

| Table | Used for | Rows | Readers |
|---|---|---|---|
| `SublineProductWithdrawal` | Subline stat code for 365 | 0 in every edition | **0 — orphan table**, the second one found in this project after `RailroadLossCost` |
| `CyberCoverageLimitStatCode` | Cyber stat code (mentioned only in the CA-withdrawal table list, GATE-365 §10) | not given | not given — table is emptied to 0 rows in `GL_CA_20241101_V01` |

Not resolved in source docs — the gate does not enumerate a stat-code table for LoED, Product Withdrawal Coverage A/B, or Limited Product Withdrawal beyond `SublineProductWithdrawal` and `CyberCoverageLimitStatCode`.

---

## Not ERC tables

`PackageModFactor` appears throughout the `SetFinalRate` formulas (Product Withdrawal Coverage A/B, Limited Product Withdrawal). Per the CF documentation pattern this is normally a policy-level user/schedule-rated input copied down rather than a filed rate table (`rul:Copy`, not `rul:Lookup`) — the GL gate does not confirm this mechanism explicitly for GL. Not resolved in source docs — whether `PackageModFactor`, `ExperienceRatingModificationFactor`, `ExpenseModification`, and `ModToUse` are copies (as in CF) or lookups in GL's ERC.

`ProductWithdrawalParticipationPercentage` is documented explicitly as **a new submission input**, applied at the coverage level after class premiums are rolled up (GATE-365 §9.2, item 3) — not a rate table.

---

## Verification

The gate's own verification, reused here rather than re-run (GATE-365 §6, §9.7, §10):

| Check | Result |
|---|---|
| `tests/verify_golden.py` | 80/80 unchanged — no Product Withdrawal, LoED, or Cyber premium in the golden case (fourth consecutive subline without an oracle) |
| `ProductWithdrawlFactor` vs manual Table 44.B.3.b | 3/3 exact, key axis included |
| `ProductWithdrawalExpensesFactor`/`…LiabilityFactor` vs manual | not independently re-verified in this gate beyond the misspelled table's crosscheck |
| Rate-driven groups in item 6 | 7 (2 Product Withdrawal + 4 LoED/Cyber + 1 Limited Product Withdrawal rating chain), 150 countrywide rules, plus the 43 supporting Limited Product Withdrawal rules across 4 more groups (54 total for that coverage) |
| Pairwise identical rule bodies across the 6 rate-driven groups | 0 |
| Tables with 0 rows and 0 readers | 1 (`SublineProductWithdrawal`) |
| State deviation surface (whole gate) | 17 rules, 9 jurisdictions (CA, IN, MO, MT, ND, NH, OK, TN, UT) |
| State deviation, Limited Product Withdrawal specifically | 1 of 51 (Texas — `InitializeRuleSet` + 2 stat-code lookups); 0 of 51 on the 11 rating rules themselves |
| `ProductWithdrawalExpensesAndLiabilityIncrdLimitFactor` state coverage | 0 of 10 countrywide editions carry rows; 51 of 51 jurisdictions do, 36 rows each — no coverage gap |
| California LoED/Cyber withdrawal | Confirmed via `SetCoverageOnPolicyIndicator` stubbed to `0` in all 6 groups; 13 tables emptied but unreached — not a defect (`40_referral_census.py` probe 6) |
| `verify_oi50.py` | Pins the Limited Product Withdrawal derivation (§9) |

This gate carries no direct file-existence/row-count crosscheck against the raw `.RateTable.csv` files comparable to CF's "26 tables confirmed present... by recursively resolving RunRule references" pass, and no equivalent of CF's later correction (header-only tables silently resolving to null). Not resolved in source docs — whether any table listed above is header-only (present but empty) at the countrywide level, apart from the ones explicitly reported as such (`ProductWithdrawalMinPremium` = 0 in CW 2027, `ProductWithdrawalExpensesAndLiabilityIncrdLimitFactor` = 0 rows CW by design, `SublineProductWithdrawal` = 0 rows always). Recommend running the equivalent of CF's row-count verification pass against `GL_CW_20231201_V03`'s `Rate Tables` directory before this port is relied on for actual rating.

---
