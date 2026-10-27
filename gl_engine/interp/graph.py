"""The rating graph: which values each written value was computed from (docs/RATING-GRAPH-PLAN.md, G1).

The interpreter stays the source of truth. This records, while ONE rating runs, a graph of values and the edges
between them; it never computes a value and never changes one. It is off unless a caller sets
`Interpreter.deps = RatingGraph()` before `run` (`cf_engine.rating.rate(graph=True)`, `Kernel.rate(graph=True)`).

**Nodes.** `input` (a submitted field read during the rating), `table` (a table row a lookup returned; `company`
when a carrier's layer supplied it), `write` (each write: a field written twice is two nodes), `company` (a carrier
source the deviations layer applied: a record LCM, a group LCM).

**Edges**, stored on the node they point to:

  * `data` -- read while the written value's expression was being evaluated;
  * `control` -- read by an `If` / `Choose` test that decided whether the write happened at all, including writes in
    rules called from the chosen branch.

A read points at the latest version of a field at the moment it is read. Rule parameters carry the reads their
argument was computed from, so a rule body that reads a parameter depends on what the caller passed.

The recorder protocol the interpreter calls (it replaced P3's coarser taint tracker, G3): `around`, `read`, `read_many`,
`param`, `bind`, `capture_begin` / `capture_end`, `control_push` / `control_pop`, `wrote`, `lookup`, `company`,
`mark`, `enter_rule` / `leave_rule`.
"""
from __future__ import annotations

from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

_REPLAYABLE = ("Product", "Sum")


def normalise(path: str) -> str:
    """The worksheet's path form (`console.worksheet.normalise`, kept here so the engine does not import the
    console): drop `[0]` and the `XTable` containers ISO's response does not emit."""
    parts = [p for p in path.replace("[0]", "").split("/") if p]
    out = []
    for i, p in enumerate(parts):
        nxt = parts[i + 1] if i + 1 < len(parts) else ""
        if p.endswith("Table") and p[:-5] == nxt.split("[")[0]:
            continue
        out.append(p)
    return "/" + "/".join(out)


class RatingGraph:
    def __init__(self):
        self.nodes: list[dict] = []
        self.data: dict[int, set] = {}
        self.control: dict[int, set] = {}
        self._tree: dict[int, object] = {}        # gid -> tree node (inputs and writes), until finalize
        self._of: dict[int, int] = {}             # id(tree node) -> gid of its latest version
        self._keep: list = []                     # tree nodes and param dicts kept alive while ids are used
        self._stack: list[set] = [set()]
        self._ctl: list[frozenset] = []
        self._params: dict[int, dict] = {}        # id(params dict) -> {name: set of gids}
        self._tables: dict[tuple, int] = {}
        self._versions: dict[int, int] = defaultdict(int)
        self.finalized = False

    # ------------------------------------------------------------------ building

    def _node(self, **kw) -> int:
        gid = len(self.nodes)
        kw["id"] = gid
        self.nodes.append(kw)
        return gid

    def around(self, fn, el, frame):
        self._stack.append(set())
        try:
            return fn(el, frame)
        finally:
            s = self._stack.pop()
            if s:
                self._stack[-1] |= s

    def read(self, node) -> None:
        if node is None:
            return
        gid = self._of.get(id(node))
        if gid is None:
            gid = self._node(kind="input", value=None if node.children else node.text)
            self._of[id(node)] = gid
            self._tree[gid] = node
            self._keep.append(node)
        self._stack[-1].add(gid)

    def read_many(self, nodes) -> None:
        for n in nodes:
            self.read(n)

    def capture_begin(self) -> None:
        self._stack.append(set())

    def capture_end(self) -> set:
        return self._stack.pop()

    def bind(self, params: dict, provenance: dict) -> None:
        """A rule's (or WithArgs') parameter dict, and what each argument was computed from."""
        prior = {}
        self._params[id(params)] = {**prior, **provenance}
        self._keep.append(params)

    def inherit(self, params: dict, outer: dict) -> None:
        """WithArgs merges new bindings over the outer frame's: the outer provenance carries over."""
        got = dict(self._params.get(id(outer), {}))
        got.update(self._params.get(id(params), {}))
        self._params[id(params)] = got
        self._keep.append(params)

    def param(self, params: dict, name: str) -> None:
        src = self._params.get(id(params), {}).get(name)
        if src:
            self._stack[-1] |= src

    def control_push(self, reads) -> None:
        self._ctl.append(frozenset(reads))

    def control_pop(self) -> None:
        self._ctl.pop()

    def wrote(self, node, value=None, op: str = "", el=None, rule: str = "") -> None:
        key = id(node)
        self._versions[key] += 1
        replay = None
        if el is not None and op in _REPLAYABLE:
            kids = list(el)
            if kids and all(k.tag.rsplit("}", 1)[-1] in ("Value", "FirstValue") and "FromDataDef" in k.attrib
                            for k in kids):
                replay = {"operands": len(kids), "decimals": el.attrib.get("DecimalPlaces")}
        gid = self._node(kind="write", value=None if value is None else str(value), op=op, rule=rule,
                         version=self._versions[key], replay=replay)
        self.data[gid] = set(self._stack[-1])
        ctl = set().union(*self._ctl) if self._ctl else set()
        if ctl:
            self.control[gid] = ctl - self.data[gid]
        self._of[key] = gid
        self._tree[gid] = node
        self._keep.append(node)
        self._stack[-1] = {gid}

    def lookup(self, table: str, column: str, keys, value, package: str) -> None:
        k = (table, column, tuple(str(x) for x in keys), str(package))
        gid = self._tables.get(k)
        if gid is None:
            gid = self._node(kind="table", table=table, column=column, keys=list(k[2]),
                             value=None if value is None else str(value), package=str(package),
                             company="+" in str(package))
            self._tables[k] = gid
        self._stack[-1].add(gid)

    def company(self, label: str, value=None, explain: str = "", **info) -> None:
        gid = self._node(kind="company", label=label, value=None if value is None else str(value),
                         explain=explain, **info)
        self._stack[-1].add(gid)

    def mark(self, node, label: str = "company LCM", value=None, explain: str = "") -> None:
        """A field a carrier wrote before the rules ran: reading it reads the company source."""
        gid = self._node(kind="company", label=label, value=None if value is None else str(value),
                         explain=explain)
        self._of[id(node)] = gid
        self._tree[gid] = node
        self._keep.append(node)

    def enter_rule(self) -> None:
        pass

    def leave_rule(self) -> None:
        pass

    # ------------------------------------------------------------------ after the rating

    def finalize(self, tree) -> "RatingGraph":
        """Name every node by its path in the rated tree (the worksheet's path form), then drop tree references."""
        if self.finalized:
            return self
        where: dict[int, str] = {}

        def walk(node, prefix):
            seen: dict = {}
            for c in node.children:
                i = seen.get(c.tag, 0)
                seen[c.tag] = i + 1
                p = f"{prefix}/{c.tag}[{i}]"
                where[id(c)] = normalise(p)
                walk(c, p)
        walk(tree, "")
        self.final: dict[str, int] = {}
        for gid, node in self._tree.items():
            path = where.get(id(node)) or getattr(node, "path", "")
            self.nodes[gid]["path"] = path
        for key, gid in self._of.items():
            p = self.nodes[gid].get("path")
            if p and self.nodes[gid]["kind"] in ("write", "input", "company"):
                self.final[p] = gid
        self._tree, self._of, self._keep, self._params = {}, {}, [], {}
        self.finalized = True
        return self

    # ------------------------------------------------------------------ reading it

    def parents(self, gid: int) -> list[tuple[int, str]]:
        return [(s, "data") for s in sorted(self.data.get(gid, ()))] + \
               [(s, "control") for s in sorted(self.control.get(gid, ()))]

    def edges(self) -> list[tuple[int, int, str]]:
        return [(s, d, k) for d in range(len(self.nodes)) for s, k in self.parents(d)]

    def children_map(self) -> dict[int, set]:
        out: dict[int, set] = defaultdict(set)
        for s, d, _ in self.edges():
            out[s].add(d)
        return out

    def reach(self, sources) -> set:
        """Every node reachable from `sources` along any edge (what they could have affected)."""
        kids = self.children_map()
        seen, stack = set(), list(sources)
        while stack:
            n = stack.pop()
            for c in kids.get(n, ()):
                if c not in seen:
                    seen.add(c)
                    stack.append(c)
        return seen

    def ancestry(self, gid: int, depth: int = 3) -> dict:
        """A node and its inputs, `depth` levels up: the worksheet's "why this value"."""
        n = dict(self.nodes[gid])
        out = {k: n.get(k) for k in ("id", "kind", "path", "value", "op", "rule", "version", "table", "column",
                                     "keys", "package", "company", "label", "explain", "group")}
        ps = self.parents(gid)
        out["inputs"] = len(ps)
        if depth > 0:
            out["from"] = [dict(self.ancestry(s, depth - 1), edge=k) for s, k in ps]
        return out

    def sources(self, gid: int) -> list[dict]:
        """Every table row, company source and input a value ultimately came from (its full ancestry's leaves)."""
        seen, stack, out = set(), [gid], []
        while stack:
            n = stack.pop()
            for s, _ in self.parents(n):
                if s in seen:
                    continue
                seen.add(s)
                node = self.nodes[s]
                if node["kind"] in ("table", "company", "input"):
                    out.append({k: node.get(k) for k in ("id", "kind", "path", "value", "table", "column", "keys",
                                                         "package", "company", "label", "explain")})
                stack.append(s)
        return out

    def replay(self, gid: int, rounding: str = "ROUND_HALF_UP"):
        """Re-apply a plain Product / Sum to the values on its data edges. (expected, got) or None if not replayable."""
        n = self.nodes[gid]
        rp = n.get("replay")
        src = sorted(self.data.get(gid, ()))
        if not rp or len(src) != rp["operands"] or n["value"] is None:
            return None
        try:
            vals = [Decimal(str(self.nodes[s]["value"])) for s in src]
        except (InvalidOperation, TypeError):
            return None
        if n["op"] == "Product":
            got = Decimal(1)
            for v in vals:
                got *= v
        else:
            got = sum(vals, Decimal(0))
        if rp.get("decimals") not in (None, ""):
            got = got.quantize(Decimal(1).scaleb(-int(rp["decimals"])), rounding=ROUND_HALF_UP)
        return Decimal(n["value"]), got

    def to_json(self) -> dict:
        return {"nodes": self.nodes, "edges": [[s, d, k] for s, d, k in self.edges()]}
