#!/usr/bin/env python3
"""Smoke test for iso-erc-expert.

Every case asserts a fact independently established by measurement over the
ISO ERC General Liability corpus (see docs/erc/01..06). If the knowledge
base drifts away from the corpus, or the CLI stops answering correctly,
these fail loudly and name the report section that established the fact.

    python smoke_test.py            # run all
    python smoke_test.py -v         # show every passing case

Exit 0 if all pass, 1 otherwise.  Standard library only.
"""
from __future__ import annotations

import io
import json
import sys
import contextlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import erc  # noqa: E402

FAIL: list[str] = []
PASS = 0
VERBOSE = "-v" in sys.argv


def check(name, got, want, why):
    global PASS
    if got == want:
        PASS += 1
        if VERBOSE:
            print(f"  ok   {name}: {got!r}")
    else:
        FAIL.append(f"{name}\n       expected {want!r}\n       got      {got!r}"
                    f"\n       basis: {why}")


def check_pred(name, ok, why, detail=""):
    global PASS
    if ok:
        PASS += 1
        if VERBOSE:
            print(f"  ok   {name}")
    else:
        FAIL.append(f"{name}\n       predicate failed. {detail}"
                    f"\n       basis: {why}")


def cli(args):
    """Run the CLI with --json and return the parsed object."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        erc.main(list(args) + ["--json"])
    return json.loads(buf.getvalue())


def cli_code(args):
    buf, err = io.StringIO(), io.StringIO()
    try:
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
            return erc.main(list(args) + ["--json"]), buf.getvalue()
    except SystemExit as e:
        return e.code, buf.getvalue()


# ---------------------------------------------------------------------------
print("iso-erc-expert smoke test")
print("=" * 70)

# --- 1. corpus shape -------------------------------------------------------
print("\n[1] corpus shape (report 01 §1, re-derived post-remediation)")
C = cli(["corpus"])
check("package directories", C["package_directories"], 572,
      "01_inventory.py on the post-remediation tree")
check("distinct packages", C["distinct_packages"], 567,
      "572 directories minus 5 duplicated package ids")
check("countrywide packages", C["countrywide_packages"], 10, "report 01 §1.1")
check("state packages", C["state_packages"], 557, "567 - 10")
check("jurisdictions", C["jurisdictions"], 52, "51 states/DC/PR + CW")
check("rate tables", C["rate_tables"], 23945, "02_table_defs.py")
check("domain tables", C["domain_tables"], 6828, "02_table_defs.py")
check("rule elements", C["rule_elements"], 114726, "05_rules.py")
check("distinct table names", C["distinct_table_names"], 825,
      "21_variation_surface.py")
check("edition range", C["edition_range"], ["20201201", "20270401"],
      "report 01 §1.5")

# --- 2. identity comes from the XSD, not the path --------------------------
print("\n[2] identity (invariant ERC-ID-001, report 02 §4)")
I = cli(["identity", "GL_NJ_20250301_V01"])
p = I["packages"]["GL_NJ_20250301_V01"]
check("NJ package jurisdiction", p["jurisdiction"], "NJ", "XSD targetNamespace")
check("NJ package edition", p["edition"], "20250301", "XSD targetNamespace")
check("NJ targetNamespace", p["xsd_target_ns"],
      "http://www.verisk.com/iso/erc/GL_NJ_20250301_V01/MasterGLNJ",
      "DataDefs/MasterGLNJ.DataDef.xsd")
check("NJ imports a specific CW edition", p["parent_package_id"],
      "GL_CW_20231201_V02", "the single xs:import in the NJ XSD")

P = json.load(open(erc.KB / "packages.json", encoding="utf-8"))["packages"]
check_pred("every package has a targetNamespace matching its id",
           all(v["xsd_target_ns"] and
               v["xsd_target_ns"].split("/erc/")[1].split("/")[0] == k
               for k, v in P.items()),
           "16_self_dating.py: 567/567 match")
check("packages with duplicate directories",
      sum(1 for v in P.values() if v["duplicate_dirs"]), 5,
      "15_integrity.py recursive tree hash: 5 ids, all byte-identical")
check_pred("every state package imports a countrywide package",
           all(v["parent_package_id"] and
               v["parent_package_id"].startswith("GL_CW")
               for v in P.values() if not v["is_countrywide"]),
           "04_datadefs.py: 10 referenced, 10 present, 0 missing")
check("countrywide packages import ErcCore",
      sorted({v["xsd_import"] for v in P.values() if v["is_countrywide"]}),
      ["ErcCore"],
      "all 10 CW XSDs import ErcCore, which is absent from the corpus")

# --- 3. the misfiling remediation held -------------------------------------
print("\n[3] remediation (report 03 §0)")
PR = cli(["juris", "PR"])
check("PR package count", PR["n_packages"], 8,
      "PR's newest edition was under RI/ and has been moved back")
check("PR latest edition", PR["latest_edition"], "20270401",
      "the edition that previously existed only under RI/")
RI = cli(["juris", "RI"])
check("RI package count", RI["n_packages"], 8, "RI holds only RI packages now")
check_pred("no PR package is attributed to RI",
           all(v["jurisdiction"] == "RI" for k, v in P.items()
               if v["jurisdiction"] == "RI"),
           "report 03 §0: 0 misfiled packages remain")

# --- 4. as-of edition selection --------------------------------------------
print("\n[4] as-of selection (invariant ERC-ED-001)")
A = cli(["asof", "NJ", "2025-06-01"])
check("NJ in force 2025-06-01", A["in_force"]["package_id"],
      "GL_NJ_20250301_V01", "newest edition <= the rating date")
check_pred("future editions were excluded",
           A["n_future_dated_editions_excluded"] > 0,
           "NJ has editions after 2025-06-01 that must not be selected")
A2 = cli(["asof", "NJ", "2027-12-31"])
check("NJ in force 2027-12-31", A2["in_force"]["package_id"],
      "GL_NJ_20270101_V01", "the latest NJ edition")
code, _ = cli_code(["asof", "NJ", "2019-01-01"])
check_pred("a date before the first edition yields nothing in force",
           code == 2, "the corpus starts at 2020-12-01; exit code 2 expected",
           f"exit code was {code}")

# --- 5. composition / override mechanics -----------------------------------
print("\n[5] composition (invariants ERC-CMP-002/003/004/005)")
K = json.load(open(erc.KB / "composition.json", encoding="utf-8"))
te = K["tag_exactness"]
check("RuleTypeOverridden rules that shadow the parent",
      te.get("RuleTypeOverridden|shadows=True"), 23404,
      "18_composition.py: 100.0%, zero exceptions")
check("RuleTypeOverridden rules that do NOT shadow",
      te.get("RuleTypeOverridden|shadows=False", 0), 0,
      "18_composition.py: 100.0% shadow, so this must be exactly zero — "
      "the tag is an exact declaration, not a label")
check("RuleTypeStateSpecific rules that shadow the parent",
      te.get("RuleTypeStateSpecific|shadows=True", 0), 0,
      "18_composition.py: 0.0%, zero exceptions")
check("RuleTypeStateSpecific rules that do NOT shadow",
      te.get("RuleTypeStateSpecific|shadows=False", 0), 23755,
      "18_composition.py: all 23,755 are novel")
check_pred("RuleTypeCountrywide never appears in a state package",
           not any(k.startswith("RuleTypeCountrywide") for k in te),
           "the four tags partition perfectly by package kind; this table "
           "covers state packages only")
ob = K["override_behaviour"]
check("overrides that replace outright", ob["overridden_replaces"], 17556,
      "75.0% of 23,404")
check("overrides that call-super the same rule",
      ob["overridden_callsuper_same_rule"], 4598,
      "19.6% — these recurse forever if ProjectName is not honoured")
to = K["table_overlay"]
check("shadowed tables identical to the parent", to["shadowed_identical"], 36,
      "0.17% of 21,694 — a shadow is essentially always a real override")
lr = K["lookup_resolution"]
check("lookups where both layers hold the table and they differ",
      lr["both_differ"], 374, "10.88% — resolution order changes the answer")
check("lookups where both layers agree", lr["both_identical"], 0,
      "there is no case where the choice is moot")

# --- 6. what actually rates -------------------------------------------------
print("\n[6] rating scope (invariant ERC-RAT-001)")
R = cli(["premium"])
w = R["premium_writers"]
check("tables writing a Premium", w["total_tables"], 420,
      "20_rating_structure.py over 73,990 dataflow edges")
check("capture tables (ManualPremium)", w["capture_manualpremium"], 381,
      "90.7% — the user supplies the premium")
check("tables that genuinely rate", w["rated_from_rates"], 19, "4.5%")
check("rating table list length", len(R["rating_tables"]), 19,
      "the list must match the count")
check_pred("PremOps classification coverage is in the rated set",
           "GeneralLiabilityClassificationPremOpsCoverage" in R["rating_tables"],
           "the primary class-rated coverage")
check_pred("an additional-insured table is NOT in the rated set",
           not any("AddlInsd" in t for t in R["rating_tables"]),
           "additional-insured endorsements are capture tables")
check("FinalRate formula", R["premium_chain"]["FinalRate"],
      "Product(BaseRate, FinalILF, PackageModFactor, "
      "ExperienceRatingModificationFactor, ExpenseModification, ModToUse "
      "[, SizeOfRiskFinalRelativity] [, PremiumDiscountCharge])",
      "SetFinalRate in GeneralLiabilityClassificationPremOpsCoverageRules.Rule.xml")
check("refer-to-company cell sentinel count",
      R["refer_to_company"]["cell_sentinel_occurrences"], 1153,
      "07_csv_values.py: 'Refer To Co.' in rate cells")
check("DOC refer-to-company rows", R["refer_to_company"]["doc_rows"], 5300,
      "08_doc_stc_forms.py")

# --- 7. coverage resolution -------------------------------------------------
print("\n[7] resolved coverage (invariant ERC-CMP-006)")
CV = cli(["coverage"])
check("distinct sublines", CV["n_sublines"], 11, "19_coverage_inventory.py")
sp = CV["sublines"]["Special Protective And Highway"]
check("Special Protective And Highway is NY only",
      sp["jurisdictions"], ["NY"], "report 03 §2.1")
check("Pollution absent from NY only",
      CV["sublines"]["Pollution"]["absent_from"], ["NY"], "report 03 §2.1")
check("Electronic Data Liability absent from IL and NY",
      CV["sublines"]["Electronic Data Liability"]["absent_from"], ["IL", "NY"],
      "report 03 §2.1")
check("Underground Storage Tank absent from 4 jurisdictions",
      CV["sublines"]["Underground Storage Tank"]["absent_from"],
      ["NY", "TX", "VA", "VT"], "report 03 §2.1")
check_pred("every jurisdiction resolves to at least 6 sublines",
           all(v["n_resolved_sublines"] >= 6 for v in
               json.load(open(erc.KB / "jurisdictions.json",
                              encoding="utf-8"))["jurisdictions"].values()),
           "six sublines are universal; fewer means resolution did not happen")

# --- 8. territory ----------------------------------------------------------
print("\n[8] territory (invariants ERC-TER-001/002)")
T = cli(["territory"])
check("jurisdictions with a ZIP map", T["n_with_zip_map"], 27,
      "22_territory.py")
check("jurisdictions without a ZIP map", T["n_without_zip_map"], 25,
      "territory must be supplied as an input in these")
check("ProdsCompldOpsTerr only value",
      T["prodscompldopsterr_degenerate"]["only_value"], "999",
      "22_territory.py: degenerate key corpus-wide")
check("distinct ZIP values", T["n_distinct_zipcodes"], 23782,
      "22_territory.py")
NY = cli(["territory", "NY"])
check("NY territory codes", NY["n_distinct_codes"], 89,
      "the most granular jurisdiction")
# CORRECTED 2026-08-10: a missing ZIP map is not an inability to resolve.
# 20 jurisdictions are single-territory; 4 key on county/place. See ERC-TER-001.
_sch = {j: v.get("scheme") for j, v in T["jurisdictions"].items()}
check("single-territory jurisdictions", sum(1 for s in _sch.values()
      if s == "SINGLE_TERRITORY"), 20, "no lookup needed")
check("county/place jurisdictions", sum(1 for s in _sch.values()
      if s == "COUNTY_PLACE"), 4, "CA, FL, NY, TX")
check("ZIP-table jurisdictions", sum(1 for s in _sch.values()
      if s == "ZIP_TABLE"), 27, "CW is not a rating jurisdiction")
check("AK rates at a single territory",
      cli(["territory", "AK"])["rating_territory"], "001", "entire state")
check("NC is the lone 002 jurisdiction",
      cli(["territory", "NC"])["rating_territory"], "002",
      "the exception among the 20")
check_pred("every rating jurisdiction resolves to exactly one scheme",
           all(s in ("SINGLE_TERRITORY", "COUNTY_PLACE", "ZIP_TABLE")
               for j, s in _sch.items() if j != "CW"),
           "ERC-TER-001: territory is always derivable from ERC")

# --- 9. table resolution ---------------------------------------------------
print("\n[9] table catalogue (invariant ERC-CMP-004)")
TB = cli(["table", "ProdsCompldOpsLossCost"])
k = "Rate:ProdsCompldOpsLossCost"
check("ProdsCompldOpsLossCost is universally overridden",
      TB["tables"][k]["variation_class"], "universally-overridden",
      "21_variation_surface.py: all 51 state jurisdictions ship their own")
check("ProdsCompldOpsLossCost distinct state contents",
      TB["tables"][k]["n_distinct_state_contents"], 334,
      "the most-varied table in the corpus")
check("ProdsCompldOpsLossCost keys",
      TB["tables"][k]["key_cols"],
      ["StateCode", "ProdsCompldOpsTerr", "ClassCodeCGLProds"],
      "its RateTableDef")
CAT = json.load(open(erc.KB / "table_catalogue.json", encoding="utf-8"))
check("table variation classes", CAT["class_counts"],
      {"countrywide-only": 337, "state-only": 288,
       "sometimes-overridden": 176, "universally-overridden": 24},
      "21_variation_surface.py")
check_pred("the interpolated tables are catalogued",
           any(v["shape"] == "interpolated band" for v in
               CAT["tables"].values()),
           "18 interpolated table instances exist [ERC-RAT-005]")

# --- 10. rule model --------------------------------------------------------
print("\n[10] rule model (invariant ERC-RUL-001)")
RM = json.load(open(erc.KB / "rule_model.json", encoding="utf-8"))
check("entry points", RM["entry_points"],
      ["GeneralLiabilityRules/ErcProcess",
       "GeneralLiabilityRules/ErcCalculateTotalPremium"],
      "23_rule_program.py: both in 567/567 packages")
check("distinct Erc* lifecycle names", len(RM["lifecycle_names"]), 10,
      "exactly ten corpus-wide")
check("call graph is acyclic", RM["call_graph"]["acyclic"], True,
      "0 back-edges on GL_CW_20270401_V01")
check("call graph max depth", RM["call_graph"]["max_depth"], 8, "23_rule_program.py")
check("DataDefGroups", RM["n_datadef_groups"], 1032,
      "1:1 with rule files in all 1,032 cases")
check("operator count", RM["n_operators"], 52, "05_rules.py")
check_pred("rounding mode is listed as unspecified",
           any("rounding MODE" in s or "DecimalPlaces" in s
               for s in RM["unspecified_semantics"]),
           "ERC-RAT-002: the sharpest blocker")

# --- 11. invariants register ------------------------------------------------
print("\n[11] invariant register")
INV = cli(["invariants"])
check_pred("at least 20 invariants are registered", INV["n"] >= 20,
           "the register must cover the blocking facts",
           f"got {INV['n']}")
ids = {x["id"] for x in INV["invariants"]}
for want in ("ERC-ID-001", "ERC-ED-001", "ERC-CMP-002", "ERC-CMP-003",
             "ERC-RAT-001", "ERC-RAT-002", "ERC-TER-001", "ERC-FRM-001"):
    check_pred(f"invariant {want} present", want in ids,
               "these are the facts that produce a wrong premium if missed")
check_pred("every invariant has id, severity, statement, evidence and check",
           all(all(x.get(f) for f in
                   ("id", "severity", "statement", "evidence", "check"))
               for x in INV["invariants"]),
           "the output contract requires evidence and an executable check")
check_pred("severities are from the declared vocabulary",
           all(x["severity"] in ("BLOCKER", "MAJOR", "MINOR")
               for x in INV["invariants"]), "AGENT.md output contract")
B = cli(["invariants", "--severity", "BLOCKER"])
check_pred("blockers are a strict subset", 0 < B["n"] < INV["n"],
           "not everything is a blocker", f"{B['n']} of {INV['n']}")

# --- 12. the agent can say 'unverifiable' ----------------------------------
print("\n[12] unverifiable is a valid answer (AGENT.md output contract)")
code, body = cli_code(["rule", "SomeRuleThatDoesNotExistAnywhere"])
check_pred("an unknown rule yields verdict=unverifiable, not a guess",
           code == 2 and '"verdict": "unverifiable"' in body,
           "the agent must decline rather than fabricate",
           f"exit {code}")
code2, _ = cli_code(["juris", "ZZ"])
check_pred("an unknown jurisdiction errors cleanly", code2 == 2,
           "no silent empty answer")

# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
if FAIL:
    print(f"FAILED: {len(FAIL)} of {PASS + len(FAIL)} checks\n")
    for f in FAIL:
        print("  FAIL " + f + "\n")
    sys.exit(1)
print(f"PASSED: all {PASS} checks")
sys.exit(0)
