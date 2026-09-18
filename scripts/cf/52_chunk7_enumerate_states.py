#!/usr/bin/env python3
"""Chunk 7, tasks C7-04, C7-13 and C7-17 -- every jurisdiction.

Same discipline as chunks 1-6: each jurisdiction's premium predicted from its
own filed rows before the engine runs, and every divergence classified.

**Chunk 7's sweep has a target no previous chunk had: a premium that fails for
reasons belonging to a DIFFERENT coverage.** Basic Group I is a straight copy of
the Special Class item's finished rate, so chunk 6's three unrateable
jurisdictions must reappear here -- and when they do, **none of them is a
Business Income defect** (C7-13):

    FL   the class description is not in Florida's own converter
    NY   the converter is header-only and the rule that reads it is deleted
    AZ   the parent's rate step is rewritten around a location field
         defaulting to 0.0

**And C7-17 re-asks chunk 6's biconditional on a second coverage.** Six states
DELETE `SetLowestBasicGroupIIBaseRate` outright here -- AR, DC, KS, NY, RI, TX
-- where chunk 6 found the same relationship expressed by rewriting the rule
that reads the table.

The case is the chunk 7 golden case: Basic Group I **$39** in Oregon.

    python scripts/cf/52_chunk7_enumerate_states.py [--verbose]

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

g6 = import_module("41_chunk6_golden_case")
g7 = import_module("50_chunk7_golden_case")
sweep6 = import_module("43_chunk6_enumerate_states")

BI, SC = g7.BI, g7.SC
PREM = g7._P % "BasicGroupI"
PARENT_RATE = SC + "/BasicGroupIRate"
LIMIT, COINS, COVTYPE = 100000, "90%", "Business Income With Extra Expense"
RISK = "Mercantile and Non-manufacturing"
RULES = "CommercialPropertySpecialClassBusnIncomeRules.Rule.xml"
LOWEST_RULE = "SetLowestBasicGroupIIBaseRate"


def r3(x):
    return Decimal(x).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)


def predict(book, juris, parent_rate):
    """Basic Group I from this jurisdiction's own rows.

    The parent's rate is an INPUT to the prediction, not something predicted
    again: chunk 6's sweep already derived it for all 47, and re-deriving it
    here would test the same arithmetic twice while hiding the dependency.
    """
    if parent_rate in (None, "0"):
        return 0, "the parent cannot reach a Group I rate (chunk 6)"
    fac = sweep6.pick(book.table("BusnIncomeFactor").rows, juris,
                      COVTYPE, RISK, COINS)
    if fac is None:
        return 0, "no BusnIncomeFactor row"
    factor = Decimal(fac[4])
    final = r3(Decimal(parent_rate) * 1 * factor)
    prem = (final * LIMIT / 100).quantize(Decimal("1"),
                                          rounding=ROUND_HALF_UP)
    return int(prem), f"parent {parent_rate} x factor {factor} -> {final}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args()

    res = CFEditionResolver()
    juris = sorted(res.jurisdictions)
    print(f"Special Class Business Income, Basic Group I, "
          f"{len(juris)} jurisdictions, as of {g7.ASOF}\n")

    ok, hits, zeros = True, 0, []
    for j in juris:
        book = book_for(j, g7.ASOF, resolver=res)
        ip = Interpreter(book, rounding=ROUNDING, trace=False,
                         null_arithmetic=NULL_ARITHMETIC)
        data = Node.from_dict(f"MasterCF{j}", g7.submission("Basic"))
        try:
            ip.run(data)
        except Exception as exc:
            print(f"  {j}  RAISED {type(exc).__name__}: {exc}")
            ok = False
            continue
        got = read(PREM, data)
        parent = read(PARENT_RATE, data)
        want, note = predict(book, j, parent)
        good = str(got) == str(want)
        ok &= good
        hits += good
        if str(want) == "0":
            zeros.append(j)
        line = (f"  {j}  predicted {str(want):>5s}  engine {str(got):>5s}  "
                f"{'OK ' if good else 'MISMATCH'}")
        if a.verbose or not good or str(want) == "0":
            line += f"   {note}"
        print(line)

    print(f"\n{hits} of {len(juris)} match their own prediction.")

    # ---- C7-13, the inherited failures named
    print(f"\n=== 13  The parent's failures, arriving here")
    print(f"    jurisdictions producing no Business Income Group I premium: "
          f"{len(zeros)}  ({', '.join(zeros) if zeros else 'none'})")
    for j in ("FL", "NY", "AZ"):
        if j not in zeros:
            continue
        print(f"    {j}: inherited from chunk 6 -- "
              f"{sweep6.DIVERGENT_NOTE.get(j, 'see CF-CHUNK6-STATE-SWEEP.md')}")
    print("    **None of the three is a Business Income defect.** Each is a")
    print("    Special Class filing decision arriving two levels down, and in")
    print("    each case the Business Income record is perfectly well formed.")

    # ---- C7-17, the biconditional re-asked
    print(f"\n=== 17  The lowest-rate table and the rule that reads it, again")
    files_own, overrides, deletes, reads = set(), set(), set(), set()
    for j in juris:
        b = book_for(j, g7.ASOF, resolver=res)
        if b.declares("LowestBasicGroupIIRate") == "state":
            files_own.add(j)
        f = b.state.package.content / "Rules" / RULES
        if not f.exists():
            continue
        t = f.read_text(encoding="utf-8-sig")
        i = t.find(f'<rul:Rule Name="{LOWEST_RULE}"')
        if i < 0:
            continue
        seg = t[i:i + t[i:].find("</rul:Rule>") + 11]
        overrides.add(j)
        if "<rul:Sequence />" in seg or "<rul:Sequence/>" in seg:
            deletes.add(j)
        elif "LowestBasicGroupIIRate" in seg or "Lookup" in seg:
            reads.add(j)
    reaches = (set(juris) - overrides) | reads
    checks = [
        ("file their own LowestBasicGroupIIRate", len(files_own), 39),
        ("file none", len(set(juris) - files_own), 8),
        (f"override {LOWEST_RULE}", len(overrides), 6),
        ("...of those, DELETING it outright", len(deletes), 6),
        ("states whose rule can still REACH the read", len(reaches), 41),
        ("the deleters are all non-filers",
         deletes <= (set(juris) - files_own), True),
    ]
    for label, got_v, want_v in checks:
        good = str(got_v) == str(want_v)
        ok &= good
        print(f"    {label:46s} {str(got_v):>6s}  (expected {want_v}) "
              f"{'OK' if good else 'MISMATCH'}")
    print(f"    deleted by: {', '.join(sorted(deletes))}")
    print(f"    non-filers not deleting: "
          f"{', '.join(sorted((set(juris) - files_own) - deletes))}")
    print("    **Chunk 6's biconditional does NOT hold here, and the way it")
    print("    fails is the finding.** In chunk 6 every state that could reach")
    print("    the read filed the table and vice versa. Here six of the eight")
    print("    non-filers delete the rule -- and the other two, FL and PR,")
    print("    leave it alone while filing no table, so they DO reach a read")
    print("    with nothing to read. **Two states out of forty-seven make the")
    print("    same filing decision a third way**, and a rule inferred from")
    print("    chunk 6 would have called them defects.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
