"""GL rating engine -- an interpreter for ISO's filed Electronic Rating Content.

It does not re-implement ISO's rules in Python. It executes them. That fork was
decided on 2026-08-12 on a measurement: ISO's instruction language is 58 node
types across 809,088 occurrences, and the top 20 cover 94.1% -- so implementing
the language once is cheaper than hand-writing 4,461 rules per package and doing
it again at every filing.

STAGE 1: load and resolve. Given a jurisdiction and a date, return the exact
rule set and tables ISO says apply, with every value carrying its source.

    from gl_engine import EditionResolver, ResolvedBook
    r = EditionResolver()
    book = ResolvedBook(r.resolve("NJ", "20260811"))
    book.rating_table("PremOpsLossCost")

STAGE 2: the interpreter. All 54 nodes of ISO's rule language, written against
`docs/rating-engine/14-EVALUATION-CONTRACT.md`. Execution begins at the
`Default` block of `Overall Rating.Rule.xml` -- NOT at `ErcProcess`, which is
the third thing that block calls.

    from gl_engine.interp import Interpreter, Node
    ip = Interpreter(book)
    ip.run(Node.from_dict("GeneralLiabilityRequest", {"EffDate": "06/01/2026"}))

STAGE 3: the kernel. A submission goes in, a premium comes out, in one of two
modes -- `strict-erc` reproduces ISO exactly, `underwriting` additionally
enforces the referral register. One code path.

    from gl_engine.rating import Kernel
    r = Kernel().rate("Payloads/OK/1. Input.json")
    r.premium        # Decimal('7839') -- the golden case, to the penny
    r.by_coverage    # the parts
    r.trace          # every value, with where it came from

Measured against ISO's own 50 priced examples: all 50 rate end to end and 22
agree to the penny. Every difference is our defect until proven otherwise --
`python scripts/rate_all_payloads.py`.
"""
from .domain import Cell, Citation, Disposition
from .errors import (AssertionFailure, EngineError, IdentityError, LoadError,
                     ReferToCompany, ResolutionError, TableError)
from .erc import Package, Population, Shape, Table, discover
from .resolve import EditionResolver, ResolvedBook, Resolution

__version__ = "0.3.0-stage3"

__all__ = [
    "Cell", "Citation", "Disposition",
    "EngineError", "LoadError", "IdentityError", "ResolutionError",
    "TableError", "AssertionFailure", "ReferToCompany",
    "discover", "Package", "Table", "Shape", "Population",
    "EditionResolver", "Resolution", "ResolvedBook",
]
