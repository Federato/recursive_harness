#!/usr/bin/env python3
"""Chunk 15, RC-5 (C15-19): what the manual-premium endorsements feed downstream.

Predicted from the rules before running (2026-09-25):
  TOTAL      each record's Premium enters the policy total like any other (chunk 14:
             CalculateTotalPremium sums every record with PremiumIndicator 1). So the
             total moves by exactly the endorsements' premiums:
               X1b - X1a (RC-3: Cannabis on five coverages) = 1013 + 959 + 1066 + 959 + 1066 = 5,063
               G10 - X1a (RC-2 all 23 vs the same policy bare)  = 4 x 1013 + 10 x 959 + 7 x 1066
                                                                  + 2 x 1065 = 23,234
  TERRORISM  no terrorism rule in the countrywide edition reads any chunk 15 record, and
             terrorism is priced from each coverage's own rates and limits (chunk 13), so
             adding all 23 records changes no terrorism premium:
               T0  RC-2's policy + terrorism in effect (Multnomah), no chunk 15 record
               T1  the same + all 23 records: every terrorism field identical to T0, and
                   the total exactly 23,234 higher
  CORRECTION (2026-09-25, after the first run): G10 - X1a was 23,210 at ISO and ours, not
             23,234, and T1 - T0 23,218. Not the endorsements: Valuable Papers needs a Contents
             row of its own (C15-05), copied from the first, and that row (a) raises the
             building's total insured value, so the first Contents row's deductible band moves
             and its Group I / II premiums fall 197 -> 176 and 21 -> 18 (-24; chunk 1's rule),
             and (b) is a $100,000 Contents coverage with its own terrorism charge, $8 (policy
             terrorism 34 -> 42): 23,234 - 24 = 23,210, and + 8 = 23,218, both equal at ISO.
             Those were explained AFTER the answer, so T2 is the clean test, predicted first:
               T2  all 22 records except Valuable Papers (no second Contents row): total exactly
                   23,234 - 1,013 = 22,221 above T0; policy terrorism charge unchanged at $34.
  STAT CODES the 29 files carry no statistical-code rule of their own. Every stat field
             ISO returns on a chunk 15 record is compared with ours, strictly as text
             (161_'s rule), on every stored chunk 15 response (RC-2, RC-3, RC-4).

    python scripts/cf/172_chunk15_c15-19_downstream.py [--live]

The TOTAL and STAT parts are offline (stored responses); --live sends T0 and T1.
Exits 1 on any disagreement.
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
sys.path.insert(0, str(ROOT / "scripts" / "cf"))
sys.path.insert(0, str(ROOT / "scripts"))

gc = import_module("149_chunk13_golden_case")
rep = import_module("157_chunk14_c14-02_total_replay")
cmp = import_module("154_chunk13_rc5_fields_messages")
tot = import_module("159_chunk14_rc2_total")
rc1 = import_module("168_chunk15_rc1")
rc2 = import_module("169_chunk15_rc2")
r11 = gc.r11
P = "CommercialProperty"
RECS = {P + r for r in rc1.CW_RECORDS + rc1.VA_RECORDS}
STAT = re.compile(r"StatCode|StatAmount|^Stat[A-Z]|ForStat|ToUseStat")
TERR = re.compile(r"Terror|TRIA|Terrsm|CertfdActs|Disclosure")
TOTAL = "CommercialProperty[0]/ErcCalculatedTotalPremium"
OUT = gc.OUT


import _regress  # noqa: E402  regression-mode sampling: 104_ sets CF_REGRESSION_SAMPLE; gates run in full

def blank(v):
    return v is None or (isinstance(v, str) and v.strip() == "")


def same(iso, ours):
    """161_'s strict rule: text is text ("07" is not "7"), a JSON number is a number."""
    if blank(iso) or blank(ours):
        return blank(iso) and blank(ours)
    if isinstance(iso, (int, float)) and not isinstance(iso, bool):
        try:
            return float(ours) == float(iso)
        except (TypeError, ValueError):
            return False
    return str(iso) == str(ours)


def iso_fields(resp, want_rec, want_field):
    out = {}

    def walk(o, path, rec):
        for k, v in o.items():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                for i, x in enumerate(v):
                    walk(x, f"{path}/{k}[{i}]", k)
            elif isinstance(v, dict):
                walk(v, f"{path}/{k}[0]", k)
            elif want_rec(rec) and want_field(k):
                out[f"{path}/{k}"] = v
    cp = resp["Body"]["CommercialProperty"]
    for i, x in enumerate(cp if isinstance(cp, list) else [cp]):
        walk(x, f"CommercialProperty[{i}]", P)
    return out


def our_fields(data, want_rec, want_field):
    out = {}

    def walk(n, path, rec):
        idx = {}
        for c in n.children:
            if c.tag.endswith("Table"):
                for r in c.children:
                    i = idx.get(r.tag, 0)
                    idx[r.tag] = i + 1
                    walk(r, f"{path}/{r.tag}[{i}]", r.tag)
            elif c.children:
                i = idx.get(c.tag, 0)
                idx[c.tag] = i + 1
                walk(c, f"{path}/{c.tag}[{i}]", c.tag)
            elif want_rec(rec) and want_field(c.tag):
                out[f"{path}/{c.tag}"] = c.text
    for t in data.children:
        if t.tag == "CommercialPropertyTable":
            for i, r in enumerate(t.children):
                walk(r, f"CommercialProperty[{i}]", P)
    return out


def total_of(resp):
    return float(rep.iso_prem(resp)[TOTAL])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    a = ap.parse_args()
    fails = []

    print("TOTAL (stored ISO responses)")
    x1a = json.loads((OUT / "chunk15_rc3_X1a_response.json").read_text(encoding="utf-8"))
    x1b = json.loads((OUT / "chunk15_rc3_X1b_response.json").read_text(encoding="utf-8"))
    g10 = json.loads((OUT / "chunk15_rc2_G10_response.json").read_text(encoding="utf-8"))
    for label, hi, want in (("X1b - X1a (Cannabis on five coverages)", x1b, 5063),
                            ("G10 - X1a (all 23, plus VP's second Contents row: -24, see CORRECTION)", g10, 23210)):
        d = total_of(hi) - total_of(x1a)
        ok = d == want
        print(f"  {label}: ISO {total_of(hi):,.0f} - {total_of(x1a):,.0f} = {d:,.0f}; predicted {want:,}  "
              f"{'ok' if ok else 'DIFFERS'}")
        if not ok:
            fails.append(label)

    print("\nSTAT CODES on chunk 15 records (stored responses, strict)")
    n = values = 0
    fields = collections.Counter()
    for rpath in _regress.sample(sorted(OUT.glob("chunk15_rc[234]_*_response.json"))):
        tag = rpath.name[len("chunk15_"):-len("_response.json")]
        if tag.endswith("VA-OLD"):
            continue                        # the 2020 edition cannot be rated whole (OI-114)
        req = json.loads((OUT / f"chunk15_{tag}_request.json").read_text(encoding="utf-8"))
        resp = json.loads(rpath.read_text(encoding="utf-8"))
        data, ip = cmp.rate(req)
        want_rec = lambda r: r in RECS
        iso, ours = iso_fields(resp, want_rec, STAT.search), our_fields(data, want_rec, STAT.search)
        n += 1
        values += len(iso)
        fields.update(k.rsplit("/", 1)[-1] for k in iso)
        bad = [(k, v, ours.get(k)) for k, v in iso.items() if not same(v, ours.get(k))]
        extra = [k for k, v in ours.items() if k not in iso and not blank(v)]
        if bad or extra:
            fails.append(f"stat {tag}")
            print(f"  {tag}: {len(bad)} differ, {len(extra)} ours-only"
                  + "".join(f"\n      {k[-80:]} ISO {v!r} ours {o!r}" for k, v, o in bad[:4])
                  + "".join(f"\n      ours only {k[-80:]}" for k in extra[:3]))
    print(f"  {n} stored chunk 15 responses re-rated; {values} stat values on chunk 15 records "
          f"({dict(fields) or 'none'}); {'all equal' if not any(f.startswith('stat') for f in fails) else 'DIFFERENCES above'}")

    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
        print("\nTERRORISM (ISO live): T0 without, T1 with all 23 records")
        resp = {}
        for cid, recs in (("T0", []), ("T1", list(rc2.ALL)), ("T2", [r for r in rc2.ALL if r != rc2.VP])):
            sub = tot.terror(rc2.build(recs))
            req = r11.payload(sub)
            (OUT / f"chunk15_c15-19_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
            try:
                resp[cid] = client.rate(req)
            except raas_mod.RaaSError as exc:
                print(f"  {cid} ISO REFUSES {str(exc.body)[:160]}")
                fails.append(f"{cid} live")
                continue
            (OUT / f"chunk15_c15-19_{cid}_response.json").write_text(json.dumps(resp[cid], indent=2), encoding="utf-8")
            data, ip = cmp.rate(req)
            ip_, op_ = rep.iso_prem(resp[cid]), rep.our_prem(data)
            d = [(k, v, op_.get(k)) for k, v in ip_.items() if not rep.cmp.same(v, op_.get(k))]
            is_, os_ = iso_fields(resp[cid], lambda r: True, TERR.search), our_fields(data, lambda r: True, TERR.search)
            ds = [(k, v, os_.get(k)) for k, v in is_.items() if not same(v, os_.get(k))]
            mi, mo = cmp.iso_messages(resp[cid]), set(ip.messages)
            ok = not d and not ds and mi == mo
            print(f"  {cid}: {'AGREE' if ok else 'DIFFER'} on {len(ip_)} premiums, {len(is_)} terrorism fields, "
                  f"messages {'equal' if mi == mo else 'DIFFER'}; ISO total {rep.iso_prem(resp[cid])[TOTAL]}"
                  + "".join(f"\n      {k[-80:]} ISO {v!r} ours {o!r}" for k, v, o in (d + ds)[:5]))
            if not ok:
                fails.append(f"{cid} live")
        if len(resp) == 3:
            disc = lambda r: next(float(v) for k, v in rep.iso_prem(r).items()
                                  if "ZzDisclosurePursuantToTerrorismRiskInsAct2002" in k and k.endswith("/Premium"))
            t0 = iso_fields(resp["T0"], lambda r: r not in RECS, TERR.search)
            for cid, want_total, want_disc in (("T1", 23218, 42), ("T2", 22221, 34)):
                t = iso_fields(resp[cid], lambda r: r not in RECS, TERR.search)
                moved = [(k, v, t.get(k)) for k, v in t0.items() if not same(v, t.get(k))]
                on_c15 = [k for k, v in iso_fields(resp[cid], lambda r: r in RECS, TERR.search).items() if not blank(v)]
                d = total_of(resp[cid]) - total_of(resp["T0"])
                ok = not moved and not on_c15 and d == want_total and disc(resp[cid]) == want_disc
                print(f"  {cid}: existing terrorism fields {len(t0) - len(moved)} of {len(t0)} identical to T0; "
                      f"terrorism fields on chunk 15 records {len(on_c15)}; policy terrorism {disc(resp['T0']):.0f} -> "
                      f"{disc(resp[cid]):.0f} (predicted {want_disc}); total - T0 {d:,.0f} (predicted {want_total:,})  "
                      f"{'ok' if ok else 'DIFFERS'}"
                      + "".join(f"\n      {k[-80:]} T0 {v!r} {cid} {w!r}" for k, v, w in moved[:5]))
                if not ok:
                    fails.append(f"{cid} downstream")
    print(f"\nC15-19: {'ALL AGREE' if not fails else 'FAILED: ' + ', '.join(fails)}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
