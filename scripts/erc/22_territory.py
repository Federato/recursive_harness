"""Phase 5 step 5: how is geography expressed?

Finds the geographic rating mechanism from the data:

  T1 which key columns are geographic?  Identified by scanning ALL 221
     distinct key-column names for territory/zip/county/city tokens, so
     the set is discovered rather than assumed.
  T2 the resolution chain: how does a rater get from an address to a
     territory code?  Traced through the domain tables that map ZIP ->
     territory and the rate tables keyed on territory.
  T3 coverage: per jurisdiction, is territory actually used - i.e. does
     the jurisdiction's resolved content contain more than one distinct
     territory value?  A single-territory state is geographically flat.
  T4 vocabulary: the territory code values themselves, and the ZIP
     coverage per jurisdiction.

Emits out/territory_by_juris.csv, out/territory_vocab.csv,
out/territory.txt.
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
csv.field_size_limit(1 << 24)

GEO_TOKENS = ("Terr", "Territor", "ZipCode", "Zip", "County", "City",
              "Postal", "Region", "Location")


def scan(a):
    """Collect territory-ish column values from one package's tables."""
    pkg_id, juris, edition, content = a
    content = Path(content)
    vals = defaultdict(Counter)     # column -> value counter
    zipmap = Counter()              # territory -> n zips
    n_zip = 0
    for cat, suf in (("Rate Tables", ".RateTable.csv"),
                     ("Domain Tables", ".DomainTable.csv")):
        d = content / cat
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*" + suf)):
            table = f.name[: -len(suf)]
            try:
                hdr, rdr = c.read_csv_rows(f)
            except Exception:
                continue
            gi = [i for i, h in enumerate(hdr)
                  if any(t in h for t in GEO_TOKENS)]
            if not gi:
                continue
            is_zipmap = "ZipCode" in table or "TerritoryCodeByZip" in table
            di = hdr.index("DataValue") if "DataValue" in hdr else -1
            zi = hdr.index("ZipCode") if "ZipCode" in hdr else -1
            for r in rdr:
                for i in gi:
                    if i < len(r) and r[i].strip():
                        vals[hdr[i]][r[i].strip()] += 1
                if is_zipmap and zi >= 0 and di >= 0 and di < len(r):
                    zipmap[r[di].strip()] += 1
                    n_zip += 1
    return pkg_id, juris, edition, {k: dict(v) for k, v in vals.items()}, \
        dict(zipmap), n_zip


def load(n):
    with open(c.OUT / n, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def main():
    tabs = load("table_defs.csv")
    geo_cols = Counter()
    geo_tables = defaultdict(set)
    for t in tabs:
        for k in t["key_cols"].split("|"):
            if k and any(x in k for x in GEO_TOKENS):
                geo_cols[k] += 1
                geo_tables[k].add(t["table"])

    pkgs = c.find_packages()
    seen, args = set(), []
    for p in pkgs:
        if p.pkg_id in seen:
            continue
        seen.add(p.pkg_id)
        args.append((p.pkg_id, p.juris, p.edition, str(p.content)))
    with Pool() as pool:
        res = pool.map(scan, args, chunksize=4)

    parent = {r["pkg_id"]: r["import_pkgs"] for r in load("xsd_packages.csv")}
    byid = {r[0]: r for r in res}
    ed = {r[0]: r[2] for r in res}
    jur = {r[0]: r[1] for r in res}
    latest = {}
    for p, j in jur.items():
        if j not in latest or ed[p] > ed[latest[j]]:
            latest[j] = p

    L = []; A = L.append
    A("TERRITORY AND GEOGRAPHY")
    A("")
    A("T1  GEOGRAPHIC KEY COLUMNS (discovered by token scan over all 221 "
      "distinct key-column names)")
    A(f"    {'key column':46s} {'table defs':>11} {'distinct tables':>16}")
    for k, n in geo_cols.most_common():
        A(f"    {k:46s} {n:11d} {len(geo_tables[k]):16d}")
    A(f"    total table defs keyed on a geographic column: "
      f"{sum(geo_cols.values())} of {len(tabs)}")

    A("")
    A("T2  RESOLUTION CHAIN")
    A("    The corpus expresses geography as a two-step indirection:")
    A("      (a) a domain table maps a postal code to a territory code")
    A("          (tables whose name contains 'TerritoryCodeByZipCode' / 'ZipCode')")
    A("      (b) rate tables are keyed on the territory code")
    A("          (PremOpsTerr / ProdsCompldOpsTerr / LiquorLiabTerr ...)")
    A("    Form Related Fields wires step (a) into the UI: a row with")
    A("      ColumnName=<Terr field>, DomainTableName=TerritoryCodeByZipCode,")
    A("      RelatedField=ZipCode")
    rf = 0
    seen2 = set()
    examples = []
    for p in pkgs:
        if p.pkg_id in seen2:
            continue
        seen2.add(p.pkg_id)
        f = Path(p.content) / "Form Related Fields" / "RelatedFields.FormField.csv"
        if not f.exists():
            continue
        hdr, rdr = c.read_csv_rows(f)
        for r in rdr:
            d = dict(zip(hdr, r))
            if any(t in d.get("DomainTableName", "") for t in GEO_TOKENS) or \
               any(t in d.get("RelatedField", "") for t in GEO_TOKENS):
                rf += 1
                if len(examples) < 6:
                    examples.append((p.pkg_id, d.get("ColumnName"),
                                     d.get("DomainTableName"),
                                     d.get("RelatedField")))
    A(f"    Form Related Fields rows wiring a geographic lookup: {rf} of 3122")
    for e in examples:
        A(f"      {e[0]}: {e[1]} <- {e[2]} keyed by {e[3]}")

    A("")
    A("T3  IS GEOGRAPHY ACTUALLY USED?  (latest package per jurisdiction, "
      "resolved through the countrywide parent)")
    A(f"    {'juris':6} {'terr cols':>10} {'distinct terr codes':>20} "
      f"{'zip rows':>9} {'verdict':>18}")
    rows = []
    flat = multi = 0
    for j in sorted(latest):
        p = latest[j]
        own = byid[p][3]
        par = byid.get(parent.get(p, ""), (None, None, None, {}, {}, 0))[3]
        codes = set()
        ncols = 0
        for col, vv in list(own.items()) + list(par.items()):
            if "Terr" in col and "Zip" not in col:
                ncols += 1
                codes |= set(vv)
        codes = {x for x in codes if x not in ("", "CW")}
        nz = byid[p][5] or byid.get(parent.get(p, ""), (0,) * 6)[5]
        verdict = ("multi-territory" if len(codes) > 1 else
                   "single/flat" if len(codes) == 1 else "no territory")
        flat += verdict != "multi-territory"
        multi += verdict == "multi-territory"
        rows.append([j, ncols, len(codes), nz, verdict,
                     ";".join(sorted(codes))[:300]])
        A(f"    {j:6} {ncols:10d} {len(codes):20d} {nz:9d} {verdict:>18}")
    A(f"    multi-territory jurisdictions: {multi}; flat/none: {flat}")
    with open(c.OUT / "territory_by_juris.csv", "w", newline="",
              encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["juris", "n_territory_columns", "n_distinct_codes",
                    "n_zip_rows", "verdict", "codes"])
        w.writerows(rows)

    A("")
    A("T4  VOCABULARY")
    allv = defaultdict(Counter)
    for r in res:
        for col, vv in r[3].items():
            allv[col].update(vv)
    with open(c.OUT / "territory_vocab.csv", "w", newline="",
              encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["column", "value", "n_cells"])
        for col in sorted(allv):
            for v, n in allv[col].most_common():
                w.writerow([col, v, n])
    for col in sorted(allv, key=lambda x: -len(allv[x]))[:10]:
        vv = allv[col]
        A(f"    {col:40s} {len(vv):6d} distinct; sample: "
          f"{[v for v, _ in vv.most_common(8)]}")
    zc = allv.get("ZipCode", Counter())
    A(f"    ZipCode column: {len(zc)} distinct values corpus-wide")
    A(f"      non-numeric ZipCode values: "
      f"{[v for v in zc if not v.isdigit()][:10]}")
    (c.OUT / "territory.txt").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L[:90]))


if __name__ == "__main__":
    main()
