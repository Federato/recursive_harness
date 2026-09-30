#!/usr/bin/env python3
"""Chunk 21, RC-2: golden cases, live ISO. C21-06 Sewer backup.

Every case sits on 175_'s Oregon policy (chunk 7's five coverages, chunk 15's modifiers), cause Special.
Each sewer premium is predicted by 207_'s hand model (C21-03: the record's OWN rule file, every borrowed
value read where its ../ path lands, 33 of 33 hand = engine) and by 174_'s SetPremium evaluator; the
engine must equal both, and --live ISO must equal the prediction, every premium on the policy compared,
messages compared. Each case is chosen so a competing reading gives a different dollar:

  SW1  all five records, limit 25,000 each: PD 0.77 x the deductible factor x 250; BI 0.07 x 250
       Personal Property borrows the BUILDING sewer's factor (0.98), not its own parent's
  SW2  building deductible 250 (Deductible250Factor 'All Other' 1.1), special class deductible 5,000:
       the deductible moves the Building, Personal Property (borrowed) and Special Class premiums
  SW3  Personal Property sewer ALONE: no Building sewer record to borrow from -> factor 1 (170);
       the reading "its own parent's deductible" gives 167
  SW4  limits differ by record: Building 50,000, PP 10,000, Special Class 30,000, BI 100,000, SCBI 40,000
  SW5  PROBE: the No Waiting Period endorsement on both Business Income parents. The rules multiply the
       sewer BI rate by the endorsement's Factor (BaseFactor - 1 = 0 in Oregon), so the engine prices sewer
       BI at $0; the reading "rate x BaseFactor" or "rate unchanged" gives 17

C21-07 Loss assessment (predicted by 207_'s la_by_hand, C21-04: 33 of 33 hand = engine)
  LA1  1,000, Special, deductible 1,000                LA2  5,000, Broad, deductible 500, sub-limit 3,000 (band 1)
  LA3  10,000, Basic, N/A, sub-limit 8,000 (band 2)    LA4  Over 10,000 = 25,000, Special, 250, sub 14,000 (band 3)
  LA5  Over 10,000 = 20,000, Broad, 2,500, sub-limit 10,000 (N = 9: the band 2 / band 3 edge)
  PROBES, ISO's own edges (engine / competing reading):
  LA6  Over 10,000 = 12,000: the multiple-of-5,000 check runs only from 15,000, so it prices at 0.4 of a
       step with no message / a message and $0
  LA7  Over 10,000 = 17,500: $0 with the multiple-of-5,000 message / priced
  LA8  sub-limit 11,500: not a multiple of 1,000 above 10,000 -> ignored, with a message / priced
  LA9  sub-limit 5,500: the check only runs above 10,000 -> priced as 5 thousands, no message / a message

C21-08 Miscellaneous real property: Rate 0.528 (MiscRealPropRate, key "Y", no cause of loss) x the contents'
  LCM x a deductible factor x limit / 100 x the modifiers. The factor reads the CONTAINER's
  LossAssessmentDeductible: blank or N/A -> 1.0 (loss assessment's blank gives 0); 250 -> 1.1; otherwise
  DeductibleFactor banded on the misc. real property LIMIT, 'Other Cause Of Loss'.
  MR1  20,000, Special, no deductible (93; the loss-assessment reading of a blank gives 0)
  MR2  50,000, Broad, 1,000        MR3  20,000, Basic, 250        MR4  50,000, Special, 2,500
  MR5  20,000, Special, N/A        MR6  50,000, Basic, 1,000 (= MR2: the cause of loss moves nothing)
  Each sends loss assessment limit "0". The container's InitializeRuleSet creates the loss assessment record
  whether it is sent or not, and its switch tests only for "0": a BLANK limit switches it on and ISO refuses
  at LossAssessmentRate (keys CW, blank, cause) while ours prices it $0. MRZ pins that (OI-103), found
  2026-09-30 when MR1-MR6 were first sent without the "0".

C21-09 Florida, Commercial Units in Residential Condominiums (FL's own five records, on 189_'s portable FL
  policy): Premium = round0(ManualPremium x IRPM x package mod), ONE rounding, no multi-premium credit
  (the stepwise reading gives 245 for 250; the credit reading gives 88 for 100). The three CPP records
  price only on their CovForm / CovType + PolicyType "Commercial Property Policy"; the two SPP records are
  ISO auto-attach forms (CovForm unit owners + PolicyType SPP + class 0331-0343 / ItemsBelongToResidentialCondo).
  The CPP special-class record declares ManualPremium as TEXT (its rule converts it); it is sent as text.
  FC1  occupancy, unit owners form, 100          FC2  building, Condominium Association, 250
  FC3  special class, unit owners form, 175      FC4  SPP occupancy, class 0331, 100
  FC5  SPP special class, ItemsBelongToResidentialCondo Yes, 300
  FC6  occupancy record on the policy's own form (gate not met): $0 / priced
  The Florida cases drop every earthquake input (FL files EQ classes like "1C", not the portable "A1":
  OI-103) and use FL_SC for the special class (FL files no "Towers - Broadcasting Antennas").
  FC5 is a KNOWN difference (OI-116, 2026-09-30): ISO never attaches the SPP special-class record.

    python scripts/cf/208_chunk21_rc2.py [--live] [--cases SW1,SW5]

Progress streams as [i/n elapsed] lines. Exits 1 on any disagreement.
"""
from __future__ import annotations

import argparse
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

from gl_engine.interp.values import InterpretError                       # noqa: E402

h21 = import_module("207_chunk21_rc1")
r2, g19, rc1, r16 = h21.r2, h21.g19, h21.rc1, h21.r16
gc, rep, cmp, r11 = r2.gc, r2.rep, r2.cmp, r2.r11
P, SEWER, NWP = h21.P, h21.SEWER, h21.NWP
same = r2.same
r11.NUMERIC |= {"DischargeLimitPD", "DischargeLimitBI", "ManualPremium",  # xs:int / xs:decimal in the XSD
                "LossAssessmentLimitOver10000", "LossAssessmentSubLimit", "MiscRealPropLimit"}
LA, MRP, OPT = h21.LA, h21.MRP, h21.OPT
cen20 = import_module("901_chunk20_census")
FAIL = []
BLDG, PP, SC, BI, SCBI = SEWER
#: OI-103 (a SingleResult lookup with no row): ISO refuses where the engine rates. A refusal naming this
#: table is the EXPECTED live result for these cases, pinned as evidence; the decision stays with chunk 28.
EXPECT_REFUSAL = {"MRZ": "LossAssessmentRate"}
#: known ISO differences, pinned: the case prints its differences and does not fail the run.
KNOWN_DIFF = {"FC5": "OI-116: ISO never attaches FL's SPP special-class condo record; ours prices it"}


def progress(i, n, what):
    m, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{i}/{n}  {m}m{s:02d}s] {what}")


def base(cause="Special"):
    return g19.with_cause(g19.portable("OR"), cause)


def options(cause, cont, recs=None):
    """the unit-owners options container on the contents with the coverage records `recs` beneath it (both by
    default). Send only the record wanted: an EMPTY loss assessment record switches itself on at a blank
    limit (its switch tests only for "0"), and ISO then refuses at its rate lookup (OI-103)."""
    def b():
        sub = base(cause)
        rc1.node_dicts(sub)[P + "PersonalProperty"][P + OPT + "Table"] = {
            P + OPT: [dict(cont, **{P + r: {} for r in (recs or (LA, MRP))})]}
        return sub
    return b


def la(lim, cause, ded=None, sub=None, over=None):
    c = {"LossAssessmentLimit": lim}
    for k, v in (("LossAssessmentDeductible", ded), ("LossAssessmentSubLimit", sub), ("LossAssessmentLimitOver10000", over)):
        if v is not None:
            c[k] = v
    return options(cause, c)


def mrp(lim, cause, ded=None, la_limit="0"):
    """misc. real property alone. The container's InitializeRuleSet CREATES both coverage records whether sent
    or not, so "alone" means loss assessment limit "0" (the dropdown's none); blank switches it ON (OI-103)."""
    c = {"MiscRealPropLimit": lim}
    if la_limit is not None:
        c["LossAssessmentLimit"] = la_limit
    if ded is not None:
        c["LossAssessmentDeductible"] = ded
    return options(cause, c, [MRP])


def mrp_by_hand(node):
    """SetRate / SetDeductibleFactor / SetPremium of the misc. real property record, written out."""
    cont, pp, cp = node.parent, h21.up(node, 3), h21.up(node, 11)
    lim = h21.val(cont, "MiscRealPropLimit")
    if lim is None:
        return Decimal(0)
    own, cw, _ = h21.table_rows("MiscRealPropRate")
    rate = next(Decimal(x["Rate"]) for x in own + cw if x["Constant"] == "Y")
    ded = h21.val(cont, "LossAssessmentDeductible") or ""
    if ded in ("", "Not Applicable"):
        dedf = Decimal("1.0")
    elif ded == "250":
        own, cw, _ = h21.table_rows("Deductible250Factor")
        dedf = next(Decimal(x["Factor"]) for x in own + cw if x["CauseOfLoss"] == "All Other")
    else:
        own, cw, _ = h21.table_rows("DeductibleFactor")
        dedf = next((Decimal(x["Factor"]) for rows in (own, cw) for x in rows
                     if x["Deductible"] == ded and x["CauseOfLossDeductible"] == "Other Cause Of Loss"
                     and Decimal(x["Limit_FromGreaterThan"]) < Decimal(lim) <= Decimal(x["Limit_To"])), Decimal(0))
    r = h21.r
    p = r(r(r(rate * Decimal(h21.val(pp, "LossCostMultiplier") or 0), 3) * dedf, 3) * Decimal(lim) / 100, 0)
    for f in (h21.val(cp, "PackageModFactor"), h21.val(pp, "MultiPremiumAndDispersionCreditFactor"), h21.val(cp, "IRPMFactor")):
        p = r(p * Decimal(f or 0), 0)
    return p


FLR = "ChangesCommercialUnitsInResidentialCondominiumsIncludingOptionForAddlCoveredProperty"
FLSPP = "ChangesCommercialUnitsInResidentialCondosIncludingOptionForAddlCoveredPropertySPP"
FL_RECS = {FLR + "OccupClass", FLR, FLR + "SpecClass", FLSPP + "OccupClass", FLSPP + "SpecClass"}
TEXT_MANUAL = P + FLR + "SpecClass"                   # ManualPremium declared xs:string on this record only
UO = "Condominium Commercial Unit Owners Coverage"
FL_SC = import_module("177_chunk16_rc4").FL_SC     # FL files no "Towers - Broadcasting Antennas" (C15-16)


def no_eq(o):
    """drop every earthquake input: the portable policy's EQ class "A1" is not one Florida files (FL's
    BldgHeightFactor keys EQ classes like "1C"; ISO refuses, ours rates: OI-103, logged at chunk 17's gate).
    The Florida condo records read nothing from earthquake."""
    if isinstance(o, dict):
        for k in [k for k in o if k.startswith("EQ")]:
            del o[k]
        for v in o.values():
            no_eq(v)
    elif isinstance(o, list):
        for v in o:
            no_eq(v)
    return o


def florida(rec, manual, gate=True):
    def b():
        sub = no_eq(g19.with_cause(g19.portable("FL"), "Special"))
        at = rc1.node_dicts(sub)
        at[P + "SpecialClass"]["ClassDescription"] = FL_SC
        spp = "SPP" in rec
        at[P]["PolicyType"] = "Standard Property Policy" if spp else "Commercial Property Policy"
        if gate:
            if rec.endswith("OccupClass"):
                at[P + "OccupClass"]["CovForm"] = UO
                if spp:
                    at[P + "OccupClass"]["ClassCode"] = "0331"
            elif rec.endswith("SpecClass"):
                at[P + "SpecialClass"]["CovForm"] = UO
                if spp:
                    at[P + "SpecialClass"]["ItemsBelongToResidentialCondo"] = "Yes"
            else:
                at[P + "Structure"]["CovType"] = "Condominium Association"
        r2.put(sub, rec, {"ManualPremium": str(manual)}, state="FL")
        return sub
    return b


def fl_by_hand(node, rec):
    depth = 8 if rec.endswith("OccupClass") else 6
    cp = h21.up(node, depth)
    par = node.parent.parent
    gate = True
    if "SPP" not in rec:
        gate = (h21.val(par, "CovType") == "Condominium Association" if rec == FLR else h21.val(par, "CovForm") == UO)             and h21.val(cp, "PolicyType") == "Commercial Property Policy"
    if not gate:
        return Decimal(0)
    return h21.r(Decimal(h21.val(node, "ManualPremium") or 0) * Decimal(h21.val(cp, "IRPMFactor") or 0)
                 * Decimal(h21.val(cp, "PackageModFactor") or 0), 0)


def payload(sub, j="OR"):
    """r11's payload, re-keyed to state `j` (r11 writes Oregon's State and ProductName: one request prices one
    state's scheme, so a Florida policy under Oregon's product is priced, or refused, on Oregon's tables)."""
    req = r11.payload(sub)
    if j != "OR":
        for cp in req["body"]["CommercialProperty"]:
            cp["State"] = j
        req["body"]["SchemeKeys"]["ProductName"] = r11.PRODUCT.format(state=j)

    def fix(o, k=None):
        if isinstance(o, dict):
            if k == TEXT_MANUAL and "ManualPremium" in o:
                o["ManualPremium"] = str(o["ManualPremium"])
            for kk, v in o.items():
                fix(v, kk)
        elif isinstance(o, list):
            for v in o:
                fix(v, k)
    fix(req)
    return req


def sewer(limits, deds=None, nwp=False):
    """limits: {record: limit}; deds: {parent short name: deductible}; nwp: the No Waiting Period endorsement
    on both BI parents."""
    def b():
        sub = base()
        at = rc1.node_dicts(sub)
        for par, d in (deds or {}).items():
            at[P + par]["Deductible"] = d
        if nwp:
            r2.put(sub, NWP, {})
            r2.put(sub, NWP + "SpclClassBusnIncome", {})
        for rec, lim in limits.items():
            r2.put(sub, rec, {SEWER[rec]: str(lim)})
        return sub
    return b


def cases():
    all25 = {r: 25000 for r in SEWER}
    return {
        "SW1": ("C21-06", "all five records at 25,000 (building deductible 1,000)", sewer(all25), list(SEWER)),
        "SW2": ("C21-06", "building deductible 250, special class deductible 5,000",
                sewer(all25, {"Structure": "250", "SpecialClass": "5,000"}), list(SEWER)),
        "SW3": ("C21-06", "Personal Property sewer alone: nothing to borrow, factor 1", sewer({PP: 25000}), [PP]),
        "SW4": ("C21-06", "limits 50,000 / 10,000 / 30,000 / 100,000 / 40,000",
                sewer({BLDG: 50000, PP: 10000, SC: 30000, BI: 100000, SCBI: 40000}), list(SEWER)),
        "SW5": ("C21-06", "PROBE: No Waiting Period on both BI parents (engine: sewer BI $0; else 17)",
                sewer(all25, nwp=True), list(SEWER)),
        "LA1": ("C21-07", "1,000, Special, deductible 1,000", la("1,000", "Special", "1,000"), [LA]),
        "LA2": ("C21-07", "5,000, Broad, deductible 500, sub-limit 3,000", la("5,000", "Broad", "500", "3000"), [LA]),
        "LA3": ("C21-07", "10,000, Basic, N/A, sub-limit 8,000", la("10,000", "Basic", "Not Applicable", "8000"), [LA]),
        "LA4": ("C21-07", "Over 10,000 = 25,000, Special, 250, sub-limit 14,000",
                la("Over 10,000", "Special", "250", "14000", "25000"), [LA]),
        "LA5": ("C21-07", "Over 10,000 = 20,000, Broad, 2,500, sub-limit 10,000",
                la("Over 10,000", "Broad", "2,500", "10000", "20000"), [LA]),
        "LA6": ("C21-07", "PROBE: Over 10,000 = 12,000 (engine: priced, no message)",
                la("Over 10,000", "Special", "1,000", None, "12000"), [LA]),
        "LA7": ("C21-07", "PROBE: Over 10,000 = 17,500 (engine: $0 + multiple-of-5,000 message)",
                la("Over 10,000", "Special", "1,000", None, "17500"), [LA]),
        "LA8": ("C21-07", "PROBE: sub-limit 11,500 (engine: ignored + multiple-of-1,000 message)",
                la("Over 10,000", "Special", "250", "11500", "20000"), [LA]),
        "LA9": ("C21-07", "PROBE: sub-limit 5,500 (engine: 5 thousands, no message)",
                la("10,000", "Special", "250", "5500"), [LA]),
        "MR1": ("C21-08", "20,000, Special, no deductible (factor 1, not loss assessment's 0)", mrp("20000", "Special"), [MRP]),
        "MR2": ("C21-08", "50,000, Broad, deductible 1,000", mrp("50000", "Broad", "1,000"), [MRP]),
        "MR3": ("C21-08", "20,000, Basic, deductible 250", mrp("20000", "Basic", "250"), [MRP]),
        "MR4": ("C21-08", "50,000, Special, deductible 2,500", mrp("50000", "Special", "2,500"), [MRP]),
        "MR5": ("C21-08", "20,000, Special, deductible Not Applicable", mrp("20000", "Special", "Not Applicable"), [MRP]),
        "MR6": ("C21-08", "50,000, Basic, deductible 1,000 (= MR2)", mrp("50000", "Basic", "1,000"), [MRP]),
        "FC1": ("C21-09", "FL occupancy, unit owners form, manual 100", florida(FLR + "OccupClass", 100), [FLR + "OccupClass"], "FL"),
        "FC2": ("C21-09", "FL building, Condominium Association, manual 250 (one rounding: 244)", florida(FLR, 250), [FLR], "FL"),
        "FC3": ("C21-09", "FL special class, unit owners form, manual 175 (sent as text)", florida(FLR + "SpecClass", 175),
                [FLR + "SpecClass"], "FL"),
        "FC4": ("C21-09", "FL SPP occupancy, class 0331, manual 100", florida(FLSPP + "OccupClass", 100), [FLSPP + "OccupClass"], "FL"),
        "FC5": ("C21-09", "FL SPP special class, items belong to a residential condo, manual 300",
                florida(FLSPP + "SpecClass", 300), [FLSPP + "SpecClass"], "FL"),
        "FC6": ("C21-09", "FL occupancy on the policy's own form: gate not met, $0", florida(FLR + "OccupClass", 100, gate=False),
                [FLR + "OccupClass"], "FL"),
        "MRZ": ("C21-08", "OI-103: MR1 with the loss assessment limit BLANK (ISO refuses; ours $0)",
                mrp("20000", "Special", la_limit=None), [MRP]),
    }


def predict(data, rec):
    """[(hand model, SetPremium evaluator, engine)] per node of `rec`."""
    pkg = h21.FLPKG if rec in FL_RECS else r2.CW
    body = cen20.set_premium((pkg / "Rules" / f"{P}{rec}Rules.Rule.xml").read_text(encoding="utf-8-sig"))
    out = []
    for node in rc1.find(data, P + rec):
        if rec in FL_RECS:
            hand = fl_by_hand(node, rec)
        elif rec == MRP:
            hand = mrp_by_hand(node)
        elif rec == LA:
            cont = {c.tag: c.text for c in node.parent.children if c.text not in (None, "") and not c.children}
            cont = {k: v for k, v in cont.items() if k in ("LossAssessmentLimit", "LossAssessmentLimitOver10000",
                                                              "LossAssessmentSubLimit", "LossAssessmentDeductible")}
            hand = h21.la_by_hand(cont, h21.up(node, 3), h21.up(node, 11))["Premium"]
        else:
            lim = h21.val(node, SEWER[rec])
            hand = h21.sewer_by_hand(node, rec, lim)["Premium"]
        prem = node.first("Premium")
        out.append((hand, r16.hand(body, node), None if prem is None else prem.text))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--cases")
    a = ap.parse_args()
    cs = cases()
    if a.cases:
        cs = {k: v for k, v in cs.items() if k in a.cases.split(",")}
    preds = {}
    for i, (cid, (task, label, build, recs, *jj)) in enumerate(cs.items(), 1):
        j = jj[0] if jj else "OR"
        progress(i, len(cs), f"engine {cid}")
        try:
            data, ip = gc.run(build(), j)
        except InterpretError as exc:
            print(f"{cid} {task} {label}: RAISED {str(exc)[:150]}")
            FAIL.append(cid)
            continue
        preds[cid] = {}
        lines, bad = [], False
        for rec in recs:
            res = predict(data, rec)
            ok = bool(res) and all(same(h, e) and same(ev, e) for h, ev, e in res)
            bad |= not ok
            preds[cid][rec] = [h for h, _, _ in res]
            lines.append(f"      {'ok  ' if ok else 'FAIL'} {r16.short(rec)[-44:]:44s} predicted {[str(h) for h, _, _ in res]}"
                         f" evaluator {[str(ev) for _, ev, _ in res]} engine {[e for _, _, e in res]}")
        msgs = sorted({str(x)[:90] for x in ip.messages if re.search("Loss Assessment|SubLimit|multiple", str(x))})
        print(f"{cid} {task} {j} {label}: engine {'as predicted' if not bad else 'DIFFERS'}"
              + (f"  messages {msgs}" if msgs else ""))
        print("\n".join(lines))
        if bad:
            FAIL.append(cid)

    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
        print("\nISO live at 2026-09-17 (predicted records, every premium field for field, messages):")
        for i, (cid, (task, label, build, recs, *jj)) in enumerate(cs.items(), 1):
            progress(i, len(cs), f"ISO {cid}")
            req = payload(build(), jj[0] if jj else "OR")
            (gc.OUT / f"chunk21_rc2_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
            try:
                resp = client.rate(req)
            except raas_mod.RaaSError as exc:
                m = re.search(r"Matrix: (\w+).*?Keys: ([^.]*)", str(exc.body)) or re.search(r'"Message":"([^"]{0,200})', str(exc.body))
                what = m.group(0)[:220] if m else str(exc.body)[:220]
                if cid in EXPECT_REFUSAL and EXPECT_REFUSAL[cid] in what:
                    print(f"  {cid} REFUSES AS EXPECTED (OI-103; ours rates): {what}")
                    continue
                print(f"  {cid} ISO REFUSES {what}")
                FAIL.append(f"{cid} live")
                continue
            (gc.OUT / f"chunk21_rc2_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
            pbad = []
            for rec in recs:
                want = [w for w in preds.get(cid, {}).get(rec, []) if not same(w, 0)]
                iso = [x for x in r2.iso_of(resp, rec) if not same(x, 0)]
                if sorted(Decimal(str(x)) for x in iso) != sorted(Decimal(str(w)) for w in want):
                    pbad.append((rec, iso, [str(w) for w in want]))
            data, ip = rep.cmp.rate(req)
            ipr, opr = rep.iso_prem(resp), rep.our_prem(data)
            d = [(k, v, opr.get(k)) for k, v in ipr.items() if not rep.cmp.same(v, opr.get(k))]
            mi, mo = cmp.iso_messages(resp), set(ip.messages)
            ok = not pbad and not d and mi == mo
            print(f"  {cid} {'AGREE' if ok else 'DIFFER'}: predicted {len(recs) - len(pbad)} of {len(recs)} records; "
                  f"{len(ipr) - len(d)} of {len(ipr)} premiums; messages {'equal' if mi == mo else 'DIFFER'}"
                  + "".join(f"\n        predicted {r16.short(r)[-50:]}: ISO {x}, derived {w}" for r, x, w in pbad[:6])
                  + "".join(f"\n        {k[-90:]} ISO {v} ours {o}" for k, v, o in d[:5])
                  + (f"\n        ISO only {sorted(mi - mo)[:3]}\n        ours only {sorted(mo - mi)[:3]}" if mi != mo else ""))
            if not ok and cid in KNOWN_DIFF:
                print(f"        KNOWN DIFFERENCE ({KNOWN_DIFF[cid]})")
            elif not ok:
                FAIL.append(f"{cid} live")
    m, s = divmod(int(time.monotonic() - T0), 60)
    print(f"\nRC-2 (C21-06..C21-09): {'ALL AGREE' if not FAIL else 'FAILED: ' + ', '.join(FAIL)}  ({m}m{s:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
