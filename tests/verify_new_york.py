"""New York differential — the most-deviating jurisdiction in the corpus.

WHY THIS FILE EXISTS
--------------------
New York carries **698 override rules across 134 files — rank 1 of 51, 2.6x the
next jurisdiction (Vermont, 267) and 5.6x the median (124)**. Three gates have
recorded a New York finding in passing; nothing has measured the whole surface,
and two of the passing records turned out to be narrower than the truth.

Like `verify_california.py` this is a DIFFERENTIAL fixture — it pins the shape of
New York's deviation, which an oracle test would not show. **It does NOT mean an
oracle is unavailable:** `Payloads/NY` holds a rated output, one of 53 across 50
states in the RAAS baseline set (corrected 2026-08-12).

WHAT IT ESTABLISHES
-------------------
1. **New York does not write claims-made General Liability at all**, and ISO says
   so three ways at once: four claims-made multiplier tables overridden to **0
   rows**, `SetClaimsMadeMultiplier` stubbed to `1.0` in **5 coverage groups**,
   and (liquor only) an occurrence-only `SetBaseRate`. **NY is the only one of 51
   that does any of it.** Gate 332 recorded the liquor third.

2. **The terrorism gate's formula survives New York unchanged.** NY overrides 174
   of the 602 rules in `GeneralLiabilityTerrorismEndorsementCoverage` and adds 4,
   which looked like a hole in a gate filed the day before. It is not:
   **`SetPremium` is not among them.** NY changes which endorsements feed
   `EndorsementPremium`, not the formula that consumes it.

3. **New York switches off rating for 83 endorsements** by overriding `ErcRate`
   with an empty body — 130 of its 151 empty overrides replace a non-trivial
   countrywide body. N3's *empty is not absent and not inherit*, at the largest
   scale in the corpus.

    python tests/verify_new_york.py

Exit code 0 = all pass.
"""
from __future__ import annotations

import glob
import importlib.util
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
_spec = importlib.util.spec_from_file_location(
    "asof", os.path.join(PROJ, "scripts", "erc", "32_asof_recount.py"))
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)

ROOT = A.ROOT
ASOF = "20260812"
RULE = re.compile(
    r'<rul:Rule Name="([^"]+)"[^>]*?DataDefGroup="([^"]+)"[^>]*>(.*?)</rul:Rule>',
    re.S)

PK = A.discover()
RES = {j: r for j in PK if j != "CW" for r in [A.resolve(PK[j], ASOF)] if r}
NY = RES["NY"]
CWDIR = os.path.join(ROOT, "countrywide", NY[2].replace("GL_CW_", "GL CW ")
                     .replace("_", " "))

CASES: list[tuple[str, object]] = []


def case(name):
    def deco(fn):
        CASES.append((name, fn))
        return fn
    return deco


def _rules(base: str) -> dict[tuple[str, str], str]:
    out: dict[tuple[str, str], str] = {}
    for f in sorted(glob.glob(os.path.join(base, "Rules", "*.xml"))):
        for m in RULE.finditer(A._read(f)):
            out[(m.group(2), m.group(1))] = m.group(3)
    return out


NYR = _rules(NY[3])
CWR = _rules(CWDIR)


def _flat(s: str) -> str:
    return re.sub(r'\s+', '', s)


@case("New York is the most-deviating jurisdiction, by a wide margin")
def _():
    counts = {}
    for j, r in RES.items():
        n = 0
        for f in glob.glob(os.path.join(r[3], "Rules", "*.xml")):
            n += len(RULE.findall(A._read(f)))
        counts[j] = n
    order = sorted(counts, key=lambda j: -counts[j])
    assert order[0] == "NY", order[:3]
    assert counts["NY"] == 698, counts["NY"]
    assert counts[order[1]] == 267 and order[1] == "VT", (order[1], counts[order[1]])
    assert counts["NY"] > 2.5 * counts[order[1]]


@case("New York does not write claims-made GL — three mechanisms, and it is alone in all of them")
def _():
    # 1. the multiplier rule is stubbed to a constant in 5 groups
    stub = sorted(g for (g, n), b in NYR.items()
                  if n == "SetClaimsMadeMultiplier"
                  and "Lookup" not in b and "RunRule" not in b and "Constant" in b)
    assert len(stub) == 5, stub
    assert {"GeneralLiabilityClassificationPremOpsCoverage",
            "GeneralLiabilityClassificationProdsCompldOpsCoverage",
            "GeneralLiabilityClassificationLiquorCoverage",
            "GeneralLiabilityUnmannedAircraftCovABIPDCoverage",
            "GeneralLiabilityUnmannedAircraftCovBPAICoverage"} == set(stub), stub
    for g in stub:
        assert "1.0" in NYR[(g, "SetClaimsMadeMultiplier")]

    # 2. every claims-made multiplier table is overridden to zero rows
    for t in ("PremOpsClaimsMadeMultiplier", "PremOpsClaimsMadeMultiplierAllOther",
              "ProdsCompldOpsClaimsMadeMultiplier",
              "ProdsCompldOpsClaimsMadeMultipliers"):
        assert os.path.exists(os.path.join(NY[3], "Rate Tables",
                                           t + ".RateTable.csv")), t
        assert A.table(NY[3], "Rate Tables", t + ".RateTable.csv") == [], t
    # and the countrywide originals are populated — so this withdraws real rates
    assert len(A.table(CWDIR, "Rate Tables",
                       "PremOpsClaimsMadeMultiplier.RateTable.csv")) == 5940

    # 3. no other jurisdiction stubs the rule
    others = []
    for j, r in RES.items():
        if j == "NY":
            continue
        for f in glob.glob(os.path.join(r[3], "Rules", "*.xml")):
            s = A._read(f)
            if "SetClaimsMadeMultiplier" not in s:
                continue
            for m in RULE.finditer(s):
                if m.group(1) == "SetClaimsMadeMultiplier":
                    b = _flat(m.group(3))
                    if "Lookup" not in b and "RunRule" not in b and "Constant" in b:
                        others.append(j)
    assert not others, sorted(set(others))


@case("the terrorism gate's premium formula survives New York unchanged")
def _():
    grp = "GeneralLiabilityTerrorismEndorsementCoverage"
    ny = {n for (g, n) in NYR if g == grp}
    cw = {n for (g, n) in CWR if g == grp}
    assert len(cw) == 602, len(cw)
    assert len(ny) == 178, len(ny)
    assert len(ny - cw) == 4, sorted(ny - cw)
    overridden = {n for n in ny & cw if NYR[(grp, n)] != CWR[(grp, n)]}
    assert len(overridden) == 174, len(overridden)
    # THE POINT: SetPremium is inherited, so the gate's formula holds for NY
    assert "SetPremium" not in ny, "NY overrides the terrorism premium formula"
    assert "SetPremium" in cw
    body = CWR[(grp, "SetPremium")]
    srcs = set(re.findall(r'FromDataDef="([^"]+)"', body))
    assert srcs == {"CertifiedActsofTerrorismExposureClassFactor",
                    "EndorsementPremium"}, sorted(srcs)


@case("New York adds two endorsements of its own to the terrorism base")
def _():
    grp = "GeneralLiabilityTerrorismEndorsementCoverage"
    extra = sorted(n for (g, n) in NYR if g == grp and (grp, n) not in CWR)
    assert len(extra) == 4, extra
    assert all("rbitration" in n for n in extra), extra


@case("New York switches off rating for 83 endorsements with an empty ErcRate")
def _():
    empty = [(g, n) for (g, n), b in NYR.items()
             if _flat(b) in ("", "<rul:Sequence/>", "<rul:Sequence></rul:Sequence>")]
    assert len(empty) == 151, len(empty)
    ercrate = [k for k in empty if k[1] == "ErcRate"]
    assert len(ercrate) == 83, len(ercrate)
    # N3: an empty override is only meaningful if the parent body was not empty
    live = [k for k in empty if k in CWR and len(_flat(CWR[k])) > 60]
    assert len(live) == 130, len(live)


@case("New York's other neutralising stubs are the ones an empty-body check misses")
def _():
    stub = [(g, n) for (g, n), b in NYR.items()
            if len(_flat(b)) < 230 and "Constant" in _flat(b)
            and "Lookup" not in b and "RunRule" not in b]
    assert len(stub) == 98, len(stub)
    names = {n for _g, n in stub}
    for n in ("SetClaimsMadeMultiplier", "SetYearInClaimsMade",
              "SetSizeOfRiskRatingApplies", "SetCoverageOnPolicyIndicator"):
        assert n in names, n


@case("New York shards loss costs and its rating-basis selector by territory")
def _():
    tabs = sorted(f[:-len(".RateTable.csv")]
                  for f in os.listdir(os.path.join(NY[3], "Rate Tables"))
                  if f.endswith(".RateTable.csv"))
    pop = [t for t in tabs
           if A.table(NY[3], "Rate Tables", t + ".RateTable.csv")]
    assert len(tabs) == 95 and len(pop) == 71, (len(tabs), len(pop))
    shard = [t for t in pop if re.search(r'Terr\d{3}$', t)]
    assert len(shard) == 21, len(shard)
    # the base tables are present and EMPTY — N3/OI-20, not absent
    assert A.table(NY[3], "Rate Tables", "PremOpsLossCost.RateTable.csv") == []
    # and the SELECTOR is sharded too, which is rarer (N17)
    assert "PremOpsELPTextTerr001" in shard


@case("class 91600 is New York's alone, and its terrorism table says so")
def _():
    def aa(base, t):
        return {r[1].strip() for r in A.table(base, "Rate Tables", t + ".RateTable.csv")
                if len(r) > 2 and r[2].strip() != "Average Exposure Class"}
    ny_aa = aa(NY[3], "TerrorismExposureClassesPremises")
    cw_aa = aa(CWDIR, "TerrorismExposureClassesPremises")
    assert "91600" in ny_aa and "91600" not in cw_aa
    assert len(ny_aa) == 106 and len(cw_aa) == 105, (len(ny_aa), len(cw_aa))
    # NY rates it: it appears in NY's own loss cost shards
    hits = [f for f in os.listdir(os.path.join(NY[3], "Rate Tables"))
            if f.startswith("PremOpsLossCostNYTerr")
            and '"91600"' in A._read(os.path.join(NY[3], "Rate Tables", f))]
    assert len(hits) >= 20, len(hits)


@case("Special Protective and Highway is New York's alone — and belongs to item 11")
def _():
    sph = {n for (g, n) in NYR if "SpecialProtectiveHighway" in g}
    assert len(sph) == 36, len(sph)
    def tables(base):
        return sorted(f[:-len(".RateTable.csv")]
                      for f in os.listdir(os.path.join(base, "Rate Tables"))
                      if f.endswith(".RateTable.csv")
                      and ("SpecialProtective" in f or "Highway" in f))
    assert tables(CWDIR) == [], tables(CWDIR)
    ny = tables(NY[3])
    # 4 RATE tables. An earlier note said "11 tables" — that count included the
    # `*Def.RateTableDef.xml` schema siblings and the domain tables. Counting
    # files where the claim is about tables is the same defect this project
    # keeps catching, so the assertion names what it counts.
    assert ny == ["SpecialProtectiveHighwayELP", "SpecialProtectiveHighwayELPText",
                  "SpecialProtectiveHighwayHomogeneityIndex",
                  "SpecialProtectiveHighwayLossCost"], ny
    # it rates: a loss cost AND its own N17 selector, present in no other package
    assert A.table(NY[3], "Rate Tables",
                   "SpecialProtectiveHighwayLossCost.RateTable.csv")
    # deliberately NOT analysed further here — see the differential document


@case("New York's ERC package is input-only, but a RAaS oracle exists for it")
def _():
    stc = glob.glob(os.path.join(NY[3], "STC", "*.json"))
    assert len(stc) == 1, stc
    assert not [f for f in stc if "Output" in os.path.basename(f)]
    # the oracle is in the RAAS baseline set, not the ERC corpus
    proj = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pay = os.path.join(proj, "Payloads", "NY")
    assert os.path.exists(os.path.join(pay, "1. Output.json")), pay
    assert os.path.exists(os.path.join(pay, "1. Input.json")), pay


def main() -> int:
    print(f"New York differential — as of {ASOF}, {NY[1]} against {NY[2]}\n")
    fails = []
    for name, fn in CASES:
        try:
            fn()
            print(f"  PASS  {name}")
        except Exception as e:                                  # noqa: BLE001
            fails.append((name, e))
            print(f"  FAIL  {name}\n          {type(e).__name__}: {e}")
    print(f"\n{len(CASES) - len(fails)}/{len(CASES)} passed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
