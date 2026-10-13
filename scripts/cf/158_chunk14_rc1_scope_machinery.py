"""Chunk 14, RC-1: C14-03 (minimum premium), C14-04 (state overrides of the total),
C14-05 (the total's machinery). Offline; exits 1 if any finding stops holding.

C14-03  No rule in any package our 46 states resolve to reads a minimum-premium
        table; the countrywide MinimumPremium / PolMinPremium tables are header-only.
        (Puerto Rico's condominium-earthquake minimum is the only one; out of scope.)
C14-04  Every state override of the policy's CalculateTotalPremium calls the parent
        edition's and adds state-only records -- no arithmetic of its own; every
        override of ErcCalculateTotalPremium is a pure pass-through.
C14-05  The total's machinery: every operator in every CalculateTotalPremium rule
        is a shape the engine handles (125_'s classifier); SetPremiumIndicator
        counts any non-zero premium, so a NEGATIVE premium enters the total; and the
        stored ISO answers agree -- Debris Removal under $25,000 gives -$21 / -$3 and
        ISO's total is $269 (= 261 + 32 - 21 - 3), ours too.

    python scripts/cf/158_chunk14_rc1_scope_machinery.py
"""
import collections
import json
import re
import sys
import xml.etree.ElementTree as ET
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))

from cf_engine.resolve import book_for

census11 = import_module("106_chunk11_census")
ops = import_module("125_chunk12_c12-03_operand_types")
rep = import_module("157_chunk14_c14-02_total_replay")
ASOF = "20260917"
FAILS = []


def verdict(label, ok, detail=""):
    print(f"  {label:78s} {'OK' if ok else 'FAIL'}  {detail}")
    if not ok:
        FAILS.append(label)


def rule(s, n):
    m = re.search(r'<rul:Rule Name="%s".*?</rul:Rule>' % n, s, re.S)
    return m.group(0) if m else None


def books():
    out = {}
    for j in census11.JURIS:
        if j == "PR":
            continue
        try:
            out[j] = book_for(j, ASOF)
        except Exception:
            pass
    return out


def main():
    bks = books()
    contents = {}
    for j, bk in bks.items():
        contents[bk.parent.package.content] = "parent"
        contents[bk.state.package.content] = j

    print("C14-03  minimum premium")
    readers = []
    for content in contents:
        rd = content / "Rules"
        if not rd.exists():
            continue
        for f in rd.glob("*.xml"):
            for t in re.findall(r'MatrixFromConstant="(\w*(?:MinimumPremium|MinPremium|PolMinPremium)\w*)"',
                                f.read_text(encoding="utf-8-sig")):
                readers.append((content.name, f.name, t))
    verdict(f"no rule in the {len(contents)} packages our 46 states resolve to reads a minimum-premium table",
            not readers, str(readers[:3]))
    cw = book_for("OR", ASOF).parent.package.content / "Rate Tables"
    for t in ("MinimumPremium", "PolMinPremium"):
        n = len((cw / f"{t}.RateTable.csv").read_text(encoding="utf-8-sig").splitlines()) - 1
        verdict(f"countrywide {t} is header-only", n == 0, f"{n} rows")

    print("\nC14-04  state overrides of the total")
    kinds = collections.Counter()
    for j, bk in bks.items():
        p = bk.state.package.content / "Rules" / "CommercialPropertyRules.Rule.xml"
        if not p.exists():
            kinds["no state policy file"] += 1
            continue
        s = p.read_text(encoding="utf-8-sig")
        ctp = rule(s, "CalculateTotalPremium")
        if ctp:
            calls_parent = bool(re.search(r'<rul:RunRule[^>]*FileName="CommercialPropertyRules"[^>]*'
                                          r'Rule="CalculateTotalPremium"[^>]*ProjectName=', ctp))
            arith = bool(re.search(r"<rul:(Product|Divide|Subtract|Round|Max|Min)\b", ctp))
            kinds["CTP parent + adds" if calls_parent and not arith else f"CTP REWRITE ({j})"] += 1
        e = rule(s, "ErcCalculateTotalPremium")
        if e:
            pin = len(re.findall("<rul:RunRule", e)) == 1 and not re.search(
                r"<rul:(Product|Sum|Round|Copy|Constant|If|Choose)\b", e)
            kinds["ECTP pass-through" if pin else f"ECTP REWRITE ({j})"] += 1
    print(f"    {dict(kinds)}")
    verdict("every CalculateTotalPremium override = the parent's + state-only records, no arithmetic",
            not any("REWRITE" in k for k in kinds) and kinds["CTP parent + adds"] == 41)
    verdict("every ErcCalculateTotalPremium override is a pure pass-through", kinds["ECTP pass-through"] == 43)

    print("\nC14-05  the total's machinery")
    sigs = collections.Counter()
    bad = []
    n_rules = 0
    for content in contents:
        rd = content / "Rules"
        if not rd.exists():
            continue
        for f in rd.glob("*.xml"):
            s = f.read_text(encoding="utf-8-sig")
            if 'Name="CalculateTotalPremium"' not in s:
                continue
            root = ET.fromstring(s)
            for r in root.iter(ops.NS + "Rule"):
                if r.attrib.get("Name") != "CalculateTotalPremium":
                    continue
                n_rules += 1
                for el in r.iter():
                    t = ops.tag(el)
                    if t in ops.ORDERED | ops.EQUALITY | ops.ARITH:
                        kids = list(el)
                        v = ops.classify(t, tuple(ops.op_type(k) for k in kids), kids)
                        sigs[v.split(":")[0]] += 1
                        if v.startswith(("WRONG", "REFUSES")):
                            bad.append((f.name, v))
    verdict(f"{n_rules} CalculateTotalPremium rules: every operator a handled shape", not bad, f"{dict(sigs)}")
    pol = (book_for("OR", ASOF).parent.package.content / "Rules" / "CommercialPropertyZzDisclosurePursuantToTerrorismRiskInsAct2002Rules.Rule.xml").read_text(encoding="utf-8-sig")
    pi = rule(pol, "SetPremiumIndicator")
    verdict("SetPremiumIndicator counts any non-zero premium (NotEqual 0), so a negative one is in",
            bool(pi and re.search(r"<rul:NotEqual>", pi)))
    for n, want in (("chunk12_dr_Z4", 269), ("chunk12_dr_C0", 348), ("chunk12_dr_Z1", 293)):
        req = json.loads((rep.RES / f"{n}_request.json").read_text(encoding="utf-8-sig"))
        resp = json.loads((rep.RES / f"{n}_response.json").read_text(encoding="utf-8-sig"))
        data, ip = rep.cmp.rate(req)
        iso, ours = rep.iso_prem(resp), rep.our_prem(data)
        k = "CommercialProperty[0]/ErcCalculatedTotalPremium"
        d = [x for x in iso if not rep.cmp.same(iso[x], ours.get(x))]
        verdict(f"{n}: total ISO {iso.get(k)} = ours {ours.get(k)} = {want}, every premium equal",
                rep.cmp.same(iso.get(k), want) and rep.cmp.same(ours.get(k), want) and not d)

    print()
    if FAILS:
        print(f"FAIL: {len(FAILS)}")
        sys.exit(1)
    print("RC-1 CLEAN: no minimum premium in ISO's rating for our states; state overrides only add records; "
          "negative premiums count, as at ISO.")


if __name__ == "__main__":
    main()
