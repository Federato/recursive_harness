#!/usr/bin/env python3
"""The test console's landing screen, Upload & Compare: requests the user already has, rated free and set beside
ISO's stored answer for exactly that request; the rest sent one call each after a confirmation. No ISO calls.

  A  reading a request: line, state and effective date from ProductName; what a wrong upload is told
  B  rating: every GL and Property sample, uploaded as its file's text, rates as the engine does; the stored answer
     is found from the text as uploaded (a browser's JSON round trip would turn 1.0 into 1 and miss it)
  C  sending: a request ISO already answered is reused, no call; otherwise the route hands the request as uploaded to
     the Workbench's send (ad hoc lane, the reason past the cap)
  D  the page: the first tab and where /console opens; app-only in the read-only snapshot; the JS parses
  E  generating: a working request for a line and state (the Workbench's base request), rated like an upload

    python tests/verify_console_upload.py
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT, ROOT / "scripts", ROOT / "scripts" / "cf"):
    sys.path.insert(0, str(p))
sys.stdout.reconfigure(encoding="utf-8")
TMP = Path(tempfile.mkdtemp(prefix="tc-upload-"))
os.environ["RAAS_LEDGER_DIR"] = str(TMP / "ledger")
os.environ["TC_DISPATCH"] = "0"

import property_rating as pr  # noqa: E402
from console import workbench as WB  # noqa: E402
from gl_engine.rating import Kernel  # noqa: E402
from ui import console_page as CP  # noqa: E402

RESULTS = []
SAMPLES = ROOT / "Engine_Payloads"


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok)))
    print(f"  {'ok  ' if ok else 'FAIL'} {name}" + (f"  -- {detail}" if detail and not ok else ""))


def post(op, body):
    code, out, _ = CP.dispatch("POST", f"/api/console/workbench/{op}", {}, body)
    return code, json.loads(out)


def part_a():
    print("A. reading a request")
    gl = json.loads((SAMPLES / "OH" / "submission.json").read_text(encoding="utf-8"))
    check("A1 GL: line, state and effective date from SchemeKeys",
          WB.identify(gl) == {"line": "GL", "state": "OH", "effective": "2026-08-01"}, WB.identify(gl))
    cp = WB.identify(pr.sample("FL"))
    check("A2 Property: line and state", cp["line"] == "CP" and cp["state"] == "FL", cp)
    wrong = {"empty": {}, "not JSON": "{oops", "no state": {"body": {"SchemeKeys": {"ProductName": "General Liability"}}},
             "another product": {"body": {"SchemeKeys": {"ProductName": "Commercial Auto OH"}}},
             "no GL block": {"body": {"SchemeKeys": {"ProductName": "General Liability OH"}}}}
    said = {k: post("upload", {"text": v if isinstance(v, str) else json.dumps(v)}) for k, v in wrong.items()}
    check("A3 a wrong upload is refused with a 400 and says why, without the exception's type",
          all(c == 400 and r.get("error") and not r["error"].startswith("ValueError") for c, r in said.values()),
          {k: r for k, (_, r) in said.items()})
    check("A4 the message names the problem",
          "ProductName" in said["empty"][1]["error"] and "names no state" in said["no state"][1]["error"]
          and "Commercial Auto OH" in said["another product"][1]["error"]
          and "body.GeneralLiability" in said["no GL block"][1]["error"], said)
    code, r = post("upload", {"text": json.dumps([gl, pr.sample("FL")]), "index": 1})
    check("A5 a file holding a list: each item by its index", code == 200 and r["line"] == "CP" and r["state"] == "FL", r)


def part_b():
    print("B. rating")
    k, bad, n, stored = Kernel(mode="strict-erc"), [], 0, 0
    for d in sorted(SAMPLES.iterdir()):
        f = d / "submission.json"
        if not f.exists():
            continue
        n += 1
        _, r = post("upload", {"text": f.read_text(encoding="utf-8")})
        stored += bool(r.get("stored"))
        try:
            ref = str(k.rate(str(f)).premium)
        except Exception:                                    # noqa: BLE001
            ref = "refused"
        got = r.get("premium") if r.get("outcome") == "rated" else "refused"
        if (r.get("line"), r.get("state"), got) != ("GL", d.name, ref):
            bad.append((d.name, got, ref))
    check(f"B1 every GL sample ({n}) rates as the engine does", not bad, bad[:5])
    check("B2 the stored ISO answer is found from the uploaded text (most GL samples have one)", stored >= n - 5,
          f"{stored} of {n}")
    bad, n = [], 0
    for st in pr.states():
        n += 1
        req = pr.sample(st)
        _, r = post("upload", {"text": json.dumps(req, indent=1)})
        ref = pr.rate(req)
        ref = str(ref["premium"]) if ref["complete"] else "refused"
        got = str(r.get("premium")) if r.get("outcome") == "rated" else "refused"
        if (r.get("line"), r.get("state"), got) != ("CP", st, ref):
            bad.append((st, got, ref))
    check(f"B3 every Property sample ({n}) rates as property_rating does", not bad, bad[:5])
    text = (SAMPLES / "OH" / "submission.json").read_text(encoding="utf-8")
    via_text = post("upload", {"text": text})[1]
    check("B4 OH GL: ISO's stored answer, and ours agrees with it",
          via_text.get("stored") and float(via_text["stored"]["iso"]) == float(via_text["premium"]), via_text)


def part_c():
    print("C. sending")
    from console import ledger
    before = len(ledger.entries())
    text = (SAMPLES / "OH" / "submission.json").read_text(encoding="utf-8")
    code, r = post("upload-send", {"text": text, "reuse": True})
    check("C1 a request ISO already answered is reused: nothing sent", code == 200 and r.get("reused") and not r.get("sent"), r)
    check("C2 and no call is recorded in the ledger", len(ledger.entries()) == before, len(ledger.entries()))
    seen = {}
    real = WB.send
    WB.send = lambda line, payload, reuse=True, override=None, client=None: (
        seen.update(line=line, payload=payload, reuse=reuse, override=override) or {"sent": True, "reused": False, "stored": None})
    try:
        req = pr.sample("FL")
        code, r = post("upload-send", {"text": json.dumps([{}, req]), "index": 1, "reuse": True, "override": "triage"})
    finally:
        WB.send = real
    check("C3 otherwise the request as uploaded goes to the Workbench's send, with the reason past the cap",
          code == 200 and r.get("sent") and seen.get("line") == "CP" and seen.get("payload") == req
          and seen.get("reuse") is True and seen.get("override") == "triage", seen)


def part_e():
    print("E. generating a request")
    get = lambda q: json.loads(CP.dispatch("GET", "/api/console/workbench/generate", q, None)[1])   # noqa: E731
    bad, stored = [], 0
    for lob, states in (("GL", ["AK", "NY", "OH", "TX", "WY"]), ("CP", ["AZ", "FL", "OH", "TX"])):
        for st in states:
            g = get({"lob": lob, "state": st})
            _, r = post("upload", {"text": g["text"]})
            stored += bool(r.get("stored"))
            if (g["line"], g["state"], r.get("line"), r.get("state"), r.get("outcome")) != (lob, st, lob, st, "rated"):
                bad.append((lob, st, g.get("line"), r.get("outcome"), r.get("detail") or r.get("error")))
    check("E1 a generated request reads back as its line and state and rates (GL and Property)", not bad, bad)
    check("E2 generated GL is the Workbench's base request, so ISO's stored answers match it", stored >= 4, stored)
    g = get({"lob": "GL", "state": "OH"})
    check("E3 it is sent as text, as an uploaded file is (1.0 stays 1.0)", isinstance(g["text"], str)
          and json.loads(g["text"]) == WB.build("GL", "OH"))


def part_d():
    print("D. the page")
    check("D1 Upload & Compare is the first tab", CP.SCREENS[0][:2] == ("compare", "Upload & Compare"))
    html = CP.page()
    check("D2 /console opens on it", "(location.hash||'#compare')" in html and "?k:'compare'" in html)
    check("D3 its controls are on the page", all(f'id="{i}"' in html for i in
                                                 ("up-drop", "up-file", "up-text", "up-send", "up-out", "up-side")))
    check("D6 the generator and the row actions are on the page",
          all(s in html for s in ('id="up-lob"', 'id="up-state"', 'id="up-gen"', "data-dl=", "data-ed=")))
    snap = CP.page(app_only=frozenset({"compare", "plan", "workbench"}))
    sec = re.search(r'<section class="screen" id="s-compare".*?</section>', snap, re.S).group(0)
    check("D4 in the read-only snapshot it says it needs the running app", "needs the running app" in sec and "up-drop" not in sec)
    js = TMP / "page.js"
    js.write_text("\n".join(re.findall(r"<script>(.*?)</script>", html, re.S)), encoding="utf-8")
    node = shutil.which("node")
    if node:
        r = subprocess.run([node, "--check", str(js)], capture_output=True, text=True)
        check("D5 the page's JS parses", r.returncode == 0, r.stderr[:300])
    else:
        check("D5 the page's JS parses (node not found: skipped)", True)


if __name__ == "__main__":
    try:
        part_a(); part_b(); part_c(); part_d(); part_e()
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
    n = sum(ok for _, ok in RESULTS)
    print(f"\n{n}/{len(RESULTS)} passed")
    sys.exit(0 if n == len(RESULTS) else 1)
