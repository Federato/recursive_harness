"""CF ERC jurisdictions.json builder (Phase 3).

Independent of CF_Algorithm / CFBranch / cf-circular-expert. Reads only the
raw ERC corpus at C:\\Projects\\ISO_ERC_Files\\CF\\ and this project's own
Agentic/cf-erc-expert/knowledge/packages.json (built by cf_02_packages.py).

Two things happen here:

1. Deep: for the 20260601 edition, group packages.json entries by
   jurisdiction code -> n_packages, editions present.

2. Shallow survey: walk EVERY edition folder under the CF root (not just
   20260601) and pull the 2-letter jurisdiction token out of each package
   directory name. This gives the full set of jurisdictions that appear
   ANYWHERE in the CF corpus, cheaply (name parsing only, no file reads),
   so we can diff it against the 52-member reference list (50 states + DC
   + PR) the way GL's jurisdictions.json flagged Hawaii as absent. Any
   reference-list jurisdiction not found in ANY CF edition folder is
   reported as missing_from_corpus.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(r"C:\Projects\ISO_ERC_Files\CF")
PACKAGES_PATH = Path(r"C:\Projects\Recursive_Harness_2.0\Agentic\cf-erc-expert\knowledge\packages.json")
OUT = Path(r"C:\Projects\Recursive_Harness_2.0\Agentic\cf-erc-expert\knowledge\jurisdictions.json")

NAME_RE_STATE = re.compile(r"^CF\s+([A-Z]{2})\s+\d{8}\s+V\d+$", re.I)
NAME_RE_CW = re.compile(r"^CFCW\d{8}V\d+$", re.I)

# 50 states + DC + PR, same 52-member reference set GL's jurisdictions.json used.
REFERENCE_52 = sorted([
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA",
    "KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
    "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT",
    "VA","WA","WV","WI","WY","DC","PR",
])


def main() -> None:
    packages = json.loads(PACKAGES_PATH.read_text(encoding="utf-8"))["packages"]

    by_juris = {}
    for pkg_id, entry in packages.items():
        j = entry.get("jurisdiction")
        if j is None or j == "CW":
            continue
        by_juris.setdefault(j, []).append(entry)

    jurisdictions_20260601 = {}
    for j, entries in sorted(by_juris.items()):
        editions = sorted({e["edition"] for e in entries})
        jurisdictions_20260601[j] = {
            "n_packages": len(entries),
            "editions_present_in_20260601_folder": editions,
            "package_ids": sorted(e["source_dir"] for e in entries),
        }

    # Shallow survey across ALL edition folders (name parsing only)
    all_juris_by_edition = {}
    all_juris_seen = set()
    for ed_dir in sorted(p for p in ROOT.iterdir() if p.is_dir()):
        found = set()
        for pk in ed_dir.iterdir():
            if not pk.is_dir():
                continue
            if NAME_RE_CW.match(pk.name.strip()):
                continue
            m = NAME_RE_STATE.match(pk.name.strip())
            if m:
                found.add(m.group(1).upper())
        all_juris_by_edition[ed_dir.name] = sorted(found)
        all_juris_seen |= found

    missing_from_corpus = sorted(set(REFERENCE_52) - all_juris_seen)

    result = {
        "_note": (
            "Built by scripts/erc/cf_03_jurisdictions.py. The per-jurisdiction "
            "detail (n_packages, editions_present_in_20260601_folder) is "
            "derived from Agentic/cf-erc-expert/knowledge/packages.json, "
            "which was itself built by an exact walk of the 20260601 edition "
            "folder only (cf_02_packages.py). The all-editions jurisdiction "
            "survey below is a SHALLOW pass: it parses package directory "
            "names across every edition folder in C:\\Projects\\ISO_ERC_Files\\CF\\ "
            "(no file contents read) to build the full set of jurisdictions "
            "that appear anywhere in the CF corpus, then diffs that set "
            "against the 52-member reference list (50 states + DC + PR) used "
            "by the GL survey to find its Hawaii gap."
        ),
        "n_jurisdictions_20260601": len(jurisdictions_20260601),
        "jurisdictions_20260601": jurisdictions_20260601,
        "reference_list_52": REFERENCE_52,
        "jurisdictions_present_any_edition": sorted(all_juris_seen),
        "n_jurisdictions_present_any_edition": len(all_juris_seen),
        "jurisdictions_by_edition_folder": all_juris_by_edition,
        "missing_from_corpus": missing_from_corpus,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=1), encoding="utf-8")
    print("missing_from_corpus:", missing_from_corpus)
    print("n present any edition:", len(all_juris_seen))


if __name__ == "__main__":
    main()
