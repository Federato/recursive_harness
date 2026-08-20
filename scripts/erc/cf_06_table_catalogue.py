import os, re, json, collections, csv, io

BASE = r"C:\Projects\ISO_ERC_Files\CF\20260601\CFCW20260601V01\Rate Tables"

files = os.listdir(BASE)
print("Total files in Rate Tables:", len(files))

exts = collections.Counter(os.path.splitext(f)[1].lower() for f in files)
print("Extensions:", dict(exts))

# Group by leading camel-case topic word(s) - try prefix before "Rate"
def prefix_group(f):
    stem = os.path.splitext(f)[0]
    # common pattern: <Coverage><Descriptor>Rate  or similar; try to split at "Rate" occurrence
    m = re.match(r"^([A-Za-z]+?)(Rate)", stem)
    if m:
        return m.group(1) + m.group(2)
    # fallback: first camel word
    m2 = re.match(r"[A-Z][a-z0-9]*", stem)
    return m2.group(0) if m2 else stem

groups = collections.Counter(prefix_group(f) for f in files)
print("\n=== Groups by <Prefix>Rate pattern (top 40) ===")
for k, v in groups.most_common(40):
    print(f"{v:4d}  {k}")
print("\nDistinct groups:", len(groups))

# also try grouping by first 2 camel words after stripping common prefixes
def first_topic_words(f, n=2):
    stem = os.path.splitext(f)[0]
    words = re.findall(r"[A-Z][a-z0-9]*", stem)
    return " ".join(words[:n])

topic2 = collections.Counter(first_topic_words(f) for f in files)
print("\n=== First-2-camel-word groups (top 30) ===")
for k, v in topic2.most_common(30):
    print(f"{v:4d}  {k}")

json.dump({
    "total_files": len(files),
    "extensions": dict(exts),
    "prefix_rate_groups": dict(groups),
    "first2word_groups": dict(topic2),
}, open(r"C:\Projects\Recursive_Harness_2.0\scripts\erc\_cf_table_survey.json", "w"), indent=2)
