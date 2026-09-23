#!/usr/bin/env python3
"""Chunk 10, C10-02 -- row counts and chain-membership for all 66 EQ-named
Rate Tables (census Sec.7), re-confirmed directly rather than carried over
from the census's own printed summary, same discipline as C9-04.

Two things the census did NOT do, both done here:

  1. Row counts and state-filing counts for ALL 66 (the census sampled 6).
  2. Classify each of the 66 into one of four buckets, based on WHO reads it
     (direct `MatrixDef="<table>Def"` search across every countrywide rule
     file, not just the 97-file Earthquake population or the 5 parent files):

       A. CORE CHAIN   -- read inside one of the 5 parent files' own EQ
                          engine rules (`SetEQBaseRate`..`SetFinalEQRate`,
                          C10-01's traced path) or `CommercialPropertyLocation
                          Rules`'s EQ-input resolution step.
       B. SUB-LIMIT / FLAT-DEDUCTIBLE CHAIN -- read only inside the 20-file
                          `EarthquakeAndVolcanicEruption*` core Endorsement
                          family (census Sec.1) -- the build order's own
                          "sub-limit and flat-dollar-deductible variants"
                          callout, C10-19's fuller job but in THIS chunk's
                          scope per the build order's own sentence.
       C. OUT OF SCOPE  -- read only by a DIFFERENT coverage form entirely
                          (Ordinance or Law, Outside Signs, Radio/TV Antennas,
                          Builders Risk Renovations, Limited Coverage for
                          Unmanned Aircraft, or a bare policy/location-level
                          stat code) -- confirmed by filename, not assumed.
       D. DEAD          -- zero `Lookup MatrixDef` reference anywhere in the
                          corpus (census's own 12, re-confirmed here).

    python scripts/cf/86_chunk10_c10-02_tables.py

Always exits 0 -- a census, not a test.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from cf_engine.resolve import CFEditionResolver, book_for

ASOF = "20260917"

TABLES = [
    "ASLOBEarthquake", "BCEGEQFactor", "BCEGEarthquakeFactor", "BldrsRiskEQFactor",
    "EQClassToUse", "EQExposureBaseStatCode", "EQFlatDeductibleFactor",
    "EQLossCostBldg", "EQLossCostPrsnlProp", "EQPercentageDeductibleFactor",
    "EQRateBldg", "EQRatePrsnlProp", "EQRoofTankHazardFactor",
    "EQSprinklerLeakageCoinsuranceFactor", "EQSprinklerLeakageOnlyBldgFactor",
    "EQSprinklerLeakageOnlyLessThan80PctFactor", "EQSprinklerLeakageOnlyPrsnlPropFactor",
    "EQSprinkleredRiskFactor",
    "EQSubLimit1000000FlatDeductibleFactor", "EQSubLimit100000FlatDeductibleFactor",
    "EQSubLimit10000FlatDeductibleFactor", "EQSubLimit1000FlatDeductibleFactor",
    "EQSubLimit250000FlatDeductibleFactor", "EQSubLimit25000FlatDeductibleFactor",
    "EQSubLimit2500FlatDeductibleFactor", "EQSubLimit500000FlatDeductibleFactor",
    "EQSubLimit50000FlatDeductibleFactor", "EQSubLimit5000FlatDeductibleFactor",
    "EQSubLimit500FlatDeductibleFactor", "EQSubLimit750000FlatDeductibleFactor",
    "EQSubLimit75000FlatDeductibleFactor", "EQSubLimitDeductibleFactor",
    "EQSubLimitDeductibleTierCWTable", "EQSubLimitPctToTimeElementCoinsurance",
    "EQSublimitSprinklerLeakageFactor",
    "EarthquakeAttachmentIndicatorCode", "EarthquakeBuildingCoverageCode",
    "EarthquakeBuildingHeightStatCode", "EarthquakeConstructionStatCode",
    "EarthquakeDeductibleStatCode", "EarthquakeDeductibleTier",
    "EarthquakeExposureBaseStatCode", "EarthquakeFlatDollarDeductibleStatCode",
    "EarthquakeNoBuildingHeightStatCode", "EarthquakeNonSprinkleredBlanketRiskIDCode",
    "EarthquakeNonSprinkleredNonBlanketRiskIDCode",
    "EarthquakeOtherThanSprinklerLeakageExtensionCoverage",
    "EarthquakePrsnlPropertyCoverageCode", "EarthquakeRateGradeStatCode",
    "EarthquakeSprinklerLeakageExtensionCoverage",
    "EarthquakeSprinkleredBlanketRiskIDCode", "EarthquakeSprinkleredNonBlanketRiskIDCode",
    "EarthquakeSubLimitCoverage", "EarthquakeSubLimitExposureBaseStatCode",
    "EarthquakeSubLimitSprinklerLeakageExtensionCoverage",
    "EarthquakeSubLimitTimeElementFactor", "EarthquakeSusceptibilityGradeStatCode",
    "EarthquakeTimeElementCoverageCode",
    "OrdOrLawIncrPeriodOfRestorationEQFactor", "OrdinanceOrLawCovAEQFactor",
    "PctOfMasonryVeneerEQFactor",
    "SprinklerLeakageEQExtensionBldgRate", "SprinklerLeakageEQExtensionPrsnlPropRate",
    "SprinklerLeakageEQExtensionZoneFactor", "SublineEarthquake", "TypeOfPolicyEQStatCode",
]
assert len(TABLES) == 66, len(TABLES)

CORE_PARENT_FILES = {
    "CommercialPropertyStructureRules.Rule.xml",
    "CommercialPropertyPersonalPropertyRules.Rule.xml",
    "CommercialPropertyBusinessIncomeRules.Rule.xml",
    "CommercialPropertySpecialClassRules.Rule.xml",
    "CommercialPropertySpecialClassBusnIncomeRules.Rule.xml",
    "CommercialPropertyLocationRules.Rule.xml",  # EQDeductibleTier resolution -- feeds the same chain
}
#: the 20-file core Endorsement family (census Sec.1) -- the build order's own
#: "sub-limit and flat-dollar-deductible variants" callout.
CORE_ENDORSEMENT_FILES_MARKER = "EarthquakeAndVolcanicEruption"

#: other-coverage consumers, confirmed by filename, not assumed -- each is a
#: DIFFERENT optional CF coverage with its OWN EQ extension, out of THIS
#: chunk's Building/Contents/BusinessIncome/SpecialClass/SCBI-EQ scope.
OUT_OF_SCOPE_MARKERS = {
    "OrdinanceOrLaw": "Ordinance or Law coverage's own EQ rider -- a different, unbuilt CF coverage",
    "OutsideSigns": "Outside Signs coverage's own EQ base-rate read",
    "RadioOrTelevisionAntennas": "Radio/TV Antennas coverage's own EQ base-rate read",
    "BuildersRiskRenovations": "Builders Risk Renovations coverage's own EQ factor read (distinct from Structure's own BldrsRiskEQFactor read, which IS in scope)",
    "LimitedCoverageForUnmannedAircraft": "Unmanned Aircraft coverage -- blocked/unbuilt per this project's rater-gap tracking (project_memory: rater-missing-coverages)",
    "CommercialPropertyRules.Rule.xml": "policy-level stat code, not a rate factor",
}


def main() -> int:
    res = CFEditionResolver()
    juris = sorted(res.jurisdictions)
    books = {j: book_for(j, ASOF, resolver=res) for j in juris}
    any_book = books[juris[0]]
    rules_dir = any_book.parent.package.content / "Rules"
    tables_dir = any_book.parent.package.content / "Rate Tables"

    all_rule_files = list(rules_dir.glob("*.xml"))
    bodies = {p.name: p.read_text(encoding="utf-8-sig") for p in all_rule_files}

    print(f"=== A  Row counts and state-filing counts, all 66, re-confirmed "
          f"directly ({len(juris)} jurisdictions, as of {ASOF})\n")
    header_only, has_rows = [], []
    for t in TABLES:
        cw = any_book.parent_table(t)
        own = [j for j, b in books.items() if b.declares(t) == "state"]
        (header_only if len(cw.rows) == 0 else has_rows).append(t)
        print(f"    {t:52s} CW rows={len(cw.rows):<4d} states filing="
              f"{len(own):2d} of {len(juris)}" + ("   " + ",".join(own) if own else ""))
    print(f"\n    header-only at CW: {len(header_only)} of 66   "
          f"carrying rows at CW: {len(has_rows)} of 66 "
          f"(census's own 17/49 split, re-confirmed: "
          f"{'MATCH' if (len(header_only), len(has_rows)) == (17, 49) else 'DOES NOT MATCH'})")

    print("\n=== B  Chain-membership classification, all 66 -- who reads each "
          "table, by direct MatrixDef search\n")

    def consumer_files(table: str) -> list[str]:
        matrix_def = table + "Def"
        return sorted({fn for fn, body in bodies.items()
                       if re.search(rf'MatrixDef="{re.escape(matrix_def)}"', body)})

    buckets = {"A_CORE": [], "B_SUBLIMIT": [], "C_OUT": [], "D_DEAD": []}
    detail = {}
    for t in TABLES:
        files = consumer_files(t)
        if not files:
            buckets["D_DEAD"].append(t)
            detail[t] = ("D_DEAD", "zero Lookup MatrixDef reference anywhere in the corpus")
            continue
        in_core = [f for f in files if f in CORE_PARENT_FILES]
        in_endorsement_core = [f for f in files if CORE_ENDORSEMENT_FILES_MARKER in f]
        out_files = [f for f in files if f not in CORE_PARENT_FILES
                     and CORE_ENDORSEMENT_FILES_MARKER not in f]
        if in_core:
            buckets["A_CORE"].append(t)
            note = f"read by {in_core}"
            if out_files:
                note += f"  ALSO read by out-of-scope consumer(s): {out_files}"
            detail[t] = ("A_CORE", note)
        elif in_endorsement_core:
            buckets["B_SUBLIMIT"].append(t)
            detail[t] = ("B_SUBLIMIT", f"read only inside the 20-file core Endorsement "
                         f"family, e.g. {in_endorsement_core[0]}")
        else:
            buckets["C_OUT"].append(t)
            reasons = []
            for f in out_files:
                for marker, why in OUT_OF_SCOPE_MARKERS.items():
                    if marker in f:
                        reasons.append(why)
                        break
                else:
                    reasons.append(f"consumed only by {f}")
            detail[t] = ("C_OUT", "; ".join(sorted(set(reasons))) or f"{out_files}")

    for t in TABLES:
        bucket, note = detail[t]
        print(f"    [{bucket:10s}] {t:48s} {note}")

    print(f"\n    Totals: A(core chain)={len(buckets['A_CORE'])}  "
          f"B(sub-limit/flat-deductible chain)={len(buckets['B_SUBLIMIT'])}  "
          f"C(out of scope)={len(buckets['C_OUT'])}  D(dead)={len(buckets['D_DEAD'])}  "
          f"sum={sum(len(v) for v in buckets.values())} of 66")

    print("\n    D (dead), re-confirmed against the census's own 12: "
          + ("MATCH" if sorted(buckets["D_DEAD"]) == sorted([
              "ASLOBEarthquake", "BCEGEQFactor", "EQRateBldg", "EQRatePrsnlProp",
              "EQRoofTankHazardFactor", "EQSprinklerLeakageOnlyLessThan80PctFactor",
              "EQSubLimitDeductibleFactor", "EarthquakeExposureBaseStatCode",
              "EarthquakeRateGradeStatCode", "SprinklerLeakageEQExtensionBldgRate",
              "SprinklerLeakageEQExtensionPrsnlPropRate", "SprinklerLeakageEQExtensionZoneFactor",
          ]) else "DOES NOT MATCH -- see list above"))

    print("\n=== C  What this means for THIS chunk's scope\n")
    print(f"    {len(buckets['A_CORE'])} of 66 tables are genuinely IN the "
          f"golden case's own chain (Building's plain percentage-deductible "
          f"path plus the analogous Contents/SpecialClass/BusinessIncome/SCBI "
          f"paths and the Location-level EQDeductibleTier resolution step).")
    print(f"    {len(buckets['B_SUBLIMIT'])} are IN the sub-limit/flat-"
          f"dollar-deductible chain the build order's own sentence named -- "
          f"reachable only through the 4 non-plain AttachForm* variants "
          f"C10-01 read but did not exercise (C10-19's fuller job).")
    print(f"    {len(buckets['C_OUT'])} are OUT OF SCOPE for chunk 10 "
          f"entirely -- they belong to five OTHER optional CF coverages "
          f"(Ordinance or Law, Outside Signs, Radio/TV Antennas, Builders "
          f"Risk Renovations, Unmanned Aircraft) that happen to file their "
          f"OWN independent EQ rider/extension, a consumer population the "
          f"census's filename-only scan (Rules/*Earthquake*) never surfaced "
          f"because none of those 5 coverages' own rule files are named "
          f"*Earthquake* -- a structurally new finding this task adds.")
    print(f"    {len(buckets['D_DEAD'])} are DEAD -- re-confirmed, not just "
          f"re-cited from the census.")
    print("\n    One item flagged, not resolved here: `EarthquakeDeductibleTier` "
          "is read by a real `LookupEarthquakeDeductibleTier` rule inside "
          "`CommercialPropertyLocationRules.Rule.xml` -- meaning EQDeductibleTier "
          "may have a DERIVATION path, not only the raw-submission-input "
          "treatment the golden case gave it (which set it directly to \"1\"). "
          "Whether that Lookup rule ever actually WRITES EQDeductibleTier, or "
          "only reads/validates it, is not settled here -- flagged for chunk "
          "10's open-items list, not this task's job to resolve.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
