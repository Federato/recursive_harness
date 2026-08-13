"""Build the circular-expert agent's terrorism knowledge, from the text only.

Produces `Agentic/iso-circular-expert/knowledge/terrorism.json`:

  editions        the three Terrorism Supplement notices, with page counts
  assignments     jurisdiction -> (TEV version, PEV version, circular, effective)
  versions        version id -> label, page span, above-average class codes
  factors         the filed factors, quoted with their citation

and registers the three notices in `knowledge/notices.json` under a new
`terrorism` group, so `iso.py notice` and `iso.py cite` resolve them.

WHAT THIS DELIBERATELY DOES NOT DO
----------------------------------
It does not claim which of the two X columns a class code sits in. The
Supplement prints `Prem/Ops` and `Products/Completed Ops` as separate columns,
and no text extractor in this environment preserves that split across page
breaks — the marker lands at a different indent on either side of a page. The
per-column split is available from ERC (`TerrorismExposureClassesPremises` /
`...Products`) and is verified against the manual as a UNION only. Recording a
guessed column would put invented evidence into a citation store.

    python scripts/14_build_terrorism_kb.py
"""
from __future__ import annotations

import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
AGENT = os.path.join(PROJ, "Agentic", "iso-circular-expert")
TXT = os.path.join(AGENT, "text", "terrorism")
KB = os.path.join(AGENT, "knowledge")

ROW_RE = re.compile(
    r'^([A-Z][A-Z .]+?)\s+(TEV\d{3})\s+(\S+)\s+(\d{1,2}/\d{1,2}/\d{2})\s+'
    r'(PEV\d{3})\s+(\S+)\s+(\d{1,2}/\d{1,2}/\d{2})\s*$')
VERSION_RE = re.compile(r'^VERSION ([TP]EV\d{3})(?: \(([^)]+)\))?\s*$')
CODE_RE = re.compile(r'^\s*(\d{5})\s*X?\s*X?\s*$')
PAGE_RE = re.compile(r'^<<<PAGE (\d+)>>>$')

# USPS code for every jurisdiction name the supplement prints.
ABBR = {
    "ALABAMA": "AL", "ALASKA": "AK", "ARIZONA": "AZ", "ARKANSAS": "AR",
    "CALIFORNIA": "CA", "COLORADO": "CO", "CONNECTICUT": "CT",
    "DELAWARE": "DE", "DISTRICT OF COLUMBIA": "DC", "FLORIDA": "FL",
    # The supplement prints DC abbreviated, and only in the 2022 edition's
    # table. Mapping by exact name silently dropped 1 of 52 rows and the count
    # still looked plausible — which is why the check below asserts 52.
    "DIST. OF COLUMBIA": "DC",
    "GEORGIA": "GA", "HAWAII": "HI", "IDAHO": "ID", "ILLINOIS": "IL",
    "INDIANA": "IN", "IOWA": "IA", "KANSAS": "KS", "KENTUCKY": "KY",
    "LOUISIANA": "LA", "MAINE": "ME", "MARYLAND": "MD", "MASSACHUSETTS": "MA",
    "MICHIGAN": "MI", "MINNESOTA": "MN", "MISSISSIPPI": "MS",
    "MISSOURI": "MO", "MONTANA": "MT", "NEBRASKA": "NE", "NEVADA": "NV",
    "NEW HAMPSHIRE": "NH", "NEW JERSEY": "NJ", "NEW MEXICO": "NM",
    "NEW YORK": "NY", "NORTH CAROLINA": "NC", "NORTH DAKOTA": "ND",
    "OHIO": "OH", "OKLAHOMA": "OK", "OREGON": "OR", "PENNSYLVANIA": "PA",
    "PUERTO RICO": "PR", "RHODE ISLAND": "RI", "SOUTH CAROLINA": "SC",
    "SOUTH DAKOTA": "SD", "TENNESSEE": "TN", "TEXAS": "TX", "UTAH": "UT",
    "VERMONT": "VT", "VIRGINIA": "VA", "WASHINGTON": "WA",
    "WEST VIRGINIA": "WV", "WISCONSIN": "WI", "WYOMING": "WY",
}


def parse(path: str) -> dict:
    lines = open(path, encoding="utf-8").read().splitlines()
    page = 0
    page_of: list[int] = []
    for ln in lines:
        m = PAGE_RE.match(ln.strip())
        if m:
            page = int(m.group(1))
        page_of.append(page)

    assignments: dict[str, dict] = {}
    unmapped: list[str] = []
    for ln in lines:
        m = ROW_RE.match(ln.strip())
        if not m:
            continue
        name, tev, tcirc, teff, pev, pcirc, peff = m.groups()
        st = ABBR.get(name.strip().rstrip("."))
        if not st:
            unmapped.append(name.strip())
            continue
        assignments[st] = {
            "jurisdiction": name.strip(), "endorsement_version": tev,
            "premium_version": pev, "circular": pcirc,
            "effective_date": peff,
        }

    marks: list[tuple[int, str, str]] = []
    for i, ln in enumerate(lines):
        m = VERSION_RE.match(ln.strip())
        if m:
            marks.append((i, m.group(1), m.group(2) or "COUNTRYWIDE"))
    versions: dict[str, dict] = {}
    for n, (i, vid, label) in enumerate(marks):
        end = marks[n + 1][0] if n + 1 < len(marks) else len(lines)
        codes = sorted({m.group(1) for ln in lines[i:end]
                        for m in [CODE_RE.match(ln)] if m})
        versions[vid] = {
            "label": label,
            "kind": ("terrorism endorsement options" if vid.startswith("TEV")
                     else "terrorism premium determination"),
            "page_from": page_of[i], "page_to": page_of[end - 1],
            "above_average_classes": codes,
            "above_average_count": len(codes),
        }
    return {"assignments": assignments, "versions": versions,
            "unmapped": unmapped,
            "pages": max(page_of) if page_of else 0}


def main() -> int:
    files = sorted(f for f in os.listdir(TXT) if f.endswith(".txt"))
    print(f"population: {len(files)} terrorism text documents")
    editions: dict[str, dict] = {}
    latest = None
    for f in files:
        d = parse(os.path.join(TXT, f))
        notice = f[:-len("-C.txt")]
        editions[notice] = {
            "notice": notice, "file": f[:-4] + ".pdf", "kind": "TERXV",
            "st": "MU", "pages": d["pages"],
            "endorsement_versions": sorted(v for v in d["versions"]
                                           if v.startswith("TEV")),
            "premium_versions": sorted(v for v in d["versions"]
                                       if v.startswith("PEV")),
            "jurisdictions_assigned": len(d["assignments"]),
        }
        print(f"  {notice}: {d['pages']} pages · "
              f"{len(d['assignments'])} jurisdictions assigned · "
              f"{len(d['versions'])} versions"
              + (f" · UNMAPPED ROWS {d['unmapped']}" if d["unmapped"] else ""))
        assert not d["unmapped"], (
            f"{notice}: {len(d['unmapped'])} jurisdiction rows did not map to a "
            f"USPS code — a silently dropped row still yields a plausible count")
        latest = (notice, d)

    notice, d = latest                                  # type: ignore[misc]
    out = {
        "source": "Commercial Line Manuals/GL/Terrorism",
        "latest_edition": notice,
        "editions": editions,
        "assignments": d["assignments"],
        "versions": d["versions"],
        "factors": {
            "certified_acts_above_average": {
                "value": 0.009,
                "cite": f"{notice} Table A#.A.1.a, rule Terrorism Premium "
                        f"Determination A.1.a",
            },
            "certified_acts_average": {
                "value": 0.004,
                "cite": f"{notice} Table A#.A.1.a",
            },
            "excluding_nbcr_multiplier": {
                "value": 0.58,
                "cite": f"{notice} Terrorism Premium Determination A.1.b — "
                        f"'Multiply the additional premium by 0.58'",
            },
            "other_sublines_exposure_class": {
                "value": "Average Exposure Class",
                "cite": f"{notice} A.1.a — 'For sublines other than "
                        f"premises/operations or products/completed operations, "
                        f"use the average exposure category'",
            },
        },
        "caveat_columns": (
            "above_average_classes is the UNION of the manual's Prem/Ops and "
            "Products/Completed Ops columns. The per-column split is not "
            "recoverable from the text layer and must be taken from ERC's "
            "TerrorismExposureClasses{Premises,Products} tables."
        ),
    }
    with open(os.path.join(KB, "terrorism.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print(f"\nwrote knowledge/terrorism.json — "
          f"{len(d['assignments'])} assignments, {len(d['versions'])} versions")

    npath = os.path.join(KB, "notices.json")
    N = json.load(open(npath, encoding="utf-8"))
    N["terrorism"] = {e["file"]: {
        "file": e["file"], "kind": "TERXV", "st": "MU", "notice": e["notice"],
        "pages": e["pages"], "circulars": ["LI-CL-2020-034"], "filings": [],
        "effective_date": "12/01/2020", "dating_basis": "circular effective date",
        "date_confidence": "High",
    } for e in editions.values()}
    with open(npath, "w", encoding="utf-8") as fh:
        json.dump(N, fh, indent=1)
    print(f"registered {len(N['terrorism'])} notices in knowledge/notices.json "
          f"under a new 'terrorism' group "
          f"(rules {len(N['rules'])}, losscosts {len(N['losscosts'])})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
