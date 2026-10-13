"""Chunk 13 opening census: Terrorism / TRIA.

Read-only. Always exits 0 -- a census, not a test.

The build order sizes chunk 13 as "16 rule files". This census counts what is
actually there, in three places, because terrorism turns out not to be a
coverage file of its own:

  1. the terrorism-NAMED rule files (forms, disclosures, PostTRIA);
  2. terrorism rules EMBEDDED in the core datadef groups (policy, location,
     and each of the five coverage groups);
  3. the state layer: which of the 46 states (PR excluded) file or override
     any of either.

Plus the tables those rules read (row counts, header-only), the elements they
use against the interpreter's registry, the date arithmetic (OI-107 lives
here), and the ISO STC fixtures that carry a terrorism record.

    python scripts/cf/143_chunk13_census.py
"""
import collections
import csv
import re
import sys
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from cf_engine.resolve import book_for
from gl_engine.interp import nodes

census11 = import_module("106_chunk11_census")
ASOF = "20260917"
ISO_CF = Path("F:/ISO_ERC_Files/CF")
KEY = re.compile(r"Terror|TRIA|Terrsm")
DATE_NODES = {"DateDifference", "DateAdd", "DateCreate", "DatePart"}
STRUCTURAL = {"Rules", "Rule", "MetaData", "MetaDataCode", "Test", "Then", "Else",
              "Keys", "When", "Otherwise", "Arg", "Param"}
CORE = {
    "policy": "CommercialPropertyRules.Rule.xml",
    "location": "CommercialPropertyLocationRules.Rule.xml",
    "building": "CommercialPropertyStructureRules.Rule.xml",
    "contents": "CommercialPropertyPersonalPropertyRules.Rule.xml",
    "business income": "CommercialPropertyBusinessIncomeRules.Rule.xml",
    "special class": "CommercialPropertySpecialClassRules.Rule.xml",
    "SC business income": "CommercialPropertySpecialClassBusnIncomeRules.Rule.xml",
}


def rows(path):
    with open(path, encoding="utf-8-sig") as h:
        return sum(1 for r in csv.reader(h) if r) - 1


def rules_in(text):
    return {m.group(1): m.group(0)
            for m in re.finditer(r'<rul:Rule Name="([^"]+)".*?</rul:Rule>', text, re.S)}


def main():
    b = book_for("OR", ASOF)
    cw = b.parent.package.content
    rules_dir, tables_dir = cw / "Rules", cw / "Rate Tables"
    all_rules = {f.name: f.read_text(encoding="utf-8-sig") for f in rules_dir.glob("*.xml")}
    registry = set(nodes.EVAL)

    books = {}
    for j in census11.JURIS:
        if j == "PR":
            continue
        try:
            books[j] = book_for(j, ASOF)
        except Exception:
            pass
    print(f"{b}\n{len(all_rules)} countrywide rule files; {len(books)} states (PR excluded)\n")

    # 1. named files -----------------------------------------------------------------------
    named = sorted(n for n in all_rules if KEY.search(n))
    print("=" * 78)
    print(f"1. TERRORISM-NAMED RULE FILES (countrywide {b.parent.package.content.parent.name})")
    print("-" * 78)
    for n in named:
        rs = rules_in(all_rules[n])
        kind = "SetPremium" if "SetPremium" in rs else (
            "inert (system rules only)" if set(rs) <= {"InitializeRuleSet", "CalculateTotalPremium", "ErcProcess"}
            else "rules, no premium")
        print(f"  {n.replace('CommercialProperty', '').replace('Rules.Rule.xml', ''):95s} {len(rs):3d} rules  {kind}")
    print(f"  total: {len(named)}  (build order says 16)")

    # 1b. across parent editions
    parents = {}
    for j, bk in books.items():
        parents.setdefault(bk.parent.package.content.parent.name, bk.parent.package.content)
    print("\n  named files by parent edition:")
    for name, content in sorted(parents.items()):
        fs = sorted(f.name for f in (content / "Rules").glob("*.xml") if KEY.search(f.name))
        print(f"    {name:28s} {len(fs)}")
    union = set()
    for content in parents.values():
        union |= {f.name for f in (content / "Rules").glob("*.xml") if KEY.search(f.name)}
    print(f"    union across parents: {len(union)}")

    # 2. embedded rules ----------------------------------------------------------------------
    print("\n" + "=" * 78)
    print("2. TERRORISM RULES EMBEDDED IN THE CORE GROUPS (countrywide)")
    print("-" * 78)
    embedded = {}
    for grp, f in CORE.items():
        rs = rules_in(all_rules[f])
        hit = {n: body for n, body in rs.items() if KEY.search(body)
               and n not in {"InitializeRuleSet", "CalculateTotalPremium", "ErcProcess",
                             "ErcSetRatesAndFactors", "ErcRate", "ErcRunPostUnderwritingLogic",
                             "ErcSetStatisticalCodes", "ErcDoConditionalMandatoryLogic",
                             "SetLimitsToUse", "SetBlanketRatesAndFactors"}}
        embedded[grp] = hit
        kinds = collections.Counter(
            "attach form" if n.startswith("AttachForm") else
            "message" if n.startswith("DoMess") else
            "stat code" if "StatCode" in n else
            "lookup" if n.startswith("Lookup") else
            "premium" if "Premium" in n else "rate/factor" for n in hit)
        print(f"  {grp:20s} {len(hit):3d} rules  " + ", ".join(f"{v} {k}" for k, v in sorted(kinds.items())))
    # premium rules per coverage group, and what they read
    print("\n  premium-bearing terrorism rules per coverage group:")
    for grp in ["building", "contents", "business income", "special class", "SC business income"]:
        prem = sorted(n for n in embedded[grp] if "Premium" in n and not n.startswith("DoMess"))
        print(f"    {grp:20s} {', '.join(prem)}")
    # does any terrorism premium read another group's finished premium?
    readers = collections.Counter()
    for grp, hit in embedded.items():
        for n, body in hit.items():
            for fld in re.findall(r'FromDataDef="([^"]*Premium[^"]*)"', body):
                readers[(grp, n, fld)] += 1
    print("\n  premium fields READ by terrorism rules (the 'runs last' claim):")
    for (grp, n, fld), c in sorted(readers.items()):
        print(f"    {grp:20s} {n:40s} reads {fld}")

    # 3. tables -------------------------------------------------------------------------------
    print("\n" + "=" * 78)
    print("3. TABLES READ")
    print("-" * 78)
    bodies = [body for hit in embedded.values() for body in hit.values()] + \
             [all_rules[n] for n in named]
    mats = collections.Counter()
    for body in bodies:
        mats.update(set(re.findall(r'MatrixFromConstant="([^"]+)"', body)) - {"Pages"})
    for t in sorted(mats):
        f = tables_dir / f"{t}.RateTable.csv"
        r = rows(f) if f.exists() else None
        filers = sorted(j for j, bk in books.items()
                        if (bk.state.package.content / "Rate Tables" / f"{t}.RateTable.csv").exists())
        print(f"  {t:60s} CW rows {str(r):>5s}   states filing {len(filers):2d}"
              + (f" ({' '.join(filers)})" if 0 < len(filers) <= 12 else ""))

    # 4. elements -----------------------------------------------------------------------------
    print("\n" + "=" * 78)
    print("4. ENGINE READINESS BY ELEMENT NAME (operand types are a task, C11 lesson)")
    print("-" * 78)
    elems = collections.Counter()
    for body in bodies:
        elems.update(re.findall(r"<rul:(\w+)", body))
    missing = sorted(e for e in elems if e not in registry and e not in STRUCTURAL)
    print(f"  distinct elements: {len(elems)};  not in the interpreter registry: {missing or 'none'}")
    print(f"  date nodes: {dict((e, elems[e]) for e in DATE_NODES if e in elems) or 'none'}")
    print(f"  Power: {elems.get('Power', 0)}")

    # 5. state layer --------------------------------------------------------------------------
    print("\n" + "=" * 78)
    print("5. STATE LAYER (46 states, both layers)")
    print("-" * 78)
    emb_names = {(CORE[g], n) for g, hit in embedded.items() for n in hit}
    named_filers, override = collections.defaultdict(list), collections.defaultdict(list)
    for j, bk in sorted(books.items()):
        rd = bk.state.package.content / "Rules"
        if not rd.exists():
            continue
        for f in rd.glob("*.xml"):
            if KEY.search(f.name):
                named_filers[f.name.replace("CommercialProperty", "").replace("Rules.Rule.xml", "")].append(j)
            elif f.name in CORE.values():
                rs = rules_in(f.read_text(encoding="utf-8-sig"))
                for n in rs:
                    if (f.name, n) in emb_names:
                        override[n].append(j)
    print("  states filing a terrorism-NAMED file:")
    for n, js in sorted(named_filers.items()):
        print(f"    {n:80s} {len(js):2d}  {' '.join(js)}")
    print("  states overriding an EMBEDDED terrorism rule (incl. pure pins):")
    for n, js in sorted(override.items(), key=lambda kv: -len(kv[1])):
        print(f"    {n:60s} {len(js):2d}  {' '.join(js) if len(js) <= 14 else ''}")
    touched = set(j for js in named_filers.values() for j in js) | set(j for js in override.values() for j in js)
    print(f"  states touching terrorism at all: {len(touched)} of {len(books)}")

    # 6. fixtures -----------------------------------------------------------------------------
    print("\n" + "=" * 78)
    print("6. ISO STC FIXTURES")
    print("-" * 78)
    stc = sorted(ISO_CF.rglob("STC/*.json"))
    disc = [p for p in stc if "ZzDisclosure" in p.read_text(encoding="utf-8", errors="replace")]
    forms = collections.Counter()
    for p in stc:
        t = p.read_text(encoding="utf-8", errors="replace")
        for n in named:
            stem = n.replace("Rules.Rule.xml", "")
            if f'"{stem}"' in t or f'"{stem}Table"' in t:
                forms[stem.replace("CommercialProperty", "")] += 1
    print(f"  {len(stc)} CF STC payloads; {len(disc)} carry a terrorism disclosure record")
    for n, c in forms.most_common():
        print(f"    {n:95s} {c}")
    tria = [p for p in stc if re.search(r'"TRIAExpirationDate"|"TerrorismTerritory"', p.read_text(encoding="utf-8", errors="replace"))]
    print(f"  payloads carrying TRIAExpirationDate or TerrorismTerritory: {len(tria)}")


if __name__ == "__main__":
    main()
