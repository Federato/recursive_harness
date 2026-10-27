"""Chunk 13, C13-19 / C13-20: the states that rewrite terrorism, engine against ISO.

C13-19  FL (older parent, own rules), NY (34 rewritten rules, no NBC or sub-limit rows),
        AK (its own Alaska exclusion forms).
C13-20  CT, MA, VA (premium rewrites), AZ (CP 09 01: the fire exception only for
        residential property under four units), CA, TX (CP 00 70 messages),
        IL (territory checks), DC, MD, and the 25% cap states CA/DC/IL/MD/NY/VA.

A state that rewrites a rule has no countrywide prediction to hold it to, so
here ISO is the reference: every form choice the attach map allows (C13-05) is
rated on the portable building (152_) in each state, on the engine and live,
and compared field for field -- every coverage's Pre/Post/Terrorism premium and
every roll-up total, the 25% caps included. Engine-only, it prints the grid.

    python scripts/cf/153_chunk13_c13-19-20_state_rewrites.py [--live]
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

from cf_engine.resolve import book_for
from gl_engine.interp.values import InterpretError

st4 = import_module("152_chunk13_rc4_states")
rc3, gc, r11, rp = st4.rc3, st4.gc, st4.r11, st4.rp
WILL, POST, COND = gc.WILL_EXPIRE, rc3.POST, rc3.COND

STATES = ["FL", "NY", "AK", "CT", "MA", "VA", "AZ", "CA", "TX", "IL", "DC", "MD"]
CERT = ["Yes", "No", "Yes, but Excludes Nuclear, Biological and Chemical Acts", "Yes, Subject to Sub-Limit"]
EXCL = ["Exclude", "Exclude Nuclear, Biological and Chemical Acts", "Cover Subject to Sub-Limit", "No Exclusion"]
GRID = ([("in effect", c[:22], dict(cert=c, sublimit=30000)) for c in CERT]
        + [("expiring", e[:22], dict(tria=WILL, exp="06/01/2027", cond=e, sublimit=30000)) for e in EXCL]
        + [("post-TRIA", e[:22], dict(tria=POST, post=e, sublimit=30000)) for e in EXCL])


def cases():
    for j in STATES:
        book = book_for(j, st4.ASOF)
        plan, _, _ = st4.territory_plan(book, j)
        terr = plan[0]["territory"] if plan else ""
        for group, label, kw in GRID:
            yield j, group, label, st4.state_sub(j, terr, **kw)
        if j == "AZ":
            s = st4.state_sub(j, terr, cert="No")
            (s["CommercialPropertyTable"]["CommercialProperty"][0]["CommercialPropertyLocationTable"]
             ["CommercialPropertyLocation"][0]["CommercialPropertyStructureTable"]["CommercialPropertyStructure"][0]
             ["UnderFourUnits"]) = "Yes"
            yield j, "in effect", "No + under four units", s


def engine_fields(j, sub):
    req = r11.payload(sub)
    for cp in req["body"]["CommercialProperty"]:
        cp["State"] = j
    req["body"]["SchemeKeys"]["ProductName"] = r11.PRODUCT.format(state=j)
    st, eff, ours = rp.replay(req, None)
    return req, ours


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    a = ap.parse_args()
    client = None
    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
    tally = collections.Counter()
    out = collections.defaultdict(list)
    for j, group, label, sub in cases():
        try:
            req, ours = engine_fields(j, sub)
        except InterpretError as exc:
            out[j].append(f"{group:9s} {label:24s} ENGINE RAISED {str(exc)[:70]}")
            tally["engine raised"] += 1
            continue
        b = [v for k, v in ours.items() if k.endswith("CommercialPropertyStructure[0]/TerrorismPremium")]
        roll = {k.split("/")[-2].split("[")[0].replace("CommercialProperty", "")[:14]: v
                for k, v in ours.items() if k.endswith("/Premium") and (rp.num(v) or 0) > 0}
        line = f"{group:9s} {label:24s} building {b[0] if b else None!s:>5s}  roll-up {roll}"
        if client is not None:
            try:
                resp = client.rate(req)
            except Exception as exc:                                  # RaaSError
                body = str(getattr(exc, "body", exc))
                m = re.search(r"Matrix: (\w+).*?Keys: ([^.]*)", body) or re.search(r'"Message":"([^"]{0,90})', body)
                out[j].append(line + f"   ISO REFUSES {m.group(0)[:90] if m else body[:90]}")
                tally["ISO refuses"] += 1
                continue
            (gc.OUT / f"chunk13_c1319_{j}_{group.replace(' ', '')}_{label[:10].replace(' ', '').replace(',', '')}_response.json"
             ).write_text(json.dumps(resp, indent=2), encoding="utf-8")
            iso = rp.iso_fields(resp)
            d = [(k, v, ours.get(k)) for k, v in iso.items() if rp.num(v) != rp.num(ours.get(k))
                 and not (rp.num(v) in (None, 0.0) and rp.num(ours.get(k)) in (None, 0.0))]
            tally["agree" if not d else "DIFFER"] += 1
            line += "   ISO AGREES" if not d else "   ISO DIFFERS: " + "; ".join(
                f"{k[-45:]} ISO {v} ours {o}" for k, v, o in d[:3])
        out[j].append(line)
    for j in STATES:
        print(f"\n{j}")
        for ln in out[j]:
            print("  " + ln)
    print(f"\n{dict(tally)}")
    sys.exit(1 if tally["DIFFER"] or tally["engine raised"] else 0)


if __name__ == "__main__":
    main()
