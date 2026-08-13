"""Stage 2 acceptance: the interpreter.

Four groups, in the order they matter.

  A  coverage   every one of the 54 language nodes has an evaluator, and the
                list of 54 is read from the corpus census rather than typed here
  B  semantics  each node group against small hand-built programs, checking the
                contract clause rather than the happy path
  C  the real   the `Default` block of a real ISO package, executed. This is the
     thing      finding of contract section 2 turned into a test: an interpreter
                entered at `ErcProcess` would skip everything asserted here
  D  refusals   every hard failure in contract section 12 actually fires

Run: python tests/verify_interp.py
"""
from __future__ import annotations

import csv
import datetime as dt
import sys
import xml.etree.ElementTree as ET
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from gl_engine import EditionResolver, ResolvedBook            # noqa: E402
from gl_engine.interp import Interpreter, Node                 # noqa: E402
from gl_engine.interp.nodes import EVAL                        # noqa: E402
from gl_engine.interp.values import InterpretError             # noqa: E402
from gl_engine.interp import tree                              # noqa: E402

CENSUS = ROOT / "scripts" / "erc" / "out" / "node_surface.csv"
ASOF = "20260811"

PASS, FAIL = [], []


def check(name: str, cond: bool, detail: str = "") -> None:
    (PASS if cond else FAIL).append(f"{name}  {detail}".rstrip())
    print(f"  {'PASS' if cond else 'FAIL'}  {name}"
          + (f"  [{detail}]" if detail else ""))


def prog(xml: str):
    """Parse a rule fragment written in the corpus's own namespace."""
    return ET.fromstring(
        '<rul:Wrap xmlns:rul="http://www.verisk.com/iso/erc/Rule">'
        + xml + "</rul:Wrap>")[0]


class Fake(Interpreter):
    """An interpreter with no corpus behind it, for evaluating fragments."""

    def __init__(self, tables=None, rounding="ROUND_HALF_UP"):
        self.book = None
        self.rounding_name = rounding
        from decimal import ROUND_HALF_UP
        from gl_engine.interp.interpreter import ROUNDING_MODES
        self.rounding = ROUNDING_MODES[rounding]
        self.tracing = True
        self.trace = []
        self._guid = 0
        self._programs = {}
        self.state_program = None
        self.parent_program = None
        self._tables = tables or {}

    def lookup(self, name, col, keys, mode, typ, where):
        rows = self._tables.get(name)
        if rows is None:
            raise InterpretError(f"no table {name!r}", "§7", where)
        from gl_engine.interp.values import coerce, compare_key
        hits = [r for r in rows
                if [compare_key(x) for x in r[:len(keys)]]
                == [compare_key(k) for k in keys]]
        if not hits:
            return None
        if mode == "SingleResult" and len(hits) > 1:
            raise InterpretError("SingleResult matched more than one row",
                                 "§7", where)
        return coerce(hits[0][-1], typ, where)


def run(xml: str, data=None, ip=None):
    from gl_engine.interp.interpreter import Frame
    ip = ip or Fake()
    node = data if isinstance(data, Node) else Node.from_dict("Root", data or {})
    return ip.eval(prog(xml), Frame(node, None, "test")), node, ip


# ------------------------------------------------------------------ A coverage

def group_a() -> None:
    print("\nA  COVERAGE -- every language node has an evaluator")
    if not CENSUS.exists():
        check("A1 census present", False,
              "run scripts/erc/42_node_surface.py first")
        return
    csv.field_size_limit(1 << 24)
    language = sorted(r["node"] for r in
                      csv.DictReader(open(CENSUS, encoding="utf-8"))
                      if r["kind"] == "executable")
    check("A1 census read from source", len(language) == 54,
          f"{len(language)} language nodes")
    missing = [n for n in language if n not in EVAL]
    check("A2 every node has an evaluator", not missing,
          f"{len(language) - len(missing)} of {len(language)}"
          + (f"; missing {missing}" if missing else ""))
    extra = [n for n in EVAL if n not in language]
    check("A3 no evaluator for a node the corpus does not have", not extra,
          f"extra {extra}" if extra else "")


# ----------------------------------------------------------------- B semantics

def group_b() -> None:
    print("\nB  SEMANTICS -- the contract clause, not the happy path")

    v, _, _ = run('<rul:Constant Type="decimal">1.05</rul:Constant>')
    check("B1 Constant is Decimal, never float",
          isinstance(v, Decimal) and v == Decimal("1.05"), repr(v))

    v, _, _ = run('<rul:Constant Type="string"></rul:Constant>')
    check("B2 empty Constant is the empty string, not null (Q1)",
          v == "" and v is not None, repr(v))

    v, _, _ = run('<rul:FirstValue Type="decimal" FromConstant="7"'
                  ' FromDataDef="Missing" Order="DataDefInputParamConstant"/>')
    check("B3 FirstValue falls through to the constant (C2)",
          v == Decimal(7), repr(v))

    v, _, _ = run('<rul:FirstValue Type="decimal" FromConstant="7"'
                  ' FromDataDef="Rate" Order="DataDefInputParamConstant"/>',
                  {"Rate": "2.5"})
    check("B4 FirstValue prefers the DataDef", v == Decimal("2.5"), repr(v))

    v, _, ip = run("<rul:FirstNonNull Type=\"string\">"
                   '<rul:Value Type="string" FromDataDef="A"'
                   ' AllowNullReturn="true"/>'
                   '<rul:Value Type="string" FromDataDef="B"'
                   ' AllowNullReturn="true"/></rul:FirstNonNull>')
    check("B5 FirstNonNull exhausts to null and is traced (C6)",
          v is None and any(t.kind == "first-non-null-exhausted"
                            for t in ip.trace), repr(v))

    v, _, _ = run('<rul:FirstNonNull Type="string">'
                  '<rul:Value Type="string" FromDataDef="A"'
                  ' AllowNullReturn="true"/>'
                  '<rul:Constant Type="string">fallback</rul:Constant>'
                  "</rul:FirstNonNull>")
    check("B6 FirstNonNull takes the total fallback", v == "fallback", repr(v))

    v, _, _ = run("<rul:If><rul:Test>"
                  "<rul:Equal><rul:Constant Type=\"integer\">1</rul:Constant>"
                  '<rul:Constant Type="integer">2</rul:Constant></rul:Equal>'
                  "</rul:Test><rul:Then>"
                  '<rul:Constant Type="decimal">9</rul:Constant>'
                  "</rul:Then></rul:If>")
    check("B7 If with no Else yields null, not zero (§5)", v is None, repr(v))

    v, _, _ = run("<rul:And>"
                  '<rul:Constant Type="string">x</rul:Constant>'
                  "</rul:And>") if False else (None, None, None)
    v, _, _ = run("<rul:Choose><rul:When><rul:Test>"
                  '<rul:Equal><rul:Constant Type="integer">1</rul:Constant>'
                  '<rul:Constant Type="integer">1</rul:Constant></rul:Equal>'
                  '</rul:Test><rul:Then><rul:Constant Type="string">hit'
                  "</rul:Constant></rul:Then></rul:When><rul:Otherwise>"
                  '<rul:Constant Type="string">miss</rul:Constant>'
                  "</rul:Otherwise></rul:Choose>")
    check("B8 Choose takes the first matching When", v == "hit", repr(v))

    v, _, _ = run('<rul:Product DecimalPlaces="3">'
                  '<rul:Constant Type="decimal">1.23456</rul:Constant>'
                  '<rul:Constant Type="decimal">2</rul:Constant>'
                  "</rul:Product>")
    check("B9 Product rounds to @DecimalPlaces", v == Decimal("2.469"), repr(v))

    v, _, ip = run('<rul:Round DecimalPlaces="2">'
                   '<rul:Constant Type="decimal">2.345</rul:Constant>'
                   "</rul:Round>")
    check("B10 rounding is half-up by default and traced (C10)",
          v == Decimal("2.35") and any(t.kind == "round" for t in ip.trace),
          repr(v))

    ip = Fake(rounding="ROUND_HALF_EVEN")
    v, _, _ = run('<rul:Round DecimalPlaces="2">'
                  '<rul:Constant Type="decimal">2.345</rul:Constant>'
                  "</rul:Round>", ip=ip)
    check("B11 rounding mode is one engine-wide setting",
          v == Decimal("2.34"), repr(v))

    v, root, _ = run('<rul:DateAdd ToDataDef="ExpDate" UnitType="Years">'
                     '<rul:Value Type="dateTime" FromDataDef="EffDate"/>'
                     '<rul:Constant Type="integer">1</rul:Constant>'
                     "</rul:DateAdd>", {"EffDate": "06/01/2026"})
    check("B12 DateAdd writes ExpDate = EffDate + 1 year (§2)",
          v == dt.date(2027, 6, 1) and tree.read("ExpDate", root) == "06/01/2027",
          str(v))

    v, root, _ = run('<rul:ForEach AtDataDef="T/Row">'
                     '<rul:Constant Type="string" ToDataDef="Seen">y'
                     "</rul:Constant></rul:ForEach>", {"T": {"Row": []}})
    check("B13 ForEach over an empty path runs zero times (§9)",
          tree.read("Seen", root) is None, "no writes")

    _, root, _ = run('<rul:ForEach AtDataDef="T/Row">'
                     '<rul:Sequence>'
                     '<rul:Constant Type="string" ToDataDef="Mark">x</rul:Constant>'
                     "<rul:Break/></rul:Sequence></rul:ForEach>",
                     {"T": {"Row": [{"n": 1}, {"n": 2}, {"n": 3}]}})
    marked = [n for n in tree.select("T/Row", root) if n.first("Mark")]
    check("B14 Break stops the enclosing ForEach (C12)",
          len(marked) == 1, f"{len(marked)} of 3 rows marked")

    v, _, _ = run('<rul:WithArgs>'
                  '<rul:Arg Type="decimal" Param="P">'
                  '<rul:Constant Type="decimal">3</rul:Constant></rul:Arg>'
                  '<rul:Value Type="decimal" FromParam="P"/></rul:WithArgs>')
    check("B15 WithArgs binds a parameter Value can read (C13)",
          v == Decimal(3), repr(v))

    v, _, _ = run('<rul:Value Type="decimal" FromDataDef="A/B/C"/>',
                  {"A": {"B": {"C": "4.5"}}})
    check("B16 nested path reads", v == Decimal("4.5"), repr(v))

    # B16b is the corrected clause. 75.30% of declared elements are nillable
    # and no read in the corpus targets a non-nillable one, so a bare read of
    # an absent element is ISO's normal case, not an error.
    v, _, _ = run('<rul:Value Type="dateTime" FromDataDef="TRIAExpirationDate"/>')
    check("B16b a bare Value on an absent element returns null, not an error",
          v is None, repr(v))

    root = Node.from_dict("Root", {"L": {"M": {"N": {"x": "1"}}}, "Top": "hit"})
    deep = tree.select_one("L/M/N", root)
    check("B17 ../../.. reaches across the tree (E18)",
          tree.read("../../../Top", deep) == "hit",
          tree.read("../../../Top", deep))

    ip = Fake(tables={"Rates": [("CW", "A", "1.75")]})
    v, _, _ = run('<rul:Lookup Type="decimal" MatrixCol="Factor"'
                  ' MatrixDef="RatesDef" MatrixFromConstant="Rates"'
                  ' ResultMode="FirstResult"><rul:Keys>'
                  '<rul:Constant Type="string">CW</rul:Constant>'
                  '<rul:Constant Type="string">A</rul:Constant>'
                  "</rul:Keys></rul:Lookup>", ip=ip)
    check("B18 Lookup matches keys in order", v == Decimal("1.75"), repr(v))

    v, _, _ = run('<rul:Lookup Type="decimal" MatrixCol="Factor"'
                  ' MatrixDef="RatesDef" MatrixFromConstant="Rates"'
                  ' ResultMode="FirstResult"><rul:Keys>'
                  '<rul:Constant Type="string">ZZ</rul:Constant>'
                  '<rul:Constant Type="string">A</rul:Constant>'
                  "</rul:Keys></rul:Lookup>", ip=Fake(tables={"Rates": []}))
    check("B19 a Lookup that matches nothing returns null", v is None, repr(v))

    _, root, _ = run('<rul:Locate AtOutputDataDef="Policy" OutputAction="Append">'
                     "<rul:Sequence/></rul:Locate>")
    check("B20 Locate Append creates the node (§9)",
          root.first("Policy") is not None, tree.dump(root).replace("\n", " | "))

    _, root, _ = run('<rul:Remove AtDataDef="T/Row"/>',
                     {"T": {"Row": [{"n": 1}, {"n": 2}]}})
    check("B21 Remove is all-matching (C5)",
          not tree.select("T/Row", root), "0 rows left")

    v, _, _ = run("<rul:Sum>"
                  '<rul:Constant Type="decimal">1.1</rul:Constant>'
                  '<rul:Constant Type="decimal">2.2</rul:Constant></rul:Sum>')
    check("B22 Sum is exact in Decimal (N10)", v == Decimal("3.3"), repr(v))

    v, _, ip = run('<rul:Guid ToDataDef="Id"/>')
    v2, _, _ = run('<rul:Guid ToDataDef="Id"/>', ip=ip)
    check("B23 Guid is seeded and reproducible, not random (§9)",
          v != v2 and v.endswith("-000000000000"), f"{v} then {v2}")


# ------------------------------------------------------------------- C the real

def group_c() -> None:
    print("\nC  A REAL ISO PACKAGE -- the Default block executed")
    try:
        book = ResolvedBook(EditionResolver().resolve("CW", ASOF))
    except Exception as exc:                       # pragma: no cover
        check("C0 corpus reachable", False, str(exc))
        return

    ip = Interpreter(book)
    data = Node.from_dict("GeneralLiabilityRequest", {"EffDate": "06/01/2026"})
    try:
        ip.run(data)
    except Exception as exc:
        check("C1 Default block executes", False, f"{type(exc).__name__}: {exc}")
        print(tree.dump(data))
        return

    check("C1 Default block executes", True, f"{len(ip.trace)} trace entries")
    check("C2 Renewal seeded to 0", tree.read("Renewal", data) == "0",
          repr(tree.read("Renewal", data)))
    check("C3 State/Code seeded", tree.read("State/Code", data) == "CW",
          repr(tree.read("State/Code", data)))
    check("C4 State/Name seeded",
          tree.read("State/Name", data) == "Countrywide",
          repr(tree.read("State/Name", data)))
    check("C5 ExpDate computed as EffDate + 1 year -- THE FINDING",
          tree.read("ExpDate", data) == "06/01/2027",
          repr(tree.read("ExpDate", data)))
    check("C6 Policy node appended", data.first("Policy") is not None,
          "present" if data.first("Policy") is not None else "absent")
    check("C7 no rules ran -- no GeneralLiability rows supplied",
          not any(t.kind == "call" for t in ip.trace),
          f"{sum(1 for t in ip.trace if t.kind == 'call')} calls")

    # The entry point is not ErcProcess: prove ErcProcess alone omits all of it.
    entry = ip.state_program.entry()
    calls = [(c.attrib.get("Rule")) for c in entry.iter()
             if c.tag.endswith("RunRule")]
    check("C8 Default calls Initialize, ErcProcess, then the total (§2)",
          calls == ["InitializeRuleSet", "ErcProcess",
                    "ErcCalculateTotalPremium"], str(calls))

    # C9 and C10 exist because C1-C8 all passed on their first run, and the
    # standing rule here is to suspect a check that has never failed.

    # C9 is the counterfactual, measured rather than asserted: if any RULE
    # wrote ExpDate, an interpreter entered at ErcProcess could still have
    # produced it and contract section 2 would be a smaller finding than
    # claimed. Nothing does. The Default block is the only source in the
    # package, so entering at ErcProcess cannot produce an expiry date.
    writers = []
    for f in sorted((book.resolution.state.content / "Rules")
                    .glob("*.Rule.xml")):
        root = ET.fromstring(f.read_text(encoding="utf-8-sig"))
        for rule in root:
            if not rule.tag.endswith("}Rule"):
                continue
            for el in rule.iter():
                if el.attrib.get("ToDataDef") == "ExpDate":
                    writers.append((f.name, rule.attrib.get("Name")))
    check("C9 no rule writes ExpDate -- only Default does (§2)",
          not writers, f"{len(writers)} rule writers found")

    # C10 proves C5 is not vacuous: remove the input it depends on and the
    # engine must refuse rather than quietly leave ExpDate unset.
    bare = Node.from_dict("GeneralLiabilityRequest", {})
    try:
        Interpreter(book, trace=False).run(bare)
        check("C10 a missing EffDate is refused, not skipped", False,
              "ran to completion with no EffDate")
    except InterpretError as exc:
        check("C10 a missing EffDate is refused, not skipped",
              tree.read("ExpDate", bare) is None, exc.clause or "?")


# ------------------------------------------------------------------ D refusals

def group_d() -> None:
    print("\nD  REFUSALS -- every hard failure in section 12 fires")

    def refuses(label, xml, data=None, clause=""):
        try:
            run(xml, data)
        except InterpretError as exc:
            check(label, clause in (exc.clause or ""), exc.clause or "?")
            return
        except Exception as exc:                   # pragma: no cover
            check(label, False, f"wrong error {type(exc).__name__}: {exc}")
            return
        check(label, False, "did not raise")

    refuses("D1 unknown node type", "<rul:Frobnicate/>", clause="§12.1")
    refuses("D2 RunRule ClearCache=false",
            '<rul:RunRule Type="none" FileName="F" Rule="R"'
            ' ClearCache="false"/>', clause="§12.2")
    refuses("D3 FirstValue FromParam (never filed)",
            '<rul:FirstValue Type="decimal" FromConstant="0"'
            ' FromDataDef="X" FromParam="P"/>', clause="§12.2")
    refuses("D4 null reaching arithmetic",
            "<rul:Subtract>"
            '<rul:Value Type="decimal" FromDataDef="Nope" AllowNullReturn="true"/>'
            '<rul:Constant Type="decimal">1</rul:Constant></rul:Subtract>',
            clause="§12.3")
    refuses("D5 division by zero",
            "<rul:Divide>"
            '<rul:Constant Type="decimal">1</rul:Constant>'
            '<rul:Constant Type="decimal">0</rul:Constant></rul:Divide>',
            clause="§12.5")
    refuses("D6 a sixth @Type",
            '<rul:Constant Type="binary">x</rul:Constant>', clause="§12.2")
    refuses("D7 Value with neither @FromDataDef nor @FromParam",
            '<rul:Value Type="decimal"/>', clause="§4")
    refuses("D8 a condition that is not a boolean",
            "<rul:If><rul:Test>"
            '<rul:Constant Type="integer">1</rul:Constant></rul:Test>'
            '<rul:Then><rul:Constant Type="integer">2</rul:Constant>'
            "</rul:Then></rul:If>", clause="§5")

    ip = Fake(tables={"Dup": [("A", "1"), ("A", "2")]})
    try:
        run('<rul:Lookup Type="decimal" MatrixCol="V" MatrixDef="DupDef"'
            ' MatrixFromConstant="Dup" ResultMode="SingleResult"><rul:Keys>'
            '<rul:Constant Type="string">A</rul:Constant>'
            "</rul:Keys></rul:Lookup>", ip=ip)
        check("D9 SingleResult matching two rows", False, "did not raise")
    except InterpretError as exc:
        check("D9 SingleResult matching two rows", True, exc.clause)

    # A package with no Default must fail rather than fall back to ErcProcess.
    from gl_engine.interp.program import Program
    try:
        book = ResolvedBook(EditionResolver().resolve("CW", ASOF))
        p = Program(book.resolution.state)
        rf = p.file("GeneralLiabilityRules")
        check("D10 a rule file without Default has none", rf.default is None,
              "as expected")
    except Exception as exc:                       # pragma: no cover
        check("D10 a rule file without Default has none", False, str(exc))


def group_e() -> None:
    """Depth on a real ISO payload.

    Stage 2 is the interpreter, not the kernel: mapping a submission onto the
    ERC data tree is stage 4 and orchestrating a rating is stage 3. So this
    group does not assert a premium. It asserts that the interpreter executes
    ISO's real rules at depth -- cross-package dispatch, real table lookups,
    the state-then-countrywide idiom -- against a genuine RAaS input.

    The thresholds are deliberately loose. They exist to catch a regression that
    stops execution early, not to pin a number that will move as stages 3 and 4
    fill the tree in.
    """
    print("\nE  DEPTH ON A REAL ISO PAYLOAD (stage 2 scope: executes, does not rate)")
    payload = ROOT / "Payloads" / "AK" / "1. Input.json"
    if not payload.exists():
        check("E0 payload present", False, str(payload))
        return
    import json
    p = json.loads(payload.read_text(encoding="utf-8-sig"))

    book = ResolvedBook(EditionResolver().resolve("AK", ASOF))
    ip = Interpreter(book)
    data = Node.from_dict("GeneralLiabilityRequest", {
        "EffDate": p["body"]["SchemeKeys"]["EffectiveDateTime"][:10],
        "GeneralLiabilityTable": {
            "GeneralLiability": p["body"]["GeneralLiability"]},
    })
    stopped = None
    try:
        ip.run(data)
    except InterpretError as exc:
        stopped = exc

    kinds = {}
    for t in ip.trace:
        kinds[t.kind] = kinds.get(t.kind, 0) + 1

    check("E1 executes ISO's real rules at depth",
          kinds.get("call", 0) >= 200, f"{kinds.get('call', 0)} rule calls")
    check("E2 real table lookups succeed",
          kinds.get("lookup", 0) >= 5, f"{kinds.get('lookup', 0)} hits, "
          f"{kinds.get('lookup-miss', 0)} misses")
    check("E3 cross-package dispatch reaches the countrywide parent (N2)",
          any(t.source == book.resolution.parent.pkg_id for t in ip.trace),
          book.resolution.parent.pkg_id)
    check("E4 writes land on the tree", kinds.get("write", 0) >= 50,
          f"{kinds.get('write', 0)} writes")
    # Stopping here is correct and expected: the submission tree is not yet
    # built by stage 4, so a required value is genuinely absent. What matters
    # is that it stops on a NAMED contract clause rather than inventing a
    # number -- a silent zero here is the failure this engine exists to refuse.
    check("E5 stops on a named contract clause, never on a guess",
          stopped is not None and bool(stopped.clause),
          f"{stopped.clause} ({stopped})" if stopped
          else "ran to completion -- update this test")


def main() -> int:
    print(f"Stage 2 acceptance -- the interpreter   (as of {ASOF})")
    group_a()
    group_b()
    group_c()
    group_d()
    group_e()
    total = len(PASS) + len(FAIL)
    print(f"\n{len(PASS)}/{total} passed")
    if FAIL:
        print("\nFAILURES:")
        for f in FAIL:
            print(f"  {f}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
