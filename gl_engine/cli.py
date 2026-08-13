"""Command line for stage 1. Look at what resolves, and prove it.

    python -m gl_engine.cli resolve NJ 20260811
    python -m gl_engine.cli parents 20260811
    python -m gl_engine.cli parents 20270401
    python -m gl_engine.cli table NJ 20260811 PremOpsLossCost --rows 5
    python -m gl_engine.cli check 20260811 --deep
    python -m gl_engine.cli census 20260811

The as-of date is REQUIRED everywhere. There is no default and "today" is not
one -- this corpus holds filings that have not taken effect, so a defaulted date
would answer a question nobody asked (N4).
"""
from __future__ import annotations

import argparse
import sys
import time
from collections import Counter

from .assertions import run_all
from .config import CORPUS_ROOT
from .errors import EngineError
from .resolve import EditionResolver, ResolvedBook


def _resolver(args):
    t0 = time.time()
    r = EditionResolver()
    if not args.quiet:
        print(f"corpus {CORPUS_ROOT}\n{len(r.packages)} packages, "
              f"{len(r.jurisdictions)} jurisdictions + countrywide  "
              f"({time.time() - t0:.1f}s)\n")
    return r


# ------------------------------------------------------------------ commands

def cmd_resolve(args):
    r = _resolver(args)
    for juris in args.juris:
        res = r.resolve(juris, args.asof)
        book = ResolvedBook(res)
        print(f"{juris}  as of {args.asof}")
        print(f"  state       {res.state.pkg_id}   "
              f"(effective {res.state.identity.edition})")
        print(f"  countrywide {res.parent.pkg_id if res.parent else '-'}   "
              f"declared by the state, not chosen by us (N5)")
        inv = book.inventory()
        for kind, v in inv.items():
            print(f"  {kind:<7} tables  visible {v['visible']:>4}  "
                  f"= state-only {v['state_only']:>3} + overridden "
                  f"{v['overridden']:>3} + inherited {v['inherited']:>4}")
        print()


def cmd_parents(args):
    r = _resolver(args)
    parents = r.declared_parents(args.asof)
    print(f"countrywide parents in force at {args.asof}: {len(parents)}")
    for pid, js in parents.items():
        print(f"  {pid:<24} {len(js):>2} jurisdictions   {', '.join(js)}")
    cw = [p for p in r.by_juris.get("CW", []) if p.identity.edition <= args.asof]
    if cw:
        print(f"\nnewest countrywide edition in force: {cw[-1].pkg_id}")
        older = {p: js for p, js in parents.items() if p != cw[-1].pkg_id}
        n = sum(len(v) for v in older.values())
        print(f"jurisdictions declaring something OLDER than that: {n}"
              f"{'  <- these are the ones N5 exists for' if n else ''}")


def cmd_table(args):
    r = _resolver(args)
    book = ResolvedBook(r.resolve(args.juris, args.asof))
    t = book.table(args.name, args.kind)
    print(f"{args.name}  [{args.kind}]")
    print(f"  resolved to   {t.package}   (layer: {book.declares(args.name, args.kind)})")
    print(f"  shape         {t.shape.value}")
    print(f"  population    {t.population.value}   {len(t.rows)} rows")
    if t.split_siblings:
        print(f"  siblings      {len(t.split_siblings)} suffixed tables carry the rows (OI-20)")
        for s in t.split_siblings[:5]:
            print(f"                {s}  {len(book.state.table(args.kind, s))} rows")
    d = t.definition
    print(f"  key cols      {[c.name for c in d.key_cols]}")
    for rg in d.key_ranges:
        print(f"  key range     {rg.name} [{rg.range_type}] "
              f"{rg.lo_col} .. {rg.hi_col}")
    print(f"  value cols    {[c.name for c in d.value_cols]}")
    for rg in d.value_ranges:
        print(f"  value range   {rg.name} interpolate={rg.interpolate} "
              f"along {rg.range_key_col}")
    if args.rows:
        print(f"  header        {list(t.header)}")
        for row in t.rows[:args.rows]:
            print(f"    {row}")


def cmd_check(args):
    r = _resolver(args)
    t0 = time.time()
    rep = run_all(r, args.asof, deep=args.deep)
    for c in rep.checks:
        print(c)
    n = len(rep.checks)
    print(f"\n{n - len(rep.failures)}/{n} load-time assertions passed "
          f"({time.time() - t0:.1f}s)")
    return 0 if rep.ok else 1


def cmd_census(args):
    """What the corpus actually contains, counted rather than assumed."""
    r = _resolver(args)
    shapes, pops, kinds = Counter(), Counter(), Counter()
    empty_rating = Counter()
    t0 = time.time()
    seen_pkgs = set()
    for juris in r.jurisdictions:
        book = ResolvedBook(r.resolve(juris, args.asof))
        for layer in (book.state, book.parent):
            if layer is None or layer.pkg_id in seen_pkgs:
                continue
            seen_pkgs.add(layer.pkg_id)
            for kind in ("Rate", "Domain"):
                for name in layer.names(kind):
                    t = layer.table(kind, name)
                    shapes[t.shape.value] += 1
                    pops[t.population.value] += 1
                    kinds[kind] += 1
                    if t.is_empty:
                        empty_rating[name] += 1
    total = sum(kinds.values())
    print(f"table instances across {len(seen_pkgs)} resolved packages: {total}")
    print(f"  by kind      {dict(kinds)}")
    print(f"  by shape     {dict(shapes.most_common())}")
    print(f"  by population{dict(pops.most_common())}")
    print(f"\nthe most-often-empty table names (N7: empty is a statement):")
    for name, n in empty_rating.most_common(10):
        print(f"  {n:>4}  {name}")
    print(f"\n({time.time() - t0:.1f}s)")


# ---------------------------------------------------------------------- main

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="gl_engine", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-q", "--quiet", action="store_true")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("resolve", help="what applies to a state on a date")
    p.add_argument("juris", nargs="+")
    p.add_argument("asof")
    p.set_defaults(fn=cmd_resolve)

    p = sub.add_parser("parents", help="which countrywide editions are live")
    p.add_argument("asof")
    p.set_defaults(fn=cmd_parents)

    p = sub.add_parser("table", help="load one table and describe it")
    p.add_argument("juris")
    p.add_argument("asof")
    p.add_argument("name")
    p.add_argument("--kind", default="Rate", choices=["Rate", "Domain"])
    p.add_argument("--rows", type=int, default=0)
    p.set_defaults(fn=cmd_table)

    p = sub.add_parser("check", help="run the load-time assertions")
    p.add_argument("asof")
    p.add_argument("--deep", action="store_true",
                   help="also open every table CSV in all 51 jurisdictions")
    p.set_defaults(fn=cmd_check)

    p = sub.add_parser("census", help="count what the corpus contains")
    p.add_argument("asof")
    p.set_defaults(fn=cmd_census)

    args = ap.parse_args(argv)
    try:
        return args.fn(args) or 0
    except EngineError as e:
        print(f"\nERROR  {type(e).__name__}: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
