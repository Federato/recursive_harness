"""Stage 4 -- the submission schema, read from ISO rather than designed.

    from gl_engine.schema import Schema
    s = Schema.for_book(book)
    s.required()                 # what a rating needs
    s.legal_values("Subline")    # from ISO's own domain table
    s.validate(payload)          # findings, not exceptions
"""
from .fields import Field, Schema
from .validate import Finding, validate

__all__ = ["Field", "Schema", "Finding", "validate"]
