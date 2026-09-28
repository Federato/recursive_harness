#!/usr/bin/env python3
"""Chunk 22 opening census -- multi-location: value reporting and special coinsurance.

166_ grouped two countrywide families, the Value Reporting Form (four reporting
forms and a general-information record) and Additional Locations Special
Coinsurance. Same nine checks as 902_ (chunk 21): messages in every rule file,
SetPremium per in-force edition, form numbers from the package's Form Pages
table, sibling names flagged. Plus a tenth, because this is the first chunk
whose values reach coverages already built:

  10  The multi-location trail: every rule file (CW and the 46 in-force state
      packages) that WRITES or READS a multi-location average-rate field
      (MLAR / MultiLoc) or runs the additional-locations reset, with the
      datadef groups involved. Chunk 14 (C14-14) found MultiLocAvgRates
      "Not Used" without the form; C14-08 met the reset but did not test it.

  1  Population: premium files per family, earthquake riders included (166_'s
     rule: an EQ rider belongs to its parent coverage), and the state-only files
     in every batch.
  2  The premium formula per file: its operands, the rate tables it reads
     directly, the rules it runs in other files, rounding.
  3  Rate tables: row counts countrywide, header-only tables, which states file
     their own rows.
  4  Messages: every message rule in ANY rule file (CW and the 46 in-force state
     packages) that names a family record, form or wording.
  5  Editions: each premium file's SetPremium in every countrywide parent a
     state stands on (2026 V01, 2023 V02 / V03 / V04), formula diffed.
  6  State layer: which of the 46 in-force packages rewrite a family file, and
     which rules.
  7  ISO evidence: fixtures carrying each record, stored responses with a
     non-zero premium on it, and so which records ISO has NEVER priced.
  8  Attach points (DataDef XSD) and on-switches (rules that force Premium 0).
  9  Engine readiness: rul: elements not registered; date / Power arithmetic.

    python scripts/cf/903_chunk22_census.py

Always exits 0 -- a census, not a test.
"""
from __future__ import annotations

import collections
import csv
import json
import re
import sys
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
EDITIONS = {"CW 2026 V01": ISO_CF / "20260601" / "CFCW20260601V01",
            "CW 2023 V02": ISO_CF / "20230801v2" / "CF CW 20230801 V02",
            "CW 2023 V03": ISO_CF / "20230801v3" / "CF CW 20230801 V03",
            "CW 2023 V04": ISO_CF / "20230801v4" / "CF CW 20230801 V04"}

FAMILIES = [
    ("Value Reporting Form", r"ValueReportingForm"),
    ("Additional Locations Special Coinsurance", r"AdditionalLocationsSpecialCoinsurance"),
]
#: the family's own wording, searched in every message text and every Form Pages display name
WORDS = {"Value Reporting Form": ["Value Reporting", "Reporting Form", "Multiple Location", "Multi-Location",
                                  "Multiple Locations"],
         "Additional Locations Special Coinsurance": ["Additional Locations", "Special Coinsurance"]}
#: MA's heating-oil files are chunk 23's, as in 166_
EXCLUDE = re.compile(r"HeatingOil")
#: check 10: the multi-location fields and the reset
MLAR = re.compile(r"MLAR|MultiLoc|MultipleLoc|ResetPrsnlPropPremiumForAdditionalLocations", re.I)


def mlar_trail(pools):
    """(package, file) -> (fields written, fields read, rules named) for the multi-location fields."""
    out = {}
    for j, fname, text in pools:
        w = sorted(set(x.rsplit("/", 1)[-1] for x in re.findall(r'ToDataDef="([^"]+)"', text) if MLAR.search(x)))
        r = sorted(set(x.rsplit("/", 1)[-1] for x in re.findall(r'FromDataDef="([^"]+)"', text) if MLAR.search(x)))
        rn = sorted(set(x for x in re.findall(r'<rul:Rule Name="([^"]+)"', text) if MLAR.search(x)))
        if w or r or rn:
            out[(j, fname)] = (w, r, rn)
    return out


def form_pages(pkgs):
    """(TableName, display Name, form number 'CP nn nn') from every package's Form Pages table."""
    out = set()
    for pkg in pkgs:
        f = pkg / "Form Pages" / "Pages.FormPage.csv"
        if not f.exists():
            continue
        with open(f, encoding="utf-8-sig") as h:
            for r in csv.DictReader(h):
                num = re.match(r"((?:CP|IL) \d\d \d\d)", r.get("Number") or "")
                out.add((r["TableName"], r["Name"], num.group(1) if num else None, r["StateCode"]))
    return out


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


def main():
    or_book = book_for("OR", ASOF)
    cw = or_book.parent.package.content
    cw_rules = {f.name: f.read_text(encoding="utf-8-sig") for f in (cw / "Rules").glob("*.xml")}
    registry = set(nodes.EVAL)
    books = {j: book_for(j, ASOF) for j in s18.STATES}
    state_rules = {j: {f.name: f for f in (b.state.package.content / "Rules").glob("*.xml")}
                   for j, b in books.items() if (b.state.package.content / "Rules").exists()}
    ed_rules = {k: {f.name: f for f in (v / "Rules").glob("*.xml")} for k, v in EDITIONS.items()}
    stc = {p.stem: p.read_text(encoding="utf-8-sig", errors="replace") for p in ISO_CF.rglob("STC/*.json")}
    xsd = rc1.xsd_for(or_book)
    pages = form_pages([cw] + [b.state.package.content for b in books.values()])

    # stored ISO responses: non-zero premium by record, and the forms seen
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

    # every rule file anywhere we will search for messages: CW + in-force state packages
    msg_pool = [("CW", f.name, cw_rules[f.name]) for f in (cw / "Rules").glob("*.xml")]
    for j, fs in state_rules.items():
        for n, f in fs.items():
            msg_pool.append((j, n, f.read_text(encoding="utf-8-sig", errors="replace")))

    print(f"{or_book}\n{len(cw_rules)} CW rule files; {len(books)} states (PR excluded); "
          f"{len(stc)} CF STC payloads; {sum(1 for _ in RES.glob('chunk13_fixture_*_response.json'))} stored ISO responses\n")

    summary = []
    import time
    t0 = time.monotonic()
    for i, (fam, pat) in enumerate(FAMILIES, 1):
        m, sec = divmod(int(time.monotonic() - t0), 60)
        print(f"[{i}/{len(FAMILIES)}  {m}m{sec:02d}s] {fam}", flush=True)
        print("=" * 90)
        cw_files = sorted(n for n, s in cw_rules.items() if re.search(pat, n) and not EXCLUDE.search(n))
        prem = [n for n in cw_files if '"SetPremium"' in cw_rules[n]]
        # state-only files, every batch
        only = collections.defaultdict(set)
        for pkg in sorted(ISO_CF.glob("*/CF ?? *")):
            st = pkg.name.split()[1]
            if st == "PR" or not (pkg / "Rules").exists():
                continue
            for f in (pkg / "Rules").glob("*.xml"):
                if f.name in cw_rules or not re.search(pat, f.name) or EXCLUDE.search(f.name):
                    continue
                s = f.read_text(encoding="utf-8-sig", errors="replace")
                only[f.name].add((st, pkg.name.split()[2], '"SetPremium"' in s))
        print(f"{fam}: {len(prem)} CW premium files ({len(cw_files)} CW files in all); "
              f"{len(only)} state-only files")
        for n, v in sorted(only.items()):
            sts = sorted({s for s, _, _ in v})
            pr = any(p for _, _, p in v)
            print(f"    state-only {n.replace(P, '').replace('Rules.Rule.xml', '')}: {' '.join(sts)}"
                  f"{'' if pr else '  (no SetPremium)'}")

        texts = {n: cw_rules[n] for n in cw_files}
        # state-only in-force texts (for Mine Subsidence the whole family is state-only)
        for j, fs in state_rules.items():
            for n, f in fs.items():
                if n in only and n not in texts:
                    texts[n] = f.read_text(encoding="utf-8-sig", errors="replace")
        recs = set()
        tables = collections.Counter()
        ext = collections.Counter()
        elems = collections.Counter()
        for n, s in texts.items():
            recs |= set(re.findall(r'DataDefGroup="([^"]+)"', s))
            tables.update(set(re.findall(r'MatrixFromConstant="([^"]+)"', s)) - {"Pages"})
            stem = n.replace(".Rule.xml", "")
            ext.update(x for x in re.findall(r'RunRule[^>]*FileName="([^"]+)"', s)
                       if x != stem and x != "MessageHelper")
            elems.update(re.findall(r"<rul:(\w+)", s))

        # 2 formula per premium file
        print("  premium files (operands of SetPremium; rounding):")
        for n in sorted(texts):
            body = set_premium(texts[n])
            if not body:
                continue
            ops = sorted(set(o.rsplit("/", 1)[-1] for o in re.findall(r'FromDataDef="([^"]+)"', body)))
            dps = re.findall(r'DecimalPlaces="(\d+)"', body)
            extra = [r for r in rule_names(texts[n]) if r not in STANDARD]
            print(f"    {n.replace(P, '').replace('Rules.Rule.xml', '')}")
            print(f"        reads {', '.join(ops)[:200]}; rounds {dps}")
            if extra:
                print(f"        other rules ({len(extra)}): {', '.join(extra[:10])}{' ...' if len(extra) > 10 else ''}")

        # 3 tables
        print(f"  rate tables read directly ({len(tables)}):")
        for t in sorted(tables):
            f = cw / "Rate Tables" / f"{t}.RateTable.csv"
            n = rows(f) if f.exists() else None
            filers = sorted(j for j, b in books.items()
                            if (b.state.package.content / "Rate Tables" / f"{t}.RateTable.csv").exists())
            print(f"    {t:60s} CW rows {n if n is not None else 'NOT FILED'}; state-filed in {len(filers)}"
                  f"{': ' + ' '.join(filers[:12]) if filers else ''}")
        print(f"  runs rules in other files: {dict(ext.most_common(8)) or '-'}")

        # the family's form numbers, from its own files' ErcFormNumber constants and lookups, and its wording
        forms = set(f for t in texts.values() for f in re.findall(r"\b(?:CP|IL) \d\d \d\d\b", t))
        forms |= {n for t, _, n, _ in pages if n and re.search(pat, t) and not EXCLUDE.search(t)}
        # sibling names: a Form Pages row with the family's wording whose table name the pattern misses
        wre = re.compile("|".join(re.escape(w) for w in WORDS[fam]), re.I)
        sib = sorted({(t, st) for t, nm, _, st in pages if wre.search(nm or "") and not re.search(pat, t)})
        if sib:
            listed = "; ".join(t.replace(P, "") + " [" + st + "]" for t, st in sib)
            print(f"  SIBLING NAMES (display name matches, table name does not): {listed[:600]}")
        words = re.compile("|".join(re.escape(w) for w in WORDS[fam]), re.I)
        # 4 messages anywhere
        msgs = collections.defaultdict(set)
        for j, fname, s in msg_pool:
            for m in re.finditer(r'<rul:Rule Name="([^"]+)"[^>]*DataDefGroup="([^"]+)"[^>]*>(.*?)</rul:Rule>', s, re.S):
                name, grp, body = m.groups()
                if "AddErrorMessage" not in body and "AddWarningMessage" not in body and "AddInfoMessage" not in body:
                    continue
                text = re.findall(r'Param="Message">\s*<rul:Constant[^>]*>([^<]+)<', body)
                joined = "; ".join(text)
                by_record = grp in recs or any(r in body for r in recs)
                # chunk 17's lesson: a message can name the FORM or the family's wording and not
                # the record (4 Watercraft messages named the waterfront input): search those too
                by_form = any(f in joined for f in forms) or bool(words.search(joined))
                if by_record or by_form:
                    own = "own" if grp in recs else fname.replace(P, "").replace("Rules.Rule.xml", "")
                    how = "record" if by_record else "FORM/WORDING ONLY"
                    msgs[(name, joined[:110], own, how)].add(j)
        print(f"  message rules naming a family record, its forms ({', '.join(sorted(forms)) or 'none found'}) "
              f"or its wording, any file (CW + 46 states): {len(msgs)}")
        for (name, text, own, how), js in sorted(msgs.items()):
            print(f"    [{own[:26]:26s}] {'(' + how + ') ' if how != 'record' else ''}{text or name}  "
                  f"({' '.join(sorted(js)) if len(js) < 8 else str(len(js)) + ' packages'})")

        # 5 editions
        print("  per edition (SetPremium present / formula vs 2026):")
        ed_diff = 0
        for n in sorted(prem):
            base = norm(set_premium(cw_rules[n]))
            row = []
            for k, fs in ed_rules.items():
                if k == "CW 2026 V01":
                    continue
                f = fs.get(n)
                if f is None:
                    row.append(f"{k}: NO FILE")
                    ed_diff += 1
                    continue
                b = set_premium(f.read_text(encoding="utf-8-sig", errors="replace"))
                if b is None:
                    row.append(f"{k}: no SetPremium")
                    ed_diff += 1
                elif norm(b) != base:
                    row.append(f"{k}: different formula")
                    ed_diff += 1
            if row:
                print(f"    {n.replace(P, '').replace('Rules.Rule.xml', '')}: {'; '.join(row)}")
        if not ed_diff:
            print("    identical in all four editions")

        # 6 state layer
        rew = collections.defaultdict(list)
        for j, fs in state_rules.items():
            for n in texts:
                if n in fs and n in cw_rules:
                    s = fs[n].read_text(encoding="utf-8-sig", errors="replace")
                    rew[j].append(f"{n.replace(P, '').replace('Rules.Rule.xml', '')[:40]}"
                                  f"[{','.join(r for r in rule_names(s) if r != 'InitializeRuleSet')[:70]}]")
        print(f"  states rewriting a family file: {len(rew)}")
        for j, v in sorted(rew.items()):
            print(f"    {j}: {'; '.join(v)[:230]}")

        # 7 evidence, 8 attach
        # the records that carry a premium: each premium file's own group (state-only files included)
        prem_recs = {g for n, t in texts.items() if set_premium(t)
                     for g in re.findall(r'DataDefGroup="([^"]+)"', set_premium(t))}
        print("  records: attach point / fixtures / stored responses with a non-zero ISO premium")
        never = []
        for r in sorted(recs):
            parent, table = xsd.attach(r.replace(P, "")) if r.startswith(P) else (None, None)
            fx = sum(1 for t in stc.values() if f'"{r}"' in t)
            print(f"    {r.replace(P, ''):75s} {str(parent).replace(P, '') or 'policy'}{' []' if table else ''}"
                  f" / {fx} / {replay[r]}")
            if not replay[r] and r in prem_recs:
                never.append(r)
        switches = sorted({n for n, s in texts.items() if re.search(r'ToDataDef="Premium">0', s.replace(" ", ""))
                           or "SetCoverageOnPolicyIndicator" in s})
        print(f"  premium records ISO has never priced: {len(never)}")
        print(f"  files with an on-switch / forced $0: {[x.replace(P, '').replace('Rules.Rule.xml', '') for x in switches] or '-'}")

        # 9 engine
        missing = sorted(e for e in elems if e not in registry and e not in STRUCTURAL)
        dates = sorted(e for e in elems if e in {"DateDifference", "DateAdd", "DateCreate", "DatePart"})
        print(f"  engine: rul: elements not registered: {missing or 'none'}; date nodes {dates or 'none'}; "
              f"Power {elems.get('Power', 0)}")
        summary.append((fam, len(prem_recs), len(tables),
                        len(msgs), len(rew), ed_diff, len(never), sum(replay[r] for r in recs)))

    # 10 the multi-location trail, across every rule file
    print("\n" + "=" * 90 + "\nMULTI-LOCATION TRAIL (check 10): files writing / reading MLAR / MultiLoc fields")
    trail = mlar_trail(msg_pool)
    by_file = collections.defaultdict(list)
    for (j, fname), v in trail.items():
        by_file[fname].append((j, v))
    for fname, rows_ in sorted(by_file.items()):
        cw_row = [v for j, v in rows_ if j == "CW"]
        states = sorted(j for j, _ in rows_ if j != "CW")
        w, r, rn = cw_row[0] if cw_row else rows_[0][1]
        print(f"  {fname.replace(P, '').replace('Rules.Rule.xml', '')}")
        print(f"      writes {', '.join(w) or '-'}; reads {', '.join(r)[:180] or '-'}; rules {', '.join(rn)[:150] or '-'}")
        print(f"      {'CW' if cw_row else 'state-only'}{'; states rewriting: ' + ' '.join(states) if states else ''}")
    print("\n" + "=" * 90 + "\nSUMMARY")
    print(f"  {'family':34s} {'prem':>4s} {'tabs':>4s} {'msgs':>4s} {'st':>3s} {'ed':>3s} {'never':>5s} {'repl':>5s}")
    for r in summary:
        print(f"  {r[0]:34s} {r[1]:4d} {r[2]:4d} {r[3]:4d} {r[4]:3d} {r[5]:3d} {r[6]:5d} {r[7]:5d}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
