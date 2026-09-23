"""Payload generator, Step 2 -- harvest the union field set ISO actually accepts.

Two corpora, both of them evidence rather than documentation:

  1. ``results/cf-raas/*request*.json`` -- 44 payloads **this project sent to live
     ISO and had accepted**, spanning Building, Contents, Business Income,
     Special Class and Special Class Business Income.
  2. ISO's own ``STC/`` folders under ``ISO_ERC_Files/CF`` -- ISO-authored
     regression payloads. Stronger evidence than ours: ISO wrote them.

The output is the specification for the ``Payload Export`` sheet: every record
type, every field ISO has been seen to accept on it, and how often.

**Frequency is not requiredness.** ISO marks every field in the CF DataDef
``nillable="yes"`` with no ``minOccurs``, so the schema says nothing about what
must be sent. A field in 44 of 44 payloads may still be optional; a field in 3
may still be mandatory on a path the corpus never exercises. Everything below
reports *observed frequency* and labels it as such.

Writes three artefacts next to the other payload docs and prints a summary.
Read-only: touches no workbook, sends no request.
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RAAS = REPO / "results" / "cf-raas"
ERC = Path("C:/Projects/ISO_ERC_Files/CF")
OUT = REPO / "CF_Algorithm"
INVENTORY = OUT / "CF_Payload_Excel_Input_Inventory.csv"

#: A record type is any key whose value is a dict/list of dicts and whose name
#: ISO prefixes this way. Everything else is a scalar field on its parent.
RECORD_PREFIX = "CommercialProperty"

#: The envelope, not the risk -- excluded so it doesn't pollute the field matrix.
ENVELOPE = {"header", "body", "quoteback", "authorization", "orgId", "shipId"}


def walk(node, record: str, out: dict[tuple[str, str], list]) -> None:
    """Collect (record type, scalar field) -> sample values, recursively."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key in ENVELOPE:
                walk(value, record, out)
            elif isinstance(value, dict):
                walk(value, key if key.startswith(RECORD_PREFIX) else record, out)
            elif isinstance(value, list):
                child = key if key.startswith(RECORD_PREFIX) else record
                for item in value:
                    walk(item, child, out)
            else:
                out[(record, key)].append(value)
    elif isinstance(node, list):
        for item in node:
            walk(item, record, out)


def harvest(paths, label: str):
    """Return per-(record, field) stats plus the number of payloads read."""
    seen_in: dict[tuple[str, str], int] = defaultdict(int)
    samples: dict[tuple[str, str], set] = defaultdict(set)
    total = 0
    for path in paths:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError, OSError):
            continue
        found: dict[tuple[str, str], list] = defaultdict(list)
        walk(data, "Policy", found)
        if not found:
            continue
        total += 1
        for key, values in found.items():
            seen_in[key] += 1
            for value in values[:3]:
                if value is not None and str(value) != "":
                    samples[key].add(str(value)[:40])
    print(f"  {label}: {total} payloads, {len(seen_in)} distinct (record, field) pairs")
    return seen_in, samples, total


#: The record types the rater actually emits. The STC corpus exercises 57,
#: but ~48 of those are endorsement records with no counterpart in the
#: workbook -- scoping the gap analysis to these keeps "fields with no rater
#: source" meaning *fields we must default*, not *the whole CF line*.
CORE = {
    "Policy",
    "CommercialProperty",
    "CommercialPropertyLocation",
    "CommercialPropertyStructure",
    "CommercialPropertyOccupClass",
    "CommercialPropertyPersonalProperty",
    "CommercialPropertyBusinessIncome",
    "CommercialPropertySpecialClass",
    "CommercialPropertySpecialClassBusnIncome",
}

#: Rater prose -> ISO field name, where the two genuinely differ. Built by hand
#: against Step 1's inventory; anything not here falls through to the loose
#: match and, failing that, is reported as needing a verdict.
ALIASES = {
    "buildingclasscode": "ClassCode",
    "tenantsclasscode": "ClassCode",
    "classdescription": "ClassificationDescription",
    "constructiontype": "ConstructionType",
    "constructioncode": "ConstructionCode",
    "protectionclass": "ProtectClass",
    "buildingcodeeffectivenessgradebceg": "BCEG",
    "bgiterritory": "BasicGroupIRatingTerr",
    "bgiiterritory": "BasicGroupIIRatingTerr",
    "specialterritory": "SpecialRatingTerr",
    "buildinglimit": "Limit",
    "contentslimit": "Limit",
    "businessincomelimit": "Limit",
    "specialclassbuildinglimit": "Limit",
    "buildingcoinsurance": "Coinsurance",
    "contentscoinsurance": "Coinsurance",
    "businessincomecoinsurance": "Coinsurance",
    "valuation": "ValuationType",
    "vacancy": "VacantBuilding",
    "numberofstories": "NumStories",
    "buildingcoveragetype": "CovType",
    "contentscoveragetype": "CovType",
    "businessincomecoveragetype": "CovType",
    "personalpropertycoveragetype": "CovType",
    "personalpropertycoverageform": "CovForm",
    "causeofloss": "CauseOfLoss",
    "policydeductible": "Deductible",
    "windstormorhaildeductible": "WindstormOrHailDeductible",
    "theftdeductible": "TheftDeductible",
    "businessincometypeofrisk": "TypeOfRisk",
    "typeofrisk": "TypeOfRisk",
    "maxperiodofindemnity": "MaxPeriod",
    "monthlylimitofindemnity": "MonthlyLimitOfIndemnity",
    "includedinblanket": "IncludedInBlkt",
    "occupancycategory": "OccupCategory",
    "occupancyseverity": "OccupCategoryRiskSeverity",
    "policytype": "PolicyType",
    "opensides": "OpenSides",
    "zipcode": "ZipCode",
    "city": "City",
}


def normalise(label: str) -> str:
    """Rater label -> a loose key for matching against ISO field names."""
    return "".join(c for c in label.lower() if c.isalnum())


def main() -> int:
    print("Step 2 -- harvesting the field set ISO accepts\n")

    print("Corpus 1 -- payloads live ISO accepted from us:")
    raas_files = sorted(RAAS.glob("*request*.json"))
    raas_seen, raas_samples, raas_total = harvest(raas_files, "results/cf-raas")

    print("\nCorpus 2 -- ISO's own STC regression payloads:")
    stc_files = sorted(ERC.glob("*/*/STC/*.json"))
    stc_seen, stc_samples, stc_total = harvest(stc_files, "ISO_ERC_Files/CF")

    records = sorted({r for r, _ in list(raas_seen) + list(stc_seen)})
    print(f"\nRecord types seen: {len(records)}")
    for rec in records:
        n_ours = sum(1 for r, _ in raas_seen if r == rec)
        n_iso = sum(1 for r, _ in stc_seen if r == rec)
        print(f"  {rec:<46} ours {n_ours:>3} fields | ISO {n_iso:>3} fields")

    # ---- artefact 1: the field matrix -------------------------------------
    matrix = OUT / "CF_Payload_Field_Matrix.csv"
    all_keys = sorted(set(raas_seen) | set(stc_seen))
    with matrix.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["RecordType", "Field", "InOurPayloads", "OurPct",
                    "InISOPayloads", "ISOPct", "Evidence", "SampleValues"])
        for rec, field in all_keys:
            ours, iso = raas_seen.get((rec, field), 0), stc_seen.get((rec, field), 0)
            if ours and iso:
                evidence = "both"
            elif iso:
                evidence = "ISO only"
            else:
                evidence = "ours only"
            vals = sorted(raas_samples.get((rec, field), set())
                          | stc_samples.get((rec, field), set()))[:4]
            w.writerow([rec, field, ours,
                        f"{100 * ours / raas_total:.0f}%" if raas_total else "",
                        iso,
                        f"{100 * iso / stc_total:.0f}%" if stc_total else "",
                        evidence, " | ".join(vals)])
    print(f"\nwrote {matrix.name}  ({len(all_keys)} rows)")

    # ---- artefact 2: gap lists --------------------------------------------
    iso_fields = {f for r, f in all_keys if r in CORE}
    iso_norm = {normalise(f): f for f in iso_fields}
    for alias, target in ALIASES.items():
        if target in iso_fields:
            iso_norm.setdefault(alias, target)

    rater_rows = []
    if INVENTORY.exists():
        with INVENTORY.open(encoding="utf-8") as fh:
            rater_rows = [r for r in csv.DictReader(fh) if r["Kind"] == "FIELD"]

    gaps = OUT / "CF_Payload_Field_Gaps.csv"
    matched = unmatched = 0
    with gaps.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["Direction", "Sheet", "LabelCell", "RaterLabel",
                    "ISOField", "SampleValue"])
        for row in rater_rows:
            label = row["Label"].rstrip(":").strip()
            hit = iso_norm.get(normalise(label))
            if hit:
                matched += 1
                w.writerow(["rater -> ISO", row["Sheet"], row["LabelCell"],
                            label, hit, row["SampleValue"]])
            else:
                unmatched += 1
                w.writerow(["rater field, NO ISO match", row["Sheet"],
                            row["LabelCell"], label, "", row["SampleValue"]])
        rater_norm = {normalise(r["Label"].rstrip(":").strip()) for r in rater_rows}
        rater_norm |= {ALIASES[k] and normalise(ALIASES[k])
                       for k in ALIASES if k in rater_norm}
        no_source = sorted(f for f in iso_fields if normalise(f) not in rater_norm)
        for field in no_source:
            w.writerow(["ISO field, NO rater source", "", "", "", field, ""])
    print(f"wrote {gaps.name}")

    print("\n--- the join ---")
    print(f"  rater inputs with a direct ISO field name match : {matched:>4}")
    print(f"  rater inputs with NO match (need a verdict)     : {unmatched:>4}")
    print(f"  ISO fields with no rater source (Defaults rows) : {len(no_source):>4}")

    # ---- artefact 3: the composition check --------------------------------
    print("\n--- composition risk ---")
    coverage = sorted(CORE - {"Policy", "CommercialProperty"})
    combos = defaultdict(int)
    for path in raas_files:
        try:
            raw = path.read_text(encoding="utf-8")
        except OSError:
            continue
        combos[tuple(r for r in coverage if f'"{r}"' in raw)] += 1
    widest = max(combos, key=len) if combos else ()
    print(f"  coverage blocks the rater emits        : {len(coverage)}")
    print(f"  widest single payload ISO has accepted : {len(widest)}")
    for rec in widest:
        print(f"      - {rec}")
    missing = [r for r in coverage if r not in widest]
    print("  never co-occurring with the above      :")
    for rec in missing:
        print(f"      - {rec}")
    print("  => each block is individually ISO-proven; the FULL combination is not.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
