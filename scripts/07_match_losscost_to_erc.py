import os, re, json
from collections import defaultdict
import openpyxl

HERE = os.path.dirname(os.path.abspath(__file__))
PAGES = os.path.join(HERE, "lc_pages")
ROOT = r"C:\Projects\Recursive_Harness_2.0"

# ---------------- 1. Parse each loss-cost notice page 1 ----------------
CIRC_RE = re.compile(r"\b(LI-[A-Z]{2,3}-\d{4}-\d{3})\b")
FILING_RE = re.compile(r"\b(GL-\d{4}-[A-Z0-9]{3,8})\b")
NOTICE_RE = re.compile(r"\b(GL-[A-Z]{2}-\d{4}-LC-\d{3})\b")
DATED_CIRC_RE = re.compile(r"(LI-[A-Z]{2,3}-\d{4}-\d{3})\s*\((\d{2}/\d{2}/\d{4})\)")
EDMARK_RE = re.compile(r"\b(\d{1,2})[/-](\d{2})\b")

pdfs = []
for fn in sorted(os.listdir(PAGES)):
    if not fn.endswith(".txt"):
        continue
    pdf = fn[:-4] + ".pdf"
    txt = open(os.path.join(PAGES, fn), encoding="utf-8").read()
    head = txt[:4000]
    st = pdf.split("-")[1]
    m = NOTICE_RE.search(head)
    notice = m.group(1) if m else pdf[:-6]
    # restrict reference scraping to the reference-information block
    ref_block = head
    ix = head.upper().find("REFERENCE INFORMATION")
    if ix >= 0:
        ref_block = head[ix:ix + 1500]
    circs = []
    for c in CIRC_RE.findall(ref_block):
        if c not in circs:
            circs.append(c)
    filings = []
    for f in FILING_RE.findall(ref_block):
        if f not in filings:
            filings.append(f)
    cdates = dict(DATED_CIRC_RE.findall(ref_block))
    pdfs.append(dict(pdf=pdf, st=st, notice=notice, circs=circs, filings=filings,
                     cdates=cdates, empty=len(txt.strip()) < 40))

print("parsed", len(pdfs), "| no circular:", sum(1 for p in pdfs if not p["circs"]))

# ---------------- 2. Load ERC circular index ----------------
wb = openpyxl.load_workbook(os.path.join(ROOT, "GL_ERC_Edition_Hierarchy.xlsx"), read_only=True)
ws = wb["ERC Circulars"]
rows = list(ws.iter_rows(values_only=True))
hdr = {h: i for i, h in enumerate(rows[0])}

# circular -> per state list of (edition_date, package, cw_parent, type, filing, desc)
by_state_circ = defaultdict(list)
by_state_filing = defaultdict(list)
circ_meta = {}
for r in rows[1:]:
    st = r[hdr["ST"]]
    pkg = r[hdr["ERC package"]]
    ed = r[hdr["Edition date"]]
    cw = r[hdr["CW parent"]]
    circ = r[hdr["Circular"]]
    eff = r[hdr["Eff. date (as stated in THIS package)"]]
    typ = r[hdr["Type"]]
    filing = r[hdr["Filing reference"]] or ""
    desc = r[hdr["Circular description"]]
    rec = (ed, pkg, cw, typ, filing, desc, eff)
    if circ:
        by_state_circ[(st, circ)].append(rec)
        if circ not in circ_meta or not circ_meta[circ][0]:
            circ_meta[circ] = (desc, typ)
    for f in re.split(r"[,\s]+", str(filing)):
        f = f.strip()
        if FILING_RE.fullmatch(f):
            by_state_filing[(st, f)].append(rec)

print("ERC circular keys:", len(by_state_circ), "| filing keys:", len(by_state_filing))

def dkey(d):
    if not d:
        return "9999-99-99"
    mm, dd, yy = str(d).split("/")
    return f"{yy}-{mm}-{dd}"

# ---------------- 3. Match ----------------
out = []
detail = []
for p in pdfs:
    st = p["st"]
    matched = None
    method = None
    conf = None
    key_used = None
    hits = []
    # Try circular reference first (state-scoped, then CW-scoped)
    for c in p["circs"]:
        for scope in (st, "CW"):
            recs = by_state_circ.get((scope, c))
            if recs:
                hits.extend(recs)
                if key_used is None:
                    key_used, method = c, "Circular reference"
                break
        for scope in (st, "CW"):
            for rec in by_state_circ.get((scope, c), []):
                detail.append(dict(pdf=p["pdf"], notice=p["notice"], st=st,
                                   keytype="Circular reference", key=c, scope=scope,
                                   pkg=rec[1], ed=rec[0], cw=rec[2], typ=rec[3],
                                   filing=rec[4], desc=rec[5]))
    if not hits:
        for f in p["filings"]:
            for scope in (st, "CW"):
                recs = by_state_filing.get((scope, f))
                if recs:
                    hits.extend(recs)
                    if key_used is None:
                        key_used, method = f, "Filing reference"
                    for rec in recs:
                        detail.append(dict(pdf=p["pdf"], notice=p["notice"], st=st,
                                           keytype="Filing reference", key=f, scope=scope,
                                           pkg=rec[1], ed=rec[0], cw=rec[2], typ=rec[3],
                                           filing=rec[4], desc=rec[5]))
                    break

    if hits:
        state_hits = [h for h in hits if h[1] and h[1].split()[1] == st]
        pool = state_hits or hits
        pool = sorted(set(pool), key=lambda h: (dkey(h[0]), h[1] or ""))
        matched = pool[0]
        conf = "High" if method == "Circular reference" and state_hits else \
               ("Medium" if state_hits else "Low")
        all_eds = ", ".join(sorted({h[1] for h in pool if h[1]},
                                   key=lambda pk: pk.split()[-2] if len(pk.split()) > 2 else pk))
    else:
        all_eds = ""

    circ_desc = ""
    circ_type = ""
    for c in p["circs"]:
        if c in circ_meta:
            circ_desc, circ_type = circ_meta[c]
            break

    out.append(dict(
        pdf=p["pdf"], st=st, notice=p["notice"],
        circs="; ".join(p["circs"]),
        circ_dates="; ".join(f"{k} ({v})" for k, v in p["cdates"].items()),
        filings="; ".join(p["filings"]),
        circ_type=circ_type, circ_desc=circ_desc,
        method=method or ("no reference found on page 1" if not p["circs"] and not p["filings"]
                          else "reference not present in ERC"),
        key=key_used or "",
        conf=conf or "Unmatched",
        pkg=matched[1] if matched else "",
        ed=matched[0] if matched else "",
        cw=matched[2] if matched else "",
        all_eds=all_eds,
        note="page 1 could not be extracted (file truncated)" if p["empty"] else "",
    ))

json.dump({"out": out, "detail": detail}, open(os.path.join(HERE, "lc_match.json"), "w"))
from collections import Counter
print(Counter(o["conf"] for o in out))
print(Counter(o["method"] for o in out))
