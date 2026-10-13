"""Which Property rules apply, for this state, on this date.

The five steps are ISO's filing model, not General Liability's, so they are
inherited rather than restated -- see `gl_engine.resolve.resolver`. Two things
are line-specific and both are declared here: the corpus to discover, and the
date floor.

**The floor is a different KIND of fact here, and the difference is not
pedantic.** GL's floor is a coverage floor: below it the corpus cannot resolve
all 51 jurisdictions, so a date under it would silently serve a partial answer.
Property's floor is an existence floor: below 20191201 there is no Property
package at all. No coverage measurement has been made for Property, so this
does not claim one -- above the floor a jurisdiction may still fail to resolve,
and it will say so per jurisdiction rather than being waved through by a date
check that was never computed for this corpus.

**What is NOT built here, deliberately.** The Property build order supposed an
edition-chain carry-forward layer -- a table absent from the current edition
still being in force from the last edition that filed it. That is a claim about
ISO's filing model that this engine does not implement, because ISO's own
packages state their parentage explicitly (N5) and two layers is what they
declare. If a Property rating is ever found to need a table that is in neither
its resolved state package nor that package's DECLARED parent, that is the
evidence for a third layer, and it should be built then, against that case.
Building it first would mean resolving values from editions ISO did not say to
read.
"""
from __future__ import annotations

from ..config import COUNTRYWIDE, MIN_ASOF
from ..erc.discovery import discover
from gl_engine.resolve.resolver import EditionResolver, Resolution

__all__ = ["CFEditionResolver", "Resolution"]

assert COUNTRYWIDE == "CW", "both lines use CW as the countrywide token"


class CFEditionResolver(EditionResolver):
    """The Property corpus, answering (jurisdiction, date) questions."""

    MIN_ASOF = MIN_ASOF
    FLOOR_REASON = ("the Property corpus holds no package before that date. "
                    "Note this is a floor on EXISTENCE, not on coverage: no "
                    "all-jurisdiction coverage floor has been measured for "
                    "this corpus")

    @staticmethod
    def _discover(root):
        return discover(root)
