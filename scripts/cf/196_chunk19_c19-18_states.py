#!/usr/bin/env python3
"""Chunk 19, RC-4 (C19-18): the state formula rewrites, FL's switches and own glass files, MT's glass files.

One portable policy per state (192_'s: 175_'s policy made portable the 189_ way, Special, the contents' own
earthquake election) carrying EVERY chunk 19 family, placed from THAT state's DataDef XSD, with the state-only
premium files of the family patterns added (FL's five BuildingGlassTenantsPolicyDetail forms; MT files the
same names with NO premium rule). Every record is predicted from THAT state's own SetPremium (its file if it
rewrites it, else its countrywide edition's: 177_'s rule_text), evaluated by hand on the tree; a record the
state switches off with a bare 0 (FL: all 20 countrywide tenants' records and all 5 Temporarily Away), empties
ErcRate for, or has no premium rule for (MT glass) must price nothing. Independent state values checked on the
tree: the trees' vehicle factor (1.15 in RI VT; VehExcl "No") and the Group II symbol numbers NY files
HEADER-ONLY (the engine falls back to the CW value since 2026-09-28; ISO arbitrates -- C19-17 found ISO does not
always fall back).

  states: AL AR DC FL GA KS NY RI TX VT (the formula rewrites) and MT (the glass files); OR as the control
  probes P-pip-AL / KS / RI: the Public Institutional Plan applied (building, occupancy, contents, special class)
  FL drops the earthquake election (its own EQ class scheme is untested here, as in chunks 16-18)

    python scripts/cf/196_chunk19_c19-18_states.py [--live] [--states NY,FL] [--all]

  --all is C19-20: every chunk 19 family on each of the 46 in-force states' own package, predicted per state.

Progress streams as [i/n elapsed] lines. Exits 1 on any disagreement.
"""
from __future__ import annotations

import argparse
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
sys.path.insert(0, str(ROOT / "scripts"))

sys.stdout.reconfigure(line_buffering=True)
T0 = time.monotonic()

from cf_engine.resolve import book_for                                   # noqa: E402
from gl_engine.interp.values import InterpretError                       # noqa: E402

g = import_module("192_chunk19_rc2")
rc1m = import_module("191_chunk19_rc1")
r4 = import_module("177_chunk16_rc4")
x17 = import_module("183_chunk17_rc4")
r2, rc1, gc, rep, cmp, r11, r16 = g.r2, g.rc1, g.gc, g.rep, g.cmp, g.r11, g.r16
P, same = g.P, g.same
r11.NUMERIC |= {"EachTreeLimit"}
FAIL = []
STATES = ["OR", "AL", "AR", "DC", "FL", "GA", "KS", "NY", "RI", "TX", "VT", "MT"]
PROBES = {f"P-pip-{j}": j for j in ("AL", "KS", "RI")}
EQ_KEYS = ("EQCovIndicator", "EQClass", "EQCoinsurance", "EQDeductible", "EQSprinklerLeakageOnly", "EQGrade")


def progress(i, n, what):
    m, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{i}/{n}  {m}m{s:02d}s] {what}")


@functools.lru_cache(maxsize=None)
def xsd(j):
    return rc1.xsd_for(book_for(j, r2.ASOF))


@functools.lru_cache(maxsize=None)
def population(j):
    """the CW premium records of the nine families + the state's own premium-less or premium files of the
    same patterns (FL / MT glass)."""
    recs = {r[len(P):] for rs in rc1m.population().values() for r in rs}
    rd = book_for(j, r2.ASOF).state.package.content / "Rules"
    for f in rd.glob("*.xml"):
        name = f.name[len(P):-len("Rules.Rule.xml")]
        if any(re.search(pat, f.name) for _, pat in rc1m.cen.FAMILIES) and not rc1m.cen.EXCLUDE.search(f.name):
            if re.search(r"(Coverage|Cov)$", name):
                recs.add(name)
    return sorted(recs)


def fields(j, cause="Special"):
    cf = rc1m.container_fields(cause)
    cf["OutdoorTreesShrubsAndPlants"] = dict(cf["OutdoorTreesShrubsAndPlants"], VehExcl="No", EachTreeLimit="1000")
    # FL's glass forms sit directly under the BuildingGlassTenantsPolicy container on the building and price its
    # OWN Limit x the building's final rates (no Detail container: first run priced $0 with the limit misplaced)
    cf["BuildingGlassTenantsPolicy"] = {"Limit": "30000"}
    if j == "FL":
        for k in ("RadioOrTelevisionAntennasDetail", "OutsideSignsDetail"):
            cf[k] = dict(cf[k], EQCovIndicator="No")
    if j not in ("OR", "NY"):
        for k in ("RadioOrTelevisionAntennasDetail", "RadioOrTelevisionAntennasBusinessIncomeOrExtraExpense",
                  "OutsideSignsDetail", "OutdoorTreesShrubsAndPlants"):
            cf[k] = dict(cf[k], BasicGroupIIBaseRate="0.030")       # no Group II territory on the portable policy
    return cf


#: NY prices antennas' and trees' Group II from its OWN tables keyed by the location's Group II territory
#: (I / II / III), not the symbol chain: the NY policy carries territory "I" and submits no base rate
NY_TERR = "I"


def build(j, pip=False):
    def b():
        sub = g.with_cause(g.portable(j), "Special")
        at = rc1.node_dicts(sub)
        if j == "FL":
            # FL does not file the five-coverage policy's special class description: ISO refuses it (C15-16,
            # OI-103); use the one chunks 15-18 use (177_'s FL_SC)
            at[P + "SpecialClass"]["ClassDescription"] = r4.FL_SC
            for k in ("Structure", "SpecialClass", "BusinessIncome", "SpecialClassBusnIncome"):
                for f in EQ_KEYS:
                    at[P + k].pop(f, None)
            # and the location's earthquake settings: with them, the antenna / sign EQ base rate looks up FL's
            # EQLossCostBldg with FL's own class ("5C") and ISO refuses (second FL live run, 2026-09-29; we priced)
            for f in ("EQCauseOfLossForm", "EQTerr", "EQDeductibleTier"):
                at[P + "Location"].pop(f, None)
        else:
            g.contents_eq(sub)
        at[P + "PersonalProperty"]["CovType"] = "Stock"               # Manufacturers' factor row (C19-04)
        if j == "NY":
            at[P + "Location"]["BasicGroupIIRatingTerr"] = NY_TERR
        if pip:
            for k in ("Structure", "OccupClass", "PersonalProperty", "SpecialClass"):
                at[P + k]["PublicInstitutionalPlanApply"] = "Yes"
        cf = fields(j)
        for rec in population(j):
            ch = r16.chain_down(xsd(j), rec)
            if ch is None:
                continue
            top, steps = ch
            d = rc1.node_dicts(sub)[top]
            for t, table in steps:
                if table:
                    lst = d.setdefault(t + "Table", {t: []})[t]
                    if not lst:
                        lst.append({})
                    d = lst[-1]
                else:
                    d = d.setdefault(t, {})
                for k, v in cf.get(r16.short(t), {}).items():
                    d.setdefault(k, v)
        return sub
    return b


def expectations(j):
    exp = {}
    for rec in population(j):
        text, src = r4.rule_text(j, rec)
        exp[rec] = "NONE" if text is None or r4.forced_zero(j, rec) or x17.empty_ercrate(j, rec) else {}
    return exp


def field_checks(data, j):
    """independent state values on the tree."""
    out = []
    gv = lambda n, f: n.first(f).text if n.first(f) is not None else None
    trees = r16.find(data, P + "OutdoorTreesShrubsAndPlants")
    if trees:
        out.append(("trees VehExclFactor", gv(trees[0], "VehExclFactor"),
                    r4.val(j, "VehExclFactorOutdoorTrees", "Factor", Constant="Y")))
    for rec, table in (("RadioOrTelevisionAntennasDetail", "RadioOrTelevisionAntennasBasicGroupIISymbol"),
                       ("OutdoorTreesShrubsAndPlants", "OutdoorTreeBasicGroupIISymbol"),
                       ("OutsideSignsDetail", "OutsideSignsBasicGroupIISymbol")):
        n = r16.find(data, P + rec)
        if not n:
            continue
        # the Group II rate rule THIS state uses: its own file's if it rewrites it, else the countrywide one
        rate_rule = None
        for pk in r4.pkgs(j):
            f = pk / "Rules" / f"{P}{rec}Rules.Rule.xml"
            if f.exists():
                m = re.search(r'<rul:Rule Name="SetBasicGroupIIRate".*?</rul:Rule>', f.read_text(encoding="utf-8-sig", errors="replace"), re.S)
                if m:
                    rate_rule = m.group(0)
                    break
        if rate_rule is not None and "BasicGroupIISymbolNum" not in rate_rule:
            # NY: base rate x LCM, no symbol -- the (header-only) symbol tables are never read (2026-09-29)
            out.append((f"{rec[:20]} symbol not read ({j}'s Group II rate uses none)", None, None))
            if j == "NY" and rec != "OutsideSignsDetail":
                tb = {"RadioOrTelevisionAntennasDetail": "BasicGroupIIRateRadioAntennasNY",
                      "OutdoorTreesShrubsAndPlants": "BasicGroupIIRateOutdoorTreesNY"}[rec]
                out.append((f"{rec[:20]} BasicGroupIIBaseRate ({tb}, terr {NY_TERR})", gv(n[0], "BasicGroupIIBaseRate"),
                            r4.val(j, tb, "Rate", BasicGroupIIRatingTerr=NY_TERR)))
        else:
            # r4.rows: the state's table if it has ROWS, else the countrywide one
            out.append((f"{rec[:20]} BasicGroupIISymbolNum", gv(n[0], "BasicGroupIISymbolNum"),
                        r4.val(j, table, "Factor", Constant="Y")))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--states")
    ap.add_argument("--all", action="store_true", help="C19-20: all 46 in-force states (Puerto Rico excluded)")
    a = ap.parse_args()
    s18 = import_module("164_chunk14_c14-18_all_states")
    runs = [(j, j, False) for j in (a.states.split(",") if a.states else s18.STATES if a.all else STATES)]
    runs += [(pid, j, True) for pid, j in PROBES.items() if not a.states or j in a.states.split(",")]
    results = {}
    for i, (rid, j, pip) in enumerate(runs, 1):
        progress(i, len(runs), f"engine {rid}")
        try:
            data, ip = gc.run(build(j, pip)(), j)
        except (InterpretError, LookupError) as exc:
            print(f"  {rid:9s} RAISED {str(exc)[:150]}")
            FAIL.append(rid)
            continue
        exp = expectations(j)
        bad, detail, n, preds = r4.evaluate(j, data, exp)
        results[rid] = (j, pip, preds)
        fc = field_checks(data, j)
        fbad = [c for c in fc if not same(c[1], c[2])]
        none = sorted({re.sub(r"(BasicGroupI+|Broad|Special|Earthquake|EQ)(Coverage|Cov)$", "*", r) for r, v in exp.items() if v == "NONE"})
        priced = sum(1 for v in preds.values() if v != "NONE" and any(not same(x, 0) for x in v))
        state_rules = sum(1 for r in exp if r4.rule_text(j, r)[1] == "state")
        print(f"  {rid:9s} {r4.pkgs(j)[0].name[-14:]:14s} engine {'as derived' if not bad and not fbad else 'DIFFERS'}: "
              f"{n - len(bad)} of {n} records ({state_rules} on the state's own SetPremium), {priced} priced"
              + (f"; must price nothing: {', '.join(none)[:160]}" if none else ""))
        for name, got, want in fc:
            print(f"      {'ok  ' if same(got, want) else 'FAIL'} {name:52s} tree {got}  independent {want}")
        for d in detail[:6]:
            print(d)
        if bad or fbad:
            FAIL.append(rid)

    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
        agree = 0
        print("\nISO live at 2026-09-17 (every predicted record, every premium field for field, messages):")
        for i, (rid, (j, pip, preds)) in enumerate(results.items(), 1):
            progress(i, len(results), f"ISO {rid}")
            req = r11.payload(build(j, pip)())
            if j != "OR":
                for cp in req["body"]["CommercialProperty"]:
                    cp["State"] = j
                req["body"]["SchemeKeys"]["ProductName"] = r11.PRODUCT.format(state=j)
            (gc.OUT / f"chunk19_c19-18_{rid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
            try:
                resp = client.rate(req)
            except raas_mod.RaaSError as exc:
                m = re.search(r"Matrix: (\w+).*?Keys: ([^.]*)", str(exc.body)) or re.search(r'"Message":"([^"]{0,200})', str(exc.body))
                print(f"  {rid:9s} ISO REFUSES {m.group(0)[:200] if m else str(exc.body)[:200]}")
                FAIL.append(f"{rid} live")
                continue
            (gc.OUT / f"chunk19_c19-18_{rid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
            pbad = []
            for rec, want in preds.items():
                iso = r2.iso_of(resp, rec)
                if want == "NONE":
                    if not all(r4.zeroish(x) for x in iso):
                        pbad.append((rec, iso, "nothing"))
                elif sorted(Decimal(str(x)) for x in iso if not same(x, 0)) != sorted(Decimal(str(w)) for w in want if not same(w, 0)):
                    pbad.append((rec, iso, [str(w) for w in want]))
            data, ip = rep.cmp.rate(req)
            ipr, opr = rep.iso_prem(resp), rep.our_prem(data)
            d = [(k, v, opr.get(k)) for k, v in ipr.items() if not rep.cmp.same(v, opr.get(k))]
            mi, mo = cmp.iso_messages(resp), set(ip.messages)
            ok = not pbad and not d and mi == mo
            agree += ok
            print(f"  {rid:9s} {'AGREE' if ok else 'DIFFER'}: predicted {len(preds) - len(pbad)} of {len(preds)}; "
                  f"{len(ipr) - len(d)} of {len(ipr)} premiums; messages {'equal' if mi == mo else 'DIFFER'}"
                  + "".join(f"\n        predicted {r16.short(r)[:58]}: ISO {x}, derived {w}" for r, x, w in pbad[:5])
                  + "".join(f"\n        {k[-90:]} ISO {v} ours {o}" for k, v, o in d[:5])
                  + (f"\n        ISO only {sorted(mi - mo)[:3]}\n        ours only {sorted(mo - mi)[:3]}" if mi != mo else ""))
            if not ok:
                FAIL.append(f"{rid} live")
        print(f"\n  live: {agree} of {len(results)} agree")
    m, s = divmod(int(time.monotonic() - T0), 60)
    print(f"\nC19-18: {'ALL AGREE' if not FAIL else 'FAILED: ' + ', '.join(FAIL)}  ({m}m{s:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
