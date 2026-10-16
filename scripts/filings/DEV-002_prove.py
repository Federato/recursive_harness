"""DEV-002 (UFG Alabama CF LCMs): T5-style checks on the live carrier store against technical, and the dates.

v2 (B-21) adds the exception pages' terrorism pricing (Rule A11.C: 2% of the total property premium when coverage for
certified acts is taken, IL 09 52) and the policy writing minimum (Rule 8: $300). Our engine only (D21): checked
against technical and the filing's arithmetic, never sent to ISO.

    python scripts/filings/DEV-002_prove.py
"""
import copy
import os
import sys
from decimal import Decimal

ROOT = __import__("pathlib").Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts"), str(ROOT / "scripts" / "cf"), str(ROOT / "tests")]
os.environ["TC_DISPATCH"] = "0"
sys.stdout.reconfigure(encoding="utf-8")
import property_rating as pr
import verify_deviations_engine as E
from cf_engine.rating import rate
from deviations import engine as dv

WANT = {"UFC": {"A": ("2.047", "2.112"), "B": ("1.898", "1.965"), "other": ("2.185", "2.192"), "EQ": "1.529"},
        "LAF": {"A": ("2.559", "2.64"), "B": ("2.373", "2.456"), "other": ("2.731", "2.74"), "EQ": "1.91"}}
CLASSES = {"A": [("1150", None), ("0532", None), ("2000", None)], "B": [("0511", "Service")], "other": [(None, None)]}
ok_all = True


def check(name, ok, detail=""):
    global ok_all
    ok_all &= bool(ok)
    print(f"  {'ok  ' if ok else 'FAIL'} {name}" + (f"  -- {detail}" if detail and not ok else ""))


def req_for(co, cls, cat, date="2025-08-01", pt="New"):
    r = copy.deepcopy(pr.sample("AL", date))
    r["header"].update(WritingCompany=co, PolicyType=pt)
    st = r["body"]["CommercialProperty"][0]["CommercialPropertyLocation"][0]["CommercialPropertyStructure"][0]
    if cls:
        st["ClassCode"] = cls
        oc = st["CommercialPropertyOccupClass"][0]
        oc["ClassCode"] = cls
        if cat:
            oc["OccupCategory"] = cat
    return r, st


print("DEV-002 UFG Alabama CF LCMs: proof on the live carrier store")
for co in ("UFC", "LAF"):
    for grp, tries in CLASSES.items():
        res = None
        for cls, cat in tries:
            q, st = req_for(co, cls, cat)
            r = rate(q, with_technical=True, waterfall=False)
            if r.tree is not None and r.technical is not None and r.technical.tree is not None:
                res = (cls or st["ClassCode"], r)
                break
        if res is None:
            check(f"{co} group {grp}: a sample risk rates", False, str(getattr(r, "outcome", "")))
            continue
        cls, r = res
        notes = [n.data for n in r.ip.trace if n.kind == "company-group-lcm"]
        got = {}
        for n in notes:
            got.setdefault(n["group"], set()).add(str(Decimal(n["value"]).normalize()))
        g1, g2 = (Decimal(x).normalize() for x in WANT[co][grp])
        exp = {"GroupI": {str(g1)}, "GroupII": {str(g2)}, "Broad": {str(g2)}, "Special": {str(g2)},
               "Earthquake": {str(Decimal(WANT[co]["EQ"]).normalize())}}
        bad = {k: v for k, v in got.items() if k in exp and v != exp[k]}
        check(f"{co} class {cls} (group {grp}): {len(notes)} group-rate products read exactly the filed LCMs "
              f"{dict((k, sorted(v)) for k, v in sorted(got.items()))}", notes and not bad, str(bad))
        st_c, st_t = E._structure(r.tree), E._structure(r.technical.tree)
        want = {"GroupI": ("BasicGroupIRate", g1), "GroupII": ("BasicGroupIIRate", g2)}
        bad = []
        for g, (f, L_) in want.items():
            if st_c.first(f) is None:
                continue
            tv, cv = Decimal(st_t.first(f).text), Decimal(st_c.first(f).text)
            if abs(cv - tv * L_) > Decimal("0.0005") * (L_ + 2):
                bad.append(f"{f}: {tv} x {L_} vs {cv}")
        check(f"{co} class {cls}: Group I and II rates scale by their own LCM (technical x LCM, ISO's rounding)",
              not bad, "; ".join(bad))
        print(f"       premium: technical {r.technical.premium} -> {co} {r.premium}")

print("dates")
for co in ("UFC", "LAF"):
    for date, pt, inforce in (("2025-07-14", "New", False), ("2025-07-15", "New", True),
                              ("2025-10-31", "Renewal", False), ("2025-11-01", "Renewal", True)):
        plan = dv.plan_for("CF", co, "AL", date, pt)
        f = [x["id"] for x in plan.filings] if hasattr(plan, "filings") else []
        has = bool(plan.group_lcm)
        check(f"{co} {pt} on {date}: filing {'in force' if inforce else 'not in force'}", has == inforce,
              f"group LCMs present: {has}")

print("v2 (B-21): terrorism at 2% and the $300 minimum")


def terror_req(co, small=False):
    r, _ = req_for(co, None, None)
    pol = r["body"]["CommercialProperty"][0]
    if not small:     # ISO attaches IL 09 52 and charges terrorism when coverage for certified acts is taken
        pol.update(CoverageForCertifiedActs="Yes", TRIAType="Is in Effect for the Next 12 Months")
    else:             # a small risk: limits a hundredth of the sample's
        def shrink(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    if k == "Limit" and isinstance(v, (int, float)):
                        o[k] = int(v / 100)
                    else:
                        shrink(v)
            elif isinstance(o, list):
                for x in o:
                    shrink(x)
        shrink(pol)
    return r


def field(tree, tag):
    out, stack = [], [tree]
    while stack:
        n = stack.pop()
        stack.extend(n.children)
        if n.tag == tag and n.text not in (None, ""):
            out.append(Decimal(n.text))
    return out


for co in ("UFC", "LAF"):
    plan = dv.plan_for("CF", co, "AL", "2025-08-01", "New")
    check(f"{co}: v2 is in force with both policy items ({plan.ref})",
          plan.ref == "AL-CF-UNFG-134461534.v2" and set(plan.policy) == {"PCT:Terrorism", "MIN:Policy"},
          f"{plan.ref} {sorted(plan.policy)}")
    q, _ = req_for(co, None, None)
    r = rate(q, with_technical=True)
    wf = {x["step"]: Decimal(x["effect"]) for x in r.deviation["waterfall"]}
    check(f"{co}: no terrorism taken -> no terrorism charged by either (steps {wf.get('terrorism at 2% of premium')}, "
          f"{wf.get('policy minimum $300')})", wf.get("terrorism at 2% of premium") == 0
          and wf.get("policy minimum $300") == 0 and not field(r.tree, "CompanyTerrorismPremium"))
    r = rate(terror_req(co), with_technical=True)
    iso_t = sum(field(r.technical.tree, "TerrorismPremium"))
    mine = field(r.tree, "CompanyTerrorismPremium")
    total = Decimal(r.premium)
    want = ((total - (mine[0] if mine else 0)) * Decimal("0.02")).quantize(Decimal(1), rounding="ROUND_HALF_UP")
    check(f"{co}: terrorism taken -> technical carries ISO's charge {iso_t}; carrier charges {mine} = 2% of the rest "
          f"of its premium ({total} - terrorism, {want})", iso_t > 0 and mine == [want], f"{mine} vs {want}")
    wf = {x["step"]: x["effect"] for x in r.deviation["waterfall"]}
    steps = sum(Decimal(x["effect"]) for x in r.deviation["waterfall"])
    check(f"{co}: the waterfall {wf} adds up from technical {r.technical.premium} to carrier {r.premium}",
          steps == total - Decimal(r.technical.premium) and Decimal(wf["terrorism at 2% of premium"]) > 0)
    s_ = rate(terror_req(co, small=True), with_technical=True)
    wf = {x["step"]: Decimal(x["effect"]) for x in s_.deviation["waterfall"]}
    before = Decimal(s_.premium) - wf["policy minimum $300"]
    check(f"{co}: a small risk (technical {s_.technical.premium}, carrier before the minimum {before}) is raised to "
          f"{s_.premium}; MinimumPremium {field(s_.tree, 'MinimumPremium')}",
          Decimal(s_.premium) == 300 and before < 300 and field(s_.tree, "MinimumPremium") == [Decimal(300)]
          and not field(s_.technical.tree, "MinimumPremium"))
print("PASS" if ok_all else "FAIL")
