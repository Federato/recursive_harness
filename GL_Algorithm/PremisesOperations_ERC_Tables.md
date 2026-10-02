# Premises/Operations — Required ERC Tables

**Source gate:** `docs/gates/GATE-334-PREMISES-OPERATIONS.md` (subline 334)
**Also drawn from:** `docs/erc/03-RATING-STRUCTURE.md` §4.2, `docs/rating-engine/03-SUBLINE-COVERAGE-PLAN.md` §3.1.1
**Line:** General Liability (GL), Subline `334` — Premises/Operations
**Derived from:** `PremisesOperations_RatingAlgorithms.md`
**Measured on:** CW `GL CW 20231201 V03` package and state `GL_OK 20250601 V01` package (the golden
case's resolved parent and jurisdiction)
**Documented:** 2026-08-20
**Reconciled against the built engine:** 2026-10-02 (commit `630ba2f`) — OK golden (OK@2025-08-01) and OK@2026-08-01 / 2026-10-02 / 2027-04-01 rated offline with every lookup key and returned row read from the engine trace; CW row counts re-counted in all five CW packages (20231201 V03, 20260101 V01, 20261001 V01, 20270401 V01, 20270401 V02) and OK row counts in `GL_OK_20250601_V01`, `GL_OK_20260801_V01` and `GL_OK_20270401_V04`.

This began as a reformat of gate content — every table below is one the gate document named while
tracing `ErcSetRatesAndFactors` (classification and coverage level) down to its `Lookup` calls. On
2026-10-02 the keys, the layer classifications and the row counts in "Verification" were
re-counted from the CSVs and checked against the lookups the engine actually performed; the
edition-scoped tables (pre-2027 vs CW 2027) are now marked. Corpus-wide claims beyond those
packages remain the gate's.

All tables follow the two-pass `FirstNonNull(state row, "CW" row)` lookup pattern — a state can
override any of these with its own row, but if it doesn't, a CW row is required for the lookup to
resolve.

---

## Rate-build-up tables (state-or-CW keyed)

| Table | Used for | Keys |
|---|---|---|
| `PremOpsLossCost` | Premises/Operations loss cost, per class and territory | State, `PremisesOperationsTerritory`, ClassCode — a **null** result (no state row, no CW row) is refused by the engine (OI-94); a filed `0` routes to ELP |
| `ILFPremOps` | CSL increased-limits factor | State, ILF table#, occurrence limit, general aggregate limit — limit values `"1,000,000 CSL"` pre-2027, `"1,000,000"` in the 2027-04-01 filings (OI-96/97) |
| `PremOpsIncrdLimitTableAssignment` | Class → ILF table number (or `"Refer To Co."`) | State, ClassCode |
| `PremOpsHomogeneityIndex` | Homogeneity index | State, ClassCode |
| `PremOpsELPText` | Rating-basis selector, read at classification level (`"Rate/Loss Cost Applies"`, `"Industry"`, `"Company"`, …) | State, ClassCode |
| `PremOpsELP` | Expected loss potential (fallback rate source when loss cost is 0) | State, ClassCode |
| `PremOpsSizeOfRiskLossCost` | Loss cost when size-of-risk rating applies | Not resolved in source docs — key list beyond "size-of-risk applies" not given. Not filed by every state: TX@2027-04-01 with size-of-risk on misses it and the engine refuses the risk (OI-94) |
| `PremOpsLCM` | Loss cost multiplier | State, `"Y"` — one CW row `"CW","Y",1` in every CW edition; OK files none |
| `BringYourOwnAlcoholExclusionFactor` table | BYOA liquor exclusion factor | Not resolved in source docs — only the gating condition (class `16905`/`16906` + endorsement presence) is given, not the table's own key columns |
| `MedPayFactor` (pre-2027 only) | Medical payments factor feeding `MedicalPaymentsCharge` | CW, ClassCode — 1,188 CW rows; header-only in CW 2027 |
| `IncreasedMedPayLimitFactor` (CW 2027 only) | Medical payments term folded into `FinalILF` | State/CW, ClassificationType, med-pay limit — 20 CW rows (5 classification types × `10,000`/`15,000`/`20,000`/`25,000`); not consulted at the `5,000` limit |
| `PremOpsClaimsMadeMultiplier` (pre-2027) / `ClaimsMadeMultiplierPremOps` (CW 2027) | Claims-made year multiplier | State/CW, year (capped at 5), ClassCode (pre-2027) / ClassificationType (CW 2027) — CW rows resolve in OK (year 5 → `0.92`) |
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
| `DedFactorPremOpsBI` | Bodily-injury-only deductible factor | State, ILF table#, deductible (engine trace: `['CW', 3, 'No Deductible']`) |
| `DedFactorPremOpsPD` | Property-damage-only deductible factor | State, ILF table#, deductible (same shape) |
| `DedFactorPremOpsPD` via `SetDedFactorPremOpsPD250PerClaim` (pre-2027 only) | the "250 Per Claim" PD cell, subtracted from the before-adjustment factor for spray painting and ten named classes | State, ILF table#, `"250 Per Claim"` |

All three are 93 CW rows in every CW edition checked, unchanged between pre-2027 and CW 2027.

**Sentinel, confirmed in the countrywide tables above:** every "Per Claim" deductible row is `0`
(`"CW",3,"250 Per Claim",0` … `"100,000 Per Claim",0` — 45 rows in `DedFactorPremOpsCSL`, all `0`,
in both CW 20260101 V01 and CW 20270401 V02) while every corresponding "Per Occurrence" row carries a
real factor (`0.008`, `0.015`, `0.022`, `0.029`, … on table 1). The factors are unpublished,
encoded as `0`, and the only guard is the validation rule
`DoMessageMustEnterPremOpsBIPDDeductibleFactorOverride` — not a rating-chain check.
*(per GATE-334-PREMISES-OPERATIONS.md § 7 item 2; re-counted 2026-10-02)*

`PremOps{BI,BIPD,PD}DeductibleFactorOverride` are user-supplied inputs (default `0.0`), not table
lookups — see "Not ERC tables" below.

---

## Premium-level tables

| Table | Used for | Keys |
|---|---|---|
| `PremOpsMinPremium` (pre-2027 only) | `MinimumPremium` → `MinPremium = round(MinimumPremium × FinalILF × AdditionalInterestFactor, 0)` → policy-level top-up | Table# — **CW only, 3 rows, all `0`** in CW 20231201 V03 / 20260101 V01 / 20261001 V01; header-only and read by no rule in CW 2027 |
| `SpecialCombinedMinPremium` (pre-2027 only) | `SpecialCombinedMinimumPremium` → `SpecialCombinedMinPremium` on the combined subline | `"Y"` — **CW only, 1 row, `0`**; header-only in CW 2027 |

On filed data both minimums are `0`, so the pre-2027 policy-level top-up
(`GeneralLiabilityPremOpsPremiumToReachMinCoverage`) is `0` on every run checked (golden case:
`CoveragePremium 976`, `MinPremium 0`). *(engine-verified 2026-10-02)*

---

## Statistical/subline tables

Not resolved in source docs. Unlike the CF Building document (which names `SublineBasicGroupI` and
its exclusion variants explicitly), neither `GATE-334-PREMISES-OPERATIONS.md` nor the
`03-RATING-STRUCTURE.md` / `03-SUBLINE-COVERAGE-PLAN.md` excerpts read for this subline name a
statistical-code or subline-reporting table for 334 specifically. `ClassificationType` (listed
above under rate-build-up, since it also feeds `SetClassificationType`) is the only table in the
source material that reads as reporting-adjacent, and it is load-bearing for classification, not
purely statistical.

Seen in the engine trace (2026-10-02, OK@2027-04-01), not in the gate: the statistical pass reads
the countrywide `Subline` table (`"CW", "Premises/Operations and Products/Completed Operations"` →
`334`) along with `LimitsIdentifier2` and `RatingIdentificationCode`. None affects premium.

---

## Not ERC tables

The following are policy-level or rule-computed inputs, not filed rate tables — copied down or
defaulted, not looked up in a `RateTable.csv`:

- `PackageModFactor`, `ExperienceRatingModificationFactor`, `ExpenseModification`, `ModToUse` —
  default `1.0` (decisions E5/E10 per the gate doc).
- `AdditionalInterestFactor` — input, else `1.0`; computed by `SetAdditionalInterestFactor`.
  **Pre-2027 it is read by `SetMinPremium` / `SetSpecialCombinedMinPremium`; in CW 2027 it is read
  by no rule** (both minimum rules were removed). Open item E11 applies to CW 2027 only.
  *(corrected 2026-10-02 from the rule XML of both branches)*
- `PremOps{BI,BIPD,PD}DeductibleFactorOverride` — user overrides, default `0.0`.
- `PremOpsIncrdLimitTableAssignmentOverride` — user override, substituted when the assignment table
  returns the literal `"Refer To Co."`.
- `LCM` (`PremOpsLCM`) is resolved through a `Lookup` rule (`LookupPremOpsLCM(state, "Y")`), so it
  is listed under rate-build-up tables above. **Resolved 2026-10-02:** the engine returns a filed
  value — the state row misses and the countrywide row `"CW","Y",1` answers (trace:
  `PremOpsLCM[Rate] keys=['CW', 'Y'] -> 1` from `GL_CW_20270401_V02`; same row in every CW edition).
  E9's `1.0` is that filed row, not an engine placeholder. A state that files its own LCM row would
  override it.

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
| `PremOpsHomogeneityIndex` | 0 rows (header only) | 1,188 | state only |
| `PremOpsELP` | 0 rows (header only) | 1,188 | state only |
| `PremOpsELPText` | 0 rows (header only) | 1,188 | state only |
| `PremOpsLCM` | 1 (`"CW","Y",1`) | absent | **countrywide only** |
| `MedPayFactor` | 1,188 | absent | **countrywide only** |
| `DedFactorPremOpsCSL` / `BI` / `PD` | 93 each | absent | **countrywide only** |
| `PremOpsMinPremium` | 3 (all `0`) | absent | **countrywide only** |
| `ClassificationType` | 1,188 | absent | **countrywide only** |

**Re-counted 2026-10-02** — the figures above hold for CW 20231201 V03, 20260101 V01 and 20261001 V01
and for `GL_OK_20250601_V01` and `GL_OK_20260801_V01`. Under the 2027-04-01 filings
(`GL_CW_20270401_V01`/`V02`, `GL_OK_20270401_V04`): `PremOpsLossCost` 3,489, `ILFPremOps` **216**
(limit keys lose the `" CSL"` suffix), `PremOpsIncrdLimitTableAssignment` / `HomogeneityIndex` /
`ELP` / `ELPText` 1,163 each; CW `ClassificationType` 1,163; `MedPayFactor` and `PremOpsMinPremium`
header-only; new CW `IncreasedMedPayLimitFactor` 20 rows. The header-only pattern for the three
primary 334 tables is unchanged in every edition.

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
`GATE-334-PREMISES-OPERATIONS.md` §8, and re-run through the engine on 2026-10-02 (`976`, policy
`7,839`). At OK@2027-04-01 the same three state tables plus CW `IncreasedMedPayLimitFactor`
(`CW, Manufacturing Or Processing, 10,000 → 1.007`) give `965`.

*(per GATE-334-PREMISES-OPERATIONS.md § 5 and § 8)*

---
