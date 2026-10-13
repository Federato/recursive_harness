#!/usr/bin/env python3
"""Gate point 6 -- shared names diffed, not assumed.

The gate says it plainly: *a shared name is a question*. Property has already
been caught filing one rule name in two datadef groups where the two read
DIFFERENT rate tables (`SetSpecialBaseRate`, `SetSpecialTheftExclusionFactor`).
Nothing warns you: both rules exist, both resolve, both return a number.

So this enumerates the whole population rather than checking the two known
cases. For every rule name defined in more than one datadef group, it collects
the rate tables each definition actually reads -- the `MatrixFromConstant` of
every `Lookup` in that rule's own body -- and reports where they disagree.

Two populations are reported separately:

  * **On the chunk 1 chain.** These are the ones that could have made chunk 1's
    golden case wrong. If this list is empty, chunk 1's silence on point 6 is
    an enumerated fact rather than an untested assumption.
  * **Everywhere else.** Reported as the map later chunks inherit, so Contents,
    Business Income and Special Class each start from a list rather than from
    the same discovery.

    python scripts/cf/04_shared_names.py [--juris CW] [--all]

Exit 0 when no chunk 1 chain rule name is ambiguous.
"""
from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from importlib import import_module

from cf_engine.resolve import book_for

golden = import_module("01_golden_case")

#: The rule names chunk 1's golden case actually executes, plus the lookups
#: they call. Taken from the chain in `CauseOfLoss_Building_RatingAlgorithms.md`
#: and the premium branch, not from a guess at what "the chain" means.
CHUNK1_RULES = {
    "SetBGIRatesAndFactors", "SetBasicGroupIBaseRate", "SetBasicGroupIRate",
    "SetBasicGroupICauseOfLossAdjustment", "SetCoinsuranceFactor",
    "SetBasicGroupILOIFactor", "SetAdjustedBasicGroupIRate",
    "SetDeductibleFactorBasicGroupI", "SetFinalBasicGroupIRate",
    "SetProtectionClassFactor", "SetBasicGroupIRatingTerrFactor",
    "SetBasicGroupIRatingTerr", "SetClassCodeToUse", "SetConstructionCode",
    "SetTotAmtInsurance", "SetSprinklerLeakageExclNonSprinkleredBldgRate",
    "SetVacantBuildingRate", "SetSubStdConditionRate", "SetVandalismExclFactor",
    "SetStdPropPolGroupIFactor", "SetPremium", "SetCoverageOnPolicyIndicator",
    "LookupBasicGroupIRate", "LookupRatingTerritoryGroupIFactor",
    "LookupProtectionClassFactor", "LookupCoinsuranceFactor",
    "LookupBasicGroupILOIFactor", "LookupBasicGroupILOIFactorWithArgs",
    "LookupDeductibleFactor", "LookupDeductible250Factor",
    "LookupConstructionCode", "LookupCyberIncidentExclusionFactors",
}


#: The rule names chunk 2's Basic Group II chain executes. Same treatment:
#: taken from the 11-step chain in the algorithms doc and the premium branch,
#: not guessed at.
CHUNK2_RULES = {
    "SetBGIIRatesAndFactors", "SetBasicGroupIINumericValue",
    "SetBasicGroupIIBaseRate", "SetLowestBasicGroupIIBaseRate",
    "SetBasicGroupIIRate", "SetBasicGroupIICauseOfLossAdjustment",
    "SetBasicGroupIICoinsuranceFactor", "SetBasicGroupIILOIFactor",
    "SetAdjustedBasicGroupIIRate", "SetBGIIDeductibleByLocationFactor",
    "SetDeductibleFactorBasicGroupII", "SetFinalBasicGroupIIRate",
    "SetBasicGroupIISymbol", "SetBasicGroupIIRatingTerr", "SetBCEGFactor",
    "SetStdPropPolGroupIIFactor", "SetWindstormOrHailExclFactor",
    "LookupBasicGroupIIRate", "LookupLowestBasicGroupIIRate",
    "LookupBasicGroupIIConstructionSymbol",
    "LookupBasicGroupIISymbolAdditionalClasses",
    "LookupBGIISymbolAdditionalClassesRoofConstruction",
    "LookupBasicGroupIISymbolOilDistributingStations",
    "LookupGroupIINumericValue", "LookupGroupIIOpenSidesNumericValue",
    "LookupBCEGFactor", "LookupWindstormOrHailExclFactor",
    "LookupBasicGroupIIFlatCoinsuranceFactor", "LookupBasicGroupIILOIFactor",
    "LookupBasicGroupIILOIFactorWithArgs",
}

#: The rule names chunk 3's Broad (6 steps) and Special (9 steps) chains
#: execute, from the same algorithms doc. **This is the chunk point 6 was
#: written around** -- `SetSpecialBaseRate` and `SetSpecialTheftExclusionFactor`
#: are the corpus's documented same-name-different-table cases, so the two
#: known traps are expected to appear here rather than being hunted for.
CHUNK3_RULES = {
    # Broad
    "SetBroadRatesAndFactors", "SetBroadBaseRate", "SetBroadRate",
    "SetBroadLOIFactor", "SetAdjustedBroadRate", "SetDeductibleFactorBroad",
    "SetFinalBroadRate", "LookupBroadFormBaseRate",
    # Special
    "SetSpecialRatesAndFactors", "SetSpecialTheftExclusionIndicator",
    "SetSpecialTheftExclusionFactor", "SetSpecialBaseRate", "SetSpecialRate",
    "SetSpecialCauseOfLossAdjustment", "SetSpecialLOIFactor",
    "SetAdjustedSpecialRate", "SetSpecialDeductibleByLocationFactor",
    "SetDeductibleFactorSpecial", "SetFinalSpecialRate",
    "SetSpecialTotAmtInsurance", "SetSpecialIncludingTheftTotAmtInsurance",
    "LookupSpecialBuildingRate", "LookupSpecialBuildersRiskRate",
    "LookupSpecialBldgTheftExclusionFactor",
    # shared by both forms
    "LookupBroadSpecialLOIFactor", "LookupBroadSpecialLOIFactorWithArgs",
    "LookupDeductibleFactor", "LookupDeductible250Factor",
    "LookupDeductibleByLocationFactor", "SetDeductibleByLocationFactor",
    "SetLimitationsOnCovForRoofSurfacingACVFactor",
    "SetMultiResidentialPropSpecialCreditFactor",
    "SetPremium", "SetCoverageOnPolicyIndicator",
}

#: The datadef group chunk 1's golden case actually executes in.
CHUNK4_RULES = {
    "SetBGIRatesAndFactors", "SetBasicGroupIBaseRate", "SetFireSafeVaultFactor",
    "SetProtectionClassFactor", "SetBasicGroupIRate",
    "SetBasicGroupICauseOfLossAdjustment", "SetBasicGroupILOIFactor",
    "SetCoinsuranceFactor", "SetAdjustedBasicGroupIRate",
    "SetDeductibleFactorBasicGroupI", "SetFinalBasicGroupIRate",
    "SetBGIIRatesAndFactors", "SetBasicGroupIIBaseRate",
    "SetBasicGroupIILOIFactor", "SetBroadRatesAndFactors", "SetBroadLOIFactor",
    "SetBroadBaseRate", "SetBroadRate", "SetSpecialRatesAndFactors",
    "SetSpecialBaseRate", "SetSpecialTheftExclusionFactor",
    "SetSpecialLOIFactor", "SetPrsnlPropTerrMultiplier",
    "SetWatchmanCreditFactor", "SetBurglaryAlarmCreditFactor",
    "SetOccupCategory", "SetGroup", "LookupBasicGroupIRate",
    "LookupBasicGroupILOIFactor", "LookupBroadSpecialLOIFactor",
    "LookupSpecialBaseRate", "LookupFireSafeVaultFactor",
}

#: Chunk 5's Business Income chains. Business Income is arithmetically
#: DOWNSTREAM of Building, so several of these resolve to no matrix at all in
#: our group -- which is the finding, not an omission.
CHUNK5_RULES = {
    "SetBGIRatesAndFactors", "SetBGIBaseRateAdjustmentFactor",
    "SetBasicGroupIRate", "SetBasicGroupICauseOfLossAdjustment",
    "SetFinalBasicGroupIRate", "SetFactor", "SetTypeOfRiskFactor",
    "SetBGIIRatesAndFactors", "SetBasicGroupIIBaseRate",
    "SetBasicGroupIICauseOfLossAdjustment", "SetBroadRatesAndFactors",
    "SetBroadBaseRate", "SetBroadRate", "SetSpecialRatesAndFactors",
    "SetSpecialBaseRate", "SetSpecialTheftExclusionFactor",
    "SetCoinsuranceToUse", "LookupBusnIncomeFactor", "LookupBasicGroupIIRate",
    "LookupBroadFormBaseRate",
}

#: Chunk 6's Special Class chains. The rating driver is a free-text class
#: DESCRIPTION resolved through two converter tables, so the names to watch are
#: the two `Lookup*` converters as much as the rate rules themselves.
CHUNK6_RULES = {
    "SetBGIRatesAndFactors", "SetCoinsuranceFactor", "SetBasicGroupIBaseRate",
    "SetBasicGroupIRate", "SetBasicGroupICauseOfLossAdjustment",
    "SetAdjustedBasicGroupIRate", "SetDeductibleFactorBasicGroupI",
    "SetFinalBasicGroupIRate", "SetSpecialClassDescConvertedOption",
    "SetBasicGroupIISymbolNum", "SetBGIIRatesAndFactors",
    "SetBasicGroupIINumericValue", "SetBasicGroupIIBaseRate",
    "SetLowestBasicGroupIIBaseRate", "SetBasicGroupIIRate",
    "SetBasicGroupIICauseOfLossAdjustment", "SetBasicGroupIICoinsuranceFactor",
    "SetFinalBasicGroupIIRate", "SetBroadRatesAndFactors", "SetBroadBaseRate",
    "SetBroadRate", "SetAdjustedBroadRate", "SetDeductibleFactorBroad",
    "SetFinalBroadRate", "SetSpecialRatesAndFactors",
    "SetSpecialTheftExclusionIndicator", "SetSpecialTheftExclusionFactor",
    "SetSpecialBaseRate", "SetSpecialRate", "SetSpecialCauseOfLossAdjustment",
    "SetDeductibleFactorSpecial", "SetFinalSpecialRate",
    "SetProtectionClassFactor", "SetProtectionClassToUse", "SetPolicyType",
    "SetTotAmtInsurance", "SetTotAmtInsuranceToUse",
    "LookupBasicGroupIRateSpecialClass",
    "LookupSpecialClassDescriptionConvertedOption",
    "LookupSpecialClassBasicGroupIINumber", "LookupBroadFormBaseRate",
    "LookupSpecialBuildingRate", "LookupSpecialBldgTheftExclusionFactor",
}

#: Chunk 7's Special Class Business Income chains. Basic Group I and
#: Earthquake have no lookup of their own at all -- they copy the Special Class
#: item's FINISHED rate -- so several of these must resolve to no matrix in our
#: group, which is the finding rather than an omission.
CHUNK7_RULES = {
    "SetBGIRatesAndFactors", "SetBasicGroupIRate",
    "SetBasicGroupICauseOfLossAdjustment", "SetFinalBasicGroupIRate",
    "SetBGIIRatesAndFactors", "SetBasicGroupIIBaseRate",
    "SetLowestBasicGroupIIBaseRate", "SetBasicGroupIIRate",
    "SetBasicGroupIICauseOfLossAdjustment", "SetFinalBasicGroupIIRate",
    "SetBroadRatesAndFactors", "SetBroadBaseRate", "SetBroadRate",
    "SetSpecialRatesAndFactors", "SetSpecialBaseRate", "SetSpecialRate",
    "SetSpecialTheftExclusionFactor", "SetFactor", "SetTypeOfRiskFactor",
    "SetCoinsuranceToUse", "SetEQRate", "LookupBusnIncomeFactor",
    "LookupBasicGroupIIRate", "LookupBroadFormBaseRate",
    "LookupSpecialFormIncldgTheftTimeElementBaseRate",
}

#: Chunk 8's Legal Liability fork. The rate chain is shared with the
#: class-rated path, so the names here are the PREMIUM-side ones plus the two
#: factors that exist only on this branch -- and those two are the point: they
#: are **different names for the same idea in sibling files**.
CHUNK8_RULES = {
    "SetPremium", "SetCoverageOnPolicyIndicator", "CalculateTotalPremium",
    "SetLegalLiabilityFactor", "SetLegalLiabFactor",
    "SetLegalLiabAddlInsurableIntFactor", "LookupLegalLiabilityFactor",
    "LookupAddlInsurableInterestFactor",
    "AttachFormCommercialPropertyLegalLiabilityCoverageForm",
    "InitializeLegalLiality", "SetCovForm", "SetCovType",
}

#: Chunk 9's blanket-rating chain, taken from C9-02's traced
#: `ErcDoBlanketRating` sequence and C9-08/C9-09's dispatcher/value-rule names
#: -- not guessed at. `CommercialPropertyBlanketRatingDetail` is a NEW, 7th
#: datadef group this project has populated, so this is the first time this
#: script's transitive scan has ever looked inside it.
CHUNK9_RULES = {
    # the Detail engine's own 7-step Sequence (C9-02) and the two named rules
    # its averaging fan-out reaches for Basic Group I
    "ErcDoBlanketRating", "SetCounters", "SetPolicyType",
    "ErcSetRiskLevelAverageAndHighestRates", "SetCoinsuranceFactor",
    "SetBldrsRiskFactor", "SetTenPctOfTotalFullValueAmount",
    "SetFinalCalculations", "SetBuildingPPSpecialClassAverageRates",
    "SetBasicGroupIStructureCalc", "SetMaxBasicGroupIStructureCalc",
    "SetMaxBasicGroupICauseOfLossAdjmtRate", "SetBasicGroupIAvgRate",
    "LookupBuildersRiskBlanketFactor", "LookupCoinsuranceFactorBlkt",
    "LookupBldgPrsnlPropBlktCoverageCode", "SetBldgPrsnlPropBlktCoverageCode",
    # the premium-group dispatcher/value rules (C9-08/C9-09) that hand off
    # into the Detail engine above
    "SetBlanketValuesSection", "SetBlanketValues", "SetNonEQBlanketValues",
    "SetEQBlanketValues", "SetPremium",
}

#: The datadef group every chunk so far rates in.
CHUNK1_GROUP = "CommercialPropertyStructure"

#: An ambiguous name on the chunk 1 chain, ADJUDICATED. The gate says a shared
#: name is a question; this is where the answer is written down, and the script
#: fails if an ambiguous chain name has no entry here. Each value is the table
#: that name must resolve to IN CHUNK 1'S DATADEF GROUP, plus why.
#: Three recurring shapes, so the 19 entries below do not each re-argue them.
#:
#:   BLDG_PERSPROP  the name is split Building-side / Personal-Property-side.
#:                  Correct, scoped by datadef group, and the PersProp half is
#:                  what chunk 4 will execute.
#:   ORCHESTRATOR   a `Set*RatesAndFactors` rule: its "matrices" are the union
#:                  of everything its whole chain reaches, so of course they
#:                  differ per coverage. Ambiguity here is an artefact of the
#:                  transitive scan, not a trap -- the question is only whether
#:                  OUR group's union is the set we expect.
#:   NAME_REUSE     an unrelated coverage borrows the rule name. Nothing is
#:                  shared but the string.
BLDG_PERSPROP = "BLDG_PERSPROP"
ORCHESTRATOR = "ORCHESTRATOR"
NAME_REUSE = "NAME_REUSE"

ADJUDICATED = {
    "LookupBasicGroupILOIFactor": (
        "BasicGroupILOIFactorBldg",
        "Nine datadef groups define this name. The five Building-side groups "
        "read `BasicGroupILOIFactorBldg`; the four Personal-Property-side "
        "groups read `BasicGroupILOIFactorPersProp`. That is correct and not a "
        "trap -- the name is scoped by datadef group and the interpreter "
        "dispatches per group. It is recorded because the SAME name reading a "
        "different table is exactly the shape that has already bitten this "
        "corpus elsewhere, and because chunk 4 (Contents) will execute the "
        "OTHER branch of this very name. Verified: chunk 1's golden case C "
        "interpolates 1.150 out of `BasicGroupILOIFactorBldg`."),
    "LookupBasicGroupIILOIFactor": (
        "BasicGroupIILOIFactorBldg",
        "Group II's exact mirror of the Group I entry above, and it splits the "
        "same nine datadef groups the same way -- five Building-side reading "
        "`BasicGroupIILOIFactorBldg`, four Personal-Property-side reading "
        "`BasicGroupIILOIFactorPersProp`. That the two coverages share the "
        "shape is worth recording rather than assuming: it is the reason a "
        "single adjudication habit will carry to chunks 3 and 4 instead of "
        "each rediscovering it. Verified: chunk 2's golden case reads 1.266 "
        "out of `BasicGroupIILOIFactorBldg` at a 100,000 limit.\n"
        "        One real difference from Group I, found while checking: "
        "`BasicGroupIILOIFactorBldg` is keyed on (StateCode, Limit) ONLY. "
        "Group I's is keyed on (StateCode, Limit, ConstructionCode). Same "
        "name shape, same table shape -- one fewer key."),

    # ---- exposed 2026-09-18 by making the scan transitive -----------------
    # Chunks 1 and 2 passed point 6 without these, because a `Set*` rule
    # delegates its lookups and so reported no matrix at all. They are
    # adjudicated here rather than left as a silence those gates inherited.

    "SetBasicGroupIBaseRate": (
        "BasicGroupIRate",
        "**The real one on chunk 1's chain.** Four groups define it and they "
        "read TWO tables: Structure and PersonalProperty read "
        "`BasicGroupIRate`, while SpecialClass and OutdoorTreesShrubsAndPlants "
        "read `BasicGroupIRateSpecialClass`. Same rule name, same datadef "
        "name, different rate table -- the documented trap shape, on the spine "
        "of the build. Chunk 1 is correct because it executes in "
        "`CommercialPropertyStructure`; chunk 6 will execute the other half, "
        "and the build order already warns that Special Class keys on class "
        "DESCRIPTION rather than class code. This entry is why that will not "
        "be a surprise."),
    "SetBasicGroupIRate": (
        None,
        NAME_REUSE + ". Four groups define it -- Mining Properties Business "
        "Income (x2, reading `MiningPropertiesBusnIncomeRate`), Outside Signs "
        "and Radio/TV Antennas (reading `BasicGroupIRateSpecialClass`). "
        "`CommercialPropertyStructure` does not appear in that list at all: "
        "chunk 1's rate step is a pure `Product` of the base rate and the "
        "factors, with no lookup of its own. Reading NOTHING is the right "
        "answer here, and asserting it is what makes the silence mean "
        "something."),
    "SetCoinsuranceFactor": (
        {"CoinsuranceFactor", "LessThan80PctMultiplicativeFactor"},
        "Fourteen groups, three tables. Ours reads `CoinsuranceFactor` and "
        "`LessThan80PctMultiplicativeFactor` -- the second is the branch taken "
        "when coinsurance is under 80%, part of the same rule rather than a "
        "separate step. The divergent groups are worth naming: BlanketRating"
        "Detail and PeakSeasonGeneralInformation read `CoinsuranceFactorBlkt`, "
        "a different table entirely, and AdditionalLocationsSpecialCoinsurance "
        "reads `AddlLocSpclCoinsFactor`. **Confirmed live 2026-09-21 (C9-21)**: "
        "chunk 9's own golden case now populates `CommercialPropertyBlanketRating"
        "Detail`, and its `SetCoinsuranceFactor` reads exactly `CoinsuranceFactor"
        "Blkt` there -- this entry's prediction held to the table name, before "
        "any chunk 9 task ran."),
    "SetBGIRatesAndFactors": (
        {"BasicGroupIRate", "BasicGroupILOIFactorBldg", "CoinsuranceFactor",
         "Deductible250Factor", "DeductibleFactor",
         "LessThan80PctMultiplicativeFactor"},
        ORCHESTRATOR + " Our group's union is exactly chunk 1's chain and "
        "nothing else -- asserted as a set, so a table silently entering or "
        "leaving the Group I chain fails this script."),
    "SetBGIIRatesAndFactors": (
        {"BasicGroupIIRate", "LowestBasicGroupIIRate",
         "BasicGroupIIFlatCoinsuranceFactor", "BasicGroupIILOIFactorBldg",
         "Deductible250Factor", "DeductibleByLocationFactor",
         "DeductibleFactor", "GroupIINumericValue",
         "GroupIIOpenSidesNumericValue"},
        ORCHESTRATOR + " Chunk 2's chain, asserted as a set. Note it reaches "
        "`GroupIIOpenSidesNumericValue`, which the golden case never exercises "
        "-- reachable but untested, and that is a statement worth having."),
    "SetBasicGroupIIBaseRate": (
        "BasicGroupIIRate",
        "Nine groups, and this one is nearly uniform: every group reads "
        "`BasicGroupIIRate`, with four ALSO reaching `LowestBasicGroupIIRate` "
        "(Outdoor Trees, Outside Signs, both Radio/TV Antennas groups). Ours "
        "reads the single table. The lowest-rate branch is the wind/hail-"
        "excluded path chunk 2 tested separately, so its absence from "
        "Structure's base-rate rule is expected rather than missing."),
    "SetBasicGroupILOIFactor": (BLDG_PERSPROP, "BasicGroupILOIFactorBldg"),
    "SetBasicGroupIILOIFactor": (BLDG_PERSPROP, "BasicGroupIILOIFactorBldg"),

    # ---- chunk 3's chain --------------------------------------------------
    "LookupBroadSpecialLOIFactor": (BLDG_PERSPROP,
                                    "BroadSpecialLOIFactorBldg"),
    "SetBroadLOIFactor": (BLDG_PERSPROP, "BroadSpecialLOIFactorBldg"),
    "SetSpecialLOIFactor": (BLDG_PERSPROP, "BroadSpecialLOIFactorBldg"),

    "SetSpecialBaseRate": (
        {"SpecialBuildingRate", "SpecialBuildersRiskRate"},
        "**The case gate point 6 was written around, and it is wider than the "
        "documentation said.** Sixteen datadef groups define this one rule "
        "name and they read FIVE different tables -- `SpecialBuildingRate` "
        "(6 groups, including ours), "
        "`SpecialFormIncldgTheftTimeElementBaseRate` (6), "
        "`SpecialPrsnlPropRate` (2), "
        "`SpecialFormBldrsRiskTimeElementBaseRate` (1), and "
        "`SpecialBuildersRiskRate` (ours, on the class 1150 branch). "
        "Ours reads the building rate plus the Builders Risk rate, because the "
        "rule branches on class code 1150 before it looks anything up. Nothing "
        "in the rule name, the datadef name or the returned value "
        "distinguishes these five; only the datadef group does. Chunks 4, 5, 6 "
        "and 7 each execute a DIFFERENT one of them."),
    "SetSpecialTheftExclusionFactor": (
        "SpecialBldgTheftExclusionFactor",
        "The second documented case, and a cleaner three-way split: Structure "
        "and SpecialClass read `SpecialBldgTheftExclusionFactor`, "
        "PersonalProperty reads `SpecialPrsnlPropTheftExclusionFactor`, and "
        "the three time-element groups read "
        "`SpecialLeaseHoldTimeElementTheftExclusionFactor`. Ours is the "
        "building table. Worth noting against Puerto Rico: PR overrides this "
        "rule and folds the theft decision into its cause-of-loss values "
        "instead, so PR reaches no theft factor at all."),
    "SetBroadRate": (
        None,
        NAME_REUSE + ". Five groups define it and NONE is ours: Debris Removal "
        "(x3) reads `DebrisRemovalRate`, Leasehold Interest reads "
        "`LeaseholdInterestBroadSpecialRate`, Pollutant Clean-Up reads "
        "`PollutantCleanUpAndRemovalRate`. Chunk 3's `SetBroadRate` is a pure "
        "`Product` of base rate and loss cost multiplier with no lookup, so "
        "reading nothing is correct -- and asserted rather than assumed."),
    "SetSpecialRate": (
        None,
        NAME_REUSE + ", the exact mirror of `SetBroadRate` above across the "
        "same five groups. Ours reaches no matrix."),
    "SetBroadRatesAndFactors": (
        {"BroadFormBaseRate", "BroadSpecialLOIFactorBldg",
         "Deductible250Factor", "DeductibleFactor"},
        ORCHESTRATOR + " Four tables, which is the whole of Broad's 6-step "
        "chain -- the shortest in the coverage, and the set says so."),
    # ---- chunk 5's chain, the BusinessIncome half -------------------------
    "SetBGIBaseRateAdjustmentFactor": (
        "BaseRateAdjustmentFactor",
        "Business Income's own multiplier, and the only header-only table in "
        "the chunk -- 46 of 47 file it, PR does not."),
    "SetTypeOfRiskFactor": (
        "BusnIncomeFactor",
        "the default `SetFactor` branch, on three keys: CovType x TypeOfRisk x "
        "CoinsuranceToUse. 131 countrywide rows. This is Business Income's "
        "replacement for Building's flat coinsurance table."),
    "SetFinalBasicGroupIRate": (
        None,
        "reads nothing -- the final rate is the cause-of-loss adjustment times "
        "`Factor`, both already computed."),
    "SetCoinsuranceToUse": (
        None,
        "no matrix: it resolves a VALUE, not a factor, and when blanketed it "
        "scans the policy blanket table rather than a rate table."),
    "SetBasicGroupICauseOfLossAdjustment": (
        None,
        "the sprinkler, vandalism and Builders Risk factors are all computed "
        "elsewhere and multiplied in here."),
    "SetBasicGroupIICauseOfLossAdjustment": (
        None,
        "the one rule in the chunk that 10 of 47 states override -- and even "
        "those read no matrix of their own, only already-computed factors."),

    "SetSpecialRatesAndFactors": (
        {"SpecialBuildingRate", "SpecialBuildersRiskRate",
         "SpecialBldgTheftExclusionFactor", "BroadSpecialLOIFactorBldg",
         "Deductible250Factor", "DeductibleByLocationFactor",
         "DeductibleFactor"},
        ORCHESTRATOR + " Seven tables against Broad's four, and the difference "
        "is exactly the three steps Special has that Broad does not: the theft "
        "exclusion factor, its own deductible-by-location rule, and the "
        "Builders Risk base-rate branch."),
}


def _wrap(text, width=68):
    words, line, out = text.split(), "", []
    for w in words:
        if len(line) + len(w) + 1 > width:
            out.append(line); line = w
        else:
            line = f"{line} {w}".strip()
    if line:
        out.append(line)
    return out


def lname(tag):
    return tag.rsplit("}", 1)[-1]


def scan(package_dir: Path):
    """rule name -> {datadef group -> (files, matrices)}.

    The matrices are **effective**, not direct: a rule's own `Lookup` elements
    plus everything reachable through the `RunRule` calls it makes inside its
    own datadef group.

    That transitive step was added 2026-09-18 and it is the whole point of the
    check. ISO's `Set*` rules almost never contain a `Lookup`; they delegate to
    a `Lookup*` rule by name. Reading only the direct matrices made this script
    **blind to exactly the two cases gate point 6 was written around** --
    `SetSpecialBaseRate` and `SetSpecialTheftExclusionFactor` are each defined
    in 16 and 6 datadef groups respectively and reported ZERO matrices apiece,
    so they could never have been flagged. Chunks 1 and 2 passed point 6 under
    that blindness; re-running this script re-tests them.
    """
    direct = defaultdict(lambda: defaultdict(lambda: [set(), set(), set()]))
    rules_dir = package_dir / "Rules"
    for f in sorted(rules_dir.glob("*.Rule.xml")):
        try:
            root = ET.fromstring(f.read_text(encoding="utf-8-sig",
                                             errors="replace"))
        except ET.ParseError:
            continue
        for el in root:
            if lname(el.tag) != "Rule":
                continue
            name = el.get("Name")
            group = el.get("DataDefGroup", "?")
            mats = {d.get("MatrixFromConstant") for d in el.iter()
                    if lname(d.tag) == "Lookup" and d.get("MatrixFromConstant")}
            calls = {d.get("Rule") for d in el.iter()
                     if lname(d.tag) == "RunRule" and d.get("Rule")}
            slot = direct[name][group]
            slot[0].add(f.name[: -len(".Rule.xml")])
            slot[1] |= mats
            slot[2] |= calls

    def effective(name, group, seen):
        """Matrices this rule reaches, following RunRule within its group."""
        if (name, group) in seen:
            return set()
        seen.add((name, group))
        slot = direct.get(name, {}).get(group)
        if slot is None:
            # A called rule may be defined only in the parent group; falling
            # back to any definition of the name is how ISO resolves it.
            others = direct.get(name, {})
            if len(others) != 1:
                return set()
            (group, slot), = others.items()
            if (name, group) in seen:
                return set()
            seen.add((name, group))
        mats = set(slot[1])
        for callee in slot[2]:
            mats |= effective(callee, group, seen)
        return mats

    out = defaultdict(lambda: defaultdict(lambda: [set(), set()]))
    for name, groups in direct.items():
        for group, slot in groups.items():
            out[name][group] = [slot[0], effective(name, group, set())]
    return out


def report(out, title, names=None, limit=None):
    shared = {n: g for n, g in out.items()
              if len(g) > 1 and (names is None or n in names)}
    differing = {}
    for n, groups in shared.items():
        mats = {frozenset(v[1]) for v in groups.values() if v[1]}
        if len(mats) > 1:
            differing[n] = groups
    print(f"\n{title}")
    print(f"  names defined in more than one datadef group : {len(shared)}")
    print(f"  ...of those, reading DIFFERENT rate tables   : {len(differing)}")
    shown = sorted(differing.items())[:limit] if limit else sorted(differing.items())
    for n, groups in shown:
        print(f"\n  {n}")
        for g, (files, mats) in sorted(groups.items()):
            if mats:
                print(f"      {g:46s} -> {', '.join(sorted(mats))}")
    if limit and len(differing) > limit:
        print(f"\n  ... and {len(differing) - limit} more; "
              f"run with --all to list every one")
    return shared, differing


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--juris", default="CW")
    ap.add_argument("--asof", default=golden.ASOF)
    ap.add_argument("--all", action="store_true",
                    help="list every ambiguous name, not the first 12")
    a = ap.parse_args()

    book = book_for(a.juris, a.asof)
    pkg = book.state.package
    print(f"Gate point 6 -- shared names, {pkg.pkg_id}")
    out = scan(pkg.content)
    print(f"{len(out)} distinct rule names across "
          f"{len(list((pkg.content / 'Rules').glob('*.Rule.xml')))} rule files")

    _, chunk1_bad = report(out, "ON THE CHUNK 1 CHAIN", names=CHUNK1_RULES)
    _, chunk2_bad = report(out, "ON THE CHUNK 2 CHAIN (Basic Group II)",
                           names=CHUNK2_RULES)
    _, chunk3_bad = report(out, "ON THE CHUNK 3 CHAIN (Broad and Special)",
                           names=CHUNK3_RULES)
    _, chunk4_bad = report(out, "ON THE CHUNK 4 CHAIN (Contents)",
                           names=CHUNK4_RULES)
    _, chunk5_bad = report(out, "ON THE CHUNK 5 CHAIN (Business Income)",
                           names=CHUNK5_RULES)
    _, chunk6_bad = report(out, "ON THE CHUNK 6 CHAIN (Special Class)",
                           names=CHUNK6_RULES)
    _, chunk7_bad = report(out, "ON THE CHUNK 7 CHAIN (Special Class Busn Income)",
                           names=CHUNK7_RULES)
    _, chunk8_bad = report(out, "ON THE CHUNK 8 CHAIN (Legal Liability)",
                           names=CHUNK8_RULES)
    _, chunk9_bad = report(out, "ON THE CHUNK 9 CHAIN (Blanket Rating Detail)",
                           names=CHUNK9_RULES)
    chunk1_bad = {**chunk1_bad, **chunk2_bad, **chunk3_bad}

    unresolved = []
    if chunk1_bad:
        print("\n  ADJUDICATION -- the gate says a shared name is a question, so")
        print("  each one gets an answer here rather than a shrug:")
        for n, groups in sorted(chunk1_bad.items()):
            entry = ADJUDICATED.get(n)
            if entry is None:
                unresolved.append(n)
                print(f"\n  {n}: NOT ADJUDICATED -- this is what fails the gate")
                continue
            expect, why = entry
            if expect == BLDG_PERSPROP:
                expect, why = {why}, (
                    "The name is split Building-side / Personal-Property-side "
                    "and is scoped by datadef group, so the interpreter "
                    "dispatches correctly. Recorded rather than waved past, "
                    "because chunk 4 (Contents) executes the OTHER half of "
                    "this same name.")
            actual = groups.get(CHUNK1_GROUP, [set(), set()])[1]
            # Three answer shapes: a set (assert it exactly), a single table
            # name (assert membership), or None (assert our group reaches NO
            # matrix -- a silence that has to be deliberate to mean anything).
            if expect is None:
                ok, shown = not actual, "(no matrix -- pure arithmetic)"
            elif isinstance(expect, set):
                ok, shown = actual == expect, ", ".join(sorted(expect))
            else:
                ok, shown = expect in actual, expect
            if not ok:
                unresolved.append(n)
            print(f"\n  {n} in {CHUNK1_GROUP}")
            print(f"      resolves to : {', '.join(sorted(actual)) or '(none)'}")
            print(f"      adjudicated : {shown}   "
                  f"[{'MATCH' if ok else 'MISMATCH'}]")
            for line in _wrap(why):
                print(f"      {line}")
    else:
        print("\n  Nothing on chunk 1's chain is ambiguous.")

    report(out, "EVERYWHERE ELSE -- the map later chunks inherit",
           limit=None if a.all else 12)

    print("\n  A name reading different tables is not a defect. It is a")
    print("  QUESTION, and the answer has to be written down per coverage")
    print("  before that coverage's gate can pass.")
    if unresolved:
        print(f"\n  {len(unresolved)} chunk 1 chain name(s) ambiguous and NOT")
        print("  adjudicated. Point 6 does not pass until each has an answer.")
        return 1
    print("\n  Every ambiguous name on chunk 1's chain is adjudicated and the")
    print("  adjudication matches the corpus. Point 6 is an enumerated fact")
    print("  for this chunk rather than an untested silence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
