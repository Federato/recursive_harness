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

**Each jurisdiction is reviewed as its RESOLVED rulebook, state over its own
DECLARED parent (N5) -- `--juris TX` merges Texas's own filed package with
whichever countrywide package TX's OWN edition actually declares as parent
(`declared_parent`, read from the state package's `xs:import`, never
"whichever CW happens to share a date"), old snapshot and new snapshot each
resolved independently.** This is deliberately NOT a per-file diff: two
different questions -- "did TX's own filing change" and "did TX's effective
rulebook change" -- have different answers whenever TX inherits a countrywide
change without refiling, and the second is the one a review has to answer,
because it's the one that changes a premium. **First cut of this tool
diffed each package against its own history only and missed exactly this:
`--juris TX` at the 2027 cliff didn't show `ProdsCompldOpsExclusion`,
because that field is filed at the countrywide layer and TX's own package
never mentions it either way.** Every finding below is tagged with WHICH
layer it came from (`[state]` or `[CW]`), so a state-declared change and an
inherited one are never confused with each other even though both now
appear under the same jurisdiction code. `--juris CW` on its own still
reviews the countrywide package in isolation (it has no parent), and
remains the direct source for anything a state-level review attributes to
`[CW]`.

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


def resolved_parent(pkg: Package, by_id: dict[str, Package]) -> Package | None:
    """The package THIS ONE actually declares as parent (N5) -- never the
    newest countrywide edition, never one sharing its date by coincidence."""
    if pkg.is_countrywide or not pkg.declared_parent:
        return None
    return by_id.get(pkg.declared_parent)


def _merged_fields(pkg: Package, parent: Package | None
                   ) -> dict[tuple[str, str], tuple[dict, str]]:
    """Parent's fields first, state's own override by key -- same precedence
    `Schema._load` gives the engine's own resolved rulebook. Each value
    carries which layer supplied it, for attribution in the report."""
    out = {}
    if parent is not None:
        for k, v in _fields(parent).items():
            out[k] = (v, parent.identity.juris)
    for k, v in _fields(pkg).items():
        out[k] = (v, pkg.identity.juris)
    return out


def _merged_tables(pkg: Package, parent: Package | None
                   ) -> dict[str, tuple[Path, str]]:
    def own(p: Package) -> dict[str, Path]:
        return {**_tables(p, "Rate Tables", "RateTable"),
                **_tables(p, "Domain Tables", "DomainTable")}
    out = {}
    if parent is not None:
        for name, path in own(parent).items():
            out[name] = (path, parent.identity.juris)
    for name, path in own(pkg).items():
        out[name] = (path, pkg.identity.juris)
    return out


def edition_review(old: Package, new: Package,
                   old_parent: Package | None, new_parent: Package | None) -> dict:
    """Every structural change between two RESOLVED snapshots of the SAME
    jurisdiction, old -> new -- state merged over its own declared parent at
    each snapshot, never a raw single-file diff. Neither package's own
    content is modified or assumed -- every finding is read fresh."""
    of, nf = (_merged_fields(old, old_parent), _merged_fields(new, new_parent))
    added_fields = sorted(set(nf) - set(of))
    removed_fields = sorted(set(of) - set(nf))
    changed_fields = []
    for key in sorted(set(of) & set(nf)):
        (o, _osrc), (n, nsrc) = of[key], nf[key]
        diffs = [(a, o.get(a, ""), n.get(a, "")) for a in _WATCHED_ATTRS
                if (o.get(a) or "") != (n.get(a) or "")]
        if diffs:
            changed_fields.append((key, nsrc, diffs))

    ot, nt = (_merged_tables(old, old_parent), _merged_tables(new, new_parent))
    added_tables = sorted(set(nt) - set(ot))
    removed_tables = sorted(set(ot) - set(nt))

    header_changed = []
    for name in sorted(set(ot) & set(nt)):
        (opath, _osrc), (npath, nsrc) = ot[name], nt[name]
        oh, nh = _header(opath), _header(npath)
        if oh != nh:
            header_changed.append((name, nsrc, oh, nh))

    return {
        "juris": new.identity.juris,
        "old": old.pkg_id, "new": new.pkg_id,
        "old_parent": old_parent.pkg_id if old_parent else None,
        "new_parent": new_parent.pkg_id if new_parent else None,
        "added_fields": [(k, nf[k][1]) for k in added_fields],
        "removed_fields": [(k, of[k][1]) for k in removed_fields],
        "changed_fields": changed_fields,
        "added_tables": [(n, nt[n][1]) for n in added_tables],
        "removed_tables": [(n, ot[n][1]) for n in removed_tables],
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
    old_full = r["old"] + (f" over {r['old_parent']}" if r["old_parent"] else "")
    new_full = r["new"] + (f" over {r['new_parent']}" if r["new_parent"] else "")
    lines = [f"{r['juris']}: {old_full} -> {new_full}"]
    if r["added_fields"]:
        lines.append(f"  fields ADDED ({len(r['added_fields'])}): " +
                     ", ".join(f"{t}.{c} [{src}]" for (t, c), src in r["added_fields"]))
    if r["removed_fields"]:
        lines.append(f"  fields REMOVED ({len(r['removed_fields'])}): " +
                     ", ".join(f"{t}.{c} [{src}]" for (t, c), src in r["removed_fields"]))
    for (t, c), src, diffs in r["changed_fields"]:
        for attr, o, n in diffs:
            lines.append(f"  field CHANGED {t}.{c} [{src}]: {attr} {o!r} -> {n!r}")
    if r["added_tables"]:
        lines.append(f"  tables ADDED ({len(r['added_tables'])}): " +
                     ", ".join(f"{n} [{src}]" for n, src in r["added_tables"]))
    if r["removed_tables"]:
        lines.append(f"  tables REMOVED ({len(r['removed_tables'])}): " +
                     ", ".join(f"{n} [{src}]" for n, src in r["removed_tables"]))
    for name, src, oh, nh in r["header_changed"]:
        added = [c for c in nh if c not in oh]
        removed = [c for c in oh if c not in nh]
        detail = []
        if added:
            detail.append(f"+{','.join(added)}")
        if removed:
            detail.append(f"-{','.join(removed)}")
        lines.append(f"  table COLUMNS CHANGED {name} [{src}]: "
                     f"{'; '.join(detail) or 'reordered'}")
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
    by_id: dict[str, Package] = {}
    for p in packages:
        by_juris.setdefault(p.identity.juris, []).append(p)
        by_id[p.pkg_id] = p

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
        old_parent = resolved_parent(old, by_id)
        new_parent = resolved_parent(new, by_id)
        if not old.is_countrywide and old.declared_parent and old_parent is None:
            skipped.append((j, f"{old.pkg_id} declares parent "
                              f"{old.declared_parent!r}, not in the corpus"))
            continue
        if not new.is_countrywide and new.declared_parent and new_parent is None:
            skipped.append((j, f"{new.pkg_id} declares parent "
                              f"{new.declared_parent!r}, not in the corpus"))
            continue
        results.append(edition_review(old, new, old_parent, new_parent))

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
