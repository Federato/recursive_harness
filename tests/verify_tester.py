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
from ui import charts, store, tester, variables               # noqa: E402

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
