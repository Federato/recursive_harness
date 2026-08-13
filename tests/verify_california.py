"""California differential — the sole `GL_CW_20231201_V02` jurisdiction.

WHY THIS FILE EXISTS
--------------------
California resolves to `GL_CW_20231201_V02` and is the only jurisdiction that
does. Nothing tests that path.

**CORRECTED 2026-08-12.** This file previously said *"the project's one oracle is
Oklahoma — 1 of 517 STC payloads is a rated output"* and asserted that California
ships none. **That was measured over the ERC corpus and stated about the
project.** `Payloads/` — the RAAS baseline set, documented in `OPEN-ITEMS` §G
since 2026-08-10 — holds **53 rated outputs across 50 states, every one paired
with its input, and California is among them.** So a California ORACLE test is
possible and should be written once an engine exists.

This file remains a DIFFERENTIAL fixture because that is what it is for: it pins
how the two countrywide parents differ, which an oracle test would not show. It
no longer claims that an oracle is unavailable.

WHAT THE DIFFERENCE ACTUALLY IS
-------------------------------
345 of 4,461 rule bodies differ between the two parents, across 43 of 547 files,
with **zero rules added or removed** — the same names throughout, which is N11's
warning in its purest form.

**341 of the 345 are one change**: V03 wraps each write in `if (target IsNull)`,
over **210 further DataDefs**. The remaining 4 are the same idea in a different
shape.

V02 is not innocent of the idiom — it guards **exactly 3**: `LCM`, `LCMStatCode`
and `LmtdProdsWithdrawalLCM`. So V03 **generalised** an existing pattern from 3
DataDefs to 213 rather than inventing one, and the three ISO had already
protected say what it is for: **the loss cost multiplier must not be recomputed.**
*(An earlier draft of this file asserted "V02 has no guard anywhere" and the
assertion failed on its first run — which is the argument for writing the claim
as a test rather than as a sentence.)*

The first reading was "V02 overwrites a broker-supplied value". That is wrong:
`SetGeneralAggregateLimit` copies from a policy-level DataDef to a local one in
BOTH editions, from the same source. **The guard is about idempotency under
re-evaluation, not about protecting input.** Its consequence is:

    V03: every one of these 210 DataDefs is WRITE-ONCE.
    V02: they are RECOMPUTED on every evaluation of the rule.

and nothing else stops recomputation, because **all 5,601 `RunRule` calls in the
countrywide package carry `ClearCache="true"`**. ERC evaluates a coverage more
than once wherever a minimum premium must be reached — there are **14
`PremiumToReachMinCoverage` groups**, one per rateable coverage. Three of the
four non-guard differences are `SetTotal*Premium` rules inside three of those
very groups, which is the corroboration.

**Whether that changes a California premium is unproven and cannot be proven from
this corpus.** Recomputation from unchanged inputs returns the same answer; it
diverges only if an intermediate is mutated between passes. Establishing which
needs an engine, and the engine is not built. This file pins the facts so the
question stays askable.

    python tests/verify_california.py

Exit code 0 = all pass.
"""
from __future__ import annotations

import glob
import importlib.util
import json
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
CW = os.path.join(ROOT, "countrywide")
V02, V03 = "GL CW 20231201 V02", "GL CW 20231201 V03"
ASOF = "20260812"

RULE = re.compile(
    r'<rul:Rule Name="([^"]+)"[^>]*?DataDefGroup="([^"]+)"[^>]*>(.*?)</rul:Rule>',
    re.S)
GUARD = re.compile(
    r'<rul:IsNull>\s*<rul:Value[^>]*FromDataDef="([^"]+)"[^>]*AllowNullReturn="true"',
    re.S)

CASES: list[tuple[str, object]] = []


def case(name):
    def deco(fn):
        CASES.append((name, fn))
        return fn
    return deco


def _rules(pkg: str, fn: str) -> dict[str, tuple[str, str]]:
    p = os.path.join(CW, pkg, "Rules", fn)
    if not os.path.exists(p):
        return {}
    return {m.group(1): (m.group(2), m.group(3))
            for m in RULE.finditer(A._read(p))}


def _diff():
    """-> (differing, total, guard_only, other, guarded_defs, per_file)."""
    f2 = {os.path.basename(x)
          for x in glob.glob(os.path.join(CW, V02, "Rules", "*.xml"))}
    f3 = {os.path.basename(x)
          for x in glob.glob(os.path.join(CW, V03, "Rules", "*.xml"))}
    differing = total = guard_only = other = 0
    guarded: set[str] = set()
    per_file: dict[str, int] = {}
    for fn in sorted(f2 & f3):
        a, b = _rules(V02, fn), _rules(V03, fn)
        names = set(a) | set(b)
        total += len(names)
        d = 0
        for n in names:
            ba = a.get(n, (None, None))[1]
            bb = b.get(n, (None, None))[1]
            if ba == bb:
                continue
            d += 1
            differing += 1
            if bb:
                guarded.update(GUARD.findall(bb))
            strip = re.sub(r'\s+', '', re.sub(r'</?rul:(If|Test|Then|Sequence)>',
                                              '', bb or ''))
            base = re.sub(r'\s+', '', re.sub(r'</?rul:(If|Test|Then|Sequence)>',
                                             '', ba or ''))
            strip = re.sub(
                r'<rul:IsNull><rul:Value[^>]*AllowNullReturn="true"/></rul:IsNull>',
                '', strip)
            if strip == base:
                guard_only += 1
            else:
                other += 1
        if d:
            per_file[fn] = d
    return differing, total, guard_only, other, guarded, per_file, len(f2), len(f3)


D = _diff()


@case("California resolves to GL_CW_20231201_V02 and is the only jurisdiction that does")
def _():
    pk = A.discover()
    res = {j: r for j in pk if j != "CW"
           for r in [A.resolve(pk[j], ASOF)] if r}
    assert len(res) == 51, len(res)
    ca = res["CA"]
    assert ca[2] == "GL_CW_20231201_V02", ca[2]
    others = sorted(j for j, r in res.items() if r[2] == "GL_CW_20231201_V02")
    assert others == ["CA"], others
    # and the parent it does NOT take
    assert "GL_CW_20270401_V01" in {p for _e, p, _x, _c in pk["CW"]}


@case("the two parents carry the same rule names — nothing added, nothing removed")
def _():
    differing, total, _g, _o, _gd, _pf, n2, n3 = D
    assert n2 == n3 == 547, (n2, n3)
    assert total == 4461, total


@case("345 of 4,461 rule bodies differ, across 43 of 547 files")
def _():
    differing, total, _g, _o, _gd, per_file, _n2, _n3 = D
    assert differing == 345, differing
    assert len(per_file) == 43, len(per_file)


@case("341 of the 345 are exactly one change: V03 adds an IsNull write guard")
def _():
    _d, _t, guard_only, other, guarded, _pf, _n2, _n3 = D
    assert guard_only == 341, guard_only
    assert other == 4, other
    assert len(guarded) == 210, len(guarded)


@case("V02 already had the idiom — on 3 DataDefs; V03 generalised it to 213")
def _():
    # The first draft asserted "V02 has no guard anywhere" and it fails: V02
    # carries 35 occurrences over exactly 3 DataDefs. The change is therefore a
    # GENERALISATION of an existing idiom, not an invention — and the three ISO
    # had already protected say what the idiom is for: the loss cost multiplier
    # must not be recomputed.
    def guarded(pkg):
        out = set()
        for f in glob.glob(os.path.join(CW, pkg, "Rules", "*.xml")):
            for m in RULE.finditer(A._read(f)):
                out.update(GUARD.findall(m.group(3)))
        return out
    a, b = guarded(V02), guarded(V03)
    assert a == {"LCM", "LCMStatCode", "LmtdProdsWithdrawalLCM"}, sorted(a)
    assert len(b) == 213, len(b)
    assert len(b - a) == 210 and not (a - b), (len(b - a), sorted(a - b))


@case("nothing but the guard makes a value write-once: every RunRule clears its cache")
def _():
    rr = cc = 0
    for f in glob.glob(os.path.join(CW, V03, "Rules", "*.xml")):
        s = A._read(f)
        rr += s.count("<rul:RunRule")
        cc += s.count('ClearCache="true"')
    assert rr == cc == 5601, (rr, cc)


@case("ERC re-evaluates coverages: 14 PremiumToReachMinCoverage groups exist")
def _():
    its = [f for f in os.listdir(os.path.join(CW, V03, "Rules"))
           if "PremiumToReachMin" in f]
    assert len(its) == 14, len(its)
    # 3 of the 4 non-guard differences live in three of them
    # The rule is named for the COVERAGE, not for the group stem — the unmanned
    # aircraft group's total is `SetTotalUnmannedAircraftPremium`, not
    # `SetTotalLimitedCovForDesignatedUnmannedAircraftPremium`. Deriving the name
    # from the stem is the same defect this project keeps catching, so the names
    # are listed.
    for stem, n in (
        ("GeneralLiabilityCyberIncidentLiabilityPremiumToReachMinCoverage",
         "SetTotalCyberIncidentLiabilityPremium"),
        ("GeneralLiabilityLossOfElectronicDataPremiumToReachMinCoverage",
         "SetTotalLossOfElectronicDataPremium"),
        ("GeneralLiabilityLimitedCovForDesignatedUnmannedAircraftPremiumToReachMinCoverage",
         "SetTotalUnmannedAircraftPremium"),
    ):
        a = _rules(V02, stem + "Rules.Rule.xml")
        b = _rules(V03, stem + "Rules.Rule.xml")
        assert n in a and n in b, (stem, n, sorted(a))
        assert a[n][1] != b[n][1], f"{n} expected to differ"


@case("every passed gate is touched — the difference is not confined to one subline")
def _():
    _d, _t, _g, _o, _gd, per_file, _n2, _n3 = D
    want = {
        "GeneralLiabilityClassificationPremOpsCoverageRules.Rule.xml": 40,
        "GeneralLiabilityClassificationProdsCompldOpsCoverageRules.Rule.xml": 33,
        "GeneralLiabilityClassificationRailroadCoverageRules.Rule.xml": 21,
        "GeneralLiabilityClassificationOwnersContractorsCoverageRules.Rule.xml": 17,
        "GeneralLiabilityClassificationLiquorCoverageRules.Rule.xml": 12,
        "GeneralLiabilityRules.Rule.xml": 55,
        "GeneralLiabilityClassificationRules.Rule.xml": 33,
    }
    for fn, n in want.items():
        assert per_file.get(fn) == n, (fn, per_file.get(fn), n)


@case("all 10 size-of-risk setters differ — and California can never reach them")
def _():
    for fn, pre in (
            ("GeneralLiabilityClassificationPremOpsCoverageRules.Rule.xml", "PremOps"),
            ("GeneralLiabilityClassificationProdsCompldOpsCoverageRules.Rule.xml",
             "ProdsCompldOps")):
        a, b = _rules(V02, fn), _rules(V03, fn)
        sor = [n for n in a if "SizeOfRisk" in n and not n.startswith("Lookup")]
        assert len(sor) == 5, (fn, sor)
        for n in sor:
            assert a[n][1] != b[n][1], (fn, n)
    # ...but CA hardcodes the flag off, so none of those ten can differ in effect
    pk = A.discover()
    ca = A.resolve(pk["CA"], ASOF)
    writers = []
    for f in glob.glob(os.path.join(ca[3], "Rules", "*.xml")):
        s = A._read(f)
        if 'ToDataDef="SizeOfRiskRatingApplies"' in s:
            writers.append(os.path.basename(f))
    assert writers, "CA must override SetSizeOfRiskRatingApplies"
    body = "".join(A._read(os.path.join(ca[3], "Rules", f)) for f in writers)
    m = re.search(r'<rul:Constant Type="string" ToDataDef="SizeOfRiskRatingApplies">'
                  r'(.*?)</rul:Constant>', body, re.S)
    assert m and m.group(1).strip() == "No", m.group(1) if m else None


@case("the oracle population is 54, and California is in it")
def _():
    # The ERC corpus holds ONE rated output, in Oklahoma. The earlier version of
    # this check asserted that and concluded the project had one oracle — a
    # search scoped to one directory, stated as a fact about everything, which
    # is the defect this project has spent a week cataloguing. `Payloads/` holds
    # 53 more.
    erc = glob.glob(os.path.join(ROOT, "**", "STC", "*Output*.json"),
                    recursive=True)
    assert len(erc) == 1, [os.path.relpath(o, ROOT) for o in erc]
    assert os.path.relpath(erc[0], ROOT).split(os.sep)[0] == "OK"
    # 518 since 2026-08-13: GL_OK_20261001_V01 ships one STC file (OI-79).
    assert len(glob.glob(os.path.join(ROOT, "**", "STC", "*.json"),
                         recursive=True)) == 518

    pay = sorted(glob.glob(os.path.join(PROJ, "Payloads", "*", "*Output*.json")))
    assert len(pay) == 53, len(pay)
    states = {os.path.basename(os.path.dirname(p)) for p in pay}
    assert len(states) == 50, sorted(states)
    assert "CA" in states, sorted(states)
    # every output is paired with its input — so each is a runnable case
    assert all(os.path.exists(p.replace("Output", "Input")) for p in pay)
    # Puerto Rico is the only ERC jurisdiction with no payload
    assert "PR" not in states


@case("California's own filed submission exercises the disabled paths only")
def _():
    pk = A.discover()
    ca = A.resolve(pk["CA"], ASOF)
    stc = glob.glob(os.path.join(ca[3], "STC", "*.json"))
    assert len(stc) == 1, stc
    s = A._read(stc[0])
    for k, v in (("SizeOfRiskRatingApplies", "No"), ("TerrorismCoverage", "No")):
        m = re.search(r'"%s"\s*:\s*"([^"]*)"' % k, s)
        assert m and m.group(1) == v, (k, m.group(1) if m else None)
    # so the payload cannot exercise size-of-risk or terrorism in CA
    assert '"CA"' in s


def main() -> int:
    print(f"California differential — as of {ASOF}, "
          f"{V02} against {V03}\n")
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
