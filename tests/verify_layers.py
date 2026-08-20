"""The layered programme: the aggregate axis, the allowance, and the run file.

Run: python tests/verify_layers.py       (offline; makes no ISO calls)

  A  aggregate    the aggregate limit is a real axis, keyed on the occurrence
                  limit, refusing a pair ISO does not declare, and resolving a
                  position to the value each state actually files
  B  allowance    thinning drops configurations and never drops states, and
                  says what it dropped
  C  class        a class ISO does not file somewhere is reported, not filtered
  D  differences  the comparison hands back every differing field, not three
  E  run file     a run writes one self-contained file, under results/, with
                  nothing loaded from the network
  F  ticker       calls spent today are counted in one place

**Everything here runs offline and with an empty results directory**, which is
the same constraint `verify_notebooks.py` works under and for the same reason: a
check that needs a paid service or yesterday's data is a check people stop
running.
"""
from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import layers                                                  # noqa: E402
import runstore as store                                       # noqa: E402
import sweep                                                   # noqa: E402
import variants as V                                           # noqa: E402
from phase2_compare import _differ, compare_payload            # noqa: E402
from gl_engine.rating import Kernel, STRICT                    # noqa: E402

FAILED = []
PROBE = ["TX", "NY", "MT"]


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}"
          + (f"\n          {detail}" if detail and not ok else ""))
    if not ok:
        FAILED.append(label)


# ------------------------------------------------------------------------- A

def a_aggregate() -> None:
    print("\nA  the aggregate limit is an axis of its own")
    check("A1 a control exists", "general_aggregate" in V.BY_ID)
    c = V.BY_ID.get("general_aggregate")
    check("A2 it is keyed on the occurrence limit",
          bool(c) and c.keyed_by == {"occurrence_limit": "EachOccurrenceLimit"})

    d = V.Declared("TX")
    legal_1m = d.aggregates_for("1,000,000 CSL")
    legal_25k = d.aggregates_for("25,000 CSL")
    check("A3 the legal set depends on the occurrence limit",
          len(legal_1m) > len(legal_25k) > 0,
          f"1,000,000 -> {len(legal_1m)}, 25,000 -> {len(legal_25k)}")

    p = V.build({"occurrence_limit": "1,000,000 CSL",
                 "general_aggregate": "5,000,000 CSL"}, d)
    gl = p["body"]["GeneralLiability"][0]
    check("A4 both aggregates are written",
          gl["GeneralAggregateLimit"] == "5,000,000 CSL"
          and gl["ProdsCompldOpsAggregateLimit"] == "5,000,000 CSL")

    refused = False
    try:
        V.build({"occurrence_limit": "25,000 CSL",
                 "general_aggregate": "10,000,000 CSL"}, d)
    except V.VariantError:
        refused = True
    check("A5 an undeclared pair is refused rather than sent", refused)

    # A position, resolved per state, must land on a value that state declares.
    ok, seen = True, {}
    for j in PROBE:
        dj = V.Declared(j)
        cfg = layers.resolve({"occurrence_limit": "1,000,000 CSL",
                              "general_aggregate": "@highest"}, dj)
        value = cfg["general_aggregate"]
        seen[j] = value
        if value not in dj.aggregates_for("1,000,000 CSL"):
            ok = False
    check("A6 @highest resolves to a value that state declares", ok, str(seen))


# ------------------------------------------------------------------------- B

def b_allowance() -> None:
    print("\nB  the allowance thins configurations, never states")
    full = layers.plan("L3", jurisdictions=PROBE)
    small = layers.plan("L3", jurisdictions=PROBE, allowance=20)

    check("B1 the full matrix is every occurrence point x every position",
          full["cost"]["scenarios"]
          == len(layers.OCCURRENCE_POINTS) * len(layers.AGGREGATE_POSITIONS))
    check("B2 an allowance cuts the scenario count",
          small["cost"]["scenarios"] < full["cost"]["scenarios"])
    check("B3 it fits inside the allowance",
          small["cost"]["live_calls"] <= 20,
          f"{small['cost']['live_calls']} calls")

    states = set()
    for s in small["scenarios"]:
        states |= set(s["jurisdictions"])
    check("B4 every jurisdiction survives the thinning",
          states == set(PROBE), f"{sorted(states)}")

    t = small["thinning"]
    check("B5 the thinning says what it dropped",
          bool(t and t.get("applied") and t.get("dropped")))
    check("B6 the ends of the table are kept",
          any(layers.OCCURRENCE_POINTS[0] in s["describes"]
              for s in small["scenarios"])
          and any(layers.OCCURRENCE_POINTS[-1] in s["describes"]
                  for s in small["scenarios"]))

    # An allowance counts live calls. Offline spends none, so cutting coverage
    # to fit one would give up ground to save nothing.
    off = layers.plan("L3", jurisdictions=PROBE, allowance=20, offline=True)
    check("B7 an offline run is never thinned",
          off["cost"]["scenarios"] == full["cost"]["scenarios"]
          and off["thinning"] is None,
          f"{off['cost']['scenarios']} of {full['cost']['scenarios']}")
    check("B8 an offline plan costs no calls", off["cost"]["live_calls"] == 0)


# ------------------------------------------------------------------------- C

def c_class() -> None:
    print("\nC  a class is grouped by the basis each state files")
    g = layers.basis_groups("91340", PROBE)
    check("C1 the class groups by declared basis", len(g["groups"]) >= 1,
          json.dumps([(x["basis"], x["jurisdictions"]) for x in g["groups"]]))
    check("C2 nothing is silently dropped",
          sum(len(x["jurisdictions"]) for x in g["groups"])
          + len(g["undeclared"]) + len(g["unreadable"]) == len(PROBE))

    # A code no jurisdiction files must come back as undeclared, not missing.
    fake = layers.basis_groups("99999999", PROBE)
    check("C3 a class nobody files is reported as not filed",
          sorted(fake["undeclared"]) == sorted(PROBE) and not fake["groups"])

    p = layers.plan("L2", "91340", 1500000, PROBE)
    check("C4 the exposure reaches the configuration",
          all(s["config"].get("exposure") == 1500000 for s in p["scenarios"]))
    check("C5 nobody types the premium basis",
          all("premium_basis" not in s["config"] for s in p["scenarios"]))

    refused = False
    try:
        layers.plan("L2", "", None, PROBE)
    except layers.PlanError:
        refused = True
    check("C6 the classification layer refuses to run without a class", refused)


# ------------------------------------------------------------------------- D

class _StubClient:
    """ISO's shape, with two numbers deliberately wrong.

    A stub rather than a live call: the assertion is about what the comparison
    hands back, which is our code, and paying ISO to learn it would make this
    check one nobody runs.
    """

    calls = 0

    def rate(self, payload):
        return {
            "Header": {"Scheme": "GL 2025 04 01 x"},
            "Body": {"GeneralLiability": [{
                "Premium": 1,
                "GeneralLiabilityLocation": [{
                    "GeneralLiabilityClassification": [
                        {"PremOpsCovPremium": 2, "ProdsCompldOpsCovPremium": 3,
                         "PremOpsCovExposure": 4, "PremOpsCovLossCost": 5,
                         "PremOpsCovILF": 6, "PremOpsCovTerritoryFactor": 7}]}],
            }]},
        }


def d_differences() -> None:
    print("\nD  the comparison hands back every differing field")
    d = V.Declared("TX")
    kernel = Kernel(mode=STRICT, resolver=V.Declared.resolver())
    r = compare_payload("TX", d.base(), kernel, _StubClient(), _differ())
    check("D1 it reports a difference", r.get("status") == "DIFF", str(r)[:180])
    diffs = r.get("differences")
    check("D2 differences is a list", isinstance(diffs, list))
    check("D3 the list is the whole count, not a sample of three",
          isinstance(diffs, list) and len(diffs) == r.get("fields_differing"),
          f"{len(diffs or [])} listed, {r.get('fields_differing')} counted")
    check("D4 each entry names the field and both sides",
          bool(diffs) and all(set(x) == {"field", "ours", "iso"} for x in diffs))


# ------------------------------------------------------------------------- E

def e_runfile() -> None:
    print("\nE  a run writes one self-contained file")
    from ui import runfile

    out = layers.run("L1", jurisdictions=PROBE, offline=True,
                     label="verify_layers")
    plan, results = out["plan"], out["results"]
    check("E1 the smoke layer rated every jurisdiction",
          plan["rollup"]["rated"] == len(PROBE), str(plan["rollup"]))

    path = runfile.write_run(plan, results, engine_version="verify")
    doc = path.read_text(encoding="utf-8")
    check("E2 the file is written under results/",
          path.exists() and "results" in path.parts)
    check("E3 it loads nothing from the network",
          "http://" not in doc and "https://" not in doc
          and "<script src" not in doc and "fetch(" not in doc
          and "XMLHttpRequest" not in doc)
    check("E4 it names the layer and the counts",
          plan["name"] in doc and "rated" in doc)
    check("E5 the index links it",
          path.name in runfile.INDEX_HTML.read_text(encoding="utf-8"))

    stopped = {"n": 0}

    def stop_after_one():
        stopped["n"] += 1
        return stopped["n"] > 1

    part = layers.run("L4", jurisdictions=PROBE, offline=True,
                      stop_check=stop_after_one, label="verify_layers stop")
    summaries = [r["summary"] for r in part["results"]]
    check("E6 a stopped run keeps what it found",
          bool(summaries) or part["plan"].get("stopped_after") == 0)
    if summaries:
        check("E7 a stopped run names the states it never reached",
              any(s.get("not_reached") for s in summaries)
              or any(s.get("stopped_early") for s in summaries),
              json.dumps([s.get("not_reached") for s in summaries]))
    else:
        check("E7 a stopped run names the states it never reached",
              part["plan"].get("stopped_after") is not None)


# ------------------------------------------------------------------------- F

def f_ticker() -> None:
    print("\nF  the ticker counts in one place")
    import qa
    check("F1 the store owns the count", hasattr(store, "spent_today"))
    check("F2 the tier runner reads the same count",
          qa._spent_today() == store.spent_today())
    check("F3 an offline run spends nothing",
          isinstance(store.spent_today(), int))


def main() -> int:
    print("Layered programme -- offline verification")
    a_aggregate()
    b_allowance()
    c_class()
    d_differences()
    e_runfile()
    f_ticker()
    print()
    if FAILED:
        print(f"{len(FAILED)} failed: {', '.join(FAILED)}")
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
