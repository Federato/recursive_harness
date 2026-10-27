"""Stage 6 found a hole in stage 2's path dialect: the `ancestor::` axis.

Asking the UI for *"premiums per coverage and per subline"* -- a deliverable the
plan named -- exposed that we write no statistical codes at all, because
`ErcSetStatisticalCodes` is guarded by

    <rul:Exist AtInputDataDef="ancestor::MasterGLCW/Policy" />

and `interp/tree.py` implements `..`, `.`, `*`, `name` and `name[n]` but **not
`ancestor::`**. An unimplemented axis matches nothing, `Exist` returns false, and
the whole block is silently skipped. No error, no warning -- the premium is
right and the statistical codes ISO publishes are simply absent.

Before fixing it, enumerate: **which axes appear, where, and how many
statements does each guard?**

  A1 axes        every `axis::` form in every path attribute
  A2 targets     what each axis names
  A3 blast       how many rule statements sit inside a test that uses one
  A4 root        what the document root is actually called, since
                 `ancestor::MasterGLCW` names it

Emits out/path_axes.txt.
"""
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
c = import_module("00_common")
rules_packages = import_module("42_node_surface").rules_packages

PATH_ATTRS = ("FromDataDef", "AtDataDef", "AtInputDataDef", "AtOutputDataDef",
              "ToDataDef")
AXIS = re.compile(r"(\w+)::")


def main() -> None:
    pkgs, _, _ = rules_packages()

    axes = Counter()
    forms = Counter()
    by_attr = defaultdict(Counter)
    by_node = Counter()
    guarded = Counter()
    masters = Counter()

    for pk in pkgs:
        d = pk.content / "DataDefs"
        if d.is_dir():
            for f in d.glob("*.xsd"):
                masters[f.name.split(".")[0]] += 1

        for f in (pk.content / "Rules").glob("*.Rule.xml"):
            root = ET.fromstring(c.read_text(f))
            for el in root.iter():
                tag = c.lname(el.tag)
                for a in PATH_ATTRS:
                    v = el.attrib.get(a)
                    if not v or "::" not in v:
                        continue
                    m = AXIS.search(v)
                    axis = m.group(1) if m else "?"
                    axes[axis] += 1
                    forms[v] += 1
                    by_attr[a][axis] += 1
                    by_node[tag] += 1
                    # How much rides on it: the statements inside the Then of
                    # the If whose Test contains this node.
                    guarded[axis] += sum(1 for _ in el.iter())

    L = []; A = L.append
    A("PATH AXES -- THE DIALECT STAGE 2 DID NOT IMPLEMENT")
    A("")
    A(f"    packages: {len(pkgs)}")
    A("")
    A("A1  AXES IN USE")
    for k, n in axes.most_common():
        A(f"    {k + '::':16s} {n}")
    A(f"    total paths carrying an axis: {sum(axes.values())}")
    A("")
    A("A2  THE FULL FORMS")
    A(f"    distinct: {len(forms)}")
    for k, n in forms.most_common(20):
        A(f"      {k:52s} {n}")
    A("")
    A("A3  WHICH NODES USE THEM")
    for k, n in by_node.most_common():
        A(f"    {k:16s} {n}")
    A("    by attribute:")
    for a, cnt in by_attr.items():
        A(f"      {a:18s} {dict(cnt)}")
    A("")
    A("A4  THE DOCUMENT ROOT")
    A("    `ancestor::MasterGLCW` names the root element, so what is it called?")
    A(f"    distinct master DataDef names: {len(masters)}")
    for k, n in masters.most_common(8):
        A(f"      {k:24s} in {n} packages")

    (c.OUT / "path_axes.txt").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
