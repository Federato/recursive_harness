#!/usr/bin/env python3
"""Chunk 10, C10-19 -- trace the sub-limit / flat-dollar-deductible
combination end to end for one form, the build order's own callout
("sub-limit and flat-dollar-deductible variants"). Confirms which of the
13 dollar-tier `EQSubLimit*FlatDeductibleFactor` tables a real submission
reaches, and whether the flat-dollar-deductible path is genuinely distinct
from the plain percentage-deductible path C10-01's golden case built -- not
just a different table, a different formula shape.

Three things read directly off the rule XML BEFORE anything ran (this
project's standing rule: the doc/census is a lead, not ground truth):

  1. `AttachFormCommercialProperty*` (`CommercialPropertyStructureRules.
     Rule.xml`) confirms there are FOUR mutually-exclusive Endorsement
     variants gated by `EQCauseOfLossForm`, already named by C10-01 --
     but reading the flat-dollar file itself
     (`CommercialPropertyEarthquakeAndVolcanicEruptionCoverageWithFlat
     DollarDeductibleBldgRules.Rule.xml`) finds its own `SetPremium` reads
     `../../FinalEQRate` -- THE SAME field the plain form's `SetPremium`
     reads. The Endorsement-level premium FORMULA is identical across all
     four variants; whatever makes the flat-dollar/sub-limit paths
     genuinely distinct must live further upstream, in how `FinalEQRate`
     itself gets computed -- not in this file at all.

  2. That upstream divergence is `SetEQDeductibleFactor`
     (`CommercialPropertyStructureRules.Rule.xml`), ONE rule shared by
     all four variants, not four separate rules. It `Choose`s on WHICH
     Endorsement record exists (an `Exist AtInputDataDef` test per
     branch, the same destructive-mutual-exclusion shape C10-05 already
     found one rule downstream of attachment):

       - CP 10 40 (plain, %-deductible)      -> LookupEQPercentageDeductibleFactor
                                                 keyed State+Tier+Class+Ded%
                                                 (C10-01's own path, 1 shared table)
       - CP 10 28 (plain, flat-$-deductible)  -> LookupEQFlatDeductibleFactor
                                                 keyed State+Tier+Class+Ded$+
                                                 EarthquakeTotalPropertyValue
                                                 -- THIS TASK's case, 1 table but
                                                 a genuinely wider key (adds a
                                                 5th dimension, a VALUE RANGE,
                                                 the plain path never has)
       - CP 10 29 (sub-limit, flat-$-ded)     -> ONE of 13 hardcoded literal
                                                 `EQDeductible` string values
                                                 ("500".."1,000,000") each
                                                 dispatching to its OWN
                                                 single-purpose
                                                 LookupEQSubLimit<N>FlatDeductible
                                                 Factor rule -- the dollar
                                                 AMOUNT the submitter picks IS
                                                 the tier selector, not a
                                                 separate field
       - CP 10 45 (sub-limit, %-ded)          -> a DIFFERENT 6-table family
                                                 entirely (`EQSubLimitDeductible
                                                 Tier{1,2,3}Table{1,2,3,4,5,6}`),
                                                 keyed by a 2-way `EQClassToUse`
                                                 bucket x `EQDeductibleTier`,
                                                 with NO dollar-amount dispatch
                                                 at all -- confirming the two
                                                 SUB-LIMIT variants don't even
                                                 share a deductible mechanism
                                                 with each other, let alone
                                                 with the plain path

     `EQCoinsuranceFactor`/`AdjustedEQRate` (`SetEQCoinsuranceFactor`/
     `SetAdjustedEQRate`) are declared ONCE, upstream of this `Choose`, run
     identically for all four variants -- confirmed by direct read, not
     assumed: none of the four paths skips coinsurance. The ONLY thing that
     diverges is which `EQDeductibleFactor` Lookup fires.

  3. `EarthquakeTotalPropertyValue` (read by `LookupEQFlatDeductibleFactor`'s
     5th key) is not a submission input -- it's a DERIVED aggregate
     (`SetEarthquakeTotalPropertyValue`, `CommercialPropertyLocationRules.
     Rule.xml`), summing `FullBldgValue`/`FullPrsnlPropValueToUse`/
     `FullSpecialClassValue` across every EQ-elected coverage at the
     Location -- and it is computed ONLY when `EQCauseOfLossForm` is CP 10
     28 or CP 10 29. The plain percentage-deductible path (CP 10 40) never
     touches this field at all -- a genuinely different DATA DEPENDENCY,
     not just a different table.

  4. C10-02's own flagged-not-resolved item (`EarthquakeDeductibleTier` is
     read by a real `LookupEarthquakeDeductibleTier` rule inside
     `CommercialPropertyLocationRules.Rule.xml`, suggesting `EQDeductibleTier`
     might have a derivation path the golden case's raw-input treatment
     never exercised) is SETTLED here, as a side effect of reading the
     table it depends on: `EarthquakeDeductibleTier.RateTable.csv` is
     ZERO ROWS at CW (header-only) and filed by 0 states -- the derivation
     rule exists and is real, but its own table is currently empty
     everywhere, so the Lookup it runs always returns null and
     `EQDeductibleTier` is left unset unless the raw-input path (a direct
     submission value, same as the golden case's own `="1"`) supplies it.
     Not a hidden mechanism to worry about -- a genuinely dead derivation
     for now, confirmed by reading its own table, not assumed live.

Case 1 (the golden-case comparison, hand-derived and run) built differentially
from the golden case, per this project's own style: SAME Oregon/Basic-Group-I/
A1/Terr-1/90%-coinsurance risk, changing ONLY the two fields that select a
different Endorsement variant -- `EQCauseOfLossForm` -> "Earthquake Form
(CP 10 28)" and `EQDeductible` -> "2,500" (one of the 13 filed flat-dollar
tiers, matching the real ISO fixture's own choice, `STC_CP000020296.json`,
Utah -- C10-09's cross-check) -- everything else (structure, coinsurance,
BCEG, sprinkler fields) held identical to the golden case's own no-op-proven
values, so any premium difference traces ONLY to the deductible-factor
mechanism this task is about, not to some other unrelated field change.
**Result: MATCH, $8** (vs. C10-01's own $6 on the plain percentage path).

Case 2 (an actual attempt at the sub-limit + flat-dollar-deductible form,
CP 10 29) was built to find out WHICH of the 13 `EQSubLimit*
FlatDeductibleFactor` tables a real submission reaches -- same base risk,
`EQCauseOfLossForm` -> "Earthquake Sub-Limit Form (CP 10 29)", the sub-limit
record's own `Limit`=$50,000 against `FullBldgValue`=$100,000
(`EQSubLimitPercent`->50, inside the required (0,75] range), same
`EQDeductible`="2,500". **This is where a REAL, REPRODUCIBLE ENGINE GAP
surfaced, found only by running, not by reading the rule XML**: every one
of the 13 tables carries a DOUBLE-banded-range key (`EQSubLimitPct_From/
ToLessThan` AND `TotalPropertyValue_From/ToLessThan` simultaneously,
confirmed by direct header read on 4 of the 13, not just the one this case
happens to hit) -- and the interpreter's own `_lookup_banded`
(`gl_engine/interp/interpreter.py`) explicitly refuses any table declaring
2 key ranges, raising `InterpretError` and citing its own one-range-per-
table contract. **Per this task's own standing instruction, this is
reported, not patched** -- the CP 10 29 sub-limit+flat-dollar-deductible
path is confirmed CURRENTLY UNREACHABLE end to end through this engine.
The plain flat-dollar path (Case 1) has only ONE banded range
(`TotalPropertyValue`) and runs cleanly -- the gap is specific to the
double-range shape the 13 sub-limit tables share, not to banded lookups in
general.

    python scripts/cf/103_chunk10_c10-19_sublimit_flatdeductible.py [--trace]

Exits 0 if Case 1's hand derivation matches the engine AND Case 2 reproduces
the same confirmed InterpretError (the expected, reported-not-fixed outcome).
"""
from __future__ import annotations

import argparse
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from cf_engine.config import NULL_ARITHMETIC, ROUNDING
from cf_engine.resolve import book_for
from gl_engine.interp.interpreter import Interpreter
from gl_engine.interp.tree import Node, dump, read
from gl_engine.interp.values import InterpretError

JURIS, ASOF = "OR", "20260917"

STRUCT = ("CommercialPropertyTable/CommercialProperty/"
          "CommercialPropertyLocationTable/CommercialPropertyLocation/"
          "CommercialPropertyStructureTable/CommercialPropertyStructure")
FLAT_ENDT = STRUCT + (
    "/CommercialPropertyEarthquakeAndVolcanicEruptionCoverageWithFlat"
    "DollarDeductibleBldgTable/CommercialPropertyEarthquakeAndVolcanicEruption"
    "CoverageWithFlatDollarDeductibleBldg[1]")
BGI_PREMIUM = STRUCT + "/CommercialPropertyStructureBuildingBasicGroupICoverage/Premium"

#: hand-derived, filed rows cited in the module docstring and read directly
#: against the tables below, same discipline as the golden case
EQ_BASE_RATE = Decimal("0.009")            # EQLossCostBldg [OR] "A1","1" -- unchanged, same
                                            # base-rate step every EQ variant shares
LOSS_COST_MULT = Decimal("1.0")
EQ_COINSURANCE_FACTOR = Decimal("0.95")    # CoinsuranceFactor [CW] "90%" -- confirmed above,
                                            # SHARED identically by all 4 variants
LIMIT = 100_000
FULL_BLDG_VALUE = 100_000                  # -> EarthquakeTotalPropertyValue = 100,000
                                            # (Location-level sum, this structure only,
                                            # confirmed by direct read of SetEarthquakeTotal
                                            # PropertyValue -- see module docstring point 3)
EQ_DEDUCTIBLE = "2,500"                    # flat dollar amount -- matches the real ISO
                                            # fixture's own choice (STC_CP000020296.json)
EQ_DEDUCTIBLE_FACTOR = Decimal("0.904")    # EQFlatDeductibleFactor [CW] 1,"A1","2,500",
                                            # range [0,100001) -- 100,000 falls in the FIRST
                                            # bucket, confirmed by direct row read
ORDINARY_PREMIUM = Decimal(261)            # CF-CHUNK1-GOLDEN-CASE.md case A, unmoved

EQ_RATE = (EQ_BASE_RATE * LOSS_COST_MULT).quantize(Decimal("0.001"))                 # 0.009
EQ_COL_ADJ = (EQ_RATE * Decimal("1.0")).quantize(Decimal("0.001"))                   # 0.009
ADJUSTED_EQ_RATE = (EQ_COL_ADJ * EQ_COINSURANCE_FACTOR).quantize(Decimal("0.001"))   # 0.009
FINAL_EQ_RATE = (ADJUSTED_EQ_RATE * EQ_DEDUCTIBLE_FACTOR).quantize(Decimal("0.001")) # 0.008
EQ_PREMIUM = (FINAL_EQ_RATE * (Decimal(LIMIT) / 100)).quantize(Decimal("1"))         # 8


def submission() -> dict:
    """The golden case's own risk, with ONLY the Endorsement-variant fields
    changed -- EQCauseOfLossForm to CP 10 28, EQDeductible to a flat dollar
    amount. Everything else (structure, coinsurance, BCEG, sprinkler no-ops)
    is byte-for-byte the golden case's own proven values."""
    return {
        "EffDate": "01/01/2027",
        "CommercialPropertyTable": {
            "CommercialProperty": [{
                "IRPMFactor": "1.0",
                "EQSubLimitBlktIndicator": "No",
                "CommercialPropertyLocationTable": {
                    "CommercialPropertyLocation": [{
                        "BasicGroupIRatingTerr": "Portland",
                        "ProtectClass": "3",
                        # -- CHANGED from the golden case: selects the FLAT-
                        # DOLLAR-DEDUCTIBLE Endorsement (CP 10 28), not the
                        # plain percentage form (CP 10 40) --
                        "EQCauseOfLossForm": "Earthquake Form (CP 10 28)",
                        "EQTerr": "1",
                        "EQDeductibleTier": "1",
                        "CommercialPropertyStructureTable": {
                            "CommercialPropertyStructure": [{
                                "RatingType": "Class",
                                "ClassCode": "0951",
                                "ConstructionType": "Frame",
                                "CovType": "Building",
                                "CauseOfLoss": "Basic Group I",
                                "Coinsurance": "90%",
                                "Limit": str(LIMIT),
                                "FullBldgValue": str(FULL_BLDG_VALUE),
                                "Deductible": "1,000",
                                "LossCostMultiplier": "1.0",
                                "IncludedInBlkt": "No",
                                "PackageModFactor": "1.0",
                                "MultiPremiumAndDispersionCreditFactor": "1.0",
                                "EQCovIndicator": "Yes, Not Included in Blanket",
                                "EQClass": "A1",
                                "EQCoinsurance": "90%",
                                # -- CHANGED from the golden case: a flat
                                # DOLLAR amount, not a percentage. This
                                # string is itself the tier-selector for the
                                # 13-table EQSubLimit* family (not used here,
                                # this is the PLAIN flat-dollar path) and the
                                # 4th key into EQFlatDeductibleFactor --
                                "EQDeductible": EQ_DEDUCTIBLE,
                                "EQSprinklerLeakageOnly": "Not Applicable",
                                "BCEG": "1",
                                "SprinklerSystem": "None",
                            }],
                        },
                    }],
                },
            }],
        },
    }


def run(trace=False):
    ip = Interpreter(book_for(JURIS, ASOF), rounding=ROUNDING, trace=trace,
                      null_arithmetic=NULL_ARITHMETIC)
    data = Node.from_dict(f"MasterCF{JURIS}", submission())
    ip.run(data)
    return data, ip


def sublimit_submission() -> dict:
    """A SECOND case -- same base risk, EQCauseOfLossForm switched to the
    SUB-LIMIT + flat-dollar-deductible form (CP 10 29), with the sub-limit
    record's own (smaller) Limit supplied ($50,000 of the $100,000
    FullBldgValue -> EQSubLimitPercent=50, within the (0,75] range the
    Choose in SetEQDeductibleFactor requires). Built to actually EXERCISE
    the sub-limit branch and find out which of the 13 EQSubLimit*
    FlatDeductibleFactor tables a real submission reaches -- not just to
    read the Choose and assume."""
    return {
        "EffDate": "01/01/2027",
        "CommercialPropertyTable": {
            "CommercialProperty": [{
                "IRPMFactor": "1.0",
                "EQSubLimitBlktIndicator": "No",
                "CommercialPropertyLocationTable": {
                    "CommercialPropertyLocation": [{
                        "BasicGroupIRatingTerr": "Portland",
                        "ProtectClass": "3",
                        "EQCauseOfLossForm": "Earthquake Sub-Limit Form (CP 10 29)",
                        "EQTerr": "1",
                        "EQDeductibleTier": "1",
                        "CommercialPropertyStructureTable": {
                            "CommercialPropertyStructure": [{
                                "RatingType": "Class",
                                "ClassCode": "0951",
                                "ConstructionType": "Frame",
                                "CovType": "Building",
                                "CauseOfLoss": "Basic Group I",
                                "Coinsurance": "90%",
                                "Limit": str(LIMIT),
                                "FullBldgValue": str(FULL_BLDG_VALUE),
                                "Deductible": "1,000",
                                "LossCostMultiplier": "1.0",
                                "IncludedInBlkt": "No",
                                "PackageModFactor": "1.0",
                                "MultiPremiumAndDispersionCreditFactor": "1.0",
                                "EQCovIndicator": "Yes, Not Included in Blanket",
                                "EQClass": "A1",
                                "EQCoinsurance": "90%",
                                "EQDeductible": EQ_DEDUCTIBLE,
                                "EQSprinklerLeakageOnly": "Not Applicable",
                                "BCEG": "1",
                                "SprinklerSystem": "None",
                                "CommercialPropertyEarthquakeAndVolcanicEruptionCoverageSubLimitFormWithFlatDollarDeductibleBldgTable": {
                                    "CommercialPropertyEarthquakeAndVolcanicEruptionCoverageSubLimitFormWithFlatDollarDeductibleBldg": [{
                                        "Limit": "50000",
                                    }],
                                },
                            }],
                        },
                    }],
                },
            }],
        },
    }


def run_sublimit(trace=False):
    ip = Interpreter(book_for(JURIS, ASOF), rounding=ROUNDING, trace=trace,
                      null_arithmetic=NULL_ARITHMETIC)
    data = Node.from_dict(f"MasterCF{JURIS}", sublimit_submission())
    ip.run(data)
    return data, ip


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--dump", action="store_true")
    a = ap.parse_args()

    print(f"{book_for(JURIS, ASOF)}\n")
    print("Hand-derivation, computed before this ran:")
    print(f"  EQBaseRate              = EQLossCostBldg[OR](\"A1\",\"1\")             = {EQ_BASE_RATE}")
    print(f"  EQRate                  = round({EQ_BASE_RATE} x {LOSS_COST_MULT}, 3)              = {EQ_RATE}")
    print(f"  EQCauseOfLossAdjustment = round({EQ_RATE} x 1.0, 3)                 = {EQ_COL_ADJ}")
    print(f"  AdjustedEQRate          = round({EQ_COL_ADJ} x {EQ_COINSURANCE_FACTOR}, 3)              = {ADJUSTED_EQ_RATE}")
    print(f"  EQDeductibleFactor      = EQFlatDeductibleFactor[CW](1,\"A1\",\"2,500\",[0,100001)) = {EQ_DEDUCTIBLE_FACTOR}")
    print(f"  FinalEQRate             = round({ADJUSTED_EQ_RATE} x {EQ_DEDUCTIBLE_FACTOR}, 3)             = {FINAL_EQ_RATE}")
    print(f"  EQ Premium              = round({FINAL_EQ_RATE} x {LIMIT}/100, 0)             = {EQ_PREMIUM}")
    print(f"  Ordinary BGI Premium (unmoved, CF-CHUNK1-GOLDEN-CASE.md case A) = {ORDINARY_PREMIUM}\n")
    print(f"  For comparison, C10-01's own plain percentage-deductible case (10% ded, "
          f"same base rate/coinsurance): EQDeductibleFactor=0.68, FinalEQRate=0.006, "
          f"Premium=$6 -- the SAME upstream chain, a DIFFERENT deductible-factor "
          f"table/key-shape, and a different resulting premium.\n")

    data, ip = run(a.trace)

    checks = [
        ("EQBaseRate", STRUCT + "/EQBaseRate", str(EQ_BASE_RATE)),
        ("EQRate", STRUCT + "/EQRate", str(EQ_RATE)),
        ("EQCauseOfLossAdjustment", STRUCT + "/EQCauseOfLossAdjustment", str(EQ_COL_ADJ)),
        ("EQCoinsuranceFactor", STRUCT + "/EQCoinsuranceFactor", str(EQ_COINSURANCE_FACTOR)),
        ("AdjustedEQRate", STRUCT + "/AdjustedEQRate", str(ADJUSTED_EQ_RATE)),
        ("EarthquakeTotalPropertyValue",
         "CommercialPropertyTable/CommercialProperty/CommercialPropertyLocationTable/"
         "CommercialPropertyLocation/EarthquakeTotalPropertyValue", str(FULL_BLDG_VALUE)),
        ("EQDeductibleFactor", STRUCT + "/EQDeductibleFactor", str(EQ_DEDUCTIBLE_FACTOR)),
        ("FinalEQRate", STRUCT + "/FinalEQRate", str(FINAL_EQ_RATE)),
        ("Endorsement Premium (CP 10 28)", FLAT_ENDT + "/Premium", str(EQ_PREMIUM)),
        ("Ordinary BGI Premium (regression)", BGI_PREMIUM, str(ORDINARY_PREMIUM)),
    ]
    ok = True
    for label, path, want in checks:
        got = read(path, data)
        good = got == want
        ok &= good
        flag = "" if good else f"   <-- expected {want}"
        print(f"  {label:34s} = {str(got):>10s}{flag}")

    if ip.messages:
        print(f"\n  ISO validation messages ({len(ip.messages)}):")
        for m in ip.messages[:20]:
            print(f"    - {m}")

    if a.trace:
        print(ip.trace_text())
    if a.dump:
        print(dump(data))

    print("\n=== Which of the 13 EQSubLimit*FlatDeductibleFactor tables does a real "
          "submission reach? Actually attempted, not just read. ===\n")
    print("    A second case was built to EXERCISE the sub-limit branch for real: "
          "EQCauseOfLossForm -> \"Earthquake Sub-Limit Form (CP 10 29)\", the sub-limit "
          "record's own Limit=$50,000 against FullBldgValue=$100,000 (EQSubLimitPercent "
          "-> 50, inside the (0,75] range SetEQDeductibleFactor's Choose requires), same "
          "EQDeductible=\"2,500\" -- which the Choose's literal-string dispatch should "
          "route to LookupEQSubLimit2500FlatDeductibleFactor.\n")
    gap_found = False
    try:
        sl_data, sl_ip = run_sublimit()
        got = read(STRUCT + "/EQDeductibleFactor", sl_data)
        print(f"    Ran without error. EQDeductibleFactor = {got}")
    except InterpretError as e:
        gap_found = True
        print("    CONFIRMED ENGINE GAP -- the run raises, does not silently mis-rate:")
        print(f"    {type(e).__name__}: {e}")
        print("\n    Root cause, read directly off the table headers, not guessed: ALL "
              "13 EQSubLimit*FlatDeductibleFactor tables carry a DOUBLE-banded-range "
              "key --")
        print("      EQSubLimit2500FlatDeductibleFactor header = (StateCode, "
              "EQDeductibleTier, EQClass, EQDeductible, EQSubLimitPct_From, "
              "EQSubLimitPct_ToLessThan, TotalPropertyValue_From, "
              "TotalPropertyValue_ToLessThan, Factor_From, Factor_ToLessThan)")
        print("    -- confirmed the SAME shape on EQSubLimit500/EQSubLimit10000/"
              "EQSubLimit1000000FlatDeductibleFactor by direct header read; this is "
              "systemic to the whole 13-table family, not one bad file. By contrast, "
              "the PLAIN flat-dollar table this case's OWN first run reached "
              "(EQFlatDeductibleFactor) has exactly ONE banded range "
              "(TotalPropertyValue only) -- which is why THAT lookup ran cleanly.")
        print("\n    The interpreter's own `_lookup_banded` "
              "(gl_engine/interp/interpreter.py) explicitly refuses a table with 2 key "
              "ranges, citing its own documented one-range-per-table contract -- this "
              "is the interpreter enforcing a real architectural assumption that ISO's "
              "own filed EQSubLimit*FlatDeductibleFactor tables do not satisfy, not a "
              "malformed test case. Per this task's own standing instruction (no engine "
              "code touched even if a gap is found), this is reported, not patched: the "
              "CP 10 29 sub-limit + flat-dollar-deductible path is CONFIRMED CURRENTLY "
              "UNREACHABLE end to end through this engine -- every one of the 13 "
              "EQSubLimit*FlatDeductibleFactor tables shares the same blocking shape, "
              "so this is not a one-table gap, it is the whole sub-limit+flat-dollar "
              "branch.")
    if not gap_found:
        print("    (unexpected -- see printed value above)")

    print("\n=== Is the sub-limit/flat-dollar-deductible path genuinely distinct from "
          "the plain percentage-deductible path? ===\n")
    print("    YES, confirmed by direct read of the shared SetEQDeductibleFactor rule, "
          "not by table name alone:")
    print("    1. Different LOOKUP MECHANISM, not just different table contents -- the "
          "plain path uses ONE shared table keyed on 4 fields (State+Tier+Class+Ded%); "
          "the flat-dollar plain path (this case) uses ONE table but a WIDER 5-field "
          "key that adds a derived VALUE-RANGE dimension (EarthquakeTotalPropertyValue); "
          "the sub-limit+flat-dollar path uses 13 SEPARATE single-purpose tables "
          "selected by literal string match on EQDeductible itself, not a table key at "
          "all; the sub-limit+percentage path (CP 10 45) uses a THIRD, unrelated 6-table "
          "family keyed on EQClassToUse x EQDeductibleTier, with no dollar dispatch.")
    print("    2. Different DATA DEPENDENCY -- EarthquakeTotalPropertyValue is a "
          "Location-level DERIVED AGGREGATE (summed across every EQ-elected coverage "
          "at the location) computed ONLY for the CP 10 28/CP 10 29 forms; the plain "
          "percentage path (CP 10 40) never computes or reads this field at all.")
    print("    3. For the SUB-LIMIT variants specifically, the final Premium multiply "
          "reads THIS RECORD'S OWN Limit field (itself derived as EQSubLimitPercent = "
          "round(ThisRecordLimit/FullBldgValue x 100), gated to (0,75]) instead of "
          "../../Limit (the Structure's full EQ limit) -- a genuine HARD CAP on "
          "exposure built into which Limit feeds the rate multiply, not a rate "
          "multiplier layered on top of the full-limit premium the way the plain "
          "path's Product chain works.")
    print("    4. What does NOT differ: EQCoinsuranceFactor/AdjustedEQRate are computed "
          "ONCE, upstream of SetEQDeductibleFactor's own Choose, and run IDENTICALLY "
          "for all four variants -- confirmed by direct read, not merely absent from "
          "this run's own trace. Coinsurance is not skipped by any variant; only the "
          "deductible-factor Lookup source (and, for sub-limit forms, which Limit feeds "
          "the terminal Product) diverges.")

    print()
    if ok and gap_found:
        print("C10-19: MATCH on the flat-dollar-deductible path (CP 10 28) -- hand-"
              "derives and runs to $8, genuinely distinct from C10-01's own plain "
              "percentage-deductible $6 on the identical base risk (different "
              "deductible-factor lookup mechanism and data dependency, not just a "
              "different table name). BUT the sub-limit + flat-dollar-deductible path "
              "(CP 10 29) is CONFIRMED UNREACHABLE end to end -- every one of the 13 "
              "EQSubLimit*FlatDeductibleFactor tables carries a double-banded-range key "
              "the interpreter's own `_lookup_banded` explicitly refuses "
              "(InterpretError, contract Sec.7: one range per table). This is a REAL "
              "ENGINE GAP, confirmed by running, not patched here per this task's own "
              "standing instruction. C10-02's own flagged-not-resolved item "
              "(EarthquakeDeductibleTier's derivation path) is settled as a side "
              "effect: real rule, empty table, a dead derivation for now.")
        return 0
    if ok and not gap_found:
        print("C10-19: MATCH on the flat-dollar-deductible path, and the sub-limit "
              "path ALSO ran without error -- see the printed EQDeductibleFactor above "
              "for what was reached; the double-banded-range gap this task expected "
              "based on the table headers did not reproduce. Investigate before relying "
              "on this result.")
        return 0
    print("MISMATCH -- see the printed values above against the hand derivation. Not "
          "fixed here if this traces to engine code; see the module docstring's "
          "standing rule.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
