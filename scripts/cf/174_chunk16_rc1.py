#!/usr/bin/env python3
"""Chunk 16, RC-1 (C16-02 to C16-05): evidence and plumbing, before any golden case.

C16-02  STORED EVIDENCE. Every stored ISO response with a non-zero premium on a
        chunk 16 record is re-rated (157_'s request): ISO's premium, ours, the
        record's state, and the inputs on its parent that drive it. No ISO calls.
        The gaps (records, forms and states ISO never priced) are what RC-2 fills.
C16-03  ATTACH MAP AND SWITCHES. Each premium record's chain up to a coverage
        record, from ISO's DataDef XSD (CW; the five Mine Subsidence states' own),
        the containers' rules, and every premium file's switch rule, grouped by shape.
C16-04  BORROWED VALUES. (a) All 43 premium files: every record placed on a real
        tree (chunk 7's five-coverage Oregon policy; each Mine Subsidence state its
        own), the engine run, every SetPremium operand resolved with the engine's own
        select from the record node: the record it lands on, flagged if a Table
        wrapper, nowhere, or a different record type from its sibling forms.
        (b) The 16 records ISO priced: on ISO's own example trees, SetPremium is
        evaluated by hand (half-up at each DecimalPlaces) from the landed values and
        must equal the engine's premium and ISO's -- a value read before it is set
        would break that. The 27 never priced get the same check in RC-2.
C16-05  TABLES AND LITERALS. Every table the family's files read (premium files,
        containers, the state files), countrywide rows, and every state-filed
        table whose name belongs to the family under ANY name (the sibling-table
        rule); every string / number literal the family's tests compare against.

    python scripts/cf/174_chunk16_rc1.py

Exits 1 on any check that fails.
"""
from __future__ import annotations

import collections
import csv
import json
import re
import sys
import xml.etree.ElementTree as ET
from decimal import Decimal, ROUND_HALF_UP
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))

from cf_engine.resolve import book_for
import functools                                               # noqa: E402
# book_for re-discovers the whole ERC corpus (~0.5-1.8 s) on every call, and this script calls it
# inside loops (~640 times in C16-05 alone). The packages do not change within a run: cache it.
# Measured 2026-09-28 before / after, output identical (logs/174_before.log, 174_after.log).
book_for = functools.lru_cache(maxsize=None)(book_for)
from gl_engine.interp import tree
from gl_engine.interp.values import InterpretError

gc = import_module("149_chunk13_golden_case")
grp = import_module("150_chunk13_c13-08-09_groups_rollup")
rep = import_module("157_chunk14_c14-02_total_replay")
s18 = import_module("164_chunk14_c14-18_all_states")
rc1 = import_module("168_chunk15_rc1")
cen = import_module("173_chunk16_census")
ASOF = "20260917"
P = "CommercialProperty"
RES = ROOT / "results" / "cf-raas"
MINE_STATES = ["IL", "IN", "KY", "OK", "WV"]
FAIL = []


def check(ok, msg):
    print(f"    [{'ok' if ok else 'FAIL'}] {msg}")
    if not ok:
        FAIL.append(msg)


def short(name):
    return name.replace(P, "").replace("Rules.Rule.xml", "") or "policy"


# -------------------------------------------------------------- the population

def population():
    """family -> {premium record: (rule text, package)} across CW and the Mine Subsidence states."""
    cw = book_for("OR", ASOF).parent.package.content
    cw_rules = {f.name: f for f in (cw / "Rules").glob("*.xml")}
    out = {}
    for fam, pat in cen.FAMILIES:
        recs = {}
        if fam.startswith("Mine"):
            for j in MINE_STATES:
                for f in (book_for(j, ASOF).state.package.content / "Rules").glob("*.xml"):
                    if re.search(pat, f.name):
                        t = f.read_text(encoding="utf-8-sig", errors="replace")
                        if cen.set_premium(t):
                            recs.setdefault(f.name[:-len("Rules.Rule.xml")], {})[j] = t
        else:
            for n, f in cw_rules.items():
                if re.search(pat, n) and not cen.EXCLUDE.search(n):
                    t = f.read_text(encoding="utf-8-sig")
                    if cen.set_premium(t):
                        recs[n[:-len("Rules.Rule.xml")]] = {"CW": t}
        out[fam] = recs
    return out


# ------------------------------------------------------------ hand evaluator

def _xml(body):
    root = ET.fromstring(re.sub(r"\brul:", "", body))
    return root if root.tag == "Rule" else root.find(".//Rule")


def _sel(path, ctx):
    return tree.select(path, ctx) if path else [ctx]


def hand(body, node):
    """SetPremium evaluated independently of the engine, from the record node:
    Product / Round (half-up at DecimalPlaces), Sum, Subtract, Divide, FirstValue (its
    FromConstant when absent), Value (FromDataDef / FromParam), Constant, If / Test with
    Equal / NotEqual / Exist, FirstNonNull, WithArgs, and ForEach (each item becomes the
    context, as the engine and ISO do). Returns the value written to Premium."""
    written = {}

    def num(v):
        return Decimal(str(v))

    def q(x, dp):
        return x.quantize(Decimal(1).scaleb(-int(dp)), ROUND_HALF_UP) if dp is not None else x

    def flat(v):
        if isinstance(v, list):
            for x in v:
                yield from flat(x)
        else:
            yield v

    def read(path, ctx):
        hit = tree.select_one(path, ctx)
        return None if hit is None or hit.text in (None, "") else hit.text

    def ev(e, ctx, params):
        tag = e.tag
        if tag == "WithArgs":
            p2 = dict(params)
            out = None
            for c in e:
                if c.tag == "Arg":
                    p2[c.get("Param")] = ev(list(c)[0], ctx, p2)
                else:
                    out = ev(c, ctx, p2)
            return out
        if tag in ("Sequence", "Then", "Else", "Test"):
            out = None
            for c in e:
                out = ev(c, ctx, params)
            return out
        if tag == "ForEach":
            items = _sel(e.get("AtDataDef") or e.get("AtInputDataDef"), ctx)
            res = []
            for it in items:
                out = None
                for c in e:
                    out = ev(c, it, params)
                res.append(out)
            return res
        if tag == "FirstValue":
            v = read(e.get("FromDataDef"), ctx)
            val = e.get("FromConstant") if v is None else v
        elif tag == "Value":
            val = params.get(e.get("FromParam")) if e.get("FromParam") else read(e.get("FromDataDef"), ctx)
        elif tag == "Constant":
            val = e.text or ""
        elif tag == "Exist":
            val = bool(_sel(e.get("AtInputDataDef") or e.get("AtDataDef"), ctx))
        elif tag == "FirstNonNull":
            val = None
            for c in e:
                cand = [x for x in flat(ev(c, ctx, params)) if x not in (None, "")]
                if cand:
                    val = cand[0] if len(cand) == 1 else cand
                    break
        elif tag == "Product":
            r = Decimal(1)
            for c in e:
                r *= num(ev(c, ctx, params))
            val = q(r, e.get("DecimalPlaces"))
        elif tag == "Round":
            val = q(num(ev(list(e)[0], ctx, params)), e.get("DecimalPlaces"))
        elif tag == "Sum":
            val = sum((num(x) for c in e for x in flat(ev(c, ctx, params)) if x not in (None, "")), Decimal(0))
            val = q(val, e.get("DecimalPlaces"))
        elif tag == "Subtract":
            x, y = list(e)
            val = q(num(ev(x, ctx, params)) - num(ev(y, ctx, params)), e.get("DecimalPlaces"))
        elif tag == "Divide":
            # DecimalPlaces applies to Divide and Subtract too (found 2026-09-29, chunk 19 C19-18: GA's tenants'
            # glass <Divide DecimalPlaces="0"> of limit x rate / 100; unrounded, the hand value was $1 high)
            x, y = list(e)
            val = q(num(ev(x, ctx, params)) / num(ev(y, ctx, params)), e.get("DecimalPlaces"))
        elif tag in ("Equal", "NotEqual"):
            x, y = [str(ev(c, ctx, params) or "") for c in e]
            val = (x == y) if tag == "Equal" else (x != y)
        elif tag == "If":
            if ev(e.find("Test"), ctx, params):
                val = ev(e.find("Then"), ctx, params)
            else:
                els = e.find("Else")
                val = ev(els, ctx, params) if els is not None else None
        elif tag == "Truncate":
            v = num(ev(list(e)[0], ctx, params))
            dp = int(e.get("DecimalPlaces") or 0)
            val = v.quantize(Decimal(1).scaleb(-dp), rounding="ROUND_DOWN")
        elif tag == "Convert":
            val = ev(list(e)[0], ctx, params)
        elif tag == "Choose":
            val = None
            for w in e:
                if w.tag == "When" and ev(w.find("Test"), ctx, params):
                    val = ev(w.find("Then"), ctx, params)
                    break
                if w.tag == "Otherwise":
                    val = ev(w, ctx, params) if len(w) else None
                    break
        elif tag == "Otherwise":
            val = None
            for c in e:
                val = ev(c, ctx, params)
        elif tag in ("And", "Or"):
            vals = [bool(ev(c, ctx, params)) for c in e]
            val = all(vals) if tag == "And" else any(vals)
        elif tag == "Not":
            val = not ev(list(e)[0], ctx, params)
        elif tag in ("GreaterThan", "LessThan", "GreaterThanOrEqual", "LessThanOrEqual"):
            x, y = [num(ev(c, ctx, params) or 0) for c in e]
            val = {"GreaterThan": x > y, "LessThan": x < y,
                   "GreaterThanOrEqual": x >= y, "LessThanOrEqual": x <= y}[tag]
        elif tag in ("IsNull", "IsNotNull"):
            v = ev(list(e)[0], ctx, params)
            val = (v in (None, "")) == (tag == "IsNull")
        elif tag == "NotExist":
            val = not _sel(e.get("AtInputDataDef") or e.get("AtDataDef"), ctx)
        else:
            raise ValueError(f"hand: unhandled node {tag}")
        if e.get("ToDataDef") == "Premium":
            written["Premium"] = val
        return val
    try:
        rule = _xml(body)
        for c in rule:
            ev(c, node, {})
        return written.get("Premium")
    except (ValueError, TypeError, ArithmeticError) as exc:
        return f"hand error: {exc}"


def operands(body, node):
    """[(path, owner record | NOWHERE | LOOP EMPTY)] for every FromDataDef in SetPremium, each
    resolved in its own loop context. A path's OWNER is the record it names up to its last
    step: a field absent on an existing owner is an input not given, not a broken path."""
    out = []

    def owner(path, ctx):
        head = path.rsplit("/", 1)[0] if "/" in path else ""
        hits = _sel(head, ctx)
        if not hits:
            return "NOWHERE"
        o = hits[0]
        return short(o.tag) + (" <-- TABLE WRAPPER" if o.tag.endswith("Table") else "")

    def walk(e, ctxs):
        if e.tag == "ForEach":
            path = e.get("AtDataDef") or e.get("AtInputDataDef")
            nxt = [it for c in ctxs for it in _sel(path, c)]
            if not nxt:
                out.append((path, "LOOP EMPTY"))
                return
            ctxs = nxt[:1]
        if e.get("FromDataDef"):
            out.append((e.get("FromDataDef"), owner(e.get("FromDataDef"), ctxs[0])))
        for c in e:
            walk(c, ctxs)
    walk(_xml(body), [node])
    return out


# --------------------------------------------------------------- placement

KNOWN = {P, P + "Location", P + "Structure", P + "OccupClass", P + "PersonalProperty",
         P + "BusinessIncome", P + "SpecialClass", P + "SpecialClassBusnIncome"}


def chain_down(xsd, rec):
    """[(type, in_table)] from the nearest known coverage record down to rec (rec last)."""
    steps, t = [], P + rec
    while t not in KNOWN:
        ps = xsd.parents.get(t)
        if not ps:
            return None
        ptype = ps[0][0]
        if ptype == t + "Table":
            steps.append((t, True))
            t = xsd.parents[ptype][0][0]
        else:
            steps.append((t, False))
            t = ptype
    return t, list(reversed(steps))


def place(sub, xsd, rec, fields=None):
    top, steps = chain_down(xsd, rec)
    d = rc1.node_dicts(sub)[top]
    for i, (t, table) in enumerate(steps):
        last = i == len(steps) - 1
        if table:
            lst = d.setdefault(t + "Table", {t: []})[t]
            if not lst or last:
                lst.append({})
            d = lst[-1]
        else:
            d = d.setdefault(t, {})
    d.update(fields or {})
    return short(top) + " > " + " > ".join(short(t) + ("[]" if tb else "") for t, tb in steps)


def find(data, tag):
    return rc1.find(data, tag)


# ------------------------------------------------------------------ C16-02

def stored_evidence(pop):
    print("\n" + "=" * 90 + "\nC16-02  STORED EVIDENCE (no ISO calls)\n" + "-" * 90)
    recs = {r for fam in pop.values() for r in fam}         # file stems already carry the prefix
    index = rep.fixture_index()
    hits = collections.defaultdict(list)          # stem -> [(rec, iso premium, path)]
    for rp in sorted(RES.glob("chunk13_fixture_*_response.json")):
        stem = rp.name[len("chunk13_fixture_"):-len("_response.json")]
        resp = json.loads(rp.read_text(encoding="utf-8"))

        def walk(o, k=None, path=""):
            if isinstance(o, dict):
                if k in recs and o.get("Premium") not in (None, "", 0, 0.0, "0"):
                    hits[stem].append((k, o.get("Premium")))
                for kk, v in o.items():
                    if isinstance(v, (dict, list)):
                        walk(v, kk)
            elif isinstance(o, list):
                for x in o:
                    walk(x, k)
        walk(resp["Body"])
    trees = {}
    by_rec = collections.defaultdict(list)
    for stem, lst in sorted(hits.items()):
        d = json.loads(index[stem].read_text(encoding="utf-8-sig"))
        st = d["SchemeKeys"]["ProductName"].split()[-1]
        req = {"header": {}, "body": {"SchemeKeys": {"ProductName": d["SchemeKeys"]["ProductName"],
                                                     "EffectiveDateTime": "2026-09-17T00:00:00"},
                                      "CommercialProperty": d["CommercialProperty"]}}
        data, ip = rep.cmp.rate(req)
        trees[stem] = (st, data)
        ours = collections.defaultdict(list)
        for rec, _ in lst:
            ours[rec] = [x.first("Premium").text for x in find(data, rec) if x.first("Premium") is not None]
        for rec, iso in lst:
            ok = any(o not in (None, "") and Decimal(o) == Decimal(str(iso)) for o in ours[rec])
            by_rec[rec].append((stem, st, iso, ok))
    total = 0
    for rec in sorted(by_rec):
        rows = by_rec[rec]
        total += len(rows)
        sts = sorted({st for _, st, _, _ in rows})
        vals = sorted({float(i) for _, _, i, _ in rows})
        check(all(ok for *_, ok in rows),
              f"{short(rec)}: {len(rows)} stored ISO premiums ({', '.join(f'{v:g}' for v in vals[:6])}"
              f"{'...' if len(vals) > 6 else ''}) in {' '.join(sts)}; ours equal on all")
    priced = {r for r in by_rec}
    print(f"  {total} stored ISO premiums on {len(priced)} records across {len(hits)} fixtures")
    never = collections.defaultdict(list)
    for fam, rs in pop.items():
        for r in rs:
            if r not in priced:
                never[fam].append(short(r))
    print("  never priced by ISO (RC-2 fills these):")
    for fam, rs in never.items():
        print(f"    {fam} ({len(rs)}): {', '.join(rs)}")
    return trees, by_rec


# ------------------------------------------------------------------ C16-03

def attach_and_switches(pop):
    print("\n" + "=" * 90 + "\nC16-03  ATTACH MAP AND SWITCHES\n" + "-" * 90)
    xsd_cw = rc1.xsd_for(book_for("OR", ASOF))
    shapes = collections.defaultdict(list)
    for fam, rs in pop.items():
        print(f"  {fam}")
        for r, pk in sorted(rs.items()):
            st = next(iter(pk))
            xsd = xsd_cw if st == "CW" else rc1.xsd_for(book_for(st, ASOF))
            ch = chain_down(xsd, short(P + r) if r.startswith(P) else r)
            where = "NOT IN XSD" if ch is None else short(ch[0]) + " > " + " > ".join(
                short(t) + ("[]" if tb else "") for t, tb in ch[1])
            check(ch is not None, f"{short(r)}: {where}{'' if st == 'CW' else '  (' + ' '.join(pk) + ')'}")
            text = pk[st]
            m = re.search(r'<rul:Rule Name="SetCoverageOnPolicyIndicator".*?</rul:Rule>', text, re.S)
            ep = re.search(r'<rul:Rule Name="ErcProcess".*?</rul:Rule>', text, re.S)
            if m:
                body = m.group(0)
                tests = sorted(set(re.findall(r'FromDataDef="([^"]+)"', body)))
                consts = sorted(set(c for c in re.findall(r'<rul:Constant[^>]*>([^<]+)<', body) if c not in ("0", "1")))
                shapes[(tuple(t.rsplit("/", 1)[-1] for t in tests), tuple(consts))].append(short(r))
            elif ep and "Premium" in ep.group(0):
                shapes[(("ErcProcess forces $0",), ())].append(short(r))
            else:
                shapes[(("no switch",), ())].append(short(r))
    print("\n  switch shapes (fields tested; values compared):")
    for (fields, consts), rs in sorted(shapes.items(), key=lambda x: -len(x[1])):
        print(f"    {len(rs):2d} files: {', '.join(fields) or '(none)'}  {list(consts) if consts else ''}")
        print(f"         e.g. {', '.join(rs[:3])}")
    cw = book_for("OR", ASOF).parent.package.content / "Rules"
    print("\n  containers (records with no SetPremium that carry the premium records):")
    for n in sorted(cw.glob("*.xml")):
        if any(re.search(p, n.name) for _, p in cen.FAMILIES) and not cen.EXCLUDE.search(n.name):
            t = n.read_text(encoding="utf-8-sig")
            if not cen.set_premium(t):
                rules = [x for x in cen.rule_names(t) if x not in cen.STANDARD]
                print(f"    {short(n.name)}: {', '.join(rules) or 'system rules only'}")


# ------------------------------------------------------------------ C16-04

def borrowed(pop, trees, by_rec):
    print("\n" + "=" * 90 + "\nC16-04  BORROWED VALUES\n" + "-" * 90)
    # (a) every premium file placed on a real tree
    placements = {}
    sub = grp.five()
    xsd_cw = rc1.xsd_for(book_for("OR", ASOF))
    for fam, rs in pop.items():
        if fam.startswith("Mine"):
            continue
        for r in rs:
            try:
                placements[r] = place(sub, xsd_cw, short(P + r))
            except Exception as exc:
                check(False, f"{short(r)}: could not place ({exc})")
    try:
        data, ip = gc.run(sub, "OR")
    except InterpretError as exc:
        check(False, f"OR tree raised: {exc}")
        return
    land = collections.defaultdict(dict)      # operand -> {record: landed record}
    print("  (a) all countrywide premium files on chunk 7's five-coverage Oregon policy:")
    for fam, rs in pop.items():
        if fam.startswith("Mine"):
            continue
        for r in sorted(rs):
            nodes_ = find(data, r if r.startswith(P) else P + r)
            if not nodes_:
                check(False, f"{short(r)}: not on the rated tree")
                continue
            body = cen.set_premium(rs[r]["CW"])
            ops = operands(body, nodes_[0])
            bad = []
            for op, where in ops:
                land[op.rsplit("/", 1)[-1]][short(r)] = where
                if "WRAPPER" in where or where == "NOWHERE":
                    bad.append(f"{op} -> {where}")
            check(not bad, f"{short(r)}: {len(ops)} operands, every owner record exists" + (f"; {bad}" if bad else ""))
    print("\n  where each borrowed operand lands (by operand name, across the family files):")
    for op, by in sorted(land.items()):
        dist = collections.Counter(by.values())
        if len(dist) > 1 or next(iter(dist)) != "NOWHERE":
            print(f"    {op:55s} {dict(dist)}")
    for fam in ("Mine Subsidence (state-only)",):
        print(f"  (a) {fam}, each state on its own package:")
        for j in MINE_STATES:
            sj = grp.five()
            sj["CommercialPropertyTable"]["CommercialProperty"][0]["State"] = j
            loc = sj["CommercialPropertyTable"]["CommercialProperty"][0]["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0]
            loc.pop("BasicGroupIRatingTerr", None)
            loc.pop("BasicGroupIIRatingTerr", None)
            loc["BasicGroupIRatingTerrFactor"] = "1.0"
            loc.update(s18.STATE_LOC.get(j, {}))
            xj = rc1.xsd_for(book_for(j, ASOF))
            recs = [r for r, pk in pop[fam].items() if j in pk]
            for r in recs:
                try:
                    place(sj, xj, short(P + r) if r.startswith(P) else r)
                except Exception as exc:
                    check(False, f"{j} {short(r)}: could not place ({exc})")
            try:
                dj, _ = gc.run(sj, j)
            except InterpretError as exc:
                check(False, f"{j}: tree raised {str(exc)[:100]}")
                continue
            for r in recs:
                nodes_ = find(dj, r if r.startswith(P) else P + r)
                body = cen.set_premium(pop[fam][r][j])
                ops = operands(body, nodes_[0]) if nodes_ else []
                bad = [f"{op} -> {w}" for op, w in ops if w == "NOWHERE" or "WRAPPER" in w]
                loops = [op for op, w in ops if w == "LOOP EMPTY"]
                check(bool(nodes_) and not bad, f"{j} {short(r)}: {len(ops)} operands, every owner record exists"
                      + (f"; {bad}" if bad else "") + (f"; loops over {loops} (nothing placed there)" if loops else "")
                      + ("" if nodes_ else "; NOT ON TREE"))

    # (b) the records ISO priced, on ISO's own trees: hand == engine == ISO
    print("\n  (b) the records ISO priced, on ISO's own example trees: hand (landed values) = engine = ISO")
    texts = {}
    for fam, rs in pop.items():
        for r, pk in rs.items():
            for st, t in pk.items():
                texts[(r, st)] = t
    for rec, rows in sorted(by_rec.items()):
        n_ok = n = 0
        detail = ""
        for stem, st, iso, _ in rows:
            state, data = trees[stem]
            text = texts.get((rec, "CW")) or texts.get((rec, state))
            if text is None:
                text = next((t for (r_, st_), t in texts.items() if r_ == rec), None)
            if text is None:
                continue
            # the in-force state file wins where a state rewrites SetPremium
            sp = book_for(state, ASOF).state.package.content / "Rules" / f"{rec}Rules.Rule.xml"
            if sp.exists() and cen.set_premium(sp.read_text(encoding="utf-8-sig", errors="replace")):
                text = sp.read_text(encoding="utf-8-sig", errors="replace")
            body = cen.set_premium(text)
            for node in find(data, rec):
                prem = node.first("Premium")
                if prem is None or prem.text in (None, "") or Decimal(prem.text) == 0:
                    continue
                n += 1
                h = hand(body, node)
                if isinstance(h, Decimal) and h == Decimal(prem.text) == Decimal(str(iso)):
                    n_ok += 1
                elif not detail:
                    detail = f"; e.g. {stem} {state}: hand {h}, engine {prem.text}, ISO {iso}"
        if n:
            check(n_ok == n, f"{short(rec)}: {n_ok} of {n} (hand = engine = ISO){detail}")


# ------------------------------------------------------------------ C16-05

def tables_and_literals(pop):
    print("\n" + "=" * 90 + "\nC16-05  TABLES AND LITERALS\n" + "-" * 90)
    cw = book_for("OR", ASOF).parent.package.content
    cw_files = [f for f in (cw / "Rules").glob("*.xml")
                if any(re.search(p, f.name) for _, p in cen.FAMILIES) and not cen.EXCLUDE.search(f.name)]
    words = {"BI no waiting period": ["BusnIncomeChanges", "NoWaiting", "TimePeriod"],
             "Extended Period of Indemnity": ["ExtendedPeriod"],
             "Civil Authority increased period": ["CivilAuthority"],
             "Pollutant Clean Up aggregate": ["Pollutant"],
             "Spoilage": ["Spoilage"],
             "Molten Material": ["MoltenMaterial", "PublicInstitutional", "PublicInstutional"],
             "Mine Subsidence (state-only)": ["MineSubsidence", "CoalMine"]}
    for fam, pat in cen.FAMILIES:
        texts = [f.read_text(encoding="utf-8-sig") for f in cw_files if re.search(pat, f.name)]
        for j in s18.STATES:
            rd = book_for(j, ASOF).state.package.content / "Rules"
            if rd.exists():
                texts += [f.read_text(encoding="utf-8-sig", errors="replace") for f in rd.glob("*.xml")
                          if re.search(pat, f.name) and not cen.EXCLUDE.search(f.name)]
        tabs = sorted(set(t for s in texts for t in re.findall(r'MatrixFromConstant="([^"]+)"', s)) - {"Pages"})
        print(f"  {fam}")
        for t in tabs:
            f = cw / "Rate Tables" / f"{t}.RateTable.csv"
            print(f"    reads {t:58s} CW rows {cen.rows(f) if f.exists() else 'NOT FILED'}")
        filed = collections.defaultdict(list)
        for j in s18.STATES:
            td = book_for(j, ASOF).state.package.content / "Rate Tables"
            if not td.exists():
                continue
            for f in td.glob("*.RateTable.csv"):
                if any(w in f.name for w in words[fam]):
                    filed[f.name[:-len(".RateTable.csv")]].append(f"{j}:{cen.rows(f)}")
        for t, js in sorted(filed.items()):
            flag = "" if t in tabs else "   <-- a state name, not read by the countrywide files"
            print(f"    state-filed {t:52s} {' '.join(js)}{flag}")
        lits = collections.Counter()
        for s in texts:
            for m in re.finditer(r'<rul:(?:Equal|NotEqual|GreaterThan|LessThan|GreaterThanOrEqual|LessThanOrEqual)>(.*?)</rul:(?:Equal|NotEqual|GreaterThan|LessThan|GreaterThanOrEqual|LessThanOrEqual)>', s, re.S):
                for c in re.findall(r'<rul:Constant[^>]*>([^<]*)<', m.group(1)):
                    lits[c] += 1
        print(f"    literals compared in tests: {', '.join(f'{k!r}' for k, _ in lits.most_common(24))}")


def main():
    pop = population()
    print(f"{book_for('OR', ASOF)}\n" + "\n".join(f"  {fam}: {len(rs)} premium records" for fam, rs in pop.items()))
    trees, by_rec = stored_evidence(pop)
    attach_and_switches(pop)
    borrowed(pop, trees, by_rec)
    tables_and_literals(pop)
    print("\n" + ("RC-1: ALL CHECKS PASS" if not FAIL else f"RC-1: {len(FAIL)} FAILED"))
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
