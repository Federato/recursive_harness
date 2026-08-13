"""Phase 2: catalogue every declared Rate Table and Domain Table.

Parses every *Def.RateTableDef.xml and *Def.DomainTableDef.xml in the
corpus (multiprocessing over packages) and emits:

  out/table_defs.csv       one row per (package, table): kind, table name,
                           metadata codes, key columns + types +
                           CaseInsensitive flag, value columns + types,
                           declared column count, whether a paired CSV exists,
                           and the CSV's actual header + row count.
  out/table_catalogue.csv  one row per distinct SIGNATURE
                           (kind|table|keycols|valuecols) with the number of
                           packages and the jurisdictions carrying it.
  out/table_defs_report.txt  element model of the Def files, distinct
                           attributes seen, type vocabulary, header/def
                           reconciliation results and mismatches.

Reconciliation performed: the declared KeyCols+ValueCols sequence is
compared, in order, against the CSV header row of the paired data file.
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


def scan_pkg(pk_tuple):
    juris, pkg_id, content = pk_tuple
    content = Path(content)
    out = []
    elem_tags = Counter()
    attrs = Counter()
    problems = []
    for cat, defsuf, datasuf, kind in [
        ("Rate Tables", ".RateTableDef.xml", ".RateTable.csv", "Rate"),
        ("Domain Tables", ".DomainTableDef.xml", ".DomainTable.csv", "Domain"),
    ]:
        d = content / cat
        if not d.is_dir():
            continue
        defs = {}
        datas = {}
        for f in d.iterdir():
            if f.name.endswith(defsuf):
                # 'FooDef.RateTableDef.xml' -> 'Foo'
                base = f.name[: -len(defsuf)]
                base = base[:-3] if base.endswith("Def") else base
                defs[base] = f
            elif f.name.endswith(datasuf):
                datas[f.name[: -len(datasuf)]] = f
        for base in sorted(set(defs) | set(datas)):
            df, cf = defs.get(base), datas.get(base)
            mcodes, keys, vals = [], [], []
            if df is not None:
                try:
                    root = c.parse_xml(df)
                except Exception as e:
                    problems.append(f"XMLFAIL {pkg_id} {df.name}: {e}")
                    continue
                elem_tags[c.lname(root.tag)] += 1
                for el in root.iter():
                    ln = c.lname(el.tag)
                    elem_tags[ln] += 1
                    for a in el.attrib:
                        attrs[f"{ln}@{a}"] += 1
                    if ln == "MetaDataCode":
                        mcodes.append((el.text or "").strip())
                    elif ln == "KeyCol":
                        keys.append((el.get("Name"), el.get("Type"),
                                     el.get("CaseInsensitive")))
                    elif ln == "ValueCol":
                        vals.append((el.get("Name"), el.get("Type")))
            hdr, nrows, mismatch = "", -1, ""
            if cf is not None:
                try:
                    h, rdr = c.read_csv_rows(cf)
                    hdr = "|".join(h)
                    nrows = sum(1 for _ in rdr)
                    declared = [k[0] for k in keys] + [v[0] for v in vals]
                    if df is not None and declared != h:
                        mismatch = f"decl={'|'.join(declared)}"
                except Exception as e:
                    problems.append(f"CSVFAIL {pkg_id} {cf.name}: {e}")
            out.append(dict(
                pkg_id=pkg_id, juris=juris, kind=kind, table=base,
                has_def=df is not None, has_csv=cf is not None,
                metadata_codes=";".join(mcodes),
                key_cols="|".join(k[0] or "" for k in keys),
                key_types="|".join(k[1] or "" for k in keys),
                key_ci="|".join(k[2] or "" for k in keys),
                value_cols="|".join(v[0] or "" for v in vals),
                value_types="|".join(v[1] or "" for v in vals),
                n_key=len(keys), n_value=len(vals),
                csv_header=hdr, csv_rows=nrows, header_mismatch=mismatch,
            ))
    return out, elem_tags, attrs, problems


def main():
    pkgs = c.find_packages()
    args = [(p.juris, p.pkg_id, str(p.content)) for p in pkgs]
    rows = []
    elem_tags, attrs = Counter(), Counter()
    problems = []
    with Pool() as pool:
        for o, e, a, pr in pool.imap_unordered(scan_pkg, args, chunksize=4):
            rows.extend(o)
            elem_tags.update(e)
            attrs.update(a)
            problems.extend(pr)

    with open(c.OUT / "table_defs.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    sig = defaultdict(lambda: {"pkgs": set(), "juris": set(), "rows": 0})
    for r in rows:
        k = (r["kind"], r["table"], r["key_cols"], r["key_types"],
             r["value_cols"], r["value_types"])
        s = sig[k]
        s["pkgs"].add(r["pkg_id"])
        s["juris"].add(r["juris"])
        s["rows"] += max(r["csv_rows"], 0)
    with open(c.OUT / "table_catalogue.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["kind", "table", "key_cols", "key_types", "value_cols",
                    "value_types", "n_packages", "n_juris", "juris_list",
                    "total_csv_rows"])
        for k, s in sorted(sig.items()):
            w.writerow(list(k) + [len(s["pkgs"]), len(s["juris"]),
                                  ";".join(sorted(s["juris"])), s["rows"]])

    L = []
    A = L.append
    A(f"table def rows (package x table): {len(rows)}")
    A(f"  Rate:   {sum(1 for r in rows if r['kind']=='Rate')}")
    A(f"  Domain: {sum(1 for r in rows if r['kind']=='Domain')}")
    A(f"def present, csv missing:  {sum(1 for r in rows if r['has_def'] and not r['has_csv'])}")
    A(f"csv present, def missing:  {sum(1 for r in rows if r['has_csv'] and not r['has_def'])}")
    A(f"   of which Domain: {sum(1 for r in rows if r['has_csv'] and not r['has_def'] and r['kind']=='Domain')}")
    A(f"   of which Rate:   {sum(1 for r in rows if r['has_csv'] and not r['has_def'] and r['kind']=='Rate')}")
    A(f"distinct table names: Rate={len({r['table'] for r in rows if r['kind']=='Rate'})} "
      f"Domain={len({r['table'] for r in rows if r['kind']=='Domain'})}")
    A(f"distinct signatures: {len(sig)}")
    A(f"total CSV data rows: {sum(max(r['csv_rows'],0) for r in rows)}")
    A("")
    A("HEADER/DEF RECONCILIATION")
    mm = [r for r in rows if r["header_mismatch"]]
    A(f"  defs with a paired csv: {sum(1 for r in rows if r['has_def'] and r['has_csv'])}")
    A(f"  header != KeyCols+ValueCols (in order): {len(mm)}")
    for r in mm[:20]:
        A(f"   {r['pkg_id']} {r['kind']}:{r['table']}  csv={r['csv_header']}  {r['header_mismatch']}")
    A("")
    A("ELEMENT MODEL (tag -> occurrences across all Def files)")
    for t, n in elem_tags.most_common():
        A(f"  {t:20s} {n}")
    A("")
    A("ATTRIBUTES")
    for t, n in attrs.most_common():
        A(f"  {t:30s} {n}")
    A("")
    A("DECLARED TYPE VOCABULARY")
    tv = Counter()
    for r in rows:
        for t in r["key_types"].split("|"):
            if t:
                tv["key:" + t] += 1
        for t in r["value_types"].split("|"):
            if t:
                tv["value:" + t] += 1
    for t, n in tv.most_common():
        A(f"  {t:20s} {n}")
    A("")
    A(f"CaseInsensitive values seen: "
      f"{Counter(x for r in rows for x in r['key_ci'].split('|') if x)}")
    A("")
    A(f"PROBLEMS: {len(problems)}")
    for p in problems[:50]:
        A("  " + p)
    (c.OUT / "table_defs_report.txt").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L[:80]))


if __name__ == "__main__":
    main()
