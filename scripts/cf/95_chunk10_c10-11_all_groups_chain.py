#!/usr/bin/env python3
"""Chunk 10, C10-11 -- run the full SetEQBaseRate/SetEQRate/SetEQCauseOfLoss
Adjustment/SetFinalEQRate chain for the other 4 premium groups (Contents,
Business Income, Special Class, SC Business Income), not just Building.

C10-01's golden case (`85_chunk10_golden_case.py`) proved the chain end to
end for Building only. C10-06 (`92_chunk10_c10-06_shared_names.py`) read
every group's rule BODIES and found two confirmed mechanisms explaining why
Contents/Business Income/Special Class/SC Business Income carry fewer of the
9 named EQ-engine rules than Building -- an ancestor-copy of Building's own
`EQBaseRate`, and a differently-keyed base-rate table. Neither of those
findings was ever RUN. This script builds one real submission per group,
extending the existing chunk 4/5/6/7 golden-case builders exactly the way
`93_chunk10_c10-07_exclusion_records.py` extended chunk 4's own Personal
Property record, hand-derives the expected EQ premium for each from the
filed rows, and confirms match or documents mismatch.

All four submissions share chunk 10's own golden-case EQ election
(EQClass="A1", EQTerr="1", EQCoinsurance="90%", EQDeductible="10%",
BCEG="1", SprinklerSystem="None", EQSprinklerLeakageOnly="Not Applicable")
on the SAME Oregon Basic-Group-I structure the golden case built, so
Building's own EQBaseRate=0.009 chain is reused rather than re-derived.

  CONTENTS (Personal Property) -- has its OWN SetEQBaseRate, keyed on raw
      EQClass + EQGrade (C10-06 finding), not the normalized EQClassToUse
      Building uses. `EQLossCostPrsnlProp[OR]("A1","1")` is read directly.

  BUSINESS INCOME -- confirmed here to be MORE than a pure ancestor-copy:
      `SetEQRate` reads `../../EQBaseRate` (0.009, Building's) but also
      `../../SoftStoryModificationFactor`, `../../EQSprinkleredRiskFactor`,
      `../../BldgHeightFactor`, `../../BuildersRiskEQFactor` -- ALL from the
      Structure ancestor -- and only `LossCostMultiplier` and a LOCAL
      `BCEGEQFactor` (itself copied from `../../BCEGEQFactor`) are its own.
      `SetEQCauseOfLossAdjustment` = StoryModFactor x BuildersRiskFactor x
      EQRate x EQSprinklerLeakageOnlyBldgFactor (all local, all no-op here).
      `SetEQFactor`, absent any sub-limit record, copies the ORDINARY
      (non-EQ) `Factor` field directly -- chunk 5's own `TypeOfRiskFactor`
      value. `SetFinalEQRate` = EQCauseOfLossAdjustment x EQFactor.

  SPECIAL CLASS -- carries 8/9 of the named rules (only missing
      SetEQDeductibleByLocationFactor, C10-06). Runs its OWN
      SetEQBaseRate/SetEQRate/SetEQClassToUse/SetEQDeductibleFactor chain,
      the same shape as Building, on the Special Class item instead of the
      Structure.

  SC BUSINESS INCOME -- the same two ancestor-copy/EQFactor mechanisms as
      Business Income, one level down (its ancestor is Special Class, not
      Building): `SetEQRate` copies `../../EQRate` from the Special Class
      item, and `SetEQFactor` copies the ordinary `Factor` (chunk 7's own
      Business Income Factor for the parent's Special Class item).

    python scripts/cf/95_chunk10_c10-11_all_groups_chain.py [--trace]

Exit 0 when all four groups' EQ chain matches its hand derivation.
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

golden = import_module("85_chunk10_golden_case")
chunk4 = import_module("22_chunk4_golden_case")
chunk5 = import_module("32_chunk5_golden_case")
chunk6 = import_module("41_chunk6_golden_case")
chunk7 = import_module("50_chunk7_golden_case")

JURIS, ASOF = golden.JURIS, golden.ASOF

#: the EQ election golden case C10-01 already proved, reused verbatim on
#: every group's own record below.
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


def table_value(book, name, col, **keys):
    """Find the one row of a filed table matching `keys` (col=value)."""
    t = book.table(name)
    idx = {k: t.col(k) for k in keys}
    for r in t.rows:
        if all(str(r[i]) == str(keys[k]) for k, i in idx.items()):
            return r[t.col(col)]
    raise LookupError(f"{name}: no row matching {keys}")


def _loc(sub):
    return (sub["CommercialPropertyTable"]["CommercialProperty"][0]
            ["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0])


# ------------------------------------------------------------------ CONTENTS
# EQLossCostPrsnlProp is keyed on (State, EQClass, EQGrade) -- confirmed by
# C10-06 read of Contents' own SetEQBaseRate. EQGrade is a THIRD field
# Building's own chain never uses.

def contents_submission():
    """Chunk 4's own Contents case, plus chunk 10's EQ election.

    **Finding, not assumed**: `CommercialPropertyPersonalPropertyRules`' own
    `SetEQClass` is a bare, UNGUARDED `Copy ToDataDef="EQClass"
    FromDataDef="../../../../EQClass"` -- the STRUCTURE's own `EQClass`
    field, four levels up, with no `IsNull` check. A value set directly on
    the Personal Property record itself is silently overwritten by
    whatever (or nothing) the Structure carries -- the exact shape this
    project already logged for chunk 4's own `OccupCategoryRiskSeverity`
    trap, now confirmed for a THIRD field and a fourth chunk. `EQClass` is
    therefore a STRUCTURE-level input for Contents too, the same as
    Building, not a Personal-Property-level one as C10-06's own rule-body
    read (which never looked at `SetEQClass`, only at `SetEQBaseRate`)
    would suggest. `EQGrade` has no such rule at all -- it genuinely is
    local to the Personal Property record.
    """
    sub = chunk4.submission("Basic")
    _loc(sub).update(LOC_EQ)
    struct = (sub["CommercialPropertyTable"]["CommercialProperty"][0]
              ["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0]
              ["CommercialPropertyStructureTable"]["CommercialPropertyStructure"][0])
    struct["EQClass"] = "A1"          # see the trap above -- required here, not on PP
    # A SECOND finding, found only by running: PersonalPropertyRules' own
    # SetSoftStoryModificationFactor/SetEQSprinkleredRiskFactor/
    # SetBldgHeightFactor/SetBCEGEQFactor are ALSO ancestor-copies of the
    # Structure's own already-computed values (`../../<field>`), the same
    # shape C10-06 found for Business Income but did not name for Contents
    # (it only diffed the 9 EQ-ENGINE rule names, not these four factor
    # rules). Left unset, the Structure's own `SprinklerSystem`/`BCEG` are
    # blank, which reproduces the golden case's own finding-3 trap
    # (`EQSprinkleredRiskFactor` -> 1.06, not the genuine 1.0) one level up
    # -- so the Structure needs the SAME no-op inputs the golden case gave
    # Building, even though this submission never elects EQ on the
    # Structure's own Building coverage.
    struct["SprinklerSystem"] = "None"
    struct["BCEG"] = "1"
    pp_rec = (struct["CommercialPropertyOccupClassTable"]["CommercialPropertyOccupClass"][0]
              ["CommercialPropertyPersonalPropertyTable"]["CommercialPropertyPersonalProperty"][0])
    pp_rec.update(EQ_ELECTION)
    pp_rec["EQGrade"] = "1"
    return sub


def contents_predict(book):
    eq_base = Decimal(str(table_value(book, "EQLossCostPrsnlProp", "LossCost",
                                       StateCode="OR", EQClass="A1", EQTerr="1",
                                       EQGrade="1")))
    eq_rate = (eq_base * Decimal("1.0")).quantize(Decimal("0.001"))
    eq_col_adj = eq_rate  # no-op factors, same as Building
    coins = Decimal("0.95")  # CoinsuranceFactor[CW]("90%") -- shared table, C10-01 finding C
    adj = (eq_col_adj * coins).quantize(Decimal("0.001"))
    ded = Decimal(str(table_value(book, "EQPercentageDeductibleFactor", "Factor",
                                   StateCode="OR", EQDeductibleTier=1, EQClass="A1",
                                   EQDeductible="10%")))
    final = (adj * ded).quantize(Decimal("0.001"))
    limit = Decimal(100_000)
    prem = (final * limit / 100).quantize(Decimal("1"))
    return {
        "EQBaseRate": eq_base, "EQRate": eq_rate,
        "EQCauseOfLossAdjustment": eq_col_adj, "EQCoinsuranceFactor": coins,
        "AdjustedEQRate": adj, "EQDeductibleFactor": ded,
        "FinalEQRate": final, "Premium": prem,
    }


CONTENTS_PP = (chunk4.PP + "[1]")
CONTENTS_ENDT = (chunk4.PP.rsplit("/", 1)[0] + "/CommercialPropertyPersonalProperty[1]"
                  "/CommercialPropertyEarthquakeAndVolcanicEruptionEndorsementPrsnlPropTable"
                  "/CommercialPropertyEarthquakeAndVolcanicEruptionEndorsementPrsnlProp[1]")


# ------------------------------------------------------------- BUSINESS INC
# SetEQRate for Business Income reads ../../EQBaseRate (Structure's, 0.009)
# times its OWN LossCostMultiplier and FOUR MORE ../../ factors (Structure's
# SoftStoryModificationFactor/EQSprinkleredRiskFactor/BldgHeightFactor/
# BuildersRiskEQFactor -- all confirmed no-op 1.0 by the golden case) and a
# LOCAL BCEGEQFactor that itself just copies ../../BCEGEQFactor (also 1.0).
# SetEQFactor, absent a sub-limit record, copies the ORDINARY Factor field
# -- chunk 5's own 0.55 TypeOfRiskFactor for this exact CovType/TypeOfRisk/
# Coinsurance combination.

def business_income_submission():
    sub = chunk5.submission("Basic")
    _loc(sub).update(LOC_EQ)
    struct = (sub["CommercialPropertyTable"]["CommercialProperty"][0]
              ["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0]
              ["CommercialPropertyStructureTable"]["CommercialPropertyStructure"][0])
    struct.update(EQ_ELECTION)
    bi_rec = struct["CommercialPropertyBusinessIncomeTable"]["CommercialPropertyBusinessIncome"][0]
    bi_rec["EQCovIndicator"] = "Yes, Not Included in Blanket"
    return sub


def business_income_predict():
    eq_base = Decimal("0.009")            # Structure's own EQBaseRate, golden case
    eq_rate = (eq_base * Decimal("1.0")).quantize(Decimal("0.001"))  # x LCM x five 1.0 no-ops
    col_adj = eq_rate                     # x StoryModFactor(1) x BuildersRiskFactor(1)
                                           #   x EQSprinklerLeakageOnlyBldgFactor(1)
    eq_factor = Decimal("0.55")           # copy of ordinary Factor (chunk 5's TypeOfRiskFactor)
    final = (col_adj * eq_factor).quantize(Decimal("0.001"))
    limit = Decimal(100_000)
    prem = (final * limit / 100).quantize(Decimal("1"))
    return {"EQBaseRate_ancestor": eq_base, "EQRate": eq_rate,
            "EQCauseOfLossAdjustment": col_adj, "EQFactor": eq_factor,
            "FinalEQRate": final, "Premium": prem}


BI_REC = chunk5.BI + "[1]"
BI_ENDT = chunk5.BI + ("[1]/CommercialPropertyEarthquakeAndVolcanicEruptionEndorsementBusnIncomeTable"
                       "/CommercialPropertyEarthquakeAndVolcanicEruptionEndorsementBusnIncome[1]")


# ------------------------------------------------------------- SPECIAL CLASS
# Special Class runs its OWN SetEQBaseRate/SetEQRate/SetEQClassToUse/
# SetEQDeductibleFactor -- the same shape Building's chain has, just on the
# Special Class item (a LOCATION sibling, not a Structure).

def special_class_submission():
    sub = chunk6.submission("Basic")
    _loc(sub).update(LOC_EQ)
    item = chunk6.item(sub)
    item.update(EQ_ELECTION)
    return sub


def special_class_predict(book):
    eq_base = Decimal(str(table_value(book, "EQLossCostBldg", "LossCost",
                                       StateCode="OR", EQClass="A1", EQTerr="1")))
    eq_rate = (eq_base * Decimal("1.0")).quantize(Decimal("0.001"))
    col_adj = eq_rate                      # no sprinkler-leakage-only term elected
    class_to_use = table_value(book, "EQClassToUse", "EQClassToUse",
                                StateCode="CW", EQClass="A1")
    ded = Decimal(str(table_value(book, "EQPercentageDeductibleFactor", "Factor",
                                   StateCode="OR", EQDeductibleTier=1,
                                   EQClass=class_to_use, EQDeductible="10%")))
    final = (col_adj * ded).quantize(Decimal("0.001"))
    limit = Decimal(100_000)
    prem = (final * limit / 100).quantize(Decimal("1"))
    return {"EQBaseRate": eq_base, "EQRate": eq_rate,
            "EQCauseOfLossAdjustment": col_adj, "EQClassToUse": class_to_use,
            "EQDeductibleFactor": ded, "FinalEQRate": final, "Premium": prem}


SC_ITEM = chunk6.SC + "[1]"
SC_ENDT = chunk6.SC + ("[1]/CommercialPropertyEarthquakeAndVolcanicEruptionEndorsementSpecialClassTable"
                      "/CommercialPropertyEarthquakeAndVolcanicEruptionEndorsementSpecialClass[1]")


# --------------------------------------------------------- SC BUSN INCOME
# The exact mirror of Business Income one datadef group down: SetEQRate
# copies ../../EQRate (the Special Class item's OWN EQRate this time, not
# Building's), and SetEQFactor copies the ordinary Factor (chunk 7's own
# BusnIncomeFactor for the SAME CovType/TypeOfRisk/Coinsurance combination
# Business Income used -- 0.55, since chunk 7's own case reuses chunk 5's
# RECORD dict verbatim).

def scbi_submission():
    sub = chunk6.submission("Basic")
    _loc(sub).update(LOC_EQ)
    item = chunk6.item(sub)
    item.update(EQ_ELECTION)
    rec = dict(chunk7.RECORD, CauseOfLoss="Basic")
    rec["EQCovIndicator"] = "Yes, Not Included in Blanket"
    item["CommercialPropertySpecialClassBusnIncomeTable"] = {
        "CommercialPropertySpecialClassBusnIncome": [rec],
    }
    return sub


def scbi_predict(sc_predict):
    eq_rate = sc_predict["EQRate"]          # ../../EQRate, the Special Class item's own
    col_adj = eq_rate                       # x StoryModFactor(1) x BuildersRiskFactor(1) x
                                             #   EQSprinklerLeakageOnlyBldgFactor(1), all no-op
    eq_factor = Decimal("0.55")             # copy of ordinary Factor -- chunk 7's own value
    final = (col_adj * eq_factor).quantize(Decimal("0.001"))
    limit = Decimal(100_000)
    prem = (final * limit / 100).quantize(Decimal("1"))
    return {"EQRate_ancestor": eq_rate, "EQCauseOfLossAdjustment": col_adj,
            "EQFactor": eq_factor, "FinalEQRate": final, "Premium": prem}


SCBI_REC = chunk6.SC + ("[1]/CommercialPropertySpecialClassBusnIncomeTable"
                        "/CommercialPropertySpecialClassBusnIncome[1]")
SCBI_ENDT = SCBI_REC + ("/CommercialPropertyEarthquakeAndVolcanicEruptionEndorsementSpclClassBusnIncomeTable"
                        "/CommercialPropertyEarthquakeAndVolcanicEruptionEndorsementSpclClassBusnIncome[1]")


def run_group(book, label, build, checks):
    print(f"=== {label}")
    ip = Interpreter(book, rounding=ROUNDING, trace=False,
                      null_arithmetic=NULL_ARITHMETIC)
    data = Node.from_dict(f"MasterCF{JURIS}", build())
    try:
        ip.run(data)
    except Exception as exc:
        print(f"    RAISED {type(exc).__name__}: {exc}")
        return False
    ok = True
    for clabel, path, want in checks:
        got = read(path, data)
        try:
            good = got is not None and Decimal(got) == Decimal(want)
        except Exception:
            good = got == want
        ok &= good
        flag = "" if good else f"   <-- expected {want}"
        print(f"    {clabel:32s} = {str(got):>10s}{flag}")
    if ip.messages:
        print(f"    ISO validation messages ({len(ip.messages)})")
    print()
    return ok


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--trace", action="store_true")
    a = ap.parse_args()

    book = book_for(JURIS, ASOF)
    print(f"{book}\n")

    ok = True

    c = contents_predict(book)
    print("Contents hand-derivation:", {k: str(v) for k, v in c.items()})
    ok &= run_group(book, "Contents (Personal Property)", contents_submission, [
        ("EQBaseRate", CONTENTS_PP + "/EQBaseRate", str(c["EQBaseRate"])),
        ("EQRate", CONTENTS_PP + "/EQRate", str(c["EQRate"])),
        ("EQCauseOfLossAdjustment", CONTENTS_PP + "/EQCauseOfLossAdjustment", str(c["EQCauseOfLossAdjustment"])),
        ("EQCoinsuranceFactor", CONTENTS_PP + "/EQCoinsuranceFactor", str(c["EQCoinsuranceFactor"])),
        ("AdjustedEQRate", CONTENTS_PP + "/AdjustedEQRate", str(c["AdjustedEQRate"])),
        ("EQDeductibleFactor", CONTENTS_PP + "/EQDeductibleFactor", str(c["EQDeductibleFactor"])),
        ("FinalEQRate", CONTENTS_PP + "/FinalEQRate", str(c["FinalEQRate"])),
        ("Endorsement Premium", CONTENTS_ENDT + "/Premium", str(c["Premium"])),
        ("Ordinary BasicGroupI Premium (regression)",
         CONTENTS_PP + "/CommercialPropertyPersonalPropertyPrsnlPropBasicGroupICoverage/Premium", "223"),
    ])

    bi = business_income_predict()
    print("Business Income hand-derivation:", {k: str(v) for k, v in bi.items()})
    ok &= run_group(book, "Business Income", business_income_submission, [
        ("EQRate", BI_REC + "/EQRate", str(bi["EQRate"])),
        ("EQCauseOfLossAdjustment", BI_REC + "/EQCauseOfLossAdjustment", str(bi["EQCauseOfLossAdjustment"])),
        ("EQFactor", BI_REC + "/EQFactor", str(bi["EQFactor"])),
        ("FinalEQRate", BI_REC + "/FinalEQRate", str(bi["FinalEQRate"])),
        ("Endorsement Premium", BI_ENDT + "/Premium", str(bi["Premium"])),
        ("Ordinary BasicGroupI Premium (regression)",
         BI_REC + "/CommercialPropertyBusinessIncomeBasicGroupICoverage/Premium", "112"),
    ])

    sc = special_class_predict(book)
    print("Special Class hand-derivation:", {k: str(v) for k, v in sc.items()})
    ok &= run_group(book, "Special Class", special_class_submission, [
        ("EQBaseRate", SC_ITEM + "/EQBaseRate", str(sc["EQBaseRate"])),
        ("EQRate", SC_ITEM + "/EQRate", str(sc["EQRate"])),
        ("EQCauseOfLossAdjustment", SC_ITEM + "/EQCauseOfLossAdjustment", str(sc["EQCauseOfLossAdjustment"])),
        ("EQClassToUse", SC_ITEM + "/EQClassToUse", sc["EQClassToUse"]),
        ("EQDeductibleFactor", SC_ITEM + "/EQDeductibleFactor", str(sc["EQDeductibleFactor"])),
        ("FinalEQRate", SC_ITEM + "/FinalEQRate", str(sc["FinalEQRate"])),
        ("Endorsement Premium", SC_ENDT + "/Premium", str(sc["Premium"])),
        ("Ordinary BasicGroupI Premium (regression)",
         SC_ITEM + "/CommercialPropertySpecialClassBasicGroupICoverage/Premium", "66"),
    ])

    scbi = scbi_predict(sc)
    print("SC Business Income hand-derivation:", {k: str(v) for k, v in scbi.items()})
    ok &= run_group(book, "SC Business Income", scbi_submission, [
        ("EQRate", SCBI_REC + "/EQRate", str(scbi["EQRate_ancestor"])),
        ("EQCauseOfLossAdjustment", SCBI_REC + "/EQCauseOfLossAdjustment", str(scbi["EQCauseOfLossAdjustment"])),
        ("EQFactor", SCBI_REC + "/EQFactor", str(scbi["EQFactor"])),
        ("FinalEQRate", SCBI_REC + "/FinalEQRate", str(scbi["FinalEQRate"])),
        ("Endorsement Premium", SCBI_ENDT + "/Premium", str(scbi["Premium"])),
        ("Ordinary BasicGroupI Premium (regression)",
         SCBI_REC + "/CommercialPropertySpecialClassBusnIncomeBasicGroupICoverage/Premium", "39"),
    ])

    print()
    if ok:
        print("All four groups' EQ chain matches its hand derivation -- "
              "C10-06's ancestor-copy and differently-keyed-table claims "
              "confirmed by running, not just reading. No engine gap.")
        return 0
    print("MISMATCH above -- see printed values. Not patched here if it "
          "traces to engine code, per this project's standing rule.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
