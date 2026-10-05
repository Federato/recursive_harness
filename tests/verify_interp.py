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

    def __init__(self, tables=None, rounding="ROUND_HALF_UP",
                 null_arithmetic="refuse"):
        self.book = None
        self.rounding_name = rounding
        from decimal import ROUND_HALF_UP
        from gl_engine.interp.interpreter import ROUNDING_MODES
        self.rounding = ROUNDING_MODES[rounding]
        self.tracing = True
        self.trace = []
        self.messages = []
        self._guid = 0
        self._programs = {}
        self.state_program = None
        self.parent_program = None
        self._tables = tables or {}
        # Mirrors the real constructor. This class bypasses `Interpreter.
        # __init__`, so every new piece of interpreter state has to be added
        # here too -- which is exactly how it was noticed that `ip.num()` had
        # become the single door into arithmetic.
        self.null_arithmetic = null_arithmetic
        self.guard_null_premium = True
        self.null_premium = "refuse"       # the refusal is what B27/B28 test
        self.null_premiums = []
        self.product_skips_null = False    # B31 turns it on explicitly
        self.null_skips = []
        self.strict_single_result = False
        self.strict_refusals = []
        self.coercions = []

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
    # A3 used to assert the registry matched the GL census EXACTLY, which was
    # right while the engine read one line of business and became wrong the day
    # it read two. Commercial Property files five elements GL does not, and
    # they are registered here because ISO files one rule language, not one per
    # line -- see the Commercial Property section of `interp/nodes.py`.
    #
    # The assertion that still earns its place is the one that would catch a
    # typo'd or invented evaluator: an evaluator must be in the GL census OR in
    # this named list, and nothing else is allowed in. So the list is written
    # out rather than computed, and adding a sixth means saying so here.
    CF_ONLY = {"Null", "Power", "LastNonNull", "Custom", "FromList"}
    extra = [n for n in EVAL if n not in language and n not in CF_ONLY]
    check("A3 every evaluator is in the census or a declared CF extension",
          not extra, f"extra {extra}" if extra else
          f"{len(language)} GL + {len(CF_ONLY)} CF = {len(EVAL)} registered")
    absent_from_gl = sorted(CF_ONLY & set(language))
    check("A4 the CF extensions are genuinely absent from the GL corpus",
          not absent_from_gl,
          f"in the GL census after all: {absent_from_gl}" if absent_from_gl
          else "so no GL rating can reach one of them")


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

    # OI-88. ISO writes state-to-countrywide fallbacks as Round(Lookup(state))
    # then Round(Lookup('CW')), and branch one is *designed* to miss. Branch one
    # here is a Round over an absent data def, which is exactly that shape.
    v, _, ip = run('<rul:FirstNonNull Type="decimal">'
                   '<rul:Round DecimalPlaces="3">'
                   '<rul:Value Type="decimal" FromDataDef="Missing"'
                   ' AllowNullReturn="true"/></rul:Round>'
                   '<rul:Constant Type="decimal">0.85</rul:Constant>'
                   "</rul:FirstNonNull>")
    check("B6a a branch that reaches null through arithmetic is abandoned, "
          "not raised (OI-88)",
          v == Decimal("0.85"), repr(v))
    check("B6b ...and the abandonment is traced, so an absorbed null leaves "
          "evidence",
          any(t.kind == "first-non-null-branch-abandoned" for t in ip.trace),
          f"{len(ip.trace)} trace entries")

    # The load-bearing half. If this ever passes by absorbing the refusal, the
    # engine has started answering where it should stop, and OI-88's fix has
    # become the defect it was meant to close.
    try:
        run('<rul:FirstNonNull Type="decimal">'
            '<rul:Round DecimalPlaces="3">'
            '<rul:Constant Type="string">not-a-number</rul:Constant>'
            "</rul:Round>"
            '<rul:Constant Type="decimal">0.85</rul:Constant>'
            "</rul:FirstNonNull>")
        absorbed = True
    except InterpretError:
        absorbed = False
    check("B6c a branch that fails for any OTHER reason still refuses",
          not absorbed,
          "only NullInArithmetic is absorbed; a non-numeric string is not")

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

    # B23/B24 -- contract §12.3, tested by trying to break it.
    #
    # Commercial Property raised the question for real: ISO's own service rates
    # a New York risk this engine refuses, because a rule filed only in New
    # York subtracts a policy premium that is not computed until after
    # validation. One explanation was that ISO coerces null to zero in
    # arithmetic -- which would mean §12.3 is wrong for this corpus, GL
    # included. So `Interpreter(null_arithmetic="zero")` exists to MEASURE
    # that, and these two tests are the measurement.
    #
    # The idiom under test is ISO's own state-to-countrywide fallback:
    # `FirstNonNull(Round(Lookup(state)), Round(Lookup('CW')))`, where the
    # state lookup is DESIGNED to miss. Refusing lets `FirstNonNull` abandon
    # branch one and reach countrywide. Coercing turns the miss into a
    # perfectly good `0`, which `FirstNonNull` accepts -- and countrywide is
    # never read.
    FALLBACK = (
        '<rul:FirstNonNull Type="decimal">'
        '<rul:Round DecimalPlaces="3"><rul:Lookup Type="decimal"'
        ' MatrixCol="Factor" MatrixDef="RatesDef" MatrixFromConstant="Rates"'
        ' ResultMode="FirstResult"><rul:Keys>'
        '<rul:Constant Type="string">NY</rul:Constant>'
        "</rul:Keys></rul:Lookup></rul:Round>"
        '<rul:Round DecimalPlaces="3"><rul:Lookup Type="decimal"'
        ' MatrixCol="Factor" MatrixDef="RatesDef" MatrixFromConstant="Rates"'
        ' ResultMode="FirstResult"><rul:Keys>'
        '<rul:Constant Type="string">CW</rul:Constant>'
        "</rul:Keys></rul:Lookup></rul:Round>"
        "</rul:FirstNonNull>")
    rows = {"Rates": [("CW", "1.172")]}          # no NY row, by design

    v, _, _ = run(FALLBACK, ip=Fake(tables=rows))
    check("B23 refusing a null lets the countrywide fallback be reached (OI-88)",
          v == Decimal("1.172"), repr(v))

    v, _, ipz = run(FALLBACK,
                    ip=Fake(tables=rows, null_arithmetic="zero"))
    check("B24 coercing null to zero DESTROYS that fallback -- so ISO cannot "
          "be coercing", v == Decimal(0) and len(ipz.coercions) == 1,
          f"{v!r} after {len(ipz.coercions)} coercion(s); ISO returns the "
          f"countrywide factor for exactly this shape, so coercion is "
          f"disproven and §12.3 stands")

    # B25 -- the mode that survived. Propagation has to leave the fallback
    # working, or it is just `zero` with extra steps. This is the assertion
    # that lets Commercial Property run in `propagate` without anyone having to
    # take it on trust.
    v, _, ipp = run(FALLBACK,
                    ip=Fake(tables=rows, null_arithmetic="propagate"))
    check("B25 propagating a null PRESERVES the countrywide fallback",
          v == Decimal("1.172"),
          f"{v!r} after {len(ipp.coercions)} propagation(s) -- null flows, "
          f"FirstNonNull still falls through, and New York rates to ISO's "
          f"own figure")

    v, _, _ = run('<rul:GreaterThan>'
                  '<rul:Constant Type="decimal">0</rul:Constant>'
                  '<rul:Value Type="decimal" FromDataDef="Absent"'
                  ' AllowNullReturn="true"/></rul:GreaterThan>',
                  ip=Fake(null_arithmetic="propagate"))
    check("B26 a comparison against a null is false, not a refusal",
          v is False, f"{v!r} -- this is the step that lets New York's "
          f"validation rule complete instead of stopping the rating")

    # B27-B29 -- the null-premium guard, which is what `propagate` traded away
    # bought back. Nulls flow freely through intermediate arithmetic, because
    # ISO's fallback idiom needs them to; they are refused at the one boundary
    # where "absent" silently becomes "free".
    NULL_PREMIUM = ('<rul:Product ToDataDef="{to}">'
                    '<rul:Value Type="decimal" FromDataDef="MissingRate"'
                    ' AllowNullReturn="true"/>'
                    '<rul:Constant Type="decimal">1000</rul:Constant>'
                    "</rul:Product>")

    try:
        run(NULL_PREMIUM.format(to="Premium"),
            ip=Fake(null_arithmetic="propagate"))
        check("B27 a null written to Premium is refused", False,
              "it was written silently")
    except InterpretError as exc:
        check("B27 a null written to Premium is refused",
              "Premium" in str(exc) and "money" in str(exc), str(exc)[:90])

    # The hazard itself, demonstrated rather than asserted: with the guard off
    # the same program writes an empty Premium and raises nothing. `Sum` skips
    # null operands by design, so that coverage would simply never be added up.
    ip = Fake(null_arithmetic="propagate")
    ip.guard_null_premium = False
    _, root, _ = run(NULL_PREMIUM.format(to="Premium"), ip=ip)
    check("B28 ...and without the guard it is written silently -- the hazard",
          root.first("Premium") is not None
          and root.first("Premium").text in (None, ""),
          f"Premium = {root.first('Premium').text!r}, no error raised")

    # OI-109: in "zero" mode (Property's default under `propagate`) the same
    # program writes 0, as ISO does, and the zeroing is recorded, not silent.
    ip = Fake(null_arithmetic="propagate")
    ip.null_premium = "zero"
    _, root, ip = run(NULL_PREMIUM.format(to="Premium"), ip=ip)
    check("B30 zero mode writes 0 and records it (OI-109)",
          root.first("Premium") is not None
          and root.first("Premium").text == "0"
          and ip.null_premiums == ["Premium"]
          and any(t.kind == "null-premium-zeroed" for t in ip.trace),
          f"Premium = {root.first('Premium').text!r}, recorded {ip.null_premiums}")

    # OI-110: ISO skips a null operand in Product. 0.5 x <null> = 0.5, not null.
    ip = Fake(null_arithmetic="propagate")
    ip.product_skips_null = True
    got, _, ip = run('<rul:Product><rul:Constant Type="decimal">0.5</rul:Constant>'
                     '<rul:Value Type="decimal" FromDataDef="Missing"/></rul:Product>', ip=ip)
    check("B31 Product skips a null operand and records it (OI-110)",
          str(got) == "0.5" and len(ip.null_skips) == 1
          and any(t.kind == "product-null-skipped" for t in ip.trace),
          f"got {got!r}, skipped {ip.null_skips}")

    # OI-115: ISO skips a single null operand of Subtract and keeps the other
    # as it is. <null> - 1000 = 1000 (not -1000); 1065 - <null> = 1065.
    ip = Fake(null_arithmetic="propagate")
    ip.product_skips_null = True
    got, _, ip = run('<rul:Subtract><rul:Value Type="decimal" FromDataDef="Missing"/>'
                     '<rul:Constant Type="decimal">1000</rul:Constant></rul:Subtract>', ip=ip)
    check("B32 Subtract skips a null FIRST operand, keeps the other un-negated (OI-115)",
          str(got) == "1000" and len(ip.null_skips) == 1
          and any(t.kind == "subtract-null-skipped" for t in ip.trace),
          f"got {got!r}, skipped {ip.null_skips}")
    ip = Fake(null_arithmetic="propagate")
    ip.product_skips_null = True
    got, _, ip = run('<rul:Subtract><rul:Constant Type="decimal">1065</rul:Constant>'
                     '<rul:Value Type="decimal" FromDataDef="Missing"/></rul:Subtract>', ip=ip)
    check("B33 Subtract skips a null SECOND operand (OI-115)",
          str(got) == "1065" and len(ip.null_skips) == 1, f"got {got!r}")
    # With the flag off (General Liability) nothing changes: the null still
    # reaches arithmetic and propagates or refuses as before.
    ip = Fake(null_arithmetic="propagate")
    try:
        got, _, ip = run('<rul:Subtract><rul:Value Type="decimal" FromDataDef="Missing"/>'
                         '<rul:Constant Type="decimal">1000</rul:Constant></rul:Subtract>', ip=ip)
        off_ok = got is None and not ip.null_skips
    except Exception:
        off_ok = not ip.null_skips
    check("B34 Subtract is unchanged with the skip flag off (GL)", off_ok, "no skip recorded")

    # OI-126 (chunk 28 C28-07): a filed empty Constant ends a FirstNonNull with
    # "" in Property; GL still skips it and exhausts to null.
    FNN_EMPTY = ('<rul:FirstNonNull Type="string"><rul:Value Type="string" FromDataDef="Missing"/>'
                 '<rul:Constant Type="string"></rul:Constant></rul:FirstNonNull>')
    ip = Fake(null_arithmetic="propagate")
    ip.product_skips_null = True
    got_cf, _, _ = run(FNN_EMPTY, ip=ip)
    got_gl, _, _ = run(FNN_EMPTY, ip=Fake(null_arithmetic="propagate"))
    check("B35 FirstNonNull returns a filed empty Constant in Property, null in GL (OI-126)",
          got_cf == "" and got_gl is None, f"Property {got_cf!r}, GL {got_gl!r}")

    # OI-123 (chunk 28 C28-07): an Exist / NotExist with no path selects
    # nothing in Property (Exist false, NotExist true); GL selects the node.
    ip = Fake(null_arithmetic="propagate")
    ip.product_skips_null = True
    ex_cf, _, _ = run("<rul:Exist/>", ip=ip)
    nx_cf, _, _ = run("<rul:NotExist/>", ip=ip)
    ex_gl, _, _ = run("<rul:Exist/>", ip=Fake(null_arithmetic="propagate"))
    check("B36 an Exist / NotExist with no path selects nothing in Property, the node in GL (OI-123)",
          ex_cf is False and nx_cf is True and ex_gl is True,
          f"Property Exist {ex_cf} NotExist {nx_cf}; GL Exist {ex_gl}")

    # OI-114 (chunk 28 C28-10): a <rul:Null/> operand of And / Or is false in
    # Property; GL still refuses a condition that is neither true nor false.
    AND_NULL = '<rul:And><rul:Null/><rul:Constant Type="boolean">true</rul:Constant></rul:And>'
    OR_NULL = '<rul:Or><rul:Null/><rul:Constant Type="boolean">true</rul:Constant></rul:Or>'
    ip = Fake(null_arithmetic="propagate")
    ip.product_skips_null = True
    and_cf, _, _ = run(AND_NULL, ip=ip)
    or_cf, _, _ = run(OR_NULL, ip=ip)
    try:
        run(AND_NULL, ip=Fake(null_arithmetic="propagate"))
        gl_refuses = False
    except InterpretError:
        gl_refuses = True
    check("B37 a Null operand of And / Or is false in Property; GL refuses it (OI-114)",
          and_cf is False and or_cf is True and gl_refuses,
          f"Property And {and_cf} Or {or_cf}; GL refuses {gl_refuses}")

    # The substring trap: `PremiumIndicator` is a 0/1 flag, not money, and
    # guarding it by name-contains would refuse ordinary content.
    _, root, _ = run(NULL_PREMIUM.format(to="PremiumIndicator"),
                     ip=Fake(null_arithmetic="propagate"))
    check("B29 PremiumIndicator is NOT guarded -- it is a flag, not money",
          root.first("PremiumIndicator") is not None,
          "guarding on a substring would have refused this")

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
    # E5 originally asserted that the run STOPPED on a named contract clause,
    # because at stage 2 the submission tree was not yet built and completing
    # would have meant inventing values. It was written to fail the moment
    # completion became meaningful, and stage 3 made it so -- the submission
    # mapper, positional predicates and rule-file inheritance between them
    # carry Alaska all the way through. The assertion is inverted rather than
    # deleted, so the transition is on the record.
    check("E5 completes now that stage 3 builds the tree (was: stops)",
          stopped is None,
          f"stopped on {stopped.clause}: {stopped}" if stopped
          else f"{kinds.get('call', 0)} calls, no refusal")


def group_f() -> None:
    """Banded and interpolated lookups, against real ISO tables.

    The whole population is 11 table names, every one reachable, each with
    exactly one key range and two boundary types
    (`scripts/erc/46_banded_lookups.py`). Two are interpolated, both
    size-of-risk relativity, both Linear.
    """
    print("\nF  BANDED LOOKUPS -- boundaries and interpolation")
    from decimal import Decimal
    book = ResolvedBook(EditionResolver().resolve("OK", "20260801"))
    ip = Interpreter(book)

    def look(name, col, keys):
        return ip.lookup(name, col, keys, "FirstResult", "decimal", "test")

    # CredibilityFactor is FromInclusiveToExclusive: [0,10879) -> 0,
    # [10879,15388) -> 0.03. The boundary is the whole point -- a stepped or
    # off-by-one reading lands in the wrong band and the factor is silently
    # wrong.
    check("F1 a value below the boundary stays in the lower band",
          look("CredibilityFactor", "Factor", ["CW", Decimal(10878)])
          == Decimal("0"), "10878 -> 0")
    check("F2 the boundary itself belongs to the UPPER band (FromInclusive)",
          look("CredibilityFactor", "Factor", ["CW", Decimal(10879)])
          == Decimal("0.03"), "10879 -> 0.03")
    check("F3 a value outside every band returns null, not the nearest",
          look("CredibilityFactor", "Factor", ["CW", Decimal(-1)]) is None,
          "-1 -> null")

    # PremOpsSizeOfRiskRelativity interpolates Relativity linearly along the
    # exposure band. Take a band whose endpoints differ, so a stepped reading
    # would be visibly wrong.
    t = book.table("PremOpsSizeOfRiskRelativity")
    band = next((r for r in t.rows if r[0] == "CW" and r[4] != r[5]), None)
    if band is None:
        check("F4 an interpolated band exists to test", False, "none found")
        return
    lo, hi, v_lo, v_hi = band[2], band[3], band[4], band[5]
    at_lo = look("PremOpsSizeOfRiskRelativity", "Relativity",
                 ["CW", band[1], lo])
    mid_x = lo + (hi - lo) / 2
    at_mid = look("PremOpsSizeOfRiskRelativity", "Relativity",
                  ["CW", band[1], mid_x])
    check("F4 at the band's lower bound, the value is the band's lower value",
          at_lo == v_lo, f"{at_lo}")
    check("F5 midway along the band, the value is midway between the bounds",
          at_mid == v_lo + (v_hi - v_lo) / 2,
          f"{at_mid} between {v_lo} and {v_hi}")
    check("F6 interpolation is traced, so a factor can be re-derived",
          any(t2.kind == "lookup-interpolated" for t2 in ip.trace),
          f"{sum(1 for t2 in ip.trace if t2.kind == 'lookup-interpolated')} traced")


def main() -> int:
    print(f"Stage 2 acceptance -- the interpreter   (as of {ASOF})")
    group_a()
    group_b()
    group_c()
    group_d()
    group_e()
    group_f()
    total = len(PASS) + len(FAIL)
    print(f"\n{len(PASS)}/{total} passed")
    if FAIL:
        print("\nFAILURES:")
        for f in FAIL:
            print(f"  {f}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
