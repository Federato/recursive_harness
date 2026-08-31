"""A standing mechanism to review what a new edition changed, before it's
trusted -- run this every time a new edition lands in the corpus, not only
when a defect is already suspected.

**What raised this.** OI-96 (a reformatted limit value) and OI-97 (a newly-
required field) were both found by a person happening to look -- one by
hand-testing the 2027 cliff, the other by asking "does that number look
right" about the first fix's own result. Neither was caught by anything that
runs automatically. The corrected lesson (BUILD-LOG.md Entry 56, amended):
**the gap is process, not a checklist item** -- every new edition needs an
automatic, corpus-wide sweep for structural change, run as a standing step,
not built ad hoc after each new shape of defect is found by chance.

**What this checks, for one jurisdiction's two most recent editions (or an
explicit --old/--new pair):**

1. **Fields added, removed, or changed** -- `Form Fields/Fields.FormField.csv`,
   read per package (not merged state-over-countrywide, so a change is
   attributed to the layer that actually made it). "Changed" flags a
   difference in `Type`, `DomainTableName`, `PolicyRequired`, `QuoteRequired`,
   `Condition` or `RequiredCondition` -- the attributes that decide whether a
   field is legal, required, or gates another field's coverage. This is
   exactly OI-97's shape: `ProdsCompldOpsExclusion` would have shown as
   ADDED at GL_CW_20270401.
2. **Rate/domain tables added or removed** -- every `*.RateTable.csv` and
   `*.DomainTable.csv` filename present in one edition and not the other.
3. **Column headers changed on a table present in both editions** -- a cheap,
   structural signal (added/removed/reordered columns), not a full value
   diff.

**What this does NOT check**, on purpose, so the scope is honest rather than
implied complete: it does not diff table CONTENTS cell-by-cell (OI-96's
shape -- a value reformatted within an unchanged column needs
`54_oi96_csl_suffix.py` or a similar targeted script, because a general
cell-by-cell diff across every table in the corpus is a different cost
tradeoff than this structural sweep). It does not diff Rules (the rating
logic itself) or DataDefs XSDs directly -- `Form Fields.csv` is ISO's own
business-level declaration of the same information and is what the engine's
`Schema` class already reads, so a change invisible there is a change the
engine's own schema layer would not see either.

**Each jurisdiction code is reviewed against its OWN edition history only --
`--juris TX` diffs Texas's own filed package, never its countrywide
parent.** This mirrors how ISO actually files the corpus (a state package
and its countrywide parent are versioned independently, N5) rather than
merging them, which would attribute a countrywide change to whichever state
happened to be asked about. **The consequence, confirmed while building
this: `--juris TX` at the 2027 cliff does NOT show `ProdsCompldOpsExclusion`
-- that field is countrywide, and only shows up under `--juris CW`.** A full
review after a new edition lands means running this once per package that
actually changed, including `CW` whenever the countrywide parent refiles --
`--all` already includes `CW` alongside every state code. A state that
inherits a countrywide change without refiling its own package will not
show it under its own code, by design; the review is per FILED package, not
per resolved rulebook.

Run:
    python scripts/erc/56_edition_review.py --juris TX
    python scripts/erc/56_edition_review.py --all
    python scripts/erc/56_edition_review.py --juris TX --old 20250801 --new 20270401
"""
from __future__ import annotations

import argparse
import csv
import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from gl_engine.config import COUNTRYWIDE                          # noqa: E402
from gl_engine.erc.discovery import discover, read_text, Package  # noqa: E402

OUT = Path(__file__).resolve().parent / "out"

FIELD_FILE = Path("Form Fields") / "Fields.FormField.csv"
_WATCHED_ATTRS = ("Type", "DomainTableName", "PolicyRequired",
                  "QuoteRequired", "Condition", "RequiredCondition")


def _csv_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [r for r in csv.DictReader(io.StringIO(read_text(path))) if r]


def _fields(pkg: Package) -> dict[tuple[str, str], dict]:
    out = {}
    for r in _csv_rows(pkg.content / FIELD_FILE):
        key = (r.get("TableName", ""), r.get("ColumnName", ""))
        if key[1]:
            out[key] = r
    return out


def _tables(pkg: Package, subdir: str, suffix: str) -> dict[str, Path]:
    d = pkg.content / subdir
    if not d.exists():
        return {}
    return {f.name: f for f in d.glob(f"*.{suffix}.csv")}


def _header(path: Path) -> tuple[str, ...]:
    rows = list(csv.reader(io.StringIO(read_text(path))))
    return tuple(rows[0]) if rows else ()


def edition_review(old: Package, new: Package) -> dict:
    """Every structural change between two packages of the SAME jurisdiction,
    old -> new. Neither package's own content is modified or assumed --
    every finding is read fresh from both."""
    of, nf = _fields(old), _fields(new)
    added_fields = sorted(set(nf) - set(of))
    removed_fields = sorted(set(of) - set(nf))
    changed_fields = []
    for key in sorted(set(of) & set(nf)):
        o, n = of[key], nf[key]
        diffs = [(a, o.get(a, ""), n.get(a, "")) for a in _WATCHED_ATTRS
                if (o.get(a) or "") != (n.get(a) or "")]
        if diffs:
            changed_fields.append((key, diffs))

    o_rt, n_rt = (_tables(old, "Rate Tables", "RateTable"),
                 _tables(new, "Rate Tables", "RateTable"))
    o_dt, n_dt = (_tables(old, "Domain Tables", "DomainTable"),
                 _tables(new, "Domain Tables", "DomainTable"))
    o_tables, n_tables = {**o_rt, **o_dt}, {**n_rt, **n_dt}
    added_tables = sorted(set(n_tables) - set(o_tables))
    removed_tables = sorted(set(o_tables) - set(n_tables))

    header_changed = []
    for name in sorted(set(o_tables) & set(n_tables)):
        oh, nh = _header(o_tables[name]), _header(n_tables[name])
        if oh != nh:
            header_changed.append((name, oh, nh))

    return {
        "juris": new.identity.juris,
        "old": old.pkg_id, "new": new.pkg_id,
        "added_fields": added_fields, "removed_fields": removed_fields,
        "changed_fields": changed_fields,
        "added_tables": added_tables, "removed_tables": removed_tables,
        "header_changed": header_changed,
    }


def has_findings(r: dict) -> bool:
    return bool(r["added_fields"] or r["removed_fields"] or r["changed_fields"]
               or r["added_tables"] or r["removed_tables"] or r["header_changed"])


def latest_two_editions(packages: list[Package]) -> tuple[Package | None, Package | None]:
    """The newest version of the two most recent DISTINCT edition dates.

    A within-edition version bump (a corpus refresh, not a new filing) is not
    a new edition to review -- this compares filings, not pulls.
    """
    by_edition: dict[str, list[Package]] = {}
    for p in packages:
        by_edition.setdefault(p.identity.edition, []).append(p)
    editions = sorted(by_edition)
    if len(editions) < 2:
        return None, None
    old_ed, new_ed = editions[-2], editions[-1]
    newest = lambda ps: sorted(ps, key=lambda p: p.identity.sort_key)[-1]
    return newest(by_edition[old_ed]), newest(by_edition[new_ed])


def render(r: dict) -> str:
    lines = [f"{r['juris']}: {r['old']} -> {r['new']}"]
    if r["added_fields"]:
        lines.append(f"  fields ADDED ({len(r['added_fields'])}): " +
                     ", ".join(f"{t}.{c}" for t, c in r["added_fields"]))
    if r["removed_fields"]:
        lines.append(f"  fields REMOVED ({len(r['removed_fields'])}): " +
                     ", ".join(f"{t}.{c}" for t, c in r["removed_fields"]))
    for (t, c), diffs in r["changed_fields"]:
        for attr, o, n in diffs:
            lines.append(f"  field CHANGED {t}.{c}: {attr} {o!r} -> {n!r}")
    if r["added_tables"]:
        lines.append(f"  tables ADDED ({len(r['added_tables'])}): " +
                     ", ".join(r["added_tables"]))
    if r["removed_tables"]:
        lines.append(f"  tables REMOVED ({len(r['removed_tables'])}): " +
                     ", ".join(r["removed_tables"]))
    for name, oh, nh in r["header_changed"]:
        added = [c for c in nh if c not in oh]
        removed = [c for c in oh if c not in nh]
        detail = []
        if added:
            detail.append(f"+{','.join(added)}")
        if removed:
            detail.append(f"-{','.join(removed)}")
        lines.append(f"  table COLUMNS CHANGED {name}: {'; '.join(detail) or 'reordered'}")
    return "\n".join(lines)


def main(argv) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--juris", help="one jurisdiction, or CW for countrywide")
    ap.add_argument("--all", action="store_true",
                    help="every jurisdiction plus countrywide")
    ap.add_argument("--old", help="explicit old edition YYYYMMDD, "
                                  "overrides auto-detection")
    ap.add_argument("--new", help="explicit new edition YYYYMMDD")
    a = ap.parse_args(argv)
    if not a.juris and not a.all:
        print("pass --juris X or --all")
        return 2

    packages = discover()
    by_juris: dict[str, list[Package]] = {}
    for p in packages:
        by_juris.setdefault(p.identity.juris, []).append(p)

    jurisdictions = [a.juris.upper()] if a.juris else sorted(by_juris)
    results, skipped = [], []
    for j in jurisdictions:
        pool = by_juris.get(j, [])
        if not pool:
            skipped.append((j, "not in corpus"))
            continue
        if a.old and a.new:
            old_matches = [p for p in pool if p.identity.edition == a.old]
            new_matches = [p for p in pool if p.identity.edition == a.new]
            if not old_matches or not new_matches:
                skipped.append((j, f"missing edition {a.old if not old_matches else a.new}"))
                continue
            old = sorted(old_matches, key=lambda p: p.identity.sort_key)[-1]
            new = sorted(new_matches, key=lambda p: p.identity.sort_key)[-1]
        else:
            old, new = latest_two_editions(pool)
            if old is None:
                skipped.append((j, "fewer than 2 editions on file"))
                continue
        results.append(edition_review(old, new))

    flagged = [r for r in results if has_findings(r)]
    print(f"reviewed {len(results)} jurisdiction(s), "
         f"{len(flagged)} with a change to review, "
         f"{len(skipped)} skipped\n")
    for j, why in skipped:
        print(f"  skip {j}: {why}")
    if skipped:
        print()

    out_lines = []
    for r in flagged:
        block = render(r)
        print(block)
        print()
        out_lines.append(block)

    if out_lines:
        OUT.mkdir(parents=True, exist_ok=True)
        dest = OUT / ("edition_review_all.txt" if a.all
                      else f"edition_review_{jurisdictions[0]}.txt")
        dest.write_text("\n\n".join(out_lines), encoding="utf-8")
        print(f"written: {dest}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
