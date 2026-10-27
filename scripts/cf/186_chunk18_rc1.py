#!/usr/bin/env python3
"""Chunk 18, RC-1 (C18-02 to C18-05): evidence and plumbing, before any golden case.

C18-02  THE $0 FIXTURES. Agreed Value and Inflation Guard records sit on every stored
        example policy (364 buildings, 206 contents rows, 82 BI, 28 special classes) and
        ISO never priced one. Every stored ISO response carrying them is re-rated: ISO's
        premium, ours, and the parent inputs that decide it. Then each on-switch is
        flipped one at a time on chunk 7's Oregon policy. No ISO calls.
C18-03  ATTACH MAP AND SWITCHES. Each premium record's chain up to its coverage record
        (DataDef XSD), each container's own rules, every on-switch shape, and every rule
        that defaults a rate / factor to 0 when an input is blank.
C18-04  BORROWED VALUES. The family records placed on the Oregon policy with their inputs
        (three trees: causes Basic, Broad, Special), the engine run, every SetPremium operand
        resolved from the record node in its loop context, and SetPremium evaluated by hand
        (174_'s evaluator) from the landed values: hand must equal engine. Records that price
        $0 are listed with the reason (RC-2 / RC-3's inputs).
C18-05  TABLES AND LITERALS. Every table the family files read, CW rows, every state-filed
        table under ANY name that belongs to the family, and the literals the tests compare.

    python scripts/cf/186_chunk18_rc1.py

Progress streams as [i/n elapsed] lines. Exits 1 on any check that fails.
"""
from __future__ import annotations

import collections
import copy
import functools
import json
import re
import sys
import time
from decimal import Decimal
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))

sys.stdout.reconfigure(line_buffering=True)
T0 = time.monotonic()

from cf_engine.resolve import book_for                                   # noqa: E402
from gl_engine.interp.values import InterpretError                       # noqa: E402

book_for = functools.lru_cache(maxsize=None)(book_for)                  # see 180_ / 183_ (2026-09-28)

gc = import_module("149_chunk13_golden_case")
grp = import_module("150_chunk13_c13-08-09_groups_rollup")
rep = import_module("157_chunk14_c14-02_total_replay")
s18 = import_module("164_chunk14_c14-18_all_states")
rc1 = import_module("168_chunk15_rc1")
r16 = import_module("174_chunk16_rc1")
cen = import_module("185_chunk18_census")
ASOF = "20260917"
P = "CommercialProperty"
RES = ROOT / "results" / "cf-raas"
FAIL = []
short = r16.short
PARENTS = ("Structure", "PersonalProperty", "BusinessIncome", "SpecialClass", "SpecialClassBusnIncome")


def progress(what):
    m, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{m}m{s:02d}s] {what}")


def check(ok, msg):
    print(f"    [{'ok' if ok else 'FAIL'}] {msg}")
    if not ok:
        FAIL.append(msg)


def population():
    """family -> {premium record stem: CW rule text}."""
    cw = book_for("OR", ASOF).parent.package.content
    out = {}
    for fam, pat in cen.FAMILIES:
        out[fam] = {}
        for f in sorted((cw / "Rules").glob("*.xml")):
            if re.search(pat, f.name) and not cen.EXCLUDE.search(f.name):
                t = f.read_text(encoding="utf-8-sig")
                if cen.set_premium(t):
                    out[fam][f.name[:-len("Rules.Rule.xml")]] = t
    return out


def prem_of(data, tag):
    return [n.first("Premium").text if n.first("Premium") is not None else None for n in r16.find(data, tag)]


def money(v):
    return Decimal(v) if v not in (None, "") else Decimal(0)


# ------------------------------------------------------------------ the trees

EFF, EXP = "09/17/2026", "09/17/2027"          # a 365-day term
#: the parent coverages' own inputs for the six families
PARENT_FIELDS = {"AgreedValueOption": "Yes", "AgreedValueLimit": "80000", "InflationGuard": "4%",
                 # Structure / PersonalProperty ATTACH Functional Valuation only for this valuation type and
                 # DELETE it otherwise (AttachForm...FunctionalBuildingValuation; found by the first run)
                 "ValuationType": "Functional Valuation"}
#: container record -> its own inputs (from the rules that read them, C18-01)
CONTAINER_FIELDS = {
    "FunctionalBuildingValuation": {"PostLossOrdinanceOrLawOption": "Yes"},
    "IncreaseInRebuildingExpensesFollowingDisaster": {"AdditionalExpenseCoveragePercentage": "10%"},
    "IncreaseInRebuildingExpensesFollowingDisasterSpecialClass": {"AdditionalExpenseCoveragePercentage": "10%"},
    "VacancyPermit": {"PermitPeriodFrom": "11/01/2026", "PermitPeriodTo": "01/30/2027", "Vandalism": "Yes",
                      "SprinklerLeakage": "Yes"},
    "VacancyPermitPrsnlProp": {"PermitPeriodFrom": "11/01/2026", "PermitPeriodTo": "01/30/2027", "Vandalism": "Yes",
                               "SprinklerLeakage": "Yes"},
    "PeakSeasonLimitOfInsuranceDetail": {"Limit": "30000", "FullValue": "30000", "PeriodFrom": "11/01/2026",
                                         "PeriodTo": "12/31/2026"},
}


def base(cause, parent_fields=None, dated=True):
    sub = grp.five()
    at = rc1.node_dicts(sub)
    if dated:
        sub["EffDate"], sub["ExpDate"] = EFF, EXP
        at[P].update({"EffectiveDt": EFF, "ExpirationDt": EXP})
    for k in PARENTS:
        at[P + k]["CauseOfLoss"] = cause
        at[P + k].update(parent_fields if parent_fields is not None else PARENT_FIELDS)
    return sub


def place(sub, xsd, rec, fields):
    """rec under its known coverage record, creating (or reusing) each container on the way."""
    ch = r16.chain_down(xsd, rec)
    if ch is None:
        return None
    top, steps = ch
    d = rc1.node_dicts(sub).get(top)
    if d is None:
        return None
    for t, table in steps:
        if table:
            lst = d.setdefault(t + "Table", {t: []})[t]
            if not lst:
                lst.append({})
            d = lst[-1]
        else:
            d = d.setdefault(t, {})
        for k, v in fields.get(short(t), {}).items():
            d.setdefault(k, v)
    return short(top) + " > " + " > ".join(short(t) + ("[]" if tb else "") for t, tb in steps)


def tree(cause, pop, xsd, only=None, fields=None, parent_fields=None, dated=True):
    sub = base(cause, parent_fields, dated)
    where = {}
    for fam, rs in pop.items():
        for r in rs:
            if only and r not in only:
                continue
            where[r] = place(sub, xsd, short(P + r), fields if fields is not None else CONTAINER_FIELDS)
    return sub, where


# ------------------------------------------------------------------ C18-02

AV_IG = ("AgreedVal", "InflationGuard")


def zero_fixtures(pop, xsd, skip_stored=False):
    progress("C18-02  THE $0 FIXTURES")
    print("=" * 90 + "\nC18-02  THE $0 FIXTURES (no ISO calls)\n" + "-" * 90)
    recs = [r for fam in ("Agreed Value", "Inflation Guard") for r in pop[fam]]
    index = rep.fixture_index()
    stored = [] if skip_stored else sorted(RES.glob("chunk13_fixture_*_response.json"))
    reasons = collections.Counter()
    n = ok_n = 0
    for i, rp in enumerate(stored, 1):
        stem = rp.name[len("chunk13_fixture_"):-len("_response.json")]
        if i % 50 == 0:
            progress(f"  stored fixture {i}/{len(stored)}")
        fx = index.get(stem)
        if fx is None:
            continue
        d = json.loads(fx.read_text(encoding="utf-8-sig"))
        req = {"header": {}, "body": {"SchemeKeys": {"ProductName": d["SchemeKeys"]["ProductName"],
                                                     "EffectiveDateTime": "2026-09-17T00:00:00"},
                                      "CommercialProperty": d["CommercialProperty"]}}
        resp = json.loads(rp.read_text(encoding="utf-8"))
        iso = collections.defaultdict(list)

        def walk(o, k=None):
            if isinstance(o, dict):
                if k in recs:
                    iso[k].append(o.get("Premium"))
                for kk, v in o.items():
                    if isinstance(v, (dict, list)):
                        walk(v, kk)
            elif isinstance(o, list):
                for x in o:
                    walk(x, k)
        walk(resp["Body"])
        if not iso:
            continue
        try:
            data, _ = rep.cmp.rate(req)
        except InterpretError as exc:
            check(False, f"{stem}: ours raised {str(exc)[:100]}")
            continue
        n += 1
        ok = True
        for r in iso:
            ok &= all(money(x) == 0 for x in iso[r]) and all(money(x) == 0 for x in prem_of(data, r))
            for node in r16.find(data, r):
                par = node.parent
                g = lambda f: (par.first(f).text if par.first(f) is not None else None)
                if "AgreedVal" in r:
                    why = f"AgreedValueOption={g('AgreedValueOption')}, BlktAgreedVal={g('BlktAgreedVal')}, IncludedInBlkt={g('IncludedInBlkt')}"
                else:
                    why = f"InflationGuard={g('InflationGuard')}, BlktInflationGuard={g('BlktInflationGuard')}"
                reasons[(re.sub(r"(BasicGroupI+|Broad|Special|Earthquake)?Coverage$", "", short(r)), why)] += 1
        ok_n += ok
    if skip_stored:
        print("  (stored responses skipped: --skip-stored)")
    else:
        check(ok_n == n and n > 0, f"{n} stored responses carry Agreed Value / Inflation Guard records: ISO $0 and ours $0 on {ok_n}")
    print("  why they price $0 (the parent's inputs, read from our rated tree; records per reason):")
    for (r, why), k in sorted(reasons.items(), key=lambda x: -x[1])[:14]:
        print(f"    {k:5d} x {r[:40]:40s} {why}")

    print("\n  Flip each switch on the Oregon policy (Structure, Basic cause):")
    av, ig = P + "StructureAgreedValBasicGroupICoverage", P + "StructureInflationGuardBasicGroupICoverage"
    only = {av, ig}
    for label, pf, want_av, want_ig in [
            ("AgreedValueOption Yes, InflationGuard 4%", {"AgreedValueOption": "Yes", "AgreedValueLimit": "80000", "InflationGuard": "4%"}, True, True),
            ("AgreedValueOption No, InflationGuard Not Applicable", {"AgreedValueOption": "No", "AgreedValueLimit": "80000", "InflationGuard": "Not Applicable"}, False, False),
            ("both blank", {}, False, False),
            ("AV Yes, no AgreedValueLimit", {"AgreedValueOption": "Yes", "InflationGuard": "28%"}, False, True),
            ("IG 'Blanket Inflation Guard Value Applies', not blanketed", {"AgreedValueOption": "Yes", "AgreedValueLimit": "80000", "InflationGuard": "Blanket Inflation Guard Value Applies"}, True, False)]:
        sub, _ = tree("Basic", pop, xsd, only=only, parent_fields=pf)
        try:
            data, _ = gc.run(sub, "OR")
        except InterpretError as exc:
            check(False, f"{label}: raised {str(exc)[:100]}")
            continue
        a, b = prem_of(data, av), prem_of(data, ig)
        ga, gb = bool(a) and money(a[0]) > 0, bool(b) and money(b[0]) > 0
        check(ga == want_av and gb == want_ig, f"{label:58s} Agreed Value {a}, Inflation Guard {b}")


# ------------------------------------------------------------------ C18-03

def attach_and_switches(pop, xsd):
    progress("C18-03  ATTACH MAP AND SWITCHES")
    print("\n" + "=" * 90 + "\nC18-03  ATTACH MAP AND SWITCHES\n" + "-" * 90)
    shapes = collections.defaultdict(list)
    for fam, rs in pop.items():
        print(f"  {fam}")
        for r, text in sorted(rs.items()):
            ch = r16.chain_down(xsd, short(P + r))
            where = "NOT IN XSD" if ch is None else short(ch[0]) + " > " + " > ".join(
                short(t) + ("[]" if tb else "") for t, tb in ch[1])
            print(f"    {short(r):70s} {where}")
            m = re.search(r'<rul:Rule Name="SetCoverageOnPolicyIndicator".*?</rul:Rule>', text, re.S)
            gate = "always on"
            if m and "<rul:If>" in m.group(0):
                tests = [a or ("exists " + b.rsplit("/", 1)[-1]) for a, b in
                         re.findall(r'FromDataDef="([^"]+)"|AtInputDataDef="([^"]+)"', m.group(0))]
                consts = [c for c in re.findall(r'<rul:Constant[^>]*>([^<]*)<', m.group(0)) if c not in ("0", "1")]
                gate = ", ".join(t.rsplit("/", 1)[-1] for t in tests) + f" = {consts}"
            body = cen.set_premium(text)
            if re.search(r"<rul:(If|Choose)>", body):
                cond = sorted(set(c.rsplit("/", 1)[-1] for c in re.findall(r'FromDataDef="([^"]+)"',
                              "".join(re.findall(r"<rul:Test>(.*?)</rul:Test>", body, re.S)))))
                gate += f"; SetPremium branches on {', '.join(cond)}"
            shapes[(fam, gate)].append(short(r))
    print("\n  on-switch shapes (SetCoverageOnPolicyIndicator; ErcProcess writes $0 when it is 0):")
    for (fam, g), rs in sorted(shapes.items()):
        print(f"    {fam[:22]:22s} {len(rs):2d} files: {g[:190]}")
    cw = book_for("OR", ASOF).parent.package.content / "Rules"
    zero = set()
    print("\n  containers (no SetPremium) and their Set rules:")
    for fam, pat in cen.FAMILIES:
        for f in sorted(cw.glob("*.xml")):
            if not re.search(pat, f.name) or cen.EXCLUDE.search(f.name):
                continue
            t = f.read_text(encoding="utf-8-sig")
            for m in re.finditer(r'<rul:Constant Type="decimal" ToDataDef="(\w+)">0(?:\.0)?</rul:Constant>', t):
                if m.group(1) != "Premium":
                    zero.add((short(f.name), m.group(1)))
            if not cen.set_premium(t):
                sets = [x for x in cen.rule_names(t) if x.startswith("Set")]
                print(f"    {short(f.name)[:60]:60s} {len(sets)} Set rules: {', '.join(sets[:7])}{' ...' if len(sets) > 7 else ''}")
    print("  rates / factors that default to 0 when an input is blank (a $0 with no switch):")
    for f, what in sorted(zero):
        print(f"    {f[:60]:60s} {what}")


# ------------------------------------------------------------------ C18-04

def borrowed(pop, xsd):
    progress("C18-04  BORROWED VALUES")
    print("\n" + "=" * 90 + "\nC18-04  BORROWED VALUES (hand = engine on the Oregon policy)\n" + "-" * 90)
    priced, zero = set(), collections.defaultdict(list)
    unplaced, notsetup, absent_src = set(), {}, collections.defaultdict(set)
    for cause in ("Basic", "Broad", "Special"):
        progress(f"  tree: cause {cause}")
        sub, where = tree(cause, pop, xsd)
        unplaced |= {short(r) for r, w in where.items() if w is None}
        try:
            data, _ = gc.run(sub, "OR")
        except InterpretError as exc:
            check(False, f"cause {cause}: tree raised {str(exc)[:160]}")
            continue
        print(f"  cause {cause}:")
        for fam, rs in pop.items():
            for r in sorted(rs):
                if where.get(r) is None:
                    continue
                nodes_ = r16.find(data, r)
                if not nodes_:
                    zero[short(r)].append(f"{cause}: removed from the tree")
                    continue
                body = cen.set_premium(rs[r])
                ops = r16.operands(body, nodes_[0])
                # a Table wrapper is always a defect; a path to an ABSENT record is not, when it is one of
                # several alternative sources (Inflation Guard reads whichever finished premium exists) --
                # it is reported, and hand = engine decides
                wrapper = [f"{op} -> {w}" for op, w in ops if "WRAPPER" in w]
                absent = sorted({op.split("/")[1].replace(P, "")[:48] for op, w in ops if w == "NOWHERE"})
                prem = nodes_[0].first("Premium")
                eng = money(prem.text if prem is not None else None)
                cov = nodes_[0].first("CoverageOnPolicyIndicator")
                if cov is not None and cov.text == "0":
                    zero[short(r)].append(f"{cause}: switched off")
                    continue
                h = r16.hand(body, nodes_[0])
                try:
                    hv = Decimal(str(h))
                except ArithmeticError:
                    hv = None
                if hv is None and eng == 0:
                    # the hand evaluator met a blank input the engine read as 0: the parent is not set up here
                    notsetup[short(r)] = str(h)[:60]
                    continue
                ok = not wrapper and hv is not None and hv == eng
                if absent:
                    absent_src[short(r)] |= set(absent)
                if eng == 0:
                    zero[short(r)].append(f"{cause}: $0 with the switch on")
                    if not ok:
                        check(False, f"{short(r)} ({cause}): hand {h}, engine {eng}" + (f"; {wrapper}" if wrapper else ""))
                    continue
                priced.add(short(r))
                check(ok, f"{short(r)[:72]:72s} ${eng}  (hand {hv}; {len(ops)} operands)" + (f"; {wrapper}" if wrapper else ""))
    total = sum(len(v) for v in pop.values())
    print(f"\n  records priced (> $0, hand = engine) on at least one tree: {len(priced)} of {total}")
    if unplaced:
        print(f"  not placed (no attach point on the five-coverage policy -- RC-2 builds their parent): {sorted(unplaced)}")
    if absent_src:
        print("  alternative sources absent on this policy (hand = engine regardless):")
        for r, a in sorted(absent_src.items()):
            print(f"    {r[:60]:60s} {', '.join(sorted(a))[:130]}")
    if notsetup:
        print("  parent not set up on this policy (hand met a blank the engine read as 0; RC-2 builds it):")
        for r, why in sorted(notsetup.items()):
            print(f"    {r[:60]:60s} {why}")
    print("  records not priced on these trees, and why (their inputs are RC-2's):")
    for r, why in sorted(zero.items()):
        if r not in priced:
            print(f"    {r[:66]:66s} {'; '.join(sorted(set(why)))[:120]}")
    # the dated families: what the engine made of the periods
    sub, _ = tree("Basic", pop, xsd)
    data, _ = gc.run(sub, "OR")
    for tag in ("VacancyPermit", "VacancyPermitPrsnlProp"):
        for n in r16.find(data, P + tag):
            f = n.first("VacancyPermitProRateFactor")
            print(f"  {tag}: VacancyPermitProRateFactor {f.text if f is not None else None} "
                  f"(permit 11/01/2026-01/30/2027 = 90 days of a 365-day term -> 0.247 by hand)")


# ------------------------------------------------------------------ C18-05

WORDS = {"Agreed Value": ["AgreedVal"], "Inflation Guard": ["InflationGuard"],
         "Functional Valuation": ["FunctionalValuation", "PostLossOrdinance"],
         "Increase in Rebuilding Expenses after Disaster": ["RebuildingExpenses", "AdditionalExpenseCoverage"],
         "Vacancy Permit": ["Vacancy", "Vandalism", "SprinklerLeakageExcl", "Subline"],
         "Peak Season": ["PeakSeason", "LOIFactor", "CoinsuranceFactorBlkt"]}


def tables_and_literals(pop):
    progress("C18-05  TABLES AND LITERALS")
    print("\n" + "=" * 90 + "\nC18-05  TABLES AND LITERALS\n" + "-" * 90)
    cw = book_for("OR", ASOF).parent.package.content
    for fam, pat in cen.FAMILIES:
        texts = [f.read_text(encoding="utf-8-sig") for f in (cw / "Rules").glob("*.xml")
                 if re.search(pat, f.name) and not cen.EXCLUDE.search(f.name)]
        stexts = []
        for j in s18.STATES:
            rd = book_for(j, ASOF).state.package.content / "Rules"
            if rd.exists():
                stexts += [f.read_text(encoding="utf-8-sig", errors="replace") for f in rd.glob("*.xml")
                           if re.search(pat, f.name) and not cen.EXCLUDE.search(f.name)]
        tabs = sorted(set(t for s in texts + stexts for t in re.findall(r'MatrixFromConstant="([^"]+)"', s)) - {"Pages"})
        print(f"  {fam}")
        for t in tabs:
            f = cw / "Rate Tables" / f"{t}.RateTable.csv"
            print(f"    reads {t:58s} CW rows {cen.rows(f) if f.exists() else 'NOT FILED'}")
        filed = collections.defaultdict(list)
        for j in s18.STATES:
            td = book_for(j, ASOF).state.package.content / "Rate Tables"
            if td.exists():
                for f in td.glob("*.RateTable.csv"):
                    if any(w in f.name for w in WORDS[fam]):
                        filed[f.name[:-len(".RateTable.csv")]].append(f"{j}:{cen.rows(f)}")
        for t, js in sorted(filed.items()):
            flag = "" if t in tabs else "   <-- not read by any family file"
            print(f"    state-filed {t:52s} {' '.join(js)[:80]}{flag}")
        lits = collections.Counter()
        for s in texts:
            for m in re.finditer(r'<rul:(Equal|NotEqual)>(.*?)</rul:\1>', s, re.S):
                for c in re.findall(r'<rul:Constant[^>]*>([^<]*)<', m.group(2)):
                    lits[c] += 1
        print(f"    literals compared in tests: {', '.join(repr(k) for k, _ in lits.most_common(18))}")


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-stored", action="store_true",
                    help="skip C18-02's re-rating of the 293 stored responses (~16 min); the switch flips still run")
    a = ap.parse_args()
    pop = population()
    xsd = rc1.xsd_for(book_for("OR", ASOF))
    print(f"{book_for('OR', ASOF)}\n" + "\n".join(f"  {fam}: {len(rs)} premium records" for fam, rs in pop.items()))
    zero_fixtures(pop, xsd, skip_stored=a.skip_stored)
    attach_and_switches(pop, xsd)
    borrowed(pop, xsd)
    tables_and_literals(pop)
    m, s = divmod(int(time.monotonic() - T0), 60)
    print("\n" + ("RC-1: ALL CHECKS PASS" if not FAIL else f"RC-1: {len(FAIL)} FAILED") + f"  ({m}m{s:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
