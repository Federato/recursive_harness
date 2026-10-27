"""Stage 3 -- the rating kernel. A submission goes in, a premium comes out.

    from gl_engine.rating import Kernel
    r = Kernel().rate("Payloads/OK/1. Input.json")
    r.premium        # Decimal('7839')
    r.by_coverage    # the parts, per coverage
    r.trace          # every value, with where it came from
"""
from .kernel import (Kernel, Rating, RatingError, Referral, MODES, STRICT,
                     UNDERWRITING, rate)
from .submission import from_raas, load

__all__ = ["Kernel", "Rating", "RatingError", "Referral", "MODES", "STRICT",
           "UNDERWRITING", "rate", "from_raas", "load"]
