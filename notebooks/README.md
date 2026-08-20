# notebooks

**How the code works, one notebook per Python file, every example runnable.**

These are a description layer over the engine. They import it, run it, and show what comes back.
Nothing here is imported *by* the engine, and nothing here is required to rate a submission.

## Setup

```bash
pip install -r notebooks/requirements.txt
jupyter lab notebooks/
```

Start at [`00-index.ipynb`](00-index.ipynb). It checks your environment and links every other
notebook in reading order.

**A second set covers the QA harness** -- `qa.py`, `variants.py`, `sweep.py` and the rest of
`scripts/` and the chart layer in `ui/` -- rather than the engine. It lives in
[`harness/`](harness/00-index.ipynb), with its own index and the same shape of notebook, and it
exists as a separate set on purpose: the engine notebooks make the claim that no rating concept
lives in `gl_engine/` outside the interpreter, and mixing harness code into that set would blur it.

**You need a licensed copy of ISO's ERC corpus**, at the path in `GL_ERC_ROOT` — the same
requirement the engine has. `00-index` checks for it and says what's missing rather than letting
each notebook fail obscurely.

## Reading order

The numbering is dependency order, not alphabetical. Each notebook may assume the ones above it.
`00-index` has the full table.

Roughly: where the content lives → how failures work → the typed value → finding and resolving
packages → reading tables → the interpreter's value model and tree → the 54 instructions → the
interpreter → schemas → rating → the assertions → the CLI. Then the analysis scripts and the test
suites.

## The shape of every notebook

The same six cells each time, so the fiftieth reads like the first:

| | |
|---|---|
| 1 | **What this file is for** — plain English, a few sentences |
| 2 | **Its public surface** — generated from the module, so it cannot drift |
| 3 | **The smallest thing that works** — real output, a handful of lines |
| 4 | **The interesting case** — the thing the file exists to get right |
| 5 | **What it refuses** — a deliberate failure, because the refusals are designed behaviour |
| 6 | **Try it yourself** — prompts, blank cells, answers at the bottom |

## Outputs are stripped before commit

**A notebook that has run holds ISO's numbers inside it** — loss costs, factors, rated premiums,
saved into the `.ipynb` as JSON. Those are licensed ISO content, which this repository deliberately
excludes (see [`.gitignore`](../.gitignore)).

So committed notebooks carry **code and prose only**. You run them to see the numbers.

`nbstripout` is configured as a git filter and does this automatically:

```bash
pip install -r notebooks/requirements.txt
nbstripout --install --attributes .gitattributes
```

If you have committed outputs by accident, `nbstripout notebooks/*.ipynb` clears them. The benefit
beyond licensing: notebook diffs stay readable, instead of every rerun showing as a change.

## They are tested

`tests/verify_notebooks.py` executes them headless and fails on any exception, so a notebook that
stops matching the code becomes a red test rather than quietly wrong documentation.
