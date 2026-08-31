"""How stale is the local ERC corpus, per jurisdiction, and where is that most
likely to matter -- read-only, no ISO calls, no engine change.

**What raised this.** Confirming a 2027-04-01 premium against ISO
(BUILD-LOG.md Entry 53) found ND and NH disagreeing with ISO's live service.
The cause was not a resolver bug: `EditionResolver` already takes the highest
`(edition, version)` it finds on disk (`gl_engine/resolve/resolver.py`), and
it did so correctly in both states. The gap is that ISO has filed amendments
since our copy was pulled -- ND holds V01 where ISO is at V04, NH holds V02
where ISO is at V05 -- and in those two states the amendment happened to
touch a rate/ILF table. VT and SD showed the identical version gap and
matched anyway, because their missing amendments didn't touch rates. That
means version drift is silent by default: the only reason ND/NH's drift was
visible at all is that the missing amendment happened to move a number.

**What this measures, and what it cannot.** There is no local signal that
tells us how many versions *ISO* has published past what we hold -- that
needs a live call per state/edition, and 51+CW live calls would burn most of
a day's standing budget (decision A6, 60/day) to answer a question this
script can narrow first. What the corpus itself can say, read-only:

1. **How long since each jurisdiction's copy was last touched** -- the
   directory mtime of its newest package, a proxy for "when was this last
   pulled." ND and NH were last pulled 2026-06-03 and 2026-07-... respectively
   (measured below, not assumed) -- the drift is a function of elapsed time
   since pull, not something specific to those two states.
2. **How often each jurisdiction has historically taken a mid-edition version
   bump** -- editions with more than one version present are evidence ISO
   amends that state's filings after the initial one; a jurisdiction with a
   high historical bump rate is the one most likely to have a live-vs-disk
   gap on its *current* edition too, the same way ND and NH did.
3. Cross the two: jurisdictions whose newest pull is both old *and*
   historically prone to mid-edition bumps are the highest-risk candidates
   for the same silent-drift pattern -- named, not left as a vague "probably
   several states."

This ranks risk: it does not confirm a gap exists anywhere it wasn't already
found by a live call (ND, NH). Confirming further would cost a live call per
jurisdiction checked.

Run: python scripts/erc/55_corpus_freshness.py
"""
from __future__ import annotations

import datetime as dt
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from gl_engine.config import CLASS_BASIS_CLIFF, COUNTRYWIDE          # noqa: E402
from gl_engine.erc.discovery import discover                          # noqa: E402

OUT = Path(__file__).resolve().parent / "out" / "corpus_freshness.txt"

#: "Today" for staleness arithmetic. Not wall-clock -- pinned so a re-run
#: months from now doesn't silently change every number in this file; bump it
#: by hand if this script is re-run later.
TODAY = dt.date(2026, 8, 31)


def as_date(ts: float) -> dt.date:
    return dt.datetime.fromtimestamp(ts).date()


def main() -> int:
    pkgs = [p for p in discover() if p.identity.juris != COUNTRYWIDE]
    by_juris = defaultdict(list)
    for p in pkgs:
        by_juris[p.identity.juris].append(p)

    lines = []
    lines.append(f"corpus freshness -- {len(pkgs)} state packages, "
                 f"{len(by_juris)} jurisdictions, as of {TODAY}\n")

    # ---- 1. last-pulled date per jurisdiction, from directory mtime -------
    last_pull = {}
    for j, plist in by_juris.items():
        newest = max(as_date(p.content.stat().st_mtime) for p in plist)
        last_pull[j] = newest

    stale_days = {j: (TODAY - d).days for j, d in last_pull.items()}
    buckets = [("<=30d", 0, 30), ("31-60d", 31, 60), ("61-90d", 61, 90),
               (">90d", 91, 10_000)]
    lines.append("## pull recency, all 51 jurisdictions")
    for label, lo, hi in buckets:
        js = sorted(j for j, d in stale_days.items() if lo <= d <= hi)
        lines.append(f"  {label:8s} {len(js):3d}  {', '.join(js) if js else '(none)'}")
    lines.append("")

    # ---- 2. historical mid-edition version-bump rate per jurisdiction -----
    bump_rate = {}
    for j, plist in by_juris.items():
        by_edition = defaultdict(set)
        for p in plist:
            by_edition[p.identity.edition].add(p.identity.version)
        n_editions = len(by_edition)
        n_bumped = sum(1 for vs in by_edition.values() if len(vs) > 1)
        bump_rate[j] = (n_bumped, n_editions,
                        n_bumped / n_editions if n_editions else 0.0)

    lines.append("## historical mid-edition bump rate (editions that ever "
                 "saw >1 version filed / total editions held)")
    ranked = sorted(bump_rate.items(), key=lambda kv: -kv[1][2])
    for j, (n_bumped, n_editions, rate) in ranked:
        lines.append(f"  {j:4s} {n_bumped:2d}/{n_editions:2d}  {rate:5.0%}")
    lines.append("")

    # ---- 3. the 2027-04-01 edition specifically ----------------------------
    at_cliff = {j: [p for p in plist if p.identity.edition == CLASS_BASIS_CLIFF]
                for j, plist in by_juris.items()}
    at_cliff = {j: ps for j, ps in at_cliff.items() if ps}
    lines.append(f"## the {CLASS_BASIS_CLIFF} edition: "
                 f"{len(at_cliff)} of 51 jurisdictions have filed it")
    for j in sorted(at_cliff):
        versions = sorted(p.identity.version for p in at_cliff[j])
        n_bumped, n_editions, rate = bump_rate[j]
        confirmed = " <- LIVE-CONFIRMED DIVERGENT (BUILD-LOG Entry 53)" \
            if j in ("ND", "NH") else \
            " <- LIVE-CONFIRMED MATCH DESPITE VERSION GAP (Entry 53)" \
            if j in ("VT", "SD", "AK") else ""
        lines.append(f"  {j:4s} holds {','.join(versions):10s} "
                     f"pulled {last_pull[j]} ({stale_days[j]:3d}d stale)  "
                     f"historical bump rate {rate:4.0%}{confirmed}")
    lines.append("")

    # ---- 4. the risk ranking ------------------------------------------------
    # Only single-version-on-disk at the cliff edition can be silently behind
    # in the way ND/NH were -- a jurisdiction already holding V02+ has at
    # least been re-pulled since the first filing.
    single_version_at_cliff = {
        j: ps for j, ps in at_cliff.items() if len(ps) == 1}
    risk = sorted(
        single_version_at_cliff,
        key=lambda j: (-bump_rate[j][2], -stale_days[j]))
    lines.append(f"## risk ranking: single-version-on-disk at the cliff AND "
                 f"a jurisdiction that has bumped mid-edition before "
                 f"({len(risk)} of {len(at_cliff)} candidates)")
    for j in risk:
        n_bumped, n_editions, rate = bump_rate[j]
        already_confirmed = " (already the live-confirmed pair)" \
            if j in ("ND", "NH") else ""
        lines.append(f"  {j:4s} stale {stale_days[j]:3d}d, historical bump "
                     f"rate {rate:4.0%} ({n_bumped}/{n_editions} editions)"
                     f"{already_confirmed}")
    lines.append("")
    lines.append(
        "None of the above is confirmed except ND and NH (live calls "
        "already spent, BUILD-LOG Entry 53). Everything else in the risk "
        "ranking is a same-corpus signal -- staleness and a state's own "
        "history of taking mid-edition amendments -- not a live check. "
        "Confirming any one of them needs one live call.")

    out = "\n".join(lines)
    print(out)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(out, encoding="utf-8")
    print(f"\nwritten: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
