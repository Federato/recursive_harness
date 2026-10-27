"""Stage 2 step 2: the Default block -- the program's true entry point.

`42_node_surface.py` found two language nodes that every prior census missed,
`Default` and `DateAdd`, because `Default` is a child of the document root
`Rules` and not of `Rule`.  Every census walked `Rule` elements.

That matters more than a count.  P3 of `23_rule_program.py` derived the entry
point as `(GeneralLiabilityRules, ErcProcess)` by finding rules no `RunRule`
targets.  `ErcProcess` is the third thing the `Default` block calls.  An
interpreter entered at `ErcProcess` skips whatever the block does first --
silently, and with a complete-looking result.

So this script asks, of every package rather than of one:

  D1 where          which file carries `Default`, and do any carry two
  D2 what it seeds  every ToDataDef written before any rule runs
  D3 what it calls  the RunRule sequence, in order, and what it iterates
  D4 how it varies  countrywide vs state, and across editions

Emits out/default_blocks.csv and out/default_block.txt.
"""
from __future__ import annotations

import csv
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
c = import_module("00_common")
rules_packages = import_module("42_node_surface").rules_packages


def summarise(el) -> tuple[list[str], list[str], list[str]]:
    """Return (seeds, calls, iterates) for one Default element."""
    seeds, calls, iters = [], [], []
    for n in el.iter():
        t = c.lname(n.tag)
        to = n.attrib.get("ToDataDef")
        if to:
            if t == "Constant":
                seeds.append(f"{to}={(n.text or '').strip()}")
            else:
                seeds.append(f"{to}<-{t}")
        if t == "RunRule":
            calls.append(f"{n.attrib.get('FileName', '?')}."
                         f"{n.attrib.get('Rule', '?')}"
                         f"{'!' if n.attrib.get('ClearCache') == 'true' else ''}")
        if t == "ForEach":
            iters.append(n.attrib.get("AtDataDef", "?"))
    return seeds, calls, iters


def main() -> None:
    pkgs, n_dirs, dupes = rules_packages()
    rows = []
    per_pkg = Counter()
    files = Counter()
    seed_shapes = Counter()
    call_shapes = Counter()
    iter_shapes = Counter()

    for pk in pkgs:
        for f in sorted((pk.content / "Rules").glob("*.Rule.xml")):
            try:
                root = ET.fromstring(c.read_text(f))
            except ET.ParseError:
                continue
            for el in root:
                if c.lname(el.tag) != "Default":
                    continue
                seeds, calls, iters = summarise(el)
                per_pkg[pk.pkg_id] += 1
                files[f.name] += 1
                seed_shapes["; ".join(seeds)] += 1
                call_shapes[" -> ".join(calls)] += 1
                iter_shapes["; ".join(iters)] += 1
                rows.append([pk.pkg_id, pk.juris, pk.edition, f.name,
                             "; ".join(seeds), " -> ".join(calls),
                             "; ".join(iters)])

    with open(c.OUT / "default_blocks.csv", "w", newline="",
              encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["pkg_id", "juris", "edition", "file", "seeds", "calls",
                    "iterates"])
        w.writerows(rows)

    L = []; A = L.append
    A("THE Default BLOCK -- THE PROGRAM'S TRUE ENTRY POINT")
    A("")
    A(f"    package directories        : {n_dirs}")
    A(f"    packages read              : {len(pkgs)}  (after de-duplicating "
      f"{len(dupes)})")
    A(f"    Default blocks found       : {len(rows)}")
    A(f"    packages carrying at least one: {len(per_pkg)} of {len(pkgs)}")
    A(f"    packages carrying more than one: "
      f"{sum(1 for v in per_pkg.values() if v > 1)}")
    miss = [p.pkg_id for p in pkgs if per_pkg[p.pkg_id] == 0]
    A(f"    packages carrying NONE     : {len(miss)}  {sorted(set(miss))[:12]}")
    A("")
    A("D1  WHICH FILE CARRIES IT")
    for k, n in files.most_common():
        A(f"    {k:44s} {n}")
    A("")
    A("D2  WHAT IT SEEDS BEFORE ANY RULE RUNS")
    A(f"    distinct seed shapes: {len(seed_shapes)}")
    for k, n in seed_shapes.most_common(10):
        A(f"    [{n:4d} packages] {k}")
    A("")
    A("D3  WHAT IT CALLS, IN ORDER")
    A(f"    distinct call shapes: {len(call_shapes)}   (! = ClearCache)")
    for k, n in call_shapes.most_common(10):
        A(f"    [{n:4d} packages] {k}")
    A("")
    A("D4  WHAT IT ITERATES")
    A(f"    distinct iteration shapes: {len(iter_shapes)}")
    for k, n in iter_shapes.most_common(10):
        A(f"    [{n:4d} packages] {k}")
    A("")
    A("D5  VARIATION BY JURISDICTION")
    by_j = defaultdict(set)
    for pid, j, ed, fn, s, ca, it in rows:
        by_j[j].add(s)
    multi = {j: v for j, v in by_j.items() if len(v) > 1}
    A(f"    jurisdictions whose seed shape changed across editions: "
      f"{len(multi)} of {len(by_j)}")
    for j in sorted(multi):
        A(f"      {j}: {len(multi[j])} distinct shapes")

    (c.OUT / "default_block.txt").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
