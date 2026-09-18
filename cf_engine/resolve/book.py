"""The resolved Property rulebook.

`ResolvedBook` is composition, not content: state layer over declared parent,
override by NAME even when the override is empty (N3), and `rating_table()`
refusing an empty table where a premium depends on it. None of that is General
Liability-specific, so Property uses it directly rather than restating it.

**`rating_table()` IS the header-only detector chunk 0 owes**, and Property
needs it more than GL does. 103 of 460 countrywide Property rate tables carry
zero data rows -- 22.4% against GL's own header-only population -- and the
first lookup of the very first coverage is one of them: `BasicGroupIRate` is
header-only at countrywide in EVERY edition from 20191201 to 20260601, so a
reader that treats an empty table as a zero rate produces a free building
rather than an error.

The one thing that behaves differently here is `siblings()` / `split_families()`,
which groups per-territory loss-cost slices under a base name. Its pattern
requires `LossCost` in the table name, and Property files no such table, so it
returns nothing for every Property book. That is correct rather than merely
harmless: the split-family mechanism is a GL filing idiom, and Property does
not use it.
"""
from __future__ import annotations

from gl_engine.resolve.book import Layer, ResolvedBook

from .resolver import CFEditionResolver, Resolution

__all__ = ["Layer", "ResolvedBook", "Resolution", "book_for"]


def book_for(juris: str, asof: str, version: str | None = None,
             resolver: CFEditionResolver | None = None) -> ResolvedBook:
    """The Property rulebook in force for one jurisdiction on one date."""
    res = (resolver or CFEditionResolver()).resolve(juris, asof, version)
    return ResolvedBook(res)
