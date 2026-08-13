"""Phase 2: parse every DataDefs/*.DataDef.xsd and derive the data model.

Emits:
  out/xsd_packages.csv    one row per package: xsd filename, targetNamespace,
                          declared package id parsed from the namespace,
                          every xs:import (schemaLocation + namespace) and
                          the countrywide package id it resolves to,
                          counts of complexTypes / elements / simpleTypes /
                          enumerations / annotations, file size.
  out/xsd_types.csv       one row per (package, complexType, element):
                          element name, type, minOccurs, maxOccurs, and any
                          "Metadata codes:" listed in the type's annotation.
  out/xsd_enums.csv       one row per (package, simpleType, enumeration
                          value) - the declared value vocabulary.
  out/xsd_report.txt      namespace pattern, the state->countrywide
                          dependency graph, restriction base types,
                          and how much the schema varies across packages.

Key derived fact: state schemas xs:import a specific countrywide package
namespace, so the corpus carries an explicit state->countrywide edition
dependency. This script materialises that edge for every package.
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

NS_RE = re.compile(r"^http://www\.verisk\.com/iso/erc/(?P<pkg>[^/]+)/(?P<root>.+)$")
MC_RE = re.compile(r"Metadata codes:\s*(.*)", re.S)


def scan(a):
    pkg_id, juris, content = a
    content = Path(content)
    d = content / "DataDefs"
    if not d.is_dir():
        return None
    files = [f for f in d.iterdir() if f.is_file()]
    prow = dict(pkg_id=pkg_id, juris=juris, n_xsd=len(files))
    types, enums = [], []
    stats = Counter()
    bases = Counter()
    imports = []
    f = files[0]
    try:
        root = c.parse_xml(f)
    except Exception as e:
        return dict(prow, xsd=f.name, error=str(e)), [], [], Counter(), Counter()
    tns = root.get("targetNamespace", "")
    m = NS_RE.match(tns)
    prow.update(xsd=f.name, bytes=f.stat().st_size, target_ns=tns,
                ns_pkg=m["pkg"] if m else "", ns_root=m["root"] if m else "",
                error="")
    for el in root:
        ln = c.lname(el.tag)
        if ln == "import":
            ins = el.get("namespace", "")
            im = NS_RE.match(ins)
            imports.append((el.get("schemaLocation", ""), ins,
                            im["pkg"] if im else ""))
    prow["imports"] = ";".join(i[1] for i in imports)
    prow["import_pkgs"] = ";".join(i[2] for i in imports)
    prow["import_locs"] = ";".join(i[0] for i in imports)
    prow["n_imports"] = len(imports)

    for el in root.iter():
        ln = c.lname(el.tag)
        stats[ln] += 1
        if ln == "restriction":
            bases[el.get("base", "")] += 1
    for ct in root:
        ln = c.lname(ct.tag)
        name = ct.get("name", "")
        if ln == "complexType":
            mcodes = ""
            for ann in ct.iter():
                if c.lname(ann.tag) == "documentation" and ann.text:
                    mm = MC_RE.search(ann.text)
                    if mm:
                        mcodes = " ".join(mm.group(1).split())
            base = ""
            for ext in ct.iter():
                if c.lname(ext.tag) in ("extension", "restriction"):
                    base = ext.get("base", "")
                    break
            for e in ct.iter():
                if c.lname(e.tag) == "element":
                    types.append((pkg_id, juris, name, base, mcodes,
                                  e.get("name", ""), e.get("type", ""),
                                  e.get("minOccurs", ""), e.get("maxOccurs", "")))
            if not any(c.lname(e.tag) == "element" for e in ct.iter()):
                types.append((pkg_id, juris, name, base, mcodes, "", "", "", ""))
        elif ln == "simpleType":
            for e in ct.iter():
                if c.lname(e.tag) == "enumeration":
                    enums.append((pkg_id, juris, name, e.get("value", "")))
    prow.update(n_complexType=stats["complexType"], n_element=stats["element"],
                n_simpleType=stats["simpleType"], n_enumeration=stats["enumeration"],
                n_attribute=stats["attribute"], n_documentation=stats["documentation"])
    return prow, types, enums, stats, bases


def main():
    pkgs = c.find_packages()
    args = [(p.pkg_id, p.juris, str(p.content)) for p in pkgs]
    prows, types, enums = [], [], []
    stats, bases = Counter(), Counter()
    with Pool() as pool:
        for res in pool.imap_unordered(scan, args, chunksize=4):
            if res is None:
                continue
            p, t, e, s, b = res
            prows.append(p); types.extend(t); enums.extend(e)
            stats.update(s); bases.update(b)

    keys = ["pkg_id", "juris", "xsd", "bytes", "n_xsd", "target_ns", "ns_pkg",
            "ns_root", "n_imports", "import_pkgs", "imports", "import_locs",
            "n_complexType", "n_element", "n_simpleType", "n_enumeration",
            "n_attribute", "n_documentation", "error"]
    with open(c.OUT / "xsd_packages.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        for r in sorted(prows, key=lambda x: x["pkg_id"]):
            w.writerow(r)
    with open(c.OUT / "xsd_types.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["pkg_id", "juris", "complexType", "base", "metadata_codes",
                    "element", "element_type", "minOccurs", "maxOccurs"])
        w.writerows(types)
    with open(c.OUT / "xsd_enums.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["pkg_id", "juris", "simpleType", "value"])
        w.writerows(enums)

    L = []; A = L.append
    A(f"packages with a DataDefs dir: {len(prows)}")
    A(f"xsd files per package: {Counter(r['n_xsd'] for r in prows)}")
    A(f"xsd filenames: {Counter(r['xsd'] for r in prows).most_common(8)}")
    A(f"parse errors: {sum(1 for r in prows if r.get('error'))}")
    A(f"target namespace matches erc/<pkg>/<root>: "
      f"{sum(1 for r in prows if r['ns_pkg'])}/{len(prows)}")
    A(f"ns_pkg == dir-derived pkg_id: "
      f"{sum(1 for r in prows if r['ns_pkg'] == r['pkg_id'])}/{len(prows)}")
    mismatch = [(r['pkg_id'], r['ns_pkg']) for r in prows if r['ns_pkg'] != r['pkg_id']]
    for m in mismatch[:20]:
        A(f"   NSMISMATCH dir={m[0]} ns={m[1]}")
    A("")
    A(f"imports per package: {Counter(r['n_imports'] for r in prows)}")
    A("STATE -> COUNTRYWIDE DEPENDENCY (imported pkg -> n state packages)")
    dep = Counter(r["import_pkgs"] for r in prows if r["import_pkgs"])
    for d, n in dep.most_common():
        A(f"  {d:28s} {n}")
    A("")
    A("countrywide packages and their imports:")
    for r in sorted(prows, key=lambda x: x["pkg_id"]):
        if r["juris"] == "CW":
            A(f"  {r['pkg_id']:22s} ns_root={r['ns_root']:14s} "
              f"imports={r['import_pkgs'] or '(none)'}  "
              f"cT={r['n_complexType']} el={r['n_element']} "
              f"sT={r['n_simpleType']} enum={r['n_enumeration']}")
    A("")
    A("SCHEMA SIZE RANGE (state packages)")
    sp = [r for r in prows if r["juris"] != "CW"]
    for k in ("n_complexType", "n_element", "n_simpleType", "n_enumeration", "bytes"):
        v = sorted(r[k] for r in sp)
        A(f"  {k:16s} min={v[0]} median={v[len(v)//2]} max={v[-1]}")
    A("")
    A(f"XSD ELEMENT TAGS: {stats.most_common()}")
    A(f"RESTRICTION BASE TYPES: {bases.most_common()}")
    A("")
    A(f"complexTypes (distinct names across corpus): "
      f"{len({t[2] for t in types})}")
    A(f"elements (distinct names): {len({t[5] for t in types if t[5]})}")
    A(f"simpleTypes (distinct names): {len({e[2] for e in enums})}")
    A(f"enumeration values (distinct): {len({e[3] for e in enums})}")
    A(f"complexTypes carrying Metadata codes annotation: "
      f"{len({(t[0], t[2]) for t in types if t[4]})}")
    A("")
    A("TOP 25 enumeration values by frequency")
    for v, n in Counter(e[3] for e in enums).most_common(25):
        A(f"  {n:7d}  {v[:100]}")
    (c.OUT / "xsd_report.txt").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
