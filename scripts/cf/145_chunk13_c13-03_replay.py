"""C13-03: replay every stored ISO response that carries a non-zero terrorism premium.

No ISO calls. For each `results/cf-raas/*_response.json` whose tree holds a
`TerrorismPremium` above 0, the matching `*_request.json` (the exact payload ISO
priced) is converted back to an engine submission (`to_engine`, C12-03), rated
at the same effective date and state, and every terrorism field is compared
record by record:

    PreTRIAPremium, PostTRIAPremium, TerrorismPremium   on every coverage record
    Premium, Total*Premium                               on every roll-up record
                                                         (ZzDisclosure*, PostTRIACoverage)

Records are matched by path (record names and positions), never by order of
appearance. Exits 1 on any disagreement.

    python scripts/cf/145_chunk13_c13-03_replay.py [--verbose]
"""
import argparse
import json
import re
import sys
from datetime import date
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))

from cf_engine.config import NULL_ARITHMETIC, ROUNDING
from cf_engine.resolve import book_for
from gl_engine.interp.interpreter import Interpreter
from gl_engine.interp.tree import Node
from gl_engine.interp.values import InterpretError

to_engine = import_module("125_chunk12_c12-03_operand_types").to_engine
RESULTS = ROOT / "results" / "cf-raas"
COVERAGE_FIELDS = ("PreTRIAPremium", "PostTRIAPremium", "TerrorismPremium")
ROLLUP = re.compile(r"ZzDisclosure|PostTRIACoverage")
ROLLUP_FIELDS = re.compile(r"^(Premium|Total\w*Premium)$")


def iso_fields(resp):
    """{path: value} for every terrorism field in ISO's response."""
    out = {}

    def walk(o, path):
        if isinstance(o, dict):
            rec = path.rsplit("/", 1)[-1].split("[")[0]
            for k, v in o.items():
                if isinstance(v, list) and v and isinstance(v[0], dict):
                    for i, x in enumerate(v):
                        walk(x, f"{path}/{k}[{i}]")
                elif isinstance(v, dict):
                    walk(v, f"{path}/{k}[0]")
                elif k in COVERAGE_FIELDS or (ROLLUP.search(rec) and ROLLUP_FIELDS.match(k)):
                    out[f"{path}/{k}"] = v
    body = resp["Body"]
    cp = body["CommercialProperty"]
    for i, x in enumerate(cp if isinstance(cp, list) else [cp]):
        walk(x, f"CommercialProperty[{i}]")
    return out


def our_fields(data):
    """The same paths from the engine's rated tree (Table wrappers skipped)."""
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
            elif c.children:                          # a record addressed without a Table
                i = idx.get(c.tag, 0)
                idx[c.tag] = i + 1
                walk(c, f"{path}/{c.tag}[{i}]")
            elif c.tag in COVERAGE_FIELDS or (ROLLUP.search(rec) and ROLLUP_FIELDS.match(c.tag)):
                out[f"{path}/{c.tag}"] = c.text
    for t in data.children:
        if t.tag == "CommercialPropertyTable":
            for i, r in enumerate(t.children):
                walk(r, f"CommercialProperty[{i}]")
    return out


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


_SINGLETONS = {}


def singletons(bk):
    """Records the rules address WITHOUT a Table wrapper (e.g. the policy's
    `CommercialPropertyPostTRIACoverage`), read from the filed rules, not listed
    by hand. ISO sends these as a JSON object; `to_engine` wraps every object in
    a one-row table, which puts the record where no rule looks (found by C13-03:
    AK and WY's PostTRIA premium read as absent until this was fixed)."""
    # Keyed by parent AND state: a state's own rules can address a record bare that the
    # countrywide rules never mention (KY's CommercialPropertyMineSubsidenceCoverage). Keyed
    # by the parent alone, the first state rated (Oregon) fixed the set for every state on
    # that parent, and Kentucky's mine subsidence record was never unwrapped (C14-02).
    key = (bk.parent.package.content, bk.state.package.content)
    if key not in _SINGLETONS:
        names = set()
        for content in (bk.parent.package.content, bk.state.package.content):
            rd = content / "Rules"
            if not rd.exists():
                continue
            for f in rd.glob("*.xml"):
                names |= set(re.findall(r'At(?:Input|Output)?DataDef="(CommercialProperty\w+)"',
                                        f.read_text(encoding="utf-8-sig")))
        _SINGLETONS[key] = {n for n in names if not n.endswith("Table")}
    return _SINGLETONS[key]


def unwrap(node, names):
    """`XTable: {X: [rec]}` -> `X: rec` for every X the rules address bare."""
    if isinstance(node, dict):
        for k in list(node):
            v = node[k]
            base = k[:-5] if k.endswith("Table") else None
            if base in names and isinstance(v, dict) and len(v.get(base, [])) == 1:
                node.pop(k)
                node[base] = v[base][0]
                unwrap(node[base], names)
            else:
                unwrap(v, names)
    elif isinstance(node, list):
        for x in node:
            unwrap(x, names)
    return node


def replay(req, resp):
    sk = req["body"]["SchemeKeys"]
    st = sk["ProductName"].split()[-1]
    eff = date.fromisoformat(sk["EffectiveDateTime"][:10])
    exp = eff.replace(year=eff.year + 1)
    bk = book_for(st, eff.strftime("%Y%m%d"))
    sub = {"EffDate": eff.strftime("%m/%d/%Y"), "ExpDate": exp.strftime("%m/%d/%Y")}
    sub.update(unwrap(to_engine({"CommercialProperty": req["body"]["CommercialProperty"]}), singletons(bk)))
    ip = Interpreter(bk, rounding=ROUNDING, null_arithmetic=NULL_ARITHMETIC)
    data = Node.from_dict(f"MasterCF{st}", sub)
    ip.run(data)
    return st, eff, our_fields(data)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args()

    cases = []
    for p in sorted(RESULTS.glob("*_response.json")):
        # C13-03's population is the responses that existed BEFORE chunk 13 went live
        # (chunk 12's and NY's). chunk13_* responses are chunk 13's own evidence and
        # are compared, field for field and message for message, by 154_ and 155_;
        # several of them are stored without a request file, so they don't belong here.
        if p.name.startswith("chunk13_"):
            continue
        resp = json.loads(p.read_text(encoding="utf-8-sig"))
        iso = iso_fields(resp)
        if any((num(v) or 0) > 0 for k, v in iso.items() if k.endswith("TerrorismPremium")):
            q = p.with_name(p.name.replace("_response.json", "_request.json"))
            cases.append((p.name.replace("_response.json", ""), q, iso))
    print(f"{len(cases)} stored ISO responses carry a non-zero TerrorismPremium\n")

    agree = disagree = refused = 0
    fails = []
    for name, q, iso in cases:
        if not q.exists():
            print(f"  {name:40s} NO REQUEST ON DISK")
            fails.append(name)
            continue
        req = json.loads(q.read_text(encoding="utf-8-sig"))
        try:
            st, eff, ours = replay(req, None)
        except InterpretError as exc:
            refused += 1
            print(f"  {name:40s} ours REFUSED: {str(exc)[:110]}")
            fails.append(name)
            continue
        diffs = []
        for k, v in iso.items():
            o = ours.get(k)
            if num(v) != num(o) and not (num(v) in (None, 0.0) and num(o) in (None, 0.0)):
                diffs.append((k, v, o))
        extra = [k for k in ours if k not in iso and (num(ours[k]) or 0) != 0]
        terr = {k.split("/")[-2].split("[")[0].replace("CommercialProperty", "") + "." + k.rsplit("/", 1)[-1]: v
                for k, v in iso.items() if (num(v) or 0) > 0}
        if not diffs and not extra:
            agree += 1
            print(f"  {name:40s} {st} {eff}  AGREE  ISO non-zero: {terr}")
        else:
            disagree += 1
            fails.append(name)
            print(f"  {name:40s} {st} {eff}  DIFFER")
            for k, v, o in diffs:
                print(f"       {k.replace('CommercialProperty', ''):110s} ISO {v}  ours {o}")
            for k in extra:
                print(f"       {k.replace('CommercialProperty', ''):110s} ISO (absent)  ours {ours[k]}")
        if a.verbose:
            for k in sorted(iso):
                print(f"       {k.replace('CommercialProperty', ''):110s} ISO {iso[k]}  ours {ours.get(k)}")

    print(f"\n{agree} agree, {disagree} differ, {refused} refused, of {len(cases)}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
