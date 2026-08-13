"""GL rating engine -- an interpreter for ISO's filed Electronic Rating Content.

It does not re-implement ISO's rules in Python. It executes them. That fork was
decided on 2026-08-12 on a measurement: ISO's instruction language is 58 node
types across 809,088 occurrences, and the top 20 cover 94.1% -- so implementing
the language once is cheaper than hand-writing 4,461 rules per package and doing
it again at every filing.

STAGE 1 IS BUILT: load and resolve. Given a jurisdiction and a date, this
package returns the exact rule set and tables ISO says apply, with every value
carrying its source. The interpreter (stage 2) is not written.

    from gl_engine import EditionResolver, ResolvedBook
    r = EditionResolver()
    book = ResolvedBook(r.resolve("NJ", "20260811"))
    book.rating_table("PremOpsLossCost")
"""
from .domain import Cell, Citation, Disposition
from .errors import (AssertionFailure, EngineError, IdentityError, LoadError,
                     ReferToCompany, ResolutionError, TableError)
from .erc import Package, Population, Shape, Table, discover
from .resolve import EditionResolver, ResolvedBook, Resolution

__version__ = "0.1.0-stage1"

__all__ = [
    "Cell", "Citation", "Disposition",
    "EngineError", "LoadError", "IdentityError", "ResolutionError",
    "TableError", "AssertionFailure", "ReferToCompany",
    "discover", "Package", "Table", "Shape", "Population",
    "EditionResolver", "Resolution", "ResolvedBook",
]
