# Stop Gap - Employers Liability Coverage - Required ERC Tables

**Source ERC package:** state-filed Rule A2 -- no ISO subline code, no countrywide rating package
**Line:** General Liability (GL), state-only Additional Rule A2, filed in 5 monopolistic-fund
jurisdictions -- ND, OH, PR, WA, WY
**Derived from:** `StopGap_RatingAlgorithms.md`, reformatted from
`docs/gates/GATE-STOPGAP-EMPLOYERS-LIABILITY.md`
**Documented:** 2026-09-02

This lists every ERC rate table named in GATE-STOPGAP-EMPLOYERS-LIABILITY.md, resolved by tracing
the classification-level `ErcRate` override chain (`SetStopGapIncrdLimitFactor` ->
`SetStopGapFactor` -> `SetStopGapFinalRate` -> `SetStopGapPremium`) and the policy-level
`SetPremium` aggregator, confirmed directly against the raw ERC package tree at
`C:\Projects\ISO_ERC_Files\General_Liability\{ND,OH,PR,WA,WY}\` -- **not** against the project's
precomputed knowledge base, which omits this coverage entirely (see "Verification" below).

**Every rate-bearing table on this coverage is state-only.** The countrywide layer carries a
header-only, 0-row `StopGapRate` table at every edition checked (20261001 V01, 20270401 V01,
20270401 V02) and nothing else -- there is no countrywide fallback for the factor lookup.

---

## Rate-build-up tables (state-only)

| Table | Used for | Keys |
|---|---|---|
| `StopGapRate` (via `LookupStopGapRate`) | Stop Gap rate factor -- 0.03 (Manufacturing/Processing, Contracting/Servicing) or 0.02 (Buildings/Premises, Mercantile, Miscellaneous) | `StateCode`, `ClassificationType` -- 5 rows per state, **5/5 of the named states populated, 0/51 countrywide** |
| (Premises/Operations ILF table, via `LookupILFPremOpsWithArgs`) | Increased Limits Factor, borrowed from Prem/Ops and called with Stop Gap's own submitted limits | `assignment` (Prem/Ops ILTA table assignment), `accidentLimit`, `diseaseLimit` -- keys and full row values **not resolved in source docs** (borrowed rule, not traced independently here) |
| (Premises/Operations classification coverage, via `GeneralLiabilityClassificationPremOpsCoverage/BaseRate`) | Base rate multiplied by the Stop Gap factor | Not a lookup table -- an already-computed sibling-coverage value read directly off the same classification node (the E18 cross-coverage dependency) |
| (Premises/Operations exposure, via `PremOpsExposureCalc`) | Units of exposure multiplied by the Stop Gap final rate | Not a lookup table -- an already-computed sibling-coverage value, same classification node |

All state tables in this section follow the two-pass `FirstNonNull(state row, "CW" row)` pattern
used elsewhere in this corpus, but **the CW pass can never succeed here** -- `StopGapRate` is 0
rows countrywide at every edition checked, confirmed directly rather than assumed
(GATE-STOPGAP-EMPLOYERS-LIABILITY.md Section 5).

---

## Coinsurance / LOI / deductible tables

Not applicable to this coverage -- General Liability rating has no coinsurance or limit-of-
insurance concept, and Stop Gap carries no deductible mechanism of its own (it inherits nothing
comparable to drone's borrowed Prem/Ops deductible tables). The manual's only limit-shaped
mechanic is the two Bodily Injury limit fields that gate the algorithmic vs. refer-to-company
branch (see Premium-level tables, below).

---

## Premium-level tables

| Table | Used for | Notes |
|---|---|---|
| `DomainStopGapBIByAccidentOrByDisease` | Legal values for `LimitBodilyInjuryByAccident`, `LimitBodilyInjuryByDiseaseEachEmployee`, `LimitBodilyInjuryByDiseaseAggregate` | 13 whole-dollar bands, $25,000-$10,000,000 (ND); not re-checked for OH/WA/WY/PR -- **not resolved in source docs** whether the band set is identical across all five |
| `PackageModFactor`, `ExperienceRatingModificationFactor`, `ModToUse` | Premium-level multipliers in `SetStopGapFinalRate` and in both branches of the policy-level `SetPremium` | Not resolved in source docs -- whether these are filed rate tables or policy-level copied (`rul:Copy`) values; same open question `UnmannedAircraft_ERC_Tables.md` records for the identically-named fields there |
| `ManualPremium` | Submission-supplied premium used in the refer-to-company branch (limits differ) | **Not a lookup table at all** -- a plain input DataDef the submission must populate for Branch B to produce a non-zero premium. No ERC computation feeds it |

---

## Statistical / subline tables

| Table | Used for | Keys |
|---|---|---|
| `StopGapStatCode` (via `LookupStopGapStatCode`) | Statistical reporting code per classification | `StateCode`, `ClassificationType` -- 5 rows in ND, mapping the same 5 classification types onto exactly 2 codes: `92400` (Manufacturing Or Processing, Contracting Or Servicing) and `92405` (the other three) |
| `StopGapManProcContServRiskStatCode` | Declared, unread | 0 rows in ND -- no rule reads this table (checked by name against the full `SetStopGap*`/`LookupStopGap*` rule set) |
| `StopGapRisksOtherThanManProcContServRiskStatCode` | Declared, unread | 0 rows in ND -- same as above |

Not resolved in source docs -- row counts for `StopGapStatCode` and the two orphan tables in
OH/WA/WY/PR; only ND was checked directly for this section.

---

## Not ERC tables

`PackageModFactor`, `ExperienceRatingModificationFactor`, and `ModToUse` are policy-level inputs
by their names and by analogy to the CF documentation's treatment of `IRPMFactor`/`PackageModFactor`
(confirmed via `rul:Copy`, not `rul:Lookup`, in the CF corpus). **That confirmation does not exist
for this GL coverage** -- neither this gate nor `GATE-370-UNMANNED-AIRCRAFT.md`, which names the
same four fields, states the ERC mechanism behind them. Flagged here as likely-not-ERC-tables by
analogy only.

`ManualPremium` is unambiguously not an ERC table -- it is a plain submission-level input field
consumed directly by the policy-level `SetPremium` rule's refer-to-company branch, with no lookup
or computation feeding it anywhere in the traced Stop Gap chain
(GATE-STOPGAP-EMPLOYERS-LIABILITY.md Section 2).

Not resolved in source docs -- confirm the ERC mechanism for `PackageModFactor`,
`ExperienceRatingModificationFactor`, and `ModToUse` before treating that part of this section as
settled.

---

## Verification

**This coverage was located entirely by reading the raw ERC package tree, not by trusting a
derived index.** The project's precomputed knowledge base
(`Agentic/iso-erc-expert/knowledge/jurisdictions.json`) lists `resolved_sublines` for ND, OH, PR,
WA, and WY, and **Stop Gap does not appear in any of the five lists.** That absence was checked
and traced to its cause rather than accepted at face value: the knowledge extraction's pattern
appears to key on `GeneralLiabilityClassification<Name>CoverageRules`-shaped file names, and Stop
Gap's rule file is named
`GeneralLiabilityStopGapEmployersLiabilityCoverageEndorsementPolLvlRules` -- a policy-level
("PolLvl") shape the extraction pattern does not match. **The tables and rules documented above
were confirmed present by direct filesystem search and direct XML/CSV reading, not by the
knowledge base tool.** (GATE-STOPGAP-EMPLOYERS-LIABILITY.md Section 0.)

What was verified directly, per table:

- `StopGapRate`: read in full (all 5 rows) for **all five** states (ND, OH, WA, WY, PR) at the
  newest package on disk for each -- **25/25 cells match the manual's two-bucket table** (Section
  4 of the gate doc).
- `StopGapStatCode`: read in full for **ND only** -- 5 rows, maps onto the same two-bucket
  boundary a second, independent way.
- `StopGapManProcContServRiskStatCode`, `StopGapRisksOtherThanManProcContServRiskStatCode`:
  confirmed 0 rows for **ND only**; not re-checked for the other four states.
- Countrywide `StopGapRate`: confirmed 0 rows at **three** countrywide editions (20261001 V01,
  20270401 V01, 20270401 V02) -- not exhaustive across every countrywide edition on disk.
- WV (negative control, not one of the five rating states): confirmed to carry only
  `StopGapStatCodeDef`/`StopGapStatCode`, at every edition from 2021-08-01 through 2027-04-01, with
  no Rules file and no `StopGapRate` table -- corroborates rather than narrows the five-state scope.

No independent re-verification of row counts against a second reading pass was performed beyond
what is listed above; the counts in this document are as read directly from the files named,
during the single research pass that produced this document.
