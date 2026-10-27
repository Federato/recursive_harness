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

import dataclasses
import json
from pathlib import Path

from gl_engine.erc.tables import Table
from gl_engine.resolve.book import Layer, ResolvedBook

from ..run_checks import PropertyRunChecks
from ..write_once import ids_for as _write_once_ids

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

    #: Property's steps around every rating (`cf_engine.run_checks`, moved out of GL's interpreter by C28-21): refuse a
    #: known-older package (C28-19), drop what ISO drops (OI-112), don't read a submitted value a rule writes (OI-125,
    #: C28-08), refuse an input whose absence prices an attached coverage at $0 (C28-17), refer below a company minimum
    #: (OI-113).
    run_hooks = PropertyRunChecks()

    #: Writes ISO makes only while the field is empty, on the countrywide 2023-08 V01 rules our corpus holds without
    #: their guards (`cf_engine.write_once`: OI-144, OI-146, OI-148, OI-149). Read by the interpreter at each write.
    write_once = staticmethod(_write_once_ids)

    def older_than_iso(self) -> tuple[str, str] | None:
        """(ours, ISO's) when this book's state package is older than one ISO is known to rate on for this date.

        ISO names the package it used in every response (`Scheme`); `iso_packages.json` holds every one named per state
        in the live comparisons (`242_`, written by `255_ --write`). A package is taken as in force from the edition date
        in its name. ISO's package for this date is the newest named one in force by then (edition, then version); ours
        is older when it sorts below it, as when the corpus lacks an edition (OR 20270101), an edition between two it
        holds (CT 20270101), or a later version (CT 20270301 V02). Importing the package lifts it with no re-run. A
        date nothing was named for, or where ours is the same or newer, is not flagged: "unchecked" is not "older".
        """
        named = _iso_packages().get(self.juris, ())
        due = [p for p in named if p[1] <= self.asof]
        if not due:
            return None
        iso = max(due, key=lambda p: (p[1], p[2]))
        mine = self.resolution.state.identity
        if (mine.edition, mine.version) < (iso[1], iso[2]):
            return mine.raw, iso[0]
        return None

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

    #: (state, table) read as filed even when empty: the state withdrew the table's form (`Pages` Status "D"), and ISO
    #: reads such a table as filed and refuses, where for an offered form it fills an empty state table from countrywide
    #: (OI-133, 2026-10-06, `258_`: FL CP 10 75 and CP 10 76 refused live; VT vacancy and NY off-premises fall back).
    #: Florida withdrew the Cyber Incident Exclusion forms; these are their five tables, all empty in FL. Narrow by
    #: design: moving every stored request into 15 states, these are the only withdrawn-form tables any rating reaches.
    NO_EMPTY_FALLBACK_STATE = frozenset({
        ("FL", "CyberIncidentExclusionFactors"),
        ("FL", "CyberIncidentExclusionWithEnsuingCauseOfLossExceptionsFactors"),
        ("FL", "CyberIncidentExclusionFactorMortgageholdersErrorsAndOmissions"),
        ("FL", "CyberExclCoverageExclusionIndicatorCode"),
        ("FL", "CyberExclSpecifiedPerilCoverageExclusionIndicatorCode"),
    })

    def table(self, name: str, kind: str = "Rate") -> Table:
        if self.state.has(kind, name):
            own = self.state.table(kind, name)
            if (not own.rows and name not in self.NO_EMPTY_FALLBACK
                    and (self.juris, name) not in self.NO_EMPTY_FALLBACK_STATE
                    and self.parent and self.parent.has(kind, name)):
                upstairs = self.parent.table(kind, name)
                if upstairs.rows:
                    return upstairs
            if kind == "FormPage" and self.parent and self.parent.has(kind, name):
                return self._form_pages(name, own)
            return own
        return super().table(name, kind)

    def _form_pages(self, name: str, own: Table) -> Table:
        """A state `FormPage` table merged with countrywide's (OI-106, chunk 28 C28-12).

        Every in-force state files its own `Pages` table, and read wholesale it left most forms "Value Not Found"
        (13,455 of the 90,645 names and numbers ISO gives on the stored requests). ISO uses the state's rows, then
        countrywide's for every record (`TableName`) the state does not file a row for; a state row of `Status`
        "D" files nothing. Each part measured (`253_`): VA's own CP 14 10 row hides countrywide's (ISO leaves it
        unnamed), NC's "D" rows do not. Built as measured: 90,645 of 90,645 equal to ISO, no premium or message
        moved. Rate and Domain tables are untouched (a state rate table with rows replaces countrywide's at ISO).
        """
        cache = self.__dict__.setdefault("_form_page_cache", {})
        got = cache.get(name)
        if got is None:
            cw = self.parent.table("FormPage", name)
            idx = [cw.header.index(h) if h in cw.header else None for h in own.header]
            tn = own.header.index("TableName")
            st = own.header.index("Status") if "Status" in own.header else None
            filed = {r[tn] for r in own.rows if st is None or r[st] != "D"}
            extra = [row for row in (tuple(r[i] if i is not None else None for i in idx) for r in cw.rows)
                     if row[tn] not in filed]
            got = cache[name] = dataclasses.replace(own, rows=list(own.rows) + extra)
        return got


_ISO_PACKAGES: dict | None = None


def _iso_packages() -> dict:
    """state -> [(package id, edition, version)] ISO is known to rate on (`iso_packages.json`, C28-19)."""
    global _ISO_PACKAGES
    if _ISO_PACKAGES is None:
        raw = json.loads((Path(__file__).with_name("iso_packages.json")).read_text(encoding="utf-8"))["served"]
        _ISO_PACKAGES = {st: [(p, *p.split("_")[2:4]) for p in ids] for st, ids in raw.items()}
    return _ISO_PACKAGES


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
