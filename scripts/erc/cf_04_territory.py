"""CF ERC territory.json builder (Phase 4).

Independent of CF_Algorithm / CFBranch / cf-circular-expert. Reads only the
raw ERC corpus at C:\\Projects\\ISO_ERC_Files\\CF\\20260601\\.

For each sampled package, finds its "BasicGroupIRatingTerritory<ST>" domain
table (the primary Group I premises rating-territory table; excludes
*Def.xml schema files and the countrywide template, which ships with a
header row only) and classifies the scheme by inspecting the CSV header and
rows:

  COUNTY_PLACE   - header includes a City and/or County column, values are
                   place names (e.g. "Phoenix", "Balance of State")
  SINGLE_TERRITORY - header is StateCode/DisplayValue/DataValue with exactly
                   one data row reading "Entire State"
  ZIP_TABLE      - header includes a Zip/ZipCode column keyed to a distinct
                   territory value per zip
  UNKNOWN        - none of the above patterns matched; flagged, not guessed

Also separately records whether each sampled package ships a DomainZipCode
table, and whether that table maps zip -> territory (extra columns beyond
StateCode/DisplayValue/DataValue) or is just a flat list of valid zip codes
(observed in NY/TX/NC/OH samples: 3 columns, DataValue == the zip itself,
i.e. NOT a territory map).

Samples: the countrywide package plus 7 state packages chosen to prioritize
large states, drawn from what is actually PRESENT in the 20260601 edition
folder (FL, IL, NJ do not have a package in the 20260601 folder -- see
cf_03_jurisdictions.py's jurisdictions_by_edition_folder for where they last
appeared -- so they are explicitly listed as not-sampled rather than
guessed).
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(r"C:\Projects\ISO_ERC_Files\CF\20260601")
OUT = Path(r"C:\Projects\Recursive_Harness_2.0\Agentic\cf-erc-expert\knowledge\territory.json")

SAMPLE = [
    ("CFCW20260601V01", "CW"),
    ("CF CA 20261101 V01", "CA"),
    ("CF NY 20260801 V01", "NY"),
    ("CF TX 20260901 V03", "TX"),
    ("CF NC 20261201 V01", "NC"),
    ("CF MI 20260601 V02", "MI"),
    ("CF PA 20260901 V01", "PA"),
    ("CF AZ 20260601 V01", "AZ"),
    ("CF MT 20260601 V01", "MT"),
    ("CF KS 20260601 V01", "KS"),
]

NOT_SAMPLED_LARGE = {
    "FL": "no package directory present in the 20260601 edition folder (checked via cf_03_jurisdictions.py survey; FL exists in an earlier edition folder only)",
    "IL": "no package directory present in the 20260601 edition folder",
    "NJ": "no package directory present in the 20260601 edition folder",
}


def read_csv_rows(path: Path):
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return list(csv.reader(fh))


def classify(pkg_dir: Path, state_code: str):
    dt_dir = pkg_dir / "Domain Tables"
    if not dt_dir.is_dir():
        return {"scheme": "UNKNOWN", "note": "no Domain Tables directory"}

    # Find the primary Group I rating-territory table for this state.
    candidates = sorted(
        f for f in dt_dir.glob("DomainBasicGroupIRatingTerritory*.DomainTable.csv")
    )
    # Prefer the state-suffixed one over the generic countrywide template.
    state_specific = [f for f in candidates if f.stem.upper().endswith(state_code.upper())]
    target = state_specific[0] if state_specific else (candidates[0] if candidates else None)

    result = {"territory_table_file": target.name if target else None}

    if target is None:
        result["scheme"] = "UNKNOWN"
        result["note"] = "no DomainBasicGroupIRatingTerritory*.DomainTable.csv found"
        return result

    rows = read_csv_rows(target)
    if not rows:
        result["scheme"] = "UNKNOWN"
        result["note"] = "territory table file is empty"
        return result

    header = [h.strip() for h in rows[0]]
    data_rows = rows[1:]
    result["header"] = header
    result["n_data_rows"] = len(data_rows)

    header_lower = [h.lower() for h in header]
    has_city = "city" in header_lower
    has_county = "county" in header_lower
    has_zip = any("zip" in h for h in header_lower)

    if len(data_rows) == 0:
        result["scheme"] = "N/A"
        result["note"] = "header-only template table, no data rows (countrywide package ships the schema shape only; states supply the actual rows)"
    elif has_zip and not (has_city or has_county):
        result["scheme"] = "ZIP_TABLE"
    elif has_city or has_county:
        result["scheme"] = "COUNTY_PLACE"
        places = set()
        for r in data_rows:
            if len(r) > 1:
                places.add(r[1])
        result["n_distinct_place_values"] = len(places)
    elif len(data_rows) == 1 and "entire state" in [c.strip().lower() for c in data_rows[0]]:
        result["scheme"] = "SINGLE_TERRITORY"
    else:
        result["scheme"] = "SINGLE_TERRITORY" if len(data_rows) <= 2 else "UNKNOWN"
        if result["scheme"] == "UNKNOWN":
            result["note"] = f"header did not match known patterns and n_data_rows={len(data_rows)} > 2; needs manual review"

    # DomainZipCode presence / whether it's a territory map
    zip_files = list(dt_dir.glob("DomainZipCode.DomainTable.csv"))
    if zip_files:
        zrows = read_csv_rows(zip_files[0])
        zheader = [h.strip() for h in zrows[0]] if zrows else []
        is_territory_map = len(zheader) > 3
        result["has_domain_zip_code_table"] = True
        result["domain_zip_code_header"] = zheader
        result["domain_zip_code_is_territory_map"] = is_territory_map
        result["domain_zip_code_n_rows"] = len(zrows) - 1 if zrows else 0
    else:
        result["has_domain_zip_code_table"] = False

    return result


def main() -> None:
    samples = {}
    for dirname, code in SAMPLE:
        pkg_dir = ROOT / dirname
        if not pkg_dir.is_dir():
            samples[code] = {"error": f"package dir not found: {dirname}"}
            continue
        samples[code] = classify(pkg_dir, code)

    result = {
        "_note": (
            "Built by scripts/erc/cf_04_territory.py, reading only "
            "C:\\Projects\\ISO_ERC_Files\\CF\\20260601\\. Classifies each "
            "sampled package's primary Group I premises rating-territory "
            "domain table (DomainBasicGroupIRatingTerritory<ST>) into one of "
            "three schemes -- ZIP_TABLE, SINGLE_TERRITORY, COUNTY_PLACE -- by "
            "reading its CSV header and row count. No CF package sampled so "
            "far uses a ZIP-keyed rating-territory table for Group I premises "
            "(a DomainZipCode table exists in several packages, e.g. NY/TX/NC, "
            "but its header is StateCode/DisplayValue/DataValue with "
            "DataValue == the zip code itself -- a flat valid-zip list, not a "
            "zip -> territory map -- so it is NOT treated as evidence of a "
            "ZIP_TABLE scheme here). Sample: countrywide + 7 states, chosen "
            "to prioritize large states actually present in the 20260601 "
            "edition folder."
        ),
        "sampled_packages": [d for d, _ in SAMPLE],
        "not_sampled_large_states": NOT_SAMPLED_LARGE,
        "not_sampled_note": (
            "All other jurisdictions present in the 20260601 folder (see "
            "jurisdictions.json) were not sampled here and their scheme is "
            "left undetermined rather than guessed."
        ),
        "samples": samples,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=1), encoding="utf-8")
    for code, r in samples.items():
        print(code, r.get("scheme"), r.get("territory_table_file"))


if __name__ == "__main__":
    main()
