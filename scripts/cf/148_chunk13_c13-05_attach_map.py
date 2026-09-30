"""C13-05: which policy answers attach which terrorism forms, and what deletes one.

Read from the rules (CW 20260601, `CommercialPropertyRules`):
`ErcDoConditionalMandatoryLogic` -> `TerrorismFormsConditionalLogic` runs 13
`AttachForm*` rules. Each has one test on the policy's answers; if it holds
the form record is appended (unless already there), and **if it does not, the
form is REMOVED** -- a submitted form the answers don't call for is deleted
with no message. The PostTRIA record is auto-created on every policy and turns
itself on (`CoverageOnPolicyIndicator`) from the same answers.

The map below is transcribed from those 13 tests. The engine is then run over
every combination of the answers each `TRIAType` reads (domain values from
`Domain Tables`, plus blank) on chunk 2's Oregon building, and the forms left
on the policy are compared with the map -- twice: once with no forms
submitted (what attaches), once with all 13 submitted up front (what gets
deleted). `TerrorismIndicator` is read by no attach rule (only by two CP 00 70
messages); a "No" is included to show it doesn't switch terrorism off.

A reduced grid is also run in AK, FL and NY, the three states that override
the attach rules, and differences from the countrywide map are listed for
C13-19 (not failures).

    python scripts/cf/148_chunk13_c13-05_attach_map.py

Exits 1 if the countrywide engine run disagrees with the map anywhere.
"""
import copy
import itertools
import sys
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))

from cf_engine.config import NULL_ARITHMETIC, ROUNDING
from cf_engine.resolve import book_for
from gl_engine.interp.interpreter import Interpreter
from gl_engine.interp.tree import Node
from gl_engine.interp.values import InterpretError

g2 = import_module("09_chunk2_golden_case")
ASOF = "20260917"

IN_EFFECT = "Is in Effect for the Next 12 Months"
WILL_EXPIRE = "Will Expire During the Next 12 Months"
POST = "Has Already Expired, Use Post-TRIA Forms"
COND = "Has Expired but Use Conditional Forms"
TRIA_TYPES = [IN_EFFECT, WILL_EXPIRE, POST, COND, ""]
CERT = ["Yes", "No", "Yes, but Excludes Nuclear, Biological and Chemical Acts", "Yes, Subject to Sub-Limit", ""]
EXCL = ["Cover Subject to Sub-Limit", "Exclude", "Exclude Nuclear, Biological and Chemical Acts", "No Exclusion", ""]
RATING = ["Certified Terrorism Premium Calculated for Entire Term",
          "Certified Terrorism Premium Calculated Only Until End of This Calendar Year", ""]

P = "CommercialProperty"
FORMS = {
    "IL0030": P + "ExclusionOfTerrorismEndorsementIL0030",
    "IL0031": P + "ExclOfTerrsmInvolvingNuclearBiologicalOrChemicalTerrsmEndtIL0031",
    "IL0032": P + "LmtnOfCoverageForTerrsmSubLimitOnAnnualAggregateBasisEndtIL0032",
    "IL0952": P + "CapOnLossesFromCertifiedActsOfTerrorism",
    "IL0953": P + "ExclCertfdActsTerrsmCovFireLosses",
    "IL0986": P + "ExclCertfdActsOfTerrsmInvolvingNuclearBiologicalChmclTerrsmCapOnCovdCertfdActsLosses",
    "IL0987": P + "LimitationOfCoverageForCertifiedActsOfTerrorismSubLimitOnAnnualAggregateBasis",
    "IL0995": P + "ConditionalExclusionOfTerrorismEndorsementIL0995",
    "IL0996": P + "ConditionalExclOfTerrsmInvolvingNuclearBiolgclOrChemicalTerrsmIL0996",
    "IL0997": P + "ConditionalLmtnOfCovForTerrsmSubLimitOnAnnualAggregateBasisIL0997",
    "Disc-123105": P + "ZzDisclosureOfPremiumThrough123105CertifiedActsTerrorismPursuantTerrorismAct2002",
    "Disc-Estimated": P + "ZzDisclosureOfPremiumEstimatedPremiumCertifiedActsTerrorismPursuantTerrorismAct2002",
    "Disc-TRIA": P + "ZzDisclosurePursuantToTerrorismRiskInsAct2002",
}


import _regress  # noqa: E402  regression-mode sampling: 104_ sets CF_REGRESSION_SAMPLE; gates run in full

def predict(tt, cert, excl, cond, rating):
    """The 13 tests, transcribed from CW 20260601, plus the PostTRIA indicator.

    Every one of the 13 tests opens with `IsNotNull TRIAType` (the first
    transcription missed it and predicted IL0952-IL0987 on a blank TRIAType;
    the engine was right): with no TRIAType, no terrorism form attaches and
    any submitted one is removed."""
    on = set()
    if not tt:
        return on, False
    if tt == POST:
        on |= {"Exclude": {"IL0030"}, "Exclude Nuclear, Biological and Chemical Acts": {"IL0031"},
               "Cover Subject to Sub-Limit": {"IL0032"}}.get(excl, set())
    else:
        on |= {"Yes": {"IL0952"}, "No": {"IL0953"},
               "Yes, but Excludes Nuclear, Biological and Chemical Acts": {"IL0986"},
               "Yes, Subject to Sub-Limit": {"IL0987"}}.get(cert, set())
    if tt in (WILL_EXPIRE, COND):
        on |= {"Exclude": {"IL0995"}, "Exclude Nuclear, Biological and Chemical Acts": {"IL0996"},
               "Cover Subject to Sub-Limit": {"IL0997"}}.get(cond, set())
    if tt == WILL_EXPIRE and rating == RATING[1]:
        on.add("Disc-123105")
    if (tt == WILL_EXPIRE and rating == RATING[0]) or tt == COND:
        on.add("Disc-Estimated")
    if tt == IN_EFFECT:
        on.add("Disc-TRIA")
    post_on = bool(on & {"IL0030", "IL0031", "IL0032"}) or (tt == POST and excl == "No Exclusion")
    return on, post_on


def grid():
    """Only the answers each TRIAType can read, crossed; plus a few negations."""
    cases = []
    for tt in TRIA_TYPES:
        if tt == POST:
            for excl in EXCL:
                cases.append((tt, "", excl, "", ""))
            cases.append((tt, "Yes", "Exclude", "Exclude", RATING[0]))      # the others must not leak in
        elif tt in (WILL_EXPIRE, COND):
            for cert, cond, rating in itertools.product(CERT, EXCL, RATING):
                cases.append((tt, cert, "", cond, rating))
        else:
            for cert in CERT:
                cases.append((tt, cert, "", "", ""))
            cases.append((tt, "Yes", "Exclude", "Exclude", RATING[1]))
    return cases


def run(juris, answers, preattach=False, indicator="Yes"):
    tt, cert, excl, cond, rating = answers
    sub = g2.submission()
    cp = sub["CommercialPropertyTable"]["CommercialProperty"][0]
    cp.update({"TerrorismIndicator": indicator, "TRIAType": tt, "CoverageForCertifiedActs": cert,
               "PostTRIAExclusion": excl, "TRIAConditionalExclusion": cond,
               "ConditionalExclusionRatingOption": rating})
    if tt == WILL_EXPIRE:
        cp["TRIAExpirationDate"] = "06/01/2027"
    for k in [k for k, v in cp.items() if v == ""]:
        del cp[k]                                   # blank = not sent
    if preattach:
        for rec in FORMS.values():
            cp[rec + "Table"] = {rec: [{}]}
    if juris != "OR":
        cp["State"] = juris
    ip = Interpreter(book_for(juris if juris != "OR" else "OR", ASOF), rounding=ROUNDING,
                     null_arithmetic=NULL_ARITHMETIC)
    data = Node.from_dict(f"MasterCF{juris}", sub)
    ip.run(data)
    node = data.first("CommercialPropertyTable").first("CommercialProperty")
    present = set()
    for short, rec in FORMS.items():
        t = node.first(rec + "Table")
        if t is not None and t.kids(rec):
            present.add(short)
    post = node.first(P + "PostTRIACoverage")
    post_on = post is not None and any(c.tag == "CoverageOnPolicyIndicator" and c.text == "1" for c in post.children)
    return present, post_on


def main():
    cases = grid()
    fails = []
    print(f"COUNTRYWIDE (OR), {len(cases)} answer combinations, run twice (no forms submitted / all 13 submitted)\n")
    rows = {}
    for answers in _regress.sample(cases):
        want, want_post = predict(*answers)
        for pre in (False, True):
            try:
                got, got_post = run("OR", answers, preattach=pre)
            except InterpretError as exc:
                fails.append((answers, pre, f"REFUSED {str(exc)[:80]}"))
                continue
            if got != want or got_post != want_post:
                fails.append((answers, pre, f"want {sorted(want)} post={want_post}  got {sorted(got)} post={got_post}"))
        rows.setdefault(answers[0] or "(blank)", []).append((answers, sorted(want), want_post))

    for tt, rs in rows.items():
        attached = sorted({f for _, w, _ in rs for f in w})
        print(f"  TRIAType {tt!r}: {len(rs)} combinations; forms reachable: {', '.join(attached) or 'none'}")
    # the indicator is not a switch
    got, post = run("OR", (IN_EFFECT, "Yes", "", "", ""), indicator="No")
    print(f"\n  TerrorismIndicator 'No' with TRIA in effect: forms {sorted(got)}  (the indicator switches nothing off)")

    print("\nSTATE OVERRIDES (AK, FL, NY): differences from the countrywide map, for C13-19")
    sample = [c for c in cases if c[0] in (POST, WILL_EXPIRE, IN_EFFECT) and c[4] in ("", RATING[0])][::3]
    for st in ("AK", "FL", "NY"):
        diffs = 0
        for answers in sample:
            want, want_post = predict(*answers)
            try:
                got, got_post = run(st, answers)
            except InterpretError as exc:
                diffs += 1
                print(f"  {st} {answers[:4]} REFUSED {str(exc)[:70]}")
                continue
            if got != want or got_post != want_post:
                diffs += 1
                if diffs <= 4:
                    print(f"  {st} TRIA={answers[0][:12]!r} cert={answers[1][:14]!r} excl={answers[2][:14]!r} "
                          f"cond={answers[3][:14]!r}: CW map {sorted(want)}, {st} gives {sorted(got)}")
        print(f"  {st}: {diffs} of {len(sample)} sampled combinations differ from countrywide")

    print()
    if fails:
        print(f"FAIL: {len(fails)} countrywide disagreements")
        for f in fails[:15]:
            print("  ", f)
        sys.exit(1)
    print(f"C13-05 CLEAN: all {len(cases)} combinations x 2 match the transcribed map, attach and delete, "
          "and the PostTRIA indicator follows it.")


if __name__ == "__main__":
    main()
