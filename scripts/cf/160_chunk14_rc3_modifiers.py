"""Chunk 14, RC-3 (C14-10 to C14-14): the policy-wide modifiers, derived by hand first.

Every case is chunk 2's Oregon building (Group I final rate 0.261, Group II 0.032,
limit 100,000, cyber 0.995 on Group II: 261 + 32 = 293). The premium rule is
round0(IRPM x MPD x PackageMod x FinalRate x Limit/100) x cyber, so a modifier f
gives round0(261 f) + round0(round0(32 f) x 0.995).

C14-10  IRPM. Six category percentages ("-10%") go through IRPMConversion to
        integers, sum into TotalModificationPct, and IRPMFactor = round3(1 + t/100),
        capped at the countrywide +/-25 -- but only when IRPMFactor is blank: the
        rule is IsNull-guarded, so a supplied factor wins. The base policy supplies
        IRPMFactor 1.0, so every computed case removes it.
        I1 Management -8%, Location -2% (= -10)          -> 0.9  -> 235 + 29 = 264
        I2 six categories summing to +30                 -> 1.25 -> 326 + 40 = 366 + cap message
        I3 six categories summing to -30                 -> 0.75 -> 196 + 24 = 220 + cap message
        I4 IRPMApplies No, CPPIRPMFactor 0.85            -> 0.85 -> 222 + 27 = 249
        I5 IRPMApplies Yes, no categories                -> 1.0  -> 293
        I6 the same -10 but IRPMFactor 1.1 supplied      -> 1.1  -> 287 + 35 = 322
        STATES (in force at 2026-09-17; the building made portable as in 152_). The
        cap follows each state's IRPMMaximumDebit / Credit; the message is a separate
        rule each state may blank or rewrite -- the two need not agree:
        NY  +/-15 table; CW message blanked; own "cannot exceed 15%" message; and a
            second "total of all credits or debits cannot exceed 25%" that adds the
            IRPM PERCENT to the multi-premium FACTOR (~1.0) -- units mixed, so +25
            trips it where +25 alone would not.
            NY also rates on its OWN twelve categories (AccessToPropertyPct ...), not the
            six countrywide ones. (First prediction put +20 in ManagementPct; the engine
            read 1.0 -- right, NY never reads that field.)
            Y0 the CW six summing to +20 -> ignored, 1.0, silent (NY blanks their domains).
            Y1 six NY categories summing to +20 -> 1.15, 15% message.
            Y2 eight NY categories summing to +25 -> 1.15, 15% and all-credits messages.
        MO  credit -35 (debit CW 25); own message tests the state limits.
            O1 -30 -> 0.70, no message (a CW cap would give 0.75 + message).
            O2 -30 + expenses -10 = -40 -> 0.65, MO message.
            MO adds a seventh category, ReductionInExpensesPct, to the sum.
            O3 six at their limits (-30) + expenses -5% = -35 -> 0.65, silent (not BELOW -35);
               a six-category reading gives -30 -> 0.70.
            The seventh lookup has no blank guard: left blank, ISO REFUSES the policy
            (IRPMConversion, keys CW + ""), where our engine reads 0 and prices -- OI-103's
            shape. So O1 / O2 carry a filed "0%" for it, and O4 pins the refusal.
            O4 MO IRPM Yes, expenses blank -> ISO refuses; ours prices (OI-103, known).
        GA  CW +/-25 table but its own message says 15%.
            G1 +20 -> 1.20 AND the 15% message.
        VA  message blanked, no replacement.  V1 +30 -> 1.25, silent.
        NE  IRPM off: categories ignored, IRPMFactor 1.0 unless supplied, no form.
            N1 Yes, -10% -> 1.0.   N2 IRPMFactor 0.9 supplied -> 0.9.
C14-11  PACKAGE MODIFICATION: the policy's factor reaches the building only when
        the building's own is blank.
        P1 policy 0.8, building blank                    -> 209 + 26 = 235
        P2 policy 0.8, building 1.0                      -> 293
C14-12  MULTI-PREMIUM AND DISPERSION CREDIT, from the policy's User field.
        M1 MultiPremiumAndDispersionCreditFactorUser 0.9, building blank -> 235 + 29 = 264
C14-13  STANDARD PROPERTY POLICY: CW 0.98 on Group I and Group II, multiplied in at
        the cause-of-loss step (not on the premium), so it rounds with the chain:
        I  0.239 x .98 = 0.234; r3(.234 x .95) = 0.222; r3(.222 x 1.172) = 0.260; x .98 = 0.255 -> 255
        II 0.027 x .98 = 0.026; r3(.026 x .95) = 0.025; r3(.025 x 1.266) = 0.032; x .98 = 0.031
           -> round0(31 x 0.995) = 31
        S1 PolicyType "Standard Property Policy"          -> 255 + 31 = 286
        S2 chunk 7's five-coverage policy as a Standard Property Policy: ISO's
           eligibility rules say "Business Income coverage is not available with the
           Standard Property Policy" (a message, not a refusal). Premiums are not
           hand-derived here (S1 derived the 0.98 chain); ISO checks all of them.
C14-14  MULTI-LOCATION AVERAGE RATES: with no value reporting form the field defaults
        to "Not Used" and nothing prices off it.
        L1 base policy                                   -> MultiLocAvgRates "Not Used", 293

    python scripts/cf/160_chunk14_rc3_modifiers.py [--live]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))
sys.path.insert(0, str(ROOT / "scripts"))

from gl_engine.interp.values import InterpretError
import _iso_refusals as _iso                                    # noqa: E402

gc = import_module("149_chunk13_golden_case")
rep = import_module("157_chunk14_c14-02_total_replay")
t2 = import_module("159_chunk14_rc2_total")
r11 = gc.r11
r11.NUMERIC |= {"CPPIRPMFactor", "IRPMFactor", "PackageModFactor", "MultiPremiumAndDispersionCreditFactorUser"}
POL, STRUCT = gc.POL, gc.STRUCT
TOTAL = f"{POL}/ErcCalculatedTotalPremium"
B1, B2 = t2.B1, t2.B2
IRPMF = f"{POL}/IRPMFactor"
TMP = f"{POL}/CommercialPropertyIRPMTable/CommercialPropertyIRPM/TotalModificationPct"
MLA = f"{POL}/MultiLocAvgRates"
CW_MSG = "The total Individual Risk Premium Modification credits or debits cannot exceed 25%"
M15 = "The total Individual Risk Premium Modification credits or debits cannot exceed 15%"
ALL25 = "The total of all credits or debits cannot exceed 25%"
MO_MSG = "The total Individual Risk Premium Modification cannot exceed credits of 35% or debits of 25%"


BI_SPP = "Business Income coverage is not available with the Standard Property Policy"


def irpm_msgs(msgs):
    """The messages RC-3 owns: IRPM limits and Standard Property Policy eligibility."""
    return {m for m in msgs if "Risk Premium Modification" in m or "credits or debits" in m
            or "Standard Property Policy" in m}
#: Every percentage below is ON its category's domain (Domain Tables, 2026-09-24): CW
#: Management +/-8, Location +/-7, Building Features +/-5, Premises & Equipment +/-5,
#: Employees +/-3, Protection +/-2 (at their limits the six sum to exactly +/-30); NY's
#: twelve, in NY_CATS order, +/-4 4 4 3 3 3 2 2 2 1 1 1 (also 30); MO's expense
#: reduction 0% to -10%. (A first version used off-domain values -- "5%" on Employees and
#: Protection, "20%" on one category. ISO rated them, and only the sum matters because
#: IRPMConversion is one-to-one, but a probe should use inputs a user can enter.)
NY_CATS = ("AccessToPropertyPct", "EliminationOfHazardsPct", "SafeguardingPropertyPct", "DesignOfPremisesPct",
           "StructuralFeaturesPct", "SurroundingPremisesPct", "ConditionOfFixturesPct", "ConditionOfPremisesPct",
           "EmployeeSelectionPct", "IdentificationAndIsolationHazardsPct", "TrainingAndSupervisionPct",
           "WindstormLossPreventionPct")
P30 = ["8%", "7%", "5%", "5%", "3%", "2%"]                 # CW six at their limits: +30
N30 = ["-" + x for x in P30]                               # -30
N10 = ["-8%", "-2%"]                                       # -10
P20 = ["8%", "7%", "5%"]                                   # +20
NY20 = ["4%", "4%", "4%", "3%", "3%", "2%"]
NY25 = ["4%", "4%", "4%", "3%", "3%", "3%", "2%", "2%"]
NY30 = ["4%", "4%", "4%", "3%", "3%", "3%", "2%", "2%", "2%", "1%", "1%", "1%"]
REFUSES = {"O4"}      # ISO refuses by design; our engine prices (OI-103)
CATS = ("ManagementPct", "LocationPct", "BuildingFeaturesPct", "PremisesEquipmentPct", "EmployeesPct", "ProtectionPct")
MO_CATS = CATS + ("ReductionInExpensesPct",)


def pol(sub):
    return sub["CommercialPropertyTable"]["CommercialProperty"][0]


def bldg(sub):
    return t2.structs(t2.locs(sub)[0])[0]


def portable(juris):
    """Chunk 2's building in another state: Oregon's territories removed, the Group I
    territory factor pinned to 1.0 (152_'s approach, OI-103 shape)."""
    sub = t2.base()
    cp = pol(sub)
    cp["State"] = juris
    loc = t2.locs(sub)[0]
    loc.pop("BasicGroupIRatingTerr", None)
    loc.pop("BasicGroupIIRatingTerr", None)
    loc["BasicGroupIRatingTerrFactor"] = "1.0"
    return sub


def irpm(pcts, supplied=None, juris=None, cats=CATS):
    def build():
        sub = portable(juris) if juris else t2.base()
        cp = pol(sub)
        cp.pop("IRPMFactor", None)
        cp["IRPMApplies"] = "Yes"
        if supplied is not None:
            cp["IRPMFactor"] = supplied
        if pcts:
            cp["CommercialPropertyIRPMTable"] = {"CommercialPropertyIRPM": [{k: v for k, v in zip(cats, pcts) if v}]}
        return sub
    return build


def cpp():
    sub = t2.base()
    cp = pol(sub)
    cp.pop("IRPMFactor", None)
    cp.update({"IRPMApplies": "No", "CPPIRPMFactor": "0.85"})
    return sub


def pkg(building):
    def build():
        sub = t2.base()
        pol(sub)["PackageModFactor"] = "0.8"
        if building is None:
            bldg(sub).pop("PackageModFactor", None)
        else:
            bldg(sub)["PackageModFactor"] = building
        return sub
    return build


def mpd():
    sub = t2.base()
    pol(sub)["MultiPremiumAndDispersionCreditFactorUser"] = "0.9"
    bldg(sub).pop("MultiPremiumAndDispersionCreditFactor", None)
    return sub


def spp(sub=None):
    sub = sub or t2.base()
    pol(sub)["PolicyType"] = "Standard Property Policy"
    return sub


def spp_five():
    sub = spp(r11.at_date(t2.grp.five()))
    for loc in t2.locs(sub):
        for st in t2.structs(loc):
            st.setdefault("WindstormOrHailDeductible", "1,000")    # ISO refuses it blank (C13-08)
    return sub


CASES = {
    "I1": ("C14-10 IRPM -10 (Management -8, Location -2)", irpm(N10), {IRPMF: 0.9, TMP: -10, B1: 235, B2: 29, TOTAL: 264}, set()),
    "I2": ("C14-10 IRPM +30 capped at 1.25", irpm(P30), {IRPMF: 1.25, TMP: 30, B1: 326, B2: 40, TOTAL: 366}, {CW_MSG}),
    "I3": ("C14-10 IRPM -30 capped at 0.75", irpm(N30), {IRPMF: 0.75, TMP: -30, B1: 196, B2: 24, TOTAL: 220}, {CW_MSG}),
    "I4": ("C14-10 IRPM No, CPPIRPMFactor 0.85", cpp, {B1: 222, B2: 27, TOTAL: 249}, set()),
    "I5": ("C14-10 IRPM Yes, no categories", irpm([]), {B1: 261, B2: 32, TOTAL: 293}, set()),
    "I6": ("C14-10 IRPM -10 but IRPMFactor 1.1 supplied", irpm(N10, "1.1"), {IRPMF: 1.1, B1: 287, B2: 35, TOTAL: 322}, set()),
    "P1": ("C14-11 package mod 0.8, building blank", pkg(None), {B1: 209, B2: 26, TOTAL: 235}, set()),
    "P2": ("C14-11 package mod 0.8, building 1.0 wins", pkg("1.0"), {B1: 261, B2: 32, TOTAL: 293}, set()),
    "M1": ("C14-12 multi-premium credit 0.9", mpd, {B1: 235, B2: 29, TOTAL: 264}, set()),
    "S1": ("C14-13 Standard Property Policy 0.98 / 0.98", spp, {B1: 255, B2: 31, TOTAL: 286}, set()),
    "S2": ("C14-13 Standard Property Policy with Business Income", spp_five,
           {POL + "/PolicyType": "Standard Property Policy"}, {BI_SPP}),
    "L1": ("C14-14 multi-location average rates default", t2.base, {MLA: "Not Used", B1: 261, TOTAL: 293}, set()),
    "Y0": ("C14-10 NY ignores the CW categories", irpm(P20, juris="NY"), {IRPMF: 1.0, TMP: 0}, set()),
    "Y1": ("C14-10 NY +20 -> 1.15", irpm(NY20, juris="NY", cats=NY_CATS), {IRPMF: 1.15, TMP: 20}, {M15}),
    "Y2": ("C14-10 NY +25 -> 1.15, all-credits message", irpm(NY25, juris="NY", cats=NY_CATS),
           {IRPMF: 1.15, TMP: 25}, {M15, ALL25}),
    "O1": ("C14-10 MO -30 -> 0.70, silent", irpm(N30 + ["0%"], juris="MO", cats=MO_CATS), {IRPMF: 0.7, TMP: -30}, set()),
    "O2": ("C14-10 MO -40 -> 0.65", irpm(N30 + ["-10%"], juris="MO", cats=MO_CATS), {IRPMF: 0.65, TMP: -40}, {MO_MSG}),
    "O3": ("C14-10 MO seventh category, -35 -> 0.65 silent", irpm(N30 + ["-5%"], juris="MO", cats=MO_CATS),
           {IRPMF: 0.65, TMP: -35}, set()),
    "O4": ("C14-10 MO expenses blank: ISO refuses (OI-103)", irpm(N10, juris="MO"), {IRPMF: 0.9, TMP: -10}, set()),
    "G1": ("C14-10 GA +20 -> 1.20 with a 15% message", irpm(P20, juris="GA"), {IRPMF: 1.2, TMP: 20}, {M15}),
    "V1": ("C14-10 VA +30 -> 1.25, silent", irpm(P30, juris="VA"), {IRPMF: 1.25, TMP: 30}, set()),
    "N1": ("C14-10 NE IRPM off: -10% ignored", irpm(N10, juris="NE"), {IRPMF: 1.0}, set()),
    "N2": ("C14-10 NE supplied 0.9", irpm(N10, "0.9", juris="NE"), {IRPMF: 0.9}, set()),
}
JURIS = {"Y": "NY", "O": "MO", "G": "GA", "V": "VA", "N": "NE"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    a = ap.parse_args()
    fails = []
    for cid, (label, build, want, msgs) in CASES.items():
        try:
            data, ip = gc.run(build(), juris=JURIS.get(cid[0], "OR"))
        except InterpretError as exc:
            if _iso.refused_as_iso(__file__, cid, exc):          # C28-05: ours refuses where ISO does
                continue
            print(f"{cid}  {label}: RAISED {exc}")
            fails.append(cid)
            continue
        bad = []
        for k, v in want.items():
            got = gc.read(k, data)
            ok = got == v if isinstance(v, str) else gc.num_eq(got if got is not None else 0, v)
            if not ok:
                bad.append((k, got, v))
        got_m = irpm_msgs(ip.messages)
        if got_m != msgs:
            bad.append(("IRPM messages", sorted(got_m), sorted(msgs)))
        n = len(want) + 1
        print(f"{cid}  {label}: {n - len(bad)} of {n}"
              + "".join(f"\n      {k.rsplit('/', 1)[-1]} got {g} want {v}   << expected" for k, g, v in bad))
        if bad:
            fails.append(cid)
    print(f"\nengine: {len(CASES) - len(fails)} of {len(CASES)} as derived")
    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
        agree = 0
        print("\nISO live at 2026-09-17 (every Premium and ErcCalculatedTotalPremium, by path):")
        for cid, (label, build, want, msgs) in CASES.items():
            req = r11.payload(build())
            j = JURIS.get(cid[0], "OR")        # r11.payload always writes Oregon; retarget (152_'s way)
            for cp in req["body"]["CommercialProperty"]:
                cp["State"] = j
            req["body"]["SchemeKeys"]["ProductName"] = r11.PRODUCT.format(state=j)
            (gc.OUT / f"chunk14_rc3_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
            try:
                resp = client.rate(req)
            except raas_mod.RaaSError as exc:
                m = re.search(r"Matrix: (\w+).*?Keys: ([^.]*)", str(exc.body)) or re.search(r'"Message":"([^"]{0,160})', str(exc.body))
                print(f"  {cid}  ISO REFUSES {m.group(0) if m else str(exc.body)[:160]}"
                      + ("   (as pinned: OI-103)" if cid in REFUSES else ""))
                agree += cid in REFUSES
                continue
            if cid in REFUSES:
                print(f"  {cid}  ISO RATED -- expected a refusal (OI-103); re-read the item")
                continue
            (gc.OUT / f"chunk14_rc3_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
            data, ip = rep.cmp.rate(req)
            iso, ours = rep.iso_prem(resp), rep.our_prem(data)
            d = [(k, v, ours.get(k)) for k, v in iso.items() if not rep.cmp.same(v, ours.get(k))]
            iso_m, our_m = irpm_msgs(rep.cmp.iso_messages(resp)), irpm_msgs(ip.messages)
            if iso_m != our_m or iso_m != msgs:
                d.append(("IRPM messages (derived " + str(sorted(msgs)) + ")", sorted(iso_m), sorted(our_m)))
            tot = iso.get("CommercialProperty[0]/ErcCalculatedTotalPremium")
            agree += not d
            print(f"  {cid}  {'AGREE ' if not d else 'DIFFER'}  ISO total {tot}  ({len(iso)} premiums compared, IRPM messages {len(iso_m)})"
                  + "".join(f"\n        {str(k)[-80:]} ISO {v} ours {o}" for k, v, o in d[:4]))
        print(f"\n  live: {agree} of {len(CASES)} agree field for field")
        if agree != len(CASES):
            fails.append("live")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
