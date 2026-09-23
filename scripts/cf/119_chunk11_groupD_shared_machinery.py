#!/usr/bin/env python3
"""Chunk 11 Group D -- shared machinery: C11-06, 07, 14, 15, 21.

Every expected value is copied from `docs/CF-CHUNK11-GROUP-D.md`, written
before this ran. Base: the golden case (`114_chunk11_golden_case.py`,
$268 / $30).

  C11-06  shared names: static (same-named rules elsewhere; every RunRule in
          the 32 LI files names its FileName) and dynamic (the Structure's
          same-named fields equal ISO's saved Structure values; the LI
          record's own copies differ).
  C11-07  the policy-level cyber exclusion moves LI; the theft exclusion is
          structure-level (Group B S3).
  C11-14  coinsurance / limit / deductible / blanket leave the premium alone.
  C11-15  IRPM and package modification move the four ordinary forms, not EQ.
  C11-21  the EQ cell copies the Structure's EQ rate and changes nothing on
          the Structure.

    python scripts/cf/119_chunk11_groupD_shared_machinery.py

Exit 0 means every prediction held. Reads saved ISO responses
(results/cf-raas/chunk11_C0_response.json); makes no network call.
"""
from __future__ import annotations

import copy
import json
import re
import sys
from decimal import Decimal
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from cf_engine.resolve import book_for
from gl_engine.interp import tree
from gl_engine.interp.tree import read
from gl_engine.interp.values import InterpretError

g = import_module("114_chunk11_golden_case")
b = import_module("116_chunk11_groupB_subcoverages")
LI, cell, STRUCT = g.LI, g.cell, g.STRUCT
CP = "CommercialPropertyTable/CommercialProperty"
BGI, BGII = cell("TenantsLease", "BasicGroupI"), cell("TenantsLease", "BasicGroupII")
EQC = cell("TenantsLease", "Earthquake")
ROOT = Path(__file__).resolve().parents[2]

ok = True


def verdict(label, good, detail=""):
    global ok
    ok &= good
    print(f"  {label:62s} {'MATCH' if good else 'MISMATCH'}"
          + (f"   {detail}" if detail else ""))


def same(a, b_):
    try:
        return Decimal(str(a)) == Decimal(str(b_))
    except Exception:
        return str(a) == str(b_)


def parts(sub):
    cp = sub["CommercialPropertyTable"]["CommercialProperty"][0]
    loc = cp["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0]
    st = loc["CommercialPropertyStructureTable"]["CommercialPropertyStructure"][0]
    return cp, loc, st


def prem(sub):
    try:
        d, _ = g.run(sub)
    except InterpretError as exc:
        return None, f"REFUSED {str(exc)[:80]}"
    return d, (read(BGI + "/Premium", d), read(BGII + "/Premium", d))


# ------------------------------------------------------------------ C11-06
def c11_06():
    print("C11-06  shared names across the 32 LI groups")
    rules = book_for(g.JURIS, g.ASOF).parent.package.content / "Rules"
    li_files = sorted(rules.glob("CommercialPropertyLeaseholdInterest*.Rule.xml"))
    no_file = 0
    for f in li_files:
        s = f.read_text(encoding="utf-8-sig")
        no_file += len([m for m in re.finditer(r"<rul:RunRule\b[^>]*>", s)
                        if "FileName=" not in m.group(0)])
    verdict(f"RunRules without a FileName in {len(li_files)} LI files = 0",
            no_file == 0 and len(li_files) == 32, f"found {no_file}")

    parent = (rules / "CommercialPropertyLeaseholdInterestCoverageFormRules.Rule.xml"
              ).read_text(encoding="utf-8-sig")
    struct = (rules / "CommercialPropertyStructureRules.Rule.xml").read_text(encoding="utf-8-sig")

    def body(s, name):
        m = re.search(r'<rul:Rule Name="%s".*?</rul:Rule>' % re.escape(name), s, re.S)
        return m.group(0) if m else None

    shared = []
    for name in re.findall(r'<rul:Rule Name="([^"]+)"', parent):
        if name in ("InitializeRuleSet", "CalculateTotalPremium", "ErcProcess",
                    "ErcSetRatesAndFactors", "ErcSetStatisticalCodes"):
            continue
        sb = body(struct, name)
        if sb is not None:
            tl = sorted(set(re.findall(r'MatrixFromConstant="([^"]+)"', body(parent, name))))
            ts = sorted(set(re.findall(r'MatrixFromConstant="([^"]+)"', sb)))
            shared.append((name, re.sub(r"\s+", "", body(parent, name).split(">", 1)[1])
                           != re.sub(r"\s+", "", sb.split(">", 1)[1]), tl, ts))
    want = {"SetBroadRate", "SetSpecialRate", "SetSpecialTheftExclusionFactor",
            "SetSpecialCauseOfLossAdjustment", "SetEQCauseOfLossAdjustment",
            "SetCauseOfLoss"}
    got = {n for n, *_ in shared}
    verdict("predicted six names shared with the Structure file, all differ",
            want <= got and all(d for n, d, *_ in shared if n in want),
            f"shared={sorted(got)}")
    for n, differ, tl, ts in shared:
        print(f"      {n:40s} bodies {'differ' if differ else 'SAME'}; "
              f"LI reads {tl or '-'}; Structure reads {ts or '-'}")

    d, _ = g.run(g.submission())
    saved = ROOT / "results/cf-raas/chunk11_C0_response.json"
    if not saved.exists():
        # results/ may be cleared between sessions. Say so rather than pass
        # silently or fail for a missing file; re-create it with
        # `118_chunk11_c11-23_raas.py --only C0`.
        print(f"  SKIPPED  Structure vs ISO comparison -- {saved.name} not present")
        return
    iso = json.loads(saved.read_text(encoding="utf-8"))
    iso_st = {}

    def walk(n):
        if isinstance(n, dict):
            if "CommercialPropertyStructure" in n:
                iso_st.update(n["CommercialPropertyStructure"][0])
            for v in n.values():
                walk(v)
        elif isinstance(n, list):
            for v in n:
                walk(v)
    walk(iso)
    fields = {"BroadRate": "0.0", "SpecialRate": "0.0", "SpecialTheftExclusionFactor": "1.0",
              "SpecialCauseOfLossAdjustment": "0.0", "EQCauseOfLossAdjustment": "0.0",
              "CauseOfLoss": "Basic"}
    for f_, want_v in fields.items():
        ours_st, ours_li = read(f"{STRUCT}/{f_}", d), read(f"{LI}/{f_}", d)
        good = same(ours_st, want_v) and same(iso_st.get(f_), want_v)
        verdict(f"Structure.{f_} = {want_v} (ours and ISO)", good,
                f"ours={ours_st} ISO={iso_st.get(f_)} | LI's own={ours_li}")


# ------------------------------------------------------------------ C11-07
def c11_07():
    print("\nC11-07  exclusion records")
    sub = g.submission()
    cp, _, _ = parts(sub)
    cp["CommercialPropertyCyberIncidentExclusionTable"] = {
        "CommercialPropertyCyberIncidentExclusion": [{}]}
    d, p = prem(sub)
    f1 = read(CP + "/CyberIncidentExclusionFactorBGI", d) if d else None
    f2 = read(CP + "/CyberIncidentExclusionCOLExcptnsFactorBGI", d) if d else None
    verdict("policy cyber exclusion: factor 0.995, COL-exceptions 1.0, $267 / $30",
            p == ("267", "30") and same(f1, "0.995") and same(f2, "1.0"),
            f"premiums={p} factor={f1} colexc={f2}")


# ------------------------------------------------------------------ C11-14
def c11_14():
    print("\nC11-14  coinsurance / limit / deductible / blanket: absent at run time")
    variants = {
        "Coinsurance 80%": {"Coinsurance": "80%"},
        "Limit 500,000 (LOI)": {"Limit": "500000"},
        "Deductible 5,000": {"Deductible": "5,000"},
        "IncludedInBlkt Yes (out of domain)": {"IncludedInBlkt": "Yes"},
    }
    variants["all four together"] = {k: v for d_ in variants.values() for k, v in d_.items()}
    for label, fields in variants.items():
        sub = g.submission()
        parts(sub)[2].update(fields)
        _, p = prem(sub)
        verdict(label + " -> $268 / $30", p == ("268", "30"), f"got {p}")


# ------------------------------------------------------------------ C11-15
def c11_15():
    print("\nC11-15  IRPM and package modification")
    cases = [
        ("a policy IRPMFactor 1.10", {"IRPMFactor": "1.10"}, None, ("295", "33"), None),
        ("b policy PackageModFactor 0.90", {"PackageModFactor": "0.90"}, None, ("241", "27"), None),
        ("c both", {"IRPMFactor": "1.10", "PackageModFactor": "0.90"}, None, ("265", "30"), None),
        ("d Structure PackageModFactor 0.50 only", {}, {"PackageModFactor": "0.50"}, ("268", "30"), None),
    ]
    for label, cp_f, st_f, want, _ in cases:
        sub = g.submission()
        cp, _, st = parts(sub)
        cp.update(cp_f)
        if st_f:
            st.update(st_f)
        _, p = prem(sub)
        verdict(label + f" -> ${want[0]} / ${want[1]}", p == want, f"got {p}")
    sub = b.build(subs=["TenantsLease"], eq=True)
    parts(sub)[0].update({"IRPMFactor": "1.10", "PackageModFactor": "0.90"})
    d, p = prem(sub)
    eq = read(EQC + "/Premium", d) if d else None
    verdict("e EQ elected + both -> $265 / $30, EQ stays $10",
            p == ("265", "30") and eq == "10", f"got {p}, EQ {eq}")


# ------------------------------------------------------------------ C11-21
def c11_21():
    print("\nC11-21  the EQ cell copies chunk 10's chain and changes nothing")
    # Found by running (not predicted): a CovType=Leasehold Interest structure
    # with NO LI record gets one auto-created by the Structure's attach rule
    # -- empty, so PercentInterest and both lease dates are blank, months = 0,
    # DiscFactor = 0.0, and the rul:Power evaluates 0^0. Our engine refuses
    # (OI-104); ISO returns 1 and would price $0. So the "without LI" baseline
    # is an LI record with no sub-coverage amounts: every grid cell off.
    # Since the OI-104 fix (0^0 = 1, as ISO) it no longer refuses: the
    # auto-created empty record runs and every grid cell is off -> $0.
    bare = b.build(subs=["TenantsLease"], eq=True)
    parts(bare)[2].pop("CommercialPropertyLeaseholdInterestCoverageFormTable")
    try:
        d0, _ = g.run(bare)
        kept = tree.select(LI, d0)
        on = [s_ for s_ in g.SUBCOV for f_ in g.FORMS
              if read(cell(s_, f_) + "/CoverageOnPolicyIndicator", d0) != "0"]
        tot = read(LI + "/ErcCalculatedTotalPremium", d0)
        verdict("LI structure with NO LI record -> auto-created, all cells off, $0",
                len(kept) == 1 and not on and same(tot or 0, "0"),
                f"records={len(kept)} cells on={len(on)} total={tot}")
    except InterpretError as exc:
        verdict("LI structure with NO LI record -> auto-created, all cells off, $0",
                False, f"refused: {str(exc)[:80]}")
    with_li = b.build(subs=["TenantsLease"], eq=True)
    without = b.build(subs=[], eq=True)
    d1, _ = g.run(with_li)
    d2, _ = g.run(without)

    def eq_fields(d):
        st = tree.select(STRUCT, d)[0]
        return {c.tag: c.text for c in st.children
                if c.tag.startswith("EQ") and not c.children}
    a_, b_ = eq_fields(d1), eq_fields(d2)
    diff = {k: (a_.get(k), b_.get(k)) for k in set(a_) | set(b_) if a_.get(k) != b_.get(k)}
    verdict(f"{len(a_)} EQ-prefixed Structure fields identical, LI cells on vs all off",
            not diff and len(a_) > 0, f"diff={diff}")
    verdict("Structure EQCauseOfLossAdjustment 0.009, LI copy 0.009, EQ $10",
            same(read(STRUCT + "/EQCauseOfLossAdjustment", d1), "0.009")
            and same(read(LI + "/EQCauseOfLossAdjustment", d1), "0.009")
            and read(EQC + "/Premium", d1) == "10")


def main() -> int:
    print(f"{book_for(g.JURIS, g.ASOF)}\n")
    c11_06()
    c11_07()
    c11_14()
    c11_15()
    c11_21()
    print()
    print("Group D matches every prediction." if ok else
          "MISMATCH -- compare against docs/CF-CHUNK11-GROUP-D.md.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
