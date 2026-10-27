"""R-8 Phase 4c / backlog W-8 -- does ISO key the Special Class Group II rate on the
Special Class item's OWN construction symbol?

The filed rule says yes: `LookupBasicGroupIIRate` in the countrywide
`CommercialPropertySpecialClassRules.Rule.xml` keys on state + BasicGroupIIRatingTerr +
the item's `BasicGroupIISymbol` + "Bldg", and no rule copies the symbol from a
building. The rater instead keys on building k's symbol.

The probe: chunk 6's Oregon Special Class request (ISO-confirmed, symbol "B", base
rate 0.028) re-sent with only the item's symbol changed. If ISO's base rate moves,
ISO reads the item's own symbol. (Florida -- where the rater's item sits -- cannot be
used: FL drops these classes from its converter and ISO refuses, chunk 6.)

    python scripts/cf/114_r8_sc_symbol_probe.py
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
import raas as raas_mod                                             # noqa: E402

REQ = REPO / "results/cf-raas/OR_chunk6_Basic_request.json"


def sc_item(obj):
    return obj["CommercialProperty"][0]["CommercialPropertyLocation"][0]["CommercialPropertySpecialClass"][0]


def main() -> int:
    raas_mod.load_env()
    client = raas_mod.RaaS()
    base = json.loads(REQ.read_text())
    out = {}
    for sym in ("B", "AB"):
        req = copy.deepcopy(base)
        sc_item(req["body"])["BasicGroupIISymbol"] = sym
        resp = client.rate(req)
        it = sc_item(resp["Body"])
        out[sym] = {k: it.get(k) for k in ("BasicGroupIISymbol", "BasicGroupIIBaseRate",
                                           "FinalBasicGroupIIRate", "TotalSpecialClassCoveragePremium")}
        print(f"  item symbol {sym!r:5} -> {out[sym]}")
    moved = out["B"]["BasicGroupIIBaseRate"] != out["AB"]["BasicGroupIIBaseRate"]
    print("\n  ISO keys the Group II base rate on the item's own symbol:", "YES" if moved else "NO")
    return 0 if moved else 1


if __name__ == "__main__":
    raise SystemExit(main())
