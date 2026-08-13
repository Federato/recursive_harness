#!/usr/bin/env python3
"""iso-erc-expert retrieval CLI.

Answers questions about the ISO ERC General Liability corpus from the
structured knowledge base in ../knowledge/, without rescanning the 700 MB
source tree.  Python standard library only.

    python erc.py <subcommand> [args] [--json]

Subcommands
    identity   <package-id|jurisdiction>   package identity and lineage
    asof       <jurisdiction> <YYYY-MM-DD> what was in force on a date
    juris      <jurisdiction>              jurisdiction profile
    table      <name>                      resolve a table through the
                                           override chain
    rule       <name-or-prefix>            rule / lifecycle information
    territory  [jurisdiction]              geographic rating profile
    coverage   [jurisdiction]              sublines and coverage counts
    premium                                the premium chain and what rates
    invariants [--severity S] [--id ID]    the invariant register
    corpus                                 headline counts
    resolve    <jurisdiction> <date>       the full resolver plan

Every answer carries a `source` naming the knowledge file and, where the
underlying evidence is a corpus file, the ERC path that authorises it.
Exit code 0 on success, 2 on "not found", 3 on bad usage.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

KB = Path(__file__).resolve().parent.parent / "knowledge"
_cache: dict[str, dict] = {}


def kb(name: str) -> dict:
    if name not in _cache:
        p = KB / f"{name}.json"
        if not p.exists():
            die(f"knowledge file missing: {p}", 3)
        with open(p, encoding="utf-8") as fh:
            _cache[name] = json.load(fh)
    return _cache[name]


def die(msg: str, code: int = 2):
    print(f"error: {msg}", file=sys.stderr)
    raise SystemExit(code)


def out(obj, as_json: bool, lines=None):
    if as_json:
        print(json.dumps(obj, indent=1, sort_keys=False))
    else:
        for ln in (lines or []):
            print(ln)
    return 0


def parse_date(s: str) -> str:
    try:
        y, m, d = s.split("-")
        date(int(y), int(m), int(d))
    except Exception:
        die(f"bad date {s!r}; expected YYYY-MM-DD", 3)
    return f"{y}{m}{d}"


# --------------------------------------------------------------- identity
def cmd_identity(a):
    P = kb("packages")["packages"]
    key = a.target.upper()
    if key in P:
        hits = {key: P[key]}
    else:
        hits = {k: v for k, v in P.items() if v["jurisdiction"] == key}
    if not hits:
        die(f"no package or jurisdiction matching {a.target!r}")
    obj = {"query": a.target, "n_matches": len(hits), "packages": hits,
           "source": "knowledge/packages.json",
           "authority": "identity is the XSD targetNamespace "
                        "(DataDefs/*.xsd), never the directory path "
                        "[ERC-ID-001]"}
    L = [f"{len(hits)} package(s) matching {a.target!r}",
         "identity source: XSD targetNamespace [ERC-ID-001]", ""]
    for k, v in sorted(hits.items(), key=lambda x: x[1]["edition"]):
        L.append(f"  {k}")
        L.append(f"    jurisdiction   {v['jurisdiction']}")
        L.append(f"    edition        {v['edition_date']}  version {v['version']}")
        L.append(f"    parent (import) {v['parent_package_id'] or v['xsd_import']}")
        L.append(f"    targetNamespace {v['xsd_target_ns']}")
        L.append(f"    content        {v['n_rate_tables']} rate tables, "
                 f"{v['n_domain_tables']} domain tables, {v['n_rules']} rules, "
                 f"{v['n_files']} files")
        if v["duplicate_dirs"]:
            L.append(f"    !! this package id occupies {len(v['source_dirs'])} "
                     f"byte-identical directories [ERC-ID-002]")
        L.append(f"    directories    {', '.join(v['source_dirs'])}")
    return out(obj, a.json, L)


# ------------------------------------------------------------------- asof
def _asof(juris: str, edition: str):
    J = kb("jurisdictions")["jurisdictions"]
    if juris not in J:
        die(f"unknown jurisdiction {juris!r}; known: {', '.join(sorted(J))}")
    eds = [e for e in J[juris]["editions"] if e["edition"] <= edition]
    return J[juris], (eds[-1] if eds else None), len(J[juris]["editions"]) - len(eds)


def cmd_asof(a):
    ed = parse_date(a.date)
    j = a.jurisdiction.upper()
    prof, sel, n_future = _asof(j, ed)
    P = kb("packages")["packages"]
    if sel is None:
        obj = {"jurisdiction": j, "as_of": a.date, "in_force": None,
               "reason": "no package with an edition date on or before this "
                         "date", "first_edition": prof["first_edition"],
               "source": "knowledge/jurisdictions.json"}
        return out(obj, a.json,
                   [f"{j} as of {a.date}: NOTHING IN FORCE",
                    f"  first edition is {prof['first_edition']}"]) or 2
    pk = P[sel["package_id"]]
    obj = {"jurisdiction": j, "as_of": a.date,
           "in_force": {**sel, "parent_package_id": pk["parent_package_id"]},
           "n_future_dated_editions_excluded": n_future,
           "rule": "select the newest edition <= the rating date; never max() "
                   "[ERC-ED-001: 83 of 572 packages are future-effective]",
           "source": "knowledge/jurisdictions.json"}
    L = [f"{j} as of {a.date}",
         f"  in force      {sel['package_id']}",
         f"  edition       {sel['edition']}  version {sel['version']}",
         f"  countrywide   {pk['parent_package_id']}",
         f"  excluded      {n_future} later edition(s) not yet effective",
         "  [ERC-ED-001] selection is as-of, never latest"]
    return out(obj, a.json, L)


# ------------------------------------------------------------------ juris
def cmd_juris(a):
    J = kb("jurisdictions")["jurisdictions"]
    j = a.jurisdiction.upper()
    if j not in J:
        die(f"unknown jurisdiction {j!r}; known: {', '.join(sorted(J))}")
    v = J[j]
    obj = {"jurisdiction": j, **v, "source": "knowledge/jurisdictions.json",
           "caveat": "sublines and coverages are RESOLVED through the "
                     "countrywide parent [ERC-CMP-006]"}
    o = v["latest_override_profile"] or {}
    t = v["territory"]
    L = [f"{j}: {v['n_packages']} packages, {v['first_edition']} .. "
         f"{v['latest_edition']}",
         f"  latest        {v['latest_package_id']}  parent {v['latest_parent']}",
         f"  sublines ({v['n_resolved_sublines']}, resolved):"]
    L += [f"      - {s}" for s in v["resolved_sublines"]]
    L += [f"  territory     {t['n_distinct_codes']} codes; "
          f"ZIP map: {'yes' if t['has_zip_map'] else 'NO [ERC-TER-001]'}"]
    if o:
        L += [f"  overrides     {o['rules_overridden']} rules overridden, "
              f"{o['rules_state_specific']} state-specific, of "
              f"{o['n_rules']} total",
              f"  tables        {o['tables_state_only']} state-only, "
              f"{o['tables_shadowed']} shadowing countrywide, "
              f"{o['tables_inherited_only']} inherited only"]
    return out(obj, a.json, L)


# ------------------------------------------------------------------ table
def cmd_table(a):
    C = kb("table_catalogue")
    T = C["tables"]
    q = a.name.lower()
    hits = {k: v for k, v in T.items() if q in v["table"].lower()}
    if not hits:
        die(f"no table matching {a.name!r}")
    exact = {k: v for k, v in hits.items() if v["table"].lower() == q}
    if exact:
        hits = exact
    obj = {"query": a.name, "n_matches": len(hits), "tables": hits,
           "source": "knowledge/table_catalogue.json",
           "resolution": "state copy replaces the countrywide copy wholesale; "
                         "never merge rows [ERC-CMP-004]"}
    L = [f"{len(hits)} table(s) matching {a.name!r}", ""]
    for k, v in sorted(hits.items())[:25]:
        L.append(f"  {v['kind']}:{v['table']}")
        L.append(f"    variation    {v['variation_class']}   shape {v['shape']}")
        L.append(f"    keys         {' | '.join(v['key_cols']) or '(none)'}")
        L.append(f"    values       {' | '.join(v['value_cols']) or '(none)'}")
        L.append(f"    countrywide  {v['n_countrywide_packages']} package(s)")
        L.append(f"    state copies {v['n_state_packages']} package(s) in "
                 f"{v['n_jurisdictions']} jurisdiction(s), "
                 f"{v['n_distinct_state_contents']} distinct contents")
        if v["variation_class"] == "countrywide-only":
            L.append("    -> inherited by every jurisdiction; never overridden")
        elif v["variation_class"] == "universally-overridden":
            L.append("    -> EVERY jurisdiction ships its own copy; the "
                     "countrywide copy is never used")
        elif v["variation_class"] == "state-only":
            L.append("    -> exists only in state packages")
        else:
            L.append("    -> resolve state-first; if absent, inherit "
                     "countrywide [ERC-CMP-005]")
        L.append("")
    if len(hits) > 25:
        L.append(f"  ... {len(hits)-25} more (use --json for all)")
    return out(obj, a.json, L)


# ------------------------------------------------------------------- rule
def cmd_rule(a):
    R = kb("rule_model")
    q = a.name.lower()
    life = [n for n in R["lifecycle_names"] if q in n.lower()]
    ops = {k: v for k, v in R["operators"].items() if q in k.lower()}
    entry = [e for e in R["entry_points"] if q in e.lower()]
    if not (life or ops or entry) and q not in ("", "all"):
        obj = {"query": a.name, "found": False,
               "note": "not a lifecycle rule name, entry point or operator. "
                       "The knowledge base indexes the rule MODEL, not every "
                       "one of the 114,726 rule elements.",
               "source": "knowledge/rule_model.json", "verdict": "unverifiable"}
        return out(obj, a.json,
                   [f"{a.name!r}: not in the rule model index.",
                    "  the KB holds the model (entry points, lifecycle, 52 "
                    "operators), not every rule instance.",
                    "  verdict: unverifiable from the knowledge base — "
                    "rescan the corpus to answer."]) or 2
    obj = {"query": a.name, "matching_lifecycle_rules": life,
           "matching_entry_points": entry, "matching_operators": ops,
           "model": {k: R[k] for k in
                     ("entry_points", "file_to_group", "call_graph",
                      "top_level_sequence", "leaf_rate_sequence",
                      "n_rule_elements", "n_datadef_groups")},
           "source": "knowledge/rule_model.json"}
    L = [f"rule query {a.name!r}"]
    if entry:
        L += ["  entry points:"] + [f"    {e}" for e in entry]
    if life:
        L += ["  lifecycle rules:"] + [f"    {n}" for n in life]
    if ops:
        L += ["  operators:"] + [f"    {k}  x{v}" for k, v in
                                 sorted(ops.items(), key=lambda x: -x[1])]
    L += ["", f"  organisation: {R['file_to_group']}",
          f"  call graph: acyclic={R['call_graph']['acyclic']}, "
          f"max depth {R['call_graph']['max_depth']}",
          "  [ERC-CMP-003] RunRule@ProjectName dispatches to the PARENT, "
          "bypassing the overlay"]
    return out(obj, a.json, L)


# -------------------------------------------------------------- territory
def cmd_territory(a):
    T = kb("territory")
    if a.jurisdiction:
        j = a.jurisdiction.upper()
        if j not in T["jurisdictions"]:
            die(f"unknown jurisdiction {j!r}")
        v = T["jurisdictions"][j]
        sch = v.get("scheme", "ZIP_TABLE")
        obj = {"jurisdiction": j, **v, "mechanism": T["mechanism"],
               "source": "knowledge/territory.json"}
        L = [f"{j} territory profile", f"  scheme         {sch}"]
        if sch == "SINGLE_TERRITORY":
            L += [f"  territory      {v['rating_territory']} (entire state)",
                  "  ZIP map        not needed - one rating territory only",
                  f"  RESOLVED: every risk rates at territory "
                  f"{v['rating_territory']}; Prod/CompOps at 999 [ERC-TER-001]"]
        elif sch == "COUNTY_PLACE":
            L += [f"  territories    {v['n_rating_territories']} codes via "
                  f"{v['n_place_names']} county/place names",
                  "  ZIP map        none - this jurisdiction keys on place, not ZIP",
                  "  INPUT NEEDED: resolve the risk address to a county/place "
                  "name [OI-34].",
                  "           An unmatched place must REFER - never fuzzy-match."]
        else:
            L += [f"  territories    {v['n_distinct_codes']} codes",
                  f"  ZIP map        yes, {v['n_zip_rows']} rows",
                  "  RESOLVED: look up the risk ZIP in "
                  "DomainTerritoryCodeByZipCode [ERC-TER-001]"]
        return out(obj, a.json, L)
    obj = {**T, "source": "knowledge/territory.json"}
    L = ["territory mechanism:"] + [f"  {i+1}. {m}" for i, m in
                                    enumerate(T["mechanism"])]
    L += ["", f"  jurisdictions with a ZIP map:    {T['n_with_zip_map']}",
          f"  jurisdictions WITHOUT a ZIP map: {T['n_without_zip_map']} "
          f"(20 single-territory, 4 county/place) [ERC-TER-001]",
          f"  distinct ZIP values: {T['n_distinct_zipcodes']} "
          f"(+ sentinel {T['zipcode_sentinel']!r})",
          f"  ProdsCompldOpsTerr is degenerate: only value "
          f"{T['prodscompldopsterr_degenerate']['only_value']!r} "
          f"[ERC-TER-002]",
          "", "  no ZIP map in: " + ", ".join(
              sorted(k for k, v in T["jurisdictions"].items()
                     if not v["has_zip_map"]))]
    return out(obj, a.json, L)


# --------------------------------------------------------------- coverage
def cmd_coverage(a):
    J = kb("jurisdictions")["jurisdictions"]
    if a.jurisdiction:
        j = a.jurisdiction.upper()
        if j not in J:
            die(f"unknown jurisdiction {j!r}")
        v = J[j]
        obj = {"jurisdiction": j,
               "resolved_sublines": v["resolved_sublines"],
               "n_resolved_sublines": v["n_resolved_sublines"],
               "source": "knowledge/jurisdictions.json",
               "caveat": "RESOLVED through the countrywide parent; the state "
                         "package alone would show far fewer [ERC-CMP-006]"}
        return out(obj, a.json,
                   [f"{j}: {v['n_resolved_sublines']} sublines (resolved)"] +
                   [f"    - {s}" for s in v["resolved_sublines"]])
    allsubs = {}
    for j, v in J.items():
        for s in v["resolved_sublines"]:
            allsubs.setdefault(s, []).append(j)
    obj = {"n_sublines": len(allsubs),
           "sublines": {s: {"n_jurisdictions": len(v),
                            "jurisdictions": sorted(v),
                            "absent_from": sorted(set(J) - set(v))}
                        for s, v in allsubs.items()},
           "source": "knowledge/jurisdictions.json"}
    L = [f"{len(allsubs)} sublines, resolved across {len(J)} jurisdictions", ""]
    for s, v in sorted(allsubs.items(), key=lambda x: -len(x[1])):
        miss = sorted(set(J) - set(v))
        L.append(f"  {len(v):2d}/{len(J)}  {s}" +
                 (f"   absent: {' '.join(miss)}" if miss and len(miss) <= 45
                  else (f"   present only in: {' '.join(sorted(v))}"
                        if len(v) <= 10 else "")))
    return out(obj, a.json, L)


# ---------------------------------------------------------------- premium
def cmd_premium(a):
    R = kb("rating")
    obj = {**R, "source": "knowledge/rating.json"}
    L = ["THE PREMIUM CHAIN (derived from 73,990 dataflow edges)", ""]
    for k, v in R["premium_chain"].items():
        L.append(f"  {k:26s} = {v}")
    w = R["premium_writers"]
    L += ["", f"WHAT ACTUALLY RATES [ERC-RAT-001]",
          f"  {w['total_tables']} schema tables write a Premium",
          f"  {w['capture_manualpremium']} ({w['capture_manualpremium']/w['total_tables']*100:.1f}%) "
          f"capture a user-entered ManualPremium",
          f"  {w['rated_from_rates']} ({w['rated_from_rates']/w['total_tables']*100:.1f}%) "
          f"compute a premium from rates",
          f"  {w['other_mixed']} other/mixed", "",
          "  the rated core:"]
    L += [f"    - {t}" for t in R["rating_tables"]]
    L += ["", "BLOCKER [ERC-RAT-002]: rounding mode is undefined anywhere in "
          "the corpus (7,682 @DecimalPlaces declarations).",
          "  No premium from this content can be asserted correct to the cent.",
          "", "refer-to-company triggers:"]
    L += [f"    - {t}" for t in R["refer_to_company"]["triggers"]]
    return out(obj, a.json, L)


# ------------------------------------------------------------- invariants
def cmd_invariants(a):
    I = kb("invariants")
    inv = I["invariants"]
    if a.id:
        inv = [x for x in inv if x["id"].upper() == a.id.upper()]
        if not inv:
            die(f"no invariant with id {a.id!r}")
    if a.severity:
        inv = [x for x in inv if x["severity"].upper() == a.severity.upper()]
    obj = {"n": len(inv), "invariants": inv,
           "source": "knowledge/invariants.json"}
    L = [f"{len(inv)} invariant(s)", ""]
    for x in inv:
        L.append(f"  [{x['severity']:7s}] {x['id']}  {x['title']}")
        if a.verbose or a.id:
            L.append(f"      statement: {x['statement']}")
            L.append(f"      evidence : {x['evidence']}")
            L.append(f"      check    : {x['check']}")
            if x.get("impact_if_wrong"):
                L.append(f"      impact   : {x['impact_if_wrong']}")
            L.append("")
    return out(obj, a.json, L)


# ----------------------------------------------------------------- corpus
def cmd_corpus(a):
    C = kb("corpus")
    obj = {**C, "source": "knowledge/corpus.json"}
    L = ["ISO ERC General Liability corpus"]
    for k, v in C.items():
        if k.startswith("_") or k == "reports":
            continue
        L.append(f"  {k:24s} {v}")
    return out(obj, a.json, L)


# ---------------------------------------------------------------- resolve
def cmd_resolve(a):
    ed = parse_date(a.date)
    j = a.jurisdiction.upper()
    prof, sel, n_future = _asof(j, ed)
    if sel is None:
        die(f"no {j} package in force as of {a.date} "
            f"(first edition {prof['first_edition']})")
    P = kb("packages")["packages"]
    pk = P[sel["package_id"]]
    parent = pk["parent_package_id"]
    par = P.get(parent, {})
    steps = kb("composition")["resolver_rules"]
    obj = {"jurisdiction": j, "as_of": a.date,
           "state_package": sel["package_id"],
           "countrywide_package": parent,
           "layer_sizes": {
               "state_rate_tables": pk["n_rate_tables"],
               "state_domain_tables": pk["n_domain_tables"],
               "state_rules": pk["n_rules"],
               "countrywide_rate_tables": par.get("n_rate_tables"),
               "countrywide_domain_tables": par.get("n_domain_tables"),
               "countrywide_rules": par.get("n_rules")},
           "override_profile": prof["latest_override_profile"]
           if sel["package_id"] == prof["latest_package_id"] else None,
           "resolver_rules": steps,
           "both_layers_must_stay_addressable": True,
           "reason": "RunRule@ProjectName dispatches to the parent, bypassing "
                     "the overlay [ERC-CMP-003]",
           "source": "knowledge/packages.json + knowledge/composition.json"}
    L = [f"RESOLVER PLAN — {j} as of {a.date}", "",
         f"  1. state package      {sel['package_id']}  "
         f"(edition {sel['edition']} {sel['version']})",
         f"  2. countrywide parent {parent}  (from the single xs:import)",
         f"  3. layer sizes        state {pk['n_rate_tables']} rate / "
         f"{pk['n_domain_tables']} domain / {pk['n_rules']} rules",
         f"                        cw    {par.get('n_rate_tables')} rate / "
         f"{par.get('n_domain_tables')} domain / {par.get('n_rules')} rules",
         f"  4. overlay countrywide then state, by name, state wins, "
         f"no row merging",
         f"  5. KEEP BOTH LAYERS ADDRESSABLE — ProjectName dispatch needs the "
         f"parent's copy",
         f"  6. entry points: GeneralLiabilityRules/ErcProcess then "
         f"/ErcCalculateTotalPremium", "",
         "  resolver rules:"]
    L += [f"    {s}" for s in steps]
    return out(obj, a.json, L)


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="erc.py", description="ISO ERC General Liability retrieval CLI")
    p.add_argument("--json", action="store_true", help="emit JSON")
    # --json is accepted either before or after the subcommand
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true", help="emit JSON")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add(name):
        return sub.add_parser(name, parents=[common])

    s = add("identity"); s.add_argument("target"); s.set_defaults(f=cmd_identity)
    s = add("asof"); s.add_argument("jurisdiction"); s.add_argument("date"); s.set_defaults(f=cmd_asof)
    s = add("juris"); s.add_argument("jurisdiction"); s.set_defaults(f=cmd_juris)
    s = add("table"); s.add_argument("name"); s.set_defaults(f=cmd_table)
    s = add("rule"); s.add_argument("name"); s.set_defaults(f=cmd_rule)
    s = add("territory"); s.add_argument("jurisdiction", nargs="?"); s.set_defaults(f=cmd_territory)
    s = add("coverage"); s.add_argument("jurisdiction", nargs="?"); s.set_defaults(f=cmd_coverage)
    s = add("premium"); s.set_defaults(f=cmd_premium)
    s = add("invariants")
    s.add_argument("--severity"); s.add_argument("--id")
    s.add_argument("-v", "--verbose", action="store_true"); s.set_defaults(f=cmd_invariants)
    s = add("corpus"); s.set_defaults(f=cmd_corpus)
    s = add("resolve"); s.add_argument("jurisdiction"); s.add_argument("date"); s.set_defaults(f=cmd_resolve)

    a = p.parse_args(argv)
    return a.f(a) or 0


if __name__ == "__main__":
    sys.exit(main())
