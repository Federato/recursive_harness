"""B-19 / DEV-003: UFG's Iowa GL filing (SERFF UNFG-134374972), proved end to end on a real GL filing.

Run: python tests/verify_deviations_ufg_ia_gl.py [--live [--override REASON]]    (offline unless --live: 3 ISO calls)

The filing: one LCM per company per subline -- UFC Prem/Ops 0.942, Products 1.789; Addison 1.272, 2.415 -- on
every class except "a"-rated ones (UFG's own ELP ranges); new business 7/15/2025, renewal 11/1/2025. The LCMs ride
ISO's edition in force on the policy date (edition pins retired, the user's decision 2026-10-16; B-19 had pinned
GL_IA_20240401_V01).

  U1  T10  both companies' files validate, compile, and read back as the rows written
  U2  T5   every Prem/Ops and Products record carries exactly its filed LCM, and each subline's base rate is
           technical's x the LCM, to ISO's three places (the premium follows through ISO's own rounding)
  U3  T5   an "a"-rated class keeps LCM 1: its Prem/Ops premium is technical's
  U4  T7   new business from 7/15/2025 (not 7/14), renewals from 11/1/2025 (not 10/31)
  U5       technical rates on ISO's edition in force on the policy date and equals an ISO-only rating that day; the
           waterfall (LCM, then the rest) adds up from technical to carrier, with no edition step
  U6  T4   only Prem/Ops and Products coverage records (and the premiums they roll into) change
  U7       carrier on 7/15/2025 equals ISO's own rules run that day with UFG's LCMs written in
  U8  live ISO's service, asked that same request, prices it as we do
  v2 (B-21): the filing's experience rating ELR 68.6% and policy writing minimums (UFC $500, ADD $625)
  U9  T10  v2 validates, compiles and reads back as its 6 rows (the ELR a table row, the minimum a policy item)
  U10 T6   ELR: an experience-rated risk reads ERPExpectedLossRatio 0.686 (technical 1); carrier without the ELR
           step is v1's carrier; the step is the whole difference
  U11 T6   minimum: a small risk is raised to the company's minimum, the top-up shown as its own line and step;
           technical is untouched; a risk above it is v1's carrier
  U12 T4   on an ordinary risk v2 changes only what v1 changed, plus the minimum written on the policy
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
REF2 = "IA-GL-UNFG-134374972.v2"
MINIMUM = {"UFC": Decimal(500), "ADD": Decimal(625)}
EXPERIENCED = {"experience_rating": "Yes", "exposure": "50000000"}   # credibility 0.18: the mod applies
SMALL = {"exposure": "20000"}                                        # technical about $55: under every minimum
FILED = {"UFC": {"PremOps": Decimal("0.942"), "ProdsCompldOps": Decimal("1.789")},
         "ADD": {"PremOps": Decimal("1.272"), "ProdsCompldOps": Decimal("2.415")}}
A_RATED = ("10119", {"elp_override_premops": "0.5"})


def _num(v):
    try:
        return Decimal(str(v))
    except Exception:                                          # a refusal's text is not a premium
        return None


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
            p, lcm, br = n.first("Premium"), n.first("LCM"), n.first("BaseRate")
            out[GL_LCM_RECORDS[n.tag][0]] = (Decimal(p.text or 0), Decimal(lcm.text) if lcm is not None else None,
                                             Decimal(br.text) if br is not None and br.text else None)
    return out


def _field(tree, tag):
    out, stack = [], [tree]
    while stack:
        n = stack.pop()
        stack.extend(n.children)
        if n.tag == tag and n.text not in (None, ""):
            out.append(Decimal(n.text))
    return out


def v2(K, root, v1, show, load_filing, log_action, read_json) -> None:
    """B-21: the same filing's v2, with the ELR and the policy writing minimum."""
    print("\nU9..U12  v2: experience rating ELR and policy writing minimum (B-21)")
    for co in MINIMUM:
        p = root / "UFG" / co / "authored" / f"{REF2}.json"
        f = load_filing(p)
        log_action(f.company_dir, f.filing, f.version, "propose", "Dan Roman")
        log_action(f.company_dir, f.filing, f.version, "sign-off", "Dan Roman")
        E.build(p)
        key = lambda r: (r["target"], json.dumps(r["scope"], sort_keys=True), str(Decimal(str(r["value"]))))  # noqa
        wrote = sorted(map(key, read_json(p)["rows"]))
        got = sorted(map(key, show(f.company_dir, "GL", REF2)["rows"]))
        check(f"U9 {co}: v2 validates, compiles and reads back as its {len(wrote)} rows", got == wrote,
              f"{got} vs {wrote}")
        from deviations.diff import diff_iso
        from deviations.validate import validate
        try:
            lines = diff_iso(validate(f))
        except Exception as exc:  # noqa: BLE001 - OI-142 raised here
            lines = [f"raised {exc!r}"]
        mn = MINIMUM[co]
        check(f"U13 {co}: diff --iso reads v2 whole: the policy minimum {mn} against ISO none, beside the LCMs (OI-142)",
              any(x.split() == ["MIN:Policy", "ISO", "none", "company", str(mn), "(replace)"] for x in lines)
              and any(x.strip().startswith("LCM PremOps") for x in lines), "; ".join(lines[:6]))
    for co, mn in MINIMUM.items():
        print(f"\n{co} v2")
        r = K.rate(request(co, **EXPERIENCED), root=root, with_technical=True)
        old = v1[co]["exp"]
        wf = {s["step"]: Decimal(s["effect"]) for s in r.deviation["waterfall"]}
        elr = _field(r.tree, "ERPExpectedLossRatio")
        check(f"U10 {co}: experience-rated carrier reads ERPExpectedLossRatio {sorted(set(elr))}, technical "
              f"{sorted(set(_field(r.technical.tree, 'ERPExpectedLossRatio')))}",
              elr and set(elr) == {Decimal("0.686")} and set(_field(r.technical.tree, "ERPExpectedLossRatio")) ==
              {Decimal(1)})
        check(f"U10 {co}: v1 carrier {old.premium} + ELR step {wf.get('ExpectedLossRatio')} = v2 carrier {r.premium}",
              r.technical.premium == old.technical.premium and wf.get("ExpectedLossRatio") not in (None, 0)
              and Decimal(old.premium) + wf["ExpectedLossRatio"] == Decimal(r.premium), str(wf))
        s_ = K.rate(request(co, **SMALL), root=root, with_technical=True)
        old = v1[co]["small"]
        wf = {s["step"]: Decimal(s["effect"]) for s in s_.deviation["waterfall"]}
        label = f"policy minimum ${mn:,}"
        check(f"U11 {co}: a small risk, technical {s_.technical.premium}, v1 carrier {old.premium}, is raised to "
              f"{s_.premium} (the minimum {mn})",
              Decimal(s_.premium) == mn and Decimal(s_.technical.premium) < mn
              and s_.technical.premium == old.technical.premium)
        top = mn - Decimal(old.premium)
        check(f"U11 {co}: the top-up {top} is its own line ({s_.by_coverage.get('PolicyWritingMinimum')}) and its own "
              f"waterfall step ({wf.get(label)})",
              s_.by_coverage.get("PolicyWritingMinimum") == top == wf.get(label), str(wf))
        check(f"U11 {co}: ISO's own field GeneralLiability.PolicyWritingMinimum carries {mn}; technical has none",
              _field(s_.tree, "PolicyWritingMinimum") == [mn] and not _field(s_.technical.tree, "PolicyWritingMinimum"))
        plain = K.rate(request(co), root=root, with_technical=True)
        check(f"U11 {co}: a risk above the minimum is v1's carrier ({v1[co]['plain'].premium} = {plain.premium})",
              plain.premium == v1[co]["plain"].premium)
        before = {c["path"] for c in v1[co]["plain"].deviation["changedPaths"]}
        after = {c["path"] for c in plain.deviation["changedPaths"]}
        extra = sorted(after - before)
        check(f"U12 {co}: v2 changes what v1 changed plus {[x.rsplit('/', 1)[-1] for x in extra]}",
              before <= after and all(x.rsplit("/", 1)[-1].startswith(("PolicyWritingMinimum", "ERPExpectedLossRatio"))
                                      for x in extra), str(extra))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--override", help="a reason, when the adhoc lane is full and the user approved going over it")
    a = ap.parse_args()
    from gl_engine.rating import Kernel
    from deviations import proof as P
    from deviations.compile import show
    from deviations.files import load_filing, log_action, read_json
    K = Kernel()
    root = E.tmp_root()
    live_cases = []
    v1: dict = {}
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
                t, v = tech[c][2], rec[c][2]
                want = (t * lcms[c]).quantize(Decimal("0.001"), rounding="ROUND_HALF_UP")
                check(f"U2 {co}: {c} base rate {t} -> {v} is x{lcms[c]} ({want}); premium {tech[c][0]} -> {rec[c][0]}",
                      v == want, f"expected {want}")
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
            plain = K.rate(request(None))
            check(f"U5 {co}: technical rates on {r.technical.packages[0]}, ISO's edition in force on 7/15/2025, and "
                  f"equals ISO-only that day ({r.technical.premium} = {plain.premium})",
                  r.technical.packages[0] == plain.packages[0] and r.technical.premium == plain.premium)
            wf = r.deviation["waterfall"]
            steps = sum(Decimal(s["effect"]) for s in wf)
            check(f"U5 {co}: waterfall {[(s['step'], s['effect']) for s in wf]} adds up "
                  f"{r.technical.premium} -> {r.premium}, no edition step",
                  [s["step"] for s in wf][0] == "LCM" and "edition pin" not in [s["step"] for s in wf]
                  and steps == Decimal(r.premium) - Decimal(r.technical.premium))
            stray = [c["path"] for c in r.deviation["changedPaths"]
                     if not any(k in c["path"] for k in ("PremOpsCoverage", "ProdsCompldOpsCoverage"))
                     and "Premium" not in c["path"].rsplit("/", 1)[-1]]
            check(f"U6 {co}: {len(r.deviation['changedPaths'])} changed paths, all Prem/Ops, Products or roll-ups",
                  not stray, str(stray[:3]))
            from deviations import engine as dv
            plan = dv.plan_for("GL", co, "IA", "2025-07-15", "New", root=root)
            for cls_, extra_ in (("18501", {}), A_RATED):
                base = P.with_company(request(None, cls=cls_, **extra_), co)
                creq = P.gl_carrier_request(plan, base, dv.book_for(plan))
                ours_lcm = K.rate(copy.deepcopy(creq))
                carrier = r if cls_ == "18501" else ar
                check(f"U7 {co} {cls_}: carrier {carrier.premium} = ISO's rules on 7/15/2025 with the LCMs "
                      f"written in ({ours_lcm.premium})", ours_lcm.premium == carrier.premium)
                if co == "UFC" or cls_ == "18501":
                    live_cases.append((f"{co} {cls_}", creq, ours_lcm.premium))
            v1[co] = {k: K.rate(request(co, **cfg), root=root, with_technical=True)
                      for k, cfg in (("plain", {}), ("exp", EXPERIENCED), ("small", SMALL))}
        v2(K, root, v1, show, load_filing, log_action, read_json)
    finally:
        shutil.rmtree(root, ignore_errors=True)

    if a.live:
        print("\nU8  live")
        import raas
        client = raas.RaaS(lane="adhoc", origin="B-19 UFG IA GL (DEV-003)", override=a.override)
        for name, creq, ours in live_cases:
            try:
                resp = client.rate(creq)
                iso = ((resp.get("Body", {}).get("GeneralLiability") or [{}])[0]).get("Premium")
            except raas.RaaSError as exc:
                iso = f"refused: {str(exc)[:120]}"
            check(f"U8 {name}: ISO prices the edition in force with UFG's LCMs at {iso}, ours {ours}",
                  isinstance(iso, (int, float, str)) and _num(iso) == _num(ours), str(iso))
    from deviations import suite_log
    suite_log.record("ufg_ia_gl", CHECKS)
    print(f"\n{'FAILED: ' + ', '.join(FAILED) if FAILED else 'all passed'}")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
