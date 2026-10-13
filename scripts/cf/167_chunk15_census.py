#!/usr/bin/env python3
"""Chunk 15 opening census -- the manual-premium endorsements.

166_ grouped ten families whose `SetPremium` multiplies a company-entered
`ManualPremium` by policy modifiers and reads no rate table of its own. This
census checks that claim file by file, before any task is written:

  1  Population: every countrywide premium file of the ten families, and the
     state-only files (VA's Y2K variants), all batches.
  2  The premium formula, per file: its operands (which modifiers), the
     `DecimalPlaces` on each Product (intermediate rounding), and the `../`
     depth of each modifier path -- the same field reached from different
     depths is exactly where chunk 13's OI-111 and the Table-wrapper trap hid.
  3  Every other rule in the file: anything beyond the standard set is a
     second mechanism (a lookup, a message, a stat code) to be traced.
  4  Where the record sits: its parent in the ISO fixtures (the payload path).
  5  The state layer: 46 in-force packages (PR excluded) -- which states
     rewrite a family file, and whether the rewrite touches SetPremium.
  6  ISO evidence: fixtures carrying the record, stored responses (293) with a
     non-zero premium on it.
  7  Engine readiness: rul: elements not registered.

    python scripts/cf/167_chunk15_census.py

Always exits 0 -- a census, not a test.
"""
from __future__ import annotations

import collections
import json
import re
import sys
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))

from cf_engine.resolve import book_for
from gl_engine.interp import nodes

census11 = import_module("106_chunk11_census")
ASOF = "20260917"
ISO_CF = Path("F:/ISO_ERC_Files/CF")
RES = ROOT / "results" / "cf-raas"
STANDARD = {"InitializeRuleSet", "CalculateTotalPremium", "ErcRate", "SetPremium",
            "SetPremiumIndicator", "ErcProcess", "SetCoverageOnPolicyIndicator"}
STRUCTURAL = {"Rules", "Rule", "MetaData", "MetaDataCode", "Test", "Then", "Else",
              "Keys", "When", "Otherwise", "Arg", "Param"}

FAMILIES = [
    ("Cannabis Exclusion", r"CannabisExclusion"),
    ("Valuable Papers", r"ValuablePapers"),
    ("Newly Acquired Location (TE)", r"NewlyAcquiredLocationTimeElement"),
    ("Newly Acquired Property incr. limit", r"NewlyAcquiredOrConstructed"),
    ("Portable Storage Units", r"PortableStorageUnits"),
    ("Discretionary Payroll Expense", r"DiscretionaryPayroll"),
    ("Electronic Commerce", r"ElectronicCommerce"),
    ("Limited International Coverage", r"^CommercialProperty(BusnPrsnlProp|PropInProcessOfMfrByOthers)LimitedInternational"),
    ("Interruption of Computer Operations", r"InterruptionOfComputerOperations"),
    ("BI Y2K / electronic problems", r"Y2K"),
]


def rules(text):
    return re.findall(r'<rul:Rule Name="([^"]+)"', text)


def premium_shape(text):
    m = re.search(r'<rul:Rule Name="SetPremium".*?</rul:Rule>', text, re.S)
    if not m:
        return None
    body = m.group(0)
    ops = re.findall(r'FromDataDef="([^"]+)"', body)
    dps = [(re.search(r'DecimalPlaces="(\d+)"', a) or [None, None])[1]
           for a in re.findall(r'<rul:Product([^>]*)>', body)]
    shape = []
    for o in ops:
        depth = o.count("../")
        shape.append(f"{o.replace('../', '')}@{depth}" if depth else o)
    other = sorted(set(re.findall(r"<rul:(\w+)", body)) - {"Rule", "Sequence", "Product", "FirstValue"})
    return shape, [d or "-" for d in dps], other


def record_paths(stc_text, rec):
    """parent chain of a record in the fixtures (first hit)."""
    for t in stc_text.values():
        if f'"{rec}"' not in t:
            continue
        d = json.loads(t)
        hit = []

        def walk(o, path):
            if hit:
                return
            if isinstance(o, dict):
                for k, v in o.items():
                    if k == rec:
                        hit.append(path)
                        return
                    if isinstance(v, (dict, list)):
                        walk(v, path + [k])
            elif isinstance(o, list):
                for x in o:
                    walk(x, path)
        walk(d, [])
        if hit:
            return "/".join(p.replace("CommercialProperty", "") or "CP" for p in hit[0])
    return None


def main():
    b = book_for("OR", ASOF)
    cw = b.parent.package.content
    all_rules = {f.name: f.read_text(encoding="utf-8-sig") for f in (cw / "Rules").glob("*.xml")}
    registry = set(nodes.EVAL)

    books = {}
    for j in census11.JURIS:
        if j == "PR":
            continue
        try:
            books[j] = book_for(j, ASOF)
        except Exception:
            pass

    stc = {p.stem: p.read_text(encoding="utf-8-sig", errors="replace") for p in ISO_CF.rglob("STC/*.json")}
    replay = collections.Counter()
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

    print(f"{b}\n{len(books)} states (PR excluded); {len(stc)} CF STC payloads; "
          f"{sum(1 for _ in RES.glob('chunk13_fixture_*_response.json'))} stored ISO responses\n")

    total = 0
    shapes = collections.Counter()
    extra_all = collections.Counter()
    elems = collections.Counter()
    for fam, pat in FAMILIES:
        files = sorted(n for n, s in all_rules.items() if re.search(pat, n) and '"SetPremium"' in s)
        allf = sorted(n for n in all_rules if re.search(pat, n))
        total += len(files)
        print("=" * 78)
        print(f"{fam}: {len(files)} premium files ({len(allf)} files in all)")
        for n in allf:
            s = all_rules[n]
            elems.update(re.findall(r"<rul:(\w+)", s))
            recs = sorted(set(re.findall(r'DataDefGroup="([^"]+)"', s)))
            rs = rules(s)
            extra = [r for r in rs if r not in STANDARD]
            extra_all.update(extra)
            ps = premium_shape(s)
            print(f"  {n.replace('CommercialProperty', '').replace('Rules.Rule.xml', '')}")
            print(f"    records : {', '.join(r.replace('CommercialProperty', '') for r in recs)}")
            for r in recs:
                where = record_paths(stc, r)
                fx = sum(1 for t in stc.values() if f'"{r}"' in t)
                print(f"    in fixtures: {fx:3d}  non-zero ISO premium: {replay[r]:3d}  path: {where or '-'}")
            if ps:
                shapes[tuple(o.split('@')[0] for o in ps[0])] += 1
                print(f"    SetPremium: {' x '.join(ps[0])}")
                print(f"      Product DecimalPlaces (outer->inner): {ps[1]}   other nodes: {ps[2] or '-'}")
            else:
                print("    SetPremium: none (not a premium file)")
            if extra:
                print(f"    other rules ({len(extra)}): {', '.join(extra[:14])}{' ...' if len(extra) > 14 else ''}")
            rewrites = []
            for j, bk in books.items():
                sp = bk.state.package.content / "Rules" / n
                if sp.exists():
                    st = sp.read_text(encoding="utf-8-sig")
                    touched = "SetPremium" if 'Name="SetPremium"' in st else ",".join(r for r in rules(st) if r not in ("InitializeRuleSet",))[:60]
                    rewrites.append(f"{j}[{touched}]")
            print(f"    state rewrites: {' '.join(rewrites) or '-'}")

    # state-only files of these families (every batch, PR excluded)
    print("=" * 78)
    print("State-only files of these families (all batches, PR excluded):")
    cw_names = set(all_rules)
    only = collections.defaultdict(set)
    for pkg in sorted(ISO_CF.glob("*/CF ?? *")):
        st = pkg.name.split()[1]
        if st == "PR" or not (pkg / "Rules").exists():
            continue
        for p in (pkg / "Rules").glob("*.xml"):
            if p.name in cw_names or not any(re.search(pat.lstrip("^"), p.name) for _, pat in FAMILIES):
                continue
            s = p.read_text(encoding="utf-8-sig", errors="replace")
            ps = premium_shape(s)
            key = p.name.replace("CommercialProperty", "").replace("Rules.Rule.xml", "")
            only[(key, " x ".join(ps[0]) if ps else "no SetPremium")].add(f"{st} {pkg.name.split()[2]}")
    for (k, shp), v in sorted(only.items()):
        print(f"  {k}\n    {shp}\n    in: {', '.join(sorted(v))}")

    print("=" * 78)
    print(f"TOTAL countrywide premium files: {total}")
    print("Premium shapes (operands, ignoring depth):")
    for sh, c in shapes.most_common():
        print(f"  {c:2d} x {' x '.join(sh)}")
    print(f"Non-standard rules across the families: {dict(extra_all.most_common(20))}")
    missing = sorted(e for e in elems if e not in registry and e not in STRUCTURAL)
    print(f"rul: elements not registered in the engine: {missing or 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
