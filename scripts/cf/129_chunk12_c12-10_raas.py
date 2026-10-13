#!/usr/bin/env python3
"""Chunk 12, C12-10 -- Debris Removal against ISO, live, and its messages.

Sent at EffectiveDateTime 2026-09-17 (OI-105). Two kinds of case:

  Engine-built  the golden case (127) and the gate cases from 128 whose
                behaviour is ours to predict but ISO's to confirm: the limit
                at the minimum (Z1), below it with a negative premium (Z4),
                a 'No Coverage' building still charging (Z5), the Special
                cell with and without a theft exclusion, and a vandalism
                exclusion.
  ISO fixtures  the 3 STC payloads that carry Debris Removal (AK, WY, WY),
                re-dated to 2026-09-17. They exercise the Broad, Special and
                Earthquake cells the Oregon golden case leaves at $0.

Each prints ours and ISO's premium per cell, and whether they agree. Requests
and responses are saved to results/cf-raas/chunk12_dr_*.json.

    python scripts/cf/129_chunk12_c12-10_raas.py [--only C0,Z4] [--dry-run]
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from importlib import import_module

import raas as raas_mod                                        # noqa: E402
from cf_engine.config import NULL_ARITHMETIC, ROUNDING         # noqa: E402
from cf_engine.resolve import book_for                         # noqa: E402
from gl_engine.interp.interpreter import Interpreter           # noqa: E402
from gl_engine.interp.tree import Node, read                   # noqa: E402
from gl_engine.interp.values import InterpretError             # noqa: E402

g = import_module("127_chunk12_golden_case")
gates = import_module("128_chunk12_debris_removal_gates")
r11 = import_module("118_chunk11_c11-23_raas")
ops = import_module("125_chunk12_c12-03_operand_types")

EFFECTIVE = r11.EFFECTIVE
PFX = g.PFX
FORMS = g.FORMS
OUT = Path(__file__).resolve().parents[2] / "results" / "cf-raas"


def engine_cases():
    def with_cp(sub, **kv):
        sub["CommercialPropertyTable"]["CommercialProperty"][0].update(kv)
        return sub

    def excl(sub, table):
        gates.structure(sub)[table + "Table"] = {table: [{}]}
        return sub

    special = lambda: g.submission(structure={"CauseOfLoss": "Special"})
    return [
        ("C0", "golden case: OR, DR limit 60,000 (ours $49 + $6)", g.submission()),
        ("Z1", "limit = 25,000 (ours: on, $0, CP 04 15 error)", g.submission(limit=25000)),
        ("Z4", "limit 10,000 (ours: -$21 / -$3 behind CP 04 15)", g.submission(limit=10000)),
        ("Z5", "building CovType 'No Coverage' (ours: DR still $42 + $5)",
         g.submission(structure={"CovType": "No Coverage"})),
        ("S1", "Special building (ours: DR Special $4)", special()),
        ("S2", "Special + theft exclusion (ours: bldg $54 -> $47, DR Special stays $4)",
         excl(special(), "CommercialPropertyTheftExclusion")),
        ("V1", "vandalism exclusion (ours: DR BGI $49 -> $47)",
         excl(with_cp(g.submission(), PolicyType="Commercial Property Policy"),
              "CommercialPropertyVandalismExclusion")),
    ]


def fixture_cases():
    out = []
    for p in sorted(ops.ISO_CF.rglob("STC/*.json")):
        t = p.read_text(encoding="utf-8-sig", errors="replace")
        if "DebrisRemoval" in t:
            d = json.loads(t)
            st = d["SchemeKeys"]["ProductName"].split()[-1]
            out.append((f"F-{p.stem[-5:]}", f"ISO fixture {p.name} ({st})", (st, d)))
            if '"EQTerr": "22"' in t or '"EQTerr":"22"' in t:
                # EQTerr 22 has no EarthquakeDeductibleTier row at 2026-09-17 in AK or
                # WY (both file 1-4). ISO refuses; ours tolerates. Re-sent at a filed
                # territory so the Debris Removal cells can still be compared.
                d2 = json.loads(t.replace('"EQTerr": "22"', '"EQTerr": "1"')
                                .replace('"EQTerr":"22"', '"EQTerr":"1"'))
                out.append((f"F-{p.stem[-5:]}t1", f"same fixture, EQTerr 22 -> 1 ({st})", (st, d2)))
    return out


def dr_cells_from_tree(data):
    """{record#/form: Premium} from our tree, every DR record on every structure."""
    got = {}
    stack = [data]
    n = 0
    while stack:
        node = stack.pop()
        for c in node.children:
            if c.tag == PFX:
                n += 1
                for f in FORMS:
                    cell = next((x for x in c.children if x.tag == f"{PFX}{f}Coverage"), None)
                    prem = next((x.text for x in cell.children if x.tag == "Premium"), None) if cell else None
                    got[f"{n}/{f}"] = prem
            stack.append(c)
    return got


def dr_cells_from_iso(resp):
    got = {}
    n = 0
    for recs in r11.find(resp, PFX):
        for rec in (recs if isinstance(recs, list) else [recs]):
            if not isinstance(rec, dict):
                continue
            n += 1
            for f in FORMS:
                cell = rec.get(f"{PFX}{f}Coverage")
                cell = cell[0] if isinstance(cell, list) and cell else cell
                got[f"{n}/{f}"] = cell.get("Premium") if isinstance(cell, dict) else None
    return got


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def show(d):
    nz = {k: v for k, v in d.items() if num(v) != 0}
    return ", ".join(f"{k}={num(v):g}" for k, v in nz.items()) or "all $0"


def prepare(case):
    """(ours: dict | str, request payload)."""
    cid, label, sub = case
    if cid.startswith("F-"):
        st, d = sub
        esub = {"EffDate": "09/17/2026", "ExpDate": "09/17/2027"}
        esub.update(ops.to_engine({"CommercialProperty": d["CommercialProperty"]}))
        req = {"header": {"quoteback": "", "authorization": {}},
               "body": {"SchemeKeys": {"ProductName": d["SchemeKeys"]["ProductName"],
                                       "EffectiveDateTime": EFFECTIVE},
                        "CommercialProperty": d["CommercialProperty"]}}
        juris = st
    else:
        esub = r11.at_date(sub)
        req = r11.payload(esub)
        juris = "OR"
    try:
        ip = Interpreter(book_for(juris, g.ASOF), rounding=ROUNDING, null_arithmetic=NULL_ARITHMETIC)
        data = Node.from_dict(f"MasterCF{juris}", esub)
        ip.run(data)
        ours = dr_cells_from_tree(data)
        ours_msgs = list(ip.messages)
    except InterpretError as exc:
        ours, ours_msgs = f"REFUSED {str(exc)[:100]}", []
    return ours, ours_msgs, req


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    only = {x.strip() for x in a.only.split(",") if x.strip()}
    todo = [c for c in engine_cases() + fixture_cases() if not only or c[0] in only]

    if a.dry_run:
        print(json.dumps(prepare(todo[0])[2], indent=2)[:4000])
        return 0
    try:
        client = raas_mod.RaaS()
    except raas_mod.RaaSError as exc:
        print(f"CANNOT CALL: {exc}")
        return 2
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"Chunk 12 C12-10 -- Debris Removal, live ISO at {EFFECTIVE}\n")
    agree = 0
    for case in todo:
        cid, label = case[0], case[1]
        ours, ours_msgs, req = prepare(case)
        (OUT / f"chunk12_dr_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
        try:
            resp = client.rate(req)
            (OUT / f"chunk12_dr_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
            iso = dr_cells_from_iso(resp)
            msgs = sorted({e.get("Description") for errs in r11.find(resp, "RatingMessages")
                           for kind in (errs.values() if isinstance(errs, dict) else [])
                           for e in (kind if isinstance(kind, list) else [])
                           if isinstance(e, dict) and e.get("Description")})
            iso_s = show(iso) if iso else "NO DR RECORD RETURNED"
            same = isinstance(ours, dict) and bool(iso) and all(
                num(iso.get(k)) == num(ours.get(k)) for k in set(iso) | set(ours))
        except raas_mod.RaaSError as exc:
            (OUT / f"chunk12_dr_{cid}_refusal.json").write_text(str(exc.body), encoding="utf-8")
            iso_s, msgs, same = f"ISO REFUSED status={exc.status}: {str(exc.body)[:200]}", [], False
        agree += same
        print(f"  {cid:8s} {label}")
        print(f"       ours : {show(ours) if isinstance(ours, dict) else ours}")
        print(f"       ISO  : {iso_s}")
        same_msgs = sorted(set(ours_msgs)) == msgs
        print(f"       {'AGREE' if same else 'DIVERGE'}   messages {'identical' if same_msgs else 'DIFFER'}")
        print(f"       ours messages ({len(ours_msgs)}): {sorted(set(ours_msgs))}")
        print(f"       ISO  messages ({len(msgs)}): {msgs}")
    print(f"\n{agree} of {len(todo)} agree")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
