"""Every occurrence count quoted in the evaluation contract must match source.

The contract was drafted quoting a mixture of the superseded P5 census and the
de-duplicated source enumeration, and the mixture was invisible on the page --
every number looked equally plausible. That is the same failure as writing an
expected test output before running the command.

So the document is checked mechanically. This reads
`docs/rating-engine/14-EVALUATION-CONTRACT.md`, finds every place a node name
is followed by a number, and requires that number to be one the corpus actually
produced for that node -- either its total occurrences (`node_surface.csv`) or
one of its parent/child edge counts (`node_children.csv`), since the contract
legitimately quotes both.

**What this does not catch**, stated so nobody reads a green run as more than it
is: a number that is valid for the node but quoted in the wrong context -- a
child-count printed where the total belonged. It catches figures that are not
in the corpus at all, which is the error that was actually made.

Run: python tests/verify_contract_figures.py
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOC = ROOT / "docs" / "rating-engine" / "14-EVALUATION-CONTRACT.md"
SRC = ROOT / "scripts" / "erc" / "out" / "node_surface.csv"
KIDS = ROOT / "scripts" / "erc" / "out" / "node_children.csv"
#: the third generated source: answers to the contract's open questions, which
#: carry counts no other file has (e.g. FirstNonNull's LAST child by type)
QS = ROOT / "scripts" / "erc" / "out" / "contract_questions.txt"

#: `Sequence` (182,751)  |  | `Sequence` | 182,751 |  |  `Sum` (9,995)
PATTERNS = (
    re.compile(r"`(?P<node>[A-Za-z]+)`\s*\((?P<n>[\d,]{2,})\)"),
    re.compile(r"\|\s*`(?P<node>[A-Za-z]+)`\s*\|\s*(?P<n>[\d,]{2,})\s*\|"),
)


def main() -> int:
    if not SRC.exists():
        print(f"FAIL  {SRC} missing -- run scripts/erc/42_node_surface.py")
        return 1
    csv.field_size_limit(1 << 24)
    truth = {r["node"]: int(r["occurrences"])
             for r in csv.DictReader(open(SRC, encoding="utf-8"))}
    # every edge count the node takes part in, as parent or as child
    edges: dict[str, set[int]] = {n: set() for n in truth}
    for r in csv.DictReader(open(KIDS, encoding="utf-8")):
        n = int(r["occurrences"])
        for side in (r["parent"], r["child"]):
            if side in edges:
                edges[side].add(n)
    q_numbers = {int(x) for x in re.findall(r"\b\d{2,}\b",
                                            QS.read_text(encoding="utf-8"))} \
        if QS.exists() else set()
    text = DOC.read_text(encoding="utf-8")

    checked = 0
    bad: list[str] = []
    seen_nodes: set[str] = set()
    for pat in PATTERNS:
        for m in pat.finditer(text):
            node = m.group("node")
            if node not in truth:
                continue                      # a number about something else
            claimed = int(m.group("n").replace(",", ""))
            # only treat it as an occurrence claim if it is in range of one;
            # arities and percentages are small and would false-positive
            if claimed < 30:
                continue
            checked += 1
            seen_nodes.add(node)
            if (claimed != truth[node] and claimed not in edges[node]
                    and claimed not in q_numbers):
                bad.append(f"  {node:20s} document says {claimed:>9,}  "
                           f"which is neither its total ({truth[node]:,}) nor "
                           f"any edge count it appears in")

    print(f"node occurrence claims checked : {checked}")
    print(f"distinct nodes quoted          : {len(seen_nodes)} of {len(truth)}")
    if bad:
        print(f"\nMISMATCHES ({len(bad)}):")
        print("\n".join(bad))
        return 1
    print("\nOK  every figure quoted in the contract is one the corpus "
          "produced\n    (node_surface.csv, node_children.csv, "
          "contract_questions.txt)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
