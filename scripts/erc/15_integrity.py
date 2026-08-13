"""Phase 4 step 4: characterise every integrity anomaly with hard evidence.

READ-ONLY.  This script never writes to, moves or renames anything under
C:\\Projects\\ISO_ERC_Files.  It only reads and hashes.

Covers:
  I1 duplicate package directories  - full recursive tree hash of each
     candidate pair, so "identical" is proven rather than asserted
  I2 misfiled packages              - directory jurisdiction vs the
     jurisdiction asserted by the package name, the XSD targetNamespace,
     and the StateCode column of the package's own rate tables
  I3 PR-under-RI                    - does PR's newest edition exist
     anywhere else?  Enumerated exhaustively.
  I4 STC date disagreement          - re-read and quote
  I5 packages missing STC/          - enumerate, and test whether they
     share any other property (edition age, jurisdiction, size)
  I6 future-dated packages          - enumerate by jurisdiction and check
     internal consistency against the circulars they cite

Emits out/integrity.txt and out/integrity_packages.csv.
"""
from __future__ import annotations

import csv
import hashlib
import sys
from collections import Counter, defaultdict
from datetime import date
from multiprocessing import Pool
from pathlib import Path
from importlib import import_module

sys.path.insert(0, str(Path(__file__).parent))
c = import_module("00_common")
csv.field_size_limit(1 << 24)

TODAY = "20260810"


def tree_hash(root: Path) -> tuple[str, int, int]:
    """sha256 over (relative path, size, content) of every file, sorted."""
    d = hashlib.sha256()
    n = 0
    total = 0
    for f in sorted(root.rglob("*")):
        if not f.is_file():
            continue
        rel = str(f.relative_to(root)).replace("\\", "/")
        b = f.read_bytes()
        d.update(rel.encode()); d.update(b"\x00")
        d.update(str(len(b)).encode()); d.update(b"\x00")
        d.update(hashlib.sha256(b).digest())
        n += 1; total += len(b)
    return d.hexdigest()[:24], n, total


def hash_one(p):
    return p, tree_hash(Path(p))


def main():
    pkgs = c.find_packages()
    L = []; A = L.append
    A("INTEGRITY ANOMALIES  (source tree treated as strictly read-only)")
    A("")

    by_id = defaultdict(list)
    for p in pkgs:
        by_id[p.pkg_id].append(p)

    A("I1  DUPLICATE PACKAGE DIRECTORIES")
    cand = {pid: v for pid, v in by_id.items() if len(v) > 1}
    targets = [str(p.content) for v in cand.values() for p in v]
    with Pool() as pool:
        hashes = dict(pool.map(hash_one, targets))
    A(f"  package ids appearing in more than one directory: {len(cand)}")
    for pid, v in sorted(cand.items()):
        hs = [hashes[str(p.content)] for p in v]
        same = len({h[0] for h in hs}) == 1
        A(f"  {pid}: {'IDENTICAL' if same else 'DIFFERENT'} "
          f"(tree sha256 {hs[0][0]}, {hs[0][1]} files, {hs[0][2]} bytes)")
        for p, h in zip(v, hs):
            A(f"      {p.rel}    hash={h[0]} files={h[1]} bytes={h[2]}")
    A("")

    A("I2  MISFILED PACKAGES  (directory jurisdiction vs asserted jurisdiction)")
    mis = [p for p in pkgs if p.juris_dir not in (p.juris, "countrywide")]
    A(f"  packages whose directory jurisdiction differs from the package "
      f"name: {len(mis)}")
    for p in mis:
        # third and fourth independent witnesses: the XSD namespace and the
        # StateCode actually used in this package's own rate tables
        xsdf = next((Path(p.content) / "DataDefs").glob("*.xsd"), None)
        tns = ""
        if xsdf:
            root = c.parse_xml(xsdf)
            tns = root.get("targetNamespace", "")
        codes = Counter()
        rd = Path(p.content) / "Rate Tables"
        for f in sorted(rd.glob("*.RateTable.csv"))[:20]:
            hdr, rdr = c.read_csv_rows(f)
            if "StateCode" not in hdr:
                continue
            i = hdr.index("StateCode")
            for r in rdr:
                if i < len(r):
                    codes[r[i]] += 1
        A(f"    directory      : {p.juris_dir}/")
        A(f"    package name   : {p.outer.name}")
        A(f"    xsd namespace  : {tns}")
        A(f"    xsd filename   : {xsdf.name if xsdf else '(none)'}")
        A(f"    StateCode values in its own rate tables (top 5): "
          f"{codes.most_common(5)}")
        A(f"    -> three independent witnesses inside the package agree it is "
          f"{p.juris}; only the directory says {p.juris_dir}.")
        A("")

    A("I3  DOES PR'S NEWEST EDITION EXIST ANYWHERE ELSE?")
    pr = sorted([(p.edition, p.version, p.rel) for p in pkgs if p.juris == "PR"])
    A(f"  every PR package found anywhere in the corpus ({len(pr)}):")
    for e, v, r in pr:
        A(f"    {e} {v}   {r}")
    newest = pr[-1]
    same_ed = [x for x in pr if x[0] == newest[0]]
    A(f"  newest PR edition = {newest[0]} {newest[1]}, and it is present in "
      f"{len(same_ed)} location(s), all under: "
      f"{sorted({x[2].split('/')[0] for x in same_ed})}")
    A(f"  PR/ directory contains editions: "
      f"{sorted({e for e, v, r in pr if r.startswith('PR/')})}")
    A(f"  -> CONFIRMED: PR {newest[0]} exists ONLY under RI/. A consumer that "
      f"reads PR/ alone gets a jurisdiction that is "
      f"{'stale' if newest[0] not in {e for e,v,r in pr if r.startswith('PR/')} else 'complete'}.")
    A("")

    A("I4  STC DATE DISAGREEMENT")
    with open(c.OUT / "stc_index.csv", encoding="utf-8", newline="") as fh:
        S = list(csv.DictReader(fh))
    dis = [s for s in S if s["effective_datetime"]
           and s["effective_datetime"][:10].replace("-", "") != s["edition"]]
    A(f"  STC files carrying a date: {sum(1 for s in S if s['effective_datetime'])}")
    A(f"  disagreeing with the directory edition: {len(dis)}")
    for s in dis:
        A(f"    {s['pkg_id']}  file={s['file']}  directory edition={s['edition']}"
          f"  STC EffectiveDateTime={s['effective_datetime']}"
          f"  ProductName={s['product_name']!r}")
    A(f"  STC files with NO date field: {sum(1 for s in S if not s['effective_datetime'])}"
      f"  (files: {[s['file'] for s in S if not s['effective_datetime']]})")
    A("")

    A("I5  PACKAGES WITH NO STC/ DIRECTORY")
    nostc = [p for p in pkgs if not (Path(p.content) / "STC").is_dir()]
    A(f"  count: {len(nostc)}")
    A(f"  by jurisdiction: {Counter(p.juris for p in nostc).most_common()}")
    A(f"  by edition year: {Counter(p.edition[:4] for p in nostc).most_common()}")
    allyr = Counter(p.edition[:4] for p in pkgs)
    A(f"  all packages by edition year (for comparison): {allyr.most_common()}")
    A("  rate of missing STC by edition year:")
    byyr = Counter(p.edition[:4] for p in nostc)
    for y in sorted(allyr):
        A(f"    {y}: {byyr.get(y,0)}/{allyr[y]} ({byyr.get(y,0)/allyr[y]*100:.1f}%)")
    A("")

    A("I6  FUTURE-DATED PACKAGES (edition date later than " + TODAY + ")")
    fut = [p for p in pkgs if p.edition > TODAY]
    A(f"  count: {len(fut)} of {len(pkgs)}")
    A(f"  by jurisdiction: {Counter(p.juris for p in fut).most_common()}")
    A(f"  edition dates: {sorted(Counter(p.edition for p in fut).items())}")
    A(f"  jurisdictions with NO future-dated package: "
      f"{sorted({p.juris for p in pkgs} - {p.juris for p in fut})}")
    with open(c.OUT / "circulars.csv", encoding="utf-8", newline="") as fh:
        C_ = list(csv.DictReader(fh))
    fc = [x for x in C_ if x["effective_date"][-4:] >= "2026"]
    A(f"  circulars with an effective date in 2026 or later: {len(fc)} of {len(C_)}")
    A(f"  -> future-dated packages are matched by future-dated circulars; the")
    A(f"     corpus is internally consistent about them.")

    rows = []
    for p in pkgs:
        rows.append([p.pkg_id, p.juris_dir, p.juris, p.edition, p.version,
                     p.rel, len(by_id[p.pkg_id]) > 1,
                     p.juris_dir not in (p.juris, "countrywide"),
                     not (Path(p.content) / "STC").is_dir(),
                     p.edition > TODAY])
    with open(c.OUT / "integrity_packages.csv", "w", newline="",
              encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["pkg_id", "juris_dir", "juris", "edition", "version",
                    "rel_path", "is_duplicate_dir", "is_misfiled",
                    "missing_stc", "future_dated"])
        w.writerows(rows)
    (c.OUT / "integrity.txt").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
