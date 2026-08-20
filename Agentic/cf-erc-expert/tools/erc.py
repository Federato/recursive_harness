#!/usr/bin/env python3
"""cf-erc-expert retrieval CLI.

Answers questions about the ISO ERC Commercial Property corpus from the
structured knowledge base in ../knowledge/, without rescanning the source
tree.  Python standard library only.

    python erc.py <subcommand> [args] [--json]

Subcommands
    corpus                                 headline counts (edition folders,
                                           package counts, countrywide detail)
    identity   <package-id|jurisdiction>   package identity, from packages.json
                                           (66 packages, 20260601 edition ONLY)
    juris      <jurisdiction>              jurisdiction profile: package count
                                           in 20260601, editions across ALL
                                           edition folders
    table      <name>                      what is known about a rate table:
                                           population census + any sampled
                                           detail matching the name
    rule       <name-or-keyword>           rule-model facts matching a topic
                                           word, coverage-form suffix, or
                                           control-flow element name
    territory  [jurisdiction]              geographic rating scheme, from the
                                           10-jurisdiction sample only
    rating                                 the premium chain as traced
                                           (entry point, fan-out, one traced
                                           Building/Special chain)
    schema                                 CF vs GL schema-file comparison
                                           (composition.json)
    invariants [--severity S] [--id ID]    the invariant register (8 items,
                                           CF-ERC-ID-NNN)

Every answer carries a `source` naming the knowledge file. This knowledge
base was mined blind, independently of CF_Algorithm/, CFBranch/ and
Agentic/cf-circular-expert/ -- do not cross-reference those.

IMPORTANT SHAPE DIFFERENCE FROM GL's erc.py: this knowledge base is a set of
census/narrative findings over ONE edition folder (20260601) plus a 10-state
territory sample, NOT a full per-package, per-table, per-jurisdiction index
across all 52 jurisdictions and all editions the way GL's is. Several
subcommands here (juris, table, territory) will correctly report
"unverifiable" / "not sampled" more often than GL's equivalents -- that is
the honest state of this knowledge base, not a bug.

Exit code 0 on success, 2 on "not found" / "unverifiable", 3 on bad usage.
"""
from __future__ import annotations

import argparse
import json
import sys
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


# ----------------------------------------------------------------- corpus
def cmd_corpus(a):
    C = kb("corpus")
    pe = C["precise_edition_detail"]
    cw = C["countrywide_package_20260601_detail"]
    obj = {**C, "source": "knowledge/corpus.json",
           "caveat": "package_dirs_per_edition / total_package_dirs_all_editions "
                     "are directory-name counts across all 8 edition folders; "
                     "the detailed file-kind breakdown (rule/rate/domain "
                     "counts) exists ONLY for the 20260601 edition folder"}
    L = ["CF ERC Commercial Property corpus",
         f"  edition folders       {C['n_edition_folders']}: "
         f"{', '.join(C['edition_folders'])}",
         f"  package dirs (all editions)  {C['total_package_dirs_all_editions']}",
         f"  total files (all editions)   {C['total_files_all_editions']}",
         "",
         f"  DETAIL EDITION: {C['precise_edition']}",
         f"    packages            {pe['n_packages']}  "
         f"({pe['n_countrywide_packages']} countrywide, "
         f"{pe['n_state_packages']} state, "
         f"{pe['n_distinct_jurisdictions']} jurisdictions)",
         f"    files                {pe['n_files']}",
         f"    rule files           {pe['n_rule_files']}",
         f"    rate table csv/xml   {pe['n_rate_table_csv']} / "
         f"{pe['n_rate_table_def_xml']}",
         f"    domain table csv/xml {pe['n_domain_table_csv']} / "
         f"{pe['n_domain_table_def_xml']}",
         "",
         f"  countrywide package ({cw['package_dir']}): "
         f"{cw['total_files']} files",
         "    " + ", ".join(f"{k}={v}" for k, v in cw["categories"].items()),
         "",
         "  NOTE: this is a first measurement, not a verified inventory "
         "(see AGENT.md). File-kind detail exists only for 20260601."]
    return out(obj, a.json, L)


# --------------------------------------------------------------- identity
def cmd_identity(a):
    P = kb("packages")["packages"]
    key_norm = a.target.strip().upper().replace("_", " ")
    hits = {}
    for k, v in P.items():
        if k.upper() == key_norm or k.upper().replace(" ", "") == key_norm.replace(" ", ""):
            hits[k] = v
    if not hits:
        hits = {k: v for k, v in P.items() if v["jurisdiction"] == a.target.upper()}
    if not hits:
        die(f"no package or jurisdiction matching {a.target!r} in the "
            f"20260601 package set (packages.json covers 20260601 only)")
    obj = {"query": a.target, "n_matches": len(hits), "packages": hits,
           "source": "knowledge/packages.json",
           "caveat": "packages.json indexes ONLY the 66 packages in the "
                     "20260601 edition folder, not all 438 across the "
                     "corpus's 8 edition folders",
           "authority": "identity read from DataDefs/*.DataDef.xsd "
                        "targetNamespace and its single xs:import"}
    L = [f"{len(hits)} package(s) matching {a.target!r} (20260601 edition set)", ""]
    for k, v in sorted(hits.items(), key=lambda x: x[1]["edition"]):
        L.append(f"  {k}")
        L.append(f"    jurisdiction    {v['jurisdiction']}")
        L.append(f"    edition         {v['edition_date']}  version {v['version']}")
        L.append(f"    is_countrywide  {v['is_countrywide']}")
        L.append(f"    parent          {v['parent_package_id']}")
        L.append(f"    targetNamespace {v['xsd_target_ns']}")
        L.append(f"    content         {v['n_rate_tables']} rate tables, "
                 f"{v['n_domain_tables']} domain tables, "
                 f"{v['n_rule_files']} rule files, {v['n_files']} files")
    return out(obj, a.json, L)


# ------------------------------------------------------------------ juris
def cmd_juris(a):
    J = kb("jurisdictions")
    j = a.jurisdiction.upper()
    present_any = j in J["jurisdictions_present_any_edition"]
    if j not in J["jurisdictions_20260601"] and not present_any:
        die(f"{j!r} does not appear in any edition folder of the CF corpus "
            f"(missing_from_corpus: {', '.join(J['missing_from_corpus'])})")
    by_ed = {ed: (j in js) for ed, js in J["jurisdictions_by_edition_folder"].items()}
    v = J["jurisdictions_20260601"].get(j)
    obj = {"jurisdiction": j, "present_in_20260601": v is not None,
           "detail_20260601": v, "present_in_edition_folder": by_ed,
           "present_any_edition": present_any,
           "source": "knowledge/jurisdictions.json",
           "caveat": "package-level detail (n_packages, package_ids) is "
                     "known only for the 20260601 folder; older folders are "
                     "presence-only (directory-name survey, no file reads)"}
    L = [f"{j}"]
    if v:
        L += [f"  20260601 packages   {v['n_packages']}: "
              f"{', '.join(v['package_ids'])}",
              f"  editions present    {', '.join(v['editions_present_in_20260601_folder'])}"]
    else:
        L.append("  NOT present in the 20260601 edition folder")
    L.append("  present by edition folder:")
    L += [f"      {ed:12s} {'yes' if p else 'no'}" for ed, p in by_ed.items()]
    if j in J["missing_from_corpus"]:
        L.append(f"  !! {j} is in missing_from_corpus (never seen in any "
                 f"edition folder this survey walked)")
    return out(obj, a.json, L)


# ------------------------------------------------------------------ table
def cmd_table(a):
    CAT = kb("table_catalogue")
    q = a.name.lower()
    hits = {}
    for fname, detail in CAT.get("representative_tables_examined", {}).items():
        if q in fname.lower():
            hits[fname] = {**detail, "group": "representative_tables_examined"}
    br = CAT.get("naming_groups", {}).get("baserate_tables", {}).get("files", {})
    for fname, lines in br.items():
        if q in fname.lower():
            hits.setdefault(fname, {"lines": lines, "group": "baserate_tables"})
    ps = CAT["population_survey"]
    obj = {"query": a.name, "n_matches": len(hits), "matches": hits,
           "population_survey": ps,
           "source": "knowledge/table_catalogue.json",
           "caveat": "this is NOT a full per-table catalogue like GL's "
                     "825-table index -- only a population census (all 460 "
                     "countrywide tables, populated-vs-header-only) plus a "
                     "handful of individually examined tables. A name with "
                     "no match here may still exist among the 460; it simply "
                     "was not individually inspected this session."}
    L = []
    if hits:
        L.append(f"{len(hits)} known table(s) matching {a.name!r}:")
        for k, v in hits.items():
            L.append(f"  {k}  [{v['group']}]  {v}")
    else:
        L.append(f"no individually-examined table matches {a.name!r} "
                 f"(unverifiable from this knowledge base -- go to the "
                 f"corpus's Rate Tables/ folder to check)")
    L += ["", "countrywide population census (all 460 tables):",
          f"  header-only (0 rows)  {ps['header_only_0_data_rows']} "
          f"({ps['header_only_pct']})",
          f"  populated (1+ rows)   {ps['populated_1plus_data_rows']}",
          f"  finding: {ps['finding']}"]
    out(obj, a.json, L)
    return 0 if hits else 2


# ------------------------------------------------------------------- rule
def cmd_rule(a):
    RM = kb("rule_model")
    q = a.name.lower()
    if q in ("", "all"):
        obj = {**RM, "source": "knowledge/rule_model.json"}
        L = ["rule model summary",
             f"  total rule files  {RM['total_rule_files']}",
             f"  naming pattern    {RM['naming_pattern']['description']}"]
        return out(obj, a.json, L)
    hits = {}
    tg = RM["topic_groups"]
    for word_entry in tg.get("most_common_topic_words", []):
        if q in word_entry.lower():
            hits.setdefault("topic_word", []).append(word_entry)
    for suffix, cnt in tg.get("coverage_form_suffix_counts", {}).items():
        if q in suffix.lower():
            hits.setdefault("coverage_form_suffix", {})[suffix] = cnt
    ce = RM["control_flow_elements"]["element_counts_combined"]
    for elem, cnt in ce.items():
        if q in elem.lower():
            hits.setdefault("control_flow_element", {})[elem] = cnt
    if q in RM["naming_pattern"]["description"].lower():
        hits.setdefault("naming_pattern", RM["naming_pattern"])
    if not hits:
        obj = {"query": a.name, "found": False,
               "note": "not a topic word, coverage-form suffix, or "
                       "control-flow element name in the sampled rule "
                       "model. This knowledge base surveyed 5 representative "
                       "files, not all 882 -- absence here does not mean "
                       "the rule does not exist in the corpus.",
               "source": "knowledge/rule_model.json", "verdict": "unverifiable"}
        return out(obj, a.json,
                   [f"{a.name!r}: not in the sampled rule model.",
                    "  the KB surveyed 5 of 882 rule files for element/topic "
                    "shape, not a full rule index.",
                    "  verdict: unverifiable from the knowledge base -- "
                    "read the corpus's Rules/*.xml directly."]) or 2
    obj = {"query": a.name, "matches": hits,
           "source": "knowledge/rule_model.json",
           "caveat": "sampled from 5 of 882 rule files, not exhaustive"}
    L = [f"rule query {a.name!r}"]
    for kind, v in hits.items():
        L.append(f"  {kind}: {v}")
    return out(obj, a.json, L)


# -------------------------------------------------------------- territory
def cmd_territory(a):
    T = kb("territory")
    if a.jurisdiction:
        j = a.jurisdiction.upper()
        samples = T["samples"]
        if j not in samples:
            obj = {"jurisdiction": j, "sampled": False,
                   "verdict": "unverifiable",
                   "reason": T["not_sampled_note"],
                   "known_gaps": T.get("not_sampled_large_states", {}),
                   "source": "knowledge/territory.json"}
            return out(obj, a.json,
                       [f"{j}: NOT SAMPLED",
                        f"  {T['not_sampled_note']}",
                        f"  known explicit gaps: {T.get('not_sampled_large_states', {})}"]) or 2
        v = samples[j]
        obj = {"jurisdiction": j, **v, "source": "knowledge/territory.json"}
        L = [f"{j} territory sample",
             f"  table          {v.get('territory_table_file')}",
             f"  scheme         {v.get('scheme')}",
             f"  data rows      {v.get('n_data_rows')}"]
        if v.get("has_domain_zip_code_table"):
            L.append(f"  DomainZipCode  present but NOT a territory map "
                     f"(is_territory_map={v.get('domain_zip_code_is_territory_map')}) "
                     f"-- {v.get('domain_zip_code_n_rows')} rows, a flat valid-zip list")
        return out(obj, a.json, L)
    obj = {**T, "source": "knowledge/territory.json"}
    L = ["territory mechanism (SAMPLE ONLY, 10 of 42 jurisdictions in the "
         "20260601 folder):",
         f"  sampled: {', '.join(T['sampled_packages'])}", ""]
    for j, v in T["samples"].items():
        L.append(f"  {j:4s} {v.get('scheme', 'N/A'):16s} "
                 f"{v.get('n_data_rows', '?')} rows  {v.get('territory_table_file', '')}")
    L += ["", "not sampled (explicit gaps): " +
          str(T.get("not_sampled_large_states", {})),
          "", T["not_sampled_note"]]
    return out(obj, a.json, L)


# ----------------------------------------------------------------- rating
def cmd_rating(a):
    R = kb("rating")
    obj = {**R, "source": "knowledge/rating.json"}
    ep = R["entry_point"]
    fan = R["premium_fanout_pattern"]
    ovr = R["premium_indicator_override_pattern"]
    tr = R["traced_building_premium_chain"]
    L = ["CF PREMIUM CHAIN (as traced this session, NOT a full census)", "",
         f"entry point: {ep['file']} ({ep['lines']} lines)",
         f"  {ep['description']}", "",
         "fan-out pattern:", f"  {fan['description']}", "",
         "PremiumIndicator override pattern:", f"  {ovr['description']}", "",
         f"  caveat: {ovr['caveat']}", "",
         "traced Building/Special chain (CommercialPropertyStructureRules):"]
    for step in tr["steps"]:
        L.append(f"    {step['rule']} (lines {step['lines']}): {step['action']}")
    L += [f"  summary: {tr['chain_summary']}",
          f"  BLOCKER: {tr['critical_caveat_verified_this_session']}",
          f"  not verified: {tr['not_verified']}"]
    return out(obj, a.json, L)


# ----------------------------------------------------------------- schema
def cmd_schema(a):
    K = kb("composition")
    obj = {**K, "source": "knowledge/composition.json"}
    cf, gl = K["cf_schema"], K["gl_comparison"]
    L = ["CF vs GL master schema comparison",
         f"  CF: {cf['file']}  {cf['size_mb']} MB, "
         f"{cf['complexType_count']} complexType, "
         f"{cf['simpleType_count']} simpleType, monolithic={cf['single_file_monolithic']}",
         f"  GL: {gl['file_checked']}  {gl['size_mb']} MB, "
         f"{gl['complexType_count']} complexType, "
         f"monolithic={gl['single_file_monolithic']}",
         "", K["finding"]]
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
            L.append(f"      statement : {x['statement']}")
            L.append(f"      evidence  : {x['evidence']}")
            if x.get("if_wrong"):
                L.append(f"      if wrong  : {x['if_wrong']}")
            L.append("")
    return out(obj, a.json, L)


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="erc.py", description="CF ERC Commercial Property retrieval CLI")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true", help="emit JSON")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add(name):
        return sub.add_parser(name, parents=[common])

    s = add("corpus"); s.set_defaults(f=cmd_corpus)
    s = add("identity"); s.add_argument("target"); s.set_defaults(f=cmd_identity)
    s = add("juris"); s.add_argument("jurisdiction"); s.set_defaults(f=cmd_juris)
    s = add("table"); s.add_argument("name"); s.set_defaults(f=cmd_table)
    s = add("rule"); s.add_argument("name"); s.set_defaults(f=cmd_rule)
    s = add("territory"); s.add_argument("jurisdiction", nargs="?"); s.set_defaults(f=cmd_territory)
    s = add("rating"); s.set_defaults(f=cmd_rating)
    s = add("schema"); s.set_defaults(f=cmd_schema)
    s = add("invariants")
    s.add_argument("--severity"); s.add_argument("--id")
    s.add_argument("-v", "--verbose", action="store_true"); s.set_defaults(f=cmd_invariants)

    a = p.parse_args(argv)
    return a.f(a) or 0


if __name__ == "__main__":
    sys.exit(main())
