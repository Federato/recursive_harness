"""C14-02: the policy total, replayed against every stored ISO fixture response.

No ISO calls. Chunk 13's C13-23 sent 355 ISO STC fixtures to ISO at 2026-09-17
and kept 294 responses (`results/cf-raas/chunk13_fixture_*_response.json`). Each
fixture is rebuilt exactly (`155_`'s request), rated on the engine, and every
`Premium` and `ErcCalculatedTotalPremium` on every record -- the policy's total
included -- is compared with ISO's, by path.

    python scripts/cf/157_chunk14_c14-02_total_replay.py          # the 46-fixture sample (regression)
    python scripts/cf/157_chunk14_c14-02_total_replay.py --all    # all 293 (chunk close-outs, edition changes)

THE SAMPLE (fixed 2026-09-24, user-approved). The full run re-rates 293 full ISO
policies (~8 min alone, ~22 min inside the regression). SAMPLE is a covering set
chosen from the stored responses by a greedy cover of 133 features -- every state
represented (46) and every record type that carries a non-zero premium in ISO's
answers (87, KY mine subsidence among them) -- so anything the full run exercises,
the sample exercises at least once. None of the 293 has a negative premium or more
than one location, so the sample gives nothing up there: negative premiums are
pinned by 158_, multiple locations are C14-08. What the sample can miss: a defect
confined to a (state, record type) pairing it doesn't hold -- which is why --all
runs at every chunk gate.

Exits 1 on any disagreement.
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))

from cf_engine.config import CORPUS_ROOT
from gl_engine.interp.values import InterpretError

cmp = import_module("154_chunk13_rc5_fields_messages")
rp = cmp.rp
ISO_CF = CORPUS_ROOT  # the engine's own corpus root (env CF_ERC_ROOT), not a hardcoded path
RES = ROOT / "results" / "cf-raas"
FIELDS = ("Premium", "ErcCalculatedTotalPremium")
SAMPLE = ['STC_CP000011752', 'STC_CP000012176', 'STC_CP000012566', 'STC_CP000013009', 'STC_CP000013096', 'STC_CP000013796', 'STC_CP000013797', 'STC_CP000013798', 'STC_CP000013799', 'STC_CP000013817', 'STC_CP000013908', 'STC_CP000013983', 'STC_CP000014003', 'STC_CP000014036', 'STC_CP000014057', 'STC_CP000014113', 'STC_CP000014177', 'STC_CP000014227', 'STC_CP000014270', 'STC_CP000014372', 'STC_CP000014470', 'STC_CP000014480', 'STC_CP000014517', 'STC_CP000014589', 'STC_CP000014647', 'STC_CP000014704', 'STC_CP000014706', 'STC_CP000014746', 'STC_CP000014784', 'STC_CP000014907', 'STC_CP000014948', 'STC_CP000015398', 'STC_CP000015565', 'STC_CP000015566', 'STC_CP000015648', 'STC_CP000015848', 'STC_CP000016007', 'STC_CP000016089', 'STC_CP000016624', 'STC_CP000016756', 'STC_CP000017535', 'STC_CP000017811', 'STC_CP000017917', 'STC_CP000019069', 'STC_CP000019697', 'STC_CP000021017']


def fixture_index():
    """stem -> STC path, in one pass instead of a corpus-wide search per fixture."""
    return {p.stem: p for p in ISO_CF.rglob("STC/*.json")}


def iso_prem(resp):
    out = {}

    def walk(o, path):
        for k, v in o.items():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                for i, x in enumerate(v):
                    walk(x, f"{path}/{k}[{i}]")
            elif isinstance(v, dict):
                walk(v, f"{path}/{k}[0]")
            elif k in FIELDS:
                out[f"{path}/{k}"] = v
    cp = resp["Body"]["CommercialProperty"]
    for i, x in enumerate(cp if isinstance(cp, list) else [cp]):
        walk(x, f"CommercialProperty[{i}]")
    return out


def our_prem(data):
    out = {}

    def walk(n, path):
        idx = {}
        for c in n.children:
            if c.tag.endswith("Table"):
                for r in c.children:
                    i = idx.get(r.tag, 0)
                    idx[r.tag] = i + 1
                    walk(r, f"{path}/{r.tag}[{i}]")
            elif c.children:
                i = idx.get(c.tag, 0)
                idx[c.tag] = i + 1
                walk(c, f"{path}/{c.tag}[{i}]")
            elif c.tag in FIELDS:
                out[f"{path}/{c.tag}"] = c.text
    for t in data.children:
        if t.tag == "CommercialPropertyTable":
            for i, r in enumerate(t.children):
                walk(r, f"CommercialProperty[{i}]")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--all", action="store_true", help="all 293 stored responses, not the 46-fixture sample")
    a = ap.parse_args()
    index = fixture_index()
    n = ok = values = 0
    totals_ok = totals = 0
    diffs = collections.Counter()
    worst = []
    import time
    t0 = time.monotonic()
    paths = [r for r in sorted(RES.glob("chunk13_fixture_*_response.json"))
             if a.all or r.name[len("chunk13_fixture_"):-len("_response.json")] in SAMPLE]
    for i, rpath in enumerate(paths, 1):
        stem = rpath.name[len("chunk13_fixture_"):-len("_response.json")]
        if i == 1 or i % 25 == 0 or i == len(paths):       # progress: long runs must show it (2026-09-28)
            m, s_ = divmod(int(time.monotonic() - t0), 60)
            print(f"[{i}/{len(paths)}  {m}m{s_:02d}s] {stem}", flush=True)
        fx = index.get(stem)
        if fx is None:
            continue
        d = json.loads(fx.read_text(encoding="utf-8-sig"))
        req = {"header": {}, "body": {"SchemeKeys": {"ProductName": d["SchemeKeys"]["ProductName"],
                                                     "EffectiveDateTime": "2026-09-17T00:00:00"},
                                      "CommercialProperty": d["CommercialProperty"]}}
        try:
            data, ip = cmp.rate(req)
        except InterpretError as exc:
            print(f"  {stem}: ENGINE RAISED {str(exc)[:90]}")
            worst.append(stem)
            continue
        resp = json.loads(rpath.read_text(encoding="utf-8"))
        iso, ours = iso_prem(resp), our_prem(data)
        n += 1
        values += len(iso)
        d_ = [(k, v, ours.get(k)) for k, v in iso.items() if not cmp.same(v, ours.get(k))]
        pol = "CommercialProperty[0]/ErcCalculatedTotalPremium"
        if pol in iso:
            totals += 1
            totals_ok += cmp.same(iso[pol], ours.get(pol))
        if not d_:
            ok += 1
        else:
            worst.append(stem)
            for k, v, o in d_:
                rec = k.rsplit("/", 2)[-2].split("[")[0].replace("CommercialProperty", "")
                diffs[(rec, k.rsplit("/", 1)[-1])] += 1
            if a.verbose or len(worst) <= 8:
                st = d["SchemeKeys"]["ProductName"].split()[-1]
                print(f"  {stem} ({st}): {len(d_)} differ, e.g. " +
                      "; ".join(f"{k[-70:]} ISO {v} ours {o}" for k, v, o in d_[:3]))
    print(f"\n{'ALL' if a.all else 'SAMPLE'}: {n} stored ISO responses re-rated; {values} premium values compared")
    print(f"  every premium equal to ISO: {ok} of {n}")
    print(f"  the policy total (ErcCalculatedTotalPremium) equal to ISO: {totals_ok} of {totals}")
    for (rec, f), c in diffs.most_common(15):
        print(f"    {c:4d}x  {rec} . {f}")
    sys.exit(0 if ok == n and n else 1)


if __name__ == "__main__":
    main()
