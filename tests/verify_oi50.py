"""OI-50 — Limited Product Withdrawal Expense, pinned.

The chain derived in [gate 365 §9](../docs/gates/GATE-365-WITHDRAWAL-LOED-CYBER.md),
as assertions. It is the smallest of the three owed items and the only rating
chain in the project with a countrywide-only derivation and **zero state
arithmetic deviation** — which is what made it safe to do last.

Two figures here correct earlier notes, and both corrections are the same shape:
a count taken over a subset and stated over the whole.

  * "an 11-rule chain"        -> 11 RATING rules; the coverage is **54** across
                                five DataDefGroups
  * "0 of 51 override any"    -> holds, and is stronger than it looked: 0 of 51
                                touch the 11 rating rules, and only **Texas**
                                touches the coverage groups at all — with
                                `InitializeRuleSet` and two stat-code lookups.
                                (A first re-measurement said 27 of 51. It matched
                                `ErcProcess`/`InitializeRuleSet` BY NAME anywhere
                                in the package; those names exist in hundreds of
                                groups. Membership is by group.)

    python tests/verify_oi50.py
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

ASOF = "20260812"
CWDIR = os.path.join(A.ROOT, "countrywide", "GL CW 20260101 V01")
RULE = re.compile(
    r'<rul:Rule Name="([^"]+)"[^>]*?DataDefGroup="([^"]+)"[^>]*>(.*?)</rul:Rule>',
    re.S)

CHAIN = [
    "SetLmtdLCM", "SetLmtdProductWithdrawlFactor",
    "SetLmtdProdsWithdrawalBaseRate", "SetLimitedProductWithdrawalAggregateAndDeductibleLimits",
    "SetLmtdProdsWithdrawalIncreasedLimitsFactor", "SetLmtdCSLILF",
    "SetLmtdDeductibleFactor", "SetLmtdFinalILF",
    "SetLmtdProdsWithdrawalFinalRate", "SetLmtdProdsWithdrawalPremium",
    "SetHighestLmtdProdsWithdrawalFinalILFFlag",
]
GUARDS = [
    "DoMessageLimitedProductWithdrawalEndt",
    "DoMessageMustEnterLimitedProductWithdrawalDeductibleFactorOverride",
    "DoMessageProdWithdrawalDedFactorCannotExceedPWILF",
    "DoMessageTheLimitedProductWithdrawalCoveragepremiumCannotBeANegativePremium",
]
GROUPS = [
    "GeneralLiabilityLimitedProductWithdrawalExpenseCoverage",
    "GeneralLiabilityLimitedProductWithdrawalExpenseEndtPolLvl",
    "GeneralLiabilityLimitedProductWithdrawalExpenseEndtPremiumToReachMinCoveragePolLvl",
]

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


CW = _rules(CWDIR)


@case("the coverage is 54 rules across five groups, not the 11 first recorded")
def _():
    chain = [k for k in CW if k[0] == "GeneralLiabilityClassification"
             and k[1] in CHAIN]
    assert len(chain) == 11, sorted(k[1] for k in chain)
    guards = [k for k in CW if k[1] in GUARDS]
    assert len(guards) == 4, sorted(k[1] for k in guards)
    grouped = [k for k in CW if k[0] in GROUPS]
    assert len(grouped) == 39, len(grouped)
    assert 11 + 4 + 39 == 54
    assert len(CW) == 4557, len(CW)


@case("the rating chain is exact, in order, and ends in a 0dp premium")
def _():
    g = "GeneralLiabilityClassification"
    br = CW[(g, "SetLmtdProdsWithdrawalBaseRate")]
    # base rate = (sibling loss cost | ELP) x LCM x product-withdrawal factor
    assert "GeneralLiabilityClassificationProdsCompldOpsCoverage/ProdsCompldOpsLossCost" in br
    assert "FinalProdsCompldOpsELP" in br
    assert "LmtdProdsWithdrawalLCM" in br
    assert "LmtdProdsWithdrawalProductWithdrawalFactor" in br

    ilf = CW[(g, "SetLmtdFinalILF")]
    assert re.search(r'<rul:Subtract[^>]*ToDataDef="LmtdProdsWithdrawalFinalILF"', ilf)

    fr = CW[(g, "SetLmtdProdsWithdrawalFinalRate")]
    assert re.search(r'ToDataDef="LmtdProdsWithdrawalFinalRate"[^>]*DecimalPlaces="3"', fr)

    pr = CW[(g, "SetLmtdProdsWithdrawalPremium")]
    assert re.search(r'ToDataDef="LmtdProdsWithdrawalPremium"[^>]*DecimalPlaces="0"', pr)
    # the divisor is chosen by the SAME filed nine-value premium-basis list
    for basis in ("Admissions", "Area", "Gallons", "Gross Sales", "Passenger Days",
                  "Payroll", "Total Cost", "Total Operating Expenses", "Vehicles"):
        assert f">{basis}<" in pr, basis


@case("it reads the sibling group's loss cost — E18, third instance")
def _():
    br = CW[("GeneralLiabilityClassification", "SetLmtdProdsWithdrawalBaseRate")]
    sib = re.findall(r'FromDataDef="(GeneralLiabilityClassification[A-Za-z]+/[A-Za-z]+)"', br)
    assert sib, br[:200]
    assert any("ProdsCompldOpsCoverage/ProdsCompldOpsLossCost" in s for s in sib), sib


@case("the MISSPELLED factor table is the one this coverage reads, and they differ on values")
def _():
    body = CW[("GeneralLiabilityClassification", "SetLmtdProductWithdrawlFactor")]
    assert 'Rule="LookupProductWithdrawlFactor"' in body, "must read the misspelled lookup"
    mis = A.table(CWDIR, "Rate Tables", "ProductWithdrawlFactor.RateTable.csv")
    ok = A.table(CWDIR, "Rate Tables", "ProductWithdrawalExpensesFactor.RateTable.csv")
    assert [r[-1] for r in mis] == ["0.2", "0.15", "0.1"], mis
    assert [r[-1] for r in ok] == ["0.25", "0.19", "0.13"], ok
    assert mis != ok, "normalising the spelling would merge two different tables"


@case("four guards, including the corpus's only negative-premium check")
def _():
    found = {k[1]: CW[k] for k in CW if k[1] in GUARDS}
    assert len(found) == 4, sorted(found)
    neg = found["DoMessageTheLimitedProductWithdrawalCoveragepremiumCannotBeANegativePremium"]
    assert "<rul:LessThan>" in neg
    pw = found["DoMessageProdWithdrawalDedFactorCannotExceedPWILF"]
    assert "cannot exceed the Limited Product Withdrawal Increased Limits Factor" in pw
    # and it is the ONLY negative-premium guard anywhere countrywide
    allneg = [k[1] for k in CW if k[1].startswith("DoMessage")
              and "NegativePremium" in k[1]]
    assert allneg == [
        "DoMessageTheLimitedProductWithdrawalCoveragepremiumCannotBeANegativePremium"], allneg


@case("N8 at its cleanest: 0 of 11 countrywide editions, 51 of 51 jurisdictions")
def _():
    T = "ProductWithdrawalExpensesAndLiabilityIncrdLimitFactor.RateTable.csv"
    pk = A.discover()
    cw = {p: c for _e, p, _x, c in pk["CW"]}
    assert len(cw) == 11, len(cw)   # 11 since GL_CW_20261001_V01 (OI-79)
    for p, c in cw.items():
        assert A.table(c, "Rate Tables", T) == [], p
    res = {j: r for j in pk if j != "CW" for r in [A.resolve(pk[j], ASOF)] if r}
    assert len(res) == 51, len(res)
    counts = {j: len(A.table(r[3], "Rate Tables", T)) for j, r in res.items()}
    assert all(n == 36 for n in counts.values()), \
        {j: n for j, n in counts.items() if n != 36}


@case("zero state deviation on the arithmetic — 1 of 51 touches the coverage at all")
def _():
    pk = A.discover()
    res = {j: r for j in pk if j != "CW" for r in [A.resolve(pk[j], ASOF)] if r}
    touch_chain, touch_any = [], []
    for j, r in sorted(res.items()):
        hit_chain = hit_any = False
        for f in glob.glob(os.path.join(r[3], "Rules", "*.xml")):
            s = A._read(f)
            if "Lmtd" not in s and "LimitedProductWithdrawal" not in s:
                continue
            for m in RULE.finditer(s):
                if m.group(1) in CHAIN or m.group(1) in GUARDS:
                    hit_chain = True
                # membership is by GROUP, never by rule name: `ErcProcess` and
                # `InitializeRuleSet` exist in hundreds of groups, and matching
                # them by name anywhere in the package inflated this from 1 to 27
                # on the first attempt.
                if m.group(2) in GROUPS:
                    hit_any = True
        if hit_chain:
            touch_chain.append(j)
        if hit_any:
            touch_any.append(j)
    assert touch_chain == [], touch_chain
    assert touch_any == ["TX"], touch_any


def main() -> int:
    print(f"OI-50 — Limited Product Withdrawal Expense, as of {ASOF}, "
          f"against GL_CW_20260101_V01\n")
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
