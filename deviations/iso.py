"""The ISO side of a filing: which edition applies, and what it lets a filing name.

Everything a deviation is checked against comes from the edition in force for
that jurisdiction on the filing's date, read through the engine's own resolver,
so `validate` and the engine can never disagree about what ISO has.
"""
from __future__ import annotations

from functools import lru_cache

from gl_engine.erc.tables import Range, Table


def _norm_date(d: str) -> str:
    """'2025-06-01' -> '20250601' (the resolver's form)."""
    return d.replace("-", "")


@lru_cache(maxsize=None)
def resolver(line: str):
    if line == "CF":
        from cf_engine.resolve.resolver import CFEditionResolver
        return CFEditionResolver()
    from gl_engine.resolve.resolver import EditionResolver
    return EditionResolver()


@lru_cache(maxsize=None)
def book(line: str, juris: str, date: str):
    """The resolved rulebook for one line, state and date."""
    if line == "CF":
        from cf_engine.resolve.book import book_for
        return book_for(juris, _norm_date(date))
    from gl_engine.resolve.book import ResolvedBook
    return ResolvedBook(resolver("GL").resolve(juris, _norm_date(date)))


def edition(line: str, juris: str, date: str) -> dict:
    """Which packages apply: the state package and the countrywide parent."""
    b = book(line, juris, date)
    return {"state": b.state.pkg_id,
            "countrywide": b.parent.pkg_id if b.parent else None}


def jurisdictions(line: str, date: str) -> list[str]:
    """Every jurisdiction that resolves on `date`, countrywide excluded."""
    out = []
    for j in resolver(line).jurisdictions:
        try:
            book(line, j, date)
        except Exception:          # not filed on that date: not part of "all states"
            continue
        out.append(j)
    return out


#: The table that lists every class the line rates, per line. Property's
#: occupancy-group domain holds all 154 CSP class codes (every UFG range
#: endpoint is in it); GL's classification-type table holds all 1,188.
_CLASS_TABLE = {"CF": ("DomainOccupancyGroup", "Domain"),
                "GL": ("ClassificationType", "Rate")}


@lru_cache(maxsize=None)
def class_codes(line: str, juris: str, date: str) -> tuple[str, ...]:
    name, kind = _CLASS_TABLE[line]
    t = book(line, juris, date).table(name, kind)
    i = t.col("ClassCode")
    return tuple(sorted({str(r[i]) for r in t.rows if str(r[i]).strip()}))


def table(line: str, juris: str, date: str, name: str) -> Table:
    """ISO's rate table by name, state over countrywide (N3)."""
    return book(line, juris, date).table(name, "Rate")


def table_keys(t: Table) -> list[str]:
    """The key columns a filing may scope on: every key except StateCode.

    Banded keys (a `Range`) are refused by the caller: a v1 override replaces
    or multiplies an exact row, and a band's rows are not addressable by value.
    """
    return [c.name for c in t.definition.key_items
            if not isinstance(c, Range) and c.name != "StateCode"]


def is_banded(t: Table) -> bool:
    return bool(t.definition.key_ranges)


def value_cols(t: Table) -> list[str]:
    return [c.name for c in t.definition.value_cols]
