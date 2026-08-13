"""Phase 5 step 1: the composition model in practice.

How does a state override actually take effect, and what would a correct
resolver have to do?

Inputs: out/rules_index.csv, out/rule_refs.csv, out/fp_tables.csv,
        out/xsd_packages.csv, out/xsd_types.csv, out/table_defs.csv

Measures, for every state package against the *specific* countrywide
package its .xsd xs:import names:

  M1 rule provenance vs reality
     cross-tabulates the RuleType* MetadataCode on each <Rule> against
     whether a rule of the same (file, name) exists in the countrywide
     parent.  This tests whether `RuleTypeOverridden` and
     `RuleTypeStateSpecific` are distinct mechanisms or just labels.

  M2 call-super
     for each state rule that shadows a countrywide rule, does its body
     contain a <RunRule ProjectName="GL CW ..."> pointing at the SAME
     file+rule (delegation / call-super) or not (full replacement)?

  M3 table shadowing
     state tables that share a name with a parent table, and whether the
     content differs; plus tables only in state and only in parent.

  M4 type extension
     state complexTypes whose xs:extension base is in the parent
     namespace (prefix "a:"), i.e. schema-level inheritance.

  M5 lookup resolution order
     where a <Lookup> names a table that exists in BOTH the state package
     and the parent, which one would a local-first resolver pick, and how
     often does that choice actually matter (i.e. contents differ)?

Emits out/composition.csv (per-package numbers) and out/composition.txt.
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
    xsd = {r["pkg_id"]: r for r in load("xsd_packages.csv")}
    parent = {p: r["import_pkgs"] for p, r in xsd.items()}
    juris = {p: r["juris"] for p, r in xsd.items()}

    rules = load("rules_index.csv")
    refs = load("rule_refs.csv")
    fpt = load("fp_tables.csv")
    xt = load("xsd_types.csv")

    rule_at = defaultdict(dict)          # pkg -> (file, name) -> rule_type
    for r in rules:
        rt = r["metadata_codes"]
        rule_at[r["pkg_id"]][(r["rule_file"], r["rule_name"])] = rt
    # delegation edges: (pkg, file, name) -> set of (proj, target_file, target_rule)
    deleg = defaultdict(set)
    for r in refs:
        if r["ref_kind"] == "RunRule" and r["project_name"]:
            deleg[(r["pkg_id"], r["rule_file"], r["rule_name"])].add(
                (r["project_name"].replace(" ", "_"), r["target"],
                 r["target_rule"]))
    tab_at = defaultdict(dict)           # pkg -> (kind, table) -> rows_hash
    for r in fpt:
        tab_at[r["pkg_id"]][(r["kind"], r["table"])] = r["rows_hash"]
    ct_base = defaultdict(dict)          # pkg -> complexType -> base
    for r in xt:
        if r["complexType"]:
            ct_base[r["pkg_id"]][r["complexType"]] = r["base"]
    # "Pages" is the engine-provided Form Pages matrix, not a shipped table;
    # it is excluded from the resolution-order measurement (see report 1).
    lookups = defaultdict(Counter)       # pkg -> table -> n lookups
    n_pages_lookups = 0
    for r in refs:
        if r["ref_kind"] != "Lookup":
            continue
        if r["target"] == "Pages":
            n_pages_lookups += 1
            continue
        lookups[r["pkg_id"]][r["target"]] += 1

    M1 = Counter()      # (rule_type, shadows_parent?)
    M2 = Counter()      # (rule_type, delegates_to_same?)
    M2b = Counter()
    M3 = Counter()
    M4 = Counter()
    M5 = Counter()
    prows = []

    states = [p for p in xsd if juris[p] != "CW" and parent.get(p, "").startswith("GL_CW")]
    for p in states:
        par = parent[p]
        pr_rules = rule_at.get(par, {})
        pr_tabs = tab_at.get(par, {})
        row = dict(pkg_id=p, juris=juris[p], parent=par)

        # M1 / M2
        cnt = Counter()
        for (f, n), rt in rule_at.get(p, {}).items():
            shadow = (f, n) in pr_rules
            M1[(rt, shadow)] += 1
            cnt[rt] += 1
            cnt["shadow" if shadow else "novel"] += 1
            d = deleg.get((p, f, n), set())
            same = any(t[0] == par and t[1] == f and t[2] == n for t in d)
            anyd = any(t[0] == par for t in d)
            if shadow:
                M2[(rt, "callsuper_same_rule" if same
                    else ("callsuper_other" if anyd else "replaces"))] += 1
            else:
                M2b[(rt, "delegates" if anyd else "self-contained")] += 1

        # M3
        st, pt = set(tab_at.get(p, {})), set(pr_tabs)
        both = st & pt
        samec = sum(1 for k in both if tab_at[p][k] == pr_tabs[k])
        M3["state_only"] += len(st - pt)
        M3["parent_only"] += len(pt - st)
        M3["shadowed"] += len(both)
        M3["shadowed_identical"] += samec
        row.update(n_rules=len(rule_at.get(p, {})),
                   rules_shadowing=cnt["shadow"], rules_novel=cnt["novel"],
                   rt_system=cnt["RuleTypeSystem"],
                   rt_countrywide=cnt["RuleTypeCountrywide"],
                   rt_statespecific=cnt["RuleTypeStateSpecific"],
                   rt_overridden=cnt["RuleTypeOverridden"],
                   tables_state_only=len(st - pt),
                   tables_shadowed=len(both),
                   tables_shadowed_identical=samec,
                   tables_parent_only=len(pt - st))

        # M4
        for ctn, base in ct_base.get(p, {}).items():
            M4["state_complexTypes"] += 1
            if base.startswith("a:"):
                M4["extends_parent_ns"] += 1
            elif base:
                M4["extends_local"] += 1
            else:
                M4["no_base"] += 1

        # M5
        for t, n in lookups.get(p, {}).items():
            in_s = any(k[1] == t for k in st)
            in_p = any(k[1] == t for k in pt)
            if in_s and in_p:
                sh_s = next(v for k, v in tab_at[p].items() if k[1] == t)
                sh_p = next(v for k, v in pr_tabs.items() if k[1] == t)
                M5["both_" + ("same" if sh_s == sh_p else "differ")] += n
            elif in_s:
                M5["state_only"] += n
            elif in_p:
                M5["parent_only"] += n
            else:
                M5["neither"] += n
        prows.append(row)

    with open(c.OUT / "composition.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(prows[0].keys()))
        w.writeheader(); w.writerows(prows)

    L = []; A = L.append
    A(f"COMPOSITION MODEL - {len(states)} state packages vs the countrywide "
      f"package each one's xs:import names")
    A("")
    A("M1  RuleType tag vs whether a rule of the same (file, name) exists in")
    A("    the countrywide parent")
    A(f"    {'RuleType':26s} {'shadows parent':>15} {'novel':>9} {'total':>9} {'shadow%':>8}")
    for rt in sorted({k[0] for k in M1}):
        s = M1[(rt, True)]; n = M1[(rt, False)]
        A(f"    {rt:26s} {s:15d} {n:9d} {s+n:9d} {s/(s+n)*100:7.1f}%")
    A("")
    A("M2  For state rules that SHADOW a parent rule: does the body call back")
    A("    into the parent (RunRule ProjectName=<parent>)?")
    A(f"    {'RuleType':26s} {'call-super(same)':>17} {'call-super(other)':>18} {'replaces':>10}")
    for rt in sorted({k[0] for k in M2}):
        A(f"    {rt:26s} {M2[(rt,'callsuper_same_rule')]:17d} "
          f"{M2[(rt,'callsuper_other')]:18d} {M2[(rt,'replaces')]:10d}")
    A("")
    A("    For state rules with NO parent counterpart:")
    for rt in sorted({k[0] for k in M2b}):
        A(f"    {rt:26s} delegates={M2b[(rt,'delegates')]:7d} "
          f"self-contained={M2b[(rt,'self-contained')]:7d}")
    A("")
    A("M3  Table shadowing (all state packages summed)")
    for k in ("parent_only", "shadowed", "shadowed_identical", "state_only"):
        A(f"    {k:22s} {M3[k]}")
    A(f"    -> of {M3['shadowed']} shadowed tables, {M3['shadowed_identical']} "
      f"({M3['shadowed_identical']/M3['shadowed']*100:.2f}%) are byte-identical "
      f"to the parent's copy")
    A("")
    A("M4  Schema-level inheritance (state complexTypes)")
    for k, v in M4.most_common():
        A(f"    {k:22s} {v}")
    A("")
    A("M5  Lookup resolution - which copy would a local-first resolver use?")
    A(f"    (excludes {n_pages_lookups} lookups against the engine-provided "
      f"'Pages' matrix)")
    tot = sum(M5.values())
    for k, v in M5.most_common():
        A(f"    {k:22s} {v:8d} ({v/tot*100:5.2f}%)")
    A(f"    -> the local-first choice CHANGES THE ANSWER for "
      f"{M5['both_differ']} of {tot} lookups "
      f"({M5['both_differ']/tot*100:.2f}%); for {M5['both_same']} it is moot.")
    (c.OUT / "composition.txt").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
