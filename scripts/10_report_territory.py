"""Whitespace-insensitive content inventory over the latest loss cost notice per state."""
import os, re, json, sys
from collections import defaultdict, Counter
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
PY = os.path.join(HERE, "lc_pypdf")
docs = json.load(open(os.path.join(HERE, "lc_analysis2.json")))
mode = json.load(open(os.path.join(HERE, "lc_extractor.json")))

by_state = defaultdict(list)
for d in docs.values():
    by_state[d["st"]].append(d)
latest = {st: max(v, key=lambda d: d["file"]) for st, v in by_state.items()}

def squash(s):
    return re.sub(r"[\s ]+", "", s).upper()

PAGE = re.compile(r"<<<PAGE (\d+)>>>")
CGMARK = re.compile(r"CG-(LC|ELP|LCADD|ILADD)-(\d{1,3})")

CHECKS = [
    ("LC grid: Prem/Ops 334",        "lc",  "(SUBLINECODE334)"),
    ("LC grid: Prod/COps 336",       "lc",  "(SUBLINECODE336)"),
    ("LC: OCP/PP 335 loss costs",    "lc",  "OWNERSANDCONTRACTORSPROTECTIVE"),
    ("LC: OCP class 16291 priced",   "lc",  "16291."),
    ("LC: Unmanned 370 loss costs",  "lc",  "UNMANNEDAIRCRAFTLIMITEDLIABILITY"),
    ("LC: Railroad 335 loss costs",  "lc",  "RAILROADPROTECTIVELIABILITY"),
    ("LC: Liquor 332 loss costs",    "lc",  "LIQUORLIABILITYCOVERAGE(SUBLINECODE332)"),
    ("ELP: Supplement Proc.1-5",     "all", "ESTIMATEDLOSSPOTENTIALS(ELPS)SUPPLEMENT"),
    ("ELP: 5.B Prem/Ops+Prod/COps",  "elp", "PREMISES/OPERATIONSANDPRODUCTS/COMPLETED"),
    ("ELP: 5.C OCP & PP",            "elp", "OCP&PPELPS"),
    ("ELP: 5.D Liquor",              "elp", "LIQUORLIABILITYELPS"),
    ("ELP: 5.E Railroad Protective", "elp", "RAILROADPROTECTIVELIABILITYELPS"),
    ("ELP: Homogeneity Index",       "elp", "PROCEDURE3.HOMOGENEITYINDEX"),
    ("ELP: Reliability Index",       "elp", "PROCEDURE4.RELIABILITYINDEX"),
    ("LCADD: Loss Cost Mapping",     "all", "LOSSCOSTMAPPINGBYCLASS"),
    ("RRP banded on trains/day",     "all", "NUMBEROFPASSENGER"),
    ("WC-percentage ELP (15191)",    "all", "PERCENTAGEOFOTHERWISEAPPLICABLEWORKERSCOMPENSATION"),
    ("Terrorism content",            "all", "TERRORISM"),
    ("Territory Definitions",        "all", "TERRITORYDEFINITIONS"),
    ("ZIP code content",             "all", "ZIPCODE"),
    ("Stop Gap content",             "all", "STOPGAP"),
    ("Cyber / Electronic Data",      "all", "CYBERINCIDENT"),
    ("Product Withdrawal",           "all", "PRODUCTWITHDRAWAL"),
    ("Loss cost multiplier (LCM)",   "all", "LOSSCOSTMULTIPLIER"),
]

hits = defaultdict(list)
maxlc = {}
for st in sorted(latest):
    t = open(os.path.join(PY, latest[st]["file"][:-4] + ".txt"), encoding="utf-8").read()
    parts = PAGE.split(t)[1:]
    pages = [parts[i + 1] for i in range(0, len(parts), 2)]
    sq_pages = [squash(p) for p in pages]
    lc = "|".join(p for p in sq_pages if "LOSSCOSTPAGES" in p)
    elp = "|".join(p for p in sq_pages if "ESTIMATEDLOSSPOTENTIAL" in p)
    allsq = "|".join(sq_pages)
    scope = {"lc": lc, "elp": elp, "all": allsq}
    for label, sc, needle in CHECKS:
        if needle in scope[sc]:
            hits[label].append(st)
    lcn = [int(n) for n in re.findall(r"CG\s*-\s*LC\s*-\s*(\d{1,3})(?!\d)", t)]
    maxlc[st] = max(lcn) if lcn else 0

print("== CONTENT INVENTORY, latest notice per jurisdiction (51) ==")
for label, sc, needle in CHECKS:
    v = hits[label]
    miss = sorted(set(latest) - set(v))
    print(f"   {label:32} {len(v):3}/51   {'missing: ' + ','.join(miss) if miss and len(miss) <= 12 else ('present in: ' + ','.join(v) if v and len(v) <= 12 else ('-' if not miss else f'{len(miss)} missing'))}")

print("\n== LC PAGE COUNT vs TERRITORY COUNT ==")
ok = 0
for st in sorted(latest):
    T = latest[st]["n_territories"]
    if maxlc[st] == 8 * T + 1:
        ok += 1
    else:
        print(f"   {st}: territories={T}  expected CG-LC-{8*T+1}  observed max CG-LC-{maxlc[st]}")
print(f"   8*T+1 holds for {ok}/51")

print("\n== TERRITORY COUNTS ==")
tc = {st: latest[st]["n_territories"] for st in sorted(latest)}
print("   ", tc)
print("   distribution:", dict(sorted(Counter(tc.values()).items())))
print("   single-territory jurisdictions:", sorted(s for s, n in tc.items() if n == 1))
print("   territory numbers seen:", sorted({t for st in latest for t in latest[st]["territories"]})[:40])
