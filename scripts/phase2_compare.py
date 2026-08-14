"""Phase 2: the same submission through our engine and through ISO's service.

    python scripts/phase2_compare.py OK
    python scripts/phase2_compare.py --all

The build plan is explicit about the doctrine, and it is the whole reason
`strict-erc` mode exists:

> **Any difference is our defect until proven otherwise.**

This is the live half. The offline half (`rate_all_payloads.py`) compares
against 50 stored answers and reached 49 of 49; **that population is one class
code and one location in each state.** ISO's service will rate anything, so
this is the first comparison that can be extended past what happened to be on
disk.

Three things it does that the offline comparison could not:

* **Rates what we send**, so the input is never in question -- the stored pairs
  had to be checked for that (OI-77, OI-78) and three of fifty were unusable
* **Names the edition ISO used**, in the response header, so a difference from
  resolving the wrong rulebook is distinguishable from a difference in
  arithmetic
* **Compares every published field**, not just the premium -- a total can be
  right for the wrong reasons

Live calls are counted and reported. It runs one jurisdiction unless told
otherwise, because a comparison that quietly makes 51 calls to a rating service
is a surprise nobody asked for.
"""
from __future__ import annotations

import csv
import json
import sys
from decimal import Decimal
from importlib import util as _util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from raas import NO_ISO, RaaS, RaaSError                      # noqa: E402
from gl_engine import EditionResolver                         # noqa: E402
from gl_engine.rating import Kernel, STRICT                   # noqa: E402

SAMPLES = ROOT / "Engine_Payloads"
OUT = ROOT / "scripts" / "erc" / "out" / "phase2.csv"


def _differ():
    """Reuse the field-level differ rather than writing a second one."""
    spec = _util.spec_from_file_location("dp", ROOT / "scripts" / "diff_payload.py")
    mod = _util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def compare(juris: str, kernel, client, dp) -> dict:
    """Rate one submission both ways and diff every published number."""
    src = SAMPLES / juris / "submission.json"
    if not src.exists():
        return {"juris": juris, "status": "NO SAMPLE"}
    payload = json.loads(src.read_text(encoding="utf-8"))
    return compare_payload(juris, payload, kernel, client, dp)


def compare_payload(juris: str, payload: dict, kernel, client, dp) -> dict:
    """The comparison itself, for a submission held in memory.

    Split out from `compare` so **breadth** (`scripts/breadth.py`) can put a
    generated submission through the identical path. A second comparison
    written alongside this one would be a second definition of *agreement*, and
    the two would drift.
    """
    try:
        ours = kernel.rate(payload)
    except Exception as exc:                                  # noqa: BLE001
        return {"juris": juris, "status": "OURS FAILED",
                "detail": f"{type(exc).__name__}: {exc}"}
    if not ours.complete:
        return {"juris": juris, "status": "OURS STOPPED",
                "detail": str(ours.stopped)[:120]}

    try:
        live = client.rate(payload)
    except RaaSError as exc:
        return {"juris": juris, "status": "RAAS FAILED", "detail": str(exc)[:160]}

    body = live.get("Body", {})
    gl = (body.get("GeneralLiability") or [{}])[0]
    scheme = live.get("Header", {}).get("Scheme", "")
    iso_premium = gl.get("Premium")

    # The edition ISO used, so a resolution difference is never mistaken for an
    # arithmetic one.
    iso_pkg = ""
    parts = scheme.split()
    if len(parts) >= 4:
        iso_pkg = f"GL_{parts[1]}_{parts[2]}_{parts[3]}"

    want = {dp.normalise(k): v for k, v in dp.iso_numbers(gl).items()}
    from gl_engine.interp import tree as _t
    ours_gl = _t.select_one("GeneralLiabilityTable/GeneralLiability", ours.tree)
    got = {dp.normalise(k): v for k, v in dp.our_numbers(ours_gl).items()}

    differ = [(k, got[k], want[k]) for k in sorted(want)
              if k in got and got[k] != want[k]]
    missing = [k for k in sorted(want) if k not in got]

    same_premium = (iso_premium is not None
                    and Decimal(str(iso_premium)) == ours.premium)
    return {
        "juris": juris,
        "status": "MATCH" if same_premium and not differ else
                  ("PREMIUM ONLY" if same_premium else "DIFF"),
        "ours": str(ours.premium), "iso": str(iso_premium),
        "delta": str(ours.premium - Decimal(str(iso_premium)))
                 if iso_premium is not None else "",
        "our_packages": " over ".join(ours.packages),
        "iso_package": iso_pkg,
        "edition_agrees": "yes" if iso_pkg == ours.packages[0] else "NO",
        "fields_compared": len(want),
        "fields_differing": len(differ),
        "fields_missing": len(missing),
        "first_differences": "; ".join(
            f"{k}: ours {a} ISO {b}" for k, a, b in differ[:3]),
        "messages": len(body.get("RatingMessages", {}).get("Errors", []) or []),
    }


def main(argv) -> int:
    dp = _differ()
    resolver = EditionResolver()
    kernel = Kernel(mode=STRICT, resolver=resolver)
    try:
        client = RaaS()
    except RaaSError as exc:
        print(f"cannot reach ISO: {exc}")
        return 1

    which = [a.upper() for a in argv if not a.startswith("--")]
    if "--all" in argv:
        which = sorted(p.name for p in SAMPLES.iterdir()
                       if p.is_dir() and (p / "submission.json").exists())
        # NO_ISO jurisdictions rate offline but cannot be compared -- ISO has
        # nothing to say about them. Naming one explicitly still runs it, so
        # the 401 can be re-checked if the subscription ever changes.
        skipped = [j for j in which if j in NO_ISO]
        which = [j for j in which if j not in NO_ISO]
        if skipped:
            print(f"[not on the ISO subscription, left out: {', '.join(skipped)}]")
    if not which:
        which = ["OK"]

    print(f"PHASE 2 -- our engine against ISO's live service "
          f"({len(which)} jurisdiction{'s' if len(which) != 1 else ''})")
    print()
    rows = []
    for j in which:
        r = compare(j, kernel, client, dp)
        rows.append(r)
        line = (f"    {r['juris']:4s} {r['status']:13s} "
                f"ours={r.get('ours', '-'):>9s} iso={r.get('iso', '-'):>9s}")
        if r.get("edition_agrees") == "NO":
            line += f"  EDITION {r.get('iso_package')} != {r.get('our_packages','').split(' over ')[0]}"
        if r.get("fields_differing"):
            line += f"  {r['fields_differing']} of {r['fields_compared']} fields differ"
        if r.get("detail"):
            line += f"  {r['detail'][:70]}"
        print(line)
        if r.get("first_differences"):
            print(f"         {r['first_differences'][:150]}")

    # **A one-jurisdiction check must not destroy the record of fifty-one.**
    # `phase2.csv` is the result of record -- `verify_phase2` group C reads it
    # to assert that a full live comparison has been run, and to answer the
    # rounding question (OI-70) over the whole population. Running
    # `phase2_compare.py GA` used to overwrite it with a single row, which
    # silently turned "50 of 51 match" into "1 of 1" and failed the suite for a
    # reason that had nothing to do with the engine. Found on 2026-08-14 by
    # doing exactly that.
    out_path = OUT if "--all" in argv else OUT.with_name("phase2-partial.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    keys = sorted({k for r in rows for k in r})
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)

    n = len(rows)
    ok = sum(1 for r in rows if r["status"] == "MATCH")
    prem = sum(1 for r in rows if r["status"] == "PREMIUM ONLY")
    print()
    print(f"    premium AND every published field agree : {ok} of {n}")
    if prem:
        print(f"    premium agrees, some fields differ      : {prem} of {n}")
    bad = [r for r in rows if r["status"] not in ("MATCH", "PREMIUM ONLY")]
    if bad:
        print(f"    not matching                            : {len(bad)} "
              f"({', '.join(r['juris'] for r in bad)})")
    print(f"    live calls made                         : {client.calls}")
    print()
    print("    Any difference is our defect until proven otherwise.")
    print(f"\n[wrote {OUT}]")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
