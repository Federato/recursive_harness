#!/usr/bin/env python3
"""Chunk 28 C28-19, confirmed: a date ISO is known to rate on a package the corpus lacks refuses; nothing else does.

No ISO calls. Two parts:
  1. The check, every state at every date the live comparison asked (`iso_packages.json`) plus today: the book's own
     answer (`older_than_iso`) against `242_`'s recorded verdict -- refuse exactly where ISO named a package newer than
     ours, rate everywhere else. Since C28-20 imported all 34 packages (2026-10-06) nothing refuses there, so the
     three kinds named in CF-CHUNK28-PROPOSAL-F.md are pinned on packages ISO is *made* to name and the corpus does not
     hold (`ISO_EXTRA`, added to the check's table for this script only): an edition the corpus lacks (OR 20271001),
     an edition between two it holds (CT 20270201), a later version (CT 20270301 V03).
  2. A real rating: a stored Illinois fixture at 2027-01-01 rates (the package is in); with ISO made to name
     CF_IL_20270701_V01, the same at 2027-07-01 refuses with outcome "older package" naming it.

    python scripts/cf/257_chunk28_c28-19_older_package.py

Exits 1 on any disagreement.
"""
from __future__ import annotations

import json
import re
import sys
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))
sys.stdout.reconfigure(encoding="utf-8")

from cf_engine.config import CORPUS_ROOT
from cf_engine.resolve import book_for
from cf_engine.resolve import book as book_mod
from cf_engine.run_checks import OlderPackage
from gl_engine.interp.interpreter import Interpreter

EDITIONS = ROOT / "results" / "cf-raas" / "chunk27_c27-13_editions.json"
FAIL = []
#: hypothetical packages ISO is made to name, none in the corpus: one per kind of known-older package
ISO_EXTRA = {"OR": ["CF_OR_20271001_V01"], "CT": ["CF_CT_20270201_V01", "CF_CT_20270301_V03"], "IL": ["CF_IL_20270701_V01"]}


def with_extra():
    real = book_mod._iso_packages()
    book_mod._ISO_PACKAGES = {st: list(v) + [(p, *p.split("_")[2:4]) for p in ISO_EXTRA.get(st, [])]
                              for st, v in real.items()}
    return real


def check(label, got, want):
    ok = got == want
    print(f"  {'OK ' if ok else 'BAD'} {label}: {got}" + ("" if ok else f"  (expected {want})"))
    if not ok:
        FAIL.append(label)


def part1():
    d = json.loads(EDITIONS.read_text(encoding="utf-8"))
    n = refused = 0
    for st, by_date in sorted(d.items()):
        for date, row in sorted(by_date.items()):
            got = book_for(st, date.replace("-", "")).older_than_iso()
            # recorded verdict, re-read against today's corpus: ISO's named package sorts above our resolved one
            iso = row["iso"].replace(" ", "_")
            mine = re.search(r"CF_[A-Z]{2}_\d{8}_V\d\d", str(book_for(st, date.replace("-", "")))).group(0)
            want = (mine, iso) if tuple(iso.split("_")[2:4]) > tuple(mine.split("_")[2:4]) else None
            n += 1
            refused += bool(got)
            if got != want:
                check(f"{st} {date}", got, want)
    print(f"  every state at every date asked: {n} checked, {refused} refuse, {n - refused} rate; "
          f"{'all as recorded' if not FAIL else 'DISAGREEMENTS above'}")
    check("states refused at any date asked (all 34 packages imported)", refused, 0)
    real = with_extra()
    try:
        check("OR 2027-10-01 (edition the corpus lacks)", book_for("OR", "20271001").older_than_iso(),
              ("CF_OR_20270101_V01", "CF_OR_20271001_V01"))
        check("CT 2027-02-01 (edition between two held)", book_for("CT", "20270201").older_than_iso(),
              ("CF_CT_20270101_V01", "CF_CT_20270201_V01"))
        check("CT 2027-04-01 (later version)", book_for("CT", "20270401").older_than_iso(),
              ("CF_CT_20270301_V02", "CF_CT_20270301_V03"))
        check("OR 2027-09-30 (the day before)", book_for("OR", "20270930").older_than_iso(), None)
    finally:
        book_mod._ISO_PACKAGES = real
    check("IL 2026-10-06 (today; October package imported)", book_for("IL", "20261006").older_than_iso(), None)
    check("CA 2027-10-01 (ISO named ours throughout)", book_for("CA", "20271001").older_than_iso(), None)
    check("OR 2026-09-17 (every comparison date)", book_for("OR", "20260917").older_than_iso(), None)
    today = [st for st in d if book_for(st, "20261006").older_than_iso()]
    check("states refused today (2026-10-06)", today, [])


def part2():
    cmp = import_module("154_chunk13_rc5_fields_messages")
    fx = next(CORPUS_ROOT.rglob("STC/STC_CP000013983.json"))
    d = json.loads(fx.read_text(encoding="utf-8-sig"))

    def rate(date, product=None):
        req = {"header": {}, "body": {"SchemeKeys": {"ProductName": product or d["SchemeKeys"]["ProductName"],
                                                     "EffectiveDateTime": f"{date}T00:00:00"},
                                      "CommercialProperty": d["CommercialProperty"]}}
        seen = {}
        orig = Interpreter.run

        def run(self, data):
            seen.setdefault("ip", self)       # the first is the main rating; OI-125's look-ahead runs inside it
            return orig(self, data)
        Interpreter.run = run
        try:
            data, _ = cmp.rate(req)
            return seen["ip"].outcome, None
        except OlderPackage as exc:
            return seen["ip"].outcome, str(exc)
        finally:
            Interpreter.run = orig

    out, err = rate("2027-01-01")
    check("IL fixture 2027-01-01 rates (CF_IL_20270101_V02 imported)", out["status"], "rated")
    real = with_extra()
    try:
        out, err = rate("2027-07-01")
    finally:
        book_mod._ISO_PACKAGES = real
    check("IL fixture 2027-07-01, ISO made to name CF_IL_20270701_V01: refuses",
          (out["status"], out["reasons"][0]["kind"] if out["reasons"] else None), ("refused", "older package"))
    check("  and names ISO's package", "CF_IL_20270701_V01" in (err or ""), True)
    print(f"      {err[:200] if err else ''}")


def main() -> int:
    print("1. The check against every recorded comparison")
    part1()
    print("2. A real rating")
    part2()
    print(f"\nC28-19: {'ALL AS EXPECTED' if not FAIL else 'FAILED: ' + ', '.join(FAIL)}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
