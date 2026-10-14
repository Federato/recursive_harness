"""Stage 4 acceptance: the submission schema and the sample payloads.

  A  the schema     read from ISO's own Form Fields, per jurisdiction
  B  legal values   from ISO's domain tables, via `DataValue`
  C  real payloads  ISO's own 50 submissions validate with no errors
  D  the four       CA, FL, NY, TX code terrorism territory explicitly (E8)
  E  the samples    one per jurisdiction, same risk, all of them rate
  F  what is absent Hawaii is not in the corpus and cannot be rated
  G  territories    no sample omits a rating-required territory (OI-92)

Run: python tests/verify_stage4.py
"""
from __future__ import annotations

import csv
import json
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from gl_engine import EditionResolver, ResolvedBook, discover   # noqa: E402
from gl_engine.rating import Kernel                             # noqa: E402
from gl_engine.schema import Schema, validate                   # noqa: E402
from gl_engine.schema.validate import PLACE_CODED               # noqa: E402

ASOF = "20260801"
PAYLOADS = ROOT / "Payloads"
SAMPLES = ROOT / "Engine_Payloads"
PASS, FAIL = [], []
RESOLVER = EditionResolver()


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(f"{name}  {detail}".rstrip())
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f"  [{detail}]" if detail else ""))


def schema_for(juris, asof=ASOF):
    return Schema.for_book(ResolvedBook(RESOLVER.resolve(juris, asof)))


def group_a():
    print("\nA  THE SCHEMA -- read from ISO, not designed")
    s = schema_for("OK")
    check("A1 the schema loads and is large", len(s) > 1000,
          f"{len(s)} fields over {len(s.tables())} tables")
    check("A2 it names the packages it came from",
          s.summary()["packages"][0].startswith("GL_OK"),
          " over ".join(s.summary()["packages"]))
    # `Type` is a form control, not a data type. Asserted so the distinction
    # cannot be quietly lost -- a validator reading TEXT as "string" would
    # accept an exposure of "banana".
    controls = {f.control for f in s}
    check("A3 Type is a form control, not a data type",
          controls <= {"TEXT", "SELECT", "CHECKBOX", "HIDDEN", "TEXTAREA",
                       "BUTTON", "ANCHOR", ""},
          str(sorted(controls)))
    check("A4 required-to-rate is a different, smaller set than required-on-form",
          0 < len(s.rating_required()) < len(s.required(False)),
          f"{len(s.rating_required())} rating-required vs "
          f"{len(s.required(False))} form-required")
    # Every jurisdiction must produce a schema; a state with none would mean
    # the submission format for it is unknown.
    js = sorted({p.identity.juris for p in RESOLVER.packages
                 if p.identity.juris != "CW"})
    sizes = {}
    for j in js:
        try:
            sizes[j] = len(schema_for(j))
        except Exception as exc:                          # noqa: BLE001
            sizes[j] = 0
    check("A5 every jurisdiction has a schema",
          all(v > 1000 for v in sizes.values()),
          f"{len(sizes)} jurisdictions, "
          f"{min(sizes.values())}..{max(sizes.values())} fields")


def group_b():
    print("\nB  LEGAL VALUES -- from ISO's domain tables")
    s = schema_for("OK")
    subline = s.legal_values("GeneralLiability", "Subline")
    check("B1 Subline's legal values are ISO's own",
          "Premises/Operations and Products/Completed Operations" in subline
          and len(subline) >= 8, f"{len(subline)} values")
    basis = s.legal_values("GeneralLiabilityClassification",
                           "PremOpsPremiumBasis")
    check("B2 premium basis includes Gross Sales", "Gross Sales" in basis,
          f"{len(basis)} values")
    # The value is DataValue, not the first non-state column -- taking the
    # latter returns the ZIP from a ZIP-to-territory table and reports every
    # real territory as illegal. That was the first implementation.
    terr = s.legal_values("GeneralLiabilityLocation",
                          "PremisesOperationsTerritory")
    check("B3 a ZIP-keyed domain yields territories, not ZIPs",
          bool(terr) and all(len(v) <= 4 for v in terr[:20]),
          f"{len(terr)} values, e.g. {list(terr[:3])}")
    check("B4 an unconstrained field reports no legal values, not an empty set "
          "of one",
          s.legal_values("GeneralLiabilityClassification", "ClassDescription")
          == (), "()")


def group_b2():
    """Dependent domains, resolved through ISO's own declared relationship."""
    print("\nB2 DEPENDENT DOMAINS -- exact where ISO declares the dependency")
    import json as _json
    from gl_engine.rating.submission import from_raas
    from gl_engine.interp import tree as _t

    s = schema_for("OK")
    tbl = ("GeneralLiabilityCertifiedActsOfTerrorismAggregateLimitCapOn"
           "LossesFromCertifiedActsOfTerrorismPremOps")
    check("B5 ISO declares the dependency path for this field",
          s.related_path(tbl, "AggregateLimit").endswith(
              "PremOpsProdsEachOccurrenceLimit"),
          s.related_path(tbl, "AggregateLimit"))
    check("B6 the domain is keyed by another field's value",
          s.dependency_columns(tbl, "AggregateLimit")[0]
          == "PolicyEachOccurrenceLimit",
          str(s.dependency_columns(tbl, "AggregateLimit")))

    p = _json.loads((PAYLOADS / "OK" / "1. Input.json").read_text(
        encoding="utf-8-sig"))
    root, _, _ = from_raas(p)
    gl = _t.select_one("GeneralLiabilityTable/GeneralLiability", root)
    node = _t.select_one(f"{tbl}Table/{tbl}", gl)
    union, u_exact = s.resolved_values(tbl, "AggregateLimit", None)
    exact, is_exact = s.resolved_values(tbl, "AggregateLimit", node)
    check("B7 with no context it is a superset, and says so",
          not u_exact and len(union) > 0, f"{len(union)} values, exact=False")
    check("B8 with the submission it resolves exactly",
          is_exact and len(exact) < len(union),
          f"{len(exact)} of {len(union)} -- policy limit "
          f"{_t.read('PremOpsProdsEachOccurrenceLimit', gl)!r}")
    # A field whose domain has no dependency is exact either way -- the flag
    # must not claim precision it does not have, nor withhold it.
    plain, p_exact = s.resolved_values("GeneralLiability", "Subline", None)
    check("B9 a plain list is exact with or without context",
          p_exact and len(plain) >= 8, f"{len(plain)} values")


def group_c():
    print("\nC  ISO'S OWN 50 SUBMISSIONS VALIDATE")
    errs, warns, n, known = 0, 0, 0, 0
    worst = []
    for d in sorted(p for p in PAYLOADS.iterdir() if p.is_dir()):
        src = d / "1. Input.json"
        if not src.exists():
            continue
        n += 1
        p = json.loads(src.read_text(encoding="utf-8-sig"))
        eff = p["body"]["SchemeKeys"]["EffectiveDateTime"][:10].replace("-", "")
        f = validate(p, schema_for(d.name, eff))
        # OI-92: ISO's own GA example omits its rating-required prem/ops territory (it rates products only:
        # 6845, not 7366). Since OI-134 the validator reports that as the V7 error it is; it is the one expected.
        e = [x for x in f if x.level == "error"
             and not (d.name == "GA" and x.code == "V7"
                      and x.where == "GeneralLiabilityLocation.PremisesOperationsTerritory")]
        known += sum(1 for x in f if x.level == "error") - len(e)
        errs += len(e)
        warns += sum(1 for x in f if x.level == "warning")
        if e:
            worst.append(f"{d.name}: {e[0]}")
    check("C0 ISO's GA example is reported missing its prem/ops territory (OI-92, found again by OI-134's V7)",
          known == 1, f"{known} known error(s)")
    check("C1 every ISO submission validates with no errors", errs == 0,
          f"{n} payloads, {errs} errors, {warns} warnings"
          + (f"; {worst[:2]}" if worst else ""))
    check("C2 warnings are reported rather than suppressed", warns > 0,
          f"{warns} warnings -- envelope fields ISO's form does not declare")


def group_d():
    print("\nD  THE FOUR PLACE-CODED JURISDICTIONS (E8)")
    check("D1 exactly four are place-coded", len(PLACE_CODED) == 4,
          str(PLACE_CODED))
    # Measured, not asserted: they use TerrorismTerritoryCode where 11 others
    # use TerritoryCodeByZipCode.
    coded, zipped = [], []
    for j in sorted({p.identity.juris for p in RESOLVER.packages
                     if p.identity.juris != "CW"}):
        f = schema_for(j).get("GeneralLiabilityLocation", "TerrorismTerritory")
        if f is None:
            continue
        (coded if f.domain == "TerrorismTerritoryCode" else zipped).append(j)
    check("D2 the four are exactly the TerrorismTerritoryCode jurisdictions",
          sorted(coded) == sorted(PLACE_CODED), str(sorted(coded)))
    check("D3 others derive terrorism territory from a ZIP", len(zipped) >= 10,
          f"{len(zipped)} use TerritoryCodeByZipCode")
    # A submission in one of the four without the field is warned about, since
    # it cannot be derived and an unmatched one refers (R22).
    p = json.loads((PAYLOADS / "CA" / "1. Input.json").read_text(
        encoding="utf-8-sig"))
    for risk in p["body"]["GeneralLiability"]:
        for loc in risk.get("GeneralLiabilityLocation", []):
            loc.pop("TerrorismTerritory", None)
    f = validate(p, schema_for("CA"))
    check("D4 a missing terrorism territory in the four is reported",
          any(x.code == "V4" for x in f),
          f"{sum(1 for x in f if x.code == 'V4')} findings")


def group_e():
    print("\nE  THE SAMPLES -- one per jurisdiction, the same risk")
    if not SAMPLES.is_dir():
        check("E0 samples built", False, "run scripts/build_sample_payloads.py")
        return
    dirs = sorted(p for p in SAMPLES.iterdir() if p.is_dir())
    check("E1 one sample per jurisdiction", len(dirs) == 51, f"{len(dirs)}")

    # Same risk everywhere is the whole point: a price difference between two
    # states says nothing if the risk also moved.
    risks = {}
    for d in dirs:
        p = json.loads((d / "submission.json").read_text(encoding="utf-8"))
        cls = (p["body"]["GeneralLiability"][0]
               ["GeneralLiabilityLocation"][0]
               ["GeneralLiabilityClassification"][0])
        risks[d.name] = (cls["ClassCode"], cls["PremOpsCovExposure"],
                         p["body"]["GeneralLiability"][0]["GeneralAggregateLimit"])
    check("E2 every sample carries the identical risk",
          len(set(risks.values())) == 1, str(next(iter(set(risks.values())))))

    out = ROOT / "scripts" / "erc" / "out" / "sample_payloads.csv"
    if not out.exists():
        check("E3 the reconciliation exists", False, str(out))
        return
    rows = list(csv.DictReader(open(out, encoding="utf-8")))
    rated = [r for r in rows if r["premium"]]
    check("E3 every jurisdiction rates the sample", len(rated) == 51,
          f"{len(rated)} of {len(rows)}")
    check("E4 no sample has a schema error",
          all(r["schema_errors"] in ("0", "") for r in rows),
          "0 errors across 51")
    prem = sorted(int(r["premium"]) for r in rated)
    check("E5 the same risk prices differently by jurisdiction",
          prem[0] != prem[-1],
          f"cheapest {prem[0]:,} .. dearest {prem[-1]:,}")


def group_f():
    print("\nF  WHAT IS ABSENT, STATED RATHER THAN DISCOVERED")
    juris = {p.identity.juris for p in discover()}
    check("F1 Hawaii is not in the corpus and cannot be rated",
          "HI" not in juris, "51 jurisdictions + CW, no HI")
    check("F2 Puerto Rico IS in the corpus", "PR" in juris, "PR present")
    # PR has no RAaS payload of its own; its sample is built from ISO's domain
    # tables, so nothing about it is invented.
    check("F3 Puerto Rico has no ISO payload, and its sample is built from "
          "ISO's domain tables instead",
          not (PAYLOADS / "PR").exists() and (SAMPLES / "PR").exists(),
          "sample present, source payload absent")


def group_g():
    """OI-92: a sample that omits a rating-required territory rates half a risk.

    ISO's own stored input for Georgia carried no `PremisesOperationsTerritory`
    and the generator copied the hole. The prem/ops loss cost then never
    resolved, GA's premium was **products only**, and **it still matched ISO**,
    because ISO rates the same deficient submission the same way. It presented
    as a `MATCH` for as long as nobody varied anything.

    This is the guard. It asserts the property rather than the one jurisdiction,
    so the next example ISO ships with a hole fails here instead of quietly
    halving a risk.
    """
    print("\nG  EVERY SAMPLE SUPPLIES ITS RATING-REQUIRED TERRITORIES (OI-92)")
    import json as _json
    from build_sample_payloads import SUBLINE_TERRITORY_FIELDS
    missing = []
    for d in sorted(p for p in SAMPLES.iterdir() if p.is_dir()):
        f = d / "submission.json"
        if not f.exists():
            continue
        juris = d.name
        schema = schema_for(juris)
        loc = (_json.loads(f.read_text(encoding="utf-8"))["body"]
               ["GeneralLiability"][0]["GeneralLiabilityLocation"][0])
        for col in SUBLINE_TERRITORY_FIELDS:
            fl = schema.get("GeneralLiabilityLocation", col)
            if fl is None or not fl.rating_required:
                continue
            if not schema.legal_values("GeneralLiabilityLocation", col):
                continue                     # nothing declared to supply
            if loc.get(col) in (None, ""):
                missing.append(f"{juris}.{col}")
    check("G1 no sample omits a rating-required territory it could supply",
          not missing,
          "; ".join(missing) if missing
          else f"{len(list(SAMPLES.iterdir()))} samples checked")

    # And the consequence, pinned on the jurisdiction that had it: GA must
    # price its prem/ops side, not only its products side.
    ga = _json.loads((SAMPLES / "GA" / "submission.json").read_text(
        encoding="utf-8"))
    r = Kernel(resolver=RESOLVER).rate(ga)
    has_lc = any(e.kind == "lookup" and "PremOpsLossCost" in e.detail
                 for e in r.trace)
    check("G2 Georgia resolves a prem/ops loss cost and prices both sides",
          has_lc and r.premium == Decimal("7366"),
          f"premium {r.premium}, prem/ops loss cost "
          f"{'looked up' if has_lc else 'NEVER LOOKED UP'}")


def group_h():
    print("\nH  REQUIRED INPUTS -- ISO's conditions evaluated, missing rating inputs refused (OI-134)")
    import copy
    from gl_engine.interp.tree import Node
    from gl_engine.interp import tree as T
    from gl_engine.schema.condition import ConditionError, holds
    from gl_engine.schema.validate import rating_inputs

    root = Node.from_dict("Root", {"GeneralLiabilityTable": {"GeneralLiability": {
        "Subline": "Premises/Operations and Products/Completed Operations", "ProdsCompldOpsExclusion": "No",
        "GeneralLiabilityLocationTable": {"GeneralLiabilityLocation": {"GeneralLiabilityClassificationTable": {
            "GeneralLiabilityClassification": {"ClassCode": "10020", "PremOpsPDDeductible": "500 Per Claim"}}}}}}})
    gl = T.select("GeneralLiabilityTable/GeneralLiability", root)[0]
    cl = T.select("GeneralLiabilityLocationTable/GeneralLiabilityLocation/GeneralLiabilityClassificationTable/"
                  "GeneralLiabilityClassification", gl)[0]
    cases = [
        (gl, "Subline[.='Premises/Operations and Products/Completed Operations']", True),
        (gl, "Subline[.= 'Products/Completed Operations' or .='Liquor']", False),
        (cl, "((../../../../Subline[.='Premises/Operations and Products/Completed Operations'] and "
             "../../../../ProdsCompldOpsExclusion[.='No'])  or ../../../../Subline[.='Products/Completed Operations'])"
             " and ClassCode[.='10011' or .='10020']", True),
        (cl, "../../../../Subline[.='Premises/Operations and Products/Completed Operations'] and "
             "PremOpsPDDeductible[contains(.,'Per Claim')]", True),
        (cl, "count(../../GeneralLiabilityClassificationTable/GeneralLiabilityClassification) > 1", False),
        (gl, "ScheduleRatingModificationApplies [.= 'Yes']", False),
    ]
    bad = [c for n, c, want in cases if holds(c, n) != want]
    check("H1 ISO's condition slice evaluates: paths, predicates, or/and, contains(), count()",
          not bad, f"{len(cases) - len(bad)} of {len(cases)}" + (f"; wrong: {bad[0][:60]}" if bad else ""))
    try:
        holds("substring(Subline,1,3)='Pre'", gl)
        refused = False
    except ConditionError:
        refused = True
    check("H2 a function outside the slice is refused, not guessed", refused)

    inputs = rating_inputs()
    check("H3 the measured rating inputs are loaded (57_rating_inputs.py)",
          {"GeneralLiability.Subline", "GeneralLiability.ProdsCompldOpsExclusion"} <= inputs, f"{len(inputs)} fields")

    sys.path.insert(0, str(ROOT / "scripts"))
    from console import workbench as WB
    k = Kernel(resolver=RESOLVER)
    req = WB.build("GL", "TX", {"effective_date": "20270501"})
    ok = k.rate(copy.deepcopy(req))
    omit = copy.deepcopy(req)
    omit["body"]["GeneralLiability"][0].pop("ProdsCompldOpsExclusion")
    r = k.rate(omit)
    check("H4 TX 2027 with ProdsCompldOpsExclusion rates; without it the engine refuses, naming it "
          "(ISO prices $895 vs $7,740, no message)",
          ok.complete and ok.premium == Decimal("7740") and not r.complete
          and "ProdsCompldOpsExclusion" in str(r.stopped), f"{ok.premium}; refused: {str(r.stopped)[:90]}")
    f = [x for x in validate(omit, schema_for("TX", "20270501")) if x.code == "V7"]
    check("H5 the validator reports it as a V7 error", len(f) == 1 and f[0].level == "error",
          f"{[x.where for x in f]}")
    no_sub = copy.deepcopy(req)
    no_sub["body"]["GeneralLiability"][0].pop("Subline")
    r = k.rate(no_sub)
    check("H6 an unconditional rating input (Subline: priced $0 without it) refuses too",
          not r.complete and "Subline" in str(r.stopped), str(r.stopped)[:90])
    warn = [x for x in validate(req, schema_for("TX", "20270501")) if x.code in ("V6", "V7")]
    check("H7 an informational required field left out is a warning, never an error",
          warn and all(x.level != "error" for x in warn if x.code == "V6") and not any(x.code == "V7" for x in warn),
          f"{len(warn)} V6 finding(s) on the console's TX request")


def group_i():
    print("\nI  SILENT ZEROS (OI-130, B-07): blanks, off-list answers, form combinations, the safety net")
    import copy
    sys.path.insert(0, str(ROOT / "scripts"))
    from console import workbench as WB
    from gl_engine.rating import referrals as RF
    from gl_engine.schema.validate import list_inputs
    k = Kernel(resolver=RESOLVER)
    uw = Kernel(mode="underwriting", resolver=RESOLVER)

    def gl(p):
        return p["body"]["GeneralLiability"][0]

    def cls(p):
        return gl(p)["GeneralLiabilityLocation"][0]["GeneralLiabilityClassification"][0]

    tx = WB.build("GL", "TX", {"effective_date": "20270501"})
    p = copy.deepcopy(tx)
    gl(p)["Subline"] = "  "
    r = k.rate(p)
    check("I1 a blank answer is no answer: Subline '  ' refuses (it priced $0 past OI-134)",
          not r.complete and "Subline" in str(r.stopped), str(r.stopped)[:80])

    check("I2 the measured list fields are loaded (57_rating_inputs.py)", len(list_inputs()) > 0,
          f"{len(list_inputs())} list fields")
    p = copy.deepcopy(tx)
    gl(p)["Subline"] = "Premises/Operations"          # not a 2027 value: the whole policy priced $0
    r = k.rate(p)
    check("I3 an answer off ISO's list refuses, naming it (2027 'Premises/Operations' alone: was $0)",
          not r.complete and "not on ISO's list" in str(r.stopped), str(r.stopped)[:90])

    ny = WB.build("GL", "NY", {"terrorism": "Yes"})
    check("I4 the console answers NY's Manhattan question when terrorism is on (it priced terrorism $0)",
          gl(ny)["GeneralLiabilityLocation"][0].get("CertifiedActsOfTerrorismManhattan") is not None
          and k.rate(copy.deepcopy(ny)).premium == Decimal("12602"))
    p = copy.deepcopy(ny)
    gl(p)["GeneralLiabilityLocation"][0].pop("CertifiedActsOfTerrorismManhattan")
    r = k.rate(p)
    check("I5 NY terrorism without the Manhattan answer refuses", not r.complete
          and "Manhattan" in str(r.stopped), str(r.stopped)[:90])

    sg = WB.build("GL", "ND", {"effective_date": "20260801"})
    gl(sg)["StopGap"] = "Yes"
    gl(sg)["GeneralLiabilityStopGapEmployersLiabilityCoverageEndorsementPolLvl"] = [{
        "LimitBodilyInjuryByAccident": "100,000 BI", "LimitBodilyInjuryByDiseaseEachEmployee": "100,000 BI",
        "LimitBodilyInjuryByDiseaseAggregate": "500,000 BI"}]
    ok = k.rate(copy.deepcopy(sg))
    p = copy.deepcopy(sg)
    gl(p).pop("StopGap")
    r = k.rate(p)
    p2 = copy.deepcopy(sg)
    gl(p2)["StopGap"] = "No"
    r2 = k.rate(p2)
    f2 = [x for x in validate(p2, schema_for("ND")) if x.code == "V8"]
    check("I6 Stop Gap details with the question unanswered refuse; answered 'No' rates with a V8 warning",
          ok.complete and not r.complete and "StopGap" in str(r.stopped) and r2.complete
          and f2 and f2[0].level == "warning", f"{ok.premium}; {str(r.stopped)[:50]}; {r2.premium}")
    p = copy.deepcopy(sg)
    gl(p)["GeneralLiabilityStopGapEmployersLiabilityCoverageEndorsementPolLvl"][0][
        "LimitBodilyInjuryByDiseaseEachEmployee"] = "500,000 BI"
    r = k.rate(p)
    check("I7 Stop Gap limits off ISO's combinations with no manual premium refuse (ISO's form requires it)",
          not r.complete and "ManualPremium" in str(r.stopped), str(r.stopped)[:90])

    p = copy.deepcopy(tx)
    cls(p).update(ClassCode="54444", PremOpsELPOverride=0.5, ProdsCompldOpsELPOverride=0.5)
    r = k.rate(p)
    check("I8 a company rate without its limit-table override refuses (priced $8 for $4,633 of Prem/Ops)",
          not r.complete and "IncrdLimitTableAssignmentOverride" in str(r.stopped), str(r.stopped)[:90])

    p = copy.deepcopy(tx)
    cls(p).update(ClassCode="10113", ClassDescription="Barber Shops")
    r = k.rate(p)
    check("I9 a class whose Products ISO marks 'Not Applicable' prices, labelled not offered (no R30)",
          r.complete and any(n.startswith("Not offered") for n in r.notices)
          and not any(n.startswith("R30") for n in r.notices), str(r.notices)[:120])

    clean = [k.rate(copy.deepcopy(WB.build("GL", s, {"effective_date": d})))
             for s in ("TX", "OK", "OR", "MT") for d in ("20260801", "20270501")]
    check("I10 the safety net (R30) is quiet on clean requests", all(c.complete and not c.notices for c in clean),
          f"{sum(1 for c in clean if c.notices)} of {len(clean)} with notices")
    os_ = __import__("os")
    os_.environ["ERC_RATING_INPUTS"] = "off"
    from gl_engine.rating import kernel as KM
    was, KM.RATING_INPUTS_CHECK = KM.RATING_INPUTS_CHECK, "off"
    try:
        p = copy.deepcopy(tx)
        gl(p)["PremOpsProdsCoverageForm"] = ""
        r = k.rate(p)
        ru = uw.rate(copy.deepcopy(p))
    finally:
        KM.RATING_INPUTS_CHECK = was
    check("I11 with the refusals off, a silent $0 coverage raises R30: a notice, and a referral in underwriting",
          r.complete and any(n.startswith("R30") for n in r.notices) and any(x.code == "R30" for x in ru.referrals),
          f"{[n[:40] for n in r.notices]}; {[x.code for x in ru.referrals]}")

    te = WB.build("GL", "OK", {"effective_date": "20260801", "terrorism": "Yes"})
    gl(te)["GeneralLiabilityAddlInsdLessorOfLeasedEquipmtAutomtcStatusWhenReqdInLeaseAgrmtWithYou"] = [
        {"ManualPremium": 1000.0}]
    gl(te)["GeneralLiabilityTerrorismEndorsementCoverage"] = {"CertifiedActsofTerrorismExposureClassFactor": 0.004}
    good = k.rate(copy.deepcopy(te))
    gl(te)["GeneralLiabilityTerrorismEndorsementCoverage"] = {}
    r = k.rate(copy.deepcopy(te))
    ru = uw.rate(copy.deepcopy(te))
    check("I12 terrorism on endorsements without its factor: R31 notice, and a referral in underwriting",
          not good.notices and any(n.startswith("R31") for n in r.notices) and any(x.code == "R31" for x in ru.referrals),
          f"{good.premium} -> {r.premium}")
    check("I13 R30 and R31 are wired as detectors", {"R30", "R31"} <= set(RF.DETECTORS))


def group_j():
    print("\nJ  PRE-2027 LIMITED PRODUCT WITHDRAWAL RATES (OI-128, B-08)")
    import copy
    sys.path.insert(0, str(ROOT / "scripts"))
    from console import workbench as WB
    from gl_engine.interp import tree
    k = Kernel(resolver=RESOLVER)
    p = WB.build("GL", "TX", {"effective_date": "20260801"})
    g = p["body"]["GeneralLiability"][0]
    g.update(ProdsWithdrawalCoverage="Yes", ProductWithdrawalParticipationPercentage="50", PremiumDiscountPercentage=0)
    g["GeneralLiabilityLimitedProductWithdrawalExpenseEndtPolLvl"] = [
        {"AggregateLimit": "100,000", "Deductible": "1,000 Per Occurrence", "ManualPremium": 500.0}]
    r = k.rate(copy.deepcopy(p))
    lpw = [c.first("Premium").text for c in tree.select(
        "GeneralLiabilityTable/GeneralLiability/GeneralLiabilityLimitedProductWithdrawalExpenseEndtPolLvlTable/"
        "GeneralLiabilityLimitedProductWithdrawalExpenseEndtPolLvl/GeneralLiabilityLimitedProductWithdrawalExpenseCoverage",
        r.tree)] if r.complete else []
    check("J1 TX 2026-08 with Limited Product Withdrawal rates as ISO does: $8,321, the endorsement $500 (it stopped: "
          "SetMinPremium's Arg read its siblings)", r.complete and r.premium == Decimal("8321") and lpw == ["500"],
          f"{r.premium if r.complete else str(r.stopped)[:80]}; LPW {lpw}")


def group_k():
    print("\nK  LOSS OF ELECTRONIC DATA IN A REFER BAND (OI-129, B-09)")
    import copy
    from variants import Declared
    k = Kernel(resolver=RESOLVER)
    hosts = Kernel.LOED_HOSTS

    def loed(juris, asof, limit, override=None):
        p = copy.deepcopy(Declared(juris, asof).base())
        g = p["body"]["GeneralLiability"][0]
        g["LossOfElectronicDataCoverageApplies"] = "Yes"
        g["GeneralLiabilityLossOfElectronicDataFromPhysicalInjuryToTangiblePropLiabCovSubToCyberIncidentExcl"] = [
            {"LossOfElectronicDataLimit": limit}]
        if override is not None:
            c = g["GeneralLiabilityLocation"][0]["GeneralLiabilityClassification"][0]
            for h in hosts:
                c.setdefault(h, {})["ILFOverride"] = override
        return p

    for mode in ("strict-erc", "underwriting"):
        r = Kernel(mode=mode, resolver=RESOLVER).rate(loed("IL", "20270401", "100,000"))
        check(f"K1 {mode}: $100,000 under a $2M aggregate with no ILFOverride refuses by name (it stopped on a bare "
              f"null; ISO prices LoED $0 with 'please enter the ILF override')",
              not r.complete and f"{hosts[0]}.ILFOverride is required" in str(r.stopped), str(r.stopped)[:90])
    r = k.rate(loed("IL", "20270401", "100,000", 1.1))
    check("K2 with ILFOverride 1.1 it rates as ISO does: $8,387 (ISO 2026-10-14)",
          r.complete and r.premium == Decimal("8387"), f"{r.premium if r.complete else str(r.stopped)[:80]}")
    r = k.rate(loed("IL", "20270401", "200,000"))
    check("K3 $200,000 is no refer band: rates without an override, $8,387", r.complete and r.premium == Decimal("8387"),
          f"{r.premium if r.complete else str(r.stopped)[:80]}")
    r = k.rate(loed("TX", "20261002", "100,000"))
    check("K4 last edition (TX 2026-10-02) refuses the same way", f"{hosts[0]}.ILFOverride is required" in str(r.stopped),
          str(r.stopped)[:90])


def group_l():
    print("\nL  REFERRALS THAT FIRED ON EVERY RISK OF A KIND (OI-131 B-10, B-35)")
    import copy
    import importlib.util
    spec = importlib.util.spec_from_file_location("ri", ROOT / "scripts" / "erc" / "57_rating_inputs.py")
    ri = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ri)
    k = Kernel(mode="underwriting", resolver=RESOLVER)

    def codes(p):
        r = k.rate(p)
        return sorted({f.code for f in r.referrals}) if r.complete else ["STOP"]

    def deductible(p, v):
        g = p["body"]["GeneralLiability"][0]
        g["LiquorDeductible"] = v
        for loc in g["GeneralLiabilityLocation"]:
            loc["LiquorDeductible"] = v
            for c in loc["GeneralLiabilityClassification"]:
                c["LiquorDeductible"] = v
        return p

    def usage(p, v):
        p["body"]["GeneralLiability"][0]["GeneralLiabilityLocation"][0]["GeneralLiabilityClassification"][0][
            "GeneralLiabilityUnmannedAircraft"][0]["Usage"] = v
        return p

    for d in ("20261002", "20270401"):
        got = codes(ri._built("Liquor-AL", d))
        check(f"L1 {d} ISO's AL liquor sample, No Deductible: no R14 (the one legitimate zero)", "R14" not in got, got)
        got = codes(deductible(ri._built("Liquor-AL", d), "5,000 Per Common Cause"))
        check(f"L2 {d} a Per Common Cause deductible, unguarded and zero: R14", "R14" in got, got)
        got = codes(ri._built("Drone-TX", d))
        check(f"L3 {d} a photography drone: no R19 (the $0 min-premium row) and no R13 (banded loss costs resolve)",
              not {"R13", "R19"} & set(got), got)
        got = codes(usage(ri._built("Drone-TX", d), "Crop spraying, dispersing of chemicals"))
        check(f"L4 {d} a crop-spraying drone, a refer-to-company cell: R19", "R19" in got, got)
    p = copy.deepcopy(ri._built("console-IL", "20270401"))
    g = p["body"]["GeneralLiability"][0]
    g["LossOfElectronicDataCoverageApplies"] = "Yes"
    g["GeneralLiabilityLossOfElectronicDataFromPhysicalInjuryToTangiblePropLiabCovSubToCyberIncidentExcl"] = [
        {"LossOfElectronicDataLimit": "200,000"}]
    r = k.rate(p)
    check("L5 LoED's $1 Prem/Ops premium from a real rate is not R30 (B-35; ISO prices it $1)",
          r.complete and "R30" not in {f.code for f in r.referrals}, f"{r.premium if r.complete else r.stopped}")


def main() -> int:
    print("Stage 4 acceptance -- schemas and payloads")
    group_a(); group_b(); group_b2(); group_c(); group_d(); group_e()
    group_f(); group_g(); group_h(); group_i(); group_j(); group_k(); group_l()
    total = len(PASS) + len(FAIL)
    print(f"\n{len(PASS)}/{total} passed")
    if FAIL:
        print("\nFAILURES:")
        for f in FAIL:
            print(f"  {f}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
