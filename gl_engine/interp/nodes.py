"""The node evaluators -- one per element of ISO's rule language.

Every function here implements a clause of
`docs/rating-engine/14-EVALUATION-CONTRACT.md`, and the docstrings name the
clause rather than restating it. Where the contract says a case is a hard
failure, the code raises `InterpretError` naming the clause; **nothing here
guesses**, because every guess in this language produces a complete, plausible,
wrong premium rather than a crash.

Implementation order follows the corpus, not the alphabet: the top 20 nodes are
94.03% of all occurrences and are the ones exercised on every rating.
"""
from __future__ import annotations

import datetime as _dt
from decimal import Decimal, InvalidOperation

from . import tree
from .values import (TYPES, InterpretError, Multi, NullInArithmetic, coerce,
                     equal, flatten, to_text, truthy)

# NOTE: `to_decimal` is deliberately NOT imported here any more. Every
# conversion into arithmetic goes through `ip.num(...)`, the interpreter's
# single door, so that the null-in-arithmetic policy is one decision in one
# place rather than sixteen call sites that could drift apart.

#: node name -> evaluator. Populated by the decorator below.
EVAL: dict = {}


def node(*names):
    def wrap(fn):
        for n in names:
            EVAL[n] = fn
        return fn
    return wrap


class BreakLoop(Exception):
    """`Break`, travelling to the nearest enclosing loop (contract C12)."""


def _kids(el):
    return list(el)


def _only(el, ip):
    ch = _kids(el)
    if len(ch) != 1:
        raise InterpretError(
            f"{ip.tag(el)} takes exactly one child, found {len(ch)}",
            "§5", ip.where(el))
    return ch[0]


def _two(el, ip):
    ch = _kids(el)
    if len(ch) != 2:
        raise InterpretError(
            f"{ip.tag(el)} takes exactly two children, found {len(ch)}",
            "§5", ip.where(el))
    return ch


# ------------------------------------------------------------------ sequencing

@node("Sequence")
def _sequence(ip, el, fr):
    """Left to right, all of them; the value is the last child's (contract §3)."""
    out = None
    for ch in _kids(el):
        out = ip.eval(ch, fr)
    return out


@node("Default")
def _default(ip, el, fr):
    """The entry block (contract §2). Structurally a one-child wrapper."""
    return ip.eval(_only(el, ip), fr)


@node("Break")
def _break(ip, el, fr):
    """Terminate the nearest enclosing loop.

    84 of 84 occurrences sit inside one (`ForEach` 82, `GetList` 2), so the
    no-enclosing-loop case is unreachable in this corpus -- and is therefore a
    hard failure rather than a silent no-op, which is what it would have to be
    if we let it fall through.
    """
    raise BreakLoop()


# ---------------------------------------------------------------------- values

@node("Constant")
def _constant(ip, el, fr):
    """The text payload. Absent text is the empty string, not null (Q1)."""
    typ = el.attrib.get("Type", "string")
    raw = el.text if el.text is not None else ""
    return coerce(raw, typ, ip.where(el))


@node("Value")
def _value(ip, el, fr):
    """Read a DataDef or a parameter (contract §4, C13).

    `@FromParam` is 47.81% of `Value` nodes -- parameters are not a rarity, and
    C2's finding about `FirstValue` says nothing about them.
    """
    typ = el.attrib.get("Type", "string")
    where = ip.where(el)

    if "FromParam" in el.attrib:
        name = el.attrib["FromParam"]
        if not fr.has_param(name):
            raise InterpretError(
                f"parameter {name!r} is not bound here", "§8", where)
        return coerce(fr.param(name), typ, where)

    path = el.attrib.get("FromDataDef")
    if path is None:
        raise InterpretError(
            "Value with neither @FromDataDef nor @FromParam", "§4", where)
    # A read that resolves to nothing returns null. It does NOT raise, even
    # without @AllowNullReturn -- 75.30% of declared elements are nillable, no
    # read in the corpus targets a non-nillable one, and 28,347 bare reads
    # address an explicitly nillable element. The guard against nulls sits at
    # the arithmetic boundary (§12.3), which is where a null becomes a wrong
    # premium rather than merely an absent one.
    return coerce(tree.read(path, fr.data), typ, where)


@node("FirstValue")
def _first_value(ip, el, fr):
    """DataDef if non-null, else the constant (contract C2).

    `@Order` carries one value corpus-wide and only `FromDataDef` +
    `FromConstant` are ever filed, across all 171,189 nodes. `FromInput` and
    `FromParam` are hard failures **here** -- the engine does not invent a
    precedence it has never seen exercised.
    """
    where = ip.where(el)
    order = el.attrib.get("Order")
    if order not in (None, "DataDefInputParamConstant"):
        raise InterpretError(
            f"FirstValue @Order={order!r} was never filed", "§12.2", where)
    for unused in ("FromInput", "FromParam"):
        if unused in el.attrib:
            raise InterpretError(
                f"FirstValue @{unused} was never filed in the corpus; its "
                f"precedence is unexercised and will not be guessed",
                "§12.2", where)

    typ = el.attrib.get("Type", "string")
    path = el.attrib.get("FromDataDef")
    if path is not None:
        raw = tree.read(path, fr.data)
        if raw is not None and str(raw) != "":
            return coerce(raw, typ, where)
    if "FromConstant" in el.attrib:
        return coerce(el.attrib["FromConstant"], typ, where)
    return None


@node("FirstNonNull")
def _first_non_null(ip, el, fr):
    """First non-null child; null if all are null (contract C6).

    Exhaustion is legal and traced rather than raised: 34,051 of 38,378 end in a
    `Constant` and cannot exhaust, but 4,327 can. Where ISO wants a guaranteed
    value it appends a total fallback itself.

    **A branch may also *become* null through arithmetic (OI-88).** ISO writes
    state-to-countrywide fallbacks as `Round(Lookup(state))` then
    `Round(Lookup('CW'))`, and the first lookup is *designed* to miss --
    `PremOpsSizeOfRiskRelativity` holds 8,330 rows, every one of them `CW`.
    Letting `Round`'s refusal escape made branch two unreachable and stopped
    size-of-risk in 49 of 51 jurisdictions.

    So `NullInArithmetic` -- and **only** that type -- is caught per branch and
    treated as a null argument. Every other refusal still escapes: this is the
    one construct that declares a null branch legal, and it is not a licence to
    answer where the engine should stop.
    """
    for idx, ch in enumerate(_kids(el)):
        try:
            vals = flatten(ip.eval(ch, fr))
        except NullInArithmetic as exc:
            ip.trace_branch_abandoned(el, idx, exc)
            continue
        for v in vals:
            if v is not None and v != "":
                return v
    ip.trace_exhausted(el)
    return None


@node("Param")
def _param(ip, el, fr):
    """A rule's parameter declaration. Binding happens at the call site."""
    return None


# ---------------------------------------------------------------- conditionals

@node("If")
def _if(ip, el, fr):
    """`Test` + `Then`, `Else` optional and absent 41% of the time (§5).

    No `Else` and a false test yields null -- not zero, which would be a rate.
    """
    test = then = other = None
    for ch in _kids(el):
        t = ip.tag(ch)
        if t == "Test":
            test = ch
        elif t == "Then":
            then = ch
        elif t == "Else":
            other = ch
        else:
            raise InterpretError(
                f"If holds a {t}", "§5", ip.where(el))
    if test is None or then is None:
        raise InterpretError("If without Test or Then", "§5", ip.where(el))
    if truthy(ip.eval(test, fr), ip.where(test)):
        return ip.eval(then, fr)
    return ip.eval(other, fr) if other is not None else None


@node("Test", "Then", "Else", "Otherwise")
def _wrapper(ip, el, fr):
    """One-child clause wrappers (contract §5)."""
    return ip.eval(_only(el, ip), fr)


@node("Choose")
def _choose(ip, el, fr):
    """First `When` whose test holds; `Otherwise` optional (contract §5)."""
    other = None
    for ch in _kids(el):
        t = ip.tag(ch)
        if t == "When":
            test = then = None
            for sub in _kids(ch):
                st = ip.tag(sub)
                if st == "Test":
                    test = sub
                elif st == "Then":
                    then = sub
            if test is None or then is None:
                raise InterpretError(
                    "When without Test or Then", "§5", ip.where(ch))
            if truthy(ip.eval(test, fr), ip.where(test)):
                return ip.eval(then, fr)
        elif t == "Otherwise":
            other = ch
        else:
            raise InterpretError(f"Choose holds a {t}", "§5", ip.where(el))
    return ip.eval(other, fr) if other is not None else None


@node("When")
def _when(ip, el, fr):                       # reached only if nested oddly
    raise InterpretError("When outside a Choose", "§5", ip.where(el))


# ------------------------------------------------------------------ predicates

def _operand_bools(ip, el, ch, fr) -> list:
    """One `And`/`Or` operand as a list of booleans.

    Normally one boolean. But an operand may be a `ForEach`, in which case it
    is a quantifier over the iteration: `Or(ForEach(...))` is "any structure
    has this endorsement", `And(ForEach(...))` is "every one does".

    **General Liability never files this shape** -- 0 of its 58,752 `And`/`Or`
    elements has a `ForEach` child -- which is why the first version of these
    two evaluators passed each operand straight to `truthy()` and a `Multi`
    reaching a condition was a hard failure. Commercial Property files it 369
    times (317 `Or`, 52 `And`), typically as an `Or` wrapping a single nested
    `ForEach` over locations and structures. So this is a shape the language
    always had and one corpus happened never to use.
    """
    v = ip.eval(ch, fr)
    if not isinstance(v, Multi):
        return [truthy(v, ip.where(ch))]
    vals = flatten(v)
    if not vals:
        # Zero iterations. `any([])` is False and `all([])` is True, which is
        # the ordinary reading of a quantifier over an empty set -- but it is a
        # reading, and on an `And` it makes the condition TRUE for a submission
        # that simply has no locations. Traced rather than silent, because a
        # validation message that fires on an empty policy should be visible as
        # this decision rather than look like data.
        ip.note("quantifier-empty",
                f"{ip.tag(el)} over an iteration that yielded nothing; "
                f"{'vacuously true' if ip.tag(el) == 'And' else 'false'}",
                ip.where(ch))
    return [truthy(x, ip.where(ch)) for x in vals]


@node("And")
def _and(ip, el, fr):
    """Variadic, short-circuiting left to right (contract C11).

    An operand that is an iteration means "every iteration" -- see
    `_operand_bools`.
    """
    for ch in _kids(el):
        if not all(_operand_bools(ip, el, ch, fr)):
            return False
    return True


@node("Or")
def _or(ip, el, fr):
    """Variadic, short-circuiting. An iteration operand means "any"."""
    for ch in _kids(el):
        if any(_operand_bools(ip, el, ch, fr)):
            return True
    return False


@node("Equal")
def _equal(ip, el, fr):
    a, b = _two(el, ip)
    return equal(ip.eval(a, fr), ip.eval(b, fr))


@node("NotEqual")
def _not_equal(ip, el, fr):
    a, b = _two(el, ip)
    return not equal(ip.eval(a, fr), ip.eval(b, fr))


def _cmp(ip, el, fr, op):
    a, b = _two(el, ip)
    x = ip.num(ip.eval(a, fr), ip.where(el))
    y = ip.num(ip.eval(b, fr), ip.where(el))
    return op(x, y)


@node("GreaterThan")
def _gt(ip, el, fr):
    return _cmp(ip, el, fr, lambda x, y: x > y)


@node("LessThan")
def _lt(ip, el, fr):
    return _cmp(ip, el, fr, lambda x, y: x < y)


@node("GreaterThanOrEqual")
def _ge(ip, el, fr):
    return _cmp(ip, el, fr, lambda x, y: x >= y)


@node("LessThanOrEqual")
def _le(ip, el, fr):
    return _cmp(ip, el, fr, lambda x, y: x <= y)


@node("IsNull")
def _is_null(ip, el, fr):
    v = ip.eval(_only(el, ip), fr)
    return v is None or v == ""


@node("IsNotNull")
def _is_not_null(ip, el, fr):
    v = ip.eval(_only(el, ip), fr)
    return not (v is None or v == "")


@node("Exist")
def _exist(ip, el, fr):
    """Presence in the tree, which is a different question from nullity (§4)."""
    path = el.attrib.get("AtInputDataDef", "")
    return bool(tree.select(path, fr.data))


@node("NotExist")
def _not_exist(ip, el, fr):
    path = el.attrib.get("AtInputDataDef", "")
    return not tree.select(path, fr.data)


# --------------------------------------------------------------------- lookup

@node("Lookup")
def _lookup(ip, el, fr):
    """Table lookup keyed by `Keys`, in filed row order (contract §7)."""
    where = ip.where(el)
    name = el.attrib.get("MatrixFromConstant")
    col = el.attrib.get("MatrixCol")
    mode = el.attrib.get("ResultMode", "FirstResult")
    if not name or not col:
        raise InterpretError(
            "Lookup without @MatrixFromConstant or @MatrixCol", "§7", where)
    if mode not in ("FirstResult", "SingleResult"):
        raise InterpretError(
            f"Lookup @ResultMode={mode!r} was never filed", "§12.2", where)

    keys_el = _only(el, ip)
    if ip.tag(keys_el) != "Keys":
        raise InterpretError("Lookup's child is not Keys", "§7", where)
    keys = [ip.eval(k, fr) for k in _kids(keys_el)]

    return ip.lookup(name, col, keys, mode, el.attrib.get("Type", "string"),
                     where)


@node("Keys")
def _keys(ip, el, fr):                       # evaluated by Lookup itself
    raise InterpretError("Keys outside a Lookup", "§7", ip.where(el))


# ------------------------------------------------------------------- dispatch

@node("RunRule")
def _run_rule(ip, el, fr):
    """Call a rule; never memoised (contract C3, §8).

    `@ClearCache` is `true` on all 173,204 occurrences, so the corpus never asks
    for a cached call and `false` is a hard failure rather than an optimisation.
    """
    where = ip.where(el)
    cache = el.attrib.get("ClearCache")
    if cache not in (None, "true"):
        raise InterpretError(
            f"RunRule @ClearCache={cache!r} was never filed; the interpreter "
            f"does not memoise and will not start", "§12.2", where)

    file_name = el.attrib.get("FileName")
    rule_name = el.attrib.get("Rule")
    if not file_name or not rule_name:
        raise InterpretError(
            "RunRule without @FileName or @Rule", "§8", where)

    args = {}
    for ch in _kids(el):
        if ip.tag(ch) != "Arg":
            raise InterpretError(
                f"RunRule holds a {ip.tag(ch)}", "§8", where)
        args.update(_arg_binding(ip, ch, fr))

    return ip.call(file_name, rule_name, el.attrib.get("ProjectName"),
                   args, fr, where)


def _arg_binding(ip, el, fr) -> dict:
    """`Arg` binds one parameter, evaluated in the CALLER's frame (§8)."""
    name = el.attrib.get("Param")
    if not name:
        raise InterpretError("Arg without @Param", "§8", ip.where(el))
    return {name: ip.eval(_only(el, ip), fr)}


@node("Arg")
def _arg(ip, el, fr):
    raise InterpretError("Arg outside a call or WithArgs", "§8", ip.where(el))


@node("WithArgs")
def _with_args(ip, el, fr):
    """Bind parameters around a body (contract §8).

    Args come first and are evaluated in the enclosing frame; every remaining
    child is the body, evaluated with the bindings visible.
    """
    bindings = {}
    body = []
    for ch in _kids(el):
        if ip.tag(ch) == "Arg":
            if body:
                raise InterpretError(
                    "WithArgs has an Arg after the body began", "§8",
                    ip.where(el))
            bindings.update(_arg_binding(ip, ch, fr))
        else:
            body.append(ch)
    inner = fr.with_params(bindings)
    out = None
    for ch in body:
        out = ip.eval(ch, inner)
    return out


# ------------------------------------------------------------------ iteration

@node("ForEach")
def _for_each(ip, el, fr):
    """Iterate in filed document order (contract §9).

    An absent or empty path iterates zero times and is not an error -- that is
    how an absent coverage disappears rather than raising.
    """
    path = el.attrib.get("AtDataDef") or el.attrib.get("AtInputDataDef")
    if path is None:
        raise InterpretError(
            "ForEach without @AtDataDef or @AtInputDataDef", "§9",
            ip.where(el))
    yielded = []
    for item in tree.select(path, fr.data):
        inner = fr.at(item)
        out = None
        try:
            for ch in _kids(el):
                out = ip.eval(ch, inner)
        except BreakLoop:
            yielded.append(out)
            break
        yielded.append(out)
    # A collection, not the last value: `Sum` over a `ForEach` must total every
    # iteration. Statement contexts discard it, so this is free there.
    return Multi(yielded)


@node("GetList")
def _get_list(ip, el, fr):
    """Two occurrences in two packages -- the whole tail (contract §10)."""
    out = None
    try:
        for ch in _kids(el):
            out = ip.eval(ch, fr)
    except BreakLoop:
        pass
    return out


# --------------------------------------------------------------- output tree

@node("Locate")
def _locate(ip, el, fr):
    """Position subsequent writes (contract §9).

    `@OutputAction` is `Append` on all 9,011 that carry it; absent means
    position at the existing node.
    """
    where = ip.where(el)
    action = el.attrib.get("OutputAction")
    if action not in (None, "Append"):
        raise InterpretError(
            f"Locate @OutputAction={action!r} was never filed", "§12.2", where)

    path = (el.attrib.get("AtOutputDataDef") or el.attrib.get("AtDataDef")
            or el.attrib.get("AtInputDataDef"))
    if path is None:
        raise InterpretError("Locate without a path", "§9", where)

    if action == "Append" and not path.endswith("]"):
        # An unpredicated Append genuinely adds a row -- the `Policy` node in
        # the Default block is the case.
        parent_path, _, leaf = path.rpartition("/")
        base = tree.ensure(parent_path, fr.data) if parent_path else fr.data
        target = base.add(leaf)
    else:
        # A predicated Append addresses one specific row, and 8,014 of the
        # 9,012 Append paths carry `[1]`. It means "make sure row 1 is there",
        # which has to be idempotent: ISO appends and then immediately reads
        # the same `[1]` back, and its own output carries exactly one row.
        target = tree.ensure(path, fr.data)

    inner = fr.at(target)
    out = None
    for ch in _kids(el):
        out = ip.eval(ch, inner)
    return out


@node("Remove")
def _remove(ip, el, fr):
    """Always all-matching (contract C5): `@RemoveMultiple` is true on all."""
    where = ip.where(el)
    mult = el.attrib.get("RemoveMultiple")
    if mult not in (None, "true"):
        raise InterpretError(
            f"Remove @RemoveMultiple={mult!r} was never filed", "§12.2", where)
    path = el.attrib.get("AtDataDef")
    if path is None:
        raise InterpretError("Remove without @AtDataDef", "§9", where)
    for n in tree.select(path, fr.data):
        if n.parent is not None:
            n.parent.children.remove(n)
    return None


@node("Copy")
def _copy(ip, el, fr):
    """Copy a value to `@ToDataDef` (contract §9)."""
    where = ip.where(el)
    typ = el.attrib.get("Type", "string")
    if "FromParam" in el.attrib:
        name = el.attrib["FromParam"]
        if not fr.has_param(name):
            raise InterpretError(
                f"parameter {name!r} is not bound here", "§8", where)
        return coerce(fr.param(name), typ, where)
    path = el.attrib.get("FromDataDef")
    if path is None:
        raise InterpretError(
            "Copy with neither @FromDataDef nor @FromParam", "§9", where)
    return coerce(tree.read(path, fr.data), typ, where)


@node("Guid")
def _guid(ip, el, fr):
    """Seeded, not random (contract §9).

    The only non-deterministic node in the language, and its whole job in this
    corpus is identifying a message row -- so a per-run counter keeps two runs
    of the same submission byte-identical and the Phase 2 RAaS diff free of
    false positives.
    """
    return ip.next_guid()


# ----------------------------------------------------------------- arithmetic

@node("Sum")
def _sum(ip, el, fr):
    """Total every operand, spreading a `ForEach` over its iterations (§6)."""
    total = Decimal(0)
    for ch in _kids(el):
        for v in flatten(ip.eval(ch, fr)):
            if v is None:
                continue                   # an absent addend contributes nothing
            total += ip.num(v, ip.where(ch))
    return total


@node("Product")
def _product(ip, el, fr):
    out = None
    for ch in _kids(el):
        v = ip.num(ip.eval(ch, fr), ip.where(ch))
        out = v if out is None else out * v
    return ip.round_to(out, el, ip.where(el))


@node("Subtract")
def _subtract(ip, el, fr):
    a, b = _two(el, ip)
    return (ip.num(ip.eval(a, fr), ip.where(el))
            - ip.num(ip.eval(b, fr), ip.where(el)))


@node("Divide")
def _divide(ip, el, fr):
    a, b = _two(el, ip)
    x = ip.num(ip.eval(a, fr), ip.where(el))
    y = ip.num(ip.eval(b, fr), ip.where(el))
    if y == 0:
        raise InterpretError("division by zero", "§12.5", ip.where(el))
    return ip.round_to(x / y, el, ip.where(el))


@node("Max")
def _max(ip, el, fr):
    """Largest operand, spreading a `ForEach` (§6).

    The corpus idiom is `Max(ForEach(...), Constant 0)` -- the highest minimum
    premium across every classification, floored at zero. With no locations the
    `ForEach` yields nothing and the constant carries it, which is why an empty
    iteration must contribute no operands rather than one null.
    """
    vals = [v for ch in _kids(el) for v in flatten(ip.eval(ch, fr))
            if v is not None]
    if not vals:
        return None
    return max(ip.num(v, ip.where(el)) for v in vals)


@node("Round")
def _round(ip, el, fr):
    v = ip.num(ip.eval(_only(el, ip), fr), ip.where(el))
    return ip.round_to(v, el, ip.where(el), required=True)


@node("Truncate")
def _truncate(ip, el, fr):
    v = ip.num(ip.eval(_only(el, ip), fr), ip.where(el))
    return Decimal(int(v))


@node("Count")
def _count(ip, el, fr):
    path = el.attrib.get("AtInputDataDef", "")
    return len(tree.select(path, fr.data))


# -------------------------------------------------------- strings and dates

@node("Concat")
def _concat(ip, el, fr):
    a, b = _two(el, ip)
    return to_text(ip.eval(a, fr)) + to_text(ip.eval(b, fr))


@node("Length")
def _length(ip, el, fr):
    return len(to_text(ip.eval(_only(el, ip), fr)))


@node("PadLeft")
def _pad_left(ip, el, fr):
    """Fixed-width statistical codes, not arithmetic (contract §10)."""
    ch = _kids(el)
    if len(ch) != 3:
        raise InterpretError(
            f"PadLeft takes three children, found {len(ch)}", "§10",
            ip.where(el))
    text = to_text(ip.eval(ch[0], fr))
    width = int(ip.num(ip.eval(ch[1], fr), ip.where(el)))
    fill = to_text(ip.eval(ch[2], fr)) or " "
    return text.rjust(width, fill[0])


@node("Convert")
def _convert(ip, el, fr):
    typ = el.attrib.get("Type", "string")
    v = ip.eval(_only(el, ip), fr)
    return coerce(to_text(v) if v is not None else None, typ, ip.where(el))


def _unit(el, ip):
    u = el.attrib.get("UnitType")
    if u not in ("Days", "Months", "Years"):
        raise InterpretError(
            f"@UnitType={u!r} was never filed", "§12.2", ip.where(el))
    return u


@node("DatePart")
def _date_part(ip, el, fr):
    v = ip.eval(_only(el, ip), fr)
    if not isinstance(v, _dt.date):
        raise InterpretError(
            f"DatePart of a {type(v).__name__}", "§10", ip.where(el))
    return {"Days": v.day, "Months": v.month, "Years": v.year}[_unit(el, ip)]


def _add_years(d: _dt.date, n: int) -> _dt.date:
    try:
        return d.replace(year=d.year + n)
    except ValueError:                       # 29 February
        return d.replace(year=d.year + n, day=28)


@node("DateAdd")
def _date_add(ip, el, fr):
    """`ExpDate = EffDate + 1 year` in all 567 packages (contract §2)."""
    a, b = _two(el, ip)
    d = ip.eval(a, fr)
    if not isinstance(d, _dt.date):
        raise InterpretError(
            f"DateAdd on a {type(d).__name__}", "§10", ip.where(el))
    n = int(ip.num(ip.eval(b, fr), ip.where(el)))
    unit = _unit(el, ip)
    if unit == "Days":
        return d + _dt.timedelta(days=n)
    if unit == "Years":
        return _add_years(d, n)
    month = d.month - 1 + n
    year = d.year + month // 12
    month = month % 12 + 1
    day = min(d.day, [31, 29 if year % 4 == 0 and (year % 100 or year % 400
                                                   == 0) else 28,
                      31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
    return _dt.date(year, month, day)


@node("DateCreate")
def _date_create(ip, el, fr):
    ch = _kids(el)
    if len(ch) != 3:
        raise InterpretError(
            f"DateCreate takes three children, found {len(ch)}", "§10",
            ip.where(el))
    y, m, d = (int(ip.num(ip.eval(c, fr), ip.where(el))) for c in ch)
    return _dt.date(y, m, d)


@node("DateDifference")
def _date_difference(ip, el, fr):
    a, b = _two(el, ip)
    x, y = ip.eval(a, fr), ip.eval(b, fr)
    if not isinstance(x, _dt.date) or not isinstance(y, _dt.date):
        raise InterpretError("DateDifference on a non-date", "§10",
                             ip.where(el))
    if _unit(el, ip) != "Days":
        raise InterpretError(
            "DateDifference @UnitType is Days on all 30 occurrences",
            "§12.2", ip.where(el))
    return (x - y).days


# ======================================================================
# Commercial Property
# ======================================================================
#
# ISO files one rule language, not one per line of business, and the Property
# corpus proves it: 60 distinct `rul:` element names against General
# Liability's 58, with the same semantics everywhere the two overlap. The five
# below are what Property files and GL does not.
#
# **Adding them cannot change a GL rating.** None of the five occurs anywhere
# in the GL corpus -- enumerated over both corpora, every edition -- so each of
# these evaluators is unreachable from a GL book. That is the argument for
# extending this module rather than forking it, and it is measured rather than
# hoped.
#
# Two of the five are refusals. A refusal here is not a stub: it is a named
# error at the exact element, which is the only outcome that keeps contract
# 12.1's promise when ISO files something the engine has not been taught.
#
# Per-edition census of the Property corpus, all eight edition folders:
#
#     element        2019  2020  2022  23v1  23v2  23v3  23v4  2026
#     Power             2     4     2     2     2     2     2     2
#     LastNonNull       0     3     0     1     0     1     2     3
#     Custom            0     0     2     0     2     2     2     2
#     Null             12     3     0    20     0     0     0     0
#     FromList          0     6     2     2     4     4     0     0
#
# `Null` and `FromList` are retired -- absent from the current edition
# entirely. They are still handled because the engine resolves by as-of date,
# and an as-of before 2022-10 lands on an edition that files them.


@node("Null")
def _null(ip, el, fr):
    """An explicit typed null literal (Property only).

    Worth being exact about why this needs an evaluator rather than being read
    as "nothing here": the element is how ISO writes *deliberately absent*, as
    against a branch that merely happened not to assign. It declares a `@Type`,
    and the value it produces is `None` -- which `IsNull` answers true for and
    which arithmetic refuses, exactly as contract 12.3 requires.

    Returning `None` is the whole behaviour. Returning zero would be the
    specific corruption `values.py` exists to prevent.
    """
    typ = el.attrib.get("Type", "none")
    if typ not in TYPES:
        raise InterpretError(f"Null declares @Type={typ!r}", "§12.2",
                             ip.where(el))
    if _kids(el):
        raise InterpretError(
            f"Null holds {len(_kids(el))} children; it is a literal", "§4",
            ip.where(el))
    ip.note("null-literal", f"explicit null typed {typ}", ip.where(el))
    return None


@node("Power")
def _power(ip, el, fr):
    """`base ** exponent` -- the only exponentiation in either corpus.

    Two children, base then exponent, in filed order. Every occurrence is
    Leasehold Interest discounting a lease's remaining months to present value
    (`DiscFactor ** NumOfMonthsRemaining`), and the exponent arrives through a
    `Convert Type="decimal"` rather than as an integer -- so a whole-number-only
    implementation would be wrong for the one thing this element is used for.

    `Decimal.__pow__` takes a fractional exponent only for a positive base,
    which is all the corpus files: a discount factor. A non-positive base with
    a fractional exponent is refused rather than approximated through floats,
    because N10 applies here more than anywhere -- this is the one operator
    whose error compounds.
    """
    a, b = _two(el, ip)
    where = ip.where(el)
    base = ip.num(ip.eval(a, fr), where)
    exp = ip.num(ip.eval(b, fr), where)
    if base <= 0 and exp != int(exp):
        raise InterpretError(
            f"Power with base {base} and fractional exponent {exp} is not "
            f"real-valued; the corpus files only positive bases", "§6", where)
    try:
        out = base ** exp
    except (InvalidOperation, OverflowError, ValueError) as exc:
        raise InterpretError(f"Power({base}, {exp}) is undefined: {exc}",
                             "§6", where) from None
    return ip.round_to(out, el, where)


@node("LastNonNull")
def _last_non_null(ip, el, fr):
    """The LAST non-null value across every child, or null if there is none.

    `FirstNonNull`'s mirror, and the difference is not cosmetic. Every
    occurrence wraps a nested `ForEach` over locations and structures -- the
    idiom is "the last structure that named a mine-subsidence limit" -- so the
    element exists precisely to reach past the first answer to the final one.
    Short-circuiting on the first non-null, which is how this gets written by
    analogy, returns a different row's value and raises nothing.

    So every child is evaluated, in filed order, and nothing is skipped.

    `NullInArithmetic` is absorbed per branch for the same reason C6 absorbs it
    in `FirstNonNull` (OI-88): this construct declares a null branch legal, and
    a branch that reached null through arithmetic produced nothing rather than
    failed. Every other refusal still escapes.
    """
    found = None
    seen = False
    for idx, ch in enumerate(_kids(el)):
        try:
            vals = flatten(ip.eval(ch, fr))
        except NullInArithmetic as exc:
            ip.trace_branch_abandoned(el, idx, exc)
            continue
        for v in vals:
            if v is not None and v != "":
                found, seen = v, True
    if not seen:
        ip.trace_exhausted(el)
    return found


@node("Custom")
def _custom(ip, el, fr):
    """A call into ISO's own .NET runtime. Refused by name, never guessed.

    Every occurrence in the corpus is the same method::

        AssemblyName="Mscl.RuleBook.Runtime"
        Namespace="Mscl.RuleBook.Runtime.RuleSet.Custom.DateFunctions"
        ClassName="DateFunctionManager" MethodName="GetLeapDays"

    This is not an operator with filed semantics -- it is a host function whose
    body ISO ships as compiled code and does not publish. Reimplementing it
    from its name is the guess this engine refuses to make: a leap-day count
    has several defensible conventions over a policy term, they disagree by a
    day, and a Builders Risk premium adjustment pro-rates on the answer.

    Reachable only from Builders Risk premium adjustment. Refusing costs that
    one coverage and protects every other.
    """
    method = el.attrib.get("MethodName", "?")
    cls = el.attrib.get("ClassName", "?")
    raise InterpretError(
        f"Custom calls {cls}.{method} in {el.attrib.get('AssemblyName', '?')}, "
        f"a host function ISO ships as compiled code and does not publish. The "
        f"engine does not reimplement it from its name",
        "§12.1", ip.where(el))


@node("FromList")
def _from_list(ip, el, fr):
    """A loop-variable binder for a bare `ForEach`. Refused, with the reason.

    The shape is always the same: a `ForEach` carrying NO `@AtDataDef`, whose
    first child is this element, which names a `@Param` and holds a `GetList`
    of the values to iterate. So it is not a value-producing operator at all --
    it iterates a *parameter list* rather than a path into the data tree, and
    binds each element to a new parameter for the loop body.

    Supporting it means extending `ForEach`'s iteration model to a second
    source, which is a change to an evaluator GL shares. That change is not
    made on speculation: `FromList` is retired -- zero occurrences in the
    current edition -- and every live use is Blanket rating, which is its own
    build chunk. It gets built when that chunk needs it, against that chunk's
    evidence.

    Until then this raises rather than returning something. A bare `ForEach`
    already refuses by name, so neither half of the construct passes silently.
    """
    raise InterpretError(
        f"FromList binds @Param={el.attrib.get('Param')!r} for a bare ForEach "
        f"over a parameter list; that iteration model is not built. Reachable "
        f"only from Blanket rating, and only at editions before 20230801 V04",
        "§12.1", ip.where(el))
