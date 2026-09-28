#!/usr/bin/env python3
"""Chunk 6, tasks C6-10 to C6-14 -- the class-description chain.

  10  **Two lookups in series**, moved one at a time: the description, the
      protection-class band, and the band gone. Plus the deductible-band
      question C6-01 and C6-03 could not settle.
  11  **Florida is not a private namespace. Florida is an OLD EDITION.**
  12  **New York's 189 filed rate rows ARE reachable** -- by submitting the
      converted option, which New York's deleted rule then does not overwrite.
  13  **New York and Puerto Rico each make THREE coordinated edits** to remove
      the Group II numeric value as a concept.
  14  **Near-miss spellings**, all worth zero, none of them reported.

Every figure below was read off the filed rows and worked out by hand before
the run. The baseline is the chunk 6 golden case: Basic Group I **$66**.

    C6-10  Aircraft Stored in the Open -> Option2
             PC 3  "1 to 4"   0.286  -> r3(0.286 x .95)=0.272 x .98 -> 0.267  $267
             PC 6  "5 to 8"   0.368  -> r3(0.3496)  =0.350 x .98 -> 0.343     $343
             PC 9  "9 to 10"  0.448  -> r3(0.4256)  =0.426 x .98 -> 0.417     $417
             no protection class     -> the base rate gates shut              $0

    C6-12  NY, option SUBMITTED   Option34a "1 to 4" = 0.43
             r3(0.43 x .95) = 0.409 x CW ded 0.96 -> 0.393                    $393

**C6-10's last case settles a question two earlier tasks had to leave open.**
`TotAmtInsuranceToUse` keys the deductible band, and with one 100,000 item the
item's own total and the location's total are the same number. A SECOND Special
Class item at 100,000 separates them: the item's own total stays 100,000 (band
0.98, $267) while a location total would be 200,000 (band 0.99, $269). Two
dollars, and the only case in the chunk that can tell them apart.

    python scripts/cf/45_chunk6_description_chain.py

Exit 0 when every case matches its derivation.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from importlib import import_module

from cf_engine.config import NULL_ARITHMETIC, ROUNDING
from cf_engine.resolve import book_for
from gl_engine.interp.interpreter import Interpreter
from gl_engine.interp.tree import Node, read

raas6 = import_module("44_chunk6_raas")
g = import_module("41_chunk6_golden_case")

SC = g.SC
P_BGI = g._P % "BasicGroupI"
P_BGII = g._P % "BasicGroupII"
ASOF = g.ASOF

AIRCRAFT = "Aircraft Stored in the Open"
NAME = "SpecialClassDescriptionConvertedOption"

#: id, state, item overrides, expected Basic Group I premium, why
CHAIN = [
    ("10  baseline -- Option34a, PC 3", "OR", {}, "66", "the reference"),

    ("10  description moves -- Aircraft", "OR",
     {"ClassDescription": AIRCRAFT}, "267",
     "**lookup 1 of 2.** A different English string converts to Option2 and "
     "the base rate goes 0.07 -> 0.286. Nothing else in the payload changed"),

    ("10  band moves -- PC 6", "OR",
     {"ClassDescription": AIRCRAFT, "loc:ProtectClass": "6"}, "343",
     "**lookup 2 of 2.** The same option, one band along: 0.286 -> 0.368. "
     "Protection class is a KEY here, and this is the case that shows it "
     "reaching the rate without any factor in the chain"),

    ("10  band moves -- PC 9", "OR",
     {"ClassDescription": AIRCRAFT, "loc:ProtectClass": "9"}, "417",
     "the third band, 0.448 -- a 56% spread across protection class on one "
     "class of property"),

    ("10  NO protection class at all", "OR",
     {"ClassDescription": AIRCRAFT, "loc:ProtectClass": None}, "417",
     "**predicted $0 and it is $417 -- the finding is the correction.** An "
     "absent `ProtectClass` does not blank the key and gate the rate shut, the "
     "way an absent description does. The Location resolves it to **`9 to 10`, "
     "the WORST band**, and the premium goes UP by 56%. Every other absent "
     "field in this chunk costs coverage; this one charges for it"),

    ("12  NY, option SUBMITTED", "NY",
     {"SpecialClassDescConvertedOption": "Option1a"}, "393",
     "**New York's 189 filed rows are reachable after all.** NY empties "
     "`SetSpecialClassDescConvertedOption` to `<rul:Sequence />`, and an "
     "emptied rule cannot overwrite what the submission supplies. So the "
     "deleted rule is not a dead end -- **it is how ISO says the field is an "
     "INPUT in New York**. And the code has to be **New York's own**: NY files "
     "63 option codes to countrywide's 71, of which **35 exist nowhere "
     "countrywide** and 43 countrywide codes are absent here. `Option34a`, the "
     "golden case's code, is one of the 43 -- **the private namespace is New "
     "York's, not Florida's**"),

    ("12  NY, option NOT submitted", "NY", {}, "0",
     "the same state, the same table, nothing submitted -- and no message. "
     "**The difference between $393 and $0 in New York is a field no other "
     "jurisdiction wants**"),
]

#: C6-14: near-miss spellings of the golden case's description. Every one of
#: these is a plausible thing for a person or a mapping layer to produce.
NEAR_MISSES = [
    (g.DESC, "66", "exact -- the reference"),
    ("Towers - Broadcasting Antennas (Radio and TV)", "0",
     "**Florida's spelling**, and a real ISO string -- in Florida's package"),
    ("towers - broadcasting antennas (cell, radio and tv)", "0", "case"),
    (g.DESC + " ", "0", "one trailing space"),
    ("Towers - Broadcasting Antennas (Cell, Radio & TV)", "0",
     "`&` for `and`"),
    ("Towers  - Broadcasting Antennas (Cell, Radio and TV)", "0",
     "one doubled space"),
    ("Towers – Broadcasting Antennas (Cell, Radio and TV)", "0",
     "an en dash for the hyphen -- what a word processor does by itself"),
]


def tree(state, over, second_item=False):
    """The standalone item, with `loc:` keys routed to the location.

    `loc:X = None` REMOVES the location field, which is how C6-10's
    no-protection-class case is built.
    """
    item_over, loc_over = raas6.split(over)
    item = {k: str(v) for k, v in dict(raas6.ITEM, **item_over).items()}
    # Basic unless the caller names a cause of loss: Broad and Special gate
    # their base rates on an exact match, so a test that moves a SHARED value
    # and reads them has to send their own submission.
    item.setdefault("CauseOfLoss", "Basic")
    items = [item]
    if second_item:
        items.append(dict(item))
    loc = {"ProtectClass": "3", "BasicGroupIIRatingTerr": "Entire State",
           "CommercialPropertySpecialClassTable": {
               "CommercialPropertySpecialClass": items}}
    for k, v in loc_over.items():
        if v is None:
            loc.pop(k, None)
        else:
            loc[k] = str(v)
    return {
        "EffDate": "01/01/2027",
        "CommercialPropertyTable": {"CommercialProperty": [{
            "IRPMFactor": "1.0",
            "PolicyType": "Commercial Property Policy",
            "CommercialPropertyLocationTable": {
                "CommercialPropertyLocation": [loc]},
        }]},
    }


def run(state, over, second_item=False):
    book = book_for(state, ASOF)
    ip = Interpreter(book, rounding=ROUNDING, trace=False,
                     null_arithmetic=NULL_ARITHMETIC)
    data = Node.from_dict(f"MasterCF{state}", tree(state, over, second_item))
    ip.run(data)
    return data


def main() -> int:
    ok = True

    print("=== 10 / 12  The two lookups, moved one at a time\n")
    for name, state, over, want, _ in CHAIN:
        data = run(state, over)
        got = str(read(P_BGI, data))
        opt = read(f"{SC}/SpecialClassDescConvertedOption", data)
        band = read(f"{SC}/ProtectionClassToUse", data)
        base = read(f"{SC}/BasicGroupIBaseRate", data)
        good = got == want
        ok &= good
        print(f"  {name:38s} opt={str(opt):>11s} band={str(band):>8s} "
              f"base={str(base):>6s} premium={got:>4s}"
              + ("" if good else f"   <-- expected {want}"))

    # ---- C6-10, the deductible band, settled
    print("\n=== 10  Whose total keys the deductible band -- settled")
    data = run("OR", {"ClassDescription": AIRCRAFT}, second_item=True)
    got = str(read(P_BGI, data))
    tot = read(f"{SC}/TotAmtInsuranceToUse", data)
    ded = read(f"{SC}/DeductibleFactorBasicGroupI", data)
    good = got == "267"
    ok &= good
    print(f"    two 100,000 items on one location")
    print(f"    TotAmtInsuranceToUse = {tot}   deductible factor = {ded}")
    print(f"    premium = {got}   (expected 267 -- the ITEM's own total) "
          f"{'OK' if good else 'MISMATCH -- 269 would mean the LOCATION total'}")
    print("    **C6-01 and C6-03 both had to leave this open**, because with")
    print("    one item the two readings give the same number. `SetTotAmtInsurance`")
    print("    copies `Limit` when the item is not blanketed, and this is the")
    print("    case that proves the copy is what the band keys on.")

    # ---- C6-11
    print("\n=== 11  Florida under V02: its OWN option namespace (under V01 it was an old edition)")
    fl = book_for("FL", ASOF)
    parent = fl.parent_table(NAME)
    own = fl.table(NAME)
    p_desc = {r[1] for r in parent.rows}
    o_desc = {r[1] for r in own.rows}
    p_codes = {r[2] for r in parent.rows}
    o_codes = {r[2] for r in own.rows}
    cwm = {r[1]: r[2] for r in parent.rows}
    stm = {r[1]: r[2] for r in own.rows}
    remap = [d for d in o_desc & p_desc if cwm[d] != stm[d]]
    orb = book_for("OR", ASOF)
    ref_desc = {r[1] for r in orb.parent_table(NAME).rows}
    # 2026-09-24: the user added CF FL 20241201 V02 (the edition ISO rates on). It rides on
    # CW 20230801 V04 and RENUMBERS Florida's options: under V01 (over CW 2023 V01) the
    # figures were 0 / 0 / 3 / 6 / 11 and Florida shared every option code with its parent.
    # Measured from the V02 files, Florida now has its own option namespace -- confirmed
    # independently by the rater's SCSTATE finding (a state-filed option map replaces CW's
    # inside the state's project; Rater_Simplifications_Backlog.md, RC-5 ED-FL).
    checks = [
        ("Florida's resolved parent", fl.parent.pkg_id, "CF_CW_20230801_V04"),
        ("Oregon's resolved parent", orb.parent.pkg_id, "CF_CW_20260601_V01"),
        ("option codes outside its parent's set", len(o_codes - p_codes), 23),
        ("shared descriptions mapped elsewhere", len(remap), 35),
        ("descriptions its own parent does not file", len(o_desc - p_desc), 4),
        ("descriptions it drops from its own parent", len(p_desc - o_desc), 7),
        ("...the same table against the 2026 parent", len(o_desc - ref_desc),
         4),
    ]
    for label, got_v, want_v in checks:
        good = str(got_v) == str(want_v)
        ok &= good
        print(f"    {label:44s} {str(got_v):>22s}  (expected {want_v}) "
              f"{'OK' if good else 'MISMATCH'}")
    print("    **Since 2026-09-24 Florida resolves to CF FL 20241201 V02 over CW")
    print("    2023 V04**, the edition ISO rates on. V02 renumbers Florida's")
    print("    options: 23 codes outside its parent's set and 35 shared")
    print("    descriptions mapped to different codes, so Florida now has its")
    print("    OWN option namespace (the rater's SCSTATE finding agrees: a")
    print("    state-filed option map replaces CW's inside the state's project).")
    print("    Under V01 (over CW 2023 V01) the answer was the opposite: every")
    print("    code shared, none remapped, Florida frozen at the 2023 vocabulary.")

    # ---- C6-11 / C6-12: where the private namespace actually is
    print("\n=== 11/12  The private namespace is NEW YORK's")
    ny = book_for("NY", ASOF)
    nyc = {r[1] for r in ny.table("BasicGroupIRateSpecialClass").rows}
    cwc = {r[1] for r in ny.parent_table("BasicGroupIRateSpecialClass").rows}
    for label, got_v, want_v in (
            ("New York option codes", len(nyc), 63),
            ("countrywide option codes", len(cwc), 71),
            ("codes only New York files", len(nyc - cwc), 35),
            ("countrywide codes New York lacks", len(cwc - nyc), 43),
            ("is the golden case's Option34a in New York", "Option34a" in nyc,
             False)):
        good = str(got_v) == str(want_v)
        ok &= good
        print(f"    {label:44s} {str(got_v):>22s}  (expected {want_v}) "
              f"{'OK' if good else 'MISMATCH'}")
    print("    Only 28 of the two sets are shared. **A countrywide option code")
    print("    submitted into New York misses**, and New York's own converter")
    print("    is header-only, so nothing in the corpus maps a description to")
    print("    an NY code. The 189 rows are reachable only by a caller that")
    print("    already knows New York's private vocabulary.")

    # ---- C6-13
    print("\n=== 13  Three coordinated edits, twice")
    for state, want_ii, terr in (("NY", "55", "I"), ("PR", "0", "Entire State")):
        book = book_for(state, ASOF)
        rules = (book.state.package.content / "Rules"
                 / "CommercialPropertySpecialClassRules.Rule.xml")
        body = rules.read_text(encoding="utf-8-sig")

        def emptied(rule):
            i = body.find(f'<rul:Rule Name="{rule}"')
            if i < 0:
                return None
            seg = body[i:i + body[i:].find("</rul:Rule>") + 11]
            return "<rul:Sequence />" in seg or "<rul:Sequence/>" in seg

        i = body.find('<rul:Rule Name="SetBasicGroupIIRate"')
        rate_rule = body[i:i + body[i:].find("</rul:Rule>") + 11] if i >= 0 else ""
        drops_term = "BasicGroupIINumericValue" not in rate_rule
        # the STATE'S OWN FILE (what it filed), not the book's resolution: since 2026-09-28 a Property
        # book resolves an empty state table to the countrywide rows (CFResolvedBook, ISO-confirmed in VT)
        n_rows = len(book.state.table("Rate", "SpecialClassBasicGroupIINumber").rows)
        data = run(state, {"loc:BasicGroupIIRatingTerr": terr})
        got = str(read(P_BGII, data))
        num = read(f"{SC}/BasicGroupIINumericValue", data)
        good = (n_rows == 0 and emptied("SetBasicGroupIISymbolNum")
                and drops_term and got == want_ii and num is None)
        ok &= good
        print(f"    {state}: number table {n_rows} rows | "
              f"SetBasicGroupIISymbolNum emptied={emptied('SetBasicGroupIISymbolNum')}"
              f" | rate rule drops the term={drops_term}")
        print(f"        numeric value = {num}   Group II premium = {got}  "
              f"(expected {want_ii}) {'OK' if good else 'MISMATCH'}")
    print("    **Not a filing with a hole in it -- a different chain.** Each")
    print("    state empties the table, empties the rule that fills it, AND")
    print("    rewrites the rate rule so it never reads it. Oregon multiplies")
    print("    by 8; these two have no such concept. PR then prices Group II")
    print("    at zero for a separate reason -- it files no Group II base rate")
    print("    at all, state or countrywide.")

    # ---- C6-13, the submitted numeric value
    print("\n=== 13  And the numeric value cannot be supplied either")
    for state, want in (("OR", "209"), ("NY", "55")):
        terr = "I" if state == "NY" else "Entire State"
        data = run(state, {"BasicGroupIISymbolNum": "2",
                           "loc:BasicGroupIIRatingTerr": terr})
        got = str(read(P_BGII, data))
        good = got == want
        ok &= good
        print(f"    {state}: BasicGroupIISymbolNum submitted as 2 -> "
              f"premium {got}  (expected {want}, unchanged) "
              f"{'OK' if good else 'MISMATCH'}")
    print("    Oregon overwrites it from the lookup; New York never reads it.")
    print("    **The same submitted field is ignored for two opposite reasons**")
    print("    -- and C6-12 showed the converted OPTION going the other way in")
    print("    the same state. A deleted rule makes a field an input; a live")
    print("    unguarded rule makes it a decoy.")

    # ---- C6-14
    print("\n=== 14  Near-miss spellings")
    for desc, want, why in NEAR_MISSES:
        data = run("OR", {"ClassDescription": desc})
        got = str(read(P_BGI, data))
        good = got == want
        ok &= good
        print(f"    {got:>3s} (expected {want:>3s}) {'OK ' if good else 'MISS'}"
              f"  {why}")
    print("    **Seven spellings, one of which is worth $66 and six of which")
    print("    are worth nothing, and the engine reports no difference between")
    print("    them.** The input is a 46-character English string with")
    print("    punctuation; ISO's own list runs to 100 characters with")
    print("    abbreviations like `Undrgrd` and `Incldg`.")

    print()
    if ok:
        print("Every case matches its derivation.")
        return 0
    print("MISMATCHES above.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
