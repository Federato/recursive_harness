"""Impact preview (B-18): what a company's filings do to premiums, projected by risk type.

There is no book to re-rate, so the preview builds one: for each risk type a few ISO classes, each at three sizes
(and, for Property, four constructions), in every state the company has a compiled filing for that line. Each risk
is rated twice on our engine -- technical (pure ISO) and carrier -- and the change is summed by risk type, coverage
group, state, size and construction. No ISO call is made: ISO only ever sees technical (D21), and technical is
already proved against ISO by the suites.

It answers "what does this filing do to a typical apartment risk", not "what does it do to the carrier's book":
the mix is ours (the user's choice, 2026-10-15), every risk weighs the same, and the sizes are round numbers.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

from .config import CARRIERS_ROOT

ROOT = Path(__file__).resolve().parent.parent
for _p in (ROOT, ROOT / "scripts", ROOT / "console"):
    if str(_p) not in sys.path:
        sys.path.append(str(_p))

#: Property risk types, each a few class-rated CSP classes (descriptions from ISO's DomainClassDesc). Every code is
#: class-rated in IA and AL; a code a state doesn't rate is skipped there and counted.
CP_RISK_TYPES = (
    ("Apartments", ("0311", "0312", "0313")),        # without mercantile: up to 10, 11-30, over 30 units
    ("Offices", ("0701", "0702")),                   # governmental, non-governmental
    ("Mercantile", ("0532", "0563", "0567")),        # grocery and food; hardware; mercantile NOC
    ("Restaurants and bars", ("0545", "0541")),      # limited cooking; bars and taverns
    ("Manufacturing", ("2200", "2350", "4809")),     # bakery plants; beverage bottlers; printers' supplies
    ("Warehouses", ("1212", "1213", "1220")),        # public NOC; mini-warehouses; household goods
)
#: (label, building limit, personal property limit)
CP_SIZES = (("Small", 500000, 100000), ("Medium", 2000000, 500000), ("Large", 10000000, 2000000))
CP_CONSTRUCTIONS = (
    ("Frame", "Frame"),
    ("Joisted masonry", "Joisted Masonry - Other Than Reinforced"),
    ("Masonry non-combustible", "Masonry Non-Combustible - Other Than Reinforced - Other Than Light Steel"),
    ("Fire resistive", "Fire Resistive - Other Than Reinforced Masonry - Other Than Light Steel"),
)
#: GL sizes: a multiple of the class's own basis exposure (`catalog.basis_exposure`).
GL_SIZES = (("Small", Decimal("0.2")), ("Medium", Decimal(1)), ("Large", Decimal(5)))


def cp_group(tag: str) -> str:
    for key, label in (("BasicGroupII", "Group II"), ("BasicGroupI", "Group I"), ("Special", "Special"),
                       ("Broad", "Broad"), ("Earthquake", "Earthquake")):
        if key in tag:
            return label
    return "Other"


def gl_group(tag: str) -> str:
    if "ProdsCompldOps" in tag:
        return "Products/Completed Ops"
    if "PremOps" in tag:
        return "Premises/Operations"
    return "Other"


def coverage_premiums(tree, group) -> dict:
    """{coverage group: premium} over every `...Coverage` record that carries a premium."""
    out: dict = defaultdict(Decimal)
    stack = [tree]
    while stack:
        n = stack.pop()
        for c in n.children:
            if c.tag.endswith("Coverage"):
                p = c.first("Premium")
                if p is not None and p.text not in (None, ""):
                    out[group(c.tag)] += Decimal(p.text)
            stack.append(c)
    return {k: v for k, v in out.items() if v}


@dataclass
class Risk:
    state: str
    risk_type: str
    class_code: str
    size: str
    construction: str = ""
    status: str = "rated"                   # rated | refused | no filing
    technical: Decimal = Decimal(0)
    carrier: Decimal = Decimal(0)
    by_group: dict = field(default_factory=dict)      # group -> [technical, carrier]
    driver: str = ""
    detail: str = ""

    @property
    def change(self) -> Decimal | None:
        return (self.carrier / self.technical - 1) if self.technical else None


def company_states(company: str, line: str, root: Path = CARRIERS_ROOT) -> list[str]:
    from .engine import find_company
    base = find_company(company, root) / "compiled" / line
    return sorted(p.name for p in base.iterdir() if p.is_dir()) if base.is_dir() else []


def _filing_date(company: str, line: str, state: str, root: Path) -> str:
    """The latest new-business effective date among the state's compiled filings: the preview rates under it."""
    from .engine import find_company
    from .files import read_json
    ms = sorted((find_company(company, root) / "compiled" / line / state).glob("*/manifest.json"))
    return max(str(read_json(m)["new_eff"]) for m in ms)


def _driver(plan, line: str, cls: str) -> str:
    """Which part of the filing reaches this class: its class group (or 'all other') and the LCM per coverage."""
    if not plan.manifest:
        return "no filing in force"
    groups = plan.manifest.get("class_groups") or {}
    grp = next((g for g, codes in groups.items() if cls in codes), None)
    label = f"class group {grp}" if grp else "all other classes"
    if line == "CF":
        lcms = {k[0]: v[0] for k, v in plan.group_lcm.items() if k[1] == "Class" and k[2] == cls}
        if not lcms:
            lcms = {k[0]: v[0] for k, v in plan.unlisted_lcm.items() if k[1] == "Class"}
    else:
        lcms = {k[0]: v[0] for k, v in plan.lcm.items() if k[1] == cls}
    order = ("GroupI", "GroupII", "Broad", "Special", "Earthquake", "PremOps", "Products")
    parts = [f"{t} {lcms[t]}" for t in order if t in lcms] + [f"{t} {v}" for t, v in lcms.items() if t not in order]
    return f"{label}: {', '.join(parts)}" if parts else label


def _risks(line: str, state: str):
    if line == "CF":
        for rt, codes in CP_RISK_TYPES:
            for cls in codes:
                for size, bldg, bpp in CP_SIZES:
                    for cname, cval in CP_CONSTRUCTIONS:
                        yield Risk(state, rt, cls, size, cname), {
                            "class_code": cls, "bldg_limit": str(bldg), "bpp_limit": str(bpp),
                            "construction": cval, "cause_of_loss": "Special"}
    else:
        from console import catalog
        types: dict = defaultdict(list)
        for code, label in catalog.GL_CLASS_MIX:
            types[label].append(code)
        for rt, codes in types.items():
            for cls in codes:
                for size, mult in GL_SIZES:
                    yield Risk(state, rt, cls, size), {"class_code": cls, "_size": mult}


def _rate_one(line: str, company: str, state: str, date: str, risk: Risk, cfg: dict, root: Path, plan) -> Risk:
    from console import catalog
    risk.driver = _driver(plan, line, risk.class_code)
    try:
        if line == "CF":
            from cf_engine.rating import rate
            req = catalog.build("CP", state, {**cfg, "effective_date": date})
            req["header"].update(WritingCompany=company, PolicyType="New")
            r = rate(req, root=root, with_technical=True)
            group = cp_group
        else:
            from gl_engine.rating import Kernel
            import variants as V
            d = V.Declared(state, date.replace("-", ""))
            basis = d.basis_for(cfg["class_code"], "PremOps")
            exposure = int(Decimal(catalog.basis_exposure(basis)) * cfg["_size"]) or 1
            req = catalog.build("GL", state, {"class_code": cfg["class_code"], "exposure": exposure,
                                              "effective_date": date.replace("-", "")})
            req["header"].update(WritingCompany=company, PolicyType="New")
            r = Kernel().rate(req, root=root, with_technical=True)
            group = gl_group
    except Exception as exc:                                   # a refusal is a finding, not a crash
        risk.status, risk.detail = "refused", str(exc)[:200]
        return risk
    tech = getattr(r, "technical", None)
    if not getattr(r, "complete", True) or tech is None or r.tree is None or tech.tree is None:
        risk.status = "refused"
        risk.detail = str(getattr(r, "outcome", None) or getattr(r, "stopped", ""))[:200]
        return risk
    risk.technical, risk.carrier = Decimal(str(tech.premium)), Decimal(str(r.premium))
    t, c = coverage_premiums(tech.tree, group), coverage_premiums(r.tree, group)
    risk.by_group = {g: [t.get(g, Decimal(0)), c.get(g, Decimal(0))] for g in sorted(set(t) | set(c))}
    return risk


def run(company: str, line: str = "CF", states: list[str] | None = None, root: Path = CARRIERS_ROOT,
        limit: int | None = None, progress=None, dates: dict | None = None) -> dict:
    """Rate the projected book for one company and line; the result is plain JSON-ready data. `dates` fixes the
    effective date per state (a draft's comparison with the filing in force rates both on the draft's date)."""
    from .engine import plan_for
    states = states or company_states(company, line, root)
    risks: list[Risk] = []
    meta_states = {}
    for st in states:
        date = (dates or {}).get(st) or _filing_date(company, line, st, root)
        plan = plan_for(line, company, st, date, "New", root=root)
        meta_states[st] = {"date": date, "filing": plan.ref}
        for i, (risk, cfg) in enumerate(_risks(line, st)):
            if limit is not None and i >= limit:
                break
            risks.append(_rate_one(line, company, st, date, risk, cfg, root, plan))
            if progress:
                progress(risks[-1])
    return summarize(company, line, meta_states, risks)


def run_draft(authored: Path, root: Path = CARRIERS_ROOT, progress=None) -> dict:
    """B-20: a draft's impact before it is built. The carrier's files are copied to a scratch store, where the draft
    alone is marked approved, signed off and compiled; the projected book is rated there. The real store is not
    touched, and nothing is approved in it."""
    import shutil
    import tempfile
    from .compile import compile_filing
    from .files import load_filing, log_action, read_json, write_json
    from .validate import validate
    a = Path(authored).resolve()
    f = load_filing(a)
    tmp = Path(tempfile.mkdtemp(prefix="impact_draft_"))
    try:
        dst = tmp / f.carrier_dir.name
        shutil.copytree(f.carrier_dir, dst, ignore=shutil.ignore_patterns("sources"))
        p = dst / a.relative_to(f.carrier_dir)
        d = read_json(p)
        d["status"] = "approved"
        write_json(p, d)
        g = load_filing(p)
        rep = validate(g)
        if not rep.ok:
            raise ValueError(f"{g.ref} does not validate: " + "; ".join(rep.errors))
        compile_filing(rep, require_approval=False)
        for action in ("propose", "sign-off"):
            log_action(g.company_dir, g.filing, g.version, action, "impact preview (draft, scratch store)")
        out = run(g.company, g.line, list(rep.juris), tmp, progress=progress)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    out["draft"] = f.ref
    # the same book on the same dates under what is in force today (a filing, or technical where there is none)
    cur = run(f.company, f.line, list(out["states"]), f.carrier_dir.parent, progress=progress,
              dates={st: v["date"] for st, v in out["states"].items()})
    out["current"] = {"states": cur["states"], "all": cur["all"]}
    out["vs_current"] = versus(cur, out)
    return out


def versus(cur: dict, new: dict) -> dict:
    """The change from one rating of the projected book to another, risk for risk: overall, by risk type, by coverage
    group. Both must be the same book (same states, classes, sizes, constructions)."""
    def key(r):
        return (r["state"], r["risk_type"], r["class"], r["size"], r["construction"])
    a = {key(r): r for r in cur["risks"] if r["status"] == "rated"}
    pairs = [(a[key(r)], r) for r in new["risks"] if r["status"] == "rated" and key(r) in a]

    def ch(x, y):
        return _pct(y / x - 1) if x else None
    tot = [Decimal(0), Decimal(0)]
    by_type: dict = defaultdict(lambda: [Decimal(0), Decimal(0)])
    by_cov: dict = defaultdict(lambda: [Decimal(0), Decimal(0)])
    for o, n in pairs:
        tot[0] += Decimal(o["carrier"])
        tot[1] += Decimal(n["carrier"])
        by_type[n["risk_type"]][0] += Decimal(o["carrier"])
        by_type[n["risk_type"]][1] += Decimal(n["carrier"])
        for g, v in (n.get("groups") or {}).items():
            by_cov[g][1] += Decimal(v[1])
        for g, v in (o.get("groups") or {}).items():
            by_cov[g][0] += Decimal(v[1])
    return {"risks": len(pairs), "change": ch(*tot), "by_risk_type": {k: ch(*v) for k, v in by_type.items()},
            "by_coverage": {k: ch(*v) for k, v in sorted(by_cov.items())},
            "filings": {st: v.get("filing") for st, v in cur["states"].items()}}


def _agg(risks: list[Risk]) -> dict:
    rated = [r for r in risks if r.status == "rated"]
    t = sum((r.technical for r in rated), Decimal(0))
    c = sum((r.carrier for r in rated), Decimal(0))
    ch = [r.change for r in rated if r.change is not None]
    return {"risks": len(risks), "rated": len(rated), "technical": str(t), "carrier": str(c),
            "change": _pct(c / t - 1) if t else None,
            "min": _pct(min(ch)) if ch else None, "max": _pct(max(ch)) if ch else None}


def _pct(x: Decimal) -> str:
    return f"{(x * 100).quantize(Decimal('0.1'))}"


def summarize(company: str, line: str, states: dict, risks: list[Risk]) -> dict:
    def by(key):
        groups: dict = defaultdict(list)
        for r in risks:
            groups[key(r)].append(r)
        return {k: _agg(v) for k, v in groups.items()}

    cov: dict = defaultdict(lambda: defaultdict(lambda: [Decimal(0), Decimal(0)]))
    for r in risks:
        if r.status != "rated":
            continue
        for g, (t, c) in r.by_group.items():
            for k in (r.risk_type, "All"):
                cov[k][g][0] += t
                cov[k][g][1] += c
    coverage = {k: {g: {"technical": str(t), "carrier": str(c), "change": _pct(c / t - 1) if t else None}
                    for g, (t, c) in sorted(v.items())} for k, v in cov.items()}
    drivers: dict = defaultdict(set)
    for r in risks:
        drivers[(r.state, r.risk_type, r.class_code)].add(r.driver)
    return {
        "company": company, "line": line, "states": states, "iso_calls": 0,
        "all": _agg(risks),
        "by_risk_type": by(lambda r: r.risk_type),
        "by_state": by(lambda r: r.state),
        "by_state_risk_type": {f"{k[0]} | {k[1]}": v for k, v in by(lambda r: (r.state, r.risk_type)).items()},
        "by_size": by(lambda r: r.size),
        "by_construction": by(lambda r: r.construction) if line == "CF" else {},
        "by_coverage": coverage,
        "drivers": [{"state": s, "risk_type": t, "class": c, "driver": "; ".join(sorted(d))}
                    for (s, t, c), d in sorted(drivers.items())],
        "refused": [{"state": r.state, "class": r.class_code, "size": r.size, "construction": r.construction,
                     "detail": r.detail} for r in risks if r.status != "rated"],
        "risks": [{"state": r.state, "risk_type": r.risk_type, "class": r.class_code, "size": r.size,
                   "construction": r.construction, "status": r.status, "technical": str(r.technical),
                   "carrier": str(r.carrier), "change": _pct(r.change) if r.change is not None else None,
                   "groups": {g: [str(t), str(c)] for g, (t, c) in r.by_group.items()}}
                  for r in risks],
    }


def markdown(rep: dict) -> str:
    """The report as Markdown tables (the console tab, B-20, will read the JSON)."""
    def table(title, rows, first):
        out = [f"\n### {title}\n", f"| {first} | Risks | Technical | Carrier | Change | Range |", "|---|---|---|---|---|---|"]
        for k, a in rows.items():
            rng = f"{a['min']}% to {a['max']}%" if a["min"] is not None else "—"
            out.append(f"| {k} | {a['rated']}/{a['risks']} | {int(Decimal(a['technical'])):,} | "
                       f"{int(Decimal(a['carrier'])):,} | {a['change']}% | {rng} |")
        return out

    st = ", ".join(f"{s} ({v['filing']}, {v['date']})" for s, v in rep["states"].items())
    out = [f"# Impact preview: {rep['company']} {rep['line']}" + (f" -- DRAFT {rep['draft']}, not approved" if rep.get("draft") else ""), "",
           f"Filings: {st}. Projected book, every risk weighted the same; technical vs carrier on our engine, "
           f"{rep['iso_calls']} ISO calls.",
           f"\n**Overall: {rep['all']['change']}%** ({rep['all']['rated']} of {rep['all']['risks']} risks rated; "
           f"per-risk range {rep['all']['min']}% to {rep['all']['max']}%)."]
    out += table("By risk type", rep["by_risk_type"], "Risk type")
    groups = sorted({g for v in rep["by_coverage"].values() for g in v})
    out += ["\n### By coverage group (change %)\n", "| Risk type | " + " | ".join(groups) + " |",
            "|---|" + "---|" * len(groups)]
    for k in [*rep["by_risk_type"], "All"]:
        v = rep["by_coverage"].get(k, {})
        out.append(f"| {k} | " + " | ".join(f"{v[g]['change']}%" if g in v else "—" for g in groups) + " |")
    out += table("By state", rep["by_state"], "State")
    out += table("By size", rep["by_size"], "Size")
    if rep["by_construction"]:
        out += table("By construction", rep["by_construction"], "Construction")
    out += ["\n### What drives each class\n", "| State | Risk type | Class | Filing reaches it as |", "|---|---|---|---|"]
    out += [f"| {d['state']} | {d['risk_type']} | {d['class']} | {d['driver']} |" for d in rep["drivers"]]
    vc = rep.get("vs_current")
    if vc:
        cur = ", ".join(f"{s} {f or 'technical only'}" for s, f in vc["filings"].items())
        out += [f"\n### Draft vs what is in force ({cur})\n", f"Overall **{vc['change']}%** over {vc['risks']} risks.\n",
                "| Risk type | Change |", "|---|---|"] + [f"| {k} | {v}% |" for k, v in vc["by_risk_type"].items()]
    if rep["refused"]:
        out += ["\n### Not rated\n", "| State | Class | Size | Construction | Why |", "|---|---|---|---|---|"]
        out += [f"| {r['state']} | {r['class']} | {r['size']} | {r['construction']} | {r['detail'][:120]} |"
                for r in rep["refused"]]
    return "\n".join(out) + "\n"


def write(rep: dict, out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    import time
    rep.setdefault("generated", time.strftime("%Y-%m-%dT%H:%M:%S"))
    stem = f"{rep['company']}-{rep['line']}-{'-'.join(rep['states'])}" + (f"-draft-{rep['draft']}" if rep.get("draft") else "")
    j, m = out_dir / f"{stem}.json", out_dir / f"{stem}.md"
    j.write_text(json.dumps(rep, indent=1), encoding="utf-8")
    m.write_text(markdown(rep), encoding="utf-8")
    return j, m
