#!/usr/bin/env python3
"""Chunk 11 Groups E and F -- inventory (C11-02, 05, 10) and states (C11-03, 08).

Every expected value is copied from `docs/CF-CHUNK11-GROUPS-E-F.md`, written
before this ran.

  C11-02  the six LI tables: rows per package (CW 2026, CW 2023 = FL's parent),
          live or dead, and no state of the 46 filing any of them.
  (Puerto Rico is excluded throughout -- standing project rule: "all states"
  means the 46, PR excluded.)
  C11-05  every string literal an LI rule compares against has a source (a
          Domain table value, a rate-table key, or a Structure-derived value).
  C11-10  the 11 FactorsFor<N>Percent files are inert: static read, and each
          rate attaches exactly its own marker with no premium.
  C11-03  which of the 47 jurisdictions file LI rules, and which override.
  C11-08  the edition each of FL and PR resolves to.
  OI-107  the DateDifference sign, pinned on Oregon's TRIA days-until
          (ISO +257, confirmed live). Puerto Rico's own runs were removed
          2026-09-22 at the user's direction.
  F1-F3   Florida's chain, run: same arithmetic, sinkhole-in-BGII. Since
          2026-09-24 (FL V02 over CW 2023 V04) the injection guard applies in
          Florida too; under V01 it did not.

    python scripts/cf/120_chunk11_groupsEF_inventory_states.py

Exit 0 means every prediction held.
"""
from __future__ import annotations

import csv
import re
import sys
from decimal import Decimal, ROUND_HALF_UP
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from cf_engine.config import NULL_ARITHMETIC, ROUNDING
from cf_engine.resolve import book_for
from gl_engine.interp import tree
from gl_engine.interp.interpreter import Interpreter
import _iso_refusals as _iso                                    # noqa: E402
from gl_engine.interp.tree import Node, read

g = import_module("114_chunk11_golden_case")
census = import_module("106_chunk11_census")
LI, STRUCT, cell = g.LI, g.STRUCT, g.cell
ASOF = g.ASOF
TABLES = ["LeaseholdInterestAnnuityConstant", "LeaseholdInterestDiscFactor",
          "LeaseholdInterestBroadSpecialRate", "SpecialFormIncldgTheftLeaseHoldBaseRate",
          "SpecialFormExclgTheftLeaseHoldBaseRate",
          "SpecialLeaseHoldTimeElementTheftExclusionFactor"]

ok = True


def verdict(label, good, detail=""):
    global ok
    ok &= bool(good)
    print(f"  {label:66s} {'MATCH' if good else 'MISMATCH'}"
          + (f"   {detail}" if detail else ""))


def same(a, b):
    try:
        return Decimal(str(a)) == Decimal(str(b))
    except Exception:
        return str(a) == str(b)


def rows(pkg, name):
    f = pkg / "Rate Tables" / f"{name}.RateTable.csv"
    if not f.exists():
        return None
    with open(f, encoding="utf-8-sig") as h:
        return sum(1 for r in csv.reader(h) if r) - 1


def books():
    out = {}
    for j in census.JURIS:
        if j == "PR":
            continue                  # standing rule: PR is out of scope
        try:
            out[j] = book_for(j, ASOF)
        except Exception:
            pass
    return out


def run_in(juris, sub):
    ip = Interpreter(book_for(juris, ASOF), rounding=ROUNDING, trace=False,
                     null_arithmetic=NULL_ARITHMETIC)
    data = Node.from_dict(f"MasterCF{juris}", sub)
    ip.run(data)
    return data


# ------------------------------------------------------------------ C11-02
def c11_02(bk):
    print("C11-02  the six LI tables")
    cw26 = bk["OR"].parent.package.content
    cw23 = bk["FL"].parent.package.content
    want = {  # table: (CW26, CW23)
        "LeaseholdInterestAnnuityConstant": (11, 11),
        "LeaseholdInterestDiscFactor": (11, 11),
        "LeaseholdInterestBroadSpecialRate": (6, 6),
        "SpecialFormIncldgTheftLeaseHoldBaseRate": (12, 12),
        "SpecialFormExclgTheftLeaseHoldBaseRate": (0, 0),
        "SpecialLeaseHoldTimeElementTheftExclusionFactor": (2, 2),
    }
    for t, w in want.items():
        got = (rows(cw26, t), rows(cw23, t))
        verdict(f"{t} rows CW26/CW23 = {w}", got == w, f"got {got}")
    n = sum(f.read_text(encoding="utf-8-sig").count(
        'MatrixFromConstant="SpecialFormExclgTheftLeaseHoldBaseRate"')
        for f in (cw26 / "Rules").glob("*.xml"))
    verdict("ExclgTheft table: 0 rows and read by 0 countrywide lookups (dead)",
            n == 0, f"readers={n}")
    filers = sorted(j for j, b in bk.items()
                    if any((b.state.package.content / "Rate Tables" / f"{t}.RateTable.csv").exists()
                           for t in TABLES))
    verdict(f"of {len(bk)} states, none files any of the six", filers == [],
            f"filers={filers}")


# ------------------------------------------------------------------ C11-05
def domain_values(pkgs):
    vals = set()
    for pkg in pkgs:
        for f in (pkg / "Domain Tables").glob("*.DomainTable.csv"):
            with open(f, encoding="utf-8-sig") as h:
                for r in csv.reader(h):
                    vals.update(x.strip() for x in r)
    return vals


def c11_05(bk):
    print("\nC11-05  hardcoded literals")
    cw26 = bk["OR"].parent.package.content
    fl = bk["FL"].state.package.content
    files = list((cw26 / "Rules").glob("CommercialPropertyLeaseholdInterest*.Rule.xml"))
    files += list((fl / "Rules").glob("CommercialPropertyLeaseholdInterest*.Rule.xml"))
    # Regex, not ElementTree: the first version guessed the XML namespace
    # wrong, matched nothing in the LI files, and "passed" on the 2 literals
    # from the attach rule alone -- a vacuous pass caught by its own count.
    lits = set()
    for f in files:
        s = f.read_text(encoding="utf-8-sig")
        for blk in re.findall(r"<rul:(?:Equal|NotEqual)>(.*?)</rul:(?:Equal|NotEqual)>", s, re.S):
            lits.update(x.strip() for x in re.findall(
                r'<rul:Constant Type="string">([^<]+)</rul:Constant>', blk) if x.strip())
    # the Structure's own attach gate for LI
    s = (cw26 / "Rules" / "CommercialPropertyStructureRules.Rule.xml").read_text(encoding="utf-8-sig")
    m = re.search(r'<rul:Rule Name="AttachFormCommercialPropertyLeaseholdInterestCoverageForm".*?</rul:Rule>', s, re.S)
    lits.update(re.findall(r'<rul:Constant Type="string">([^<]+)</rul:Constant>', m.group(0)))
    dom = domain_values([cw26])
    keys = {r["LeaseholdInterestPct"] for r in csv.DictReader(
        open(cw26 / "Rate Tables" / "LeaseholdInterestAnnuityConstant.RateTable.csv", encoding="utf-8-sig"))}
    derived = {"Yes", "No"}                    # ApartmentCondoIndicator, SetApartmentCondoIndicator
    orphans = sorted(x for x in lits if x not in dom and x not in keys and x not in derived)
    verdict(f"{len(lits)} compared literals, all with a source", not orphans,
            f"literals={sorted(lits)} orphans={orphans}")
    verdict("the 11 PercentInterest keys are 5%..15%",
            keys == {f"{n}%" for n in range(5, 16)}, f"{sorted(keys, key=lambda k: int(k[:-1]))}")


# ------------------------------------------------------------------ C11-10
def c11_10(bk):
    print("\nC11-10  the 11 FactorsFor<N>Percent files")
    rules = bk["OR"].parent.package.content / "Rules"
    bad = []
    for n in range(5, 16):
        s = (rules / f"CommercialPropertyLeaseholdInterestFactorsFor{n}PercentRules.Rule.xml").read_text(encoding="utf-8-sig")
        names = re.findall(r'<rul:Rule Name="([^"]+)"', s)
        writes = set(re.findall(r'ToDataDef="([^"]+)"', s))
        mats = set(re.findall(r'MatrixFromConstant="([^"]+)"', s))
        if (set(names) != {"InitializeRuleSet", "CalculateTotalPremium", "ErcProcess"}
                or writes - {"ErcFormName", "ErcFormNumber", "ErcCalculatedTotalPremium"}
                or mats - {"Pages"} or 'ToDataDef="Premium"' in s):
            bad.append((n, names, sorted(writes), sorted(mats)))
    verdict("static: 11 of 11 declare only the 3 system rules, write only form fields",
            not bad, f"{bad}")
    wrong = []
    for n in range(5, 16):
        li = dict(g.LI_RECORD, PercentInterest=f"{n}%")
        d, _ = g.run(g.submission(li=li))
        present = [k for k in range(5, 16) if tree.select(
            f"{STRUCT}/CommercialPropertyLeaseholdInterestFactorsFor{k}PercentTable/"
            f"CommercialPropertyLeaseholdInterestFactorsFor{k}Percent", d)]
        prem = read(f"{STRUCT}/CommercialPropertyLeaseholdInterestFactorsFor{n}PercentTable/"
                    f"CommercialPropertyLeaseholdInterestFactorsFor{n}Percent/Premium", d)
        if present != [n] or prem not in (None, "0"):
            wrong.append((n, present, prem))
    verdict("dynamic: each of 11 rates attaches exactly its own marker, no premium",
            not wrong, f"{wrong}")


# ---------------------------------------------------------- C11-03 / C11-08
def c11_03_08(bk):
    print("\nC11-03 / C11-08  states and editions")
    filing = {}
    for j, b in sorted(bk.items()):
        d = b.state.package.content / "Rules"
        if d.exists():
            fs = sorted(d.glob("CommercialPropertyLeaseholdInterest*.Rule.xml"))
            if fs:
                filing[j] = fs
    verdict(f"of {len(bk)} states, LI rule files in FL (4) only",
            {j: len(v) for j, v in filing.items()} == {"FL": 4},
            f"{ {j: len(v) for j, v in filing.items()} }")
    for j in ("FL",):
        codes = []
        for f in filing.get(j, []):
            s = f.read_text(encoding="utf-8-sig")
            for name, code in re.findall(r'<rul:Rule Name="([^"]+)"[^>]*MetadataCodes="([^"]+)"', s):
                if code in ("RuleTypeOverridden", "RuleTypeStateSpecific"):
                    codes.append((f.name.replace("CommercialPropertyLeaseholdInterestCoverageForm", "")
                                  .replace("Rules.Rule.xml", "") or "(parent)", name, code))
        print(f"      {j}: " + "; ".join(f"{a}.{b} [{c[8:]}]" for a, b, c in codes))
    fl = bk["FL"]
    # 2026-09-24: the user added CF FL 20241201 V02 (the edition ISO rates on, named in its
    # own error text since chunk 6). It rides on CW 20230801 V04; until then FL resolved to
    # V01 over CW 20230801 V01, which is what C11-08 originally recorded.
    verdict("FL = CF_FL_20241201_V02 over CF_CW_20230801_V04",
            (fl.state.pkg_id, fl.parent.pkg_id) == ("CF_FL_20241201_V02", "CF_CW_20230801_V04"),
            f"{fl.state.pkg_id} over {fl.parent.pkg_id}")


# ------------------------------------------------------------------ P / F
def state_runs():
    # Puerto Rico's own runs (P1-P4) were removed 2026-09-22 at the user's
    # direction: PR is out of scope for this project's CF work. What they
    # found -- the DateDifference sign, OI-107 -- is pinned below on Oregon.
    print("\nOI-107  DateDifference sign, pinned on Oregon (offline)")
    sub = g.submission()
    sub["EffDate"] = "09/17/2026"
    cp = sub["CommercialPropertyTable"]["CommercialProperty"][0]
    cp["TRIAType"] = "Will Expire During the Next 12 Months"
    cp["TRIAExpirationDate"] = "06/01/2027"
    d = run_in("OR", sub)
    got = read("CommercialPropertyTable/CommercialProperty/DaysUntilTRIAExpiration", d)
    verdict("DaysUntilTRIAExpiration 2026-09-17 -> 2027-06-01 = +257 (ISO, live)",
            same(got, "257"), f"got {got}")

    print("\nF1-F3  Florida, run")
    d = run_in("FL", _iso.without_oregon_territories(g.submission()))   # C28-05: no Oregon territory in FL
    got = tuple(read(f"{LI}/{f}", d) for f in (
        "NumOfMonthsRemainingAtInception", "NumOfMonthsRemainingAtExpiration",
        "TenantsNetLeaseholdInt"))
    verdict("F1 months 120/108, net 111,958 (2023 chain, same arithmetic)",
            all(same(a, b) for a, b in zip(got, ("120", "108", "111958"))), f"got {got}")
    li = dict(g.LI_RECORD, DiscFactor="0.99")
    d2 = run_in("FL", _iso.without_oregon_territories(g.submission(li=li)))
    got = (read(LI + "/DiscFactor", d2), read(LI + "/TenantsNetLeaseholdInt", d2))
    # Under V01 (CW 2023 V01, no IsNull guard on SetDiscFactor) an injected DiscFactor was
    # overwritten (0.99208894, net 111,958). Under V02 the parent is CW 2023 V04, which
    # guards it, so the injection is KEPT -- exactly Oregon's hand-derived case B
    # (CF-CHUNK11-GOLDEN-CASE.md: 0.99 -> net 128,183). The trap now exists in Florida too.
    verdict("F2 injected DiscFactor 0.99 is kept (V04 guard): 0.99, net 128,183 = Oregon's case B",
            same(got[0], "0.99") and same(got[1], "128183"), f"got {got}")
    adj2 = read(LI + "/BasicGroupIICauseOfLossAdjmt", d)
    sink = read(STRUCT + "/SinkholeRateAdjustment", d)
    net = Decimal(read(LI + "/TenantsNetLeaseholdInt", d))
    rate = (Decimal(str(adj2 or 0)) + Decimal(str(sink or 0))).quantize(Decimal("0.001"), ROUND_HALF_UP)
    want = (rate * net / 100).quantize(Decimal("1"), ROUND_HALF_UP)
    got = read(cell("TenantsLease", "BasicGroupII") + "/Premium", d)
    if same(adj2 or 0, "0") and same(sink or 0, "0"):
        print(f"  F3 BGII = round(round(adjII + sinkhole, 3) x net/100)          "
              f"NOT EXERCISED   adjII={adj2} sinkhole={sink}: the Oregon territory "
              f"is not valid in FL, so both inputs are 0 and a match proves nothing. "
              f"Formula confirmed by reading only.")
    else:
        verdict("F3 BGII = round(round(adjII + sinkhole, 3) x net/100)",
                same(got, want), f"adjII={adj2} sinkhole={sink} -> want {want}, got {got}")


def main() -> int:
    bk = books()
    print(f"{len(bk)} jurisdictions resolved at {ASOF}\n")
    c11_02(bk)
    c11_05(bk)
    c11_10(bk)
    c11_03_08(bk)
    state_runs()
    print()
    print("Groups E and F match every prediction." if ok else
          "MISMATCH -- compare against docs/CF-CHUNK11-GROUPS-E-F.md.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
