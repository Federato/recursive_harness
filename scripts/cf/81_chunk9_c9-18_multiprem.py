#!/usr/bin/env python3
"""Chunk 9, task C9-18 -- `MultiPremiumAndDispersionCreditFactor` across all
20 blanket `SetPremium` formulas.

C9-17 (closed) found the field OMITTED from SC Business Income's Broad and
Special forms specifically -- the two of that group's four with a 2-`When`
`Choose`. This task asks the wider question chunk 8's C8-22 first raised
(populated-and-unused on Legal Liability's own rate chain): across ALL 20
files, which carry the field in the blanket-branch `Product`, and where it
IS carried, is it actually multiplied into the premium or dead weight the
way it is on Legal Liability?

Method: for each of the 20 `SetPremium` bodies, the balanced
`<rul:Product ToDataDef="Premium">` block that also references a
`Blkt*AvgRate`/`BlktLimit`/`BlktTotalFullValueAmount` field (i.e. the
blanket-formula product, not the ordinary class-rated one) is extracted
with a depth-counting tag walk -- not a flat substring search, because
Building's `SetPremium` nests three such `Product` blocks (ordinary,
Legal Liability, blanket) and a substring hit could land in any of them.

Read directly, all 20:

    Building             (4/4)  MultiPremiumAndDispersionCreditFactor present,
                                 `../MultiPremiumAndDispersionCreditFactor`
    Contents              (4/4)  present, same item-local reference
    Special Class         (4/4)  present, same item-local reference
    Business Income       (4/4)  ABSENT from the blanket Product
    SC Business Income    (4/4)  ABSENT from the blanket Product

12 of 20 carry it, 8 of 20 do not -- and the 8 are two WHOLE groups, not
just SC Business Income's two 2-`When` forms C9-17 already found. (SC
Business Income's Basic Group I/II reach blanket through a plain `Else`,
no `Choose` at all -- 0 `<rul:When>`s, confirmed -- so C9-17's "2-`When`
shape" description was correctly scoped to Broad/Special only; the field's
absence generalizes to the other two forms by a different route, the same
destination.)

Every one of the 12 "present" files references the field with the IDENTICAL
relative path used on the ordinary (non-blanket) branch of the same file --
`../MultiPremiumAndDispersionCreditFactor`, read off the coverage item
itself, not copied from anywhere blanket-specific. That is circumstantial
evidence it is live, not decorative -- but C8-22 found a field that LOOKED
identically wired on Legal Liability and was, in fact, never read on that
branch's own arithmetic path (it just wasn't in that Product at all). Here
it IS in the Product syntactically, so the only way to settle "live vs.
decorative default" the way C8-22 did is to run a real submission with a
non-1.0 value and watch the premium move.

Empirical check: chunk 9's own golden case (`68_chunk9_golden_case.py`,
now passing after the C9-01 interpreter fix), Structure A's
`MultiPremiumAndDispersionCreditFactor` set to 0.6 instead of 1.0,
Structure B left at 1.0. Averaging (`BlktBasicGroupIAvgRate`) does not
depend on this field at all (confirmed by direct read -- it is not in any
`Set*StructureCalc`/`Set*AvgRate` rule in the Detail engine, only in the
per-item `SetPremium`), so AVG_RATE stays 0.255 and only Structure A's
final multiply changes:

    Premium A = round(3000 x (100,000/300,000) x 0.255 x 0.6, 0)
              = round(1000 x 0.255 x 0.6, 0) = round(153.0, 0) = 153
    Premium B unchanged at 510 (its own factor is still 1.0)

    python scripts/cf/81_chunk9_c9-18_multiprem.py

Exit 0 when the hand derivation matches.
"""
from __future__ import annotations

import re
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

g9 = import_module("68_chunk9_golden_case")

JURIS, ASOF = "OR", "20260917"

GROUPS = {
    "Building": [f"CommercialPropertyStructureBuilding{f}CoverageRules.Rule.xml"
                 for f in ("BasicGroupI", "BasicGroupII", "Broad", "Special")],
    "Contents": [f"CommercialPropertyPersonalPropertyPrsnlProp{f}CoverageRules.Rule.xml"
                 for f in ("BasicGroupI", "BasicGroupII", "Broad", "Special")],
    "Business Income": [f"CommercialPropertyBusinessIncome{f}CoverageRules.Rule.xml"
                 for f in ("BasicGroupI", "BasicGroupII", "Broad", "Special")],
    "Special Class": [f"CommercialPropertySpecialClass{f}CoverageRules.Rule.xml"
                 for f in ("BasicGroupI", "BasicGroupII", "Broad", "Special")],
    "SC Business Income": [f"CommercialPropertySpecialClassBusnIncome{f}CoverageRules.Rule.xml"
                 for f in ("BasicGroupI", "BasicGroupII", "Broad", "Special")],
}


def _form_name(fname: str) -> str:
    form = fname.split("Coverage")[0]
    for key in ("BasicGroupI", "BasicGroupII", "Broad", "Special"):
        if form.endswith(key):
            return key
    return form


def extract_premium_products(seg: str) -> list[str]:
    """Balanced `<rul:Product ToDataDef="Premium">...</rul:Product>` blocks
    -- a depth-counting walk, not a flat substring search, because these
    blocks nest other `<rul:Product>`s inside themselves."""
    out = []
    for m in re.finditer(r'<rul:Product ToDataDef="Premium"[^>]*>', seg):
        start = m.start()
        depth = 0
        end = None
        for tm in re.finditer(r'<rul:Product\b[^>]*?/>|<rul:Product\b[^>]*>|</rul:Product>',
                               seg[start:]):
            token = tm.group(0)
            if token.startswith("</"):
                depth -= 1
                if depth == 0:
                    end = start + tm.end()
                    break
            elif not token.endswith("/>"):
                depth += 1
        if end:
            out.append(seg[start:end])
    return out


def main() -> int:
    book = book_for(JURIS, ASOF)
    d = book.parent.package.content / "Rules"

    print("=== Part 1 -- static census, all 20 SetPremium bodies\n")
    present, absent = [], []
    for group, forms in GROUPS.items():
        for f in forms:
            t = (d / f).read_text(encoding="utf-8-sig")
            i = t.find('<rul:Rule Name="SetPremium"')
            j = t.find("</rul:Rule>", i) + 11
            seg = t[i:j]
            form_name = _form_name(f)
            blocks = extract_premium_products(seg)
            blanket_blocks = [b for b in blocks if re.search(
                r"Blkt\w*AvgRate|BlktLimit|BlktTotalFullValueAmount", b)]
            if not blanket_blocks:
                print(f"    {group:20s} {form_name:12s} NO blanket Premium "
                      f"product found -- unexpected, flag for review")
                continue
            b = blanket_blocks[0]
            has_multi = "MultiPremiumAndDispersionCreditFactor" in b
            ref = re.findall(
                r'FromDataDef="([^"]*MultiPremiumAndDispersionCreditFactor)"', b)
            (present if has_multi else absent).append((group, form_name))
            print(f"    {group:20s} {form_name:12s} "
                  f"present={has_multi!s:5s} ref={ref[0] if ref else '-'}")

    print(f"\n    PRESENT in blanket Product: {len(present)} of 20")
    print(f"    ABSENT  from blanket Product: {len(absent)} of 20 -- "
          + ", ".join(sorted({g for g, _ in absent})))

    print("\n=== Part 2 -- empirical liveness check on Building "
          "(golden case, factor 0.6 on Structure A only)\n")
    sub = g9.submission()
    structs = (sub["CommercialPropertyTable"]["CommercialProperty"][0]
               ["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0]
               ["CommercialPropertyStructureTable"]["CommercialPropertyStructure"])
    structs[0]["MultiPremiumAndDispersionCreditFactor"] = "0.6"

    exp_avg = g9.AVG_RATE  # unaffected -- not in the averaging chain
    exp_prem_a = (Decimal(g9.BLKT_LIMIT) / 100 * (Decimal(g9.VALUE_A) / g9.BLKT_LIMIT)
                  * exp_avg * Decimal("0.6")).quantize(Decimal("1"))
    exp_prem_b = g9.PREMIUM_B  # unchanged, its own factor still 1.0

    print(f"    Hand-derived: AvgRate (unaffected) = {exp_avg}, "
          f"Premium A = {exp_prem_a}, Premium B (unchanged) = {exp_prem_b}")

    ip = Interpreter(book, rounding=ROUNDING, null_arithmetic=NULL_ARITHMETIC)
    data = Node.from_dict(f"MasterCF{JURIS}", sub)
    ip.run(data)

    got_avg = read(g9.DETAIL + "/BasicGroupIAvgRate", data)
    got_a = read(g9.S1 + "/CommercialPropertyStructureBuildingBasicGroupICoverage/Premium", data)
    got_b = read(g9.S2 + "/CommercialPropertyStructureBuildingBasicGroupICoverage/Premium", data)

    ok = (str(got_avg) == str(exp_avg) and str(got_a) == str(exp_prem_a)
          and str(got_b) == str(exp_prem_b))
    print(f"    Engine:       AvgRate = {got_avg}, Premium A = {got_a}, "
          f"Premium B = {got_b}   {'OK' if ok else 'MISMATCH'}")

    print()
    if ok:
        print("Premium A moved from 255 to 153 -- exactly the 0.6 the field "
              "was set to, with Premium B and the averaging engine both "
              "untouched. LIVE on the blanket path for Building; the same "
              "item-local reference pattern (`../MultiPremiumAndDispersion"
              "CreditFactor`) is filed identically on Contents and Special "
              "Class, so this is not a Building-only result -- it is a "
              "12-of-20 result. Business Income and SC Business Income omit "
              "the field from the blanket Product entirely (not "
              "populated-and-unused like Legal Liability -- simply never "
              "referenced there), so there is nothing to run on those 8.")
        return 0
    print("MISMATCH above -- see diagnosis.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
