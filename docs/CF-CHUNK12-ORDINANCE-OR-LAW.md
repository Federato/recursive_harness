# Chunk 12, Group C: Ordinance or Law (C12-11 to C12-16)

**Closed 2026-09-23, 6 of 6. All nine gate points hold. ISO agrees live on
every case it rated but one, and that one is an engine difference, logged as
OI-109.** No engine code was written.

| Task | Script |
|---|---|
| C12-11 golden case | [`130_chunk12_ordinance_golden_case.py`](../scripts/cf/130_chunk12_ordinance_golden_case.py) |
| C12-12 to C12-15 | [`131_chunk12_ordinance_gates.py`](../scripts/cf/131_chunk12_ordinance_gates.py) |
| C12-16 live ISO | [`132_chunk12_family_raas.py ordinance`](../scripts/cf/132_chunk12_family_raas.py), responses in `results/cf-raas/chunk12_ordinance_*` |

---

## In plain English

Ordinance or Law (CP 04 05) pays the extra cost when building codes force
more than a like-for-like repair. Three parts:

* **Coverage A**: the undamaged part you're forced to tear down. Priced as a
  **15% loading on the building's own premium** (factor 1.15 − 1), using the
  building's final rate and full limit.
* **Coverage B** (demolition) and **Coverage C** (increased cost to build to
  code): priced like extra building limit, the building's own adjusted rate
  × its limit and deductible factors, on the B and C limits.
* **Increased Period of Restoration**: the Business Income version, a 20%
  loading on the income premium.

What we found:

* **It prices exactly as ISO does** on every combination of A, B and C, with
  the post-loss option, with an exclusion, and on the Business Income side.
* **A blank coverage choice still charges Coverage A**, at ISO too. The rule
  only asks "is it not Coverage C Only?", and blank isn't.
* **One real difference from ISO (OI-109).** Leave out the B and C limits and
  ISO prices those parts at $0, while our engine stops with an error.
* **Six states change it, and Virginia and West Virginia add their own
  coverage** (see C12-13).

---

## C12-11: the golden case (gate 1)

Chunk 2's Oregon building, `ValuationType` Replacement Cost (the filed
requirement for Coverage C), plus one Ordinance or Law record: "Coverages A
and B & C Separate", demolition 20,000, increased construction 30,000, no
post-loss option. Derived by hand before the run:

| Cell | Arithmetic | Premium |
|---|---|---|
| A · Group I | round3((1.15 × 1.0 − 1) × 0.261) = 0.039 × 100,000/100 | **$39** |
| A · Group II | round3(0.15 × 0.032) = 0.005 × 1,000, × cyber 0.995 | **$5** |
| B · Group I | 0.239 × 1.0 → × 1.172 = 0.280 → × 0.98 × 1.0 = 0.274 × 200 | **$55** |
| B · Group II | 0.027 → × 1.266 = 0.034 → × 0.98 = 0.033 × 200 = 6.6, × 0.995 | **$7** |
| C · Group I | 0.274 × 300 | **$82** |
| C · Group II | 0.033 × 300 = 9.9, × 0.995 | **$10** |
| **Total** | building unmoved at $261 / $32 | **$198** |

**15 of 15 figures on the first run. ISO live: identical**, same 2 messages.

## C12-12: tables and literals (gates 2, 5)

11 single-row tables, all countrywide: Coverage A 1.15, Coverage A
Earthquake 1.85, post-loss option 1.02, Increased Period of Restoration 1.2
(Earthquake 2), and 6 statistical-code indicators. **Minnesota** files its
own Coverage A (1.05) and A-Earthquake (1.5) rows. **Florida's** post-loss
table is header-only, so it falls through to countrywide.

All 5 `CovType` literals the rules test are exactly the 5 values in
`DomainOrdinanceOrLawCovType`. The limit domains are open ranges (1 to
999,999,999) for the parts each combination uses, and 0 otherwise.

## C12-13: states and edition basis (gates 3, 8)

| State | What changes |
|---|---|
| **AK** | its own minimum Coverage C limit (`SetMinCovCLimit`) |
| **CA** | Ordinance or Law is **$0 for public schools** ("Schools, Academic - Public", and public trade/vocational schools) |
| **FL** | no cyber factors, sinkhole added to Group II, no post-loss option |
| **MN** | its own Coverage A factors (table rows only) |
| **NY** | Earthquake cells only: no cyber, a coinsurance factor in place of the Earthquake deductible factors |
| **VA** | **43 state-only files**: a state broad form with its own A/B/C grid and a Pollutant Cleanup cell, rated alongside the countrywide form |
| **WV** | two extra combinations with no Coverage A ("B & C Separate", "B & C Combined"), a flood-only flag that zeroes the premium, and 2 state-only Flood cells |

Edition basis: 20230801 V04 and 20260601 are identical; V03 (CA, NC)
differs in 2 rules, V02 (MO) in 22, V01 (FL) in 39. The CA, FL, VA and WV
mechanisms are read from the filed rules. The Oregon golden building doesn't
rate in those states, and none of the 10 ISO fixtures is from them.

## C12-14: zero cases (gate 4)

| # | Case | Result | ISO |
|---|---|---|---|
| K1 | Coverage A Only | A cells only, $39 + $5 | |
| K2 | Coverage C Only | C cells only, $82 + $10; the Coverage A factor is set to 1.0 | agrees |
| K3 | Coverages A and B | A + B, $106 | |
| K4 | A and B & C Combined, 50,000 | A + (B+C) $137 + $17 = $198 | agrees |
| **K5** | `CovType` **blank** | **Coverage A still charged, $39 + $5** | **agrees** |
| K6 | post-loss option Yes | 1.02 on every cell, $208 | agrees |
| **K7** | B and C limits **absent** | **ours: refuses** (a null reached the premium) | **ISO: A $39 + $5, B and C on at $0 (OI-109)** |
| K8 | submitted Coverage A `Factor` 2.0 | A $261 + $32 (the `IsNull` guard keeps it) | |

## C12-15: shared names and exclusions (gates 6, 7)

Only `CovType` and `ErcCalculatedTotalPremium` sit on both the Ordinance or
Law record and its Structure; every `../` read climbs to the intended record.
A **vandalism exclusion flows into all three parts**: A through the final
rate ($39 → $37), B and C through the cause-of-loss adjustment ($55 → $52,
$82 → $78). ISO agrees. **Increased Period of Restoration** on chunk 5's
Business Income risk: round3((1.2 − 1) × 0.112) × 1,000 = **$22** (and $3
Group II). ISO agrees.

## C12-16: ISO confirmation and messages (gate 9)

**Engine-built cases: 7 of 8 agree to the dollar** (C0, K2, K4, K5, K6, V1,
I1), messages identical. The eighth is K7 (OI-109). **After the OI-109
fix, K7 was re-run live on 2026-09-24 and agrees: 8 of 8.**

**Fixtures: every one ISO rated agrees**, cell for cell, including the
Earthquake and Increased Period of Restoration cells: NH ×2, NM, and IN and
GA once their 2023 Earthquake territory was moved to a 2026-filed one. The
other fixtures are ISO refusing Earthquake **Structure** lookups
(`BuildingHeightFactor`, `BCEGEQFactor`, `HeightTerrGroup`) on 2023 fixture
data. Those are OI-103 data points, not Ordinance or Law.

**Messages:** the golden case fires only M-001 and M-002, **0 unexplained**.
Coverage C without Replacement Cost valuation fires a filed error, designed
out of the golden case by setting the valuation.
