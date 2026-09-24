"""Chunk 14, RC-5 (C14-18, gates 2, 3, 8): the policy modifiers in all 46 states.

The policy TOTAL is already proven in all 46 (157_ --all: 293 stored ISO responses,
every state, total equal on 293 of 293). This sweeps the MODIFIERS, each state on
its own rows and rules, on chunk 2's building made portable (152_'s way).

What each state does, from a scan of all 46 in-force packages (C14-10, 2026-09-24):
  IRPM categories   CW six, except NY (its own twelve), MO (CW six + ReductionInExpensesPct,
                    whose lookup has no blank guard -- sent as "0%"), NE (IRPM off)
  IRPM limits       CW +/-25, except NY +/-15 and MO credit -35
  IRPM message      CW "25%", except GA ("15%", cap still 25), NY ("15%" + the
                    units-mixed "all credits 25%"), MO (its own, against its own
                    limits), VA and NE (none)
  SPP factors       CW 0.98 / 0.98, except KS, NY, VT: the Standard Property Policy is
                    switched off (factor, form and structure setters all emptied), so
                    an SPP policy prices exactly like a normal one there
So, per state, derived before running:
  I  IRPM +30 (every category at its domain limit; NY's twelve likewise)  -> factor 1 + min(30, max)/100 (1.25; NY 1.15; NE 1.0)
                                         messages as above; TotalRatingModificationStatCode
                                         = the factor in hundredths ("125", "115", "100")
  S  PolicyType "Standard Property Policy" -> the structure's StdPropPolGroupIFactor 0.98
                                         (KS/NY/VT: none, and the premium equals the plain
                                         policy's)
Premiums are not hand-derived per state (46 chains; chunks 1-2 and 13's sweep own
those); every Premium, every stat field (strictly) and every message goes to ISO.

    python scripts/cf/164_chunk14_c14-18_all_states.py [--live] [--states NY,MO]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))
sys.path.insert(0, str(ROOT / "scripts"))

from gl_engine.interp.values import InterpretError

m3 = import_module("160_chunk14_rc3_modifiers")
sc = import_module("161_chunk14_c14-16_statcode_replay")
gc, rep, r11 = m3.gc, m3.rep, m3.r11
POL, STRUCT, TOTAL, B1 = m3.POL, m3.STRUCT, m3.TOTAL, m3.B1
STATES = """AL AK AZ AR CA CO CT DE DC FL GA IL IN IA KS KY ME MD MA MI MN MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WV WI WY""".split()     # the 46 (PR excluded)
NO_SPP = {"KS", "NY", "VT"}
SPP_F = f"{STRUCT}/StdPropPolGroupIFactor"
CODE = f"{POL}/TotalRatingModificationStatCode"


def irpm_expect(j):
    if j == "NE":
        return 1.0, set()
    f = 1.15 if j == "NY" else 1.25
    msgs = {"NY": {m3.M15, m3.ALL25}, "GA": {m3.M15}, "MO": {m3.MO_MSG}, "VA": set()}.get(j, {m3.CW_MSG})
    return f, msgs


def build_irpm(j):
    if j == "NY":
        return m3.irpm(m3.NY30, juris=j, cats=m3.NY_CATS)()
    if j == "MO":
        return m3.irpm(m3.P30 + ["0%"], juris=j, cats=m3.MO_CATS)()
    return m3.irpm(m3.P30, juris=j)()


def build_spp(j):
    sub = m3.portable(j)
    m3.pol(sub)["PolicyType"] = "Standard Property Policy"
    return sub


#: Location fields four states ADD and ISO requires (139_'s state-field sweep; the first
#: live run, 2026-09-24, refused all 8 of their cases on exactly these lookups):
#: CO / IN a county for GeographicWindHazardLevel, OK "Entire State", SC an EQTerr
#: (BCEGEQFactor prices every SC building) and a county.
STATE_LOC = {"CO": {"GeographicWindHazardLevelTerritory": "Baca"},
             "IN": {"GeographicWindHazardLevelTerritory": "Benton"},
             "OK": {"GeographicWindHazardLevelTerritory": "Entire State"},
             "SC": {"GeographicWindHazardLevelTerritory": "Beaufort", "EQTerr": "1"}}


def windhail(sub):
    loc = m3.t2.locs(sub)[0]
    loc.update(STATE_LOC.get(m3.pol(sub).get("State", "OR"), {}))
    for st in m3.t2.structs(loc):
        st.setdefault("WindstormOrHailDeductible", "1,000")    # ISO refuses it blank (C13-08)
    return sub


def cases(states):
    for j in states:
        f, msgs = irpm_expect(j)
        yield j, "I", windhail(build_irpm(j)), {m3.IRPMF: f, CODE: str(round(f * 100))}, msgs
        yield j, "S", windhail(build_spp(j)), {SPP_F: None if j in NO_SPP else 0.98}, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--states")
    a = ap.parse_args()
    states = a.states.split(",") if a.states else STATES
    fails, n = [], 0
    for j, kind, sub, want, msgs in cases(states):
        n += 1
        try:
            data, ip = gc.run(sub, juris=j)
        except InterpretError as exc:
            print(f"  {j} {kind}: RAISED {str(exc)[:100]}")
            fails.append((j, kind))
            continue
        bad = []
        for k, v in want.items():
            got = gc.read(k, data)
            if v is None:
                if got not in (None, ""):
                    bad.append((k, got, v))
            elif isinstance(v, str):
                if (got or "") != v:
                    bad.append((k, got, v))
            elif not gc.num_eq(got if got is not None else 0, v):
                bad.append((k, got, v))
        if kind == "S" and j in NO_SPP:
            plain, _ = gc.run(windhail(m3.portable(j)), juris=j)
            if gc.read(TOTAL, plain) != gc.read(TOTAL, data):
                bad.append(("total vs the plain policy", gc.read(TOTAL, data), gc.read(TOTAL, plain)))
        if msgs is not None and m3.irpm_msgs(ip.messages) != msgs:
            bad.append(("IRPM messages", sorted(m3.irpm_msgs(ip.messages)), sorted(msgs)))
        if bad:
            fails.append((j, kind))
            print(f"  {j} {kind}: " + "; ".join(f"{str(k).rsplit('/', 1)[-1]} got {g} want {v}" for k, g, v in bad))
    print(f"\nengine: {n - len(fails)} of {n} state cases as derived ({len(states)} states x IRPM, SPP)")
    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
        agree, refused = 0, []
        print("\nISO live at 2026-09-17 (every Premium, every stat field strictly, every message):")
        for j, kind, sub, want, msgs in cases(states):
            req = r11.payload(sub)
            for cp in req["body"]["CommercialProperty"]:
                cp["State"] = j
            req["body"]["SchemeKeys"]["ProductName"] = r11.PRODUCT.format(state=j)
            try:
                resp = client.rate(req)
            except raas_mod.RaaSError as exc:
                mm = re.search(r"Matrix: (\w+).*?Keys: ([^.]*)", str(exc.body)) or re.search(r'"Message":"([^"]{0,140})', str(exc.body))
                print(f"  {j} {kind}  ISO REFUSES {mm.group(0)[:140] if mm else str(exc.body)[:140]}")
                refused.append((j, kind))
                continue
            (gc.OUT / f"chunk14_states_{j}_{kind}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
            data, ip = rep.cmp.rate(req)
            d = [(k, v, o) for k, v, o in ((k, v, rep.our_prem(data).get(k)) for k, v in rep.iso_prem(resp).items())
                 if not rep.cmp.same(v, o)]
            ours_s = rep.cmp.ours_all(data)
            d += [(k, v, ours_s.get(k)) for k, v in rep.cmp.iso_all(resp).items() if not sc.same(v, ours_s.get(k))]
            mi, mo = rep.cmp.iso_messages(resp), set(ip.messages)
            if mi != mo:
                d.append(("messages", sorted(mi - mo), sorted(mo - mi)))
            agree += not d
            tot = rep.iso_prem(resp).get("CommercialProperty[0]/ErcCalculatedTotalPremium")
            if d:
                print(f"  {j} {kind}  DIFFER  ISO total {tot}"
                      + "".join(f"\n        {str(k)[-80:]} ISO {v!r} ours {o!r}" for k, v, o in d[:5]))
        print(f"\n  live: {agree} of {n} agree field for field, stat codes and messages included; "
              f"{len(refused)} refused {refused if refused else ''}")
        if agree + len(refused) != n or refused:
            fails.append("live")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
