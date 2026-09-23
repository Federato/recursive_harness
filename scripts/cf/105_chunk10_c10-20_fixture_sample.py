"""C10-20 -- what ISO's own Earthquake fixtures actually exercise.

The task: "Pull a sample of the 69 ISO fixtures that elect Earthquake
(census 10) and characterize what they actually exercise -- which states,
forms, CovTypes -- before treating '69 exist' as proof of coverage breadth."

This does not sample. It reads all 364 Commercial Property STC payloads and
parses every one, because the opening census's own figures turned out to rest
on two measurement choices that do not survive contact:

  1. The DENOMINATOR is not 924. The census scanned
     `C:/Projects/ISO_ERC_Files` whole, which holds 560 General Liability
     payloads alongside 364 Commercial Property ones. `EQCovIndicator` is a
     CF field, so "364 of 924 carry the field at all" is not a coverage
     statistic -- it is the CF payload count restated. The real denominator
     for any Earthquake claim is 364.

  2. The census matched ONE `EQCovIndicator` per file, via
     `re.search` on the raw text. A CF payload carries the field on up to six
     DIFFERENT record types, and re.search returns only the first. The
     headline "69" survives (the Structure record happens to come first), but
     it is 69 STRUCTURES, not 69 payloads' worth of Earthquake, and it misses
     78 further electing records on four other record types.

Both are the "a check that finds nothing needs its denominator tested too"
shape this project keeps re-learning, applied to a check that DID find
something and was believed because of it.

Usage:
    python scripts/cf/105_chunk10_c10-20_fixture_sample.py
    python scripts/cf/105_chunk10_c10-20_fixture_sample.py --list-forms
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

ISO = Path("C:/Projects/ISO_ERC_Files")
CF = ISO / "CF"

# The 4 EQCauseOfLossForm variants, by the record key each attaches as.
# Names confirmed against the corpus in C10-01/C10-19, not guessed here.
FORMS = {
    "CommercialPropertyEarthquakeAndVolcanicEruptionEndorsement":
        "CP 10 40  plain, percentage deductible",
    "CommercialPropertyEarthquakeAndVolcanicEruptionCoverageWith"
    "FlatDollarDeductibleBldg":
        "CP 10 28  flat-dollar deductible",
    "CommercialPropertyEarthquakeAndVolcanicEruptionEndorsementSubLimitForm":
        "CP 10 29  sub-limit + flat-dollar deductible",
    "CommercialPropertyEarthquakeAndVolcanicEruptionEndorsementSubLimitForm"
    "WithFlatDollarDeductible":
        "CP 10 45  percentage-based sub-limit",
}

# Electing values. Note two DISTINCT domains live under one field name --
# see the per-record-type breakdown in section 3.
ELECT = {"Yes, Not Included in Blanket", "Yes, Included in Blanket", "Yes"}
DECLINE = {"No Coverage", "Not Applicable", "No", ""}

# The chunk 10 golden case's own coordinates, for the representativeness
# cross-tab in section 6.
GOLDEN = {"state": "OR", "cause_of_loss": "Basic Group I",
          "cov_type": "Building", "form": "CP 10 40  plain, percentage deductible"}


def walk(o, parent=None):
    """Yield (record_type, node) for every dict in the payload."""
    if isinstance(o, dict):
        yield parent, o
        for k, v in o.items():
            yield from walk(v, k)
    elif isinstance(o, list):
        for v in o:
            yield from walk(v, parent)


def state_of(path):
    m = re.search(r"CF[ _]([A-Z]{2})[ _]", str(path))
    return m.group(1) if m else "??"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list-forms", action="store_true",
                    help="list every Earthquake-named record key in the corpus")
    a = ap.parse_args()

    if not CF.exists():
        print(f"ISO fixture corpus not found at {CF}")
        return 1

    files = sorted(CF.rglob("STC/*.json"))
    gl = sorted((ISO / "General_Liability").rglob("STC/*.json"))

    print("C10-20 -- what ISO's Earthquake fixtures actually exercise")
    print("=" * 78)

    # ---------------------------------------------------------------- 1
    print("\n1 . THE DENOMINATOR -- the census's 924 is two lines of business")
    print("-" * 78)
    print(f"    Commercial Property STC payloads : {len(files)}")
    print(f"    General Liability STC payloads   : {len(gl)}")
    print(f"    the census's '924'               : {len(files) + len(gl)}")
    print()
    print("    `EQCovIndicator` is a Commercial Property field. The census's")
    print("    '364 of 924 carry the field at all' is therefore not a")
    print("    coverage statistic -- it is the CF payload count restated, and")
    print("    the 560 GL payloads could never have carried it. Every rate")
    print("    below is stated against 364.")

    # ---------------------------------------------------------------- 2
    print("\n2 . ELECTION, counted per RECORD rather than per first regex hit")
    print("-" * 78)
    by_type = collections.defaultdict(collections.Counter)
    payload_elects = 0
    for f in files:
        d = json.loads(f.read_text(encoding="utf-8-sig"))
        any_elect = False
        for rec, node in walk(d):
            if "EQCovIndicator" in node:
                by_type[rec][node["EQCovIndicator"]] += 1
                if node["EQCovIndicator"] in ELECT:
                    any_elect = True
        payload_elects += any_elect

    tot_elect = sum(c[v] for c in by_type.values() for v in c if v in ELECT)
    print(f"    payloads with at least one EQ election : {payload_elects} "
          f"of {len(files)}  ({payload_elects / len(files):.0%})")
    print(f"    ELECTING RECORDS, all record types     : {tot_elect}")
    print(f"    the census reported                    : 69")
    print()
    print("    69 is right about Structures and wrong about the corpus: it is")
    print(f"    69 Building structures, plus {tot_elect - 69} further electing")
    print("    records the one-match-per-file regex could not see.")

    # ---------------------------------------------------------------- 3
    print("\n3 . TWO DOMAINS SHARE THE FIELD NAME -- C10-05 adjudicated one")
    print("-" * 78)
    for rec, c in sorted(by_type.items(), key=lambda kv: -sum(kv[1].values())):
        vals = ", ".join(f"{v!r}x{n}" for v, n in c.most_common())
        print(f"    {rec:56s} {vals}")
    print()
    print("    The 4 premium-group record types use the 4-value domain C10-05")
    print("    checked against `DomainEQCovIndicatorBldg`. The auxiliary")
    print("    riders -- Utility Services, Radio/TV Antennas, Outside Signs,")
    print("    the Tenants-Policy building glass record -- use a plain")
    print("    Yes/No domain instead. Same field NAME, different field.")
    print("    C10-05's adjudication is correct and does not cover these:")
    print("    they are part of the 5-coverage consumer population C10-02")
    print("    found the filename census structurally could not see.")

    # ---------------------------------------------------------------- 4
    print("\n4 . THE 69 ELECTING STRUCTURES -- what they actually exercise")
    print("-" * 78)
    st = collections.Counter()
    cov = collections.Counter()
    col = collections.Counter()
    form = collections.Counter()
    terr = collections.Counter()
    eqclass = collections.Counter()
    ded = collections.Counter()
    all_states = collections.Counter()
    grp = collections.Counter()

    for f in files:
        d = json.loads(f.read_text(encoding="utf-8-sig"))
        s = state_of(f)
        all_states[s] += 1
        cp = d["CommercialProperty"][0]
        for loc in cp.get("CommercialPropertyLocation", []):
            for stru in loc.get("CommercialPropertyStructure", []):
                if stru.get("EQCovIndicator") not in ELECT:
                    continue
                st[s] += 1
                cov[stru.get("CovType")] += 1
                col[stru.get("CauseOfLoss")] += 1
                # EQTerr is filed on the LOCATION, not the structure --
                # confirmed by a corpus-wide field-location scan, after a
                # first pass read it off the structure and wrongly concluded
                # it was never populated at all.
                terr[str(loc.get("EQTerr"))] += 1
                eqclass[str(stru.get("EQClass"))] += 1
                ded[str(stru.get("EQDeductible"))] += 1
                got = [lbl for k, lbl in FORMS.items() if k in stru]
                form[got[0] if got else "(no form record attached)"] += 1
        for rec, node in walk(d):
            if node.get("EQCovIndicator") in ELECT:
                grp[rec] += 1

    print(f"    STATES  -- {len(st)} of {len(all_states)} jurisdictions "
          f"elect EQ on at least one structure")
    print(f"      {', '.join(f'{k}:{v}' for k, v in st.most_common())}")
    silent = sorted(set(all_states) - set(st))
    print(f"    NEVER    -- {len(silent)} file CF payloads but never elect EQ:")
    print(f"      {', '.join(silent)}")
    print()
    print("    CovType          :", dict(cov))
    print("    CauseOfLoss      :", dict(col))
    print("    EQClass          :", dict(eqclass.most_common(8)))
    print("    EQDeductible     :", dict(ded.most_common(8)))
    print("    EQTerr (location):", dict(terr.most_common()))
    print()
    print("    FORM VARIANT ATTACHED:")
    for k, v in form.most_common():
        print(f"      {v:3d}   {k}")

    print("\n    Electing records by premium group / record type:")
    for k, v in grp.most_common():
        print(f"      {v:3d}   {k}")

    # ---------------------------------------------------------------- 5
    print("\n5 . EVERY EARTHQUAKE-NAMED RECORD KEY PRESENT IN THE 364")
    print("-" * 78)
    names = collections.Counter()
    for f in files:
        t = f.read_text(encoding="utf-8-sig")
        for n in re.findall(r'"(CommercialProperty\w*Earthquake\w*)"', t):
            names[n] += 1
    if a.list_forms:
        for n, c in names.most_common():
            print(f"    {c:4d}  {n}")
    else:
        for n, c in names.most_common(12):
            print(f"    {c:4d}  {n}")
        print(f"    ... {len(names) - 12} more (--list-forms for all)")

    # ---------------------------------------------------------------- 6
    print("\n6 . REPRESENTATIVENESS -- the golden case against the corpus")
    print("-" * 78)
    rows = [
        ("state", GOLDEN["state"], st.get(GOLDEN["state"], 0)),
        ("CovType", GOLDEN["cov_type"], cov.get(GOLDEN["cov_type"], 0)),
        ("CauseOfLoss", GOLDEN["cause_of_loss"],
         col.get(GOLDEN["cause_of_loss"], 0)),
        ("form variant", GOLDEN["form"], form.get(GOLDEN["form"], 0)),
    ]
    print(f"    {'dimension':16s} {'golden case (C10-01)':38s} fixtures")
    for label, val, n in rows:
        mark = "" if n else "   <<< ZERO"
        print(f"    {label:16s} {val:38s} {n:3d}{mark}")
    print()
    print("    C10-09 already suspected this: 'the golden case's own shape is")
    print("    the SHORTEST reachable chain, not the most representative one.'")
    print("    Quantified here -- three of its four coordinates are exercised")
    print("    by ZERO of ISO's 69, and the combination by none.")

    # ---------------------------------------------------------------- 7
    print("\n7 . WHAT THE CORPUS DOES NOT DEMONSTRATE")
    print("-" * 78)
    blanket = sum(c["Yes, Included in Blanket"] for c in by_type.values())
    print(f"    EQ BLANKET   -- 'Yes, Included in Blanket' appears "
          f"{blanket} times in 364 payloads.")
    print("      C10-15 reached that branch on a hand-built 2-structure case")
    print("      and proved it rates ($6/$12). ISO's corpus never elects it,")
    print("      so chunk 9's 'no fixture, ever' problem is INHERITED by EQ's")
    print("      blanket branch specifically -- the census's claim that")
    print("      chunk 10 'does not face chunk 9's problem' holds for the")
    print("      plain chain and fails for blanket.")
    print(f"    CP 10 45     -- {form.get('CP 10 45  percentage-based sub-limit', 0)} "
          f"fixtures. The one form variant this project has never rated,")
    print("      and ISO has never demonstrated either.")
    print("    CALIFORNIA   -- "
          f"{all_states.get('CA', 0)} CF payloads, {st.get('CA', 0)} elect EQ.")
    print("      Alaska: "
          f"{all_states.get('AK', 0)} payloads, {st.get('AK', 0)} electing.")
    print("      The two most earthquake-exposed jurisdictions in the book are")
    print("      among the thinnest evidence in it. Whatever the 69 prove,")
    print("      they do not prove the high-hazard states rate correctly.")

    print("\n" + "=" * 78)
    print("C10-20 complete. No engine gap -- this task reads fixtures, it")
    print("does not rate them.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
