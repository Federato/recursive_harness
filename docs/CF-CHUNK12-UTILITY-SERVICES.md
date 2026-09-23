# Chunk 12, Group D: Utility Services (C12-17 to C12-22)

**Closed 2026-09-23, 6 of 6. All nine gate points hold. ISO agrees live on
every case it rated.** No engine code was written.

| Task | Script |
|---|---|
| C12-17 golden case | [`133_chunk12_utility_golden_case.py`](../scripts/cf/133_chunk12_utility_golden_case.py) |
| C12-18 to C12-21 | [`134_chunk12_utility_gates.py`](../scripts/cf/134_chunk12_utility_gates.py) |
| C12-22 live ISO | [`132_chunk12_family_raas.py utility`](../scripts/cf/132_chunk12_family_raas.py), responses in `results/cf-raas/chunk12_utility_*` |

---

## In plain English

Utility Services covers loss when an off-site utility (water, power,
communications, wastewater) is knocked out. It comes in two halves:

* **Direct damage** (CP 04 17), on Building, Contents or Special Class: the
  physical damage caused by the outage.
* **Time element** (CP 15 45), on Business Income: the lost income, with a
  waiting-period factor.

Unlike Debris Removal and Ordinance or Law, **Utility Services has its own
rates**. It doesn't take a slice of the building's rate. Each utility is its
own "detail" line, priced from the family's own tables by utility, by
public vs non-public, and by whether overhead lines are included.

What we found:

* **It prices exactly as ISO does**, both halves, every variation tried.
* **Non-public utilities are free on the time-element side.** ISO files every
  rate in those three tables as 0. ISO confirms $0.
* **Leave the waiting period out and the time-element premium is $0** (the
  factor defaults to 0, not 1). ISO agrees.
* **Leave the limit off a direct-damage line and it covers the whole building
  limit**, at ISO too.
* **An unfiled waiting period ("36 hours"): ISO refuses, we charge $0.** Added
  to the open "empty lookup" question (OI-103).

---

## C12-17: the golden case (gate 1)

Derived by hand before the run.

**Direct damage** on chunk 2's Oregon building ($261 + $32): one detail,
Public Utilities, Water Supply (no overhead lines), limit 40,000, Basic.

| Cell | Arithmetic | Premium |
|---|---|---|
| Group I | round3(0.038 × LCM 1.0) + 0 overhead = 0.038 × 400 = 15.2 | **$15** |
| Group II | 0.011 × 400 = 4.4, × cyber 0.995 | **$4** |

**Time element** on chunk 5's Business Income risk ($112 + $13): one detail,
Public Utilities, Water Supply, limit 40,000, 72-hour waiting period
(factor 1.0).

| Cell | Arithmetic | Premium |
|---|---|---|
| Group I | 0.022 × 1.0 × 400 = 8.8 | **$9** |
| Group II | 0.011 × 1.0 × 400 = 4.4 | **$4** |

**14 of 14 figures on the first run**, building and Business Income unmoved.
**ISO live: identical**, same 2 messages.

## C12-18: tables and literals (gates 2, 5)

9 tables, all countrywide. **The three time-element "NonPublic" tables file
all 15 rates as 0**, so a non-public utility's time-element cover is free by
filing. The waiting-period table runs from 0.88 (168 hours) to 1.15 (no
waiting period); only Florida files its own. All 7 `Utility` / `UtilityType`
/ `WaitingPeriod` literals the rules test are domain values.

## C12-19: states and edition basis (gates 3, 8)

**Florida** is the only state that files Utility Services rules. Its
time-element cells drop the waiting-period factor and both cyber factors,
and the "a waiting period other than 72 hours needs Business Income" message
is removed. Edition basis: 20260601, V04 and V03 are identical. V02 (MO) only
lacks a blanket cause-of-loss validation message (no premium effect). V01
(FL) differs in 146 rules, most of them overridden by Florida's own layer.

## C12-20: zero cases (gate 4)

| # | Case | Result | ISO |
|---|---|---|---|
| Z1 | detail `CauseOfLoss` blank | $0, cells off | agrees |
| Z2 | `UtilityType` blank | $0 | |
| **Z3** | detail `Limit` absent | **the building's whole limit: $38 + $11** | **agrees** |
| Z4 | time element, non-public utility | $0 (filed rate 0) | agrees |
| Z5 | time element, no waiting period | $0 (factor 0.0) | agrees |
| **Z6** | time element, unfiled waiting period | **ours $0** | **ISO refuses** (OI-103) |
| Z7 | submitted `BasicGroupIRate` 1.0 | $400 (the `IsNull` guard keeps it) | |

## C12-21: shared names and exclusions (gates 6, 7)

The five attachments (Building, Contents and Special Class direct damage;
Business Income and SC Business Income time element) read **exactly the same
fields**, form for form (Group I, Special and Earthquake compared). Utility
Services reads **no cause-of-loss adjustment**, so a vandalism exclusion
moves the building ($261 → $248) and **not** Utility Services ($15 stays
$15). Its Earthquake cell prices from the family's own "Earthquake" rows, not
chunk 10's chain (C12-04); ISO confirms it on fixtures.

## C12-22: ISO confirmation and messages (gate 9)

**Engine-built: 10 of 11 agree to the dollar**: golden direct damage and
time element; overhead lines ($18 + $7); non-public ($30 + $9); Special
($15 + $4 + $2); blank cause of loss; non-public time element; no waiting
period; 24-hour wait ($10 + $5); missing limit. The eleventh is ISO refusing
the unfiled waiting period (OI-103).

**Fixtures: all 8 that ISO rated agree**, cell for cell (CT ×3 direct
damage; AK, NH ×2, and IN and GA with the Earthquake territory moved to a
2026-filed one). The rest are ISO refusing Earthquake Structure lookups on
2023 fixture data (OI-103), never a Utility Services cell.

**Messages:** only M-001 and M-002 on the golden cases, **0 unexplained**.
