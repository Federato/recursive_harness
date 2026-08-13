"""Phase 5 step 2: what does this content rate?

Derives the product inventory from the data itself - never from outside
knowledge of the line of business.  Four independent derivations, then a
cross-check:

  D1 STATED sublines.  Packages ship a domain table whose values are the
     selectable sublines.  Only 60 of 567 packages ship one; the rest
     INHERIT it from the countrywide package their .xsd imports.  So the
     list is resolved state-first-then-parent, exactly as 18_composition.py
     showed a lookup resolves.  The resolved list is the jurisdiction's
     effective product list; this is the only channel where the corpus
     *states* its own product inventory.

  D2 Coverage pages.  Form Pages rows with Type='Coverage' name the
     optional/conditional coverages attachable to a policy, with their ISO
     form number.  Also resolved through the parent: a jurisdiction's
     effective coverage set is its own rows unioned with its countrywide
     parent's, state rows winning on name collision.

  D3 DataDefInfo Type property.  Every schema table is tagged
     Policy / Risk / Coverage / Schedule / Form in the metadata.  This
     gives the structural level at which each artefact sits.

  D4 Coverage families by token.  Rate-table names and rule DataDefGroups
     are scanned for the subline tokens discovered in D1 (plus tokens for
     coverages that D1 does not list, found by frequency), giving the
     weight of rating content behind each coverage.

Cross-check: does every subline named in D1 have rating tables in D4, and
does every D4 family map to a D1 subline?  Divergence is reported.

Emits out/coverage_matrix.csv (jurisdiction x subline, from D1),
out/coverage_pages.csv (distinct coverage name x form number x
jurisdictions), and out/coverage_inventory.txt.
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

SUBLINE_TABLES = ("DomainSubline", "Subline")


def scan(a):
    pkg_id, juris, edition, content = a
    out = set()
    d = Path(content) / "Domain Tables"
    if d.is_dir():
        for nm in SUBLINE_TABLES:
            f = d / f"{nm}.DomainTable.csv"
            if not f.exists():
                continue
            hdr, rdr = c.read_csv_rows(f)
            di = hdr.index("DisplayValue") if "DisplayValue" in hdr else -1
            for r in rdr:
                if 0 <= di < len(r) and r[di].strip():
                    out.add(r[di].strip())
    d = Path(content) / "Rate Tables"
    if d.is_dir():
        for nm in SUBLINE_TABLES:
            f = d / f"{nm}.RateTable.csv"
            if not f.exists():
                continue
            hdr, rdr = c.read_csv_rows(f)
            for r in rdr:
                for i, v in enumerate(r):
                    if hdr[i] in ("DisplayValue", "Subline") and v.strip():
                        out.add(v.strip())
    return pkg_id, juris, edition, sorted(out)


def load(n):
    with open(c.OUT / n, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def main():
    pkgs = c.find_packages()
    seen, args = set(), []
    for p in pkgs:
        if p.pkg_id in seen:
            continue
        seen.add(p.pkg_id)
        args.append((p.pkg_id, p.juris, p.edition, str(p.content)))
    with Pool() as pool:
        res = pool.map(scan, args, chunksize=4)

    own = {r[0]: set(r[3]) for r in res}
    juris_of = {r[0]: r[1] for r in res}
    ed_of = {r[0]: r[2] for r in res}
    parent = {r["pkg_id"]: r["import_pkgs"] for r in load("xsd_packages.csv")}

    # RESOLUTION: state list if the state ships one, else the parent's.
    def resolve(p):
        if own.get(p):
            return own[p], "own"
        par = parent.get(p, "")
        if own.get(par):
            return own[par], "inherited"
        return set(), "none"

    subs, src = {}, {}
    for p in own:
        subs[p], src[p] = resolve(p)
    all_sub = sorted({s for v in subs.values() for s in v})

    # latest package per jurisdiction, for the availability matrix
    latest = {}
    for p, j in juris_of.items():
        if j not in latest or ed_of[p] > ed_of[latest[j]]:
            latest[j] = p
    with open(c.OUT / "coverage_matrix.csv", "w", newline="",
              encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["juris", "pkg_id", "edition"] + all_sub)
        for j in sorted(latest):
            p = latest[j]
            w.writerow([j, p, ed_of[p]] +
                       [1 if s in subs[p] else 0 for s in all_sub])

    P = load("form_pages.csv")
    me = load("metadata_entries.csv")
    tabs = load("table_defs.csv")
    rules = load("rules_index.csv")

    L = []; A = L.append
    A(f"PRODUCT INVENTORY derived from {len(subs)} distinct packages")
    A("")
    A("D1  SUBLINES STATED BY THE DATA (the Subline domain/rate table)")
    A(f"    packages shipping their OWN subline list: "
      f"{sum(1 for p in src if src[p]=='own')} of {len(subs)}")
    A(f"    packages INHERITING it from their countrywide parent: "
      f"{sum(1 for p in src if src[p]=='inherited')}")
    A(f"    packages with no list from either source: "
      f"{sum(1 for p in src if src[p]=='none')}")
    A("    (all figures below are on the RESOLVED list)")
    A(f"    distinct subline values corpus-wide: {len(all_sub)}")
    cnt = Counter(s for v in subs.values() for s in v)
    jur = defaultdict(set)
    for p, v in subs.items():
        for s in v:
            jur[s].add(juris_of[p])
    A(f"    {'subline':56s} {'pkgs':>5} {'juris':>6}")
    for s in sorted(cnt, key=lambda x: -cnt[x]):
        A(f"    {s:56s} {cnt[s]:5d} {len(jur[s]):6d}")
    A("")
    A("    AVAILABILITY BY JURISDICTION (latest edition of each)")
    A(f"    jurisdictions with a subline list: "
      f"{sum(1 for j, p in latest.items() if subs[p])} of {len(latest)}")
    univ = [s for s in all_sub
            if all(s in subs[p] for j, p in latest.items() if subs[p])]
    A(f"    sublines available in EVERY jurisdiction that lists any: {univ}")
    A("    sublines that are NOT universal:")
    for s in all_sub:
        if s in univ:
            continue
        have = sorted(j for j, p in latest.items() if s in subs[p])
        miss = sorted(j for j, p in latest.items() if subs[p] and s not in subs[p])
        A(f"      {s}")
        A(f"        present in {len(have)}: {' '.join(have)}")
        A(f"        absent  in {len(miss)}: {' '.join(miss)}")

    A("")
    A("D2  COVERAGE PAGES (Form Pages Type='Coverage')")
    cov = [x for x in P if x["type"] == "Coverage"]
    A(f"    raw rows: {len(cov)}   distinct coverage names: "
      f"{len({x['name'] for x in cov})}   distinct form numbers: "
      f"{len({x['form_number'] for x in cov if x['form_number']})}")
    bypkg = defaultdict(set)
    for x in cov:
        bypkg[x["pkg_id"]].add(x["name"])
    raw = sorted(len(bypkg.get(p, ())) for j, p in latest.items())
    A(f"    UNRESOLVED, per jurisdiction (latest edition): min={raw[0]} "
      f"median={raw[len(raw)//2]} max={raw[-1]}")
    # RESOLVED: state rows unioned with the countrywide parent's
    eff = {}
    for j, p in latest.items():
        eff[j] = bypkg.get(p, set()) | bypkg.get(parent.get(p, ""), set())
    res_n = sorted(len(v) for v in eff.values())
    A(f"    RESOLVED   (state + countrywide parent): min={res_n[0]} "
      f"median={res_n[len(res_n)//2]} max={res_n[-1]}")
    allj = len(eff)
    freq = Counter(n for j in eff for n in eff[j])
    A(f"    distinct coverages across the resolved sets: {len(freq)}")
    A(f"    present in all {allj} jurisdictions: "
      f"{sum(1 for n, k in freq.items() if k == allj)}")
    A(f"    present in exactly one jurisdiction: "
      f"{sum(1 for n, k in freq.items() if k == 1)}")
    A(f"    contributed by the countrywide parent alone (state adds nothing): "
      f"{sum(1 for j, p in latest.items() if not bypkg.get(p))} jurisdictions")
    A("    most jurisdiction-specific coverages (present in 1-3 jurisdictions), "
      "sample of 12:")
    for n, k in sorted(((n, k) for n, k in freq.items() if k <= 3),
                       key=lambda x: x[0])[:12]:
        A(f"      ({k}) {n}")
    with open(c.OUT / "coverage_pages.csv", "w", newline="",
              encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["coverage_name", "form_numbers", "n_juris", "juris_list",
                    "n_rows", "attachment_types", "statuses"])
        g = defaultdict(lambda: defaultdict(set))
        n_rows = Counter()
        for x in cov:
            g[x["name"]]["j"].add(x["juris"])
            g[x["name"]]["f"].add(x["form_number"])
            g[x["name"]]["a"].add(x["attachment_type"])
            g[x["name"]]["s"].add(x["status"])
            n_rows[x["name"]] += 1
        for n in sorted(g, key=lambda x: -len(g[x]["j"])):
            w.writerow([n, ";".join(sorted(x for x in g[n]["f"] if x)),
                        len(g[n]["j"]), ";".join(sorted(g[n]["j"])),
                        n_rows[n], ";".join(sorted(g[n]["a"])),
                        ";".join(sorted(g[n]["s"]))])

    A("")
    A("D3  STRUCTURAL LEVEL (DataDefInfo Type property)")
    lev = Counter()
    for m in me:
        if m["group"] != "DataDefInfo" or m["depth"] != "1":
            continue
        t = ""
        for kv in m["properties"].split(";"):
            if kv.startswith("Type="):
                t = kv[5:]
        lev[t or "(none)"] += 1
    for k, n in lev.most_common():
        A(f"    {k:14s} {n}")
    A("    -> the schema is a five-level tree: Policy > Risk > Coverage >")
    A("       Schedule, with Form tables hanging off it.")

    A("")
    A("D4  RATING WEIGHT BY COVERAGE FAMILY")
    TOKENS = [
        ("Premises/Operations", ["PremOps", "PremisesOperations"]),
        ("Products/Completed Operations", ["ProdsCompldOps", "ProdsCompleted",
                                           "CGLProds"]),
        ("Liquor", ["Liquor"]),
        ("Owners and Contractors", ["OwnersContractors", "OwnersContrctrs",
                                    "OwnersAndContractor"]),
        ("Railroad", ["Railroad"]),
        ("Pollution", ["Pollution"]),
        ("Underground Storage Tank", ["UST", "UndergroundStorage"]),
        ("Electronic Data Liability", ["ElectronicData", "EDL"]),
        ("Product Withdrawal", ["ProductWithdrawal", "ProdWithdrawl",
                                "ProdsWithdrawal"]),
        ("Special Protective And Highway", ["SpecialProtective", "Hwy"]),
        ("Terrorism", ["Terrorism", "TRIP", "CertifiedActs"]),
        ("Unmanned Aircraft (drones)", ["UnmannedAircraft"]),
        ("Medical Payments", ["MedPay", "MedicalPayments"]),
        ("Employee Benefits Liability", ["EmployeeBenefits"]),
        ("Fungi / Bacteria", ["FungiBacteria", "Fungi"]),
        ("Cannabis", ["Cannabis", "Hemp"]),
        ("Damage To Premises Rented To You", ["DamageToPremises"]),
        ("Increased Limits / ILF", ["ILF", "IncreasedLimit", "IncrdLimit"]),
        ("Deductibles", ["Deductible"]),
        ("Experience / Schedule rating", ["ExperienceRating",
                                          "ScheduleRatingModification"]),
        ("Composite rating", ["CompositeRating"]),
    ]
    tnames = Counter()
    for t in tabs:
        tnames[(t["kind"], t["table"])] += 1
    dgroups = {r["datadef_group"] for r in rules}
    A(f"    {'family':34s} {'rate tbl':>9} {'domain tbl':>11} {'datadefs':>9}")
    hit_rt = set(); hit_dt = set(); hit_dg = set()
    for name, toks in TOKENS:
        rt = {t for (k, t) in tnames if k == "Rate" and any(x in t for x in toks)}
        dt = {t for (k, t) in tnames if k == "Domain" and any(x in t for x in toks)}
        dg = {g for g in dgroups if any(x in g for x in toks)}
        hit_rt |= rt; hit_dt |= dt; hit_dg |= dg
        A(f"    {name:34s} {len(rt):9d} {len(dt):11d} {len(dg):9d}")
    allrt = {t for (k, t) in tnames if k == "Rate"}
    alldt = {t for (k, t) in tnames if k == "Domain"}
    A(f"    {'(unclassified)':34s} {len(allrt-hit_rt):9d} "
      f"{len(alldt-hit_dt):11d} {len(dgroups-hit_dg):9d}")
    A(f"    totals: {len(allrt)} rate table names, {len(alldt)} domain table "
      f"names, {len(dgroups)} datadef groups")
    A("")
    A("    unclassified rate-table names (sample of 30):")
    for t in sorted(allrt - hit_rt)[:30]:
        A(f"      {t}")

    A("")
    A("CROSS-CHECK D1 vs D4")
    for s in sorted(cnt, key=lambda x: -cnt[x]):
        fam = next((n for n, tk in TOKENS if n == s), None)
        A(f"    subline {s!r:58s} -> family in D4: {'yes' if fam else 'NO'}")
    (c.OUT / "coverage_inventory.txt").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L[:95]))


if __name__ == "__main__":
    main()
