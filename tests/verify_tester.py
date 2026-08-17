"""Variable tester acceptance: the controls, the routes and the separation.

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
  E  store          runs round-trip, and the long view is computed from them
  F  charts         every chart returns SVG, and an empty one says what would
                    fill it
  G  routes         the page and its API answer without a server running

**No live calls and no server.** `dispatch` is called directly and the results
store is redirected to a temporary directory, so this suite never touches the
real `results/` and never spends a call.

Run: python tests/verify_tester.py
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
from ui import charts, tester, variables                      # noqa: E402

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
    print("Variable tester acceptance -- no server, no live calls")

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

    ny = probe("NY", {"terrorism": "Yes"})
    check("D4 an INERT VALUE is named, with the value that would have moved it",
          ny["verdict"] == V.INERT_VALUE and ny["chosen"] == "001"
          and ny["moves_with"] == "002",
          f"NY {ny.get('column')}={ny.get('chosen')} does nothing; "
          f"{ny.get('moves_with')} gives {ny.get('premium')}")
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
    src = (ROOT / "scripts" / "qa_review.py").read_text(encoding="utf-8")
    borrowed = [n for n in ("V.build(", "control.options(", ".resolved_values(")
                if n in src]
    check("R5 it re-derives independently rather than asking the same code",
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


    print("\nQ  THE QA PROGRAMME -- TIERS, BUDGET, VERDICT AND MAP")
    import qa                                                 # noqa: E402
    code, body, _ = tester.dispatch("GET", "/api/tester/qa", {}, None)
    spec = json.loads(body)
    check("Q1 the tiers come from scripts/qa.py, not a second list",
          [t["id"] for t in spec["tiers"]] == sorted(qa.TIERS),
          f"{len(spec['tiers'])} tiers; one definition, as with 'agree'")
    unbuilt = [t["id"] for t in spec["tiers"] if not t["runnable"]]
    check("Q2 a tier that is not built says so rather than pretending",
          "T3" in unbuilt, f"not runnable: {unbuilt} -- each names what it needs")

    # The guard has to hold on the button as well as the command line, or the
    # budget becomes a matter of which door you came in by.
    real = qa._spent_today
    try:
        qa._spent_today = lambda: qa.DAILY_STANDING - 1
        code_over, body_over, _ = tester.dispatch(
            "POST", "/api/tester/qa/run", {}, {"tier": "T1"})
        code_off, _, _ = tester.dispatch(
            "POST", "/api/tester/qa/run", {}, {"tier": "T1", "offline": True})
    finally:
        qa._spent_today = real
    check("Q3 a tier over the daily budget is refused through the UI too",
          code_over == 429,
          f"HTTP {code_over}: {json.loads(body_over).get('detail', '')[:58]}")
    check("Q4 ...and offline is always allowed, because it costs nothing",
          code_off == 200, f"HTTP {code_off}")

    code, body, _ = tester.dispatch("POST", "/api/tester/qa/plan", {}, {"tier": "T1"})
    plan = json.loads(body)
    check("Q5 the matrix can be seen without running it",
          code == 200 and len(plan["scenarios"]) == plan["cost"]["scenarios"],
          f"{len(plan['scenarios'])} scenarios, {plan['cost']['live_calls']} "
          f"calls if run live")

    code, body, _ = tester.dispatch("GET", "/api/tester/qa/summary", {}, None)
    summ = json.loads(body)
    check("Q6 the verdict and the map are inline SVG with no external asset",
          summ["verdict"].startswith("<svg") and summ["map"].startswith("<svg")
          and "http" not in summ["map"],
          f"verdict {len(summ['verdict'])}b, map {len(summ['map'])}b")

    # A missing tile would silently drop a jurisdiction from the picture.
    missing = sorted(set(V.Declared.jurisdictions()) - set(charts.TILES))
    check("Q7 every jurisdiction has a tile on the map", not missing,
          "HI is drawn and permanently blank because ISO does not file it"
          if not missing else f"missing: {missing}")

    # not-applicable must never colour a tile as a failure.
    roll = store.qa_rollup()
    softened = [j for j, v in roll["status"].items() if v == "partial"]
    check("Q8 'not offered here' softens a tile, never fails it",
          all(v in ("differs", "refused", "agrees", "uncompared", "partial",
                    "untested") for v in roll["status"].values()),
          f"{roll['counts']['not_applicable']} not-applicable outcomes; "
          f"{len(softened)} tile(s) softened to 'partial'")


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

    print("\nG  ROUTES, WITHOUT A SERVER")
    code, body, kind = tester.dispatch("GET", "/tester", {}, None)
    check("G1 the page is served", code == 200 and kind == "html"
          and "Variable tester" in body, f"{len(body):,} bytes")
    code, body, kind = tester.dispatch("GET", "/api/tester/spec", {}, None)
    spec = json.loads(body)
    check("G2 the spec carries every control and every jurisdiction",
          len(spec["controls"]) == len(V.CONTROLS)
          and len(spec["jurisdictions"]) == 51,
          f"{len(spec['controls'])} controls over {len(spec['groups'])} groups")
    check("G3 the spec says where each value is legal, not just that it is",
          all("states" in v for c in spec["controls"] if c["kind"] == "select"
              for v in c["values"]),
          "so a dropdown can show '50/51 states'")
    code, body, _ = tester.dispatch("POST", "/api/tester/legality", {},
                                    {"config": {"coverage_form": "Claims Made"}})
    check("G4 legality answers without rating anything",
          json.loads(body)["summary"] == "50 of 51")
    code, body, _ = tester.dispatch("GET", "/api/tester/run/nope", {}, None)
    check("G5 an unknown run is a 404, not a crash", code == 404)
    check("G6 a path that is not the tester's is declined, not swallowed",
          tester.dispatch("GET", "/api/samples", {}, None) is None,
          "app.py keeps its own routes")

    print(f"\n{len(PASS)}/{len(PASS) + len(FAIL)} passed")
    for f in FAIL:
        print(f"  FAILED  {f}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
