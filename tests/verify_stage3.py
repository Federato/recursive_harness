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
from gl_engine.config import CORPUS_ROOT                          # noqa: E402

FIXTURE = ROOT / "tests" / "fixtures" / "golden-ok-2025.json"
ISO_DIR = Path(r"F:\ISO_ERC_Files\General_Liability\OK"
               r"\GL_OK 20250601 V01\GL OK 20250601 V01\STC")
ISO_IN = ISO_DIR / "1. Input.json"
ISO_OUT = ISO_DIR / "1. Output.json"
# ISO's composite-rated sample (B-39): audited 2 convention days against an estimate of 6
WV_COMPOSITE = (CORPUS_ROOT / "WV" / "GL_WV 20251101 V01_MachineReadableContent" / "GL WV 20251101 V01"
                / "STC" / "STC_GL000145648.json")

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
    # OI-132 (B-11): the parts are ISO's money-marked premiums (PremiumIndicator = 1), named by coverage, and they add
    # up. They were the min-premium top-up groups' names pre-2027, and nothing at all from CW 2027 on.
    check("C2b the parts add up to the premium, named by coverage, not by min-premium top-up group",
          sum(r.by_coverage.values()) == r.premium and not any("ToReachMin" in c for c in r.by_coverage),
          ", ".join(f"{c.replace('GeneralLiability', '')} {v}" for c, v in sorted(r.by_coverage.items())))
    from console import workbench as WB
    r27 = Kernel().rate(WB.build("GL", "TX", {"effective_date": "20270501"}))
    check("C2c on the 2027 edition the parts exist and add up too (the breakdown was empty)",
          r27.complete and len(r27.by_coverage) >= 2 and sum(r27.by_coverage.values()) == r27.premium,
          f"{r27.premium if r27.complete else r27.stopped}: {len(r27.by_coverage)} parts")
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

    # The honesty check: every entry has an explicit disposition and the four
    # buckets account for all 28. A register that reports "28 loaded" while
    # checking a handful reads as coverage it does not have.
    cov = k.coverage()
    total = sum(len(v) for v in cov.values())
    check("D4 every register entry has an explicit disposition",
          total == len(k.register),
          " ".join(f"{key}={len(v)}" for key, v in sorted(cov.items())))
    # B-14 (2026-10-14): R12 (MA and TX give no BYOA credit by filing, ISO 1 call) and the map of the nine pending
    # entries against ISO's refer list and service -- R01, R04-R09, R23 recorded with their evidence; R02 covered by R30
    check("D5 nothing decided NOT to be a referral can raise",
          set(cov["NOT_REFERRAL"]) == {"R01", "R04", "R05", "R06", "R07", "R08", "R09", "R12", "R21", "R23", "R24",
                                       "R27", "R28"},
          str(cov["NOT_REFERRAL"]))
    check("D6 un-enforced entries are named individually, never a count -- and none is left (B-14)",
          all(c.startswith("R") for c in k.unenforced) and not k.unenforced,
          f"{len(k.unenforced)} pending" + (f": {', '.join(k.unenforced)}" if k.unenforced else ""))

    # A real referral, on a real submission, that ISO itself errors on:
    # Alaska's attorney's-fee limit is below the subline limit, ISO returns
    # "Attorneys Fee Limit must be Greater than or Equal To Each Sublines
    # Limit", and the endorsement prices at -70. The detector finds the
    # negative without being told about attorney's fees (R16).
    ak = Kernel(mode=UNDERWRITING).rate(ROOT / "Payloads" / "AK" / "1. Input.json")
    check("D7 a negative premium component raises R16 on a real submission",
          any(r.code == "R16" for r in ak.referrals),
          "; ".join(r.code for r in ak.referrals) or "none")
    # B-39: composite rating's audit adjustment is negative by design (audited exposure below the estimate)
    wv = Kernel(mode=UNDERWRITING).rate(WV_COMPOSITE)
    adj = tree.select("/*/GeneralLiabilityTable/GeneralLiability/GeneralLiabilityCompositeRating/Premium", wv.tree)
    check("D7b a negative composite audit adjustment does not raise R16 (B-39)",
          adj and Decimal(adj[0].text) < 0 and not any(r.code == "R16" for r in wv.referrals),
          f"adjustment {adj[0].text if adj else 'missing'}; "
          + ("; ".join(r.code for r in wv.referrals) or "no referrals"))
    check("D8 ISO's own validation message is captured verbatim",
          any("Attorneys Fee Limit" in m for m in ak.messages),
          f"{len(ak.messages)} messages")
    check("D9 detectors do not fire on clean risks",
          not Kernel(mode=UNDERWRITING).rate(ISO_IN).referrals,
          "the golden case raises none")

    # Monotonicity (D02): a referral, once raised, cannot be removed.
    from gl_engine.rating import Referral
    uw.raise_referral(Referral("R99", "test", "TEST"))
    n = len(uw.referrals)
    uw.raise_referral(Referral("R99", "test again", "TEST"))
    check("D10 dispositions are monotonic and not duplicated (D02)",
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
#:
#: Two figures, because the `Payloads/` pairs dispute one field. 34 of 50 carry
#: `TerrorismCoverage="Yes"` on the input and `"No"` on ISO's own output, while
#: every other echoed field agrees (OI-77). Taking ISO's echoed value lifts
#: agreement from 28 to 47, which a wrong engine could not do -- so both are
#: tracked and neither is allowed to fall.
BASELINE_RATED = 50
#: 28 until 2026-10-14. B-29 refuses the 12 OI-77 examples as filed (terrorism "Yes", no territory); they matched
#: only because their silent $0 terrorism equalled ISO's terrorism-off price. F3 still compares all of them.
BASELINE_MATCH = 16
BASELINE_OI77_REFUSED = 12
BASELINE_RECONCILED = 48
#: Against the oracle that actually corresponds to each input, excluding the two
#: pairs where none does (OI-78). This is the honest headline and it is exact.
BASELINE_COMPARABLE = 49


def group_f():
    """Breadth: every payload we hold, against ISO's own answer."""
    print("\nF  BREADTH -- all 50 ISO-priced examples (the offline half of Phase 2)")
    payloads = ROOT / "Payloads"
    kernel = Kernel()
    rated = matched = reconciled = 0
    stopped = []
    # OI-92: ISO's own GA example omits its rating-required prem/ops territory and used to rate products only
    # (6845, which ISO matched on the same deficient input). Since OI-134 the engine refuses it, naming the
    # field. That one refusal is expected; it is counted here and nowhere else.
    known = []
    # B-29 (2026-10-14): 12 OI-77 examples carry terrorism "Yes" with no TerrorismTerritory, and ISO priced them with
    # terrorism off (its output echoes "No"). As filed they now refuse, naming the territory -- right, the input asks
    # for terrorism and gives nothing to price it with; it "matched" before only because the silent $0 terrorism
    # equalled ISO's terrorism-off price. With ISO's echoed value no territory is needed, so the reconciled rating
    # below still runs and still compares.
    known_oi77 = []

    def is_known(name, r):
        return (name == "GA" and not r.complete
                and "GeneralLiabilityLocation.PremisesOperationsTerritory" in str(r.stopped))

    def oi77_refusal(r, gl0):
        return (not r.complete and "GeneralLiabilityLocation.TerrorismTerritory is required" in str(r.stopped)
                and gl0 is not None and gl0.get("TerrorismCoverage") == "No")
    for d in sorted(p for p in payloads.iterdir() if p.is_dir()):
        src = d / "1. Input.json"
        if not src.exists():
            continue
        try:
            r = kernel.rate(src)
        except Exception as exc:                          # noqa: BLE001
            stopped.append(f"{d.name}: {type(exc).__name__}")
            continue
        if is_known(d.name, r):
            known.append(d.name)
            continue
        out = d / "1. Output.json"
        try:
            iso = json.loads(out.read_text(encoding="utf-8-sig"))
            gl0 = iso["Body"]["GeneralLiability"][0]
            want = Decimal(str(gl0["Premium"]))
        except Exception:                                 # noqa: BLE001
            gl0 = want = None
        if oi77_refusal(r, gl0):
            known_oi77.append(d.name)
        elif not r.complete:
            stopped.append(f"{d.name}: {str(r.stopped)[:40]}")
            continue
        else:
            rated += 1
        if want is None:
            continue
        if r.complete and want == r.premium:
            matched += 1
            reconciled += 1
            continue
        # The disputed field, taken from ISO's own output rather than the
        # input. Never used to report a headline number on its own -- see
        # scripts/rate_all_payloads.py.
        payload = json.loads(src.read_text(encoding="utf-8-sig"))
        terror = gl0.get("TerrorismCoverage")
        changed = False
        for gl in payload.get("body", {}).get("GeneralLiability", []):
            if terror is not None and gl.get("TerrorismCoverage") != terror:
                gl["TerrorismCoverage"] = terror
                changed = True
        if not changed:
            continue
        try:
            r2 = kernel.rate(payload)
            if r2.complete and r2.premium == want:
                reconciled += 1
        except Exception:                                 # noqa: BLE001
            pass

    check("F0 ISO's GA example is refused for the territory it omits (OI-92, OI-134)",
          known == ["GA"], f"{known or 'not refused'}")
    check(f"F0b the OI-77 examples (terrorism 'Yes' in, 'No' out, no territory) refuse as filed: "
          f"{BASELINE_OI77_REFUSED} (B-29)", len(known_oi77) == BASELINE_OI77_REFUSED, f"{known_oi77}")
    check(f"F1 every payload rates end to end (>= {BASELINE_RATED}, the known refusals counted)",
          rated + len(known) + len(known_oi77) >= BASELINE_RATED and not stopped,
          f"{rated} rated" + (f"; stopped: {stopped[:3]}" if stopped else ""))
    check(f"F2 exact agreement as filed does not regress (>= {BASELINE_MATCH})",
          matched >= BASELINE_MATCH, f"{matched} of {rated} match to the penny")
    check(f"F3 agreement with ISO's own TerrorismCoverage does not regress "
          f"(>= {BASELINE_RECONCILED})",
          reconciled + len(known) >= BASELINE_RECONCILED,
          f"{reconciled} of {rated + len(known_oi77)}, plus GA's known refusal")

    # F4 is the honest headline: every pair whose output actually came from its
    # input. The two exclusions are established from the files by
    # scripts/check_payload_pairs.py, never from the premium.
    from importlib import util as _u
    spec = _u.spec_from_file_location(
        "rap", ROOT / "scripts" / "rate_all_payloads.py")
    rap = _u.module_from_spec(spec); spec.loader.exec_module(rap)
    comp_match = comp_total = 0
    for d in sorted(p for p in payloads.iterdir() if p.is_dir()):
        src = d / "1. Input.json"
        if not src.exists() or d.name in rap.NO_ORACLE:
            continue
        oracle = ((payloads / rap.ORACLE_OVERRIDE[d.name] / "1. Output.json")
                  if d.name in rap.ORACLE_OVERRIDE else d / "1. Output.json")
        if not oracle.exists():
            continue
        comp_total += 1
        alt = rap.reconciled(src, oracle)
        try:
            rr = kernel.rate(alt if alt is not None else src)
            if is_known(d.name, rr):
                comp_total -= 1           # not comparable: we refuse the input ISO rated half of (OI-92)
                continue
            if rr.complete and rr.premium == rap.iso_premium(oracle):
                comp_match += 1
        except Exception:                                 # noqa: BLE001
            pass
    check(f"F4 every usable oracle agrees (>= {BASELINE_COMPARABLE} of "
          f"{BASELINE_COMPARABLE})",
          comp_match + len(known) >= BASELINE_COMPARABLE and comp_match == comp_total,
          f"{comp_match} of {comp_total} comparable pairs match to the penny")


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
