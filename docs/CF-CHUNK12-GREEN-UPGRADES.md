# Chunk 12, Group F: Green Upgrades (C12-29 to C12-34)

**Closed 2026-09-23, 6 of 6. All nine gate points hold.** The family has **no
ISO fixture**, so gate 9 rests on live calls: **8 of 8 agree to the dollar**.
The ninth call (an unfiled percentage) is refused by ISO where we rate, an
OI-103 instance. No engine code was written.

| Task | Script |
|---|---|
| C12-29 golden case, and the live cases | [`139_chunk12_green_golden_case.py`](../scripts/cf/139_chunk12_green_golden_case.py) |
| C12-30 to C12-33 | [`140_chunk12_green_gates.py`](../scripts/cf/140_chunk12_green_gates.py) |
| C12-34 live ISO | [`132_chunk12_family_raas.py green`](../scripts/cf/132_chunk12_family_raas.py) |

---

## In plain English

Green Upgrades (CP 04 23) pays the extra cost of rebuilding "green" after a
loss, plus related expenses (certification, recycling). Two premiums per form:

* **Green upgrades**: the building's own adjusted rate × a discount factor ×
  the Green Upgrades limit. The discount depends on how big that limit is
  relative to the building (a bigger ratio gets a deeper discount, down to
  0.5).
* **Related expenses**: 10% of the building's adjusted rate × the related
  expenses amount.

What we found:

* **It prices exactly as ISO does** on every variation, including the
  Business Income version.
* **Leaving the percentage blank nearly doubles the premium** ($30 → $56):
  with no percentage the ratio is 0, which selects the undiscounted factor
  1.0. ISO does the same.
* **An unfiled percentage ("25%") prices at $56 here and is refused by ISO**
  (OI-103).

## C12-29: the golden case (gate 1)

Chunk 2's Oregon building (adjusted rates 0.266 / 0.033, limit 100,000) plus
Green Upgrades: limit 20,000, 20%, related expenses 10,000.

| Step | Value |
|---|---|
| Ratio = round3(round3(20,000 / 100,000) / 0.2) | 1.000 → 1,000 |
| Rate-modification factor (band 900–1,000) | 0.5 |
| Group I green: round3(0.5 × 0.266) = 0.133 × 200 | **$27** |
| Group I related: round3(0.266 × 0.1) = 0.027 × 100 | **$3** |
| Group II green: round3(0.5 × 0.033) = 0.017 × 200 = 3.4, × 0.995 | **$3** |
| Group II related: 0.003 × 100 = 0.3 | $0 |
| **Total** | **$33** |

**12 of 12 on the first run; ISO live identical.**

## C12-30: tables and literals (gates 2, 5)

4 single-purpose countrywide tables, none filed by a state: increased-cost %
(10–50%), period of restoration (30–180 days, 1.0–1.06), rate modification
(12 bands, 1.0 down to 0.5), related expenses 0.1. Every percentage key is a
domain value.

## C12-31: states and edition (gates 3, 8)

**Florida** is the only state that changes it: sinkhole is added to Group II
(`AdjustedSinkholeRate`), and the cyber factors are dropped. Edition basis:
20260601, V04, V03 and V02 identical; V01 (FL) differs in 31 rules.

## C12-32: zero cases (gate 4)

| # | Case | Result | ISO |
|---|---|---|---|
| G1 | percentage blank | **ratio 0 → factor 1.0 → $56 + $7** | agrees |
| G2 | no related expenses | $27 + $3 | agrees |
| G3 | limit = the building's | ratio 5.0 → 0.5 → $136 + $17 | agrees |
| G4 | 5,000 at 50% | ratio 0.1 → RatioToUse 100 → $16 + $2 | agrees |
| G5 | limit absent | green $0 (the product skips the null, 0.133 rounds to $0), related $3 | agrees |
| G8 | percentage unfiled ("25%") | **ours $56 + $7** | **ISO refuses** (OI-103) |
| Z2 | limit above the building's | ratio 7.5 → 0.5 → $203 + $26 | |
| Z3 | submitted rate-modification factor 2 | $109 (the `IsNull` guard keeps it) | |

## C12-33: shared names and exclusions (gates 6, 7)

Building, Contents and Special Class read identical fields, form for form.
The two Business Income versions use their own formula (period of
restoration instead of the ratio); G7 confirms it live ($4). The family reads
the building's **adjusted** rate, so a **vandalism exclusion flows through**
($30 → $28).

## C12-34: ISO confirmation and messages (gate 9)

**8 of 8 live cases agree to the dollar**, messages identical: the golden
case, blank percentage, no related expenses, two ratio bands, a missing
limit, a Special building ($30 + $3 + $7) and the Business Income version
($4). The ninth, an unfiled percentage, is ISO refusing a lookup we tolerate
(OI-103). **Messages:** M-001 and M-002 only, **0 unexplained**.
