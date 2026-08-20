# Unmanned Aircraft — Required ERC Tables

**Source ERC package:** `GL_CW_20231201_V03`
**Line:** General Liability (GL), Countrywide, subline 370 — Unmanned Aircraft, Rule 37
**Derived from:** `UnmannedAircraft_RatingAlgorithms.md`, reformatted from `docs/gates/GATE-370-UNMANNED-AIRCRAFT.md`
**Documented:** 2026-08-20

This lists every ERC rate table named in GATE-370-UNMANNED-AIRCRAFT.md, resolved by tracing the
13-rule chain (`SetAggregateLimit` … `SetPremium`) across both Coverage A (BI/PD) and Coverage B
(PAI) rate-driven groups. Unlike the CF Basic Group I documentation this list draws, the gate doc
does **not** report a file-existence verification pass against the ERC package's `Rate Tables`
directory — table presence here is as stated in the gate doc's own row/state counts, not
independently re-verified against the filesystem.

**Every table on this subline is countrywide-only except two,** which carry a single Washington
override; see the notes column.

---

## Rate-build-up tables (state-or-CW keyed)

| Table | Used for | Keys |
|---|---|---|
| `UnmannedAircraftLimitedLiabilityBIPDLossCost` | Coverage A loss cost, banded by takeoff-weight ceiling | State\|CW (**0/51** states), weight band — 5 rows |
| `UnmannedAircraftLimitedLiabilityPAILossCost` | Coverage B loss cost, banded by takeoff-weight ceiling | State\|CW (**0/51**), weight band — 2 rows |
| (Prem/Ops LCM table, via `LookupPremOpsLCM`) | Coverage A & B LCM, borrowed from Premises/Operations | CW value **1** |
| (Prem/Ops claims-made table, via `LookupPremOpsClaimsMadeMultiplierAllOther`) | Claims-made multiplier — explicitly the Prem/Ops "All Other" variant | borrowed; NY overrides the calling rule (`SetClaimsMadeMultiplier`), not the table itself |
| `UnmannedAircraftOwnershipAndOperationBIPDRatingModifiers` | Coverage A ownership/operation modifier | State\|CW — 9 rows, 1/51 (**WA**) |
| `UnmannedAircraftOwnershipAndOperationPAIRatingModifiers` | Coverage B ownership/operation modifier | State\|CW — 9 rows, **0/51** |
| `UnmannedAircraftPrimaryPlaceOfOperationBIPDRatingModifiers` | Coverage A place-of-operation modifier | State\|CW — 9 rows, 1/51 (**WA**) |
| `UnmannedAircraftPrimaryPlaceOfOperationPAIRatingModifiers` | Coverage B place-of-operation modifier | State\|CW — 9 rows, **0/51** |
| `UnmannedAircraftUsageBIPDRatingModifiers` | Coverage A usage modifier | State\|CW — 12 rows, **0/51** |
| `UnmannedAircraftUsagePAIRatingModifiers` | Coverage B usage modifier | State\|CW — 12 rows, **0/51** |
| (aggregate limit table, via `unmannedAircraftAggregateLimitLookup`) | Aggregate limit | Not resolved in source docs — keys not stated |
| (Prem/Ops ILF table, via `LookupILFPremOps`) | Increased limits factor, borrowed from Prem/Ops | Not resolved in source docs — keys not stated; rule body is 15,857 characters |

All CW tables in this section follow the two-pass `FirstNonNull(state row, "CW" row)` pattern
elsewhere in this corpus; the gate doc does not explicitly re-state that pattern for this subline,
so treat this as **carried over from the CF documentation convention, not independently confirmed
here.**

---

## Coinsurance / LOI / deductible tables

Not applicable to this subline in the CF sense — General Liability rating has no coinsurance or
limit-of-insurance concept. The subline does carry deductible factor tables, reused from
Premises/Operations and applied to Coverage A only:

| Table | Used for | Notes |
|---|---|---|
| (Prem/Ops CSL deductible table, via `LookupDedFactorPremOpsCSL`) | Coverage A deductible factor | Combined Single Limit variant |
| (Prem/Ops BI deductible table, via `LookupDedFactorPremOpsBI`) | Coverage A deductible factor | Bodily Injury variant |
| (Prem/Ops PD deductible table, via `LookupDedFactorPremOpsPD`) | Coverage A deductible factor | Property Damage variant |

Not resolved in source docs — which of the three is selected under what condition, and their
keys/values. Coverage B's premium formula drops the deductible term, so none of these three apply
to Coverage B.

---

## Premium-level tables

| Table | Used for | Notes |
|---|---|---|
| `UnmannedAircraftMinPremium` | Minimum premium floor | 1 row, CW, **value 0** — E16 confirmed a fourth time on this subline |
| (governmental-units ILF variant, via `LookupGovernmentalUnitsPremisesOperationsIncreasedLimitsFactor`) | Replaces `SetAggregateLimit`/`SetILF` in 8 states | IN, MO, MT, ND, NH, OK, TN, UT — one deviation, eight filings |
| `PackageModFactor`, `ExperienceRatingModificationFactor`, `ExpenseModification`, `ModToUse` | Premium-level multipliers in `SetPremium` | Not resolved in source docs — whether these are filed rate tables or policy-level copied values (the gate doc lists them as multipliers without stating the ERC mechanism); see "Not ERC tables" caveat below |

---

## Statistical / subline tables

Not applicable to this subline — the gate doc does not reference any statistical reporting or
subline-code table for Unmanned Aircraft (unlike CF's `SublineBasicGroupI` family). No stat-code
rule is named anywhere in GATE-370-UNMANNED-AIRCRAFT.md.

---

## Not ERC tables

`PackageModFactor`, `ExperienceRatingModificationFactor`, `ExpenseModification`, and `ModToUse` are
policy-level inputs by their names and by analogy to the CF documentation's treatment of
`IRPMFactor`/`PackageModFactor` (those are confirmed via `rul:Copy`, not `rul:Lookup`, in the CF
corpus). **That confirmation does not exist for this GL subline** — GATE-370-UNMANNED-AIRCRAFT.md
does not state whether these four are `rul:Copy` policy-level values or filed `rul:Lookup` rate
tables. Flagged here as likely-not-ERC-tables by analogy only.

Not resolved in source docs — confirm the ERC mechanism for `PackageModFactor`,
`ExperienceRatingModificationFactor`, `ExpenseModification`, and `ModToUse` before treating this
section as settled.

---

## Verification

**Not resolved in source docs, and structurally different from the CF verification pass.** The CF
`BasicGroupI_ERC_Tables.md` document reports an explicit check that every listed table exists as a
`<TableName>.RateTable.csv` file in the ERC package's `Rate Tables` directory (and a follow-up
correction when two of those files were found to be header-only). GATE-370-UNMANNED-AIRCRAFT.md
contains **no equivalent file-existence or row-count-in-the-actual-CSV check** — its row counts and
state-filing counts (reproduced in the tables above) come from the gate's own analysis, not a
directory listing.

What GATE-370-UNMANNED-AIRCRAFT.md **does** verify exhaustively, and which substitutes for a
CF-style completeness check on this subline:

- **Usage modifier tables**, both coverages: 24/24 cells cross-checked against manual Table 37.E,
  cell for cell, both directions (§0).
- **Ownership & Operation and Primary Place of Operation modifier tables**, both coverages: zero-cell
  counts confirmed (3+3 and 2+2 respectively — 18 of 60 cells across all three axes and both
  coverages are referral markers) (§7a).
- **Referral guard coverage**: 0 `DoMessage*` guards found on any of the three modifier axes,
  checked across both rate-driven groups (§0, §7).
- **State filing counts**: countrywide-only for every table except the two WA overrides, checked
  per table (§5).

No independent re-verification of these counts against the raw ERC package was performed in
producing this document — they are carried forward from the gate doc as-is.

---
