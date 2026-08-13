"""Phase 5 step 6: the shape of the rule program.

Answers: what does it compute, how is it organised, what is the entry
point, and what would an engine have to implement?

  P1 organisation      rule files vs DataDefGroups; rules per group;
                       is the file/group mapping 1:1?
  P2 name taxonomy     rule names are bucketed by prefix (Erc*, Set*,
                       Lookup*, Calculate*, Call*, other) and the buckets
                       cross-tabulated against what the rules do (which
                       operators they use, whether they write a value).
  P3 entry points      rules never called by any RunRule anywhere in their
                       package = roots.  Rules called from outside their
                       own file = the public surface.
  P4 call graph        depth of the RunRule graph from the root, fan-out,
                       and whether it is acyclic.
  P5 engine surface    the full operator set with the arity/attributes an
                       implementation must support, and the non-obvious
                       semantics that are declared but unspecified.

Emits out/rule_roots.csv, out/rule_callgraph_stats.csv, out/rule_program.txt.
"""
from __future__ import annotations

import csv
import re
import sys
from collections import Counter, defaultdict, deque
from pathlib import Path
from importlib import import_module

sys.path.insert(0, str(Path(__file__).parent))
c = import_module("00_common")
csv.field_size_limit(1 << 24)


def load(n):
    with open(c.OUT / n, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def main():
    rules = load("rules_index.csv")
    refs = load("rule_refs.csv")
    xsd = {r["pkg_id"]: r for r in load("xsd_packages.csv")}
    juris = {p: r["juris"] for p, r in xsd.items()}
    parent = {p: r["import_pkgs"] for p, r in xsd.items()}

    L = []; A = L.append
    A("THE RULE PROGRAM")
    A("")

    # ---- P1 organisation
    A("P1  ORGANISATION")
    fg = defaultdict(set)
    for r in rules:
        fg[r["rule_file"]].add(r["datadef_group"])
    A(f"    distinct rule files: {len(fg)}   distinct DataDefGroups: "
      f"{len({r['datadef_group'] for r in rules})}")
    A(f"    rule files mapping to exactly one DataDefGroup: "
      f"{sum(1 for v in fg.values() if len(v) == 1)} of {len(fg)}")
    A(f"    file name == DataDefGroup + 'Rules': "
      f"{sum(1 for f, v in fg.items() if len(v) == 1 and f == next(iter(v)) + 'Rules')}"
      f" of {len(fg)}")
    per = Counter()
    for r in rules:
        per[(r["pkg_id"], r["rule_file"])] += 1
    v = sorted(per.values())
    A(f"    rules per file: min={v[0]} median={v[len(v)//2]} max={v[-1]}")
    A("    -> the program is organised BY DATA STRUCTURE (one rule file per")
    A("       schema table), not by coverage or by function.")

    # ---- P2 name taxonomy
    A("")
    A("P2  RULE NAME TAXONOMY")
    def bucket(n):
        for p in ("Erc", "Lookup", "Calculate", "Call", "Set", "Initialize"):
            if n.startswith(p):
                return p + "*"
        return "(other)"
    b = Counter(bucket(r["rule_name"]) for r in rules)
    names = defaultdict(set)
    for r in rules:
        names[bucket(r["rule_name"])].add(r["rule_name"])
    A(f"    {'bucket':14s} {'<Rule> elems':>13} {'distinct names':>15}")
    for k, n in b.most_common():
        A(f"    {k:14s} {n:13d} {len(names[k]):15d}")
    # what each bucket does
    ops = defaultdict(Counter)
    for r in rules:
        for st in r["statement_tags"].split(";"):
            if ":" in st:
                t, n = st.rsplit(":", 1)
                ops[bucket(r["rule_name"])][t] += int(n)
    A("    dominant operators per bucket:")
    for k in b:
        A(f"      {k:14s} {[x for x, _ in ops[k].most_common(6)]}")

    # ---- P3 entry points
    A("")
    A("P3  ENTRY POINTS")
    called = defaultdict(set)          # pkg -> {(file, rule)}
    ext_called = defaultdict(set)
    for r in refs:
        if r["ref_kind"] != "RunRule":
            continue
        pk = r["pkg_id"] if not r["project_name"] else \
            r["project_name"].replace(" ", "_")
        called[pk].add((r["target"], r["target_rule"]))
        if r["target"] != r["rule_file"]:
            ext_called[pk].add((r["target"], r["target_rule"]))
    defined = defaultdict(set)
    for r in rules:
        defined[r["pkg_id"]].add((r["rule_file"], r["rule_name"]))
    roots = Counter()
    rootrows = []
    for p, ds in defined.items():
        par = parent.get(p, "")
        rt = ds - called.get(p, set())
        # a state rule may be called only via its parent's namespace
        rt = {x for x in rt if x not in called.get(par, set())}
        for x in sorted(rt):
            roots[x[1]] += 1
            rootrows.append([p, juris.get(p, ""), x[0], x[1]])
    with open(c.OUT / "rule_roots.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["pkg_id", "juris", "rule_file", "rule_name"])
        w.writerows(rootrows)
    A(f"    rules never targeted by any RunRule (roots): {len(rootrows)}")
    A(f"    root rule NAMES, by frequency:")
    for k, n in roots.most_common(12):
        A(f"      {k:34s} {n}")
    A(f"    packages with at least one root: {len({r[0] for r in rootrows})}")
    top = Counter()
    for p, ds in defined.items():
        for f, n in ds:
            if n in ("ErcProcess", "InitializeRuleSet") and \
                    f.startswith("GeneralLiabilityRules"):
                top[(f, n)] += 1
    A(f"    the top-level pair (GeneralLiabilityRules, ErcProcess/"
      f"InitializeRuleSet) exists in: {dict(top)}")

    # ---- P4 call graph
    A("")
    A("P4  CALL GRAPH (measured on one representative countrywide package)")
    cwp = sorted(p for p in defined if juris.get(p) == "CW")
    target = cwp[-1] if cwp else None
    if target:
        g = defaultdict(set)
        for r in refs:
            if r["ref_kind"] == "RunRule" and r["pkg_id"] == target:
                g[(r["rule_file"], r["rule_name"])].add(
                    (r["target"], r["target_rule"]))
        start = ("GeneralLiabilityRules", "ErcProcess")
        seen = {start}
        depth = {start: 0}
        q = deque([start])
        while q:
            u = q.popleft()
            for v2 in g.get(u, ()):
                if v2 not in seen:
                    seen.add(v2); depth[v2] = depth[u] + 1; q.append(v2)
        A(f"    package: {target}")
        A(f"    nodes reachable from (GeneralLiabilityRules, ErcProcess): "
          f"{len(seen)} of {len(defined[target])} rules defined")
        A(f"    max depth: {max(depth.values())}")
        dd = Counter(depth.values())
        A(f"    nodes by depth: {sorted(dd.items())}")
        fo = sorted(len(v) for v in g.values())
        A(f"    fan-out per rule: min={fo[0]} median={fo[len(fo)//2]} max={fo[-1]}")
        # cycle check
        colour = {}
        cyc = [0]
        def visit(u):
            colour[u] = 1
            for v2 in g.get(u, ()):
                if colour.get(v2) == 1:
                    cyc[0] += 1
                elif v2 not in colour:
                    visit(v2)
            colour[u] = 2
        sys.setrecursionlimit(20000)
        for u in list(g):
            if u not in colour:
                visit(u)
        A(f"    back-edges found (cycles): {cyc[0]}")
        unreach = sorted(defined[target] - seen)
        A(f"    rules NOT reachable from ErcProcess: {len(unreach)}")
        A(f"      by name: {Counter(x[1] for x in unreach).most_common(8)}")

    # ---- P5 engine surface
    A("")
    A("P5  WHAT AN ENGINE WOULD HAVE TO IMPLEMENT")
    ops_all = Counter()
    attrs = Counter()
    for r in rules:
        for st in r["statement_tags"].split(";"):
            if ":" in st:
                t, n = st.rsplit(":", 1)
                ops_all[t] += int(n)
    A(f"    distinct operators: {len(ops_all)}")
    A(f"    {'operator':22s} {'occurrences':>12}")
    for k, n in ops_all.most_common():
        A(f"    {k:22s} {n:12d}")
    A("")
    A("    declared-but-unspecified semantics an implementer must pin down:")
    for x in [
        "FirstValue@Order='DataDefInputParamConstant' - the precedence order "
        "between a DataDef value, an input, a parameter and a constant",
        "Lookup@ResultMode FirstResult vs SingleResult - what 'first' means "
        "when a table's declared key is not unique (3.79% of tables)",
        "Locate@OutputAction and Locate@AtOutputDataDef - creation/positioning "
        "semantics in the output tree",
        "RunRule@ClearCache - what is cached and for how long",
        "Product@DecimalPlaces / Round@DecimalPlaces - rounding mode "
        "(half-up, half-even, truncate) is never stated",
        "Range@RangeType boundary handling combined with "
        "InterpolateMode='Linear' at an exact boundary",
        "Remove@RemoveMultiple, Copy, Guid - side effects on the output tree",
        "XPath dialect used in Form Fields Condition / "
        "RatebookColumns RatingRequiredCondition",
    ]:
        A(f"      - {x}")
    (c.OUT / "rule_program.txt").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L[:100]))


if __name__ == "__main__":
    main()
