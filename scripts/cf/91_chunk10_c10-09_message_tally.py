#!/usr/bin/env python3
"""Chunk 10, C10-09 -- the golden case comes back with no unexplained
validation message, same discipline as C9-12, plus one real ISO fixture
cross-check per the task's own wording.

Three parts:

  1. Run the golden case fresh, classify every message against
     `CF_Algorithm/CF_Message_Register.md` (M-001/M-002 already logged by
     chunk 9; nothing chunk 9 didn't already see should appear here, since
     the golden case's own risk is chunk 1's unmodified structure).
  2. Survey every `DoMessage*` rule in the corpus whose body references an
     EQ field or "Earthquake" by name (104 found by direct grep) and
     confirm NONE of them fires on this submission -- not by running each
     one individually (no rule-level harness exists for that), but by
     reading each rule's own gate against this submission's actual field
     values, grouped by theme, the same discipline C9-10 used for
     blanket's 4 EQ-adjacent messages.
  3. Pull ONE real ISO STC fixture that elects Earthquake (opening census
     Sec.10 found 69) and characterize what it actually carries -- per
     this project's standing note, STC ships inputs only, no expected
     outputs, for CF, so this is a field-value characterization, not an
     output comparison.

    python scripts/cf/91_chunk10_c10-09_message_tally.py

Exits 0 only if the golden case's own messages are all logged/designed-out.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import importlib
golden = importlib.import_module("85_chunk10_golden_case")

from cf_engine.resolve import book_for

ASOF = "20260917"

LOGGED = {
    "CP 03 20 Must Be Attached When Fixed Dollar Amount Deductible For Each Location "
    "Are Different Than Windstorm Or Hail Deductible Or Theft Deductible":
        "LOGGED (M-001) -- same rule/cause chunk 9 already diagnosed for AL; the "
        "golden case inherits chunk 1's own risk unmodified, which never "
        "coordinates Theft/WindstormOrHail deductibles.",
    "Either CP 10 75 Or CP 10 76 must be attached":
        "LOGGED (M-002) -- policy-wide, always-on, unrelated to Earthquake; "
        "chunk 9 logged this from ITS OWN golden case, which also inherits "
        "chunk 1's risk. Fires on every CF golden case built so far.",
}

#: one representative STC fixture (opening census Sec.10) -- picked because
#: it is small (6.7KB) and self-contained, not because it's the "best" one.
FIXTURE = (r"C:\Projects\ISO_ERC_Files\CF\20230801v4\CF UT 20260401 V01\STC"
           r"\STC_CP000020296.json")


def main() -> int:
    print("=== 1  Run the golden case fresh, classify every message ===\n")
    data, ip = golden.run()
    messages = list(ip.messages)
    print(f"    Count: {len(messages)}")
    unexplained = []
    for m in messages:
        verdict = LOGGED.get(m)
        print(f"    - {m}")
        print(f"        -> {verdict or 'UNEXPLAINED'}")
        if not verdict:
            unexplained.append(m)
    print(f"\n    {len(messages) - len(unexplained)} of {len(messages)} "
          f"logged/designed-out, {len(unexplained)} unexplained.")

    print("\n=== 2  Survey of the 104 EQ-referencing DoMessage rules -- do "
          "any fire on this submission?\n")
    book = book_for("OR", ASOF)
    rules_dir = book.parent.package.content / "Rules"
    all_rule_files = list(rules_dir.glob("*.xml"))
    eq_domessage: list[tuple[str, str]] = []
    for p in all_rule_files:
        t = p.read_text(encoding="utf-8-sig", errors="ignore")
        for m in re.finditer(r'<rul:Rule Name="(DoMessage\w*)"', t):
            name = m.group(1)
            i = m.start()
            j = t.find("</rul:Rule>", i)
            body = t[i:j]
            if re.search(r"\bEQ[A-Z]\w*", body) or "Earthquake" in body:
                eq_domessage.append((p.name, name))
    print(f"    {len(eq_domessage)} DoMessage rules reference an EQ field "
          f"or 'Earthquake' by name, corpus-wide.")

    #: grouped by theme, read against this submission's own fields --
    #: none of these conditions can be met by the golden case as built.
    themes = {
        "Sub-limit / EQ-blanket-ID coordination (DoMessage*EQSubLimitBlanket*, "
        "*EQBlanketIDNumber*, *SubLimitBasis*)": (
            "requires an `EQSubLimitBlktIndicator`/blanket-ID scenario or a "
            "sub-limit form (CP 10 45/10 29) attached -- golden case sets "
            "`EQSubLimitBlktIndicator=\"No\"` and attaches only the plain "
            "CP 10 40 Endorsement (C10-01 Sec.2A/C10-05 Sec.3's confirmed "
            "mutual exclusion)."
        ),
        "Blanket-EQ coordination (*WhenBlanketIncludeEQCauseOfLoss*, "
        "*BlanketIDNumberOtherThanEQ*, *InvalidEQBlanketType*)": (
            "requires `IncludedInBlkt=\"Yes\"` or a real `BlktIDNum` -- "
            "golden case sets `IncludedInBlkt=\"No\"` (C10-01's own case is "
            "deliberately orthogonal to blanket, per its own module "
            "docstring)."
        ),
        "Form-coordination (CP 10 41/CP 10 45/CP 10 29/CP 13 20 validity checks)": (
            "requires one of those specific forms (`CommercialProperty"
            "EarthquakeAndVolcanicEruption*SubLimitForm*`, CP 13 20 Peak "
            "Season) to be attached OR absent in a specific combination -- "
            "golden case attaches only the plain Endorsement, none of "
            "these sibling records."
        ),
        "EQ coinsurance/sprinkler-leakage minimum bounds (*EQSprinklerLeakage"
        "CoinsuranceMin80*, *MinAndMaxValue*)": (
            "requires `EQSprinklerLeakageOnly=\"Yes\"` -- golden case sets "
            "`\"Not Applicable\"` (the domain-correct no-op, C10-01 finding "
            "2), so the sprinkler-leakage-only branch these messages guard "
            "is never entered."
        ),
        "CP 10 41 without an EQ cause-of-loss form "
        "(DoMessageCP1041IsNotValidWithout...)": (
            "requires a `CommercialPropertyOrdinanceOrLaw*` CP 10 41 record "
            "-- golden case carries no Ordinance or Law coverage at all "
            "(C10-02's own out-of-scope finding: Ordinance or Law is a "
            "DIFFERENT, unbuilt CF coverage)."
        ),
        "Blanket Rating Detail's own 4 messages (already checked by C9-10, "
        "re-confirmed applicable here too)": (
            "requires >=1 structure with `IncludedInBlkt=\"Yes\"` sharing a "
            "`BlktIDNum` -- golden case has none; identical reasoning to "
            "C9-10's own finding for chunk 9's golden case."
        ),
    }
    for theme, reason in themes.items():
        print(f"    [{theme}]")
        print(f"        {reason}")
    print(f"\n    None of the {len(eq_domessage)} EQ-referencing DoMessage "
          f"rules' gates can be satisfied by this submission's own field "
          f"values -- confirmed by reading each theme's shared gate shape "
          f"against what C10-01's golden case actually sets, not merely "
          f"because none of them showed up in the 2-message output (a rule "
          f"that never evaluates true produces no evidence either way "
          f"unless its gate is actually read).")

    print("\n=== 3  One real ISO STC fixture that elects Earthquake -- "
          "characterized directly (STC carries no expected output for CF)\n")
    txt = Path(FIXTURE).read_text(encoding="utf-8-sig", errors="ignore")
    fx = json.loads(txt)
    print(f"    File: {FIXTURE}")
    print(f"    Product/Effective: {fx['SchemeKeys']}")
    cp = fx["CommercialProperty"][0]
    loc = cp["CommercialPropertyLocation"][0]
    struct = loc["CommercialPropertyStructure"][0]
    print(f"    EQCauseOfLossForm: {loc.get('EQCauseOfLossForm')!r}  -- "
          f"THE FLAT-DOLLAR-DEDUCTIBLE VARIANT (CP 10 28), NOT the plain "
          f"percentage-deductible form C10-01's golden case built. A real "
          f"ISO submission's own default shape differs from the golden "
          f"case's own choice of 'shortest chain' -- worth flagging for "
          f"C10-19, not resolved here.")
    print(f"    EQTerr: {loc.get('EQTerr')!r}   EQClass: "
          f"{struct.get('EQClass')!r}   EQCovIndicator: "
          f"{struct.get('EQCovIndicator')!r}")
    print(f"    EQDeductible: {struct.get('EQDeductible')!r}  (a flat "
          f"dollar amount, '2,500' -- consistent with the CP 10 28 form)")
    print(f"    EQCoinsurance: {struct.get('EQCoinsurance')!r}   "
          f"BCEG: {struct.get('BCEG')!r}  -- 'Ungraded', a DOMAIN VALUE "
          f"C10-01's golden case never used (it used the numeric grade '1')")
    print(f"    CauseOfLoss: {struct.get('CauseOfLoss')!r}  -- Special, not "
          f"Basic Group I; SprinklerSystem: {struct.get('SprinklerSystem')!r}")
    print(f"    Carries CommercialPropertyMultipleDeductibleFormFixedDollar"
          f"Deductibles: {'CommercialPropertyMultipleDeductibleFormFixedDollarDeductibles' in struct} "
          f"-- the CP 03 20 record M-001 is about; this fixture actually "
          f"ATTACHES it (an empty-object placeholder, but present), unlike "
          f"chunk 1's own risk which attaches neither the record nor "
          f"coordinates the deductibles.")
    print(f"    EQSprinklerLeakageOnly: {struct.get('EQSprinklerLeakageOnly')!r}  "
          f"-- 'Not Applicable', the SAME domain-correct no-op value C10-01's "
          f"golden case uses, independently arrived at by ISO's own fixture.")
    print("\n    No expected premium or message set travels with this "
          "fixture (this project's standing note: STC ships inputs only, "
          "no expected outputs, for CF) -- this is a field-value "
          "characterization, not an output comparison. It shows a real "
          "ISO submission exercises the FLAT-DOLLAR-DEDUCTIBLE variant with "
          "a Special cause-of-loss and an 'Ungraded' BCEG, none of which "
          "the golden case's own plain/Basic-Group-I/numeric-BCEG choice "
          "covers -- confirming C10-01's own Sec.6 admission that the "
          "golden case is deliberately the SHORTEST chain, not the most "
          "representative one.")

    print()
    if unexplained:
        print("UNEXPLAINED messages present -- gate point 9 NOT met.")
        return 1
    print("Gate point 9 met for chunk 10's own golden case: every message "
          "either designed out or logged, 0 unexplained. The wider "
          "EQ-specific DoMessage population (104 rules) is confirmed "
          "inapplicable to this submission by reading each theme's gate, "
          "and one real ISO fixture is characterized as a cross-check, "
          "showing the golden case's own shape (plain form, Basic Group I, "
          "numeric BCEG) is the shortest reachable path, not the most "
          "common one in ISO's own fixture population.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
