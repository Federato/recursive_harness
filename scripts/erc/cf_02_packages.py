"""CF ERC packages.json builder (Phase 2), 20260601 edition only.

Independent of CF_Algorithm / CFBranch / cf-circular-expert. Reads only the
raw ERC corpus at C:\\Projects\\ISO_ERC_Files\\CF\\20260601\\.

For each package directory inside the 20260601 edition folder, records:
  jurisdiction (2-letter code, or CW for countrywide)
  edition_date (from the folder name, YYYYMMDD -> YYYY-MM-DD)
  edition (YYYYMMDD)
  version (V0n token in the folder name)
  is_countrywide (bool)
  xsd_target_ns   -- read from DataDefs/*.DataDef.xsd targetNamespace attr
  xsd_import_ns   -- the namespace that xsd imports (its parent), if any
  parent_package_id -- derived from xsd_import_ns's package-id segment,
                        e.g. ".../CF_CW_20260601_V01/MasterCFCW" -> CF_CW_20260601_V01
  n_files, n_rule_files, n_rate_tables, n_domain_tables (measured, this package only)

Any field that could not be determined from a DataDef/Metadata file is set
to null with an explanatory sibling key.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(r"C:\Projects\ISO_ERC_Files\CF\20260601")
OUT = Path(r"C:\Projects\Recursive_Harness_2.0\Agentic\cf-erc-expert\knowledge\packages.json")

NAME_RE_STATE = re.compile(r"^CF\s+([A-Z]{2})\s+(\d{8})\s+(V\d+)$", re.I)
NAME_RE_CW = re.compile(r"^CFCW(\d{8})(V\d+)$", re.I)

TARGET_NS_RE = re.compile(r'targetNamespace="([^"]+)"')
IMPORT_NS_RE = re.compile(r'<xs:import[^>]*namespace="([^"]+)"')


def parse_name(dirname: str):
    m = NAME_RE_STATE.match(dirname.strip())
    if m:
        juris, edition, version = m.group(1).upper(), m.group(2), m.group(3).upper()
        return juris, edition, version, False
    m = NAME_RE_CW.match(dirname.strip())
    if m:
        edition, version = m.group(1), m.group(2).upper()
        return "CW", edition, version, True
    return None, None, None, None


def ns_to_pkgid(ns: str) -> str | None:
    # e.g. http://www.verisk.com/iso/erc/CF_CW_20260601_V01/MasterCFCW
    m = re.search(r"/erc/([A-Za-z0-9_]+)/", ns)
    return m.group(1) if m else None


def main() -> None:
    packages = {}
    for pk in sorted(p for p in ROOT.iterdir() if p.is_dir()):
        juris, edition, version, is_cw = parse_name(pk.name)
        entry = {
            "source_dir": pk.name,
            "jurisdiction": juris,
            "edition": edition,
            "edition_date": f"{edition[0:4]}-{edition[4:6]}-{edition[6:8]}" if edition else None,
            "version": version,
            "is_countrywide": is_cw,
        }
        if juris is None:
            entry["_name_parse_note"] = "package directory name did not match expected pattern; fields left null"

        # DataDefs xsd
        datadefs_dir = pk / "DataDefs"
        xsd_files = list(datadefs_dir.glob("*.DataDef.xsd")) if datadefs_dir.is_dir() else []
        if xsd_files:
            xsd_text = xsd_files[0].read_text(encoding="utf-8-sig", errors="replace")
            tns_match = TARGET_NS_RE.search(xsd_text)
            imp_match = IMPORT_NS_RE.search(xsd_text)
            entry["xsd_target_ns"] = tns_match.group(1) if tns_match else None
            entry["xsd_import_ns"] = imp_match.group(1) if imp_match else None
            entry["parent_package_id"] = ns_to_pkgid(imp_match.group(1)) if imp_match else (
                None if not is_cw else None
            )
            if not is_cw and not imp_match:
                entry["_parent_note"] = "no <xs:import> found in DataDef xsd; parent could not be determined"
            if is_cw:
                entry["_parent_note"] = "countrywide package; no parent expected"
        else:
            entry["xsd_target_ns"] = None
            entry["xsd_import_ns"] = None
            entry["parent_package_id"] = None
            entry["_datadef_note"] = "no *.DataDef.xsd file found under DataDefs/"

        # file counts, this package only
        n_files = n_rules = n_rt = n_dt = 0
        for f in pk.rglob("*"):
            if not f.is_file():
                continue
            n_files += 1
            if f.name.endswith(".Rule.xml"):
                n_rules += 1
            elif f.name.endswith(".RateTable.csv"):
                n_rt += 1
            elif f.name.endswith(".DomainTable.csv"):
                n_dt += 1
        entry["n_files"] = n_files
        entry["n_rule_files"] = n_rules
        entry["n_rate_tables"] = n_rt
        entry["n_domain_tables"] = n_dt

        # key: normalize CW pkg name to CFCW20260601V01 style, states to "CF XX 20260601 V01"
        key = pk.name
        packages[key] = entry

    result = {
        "_note": (
            "Built by scripts/erc/cf_02_packages.py, reading only "
            "C:\\Projects\\ISO_ERC_Files\\CF\\20260601\\. Covers the 20260601 "
            "edition folder only (66 package directories: 1 countrywide + 65 "
            "state/DC/PR). Keyed by the literal package directory name as it "
            "appears on disk. xsd_target_ns and parent_package_id are read "
            "directly from each package's DataDefs/*.DataDef.xsd "
            "targetNamespace and <xs:import> namespace attributes; where no "
            "xsd or no import was found this is flagged in a _*_note sibling "
            "key rather than guessed."
        ),
        "n_packages": len(packages),
        "packages": packages,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=1), encoding="utf-8")
    print(f"wrote {len(packages)} packages to {OUT}")


if __name__ == "__main__":
    main()
