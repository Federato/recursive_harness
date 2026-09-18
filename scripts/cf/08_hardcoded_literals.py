#!/usr/bin/env python3
"""Gate point 5 -- every hardcoded literal key, listed.

Some of ISO's rules have an answer baked in rather than read from the
submission. A lookup key written as a literal is a dropdown wired shut: the
table still carries rows for every other value, and on that path none of them
can ever be reached. The rows are published, present, and unusable.

That is not a defect -- it is how ISO files several rules -- but it has to be a
STATED decision rather than something rediscovered as a bug six months later,
which is why the gate asks for the list.

This enumerates, across the whole Building coverage rather than the one chain
chunk 1 walks:

  1. **Pinned lookup keys.** Every `rul:Lookup` whose `Keys` include a literal,
     mapped positionally onto the table's DECLARED key order, with the share of
     that table's rows the literal makes unreachable.
  2. **Branch literals.** Every `Equal`/`NotEqual` comparing a datadef against
     a literal -- the conditions that decide which path a risk takes.

The countrywide `CW` literal in a state/countrywide two-pass lookup is excluded
from (1) by name: it is the fallback idiom, not a pin, and reporting 11,000 of
them would bury the handful that matter.

    python scripts/cf/08_hardcoded_literals.py [--juris OR] [--all]

Exit 0 always -- a census, not a pass/fail. What it produces is the map chunks
3-8 inherit instead of rediscovering.
"""
from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from importlib import import_module

from cf_engine.resolve import book_for
from gl_engine.errors import EngineError
from gl_engine.erc.tables import Range

golden = import_module("01_golden_case")

#: The Building side of the corpus: the structure itself and every coverage
#: hanging off it. Chunk 1 walked one chain through this; the gate wants the
#: whole of it.
BUILDING_GROUP_PREFIX = "CommercialPropertyStructure"

#: Excluded from the pinned-key report. `CW` in a state-code position is ISO's
#: two-pass fallback (`FirstNonNull(Lookup(state), Lookup("CW"))`), not a pin.
FALLBACK_LITERALS = {"CW"}


def lname(tag):
    return tag.rsplit("}", 1)[-1]


def rule_file_name(path: Path) -> str:
    """`CommercialPropertyStructureRules` from `...Rules.Rule.xml`.

    `Path.stem` strips ONE suffix and leaves `...Rules.Rule`, which matches no
    `RunRule @FileName` and silently found zero argument-supplied literals --
    the exact population this scan exists to find.
    """
    return path.name[: -len(".Rule.xml")]


def literal_of(el):
    """The literal this Keys child pins, or None if it reads live data.

    Two shapes count. `rul:Constant` is unambiguous. `rul:FirstValue` counts
    only when it carries a `@FromConstant` and NO `@FromDataDef` -- with a
    datadef it is a live read with a fallback, which is the opposite of pinned.
    """
    t = lname(el.tag)
    if t == "Constant":
        return (el.text or "").strip()
    if t == "FirstValue" and "FromConstant" in el.attrib \
            and "FromDataDef" not in el.attrib:
        return el.attrib["FromConstant"].strip()
    return None


def key_names(defn):
    """The table's key columns in ISO's declared order, ranges included."""
    out = []
    for item in defn.key_items:
        out.append(item.name if isinstance(item, Range) else item.name)
    return out


def lookup_rules(package_dir: Path):
    """rule name -> (matrix, [param name per key position]).

    **The literals that matter mostly do not appear in `Keys`.** ISO's idiom is
    a thin `LookupX` rule whose `Keys` read `FromParam`, called by a `RunRule`
    that supplies the literal as an `Arg`. The documented vacant-building trap
    is exactly that shape:

        <rul:RunRule Rule="LookupVandalismExclusionFactor">
          <rul:Arg Param="classCode">
            <rul:Constant Type="string">1180</rul:Constant>

    A scan that only reads `Keys` sees a live parameter and reports nothing.
    So this indexes the lookup rules first, and the call sites are joined to
    them below.
    """
    index = {}
    for f in sorted((package_dir / "Rules").glob("*.Rule.xml")):
        try:
            root = ET.fromstring(f.read_text(encoding="utf-8-sig",
                                             errors="replace"))
        except ET.ParseError:
            continue
        for rule in root:
            if lname(rule.tag) != "Rule":
                continue
            for lk in rule.iter():
                if lname(lk.tag) != "Lookup":
                    continue
                matrix = lk.get("MatrixFromConstant")
                keys = next((c for c in lk if lname(c.tag) == "Keys"), None)
                if not matrix or keys is None:
                    continue
                params = [c.attrib.get("FromParam") for c in keys]
                # First lookup in the rule wins: the second is the countrywide
                # pass of the same two-pass idiom, same keys.
                index.setdefault((rule_file_name(f), rule.get("Name")),
                                 (matrix, params))
    return index


def scan(package_dir: Path, index, prefix=None):
    """Returns `(pins, branches, live)`.

    `live` is every (table, key position) that is ALSO supplied from a datadef
    somewhere. It is the difference between "this table is dead" and "this
    table is dead FROM THIS SITE", and only the second is ever true here:
    `VandalismExclFactor` is pinned to class 1180 on the vacant-building
    branch, and read with the building's real class everywhere else.
    """
    pins, branches, live = [], Counter(), set()
    for f in sorted((package_dir / "Rules").glob("*.Rule.xml")):
        try:
            root = ET.fromstring(f.read_text(encoding="utf-8-sig",
                                             errors="replace"))
        except ET.ParseError:
            continue
        for rule in root:
            if lname(rule.tag) != "Rule":
                continue
            group = rule.get("DataDefGroup") or ""
            pre = prefix or BUILDING_GROUP_PREFIX
            # `startswith` is right for a coverage and its per-form coverage
            # groups, but WRONG across the Special Class / Special Class
            # Business Income boundary -- those are two chunks, not one.
            if not group.startswith(pre) or group.startswith(pre + "BusnIncome"):
                continue
            rname = rule.get("Name")

            for lk in rule.iter():
                if lname(lk.tag) != "Lookup":
                    continue
                matrix = lk.get("MatrixFromConstant")
                keys = next((c for c in lk if lname(c.tag) == "Keys"), None)
                if not matrix or keys is None:
                    continue
                for pos, child in enumerate(keys):
                    lit = literal_of(child)
                    if lit is None:
                        live.add((matrix, pos))
                        continue
                    if lit in FALLBACK_LITERALS:
                        continue
                    pins.append({"rule": rname, "group": group, "file": rule_file_name(f),
                                 "matrix": matrix, "pos": pos, "literal": lit,
                                 "via": "Keys"})

            # ...and the literals supplied as ARGUMENTS to a lookup rule,
            # which is where the ones that actually bite live.
            for rr in rule.iter():
                if lname(rr.tag) != "RunRule":
                    continue
                target = (rr.get("FileName"), rr.get("Rule"))
                if target not in index:
                    continue
                matrix, params = index[target]
                for arg in rr:
                    if lname(arg.tag) != "Arg":
                        continue
                    param = arg.get("Param")
                    kids = list(arg)
                    lit = literal_of(kids[0]) if len(kids) == 1 else None
                    if lit is None or lit in FALLBACK_LITERALS or param is None:
                        continue
                    if param not in params:
                        continue
                    if lit is None:
                        live.add((matrix, params.index(param)))
                        continue
                    pins.append({"rule": rname, "group": group, "file": rule_file_name(f),
                                 "matrix": matrix, "pos": params.index(param),
                                 "literal": lit, "via": f"Arg {param}"})

            for cmp_el in rule.iter():
                if lname(cmp_el.tag) not in ("Equal", "NotEqual"):
                    continue
                kids = list(cmp_el)
                if len(kids) != 2:
                    continue
                lits = [literal_of(k) for k in kids]
                fields = [k.attrib.get("FromDataDef") for k in kids]
                for lit, fld in zip(lits, reversed(fields)):
                    if lit is not None and lit != "" and fld:
                        branches[(fld, lit)] += 1
    return pins, branches, live


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--juris", default="OR")
    ap.add_argument("--asof", default=golden.ASOF)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--group", default=BUILDING_GROUP_PREFIX,
                    help="datadef-group prefix to census "
                         "(e.g. CommercialPropertySpecialClass)")
    a = ap.parse_args()

    book = book_for(a.juris, a.asof)
    cw = book.parent.package if book.parent else book.state.package
    print(f"Gate point 5 -- hardcoded literals across {a.group}")
    print(f"rules from {cw.pkg_id}; tables resolved for "
          f"{a.juris}@{a.asof}\n")

    index = lookup_rules(cw.content)
    pins, branches, live = scan(cw.content, index, a.group)

    # ---------------------------------------------------- 1. pinned keys
    by_site = defaultdict(list)
    for p in pins:
        by_site[(p["matrix"], p["pos"], p["literal"])].append(p)
    via_arg = sum(1 for p in pins if p["via"] != "Keys")

    print("1. PINNED LOOKUP KEYS -- a literal where a key column belongs")
    print(f"   {len(pins)} occurrences at {len(by_site)} distinct sites "
          f"(countrywide `CW` fallbacks excluded)\n")

    rows = []
    for (matrix, pos, lit), occ in by_site.items():
        try:
            table = book.table(matrix)
        except EngineError:
            rows.append((matrix, "?", lit, None, None, occ))
            continue
        names = key_names(table.definition)
        col = names[pos] if pos < len(names) else f"#{pos}"
        try:
            idx = table.col(col)
            distinct = {str(r[idx]) for r in table.rows}
            reachable = sum(1 for r in table.rows if str(r[idx]) == lit)
        except EngineError:
            distinct, reachable = set(), None
        rows.append((matrix, col, lit, len(distinct), reachable, occ))

    rows.sort(key=lambda r: (-(r[3] or 0), r[0]))
    shown = rows if a.all else [r for r in rows if (r[3] or 0) > 1]
    print(f"   {len(shown)} of those pin a column that has MORE THAN ONE "
          f"filed value -- i.e. they make filed rows unreachable:\n")
    print(f"   {'table':40s} {'key column':26s} {'pinned':30s} "
          f"{'values':>7s} {'reach':>6s} {'of':>6s}")
    for matrix, col, lit, distinct, reachable, occ in shown:
        total = None
        try:
            total = len(book.table(matrix).rows)
        except EngineError:
            pass
        print(f"   {matrix[:40]:40s} {col[:26]:26s} {lit[:30]:30s} "
              f"{str(distinct or '?'):>7s} {str(reachable if reachable is not None else '?'):>6s} "
              f"{str(total if total is not None else '?'):>6s}")
        if a.all:
            for o in occ[:3]:
                print(f"       <- {o['file']}.{o['rule']}")

    # Per-site "reach" understates coverage when SEVERAL sites pin different
    # values of the same column. `SubStdConditionRate` is pinned to A, B, C, D
    # and E at five call sites; between them every filed condition is reachable
    # and there is no finding at all. Collapsing to (table, column) is what
    # separates that from `VandalismExclFactor`, where one site pins one class
    # code out of 161 and the other 160 are dead on that path.
    print("\n   BY COLUMN -- the union of every literal pinned at any site,")
    print("   which is what actually decides whether filed rows are dead:\n")
    by_col = defaultdict(set)
    for matrix, col, lit, distinct, reachable, occ in rows:
        by_col[(matrix, col)].add(lit)
    verdicts = []
    for (matrix, col), lits in by_col.items():
        try:
            table = book.table(matrix)
            idx = table.col(col)
            values = {str(r[idx]) for r in table.rows}
        except EngineError:
            continue
        if values:
            dead = values - lits
            verdicts.append((len(dead), len(values), matrix, col,
                             sorted(lits), sorted(dead)))
    verdicts.sort(reverse=True)
    for dead_n, total_n, matrix, col, lits, dead in verdicts:
        if dead_n == 0:
            continue
        print(f"   {matrix}.{col}")
        print(f"      pinned to {', '.join(repr(x) for x in lits[:6])}"
              + (" ..." if len(lits) > 6 else ""))
        also_live = any((matrix, pos) in live
                        for (m, c, l, d, r, o) in rows if m == matrix
                        for pos in [o[0]["pos"]])
        scope = ("from the pinned site only -- the same column is also read "
                 "live elsewhere" if also_live else
                 "from EVERY site that reads this column")
        print(f"      {dead_n} of {total_n} filed values unreachable "
              f"({100.0 * dead_n / total_n:.0f}%), {scope}")
    clean = [v for v in verdicts if v[0] == 0]
    multi = [v for v in clean if v[1] > 1]
    single = [v for v in clean if v[1] == 1]
    if clean:
        print(f"\n   {len(clean)} column(s) pin nothing away -- no finding:")
        for _, total_n, matrix, col, lits, _ in multi:
            print(f"      {matrix}.{col} -- {total_n} filed values, and the "
                  f"call sites between them pin every one")
        if single:
            print(f"      ...plus {len(single)} single-row tables whose key "
                  f"column has one filed value, so pinning it removes nothing")

    print("\n   Reading this: `values` is how many distinct values that key")
    print("   column carries in the resolved table; `reach` is how many rows")
    print("   the literal can match, out of `of`. Anything where reach << of")
    print("   is filed data that this path cannot use, by ISO's design.")

    # ------------------------------------------------- 2. branch literals
    print(f"\n2. BRANCH LITERALS -- conditions that decide a path")
    print(f"   {len(branches)} distinct (field, literal) pairs, "
          f"{sum(branches.values())} comparisons\n")
    top = branches.most_common(None if a.all else 25)
    for (fld, lit), n in top:
        print(f"   {n:5d}  {fld[:42]:42s} == {lit[:40]}")
    if not a.all and len(branches) > 25:
        print(f"\n   ... and {len(branches) - 25} more; --all lists every one")

    print("\n   These are not unreachable-row problems; they are the switches")
    print("   that select a rating path. Listed because chunk 1 exercised only")
    print("   a handful of them, and every later chunk walks the rest.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
