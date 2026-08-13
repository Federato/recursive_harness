"""Structural analysis of the GL Loss Costs corpus from pypdf text (page-tagged)."""
import os, re, json
from collections import defaultdict, Counter

HERE = os.path.dirname(os.path.abspath(__file__))
PY = os.path.join(HERE, "lc_pypdf")

PAGE = re.compile(r"<<<PAGE (\d+)>>>")
MARKER = re.compile(r"\bCG-([A-Z]+)-(\d{1,3})\b")
EDITION = re.compile(r"(\d{1,3})(?:st|nd|rd|th)\s+Edition\s+(\d{1,2}-\d{2})", re.I)
TERR = re.compile(r"Territory\s*(\d{3})", re.I)
TERRHDR = re.compile(r"PREM/OPS\s+TERR\.\s*(\d{3})", re.I)
BASIC = re.compile(r"\$?([\d,]{5,9})/([\d,]{5,9})\s+BASIC LIMIT", re.I)
SUBLINE = re.compile(r"Subline\s*Code\s*(\d{3})", re.I)

# LC grid row: 4 repetitions of  <5-digit> <val> <val>
V = r"(?:\(a\)|[–—-]|\d[\d,]*\.?\d*|\.\d+)"
LCPAIR = re.compile(r"(?<![\d.])(\d{5})\s+(" + V + r")\s+(" + V + r")(?![\d.])")
# ELP row: <5-digit> then tokens from {Manual, RTC, Incl., $n} with optional H/R
ELPTOK = re.compile(r"(?<![\d.])(\d{5})\s+(Manual|RTC|Incl\.|\$[\d,]*\.?\d*)")
HR = re.compile(r"\b([1-5])/([A-E])\b")

docs = {}
for fn in sorted(os.listdir(PY)):
    if not fn.endswith(".txt"):
        continue
    raw = open(os.path.join(PY, fn), encoding="utf-8").read()
    if len(raw.strip()) < 200:
        continue
    pages = PAGE.split(raw)[1:]
    pages = [(int(pages[i]), pages[i + 1]) for i in range(0, len(pages), 2)]

    d = {"file": fn[:-4] + ".pdf", "st": fn.split("-")[1], "year": int(fn.split("-")[2]),
         "pages": len(pages)}

    fam = Counter(); maxpg = {}
    editions = set(); sublines = set(); basics = set()
    terr_by_page = {}
    lc_cells = defaultdict(dict)      # territory -> class -> (po, pc)
    lc_sym = Counter()
    elp_classes = set(); elp_sym = Counter(); hr_count = 0
    pagekind = Counter()

    for pno, ptxt in pages:
        for f2, n in MARKER.findall(ptxt):
            fam[f2] += 1
            maxpg[f2] = max(maxpg.get(f2, 0), int(n))
        for a, b in EDITION.findall(ptxt):
            editions.add(f"{a} Edition {b}")
        sublines |= set(SUBLINE.findall(ptxt))
        for a, b in BASIC.findall(ptxt):
            basics.add(f"{a}/{b}")

        up = ptxt.upper()
        is_lc = "LOSS COST PAGES" in up
        is_elp = "ESTIMATED LOSS POTENTIAL" in up
        pagekind["LC" if is_lc else "ELP" if is_elp else "OTHER"] += 1

        if is_lc:
            t = TERRHDR.search(ptxt)
            terr = t.group(1) if t else (TERR.search(ptxt).group(1) if TERR.search(ptxt) else "n/a")
            terr_by_page[pno] = terr
            for line in ptxt.splitlines():
                for cc, v1, v2 in LCPAIR.findall(line):
                    lc_cells[terr][cc] = (v1, v2)
                    for v in (v1, v2):
                        lc_sym["rtc_(a)" if v == "(a)" else
                               "not_offered_dash" if v in ("–", "—", "-") else
                               "numeric"] += 1
        if is_elp:
            for line in ptxt.splitlines():
                # split the line into per-class column groups
                idx = [(m.start(), m.group(1)) for m in re.finditer(r"(?<![\d.$])(\d{5})(?=\s)", line)]
                for j, (pos, cc) in enumerate(idx):
                    end = idx[j + 1][0] if j + 1 < len(idx) else len(line)
                    body = line[pos + 5:end]
                    toks = re.findall(r"Manual|RTC|Incl\.|\$[\d,]*\.?\d+", body)
                    if not toks:
                        continue
                    elp_classes.add(cc)
                    for side, t in zip(("po", "pc"), toks[:2]):
                        elp_sym[f"{side}:" + (t if t in ("Manual", "RTC", "Incl.") else "$ELP")] += 1
            hr_count += len(HR.findall(ptxt))

    d["marker_families"] = dict(fam)
    d["max_marker"] = maxpg
    d["page_kinds"] = dict(pagekind)
    d["editions"] = sorted(editions)
    d["sublines"] = sorted(sublines)
    d["basic_limits"] = sorted(basics)
    d["territories"] = sorted(t for t in lc_cells if t != "n/a")
    d["n_territories"] = len(d["territories"])
    d["lc_classes_per_terr"] = {t: len(v) for t, v in lc_cells.items()}
    allc = set()
    for v in lc_cells.values():
        allc |= set(v)
    d["lc_classes_total"] = len(allc)
    d["lc_class_list"] = sorted(allc)
    d["lc_cell_symbols"] = dict(lc_sym)
    d["elp_classes"] = len(elp_classes)
    d["elp_cell_symbols"] = dict(elp_sym)
    d["hr_pairs"] = hr_count
    up = raw.upper()
    for k, pat in [("unmanned", "UNMANNED AIRCRAFT"), ("ocp", "OWNERS AND CONTRACTORS PROTECTIVE"),
                   ("railroad", "RAILROAD PROTECTIVE"), ("liquor", "LIQUOR LIABILITY"),
                   ("stopgap", "STOP GAP"), ("terrorism", "TERRORISM"),
                   ("zip", "ZIP"), ("territory_defs", "TERRITORY DEFINITIONS"),
                   ("cyber", "CYBER"), ("prodwithdrawal", "PRODUCT WITHDRAWAL"),
                   ("composite", "COMPOSITE RATING"), ("elp_supp", "ESTIMATED LOSS POTENTIALS (ELPS) SUPPLEMENT")]:
        d["has_" + k] = pat in up
    docs[d["file"]] = d

json.dump(docs, open(os.path.join(HERE, "lc_analysis2.json"), "w"), indent=0)
print("analyzed", len(docs))
