# Chunk 12, Group A: sequence and readiness (C12-01 to C12-04)

**Closed 2026-09-23, 4 of 4.** No engine code was written. One suspected
engine gap was found and logged, not fixed (**OI-108**).

Scripts, all re-runnable:

| Task | Script | Output |
|---|---|---|
| C12-02 | [`124_chunk12_c12-02_attach_map.py`](../scripts/cf/124_chunk12_c12-02_attach_map.py) | [`CF-CHUNK12-ATTACH-MAP.md`](CF-CHUNK12-ATTACH-MAP.md) (generated) |
| C12-03 | [`125_chunk12_c12-03_operand_types.py`](../scripts/cf/125_chunk12_c12-03_operand_types.py) | console; exits 1 while OI-108 is open |
| C12-04 | [`126_chunk12_c12-04_eq_riders.py`](../scripts/cf/126_chunk12_c12-04_eq_riders.py) | console |

---

## In plain English

* **The order is set.** Debris Removal first, then Ordinance or Law, Utility
  Services, Unmanned Aircraft, Green Upgrades and Dependent Properties.
* **No endorsement record is ever silently thrown away.** Chunk 11 was caught
  out by a rule that deleted a submitted record. Nothing like that exists
  for any of the six families, in any edition or any state.
* **Virginia and West Virginia file extra Ordinance or Law coverage that no
  countrywide file has.** 45 extra rule files. The census counted 55; the
  true population is 100.
* **The engine can already run every ISO example that uses these
  endorsements.** 17 of 17 ran to a premium.
* **One likely engine bug, in 3 states.** In CA, NC and MO, a drone insured
  on a blanket basis loses its limit (reads 0 instead of 99,000), and that
  limit drives the drone deductible factor. Logged as OI-108, not fixed.
* **"Every Earthquake rider reuses chunk 10" is only partly true.** Some
  borrow chunk 10's rate, some add their own factor on top, some re-run
  chunk 10's lookups on their own record, and Utility Services (plus three
  Dependent Properties riders) price Earthquake from their **own** tables.
  So chunk 10 being right doesn't prove those riders right; each family's
  golden case has to cover its Earthquake cell.

---

## C12-01: sequence the six families

Order confirmed with the user on 2026-09-23 ("do group 1", given against the
recommended order, no change asked):

1. **Debris Removal** (smallest; tests the shared-LOI-table risk early)
2. **Ordinance or Law** (now known to be the largest, 100 files, see C12-02)
3. **Utility Services** (13 ISO fixtures, the best-evidenced)
4. **Unmanned Aircraft** (all 46 states; carries OI-108)
5. **Green Upgrades** (no fixtures; live ISO)
6. **Dependent Properties** (no fixtures; live ISO)

## C12-02: the attach map

What was asked: for each family, which core record attaches it, under what
gate, and what deletes it.

**Every one of the 208 countrywide family datadef groups is driven by its
parent, and none is ever deleted.**

| Question | Answer | Evidence |
|---|---|---|
| Who attaches the top-level records? | 33 top-level records, each under exactly the core record the census named: Structure, Contents, Special Class, Business Income, SC Business Income. Dependent Properties hangs off Business Income and SC Business Income only | attach map, "Top-level records" |
| Are they auto-created? | **No.** Top-level records are submitted only. Of the other 175 groups, 156 are "cells" (one per cause-of-loss form) auto-created unconditionally, guarded only by `NotExist`; the remaining 19 are submitted detail records | 156 `Append` creates, all `NotExist`-only |
| Is anything driven conditionally? | No. Every drive is unconditional (`(always)`) | same |
| What deletes them? | **Nothing.** 0 `Remove` aimed at any family group, countrywide or state. Chunk 11's silent-deletion shape doesn't occur | `deletable` column, all 0 |
| Do older parent editions differ? | No. The same map holds on all 5 parent editions (20260601 V01 for 37 states; 20230801 V01 to V04 for FL, MO, CA+NC, and IL/MA/NJ/RI/VT) | "Parent editions" section |
| Do states change the attach rules? | 167 state overrides across 16 rules are **pure pins**: the whole rule is one `RunRule` to the state's declared parent edition. All 622 `ProjectName` pins in family files match the state's declared parent, so the engine's "call the parent" behaviour is correct for all of them. **One real change**: West Virginia | "State layer" section |

**Found, and not in the census: 45 state-only Ordinance or Law files.**

* **Virginia, 43 files.** A state broad form
  (`OrdinanceOrLawCoverageStateBroadForm`) with its own Coverage A, B, C and
  B+C grid across all 5 forms, a Pollutant Cleanup cell, and a Virginia
  tenants' improvements variant. Virginia's Structure `ErcProcess` calls its
  parent first, then drives these. So countrywide Ordinance or Law still
  rates in Virginia **alongside** the state form.
* **West Virginia, 2 files.** A Flood cell on Ordinance or Law and on the
  tenants' improvements variant. West Virginia's `InitializeRuleSet` calls
  the parent, then appends the Flood cell.

This moves Ordinance or Law from 55 files to 100 and gives C12-13 (its state
task) two real state mechanisms to prove, not six states of pins.

## C12-03: engine readiness by operand type

**Static.** 21,037 operators across 1,480 family files (5 parent editions
plus 46 state layers), each classed by the declared type of every operand
against what the interpreter does with it.

| Result | Count |
|---|---|
| Unknown `@Type` | 0 |
| Handled correctly | 21,031 |
| **Wrong** | **6**, one shape: OI-108 |

Eleven other signatures are new to the closed chunks and all are handled
correctly (a `Count` against an integer, and mixed integer/decimal sums and
products).

**OI-108.** In the 20230801 V02 and V03 parent editions,
`SetTotalScheduleLimit` totals the drone limits with a `Sum` over the drone
records. A scheduled drone adds its `LimitOfInsurance`. A blanket drone adds
`Sum(BlanketLimitOfInsurance, Break)`: take the blanket limit, then stop.
Our engine raises the `Break` out of the `Sum` before the `Sum` returns, so
that iteration contributes nothing. Confirmed on a real submission (ISO
fixture `STC_CP000015474`, its one drone switched to blanket, 99,000):

| State | Parent | Scheduled | Blanket |
|---|---|---|---|
| GA, OR | 20260601 V01 | 99,000 | 99,000 |
| IL | 20230801 V04 | 99,000 | 99,000 |
| **CA, NC** | 20230801 V03 | 99,000 | **0** |
| **MO** | 20230801 V02 | 99,000 | **0** |

`TotalScheduleLimit` keys `SetDeductibleFactor` and every drone Earthquake
deductible lookup, so this is premium-bearing. The current edition rewrote
the rule without the `Break`, which is why 42 states are unaffected. No ISO
fixture has a blanket drone, so ISO's own answer is not yet on record. **The
fix is an engine change and needs the user's go.**

**Live.** Every ISO STC fixture carrying a chunk 12 record (17 unique files)
was converted to an engine submission and rated at 2026-09-17 (OI-105):
**17 of 17 ran, 0 refused.**

| Family | Fixtures | Records rated | With a premium | Above $0 |
|---|---|---|---|---|
| Ordinance or Law | 10 | 625 | 245 | 102 |
| Utility Services | 13 | 156 | 65 | 39 |
| Debris Removal | 3 | 33 | 15 | 10 |
| Unmanned Aircraft | 10 | 220 | 20 | 13 |
| Dependent Properties | 0 | | | |
| Green Upgrades | 0 | | | |

This proves the path runs; it asserts no number. STC ships inputs only for
Commercial Property, so the premiums are confirmed at each family's gate 9.
The converter (`to_engine`, the inverse of chunk 11's `to_raas`) is reusable
there.

## C12-04: the Earthquake riders

**The population is 34, not 25.** The census matched "Earthquake" in the file
name. Unmanned Aircraft names its Earthquake cells `...DetailEQCov`, which
adds 9 files (5 with a premium).

**"Each reuses chunk 10's chain" holds for some riders, not all.** Traced
statically from each rider's `SetPremium` through the family's own files to
the first field no family file writes:

| Family | Riders | How the Earthquake rate is reached |
|---|---|---|
| Debris Removal | 3 | chunk 10's computed `EQCauseOfLossAdjustment` × the family's `DebrisRemovalRate` |
| Ordinance or Law | 10 | 6 read chunk 10's `EQCauseOfLossAdjustment`; 4 take `FinalEQRate` × a **family EQ factor** (`OrdinanceOrLawCovAEQFactor`, `OrdOrLawIncrPeriodOfRestorationEQFactor`) |
| Green Upgrades | 5 | chunk 10's `AdjustedEQRate` / `EQCauseOfLossAdjustment` × the family's own factors |
| Dependent Properties | 6 | 2 read chunk 10's `EQRate`; **4 take their own rate** from the family's detail tables |
| Unmanned Aircraft | 5 | **re-runs chunk 10's lookups on its own record**: `EQLossCostPrsnlProp` and the deductible tables, with chunk 10's factors from the Structure |
| Utility Services | 5 | **its own rate**: the family's own tables' "Earthquake" rows × `LossCostMultiplier`. No chunk 10 rate at all |

What that means for later tasks: a rider on the first three rows is covered
by chunk 10 plus its own factor. A rider on the last three needs its own
Earthquake case in its family's golden-case task, or the Earthquake cell goes
unproved.

The trace is static and by field name, restricted to the rider's own lineage.
It can over-report, never under-report, and each family's gate 1 confirms it
by running.

**Unmanned Aircraft's 2 "empty" Earthquake tables aren't empty where it
matters.** `EQLossCostPrsnlProp` and `EQPercentageDeductibleFactor` are
header-only at countrywide only. **46 of 46 states** file rows under the same
names (e.g. CA 684 rows of loss cost). Both are chunk 10's own tables, also
read by the core Contents / Structure / Special Class files, so this is the
shared-table shape, not a dead lookup.

---

## What Group A changes for the rest of chunk 12

* **C12-13 (Ordinance or Law states):** prove Virginia's state broad form and
  West Virginia's Flood cells, 45 files the census missed.
* **C12-17 to C12-22 (Utility Services):** the golden case must price the
  Earthquake cell from the family's own tables; chunk 10 doesn't cover it.
* **C12-23 to C12-28 (Unmanned Aircraft):** OI-108 sits in its path. Its
  golden case should include a blanket drone in CA, NC or MO, and gate 9 a
  live ISO call on that shape.
* **C12-35 to C12-40 (Dependent Properties):** 4 of 6 riders carry their own
  Earthquake rate.
* **Every family:** the derived-field injection shape is present again
  (`IsNull`-guarded `EQRate`, `TotalScheduleLimit`, `EQFactor`); check it in
  each zero-case task.
