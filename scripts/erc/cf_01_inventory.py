"""CF ERC corpus inventory (Phase 1).

Independent of the CF_Algorithm / CFBranch / cf-circular-expert manual-reading
side. Reads only the raw ERC corpus at C:\\Projects\\ISO_ERC_Files\\CF\\.

Produces Agentic/cf-erc-expert/knowledge/corpus.json.

Method:
  - Enumerate edition folders directly under CF root (top-level dirs).
  - For each edition folder, enumerate its immediate subdirectories as
    "package directories" (each one holds DataDefs/DOC/Domain Tables/
    Form Fields/Form Pages/Form Related Fields/Metadata/Rate Tables/
    Ratebook Columns/Ratebook Tables/Rules).
  - Countrywide package dirs are those whose name contains no space-
    separated 2-letter state token (i.e. start with "CFCW").
  - Precise file counts (rule files = *.Rule.xml, rate tables =
    *.RateTable.csv, rate table defs = *.RateTableDef.xml, domain tables =
    *.DomainTable.csv) are walked EXACTLY for the 20260601 edition folder
    (all packages in it, not just countrywide) since that is the edition
    this project is building out first.
  - For the other edition folders (20191201, 20201201, 20221001,
    20230801v1..v4) we only count package directories and total files
    (not broken out by kind) -- a reasonable countrywide-package-wide
    aggregate, not a full per-kind walk. This is noted explicitly below.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(r"C:\Projects\ISO_ERC_Files\CF")
OUT = Path(r"C:\Projects\Recursive_Harness_2.0\Agentic\cf-erc-expert\knowledge\corpus.json")

PRECISE_EDITION = "20260601"


def is_countrywide(dirname: str) -> bool:
    return dirname.replace(" ", "").upper().startswith("CFCW")


def main() -> None:
    edition_dirs = sorted(p for p in ROOT.iterdir() if p.is_dir())
    edition_names = [p.name for p in edition_dirs]

    total_package_dirs = 0
    per_edition_package_counts = {}
    total_files_all_editions = 0

    for ed in edition_dirs:
        pkg_dirs = [p for p in ed.iterdir() if p.is_dir()]
        per_edition_package_counts[ed.name] = len(pkg_dirs)
        total_package_dirs += len(pkg_dirs)
        for pk in pkg_dirs:
            total_files_all_editions += sum(1 for f in pk.rglob("*") if f.is_file())

    # Precise walk of the 20260601 edition folder, all packages
    precise_dir = ROOT / PRECISE_EDITION
    n_rule_files = 0
    n_rate_table_csv = 0
    n_rate_table_def = 0
    n_domain_table_csv = 0
    n_domain_table_def = 0
    n_files_20260601 = 0
    n_packages_20260601 = 0
    n_countrywide_20260601 = 0

    for pk in sorted(p for p in precise_dir.iterdir() if p.is_dir()):
        n_packages_20260601 += 1
        if is_countrywide(pk.name):
            n_countrywide_20260601 += 1
        for f in pk.rglob("*"):
            if not f.is_file():
                continue
            n_files_20260601 += 1
            name = f.name
            if name.endswith(".Rule.xml"):
                n_rule_files += 1
            elif name.endswith(".RateTable.csv"):
                n_rate_table_csv += 1
            elif name.endswith(".RateTableDef.xml"):
                n_rate_table_def += 1
            elif name.endswith(".DomainTable.csv"):
                n_domain_table_csv += 1
            elif name.endswith(".DomainTableDef.xml"):
                n_domain_table_def += 1

    # Countrywide package precise breakdown (CFCW20260601V01) for the docstring's ask
    cw_dir = None
    for pk in precise_dir.iterdir():
        if pk.name.replace(" ", "").upper() == "CFCW20260601V01":
            cw_dir = pk
            break

    cw_detail = {}
    if cw_dir is not None:
        cats = {}
        for cat_dir in sorted(p for p in cw_dir.iterdir() if p.is_dir()):
            n = sum(1 for f in cat_dir.rglob("*") if f.is_file())
            cats[cat_dir.name] = n
        cw_detail = {
            "package_dir": cw_dir.name,
            "categories": cats,
            "total_files": sum(cats.values()),
        }

    # jurisdiction tokens present in 20260601 (2-letter state code between "CF" and edition digits)
    jurisdictions_20260601 = set()
    for pk in precise_dir.iterdir():
        nm = pk.name
        if is_countrywide(nm):
            continue
        parts = nm.split()
        if len(parts) >= 2 and parts[0].upper() == "CF":
            jurisdictions_20260601.add(parts[1].upper())

    result = {
        "_note": (
            "Built by scripts/erc/cf_01_inventory.py, reading only "
            "C:\\Projects\\ISO_ERC_Files\\CF\\. Edition folder list and "
            "package-directory counts are an EXACT walk of every edition "
            "folder found under the CF root (top-level dirs are treated as "
            "editions/snapshots; each immediate subdirectory as a package). "
            "Per-file-kind counts (rule files, rate table csv/def, domain "
            "table csv/def) are an EXACT walk of every package inside the "
            "20260601 edition folder only -- that is the edition this build "
            "targets. Older edition folders (20191201, 20201201, 20221001, "
            "20230801v1..v4) are counted only for package-directory count and "
            "total file count, not broken out by file kind -- this is a "
            "measured aggregate (Path.rglob over each package dir), not an "
            "estimate, but it does not distinguish rule/rate/domain files "
            "for those older editions."
        ),
        "corpus_root": str(ROOT),
        "edition_folders": edition_names,
        "n_edition_folders": len(edition_names),
        "package_dirs_per_edition": per_edition_package_counts,
        "total_package_dirs_all_editions": total_package_dirs,
        "total_files_all_editions": total_files_all_editions,
        "precise_edition": PRECISE_EDITION,
        "precise_edition_detail": {
            "n_packages": n_packages_20260601,
            "n_countrywide_packages": n_countrywide_20260601,
            "n_state_packages": n_packages_20260601 - n_countrywide_20260601,
            "n_distinct_jurisdictions": len(jurisdictions_20260601),
            "jurisdictions": sorted(jurisdictions_20260601),
            "n_files": n_files_20260601,
            "n_rule_files": n_rule_files,
            "n_rate_table_csv": n_rate_table_csv,
            "n_rate_table_def_xml": n_rate_table_def,
            "n_domain_table_csv": n_domain_table_csv,
            "n_domain_table_def_xml": n_domain_table_def,
        },
        "countrywide_package_20260601_detail": cw_detail,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=1), encoding="utf-8")
    print(json.dumps(result, indent=1)[:3000])


if __name__ == "__main__":
    main()
