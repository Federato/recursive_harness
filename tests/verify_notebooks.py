"""Every notebook runs, and every code cell in it runs.

The notebooks in `notebooks/` describe the engine by executing it. That makes them
useful and it makes them fragile: a rename in `gl_engine/` turns prose that reads
correct into prose that is wrong, and nothing would say so.

So they are a test suite. This executes every code cell of every notebook in a
fresh namespace per notebook, in filename order, and fails on the first exception.
A notebook that stops matching the code becomes a red suite rather than quietly
wrong documentation.

**Cells are executed, outputs are not compared.** Comparing outputs would pin this
to one corpus edition and go red every time ISO files anything -- which is noise,
not signal. What is asserted is that the code in the prose still runs against the
engine as it stands today.

    python tests/verify_notebooks.py            # all of them
    python tests/verify_notebooks.py 05         # just the ones matching "05"
"""
from __future__ import annotations

import io
import json
import contextlib
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOTEBOOKS = ROOT / "notebooks"
sys.path.insert(0, str(ROOT))


def code_cells(nb: dict) -> list[str]:
    return ["".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]


def run_notebook(path: Path) -> tuple[bool, str]:
    """Execute every code cell in one namespace. Returns (ok, detail)."""
    nb = json.loads(path.read_text(encoding="utf-8"))
    cells = code_cells(nb)
    ns: dict = {"__name__": "__main__", "__file__": str(path)}
    cwd = Path.cwd()
    try:
        import os
        os.chdir(path.parent)            # notebooks assume they run from their own dir
        for i, src in enumerate(cells, 1):
            if not src.strip() or src.strip() == "# your turn":
                continue
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    exec(compile(src, f"{path.name}#cell{i}", "exec"), ns)
            except Exception:
                return False, f"cell {i} of {len(cells)}:\n" + traceback.format_exc(limit=3)
    finally:
        os.chdir(cwd)
    return True, f"{len(cells)} cells"


def main(argv: list[str]) -> int:
    if not NOTEBOOKS.is_dir():
        print(f"no notebooks directory at {NOTEBOOKS}")
        return 1

    pattern = argv[0] if argv else ""
    paths = sorted((p for p in NOTEBOOKS.rglob("*.ipynb")
                    if pattern in p.name and ".ipynb_checkpoints" not in p.parts),
                   key=lambda p: p.relative_to(NOTEBOOKS).parts)
    if not paths:
        print(f"no notebooks match {pattern!r}")
        return 1

    print(f"{len(paths)} notebook(s) in {NOTEBOOKS}\n")
    failed = []
    for p in paths:
        name = str(p.relative_to(NOTEBOOKS)).replace("\\", "/")
        t0 = time.perf_counter()
        ok, detail = run_notebook(p)
        secs = time.perf_counter() - t0
        if ok:
            print(f"  PASS  {name:<44} {detail}, {secs:.1f}s")
        else:
            failed.append(name)
            print(f"  FAIL  {name:<44} {detail}")

    print()
    print(f"{len(paths) - len(failed)}/{len(paths)} passed")
    if failed:
        print("failed: " + ", ".join(failed))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
