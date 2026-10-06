#!/usr/bin/env python3
"""Chunk 15, RC-4 (C15-15 to C15-18): the state layer, all 46 states.

Each state gets RC-2's policy made portable (152_ / 164_'s way: Oregon's building
territories removed, the Group I territory factor pinned to 1.0, the four states'
required location fields, a windstorm deductible), with all 23 countrywide
records, their on-switches, and a Cannabis Coverage record on the Contents row
(so the Cannabis message rules, AK's and VT's variants included, all run).
Virginia also carries its six state-only Y2K records.

A manual premium does not depend on the state, so every state is predicted to
equal Oregon's RC-2 figures (1,013 / 959 / 1,066 / 1,065) EXCEPT, from the rules:

  C15-15  empty ErcRate (the record is never rated: no Premium at all)
            GA  all 10 Cannabis records
            TX  Newly Acquired Property increased limit; countrywide Y2K
            VA  countrywide Y2K (VA rates its own six instead)
          and one found by this RC's first engine sweep (2026-09-25):
            MO  both Discretionary Payroll records: MO resolves to CW 2023 V02, whose
                Discretionary Payroll files carry NO SetPremium (V03 onward rate it).
                The census checked the file existed, not that it priced, in the
                edition each state stands on.
  C15-16  FL  CoverageOnPolicyIndicator forced 0 -> Premium $0, switch or not:
              Newly Acquired Location, Portable Storage, Interruption of Computer Ops x2
  C15-17  VA  its six Y2K records: variant B, 927 x 1.15 -> $1,066 each; CP 15 58 silent
              (BI CovType is "Business Income With Extra Expense"), CP 15 59 and 15 60 fire.
          VA-OLD  the same six under VA's 20210501 edition, whose rules write the modifiers
              as ancestor::CommercialProperty/... (OI-111's shape): $927 each, because the 2020
              countrywide policy rule overwrites a supplied IRPM with 1.0 when IRPM is not
              applied (first predicted $1,066; ISO's $927 found it).
              The engine cannot run that edition whole (OI-114, an unrelated 2020 CW
              building message with a rul:Null test), so the six are checked on the tree
              (old_va_static); --live asks ISO at 2021-06-01, predictions only.
  C15-18  all 46: every record as above, every premium field for field, every message.

    python scripts/cf/171_chunk15_rc4.py [--live] [--states GA,TX]

Exits 1 on any disagreement.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from decimal import Decimal
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))
sys.path.insert(0, str(ROOT / "scripts"))

from cf_engine.config import NULL_ARITHMETIC, ROUNDING
from cf_engine.resolve import book_for
from gl_engine.interp.interpreter import Interpreter
import _state_inputs as _si                                     # noqa: E402
from gl_engine.interp.tree import Node
from gl_engine.interp.values import InterpretError

gc = import_module("149_chunk13_golden_case")
si = import_module("_state_inputs")                       # C28-17: a state's own Group II territory
rep = import_module("157_chunk14_c14-02_total_replay")
cmp = import_module("154_chunk13_rc5_fields_messages")
s18 = import_module("164_chunk14_c14-18_all_states")
rc1 = import_module("168_chunk15_rc1")
rc2 = import_module("169_chunk15_rc2")
rc3 = import_module("170_chunk15_rc3")
r11 = gc.r11
P = "CommercialProperty"
CANNABIS = [r for r in rc1.CW_RECORDS if r.startswith("Cannabis")]
Y2K = "BusinessIncomeAndOrExtraExpnCovForY2KComputerRelatedAndOtherElectronicProblems"
DPE2 = ["DiscretionaryPayrollExpense", "DiscretionaryPayrollExpenseSpclClassBusnIncome"]
FL0 = ["LocationNewlyAcquiredLocationTimeElement", "OccupClassTemporarilyInPortableStorageUnits",
       rc2.ICO, "SpecialClassBusnIncomeInterruptionOfComputerOperationsCoverage"]
VA6 = dict(zip(rc1.VA_RECORDS, [1066] * 6))
#: VA 20210501 sits on CW 20201201, whose SetIRPMFactor writes 1.0 UNCONDITIONALLY when IRPM is
#: not applied and no CPP IRPM factor is given (2026 keeps a supplied factor: IsNull guard, C14-10).
#: So the supplied 1.15 is overwritten: 1090 x .85 = 927 x 1.0 = $927. First predicted $1,066 from
#: the unrated input tree; ISO answered $927 (2026-09-25) and the 2020 rule explains it.
VA6_OLD = dict(zip(rc1.VA_RECORDS, [927] * 6))
#: Florida's special-class description table (FL V02 over CW 2023 V04) has no "Towers -
#: Broadcasting Antennas" row (only the 2026 CW does): ISO refuses, our engine prices (OI-103).
FL_SC = "Cooling Towers - Metal"
NOT_RATED = {"GA": CANNABIS, "TX": [rc2.NAP, Y2K], "VA": [Y2K], "MO": DPE2}
ZERO = {"FL": FL0}
MSG_1559 = "CP 15 59 not valid with selected Coverage Type"
MSG_1560 = "CP 15 60 not valid with selected Coverage Type"
MSG_1558 = "CP 15 58 not valid with selected Coverage Type"


import _regress  # noqa: E402  regression-mode sampling: 104_ sets CF_REGRESSION_SAMPLE; gates run in full

def expected(j):
    want = dict(rc2.ALL)
    for r in NOT_RATED.get(j, []):
        want[r] = None
    for r in ZERO.get(j, []):
        want[r] = 0
    if j in ("VA", "VA-OLD"):
        want.update(VA6)
        if j == "VA-OLD":
            want = dict(VA6_OLD)
    return want


def build(j):
    juris = "VA" if j == "VA-OLD" else j
    sub = rc2.build(list(rc2.ALL))
    cp = sub["CommercialPropertyTable"]["CommercialProperty"][0]
    cp["State"] = juris
    loc = cp["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0]
    loc.pop("BasicGroupIRatingTerr", None)
    loc.pop("BasicGroupIIRatingTerr", None)
    loc["BasicGroupIRatingTerrFactor"] = "1.0"
    loc.update(s18.STATE_LOC.get(juris, {}))
    si.localize_group2(sub, juris)
    rc3.cannabis_coverage_pp(sub)
    if juris == "FL":
        rc1.node_dicts(sub)[P + "SpecialClass"]["ClassDescription"] = FL_SC
    if juris == "VA":
        va = rc1.xsd_for(book_for("VA", gc.ASOF))
        rc1.MANUAL = rc2.MANUAL
        rc1.place(sub, va, rc1.VA_RECORDS, {})
    if j == "VA-OLD":
        sub["EffDate"], sub["ExpDate"] = "06/01/2021", "06/01/2022"
    return sub


def old_va_static(sub):
    """C15-17, edition basis: VA 20210501's six files write the modifiers as
    ancestor::CommercialProperty/... A full 2021 run stops in an unrelated 2020
    countrywide building message (a rul:Null inside a test, ISO's own "Invalid path
    removed" edit; OI-114), so the six are checked on the tree directly: every
    operand resolved with the engine's own select (OI-111 semantics) from each placed
    record, and SetPremium evaluated by hand, half-up per step, on the landed values."""
    from gl_engine.interp import tree
    b = book_for("VA", "20210601")
    rules = b.state.package.content / "Rules"
    data = Node.from_dict("MasterCFVA", sub)
    # the 2020 policy rule, applied by hand: IRPM not applied, no CPPIRPMFactor -> 1.0
    pol_node = rc1.find(data, P)[0]
    pol_node.first("IRPMFactor").text = "1.0"
    out = {}
    for rec in rc1.VA_RECORDS:
        text = (rules / f"{P}{rec}Rules.Rule.xml").read_text(encoding="utf-8-sig")
        ops, body = rc1.premium_ops(text)
        node = next(x for x in rc1.find(data, P + rec) if x.first("ManualPremium") is not None)
        vals, where = {}, []
        for op in ops:
            hit = tree.select_one(op, node)
            vals[op] = None if hit is None else hit.text
            where.append(f"{op} -> {'NOWHERE' if hit is None else hit.parent.tag.replace(P, '') or 'policy'}={vals[op]}")
        out[rec] = (rc1.hand(body, vals), where)
    return b, out


def run(j, sub):
    if j == "VA-OLD":
        _si.localize(sub, "VA", "20210601")      # C28-17: the state's own Group II territory
        ip = Interpreter(book_for("VA", "20210601"), rounding=ROUNDING, null_arithmetic=NULL_ARITHMETIC)
        data = Node.from_dict("MasterCFVA", sub)
        ip.run(data)
        return data, ip
    return gc.run(sub, juris=j)


def check(vals, want):
    """want None: never rated (no Premium, or blank); else every filled record equals want."""
    if want is None:
        return all(v in (None, "") for v in vals)
    return bool(vals) and all(v not in (None, "") and Decimal(str(v)) == Decimal(want) for v in vals)


def ours(data, rec):
    return [x.first("Premium").text if x.first("Premium") is not None else None
            for x in rc1.find(data, P + rec) if x.first("ManualPremium") is not None]


def theirs(resp, rec):
    out = []

    def walk(o, k=None):
        if isinstance(o, dict):
            if k == P + rec and o.get("ManualPremium") not in (None, "", 0):
                out.append(o.get("Premium"))
            for kk, v in o.items():
                if isinstance(v, (dict, list)):
                    walk(v, kk)
        elif isinstance(o, list):
            for x in o:
                walk(x, k)
    walk(resp["Body"])
    return out


def request(j, sub):
    juris = "VA" if j == "VA-OLD" else j
    req = r11.payload(sub)
    for cp in req["body"]["CommercialProperty"]:
        cp["State"] = juris
    req["body"]["SchemeKeys"]["ProductName"] = r11.PRODUCT.format(state=juris)
    if j == "VA-OLD":
        req["body"]["SchemeKeys"]["EffectiveDateTime"] = "2021-06-01T00:00:00"
    return req


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--states")
    a = ap.parse_args()
    states = a.states.split(",") if a.states else s18.STATES + ["VA-OLD"]
    fails = []
    for j in _regress.sample(states):
        if j == "VA-OLD":
            b, out = old_va_static(build(j))
            bad = [(r, h, 927) for r, (h, w) in out.items() if h != 927]
            print(f"  VA-OLD {b}: the six Y2K records, ancestor:: paths resolved on the tree, hand premium "
                  f"{'927 each, as derived' if not bad else 'DIFFERS'}")
            for r, (h, w) in list(out.items())[:1]:
                print("         e.g. " + "; ".join(w))
            if bad or any("NOWHERE" in x for _, w in out.values() for x in w):
                fails.append(j)
            continue
        try:
            data, ip = run(j, build(j))
        except InterpretError as exc:
            print(f"  {j}: RAISED {str(exc)[:140]}")
            fails.append(j)
            continue
        want = expected(j)
        bad = [(r, ours(data, r), v) for r, v in want.items() if not check(ours(data, r), v)]
        msgs = set(ip.messages)
        mb = []
        if j in ("VA", "VA-OLD"):
            mb = [m for m in (MSG_1559, MSG_1560) if m not in msgs] + ([MSG_1558] if MSG_1558 in msgs else [])
        special = [f"{r[:28]}={v}" for r, v in want.items() if v != rc2.ALL.get(r)]
        if bad or mb:
            fails.append(j)
        print(f"  {j:6s} engine {'as derived' if not bad and not mb else 'DIFFERS'} ({len(want)} records"
              + (f"; state-specific: {', '.join(special)}" if special else "") + ")"
              + "".join(f"\n         {r}: got {g}, derived {v}" for r, g, v in bad)
              + "".join(f"\n         message: {m}" for m in mb))
    print(f"\nengine: {len(states) - len(fails)} of {len(states)} as derived")

    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
        agree, refused = 0, []
        print("\nISO live (every predicted record, every Premium field for field, every message):")
        for j in states:
            sub = build(j)
            req = request(j, sub)
            (gc.OUT / f"chunk15_rc4_{j}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
            try:
                resp = client.rate(req)
            except raas_mod.RaaSError as exc:
                mm = re.search(r"Matrix: (\w+).*?Keys: ([^.]*)", str(exc.body)) or re.search(r'"Message":"([^"]{0,160})', str(exc.body))
                print(f"  {j:6s} ISO REFUSES {mm.group(0)[:160] if mm else str(exc.body)[:160]}")
                refused.append(j)
                continue
            (gc.OUT / f"chunk15_rc4_{j}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
            want = expected(j)
            pbad = [(r, theirs(resp, r), v) for r, v in want.items() if not check(theirs(resp, r), v)]
            if j == "VA-OLD":        # predictions only: our engine cannot run the 2020 CW whole (OI-114)
                ok = not pbad
                agree += ok
                print(f"  {j:6s} {'AGREE' if ok else 'DIFFER'}: predicted {len(want) - len(pbad)} of {len(want)} (predictions only, OI-114)"
                      + "".join(f"\n         predicted {r}: ISO {x}, derived {v}" for r, x, v in pbad))
                continue
            data, ip = rep.cmp.rate(req)
            ip_, op_ = rep.iso_prem(resp), rep.our_prem(data)
            d = [(k, v, op_.get(k)) for k, v in ip_.items() if not rep.cmp.same(v, op_.get(k))]
            mi, mo = cmp.iso_messages(resp), set(ip.messages)
            ok = not pbad and not d and mi == mo
            agree += ok
            print(f"  {j:6s} {'AGREE' if ok else 'DIFFER'}: predicted {len(want) - len(pbad)} of {len(want)}, "
                  f"{len(ip_) - len(d)} of {len(ip_)} premiums, messages {'equal' if mi == mo else 'DIFFER'}"
                  + "".join(f"\n         predicted {r}: ISO {x}, derived {v}" for r, x, v in pbad)
                  + "".join(f"\n         {k[-90:]} ISO {v} ours {o}" for k, v, o in d[:5])
                  + (f"\n         ISO only {sorted(mi - mo)}\n         ours only {sorted(mo - mi)}" if mi != mo else ""))
        print(f"\n  live: {agree} of {len(states)} agree; {len(refused)} refused {refused or ''}")
        if agree != len(states):
            fails.append("live")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
