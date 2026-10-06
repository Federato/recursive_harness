#!/usr/bin/env python3
"""OI-133, built: FL's withdrawn cyber exclusion tables read as filed. Confirmed against ISO on clean requests. Live ISO.

Clean requests: the app's FL sample (scripts/property_rating.py; it rates in FL and equals ISO, $2,787) with the cyber
exclusion form added back -- CP 10 75 (`CommercialPropertyCyberIncidentExclusion`) and CP 10 76 (`...WithEnsuing
CausesOfLossExceptions`, its fields from 258_'s probe). Each must refuse in ours at the SAME table ISO names.
Controls, which must still rate and equal ISO: the FL sample as the app sends it (no cyber form), VT's vacancy probe
(an offered form's empty table, ISO fills it from countrywide: C28-03 V-VT) and NY's off-premises probe (258_ W-NY-2).

    python scripts/cf/259_oi133_confirm.py [--offline]

Exits 1 on any disagreement.
"""
from __future__ import annotations

import argparse
import copy
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
from gl_engine.interp.values import InterpretError

cmp = import_module("154_chunk13_rc5_fields_messages")
rep = import_module("157_chunk14_c14-02_total_replay")
RES = ROOT / "results" / "cf-raas"
TABLE = re.compile(r"(?:Matrix: |in ')([A-Za-z0-9]+)")


def cases() -> list:
    fl = pr.sample("FL")
    c75 = copy.deepcopy(fl)
    c75["body"]["CommercialProperty"][0]["CommercialPropertyCyberIncidentExclusion"] = [{}]
    c76 = copy.deepcopy(fl)
    donor = json.loads((RES / "oi133_W-FL-1_request.json").read_text(encoding="utf-8"))
    rec = "CommercialPropertyCyberIncidentExclusionWithEnsuingCausesOfLossExceptions"
    c76["body"]["CommercialProperty"][0][rec] = donor["body"]["CommercialProperty"][0][rec]
    load = lambda n: json.loads((RES / n).read_text(encoding="utf-8"))
    return [
        ("FL-CP1075", "refuse", "CyberIncidentExclusionFactors", c75),
        ("FL-CP1076", "refuse", "CyberIncidentExclusionWithEnsuingCauseOfLossExceptionsFactors", c76),
        ("FL-sample", "rate", None, fl),
        ("VT-vacancy", "rate", None, load("chunk28_c28-03_V-VT_request.json")),
        ("NY-offprem", "rate", None, load("oi133_W-NY-2_request.json")),
    ]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true")
    a = ap.parse_args()
    client = None
    if not a.offline:
        import raas as raas_mod
        client = raas_mod.RaaS()
    fails = []
    for cid, want, table, req in cases():
        try:
            data, _ = cmp.rate(req)
            ours, ours_table = "rated", None
        except InterpretError as exc:
            data, ours = None, "refused"
            m = TABLE.search(str(exc))
            ours_table = m.group(1) if m else str(exc)[:80]
        ok = ours == ("refused" if want == "refuse" else "rated") and (table is None or ours_table == table)
        line = f"{cid:11s} ours {ours}{' at ' + ours_table if ours_table else ''}"
        if client is not None:
            (RES / f"oi133_confirm_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
            try:
                resp = client.rate(req)
                iso, iso_table = "rated", None
                ip, op = rep.iso_prem(resp), rep.our_prem(data) if data is not None else {}
                dd = [k for k, v in ip.items() if not cmp.same(v, op.get(k))]
                total = ip.get("CommercialProperty[0]/ErcCalculatedTotalPremium")
                same = ours == "rated" and not dd
                line += f" | ISO rated, total {total}; {len(ip) - len(dd)} of {len(ip)} premiums equal"
                ok = ok and same
            except Exception as exc:                              # noqa: BLE001 -- a refusal is an answer
                body = str(getattr(exc, "body", exc))
                msg = (re.findall(r'"Message":"([^"]{0,300})', body) or [body[:300]])[0]
                iso, m = "refused", TABLE.search(msg)
                iso_table = m.group(1) if m else msg[:80]
                line += f" | ISO refused at {iso_table}"
                ok = ok and ours == "refused" and ours_table == iso_table
        print(f"  {'OK ' if ok else 'BAD'} {line}")
        if not ok:
            fails.append(cid)
    print(f"\nOI-133: {'ALL AS EXPECTED' if not fails else 'FAILED: ' + ', '.join(fails)}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
