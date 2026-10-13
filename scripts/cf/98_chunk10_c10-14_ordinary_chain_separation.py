#!/usr/bin/env python3
"""Chunk 10, C10-14 -- confirm EQ's separation from IRPMFactor/
PackageModFactor/MultiPremiumAndDispersionCreditFactor/ordinary Deductible/
Coinsurance/LOI (opening census finding 4) holds for all 5 premium groups'
own EQ `SetPremium`, not just the core Building `Earthquake
AndVolcanicEruptionEndorsementRules.Rule.xml` file the census read directly.

Reads each of the 5 groups' own EQ Endorsement `SetPremium` rule body
directly (not the 97-file population at large -- these 5 specific files are
each group's "real" EQ premium node, the same shape C10-01's golden case
traced for Building) and lists every `FromDataDef` field it references,
checking for the 6 ordinary-chain names by substring, deliberately loose so
an EQ-prefixed near-namesake (`EQDeductibleFactor` etc.) would also be
caught and has to be explained rather than silently passed.

    python scripts/cf/98_chunk10_c10-14_ordinary_chain_separation.py

Exit 0 when none of the 6 names appear in any of the 5 groups' SetPremium.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from cf_engine.resolve import book_for

ASOF = "20260917"

GROUP_FILES = {
    "Building": "CommercialPropertyEarthquakeAndVolcanicEruptionEndorsementRules.Rule.xml",
    "Contents": "CommercialPropertyEarthquakeAndVolcanicEruptionEndorsementPrsnlPropRules.Rule.xml",
    "Business Income": "CommercialPropertyEarthquakeAndVolcanicEruptionEndorsementBusnIncomeRules.Rule.xml",
    "Special Class": "CommercialPropertyEarthquakeAndVolcanicEruptionEndorsementSpecialClassRules.Rule.xml",
    "SC Business Income": "CommercialPropertyEarthquakeAndVolcanicEruptionEndorsementSpclClassBusnIncomeRules.Rule.xml",
}

#: the 6 ordinary-chain names the census's finding 4 named, matched loosely
#: (substring) so an EQ-prefixed near-namesake is caught too, not excluded
#: by the match pattern itself.
BANNED = ["IRPMFactor", "PackageModFactor", "MultiPremiumAndDispersionCreditFactor",
          "DeductibleFactor", "CoinsuranceFactor", "LOIFactor"]


def main() -> int:
    book = book_for("CW", ASOF)
    rules_dir = book.state.package.content / "Rules"

    ok = True
    print("=== EQ SetPremium fields read, all 5 groups' own Endorsement file\n")
    for g, fn in GROUP_FILES.items():
        t = (rules_dir / fn).read_text(encoding="utf-8-sig")
        i = t.find('<rul:Rule Name="SetPremium"')
        assert i >= 0, f"{fn}: no SetPremium rule found"
        j = t.find("</rul:Rule>", i) + 11
        body = t[i:j]
        fields = sorted(set(re.findall(r'FromDataDef="([^"]+)"', body)))
        print(f"    -- {g} ({fn}) --")
        for f in fields:
            print(f"        {f}")
        hits = {b: [f for f in fields if b in f] for b in BANNED}
        hits = {b: v for b, v in hits.items() if v}
        if hits:
            ok = False
            print(f"        BANNED NAME(S) FOUND: {hits}")
        else:
            print("        none of the 6 ordinary-chain names (or an "
                  "EQ-prefixed near-namesake) appear")
        print()

    print("=== Verdict\n")
    if ok:
        print("Confirmed for all 5 groups, by direct read of each group's own "
              "EQ Endorsement SetPremium rule, not just Building's: none of "
              "IRPMFactor/PackageModFactor/MultiPremiumAndDispersionCredit"
              "Factor/DeductibleFactor/CoinsuranceFactor/LOIFactor (nor an "
              "EQ-prefixed near-namesake) is read directly by any group's own "
              "EQ premium formula. Each group's SetPremium instead reads only "
              "its own already-computed FinalEQRate/BlktEQAvgRate (or, for "
              "Building/Contents, the Legal Liability branch's "
              "LegalLiabFactor/LegalLiabAddlInsurableIntFactor) plus the two "
              "EQ-specific Cyber-exclusion factors -- the census's finding 4 "
              "holds project-wide, not just for the one file read directly. "
              "No engine gap.")
        return 0
    print("MISMATCH -- see BANNED NAME(S) FOUND above. A real finding, not "
          "patched here per this project's standing rule.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
