#!/usr/bin/env python3
"""TC-33: seed the Regression Library with what we already trust. No ISO calls.

  * **ISO's STC fixtures**: every stored fixture response (`chunk13_fixture_*_response.json`, 293), each its own entry
    with its own response as the reference, rebuilt as `157_` sends it -- so the library's count is `157_ --all`'s;
  * **the chunk golden cases** with an ISO answer on disk (`chunk13_golden_*`);
  * **the samples** (D22: `/`'s all-samples check, as a zero-call library run): GL's 51 `Engine_Payloads` submissions
    and CP's sample in each state; the reference is ISO's stored answer to that exact request when one exists, else our
    premium today (labelled ours).

Re-running is safe: a scenario already in the library is left as it is.

    python scripts/tc/tc33_seed_library.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "scripts", ROOT / "scripts" / "cf"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from console import library, regression, store, tracediff, workbench as WB  # noqa: E402

RES = ROOT / "results" / "cf-raas"


def main() -> int:
    have = {e["scenario"] for e in library.entries()}
    added = Counter()

    def add(**kw):
        if kw["scenario"] in have:
            return
        library.promote(**kw)
        have.add(kw["scenario"])
        added[kw["origin"]] += 1

    r157 = import_module("157_chunk14_c14-02_total_replay")
    fx = r157.fixture_index()
    for resp in sorted(RES.glob("chunk13_fixture_*_response.json")):
        stem = resp.name[len("chunk13_fixture_"):-len("_response.json")]
        f = fx.get(stem)
        if f is None:
            continue
        d = json.loads(f.read_text(encoding="utf-8-sig"))
        state = d["SchemeKeys"]["ProductName"].split()[-1]
        add(scenario=f"FX-{stem}", line="CP", state=state, origin="fixture", fixture=stem, fixture_file=str(f),
            response_file=resp.relative_to(ROOT).as_posix(), note="ISO STC fixture, rebuilt as 157_ sends it",
            request=regression.request_for({"fixture": stem, "fixture_file": str(f)}))

    idx = {e["hash"]: e for e in store.load()["references"]}
    for e in idx.values():
        if any("golden" in f for f in e["files"]) and e["outcome"] == "rated":
            add(scenario=tracediff.scenario_id(e["line"], e["state"], e["hash"]), line=e["line"], state=e["state"],
                origin="golden", request_hash=e["hash"], note="chunk golden case")

    import property_rating as pr
    for st in pr.states():
        req = pr.sample(st)
        e = store.lookup(req)
        sid = f"SAMPLE-CP-{st}"
        if e and e["outcome"] == "rated":
            add(scenario=sid, line="CP", state=st, origin="sample", request_hash=e["hash"], note="the app's sample")
        else:
            r = WB.rate("CP", req)
            if r["outcome"] == "rated":
                add(scenario=sid, line="CP", state=st, origin="sample", request=req, ours=r["premium"],
                    note="the app's sample; ISO has not answered it")
    for d in sorted((ROOT / "Engine_Payloads").iterdir()):
        f = d / "submission.json"
        if not f.exists():
            continue
        req = json.loads(f.read_text(encoding="utf-8"))
        e = store.lookup(req)
        sid = f"SAMPLE-GL-{d.name}"
        if e and e["outcome"] == "rated":
            add(scenario=sid, line="GL", state=d.name, origin="sample", request_hash=e["hash"], note="the app's sample")
        else:
            r = WB.rate("GL", req)
            if r["outcome"] == "rated":
                add(scenario=sid, line="GL", state=d.name, origin="sample", request=req, ours=r["premium"],
                    note="the app's sample; ISO has not answered it")
    print(f"added {dict(added)}; the library holds {len(library.entries())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
