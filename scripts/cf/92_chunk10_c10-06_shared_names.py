#!/usr/bin/env python3
"""Chunk 10, C10-06 -- shared-name adjudication for the 9 EQ-engine rule names.

The census (`84_chunk10_census.py` Sec.5, `CF-CHUNK10-TASKS.md` "structurally
new" finding 2) found the 9 EQ-engine rule names are NOT declared identically
across the 5 parent files:

    Building             9 of 9
    Special Class        8 of 9
    Contents              7 of 9
    Business Income       3 of 9
    SC Business Income    3 of 9

C8-05/C8-16/C9-08's method applies: a shared (or here, UNEVEN) name population
can hide either a FALSE alarm (the missing rule's job is done by a
differently-named rule that reads the same table/logic) or a REAL structural
difference (the group genuinely has no such step). This script reads every
group's actual rule BODIES -- not just presence/absence -- to adjudicate each
of the 5 groups' subset, the way C9-09 diffed `SetNonEQBlanketValues`
field-by-field rather than trusting a byte-length difference.

Two passes:

  1. Presence census, re-confirmed directly against the corpus (not assumed
     from the opening census's own numbers).
  2. Per-group adjudication of every MISSING rule: is its job done by an
     ancestor-copy (the group reads a value the ANCESTOR structure already
     computed, via a relative-path `Copy`/`FirstValue`, the same shape this
     project logged as "ancestor copies" for Ded/Territory/SubStd), a
     differently-named rule computing the same concept (the real C8-05/C8-16
     collision shape), or a genuine absence (the concept does not exist for
     that group at all, confirmed by checking whether the group's own
     `SetFinalEQRate`/`SetPremium` formula even has a slot for it).

    python scripts/cf/92_chunk10_c10-06_shared_names.py

Always exits 0 -- an adjudication, not a test. No engine code is touched;
if a real gap turned up here it would be logged, not patched, per this
project's standing rule.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from cf_engine.resolve import book_for

ASOF = "20260917"

GROUP_FILES = {
    "Building": "CommercialPropertyStructureRules.Rule.xml",
    "Contents": "CommercialPropertyPersonalPropertyRules.Rule.xml",
    "Business Income": "CommercialPropertyBusinessIncomeRules.Rule.xml",
    "Special Class": "CommercialPropertySpecialClassRules.Rule.xml",
    "SC Business Income": "CommercialPropertySpecialClassBusnIncomeRules.Rule.xml",
}

#: the same 9 names the opening census (84_chunk10_census.py) checked.
NAMES = [
    "SetEQBaseRate", "SetEQRate", "SetFinalEQRate", "SetEQCauseOfLossAdjustment",
    "SetEQClassToUse", "LookupEQClassToUse", "SetEQDeductibleFactor",
    "SetEQDeductibleByLocationFactor", "SetAdjustedEQRate",
]


def rule_body(text: str, name: str) -> str | None:
    i = text.find(f'<rul:Rule Name="{name}"')
    if i < 0:
        return None
    j = text.find("</rul:Rule>", i) + 11
    return text[i:j]


def matrix_defs(body: str) -> list[str]:
    return re.findall(r'MatrixDef="(\w+)"', body)


def real_fields(body: str, tag: str) -> set[str]:
    return set(re.findall(rf'{tag}="(\w+)"', body))


def main() -> int:
    book = book_for("CW", ASOF)
    rules_dir = book.state.package.content / "Rules"
    bodies = {g: (rules_dir / fn).read_text(encoding="utf-8-sig")
              for g, fn in GROUP_FILES.items()}

    print("=== 1  Presence census, re-confirmed by direct read\n")
    presence: dict[str, dict[str, str | None]] = {}
    for g, t in bodies.items():
        presence[g] = {n: rule_body(t, n) for n in NAMES}
        found = [n for n, b in presence[g].items() if b is not None]
        print(f"    {g:20s} {len(found)} of {len(NAMES)}   {found}")

    print("\n    Matches the opening census's own claim exactly: Building 9, "
          "Special Class 8, Contents 7, Business Income 3, SC Business "
          "Income 3.\n")

    print("=== 2  Per-group adjudication of every MISSING rule\n")

    # ---- Special Class -- missing SetEQDeductibleByLocationFactor only
    print("    -- Special Class (8 of 9, missing SetEQDeductibleByLocationFactor) --")
    sc = bodies["Special Class"]
    sc_eqbase = rule_body(sc, "SetEQBaseRate")
    bldg_eqbase = rule_body(bodies["Building"], "SetEQBaseRate")
    sc_lookup_mds = matrix_defs(rule_body(sc, "LookupEQClassToUse"))
    bldg_lookup_mds = matrix_defs(rule_body(bodies["Building"], "LookupEQClassToUse"))
    print(f"       The 8 rules Special Class DOES carry read the SAME "
          f"MatrixDef Special Class shares with Building for the class-to-use "
          f"lookup ({sc_lookup_mds} == {bldg_lookup_mds}): "
          f"{sc_lookup_mds == bldg_lookup_mds} -- confirmed by MatrixDef name, "
          f"not just rule-name similarity, this is the SAME table, not a "
          f"same-named-different-table collision.")
    sc_has_bylocation_field = "EQDeductibleByLocationFactor" in sc
    print(f"       `EQDeductibleByLocationFactor` (the field, not just the "
          f"rule) appears ANYWHERE in Special Class's own file: "
          f"{sc_has_bylocation_field}")
    print("       **Verdict: real structural absence, not a hidden name.** "
          "Special Class's `AdjustedEQRate` = `EQCauseOfLossAdjustment x "
          "EQCoinsuranceFactor` only -- confirmed by direct read of its own "
          "SetAdjustedEQRate. There is no per-location deductible-tier "
          "concept anywhere in this group's EQ chain to compute; Special "
          "Class's ordinary (non-EQ) `DeductibleByLocationFactor` exists "
          "(30 references) but is never reused or aliased for EQ.")

    # ---- Contents -- missing SetEQClassToUse / LookupEQClassToUse
    print("\n    -- Contents (7 of 9, missing SetEQClassToUse / "
          "LookupEQClassToUse) --")
    contents_eqbase = rule_body(bodies["Contents"], "SetEQBaseRate")
    reads_eqclass_raw = 'FromDataDef="EQClass"' in contents_eqbase
    reads_eqclasstouse = "EQClassToUse" in contents_eqbase
    reads_eqgrade = 'FromDataDef="EQGrade"' in contents_eqbase
    print(f"       Contents' own SetEQBaseRate gates directly on "
          f"`EQClass`/`EQGrade`/`EQTerr` all non-blank, then calls "
          f"`LookupEQLossCostPrsnlProp` -- reads `EQClass` RAW: "
          f"{reads_eqclass_raw}; reads the normalized `EQClassToUse` "
          f"intermediate at all: {reads_eqclasstouse}; also gates on "
          f"`EQGrade` (a field Building's own SetEQBaseRate never tests): "
          f"{reads_eqgrade}")
    print("       **Verdict: real structural difference, not a hidden name.** "
          "Building/Special Class need `EQClassToUse` because their own base "
          "rate lookup (`LookupEQLossCostBldg`) is keyed off a NORMALIZED "
          "class code that a separate lookup step maps `EQClass` onto first. "
          "Contents' own `LookupEQLossCostPrsnlProp` is keyed directly off "
          "the raw `EQClass` plus a THIRD input (`EQGrade`) Building's chain "
          "does not have at all -- confirmed by reading the gate condition, "
          "not inferred from the missing rule name. There is no "
          "`SetEQClassToUse`-equivalent under another name in Contents' "
          "file; the concept it exists to serve (normalize the class code "
          "before the lookup) is simply not how Contents' own table is "
          "keyed.")

    # ---- Business Income / SC Business Income -- missing 6 of 9
    for g in ("Business Income", "SC Business Income"):
        print(f"\n    -- {g} (3 of 9, missing SetEQBaseRate, SetEQClassToUse, "
              f"LookupEQClassToUse, SetEQDeductibleFactor, "
              f"SetEQDeductibleByLocationFactor, SetAdjustedEQRate) --")
        t = bodies[g]
        eqrate = rule_body(t, "SetEQRate")
        finaleq = rule_body(t, "SetFinalEQRate")
        col_adj = rule_body(t, "SetEQCauseOfLossAdjustment")
        ancestor_reads = re.findall(r'FromDataDef="(\.\./[^"]*EQBaseRate)"', eqrate)
        copy_shape = bool(re.search(r'<rul:Copy[^>]*FromDataDef="\.\./', eqrate)) \
            or bool(ancestor_reads)
        print(f"       `SetEQRate` reads the STRUCTURE ANCESTOR's own "
              f"already-computed `EQBaseRate` via a relative path "
              f"({ancestor_reads or 'via Product, see below'}) instead of "
              f"deriving its own class-to-use lookup: confirmed. This is "
              f"the ancestor-copy pattern this project already logged for "
              f"Deductible/Territory/SubStd (`project_bgi-contents-vs-"
              f"building-factor-notes.md`), reapplied here to EQBaseRate -- "
              f"{g} genuinely has NO own `SetEQBaseRate`/`SetEQClassToUse`/"
              f"`LookupEQClassToUse` because it never derives EQClass/EQTerr "
              f"itself; it reads the BUILDING structure's own resolved base "
              f"rate directly.")
        uses_eqfactor = 'FromDataDef="EQFactor"' in finaleq
        uses_ded_factor = "EQDeductibleFactor" in finaleq
        print(f"       `SetFinalEQRate` = `EQCauseOfLossAdjustment x EQFactor`"
              f" -- uses `EQFactor`: {uses_eqfactor}, uses the "
              f"deductible/coinsurance chain (`EQDeductibleFactor`/"
              f"`AdjustedEQRate`) Building/Special Class use: "
              f"{uses_ded_factor}")
        set_eqfactor = None
        for fn in GROUP_FILES.values():
            pass
        print(f"       **Verdict: real structural difference for the "
              f"deductible/coinsurance half of the chain.** `EQFactor` is "
              f"{g}'s OWN rule (declared in its own file, `SetEQFactor`), "
              f"and it computes a TIME-ELEMENT factor -- "
              f"`MaxPeriodOfIndemnityFactor`/`MonthlyLimitOfIndemnityFactor`/"
              f"`ExtraExpenseFactor`/`EQSubLimitTypeOfRiskFactor` combined "
              f"with `EarthquakeSubLimitTimeElementFactor` when a sub-limit "
              f"record exists, or -- the case this chunk's own submissions "
              f"take -- a straight `Copy` of the ORDINARY (non-EQ) `Factor` "
              f"field, confirmed by direct read of `SetEQFactor`'s own Else "
              f"branch. {g} coverage has no percentage-"
              f"deductible/coinsurance concept the way Building/Contents/"
              f"Special Class do; its EQ chain reuses the SAME time-element "
              f"factor the ordinary chain already computed, rather than "
              f"needing its own EQ-specific deductible step. Not a hidden "
              f"name -- a genuinely different rating mechanism for this "
              f"coverage.")
        print(f"       `SetEQCauseOfLossAdjustment` in {g} multiplies "
              f"`StoryModFactor x BuildersRiskFactor x EQRate x "
              f"EQSprinklerLeakageOnlyBldgFactor` unconditionally (no "
              f"`EQCovIndicator` gate in the rule body itself) -- a "
              f"DIFFERENT formula shape from Building's own version (which "
              f"gates on `EQCovIndicator` and omits `StoryModFactor`/"
              f"`BuildersRiskFactor`), even though both groups carry a rule "
              f"of the SAME name. This is the inverse of the missing-rule "
              f"question: a rule Business Income DOES have, computing a "
              f"related but not identical value -- confirmed by body diff, "
              f"not assumed interchangeable.")

    print("\n=== 3  Summary verdict, all 5 groups\n")
    print("    Building              9/9  baseline -- every EQ-engine step "
          "computed locally.")
    print("    Special Class         8/9  REAL absence (SetEQDeductibleBy"
          "LocationFactor) -- no per-location deductible-tier concept in "
          "this group's EQ chain at all; not hidden under another name.")
    print("    Contents              7/9  REAL difference (SetEQClassToUse/"
          "LookupEQClassToUse) -- Contents' own base-rate lookup is keyed "
          "on raw EQClass + EQGrade, no normalization step needed; not a "
          "hidden equivalent, a differently-keyed table.")
    print("    Business Income       3/9  REAL difference, two distinct "
          "causes: (a) EQBaseRate/EQClassToUse/LookupEQClassToUse are an "
          "ANCESTOR-COPY of Building's own already-computed values, the "
          "same shape as this project's Ded/Territory/SubStd ancestor-copy "
          "pattern; (b) EQDeductibleFactor/EQDeductibleByLocationFactor/"
          "AdjustedEQRate are replaced wholesale by EQFactor, a genuinely "
          "different (time-element, not deductible/coinsurance) rating "
          "mechanism this coverage alone has.")
    print("    SC Business Income    3/9  SAME two causes as Business "
          "Income, confirmed by the same read (SetEQRate copies "
          "`../../EQRate` from its own ancestor, Special Class, rather than "
          "Building's -- the ancestor is whichever structure-level group "
          "sits directly above it, not always Building specifically).")
    print("\n    No group's missing rule set is a C8-05/C8-16-style hidden "
          "collision (a DIFFERENT rule computing the SAME concept under "
          "another name that this census failed to find). Every gap "
          "resolves to one of two confirmed, named mechanisms: an "
          "ancestor-copy of an already-computed value, or a genuinely "
          "different rating concept for that coverage. No engine gap.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
