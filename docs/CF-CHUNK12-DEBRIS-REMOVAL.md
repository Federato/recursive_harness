# Chunk 12, Group B: Debris Removal (C12-05 to C12-10)

**Closed 2026-09-23, 6 of 6. All nine gate points hold, and ISO agrees
live.** No engine code was written.

| Task | Script |
|---|---|
| C12-05 golden case | [`127_chunk12_golden_case.py`](../scripts/cf/127_chunk12_golden_case.py) |
| C12-06 to C12-09 | [`128_chunk12_debris_removal_gates.py`](../scripts/cf/128_chunk12_debris_removal_gates.py) |
| C12-10 live ISO | [`129_chunk12_c12-10_raas.py`](../scripts/cf/129_chunk12_c12-10_raas.py), responses in `results/cf-raas/chunk12_dr_*` |

---

## In plain English

Debris Removal (CP 04 15) buys extra money for clearing debris after a loss,
above what the building form already includes. It's priced as a slice of the
building's own rate:

> building's rate for the form × a debris factor × the building's
> limit-of-insurance factor × (debris limit − 25,000) / 100

So the first $25,000 of debris limit is free (it's already in the base form)
and only the extra is charged.

* **It prices exactly as ISO does:** $49 + $6 on the golden case, matched
  cell for cell, messages included.
* **A limit below $25,000 produces a negative premium, and ISO does it too.**
  The only thing in front of it is an error message. A system that ignores
  ISO's messages would bill a credit.
* **A building marked "No Coverage" still gets charged for debris removal**,
  at ISO too.
* **A theft exclusion doesn't reduce Debris Removal on the Special form.**
  Its Special rate is a flat 0.01, not the building's. ISO agrees.
* **Florida is different:** a $10,000 minimum, no Debris Removal on Contents
  at all, and sinkhole added into Group II. New York drops the cyber factors
  from its Earthquake piece.

---

## C12-05: the golden case (gate 1)

Chunk 2's Oregon building (Basic, Frame, class 0951, limit 100,000,
ISO-confirmed at $261 + $32) plus one Debris Removal record, `Limit`
60,000. Derived by hand before the run:

| Step | Source | Value |
|---|---|---|
| Minimum limit | `DebrisRemovalMinimumLimit` [CW] `"CW","Y",25000` | 25,000 → exposure (60,000 − 25,000)/100 = **350** |
| Group I factor | `DebrisRemovalRate` [CW] `GroupI` | 0.5 |
| Group II factor | `DebrisRemovalRate` [CW] `GroupII` | 0.5 |
| Group I LOI | `BasicGroupILOIFactorBldg` [CW] at the **building's** 100,000, Frame | 1.172 |
| Group II LOI | `BasicGroupIILOIFactorBldg` [CW] at 100,000 | 1.266 |
| Group I premium | round3(round3(0.239 × 0.5) × 1.172) = 0.141; × 350 = 49.35 | **$49** |
| Group II premium | round3(round3(0.027 × 0.5) × 1.266) = 0.018; × 350 = 6.3; × cyber 0.995 | **$6** |
| Broad, Special, Earthquake | form not elected (their on/off gates read `CauseOfLossToUse` / `EQCovIndicator`) | $0 |
| **Debris Removal total** | | **$55** |
| Building | unmoved | $261 / $32 |

**21 of 21 figures matched on the first run. ISO live: identical**, $49 / $6,
and the same 2 messages.

## C12-06: tables and literals (gates 2, 5)

| Table | Rows | Notes |
|---|---|---|
| `DebrisRemovalRate` | 6 CW, **no state files rows** | `GroupI` 0.5, `GroupII` 0.5 and `Earthquake` 0.75 are **multipliers** on the building's own adjusted rate; `Broad` 0.01, `SpecialBldg` 0.01 and `SpecialPersProp` 0.01 are **flat rates** × the Structure's `LossCostMultiplier`. All 6 rows are read |
| `DebrisRemovalMinimumLimit` | 1 CW (25,000) + **FL 10,000** | |
| `BasicGroupILOIFactorBldg`, `BasicGroupIILOIFactorBldg`, `BroadSpecialLOIFactorBldg` | 342 / 57 / 57 | the **core** LOI tables, shared |

**The shared-LOI risk (the reason Debris Removal went first) is clear.**
Debris Removal keys the LOI tables on the **building's** limit (or
`FullBldgValue` when blanket, or the Builders Risk reporting limit), never on
its own limit. Its factor equals the building's own at a band edge, inside an
interpolated band (110,000 → 1.154 / 1.238) and in a higher band
(1,100,000 → 0.774 / 0.684). Raising the debris limit to 200,000 leaves the
LOI factor at 1.172.

**Literals.** Every string constant in the 18 files is a filed domain value
except one: `'Tobacco Sales Warehouses'`, which is a **form name** (Form
Pages), never a `CovType` value in any edition. The Contents gate
`CovType != 'Tobacco Sales Warehouses'` is therefore always true. Dead and
harmless.

## C12-07: states and edition basis (gates 3, 8)

44 of the 46 states run their parent's Debris Removal unchanged.

| State | What changes | How |
|---|---|---|
| **FL** | Minimum limit **10,000**, and the CP 04 15 message says $10,000 to match | state table row + state `DoMessage` override |
| **FL** | **No Debris Removal on Contents**: all 5 Contents cells hard-coded "not on policy" | `SetCoverageOnPolicyIndicator` = constant 0 |
| **FL** | Group II (Building and Special Class) adds `SinkholeRateAdjustment` to the Group II rate | `SetPremium` override |
| **NY** | The Earthquake cell drops both cyber factors | `SetPremium` override |

The FL-specific figures couldn't be priced end to end: chunk 2's Oregon
building doesn't rate in Florida (its building premium is $0 there). The FL
mechanisms above are read from the filed rules; the minimum limit (10,000)
and exposure (50) were confirmed on the engine.

**Edition basis.** The family's rules and all 5 tables are identical across
the 20230801 V02, V03, V04 and 20260601 parents. Florida's parent (20230801
V01) differs in 26 rules, and only by having **no `IsNull` guard**: the older
edition always recomputes. So the "submitted value overrides the filed table"
shape (C12-08, Z8/Z9) exists everywhere except Florida.

## C12-08: zero cases (gate 4)

| # | Case | Result | Cause | ISO |
|---|---|---|---|---|
| Z1 | limit = 25,000 | cells **on**, $0, CP 04 15 error | exposure 0 | **agrees**, same messages |
| Z2 | limit = 25,001 | on, $0 | exposure 0.01 rounds away | |
| Z3 | limit absent | **off**, $0, CP 04 15 error | `FirstValue` reads 0 | |
| **Z4** | limit 10,000 | on, **−$21 / −$3** | the on/off check runs in setup, before `MinimumLimit` is looked up, so it compares 10,000 > 0 | **agrees: −$21 / −$3** |
| **Z5** | building `CovType` "No Coverage" | **$42 + $5 still charged** | LOI falls to its `Otherwise` (1.0); nothing gates Debris Removal on the building being covered | **agrees** |
| Z6 | no construction type | $0 | LOI needs `ConstructionCode` ≠ 0 | |
| Z7 | EQ elected, no EQ inputs | EQ cell $0 | chunk 10's `EQCauseOfLossAdjustment` is empty | |
| Z8 | submitted `MinimumLimit` = 0 | **$85 + $11** | `IsNull` guard keeps the submitted value | |
| Z9 | submitted `BasicGroupIFactor` = 5 | **$490** | same | |

Nine distinct causes. Z4 and Z5 are the ones worth knowing about in a
product: a negative premium guarded only by an error message, and a charge on
an uncovered building. Both are ISO's own behaviour, not ours.

## C12-09: shared names and exclusion records (gates 6, 7)

**Shared names.** 8 field names sit on both the Debris Removal record and its
Structure. The 4 LOI factors hold equal values by construction (same table,
same key), and the other 4 (`Limit`, `BroadRate`, `SpecialRate`,
`ErcCalculatedTotalPremium`) hold different values on the two records. No
rule reads one for the other; every Debris Removal `../` path climbs to the
intended record.

**Exclusion records.** Debris Removal has none of its own. It inherits
through the building's cause-of-loss adjustment, so:

| Exclusion | Building | Debris Removal | ISO |
|---|---|---|---|
| Vandalism (needs `PolicyType` = Commercial Property Policy) | COL adj 0.239 → 0.227, BGI $261 → $248 | **BGI $49 → $47** (flows through) | agrees |
| Theft, Special form | Special $54 → $47 | **Special $4 → $4** (doesn't flow: flat 0.01 rate) | agrees |

## C12-10: ISO confirmation and messages (gate 9)

Live at 2026-09-17: **9 of 12 agree to the dollar, cell by cell, with
identical message sets wherever ISO rated.**

| Case | Ours | ISO |
|---|---|---|
| C0 golden | $49 / $6 | same |
| Z1, Z4, Z5, S1, S2, V1 | as above | same |
| Fixture AK 13933, EQTerr patched 22 → 1 | $56 / $8 / Special $2 | same |
| Fixture WY 14517 | $39 / $116 / Special $3 / **EQ $1** | same, the Earthquake cell included |
| Fixtures AK 13933, WY 14095 as filed | rated | **ISO refuses**: `EarthquakeDeductibleTier` has no row for EQTerr 22 at 2026 |
| WY 14095, EQTerr patched | rated | **ISO refuses**: `BuildingHeightFactor` has no row (CW, 9-20, 3C, 2) |

The 3 refusals are all Location/Structure Earthquake lookups, not Debris
Removal. They're 2023 fixtures sent at 2026, and they are three more data
points for the open "empty lookup: ISO refuses, we tolerate" question
(OI-103).

**Messages.** The golden case fires 2, both already logged (M-001, M-002):
**0 unexplained**. The zero cases add CP 04 15, now logged as **M-003**.
