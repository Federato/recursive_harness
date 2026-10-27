#!/usr/bin/env python3
"""Chunk 10, C10-16 -- the 9-file Legal Liability EQ branch.

The census (finding 3) and the opening census script (`84_chunk10_census.py`)
counted 9 files whose bodies mention `LegalLiab` (0 by filename). Re-derived
here directly, not trusted from the doc: a fresh content search of the same
97-file `Rules/*Earthquake*` population finds the SAME 9 files:

    CommercialPropertyEarthquakeAndVolcanicEruptionCoverageSubLimitFormWithFlatDollarDeductibleBldgRules.Rule.xml
    CommercialPropertyEarthquakeAndVolcanicEruptionCoverageSubLimitFormWithFlatDollarDeductiblePrsnlPropRules.Rule.xml
    CommercialPropertyEarthquakeAndVolcanicEruptionCoverageWithFlatDollarDeductibleBldgRules.Rule.xml
    CommercialPropertyEarthquakeAndVolcanicEruptionCoverageWithFlatDollarDeductiblePrsnlPropRules.Rule.xml
    CommercialPropertyEarthquakeAndVolcanicEruptionEndorsementPrsnlPropRules.Rule.xml
    CommercialPropertyEarthquakeAndVolcanicEruptionEndorsementRules.Rule.xml   <- this case
    CommercialPropertyEarthquakeAndVolcanicEruptionEndorsementSubLimitFormPrsnlPropRules.Rule.xml
    CommercialPropertyEarthquakeAndVolcanicEruptionEndorsementSubLimitFormRules.Rule.xml
    CommercialPropertyNonOwnedTrailersEarthquakeCoverageRules.Rule.xml

8 are the 4 Bldg/PrsnlProp variants of the 2 core EQ Endorsement families
(plain + sub-limit), each of which carries its own `CovType="Legal Liability"`
`When` inside `SetPremium`, plus Non-Owned Trailers' own file (C10-17's job).
This script traces the PLAIN Endorsement's own Legal Liability `When`, read
directly off the XML (not assumed from the census prose):

    Product DecimalPlaces=0 [
      Product DecimalPlaces=0 [
        Product DecimalPlaces=0 [
          Product DecimalPlaces=3 [
            Product DecimalPlaces=3 [ ../../EQCauseOfLossAdjustment x ../../LegalLiabilityFactor ]
            x ../../LegalLiabAddlInsurableIntFactor
          ]
          x (../../Limit / 100)
        ]
        x ../../../../../../CyberIncidentExclusionFactorEQ
      ]
      x ../../../../../../CyberIncidentExclusionCOLExcptnsFactorEQ
    ]

**The load-bearing finding**: `LegalLiabilityFactor` and
`LegalLiabAddlInsurableIntFactor` are NOT EQ-prefixed fields -- they are the
IDENTICAL field names chunk 8's own ordinary (non-EQ) Legal Liability chain
already computes on the Structure record
(`SetLegalLiabilityFactor`/`SetLegalLiabAddlInsurableIntFactor`,
`CommercialPropertyStructureRules.Rule.xml`, both gated purely on
`CovType="Legal Liability"`, unconditional of any EQ election). EQ's own
`SetPremium` reads them with a plain `../../` relative path, the same level
as `EQCauseOfLossAdjustment` -- a genuine SHARED-FIELD reuse, not a
collision: both rules that WRITE these fields are declared exactly once, run
once per structure regardless of whether EQ is elected, and EQ's Legal
Liability branch just multiplies its own EQ-specific rate
(`EQCauseOfLossAdjustment`) by whatever the ordinary chain already computed.
Chunk 8's own C8-01 formula (`RATE x LegalLiabilityFactor x
LegalLiabAddlInsurableIntFactor x Limit/100 x 2 Cyber factors`) and EQ's
formula above are IDENTICAL in shape, differing only in which "RATE" feeds
the product -- `SpecialRate`/`BasicGroupICauseOfLossAdjustment` for the
ordinary chain, `EQCauseOfLossAdjustment` for EQ -- confirming they are two
independent Product trees sharing two already-computed factor inputs, not
two writers of the same field.

This script builds ONE real submission -- chunk 8's own Legal Liability
Basic Group I case (`59_chunk8_golden_case.py`'s `building()`, `$60`,
`AddlInsurableInt="None"` -> Option4 -> 1.0) -- plus chunk 10's own golden-
case EQ election added on the SAME structure, and confirms by running:

  (a) the EQ branch fires correctly for a Legal Liability CovType
  (b) chunk 8's own $60 ordinary Legal Liability premium is unmoved
  (c) the two branches read the SAME LegalLiabilityFactor/
      LegalLiabAddlInsurableIntFactor values without either recomputing or
      overwriting the other's inputs -- no double-count, no collision

    python scripts/cf/99_chunk10_c10-16_legal_liability_eq.py [--trace]

Exit 0 on match. No engine code touched regardless of outcome.
"""
from __future__ import annotations

import argparse
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from importlib import import_module

from cf_engine.config import NULL_ARITHMETIC, ROUNDING
from cf_engine.resolve import book_for
from gl_engine.interp.interpreter import Interpreter
from gl_engine.interp.tree import Node, read

chunk8 = import_module("59_chunk8_golden_case")
golden10 = import_module("85_chunk10_golden_case")

JURIS, ASOF = chunk8.JURIS, chunk8.ASOF

STRUCT = ("CommercialPropertyTable/CommercialProperty/"
          "CommercialPropertyLocationTable/CommercialPropertyLocation/"
          "CommercialPropertyStructureTable/CommercialPropertyStructure")
LL_PREM = STRUCT + "/CommercialPropertyStructureBuildingBasicGroupICoverage/Premium"
ENDT = STRUCT + ("/CommercialPropertyEarthquakeAndVolcanicEruptionEndorsementTable"
                  "/CommercialPropertyEarthquakeAndVolcanicEruptionEndorsement[1]")

#: chunk 10's own golden-case EQ election, verbatim -- same structure-level
#: no-op inputs (BCEG, SprinklerSystem, EQSprinklerLeakageOnly) proven there.
EQ_ELECTION = {
    "EQCovIndicator": "Yes, Not Included in Blanket",
    "EQClass": "A1",
    "EQCoinsurance": "90%",
    "EQDeductible": "10%",
    "EQSprinklerLeakageOnly": "Not Applicable",
    "BCEG": "1",
    "SprinklerSystem": "None",
}
LOC_EQ = {"EQCauseOfLossForm": "Earthquake Form (CP 10 40)", "EQTerr": "1",
          "EQDeductibleTier": "1"}

#: chunk 8's own filed values, re-used verbatim (Bldg row of LegalLiabilityFactor).
LEGAL_LIABILITY_FACTOR = Decimal("0.25")          # [CW, "Bldg"]
LEGAL_LIAB_ADDL_INT_FACTOR = Decimal("1.0")       # "None" -> Option4
ORDINARY_LL_PREMIUM = Decimal("60")               # chunk 8's own C8-01 result, unmoved

#: chunk 10's own golden-case EQ chain, re-used verbatim -- unaffected by
#: CovType (confirmed by running below, not assumed).
EQ_CAUSE_OF_LOSS_ADJ = Decimal("0.009")


def submission() -> dict:
    """Chunk 8's own Legal Liability Basic Group I structure, PLUS chunk 10's
    own EQ election on the SAME structure. Both branches' inputs present at
    once -- the only way to test (b) and (c), not just (a)."""
    sub = chunk8.building(col="Basic", option="None", record=True)
    loc = (sub["CommercialPropertyTable"]["CommercialProperty"][0]
           ["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0])
    loc.update(LOC_EQ)
    st = loc["CommercialPropertyStructureTable"]["CommercialPropertyStructure"][0]
    st.update(EQ_ELECTION)
    return sub


def predict() -> dict:
    step1 = (EQ_CAUSE_OF_LOSS_ADJ * LEGAL_LIABILITY_FACTOR).quantize(Decimal("0.001"))
    step2 = (step1 * LEGAL_LIAB_ADDL_INT_FACTOR).quantize(Decimal("0.001"))
    step3 = (step2 * (Decimal(100_000) / 100)).quantize(Decimal("1"))
    step4 = (step3 * Decimal("1.0")).quantize(Decimal("1"))   # CyberIncidentExclusionFactorEQ
    step5 = (step4 * Decimal("1.0")).quantize(Decimal("1"))   # CyberIncidentExclusionCOLExcptnsFactorEQ
    return {"step1": step1, "step2": step2, "step3": step3, "eq_premium": step5}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--trace", action="store_true")
    a = ap.parse_args()

    book = book_for(JURIS, ASOF)
    print(f"{book}\n")

    # -------------------------------------------------------- re-derive the 9
    rules_dir = book.parent.package.content / "Rules"
    eq_files = sorted(p.name for p in rules_dir.glob("*.xml") if "Earthquake" in p.name)
    ll_files = sorted(f for f in eq_files
                       if "LegalLiab" in (rules_dir / f).read_text(encoding="utf-8-sig"))
    print(f"Re-derived Legal-Liability-touching EQ files: {len(ll_files)} of "
          f"{len(eq_files)} (census claim: 9, "
          f"{'MATCH' if len(ll_files) == 9 else 'DOES NOT MATCH'})")
    for f in ll_files:
        print(f"    {f}")
    print()

    p = predict()
    print("Hand-derivation, EQ Legal Liability branch (computed before running):")
    print(f"  EQCauseOfLossAdjustment x LegalLiabilityFactor       = round({EQ_CAUSE_OF_LOSS_ADJ} x {LEGAL_LIABILITY_FACTOR}, 3) = {p['step1']}")
    print(f"  x LegalLiabAddlInsurableIntFactor                    = round({p['step1']} x {LEGAL_LIAB_ADDL_INT_FACTOR}, 3) = {p['step2']}")
    print(f"  x Limit/100                                          = round({p['step2']} x 1000, 0) = {p['step3']}")
    print(f"  x 2 Cyber factors (both 1.0, no exclusion record)    = {p['eq_premium']}")
    print(f"  Ordinary Legal Liability Premium (chunk 8, unmoved)  = {ORDINARY_LL_PREMIUM}\n")

    ip = Interpreter(book, rounding=ROUNDING, trace=a.trace,
                      null_arithmetic=NULL_ARITHMETIC)
    data = Node.from_dict(f"MasterCF{JURIS}", submission())
    ip.run(data)

    checks = [
        ("EQCauseOfLossAdjustment", STRUCT + "/EQCauseOfLossAdjustment", str(EQ_CAUSE_OF_LOSS_ADJ)),
        ("LegalLiabilityFactor (shared field)", STRUCT + "/LegalLiabilityFactor", str(LEGAL_LIABILITY_FACTOR)),
        ("LegalLiabAddlInsurableIntFactor (shared field)",
         STRUCT + "/LegalLiabAddlInsurableIntFactor", str(LEGAL_LIAB_ADDL_INT_FACTOR)),
        ("EQ Endorsement Premium (Legal Liability branch)", ENDT + "/Premium", str(p["eq_premium"])),
        ("Ordinary Legal Liability Premium (regression)", LL_PREM, str(ORDINARY_LL_PREMIUM)),
    ]
    ok = True
    for label, path, want in checks:
        got = read(path, data)
        try:
            good = got is not None and Decimal(got) == Decimal(want)
        except Exception:
            good = got == want
        ok &= good
        flag = "" if good else f"   <-- expected {want}"
        print(f"  {label:52s} = {str(got):>10s}{flag}")

    if ip.messages:
        print(f"\n  ISO validation messages ({len(ip.messages)}): "
              + "; ".join(str(m)[:60] for m in ip.messages[:6]))

    print()
    if ok:
        print("MATCH -- EQ's own Legal Liability branch fires correctly on a "
              "real Legal Liability CovType, chunk 8's own $60 ordinary "
              "premium is unmoved, and both branches read the SAME "
              "LegalLiabilityFactor/LegalLiabAddlInsurableIntFactor values "
              "without recomputing or overwriting them -- confirmed shared, "
              "not colliding. No engine gap.")
        return 0
    print("MISMATCH above -- not patched here if it traces to engine code, "
          "per this project's standing rule.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
