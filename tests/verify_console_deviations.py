#!/usr/bin/env python3
"""P4 of DEVIATIONS-PLAN.md: carrier deviations in the console. No ISO calls.

  A  the writing-company picker lists every company with a compiled filing, and which filings are in force
  B  Upload & Compare with a company: Technical / ISO / Carrier -- `premium` is technical's (the figure set beside
     ISO), the carrier is ours only, and the deviations panel carries the filing, the waterfall and the warnings
  C  asking ISO about a company request sends the NON-DEVIATED payload: no company, no PolicyType, no LCM (D21)
  D  the page: the picker, the Technical / ISO / Carrier columns, the Deviations Proof tab; the JS parses
  E  the Deviations Proof board: T1-T10 as rows from each suite's last run; T3 and T8 list ISO's cases
  F  the rating worksheet: every field, Technical | ISO | Deviated, free, with the rule that wrote each value
  G  why this value: a worksheet value's ancestry from the rating graph, its sources, the carrier's path marked
  H  Carrier Filings: the filings log, each filing's sources re-hashed and openable, each company's versions
  I  the worksheet's Formula view: each premium as arithmetic with its actual factors, checked against the engine
  J  B-20's demo view: the filings board (company x line and state, pins), each filing's rows, its impact previews
     (built and draft), its filing sheet rendered, and its proving suite's last run

    python tests/verify_console_deviations.py
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT, ROOT / "scripts", ROOT / "scripts" / "cf", ROOT / "tests"):
    sys.path.insert(0, str(p))
sys.stdout.reconfigure(encoding="utf-8")
TMP = Path(tempfile.mkdtemp(prefix="tc-deviations-"))
os.environ["RAAS_LEDGER_DIR"] = str(TMP / "ledger")
os.environ["TC_DISPATCH"] = "0"
os.environ["CARRIERS_ROOT"] = str(TMP / "carriers")          # before `deviations.config` is imported

shutil.copytree(ROOT / "tests" / "fixtures" / "deviations" / "UFG", TMP / "carriers" / "UFG")

import property_rating as pr  # noqa: E402
from console import workbench as WB  # noqa: E402
from ui import console_page as CP  # noqa: E402

RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok)))
    print(f"  {'ok  ' if ok else 'FAIL'} {name}" + (f"  -- {detail}" if detail and not ok else ""))


def post(op, body):
    code, out, _ = CP.dispatch("POST", f"/api/console/workbench/{op}", {}, body)
    return code, json.loads(out)


def get(path):
    code, out, _ = CP.dispatch("GET", path, {}, None)
    return code, json.loads(out)


def setup():
    from deviations.compile import compile_filing
    from deviations.files import load_filing, log_action
    from deviations.validate import validate
    for co in ("UFC", "ADD"):
        f = load_filing(TMP / "carriers" / "UFG" / co / "authored" / "IA-CF-UNFG-134289779.v1.json")
        log_action(f.company_dir, f.filing, f.version, "propose", "Dan Roman")
        if co == "UFC":
            log_action(f.company_dir, f.filing, f.version, "sign-off", "Dan Roman")
            compile_filing(validate(f))
        else:                       # compiled, then withdrawn: listed, not in force
            log_action(f.company_dir, f.filing, f.version, "sign-off", "Dan Roman")
            compile_filing(validate(f))
            log_action(f.company_dir, f.filing, f.version, "withdraw", "Dan Roman")


def part_a():
    print("A. the writing-company picker")
    code, j = get("/api/console/workbench/companies")
    by = {c["code"]: c for c in j["companies"]}
    check("A1 both UFG companies are listed, with names and their carrier",
          code == 200 and set(by) == {"UFC", "ADD"} and by["UFC"]["carrier"] == "UFG"
          and by["UFC"]["name"].startswith("United Fire"), by)
    check("A2 a filing in force is marked approved; one withdrawn after it compiled is not",
          by["UFC"]["filings"][0]["approved"] and not by["ADD"]["filings"][0]["approved"],
          [by[c]["filings"] for c in by])


def part_b():
    print("B. Upload & Compare with a writing company")
    text = json.dumps(pr.sample("IA", "2025-07-01"))
    _, plain = post("upload", {"text": text})
    code, r = post("upload", {"text": text, "company": "UFC", "policyType": "New"})
    check("B1 rated", code == 200 and r["outcome"] == "rated" and r["carrier"]["outcome"] == "rated", r)
    check("B2 `premium` is TECHNICAL's: it equals the same request rated with no company",
          r["premium"] == plain["premium"], (r["premium"], plain["premium"]))
    check("B3 the carrier is above technical (UFG's Iowa LCMs, class 0951)",
          Decimal(r["carrier"]["premium"]) > Decimal(r["premium"]), r["carrier"])
    d = r["deviation"]
    check("B4 the panel carries the filing, both premiums and a waterfall that adds up",
          d["filings"] and d["filings"][0]["id"] == "IA-CF-UNFG-134289779"
          and sum(Decimal(s["effect"]) for s in d["waterfall"])
          == Decimal(d["carrierPremium"]) - Decimal(d["technicalPremium"]), d)
    from deviations.engine import iso_request
    dev_req = pr.sample("IA", "2025-07-01")
    dev_req["header"].update(WritingCompany="UFC", PolicyType="New")
    check("B5 the hash is the non-deviated payload's: what ISO's stored answer is looked up by",
          r["hash"] == WB.store.request_hash(iso_request(dev_req, "CF")[0]), r["hash"])
    code, r2 = post("upload", {"text": text, "company": "ADD"})
    check("B6 a company whose filing was withdrawn rates as technical, and says so",
          r2["carrier"]["premium"] == r2["premium"]
          and any("no approved" in w for w in r2["deviation"]["warnings"]), r2["deviation"])
    code, r3 = post("upload", {"text": text, "company": "NOPE"})
    check("B7 an unknown company is refused with the reason, not rated as technical",
          r3["carrier"]["outcome"] == "refused" and "NOPE" in (r3["deviation"].get("refused") or ""), r3)


def part_c():
    print("C. asking ISO about a company request")
    sent = []
    real = WB.send

    def fake(line, payload, reuse=True, override=None, client=None):
        sent.append(payload)
        return {"sent": True, "reused": False, "stored": None}
    WB.send = fake
    try:
        req = pr.sample("IA", "2025-07-01")
        code, j = post("upload-send", {"text": json.dumps(req), "company": "UFC", "reuse": True})
    finally:
        WB.send = real
    body = json.dumps(sent[0]) if sent else ""
    check("C1 one request handed to the send", code == 200 and len(sent) == 1, j)
    check("C2 it names no company and no PolicyType", sent and not any(
        k in (sent[0].get("header") or {}) for k in ("WritingCompany", "PolicyType")), sent[0].get("header") if sent else None)
    check("C3 it carries no LCM (D21: ISO is never sent one)", "LossCostMultiplier" not in body)
    check("C4 the rest of the request is as uploaded", sent and sent[0]["body"]["SchemeKeys"] == req["body"]["SchemeKeys"])


def part_d():
    print("D. the page")
    code, html, kind = CP.dispatch("GET", "/console", {}, None)
    check("D1 ten tabs, Deviations Proof then Carrier Filings last", html.count('class="tab"') == 10
          and [k for k, _, _ in CP.SCREENS][-2:] == ["proof", "filings"])
    check("D2 the writing-company picker and New / Renewal", 'id="up-company"' in html and 'id="up-pt"' in html)
    check("D3 the table reads Technical, ISO, Carrier, and the ISO test",
          all(s in html for s in ("<th class=\"v\">Technical</th>", "<th class=\"v\">ISO</th>",
                                  "<th class=\"v\">Carrier</th>", "<th>ISO test</th>")))
    check("D4 the read-only snapshot marks the proof board as needing the app",
          "proof" in re.search(r'app_only=frozenset\(\{([^}]*)\}', Path(CP.__file__).read_text(encoding="utf-8")).group(1))
    js = "\n".join(re.findall(r"<script>(.*?)</script>", html, re.S))
    f = TMP / "page.js"
    f.write_text(js, encoding="utf-8")
    try:
        r = subprocess.run(["node", "--check", str(f)], capture_output=True, text=True, timeout=60)
        check("D5 the page's JavaScript parses", r.returncode == 0, r.stderr[:300])
    except FileNotFoundError:
        check("D5 the page's JavaScript parses (node not installed: skipped)", True)


def part_e():
    print("E. the Deviations Proof board")
    from deviations import suite_log
    keep = suite_log.DIR
    suite_log.DIR = TMP / "suites"
    try:
        suite_log.record("engine", [("A1 no company", True), ("C1 identity", True), ("D1 gl identity", False),
                                    ("E1 P0", True)])
        suite_log.record("files", [("A1 ufc", True), ("B1 import", True)])
        code, j = get("/api/console/deviations/proof")
    finally:
        suite_log.DIR = keep
    t = {r["test"]: r for r in j["tests"]}
    check("E1 ten rows, T1 to T10", code == 200 and [r["test"] for r in j["tests"]] == [f"T{i}" for i in range(1, 11)])
    check("E2 a row passes when every check of its own passes (T1 = the engine suite's A checks)",
          t["T1"]["status"] == "pass" and t["T1"]["total"] == 1, t["T1"])
    check("E3 ...and fails when one fails (T2 = its C and D checks)", t["T2"]["status"] == "fail" and t["T2"]["total"] == 2)
    check("E4 a suite that has not run leaves its rows 'not run'", t["T4"]["status"] == "not run")
    check("E5 T10 is the whole files suite", t["T10"]["status"] == "pass" and t["T10"]["total"] == 2)
    check("E6 T3 lists the cases ISO answered", all(c["line"] in ("CP", "GL") for c in t["T3"]["cases"]))


def part_f():
    print("F. the rating worksheet: Technical | ISO | Deviated")
    text = json.dumps(pr.sample("IA", "2025-07-01"))
    code, w = post("worksheet", {"text": text, "company": "UFC", "policyType": "New"})
    rows = w.get("rows", [])
    check("F1 built, with all three premiums' columns", code == 200 and w["premium"]["technical"]
          and w["premium"]["deviated"] and rows, {k: w.get(k) for k in ("premium", "iso", "error")})
    check("F2 every row says where it sits: record, field, technical, ISO, deviated, the rule that wrote it",
          all({"record", "field", "technical", "iso", "deviated", "rule", "tables"} <= set(r) for r in rows))
    ch = [r for r in rows if r["changed"] and not r.get("applied")]
    check("F3 the deviated changes are the fields the filing moved (67 on this risk, as the panel says)",
          len(ch) == 67 and any(r["field"] == "LossCostMultiplier" and r["deviated"] == "1.511" for r in ch),
          len(ch))
    check("F4 the premiums on the worksheet are the ones the row shows",
          w["premium"]["technical"] == "4334" and w["premium"]["deviated"] == "9026", w["premium"])
    check("F5 opening a worksheet never calls ISO: the ISO column is a stored answer or 'not asked'",
          w["iso"] in ("rated", "refused", "not asked"))
    check("F6 an ISO-only field with no value is not listed as a difference",
          not any(r.get("isoOnly") and r["iso"] in (None, "") for r in rows))
    code, w2 = post("worksheet", {"text": text})
    check("F7 with no company: Technical and ISO only, no deviated column",
          code == 200 and w2["company"] is None and w2["premium"]["deviated"] is None
          and not any(r["changed"] for r in w2["rows"]))
    secs = {sc["label"]: sc for sc in w.get("sections", [])}
    by = {r["path"]: r for r in rows}
    g1 = secs.get("Location › Building · Basic Group I")
    check("F9 by calculation: one section per coverage group of each rated item, every row in exactly one",
          g1 and sum(len(sc["paths"]) for sc in w["sections"]) == len(rows)
          and len({p for sc in w["sections"] for p in sc["paths"]}) == len(rows), list(secs)[:6])
    chain = [by[p]["field"] for p in (g1 or {}).get("paths", [])]
    want = ["BasicGroupIBaseRate", "BasicGroupIRate", "AdjustedBasicGroupIRate", "FinalBasicGroupIRate"]
    check("F10 a group's factors run in the order the engine computed them: base rate, rate, adjusted, final",
          all(f in chain for f in want) and [chain.index(f) for f in want] == sorted(chain.index(f) for f in want),
          chain[:12])
    check("F11 Basic Group II, Broad, Special and Earthquake each have their own section for the building",
          all(f"Location › Building · {g}" in secs for g in ("Basic Group II", "Broad", "Special", "Earthquake")))
    check("F12 a field under a coverage record says which: 'BuildingBasicGroupICoverage › Premium'",
          any(by[p]["label"] == "BuildingBasicGroupICoverage › Premium" for p in g1["paths"]) if g1 else False)
    g2 = secs.get("Location › Building · Basic Group II")
    g2rows = [by[p] for p in (g2 or {}).get("paths", [])]
    ap = [r for r in g2rows if r.get("applied")]
    check("F14 each group shows the LCM its rate was multiplied by: Building · Basic Group II applies 3.28 "
          "(the record field holds Group I's 1.511)",
          len(ap) == 1 and ap[0]["deviated"] == "3.28" and ap[0]["label"] == "LCM applied", [r["deviated"] for r in ap])
    fl = [r["field"] for r in g2rows]
    check("F15 ...placed in the chain: after the base rate, before the rate it multiplies",
          ap and fl.index("BasicGroupIIBaseRate") < fl.index(ap[0]["field"]) < fl.index("BasicGroupIIRate"), fl[:10])
    rec = [r for r in rows if r["field"] == "LossCostMultiplier" and r.get("note")]
    check("F16 the record's LossCostMultiplier says it is the Group I value", rec and "Group I" in rec[0]["note"])
    from console import catalog
    code, wg = post("worksheet", {"text": json.dumps(catalog.build("GL", "TX", {}))})
    labels = [sc["label"] for sc in wg.get("sections", [])]
    check("F13 GL groups by subline: Premises/Operations and Products/Completed Operations for the classification",
          "Location › Classification · Premises/Operations" in labels
          and "Location › Classification · Products/Completed Operations" in labels, labels[:8])
    code, html, _ = CP.dispatch("GET", "/console", {}, None)
    check("F8 each row has a Worksheet link, and the worksheet has its filters and a CSV download",
          "data-ws=" in html and "data-wcsv" in html and "Deviated changes" in html and "By calculation" in html)


def part_g():
    print("G. why this value: the worksheet's rating graph (G2)")
    text = json.dumps(pr.sample("IA", "2025-07-01"))
    code, w = post("worksheet", {"text": text, "company": "UFC", "policyType": "New"})
    tok = w.get("graph")
    row = next(r for r in w["rows"] if r["path"].endswith("CommercialPropertyStructure/FinalBasicGroupIIRate"))
    check("G1 a worksheet carries a graph token, and its values carry node ids on both sides",
          tok and row.get("tg") is not None and row.get("dg") is not None, {k: row.get(k) for k in ("tg", "dg")})
    code, y = post("why", {"token": tok, "side": "deviated", "gid": row["dg"], "depth": 3})
    n = y["node"]
    check("G2 the deviated final Group II rate's inputs are its chain: adjusted rate, deductible factor",
          {"AdjustedBasicGroupIIRate", "DeductibleFactorBasicGroupII"} <= {c["name"] for c in n.get("from", [])},
          [c["name"] for c in n.get("from", [])])
    check("G3 three levels by default, with a count of inputs below that",
          all("from" in c for c in n["from"]) and any(
              cc.get("inputs") and "from" not in cc for c in n["from"] for g in c.get("from", [])
              for cc in g.get("from", [])))
    src = y["sources"]
    check("G4 everything it came from: the filing's Group II LCM (3.28) and ISO's own table rows",
          any(x["kind"] == "company" and x["value"] == "3.28" for x in src)
          and any(x["kind"] == "table" and x["name"].startswith("BasicGroupIIRate[") for x in src),
          [(x["kind"], x["name"]) for x in src][:5])
    check("G5 the carrier's path is marked: the final rate is reached by the filing", n["affected"] is True)
    code, t = post("why", {"token": tok, "side": "technical", "gid": row["tg"], "depth": 3})
    check("G6 technical's ancestry of the same value has no filing source and nothing marked",
          not any(x["kind"] == "company" for x in t["sources"]) and t["node"]["affected"] is False)
    code, e = post("why", {"token": "nope", "side": "deviated", "gid": 0})
    check("G7 an expired worksheet says to open it again", "open it again" in e.get("error", ""))
    code, html, _ = CP.dispatch("GET", "/console", {}, None)
    check("G8 the page makes worksheet values clickable and draws the panel", "ws-why" in html and "wyHtml" in html)


def part_h():
    print("H. Carrier Filings: the filings log, its archived sources (re-hashed) and where each company's versions stand")
    import hashlib
    src = TMP / "carriers" / "UFG" / "sources" / "UNFG-134289779"
    src.mkdir(parents=True)
    csv = (ROOT / "tests" / "fixtures" / "deviations" / "UFG_IA_CP_LCMs.csv").read_bytes()
    (src / "UFG_IA_CP_LCMs.csv").write_bytes(csv)
    (src / "memo.pdf").write_bytes(b"%PDF-1.4 edited after it arrived")
    (src / "source.json").write_text(json.dumps({
        "serff": "UNFG-134289779", "carrier": "UFG", "companies": ["UFC", "ADD"], "line": "CF", "juris": ["IA"],
        "received": "2026-10-08", "files": [
            {"name": "UFG_IA_CP_LCMs.csv", "what": "the LCM table", "sha256": hashlib.sha256(csv).hexdigest()},
            {"name": "memo.pdf", "what": "the memo", "sha256": "0" * 64},
            {"name": "gone.pdf", "what": "never copied", "sha256": "1" * 64}]}), encoding="utf-8")
    new = TMP / "carriers" / "UFG" / "sources" / "UNFG-999"
    new.mkdir(parents=True)
    (new / "source.json").write_text(json.dumps({"serff": "UNFG-999", "carrier": "UFG", "companies": ["UFC"],
                                                 "line": "GL", "juris": ["IA"], "files": []}), encoding="utf-8")
    code, d = get("/api/console/filings")
    f = next((x for x in d["filings"] if x["id"] == "DEV-001"), None)
    check("H1 the log's DEV-001 is listed, with its carrier, line, state and SERFF",
          code == 200 and f and (f["carrier"], f["line"], f["state"], f["serff"]) == ("UFG", "CF", "IA", "UNFG-134289779"),
          f and {k: f[k] for k in ("carrier", "line", "state", "serff")})
    by = {x["name"]: x for x in f["sources"]}
    check("H2 each source is re-hashed: the CSV unchanged, the edited memo changed, the uncopied file missing",
          by["UFG_IA_CP_LCMs.csv"]["intact"] and by["memo.pdf"]["present"] and not by["memo.pdf"]["intact"]
          and not by["gone.pdf"]["present"], {k: (v["present"], v["intact"]) for k, v in by.items()})
    st = {v["company"]: v["status"] for v in f["versions"]}
    check("H3 each writing company's authored version, read from its workflow log (UFC approved, ADD withdrawn)",
          st == {"UFC": "approved", "ADD": "withdrawn"} and all(v["rows"] == 13 for v in f["versions"]), st)
    code, body, kind = CP.dispatch("GET", "/api/console/filings/source",
                                   {"carrier": "UFG", "serff": "UNFG-134289779", "file": "UFG_IA_CP_LCMs.csv"}, None)
    bad = [CP.dispatch("GET", "/api/console/filings/source", q, None)[0] for q in (
        {"carrier": "UFG", "serff": "..", "file": "UFC/workflow.jsonl"},
        {"carrier": "UFG", "serff": "UNFG-134289779", "file": "source.json"},
        {"carrier": "UFG", "serff": "UNFG-134289779", "file": "gone.pdf"})]
    check("H4 a source opens exactly as received; nothing outside the archive, and not source.json",
          code == 200 and kind == "csv" and body == csv and bad == [404, 404, 404], (code, kind, bad))
    u = next((x for x in d["filings"] if x["serff"] == "UNFG-999"), None)
    check("H5 a filing archived but not yet logged still shows, as received and not logged",
          u and u["id"] == "" and u["status"] == "Received, not logged", u and u["status"])
    e = f["entry"]
    check("H6 the log entry is rendered: its tables, its source hashes, no raw markdown",
          "<table" in e and "c3fd5ef14ab5" in e and "Decisions made on this filing" in e
          and "|" not in re.sub(r"<[^>]+>", "", e) and "**" not in e)
    code, html, _ = CP.dispatch("GET", "/console", {}, None)
    check("H7 the page has the Carrier Filings tab and draws it", 'id="s-filings"' in html and "flLoad" in html)


def part_i():
    print("I. the worksheet's Formula view: each premium as arithmetic with its factors, checked against the engine")
    from decimal import Decimal
    text = json.dumps(pr.sample("IA", "2025-07-01"))
    code, w = post("worksheet", {"text": text, "company": "UFC", "policyType": "New"})
    code, d = post("formula", {"token": w["graph"], "side": "deviated"})
    root = d.get("root") or {}
    check("I1 the formula tree starts at the policy's total premium, the worksheet's deviated premium",
          code == 200 and root.get("name") == "Policy total premium" and Decimal(root["value"]) ==
          Decimal(w["premium"]["deviated"]), {k: root.get(k) for k in ("name", "value")})
    flat = []

    def walk(f):
        if f.get("op") and not f.get("seeAbove"):
            flat.append(f)
            for t in f.get("terms", []):
                walk(t)
    walk(root)
    sc = {"": 1, "÷ 100": Decimal("0.01"), "÷ 1,000": Decimal("0.001"), "× 100": 100}
    bad = []
    for f in flat:
        if not f["checks"] or f.get("step") or f["op"] == "Mixed" or (f.get("note") and f.get("exact") == "0"):
            continue
        vals = [Decimal(t["value"]) for t in f["terms"]]
        got = sum(vals, Decimal(0)) if f["op"] == "Sum" else __import__("math").prod(vals) * Decimal(str(sc[f.get("scale") or ""]))
        if abs(got - Decimal(f["value"])) > Decimal("0.5"):
            bad.append((f["name"], f["value"], str(got)))
    check("I2 every formula shown reproduces its value from the terms shown (re-done here, independently)",
          flat and not bad, str(bad[:3]))
    ok = sum(1 for f in flat if f["checks"])
    check("I3 nearly every step is reconstructed (the rest say 'computed from', never a guessed formula)",
          ok >= 0.9 * len(flat) and all(f.get("note") for f in flat if not f["checks"]), f"{ok} of {len(flat)}")

    def leaves(f):
        for t in f.get("terms", []):
            yield t
            yield from leaves(t)
    lcm = [t for t in leaves(root) if t.get("source") == "filing"]
    check("I4 the filing's LCMs appear as factors, marked as the carrier's, e.g. Group II 3.28",
          any(t["value"] == "3.28" for t in lcm) and all(t["affected"] for t in lcm), [(t["name"], t["value"]) for t in lcm][:4])
    code, t = post("formula", {"token": w["graph"], "side": "technical"})
    tl = list(leaves(t["root"]))
    check("I5 technical's formulas carry no filing factor", not any(x.get("source") == "filing" for x in tl))
    code, both = post("formula", {"token": w["graph"]})
    rb = both.get("root") or {}
    check("I6a the combined view: each line carries Technical and Deviated (and ISO where ISO answered)",
          Decimal(rb.get("tech")) == Decimal(w["premium"]["technical"]) and Decimal(rb.get("dev")) ==
          Decimal(w["premium"]["deviated"]) and (w["premium"]["iso"] is None or
                                                 Decimal(rb.get("iso")) == Decimal(w["premium"]["iso"])),
          {k: rb.get(k) for k in ("tech", "iso", "dev")})
    lb = [t for t in leaves(rb) if t.get("source") == "filing"]
    check("I6b a factor the filing changed shows both: technical's LCM beside the filed one (1 -> 3.28)",
          any(t["value"] == "3.28" and Decimal(t.get("tech") or 0) == 1 for t in lb),
          [(t["name"], t.get("tech"), t["value"]) for t in lb][:4])
    same = [t for t in leaves(rb) if t.get("source") == "table" and t.get("tech") is not None]
    check("I6c an ISO table factor the filing didn't touch has the same value on both sides",
          same and all(Decimal(t["tech"]) == Decimal(t["value"]) for t in same), len(same))
    code, w0 = post("worksheet", {"text": text})
    code, b0 = post("formula", {"token": w0["graph"]})
    check("I6d with no writing company: Technical only (and ISO where answered), no Deviated",
          b0["root"].get("tech") is not None and "dev" not in b0["root"] and b0.get("hasDeviated") is False)
    code, e = post("formula", {"token": "nope", "side": "deviated"})
    check("I6 an expired worksheet says to open it again", "open it again" in e.get("error", ""))
    code, html, _ = CP.dispatch("GET", "/console", {}, None)
    check("I7 the page has the Formula view", 'data-wv="' in html and "fxPanel" in html and "formula" in html)


def part_j():
    print("J. B-20 demo view: the board, each filing's rows, impact previews, filing sheet and proof")
    import hashlib
    from deviations import suite_log
    from deviations.compile import compile_filing
    from deviations.files import load_filing, log_action
    from deviations.validate import validate
    gl = load_filing(TMP / "carriers" / "UFG" / "UFC" / "authored" / "IA-GL-UNFG-134374972.v1.json")
    for action in ("propose", "sign-off"):
        log_action(gl.company_dir, gl.filing, gl.version, action, "Dan Roman")
    compile_filing(validate(gl))
    code, b = get("/api/console/filings/board")
    cell = {(c["company"], c["line"], c["state"]): c for c in b["cells"]}
    ufc_gl = cell.get(("UFC", "GL", "IA"))
    check("J1 the board: UFC rates CF and GL in Iowa, GL pinned to GL_IA_20240401_V01; ADD's CF filing is withdrawn",
          code == 200 and cell.get(("UFC", "CF", "IA"), {}).get("status") == "approved" and ufc_gl
          and ufc_gl["status"] == "approved" and ufc_gl["pin"] == "GL_IA_20240401_V01"
          and cell.get(("ADD", "CF", "IA"), {}).get("status") == "withdrawn"
          and {"line": "GL", "state": "IA"} in b["columns"], {k: (v["status"], v["pin"]) for k, v in cell.items()})
    src = TMP / "carriers" / "UFG" / "sources" / "UNFG-134374972"
    src.mkdir(parents=True, exist_ok=True)
    sheet = "\n".join(["# Filing sheet: UFG Iowa GL", "", "| Company | LCM |", "|---|---|", "| UFC | **0.942** |", ""])
    (src / "sheet.md").write_text(sheet, encoding="utf-8")
    (src / "source.json").write_text(json.dumps({
        "serff": "UNFG-134374972", "carrier": "UFG", "companies": ["UFC"], "line": "GL", "juris": ["IA"],
        "sheet": "sheet.md", "suite": "ufg_test", "files": [{"name": "sheet.md", "what": "our filing sheet",
                                                             "sha256": hashlib.sha256(sheet.encode()).hexdigest()}]}),
        encoding="utf-8")
    imp = TMP / "impact"
    imp.mkdir(exist_ok=True)
    os.environ["IMPACT_DIR"] = str(imp)
    base = {"company": "UFC", "line": "GL", "states": {"IA": {"date": "2025-07-15", "filing": "IA-GL-UNFG-134374972.v1"}},
            "all": {"change": "28.7",
            "risks": 30, "rated": 30, "min": "-6.0", "max": "80.0"}, "by_risk_type": {"Retail": {"change": "-5.0"}},
            "by_coverage": {"All": {"Premises/Operations": {"change": "-5.8"}}}, "by_state": {}, "drivers": [],
            "refused": []}
    (imp / "UFC-GL-IA.json").write_text(json.dumps(base), encoding="utf-8")
    (imp / "UFC-GL-IA-draft-x.json").write_text(json.dumps({**base, "draft": "IA-GL-UNFG-134374972.v9"}), encoding="utf-8")
    (imp / "ADD-GL-IA.json").write_text(json.dumps({**base, "company": "ADD"}), encoding="utf-8")
    (imp / "UFC-CF-IA.json").write_text(json.dumps({**base, "line": "CF"}), encoding="utf-8")
    keep = suite_log.DIR
    suite_log.DIR = TMP / "suites"
    try:
        suite_log.record("ufg_test", [("U1 files", True), ("U2 lcm", True)])
        code, d = get("/api/console/filings")
    finally:
        suite_log.DIR = keep
    f = next((x for x in d["filings"] if x["serff"] == "UNFG-134374972"), None)
    v = f and next((x for x in f["versions"] if x["company"] == "UFC"), None)
    check("J2 each version carries its rows (target, scope, value), its compiled keys and its pin",
          v and len(v["detail"]) == 4 and v["detail"][0]["value"] == "0.942" and v["detail"][2]["scope"]
          == {"class_group": "UFG-IA-GL-aRated-PremOps@v1"} and v["compiledKeys"] > 0
          and v["pins"] == {"IA": "GL_IA_20240401_V01"}, v and {k: v[k] for k in ("compiledKeys", "pins")})
    got = sorted((i["company"], i["draft"] or "") for i in (f or {}).get("impacts", []))
    check("J3 the filing's impact previews: built and draft, for its own companies and line only",
          got == [("UFC", ""), ("UFC", "IA-GL-UNFG-134374972.v9")], got)
    check("J4 the filing sheet is rendered: its table, no raw markdown",
          f and "<table" in f["sheet"] and "<b>0.942</b>" in f["sheet"] and "|" not in re.sub(r"<[^>]+>", "", f["sheet"]))
    code, body, kind = CP.dispatch("GET", "/api/console/filings/source",
                                   {"carrier": "UFG", "serff": "UNFG-134374972", "file": "sheet.md"}, None)
    check("J5 a filing sheet opens as a page, rendered", code == 200 and kind == "html" and b"<table" in body, (code, kind))
    p = f and f["proof"]
    check("J6 the proving suite's last run: 2 of 2", p and p["ran"] and p["passed"] and (p["ok"], p["checks"]) == (2, 2), p)
    code, html, _ = CP.dispatch("GET", "/console", {}, None)
    check("J7 the page draws the board, the rows, the impact and the proof", all(
        k in html for k in ('id="fl-board"', "flBoard", "flRows", "flImpact", "flProof")))
    stages = {x["serff"]: x["stage"] for x in d["filings"]}
    check("J8 each filing's stage: DEV-003 proved (its suite passed), UNFG-999 only received",
          stages.get("UNFG-134374972") == "Proved" and stages.get("UNFG-999") == "Received", stages)
    from deviations.files import read_json, write_json
    v2 = read_json(gl.path) if hasattr(gl, "path") else read_json(
        TMP / "carriers" / "UFG" / "UFC" / "authored" / "IA-GL-UNFG-134374972.v1.json")
    v2.update(version=2, status="draft")
    write_json(TMP / "carriers" / "UFG" / "UFC" / "authored" / "IA-GL-UNFG-134374972.v2.json", v2)
    (imp / "UFC-GL-IA-draft-x.json").write_text(json.dumps({**base, "draft": "IA-GL-UNFG-134374972.v2",
        "vs_current": {"risks": 30, "change": "6.2", "by_risk_type": {"Retail": "6.2"}, "by_coverage": {},
                       "filings": {"IA": "IA-GL-UNFG-134374972.v1"}}}), encoding="utf-8")
    code, b = get("/api/console/filings/board")
    cell = {(c["company"], c["line"], c["state"]): c for c in b["cells"]}
    check("J9 drafts on the board: UFC's v2 tagged on the GL filing in force; ADD's unapproved GL v1 on its own cell",
          cell[("UFC", "GL", "IA")].get("drafts") == ["IA-GL-UNFG-134374972 v2"]
          and cell.get(("ADD", "GL", "IA"), {}).get("status") == "draft",
          {k: (v["status"], v.get("drafts")) for k, v in cell.items()})
    code, d = get("/api/console/filings")
    f = next(x for x in d["filings"] if x["serff"] == "UNFG-134374972")
    dv = next((i for i in f["impacts"] if i["draft"] == "IA-GL-UNFG-134374972.v2"), None)
    vers = sorted((v["company"], v["version"], v["status"]) for v in f["versions"])
    check("J10 the draft's impact carries its change from what is in force, and the draft is listed as a version",
          dv and dv["vsCurrent"]["change"] == "6.2" and ("UFC", 2, "draft") in vers, (dv and dv.get("vsCurrent"), vers))
    check("J11 the page shows stages, drafts and the in-force comparison",
          all(k in html for k in ("f.stage", "flDraftImpact", "vs in force")))


def main() -> int:
    setup()
    for part in (part_a, part_b, part_c, part_d, part_e, part_f, part_g, part_h, part_i, part_j):
        part()
    bad = [n for n, ok in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(bad)}/{len(RESULTS)} passed" + (f"; FAILED: {', '.join(bad)}" if bad else ""))
    shutil.rmtree(TMP, ignore_errors=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
