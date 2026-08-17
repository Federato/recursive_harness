"""The runtime value model: five types, and a null that is not zero.

Contract sections 1 and 4 (`docs/rating-engine/14-EVALUATION-CONTRACT.md`).

Two rules here carry most of the risk in the whole interpreter.

**Decimal, never float (N10).** A float `0.1` is not one tenth, and a rating
engine multiplies. Every decimal value in this module is a `decimal.Decimal`
constructed from the *string* ISO filed, never via `float`.

**Null is a value, and it is neither zero nor the empty string.** ISO
distinguishes them deliberately -- `IsNull`, `Exist` and `AllowNullReturn` all
exist so a rule can ask which it has. Folding null into zero is how a missing
coverage becomes a free one. Null is Python `None`; the empty string is `""`,
and the contract's Q1 established that every one of the corpus's 20,520 empty
`Constant`s is the second and not the first.
"""
from __future__ import annotations

import datetime as _dt
from decimal import Decimal, InvalidOperation

from ..errors import EngineError


class InterpretError(EngineError):
    """The interpreter met content it will not guess about.

    Deliberately a plain `EngineError` and not a `LoadError`: the corpus loaded
    fine, we simply refuse to invent a behaviour for it. Every raise site names
    the contract clause it is enforcing.
    """

    def __init__(self, message: str, clause: str = "", where: str = ""):
        self.clause = clause
        self.where = where
        bits = [message]
        if clause:
            bits.append(f"contract {clause}")
        if where:
            bits.append(f"at {where}")
        super().__init__(" -- ".join(bits))


class NullInArithmetic(InterpretError):
    """A null reached arithmetic -- §12.3, and the one refusal `FirstNonNull`
    is allowed to absorb.

    Its own type for one reason: `FirstNonNull` must be able to treat *this*
    failure as "the branch produced nothing, try the next one" **without**
    absorbing any other refusal. A bare `except InterpretError` around a branch
    would also swallow a `Multi` in a scalar position, a non-numeric string and
    a missing table, and the engine would answer where it should stop (OI-88).

    Nothing else catches it. Outside a `FirstNonNull` branch this stays exactly
    what it was: a refusal with its clause and location intact.
    """


class Multi(tuple):
    """The values one `ForEach` yielded, one per iteration.

    `ForEach` is not only a statement. In a value position it feeds an
    aggregator -- `Sum` takes a `ForEach` child 18,918 times, and `Max` and
    `FirstNonNull` take one too -- and the aggregator wants **every** iteration,
    not the last.

    Returning a scalar there is a silent wrong answer rather than an error: a
    `Sum` over five locations would quietly total one of them. So iteration
    yields this, and every aggregator flattens it explicitly. A `Multi` that
    reaches a scalar context is a hard failure, because that is a place the
    corpus never puts one and guessing which element was meant is unthinkable.
    """

    def __repr__(self) -> str:            # pragma: no cover - display only
        return f"Multi({list(self)!r})"


def flatten(v) -> list:
    """One operand as a list of scalars. A `Multi` spreads; anything else is one.

    Recursive, because `ForEach` nests 3,494 times in the corpus -- locations
    inside a risk, classifications inside a location -- and each outer iteration
    then yields the inner iteration's whole collection. Flattening one level
    would put a `Multi` into arithmetic.
    """
    if not isinstance(v, Multi):
        return [v]
    out: list = []
    for item in v:
        out.extend(flatten(item))
    return out


#: The five types the corpus declares. A sixth is a hard failure (contract §12).
TYPES = frozenset({"string", "decimal", "integer", "long", "dateTime", "none"})

#: `01/01/0001` is ISO's dateTime zero and appears on 1,642 `FirstValue`s. It is
#: a sentinel meaning "no date", not a date to compute with.
DATE_ZERO = "01/01/0001"

_DATE_FORMATS = ("%m/%d/%Y", "%Y-%m-%d", "%Y%m%d", "%m/%d/%Y %H:%M:%S")


def parse_date(raw: str) -> _dt.date | None:
    for fmt in _DATE_FORMATS:
        try:
            return _dt.datetime.strptime(raw.strip(), fmt).date()
        except ValueError:
            continue
    return None


def coerce(raw, typ: str, where: str = ""):
    """Turn filed text into a typed runtime value.

    `None` in, `None` out -- coercion never manufactures a value out of a null,
    because that is the same mistake as reading an empty table as zero.
    """
    if typ not in TYPES:
        raise InterpretError(f"unknown @Type {typ!r}", "§12.2", where)
    if raw is None:
        return None
    if isinstance(raw, (Decimal, int, _dt.date)) and not isinstance(raw, bool):
        return raw
    text = str(raw)

    if typ == "string":
        return text
    if typ == "none":
        return None

    stripped = text.strip()
    if stripped == "":
        # An empty numeric is not zero. Nothing in the corpus files one
        # (contract Q1: all 20,520 empty Constants are string-typed), so this
        # is reachable only from a DataDef, where it means absent.
        return None

    if typ in ("integer", "long"):
        try:
            return int(Decimal(stripped))
        except (InvalidOperation, ValueError):
            raise InterpretError(
                f"{stripped!r} is not {typ}", "§1", where) from None
    if typ == "decimal":
        try:
            return Decimal(stripped)          # from the STRING, never a float
        except InvalidOperation:
            raise InterpretError(
                f"{stripped!r} is not decimal", "§1", where) from None
    if typ == "dateTime":
        if stripped == DATE_ZERO:
            return None                       # the sentinel, not 1 Jan year 1
        d = parse_date(stripped)
        if d is None:
            raise InterpretError(
                f"{stripped!r} is not a date", "§1", where)
        return d
    raise InterpretError(f"unhandled @Type {typ!r}", "§12.2", where)


def to_text(v) -> str:
    """Render a runtime value the way ISO's own CSVs render it."""
    if v is None:
        return ""
    if isinstance(v, _dt.date):
        return v.strftime("%m/%d/%Y")
    if isinstance(v, Decimal):
        return format(v.normalize(), "f")
    return str(v)


def to_decimal(v, where: str = "") -> Decimal:
    """The only way a number enters arithmetic. Null does not become zero."""
    if isinstance(v, Multi):
        raise InterpretError(
            f"a ForEach yielding {len(v)} values reached a scalar position; "
            f"only Sum, Max and FirstNonNull aggregate one", "§9", where)
    if v is None:
        raise NullInArithmetic(
            "null reached arithmetic; the engine does not coerce it to zero",
            "§12.3", where)
    if isinstance(v, Decimal):
        return v
    if isinstance(v, int) and not isinstance(v, bool):
        return Decimal(v)
    if isinstance(v, str):
        s = v.strip()
        if s == "":
            raise InterpretError(
                "empty string reached arithmetic", "§12.3", where)
        try:
            return Decimal(s)
        except InvalidOperation:
            raise InterpretError(
                f"{v!r} is not numeric", "§12.3", where) from None
    raise InterpretError(f"{type(v).__name__} is not numeric", "§12.3", where)


def compare_key(v):
    """Normalise a value for equality against a table key or another value.

    ISO compares a typed runtime value against text filed in a CSV, so `1`,
    `1.0` and `"1"` have to meet. Numbers compare numerically; everything else
    compares as text. `CaseInsensitive` is `false` on all 67,661 key columns in
    the corpus, so case is significant and is not folded.
    """
    if v is None:
        return None
    if isinstance(v, bool):
        return v
    if isinstance(v, (Decimal, int)):
        return Decimal(v)
    if isinstance(v, _dt.date):
        return v
    s = str(v)
    try:
        return Decimal(s.strip())
    except (InvalidOperation, ValueError):
        return s


def equal(a, b) -> bool:
    """ISO's `Equal`. Two nulls are equal; a null and a value are not."""
    ka, kb = compare_key(a), compare_key(b)
    if ka is None or kb is None:
        return ka is None and kb is None
    if isinstance(ka, Decimal) != isinstance(kb, Decimal):
        return str(a) == str(b)               # one is text, compare as text
    return ka == kb


def truthy(v, where: str = "") -> bool:
    """A `Test`'s value as a boolean.

    Only genuine booleans are accepted. The corpus never puts a number where a
    condition belongs, and silently treating `0` as false is how a rate of zero
    becomes a control-flow decision.
    """
    if isinstance(v, bool):
        return v
    raise InterpretError(
        f"a condition evaluated to {type(v).__name__}, not a boolean",
        "§5", where)
