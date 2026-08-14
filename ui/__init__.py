"""The interface layer. Presentation and history; no rating, no rules.

**The dependency runs one way and is asserted by a test.**

    ui  ->  scripts/variants.py  ->  gl_engine
    ui  ->  scripts/sweep.py     ->  gl_engine

`gl_engine` imports neither, and nothing in this package decides what a legal
value is, what a premium is, or whether two answers agree. Those three questions
have exactly one answer each and it lives outside here:

* **legal values** -- `variants.Declared`, read from ISO's declared domains
* **the premium** -- `gl_engine.rating.Kernel`
* **agreement** -- `phase2_compare.compare_payload`, the same function the
  phase 2 command line uses

`tests/verify_tester.py` asserts the direction by parsing the imports, because
the separation is the thing stage 6 existed to prove and a comment does not
prove it.

    from ui import tester
    tester.routes()          # (method, path) -> handler, mounted by app.py
"""
from . import charts, store, tester, variables

__all__ = ["charts", "store", "tester", "variables"]
