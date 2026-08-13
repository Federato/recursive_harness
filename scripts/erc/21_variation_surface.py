"""Phase 5 step 4: the state-variation surface.

What varies by jurisdiction and what does not?  Every artefact in the
corpus is classified against the countrywide layer:

  COUNTRYWIDE-ONLY   the artefact exists in countrywide packages and no
                     state package ever ships its own copy
  UNIVERSALLY-STATE  every state package ships it (countrywide may or may
                     not also have it)
  SOMETIMES-OVERRIDDEN  countrywide has it and SOME states shadow it
  STATE-ONLY         only ever appears in state packages, never in
                     countrywide - a jurisdiction-specific artefact

Done for rate tables, domain tables, rule files and rules.  Then the
override *volume* per jurisdiction, so the map shows where the
jurisdiction axis actually bites.

Emits out/variation_tables.csv, out/variation_rules.csv,
out/variation_by_juris.csv and out/variation_surface.txt.
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


def classify(n_cw, n_state, n_state_pkgs, total_state_pkgs):
    if n_cw and not n_state:
        return "countrywide-only"
    if n_cw and n_state_pkgs >= total_state_pkgs:
        return "universally-overridden"
    if n_cw and n_state:
        return "sometimes-overridden"
    if not n_cw and n_state_pkgs >= total_state_pkgs:
        return "universally-state"
    return "state-only"


def main():
    xsd = {r["pkg_id"]: r for r in load("xsd_packages.csv")}
    juris = {p: r["juris"] for p, r in xsd.items()}
    state_pkgs = {p for p in xsd if juris[p] != "CW"}
    cw_pkgs = {p for p in xsd if juris[p] == "CW"}
    NS = len(state_pkgs)

    fpt = load("fp_tables.csv")
    rules = load("rules_index.csv")

    L = []; A = L.append
    A(f"STATE-VARIATION SURFACE  ({NS} state packages, {len(cw_pkgs)} "
      f"countrywide packages, {len({juris[p] for p in state_pkgs})} jurisdictions)")

    for label, recs, keyfn, outfile in [
        ("TABLES", fpt, lambda r: (r["kind"], r["table"]), "variation_tables.csv"),
        ("RULES", rules, lambda r: (r["rule_file"], r["rule_name"]),
         "variation_rules.csv"),
    ]:
        in_cw = defaultdict(set)
        in_st = defaultdict(set)
        st_juris = defaultdict(set)
        hashes = defaultdict(set)
        for r in recs:
            k = keyfn(r)
            p = r["pkg_id"]
            if p in cw_pkgs:
                in_cw[k].add(p)
            elif p in state_pkgs:
                in_st[k].add(p)
                st_juris[k].add(juris[p])
                if "rows_hash" in r:
                    hashes[k].add(r["rows_hash"])
        allk = set(in_cw) | set(in_st)
        cls = Counter()
        rows = []
        for k in sorted(allk):
            cl = classify(len(in_cw[k]), len(in_st[k]), len(in_st[k]), NS)
            cls[cl] += 1
            rows.append([*k, cl, len(in_cw[k]), len(in_st[k]),
                         len(st_juris[k]),
                         ";".join(sorted(st_juris[k]))[:400],
                         len(hashes.get(k, ()))])
        with open(c.OUT / outfile, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow((["kind", "table"] if label == "TABLES"
                        else ["rule_file", "rule_name"]) +
                       ["class", "n_cw_pkgs", "n_state_pkgs", "n_juris",
                        "juris_list", "n_distinct_state_contents"])
            w.writerows(rows)
        A("")
        A(f"{label} - distinct artefacts: {len(allk)}")
        for cl, n in sorted(cls.items(), key=lambda x: -x[1]):
            A(f"    {cl:26s} {n:6d} ({n/len(allk)*100:5.1f}%)")
        A(f"    artefacts in EVERY state package: "
          f"{sum(1 for k in allk if len(in_st[k]) >= NS)}")
        A(f"    artefacts in exactly ONE state package: "
          f"{sum(1 for k in allk if len(in_st[k]) == 1)}")
        A(f"    artefacts in exactly ONE jurisdiction: "
          f"{sum(1 for k in allk if len(st_juris[k]) == 1)}")
        if label == "TABLES":
            A("    most-overridden countrywide tables (n jurisdictions "
              "shipping their own copy):")
            for k in sorted(allk, key=lambda x: -len(st_juris[x]))[:15]:
                if not in_cw[k]:
                    continue
                A(f"      {k[1][:56]:58s} {len(st_juris[k]):3d} juris, "
                  f"{len(hashes.get(k, ()))} distinct contents")
            A("    tables NEVER overridden by any state "
              f"(countrywide-only): {cls['countrywide-only']}")

    # per-jurisdiction override volume
    comp = load("composition.csv")
    A("")
    A("OVERRIDE VOLUME BY JURISDICTION (latest package of each)")
    latest = {}
    ed = {r["pkg_id"]: r for r in load("packages.csv")}
    for r in comp:
        j = r["juris"]
        e = ed.get(r["pkg_id"], {}).get("edition", "")
        if j not in latest or e > latest[j][0]:
            latest[j] = (e, r)
    rows = []
    A(f"    {'juris':6} {'edition':>9} {'rules':>7} {'ovr':>6} {'state':>7} "
      f"{'tbl own':>8} {'tbl ovr':>8} {'tbl inherit':>12}")
    for j in sorted(latest):
        e, r = latest[j]
        rows.append([j, e, r["n_rules"], r["rt_overridden"],
                     r["rt_statespecific"], r["tables_state_only"],
                     r["tables_shadowed"], r["tables_parent_only"]])
        A(f"    {j:6} {e:>9} {r['n_rules']:>7} {r['rt_overridden']:>6} "
          f"{r['rt_statespecific']:>7} {r['tables_state_only']:>8} "
          f"{r['tables_shadowed']:>8} {r['tables_parent_only']:>12}")
    with open(c.OUT / "variation_by_juris.csv", "w", newline="",
              encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["juris", "edition", "n_rules", "rules_overridden",
                    "rules_state_specific", "tables_state_only",
                    "tables_shadowed", "tables_inherited_only"])
        w.writerows(rows)
    ov = sorted((int(r[3]) for r in rows))
    A(f"    overridden rules per jurisdiction: min={ov[0]} "
      f"median={ov[len(ov)//2]} max={ov[-1]}")
    ss = sorted((int(r[4]) for r in rows))
    A(f"    state-specific rules per jurisdiction: min={ss[0]} "
      f"median={ss[len(ss)//2]} max={ss[-1]}")
    (c.OUT / "variation_surface.txt").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
