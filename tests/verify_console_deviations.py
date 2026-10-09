#!/usr/bin/env python3
"""P4 of DEVIATIONS-PLAN.md: carrier deviations in the console. No ISO calls.

  A  the writing-company picker lists every company with a compiled filing, and which filings are in force
  B  Upload & Compare with a company: Technical / ISO / Carrier -- `premium` is technical's (the figure set beside
     ISO), the carrier is ours only, and the deviations panel carries the filing, the waterfall and the warnings
  C  asking ISO about a company request sends the NON-DEVIATED payload: no company, no PolicyType, no LCM (D21)
  D  the page: the picker, the Technical / ISO / Carrier columns, the Deviations Proof tab; the JS parses
  E  the Deviations Proof board: T1-T10 as rows from each suite's last run; T3 and T8 list ISO's cases
  F  the rating worksheet: every field, Technical | ISO | Deviated, free, with the rule that wrote each value

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
    check("D1 nine tabs, Deviations Proof last", html.count('class="tab"') == 9
          and [k for k, _, _ in CP.SCREENS][-1] == "proof")
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
    ch = [r for r in rows if r["changed"]]
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
    code, html, _ = CP.dispatch("GET", "/console", {}, None)
    check("F8 each row has a Worksheet link, and the worksheet has its filters and a CSV download",
          "data-ws=" in html and "data-wcsv" in html and "Deviated changes" in html)


def main() -> int:
    setup()
    for part in (part_a, part_b, part_c, part_d, part_e, part_f):
        part()
    bad = [n for n, ok in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(bad)}/{len(RESULTS)} passed" + (f"; FAILED: {', '.join(bad)}" if bad else ""))
    shutil.rmtree(TMP, ignore_errors=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
