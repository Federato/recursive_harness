"""Phase 3 verification: are the declared KeyCols actually a unique key?

The Def files declare <KeyCols> but nothing in the corpus states that the
key is unique. This script tests it empirically: for every Rate Table and
Domain Table CSV that has a Def, it builds the tuple of declared key
columns for each data row and counts duplicates.

Emits out/key_uniqueness.csv (one row per package x table with
n_rows / n_distinct_keys / n_duplicate_keys and an example duplicate) and
out/key_uniqueness.txt with the corpus-wide verdict, broken down by
whether the table declares a <Range> (where the key is an interval and
exact-tuple duplication is expected to be meaningful).

Range-typed key columns are included using their literal _From /
_ToLessThan column names, since that is how they appear in the CSV.
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
csv.field_size_limit(1 << 24)


def check(a):
    pkg_id, juris, content = a
    content = Path(content)
    out = []
    for cat, defsuf, datasuf, kind in [
        ("Rate Tables", ".RateTableDef.xml", ".RateTable.csv", "Rate"),
        ("Domain Tables", ".DomainTableDef.xml", ".DomainTable.csv", "Domain"),
    ]:
        d = content / cat
        if not d.is_dir():
            continue
        for df in sorted(d.glob("*" + defsuf)):
            base = df.name[: -len(defsuf)]
            base = base[:-3] if base.endswith("Def") else base
            cf = d / (base + datasuf)
            if not cf.exists():
                continue
            try:
                root = c.parse_xml(df)
            except Exception:
                continue
            keys, has_range = [], False
            for el in root.iter():
                ln = c.lname(el.tag)
                if ln == "Range":
                    has_range = True
                elif ln == "KeyCol":
                    keys.append(el.get("Name"))
            try:
                hdr, rdr = c.read_csv_rows(cf)
            except Exception:
                continue
            idx = [hdr.index(k) for k in keys if k in hdr]
            if len(idx) != len(keys):
                continue
            seen = Counter()
            n = 0
            for row in rdr:
                n += 1
                seen[tuple(row[i] if i < len(row) else "" for i in idx)] += 1
            dup = sum(v - 1 for v in seen.values() if v > 1)
            ex = ""
            if dup:
                ex = "|".join(next(k for k, v in seen.items() if v > 1))
            out.append((pkg_id, juris, kind, base, has_range, len(keys),
                        n, len(seen), dup, ex[:120]))
    return out


def main():
    pkgs = c.find_packages()
    args = [(p.pkg_id, p.juris, str(p.content)) for p in pkgs]
    rows = []
    with Pool() as pool:
        for o in pool.imap_unordered(check, args, chunksize=2):
            rows.extend(o)
    with open(c.OUT / "key_uniqueness.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["pkg_id", "juris", "kind", "table", "has_range", "n_keycols",
                    "n_rows", "n_distinct_keys", "n_dup_rows", "example_dup_key"])
        w.writerows(rows)

    L = []; A = L.append
    A(f"tables tested (package x table with a Def and a CSV): {len(rows)}")
    A(f"rows tested: {sum(r[6] for r in rows)}")
    bad = [r for r in rows if r[8] > 0]
    A(f"tables where the declared KeyCols are NOT unique: {len(bad)} "
      f"({len(bad)/len(rows)*100:.3f}%)")
    A(f"  of those, declaring a <Range>: {sum(1 for r in bad if r[4])}")
    A(f"  duplicate rows in total: {sum(r[8] for r in bad)}")
    A("")
    A("NON-UNIQUE TABLE NAMES (distinct, with package count)")
    for t, n in Counter(r[3] for r in bad).most_common(30):
        A(f"  {t:52s} {n}")
    A("")
    A("EXAMPLES")
    for r in bad[:15]:
        A(f"  {r[0]} {r[2]}:{r[3]} rows={r[6]} distinct={r[7]} dup={r[8]} "
          f"range={r[4]} key={r[9]}")
    (c.OUT / "key_uniqueness.txt").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L[:60]))


if __name__ == "__main__":
    main()
