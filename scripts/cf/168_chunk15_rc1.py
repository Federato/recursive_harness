#!/usr/bin/env python3
"""Chunk 15, RC-1 (C15-02 to C15-05): evidence and plumbing, before any golden case.

C15-05  ATTACH MAP. Where each of the 23 countrywide records (and VA's 6) sits,
        read from ISO's own DataDef XSD -- its parent record, and whether it is
        a repeating Table (a `../` from inside a Table row first reaches the
        wrapper) -- plus which rule file dispatches it, and what the 3 container
        files do. Gate 2: the family reads 0 rate tables.
C15-03  MODIFIER PATHS. Every record is placed on chunk 7's five-coverage
        Oregon policy (plus VA's six on a Virginia copy), the engine runs, and
        every `FromDataDef` operand of its `SetPremium` is resolved with the
        engine's own `select` from the record node. Reported: the record each
        path lands on, and its value. Flagged: a path that lands on a Table
        wrapper, lands nowhere, or lands on a different record type from its
        sibling files' same operand.
C15-04  ROUNDING. The order and rounding of each Product per file, the mode
        (half-up, proved against ISO 2026-09-17, cf_engine.config.ROUNDING),
        and every literal (gate 5). The engine's premium on the placed tree is
        checked against a step-by-step hand computation from the landed values.
C15-02  STORED EVIDENCE. The stored ISO responses that carry a chunk 15 record:
        what ISO returns on it (Premium, echoed fields), whether the request
        carried a ManualPremium, and ours on the same fixture. No ISO calls.

    python scripts/cf/168_chunk15_rc1.py

Exits 1 on any check that fails.
"""
from __future__ import annotations

import collections
import copy
import json
import re
import sys
import xml.etree.ElementTree as ET
from decimal import Decimal, ROUND_HALF_UP
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))

from cf_engine.config import ROUNDING
from cf_engine.resolve import book_for
from gl_engine.interp import tree
from gl_engine.interp.values import InterpretError

gc = import_module("149_chunk13_golden_case")
grp = import_module("150_chunk13_c13-08-09_groups_rollup")
rep = import_module("157_chunk14_c14-02_total_replay")
ASOF = "20260917"
ISO_CF = Path("C:/Projects/ISO_ERC_Files/CF")
RES = ROOT / "results" / "cf-raas"
XS = "{http://www.w3.org/2001/XMLSchema}"
P = "CommercialProperty"

#: the 23 countrywide premium files of chunk 15 (167_), record = file stem minus "Rules"
CW_RECORDS = [
    "CannabisExclusionBuilding", "CannabisExclusionPersonalProperty", "CannabisExclusionBusinessIncome",
    "CannabisExclusionSpecialClass", "CannabisExclusionSpecialClassBusinessIncome",
    "CannabisExclusionWithHempExceptionBuilding", "CannabisExclusionWithHempExceptionPersonalProperty",
    "CannabisExclusionWithHempExceptionBusinessIncome", "CannabisExclusionWithHempExceptionSpecialClass",
    "CannabisExclusionWithHempExceptionSpecialClassBusinessIncome",
    "ValuablePapersAndRecsOTElectronicDataCoverage", "LocationNewlyAcquiredLocationTimeElement",
    "NewlyAcquiredOrConstructedPropertyIncreasedLimit", "OccupClassTemporarilyInPortableStorageUnits",
    "DiscretionaryPayrollExpense", "DiscretionaryPayrollExpenseSpclClassBusnIncome",
    "ElectronicCommerceLossOfBusinessIncomeCov", "ElectronicCommerceLossOfDataCov",
    "BusnPrsnlPropLimitedInternationalCov", "PropInProcessOfMfrByOthersLimitedInternationalCov",
    "BusinessIncomeInterruptionOfComputerOperationsCoverage",
    "SpecialClassBusnIncomeInterruptionOfComputerOperationsCoverage",
    "BusinessIncomeAndOrExtraExpnCovForY2KComputerRelatedAndOtherElectronicProblems",
]
CONTAINERS = ["DiscretionaryPayrollExpenseDetail", "DiscretionaryPayrollExpenseSpclClassBusnIncomeDetail",
              "ElectronicCommerce"]
VA_RECORDS = [
    "BusIncSpcClsAndExtraExpnCovForY2KComputerRelatedAndOtherElectronicProblems",
    "BusIncSpcClsWOExtraExpnCovForY2KComputerRelatedAndOtherElectronicProblems",
    "BusinessIncomeSpcClsAndExtraExpnCovForY2KComputerRelatedAndOtherElectronicProblems",
    "BusinessIncomeSpcClsWOExtraExpnCovForY2KComputerRelatedAndOtherElectronicProblems",
    "ExtraExpnCovForY2KComputerRelatedAndOtherElectronicProblemsBusiness",
    "ExtraExpnCovForY2KComputerRelatedAndOtherElectronicProblemsSpecialClass",
]
#: modifier values placed on the policy, distinct so a landed value names its source
POLICY_MODS = {"IRPMFactor": "1.1", "PackageModFactor": "0.8",
               "MultiPremiumAndDispersionCreditFactorUser": "0.9"}
MANUAL = "1000"
FAIL = []
#: each record's own on-switch (SetCoverageOnPolicyIndicator); without it ErcProcess writes Premium 0
SWITCH = {"LocationNewlyAcquiredLocationTimeElement": {"Indicator": "Yes"},
          "OccupClassTemporarilyInPortableStorageUnits": {"TemporarilyInPortableStorageUnitsIndicator": "Yes"},
          "BusinessIncomeInterruptionOfComputerOperationsCoverage": {"InterruptionCompuOpsIndicator": "Yes", "Limit": "10000"},
          "SpecialClassBusnIncomeInterruptionOfComputerOperationsCoverage": {"InterruptionCompuOpsIndicator": "Yes", "Limit": "10000"}}
#: Valuable Papers switches on from its PARENT: ../CovType on the Personal Property row
VP = "ValuablePapersAndRecsOTElectronicDataCoverage"
VP_COVTYPE = "Valuable Papers and Records - Other Than Electronic Data"
#: where each modifier is expected to land (the prediction C15-03 tests)
POLICY = P
EXPECT_MPDC = {"LocationNewlyAcquiredLocationTimeElement": POLICY,
               "OccupClassTemporarilyInPortableStorageUnits": POLICY,
               "ElectronicCommerceLossOfBusinessIncomeCov": POLICY, "ElectronicCommerceLossOfDataCov": POLICY,
               # written ../ x5 from a child of Personal Property: past the Contents row, its
               # Table and the occupancy, onto the BUILDING -- unlike every other Contents
               # endorsement (x2, the Contents row). As filed; ISO settles it in C15-06.
               VP: P + "Structure"}


def check(ok, msg):
    print(f"    [{'ok' if ok else 'FAIL'}] {msg}")
    if not ok:
        FAIL.append(msg)


# ------------------------------------------------------------------ C15-05 XSD

class Xsd:
    def __init__(self, paths):
        self.kids = collections.defaultdict(list)    # type -> [(element name, element type, repeating)]
        for p in paths:
            root = ET.parse(p).getroot()
            for ct in root.iter(f"{XS}complexType"):
                name = ct.get("name")
                if not name:
                    continue
                rep = ct.find(f"{XS}choice") is not None and ct.find(f"{XS}choice").get("maxOccurs") == "unbounded"
                for el in ct.iter(f"{XS}element"):
                    if el.get("type"):
                        self.kids[name].append((el.get("name"), el.get("type"), rep))
        self.parents = collections.defaultdict(list)
        for ptype, kids in self.kids.items():
            for ename, etype, rep in kids:
                self.parents[etype].append((ptype, ename, rep))

    def chain(self, rtype):
        """record type -> [(type, element, via-Table)] up to the root, first parent each step."""
        out, t, seen = [], rtype, set()
        while t in self.parents and t not in seen:
            seen.add(t)
            ptype, ename, rep = self.parents[t][0]
            out.append((t, rep))
            t = ptype
        out.append((t, False))
        return out

    def attach(self, rec):
        """(parent record, via Table?) for P+rec."""
        full = P + rec
        for ptype, ename, rep in self.parents.get(full, []):
            if ptype == full + "Table":
                for pp, _, _ in self.parents.get(ptype, []):
                    return pp, True
            return ptype, False
        return None, None


def xsd_for(book):
    paths = [book.parent.package.content / "DataDefs" / "MasterCFCW.DataDef.xsd"]
    sd = book.state.package.content / "DataDefs"
    paths += sorted(sd.glob("*.xsd")) if sd.exists() else []
    return Xsd(paths)


def dispatchers(all_rules, rec):
    stem = P + rec + "Rules"
    return sorted({n.replace(P, "").replace("Rules.Rule.xml", "") for n, s in all_rules.items()
                   if f'FileName="{stem}"' in s and n != stem + ".Rule.xml"})


# --------------------------------------------------------------- placement

def node_dicts(sub):
    """engine-shape dicts for each attach point on the five-coverage policy."""
    cp = sub["CommercialPropertyTable"]["CommercialProperty"][0]
    loc = cp["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0]
    st = loc["CommercialPropertyStructureTable"]["CommercialPropertyStructure"][0]
    oc = st["CommercialPropertyOccupClassTable"]["CommercialPropertyOccupClass"][0]
    return {P: cp, P + "Location": loc, P + "Structure": st, P + "OccupClass": oc,
            P + "PersonalProperty": oc["CommercialPropertyPersonalPropertyTable"]["CommercialPropertyPersonalProperty"][0],
            P + "BusinessIncome": st["CommercialPropertyBusinessIncomeTable"]["CommercialPropertyBusinessIncome"][0],
            P + "SpecialClass": loc["CommercialPropertySpecialClassTable"]["CommercialPropertySpecialClass"][0],
            P + "SpecialClassBusnIncome": loc["CommercialPropertySpecialClassTable"]["CommercialPropertySpecialClass"][0]
            ["CommercialPropertySpecialClassBusnIncomeTable"]["CommercialPropertySpecialClassBusnIncome"][0]}


def place(sub, xsd, recs, fields):
    at = node_dicts(sub)
    placed = {}
    if VP in recs:
        oc = at[P + "OccupClass"]
        vp_pp = copy.deepcopy(at[P + "PersonalProperty"])
        vp_pp["CovType"] = VP_COVTYPE
        vp_pp[P + VP] = {"ManualPremium": MANUAL}
        oc[P + "PersonalPropertyTable"][P + "PersonalProperty"].append(vp_pp)
        placed[VP] = "PersonalProperty (its own row, CovType = Valuable Papers)"
    ecom = [r for r in recs if r.startswith("ElectronicCommerce")]
    if ecom:
        at[P][P + "ElectronicCommerceTable"] = {P + "ElectronicCommerce": [
            {P + r: {"ManualPremium": MANUAL} for r in ecom}]}
        for r in ecom:
            placed[r] = "ElectronicCommerce (policy, via Table)"
    for rec in recs:
        if rec in placed:
            continue
        parent, table = xsd.attach(rec)
        tgt = at.get(parent)
        if tgt is None:
            placed[rec] = f"no attach point on the policy for parent {parent}"
            continue
        row = dict(fields.get(rec, {}), ManualPremium=MANUAL)
        if table:
            tgt.setdefault(P + rec + "Table", {P + rec: []})[P + rec].append(row)
        else:
            tgt[P + rec] = row
        placed[rec] = parent.replace(P, "") + (" (Table)" if table else "")
    return placed


def find(data, tag):
    out = []

    def walk(n):
        if n.tag == tag:
            out.append(n)
        for c in n.children:
            walk(c)
    walk(data)
    return out


def rec_of(node):
    """the record a path landed on, for naming."""
    if node.tag == P:
        return "CommercialProperty (policy)"
    return node.tag.replace(P, "") + ("  <-- TABLE WRAPPER" if node.tag.endswith("Table") else "")


def premium_ops(text):
    m = re.search(r'<rul:Rule Name="SetPremium".*?</rul:Rule>', text, re.S)
    if not m:
        return None, None
    body = m.group(0)
    return re.findall(r'FromDataDef="([^"]+)"', body), body


def hand(body, vals):
    """evaluate SetPremium's nested Products by hand, half-up at each DecimalPlaces."""
    root = ET.fromstring(body.replace("rul:", "").replace('xmlns:rul', 'x'))

    def ev(e):
        if e.tag == "FirstValue":
            v = vals.get(e.get("FromDataDef"))
            return Decimal(v) if v not in (None, "") else Decimal(e.get("FromConstant"))
        if e.tag == "Product":
            r = Decimal(1)
            for c in e:
                r *= ev(c)
            dp = e.get("DecimalPlaces")
            return r.quantize(Decimal(1).scaleb(-int(dp)), ROUND_HALF_UP) if dp is not None else r
        for c in e:
            return ev(c)
    return ev(root.find(".//Product"))


def audit(data, recs, rules_text, label):
    """C15-03 + C15-04 on one rated tree."""
    landed = collections.defaultdict(dict)      # operand name -> {record: landed record}
    print(f"\n  {label}")
    for rec in recs:
        nodes_ = find(data, P + rec)
        if not nodes_:
            check(False, f"{rec}: record not on the rated tree")
            continue
        # the engine creates an empty record on every eligible parent; audit the one we filled
        n = next((x for x in nodes_ if x.first("ManualPremium") is not None), nodes_[0])
        ops, body = premium_ops(rules_text[rec])
        vals, where = {}, []
        for op in ops:
            hit = tree.select_one(op, n)
            name = op.rsplit("/", 1)[-1]
            if hit is None:
                where.append(f"{name}: NOWHERE")
                landed[name][rec] = None
                continue
            owner = hit.parent
            vals[op] = hit.text
            landed[name][rec] = owner.tag
            where.append(f"{name}@{op.count('../')} -> {rec_of(owner)} = {hit.text}")
        prem = n.first("Premium")
        got = None if prem is None else prem.text
        want = hand(body, vals)
        print(f"    {rec}")
        for w in where:
            print(f"        {w}")
        check(got is not None and Decimal(got) == want,
              f"{rec}: engine Premium {got}, hand (half-up at each step, landed values) {want}")
        for w in where:
            if "TABLE WRAPPER" in w or "NOWHERE" in w:
                check(False, f"{rec}: {w}")
        parent = n.parent.parent if n.parent.tag.endswith("Table") else n.parent
        for op in ops:
            name = op.rsplit("/", 1)[-1]
            if name == "ManualPremium":
                continue
            want_on = POLICY if name in ("IRPMFactor", "PackageModFactor") else EXPECT_MPDC.get(rec, parent.tag)
            check(landed[name].get(rec) == want_on,
                  f"{rec}: {name} lands on {str(landed[name].get(rec)).replace(P, '') or 'policy'}, "
                  f"predicted {want_on.replace(P, '') or 'policy'}")
    return landed


def main():
    cw_book = book_for("OR", ASOF)
    va_book = book_for("VA", ASOF)
    cw = cw_book.parent.package.content
    all_rules = {f.name: f.read_text(encoding="utf-8-sig") for f in (cw / "Rules").glob("*.xml")}
    va_rules = {f.name: f.read_text(encoding="utf-8-sig") for f in (va_book.state.package.content / "Rules").glob("*.xml")}
    text = {r: all_rules[P + r + "Rules.Rule.xml"] for r in CW_RECORDS}
    text.update({r: va_rules[P + r + "Rules.Rule.xml"] for r in VA_RECORDS})
    xsd, va_xsd = xsd_for(cw_book), xsd_for(va_book)
    print(f"{cw_book}\n{va_book}\nrounding mode: {ROUNDING}")

    # ---------------------------------------------------------------- C15-05
    print("\n" + "=" * 78 + "\nC15-05  ATTACH MAP (DataDef XSD)\n" + "-" * 78)
    for rec in CW_RECORDS + CONTAINERS:
        parent, table = xsd.attach(rec)
        ch = " > ".join(t.replace(P, "") + ("[]" if r else "") for t, r in reversed(xsd.chain(P + rec)))
        print(f"  {rec}\n      parent {str(parent).replace(P, '')}{' via Table' if table else ''};"
              f" dispatched by {', '.join(dispatchers(all_rules, rec)) or 'its own ErcProcess only'}\n      {ch}")
        check(parent is not None, f"{rec}: attach point found in the XSD")
    for rec in VA_RECORDS:
        parent, table = va_xsd.attach(rec)
        print(f"  VA {rec}\n      parent {str(parent).replace(P, '')}{' via Table' if table else ''}")
        check(parent is not None, f"VA {rec}: attach point found in the VA XSD")
    print("\n  Container files (no SetPremium):")
    for rec in CONTAINERS:
        s = all_rules[P + rec + "Rules.Rule.xml"]
        kids = [k for k, _, _ in xsd.kids.get(P + rec, []) if k.startswith(P)]
        print(f"    {rec}: rules {re.findall(r'<rul:Rule Name=\"([^\"]+)\"', s)}; child records {[k.replace(P, '') for k in kids]}")
    tables = set()
    for r in CW_RECORDS + VA_RECORDS:
        tables |= set(re.findall(r'MatrixFromConstant="([^"]+)"', text[r])) - {"Pages"}
    check(not tables, f"gate 2: rate tables read by the 29 premium files: {sorted(tables) or 0}")

    # ------------------------------------------------------- C15-03 / C15-04
    print("\n" + "=" * 78 + "\nC15-03 / C15-04  MODIFIER PATHS AND ROUNDING (engine tree)\n" + "-" * 78)
    print(f"  policy modifiers set: {POLICY_MODS}; ManualPremium {MANUAL} on every record")
    fields = {"BusinessIncomeInterruptionOfComputerOperationsCoverage": {"Limit": "10000"},
              "SpecialClassBusnIncomeInterruptionOfComputerOperationsCoverage": {"Limit": "10000"}}
    sub = grp.five()
    sub["CommercialPropertyTable"]["CommercialProperty"][0].update(POLICY_MODS)
    fields.update(SWITCH)
    placed = place(sub, xsd, CW_RECORDS, fields)
    for r, p in placed.items():
        if p.startswith("no attach"):
            check(False, f"{r}: {p}")
    try:
        data, ip = gc.run(sub, "OR")
    except InterpretError as exc:
        check(False, f"OR tree raised: {exc}")
        return 1
    landed = audit(data, CW_RECORDS, text, "Oregon, 23 countrywide records")

    vsub = grp.five()
    vsub["CommercialPropertyTable"]["CommercialProperty"][0].update(POLICY_MODS)
    place(vsub, va_xsd, VA_RECORDS + ["BusinessIncomeAndOrExtraExpnCovForY2KComputerRelatedAndOtherElectronicProblems"], {})
    try:
        vdata, _ = gc.run(vsub, "VA")
        landed_va = audit(vdata, VA_RECORDS, text, "Virginia, its 6 state-only Y2K records")
        y2k = find(vdata, P + "BusinessIncomeAndOrExtraExpnCovForY2KComputerRelatedAndOtherElectronicProblems")
        prem = y2k[0].first("Premium") if y2k else None
        print(f"    VA, countrywide Y2K record (ErcRate emptied in VA): Premium = "
              f"{None if prem is None else prem.text!r}")
        for k, v in landed_va.items():
            for r, o in v.items():
                landed[k][f"VA {r}"] = o
    except InterpretError as exc:
        check(False, f"VA tree raised: {exc}")

    print("\n  Where each modifier lands, by record type (C15-03 summary):")
    for op, by in sorted(landed.items()):
        dist = collections.Counter(str(o).replace(P, "") for o in by.values())
        print(f"    {op}: {dict(dist)}")

    # ---------------------------------------------------------------- C15-02
    print("\n" + "=" * 78 + "\nC15-02  STORED EVIDENCE (no ISO calls)\n" + "-" * 78)
    names = {P + r for r in CW_RECORDS + VA_RECORDS}
    index = rep.fixture_index()
    carry = collections.defaultdict(list)
    for rpath in sorted(RES.glob("chunk13_fixture_*_response.json")):
        t = rpath.read_text(encoding="utf-8")
        for nm in names:
            if f'"{nm}"' in t:
                carry[nm].append(rpath)
    for nm in sorted(carry):
        paths = carry[nm]
        nonzero, manual_req, echoed = [], 0, collections.Counter()
        for rpath in paths:
            resp = json.loads(rpath.read_text(encoding="utf-8"))
            stem = rpath.name[len("chunk13_fixture_"):-len("_response.json")]
            req = index[stem].read_text(encoding="utf-8-sig")
            if re.search(rf'"{nm}"\s*:\s*[\[{{][^\]}}]*"ManualPremium"\s*:\s*"?[1-9]', req):
                manual_req += 1

            def walk(o, k=None):
                if isinstance(o, dict):
                    if k == nm:
                        echoed.update(o.keys())
                        if o.get("Premium") not in (None, "", 0, "0", "0.0"):
                            nonzero.append((stem, o.get("Premium"), o.get("ManualPremium")))
                    for kk, v in o.items():
                        if isinstance(v, (dict, list)):
                            walk(v, kk)
                elif isinstance(o, list):
                    for x in o:
                        walk(x, k)
            walk(resp["Body"])
        print(f"  {nm.replace(P, '')}: in {len(paths)} stored responses; request carries a ManualPremium in "
              f"{manual_req}; ISO premium non-zero in {len(nonzero)}")
        print(f"      ISO echoes: {sorted(echoed)}")
        for stem, prem, man in nonzero:
            d = json.loads(index[stem].read_text(encoding="utf-8-sig"))
            req = {"header": {}, "body": {"SchemeKeys": {"ProductName": d["SchemeKeys"]["ProductName"],
                                                         "EffectiveDateTime": "2026-09-17T00:00:00"},
                                          "CommercialProperty": d["CommercialProperty"]}}
            data, _ = rep.cmp.rate(req)
            ours = [x.first("Premium").text if x.first("Premium") is not None else None for x in find(data, nm)]
            check(any(o is not None and Decimal(o) == Decimal(str(prem)) for o in ours),
                  f"{stem} ({d['SchemeKeys']['ProductName'].split()[-1]}): ISO {prem} (ManualPremium {man}), ours {ours}")
        if not nonzero:
            check(manual_req == 0, f"{nm.replace(P, '')}: ISO $0 everywhere, and no request enters a ManualPremium")

    print("\n" + ("RC-1: ALL CHECKS PASS" if not FAIL else f"RC-1: {len(FAIL)} FAILED"))
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
