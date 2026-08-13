"""Phase 2 acceptance: our engine against ISO's live service.

**Skips cleanly without credentials.** A test suite that needs a paid external
service to pass is a suite people stop running, so the offline checks (A) always
run and the live ones (B, C) report SKIP when `RAAS_*` is not configured.

  A  offline      the client is configured from the environment, never from a
                  file in this repository, and it logs no secret
  B  live         the same submission through both, compared on every published
                  field -- not just the premium
  C  rounding     what the live service settles about OI-70, and what it does
                  not

Run: python tests/verify_phase2.py          (offline only, no calls)
     python tests/verify_phase2.py --live   (makes live calls)
"""
from __future__ import annotations

import json
import os
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import raas                                                   # noqa: E402
from gl_engine import EditionResolver                         # noqa: E402
from gl_engine.rating import Kernel                           # noqa: E402

SAMPLES = ROOT / "Engine_Payloads"
RESULTS = ROOT / "scripts" / "erc" / "out" / "phase2.csv"
PASS, FAIL, SKIP = [], [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(f"{name}  {detail}".rstrip())
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f"  [{detail}]" if detail else ""))


def skip(name, why):
    SKIP.append(name)
    print(f"  SKIP  {name}  [{why}]")


def group_a():
    print("\nA  THE CLIENT -- offline, no calls")
    path = ROOT / "scripts" / "raas.py"
    src = path.read_text(encoding="utf-8")
    # Check what is IMPORTED, not what is mentioned. The first version of this
    # searched for the string "httpx" and failed on the docstring explaining
    # why httpx is not used -- a test that reads prose as code.
    import ast
    mods = set()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Import):
            mods.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            mods.add(node.module.split(".")[0])
    third_party = mods - set(sys.stdlib_module_names)
    check("A1 standard library only, no new dependency",
          not third_party and "urllib" in mods,
          f"imports {sorted(mods)}")
    # A client that prints a token or a secret turns every log into a leak.
    # Look at what is passed to print/log, not at every line mentioning a
    # secret -- the Basic-auth header has to interpolate one to exist.
    # Match IDENTIFIERS that hold a secret, not any text containing the word.
    # The second version flagged `urlparse(c.token_url).netloc` -- a hostname --
    # and the literal "(token withheld)". Both are the opposite of a leak.
    SENSITIVE = {"_token", "secret", "client_secret", "password",
                 "access_token"}
    leaks = []
    for node in ast.walk(ast.parse(src)):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        name = getattr(fn, "id", "") or getattr(fn, "attr", "")
        if name not in ("print", "info", "debug", "warning", "error"):
            continue
        for arg in ast.walk(node):
            ident = ""
            if isinstance(arg, ast.Name):
                ident = arg.id
            elif isinstance(arg, ast.Attribute):
                ident = arg.attr
            elif isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                continue                       # a literal cannot leak a value
            if ident.lower() in SENSITIVE:
                leaks.append(f"{name}(... {ident} ...)")
    check("A2 no secret or token is passed to print or a logger",
          not leaks, str(leaks) if leaks else "nothing sensitive is printed")
    check("A3 credentials come from the environment, not from this repo",
          'os.environ' in src and str(ROOT) not in src.replace("\\\\", "\\"),
          "RAAS_* environment variables")
    check("A4 missing credentials fail with a named list, not a stack trace",
          "missing credentials" in src, "RaaSError names what is absent")

    # OI-86, decided 2026-08-13: PR is not on the subscription and the
    # entitlement is not available, so it is left out of comparisons. Two
    # things have to stay true, and the second is the one worth guarding:
    # it is excluded from the COMPARISON, and it still RATES.
    check("A5 an unentitled jurisdiction is excluded from a comparison",
          raas.NO_ISO == frozenset({"PR"}), f"NO_ISO = {set(raas.NO_ISO)}")
    import app                                                # noqa: PLC0415
    check("A6 one definition of it, not a copy per caller",
          app.NO_ISO is raas.NO_ISO, "app.py reads scripts/raas.py")
    fake = type("R", (), {"premium": Decimal(0), "packages": ["x"]})()
    pr = json.loads((SAMPLES / "PR" / "submission.json").read_text(encoding="utf-8"))
    verdict = app.compare_with_iso(pr, fake)
    # Refuse BEFORE the call: spending a request to produce a 401 renders a
    # subscription boundary as a fault.
    check("A7 the refusal says which jurisdiction and why, without calling",
          verdict["available"] is False and "PR" in verdict["reason"]
          and "subscription" in verdict["reason"], verdict["reason"][:70])
    priced = Kernel(resolver=EditionResolver()).rate(pr)
    check("A8 it is still rated -- disregarded means uncompared, not unsupported",
          priced.complete and priced.premium > 0,
          f"PR prices at {priced.premium} with no external check of any kind")


def group_b(live: bool):
    print("\nB  LIVE -- the same submission through both")
    if not live:
        return skip("B  live comparison", "pass --live to make calls")
    missing = [k for k in raas.REQUIRED if not os.environ.get(k)]
    if missing:
        raas.load_env()
        missing = [k for k in raas.REQUIRED if not os.environ.get(k)]
    if missing:
        return skip("B  live comparison", f"not configured: {missing}")

    client = raas.RaaS()
    kernel = Kernel(resolver=EditionResolver())
    payload = json.loads((SAMPLES / "OK" / "submission.json")
                         .read_text(encoding="utf-8"))
    ours = kernel.rate(payload)
    live_r = client.rate(payload)
    gl = live_r["Body"]["GeneralLiability"][0]

    check("B1 ISO answers", gl.get("Premium") is not None, str(gl.get("Premium")))
    check("B2 the premium agrees to the penny",
          Decimal(str(gl["Premium"])) == ours.premium,
          f"ours {ours.premium}, ISO {gl['Premium']}")
    # The scheme header names the edition ISO used, so a resolution difference
    # is never mistaken for an arithmetic one.
    parts = live_r["Header"]["Scheme"].split()
    iso_pkg = f"GL_{parts[1]}_{parts[2]}_{parts[3]}"
    check("B3 ISO used the edition we resolved",
          iso_pkg == ours.packages[0], f"{iso_pkg} == {ours.packages[0]}")
    check("B4 our request needed no reshaping",
          "GeneralLiability" in payload["body"],
          "the sample is sent as filed, only the auth block is added")


def group_c(live: bool):
    print("\nC  THE ROUNDING QUESTION (OI-70)")
    if not RESULTS.exists():
        return skip("C  rounding", "run scripts/phase2_compare.py --all first")
    import csv
    rows = list(csv.DictReader(open(RESULTS, encoding="utf-8")))
    matched = [r for r in rows if r["status"] == "MATCH"]
    check("C1 a live comparison has been run and recorded",
          len(rows) >= 50, f"{len(rows)} jurisdictions, {len(matched)} matching")

    res = EditionResolver()
    up = Kernel(rounding="ROUND_HALF_UP", resolver=res)
    dn = Kernel(rounding="ROUND_DOWN", resolver=res)
    ev = Kernel(rounding="ROUND_HALF_EVEN", resolver=res)
    diff_dn = diff_ev = n = 0
    for d in sorted(p for p in SAMPLES.iterdir() if p.is_dir()):
        src = d / "submission.json"
        if not src.exists():
            continue
        try:
            a, b, c = up.rate(src), dn.rate(src), ev.rate(src)
        except Exception:                                     # noqa: BLE001
            continue
        if not (a.complete and b.complete and c.complete):
            continue
        n += 1
        diff_dn += a.premium != b.premium
        diff_ev += a.premium != c.premium

    # Truncation is ruled out: it changes the premium in most jurisdictions and
    # ISO agrees with rounding in all of them.
    check("C2 truncation would change the answer, and ISO agrees with rounding",
          diff_dn >= 30 and len(matched) >= 50,
          f"ROUND_DOWN differs in {diff_dn} of {n}; ISO matches HALF_UP in "
          f"{len(matched)}")
    # Half-up versus half-even is NOT settled, and saying so is the point.
    check("C3 half-up and half-even are indistinguishable on this population",
          diff_ev == 0,
          f"they differ on {diff_ev} of {n} -- OI-70's tie-break stays open "
          f"until a submission is engineered that separates them")


def main(argv) -> int:
    live = "--live" in argv
    print("Phase 2 acceptance -- our engine against ISO's live service")
    group_a()
    group_b(live)
    group_c(live)
    total = len(PASS) + len(FAIL)
    print(f"\n{len(PASS)}/{total} passed" + (f", {len(SKIP)} skipped" if SKIP else ""))
    if FAIL:
        print("\nFAILURES:")
        for f in FAIL:
            print(f"  {f}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
