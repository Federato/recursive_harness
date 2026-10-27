# Chunk 12, Group G: Dependent Properties (C12-35 to C12-40)

**Closed 2026-09-23, 6 of 6. All nine gate points hold.** The family has **no
ISO fixture**, so gate 9 rests on live calls: **12 of 12 agree to the
dollar**, messages identical. No engine code was written.

| Task | Script |
|---|---|
| C12-35 golden case, and the live cases | [`141_chunk12_dependent_golden_case.py`](../scripts/cf/141_chunk12_dependent_golden_case.py) |
| C12-36 to C12-39 | [`142_chunk12_dependent_gates.py`](../scripts/cf/142_chunk12_dependent_gates.py) |
| C12-40 live ISO | [`132_chunk12_family_raas.py dependent`](../scripts/cf/132_chunk12_family_raas.py) |

---

## In plain English

Dependent Properties covers the insured's lost income when someone **else's**
premises is damaged: a key supplier, a key customer, a manufacturer, or a
"leader" location that draws customers. It hangs only off Business Income and
SC Business Income.

* **It is priced off the dependent property's own rate**, which the submitter
  supplies (no rule computes it), times a "nature of dependency" factor (1.0
  if it's the only readily available source, 0.4 Broad / 0.5 Limited
  otherwise), times 1.5 if a secondary location is involved.
* **With several dependent properties, the highest rate wins.**
* **The exposure is the insured's Business Income limit** (Broad form), the
  dependent properties' own limits (Limited form), or a submitted manual
  premium (International).
* **It prices exactly as ISO does** on every variation, both attachments.

## C12-35: the golden case (gate 1)

Chunk 5's Oregon Business Income (Basic, limit 100,000, ISO-confirmed $112 +
$13) plus the Broad form with one dependent property: submitted Group I rate
0.200 and Group II 0.030, "not the only source", no secondary location.

| Step | Value |
|---|---|
| Detail: round3(round3(0.2 × LCM 1.0) × 0.4) | 0.080 |
| Record rate: max over dependent properties | 0.080 |
| Group I: round3(0.080 × 1.0) × 100,000/100 | **$80** |
| Group II: round3(0.03 × 0.4) = 0.012 × 1,000 = 12, × 0.995 | **$12** |

**7 of 7 on the first run; ISO live identical.**

## C12-36: tables, literals, the inert files (gates 2, 5)

6 tables: Broad-form base rates (30 rows), construction map (25), the two
nature-of-dependency factors, secondary location (1.5), and the Special
time-element base rate (24). Florida files its own secondary-location and
Special rows. **The 4 inert files** are the International variants' *detail*
records: system rules only, no rate, no premium; the International premium
sits on the parent record as a submitted `ManualPremium`. Both
nature-of-dependency values are domain values.

## C12-37: states and edition (gates 3, 8)

**Florida** only: no secondary-location factor and no cyber factors in any
cell. Edition basis: 20260601 and V04 identical; V03 and V02 differ in 3
rules; V01 (FL) in 77.

## C12-38: zero cases (gate 4)

| # | Case | Result | ISO |
|---|---|---|---|
| P1 | the only source (1.0) | $200 + $30 | agrees |
| P2 | secondary location (1.5) | $120 + $18 | agrees |
| P3 | two dependent properties, 0.080 and 0.500 | **the higher wins**: $500 + $30 | agrees |
| P4 | dependent property's Group I rate absent | Group I $0, Group II $12 | agrees |
| P5 | nature of dependency blank | $0 (factor 0) | agrees |
| Z1 | nature of dependency unfiled | $0 | |
| Z2 | no dependent property | $0 | |
| Z3 | submitted record rate 1.0 | $1,000 (the `IsNull` guard keeps it) | |

## C12-39: shared names and exclusions (gates 6, 7)

The SC Business Income files mirror the Business Income ones: 17 of 25 pairs
are identical apart from names and paths. The other 8 differ by parameter
names and by testing the same gate at a different step. The SC Business
Income version matches ISO live on Basic and Special ($80 + $12 + $19), the
same figures as the Business Income version. The theft-exclusion probe was
attached at the building and did not reach the Business Income theft factor,
so it is **not tested** here.

## C12-40: ISO confirmation and messages (gate 9)

**12 of 12 live cases agree to the dollar**, messages identical: the Broad
form in 6 variations, the Limited form ($40 + $6), Extra Expense ($200 + $30,
priced on the Business Income limit, not the 30,000 location limit, at ISO
too), International ($250 manual), the Special form, and SC Business Income
twice. **Messages:** M-001 and M-002 only, **0 unexplained**.
