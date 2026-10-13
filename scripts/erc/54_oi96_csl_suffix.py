"""OI-96, generalized: did the 2027 filing drop the " CSL" suffix from limit
values, and in how many jurisdictions, and in which tables?

Found by hand in TX's ILFPremOps while root-causing OI-96 (BUILD-LOG.md
Entry 45): the 2027 edition's `ILFPremOps.RateTable.csv` carries
`EachOccurrenceLimit = "1,000,000"` where the prior edition carried
`"1,000,000 CSL"` -- same table, same column, same factor, just reformatted.
A stored payload built against the old format then misses every lookup keyed
on that column in the new edition.

**The instruction behind this script**: a value-format change like this is
not a one-state, one-table thing to notice by hand and move on from -- it
should be checked across every jurisdiction and every shared table whenever a
new edition lands, the same discipline OI-95 already applied to the ELP
regime split. This measures, decides nothing, and changes no engine code.

Method: for each jurisdiction, find its first 2027-edition package (the one
whose own edition date is >= CLASS_BASIS_CLIFF) and the edition immediately
before it. For every Rate Tables CSV present in BOTH by filename, check each
column for whether the " CSL" substring's presence flips from "some rows
have it" in the old file to "no rows have it" in the new one (or the
reverse). That is the exact shape of the TX finding, generalized to every
table and every state rather than assumed to be ILF-only.

Run: python scripts/erc/54_oi96_csl_suffix.py
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from gl_engine.config import CLASS_BASIS_CLIFF, COUNTRYWIDE       # noqa: E402
from gl_engine.erc.discovery import discover                      # noqa: E402

OUT = Path(__file__).resolve().parent / "out" / "oi96_csl_suffix.txt"


def read_rows(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as fh:
        r = csv.reader(fh)
        head = next(r, None)
        if head is None:
            return [], []
        return head, list(r)


def csl_columns(header, rows) -> set:
    """Column indices where at least one row's cell contains ' CSL'."""
    out = set()
    for i in range(len(header)):
        for row in rows:
            if i < len(row) and " CSL" in row[i]:
                out.add(i)
                break
    return out


def edition_pair(packages: list) -> tuple:
    """(pre-2027 edition, the first-effective 2027-vintage edition) for one
    jurisdiction's own package list, sorted oldest first."""
    at_or_after = [p for p in packages if p.identity.edition >= CLASS_BASIS_CLIFF]
    before = [p for p in packages if p.identity.edition < CLASS_BASIS_CLIFF]
    if not at_or_after or not before:
        return None, None
    return before[-1], at_or_after[0]


def main() -> int:
    pkgs = discover()
    by_juris: dict = {}
    for p in pkgs:
        by_juris.setdefault(p.identity.juris, []).append(p)
    for v in by_juris.values():
        v.sort(key=lambda p: p.identity.sort_key)

    lines = []
    affected_jurisdictions = set()
    table_hits: dict = {}          # table name -> set of jurisdictions
    checked_pairs = 0
    no_pair = []

    for juris in sorted(by_juris):
        old, new = edition_pair(by_juris[juris])
        if old is None or new is None:
            no_pair.append(juris)
            continue
        checked_pairs += 1
        old_dir = old.content / "Rate Tables"
        new_dir = new.content / "Rate Tables"
        if not old_dir.is_dir() or not new_dir.is_dir():
            continue
        old_tables = {f.name: f for f in old_dir.glob("*.RateTable.csv")}
        new_tables = {f.name: f for f in new_dir.glob("*.RateTable.csv")}
        shared = sorted(set(old_tables) & set(new_tables))

        for name in shared:
            oh, orows = read_rows(old_tables[name])
            nh, nrows = read_rows(new_tables[name])
            if not orows or not nrows or oh != nh:
                continue                     # header changed -- a different finding
            old_csl = csl_columns(oh, orows)
            new_csl = csl_columns(nh, nrows)
            dropped = old_csl - new_csl
            if dropped:
                cols = ", ".join(oh[i] for i in sorted(dropped))
                lines.append(f"  {juris}: {name} dropped ' CSL' in [{cols}] "
                             f"({old.identity} -> {new.identity})")
                affected_jurisdictions.add(juris)
                table_hits.setdefault(name.replace(".RateTable.csv", ""),
                                      set()).add(juris)

    header = [
        "OI-96, generalized -- the ' CSL' suffix drop, measured across every "
        "jurisdiction",
        f"Jurisdictions with both a pre-cliff and a 2027-vintage edition: "
        f"{checked_pairs}",
        f"No qualifying pair (2027 edition not yet filed, or no prior "
        f"edition): {no_pair or 'none'}",
        "",
        f"Jurisdictions where at least one shared table dropped ' CSL': "
        f"{len(affected_jurisdictions)} of {checked_pairs}",
        f"  {sorted(affected_jurisdictions)}",
        "",
        f"Tables affected, and in how many jurisdictions:",
    ]
    for name in sorted(table_hits, key=lambda n: -len(table_hits[n])):
        js = table_hits[name]
        header.append(f"  {name}: {len(js)} jurisdiction(s) -- {sorted(js)}")
    header.append("")
    header.append("Every instance found:")

    report = "\n".join(header) + "\n" + "\n".join(lines) + "\n"
    print(report)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(report, encoding="utf-8")
    print(f"\nWritten to {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
