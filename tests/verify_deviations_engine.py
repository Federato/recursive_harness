"""P2: the engine rates writing companies without moving ISO (DEVIATIONS-PLAN.md, P2 gate).

Run: python tests/verify_deviations_engine.py [--jobs N] [--per-state N]    (offline; no ISO calls)

  A  T1 Property   no company: `cf_engine.rating.rate` is the console's rating, field for field, on a
                   sample of every state's stored ISO requests; a header carrying only our PolicyType
                   rates exactly as no header
  B  T1 GL         the same header check through `Kernel.rate` (GL's own suites cover the rest)
  C  T2 Property   a company whose every row is neutral (LCM:All x 1, every exact decimal ISO table x 1)
                   rates field-for-field equal to technical
  D  T2 GL         the same, on GL
  E  P0 filing     UFG Iowa rates: each group's rate scales by exactly its filed LCM, for both companies,
                   on the default class group and on class group A
  F  waterfall     LCM and a table override, stepped; the steps add up to carrier - technical
  G  pin           an edition pin rates on the pinned package, technical too (M3), and is a waterfall step
  H  refusals      unknown company, impossible pin, an override key the edition lacks, a bad policy
                   type -- refused with the reason; a withdrawn filing is not in force (said so)
  I  M6 / D13      our header fields and submitted LCMs never reach ISO's request; a submitted LCM is named
  J  GL company    PremOps and Products LCMs, a class-scoped multiply, a GL table override

The full stored Property population (2,082 requests) is `scripts/cf/206_snapshot_regression.py --check`: run it
too after any engine change; this suite samples it. T2 covers exact-keyed tables only: banded tables cannot be
overridden in v1, so no company row can reach them.
"""
from __future__ import annotations

import argparse
import copy
import glob
import json
import os
import shutil
import sys
import tempfile
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for p in (ROOT, ROOT / "scripts", ROOT / "scripts" / "cf"):
    sys.path.insert(0, str(p))

FIX = ROOT / "tests" / "fixtures" / "deviations"
FAILED = []


CHECKS = []


def check(label: str, ok: bool, detail: str = "") -> None:
    CHECKS.append((label, ok))
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}"
          + (f"\n          {detail}" if detail and not ok else ""))
    if not ok:
        FAILED.append(label)


# ---------------------------------------------------------------- helpers

def leaves(node, prefix="", out=None) -> dict:
    out = {} if out is None else out
    seen: dict = {}
    for c in node.children:
        i = seen.get(c.tag, 0)
        seen[c.tag] = i + 1
        p = f"{prefix}/{c.tag}[{i}]"
        if c.children:
            leaves(c, p, out)
        elif c.text not in (None, ""):
            out[p] = c.text
    return out


def _eq(a, b) -> bool:
    try:
        return Decimal(str(a)) == Decimal(str(b))
    except Exception:
        return str(a) == str(b)


def tree_diff(a, b, minted=("Guid",)) -> list:
    la, lb = leaves(a), leaves(b)
    out = []
    for p in sorted(set(la) | set(lb)):
        name = p.rsplit("/", 1)[-1].split("[")[0]
        if name.endswith(minted):
            continue
        if not (p in la and p in lb and _eq(la[p], lb[p])):
            out.append((p, la.get(p), lb.get(p)))
    return out


def stored(only_states=None) -> list:
    out = []
    for f in sorted(glob.glob(str(ROOT / "results" / "cf-raas" / "*_request.json"))):
        d = json.loads(Path(f).read_text(encoding="utf-8"))
        body = d.get("body", d)
        sk = body.get("SchemeKeys") or {}
        if not str(sk.get("ProductName", "")).startswith("Commercial Property ") or "CommercialProperty" not in body:
            continue
        st = sk["ProductName"].split()[-1]
        if only_states and st not in only_states:
            continue
        req = d if "body" in d else {"header": {}, "body": d}
        out.append((Path(f).name, st, str(sk.get("EffectiveDateTime", ""))[:10], req))
    return out


def per_state(items, n: int) -> list:
    by = defaultdict(list)
    for it in items:
        by[it[1]].append(it)
    out = []
    for st in sorted(by):
        xs = by[st]
        step = max(1, len(xs) // n)
        out += xs[::step][:n]
    return out


def tmp_root() -> Path:
    d = Path(tempfile.mkdtemp(prefix="deviations_engine_"))
    shutil.copytree(FIX / "UFG", d / "UFG")
    from deviations.files import load_filing, log_action
    for co in ("UFC", "ADD"):
        p = d / "UFG" / co / "authored" / "IA-CF-UNFG-134289779.v1.json"
        f = load_filing(p)
        log_action(f.company_dir, f.filing, f.version, "propose", "Dan Roman")
        log_action(f.company_dir, f.filing, f.version, "sign-off", "Dan Roman")
        build(p)
    return d


def build(path: Path):
    from deviations.compile import compile_filing
    from deviations.files import load_filing
    from deviations.validate import validate
    rep = validate(load_filing(path))
    if not rep.ok:
        raise AssertionError("\n".join(rep.errors[:10]))
    return compile_filing(rep)


def filing(root: Path, company: str, name: str, line: str, juris: list, eff: str, rows: list,
           version: int = 1) -> Path:
    from deviations.files import load_filing, log_action, write_json
    cdir = root / "UFG" / company
    p = cdir / "authored" / f"{name}.v{version}.json"
    write_json(p, json.loads(json.dumps({
        "filing": name, "company": company, "line": line, "juris": juris, "version": version,
        "status": "approved", "new_eff": eff, "renewal_eff": eff, "rows": rows}), parse_float=Decimal))
    f = load_filing(p)
    log_action(f.company_dir, f.filing, f.version, "propose", "Dan Roman")
    log_action(f.company_dir, f.filing, f.version, "sign-off", "Dan Roman")
    build(p)
    return p


def identity_rows(line: str, juris: str, date: str) -> list:
    """LCM:All x 1 and x 1 on every exact, populated, decimal value column ISO declares."""
    from deviations import iso
    b = iso.book(line, juris, date)
    rows = [{"target": "LCM:All", "scope": {}, "value": "1", "mode": "multiply"}]
    names = set(b.state.names("Rate")) | (set(b.parent.names("Rate")) if b.parent else set())
    for n in sorted(names):
        try:
            t = b.table(n)
        except Exception:
            continue
        if not t.rows or iso.is_banded(t) or not t.definition.declared:
            continue
        for c in t.definition.value_cols:
            if c.type == "decimal":
                rows.append({"target": f"TABLE:{n}.{c.name}", "scope": {}, "value": "1",
                             "mode": "multiply"})
    return rows


def ia_sample(company: str | None = None, date: str = "2025-07-01") -> dict:
    import property_rating as pr
    req = pr.sample("IA", date)
    if company:
        req["header"]["WritingCompany"] = company
        req["header"]["PolicyType"] = "New"
    return req


# ------------------------------------------------------------------ workers

def _t1_one(args):
    name, req = args
    from importlib import import_module
    from cf_engine.rating import rate
    console = import_module("154_chunk13_rc5_fields_messages")
    try:
        data, ip = console.rate(copy.deepcopy(req))
        base = ("rated", data, sorted(map(str, ip.messages)))
    except Exception as exc:
        base = ("refused", None, str(exc)[:200])
    r = rate(copy.deepcopy(req))
    if r.complete:
        mine = ("rated", r.tree, sorted(map(str, r.ip.messages)))
    else:
        mine = ("refused", None, r.outcome["reasons"][0]["detail"][:200])
    if base[0] != mine[0]:
        return name, f"outcome {base[0]} vs {mine[0]}: {base[2]} | {mine[2]}"
    if base[0] == "refused":
        return name, None if base[2] == mine[2] else f"refusal text differs: {base[2]} | {mine[2]}"
    d = tree_diff(base[1], mine[1], minted=())
    if d:
        return name, f"{len(d)} fields differ, first {d[0]}"
    if base[2] != mine[2]:
        return name, "messages differ"
    hdr = copy.deepcopy(req)
    hdr.setdefault("header", {})["PolicyType"] = "Renewal"
    r2 = rate(hdr)
    if r2.complete and tree_diff(r.tree, r2.tree, minted=()):
        return name, "a PolicyType-only header changed the rating"
    return name, None


def _t2_one(args):
    name, req, root, company = args
    from cf_engine.rating import rate
    req = copy.deepcopy(req)
    req.setdefault("header", {})["WritingCompany"] = company
    req["header"]["PolicyType"] = "New"
    r = rate(req, with_technical=True, waterfall=False, root=Path(root))
    t = r.technical
    if t is None:
        return name, f"no technical: {r.outcome}"
    if t.complete != r.complete:
        return name, f"technical {t.outcome.get('status')} vs carrier {r.outcome.get('status')}: " \
                     f"{(r.outcome.get('reasons') or [{}])[0].get('detail', '')[:160]}"
    if not r.complete:
        same = t.outcome["reasons"][0]["detail"] == r.outcome["reasons"][0]["detail"]
        return name, None if same else "refusals differ"
    d = tree_diff(t.tree, r.tree)
    return name, (f"{len(d)} fields differ, first {d[0]}" if d else None)


def pool_map(fn, items, jobs):
    if jobs <= 1:
        return [fn(x) for x in items]
    with ProcessPoolExecutor(max_workers=jobs, max_tasks_per_child=1) as ex:
        return list(ex.map(fn, items, chunksize=1))


# ------------------------------------------------------------------------- A

def a_t1_property(jobs, n) -> None:
    print("\nA  T1 Property: no company is today's engine")
    sample = per_state(stored(), n)
    res = pool_map(_t1_one, [(name, req) for name, _, _, req in sample], jobs)
    bad = [(nm, why) for nm, why in res if why]
    states = len({s for _, s, _, _ in sample})
    check(f"A1 {len(sample)} stored requests in {states} states rate identically, field for field "
          f"(and a PolicyType-only header changes nothing)", not bad,
          "; ".join(f"{nm}: {why}" for nm, why in bad[:5]))


# ------------------------------------------------------------------------- B

def b_t1_gl() -> None:
    print("\nB  T1 GL: a header with only our field rates as no header")
    from console import catalog
    from gl_engine.rating import Kernel
    k = Kernel()
    bad = []
    for st in ("TX", "NY", "CA", "OH"):
        req = catalog.build("GL", st, {})
        a = k.rate(copy.deepcopy(req))
        req["header"]["PolicyType"] = "Renewal"
        b = k.rate(req)
        if a.premium != b.premium or tree_diff(a.tree, b.tree, minted=()):
            bad.append(st)
    check("B1 TX, NY, CA, OH unchanged by a PolicyType-only header", not bad, ", ".join(bad))


# ------------------------------------------------------------------------- C

def c_t2_property(jobs, n) -> None:
    print("\nC  T2 Property: neutral deviations change nothing")
    root = Path(tempfile.mkdtemp(prefix="deviations_t2_"))
    shutil.copytree(FIX / "UFG", root / "UFG")
    items = per_state(stored(), max(1, n // 2))
    groups = defaultdict(list)
    for it in items:
        groups[(it[1], it[2])].append(it)
    todo, made = [], 0
    for i, ((st, eff), its) in enumerate(sorted(groups.items())):
        co = f"ID{i:03d}"
        (root / "UFG" / co).mkdir(parents=True)
        (root / "UFG" / co / "company.json").write_text(json.dumps({"code": co}), encoding="utf-8")
        try:
            filing(root, co, f"ID-{st}", "CF", [st], eff, identity_rows("CF", st, eff))
        except Exception as exc:
            print(f"        (skipped {st} {eff}: {str(exc)[:120]})")
            continue
        made += 1
        todo += [(nm, req, str(root), co) for nm, _, _, req in its]
    res = pool_map(_t2_one, todo, jobs)
    bad = [(nm, why) for nm, why in res if why]
    check(f"C1 {len(todo)} stored requests under {made} identity filings: carrier == technical",
          not bad and len(todo) > 20, "; ".join(f"{nm}: {why}" for nm, why in bad[:5]) or f"only {len(todo)}")
    shutil.rmtree(root, ignore_errors=True)


# ------------------------------------------------------------------------- D

def d_t2_gl() -> None:
    print("\nD  T2 GL: neutral deviations change nothing")
    from console import catalog
    from gl_engine.rating import Kernel
    root = Path(tempfile.mkdtemp(prefix="deviations_t2gl_"))
    shutil.copytree(FIX / "UFG", root / "UFG")
    k = Kernel()
    bad, n = [], 0
    for st in ("TX", "NY", "CA", "OH", "FL", "IL"):
        req = catalog.build("GL", st, {})
        eff = req["body"]["SchemeKeys"]["EffectiveDateTime"][:10]
        co = f"G{st}"
        (root / "UFG" / co).mkdir(parents=True)
        (root / "UFG" / co / "company.json").write_text(json.dumps({"code": co}), encoding="utf-8")
        filing(root, co, f"ID-{st}", "GL", [st], eff, identity_rows("GL", st, eff))
        req["header"]["WritingCompany"] = co
        r = k.rate(req, with_technical=True, waterfall=False, root=root)
        n += 1
        d = tree_diff(r.technical.tree, r.tree)
        if r.premium != r.technical.premium or d:
            bad.append(f"{st}: {r.technical.premium} vs {r.premium}, {d[:1]}")
    check(f"D1 {n} GL states: carrier == technical under an identity filing", not bad, "; ".join(bad))
    shutil.rmtree(root, ignore_errors=True)


# ------------------------------------------------------------------------- E

GROUP_RATES = {"GroupI": "BasicGroupIRate", "GroupII": "BasicGroupIIRate", "Special": "AdjustedSpecialRate"}


def e_p0(root: Path) -> None:
    print("\nE  the P0 filing rates (UFG Iowa CF)")
    from cf_engine.rating import rate
    want = {"UFC": {"GroupI": "1.511", "GroupII": "3.28", "Special": "3.28"},
            "ADD": {"GroupI": "1.813", "GroupII": "3.934", "Special": "3.934"}}
    for co, lcms in want.items():
        r = rate(ia_sample(co), with_technical=True, root=root)
        t = r.technical
        check(f"E1 {co} rates, and the filing in force is the P0 filing",
              r.complete and r.deviation["filings"][0]["id"] == "IA-CF-UNFG-134289779", str(r.outcome))
        st_c = r.tree.first("CommercialPropertyTable").first("CommercialProperty")
        s_c = _structure(r.tree)
        s_t = _structure(t.tree)
        used = {(n.data["group"], n.data["operands"][0]): n.data["value"]
                for n in r.ip.trace if n.kind == "company-group-lcm"}
        bad = [f"{g}: {used.get((g, op))}" for g, op in (("GroupI", "BasicGroupIBaseRate"),
                                                         ("GroupII", "BasicGroupIIBaseRate"),
                                                         ("Special", "SpecialBaseRate"))
               if not _eq(used.get((g, op)), lcms[g])]
        check(f"E2 {co} class 0951 (all other): each group's base-rate product reads its filed LCM",
              not bad, "; ".join(bad))
        bad = []
        for g, field in GROUP_RATES.items():
            tv, cv, L = Decimal(s_t.first(field).text), Decimal(s_c.first(field).text), Decimal(lcms[g])
            # ISO rounds to 3 places at each product, and adjusts the rate after the LCM step,
            # so the scale holds to within the rounding carried through it, not to the digit
            if abs(cv - tv * L) > Decimal("0.0005") * (L + 2):
                bad.append(f"{field}: {tv} x {L} = {tv * L}, got {cv}")
        check(f"E2b {co} and the group rates scale by those LCMs, within ISO's 3-place rounding",
              not bad, "; ".join(bad))
        lcm = s_c.first("LossCostMultiplier").text
        check(f"E3 {co} the building's LossCostMultiplier field carries the Group I LCM (G2)",
              _eq(lcm, lcms["GroupI"]), lcm)
        check(f"E4 {co} carrier is above technical (every LCM > 1 on this class)",
              Decimal(r.premium) > Decimal(t.premium), f"{t.premium} -> {r.premium}")
        _ = st_c
    # class group A, on a stored Iowa request ISO rated (classes 0951 and 1150)
    items = [it for it in stored({"IA"}) if it[0].startswith("chunk24_rc4_S-IA")]
    if items:
        req = copy.deepcopy(items[0][3])
        req["header"]["WritingCompany"] = "UFC"
        req["header"]["PolicyType"] = "New"
        r = rate(req, root=root)
        notes = [n.data for n in r.ip.trace if n.kind == "company-group-lcm"] if r.complete else []
        a = {(d["group"], d["class_code"]): d["value"] for d in notes}
        check("E5 on a stored Iowa request, class 1150 (group A) takes group A's LCMs and class 0951 "
              "the all-other ones, side by side",
              a.get(("GroupI", "1150")) == "1.067" and a.get(("Special", "1150")) == "2.448"
              and a.get(("GroupI", "0951")) == "1.511" and a.get(("Special", "0951")) == "3.28",
              f"{r.outcome} {sorted(a.items())}")
        check("E6 a request on a later ISO edition carries the D9 'ISO revised' warning",
              any("ISO revised" in w for w in r.deviation["warnings"]), str(r.deviation["warnings"]))


def _structure(tree):
    cp = tree.first("CommercialPropertyTable").first("CommercialProperty")
    loc = cp.first("CommercialPropertyLocationTable").first("CommercialPropertyLocation")
    return loc.first("CommercialPropertyStructureTable").first("CommercialPropertyStructure")


# ------------------------------------------------------------------------- F

def f_waterfall(root: Path) -> None:
    print("\nF  the waterfall, with a table override")
    from cf_engine.rating import rate
    p = root / "UFG" / "UFC" / "authored" / "IA-CF-UNFG-134289779.v1.json"
    d = json.loads(p.read_text(encoding="utf-8"), parse_float=Decimal)
    d["version"] = 2
    d["rows"].append({"target": "TABLE:BasicGroupIIRate.Rate", "scope": {}, "value": Decimal("1.1"),
                      "mode": "multiply"})
    from deviations.files import write_json
    p2 = p.with_name("IA-CF-UNFG-134289779.v2.json")
    write_json(p2, d)
    from deviations.files import load_filing, log_action
    f = load_filing(p2)
    log_action(f.company_dir, f.filing, 2, "propose", "Dan Roman")
    log_action(f.company_dir, f.filing, 2, "sign-off", "Dan Roman")
    build(p2)
    r = rate(ia_sample("UFC"), with_technical=True, root=root)
    dv = r.deviation
    steps = [s["step"] for s in dv["waterfall"]]
    check("F1 the later version is the one in force", dv["filings"][0]["version"] == 2, str(dv["filings"]))
    check("F2 steps in the fixed order: LCM, the table, rounding left over",
          steps == ["LCM", "BasicGroupIIRate", "rounding left over"], str(steps))
    total = sum(Decimal(s["effect"]) for s in dv["waterfall"])
    check("F3 the steps add up exactly to carrier - technical",
          total == Decimal(r.premium) - Decimal(r.technical.premium),
          f"{total} vs {Decimal(r.premium) - Decimal(r.technical.premium)}")
    check("F4 the table step moved the premium (Group II is rated on this risk)",
          Decimal(dv["waterfall"][1]["effect"]) > 0, str(dv["waterfall"]))
    looked = [n.data for n in r.ip.trace if n.kind == "lookup" and n.data.get("table") == "BasicGroupIIRate"]
    check("F5 the trace shows the lookup came from the company layer",
          looked and looked[0]["package"].endswith("+IA-CF-UNFG-134289779.v2"), str(looked[:1]))
    shutil.rmtree(p2.parent.parent / "compiled" / "CF" / "IA" / "IA-CF-UNFG-134289779.v2")
    log_action(f.company_dir, f.filing, 2, "withdraw", "Dan Roman")


# ------------------------------------------------------------------------- G

def g_pin(root: Path) -> None:
    print("\nG  an edition pin")
    from cf_engine.rating import rate
    cj = root / "UFG" / "UFC" / "company.json"
    base = json.loads(cj.read_text(encoding="utf-8"))
    cj.write_text(json.dumps(base | {"edition_pins": {"CF": {"IA": "CF_IA_20250101_V01"}}}), encoding="utf-8")
    r = rate(ia_sample("UFC"), with_technical=True, root=root)
    check("G1 the carrier rates on the pinned package", r.complete and r.packages[0] == "CF_IA_20250101_V01",
          f"{r.packages} {r.outcome}")
    check("G2 technical rates on the same pinned package (M3)",
          r.technical.packages[0] == "CF_IA_20250101_V01", str(r.technical.packages))
    check("G3 the pin is reported and is the waterfall's first step",
          r.deviation["pinned"] and r.deviation["waterfall"][0]["step"] == "edition pin",
          str(r.deviation["waterfall"]))
    cj.write_text(json.dumps(base | {"edition_pins": {"CF": {"IA": "CF_IA_20990101_V01"}}}), encoding="utf-8")
    r = rate(ia_sample("UFC"), root=root)
    check("G4 a pin that cannot be honoured is refused with the reason",
          r.outcome["status"] == "refused" and "cannot be honoured" in r.outcome["reasons"][0]["detail"],
          str(r.outcome))
    cj.write_text(json.dumps(base), encoding="utf-8")


# ------------------------------------------------------------------------- H

def h_refusals(root: Path) -> None:
    print("\nH  refusals, and what is not in force")
    from cf_engine.rating import rate
    r = rate(ia_sample("NOPE"), root=root)
    check("H1 an unknown company is refused, by name", r.outcome["status"] == "refused"
          and "'NOPE' is not known" in r.outcome["reasons"][0]["detail"], str(r.outcome))
    req = ia_sample("UFC")
    req["header"]["PolicyType"] = "Endorsement"
    r = rate(req, root=root)
    check("H2 a PolicyType that is not New or Renewal is refused", r.outcome["status"] == "refused", str(r.outcome))
    r = rate(ia_sample("UFC", "2025-05-15"), root=root)
    check("H3 before the filing's new-business date: rated, carrier = technical, and said so",
          r.complete and r.deviation["carrierPremium"] == r.deviation["technicalPremium"]
          and any("no approved CF filing in force" in w for w in r.deviation["warnings"]),
          str(r.deviation.get("warnings")))
    req = ia_sample("UFC", "2025-09-15")
    req["header"]["PolicyType"] = "Renewal"
    r = rate(req, root=root)
    check("H4 a renewal before 10/1/2025 is not under the filing (D4)",
          any("renewal business" in w for w in r.deviation["warnings"]), str(r.deviation["warnings"]))
    req["body"]["SchemeKeys"]["EffectiveDateTime"] = "2025-10-15T00:00:00"
    r = rate(req, root=root)
    check("H5 a renewal on 10/15/2025 is", r.deviation["filings"] and
          Decimal(r.deviation["carrierPremium"]) > Decimal(r.deviation["technicalPremium"]),
          str(r.deviation))
    from deviations.files import log_action
    cdir = root / "UFG" / "ADD"
    log_action(cdir, "IA-CF-UNFG-134289779", 1, "withdraw", "Dan Roman")
    r = rate(ia_sample("ADD"), root=root)
    check("H6 a filing withdrawn after it compiled is no longer in force (latest line wins)",
          not r.deviation["filings"], str(r.deviation["filings"]))
    log_action(cdir, "IA-CF-UNFG-134289779", 1, "propose", "Dan Roman")
    log_action(cdir, "IA-CF-UNFG-134289779", 1, "sign-off", "Dan Roman")
    man = root / "UFG" / "UFC" / "compiled" / "CF" / "IA" / "IA-CF-UNFG-134289779.v1"
    extra = filing(root, "UFC", "IA-CF-BOGUS", "CF", ["IA"], "2025-06-02",
                   [{"target": "TABLE:BasicGroupIIRate.Rate", "scope": {}, "value": "1.1", "mode": "multiply"}])
    bog = root / "UFG" / "UFC" / "compiled" / "CF" / "IA" / "IA-CF-BOGUS.v1" / \
        "Rate Tables" / "BasicGroupIIRate.Company.RateTable.csv"
    with bog.open("a", encoding="utf-8", newline="") as fh:
        fh.write('"IA","999","Z9","Building","1.1","multiply","IA-CF-BOGUS.v1#1:multiply:1.1"\r\n')
    r = rate(ia_sample("UFC", "2025-07-01"), root=root)
    check("H7 an override key the edition does not have is refused, never rated as technical",
          r.outcome["status"] == "refused" and "does not have" in r.outcome["reasons"][0]["detail"],
          str(r.outcome))
    shutil.rmtree(bog.parent.parent)
    extra.unlink()
    _ = man


# ------------------------------------------------------------------------- I

def i_m6(root: Path) -> None:
    print("\nI  M6 and D13: what ISO may see")
    from cf_engine.rating import rate
    from deviations.engine import iso_request
    from raas import without_own_fields
    req = ia_sample("UFC")
    st = req["body"]["CommercialProperty"][0]["CommercialPropertyLocation"][0]["CommercialPropertyStructure"][0]
    st["LossCostMultiplier"] = 1.10
    clean, warns = iso_request(req, "CF")
    check("I1 the ISO request has neither of our header fields", not any(
        k in clean["header"] for k in ("WritingCompany", "PolicyType")), str(clean["header"]))
    check("I2 ...nor any submitted LCM", "LossCostMultiplier" not in json.dumps(clean["body"]))
    check("I3 ...and the original request is untouched", req["header"]["WritingCompany"] == "UFC"
          and st["LossCostMultiplier"] == 1.10)
    w = without_own_fields(req)
    check("I4 the ISO client strips our header fields itself, whoever calls it",
          "WritingCompany" not in w["header"] and "authorization" in w["header"]
          and req["header"]["WritingCompany"] == "UFC")
    check("I4b ...and, for a request naming a company, every LCM too: ISO only rates technical (D21, O6)",
          "LossCostMultiplier" not in json.dumps(w["body"]) and "LossCostMultiplier" in json.dumps(req["body"]))
    plain = ia_sample(None)
    plain["header"]["PolicyType"] = "New"
    check("I4c a request naming no company keeps its LCMs on the way to ISO",
          "LossCostMultiplier" in json.dumps(without_own_fields(plain)["body"]))
    r = rate(req, with_technical=True, root=root)
    check("I5 a submitted LCM of 1.10 is named in the warnings (D13)",
          any("1.1" in x and "D13" in x for x in r.deviation["warnings"]), str(r.deviation["warnings"]))
    plain = rate(ia_sample(None))
    check("I6 technical ignores the submitted LCM: it equals ISO-only at LCM 1",
          r.technical.premium == plain.premium, f"{r.technical.premium} vs {plain.premium}")
    _ = warns


# ------------------------------------------------------------------------- J

def j_gl(root: Path) -> None:
    print("\nJ  a GL company")
    from console import catalog
    from deviations import iso
    from gl_engine.rating import Kernel
    req = catalog.build("GL", "TX", {})
    eff = req["body"]["SchemeKeys"]["EffectiveDateTime"][:10]
    cls = req["body"]["GeneralLiability"][0]["GeneralLiabilityLocation"][0][
        "GeneralLiabilityClassification"][0]["ClassCode"]
    t = iso.table("GL", "TX", eff, "PremOpsLCM")
    filing(root, "UFC", "TX-GL", "GL", ["TX"], eff, [
        {"target": "LCM:PremOps", "scope": {}, "value": "1.12", "mode": "replace"},
        {"target": "LCM:PremOps", "scope": {"class": str(cls)}, "value": "1.05", "mode": "multiply"},
        {"target": "LCM:ProdsCompldOps", "scope": {}, "value": "1.25", "mode": "replace"}])
    req["header"]["WritingCompany"] = "UFC"
    k = Kernel()
    r = k.rate(req, with_technical=True, root=root)
    tech, car = r.technical, r
    def cov(rating, tag):
        out = {}
        stack = [rating.tree]
        while stack:
            n = stack.pop()
            stack.extend(n.children)
            if n.tag == tag:
                for f in ("LCM", "BasicLimitPremium", "BaseRate"):
                    c = n.first(f)
                    if c is not None:
                        out[f] = c.text
        return out
    po_t, po_c = cov(tech, "GeneralLiabilityClassificationPremOpsCoverage"), \
        cov(car, "GeneralLiabilityClassificationPremOpsCoverage")
    pc_t, pc_c = cov(tech, "GeneralLiabilityClassificationProdsCompldOpsCoverage"), \
        cov(car, "GeneralLiabilityClassificationProdsCompldOpsCoverage")
    check("J1 PremOps carries 1.12 x 1.05 = 1.176 for the risk's class", _eq(po_c.get("LCM"), "1.176"), str(po_c))
    check("J2 Products carries 1.25", _eq(pc_c.get("LCM"), "1.25"), str(pc_c))
    check("J3 Products' basic limit premium is technical x 1.25, to the dollar",
          abs(Decimal(pc_c["BasicLimitPremium"]) - Decimal(pc_t["BasicLimitPremium"]) * Decimal("1.25")) <= 1,
          f"{pc_t} -> {pc_c}")
    wf = r.deviation["waterfall"]
    check("J4 the GL waterfall adds up", sum(Decimal(s["effect"]) for s in wf)
          == Decimal(str(r.premium)) - Decimal(str(tech.premium)), str(wf))
    _ = (po_t, t)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=int(os.environ.get("ERC_MAX_WORKERS", "2")))  # memory-bound machine
    ap.add_argument("--per-state", type=int, default=2)
    a = ap.parse_args()
    a_t1_property(a.jobs, a.per_state)
    b_t1_gl()
    c_t2_property(a.jobs, a.per_state)
    d_t2_gl()
    root = tmp_root()
    for step in (e_p0, f_waterfall, g_pin, h_refusals, i_m6, j_gl):
        step(root)
    shutil.rmtree(root, ignore_errors=True)
    from deviations import suite_log
    suite_log.record("engine", CHECKS)
    print(f"\n{'FAILED: ' + ', '.join(FAILED) if FAILED else 'all passed'}")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
