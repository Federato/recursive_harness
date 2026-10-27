# Chunk 12, Group E: Unmanned Aircraft (C12-23 to C12-28)

**Closed 2026-09-23, 6 of 6. All nine gate points hold. ISO agrees live on
every engine-built case (10 of 10) and every fixture it rated.** One engine
bug in this family's path (OI-108) was found in Group A and fixed the same
day, with the user's authorization.

| Task | Script |
|---|---|
| C12-23 golden case | [`137_chunk12_drone_golden_case.py`](../scripts/cf/137_chunk12_drone_golden_case.py) |
| C12-24 to C12-27 | [`138_chunk12_drone_gates.py`](../scripts/cf/138_chunk12_drone_gates.py) |
| C12-28 live ISO | [`132_chunk12_family_raas.py drone`](../scripts/cf/132_chunk12_family_raas.py); OI-108 live: [`135_chunk12_oi108_raas.py`](../scripts/cf/135_chunk12_oi108_raas.py) |

---

## In plain English

Unmanned Aircraft (CP 04 64) insures drones: each one listed with its own
limit, or a blanket limit for drones not individually listed. It attaches to
Building, Contents, Special Class and the two Business Income records.

* **Drones are only rated on the Special form.** On Basic or Broad the drone
  premium is $0, by ISO's own rule.
* **The rate is the family's own**: a loss cost by risk class (search and
  rescue, firefighting and weather monitoring are "high risk", 2.525;
  everything else 1.625), times a no-deductible or deductible factor, times
  the limit.
* **It prices exactly as ISO does**, including two drones, a blanket drone,
  a deductible, the newly-acquired extension, and a Contents windstorm
  exclusion.
* **A blanket drone lost its limit in CA, NC and MO (OI-108).** Fixed;
  confirmed against ISO in all three.

## C12-23: the golden case (gate 1)

Chunk 4's Oregon Contents on the Special form (ISO-confirmed $137) plus one
scheduled drone: "All Other" operations, limit 10,000, no deductible.

| Step | Source | Value |
|---|---|---|
| Risk class | `UnmannedAircraftRiskClass` [CW] "All Other" | Ordinary |
| Loss cost | `UnmannedAircraftLossCosts` [CW] | 1.625 |
| × LCM 1.0, newly-acquired 1.0 | | 1.625 |
| × no-deductible factor | `UnmannedAircraftNoDeductibleFactor` [CW] | round3(× 1.15) = 1.869 |
| × vandalism, sprinkler, wind, theft (all 1.0 here) | Contents record | 1.869 |
| × 10,000 / 100 | | 186.9 → **$187** |
| Earthquake cell | not elected | $0 |

**10 of 10 on the first run; ISO live $187.** The case sets the building's
`WindstormOrHailDeductible` to 1,000: chunk 4's building left it blank, and on
the Special form ISO refuses a blank key there (another OI-103 instance).

## C12-24: tables and literals (gates 2, 5)

36 tables. The family's own (loss costs, risk class, deductible and
newly-acquired factors, 9 statistical-code tables) are countrywide, with only
**Florida** filing its own. The Earthquake tables are chunk 10's. The two
header-only ones (`EQLossCostPrsnlProp`, `EQPercentageDeductibleFactor`) are
filed by all 46 states (C12-04). Every golden drone value is a domain value.

## C12-25: all 46 states, both layers (gates 3, 8)

**Many patterns, not one**, but they are mostly Earthquake plumbing:

* **39 states** change only the Earthquake sub-limit deductible-tier lookups
  (which of the six tier tables they use), in 4 groupings.
* **AL, TX**: their own windstorm-exclusion factor rule.
* **AR, DC, KS, NY, RI**: the Business Income drone premium and its wind
  factor (DC and NY also the Earthquake rate).
* **AK, CA**: the Earthquake deductible factor.
* **FL**: its own copy of the family tables and statistical-code rules.

Edition basis: 20260601 and V04 identical. V03 (CA, NC) and V02 (MO) differ
in `SetTotalScheduleLimit`, the OI-108 shape, now handled. V01 (FL) differs
in 46 rules.

## C12-26: zero cases (gate 4)

| # | Case | Result | ISO |
|---|---|---|---|
| Z1 | Contents on the Basic form | $0 (drones are Special-only) | agrees |
| Z2 | no type of operations | $0 (no risk class, no loss cost) | agrees |
| Z3 | Search & Rescue | high risk 2.525 → $290 | agrees |
| **Z4** | **no limit** | **$2**: the missing limit is left out of the product, not zeroed (OI-110) | **agrees** |
| Z5 | deductible 1,000 | factor 0.96 → $156 | agrees |
| Z6 | newly-acquired extension | 1.05 → $196 | agrees |
| Z7 | blanket drone 10,000 | $187 | agrees |
| Z8 | two drones, 10,000 and 5,000 | $187 + $93 | agrees |
| Z9 | submitted base rate 10 | $1,150 (the `IsNull` guard keeps it) | |

Z4 is a second discriminating confirmation of OI-110's rule: "write $0" would
have given $0.

## C12-27: shared names and exclusions (gates 6, 7)

The drone adds **no message of its own**: the golden case's 4 messages are
exactly those of the same Contents case without a drone. A **Contents
windstorm exclusion** reaches the drone through its own wind factor (0.315
for symbol B): **$59**, ISO agrees, while the Contents premium stays $137. The
theft-exclusion probe was attached at the building level and didn't engage;
the drone's theft factor is read from the Contents record and wasn't tested
with an attached exclusion.

## C12-28: ISO confirmation and messages (gate 9)

* **Engine-built: 10 of 10 agree to the dollar**, messages identical.
* **Fixtures: every one ISO rated agrees**, drone and Earthquake cells
  included (NH ×2, NM, and IN and GA with the Earthquake territory moved to a
  2026-filed one). The rest are ISO refusing Earthquake Structure lookups on
  2023 fixture data (OI-103).
* **OI-108 live**: blanket drones in CA, NC and MO now match ISO, 8 of 8.
* **Messages**: 0 unexplained (the base Contents case's own four, M-001,
  M-002 and two Contents validation messages).
