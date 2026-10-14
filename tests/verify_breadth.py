"""Breadth acceptance: the variant harness, offline. **OI-87.**

  A  the catalogue     it builds, it is grouped, and every variant says what it
                       exercises
  B  declared values   every value a variant sets is in ISO's own declared set,
                       and a value that is not is REFUSED at build time
  C  the constraints   the two the declaration supplied and no reading of the
                       sample submission would have given: the deductibles are
                       mutually exclusive, and terrorism is located two
                       different ways
  D  state narrowing   a variant illegal in a jurisdiction is not built there,
                       and the refusal names the declaration
  E  it rates          every buildable variant either rates through our engine
                       or fails in a way the report names -- and a variant that
                       leaves the premium at the base is reported, not passed

**No live calls.** The live half of breadth is `scripts/breadth.py --live`, and a
test suite that spent 34 calls on ISO's service every time it ran would not get
run. What is checked here is everything that can be wrong before the call.

Run: python tests/verify_breadth.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from breadth import (BreadthError, Declared, catalogue,      # noqa: E402
                     classifications, gl, locations)
from gl_engine import EditionResolver                        # noqa: E402
from gl_engine.config import CLASS_BASIS_CLIFF, CORPUS_ROOT   # noqa: E402
from gl_engine.rating import Kernel, STRICT, UNDERWRITING    # noqa: E402
from gl_engine.schema import validate                        # noqa: E402

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(f"{name}  {detail}".rstrip())
    print(f"  {'PASS' if cond else 'FAIL'}  {name}"
          + (f"  [{detail}]" if detail else ""))


def base_for(juris: str) -> dict:
    p = ROOT / "Engine_Payloads" / juris / "submission.json"
    return json.loads(p.read_text(encoding="utf-8"))


def _ok_stc_input(class_code: str | None = None) -> dict:
    """The OK golden fixture's own ISO-filed sample submission, optionally
    with its classification's `ClassCode` swapped -- for OI-95, to reach a
    class ISO's own tables mark `Company` (no published ELP) rather than the
    fixture's own `50017` (`Industry`, ELP `0.82`, already confirmed correct)."""
    p = (CORPUS_ROOT / "OK" / "GL_OK 20250601 V01" / "GL OK 20250601 V01"
         / "STC" / "1. Input.json")
    data = json.loads(p.read_text(encoding="utf-8-sig"))
    if class_code is not None:
        cls = (data["body"]["GeneralLiability"][0]["GeneralLiabilityLocation"][0]
               ["GeneralLiabilityClassification"][0])
        cls["ClassCode"] = class_code
    return data


def _loss_cost_nodes(kernel, juris):
    """Every `*LossCost` node in a rated tree, for the zero-is-legal check."""
    import variants as VV
    from gl_engine.interp import tree as _t
    r = kernel.rate(VV.build({"size_of_risk": "Yes"}, VV.Declared(juris)))
    out = []

    def walk(n):
        for c in n.children:
            if c.tag.endswith("LossCost"):
                out.append(c)
            walk(c)

    walk(r.tree)
    return out


def _terrorism_rates_without_a_place() -> bool:
    """OI-91: terrorism on, no location field sent, premium must move.

    The claim this pins is that the 36 jurisdictions filing no
    `TerrorismTerritory` are **not** blocked -- countrywide reads no terrorism
    location, so there is nothing to send rather than something we cannot
    supply. If this ever fails, the harness was right to refuse and OI-91's
    closure was wrong.
    """
    import copy
    kernel = Kernel(mode=STRICT, resolver=EditionResolver())
    for juris in ("AK", "VT", "WY", "MT"):
        base = base_for(juris)
        on = copy.deepcopy(base)
        gl(on)["TerrorismCoverage"] = "Yes"
        before, after = kernel.rate(copy.deepcopy(base)), kernel.rate(on)
        if not (after.complete and before.complete
                and after.premium > before.premium):
            return False
    return True


def main() -> int:
    print("Breadth acceptance -- the variant harness (no live calls)")

    ok = Declared("OK")
    cat = catalogue(ok)
    base = base_for("OK")

    print("\nA  THE CATALOGUE")
    check("A1 it builds", len(cat) >= 15, f"{len(cat)} variants")
    groups = sorted({v.group for v in cat})
    check("A2 the groups are the ones the backlog names",
          {"deductible", "structure", "limits", "form", "plans", "terrorism",
           "sizeofrisk"} <= set(groups), ", ".join(groups))
    check("A3 every variant says what it exercises",
          all(len(v.exercises) > 20 for v in cat),
          "no variant exists without a stated reason")
    check("A4 names are unique", len({v.name for v in cat}) == len(cat))

    print("\nB  EVERY VALUE IS ISO'S, AND A WRONG ONE IS REFUSED")
    # The whole design rests on this: the harness cannot invent a value.
    try:
        ok.require("GeneralLiability", "PremOpsPDDeductible", "6,500 Per Fortnight")
        refused = False
    except BreadthError:
        refused = True
    check("B1 an undeclared value is refused at build time", refused,
          "Declared.require raises rather than sending it")
    check("B2 a declared value passes",
          ok.require("GeneralLiability", "PremOpsPDDeductible",
                     "5,000 Per Occurrence") == "5,000 Per Occurrence")

    # And the built submissions have to pass ISO's own schema, not just ours.
    illegal = []
    for v in cat:
        try:
            p = v.payload(base, ok)
        except BreadthError:
            continue
        errs = [f for f in validate(p, ok.schema) if f.level == "error"]
        if errs:
            illegal.append(f"{v.name}: {errs[0]}")
    check("B3 no built variant breaks ISO's declared schema", not illegal,
          "; ".join(illegal)[:150] or f"{len(cat)} variants checked")

    print("\nC  THE TWO CONSTRAINTS THE DECLARATION SUPPLIED")
    # C1: with BI or PD set, the only legal combined deductible is none. This is
    # the constraint that would have looked like an engine defect.
    with_none = ok.dependent("GeneralLiability", "PremOpsBIPDDeductible",
                             "No Deductible")
    with_set = ok.dependent("GeneralLiability", "PremOpsBIPDDeductible",
                            "750 Per Occurrence")
    check("C1 split and combined deductibles are mutually exclusive",
          len(with_none) > 1 and list(with_set) == ["No Deductible"],
          f"BI/PD none -> {len(with_none)} legal; PD set -> {list(with_set)}")

    # C2: fifteen jurisdictions file a terrorism location and all fifteen file
    # the SAME field; the other 36 file none and rate terrorism anyway (OI-91).
    # Asked of the declaration rather than a list of state codes.
    ny = Declared("NY")
    place_ok, place_ny = ok.terrorism_place(), ny.terrorism_place()
    check("C2 terrorism is located by declaration, not by state code",
          place_ok is None and place_ny == ("TerrorismTerritory",
                                            place_ny[1] if place_ny else None),
          f"OK -> {place_ok}, NY -> {place_ny}")
    check("C2b a jurisdiction that files no terrorism location rates it "
          "anyway (OI-91)",
          _terrorism_rates_without_a_place(),
          "AK, VT, WY and MT: premium moves with no location field sent")

    # C3: a class code brings its own description and basis from ISO's tables.
    check("C3 a class code carries ISO's own description",
          ok.description("50017").startswith("Abrasives"),
          f"50017 -> {ok.description('50017')!r}")

    print("\nD  STATE NARROWING IS READ, NOT DISCOVERED FROM A 400")
    ny_cat = {v.name: v for v in catalogue(ny)}
    ny_base = base_for("NY")
    try:
        ny_cat["claims-made-year-1"].payload(ny_base, ny)
        built = True
        why = ""
    except BreadthError as exc:
        built, why = False, str(exc)
    check("D1 NY declares Occurrence as the only coverage form, so "
          "claims-made is not built there", not built, why[:110])

    # The same variant IS built in OK, so D1 is narrowing and not a broken
    # variant.
    okp = {v.name: v for v in cat}["claims-made-year-1"].payload(base, ok)
    check("D2 the same variant builds in OK",
          gl(okp)["PremOpsProdsCoverageForm"] == "Claims Made",
          "so D1 is a jurisdiction difference, not a broken variant")
    check("D3 the claims-made year is an INTEGER (OI-90)",
          isinstance(gl(okp)["YearInClaimsMade"], int),
          "Type is a form control, not a data type")

    print("\nE  IT RATES, AND A NO-OP IS REPORTED RATHER THAN PASSED")
    kernel = Kernel(mode=STRICT, resolver=EditionResolver())
    b = kernel.rate(base_for("OK"))
    check("E1 the base submission rates", b.complete, f"base premium {b.premium}")

    rated, stopped, flat = [], [], []
    premium: dict = {}
    for v in cat:
        try:
            p = v.payload(base, ok)
        except BreadthError:
            continue
        r = kernel.rate(p)
        if not r.complete:
            stopped.append(v.name)
            continue
        rated.append(v.name)
        premium[v.name] = r.premium
        if r.premium == b.premium:
            flat.append(v.name)
    check("E2 the deductible chain moves the premium",
          all(n not in flat for n in
              ("premops-pd-5000-occ", "premops-bipd-10000-occ",
               "prods-pd-2000-occ")),
          "a deductible that changes nothing exercised nothing")
    check("E3 structure and limits move the premium",
          all(n not in flat for n in
              ("two-locations", "two-classifications", "area-basis-class",
               "occurrence-limit-500k", "occurrence-limit-5m")),
          f"{len(rated)} variants rated")
    # **OI-88 is closed, and this is now the comparison the old assertion said
    # it would become.** It stayed an assertion for as long as the defect was
    # open so it could not regress silently; 8816 is ISO's own figure for this
    # submission, recorded when the live service found the defect.
    check("E4 OI-88 is closed: size-of-risk rates in OK",
          "size-of-risk" not in stopped,
          "was ENGINE STOPPED on a null inside a FirstNonNull branch")
    # OI-94: the three ISO refuses must refuse here too, and for the stated
    # reason. `0` is a legal filed loss cost -- only a NULL is unratable -- so
    # this must not become "refuse when the loss cost is falsy".
    kern94 = Kernel(mode=STRICT, resolver=EditionResolver())
    import variants as VV
    refused, rated94 = [], []
    for juris in ("GA", "TX", "FL", "OK", "CA", "RI"):
        dd = VV.Declared(juris)
        rr = kern94.rate(VV.build({"size_of_risk": "Yes"}, dd))
        (rated94 if rr.complete else refused).append(juris)
    check("E6 a null loss cost refuses, in exactly the jurisdictions ISO "
          "refuses (OI-94)",
          refused == ["GA", "TX", "FL"] and rated94 == ["OK", "CA", "RI"],
          f"refused {refused}; rated {rated94} -- ISO 400s on the first three")
    check("E7 ...and a loss cost of ZERO still rates, because 0 is filed",
          "0" in [str(n.text) for n in _loss_cost_nodes(kern94, "OK")],
          "OK writes ProdsCompldOpsLossCost=0 on a risk that rates")

    check("E4b ...and it lands on ISO's number",
          premium.get("size-of-risk") == 8816,
          f"ours={premium.get('size-of-risk')} ISO=8816 (base {b.premium})")
    check("E5 the no-op variants are the ones on record (OI-89)",
          set(flat) <= {"premops-bi-1000-claim", "if-any-basis",
                        "schedule-rating-credit", "schedule-rating-stacked"},
          f"unchanged from base: {sorted(flat)}")

    # OI-95: the `Industry` ELP path is already correct -- confirmed against
    # ISO's own certified STC output, no fix needed. The `Company` (RTC) path
    # completes with ISO's own filed validation message unread; R29 reads it.
    kern_strict = Kernel(mode=STRICT, resolver=EditionResolver())
    kern_uw = Kernel(mode=UNDERWRITING, resolver=EditionResolver())

    r_industry = kern_strict.rate(_ok_stc_input())
    check("E8 OI-95 the `Industry` ELP path needs no fix -- matches ISO's own "
          "STC output exactly",
          r_industry.complete and r_industry.premium == 7839,
          f"premium={r_industry.premium}, ISO's own STC output=7839")

    msg = "Must enter Estimated Loss Potential Override"
    r_company_strict = kern_strict.rate(_ok_stc_input("10011"))
    check("E9 strict mode stays a pure mirror: ISO's own message is captured, "
          "no referral raised, same as ISO's own filed rules would score it",
          r_company_strict.complete
          and any(msg in m for m in r_company_strict.messages)
          and r_company_strict.referrals == [],
          f"messages={r_company_strict.messages}, "
          f"referrals={r_company_strict.referrals}")

    r_company_uw = kern_uw.rate(_ok_stc_input("10011"))
    check("E10 underwriting mode raises R29 on that exact message (OI-95)",
          r_company_uw.complete
          and [ref.code for ref in r_company_uw.referrals] == ["R29"]
          and msg in r_company_uw.referrals[0].where,
          f"referrals={r_company_uw.referrals}")

    r_premops_uw = kern_uw.rate(_ok_stc_input("10119"))
    check("E11 ...and the Premises/Operations side of the same message fires "
          "R29 too, not only Products/Completed Operations",
          r_premops_uw.complete
          and any(ref.code == "R29" for ref in r_premops_uw.referrals),
          f"referrals={r_premops_uw.referrals}")

    # OI-96: the 2027 filing dropped " CSL" from limit values; 7 of the 12
    # CORE states stopped outright before variants.py started renormalizing
    # the base's own limit fields against the resolved edition. Pinned as a
    # standing regression case, not just a one-time check -- exact premiums,
    # not just "it completes", the same discipline as E4b/E6/E9-E11 above.
    import qa
    kern_cliff = Kernel(mode=STRICT, resolver=EditionResolver())
    cliff_premiums = {}
    cliff_stopped = []
    for juris in qa.CORE:
        cfg = {"effective_date": CLASS_BASIS_CLIFF}
        d = VV.Declared.for_config(juris, cfg)
        r = kern_cliff.rate(VV.build(cfg, d))
        if r.complete:
            cliff_premiums[juris] = str(r.premium)
        else:
            cliff_stopped.append(juris)
    check("E12 OI-96: every CORE state rates at the 2027 cliff, none stopped "
          "on the CSL lookup miss",
          not cliff_stopped, f"stopped: {cliff_stopped}" if cliff_stopped
          else f"{len(cliff_premiums)} of {len(qa.CORE)} rated")
    # Re-measured 2026-08-31 (OI-97, BUILD-LOG.md Entry 54): OH, FL, PA, RI
    # and DE moved when the corpus refresh bumped the countrywide parent from
    # GL_CW_20270401_V01 to V02 for most CORE states.
    #
    # Re-measured again the same day (OI-97's fix, Entry 56): every state that
    # declares `ProdsCompldOpsExclusion` jumped hard -- OH, TX, FL, PA, RI,
    # MT, WY, DE were all silently pricing Products/Completed Operations at
    # zero until now. NY, CA, NJ, GA are unchanged -- they have no 2027
    # edition filed and never reach the field at all.
    # CA 7586 -> 7611 on 2026-10-14 (B-38): GL CA 20270101 V01, a package the
    # corpus lacked, now in it; ISO rates the same request $7,611 on it.
    # NJ 9444 -> 10429 (GL NJ 20270101 V03) and RI 8715 -> 8695 (GL RI 20270401
    # V03), the same day: ISO's own figures for these requests on those packages.
    expected_cliff = {
        "NY": "12141", "CA": "7611", "NJ": "10429", "OH": "7670", "TX": "7740",
        "FL": "8610", "PA": "10570", "GA": "7366", "RI": "8695", "MT": "8539",
        "WY": "8245", "DE": "8320",
    }
    check("E13 ...and the premiums are the exact figures measured when this "
          "was fixed, not just SOME number",
          cliff_premiums == expected_cliff,
          f"{cliff_premiums}" if cliff_premiums != expected_cliff else
          "all 12 match")

    print(f"\n{len(PASS)}/{len(PASS) + len(FAIL)} passed")
    for f in FAIL:
        print(f"  FAILED  {f}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
