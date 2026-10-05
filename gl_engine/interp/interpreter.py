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

import os
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP, ROUND_HALF_EVEN, ROUND_DOWN

from ..domain import Citation
from ..erc.tables import Range, Shape, Table
from . import nodes, tree
from .program import Program
from .tree import Node
from .values import (InterpretError, NullInArithmetic, coerce, compare_key,
                     to_decimal)

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

#: Datadefs that carry MONEY OUT of a rating, and so must never be written
#: null. Named explicitly rather than matched by pattern.
#:
#: A substring test on "Premium" was the obvious implementation and is wrong:
#: the corpora write `PremiumIndicator` (a 0/1 flag, 21,386 writes across both),
#: `MultiPremiumAndDispersionCreditFactor` (a factor), `PremiumBasis` (an
#: exposure basis) and `PremiumDiscountCharge`. Guarding those would refuse
#: ordinary content. This project has already paid once for letting a search
#: predicate define a population; the set below is a decision, and adding to it
#: is also a decision.
#:
#: `Premium` is every coverage's own answer and the policy's;
#: `ErcCalculatedTotalPremium` is the figure a RAaS response leads with.
#: Between them they are what "the policy came out free" would have to pass
#: through.
PREMIUM_TARGETS = frozenset({"Premium", "ErcCalculatedTotalPremium"})


def _premium_target(path: str) -> bool:
    """Does this `ToDataDef` path address a premium?

    Only the LAST step matters -- `Premium`, `../Premium` and
    `../../CommercialPropertyStructure[1]/Premium` are all the same datadef
    reached from different places.
    """
    leaf = path.rstrip("/").rsplit("/", 1)[-1]
    if leaf.endswith("]"):
        leaf = leaf[:leaf.rindex("[")]
    return leaf in PREMIUM_TARGETS


#: The null-in-arithmetic policy every `Interpreter` starts with.
#:
#: Overridable by environment variable for ONE purpose: running an entire test
#: suite under a variant to measure what it would change. That is how `"zero"`
#: was disproven and how `"propagate"` was shown to move nothing in General
#: Liability. It is not a configuration knob for production, and a caller that
#: means it passes `null_arithmetic=` explicitly.
DEFAULT_NULL_ARITHMETIC = os.environ.get("ERC_NULL_ARITHMETIC", "refuse")

#: Whether a `SingleResult` lookup matching no row refuses (open item 8).
#:
#: Unset (None), the BOOK decides: a book whose class sets
#: `strict_single_result = True` refuses (Property, chunk 28 C28-05: ISO refuses
#: 65 of 66 such misses live, and none of 1,690 rated requests has one); any
#: other book does not (General Liability, unmeasured). The environment
#: variable overrides both ways, for the same one purpose as above: running a
#: whole suite under the variant to see what it would change.
_STRICT_ENV = os.environ.get("ERC_STRICT_SINGLE_RESULT", "").strip().lower()
DEFAULT_STRICT_SINGLE_RESULT = (
    True if _STRICT_ENV in ("1", "true", "yes", "on")
    else False if _STRICT_ENV in ("0", "false", "no", "off")
    else None)


@dataclass
class Frame:
    """One evaluation context: where in the data, which package, which params."""

    data: Node
    program: Program
    rule_file: str
    parent_scope: bool = False            # inside a @ProjectName call (N2)
    params: dict = field(default_factory=dict)
    depth: int = 0
    # `None` means "same as `data`" -- the ordinary case, where reads and
    # writes share one position. `AtInputDataDef` is the one place the two
    # diverge (§9): it rebinds `data` so the loop body can READ the item, but
    # a bare `ToDataDef` inside it still means the enclosing record, not the
    # item -- see `_for_each`'s `keep_write_root`.
    write_root: Node | None = None

    @property
    def write_target(self) -> Node:
        return self.write_root if self.write_root is not None else self.data

    def at(self, node: Node, keep_write_root: bool = False) -> "Frame":
        write_root = self.write_target if keep_write_root else None
        return Frame(node, self.program, self.rule_file, self.parent_scope,
                     self.params, self.depth, write_root)

    def with_params(self, bindings: dict) -> "Frame":
        if not bindings:
            return self
        merged = dict(self.params)
        merged.update(bindings)
        return Frame(self.data, self.program, self.rule_file,
                     self.parent_scope, merged, self.depth, self.write_root)

    def in_rule(self, program: Program, rule_file: str, params: dict,
                parent_scope: bool) -> "Frame":
        return Frame(self.data, program, rule_file, parent_scope, params,
                     self.depth + 1, self.write_root)

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

    #: What a null reaching arithmetic does. `"refuse"` is contract §12.3 and
    #: the default: a null is not a zero, and folding one into the other is how
    #: a missing coverage becomes a free one.
    #:
    #: `"zero"` is the alternative hypothesis, added 2026-09-17 to be MEASURED
    #: rather than argued about. ISO's own service rates a New York Property
    #: risk that this engine refuses, because a rule filed only in New York
    #: subtracts a policy premium that is not computed until after validation
    #: runs. Either ISO coerces, or ISO's ordering differs.
    #:
    #: **The measurement was made, and coercion is DISPROVEN.** Kept only so
    #: the disproof is one line to reproduce -- never as a fallback, and never
    #: to be switched on to make a stubborn case pass.
    #:
    #: Rating New York with `"zero"` completes, and returns **$0** where ISO
    #: returns **$396**. The trace says exactly why, and it is not subtle:
    #:
    #:     lookup-miss: BasicGroupILOIFactorBldg keys=['NY', 100000, 1]
    #:     null-coerced: null reached arithmetic and became 0
    #:
    #: ISO writes every state-to-countrywide fallback as
    #: `FirstNonNull(Round(Lookup(state)), Round(Lookup('CW')))`, where the
    #: state lookup is DESIGNED to miss. Refusing lets `FirstNonNull` abandon
    #: branch one and reach countrywide (OI-88). Coercing turns the miss into a
    #: perfectly good `0`, `FirstNonNull` accepts it, and **the countrywide row
    #: is never read**. That idiom is everywhere in both corpora, so a coercing
    #: engine would price vast numbers of risks at zero -- and ISO's service
    #: plainly does not.
    #:
    #: So §12.3 is not merely intact, it is confirmed by its own counter-test.
    #: New York's cause must be the other candidate: ISO's `Premium` is already
    #: populated when validation runs. Locked in by `verify_interp` B23/B24.
    #: `"propagate"` is the third hypothesis, and the one that survives.
    #: Arithmetic with a null operand yields **null**, not zero and not a
    #: refusal; a comparison with a null operand is **false**. It was reached
    #: by elimination after the other two failed, and it is the only one of the
    #: three consistent with everything observed:
    #:
    #: * New York's rule becomes `0 > null` -> false, no message, rating
    #:   completes -- which is what ISO does.
    #: * The state-to-countrywide fallback SURVIVES, because `Round(null)`
    #:   yields null and `FirstNonNull` still falls through to countrywide.
    #:   This is precisely where `"zero"` destroyed it.
    #:
    #: Null propagation is also the ordinary semantics of every three-valued
    #: system this language resembles (SQL, XPath), which is weak evidence but
    #: not no evidence.
    NULL_ARITHMETIC = ("refuse", "zero", "propagate")

    #: Nodes whose result is null when an operand is null, under `propagate`.
    PROPAGATING = frozenset({
        "Product", "Subtract", "Divide", "Max", "Round", "Truncate", "Sum",
        "Power", "Convert", "DateAdd", "DateDifference", "DatePart",
        "DateCreate", "PadLeft", "Length",
    })

    #: Comparisons, which yield FALSE rather than null when an operand is null.
    #: A `Test` demands a boolean, so a null here would only move the refusal
    #: one level up.
    COMPARING = frozenset({
        "GreaterThan", "GreaterThanOrEqual", "LessThan", "LessThanOrEqual",
    })

    def __init__(self, book, rounding: str = "ROUND_HALF_UP",
                 trace: bool = True, null_arithmetic: str | None = None,
                 guard_null_premium: bool = True,
                 strict_single_result: bool | None = None,
                 null_premium: str | None = None):
        null_arithmetic = null_arithmetic or DEFAULT_NULL_ARITHMETIC
        if rounding not in ROUNDING_MODES:
            raise InterpretError(
                f"unknown rounding mode {rounding!r}", "§6", "")
        if null_arithmetic not in self.NULL_ARITHMETIC:
            raise InterpretError(
                f"unknown null_arithmetic mode {null_arithmetic!r}; "
                f"one of {self.NULL_ARITHMETIC}", "§12.3", "")
        self.book = book
        self.rounding_name = rounding
        self.rounding = ROUNDING_MODES[rounding]
        self.null_arithmetic = null_arithmetic
        #: Refuse to write a null into a money datadef (`PREMIUM_TARGETS`).
        #:
        #: **This is what `propagate` traded away, bought back.** `refuse`
        #: failed loudly the moment a null reached arithmetic; `propagate`
        #: lets nulls flow, which is what ISO does, but a null can then reach
        #: a premium and vanish -- `Sum` skips null operands by design, so a
        #: coverage that resolved to nothing would simply not be added up, and
        #: the policy would come out cheaper with nothing raised anywhere.
        #:
        #: So the loudness moves from "any arithmetic" to "the money". Nulls
        #: are free to flow through intermediate steps, exactly as ISO's own
        #: fallback idiom needs, and are refused at the one boundary where
        #: absent silently becomes free.
        self.guard_null_premium = guard_null_premium
        #: What the guard does with a null premium: "refuse" (raise), or
        #: "zero" (write 0, as ISO does, and say so in the trace).
        #:
        #: **ISO writes $0 (OI-109, confirmed live 5 of 5).** A coverage whose
        #: limit is missing prices at $0 while the rest of the policy rates:
        #: a building with no Limit ($0 plus ISO's "Please enter a Limit"
        #: message), Business Income with no Limit ($0, NO message), Ordinance
        #: or Law without its B/C limits. Refusing the whole submission there
        #: is stricter than the oracle. So under `propagate` -- the mode that
        #: already exists to behave as ISO does -- the default is "zero", and
        #: every zeroed premium is noted (`null-premium-zeroed`) and listed in
        #: `null_premiums`, so a silent ISO $0 is never a silent $0 here.
        #: `refuse` arithmetic (General Liability) keeps "refuse".
        if null_premium is None:
            null_premium = "zero" if null_arithmetic == "propagate" else "refuse"
        if null_premium not in ("refuse", "zero"):
            raise InterpretError(
                f"unknown null_premium mode {null_premium!r}", "§12.3", "")
        self.null_premium = null_premium
        #: Every premium target a null was written to as 0 ("zero" mode).
        self.null_premiums: list[str] = []
        #: `Product` skips a null operand instead of yielding null (OI-110):
        #: ISO's own behaviour, confirmed live where the remainder does not
        #: round to zero ($1, $3, $5). On under `propagate` (Property) only.
        #: With it on, "zero" above is reached only when EVERY operand of the
        #: premium product was null.
        self.product_skips_null = null_arithmetic == "propagate"
        #: Every operand `Product` left out, for the same visibility.
        self.null_skips: list[str] = []
        #: Refuse a `SingleResult` lookup that matches NO row -- see
        #: `_empty_lookup`. An explicit argument wins, then the environment,
        #: then the book's own class default (on for Property, off for GL).
        if strict_single_result is None:
            strict_single_result = DEFAULT_STRICT_SINGLE_RESULT
        if strict_single_result is None:
            strict_single_result = bool(
                getattr(book, "strict_single_result", False))
        self.strict_single_result = strict_single_result
        #: Every table a strict refusal fired on, for measuring the population.
        self.strict_refusals: list[str] = []
        #: Every site where a null was coerced. Empty in `refuse` mode.
        self.coercions: list[str] = []
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

    # -------------------------------------------------------------- arithmetic

    def num(self, value, where: str) -> Decimal:
        """The one door a value goes through to become a number.

        In `refuse` mode this is exactly `to_decimal` -- contract §12.3
        unchanged, and `NullInArithmetic` still escapes so `FirstNonNull` can
        still absorb it per branch (C6/OI-88).

        In `zero` mode a null becomes `Decimal(0)` **and is recorded**. Nothing
        else changes: an empty string, a non-numeric string and a `Multi` in a
        scalar position are still refusals, because none of those is the
        hypothesis under test.
        """
        if value is None and self.null_arithmetic == "zero":
            self.coercions.append(where)
            self.note("null-coerced",
                      "null reached arithmetic and became 0 "
                      "(null_arithmetic='zero')", where)
            return Decimal(0)
        return to_decimal(value, where)

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
            # The count is read from the registry rather than written down. It
            # was a literal 54 until Commercial Property added five evaluators,
            # at which point the message named a number that was no longer
            # true -- in the one error whose entire job is to say "ISO filed
            # something this engine has not been taught".
            n = len(nodes.EVAL)
            raise InterpretError(
                f"unknown node {name!r}; the engine implements {n} and a "
                f"{n + 1}th means ISO filed something new", "§12.1", name)
        if self.null_arithmetic == "propagate":
            # Null propagation is applied HERE rather than inside each
            # evaluator, so the sixteen arithmetic sites keep one behaviour and
            # the policy stays one decision. `NullInArithmetic` is the only
            # thing caught, and only for nodes that are declared to propagate:
            # a `Multi` in a scalar position, an empty string or a non-numeric
            # string still refuse, because none of those is null.
            try:
                value = fn(self, el, frame)
            except NullInArithmetic as exc:
                if name in self.PROPAGATING:
                    self.coercions.append(name)
                    self.note("null-propagated",
                              f"{name} had a null operand and yielded null",
                              name)
                    value = None
                elif name in self.COMPARING:
                    self.coercions.append(name)
                    self.note("null-comparison-false",
                              f"{name} had a null operand and yielded false",
                              name)
                    value = False
                else:
                    raise exc
        else:
            value = fn(self, el, frame)

        to = el.attrib.get("ToDataDef")
        if to is not None:
            if value is None and self.guard_null_premium \
                    and _premium_target(to) and self.null_premium == "zero":
                # OI-109: ISO writes $0. Do the same, and leave a mark.
                self.null_premiums.append(to)
                self.note("null-premium-zeroed",
                          f"{name} resolved to NULL for {to!r}; written as 0, "
                          f"as ISO does (OI-109). Something upstream resolved "
                          f"to nothing -- the trace above names it", name,
                          target=to)
                value = Decimal(0)
            elif value is None and self.guard_null_premium \
                    and _premium_target(to):
                raise InterpretError(
                    f"{name} wrote a NULL to {to!r}. A premium is money: "
                    f"absent is not zero, and a null here disappears into "
                    f"`Sum`, which skips null operands by design. Something "
                    f"upstream resolved to nothing -- most often a rate table "
                    f"that missed -- and the trace above names it",
                    "§12.3", name)
            tree.write(to, frame.write_target, value)
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

    def _empty_lookup(self, name, col, keys, mode, table, where):
        """A lookup that matched NO row. Null, or a refusal (§7).

        **ISO refuses, and this engine does not -- open item 8.** Sending a
        construction type ISO does not file returns a 400 from its service:

            Matrix: ConstructionTypeToUse, Keys: CW, Masonry Non-Combustible.
            No results have been returned.

        ...while this engine returns null, lets it flow, and prices the
        coverage at zero. A submission ISO would reject can come back from us
        as a quiet, plausible premium.

        **Property refuses (chunk 28 C28-05, 2026-10-05).** `CFResolvedBook`
        turns `strict_single_result` on: ISO refuses 65 of 66 such misses live
        at its own table, and none of 1,690 requests ISO rated has one
        (`docs/CF-CHUNK28-PROPOSAL-A.md`). General Liability keeps it off
        until measured on its own evidence. The population is why it is
        `SingleResult` only:

        * `FirstResult` misses are ISO's own two-pass idiom and are DESIGNED to
          happen -- the state pass misses so the countrywide pass can answer.
          Those must stay null under every mode.
        * `SingleResult` is the countrywide pass, the last resort. It is the
          last resort in 23,586 of 23,631 Commercial Property `FirstNonNull`
          constructs, and in 4,935 of 4,935 in General Liability.
        * The other **45 CF sites put a `Constant` AFTER it** -- a real
          fallback that a refusal would skip.
        """
        if mode == "SingleResult" and self.strict_single_result:
            self.strict_refusals.append(name)
            raise InterpretError(
                f"SingleResult matched NO row in {name!r} for keys {keys!r}. "
                f"ISO's own service refuses a submission at this point rather "
                f"than returning nothing", "§7", where)
        return None

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
            return self._empty_lookup(name, col, keys, mode, table, where)
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
        GL-side population is 11 table names, every one of them reachable:

        * **exactly one key range each**, always alongside plain equality key
          columns, so the supplied `Keys` map positionally onto the key columns
          in ISO's DECLARED order -- the same order the CSV header is built in
        * **two boundary types**: `FromInclusiveToExclusive` (115 definitions)
          and `FromExclusiveToInclusive` (78)
        * **two interpolated tables**, both size-of-risk relativity, both
          `Linear`

        **A stepped reading of an interpolated band is wrong by up to the width
        of the band**, which is why this refused rather than approximated until
        it was specified.

        **The band is not necessarily the last key.** It is in General
        Liability -- 218 definitions with a key range, 218 declaring it last --
        and the first version of this method read `keys[-1]` as the band on the
        strength of that. Commercial Property files 19 table names that declare
        a range in the middle: `DeductibleFactor` is `StateCode, Deductible,
        Range(Limit), CauseOfLossDeductible`, so reading its third key as its
        fourth sends the string `'Basic Group I'` into `to_decimal`. That at
        least raised. The same mistake on a table whose trailing key happens to
        be numeric would have matched the wrong band and returned a plausible
        factor, which is why the order is now read from the definition rather
        than assumed from a measurement of one corpus.

        **A second range, found later on the Commercial Property side, is a
        plain containment filter, not a second interpolation dimension
        (C10-19, then this fix).** `46_banded_lookups.py` never saw it because
        it scanned General Liability alone, where the population above is
        exhaustive; scanning Commercial Property finds 28 more table names
        that declare TWO `rt:Range` key columns, all sharing one shape --
        N equality columns, then two ranges. Every one of the 28 is one of:

        * 13 `EQSubLimit<N>FlatDeductibleFactor` tables (Earthquake sub-limit
          plus flat-dollar-deductible rating, `CommercialPropertyStructure
          Rules.Rule.xml`'s `SetEQDeductibleFactor`) -- live.
        * 7 `PropertyRateModificationFactors1`-`7` (plural family, Flood
          coverage endorsements, `CommercialPropertyFloodCoverageEndorsement
          Rules.Rule.xml`) -- live.
        * 1 `HeatingOilTankServingResidentialPropertiesIndicator`
          (Massachusetts structure rule) -- live.
        * 7 `PropertyRateModificationFactor1`-`7` (singular/unnumbered-plural
          sibling family) -- confirmed dead, zero rule references anywhere;
          left unreachable on purpose, same as the dead EQ tables C10-13 found.

        Every live one of the 28 declares AT MOST ONE of its ranges with a
        `ValueCols/rt:Range@RangeKeyCol` naming it -- that is the
        interpolation dimension when one is filed at all, resolved by name,
        not position. `HeatingOilTankServingResidentialPropertiesIndicator`
        files a plain `ValueCol` and no `RangeKeyCol` anywhere, same as an
        ordinary equality lookup except two of its keys are containment
        ranges instead of exact matches -- there is no interpolation to do,
        and none is attempted. Every OTHER range (there is at most one, in
        every table measured so far) is a plain `[lo, hi)`/`(lo, hi]`
        containment filter per its own `RangeType`, exactly like an equality
        key column except the match is a range instead of an exact value --
        it narrows `hits` and nothing else. A value range whose `RangeKeyCol`
        does not name one of the table's own key ranges refuses rather than
        guessing which one is meant.
        """
        defn = table.definition
        ranges = defn.key_ranges
        items = defn.key_items

        if len(keys) != len(items):
            raise InterpretError(
                f"banded table {name!r} declares {len(items)} key columns "
                f"({len(items) - len(ranges)} equality plus {len(ranges)} "
                f"range{'s' if len(ranges) != 1 else ''}); the lookup "
                f"supplied {len(keys)}", "§7", where)

        # Positional, in ISO's filed order: every Range slot is a containment
        # filter -- [lo, hi) or (lo, hi], per its own RangeType -- and every
        # other slot is an equality match. Which range (if any) also drives a
        # value-range interpolation is resolved separately, below, by name.
        eq_pairs, range_pairs = [], []
        for item, supplied in zip(items, keys):
            if isinstance(item, Range):
                range_pairs.append((item, to_decimal(supplied, where)))
            else:
                eq_pairs.append((table.col(item.name), compare_key(supplied)))
        range_cols = [(r, v, table.col(r.lo_col), table.col(r.hi_col))
                      for r, v in range_pairs]

        hits = []
        for row in table.rows:
            if any(compare_key(row[i]) != w for i, w in eq_pairs):
                continue
            bands, ok = {}, True
            for r, v, lo_i, hi_i in range_cols:
                lo, hi = row[lo_i], row[hi_i]
                if lo is None or hi is None:
                    ok = False
                    break
                lo, hi = Decimal(lo), Decimal(hi)
                below = lo <= v if r.lo_inclusive else lo < v
                above = v <= hi if r.hi_inclusive else v < hi
                if not (below and above):
                    ok = False
                    break
                bands[r.name] = (v, lo, hi)
            if ok:
                hits.append((row, bands))

        if not hits:
            self.note("lookup-miss",
                      f"{name}[{col}] keys={keys!r} fell outside every band",
                      table.package)
            return self._empty_lookup(name, col, keys, mode, table, where)
        if mode == "SingleResult" and len(hits) > 1:
            raise InterpretError(
                f"SingleResult matched {len(hits)} bands in {name!r}; the "
                f"bands overlap and ISO asserts they do not", "§7", where)
        if len(hits) > 1:
            self.note("lookup-nonunique",
                      f"{name}[{col}] keys={keys!r} matched {len(hits)} "
                      f"overlapping bands; took the first in filed order",
                      table.package)

        row, bands = hits[0]

        # The value may itself be a range, interpolated along ONE of the key
        # ranges -- named by RangeKeyCol, not assumed positionally.
        for vr in defn.value_ranges:
            if vr.name != col:
                continue
            if vr.range_key_col not in bands:
                raise InterpretError(
                    f"value range {col!r} in {name!r} declares "
                    f"RangeKeyCol={vr.range_key_col!r}, which is not one of "
                    f"this table's own key ranges "
                    f"({[r.name for r, _ in range_pairs]!r})", "§7", where)
            x, lo, hi = bands[vr.range_key_col]
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
        bands_desc = ", ".join(f"{rname}={v} in [{lo},{hi}]"
                               for rname, (v, lo, hi) in bands.items())
        self.note("lookup-banded",
                  f"{name}[{col}] {bands_desc} -> {value!r}",
                  str(Citation(table.package, f"{kind} Tables", name,
                               repr(keys))),
                  table=name, column=col, keys=[str(k) for k in keys],
                  value=str(value), package=table.package, category=kind,
                  banded_on=list(bands.keys()))
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
