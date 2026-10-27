#!/usr/bin/env python3
"""Gate point 7 -- every exclusion's endorsement record, per datadef group.

The gate exists because Property does not file one exclusion record per policy.
It files **one per coverage**: a vandalism exclusion on the building is a
different record from a vandalism exclusion on the contents, which is different
again from one on business income. A rater that offers a single "vandalism
excluded?" checkbox and feeds it to every coverage is not reading ISO's content
-- it is making a simplification, and the gate's requirement is that the
simplification be logged rather than left implicit.

This enumerates, for every exclusion factor rule in the countrywide package,
the endorsement record each datadef group actually tests -- the `AtInputDataDef`
of its `Exist`/`NotExist` gate.

    python scripts/cf/05_exclusion_records.py [--asof YYYYMMDD]

Exit 0 always: this is a census, not a pass/fail. What it produces is the list
that a rating UI, a payload builder and every later chunk have to honour.
"""
from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from importlib import import_module

from cf_engine.resolve import book_for

golden = import_module("01_golden_case")

#: A rule that turns an exclusion election into a rating input -- a factor, a
#: rate, or an INDICATOR.
#:
#: `Indicator` was added 2026-09-18, in chunk 3, and it is the whole reason
#: theft appears in this census at all. Vandalism, wind/hail and sprinkler
#: leakage all test their endorsement record inside the rule that computes the
#: factor, so `Factor|Rate` found them. **Theft does not.**
#: `SetSpecialTheftExclusionFactor` tests an integer,
#: `SpecialTheftExclusionIndicator`, which a SEPARATE rule sets from the
#: endorsement record -- so the factor rule contains no `Exist` at all and this
#: census reported theft as though it did not exist.
#:
#: That matters because **theft is chunk 3's exclusion.** Gate point 7 would
#: have passed on a census that silently omitted the one family the chunk
#: actually needed. Same failure shape as gate point 6's: a rule that delegates
#: is invisible to a check that only reads the rule in front of it.
_EXCL_RULE = re.compile(
    r"^(Set|Lookup).*Excl(usion|uded)?.*(Factor|Rate|Indicator)")

#: `DoMessage*` rules also test endorsement records, but they validate rather
#: than rate. Counted separately: they are gate point 9's population, not
#: point 7's.
_MSG_RULE = re.compile(r"^DoMessage")

#: The datadef group chunks 1, 2 and 3 all rate in.
CHUNK1_GROUP = "CommercialPropertyStructure"

#: The exclusion families each chunk's chain actually consumes, so the census
#: can say which are answered and which are still inherited silence.
BY_CHUNK = {
    "chunk 1 (Basic Group I)": ["VandalismExclusion",
                                "SprinklerLeakageExclusion"],
    "chunk 2 (Basic Group II)": ["WindstormOrHailExclusion"],
    "chunk 3 (Broad and Special)": [
        "TheftExclusion", "CyberIncidentExclusion",
        "CyberIncidentExclusionWithEnsuingCausesOfLossExceptions"],
    # Chunk 6 rates in a DIFFERENT datadef group, so "ours" has to be asked of
    # that group. Special Class files its own record for every family it
    # consumes -- none of them is Building's.
    "chunk 6 (Special Class)": (
        "CommercialPropertySpecialClass",
        ["VandalismExclusion", "WindstormOrHailExclusion", "TheftExclusion",
         "CyberIncidentExclusion",
         "CyberIncidentExclusionWithEnsuingCausesOfLossExceptions"]),
    "chunk 7 (Special Class Busn Income)": (
        "CommercialPropertySpecialClassBusnIncome",
        ["VandalismExclusion", "WindstormOrHailExclusion", "TheftExclusion",
         "CyberIncidentExclusion",
         "CyberIncidentExclusionWithEnsuingCausesOfLossExceptions"]),
    # **Chunk 8 is not its own datadef group.** Legal Liability's factors live
    # in `CommercialPropertyStructure` and `CommercialPropertyPersonalProperty`
    # -- it is a BRANCH of those coverages, not a coverage beside them -- so it
    # inherits their exclusion records wholesale and files none of its own.
    # Listed twice, once per side, because that is the claim being checked.
    "chunk 8 (Legal Liability, Building side)": (
        "CommercialPropertyStructure",
        ["VandalismExclusion", "SprinklerLeakageExclusion",
         "WindstormOrHailExclusion", "TheftExclusion"]),
    "chunk 8 (Legal Liability, Contents side)": (
        "CommercialPropertyPersonalProperty",
        ["VandalismExclusion", "SprinklerLeakageExclusion",
         "WindstormOrHailExclusion", "TheftExclusion"]),
    # Chunk 9's own averaging engine, `CommercialPropertyBlanketRatingDetail`
    # -- the 7th datadef group this project has populated. Its own 135 rules
    # test NO exclusion-family `Exist`/`NotExist` at all (confirmed directly,
    # 0 hits under the same regex every prior chunk used) -- unlike C9-14's
    # finding that the blanket PREMIUM path inherits Structure/Contents'
    # exclusion records by re-executing their SetPremium rules, the Detail
    # engine that computes the average/highest rate never elects or tests one
    # of its own. Listed with the same five families every prior chunk
    # checked, so the absence is an enumerated fact rather than an omission.
    "chunk 9 (Blanket Rating Detail)": (
        "CommercialPropertyBlanketRatingDetail",
        ["VandalismExclusion", "WindstormOrHailExclusion", "TheftExclusion",
         "CyberIncidentExclusion",
         "CyberIncidentExclusionWithEnsuingCausesOfLossExceptions"]),
}


def lname(tag):
    return tag.rsplit("}", 1)[-1]


def family(record: str) -> str:
    """The exclusion family a record belongs to, from the record's own name."""
    leaf = record.rstrip("/").split("/")[-1]
    leaf = leaf.replace("CommercialProperty", "")
    # Longest first: `SpclClassBusnIncome` must not be stripped to
    # `SpclClass` by matching `BusnIncome` and leaving the rest, which would
    # split one family into two and overstate the count.
    for suffix in sorted(("BusnIncome", "PrsnlProp", "SpecialClass",
                          "SpclClass", "SpclClassBusnIncome",
                          "SpecialClassBusnIncome"), key=len, reverse=True):
        if leaf.endswith(suffix):
            return leaf[: -len(suffix)]
    return leaf


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--asof", default=golden.ASOF)
    a = ap.parse_args()

    book = book_for("CW", a.asof)
    rules_dir = book.state.package.content / "Rules"
    print(f"Gate point 7 -- exclusion endorsement records, "
          f"{book.state.pkg_id}\n")

    # family -> datadef group -> set of records
    fams = defaultdict(lambda: defaultdict(set))
    rule_of = defaultdict(set)
    msg_refs = defaultdict(set)
    for f in sorted(rules_dir.glob("*.Rule.xml")):
        try:
            root = ET.fromstring(f.read_text(encoding="utf-8-sig",
                                             errors="replace"))
        except ET.ParseError:
            continue
        for el in root:
            if lname(el.tag) != "Rule":
                continue
            name = el.get("Name") or ""
            rating, message = _EXCL_RULE.match(name), _MSG_RULE.match(name)
            if not (rating or message):
                continue
            group = el.get("DataDefGroup", "?")
            for d in el.iter():
                if lname(d.tag) not in ("Exist", "NotExist"):
                    continue
                rec = d.get("AtInputDataDef")
                if not rec:
                    continue
                if rating:
                    fams[family(rec)][group].add(rec)
                    rule_of[family(rec)].add(name)
                elif "Excl" in rec:
                    msg_refs[family(rec)].add(name)

    total_groups = 0
    for fam in sorted(fams):
        groups = fams[fam]
        total_groups += len(groups)
        distinct = {r.rstrip("/").split("/")[-1]
                    for recs in groups.values() for r in recs}
        print(f"{fam}")
        print(f"   {len(groups)} datadef groups, {len(distinct)} DISTINCT "
              f"endorsement records")
        print(f"   rules: {', '.join(sorted(rule_of[fam]))}")
        for g in sorted(groups):
            marker = "  <-- chunks 1-3 rate here" if g == CHUNK1_GROUP else ""
            for rec in sorted(groups[g]):
                print(f"      {g:52s} {rec.rstrip('/').split('/')[-1]}{marker}")
        print()

    print("-" * 72)
    print(f"{len(fams)} exclusion families, {total_groups} "
          f"(family, datadef group) pairs.\n")
    print("What this means for anything that collects these as INPUTS:")
    print("  * An exclusion is elected PER COVERAGE, not per policy. The record")
    print("    a building's vandalism exclusion lives in is not the record the")
    print("    contents' lives in, and neither is business income's.")
    print("  * So a single 'vandalism excluded?' control feeding every coverage")
    print("    is a SIMPLIFICATION. It may well be the right product decision;")
    print("    it is not what ISO filed, and the gate's requirement is that it")
    print("    be logged (S-1/S-2/S-3 in Rater_Simplifications_Backlog.md)")
    print("    rather than left implicit.")
    print("  * Chunk 1 elects none of them, which is why its golden cases say")
    print("    nothing about this. That is the silence this census replaces.")

    print("\n" + "-" * 72)
    print("PER CHUNK -- the families each chain actually consumes\n")
    for chunk, wanted in BY_CHUNK.items():
        group = CHUNK1_GROUP
        if isinstance(wanted, tuple):
            group, wanted = wanted
        print(f"  {chunk}" + ("" if group == CHUNK1_GROUP
                              else f"   [{group}]"))
        for fam in wanted:
            groups = fams.get(fam)
            if not groups:
                print(f"      {fam:24s} NOT FOUND IN THE CENSUS")
                continue
            mine = groups.get(group, set())
            distinct = {r.rstrip("/").split("/")[-1]
                        for recs in groups.values() for r in recs}
            rec = ", ".join(sorted(r.rstrip("/").split("/")[-1] for r in mine)) \
                or "(not elected in this datadef group)"
            print(f"      {fam:24s} {len(distinct)} record(s) across "
                  f"{len(groups)} group(s)")
            print(f"      {'':24s} ours: {rec}")
        print()

    if msg_refs:
        n = sum(len(v) for v in msg_refs.values())
        print(f"  {n} DoMessage rules also test an exclusion record, across "
              f"{len(msg_refs)} families.")
        print("  Those validate rather than rate, so they are gate point 9's")
        print("  population, not point 7's -- but they are the reason an")
        print("  exclusion can be elected correctly and STILL return an error:")
        for fam in sorted(msg_refs):
            print(f"      {fam:28s} {len(msg_refs[fam])} message rule(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
