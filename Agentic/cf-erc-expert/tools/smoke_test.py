#!/usr/bin/env python3
"""Smoke test for cf-erc-expert.

Every case asserts a fact independently readable from knowledge/*.json (see
each file's "_note" for how it was measured). If the knowledge base drifts,
or the CLI stops answering correctly, these fail loudly.

    python smoke_test.py            # run all
    python smoke_test.py -v         # show every passing case

Exit 0 if all pass, 1 otherwise. Standard library only.
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
print("cf-erc-expert smoke test")
print("=" * 70)

# --- 1. corpus shape ---------------------------------------------------
print("\n[1] corpus shape (corpus.json)")
C = cli(["corpus"])
check("edition folders", C["n_edition_folders"], 8, "cf_01_inventory.py")
check("total package dirs (all editions)", C["total_package_dirs_all_editions"],
      438, "cf_01_inventory.py")
check("20260601 package count", C["precise_edition_detail"]["n_packages"], 66,
      "cf_01_inventory.py precise_edition_detail")
check("20260601 distinct jurisdictions", C["precise_edition_detail"]["n_distinct_jurisdictions"],
      42, "cf_01_inventory.py")
check("countrywide rule files (20260601)", C["countrywide_package_20260601_detail"]["categories"]["Rules"],
      882, "cf_01_inventory.py countrywide_package_20260601_detail")

# --- 2. package identity -------------------------------------------------
print("\n[2] package identity (packages.json)")
I = cli(["identity", "CF AK 20260601 V01"])
p = I["packages"]["CF AK 20260601 V01"]
check("AK package jurisdiction", p["jurisdiction"], "AK", "cf_02_packages.py")
check("AK package parent", p["parent_package_id"], "CF_CW_20260601_V01",
      "the single xs:import in the AK XSD")
code, _ = cli_code(["identity", "CF ZZ 20260601 V01"])
check_pred("unknown package errors cleanly", code == 2, "not present in the 66-package set")

# --- 3. jurisdiction lookup ----------------------------------------------
print("\n[3] jurisdiction lookup (jurisdictions.json)")
J = cli(["juris", "CA"])
check("CA present in 20260601", J["present_in_20260601"], True, "jurisdictions_20260601")
check("CA n_packages in 20260601", J["detail_20260601"]["n_packages"], 2,
      "jurisdictions_20260601.CA")
FL = cli(["juris", "FL"])
check("FL NOT present in 20260601", FL["present_in_20260601"], False,
      "FL is one of the not_sampled_large_states / absent from 20260601 folder")
code2, _ = cli_code(["juris", "ZZ"])
check_pred("nonexistent jurisdiction errors cleanly", code2 == 2,
           "ZZ is in missing_from_corpus territory")

# --- 4. table catalogue ---------------------------------------------------
print("\n[4] table catalogue (table_catalogue.json)")
TB = cli(["table", "SpecialBuildingRate"])
m = TB["matches"]["SpecialBuildingRate.RateTable.csv"]
check("SpecialBuildingRate is header-only", m["lines"], 1,
      "cf_06_table_catalogue.py representative_tables_examined")
check("population survey header-only count", TB["population_survey"]["header_only_0_data_rows"],
      103, "cf_06_table_catalogue.py full census of 460 tables")
check("population survey populated count", TB["population_survey"]["populated_1plus_data_rows"],
      357, "103 + 357 = 460")
code3, _ = cli_code(["table", "NoSuchTableXYZ"])
check_pred("unmatched table name returns exit 2 (unverifiable)", code3 == 2,
           "not individually examined this session")

# --- 5. rule model ---------------------------------------------------------
print("\n[5] rule model (rule_model.json)")
RM = json.load(open(erc.KB / "rule_model.json", encoding="utf-8"))
check("total rule files", RM["total_rule_files"], 882, "cf_05_rule_model.py")
check("rul:Product occurrence count", RM["control_flow_elements"]["element_counts_combined"]["rul:Product"],
      342, "5-file element survey")
check_pred("rul:Multiply does not appear as a key",
           "rul:Multiply" not in RM["control_flow_elements"]["element_counts_combined"],
           "CF's multiplication operator is rul:Product, not rul:Multiply")
R = cli(["rule", "Product"])
check("rule query for Product finds the control-flow element", R["matches"]["control_flow_element"]["rul:Product"],
      342, "erc.py rule command searches element_counts_combined")
code4, body4 = cli_code(["rule", "NoSuchRuleNameAtAll"])
check_pred("unknown rule/keyword yields verdict=unverifiable", code4 == 2 and
           '"verdict": "unverifiable"' in body4,
           "the agent must decline rather than fabricate")

# --- 6. territory ------------------------------------------------------
print("\n[6] territory (territory.json)")
T = cli(["territory"])
check("n sampled packages", len(T["sampled_packages"]), 10, "cf_04_territory.py")
NY = cli(["territory", "NY"])
check("NY scheme", NY["scheme"], "COUNTY_PLACE", "cf_04_territory.py NY sample")
check("NY data rows", NY["n_data_rows"], 1302, "cf_04_territory.py")
MT = cli(["territory", "MT"])
check("MT scheme", MT["scheme"], "SINGLE_TERRITORY", "cf_04_territory.py MT sample")
code5, _ = cli_code(["territory", "WA"])
check_pred("unsampled jurisdiction (WA) is reported unverifiable", code5 == 2,
           "WA is not among the 10 sampled packages")

# --- 7. rating chain -------------------------------------------------------
print("\n[7] rating chain (rating.json)")
Rt = cli(["rating"])
check("entry point file", Rt["entry_point"]["file"], "Rules/Overall Rating.Rule.xml",
      "cf_08_rating.py direct read")
check("traced chain step count", len(Rt["traced_building_premium_chain"]["steps"]), 4,
      "SetSpecialBaseRate -> LookupSpecialBuildingRate -> SetSpecialRate -> "
      "SetSpecialCauseOfLossAdjustment")

# --- 8. schema comparison ----------------------------------------------
print("\n[8] schema comparison (composition.json)")
S = cli(["schema"])
check("CF complexType count", S["cf_schema"]["complexType_count"], 1275,
      "cf_07_composition.py grep -c")
check("GL complexType count", S["gl_comparison"]["complexType_count"], 1055,
      "cf_07_composition.py grep -c on GL's countrywide XSD")
check_pred("both schemas are monolithic (single file)",
           S["cf_schema"]["single_file_monolithic"] and S["gl_comparison"]["single_file_monolithic"],
           "the monolithic-vs-split hypothesis was NOT confirmed as a CF-specific trait")

# --- 9. invariants register -------------------------------------------------
print("\n[9] invariant register (invariants.json)")
INV = cli(["invariants"])
check("n invariants registered", INV["n"], 8, "invariants.json invariants list length")
ids = {x["id"] for x in INV["invariants"]}
for want in ("CF-ERC-ID-001", "CF-ERC-ID-002", "CF-ERC-ID-003", "CF-ERC-ID-004",
             "CF-ERC-ID-005", "CF-ERC-ID-006", "CF-ERC-ID-007", "CF-ERC-ID-008"):
    check_pred(f"invariant {want} present", want in ids, "the full seed register")
check_pred("every invariant has id, severity, title, statement, evidence",
           all(all(x.get(f) for f in ("id", "severity", "title", "statement", "evidence"))
               for x in INV["invariants"]),
           "the output contract requires evidence for each claim")
B = cli(["invariants", "--severity", "BLOCKER"])
check("exactly one BLOCKER invariant", B["n"], 1,
      "only CF-ERC-ID-002 is severity BLOCKER")
code6, _ = cli_code(["invariants", "--id", "CF-ERC-ID-999"])
check_pred("unknown invariant id errors cleanly", code6 == 2, "not in the register")

# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
if FAIL:
    print(f"FAILED: {len(FAIL)} of {PASS + len(FAIL)} checks\n")
    for f in FAIL:
        print("  FAIL " + f + "\n")
    sys.exit(1)
print(f"PASSED: all {PASS} checks")
sys.exit(0)
