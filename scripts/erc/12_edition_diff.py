"""Phase 4 step 2: are editions cumulative snapshots or incremental deltas?

Groups packages by the jurisdiction in their *package name* (not their
directory), orders them by (edition date, version), and diffs each
consecutive pair independently for four categories: rate tables, domain
tables, rules and the five form/ratebook CSVs.

The cumulative-vs-delta test.  If each edition were a delta, a later
edition would carry only what changed, so:
    carried_over / previous_total  ->  near 0, and totals would not be
    stable across the series.
If each edition is a full snapshot:
    carried_over / previous_total  ->  near 1, totals stay stable, and
    dropped items are rare and explainable.
Both predictions are measured; the report states which holds and by how
much.

Also measured, because it is the sharper test: **content churn**.  For
artefacts present in both editions, what fraction are byte-identical?  A
delta package would have ~0% unchanged carry-over (it would not re-ship
unchanged content); a snapshot has a high unchanged fraction.

Emits:
  out/edition_pairs.csv   one row per (jurisdiction, consecutive pair,
                          category): counts of added / dropped / carried /
                          carried-identical / carried-changed, and row-count
                          totals on each side
  out/edition_series.csv  one row per package in series order with its
                          per-category totals, so the series can be plotted
  out/edition_diff.txt    the verdict, per category, with the numbers
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
    tabs = load("fp_tables.csv")
    rules = load("fp_rules.csv")
    forms = load("fp_form_rows.csv")

    # package order: dedup identical pkg_ids (the 6 duplicate directories)
    meta = {}
    for r in tabs + rules + forms:
        meta[r["pkg_id"]] = (r["juris"], r["edition"], r["version"])
    series = defaultdict(list)
    for pid, (j, e, v) in meta.items():
        series[j].append((e, v, pid))
    for j in series:
        series[j] = sorted(set(series[j]))

    # artefact -> {pkg_id: content_hash}
    art = defaultdict(lambda: defaultdict(dict))   # cat -> pkg -> name -> hash
    rows = defaultdict(lambda: defaultdict(int))   # cat -> pkg -> total rows
    for r in tabs:
        cat = r["kind"] + " Tables"
        art[cat][r["pkg_id"]][r["table"]] = r["rows_hash"]
        rows[cat][r["pkg_id"]] += int(r["n_rows"])
    for r in rules:
        art["Rules"][r["pkg_id"]][r["rule_file"]] = r["text_hash"]
        rows["Rules"][r["pkg_id"]] += int(r["n_rules"])
    for r in forms:
        art[r["category"]][r["pkg_id"]][r["row_key"]] = r["payload_hash"]
        rows[r["category"]][r["pkg_id"]] += 1

    CATS = ["Rate Tables", "Domain Tables", "Rules", "Form Pages",
            "Form Fields", "Form Related Fields", "Ratebook Columns",
            "Ratebook Tables"]

    pair_rows, series_rows = [], []
    agg = defaultdict(Counter)
    for j in sorted(series):
        ser = series[j]
        for (e, v, pid) in ser:
            series_rows.append([j, e, v, pid] +
                               [len(art[cat].get(pid, {})) for cat in CATS] +
                               [rows[cat].get(pid, 0) for cat in CATS])
        for i in range(len(ser) - 1):
            (e0, v0, p0), (e1, v1, p1) = ser[i], ser[i + 1]
            for cat in CATS:
                a, b = art[cat].get(p0, {}), art[cat].get(p1, {})
                if not a and not b:
                    continue
                ka, kb = set(a), set(b)
                carried = ka & kb
                same = sum(1 for k in carried if a[k] == b[k])
                pair_rows.append([j, p0, p1, e0, e1, cat, len(ka), len(kb),
                                  len(kb - ka), len(ka - kb), len(carried),
                                  same, len(carried) - same,
                                  rows[cat].get(p0, 0), rows[cat].get(p1, 0)])
                g = agg[cat]
                g["pairs"] += 1
                g["prev"] += len(ka); g["next"] += len(kb)
                g["added"] += len(kb - ka); g["dropped"] += len(ka - kb)
                g["carried"] += len(carried)
                g["same"] += same; g["changed"] += len(carried) - same
                if len(ka - kb) == 0:
                    g["pairs_no_drop"] += 1
                if same == len(carried) and len(kb - ka) == 0 and len(ka - kb) == 0:
                    g["pairs_identical"] += 1

    with open(c.OUT / "edition_pairs.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["juris", "prev_pkg", "next_pkg", "prev_edition",
                    "next_edition", "category", "n_prev", "n_next", "added",
                    "dropped", "carried", "carried_identical",
                    "carried_changed", "prev_rows", "next_rows"])
        w.writerows(pair_rows)
    with open(c.OUT / "edition_series.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["juris", "edition", "version", "pkg_id"] +
                   [f"n_{x}" for x in CATS] + [f"rows_{x}" for x in CATS])
        w.writerows(series_rows)

    L = []; A = L.append
    A("CUMULATIVE vs DELTA — consecutive-edition diff")
    A(f"jurisdictions: {len(series)}   packages in series: {sum(len(v) for v in series.values())}")
    A(f"consecutive pairs: {sum(len(v)-1 for v in series.values())}")
    A("")
    A(f"{'category':22s} {'pairs':>6} {'prev':>8} {'next':>8} {'added':>7} "
      f"{'dropped':>8} {'carried':>8} {'identical':>10} {'changed':>8} "
      f"{'carry%':>7} {'ident%':>7}")
    for cat in CATS:
        g = agg[cat]
        if not g["pairs"]:
            continue
        carry = g["carried"] / g["prev"] * 100 if g["prev"] else 0
        ident = g["same"] / g["carried"] * 100 if g["carried"] else 0
        A(f"{cat:22s} {g['pairs']:6d} {g['prev']:8d} {g['next']:8d} "
          f"{g['added']:7d} {g['dropped']:8d} {g['carried']:8d} "
          f"{g['same']:10d} {g['changed']:8d} {carry:6.2f}% {ident:6.2f}%")
    A("")
    A("PREDICTIONS")
    A("  delta model      -> carry% near 0, and totals shrink along the series")
    A("  snapshot model   -> carry% near 100, identical% high, drops rare")
    A("")
    for cat in CATS:
        g = agg[cat]
        if not g["pairs"]:
            continue
        A(f"  {cat:22s} pairs with zero drops: {g['pairs_no_drop']}/{g['pairs']} "
          f"({g['pairs_no_drop']/g['pairs']*100:.1f}%);  "
          f"pairs completely unchanged: {g['pairs_identical']}/{g['pairs']} "
          f"({g['pairs_identical']/g['pairs']*100:.1f}%)")
    A("")
    A("SERIES STABILITY — does the artefact count shrink over a jurisdiction's series?")
    for cat in ("Rate Tables", "Rules", "Form Pages"):
        up = down = flat = 0
        for j in series:
            ser = series[j]
            for i in range(len(ser) - 1):
                a = len(art[cat].get(ser[i][2], {}))
                b = len(art[cat].get(ser[i + 1][2], {}))
                up += b > a; down += b < a; flat += b == a
        A(f"  {cat:16s} grew {up}  shrank {down}  unchanged {flat}")
    A("")
    A("FIRST vs LAST edition of each jurisdiction (Rate Tables)")
    A(f"  {'juris':6} {'first':>8} {'last':>8} {'first_n':>8} {'last_n':>7} "
      f"{'kept':>6} {'first_rows':>11} {'last_rows':>10}")
    for j in sorted(series):
        f_, l_ = series[j][0], series[j][-1]
        a = art["Rate Tables"].get(f_[2], {}); b = art["Rate Tables"].get(l_[2], {})
        A(f"  {j:6} {f_[0]:>8} {l_[0]:>8} {len(a):8d} {len(b):7d} "
          f"{len(set(a) & set(b)):6d} {rows['Rate Tables'].get(f_[2],0):11d} "
          f"{rows['Rate Tables'].get(l_[2],0):10d}")
    A("")
    A("LARGEST TABLE DROPS between consecutive editions (top 20)")
    drops = sorted([r for r in pair_rows if r[9] > 0 and "Table" in r[5]],
                   key=lambda r: -r[9])[:20]
    for r in drops:
        A(f"  {r[0]} {r[3]}->{r[4]} {r[5]}: dropped {r[9]} of {r[6]} "
          f"(added {r[8]})")
    (c.OUT / "edition_diff.txt").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L[:60]))


if __name__ == "__main__":
    main()
