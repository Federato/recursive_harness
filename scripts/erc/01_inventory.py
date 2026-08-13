"""Phase 1 inventory.

Walks every package in the ERC General Liability corpus and produces:

  out/packages.csv        one row per package: jurisdiction, id, edition,
                          version, wrapper style, categories present/absent,
                          per-category file counts, total files, total bytes
  out/files.csv           one row per file in the corpus (excluding .zip):
                          package, category, filename, extension, ERC "kind"
                          (RateTable / RateTableDef / Rule / ...), size
  out/inventory_summary.txt  reconciliation totals + anomaly list

Anomalies detected: non-conforming package directory names, missing
categories, unexpected extra categories, zero-byte files, files sitting
outside any known category, duplicate (juris, edition, version) keys,
packages with no zip counterpart and zips with no extracted dir.
"""
from __future__ import annotations

import csv
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from importlib import import_module
c = import_module("00_common")

KIND_RE = [
    (re.compile(r"\.RateTableDef\.xml$", re.I), "RateTableDef"),
    (re.compile(r"\.RateTable\.csv$", re.I), "RateTable"),
    (re.compile(r"\.DomainTableDef\.xml$", re.I), "DomainTableDef"),
    (re.compile(r"\.DomainTable\.csv$", re.I), "DomainTable"),
    (re.compile(r"\.Rule\.xml$", re.I), "Rule"),
    (re.compile(r"\.Metadata\.xml$", re.I), "Metadata"),
    (re.compile(r"\.DataDef\.xsd$", re.I), "DataDefXsd"),
    (re.compile(r"\.FormField\.csv$", re.I), "FormFieldCsv"),
    (re.compile(r"\.FormPage\.csv$", re.I), "FormPageCsv"),
    (re.compile(r"\.xlsx$", re.I), "Xlsx"),
    (re.compile(r"\.json$", re.I), "Json"),
]


def kind_of(name: str) -> str:
    for rx, k in KIND_RE:
        if rx.search(name):
            return k
    return "OTHER:" + (Path(name).suffix.lower() or "<noext>")


def main() -> None:
    pkgs = c.find_packages()
    anomalies: list[str] = []
    frows, prows = [], []
    total_files = total_bytes = 0
    seen_key: dict[tuple, list[str]] = defaultdict(list)

    for pk in pkgs:
        if not pk.name_ok:
            anomalies.append(f"NAME: package dir does not match pattern: {pk.rel}")
        seen_key[(pk.juris, pk.edition, pk.version)].append(pk.rel)

        cats_present = {p.name for p in pk.content.iterdir() if p.is_dir()}
        loose = [p.name for p in pk.content.iterdir() if p.is_file()]
        if loose:
            anomalies.append(f"LOOSE: files outside any category in {pk.rel}: {loose[:5]}")
        extra = cats_present - set(c.CATEGORIES)
        if extra:
            anomalies.append(f"EXTRACAT: {pk.rel}: {sorted(extra)}")
        missing = set(c.CATEGORIES) - cats_present
        if missing:
            anomalies.append(f"MISSINGCAT: {pk.rel}: {sorted(missing)}")

        counts = Counter()
        kcounts = Counter()
        pbytes = 0
        pfiles = 0
        for cat in sorted(cats_present):
            for f in sorted((pk.content / cat).rglob("*")):
                if not f.is_file():
                    continue
                sz = f.stat().st_size
                if sz == 0:
                    anomalies.append(f"EMPTY: {pk.rel}/{cat}/{f.name}")
                k = kind_of(f.name)
                counts[cat] += 1
                kcounts[k] += 1
                pbytes += sz
                pfiles += 1
                frows.append((pk.pkg_id, pk.juris, cat, f.name, f.suffix.lower(), k, sz))
        total_files += pfiles
        total_bytes += pbytes
        prows.append(dict(
            pkg_id=pk.pkg_id, juris_dir=pk.juris_dir, juris=pk.juris,
            edition=pk.edition, version=pk.version, dir_name=pk.outer.name,
            wrapped=pk.wrapped, content_dir=pk.content.name,
            name_ok=pk.name_ok, n_files=pfiles, n_bytes=pbytes,
            n_categories=len(cats_present),
            missing_categories=";".join(sorted(missing)),
            **{f"n_{cat.replace(' ', '_')}": counts.get(cat, 0) for cat in c.CATEGORIES},
            **{f"k_{k}": kcounts.get(k, 0) for k in
               ["RateTable", "RateTableDef", "DomainTable", "DomainTableDef",
                "Rule", "Metadata", "DataDefXsd", "FormFieldCsv", "FormPageCsv",
                "Xlsx", "Json"]},
        ))
        # pairing check
        if kcounts["RateTable"] != kcounts["RateTableDef"]:
            anomalies.append(f"PAIR: {pk.rel}: RateTable={kcounts['RateTable']} "
                             f"Def={kcounts['RateTableDef']}")
        if kcounts["DomainTable"] != kcounts["DomainTableDef"]:
            anomalies.append(f"PAIR: {pk.rel}: DomainTable={kcounts['DomainTable']} "
                             f"Def={kcounts['DomainTableDef']}")

    for k, v in seen_key.items():
        if len(v) > 1:
            anomalies.append(f"DUPKEY: {k}: {v}")

    # zip reconciliation
    zips = [z for z in c.ROOT.glob("*/*.zip")
            if z.parent.name not in c.EXCLUDE_DIRS]
    zip_stems = {z.parent.name + "/" + z.stem for z in zips}
    dir_names = {p.juris_dir + "/" + p.outer.name for p in pkgs}
    for z in sorted(zip_stems - dir_names):
        anomalies.append(f"ZIP-NOEXTRACT: {z}.zip has no matching directory")
    no_zip = sorted(dir_names - zip_stems)

    with open(c.OUT / "packages.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(prows[0].keys()))
        w.writeheader()
        w.writerows(prows)
    with open(c.OUT / "files.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["pkg_id", "juris", "category", "filename", "ext", "kind", "bytes"])
        w.writerows(frows)

    # corpus-wide raw counts for reconciliation
    all_files = sum(1 for _ in c.ROOT.rglob("*") if _.is_file())
    all_bytes = sum(f.stat().st_size for f in c.ROOT.rglob("*") if f.is_file())

    lines = []
    A = lines.append
    A(f"packages: {len(pkgs)}")
    A(f"  countrywide: {sum(1 for p in pkgs if p.juris_dir == 'countrywide')}")
    A(f"  state:       {sum(1 for p in pkgs if p.juris_dir != 'countrywide')}")
    A(f"  jurisdiction dirs: {len({p.juris_dir for p in pkgs})}")
    A(f"  wrapped (extra inner dir): {sum(1 for p in pkgs if p.wrapped)}")
    A(f"files inside packages: {total_files}")
    A(f"bytes inside packages: {total_bytes} ({total_bytes/1048576:.1f} MiB)")
    A(f"files anywhere under ROOT: {all_files}  bytes: {all_bytes} "
      f"({all_bytes/1048576:.1f} MiB)")
    A(f"zip archives: {len(zips)}  bytes: {sum(z.stat().st_size for z in zips)}")
    A(f"loose files at ROOT: {[p.name for p in c.ROOT.iterdir() if p.is_file()]}")
    A(f"package dirs with no sibling .zip: {len(no_zip)}")
    for n in no_zip:
        A(f"   NOZIP: {n}")
    A("")
    A(f"kind totals:")
    kt = Counter()
    for r in frows:
        kt[r[5]] += 1
    for k, v in kt.most_common():
        A(f"  {k:20s} {v}")
    A("")
    A(f"ANOMALIES: {len(anomalies)}")
    for a in anomalies:
        A("  " + a)
    (c.OUT / "inventory_summary.txt").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines[:60]))
    print(f"...\n(anomaly count {len(anomalies)}; full text in out/inventory_summary.txt)")


if __name__ == "__main__":
    main()
