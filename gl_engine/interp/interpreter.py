"""The interpreter: frames, dispatch, lookup, rounding and the trace.

This is the driver the evaluators in `nodes.py` hang off. Four things in it are
load-bearing and each is a contract clause rather than a design preference.

**Execution starts at the `Default` block (§2), never at `ErcProcess`.**

**Parent dispatch does not re-parent (§8, N2).** A `RunRule` carrying
`@ProjectName` runs in the countrywide package, and everything it calls resolves
*there*. 4,598 rules in this corpus are "do what the parent does, then this"; if
a parent-scope call re-enters the state override, they recurse forever. The
current package is a property of the frame, and a parent-directed call cannot be
re-parented.

**Nothing is memoised (§8, C3).** `@ClearCache` is `true` on all 173,204
occurrences. Rules write to a shared tree, so a cached call is sound only if
nothing it touched has changed, and ISO evidently does not want that assumed.

**Rounding mode is one engine-wide setting, recorded on every rounded value
(§6, C10, OI-70).** ISO never declares half-up, half-even or truncate anywhere,
and the three differ on exactly the half-cent a rating engine meets constantly.
It is the first thing the Phase 2 RAaS comparison should be pointed at.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP, ROUND_HALF_EVEN, ROUND_DOWN

from ..domain import Citation
from ..erc.tables import Shape, Table
from . import nodes, tree
from .program import Program
from .tree import Node
from .values import InterpretError, coerce, compare_key, to_decimal

#: Contract C10. Named so a caller can change it explicitly and the trace says
#: which was used -- it is never picked per node.
ROUNDING_MODES = {"ROUND_HALF_UP": ROUND_HALF_UP,
                  "ROUND_HALF_EVEN": ROUND_HALF_EVEN,
                  "ROUND_DOWN": ROUND_DOWN}

#: The categories a `Lookup` may name, searched in this order. `FormPage` is
#: last but is the most common target in practice (`Pages`, 45,388 of 54,716
#: lookups); Rate and Domain are searched first because a name collision there
#: would be a rating table and must win.
LOOKUP_KINDS = ("Rate", "Domain", "FormPage")

#: A rating that recurses deeper than this is the engine being wrong, not the
#: content: the corpus's own call graph is acyclic (0 back-edges, measured).
MAX_DEPTH = 200


@dataclass
class Frame:
    """One evaluation context: where in the data, which package, which params."""

    data: Node
    program: Program
    rule_file: str
    parent_scope: bool = False            # inside a @ProjectName call (N2)
    params: dict = field(default_factory=dict)
    depth: int = 0

    def at(self, node: Node) -> "Frame":
        return Frame(node, self.program, self.rule_file, self.parent_scope,
                     self.params, self.depth)

    def with_params(self, bindings: dict) -> "Frame":
        if not bindings:
            return self
        merged = dict(self.params)
        merged.update(bindings)
        return Frame(self.data, self.program, self.rule_file,
                     self.parent_scope, merged, self.depth)

    def in_rule(self, program: Program, rule_file: str, params: dict,
                parent_scope: bool) -> "Frame":
        return Frame(self.data, program, rule_file, parent_scope, params,
                     self.depth + 1)

    def has_param(self, name: str) -> bool:
        return name in self.params

    def param(self, name: str):
        return self.params[name]


def _message_helper(ip, rule_name: str, args: dict, frame, where: str):
    """`MessageHelper` -- the one rule file ISO does not ship.

    **The corpus is not self-contained, and this is the proof.** `MessageHelper`
    is called 4,347 times, always as `AddErrorMessage`, and exists in no package
    anywhere. ISO's rating service provides it: the messages it collects are the
    `RatingMessages` object in a RAaS response.

    So the engine provides it too, rather than treating a validation message as
    a missing file. Getting this wrong is not cosmetic -- it stopped 32 of the
    50 payloads we hold, because a real submission routinely trips at least one
    of ISO's own validation rules.
    """
    if rule_name != "AddErrorMessage":
        raise InterpretError(
            f"MessageHelper.{rule_name} is not provided; only AddErrorMessage "
            f"is called in the corpus, 4,347 times", "§8", where)
    text = args.get("Message")
    ip.messages.append(str(text) if text is not None else "")
    ip.note("message", str(text)[:160], "MessageHelper")
    return None


#: Rule files the host engine provides rather than ISO filing them.
_BUILTINS = {"MessageHelper": _message_helper}


@dataclass
class TraceEntry:
    """One recorded step. `detail` reads; `data` is for machines.

    The detail string was the only thing here until stage 6 asked to render
    factors on a screen and could not, because a sentence like
    `PremOpsLossCost[Rate] keys=['OK','501','50017'] -> 0.095` has to be
    re-parsed to be used. **A trace that can only be read is half a trace** --
    the Phase 2 diff and the Phase 3 harness both need the parts, not the
    prose. `data` carries them; `detail` stays exactly as it was.
    """

    kind: str
    detail: str
    source: str = ""
    data: dict = field(default_factory=dict)

    def __str__(self) -> str:              # pragma: no cover - display only
        tail = f"  <{self.source}>" if self.source else ""
        return f"{self.kind}: {self.detail}{tail}"


class Interpreter:
    """Executes one resolved rulebook against one data tree."""

    def __init__(self, book, rounding: str = "ROUND_HALF_UP",
                 trace: bool = True):
        if rounding not in ROUNDING_MODES:
            raise InterpretError(
                f"unknown rounding mode {rounding!r}", "§6", "")
        self.book = book
        self.rounding_name = rounding
        self.rounding = ROUNDING_MODES[rounding]
        self.tracing = trace
        self.trace: list[TraceEntry] = []
        #: ISO's own validation messages, in the order the rules raised them.
        #: These are the `RatingMessages` of a RAaS response.
        self.messages: list[str] = []
        self._guid = 0
        self._programs: dict[str, Program] = {}
        self.state_program = self._program_for(book.resolution.state)
        self.parent_program = (self._program_for(book.resolution.parent)
                               if book.resolution.parent else None)

    # ------------------------------------------------------------- machinery

    def _program_for(self, package) -> Program:
        if package.pkg_id not in self._programs:
            self._programs[package.pkg_id] = Program(package)
        return self._programs[package.pkg_id]

    @staticmethod
    def tag(el) -> str:
        return el.tag.rsplit("}", 1)[-1]

    def where(self, el) -> str:
        return self.tag(el)

    def note(self, kind: str, detail: str, source: str = "", **data) -> None:
        if self.tracing:
            self.trace.append(TraceEntry(kind, detail, source, data))

    def trace_exhausted(self, el) -> None:
        """Contract C6: an exhausted FirstNonNull is recorded, not raised."""
        self.note("first-non-null-exhausted",
                  "every argument was null; null returned", self.tag(el))

    def trace_branch_abandoned(self, el, idx: int, exc) -> None:
        """OI-88: a branch that hit null in arithmetic is recorded, not raised.

        Recorded for the same reason C6 exhaustion is. Of the 69 sites in the
        corpus where this can fire, **51 carry a trailing `Constant`** that will
        answer once the branch is abandoned -- so a genuinely missing value
        would otherwise leave no evidence at all, and a defect in our own table
        loading would read as a normal rating. Silence here is the failure mode;
        the trace is what keeps it auditable.
        """
        self.note("first-non-null-branch-abandoned",
                  f"argument {idx} reached null in arithmetic; "
                  f"trying the next -- {exc}", self.tag(el), arg=idx)

    def next_guid(self) -> str:
        self._guid += 1
        return f"{self._guid:08x}-0000-0000-0000-000000000000"

    # ---------------------------------------------------------------- rounding

    def round_to(self, value: Decimal, el, where: str,
                 required: bool = False) -> Decimal:
        places = el.attrib.get("DecimalPlaces")
        if places is None:
            if required:
                raise InterpretError(
                    "Round without @DecimalPlaces", "§6", where)
            return value
        try:
            n = int(places)
        except ValueError:
            raise InterpretError(
                f"@DecimalPlaces={places!r} is not an integer", "§6",
                where) from None
        out = value.quantize(Decimal(1).scaleb(-n), rounding=self.rounding)
        self.note("round",
                  f"{value} -> {out} at {n}dp using {self.rounding_name}",
                  where, node=where, was=str(value), now=str(out),
                  decimal_places=n, mode=self.rounding_name)
        return out

    # ------------------------------------------------------------------ eval

    def eval(self, el, frame: Frame):
        name = self.tag(el)
        fn = nodes.EVAL.get(name)
        if fn is None:
            raise InterpretError(
                f"unknown node {name!r}; the language has 54 and a 55th means "
                f"ISO filed something new", "§12.1", name)
        value = fn(self, el, frame)

        to = el.attrib.get("ToDataDef")
        if to is not None:
            tree.write(to, frame.data, value)
            self.note("write", f"{to} = {value!r}", name)
        return value

    # -------------------------------------------------------------- dispatch

    def call(self, file_name: str, rule_name: str, project: str | None,
             args: dict, frame: Frame, where: str):
        """Run a rule. Parent-directed calls never re-parent (N2, §8)."""
        if frame.depth >= MAX_DEPTH:
            raise InterpretError(
                f"rule call depth {frame.depth} exceeded; the corpus call "
                f"graph is acyclic, so this is the engine looping",
                "§8", f"{file_name}.{rule_name}")

        if project is not None:
            # An explicit call-super. It targets the parent's copy of THIS rule
            # and nothing else -- 4,598 rules are "do what the parent does,
            # then this", and naming the package is how they avoid calling
            # themselves.
            if self.parent_program is None:
                raise InterpretError(
                    f"@ProjectName={project!r} but this book has no parent "
                    f"layer", "§8", where)
            program, parent_scope = self.parent_program, True
        else:
            # **A bare call always resolves state-first, per RULE, whichever
            # package the caller is in.** This is the override mechanism and it
            # is not optional: the parent's `ErcProcess` bare-calls
            # `SetPremOpsLossCost`, and in NJ, CA, NY and OH that rule is
            # overridden by the state to read the per-territory sliced loss-cost
            # tables. Keeping a parent-scope caller inside the parent makes
            # every one of those overrides unreachable -- the countrywide rule
            # runs, its lookup misses a header-only table, and **the premises/
            # operations premium silently comes out zero**. That is what CA, NJ
            # and NY were doing: pricing products only.
            program, parent_scope = None, False
            for cand in (self.state_program, self.parent_program):
                if cand is not None and cand.has_rule(file_name, rule_name):
                    program = cand
                    parent_scope = cand is self.parent_program
                    break
            if program is None:
                builtin = _BUILTINS.get(file_name)
                if builtin is not None:
                    return builtin(self, rule_name, args, frame, where)
                program = frame.program            # let it raise where it is
            elif parent_scope and self.state_program.has_file(file_name):
                self.note("inherit-rule",
                          f"{file_name}.{rule_name} from the parent",
                          program.pkg_id)

        el = program.rule(file_name, rule_name)
        inner = frame.in_rule(program, file_name, args, parent_scope)
        self.note("call", f"{file_name}.{rule_name}"
                          + (f" @{project}" if project else ""),
                  program.pkg_id)

        out = None
        for ch in el:
            if self.tag(ch) == "Param":
                continue                      # a declaration, bound at the call
            out = self.eval(ch, inner)

        declared = el.attrib.get("Type", "none")
        if declared == "none":
            return None
        return coerce(out, declared, f"{file_name}.{rule_name}") \
            if out is not None else None

    # ---------------------------------------------------------------- lookup

    def _find_table(self, name: str, where: str) -> tuple[Table, str]:
        for kind in LOOKUP_KINDS:
            if self.book.declares(name, kind):
                return self.book.table(name, kind), kind
        raise InterpretError(
            f"no table {name!r} in {', '.join(LOOKUP_KINDS)} for "
            f"{self.book.juris}@{self.book.asof}", "§7", where)

    def lookup(self, name: str, col: str, keys: list, mode: str, typ: str,
               where: str):
        """Match `keys` against the table's key columns, in filed order (§7)."""
        table, kind = self._find_table(name, where)
        defn = table.definition

        if defn.key_ranges:
            return self._lookup_banded(table, kind, name, col, keys, mode,
                                       typ, where)

        if col not in table.header:
            raise InterpretError(
                f"table {name!r} has no column {col!r}", "§7", where)

        key_names = [c.name for c in defn.key_cols]
        if not defn.declared:
            # No definition file, so stage 1 marks every column a key -- its
            # honest "we do not know". 3,056 CSVs in the corpus are like this,
            # including `Pages`, which is the single most common lookup target.
            # The keys are the LEADING columns in filed order, which is the only
            # reading the data supports, and the trace records that we inferred
            # it rather than read it.
            if len(keys) > len(key_names):
                raise InterpretError(
                    f"undeclared table {name!r} has {len(key_names)} columns "
                    f"and the lookup supplied {len(keys)} keys", "§7", where)
            key_names = key_names[:len(keys)]
            self.note("lookup-undeclared",
                      f"{name} has no definition file; matched the first "
                      f"{len(keys)} columns {key_names} in filed order",
                      where)
        elif len(keys) != len(key_names):
            raise InterpretError(
                f"table {name!r} has {len(key_names)} key columns and the "
                f"lookup supplied {len(keys)}", "§7", where)

        idx = [table.col(k) for k in key_names]
        want = [compare_key(k) for k in keys]
        out_i = table.col(col)

        hits = [row for row in table.rows
                if all(compare_key(row[i]) == w for i, w in zip(idx, want))]

        if not hits:
            self.note("lookup-miss", f"{name}[{col}] keys={keys!r}",
                      table.package)
            return None
        if mode == "SingleResult" and len(hits) > 1:
            raise InterpretError(
                f"SingleResult matched {len(hits)} rows in {name!r}; ISO is "
                f"asserting this key is unique and it is not", "§7", where)
        if len(hits) > 1:
            # Contract §7: FirstResult on a non-unique key is order-dependent,
            # so the trace has to say it happened or a wrong answer looks clean.
            self.note("lookup-nonunique",
                      f"{name}[{col}] keys={keys!r} matched {len(hits)} rows; "
                      f"took the first in filed order", table.package)

        value = hits[0][out_i]
        self.note("lookup", f"{name}[{col}] keys={keys!r} -> {value!r}",
                  str(Citation(table.package, f"{kind} Tables", name,
                               repr(keys))),
                  table=name, column=col, keys=[str(k) for k in keys],
                  value=str(value), package=table.package, category=kind,
                  rows=len(table.rows), result_mode=mode)
        return coerce(value, typ, where)

    # ------------------------------------------------------------ banded

    def _lookup_banded(self, table, kind, name, col, keys, mode, typ, where):
        """A lookup whose key is a band, and possibly whose value is too.

        Measured over 570 packages (`scripts/erc/46_banded_lookups.py`), the
        whole population is 11 table names, every one of them reachable:

        * **exactly one key range each**, always alongside plain equality key
          columns, so the supplied `Keys` map positionally onto
          `key_cols + key_ranges` in declared order -- the same order the CSV
          header is built in
        * **two boundary types**: `FromInclusiveToExclusive` (115 definitions)
          and `FromExclusiveToInclusive` (78)
        * **two interpolated tables**, both size-of-risk relativity, both
          `Linear`

        **A stepped reading of an interpolated band is wrong by up to the width
        of the band**, which is why this refused rather than approximated until
        it was specified.
        """
        defn = table.definition
        rng = defn.key_ranges[0]
        eq = [c.name for c in defn.key_cols]

        if len(keys) != len(eq) + 1:
            raise InterpretError(
                f"banded table {name!r} takes {len(eq)} equality keys plus a "
                f"band value; the lookup supplied {len(keys)}", "§7", where)

        idx = [table.col(k) for k in eq]
        want = [compare_key(k) for k in keys[:len(eq)]]
        lo_i, hi_i = table.col(rng.lo_col), table.col(rng.hi_col)
        x = to_decimal(keys[-1], where)

        hits = []
        for row in table.rows:
            if any(compare_key(row[i]) != w for i, w in zip(idx, want)):
                continue
            lo, hi = row[lo_i], row[hi_i]
            if lo is None or hi is None:
                continue
            lo, hi = Decimal(lo), Decimal(hi)
            below = lo <= x if rng.lo_inclusive else lo < x
            above = x <= hi if rng.hi_inclusive else x < hi
            if below and above:
                hits.append((row, lo, hi))

        if not hits:
            self.note("lookup-miss",
                      f"{name}[{col}] keys={keys!r} fell outside every band",
                      table.package)
            return None
        if mode == "SingleResult" and len(hits) > 1:
            raise InterpretError(
                f"SingleResult matched {len(hits)} bands in {name!r}; the "
                f"bands overlap and ISO asserts they do not", "§7", where)
        if len(hits) > 1:
            self.note("lookup-nonunique",
                      f"{name}[{col}] keys={keys!r} matched {len(hits)} "
                      f"overlapping bands; took the first in filed order",
                      table.package)

        row, lo, hi = hits[0]

        # The value may itself be a range, interpolated along the key band.
        for vr in defn.value_ranges:
            if vr.name != col:
                continue
            v_lo = Decimal(row[table.col(vr.lo_col)])
            v_hi = Decimal(row[table.col(vr.hi_col)])
            if vr.interpolate != "Linear":
                raise InterpretError(
                    f"value range {col!r} declares InterpolateMode="
                    f"{vr.interpolate!r}; only Linear is filed", "§12.2", where)
            # Interpolation only ever occurs on FromInclusiveToExclusive bands
            # in this corpus, where `x == lo` gives position 0 and `x == hi`
            # belongs to the next band -- so the boundary is unambiguous and
            # P5's open question about the two combined does not arise.
            span = hi - lo
            pos = (x - lo) / span if span else Decimal(0)
            out = v_lo + (v_hi - v_lo) * pos
            self.note("lookup-interpolated",
                      f"{name}[{col}] {x} in [{lo},{hi}) -> {out} "
                      f"between {v_lo} and {v_hi}",
                      str(Citation(table.package, f"{kind} Tables", name,
                                   repr(keys))),
                      table=name, column=col, keys=[str(k) for k in keys],
                      value=str(out), package=table.package, category=kind,
                      band_from=str(lo), band_to=str(hi),
                      between=[str(v_lo), str(v_hi)], at=str(x),
                      interpolate="Linear")
            return coerce(out, typ, where)

        if col not in table.header:
            raise InterpretError(
                f"table {name!r} has no column or value range {col!r}",
                "§7", where)
        value = row[table.col(col)]
        self.note("lookup-banded",
                  f"{name}[{col}] {x} in band [{lo},{hi}] -> {value!r}",
                  str(Citation(table.package, f"{kind} Tables", name,
                               repr(keys))),
                  table=name, column=col, keys=[str(k) for k in keys],
                  value=str(value), package=table.package, category=kind,
                  band_from=str(lo), band_to=str(hi), banded_on=rng.name)
        return coerce(value, typ, where)

    # ------------------------------------------------------------------- run

    def run(self, data: Node) -> Node:
        """Execute the `Default` block against `data`, returning the tree."""
        entry = self.state_program.entry()
        frame = Frame(data=data, program=self.state_program,
                      rule_file="Overall Rating")
        self.note("entry", f"Default block of {self.state_program.pkg_id}",
                  "Overall Rating.Rule.xml")
        self.eval(entry, frame)
        return data

    def trace_text(self) -> str:           # pragma: no cover - display only
        return "\n".join(str(t) for t in self.trace)
