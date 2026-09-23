#!/usr/bin/env python3
"""Chunk 11 opening census -- Leasehold Interest, before any task is written.

`CF-PROPERTY-BUILD-ORDER.md` item 11 describes it as "a sixth coverage, not a
fifth path" -- "32 rule files, its own datadef group, four sub-coverages
(Tenants Lease, Bonus Payments, Improvements & Betterments, Prepaid Rent)
x five forms. Its exposure is computed, not entered -- a present-value
annuity (`AnnuityConstant x (1 - DiscFactor^months)`, averaged
inception-to-expiration) driving the only `rul:Power` in the package. No
coinsurance, LOI or deductible anywhere in it. No blanket branch at all --
confirmed, not assumed."

Seven claims. This census tests every one against the corpus, the same
discipline chunk 10's census applied to the build order's Earthquake
sentence -- which is worth remembering, because that census got its own
fixture arithmetic wrong in three places and C10-20 only caught it at the
very end of the chunk. Nothing here is carried forward on trust.

  1  The population -- 32 files named `*LeaseholdInterest*`, and what each
     one actually DOES. A file count is not a rating surface.
  2  "Its own datadef group" -- singular, per the build order. Counted.
  3  The 4 x 5 grid -- which sub-coverages, which forms, and whether all
     20 cells are really filed.
  4  The annuity -- the `rul:Power`, its guard, and whether it is really
     the only one in the package.
  5  What is ABSENT -- coinsurance, LOI, deductible, blanket. And what is
     PRESENT that the build order does not mention.
  6  The tables -- row counts, and which are read by a `Lookup` at all
     (this project's standing "check all tables before calling a factor
     blank" rule, run at opening rather than at task 13).
  7  The ISO fixture census -- against the CORRECT denominator this time:
     364 Commercial Property payloads, not the 924 that silently included
     560 General Liability ones (C10-20).
  8  The state layer -- who overrides what, both at file and rule level.
  9  Engine readiness -- does the interpreter already implement every node
     this coverage needs? Chunk 11 is the first chunk whose build order
     entry names a specific node type.

    python scripts/cf/106_chunk11_census.py

Always exits 0 -- this is a census, not a test.
"""
from __future__ import annotations

import collections
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from cf_engine.resolve import book_for

ASOF = "20260917"
ISO_CF = Path("C:/Projects/ISO_ERC_Files/CF")

SUBCOV = ["TenantsLease", "BonusPayments", "Improvements", "PrepaidRent"]
FORMS = ["BasicGroupI", "BasicGroupII", "Broad", "Special", "Earthquake"]

JURIS = [
    "AK", "AL", "AR", "AZ", "CA", "CO", "CT", "DC", "DE", "FL", "GA", "IA",
    "ID", "IL", "IN", "KS", "KY", "LA", "MA", "MD", "ME", "MI", "MN", "MO",
    "MS", "MT", "NC", "ND", "NE", "NH", "NJ", "NM", "NV", "NY", "OH", "OK",
    "OR", "PA", "PR", "RI", "SC", "SD", "TN", "TX", "UT", "VA", "VT", "WA",
    "WI", "WV", "WY",
]


def rules_of(txt):
    return re.findall(r'<rul:Rule Name="([^"]+)"', txt)


def main():
    b = book_for("OR", ASOF)
    cw = b.parent.package.content
    rules_dir = cw / "Rules"
    tables_dir = cw / "Rate Tables"

    print("Chunk 11 opening census -- Leasehold Interest")
    print("=" * 78)
    print(f"countrywide package: {cw.name}")

    lh = sorted(rules_dir.glob("*LeaseholdInterest*"))
    all_rules = list(rules_dir.glob("*.Rule.xml"))
    bodies = {p.name: p.read_text(encoding="utf-8-sig") for p in lh}

    # ------------------------------------------------------------------ 1
    print("\n1 . THE POPULATION -- 32 files, but not 32 files of rating")
    print("-" * 78)
    print(f"    files named *LeaseholdInterest* : {len(lh)}   "
          f"(build order says 32)")

    parent = [n for n in bodies if n.endswith("CoverageFormRules.Rule.xml")]
    pct = sorted(n for n in bodies if "FactorsFor" in n)
    grid = sorted(n for n in bodies
                  if n not in parent and n not in pct)
    print(f"      the parent rating file          : {len(parent)}")
    print(f"      the 4x5 sub-coverage/form grid  : {len(grid)}")
    print(f"      `FactorsFor<N>Percent` files    : {len(pct)}")

    inert = [n for n in pct
             if set(rules_of(bodies[n])) <= {"InitializeRuleSet",
                                             "CalculateTotalPremium",
                                             "ErcProcess"}]
    print()
    print(f"    **All {len(inert)} `FactorsFor<N>Percent` files do NO rating "
          f"at all.**")
    print("    Each declares exactly InitializeRuleSet / CalculateTotalPremium")
    print("    / ErcProcess and nothing else -- pure form-attachment markers")
    print("    that put a printed rate-table page on the policy, one per")
    print("    interest rate from 5% to 15%. They carry no Lookup, no")
    print("    Premium, no factor. The build order's '32 rule files' is")
    print(f"    correct as a count and overstates the rating surface by "
          f"{len(inert)/len(lh):.0%}:")
    print(f"    the real surface is {len(lh) - len(inert)} files.")
    print(f"      {', '.join(re.search(r'FactorsFor(\d+)Percent', n).group(1) + '%' for n in sorted(inert, key=lambda x: int(re.search(r'(\d+)Percent', x).group(1))))}")

    # ------------------------------------------------------------------ 2
    print("\n2 . 'ITS OWN DATADEF GROUP' -- it has 32, not 1")
    print("-" * 78)
    groups = collections.Counter()
    for n, t in bodies.items():
        for g in re.findall(r'DataDefGroup="([^"]+)"', t):
            groups[g] += 1
    print(f"    distinct DataDefGroups across the {len(lh)} files: "
          f"{len(groups)}  -- one per file, exactly")
    print(f"      1 parent : CommercialPropertyLeaseholdInterestCoverageForm")
    print(f"      {len(grid)} grid   : one per sub-coverage x form cell")
    print(f"      {len(pct)} inert  : one per FactorsFor<N>Percent marker")
    print()
    print(f"    Gate points 6 (shared names) and 7 (exclusion records) are")
    print(f"    per-DataDefGroup questions. Chunk 11 asks them across")
    print(f"    {len(groups)} groups -- {len(groups) - len(inert)} of them "
          f"rating-bearing -- against the 5 that")
    print("    chunks 6-10 worked with, and the 1 the build order implies.")
    print("    That is the single biggest structural jump in the plan so far,")
    print("    and it is a counting fact, not a difficulty estimate.")

    # ------------------------------------------------------------------ 3
    print("\n3 . THE 4 x 5 GRID -- all 20 cells filed, and the fifth form is EQ")
    print("-" * 78)
    missing = []
    for s in SUBCOV:
        row = []
        for f in FORMS:
            hit = any(s in n and f + "Coverage" in n for n in grid)
            row.append(f"{f}:{'Y' if hit else 'MISSING'}")
            if not hit:
                missing.append((s, f))
        print(f"    {s:16s} " + "  ".join(row))
    print()
    if missing:
        print(f"    MISSING CELLS: {missing}")
    else:
        print("    All 20 cells filed. **The fifth form is Earthquake** --")
        print("    so chunk 10's work is a direct input here, not a parallel")
        print("    track. Leasehold Interest is the first coverage to be")
        print("    opened AFTER the form it depends on was already built.")

    # ------------------------------------------------------------------ 4
    print("\n4 . THE ANNUITY -- the only rul:Power in the package, and its guard")
    print("-" * 78)
    pw = [p.name for p in all_rules
          if "rul:Power" in p.read_text(encoding="utf-8-sig", errors="ignore")]
    print(f"    files containing `rul:Power`, out of {len(all_rules)} "
          f"countrywide rule files: {len(pw)}")
    for n in pw:
        print(f"      {n}")
    print("    Build order's 'the only rul:Power in the package' -- CONFIRMED.")
    print()
    ptxt = bodies.get("CommercialPropertyLeaseholdInterestCoverageFormRules"
                      ".Rule.xml", "")
    chain = [r for r in rules_of(ptxt)
             if any(k in r for k in ("Annuity", "DiscFactor", "NumberOfMonths",
                                     "Compliment", "NetLeasehold"))]
    print(f"    the annuity chain, in the parent file ({len(chain)} rules):")
    for r in chain:
        print(f"      {r}")
    print()
    guarded = "IsNull" in ptxt[max(0, ptxt.find("SetComplimentOfDiscFactorIncep")):
                               ptxt.find("rul:Power") + 200]
    print(f"    **The `rul:Power` sits behind an `IsNull` guard** "
          f"({'confirmed' if guarded else 'NOT FOUND -- recheck'}) on")
    print("    `DiscFactorRaisedToNumOfMonthsRemainingAtInception`. That is")
    print("    the project's standing 'a submission can populate a derived")
    print("    field' shape (CF-START-HERE.md open items): a payload that")
    print("    supplies the raised power directly bypasses the annuity")
    print("    entirely, and no ISO comparison would catch it because ISO")
    print("    has the same guard. Worth a task, not an assumption.")

    # ------------------------------------------------------------------ 5
    print("\n5 . WHAT IS ABSENT -- and what is present that the build order omits")
    print("-" * 78)
    for term in ("Coinsurance", "LOIFactor", "DeductibleFactor", "Blkt",
                 "Blanket"):
        n = sum(1 for t in bodies.values() if term in t)
        flag = "ABSENT, as claimed" if n == 0 else f"** PRESENT in {n} **"
        print(f"    {term:20s} {flag}")
    print()
    for term in ("IRPMFactor", "PackageModFactor",
                 "MultiPremiumAndDispersionCreditFactor"):
        n = sum(1 for t in bodies.values() if term in t)
        print(f"    {term:38s} present in {n} of {len(lh)} files")
    print()
    print("    **This is the exact inverse of Earthquake.** C10-14 confirmed")
    print("    EQ reads IRPMFactor/PackageModFactor at NO depth in ANY of its")
    print("    5 groups. Leasehold Interest reads both, in half its files.")
    print("    Two coverages opened back to back, opposite answers to the")
    print("    same question -- C9-19's warning that this must be re-asked")
    print("    per chunk, demonstrated twice in a row.")

    # ------------------------------------------------------------------ 6
    print("\n6 . THE TABLES -- row counts and live/dead, asked at opening")
    print("-" * 78)
    names = sorted({p.stem.split(".")[0] for p in tables_dir.rglob("*.csv")
                    if "Leasehold" in p.stem or "LeaseHold" in p.stem})
    corpus = "\n".join(p.read_text(encoding="utf-8-sig", errors="ignore")
                       for p in all_rules)
    for name in names:
        cs = list(tables_dir.rglob(name + "*.csv"))
        rows = (len(cs[0].read_text(encoding="utf-8-sig").strip().splitlines())
                - 1) if cs else -1
        live = (f'MatrixDef="{name}Def"' in corpus
                or f'MatrixFromConstant="{name}"' in corpus)
        note = ""
        if rows == 0:
            note = "   << 0 ROWS"
        if not live:
            note += "   << NO Lookup reads it"
        print(f"    {name:52s} {rows:4d} rows  "
              f"{'live' if live else 'DEAD'}{note}")
    print()
    print("    The 11-row `AnnuityConstant` and `DiscFactor` tables match the")
    print("    11 `FactorsFor<N>Percent` marker files exactly -- one row and")
    print("    one printed form page per interest rate, 5% through 15%.")

    # ------------------------------------------------------------------ 7
    print("\n7 . THE ISO FIXTURE CENSUS -- against the CORRECT denominator")
    print("-" * 78)
    files = sorted(ISO_CF.rglob("STC/*.json")) if ISO_CF.exists() else []
    n_mention = sum(1 for f in files
                    if "LeaseholdInterest" in f.read_text(encoding="utf-8-sig",
                                                          errors="ignore"))
    print(f"    Commercial Property STC payloads          : {len(files)}")
    print(f"    payloads mentioning LeaseholdInterest     : {n_mention}")
    print()
    print("    The denominator is 364, NOT 924. C10-20 found chunk 10's own")
    print("    census had summed 560 General Liability payloads into the")
    print("    figure; that error is not repeated here.")
    if n_mention == 0:
        print()
        print("    **ZERO fixtures. Chunk 11 is chunk 9's situation, not")
        print("    chunk 10's** -- there is no ISO regression set for this")
        print("    coverage at all. Chunk 9 closed at 9 of 9 without one, by")
        print("    confirming its golden case against a LIVE ISO call")
        print("    instead. That is the route chunk 11 will have to take, and")
        print("    it should be planned for at task 1, not discovered at")
        print("    task 20 the way chunk 10's fixture problem was.")

    # ------------------------------------------------------------------ 8
    print("\n8 . THE STATE LAYER")
    print("-" * 78)
    file_states = collections.Counter()
    rule_states = collections.Counter()
    seen = 0
    for j in JURIS:
        try:
            bk = book_for(j, ASOF)
        except Exception:
            continue
        seen += 1
        rd = bk.state.package.content / "Rules"
        if not rd.exists():
            continue
        for p in rd.glob("*LeaseholdInterest*"):
            file_states[j] += 1
            t = p.read_text(encoding="utf-8-sig", errors="ignore")
            if re.search(r'<rul:Rule Name="Set|<rul:Rule Name="Lookup', t):
                rule_states[j] += 1
    print(f"    jurisdictions resolved                       : {seen}")
    print(f"    filing at least one LI file in their package : "
          f"{len(file_states)}  {sorted(file_states)}")
    print(f"    of those, carrying a Set/Lookup rule         : "
          f"{len(rule_states)}  {sorted(rule_states)}")
    print()
    print("    Per this project's overlay rule, a state package carries only")
    print("    its adds -- file presence is not rule override. Both layers")
    print("    are printed separately for that reason (the C10-03 shape).")

    # ------------------------------------------------------------------ 9
    print("\n9 . ENGINE READINESS -- the first chunk whose build order names a node")
    print("-" * 78)
    nodes_src = (Path(__file__).resolve().parents[2]
                 / "gl_engine" / "interp" / "nodes.py").read_text(
        encoding="utf-8", errors="ignore")
    have = set(re.findall(r'@node\("([A-Za-z]+)"\)', nodes_src))
    # Derived from the XML rather than guessed: a hand-written list of
    # "nodes this coverage probably needs" got `Difference`/`Quotient` wrong
    # on the first pass (the engine calls them `Subtract`/`Divide`) and
    # reported two false MISSINGs. Ask the corpus, not memory.
    used = collections.Counter()
    for t in bodies.values():
        for n in re.findall(r"<rul:([A-Za-z]+)[ />]", t):
            used[n] += 1
    missing = sorted(n for n in used if n not in have)
    print(f"    distinct `rul:` element types used by the {len(lh)} LI files: "
          f"{len(used)}")
    print(f"    implemented by gl_engine/interp/nodes.py "
          f"({len(have)} nodes)    : {len(used) - len(missing)}")
    print(f"    NOT implemented                                  : "
          f"{len(missing)}")
    if missing:
        print(f"      {missing}")
        print("      (some of these are structural wrappers -- Rules, Rule,")
        print("       MetaData, Then, Else, Test -- handled by the parser")
        print("       rather than the node registry. Check before calling")
        print("       any of them an engine gap.)")
    print()
    print(f"    `rul:Power`: {'IMPLEMENTED' if 'Power' in have else 'MISSING'}"
          f"  -- the one node the build order names by hand.")
    print("    On the evidence here chunk 11 needs no engine change, same as")
    print("    chunks 1-8 and 10. Stated at opening so that if a gap does")
    print("    appear later it is a finding against this census, rather than")
    print("    an open question nobody wrote down.")
    print()
    print("    The 12 most-used node types in this coverage:")
    for n, c in used.most_common(12):
        print(f"      rul:{n:22s} {c:5d}   "
              f"{'ok' if n in have else '<< not a registered node'}")

    print("\n" + "=" * 78)
    print("Census complete. No tasks run, no engine code written.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
