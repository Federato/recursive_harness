"""Phase 2: parse every Metadata/*.Metadata.xml and characterise the model.

Emits:
  out/metadata_entries.csv   one row per MetadataEntry across the corpus:
                             package, source file, top-level group, entry
                             code, entry name, depth, parent code,
                             description, and Property name/type/value pairs
                             flattened into columns.
  out/circulars.csv          circulars parsed out of the Circulars group:
                             code, circular number, effective date, filing
                             reference, type, description, packages citing.
  out/metadata_report.txt    element model, attribute vocabulary, the set of
                             metadata file names, the set of top-level
                             groups, Property names/types seen, and which
                             packages deviate from the common file set.

The Circulars parse is derived: the Name attribute packs four fields in
the literal form
  "Circular <no> (Circular Effective Date: <d> | Filing Reference: <r> | Type: <t>)"
which this script splits with a regex; unparsed names are reported.
"""
from __future__ import annotations

import csv
import re
import sys
from collections import Counter, defaultdict
from multiprocessing import Pool
from pathlib import Path
from importlib import import_module

sys.path.insert(0, str(Path(__file__).parent))
c = import_module("00_common")

CIRC_RE = re.compile(
    r"^Circular\s+(?P<no>\S+)\s*\(Circular Effective Date:\s*(?P<eff>[^|]*?)\s*\|"
    r"\s*Filing Reference:\s*(?P<ref>[^|]*?)\s*\|\s*Type:\s*(?P<typ>[^)]*?)\s*\)$"
)


def walk(el, depth, parent, group, out, tags, attrs, props):
    for ch in el:
        ln = c.lname(ch.tag)
        tags[ln] += 1
        for a in ch.attrib:
            attrs[f"{ln}@{a}"] += 1
        if ln != "MetadataEntry":
            continue
        code = ch.get("Code", "")
        name = ch.get("Name", "")
        desc = ""
        pr = {}
        for sub in ch:
            sl = c.lname(sub.tag)
            if sl == "Description":
                desc = (sub.text or "").strip()
            elif sl == "Property":
                pr[sub.get("Name", "")] = (sub.text or "").strip()
                props[(sub.get("Name", ""), sub.get("Type", ""))] += 1
        g = group if depth > 0 else code
        out.append((g, code, name, depth, parent, desc,
                    ";".join(f"{k}={v}" for k, v in pr.items())))
        walk(ch, depth + 1, code, g, out, tags, attrs, props)


def scan(a):
    pkg_id, juris, content = a
    content = Path(content)
    md = content / "Metadata"
    rows = []
    tags, attrs, props = Counter(), Counter(), Counter()
    fnames = []
    ns = Counter()
    if not md.is_dir():
        return rows, tags, attrs, props, fnames, ns, [f"NOMETA {pkg_id}"]
    probs = []
    for f in sorted(md.iterdir()):
        if not f.is_file():
            continue
        fnames.append(f.name)
        try:
            root = c.parse_xml(f)
        except Exception as e:
            probs.append(f"XMLFAIL {pkg_id} {f.name}: {e}")
            continue
        ns[c.ns_of(root.tag)] += 1
        tags[c.lname(root.tag)] += 1
        o = []
        walk(root, 0, "", "", o, tags, attrs, props)
        for r in o:
            rows.append((pkg_id, juris, f.name) + r)
    return rows, tags, attrs, props, fnames, ns, probs


def main():
    pkgs = c.find_packages()
    args = [(p.pkg_id, p.juris, str(p.content)) for p in pkgs]
    allrows = []
    tags, attrs, props, ns = Counter(), Counter(), Counter(), Counter()
    fileset = Counter()
    pkg_files = {}
    probs = []
    with Pool() as pool:
        for r, t, a, p, fn, n, pr in pool.imap_unordered(scan, args, chunksize=4):
            allrows.extend(r)
            tags.update(t); attrs.update(a); props.update(p); ns.update(n)
            probs.extend(pr)
            if r:
                pkg_files[r[0][0]] = fn
            for x in fn:
                fileset[x] += 1

    hdr = ["pkg_id", "juris", "file", "group", "code", "name", "depth",
           "parent", "description", "properties"]
    with open(c.OUT / "metadata_entries.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(hdr); w.writerows(allrows)

    # circulars
    circ = defaultdict(lambda: {"pkgs": set(), "fields": None, "desc": set()})
    unparsed = Counter()
    for r in allrows:
        pkg_id, juris, fname, group, code, name, depth, parent, desc, pr = r
        if group != "Circulars" or depth == 0:
            continue
        m = CIRC_RE.match(name)
        e = circ[code]
        e["pkgs"].add(pkg_id)
        if desc:
            e["desc"].add(desc)
        if m:
            e["fields"] = (m["no"], m["eff"], m["ref"], m["typ"])
        else:
            unparsed[name] += 1
    with open(c.OUT / "circulars.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["code", "circular_no", "effective_date", "filing_reference",
                    "type", "n_packages", "descriptions"])
        for code, e in sorted(circ.items()):
            f = e["fields"] or ("", "", "", "")
            w.writerow([code, *f, len(e["pkgs"]), " || ".join(sorted(e["desc"]))])

    L = []; A = L.append
    A(f"metadata entries parsed: {len(allrows)}")
    A(f"packages with a Metadata dir: {len(pkg_files)} of {len(pkgs)}")
    A(f"XML namespaces on metadata roots: {dict(ns)}")
    A("")
    A("METADATA FILE NAMES (count of packages containing)")
    for f, n in fileset.most_common(40):
        A(f"  {f:40s} {n}")
    A("")
    A("TOP-LEVEL GROUPS (depth 0 entry Code -> occurrences)")
    g0 = Counter(r[4] for r in allrows if r[6] == 0)
    for g, n in g0.most_common():
        A(f"  {g:30s} {n}")
    A("")
    A("ENTRY COUNT BY GROUP")
    gb = Counter(r[3] for r in allrows)
    for g, n in gb.most_common():
        A(f"  {g:30s} {n}")
    A("")
    A("MAX DEPTH: " + str(max(r[6] for r in allrows)))
    A("")
    A("ELEMENT MODEL"); [A(f"  {t:20s} {n}") for t, n in tags.most_common()]
    A(""); A("ATTRIBUTES"); [A(f"  {t:30s} {n}") for t, n in attrs.most_common()]
    A(""); A("PROPERTY (Name,Type) -> count")
    for (pn, pt), n in props.most_common(40):
        A(f"  {pn:24s} {pt:10s} {n}")
    A("")
    A(f"CIRCULARS: {len(circ)} distinct codes; unparsed Name forms: {len(unparsed)}")
    for u, n in unparsed.most_common(10):
        A(f"  UNPARSED({n}): {u[:150]}")
    A("")
    A(f"PROBLEMS: {len(probs)}")
    for p in probs[:40]:
        A("  " + p)
    (c.OUT / "metadata_report.txt").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
