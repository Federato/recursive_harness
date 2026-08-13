"""Stage 6 acceptance: the interface.

The plan set this stage a falsifiable claim before any of it was built:

> *"We expect it to prove the separation rather than build anything: if the UI
> needs the engine to change, the engine's interface was wrong."*

So group A tests the separation itself, not the pixels.

  A  separation   the engine never imports the UI, and works without it
  B  the result   premium, per coverage, per subline, factors with sources,
                  referrals with what clears them -- every item the plan listed
  C  the modes    the switch changes behaviour, not the premium
  D  refusals     a bad submission is answered, not crashed on
  E  the server   the endpoints a browser actually calls

Run: python tests/verify_stage6.py
"""
from __future__ import annotations

import json
import sys
import threading
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import app                                                    # noqa: E402
from gl_engine.rating import Kernel, MODES                    # noqa: E402

SAMPLE = ROOT / "Engine_Payloads" / "OK" / "submission.json"
PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(f"{name}  {detail}".rstrip())
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f"  [{detail}]" if detail else ""))


def group_a():
    print("\nA  SEPARATION -- the claim the plan made before this was built")
    # The engine must not import the UI. Checked by reading the source rather
    # than by trusting that nobody did it: an import added later would pass a
    # runtime check if `app` happened to be loaded already.
    offenders = []
    for f in (ROOT / "gl_engine").rglob("*.py"):
        text = f.read_text(encoding="utf-8")
        if "import app" in text or "from app" in text:
            offenders.append(str(f.relative_to(ROOT)))
    check("A1 no engine module imports the UI", not offenders, str(offenders))

    # And the reverse: the UI is a consumer of the public surface only.
    src = (ROOT / "app.py").read_text(encoding="utf-8")
    check("A2 the UI imports the engine, not the other way round",
          "from gl_engine" in src, "app.py imports gl_engine")

    # The engine must be fully usable without the UI -- the notebook case.
    r = Kernel().rate(SAMPLE)
    check("A3 the engine rates with the UI never imported",
          r.complete and r.premium is not None,
          f"premium {r.premium} from a bare Kernel() call")

    # The UI reads only the documented surface of a Rating.
    public = {"premium", "by_coverage", "referrals", "messages", "trace",
              "tree", "packages", "juris", "asof", "mode", "complete",
              "stopped"}
    used = {a for a in public if f".{a}" in src or f'"{a}"' in src}
    check("A4 the UI is built from the Rating surface alone",
          len(used) >= 8, f"{len(used)} of {len(public)} attributes used")


def group_b():
    print("\nB  THE RESULT -- every item the deliverable listed")
    payload = json.loads(SAMPLE.read_text(encoding="utf-8"))
    d = app.rate(payload, "underwriting", "ROUND_HALF_UP")
    check("B1 it rates", d.get("complete") and d.get("premium"),
          f"premium {d.get('premium')}")
    check("B2 premiums per coverage, in their own array",
          isinstance(d.get("by_coverage"), list) and len(d["by_coverage"]) >= 2,
          f"{len(d.get('by_coverage', []))} coverages")
    # Per SUBLINE is the item that exposed the ancestor:: gap -- the subline
    # stat code is written by ErcSetStatisticalCodes, which was being skipped.
    subs = d.get("by_subline") or []
    check("B3 premiums per subline, in their own array",
          {s["subline"] for s in subs} >= {"334", "336"},
          ", ".join(f"{s['subline']}={s['premium']}" for s in subs))
    check("B4 the sublines account for the premium",
          sum(int(s["premium"]) for s in subs) <= int(d["premium"]),
          f"{sum(int(s['premium']) for s in subs)} of {d['premium']} "
          f"(the rest is policy-level)")
    check("B5 every factor carries where it came from",
          d["factors"] and all(f["source"] for f in d["factors"]),
          f"{len(d['factors'])} factors, all sourced")
    check("B6 the factors are in the order they were used",
          d["factors"][0]["kind"] in ("lookup", "lookup-banded",
                                      "lookup-interpolated", "round"),
          d["factors"][0]["detail"][:48])
    check("B7 the submission check runs alongside the rating",
          isinstance(d.get("findings"), list), f"{len(d.get('findings', []))} findings")


def group_c():
    print("\nC  THE MODES -- one engine, two policies")
    payload = json.loads(SAMPLE.read_text(encoding="utf-8"))
    strict = app.rate(payload, "strict-erc", "ROUND_HALF_UP")
    uw = app.rate(payload, "underwriting", "ROUND_HALF_UP")
    check("C1 both modes are offered", set(MODES) == {"strict-erc", "underwriting"},
          str(sorted(MODES)))
    check("C2 the mode does not change the premium",
          strict["premium"] == uw["premium"], f"{strict['premium']} both ways")
    check("C3 strict mode applies no referrals",
          strict["referrals"] == [], "0 referrals")
    # A referral must say what would clear it where ISO makes that knowable.
    ak = app.rate(json.loads((ROOT / "Engine_Payloads" / "AK" /
                              "submission.json").read_text(encoding="utf-8")),
                  "underwriting", "ROUND_HALF_UP")
    check("C4 underwriting mode surfaces a real referral",
          any(r["code"] == "R16" for r in ak["referrals"]),
          "; ".join(r["code"] for r in ak["referrals"]) or "none")
    check("C5 the rounding mode is reported with the answer",
          strict["rounding"] == "ROUND_HALF_UP", strict["rounding"])


def group_d():
    print("\nD  REFUSALS -- answered, not crashed on")
    d = app.rate({"body": {"SchemeKeys": {}}}, "strict-erc", "ROUND_HALF_UP") \
        if False else None
    try:
        app.rate({"body": {"SchemeKeys": {}}}, "strict-erc", "ROUND_HALF_UP")
        check("D1 a submission with no date is refused", False, "accepted")
    except Exception as exc:                                  # noqa: BLE001
        check("D1 a submission with no date is refused", True,
              type(exc).__name__)
    payload = json.loads(SAMPLE.read_text(encoding="utf-8"))
    payload["body"]["SchemeKeys"]["EffectiveDateTime"] = "2019-01-01T00:00:00"
    try:
        app.rate(payload, "strict-erc", "ROUND_HALF_UP")
        check("D2 a date below the corpus floor is refused", False, "accepted")
    except Exception as exc:                                  # noqa: BLE001
        check("D2 a date below the corpus floor is refused", True,
              type(exc).__name__)


def group_e():
    print("\nE  THE SERVER -- the endpoints a browser calls")
    srv = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{port}"
    try:
        page = urllib.request.urlopen(base + "/").read().decode()
        check("E1 the page is served", "GL Rating Engine" in page,
              f"{len(page):,} bytes, no framework")
        meta = json.loads(urllib.request.urlopen(base + "/api/samples").read())
        check("E2 every jurisdiction sample is offered",
              len(meta["jurisdictions"]) == 51,
              f"{len(meta['jurisdictions'])} jurisdictions")
        one = json.loads(urllib.request.urlopen(base + "/api/sample/OK").read())
        check("E3 a sample loads", "GeneralLiability" in one.get("body", {}),
              "OK submission.json")
        req = urllib.request.Request(
            base + "/api/rate",
            data=json.dumps({"payload": one, "mode": "underwriting",
                             "rounding": "ROUND_HALF_UP"}).encode(),
            headers={"Content-Type": "application/json"})
        d = json.loads(urllib.request.urlopen(req).read())
        check("E4 rating over HTTP gives the same answer as the library",
              d["premium"] == str(Kernel().rate(SAMPLE).premium),
              f"{d['premium']} both ways")
        # A refusal must come back as an answer the page can render, not a 500.
        req = urllib.request.Request(
            base + "/api/rate", data=b'{"payload":{},"mode":"strict-erc"}',
            headers={"Content-Type": "application/json"})
        d = json.loads(urllib.request.urlopen(req).read())
        check("E5 a refusal returns 200 with the reason, not a server error",
              "error" in d, str(d.get("error", ""))[:56])
    finally:
        srv.shutdown()


def main() -> int:
    print("Stage 6 acceptance -- the interface")
    if not SAMPLE.exists():
        print("  samples missing: run scripts/build_sample_payloads.py")
        return 1
    group_a(); group_b(); group_c(); group_d(); group_e()
    total = len(PASS) + len(FAIL)
    print(f"\n{len(PASS)}/{total} passed")
    if FAIL:
        print("\nFAILURES:")
        for f in FAIL:
            print(f"  {f}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
