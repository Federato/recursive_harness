"""G1 of docs/RATING-GRAPH-PLAN.md: the rating graph records a rating and changes nothing.

Run: python tests/verify_rating_graph.py [--per-state N]        (offline; no ISO calls)

  A  unchanged     with the graph ON, every rating in the sample is the same rating, field for field, with the
                   same outcome and messages (the graph OFF is the snapshot regression, run apart)
  B  complete      every field the rules wrote has a write node, one per write; every read and lookup resolves to a
                   node; no edge points at a node that does not exist
  C  replay        plain Product and Sum writes, re-applied to the values on their data edges, give the written
                   value (rounded as filed)
  D  sources       a carrier's rating shows its sources: each group LCM and record LCM as a company node, a
                   company table row marked; a premium's ancestry reaches the filing row that moved it
  E  control       a branch's writes carry control edges to what its test read

The sample: one stored Property request per state, GL in six states, and UFG's Iowa filing.
    python scripts/cf/206_snapshot_regression.py --check     # the graph OFF: nothing moved
"""
from __future__ import annotations

import argparse
import copy
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for p in (ROOT, ROOT / "scripts", ROOT / "scripts" / "cf", ROOT / "tests"):
    sys.path.insert(0, str(p))

import verify_deviations_engine as E                      # noqa: E402  (stored requests, trees, the UFG fixture)

FAILED, CHECKS = [], []


def check(label: str, ok: bool, detail: str = "") -> None:
    CHECKS.append((label, ok))
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}" + (f"\n          {detail}" if detail and not ok else ""))
    if not ok:
        FAILED.append(label)


def _written_paths(tree, trace) -> list:
    from console import worksheet as W
    _, ids = W.our_leaves(tree)
    return [ids[t.data["node"]] for t in trace if t.kind == "write" and t.data.get("node") in ids]


def cases(per_state: int):
    from console import catalog
    out = []
    for name, st, _, req in E.per_state(E.stored(), per_state):
        out.append(("CF", f"{st} {name[:40]}", req))
    for st in ("TX", "NY", "CA", "OH", "FL", "IL"):
        out.append(("GL", f"GL {st}", catalog.build("GL", st, {})))
    return out


def rate(line, req, graph):
    if line == "CF":
        from cf_engine.rating import rate as cf_rate
        r = cf_rate(copy.deepcopy(req), graph=graph)
        return r.tree, (r.ip.trace if r.ip is not None else []), r.outcome.get("status"), \
            sorted(map(str, r.ip.messages)) if r.ip is not None else [], r.graph
    from gl_engine.rating import Kernel
    r = Kernel().rate(copy.deepcopy(req), graph=graph)
    return r.tree, r.trace, r.complete, sorted(map(str, r.messages)), getattr(r, "deps", None) if graph else None


def a_b_c(per_state: int) -> None:
    print("\nA  the graph changes nothing   B  it is complete   C  its operations replay")
    moved, incomplete, dangling, replayed, wrong = [], [], [], 0, []
    n = 0
    for line, label, req in cases(per_state):
        t0, tr0, out0, msg0, _ = rate(line, req, False)
        t1, tr1, out1, msg1, g = rate(line, req, True)
        n += 1
        if out0 != out1 or msg0 != msg1 or (t0 is not None and E.tree_diff(t0, t1, minted=())):
            moved.append(label)
            continue
        if g is None or t1 is None:
            continue
        writes = _written_paths(t1, tr1)
        gw = [x for x in g.nodes if x["kind"] == "write"]
        if len(gw) != sum(1 for t in tr1 if t.kind == "write"):
            incomplete.append(f"{label}: {len(gw)} write nodes for "
                              f"{sum(1 for t in tr1 if t.kind == 'write')} writes")
        missing = [p for p in set(writes) if g.nodes[g.final.get(p, 0)]["kind"] != "write" or p not in g.final]
        if missing:
            incomplete.append(f"{label}: {len(missing)} written fields without a final write node, e.g. {missing[:2]}")
        lookups = sum(1 for t in tr1 if t.kind in ("lookup", "lookup-banded", "lookup-interpolated"))
        if lookups and not any(x["kind"] == "table" for x in g.nodes):
            incomplete.append(f"{label}: {lookups} lookups, no table node")
        bad_edges = [(s, d) for s, d, _ in g.edges() if not (0 <= s < len(g.nodes) and 0 <= d < len(g.nodes))]
        if bad_edges:
            dangling.append(f"{label}: {bad_edges[:2]}")
        for x in gw:
            got = g.replay(x["id"])
            if got is None:
                continue
            replayed += 1
            if got[0] != got[1]:
                wrong.append(f"{label} {x.get('path', '').rsplit('/', 1)[-1]}: wrote {got[0]}, replay {got[1]}")
    check(f"A1 {n} ratings (Property in every state, GL in six) are unchanged with the graph on", not moved,
          ", ".join(moved[:5]))
    check("B1 one write node per write, and every written field's final value is a write node", not incomplete,
          "; ".join(incomplete[:3]))
    check("B2 no edge points at a node that does not exist", not dangling, "; ".join(dangling[:3]))
    check(f"C1 {replayed} plain Product and Sum writes replay to their written value", replayed >= 50 and not wrong,
          f"{replayed} replayed; " + "; ".join(wrong[:4]))


def d_sources() -> None:
    print("\nD  a carrier's sources are in its graph")
    from cf_engine.rating import rate as cf_rate
    root = E.tmp_root()
    r = cf_rate(E.ia_sample("UFC"), with_technical=True, waterfall=False, root=root, graph=True)
    g = r.graph
    comp = [x for x in g.nodes if x["kind"] == "company"]
    groups = {x.get("group") for x in comp if x.get("group")}
    check("D1 every coverage group the risk rates applied a company LCM node",
          {"GroupI", "GroupII", "Special"} <= groups, sorted(g for g in groups if g))
    check("D2 the record LCMs the carrier wrote are company nodes", any(x["label"].startswith("record LCM")
                                                                      for x in comp))
    p = next(p for p in g.final if p.endswith("CommercialPropertyStructure/FinalBasicGroupIIRate"))
    src = g.sources(g.final[p])
    lcm = [x for x in src if x["kind"] == "company"]
    check("D3 Building Group II's final rate traces back to the filing row that set its LCM (3.28, row #4)",
          any(x["value"] == "3.28" and "#4" in (x.get("explain") or "") for x in lcm), lcm[:2])
    t = r.technical.graph
    tp = next(p for p in t.final if p.endswith("CommercialPropertyStructure/FinalBasicGroupIIRate"))
    check("D4 technical's graph of the same value has no company source", not any(
        x["kind"] == "company" for x in t.sources(t.final[tp])))
    # a company table row
    E.filing(root, "ADD", "IA-CF-GTABLE", "CF", ["IA"], "2025-06-15",
             [{"target": "TABLE:BasicGroupIIRate.Rate", "scope": {}, "value": "1.1", "mode": "multiply"}])
    r2 = cf_rate(E.ia_sample("ADD"), waterfall=False, root=root, graph=True)
    rows = [x for x in r2.graph.nodes if x["kind"] == "table" and x["company"]]
    check("D5 a table a carrier overrode shows as a company table row", rows and rows[0]["table"] == "BasicGroupIIRate",
          rows[:1])


def e_control() -> None:
    print("\nE  control edges")
    import property_rating as pr
    from cf_engine.rating import rate as cf_rate
    g = cf_rate(pr.sample("IA", "2025-07-01"), graph=True).graph
    ctl = sum(1 for x in g.nodes if g.control.get(x["id"]))
    check(f"E1 writes decided by a test carry control edges ({ctl} of {len(g.nodes)} nodes)", ctl > 50, str(ctl))
    p = next(p for p in g.final if p.endswith("CommercialPropertyStructure/BGIIDeductibleByLocationFactor"))
    via = [g.nodes[s].get("path", "").rsplit("/", 1)[-1] for s in g.control.get(g.final[p], ())]
    check("E2 e.g. the Group II deductible-by-location factor is decided by the windstorm indicator's test",
          "WindstormHailIndicator" in via, via)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-state", type=int, default=1)
    a = ap.parse_args()
    a_b_c(a.per_state)
    d_sources()
    e_control()
    from deviations import suite_log
    suite_log.record("graph", CHECKS)
    print(f"\n{'FAILED: ' + ', '.join(FAILED) if FAILED else 'all passed'}")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
