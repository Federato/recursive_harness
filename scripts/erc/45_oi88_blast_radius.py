"""OI-88: how much of the corpus a null-through-arithmetic fix would touch.

The defect (OI-88 / D1): inside a `FirstNonNull`, a branch whose value arrives
through arithmetic cannot *become* null -- `to_decimal` raises instead, and the
exception escapes the `FirstNonNull` before the next branch is evaluated. ISO's
countrywide fallbacks that are written as `Round(Lookup(state))` then
`Round(Lookup('CW'))` are therefore unreachable.

This script measures, and decides nothing. Three questions:

  Q1  How many `FirstNonNull` sites have refusing arithmetic inside a branch?
      That is the true population a fix touches. Nobody had counted it.

  Q2  Of those, how many carry a total fallback -- a trailing `Constant` that
      can never be null? Those are the sites where loosening the refusal could
      let a *genuine* missing value be absorbed into a plausible wrong premium
      instead of stopping. This is the number that decides how safe the fix is,
      and it is the argument against the blunt form of it.

  Q3  Which branches are actually at risk -- refusing arithmetic over an operand
      that can plausibly be null (a `Lookup`, or a `Value`/`FirstValue` reading
      a data def with no constant to fall back on). Q1 is an upper bound; this
      is the narrower reading.

`Sum` and `Max` are NOT refusing nodes: both already skip nulls
(`gl_engine/interp/nodes.py:569,609`). The engine's null policy across
arithmetic is already deliberately inconsistent, which is why this is a
question about where a line falls rather than whether to loosen the engine.

Emits out/oi88_blast_radius.txt.
"""
from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
c = import_module("00_common")
rules_packages = import_module("42_node_surface").rules_packages

#: Nodes that call `to_decimal` and therefore raise on null.
#: Taken from `gl_engine/interp/nodes.py` call sites, not from the schema.
REFUSING = frozenset({
    "Round",            # nodes.py:618  -- the node in the OI-88 reproduction
    "Truncate",         # nodes.py:624
    "Product",          # nodes.py:577
    "Subtract",         # nodes.py:586-587
    "Divide",           # nodes.py:593-594
    "GreaterThan",      # nodes.py:287  via _cmp
    "LessThan",         # nodes.py:292  via _cmp
    "GreaterThanOrEqual",   # nodes.py:297
    "LessThanOrEqual",      # nodes.py:302
    "PadLeft",          # nodes.py:656  width operand
    "DateAdd",          # nodes.py:700  count operand
    "DateCreate",       # nodes.py:722  all three operands
})

#: Nodes that can hand a null *to* arithmetic. A `Lookup` that misses yields
#: null -- that is the whole mechanism of the OI-88 reproduction. A `Value` or
#: `FirstValue` reading a data def yields null when the def is absent, unless it
#: also carries a `FromConstant` to fall back on.
def _can_be_null(el) -> bool:
    t = c.lname(el.tag)
    if t == "Lookup":
        return True
    if t in ("Value", "FirstValue"):
        return ("FromDataDef" in el.attrib
                and "FromConstant" not in el.attrib)
    return False


def _walk(el):
    """The element and every descendant."""
    yield el
    for ch in el:
        yield from _walk(ch)


def _refusing_in(branch) -> list:
    """Every refusing-arithmetic node in this branch's subtree."""
    return [e for e in _walk(branch) if c.lname(e.tag) in REFUSING]


def _at_risk(node) -> bool:
    """Refusing arithmetic with a plausibly-null operand beneath it."""
    return any(_can_be_null(e) for e in _walk(node))


def main() -> None:
    pkgs, n_dirs, dupes = rules_packages()

    total_fnn = 0
    q1_sites = 0                    # FirstNonNull with refusing arithmetic
    q1_branches = 0
    q2_with_fallback = 0            # ...of those, a trailing Constant
    q2_without = 0
    q3_sites = 0                    # ...narrowed to plausibly-null operands
    q3_branches = 0
    q3_with_fallback = 0

    by_node = Counter()             # which refusing node, in at-risk branches
    by_file = Counter()             # which rule file holds the at-risk sites
    by_pkg = set()
    q3_pkgs = set()
    last_child = Counter()
    examples: list[str] = []

    for p in pkgs:
        pid = p.pkg_id
        for f in sorted((p.content / "Rules").glob("*.Rule.xml")):
            try:
                root = ET.fromstring(c.read_text(f))
            except ET.ParseError:
                continue
            stem = f.name.replace(".Rule.xml", "")

            for el in root.iter():
                if c.lname(el.tag) != "FirstNonNull":
                    continue
                total_fnn += 1
                kids = list(el)
                if not kids:
                    continue

                fallback = c.lname(kids[-1].tag) == "Constant"
                last_child[c.lname(kids[-1].tag)] += 1

                hits = [(b, _refusing_in(b)) for b in kids]
                hits = [(b, r) for b, r in hits if r]
                if not hits:
                    continue

                q1_sites += 1
                q1_branches += len(hits)
                by_pkg.add(pid)
                if fallback:
                    q2_with_fallback += 1
                else:
                    q2_without += 1

                risky = [(b, r) for b, r in hits
                         if any(_at_risk(n) for n in r)]
                if risky:
                    q3_sites += 1
                    q3_branches += len(risky)
                    q3_pkgs.add(pid)
                    if fallback:
                        q3_with_fallback += 1
                    by_file[stem] += 1
                    for _b, r in risky:
                        for n in r:
                            if _at_risk(n):
                                by_node[c.lname(n.tag)] += 1
                    if len(examples) < 12:
                        examples.append(f"{pid}  {stem}")

    out = []
    A = out.append
    A("OI-88 blast radius -- null through arithmetic inside FirstNonNull")
    A("=" * 70)
    A(f"packages scanned: {len(pkgs)} ({n_dirs} dirs, {len(dupes)} duplicates "
      f"dropped)")
    A(f"FirstNonNull sites in the corpus: {total_fnn}")
    A("")

    A("Q1  Sites with refusing arithmetic inside a branch (upper bound)")
    A(f"    sites:    {q1_sites} of {total_fnn} "
      f"({100 * q1_sites / max(1, total_fnn):.2f}%)")
    A(f"    branches: {q1_branches}")
    A(f"    packages: {len(by_pkg)} of {len(pkgs)}")
    A("")

    A("Q2  Of those sites, does a trailing Constant stand ready to absorb a")
    A("    genuine missing value if the refusal is loosened?")
    A(f"    total fallback present:  {q2_with_fallback} "
      f"({100 * q2_with_fallback / max(1, q1_sites):.2f}%)")
    A(f"    no total fallback:       {q2_without}")
    A("")

    A("Q3  Narrowed: refusing arithmetic over a plausibly-null operand")
    A("    (a Lookup, or a data-def read with no FromConstant beneath it)")
    A(f"    sites:    {q3_sites} of {total_fnn} "
      f"({100 * q3_sites / max(1, total_fnn):.2f}%)")
    A(f"    branches: {q3_branches}")
    A(f"    packages: {len(q3_pkgs)} of {len(pkgs)}")
    A(f"    of these sites, total fallback present: {q3_with_fallback} "
      f"({100 * q3_with_fallback / max(1, q3_sites):.2f}%)")
    A("")

    A("    by refusing node:")
    for k, n in by_node.most_common():
        A(f"      {k:20s} {n:8d}")
    A("")

    A("    top rule files by at-risk site count:")
    for k, n in by_file.most_common(15):
        A(f"      {n:6d}  {k}")
    A("")

    A("    first examples:")
    for e in examples:
        A(f"      {e}")
    A("")

    A("    every FirstNonNull's last child (exhaustion, for reconciliation")
    A("    against 44_contract_questions Q3):")
    for k, n in last_child.most_common():
        A(f"      {k:20s} {n:8d}")

    text = "\n".join(out)
    print(text)
    dest = Path(__file__).parent / "out" / "oi88_blast_radius.txt"
    dest.parent.mkdir(exist_ok=True)
    dest.write_text(text, encoding="utf-8")
    print(f"\nwrote {dest}")


if __name__ == "__main__":
    main()
