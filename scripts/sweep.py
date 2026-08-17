"""Run one configuration across jurisdictions. Engine-only, or against ISO.

    python scripts/sweep.py --set occurrence_limit="500,000 CSL"
    python scripts/sweep.py --set size_of_risk=Yes --live
    python scripts/sweep.py --set premops_pd_deductible="5,000 Per Occurrence" \
                            --juris OK --juris NY --live
    python scripts/sweep.py --controls          # what may be set, and to what

**Three outcomes, not two.** A jurisdiction that cannot express the
configuration -- NY has no claims-made form, 20 jurisdictions declare a single
prem/ops territory -- is `NOT APPLICABLE` and says why. Counting those as
disagreements would report twenty failures for a risk ISO never permitted, and
the number that matters (*do we agree where the question is legal?*) would be
buried.

**Engine-only by default.** All 51 rate offline in about ninety seconds and cost
nothing. `--live` adds one real call per jurisdiction -- about twenty minutes for
a full sweep -- and the count is reported before and after.

Agreement is not defined here. `phase2_compare.compare_payload` defines it, and
this calls it, because two definitions of *agree* would drift and the drift would
look like a rating defect.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import variants as V                                          # noqa: E402
from phase2_compare import _differ, compare_payload            # noqa: E402
from raas import NO_ISO, RaaS, RaaSError                       # noqa: E402
from gl_engine.rating import Kernel, MODES, STRICT             # noqa: E402

#: The unvaried premium per jurisdiction, cached on disk. The stored base
#: submissions do not change, so re-rating 51 of them on every sweep would
#: double the wall clock to answer a question already answered.
BASELINES = ROOT / "scripts" / "erc" / "out" / "baselines.json"

_DECLARED: dict = {}


def engine_version() -> str:
    """The engine version, for stamping a stored run.

    Here rather than in the caller so **`ui/` never imports `gl_engine`** --
    asserted by `tests/verify_tester.py`. A version string is a small thing to
    reach across a boundary for, and reaching for small things is how a
    boundary stops meaning anything.
    """
    import gl_engine
    return getattr(gl_engine, "__version__", "")


def declared(juris: str, asof: str = V.DEFAULT_ASOF) -> V.Declared:
    key = (juris, asof)
    if key not in _DECLARED:
        _DECLARED[key] = V.Declared(juris, asof)
    return _DECLARED[key]


def baselines(kernel, jurisdictions) -> dict:
    """`{juris: premium}` for the unvaried risk, computed once and kept."""
    have = {}
    if BASELINES.exists():
        try:
            have = json.loads(BASELINES.read_text(encoding="utf-8"))
        except ValueError:
            have = {}
    missing = [j for j in jurisdictions if j not in have]
    for j in missing:
        try:
            r = kernel.rate(declared(j).base())
            have[j] = str(r.premium) if r.complete else None
        except Exception:                                     # noqa: BLE001
            have[j] = None
    if missing:
        BASELINES.parent.mkdir(parents=True, exist_ok=True)
        BASELINES.write_text(json.dumps(have, indent=1, sort_keys=True),
                             encoding="utf-8")
    return have


def run_config(config: dict, jurisdictions=None, compare: bool = False,
               mode: str = STRICT, asof: str = V.DEFAULT_ASOF,
               progress=None, probe: bool = True) -> dict:
    """Rate one configuration everywhere. Returns rows and a summary.

    `progress(done, total, row)` is called after each jurisdiction so a caller
    can show a run that takes ninety seconds -- or twenty minutes -- without
    holding a request open.
    """
    cfg = V.clean(config)
    js = list(jurisdictions or V.Declared.jurisdictions())
    if compare:
        # A jurisdiction ISO will not answer for cannot be compared. Leaving it
        # in reports a permanent red row that reads as an engine failure.
        skipped_iso = [j for j in js if j in NO_ISO]
        js = [j for j in js if j not in NO_ISO]
    else:
        skipped_iso = []

    kernel = Kernel(mode=mode, resolver=V.Declared.resolver())
    base_premiums = baselines(kernel, js)
    client = dp = None
    if compare:
        client = RaaS()
        dp = _differ()

    rows, started = [], time.time()
    for i, j in enumerate(js, start=1):
        row = {"n": i, "juris": j, "base": base_premiums.get(j)}
        try:
            d = declared(j, asof)
            payload = V.build(cfg, d)
        except V.VariantError as exc:
            row.update(status="NOT APPLICABLE", detail=str(exc)[:220])
            rows.append(row)
            if progress:
                progress(i, len(js), row)
            continue
        except Exception as exc:                              # noqa: BLE001
            row.update(status="BUILD ERROR",
                       detail=f"{type(exc).__name__}: {exc}"[:220])
            rows.append(row)
            if progress:
                progress(i, len(js), row)
            continue

        try:
            ours = kernel.rate(payload)
        except Exception as exc:                              # noqa: BLE001
            row.update(status="ENGINE ERROR",
                       detail=f"{type(exc).__name__}: {exc}"[:220])
            rows.append(row)
            if progress:
                progress(i, len(js), row)
            continue
        if not ours.complete:
            row.update(status="ENGINE STOPPED", detail=str(ours.stopped)[:220])
            rows.append(row)
            if progress:
                progress(i, len(js), row)
            continue

        row["ours"] = str(ours.premium)
        row["packages"] = " over ".join(ours.packages)
        row["referrals"] = len(ours.referrals)
        b = base_premiums.get(j)
        if b:
            row["from_base"] = str(ours.premium - Decimal(b))
            row["moved"] = ours.premium != Decimal(b)

        if not compare:
            row["status"] = "RATED"
        else:
            r = compare_payload(j, payload, kernel, client, dp)
            row["status"] = r["status"]
            for k in ("iso", "delta", "iso_package", "edition_agrees",
                      "fields_compared", "fields_differing",
                      "first_differences", "detail"):
                if r.get(k) not in (None, ""):
                    row[k] = r[k]
        rows.append(row)
        if progress:
            progress(i, len(js), row)

    # OI-93: a variant that rated and left the premium alone reads exactly like
    # one that worked. Ask why -- is no declared value able to move it (a fact
    # about ISO), or did we choose one that does nothing (a fact about us)?
    # Offline, no live calls, and cheap: the ISO-side answer costs no ratings
    # at all because those configurations record no choice sites.
    if probe:
        for r in rows:
            if r.get("moved") is not False:
                continue
            try:
                d = declared(r["juris"], asof)
                v = V.probe_no_op(cfg, d, kernel,
                                  Decimal(base_premiums[r["juris"]]))
            except Exception as exc:                          # noqa: BLE001
                v = {"verdict": "PROBE FAILED",
                     "detail": f"{type(exc).__name__}: {exc}"[:160]}
            r["no_op"] = v

    def count(*statuses):
        return [r["juris"] for r in rows if r.get("status") in statuses]

    summary = {
        "config": cfg,
        "fingerprint": V.fingerprint(cfg),
        "describes": V.describe(cfg),
        "mode": mode,
        "asof": asof,
        "compared": compare,
        "seconds": round(time.time() - started, 1),
        "live_calls": client.calls if client else 0,
        "total": len(rows),
        "rated": len(count("RATED", "MATCH", "PREMIUM ONLY", "DIFF")),
        "agree": len(count("MATCH")),
        "premium_only": count("PREMIUM ONLY"),
        "differ": count("DIFF"),
        "not_applicable": count("NOT APPLICABLE"),
        "engine_stopped": count("ENGINE STOPPED"),
        "errors": count("ENGINE ERROR", "BUILD ERROR", "RAAS FAILED"),
        "unmoved": [r["juris"] for r in rows if r.get("moved") is False],
        "inert_control": [r["juris"] for r in rows
                          if (r.get("no_op") or {}).get("verdict")
                          == V.INERT_CONTROL],
        "inert_value": [r["juris"] for r in rows
                        if (r.get("no_op") or {}).get("verdict")
                        == V.INERT_VALUE],
        "iso_not_subscribed": skipped_iso,
    }
    return {"summary": summary, "rows": rows}


# ---------------------------------------------------------------------- CLI

def main(argv) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--set", action="append", default=[], metavar="id=value",
                    help="set a control; repeatable")
    ap.add_argument("--juris", action="append", default=[])
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--mode", default=STRICT, choices=sorted(MODES))
    ap.add_argument("--controls", action="store_true",
                    help="list the controls and their options, then stop")
    a = ap.parse_args(argv)

    if a.controls:
        d = V.Declared((a.juris or ["OK"])[0].upper())
        opts = V.options_for(d)
        print(f"controls, with {d.juris}'s declared options\n")
        for group in V.GROUPS:
            print(f"-- {group}")
            for c in V.CONTROLS:
                if c.group != group:
                    continue
                s = opts[c.id]
                if s["kind"] == "number":
                    detail = f"number {s['min']}..{s['max']}"
                else:
                    detail = f"{len(s['values'])} options: " \
                             f"{', '.join(map(str, s['values'][:4]))}" \
                             + (" ..." if len(s["values"]) > 4 else "")
                print(f"   {c.id:26s} {detail}")
        return 0

    config = {}
    for pair in a.set:
        if "=" not in pair:
            print(f"--set wants id=value, got {pair!r}")
            return 2
        k, v = pair.split("=", 1)
        if k not in V.BY_ID:
            print(f"unknown control {k!r}; --controls lists them")
            return 2
        config[k] = v

    js = [j.upper() for j in a.juris] or None
    print(f"SWEEP -- {V.describe(config)}")
    if a.live:
        n = len([j for j in (js or V.Declared.jurisdictions())
                 if j not in NO_ISO])
        print(f"[live: {n} calls to ISO, roughly {n * 20 // 60} minutes]")
    print()

    def show(i, total, row):
        line = f"  {row['juris']:4s} {row.get('status', ''):15s}"
        if row.get("ours"):
            line += f" ours={row['ours']:>10s}"
        if row.get("iso"):
            line += f" iso={row['iso']:>10s}"
        if row.get("moved") is False:
            line += "  UNCHANGED from base"
        if row.get("detail"):
            line += f"  {str(row['detail'])[:70]}"
        print(line)

    try:
        out = run_config(config, js, compare=a.live, mode=a.mode, progress=show)
    except RaaSError as exc:
        print(f"cannot reach ISO: {exc}")
        return 1

    s = out["summary"]
    print()
    if s["compared"]:
        print(f"    agree with ISO on premium and every field : "
              f"{s['agree']} of {s['rated']} rated")
    else:
        print(f"    rated : {s['rated']} of {s['total']}")
    for label, key in (("not applicable here", "not_applicable"),
                       ("engine refused", "engine_stopped"),
                       ("premium agrees, fields differ", "premium_only"),
                       ("disagree", "differ"),
                       ("errors", "errors")):
        if s[key]:
            print(f"    {label:41s} : {len(s[key])} ({', '.join(s[key])})")
    if s["unmoved"]:
        print(f"    premium unchanged from base : {len(s['unmoved'])} "
              f"({', '.join(s['unmoved'])})")
        if s.get("inert_control"):
            print(f"      INERT CONTROL -- no declared value moves it, so this "
                  f"is ISO's filing, not our pick : "
                  f"{', '.join(s['inert_control'])}")
        for r in out["rows"]:
            v = r.get("no_op") or {}
            if v.get("verdict") == V.INERT_VALUE:
                print(f"      INERT VALUE   -- {r['juris']}: "
                      f"{v['column']}={v['chosen']} does nothing; "
                      f"{v['moves_with']} gives {v['premium']} "
                      f"(of {v['alternatives']} alternatives). OI-93")
        print("      -- a configuration that does not move the premium "
              "exercised nothing; that is a finding, not a pass.")
    if s["live_calls"]:
        print(f"    live calls made : {s['live_calls']}")
    print(f"    {s['seconds']}s")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
