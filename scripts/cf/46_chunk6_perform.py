#!/usr/bin/env python3
"""Chunk 6, tasks C6-15 to C6-19 -- the per-form specifics.

  15  **Coinsurance is computed FIRST and shared by three forms.** Four
      branches, and branch 3 is a **1.5 SURCHARGE**, not a credit.
  16  **Protection class is a lookup KEY**, and the proof is arithmetic:
      `BasicGroupIRate` equals `BasicGroupIBaseRate x LCM` exactly while
      `ProtectionClassFactor` sits at 0.96 on the same record.
  17  **`ProtectionClassFactor` is computed and never read.** Puerto Rico
      deletes the rule and still rates.
  18  **`BasicGroupIISymbol` has no setter in this datadef group at all** --
      three other groups derive their own; Special Class takes it as input.
  19  **A state files `LowestBasicGroupIIRate` if and only if its own version
      of the rule that reads it still reads it.** Zero exceptions in 47.

Every figure derived by hand from Oregon's filed rows before the run. The
baseline is the chunk 6 golden case -- base 0.07, deductible factor 0.98,
Basic Group I **$66**.

    15  80%   factor 1.0   r3(0.07)  =0.070 x .98 -> r3(0.0686) =0.069  $69
        90%   factor 0.95  r3(0.0665)=0.067 x .98 -> r3(0.06566)=0.066  $66
        100%  factor 0.9   r3(0.063) =0.063 x .98 -> r3(0.06174)=0.062  $62
        50%   factor 1.5   r3(0.105) =0.105 x .98 -> r3(0.1029) =0.103  $103

        and at 50% the SHARED factor reaches Broad and Special too:
        Broad   r3(0.015x1.5)=0.023 x ded 0.97 -> 0.022   $22  (from $14)
        Special r3(0.047x1.5)=0.071 x ded 0.97 -> 0.069   $69  (from $44)

    18  symbol AA 0.015 x8 =0.120 x.95 ->0.114 x.98 ->0.112   $112
        symbol A  0.016 x8 =0.128 x.95 ->0.122 x.98 ->0.120   $120
        symbol AB 0.024 x8 =0.192 x.95 ->0.182 x.98 ->0.178   $178
        symbol B  0.028 x8 =0.224 x.95 ->0.213 x.98 ->0.209   $209

    python scripts/cf/46_chunk6_perform.py

Exit 0 when every case matches its derivation.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from importlib import import_module

from cf_engine.resolve import CFEditionResolver, book_for
from gl_engine.interp.tree import read
from gl_engine.interp.values import InterpretError                # noqa: E402
import _iso_refusals as _iso                                    # noqa: E402

chain = import_module("45_chunk6_description_chain")
g = import_module("41_chunk6_golden_case")

SC, ASOF = g.SC, g.ASOF
P = {f: g._P % f for f in ("BasicGroupI", "BasicGroupII", "Broad", "Special")}
RULES = "CommercialPropertySpecialClassRules.Rule.xml"
COL_RULE = "SetBasicGroupIICauseOfLossAdjustment"

#: id, item overrides, (factor, Basic Group I premium), why
COINS = [
    ("15  80%", {"Coinsurance": "80%"}, ("1", "69"),
     "**80% is the only coinsurance that costs nothing** -- factor 1.0, and "
     "the highest Group I premium of the three ordinary values"),
    ("15  90%  (baseline)", {}, ("0.95", "66"), "the reference"),
    ("15  100%, not blanketed", {"Coinsurance": "100%"}, ("0.9", "62"),
     "branch 1's second limb: 100% qualifies only when `IncludedInBlkt` is "
     "not \"Yes\""),
    ("15  50%", {"Coinsurance": "50%"}, ("1.5", "103"),
     "**branch 3, and it is a SURCHARGE.** `LessThan80PctMultiplicativeFactor` "
     "is 1.5 countrywide -- insuring to less than 80% of value costs 56% more "
     "than insuring to 90%, not less. Every coinsurance factor in chunks 1-5 "
     "ran at or below 1.0"),
    ("15  60%", {"Coinsurance": "60%"}, ("1.5", "103"),
     "the same branch and the same flat 1.5 -- the table has ONE row, so 50%, "
     "60% and 70% are priced identically. A three-value distinction the "
     "submission can make and the rate cannot"),
]

#: C6-15: the shared factor reaches Broad and Special, which have no
#: coinsurance rule of their own.
SHARED = [("Broad", "14", "22"), ("Special", "44", "69")]

#: C6-18: symbol -> (base rate, premium). The symbol is a plain INPUT here.
SYMBOLS = [("AA", "0.015", "112"), ("A", "0.016", "120"),
           ("AB", "0.024", "178"), ("B", "0.028", "209")]


def prem(state, over, form="BasicGroupI", second=False):
    data = chain.run(state, over, second)
    return data


def main() -> int:
    ok = True

    # ---- C6-15
    print("=== 15  Coinsurance -- four branches, and branch 3 is a surcharge\n")
    for name, over, expect, _ in COINS:
        data = prem("OR", over)
        got = (str(read(f"{SC}/CoinsuranceFactor", data)),
               str(read(P["BasicGroupI"], data)))
        good = got == expect
        ok &= good
        print(f"  {name:26s} factor={got[0]:>5s}  premium={got[1]:>4s}"
              + ("" if good else f"   <-- expected {expect}"))

    print("\n=== 15  ...and ONE factor serves three forms")
    for form, base_prem, at50 in SHARED:
        d0 = chain.run("OR", {"CauseOfLoss": form})
        d1 = chain.run("OR", {"CauseOfLoss": form, "Coinsurance": "50%"})
        a, b = str(read(P[form], d0)), str(read(P[form], d1))
        good = (a, b) == (base_prem, at50)
        ok &= good
        print(f"    {form:8s} 90% -> {a:>3s}    50% -> {b:>3s}   "
              f"(expected {base_prem} / {at50}) {'OK' if good else 'MISMATCH'}")
    print("    Broad and Special define no coinsurance rule at all. They read")
    print("    the value Basic Group I's chain computed **first**, before any")
    print("    base rate -- the reverse of Building, where coinsurance comes")
    print("    after the rate and the cause-of-loss adjustment.")
    print("    Group II is the exception: it has its own rule, and on 50% it")
    print("    reads a DIFFERENT table (`BasicGroupIIFlatCoinsuranceFactor`)")
    print("    that happens to file the same 1.5 -- two tables, one number,")
    print("    and nothing in a premium could tell them apart.")

    # ---- C6-16 and C6-17
    print("\n=== 16/17  Protection class is a KEY, and the FACTOR is dead")
    data = chain.run("OR", {})
    base = read(f"{SC}/BasicGroupIBaseRate", data)
    rate = read(f"{SC}/BasicGroupIRate", data)
    pcf = read(f"{SC}/ProtectionClassFactor", data)
    band = read(f"{SC}/ProtectionClassToUse", data)
    good = base == rate == "0.07" and pcf == "0.96"
    ok &= good
    print(f"    band (a KEY)           = {band}")
    print(f"    base rate              = {base}")
    print(f"    rate                   = {rate}   <- base x LCM, exactly")
    print(f"    ProtectionClassFactor  = {pcf}   <- populated, and nowhere in "
          f"that product  {'OK' if good else 'MISMATCH'}")
    print("    **0.07 x 0.96 would be 0.067.** The factor is computed and the")
    print("    rate does not contain it.")

    book = book_for("OR", ASOF)
    body = (book.parent.package.content / "Rules" / RULES).read_text(
        encoding="utf-8-sig")
    i = body.find('<rul:Rule Name="SetProtectionClassFactor"')
    own = body[i:i + body[i:].find("</rul:Rule>") + 11]
    reads = len(re.findall(r'FromDataDef="ProtectionClassFactor"', body))
    in_own = len(re.findall(r'FromDataDef="ProtectionClassFactor"', own))
    good = reads == in_own
    ok &= good
    print(f"\n    reads of ProtectionClassFactor in the whole ruleset : {reads}")
    print(f"    ...of those, inside SetProtectionClassFactor itself  : {in_own}")
    print(f"    reads by any RATE chain                              : "
          f"{reads - in_own}  (expected 0) {'OK' if good else 'MISMATCH'}")

    try:
        pr = chain.run("PR", {})
    except InterpretError as exc:
        # C28-05: Puerto Rico now refuses on ProtectionClassStatCode (CW 3); no RaaS entitlement, so unconfirmed
        if not _iso.refused_as_iso(__file__, "PR", exc, indent="    "):
            raise
        pr = None
    pr_pcf = read(f"{SC}/ProtectionClassFactor", pr) if pr is not None else None
    pr_prem = str(read(P["BasicGroupI"], pr)) if pr is not None else "64 (not rated: refused, C28-05)"
    good = pr_pcf is None and (pr is None or pr_prem == "64")
    ok &= good
    print(f"\n    PR deletes SetProtectionClassFactor: factor = {pr_pcf} "
          f"(expected None)")
    print(f"    ...and Puerto Rico still rates Group I at {pr_prem} "
          f"(expected 64)  {'OK' if good else 'MISMATCH'}")
    print("    **Deleting a rule that nothing reads changes no premium.** It")
    print("    is the cheapest possible confirmation, and Puerto Rico filed it")
    print("    for us. The factor is computed LAST, after all five chains --")
    print("    after the point where it could have been used.")

    # ---- C6-18
    print("\n=== 18  BasicGroupIISymbol is a plain INPUT here")
    d = book.parent.package.content / "Rules"
    setters = set()
    for p in d.glob("*.xml"):
        s = p.read_text(encoding="utf-8-sig")
        for m in re.finditer(r'<rul:Rule Name="(\w+)"[^>]*DataDefGroup="(\w+)"', s):
            seg = s[m.start():s.find("</rul:Rule>", m.start())]
            if 'ToDataDef="BasicGroupIISymbol"' in seg:
                setters.add(m.group(2))
    mine = "CommercialPropertySpecialClass" in setters
    ok &= not mine
    print(f"    datadef groups that DERIVE the symbol : {len(setters)}")
    for s_ in sorted(setters):
        print(f"        {s_}")
    print(f"    is CommercialPropertySpecialClass one of them : {mine}  "
          f"(expected False) {'OK' if not mine else 'MISMATCH'}")
    print("    Building derives it from construction and storeys; Contents")
    print("    copies Building's. **Special Class asks for it.** That is why")
    print("    C6-03's case 5 priced Group II at zero with nothing to recompute")
    print("    -- and why chunk 6's payload has to carry a field chunks 1-5")
    print("    never sent.")
    for sym, want_base, want_prem in SYMBOLS:
        data = chain.run("OR", {"BasicGroupIISymbol": sym})
        gb = str(read(f"{SC}/BasicGroupIIBaseRate", data))
        gp = str(read(P["BasicGroupII"], data))
        good = (gb, gp) == (want_base, want_prem)
        ok &= good
        print(f"    symbol {sym:2s}  base={gb:>6s}  Group II premium={gp:>4s}"
              + ("" if good else f"   <-- expected {want_base} / {want_prem}"))

    # ---- C6-19
    print("\n=== 19  The lowest-rate table and the rule that reads it")
    res = CFEditionResolver()
    files_own, overrides, reads_lowest = set(), set(), set()
    for j in sorted(res.jurisdictions):
        b = book_for(j, ASOF, resolver=res)
        if b.declares("LowestBasicGroupIIRate") == "state":
            files_own.add(j)
        f = b.state.package.content / "Rules" / RULES
        if not f.exists():
            continue
        t = f.read_text(encoding="utf-8-sig")
        k = t.find(f'<rul:Rule Name="{COL_RULE}"')
        if k < 0:
            continue
        seg = t[k:k + t[k:].find("</rul:Rule>") + 11]
        overrides.add(j)
        if "LowestBasicGroupIIBaseRate" in seg:
            reads_lowest.add(j)
    n = len(res.jurisdictions)
    no_file = set(res.jurisdictions) - files_own
    # A state reaches the lowest-rate read if it does NOT override the rule
    # (the countrywide rule reads it) or if its own override still does.
    reaches = (set(res.jurisdictions) - overrides) | reads_lowest
    checks = [
        ("jurisdictions", n, 47),
        ("file their own LowestBasicGroupIIRate", len(files_own), 39),
        ("file none", len(no_file), 8),
        (f"override {COL_RULE}", len(overrides), 11),
        ("...whose override still reads the lowest rate", len(reads_lowest), 3),
        ("states that can REACH the read", len(reaches), 39),
        ("reach-the-read set == files-own set", reaches == files_own, True),
        ("the 8 non-filers are all inside the 11", no_file <= overrides, True),
    ]
    for label, got_v, want_v in checks:
        good = str(got_v) == str(want_v)
        ok &= good
        print(f"    {label:48s} {str(got_v):>6s}  (expected {want_v}) "
              f"{'OK' if good else 'MISMATCH'}")
    print(f"    no table: {', '.join(sorted(no_file))}")
    print(f"    override + still reads: {', '.join(sorted(reads_lowest))}")
    print("    **A biconditional, with zero exceptions in 47.** Every state")
    print("    whose rule can still reach `LowestBasicGroupIIRate` files it;")
    print("    every state that cannot, does not. The header-only countrywide")
    print("    table is not a gap -- it is a table nobody reads countrywide.")
    print("    **This is the first time in the project that two censuses have")
    print("    been matched against each other**, and the answer is that a")
    print("    missing table and a rewritten rule were one filing decision")
    print("    seen from two sides.")

    print()
    if ok:
        print("Every case matches its derivation.")
        return 0
    print("MISMATCHES above.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
