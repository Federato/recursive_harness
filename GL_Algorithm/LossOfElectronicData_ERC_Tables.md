# Loss Of Electronic Data Coverage (CG 04 37 / CG 04 71 / CG 04 95) - Required ERC Tables

**Source ERC package:** countrywide `GL CW 20270401 V01`, cross-checked live/unmodified against
**TX** (`GL_TX 20270401 V01`) and **IL** (`GL_IL 20270401 V05`).
**Derived from:** `LossOfElectronicData_RatingAlgorithms.md`, by direct ERC XML/CSV tracing --
**not** a reformat of `GATE-365-WITHDRAWAL-LOED-CYBER.md`, which left these table identities
unresolved for LoED specifically.
**Documented:** 2026-09-02.

This lists every ERC table that actually feeds the Loss Of Electronic Data rate/premium chain,
resolved by tracing `SetLossOfElectronicDataLimit -> SetILF -> SetDeductibleFactor -> SetFinalILF
-> SetAdjustedBaseRate -> SetHazardGrade -> SetLossOfElectronicDataFactor -> SetFinalRate ->
SetPremium -> SetPremiumIndicator` directly in the raw ERC package tree.

---

## Rate-build-up tables

| Table | Used for | Keys | Rows |
|---|---|---|---|
| `ILFPremOps` **(not owned by LoED -- Prem/Ops' own host table)** | Increased Limits Factor, Prem/Ops-hosted classifications | `StateCode`, `IncreasedLimitsTableAssignmentPremOpsFinal`, `EachOccurrenceLimit` (= LoED Limit), `GeneralAggregateLimit` | 216 rows, TX (state-filed) |
| `ILFProds` **(not owned by LoED -- Prod/CompOps' own host table)** | Increased Limits Factor, Prod/CompOps-hosted classifications | same shape, `IncreasedLimitsTableAssignmentProdsCompldOpsFinal` | 216 rows, TX |
| `LossOfElectronicDataPremOpsHazardGrade` | Hazard grade, per class code, Prem/Ops host | `StateCode`, `ClassCode` | 1,163 (CW 2027); metadata `BureauRuleNumber40F`, cites circulars `CircularLIGL2023089`/`CircularLIGL2025210` |
| `LossOfElectronicDataProdsCompldOpsHazardGrade` | Hazard grade, per class code, Prod/CompOps host | same shape | 1,163 (CW 2027) |
| `LossOfElectronicDataPremOpsFactorCG0437` | Coverage factor, Prem/Ops host, CG 04 37 attached | `StateCode`, `HazardGrade` | 4 (CW: 0.001 / 0.003 / 0.005 / 0.007 -- matches manual Table 40.C exactly) |
| `LossOfElectronicDataPremOpsFactorCG0471` | Coverage factor, Prem/Ops host, CG 04 71 attached | `StateCode`, `HazardGrade` | 4 (CW: 0.0008 / 0.0024 / 0.004 / 0.0056 -- matches manual Table 40.D exactly) |
| `LossOfElectronicDataProdsCompldOpsFactorCG0437` | Coverage factor, Prod/CompOps host, CG 04 37 | `StateCode`, `HazardGrade` | 4, identical values to the PremOps pair |
| `LossOfElectronicDataProdsCompldOpsFactorCG0471` | Coverage factor, Prod/CompOps host, CG 04 71 | `StateCode`, `HazardGrade` | 4, identical values to the PremOps pair |

All eight tables above resolve to **CW unmodified in all 51 jurisdictions checked at 2027-04-01**
-- no state-filed override was located for any of them, including TX and IL.

Host tables consumed but **not owned by this coverage** (documented here because
`SetAdjustedBaseRate` reads them directly, per the algorithm doc's Step 5 -- see the host
subline's own documentation for their filed status):

| Table / value | Owner | Consumed by |
|---|---|---|
| `PremOpsLossCost`, `PremOpsELP`, `LCM`, `ClaimsMadeMultiplier`, `PremOpsSizeOfRiskFinalRelativity` | Premises/Operations (334) | `SetAdjustedBaseRate`, Prem/Ops-hosted group -- E18, computed values not just tables |
| `ProdsCompldOpsLossCost`, `ProdsCompldOpsELP`, `LCM`, equivalents | Products/Completed Operations (336) | `SetAdjustedBaseRate`, Prod/CompOps-hosted group -- E18 |
| `DeductibleFactor` / `PremOpsPDDeductibleFactor` | host classification group (either host) | `SetDeductibleFactor` -- host's own computed value, not an independent LoED table |

---

## Coinsurance / LOI / deductible tables

GL casualty coverages carry no coinsurance or limit-of-insurance concept in the CF property sense.
LoED's only "deductible" mechanic is `SetDeductibleFactor` copying the **host's own** already-
computed deductible factor (`DeductibleFactor` or `PremOpsPDDeductibleFactor`) -- not a
LoED-specific deductible table. See Rate-build-up tables above.

---

## Premium-level tables

| Table | Used for | Rows |
|---|---|---|
| `LossOfElectronicDataMinPremium` | Policy-level minimum-premium topper | 1 row, `('CW', 'Y', 0)` -- filed at $0, no state override in the 2027 corpus |
| (domain) `DomainLossOfElectronicDataLimit` | Legal values for `LossOfElectronicDataLimit` | 13 rows, $25,000-$10,000,000 -- exactly the band boundaries `SetILF`'s refer-condition tests against |

`PackageModFactor`, `ExperienceRatingModificationFactor`, `ExpenseModification`, and `ModToUse`
appear in `SetFinalRate` as premium-level multipliers. Not resolved in source docs -- whether these
are filed rate tables or policy-level copied (`rul:Copy`) values for this coverage specifically;
same open question `StopGap_ERC_Tables.md` records for the identically-named fields there.

`ILFOverride` is **not a rate table** -- a submission-supplied field consumed directly by
`SetILF`'s refer-to-company branch when the (Limit, Aggregate) pair falls in one of 14 filed "no
factor exists" combinations. No lookup or computation feeds it.

---

## Statistical / subline tables

| Table | Used for | Notes |
|---|---|---|
| (via `SetLimitStatCode`) | Statistical reporting code per classification | Table name not independently traced in this pass -- the rule exists and runs in the standard chain (`ErcSetStatisticalCodes`); not resolved in source docs beyond confirming the rule's presence and call order |

---

## Not ERC tables

`PackageModFactor`, `ExperienceRatingModificationFactor`, `ExpenseModification`, and `ModToUse` are
policy-level inputs by name and by analogy to the CF documentation's treatment of the same-shaped
fields (`rul:Copy`, not `rul:Lookup`) -- that confirmation was not independently re-run for this
coverage. Flagged as likely-not-ERC-tables by analogy only, same caveat `StopGap_ERC_Tables.md`
carries.

`ILFOverride` is unambiguously not an ERC table -- a plain submission-level input consumed by
`SetILF`'s refer-to-company branch, with `DoMessageILF` validating it is non-zero when required.

**Correction to a table initially thought to belong here:** `ElectronicDataLiabilityClassCode`
does **not** feed Loss Of Electronic Data. It belongs to the unrelated, fully refer-to-company
Rule 42 "Electronic Data Liability" coverage (`92900`/`92901`/`92909` classes,
`docs/rating-engine/03-SUBLINE-COVERAGE-PLAN.md` line 207) -- confirmed 0 rows and 0 readers
anywhere in the CW GL rule tree. Do not conflate the two "Electronic Data" coverages; they share a
name fragment and nothing else.

---

## Verification

**Located and traced entirely by reading live, non-withdrawn state ERC packages (TX, IL)** rather
than the project's precomputed knowledge base -- consistent with the caution
`StopGap_ERC_Tables.md` records about that index's blind spots, though LoED's file names *do*
match the extraction's expected `GeneralLiabilityClassification<Name>CoverageRules` shape (unlike
Stop Gap's `...EndorsementPolLvlRules` shape), so this coverage was not itself a knowledge-base
miss -- not independently re-checked here.

What was verified directly, per table:

- `ILFPremOps` / `ILFProds`: row count (216 each) and one sample row read directly from TX
  (`('TX', 1, '25,000', '50,000', 0.66)`); not re-verified against IL.
- `LossOfElectronicDataPremOpsHazardGrade` / `...ProdsCompldOpsHazardGrade`: row counts (1,163
  each) read at CW 2027; state-override absence checked across all 51 jurisdictions' newest
  2027-04-01 packages.
- `LossOfElectronicData{PremOps,ProdsCompldOps}Factor{CG0437,CG0471}`: all four values read
  directly and matched against manual Table 40.C/40.D exactly; state-override absence checked
  across all 51 jurisdictions.
- `LossOfElectronicDataMinPremium`: single row read (`$0`); state-override absence checked across
  all 51 jurisdictions' 2027-04-01 packages.
- `DomainLossOfElectronicDataLimit`: 13 rows read directly, cross-checked against `SetILF`'s
  refer-band boundaries.
- 8-state rule-body deviation (IN, MO, MT, ND, NH, OK, TN, UT): IN's override file read
  line-by-line (lines 245-301, 371-416); the other seven confirmed present and byte-length-matched
  only, not individually re-diffed.
- `ElectronicDataLiabilityClassCode` non-membership: confirmed via `grep -rl` across the CW GL
  Rules folder returning no readers.
- `gl_engine/`: zero hits for `LossOfElectronicData` or `LoED`, confirmed via `Grep`.

**Not verified in this pass:** whether an unlisted class code's hazard-grade lookup falls through
to a coded default (`"1"`, per the manual's prose) or to null -- would require either a live
`Kernel().rate(...)` test with an unlisted class code, or a person's confirmation. Recommend
running that test, or the equivalent of `tests/verify_golden.py`, before this coverage is relied on
for actual rating -- no golden-case oracle carrying a populated LoED block was located in this
pass (same "no oracle" finding as every other thin/newer coverage documented so far in this
corpus).
