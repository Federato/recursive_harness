"""DEV-002 (UFG Alabama CF LCMs): T5-style checks on the live carrier store against technical, and the dates.

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
print("PASS" if ok_all else "FAIL")
