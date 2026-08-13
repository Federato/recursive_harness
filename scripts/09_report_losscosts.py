"""Final roll-up over the pypdf-extracted loss cost corpus."""
import os, re, json, sys
from collections import defaultdict, Counter
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
PY = os.path.join(HERE, "lc_pypdf")
docs = json.load(open(os.path.join(HERE, "lc_analysis2.json")))
mode = json.load(open(os.path.join(HERE, "lc_extractor.json")))
match = json.load(open(os.path.join(HERE, "lc_match.json")))["out"]
matchby = {m["pdf"]: m for m in match}

by_state = defaultdict(list)
for d in docs.values():
    by_state[d["st"]].append(d)
latest = {st: max(v, key=lambda d: d["file"]) for st, v in by_state.items()}

print("== CORPUS ==")
print("docs analysed:", len(docs), " states:", len(by_state))
print("year distribution:", dict(sorted(Counter(d["year"] for d in docs.values()).items())))
print("notices per state: min %d max %d median %d" % (
    min(len(v) for v in by_state.values()), max(len(v) for v in by_state.values()),
    sorted(len(v) for v in by_state.values())[len(by_state) // 2]))
print("extractor modes:", Counter(v["mode"] for v in mode.values()))
print("latest-per-state needing pypdf:",
      sum(1 for st, d in latest.items() if mode[d["file"]]["mode"] == "PYPDF_FALLBACK"))

print("\n== UNIVERSAL STRUCTURE (across all analysed docs) ==")
print("page kinds:", Counter(k for d in docs.values() for k in d["page_kinds"]))
print("basic limits:", Counter(b for d in docs.values() for b in d["basic_limits"]))
print("sublines:", Counter(s for d in docs.values() for s in d["sublines"]))
print("marker families:", Counter(k for d in docs.values() for k in d["marker_families"]))
print("ELP pages (max CG-ELP-n):", Counter(d["max_marker"].get("ELP") for d in docs.values()))

# territory / page relationship
print("\n== TERRITORY MODEL (latest per state) ==")
rows = []
for st in sorted(latest):
    d = latest[st]
    lcmax = d["max_marker"].get("LC", 0)
    nt = d["n_territories"]
    percls = sorted(set(d["lc_classes_per_terr"].values()))
    rows.append((st, d["file"], d["year"], nt, lcmax, d["lc_classes_total"], percls,
                 d["elp_classes"], mode[d["file"]]["mode"] == "PYPDF_FALLBACK",
                 d["max_marker"].get("ELP", 0), "370" in d["sublines"]))
print(f"{'ST':3} {'notice':26} {'terr':4} {'CG-LC-n':7} {'LCcls':6} {'ELPcls':6} {'UAV':4} {'fallback'}")
for r in rows:
    print(f"{r[0]:3} {r[1][:-4]:26} {r[3]:<4} {r[4]:<7} {r[5]:<6} {r[7]:<6} {'Y' if r[10] else '-':4} {'pypdf' if r[8] else 'pdftotext'}")

print("\nterritory count distribution:", dict(sorted(Counter(r[3] for r in rows).items())))
print("LC page count = 8*T+1 holds:", sum(1 for r in rows if r[4] == 8 * r[3] + 1), "of", len(rows))
print("distinct lc class counts:", Counter(r[5] for r in rows))
print("distinct elp class counts:", Counter(r[7] for r in rows))

# cell vocabulary aggregated over latest per state
agg = Counter()
for st in latest:
    for k, v in latest[st]["lc_cell_symbols"].items():
        agg[k] += v
print("\n== LC CELL VOCABULARY (latest per state, all territories) ==", dict(agg))
tot = sum(agg.values())
for k, v in agg.most_common():
    print(f"   {k:20} {v:8}  {100*v/tot:5.1f}%")

aggE = Counter()
for st in latest:
    for k, v in latest[st]["elp_cell_symbols"].items():
        aggE[k] += v
print("\n== ELP CELL VOCABULARY ==")
totE = sum(aggE.values())
for k, v in aggE.most_common():
    print(f"   {k:20} {v:8}  {100*v/totE:5.1f}%")

# class code set comparison across states
sets = {st: set(latest[st]["lc_class_list"]) for st in latest}
big = max(sets.values(), key=len)
print("\n== CLASS CODE SET ==")
print("largest state set:", len(big))
common = set.intersection(*sets.values())
union = set.union(*sets.values())
print("intersection across all states:", len(common), " union:", len(union))
print("states whose set == union:", sum(1 for s in sets.values() if s == union))

# per-state extras present on the final LC page
print("\n== OPTIONAL CONTENT (latest per state) ==")
extras = defaultdict(list)
PAGE = re.compile(r"<<<PAGE (\d+)>>>")
for st in sorted(latest):
    fn = os.path.join(PY, latest[st]["file"][:-4] + ".txt")
    t = open(fn, encoding="utf-8").read()
    parts = PAGE.split(t)[1:]
    pages = [parts[i + 1] for i in range(0, len(parts), 2)]
    lcp = "\n".join(p for p in pages if "LOSS COST PAGES" in p.upper())
    elpp = "\n".join(p for p in pages if "ESTIMATED LOSS POTENTIAL" in p.upper())
    up = t.upper()
    def add(k, cond):
        if cond:
            extras[k].append(st)
    add("LC: Prem/Ops 334 grid", "(Subline Code 334)" in lcp)
    add("LC: Prod/COps 336 grid", "(Subline Code 336)" in lcp)
    add("LC: OCP/PP 335 table", bool(re.search(r"16291\s+(\.\d+|\d+\.\d+|RTC)", lcp)))
    add("LC: Unmanned 370 table", "UNMANNED AIRCRAFT LIMITED LIABILITY" in lcp.upper())
    add("LC: Liquor 332 table", "SUBLINE CODE 332" in lcp.upper())
    add("LC: Railroad 335 table", "SUBLINE CODE 335" in lcp.upper() and "RAILROAD" in lcp.upper())
    add("LCADD: mapping by class", "LOSS COST MAPPING BY CLASS" in up)
    add("ELP: Supplement Proc 1-5", "ESTIMATED LOSS POTENTIALS (ELPS) SUPPLEMENT" in up)
    add("ELP: 5.B PremOps/ProdCOps", "PREMISES/OPERATIONS AND PRODUCTS/COMPLETED" in elpp.upper())
    add("ELP: 5.C OCP & PP", "OCP & PP ELPS" in elpp.upper())
    add("ELP: 5.D Liquor", "LIQUOR LIABILITY ELPS" in elpp.upper())
    add("ELP: 5.E Railroad", "RAILROAD PROTECTIVE LIABILITY ELPS" in elpp.upper())
    add("ELP: Homogeneity/Reliability", "HOMOGENEITY INDEX" in elpp.upper())
for k, v in extras.items():
    miss = sorted(set(latest) - set(v))
    print(f"   {k:30} {len(v):3}/{len(latest)}   missing: {','.join(miss) if miss else '-'}")

# how often does a state's loss costs change edition-to-edition?
print("\n== CHURN ==")
print("notices per state:", {st: len(v) for st, v in sorted(by_state.items())})
