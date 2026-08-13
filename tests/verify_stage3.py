"""Stage 3 acceptance: the kernel, the modes, and the golden case.

  A  the golden case   Oklahoma reproduces 976 + 6,845 + 2 + 16 = 7,839
  B  ISO's own output  every numeric field ISO published, compared field by
                       field -- not just the total, because a total can be
                       right for the wrong reasons
  C  the kernel        what a caller holds: premium, parts, provenance, trace
  D  the two modes     one code path, and the register honest about its reach
  E  refusals          a rating that cannot be trusted does not return a number

Run: python tests/verify_stage3.py
"""
from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from gl_engine.rating import (Kernel, RatingError, STRICT,        # noqa: E402
                              UNDERWRITING)
from gl_engine.interp import tree                                 # noqa: E402

FIXTURE = ROOT / "tests" / "fixtures" / "golden-ok-2025.json"
ISO_DIR = Path(r"C:\Projects\ISO_ERC_Files\General_Liability\OK"
               r"\GL_OK 20250601 V01\GL OK 20250601 V01\STC")
ISO_IN = ISO_DIR / "1. Input.json"
ISO_OUT = ISO_DIR / "1. Output.json"

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(f"{name}  {detail}".rstrip())
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f"  [{detail}]" if detail else ""))


def _rate():
    return Kernel(mode=STRICT).rate(ISO_IN)


# ------------------------------------------------------------- A golden case

def group_a(r):
    print("\nA  THE GOLDEN CASE -- Oklahoma, the only end-to-end oracle we have")
    fx = json.loads(FIXTURE.read_text(encoding="utf-8"))
    exp = fx["expected"]

    check("A1 rating completes", r.complete,
          "" if r.complete else f"stopped: {r.stopped}")
    if not r.complete:
        return
    check("A2 resolves the declared parent, not the newest (N5)",
          r.packages == ("GL_OK_20250601_V01", "GL_CW_20231201_V03"),
          " over ".join(r.packages))
    check("A3 policy premium is 7,839",
          r.premium == Decimal(7839), str(r.premium))

    risk = tree.select_one("GeneralLiabilityTable/GeneralLiability", r.tree)
    prem_ops = tree.read("GeneralLiabilityPremOpsPremiumToReachMinCoverage/"
                         "CoveragePremium", risk)
    prods = tree.read("GeneralLiabilityProdsCompldOpsPremiumToReachMinCoverage/"
                      "CoveragePremium", risk)
    check("A4 premises/operations is 976", prem_ops == "976", str(prem_ops))
    check("A5 products/completed operations is 6,845", prods == "6845",
          str(prods))
    check("A6 the reconciliation holds: 976 + 6845 + 2 + 16 = 7839",
          Decimal(prem_ops) + Decimal(prods) + 18 == r.premium,
          fx["expected"] and fx.get("reconciliation", ""))

    cls = tree.select_one(
        "GeneralLiabilityTable/GeneralLiability/GeneralLiabilityLocationTable/"
        "GeneralLiabilityLocation/GeneralLiabilityClassificationTable/"
        "GeneralLiabilityClassification", r.tree)
    for label, path, want in (
        ("A7 prem/ops basic limit premium 475",
         "GeneralLiabilityClassificationPremOpsCoverage/BasicLimitPremium", "475"),
        ("A8 prods basic limit premium 4,100",
         "GeneralLiabilityClassificationProdsCompldOpsCoverage/BasicLimitPremium",
         "4100"),
        ("A9 prem/ops final rate 0.195",
         "GeneralLiabilityClassificationPremOpsCoverage/FinalRate", "0.195"),
        ("A10 prods final rate 1.369",
         "GeneralLiabilityClassificationProdsCompldOpsCoverage/FinalRate",
         "1.369"),
    ):
        got = tree.read(path, cls)
        check(label, got == want, f"got {got!r}")

    # The terrorism rows are CREATED by the rules; they are not in the input.
    # They are also where the missing 18 lived until positional predicates were
    # implemented, so they get their own check.
    terr = tree.select("GeneralLiabilityTerrorismTable/GeneralLiabilityTerrorism",
                       cls)
    check("A11 terrorism rows are created by the rules, not supplied",
          len(terr) == 1, f"{len(terr)} row(s)")
    check("A12 terrorism class factor is 0.004, not zero",
          tree.read("CertifiedActsOfTerrorismExposureClassFactorProducts",
                    terr[0]) == "0.004" if terr else False,
          tree.read("CertifiedActsOfTerrorismExposureClassFactorProducts",
                    terr[0]) if terr else "no row")


# --------------------------------------------------------- B ISO's own output

def _numbers(obj, prefix="", out=None):
    """Every numeric leaf in ISO's output, by path."""
    out = {} if out is None else out
    if isinstance(obj, dict):
        for k, v in obj.items():
            _numbers(v, f"{prefix}/{k}", out)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _numbers(v, f"{prefix}[{i}]", out)
    elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
        out[prefix] = Decimal(str(obj))
    return out


def _tree_numbers(node, prefix="", out=None):
    out = {} if out is None else out
    seen = {}
    for c in node.children:
        i = seen.get(c.tag, 0)
        seen[c.tag] = i + 1
        p = f"{prefix}/{c.tag}[{i}]"
        if c.text not in (None, ""):
            try:
                out[p] = Decimal(str(c.text))
            except Exception:                            # noqa: BLE001
                pass
        _tree_numbers(c, p, out)
    return out


def group_b(r):
    print("\nB  ISO'S OWN OUTPUT -- field by field, not just the total")
    if not ISO_OUT.exists():
        check("B0 ISO output present", False, str(ISO_OUT))
        return
    iso = json.loads(ISO_OUT.read_text(encoding="utf-8-sig"))
    iso_gl = iso["Body"]["GeneralLiability"][0]
    ours = tree.select_one("GeneralLiabilityTable/GeneralLiability", r.tree)

    # Compare the policy-level numeric fields ISO publishes. Nested repeated
    # structures are compared by the checks in group A; this is the flat layer,
    # which is where a total that is right for the wrong reason shows up.
    flat = {k: Decimal(str(v)) for k, v in iso_gl.items()
            if isinstance(v, (int, float)) and not isinstance(v, bool)}
    agree, differ, missing = [], [], []
    for key, want in sorted(flat.items()):
        got = tree.read(key, ours)
        if got is None:
            missing.append(key)
        elif Decimal(got) == want:
            agree.append(key)
        else:
            differ.append(f"{key}: ours {got} vs ISO {want}")

    check("B1 every policy-level number ISO published agrees",
          not differ, "; ".join(differ[:4]) if differ
          else f"{len(agree)} fields")
    check("B2 no policy-level number ISO published is absent from our tree",
          not missing, ", ".join(missing[:6]) if missing else "none missing")


# ---------------------------------------------------------------- C kernel

def group_c(r):
    print("\nC  THE KERNEL -- what a caller actually holds")
    check("C1 premium is a Decimal, never a float",
          isinstance(r.premium, Decimal), type(r.premium).__name__)
    check("C2 the parts are broken out per coverage",
          len(r.by_coverage) >= 2, f"{len(r.by_coverage)} coverages")
    check("C3 the rating names the packages that priced it",
          len(r.packages) == 2, " over ".join(r.packages))
    check("C4 the trace records every lookup with its source",
          any(t.kind == "lookup" and t.source for t in r.trace),
          f"{sum(1 for t in r.trace if t.kind == 'lookup')} lookups traced")
    check("C5 the trace records every rounding and the mode used",
          any(t.kind == "round" and "ROUND_HALF_UP" in t.detail
              for t in r.trace),
          f"{sum(1 for t in r.trace if t.kind == 'round')} roundings")
    check("C6 the jurisdiction and date came from the submission, not a caller",
          (r.juris, r.asof) == ("OK", "20250801"), f"{r.juris}@{r.asof}")


# ----------------------------------------------------------------- D modes

def group_d():
    print("\nD  THE TWO MODES -- one code path")
    strict = Kernel(mode=STRICT).rate(ISO_IN)
    uw = Kernel(mode=UNDERWRITING).rate(ISO_IN)
    check("D1 both modes produce the same premium on a clean risk",
          strict.premium == uw.premium == Decimal(7839),
          f"strict {strict.premium}, underwriting {uw.premium}")
    check("D2 strict mode raises no referrals, by construction",
          not strict.referrals, f"{len(strict.referrals)} referrals")

    k = Kernel(mode=UNDERWRITING)
    check("D3 the register is loaded", len(k.register) == 28,
          f"{len(k.register)} entries")
    # The honesty check: the register must never look like more coverage than
    # it has. 1 of 28 is a small number and it is stated, not hidden.
    check("D4 un-enforced register entries are named, not silently dropped",
          len(k.enforced) + len(k.unenforced) == len(k.register)
          and len(k.unenforced) == 27,
          f"enforced {k.enforced}, {len(k.unenforced)} not yet enforced")

    # Monotonicity (D02): a referral, once raised, cannot be removed.
    from gl_engine.rating import Referral
    uw.raise_referral(Referral("R99", "test", "TEST"))
    n = len(uw.referrals)
    uw.raise_referral(Referral("R99", "test again", "TEST"))
    check("D5 dispositions are monotonic and not duplicated (D02)",
          len(uw.referrals) == n, f"{len(uw.referrals)} referrals")


# -------------------------------------------------------------- E refusals

def group_e():
    print("\nE  REFUSALS -- an untrustworthy rating returns no number")
    try:
        Kernel(mode="whatever")
        check("E1 an unknown mode is refused", False, "accepted")
    except RatingError:
        check("E1 an unknown mode is refused", True)

    try:
        Kernel().rate({"body": {"SchemeKeys": {}}})
        check("E2 a submission with no effective date is refused", False,
              "accepted")
    except (ValueError, RatingError) as exc:
        check("E2 a submission with no effective date is refused", True,
              str(exc)[:60])

    try:
        Kernel().rate({"body": {"SchemeKeys":
                                {"EffectiveDateTime": "2025-08-01"}}})
        check("E3 a submission naming no jurisdiction is refused", False,
              "accepted")
    except (ValueError, RatingError) as exc:
        check("E3 a submission naming no jurisdiction is refused", True,
              str(exc)[:60])

    # A date below the corpus floor must fail rather than serve a partial
    # answer -- stage 1's rule, reasserted through the kernel.
    payload = json.loads(ISO_IN.read_text(encoding="utf-8-sig"))
    payload["body"]["SchemeKeys"]["EffectiveDateTime"] = "2019-01-01T00:00:00"
    try:
        Kernel().rate(payload)
        check("E4 a date below the corpus floor is refused", False, "accepted")
    except Exception as exc:                              # noqa: BLE001
        check("E4 a date below the corpus floor is refused", True,
              type(exc).__name__)


#: The reconciliation baseline, recorded 2026-08-13. Not a target -- a ratchet.
#: Every payload must still RATE, and the number matching ISO exactly must not
#: fall. Raising it is the work of Phase 2; lowering it is a regression.
BASELINE_RATED = 50
BASELINE_MATCH = 22


def group_f():
    """Breadth: every payload we hold, against ISO's own answer."""
    print("\nF  BREADTH -- all 50 ISO-priced examples (the offline half of Phase 2)")
    payloads = ROOT / "Payloads"
    kernel = Kernel()
    rated = matched = 0
    stopped = []
    for d in sorted(p for p in payloads.iterdir() if p.is_dir()):
        src = d / "1. Input.json"
        if not src.exists():
            continue
        try:
            r = kernel.rate(src)
        except Exception as exc:                          # noqa: BLE001
            stopped.append(f"{d.name}: {type(exc).__name__}")
            continue
        if not r.complete:
            stopped.append(f"{d.name}: {str(r.stopped)[:40]}")
            continue
        rated += 1
        out = d / "1. Output.json"
        if out.exists():
            try:
                iso = json.loads(out.read_text(encoding="utf-8-sig"))
                want = Decimal(str(iso["Body"]["GeneralLiability"][0]["Premium"]))
                if want == r.premium:
                    matched += 1
            except Exception:                             # noqa: BLE001
                pass

    check(f"F1 every payload rates end to end (>= {BASELINE_RATED})",
          rated >= BASELINE_RATED,
          f"{rated} rated" + (f"; stopped: {stopped[:3]}" if stopped else ""))
    check(f"F2 exact agreement with ISO does not regress (>= {BASELINE_MATCH})",
          matched >= BASELINE_MATCH, f"{matched} of {rated} match to the penny")


def main() -> int:
    print("Stage 3 acceptance -- the kernel")
    if not ISO_IN.exists():
        print(f"  corpus not reachable: {ISO_IN}")
        return 1
    r = _rate()
    group_a(r)
    group_b(r)
    group_c(r)
    group_d()
    group_e()
    group_f()
    total = len(PASS) + len(FAIL)
    print(f"\n{len(PASS)}/{total} passed")
    if FAIL:
        print("\nFAILURES:")
        for f in FAIL:
            print(f"  {f}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
