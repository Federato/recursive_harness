# Premises/Operations — Required ERC Tables

**Source gate:** `docs/gates/GATE-334-PREMISES-OPERATIONS.md` (subline 334)
**Also drawn from:** `docs/erc/03-RATING-STRUCTURE.md` §4.2, `docs/rating-engine/03-SUBLINE-COVERAGE-PLAN.md` §3.1.1
**Line:** General Liability (GL), Subline `334` — Premises/Operations
**Derived from:** `PremisesOperations_RatingAlgorithms.md`
**Measured on:** CW `GL CW 20231201 V03` package and state `GL_OK 20250601 V01` package (the golden
case's resolved parent and jurisdiction)
**Documented:** 2026-08-20

This is a reformat of gate content, not new research — every table below is one the gate document
named while tracing `ErcSetRatesAndFactors` (classification and coverage level) down to its
`Lookup` calls. Row counts and layer classifications ("state only" / "countrywide only" / "both")
are the gate's own measurements, not re-derived here.

All tables follow the two-pass `FirstNonNull(state row, "CW" row)` lookup pattern — a state can
override any of these with its own row, but if it doesn't, a CW row is required for the lookup to
resolve.

---

## Rate-build-up tables (state-or-CW keyed)

| Table | Used for | Keys |
|---|---|---|
| `PremOpsLossCost` | Premises/Operations loss cost, per class and territory | State, `PremisesOperationsTerritory`, ClassCode |
| `ILFPremOps` | CSL increased-limits factor | State, ILF table#, occurrence limit, general aggregate limit |
| `PremOpsIncrdLimitTableAssignment` | Class → ILF table number (or `"Refer To Co."`) | State, ClassCode |
| `PremOpsHomogeneityIndex` | Homogeneity index | State, ClassCode |
| `PremOpsELP` | Expected loss potential (fallback rate source when loss cost is 0) | State, ClassCode |
| `PremOpsSizeOfRiskLossCost` | Loss cost when size-of-risk rating applies | Not resolved in source docs — key list beyond "size-of-risk applies" not given |
| `PremOpsLCM` | Loss cost multiplier | State, `"Y"` |
| `BringYourOwnAlcoholExclusionFactor` table | BYOA liquor exclusion factor | Not resolved in source docs — only the gating condition (class `16905`/`16906` + endorsement presence) is given, not the table's own key columns |
| `MedPayFactor` (CW 2023 and earlier) | Medical payments ILF adjustment | CW, ClassCode |
| Increased med-pay limit factor table (CW 2027, name not given verbatim in source) | Medical payments ILF adjustment, CW 2027 | Not resolved in source docs — the gate doc names the rule `LookupIncreasedMedPayLimitFactor` but not the table name or key columns |
| `PremOpsClaimsMadeMultiplier` table | Claims-made year multiplier | Year (capped at 5) — state/CW scope not specified in source |
| `PremOpsSizeOfRiskRelativityTableAssignment` | Class → size-of-risk relativity table | ClassCode |
| `PremOpsSizeOfRiskRelativity` | Preliminary size-of-risk relativity | Not resolved in source docs — key columns beyond "class-keyed" not itemized |
| Size-of-risk min/max relativity tables | Clamp bounds for size-of-risk relativity | ClassCode |
| `ClassificationType` | Class code → classification type (Mercantile / Manufacturing / …) | ClassCode |

---

## Coinsurance/LOI/deductible tables

Premises/Operations has no coinsurance or limit-of-insurance concept analogous to CF Building — GL
uses increased-limits factors (ILF) in that role, tabled above. Deductible tables:

| Table | Used for | Keys |
|---|---|---|
| `DedFactorPremOpsCSL` | Combined-limits deductible factor | State, ILF table#, deductible |
| `DedFactorPremOpsBI` | Bodily-injury-only deductible factor | Not resolved in source docs beyond "BI" key dimension |
| `DedFactorPremOpsPD` | Property-damage-only deductible factor | Not resolved in source docs beyond "PD" key dimension |

**Sentinel, confirmed in the countrywide tables above:** every "Per Claim" deductible row is `0`
(`"CW",3,"250 Per Claim",0` … `"100,000 Per Claim",0`) while every corresponding "Per Occurrence"
row carries a real factor (`0.005`, `0.01`, `0.013`, `0.018`, …). The factors are unpublished,
encoded as `0`, and the only guard is the validation rule
`DoMessageMustEnterPremOpsBIPDDeductibleFactorOverride` — not a rating-chain check.
*(per GATE-334-PREMISES-OPERATIONS.md § 7 item 2)*

`PremOps{BI,BIPD,PD}DeductibleFactorOverride` are user-supplied inputs (default `0.0`), not table
lookups — see "Not ERC tables" below.

---

## Premium-level tables

| Table | Used for | Keys |
|---|---|---|
| `PremOpsMinPremium` | Minimum premium | Table# — **CW only, 3 rows, all `0`** in the measured package |

---

## Statistical/subline tables

Not resolved in source docs. Unlike the CF Building document (which names `SublineBasicGroupI` and
its exclusion variants explicitly), neither `GATE-334-PREMISES-OPERATIONS.md` nor the
`03-RATING-STRUCTURE.md` / `03-SUBLINE-COVERAGE-PLAN.md` excerpts read for this subline name a
statistical-code or subline-reporting table for 334 specifically. `ClassificationType` (listed
above under rate-build-up, since it also feeds `SetClassificationType`) is the only table in the
source material that reads as reporting-adjacent, and it is load-bearing for classification, not
purely statistical.

---

## Not ERC tables

The following are policy-level or rule-computed inputs, not filed rate tables — copied down or
defaulted, not looked up in a `RateTable.csv`:

- `PackageModFactor`, `ExperienceRatingModificationFactor`, `ExpenseModification`, `ModToUse` —
  default `1.0` (decisions E5/E10 per the gate doc).
- `AdditionalInterestFactor` — input, else `1.0`; **computed by `SetAdditionalInterestFactor` and
  read by no rule in either edition's premium chain.** Recorded as an open item (E11), not a rate
  table.
- `PremOps{BI,BIPD,PD}DeductibleFactorOverride` — user overrides, default `0.0`.
- `PremOpsIncrdLimitTableAssignmentOverride` — user override, substituted when the assignment table
  returns the literal `"Refer To Co."`.
- `LCM` (`PremOpsLCM`) is technically resolved through a `Lookup` rule
  (`LookupPremOpsLCM(state, "Y")`), so it is listed under rate-build-up tables above; but the
  golden case holds it at `1.0` "by decision E9" rather than by tracing a filed row. **Not resolved
  in source docs** — whether `LookupPremOpsLCM` actually returns a filed table value in any state
  package, or whether E9 is an engine-level placeholder because no such row exists, is not stated.

*(per GATE-334-PREMISES-OPERATIONS.md § 1, § 3, § 4)*

---

## Verification

Row counts and layer (state / countrywide / both) were measured directly by
`GATE-334-PREMISES-OPERATIONS.md` §5 against the CW `GL CW 20231201 V03` package and the state
`GL_OK 20250601 V01` package:

| Table | Countrywide | Oklahoma | Layer |
|---|---|---|---|
| `PremOpsLossCost` | **0 rows** (header only) | **3,564** | **state only** |
| `ILFPremOps` | **0 rows** (header only) | **432** | **state only** |
| `PremOpsIncrdLimitTableAssignment` | **0 rows** (header only) | **1,196** | **state only** |
| `PremOpsHomogeneityIndex` | — | 1,188 | state |
| `PremOpsELP` | — | 1,188 | state |
| `MedPayFactor` | 1,188 | absent | **countrywide only** |
| `DedFactorPremOpsCSL` / `BI` / `PD` | 93 each | absent | **countrywide only** |
| `PremOpsMinPremium` | 3 (all `0`) | absent | **countrywide only** |
| `ClassificationType` | populated | absent | **countrywide only** |

**"Table exists" and "table has a usable row" are different claims, and only the second is
load-bearing.** Three of the tables 334 depends on are **header-only at the countrywide level** —
`PremOpsLossCost`, `ILFPremOps`, and `PremOpsIncrdLimitTableAssignment` carry zero CW rows. Reading
them as populated at the countrywide layer yields a `0` loss cost, a `0` ILF, and a silent route
onto the ELP path — this is the primary-path instance of the same finding the CF corpus surfaced
for `BasicGroupIRate`/`BasicGroupIIRate` (both header-only, shared between Building and Personal
Property). The pattern generalizes: **the countrywide layer holds the method and the modifiers;
every number that varies by risk is state-supplied**, confirmed here on all three of 334's primary
rate-build-up tables and, at broader scope, on the corpus's other 24 universally state-overridden
tables (`03-RATING-STRUCTURE.md` §4.2).

The golden case (`GL_OK 20250601 V01`) reproduces the ISO-published `Premium = 976.00` exactly using
the Oklahoma-supplied rows for these three tables plus the countrywide `MedPayFactor` row — every
intermediate value traced to a named rule and a named table row, per
`GATE-334-PREMISES-OPERATIONS.md` §8.

*(per GATE-334-PREMISES-OPERATIONS.md § 5 and § 8)*

---
