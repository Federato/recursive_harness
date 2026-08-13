"""The data tree, and the paths that address it.

A submission, and the working state a rating builds on top of it, is one tree of
named nodes. ISO addresses it with a small path language -- `EffDate`,
`State/Code`, `/*/State/Code`, `../../GeneralLiabilityLocationTable/...` -- which
is XPath-shaped but is not XPath, and is implemented here rather than delegated
so that its dialect is pinned rather than inherited from a library.

**The `../../../` forms are E18** and they are not rare: they are how a coverage
reaches across coverage groups to a sibling it is priced against. Getting the
step count wrong resolves to a *different real node* rather than to nothing,
which is a wrong premium and not an error.

**Writes create.** `ToDataDef` on a node that does not exist yet means "make it";
that is how a rating result is assembled. Reads never create, because a read that
manufactures the node it was looking for can never report a missing input.
"""
from __future__ import annotations

import re

from .values import InterpretError, to_text


class Node:
    """One element of the data tree."""

    __slots__ = ("tag", "parent", "children", "text")

    def __init__(self, tag: str, parent: "Node | None" = None, text=None):
        self.tag = tag
        self.parent = parent
        self.children: list[Node] = []
        self.text = text

    # ------------------------------------------------------------- structure

    def add(self, tag: str, text=None) -> "Node":
        n = Node(tag, self, text)
        self.children.append(n)
        return n

    def kids(self, tag: str) -> list["Node"]:
        return [c for c in self.children if c.tag == tag]

    def first(self, tag: str) -> "Node | None":
        for c in self.children:
            if c.tag == tag:
                return c
        return None

    @property
    def root(self) -> "Node":
        n = self
        while n.parent is not None:
            n = n.parent
        return n

    @property
    def path(self) -> str:
        bits = []
        n = self
        while n is not None:
            bits.append(n.tag)
            n = n.parent
        return "/".join(reversed(bits))

    def __repr__(self) -> str:            # pragma: no cover - display only
        v = "" if self.text is None else f"={self.text!r}"
        return f"<{self.tag}{v} {len(self.children)} kids>"

    # ----------------------------------------------------------------- build

    @classmethod
    def from_dict(cls, tag: str, data) -> "Node":
        """Build a tree from plain Python -- the shape a submission arrives in.

        A dict becomes child elements; a list becomes repeated elements of the
        same tag; anything else becomes text.
        """
        n = cls(tag)
        n._fill(data)
        return n

    def _fill(self, data) -> None:
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, list):
                    for item in v:
                        self.add(k)._fill(item)
                elif isinstance(v, dict):
                    self.add(k)._fill(v)
                else:
                    self.add(k, None if v is None else to_text(v))
        elif data is not None:
            self.text = to_text(data)


# ------------------------------------------------------------------ addressing

#: `GeneralLiabilityTerrorismTable/GeneralLiabilityTerrorism[1]`
#:
#: The dialect has exactly one predicate and it is always `[1]`: 18,796
#: occurrences across all 567 packages, and not one other form. It carries
#: 88.9% of `AtOutputDataDef` paths, which is how ISO addresses the single row
#: it appends for a coverage.
#:
#: This was missed on the first pass, and it failed silently in the worst way:
#: an unparsed `X[1]` looks for a child literally tagged `X[1]`, matches
#: nothing, and a `Locate` onto nothing simply does nothing. The terrorism
#: premium came out 18 short with no error anywhere.
_STEP = re.compile(r"^(?P<name>[^\[\]]+)(?:\[(?P<index>\d+)\])?$")


def _steps(path: str) -> list[tuple[str, int | None]]:
    """Split a path into (name, 1-based index or None) steps."""
    out = []
    for s in path.split("/"):
        if s == "":
            continue
        m = _STEP.match(s)
        if not m:
            raise InterpretError(
                f"path step {s!r} is not a name or name[n]", "§9", path)
        idx = m.group("index")
        out.append((m.group("name"), int(idx) if idx else None))
    return out


def select(path: str, context: Node) -> list[Node]:
    """Every node `path` addresses from `context`. Never creates.

    Absolute paths (`/*/State/Code`) restart at the tree root, where `*` matches
    the root element whatever it is called -- the corpus writes `/*/` rather than
    naming it, so the engine must not hard-code a root tag.
    """
    if not path:
        return [context]
    absolute = path.startswith("/")
    here = [context.root] if absolute else [context]
    steps = _steps(path)

    if absolute and steps and steps[0][0] == "*":
        steps = steps[1:]

    for name, index in steps:
        nxt: list[Node] = []
        if name == ".":
            nxt = here
        elif name == "..":
            for n in here:
                if n.parent is None:
                    raise InterpretError(
                        f"path {path!r} steps above the tree root", "§9",
                        context.path)
                nxt.append(n.parent)
        elif name == "*":
            for n in here:
                nxt.extend(n.children)
        else:
            for n in here:
                kids = n.kids(name)
                if index is None:
                    nxt.extend(kids)
                elif len(kids) >= index:
                    nxt.append(kids[index - 1])      # 1-based
        here = nxt
        if not here:
            return []
    return here


def select_one(path: str, context: Node) -> Node | None:
    found = select(path, context)
    return found[0] if found else None


def read(path: str, context: Node):
    """The text at `path`, or None if it is not there.

    Absence and a present-but-empty node are different answers and both are
    reachable: the corpus asks `Exist` and `IsNull` as separate questions.
    """
    n = select_one(path, context)
    return None if n is None else n.text


def ensure(path: str, context: Node) -> Node:
    """The node at `path`, creating it and any missing ancestors.

    Only ever called for a write.
    """
    if not path:
        return context
    absolute = path.startswith("/")
    here = context.root if absolute else context
    steps = _steps(path)
    if absolute and steps and steps[0][0] == "*":
        steps = steps[1:]

    for name, index in steps:
        if name == ".":
            continue
        if name == "..":
            if here.parent is None:
                raise InterpretError(
                    f"write path {path!r} steps above the tree root", "§9",
                    context.path)
            here = here.parent
            continue
        if name == "*":
            raise InterpretError(
                f"write path {path!r} contains a wildcard", "§9", context.path)
        if index is None:
            nxt = here.first(name)
            here = nxt if nxt is not None else here.add(name)
        else:
            kids = here.kids(name)
            while len(kids) < index:                 # grow to the addressed row
                kids.append(here.add(name))
            here = kids[index - 1]
    return here


def write(path: str, context: Node, value) -> Node:
    n = ensure(path, context)
    n.text = to_text(value) if value is not None else None
    return n


def dump(node: Node, indent: int = 0) -> str:      # pragma: no cover - display
    pad = "  " * indent
    val = "" if node.text in (None, "") else f" = {node.text}"
    out = [f"{pad}{node.tag}{val}"]
    for c in node.children:
        out.append(dump(c, indent + 1))
    return "\n".join(out)
