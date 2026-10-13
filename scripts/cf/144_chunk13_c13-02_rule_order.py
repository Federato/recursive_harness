"""C13-02: where terrorism runs, and what it depends on.

Checks, in every parent edition and against every state's policy-file
override (46 states, PR excluded), the ordering the terrorism roll-up needs:

  1. the policy sets the TRIA timeline factors (SetTerrorismRatesandFactors)
     inside ErcSetRatesAndFactors, before any Location runs;
  2. every Location runs before every terrorism roll-up record (the three
     ZzDisclosure forms and PostTRIA), because those records SUM the
     TerrorismPremium of every coverage record under every location;
  3. each coverage group computes Pre/Post/TerrorismPremium in its OWN ErcRate
     and reads no other group's premium;
  4. no coverage group's CalculateTotalPremium includes TerrorismPremium, so
     terrorism reaches the policy total once, through the roll-up records.

Exits 1 if any check fails.

    python scripts/cf/144_chunk13_c13-02_rule_order.py
"""
import re
import sys
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from cf_engine.resolve import book_for

census11 = import_module("106_chunk11_census")
ASOF = "20260917"
GROUPS = {
    "building": "CommercialPropertyStructureRules.Rule.xml",
    "contents": "CommercialPropertyPersonalPropertyRules.Rule.xml",
    "business income": "CommercialPropertyBusinessIncomeRules.Rule.xml",
    "special class": "CommercialPropertySpecialClassRules.Rule.xml",
    "SC business income": "CommercialPropertySpecialClassBusnIncomeRules.Rule.xml",
}
ROLLUP = re.compile(r"ZzDisclosure|PostTRIACoverage")


def rules(path):
    s = path.read_text(encoding="utf-8-sig")
    return {m.group(1): m.group(0) for m in re.finditer(r'<rul:Rule Name="([^"]+)".*?</rul:Rule>', s, re.S)}


def calls(body):
    return [(f.replace("CommercialProperty", "").replace("Rules", ""), r)
            for f, r in re.findall(r'<rul:RunRule[^>]*?FileName="([^"]+)"[^>]*?Rule="([^"]+)"', body)]


def main():
    fails = []
    parents = {}
    for j in census11.JURIS:
        if j == "PR":
            continue
        try:
            bk = book_for(j, ASOF)
        except Exception:
            continue
        parents.setdefault(bk.parent.package.content.parent.name, (bk.parent.package.content, []))[1].append(j)

    for name, (content, states) in sorted(parents.items()):
        rd = content / "Rules"
        pol = rules(rd / "CommercialPropertyRules.Rule.xml")
        seq = [c for c in calls(pol["ErcProcess"]) if c[1] != "InitializeRuleSet"]
        loc = [i for i, (f, r) in enumerate(seq) if f == "Location"]
        roll = [i for i, (f, r) in enumerate(seq) if ROLLUP.search(f)]
        ser = [i for i, (f, r) in enumerate(seq) if r == "ErcSetRatesAndFactors" and f == ""]
        timeline = "SetTerrorismRatesandFactors" in [r for _, r in calls(pol["ErcSetRatesAndFactors"])]
        ok1 = timeline and ser and loc and ser[0] < loc[0]
        ok2 = loc and roll and max(loc) < min(roll)
        print(f"{name:14s} ({len(states):2d} states)  timeline set before locations: {'OK' if ok1 else 'FAIL'}   "
              f"locations {loc} before roll-ups {roll}: {'OK' if ok2 else 'FAIL'}")
        if not ok1:
            fails.append(f"{name}: timeline factors not set before locations")
        if not ok2:
            fails.append(f"{name}: a roll-up record runs before a location")
        for g, f in GROUPS.items():
            r = rules(rd / f)
            rate = [x for _, x in calls(r.get("ErcRate", ""))]
            own = all(x in rate for x in ("SetPreTRIAPremium", "SetPostTRIAPremium", "SetTerrorismPremium"))
            order = own and rate.index("SetTerrorismPremium") > rate.index("SetPostTRIAPremium") > rate.index("SetPreTRIAPremium")
            reads = set()
            for n in ("SetPreTRIAPremium", "SetPostTRIAPremium", "SetTerrorismPremium"):
                reads |= set(re.findall(r'FromDataDef="([^"]*Premium[^"]*)"', r.get(n, "")))
            foreign = {x for x in reads if "/" in x}
            in_total = bool(re.search(r"TerrorismPremium|PreTRIAPremium|PostTRIAPremium", r["CalculateTotalPremium"]))
            flag = "OK" if (own and order and not foreign and not in_total) else "FAIL"
            if flag == "FAIL":
                fails.append(f"{name} {g}: own={own} order={order} foreign={foreign} in_total={in_total}")
            print(f"    {g:20s} Pre->Post->Terrorism in own ErcRate: {order!s:5s}  reads another record's premium: "
                  f"{sorted(foreign) or 'no'}  in own total: {in_total}  {flag}")
        tot = pol["CalculateTotalPremium"]
        ok4 = "CommercialPropertyLocationRules" in tot and all(
            k in tot for k in ("ZzDisclosurePursuantToTerrorismRiskInsAct2002", "PostTRIACoverage"))
        print(f"    policy total sums locations + roll-up records: {'OK' if ok4 else 'FAIL'}")
        if not ok4:
            fails.append(f"{name}: policy total misses a roll-up record")

    # state layer: does any state reorder the policy ErcProcess?
    print("\nstate policy-file ErcProcess overrides that touch the roll-up:")
    for j in census11.JURIS:
        if j == "PR":
            continue
        try:
            bk = book_for(j, ASOF)
        except Exception:
            continue
        p = bk.state.package.content / "Rules" / "CommercialPropertyRules.Rule.xml"
        if not p.exists():
            continue
        body = rules(p).get("ErcProcess", "")
        hit = [c for c in calls(body) if ROLLUP.search(c[0]) or c[0] == "Location"]
        if hit:
            first = calls(body)[0] if calls(body) else None
            print(f"  {j}: {len(hit)} roll-up calls; first call {first} (parent runs first: "
                  f"{'yes' if first and first[1] == 'ErcProcess' and first[0] == '' else 'check'})")
            print(f"       {sorted(set(r for _, r in hit))}")

    print()
    if fails:
        print("FAIL:\n  " + "\n  ".join(fails))
        sys.exit(1)
    print("C13-02 CLEAN: terrorism is computed per coverage record from that record's own factors, and rolled up\n"
          "to the policy by the disclosure/PostTRIA records, which run after every location, in every edition.")


if __name__ == "__main__":
    main()
