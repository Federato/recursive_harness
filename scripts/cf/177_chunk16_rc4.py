#!/usr/bin/env python3
"""Chunk 16, RC-4 (C16-17 to C16-20): the states and the editions.

C16-20  ALL 46 STATES. Each state gets one policy made portable (164_ / 171_'s way) that
        carries every chunk 16 family at once:
          Business Income, Broad cause, 270 days    EPI Group I / II / Broad
                                                    no waiting period "Eliminated"
                                                    Civil Authority 180 days + Radius (manual 1,090)
                                                    Molten Material
          Special Class BI, Special cause, 180 days EPI Group I / II / Special
                                                    no waiting period "Replaced By 24 Hours"
                                                    Civil Authority 90 days + Radius
                                                    Molten Material (Special cause: $0, the rule's Else)
          two buildings (Broad, Special)            Pollutant Clean Up, 60,000 / 2,500, four forms
                                                    Molten Material on building, contents, special class
          contents                                  Spoilage, Florists, both causes, selling price,
                                                    limit 25,050 (FL and RI TRUNCATE limit / 100:
                                                    250.5 -> 250 -- but after the modifiers both land
                                                    on the same dollar; P-FLt / P-RIt / P-GAt at
                                                    99,999 are the discriminating cases)
        Earthquake stays out (proven in Oregon, RC-2; state EQ territories are chunk 10's).
        EVERY record is predicted from THAT state's own rule (its file if it rewrites
        SetPremium, else its countrywide edition's -- MO's is 2023 V02) and THAT state's own
        tables (its file if it files one, else its edition's): the family factor looked up
        independently, the premium by hand. Rules that force $0 (CA / FL switch Civil
        Authority's Radius off) and files an edition lacks (MO: no Special Class Molten
        Material) are predicted as not priced.
C16-17  SPOILAGE'S STATES are in the sweep (the additional factor in AL FL GA NC SC VA, the
        rewritten SetPremium in AL GA KS NC RI SC VA FL, truncation in FL RI), plus
          P-TX  TX in a Designated Catastrophe Area: TX applies its additional factor only there
          P-AL  AL with the Public Institutional Plan (0.85): it moves Molten Material
                ($53 -> $45), NOT Spoilage ($565 unchanged) -- engine and ISO agree
          P-RI  RI with the Public Institutional Plan (and truncation)
C16-18  THE OTHER REWRITES and state tables are in the sweep (FL no-waiting factors, AK EPI,
        CA FL MA Civil Authority, CA FL Radius off, FL Pollutant and Molten SetPremium, MA).
C16-19  EDITIONS: MO on 2023 V02, predicted from its own files.

Corrections from the first engine run (2026-09-25), each a gap in MY prediction, not the engine:
  * Pollutant Clean Up's location rate is the LAST building's (C16-09) UNLESS the special
    class's is higher: SetHighestPollutantBGIRate takes the building's when it is >= the special
    class's, else the special class's. OR: 0.101 >= 0.070 (building); FL: 0.029 < 0.286 and CA:
    buildings 0 (CA's district-split base rates, the portable building has none) -- special class.
  * A form whose own CoverageOnPolicyIndicator is 0 prices $0 (FL wraps every Pollutant form's
    ErcProcess in that switch). The indicator is read from the tree -- the one input here not
    derived independently -- and ISO settles it live.
  * TX applies its Spoilage additional factor ONLY in a Designated Catastrophe Area (else 1.0):
    the sweep expects 1.0 in TX, P-TX the table's 1.1.

    python scripts/cf/177_chunk16_rc4.py [--live] [--all] [--states GA,MO] [--probes-only]
    (default: the covering sample below + the probes; --all: the 46 + the probes)

Exits 1 on any disagreement.
"""
from __future__ import annotations

import argparse
import functools
import csv
import json
import re
import sys
from decimal import Decimal, ROUND_HALF_UP
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))
sys.path.insert(0, str(ROOT / "scripts"))

from cf_engine.resolve import book_for
from gl_engine.interp import tree
from gl_engine.interp.values import InterpretError

r2 = import_module("175_chunk16_rc2")
r16, rc1, gc, rep, cmp, r11, s18 = r2.r16, r2.rc1, r2.gc, r2.rep, r2.cmp, r2.r11, r2.s18
ASOF = r2.ASOF
P = "CommercialProperty"
NW, NW_SC, CA, PC = r2.NW, r2.NW_SC, r2.CA, r2.PC
SPOIL = dict(r2.SPOIL, Limit="25050")
FL_SC = "Cooling Towers - Metal"          # FL files no "Towers - Broadcasting Antennas" (C15-16)
FAIL = []
#: the regression's covering sample (fixed 2026-09-25): every state that rewrites a chunk 16 file or
#: files its own factor table, every countrywide edition in force (MO V02, CA / NC V03, FL / RI / MA
#: V04), and OR. `--all` runs the 46, at chunk close-outs (all 46 ISO-confirmed 2026-09-25).
SAMPLE = ["OR", "AK", "AL", "CA", "FL", "GA", "KS", "MA", "MO", "NC", "NY", "RI", "SC", "TX", "VA"]


def q(x, dp):
    return Decimal(str(x)).quantize(Decimal(1).scaleb(-dp), ROUND_HALF_UP)


# ------------------------------------------------------------ per-state tables

@functools.lru_cache(maxsize=None)
def pkgs(j):
    """cached: book_for re-discovers the whole ERC corpus (~1.8 s) per call, and this was called
    ~120 times per policy -- 2.5 min a policy, 98% discovery (profiled 2026-09-28, chunk 17 RC-4)."""
    b = book_for(j, ASOF)
    return b.state.package.content, b.parent.package.content


def rows(j, name):
    """the state's own table if it files rows, else its countrywide edition's."""
    for pk in pkgs(j):
        f = pk / "Rate Tables" / f"{name}.RateTable.csv"
        if f.exists():
            with open(f, encoding="utf-8-sig") as h:
                rs = list(csv.DictReader(h))
            if rs:
                return rs
    return []


def val(j, name, col, **keys):
    for r in rows(j, name):
        if all(str(r.get(k)) == str(v) for k, v in keys.items() if k in r):
            return Decimal(r[col])
    return None


def rule_text(j, rec):
    """(text, source) of the rule file that prices rec in state j."""
    st, par = pkgs(j)
    sf = st / "Rules" / f"{P}{rec}Rules.Rule.xml"
    if sf.exists():
        t = sf.read_text(encoding="utf-8-sig", errors="replace")
        if r16.cen.set_premium(t):
            return t, "state"
    pf = par / "Rules" / f"{P}{rec}Rules.Rule.xml"
    if pf.exists():
        t = pf.read_text(encoding="utf-8-sig", errors="replace")
        if r16.cen.set_premium(t):
            return t, par.name
    return None, None


def forced_zero(j, rec):
    """the state's file sets CoverageOnPolicyIndicator to a bare 0 (a switch-off)."""
    sf = pkgs(j)[0] / "Rules" / f"{P}{rec}Rules.Rule.xml"
    if not sf.exists():
        return False
    m = re.search(r'<rul:Rule Name="SetCoverageOnPolicyIndicator".*?</rul:Rule>',
                  sf.read_text(encoding="utf-8-sig", errors="replace"), re.S)
    return bool(m) and "<rul:If>" not in m.group(0) and ">0<" in m.group(0)


# ---------------------------------------------------------------- the policy

def build(j, extra=None):
    sub = r2.grp.five()
    at = rc1.node_dicts(sub)
    at[P].update(r2.rc2.POLICY)
    st = at[P + "Structure"]
    st["MultiPremiumAndDispersionCreditFactor"] = r2.rc2.BUILDING_CREDIT
    st.setdefault("WindstormOrHailDeductible", "1,000")
    if j != "OR":
        at[P]["State"] = j
        loc = at[P + "Location"]
        loc.pop("BasicGroupIRatingTerr", None)
        loc.pop("BasicGroupIIRatingTerr", None)
        loc["BasicGroupIRatingTerrFactor"] = "1.0"
        loc.update(s18.STATE_LOC.get(j, {}))
    if j == "FL":
        at[P + "SpecialClass"]["ClassDescription"] = FL_SC
    at[P + "BusinessIncome"].update({"CauseOfLoss": "Broad", "ExtendedPeriod": "270"})
    at[P + "SpecialClassBusnIncome"].update({"CauseOfLoss": "Special", "ExtendedPeriod": "180"})
    # the second building (Special) for Pollutant Clean Up; the first becomes Broad
    import copy
    st["CauseOfLoss"] = "Broad"
    b2 = copy.deepcopy(st)
    b2.update({"ClassCode": "0311", "Limit": "200000", "FullBldgValue": "200000", "CauseOfLoss": "Special"})
    b2.pop("CommercialPropertyBusinessIncomeTable", None)
    b2.pop("CommercialPropertyOccupClassTable", None)
    at[P + "Location"]["CommercialPropertyStructureTable"]["CommercialPropertyStructure"].append(b2)
    put = lambda rec, f=None: r2.put(sub, rec, f or {}, state=j)
    for f in ("BasicGroupI", "BasicGroupII", "Broad"):
        put(f"BusinessIncomeExtendedPeriodOfIndemnityCoverage{f}Coverage")
        put(f"{CA}{f}Coverage")
    for f in ("BasicGroupI", "BasicGroupII", "Special"):
        put(f"SpecialClassBusnIncomeExtendedPeriodOfIndemnityCoverage{f}Coverage")
        put(f"{CA}SpclClassBusnIncome{f}Coverage")
    for f in ("BasicGroupI", "BasicGroupII"):
        put(f"{NW}{f}Coverage")
        put(f"{NW_SC}{f}Coverage")
    put(f"{CA}RadiusCoverage", {"ManualPremium": r2.rc2.MANUAL})
    put(f"{CA}SpclClassBusnIncomeRadiusCoverage", {"ManualPremium": r2.rc2.MANUAL})
    r2.container(sub, "BusinessIncome", NW)["TimePeriod"] = "Eliminated"
    r2.container(sub, "SpecialClassBusnIncome", NW + "SpclClassBusnIncome")["TimePeriod"] = "Replaced By 24 Hours"
    r2.container(sub, "BusinessIncome", CA)["IncreasedCoveragePeriod"] = "180"
    r2.container(sub, "SpecialClassBusnIncome", CA + "SpclClassBusnIncome")["IncreasedCoveragePeriod"] = "90"
    for f in ("BasicGroupI", "BasicGroupII", "Broad", "Special"):
        put(f"{PC}{f}Coverage")
    r2.container(sub, "Location", PC).update({"Limit": "60000", "Deductible": "2,500"})
    xsd = r2._XSD[j]                                  # parsed once by r2.put above
    for rec in ("MoltenMaterial", "MoltenMaterialPrsnlProp", "MoltenMaterialBusnIncome",
                "MoltenMaterialSpecialClass", "MoltenMaterialSpclClassBusnIncome"):
        if xsd.attach(rec)[0]:                      # MO's 2023 V02 has no Special Class Molten records
            put(rec)
    put("SpoilageCoverage", dict(SPOIL))
    if extra:
        extra(sub)
    return sub


# ------------------------------------------------------------- expectations

def expectations(j, probe=None):
    """record -> overrides (the family factor from the state's own table) | "NONE" (not priced)."""
    epi = lambda p: val(j, "ExtendedPeriodFactor", "Factor", ExtendedPeriod=p)
    tf = lambda t: q(val(j, "BusnIncomeChangesTimePeriod", "Factor", TimePeriod=t) - 1, 3)
    cf = lambda p: q(val(j, "CivilAuthorityIncreasedCoveragePeriodEndtFactor", "Factor",
                         CivilAuthorityIncreasedCoveragePeriod=p) - 1, 3)
    prate = lambda f: val(j, "PollutantCleanUpAndRemovalRate", "Rate", CauseOfLossOptionalForm=f)
    pded = val(j, "PollutantCleanUpAndRemovalDeductibleFactor", "Factor", PollutantDeductible="2,500")
    cls = next((r["Value"] for r in rows(j, "SpoilageClassification") if r["SpoilageDesc"] == SPOIL["Description"]), None)
    srate = val(j, "SpoilageCovRate", "Rate", SpoilageClassification=cls, SpoilageCauseOfLoss=SPOIL["SpoilageCauseOfLoss"],
                RefrigerationMaintenanceAgreement=SPOIL["RefrigerationMaintenanceAgreement"])
    spf = val(j, "SpoilageSellingPriceFactor", "Factor", Constant="Y")
    exp = {}
    for f, p in (("BasicGroupI", "270"), ("BasicGroupII", "270"), ("Broad", "270")):
        exp[f"BusinessIncomeExtendedPeriodOfIndemnityCoverage{f}Coverage"] = {"Factor": epi(p)}
    for f in ("BasicGroupI", "BasicGroupII", "Special"):
        exp[f"SpecialClassBusnIncomeExtendedPeriodOfIndemnityCoverage{f}Coverage"] = {"Factor": epi("180")}
    for f in ("BasicGroupI", "BasicGroupII"):
        exp[f"{NW}{f}Coverage"] = {"../Factor": tf("Eliminated")}
        exp[f"{NW_SC}{f}Coverage"] = {"../Factor": tf("Replaced By 24 Hours")}
    for f in ("BasicGroupI", "BasicGroupII", "Broad"):
        exp[f"{CA}{f}Coverage"] = {"../Factor": cf("180")}
    for f in ("BasicGroupI", "BasicGroupII", "Special"):
        exp[f"{CA}SpclClassBusnIncome{f}Coverage"] = {"../Factor": cf("90")}
    exp[f"{CA}RadiusCoverage"] = {}
    exp[f"{CA}SpclClassBusnIncomeRadiusCoverage"] = {}
    exp[f"{PC}BasicGroupICoverage"] = {"BasicGroupIFactor": prate("GroupI"), "DeductibleFactor": pded, "HighestPollutantBGIRate": "LAST_BGI"}
    exp[f"{PC}BasicGroupIICoverage"] = {"BasicGroupIIFactor": prate("GroupII"), "DeductibleFactor": pded}
    exp[f"{PC}BroadCoverage"] = {"BroadRate": prate("Broad"), "DeductibleFactor": pded}
    exp[f"{PC}SpecialCoverage"] = {"SpecialRate": prate("Special"), "DeductibleFactor": pded}
    mf = val(j, "MoltenMaterialFactor", "Factor", Constant="Y")
    for rec in ("MoltenMaterial", "MoltenMaterialPrsnlProp", "MoltenMaterialBusnIncome",
                "MoltenMaterialSpecialClass", "MoltenMaterialSpclClassBusnIncome"):
        exp[rec] = {"Factor": mf}
    sp = {"Class": cls, "Rate": srate, "SellingPriceFactor": spf}
    addl = val(j, "SpoilageAddlFactor", "Factor", SpoilageCauseOfLoss=SPOIL["SpoilageCauseOfLoss"])
    if j == "TX" and probe != "P-TX":
        addl = Decimal("1.0")               # TX applies it only in a Designated Catastrophe Area
    if addl is not None:
        sp["SpoilageAddlFactor"] = addl
    exp["SpoilageCoverage"] = sp
    for rec in list(exp):
        text, src = rule_text(j, rec)
        if text is None or forced_zero(j, rec):
            exp[rec] = "NONE"
    return exp


def predict(data, j, rec, ov):
    """hand evaluation of the state's own SetPremium with the state's own factors substituted."""
    if ov == "NONE":
        return [("NONE", n.first("Premium").text if n.first("Premium") is not None else None)
                for n in rc1.find(data, P + rec)] or [("NONE", None)], []
    text, src = rule_text(j, rec)
    body = r16.cen.set_premium(text)
    paths = set(re.findall(r'FromDataDef="([^"]+)"', body))
    out, checks = [], []
    for node in rc1.find(data, P + rec):
        ind = node.first("CoverageOnPolicyIndicator")
        if ind is not None and ind.text == "0":
            prem = node.first("Premium")
            out.append((Decimal(0), None if prem is None else prem.text))
            continue
        saved = []
        for key, v in ov.items():
            if v is None:
                continue
            if v == "LAST_BGI":
                v = location_bgi(data)
            targets = [key] if key in paths else [x for x in paths if x.rsplit("/", 1)[-1] == key]
            if not targets and "/" not in key:
                targets = [key]             # a field set by the family's own rules, checked though not read
            for path in targets:
                hit = tree.select_one(path, node)
                if hit is not None:
                    checks.append((key, hit.text, v))
                    saved.append((hit, hit.text))
                    hit.text = str(v)
        h = r16.hand(body, node)
        for hit, old in saved:
            hit.text = old
        prem = node.first("Premium")
        out.append((h, None if prem is None else prem.text))
    return out, checks


def location_bgi(data):
    """SetHighestPollutantBGIRate: the last building's (C16-09) if it is >= the special class's, else the
    special class's (read from the tree: chunk 6's special-class rate)."""
    bldg = r2.last_bgi(data)
    c = rc1.find(data, P + PC)[0]
    sp = c.first("HighestSpecialPollutantBGIRate")
    special = Decimal(sp.text) if sp is not None and sp.text else Decimal(0)
    return bldg if bldg >= special else special


def zeroish(v):
    return v in (None, "") or (not isinstance(v, str) or not v.startswith("hand")) and r2.same(v, 0)


def evaluate(j, data, exp):
    bad, detail, n = [], [], 0
    preds = {}
    for rec, ov in exp.items():
        res, checks = predict(data, j, rec, ov)
        fac_bad = [(f, e, v) for f, e, v in checks if not r2.same(e, v) and f not in ("HighestPollutantBGIRate",)]
        if ov == "NONE":
            ok = all(zeroish(e) for _, e in res)
            preds[rec] = "NONE"
        else:
            ok = bool(res) and all(not str(h).startswith("hand") and r2.same(h, e) for h, e in res) and not fac_bad
            preds[rec] = [h for h, _ in res]
        n += 1
        if not ok:
            bad.append(rec)
            detail.append(f"      {r16.short(rec)[:62]:62s} predicted {[str(h) for h, _ in res]} engine {[e for _, e in res]}"
                          + (f" factor {fac_bad[:2]}" if fac_bad else ""))
    return bad, detail, n, preds


PROBES = {
    "P-TX": ("TX", "Designated Catastrophe Area: TX's Spoilage additional factor applies",
             lambda s: [rc1.node_dicts(s)[P].update({"DesignatedCatastropheArea": "Yes"}),
                        rc1.node_dicts(s)[P + "Location"].update({"DesignatedCatastropheArea": "Yes"})]),
    "P-AL": ("AL", "Public Institutional Plan (moves Molten Material, not Spoilage)",
             lambda s: [rc1.node_dicts(s)[P + k].update({"PublicInstitutionalPlanApply": "Yes"})
                        for k in ("Structure", "PersonalProperty", "SpecialClass")]),
    "P-RI": ("RI", "Public Institutional Plan, with RI's truncation",
             lambda s: [rc1.node_dicts(s)[P + k].update({"PublicInstitutionalPlanApply": "Yes"})
                        for k in ("Structure", "PersonalProperty", "SpecialClass")]),
    # At 25,050 the sweep's truncation (250.5 -> 250) and rounding land on the same dollar after the
    # modifiers (RI $513 either way), so it proves nothing. At 99,999 they differ: 999 vs 999.99 ->
    # 2,325 vs 2,327 -> ... -> $2,045 (truncated) vs $2,047 (not), before any state factor.
    "P-FLt": ("FL", "Spoilage limit 99,999: FL truncates limit / 100",
              lambda s: _spoil_limit(s, "99999")),
    "P-RIt": ("RI", "Spoilage limit 99,999: RI truncates limit / 100",
              lambda s: _spoil_limit(s, "99999")),
    "P-GAt": ("GA", "Spoilage limit 99,999: GA does not truncate (the control)",
              lambda s: _spoil_limit(s, "99999")),
}


def _spoil_limit(sub, limit):
    pp = rc1.node_dicts(sub)[P + "PersonalProperty"]
    for rec in pp[P + "SpoilageCoverageTable"][P + "SpoilageCoverage"]:
        rec["Limit"] = limit


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--states")
    ap.add_argument("--probes-only", action="store_true")
    ap.add_argument("--all", action="store_true", help="all 46 states (chunk close-outs); default: the covering sample")
    a = ap.parse_args()
    runs = []
    if not a.probes_only:
        default = s18.STATES if a.all else SAMPLE
        for j in (a.states.split(",") if a.states else default):
            runs.append((j, j, "sweep", None))
    for pid, (j, label, fn) in PROBES.items():
        if not a.states or j in a.states.split(","):
            runs.append((pid, j, label, fn))
    results = {}
    for rid, j, label, fn in runs:
        try:
            sub = build(j, fn)
            data, ip = gc.run(sub, j)
        except (InterpretError, LookupError) as exc:
            print(f"  {rid:5s} RAISED {str(exc)[:150]}")
            FAIL.append(rid)
            continue
        exp = expectations(j, rid)
        bad, detail, n, preds = evaluate(j, data, exp)
        results[rid] = (j, sub, preds)
        notp = sorted(r16.short(r)[:30] for r, v in exp.items() if v == "NONE")
        print(f"  {rid:5s} engine {'as derived' if not bad else 'DIFFERS'}: {n - len(bad)} of {n} records"
              + (f" (not priced here: {', '.join(notp)})" if notp else "") + (f"  [{label}]" if label != "sweep" else ""))
        for d in detail[:6]:
            print(d)
        if bad:
            FAIL.append(rid)
    print(f"\nengine: {len(runs) - len([f for f in FAIL])} of {len(runs)} as derived")

    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
        agree = 0
        print("\nISO live at 2026-09-17 (every predicted record, every premium field for field, messages):")
        for rid, (j, sub, preds) in results.items():
            req = r11.payload(sub)
            for cp in req["body"]["CommercialProperty"]:
                cp["State"] = j
            req["body"]["SchemeKeys"]["ProductName"] = r11.PRODUCT.format(state=j)
            (gc.OUT / f"chunk16_rc4_{rid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
            try:
                resp = client.rate(req)
            except raas_mod.RaaSError as exc:
                m = re.search(r"Matrix: (\w+).*?Keys: ([^.]*)", str(exc.body)) or re.search(r'"Message":"([^"]{0,160})', str(exc.body))
                print(f"  {rid:5s} ISO REFUSES {m.group(0)[:170] if m else str(exc.body)[:170]}")
                FAIL.append(f"{rid} live")
                continue
            (gc.OUT / f"chunk16_rc4_{rid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
            pbad = []
            for rec, want in preds.items():
                iso = r2.iso_of(resp, rec)
                if want == "NONE":
                    if not all(zeroish(x) for x in iso):
                        pbad.append((rec, iso, "not priced"))
                elif sorted(Decimal(str(x)) for x in iso if not r2.same(x, 0)) != sorted(Decimal(str(w)) for w in want if not r2.same(w, 0)):
                    pbad.append((rec, iso, [str(w) for w in want]))
            data, ip = rep.cmp.rate(req)
            ipr, opr = rep.iso_prem(resp), rep.our_prem(data)
            d = [(k, v, opr.get(k)) for k, v in ipr.items() if not rep.cmp.same(v, opr.get(k))]
            mi, mo = cmp.iso_messages(resp), set(ip.messages)
            ok = not pbad and not d and mi == mo
            agree += ok
            print(f"  {rid:5s} {'AGREE' if ok else 'DIFFER'}: predicted {len(preds) - len(pbad)} of {len(preds)}; "
                  f"{len(ipr) - len(d)} of {len(ipr)} premiums; messages {'equal' if mi == mo else 'DIFFER'}"
                  + "".join(f"\n        predicted {r16.short(r)[:58]}: ISO {x}, derived {w}" for r, x, w in pbad[:5])
                  + "".join(f"\n        {k[-90:]} ISO {v} ours {o}" for k, v, o in d[:5])
                  + (f"\n        ISO only {sorted(mi - mo)[:3]}\n        ours only {sorted(mo - mi)[:3]}" if mi != mo else ""))
            if not ok:
                FAIL.append(f"{rid} live")
        print(f"\n  live: {agree} of {len(results)} agree")
    print(f"\nRC-4: {'ALL AGREE' if not FAIL else 'FAILED: ' + ', '.join(FAIL)}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
