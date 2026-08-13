"""The typed cell -- the unit every number in this engine travels in.

Build plan section 4.1. The rule enforced here by the type system rather than by
review: **a value with no ERC source cannot be constructed.** `erc_source` has no
default. That is the evidence hierarchy made structural.

`Disposition` is why this type exists at all (N1). ERC does not answer "what is
the factor" with a number; it answers with a number *or* with a marker meaning
"not offered here" or "refer this to a human". A zero in this corpus has eight
distinct meanings (N13) and only one of them is the number nought. Any engine
that returns a bare `Decimal` has already thrown that away, and the failure mode
is a free policy on precisely the risks meant for underwriter review.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum, auto

from ..errors import ReferToCompany


class Disposition(Enum):
    """What ISO said. Ordered by how much it lets us do."""

    PUBLISHED = auto()      # ERC states a value and we may use it
    NOT_OFFERED = auto()    # ERC's not-offered marker: this does not exist here
    REFER = auto()          # ERC's refer marker, a confirmed sentinel, or an open escalation

    def __str__(self) -> str:            # pragma: no cover - display only
        return self.name


@dataclass(frozen=True, slots=True)
class Citation:
    """Where a value came from, precisely enough to re-open the file.

    `package` is the ERC package id as the XSD declares it (N6), never the
    directory name -- so a citation survives the corpus being re-unpacked.
    """

    package: str            # 'GL_NJ_20250301_V01'
    category: str           # 'Rate Tables' | 'Domain Tables' | 'Rules' | 'DataDefs'
    artifact: str           # table or rule name
    locator: str = ""       # key tuple, row number, or rule path

    def __str__(self) -> str:
        tail = f" @ {self.locator}" if self.locator else ""
        return f"{self.package}/{self.category}/{self.artifact}{tail}"


@dataclass(frozen=True, slots=True)
class Cell:
    """A value ISO published, or ISO's refusal to publish one.

    Three tiers travel together, matching the evidence hierarchy exactly:
      `erc_source`   tier 1 -- mandatory, the ERC artifact. No default.
      `confirmed_by` tier 2 -- optional, a manual page that CONFIRMS this artifact.
      `escalation`   tier 3 -- optional, the E-number blocking this path.
    """

    disposition: Disposition
    value: Decimal | None
    erc_source: Citation
    confirmed_by: Citation | None = None
    escalation: str | None = None
    needs: str | None = None            # for a resolvable REFER: the input that clears it

    def __post_init__(self):
        if self.disposition is Disposition.PUBLISHED and self.value is None:
            raise ValueError(f"PUBLISHED cell with no value at {self.erc_source}")
        if self.disposition is not Disposition.PUBLISHED and self.value is not None:
            # A non-published cell may not smuggle a number. This is the guard
            # against N13: the sentinel that LOOKS like a rate.
            raise ValueError(
                f"{self.disposition} cell carrying value {self.value!r} at "
                f"{self.erc_source} -- a sentinel is not a number")

    @property
    def is_usable(self) -> bool:
        return self.disposition is Disposition.PUBLISHED

    def require_value(self) -> Decimal:
        """The only way to get the number out. Raises on anything else."""
        if self.disposition is not Disposition.PUBLISHED:
            raise ReferToCompany(self.erc_source, self.confirmed_by,
                                 self.escalation, self.needs)
        return self.value

    # -- constructors, so callers never build a Cell with the wrong invariants --

    @classmethod
    def published(cls, value: Decimal, source: Citation, confirmed_by=None) -> "Cell":
        return cls(Disposition.PUBLISHED, Decimal(value), source, confirmed_by)

    @classmethod
    def refer(cls, source: Citation, escalation=None, needs=None,
              confirmed_by=None) -> "Cell":
        return cls(Disposition.REFER, None, source, confirmed_by, escalation, needs)

    @classmethod
    def not_offered(cls, source: Citation, confirmed_by=None) -> "Cell":
        return cls(Disposition.NOT_OFFERED, None, source, confirmed_by)

    def __str__(self) -> str:            # pragma: no cover - display only
        if self.disposition is Disposition.PUBLISHED:
            return f"{self.value} <{self.erc_source}>"
        return f"{self.disposition} <{self.erc_source}>"
