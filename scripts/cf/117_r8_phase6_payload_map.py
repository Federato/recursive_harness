"""R-8 Phase 6 -- the payload spec, collapsed onto `IN - Schedule`.

Payload generator Step 3 (`CF_Payload_Sheet_Spec_Step3.html`) specified a `Payload
Export` sheet whose main job was to transpose the old column-per-item input tabs into
one row per record with ID + ParentID. After R-8 Phase 5 the input sheet IS that
shape. What the spec still owns is the mapping from each Schedule column to its ISO
record and field, with the format conversions (T-1..T-7), the aliases, the RECORDS
block for exclusions, and the fields deliberately omitted for v1. This writes that map.

Read-only: no workbook access. Output: `CF_Algorithm/CF_Payload_Schedule_Map.csv`.
"""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / "CF_Algorithm" / "CF_Payload_Schedule_Map.csv"

ST, OC, PP = ("CommercialPropertyStructure", "CommercialPropertyOccupClass",
              "CommercialPropertyPersonalProperty")
LOC, BI = "CommercialPropertyLocation", "CommercialPropertyBusinessIncome"
SCR, SCB = "CommercialPropertySpecialClass", "CommercialPropertySpecialClassBusnIncome"
COINS = '0.8 -> "80%"'
REC = "Yes -> [{}]"
KEYS = [("A", "ID", "(key)", "", "join key; not sent"),
        ("C", "Active", "(filter)", "", "emit only Active = Yes")]

#: block -> (ISO record, parent block, [(col, header, iso field, conversion, note)])
MAP = {
    "LOCATION": (LOC, None, [
        ("A", "ID", "(key)", "", "join key; not sent"),
        ("B", "Active", "(filter)", "", "emit only Active = Yes"),
        ("C", "State", "SchemeKeys.ProductName", '"Commercial Property " & State',
         "T-3: not a field -- one payload per state"),
        ("D", "ZipCode", "ZipCode", "text, 5 digits", "T-2"),
        ("E", "City", "City", "", ""),
        ("F", "ProtClass", "ProtectClass", "text", ""),
        ("G", "BGITerr", "BasicGroupIRatingTerr", "", ""),
        ("H", "District", "District", "", "alias resolved in Step 3"),
        ("I", "BGIITerr", "BasicGroupIIRatingTerr", "", ""),
        ("J", "SpecialTerr", "SpecialRatingTerr", "", ""),
        ("K", "WindHailDed", "WindstormOrHailDeductible", "",
         "ISO refused Contents payloads without it (chunk 4)"),
        ("L", "MultiResCredit", "MultipleResidentialPropSpecialCredit", "", ""),
        ("M", "HeatingPlantLoc", "-", "", "OMIT v1 -- no ISO field in 408 payloads; check DataDef"),
        ("N", "PerLocationDed", "(record)", "Yes -> CommercialPropertyDeductiblesByLocationBldg [{Deductible}] on each Structure", "an endorsement record, not a field (fixed 2026-09-22)"),
    ]),
    "BUILDING": (ST, "LOCATION", [
        ("B", "ParentID", "(join -> LOCATION.ID)", "", ""),
        ("D", "CovType", "CovType", "", ""),
        ("E", "ClassCode", "ClassCode", "text, 4 digits", ""),
        ("F", "ClassDesc", "ClassificationDescription", "", "alias"),
        ("G", "RatingType", "RatingType; RatingTypeBasicGroupII = \"Class\"", "", "the rater applies a specific rate to Group I only; Defaults #10 (= RatingType) made ISO price Group II at 0 on a Specific building (fixed 2026-09-22)"),
        ("H", "ConstrCode", "-", "", "T-5: not sent; ISO derives it from ConstructionType"),
        ("I", "ConstrType", "ConstructionType", "", "T-5"),
        ("J", "ConstrSymbol", "BasicGroupIISymbol", "", "alias"),
        ("K", "NumStories", "NumStories", "", ""),
        ("L", "BCEG", "BCEG (+ BCEGClass)", "", "T-4"),
        ("M", "OpenSides", "OpenSides", "", ""),
        ("N", "Limit", "Limit + FullBldgValue", "FullBldgValue = Limit", "D-2 decision"),
        ("O", "SpecificRate", "SpecificGroupIRate", "", "alias; only when RatingType = Specific"),
        ("P", "CauseOfLoss", "CauseOfLoss", "", ""),
        ("Q", "Deductible", "Deductible", "", 'T-6: already "2,500"'),
        ("R", "TheftDed", "TheftDeductible", "", ""),
        ("S", "WindHailDed", "WindstormOrHailDeductible", "", ""),
        ("T", "Valuation", "ValuationType", "", "alias"),
        ("U", "Coinsurance", "Coinsurance", COINS, "T-1"),
        ("V", "SprinklerSystem", "SprinklerSystem", "", ""),
        ("W", "SprinklerLeakageExcl", "(record)", REC, "RECORDS block"),
        ("X", "Vacancy", "VacantBuilding", "", "alias"),
        ("Y", "RoofSurfacing", "(record)", "Paragraph A/B/A and B -> [{Applicability: value}]", "CommercialPropertyLimitationsOnCovForRoofSurfacing -- Step 3 said omit; it moves the premium (fixed 2026-09-22)"),
        ("Z", "SubStdA", "SubStdConditionA", "", ""),
        ("AA", "SubStdB", "SubStdConditionB", "", ""),
        ("AB", "SubStdC", "SubStdConditionC", "", ""),
        ("AC", "SubStdD", "SubStdConditionD", "", ""),
        ("AD", "SubStdE", "SubStdConditionE", "", ""),
        ("AE", "WindHailExcl", "(record)", REC, "RECORDS: Structure wind/hail exclusion"),
        ("AF", "VandalismExcl", "(record)", REC, "RECORDS: CommercialPropertyVandalismExclusion"),
        ("AG", "TheftExcl", "(record)", REC, "RECORDS: Structure theft exclusion"),
        ("AH", "AddlInsurableIntOption", "AddlInsurableIntOption", "", "Legal Liability only (Z-1)"),
        ("AI", "ConstrDesc", "-", "", "derived; not sent"),
    ]),
    "OCCUPANCY CLASS": (OC, "BUILDING", [
        ("B", "ParentID", "(join -> BUILDING.ID)", "", ""),
        ("D", "ClassCode", "ClassCode", "text, 4 digits", "the tenant class code"),
        ("E", "OccupCategory", "OccupCategory", "", ""),
        ("F", "OccupSeverity", "-", "", "OMIT v1 -- derived; check DataDef"),
        ("G", "ContentsGroup", "-", "", "derived; not sent"),
        ("H", "CovForm", "CovForm", "", "selects the Legal Liability form; when it does, also emit CommercialPropertyLegalLiabilityCoverageFormOccupClass [{AddlInsurableInt: description, AddlInsurableIntOption}] from the building's option, or ISO's contents AII factor is 0.0 (Z-1)"),
        ("I", "YardProperty", "-", "", "OMIT v1 -- check DataDef"),
    ]),
    "CONTENTS": (PP, "OCCUPANCY CLASS", [
        ("B", "ParentID", "(join -> OCCUPANCY CLASS.ID)", "", ""),
        ("D", "CovType", "CovType", "", ""),
        ("E", "Limit", "Limit", "", ""),
        ("F", "SpecificRate", "SpecificGroupIRate", "only when the building is Specific", "the rater uses it (Contents row 3); ISO reads it on the PP record"),
        ("G", "Coinsurance", "Coinsurance", COINS, "T-1"),
        ("H", "Valuation", "ValuationType", "", ""),
        ("I", "WindHailExcl", "(record)", REC, "RECORDS: ...ExclusionPrsnlProp"),
        ("J", "VandalismExcl", "(record)", REC, "RECORDS"),
        ("K", "TheftExcl", "(record)", REC, "RECORDS"),
        ("L", "ParentBldg", "-", "", "derived key; not sent"),
        ("M", "WatchmanService", "-", "", "OMIT v1 -- check DataDef"),
        ("N", "BurglaryAlarmType", "-", "", "OMIT v1 -- check DataDef"),
        ("O", "BurglaryRange", "-", "", "derived; not sent"),
        ("P", "BurglaryFactor", "-", "", "OMIT v1"),
    ]),
    "BUSINESS INCOME": (BI, "BUILDING", [
        ("B", "ParentID", "(join -> BUILDING.ID)", "", "parent is the Structure, not the OccupClass"),
        ("D", "CovType", "CovType", "", ""),
        ("E", "TypeOfRisk", "TypeOfRisk", "", ""),
        ("F", "PctType1", "-", "", "T-7: maps into the shared BI Factor"),
        ("G", "PctType2", "-", "", "T-7"),
        ("H", "Limit", "Limit", "", ""),
        ("I", "SpecificRate", "SpecificGroupIRate", "only when the building is Specific", "the rater uses it (BI row 3)"),
        ("J", "Coinsurance", "Coinsurance", COINS, "T-1"),
        ("K", "MaxPeriodIndemnity", "MaxPeriod", "", ""),
        ("L", "MonthlyLimitIndemnity", "MonthlyLimitOfIndemnity", "", ""),
        ("M", "ExtraExpenseSchedule", "ExtraExpenseLimitOnLossPayment", "", "alias (Extra Expense Loss Payment Schedule)"),
        ("N", "WindHailExcl", "(record)", REC, "RECORDS"),
        ("O", "VandalismExcl", "(record)", REC, "RECORDS"),
        ("P", "TheftExcl", "(record)", REC, "RECORDS"),
    ]),
    "SPECIAL CLASS": (SCR, "LOCATION", [
        ("B", "ParentID", "(join -> LOCATION.ID)", "", ""),
        ("D", "ItemDesc", "ClassDescription", "", ""),
        ("E", "CauseOfLoss", "CauseOfLoss", "", ""),
        ("F", "InclInBlanket", "IncludedInBlkt", "", ""),
        ("G", "ValuationType", "ValuationType", "", ""),
        ("H", "AgreedValue", "AgreedValueOption", "", "alias"),
        ("I", "BuildingCoins", "Coinsurance", COINS, "T-1"),
        ("J", "ContentsCoins", "-", "", "not sent -- ISO SpecialClass carries one Coinsurance"),
        ("K", "BuildingLimit", "Limit + FullSpecialClassValue", "FullSpecialClassValue = Limit", "D-2"),
        ("L", "LimitInclInBuilding", "IncludedInBuilding", "", "alias"),
        ("M", "LinkedBuildingItemID", "-", "", "derived; not sent"),
        ("N", "Deductible", "Deductible", "", ""),
        ("O", "DedByLocation", "(record)", "Yes -> CommercialPropertyDeductiblesByLocationSpecialClass [{Deductible}]", "an endorsement record (fixed 2026-09-22); ClassCode is also sent, from the rater's own derivation (Special Class row 173) -- ISO's vandalism rule gates on it"),
        ("P", "ProtClass", "-", "", "not sent -- ISO SpecialClass has no ProtectClass; it inherits the Location's. The rater prices on the item's own (W-10)"),
        ("Q", "BGIITerr", "BasicGroupIIRatingTerr", "", "ISO copies it from the Location"),
        ("R", "ConstrSymbol", "BasicGroupIISymbol", "", "W-8: the item's own symbol"),
        ("S", "WindHailDed", "WindstormOrHailDeductible", "", ""),
        ("T", "TheftDed", "TheftDeductible", "", ""),
        ("U", "VandalismExcl", "(record)", REC, "RECORDS: ...ExclusionSpecialClass"),
        ("V", "WindHailExcl", "(record)", REC, "RECORDS"),
        ("W", "TheftExcl", "(record)", REC, "RECORDS"),
    ]),
    "SC BUSINESS INCOME": (SCB, "SPECIAL CLASS", [
        ("B", "ParentID", "(join -> SPECIAL CLASS.ID)", "", ""),
        ("D", "CovType", "CovType", "", ""),
        ("E", "TypeOfRisk", "TypeOfRisk", "", ""),
        ("F", "PctType1", "-", "", "T-7"),
        ("G", "PctType2", "-", "", "T-7"),
        ("H", "Limit", "Limit", "", "the priced SC BI limit (W-9 resolved)"),
        ("I", "Coinsurance", "Coinsurance", COINS, "T-1"),
        ("J", "MaxPeriodIndemnity", "MaxPeriod", "", ""),
        ("K", "MonthlyLimitIndemnity", "MonthlyLimitOfIndemnity", "", ""),
        ("L", "ExtraExpenseSchedule", "ExtraExpenseLimitOnLossPayment", "", "alias"),
        ("M", "VandalismExcl", "(record)", REC, "RECORDS: ...SpclClassBusnIncome -- S-1 now separately electable"),
        ("N", "WindHailExcl", "(record)", REC, "RECORDS -- S-2"),
        ("O", "TheftExcl", "(record)", REC, "RECORDS -- S-3"),
    ]),
}


def kind(field: str, note: str) -> str:
    if field == "(record)":
        return "record"
    if field.startswith("("):
        return "key/filter"
    if field == "-":
        return "check" if note.startswith("CHECK") else "not sent"
    return "sent"


def main() -> int:
    rows = []
    for block, (record, parent, cols) in MAP.items():
        full = cols if block == "LOCATION" else [KEYS[0]] + cols[:1] + [KEYS[1]] + cols[1:]
        for col, hdr, field, conv, note in full:
            rows.append({"block": block, "column": col, "schedule_header": hdr,
                         "iso_record": record, "parent_block": parent or "",
                         "iso_field": field, "kind": kind(field, note),
                         "conversion": conv, "note": note})
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} Schedule columns -> {OUT.name}")
    print(" ", dict(Counter(r["kind"] for r in rows)))
    for r in rows:
        if r["kind"] == "check":
            print(f"  CHECK  {r['block']}.{r['column']} {r['schedule_header']}: {r['note']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
