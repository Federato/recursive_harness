"""Phase 2: characterise the Rules/*.Rule.xml element model and inventory
every rule.

Emits:
  out/rules_index.csv    one row per <Rule>: package, rule file, rule Name,
                         DataDefGroup, MetadataCodes, depth of its body,
                         number of child statement nodes, whether it
                         references rate tables / domain tables / other
                         projects, and the distinct statement tags it uses.
  out/rule_refs.csv      one row per cross-reference emitted by a rule:
                         RunRule (FileName/Rule/ProjectName), RateTable
                         lookup, DomainTable lookup - so the call graph and
                         the rule -> table usage graph are queryable.
  out/rules_report.txt   full element vocabulary with counts, attribute
                         vocabulary per element, an assessment of whether
                         the content is executable logic or prose (measured
                         as: proportion of text content vs elements), and
                         the ProjectName cross-edition reference summary.
"""
from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict
from multiprocessing import Pool
from pathlib import Path
from importlib import import_module

sys.path.insert(0, str(Path(__file__).parent))
c = import_module("00_common")

REF_ATTRS = {
    "RunRule": ("FileName", "Rule", "ProjectName"),
    "RateTable": ("Name", "ProjectName"),
    "DomainTable": ("Name", "ProjectName"),
    "Lookup": ("Name", "ProjectName"),
}


def depth_of(el, d=0):
    ch = list(el)
    return d if not ch else max(depth_of(x, d + 1) for x in ch)


def scan(a):
    pkg_id, juris, content = a
    d = Path(content) / "Rules"
    rows, refs = [], []
    tags = Counter()
    attrs = Counter()
    text_chars = 0
    elem_count = 0
    probs = []
    if not d.is_dir():
        return rows, refs, tags, attrs, 0, 0, [f"NORULES {pkg_id}"]
    for f in sorted(d.iterdir()):
        if not f.name.endswith(".Rule.xml"):
            continue
        try:
            root = c.parse_xml(f)
        except Exception as e:
            probs.append(f"XMLFAIL {pkg_id} {f.name}: {e}")
            continue
        fname = f.name[: -len(".Rule.xml")]
        for el in root.iter():
            ln = c.lname(el.tag)
            tags[ln] += 1
            elem_count += 1
            for k in el.attrib:
                attrs[f"{ln}@{k}"] += 1
            if el.text and el.text.strip():
                text_chars += len(el.text.strip())
        for r in root:
            if c.lname(r.tag) != "Rule":
                continue
            stags = Counter()
            n = 0
            for el in r.iter():
                ln = c.lname(el.tag)
                if el is not r:
                    stags[ln] += 1
                    n += 1
                if ln == "RunRule":
                    refs.append((pkg_id, juris, fname, r.get("Name", ""), ln,
                                 el.get("FileName", ""), el.get("Rule", ""),
                                 el.get("ProjectName", "")))
                elif ln == "Lookup":
                    # MatrixFromConstant is the table name; MatrixDef is
                    # "<table>Def"; MatrixCol names the column read.
                    refs.append((pkg_id, juris, fname, r.get("Name", ""), ln,
                                 el.get("MatrixFromConstant", ""),
                                 el.get("MatrixCol", ""),
                                 el.get("ProjectName", "")))
            rows.append((pkg_id, juris, fname, r.get("Name", ""),
                         r.get("DataDefGroup", ""), r.get("MetadataCodes", ""),
                         depth_of(r), n,
                         ";".join(f"{k}:{v}" for k, v in sorted(stags.items()))))
    return rows, refs, tags, attrs, text_chars, elem_count, probs


def main():
    pkgs = c.find_packages()
    args = [(p.pkg_id, p.juris, str(p.content)) for p in pkgs]
    allrows, allrefs = [], []
    tags, attrs = Counter(), Counter()
    tc = ec = 0
    probs = []
    with Pool() as pool:
        for r, rf, t, a, x, y, p in pool.imap_unordered(scan, args, chunksize=4):
            allrows.extend(r); allrefs.extend(rf)
            tags.update(t); attrs.update(a); tc += x; ec += y
            probs.extend(p)

    with open(c.OUT / "rules_index.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["pkg_id", "juris", "rule_file", "rule_name", "datadef_group",
                    "metadata_codes", "body_depth", "n_nodes", "statement_tags"])
        w.writerows(allrows)
    with open(c.OUT / "rule_refs.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["pkg_id", "juris", "rule_file", "rule_name", "ref_kind",
                    "target", "target_rule", "project_name"])
        w.writerows(allrefs)

    L = []; A = L.append
    A(f"rule files scanned: {len({(r[0], r[2]) for r in allrows})}")
    A(f"<Rule> elements: {len(allrows)}")
    A(f"distinct rule Names: {len({r[3] for r in allrows})}")
    A(f"distinct rule file names: {len({r[2] for r in allrows})}")
    A(f"DataDefGroup distinct: {len({r[4] for r in allrows})}")
    A(f"total XML elements in Rules: {ec}")
    A(f"total non-whitespace text characters in Rules: {tc}  "
      f"({tc/max(ec,1):.2f} chars per element)")
    A(f"max body depth: {max(r[6] for r in allrows)}  "
      f"median: {sorted(r[6] for r in allrows)[len(allrows)//2]}")
    A("")
    A("RULE ELEMENT VOCABULARY (tag -> occurrences)")
    for t, n in tags.most_common():
        A(f"  {t:26s} {n}")
    A("")
    A("ATTRIBUTE VOCABULARY (top 80)")
    for t, n in attrs.most_common(80):
        A(f"  {t:40s} {n}")
    A("")
    A(f"CROSS REFERENCES: {len(allrefs)}")
    A(f"  by kind: {Counter(r[4] for r in allrefs).most_common()}")
    A("  ProjectName values (cross-package rule/table references):")
    for p, n in Counter(r[7] for r in allrefs if r[7]).most_common(20):
        A(f"    {p:26s} {n}")
    A(f"  refs with no ProjectName (same-package): "
      f"{sum(1 for r in allrefs if not r[7])}")
    A("")
    A("MOST-REFERENCED RATE TABLES (by distinct package x table)")
    rt = Counter(r[5] for r in allrefs if r[4] == "RateTable")
    for t, n in rt.most_common(20):
        A(f"  {t:50s} {n}")
    A("")
    A("MetadataCodes on <Rule> (top 25)")
    for t, n in Counter(r[5] for r in allrows).most_common(25):
        A(f"  {t:40s} {n}")
    A("")
    A(f"PROBLEMS: {len(probs)}")
    for p in probs[:40]:
        A("  " + p)
    (c.OUT / "rules_report.txt").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L[:110]))


if __name__ == "__main__":
    main()
