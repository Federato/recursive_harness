#!/usr/bin/env python3
"""Chunk 26 opening census -- Specific and Tentative rating.

Chunk 26 adds no files: it is the second rating path (RatingType = Specific or
Tentative, and the states' RatingTypeBasicGroupII) through the core coverages
chunks 1-8 built. The engine interprets ISO's rules generically, so the branches
already exist in what it runs; the census maps them and the evidence for them:

  1  Branches: every rule, in CW and each of the 46 in-force state packages, whose
     body tests RatingType / RatingTypeBasicGroupII or reads a specific or
     tentative rate (SpecificGroupIRate, SpecificGroupIIRate, TentativeRate ...),
     by file, with the values tested.
  2  The rate tables those rules read.
  3  Messages naming Specific or Tentative rating, any file (CW + 46 states).
  4  Domains: which RatingType values each state's Domain Tables offer, per
     coverage, where the package files them.
  5  Editions: each CW branch rule compared in 2026 V01 and 2023 V02 / V03 / V04.
  6  Evidence: stored requests with a Specific / Tentative rating type, by field,
     record, state and source, and whether ISO priced the building's Group I / II
     on them (non-zero premium in the paired response).

    python scripts/cf/907_chunk26_census.py

Always exits 0 -- a census, not a test.
"""
from __future__ import annotations

import collections
import csv
import json
import re
import sys
import time
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))

from cf_engine.resolve import book_for

s18 = import_module("164_chunk14_c14-18_all_states")
ASOF = "20260917"
ISO_CF = Path("F:/ISO_ERC_Files/CF")
RES = ROOT / "results"
P = "CommercialProperty"
EDITIONS = {"CW 2026 V01": ISO_CF / "20260601" / "CFCW20260601V01",
            "CW 2023 V02": ISO_CF / "20230801v2" / "CF CW 20230801 V02",
            "CW 2023 V03": ISO_CF / "20230801v3" / "CF CW 20230801 V03",
            "CW 2023 V04": ISO_CF / "20230801v4" / "CF CW 20230801 V04"}
FIELD = re.compile(r'(RatingType(?:BasicGroupII)?|SpecificGroupI{1,2}Rate|TentativeRate|Specific\w*Rate|Tentative\w*)')
TESTED = re.compile(r'FromDataDef="[^"]*RatingType(?:BasicGroupII)?"[^>]*/>\s*</rul:\w+>\s*<rul:Constant[^>]*>([^<]+)<'
                    r'|<rul:Constant[^>]*>(Specific|Tentative|Class)</rul:Constant>')
RULE = re.compile(r'<rul:Rule Name="([^"]+)"[^>]*DataDefGroup="([^"]+)"[^>]*>(.*?)</rul:Rule>', re.S)


def short(n):
    return n.replace(P, "").replace("Rules.Rule.xml", "")


def branches(text):
    """rule name -> (group, fields named, values tested, tables read)"""
    out = {}
    for m in RULE.finditer(text):
        name, grp, body = m.groups()
        fields = sorted(set(FIELD.findall(body)))
        if not fields:
            continue
        vals = sorted({a or b for a, b in TESTED.findall(body)} - {""})
        tabs = sorted(set(re.findall(r'MatrixFromConstant="([^"]+)"', body)))
        out[name] = (grp, fields, vals, tabs)
    return out


def main():
    t0 = time.monotonic()
    or_book = book_for("OR", ASOF)
    cw = or_book.parent.package.content
    cw_rules = {f.name: f.read_text(encoding="utf-8-sig") for f in (cw / "Rules").glob("*.xml")}
    books = {j: book_for(j, ASOF) for j in s18.STATES}
    print(f"{or_book}\n{len(cw_rules)} CW rule files; {len(books)} states (PR excluded)\n")

    # 1-2 CW branches
    print("[1/6] CW rules testing a rating type or reading a specific / tentative rate", flush=True)
    cw_br = {}
    for n, t in sorted(cw_rules.items()):
        b = branches(t)
        if b:
            cw_br[n] = b
    all_tabs = collections.Counter()
    for n, b in cw_br.items():
        print(f"  {short(n)}")
        for r, (grp, fields, vals, tabs) in b.items():
            all_tabs.update(tabs)
            print(f"      {r:45s} fields {', '.join(fields)[:70]}; values {vals or '-'}; tables {', '.join(tabs)[:80] or '-'}")
    print(f"  {len(cw_br)} CW files, {sum(len(b) for b in cw_br.values())} rules")

    # 1 state layer
    m, sec = divmod(int(time.monotonic() - t0), 60)
    print(f"\n[2/6  {m}m{sec:02d}s] state packages: rules testing a rating type (overrides and state-only)", flush=True)
    per_state = {}
    gii_states = []
    for j, b in sorted(books.items()):
        rd = b.state.package.content / "Rules"
        if not rd.exists():
            continue
        found = {}
        for f in rd.glob("*.xml"):
            br = branches(f.read_text(encoding="utf-8-sig", errors="replace"))
            if br:
                found[f.name] = br
        if found:
            per_state[j] = found
            if any("RatingTypeBasicGroupII" in fl for br in found.values() for _, fl, _, _ in br.values()):
                gii_states.append(j)
    for j, found in per_state.items():
        rules = [f"{short(n)[:28]}.{r}" for n, br in found.items() for r in br]
        print(f"  {j}: {len(found)} files, {len(rules)} rules: {'; '.join(rules)[:210]}")
    print(f"  states with a rating-type rule: {len(per_state)}; testing RatingTypeBasicGroupII: {len(gii_states)} "
          f"({' '.join(gii_states)})")
    print(f"  states with NO rating-type rule: {' '.join(sorted(set(books) - set(per_state))) or 'none'}")

    # 3 messages
    m, sec = divmod(int(time.monotonic() - t0), 60)
    print(f"\n[3/6  {m}m{sec:02d}s] messages naming Specific / Tentative rating (CW + 46 states)", flush=True)
    msgs = collections.defaultdict(set)
    pools = [("CW", cw_rules)] + [(j, {f.name: f.read_text(encoding="utf-8-sig", errors="replace")
                                       for f in (b.state.package.content / "Rules").glob("*.xml")})
                                  for j, b in books.items() if (b.state.package.content / "Rules").exists()]
    for j, pool in pools:
        for n, t in pool.items():
            for mm in RULE.finditer(t):
                name, grp, body = mm.groups()
                if not re.search(r"Add(Error|Warning|Info)Message", body):
                    continue
                text = "; ".join(re.findall(r'Param="Message">\s*<rul:Constant[^>]*>([^<]+)<', body))
                if re.search(r"Specific|Tentative|Rating Type", text, re.I) or FIELD.search(body):
                    msgs[(grp.replace(P, "")[:24], text[:120] or name)].add(j)
    for (grp, text), js in sorted(msgs.items()):
        print(f"  [{grp:24s}] {text}  ({' '.join(sorted(js)) if len(js) < 8 else str(len(js)) + ' packages'})")
    print(f"  {len(msgs)} message rules")

    # 4 domains
    m, sec = divmod(int(time.monotonic() - t0), 60)
    print(f"\n[4/6  {m}m{sec:02d}s] Domain Tables offering RatingType values", flush=True)
    for pkg in [cw] + [b.state.package.content for b in books.values()]:
        dt = pkg / "Domain Tables"
        if not dt.exists():
            continue
        for f in dt.glob("*.csv"):
            head = f.open(encoding="utf-8-sig", errors="replace").readline()
            if "RatingType" not in head:
                continue
            with open(f, encoding="utf-8-sig", errors="replace") as h:
                rows = list(csv.DictReader(h))
            col = [c for c in rows[0].keys() if c and "RatingType" in c] if rows else []
            vals = collections.Counter(r[c] for r in rows for c in col)
            print(f"  {pkg.name:28s} {f.stem:40s} {len(rows):4d} rows; {dict(vals)}")

    # 5 editions
    m, sec = divmod(int(time.monotonic() - t0), 60)
    print(f"\n[5/6  {m}m{sec:02d}s] CW branch rules per edition (vs 2026 V01)", flush=True)
    diffs = 0
    for k, root in EDITIONS.items():
        if k == "CW 2026 V01":
            continue
        for n, br in cw_br.items():
            f = root / "Rules" / n
            if not f.exists():
                print(f"  {k}: {short(n)} NO FILE")
                diffs += 1
                continue
            other = {mm.group(1): re.sub(r"\s+", " ", mm.group(3))
                     for mm in RULE.finditer(f.read_text(encoding="utf-8-sig", errors="replace"))}
            mine = {mm.group(1): re.sub(r"\s+", " ", mm.group(3)) for mm in RULE.finditer(cw_rules[n])}
            for r in br:
                if other.get(r) != mine.get(r):
                    print(f"  {k}: {short(n)}.{r} {'missing' if r not in other else 'differs'}")
                    diffs += 1
    print(f"  {diffs} differences")

    # 6 evidence
    m, sec = divmod(int(time.monotonic() - t0), 60)
    print(f"\n[6/6  {m}m{sec:02d}s] stored requests with a Specific / Tentative rating type", flush=True)
    ev = collections.Counter()
    priced = collections.Counter()
    states = collections.defaultdict(collections.Counter)
    for p in RES.rglob("*request*.json"):
        t = p.read_text(encoding="utf-8", errors="replace")
        hits = re.findall(r'"(RatingType(?:BasicGroupII)?)"\s*:\s*"(Specific|Tentative)"', t)
        if not hits:
            continue
        src = p.relative_to(RES).parts[0]
        st = (re.search(r'"State"\s*:\s*"([A-Z]{2})"', t) or [None, "?"])[1]
        for fld, val in set(hits):
            ev[(src, fld, val)] += 1
            states[(fld, val)][st] += 1
        r = p.with_name(p.name.replace("request", "response"))
        if not r.exists():
            ev[(src, "no response", "")] += 1
            continue
        try:
            body = json.loads(r.read_text(encoding="utf-8"))
        except Exception:
            continue
        got = collections.Counter()

        def walk(o, tag):
            if isinstance(o, dict):
                if "Premium" in o and re.search(r"Building(BasicGroupI|BasicGroupII)Coverage$", tag):
                    try:
                        got[tag] += float(o["Premium"] or 0)
                    except (TypeError, ValueError):
                        pass
                for k2, v in o.items():
                    if isinstance(v, (dict, list)):
                        walk(v, k2)
            elif isinstance(o, list):
                for x in o:
                    walk(x, tag)
        walk(body, "Body")
        for tag, v in got.items():
            priced[(set(hits).pop()[1], short(tag), "non-zero" if v else "zero")] += 1
    for k, v in sorted(ev.items()):
        print(f"  {v:5d}  {k}")
    for (fld, val), c in states.items():
        print(f"  {fld} = {val}: {dict(c.most_common())}")
    for k, v in sorted(priced.items()):
        print(f"  ISO premium {k}: {v}")
    return 0


if __name__ == "__main__":
    rc = main()
    # every rule of the files naming the rating-type fields, across the four CW editions (carried from
    # chunk 20's gate; 211_ C21-16)
    print("\n" + "=" * 90 + "\nEDITIONS: EVERY RULE")
    import _edition_rules
    _edition_rules.report(lambda n, t: bool(FIELD.search(t)))
    raise SystemExit(rc)
