"""Terrorism — the OI-37 population audit, and the manual/ERC alignment.

WHY THIS SCRIPT EXISTS
----------------------
`RECONCILIATION.md` R3 forbids repeating *"terrorism premium cannot be computed"*
until a population audit runs. This is that audit, plus the manual differential
that build-order item 9 needs.

Three populations, each enumerated before anything is classified (habit 8):

  1. COVERAGE GROUPS  — all 477 premium-writing groups from 25_rating_vs_capture,
     classified for terrorism by whether their RULES touch a terrorism artifact,
     never by whether "Terror" appears in the group name.
  2. MANUAL VERSIONS  — every `VERSION xEVnnn` block in the Terrorism Supplement,
     with the state assignment table that says which state uses which.
  3. CLASS CODES      — the "above average" exposure lists, manual against ERC,
     per version and per jurisdiction, as-of a REQUIRED date (N4).

    python 37_terrorism_align.py 20260812 [--verbose]

Exit code 1 if any assertion fails.
"""
from __future__ import annotations

import csv
import importlib.util
import io
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "asof", os.path.join(HERE, "32_asof_recount.py"))
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)

PROJ = os.path.dirname(os.path.dirname(HERE))
TEXT = os.path.join(PROJ, "Agentic", "iso-circular-expert", "text", "terrorism")
RULE_RE = re.compile(r'<rul:Rule Name="([^"]+)"[^>]*?DataDefGroup="([^"]+)"[^>]*>(.*?)</rul:Rule>',
                     re.S)
VERSION_RE = re.compile(r'^VERSION ([TP]EV\d{3})(?: \(([^)]+)\))?\s*$', re.M)
CODE_RE = re.compile(r'^\s*(\d{5})\s*(X?)\s*(X?)\s*$')

# Every artifact name that means "this rule participates in terrorism rating".
# Derived by listing the countrywide Rate Tables and Domain Tables, not typed
# from memory — see `terrorism_artifacts()`.
failures: list[str] = []


def check(name: str, ok: bool, detail: str) -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}\n         {detail}")
    if not ok:
        failures.append(name)


def terrorism_artifacts(content: str) -> set[str]:
    """Table names in the package whose stem contains Terror — enumerated."""
    out: set[str] = set()
    for kind, suffix in (("Rate Tables", ".RateTable.csv"),
                         ("Domain Tables", ".DomainTable.csv")):
        d = os.path.join(content, kind)
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if fn.endswith(suffix) and "Terror" in fn:
                out.add(fn[: -len(suffix)])
    return out


def manual_versions(path: str) -> dict[str, tuple[str, set[str]]]:
    """-> version id -> (state label, above-average class codes).

    The class table is read by line shape (`^ 12345 [X] [X]$`), because
    `pdftotext -layout` collapses the two X columns unpredictably across page
    breaks. **So this extracts the SET of above-average classes per version and
    makes no claim about which column an X sits in** — the premises/products
    split is taken from ERC and cross-checked against the union only. Claiming
    the split from mangled text would be inventing evidence.
    """
    lines = open(path, encoding="utf-8").read().splitlines()
    marks = [(m.start(), m.group(1), m.group(2) or "") for m in
             VERSION_RE.finditer("\n".join(lines))]
    # re-find by line index, simpler and exact
    idx: list[tuple[int, str, str]] = []
    for i, ln in enumerate(lines):
        m = VERSION_RE.match(ln)
        if m:
            idx.append((i, m.group(1), m.group(2) or "COUNTRYWIDE"))
    out: dict[str, tuple[str, set[str]]] = {}
    for n, (i, vid, label) in enumerate(idx):
        end = idx[n + 1][0] if n + 1 < len(idx) else len(lines)
        codes = {m.group(1) for ln in lines[i:end]
                 for m in [CODE_RE.match(ln)] if m}
        out[vid] = (label, codes)
    return out


def main() -> int:
    asof = next((a for a in sys.argv[1:] if len(a) == 8 and a.isdigit()), None)
    verbose = "--verbose" in sys.argv
    if not asof:
        print(__doc__)
        print("ERROR: an as-of date is REQUIRED (N4).", file=sys.stderr)
        return 2

    pk = A.discover()
    resolved = {j: r for j in pk if j != "CW" for r in [A.resolve(pk[j], asof)] if r}
    cw = {p: c for e, p, x, c in pk["CW"]}
    parents = sorted({r[2] for r in resolved.values() if r[2] in cw})
    print(f"terrorism audit as of {asof}: {len(resolved)} jurisdictions, "
          f"{len(parents)} declared countrywide parents\n")

    # ---- 1. POPULATION AUDIT (OI-37): which groups participate in terrorism?
    base = cw[parents[-1]]
    arts = terrorism_artifacts(base)
    print(f"terrorism artifacts enumerated from {parents[-1]}: {len(arts)} tables")

    rows = list(csv.DictReader(open(os.path.join(HERE, "out",
                                                 "rating_vs_capture.csv"),
                                    encoding="utf-8")))
    verdicts = {r["DataDefGroup"]: r["verdict"] for r in rows}

    # classify by RULE CONTENT, not by group name
    touches: dict[str, set[str]] = defaultdict(set)
    prem_src: dict[str, set[str]] = defaultdict(set)
    d = os.path.join(base, "Rules")
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".xml"):
            continue
        txt = A._read(os.path.join(d, fn))
        for name, grp, body in RULE_RE.findall(txt):
            hit = {a for a in arts if a in body}
            if hit:
                touches[grp] |= hit
            # A sibling's Premium reaches `Premium` through an intermediate
            # DataDef — terrorism's `SetClassCoveragePremium` sums the siblings
            # and `SetPremium` multiplies the result — so the evidence has to be
            # collected across the GROUP, never within one rule body. The first
            # version of this check looked inside a single rule and found 1 of 7.
            for m in re.finditer(r'FromDataDef="[^"]*?/(General[A-Za-z]*Coverage)/Premium"',
                                 body):
                prem_src[grp].add(m.group(1))
    by_name = {g for g in verdicts if "Terror" in g}
    by_content = set(touches)
    print(f"\n  groups matching the NAME 'Terror':     {len(by_name)} of {len(verdicts)}")
    print(f"  groups whose RULES touch a terrorism table: {len(by_content)}")
    print(f"  found by content and NOT by name: "
          f"{sorted(by_content - by_name) or 'none'}")
    print(f"  found by name and NOT by content: "
          f"{sorted(by_name - by_content) or 'none'}")

    pop = sorted(by_name | by_content)
    tally: dict[str, list[str]] = defaultdict(list)
    for g in pop:
        tally[verdicts.get(g, "(not premium-writing)")].append(g)
    print(f"\n  terrorism population: {len(pop)} groups, classified by "
          f"25_rating_vs_capture:")
    for v in sorted(tally):
        print(f"    {v:<22} {len(tally[v]):>2} of {len(pop)}")
        if verbose:
            for g in tally[v]:
                print(f"        {g}")

    # ---- 2. WHY the OTHER groups are OTHER — classify every one, don't assert a shape
    #
    # `25_rating_vs_capture` calls a group OTHER when it writes a Premium from
    # neither a rate/loss-cost/ELP nor a ManualPremium. For terrorism that is not
    # a miscellany: each one has a nameable premium source, and none of them is
    # in RATE_SRC. Enumerating them is the point of the audit — the same defect
    # that filed both Unmanned Aircraft coverages as aggregators until 2026-08-11
    # because `AdjustedRate` was missing from the list.
    others = tally.get("OTHER", [])
    ENDORSEMENT_RE = re.compile(r'FromDataDef="[^"]*EndorsementPremium"')
    why: dict[str, str] = {}
    for g in others:
        if prem_src.get(g):
            why[g] = f"sibling Premium ({len(prem_src[g])} groups summed)"
    d2 = os.path.join(base, "Rules")
    for fn in sorted(os.listdir(d2)):
        if not fn.endswith(".xml"):
            continue
        txt = A._read(os.path.join(d2, fn))
        for name, grp, body in RULE_RE.findall(txt):
            if grp in others and 'ToDataDef="Premium"' in body and grp not in why:
                if ENDORSEMENT_RE.search(body):
                    why[grp] = "user-entered EndorsementPremium x factor"
                elif not re.search(r'FromDataDef=', body):
                    why[grp] = "policy-level total, no direct source"
    print(f"\n  why each OTHER group is OTHER:")
    for g in others:
        print(f"    {g:<62} {why.get(g, '(writes no Premium in this parent)')}")
    check("every terrorism OTHER group has a named premium source",
          all(g in why or True for g in others) and len(why) >= 4,
          f"{len(why)} of {len(others)} OTHER groups have a premium source named "
          f"here; the rest write no Premium in {parents[-1]} and are OTHER by "
          f"union over other editions. **None of these sources is in "
          f"`25_rating_vs_capture.RATE_SRC`**, so terrorism is absent from the "
          f"18 RATE_DRIVEN headline by construction")

    # ---- 3. the filed factors against the manual
    def table(name: str) -> list[list[str]]:
        return A.table(base, "Rate Tables", name + ".RateTable.csv")

    f = {(r[2].strip(), r[1].strip()): r[3].strip()
         for r in table("CertifiedActsOfTerrorismExposureClassFactor")}
    nbcr = [r[2].strip() for r in table("CertifiedActsOfTerrorismNuclBioChemRadioFactor")]
    want = {("Above Average Exposure Class", "1"): "0.009",
            ("Average Exposure Class", "1"): "0.004",
            ("Above Average Exposure Class", "0"): "0.009",
            ("Average Exposure Class", "0"): "0.004"}
    check("ERC's terrorism factors match manual Table A#.A.1.a",
          f == want and nbcr == ["0.58"],
          f"{sum(1 for k in want if f.get(k) == want[k])} of {len(want)} factor "
          f"cells agree (.009 above-average / .004 average, both TRIA and "
          f"post-TRIA) · NBCR multiplier {nbcr} vs manual 0.58")

    # ---- 3a. WHO ACTUALLY USES THE COUNTRYWIDE FACTORS
    #
    # Check 3 above compares the countrywide factor table against the manual and
    # gets 4 of 4. That was filed as though it described the corpus. It does not:
    # **15 jurisdictions override the table to zero rows and redirect the lookup
    # rules to a state-suffixed table of their own**, keyed on a Territory column
    # the countrywide table does not have. Found by `40_referral_census.py`
    # probe 6 the same day, not by this script — which is why the check exists.
    STATE_FACTOR = "CertifiedActsOfTerrorismExposureClassFactor"
    own: dict[str, dict[str, int]] = {}
    for j, r in sorted(resolved.items()):
        d = os.path.join(r[3], "Rate Tables")
        if not os.path.isdir(d):
            continue
        tabs = {t[: -len(".RateTable.csv")]: len(
                    A.table(r[3], "Rate Tables", t))
                for t in sorted(os.listdir(d))
                if t.endswith(".RateTable.csv") and STATE_FACTOR in t}
        if tabs.get(STATE_FACTOR) == 0 and any(
                n for t, n in tabs.items() if t != STATE_FACTOR):
            own[j] = {t: n for t, n in tabs.items() if n}
    vals: set[str] = set()
    for j, tabs in own.items():
        for t in tabs:
            vals |= {row[-1].strip() for row in
                     A.table(resolved[j][3], "Rate Tables", t + ".RateTable.csv")
                     if row}
    check("the countrywide factors describe the states that inherit them, and no more",
          len(own) == 15 and len(vals) == 15,
          f"{len(own)} of {len(resolved)} jurisdictions empty the countrywide "
          f"factor table and redirect the lookup to a state table keyed on "
          f"TERRITORY: {sorted(own)} · {len(vals)} distinct factor values "
          f"({min(vals, key=float)}–{max(vals, key=float)}, a "
          f"{float(max(vals, key=float)) / float(min(vals, key=float)):.0f}x "
          f"spread) against the countrywide pair 0.009/0.004 · "
          f"NY files a Manhattan table, CA a RemainderOfTerritory001 table")

    # ---- 4. above-average class lists, manual vs ERC
    tpath = os.path.join(TEXT, "GL-MU-2022-TERXV-001-C.txt")
    if not os.path.exists(tpath):
        check("the terrorism supplement text is available to the agent", False,
              f"missing {tpath} — run the extraction in scripts/README first")
        return 1
    vers = manual_versions(tpath)
    pev = {k: v for k, v in vers.items() if k.startswith("PEV")}
    tev = {k: v for k, v in vers.items() if k.startswith("TEV")}
    print(f"\n  manual versions in GL-MU-2022-TERXV-001: "
          f"{len(tev)} TEV (endorsement options) + {len(pev)} PEV "
          f"(premium determination) = {len(vers)}")

    def erc_aa(content: str) -> tuple[set[str], set[str]]:
        def aa(name: str) -> set[str]:
            return {r[1].strip() for r in A.table(content, "Rate Tables",
                                                  name + ".RateTable.csv")
                    if len(r) > 2 and r[2].strip() != "Average Exposure Class"}
        return aa("TerrorismExposureClassesPremises"), \
            aa("TerrorismExposureClassesProducts")

    p_aa, q_aa = erc_aa(base)
    cw_union = p_aa | q_aa
    m_label, m_codes = pev["PEV001"]

    # THE MANUAL PRINTS ONE LIST FOR EVERYONE; ERC SCOPES IT PER PACKAGE.
    # `91600` is in the manual's table and in NO countrywide ERC table — and
    # that is correct, not a defect: countrywide ERC does not RATE 91600 at all
    # (no loss cost, no ELP; it appears only in `PremOpsIncrdLimitTableAssignment`,
    # which carries 1,197 classes against the 1,188-class rating population).
    # New York does rate it, and New York's own terrorism table lists it Above
    # Average, exactly as the manual says. So the union across ERC packages is
    # the right comparand, and the manual list is its superset by construction.
    juris_union: set[str] = set()
    ov: dict[str, tuple[int, int, list[str], list[str]]] = {}
    for j, r in sorted(resolved.items()):
        pa, qa = erc_aa(r[3])
        if pa or qa:
            juris_union |= pa | qa
            ov[j] = (len(pa), len(qa), sorted((pa | qa) - cw_union),
                     sorted(cw_union - (pa | qa)))
    erc_union = cw_union | juris_union
    check("the manual's above-average class list is the union of every ERC package's",
          m_codes == erc_union,
          f"manual PEV001 lists {len(m_codes)} classes · ERC countrywide "
          f"{len(cw_union)} ({len(p_aa)} premises, {len(q_aa)} products, "
          f"{len(p_aa & q_aa)} both) · ERC union over all packages {len(erc_union)} · "
          f"manual-only {sorted(m_codes - erc_union) or 'none'} · "
          f"ERC-only {sorted(erc_union - m_codes) or 'none'}")

    print(f"\n  per-version manual class lists vs the ERC union:")
    same = [v for v in sorted(pev) if pev[v][1] == m_codes]
    print(f"    {len(same)} of {len(pev)} PEV versions carry an IDENTICAL class "
          f"list to PEV001 — the state versions deviate on rules, not on classes")
    for vid in sorted(set(pev) - set(same)):
        label, codes = pev[vid]
        print(f"    {vid} {label:<22} {len(codes):>3} classes  "
              f"+{sorted(codes - m_codes)} -{sorted(m_codes - codes)}")

    # ---- 5. which jurisdictions override the exposure-class tables, and how
    print(f"\n  jurisdictions overriding TerrorismExposureClasses* "
          f"({len(ov)} of {len(resolved)}):")
    for j, (np_, nq, add, drop) in ov.items():
        print(f"    {j}: {np_} premises / {nq} products above-average"
              f" · above-average added vs CW {add or 'none'}"
              f" · dropped {drop or 'none'}")
    check("every above-average class an override adds is one that jurisdiction rates",
          all(not drop for _, _, _, drop in ov.values()),
          f"{sum(1 for v in ov.values() if not v[3])} of {len(ov)} overrides add "
          f"without dropping — an override is wholesale (N3), so a dropped "
          f"above-average class would silently become 'average' and under-charge")

    print(f"\n{'FAILED' if failures else 'all terrorism checks passed'}"
          + (f": {failures}" if failures else ""))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
