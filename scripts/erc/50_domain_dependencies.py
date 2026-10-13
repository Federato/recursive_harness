"""Before resolving dependent domains: how many are there, and how many does
ISO declare the dependency for?

Stage 4 validates a dependent domain against the **union** of its values -- a
deliberate safe superset, because the dependency could not be resolved. ISO
files the dependency in `Form Related Fields` (`RelatedXPath`), which was found
by applying Rule #1.

**The question that must come before the implementation is coverage.** If every
dependent domain carries a declared relationship, resolving them closes the hole
completely. If some do not, the union stays as the fallback for those and the
engine must say which -- a validator that is exact for some fields and a
superset for others, without saying which is which, is worse than one that is
always a superset.

  C1 dependent      domains whose legal set depends on another column
  C2 declared       of those, how many have a RelatedXPath
  C3 uncovered      the ones with no declared dependency -- named, not counted
  C4 dialect        every distinct RelatedXPath form, since each must resolve

Emits out/domain_dependencies.txt.
"""
from __future__ import annotations

import csv
import io
import sys
from collections import Counter, defaultdict
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
c = import_module("00_common")
rules_packages = import_module("42_node_surface").rules_packages

from gl_engine.erc.discovery import read_text                  # noqa: E402
from gl_engine.erc.tables import list_tables, parse_def        # noqa: E402

FIELDS = Path("Form Fields") / "Fields.FormField.csv"
RELATED = Path("Form Related Fields") / "RelatedFields.FormField.csv"

#: Columns that are never the dependency.
STRUCTURAL = {"StateCode", "Status", "MetadataCodes", "DisplayValue",
              "DataValue"}


def rows_of(path: Path):
    if not path.exists():
        return []
    return list(csv.DictReader(io.StringIO(read_text(path))))


def main() -> None:
    pkgs, _, _ = rules_packages()

    #: (table, column) -> domain table name, from the field declarations
    field_domain: dict[tuple[str, str], str] = {}
    #: (table, column) -> RelatedXPath
    declared: dict[tuple[str, str], str] = {}
    xpaths = Counter()
    #: domain table -> its dependency columns
    dep_cols: dict[str, tuple] = {}

    for pk in pkgs:
        for r in rows_of(pk.content / FIELDS):
            dom = (r.get("DomainTableName") or "").strip()
            if dom:
                field_domain[(r["TableName"], r["ColumnName"])] = dom
        for r in rows_of(pk.content / RELATED):
            xp = (r.get("RelatedXPath") or "").strip()
            if xp:
                declared[(r["TableName"], r["ColumnName"])] = xp
                xpaths[xp] += 1
        for name in list_tables(pk.content, "Domain"):
            if name in dep_cols:
                continue
            p = pk.content / "Domain Tables" / f"{name}Def.DomainTableDef.xml"
            if not p.exists():
                continue
            try:
                d = parse_def(p, name, "Domain")
            except Exception:                              # noqa: BLE001
                continue
            cols = tuple(x.name for x in d.key_cols + d.value_cols
                         if x.name not in STRUCTURAL)
            if cols:
                dep_cols[name] = cols

    # A field's domain is dependent when its domain table carries a column
    # that is neither structural nor the value itself.
    dependent, independent = {}, []
    for key, dom in field_domain.items():
        cols = dep_cols.get(dom) or dep_cols.get(f"Domain{dom}")
        if cols:
            dependent[key] = (dom, cols)
        else:
            independent.append(key)

    covered = {k: v for k, v in dependent.items() if k in declared}
    uncovered = {k: v for k, v in dependent.items() if k not in declared}

    L = []; A = L.append
    A("DEPENDENT DOMAINS, AND WHETHER ISO DECLARES THE DEPENDENCY")
    A("")
    A(f"    packages: {len(pkgs)}")
    A(f"    fields naming a domain table       : {len(field_domain)}")
    A("")
    A("C1  DEPENDENT DOMAINS")
    A(f"    fields whose domain carries a dependency column: {len(dependent)}")
    A(f"    fields whose domain is a plain list            : {len(independent)}")
    A("")
    A("C2  DECLARED")
    A(f"    RelatedXPath declared for               : {len(declared)} "
      f"(table, column) pairs")
    A(f"    of which are dependent domains          : {len(covered)}")
    A(f"    **coverage of dependent domains**       : {len(covered)} of "
      f"{len(dependent)}"
      + (f"  ({100 * len(covered) / len(dependent):.1f}%)" if dependent else ""))
    A("")
    A("C3  DEPENDENT BUT NOT DECLARED -- named, so the fallback is explicit")
    A(f"    {len(uncovered)} fields:")
    for (t, col), (dom, cols) in sorted(uncovered.items())[:40]:
        A(f"      {t}.{col}")
        A(f"          domain {dom} keyed by {list(cols)}")
    if len(uncovered) > 40:
        A(f"      ... and {len(uncovered) - 40} more")
    A("")
    A("C4  THE RelatedXPath DIALECT  (each must resolve)")
    A(f"    distinct forms: {len(xpaths)}")
    for k, n in xpaths.most_common():
        A(f"      {k:64s} {n}")

    (c.OUT / "domain_dependencies.txt").write_text("\n".join(L),
                                                   encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
