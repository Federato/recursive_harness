"""Diff one rated submission against ISO's own output, field by field.

The reconciliation report says *which* jurisdictions disagree. This says
**where**, which is the only question that leads to a fix.

It walks ISO's output JSON and our rated tree together and reports every
numeric field that differs, plus the ones ISO published that we never wrote.
Ordered so the first line is usually the cause: a difference deep in a
classification propagates upward, so the deepest disagreement is the one to
read.

    python scripts/diff_payload.py GA
    python scripts/diff_payload.py OK --all
"""
from __future__ import annotations

import json
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from gl_engine.interp import tree                             # noqa: E402
from gl_engine.rating import Kernel                           # noqa: E402


def iso_numbers(obj, prefix="", out=None):
    """Every numeric leaf ISO published, keyed by a path we can mirror."""
    out = {} if out is None else out
    if isinstance(obj, dict):
        for k, v in obj.items():
            iso_numbers(v, f"{prefix}/{k}", out)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            iso_numbers(v, f"{prefix}[{i}]", out)
    elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
        out[prefix] = Decimal(str(obj))
    return out


def our_numbers(node, prefix="", out=None):
    out = {} if out is None else out
    seen: dict = {}
    for c in node.children:
        i = seen.get(c.tag, 0)
        seen[c.tag] = i + 1
        p = f"{prefix}/{c.tag}[{i}]"
        if c.text not in (None, ""):
            try:
                out[p] = Decimal(str(c.text))
            except (InvalidOperation, ValueError):
                pass
        our_numbers(c, p, out)
    return out


def normalise(path: str) -> str:
    """Put ISO's paths and ours in the same shape.

    Two differences, both structural rather than substantive:

    * ISO writes `X` for a single child and `X[0]` for a list entry; we always
      index. Dropping `[0]` is safe -- a repeated element with more than one
      entry keeps its index.
    * **Our tree carries the `XTable` containers ISO's rule paths require and
      ISO's response does not.** Leaving them in makes every nested field look
      absent on one side and unexpected on the other, which buries the actual
      difference under a hundred false ones. It did exactly that on the first
      run of this script.
    """
    parts = [p for p in path.replace("[0]", "").split("/") if p]
    out = []
    for i, p in enumerate(parts):
        nxt = parts[i + 1] if i + 1 < len(parts) else ""
        base = nxt.split("[")[0]
        if p.endswith("Table") and p[:-5] == base:
            continue                       # the container ISO does not emit
        out.append(p)
    return "/" + "/".join(out)


def main(argv) -> int:
    if not argv:
        print(__doc__)
        return 1
    juris = argv[0].upper()
    show_all = "--all" in argv

    src = ROOT / "Payloads" / juris / "1. Input.json"
    out = ROOT / "Payloads" / juris / "1. Output.json"
    if not src.exists() or not out.exists():
        print(f"no payload pair for {juris}")
        return 1

    iso_body = json.loads(out.read_text(encoding="utf-8-sig"))["Body"]

    # OI-77: 34 of 50 pairs dispute `TerrorismCoverage`. Diagnosing anything
    # else on top of that artefact wastes the run, so this is on by default
    # here -- `--as-filed` turns it off. The reconciliation report is the place
    # that must show both; this tool exists to localise a cause.
    payload = json.loads(src.read_text(encoding="utf-8-sig"))
    if "--as-filed" not in argv:
        want_t = iso_body["GeneralLiability"][0].get("TerrorismCoverage")
        for gl in payload.get("body", {}).get("GeneralLiability", []):
            if want_t is not None and gl.get("TerrorismCoverage") != want_t:
                gl["TerrorismCoverage"] = want_t
                print(f"[OI-77] TerrorismCoverage taken from ISO's output: "
                      f"{want_t!r}")

    r = Kernel().rate(payload)
    if not r.complete:
        print(f"{juris}: did not rate -- {r.stopped}")
        return 1
    want = {normalise(k): v
            for k, v in iso_numbers(iso_body["GeneralLiability"][0]).items()}
    ours_root = tree.select_one("GeneralLiabilityTable/GeneralLiability", r.tree)
    got = {normalise(k): v for k, v in our_numbers(ours_root).items()}

    differ, missing, extra_nonzero = [], [], []
    for k, v in sorted(want.items()):
        if k not in got:
            missing.append((k, v))
        elif got[k] != v:
            differ.append((k, got[k], v))
    for k, v in sorted(got.items()):
        if k not in want and v != 0:
            extra_nonzero.append((k, v))

    print(f"{juris}   ours {r.premium}   ISO {want.get('/Premium')}   "
          f"delta {r.premium - want.get('/Premium', 0)}")
    print(f"        {' over '.join(r.packages)}")
    print()
    print(f"DIFFER ({len(differ)}) -- deepest first, the cause is usually there")
    for k, a, b in sorted(differ, key=lambda x: -x[0].count("/")):
        print(f"    {k}\n        ours {a}   ISO {b}")
    if missing:
        print(f"\nISO PUBLISHED, WE DID NOT WRITE ({len(missing)})")
        for k, v in (missing if show_all else missing[:15]):
            print(f"    {k} = {v}")
    if extra_nonzero and show_all:
        print(f"\nWE WROTE NON-ZERO, ISO DID NOT PUBLISH ({len(extra_nonzero)})")
        for k, v in extra_nonzero[:30]:
            print(f"    {k} = {v}")
    if not differ and not missing:
        print("no numeric disagreement")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
