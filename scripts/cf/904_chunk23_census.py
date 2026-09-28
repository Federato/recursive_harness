#!/usr/bin/env python3
"""Chunk 23 opening census -- state-only coverages.

Chunk 23's families exist in one state's filing only, so the census starts from
the other end: it ENUMERATES every state-only premium file in the 46 in-force
packages (a file name no countrywide package has, carrying a SetPremium), assigns
each to the chunk that owns it, and then runs the usual checks on the files that
fall to chunk 23:

  0  Ownership: every in-force state-only premium file -> owning chunk (built,
     planned or chunk 23), with state-only files that write a premium some other
     way (totals, Mine Subsidence) listed separately.
  1  Population per chunk-23 family, and the same file names in every batch of
     that state (the state-only "editions").
  2  The premium formula per file: operands, rate tables read directly, rules
     run in other files, rounding.
  3  Rate tables: rows in the state's own package, and whether a countrywide
     table of that name exists.
  4  Messages: every message rule in the state's package and CW that names a
     family record, one of its forms (from Form Pages) or its wording.
  5  Editions: the family's SetPremium in every package of that state, all
     batches, formula diffed against the in-force one.
  7  ISO evidence: fixtures carrying each record; stored responses with a
     non-zero premium on it.
  8  Attach points (the STATE's DataDef XSD) and on-switches.
  9  Engine readiness: rul: elements not registered; date / Power arithmetic.

    python scripts/cf/904_chunk23_census.py

Always exits 0 -- a census, not a test.
"""
from __future__ import annotations

import collections
import csv
import json
import re
import sys
import time
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))

from cf_engine.resolve import book_for
from gl_engine.interp import nodes

s18 = import_module("164_chunk14_c14-18_all_states")
rc1 = import_module("168_chunk15_rc1")
ASOF = "20260917"
ISO_CF = Path("C:/Projects/ISO_ERC_Files/CF")
RES = ROOT / "results" / "cf-raas"
P = "CommercialProperty"
STRUCTURAL = {"Rules", "Rule", "MetaData", "MetaDataCode", "Test", "Then", "Else",
              "Keys", "When", "Otherwise", "Arg", "Param"}
STANDARD = {"InitializeRuleSet", "CalculateTotalPremium", "ErcRate", "SetPremium",
            "SetPremiumIndicator", "ErcProcess", "SetCoverageOnPolicyIndicator"}

#: who owns each state-only premium file, first match wins
OWNERS = [
    (r"BuildingGlassTenantsPolicy", "chunk 19 (tenants' glass)"),
    (r"NorthCarolinaChangesAdditionalCoveredProperty", "chunk 20 (Additional Covered Property)"),
    (r"ChangesCommercialUnitsInResidentialCond", "chunk 21 (FL condo units)"),
    (r"MineSubsidence", "chunk 16 (Mine Subsidence) -- GATED"),
    (r"Y2KComputerRelated", "chunk 15 (Y2K) -- GATED"),
    (r"OrdinanceOrLaw.*Flood", "chunk 25 (flood)"),
    (r"OrdinanceOrLaw", "chunk 12 (Ordinance or Law) -- counted; VA/WV priced cases open"),
    (r"HeatingOil", "chunk 23"),
    (r"TenantRelocation", "chunk 23"),
    (r"AttorneysFees", "chunk 23"),
    (r"Earthquake.*California|California.*Earthquake|EarthquakeCoverageCalifornia", "chunk 23"),
]
#: chunk 23's families: (name, state, file pattern, wording)
FAMILIES = [
    ("MA heating-oil remediation", "MA", r"HeatingOil", ["Heating Oil"]),
    ("MA Tenant Relocation Expense", "MA", r"TenantRelocation", ["Tenant Relocation"]),
    ("AK Changes: Attorneys' Fees", "AK", r"AttorneysFees", ["Attorney"]),
    ("CA Additional / Limited Earthquake", "CA", r"Earthquake.*California|California.*Earthquake|EarthquakeCoverageCalifornia",
     ["Additional Earthquake", "Limited Earthquake", "Residential Property Lessors"]),
    ("VA Ordinance or Law state forms (chunk 12 open cases)", "VA", r"OrdinanceOrLaw(?!.*Flood)",
     ["Ordinance Or Law", "Ordinance or Law"]),
]


def owner(name):
    for pat, who in OWNERS:
        if re.search(pat, name):
            return who
    return "UNASSIGNED"


def short(n):
    return n.replace(P, "").replace("Rules.Rule.xml", "")


def rows(path):
    with open(path, encoding="utf-8-sig") as h:
        return sum(1 for r in csv.reader(h) if r) - 1


def rule_names(text):
    return re.findall(r'<rul:Rule Name="([^"]+)"', text)


def set_premium(text):
    m = re.search(r'<rul:Rule Name="SetPremium".*?</rul:Rule>', text, re.S)
    return None if not m else m.group(0)


def norm(body):
    return re.sub(r'\s+', ' ', re.sub(r'DataDefGroup="[^"]+"', '', body or ""))


def form_pages(pkg):
    out = set()
    f = pkg / "Form Pages" / "Pages.FormPage.csv"
    if f.exists():
        with open(f, encoding="utf-8-sig") as h:
            for r in csv.DictReader(h):
                num = re.match(r"((?:CP|IL) \d\d \d\d)", r.get("Number") or "")
                out.add((r["TableName"], r["Name"], num.group(1) if num else None))
    return out


def main():
    t0 = time.monotonic()
    or_book = book_for("OR", ASOF)
    cw = or_book.parent.package.content
    cw_rules = {f.name: f.read_text(encoding="utf-8-sig") for f in (cw / "Rules").glob("*.xml")}
    registry = set(nodes.EVAL)
    books = {j: book_for(j, ASOF) for j in s18.STATES}
    stc = {p.stem: p.read_text(encoding="utf-8-sig", errors="replace") for p in ISO_CF.rglob("STC/*.json")}

    replay = collections.Counter()
    for rp in RES.glob("chunk13_fixture_*_response.json"):
        seen = set()

        def walk(o, tag):
            if isinstance(o, dict):
                p = o.get("Premium")
                try:
                    if p not in (None, "") and float(p) != 0:
                        seen.add(tag)
                except (TypeError, ValueError):
                    pass
                for k, v in o.items():
                    if isinstance(v, (dict, list)):
                        walk(v, k)
            elif isinstance(o, list):
                for x in o:
                    walk(x, tag)
        walk(json.loads(rp.read_text(encoding="utf-8"))["Body"], "Body")
        replay.update(seen)

    # 0 ownership of every in-force state-only premium file
    print(f"{or_book}\n{len(cw_rules)} CW rule files; {len(books)} states (PR excluded)\n")
    print("[0] OWNERSHIP of every in-force state-only premium file", flush=True)
    owned = collections.defaultdict(list)
    other_writers = []
    for j, b in sorted(books.items()):
        rd = b.state.package.content / "Rules"
        if not rd.exists():
            continue
        for f in rd.glob("*.xml"):
            if f.name in cw_rules:
                continue
            t = f.read_text(encoding="utf-8-sig", errors="replace")
            if '"SetPremium"' in t:
                owned[owner(f.name)].append(f"{j} {short(f.name)}")
            elif re.search(r'ToDataDef="[^"]*Premium"', t):
                other_writers.append(f"{j} {short(f.name)} ({owner(f.name)})")
    total = sum(len(v) for v in owned.values())
    print(f"  {total} in-force state-only premium files")
    for who, fs in sorted(owned.items()):
        states = collections.Counter(x.split()[0] for x in fs)
        print(f"  {who:70s} {len(fs):3d}  {' '.join(f'{s}:{n}' for s, n in sorted(states.items()))}")
    print(f"  state-only files writing a premium field without SetPremium (totals etc.): {len(other_writers)}")
    for x in other_writers:
        print(f"    {x}")

    # 1-9 per chunk-23 family
    summary = []
    for i, (fam, st, pat, words) in enumerate(FAMILIES, 1):
        m, sec = divmod(int(time.monotonic() - t0), 60)
        print(f"\n[{i}/{len(FAMILIES)}  {m}m{sec:02d}s] {fam} ({st})", flush=True)
        print("=" * 90)
        b = books[st]
        pkg = b.state.package.content
        srules = {f.name: f.read_text(encoding="utf-8-sig", errors="replace") for f in (pkg / "Rules").glob("*.xml")}
        files = sorted(n for n in srules if re.search(pat, n) and n not in cw_rules)
        prem = [n for n in files if '"SetPremium"' in srules[n]]
        print(f"  in force: {pkg.name}; {len(prem)} premium files, {len(files)} state-only files in all")
        texts = {n: srules[n] for n in files}
        recs, tables, ext, elems = set(), collections.Counter(), collections.Counter(), collections.Counter()
        for n, s in texts.items():
            recs |= set(re.findall(r'DataDefGroup="([^"]+)"', s))
            tables.update(set(re.findall(r'MatrixFromConstant="([^"]+)"', s)) - {"Pages"})
            ext.update(x for x in re.findall(r'RunRule[^>]*FileName="([^"]+)"', s)
                       if x != n.replace(".Rule.xml", "") and x != "MessageHelper")
            elems.update(re.findall(r"<rul:(\w+)", s))

        # 2 formula
        print("  premium files (operands of SetPremium; rounding):")
        for n in prem:
            body = set_premium(texts[n])
            ops = sorted(set(o.rsplit("/", 1)[-1] for o in re.findall(r'FromDataDef="([^"]+)"', body)))
            extra = [r for r in rule_names(texts[n]) if r not in STANDARD]
            print(f"    {short(n)}")
            print(f"        reads {', '.join(ops)[:220]}; rounds {re.findall(r'DecimalPlaces=\"(\d+)\"', body)}")
            if extra:
                print(f"        other rules ({len(extra)}): {', '.join(extra[:12])}{' ...' if len(extra) > 12 else ''}")

        # 3 tables
        print(f"  rate tables read directly ({len(tables)}):")
        for t in sorted(tables):
            sf = pkg / "Rate Tables" / f"{t}.RateTable.csv"
            cf = cw / "Rate Tables" / f"{t}.RateTable.csv"
            print(f"    {t:60s} {st} rows {rows(sf) if sf.exists() else 'not filed'}; "
                  f"CW rows {rows(cf) if cf.exists() else 'no CW table'}")
        print(f"  runs rules in other files: {dict(ext.most_common(8)) or '-'}")

        # 4 messages: state package + CW
        pages = form_pages(pkg) | form_pages(cw)
        forms = {nm for t, _, nm in pages if nm and re.search(pat, t)}
        wre = re.compile("|".join(re.escape(w) for w in words), re.I)
        sib = sorted({t for t, nmn, _ in pages if wre.search(nmn or "") and not re.search(pat, t)})
        if sib:
            print(f"  SIBLING NAMES (display name matches, table name does not): {'; '.join(short(x) for x in sib)[:500]}")
        msgs = collections.defaultdict(set)
        for where, pool in (("CW", cw_rules), (st, srules)):
            for fname, s in pool.items():
                for mm in re.finditer(r'<rul:Rule Name="([^"]+)"[^>]*DataDefGroup="([^"]+)"[^>]*>(.*?)</rul:Rule>', s, re.S):
                    name, grp, body = mm.groups()
                    if not re.search(r"Add(Error|Warning|Info)Message", body):
                        continue
                    text = "; ".join(re.findall(r'Param="Message">\s*<rul:Constant[^>]*>([^<]+)<', body))
                    by_record = grp in recs or any(r in body for r in recs)
                    by_form = any(f in text for f in forms) or bool(wre.search(text))
                    if by_record or by_form:
                        own = "own" if grp in recs else short(fname)[:26]
                        msgs[(text[:120] or name, own, "record" if by_record else "FORM/WORDING ONLY")].add(where)
        print(f"  message rules (forms {', '.join(sorted(forms)) or 'none'}), {st} package + CW: {len(msgs)}")
        for (text, own, how), ws in sorted(msgs.items()):
            print(f"    [{own:26s}] {'(' + how + ') ' if how != 'record' else ''}{text}  ({' '.join(sorted(ws))})")

        # 5 editions: every package of this state, all batches
        print(f"  {st} packages in every batch (SetPremium vs in force):")
        ed_diff = 0
        for sp in sorted(ISO_CF.glob(f"*/CF {st} *")):
            rd = sp / "Rules"
            if not rd.exists():
                continue
            row = []
            for n in prem:
                f = rd / n
                if not f.exists():
                    row.append(f"{short(n)[:30]}: NO FILE")
                    continue
                bb = set_premium(f.read_text(encoding="utf-8-sig", errors="replace"))
                if bb is None:
                    row.append(f"{short(n)[:30]}: no SetPremium")
                elif norm(bb) != norm(set_premium(texts[n])):
                    row.append(f"{short(n)[:30]}: different")
            if row:
                ed_diff += 1
            print(f"    {sp.parent.name}/{sp.name}: {'; '.join(row)[:200] if row else 'same'}")

        # 7 evidence, 8 attach
        try:
            xsd = rc1.xsd_for(b)
        except Exception as e:  # a state without its own schema falls back to CW's
            xsd = rc1.xsd_for(or_book)
            print(f"  (state XSD unavailable: {e}; using CW's)")
        prem_recs = {g for n in prem for g in re.findall(r'DataDefGroup="([^"]+)"', set_premium(texts[n]))}
        print("  records: attach point / fixtures / stored responses with a non-zero ISO premium")
        never = 0
        for r in sorted(recs):
            try:
                parent, table = xsd.attach(r.replace(P, "")) if r.startswith(P) else (None, None)
            except Exception:
                parent, table = ("?", None)
            fx = sum(1 for t in stc.values() if f'"{r}"' in t)
            print(f"    {short(r):80s} {str(parent).replace(P, '') or 'policy'}{' []' if table else ''} / {fx} / {replay[r]}")
            if r in prem_recs and not replay[r]:
                never += 1
        switches = [short(n) for n, s in texts.items() if "SetCoverageOnPolicyIndicator" in s
                    or re.search(r'ToDataDef="Premium">0', s.replace(" ", ""))]
        print(f"  premium records ISO has never priced: {never}; on-switch files: {len(switches)}")

        # 9 engine
        missing = sorted(e for e in elems if e not in registry and e not in STRUCTURAL)
        dates = sorted(e for e in elems if e in {"DateDifference", "DateAdd", "DateCreate", "DatePart"})
        print(f"  engine: rul: elements not registered: {missing or 'none'}; date nodes {dates or 'none'}; "
              f"Power {elems.get('Power', 0)}")
        summary.append((fam, st, len(prem), len(tables), len(msgs), ed_diff, never))

    print("\n" + "=" * 90 + "\nSUMMARY")
    print(f"  {'family':55s} {'st':3s} {'prem':>4s} {'tabs':>4s} {'msgs':>4s} {'eds!':>4s} {'never':>5s}")
    for r in summary:
        print(f"  {r[0]:55s} {r[1]:3s} {r[2]:4d} {r[3]:4d} {r[4]:4d} {r[5]:4d} {r[6]:5d}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
