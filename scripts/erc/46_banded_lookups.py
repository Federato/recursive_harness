"""Stage 3 step 1: what a banded lookup has to do.

`Lookup` currently refuses a table whose key is a range, because a stepped
reading of a band is wrong by up to the width of the band and a wrong factor is
invisible. This sizes and specifies the thing before it is built.

  B1 population   how many table definitions are banded, and how many carry
                  `InterpolateMode="Linear"` on the value side
  B2 reachable    which of them a `Lookup` actually names -- a banded table no
                  rule ever reads costs nothing
  B3 boundaries   every `RangeType` in use, which is what decides whether a
                  value sitting exactly on a bound falls in the band below or
                  above
  B4 arity        how many key ranges one table carries, and whether a banded
                  table also has plain equality key columns
  B5 interpolate  the shape of the 18 interpolated ranges: which key range they
                  interpolate along

Emits out/banded_lookups.txt.
"""
from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
c = import_module("00_common")
rules_packages = import_module("42_node_surface").rules_packages

from gl_engine.erc.tables import Shape, list_tables, parse_def   # noqa: E402


def main() -> None:
    pkgs, n_dirs, dupes = rules_packages()

    shapes = Counter()
    ranged: dict[str, dict] = {}          # table name -> a representative def
    range_types = Counter()
    n_key_ranges = Counter()
    mixed = Counter()
    interp = []
    named = Counter()                     # tables a Lookup actually names

    for pk in pkgs:
        for kind in ("Rate", "Domain"):
            for name in list_tables(pk.content, kind):
                cat = "Rate Tables" if kind == "Rate" else "Domain Tables"
                path = pk.content / cat / f"{name}Def.{kind}TableDef.xml"
                if not path.exists():
                    continue
                try:
                    d = parse_def(path, name, kind)
                except Exception:                        # noqa: BLE001
                    continue
                shapes[d.shape.name] += 1
                if d.key_ranges or any(r.interpolate for r in d.value_ranges):
                    ranged.setdefault(name, {"kind": kind, "def": d,
                                             "pkg": pk.pkg_id})
                    n_key_ranges[len(d.key_ranges)] += 1
                    if d.key_ranges and d.key_cols:
                        mixed["banded + equality columns"] += 1
                    elif d.key_ranges:
                        mixed["banded only"] += 1
                    for r in d.key_ranges:
                        range_types[r.range_type or "(empty)"] += 1
                    for r in d.value_ranges:
                        if r.interpolate:
                            interp.append((name, r.name, r.interpolate,
                                           r.range_key_col))

        for f in (pk.content / "Rules").glob("*.Rule.xml"):
            for el in ET.fromstring(c.read_text(f)).iter():
                if c.lname(el.tag) == "Lookup":
                    m = el.attrib.get("MatrixFromConstant")
                    if m:
                        named[m] += 1

    reachable = {n: v for n, v in ranged.items() if named.get(n)}

    L = []; A = L.append
    A("BANDED LOOKUPS -- WHAT ONE HAS TO DO")
    A("")
    A(f"    packages: {len(pkgs)} of {n_dirs} directories")
    A("")
    A("B1  POPULATION  (table DEFINITIONS, counted per package)")
    for k, n in shapes.most_common():
        A(f"    {k:14s} {n:7d}")
    A(f"    distinct table NAMES carrying a range: {len(ranged)}")
    A("")
    A("B2  REACHABLE  (named by at least one Lookup)")
    A(f"    {len(reachable)} of {len(ranged)} ranged tables are ever looked up")
    for n in sorted(reachable, key=lambda x: -named[x]):
        d = ranged[n]["def"]
        kr = ", ".join(f"{r.name}[{r.range_type or 'empty'}]"
                       for r in d.key_ranges)
        vi = ", ".join(f"{r.name}:{r.interpolate}"
                       for r in d.value_ranges if r.interpolate)
        A(f"      {n:44s} {named[n]:6d} lookups")
        A(f"        key cols   : {[x.name for x in d.key_cols]}")
        A(f"        key ranges : {kr or '-'}")
        if vi:
            A(f"        interpolate: {vi}")
    unreachable = sorted(set(ranged) - set(reachable))
    A(f"    never looked up ({len(unreachable)}): {unreachable[:12]}")
    A("")
    A("B3  BOUNDARY SEMANTICS  (@RangeType on key ranges)")
    for k, n in range_types.most_common():
        A(f"    {k:32s} {n}")
    A("")
    A("B4  ARITY")
    A(f"    key ranges per ranged table: {dict(sorted(n_key_ranges.items()))}")
    for k, n in mixed.most_common():
        A(f"    {k:32s} {n}")
    A("")
    A("B5  INTERPOLATED VALUE RANGES")
    seen = {}
    for name, rname, mode, along in interp:
        seen.setdefault((name, rname), (mode, along))
    A(f"    distinct (table, value range): {len(seen)}")
    for (name, rname), (mode, along) in sorted(seen.items()):
        A(f"      {name:40s} {rname:28s} {mode} along {along}")

    (c.OUT / "banded_lookups.txt").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
