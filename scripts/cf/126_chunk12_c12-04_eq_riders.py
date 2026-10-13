#!/usr/bin/env python3
"""Chunk 12, C12-04 -- the Earthquake riders: reused chain, or a chain of their own?

The opening census counted 25 family files with "Earthquake" in the name and
the task list assumed each one "reuses chunk 10's EQ chain". Chunk 10 built
and gated one EQ chain per core group (`SetEQRate` -> `SetFinalEQRate`, with
`EQLimitToUse`, `EQCauseOfLossAdjustment` and the deductible factors), so the
question is concrete: does each rider's premium arrive at a number chunk 10
already proved, or does it look up an Earthquake rate of its own?

Three things are checked, and none is assumed:

  1  THE POPULATION. "Earthquake" in the file name misses Unmanned
     Aircraft, whose EQ cells are named `...DetailEQCov`. Both spellings are
     counted.
  2  THE DATAFLOW. From each rider's `SetPremium`, every field it reads is
     followed back to the rule that WRITES it, through the family's own files,
     until it reaches a field no family file writes (a core record's field,
     i.e. chunk 1-11 machinery) or a table `Lookup` (a rate of the family's
     own). The trace is static and by field name, so it over-approximates.
     That errs toward reporting more own tables, never fewer.
  3  UNMANNED AIRCRAFT'S TWO EMPTY TABLES. `EQLossCostPrsnlProp` and
     `EQPercentageDeductibleFactor` are header-only at countrywide. Who reads
     them, whether any state or older parent files rows under the same or a
     sibling name, and what the EQ cell prices at when the lookup misses.

    python scripts/cf/126_chunk12_c12-04_eq_riders.py

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

census = import_module("123_chunk12_census")
census11 = import_module("106_chunk11_census")
ASOF = census.ASOF
KEYS = census.FAMILIES
EQ_NAME = re.compile(r"Earthquake|EQCov")
RULE = re.compile(r'<rul:Rule Name="([^"]+)"[\s\S]*?</rul:Rule>')
#: Fields the engine's chunk 10 chain writes on a core group (confirmed by
#: `95_chunk10_c10-11_all_groups_chain.py`); used only to label what a rider reaches.
CHUNK10 = {"EQRate", "FinalEQRate", "EQBaseRate", "EQCauseOfLossAdjustment", "BlktEQAvgRate",
           "EQLimitToUse", "EQDeductibleFactor", "EQSubLimitFlatDeductibleFactor",
           "EQFlatDeductibleFactor", "EQPercentageDeductibleFactor", "BCEGEQFactor",
           "EQSprinklerLeakageOnlyBldgFactor", "EQSprinkleredRiskFactor"}


#: The chunk 10 fields that ARE an Earthquake rate. Cyber, indicator, class and
#: limit fields are EQ-named too, but a rider that reaches only those has not
#: borrowed chunk 10's rate.
RATE_FIELDS = {"FinalEQRate", "EQCauseOfLossAdjustment", "EQRate", "AdjustedEQRate",
               "BlktEQAvgRate", "EQBaseRate"}


def rules_of(text: str) -> dict[str, str]:
    return {m.group(1): m.group(0) for m in RULE.finditer(text)}


def writers(fam_rules: dict[str, dict[str, str]]):
    """field -> [(file, rule)] for every `ToDataDef` inside a family file."""
    out = collections.defaultdict(list)
    for f, rs in fam_rules.items():
        for r, body in rs.items():
            for fld in set(re.findall(r'ToDataDef="([^"/\[\]]+)"', body)):
                out[fld].append((f, r))
    return out


def stem(n: str) -> str:
    return n.replace("CommercialProperty", "", 1).replace("Rules.Rule.xml", "")


def lineage(rider: str, fam_rules) -> set[str]:
    """The rider's own file and its ancestors inside the family: every family
    file whose stem (less a trailing `Detail`/`Dtl`) is a prefix of the
    rider's. Keeps a field-name trace from wandering into other families."""
    r = stem(rider)
    out = set()
    for n in fam_rules:
        s = re.sub(r"(Detail|Dtl)$", "", stem(n))
        if r.startswith(s):
            out.add(n)
    return out


def trace(start_file, start_rule, fam_rules, write_idx, depth=8):
    """Closure of reads from one rule: own tables, and fields no family writes."""
    tables, core, seen = set(), set(), set()
    allowed = lineage(start_file, fam_rules)
    core_calls = set()
    stack = [(start_file, start_rule, 0)]
    while stack:
        f, r, d = stack.pop()
        if (f, r) in seen or d > depth:
            continue
        seen.add((f, r))
        body = fam_rules[f].get(r, "")
        tables |= set(re.findall(r'MatrixFromConstant="([^"]+)"', body)) - {"Pages"}
        for called in re.findall(r'FileName="([^"]+)" Rule="([^"]+)"', body):
            fn = called[0] + ".Rule.xml"
            if fn in allowed:
                stack.append((fn, called[1], d + 1))
            elif fn not in fam_rules:
                core_calls.add(f"{stem(fn)}.{called[1]}")
        for path in re.findall(r'FromDataDef="([^"]+)"', body):
            fld = path.rstrip("/").split("/")[-1]
            if fld.startswith("/") or not fld:
                continue
            ws = [w for w in write_idx.get(fld, []) if w[0] in allowed]
            if ws:
                for w in ws:
                    stack.append((w[0], w[1], d + 1))
            else:
                core.add(fld)
    return tables, core | {f"call:{c}" for c in core_calls}


def main():
    b = book_for("OR", ASOF)
    cw = b.parent.package.content
    texts = {f.name: f.read_text(encoding="utf-8-sig")
             for f in (cw / "Rules").glob("*.xml")}
    fam_rules = {n: rules_of(s) for n, s in texts.items()
                 if any(k in n for k in KEYS.values())}
    write_idx = writers(fam_rules)

    riders = sorted(n for n in fam_rules if EQ_NAME.search(n)
                    and "SetPremium" in fam_rules[n])
    by_fam = collections.Counter(next(f for f, k in KEYS.items() if k in n) for n in riders)
    named = sum(1 for n in riders if "Earthquake" in n)
    print(f"{b}\n")
    print("=== 1  Population ===\n")
    print(f"  {len(riders)} EQ rider files with a SetPremium: {named} named '*Earthquake*' "
          f"(the census's 25) + {len(riders) - named} named '*EQCov*'")
    for f in KEYS:
        print(f"    {f:22s} {by_fam[f]}")

    print("\n=== 2  Dataflow from each rider's SetPremium ===\n")
    core_tables = {t for n, x in texts.items() if n not in fam_rules
                   for t in re.findall(r'MatrixFromConstant="([^"]+)"', x)}
    # What chunk 10 proved: every EQ-named field a CORE (non-family) file writes.
    chunk10 = {f for n, x in texts.items() if n not in fam_rules
               for f in re.findall(r'ToDataDef="([^"/\[\]]*EQ[^"/\[\]]*)"', x)}
    rows = []
    for n in riders:
        fam = next(f for f, k in KEYS.items() if k in n)
        tables, core = trace(n, "SetPremium", fam_rules, write_idx)
        eq_tables = sorted(t for t in tables if re.search(r"^EQ|EQ|Earthquake", t))
        other_tables = sorted(set(tables) - set(eq_tables))
        shared = [t for t in eq_tables if t in core_tables]
        own = [t for t in eq_tables if t not in core_tables]
        eq_tables = ([f"{t} (shared with core)" for t in shared]
                     + [f"{t} (family only)" for t in own])
        reached = sorted((core & chunk10) | {c for c in core if c.startswith("call:")})
        rows.append((fam, n, eq_tables, other_tables, reached, sorted(core - CHUNK10)))
    shapes = collections.defaultdict(list)
    for fam, n, eqt, ot, reached, rest in rows:
        if any("family only" in t for t in eqt):
            verdict = "family EQ factor on top of chunk 10's rate"
        elif eqt:
            verdict = "re-runs chunk 10's lookups on its own record (shared tables)"
        elif set(reached) & RATE_FIELDS:
            verdict = "reads chunk 10's computed EQ rate"
        else:
            verdict = ("OWN RATE: the family's own tables (their Earthquake rows), "
                       "no chunk 10 EQ value")
        shapes[(fam, verdict, tuple(eqt), tuple(reached), tuple(ot))].append(n)
    for (fam, verdict, eqt, reached, ot), ns in sorted(shapes.items()):
        print(f"  [{fam}] {len(ns)} rider(s): {verdict}")
        print(f"      chunk 10 fields reached: {', '.join(reached) or '-'}")
        if eqt:
            print(f"      own EQ tables:           {', '.join(eqt)}")
        if ot:
            print(f"      own non-EQ tables:       {', '.join(ot)}")
        for x in ns[:3]:
            print(f"        {x.replace('CommercialProperty', '').replace('Rules.Rule.xml', '')}")
        if len(ns) > 3:
            print(f"        ... {len(ns) - 3} more")

    print("\n=== 3  Unmanned Aircraft's two empty EQ tables ===\n")
    books = {}
    for j in census11.JURIS:
        if j == "PR":
            continue
        try:
            books[j] = book_for(j, ASOF)
        except Exception:
            pass
    for t in ("EQLossCostPrsnlProp", "EQPercentageDeductibleFactor"):
        readers = sorted({(n, r) for n, rs in fam_rules.items() for r, body in rs.items()
                          if f'MatrixFromConstant="{t}"' in body})
        print(f"  {t}")
        print(f"    read by: {', '.join(sorted({r for _, r in readers}))} in "
              f"{len({n for n, _ in readers})} files, "
              f"families: {sorted({next(f for f, k in KEYS.items() if k in n) for n, _ in readers})}")
        core_readers = sorted({n for n, s in texts.items()
                               if f'MatrixFromConstant="{t}"' in s and n not in fam_rules})
        print(f"    also read by core files: {len(core_readers)} "
              f"({', '.join(x.replace('CommercialProperty', '').replace('Rules.Rule.xml', '') for x in core_readers[:4])})")
        filed = {}
        for j, bk in books.items():
            for layer in (bk.state.package.content, bk.parent.package.content):
                p = layer / "Rate Tables" / f"{t}.RateTable.csv"
                if p.exists():
                    with open(p, encoding="utf-8-sig") as h:
                        filed[f"{j}:{layer.name}"] = sum(1 for r in csv.reader(h) if r) - 1
                    break
        nonempty = {k: v for k, v in filed.items() if v > 0}
        print(f"    rows, per state (state layer first, else its parent): "
              f"{len(nonempty)} of {len(filed)} non-empty"
              + (f": {dict(list(nonempty.items())[:6])}" if nonempty else ""))
        sib = sorted(p.name.replace(".RateTable.csv", "") for p in (cw / "Rate Tables").glob("EQ*PrsnlProp*.csv")
                     if t not in p.name)[:8] if "PrsnlProp" in t else []
        if sib:
            print(f"    sibling tables at CW: {sib}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
