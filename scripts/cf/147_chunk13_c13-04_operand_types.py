"""C13-04: engine readiness for terrorism by operand TYPE, not element name.

Part 1, static. Every operator in the terrorism population -- the 17 named
files and the terrorism rules embedded in the policy, location and five
coverage files -- in all 5 parent editions and every state's own layer (46,
PR excluded), classed by the declared type of each operand with chunk 12's
classifier (`125_chunk12_c12-03_operand_types.classify`).

Part 2, the date functions. `DatePart`, `DateCreate` and `DateDifference` are
new to the chunks' golden cases here. Each occurrence is listed with its
operands and the one way it can refuse: `DatePart` of a `01/01/0001` fallback,
which our `coerce` reads as null.

Part 3, live. One ISO STC fixture per `TRIAType` value (all four), converted
to an engine submission and rated at 2026-09-17: no refusal, and the
timeline fields (`DaysUntilTRIAExpiration`, both proration factors) equal the
values derived by hand from the rules.

    python scripts/cf/147_chunk13_c13-04_operand_types.py

Exits 1 on any WRONG / REFUSES signature reachable in terrorism, or any live
refusal or timeline mismatch.
"""
import collections
import json
import re
import sys
import xml.etree.ElementTree as ET
from datetime import date
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))

from cf_engine.config import NULL_ARITHMETIC, ROUNDING
from cf_engine.resolve import book_for
from gl_engine.interp.interpreter import Interpreter
from gl_engine.interp.tree import Node
from gl_engine.interp.values import TYPES, InterpretError

ops = import_module("125_chunk12_c12-03_operand_types")
rp = import_module("145_chunk13_c13-03_replay")
census11 = import_module("106_chunk11_census")
NS = ops.NS
ASOF = "20260917"
ISO_CF = Path("C:/Projects/ISO_ERC_Files/CF")
KEY = re.compile(r"Terror|TRIA|Terrsm")
CORE = {"CommercialPropertyRules.Rule.xml", "CommercialPropertyLocationRules.Rule.xml",
        "CommercialPropertyStructureRules.Rule.xml", "CommercialPropertyPersonalPropertyRules.Rule.xml",
        "CommercialPropertyBusinessIncomeRules.Rule.xml", "CommercialPropertySpecialClassRules.Rule.xml",
        "CommercialPropertySpecialClassBusnIncomeRules.Rule.xml"}
DISPATCH = {"InitializeRuleSet", "CalculateTotalPremium", "ErcProcess", "ErcSetRatesAndFactors", "ErcRate",
            "ErcRunPostUnderwritingLogic", "ErcSetStatisticalCodes", "ErcDoConditionalMandatoryLogic",
            "SetLimitsToUse", "SetBlanketRatesAndFactors", "ErcSetPostRatesAndFactors"}
DATE_OPS = {"DatePart", "DateCreate", "DateDifference", "DateAdd"}


def population():
    """(label, rule-name, rule element) for every terrorism rule, every edition and state."""
    seen_parent = set()
    out = []
    for j in census11.JURIS:
        if j == "PR":
            continue
        try:
            bk = book_for(j, ASOF)
        except Exception:
            continue
        layers = []
        pc = bk.parent.package.content
        if pc not in seen_parent:
            seen_parent.add(pc)
            layers.append((pc.parent.name, pc))
        layers.append((j, bk.state.package.content))
        for label, content in layers:
            rd = content / "Rules"
            if not rd.exists():
                continue
            for f in rd.glob("*.xml"):
                named = bool(KEY.search(f.name))
                if not named and f.name not in CORE:
                    continue
                root = ET.fromstring(f.read_text(encoding="utf-8-sig"))
                for r in root.iter(NS + "Rule"):
                    n = r.attrib.get("Name")
                    if named or (n not in DISPATCH and (KEY.search(n) or KEY.search(ET.tostring(r, encoding="unicode")))):
                        out.append((f"{label}/{f.name.replace('CommercialProperty', '').replace('Rules.Rule.xml', '')}", n, r))
    return out


def part1(pop):
    sigs = collections.defaultdict(list)
    bad_types = collections.Counter()
    for label, rule, r in pop:
        for el in r.iter():
            t = ops.tag(el)
            ty = el.attrib.get("Type")
            if ty is not None and ty not in TYPES:
                bad_types[(t, ty)] += 1
            if t not in ops.ORDERED | ops.EQUALITY | ops.ARITH:
                continue
            kids = list(el)
            types = tuple(ops.op_type(k) for k in kids)
            sigs[(t, types, ops.classify(t, types, kids))].append((label, rule))
    total = sum(len(v) for v in sigs.values())
    print(f"PART 1: {len(pop)} terrorism rules, {total} operators, {len(sigs)} signatures")
    fails = []
    for (op, types, verdict), where in sorted(sigs.items(), key=lambda kv: (not kv[0][2].startswith(("WRONG", "REFUSES", "RISK", "CHECK")), -len(kv[1]))):
        if verdict == "ok":
            continue
        print(f"  {len(where):5d}  {op}{types}  -> {verdict}")
        for w in sorted(set(where))[:4]:
            print(f"           e.g. {w[0]} :: {w[1]}")
        if verdict.startswith(("WRONG", "REFUSES")):
            fails.append((op, types, verdict))
    ok = sum(len(v) for k, v in sigs.items() if k[2] == "ok")
    print(f"  plain ok: {ok} operators;  undeclared @Type values: {dict(bad_types) or 'none'}")
    return fails


def part2(pop):
    print("\nPART 2: date functions in terrorism rules")
    shapes = collections.Counter()
    risky = []
    for label, rule, r in pop:
        for el in r.iter():
            t = ops.tag(el)
            if t not in DATE_OPS:
                continue
            kids = list(el)
            desc = []
            for k in kids:
                kt = ops.tag(k)
                src = k.attrib.get("FromDataDef", "")
                fb = k.attrib.get("FromConstant")
                desc.append(f"{kt}[{k.attrib.get('Type', ops.op_type(k))}]{('<-' + src) if src else ''}"
                            f"{(' fb=' + fb) if fb is not None else ''}")
                if t == "DatePart" and fb == "01/01/0001":
                    risky.append((label, rule, src))
            shapes[(t, el.attrib.get("UnitType"), tuple(desc))] += 1
    for (t, unit, desc), n in sorted(shapes.items()):
        print(f"  {n:4d}  {t}(UnitType={unit}) {', '.join(desc)}")
    fields = collections.Counter(src for _, _, src in risky)
    print(f"  DatePart over a 01/01/0001 fallback: {len(risky)} occurrences, fields {dict(fields)}")
    print("    our coerce reads that fallback as null and DatePart refuses on it; reachable only if the field is blank")
    return fields


def expected_timeline(tria_type, eff, tria_exp):
    """By hand, from SetDaysUntilTRIAExpiration / SetTerrorismProrating*Factor (CW 2026)."""
    if tria_type == "Will Expire During the Next 12 Months" and tria_exp:
        days = (tria_exp - eff).days
    elif tria_type == "Is in Effect for the Next 12 Months":
        days = 365
    else:
        days = 0
    if days >= 365:
        yr3 = 1.0
    elif days <= 0:
        yr3 = 0.0
    else:
        yr3 = round(days / 365, 2)
    full = 1.0 if yr3 == 0 else round(1 - yr3, 2)
    return days, yr3, full


def part3():
    print("\nPART 3: live, one ISO fixture per TRIAType, rated at 2026-09-17")
    want_types = ["Is in Effect for the Next 12 Months", "Will Expire During the Next 12 Months",
                  "Has Already Expired, Use Post-TRIA Forms", "Has Expired but Use Conditional Forms"]
    picks = {}
    for p in sorted(ISO_CF.rglob("STC/*.json")):
        t = p.read_text(encoding="utf-8-sig", errors="replace")
        m = re.search(r'"TRIAType"\s*:\s*"([^"]+)"', t)
        if m and m[1] in want_types and m[1] not in picks and '"TerrorismIndicator": "Yes"' in t.replace('":"', '": "'):
            picks[m[1]] = p
    fails = []
    eff = date(2026, 9, 17)
    # The one case that reaches the prorated middle branch (0 < days < 365): the
    # "will expire" fixture with TRIA moved inside the policy year. The fixture's
    # own date (2023) has already passed at 2026 and only reaches the 0 branch.
    cases = [(tt, picks.get(tt), None) for tt in want_types]
    cases.append(("Will Expire During the Next 12 Months", picks.get("Will Expire During the Next 12 Months"),
                  "06/01/2027"))
    for tt, p, override in cases:
        if p is None:
            print(f"  {tt:45s} NO FIXTURE")
            fails.append(tt)
            continue
        d = json.loads(p.read_text(encoding="utf-8-sig"))
        st = d["SchemeKeys"]["ProductName"].split()[-1]
        bk = book_for(st, ASOF)
        sub = {"EffDate": "09/17/2026", "ExpDate": "09/17/2027"}
        sub.update(rp.unwrap(ops.to_engine({"CommercialProperty": d["CommercialProperty"]}), rp.singletons(bk)))
        cp = sub["CommercialPropertyTable"]["CommercialProperty"][0]
        if override:
            cp["TRIAExpirationDate"] = override
        raw_exp = cp.get("TRIAExpirationDate")
        tria_exp = date(int(raw_exp[6:10]), int(raw_exp[0:2]), int(raw_exp[3:5])) if raw_exp else None
        try:
            ip = Interpreter(bk, rounding=ROUNDING, null_arithmetic=NULL_ARITHMETIC)
            data = Node.from_dict(f"MasterCF{st}", sub)
            ip.run(data)
        except InterpretError as exc:
            print(f"  {tt:45s} {p.name} ({st}) REFUSED: {str(exc)[:100]}")
            fails.append(tt)
            continue
        node = data.first("CommercialPropertyTable").first("CommercialProperty")
        got = {c.tag: c.text for c in node.children if c.tag in (
            "DaysUntilTRIAExpiration", "TerrorismProratingProgYr3Factor", "TerrorismProratingFullFactor")}
        days, yr3, full = expected_timeline(tt, eff, tria_exp)
        ok = (rp.num(got.get("DaysUntilTRIAExpiration")) == days
              and rp.num(got.get("TerrorismProratingProgYr3Factor")) == yr3
              and rp.num(got.get("TerrorismProratingFullFactor")) == full)
        print(f"  {tt:45s} {p.name} ({st}) TRIAExp={raw_exp}  days {got.get('DaysUntilTRIAExpiration')} (want {days})  "
              f"yr3 {got.get('TerrorismProratingProgYr3Factor')} (want {yr3})  full {got.get('TerrorismProratingFullFactor')} (want {full})  "
              f"{'OK' if ok else 'MISMATCH'}")
        if not ok:
            fails.append(tt)
    return fails


def main():
    pop = population()
    f1 = part1(pop)
    part2(pop)
    f3 = part3()
    print()
    if f1 or f3:
        print(f"FAIL: {len(f1)} unhandled signatures, {len(f3)} live problems")
        sys.exit(1)
    print("C13-04 CLEAN: no terrorism operator shape the engine mishandles; every TRIAType runs live "
          "and its timeline equals the hand derivation.")


if __name__ == "__main__":
    main()
