#!/usr/bin/env python3
"""Chunk 28 C28-20 (corpus refresh): a newly imported state package, rated against ISO. Live ISO.

For one state and one date on or after the new package's edition:
  * the new package's own ISO test cases (its `STC/*.json`), at their own date
  * every stored chunk 13 ISO fixture for that state (rated by ISO at 2026-09-17), re-dated to --date
Each is sent to ISO and rated on ours; the package ISO names (`Scheme`) is checked against the one our resolver picks,
then every `Premium` / `ErcCalculatedTotalPremium` by path and the whole (level, message) multiset are compared.
Both refusing counts as agreeing.

    python scripts/cf/256_chunk28_c28-20_new_package.py --state IL --date 2026-11-01

Results: results/cf-raas/chunk28_c28-20_<state>_<case>_{request,response}.json. Exits 1 on any disagreement.
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))
sys.stdout.reconfigure(line_buffering=True, encoding="utf-8")

from cf_engine.config import CORPUS_ROOT
from cf_engine.resolve import book_for
from gl_engine.interp.values import InterpretError

c3 = import_module("236_chunk26_rc3")          # wraps MessageHelper (TAGGED)
rep = import_module("157_chunk14_c14-02_total_replay")
r2 = import_module("239_chunk27_rc2")
cmp = rep.cmp
RES = ROOT / "results" / "cf-raas"
PKG = re.compile(r"CF ([A-Z]{2}) (\d{8}) (V\d\d)")


def cases(state: str, date: str) -> list:
    index = {p.stem: p for p in CORPUS_ROOT.rglob("STC/*.json")}
    out = []
    for pkg_dir in CORPUS_ROOT.glob(f"*/CF {state} *"):
        edition = pkg_dir.name.split()[2]
        if f"{edition[:4]}-{edition[4:6]}-{edition[6:]}" > "2026-09-17":
            for f in sorted(pkg_dir.glob("STC/*.json")):
                d = json.loads(f.read_text(encoding="utf-8-sig"))
                out.append((f"new-{f.stem}", d, d["SchemeKeys"]["EffectiveDateTime"][:10]))
    for r in sorted(RES.glob("chunk13_fixture_*_response.json")):
        stem = r.name[len("chunk13_fixture_"):-len("_response.json")]
        f = index.get(stem)
        if f is None:
            continue
        d = json.loads(f.read_text(encoding="utf-8-sig"))
        if d["SchemeKeys"]["ProductName"].split()[-1] == state:
            out.append((f"fx-{stem}", d, date))
    return out


def ours_pkg(state: str, date: str) -> str:
    m = re.search(r"CF_([A-Z]{2})_(\d{8})_(V\d\d)", str(book_for(state, date.replace("-", ""))))
    return f"CF {m.group(1)} {m.group(2)} {m.group(3)}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", required=True)
    ap.add_argument("--date", required=True)
    a = ap.parse_args()
    import raas as raas_mod
    client = raas_mod.RaaS()
    cs = cases(a.state, a.date)
    fails = []
    for i, (cid, d, date) in enumerate(cs, 1):
        req = {"header": {}, "body": {"SchemeKeys": {"ProductName": d["SchemeKeys"]["ProductName"],
                                                     "EffectiveDateTime": f"{date}T00:00:00"},
                                      "CommercialProperty": d["CommercialProperty"]}}
        base = RES / f"chunk28_c28-20_{a.state}_{cid}"
        Path(f"{base}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
        mine = ours_pkg(a.state, date)
        iso_err = our_err = None
        try:
            resp = r2.rate_retry(client, req)
            Path(f"{base}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
        except raas_mod.RaaSError as exc:
            resp, iso_err = None, (re.search(r'"Message":"([^"]{0,200})', str(exc.body)) or [None, str(exc.body)[:200]])[1]
        c3.TAGGED.clear()
        try:
            data, ip = cmp.rate(req)
        except InterpretError as exc:
            data, our_err = None, str(exc)[:200]
        head = f"[{i}/{len(cs)}] {cid} @ {date}"
        if iso_err or our_err:
            ok = bool(iso_err and our_err)
            print(f"{head}: {'AGREE, both refuse' if ok else 'DIFFER'}\n    ISO: {iso_err}\n    ours: {our_err}")
            if not ok:
                fails.append(cid)
            continue
        hdr = resp.get("Header") or resp.get("header") or {}
        m = PKG.search(str(hdr.get("Scheme", "")))
        theirs = m.group(0) if m else "?"
        iso_p, our_p = rep.iso_prem(resp), rep.our_prem(data)
        dd = [(k, v, our_p.get(k)) for k, v in iso_p.items() if not cmp.same(v, our_p.get(k))]
        ours_m = collections.Counter((c3.lvl(t), y) for t, y in c3.TAGGED)
        iso_m = collections.Counter(c3.iso_tagged(resp))
        tot = iso_p.get("CommercialProperty[0]/ErcCalculatedTotalPremium")
        ok = not dd and ours_m == iso_m and theirs == mine
        print(f"{head}: {'AGREE' if ok else 'DIFFER'}  package ISO {theirs} / ours {mine}; "
              f"{len(iso_p) - len(dd)} of {len(iso_p)} premiums; total ISO {tot}; messages "
              f"{'equal' if ours_m == iso_m else 'DIFFER'} ({sum(iso_m.values())} ISO)"
              + "".join(f"\n    {k[-90:]} ISO {v} ours {o}" for k, v, o in dd[:8])
              + "".join(f"\n    ISO only: {y[:110]} x{n}" for (t, y), n in (iso_m - ours_m).items())
              + "".join(f"\n    ours only: {y[:110]} x{n}" for (t, y), n in (ours_m - iso_m).items()))
        if not ok:
            fails.append(cid)
    print(f"\n{a.state} @ {a.date}: {len(cs) - len(fails)} of {len(cs)} agree with ISO"
          + (f"; differ: {', '.join(fails)}" if fails else ""))
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
