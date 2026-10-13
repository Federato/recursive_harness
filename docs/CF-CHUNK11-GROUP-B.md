# Chunk 11, Group B: the four sub-coverages (C11-16 to C11-20)

**Predictions written 2026-09-22, before the run.** Script:
[`116_chunk11_groupB_subcoverages.py`](../scripts/cf/116_chunk11_groupB_subcoverages.py).
Base: the golden case's Leasehold Interest structure
([`CF-CHUNK11-GOLDEN-CASE.md`](CF-CHUNK11-GOLDEN-CASE.md)): Oregon, Frame,
class 0951, 120 / 108 months remaining, 10%.

## In plain English first

Leasehold Interest has four parts, and **only one of them is discounted**.
Tenants Lease is the value today of a stream of monthly savings, so it goes
through the annuity. The other three are money already spent or owed:
bonus payments, improvements, prepaid rent. They are simply the monthly
amount × months left. The four are rated **separately**, each on its own
amount. A total is added up, but nothing is priced off it.

## What the rules say, read before any run

1. **Three of the four sub-coverages skip the annuity entirely.**
   `SetBonusPayments…`, `SetImprovAndBetterments…` and `SetPrepaidRent…` are
   each `monthly × NumOfMonthsRemaining` (at inception and at expiration),
   averaged. No `AnnuityConstant`, no `DiscFactor`. Consequences: they are
   **independent of `PercentInterest`**, and the average is always
   `monthly × (120 + 108) / 2 = monthly × 114`, a whole number, so **these
   three can never land on a rounding tie**. Tenants Lease can.
2. **The 20 grid files are the same file four times.** Renaming each
   sub-coverage's net and gate fields to placeholders makes the Basic Group I,
   Basic Group II, Broad and Special files byte-identical across the four
   sub-coverages. The Earthquake files differ only in the **order** of the
   three `And` operands in the gate, which doesn't change behaviour. So the
   "separate machinery" is entirely in the parent file's net rules, not in
   the grid.
3. **Special without a Theft Exclusion prices at $0, by ISO's own rules.**
   `SetSpecialCauseOfLossAdjustment` = `SpecialRate × SpecialTheftExclusionFactor`.
   That factor is looked up only when `CauseOfLossToUse = Special` **and**
   `SpecialTheftExclusionIndicator = 1` **and** `ApartmentCondoIndicator` is
   set. Otherwise it is **`0.0`, not `1.0`**. And
   `SpecialTheftExclusionIndicator` is 1 only if a
   `CommercialPropertyTheftExclusion` record exists. So a Special-form
   Leasehold Interest **with theft covered**, the ordinary case, prices at
   $0. ISO runs the same rule, so ISO should return $0 too. It looks like a
   filing defect, not an engine one, and it needs a live ISO call (C11-22)
   to confirm. The Special rate table itself is named *IncldgTheft*
   ("including theft"), which makes the zero harder to read as intended.
4. **Broad does not layer onto Special.** Each cell's gate is
   `CauseOfLoss = "Broad"` or `= "Special"`, so a Special risk gets
   BGI + BGII + Special, never Broad. `LeaseholdInterestBroadSpecialRate` is
   read only by `SetBroadRate`.
5. **LI's Earthquake cell reads the Structure's own `EQCauseOfLossAdjustment`**
   (C11-21's question, answered by reading). The one EQ factor that reads
   `CovType`, `SetPctOfMasonryVeneerEQFactor`, skips its lookup for
   `CovType = Leasehold Interest` and defaults to 1.0.
6. **`TotCoveredLeaseholdIntNet` is a sum, and nothing rates off it.** Every
   premium reads its own sub-coverage net.

## Inputs

Each scenario is the golden structure plus:

| Field | Value | Net (avg of inception/expiration) |
|---|---|---|
| `TenantsGrossLeaseholdInt` | 1,500 | annuity → **111,958** (golden case) |
| `BonusPaymentsMonthlyLeaseholdInt` | 200 | 200 × 114 = **22,800** |
| `ImprovementsAndBettermentsMonthly` | 300 | 300 × 114 = **34,200** |
| `PrepaidRentMonthly` | 400 | 400 × 114 = **45,600** |

Rates on this structure: BGI **0.239**, BGII **0.027** (chunks 1–2);
Broad **0.023** (`LeaseholdInterestBroadSpecialRate[CW]("Frame")`);
Special **round(0.047 × 0.86, 3) = 0.040** (`SpecialFormIncldgTheft…[CW]("Frame","No")`
× `SpecialLeaseHoldTimeElementTheftExclusionFactor[CW]("No")`. Class 0951 is
not one of the 13 apartment/condo codes, so `ApartmentCondoIndicator = "No"`);
EQ **round(0.009 × 1.04, 3) = 0.009** (`EQLossCostBldg[OR]("A1","1")` ×
`BCEGEarthquakeFactor[OR]("4")`, all other EQ factors 1.0).

Each premium is `round(net/100 × rate)`, × multipliers of 1.0. No product
lands on a half.

## Predictions

| Scenario | Tenants | Bonus | Improvements | Prepaid | LI total |
|---|---|---|---|---|---|
| **S1** Basic, all four | BGI 268, BGII 30 | 54, 6 | 82, 9 | 109, 12 | **570** |
| **S2** Broad, all four | + Broad 26 | + 5 | + 8 | + 10 | **619** |
| **S3** Special + Theft Exclusion record | + Special 45 | + 9 | + 14 | + 18 | **656** |
| **S4** Special, **no** Theft Exclusion | Special cell ON, **$0** | $0 | $0 | $0 | **570** |
| **S5** Basic + EQ elected | + EQ 10 | + 2 | + 3 | + 4 | **589** |
| **S6** Bonus only, **`PercentInterest` removed** | off | 54, 6 | off | off | **60** |
| **S7** Improvements only | off | off | 82, 9 | off | **91** |
| **S8** Prepaid Rent only | off | off | off | 109, 12 | **121** |

Also predicted:

* **S1:** `TotCoveredLeaseholdIntNet` = 111,958 + 22,800 + 34,200 + 45,600 =
  **214,558**. If premiums were rated off the total, Tenants BGI alone would
  be round(2,145.58 × 0.239) = 513, not 268.
* **S4:** `SpecialTheftExclusionFactor` = **0.0**, `SpecialCauseOfLossAdjustment`
  = **0.0**, `SpecialRate` = 0.047 (the rate is found; the factor zeroes it).
* **S6:** Bonus prices normally with no interest rate at all. Its net doesn't
  depend on the annuity.
* **S9 (C11-18):** a structure with `CovType = "Improvements and
  Betterments"` (Building's own literal, per `DomainCovTypeBldg`) **deletes**
  a submitted LI record, because the attach gate requires `CovType =
  Leasehold Interest`. The two "Improvements" concepts can't coexist on
  one structure, and no LI file contains the literal
  `Improvements and Betterments`.
