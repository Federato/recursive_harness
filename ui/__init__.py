"""The interface layer. Presentation and history; no rating, no rules.

**The dependency runs one way and is asserted by a test.**

    ui  ->  console/             ->  gl_engine, cf_engine
    ui  ->  scripts/variants.py  ->  gl_engine

`gl_engine` imports neither, and nothing in this package decides what a legal value is, what a premium is, or whether
two answers agree. Those questions have one answer each and it lives outside here:

* **legal values** -- `variants.Declared` (GL) and the state's domain tables (CP, `console.catalog`)
* **the premium** -- the engine (`gl_engine.rating.Kernel`; the interpreter for Property)
* **agreement** -- `console.worksheet.same`, field by field, as Trace Diff and the library use it

`tests/verify_gl_variants.py` asserts the direction by parsing the imports.

    from ui import console_page
    console_page.dispatch(method, path, query, body)   # mounted by app.py: the test console at /console

The old testing pages (`/tester`, `/tests`, `/review`) were retired in RC-6 (TC-37); every job they did has a home in
the console (docs/TC-36-PARITY-CHECK.md).
"""
from . import charts, console_page, variables

__all__ = ["charts", "console_page", "variables"]
