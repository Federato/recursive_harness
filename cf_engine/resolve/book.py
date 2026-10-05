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

from gl_engine.erc.tables import Table
from gl_engine.resolve.book import Layer, ResolvedBook

from .resolver import CFEditionResolver, Resolution

__all__ = ["Layer", "ResolvedBook", "CFResolvedBook", "Resolution", "book_for"]


class CFResolvedBook(ResolvedBook):
    """Property's rulebook: N3 does NOT hold for an EMPTY state table.

    GL's resolver treats a state table that declares a name as final even with
    zero rows (N3: "we do not do this here"). Property's ISO does not: when the
    in-force state package files a table with a header and no rows, ISO resolves
    the lookup against the countrywide table's rows.

    Evidence (2026-09-28, chunk 18 RC-4, live): Vermont files
    `VacancyPermitFactors` header-only; the rule's CW-keyed fallback lookup then
    found nothing here and Vacancy Permit's Special form priced $0, while ISO
    priced it $87 / $18 from the countrywide row (Special 0.053). A state table
    WITH rows still wins outright, even when the key is missing from it (Kansas
    files its own `VacancyPermitFactors`: ISO refuses a CW-keyed miss against it
    rather than falling back -- the same probe, same day).

    **One table is read as filed, empty or not** (`NO_EMPTY_FALLBACK`, chunk 28
    C28-05): ISO refuses the earthquake sub-limit tier lookup in MA, TN and VT,
    whose state tables are empty, rather than reading countrywide's rows (3 of
    3 live, 2026-10-02, `246_`). Every other empty state table keeps the
    fallback (VT `VacancyPermitFactors`, NY `OffPremEndtsModifyingCovdCOLFactor`:
    ISO used countrywide's rows, 2 of 2).

    **A `SingleResult` lookup that matches no row refuses the policy**
    (`strict_single_result`, read by the interpreter; chunk 28 C28-05). ISO
    refuses at exactly that point (65 of 66 live refusals, 0 of 1,690 rated
    requests), where ours used to carry a null on and often price $0.

    Scope: Property only. GL keeps N3 in `gl_engine.resolve.book`; nothing here
    changes a General Liability book.
    """

    #: The interpreter's default for a `SingleResult` miss: refuse (C28-05).
    strict_single_result = True

    #: A submitted value for a field the rules write is not read, as if never sent (OI-125, C28-08).
    ignore_submitted_owned = True

    #: Submitted answers ISO's request reader drops on the 2023 countrywide editions (OI-112, C28-09): three
    #: cause-of-loss answers on the multiple-deductible form (CP 03 20), whatever is sent (text or true / false),
    #: while it keeps the record's other three. Nothing in the corpus says why (identical declarations, no rule
    #: writes or removes them); measured live (`243_`) and on the 5 ISO fixtures on those parents.
    DROPPED_ON_2023 = frozenset({
        ("CommercialPropertyMultipleDeductibleFormFixedDollarDeductibles", "AllCoveredCausesOfLoss"),
        ("CommercialPropertyMultipleDeductibleFormFixedDollarDeductibles", "AllCoveredCausesOfLossExceptTheft"),
        ("CommercialPropertyMultipleDeductibleFormFixedDollarDeductibles", "Theft"),
    })
    PARENTS_2023 = frozenset({"CF_CW_20230801_V02", "CF_CW_20230801_V03", "CF_CW_20230801_V04"})

    @property
    def ignored_inputs(self) -> frozenset:
        """(record, field) pairs whose submitted value is not read on this book (as ISO drops them)."""
        parent = self.resolution.parent
        return self.DROPPED_ON_2023 if parent is not None and parent.pkg_id in self.PARENTS_2023 else frozenset()

    #: State tables read as filed even when empty: ISO refuses rather than
    #: falling back to countrywide (MA, TN, VT; C28-03, `246_`).
    NO_EMPTY_FALLBACK = frozenset({"EQSubLimitDeductibleTierCWTable"})

    def table(self, name: str, kind: str = "Rate") -> Table:
        if self.state.has(kind, name):
            own = self.state.table(kind, name)
            if (not own.rows and name not in self.NO_EMPTY_FALLBACK
                    and self.parent and self.parent.has(kind, name)):
                upstairs = self.parent.table(kind, name)
                if upstairs.rows:
                    return upstairs
            return own
        return super().table(name, kind)


#: One book per (jurisdiction, date, version) per process (2026-09-30, regression streamlining): resolving
#: a book scans the package tree (~0.7 s), and scripts ask for the same one per case. A book is read-only
#: (its own table caches are lookups), and no script modifies one. A caller passing its own `resolver`
#: is not cached.
_BOOKS: dict[tuple, ResolvedBook] = {}


def book_for(juris: str, asof: str, version: str | None = None,
             resolver: CFEditionResolver | None = None) -> ResolvedBook:
    """The Property rulebook in force for one jurisdiction on one date."""
    if resolver is None:
        key = (juris, asof, version)
        got = _BOOKS.get(key)
        if got is None:
            got = _BOOKS[key] = CFResolvedBook(CFEditionResolver().resolve(juris, asof, version))
        return got
    return CFResolvedBook(resolver.resolve(juris, asof, version))
