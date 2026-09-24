# Chunk 11, Groups E and F: inventory and states (C11-02, 05, 10, 03, 08)

**2026-09-22.** Script:
[`120_chunk11_groupsEF_inventory_states.py`](../scripts/cf/120_chunk11_groupsEF_inventory_states.py)
(in the one-command regression). **"All states" means the 46; Puerto Rico is
excluded**, per the standing project rule. An earlier version of this page
and script read Puerto Rico's package; that material has been removed.

## In plain English first

Two questions. **Is everything accounted for?** Every table, every
hardcoded value, and the 11 files that look inert. **What do the states
change?** Of the 46 states, only Florida files anything for Leasehold
Interest, and it runs on the **2023** countrywide edition. That edition's
rules do the same arithmetic but **without** the seven "only if not already
supplied" guards that 2026 added, so C11-12's injection trap **doesn't exist
in Florida**. Florida's Basic Group II premium also adds a sinkhole rate and
drops the cyber factors.

Along the way this group found an engine defect, **OI-107**: our date
subtraction had the wrong sign. It was confirmed live and has been **fixed**
(see below).

## Results

| Task | Result |
|---|---|
| **C11-02** | All six LI tables have the same rows in countrywide 2026 and 2023: 11 / 11 / 6 / 12 / **0** / 2. `SpecialFormExclgTheftLeaseHoldBaseRate` is **dead**: 0 rows, read by no countrywide lookup. **None of the 46 states files any of the six** |
| **C11-05** | **6 compared literals** (`Broad`, `Special`, `No Coverage`, `Not Applicable`, `Leasehold Interest`, `Commercial Property Policy`), every one a Domain-table value. The 11 `PercentInterest` keys are 5%–15%. `ApartmentCondoIndicator`'s Yes/No is derived by a Structure rule from 13 class codes |
| **C11-10** | The 11 `FactorsFor<N>Percent` files declare only the 3 system rules and write only form-name fields. **Run for each of the 11 rates, each attaches exactly its own marker and no premium** |
| **C11-03** | **Of 46 states, only Florida files LI rules**: 4 files, overriding `SetPremium` (and `ErcProcess`) in the four Basic Group II cells |
| **C11-08** | Florida resolves to `CF_FL_20241201_V01` over **`CF_CW_20230801_V01`**. Its 32 LI files match 2026's by name; **8 rules differ, all only by the 2026 `IsNull` guards**; the 6 tables are identical |
| **F1** | Florida gives the same arithmetic as Oregon: 120 / 108 months, net 111,958 |
| **F2** | **An injected `DiscFactor` is overwritten in Florida** (stays 0.99208894; net 111,958). In Oregon (2026) the same injection gives 128,183 |
| **F3** | **NOT EXERCISED.** Florida's BGII formula is `round(round(BGIICOLAdj + SinkholeRateAdjustment, 3) × net/100)` × PackageMod × IRPM, with no cyber factors. But the golden risk's Oregon territory isn't valid in Florida, so both inputs are 0 and a match would prove nothing. Confirmed by reading only |

### Two scripting defects caught before the result was trusted

* The C11-10 static check first "failed" all 11 files: its no-premium test
  also matched `PremiumIndicator`. Fixed to look for a write to `Premium`.
* The C11-05 check first "passed" having read nothing from the LI files: it
  guessed the XML namespace wrong. The literal count gave it away.

## OI-107: `DateDifference` had the wrong sign (fixed 2026-09-22)

Our engine computed **first date − second**; ISO computes **second −
first**. Confirmed live on Oregon's `DaysUntilTRIAExpiration =
DateDifference(EffDate, TRIAExpirationDate)`: EffDate 2026-09-17, TRIA
expiring 2027-06-01, **ISO 257, ours −257**
(`results/cf-raas/chunk11_datediff_tria_response.json`).

**Fixed with the user's authorization**: `_date_difference` in
`gl_engine/interp/nodes.py` now returns `(second − first).days`. The script
pins the Oregon case offline at **+257**. The pro-rate factors that divide
one date difference by another (Vacancy Permit, Peak Season, Builders
Risk) were never affected. General Liability's `SetMaturity*Year` rules use
`DateDifference` with different operand orders in different editions, so
the full regression includes all 16 GL suites (see
`CF-ENGINE-FIX-DATE-COMPARE.md`).

---

### Addendum 2026-09-24: Florida's V02 package closes F2's exception

The user added `CF FL 20241201 V02` on 2026-09-24; Florida now resolves to V02 over
**CW 2023 V04**. CW 2023 V01 had **no `IsNull` guard** on `SetDiscFactor` (F2: an
injected `DiscFactor` was overwritten, net 111,958); **CW 2023 V04 has it**, so the
injection is now kept in Florida exactly as in Oregon: 0.99 → net **128,183**, the
hand-derived case B of `CF-CHUNK11-GOLDEN-CASE.md`. **The "submitted value overrides the
filed calculation" trap now applies in Florida too.** `120_…` pins V02 and the new F2;
F1 (120 / 108 months, net 111,958) is unchanged.
