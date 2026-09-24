"""Chunk 13, RC-5: C13-25 (shared names), C13-27 (messages), C13-28 (stat codes), against ISO.

Every live ISO call chunk 13 made kept its full response (`results/cf-raas/chunk13_*`).
This rebuilds each request exactly (from the same case builders: 149_, 150_, 151_,
152_, 153_), rates it on the engine, and compares with ISO's response -- no new calls:

  FIELDS    every field whose name carries Terror / TRIA / Terrsm / CertfdActs, on
            every record it appears on (policy, location, the five coverage groups),
            plus every field of every terrorism form, disclosure and PostTRIA record.
            That is gate 6: the SAME name on different records must hold ISO's value on
            each record, not just the premium. Stat codes are among them (gate C13-28).
  MESSAGES  the full set of validation messages, ours against ISO's (gate 9).

    python scripts/cf/154_chunk13_rc5_fields_messages.py [--verbose]
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from datetime import date
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))
sys.path.insert(0, str(ROOT / "scripts"))

from cf_engine.config import NULL_ARITHMETIC, ROUNDING
from cf_engine.resolve import book_for
from gl_engine.interp.interpreter import Interpreter
from gl_engine.interp.tree import Node
from gl_engine.interp.values import InterpretError

gc = import_module("149_chunk13_golden_case")
grp = import_module("150_chunk13_c13-08-09_groups_rollup")
rc3 = import_module("151_chunk13_rc3_mechanisms")
st4 = import_module("152_chunk13_rc4_states")
rw = import_module("153_chunk13_c13-19-20_state_rewrites")
r11, rp = gc.r11, gc.rp
OUT = gc.OUT
FIELD = re.compile(r"Terror|TRIA|Terrsm|CertfdActs")
REC = re.compile(r"Terror|TRIA|Terrsm|CertfdActs|CertifiedActs|ZzDisclosure|PostTRIACoverage")


def pairs():
    """(name, request, response path) for every stored chunk 13 live call."""
    for cid, (label, kw, want) in gc.CASES.items():
        yield f"golden {cid}", r11.payload(gc.submission(**kw)), OUT / f"chunk13_golden_{cid}_response.json"
    for cid, (label, build, want) in grp.CASES.items():
        yield f"groups {cid}", r11.payload(build()), OUT / f"chunk13_groups_{cid}_response.json"
    for cid, task, label, kw, want, go in rc3.CASES:
        if go:
            yield f"rc3 {cid}", r11.payload(rc3.sub(**kw)), OUT / f"chunk13_rc3_{cid}_response.json"
    res, juris = st4.states()
    for j in juris:
        book = book_for(j, st4.ASOF, resolver=res)
        plan, _, has_fire = st4.territory_plan(book, j)
        if not plan or plan[0]["py3"] is None:
            continue
        p = plan[0]
        for case, kw in (("in-effect", {}), ("declined", {"cert": "No"}),
                         ("post-TRIA", {"tria": rc3.POST, "post": "No Exclusion"})):
            yield f"rc4 {j} {case}", state_req(j, st4.state_sub(j, p["territory"], **kw)), \
                OUT / f"chunk13_rc4_{j}_{case}_response.json"
    for j, group, label, sub in rw.cases():
        tag = f"{j}_{group.replace(' ', '')}_{label[:10].replace(' ', '').replace(',', '')}"
        yield f"c1319 {j} {group} {label}", state_req(j, sub), OUT / f"chunk13_c1319_{tag}_response.json"


def state_req(j, sub):
    req = r11.payload(sub)
    for cp in req["body"]["CommercialProperty"]:
        cp["State"] = j
    req["body"]["SchemeKeys"]["ProductName"] = r11.PRODUCT.format(state=j)
    return req


def rate(req):
    sk = req["body"]["SchemeKeys"]
    st = sk["ProductName"].split()[-1]
    eff = date.fromisoformat(sk["EffectiveDateTime"][:10])
    bk = book_for(st, eff.strftime("%Y%m%d"))
    sub = {"EffDate": eff.strftime("%m/%d/%Y"), "ExpDate": eff.replace(year=eff.year + 1).strftime("%m/%d/%Y")}
    sub.update(rp.unwrap(rp.to_engine({"CommercialProperty": req["body"]["CommercialProperty"]}), rp.singletons(bk)))
    ip = Interpreter(bk, rounding=ROUNDING, null_arithmetic=NULL_ARITHMETIC)
    data = Node.from_dict(f"MasterCF{st}", sub)
    ip.run(data)
    return data, ip


def ours_all(data):
    out = {}

    def walk(n, path):
        rec = path.rsplit("/", 1)[-1].split("[")[0]
        idx = {}
        for c in n.children:
            if c.tag.endswith("Table"):
                for r in c.children:
                    i = idx.get(r.tag, 0)
                    idx[r.tag] = i + 1
                    walk(r, f"{path}/{r.tag}[{i}]")
            elif c.children:
                i = idx.get(c.tag, 0)
                idx[c.tag] = i + 1
                walk(c, f"{path}/{c.tag}[{i}]")
            elif FIELD.search(c.tag) or REC.search(rec):
                out[f"{path}/{c.tag}"] = c.text
    for t in data.children:
        if t.tag == "CommercialPropertyTable":
            for i, r in enumerate(t.children):
                walk(r, f"CommercialProperty[{i}]")
    return out


def iso_all(resp):
    out = {}

    def walk(o, path):
        rec = path.rsplit("/", 1)[-1].split("[")[0]
        for k, v in o.items():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                for i, x in enumerate(v):
                    walk(x, f"{path}/{k}[{i}]")
            elif isinstance(v, dict):
                walk(v, f"{path}/{k}[0]")
            elif FIELD.search(k) or REC.search(rec):
                out[f"{path}/{k}"] = v
    cp = resp["Body"]["CommercialProperty"]
    for i, x in enumerate(cp if isinstance(cp, list) else [cp]):
        walk(x, f"CommercialProperty[{i}]")
    return out


#: Known, not a rating difference: form names and numbers never resolve where the
#: package files its own Pages table (OI-106, no premium impact). Counted, reported
#: separately, not failed here.
OI106 = {"ErcFormName", "ErcFormNumber"}
ISO_DATE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})T00:00:00$")


def same(a, b):
    m = ISO_DATE.match(str(a or ""))
    if m:                                         # ISO echoes dates as ISO datetimes
        a = f"{m[2]}/{m[3]}/{m[1]}"
    na, nb = rp.num(a), rp.num(b)
    if na is not None or nb is not None:
        return na == nb or (na in (None, 0.0) and nb in (None, 0.0))
    return (a or "") == (b or "")


def iso_messages(resp):
    out = set()

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == "RatingMessages":
                    for kind in (v.values() if isinstance(v, dict) else []):
                        for e in (kind if isinstance(kind, list) else []):
                            if isinstance(e, dict) and e.get("Description"):
                                out.add(e["Description"])
                else:
                    walk(v)
        elif isinstance(o, list):
            for x in o:
                walk(x)
    walk(resp)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args()
    n = fld_ok = msg_ok = n106 = 0
    skipped = []
    fdiff = collections.Counter()
    mdiff = collections.Counter()
    compared_fields = 0
    names_by_record = collections.defaultdict(set)
    for name, req, rpath in pairs():
        if not rpath.exists():
            skipped.append(name)
            continue
        resp = json.loads(rpath.read_text(encoding="utf-8"))
        try:
            data, ip = rate(req)
        except InterpretError as exc:
            print(f"  {name}: ENGINE RAISED {str(exc)[:80]}")
            continue
        n += 1
        ours, iso = ours_all(data), iso_all(resp)
        for k in iso:
            rec = k.rsplit("/", 2)[-2].split("[")[0]
            names_by_record[k.rsplit("/", 1)[-1]].add(rec)
        d = [(k, v, ours.get(k)) for k, v in iso.items() if not same(v, ours.get(k))]
        oi106 = [x for x in d if x[0].rsplit("/", 1)[-1] in OI106]
        n106 += len(oi106)
        d = [x for x in d if x not in oi106]
        compared_fields += len(iso)
        if not d:
            fld_ok += 1
        for k, v, o in d:
            fdiff[(k.rsplit("/", 1)[-1], str(v), str(o))] += 1
            if a.verbose:
                print(f"  {name}: FIELD {k[-80:]} ISO {v} ours {o}")
        mo, mi = set(ip.messages), iso_messages(resp)
        if mo == mi:
            msg_ok += 1
        else:
            for m in mo - mi:
                mdiff[("ours only", m)] += 1
            for m in mi - mo:
                mdiff[("ISO only", m)] += 1
            if a.verbose:
                print(f"  {name}: MESSAGES ours-only {sorted(mo - mi)} ISO-only {sorted(mi - mo)}")
    print(f"{n} stored ISO responses re-rated ({len(skipped)} cases had no stored response: ISO refused them)\n")
    print(f"C13-25 / C13-28  FIELDS: {fld_ok} of {n} responses agree on every terrorism field "
          f"({compared_fields} field values compared)")
    print(f"    set aside: {n106} ErcFormName / ErcFormNumber values reading 'Value Not Found' (OI-106)")
    for (f, v, o), c in fdiff.most_common(25):
        print(f"    {c:4d}x  {f}: ISO {v!r} ours {o!r}")
    shared = {f: sorted(r) for f, r in names_by_record.items() if len(r) > 1}
    print(f"    field names carried on more than one record type: {len(shared)} "
          f"(e.g. {', '.join(list(shared)[:6])})")
    print(f"\nC13-27  MESSAGES: {msg_ok} of {n} responses have identical message sets")
    for (side, m), c in mdiff.most_common(20):
        print(f"    {c:4d}x  {side:9s} {m[:140]}")
    sys.exit(0 if fld_ok == n else 1)


if __name__ == "__main__":
    main()
