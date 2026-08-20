import os, json

RULES = r"C:\Projects\ISO_ERC_Files\CF\20260601\CFCW20260601V01\Rules"
TABLES = r"C:\Projects\ISO_ERC_Files\CF\20260601\CFCW20260601V01\Rate Tables"

# Verify premium-chain citations found by manual reading of CommercialPropertyStructureRules.Rule.xml
struct_path = os.path.join(RULES, "CommercialPropertyStructureRules.Rule.xml")
with open(struct_path, encoding="utf-8", errors="ignore") as fh:
    content = fh.read()

checks = {
    'has_SetSpecialBaseRate': 'Name="SetSpecialBaseRate"' in content,
    'has_LookupSpecialBuildingRate': 'Name="LookupSpecialBuildingRate"' in content,
    'has_SetSpecialRate_product': 'Name="SetSpecialRate"' in content,
    'has_SetSpecialCauseOfLossAdjustment': 'Name="SetSpecialCauseOfLossAdjustment"' in content,
    'references_SpecialBuildingRateDef': 'SpecialBuildingRateDef' in content,
    'references_LossCostMultiplier': 'LossCostMultiplier' in content,
}
for k, v in checks.items():
    print(k, v)

# Verify the SpecialBuildingRate table (the one actually consumed in the chain) is header-only at countrywide
tbl_csv = os.path.join(TABLES, "SpecialBuildingRate.RateTable.csv")
with open(tbl_csv, encoding="utf-8-sig", errors="ignore") as fh:
    lines = fh.readlines()
print("SpecialBuildingRate.RateTable.csv line count (1 = header only):", len(lines))
print("Content:", lines)

# Verify entry point chain: Overall Rating -> CommercialPropertyRules ErcProcess/ErcCalculateTotalPremium
overall_path = os.path.join(RULES, "Overall Rating.Rule.xml")
with open(overall_path, encoding="utf-8", errors="ignore") as fh:
    overall = fh.read()
print("\nOverall Rating.Rule.xml references CommercialPropertyRules ErcProcess:", 'Rule="ErcProcess"' in overall)
print("Overall Rating.Rule.xml references ErcCalculateTotalPremium:", 'Rule="ErcCalculateTotalPremium"' in overall)

json.dump({
    "chain_citation_checks": checks,
    "special_building_rate_table_lines": len(lines),
    "special_building_rate_table_content": lines,
}, open(r"C:\Projects\Recursive_Harness_2.0\scripts\erc\_cf_rating_survey.json", "w"), indent=2)
