#!/usr/bin/env python3
"""Chunk 28 C28-15 (sets B and E): the silent-zero table. Each input that prices a policy at $0 without a word, on ours
and at ISO, classed. No engine change.

The inputs (CF-START-HERE "Input validation", chunks 1-3) plus NY's missing Group II symbol (chunk 27 C27-09), each one
input moved on a policy that otherwise rates, beside a control:
  Z-AZ    Arizona without its location's BasicGroupIReductionCredit          (control C-AZ: credit 1.0)
  Z-CT    an unrecognised ConstructionType ("Brick")                        (control C-OR: chunk 2's golden policy)
  Z-CTR   a construction type spelled as a rating-type name ("Masonry Non-Combustible")
  Z-BCEG  no BCEG
  Z-RT2   no RatingTypeBasicGroupII
  Z-G2T   no BasicGroupIIRatingTerr
  Z-DB    a blank Deductible on Broad                                       (control C-B: chunk 3 Broad)
  Z-DS    a blank Deductible on Special                                     (control C-S: chunk 3 Special)
  Z-NY    New York without BasicGroupIISymbol                               (control C-NY: symbol "B")
Each is classed: "ISO also $0" (a validation gap only: set B), "ISO refuses" (set A: ours should refuse too since C28-05),
or "diverges" (ISO prices what ours zeroes: a rating difference, not validation). Predicted before the run (2026-10-05):
most are "ISO also $0"; Z-CT and Z-CTR "ISO refuses" (ConstructionTypeToUse has no row: OI-103's first case).

    python scripts/cf/254_chunk28_c28-15_silent_zeros.py [--live] [--cases Z-AZ,C-AZ]
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

cmp = import_module("154_chunk13_rc5_fields_messages")
c23 = import_module("221_chunk23_rc3")
rep, TAGGED, lvl = c23.rep, c23.TAGGED, c23.lvl
g2 = import_module("09_chunk2_golden_case")
g3 = import_module("15_chunk3_golden_case")
m207 = import_module("207_chunk21_rc1")
P = m207.P
OUT = ROOT / "results" / "cf-raas"


def at(sub, k):
    loc = (sub["CommercialPropertyTable"]["CommercialProperty"][0]["CommercialPropertyLocationTable"]
           ["CommercialPropertyLocation"][0])
    if k == "Location":
        return loc
    return loc["CommercialPropertyStructureTable"]["CommercialPropertyStructure"][0]


def edit(build, rec, field, value=None):
    """`build()` with `rec.field` removed (value None) or set."""
    def b():
        sub = build()
        d = at(sub, rec)
        if value is None:
            d.pop(field, None)
        else:
            d[field] = value
        return sub
    return b


def portable(j):
    return lambda: m207.portable(j)


AZ = edit(portable("AZ"), "Location", "BasicGroupIReductionCredit", 1.0)    # a number: ISO types it Decimal
NY = edit(portable("NY"), "Structure", "BasicGroupIISymbol", "B")
CASES = {
    "C-AZ": ("AZ", "Arizona, reduction credit 1.0 (control)", AZ),
    "Z-AZ": ("AZ", "Arizona without BasicGroupIReductionCredit", edit(AZ, "Location", "BasicGroupIReductionCredit")),
    "C-OR": ("OR", "chunk 2's golden policy (control)", g2.submission),
    "Z-CT": ("OR", "ConstructionType 'Brick' (not a filed value)", edit(g2.submission, "Structure", "ConstructionType", "Brick")),
    "Z-CTR": ("OR", "ConstructionType 'Masonry Non-Combustible' (a rating-type name)",
              edit(g2.submission, "Structure", "ConstructionType", "Masonry Non-Combustible")),
    "Z-BCEG": ("OR", "no BCEG", edit(g2.submission, "Structure", "BCEG")),
    "Z-RT2": ("OR", "no RatingTypeBasicGroupII", edit(g2.submission, "Structure", "RatingTypeBasicGroupII")),
    "Z-G2T": ("OR", "no BasicGroupIIRatingTerr", edit(g2.submission, "Location", "BasicGroupIIRatingTerr")),
    "C-B": ("OR", "chunk 3 Broad (control)", lambda: g3.submission("Broad")),
    "Z-DB": ("OR", "chunk 3 Broad, blank Deductible", edit(lambda: g3.submission("Broad"), "Structure", "Deductible")),
    "C-S": ("OR", "chunk 3 Special (control)", lambda: g3.submission("Special")),
    "Z-DS": ("OR", "chunk 3 Special, blank Deductible", edit(lambda: g3.submission("Special"), "Structure", "Deductible")),
    "C-NY": ("NY", "New York, BasicGroupIISymbol 'B' (control)", NY),
    "Z-NY": ("NY", "New York without BasicGroupIISymbol", edit(NY, "Structure", "BasicGroupIISymbol")),
}


def building_premiums(prem):
    """The building's coverage premiums and the policy total, from a {path: premium} map."""
    out = {}
    for k, v in prem.items():
        if re.search(r"CommercialPropertyStructure\[0\]/CommercialPropertyStructureBuilding\w+Coverage\[0\]/Premium$", k):
            out[k.split("/")[-2].replace("CommercialPropertyStructure", "").replace("[0]", "")] = v
        elif re.fullmatch(r"CommercialProperty\[0\]/ErcCalculatedTotalPremium", k):
            out["TOTAL"] = v
    return out


def show(d):
    return ", ".join(f"{k} {v}" for k, v in sorted(d.items()))


def ours(req):
    TAGGED.clear()
    try:
        data, ip = rep.cmp.rate(req)
    except Exception as exc:                          # noqa: BLE001
        m = re.search(r"NO row in '(\w+)'", str(exc))
        return f"REFUSES {m.group(1)}" if m else f"raises {type(exc).__name__}", {}, []
    return "rates", building_premiums(rep.our_prem(data)), sorted({x for _, x in TAGGED})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--cases")
    a = ap.parse_args()
    cs = {k: v for k, v in CASES.items() if not a.cases or k in a.cases.split(",")}
    client = None
    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
    rows = []
    for cid, (j, label, build) in cs.items():
        req = cmp.state_req(j, build(), localize=False)      # the silent zeros are the subject: no localizing
        o_state, o_prem, o_msgs = ours(req)
        line = f"{cid:7s} {j} {label}\n    ours: {o_state}; {show(o_prem)}"
        iso_state, i_prem, i_msgs = None, {}, []
        if client:
            (OUT / f"chunk28_c28-15_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
            try:
                resp = client.rate(req)
                (OUT / f"chunk28_c28-15_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
                iso_state, i_prem = "rates", building_premiums(rep.iso_prem(resp))
                i_msgs = sorted({x for _, x in c23.iso_tagged(resp)})
            except raas_mod.RaaSError as exc:
                (OUT / f"chunk28_c28-15_{cid}_refusal.json").write_text(str(exc.body), encoding="utf-8")
                m = re.search(r"Matrix: (\w+)", str(exc.body))
                iso_state = f"REFUSES {m.group(1)}" if m else f"refuses: {str(exc.body)[:120]}"
            line += f"\n    ISO:  {iso_state}; {show(i_prem)}"
            new_o = [x for x in o_msgs if x not in i_msgs]
            new_i = [x for x in i_msgs if x not in o_msgs]
            if new_o or new_i:
                line += f"\n    messages: ours only {new_o[:3]}; ISO only {new_i[:3]}"
        print(line)
        rows.append((cid, o_state, o_prem, iso_state, i_prem))
    control = {"Z-AZ": "C-AZ", "Z-DB": "C-B", "Z-DS": "C-S", "Z-NY": "C-NY"}
    ours_of = {cid: o_prem for cid, o_state, o_prem, *_ in rows}
    if client:
        print("\nClass (a Z case against its control; a coverage counts as zeroed only if its control prices it):")
        for cid, o_state, o_prem, iso_state, i_prem in rows:
            if not cid.startswith("Z-"):
                continue
            base = ours_of.get(control.get(cid, "C-OR"), {})
            if iso_state and iso_state.startswith("REFUSES"):
                cls = "ISO refuses" + (" (ours too)" if o_state.startswith("REFUSES") else " (OURS RATES: set A gap)")
            else:
                zero_o = sorted(k for k, v in o_prem.items() if k != "TOTAL" and rep.cmp.same(v, 0)
                                and base.get(k) is not None and not rep.cmp.same(base[k], 0))
                same = all(rep.cmp.same(i_prem.get(k), v) for k, v in o_prem.items())
                cls = (f"ISO also $0 on {zero_o}" if same and zero_o else
                       "equal, no zero" if same else "DIVERGES: " + show({k: (o_prem.get(k), i_prem.get(k))
                                                                          for k in set(o_prem) | set(i_prem)
                                                                          if not rep.cmp.same(o_prem.get(k), i_prem.get(k))}))
            print(f"  {cid:7s} {cls}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
