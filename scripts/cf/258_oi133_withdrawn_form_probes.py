#!/usr/bin/env python3
"""OI-133: an empty state table whose form the state WITHDREW -- does ISO refuse where it falls back for an offered form?

Evidence before this script (2026-10-06): FL withdrew the Cyber Incident Exclusion (CP 10 75, `Pages` Status "D"), files
its `CyberIncidentExclusionFactors` empty, and ISO refuses a FL policy attaching it at that table; VT's empty
`VacancyPermitFactors` and NY's empty `OffPremEndtsModifyingCovdCOLFactor` belong to forms those states offer, and ISO
falls back to countrywide's rows (VT re-confirmed live, factor 0.053). Ours falls back everywhere (but the EQ stub).

Hypothesis W: ISO fills an empty state table from countrywide only when the table's form is offered in that state; for a
withdrawn form the table is read as filed, and a lookup reaching it refuses.

  search (default, no ISO): every stored request ISO rated, moved into each state that withdraws one of its forms (and,
          as controls, kept in or moved to states that offer them), rated on ours with every empty-state-table fallback
          recorded. Only a request whose rating actually REACHES an empty state table is a probe; W predicts each.
  --live: the probes found, sent to ISO at 2026-09-17; the verdict is W's prediction against ISO's answer.

    python scripts/cf/258_oi133_withdrawn_form_probes.py [--live] [--max 12]

Results: results/cf-raas/oi133_probes.json and oi133_<id>_{request,response,refusal}.json.
"""
from __future__ import annotations

import argparse
import copy
import glob
import json
import re
import sys
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

import property_rating as pr
from cf_engine.resolve import book as bk, book_for
from gl_engine.interp import interpreter as I
from gl_engine.interp.values import InterpretError

cmp = import_module("154_chunk13_rc5_fields_messages")
RES = ROOT / "results" / "cf-raas"
DATE = "20260917"

HITS: list = []
CUR = {"ruleset": None}
_table = bk.CFResolvedBook.table
_call = I.Interpreter.call


def _rec_table(self, name, kind="Rate"):
    if (kind == "Rate" and self.state.has(kind, name) and not self.state.table(kind, name).rows
            and name not in self.NO_EMPTY_FALLBACK and self.parent and self.parent.has(kind, name)
            and self.parent.table(kind, name).rows):
        HITS.append((name, CUR["ruleset"]))
    return _table(self, name, kind)


def _rec_call(self, file_name, rule_name, *a, **k):
    prev, CUR["ruleset"] = CUR["ruleset"], file_name
    try:
        return _call(self, file_name, rule_name, *a, **k)
    finally:
        CUR["ruleset"] = prev


bk.CFResolvedBook.table, I.Interpreter.call = _rec_table, _rec_call

_W: dict = {}


def withdrawn(st: str) -> set:
    if st not in _W:
        _W[st] = pr._withdrawn(book_for(st, DATE))
    return _W[st]


def records(o, out=None) -> set:
    out = set() if out is None else out
    if isinstance(o, dict):
        for k, v in o.items():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                out.add(k)
            records(v, out)
    elif isinstance(o, list):
        for x in o:
            records(x, out)
    return out


def move(req: dict, st: str) -> dict:
    """The request moved into `st`, with the state's own territories, as the app's sample is (property_rating.sample)."""
    from _state_inputs import localize_request
    q = copy.deepcopy(req)
    q["body"]["SchemeKeys"] = {"ProductName": f"Commercial Property {st}", "EffectiveDateTime": "2026-09-17T00:00:00"}
    book = book_for(st, DATE)
    for cp in q["body"]["CommercialProperty"]:
        cp["State"] = st
        for loc in cp.get("CommercialPropertyLocation", []):
            terr = pr._first(book, "RatingTerritoryGroupIFactor", "BasicGroupIRatingTerritory")
            if terr is not None:
                loc["BasicGroupIRatingTerr"] = terr
            for table, col, field in (("PrsnlPropTerrMultiplier", "SpecialRatingTerr", "SpecialRatingTerr"),
                                      ("GeographicWindHazardLevel", "GeographicWindHazardLevelTerritory",
                                       "GeographicWindHazardLevelTerritory")):
                v = pr._first(book, table, col)
                if v is not None:
                    loc[field] = v
    localize_request(q, st, DATE)
    return q


def ours(req: dict):
    HITS.clear()
    try:
        cmp.rate(req)
        out = "rated"
    except InterpretError as exc:
        out = "refused: " + str(exc)[:120]
    return out, sorted(set(HITS))


def search(limit: int, controls: bool = True) -> list:
    donors = {}
    for f in sorted(glob.glob(str(RES / "*_request.json"))):
        if not Path(f[:-len("_request.json")] + "_response.json").exists():
            continue
        try:
            req = json.loads(Path(f).read_text(encoding="utf-8"))
        except ValueError:
            continue
        if not req.get("body", {}).get("SchemeKeys", {}).get("ProductName", "").startswith("Commercial Property"):
            continue
        for r in records(req["body"]):
            donors.setdefault(r, (Path(f).name, req))
    targets = ["FL", "AK", "NY", "CT", "NE", "GA", "NC", "TX", "VA", "WV", "DC", "AR", "RI", "AL", "KS"]
    probes, seen = [], set()
    for st in targets:
        for rec in sorted(withdrawn(st)):
            if rec not in donors or len([p for p in probes if p["kind"] == "W"]) >= limit:
                continue
            name, req = donors[rec]
            q = move(req, st)
            out, hits = ours(q)
            if not hits:
                continue
            key = (st, tuple(h[0] for h in hits))
            if key in seen:
                continue
            seen.add(key)
            probes.append({"id": f"W-{st}-{len(probes)}", "kind": "W", "state": st, "form": rec, "donor": name,
                           "ours": out, "empty_tables_reached": hits, "predict": "ISO refuses (W)", "request": q})
            print(f"  W {st} {rec[:70]}: reaches {[h[0] for h in hits]}; ours {out[:40]}")
    # controls: offered forms whose empty tables are reached -- W predicts ISO falls back (rates)
    ctl = 0
    for st in (targets if controls else []):
        for rec, (name, req) in sorted(donors.items()):
            if ctl >= limit // 2 or rec in withdrawn(st):
                continue
            if any(r in withdrawn(st) for r in records(req["body"])):
                continue
            q = move(req, st)
            out, hits = ours(q)
            hits = [h for h in hits if h[0] not in ("VacancyPermitFactors", "OffPremEndtsModifyingCovdCOLFactor")]
            if not hits:
                continue
            key = ("C", st, tuple(h[0] for h in hits))
            if key in seen:
                continue
            seen.add(key)
            ctl += 1
            probes.append({"id": f"C-{st}-{len(probes)}", "kind": "C", "state": st, "form": rec, "donor": name,
                           "ours": out, "empty_tables_reached": hits, "predict": "ISO rates (W: offered form, falls back)",
                           "request": q})
            print(f"  C {st} {rec[:70]}: reaches {[h[0] for h in hits]}; ours {out[:40]}")
    return probes


def live(probes: list) -> None:
    import raas as raas_mod
    client = raas_mod.RaaS()
    for p in probes:
        base = RES / f"oi133_{p['id']}"
        Path(f"{base}_request.json").write_text(json.dumps(p["request"], indent=2), encoding="utf-8")
        try:
            resp = client.rate(p["request"])
            Path(f"{base}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
            p["iso"] = "rated"
        except raas_mod.RaaSError as exc:
            msg = (re.findall(r'"Message":"([^"]{0,400})', str(exc.body)) or [str(exc.body)[:400]])[0]
            Path(f"{base}_refusal.json").write_text(json.dumps({"message": msg}, indent=2), encoding="utf-8")
            p["iso"] = "refused: " + msg
        refused = p["iso"].startswith("refused")
        p["agrees_with_W"] = refused if p["kind"] == "W" else not refused
        print(f"  {p['id']:10s} {p['form'][:55]:55s} W predicts {'refuse' if p['kind'] == 'W' else 'rate  '} | "
              f"ISO {p['iso'][:110]}  {'= W' if p['agrees_with_W'] else '<-- AGAINST W'}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--max", type=int, default=12)
    ap.add_argument("--no-controls", action="store_true", help="skip the slow search for offered-form controls")
    a = ap.parse_args()
    print("Searching for requests that reach an empty state table (ours, no ISO):")
    probes = search(a.max, controls=not a.no_controls)
    print(f"{len([p for p in probes if p['kind'] == 'W'])} withdrawn-form probes, "
          f"{len([p for p in probes if p['kind'] == 'C'])} offered-form controls")
    if a.live and probes:
        print("ISO at 2026-09-17:")
        live(probes)
        w = [p for p in probes if "agrees_with_W" in p]
        print(f"\nW holds on {sum(p['agrees_with_W'] for p in w)} of {len(w)} probes")
    (RES / "oi133_probes.json").write_text(json.dumps([{k: v for k, v in p.items() if k != "request"} for p in probes],
                                                      indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
