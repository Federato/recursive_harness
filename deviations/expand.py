"""Authored rows -> explicit keys -> one composed value per key (M5, D7).

**Expansion.** Every row is expanded, at compile time, to the explicit keys of
the ISO edition it applies to: a class group becomes its classes, "all classes"
becomes every class the edition has, `LCM:All` becomes every LCM target of the
line, and an unscoped rating basis becomes both. The engine then never has to
interpret a group, a range or a shortcut -- it reads exact keys, as it reads
ISO's own tables.

**Composition, per key.** Of the rows that reach a key:

  * the most specific `replace` row sets the value (none: ISO's own value
    stands as the base);
  * every `multiply` row at that specificity or more specific multiplies it;
  * less specific rows are overridden at that key, which is what lets a filing
    say "1.511 for all classes, 1.067 for class group A".

Two `replace` rows that reach the same key at the same specificity are a
contradiction the filing must resolve; it is reported, never broken by row
order.

**Specificity** counts how narrowly a row was written: naming one LCM target
rather than `All` (+1), a class (+2) or a class group (+1), a rating basis
(+1); for a table override, each key column it pins (+1).

Every composed key keeps an `explain` string naming each row that contributed,
its mode and its value. That string is what makes the compiled form readable
back into authored rows (`show`), and what the engine's trace will cite.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from itertools import product

from . import iso
from .config import LCM_SCOPE_KEYS, LCM_SCOPE_LATER, LCM_TARGETS, RATING_BASES
from .files import Row


@dataclass
class Context:
    """What a filing's rows are expanded against, for one jurisdiction."""

    line: str
    juris: str
    date: str                                   # the new-business effective date
    class_groups: dict[str, list[str]]          # name -> expanded codes
    classes: tuple[str, ...] = ()

    def __post_init__(self):
        if not self.classes:
            self.classes = iso.class_codes(self.line, self.juris, self.date)


@dataclass
class Expanded:
    row: Row
    space: tuple                                # ('LCM',) or ('TABLE', name, col)
    keys: list[tuple] = field(default_factory=list)
    spec: int = 0
    problems: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def parse_target(target: str, line: str):
    """'LCM:GroupI' -> ('LCM', 'GroupI'); 'TABLE:X.Factor' -> ('TABLE', 'X', 'Factor')."""
    kind, _, rest = target.partition(":")
    if kind == "LCM":
        if rest == "All" or rest in LCM_TARGETS.get(line, ()):
            return ("LCM", rest)
        return None
    if kind == "TABLE":
        name, _, col = rest.rpartition(".")
        if name and col:
            return ("TABLE", name, col)
    return None


def lcm_header(line: str) -> list[str]:
    """Key columns of the compiled LCM table, StateCode first, as ISO keys tables."""
    if line == "CF":
        return ["StateCode", "Group", "RatingBasis", "ClassCode"]
    return ["StateCode", "Coverage", "ClassCode"]


def lcm_universe(ctx: Context) -> list[tuple]:
    """Every explicit LCM key the line has in this edition (StateCode omitted)."""
    targets = LCM_TARGETS[ctx.line]
    if ctx.line == "CF":
        return list(product(targets, RATING_BASES, ctx.classes))
    return list(product(targets, ctx.classes))


def expand(row: Row, ctx: Context) -> Expanded:
    t = parse_target(row.target, ctx.line)
    if t is None:
        e = Expanded(row, ())
        e.problems.append(f"target {row.target!r} is not one {ctx.line} has "
                          f"(LCM:{'|'.join(('All',) + LCM_TARGETS.get(ctx.line, ()))} "
                          f"or TABLE:<table>.<value column>)")
        return e
    if t[0] == "LCM":
        return _expand_lcm(row, t[1], ctx)
    return _expand_table(row, t[1], t[2], ctx)


def _expand_lcm(row: Row, target: str, ctx: Context) -> Expanded:
    e = Expanded(row, ("LCM",))
    allowed = LCM_SCOPE_KEYS[ctx.line]
    for k in row.scope:
        if k in LCM_SCOPE_LATER:
            e.problems.append(f"scope {k!r} on an LCM is not supported yet "
                              f"(arrives with the GL engine step, P2)")
        elif k not in allowed:
            e.problems.append(f"scope {k!r} is not an LCM scope for {ctx.line} "
                              f"(allowed: {', '.join(allowed)})")
    if "class" in row.scope and "class_group" in row.scope:
        e.problems.append("scope names both a class and a class group")
    if e.problems:
        return e

    targets = LCM_TARGETS[ctx.line] if target == "All" else (target,)
    e.spec = 0 if target == "All" else 1

    if "class" in row.scope:
        c = str(row.scope["class"])
        if c not in ctx.classes:
            e.problems.append(f"class {c} is not a class in {ctx.juris}'s edition")
            return e
        classes, e.spec = [c], e.spec + 2
    elif "class_group" in row.scope:
        g = str(row.scope["class_group"])
        if g not in ctx.class_groups:
            e.problems.append(f"class group {g!r} is not defined for this company "
                              f"(carrier.json or company.json)")
            return e
        classes, e.spec = ctx.class_groups[g], e.spec + 1
    else:
        classes = list(ctx.classes)

    if ctx.line == "CF":
        if "rating_basis" in row.scope:
            b = str(row.scope["rating_basis"])
            if b not in RATING_BASES:
                e.problems.append(f"rating basis {b!r} is not one of {', '.join(RATING_BASES)}")
                return e
            bases, e.spec = [b], e.spec + 1
        else:
            bases = list(RATING_BASES)
        e.keys = list(product(targets, bases, classes))
    else:
        e.keys = list(product(targets, classes))
    return e


def _expand_table(row: Row, name: str, col: str, ctx: Context) -> Expanded:
    e = Expanded(row, ("TABLE", name, col))
    try:
        t = iso.table(ctx.line, ctx.juris, ctx.date, name)
    except Exception:
        e.problems.append(f"ISO has no rate table {name!r} in {ctx.juris}'s edition")
        return e
    if iso.is_banded(t):
        e.problems.append(f"{name} is banded; v1 overrides exact-keyed tables only")
        return e
    if col not in iso.value_cols(t):
        e.problems.append(f"{name} has no value column {col!r} "
                          f"(has: {', '.join(iso.value_cols(t))})")
        return e
    keys = iso.table_keys(t)
    unknown = [k for k in row.scope if k not in keys]
    if unknown:
        e.problems.append(f"{name} has no key column {', '.join(map(repr, unknown))} "
                          f"(keys: {', '.join(keys)})")
        return e
    idx = [t.col(k) for k in keys]
    want = {t.col(k): str(v) for k, v in row.scope.items()}
    found = {tuple(str(r[i]) for i in idx) for r in t.rows
             if all(str(r[i]) == v for i, v in want.items())}
    if not found:
        e.problems.append(f"ISO's {name} has no row with "
                          + ", ".join(f"{k}={v}" for k, v in row.scope.items()))
        return e
    e.keys, e.spec = sorted(found), len(row.scope)
    # A scope key that narrows nothing still raises the row's specificity, and
    # `show` cannot tell it was written: say so rather than let it surprise.
    for k in row.scope:
        rest = {t.col(x): str(v) for x, v in row.scope.items() if x != k}
        if len({tuple(str(r[i]) for i in idx) for r in t.rows
                if all(str(r[i]) == v for i, v in rest.items())}) == len(found):
            e.notes.append(f"scope {k}={row.scope[k]} narrows nothing in {ctx.juris}'s "
                           f"{name} (every row it reaches has that value)")
    return e


# ----------------------------------------------------------- composition

@dataclass
class Composed:
    value: Decimal
    mode: str                  # 'replace' (value is final) or 'multiply' (ISO x value)
    explain: str


def canon(d: Decimal) -> str:
    """One spelling per number, so 3.280 typed from a PDF and 3.28 typed into a
    sheet compile to the same bytes: trailing zeros dropped, never an exponent."""
    return format(d.normalize(), "f")


def token(row: Row) -> str:
    return f"{row.id}:{row.mode}:{canon(row.value)}"


def compose(expanded: list[Expanded]) -> tuple[dict, list[str]]:
    """{space: {key: Composed}} for every key any row reaches, plus conflicts."""
    reach: dict = {}
    for e in expanded:
        if e.problems:
            continue
        sp = reach.setdefault(e.space, {})
        for k in e.keys:
            sp.setdefault(k, []).append(e)

    out: dict = {}
    conflicts: list[str] = []
    seen_pairs: set = set()
    for space, keys in reach.items():
        res = out.setdefault(space, {})
        for k, es in keys.items():
            reps = [x for x in es if x.row.mode == "replace"]
            top = max((x.spec for x in reps), default=None)
            winners = [x for x in reps if x.spec == top]
            if len(winners) > 1:
                pair = tuple(sorted(x.row.id for x in winners))
                if pair not in seen_pairs:
                    seen_pairs.add(pair)
                    conflicts.append(
                        f"rows {', '.join(pair)} both replace the same key "
                        f"({_fmt(space, k)}) at the same specificity")
                continue
            base = winners[0] if winners else None
            mults = [x for x in es if x.row.mode == "multiply"
                     and (base is None or x.spec >= base.spec)]
            value = base.row.value if base else Decimal(1)
            for m in mults:
                value *= m.row.value
            parts = ([base] if base else []) + sorted(mults, key=lambda x: x.row.id)
            res[k] = Composed(value, "replace" if base else "multiply",
                              " * ".join(token(x.row) for x in parts))
    return out, conflicts


def _fmt(space, key) -> str:
    if space[0] == "LCM":
        return "LCM " + "/".join(key)
    return f"{space[1]}.{space[2]} " + "/".join(key)
