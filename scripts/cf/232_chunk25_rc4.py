#!/usr/bin/env python3
"""Chunk 25, RC-4 (C25-18..C25-22): Flood in the states, the editions, WV and Off-Premises. Live ISO.

How each figure is derived before it runs:
  * countrywide SetPremium: 229_'s hand model, from THAT state's tables (state rows, else CW) and THAT state's edition
    (MO's CW 2023 V02: table 6 at '500,000' for any excess deductible, contents / SC on the location's deductible,
    blanket total property value per location); the county states pick the county or all-other loss-cost table from the
    counties / cities their SetFloodBaseRate names
  * a state that rewrites SetPremium (NY: no cyber factors): 174_'s evaluator on the state's own rule, AND the hand model
    (no cyber exclusion on these policies, so both must agree)
  * AK and FL: r0(r0(ManualPremium x package mod) x IRPM) on every premium record (their own SetPremium); AK's blanket
    detail has no premium rule at all (ErcRate emptied)
  * WV's Ordinance or Law flood forms: r0(r0(r0(ManualPremium x package mod) x the building's MPDC) x IRPM), on only with
    the O&L record's FloodOnlyLimitation "Yes"; WV's O&L Coverage A prices $0 when FloodOnlyLimitationOnOrdinanceOrLaw "Yes"
  * Off-Premises Interruption: FloodCovFactor = OffPremEndtsModifyingCovdCOLFactor 'Flood Coverage' (1.02) when the BI
    carries a flood record, else 1.0; the OTC premium by 174_'s evaluator on the state's own rule
  Then every premium is compared with ISO field for field, and the whole (level, message) multiset.

  C25-18/19/21  S-<j>  all 46 states: location 1 with flood on all five records (a LISTED county in the county states),
                       location 2 the same with building and contents in a flood blanket (an all-other county), manual
                       premiums entered on every record (read only in AK / FL)
  C25-19        Z-AK, Z-FL  the manual premium left blank: $0
  C25-21        E<x>-<j>  edition probes in MO (V02), NC (V03), IL (V04) and OR (2026): EX excess at 1,000,000 (MO table 6
                       '500,000' vs table 7), ED a blanket detail deductible of 500,000 (MO contents keep 10,000), ET blanket
                       members on two locations (MO: total property value per location)
  C25-20        W1 WV O&L and tenants' O&L flood forms on, Coverage A flood-only; W2 the O&L form with no building flood
                       record (CP 10 68 message); W3 FloodOnlyLimitation "No" (forms off, Coverage A priced)
  C25-22        O-<j> / ON-<j>  Off-Premises on BI with / without the BI flood record, in OR AK AR DC NY RI

    python scripts/cf/232_chunk25_rc4.py [--live] [--cases ...] [--states AK,AL] [--all]
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
import time
from decimal import Decimal
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))
sys.stdout.reconfigure(line_buffering=True)
T0 = time.monotonic()

c3 = import_module("231_chunk25_rc3")
c2, x, t2 = c3.c2, c3.x, c3.t2
m, rc1, rep, cmp, gc, r11 = x.m, x.rc1, x.rep, x.cmp, c3.gc, c3.r11
P, D, val, d, r = x.P, Decimal, x.val, x.d, x.r
B, PP, SC, BI, SCBI, LOCR, BRD = x.B, x.PP, x.SC, x.BI, x.SCBI, x.LOCR, x.BRD
s18 = import_module("164_chunk14_c14-18_all_states")
no_eq = import_module("217_chunk22_rc4").no_eq
FL_SC = import_module("177_chunk16_rc4").FL_SC
CW_TENANTS = import_module("221_chunk23_rc3").CW_TENANTS
r11.NUMERIC |= {"ManualPremium", "LimitOfInsurance"}
FAIL = []
ALT = {}
MANUAL = {B: "650", PP: "440", SC: "300", BI: "84", SCBI: "120"}
#: a listed county (location 1) and an all-other one (location 2) per county state; VA lists cities too
COUNTY = {"MA": ("Barnstable", "Worcester"), "NC": ("Dare", "Wake"), "NJ": ("Cape May", "Mercer"), "NY": ("Suffolk", "Albany"),
          "SC": ("Charleston", "Richland"), "TX": ("Galveston", "Travis"), "VA": ("Accomack", "Fairfax")}
OP = "OffPremInterruptionOfBusnVehsMobileEquipmtBusnInc"
OL_FLOOD, TEN_FLOOD = "OrdinanceOrLawCovFloodCoverage", "OrdinanceOrLawCoverageForTenantsInterestInImprovementsAndBettermentsFloodCoverage"
WV_RECS = [OL_FLOOD, TEN_FLOOD]


def progress(i, n, what):
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{i}/{n}  {mm}m{s:02d}s] {what}")


# ------------------------------------------------------------------ builders

def locs(sub):
    return sub[P + "Table"][P][0][P + "LocationTable"][P + "Location"]


def state_fixes(sub, j):
    if j == "FL":
        no_eq(sub)                                     # 208_'s Florida recipe (EQ class A1 not filed in FL: OI-103)

        def fl_sc(o):                                  # FL files no "Towers - Broadcasting Antennas" (C15-16)
            if isinstance(o, dict):
                for k, v in o.items():
                    if k == P + "SpecialClassTable":
                        for s_ in v[P + "SpecialClass"]:
                            s_["ClassDescription"] = FL_SC
                    fl_sc(v)
            elif isinstance(o, list):
                for v in o:
                    fl_sc(v)
        fl_sc(sub)
    return sub


def manual(sub, blank=False):
    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                for rec, mp in MANUAL.items():
                    if k == P + rec + "Table":
                        for row in v[P + rec]:
                            if blank:
                                row.pop("ManualPremium", None)
                            else:
                                row["ManualPremium"] = mp
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(sub)
    return sub


def second_location(sub, blanket_ids=None, county=None):
    """location 2: a copy of location 1 (all five flood records), the given records put in blanket 1."""
    l1 = locs(sub)[0]
    l1["UnitNumber"] = "1"
    l2 = copy.deepcopy(l1)
    l2["UnitNumber"] = "2"
    if county:
        l2["County"] = county
    for rec, bid in (blanket_ids or {}).items():
        parent = {B: "Structure", PP: "PersonalProperty", SC: "SpecialClass"}[rec]

        def walk(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    if k == P + rec + "Table":
                        for row in v[P + rec]:
                            row.update({"IncludedInBlkt": "Yes", "BlanketIDNum": str(bid)})
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)
        walk(l2)
    locs(sub).append(l2)
    return sub


def state_policy(j, blank_manual=False):
    def build():
        sub = x.flood_tree(j=j)
        if j in COUNTY:
            locs(sub)[0]["County"] = COUNTY[j][0]
            locs(sub)[0].pop("City", None)
        second_location(sub, {B: 1, PP: 1}, county=COUNTY[j][1] if j in COUNTY else None)
        x.add_blanket(sub, [c3.det(1, "300000", BldgCov="Yes", PrsnlPropCov="Yes", ManualPremium="200")], {})
        manual(sub, blank=blank_manual)
        if blank_manual:
            sub[P + "Table"][P][0][P + x.BR + "Table"][P + x.BR][0][P + BRD + "Table"][P + BRD][0].pop("ManualPremium", None)
        return state_fixes(sub, j)
    return build


def edition_probe(kind, j):
    def build():
        if kind == "EX":                               # excess at 1,000,000: 2026 table 7; MO table 6 at '500,000'
            sub = x.flood_tree(j=j, ded="1,000,000", full=("4000000", "3000000", "2500000"),
                               recs={B: {"ExcessOverMaxNFIPIndicator": "Yes", "Limit": "2000000"},
                                     PP: {"ExcessOverMaxNFIPIndicator": "Yes", "Limit": "1500000"},
                                     SC: {"ExcessOverMaxNFIPIndicator": "Yes", "Limit": "1250000"}})
        elif kind == "ED":                             # a detail deductible of 500,000: 2026 contents take it; MO 10,000
            sub = x.flood_tree(j=j)
            x.add_blanket(sub, [c3.det(1, "200000", BldgCov="Yes", PrsnlPropCov="Yes", Deductible="500,000")], {B: 1, PP: 1})
        else:                                          # ET: members on two locations; MO totals per location
            sub = x.flood_tree(j=j)
            second_location(sub, {PP: 1})
            for rec in (B, PP):                        # location 1's building and contents in the blanket too
                for row in m.at(sub)[P + {B: "Structure", PP: "PersonalProperty"}[rec]][P + rec + "Table"][P + rec]:
                    row.update({"IncludedInBlkt": "Yes", "BlanketIDNum": "1"})
            x.add_blanket(sub, [c3.det(1, "300000", BldgCov="Yes", PrsnlPropCov="Yes")], {})
        return state_fixes(sub, j)
    return build


def wv(kind):
    def build():
        sub = x.flood_tree(j="WV", keep=(x.PP, x.SC, x.BI, x.SCBI) if kind == "W2" else x.PROP + x.TE)
        st = m.at(sub)[P + "Structure"]
        flag = "No" if kind == "W3" else "Yes"
        ol = {"CovType": "Coverages A and B & C Separate", "CovBDemolitionLimit": "20000", "CovCIncreasedConstructionLimit": "30000",
              "PostLossOrdinanceOrLawOption": "No", "FloodOnlyLimitation": flag,
              "FloodOnlyLimitationOnOrdinanceOrLaw": "Yes" if kind == "W1" else "No", P + OL_FLOOD: {"ManualPremium": "300"}}
        ten = {"CovType": "Coverages A and B & C Separate", "CovBDemolitionLimit": "20000", "CovCIncreasedConstructionLimit": "30000",
               "PostLossOrdinanceOrLawOption": "No", "FloodOnlyLimitation": flag, P + TEN_FLOOD: {"ManualPremium": "150"}}
        st[P + "OrdinanceOrLawCoverageTable"] = {P + "OrdinanceOrLawCoverage": [ol]}
        st[P + CW_TENANTS + "Table"] = {P + CW_TENANTS: [ten]}
        return sub
    return build


def offprem(j, with_flood):
    def build():
        sub = x.flood_tree(j=j, keep=x.PROP + x.TE if with_flood else x.PROP + (SCBI,))
        for f in ("Collision", "OTC"):
            m.put(sub, f"{OP}Detail{f}", {}, j)
        bi = m.at(sub)[P + "BusinessIncome"]
        cont = bi[P + OP + "Table"][P + OP][0]
        cont.update({"CollisionCovCOL": "Yes", "ExtendedPeriod": "150"})
        cont[P + OP + "DetailTable"][P + OP + "Detail"][0].update({"Limit": "37500", "Option": "Option B", "PercentInsToExposure": "Under 25%"})
        return state_fixes(sub, j)
    return build


def cases(states):
    out = {}
    for j in states:
        task = "C25-18" if j in COUNTY else "C25-19" if j in ("AK", "FL") else "C25-21"
        out[f"S-{j}"] = (task, j, f"{j}: flood on all five records + a building / contents blanket on location 2", state_policy(j))
    for j in ("AK", "FL"):
        out[f"Z-{j}"] = ("C25-19", j, f"{j}: the manual premium left blank ($0)", state_policy(j, blank_manual=True))
    for kind, label in (("EX", "excess at 1,000,000"), ("ED", "blanket detail deductible 500,000"), ("ET", "blanket members on two locations")):
        for j in ("MO", "NC", "IL", "OR"):
            out[f"{kind}-{j}"] = ("C25-21", j, f"{j} ({x.edition(j)}): {label}", edition_probe(kind, j))
    for kind, label in (("W1", "O&L and tenants' O&L flood forms on, Coverage A flood-only ($0)"),
                        ("W2", "the O&L flood form with no building flood record (CP 10 68 message)"),
                        ("W3", "FloodOnlyLimitation No: the forms off, Coverage A priced")):
        out[kind] = ("C25-20", "WV", label, wv(kind))
    for j in ("OR", "AK", "AR", "DC", "NY", "RI"):
        out[f"O-{j}"] = ("C25-22", j, f"{j}: Off-Premises on BI with the BI flood record (FloodCovFactor 1.02)", offprem(j, True))
        out[f"ON-{j}"] = ("C25-22", j, f"{j}: Off-Premises on BI without it (1.0)", offprem(j, False))
    return out


# ------------------------------------------------------------------ prediction

def own_setpremium(j, rec):
    f = book_for_state(j) / "Rules" / f"{P}{rec}Rules.Rule.xml"
    if not f.exists():
        return None
    body = m.cen.set_premium(f.read_text(encoding="utf-8-sig"))
    return body if body and body != m.cen.set_premium(x.RULES.get(rec, "")) else None


def book_for_state(j):
    return x.book_for(j, x.ASOF).state.package.content


def predict(cid, case):
    task, j, label, build = case
    req = t2.state_req(t2.m20.payload(build()), j)
    c3.TAGGED.clear()
    data, ip = cmp.rate(req)
    lines, bad, preds, how = [], [], {}, {}
    for rec in x.PREMIUM_RECS:
        own = own_setpremium(j, rec)
        preds[rec] = []
        for node, hv, ev, e in x.predict(data, rec, j):
            if j in ("AK", "FL"):
                if rec == BRD and j == "AK":
                    want, kind = None, "AK: no premium rule"
                else:
                    want, kind = x.hand_manual(node), f"{j} manual premium"
                    if own:
                        ev2 = r16_hand(own, node)
                        if not m.same(ev2, want):
                            bad.append(f"{rec[-30:]} {j} evaluator {ev2} manual {want}")
                ok = (e in (None, "0", "0.0") if want is None else m.same(want, e))
            else:
                pr = {}
                x.hand(j, node, rec, pr)
                diff = x.parts_agree(rec, node, pr)
                want, kind = hv, "hand"
                ok = m.same(hv, e) and not diff
                if own:
                    ev2 = r16_hand(own, node)
                    kind = f"hand = {j}'s own rule"
                    ok = ok and m.same(ev2, e)
                elif ev is not None and not m.same(ev, e):
                    ok = False
                if diff:
                    bad.append(f"{rec[-30:]} parts {diff}")
            how[kind] = how.get(kind, 0) + 1
            preds[rec].append(want if want is not None else D(0))
            name = rec[len(x.FL):] or ("Building" if rec == B else rec)
            if not ok:
                bad.append(f"{name} {kind} {want} engine {e}")
            if not m.same(e, 0) or not ok:
                lines.append(f"      {'ok  ' if ok else 'FAIL'} {name[:30]:30s} {kind:22s} {want} engine {e}")
    if cid.startswith("W"):
        for rec in WV_RECS:
            preds[rec] = []
            for node in rc1.find(data, P + rec):
                st = x.anc(node, "Structure")
                cpn = m.root(node)
                on = val(node.parent, "FloodOnlyLimitation") == "Yes"
                want = (r(r(r(d(node, "ManualPremium") * d(cpn, "PackageModFactor"), 0) * d(st, "MultiPremiumAndDispersionCreditFactor"), 0)
                          * d(cpn, "IRPMFactor"), 0) if on else D(0))
                ok = m.same(want, val(node, "Premium") or "0")
                preds[rec].append(want)
                lines.append(f"      {'ok  ' if ok else 'FAIL'} {rec[:40]:40s} WV manual  {want} engine {val(node, 'Premium')} (FloodOnlyLimitation {val(node.parent, 'FloodOnlyLimitation')})")
                if not ok:
                    bad.append(f"{rec} {want} engine {val(node, 'Premium')}")
        cova = [(n.tag[len(P):], val(n, "Premium")) for n in rc1.find(data, P + "OrdinanceOrLawCoverage")[0].children
                if n.tag.startswith(P + "OrdinanceOrLawCovACoverage")] if rc1.find(data, P + "OrdinanceOrLawCoverage") else []
        priced = [p for _, p in cova if p not in (None, "0", "0.0")]
        want_zero = cid == "W1"
        ok = (not priced) if want_zero else bool(priced)
        lines.append(f"      {'ok  ' if ok else 'FAIL'} O&L Coverage A premiums {cova} (predicted {'all $0: flood-only' if want_zero else 'priced'})")
        if not ok:
            bad.append("WV Coverage A")
        forms = [(rec[len(x.FL):] or "Building", val(n, "ErcFormNumber")) for rec in x.PROP + x.TE for n in rc1.find(data, P + rec)]
        lines.append(f"      flood form numbers (ours): {forms}")
    if cid.startswith("O"):
        for kind_ in ("OTC", "Collision"):
            rec = f"{OP}Detail{kind_}"
            own = own_setpremium(j, rec) or m.cen.set_premium((x.CW / "Rules" / f"{P}{rec}Rules.Rule.xml").read_text(encoding="utf-8-sig"))
            preds[rec] = []
            for node in rc1.find(data, P + rec):
                ev2 = r16_hand(own, node)
                preds[rec].append(ev2)
                ok = m.same(ev2, val(node, "Premium"))
                lines.append(f"      {'ok  ' if ok else 'FAIL'} Off-Premises {kind_:9s} {j}'s rule {ev2} engine {val(node, 'Premium')}")
                if not ok:
                    bad.append(f"Off-Premises {kind_}")
        cont = rc1.find(data, P + OP)[0]
        want = x.one(j, "OffPremEndtsModifyingCovdCOLFactor", "Factor", Endorsement="Flood Coverage") if cid.startswith("O-") else D("1.0")
        ok = m.same(want, val(cont, "FloodCovFactor"))
        lines.append(f"      {'ok  ' if ok else 'FAIL'} FloodCovFactor {val(cont, 'FloodCovFactor')} (table {want})")
        if not ok:
            bad.append("FloodCovFactor")
    if cid in ("EX-MO", "ED-MO", "ET-MO"):
        # the competing reading: MO priced by the 2026 rules (contents on the detail's deductible, excess on the table the
        # deductible picks, blanket totals across locations); ISO can match only one
        real = x.edition
        x.edition = lambda jj: "2026"
        try:
            ALT[cid] = {rec: [x.hand(j, node, rec) for node in rc1.find(data, P + rec)] for rec in x.PREMIUM_RECS}
        finally:
            x.edition = real
        lines.append(f"      2026 reading in MO: {[(rr[len(x.FL):] or 'Building')[:14] + ' ' + str(v) for rr, vs in ALT[cid].items() for v in vs if not m.same(v, 0)]}")
    print(f"{cid:7s} {task} {j} {label}: {'as predicted' if not bad else 'DIFFERS ' + '; '.join(bad[:3])}  {how}")
    print("\n".join(lines[:22]))
    if bad:
        FAIL.append(cid)
    return req, data, ip, preds


def r16_hand(body, node):
    try:
        return m.r16.hand(body, node)
    except Exception as exc:
        return f"evaluator {type(exc).__name__}"


def live(client, raas_mod, cid, req, data, ip, preds):
    (gc.OUT / f"chunk25_rc4_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
    try:
        resp = client.rate(req)
    except raas_mod.RaaSError as exc:
        mm_ = re.search(r'"Message":"([^"]{0,300})', str(exc.body))
        print(f"  {cid:7s} ISO REFUSES {mm_.group(1) if mm_ else str(exc.body)[:300]}")
        FAIL.append(f"{cid} live")
        return
    (gc.OUT / f"chunk25_rc4_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
    import collections
    c3.TAGGED.clear()
    data2, _ = cmp.rate(req)
    ours = collections.Counter((c3.lvl(t), y) for t, y in c3.TAGGED)
    isos = collections.Counter(c3.iso_tagged(resp))
    ipr, opr = rep.iso_prem(resp), rep.our_prem(data2)
    dd = [(k, v, opr.get(k)) for k, v in ipr.items() if not rep.cmp.same(v, opr.get(k))]
    pbad = []
    for rec, want in preds.items():
        iso = sorted(D(str(v)) for v in t2.m.r2.iso_of(resp, rec) if v is not None and not m.same(v, 0))
        w = sorted(D(str(v)) for v in want if not isinstance(v, str) and not m.same(v, 0))
        if iso != w:
            pbad.append((rec, iso, w))
    forms = []
    if cid.startswith("W"):
        def walk(o, k=None):
            if isinstance(o, dict):
                if k and any(k == P + rec for rec in x.PROP + x.TE + tuple(WV_RECS)):
                    forms.append((k[len(P):][-24:], o.get("ErcFormNumber")))
                for kk, v in o.items():
                    if isinstance(v, (dict, list)):
                        walk(v, kk)
            elif isinstance(o, list):
                for v in o:
                    walk(v, k)
        walk(resp)
    ok = not dd and not pbad and ours == isos
    if cid in ALT:
        iso_all = {rec: sorted(D(str(v)) for v in t2.m.r2.iso_of(resp, rec) if v is not None and not m.same(v, 0)) for rec in ALT[cid]}
        alt_all = {rec: sorted(D(str(v)) for v in vs if not m.same(v, 0)) for rec, vs in ALT[cid].items()}
        pred_all = {rec: sorted(D(str(v)) for v in preds[rec] if not m.same(v, 0)) for rec in ALT[cid]}
        print(f"  {cid:7s} edition probe: ISO = the V02 reading {'YES' if iso_all == pred_all else 'no'}; ISO = the 2026 reading "
              f"{'YES' if iso_all == alt_all else 'no'} (the readings differ: {alt_all != pred_all})")
    print(f"  {cid:7s} {'AGREE' if ok else 'DIFFER'}: flood records as predicted {'yes' if not pbad else 'NO'}; "
          f"{len(ipr) - len(dd)} of {len(ipr)} premiums; (level, message) {'equal' if ours == isos else 'DIFFER'} ({sum(isos.values())} ISO)"
          + (f"\n        ISO form numbers: {forms}" if forms else "")
          + "".join(f"\n        predicted {rr[-45:]}: ISO {[str(v) for v in i_]} predicted {[str(v) for v in w_]}" for rr, i_, w_ in pbad[:6])
          + "".join(f"\n        {k[-90:]} ISO {v} ours {o}" for k, v, o in dd[:6])
          + "".join(f"\n        ISO only {t.replace(P, '') or 'policy'}: {y[:110]} x{n}" for (t, y), n in (isos - ours).items())
          + "".join(f"\n        ours only {t.replace(P, '') or 'policy'}: {y[:110]} x{n}" for (t, y), n in (ours - isos).items()))
    if not ok:
        FAIL.append(f"{cid} live")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--cases")
    ap.add_argument("--states", help="comma list for the state policies")
    ap.add_argument("--all", action="store_true", help="all 46 states (state policies only)")
    a = ap.parse_args()
    states = s18.STATES if a.all else (a.states.split(",") if a.states else [])
    cs = cases(states or s18.STATES)
    if a.cases:
        cs = {k: v for k, v in cs.items() if k in a.cases.split(",")}
    elif states:
        cs = {k: v for k, v in cs.items() if k.startswith("S-") and k[2:] in states}
    else:
        cs = {k: v for k, v in cs.items() if not k.startswith("S-")}
    client = raas_mod = None
    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
    for i, (cid, case) in enumerate(cs.items(), 1):
        progress(i, len(cs), cid)
        try:
            req, data, ip, preds = predict(cid, case)
        except Exception as exc:
            print(f"{cid}: RAISED {type(exc).__name__}: {str(exc)[:240]}")
            FAIL.append(cid)
            continue
        if a.live:
            live(client, raas_mod, cid, req, data, ip, preds)
        del data, ip
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"\nRC-4 (C25-18..C25-22): {'ALL AGREE' if not FAIL else 'FAILED: ' + ', '.join(FAIL)}  ({mm}m{s:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
