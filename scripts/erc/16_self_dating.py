"""Phase 4 step 5: is the corpus self-describing?

Question: if every directory name were stripped away, could each package's
jurisdiction, edition date, version and ordering be reconstructed from its
contents, and with what coverage over the 567 distinct packages?

Seven candidate identity channels are tested independently.  For each, the
script records what it yields and whether it agrees with the directory
name (which is used ONLY as the answer key, never as an input):

  C1 xsd_ns        targetNamespace of the .xsd  -> juris + date + version
  C2 xsd_fname     the .xsd filename MasterGL<XX> -> juris
  C3 doc_fname     the DOC workbook filename DOC-GL-<XX>-MMDDYYYY-V<nn>
                   -> juris + date + version
  C4 stc_scheme    STC SchemeKeys ProductName + EffectiveDateTime
                   -> juris + date
  C5 statecode     the StateCode column of the package's own rate tables
                   -> juris
  C6 meta_fname    the GL<XX>.Metadata.xml filename -> juris
  C7 circ_max      the latest circular effective date cited in
                   Circulars.Metadata.xml -> a LOWER BOUND on the edition

C1 and C4 are true file *content*; C2, C3 and C6 are filenames inside the
package (they survive stripping the directory names but not a flattening);
C5 and C7 are content.  The report separates content-only coverage from
filename-assisted coverage, because the two answer different questions.

Emits out/self_dating.csv (one row per package, all channels) and
out/self_dating.txt (coverage, agreement, and the reconstruction verdict).
"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter, defaultdict
from multiprocessing import Pool
from pathlib import Path
from importlib import import_module

sys.path.insert(0, str(Path(__file__).parent))
c = import_module("00_common")
csv.field_size_limit(1 << 24)

NS_RE = re.compile(r"/erc/GL_([A-Z]{2})_(\d{8})_(V\d+)/")
XSDF_RE = re.compile(r"^MasterGL([A-Z]{2})\.DataDef\.xsd$", re.I)
DOCF_RE = re.compile(r"^DOC[-_]GL[-_]([A-Z]{2})[-_](\d{2})(\d{2})(\d{4})"
                     r"[-_]?(V\d+)?", re.I)
METAF_RE = re.compile(r"^GL([A-Z]{2})\.Metadata\.xml$", re.I)
PROD_RE = re.compile(r"General Liability\s+([A-Z]{2})\s*$")


def scan(a):
    pkg_id, juris, edition, version, content = a
    content = Path(content)
    r = dict(pkg_id=pkg_id, key_juris=juris, key_edition=edition,
             key_version=version)

    # C1 / C2
    xf = next((content / "DataDefs").glob("*.xsd"), None) \
        if (content / "DataDefs").is_dir() else None
    r["xsd_file"] = xf.name if xf else ""
    ns = ""
    if xf:
        try:
            ns = c.parse_xml(xf).get("targetNamespace", "")
        except Exception:
            ns = ""
    m = NS_RE.search(ns + "/")
    r["c1_juris"], r["c1_edition"], r["c1_version"] = (
        (m.group(1), m.group(2), m.group(3)) if m else ("", "", ""))
    m = XSDF_RE.match(xf.name) if xf else None
    r["c2_juris"] = m.group(1).upper() if m else ""

    # C3
    r["c3_juris"] = r["c3_edition"] = r["c3_version"] = ""
    d = content / "DOC"
    if d.is_dir():
        for f in sorted(d.iterdir()):
            m = DOCF_RE.match(f.name)
            if m:
                r["c3_juris"] = m.group(1).upper()
                r["c3_edition"] = f"{m.group(4)}{m.group(2)}{m.group(3)}"
                r["c3_version"] = (m.group(5) or "").upper()
                r["doc_file"] = f.name
                break

    # C4
    r["c4_juris"] = r["c4_edition"] = ""
    d = content / "STC"
    if d.is_dir():
        for f in sorted(d.glob("*.json")):
            try:
                o = json.loads(c.read_text(f))
            except Exception:
                continue
            sk = o.get("SchemeKeys") if isinstance(o, dict) else None
            if not isinstance(sk, dict):
                continue
            pm = PROD_RE.search((sk.get("ProductName") or "").strip())
            if pm:
                r["c4_juris"] = pm.group(1)
            ed = (sk.get("EffectiveDateTime") or "")[:10].replace("-", "")
            if len(ed) == 8:
                r["c4_edition"] = ed
            break

    # C5
    codes = Counter()
    d = content / "Rate Tables"
    if d.is_dir():
        for f in sorted(d.glob("*.RateTable.csv")):
            try:
                hdr, rdr = c.read_csv_rows(f)
            except Exception:
                continue
            if "StateCode" not in hdr:
                continue
            i = hdr.index("StateCode")
            for row in rdr:
                if i < len(row):
                    codes[row[i]] += 1
    non_cw = [k for k in codes if k not in ("CW", "")]
    r["c5_juris"] = (Counter({k: codes[k] for k in non_cw}).most_common(1)[0][0]
                     if non_cw else ("CW" if codes else ""))
    r["c5_all_codes"] = ";".join(f"{k}:{v}" for k, v in codes.most_common(6))

    # C6
    r["c6_juris"] = ""
    d = content / "Metadata"
    if d.is_dir():
        for f in sorted(d.iterdir()):
            m = METAF_RE.match(f.name)
            if m:
                r["c6_juris"] = m.group(1).upper()
                break

    # C7 - latest circular effective date cited
    best = ""
    f = content / "Metadata" / "Circulars.Metadata.xml"
    if f.exists():
        for m in re.finditer(r"Circular Effective Date:\s*(\d{2})/(\d{2})/(\d{4})",
                             c.read_text(f)):
            v = f"{m.group(3)}{m.group(1)}{m.group(2)}"
            best = max(best, v)
    r["c7_max_circular"] = best
    return r


def main():
    pkgs = c.find_packages()
    seen = set()
    args = []
    for p in pkgs:
        if p.pkg_id in seen:
            continue
        seen.add(p.pkg_id)
        args.append((p.pkg_id, p.juris, p.edition, p.version, str(p.content)))
    with Pool() as pool:
        rows = pool.map(scan, args, chunksize=2)

    cols = ["pkg_id", "key_juris", "key_edition", "key_version", "xsd_file",
            "doc_file", "c1_juris", "c1_edition", "c1_version", "c2_juris",
            "c3_juris", "c3_edition", "c3_version", "c4_juris", "c4_edition",
            "c5_juris", "c5_all_codes", "c6_juris", "c7_max_circular"]
    with open(c.OUT / "self_dating.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in sorted(rows, key=lambda x: x["pkg_id"]):
            w.writerow({k: r.get(k, "") for k in cols})

    N = len(rows)
    L = []; A = L.append
    A(f"SELF-DESCRIPTION TEST over {N} distinct packages")
    A("The directory name is used ONLY as the answer key, never as an input.")
    A("")

    def cov(field, key):
        have = sum(1 for r in rows if r.get(field))
        ok = sum(1 for r in rows if r.get(field) and r[field] == r[key])
        bad = [(r["pkg_id"], r[field], r[key]) for r in rows
               if r.get(field) and r[field] != r[key]]
        return have, ok, bad

    A(f"{'channel':28s} {'yields':>7} {'present':>8} {'agrees':>7} {'cov%':>7} {'acc%':>7}")
    CH = [("c1_juris", "key_juris", "C1 xsd targetNamespace", "jurisdiction"),
          ("c1_edition", "key_edition", "C1 xsd targetNamespace", "edition"),
          ("c1_version", "key_version", "C1 xsd targetNamespace", "version"),
          ("c2_juris", "key_juris", "C2 xsd filename", "jurisdiction"),
          ("c3_juris", "key_juris", "C3 DOC filename", "jurisdiction"),
          ("c3_edition", "key_edition", "C3 DOC filename", "edition"),
          ("c3_version", "key_version", "C3 DOC filename", "version"),
          ("c4_juris", "key_juris", "C4 STC SchemeKeys", "jurisdiction"),
          ("c4_edition", "key_edition", "C4 STC SchemeKeys", "edition"),
          ("c5_juris", "key_juris", "C5 StateCode column", "jurisdiction"),
          ("c6_juris", "key_juris", "C6 Metadata filename", "jurisdiction")]
    fails = {}
    for f, k, name, what in CH:
        have, ok, bad = cov(f, k)
        fails[f] = bad
        A(f"{name+' -> '+what:28s} {'':>7} {have:8d} {ok:7d} "
          f"{have/N*100:6.1f}% {ok/have*100 if have else 0:6.1f}%")
    A("")
    for f, k, name, what in CH:
        if fails[f]:
            A(f"  MISMATCHES for {name} -> {what}: {len(fails[f])}")
            for x in fails[f][:8]:
                A(f"    {x[0]}: channel said {x[1]!r}, directory says {x[2]!r}")
    A("")
    A("CONTENT-ONLY reconstruction (C1 + C4 + C5; no filenames used)")
    full = sum(1 for r in rows if r["c1_juris"] and r["c1_edition"] and r["c1_version"])
    A(f"  packages where the xsd targetNamespace alone yields the complete")
    A(f"  (jurisdiction, edition, version) triple: {full}/{N} "
      f"({full/N*100:.1f}%)")
    exact = sum(1 for r in rows
                if (r["c1_juris"], r["c1_edition"], r["c1_version"])
                == (r["key_juris"], r["key_edition"], r["key_version"]))
    A(f"  and it matches the directory name exactly in: {exact}/{N} "
      f"({exact/N*100:.1f}%)")
    A("")
    A("FILENAME-ASSISTED reconstruction (C1 or C3)")
    both = sum(1 for r in rows
               if (r["c1_juris"] and r["c1_edition"])
               or (r["c3_juris"] and r["c3_edition"]))
    A(f"  packages identifiable by xsd namespace OR DOC filename: {both}/{N}")
    agree = [r for r in rows if r["c1_edition"] and r["c3_edition"]]
    dis = [r for r in agree if r["c1_edition"] != r["c3_edition"]]
    A(f"  packages where BOTH are available: {len(agree)}; they disagree in "
      f"{len(dis)}")
    for r in dis[:10]:
        A(f"    {r['pkg_id']}: xsd={r['c1_edition']} doc={r['c3_edition']} "
          f"(doc file {r.get('doc_file','')})")
    A("")
    A("C7  latest circular effective date as a bound on the edition date")
    ok = sum(1 for r in rows if r["c7_max_circular"]
             and r["c7_max_circular"] <= r["key_edition"])
    have = sum(1 for r in rows if r["c7_max_circular"])
    A(f"  packages citing at least one circular: {have}/{N}")
    A(f"  latest cited circular <= edition date: {ok}/{have} "
      f"({ok/have*100:.1f}%)")
    over = sorted([(r["c7_max_circular"], r["key_edition"], r["pkg_id"])
                   for r in rows if r["c7_max_circular"] > r["key_edition"]],
                  reverse=True)
    A(f"  packages citing a circular effective AFTER their own edition date: "
      f"{len(over)}")
    for x in over[:10]:
        A(f"    {x[2]}: edition {x[1]}, cites circular effective {x[0]}")
    A("")
    A("ORDERING")
    A("  Ordering requires (edition, version). Version is available ONLY from")
    A("  C1 (xsd namespace) and C3 (DOC filename); no other channel emits it.")
    dupdates = Counter((r["c1_juris"], r["c1_edition"]) for r in rows
                       if r["c1_juris"])
    ties = {k: v for k, v in dupdates.items() if v > 1}
    A(f"  (jurisdiction, edition) pairs carrying more than one version: "
      f"{len(ties)} covering {sum(ties.values())} packages -- for these the")
    A(f"  version token is REQUIRED to order them, and C1 supplies it.")
    (c.OUT / "self_dating.txt").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
