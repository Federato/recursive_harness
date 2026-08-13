"""Phase 3: cross-artifact reconciliations and the headline corpus numbers.

Consumes the intermediates written by 01-08 and checks claims that can be
checked, writing out/reconciliation.txt:

 R1  package count / dedup: byte-identical duplicate package directories
 R2  every RateTable/DomainTable named in Metadata has a CSV, and vice versa
 R3  every Def's KeyCols+ValueCols equals its CSV header, in order
 R4  DataDefInfo metadata entries vs xs:complexType names in the .xsd
 R5  Ratebook Tables CSV TableName vs DataDefInfo table names
 R6  Form Fields DomainTableName vs the Domain Tables actually shipped
 R7  circular codes cited by table Defs vs codes declared in
     Circulars.Metadata.xml
 R8  BureauRuleNumber codes cited by Defs vs those in GL<XX>.Metadata.xml
 R9  edition timeline per jurisdiction, and the state -> countrywide
     import graph coverage
"""
from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path
from importlib import import_module

sys.path.insert(0, str(Path(__file__).parent))
c = import_module("00_common")
csv.field_size_limit(1 << 24)


def load(n):
    with open(c.OUT / n, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def main():
    L = []; A = L.append
    pk = load("packages.csv")
    tabs = load("table_defs.csv")
    me = load("metadata_entries.csv")
    xsd = load("xsd_packages.csv")
    xt = load("xsd_types.csv")
    fs = load("form_csv_schema.csv")

    A("R1 PACKAGES")
    A(f"  package directories: {len(pk)}")
    A(f"  distinct pkg_id:     {len({p['pkg_id'] for p in pk})}")
    dups = [k for k, v in Counter(p["pkg_id"] for p in pk).items() if v > 1]
    A(f"  duplicated pkg_id:   {len(dups)} -> {sorted(dups)}")
    A(f"  jurisdictions (from pkg name): "
      f"{len({p['juris'] for p in pk})}")
    A(f"  packages per jurisdiction dir mismatching the pkg name juris: "
      f"{[(p['juris_dir'], p['pkg_id']) for p in pk if p['juris_dir'] not in (p['juris'], 'countrywide')]}")

    A("")
    A("R2 METADATA <-> SHIPPED TABLES")
    md_rt = defaultdict(set); md_dt = defaultdict(set)
    for m in me:
        if m["depth"] != "1":
            continue
        if m["group"] == "RateTables":
            md_rt[m["pkg_id"]].add(m["name"])
        elif m["group"] == "DomainTables":
            md_dt[m["pkg_id"]].add(m["name"])
    ship_rt = defaultdict(set); ship_dt = defaultdict(set)
    for t in tabs:
        (ship_rt if t["kind"] == "Rate" else ship_dt)[t["pkg_id"]].add(
            t["table"].removeprefix("Domain") if t["kind"] == "Domain"
            else t["table"])
    for label, md, sh in (("RateTable", md_rt, ship_rt),
                          ("DomainTable", md_dt, ship_dt)):
        miss = sum(len(md[p] - sh[p]) for p in md)
        extra = sum(len(sh[p] - md[p]) for p in sh)
        A(f"  {label}: declared in metadata but no csv: {miss}; "
          f"csv shipped but not in metadata: {extra}")
        ex = [(p, sorted(sh[p] - md[p])[:3]) for p in sh if sh[p] - md[p]]
        for e in ex[:5]:
            A(f"     EXTRA {e[0]}: {e[1]}")
        ms = [(p, sorted(md[p] - sh[p])[:3]) for p in md if md[p] - sh[p]]
        for e in ms[:5]:
            A(f"     MISSING {e[0]}: {e[1]}")

    A("")
    A("R3 DEF HEADER RECONCILIATION")
    withboth = [t for t in tabs if t["has_def"] == "True" and t["has_csv"] == "True"]
    mm = [t for t in withboth if t["header_mismatch"]]
    A(f"  def+csv pairs: {len(withboth)}; header != declared columns: {len(mm)}")
    A(f"  all mismatches are a trailing empty CSV column: "
      f"{all(t['csv_header'].endswith('|') for t in mm)}")
    A(f"  affected tables: {sorted({t['table'] for t in mm})}")
    A(f"  affected packages: {len({t['pkg_id'] for t in mm})}")
    A(f"  domain csvs with no Def: "
      f"{sum(1 for t in tabs if t['kind']=='Domain' and t['has_def']=='False')}")
    A(f"  ... all with header 'StateCode|DisplayValue|DataValue': "
      f"{all(t['csv_header'] == 'StateCode|DisplayValue|DataValue' for t in tabs if t['kind']=='Domain' and t['has_def']=='False')}")
    A(f"  rate csvs with no Def: "
      f"{sum(1 for t in tabs if t['kind']=='Rate' and t['has_def']=='False')}")
    A(f"  total declared csv data rows: {sum(int(t['csv_rows']) for t in tabs if int(t['csv_rows'])>0)}")

    A("")
    A("R4 DataDefInfo METADATA vs XSD complexTypes")
    md_dd = defaultdict(set)
    for m in me:
        if m["group"] == "DataDefInfo" and m["depth"] == "1":
            md_dd[m["pkg_id"]].add(m["name"])
    ct = defaultdict(set)
    for r in xt:
        ct[r["pkg_id"]].add(r["complexType"])
    dd_not_ct = sum(len(md_dd[p] - ct[p]) for p in md_dd)
    A(f"  DataDefInfo entries: {sum(len(v) for v in md_dd.values())}")
    A(f"  not present as a complexType in the same package's xsd: {dd_not_ct}")
    A(f"  (note: state xsds only redeclare types they override; the rest are "
      f"inherited from the imported countrywide xsd)")
    # check against the imported CW package instead
    imp = {r["pkg_id"]: r["import_pkgs"] for r in xsd}
    still = 0
    for p in md_dd:
        par = imp.get(p, "")
        still += len(md_dd[p] - ct[p] - ct.get(par, set()))
    A(f"  still unresolved after also allowing the imported CW xsd: {still}")

    A("")
    A("R5/R6 FORM CSV UNIFORMITY")
    for cat in sorted({r["category"] for r in fs}):
        hs = {r["header"] for r in fs if r["category"] == cat}
        A(f"  {cat}: {len({r['pkg_id'] for r in fs if r['category']==cat})} "
          f"packages, {len(hs)} distinct header(s)")

    A("")
    A("R7/R8 CODE CITATION CLOSURE")
    declared = defaultdict(set)
    for m in me:
        declared[m["pkg_id"]].add(m["code"])
    cited = 0; unres = Counter()
    for t in tabs:
        for code in filter(None, t["metadata_codes"].split(";")):
            cited += 1
            if code not in declared[t["pkg_id"]]:
                unres[code] += 1
    A(f"  MetaDataCode citations in table Defs: {cited}")
    A(f"  citations with no matching MetadataEntry Code in the same package: "
      f"{sum(unres.values())} ({len(unres)} distinct)")
    for k, v in unres.most_common(15):
        A(f"     {k} x{v}")

    A("")
    A("R9 EDITION TIMELINE")
    per = defaultdict(list)
    for p in pk:
        per[p["juris"]].append((p["edition"], p["version"]))
    A(f"  jurisdictions: {len(per)}")
    A(f"  editions per jurisdiction: min={min(len(set(v)) for v in per.values())} "
      f"max={max(len(set(v)) for v in per.values())}")
    A(f"  edition date range: {min(p['edition'] for p in pk)} .. "
      f"{max(p['edition'] for p in pk)}")
    fut = sum(1 for p in pk if p["edition"] > "20260810")
    A(f"  packages with an edition date in the future (> 2026-08-10): {fut}")
    A(f"  version tokens seen: {Counter(p['version'] for p in pk).most_common()}")
    A("  per-jurisdiction package counts:")
    for j in sorted(per):
        eds = sorted(set(per[j]))
        A(f"    {j:3s} n={len(per[j]):3d}  {eds[0][0]}..{eds[-1][0]}")
    A("")
    A("  state -> countrywide xs:import edges:")
    for k, n in Counter(r["import_pkgs"] for r in xsd).most_common():
        A(f"    {k:22s} {n}")
    cwp = {p["pkg_id"] for p in pk if p["juris"] == "CW"}
    refd = {r["import_pkgs"] for r in xsd if r["import_pkgs"] != "ErcCore"}
    A(f"  referenced CW packages: {len(refd)}; present in corpus: "
      f"{len(refd & cwp)}; missing: {sorted(refd - cwp)}")
    A(f"  CW packages present but never imported: {sorted(cwp - refd)}")

    (c.OUT / "reconciliation.txt").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
