#!/usr/bin/env python3
"""Chunk 9, task C9-19 -- `IRPMFactor`/`PackageModFactor` level counts, all
20 blanket `SetPremium` formulas, plus one empirical non-Building proof.

The golden case (`68_chunk9_golden_case.py`) read Building's blanket branch
at `../../../../../IRPMFactor` -- five `../`. Chunk 7's own crossform doc
(`CF-CHUNK7-CROSSFORM.md`) already flagged that Business Income reads it
seven levels up "because the nesting is one deeper" -- so five is NOT
assumed to be the corpus-wide answer here; every one of the 20 files is
read directly.

Method: same balanced `<rul:Product ToDataDef="Premium">` extraction as
`81_chunk9_c9-18_multiprem.py`, filtered to the block that references a
`Blkt*AvgRate`/`BlktLimit`/`BlktTotalFullValueAmount` field (the blanket
formula, not the ordinary one), then counted `../` segments on the
`IRPMFactor`/`PackageModFactor` `FromDataDef` path inside that block.

Read directly, all 20 (identical within each group's four forms):

    Building             5 / 5    (the golden case's own count)
    Special Class        5 / 5    same depth as Building -- both sit
                                   directly on Location -> Structure(-like)
    Business Income      7 / 7    one deeper, as CF-CHUNK7-CROSSFORM.md
                                   already flagged for its own group
    SC Business Income   7 / 7    same depth as (ordinary) Business Income
    Contents              9 / 9    the DEEPEST of the five, not "one level
                                   deeper" as this task's own framing
                                   guessed -- FOUR levels deeper than
                                   Building, confirmed by direct read of
                                   all four Contents forms, not inferred
                                   from chunk 4's Occupancy Class census

**The level count does NOT hold uniformly at five.** Three of five groups
diverge from Building's number, and Contents diverges further than the
"one level deeper" shape chunk 5/7 established for Business Income.

Empirical proof, non-Building, chosen to be a DIFFERENT depth than the
golden case's own (7, not 5): two full copies of chunk 5's own golden-case
structure (Building + a Business Income record together -- a bare Business
Income record with no Building sibling was tried first and left
`BasicGroupIRate` stuck at its null-safe default of `1`, because that field
is copied from the parent Building's own rate chain; not an engine gap,
just this task's own submission needing the same building chunk 5 already
proved rather than a minimal tree). `CauseOfLoss="Basic"`:
`BasicGroupICauseOfLossAdjustment=0.203`, `Factor=0.55`, both already
confirmed live by chunk 5 and reconfirmed by direct read here.
`IRPMFactor=0.9`, `PackageModFactor=0.8` set on the POLICY (7 levels up from
the Business Income item, per the read above) -- and, as a control showing
the level count is not merely cosmetic, the SAME two fields are ALSO set to
different, wrong values on the Business Income item itself, where this
group's `SetPremium` does not read them at all.

    BasicGroupIBusnIncomeCalc A = round(100,000 x 0.203 x 0.55, 0) = 11,165
    BasicGroupIBusnIncomeCalc B = round(200,000 x 0.203 x 0.55, 0) = 22,330
    BlktBasicGroupIAvgRate = round((11,165+22,330)/300,000, 3) = 0.112
    Premium A = round(0.9 x 0.8 x 0.112 x (100,000/300,000) x (300,000/100), 0)
              = round(0.72 x 0.112 x 1000, 0) = 81
    Premium B = round(0.72 x 0.112 x 2000, 0) = 161

    python scripts/cf/82_chunk9_c9-19_irpm_levels.py

Exit 0 when the hand derivation matches and the item-level decoys are
confirmed inert.
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

chunk5 = import_module("32_chunk5_golden_case")

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
    levels = {}
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
            irpm = re.findall(r'FromDataDef="([^"]*IRPMFactor)"', b)
            pkg = re.findall(r'FromDataDef="([^"]*PackageModFactor)"', b)
            li = irpm[0].count("../") if irpm else None
            lp = pkg[0].count("../") if pkg else None
            levels.setdefault(group, set()).add((li, lp))
            print(f"    {group:20s} {form_name:12s} IRPM levels={li}  "
                  f"PackageMod levels={lp}")

    print("\n    Per-group consistency (all 4 forms give the same pair?):")
    for g, s in levels.items():
        print(f"    {g:20s} {'CONSISTENT ' + str(next(iter(s))) if len(s) == 1 else 'DIVERGES: ' + str(s)}")

    print("\n=== Part 2 -- empirical proof, Business Income (7 levels), "
          "policy-set vs item-set decoy\n")

    COL_ADJ = Decimal("0.203")   # chunk 5's own OR row, CauseOfLoss="Basic"
    FACTOR = Decimal("0.55")     # chunk 5's own row, TypeOfRisk-keyed
    VALUE_A, VALUE_B = 100_000, 200_000
    BLKT_ID, BLKT_LIMIT = 100, 300_000
    IRPM, PKGMOD = Decimal("0.9"), Decimal("0.8")

    calc_a = (VALUE_A * COL_ADJ * FACTOR).quantize(Decimal("1"))
    calc_b = (VALUE_B * COL_ADJ * FACTOR).quantize(Decimal("1"))
    avg = ((calc_a + calc_b) / BLKT_LIMIT).quantize(Decimal("0.001"))
    prem_a = (IRPM * PKGMOD * avg * (Decimal(VALUE_A) / BLKT_LIMIT)
              * (Decimal(BLKT_LIMIT) / 100)).quantize(Decimal("1"))
    prem_b = (IRPM * PKGMOD * avg * (Decimal(VALUE_B) / BLKT_LIMIT)
              * (Decimal(BLKT_LIMIT) / 100)).quantize(Decimal("1"))
    print(f"    Hand-derived: CalcA={calc_a} CalcB={calc_b} AvgRate={avg} "
          f"PremA={prem_a} PremB={prem_b}")

    # Business Income's own `BasicGroupIRate` is copied from its parent
    # BUILDING's base rate (chunk 5's own chain) -- a bare-bones submission
    # with no Building coverage at all left it stuck at a null-safe default
    # (`BasicGroupIRate=1`, confirmed by a throwaway run before this script
    # was finalized), which is why this reuses chunk 5's FULL golden-case
    # structure (Building + Business Income together) rather than a minimal
    # Business-Income-only tree.
    def struct(value: int) -> dict:
        sub_i = chunk5.submission("Basic")
        st = (sub_i["CommercialPropertyTable"]["CommercialProperty"][0]
              ["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0]
              ["CommercialPropertyStructureTable"]["CommercialPropertyStructure"][0])
        bi = st["CommercialPropertyBusinessIncomeTable"]["CommercialPropertyBusinessIncome"][0]
        bi["IncludedInBlkt"] = "Yes"
        bi["BlktIDNum"] = str(BLKT_ID)
        bi["FullBusnIncomeValue"] = str(value)
        bi["Limit"] = str(value)
        # Decoys: this group's SetPremium reads IRPM/PackageMod from the
        # POLICY (7 levels up), never from the item -- these should be
        # inert if the level count is real, not just filed on paper.
        bi["IRPMFactor"] = "0.111"
        bi["PackageModFactor"] = "0.111"
        return st

    sub = chunk5.submission("Basic")
    policy = sub["CommercialPropertyTable"]["CommercialProperty"][0]
    policy["IRPMFactor"] = str(IRPM)
    policy["PackageModFactor"] = str(PKGMOD)
    policy["PolicyType"] = "Commercial Property Policy"
    policy["BlktRated"] = "Yes"
    policy["MUBlktRated"] = "No"
    policy["CommercialPropertyBlanketRatingTable"] = {"CommercialPropertyBlanketRating": [{
        "CommercialPropertyBlanketRatingDetailTable": {
            "CommercialPropertyBlanketRatingDetail": [{
                "UnitNumber": str(BLKT_ID), "Type": "Business Income With Extra Expense",
                "TypeOfBlanketRating": "Average", "Coinsurance": "90%",
                "TotalLimit": str(BLKT_LIMIT),
            }],
        },
    }]}
    loc = policy["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0]
    loc["CommercialPropertyStructureTable"]["CommercialPropertyStructure"] = [
        struct(VALUE_A), struct(VALUE_B)]

    CP = "CommercialPropertyTable/CommercialProperty"
    LOC = CP + "/CommercialPropertyLocationTable/CommercialPropertyLocation"
    S1 = LOC + "/CommercialPropertyStructureTable/CommercialPropertyStructure[1]"
    S2 = LOC + "/CommercialPropertyStructureTable/CommercialPropertyStructure[2]"
    BI1 = S1 + "/CommercialPropertyBusinessIncomeTable/CommercialPropertyBusinessIncome[1]"
    BI2 = S2 + "/CommercialPropertyBusinessIncomeTable/CommercialPropertyBusinessIncome[1]"
    DETAIL = (CP + "/CommercialPropertyBlanketRatingTable/CommercialPropertyBlanketRating[1]"
              "/CommercialPropertyBlanketRatingDetailTable/CommercialPropertyBlanketRatingDetail[1]")
    P1 = BI1 + "/CommercialPropertyBusinessIncomeBasicGroupICoverage/Premium"
    P2 = BI2 + "/CommercialPropertyBusinessIncomeBasicGroupICoverage/Premium"

    ip = Interpreter(book, rounding=ROUNDING, null_arithmetic=NULL_ARITHMETIC)
    data = Node.from_dict(f"MasterCF{JURIS}", sub)
    ip.run(data)

    got_avg = read(DETAIL + "/BasicGroupIAvgRate", data)
    got_a = read(P1, data)
    got_b = read(P2, data)
    ok = (str(got_avg) == str(avg) and str(got_a) == str(prem_a)
          and str(got_b) == str(prem_b))
    print(f"    Engine:       AvgRate={got_avg} PremA={got_a} PremB={got_b}"
          f"   {'OK' if ok else 'MISMATCH'}")
    if ip.messages:
        print(f"    ISO validation messages ({len(ip.messages)}): "
              + "; ".join(str(m)[:56] for m in ip.messages[:4]))

    print()
    if ok:
        print("The 7-level read is real, not decorative: the POLICY-set "
              "0.9/0.8 reached both Business Income items' blanket premium "
              "exactly, and the item-level 0.111/0.111 decoys (set 7 levels "
              "too shallow) were never read. Level count does NOT hold at "
              "5 for all 20 -- three of five groups diverge (Building/"
              "Special Class=5, Business Income/SC Business Income=7, "
              "Contents=9), confirmed by direct read of all 20 files, not "
              "assumed uniform.")
        return 0
    print("MISMATCH above -- see diagnosis.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
