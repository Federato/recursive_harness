"""The resolved rulebook: two layers, both addressable.

State-over-countrywide composition, with one hard constraint that shapes the
whole class. **`parent_table` and `parent_rule` are not conveniences.** ERC
contains 4,598 rules whose body is "do what the parent does, then this" -- if
`RunRule` at parent scope re-enters the override, they recurse forever (N2). The
parent layer therefore has to be reachable *explicitly*, not just as a fallback.

The second constraint is N3. **A state override is wholesale, by name, and may be
empty.** If the state package declares a table, that table is the answer even
with zero rows -- it means "we do not do this here", not "look upstairs". So the
lookup asks *does the state declare this name*, never *does the state have rows
for it*.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache

from ..domain import Citation
from ..errors import TableError
from ..erc.discovery import Package
from ..erc.tables import (Population, Table, list_tables, load_table,
                          split_families)
from .resolver import Resolution


@dataclass(eq=False)          # identity hash: lru_cache below needs `self` hashable
class Layer:
    """One package, with its table inventory read from disk and cached."""

    package: Package
    _tables: dict = field(default_factory=dict, repr=False)

    @property
    def pkg_id(self) -> str:
        return self.package.pkg_id

    @lru_cache(maxsize=None)
    def names(self, kind: str) -> tuple[str, ...]:
        return tuple(list_tables(self.package.content, kind))

    @lru_cache(maxsize=None)
    def families(self, kind: str) -> dict:
        return split_families(self.names(kind))

    def has(self, kind: str, name: str) -> bool:
        return name in self.names(kind)

    def table(self, kind: str, name: str) -> Table:
        key = (kind, name)
        if key not in self._tables:
            sibs = self.families(kind).get(name, ())
            self._tables[key] = load_table(
                self.package.content, kind, name, self.pkg_id, sibs)
        return self._tables[key]


class ResolvedBook:
    """What applies to one jurisdiction on one date, with provenance."""

    def __init__(self, resolution: Resolution):
        self.resolution = resolution
        self.state = Layer(resolution.state)
        self.parent = Layer(resolution.parent) if resolution.parent else None

    # ---------------------------------------------------------------- facts

    @property
    def juris(self) -> str:
        return self.resolution.juris

    @property
    def asof(self) -> str:
        return self.resolution.asof

    def __repr__(self) -> str:          # pragma: no cover - display only
        return (f"<ResolvedBook {self.juris}@{self.asof} "
                f"{self.state.pkg_id} over "
                f"{self.parent.pkg_id if self.parent else '-'}>")

    # -------------------------------------------------------------- lookups

    def declares(self, name: str, kind: str = "Rate") -> str | None:
        """Which layer owns this table name -- 'state', 'countrywide', or None."""
        if self.state.has(kind, name):
            return "state"
        if self.parent and self.parent.has(kind, name):
            return "countrywide"
        return None

    def table(self, name: str, kind: str = "Rate") -> Table:
        """The table that applies. State override wins by NAME, even if empty (N3)."""
        if self.state.has(kind, name):
            return self.state.table(kind, name)
        if self.parent and self.parent.has(kind, name):
            return self.parent.table(kind, name)
        raise TableError(
            f"{self.juris}@{self.asof}: no {kind} table {name!r} in "
            f"{self.state.pkg_id}"
            + (f" or {self.parent.pkg_id}" if self.parent else ""))

    def parent_table(self, name: str, kind: str = "Rate") -> Table:
        """Explicitly the countrywide copy, bypassing any state override."""
        if not self.parent:
            raise TableError(f"{self.juris} is countrywide; it has no parent layer")
        if not self.parent.has(kind, name):
            raise TableError(f"{self.parent.pkg_id}: no {kind} table {name!r}")
        return self.parent.table(kind, name)

    def siblings(self, name: str, kind: str = "Rate") -> tuple[str, ...]:
        """Per-territory slices of `name`, searched STATE FIRST (OI-20).

        Deliberately independent of which layer owns the base name. In three
        jurisdictions the state files only the slices, so `PremOpsLossCost`
        itself resolves upward to a header-only countrywide table while the rows
        that actually matter sit in the state layer under different names. Tying
        sibling lookup to the layer that won the base name loses them silently.
        """
        for layer in (self.state, self.parent):
            if layer is None:
                continue
            fam = layer.families(kind).get(name)
            if fam:
                return fam
        return ()

    def sibling_tables(self, name: str, kind: str = "Rate") -> list[Table]:
        for layer in (self.state, self.parent):
            if layer is None:
                continue
            fam = layer.families(kind).get(name)
            if fam:
                return [layer.table(kind, s) for s in fam]
        return []

    def rating_table(self, name: str, kind: str = "Rate") -> Table:
        """A table a premium depends on. Empty is an error here, not a zero.

        This is the distinction that keeps 138 header-only countrywide rate
        tables from silently becoming a free policy. `table()` will hand back an
        empty table because empty is a legitimate statement; `rating_table()`
        will not, because a rating path that reads nothing has no answer.

        The one exception is OI-20: a base loss-cost table may be empty -- or
        absent from the state layer entirely -- because per-territory slices
        carry the rows. Those are found by `siblings()`, state layer first.
        """
        t = self.table(name, kind)
        if t.is_empty and not any(sib.rows for sib in self.sibling_tables(name, kind)):
            raise TableError(
                f"{self.juris}@{self.asof}: rating table {name!r} resolved to "
                f"{t.package} with 0 rows. Empty means NOT OFFERED HERE (N3/N7); "
                f"it does not mean fall back to countrywide, and it does not "
                f"mean zero.")
        return t

    # ------------------------------------------------------------ provenance

    def cite(self, name: str, kind: str = "Rate", locator: str = "") -> Citation:
        """A citation for a value taken from `name`, naming the layer that won."""
        t = self.table(name, kind)
        return Citation(t.package, f"{kind} Tables", name, locator)

    # -------------------------------------------------------------- summary

    def inventory(self) -> dict:
        """Table counts by layer and kind. Used by the assertion suite."""
        out = {}
        for kind in ("Rate", "Domain"):
            st = set(self.state.names(kind))
            cw = set(self.parent.names(kind)) if self.parent else set()
            out[kind] = {
                "state": len(st), "countrywide": len(cw),
                "overridden": len(st & cw), "state_only": len(st - cw),
                "inherited": len(cw - st), "visible": len(st | cw),
            }
        return out
