# Loss Of Electronic Data Coverage (CG 04 37 / CG 04 71 / CG 04 95) - Required ERC Tables

**Source ERC package:** countrywide `GL CW 20270401 V01`, cross-checked live/unmodified against
**TX** (`GL_TX 20270401 V01`) and **IL** (`GL_IL 20270401 V05`).
**Derived from:** `LossOfElectronicData_RatingAlgorithms.md`, by direct ERC XML/CSV tracing --
**not** a reformat of `GATE-365-WITHDRAWAL-LOED-CYBER.md`, which left these table identities
unresolved for LoED specifically.
**Documented:** 2026-09-02.
**Reconciled against the built engine:** 2026-10-02 (commit `630ba2f`) — every table below was hit (or its miss/fallback observed) in offline engine traces at TX@20270401 (CW 20270401 V01), IL@20270401 (CW V02), TX@20261002 (CW 20231201 V03), IL@20261002 and NY@20261002 (CW 20260101 V01), with CG 04 37 / CG 04 95 records added to the base submission; row counts re-read from the CSVs in each CW edition.

This lists every ERC table that actually feeds the Loss Of Electronic Data rate/premium chain,
resolved by tracing `SetLossOfElectronicDataLimit -> SetILF -> SetDeductibleFactor -> SetFinalILF
-> SetAdjustedBaseRate -> SetHazardGrade -> SetLossOfElectronicDataFactor -> SetFinalRate ->
SetPremium -> SetPremiumIndicator` directly in the raw ERC package tree. The same tables serve
CW 20231201 V03, 20260101 V01, 20261001 V01, 20270401 V01 and V02; only the hazard-grade row counts
and the ILF key spelling (" CSL" suffix before 2027) differ by edition.

---

## Rate-build-up tables

| Table | Used for | Keys | Rows |
|---|---|---|---|
| `ILFPremOps` **(not owned by LoED -- Prem/Ops' own host table)** | Increased Limits Factor, Prem/Ops-hosted classifications | `StateCode`, `IncreasedLimitsTableAssignmentPremOpsFinal` (integer, from `FinalPremOpsIncrdLimitTableAssignmentInt`), `EachOccurrenceLimit` (= LoED Limit), `GeneralAggregateLimit` | 216 rows, TX (state-filed); engine hit `['TX', 3, '200,000', '2,000,000'] -> 1.28` at TX@20270401, `['TX', 3, '200,000 CSL', '2,000,000 CSL'] -> 1.28` at TX@20261002 |
| `ILFProds` **(not owned by LoED -- Prod/CompOps' own host table)** | Increased Limits Factor, Prod/CompOps-hosted classifications | `StateCode`, `IncreasedLimitsTableAssignmentProdsCompldOpsFinal` (letter), LoED Limit, `ProdsCompldOpsAggregateLimit` | 216 rows, TX; engine hit `['TX', 'B', '200,000', '2,000,000'] -> 1.23` |
| `LossOfElectronicDataPremOpsHazardGrade` | Hazard grade, per class code, Prem/Ops host | `StateCode`, `ClassCode` | 1,163 (CW 2027) / 1,188 (CW 20231201, 20260101, 20261001); metadata `BureauRuleNumber40F`, cites circulars `CircularLIGL2023089`/`CircularLIGL2025210` |
| `LossOfElectronicDataProdsCompldOpsHazardGrade` | Hazard grade, per class code, Prod/CompOps host | same shape | 1,163 (CW 2027) / 1,188 earlier |
| `LossOfElectronicDataPremOpsFactorCG0437` | Coverage factor, Prem/Ops host, CG 04 37 **or CG 04 95** attached | `StateCode`, `HazardGrade` | 4 (CW: 0.001 / 0.003 / 0.005 / 0.007 -- matches manual Table 40.C exactly) |
| `LossOfElectronicDataPremOpsFactorCG0471` | Coverage factor, Prem/Ops host, CG 04 71 attached | `StateCode`, `HazardGrade` | 4 (CW: 0.0008 / 0.0024 / 0.004 / 0.0056 -- matches manual Table 40.D exactly) |
| `LossOfElectronicDataProdsCompldOpsFactorCG0437` | Coverage factor, Prod/CompOps host, CG 04 37 or CG 04 95 | `StateCode`, `HazardGrade` | 4, identical values to the PremOps pair |
| `LossOfElectronicDataProdsCompldOpsFactorCG0471` | Coverage factor, Prod/CompOps host, CG 04 71 | `StateCode`, `HazardGrade` | 4, identical values to the PremOps pair |

All eight LoED-owned tables above resolve to **CW unmodified in all 51 jurisdictions checked at
2027-04-01** -- no state-filed override was located for any of them, including TX and IL. NY's 2024
packages carry header-only (0-row) copies of both hazard-grade tables; the state-first lookup misses
and falls through to CW (engine-confirmed, NY@20261002).

Host tables consumed but **not owned by this coverage** (documented here because
`SetAdjustedBaseRate` reads them directly, per the algorithm doc's Step 5 -- see the host
subline's own documentation for their filed status):

| Table / value | Owner | Consumed by |
|---|---|---|
| `PremOpsLossCost`, `PremOpsELP` (used when the loss cost is 0), `LCM`, `ClaimsMadeMultiplier`, `PremOpsSizeOfRiskFinalRelativity` | Premises/Operations (334) | `SetAdjustedBaseRate`, Prem/Ops-hosted group -- E18, computed values not just tables |
| `BaseRate`, `ProdsCompldOpsSizeOfRiskFinalRelativity` | Products/Completed Operations (336) | `SetAdjustedBaseRate`, Prod/CompOps-hosted group -- E18; reads the host's finished base rate, not loss cost x LCM |
| `DeductibleFactor` / `PremOpsPDDeductibleFactor` (Prod/CompOps: `DeductibleFactor` / `ProdsCompldOpsPDDeductibleFactor`) | host classification group (either host) | `SetDeductibleFactor` (writes `DedFactor`) -- host's own computed value, not an independent LoED table |

---

## Coinsurance / LOI / deductible tables

GL casualty coverages carry no coinsurance or limit-of-insurance concept in the CF property sense.
LoED's only "deductible" mechanic is `SetDeductibleFactor` copying the **host's own** already-
computed deductible factor (`DeductibleFactor` when a BI/PD combined deductible applies, else
`PremOpsPDDeductibleFactor` / `ProdsCompldOpsPDDeductibleFactor`, else 0.0) into `DedFactor` -- not a
LoED-specific deductible table. See Rate-build-up tables above.

---

## Premium-level tables

| Table | Used for | Rows |
|---|---|---|
| `LossOfElectronicDataMinPremium` | Policy-level minimum-premium topper | 1 row, `('CW', 'Y', 0)` -- filed at $0, no state override in the 2027 corpus; the topper computes in every edition (engine: `MinPremium 0`, topper `Premium 0.0`) |
| (domain) `DomainLossOfElectronicDataLimit` | Legal values for `LossOfElectronicDataLimit` | 13 rows, $25,000-$10,000,000 -- exactly the 13 band limits `SetILF`'s refer-condition tests |

`PackageModFactor`, `ExperienceRatingModificationFactor`, `ExpenseModification`, and `ModToUse`
appear in `SetFinalRate` as premium-level multipliers. **Resolved:** the LoED files read them as
`FirstValue ... FromDataDef=../../../../../<field>` on the `GeneralLiability` record -- no `Lookup`
in either LoED file; `PackageModFactor` is a submission input (1.0 in the engine base payloads) and
`ExperienceRatingModificationFactor` / `ModToUse` are set by policy-level rules in
`GeneralLiabilityRules` (`SetExperienceRatingModificationFactor`, `SetModToUse`).

`ILFOverride` is **not a rate table** -- a submission-supplied field on each host's LoED coverage
record, consumed directly by `SetILF`'s refer-to-company branch when the (Limit, Aggregate) pair falls
in one of 13 filed "no factor exists" bands. No lookup or computation feeds it; when it is absent the
engine stops the rating INCOMPLETE (null reaches `SetFinalILF`'s subtraction).

---

## Statistical / subline tables

| Table | Used for | Notes |
|---|---|---|
| `CyberCoverageLimitStatCode` (via `SetLimitStatCode` -> `LookupCyberCoverageLimitStatCode`) | Limit statistical code per classification, both hosts | 130 rows CW, keyed `(StateCode, EachOccurrenceLimit, AggregateLimit)` -- shared with Cyber Incident Liability; engine hit `['CW', '200,000', '2,000,000'] -> '60'` |
| `TypeOfPolicyWithCyberIncidentLiabCoverage` | Policy-level `TypeOfPolicyStatCode` (`C5` CG 04 37, `C6` CG 04 71, `C7` Cyber, `C8` CG 04 95) | read by `GeneralLiabilityRules`, not by the LoED chain; engine wrote `C8` for a CG 04 95 policy |

---

## Not ERC tables

`PackageModFactor`, `ExperienceRatingModificationFactor`, `ExpenseModification`, and `ModToUse` are
policy-level values read by path, not looked up by this coverage (see Premium-level tables above).

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

**Located and traced by reading live, non-withdrawn state ERC packages (TX, IL)**, and on
2026-10-02 confirmed by offline engine runs that hit each table (see the reconciliation stamp).
LoED's file names match the extraction's expected `GeneralLiabilityClassification<Name>CoverageRules`
shape (unlike Stop Gap's `...EndorsementPolLvlRules` shape).

What was verified directly, per table:

- `ILFPremOps` / `ILFProds`: row count (216 each) and one sample row read directly from TX
  (`('TX', 1, '25,000', '50,000', 0.66)`); engine lookups reproduced at TX and IL, 2026 and 2027 keys.
- `LossOfElectronicDataPremOpsHazardGrade` / `...ProdsCompldOpsHazardGrade`: row counts (1,163
  each at CW 2027, 1,188 at CW 20231201/20260101/20261001); state-override absence checked across all
  51 jurisdictions' newest 2027-04-01 packages; NY's 0-row copies fall through to CW.
- `LossOfElectronicData{PremOps,ProdsCompldOps}Factor{CG0437,CG0471}`: all four values read
  directly and matched against manual Table 40.C/40.D exactly; state-override absence checked
  across all 51 jurisdictions; CG0437 hit by both a CG 04 37 and a CG 04 95 schedule in engine runs.
- `LossOfElectronicDataMinPremium`: single row read (`$0`); state-override absence checked across
  all 51 jurisdictions' 2027-04-01 packages.
- `DomainLossOfElectronicDataLimit`: 13 rows read directly, cross-checked against `SetILF`'s 13
  refer-band limits.
- 8-state rule-body deviation (IN, MO, MT, ND, NH, OK, TN, UT): both host files overridden in each
  state's 2027 packages; IN's override file read line-by-line (lines 245-301, 371-416) and engine-run
  (IN@20270401 executes `SetILF` from `GL_IN_20270401_V04`); the other seven not individually re-diffed.
- `ElectronicDataLiabilityClassCode` non-membership: confirmed via `grep -rl` across the CW GL
  Rules folder returning no readers.
- `gl_engine/`: zero hits for `LossOfElectronicData` or `LoED`, confirmed via `Grep`.

**Still not verified:** no golden-case oracle carrying a populated LoED block exists (same "no
oracle" finding as every other thin/newer coverage documented so far in this corpus) -- the engine
runs above confirm the engine executes the ERC chain as traced, not that ISO's own service returns the
same premium.
