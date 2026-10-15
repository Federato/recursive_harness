"""P3: the proof that needs no ISO calls, and the live verdicts re-judged from stored answers (DEVIATIONS-PLAN.md §5).

Run: python tests/verify_deviations_proof.py [--no-live]        (offline; makes no ISO calls)

  T4  locality    every field a carrier changed is reachable in the rating graph (`gl_engine.interp.graph`) from the
                  carrier's own sources: its record LCMs, group LCMs and overridden table rows. Property and GL
  T6  arithmetic  a single table override: every lookup of that table returns ISO's value x the factor exactly,
                  and the waterfall adds up to carrier - technical exactly
  T7  boundaries  state, coverage, coverage group, the new-business date, new vs renewal, superseded versions,
                  a state opted out of an all-states filing, and a jurisdiction ISO added after it was taken
  T9  revision    one filing over two ISO editions: replace rows keep their value, multiply rows follow ISO's
                  new value, and the "ISO revised" flag is raised
  T5  LCMs       every group LCM a carrier applies is exactly the filed one, and each group's rate scales by its
                  own LCM -- proved against technical, offline (D21: ISO only ever rates technical; no LCM is sent)
  L   live        T3 and T8 re-judged from the answers ISO gave (`scripts/deviations_p3.py --judge`); skipped
                  with --no-live. A case ISO has not answered yet is reported "not run", which fails the gate.

T1, T2 and T10 are `verify_deviations_engine.py` and `verify_deviations_files.py`.
"""
from __future__ import annotations

import argparse
import copy
import json
import shutil
import sys
import tempfile
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for p in (ROOT, ROOT / "scripts", ROOT / "scripts" / "cf", ROOT / "tests"):
    sys.path.insert(0, str(p))

import verify_deviations_engine as E                          # noqa: E402  (helpers: filings, samples, trees)

FAILED = []


CHECKS = []


def check(label: str, ok: bool, detail: str = "") -> None:
    CHECKS.append((label, ok))
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}"
          + (f"\n          {detail}" if detail and not ok else ""))
    if not ok:
        FAILED.append(label)


def leaf_nodes(node, prefix="", out=None) -> dict:
    out = {} if out is None else out
    seen: dict = {}
    for c in node.children:
        i = seen.get(c.tag, 0)
        seen[c.tag] = i + 1
        p = f"{prefix}/{c.tag}[{i}]"
        if c.children:
            leaf_nodes(c, p, out)
        elif c.text not in (None, ""):
            out[p] = c
    return out


def gl_request(state="TX"):
    from console import catalog
    return catalog.build("GL", state, {})


def rate_cf(req, root, **kw):
    from cf_engine.rating import rate
    return rate(req, root=root, **kw)


def rate_gl(req, root, **kw):
    from gl_engine.rating import Kernel
    return Kernel().rate(req, root=root, **kw)


# --------------------------------------------------------------------- T4

def locality(r) -> tuple[int, int, int, list]:
    """(changed, reached, fields, changed-but-not-reached): reach is exact, along the rating graph's edges from the
    carrier's own sources -- its record LCMs, group LCMs and overridden table rows (G3)."""
    from gl_engine.interp.graph import normalise
    g = _graph(r)
    src = [n["id"] for n in g.nodes if n["kind"] == "company" or (n["kind"] == "table" and n.get("company"))]
    reach = g.reach(src) | set(src)
    reached = {p for p, gid in g.final.items() if gid in reach}
    ch = E.tree_diff(r.technical.tree, r.tree)
    bad = [p for p, _, _ in ch if normalise(p) not in reached]
    return len(ch), len(reached), len(leaf_nodes(r.tree)), bad


def _graph(r):
    """The carrier rating's graph: Property's on the result, GL's on the Rating."""
    return getattr(r, "graph", None) if hasattr(r, "ip") else getattr(r, "deps", None)


def t4(root: Path) -> None:
    print("\nT4  only what was deviated changes")
    cases = [("UFC Iowa sample (group LCMs)", lambda: rate_cf(E.ia_sample("UFC"), root, with_technical=True,
                                                             waterfall=False, graph=True)),
             ("ADD Iowa sample (group LCMs)", lambda: rate_cf(E.ia_sample("ADD"), root, with_technical=True,
                                                             waterfall=False, graph=True))]
    ia = [it for it in E.stored({"IA"}) if it[0].startswith("chunk24_rc4_S-IA")]
    if ia:
        req = copy.deepcopy(ia[0][3])
        req["header"].update(WritingCompany="UFC", PolicyType="New")
        cases.append(("UFC stored Iowa request, two classes in two groups",
                      lambda req=req: rate_cf(req, root, with_technical=True, waterfall=False, graph=True)))
    cdir = root / "UFG" / "T4T"
    cdir.mkdir(parents=True, exist_ok=True)
    (cdir / "company.json").write_text(json.dumps({"code": "T4T"}), encoding="utf-8")
    E.filing(root, "T4T", "IA-CF-T4TABLE", "CF", ["IA"], "2025-06-15",
             [{"target": "TABLE:BasicGroupIIRate.Rate", "scope": {}, "value": "1.1", "mode": "multiply"}])
    cases.append(("Iowa sample, a Property table override",
                  lambda: rate_cf(E.ia_sample("T4T", "2025-07-01"), root, with_technical=True,
                                  waterfall=False, graph=True)))
    req = gl_request()
    eff = req["body"]["SchemeKeys"]["EffectiveDateTime"][:10]
    cls = req["body"]["GeneralLiability"][0]["GeneralLiabilityLocation"][0]["GeneralLiabilityClassification"][0]["ClassCode"]
    t = _gl_table_read(req)
    rows = [{"target": "LCM:PremOps", "scope": {}, "value": "1.12", "mode": "replace"},
            {"target": "LCM:ProdsCompldOps", "scope": {"class": str(cls)}, "value": "1.3", "mode": "replace"}]
    if t:
        rows.append({"target": f"TABLE:{t[0]}.{t[1]}", "scope": {}, "value": "1.07", "mode": "multiply"})
    E.filing(root, "UFC", "TX-GL-T4", "GL", ["TX"], eff, rows)
    req["header"]["WritingCompany"] = "UFC"
    cases.append((f"UFC Texas GL: two coverage LCMs and {t[0] if t else 'no'} table override",
                  lambda req=req: rate_gl(req, root, with_technical=True, waterfall=False, graph=True)))
    for label, fn in cases:
        r = fn()
        if r.tree is None or r.technical is None or _graph(r) is None:
            check(f"T4 {label}", False, f"did not rate or has no graph: "
                                        f"{getattr(r, 'outcome', None) or getattr(r, 'stopped', None)}")
            continue
        ch, tn, n, bad = locality(r)
        check(f"T4 {label}: {ch} fields changed, all within the {tn} of {n} the carrier's inputs reach",
              ch > 0 and not bad and tn < n / 2, f"changed {ch}, reach {tn}/{n}, outside: {bad[:4]}")


def _gl_table_read(req):
    """An exact decimal table the GL request actually looks up (for an override it will reach)."""
    from deviations import iso
    from gl_engine.rating import Kernel
    r = Kernel().rate(copy.deepcopy(req))
    eff = req["body"]["SchemeKeys"]["EffectiveDateTime"][:10]
    seen = []
    for n in r.trace:
        if n.kind == "lookup" and n.data.get("category") == "Rate":
            seen.append((n.data["table"], n.data["column"]))
    for name, col in seen:
        try:
            t = iso.table("GL", "TX", eff, name)
        except Exception:
            continue
        if t.rows and not iso.is_banded(t) and t.definition.declared and t.definition.type_of(col) == "decimal" \
                and "LCM" not in name:
            return name, col
    return None


# --------------------------------------------------------------------- T6

def t6(root: Path) -> None:
    print("\nT6  a single override, to the digit")
    from deviations import iso
    plain = rate_cf(E.ia_sample(None), root)
    looked = []
    for n in plain.ip.trace:
        if n.kind == "lookup" and n.data.get("category") == "Rate" and n.data["table"] not in [x[0] for x in looked]:
            t = iso.table("CF", "IA", "2025-07-01", n.data["table"])
            if t.rows and not iso.is_banded(t) and t.definition.declared and \
                    t.definition.type_of(n.data["column"]) == "decimal":
                looked.append((n.data["table"], n.data["column"]))
    picks = looked[:4]
    for i, (name, col) in enumerate(picks):
        cdir = root / "UFG" / f"T6{i}"
        cdir.mkdir(parents=True, exist_ok=True)
        (cdir / "company.json").write_text(json.dumps({"code": f"T6{i}"}), encoding="utf-8")
        E.filing(root, f"T6{i}", f"IA-T6-{i}", "CF", ["IA"], "2025-06-01",
                 [{"target": f"TABLE:{name}.{col}", "scope": {}, "value": "1.1", "mode": "multiply"}])
        req = E.ia_sample(f"T6{i}")
        r = rate_cf(req, root, with_technical=True)
        tl = {(tuple(n.data["keys"]), n.data["column"]): n.data["value"] for n in r.technical.ip.trace
              if n.kind == "lookup" and n.data.get("table") == name}
        cl = {(tuple(n.data["keys"]), n.data["column"]): n.data["value"] for n in r.ip.trace
              if n.kind == "lookup" and n.data.get("table") == name}
        bad = [(k, tl[k], cl.get(k)) for k in tl if k[1] == col and
               Decimal(str(cl.get(k))) != Decimal(str(tl[k])) * Decimal("1.1")]
        check(f"T6 {name}.{col} x 1.1: each of its {len(tl)} lookups returns ISO's value x 1.1 exactly",
              tl and not bad, str(bad[:3]))
        wf = r.deviation["waterfall"]
        tot = sum(Decimal(s["effect"]) for s in wf)
        check(f"T6 {name}: the waterfall adds up exactly ({r.deviation['technicalPremium']} -> "
              f"{r.deviation['carrierPremium']})",
              tot == Decimal(r.premium) - Decimal(r.technical.premium), str(wf))


# --------------------------------------------------------------------- T7

def t7(root: Path) -> None:
    print("\nT7  deviations apply exactly where and when filed")
    import property_rating as pr
    req = pr.sample("OR", "2025-07-01")
    req["header"].update(WritingCompany="UFC", PolicyType="New")
    r = rate_cf(req, root, with_technical=True)
    check("T7a an Iowa filing does not touch Oregon", r.premium == r.technical.premium
          and not r.deviation["filings"], str(r.deviation["warnings"]))
    # coverage: PremOps-only GL filing leaves Products alone
    g = gl_request()
    eff = g["body"]["SchemeKeys"]["EffectiveDateTime"][:10]
    cdir = root / "UFG" / "T7GL"
    cdir.mkdir(parents=True, exist_ok=True)
    (cdir / "company.json").write_text(json.dumps({"code": "T7GL"}), encoding="utf-8")
    E.filing(root, "T7GL", "TX-T7", "GL", ["TX"], eff,
             [{"target": "LCM:PremOps", "scope": {}, "value": "1.3", "mode": "replace"}])
    g["header"]["WritingCompany"] = "T7GL"
    r = rate_gl(g, root, with_technical=True)
    moved = [p for p, _, _ in E.tree_diff(r.technical.tree, r.tree) if "ProdsCompldOps" in p.rsplit("/", 1)[-1]
             or "ProdsCompldOpsCoverage" in p]
    check("T7b a Prem/Ops LCM does not touch Products", not moved and r.premium != r.technical.premium,
          str(moved[:3]))
    # coverage group: a Group II-only LCM leaves Group I alone
    cdir = root / "UFG" / "T7CF"
    cdir.mkdir(parents=True, exist_ok=True)
    (cdir / "company.json").write_text(json.dumps({"code": "T7CF"}), encoding="utf-8")
    E.filing(root, "T7CF", "IA-T7", "CF", ["IA"], "2025-06-01",
             [{"target": "LCM:GroupII", "scope": {}, "value": "2", "mode": "replace"}])
    r = rate_cf(E.ia_sample("T7CF"), root, with_technical=True)
    moved = [p for p, _, _ in E.tree_diff(r.technical.tree, r.tree)]
    g1 = [p for p in moved if "GroupI" in p and "GroupII" not in p]
    check("T7c a Group II LCM moves Group II and leaves every Group I field alone",
          any("GroupII" in p for p in moved) and not g1, str(g1[:3]))
    # dates: the day before and on the new-business date; new vs renewal
    b = rate_cf(E.ia_sample("UFC", "2025-05-31"), root)
    o = rate_cf(E.ia_sample("UFC", "2025-06-01"), root)
    check("T7d new business: 5/31/2025 is not under the filing, 6/1/2025 is",
          not b.deviation["filings"] and o.deviation["filings"])
    req = E.ia_sample("UFC", "2025-09-30")
    req["header"]["PolicyType"] = "Renewal"
    rn = rate_cf(req, root)
    nb = rate_cf(E.ia_sample("UFC", "2025-09-30"), root)
    check("T7e 9/30/2025: new business is under the filing, a renewal is not (renewal date 10/1)",
          nb.deviation["filings"] and not rn.deviation["filings"])
    # superseded: v2 from 2025-08-01 replaces v1 from then on
    cdir = root / "UFG" / "T7SV"
    cdir.mkdir(parents=True, exist_ok=True)
    (cdir / "company.json").write_text(json.dumps({"code": "T7SV"}), encoding="utf-8")
    E.filing(root, "T7SV", "IA-SV", "CF", ["IA"], "2025-06-01",
             [{"target": "LCM:All", "scope": {}, "value": "1.2", "mode": "replace"}])
    E.filing(root, "T7SV", "IA-SV", "CF", ["IA"], "2025-08-01",
             [{"target": "LCM:All", "scope": {}, "value": "1.3", "mode": "replace"}], version=2)
    v_jul = rate_cf(E.ia_sample("T7SV", "2025-07-15"), root).deviation["filings"]
    v_aug = rate_cf(E.ia_sample("T7SV", "2025-08-15"), root).deviation["filings"]
    check("T7f superseded: v1 on 7/15/2025, v2 from 8/1/2025",
          v_jul and v_jul[0]["version"] == 1 and v_aug and v_aug[0]["version"] == 2, f"{v_jul} {v_aug}")
    # all states, opted out; and a jurisdiction added after the shortcut was taken
    cdir = root / "UFG" / "T7AS"
    cdir.mkdir(parents=True, exist_ok=True)
    (cdir / "company.json").write_text(json.dumps({"code": "T7AS"}), encoding="utf-8")
    from deviations.files import load_filing, log_action, write_json
    from deviations.compile import compile_filing
    from deviations.validate import validate
    p = cdir / "authored" / "ALL-EQ.v1.json"
    write_json(p, json.loads(json.dumps({
        "filing": "ALL-EQ", "company": "T7AS", "line": "CF", "juris": ["ALL"], "juris_asof": "2023-01-01",
        "opt_out": ["IA"], "version": 1, "status": "approved", "new_eff": "2025-06-01", "renewal_eff": "2025-06-01",
        "rows": [{"target": "LCM:Earthquake", "scope": {}, "value": "1.2", "mode": "replace"}]}),
        parse_float=Decimal))
    f = load_filing(p)
    log_action(f.company_dir, f.filing, 1, "propose", "Dan Roman")
    log_action(f.company_dir, f.filing, 1, "sign-off", "Dan Roman")
    rep = validate(f)
    check("T7g the all-states filing validates", rep.ok, "; ".join(rep.errors[:3]))
    if rep.ok:
        compile_filing(rep)
        check("T7h it covers Oregon and leaves out Iowa (opted out) and Illinois (no Property package on 1/1/2023)",
              "OR" in rep.juris and "IA" not in rep.juris and "IL" not in rep.juris, str(rep.juris))
        ia = rate_cf(E.ia_sample("T7AS"), root).deviation["filings"]
        orr = pr.sample("OR", "2025-07-01")
        orr["header"].update(WritingCompany="T7AS", PolicyType="New")
        o = rate_cf(orr, root).deviation["filings"]
        il = pr.sample("IL", "2025-07-01")
        il["header"].update(WritingCompany="T7AS", PolicyType="New")
        i = rate_cf(il, root).deviation["filings"]
        check("T7i rated: Oregon is under it; Iowa and Illinois are not", o and not ia and not i,
              f"OR {o}, IA {ia}, IL {i}")
    # D22: a class ISO adds after the filing compiled takes the "all other classes" rows. Simulated by compiling
    # one copy against an edition without the sample's classes; it must rate exactly as the copy that had them.
    from deviations import iso as dv_iso
    sample_classes = set()
    stack = [E.ia_sample()["body"]]
    while stack:
        o = stack.pop()
        if isinstance(o, dict):
            sample_classes.update(str(v) for k, v in o.items() if k == "ClassCode")
            stack.extend(o.values())
        elif isinstance(o, list):
            stack.extend(o)
    rows = [{"target": "LCM:All", "scope": {}, "value": "1.4", "mode": "replace"},
            {"target": "LCM:GroupII", "scope": {}, "value": "1.1", "mode": "multiply"}]
    for code in ("T7UK", "T7UN"):
        cdir = root / "UFG" / code
        cdir.mkdir(parents=True, exist_ok=True)
        (cdir / "company.json").write_text(json.dumps({"code": code}), encoding="utf-8")
    E.filing(root, "T7UK", "IA-UK", "CF", ["IA"], "2025-06-01", rows)
    real = dv_iso.class_codes
    dv_iso.class_codes = lambda *a: tuple(c for c in real(*a) if c not in sample_classes)
    try:
        E.filing(root, "T7UN", "IA-UN", "CF", ["IA"], "2025-06-01", rows)
    finally:
        dv_iso.class_codes = real
    known = rate_cf(E.ia_sample("T7UK"), root, with_technical=True)
    added = rate_cf(E.ia_sample("T7UN"), root)
    d22 = [w for w in added.deviation["warnings"] if "D22" in w]
    check(f"T7j a class added after the filing (classes {sorted(sample_classes)}) takes 'all other': "
          f"{added.premium} = {known.premium}, technical {known.technical.premium}",
          sample_classes and added.premium == known.premium != known.technical.premium and d22
          and not [w for w in known.deviation["warnings"] if "D22" in w], str(added.deviation["warnings"][:3]))


# --------------------------------------------------------------------- T9

def t9(root: Path) -> None:
    print("\nT9  one filing over two ISO editions")
    from deviations import engine as dv, iso
    old, new = iso.table("CF", "IA", "2025-07-01", "BasicGroupIIRate"), iso.table("CF", "IA", "2026-09-17",
                                                                                   "BasicGroupIIRate")
    ks = iso.table_keys(old)
    def val(t, key):
        idx = [t.col(k) for k in ks]
        return next(r[t.col("Rate")] for r in t.rows if tuple(str(r[i]) for i in idx) == key)
    k_rep, k_mul = ("Entire State", "AA", "Bldg"), ("Entire State", "AA", "PersProp")
    cdir = root / "UFG" / "T9"
    cdir.mkdir(parents=True, exist_ok=True)
    (cdir / "company.json").write_text(json.dumps({"code": "T9"}), encoding="utf-8")
    E.filing(root, "T9", "IA-T9", "CF", ["IA"], "2025-06-01", [
        {"target": "TABLE:BasicGroupIIRate.Rate", "scope": dict(zip(ks, k_rep)), "value": "0.2", "mode": "replace"},
        {"target": "TABLE:BasicGroupIIRate.Rate", "scope": dict(zip(ks, k_mul)), "value": "1.1", "mode": "multiply"}])
    check("T9a ISO's two editions price these keys differently (the test needs a revision)",
          val(old, k_rep) != val(new, k_rep) and val(old, k_mul) != val(new, k_mul),
          f"{val(old, k_rep)}/{val(new, k_rep)} {val(old, k_mul)}/{val(new, k_mul)}")
    got = {}
    for label, date in (("2025", "2025-07-01"), ("2026", "2026-09-17")):
        plan = dv.plan_for("CF", "T9", "IA", date, "New", root=root)
        cb = dv.CompanyBook(iso.book("CF", "IA", date), plan)
        got[label] = (val(cb.table("BasicGroupIIRate"), k_rep), val(cb.table("BasicGroupIIRate"), k_mul))
    check("T9b the replace row keeps its value on both editions",
          Decimal(str(got["2025"][0])) == Decimal(str(got["2026"][0])) == Decimal("0.2"), str(got))
    check("T9c the multiply row follows ISO: 1.1 x each edition's own value",
          Decimal(str(got["2025"][1])) == Decimal(str(val(old, k_mul))) * Decimal("1.1")
          and Decimal(str(got["2026"][1])) == Decimal(str(val(new, k_mul))) * Decimal("1.1"), str(got))
    r = rate_cf(E.ia_sample("T9", "2026-09-17"), root)
    check("T9d rated on the newer edition, the 'ISO revised' flag is raised (D9)",
          any("ISO revised" in w for w in r.deviation["warnings"]), str(r.deviation["warnings"]))


# --------------------------------------------------------------------- T5

def t5() -> None:
    print("\nT5  carrier LCMs, proved against technical (D21: ISO only rates technical)")
    import deviations_p3 as L
    from deviations import engine as dv
    L.WITH_T5_LIVE = True
    cs, t3 = L.cases()
    L.WITH_T5_LIVE = False
    L.build_carriers(t3)
    for c in [c for c in cs if c["test"] == "T5"]:
        p = L.prepare(c)
        r, line = p["result"], c["line"]
        if not (r.tree is not None and r.technical is not None and r.technical.tree is not None):
            check(f"T5 {c['id']} rates", False, str(getattr(r, "outcome", None) or getattr(r, "stopped", "")))
            continue
        eff = L._eff(p["base_request"])
        plan = dv.plan_for(line, p["company"], c["state"], eff, "New", root=L.CARRIERS)
        book = dv.book_for(plan)
        if line == "CF":
            iso_lcm = dv.iso_state_lcm(book, "CF")
            notes = [n.data for n in r.ip.trace if n.kind == "company-group-lcm"]
            bad = [n for n in notes if Decimal(n["value"]) != dv._final(
                plan.group_lcm.get((n["group"], n["basis"], n["class_code"]))
                or plan.unlisted_lcm[(n["group"], n["basis"])], iso_lcm)]
            groups = sorted({n["group"] for n in notes})
            check(f"T5 {c['id']}: {len(notes)} group-rate products read exactly the filed LCM "
                  f"({', '.join(groups)})", notes and not bad, str(bad[:2]))
        else:
            lcms = [(n.detail) for n in r.trace if n.kind == "company-record-lcm"]
            cov = {}
            stack = [r.tree]
            while stack:
                n = stack.pop()
                stack.extend(n.children)
                got = dv.GL_LCM_RECORDS.get(n.tag)
                if got and n.first("LCM") is not None:
                    cls = dv._up(n, "ClassCode")
                    e = plan.lcm.get((got[0], cls))
                    if e is not None:
                        cov[(got[0], cls)] = (Decimal(n.first("LCM").text), dv._final(e, Decimal(1)))
            bad = {k: v for k, v in cov.items() if v[0] != v[1]}
            check(f"T5 {c['id']}: every GL coverage record carries exactly its filed LCM ({len(cov)} records)",
                  cov and not bad and lcms, str(bad))
        if line == "CF" and c.get("base") in ("sample-0951", "sample-0511"):
            st_c, st_t = E._structure(r.tree), E._structure(r.technical.tree)
            want = {"GroupI": "BasicGroupIRate", "GroupII": "BasicGroupIIRate", "Special": "AdjustedSpecialRate"}
            cls = st_c.first("ClassCode").text
            bad = []
            for g, f in want.items():
                L_ = dv._final(plan.group_lcm[(g, "Class", cls)], Decimal(1))
                tv, cv = Decimal(st_t.first(f).text), Decimal(st_c.first(f).text)
                if abs(cv - tv * L_) > Decimal("0.0005") * (L_ + 2):
                    bad.append(f"{f}: {tv} x {L_} vs {cv}")
            check(f"T5 {c['id']}: each group's rate scales by its own LCM, within ISO's 3-place rounding",
                  not bad, "; ".join(bad))


# --------------------------------------------------------------------- live

def live() -> None:
    print("\nL  T3 and T8 re-judged from ISO's stored answers (no calls)")
    import deviations_p3 as L
    cs, t3 = L.cases()
    L.build_carriers(t3)
    by = {}
    for c in cs:
        try:
            v = L.judge(L.prepare(c))
        except Exception as exc:                              # noqa: BLE001
            v = {"id": c["id"], "test": c["test"], "verdict": "error", "detail": f"{type(exc).__name__}: {exc}"}
        by.setdefault(c["test"], []).append(v)
    for test, vs in sorted(by.items()):
        known = [v for v in vs if v["verdict"] == "known"]
        bad = [v for v in vs if v["verdict"] not in ("pass", "known")]
        check(f"{test} {len(vs) - len(bad) - len(known)} of {len(vs)} cases pass against ISO"
              + (f"; {len(known)} known ISO behaviour ({', '.join(v['id'] for v in known)}: O6)" if known else ""),
              not bad, "; ".join(f"{v['id']} {v['verdict']}: {str(v.get('detail', ''))[:150]}" for v in bad[:4]))
    (L.OUT / "verdicts.json").parent.mkdir(parents=True, exist_ok=True)
    (L.OUT / "verdicts.json").write_text(json.dumps([v for vs in by.values() for v in vs], indent=1, default=str),
                                         encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-live", action="store_true")
    a = ap.parse_args()
    root = E.tmp_root()
    for step in (t4, t6, t7, t9):
        step(root)
    shutil.rmtree(root, ignore_errors=True)
    t5()
    if not a.no_live:
        live()
    from deviations import suite_log
    suite_log.record("proof", CHECKS)
    print(f"\n{'FAILED: ' + ', '.join(FAILED) if FAILED else 'all passed'}")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
