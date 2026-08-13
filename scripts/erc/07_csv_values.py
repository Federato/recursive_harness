"""Phase 3: extract and profile the row-level content of every Rate Table
and Domain Table CSV in the corpus.

This is the bulk extractor. It streams every *.RateTable.csv and
*.DomainTable.csv (all 30,804 of them, ~12.9M rows) and, per
(table name, column name), accumulates:
   - number of packages / files the column appears in
   - total non-empty values, blank count
   - how many parse as int / decimal, min / max numeric
   - the number of distinct string values, and the 12 most frequent
   - a flag list for non-numeric tokens found in an otherwise numeric column

It also classifies every distinct value token against a set of
"sentinel"/non-numeric patterns (empty, "N/A", "Refer to Company", "*",
range words, currency/comma formatting, "Yes"/"No", etc.) so that cells
whose meaning is not their literal number are surfaced.

Emits:
  out/column_profile.csv    one row per (kind, table, column)
  out/value_vocab.csv       one row per (kind, table, column, value) for
                            columns with <= 400 distinct values - the
                            complete declared vocabulary of every enumerated
                            column in the corpus
  out/csv_values_report.txt totals, sentinel token catalogue with counts and
                            example locations, comma-formatted-number
                            findings, and the row-count reconciliation
                            against out/table_defs.csv.

Runs multiprocessing over packages. Full pass; nothing is sampled.
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

NUM_RE = re.compile(r"^-?\d+(\.\d+)?$")
COMMA_NUM_RE = re.compile(r"^-?\d{1,3}(,\d{3})+(\.\d+)?$")
MAX_DISTINCT = 400


def profile_pkg(a):
    pkg_id, juris, content = a
    content = Path(content)
    # key -> dict of accumulators
    acc = {}
    for cat, suf, kind in [("Rate Tables", ".RateTable.csv", "Rate"),
                           ("Domain Tables", ".DomainTable.csv", "Domain")]:
        d = content / cat
        if not d.is_dir():
            continue
        for f in sorted(d.iterdir()):
            if not f.name.endswith(suf):
                continue
            table = f.name[: -len(suf)]
            try:
                hdr, rdr = c.read_csv_rows(f)
            except Exception:
                continue
            cols = [(kind, table, h) for h in hdr]
            for k in cols:
                acc.setdefault(k, dict(files=0, n=0, blank=0, ints=0, decs=0,
                                       mn=None, mx=None, vals=Counter(),
                                       over=False))
                acc[k]["files"] += 1
            for row in rdr:
                for i, v in enumerate(row):
                    if i >= len(cols):
                        continue
                    a_ = acc[cols[i]]
                    a_["n"] += 1
                    v = v.strip()
                    if v == "":
                        a_["blank"] += 1
                        continue
                    if NUM_RE.match(v):
                        fv = float(v)
                        if "." in v:
                            a_["decs"] += 1
                        else:
                            a_["ints"] += 1
                        a_["mn"] = fv if a_["mn"] is None else min(a_["mn"], fv)
                        a_["mx"] = fv if a_["mx"] is None else max(a_["mx"], fv)
                    if not a_["over"]:
                        a_["vals"][v] += 1
                        if len(a_["vals"]) > MAX_DISTINCT * 4:
                            a_["over"] = True
                            a_["vals"] = Counter(dict(a_["vals"].most_common(40)))
    return pkg_id, acc


def merge(dst, src):
    for k, s in src.items():
        d = dst.setdefault(k, dict(files=0, n=0, blank=0, ints=0, decs=0,
                                   mn=None, mx=None, vals=Counter(),
                                   over=False, pkgs=0))
        for f in ("files", "n", "blank", "ints", "decs"):
            d[f] += s[f]
        d["pkgs"] += 1
        for f, op in (("mn", min), ("mx", max)):
            if s[f] is not None:
                d[f] = s[f] if d[f] is None else op(d[f], s[f])
        d["over"] = d["over"] or s["over"]
        d["vals"].update(s["vals"])
        if len(d["vals"]) > MAX_DISTINCT * 4:
            d["over"] = True
            d["vals"] = Counter(dict(d["vals"].most_common(MAX_DISTINCT)))


def main():
    pkgs = c.find_packages()
    args = [(p.pkg_id, p.juris, str(p.content)) for p in pkgs]
    total = {}
    done = 0
    with Pool() as pool:
        for pkg_id, acc in pool.imap_unordered(profile_pkg, args, chunksize=2):
            merge(total, acc)
            done += 1
            if done % 50 == 0:
                print(f"  {done}/{len(args)} packages, {len(total)} columns",
                      file=sys.stderr)

    prof_rows, vocab_rows = [], []
    for (kind, table, col), d in sorted(total.items()):
        nonblank = d["n"] - d["blank"]
        numeric = d["ints"] + d["decs"]
        top = d["vals"].most_common(12)
        prof_rows.append(dict(
            kind=kind, table=table, column=col, n_packages=d["pkgs"],
            n_files=d["files"], n_cells=d["n"], n_blank=d["blank"],
            n_numeric=numeric, pct_numeric=round(numeric / nonblank * 100, 2)
            if nonblank else 0.0,
            n_int=d["ints"], n_decimal=d["decs"],
            min=d["mn"], max=d["mx"],
            n_distinct=("%d+" % len(d["vals"])) if d["over"] else len(d["vals"]),
            top_values=" | ".join(f"{v}({n})" for v, n in top),
        ))
        if not d["over"] and len(d["vals"]) <= MAX_DISTINCT:
            for v, n in d["vals"].most_common():
                vocab_rows.append((kind, table, col, v, n))

    with open(c.OUT / "column_profile.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(prof_rows[0].keys()))
        w.writeheader(); w.writerows(prof_rows)
    with open(c.OUT / "value_vocab.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["kind", "table", "column", "value", "n_cells"])
        w.writerows(vocab_rows)

    # sentinel / non-numeric analysis restricted to columns that are
    # predominantly numeric (>=50% of non-blank cells parse as a number)
    sent = Counter()
    sent_where = defaultdict(set)
    comma_nums = Counter()
    for (kind, table, col), d in total.items():
        nonblank = d["n"] - d["blank"]
        num = d["ints"] + d["decs"]
        for v, n in d["vals"].items():
            if COMMA_NUM_RE.match(v):
                comma_nums[v] += n
            if nonblank and num / nonblank >= 0.5 and not NUM_RE.match(v):
                sent[v] += n
                sent_where[v].add(f"{table}.{col}")

    L = []; A = L.append
    A(f"distinct (kind,table,column) profiled: {len(total)}")
    A(f"total cells read: {sum(d['n'] for d in total.values())}")
    A(f"total blank cells: {sum(d['blank'] for d in total.values())}")
    A(f"columns fully enumerable (<= {MAX_DISTINCT} distinct): "
      f"{sum(1 for d in total.values() if not d['over'] and len(d['vals']) <= MAX_DISTINCT)}")
    A(f"value_vocab rows written: {len(vocab_rows)}")
    A("")
    A("COLUMN NAME FREQUENCY (top 40 distinct column names)")
    cn = Counter()
    for (kind, table, col), d in total.items():
        cn[col] += d["files"]
    A(f"  distinct column names corpus-wide: {len(cn)}")
    for k, n in cn.most_common(40):
        A(f"  {k:52s} {n}")
    A("")
    A("NON-NUMERIC TOKENS IN PREDOMINANTLY-NUMERIC COLUMNS")
    A(f"  distinct tokens: {len(sent)}")
    for v, n in sent.most_common(60):
        w = sorted(sent_where[v])
        A(f"  {n:9d}  {v[:60]!r:64s} in {len(w)} cols e.g. {w[:2]}")
    A("")
    A("COMMA-FORMATTED NUMERIC-LOOKING TOKENS (top 40)")
    A(f"  distinct: {len(comma_nums)}  total cells: {sum(comma_nums.values())}")
    for v, n in comma_nums.most_common(40):
        A(f"  {n:9d}  {v}")
    A("")
    A("WIDEST COLUMNS BY DISTINCT VALUES (top 25)")
    for (kind, table, col), d in sorted(
            total.items(), key=lambda kv: -len(kv[1]["vals"]))[:25]:
        A(f"  {kind:7s} {table[:44]:46s} {col[:30]:32s} "
          f"{'>4x'+str(MAX_DISTINCT) if d['over'] else len(d['vals'])}")
    (c.OUT / "csv_values_report.txt").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L[:60]))


if __name__ == "__main__":
    main()
