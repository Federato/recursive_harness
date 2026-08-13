"""Every way this engine is allowed to fail.

There is no warning tier. ISO's content either resolves or it does not, and a
rating that proceeds on a guess is worse than one that stops -- that is the whole
doctrine (`docs/GL-RATING-ENGINE-BUILD-PLAN.md` section 1) expressed as types.

`ReferToCompany` is deliberately NOT an ancestor of `LoadError`. A referral is a
legitimate rating outcome that the caller may resolve by supplying a value; a load
error is a defect in the corpus or in us.
"""
from __future__ import annotations


class EngineError(Exception):
    """Base for everything this engine raises."""


# ------------------------------------------------------------------ loading

class LoadError(EngineError):
    """The corpus could not be read as ERC content."""


class IdentityError(LoadError):
    """A package's identity could not be established from its XSD (N6).

    Never fall back to the directory name. Two packages in this corpus are
    unpacked in directories whose names disagree with their own namespace.
    """


class ResolutionError(LoadError):
    """No edition, or no declared parent, for the requested jurisdiction/date.

    Includes the as-of floor: before 2022-09-01 the corpus cannot resolve all 51
    jurisdictions (OI-41), so a date below it is refused rather than served
    partially.
    """


class TableError(LoadError):
    """A table is missing, untyped, or empty where a rating path needs it."""


class AssertionFailure(LoadError):
    """A load-time assertion did not hold.

    Section 10 of the build plan lists these and says *fail, never warn*.
    """

    def __init__(self, code: str, message: str, detail=None):
        self.code = code
        self.detail = detail
        super().__init__(f"[{code}] {message}")


# ------------------------------------------------------------------- rating

class ReferToCompany(EngineError):
    """ISO declines to price this; a human must.

    Carries the citation chain so the caller can see *why*, and -- when the
    referral is resolvable -- the name of the value that would clear it.
    """

    def __init__(self, erc_source, confirmed_by=None, escalation=None,
                 needs: str | None = None):
        self.erc_source = erc_source
        self.confirmed_by = confirmed_by
        self.escalation = escalation
        self.needs = needs
        bits = [f"REFER TO COMPANY at {erc_source}"]
        if needs:
            bits.append(f"resolvable: supply `{needs}`")
        if escalation:
            bits.append(f"escalation {escalation}")
        super().__init__("; ".join(bits))
