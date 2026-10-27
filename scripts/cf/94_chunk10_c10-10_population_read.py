#!/usr/bin/env python3
"""Chunk 10, C10-10 -- confirm the full 97-file `*Earthquake*` population by
DIRECT READ, not just filename/regex classification. The opening census and
Gate Group 1 only ever read the `EarthquakeAndVolcanicEruption*` core
family (~15 files, all thin percentage-deductible/sub-limit/flat-deductible
variants of ONE mechanism) plus a couple of wrapper examples in full. This
task reads at least one representative file from every OTHER family the
census only counted by name pattern.

19 files read in full here (9 from the task's own named list, 10 more
covering every other distinct family in the 97 -- Additional Locations
Special Coinsurance, Builders Risk, Business Income riders, Civil
Authority, Functional Valuation, Manufacturers Consequential Loss,
Non-Owned Trailers, Utility Services Time Element, Value Reporting Form,
and the Earthquake Inception Extension). All 97 filenames are enumerated
first (`Rules/*Earthquake*`, re-confirmed at 97) and grouped by family so
the read sample's coverage is visible against the whole population, not
just asserted.

    python scripts/cf/94_chunk10_c10-10_population_read.py

Always exits 0 -- a census by direct read. If a file turns out to be
structurally different from "thin wrapper reading an already-computed EQ
value," that is reported here as a finding, not silently folded into the
"thin wrapper" claim.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from cf_engine.resolve import book_for

ASOF = "20260917"

#: file -> (family label, one-line verdict from direct read).
READ = {
    # -- the 9 families the task doc names explicitly --
    "CommercialPropertyOrdinanceOrLawCovACoverageEarthquakeCoverageRules.Rule.xml": (
        "Ordinance or Law",
        "NOT a pure thin wrapper -- carries its OWN `SetEQFactor` (an "
        "ancestor-copy from `../CommercialPropertyOrdinanceOrLawCovACoverage/"
        "EQFactor`, the same shape C10-06 found for Business Income) and its "
        "`SetPremium` reads `FinalEQRate x (EQFactor x PostLossFactor - 1)` -- "
        "an INCREMENTAL premium on top of the already-computed EQ rate, not "
        "a straight read-and-multiply. Still reads the shared EQ chain, "
        "never derives its own rate."),
    "CommercialPropertyUtilityServicesDirectDamageBldgDetailEarthquakeCoverageRules.Rule.xml": (
        "Utility Services (Direct Damage)",
        "Genuine thin wrapper: `SetPremium` = `../EQRate x Limit/100 x` 2 "
        "Cyber factors. No own rate lookup."),
    "CommercialPropertyIncreasedCostOfLossAndRelatedExpensesForGreenUpgradesEndtBldgEarthquakeCovRules.Rule.xml": (
        "Green Upgrades",
        "NOT a pure thin wrapper -- 2-part premium (`RelatedExpensesPremium` "
        "+ `GreenUpgradesPremium`), each reading `../../../AdjustedEQRate` "
        "(an INTERMEDIATE EQ value, not the FinalEQRate) times its own "
        "`RelatedExpensesFactor`/`RateModificationFactor x PostLossFactor` "
        "combination. Reads mid-chain, not end-chain, but still reads "
        "already-computed EQ values -- no lookup of its own."),
    "CommercialPropertyDebrisRemovalAdditionalInsuranceEarthquakeCoverageRules.Rule.xml": (
        "Debris Removal",
        "Genuine thin wrapper: `SetPremium` = `../../../EQCauseOfLossAdjustment "
        "x ../EQFactor x (Limit-MinimumLimit)/100 x` 2 Cyber factors. Reads "
        "an intermediate EQ value plus its own local EQFactor, no lookup."),
    "CommercialPropertyLeaseholdInterestCoverageFormBonusPaymentsCoverageEarthquakeCoverageRules.Rule.xml": (
        "Leasehold Interest",
        "Genuine thin wrapper: `SetPremium` = `../BonusPaymentsNetLeaseholdInt/100 "
        "x ../EQCauseOfLossAdjustment x` 2 Cyber factors. No own rate lookup."),
    "CommercialPropertyPeakSeasonLimitOfInsuranceDetailEarthquakeCoverageRules.Rule.xml": (
        "Peak Season",
        "STRUCTURALLY DIFFERENT, not a thin wrapper -- computes "
        "`TotalLimitPremium` from `Rate` (itself `FinalEQRate` or "
        "`EQAvgRate` depending on blanket) x `EQLOIToUse`, then COPIES "
        "`PPEQPremium` from whichever of 4 SIBLING EQ Endorsement records "
        "actually exists (an `Exist`-gated 4-way `Choose` across other "
        "coverages' own premium fields), subtracts the two "
        "(`BaseAndTotalLimitsDifference`), and only THEN multiplies by its "
        "own pro-rate factor. A genuine cross-coverage premium DIFFERENCE, "
        "not a read-and-multiply -- flagged, not just logged as thin."),
    "CommercialPropertyVacancyPermitEarthquakeCoverageRules.Rule.xml": (
        "Vacancy Permit",
        "Genuine thin wrapper: `SetPremium` = `../EQFactor x LossCostMultiplier "
        "x EQLimitToUse/100 x VacancyPermitProRateFactor x` 2 Cyber factors. "
        "EQFactor here is this file's OWN local field (not the ancestor-copy "
        "shape), no lookup of its own."),
    "CommercialPropertyRadioOrTelevisionAntennasDetailEarthquakeCoverageRules.Rule.xml": (
        "Radio/TV Antennas",
        "NOT a pure thin wrapper for one of its two branches -- height "
        "<=75ft reads `EQCauseOfLossAdjustment x EQCoinsuranceFactor x "
        "EQDeductibleFactor` (intermediate factors recombined locally); "
        "height >75ft goes FURTHER and reads `EQBaseRate` itself plus "
        "LossCostMultiplier/EQSprinklerLeakageOnlyBldgFactor -- effectively "
        "re-running its own copy of the base-to-final chain rather than "
        "reading one already-computed value. Confirmed as one of the "
        "C10-02-flagged 'other coverage with its own independent EQ rider' "
        "population, not a thin wrapper at all for the >75ft branch."),
    "CommercialPropertyBrandsAndLabelsEarthquakeCoverageRules.Rule.xml": (
        "Brands and Labels",
        "Genuine thin wrapper: `SetPremium` = `../EQRate x LimitToUse/100 x` "
        "2 Cyber factors. No own rate lookup."),
    # -- 10 more distinct families the 9 named above do not cover --
    "CommercialPropertyNonOwnedTrailersEarthquakeCoverageRules.Rule.xml": (
        "Non-Owned Trailers",
        "STRUCTURALLY DIFFERENT -- its own `SetPremium` is a 3-way `Choose` "
        "mirroring BUILDING's own top-level EQ `SetPremium` shape in "
        "miniature: a Legal Liability branch (`LegalLiabFactor x "
        "LegalLiabAddlInsurableIntFactor`), a plain `FinalEQRate` branch, and "
        "a blanket `BlktEQAvgRate` branch, each x `(LimitToUse-"
        "LimitThreshold)/100`. Not a re-run of Building's chain (it has its "
        "own `LimitThreshold`/`LimitToUse` derivation) but the SAME 3-branch "
        "shape -- C10-17's fuller job, flagged here as the first sign of it."),
    "CommercialPropertyAdditionalLocationsSpecialCoinsuranceProvisionsEarthquakeCoverageRules.Rule.xml": (
        "Additional Locations Special Coinsurance",
        "Thin wrapper, but from a DIFFERENT source than the other 8: reads "
        "`EQMLAR x CoinsuranceFactor` off ANOTHER coverage's own "
        "`CommercialPropertyAdditionalLocationsSpecialCoinsuranceGeneral"
        "Information` record (a cross-coverage read, `Exist`-gated), not off "
        "the Structure/PersonalProperty/etc.'s own EQRate/FinalEQRate chain "
        "at all."),
    "CommercialPropertyBuildersRiskReportingFormEarthquakeCoverageRules.Rule.xml": (
        "Builders Risk (Reporting Form)",
        "Genuine thin wrapper, 2-branch (non-blanket reads `../EQRate x "
        "EQDeductibleByLocationFactor x EQDeductibleFactor`; blanket reads "
        "`../../BlktEQAvgRate x ../Factor`), same shape as the top-level "
        "EQCovIndicator switch, no lookup of its own."),
    "CommercialPropertyBusinessIncomeAgreedValEarthquakeCoverageRules.Rule.xml": (
        "Business Income (Agreed Value)",
        "Thin wrapper computing an INCREMENT, not the full premium: reads "
        "`FinalEQRate` (or `BlktEQAvgRate`) x `round(Factor - 1, 3)` -- the "
        "marginal cost of the agreed-value option over the base EQ rate, the "
        "same '-1' incremental shape as Green Upgrades/Ordinance or Law "
        "above. A real pattern across several riders, not unique to one."),
    "CommercialPropertyCivilAuthorityIncreasedCoveragePeriodEarthquakeCoverageRules.Rule.xml": (
        "Civil Authority",
        "Genuine thin wrapper: `SetPremium` = `../../../FinalEQRate x "
        "../Factor x EQLimitToUse/100 x` 2 Cyber factors. No own lookup."),
    "CommercialPropertyFunctionalBuildingValuationEarthquakeCoverageRules.Rule.xml": (
        "Functional Building Valuation",
        "Reads INTERMEDIATE factors, not FinalEQRate -- `EQCauseOfLoss"
        "Adjustment x EQDeductibleByLocationFactor x EQDeductibleFactor x "
        "(Factor x PostLossFactor - 1)`, the same mid-chain-recombination "
        "shape as Radio/TV Antennas' >75ft branch and Green Upgrades, "
        "confirming this is a recurring pattern (at least 3 files) rather "
        "than a one-off."),
    "CommercialPropertyManufacturersConsequentialLossAssumptionEarthquakeCoverageRules.Rule.xml": (
        "Manufacturers Consequential Loss",
        "Genuine thin wrapper: `SetPremium` = `../../../AdjustedEQRate x "
        "../Factor x Limit/100 x` 2 Cyber factors. No own lookup."),
    "CommercialPropertyValueReportingFormEarthquakeCoverageRules.Rule.xml": (
        "Value Reporting Form",
        "Genuine thin wrapper, but a 3-way `Choose` mirroring the top-level "
        "EQCovIndicator/blanket switch (`FinalEQRate`, `EQMLAR`, or "
        "`BlktEQAvgRate`, selected by `EQCovIndicator`/`MultiLocAvgRatesIndicator`) "
        "-- same read-an-already-computed-value shape, just 3 sources "
        "instead of 1."),
    "CommercialPropertyEarthquakeInceptionExtensionRules.Rule.xml": (
        "Earthquake Inception Extension",
        "STRUCTURALLY DIFFERENT -- not a premium-bearing wrapper at all. "
        "`ErcProcess` is a bare empty `<rul:Sequence />`; there is no "
        "`SetPremium` rule in the file whatsoever. A pure metadata/attachment "
        "marker, not a rate computation of any kind."),
    "CommercialPropertyUtilityServicesTimeElementDetailEarthquakeCoverageRules.Rule.xml": (
        "Utility Services (Time Element)",
        "Genuine thin wrapper: `SetPremium` = `../EQRate x WaitingPeriodFactor "
        "x EQLimitToUse/100 x` 2 Cyber factors. No own lookup."),
}


def main() -> int:
    book = book_for("CW", ASOF)
    rules_dir = book.state.package.content / "Rules"
    all_files = sorted(p.name for p in rules_dir.glob("*Earthquake*"))
    print(f"=== Population re-confirmed: {len(all_files)} files "
          f"(census claim: 97, {'MATCH' if len(all_files) == 97 else 'DOES NOT MATCH'})\n")

    print(f"=== {len(READ)} files read in full, by family, direct read verdicts\n")
    thin, not_thin = [], []
    for fn, (fam, verdict) in READ.items():
        assert fn in all_files, f"{fn} not in the 97-file population!"
        tag = "THIN WRAPPER" if verdict.startswith("Genuine thin wrapper") else "FLAGGED"
        (thin if tag == "THIN WRAPPER" else not_thin).append((fam, fn))
        print(f"    [{tag:12s}] {fam}")
        print(f"        {fn}")
        for line in re.findall(r".{1,96}(?:\s|$)", verdict):
            print(f"        {line.strip()}")
        print()

    print(f"=== Summary: {len(thin)} of {len(READ)} read files are genuine "
          f"thin wrappers (read an already-computed EQ value, multiply by "
          f"limit/100 and 2 Cyber factors, no lookup of their own); "
          f"{len(not_thin)} are flagged as structurally different:\n")
    for fam, fn in not_thin:
        print(f"    {fam} ({fn})")

    print("\n=== What this means for the census's own claim\n")
    print("    The census's 'thin wrapper reading an already-computed EQ "
          "rate' description holds for the MAJORITY of families read here "
          f"({len(thin)} of {len(READ)}), but is an OVERSIMPLIFICATION for "
          f"{len(not_thin)}: Peak Season (a cross-coverage subtraction, not "
          "a read-and-multiply), Non-Owned Trailers and Value Reporting "
          "Form (each a miniature re-run of the top-level EQCovIndicator/"
          "blanket 'Choose' rather than one value), Radio/TV Antennas' "
          ">75ft branch and Functional Building Valuation/Green Upgrades "
          "(reading INTERMEDIATE EQ factors and recombining them locally, "
          "not the terminal FinalEQRate), Ordinance or Law/Business Income "
          "Agreed Value (an INCREMENTAL premium computed as Factor-1, not "
          "the full rate), and the Earthquake Inception Extension (not a "
          "premium computation at all -- an empty attachment marker). None "
          "of these compute their OWN base-rate Lookup from a Rate Table -- "
          "every one still ultimately depends on the 5 parent files' own "
          "EQ chain, which is the load-bearing part of the census's claim "
          "and is confirmed to hold. No engine gap.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
