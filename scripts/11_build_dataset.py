import json, os, re, sys
from collections import defaultdict, Counter

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = r"C:\Projects\Recursive_Harness_2.0\docs\rating-engine"

docs = json.load(open(os.path.join(HERE, "lc_analysis2.json")))
mode = json.load(open(os.path.join(HERE, "lc_extractor.json")))
match = {m["pdf"]: m for m in json.load(open(os.path.join(HERE, "lc_match.json")))["out"]}

by = defaultdict(list)
for d in docs.values():
    by[d["st"]].append(d)
latest = {st: max(v, key=lambda d: d["file"]) for st, v in by.items()}
PRE = set("AK CA CT DC GA KS MA MI NC NJ NY RI TX VT WA".split())

states = {}
for st in sorted(latest):
    d = latest[st]
    states[st] = {
        "notice": d["file"][:-6],
        "notices": len(by[st]),
        "territories": d["n_territories"],
        "territory_list": d["territories"],
        "lc_pages": 8 * d["n_territories"] + 1,
        "classes": d["lc_classes_total"],
        "elp_classes": d["elp_classes"],
        "vintage": "PRE_2027" if st in PRE else "V2027",
        "ocp_loss_costs": st in PRE,
        "extractor": "pypdf" if mode[d["file"]]["mode"] == "PYPDF_FALLBACK" else "pdftotext",
        "erc_edition": match.get(d["file"], {}).get("pkg") or None,
    }

cells = Counter()
for st in latest:
    for k, v in latest[st]["lc_cell_symbols"].items():
        cells[k] += v
elp = Counter()
for st in latest:
    for k, v in latest[st]["elp_cell_symbols"].items():
        elp[k] += v

lc = {
    "corpus": {
        "pdf_count": 472,
        "extracted": 471,
        "failed": ["GL-MI-2027-LC-003-C (truncated PDF, no xref/EOF)"],
        "jurisdictions": 51,
        "multistate_notices": 0,
        "years": {str(y): c for y, c in sorted(Counter(d["year"] for d in docs.values()).items())},
        "notices_per_state_min": min(len(v) for v in by.values()),
        "notices_per_state_max": max(len(v) for v in by.values()),
        "extractor": {"pdftotext_layout": 389, "pypdf_required": 83,
                      "latest_needing_pypdf": sum(1 for st in latest
                                                  if mode[latest[st]["file"]]["mode"] == "PYPDF_FALLBACK")},
        "erc_matched_on_citation": 415,
    },
    "cell_vocabulary": {
        "numeric": cells["numeric"],
        "not_offered_dash": cells["not_offered_dash"],
        "refer_a": cells["rtc_(a)"],
        "total": sum(cells.values()),
    },
    "elp_vocabulary": {k: v for k, v in elp.most_common()},
    "vintage": {
        "PRE_2027": sorted(PRE),
        "V2027": sorted(set(latest) - PRE),
    },
    "ocp_withdrawal_by_year": {"2020": [54, 54], "2021": [141, 141], "2022": [37, 37],
                               "2023": [57, 57], "2024": [49, 49], "2025": [48, 48],
                               "2026": [27, 27], "2027": [22, 58]},
    "class_codes": {"in_all_51": 947, "pre2027_only": 229, "v2027_only": 204, "union": 1396},
    "subline_rate_source": {
        "334": {"label": "Premises/Operations", "loss_costs": 51, "elp": 51, "basic_limit": "100/200"},
        "336": {"label": "Products/Completed Operations", "loss_costs": 51, "elp": 51, "basic_limit": "100/200"},
        "335 OCP": {"label": "OCP / Principals Protective", "loss_costs": 15, "elp": 51, "basic_limit": "100/200"},
        "335 RRP": {"label": "Railroad Protective", "loss_costs": 0, "elp": 51, "basic_limit": "100/300"},
        "332": {"label": "Liquor Liability", "loss_costs": 0, "elp": 51, "basic_limit": "100/200"},
        "370": {"label": "Unmanned Aircraft", "loss_costs": 51, "elp": 0, "basic_limit": "100/200"},
    },
    "territory": {
        "distribution": dict(sorted(Counter(latest[st]["n_territories"] for st in latest).items())),
        "multi_territory": sorted(st for st in latest if latest[st]["n_territories"] > 1),
        "a_rule_states": sorted("AL AZ CO CT GA IA IL IN KS KY LA MA MD MI MN MO NE NJ OH OK OR PA RI TN VA WA WI".split()),
        "territory_rated_without_a_rule": ["CA", "FL", "NY", "TX"],
    },
    "states": states,
}

p = os.path.join(DOCS, "dataset.json")
D = json.load(open(p, encoding="utf-8"))
D["generated_from"] = ("ISO Commercial Lines Manual Division Six - General Liability: "
                       "Rules notices (503 PDFs) and Loss Cost notices (472 PDFs)")
D["loss_costs"] = lc
json.dump(D, open(p, "w", encoding="utf-8"), indent=1)
print("dataset.json updated; loss_costs keys:", list(lc))
print("cells", lc["cell_vocabulary"])
print("elp", lc["elp_vocabulary"])
