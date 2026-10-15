"""GL variants, the run store, pass 3 and the UI boundary: the checks of `verify_tester.py` that outlived its page.

Moved here in RC-6 (TC-37, 2026-10-07) when `/tester`, `/tests` and `/review` were retired. What tested the page
itself (its routes, its QA tab, its review tab, its "what changed" route: G, Q, R11-R13, E7-E8) went with it; those
jobs now live in the test console and are tested there (tests/verify_console_rc4.py, rc5, rc6). What stays tests code
that outlived the page: the one-way UI boundary (A), ISO's options (B, C), the effective date (H), not-applicable (D),
pass 3 and pass 4's briefs (R), multi-class (M), the run store (E1-E6) and the charts (F).

Variable tester acceptance: the controls, the routes and the separation.

  A  separation     UI code imports the engine; the engine imports no UI. This
                    is asserted by reading the imports, because it is the
                    property stage 6 existed to prove and a docstring does not
                    prove it
  B  declared       every dropdown option is a value ISO declares, and a value
                    it does not declare is refused before anything is sent
  C  keyed          a domain keyed on another answer collapses when that answer
                    is given -- the combined deductible is the case that would
                    otherwise offer 31 illegal values
  D  applicability  a jurisdiction that cannot express a configuration is
                    counted separately from one that disagrees
  H  effective date the payload and the as-of resolution are the same date,
                    by construction (decision A3) -- not two things that
                    happen to agree today
  E  store          runs round-trip, and the long view is computed from them
  F  charts         every chart returns SVG, and an empty one says what would
                    fill it
  G  routes         the page and its API answer without a server running

**No live calls and no server.** `dispatch` is called directly and the results
store is redirected to a temporary directory, so this suite never touches the
real `results/` and never spends a call.

Run: python tests/verify_gl_variants.py
"""
from __future__ import annotations

import ast
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import variants as V                                          # noqa: E402
import runstore as store                                      # noqa: E402
from ui import charts, variables                      # noqa: E402

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(f"{name}  {detail}".rstrip())
    print(f"  {'PASS' if cond else 'FAIL'}  {name}"
          + (f"  [{detail}]" if detail else ""))


def _imports(path: Path) -> set:
    """Top-level module names imported by a file."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return set()
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            out.add(node.module.split(".")[0])
    return out


def main() -> int:
    print("GL variants, run store, pass 3 and the UI boundary -- no server, no live calls")

    print("\nA  THE SEPARATION, READ FROM THE IMPORTS")
    engine_files = list((ROOT / "gl_engine").rglob("*.py"))
    offenders = [str(p.relative_to(ROOT)) for p in engine_files
                 if {"ui", "app", "variants", "sweep"} & _imports(p)]
    check("A1 gl_engine imports no UI and no script", not offenders,
          f"{len(engine_files)} engine files checked" if not offenders
          else ", ".join(offenders))

    ui_files = list((ROOT / "ui").glob("*.py"))
    check("A2 the UI package exists and is more than one file",
          len(ui_files) >= 4, ", ".join(sorted(p.name for p in ui_files)))

    # The other direction, stated as something the code either does or does
    # not do: **no file in `ui/` reaches the engine directly.** It goes through
    # `variants` for legality and `sweep` for rating, so there is nowhere in
    # the UI that a premium or an agreement could be computed.
    direct = sorted(p.name for p in ui_files if "gl_engine" in _imports(p))
    check("A3 no UI file imports the engine directly", not direct,
          "the engine is reached through variants and sweep, so the UI has "
          "nowhere to compute a premium" if not direct else ", ".join(direct))
    kernel_users = sorted(p.name for p in ui_files
                          if "Kernel(" in p.read_text(encoding="utf-8"))
    check("A3b no UI file constructs a Kernel", not kernel_users,
          ", ".join(kernel_users) or "rating belongs to sweep")
    sweep_src = (ROOT / "scripts" / "sweep.py").read_text(encoding="utf-8")
    check("A4 the sweep reuses phase 2's definition of agreement",
          "from phase2_compare import" in sweep_src
          and "compare_payload" in sweep_src,
          "one definition of 'agree', not two")
    check("A5 no script imports the UI",
          not any("ui" in _imports(p) for p in (ROOT / "scripts").glob("*.py")),
          "the dependency runs ui -> variants -> gl_engine")

    print("\nB  EVERY OPTION IS ISO'S")
    d = V.Declared("OK")
    opts = V.options_for(d)
    from gl_engine.schema import Schema                       # noqa: E402
    sch = Schema.for_book(d.book)
    declared_pd, _ = sch.resolved_values("GeneralLiability", "PremOpsPDDeductible")
    check("B1 a dropdown's options are the domain table's values",
          tuple(opts["premops_pd_deductible"]["values"]) == declared_pd,
          f"{len(declared_pd)} values, read from ISO not from the sample")
    try:
        V.build({"premops_pd_deductible": "6,500 Per Fortnight"}, d)
        refused = False
    except V.VariantError:
        refused = True
    check("B2 an undeclared value is refused before anything is sent", refused)
    check("B3 the class code list comes from the basis table, not the field",
          len(opts["class_code"]["values"]) > 1000
          and not sch.get("GeneralLiabilityClassification", "ClassCode").domain,
          f"{len(opts['class_code']['values'])} codes; the field itself "
          f"declares no domain")
    check("B4 choosing a basis narrows the codes to that basis",
          0 < len(V.options_for(d, {"premium_basis": "Area"})["class_code"]["values"])
          < len(opts["class_code"]["values"]),
          f"Area -> "
          f"{len(V.options_for(d, {'premium_basis': 'Area'})['class_code']['values'])}")

    print("\nC  A KEYED DOMAIN COLLAPSES WHEN ITS KEY IS ANSWERED")
    free = V.options_for(d)["premops_bipd_deductible"]["values"]
    pinned = V.options_for(
        d, {"premops_pd_deductible": "5,000 Per Occurrence"}
    )["premops_bipd_deductible"]["values"]
    check("C1 combined BI/PD collapses once PD is set",
          len(free) > 1 and list(pinned) == ["No Deductible"],
          f"{len(free)} -> {pinned}")
    try:
        V.build({"premops_pd_deductible": "5,000 Per Occurrence",
                 "premops_bipd_deductible": "10,000 Per Occurrence"}, d)
        both = True
    except V.VariantError:
        both = False
    check("C2 setting both split and combined is refused", not both,
          "ISO declares them mutually exclusive")

    print("\nH  THE EFFECTIVE DATE CANNOT DISAGREE WITH ITSELF (decision A3)")
    from gl_engine.config import CLASS_BASIS_CLIFF, MIN_ASOF     # noqa: E402
    from gl_engine.rating import Kernel, STRICT                  # noqa: E402
    ed_opts = V.BY_ID["effective_date"].options(d, {})
    check("H1 the options are the corpus's own edition boundaries, not an "
          "invented list",
          MIN_ASOF in ed_opts and CLASS_BASIS_CLIFF in ed_opts
          and all(len(x) == 8 and x.isdigit() for x in ed_opts),
          f"{len(ed_opts)} dates for OK, floor and cliff both present")

    cfg_cliff = {"effective_date": CLASS_BASIS_CLIFF}
    d_cliff = V.Declared.for_config("NY", cfg_cliff)
    check("H2 Declared.for_config resolves at the config's date, not "
          "DEFAULT_ASOF",
          d_cliff.asof == CLASS_BASIS_CLIFF and d_cliff.asof != V.DEFAULT_ASOF,
          f"resolved asof={d_cliff.asof}")

    payload_cliff = V.build(cfg_cliff, d_cliff)
    check("H3 the same date lands in the payload's own SchemeKeys",
          payload_cliff["body"]["SchemeKeys"]["EffectiveDateTime"]
          == "2027-04-01T00:00:00",
          payload_cliff["body"]["SchemeKeys"]["EffectiveDateTime"])

    kernel_h = Kernel(mode=STRICT, resolver=V.Declared.resolver())
    r_cliff = kernel_h.rate(payload_cliff)
    d_pkgs = (d_cliff.book.resolution.state.pkg_id,) + (
        (d_cliff.book.resolution.parent.pkg_id,)
        if d_cliff.book.resolution.parent else ())
    check("H4 the engine resolves the SAME edition Declared did -- the "
          "defect decision A3 named, closed by construction",
          r_cliff.complete and r_cliff.packages == d_pkgs,
          f"Declared={d_pkgs}, Kernel={r_cliff.packages if r_cliff.complete else r_cliff.stopped}")

    d_before = V.Declared.for_config("NY", {})
    check("H5 leaving effective_date unset still resolves DEFAULT_ASOF, "
          "unchanged from before this control existed",
          d_before.asof == V.DEFAULT_ASOF, d_before.asof)

    try:
        V.build({"effective_date": "not-a-date"}, d)
        bad_date_refused = False
    except V.VariantError:
        bad_date_refused = True
    check("H6 a malformed date is refused, not silently written",
          bad_date_refused)

    # OI-96: the 2027 filing dropped " CSL" from limit values in most states'
    # ILF tables. TX is one of the 7 CORE states that stopped outright before
    # this was fixed by renormalizing the base's own limit fields.
    cfg_96 = {"effective_date": CLASS_BASIS_CLIFF}
    d_96 = V.Declared.for_config("TX", cfg_96)
    p_96 = V.build(cfg_96, d_96)
    check("H7 OI-96: a stored limit figure is renormalized to the resolved "
          "edition's own spelling",
          p_96["body"]["GeneralLiability"][0]["PremOpsProdsEachOccurrenceLimit"]
          == "1,000,000",
          p_96["body"]["GeneralLiability"][0]["PremOpsProdsEachOccurrenceLimit"])
    r_96 = kernel_h.rate(p_96)
    check("H8 ...and TX rates past the cliff instead of stopping on the "
          "lookup miss",
          r_96.complete, f"stopped={r_96.stopped}" if not r_96.complete else "")

    cfg_96b = {"effective_date": CLASS_BASIS_CLIFF, "occurrence_limit": "500,000"}
    d_96b = V.Declared.for_config("TX", cfg_96b)
    p_96b = V.build(cfg_96b, d_96b)
    check("H9 ...and a control that sets the SAME field stays authoritative "
          "-- renormalization never overwrites a value someone chose",
          p_96b["body"]["GeneralLiability"][0]["PremOpsProdsEachOccurrenceLimit"]
          == "500,000",
          p_96b["body"]["GeneralLiability"][0]["PremOpsProdsEachOccurrenceLimit"])

    print("\nD  NOT APPLICABLE IS NOT DISAGREEMENT")
    cm = variables.legality({"coverage_form": "Claims Made"})
    check("D1 claims-made is applicable in 50 of 51, and NY is the exception",
          len(cm["applicable"]) == 50 and list(cm["not_applicable"]) == ["NY"],
          cm["summary"])
    two = variables.legality({"locations": 2})
    check("D2 two locations is undeclarable in the single-territory states",
          len(two["applicable"]) == 31,
          f"{two['summary']}; {len(two['not_applicable'])} declare one "
          f"prem/ops territory")
    check("D3 the reason is readable, not a stack trace",
          "territor" in next(iter(two["not_applicable"].values())).lower(),
          next(iter(two["not_applicable"].values()))[:80])

    # D4-D6: OI-93. A variant that rates and leaves the premium alone reads
    # exactly like one that worked, and two very different things cause it.
    # Nothing distinguished them until 2026-08-17.
    from gl_engine.rating import Kernel, STRICT
    kern = Kernel(mode=STRICT, resolver=V.Declared.resolver())

    def probe(juris, cfg):
        d = V.Declared(juris)
        return V.probe_no_op(cfg, d, kern, kern.rate(d.base()).premium)

    # The INERT VALUE this test was built on was OI-130: NY terrorism in territory 001 without the Manhattan
    # answer priced terrorism $0. B-07 fixed the builder (it answers Manhattan) and made the engine refuse the
    # unanswered form, so the shape is reproduced here on purpose: a jurisdiction that does not declare the
    # Manhattan question, with the rating-input refusals off. The detector must still name it.
    from gl_engine.rating import kernel as KM

    class NoManhattan(V.Declared):
        def values(self, table, column):
            return [] if column == "CertifiedActsOfTerrorismManhattan" else super().values(table, column)

    was, KM.RATING_INPUTS_CHECK = KM.RATING_INPUTS_CHECK, "off"
    try:
        d = NoManhattan("NY")
        ny = V.probe_no_op({"terrorism": "Yes"}, d, kern, kern.rate(d.base()).premium)
    finally:
        KM.RATING_INPUTS_CHECK = was
    check("D4 an INERT VALUE is named, with the value that would have moved it",
          ny["verdict"] == V.INERT_VALUE and ny["chosen"] == "001"
          and ny["moves_with"] == "002",
          f"NY {ny.get('column')}={ny.get('chosen')} does nothing; "
          f"{ny.get('moves_with')} gives {ny.get('premium')}")
    ny_now = probe("NY", {"terrorism": "Yes"})
    check("D4b and since B-07 (OI-130) the builder answers Manhattan, so NY terrorism moves the premium",
          ny_now["verdict"] == V.MOVED, f"NY terrorism: {ny_now['verdict']} {ny_now.get('premium', '')}")
    ok_sched = probe("OK", {"schedule_rating": "Yes"})
    check("D5 an INERT CONTROL is distinguished from it -- that one is ISO's "
          "filing, not our pick",
          ok_sched["verdict"] == V.INERT_CONTROL,
          f"OK schedule rating: {ok_sched['verdict']} (OI-89's gate)")
    ok_terr = probe("OK", {"terrorism": "Yes"})
    check("D6 and a variant that does move is not reported as either",
          ok_terr["verdict"] == V.MOVED,
          f"OK terrorism moved to {ok_terr.get('premium')}")

    print("\nR  PASS 3 -- IS A 'NOT APPLICABLE' REAL, OR IS IT OURS?")
    import qa_review as QR                                    # noqa: E402

    # The detector must detect. Fed the exact shape that fooled this project
    # for three days -- our own refusal wearing a readable reason, where ISO's
    # files say the value is perfectly legal -- it has to say so.
    oi91 = QR.review_not_applicable(
        "MT", {"terrorism": "Yes"},
        "MT declares neither a ZipCode nor a TerrorismTerritory domain")
    check("R1 the OI-91 shape is caught: our refusal, ISO's blessing",
          oi91["verdict"] == QR.CONTRADICTED,
          "MT declares TerrorismCoverage=Yes, so a refusal there is ours")

    # ...and it must not simply cry CONTRADICTED at everything.
    ny = QR.review_not_applicable("NY", {"coverage_form": "Claims Made"},
                                  "NY declares Occurrence only")
    check("R2 ...and a real narrowing is still confirmed",
          ny["verdict"] == QR.CONFIRMED,
          "NY declares one coverage form, and it is not Claims Made")

    # A configuration is refused when ONE control cannot be expressed. Every
    # other control in it being legal is the normal case -- aggregating
    # worst-first produced 20+ false findings on the first run.
    mixed = QR.review_not_applicable(
        "MT", {"locations": 2, "occurrence_limit": "100,000 CSL"},
        "MT declares 1 prem/ops territory")
    check("R3 one undeclarable control settles it; the legal ones are not "
          "findings",
          mixed["verdict"] == QR.CONFIRMED
          and mixed["cause"]["control"] == "locations",
          f"cause: {mixed['cause']['why'][:70] if mixed['cause'] else None}")

    # --- pass 4: the adversarial brief. Its value is entirely in how it asks.
    b = QR.brief("Our premium for OK is correct.",
                 {"jurisdiction": "OK", "our premium": "8229"},
                 "Which filed rule decides it?")
    check("R6 pass 4 asks every reviewer to REFUTE, never to confirm",
          all("REFUTE" in t and "Assume it is wrong" in t
              for t in b["prompts"].values()),
          "an agent asked 'is this right?' tends to agree")
    check("R7 ...and forbids each reviewer the other's corpus",
          all("independent" in t and "Do not consult" in t
              for t in b["prompts"].values()),
          "agreement between two corpora is evidence only while they stay "
          "independent")
    check("R8 ...and allows CANNOT TELL as a real answer",
          all("CANNOT TELL is a real answer" in t
              for t in b["prompts"].values()),
          "a forced verdict is a guess wearing a citation")
    check("R9 one reviewer per source, and the source is named in the prompt",
          set(b["prompts"]) == set(QR.REVIEWERS)
          and all(QR.REVIEWERS[a].split()[0].upper() in t.upper()
                  for a, t in b["prompts"].items()),
          ", ".join(sorted(QR.REVIEWERS)))

    # A clean agreement must NOT generate a brief: there is no claim to break,
    # and a review queue full of confirmations is a review queue nobody reads.
    briefs = QR.briefs_for_run("T1")
    kinds = {("refuse" in x["claim"]) for x in briefs}
    check("R10 only results worth refuting become briefs",
          all(("refuse" in x["claim"] or "differs" in x["claim"]
               or "moved nothing" in x["claim"]) for x in briefs),
          f"{len(briefs)} brief(s) from disagreements, refusals and inert "
          f"values -- never from a clean agreement")

    # Everything the stored runs actually refused must be ISO's narrowing.
    rev = QR.review_runs("T1")
    check("R4 every NOT APPLICABLE on record is ISO's, not ours",
          rev["counts"][QR.CONTRADICTED] == 0,
          f"{rev['reviewed']} reviewed: "
          f"{rev['counts'][QR.CONFIRMED]} confirmed, "
          f"{rev['counts'][QR.UNVERIFIED]} unverified")

    # The pass reads ISO's CSVs, never the code that made the decision.
    #
    # Scoped to the VERDICT path, not the whole module. Pass 4's payload export
    # legitimately calls `V.build` -- it regenerates an input so a person can
    # send it, which is not re-deriving a conclusion. Asserting over the file
    # rather than the function conflated the two and failed on a legitimate
    # use, which is how a good assertion turns into one people delete.
    src = (ROOT / "scripts" / "qa_review.py").read_text(encoding="utf-8")
    start = src.index("def review_not_applicable(")
    verdict_path = src[:src.index("def review_runs(")]
    verdict_path = verdict_path[verdict_path.index("def _declared_domain("):]
    borrowed = [n for n in ("V.build(", "control.options(", ".resolved_values(",
                            "Declared(")
                if n in verdict_path]
    check("R5 the verdict path re-derives independently rather than asking "
          "the same code",
          not borrowed,
          "reads Fields.FormField.csv and the domain CSVs directly"
          if not borrowed else f"borrows: {borrowed}")


    print("\nM  MULTI-CLASS -- THE ARRAY TWICE, WITH DIFFERENT VALUES IN IT")
    ok = V.Declared("OK")
    base_prem = None
    from gl_engine.rating import Kernel as _K, STRICT as _S
    from gl_engine import EditionResolver as _R
    _k = _K(mode=_S, resolver=_R())
    base_prem = _k.rate(ok.base()).premium

    two = V.build({"classifications": 2}, ok)
    cls = V._classes(V._locations(two)[0])
    check("M1 asking for two classifications produces two",
          len(cls) == 2, f"{len(cls)} in the first location")
    codes = [str(c.get("ClassCode")) for c in cls]
    check("M2 they carry DIFFERENT class codes",
          len(set(codes)) == 2,
          f"{codes} -- 99 of ISO's own 114 multi-class locations differ")
    bases = [c.get("PremOpsPremiumBasis") for c in cls]
    check("M3 and different premium bases, which is where the divisor bites",
          len(set(bases)) == 2,
          f"{bases} -- per $1,000 for both, but Each and Units have no divisor "
          f"at all, so one divisor per location is wrong here")
    check("M4 the second basis is money, like the first, so the inherited "
          "exposure stays plausible",
          bases[1] in V.PREFERRED_SECOND_BASIS,
          f"{bases[1]}; 5,000,000 of Payroll is a real risk, 5,000,000 square "
          f"feet is a hundred city blocks")
    r2 = _k.rate(two)
    check("M5 it rates, and the premium moves",
          r2.complete and r2.premium != base_prem,
          f"base {base_prem} -> {r2.premium}")

    # Three must add a third distinct code, not repeat the second.
    three = V.build({"classifications": 3}, ok)
    codes3 = [str(c.get("ClassCode")) for c in V._classes(V._locations(three)[0])]
    check("M6 a third classification is distinct again",
          len(set(codes3)) == 3, str(codes3))

    # Fewer than the base carries must truncate rather than raise.
    one = V.build({"classifications": 1}, ok)
    check("M7 asking for one leaves one",
          len(V._classes(V._locations(one)[0])) == 1)

    print("\nX  EXPERIENCE RATING -- THE PERIOD ISO'S SAMPLES CARRY (B-40)")
    xp = V.build({"experience_rating": "Yes", "erp_years": 2}, ok)
    risk = V._gl(xp)
    check("X1 Yes writes the experience period, dated from the effective date",
          risk.get("ERPLatestYearEffectiveDate") == "2024-04-01"
          and risk.get("ERPLatestYearLatestValuationDate") == "2025-10-01"
          and risk.get("ERPSecondLatestYearEffectiveDate") == "2023-04-01",
          f"{risk.get('ERPLatestYearEffectiveDate')} valued {risk.get('ERPLatestYearLatestValuationDate')}")
    check("X2 a year outside the period gets no dates and no losses",
          "ERPThirdLatestYearEffectiveDate" not in risk and risk.get("ERPThirdLatestYearTotalIncludedLoss") == 0.0
          and risk.get("ExperienceBusinessStartDate") == "2023-04-01")
    try:
        V.build({"erp_annual_loss": 1000}, ok)
        refused = False
    except V.VariantError:
        refused = True
    check("X3 losses without experience rating are refused, not ignored", refused)
    # ISO-confirmed 2026-10-15 (10 calls, every published field exact): credit, debit and the 0.07 credibility gate
    for label, cfg, want in (("X4 credit", {"exposure": 50000000}, 74323),
                             ("X5 debit", {"exposure": 50000000, "erp_annual_loss": 100000}, 122233),
                             ("X6 credibility 0.03, below ISO's 0.07: no modification", {}, base_prem)):
        got = _k.rate(V.build({"experience_rating": "Yes", **cfg}, ok)).premium
        check(f"{label} prices as ISO does", got == want, f"{got}, ISO {want}")


    print("\nE  THE STORE, AND THE LONG VIEW BUILT FROM IT")
    tmp = Path(tempfile.mkdtemp(prefix="tester-store-"))
    real = store.RESULTS
    store.RESULTS = tmp
    try:
        summary = {"config": {"premops_pd_deductible": "5,000 Per Occurrence"},
                   "fingerprint": "abc123", "describes": "PD=5,000",
                   "compared": True, "total": 3, "rated": 3, "agree": 2,
                   "differ": ["GA"], "not_applicable": [], "premium_only": [],
                   "engine_stopped": [], "errors": [], "unmoved": ["GA"]}
        rows = [{"juris": "OK", "status": "MATCH", "ours": "8209", "iso": "8209.0"},
                {"juris": "NY", "status": "MATCH", "ours": "12051", "iso": "12051.0"},
                {"juris": "GA", "status": "DIFF", "ours": "6845", "iso": "6800.0",
                 "detail": "made up, for the test"}]
        line = store.append(summary, rows, engine_version="test")
        check("E1 a run round-trips", store.run(line["id"]) is not None,
              line["id"])
        check("E2 history is oldest first and carries the agreement",
              store.history()[-1]["agree"] == 2)
        cov = store.coverage()
        check("E3 coverage counts only jurisdictions that actually rated",
              sorted(cov["rated"]["premops_pd_deductible"]) == ["GA", "NY", "OK"])
        defects = store.defects()
        check("E4 a disagreement becomes a defect row with first and last seen",
              len(defects) == 1 and defects[0]["juris"] == "GA"
              and defects[0]["first_seen"] == defects[0]["last_seen"])
        # Append-only: a second identical run must not overwrite the first.
        store.append(summary, rows, engine_version="test")
        check("E5 the store is append-only", len(store.runs()) == 2,
              "a corrected run is a new line; the old one stays as the record")

        # "What changed since last run" -- one tier, two batches.
        base = {"fingerprint": "fp1", "compared": True, "live_calls": 1,
               "describes": "base", "agree": 0, "differ": [],
               "premium_only": [], "not_applicable": [], "engine_stopped": []}
        store.append(base, [{"juris": "TX", "status": "DIFF"},
                            {"juris": "NY", "status": "MATCH"}],
                    label="qa T1", batch="T1-older")
        # The store orders by its timestamp, to the second: two appends in the same second could sort either way,
        # which made E6 fail now and then (seen 2026-10-07). A real tier's executions are minutes apart.
        import time
        time.sleep(1.1)
        store.append(base, [{"juris": "TX", "status": "MATCH"},
                            {"juris": "NY", "status": "MATCH"},
                            {"juris": "CA", "status": "DIFF"}],
                    label="qa T1", batch="T1-newer")
        check("E6 batches groups a tier's executions, most recent first",
              store.batches("T1", limit=2) == ["T1-newer", "T1-older"],
              store.batches("T1", limit=2))
    finally:
        store.RESULTS = real
        shutil.rmtree(tmp, ignore_errors=True)

    print("\nF  CHARTS")
    check("F1 an empty chart says what would fill it",
          "<svg" in charts.empty("nothing yet")
          and "nothing yet" in charts.empty("nothing yet"))
    grid = charts.coverage_grid([{"id": "a", "label": "A"}], ["OK", "NY"],
                                {"a": ["OK"]}, {"a": ["NY"]})
    check("F2 the coverage grid distinguishes rated from declined",
          "rated" in grid and "not declarable here" in grid)
    bars = charts.status_bars({"compared": True, "agree": 2, "rated": 3,
                               "differ": ["GA"], "not_applicable": ["NY"],
                               "premium_only": [], "engine_stopped": [],
                               "errors": []})
    check("F3 not-applicable is drawn in grey, never as a failure",
          charts.GREY in bars and "not applicable here" in bars)
    curve = charts.response_curve("Deductible", {
        "OK": [{"value": "a", "ours": "100"}, {"value": "b", "ours": "90"}]})
    check("F4 a curve draws a path per jurisdiction", "<path" in curve)

    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
