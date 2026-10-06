"""The ISO ERC Commercial Property rating engine.

Property is the second line of business in this harness. It does not fork the
General Liability engine: ISO files one rule language, and the layers that read
it -- the interpreter, the table reader, the resolved-rulebook composition --
are properties of ERC rather than of a line. Those are imported from
`gl_engine`. What lives here is what is genuinely Property-specific: the corpus
root, package identity, the date floor, and (`run_checks`, chunk 28 C28-21) the
steps a Property rating takes around the rules -- refusals, dropped inputs,
refer to company -- which the shared interpreter calls through the book's
`run_hooks` and no longer carries itself.

**The naming is honest but temporary.** `cf_engine` importing `gl_engine` reads
backwards; the shared layers want a neutral home. Moving them is a refactor
that touches every GL import path, and it is deliberately NOT bundled with a
coverage chunk -- a rename and a rating change in the same commit make a
regression impossible to attribute.
"""
