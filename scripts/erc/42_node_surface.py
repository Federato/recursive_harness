"""Stage 2 step 1: the full surface of the rule language, from source.

The build plan quotes "58 node types (54 executable)"; the P5 census in
`23_rule_program.py` enumerates 52 operators.  Neither number can be trusted
for the evaluation contract, because P5 counted `statement_tags`, which was
itself derived rather than read.  This script reads every `*.Rule.xml` in the
corpus and enumerates the language directly.

For each node type it records:

  N1 occurrence        total count, and how many packages / editions carry it
  N2 attributes        every attribute name, its cardinality, and its value
                       domain in full when small enough to be a domain
  N3 children          which node types appear inside it, how many, and in
                       what position -- the arity an interpreter must accept
  N4 parents           where the node is legal, which is what says whether it
                       is a statement, a value, or a clause of something else
  N5 text              whether the node carries a text payload

Every count is "n of N" with N enumerated here, not assumed.

Emits out/node_surface.csv, out/node_attrs.csv, out/node_children.csv,
out/node_surface.txt.
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

#: Above this many distinct values an attribute is an open field (a name, a
#: path, a number), not a domain.  Below it, the full set is worth recording
#: because the interpreter has to switch on it.
DOMAIN_MAX = 60

#: Elements that carry the document, not the language.
STRUCTURAL = {"Rules", "MetaData", "MetaDataCode", "Rule"}


def rules_packages() -> tuple[list, int, list[str]]:
    """Every package with a Rules directory, de-duplicated by package id.

    Five packages are unpacked twice -- once bare, once under a
    `_MachineReadableContent` wrapper -- and the pairs are byte-identical.
    Counting both inflates every occurrence figure by those five packages'
    worth, which is precisely the error this project keeps making. The engine
    de-duplicates the same way (`gl_engine/erc/discovery.py`, first path wins
    over a sorted walk), so the two populations agree by construction.
    """
    seen: dict[str, object] = {}
    dupes: list[str] = []
    total = 0
    for p in c.find_packages():
        if not (p.content / "Rules").is_dir():
            continue
        total += 1
        if p.pkg_id in seen:
            dupes.append(p.pkg_id)
            continue
        seen[p.pkg_id] = p
    return list(seen.values()), total, dupes


def main() -> None:
    pkgs, n_dirs, dupes = rules_packages()
    print(f"package directories with a Rules directory: {n_dirs}")
    print(f"distinct packages after de-duplication      : {len(pkgs)}")
    print(f"duplicate directories skipped               : {len(dupes)} "
          f"{sorted(set(dupes))}")

    occ = Counter()                                  # tag -> occurrences
    in_pkg = defaultdict(set)                        # tag -> {pkg_id}
    attrs = defaultdict(lambda: defaultdict(Counter))  # tag -> attr -> values
    attr_occ = defaultdict(Counter)                  # tag -> attr -> count
    kids = Counter()                                 # (parent, child) -> n
    kid_n = defaultdict(list)                        # parent -> [child count]
    kid_pos = defaultdict(Counter)                   # (parent, child) -> pos
    parents = defaultdict(Counter)                   # tag -> parent -> n
    has_text = Counter()
    roots = Counter()
    n_files = 0
    n_bad = 0

    for pk in pkgs:
        pid = pk.pkg_id
        for f in sorted((pk.content / "Rules").glob("*.Rule.xml")):
            n_files += 1
            try:
                root = ET.fromstring(c.read_text(f))
            except ET.ParseError:
                n_bad += 1
                continue
            roots[c.lname(root.tag)] += 1
            stack = [(root, None)]
            while stack:
                el, parent = stack.pop()
                tag = c.lname(el.tag)
                occ[tag] += 1
                in_pkg[tag].add(pid)
                if el.text and el.text.strip():
                    has_text[tag] += 1
                for k, v in el.attrib.items():
                    k = c.lname(k)
                    attr_occ[tag][k] += 1
                    d = attrs[tag][k]
                    # stop growing a domain once it is plainly an open field,
                    # but keep counting how many distinct values were seen
                    if len(d) <= DOMAIN_MAX:
                        d[v] += 1
                    else:
                        d["\x00OVERFLOW"] += 1
                if parent is not None:
                    parents[tag][parent] += 1
                ch = list(el)
                kid_n[tag].append(len(ch))
                for i, k2 in enumerate(ch):
                    kt = c.lname(k2.tag)
                    kids[(tag, kt)] += 1
                    kid_pos[(tag, kt)][min(i, 9)] += 1
                    stack.append((k2, tag))

    total_nodes = sum(occ.values())
    exec_tags = sorted(t for t in occ if t not in STRUCTURAL)
    all_tags = sorted(occ)

    # ---- per-node CSV
    with open(c.OUT / "node_surface.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["node", "kind", "occurrences", "pct_of_all",
                    "packages", "min_children", "max_children",
                    "median_children", "distinct_child_types",
                    "carries_text", "distinct_attrs"])
        for t in all_tags:
            n = sorted(kid_n[t])
            w.writerow([
                t,
                "structural" if t in STRUCTURAL else "executable",
                occ[t], f"{100 * occ[t] / total_nodes:.4f}",
                len(in_pkg[t]), n[0], n[-1], n[len(n) // 2],
                len({k[1] for k in kids if k[0] == t}),
                has_text[t], len(attr_occ[t]),
            ])

    # ---- attribute CSV
    with open(c.OUT / "node_attrs.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["node", "attr", "occurrences", "pct_of_node",
                    "distinct_values", "is_domain", "values"])
        for t in all_tags:
            for a, n in sorted(attr_occ[t].items(),
                               key=lambda x: -x[1]):
                d = attrs[t][a]
                over = "\x00OVERFLOW" in d
                dv = "open field" if over else str(len(d))
                vals = "" if over else "|".join(
                    f"{k}={v}" for k, v in sorted(d.items(), key=lambda x: -x[1]))
                w.writerow([t, a, n, f"{100 * n / occ[t]:.2f}",
                            dv, "no" if over else "yes", vals[:4000]])

    # ---- child CSV
    with open(c.OUT / "node_children.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["parent", "child", "occurrences", "first_position_hist"])
        for (p, ch2), n in sorted(kids.items(), key=lambda x: (-x[1],)):
            hist = ",".join(f"{k}:{v}" for k, v in sorted(kid_pos[(p, ch2)].items()))
            w.writerow([p, ch2, n, hist])

    # ---- report
    L = []; A = L.append
    A("THE RULE LANGUAGE, ENUMERATED FROM SOURCE")
    A("")
    A(f"    package directories: {n_dirs}")
    A(f"    packages read      : {len(pkgs)}  (after de-duplicating "
      f"{len(dupes)} byte-identical re-unpacks)")
    A(f"    rule files read    : {n_files}   unparseable: {n_bad}")
    A(f"    element occurrences: {total_nodes}")
    A(f"    document roots     : {dict(roots)}")
    A("")
    A("N0  RECONCILIATION OF THE NODE COUNT")
    A(f"    distinct element names in the corpus : {len(all_tags)}")
    A(f"      of which structural (document, not language): {len(STRUCTURAL & set(all_tags))}"
      f"  {sorted(STRUCTURAL & set(all_tags))}")
    A(f"      of which language nodes                     : {len(exec_tags)}")
    A("    The build plan's '58 node types (54 executable)' and P5's '52")
    A("    operators' are both restatements of derived data; the figures above")
    A("    are read from the XML itself and supersede them.")
    A("")
    A("N1  OCCURRENCE  (language nodes, descending)")
    A(f"    {'node':24s} {'occurrences':>12} {'% all':>8} {'pkgs':>6} "
      f"{'children':>10}")
    cum = 0
    exec_total = sum(occ[t] for t in exec_tags)
    for t in sorted(exec_tags, key=lambda x: -occ[x]):
        n = sorted(kid_n[t])
        cum += occ[t]
        A(f"    {t:24s} {occ[t]:12d} {100 * occ[t] / exec_total:7.3f}% "
          f"{len(in_pkg[t]):6d} {n[0]}..{n[-1]:<8}")
    A("")
    A("    cumulative coverage by rank:")
    ranked = sorted(exec_tags, key=lambda x: -occ[x])
    run = 0
    for i, t in enumerate(ranked, 1):
        run += occ[t]
        if i in (5, 10, 15, 20, 25, 30, 40, len(ranked)):
            A(f"      top {i:3d}: {100 * run / exec_total:6.2f}%")
    A("")
    A("N2  THE LONG TAIL  (fewer than 500 occurrences)")
    tail = [t for t in ranked if occ[t] < 500]
    A(f"    {len(tail)} of {len(exec_tags)} language nodes:")
    for t in tail:
        A(f"      {t:24s} {occ[t]:8d}  in {len(in_pkg[t])} packages")
    A("")
    A("N3  ATTRIBUTES THAT ARE DOMAINS  (an interpreter must switch on these)")
    for t in ranked:
        rows = []
        for a, n in sorted(attr_occ[t].items(), key=lambda x: -x[1]):
            d = attrs[t][a]
            if "\x00OVERFLOW" in d:
                continue
            if len(d) > 12:
                continue
            rows.append((a, n, sorted(d.items(), key=lambda x: -x[1])))
        if not rows:
            continue
        A(f"    {t}")
        for a, n, vals in rows:
            pct = 100 * n / occ[t]
            shown = ", ".join(f"{k or '(empty)'}({v})" for k, v in vals[:12])
            A(f"      @{a:22s} on {pct:6.2f}% of nodes -> {shown}")
    A("")
    A("N4  WHERE EACH NODE IS LEGAL  (its parents in the corpus)")
    for t in ranked:
        ps = sorted(parents[t].items(), key=lambda x: -x[1])
        shown = ", ".join(f"{k}({v})" for k, v in ps[:8])
        more = "" if len(ps) <= 8 else f"  (+{len(ps) - 8} more)"
        A(f"    {t:24s} <- {shown}{more}")
    A("")
    A("N5  NODES CARRYING TEXT")
    for t in ranked:
        if has_text[t]:
            A(f"    {t:24s} {has_text[t]} of {occ[t]} occurrences")

    (c.OUT / "node_surface.txt").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L[:80]))
    print(f"\n[wrote node_surface.txt, node_surface.csv, node_attrs.csv, "
          f"node_children.csv to {c.OUT}]")


if __name__ == "__main__":
    main()
