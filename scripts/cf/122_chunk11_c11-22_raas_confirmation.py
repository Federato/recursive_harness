#!/usr/bin/env python3
"""Chunk 11 C11-22 -- ISO confirmation of the golden case, plus the rounding
tie, plus the one LI message not yet compared (C11-09).

Chunk 11 has ZERO ISO fixtures, so confirmation is by live call (chunk 9's
route). The like-for-like date is 2026-09-17 (OI-105: at 2027-01-01 ISO
serves a newer Oregon edition than we hold). Predictions, written before
this ran:

  C0  the golden case at 2026-09-17: ours $272 / $31 -- already confirmed by
      `118_...` (C0 agrees); re-sent here so this script stands alone.
  T1  the rounding tie. Gross 1,000 at 2026-09-17 gives nets 78,195 and
      73,474, average exactly 75,834.5. Our engine rounds half-up -> 75,835;
      banker's rounding would give 75,834. The premium is $181 either way,
      so ISO's own TenantsNetLeaseholdInt field is the discriminator.
      Predicted: ISO 75,835 (half-up).
  M1  a lease whose expiration is before its inception (LeaseEffDate
      01/01/2030, LeaseExpDate 01/01/2029). Predicted: ours and ISO both
      carry "CP 00 60 - Expiration Date of Lease can not be before Inception
      Date of Lease", and the same premiums.

The hand-derived golden case ($268 / $30 at EffDate 2027-01-01) cannot be
compared like-for-like at 2027-01-01 (OI-105). What that date DID confirm
(results/cf-raas/chunk11_C0_at20270101_response.json): every annuity value
to the digit -- 120/108 months, 0.385543128682177, 77.0562/72.2213, net
111,958 -- and BGII $30. Only the BGI base rate (a newer edition) differed.

    python scripts/cf/122_chunk11_c11-22_raas_confirmation.py

Exit 2 if ISO can't be called; 0 if every prediction held; 1 otherwise.
"""
from __future__ import annotations

import json
import sys
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import raas as raas_mod                                        # noqa: E402
from gl_engine.interp.tree import read                         # noqa: E402

g = import_module("114_chunk11_golden_case")
m = import_module("118_chunk11_c11-23_raas")
ROOT = Path(__file__).resolve().parents[2]
BGI = g.cell("TenantsLease", "BasicGroupI") + "/Premium"
BGII = g.cell("TenantsLease", "BasicGroupII") + "/Premium"
NET = g.LI + "/TenantsNetLeaseholdInt"
CP0060_EXP = "CP 00 60 - Expiration Date of Lease can not be before Inception Date of Lease"


def iso_msgs(resp):
    out = set()
    for rm in m.find(resp, "RatingMessages"):
        for kind in ("Errors", "Warnings"):
            for e in rm.get(kind, []) or []:
                out.add(e.get("Description", ""))
    return out


def iso_li_field(resp, field):
    recs = m.find(resp, "CommercialPropertyLeaseholdInterestCoverageForm")
    return recs[0][0].get(field) if recs and recs[0] else None


def main() -> int:
    try:
        client = raas_mod.RaaS()
    except raas_mod.RaaSError as exc:
        print(f"CANNOT CALL: {exc}")
        return 2
    out = ROOT / "results" / "cf-raas"
    out.mkdir(parents=True, exist_ok=True)
    cases = [
        ("C0", "golden case at 09/17/2026", g.LI_RECORD),
        ("T1", "rounding tie, gross 1,000", dict(g.LI_RECORD, TenantsGrossLeaseholdInt="1000")),
        ("M1", "lease expires before it starts",
         dict(g.LI_RECORD, LeaseEffDate="01/01/2030", LeaseExpDate="01/01/2029")),
    ]
    ok = True
    print(f"Chunk 11 C11-22 -- live ISO, EffectiveDateTime {m.EFFECTIVE}\n")
    for cid, label, li in cases:
        sub = m.at_date(g.submission(li=li))
        data, ip = g.run(sub)
        ours = (read(BGI, data), read(BGII, data), read(NET, data), {str(x) for x in ip.messages})
        req = m.payload(sub)
        (out / f"chunk11_c1122_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
        resp = client.rate(req)
        (out / f"chunk11_c1122_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
        cells = m.iso_cells(resp)
        iso = (cells.get("TenantsLease/BasicGroupI"), cells.get("TenantsLease/BasicGroupII"),
               iso_li_field(resp, "TenantsNetLeaseholdInt"), iso_msgs(resp))
        same = (all(m._num(a or 0) == m._num(b or 0) for a, b in zip(ours[:3], iso[:3]))
                and ours[3] == iso[3])
        extra = ""
        if cid == "T1":
            same &= m._num(iso[2]) == 75835
            extra = "  (predicted 75,835 half-up; 75,834 would mean banker's rounding)"
        if cid == "M1":
            same &= CP0060_EXP in iso[3]
        ok &= same
        print(f"  {cid} {label}")
        print(f"     ours: BGI {ours[0]}  BGII {ours[1]}  net {ours[2]}  msgs {sorted(ours[3])}")
        print(f"     ISO : BGI {m._num(iso[0] or 0)}  BGII {m._num(iso[1] or 0)}  net {m._num(iso[2] or 0)}  msgs {sorted(iso[3])}")
        print(f"     {'AGREE' if same else 'DIVERGE'}{extra}\n")
    print("C11-22 confirmed: every prediction held." if ok else "DIVERGENCE -- see above.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
