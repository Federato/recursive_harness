"""B-18: the impact preview projects a filing over a book of typical risks, technical vs carrier, by risk type.

Run: python tests/verify_deviations_impact.py    (offline; no ISO calls)

  I1  totals    the overall and per-risk-type totals are the sums of their risks; every risk's change lies in its
                group's range
  I2  drivers   0311 is reached as class group A, 0702 as class group B, 0541 (in no group) as "all other"
  I3  group LCM Group II moves by exactly the filed Group II LCM over ISO's, within ISO's 3-place rate rounding:
                2.448 for class group A, 2.062 for B, 3.280 for all other (UFC Iowa)
  I4  GL        on a constructed TX filing (PremOps LCM 1.3), Prem/Ops moves by 1.3 over ISO's LCM and Products not
  I5  no ISO    the run never loads the ISO client
  I6  draft     a draft's impact (B-20) rates in a scratch store: the real store keeps it a draft, uncompiled
"""
from __future__ import annotations

import json
import shutil
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for p in (ROOT, ROOT / "scripts", ROOT / "scripts" / "cf", ROOT / "tests"):
    sys.path.insert(0, str(p))

import verify_deviations_engine as E                          # noqa: E402  (fixture root, filings)

FAILED, CHECKS = [], []


def check(label: str, ok: bool, detail: str = "") -> None:
    CHECKS.append((label, bool(ok)))
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}" + ("" if ok else f"  [{detail}]"))
    if not ok:
        FAILED.append(label)


def near(a: Decimal, b: Decimal, tol: Decimal = Decimal("0.015")) -> bool:
    return abs(a / b - 1) <= tol


def main() -> int:
    from deviations import impact as I
    from deviations import engine as dv
    root = E.tmp_root()
    try:
        print("\nI1-I3  UFC Iowa, two classes x 3 sizes x 4 constructions")
        date = I._filing_date("UFC", "CF", "IA", root)
        plan = dv.plan_for("CF", "UFC", "IA", date, "New", root=root)
        iso_lcm = dv.iso_state_lcm(dv.book_for(plan), "CF")
        risks = []
        for risk, cfg in I._risks("CF", "IA"):
            if risk.class_code in ("0311", "0702", "0541"):
                risks.append(I._rate_one("CF", "UFC", "IA", date, risk, cfg, root, plan))
        rep = I.summarize("UFC", "CF", {"IA": {"date": date, "filing": plan.ref}}, risks)
        rated = [r for r in risks if r.status == "rated"]
        check(f"I1 all {len(risks)} risks rate", len(rated) == len(risks) == 36, str(rep["refused"][:2]))
        tot_t = sum(r.technical for r in rated)
        tot_c = sum(r.carrier for r in rated)
        check(f"I1 the overall totals are the sums of the risks ({tot_t:,} -> {tot_c:,})",
              Decimal(rep["all"]["technical"]) == tot_t and Decimal(rep["all"]["carrier"]) == tot_c)
        bt = rep["by_risk_type"]
        check("I1 the risk types add up to the whole",
              sum(Decimal(v["carrier"]) for v in bt.values()) == tot_c)
        lo, hi = Decimal(rep["all"]["min"]), Decimal(rep["all"]["max"])
        check(f"I1 every risk's change lies in the range ({lo}% to {hi}%)",
              all(lo <= Decimal(I._pct(r.change)) <= hi for r in rated))
        cov_total = sum((c for r in rated for _, c in r.by_group.values()), Decimal(0))
        check("I1 the coverage groups add up to each risk's premium", cov_total == tot_c, f"{cov_total} vs {tot_c}")
        drv = {d["class"]: d["driver"] for d in rep["drivers"]}
        check(f"I2 0311 is reached as class group A ({drv.get('0311')})",
              "class group" in drv.get("0311", "") and "GroupII 2.448" in drv.get("0311", ""))
        check(f"I2 0702 is reached as class group B ({drv.get('0702')})",
              "class group" in drv.get("0702", "") and "GroupII 2.062" in drv.get("0702", ""))
        check(f"I2 0541 is reached as all other classes ({drv.get('0541')})",
              drv.get("0541", "").startswith("all other classes") and "GroupII 3.28" in drv.get("0541", ""))
        for cls, lcm in (("0311", Decimal("2.448")), ("0702", Decimal("2.062")), ("0541", Decimal("3.280"))):
            g2 = [r.by_group["Group II"] for r in rated if r.class_code == cls and "Group II" in r.by_group]
            t = sum(x[0] for x in g2)
            c = sum(x[1] for x in g2)
            check(f"I3 {cls}: Group II {t:,} -> {c:,} is the filed {lcm} over ISO's {iso_lcm}",
                  g2 and near(c / t, lcm / iso_lcm), f"ratio {c / t if t else None}")

        print("\nI4  GL, constructed TX filing")
        from console import catalog
        cdir = root / "UFG" / "IMPGL"
        cdir.mkdir(parents=True, exist_ok=True)
        (cdir / "company.json").write_text(json.dumps({"code": "IMPGL"}), encoding="utf-8")
        eff = catalog.build("GL", "TX", {})["body"]["SchemeKeys"]["EffectiveDateTime"][:10]
        E.filing(root, "IMPGL", "TX-IMP", "GL", ["TX"], eff,
                 [{"target": "LCM:PremOps", "scope": {}, "value": "1.3", "mode": "replace"}])
        g = I.run("IMPGL", "GL", ["TX"], root)
        cov = g["by_coverage"]["All"]
        po, pr = cov.get("Premises/Operations"), cov.get("Products/Completed Ops")
        gl_plan = dv.plan_for("GL", "IMPGL", "TX", I._filing_date("IMPGL", "GL", "TX", root), "New", root=root)
        iso_po = dv._state_value(dv.book_for(gl_plan), dv.GL_LCM_RECORDS[
            "GeneralLiabilityClassificationPremOpsCoverage"][1], "Rate")
        check(f"I4 {g['all']['rated']} of {g['all']['risks']} GL risks rate", g["all"]["rated"] == g["all"]["risks"] > 0,
              str(g["refused"][:2]))
        check(f"I4 Prem/Ops {po and po['technical']} -> {po and po['carrier']} is 1.3 over ISO's {iso_po}",
              po and near(Decimal(po["carrier"]) / Decimal(po["technical"]), Decimal("1.3") / iso_po, Decimal("0.03")),
              str(po))
        check(f"I4 Products does not move ({pr and pr['change']}%)", pr is None or pr["technical"] == pr["carrier"],
              str(pr))
        print("\nI6  a draft's impact, before it is approved or built (B-20)")
        from deviations.files import read_json, write_json
        src = root / "UFG" / "UFC" / "authored" / "IA-GL-UNFG-134374972.v1.json"
        d = read_json(src)
        d.update(version=2, status="draft")
        d["rows"][0]["value"] = Decimal("1.0")                 # Prem/Ops at 1.0: only Products should move
        draft = src.with_name("IA-GL-UNFG-134374972.v2.json")
        write_json(draft, d)
        wf = root / "UFG" / "UFC" / "workflow.jsonl"
        wf_before = wf.read_text(encoding="utf-8") if wf.exists() else ""
        dr = I.run_draft(draft, root=root)
        cov = dr["by_coverage"]["All"]
        po, pr = cov.get("Premises/Operations", {}), cov.get("Products/Completed Ops", {})
        check(f"I6 the draft rates: {dr['all']['rated']} of {dr['all']['risks']} risks, overall {dr['all']['change']}%, "
              f"labelled {dr.get('draft')}", dr["all"]["rated"] == dr["all"]["risks"] > 0
              and dr.get("draft") == "IA-GL-UNFG-134374972.v2")
        check(f"I6 Prem/Ops at the draft's 1.0 does not move ({po.get('change')}%); Products does ({pr.get('change')}%)",
              po.get("technical") == po.get("carrier") and pr and Decimal(pr["change"]) > 0, str(cov))
        check("I6 the real store is untouched: the draft is still a draft, not compiled, nothing in the workflow log",
              read_json(draft)["status"] == "draft"
              and not list((root / "UFG" / "UFC" / "compiled").glob("GL/IA/*v2"))
              and (wf.read_text(encoding="utf-8") if wf.exists() else "") == wf_before)
        check("I5 no ISO client was loaded", "raas" not in sys.modules)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    from deviations import suite_log
    suite_log.record("impact", CHECKS)
    print(f"\n{'FAILED: ' + ', '.join(FAILED) if FAILED else 'all passed'}")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
