"""Evaluate the conditions in ISO's field file (`RequiredCondition`, `Condition`) against the data tree.

ISO writes them in a slice of XPath 1.0, relative to the row of the field's own table:

    Subline[.='Premises/Operations and Products/Completed Operations']
    (../../../../Subline[.='Product Withdrawal']) and (ClassCode[.='10011' or .='10020'])
    ../../../../Subline[.='...'] and PremOpsPDDeductible[contains(.,'Per Claim')]

Measured over every GL state's 2027 book (OI-134, 2026-10-13): 227 distinct conditions, built from location
paths (`..`, `.`, child names), predicates, `or`, `and`, `=`, `!=`, `<`, `<=`, `>`, `>=`, `contains()`,
`count()` and `not()`. That is all this implements. **Anything else raises `ConditionError`**, and a caller
reports the condition as not evaluated rather than guessing at it -- the same rule `fields.py` applied when it
evaluated none of them.

Standard library only: the Mac package runs on the system Python, so lxml is not an option.

The data tree has ISO's `XTable` wrappers (`GeneralLiabilityLocationTable/GeneralLiabilityLocation`), so `..`
counts the same steps ISO's XML does: from a classification row, `../../../../Subline` is the policy's.
"""
from __future__ import annotations

import re

_TOKEN = re.compile(r"""
    \s*(?:
      (?P<str>'[^']*'|"[^"]*")
    | (?P<num>\d+(?:\.\d+)?)
    | (?P<op>!=|<=|>=|=|<|>|\(|\)|\[|\]|,|/)
    | (?P<dotdot>\.\.)
    | (?P<dot>\.)
    | (?P<name>[A-Za-z_][\w.\-]*)
    )""", re.X)

FUNCTIONS = ("contains", "count", "not")


class ConditionError(ValueError):
    """A condition outside the slice this evaluates. Report it as not evaluated; never guess."""


def _tokens(text: str) -> list:
    out, pos = [], 0
    text = text.strip()
    while pos < len(text):
        m = _TOKEN.match(text, pos)
        if not m or m.end() == pos:
            raise ConditionError(f"cannot read {text[pos:pos + 20]!r} in {text[:80]!r}")
        kind = m.lastgroup
        val = m.group(kind)
        out.append((kind, val))
        pos = m.end()
        while pos < len(text) and text[pos].isspace():
            pos += 1
    return out


class _Parser:
    """Recursive descent over the token list into a small tree of tuples."""

    def __init__(self, text: str):
        self.text = text
        self.t = _tokens(text)
        self.i = 0

    def peek(self, k=0):
        j = self.i + k
        return self.t[j] if j < len(self.t) else (None, None)

    def take(self, val=None):
        kind, v = self.peek()
        if val is not None and v != val:
            raise ConditionError(f"expected {val!r}, found {v!r} in {self.text[:80]!r}")
        self.i += 1
        return kind, v

    def parse(self):
        e = self.or_()
        if self.i != len(self.t):
            raise ConditionError(f"unread {self.peek()[1]!r} in {self.text[:80]!r}")
        return e

    def or_(self):
        e = self.and_()
        while self.peek() == ("name", "or"):
            self.take()
            e = ("or", e, self.and_())
        return e

    def and_(self):
        e = self.cmp()
        while self.peek() == ("name", "and"):
            self.take()
            e = ("and", e, self.cmp())
        return e

    def cmp(self):
        e = self.unary()
        kind, v = self.peek()
        if kind == "op" and v in ("=", "!=", "<", "<=", ">", ">="):
            self.take()
            e = ("cmp", v, e, self.unary())
        return e

    def unary(self):
        kind, v = self.peek()
        if v == "(":
            self.take()
            e = self.or_()
            self.take(")")
            return self.predicates(("group", e))
        if kind == "str":
            self.take()
            return ("lit", v[1:-1])
        if kind == "num":
            self.take()
            return ("lit", float(v))
        if kind == "name" and self.peek(1)[1] == "(":
            if v not in FUNCTIONS:
                raise ConditionError(f"function {v}() is not in the evaluated slice: {self.text[:80]!r}")
            self.take()
            self.take("(")
            args = [] if self.peek()[1] == ")" else [self.or_()]
            while self.peek()[1] == ",":
                self.take()
                args.append(self.or_())
            self.take(")")
            return ("fn", v, args)
        return self.path()

    def path(self):
        steps = [self.step()]
        while self.peek()[1] == "/":
            self.take()
            steps.append(self.step())
        return ("path", steps)

    def step(self):
        kind, v = self.peek()
        if kind not in ("dotdot", "dot", "name"):
            raise ConditionError(f"expected a path step, found {v!r} in {self.text[:80]!r}")
        self.take()
        return self.predicates(("step", v))

    def predicates(self, node):
        preds = []
        while self.peek()[1] == "[":
            self.take()
            preds.append(self.or_())
            self.take("]")
        return node + (tuple(preds),) if preds else node


_CACHE: dict = {}


def compile_condition(text: str):
    """Parse once; the same few hundred conditions are evaluated on every rating."""
    tree = _CACHE.get(text)
    if tree is None:
        tree = _CACHE[text] = _Parser(text).parse()
    return tree


# ------------------------------------------------------------------ evaluation

def _text(node) -> str:
    return "" if node is None or node.text is None else str(node.text)


def _strings(v) -> list:
    if isinstance(v, list):
        return [_text(n) for n in v]
    if isinstance(v, bool):
        return ["true" if v else "false"]
    if isinstance(v, float):
        return [str(int(v)) if v == int(v) else str(v)]
    return [str(v)]


def _truth(v) -> bool:
    if isinstance(v, list):
        return bool(v)
    if isinstance(v, str):
        return v != ""
    if isinstance(v, float):
        return v != 0
    return bool(v)


def _num(s):
    try:
        return float(str(s).replace(",", ""))
    except ValueError:
        return None


def _compare(op: str, a, b) -> bool:
    """XPath 1.0 general comparison: true if any pair of operand values compares true."""
    if op in ("=", "!="):
        for x in _strings(a):
            for y in _strings(b):
                if (x == y) == (op == "="):
                    return True
        return False
    for x in _strings(a):
        for y in _strings(b):
            nx, ny = _num(x), _num(y)
            if nx is None or ny is None:
                continue
            if {"<": nx < ny, "<=": nx <= ny, ">": nx > ny, ">=": nx >= ny}[op]:
                return True
    return False


def _filter(nodes: list, preds: tuple) -> list:
    for p in preds:
        nodes = [n for n in nodes if _truth(_eval(p, n))]
    return nodes


def _eval(e, ctx):
    kind = e[0]
    if kind == "lit":
        return e[1]
    if kind == "or":
        return _truth(_eval(e[1], ctx)) or _truth(_eval(e[2], ctx))
    if kind == "and":
        return _truth(_eval(e[1], ctx)) and _truth(_eval(e[2], ctx))
    if kind == "cmp":
        return _compare(e[1], _eval(e[2], ctx), _eval(e[3], ctx))
    if kind == "group":
        v = _eval(e[1], ctx)
        return _filter(v, e[2]) if len(e) > 2 and isinstance(v, list) else v
    if kind == "fn":
        name, args = e[1], [_eval(a, ctx) for a in e[2]]
        if name == "contains":
            if len(args) != 2:
                raise ConditionError("contains() takes two arguments")
            hay = _strings(args[0])[:1] or [""]
            return _strings(args[1])[0] in hay[0]
        if name == "count":
            if len(args) != 1 or not isinstance(args[0], list):
                raise ConditionError("count() takes one node-set")
            return float(len(args[0]))
        if name == "not":
            return not _truth(args[0])
    if kind == "path":
        nodes = [ctx]
        for step in e[1]:
            name = step[1]
            nxt = []
            for n in nodes:
                if name == ".":
                    nxt.append(n)
                elif name == "..":
                    if n.parent is not None:
                        nxt.append(n.parent)
                else:
                    nxt.extend(c for c in n.children if c.tag == name)
            nodes = _filter(nxt, step[2]) if len(step) > 2 else nxt
        return nodes
    raise ConditionError(f"cannot evaluate {kind!r}")


def holds(text: str, row) -> bool:
    """Whether ISO's condition `text` holds for `row` (a node of the field's table). Raises ConditionError."""
    return _truth(_eval(compile_condition(text), row))
