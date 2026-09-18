#!/usr/bin/env python3
"""Chunk 8 opening census -- Legal Liability, before any task is written.

Same opening move as chunks 4-7: enumerate the tables and the rule overrides
across all 47 jurisdictions FIRST. Each state is diffed against **its own
resolved parent** (chunk 6 / OI-100), and nothing is filtered by a guess about
naming (chunk 7 / C7-12).

**Chunk 8 is different from every chunk before it: the divergence is already
traced**, in `Excel_Rater_LegalLiability_vs_ClassRated_{Building,PersonalProperty}.html`,
with an eleven-point map. So the census's first job is not to discover the
shape -- it is to **check the map against the corpus**, the way C7-27 checked
the Special Class Business Income reuse map.

Four questions:

  1  **The two tables that exist only here.** `LegalLiabilityFactor` (2 rows)
     and `AddlInsurableInterestFactor` (4 rows), plus the plain-language ->
     Option mapping the map says ships EMPTY in the current package.
  2  **The branch-ordering claim.** The map's central structural argument is
     that `SetPremium` is a `Choose`, the Legal Liability test sits at branch 2
     and the blanket test at branch 3 -- so blanket is unreachable BY ORDERING.
     **A state that reorders those branches would break it**, so the ordering
     has to be checked in all 47, not asserted once.
  3  **The `SetPremium` override census.** The build order records 479 state
     rewrites of `SetPremium` across CF. How many touch these eight files?
  4  **The two gate fields**, which the map says differ by NAME and by LEVEL:
     Building gates on `CovType` on the item, Contents on `CovForm` inherited
     from the occupancy class.

    python scripts/cf/58_chunk8_census.py

Always exits 0 -- this is a census, not a test.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from cf_engine.resolve import CFEditionResolver, book_for

ASOF = "20260917"

TABLES = ["LegalLiabilityFactor", "AddlInsurableInterestFactor",
          "AdditionalInsurableIntOption"]

BLDG = [f"CommercialPropertyStructureBuilding{f}CoverageRules.Rule.xml"
        for f in ("BasicGroupI", "BasicGroupII", "Broad", "Special")]
PP = [f"CommercialPropertyPersonalPropertyPrsnlProp{f}CoverageRules.Rule.xml"
      for f in ("BasicGroupI", "BasicGroupII", "Broad", "Special")]
FILES = BLDG + PP

LL_RULES = ["SetLegalLiabilityFactor", "SetLegalLiabFactor",
            "SetLegalLiabAddlInsurableIntFactor", "SetAddlInsurableIntOption"]


def branches(body):
    """One entry per `rul:When` in `SetPremium`: (names_LL, tests_blkt_yes).

    **The first version of this function was wrong, and wrong in the direction
    that manufactures a finding.** It looked for the string `IncludedInBlkt`
    anywhere in a branch's test and called the first hit "the blanket branch" --
    but branch 1 is the SCHEDULED branch and tests `IncludedInBlkt = "No"`, so
    every file came back with blanket ahead of Legal Liability and the traced
    map looked contradicted. It is not: the map is right.

    A branch is the blanket branch only if it tests `IncludedInBlkt` against
    the literal **"Yes"**.
    """
    i = body.find('<rul:Rule Name="SetPremium"')
    if i < 0:
        return None
    seg = body[i:i + body[i:].find("</rul:Rule>") + 11]
    starts = [m.start() for m in re.finditer(r"<rul:When>", seg)]
    out = []
    for n, start in enumerate(starts):
        end = starts[n + 1] if n + 1 < len(starts) else len(seg)
        chunk = seg[start:end]
        test = chunk[:chunk.find("</rul:Test>") + 12]
        consts = re.findall(
            r"<rul:Constant Type=\"string\">([^<]*)</rul:Constant>", test)
        # **SELECTS Legal Liability, not merely mentions it.** Contents'
        # branch 1 names the Legal Liability form in a `NotEqual` -- it is the
        # branch that EXCLUDES it -- so a mention test reported Contents'
        # LL branch as 1 and Building's as 2, and the two sides looked
        # structurally different when they are not. Only an `Equal` selects.
        eq = re.findall(
            r"<rul:Equal>(?:(?!</rul:Equal>).)*?<rul:Constant "
            r"Type=\"string\">([^<]*)</rul:Constant>", test, re.S)
        ll = any("Legal Liability" in c for c in eq)
        blkt = "IncludedInBlkt" in test and "Yes" in eq
        out.append((ll, blkt, consts))
    return out, "<rul:Otherwise>" in seg


def main() -> int:
    res = CFEditionResolver()
    juris = sorted(res.jurisdictions)
    books = {j: book_for(j, ASOF, resolver=res) for j in juris}
    any_book = books[juris[0]]
    d = any_book.parent.package.content / "Rules"

    # ---- 1
    print(f"=== 1  Table census   ({len(juris)} jurisdictions, as of {ASOF})")
    print("    each state diffed against ITS OWN parent (OI-100)\n")
    for t in TABLES:
        try:
            cw = any_book.parent_table(t)
            n_cw, rows = len(cw.rows), cw.rows
        except Exception as exc:
            print(f"    {t:34s} unreadable: {exc}")
            continue
        own = [j for j, b in books.items() if b.declares(t) == "state"]
        print(f"    {t:34s} CW rows={n_cw:<3d} states filing={len(own)} of "
              f"{len(juris)}" + ("   " + ",".join(own) if own else ""))
        for r in rows[:5]:
            print(f"        {r}")

    # ---- 2
    print()
    print("=== 2  Branch ordering -- is blanket really unreachable, in all 47?")
    print()
    def report(label, f, body):
        got = branches(body)
        if got is None:
            return None
        brs, has_other = got
        ll = next((n for n, b_ in enumerate(brs) if b_[0]), None)
        blkt = next((n for n, b_ in enumerate(brs) if b_[1]), None)
        form = f.split("Coverage")[0].split("Building")[-1].split(
            "PrsnlProp")[-1]
        print(f"    {label:11s} {form:14s} {len(brs)} When(s)"
              f"{' + Otherwise' if has_other else ''}"
              f"   LL at branch {None if ll is None else ll + 1}"
              f"   blanket at branch {None if blkt is None else blkt + 1}")
        return ll, blkt

    for label, files in (("CW Building", BLDG), ("CW Contents", PP)):
        for f in files:
            report(label, f, (d / f).read_text(encoding="utf-8-sig"))
    bad, seen = [], 0
    for j_, b in books.items():
        for f in FILES:
            p = b.state.package.content / "Rules" / f
            if not p.exists():
                continue
            got = branches(p.read_text(encoding="utf-8-sig"))
            if got is None:
                continue
            brs, _ = got
            seen += 1
            ll = next((n for n, x in enumerate(brs) if x[0]), None)
            blkt = next((n for n, x in enumerate(brs) if x[1]), None)
            if ll is None or (blkt is not None and blkt < ll):
                bad.append((j_, f, ll, blkt))
    print()
    print(f"    state copies of these eight files examined : {seen}")
    print(f"    ...where Legal Liability is absent or comes AFTER blanket : "
          f"{len(bad)}   {bad if bad else '(none)'}")
    print("    **A state that reordered them would make blanket reachable for")
    print("    Legal Liability in that state alone**, which is why this is")
    print("    checked in 47 rather than read once countrywide.")
    print("    Building has no explicit blanket test at all -- its branch 3 is")
    print("    `CovType <> \"Leasehold Interest\"`, so blanket is reached by")
    print("    elimination and Legal Liability never gets there. Contents")
    print("    tests `IncludedInBlkt = \"Yes\"` explicitly AND excludes the")
    print("    Legal Liability form by name. **Same outcome, two mechanisms** --")
    print("    exactly points 7 and 9 of the traced map.")

    # ---- 3
    print("\n=== 3  SetPremium override census, these eight files\n")
    hits = {}
    for j, b in books.items():
        for f in FILES:
            p = b.state.package.content / "Rules" / f
            if not p.exists():
                continue
            t = p.read_text(encoding="utf-8-sig")
            if '<rul:Rule Name="SetPremium"' in t:
                hits.setdefault(f, []).append(j)
    for f in FILES:
        h = hits.get(f, [])
        side = "Building" if f in BLDG else "Contents"
        form = f.split("Coverage")[0].split("Building")[-1].split(
            "PrsnlProp")[-1]
        print(f"    {side:9s} {form:14s} rewritten by {len(h):>2d}"
              + ("   " + ",".join(h) if h else ""))
    everyone = sorted({j for v in hits.values() for j in v})
    print(f"\n    jurisdictions rewriting at least one of the eight: "
          f"{len(everyone)}   {everyone}")

    # ---- 4
    print("\n=== 4  The two gate fields, and the two factor datadefs\n")
    for f, want in ((BLDG[0], "CovType"), (PP[0], "CovForm")):
        t = (d / f).read_text(encoding="utf-8-sig")
        i = t.find('<rul:Rule Name="SetPremium"')
        seg = t[i:i + t[i:].find("</rul:Rule>") + 11]
        fields = sorted({m for m in re.findall(r'FromDataDef="([^"]+)"', seg)
                         if "CovType" in m or "CovForm" in m})
        side = "Building" if f in BLDG else "Contents"
        print(f"    {side:9s} gate fields in SetPremium : {fields}")
    for rule in LL_RULES:
        found = []
        for p in sorted(d.glob("*.xml")):
            t = p.read_text(encoding="utf-8-sig")
            for m in re.finditer(
                    r'<rul:Rule Name="(\w+)"[^>]*DataDefGroup="(\w+)"', t):
                if m.group(1) == rule:
                    found.append(m.group(2))
        print(f"    {rule:38s} defined in {len(found)} group(s): "
              f"{sorted(set(found))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
