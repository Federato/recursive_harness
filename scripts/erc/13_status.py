"""Phase 4 step 3: decode the Status = A / C / D vocabulary empirically.

Nothing in the corpus defines Status.  This script refuses to reason from
the letters and instead tests three falsifiable hypotheses against the
consecutive-edition diff produced by 11_fingerprint.py.

  H-delete  "D means the row is deleted."
            Prediction: a row with Status=D in edition N is ABSENT from
            edition N+1 at a rate far above the base disappearance rate.

  H-added   "A means the row was added in this edition."
            Prediction: a row with Status=A in edition N was ABSENT from
            edition N-1 at a rate far above the base rate for new rows.

  H-changed "C means the row's content changed in this edition."
            Prediction: a row with Status=C in edition N, if present in
            N-1, has a DIFFERENT payload than in N-1, at a rate far above
            the base change rate.

Each hypothesis is scored against its own base rate, so a high raw rate
that merely reflects overall churn cannot be mistaken for evidence.  A
fourth test measures Status *stability*: if Status were a per-edition
change flag it would move (A -> C -> D) as a row ages; if it were a static
classification it would not.

Emits:
  out/status_transitions.csv  full (prev_status -> next_status/ABSENT)
                              contingency table per category
  out/status_report.txt       the three hypothesis tests with base rates,
                              lift, the stability measure, and the verdict
                              plus the share of rows the interpretation
                              would affect.
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


def main():
    with open(c.OUT / "fp_form_rows.csv", encoding="utf-8", newline="") as fh:
        F = list(csv.DictReader(fh))

    # pkg -> cat -> key -> (status, payload)
    idx = defaultdict(lambda: defaultdict(dict))
    meta = {}
    for r in F:
        idx[r["pkg_id"]][r["category"]][r["row_key"]] = (r["status"],
                                                         r["payload_hash"])
        meta[r["pkg_id"]] = (r["juris"], r["edition"], r["version"])

    series = defaultdict(list)
    for pid, (j, e, v) in meta.items():
        series[j].append((e, v, pid))
    for j in series:
        series[j] = sorted(set(series[j]))

    CATS = sorted({r["category"] for r in F})
    trans = defaultdict(Counter)          # cat -> (prev_status, next_state)
    # hypothesis counters
    Hd = defaultdict(Counter)             # cat -> counters
    Ha = defaultdict(Counter)
    Hc = defaultdict(Counter)
    statmix = defaultdict(Counter)

    for j in sorted(series):
        ser = series[j]
        for r in ser:
            for cat in CATS:
                for k, (s, _) in idx[r[2]].get(cat, {}).items():
                    statmix[cat][s] += 1
        for i in range(len(ser) - 1):
            p0, p1 = ser[i][2], ser[i + 1][2]
            for cat in CATS:
                a, b = idx[p0].get(cat, {}), idx[p1].get(cat, {})
                if not a or not b:
                    continue
                # forward: what happens to a row of each status
                for k, (s0, h0) in a.items():
                    if k in b:
                        s1, h1 = b[k]
                        trans[cat][(s0, s1)] += 1
                        Hd[cat]["survived_" + s0] += 1
                        Hd[cat]["survived_all"] += 1
                        if h0 != h1:
                            Hc[cat]["changed_from_" + s0] += 1
                    else:
                        trans[cat][(s0, "ABSENT")] += 1
                        Hd[cat]["gone_" + s0] += 1
                        Hd[cat]["gone_all"] += 1
                    Hd[cat]["total_" + s0] += 1
                    Hd[cat]["total_all"] += 1
                # backward: was a row of each status new in this edition?
                for k, (s1, h1) in b.items():
                    Ha[cat]["total_" + s1] += 1
                    Ha[cat]["total_all"] += 1
                    if k not in a:
                        Ha[cat]["new_" + s1] += 1
                        Ha[cat]["new_all"] += 1
                    else:
                        h0 = a[k][1]
                        Hc[cat]["present_" + s1] += 1
                        Hc[cat]["present_all"] += 1
                        if h0 != h1:
                            Hc[cat]["diff_" + s1] += 1
                            Hc[cat]["diff_all"] += 1

    with open(c.OUT / "status_transitions.csv", "w", newline="",
              encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["category", "prev_status", "next_state", "n"])
        for cat in CATS:
            for (s0, s1), n in sorted(trans[cat].items()):
                w.writerow([cat, s0, s1, n])

    L = []; A_ = L.append
    A_("STATUS VOCABULARY - EMPIRICAL DECODE")
    A_("")
    A_("Corpus-wide Status distribution per category (all editions):")
    for cat in CATS:
        tot = sum(statmix[cat].values())
        A_(f"  {cat:22s} n={tot:7d}  " +
           "  ".join(f"{s or '(blank)'}={n} ({n/tot*100:.1f}%)"
                     for s, n in sorted(statmix[cat].items())))
    A_("")
    A_("=" * 78)
    A_("H-delete: does Status=D predict that the row is gone next edition?")
    A_(f"  {'category':22s} {'D rows':>8} {'D gone':>8} {'D gone%':>9} "
       f"{'base gone%':>11} {'lift':>7}")
    for cat in CATS:
        g = Hd[cat]
        if not g["total_D"]:
            continue
        dr = g["gone_D"] / g["total_D"] * 100
        base = g["gone_all"] / g["total_all"] * 100
        A_(f"  {cat:22s} {g['total_D']:8d} {g['gone_D']:8d} {dr:8.2f}% "
           f"{base:10.2f}% {dr/base if base else 0:6.2f}x")
    A_("")
    A_("  same test for A and C, for comparison:")
    for st in ("A", "C"):
        for cat in CATS:
            g = Hd[cat]
            if not g["total_" + st]:
                continue
            r = g["gone_" + st] / g["total_" + st] * 100
            base = g["gone_all"] / g["total_all"] * 100
            A_(f"    {st}  {cat:22s} gone {r:6.2f}%  (base {base:.2f}%, "
               f"lift {r/base if base else 0:.2f}x)")
    A_("")
    A_("=" * 78)
    A_("H-added: does Status=A mean the row is new in this edition?")
    A_(f"  {'category':22s} {'A rows':>8} {'A new':>8} {'A new%':>9} "
       f"{'base new%':>11} {'lift':>7}")
    for cat in CATS:
        g = Ha[cat]
        if not g["total_A"]:
            continue
        r = g["new_A"] / g["total_A"] * 100
        base = g["new_all"] / g["total_all"] * 100
        A_(f"  {cat:22s} {g['total_A']:8d} {g['new_A']:8d} {r:8.2f}% "
           f"{base:10.2f}% {r/base if base else 0:6.2f}x")
    A_("  same test for C and D:")
    for st in ("C", "D"):
        for cat in CATS:
            g = Ha[cat]
            if not g["total_" + st]:
                continue
            r = g["new_" + st] / g["total_" + st] * 100
            base = g["new_all"] / g["total_all"] * 100
            A_(f"    {st}  {cat:22s} new {r:6.2f}%  (base {base:.2f}%, "
               f"lift {r/base if base else 0:.2f}x)")
    A_("")
    A_("=" * 78)
    A_("H-changed: does Status=C mean the payload changed vs the previous edition?")
    A_(f"  {'category':22s} {'C carried':>10} {'C diff':>8} {'C diff%':>9} "
       f"{'base diff%':>11} {'lift':>7}")
    for cat in CATS:
        g = Hc[cat]
        if not g["present_C"]:
            continue
        r = g["diff_C"] / g["present_C"] * 100
        base = g["diff_all"] / g["present_all"] * 100
        A_(f"  {cat:22s} {g['present_C']:10d} {g['diff_C']:8d} {r:8.2f}% "
           f"{base:10.2f}% {r/base if base else 0:6.2f}x")
    A_("  same test for A and D:")
    for st in ("A", "D"):
        for cat in CATS:
            g = Hc[cat]
            if not g["present_" + st]:
                continue
            r = g["diff_" + st] / g["present_" + st] * 100
            base = g["diff_all"] / g["present_all"] * 100
            A_(f"    {st}  {cat:22s} changed {r:6.2f}%  (base {base:.2f}%, "
               f"lift {r/base if base else 0:.2f}x)")
    A_("")
    A_("=" * 78)
    A_("STATUS STABILITY: for rows carried between consecutive editions,")
    A_("does the Status value move?  (a per-edition change flag would move;")
    A_("a static classification would not)")
    for cat in CATS:
        t = trans[cat]
        carried = sum(n for (s0, s1), n in t.items() if s1 != "ABSENT")
        stable = sum(n for (s0, s1), n in t.items() if s1 == s0)
        A_(f"  {cat:22s} carried {carried:8d}  Status unchanged "
           f"{stable:8d} ({stable/carried*100:.3f}%)")
        moves = sorted(((n, s0, s1) for (s0, s1), n in t.items()
                        if s1 != "ABSENT" and s1 != s0), reverse=True)[:4]
        for n, s0, s1 in moves:
            A_(f"      {s0} -> {s1}: {n}")
    A_("")
    A_("EXPOSURE: share of rows each interpretation would affect")
    for cat in CATS:
        tot = sum(statmix[cat].values())
        d = statmix[cat].get("D", 0)
        A_(f"  {cat:22s} rows with Status=D: {d} of {tot} ({d/tot*100:.1f}%)")
    (c.OUT / "status_report.txt").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
