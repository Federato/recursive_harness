#!/usr/bin/env python3
"""Chunk 6, task C6-04 -- every jurisdiction, Special Class Basic Group I.

Same discipline as chunks 1-5: each jurisdiction's premium is predicted from
**its own filed rows** before the engine runs, and every divergence is
classified rather than tolerated.

The case is the chunk 6 golden case -- a broadcasting tower, limit 100,000,
coinsurance 90%, deductible 1,000, protection class 3 -- which rates at **$66**
in Oregon.

Chunk 6's sweep has a target chunks 1-5 did not: **the key itself is filed per
state.** Group I's base rate is reached through `ClassDescription` ->
`SpecialClassDescriptionConvertedOption` -> `OptionNN`, and three jurisdictions
declare that converter table themselves:

  * **FL** resolves over `CF_CW_20230801_V01` -- **two countrywide editions
    behind everyone else** -- so its class vocabulary is frozen at 2023, and
    the golden case's own description is one of **six countrywide classes
    Florida drops**. (C6-11. An earlier version of this docstring called
    Florida a private option namespace; it is not, and the private namespace
    turned out to be New York's -- see OI-100.)
  * **NY** files the converter table **header-only** and empties the rule that
    reads it, while still filing 189 Group I rate rows. (C6-12)
  * **PR** files a full 213-row rate table but no converter of its own.

So the sweep does not ask "does this state file a rate" -- it asks **can this
state reach a rate at all**, which is a question no previous chunk had.

    python scripts/cf/43_chunk6_enumerate_states.py [--verbose]

Exit 0 when every jurisdiction matches its own prediction.
"""
from __future__ import annotations

import argparse
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from importlib import import_module

from cf_engine.config import NULL_ARITHMETIC, ROUNDING
from cf_engine.resolve import CFEditionResolver, book_for
from gl_engine.interp.interpreter import Interpreter
from gl_engine.interp.tree import Node, read

g = import_module("41_chunk6_golden_case")

SC, DESC = g.SC, g.DESC
PREM = g._P % "BasicGroupI"
LIMIT, COINS, DED, BAND = 100000, "90%", "1,000", 100000


#: Why each jurisdiction cannot reach a Group I rate. Chunk 7 reads this
#: rather than restating it, so the two sweeps cannot drift apart.
DIVERGENT_NOTE = {
    "FL": "the class description is not in Florida's own converter",
    "NY": "the converter is header-only and the rule that reads it is deleted",
    "AZ": "the rate step is rewritten around a LOCATION field defaulting to 0.0",
}


def r3(x):
    return Decimal(x).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)


def pick(rows, juris, *keys):
    """The row whose leading key is this state's (or CW's) and whose remaining
    columns match. State rows win: a state that declares a table owns it."""
    for want_state in (juris, "CW"):
        for r in rows:
            if r[0] != want_state:
                continue
            if all(str(r[i + 1]) == str(k) for i, k in enumerate(keys)):
                return r
    return None


def predict(book, juris, prot_band):
    """Basic Group I, hand-derived from this jurisdiction's own rows.

    Returns (premium, note). `None` premium means "this state cannot reach a
    rate for this class", with the reason named.
    """
    conv = book.table("SpecialClassDescriptionConvertedOption")
    row = pick(conv.rows, juris, DESC)
    if row is None:
        if book.declares("SpecialClassDescriptionConvertedOption") == "state":
            n = len(conv.rows)
            return 0, (f"declares its own converter ({n} rows) and this "
                       f"description is not in it")
        return 0, "no converter row for this description"
    option = row[2]

    rt = book.table("BasicGroupIRateSpecialClass")
    rr = pick(rt.rows, juris, option, prot_band)
    if rr is None:
        return 0, f"converter gives {option}, and no rate row keys on it"
    base = Decimal(rr[3])

    cf = pick(book.table("CoinsuranceFactor").rows, juris, COINS)
    coins = Decimal(cf[2]) if cf else Decimal(1)

    ded = Decimal(0)
    for r in book.table("DeductibleFactor").rows:
        if (r[0] in (juris, "CW") and str(r[1]) == DED
                and r[4] == "Basic Group I"
                and int(r[2]) < BAND <= int(r[3])):
            ded = Decimal(r[5])
            if r[0] == juris:
                break

    if juris == "AZ":
        # **Arizona rewrites the rate step to multiply by a LOCATION field**,
        # `BasicGroupIReductionCredit`, read through `FromConstant="0.0"`.
        # Absent therefore means ZERO, not "no reduction" -- the whole Group I
        # rate collapses. Chunk 5 met this same AZ credit through the Building
        # dependency, where it cost a dollar; here its absence costs the
        # entire premium.
        return 0, ("rewrites the rate step to x ../../BasicGroupIReductionCredit, "
                   "a LOCATION field defaulting to 0.0")

    rate = r3(base * 1)
    adj = r3(rate * coins)
    final = r3(adj * 1 * ded)
    prem = (final * LIMIT / 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(prem), (f"{option} base {base} x coins {coins} -> {adj} "
                       f"x ded {ded} -> {final}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args()

    res = CFEditionResolver()
    juris = sorted(res.jurisdictions)
    print(f"Special Class Basic Group I, {len(juris)} jurisdictions, "
          f"as of {g.ASOF}\n")

    ok = True
    hits = misses = zeros = 0
    zero_states = []
    for j in juris:
        book = book_for(j, g.ASOF, resolver=res)
        ip = Interpreter(book, rounding=ROUNDING, trace=False,
                         null_arithmetic=NULL_ARITHMETIC)
        data = Node.from_dict(f"MasterCF{j}", g.submission("Basic"))
        try:
            ip.run(data)
        except Exception as exc:
            print(f"  {j}  RAISED {type(exc).__name__}: {exc}")
            ok = False
            misses += 1
            continue
        got = read(PREM, data)
        band = read(f"{SC}/ProtectionClassToUse", data)
        want, note = predict(book, j, band)
        good = str(got) == str(want)
        ok &= good
        if good:
            hits += 1
        else:
            misses += 1
        if str(want) == "0":
            zeros += 1
            zero_states.append(j)
        flag = "OK " if good else "MISMATCH"
        line = f"  {j}  predicted {str(want):>5s}  engine {str(got):>5s}  {flag}"
        if a.verbose or not good or str(want) == "0":
            line += f"   {note}"
        print(line)

    print(f"\n{hits} of {len(juris)} match their own prediction; "
          f"{misses} do not.")
    print(f"{zeros} jurisdiction(s) cannot reach a rate for this class: "
          f"{', '.join(zero_states) if zero_states else 'none'}")
    if zero_states:
        print("\n  **A class that rates countrywide is unrateable in these "
              "states**, and in")
        print("  no case is the reason a missing RATE. FL and NY cannot reach "
              "the key --")
        print("  the description is absent from FL's own converter and NY's is "
              "header-only")
        print("  -- and AZ rewrites the rate step around a location field that "
              "defaults to")
        print("  zero. **No message is raised by any of the three.** The "
              "premium is simply 0.")

    # ---- Arizona, proven by supplying the field rather than asserted
    print("\n=== AZ  the reduction credit, moved")
    az = book_for("AZ", g.ASOF, resolver=res)
    for credit, want in ((None, "0"), ("1.0", "66"), ("0.9", "59")):
        sub = g.submission("Basic")
        if credit is not None:
            g.location(sub)["BasicGroupIReductionCredit"] = credit
        ip = Interpreter(az, rounding=ROUNDING, trace=False,
                         null_arithmetic=NULL_ARITHMETIC)
        data = Node.from_dict("MasterCFAZ", sub)
        ip.run(data)
        got = str(read(PREM, data))
        good = got == want
        ok &= good
        label = "absent" if credit is None else credit
        print(f"    BasicGroupIReductionCredit = {label:>6s}   premium {got:>3s}"
              f"   (expected {want:>3s}) {'OK' if good else 'MISMATCH'}")
    print("    **Absent is 0.0, not 1.0.** The field lives on the LOCATION, not")
    print("    on the Special Class item, and nothing in the item's payload")
    print("    hints that it is required. Chunk 5 met the same Arizona credit")
    print("    through the Building dependency, where it cost a dollar; here")
    print("    its absence costs the entire Group I premium.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
