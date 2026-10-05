#!/usr/bin/env python3
"""Chunk 12, C12-03 -- engine readiness by operand TYPE, not element name.

Chunk 11's census said "every `rul:` node is implemented" and was right, and
the engine still had two gaps: a blank date compared differently from ISO
(OI-102) and date subtraction had the wrong sign (OI-107). Both were about
what the operands WERE, not which node held them. So this task asks the
question two ways.

**Part 1, static.** Every operator in the chunk 12 population (the 208
countrywide family files in all 5 parent editions, plus every state's own
family files, the 45 state-only ones included), with the declared `@Type` of
each operand. Each signature is classed against what the interpreter
actually does with it (`gl_engine/interp/nodes.py`, `values.py`):

  ordered comparison   numbers, or two dates; a date against a number or a
                       non-numeric string REFUSES
  arithmetic           numbers only; a dateTime, boolean or non-numeric
                       string operand REFUSES
  equality             text fallback when one side is numeric and the other
                       is not; a boolean against a string constant compares
                       `True` to `"true"` and is FALSE
  every @Type          must be one `coerce` knows

and against the signatures the closed chunks' own files carry, so a shape
chunk 12 meets for the first time is named before a golden case trips on it.

**Part 2, live.** Every ISO STC fixture that carries a chunk 12 family record
is converted to an engine submission and rated at 2026-09-17 (OI-105). A
refusal names the engine gap; a clean run with the family's records present
and priced proves the path end to end without asserting a number (STC ships
inputs only for CF, so there is no premium to compare yet; that is each
family's gate 9).

    python scripts/cf/125_chunk12_c12-03_operand_types.py

Exits 0 when no chunk 12 shape is unhandled and no fixture refuses on a
chunk 12 record; 1 otherwise.
"""
from __future__ import annotations

import collections
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from importlib import import_module

from cf_engine.config import NULL_ARITHMETIC, ROUNDING
from cf_engine.resolve import book_for
from gl_engine.interp.interpreter import Interpreter
import _iso_refusals as _iso                                    # noqa: E402
from gl_engine.interp.tree import Node
from gl_engine.interp.values import TYPES, InterpretError

census = import_module("123_chunk12_census")
census11 = import_module("106_chunk11_census")
ASOF = census.ASOF
ISO_CF = census.ISO_CF
NS = "{http://www.verisk.com/iso/erc/Rule}"
KEYS = tuple(census.FAMILIES.values())

ORDERED = {"GreaterThan", "LessThan", "GreaterThanOrEqual", "LessThanOrEqual"}
EQUALITY = {"Equal", "NotEqual"}
ARITH = {"Sum", "Subtract", "Product", "Divide", "Max", "Round", "Truncate", "Power"}
NUMERIC = {"integer", "long", "decimal"}
#: Closed chunks' own files: the five core groups and their cells, Legal
#: Liability, Earthquake, Blanket and Leasehold Interest. An approximation of
#: "already exercised", good enough to separate new shapes from familiar ones.
CLOSED = re.compile(r"CommercialProperty(Structure|PersonalProperty|BusinessIncome|SpecialClass"
                    r"|SpclClass|LegalLiability|Earthquake|Blanket|LeaseholdInterest|"
                    r"BasicGroup|Broad|Special|Policy|Location)")


def tag(el):
    return el.tag.replace(NS, "")


def op_type(el) -> str:
    """The type an operand DECLARES, as the evaluator will see it.

    `Locate`, `If`, `Choose` and the clause wrappers are not values of their
    own: each evaluates to whatever its inner branch yields, so they take the
    inner type. `Break` yields nothing at all; it raises out of the operator,
    which is the one shape here that changes a value (OI-108).
    """
    t = tag(el)
    typ = el.attrib.get("Type")
    if t == "Break":
        return "BREAK"
    if t in ("Locate", "Sequence", "Then", "Else", "Otherwise", "When", "If", "Choose"):
        inner = [k for k in el if tag(k) != "Test"]
        types = {op_type(k) for k in (inner[-1:] if t in ("Locate", "Sequence") else inner)}
        types.discard("none")
        if len(types) == 1:
            return types.pop()
        if types <= NUMERIC | {"number", "multi"} and types:
            return "number"
        return "|".join(sorted(types)) or "none"
    if t in ("Constant", "Value", "FirstValue", "Convert", "Copy", "Lookup",
             "RunRule", "FirstNonNull", "LastNonNull", "Null"):
        return typ or "string"
    if t in ORDERED | EQUALITY | {"And", "Or", "IsNull", "IsNotNull", "Exist", "NotExist"}:
        return "boolean"
    if t in ARITH | {"Count", "Length", "DatePart", "DateDifference"}:
        return "number"
    if t in ("DateAdd", "DateCreate"):
        return "dateTime"
    if t in ("Concat", "PadLeft", "Guid"):
        return "string"
    if t == "ForEach":
        return "multi"
    return t


def classify(op: str, types: tuple[str, ...], kids) -> str:
    """What the interpreter does with this signature: ok / REFUSES / WRONG."""
    num = NUMERIC | {"number", "multi"}
    if op in ORDERED:
        if all(t == "dateTime" for t in types):
            return "ok (date order; 01/01/0001 sentinel = earliest, OI-102)"
        if all(t in num for t in types):
            return "ok"
        if "dateTime" in types:
            return "REFUSES: date against non-date"
        if "string" in types:
            lits = [k.text for k, t in zip(kids, types) if t == "string" and tag(k) == "Constant"]
            if lits and all(re.fullmatch(r"-?\d+(\.\d+)?", (x or "").strip()) for x in lits):
                return "ok (numeric string literal)"
            return "RISK: ordered compare of a string (refuses unless numeric at run time)"
        return f"CHECK: {types}"
    if op in ARITH:
        if "BREAK" in types:
            if op == "Sum":
                return ("ok (Sum finishes over what it has added, then breaks the loop: "
                        "OI-108, fixed 2026-09-23)")
            return f"WRONG: Break inside {op}, which does not carry a partial value up"
        bad = [t for t in types if t not in num]
        if not bad:
            return "ok"
        if set(bad) <= {"string"}:
            return "RISK: string operand in arithmetic (refuses unless numeric at run time)"
        return f"REFUSES: {sorted(set(bad))} in arithmetic"
    if op in EQUALITY:
        s = set(types)
        if "boolean" in s and "string" in s:
            return "WRONG: boolean against string compares True to 'true' -> False"
        if "dateTime" in s and s != {"dateTime"}:
            return "CHECK: date against non-date equality (text compare)"
        return "ok"
    return "ok"


def signatures(texts: dict[str, str]):
    """(op, types, verdict) -> [(file, rule)] for every operator."""
    out = collections.defaultdict(list)
    bad_types = collections.Counter()
    for fname, s in texts.items():
        root = ET.fromstring(s)
        rule = None
        for r in root.iter(NS + "Rule"):
            rule = r.attrib.get("Name")
            for el in r.iter():
                t = tag(el)
                ty = el.attrib.get("Type")
                if ty is not None and ty not in TYPES:
                    bad_types[(t, ty)] += 1
                if t not in ORDERED | EQUALITY | ARITH:
                    continue
                kids = list(el)
                types = tuple(op_type(k) for k in kids)
                out[(t, types, classify(t, types, kids))].append((fname, rule))
    return out, bad_types


def population():
    """Family files: every CW parent edition, then every state's own."""
    books = {}
    for j in census11.JURIS:
        if j == "PR":
            continue
        try:
            books[j] = book_for(j, ASOF)
        except Exception:
            pass
    fam, closed = {}, {}
    for pdir in {bk.parent.package.content for bk in books.values()}:
        for f in (pdir / "Rules").glob("*.xml"):
            key = f"{pdir.name}/{f.name}"
            if any(k in f.name for k in KEYS):
                fam[key] = f.read_text(encoding="utf-8-sig")
            elif CLOSED.match(f.name) and pdir.name.replace(" ", "") == "CFCW20260601V01":
                closed[key] = f.read_text(encoding="utf-8-sig")
    for j, bk in books.items():
        sdir = bk.state.package.content / "Rules"
        if sdir.exists():
            for f in sdir.glob("*.xml"):
                if any(k in f.name for k in KEYS):
                    fam[f"{j}/{f.name}"] = f.read_text(encoding="utf-8-sig")
    return books, fam, closed


# ------------------------------------------------------------------ part 2

DATE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})(T.*)?$")


def to_engine(o):
    """ISO STC JSON -> engine submission: `X: [...]` becomes `XTable: {X: [...]}`,
    a single-record object becomes a one-row table, ISO dates become MM/DD/YYYY.
    The inverse of `118_chunk11_c11-23_raas.to_raas`."""
    if isinstance(o, dict):
        out = {}
        for k, v in o.items():
            if isinstance(v, list) and (not v or isinstance(v[0], dict)):
                out[k + "Table"] = {k: [to_engine(x) for x in v]}
            elif isinstance(v, dict):
                out[k + "Table"] = {k: [to_engine(v)]}
            else:
                out[k] = to_engine(v)
        return out
    if isinstance(o, bool):
        return "true" if o else "false"
    if isinstance(o, str):
        m = DATE.match(o)
        return f"{m[2]}/{m[3]}/{m[1]}" if m else o
    return o


def family_nodes(node, path=""):
    """(family, tag, Premium) for every family record in the rated tree."""
    for ch in node.children:
        fam = next((f for f, k in census.FAMILIES.items() if k in ch.tag), None)
        if fam and not ch.tag.endswith("Table"):
            prem = next((g.text for g in ch.children if g.tag == "Premium"), None)
            yield fam, ch.tag, prem
        yield from family_nodes(ch)


def run_fixtures():
    fixtures = []
    for p in sorted(ISO_CF.rglob("STC/*.json")):
        t = p.read_text(encoding="utf-8-sig", errors="replace")
        fams = [f for f, k in census.FAMILIES.items() if k in t]
        if fams:
            fixtures.append((p, fams))
    results = []
    for p, fams in fixtures:
        d = json.loads(p.read_text(encoding="utf-8-sig"))
        st = d["SchemeKeys"]["ProductName"].split()[-1]
        sub = {"EffDate": "09/17/2026", "ExpDate": "09/17/2027"}
        sub.update(to_engine({"CommercialProperty": d["CommercialProperty"]}))
        try:
            ip = Interpreter(book_for(st, ASOF), rounding=ROUNDING,
                             null_arithmetic=NULL_ARITHMETIC)
            data = Node.from_dict(f"MasterCF{st}", sub)
            ip.run(data)
        except InterpretError as exc:
            # C28-05: ours refuses where ISO refused this same fixture (chunk 12, 2026-09-17), at the same table
            iso = _iso.saved_iso_refusal(p.stem)
            results.append((p, st, fams, "ISO-REFUSED" if iso and iso == _iso.table_of(exc) else "REFUSED", str(exc), []))
            continue
        except Exception as exc:                       # noqa: BLE001 -- report, never hide
            results.append((p, st, fams, "ERROR", f"{type(exc).__name__}: {exc}", []))
            continue
        results.append((p, st, fams, "OK", "", list(family_nodes(data))))
    return results


UA_PP = "CommercialPropertyLimitedCoverageForUnmannedAircraftScheduledAndOrBlanketCoveragePrsnlProp"


def probe_drone(st: str, blanket: bool) -> str:
    """`TotalScheduleLimit` on the Contents drone record after a real run."""
    p = next(ISO_CF.rglob("STC/STC_CP000015474.json"))
    d = json.loads(p.read_text(encoding="utf-8-sig"))
    stack = [d]
    while stack:                                    # find the drone Detail record
        o = stack.pop()
        if isinstance(o, dict):
            if UA_PP in o:
                det = o[UA_PP][0][UA_PP + "Detail"][0]
                break
            stack.extend(o.values())
        elif isinstance(o, list):
            stack.extend(o)
    if blanket:
        det["BlanketCoverageUnmannedAircraftAppliesToUnmannedAircraftNotIndividuallyDescribed"] = "Yes"
        det["BlanketLimitOfInsurance"] = det["LimitOfInsurance"]
    for cp in d["CommercialProperty"]:
        cp["State"] = st
    sub = {"EffDate": "09/17/2026", "ExpDate": "09/17/2027"}
    # C28-05: the fixture's EQ keys are ones GA no longer files (ISO refuses it as filed); OI-108 is not about EQ.
    # This probe watches an ENGINE mechanism (Break inside Sum, OI-108) on a Georgia record moved to other states,
    # where Georgia's territories have no row (ISO refused that shape in OI-108's own live run): so it runs with the
    # strict SingleResult refusal OFF, explicitly. It is a diagnostic, never a rating claim.
    sub.update(to_engine(_iso.no_eq({"CommercialProperty": d["CommercialProperty"]})))
    ip = Interpreter(book_for(st, ASOF), rounding=ROUNDING, null_arithmetic=NULL_ARITHMETIC,
                     strict_single_result=False)
    data = Node.from_dict(f"MasterCF{st}", sub)
    try:
        ip.run(data)
    except InterpretError as exc:
        return f"refused ({str(exc)[:40]})"
    stack = [data]
    while stack:
        n = stack.pop()
        if n.tag == UA_PP:
            return next((c.text for c in n.children if c.tag == "TotalScheduleLimit"), "absent")
        stack.extend(n.children)
    return "no record"


def main():
    books, fam, closed = population()
    print(f"{len(fam)} family rule files (5 CW parent editions + {len(books)} state layers); "
          f"{len(closed)} closed-chunk files for comparison\n")

    sig, bad_types = signatures(fam)
    seen, _ = signatures(closed)
    seen_shapes = {(op, ty) for op, ty, _ in seen}

    print("=== Part 1: operand-type signatures ===\n")
    print(f"  unknown @Type values: {dict(bad_types) or 'none'}")
    verdicts = collections.Counter()
    flagged = []
    for (op, ty, v), where in sorted(sig.items(), key=lambda x: (-len(x[1]), x[0])):
        new = (op, ty) not in seen_shapes
        verdicts[v.split(":")[0].split(" (")[0]] += len(where)
        if not v.startswith("ok") or new:
            flagged.append((op, ty, v, new, where))
    print(f"  {sum(len(w) for w in sig.values())} operator occurrences, "
          f"{len(sig)} distinct signatures")
    for k, n in verdicts.most_common():
        print(f"    {k:10s} {n}")
    print("\n  Signatures that are not plainly ok, or new to the closed chunks:")
    for op, ty, v, new, where in flagged:
        files = sorted({re.sub(r"^.*/CommercialProperty|Rules\.Rule\.xml$", "", f) for f, _ in where})
        rules = sorted({r for _, r in where})
        print(f"    {op}{ty}  x{len(where)}  {'NEW ' if new else ''}{v}")
        print(f"        rules: {', '.join(rules[:4])}{' ...' if len(rules) > 4 else ''}")
        print(f"        files: {', '.join(files[:3])}{' ...' if len(files) > 3 else ''} ({len(files)})")

    print("\n=== Part 2: every ISO fixture carrying a chunk 12 record, rated live ===\n")
    results = run_fixtures()
    by = collections.Counter(r[3] for r in results)
    print(f"  {len(results)} fixtures: {dict(by)}")
    per_fam = collections.defaultdict(lambda: [0, 0, 0, 0])   # fixtures, records, priced, >0
    for p, st, fams, status, msg, nodes in results:
        rel = p.relative_to(ISO_CF)
        if status != "OK":
            print(f"  {status:8s} {st} {rel.name}: {msg[:300]}")
        for f in fams:
            per_fam[f][0] += 1
        for f, t, prem in nodes:
            per_fam[f][1] += 1
            if prem not in (None, ""):
                per_fam[f][2] += 1
                try:
                    if float(prem) > 0:
                        per_fam[f][3] += 1
                except ValueError:
                    pass
    print(f"\n  {'family':22s} {'fixtures':>8s} {'records':>8s} {'priced':>7s} {'> $0':>6s}")
    for f in census.FAMILIES:
        a = per_fam[f]
        print(f"  {f:22s} {a[0]:8d} {a[1]:8d} {a[2]:7d} {a[3]:6d}")

    print("\n=== Part 3: OI-108 on a real submission -- one blanket drone ===\n")
    print("  ISO fixture STC_CP000015474 (GA), its one Contents drone switched to blanket")
    print("  (BlanketLimitOfInsurance 99,000), re-rated in states on each parent edition:\n")
    for st in ("GA", "OR", "IL", "CA", "NC", "MO"):
        s, bl = probe_drone(st, False), probe_drone(st, True)
        print(f"  {st} ({books[st].parent.package.content.name:17s}) TotalScheduleLimit "
              f"scheduled {s:>6s}   blanket {bl:>6s}")

    unhandled = [x for x in flagged if x[2].startswith(("REFUSES", "WRONG"))]
    refused = [r for r in results if r[3] not in ("OK", "ISO-REFUSED")]
    print(f"\n  unhandled static shapes: {len(unhandled)}; fixtures refused: {len(refused)}")
    return 1 if unhandled or refused else 0


if __name__ == "__main__":
    raise SystemExit(main())
