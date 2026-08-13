"""Phase 3 verification: resolve every rule cross-reference against the
artifacts actually present in the corpus.

Inputs: out/rule_refs.csv, out/table_defs.csv, out/xsd_packages.csv,
        out/rules_index.csv

For each package P we build the resolution scope:
   local  = tables / rule files inside P
   parent = tables / rule files inside the countrywide package that P's
            .xsd xs:import names (from xsd_packages.import_pkgs)

Then every <Lookup MatrixFromConstant="T"> is checked to resolve to a rate
or domain table, and every <RunRule FileName="F" Rule="R"> to a rule.
A RunRule/Lookup carrying ProjectName="GL CW yyyymmdd Vnn" is resolved
against that named package instead.

Emits:
  out/ref_resolution.csv   per (package, ref kind, target) whether it
                           resolved and where (local / parent / named / none)
  out/ref_resolution.txt   totals, unresolved list, and whether the
                           ProjectName values agree with the xs:import.
"""
from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path
from importlib import import_module

sys.path.insert(0, str(Path(__file__).parent))
c = import_module("00_common")


def load(n):
    with open(c.OUT / n, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def main():
    tabs = load("table_defs.csv")
    xsd = {r["pkg_id"]: r for r in load("xsd_packages.csv")}
    rules = load("rules_index.csv")
    refs = load("rule_refs.csv")

    tables_in = defaultdict(set)          # pkg_id -> {table names}
    for r in tabs:
        tables_in[r["pkg_id"]].add(r["table"])
    rulefiles_in = defaultdict(set)       # pkg_id -> {(file, rule)}
    for r in rules:
        rulefiles_in[r["pkg_id"]].add((r["rule_file"], r["rule_name"]))

    def pid(project_name):
        # "GL CW 20231201 V02" -> "GL_CW_20231201_V02"
        return project_name.replace(" ", "_") if project_name else ""

    out = []
    tally = Counter()
    unresolved = Counter()
    import_disagree = Counter()
    for r in refs:
        p = r["pkg_id"]
        parent = xsd.get(p, {}).get("import_pkgs", "")
        named = pid(r["project_name"])
        if named and parent and named != parent:
            import_disagree[(p, named, parent)] += 1
        scope = []
        if named:
            scope.append(("named:" + named, named))
        else:
            scope.append(("local", p))
            if parent:
                scope.append(("parent:" + parent, parent))
        where = "UNRESOLVED"
        for label, target_pkg in scope:
            if r["ref_kind"] == "Lookup":
                ok = r["target"] in tables_in.get(target_pkg, ())
            else:
                ok = (r["target"], r["target_rule"]) in rulefiles_in.get(target_pkg, ())
            if ok:
                where = label.split(":")[0]
                break
        # fall back: a ProjectName ref may still be satisfied locally
        if where == "UNRESOLVED" and named:
            if r["ref_kind"] == "Lookup":
                ok = r["target"] in tables_in.get(p, ())
            else:
                ok = (r["target"], r["target_rule"]) in rulefiles_in.get(p, ())
            if ok:
                where = "local-fallback"
        tally[(r["ref_kind"], where)] += 1
        if where == "UNRESOLVED":
            unresolved[(r["ref_kind"], r["target"], r["target_rule"], named or "-")] += 1
        out.append((p, r["juris"], r["ref_kind"], r["target"], r["target_rule"],
                    named, where))

    with open(c.OUT / "ref_resolution.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["pkg_id", "juris", "ref_kind", "target", "target_rule",
                    "project_pkg", "resolved_where"])
        w.writerows(out)

    L = []; A = L.append
    A(f"references checked: {len(out)}")
    for k, n in sorted(tally.items()):
        A(f"  {k[0]:10s} {k[1]:22s} {n}")
    tot = len(out)
    unres = sum(n for k, n in tally.items() if k[1] == "UNRESOLVED")
    A(f"resolution rate: {(tot-unres)/tot*100:.3f}%  ({unres} unresolved)")
    A("")
    A(f"distinct unresolved targets: {len(unresolved)}")
    for k, n in unresolved.most_common(40):
        A(f"  {n:6d}  {k[0]} target={k[1]} rule={k[2]} project={k[3]}")
    A("")
    A(f"ProjectName disagreeing with the package's xs:import: "
      f"{len(import_disagree)} distinct (pkg,named,import) combinations")
    for k, n in import_disagree.most_common(20):
        A(f"  {n:6d}  {k[0]}  ProjectName={k[1]}  xs:import={k[2]}")
    (c.OUT / "ref_resolution.txt").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L[:70]))


if __name__ == "__main__":
    main()
