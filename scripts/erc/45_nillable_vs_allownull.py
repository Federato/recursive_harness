"""Stage 2 step 4: who decides whether a read may return null?

The evaluation contract's first draft said `Value` without `@AllowNullReturn` is
an error if the path resolves to nothing, making the RULE attribute the sole
authority on nullability. That was inferred from the attribute's name, not
measured -- and it stopped a real ISO payload dead on `TRIAExpirationDate`,
which ISO's own rules read with a bare `Value`.

The competing reading is that the **DataDef schema** is the authority:
`nillable="true"` says this element may legitimately be absent, and
`@AllowNullReturn` is something else.

This settles it by counting, over every package:

  V1  how many DataDef elements are declared nillable
  V2  of the paths read by a BARE `Value` (no @AllowNullReturn), how many
      address a nillable element -- if that is most of them, the schema is the
      authority and the first draft was wrong
  V3  of the paths read WITH @AllowNullReturn, how many are nillable -- if the
      attribute tracked nillability it would be redundant, so a low overlap
      says it means something else

Emits out/nillable_vs_allownull.txt.
"""
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
c = import_module("00_common")
rules_packages = import_module("42_node_surface").rules_packages

#: <xs:element name="TRIAExpirationDate" nillable="true" type="xs:dateTime" />
_ELEM = re.compile(r'<xs:element\s+name="([^"]+)"([^>]*)>')


def nillable_names(pkg) -> tuple[set, set]:
    """(every declared element, those declared nillable) for one package."""
    every, nil = set(), set()
    d = pkg.content / "DataDefs"
    if not d.is_dir():
        return every, nil
    for f in d.glob("*.xsd"):
        for name, attrs in _ELEM.findall(c.read_text(f)):
            every.add(name)
            if 'nillable="true"' in attrs:
                nil.add(name)
    return every, nil


def leaf(path: str) -> str:
    """The element a path addresses -- the last non-axis step."""
    for step in reversed([s for s in path.split("/") if s not in ("", "..", "*", ".")]):
        return step
    return ""


def main() -> None:
    pkgs, _, _ = rules_packages()

    tot_elems = tot_nil = 0
    bare = Counter()          # 'nillable' | 'not nillable' | 'undeclared'
    allowed = Counter()
    bare_examples, allowed_examples = Counter(), Counter()

    for pkg in pkgs:
        every, nil = nillable_names(pkg)
        tot_elems += len(every)
        tot_nil += len(nil)
        rdir = pkg.content / "Rules"
        if not rdir.is_dir():
            continue
        for f in rdir.glob("*.Rule.xml"):
            for el in ET.fromstring(c.read_text(f)).iter():
                if c.lname(el.tag) != "Value":
                    continue
                path = el.attrib.get("FromDataDef")
                if not path:
                    continue                       # a @FromParam read
                nm = leaf(path)
                if nm in nil:
                    bucket = "nillable"
                elif nm in every:
                    bucket = "not nillable"
                else:
                    bucket = "undeclared in this package"
                if el.attrib.get("AllowNullReturn") == "true":
                    allowed[bucket] += 1
                    allowed_examples[nm] += 1
                else:
                    bare[bucket] += 1
                    bare_examples[nm] += 1

    L = []; A = L.append
    A("NILLABLE (schema) vs @AllowNullReturn (rule) -- who decides?")
    A("")
    A(f"    packages: {len(pkgs)}")
    A("")
    A("V1  DECLARED ELEMENTS")
    A(f"    element declarations across all DataDefs : {tot_elems}")
    A(f"    of which nillable=\"true\"                 : {tot_nil} "
      f"({100 * tot_nil / max(1, tot_elems):.2f}%)")
    A("")
    A("V2  BARE `Value` READS  (no @AllowNullReturn)")
    tb = sum(bare.values())
    for k, n in bare.most_common():
        A(f"    {k:28s} {n:8d}  ({100 * n / max(1, tb):5.2f}%)")
    A(f"    total {tb}")
    A("")
    A("V3  READS CARRYING @AllowNullReturn=\"true\"")
    ta = sum(allowed.values())
    for k, n in allowed.most_common():
        A(f"    {k:28s} {n:8d}  ({100 * n / max(1, ta):5.2f}%)")
    A(f"    total {ta}")
    A("")
    A("V4  MOST-READ PATHS, BARE")
    for k, n in bare_examples.most_common(10):
        A(f"    {k:44s} {n}")
    A("")
    A("V5  MOST-READ PATHS, WITH @AllowNullReturn")
    for k, n in allowed_examples.most_common(10):
        A(f"    {k:44s} {n}")

    (c.OUT / "nillable_vs_allownull.txt").write_text("\n".join(L),
                                                     encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
