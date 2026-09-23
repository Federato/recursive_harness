#!/usr/bin/env python3
"""Chunk 12 opening census -- the endorsement families, before any task is written.

`CF-PROPERTY-BUILD-ORDER.md` item 12: "Sized, not sequenced -- take them by
family once the core is proved: Ordinance or Law (55), dependent properties,
utility services, green upgrades, debris removal, unmanned aircraft."

So this census SIZES each of the six families, the way chunk 11's census
tested its build-order sentence, and nothing is carried forward on trust:

  1  The population per family -- rule files by name, and how many carry a
     `SetPremium` (a file count is not a rating surface; chunk 11 found a
     third of its files inert).
  2  The Ordinance or Law "55" -- checked, not assumed.
  3  Rate tables each family's rules read, with row counts and dead tables.
  4  Which parent datadef groups each family attaches under (Building,
     Contents, Business Income, ...) -- the question chunk 10's C10-17 found
     decisive.
  5  The state layer -- 46 states, Puerto Rico excluded (standing rule).
  6  ISO fixtures -- the 364 CF STC payloads (NOT 924; C10-20).
  7  Engine readiness -- every `rul:` element the family uses, against the
     registry. Chunk 11's census checked element NAMES and missed an operand
     TYPE (dates); this one also lists which families use date and Power
     arithmetic, so that gap is looked for at opening.
  8  Overlap with chunks already closed -- chunk 10 found 5 optional
     coverages (Ordinance or Law, Outside Signs, Radio/TV, Builders Risk
     Renovations, Unmanned Aircraft) with their own EQ riders.

    python scripts/cf/123_chunk12_census.py

Always exits 0 -- a census, not a test.
"""
from __future__ import annotations

import collections
import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from importlib import import_module

from cf_engine.resolve import book_for
from gl_engine.interp import nodes

census11 = import_module("106_chunk11_census")
ASOF = "20260917"
ISO_CF = Path("C:/Projects/ISO_ERC_Files/CF")

#: filename keyword per family, as the build order names them
FAMILIES = {
    "Ordinance or Law": "OrdinanceOrLaw",
    "Dependent Properties": "DependentProperties",
    "Utility Services": "UtilityServices",
    "Green Upgrades": "GreenUpgrades",
    "Debris Removal": "DebrisRemoval",
    "Unmanned Aircraft": "UnmannedAircraft",
}
DATE_NODES = {"DateDifference", "DateAdd", "DateCreate", "DatePart"}
STRUCTURAL = {"Rules", "Rule", "MetaData", "MetaDataCode", "Test", "Then", "Else",
              "Keys", "When", "Otherwise", "Arg", "Param"}


def rows(path):
    with open(path, encoding="utf-8-sig") as h:
        return sum(1 for r in csv.reader(h) if r) - 1


def main():
    b = book_for("OR", ASOF)
    cw = b.parent.package.content
    rules_dir, tables_dir = cw / "Rules", cw / "Rate Tables"
    all_rules = {f.name: f.read_text(encoding="utf-8-sig") for f in rules_dir.glob("*.xml")}
    registry = set(nodes.EVAL)

    books = {}
    for j in census11.JURIS:
        if j == "PR":
            continue                       # standing rule: PR out of scope
        try:
            books[j] = book_for(j, ASOF)
        except Exception:
            pass

    stc = sorted(ISO_CF.rglob("STC/*.json"))
    stc_text = {p: p.read_text(encoding="utf-8", errors="replace") for p in stc}

    print(f"{b}\n{len(all_rules)} countrywide rule files; {len(books)} states (PR excluded); "
          f"{len(stc)} CF STC payloads\n")

    summary = []
    for fam, key in FAMILIES.items():
        files = sorted(n for n in all_rules if key in n)
        prem = [n for n in files if '"SetPremium"' in all_rules[n]]
        inert = [n for n in files if set(re.findall(r'<rul:Rule Name="([^"]+)"', all_rules[n]))
                 <= {"InitializeRuleSet", "CalculateTotalPremium", "ErcProcess"}]
        mats = collections.Counter()
        elems = collections.Counter()
        for n in files:
            s = all_rules[n]
            mats.update(set(re.findall(r'MatrixFromConstant="([^"]+)"', s)) - {"Pages"})
            elems.update(re.findall(r"<rul:(\w+)", s))
        tables = []
        for t in sorted(mats):
            f = tables_dir / f"{t}.RateTable.csv"
            tables.append((t, rows(f) if f.exists() else None))
        dead_or_empty = [t for t, r in tables if not r]
        missing = sorted(e for e in elems if e not in registry and e not in STRUCTURAL)
        dates = sorted(e for e in elems if e in DATE_NODES)
        power = elems.get("Power", 0)
        # parent groups: who attaches these files (callers outside the family)
        parents = collections.Counter()
        for n, s in all_rules.items():
            if key in n:
                continue
            for f in files:
                stem = f.replace(".Rule.xml", "")
                if f'FileName="{stem}"' in s:
                    parents[n.replace("CommercialProperty", "").replace("Rules.Rule.xml", "")] += 1
        # states filing any family file (46, PR excluded)
        filers = sorted(j for j, bk in books.items()
                        if (bk.state.package.content / "Rules").exists()
                        and any(key in p.name for p in (bk.state.package.content / "Rules").glob("*.xml")))
        fixtures = [p for p, t in stc_text.items() if key in t]
        # EQ riders from chunk 10
        eq_files = [n for n in files if "Earthquake" in n]

        print("=" * 78)
        print(f"{fam}  (filename key '{key}')")
        print("-" * 78)
        print(f"  rule files                : {len(files)}")
        print(f"    with SetPremium         : {len(prem)}")
        print(f"    inert (system rules only): {len(inert)}")
        print(f"    Earthquake-named (chunk 10 riders): {len(eq_files)}")
        print(f"  rate tables read          : {len(tables)}"
              + (f"  (0-row or unfiled: {len(dead_or_empty)})" if dead_or_empty else ""))
        for t, r in tables[:12]:
            print(f"      {t:60s} {r if r is not None else 'NOT FILED'}")
        if len(tables) > 12:
            print(f"      ... {len(tables) - 12} more")
        print(f"  attached from (callers)   : {dict(parents.most_common(6)) or '-'}")
        print(f"  states filing a family file (of {len(books)}): {len(filers)} {filers[:12]}")
        print(f"  ISO fixtures mentioning it: {len(fixtures)} of {len(stc)}")
        print(f"  engine: rul: elements NOT registered: {missing or 'none'}")
        print(f"          date nodes used: {dates or 'none'}; Power: {power}")
        summary.append((fam, len(files), len(prem), len(inert), len(tables),
                        len(dead_or_empty), len(filers), len(fixtures), bool(missing),
                        bool(dates) or power > 0))

    print("\n" + "=" * 78)
    print("SUMMARY")
    print("-" * 78)
    print(f"  {'family':22s} {'files':>5s} {'prem':>5s} {'inert':>5s} {'tables':>6s} "
          f"{'empty':>5s} {'states':>6s} {'fixt.':>5s}  gaps  dates/pow")
    for r in summary:
        print(f"  {r[0]:22s} {r[1]:5d} {r[2]:5d} {r[3]:5d} {r[4]:6d} {r[5]:5d} {r[6]:6d} "
              f"{r[7]:5d}  {'YES' if r[8] else 'no':4s}  {'YES' if r[9] else 'no'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
