# Property chunk 11: the gate

**Leasehold Interest, all four sub-coverages, all five forms.** Filed
2026-09-22. **9 of 9, and all 24 tasks done.**

**In plain English.** Leasehold Interest is the one Property coverage whose
insured amount is *calculated* rather than typed in. It's the value today
of a tenant's below-market lease, worked out by discounting the monthly
advantage over the months left. Every step of that calculation has been
worked out by hand, run, and **confirmed against ISO's live service to the
digit**. Along the way the chunk found and, with the user's authorization,
fixed **four engine defects**, all of them in date and power arithmetic that
no earlier coverage had exercised.

| # | Gate point | | Evidence |
|---|---|---|---|
| 1 | A golden case rates end to end | ✅ | [`CF-CHUNK11-GOLDEN-CASE.md`](CF-CHUNK11-GOLDEN-CASE.md) / `114_chunk11_golden_case.py`. Tenants Lease, Oregon, 10%, lease 2025–2037: **$268 BGI + $30 BGII**, all 20 hand-derived intermediates matched. **ISO confirmation** (`122_…`, live): at the like-for-like date 2026-09-17, **$272 / $31 on both sides**, net 113,751 on both. At 2027-01-01 every annuity value matched ISO to the digit, and only the BGI base rate differed, because ISO serves a newer Oregon edition (OI-105). The first run exposed engine gap 1 (date comparison) and two silent submission traps |
| 2 | Every table's row count stated | ✅ | `120_…` C11-02. Six LI tables, identical in countrywide 2026 and 2023: 11 / 11 / 6 / 12 / 0 / 2. `SpecialFormExclgTheftLeaseHoldBaseRate` is dead (0 rows, no reader). None of the 46 states files any of them |
| 3 | Every state is enumerated | ✅ | `120_…` C11-03. **Of 46 states, only Florida** files LI rules: 4 files overriding the BGII premium (adds a sinkhole rate, drops the cyber factors). Puerto Rico is excluded by standing rule |
| 4 | Every `0` tested against its consuming branch | ✅ | [`CF-CHUNK11-ZERO-CASES.md`](CF-CHUNK11-ZERO-CASES.md) / `117_…`. **Seven distinct tiers**, from "record deleted" to "engine refuses". Asked of ISO live (`118_…`, C11-23): **13 of 14 agree** after the fixes; the 14th is OI-103 (a rate not in the table: ISO refuses, we price $0) |
| 5 | Every hardcoded literal key listed | ✅ | `120_…` C11-05. 6 compared literals, every one a Domain-table value. The 11 `PercentInterest` keys are 5%–15% |
| 6 | Shared-name traps diffed | ✅ | [`CF-CHUNK11-GROUP-D.md`](CF-CHUNK11-GROUP-D.md) / `119_…`. Six rule names are shared with the Structure file, all with different bodies. No execution collision is possible (every `RunRule` names its file). The Structure's same-named fields equal ISO's; each group writes its own record |
| 7 | Every exclusion's endorsement record identified | ✅ | `119_…`. Cyber exclusion is policy-level and shared ($268 → $267). Theft exclusion is structure-level. No LI group files its own |
| 8 | The edition basis stated | ✅ | Oregon: `CF_CW_20260601_V01`. Florida: `CF_CW_20230801_V01`. That is the same arithmetic without the seven 2026 "keep a submitted value" guards, so the injection trap doesn't exist there |
| 9 | No unexplained validation message | ✅ | `121_…` / `122_…`. The golden case gives **one message, M-002** (CP 10 75/76, designed out). **Our message set equals ISO's on 16 of 16 cases compared**, including every LI-specific message: "At least one Leasehold Interest limit is required", both CP 00 60 date messages, the terrorism sub-limit message, and the theft-deductible message |

## Engine changes (all user-authorized, all confirmed against ISO live)

| | Defect | Fix | Evidence |
|---|---|---|---|
| **Gap 1** | Ordered comparisons refused two dates | compare dates as dates | golden case; `CF-ENGINE-FIX-DATE-COMPARE.md` |
| **OI-102** | A blank date's `01/01/0001` fallback compared as null → False; ISO treats it as a real early date | the sentinel orders as `date.min` | missing `LeaseEffDate`: $0 → **$272, = ISO** |
| **OI-104** | `Power(0, 0)` refused; .NET returns 1 | 0^0 = 1 | blank rate + expired lease, and any LI structure without its record: crash → **$0, = ISO** |
| **OI-107** | `DateDifference` computed first − second; ISO computes second − first | second − first | Oregon TRIA days-until: −257 → **257, = ISO** |

**Regression**: `104_chunk10_c10-21_regression.py` now covers **chunks 0–11**.
**Close-out run 2026-09-22: CLEAN, 69 of 69** (every golden case at its
documented figures, every machinery script, all 16 GL suites; `--selftest`
passes).

## Findings that change how this coverage must be submitted

* The Structure's own `CovType` must be `Leasehold Interest` (with
  `PolicyType = Commercial Property Policy`). Otherwise the LI record is
  **deleted with no message**.
* `EQCovIndicator` must be `No Coverage`, not blank. A blank **switches the
  EQ cells on**.
* `ExpDate` is never an input: ISO always sets it to EffDate + 1 year.
* Only Tenants Lease is discounted. Bonus Payments, Improvements &
  Betterments and Prepaid Rent are monthly × months and ignore the interest
  rate.
* Any caller can bypass the annuity by supplying a calculated field (seven
  guarded fields, 2026 edition). ISO has the same guards, so no comparison
  catches it.

## Backlog: not blocking this gate

| Item | What it is |
|---|---|
| **OI-101** | Special without a Theft Exclusion prices at $0 in the 2026 edition, **ISO's own behaviour**. ISO's 2027 edition fixes it ($53), so it closes with OI-105 |
| **OI-103** | A lookup that finds no row: ISO refuses, we price $0 (here: a rate not in the table). Waits on the general "when does ISO refuse" rule |
| **OI-105** | ISO serves a newer 2027 Oregon edition than our corpus holds. Live comparisons must use 2026-09-17 until it's ingested |
| **OI-106** | Form names and numbers never resolve ("Value Not Found") where a state files its own `Pages` table. No premium impact |
| **OI-107 follow-up** | No GL suite exercises GL's ERP `SetMaturity*Year` rules, so GL ERP under the corrected date sign is untested |
