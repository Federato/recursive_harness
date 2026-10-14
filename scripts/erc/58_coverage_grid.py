"""The GL coverage grid (B-13): which coverage families ISO has ever priced for us, and whether we agree.

The 19 families are the 13 ISO gives a policy-level minimum-premium group, plus terrorism, Stop Gap, Damage to Premises
Rented, Med Pay, endorsement charges and New York's Special Protective & Highway. For each stored ISO answer
(`results/tc/answers`, the live calls; `Payloads/`, ISO's 50 example pairs) every premium ISO marks as money
(`PremiumIndicator = 1`) is compared with our `by_coverage` line for the same request, re-rated now.

A family counts once ISO has priced it above $0 in some answer. Disagreements on the example pairs are expected where
the pair is a known defect (OI-77: terrorism "Yes" in, "No" out; OI-78: AZ's output is Alaska's).

    python scripts/erc/58_coverage_grid.py
"""
from __future__ import annotations

import collections
import glob
import json
import os
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

#: family -> substrings of the coverage tags that belong to it (first match wins, so Products before Prem/Ops' host)
FAMILIES = [
    ("Premises/Operations", ("ClassificationPremOpsCoverage",)),
    ("Products/Completed Ops", ("ClassificationProdsCompldOpsCoverage",)),
    ("Terrorism", ("GeneralLiabilityTerrorism",)),
    ("Endorsement charges", ("AlaskaChangesAttorneysFees", "ExclusionOfCertifiedActsOfTerrorism", "ExclusionPFAS",
                             "CapOnLosses", "ExclMedPay")),
    ("Limited Product Withdrawal", ("LimitedProductWithdrawal",)),
    ("Drone", ("UnmannedAircraft",)),
    ("Loss of Electronic Data", ("LossOfElectronicData",)),
    ("Liquor", ("Liquor",)),
    ("OCP", ("OwnersContractors",)),
    ("Railroad", ("ClassificationRailroad",)),
    ("Cyber Incident", ("CyberIncident",)),
    ("Stop Gap", ("StopGap",)),
    ("Pollution", ("Pollution",)),
    ("Underground Storage Tank", ("UndergroundStorageTank",)),
    ("Electronic Data Liability", ("ElectronicDataLiability",)),
    ("Special Combined", ("SpecialCombined",)),
    ("NY Special Protective & Highway", ("SpecialProtective",)),
    ("Damage to Premises Rented", ("DamageToPremisesRented",)),
    ("Med Pay", ("MedPay",)),
]


#: Families ISO cannot price separately, with the evidence (B-13, 2026-10-14). The grid shows them empty by design.
NOT_PRICEABLE = {
    "Special Combined": "a minimum-premium top-up for certain class combinations, not a coverage; ISO files every "
                        "minimum at $0, so it never fires on ISO's content",
    "NY Special Protective & Highway": "ISO's loss costs are filed at 0 for all three classes; ISO prices it $0 with no "
                                       "message (2 calls, both editions; our R30 flags it)",
    "Damage to Premises Rented": "its rules write Premium but never PremiumIndicator: carried inside Premises/Operations",
    "Med Pay": "its rules write Premium but never PremiumIndicator: carried inside Premises/Operations",
}


def iso_money(body) -> collections.Counter:
    """coverage tag -> summed Premium where ISO marks it money (PremiumIndicator 1), from a RaaS response body."""
    out: collections.Counter = collections.Counter()

    def walk(o, tag):
        if isinstance(o, dict):
            p, ind = o.get("Premium"), o.get("PremiumIndicator")
            if tag and isinstance(p, (int, float)) and str(ind).strip() in ("1", "1.0"):
                out[tag] += Decimal(str(p))
            for k, v in o.items():
                if isinstance(v, (dict, list)):
                    walk(v, k)
        elif isinstance(o, list):
            for x in o:
                walk(x, tag)
    walk(body, None)
    return out


def family(tag: str) -> str | None:
    for name, keys in FAMILIES:
        if any(k in tag for k in keys):
            return name
    return None


def main() -> int:
    from gl_engine.rating import Kernel
    pairs = [(q, q.replace("_request.json", "_response.json"))
             for q in sorted(glob.glob(str(ROOT / "results/tc/answers/*_request.json")))]
    pairs += [(f"{d}/1. Input.json", f"{d}/1. Output.json") for d in sorted(glob.glob(str(ROOT / "Payloads/*")))]
    k = Kernel()
    grid = {name: {"answers": 0, "agree": 0, "disagree": 0, "refused": 0, "states": set()} for name, _ in FAMILIES}
    n = 0
    for q, r in pairs:
        if not os.path.exists(q) or not os.path.exists(r):
            continue
        req = json.load(open(q, encoding="utf-8-sig"))
        resp = json.load(open(r, encoding="utf-8-sig"))
        body = req.get("body", req)
        rb = resp.get("Body", resp.get("body", resp))
        if "GeneralLiability" not in body or not isinstance(rb, dict) or "GeneralLiability" not in rb:
            continue
        n += 1
        ours = k.rate(req if "body" in req else {"header": {}, "body": req})
        state = ((body.get("SchemeKeys") or {}).get("ProductName") or "?").split()[-1]
        seen = set()
        for tag, v in iso_money(rb).items():
            fam = family(tag)
            if fam is None or not v:
                continue
            g = grid[fam]
            if fam not in seen:
                g["answers"] += 1
                g["states"].add(state)
                seen.add(fam)
            if not ours.complete:
                g["refused"] += 1
            elif ours.by_coverage.get(tag, Decimal(0)) == v:
                g["agree"] += 1
            else:
                g["disagree"] += 1
    filled = sum(1 for g in grid.values() if g["answers"])
    print(f"{n} GL ISO answers; {filled} of {len(FAMILIES)} coverage families priced by ISO at least once; "
          f"{len(NOT_PRICEABLE)} cannot be priced separately\n")
    print(f"| # | Family | ISO answers | States | Lines agree | Lines differ |\n|---|---|---|---|---|---|")
    for i, (name, _) in enumerate(FAMILIES, 1):
        g = grid[name]
        why = f" ({NOT_PRICEABLE[name]})" if name in NOT_PRICEABLE else ""
        print(f"| {i} | {name}{why} | {g['answers']} | {len(g['states'])} | {g['agree']} | {g['disagree']} |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
