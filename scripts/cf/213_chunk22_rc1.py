#!/usr/bin/env python3
"""Chunk 22, RC-1: evidence and plumbing for the multi-location forms, before any golden case. No ISO calls.

Every check runs on a real TWO-location Oregon tree (175_'s policy, the location copied, the second
location's contents limit raised so the two contents rows rate differently). A write tracer records every
write of the multi-location fields with the rule that made it, so "who writes what, in what order" is read
off the engine, not argued from the XML.

C22-02  WHO WRITES THE MLARs, IN WHAT ORDER. Value Reporting (CP 13 10) "Not Used" and "Used", Additional
        Locations (CP 13 20), and both forms together with the mutual-exclusion message ignored. Which value
        each reader sees; whether a submitted MLAR survives each writer.
C22-03  THE BUILT TOUCHPOINTS. SetMultipleLocationsAvgRate (the "Not Used" default, the copy, the blank-only
        guard), Personal Property's indicator (and its 9 state rewrites), the Additional Locations roll-up
        (what it sums, and who reads the result), the 293 stored policies (engine unchanged since the chunk 21
        gate, so the 2026-09-30 293 of 293 carries).
C22-04  ATTACH MAP AND SWITCHES. Which coinsurance values keep the Value Reporting Form, which records are
        auto-created, which switch the ordinary contents premium off; the three rate sources per Value
        Reporting coverage; blank-input zeros.
C22-05  VALUE REPORTING GENERAL INFORMATION BY HAND (the "Not Used" path: incidental and acquired locations);
        the MLAR arithmetic by hand under BOTH readings of the running-maximum rule (see E-1 below).
C22-06  TABLES AND LITERALS. Every lookup in the chunk's files against every in-force package, the
        MultiLocAvgRates and reporting-coinsurance domains, the two header-only sibling tables, form labels.

E-1 (found here). `SetMaxPrsnlPropLimitForMLARCalc` reads its own parameter `maxLimit` inside the binding
that defines it (a running maximum written as a self-reference). Our engine refuses ("parameter 'maxLimit'
is not bound here"), so **every Value Reporting policy with average rates "Used" raises in our engine**.
**ISO refuses the same way** (214_oi119_probe.py --live, 2026-10-01: "No value found in Params (FromParam=maxLimit)"),
so the engine agrees and no change is made. Where this script needs the "Used" path it runs it under a
labelled, scoped hypothesis (the unbound read as blank), recording the arithmetic in case ISO corrects the rule.

    python scripts/cf/213_chunk22_rc1.py

Progress streams as [m:ss] lines. Exits 1 on any check that fails.
"""
from __future__ import annotations

import contextlib
import copy
import csv
import re
import subprocess
import sys
import time
from decimal import ROUND_HALF_UP, Decimal
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))
sys.stdout.reconfigure(line_buffering=True)
T0 = time.monotonic()

import gl_engine.interp.interpreter as I                                  # noqa: E402
import gl_engine.interp.tree as tree                                      # noqa: E402
from cf_engine.resolve import book_for                                    # noqa: E402

rc1 = import_module("168_chunk15_rc1")
r2 = import_module("175_chunk16_rc2")
g19 = import_module("192_chunk19_rc2")
gc = import_module("149_chunk13_golden_case")
r4 = import_module("177_chunk16_rc4")
s18 = import_module("164_chunk14_c14-18_all_states")
ASOF = "20260917"
P = "CommercialProperty"
AL = "AdditionalLocationsSpecialCoinsurance"
VR = "ValueReportingForm"
CW = book_for("OR", ASOF).parent.package.content
ERC = Path(r"F:\ISO_ERC_Files\CF")
FAIL = []
GROUPS = ("BasicGroupI", "BasicGroupII", "Broad", "Special", "EQ")
MLARS = tuple(g + "MLAR" for g in GROUPS)
# xs:int / xs:decimal input fields on the chunk 22 records (MasterCFCW.DataDef.xsd): ISO refuses them as strings
r2.r11.NUMERIC |= {"AvgVal", "EstdAvgVal", "SpecificIns", "AvgValIncldgValOfAlcoholicBeverageTaxes",
                   "EstdAvgValIncldgValOfAlcoholicBeverageTaxes", "YourBusnPrsnlPropInc", "StockOnlyInc", "PrsnlPropOthersInc",
                   "YourBusnPrsnlPropAcqrd", "StockOnlyAcqrd", "PrsnlPropOthersAcqrd", "OverallLimit", "FullValue", "AverageLimit"}
REPORTING = ("Daily Reporting", "Weekly Reporting", "Monthly Reporting", "Quarterly Reporting", "Policy Year Reporting")


def progress(what):
    m, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{m}m{s:02d}s] {what}")


def check(ok, msg):
    print(f"    [{'ok' if ok else 'FAIL'}] {msg}")
    if not ok:
        FAIL.append(msg)


def r(x, dp):
    return Decimal(str(x)).quantize(Decimal(1).scaleb(-dp), rounding=ROUND_HALF_UP)


def short(tag):
    return tag.replace(P, "").replace(AL, "AL").replace(VR, "VRF") or "policy"


# ------------------------------------------------------------------ trees, tracer, hypothesis

def contents(loc):
    return loc[P + "StructureTable"][P + "Structure"][0][P + "OccupClassTable"][P + "OccupClass"][0][
        P + "PersonalPropertyTable"][P + "PersonalProperty"][0]


def locations(sub):
    return sub[P + "Table"][P][0][P + "LocationTable"][P + "Location"]


VR_GI = {"CauseOfLoss": "Special", "EQCauseOfLoss": "No", "YourBusnPrsnlPropInc": "10000", "StockOnlyInc": "0",
         "PrsnlPropOthersInc": "0", "YourBusnPrsnlPropAcqrd": "0", "StockOnlyAcqrd": "0", "PrsnlPropOthersAcqrd": "0"}
AL_GI = {"CauseOfLoss": "Special", "Coinsurance": "90%", "YourBusnPrsnlPropInc": "10000", "StockOnlyInc": "0",
         "PrsnlPropOthersInc": "0", "OverallLimit": "300000"}


def two_locations(vr=None, al=False, limit2="500000", vrf=None, gi=None, coins="Monthly Reporting", full=("200000", "100000")):
    """175_'s Oregon policy at Special, a second location copied from the first, its contents limit raised.
    vr: None, or the General Information's MultiLocAvgRates ("Used" / "Not Used" / "" for blank)."""
    sub = g19.with_cause(g19.portable("OR"), "Special")
    pp = rc1.node_dicts(sub)[P + "PersonalProperty"]
    if vr is not None:
        pp["Coinsurance"] = coins
        r2.put(sub, VR + "GeneralInformation", dict(VR_GI, MultiLocAvgRates=vr, **(gi or {})))
        r2.put(sub, VR, dict({"AvgVal": "40000", "SpecificIns": "0", "SeasonalRisk": "No"}, **(vrf or {})))
    if al:
        r2.put(sub, AL + "GeneralInformation", dict(AL_GI))
        r2.put(sub, AL + "Provisions", {"FullValue": full[0]})
    ls = locations(sub)
    ls.append(copy.deepcopy(ls[0]))
    ls[1]["LocationNumber"] = "2"
    pp2 = contents(ls[1])
    pp2["Limit"] = limit2
    if al:
        pp2[P + AL + "ProvisionsTable"][P + AL + "Provisions"][0]["FullValue"] = full[1]
        for pp_ in (contents(ls[0]), pp2):                       # Full Value must not be below the Limit
            pp_["FullPrsnlPropValue"] = pp_[P + AL + "ProvisionsTable"][P + AL + "Provisions"][0]["FullValue"]
    return sub


WATCH = re.compile(r"MLAR|MultiLocAvgRates|TotalValueForMLARCalc|MaxPrsnlPropLimit|TotalFullValue|FinalBasicGroupIRate$|"
                   r"RateTimesValue|PrsnlPropPremium|^Premium$|LimitToUse$")


@contextlib.contextmanager
def tracer():
    """records (rule, node tag, field, value) for every write of a watched field, in order."""
    log, stack = [], []
    w0, c0 = tree.write, I.Interpreter.call

    def w(path, ctx, value):
        n = w0(path, ctx, value)
        if WATCH.search(path):
            log.append((stack[-1] if stack else "?", ctx.tag, path, None if value is None else str(value)))
        return n

    def call(self, file_name, rule_name, *a, **k):
        stack.append(f"{short(file_name.replace('Rules', ''))}.{rule_name}")
        try:
            return c0(self, file_name, rule_name, *a, **k)
        finally:
            stack.pop()
    tree.write, I.Interpreter.call = w, call
    try:
        yield log
    finally:
        tree.write, I.Interpreter.call = w0, c0


@contextlib.contextmanager
def hypothesis_blank_maxlimit():
    """E-1 HYPOTHESIS, scoped: an unbound `maxLimit` reads as blank. Not the engine's behaviour."""
    hp, pm = I.Frame.has_param, I.Frame.param
    I.Frame.has_param = lambda self, n: True if n == "maxLimit" else hp(self, n)
    I.Frame.param = lambda self, n: self.params.get(n) if n == "maxLimit" else pm(self, n)
    try:
        yield
    finally:
        I.Frame.has_param, I.Frame.param = hp, pm


def rated(sub, j="OR"):
    try:
        data, ip = gc.run(sub, j)
        return data, ip, None
    except Exception as exc:
        return None, None, f"{type(exc).__name__}: {str(exc)[:160]}"


def nodes(data, rec):
    return rc1.find(data, P + rec)


def txt(n, f):
    c = n.first(f)
    return None if c is None else c.text


def num(n, f, default="0"):
    v = txt(n, f)
    return Decimal(v if v not in (None, "") else default)


def premiums(data, rec):
    return [txt(n, "Premium") for n in nodes(data, rec)]


def first_index(log, rule_part, field):
    for i, (rule, tag, path, v) in enumerate(log):
        if rule_part in rule and path.endswith(field):
            return i
    return None


# ------------------------------------------------------------------ C22-02

def who_writes():
    progress("C22-02  WHO WRITES THE MLARs, IN WHAT ORDER")
    print("\n" + "=" * 90 + "\nC22-02  WHO WRITES THE MLARs, IN WHAT ORDER (two locations, contents 100,000 / 500,000)\n" + "-" * 90)

    # (a) Value Reporting, "Not Used"
    with tracer() as log:
        data, ip, err = rated(two_locations(vr="Not Used"))
    check(err is None, f"VR 'Not Used' rates ({err})")
    gi = nodes(data, VR + "GeneralInformation")[0]
    vrfs = nodes(data, VR)
    print(f"  (a) VR 'Not Used': GI MLARs {[txt(gi, f) for f in MLARS]}; MLARLimit {txt(gi, 'MLARLimit')}")
    check(all(num(gi, f) == 0 for f in MLARS) and all(num(v, f) == 0 for v in vrfs for f in MLARS),
          "'Not Used': every MLAR on the GI and on both Value Reporting Form rows is 0")

    # (b) Value Reporting, "Used": the engine refuses (E-1)
    data, ip, err = rated(two_locations(vr="Used"))
    print(f"  (b) VR 'Used', engine as built: {err}")
    check(err is not None and "maxLimit" in err, "E-1: 'Used' raises in our engine at the running-maximum rule (maxLimit unbound)")

    # (b') the same under the labelled hypothesis
    with hypothesis_blank_maxlimit(), tracer() as log:
        data, ip, err = rated(two_locations(vr="Used"))
    check(err is None, f"HYPOTHESIS (unbound maxLimit = blank): 'Used' rates ({err})")
    gi = nodes(data, VR + "GeneralInformation")[0]
    vrfs = nodes(data, VR)
    print("  (b') HYPOTHESIS run, the order of the first write of each field:")
    order = [("PersonalProperty.SetMultiLocAvgRatesIndicator", "MultiLocAvgRatesIndicator"),
             (".SetMultipleLocationsAvgRate", "MultiLocAvgRates"),
             ("GeneralInformation.SetMLARLimit", "MLARLimit"),
             ("PersonalProperty.SetFinalBasicGroupIRate", "FinalBasicGroupIRate"),
             ("GeneralInformation.SetBasicGroupIMLAR", "BasicGroupIMLAR"),
             ("VRF.SetBasicGroupIMLAR", "BasicGroupIMLAR"),
             ("VRFBasicGroupICoverage.SetPremium", "Premium")]
    idx = [first_index(log, a, b) for a, b in order]
    for (a, b), i in zip(order, idx):
        print(f"      #{i!s:>5}  {a:55s} {b}")
    check(None not in idx and idx == sorted(idx),
          "order: PP indicator (InitializeChildRisks) < policy MultiLocAvgRates < GI MLARLimit < contents final "
          "rates < GI MLARs < each VR Form row's MLARs < the VR premiums")
    same = all(txt(v, f) is not None and num(v, f) == num(gi, f) for v in vrfs for f in MLARS)
    print(f"      GI MLARs {[txt(gi, f) for f in MLARS]}; VR Form rows {[[txt(v, f) for f in MLARS] for v in vrfs]}")
    check(len(vrfs) == 2 and same, "each VR Form row copies GeneralInformation[1]'s five MLARs (one value per policy, not per location)")
    mx = txt(gi, "MaxPrsnlPropLimitForMLARCalc")
    print(f"      MaxPrsnlPropLimitForMLARCalc = {mx} (first contents row 100,000 / 100 = 1000; a running maximum would give 5000)")
    check(mx == "1000", "HYPOTHESIS: the 'max' rule returns the FIRST row's limit / 100 (1000), not the largest (5000): "
                        "the two readings differ by 4,000 in MLARLimit, so ISO can decide (RC-2)")

    # submitted MLARs: who keeps them
    print("  submitted values (HYPOTHESIS run for the 'Used' path):")
    with hypothesis_blank_maxlimit():
        base = num(nodes(rated(two_locations(vr="Used"))[0], VR + "GeneralInformation")[0], "BasicGroupIMLAR")
        d1 = rated(two_locations(vr="Used", vrf={"BasicGroupIMLAR": "0.5"}))[0]
        d2 = rated(two_locations(vr="Used", gi={"BasicGroupIMLAR": "0.5"}))[0]
        d3 = rated(two_locations(vr="Used", gi={"FinalBasicGroupIRateTimesValue": "500"}))[0]
    v1 = [num(v, "BasicGroupIMLAR") for v in nodes(d1, VR)]
    g2 = num(nodes(d2, VR + "GeneralInformation")[0], "BasicGroupIMLAR")
    g3 = num(nodes(d3, VR + "GeneralInformation")[0], "BasicGroupIMLAR")
    print(f"      VR Form row MLAR 0.5 submitted -> {v1}; GI MLAR 0.5 submitted -> {g2}; GI rate x value 500 submitted -> MLAR {g3}")
    check(all(x == base for x in v1), "a submitted VR Form MLAR is overwritten (SetBasicGroupIMLAR has no IsNull guard)")
    check(g2 == base, "a submitted GI MLAR is overwritten too (no guard)")
    check(g3 == r(Decimal(500) / num(nodes(d3, VR + "GeneralInformation")[0], "MLARLimit"), 3) and g3 != base,
          "a submitted GI FinalBasicGroupIRateTimesValue survives (IsNull guard) and moves the MLAR: the one override point")

    # (c) Additional Locations
    with tracer() as log:
        data, ip, err = rated(two_locations(al=True))
    check(err is None, f"Additional Locations rates ({err})")
    runs = sum(1 for rule, tag, path, v in log if rule.endswith("ALGeneralInformation.SetBasicGroupIMLAR"))
    vals = {v for rule, tag, path, v in log if rule.endswith("ALGeneralInformation.SetBasicGroupIMLAR")}
    print(f"  (c) Additional Locations: the GI's MLAR rules ran {runs} times (main ruleset + once per contents row "
          f"carrying Provisions, via PP.SetResetPrsnlPropPremiumALSCP); values {sorted(vals)}")
    check(runs == 3 and len(vals) == 1, "the AL General Information runs 1 + 2 times and writes the same MLARs each time "
                                        "(its rate x value totals are IsNull-guarded after the first run)")
    algi = nodes(data, AL + "GeneralInformation")[0]
    for k, pp in enumerate(nodes(data, "PersonalProperty")):
        prov = pp.first(P + AL + "ProvisionsTable").first(P + AL + "Provisions")
        cov = prov.first(P + AL + "ProvisionsBasicGroupICoverage")
        lim = num(cov, "LimitToUse")
        f = [num(algi, "BasicGroupIMLAR"), num(algi, "CoinsuranceFactor")]
        cp = rc1.find(data, P)[0]
        x = r(lim / 100 * f[0] * f[1], 0)
        for fac in (num(cp, "PackageModFactor"), num(pp, "MultiPremiumAndDispersionCreditFactor"), num(cp, "IRPMFactor"),
                    num(cp, "CyberIncidentExclusionFactorBGI"), num(cp, "CyberIncidentExclusionCOLExcptnsFactorBGI")):
            x = r(x * fac, 0)
        print(f"      contents row {k + 1}: Provisions BGI LimitToUse {lim}  hand {x}  engine {txt(cov, 'Premium')}")
        check(Decimal(txt(cov, "Premium")) == x, f"row {k + 1}: Provisions Group I reads the AL GI's MLAR and coinsurance "
                                                 f"factor (not its own record's); hand = engine")

    # (d) both forms, message ignored
    with hypothesis_blank_maxlimit():
        data, ip, err = rated(two_locations(vr="Used", al=True))
    check(err is None, f"HYPOTHESIS: both forms on one policy rate ({err})")
    vgi, agi = nodes(data, VR + "GeneralInformation")[0], nodes(data, AL + "GeneralInformation")[0]
    msgs = list(getattr(ip, "messages", []))
    print(f"  (d) both forms: VR GI BGI MLAR {txt(vgi, 'BasicGroupIMLAR')}, AL GI BGI MLAR {txt(agi, 'BasicGroupIMLAR')}")
    check(txt(vgi, "BasicGroupIMLAR") != txt(agi, "BasicGroupIMLAR"),
          "the two General Information records hold their own MLARs (different nodes); neither overwrites the other")
    check(any("CP 13 10 and CP 13 20 are not valid together" in m for m in msgs), "the mutual-exclusion message fires")
    vrb = [txt(n, "Premium") for n in nodes(data, VR + "BasicGroupICoverage")]
    print(f"      VR Group I premiums {vrb}; Provisions Group I {premiums(data, AL + 'ProvisionsBasicGroupICoverage')}; "
          f"ordinary contents Group I {premiums(data, 'PersonalPropertyPrsnlPropBasicGroupICoverage')}")
    check(all(p not in (None, "0") for p in vrb) and all(p not in (None, "0") for p in premiums(data, AL + "ProvisionsBasicGroupICoverage")),
          "if the message is ignored, BOTH forms price on each contents row (a double charge ISO's message is there to stop)")


# ------------------------------------------------------------------ C22-03

def rule_text(content, file, rule):
    f = content / "Rules" / f"{file}.Rule.xml"
    if not f.exists():
        return None
    m = re.search(rf'<rul:Rule Name="{rule}".*?</rul:Rule>', f.read_text(encoding="utf-8-sig"), re.S)
    return None if m is None else re.sub(r"\s+", " ", re.sub(r'DataDefGroup="[^"]*"|MetadataCodes="[^"]*"', "", m.group(0)))


def touchpoints():
    progress("C22-03  THE BUILT TOUCHPOINTS")
    print("\n" + "=" * 90 + "\nC22-03  THE BUILT TOUCHPOINTS\n" + "-" * 90)
    pol = lambda d: txt(rc1.find(d, P)[0], "MultiLocAvgRates")                       # noqa: E731
    ind = lambda d: [txt(n, "MultiLocAvgRatesIndicator") for n in nodes(d, "PersonalProperty")]   # noqa: E731
    cases = []
    d = rated(two_locations())[0]
    cases.append(("no General Information", pol(d), ind(d), "Not Used", ["Not Used"] * 2))
    sub = two_locations()
    sub[P + "Table"][P][0]["MultiLocAvgRates"] = "Used"
    d = rated(sub)[0]
    cases.append(("no GI, policy 'Used' submitted", pol(d), ind(d), "Used", ["Not Used"] * 2))
    d = rated(two_locations(vr="Not Used"))[0]
    cases.append(("GI 'Not Used'", pol(d), ind(d), "Not Used", ["Not Used"] * 2))
    d = rated(two_locations(vr=""))[0]
    cases.append(("GI with MultiLocAvgRates blank", pol(d), ind(d), "", ["Not Used"] * 2))
    for label, p, i, wp, wi in cases:
        print(f"  {label:34s} policy MultiLocAvgRates {p!s:10s} contents indicator {i}")
        check(p == wp and i == wi, f"{label}: policy {wp}, contents {wi}")
    print("  -> the policy field and the contents indicator are set from the GI independently: a submitted policy value "
          "survives (blank-only guard) and diverges from the contents indicator, which the premiums read")

    # Personal Property's indicator rule: CW vs the 9 state rewrites
    cw = rule_text(CW, "CommercialPropertyPersonalPropertyRules", "SetMultiLocAvgRatesIndicator")
    diffs = []
    for j in ("AK", "AL", "AR", "CA", "DC", "FL", "GA", "NY", "RI"):
        st = book_for(j, ASOF).state.package.content
        t = rule_text(st, "CommercialPropertyPersonalPropertyRules", "SetMultiLocAvgRatesIndicator")
        diffs.append((j, "no own rule (CW applies)" if t is None else ("identical to CW" if t == cw else "DIFFERS")))
    print("  Personal Property's SetMultiLocAvgRatesIndicator in the 9 states that rewrite the file: " +
          ", ".join(f"{j} {s}" for j, s in diffs))
    check(all(s != "DIFFERS" for _, s in diffs), "no state rewrites the indicator rule itself (their rewrites are elsewhere in the file)")

    # the roll-up
    writers, readers = [], []
    for f in ERC.rglob("*.Rule.xml"):
        t = f.read_text(encoding="utf-8-sig", errors="ignore")
        for m in re.finditer(rf'<rul:Rule Name="([^"]+)"[^>]*DataDefGroup="{P}{AL}Provisions"[^>]*>(.*?)</rul:Rule>', t, re.S):
            if 'ToDataDef="Premium"' in m.group(2):
                writers.append((f.parent.parent.name, m.group(1)))
        if 'FromDataDef="PrsnlPropPremium"' in t or re.search(r'FromDataDef="[^"]*/PrsnlPropPremium"', t):
            readers.append(f.parent.parent.name)
    inforce = {"CFCW20260601V01", "CF CW 20230801 V02", "CF CW 20230801 V03", "CF CW 20230801 V04"}
    print(f"  roll-up: rules writing the Provisions record's own Premium, every package: {writers or 'none'}; "
          f"packages reading PrsnlPropPremium: {sorted(set(readers))}")
    check(not writers, "nothing writes the Provisions record's Premium (only its five children price), so the roll-up sums nothing")
    check(not (set(readers) & inforce), "no in-force edition reads PrsnlPropPremium (only 2023 V01, superseded): the roll-up "
                                       "moves no dollar under either reading (roll-up or reset); C22-12 reduces to one field check")
    d = rated(two_locations(al=True))[0]
    algi = nodes(d, AL + "GeneralInformation")[0]
    check(txt(algi, "PrsnlPropPremium") in ("0", "0.0"), f"engine: PrsnlPropPremium = {txt(algi, 'PrsnlPropPremium')} "
                                                       f"with two priced Provisions rows")

    # the stored policies
    # The engine's files changed since the chunk 21 gate (5a35c1f), against the WORKING TREE, each allowed only with the
    # replay that re-verified it. 2026-10-05: this guard read an empty diff as "unchanged" when git itself failed (the
    # repository's ownership check on a new PC), and had been failing since c7ffe66 unseen (the chunk 24-27 gates ran
    # the quick tier, which skips this script). Both fixed: a git error fails the check, and the changes are listed.
    REVERIFIED = {
        "gl_engine/interp/nodes.py": "c7ffe66, chunk 24 (Builders Risk); 157_ --all 293 of 293 at chunk 27, 2026-10-02",
        "gl_engine/interp/interpreter.py": "C28-05 strict SingleResult; 157_ --all 293 of 293, 2026-10-05",
        "cf_engine/resolve/book.py": "C28-05 strict default and EQ stub; 157_ --all 293 of 293, 2026-10-05",
        "cf_engine/config.py": "the corpus root's default moved to F: (new PC, 2026-10-05); no rating code",
        "gl_engine/config.py": "the corpus root's default moved to F: (new PC, 2026-10-05); no rating code",
    }
    git = subprocess.run(["git", "diff", "--name-only", "5a35c1f", "--", "cf_engine", "gl_engine"],
                         capture_output=True, text=True, cwd=ROOT)
    changed = set(git.stdout.split())
    unverified = sorted(changed - set(REVERIFIED))
    check(git.returncode == 0 and not unverified,
          f"engine changes since the chunk 21 gate (5a35c1f) each re-verified by the 293-policy replay (157_ --all, "
          f"293 of 293): {sorted(changed) or 'none'}; unverified {unverified or 'none'}"
          + (f"; git failed: {git.stderr.strip()[:120]}" if git.returncode else "")
          + "; every stored policy has no GI, so 'Not Used' as before")


# ------------------------------------------------------------------ C22-04

def attach_and_switches():
    progress("C22-04  ATTACH MAP AND SWITCHES")
    print("\n" + "=" * 90 + "\nC22-04  ATTACH MAP AND SWITCHES\n" + "-" * 90)
    for coins in REPORTING + ("90%", "80%"):
        d, ip, err = rated(two_locations(vr="Not Used", coins=coins))
        n_vrf, n_cov = len(nodes(d, VR)), len(nodes(d, VR + "SpecialCoverage"))
        ordinary = premiums(d, "PersonalPropertyPrsnlPropSpecialCoverage")
        print(f"  contents coinsurance {coins:22s} VR Form rows {n_vrf}  VR Special records {n_cov}  ordinary contents Special {ordinary}")
        if coins in REPORTING:
            check(n_vrf == 2 and n_cov == 2 and ordinary == ["0", "0"],
                  f"{coins}: the form stays, its five coverages are auto-created, the ordinary contents premium is switched off")
        else:
            check(n_vrf == 0 and all(p not in ("0", None) for p in ordinary),
                  f"{coins}: AttachFormValueReportingForm REMOVES the submitted form; the contents price as usual")
    d = rated(two_locations(al=True))[0]
    check(len(nodes(d, AL + "ProvisionsSpecialCoverage")) == 2 and len(nodes(d, AL + "GeneralInformationEarthquakeCoverage")) == 1
          and premiums(d, "PersonalPropertyPrsnlPropSpecialCoverage") == ["0", "0"],
          "Additional Locations: Provisions' five coverages and the GI's five (EQ re-appended) are auto-created; the "
          "ordinary contents premium is switched off (contents SetCoverageOnPolicyIndicator: 0 when either form exists)")

    # the three rate sources (Not Used + own rate is engine-checked here; blanket at C22-09; MLAR under E-1)
    d = rated(two_locations(vr="Not Used"))[0]
    cp = rc1.find(d, P)[0]
    print("  VR Group I, 'Not Used', not blanketed: own final rate x LimitToUse (= NewBusnFactor x SeasonalRiskFactor x Limit)")
    for k, pp in enumerate(nodes(d, "PersonalProperty")):
        vrf = pp.first(P + VR + "Table").first(P + VR)
        lim = r(num(vrf, "NewBusnFactor") * num(vrf, "SeasonalRiskFactor") * num(pp, "Limit"), 0)
        x = r(num(pp, "FinalBasicGroupIRate") * lim / 100, 0)
        for fac in (num(cp, "PackageModFactor"), num(pp, "MultiPremiumAndDispersionCreditFactor"), num(cp, "IRPMFactor"),
                    num(cp, "CyberIncidentExclusionFactorBGI"), num(cp, "CyberIncidentExclusionCOLExcptnsFactorBGI")):
            x = r(x * fac, 0)
        got = txt(vrf.first(P + VR + "BasicGroupICoverage"), "Premium")
        print(f"      row {k + 1}: rate {txt(pp, 'FinalBasicGroupIRate')}  NewBusn {txt(vrf, 'NewBusnFactor')}  "
              f"LimitToUse {txt(pp, 'LimitToUse')} (hand {lim})  hand {x}  engine {got}")
        check(Decimal(got) == x and num(pp, "LimitToUse") == lim, f"row {k + 1}: VR Group I at its own rate, hand = engine")
    print("  NewBusnFactor 0.75 applies whenever SeasonalRisk is not 'Yes' (the rule tests only SeasonalRisk, not new "
          "business): a non-seasonal reporting risk is priced on 75% of its limit")
    d = rated(two_locations(vr=""))[0]
    got = [txt(n, "Premium") for n in nodes(d, VR + "BasicGroupICoverage")]
    print(f"  GI MultiLocAvgRates blank: the contents indicator falls to 'Not Used', VR Group I {got}")
    check(all(p not in ("0", None) for p in got), "a blank GI value does NOT zero the VR premiums: they price at the own rate")
    sub = two_locations(vr="Not Used")
    for loc in locations(sub):
        contents(loc)["MultiLocAvgRatesIndicator"] = "Partly"
    d = rated(sub)[0]
    got = [txt(n, "Premium") for n in nodes(d, VR + "BasicGroupICoverage")]
    print(f"  blank-input zero: a submitted contents indicator outside the domain ('Partly'): VR Group I {got}")
    check(got == ["0", "0"], "a submitted non-domain indicator survives (IsNull guard), no SetPremium branch matches, Otherwise writes 0")


# ------------------------------------------------------------------ C22-05

def gi_by_hand():
    progress("C22-05  VALUE REPORTING GENERAL INFORMATION BY HAND")
    print("\n" + "=" * 90 + "\nC22-05  VALUE REPORTING GENERAL INFORMATION BY HAND\n" + "-" * 90)
    cases = (("Special, incidental 10,000, acquired 0", {}, "Special"),
             ("Broad, incidental 25,000, acquired 60,000", {"CauseOfLoss": "Broad", "YourBusnPrsnlPropInc": "25000",
                                                           "StockOnlyAcqrd": "60000"}, "Broad"),
             ("Special + EQ, incidental 7,500 + 2,500, acquired 50,000 (not > 50,000)",
              {"EQCauseOfLoss": "Yes", "YourBusnPrsnlPropInc": "7500", "PrsnlPropOthersInc": "2500", "StockOnlyAcqrd": "50000"}, "Special"),
             ("Basic, incidental 10,000, acquired 50,001", {"CauseOfLoss": "Basic", "StockOnlyAcqrd": "50001"}, "Basic"))
    rates = {row["CauseOfLoss"]: Decimal(row["Rate"]) for row in r4.rows("OR", "ValRptgIncLocsRate")}
    acq_rate = Decimal(r4.rows("OR", "ValRptgAcqrdLocsRate")[0]["Rate"])
    for label, gi, cause in cases:
        d, ip, err = rated(two_locations(vr="Not Used", gi=gi))
        if err:
            check(False, f"{label}: {err}")
            continue
        cp, g = rc1.find(d, P)[0], nodes(d, VR + "GeneralInformation")[0]
        lcm, pm, mp, irpm = (num(cp, f) for f in ("LossCostMultiplier", "PackageModFactor", "MultiPremiumAndDispersionCreditFactor", "IRPMFactor"))
        inc = sum(Decimal(dict(VR_GI, **gi)[k]) for k in ("YourBusnPrsnlPropInc", "StockOnlyInc", "PrsnlPropOthersInc"))
        acq = sum(Decimal(dict(VR_GI, **gi)[k]) for k in ("YourBusnPrsnlPropAcqrd", "StockOnlyAcqrd", "PrsnlPropOthersAcqrd"))

        def part(rate, grp, mods=True):
            x = r(r(rate * lcm, 3) * inc / 100, 0)
            if mods:
                x = r(r(r(x * pm, 0) * mp, 0) * irpm, 0)
            return r(r(x * num(cp, f"CyberIncidentExclusionFactor{grp}"), 0) * num(cp, f"CyberIncidentExclusionCOLExcptnsFactor{grp}"), 0)
        bgi = part(rates["Basic"], "BGI")
        broad = part(rates["Broad"], "Broad") if cause == "Broad" else 0
        spec = part(rates["Special"], "Special") if cause == "Special" else 0
        eq = part(rates["Earthquake"], "EQ", mods=False) if dict(VR_GI, **gi)["EQCauseOfLoss"] == "Yes" else 0
        acqp = r(r(r(r(r(acq_rate * lcm, 3) * acq / 100, 0) * pm, 0) * mp, 0) * irpm, 0) if acq > 50000 else 0
        hand = bgi + broad + spec + eq + acqp
        print(f"  {label}\n      hand: Group I {bgi} + Broad {broad} + Special {spec} + EQ {eq} + acquired {acqp} = {hand}; "
              f"engine IncLocs {txt(g, 'IncLocsPremium')} Acqrd {txt(g, 'AcqrdLocsPremium')} Premium {txt(g, 'Premium')}")
        check(num(g, "Premium") == hand, f"{label}: hand = engine")

    # the MLAR arithmetic, by hand under both readings of E-1 (engine only under the hypothesis)
    print("  MLAR arithmetic, 'Used', AvgVal 40,000 on both rows, contents 100,000 / 500,000:")
    with hypothesis_blank_maxlimit():
        d = rated(two_locations(vr="Used"))[0]
    g = nodes(d, VR + "GeneralInformation")[0]
    pps = nodes(d, "PersonalProperty")
    total_val = sum(min(Decimal(40000), num(pp, "Limit")) for pp in pps)
    tv = int(total_val / 100)
    times = sum(r(Decimal(40000) / 100 * num(pp, "FinalBasicGroupIRate"), 3) for pp in pps)
    for label, mx in (("first row (the hypothesis)", int(num(pps[0], "Limit") / 100)),
                      ("running maximum (the rule's name)", max(int(num(pp, "Limit") / 100) for pp in pps))):
        lim = mx if tv < mx else tv
        print(f"      {label:36s} TotalValueForMLARCalc {tv}  Max {mx}  MLARLimit {lim}  "
              f"Group I MLAR {times} / {lim} = {r(times / lim, 3)}")
    check(num(g, "TotalValueForMLARCalc") == tv and num(g, "FinalBasicGroupIRateTimesValue") == times
          and num(g, "BasicGroupIMLAR") == r(times / int(num(pps[0], "Limit") / 100), 3),
          "HYPOTHESIS: hand = engine on the 'first row' reading (the running-maximum reading cannot run until E-1 is decided)")
    print("  -> MLARLimit is the LARGER of the reported total and the 'max' limit, so the average rate is diluted when a "
          "single contents limit exceeds the reported values: the reading decides the dollar")


# ------------------------------------------------------------------ C22-06

def tables_and_literals():
    progress("C22-06  TABLES AND LITERALS")
    print("\n" + "=" * 90 + "\nC22-06  TABLES AND LITERALS\n" + "-" * 90)
    lookups = {"ValRptgIncLocsRate": ("CauseOfLoss", ("Basic", "Broad", "Special", "Earthquake")),
               "ValRptgAcqrdLocsRate": ("Constant", ("Y",)), "NewBusnFactor": ("Constant", ("Y",)),
               "SeasonalRiskFactor": ("Constant", ("Y",)), "AddlLocSpclCoinsFactor": ("Constant", ("Y",)),
               "CoinsuranceFactor": ("CoinsuranceValue", ("100%",)), "IndivisibleSublineBasic": ("Constant", ("Y",)),
               "IndivisibleSublineBroad": ("Constant", ("Y",)), "IndivisibleSublineSpecial": ("Constant", ("Y",))}
    missing = []
    for j in s18.STATES:
        for t, (col, keys) in lookups.items():
            have = {row.get(col) for row in r4.rows(j, t)}
            missing += [(j, t, k) for k in keys if k not in have]
    print(f"  {len(lookups)} literal-keyed tables x 46 states: missing rows {missing or 'none'}")
    check(not missing, "every literal key the chunk's rules pass has a row in every state (own table, else CW)")
    for t in ("ValRptgIncLocsRate", "ValRptgAcqrdLocsRate", "NewBusnFactor", "SeasonalRiskFactor", "AddlLocSpclCoinsFactor"):
        own = [j for j in s18.STATES if (r4.pkgs(j)[0] / "Rate Tables" / f"{t}.RateTable.csv").exists()
               and r4.pkgs(j)[0] != CW]
        print(f"    {t:24s} CW {[tuple(v for k, v in row.items() if k != 'StateCode') for row in r4.rows('OR', t)]}  state-filed: {own or 'none'}")
    fl = r4.rows("FL", "CoinsuranceFactor")
    print(f"    CoinsuranceFactor FL {[(row['CoinsuranceValue'], row['Factor']) for row in fl]}  (VR Form's lookup keys '100%')")
    readers = [f.name for f in (CW / "Rules").glob("*.xml") if re.search(rf"{VR}\[1\]/CoinsuranceFactor|{VR}Table/{P}{VR}\[1\]/CoinsuranceFactor",
                                                                         f.read_text(encoding="utf-8-sig"))]
    check(not readers, "the VR Form's CoinsuranceFactor (0.9 CW, FL's own) is written but read by no rule: it cannot move a dollar")
    for sib in ("ValRptgFormNewBusnFactor", "ValRptgSeasonalRiskFactor"):
        hdr = not r4.rows("OR", sib)
        used = [f.name for f in (CW / "Rules").glob("*.xml") if sib in f.read_text(encoding="utf-8-sig")]
        check(hdr and not used, f"sibling table {sib}: header-only and read by no rule (the rules read {sib.replace('ValRptgForm', '').replace('ValRptg', '')})")
    dom = CW / "Domain Tables"
    with open(dom / "DomainMultiLocAvgRates.DomainTable.csv", encoding="utf-8-sig") as h:
        mla = [row["DataValue"] for row in csv.DictReader(h)]
    with open(dom / "DomainCoinsurancePrsnlProp.DomainTable.csv", encoding="utf-8-sig") as h:
        rep = sorted({row["DataValue"] for row in csv.DictReader(h) if "Reporting" in row["DataValue"]})
    print(f"  MultiLocAvgRates domain {mla}; contents reporting coinsurance values {rep}")
    check(mla == ["Used", "Not Used"], "MultiLocAvgRates takes 'Used' / 'Not Used' (the rules' literals)")
    check(sorted(rep) == sorted(REPORTING), "the five reporting coinsurance values in the domain are exactly the five AttachFormValueReportingForm tests")
    d = rated(two_locations(vr="Not Used"))[0]
    print(f"  form label on OR: VR Form ErcFormName {txt(nodes(d, VR)[0], 'ErcFormName')!r} (CW Pages has 'CP 13 10 04 02'; "
          f"OR's own Pages table hides the CW row: OI-118)")


def main():
    who_writes()
    touchpoints()
    attach_and_switches()
    gi_by_hand()
    tables_and_literals()
    m, s = divmod(int(time.monotonic() - T0), 60)
    print("\n" + ("RC-1 (C22-02..C22-06): ALL CHECKS PASS" if not FAIL else f"RC-1: {len(FAIL)} FAILED: {FAIL}") + f"  ({m}m{s:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
