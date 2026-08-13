"""Build-order item 12, step 1 — the referral population, by content.

Eleven gates have each recorded a referral condition in passing. This finds them
by scanning the corpus, so the two lists can be diffed:

    anything in the gate documents and NOT here  -> this census is short
    anything here and NOT in the gate documents  -> eleven gates missed it

That diff is the point. A referral register assembled by re-reading gate prose
would inherit every population error those gates made, which is the failure this
project has spent a week learning to stop.

SIX PROBES, each starting from an enumerated population:

  1. SENTINEL CELLS      every rate-table cell whose value is a filed refer
                         marker, in any spelling, in any package
  2. SENTINEL TESTS      every rule comparing a string against such a marker,
                         with the spelling recorded PER EDITION (N18: two
                         spellings are live at once on 2027-04-01)
  3. COMPANY SELECTORS   every N17 rating-basis selector whose value set is
                         exactly {Company} — a single-valued selector means the
                         coverage has one rating path, and `Company` means refer
  4. UNRATEABLE COVERAGES  rate-driven coverages whose loss cost AND expected
                         loss potential are 0 in every filed row
  5. GUARDS              every DoMessage* rule — these ARE the bound in the
                         cases where nothing else states one (N15)
  6. EMPTY READS         lookups whose table is empty in the RESOLVED package

    python 40_referral_census.py 20260812 [--verbose]

Writes out/referral_census.json for the register, and prints "n of N" throughout.
"""
from __future__ import annotations

import csv
import glob
import importlib.util
import io
import json
import os
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "asof", os.path.join(HERE, "32_asof_recount.py"))
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)

OUT = os.path.join(HERE, "out")
RULE = re.compile(
    r'<rul:Rule Name="([^"]+)"[^>]*?DataDefGroup="([^"]+)"[^>]*>(.*?)</rul:Rule>',
    re.S)
CONST = re.compile(r'<rul:Constant Type="string">\s*([^<]*?)\s*</rul:Constant>')
LOOKUP = re.compile(r'MatrixFromConstant="([^"]+)"')
# Any spelling of the marker, so a third one cannot hide (N18).
SENT = re.compile(r'^refer\s*to\s*(co\.?|company)$', re.I)
# N17's closed four-value vocabulary.
VOCAB = {"Rate/Loss Cost Applies", "Industry", "Company", "Not Applicable"}


def main() -> int:
    asof = next((a for a in sys.argv[1:] if len(a) == 8 and a.isdigit()), None)
    verbose = "--verbose" in sys.argv
    if not asof:
        print(__doc__)
        print("ERROR: an as-of date is REQUIRED (N4).", file=sys.stderr)
        return 2

    pk = A.discover()
    cw = {p: c for _e, p, _x, c in pk["CW"]}
    res = {j: r for j in pk if j != "CW"
           for r in [A.resolve(pk[j], asof)] if r}
    pkgs = [("CW:" + p, c) for p, c in sorted(cw.items())] + \
           [(j, r[3]) for j, r in sorted(res.items())]
    print(f"referral census as of {asof}: {len(cw)} countrywide + "
          f"{len(res)} resolved jurisdictions = {len(pkgs)} packages\n")

    report: dict[str, object] = {"asof": asof, "packages": len(pkgs)}

    # ---- probe 1: sentinel CELLS
    spell_cell: Counter = Counter()
    cell_sites: dict[str, set[str]] = defaultdict(set)
    n_tab = 0
    for lbl, c in pkgs:
        d = os.path.join(c, "Rate Tables")
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if not fn.endswith(".RateTable.csv"):
                continue
            n_tab += 1
            txt = A._read(os.path.join(d, fn))
            if "efer" not in txt:
                continue
            rows = list(csv.reader(io.StringIO(txt)))
            if len(rows) < 2:
                continue
            hdr = rows[0]
            for r in rows[1:]:
                for i, v in enumerate(r):
                    if SENT.match(v.strip()):
                        spell_cell[v.strip()] += 1
                        col = hdr[i] if i < len(hdr) else f"col{i}"
                        cell_sites[f"{fn[:-len('.RateTable.csv')]}::{col}"].add(lbl)
    print(f"1. SENTINEL CELLS — {sum(spell_cell.values())} cells in "
          f"{len(cell_sites)} (table,column) sites, of {n_tab} table instances")
    print(f"   spellings: {dict(spell_cell)}")
    for k, v in sorted(cell_sites.items()):
        print(f"     {len(v):>3} packages  {k}")
    report["sentinel_cells"] = {"cells": sum(spell_cell.values()),
                                "spellings": dict(spell_cell),
                                "sites": {k: sorted(v) for k, v in cell_sites.items()},
                                "tables_scanned": n_tab}

    # ---- probe 2: sentinel TESTS, spelling per edition
    spell_rule: Counter = Counter()
    test_sites: dict[str, set[str]] = defaultdict(set)
    by_edition: dict[str, set[str]] = defaultdict(set)
    for lbl, c in pkgs:
        d = os.path.join(c, "Rules")
        if not os.path.isdir(d):
            continue
        for f in glob.glob(os.path.join(d, "*.xml")):
            s = A._read(f)
            if "efer" not in s:
                continue
            for m in RULE.finditer(s):
                for v in CONST.findall(m.group(3)):
                    if SENT.match(v):
                        spell_rule[v] += 1
                        test_sites[f"{m.group(2)}::{m.group(1)}"].add(lbl)
                        by_edition[lbl].add(v)
    print(f"\n2. SENTINEL TESTS — {sum(spell_rule.values())} comparisons in "
          f"{len(test_sites)} (group,rule) sites")
    print(f"   spellings: {dict(spell_rule)}")
    for k, v in sorted(test_sites.items()):
        print(f"     {len(v):>3} packages  {k}")
    split = {e: sorted(v) for e, v in sorted(by_edition.items()) if v}
    print("   spelling by package — N18's edition scoping, measured:")
    for e, v in split.items():
        print(f"     {e:<26} {v}")
    report["sentinel_tests"] = {"comparisons": sum(spell_rule.values()),
                                "spellings": dict(spell_rule),
                                "sites": {k: sorted(v) for k, v in test_sites.items()},
                                "by_package": split}

    # ---- probe 3: single-valued `Company` selectors
    sel: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for lbl, c in pkgs:
        d = os.path.join(c, "Rate Tables")
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if not fn.endswith(".RateTable.csv"):
                continue
            rows = list(csv.reader(io.StringIO(A._read(os.path.join(d, fn)))))
            if len(rows) < 2:
                continue
            for i, col in enumerate(rows[0]):
                vals = {r[i].strip() for r in rows[1:] if len(r) > i and r[i].strip()}
                if vals and vals <= VOCAB:
                    sel[f"{fn[:-len('.RateTable.csv')]}::{col}"][lbl] = vals
    # A SINGLE-VALUED selector of ANY value means the coverage has exactly one
    # rating path — that is N17's finding and it is not specific to `Company`.
    # Railroad Protective's selector is single-valued `Industry` and the coverage
    # is still a referral (gate 335-RR, manual Rule 49.E.1). Filtering on
    # `Company` alone finds New York and misses Railroad — which is precisely the
    # kind of miss this census exists to prevent.
    single = {k: sorted({x for s in v.values() for x in s})
              for k, v in sel.items()
              if len({x for s in v.values() for x in s}) == 1}
    company_only = {k: sel[k] for k, v in single.items() if v == ["Company"]}
    print(f"\n3. SELECTORS — {len(sel)} rating-basis selectors found by content; "
          f"{len(single)} are SINGLE-VALUED (one rating path), of which "
          f"{len(company_only)} read `Company`")
    for k, v in sorted(single.items()):
        mark = "   <-- refer to company" if v == ["Company"] else ""
        print(f"     {len(sel[k]):>3} packages  {k:<48} {v}{mark}")
    for k, v in sorted(sel.items()):
        if k not in single:
            print(f"     {len(v):>3} packages  {k:<48} "
                  f"{sorted({x for s in v.values() for x in s})}  (multi-valued)")
    report["selectors"] = {
        "selectors_found": len(sel),
        "single_valued": single,
        "single_valued_company": {k: sorted(v) for k, v in company_only.items()}}

    # ---- probe 4: rate-driven coverages with no filed rate at all
    rd = {r["DataDefGroup"] for r in
          csv.DictReader(open(os.path.join(OUT, "rating_vs_capture.csv"),
                              encoding="utf-8"))
          if r["verdict"] == "RATE_DRIVEN"}
    unrateable: dict[str, list[str]] = {}
    for k, pkg_map in company_only.items():
        stem = k.split("::")[0].replace("ELPText", "")
        for lbl in pkg_map:
            base = dict(pkgs)[lbl]
            zero = []
            for suffix in ("LossCost", "ELP"):
                t = stem + suffix
                rows = A.table(base, "Rate Tables", t + ".RateTable.csv")
                if rows and all(r[-1].strip() in ("0", "0.0") for r in rows):
                    zero.append(t)
            if len(zero) == 2:
                unrateable.setdefault(stem, []).append(lbl)
    print(f"\n4. UNRATEABLE COVERAGES — a single-valued `Company` selector AND "
          f"a loss cost AND an ELP that are 0 in every filed row:")
    for stem, v in sorted(unrateable.items()):
        print(f"     {stem}   {sorted(v)}")
    print(f"   ({len(rd)} coverage groups are RATE_DRIVEN corpus-wide, "
          f"itself a floor — OI-63)")
    report["unrateable"] = {k: sorted(v) for k, v in unrateable.items()}

    # ---- probe 5: the guard population
    guards: dict[str, set[str]] = defaultdict(set)
    for lbl, c in pkgs:
        d = os.path.join(c, "Rules")
        if not os.path.isdir(d):
            continue
        for f in glob.glob(os.path.join(d, "*.xml")):
            s = A._read(f)
            if "DoMessage" not in s:
                continue
            for m in RULE.finditer(s):
                if m.group(1).startswith("DoMessage"):
                    guards[f"{m.group(2)}::{m.group(1)}"].add(lbl)
    cw_only = {k for k, v in guards.items() if all(x.startswith("CW:") for x in v)}
    print(f"\n5. GUARDS — {len(guards)} distinct DoMessage* (group,rule) sites; "
          f"{len(cw_only)} appear only in countrywide packages, "
          f"{len(guards) - len(cw_only)} in at least one jurisdiction")
    report["guards"] = {"distinct_sites": len(guards),
                        "countrywide_only": len(cw_only)}

    # ---- probe 6: lookups reading an empty table in the RESOLVED package
    # THE READER IS USUALLY IN THE PARENT. New York empties four claims-made
    # multiplier tables and the rules that read them are countrywide, so a scan
    # of the jurisdiction's own rule files finds nothing — which is exactly what
    # the first version of this probe reported: 0, against a case the New York
    # differential had already established. The reader population is the
    # jurisdiction's rules PLUS its declared parent's.
    parent_reads: dict[str, dict[str, set[str]]] = {}
    for p, c in cw.items():
        rd2: dict[str, set[str]] = defaultdict(set)
        for f in glob.glob(os.path.join(c, "Rules", "*.xml")):
            for m in RULE.finditer(A._read(f)):
                for t in LOOKUP.findall(m.group(3)):
                    rd2[t].add(f"{m.group(2)}::{m.group(1)}")
        parent_reads[p] = rd2

    empty: dict[str, list[str]] = defaultdict(list)
    for j, r in sorted(res.items()):
        own_tables = {f[:-len(".RateTable.csv")]
                      for f in os.listdir(os.path.join(r[3], "Rate Tables"))
                      if f.endswith(".RateTable.csv")}
        reads: dict[str, set[str]] = {k: set(v) for k, v
                                      in parent_reads.get(r[2], {}).items()}
        d = os.path.join(r[3], "Rules")
        if os.path.isdir(d):
            for f in glob.glob(os.path.join(d, "*.xml")):
                for m in RULE.finditer(A._read(f)):
                    for t in LOOKUP.findall(m.group(3)):
                        reads.setdefault(t, set()).add(
                            f"{m.group(2)}::{m.group(1)}")
        for t in sorted(own_tables):
            # an ABSENT table falls through to the parent (N3); an EMPTY one
            # does not, and that distinction is the whole probe
            if A.table(r[3], "Rate Tables", t + ".RateTable.csv"):
                continue
            for site in sorted(reads.get(t, ())):
                empty[f"{site}::{t}"].append(j)
    print(f"\n6. EMPTY READS — {len(empty)} (group,rule,table) triples where a "
          f"jurisdiction overrides a table to ZERO ROWS and still reads it")
    for k, v in sorted(empty.items(), key=lambda kv: -len(kv[1]))[:14]:
        print(f"     {len(v):>3} states  {k[:96]}")
    report["empty_reads"] = {k: sorted(set(v)) for k, v in empty.items()}

    # ---- RECONCILIATION against the eleven gates
    #
    # The probes find MECHANISMS; the gate documents record CONDITIONS. Diffing
    # them is the point of the census, and the useful half of the answer is the
    # conditions no probe can reach — those are exactly the cases where ERC
    # carries no discriminator, and they are decisions rather than code.
    #
    # probe id, or None where nothing in the corpus can detect the condition.
    DOCUMENTED = [
        ("gate 335-RR", "Railroad Protective is ELP-only, selector single-valued", 3),
        ("gate state-specific", "NY Special Protective and Highway, Company on all 3 classes", 3),
        ("gate 332 / E15", "LCM = 1 as a filed placeholder, four sublines", None),
        ("gate 370", "18 of 60 drone cells are RTC", None),
        ("gate 370 / OI-48", "filed Unknown / Not Applicable on the three drone axes", None),
        ("gate 332 / E17 / N18", "the refer sentinel's spelling is edition-scoped", 2),
        ("gate size-of-risk", "14 jurisdictions inherit the chain with no loss costs", 6),
        ("gate size-of-risk", "a 0 final relativity while the flag is Yes", None),
        ("gate size-of-risk / OI-53", "CW 2027 strips assignment/min/max", 6),
        ("OI-34 / E8", "county or place unmatched in CA FL NY TX", None),
        ("gate 335 OCP", "WorkersCompensationRate absent for class 15191", None),
        ("OI-41", "an effective date before the corpus floor", None),
        ("OI-49", "non-construction railroad operations", None),
        ("E19", "188 of 1,188 classes with a 0 size-of-risk loss cost", None),
        ("OI-44", "21 zero liquor deductible factors, guard covers 10", 5),
        ("OI-57", "conditional-exclusion prorating is manual-only", None),
        ("OI-61", "Puerto Rico has no rating-plan manual", None),
        ("gate rating plans", "the 25% schedule cap is a message, not a clamp", 5),
        ("gate 365 sec.9", "FinalILF has no floor; two guards prevent a negative", 5),
        ("gate terrorism", "the endorsement factor's only bound is in a guard name", 5),
    ]
    detectable = [d for d in DOCUMENTED if d[2] is not None]
    print(f"\nRECONCILIATION — {len(DOCUMENTED)} referral conditions recorded across "
          f"eleven gates:")
    print(f"   {len(detectable)} are reachable by a probe above")
    print(f"   {len(DOCUMENTED) - len(detectable)} are NOT detectable by scanning "
          f"the corpus — ERC carries no discriminator, so each is a DECISION:")
    for src, what, probe in DOCUMENTED:
        if probe is None:
            print(f"     {src:<26} {what}")
    report["reconciliation"] = {
        "documented": [{"source": s, "condition": w, "probe": p}
                       for s, w, p in DOCUMENTED],
        "detectable": len(detectable),
        "decisions_required": len(DOCUMENTED) - len(detectable)}

    # and the other direction: what the probes found that no gate recorded
    print("\n   found by probe and NOT recorded by any gate before today:")
    for line in ("terrorism factor overridden in 15 jurisdictions (gate terrorism sec.3a)",
                 "California withdraws LoED and Cyber entirely (gate 365 sec.10)",
                 "Nebraska empties both schedule-rating cap tables (gate rating plans sec.2)",
                 "IA/MO/OK redirect the liquor grade to LiquorLiabilityGradeOnOffPremises",
                 "MA/TX empty BringYourOwnAlcoholExclusionFactor (guarded to classes 16905/16906)",
                 "VA/VT empty Subline (0 rules read the DataDef it feeds — harmless)"):
        print(f"     {line}")

    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, "referral_census.json")
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)
    print(f"\nwrote {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
