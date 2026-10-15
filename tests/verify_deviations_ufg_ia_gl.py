"""B-19 / DEV-003: UFG's Iowa GL filing (SERFF UNFG-134374972), proved end to end on a real GL filing.

Run: python tests/verify_deviations_ufg_ia_gl.py [--live]    (offline unless --live: 3 ISO calls)

The filing: one LCM per company per subline -- UFC Prem/Ops 0.942, Products 1.789; Addison 1.272, 2.415 -- on
every class except "a"-rated ones (UFG's own ELP ranges); new business 7/15/2025, renewal 11/1/2025; on ISO's
GL-2023-BGL1 loss costs, so both companies pin Iowa GL to GL_IA_20240401_V01 (the user's decision, 2026-10-15).

  U1  T10  both companies' files validate, compile, and read back as the rows written
  U2  T5   every Prem/Ops and Products record carries exactly its filed LCM, and each subline's premium moves by it
  U3  T5   an "a"-rated class keeps LCM 1: its Prem/Ops premium is technical's
  U4  T7   new business from 7/15/2025 (not 7/14), renewals from 11/1/2025 (not 10/31)
  U5  T8   technical rates on the pinned GL-2023-BGL1 edition: equal to an ISO-only rating dated inside it; the
           waterfall (pin, LCM, rounding) adds up from ISO's edition in force to carrier
  U6  T4   only Prem/Ops and Products coverage records (and the premiums they roll into) change
  U7       carrier on 7/15/2025 equals ISO's own rules run on the pinned edition with UFG's LCMs written in
  U8  live ISO's service, asked that same request on a date inside the pinned edition, prices it as we do
"""
from __future__ import annotations

import argparse
import copy
import json
import shutil
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for p in (ROOT, ROOT / "scripts", ROOT / "scripts" / "cf", ROOT / "console", ROOT / "tests"):
    sys.path.insert(0, str(p))

import verify_deviations_engine as E                          # noqa: E402  (fixture root, build)

FAILED, CHECKS = [], []
REF = "IA-GL-UNFG-134374972.v1"
FILED = {"UFC": {"PremOps": Decimal("0.942"), "ProdsCompldOps": Decimal("1.789")},
         "ADD": {"PremOps": Decimal("1.272"), "ProdsCompldOps": Decimal("2.415")}}
PIN = "GL_IA_20240401_V01"
INSIDE_PIN = "20250301"                     # a date ISO resolves to the pinned edition
A_RATED = ("10119", {"elp_override_premops": "0.5"})


def check(label: str, ok: bool, detail: str = "") -> None:
    CHECKS.append((label, bool(ok)))
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}" + ("" if ok else f"  [{detail}]"))
    if not ok:
        FAILED.append(label)


def request(company=None, date="20250715", cls="18501", policy_type="New", **extra):
    from console import catalog
    req = catalog.build("GL", "IA", {"class_code": cls, "effective_date": date, **extra})
    if company:
        req["header"].update(WritingCompany=company, PolicyType=policy_type)
    return req


def records(tree) -> dict:
    """{coverage: (premium, LCM)} over the GL Prem/Ops and Products coverage records."""
    from deviations.engine import GL_LCM_RECORDS
    out, stack = {}, [tree]
    while stack:
        n = stack.pop()
        stack.extend(n.children)
        if n.tag in GL_LCM_RECORDS:
            p, lcm = n.first("Premium"), n.first("LCM")
            out[GL_LCM_RECORDS[n.tag][0]] = (Decimal(p.text or 0), Decimal(lcm.text) if lcm is not None else None)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    a = ap.parse_args()
    from gl_engine.rating import Kernel
    from deviations import proof as P
    from deviations.compile import show
    from deviations.files import load_filing, log_action, read_json
    K = Kernel()
    root = E.tmp_root()
    live_cases = []
    try:
        print("\nU1  T10 files")
        for co in FILED:
            p = root / "UFG" / co / "authored" / f"{REF}.json"
            f = load_filing(p)
            log_action(f.company_dir, f.filing, f.version, "propose", "Dan Roman")
            log_action(f.company_dir, f.filing, f.version, "sign-off", "Dan Roman")
            E.build(p)
            back = show(f.company_dir, "GL", REF)
            wrote = sorted((r["target"], json.dumps(r["scope"], sort_keys=True), str(Decimal(str(r["value"]))))
                           for r in read_json(p)["rows"])
            got = sorted((r["target"], json.dumps(r["scope"], sort_keys=True), str(Decimal(str(r["value"]))))
                         for r in back["rows"])
            check(f"U1 {co}: validates, compiles and reads back as its {len(wrote)} rows", got == wrote,
                  f"{got} vs {wrote}")

        for co, lcms in FILED.items():
            print(f"\n{co}")
            r = K.rate(request(co), root=root, with_technical=True)
            rec, tech = records(r.tree), records(r.technical.tree)
            check(f"U2 {co}: Prem/Ops LCM {rec['PremOps'][1]}, Products {rec['ProdsCompldOps'][1]} (filed "
                  f"{lcms['PremOps']}, {lcms['ProdsCompldOps']})",
                  all(rec[c][1] == lcms[c] for c in lcms))
            for c in lcms:
                t, v = tech[c][0], rec[c][0]
                check(f"U2 {co}: {c} {t} -> {v} is x{lcms[c]} within ISO's whole-dollar rounding",
                      abs(t * lcms[c] / tech[c][1] - v) <= 1, f"expected {t * lcms[c]}")
            cls, extra = A_RATED
            ar = K.rate(request(co, cls=cls, **extra), root=root, with_technical=True)
            arec, atech = records(ar.tree), records(ar.technical.tree)
            check(f"U3 {co}: 'a'-rated {cls} keeps LCM {arec['PremOps'][1]} and its Prem/Ops premium "
                  f"({atech['PremOps'][0]} -> {arec['PremOps'][0]})",
                  arec["PremOps"][1] == 1 and arec["PremOps"][0] == atech["PremOps"][0])
            dates = {}
            for d, pt in (("20250714", "New"), ("20250715", "New"), ("20251031", "Renewal"), ("20251101", "Renewal")):
                dates[(d, pt)] = bool(K.rate(request(co, d, policy_type=pt), root=root).deviation["filings"])
            check(f"U4 {co}: new business from 7/15/2025, renewals from 11/1/2025",
                  dates == {("20250714", "New"): False, ("20250715", "New"): True,
                            ("20251031", "Renewal"): False, ("20251101", "Renewal"): True}, str(dates))
            plain = K.rate(request(None, INSIDE_PIN))
            check(f"U5 {co}: technical rates on {r.technical.packages[0]} and equals ISO-only on {INSIDE_PIN} "
                  f"({r.technical.premium} = {plain.premium})",
                  r.technical.packages[0] == PIN == plain.packages[0] and r.technical.premium == plain.premium)
            in_force = K.rate(request(None))
            wf = r.deviation["waterfall"]
            steps = sum(Decimal(s["effect"]) for s in wf)
            check(f"U5 {co}: waterfall {[(s['step'], s['effect']) for s in wf]} adds up "
                  f"{in_force.premium} -> {r.premium}",
                  [s["step"] for s in wf][:2] == ["edition pin", "LCM"]
                  and steps == Decimal(r.premium) - Decimal(in_force.premium))
            stray = [c["path"] for c in r.deviation["changedPaths"]
                     if not any(k in c["path"] for k in ("PremOpsCoverage", "ProdsCompldOpsCoverage"))
                     and "Premium" not in c["path"].rsplit("/", 1)[-1]]
            check(f"U6 {co}: {len(r.deviation['changedPaths'])} changed paths, all Prem/Ops, Products or roll-ups",
                  not stray, str(stray[:3]))
            from deviations import engine as dv
            plan = dv.plan_for("GL", co, "IA", "2025-07-15", "New", root=root)
            for cls_, extra_ in (("18501", {}), A_RATED):
                base = P.with_company(request(None, INSIDE_PIN, cls=cls_, **extra_), co)
                creq = P.gl_carrier_request(plan, base, dv.book_for(plan))
                ours_lcm = K.rate(copy.deepcopy(creq))
                carrier = r if cls_ == "18501" else ar
                check(f"U7 {co} {cls_}: carrier {carrier.premium} = ISO's rules on {INSIDE_PIN} with the LCMs "
                      f"written in ({ours_lcm.premium})", ours_lcm.premium == carrier.premium)
                if co == "UFC" or cls_ == "18501":
                    live_cases.append((f"{co} {cls_}", creq, ours_lcm.premium))
    finally:
        shutil.rmtree(root, ignore_errors=True)

    if a.live:
        print("\nU8  live")
        import raas
        client = raas.RaaS(lane="adhoc", origin="B-19 UFG IA GL (DEV-003)")
        for name, creq, ours in live_cases:
            try:
                resp = client.rate(creq)
                iso = ((resp.get("Body", {}).get("GeneralLiability") or [{}])[0]).get("Premium")
            except raas.RaaSError as exc:
                iso = f"refused: {str(exc)[:120]}"
            check(f"U8 {name}: ISO prices the pinned edition with UFG's LCMs at {iso}, ours {ours}",
                  str(iso) == str(ours), str(iso))
    from deviations import suite_log
    suite_log.record("ufg_ia_gl", CHECKS)
    print(f"\n{'FAILED: ' + ', '.join(FAILED) if FAILED else 'all passed'}")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
