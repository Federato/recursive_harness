#!/usr/bin/env python
"""
iso.py - retrieval CLI over the ISO GL corpora for the ISO Circular Expert agent.

Every answer is traceable to a named PDF, page and line. Nothing here infers.

  python iso.py circular LI-GL-2022-325
  python iso.py notice   GL-NJ-2026-RU-001
  python iso.py state    NJ
  python iso.py rule     45 --st TX
  python iso.py grep     "increased limits tables are displayed" --kind RU --max 5
  python iso.py page     GL-NJ-2026-RU-001 27
  python iso.py territory NJ --zip 07030
  python iso.py rate     TX --class 91581
  python iso.py invariant --severity BLOCKER
  python iso.py effective NJ --date 2026-06-01
"""
import argparse, json, os, re, sys, glob
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB = os.path.join(ROOT, "knowledge")
TXT = os.path.join(ROOT, "text")
PDF_ROOT = os.path.join(os.path.dirname(os.path.dirname(ROOT)),
                        "Commercial Line Manuals", "GL")

_cache = {}


def kb(name):
    if name not in _cache:
        p = os.path.join(KB, name + ".json")
        _cache[name] = json.load(open(p, encoding="utf-8"))
    return _cache[name]


def squash(s):
    return re.sub(r"\s+", "", s).upper()


def text_path(notice):
    """notice like GL-NJ-2026-RU-001 (with or without -C suffix)."""
    stem = notice[:-2] if notice.endswith("-C") else notice
    kind = ("terrorism" if "-TERXV-" in stem else
            "scheduleexperience" if "-CGLES-" in stem else
            "compositerating" if "-CRP-" in stem else
            "rules" if "-RU-" in stem else "losscosts")
    for cand in (stem + "-C.txt", stem + ".txt"):
        p = os.path.join(TXT, kind, cand)
        if os.path.exists(p):
            return p
    hits = glob.glob(os.path.join(TXT, kind, stem + "*.txt"))
    return hits[0] if hits else None


def pages_of(path):
    t = open(path, encoding="utf-8").read()
    parts = re.split(r"<<<PAGE (\d+)>>>", t)[1:]
    return [(int(parts[i]), parts[i + 1]) for i in range(0, len(parts), 2)]


def out(obj):
    print(json.dumps(obj, indent=1, ensure_ascii=False, default=str))


# ------------------------------------------------------------------ commands
def cmd_circular(a):
    C = kb("circulars")
    key = a.id.upper()
    if key in C:
        e = dict(C[key])
        e["notices_citing"] = sorted(
            n["notice"] for grp in kb("notices").values() for n in grp.values()
            if key in (n.get("circulars") or []))
        return out(e)
    hits = {k: v for k, v in C.items()
            if key in k.upper() or key in squash(str(v.get("description") or ""))}
    out({"query": a.id, "exact": False, "matches": len(hits),
         "results": [{"circular": k, "type": v["type"], "states": v["states"],
                      "description": v["description"]} for k, v in list(hits.items())[:a.max]]})


def cmd_notice(a):
    N = kb("notices")
    key = a.id.upper().replace(".PDF", "")
    for grp in N.values():
        for f, n in grp.items():
            if key in (n["notice"] or "").upper() or key in f.upper():
                r = dict(n)
                p = text_path(n["notice"])
                r["text_file"] = p
                r["text_pages"] = len(pages_of(p)) if p else 0
                r["pdf"] = os.path.join(PDF_ROOT,
                                        {"RU": "Rules", "TERXV": "Terrorism",
                                         "CGLES": "Schedule & Experience Rating",
                                         "CRP": "Composite Rating"}
                                        .get(n["kind"], "LossCosts"), f)
                return out(r)
    out({"error": "notice not found", "query": a.id})


def cmd_state(a):
    J = kb("jurisdictions")
    st = a.st.upper()
    if st not in J:
        return out({"error": "unknown jurisdiction", "known": sorted(J)})
    out(J[st])


def cmd_rule(a):
    """Find a rule's text in a jurisdiction's latest notice (or the CW base)."""
    J = kb("jurisdictions")
    st = (a.st or "MU").upper()
    if st == "MU":
        cands = sorted(glob.glob(os.path.join(TXT, "rules", "GL-MU-*.txt")))
        notice = os.path.basename(cands[-1])[:-4] if cands else None
    else:
        notice = J[st]["latest_rules_notice"]
    p = text_path(notice) if notice else None
    if not p:
        return out({"error": "no rules text for jurisdiction", "st": st, "notice": notice})
    pat = re.compile(r"RULE\s+" + re.escape(a.rule) + r"\s*\.", re.I)
    res = []
    for pno, txt in pages_of(p):
        for m in pat.finditer(txt):
            res.append({"page": pno,
                        "excerpt": " ".join(txt[m.start():m.start() + a.chars].split())})
    out({"notice": notice, "rule": a.rule, "st": st, "hits": len(res),
         "results": res[:a.max]})


def cmd_grep(a):
    needle = squash(a.pattern) if a.squash else a.pattern.upper()
    kinds = {"RU": ["rules"], "LC": ["losscosts"],
             "TERXV": ["terrorism"], "TER": ["terrorism"],
             "CGLES": ["scheduleexperience"], "SE": ["scheduleexperience"],
             "CRP": ["compositerating"], "CR": ["compositerating"],
             "PLANS": ["scheduleexperience", "compositerating"],
             }.get((a.kind or "").upper(),
                   ["rules", "losscosts", "terrorism",
                    "scheduleexperience", "compositerating"])
    res, scanned = [], 0
    for kind in kinds:
        files = sorted(glob.glob(os.path.join(TXT, kind, "*.txt")))
        if a.st:
            files = [f for f in files
                     if os.path.basename(f).split("-")[1] == a.st.upper()]
        for f in files:
            scanned += 1
            raw = open(f, encoding="utf-8").read()
            hay = squash(raw) if a.squash else raw.upper()
            if needle not in hay:
                continue
            for pno, txt in pages_of(f):
                h = squash(txt) if a.squash else txt.upper()
                if needle in h:
                    i = h.index(needle)
                    src = re.sub(r"\s+", " ", txt) if a.squash else txt
                    j = max(0, (i if a.squash else i) - a.before)
                    res.append({"notice": os.path.basename(f)[:-4],
                                "page": pno,
                                "excerpt": " ".join(src[j:j + a.chars].split())})
                    if len(res) >= a.max:
                        return out({"pattern": a.pattern, "files_scanned": scanned,
                                    "hits": len(res), "truncated": True, "results": res})
    out({"pattern": a.pattern, "files_scanned": scanned, "hits": len(res),
         "truncated": False, "results": res})


def cmd_page(a):
    p = text_path(a.notice)
    if not p:
        return out({"error": "no text for notice", "notice": a.notice})
    for pno, txt in pages_of(p):
        if pno == a.page:
            return out({"notice": a.notice, "page": pno, "text": txt})
    out({"error": "page not found", "notice": a.notice, "page": a.page})


def cmd_territory(a):
    J = kb("jurisdictions")
    st = a.st.upper()
    if st not in J:
        return out({"error": "unknown jurisdiction"})
    t = dict(J[st]["territory"])
    t["st"] = st
    t["rules_notice"] = J[st]["latest_rules_notice"]
    if a.zip:
        if t["scheme"] != "ZIP_TABLE":
            t["lookup"] = {"zip": a.zip, "resolved": None,
                           "reason": f"jurisdiction uses {t['scheme']}; "
                                     + ("entire state, territory " + (t["domain"][0] if t["domain"] else "?")
                                        if t["scheme"] == "ENTIRE_STATE"
                                        else "resolution needs county and place name, not a ZIP")}
        else:
            p = text_path(t["rules_notice"])
            found = None
            if p:
                pat = re.compile(r"(?<!\d)" + re.escape(a.zip) + r"\s+([A-Z][A-Z .'&/-]{1,28}?)\s+(\d{3})(?!\d)")
                for pno, txt in pages_of(p):
                    m = pat.search(txt)
                    if m:
                        found = {"zip": a.zip, "usps_name": m.group(1).strip(),
                                 "territory": m.group(2), "page": pno,
                                 "notice": t["rules_notice"]}
                        break
            t["lookup"] = found or {"zip": a.zip, "resolved": None,
                                    "reason": "not found in the ZIP table - REFER"}
    out(t)


def cmd_rate(a):
    """Locate a class code's published loss cost row in a jurisdiction's latest notice."""
    J = kb("jurisdictions")
    st = a.st.upper()
    notice = J[st]["latest_losscost_notice"]
    p = text_path(notice)
    if not p:
        return out({"error": "no loss cost text", "st": st})
    pat = re.compile(r"(?<![\d.])" + re.escape(a.klass)
                     + r"\s+(\(a\)|[–—-]|[\d,]*\.?\d+)\s+(\(a\)|[–—-]|[\d,]*\.?\d+)")
    rows, elp = [], []
    TERR = re.compile(r"PREM/OPS\s+TERR\.\s*(\d{3})", re.I)
    for pno, txt in pages_of(p):
        up = txt.upper()
        if "LOSS COST PAGES" in up:
            m = pat.search(txt)
            if m:
                tm = TERR.search(txt)
                rows.append({"page": pno, "territory": tm.group(1) if tm else None,
                             "prem_ops": m.group(1), "prod_compops": m.group(2)})
        elif "ESTIMATED LOSS POTENTIAL" in up:
            i = txt.find(a.klass)
            if i >= 0:
                elp.append({"page": pno,
                            "excerpt": " ".join(txt[i:i + 90].split())})

    def decode(v):
        return ("NOT_OFFERED (Rule 48.F.1 - reject this subline)" if v in ("–", "—", "-")
                else "REFER - consult the ELP" if v == "(a)" else "published loss cost (pre-LCM)")

    out({"st": st, "class_code": a.klass, "notice": notice,
         "vintage": J[st]["rates"]["vintage"],
         "loss_cost_rows": [dict(r, prem_ops_meaning=decode(r["prem_ops"]),
                                 prod_compops_meaning=decode(r["prod_compops"])) for r in rows],
         "elp_rows": elp[:a.max],
         "note": "Values are ISO loss costs before the company loss cost multiplier (Rule 23.B)."})


def cmd_invariant(a):
    I = kb("invariants")["invariants"]
    if a.id:
        for e in I:
            if e["id"].upper() == a.id.upper():
                return out(e)
        return out({"error": "unknown invariant", "known": [e["id"] for e in I]})
    if a.severity:
        I = [e for e in I if e["severity"] == a.severity.upper()]
    if a.q:
        q = a.q.upper()
        I = [e for e in I if q in json.dumps(e).upper()]
    out({"count": len(I), "invariants": I})


def cmd_dating(a):
    """Derive a notice's dating anchor from the PDF cover page alone - no ERC.

    Reads the printed 'Circular Reference(s): LI-GL-YYYY-NNN (MM/DD/YYYY)' block.
    Patterns are space-tolerant because pypdf renders 'LI -GL -2019 -216'.
    """
    CIRC = re.compile(r"LI\s*-\s*[A-Z]{2,3}\s*-\s*\d{4}\s*-\s*\d{3}")
    DATED = re.compile(CIRC.pattern + r"\s*\(\s*(\d{2}/\d{2}/\d{4})\s*\)")
    FILING = re.compile(r"GL\s*-\s*\d{4}\s*-\s*[A-Z0-9]{3,8}")
    FILING_LABEL = re.compile(r"Filing\s+Reference", re.I)

    def norm(s):
        return re.sub(r"\s*-\s*", "-", s.strip())

    targets = []
    if a.notice:
        p = text_path(a.notice)
        if not p:
            return out({"error": "no text for notice", "notice": a.notice})
        targets = [p]
    else:
        _k = (a.kind or "").upper()
        for kind in (["rules"] if _k == "RU"
                     else ["losscosts"] if _k == "LC"
                     else ["terrorism"] if _k in ("TER", "TERXV")
                     else ["scheduleexperience"] if _k in ("SE", "CGLES")
                     else ["compositerating"] if _k in ("CR", "CRP")
                     else ["scheduleexperience", "compositerating"] if _k == "PLANS"
                     else ["rules", "losscosts", "terrorism",
                           "scheduleexperience", "compositerating"]):
            fs = sorted(glob.glob(os.path.join(TXT, kind, "*.txt")))
            if a.st:
                fs = [f for f in fs if os.path.basename(f).split("-")[1] == a.st.upper()]
            targets += fs

    res = []
    for p in targets:
        pg = pages_of(p)
        head = "\n".join(t for _, t in pg[:3])
        dm, cm = DATED.search(head), CIRC.search(head)
        # the filing reference follows its own label; searching the whole head picks up
        # the filing-shaped substring inside the circular number (LI-GL-2019-216)
        lm = FILING_LABEL.search(head)
        fm = FILING.search(head, lm.end()) if lm else None
        res.append({
            "notice": os.path.basename(p)[:-4].replace("-C", ""),
            "circular": norm(cm.group(0)) if cm else None,
            "circular_issued": dm.group(1) if dm else None,
            "filing": norm(fm.group(0)) if fm else None,
            "anchor_quality": ("DATED_CIRCULAR" if dm else
                               "CIRCULAR_NO_DATE" if cm else "NONE"),
        })
    res.sort(key=lambda r: r["notice"])
    cov = Counter(r["anchor_quality"] for r in res)
    out({"source": "PDF cover page only - no ERC",
         "note": ("The printed date is the circular's ISSUE date, not the manual effective "
                  "date. Use it to ORDER notices and to bound the effective date from below; "
                  "do not present it as the effective date."),
         "coverage": dict(cov),
         "count": len(res),
         "notices": res if a.notice or len(res) <= a.max else res[:a.max]})


def cmd_effective(a):
    """Which notices were in force for a jurisdiction at a date."""
    N = kb("notices")
    st = a.st.upper()

    def key(d):
        if not d:
            return "0000-00-00"
        s = str(d)
        m = re.match(r"(\d{2})/(\d{2})/(\d{4})", s)
        return f"{m.group(3)}-{m.group(1)}-{m.group(2)}" if m else s[:10]

    want = a.date
    res = {}
    for grp, label in ((N["rules"], "rules"), (N["losscosts"], "losscosts")):
        cands = [n for n in grp.values() if n["st"] == st]
        dated = [(key(n.get("erc_edition_date") or n.get("effective_date")), n) for n in cands]
        elig = [x for x in dated if x[0] <= want and x[0] != "0000-00-00"]
        pick = max(elig, key=lambda x: (x[0], x[1]["notice"]))[1] if elig else None
        res[label] = {
            "in_force": pick["notice"] if pick else None,
            "edition_date": (pick.get("erc_edition_date") or pick.get("effective_date")) if pick else None,
            "date_confidence": pick.get("date_confidence") if pick else None,
            "cw_parent": pick.get("cw_parent") if pick else None,
            "candidates_held": len(cands),
        }
    res["st"] = st
    res["as_of"] = want
    res["warning"] = ("Both a rules notice AND a loss cost notice are required to rate; "
                      "they have independent effective dates (INV-THREE-STREAMS).")
    out(res)


def main():
    ap = argparse.ArgumentParser(prog="iso.py", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("circular"); p.add_argument("id"); p.add_argument("--max", type=int, default=20); p.set_defaults(fn=cmd_circular)
    p = sub.add_parser("notice");   p.add_argument("id"); p.set_defaults(fn=cmd_notice)
    p = sub.add_parser("state");    p.add_argument("st"); p.set_defaults(fn=cmd_state)
    p = sub.add_parser("rule")
    p.add_argument("rule"); p.add_argument("--st"); p.add_argument("--max", type=int, default=5)
    p.add_argument("--chars", type=int, default=1200); p.set_defaults(fn=cmd_rule)
    p = sub.add_parser("grep")
    p.add_argument("pattern"); p.add_argument("--kind"); p.add_argument("--st")
    p.add_argument("--max", type=int, default=10); p.add_argument("--chars", type=int, default=400)
    p.add_argument("--before", type=int, default=120)
    p.add_argument("--squash", action="store_true",
                   help="whitespace-insensitive match (needed on pypdf text)")
    p.set_defaults(fn=cmd_grep)
    p = sub.add_parser("page"); p.add_argument("notice"); p.add_argument("page", type=int); p.set_defaults(fn=cmd_page)
    p = sub.add_parser("territory"); p.add_argument("st"); p.add_argument("--zip"); p.set_defaults(fn=cmd_territory)
    p = sub.add_parser("rate"); p.add_argument("st"); p.add_argument("--class", dest="klass", required=True)
    p.add_argument("--max", type=int, default=5); p.set_defaults(fn=cmd_rate)
    p = sub.add_parser("invariant"); p.add_argument("--id"); p.add_argument("--severity"); p.add_argument("--q")
    p.set_defaults(fn=cmd_invariant)
    p = sub.add_parser("dating")
    p.add_argument("--notice"); p.add_argument("--st"); p.add_argument("--kind")
    p.add_argument("--max", type=int, default=40); p.set_defaults(fn=cmd_dating)
    p = sub.add_parser("effective"); p.add_argument("st"); p.add_argument("--date", required=True)
    p.set_defaults(fn=cmd_effective)

    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
