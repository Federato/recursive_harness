#!/usr/bin/env python3
"""Chunk 10, C10-18 -- Special Class's 27 EQ-touching files, classified.

The opening census (`84_chunk10_census.py` finding 2) re-confirmed 27 of the
97 `*Earthquake*` files touch Special Class BY CONTENT (identical to the
filename count). Re-derived here directly, not trusted from the doc: the
SAME `re.search(r"SpecialClass|SpclClass", body)` scan over the SAME
97-file population, run fresh, returns the SAME 27 files.

This task classifies each of the 27 as (a) a core EQ premium file or (b) an
endorsement wrapper reading an already-computed EQ value, the same
core-vs-wrapper split C10-10 did for the general 97-file population --
applied specifically to this one group's 27.

**The classification is not binary the way the task doc's own two-way
framing suggests -- Special Class's 27 files actually split across TWO
sibling premium groups, not one:**

  * 8 of the 27 have "SpecialClass" or "SpclClassBusnIncome" ONLY in a
    Endorsement/CoverageWithFlatDollarDeductible/SubLimitForm family name --
    these are the SAME 4-variant Endorsement family shape C10-10/C10-02
    already found for the core 20-file `EarthquakeAndVolcanicEruption*`
    population, just Special-Class-flavored: 4 for SPECIAL CLASS itself
    (plain, flat-dollar-deductible, sub-limit, sub-limit+flat-dollar), 4 for
    its SIBLING group SC BUSINESS INCOME (the exact same 4 variants,
    confirmed by C10-06 to read SC Business Income's OWN ancestor-copied
    `EQRate`, not Special Class's directly). Each of these 8 carries its own
    `Lookup` against one of the 29-table core-chain population C10-02
    already classified (`EQLossCostBldg`/`EQPercentageDeductibleFactor`/etc).
  * The remaining 19 are wrappers, split the same way: 6 read SPECIAL
    CLASS's own `FinalEQRate`/`EQCauseOfLossAdjustment` directly; 13 read SC
    BUSINESS INCOME's own values -- confirming the census's OWN "Special
    Class" population is really "Special Class + its own SC Business Income
    branch," the same two-group shape C10-06/C10-11 already established for
    the whole chunk, now re-surfacing inside a single family's own count.
  * **5 of the 19 wrappers are NOT pure read-and-multiply**, the same
    C10-10-flagged shape found in the general population: each carries its
    OWN small `Lookup` against an ORDINARY (non-EQ-named) factor table
    shared with that group's non-EQ chain -- `AgreedValueFactor`/
    `AgreedValueFactorBusnIncome`/`ExtendedPeriodFactor`/
    `InflationGuardBldg`/`RebuildingExpensesFactor` -- applied ON TOP of the
    shared EQ value, not instead of it. `SpecialClassInflationGuard` goes
    one step further: it reads one of the 4 core Endorsement records' own
    already-computed `Premium` directly (not a rate at all), times its own
    `Factor`. None of the 5 computes an EQ rate of its own -- confirmed by
    checking each one's `SetPremium` body directly, not inferring from
    `Lookup` presence alone (a crude "has any Lookup" scan over-counts these
    5 as core; reading what the Lookup actually feeds is what breaks the
    tie).

    python scripts/cf/102_chunk10_c10-18_special_class_census.py

Always exits 0 -- a structural census by direct read, not a runnable case.
No engine code touched.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from cf_engine.resolve import book_for

ASOF = "20260917"

#: file -> (group, verdict, note). Every verdict below was read directly off
#: the file's own `SetPremium` body -- not inferred from the filename.
CENSUS = {
    # -------- 8 CORE (4 Special Class + 4 SC Business Income) --------
    "CommercialPropertyEarthquakeAndVolcanicEruptionEndorsementSpecialClassRules.Rule.xml": (
        "Special Class", "CORE",
        "Plain percentage-deductible -- own Lookup of EQLossCostBldg-family/"
        "EQPercentageDeductibleFactor, the C10-02 core-chain tables."),
    "CommercialPropertyEarthquakeAndVolcanicEruptionCoverageWithFlatDollarDeductibleSpecialClassRules.Rule.xml": (
        "Special Class", "CORE", "Flat-dollar-deductible variant of the above."),
    "CommercialPropertyEarthquakeAndVolcanicEruptionEndorsementSubLimitFormSpecialClassRules.Rule.xml": (
        "Special Class", "CORE", "Sub-limit variant of the above."),
    "CommercialPropertyEarthquakeAndVolcanicEruptionCoverageSubLimitFormWithFlatDollarDeductibleSpecialClassRules.Rule.xml": (
        "Special Class", "CORE", "Sub-limit + flat-dollar-deductible variant."),
    "CommercialPropertyEarthquakeAndVolcanicEruptionEndorsementSpclClassBusnIncomeRules.Rule.xml": (
        "SC Business Income", "CORE",
        "SAME 4-variant shape, one sibling group down -- reads SC BI's own "
        "ancestor-copied EQRate (C10-06), not Special Class's directly."),
    "CommercialPropertyEarthquakeAndVolcanicEruptionCoverageWithFlatDollarDeductibleSpclClassBusnIncomeRules.Rule.xml": (
        "SC Business Income", "CORE", "Flat-dollar-deductible variant."),
    "CommercialPropertyEarthquakeAndVolcanicEruptionEndorsementSubLimitFormSpclClassBusnIncomeRules.Rule.xml": (
        "SC Business Income", "CORE", "Sub-limit variant."),
    "CommercialPropertyEarthquakeAndVolcanicEruptionCoverageSubLimitFormWithFlatDollarDeductibleSpclClassBusnIncomeRules.Rule.xml": (
        "SC Business Income", "CORE", "Sub-limit + flat-dollar-deductible variant."),

    # -------- 6 WRAPPER, Special-Class-side --------
    "CommercialPropertyDebrisRemovalAdditionalInsuranceSpecialClassEarthquakeCoverageRules.Rule.xml": (
        "Special Class", "wrapper", "Reads ../EQCauseOfLossAdjustment x its own EQFactor. No own Lookup."),
    "CommercialPropertyUtilityServicesDirectDamageSpecialClassDetailEarthquakeCoverageRules.Rule.xml": (
        "Special Class", "wrapper", "Reads ../EQRate x Limit/100 x 2 Cyber factors. No own Lookup."),
    "CommercialPropertyIncreaseInRebuildingExpensesFollowingDisasterSpecialClassEarthquakeCovRules.Rule.xml": (
        "Special Class", "wrapper",
        "NOT pure read-and-multiply: reads ../../../EQCauseOfLossAdjustment "
        "x its OWN RebuildingExpensesFactor (an ordinary, non-EQ-named table "
        "shared with the non-EQ chain)."),
    "CommercialPropertyIncreasedCostOfLossAndRelatedExpensesForGreenUpgradesEndtSpecialClassEarthquakeCovRules.Rule.xml": (
        "Special Class", "wrapper",
        "Reads an intermediate EQ factor and recombines locally, the same "
        "shape C10-10 found for Building's own Green Upgrades file."),
    "CommercialPropertySpecialClassAgreedValEarthquakeCoverageRules.Rule.xml": (
        "Special Class", "wrapper",
        "NOT pure read-and-multiply: reads ../FinalEQRate x its OWN "
        "AgreedValueFactor (ordinary, non-EQ-named, shared with the non-EQ "
        "Agreed Value chain)."),
    "CommercialPropertySpecialClassInflationGuardEarthquakeCoverageRules.Rule.xml": (
        "Special Class", "wrapper",
        "Reads one of the 4 CORE Endorsement records' own already-computed "
        "Premium directly (not a rate at all) x its own Factor -- the "
        "shallowest possible wrapper, one step past the other 5."),

    # -------- 13 WRAPPER, SC-Business-Income-side --------
    "CommercialPropertyBusinessIncomeFromDependentPropertiesBroadFormSpclClassBusnIncomeEarthquakeCoverageRules.Rule.xml": (
        "SC Business Income", "wrapper", "Reads SC BI's own EQ value x its own Factor. No own Lookup."),
    "CommercialPropertyBusinessIncomeFromDependentPropertiesLimitedFormSpclClassBusnIncomeEarthquakeCoverageRules.Rule.xml": (
        "SC Business Income", "wrapper", "Same shape, Limited Form variant."),
    "CommercialPropertyBusinessIncomeLandlordAsAdditionalInsuredRentalValueSpclClassBusnIncomeEarthquakeCoverageRules.Rule.xml": (
        "SC Business Income", "wrapper", "Same shape."),
    "CommercialPropertyBusnIncomeChangesBeginningOfThePerOfRestrtnNoWaitingPerSpclClassBusnIncomeEarthquakeCoverageRules.Rule.xml": (
        "SC Business Income", "wrapper", "Same shape."),
    "CommercialPropertyCivilAuthorityIncreasedCoveragePeriodSpclClassBusnIncomeEarthquakeCoverageRules.Rule.xml": (
        "SC Business Income", "wrapper", "Same shape."),
    "CommercialPropertyExtraExpenseFromDependentPropertiesSpclClassBusnIncomeDetailEarthquakeCoverageRules.Rule.xml": (
        "SC Business Income", "wrapper", "Same shape."),
    "CommercialPropertyIncreasedCostOfLossAndRelatedExpensesForGreenUpgradesEndtSpclClassBusnIncomeEarthquakeCovRules.Rule.xml": (
        "SC Business Income", "wrapper", "Intermediate-factor recombination, same as its Special Class sibling."),
    "CommercialPropertyOrdinanceOrLawIncreasedPeriodOfRestorationSpclClassBusnIncomeEarthquakeCoverageRules.Rule.xml": (
        "SC Business Income", "wrapper", "Same shape as Building's own Ordinance or Law incremental wrapper (C10-10)."),
    "CommercialPropertyOrdinaryPayrollLimitationOrExclusionSpclClassBusnIncomeEarthquakeCoverageRules.Rule.xml": (
        "SC Business Income", "wrapper", "Same shape."),
    "CommercialPropertyPowerHeatAndRefrigerationDeductionSpclClassBusnIncomeEarthquakeCoverageRules.Rule.xml": (
        "SC Business Income", "wrapper", "Same shape."),
    "CommercialPropertySpecialClassBusnIncomeAgreedValEarthquakeCoverageRules.Rule.xml": (
        "SC Business Income", "wrapper",
        "NOT pure read-and-multiply: own AgreedValueFactorBusnIncome table, "
        "the SC BI sibling of Special Class's own Agreed Value wrapper."),
    "CommercialPropertySpecialClassBusnIncomeExtendedPeriodOfIndemnityCoverageEarthquakeCoverageRules.Rule.xml": (
        "SC Business Income", "wrapper",
        "NOT pure read-and-multiply: own ExtendedPeriodFactor table (an "
        "ordinary Business-Income-only concept, no Special Class equivalent)."),
    "CommercialPropertyUtilityServicesTimeElementSpclClassBusnIncomeDetailEarthquakeCoverageRules.Rule.xml": (
        "SC Business Income", "wrapper", "Reads SC BI's own EQRate x WaitingPeriodFactor. No own Lookup."),
}


def main() -> int:
    book = book_for("CW", ASOF)
    rules_dir = book.state.package.content / "Rules"
    all_eq = sorted(p.name for p in rules_dir.glob("*.xml") if "Earthquake" in p.name)
    bodies = {f: (rules_dir / f).read_text(encoding="utf-8-sig") for f in all_eq}
    by_content = sorted(f for f in all_eq if re.search(r"SpecialClass|SpclClass", bodies[f]))

    print(f"=== Re-derived Special-Class-touching EQ files (by CONTENT): "
          f"{len(by_content)} of {len(all_eq)} (census claim: 27, "
          f"{'MATCH' if len(by_content) == 27 else 'DOES NOT MATCH'})\n")

    missing = set(by_content) - set(CENSUS)
    extra = set(CENSUS) - set(by_content)
    assert not missing, f"re-derived files not classified: {missing}"
    assert not extra, f"classified files no longer in the re-derived 27: {extra}"

    core = [(f, g, v) for f, (g, t, v) in CENSUS.items() if t == "CORE"]
    wrap = [(f, g, v) for f, (g, t, v) in CENSUS.items() if t == "wrapper"]
    core_sc = [x for x in core if x[1] == "Special Class"]
    core_bi = [x for x in core if x[1] == "SC Business Income"]
    wrap_sc = [x for x in wrap if x[1] == "Special Class"]
    wrap_bi = [x for x in wrap if x[1] == "SC Business Income"]
    wrap_not_pure = [x for x in wrap if "NOT pure read-and-multiply" in x[2]
                      or "not a rate at all" in x[2]]

    print(f"CORE:    {len(core)} of 27  ({len(core_sc)} Special Class, "
          f"{len(core_bi)} SC Business Income -- 4 Endorsement-family "
          f"variants each)")
    print(f"WRAPPER: {len(wrap)} of 27  ({len(wrap_sc)} Special Class, "
          f"{len(wrap_bi)} SC Business Income)")
    print(f"  of the {len(wrap)} wrappers, {len(wrap_not_pure)} are NOT pure "
          f"read-and-multiply -- each carries its own small Lookup against "
          f"an ordinary, non-EQ-named factor table applied on top of the "
          f"shared EQ value:")
    for f, g, v in wrap_not_pure:
        print(f"    [{g:20s}] {f}")

    print("\n=== Full classification\n")
    for f, (g, t, v) in sorted(CENSUS.items()):
        print(f"  [{t:7s}][{g:20s}] {f}")
        print(f"      {v}")

    print("\n=== What this means for the task's own framing\n")
    print("    The task doc frames this as a binary split (core Special "
          "Class EQ premium vs. wrapper reading Special Class's own "
          "EQRate). Direct read of all 27 finds the population actually "
          "spans TWO sibling premium groups, not one -- 8 core files (4 "
          "Special Class, 4 SC Business Income, the same 4-variant "
          "Endorsement-family shape) and 19 wrappers (6 Special Class, 13 "
          "SC Business Income), with 5 of the 19 carrying their own small "
          "non-EQ-named factor Lookup on top of the shared value rather "
          "than a pure read-and-multiply -- the same nuance C10-10 already "
          "flagged for the general 97-file population, now confirmed "
          "present inside this one family's own count too. No engine gap.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
