import os, re, json, collections

BASE = r"C:\Projects\ISO_ERC_Files\CF\20260601\CFCW20260601V01\Rules"

files = [f for f in os.listdir(BASE) if f.lower().endswith(".xml")]
print("Total rule xml files:", len(files))

all_start_commercialproperty = sum(1 for f in files if f.startswith("CommercialProperty"))
all_end_rulesxml = sum(1 for f in files if f.endswith("Rules.Rule.xml"))
print("Files starting with 'CommercialProperty':", all_start_commercialproperty)
print("Files ending with 'Rules.Rule.xml':", all_end_rulesxml)

# strip prefix/suffix
stems = []
for f in files:
    s = f
    if s.startswith("CommercialProperty"):
        s = s[len("CommercialProperty"):]
    if s.endswith(".Rule.xml"):
        s = s[:-len(".Rule.xml")]
    stems.append(s)

# known coverage-form suffix tokens (from observed sample)
coverage_suffixes = [
    "BasicGroupICoverageRules", "BasicGroupIICoverageRules", "BroadCoverageRules",
    "EarthquakeCoverageRules", "SpecialCoverageRules", "SpecialClassRules",
    "DetailRules", "Rules"
]
suffix_hits = collections.Counter()
for s in stems:
    matched = None
    for suf in coverage_suffixes:
        if s.endswith(suf):
            matched = suf
            break
    suffix_hits[matched or "OTHER"] += 1

print("\n=== Coverage-form suffix token counts ===")
for k, v in suffix_hits.most_common():
    print(f"{v:4d}  {k}")

# "Detail" companion pairing: how many base rules have a *Detail* counterpart
detail_files = set(s for s in stems if s.endswith("DetailRules"))
base_files = set(s for s in stems if s.endswith("Rules") and not s.endswith("DetailRules"))
paired = 0
for d in detail_files:
    base_guess = d[:-len("DetailRules")] + "Rules"
    if base_guess in base_files:
        paired += 1
print(f"\nDetail-suffixed files: {len(detail_files)}, of which {paired} have a matching non-Detail base file")

# top-level topic word after stripping prefix: first camelCase word
def first_word(s):
    m = re.match(r"[A-Z][a-z0-9]*", s)
    return m.group(0) if m else s
topic_counts = collections.Counter(first_word(s) for s in stems)
print("\n=== First topic word after 'CommercialProperty' prefix (top 30) ===")
for k, v in topic_counts.most_common(30):
    print(f"{v:4d}  {k}")
print("\nDistinct first-topic-words:", len(topic_counts))

json.dump({
    "total_files": len(files),
    "all_start_commercialproperty": all_start_commercialproperty,
    "all_end_rulesxml": all_end_rulesxml,
    "coverage_suffix_counts": dict(suffix_hits),
    "detail_files_count": len(detail_files),
    "detail_paired_with_base": paired,
    "topic_word_counts": dict(topic_counts),
}, open(r"C:\Projects\Recursive_Harness_2.0\scripts\erc\_cf_rule_survey.json","w"), indent=2)
