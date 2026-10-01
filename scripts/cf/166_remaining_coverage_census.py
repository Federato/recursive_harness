#!/usr/bin/env python3
"""Remaining-coverage census -- everything chunks 0-14 did not build, sized and ordered.

Chunks 0-14 closed 2026-09-24. This census takes every countrywide rule file
with a `SetPremium` (546), removes the ones the closed chunks own, groups the
rest into coverage families by hand-written filename patterns, and sizes each
family so the next chunks can be ordered easy -> hard:

  files      premium files in the family (countrywide)
  tables     rate tables its rules read; how many are 0-row / unfiled countrywide
  states     of 46 in-force state packages (PR excluded), how many rewrite a family file
  fixtures   ISO STC payloads (364) that carry one of the family's records
  replayed   stored ISO responses (293) with a NON-ZERO premium on a family record --
             every one of those already equals ours (157_, 14,236 of 14,236), so a
             family with replayed > 0 is ISO-confirmed on at least that shape already
  gaps       rul: elements the engine does not register
  reads      the family reads another record's finished Premium (downstream coverage)

It also sweeps every state package in every batch for premium files whose
name is not a countrywide file (state-only coverages such as MA heating oil).

    python scripts/cf/166_remaining_coverage_census.py

Always exits 0 -- a census, not a test.
"""
from __future__ import annotations

import collections
import csv
import json
import re
import sys
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from cf_engine.resolve import book_for
from gl_engine.interp import nodes

census11 = import_module("106_chunk11_census")
ASOF = "20260917"
ROOT = Path(__file__).resolve().parents[2]
ISO_CF = Path("C:/Projects/ISO_ERC_Files/CF")
RES = ROOT / "results" / "cf-raas"
STRUCTURAL = {"Rules", "Rule", "MetaData", "MetaDataCode", "Test", "Then", "Else",
              "Keys", "When", "Otherwise", "Arg", "Param"}

#: what chunks 0-14 own (premium files)
BUILT = re.compile(
    r"Terror|TRIA|Earthquake|Leasehold|OrdinanceOrLaw|DebrisRemoval|UtilityServices|Unmanned|"
    r"GreenUpgrade|DependentPropert|LegalLiab|Trailer|"
    r"^CommercialProperty(Structure(Building)?|PersonalProperty(PrsnlProp)?|BusinessIncome|SpecialClass|"
    r"SpecialClassBusnIncome|SpecialClassBusinessIncome)(BasicGroupI|BasicGroupII|Broad|Special)?"
    r"(CoverageRules|Rules)\.Rule\.xml$")

#: family -> filename regex (after the CommercialProperty prefix)
FAMILIES = [
    ("Agreed Value", r"AgreedVal"),
    ("Inflation Guard", r"InflationGuard"),
    ("Additional Covered Property", r"AdditionalCoveredProperty"),
    ("Additional Locations Special Coinsurance", r"AdditionalLocationsSpecialCoinsurance"),
    ("Brands and Labels", r"BrandsAndLabels"),
    ("Builders Risk", r"BuildersRisk"),
    ("Theft of Building Materials (not BR)", r"TheftOfBuildingMaterialsAndSupplies"),
    ("BI Y2K / electronic problems", r"Y2K"),
    ("BI no waiting period", r"BeginningOfThePer"),
    ("Extended Period of Indemnity", r"ExtendedPeriodOfIndemnity"),
    ("Interruption of Computer Operations", r"InterruptionOfComputerOperations"),
    ("Landlord as Additional Insured (Rental Value)", r"LandlordAsAdditionalInsured"),
    ("Watercraft Exclusion Buyback", r"WatercraftExclusionBuyback"),
    ("Limited International Coverage", r"LimitedInternationalCov"),
    ("Cannabis Exclusion", r"CannabisExclusion"),
    ("Fungus, Wet Rot, Dry Rot changes", r"ChangesFungus"),
    ("Civil Authority increased period", r"CivilAuthority"),
    ("Condo Unit-Owners Optional Coverages", r"CondominiumCommercialUnitOwners"),
    ("Sewer / drain backup", r"DischargeFromSewer"),
    ("Discretionary Payroll Expense", r"DiscretionaryPayroll"),
    ("Electronic Commerce", r"ElectronicCommerce"),
    ("Equipment Breakdown", r"EquipmentBreakdown"),
    ("Flood", r"Flood"),
    ("Food Contamination", r"FoodContamination"),
    ("Functional Valuation", r"Functional(Building|PersonalProperty)Valuation"),
    ("Household Personal Property", r"HouseholdPersonalProperty"),
    ("Increase in Rebuilding Expenses after Disaster", r"IncreaseInRebuildingExpenses"),
    ("Leased Property", r"LeasedPropertyDetail"),
    ("Fire Department Service Charge", r"FireDepartmentCharge"),
    ("Newly Acquired Location (time element)", r"NewlyAcquiredLocationTimeElement"),
    ("Manufacturers Consequential Loss", r"ManufacturersConsequentialLoss"),
    ("Mining Properties BI", r"MiningProperties"),
    ("Mortgageholders E&O", r"MortgageholdersErrors"),
    ("Newly Acquired Property increased limit", r"NewlyAcquiredOrConstructed"),
    ("Portable Storage Units", r"PortableStorageUnits"),
    ("Off-Premises Interruption (vehicles)", r"OffPremInterruption"),
    ("Ordinary Payroll Limitation", r"OrdinaryPayroll"),
    ("Outdoor Trees, Shrubs and Plants", r"OutdoorTrees"),
    ("Outside Signs", r"OutsideSigns"),
    ("Peak Season", r"PeakSeason"),
    ("Special Cause of Loss (furs, jewelry, patterns, stamps)", r"PersonalPropertySpecialCOL"),
    ("Tobacco Sales Warehouses", r"TobaccoSales"),
    ("Pier and Wharf", r"PierAndWharf"),
    ("Pollutant Clean Up aggregate", r"PollutantCleanUp"),
    ("Power, Heat and Refrigeration Deduction", r"PowerHeatAndRefrigeration"),
    ("Radio / TV Antennas", r"RadioOrTelevisionAntennas"),
    ("Vacancy Permit", r"VacancyPermit"),          # before Molten / Radioactive: it has riders named for both
    ("Molten Material", r"MoltenMaterial"),
    ("Radioactive Contamination", r"RadioactiveContamination"),
    ("Tenants' Building Property / Glass", r"BuildingPropertyTenantsPolicy"),
    ("Property Temporarily Away", r"TempAwayFromPremises"),
    ("Spoilage", r"Spoilage"),
    ("Valuable Papers", r"ValuablePapers"),
    ("Value Reporting Form", r"ValueReportingForm"),
]


#: families closed by chunks after the plan was drawn (2026-09-25), counted as built
CLOSED = {
    # chunk 15 (gated 2026-09-25): the manual-premium endorsements, 23 files
    "Cannabis Exclusion", "Valuable Papers", "Newly Acquired Location (time element)",
    "Newly Acquired Property increased limit", "Portable Storage Units", "Discretionary Payroll Expense",
    "Electronic Commerce", "Limited International Coverage", "Interruption of Computer Operations",
    "BI Y2K / electronic problems",
    # chunk 16 (gated 2026-09-25): the rated Business Income options and the small property adds, 39 files
    "BI no waiting period", "Extended Period of Indemnity", "Civil Authority increased period",
    "Pollutant Clean Up aggregate", "Molten Material", "Spoilage",
    # chunk 17 (gated 2026-09-28): the Business Income add-ons, 32 files
    "Ordinary Payroll Limitation", "Power, Heat and Refrigeration Deduction", "Mining Properties BI",
    "Landlord as Additional Insured (Rental Value)", "Watercraft Exclusion Buyback",
    "Off-Premises Interruption (vehicles)",
    # chunk 18 (gated 2026-09-29): the valuation and condition modifiers, 84 files
    "Agreed Value", "Inflation Guard", "Functional Valuation", "Increase in Rebuilding Expenses after Disaster",
    "Vacancy Permit", "Peak Season",
    # chunk 19 (gated 2026-09-29): the scheduled property items, 63 files
    "Tenants' Building Property / Glass", "Radio / TV Antennas", "Outdoor Trees, Shrubs and Plants", "Outside Signs",
    "Brands and Labels", "Household Personal Property", "Leased Property", "Property Temporarily Away",
    "Manufacturers Consequential Loss",
    # chunk 20 (gated 2026-09-29): small coverages with their own tables, 28 files
    "Radioactive Contamination", "Pier and Wharf", "Fire Department Service Charge", "Tobacco Sales Warehouses",
    "Special Cause of Loss (furs, jewelry, patterns, stamps)", "Additional Covered Property", "Food Contamination",
    "Mortgageholders E&O", "Fungus, Wet Rot, Dry Rot changes", "Equipment Breakdown",
    # chunk 21 (census closed 2026-09-30, C21-20): sewer backup and the condo unit-owners options, 7 CW files
    # (FL's 5 state-only condo files are not in this countrywide count)
    "Sewer / drain backup", "Condo Unit-Owners Optional Coverages",
    # chunk 22 (census closed 2026-10-01, C22-23): multi-location, 16 CW files ("Used" is unpriceable at ISO, OI-119)
    "Value Reporting Form", "Additional Locations Special Coinsurance",
    # chunk 24 (census closed 2026-10-01, C24-24): Builders Risk and CP 10 44, 20 CW files (OI-121 fixed in the chunk)
    "Builders Risk", "Theft of Building Materials (not BR)",
}


def rows(path):
    with open(path, encoding="utf-8-sig") as h:
        return sum(1 for r in csv.reader(h) if r) - 1


def family_of(name):
    for fam, pat in FAMILIES:
        if re.search(pat, name):
            return fam
    return None


def groups_of(text):
    return set(re.findall(r'DataDefGroup="([^"]+)"', text))


def main():
    b = book_for("OR", ASOF)
    cw = b.parent.package.content
    rules_dir, tables_dir = cw / "Rules", cw / "Rate Tables"
    all_rules = {f.name: f.read_text(encoding="utf-8-sig") for f in rules_dir.glob("*.xml")}
    prem = {n: s for n, s in all_rules.items() if '"SetPremium"' in s}
    registry = set(nodes.EVAL)

    # a remaining family claims its own earthquake riders first (46 files, e.g.
    # AgreedValEarthquake): an EQ rider is built only when its parent coverage is
    # (only EQ riders: DependentPropertiesLimitedInternationalCov is chunk 12's)
    built = sorted(n for n in prem if (BUILT.search(n)
                   and not (re.search(r"Earthquake|EQCov", n) and family_of(n)))
                   or family_of(n) in CLOSED)
    rest = sorted(n for n in prem if n not in built)
    fam_files = collections.defaultdict(list)
    unmapped = []
    for n in rest:
        f = family_of(n)
        (fam_files[f].append(n) if f else unmapped.append(n))

    books = {}
    for j in census11.JURIS:
        if j == "PR":
            continue
        try:
            books[j] = book_for(j, ASOF)
        except Exception:
            pass
    state_rules = {j: {p.name for p in (bk.state.package.content / "Rules").glob("*.xml")}
                   for j, bk in books.items() if (bk.state.package.content / "Rules").exists()}

    stc = {p.stem: p.read_text(encoding="utf-8-sig", errors="replace") for p in ISO_CF.rglob("STC/*.json")}

    # stored ISO responses: non-zero premium by record name
    replay = collections.Counter()          # record -> responses with a non-zero premium
    for rp in RES.glob("chunk13_fixture_*_response.json"):
        seen = set()

        def walk(o, tag):
            if isinstance(o, dict):
                p = o.get("Premium")
                try:
                    if p not in (None, "") and float(p) != 0:
                        seen.add(tag)
                except (TypeError, ValueError):
                    pass
                for k, v in o.items():
                    if isinstance(v, (dict, list)):
                        walk(v, k)
            elif isinstance(o, list):
                for x in o:
                    walk(x, tag)
        walk(json.loads(rp.read_text(encoding="utf-8"))["Body"], "Body")
        replay.update(seen)

    print(f"{b}\n{len(all_rules)} countrywide rule files, {len(prem)} with SetPremium: "
          f"{len(built)} built (chunks 0-14 and each closed chunk since), {len(rest)} remaining "
          f"({sum(len(v) for v in fam_files.values())} in {len(fam_files)} families, {len(unmapped)} unmapped)")
    print(f"{len(books)} states (PR excluded); {len(stc)} CF STC payloads; "
          f"{sum(1 for _ in RES.glob('chunk13_fixture_*_response.json'))} stored ISO responses\n")
    for n in unmapped:
        print(f"  UNMAPPED: {n}")

    out = []
    for fam, _ in FAMILIES:
        files = fam_files.get(fam, [])
        if not files:
            continue
        text = "".join(prem[n] for n in files)
        recs = set().union(*(groups_of(prem[n]) for n in files))
        mats = set(re.findall(r'MatrixFromConstant="([^"]+)"', text)) - {"Pages"}
        tabs = [(t, rows(tables_dir / f"{t}.RateTable.csv") if (tables_dir / f"{t}.RateTable.csv").exists() else None)
                for t in sorted(mats)]
        empty = sum(1 for _, r in tabs if not r)
        elems = collections.Counter(re.findall(r"<rul:(\w+)", text))
        gaps = sorted(e for e in elems if e not in registry and e not in STRUCTURAL)
        states = sorted(j for j, names in state_rules.items() if any(n in names for n in files))
        fixtures = sum(1 for t in stc.values() if any(f'"{r}"' in t for r in recs))
        rep = sum(replay[r] for r in recs)
        rep_recs = sorted(r.replace("CommercialProperty", "") for r in recs if replay[r])
        reads = bool(re.search(r'FromDataDef="[^"]*(\.\./|ancestor::)[^"]*Premium"', text))
        lookups = elems.get("Lookup", 0)
        stems = {n.replace(".Rule.xml", "") for n in files}
        ext = {x for x in re.findall(r'RunRule[^>]*FileName="([^"]+)"', text) if x not in stems}
        m = re.search(r'<rul:Rule Name="SetPremium".*?</rul:Rule>', prem[files[0]], re.S)
        shape = sorted(set(re.findall(r'FromDataDef="([^"]+)"', m.group(0))) if m else [])
        out.append((fam, len(files), len(tabs), empty, len(states), fixtures, rep, gaps, reads,
                    lookups, rep_recs, states, len(text) // 1024, len(ext), shape))

    print(f"{'family':50s} {'files':>5s} {'tabs':>4s} {'empty':>5s} {'st':>3s} {'fixt':>4s} "
          f"{'repl':>4s} {'lkps':>4s} {'kb':>4s} {'ext':>3s} reads gaps")
    for r in sorted(out, key=lambda r: (-min(r[6], 1), r[1] + r[2] + r[4] / 5)):
        print(f"{r[0][:50]:50s} {r[1]:5d} {r[2]:4d} {r[3]:5d} {r[4]:3d} {r[5]:4d} {r[6]:4d} {r[9]:4d} {r[12]:4d} {r[13]:3d} "
              f"{'Y' if r[8] else '-':5s} {','.join(r[7]) or '-'}")
    print("\nSetPremium operands (first file of each family):")
    for r in out:
        print(f"  {r[0]}: {' '.join(r[14])[:240]}")
    print("\nReplayed records (non-zero ISO premium in stored responses, all equal to ours):")
    for r in out:
        if r[10]:
            print(f"  {r[0]}: {', '.join(r[10])}")
    print("\nStates rewriting a family file:")
    for r in out:
        if r[11]:
            print(f"  {r[0]}: {' '.join(r[11])}")

    # state-only premium files, every batch (a per-state check scans all batches)
    cw_names = set(all_rules)
    only = collections.defaultdict(set)
    for pkg in sorted(ISO_CF.glob("*/CF ?? *")):
        st = pkg.name.split()[1]
        if st == "PR" or not (pkg / "Rules").exists():
            continue
        for p in (pkg / "Rules").glob("*.xml"):
            if p.name in cw_names:
                continue
            s = p.read_text(encoding="utf-8-sig", errors="replace")
            if '"SetPremium"' in s:
                only[p.name.replace("CommercialProperty", "").replace("Rules.Rule.xml", "")].add(st)
    print(f"\nState-only premium files (not a countrywide file name), all batches, PR excluded: {len(only)}")
    # chunk 23 (C23-21, 2026-10-01): every in-force state-only premium file has an owner chunk (904_, C23-17) and all are
    # built except WV's two flood files, which chunk 25 (flood) takes
    still_open = {n for n in only if "Flood" in n}
    for n, sts in sorted(only.items()):
        print(f"  {n:90s} {' '.join(sorted(sts)):12s} {'OPEN: chunk 25 (flood)' if n in still_open else 'closed'}")
    print(f"State-only list: closed except {len(still_open)} flood file(s) left to chunk 25")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
