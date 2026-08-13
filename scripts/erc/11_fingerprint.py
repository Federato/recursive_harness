"""Phase 4 step 1: content fingerprints for every package, so that
consecutive editions can be diffed without re-reading 700 MB each time.

For every package it records:

  out/fp_tables.csv    one row per (package, kind, table):
                       n_rows, sha1 of the *sorted set of data rows*
                       (order-insensitive, BOM/CRLF-normalised), sha1 of the
                       header, and sha1 of the sorted set of key-column
                       tuples (key columns taken from out/table_defs.csv)
  out/fp_rules.csv     one row per (package, rule file): bytes, sha1 of the
                       whitespace-normalised XML text, number of <Rule>
                       elements
  out/fp_form_rows.csv every row of all five Form/Ratebook CSVs in the
                       corpus, with the package, category, a derived row
                       key, the Status column, and a sha1 of the remaining
                       (non-Status, non-key) fields.  ~97k rows/package-set.

Row keys used for the form CSVs (chosen because they are the columns that
identify the artefact rather than describe it):
  Form Pages          (TableName, Name, Number)
  Form Fields         (Page, TableName, ColumnName)
  Form Related Fields (Page, TableName, ColumnName, RelatedField)
  Ratebook Columns    (TableName, ColumnName)
  Ratebook Tables     (TableName)
Key collisions within a single file are counted and reported, because a
colliding key would invalidate the Status analysis in 13_status.py.
"""
from __future__ import annotations

import csv
import hashlib
import sys
from collections import Counter, defaultdict
from multiprocessing import Pool
from pathlib import Path
from importlib import import_module

sys.path.insert(0, str(Path(__file__).parent))
c = import_module("00_common")
csv.field_size_limit(1 << 24)

FORM_KEYS = {
    "Form Pages": ["TableName", "Name", "Number"],
    "Form Fields": ["Page", "TableName", "ColumnName"],
    "Form Related Fields": ["Page", "TableName", "ColumnName", "RelatedField"],
    "Ratebook Columns": ["TableName", "ColumnName"],
    "Ratebook Tables": ["TableName"],
}
FORM_FILE = {
    "Form Pages": "Pages.FormPage.csv",
    "Form Fields": "Fields.FormField.csv",
    "Form Related Fields": "RelatedFields.FormField.csv",
    "Ratebook Columns": "RatebookColumns.FormPage.csv",
    "Ratebook Tables": "RatebookTables.FormPage.csv",
}


def h(items) -> str:
    """sha1 over a sorted, order-insensitive collection of strings."""
    d = hashlib.sha1()
    for x in sorted(items):
        d.update(x.encode("utf-8", "replace"))
        d.update(b"\x00")
    return d.hexdigest()[:16]


def hs(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8", "replace")).hexdigest()[:16]


def scan(a):
    pkg_id, juris, edition, version, content, keymap = a
    content = Path(content)
    tabs, rules, forms = [], [], []
    collisions = Counter()

    for cat, suf, kind in [("Rate Tables", ".RateTable.csv", "Rate"),
                           ("Domain Tables", ".DomainTable.csv", "Domain")]:
        d = content / cat
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*" + suf)):
            table = f.name[: -len(suf)]
            try:
                hdr, rdr = c.read_csv_rows(f)
            except Exception:
                continue
            kcols = keymap.get((kind, table), [])
            idx = [hdr.index(k) for k in kcols if k in hdr]
            rows, keys = [], []
            for r in rdr:
                rows.append("\x1f".join(r))
                if idx:
                    keys.append("\x1f".join(r[i] if i < len(r) else "" for i in idx))
            tabs.append((pkg_id, juris, edition, version, kind, table,
                         len(rows), hs("\x1e".join(hdr)), h(rows),
                         h(keys) if keys else "", len(set(keys)) if keys else -1))

    d = content / "Rules"
    if d.is_dir():
        for f in sorted(d.glob("*.Rule.xml")):
            txt = c.read_text(f)
            norm = " ".join(txt.split())
            rules.append((pkg_id, juris, edition, version,
                          f.name[: -len(".Rule.xml")], f.stat().st_size,
                          hs(norm), norm.count("<rul:Rule ")))

    for cat, fname in FORM_FILE.items():
        f = content / cat / fname
        if not f.exists():
            continue
        try:
            hdr, rdr = c.read_csv_rows(f)
        except Exception:
            continue
        kc = [hdr.index(k) for k in FORM_KEYS[cat] if k in hdr]
        si = hdr.index("Status") if "Status" in hdr else -1
        seen = set()
        for r in rdr:
            key = "\x1f".join(r[i] if i < len(r) else "" for i in kc)
            if key in seen:
                collisions[cat] += 1
            seen.add(key)
            rest = [v for j, v in enumerate(r) if j not in kc and j != si]
            forms.append((pkg_id, juris, edition, version, cat, key,
                          r[si] if 0 <= si < len(r) else "",
                          hs("\x1f".join(rest))))
    return tabs, rules, forms, collisions


def main():
    # key columns per (kind, table), taken from the Defs already parsed
    keymap_all = {}
    with open(c.OUT / "table_defs.csv", encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            k = (r["pkg_id"], r["kind"], r["table"])
            keymap_all[k] = [x for x in r["key_cols"].split("|") if x]

    pkgs = c.find_packages()
    args = []
    for p in pkgs:
        km = {(k[1], k[2]): v for k, v in keymap_all.items() if k[0] == p.pkg_id}
        args.append((p.pkg_id, p.juris, p.edition, p.version, str(p.content), km))

    T = R = F = []
    T, R, F = [], [], []
    coll = Counter()
    done = 0
    with Pool() as pool:
        for t, r, f, cl in pool.imap_unordered(scan, args, chunksize=2):
            T += t; R += r; F += f; coll.update(cl)
            done += 1
            if done % 100 == 0:
                print(f"  {done}/{len(args)}", file=sys.stderr)

    def dump(n, hdr, rows):
        with open(c.OUT / n, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh); w.writerow(hdr); w.writerows(rows)

    dump("fp_tables.csv", ["pkg_id", "juris", "edition", "version", "kind",
                           "table", "n_rows", "header_hash", "rows_hash",
                           "keys_hash", "n_distinct_keys"], T)
    dump("fp_rules.csv", ["pkg_id", "juris", "edition", "version", "rule_file",
                          "bytes", "text_hash", "n_rules"], R)
    dump("fp_form_rows.csv", ["pkg_id", "juris", "edition", "version",
                              "category", "row_key", "status", "payload_hash"], F)
    print(f"fp_tables rows   : {len(T)}")
    print(f"fp_rules rows    : {len(R)}")
    print(f"fp_form_rows rows: {len(F)}")
    print(f"form row-key collisions within a single file: {coll.most_common()}")


if __name__ == "__main__":
    main()
