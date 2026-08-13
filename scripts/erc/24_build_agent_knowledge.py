"""Phase 6: generate the iso-erc-expert agent's knowledge base.

Reads the analysis intermediates in scripts/erc/out/ and emits structured
JSON into Agentic/iso-erc-expert/knowledge/ so the agent can answer
questions without rescanning the 700 MB corpus.

Produces:
  packages.json       567 packages: identity, edition, version, parent,
                      artefact counts, source directories
  jurisdictions.json  52 jurisdictions: edition timeline, resolved
                      sublines, resolved coverage count, territory profile,
                      override volume
  table_catalogue.json  825 distinct tables: variation class, signatures,
                      shape, which jurisdictions carry a copy
  composition.json    the override mechanics with measured counts
  rating.json         the premium chain, the 19 rating tables, the capture
                      tables, premium bases, table shapes
  rule_model.json     operators, lifecycle names, entry points, call-graph
                      shape, unspecified semantics
  territory.json      geographic key columns, per-jurisdiction codes,
                      ZIP-map availability
  corpus.json         headline counts for provenance/drift detection

invariants.json is authored by hand (each invariant needs a check that no
script can infer) and is NOT written by this script.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from importlib import import_module

sys.path.insert(0, str(Path(__file__).parent))
c = import_module("00_common")
csv.field_size_limit(1 << 24)

KB = Path(r"C:\Projects\Recursive_Harness_2.0\Agentic\iso-erc-expert\knowledge")
KB.mkdir(parents=True, exist_ok=True)


def load(n):
    with open(c.OUT / n, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def dump(name, obj):
    p = KB / name
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1, sort_keys=False)
    print(f"  {name:26s} {p.stat().st_size:>9,} bytes")


def main():
    pkgs_csv = load("packages.csv")
    xsd = {r["pkg_id"]: r for r in load("xsd_packages.csv")}
    fpt = load("fp_tables.csv")
    rules = load("rules_index.csv")
    comp = {r["pkg_id"]: r for r in load("composition.csv")}
    vt = load("variation_tables.csv")
    terr = load("territory_by_juris.csv")
    covm = load("coverage_matrix.csv")
    shapes = load("table_shapes.csv")

    # ---------------- packages.json ----------------
    dirs = defaultdict(list)
    for r in pkgs_csv:
        dirs[r["pkg_id"]].append(r["dir_name"])
    seen = {}
    for r in pkgs_csv:
        seen.setdefault(r["pkg_id"], r)
    n_rules = Counter(r["pkg_id"] for r in rules)
    n_rt = Counter(r["pkg_id"] for r in fpt if r["kind"] == "Rate")
    n_dt = Counter(r["pkg_id"] for r in fpt if r["kind"] == "Domain")
    packages = {}
    for pid, r in sorted(seen.items()):
        x = xsd.get(pid, {})
        packages[pid] = dict(
            jurisdiction=r["juris"],
            edition_date=f"{r['edition'][:4]}-{r['edition'][4:6]}-{r['edition'][6:]}",
            edition=r["edition"],
            version=r["version"],
            is_countrywide=r["juris"] == "CW",
            parent_package_id=(x.get("import_pkgs") or None)
            if x.get("import_pkgs", "").startswith("GL_CW") else None,
            xsd_import=x.get("import_pkgs") or None,
            xsd_target_ns=x.get("target_ns") or None,
            n_rules=n_rules.get(pid, 0),
            n_rate_tables=n_rt.get(pid, 0),
            n_domain_tables=n_dt.get(pid, 0),
            n_files=int(r["n_files"]),
            source_dirs=sorted(dirs[pid]),
            duplicate_dirs=len(dirs[pid]) > 1,
        )
    dump("packages.json", dict(
        _note="Identity is taken from the XSD targetNamespace, not the "
              "directory path. 5 package ids occupy two byte-identical "
              "directories.",
        n_packages=len(packages), packages=packages))

    # ---------------- jurisdictions.json ----------------
    sub_cols = [k for k in covm[0] if k not in ("juris", "pkg_id", "edition")]
    subs = {r["juris"]: sorted(s for s in sub_cols if r[s] == "1")
            for r in covm}
    terr_by = {r["juris"]: r for r in terr}
    juris = {}
    for j in sorted({p["jurisdiction"] for p in packages.values()}):
        eds = sorted((p["edition"], p["version"], pid)
                     for pid, p in packages.items()
                     if p["jurisdiction"] == j)
        latest = eds[-1]
        cmp_ = comp.get(latest[2], {})
        t = terr_by.get(j, {})
        juris[j] = dict(
            n_packages=len(eds),
            first_edition=eds[0][0], latest_edition=latest[0],
            latest_package_id=latest[2],
            latest_parent=packages[latest[2]]["parent_package_id"],
            editions=[{"edition": e, "version": v, "package_id": p}
                      for e, v, p in eds],
            resolved_sublines=subs.get(j, []),
            n_resolved_sublines=len(subs.get(j, [])),
            territory=dict(
                n_distinct_codes=int(t.get("n_distinct_codes", 0) or 0),
                has_zip_map=int(t.get("n_zip_rows", 0) or 0) > 0,
                n_zip_rows=int(t.get("n_zip_rows", 0) or 0),
                codes=(t.get("codes", "") or "").split(";")[:120]
                if t.get("codes") else [],
            ),
            latest_override_profile=dict(
                n_rules=int(cmp_.get("n_rules", 0) or 0),
                rules_overridden=int(cmp_.get("rt_overridden", 0) or 0),
                rules_state_specific=int(cmp_.get("rt_statespecific", 0) or 0),
                tables_state_only=int(cmp_.get("tables_state_only", 0) or 0),
                tables_shadowed=int(cmp_.get("tables_shadowed", 0) or 0),
                tables_inherited_only=int(cmp_.get("tables_parent_only", 0) or 0),
            ) if cmp_ else None,
        )
    dump("jurisdictions.json", dict(
        _note="Sublines and coverages are RESOLVED through the countrywide "
              "parent. Only 60 of 567 packages ship their own subline list; "
              "507 inherit it.",
        n_jurisdictions=len(juris), jurisdictions=juris))

    # ---------------- table_catalogue.json ----------------
    sig = defaultdict(lambda: Counter())
    shape_of = {}
    for r in shapes:
        sig[(r["kind"], r["table"])][(r["key_cols"], r["value_cols"])] += 1
        shape_of[(r["kind"], r["table"])] = r["shape"]
    cat = {}
    for r in vt:
        k = (r["kind"], r["table"])
        sigs = sig.get(k, Counter())
        top = sigs.most_common(1)[0][0] if sigs else ("", "")
        cat[f"{r['kind']}:{r['table']}"] = dict(
            kind=r["kind"], table=r["table"],
            variation_class=r["class"],
            shape=shape_of.get(k, "unknown"),
            n_countrywide_packages=int(r["n_cw_pkgs"]),
            n_state_packages=int(r["n_state_pkgs"]),
            n_jurisdictions=int(r["n_juris"]),
            jurisdictions=r["juris_list"].split(";") if r["juris_list"] else [],
            n_distinct_state_contents=int(r["n_distinct_state_contents"]),
            key_cols=[x for x in top[0].split("|") if x],
            value_cols=[x for x in top[1].split("|") if x],
            n_signatures=len(sigs),
        )
    dump("table_catalogue.json", dict(
        _note="variation_class: countrywide-only = no state ever ships its "
              "own copy; universally-overridden = every state does; "
              "state-only = never in countrywide.",
        n_tables=len(cat),
        class_counts=dict(Counter(v["variation_class"] for v in cat.values())),
        shape_counts=dict(Counter(v["shape"] for v in cat.values())),
        tables=cat))

    # ---------------- composition.json ----------------
    rt_shadow = Counter()
    rule_by_pkg = defaultdict(dict)
    for r in rules:
        rule_by_pkg[r["pkg_id"]][(r["rule_file"], r["rule_name"])] = \
            r["metadata_codes"]
    for pid, p in packages.items():
        par = p["parent_package_id"]
        if not par:
            continue
        pr = rule_by_pkg.get(par, {})
        for k, rt in rule_by_pkg.get(pid, {}).items():
            rt_shadow[(rt, k in pr)] += 1
    dump("composition.json", dict(
        _note="Measured by 18_composition.py over 557 state packages against "
              "the countrywide package each one's xs:import names.",
        provenance_tags={
            "RuleTypeCountrywide": "base logic; ONLY in countrywide packages",
            "RuleTypeOverridden": "shadows a rule of the same (file, name) in "
                                  "the parent; ONLY in state packages",
            "RuleTypeStateSpecific": "novel; no parent counterpart; ONLY in "
                                     "state packages",
            "RuleTypeSystem": "plumbing; in both",
        },
        tag_exactness={f"{rt}|shadows={sh}": n
                       for (rt, sh), n in sorted(rt_shadow.items(), key=str)},
        override_behaviour=dict(
            overridden_total=23404, overridden_replaces=17556,
            overridden_callsuper_same_rule=4598,
            overridden_callsuper_other_rule=1250,
            system_shadowing=8205, system_callsuper=7648, system_replaces=557),
        table_overlay=dict(parent_only=266932, shadowed=21694,
                           shadowed_identical=36, state_only=3673),
        lookup_resolution=dict(state_only=2589, parent_only=476,
                               both_differ=374, both_identical=0,
                               pages_matrix_excluded=45592),
        resolver_rules=[
            "R1 identity from XSD targetNamespace, never the directory path",
            "R2 dedupe by package id (5 ids have two directories)",
            "R3 order by (edition_date, version); 45 juris/edition pairs need version",
            "R4 select newest edition <= rating date; NEVER max (83 future-dated)",
            "R5 editions are cumulative snapshots; load exactly one",
            "R6 resolve the single xs:import; never substitute another CW edition",
            "R7 overlay countrywide then state, by name, state wins",
            "R8 a shadowed table is REPLACED wholesale; never merge rows",
            "R9 10.88% of state lookups hit both layers and they always differ",
            "R10 RuleType tags are exact declarations (0 exceptions)",
            "R11 RunRule with ProjectName dispatches to the PARENT, bypassing "
            "the overlay; otherwise 4,598 call-super rules recurse forever",
            "R12 RunRule without ProjectName resolves against the overlay",
            "R13 Lookup resolves against the overlay; 'Pages' is the Form Pages CSV",
            "R14 two entry points: ErcProcess and ErcCalculateTotalPremium",
        ]))

    # ---------------- rating.json ----------------
    dump("rating.json", dict(
        _note="Derived mechanically from 73,990 dataflow edges "
              "(20_rating_structure.py). See docs/erc/03-RATING-STRUCTURE.md.",
        premium_chain={
            "BaseRate": "Product(LossCost|ELP, LCM [, ClaimsMadeMultiplier])",
            "FinalILF": "Round(ILF, DeductibleFactor) | Round(CSLILF, FinalDeductibleFactor)",
            "FinalDeductibleFactor": "Sum(BIDeductibleFactor, PDDeductibleFactor) | Copy(one)",
            "FinalRate": "Product(BaseRate, FinalILF, PackageModFactor, "
                         "ExperienceRatingModificationFactor, ExpenseModification, "
                         "ModToUse [, SizeOfRiskFinalRelativity] "
                         "[, PremiumDiscountCharge])",
            "BasicLimitPremium": "Product(BaseRate, FinalDeductibleFactor, "
                                 "PackageModFactor, <Subline>CovExposure "
                                 "[, SizeOfRiskFinalRelativity])",
            "Premium(rated)": "Round(FinalRate * <Subline>CovExposure "
                              "+ MedicalPaymentsCharge, 0)",
            "Premium(capture)": "Product(ManualPremium, PackageModFactor)",
            "ErcCalculatedTotalPremium": "Sum(Premium, PremiumIndicator) over "
                                         "every coverage row",
        },
        premium_writers=dict(total_tables=420, capture_manualpremium=381,
                             rated_from_rates=19, other_mixed=20),
        rating_tables=[
            "GeneralLiabilityClassificationPremOpsCoverage",
            "GeneralLiabilityClassificationProdsCompldOpsCoverage",
            "GeneralLiabilityClassificationLiquorCoverage",
            "GeneralLiabilityClassificationOwnersContractorsCoverage",
            "GeneralLiabilityClassificationSpecialProtectiveHighwayCoverage",
            "GeneralLiabilityClassificationCyberIncidentLiabilityPremOpsCoverage",
            "GeneralLiabilityClassificationCyberIncidentLiabilityProdsCompldOpsCoverage",
            "GeneralLiabilityClassificationLossOfElectronicDataPremOpsCoverage",
            "GeneralLiabilityClassificationLossOfElectronicDataProdsCompldOpsCoverage",
            "GeneralLiabilityClassificationExclusionCoverageAProductWithdrawalExpense",
            "GeneralLiabilityClassificationExclusionCoverageBProductWithdrawalLiability",
            "GeneralLiabilityUnmannedAircraftTerrorismCoverage",
            "GeneralLiabilityPremOpsPremiumToReachMinCoverage",
            "GeneralLiabilityProdsCompldOpsPremiumToReachMinCoverage",
            "GeneralLiabilityLiquorPremiumToReachMinCoverage",
            "GeneralLiabilityOwnersContractorsPremiumToReachMinCoverage",
            "GeneralLiabilityRailroadPremiumToReachMinCoverage",
            "GeneralLiabilitySpecialProtectiveHighwayPremiumToReachMinCoverage",
            "GeneralLiabilitySpecialCombinedPremiumToReachMinCoverage",
        ],
        premium_bases=["Admissions", "Area", "Gallons", "Gross Sales",
                       "Passenger Days", "Payroll", "Total Cost",
                       "Total Operating Expenses", "Vehicles"],
        table_shapes=dict(flat="key tuple -> value tuple",
                          banded="<Range> in KeyCols; _From/_ToLessThan; 164 tables",
                          interpolated="<Range> in ValueCols with "
                                       "InterpolateMode=Linear; 18 tables; the "
                                       "cell is NOT its literal value",
                          assignment="value names another table to consult; "
                                     "1,174 tables",
                          statistical="returns a reporting code; 1,490 tables"),
        lookup_dimensions_top=[
            ["StateCode", 27717], ["ClassCodeCGLProds", 6691],
            ["ClassCodeOwnersContrctrs", 4376], ["ClassCodeLiquor", 2300],
            ["ClassCodeRailroad", 1796], ["ClassCode", 1754],
            ["EachOccurrenceLimit", 1354], ["GeneralAggregateLimit", 1269],
            ["PremOpsTerr", 1137], ["ProdsCompldOpsTerr", 896]],
        value_gotchas=dict(
            compound_limits="EachOccurrenceLimit has 40 values = amount x basis "
                            "('1,000,000' vs '1,000,000 CSL' vs '1,000,000 BI' "
                            "are DISTINCT keys). 390,852 comma-formatted cells.",
            sentinels={"NA": 13398, "Other": 1846, "Refer To Co.": 1153,
                       "N/A": 54, "<1 (Yr)": 30, "9+": 30, "Unknown": 30},
            blanks="only 80 blank cells in 45,195,864",
            no_xsd_enumerations="the XSD constrains precision/length only; "
                                "value vocabularies live in domain tables"),
        refer_to_company=dict(
            doc_rows=5300, doc_form_numbers=590, doc_packages=390,
            not_supported_rows=395, not_supported_packages=35,
            special_consideration_rows=1113,
            cell_sentinel_occurrences=1153,
            triggers=["form listed in the DOC 'Refer to Company' sheet",
                      "a lookup returns the 'Refer To Co.' sentinel",
                      "a capture table with no ManualPremium supplied"])))

    # ---------------- rule_model.json ----------------
    ops = Counter()
    for r in rules:
        for st in r["statement_tags"].split(";"):
            if ":" in st:
                t, n = st.rsplit(":", 1)
                ops[t] += int(n)
    dump("rule_model.json", dict(
        _note="Measured by 05_rules.py / 23_rule_program.py.",
        n_rule_elements=len(rules),
        n_rule_files=len({(r["pkg_id"], r["rule_file"]) for r in rules}),
        n_datadef_groups=len({r["datadef_group"] for r in rules}),
        file_to_group="1:1 in all 1,032 cases; filename is always <group>Rules",
        entry_points=["GeneralLiabilityRules/ErcProcess",
                      "GeneralLiabilityRules/ErcCalculateTotalPremium"],
        lifecycle_names=sorted({r["rule_name"] for r in rules
                                if r["rule_name"].startswith("Erc")}),
        call_graph=dict(acyclic=True, back_edges=0, max_depth=8,
                        measured_on="GL_CW_20270401_V01",
                        reachable_from_ercprocess=3888, rules_defined=4528),
        top_level_sequence=[
            "ErcSetRatesAndFactors",
            "ForEach location: InitializeRuleSet, CallErcSetRatesAndFactors",
            "ErcDoConditionalMandatoryLogic", "ErcDoOptionalConditionalLogic",
            "ErcSetPostRatesAndFactors", "SetModFactors",
            "ForEach child table: InitializeRuleSet, ErcProcess (recursive)"],
        leaf_rate_sequence=[
            "SetFinalRate", "SetMedicalPaymentsCharge",
            "SetAdditionalInterestFactor", "SetMinimumPremium", "SetMinPremium",
            "SetSpecialCombinedMinimumPremium", "SetSpecialCombinedMinPremium",
            "SetPremium", "SetPremiumIndicator"],
        operators={k: v for k, v in ops.most_common()},
        n_operators=len(ops),
        unspecified_semantics=[
            "FirstValue@Order='DataDefInputParamConstant' precedence (171,865 nodes)",
            "Lookup@ResultMode FirstResult vs SingleResult against non-unique keys",
            "Product/Round @DecimalPlaces rounding MODE (7,682 declarations)",
            "Range@RangeType boundary combined with InterpolateMode at an exact bound",
            "RunRule@ClearCache scope and lifetime",
            "Locate@OutputAction / @AtOutputDataDef output-tree semantics",
            "the XPath dialect in FormField.Condition and RatingRequiredCondition",
            "ErcCore (imported by all 10 CW xsds, absent from the corpus)",
            "MessageHelper.AddErrorMessage (4,375 refs, not shipped)"]))

    # ---------------- territory.json ----------------
    dump("territory.json", dict(
        _note="Measured by 22_territory.py. All 52 jurisdictions are "
              "multi-territory once resolved; only 27 ship a ZIP map.",
        mechanism=["domain table maps postal code -> territory code",
                   "rate tables are keyed on the territory code",
                   "Form Related Fields wires the two together (257 of 3,122 rows)"],
        geographic_key_columns={
            "PremOpsTerr": 1137, "ProdsCompldOpsTerr": 896, "ZipCode": 333,
            "Territory": 197, "PremOpsTerrName": 94,
            "PremisesOperationsTerritory": 40, "TerrorismTerritory": 40,
            "TerritoryIndicator": 40, "TerritoryBorough": 40,
            "LiquorLiabTerritory": 20, "SpecialClassPremOpsTerritory": 20,
            "CityTown": 17, "County": 7},
        n_geo_keyed_table_defs=2969, n_table_defs=30773,
        n_distinct_zipcodes=23782, zipcode_sentinel="Other",
        prodscompldopsterr_degenerate=dict(
            only_value="999",
            note="Products/completed-operations rating is keyed on territory "
                 "but the key is degenerate everywhere in the corpus."),
        jurisdictions={r["juris"]: dict(
            n_distinct_codes=int(r["n_distinct_codes"] or 0),
            has_zip_map=int(r["n_zip_rows"] or 0) > 0,
            n_zip_rows=int(r["n_zip_rows"] or 0)) for r in terr},
        n_with_zip_map=sum(1 for r in terr if int(r["n_zip_rows"] or 0) > 0),
        n_without_zip_map=sum(1 for r in terr
                              if int(r["n_zip_rows"] or 0) == 0)))

    # ---------------- corpus.json ----------------
    dump("corpus.json", dict(
        _note="Headline counts for drift detection. Re-derive with "
              "scripts/erc/01_inventory.py.",
        corpus_root=r"C:\Projects\ISO_ERC_Files\General_Liability",
        excluded_dirs=sorted(c.EXCLUDE_DIRS),
        package_directories=len(pkgs_csv), distinct_packages=len(packages),
        countrywide_packages=sum(1 for p in packages.values()
                                 if p["is_countrywide"]),
        state_packages=sum(1 for p in packages.values()
                           if not p["is_countrywide"]),
        jurisdictions=len(juris),
        files_in_packages=sum(int(r["n_files"]) for r in pkgs_csv),
        rate_tables=sum(1 for r in fpt if r["kind"] == "Rate"),
        domain_tables=sum(1 for r in fpt if r["kind"] == "Domain"),
        rule_elements=len(rules),
        distinct_table_names=len({(r["kind"], r["table"]) for r in fpt}),
        edition_range=[min(p["edition"] for p in packages.values()),
                       max(p["edition"] for p in packages.values())],
        reports=["docs/erc/01-CORPUS-AND-SCHEMA.md",
                 "docs/erc/02-EDITIONS-AND-INTEGRITY.md",
                 "docs/erc/03-RATING-STRUCTURE.md",
                 "docs/erc/04-BUILD-SCOPE-AND-RESOLVER.md",
                 "docs/erc/05-DATA-MODEL-AND-INGESTION.md",
                 "docs/erc/06-VALIDATION-AND-BACKLOG.md"]))
    print("knowledge base written to", KB)


if __name__ == "__main__":
    main()
