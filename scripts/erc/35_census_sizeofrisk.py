"""Size-Of-Risk census — build-order item 8.

WHY THIS SCRIPT EXISTS
----------------------
The Step 38 handoff warned that item 8's own data carries the OI-20 sharded-table
trap: the countrywide `*SizeOfRiskLossCost` tables are 0 rows while New Jersey
ships `PremOpsSizeOfRiskLossCostTerr501..517` at ~1,187 rows each. The instruction
was **resolve the lookup RULE, never the table name.** This script does exactly
that, and obeys habit 8 while doing it:

  * the population of SIZE-OF-RISK TABLES is every `*.RateTable.csv` in the
    package whose stem contains `SizeOfRisk` — enumerated from the directory,
    never from a list of names this script already knew;
  * the population of SIZE-OF-RISK LOOKUPS is every `<rul:Rule Name="Lookup...">`
    in the package whose name contains `SizeOfRisk` — and the table it actually
    reads is taken from its own `MatrixFromConstant`, per lookup;
  * the population of JURISDICTIONS is all of them, resolved as of a REQUIRED
    as-of date (N4), each against its own DECLARED countrywide parent (N6).

Every check prints "n of N" with N named.

    python 35_census_sizeofrisk.py 20260812 [--verbose]

Exit code 1 if any assertion fails, so it can join the verification routine.
"""
from __future__ import annotations

import importlib.util
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "asof", os.path.join(HERE, "32_asof_recount.py"))
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)

RULE_RE = re.compile(r'<rul:Rule Name="([^"]+)"[^>]*>(.*?)</rul:Rule>', re.S)
MATRIX_RE = re.compile(r'MatrixFromConstant="([^"]+)"')
RUNRULE_RE = re.compile(r'Rule="([^"]+)"')
SOR = "SizeOfRisk"

failures: list[str] = []


def check(name: str, ok: bool, detail: str) -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}\n         {detail}")
    if not ok:
        failures.append(name)


# --------------------------------------------------------------- populations

def sor_tables(content: str) -> dict[str, int]:
    """Every rate table in the package whose stem contains SizeOfRisk -> row count.

    Enumerated by listing the directory. A name-list would reproduce the exact
    defect this project keeps catching.
    """
    d = os.path.join(content, "Rate Tables")
    if not os.path.isdir(d):
        return {}
    out: dict[str, int] = {}
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".RateTable.csv"):
            continue
        stem = fn[: -len(".RateTable.csv")]
        if SOR not in stem:
            continue
        out[stem] = len(A.table(content, "Rate Tables", fn))
    return out


def sor_lookups(content: str) -> dict[str, set[str]]:
    """Every SizeOfRisk lookup rule -> the set of tables it actually reads.

    Keyed by rule name, valued by `MatrixFromConstant`. This is the handoff's
    instruction made mechanical: the binding from concept to table is read out
    of the rule, so a jurisdiction that re-points a lookup at a sharded table
    is seen rather than assumed absent.
    """
    d = os.path.join(content, "Rules")
    if not os.path.isdir(d):
        return {}
    out: dict[str, set[str]] = defaultdict(set)
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".xml"):
            continue
        for name, body in RULE_RE.findall(A._read(os.path.join(d, fn))):
            if SOR in name and name.startswith("Lookup"):
                out[name] |= set(MATRIX_RE.findall(body))
    return dict(out)


def sor_setters(content: str) -> dict[str, set[str]]:
    """Every non-Lookup rule mentioning SizeOfRisk -> the lookup rules it calls."""
    d = os.path.join(content, "Rules")
    out: dict[str, set[str]] = defaultdict(set)
    if not os.path.isdir(d):
        return {}
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".xml"):
            continue
        for name, body in RULE_RE.findall(A._read(os.path.join(d, fn))):
            if name.startswith("Lookup"):
                continue
            if SOR in name or SOR in body:
                out[name] |= {r for r in RUNRULE_RE.findall(body) if SOR in r}
    return dict(out)


def family(stem: str) -> str:
    """Classify a size-of-risk table stem into its rating role.

    Order matters: `...LossCostTerr501` must land in LossCost, and
    `...RelativityTableAssignment` must not be swallowed by `Relativity`.
    """
    for key, fam in (("TableAssignment", "TableAssignment"),
                     ("MinimumRelativity", "Minimum"),
                     ("MaximumRelativity", "Maximum"),
                     ("LossCost", "LossCost"),
                     ("Relativity", "Relativity")):
        if key in stem:
            return fam
    return "OTHER"


def main() -> int:
    asof = next((a for a in sys.argv[1:] if len(a) == 8 and a.isdigit()), None)
    verbose = "--verbose" in sys.argv
    if not asof:
        print(__doc__)
        print("ERROR: an as-of date is REQUIRED (N4).", file=sys.stderr)
        return 2

    pk = A.discover()
    resolved = {j: r for j in pk if j != "CW" for r in [A.resolve(pk[j], asof)] if r}
    cw_all = {p: c for e, p, x, c in pk["CW"]}
    parents = sorted({r[2] for r in resolved.values() if r[2] in cw_all})
    print(f"size-of-risk census as of {asof}: {len(resolved)} jurisdictions "
          f"resolved of {len(pk) - 1} present, {len(parents)} declared countrywide "
          f"parents of {len(cw_all)} countrywide packages\n")

    # ---- 1. the countrywide picture, per declared parent
    print("countrywide parents — size-of-risk tables by family (rows):")
    cw_fam: dict[str, dict[str, int]] = {}
    for p in parents:
        tabs = sor_tables(cw_all[p])
        fam: dict[str, int] = defaultdict(int)
        for stem, n in tabs.items():
            fam[family(stem)] += n
        cw_fam[p] = dict(fam)
        print(f"  {p:<24} {len(tabs)} tables · "
              + " · ".join(f"{k}={fam.get(k, 0)}"
                           for k in ("TableAssignment", "Relativity", "Minimum",
                                     "Maximum", "LossCost")))
    print()

    # ---- 2. no countrywide parent ships a size-of-risk LOSS COST row
    #
    # `SetPremOpsLossCost` SWAPS the loss cost source when size-of-risk applies:
    # it reads `PremOpsSizeOfRiskLossCost` instead of `PremOpsLossCost`. So an
    # empty countrywide loss cost table is not a cosmetic gap — it is the whole
    # front of the premium chain going missing.
    empty = [p for p in parents if cw_fam[p].get("LossCost", 0) == 0]
    check("no declared countrywide parent carries a size-of-risk loss cost row",
          len(empty) == len(parents),
          f"{len(empty)} of {len(parents)} parents have 0 loss-cost rows — the "
          f"size-of-risk loss cost is a JURISDICTION obligation, never countrywide")

    # ---- 3. the relativity apparatus is NOT uniform across parents
    have_minmax = [p for p in parents if cw_fam[p].get("Maximum", 0) > 0]
    check("the min/max clamp tables are present in every declared parent",
          len(have_minmax) == len(parents),
          f"{len(have_minmax)} of {len(parents)} parents carry Maximum rows"
          + ("" if len(have_minmax) == len(parents)
             else f" · EMPTY IN {[p for p in parents if p not in have_minmax]}"))

    # ---- 4. jurisdictions: enumerate all, classify every one
    ships: dict[str, dict[str, int]] = {}
    shard: dict[str, list[str]] = {}
    for j, r in sorted(resolved.items()):
        tabs = sor_tables(r[3])
        fam: dict[str, int] = defaultdict(int)
        stems: list[str] = []
        for stem, n in tabs.items():
            fam[family(stem)] += n
            if family(stem) == "LossCost" and n:
                stems.append(stem)
        ships[j] = dict(fam)
        shard[j] = sorted(stems)
    with_lc = sorted(j for j in ships if ships[j].get("LossCost", 0) > 0)
    check("every jurisdiction is classified for size-of-risk loss costs",
          len(ships) == len(resolved),
          f"{len(with_lc)} of {len(resolved)} jurisdictions ship size-of-risk "
          f"loss-cost ROWS; {len(resolved) - len(with_lc)} ship none")

    # ---- 5. sharding: how many distinct table NAMES carry ONE subline's concept
    #
    # Two names is the NORMAL case — `PremOps...` and `ProdsCompldOps...` are two
    # different sublines, not two shards. Sharding means one SUBLINE's loss cost
    # split across several names, which is what the `Terr501..517` suffix does.
    def per_subline(stems: list[str]) -> dict[str, int]:
        out: dict[str, int] = defaultdict(int)
        for s in stems:
            out["ProdsCompldOps" if s.startswith("ProdsCompldOps")
                else "PremOps"] += 1
        return dict(out)

    sharded = {j: per_subline(v) for j, v in shard.items()
               if any(n > 1 for n in per_subline(v).values())}
    print(f"\n  jurisdictions shipping size-of-risk loss costs "
          f"({len(with_lc)} of {len(resolved)}):")
    for j in with_lc:
        ps = per_subline(shard[j])
        print(f"    {j:<4} {ships[j]['LossCost']:>7} rows across "
              f"{len(shard[j]):>2} table name(s)  "
              + " · ".join(f"{k}×{n}" for k, n in sorted(ps.items()))
              + ("   <-- SHARDED" if j in sharded else ""))
    print(f"\n  {len(sharded)} of {len(with_lc)} shard ONE subline's loss cost "
          f"across more than one table name: "
          f"{ {j: sharded[j] for j in sorted(sharded)} }")

    # ---- 6. resolve the LOOKUP, not the name: what does each jurisdiction read?
    #
    # A jurisdiction that does NOT redefine a lookup inherits its DECLARED parent's.
    # The first version of this check forgot that and reported 68 unread tables in
    # 33 jurisdictions that are simply reading the countrywide rule — habit 8's
    # failure mode committed inside habit 8's own script, for the second time.
    print("\n  size-of-risk lookups, resolved from the rule bodies:")
    cw_reads: dict[str, set[str]] = {}
    for p in parents:
        lk = sor_lookups(cw_all[p])
        cw_reads[p] = {t for v in lk.values() for t in v}
        print(f"    countrywide {p}: {len(lk)} size-of-risk lookup rules "
              f"reading {len(cw_reads[p])} tables")
    reads: dict[str, set[str]] = {}
    for j in with_lc:
        lk = sor_lookups(resolved[j][3])
        inherited = cw_reads.get(resolved[j][2], set())
        reads[j] = {t for v in lk.values() for t in v} | inherited
        if verbose:
            for name in sorted(lk):
                print(f"    {j}  {name} -> {sorted(lk[name])}")
    for j in with_lc:
        own = sor_lookups(resolved[j][3])
        extra = sorted({t for v in own.values() for t in v}
                       - cw_reads.get(resolved[j][2], set()))
        if extra:
            print(f"    {j}: overrides {len(own)} lookup rule(s) to read "
                  f"{len(extra)} table(s) the parent never names "
                  f"-> {extra[0]}{' … ' + extra[-1] if len(extra) > 1 else ''}")

    # every table a jurisdiction SHIPS with rows must be READ by some lookup
    unread: list[str] = []
    n_pop = 0
    for j in with_lc:
        for stem, n in sor_tables(resolved[j][3]).items():
            if not n:
                continue
            n_pop += 1
            if stem not in reads[j]:
                unread.append(f"{j}:{stem}")
    check("every POPULATED size-of-risk table is read by a resolved lookup rule",
          not unread,
          f"{n_pop - len(unread)} of {n_pop} populated size-of-risk tables across "
          f"{len(with_lc)} shipping jurisdictions have a resolved reader"
          + (f" · UNREAD {unread[:8]}" if unread else ""))

    # ---- 6b. WHO BINDS the size-of-risk loss cost, per jurisdiction
    #
    # New Jersey does not override the LOOKUP. It overrides the SETTER
    # (`SetPremOpsLossCost`) and dispatches with a hand-written Choose over the
    # territory code to 15 territory-specific lookup rules. So the binding from
    # "size-of-risk loss cost" to a table is a property of the SETTER in the
    # resolved package, and an engine that keys off the lookup name — or off the
    # table name — gets New Jersey and Ohio wrong. This check enumerates the
    # binding for every shipping jurisdiction rather than assuming the shape.
    SETTERS = ("SetPremOpsLossCost", "SetProdsCompldOpsLossCost")
    print("\n  who binds the size-of-risk loss cost (setter override, "
          f"{len(with_lc)} shipping jurisdictions):")
    override: dict[str, list[str]] = {}
    for j in with_lc:
        own = []
        d = os.path.join(resolved[j][3], "Rules")
        for fn in sorted(os.listdir(d)) if os.path.isdir(d) else []:
            if not fn.endswith(".xml"):
                continue
            txt = A._read(os.path.join(d, fn))
            for name, _b in RULE_RE.findall(txt):
                if name in SETTERS:
                    own.append(name)
        override[j] = sorted(set(own))
    by_shape: dict[str, list[str]] = defaultdict(list)
    for j in with_lc:
        by_shape[", ".join(override[j]) or "(inherits the parent setter)"].append(j)
    for shape, js in sorted(by_shape.items(), key=lambda kv: -len(kv[1])):
        print(f"    {len(js):>2} of {len(with_lc)}  {shape}: {js}")
    check("every jurisdiction that shards its loss cost also overrides the setter",
          all(override[j] for j in sharded),
          f"{sum(1 for j in sharded if override[j])} of {len(sharded)} sharding "
          f"jurisdictions override a loss-cost setter — the binding lives in the "
          f"setter, not the table name")

    # ---- 6a. forward-dated countrywide editions: does the apparatus survive?
    future = sorted(p for p in cw_all if p not in parents)
    print(f"\n  countrywide packages NOT yet any jurisdiction's declared parent "
          f"as of {asof} ({len(future)} of {len(cw_all)}):")
    for p in future:
        fam: dict[str, int] = defaultdict(int)
        for stem, n in sor_tables(cw_all[p]).items():
            fam[family(stem)] += n
        print(f"    {p:<24} "
              + " · ".join(f"{k}={fam.get(k, 0)}"
                           for k in ("TableAssignment", "Relativity", "Minimum",
                                     "Maximum", "LossCost")))

    # ---- 7. the setter chain, and where the sentinel zero can reach
    st = sor_setters(cw_all[parents[-1]]) if parents else {}
    print(f"\n  {parents[-1] if parents else '-'} — setter rules touching "
          f"size-of-risk: {len(st)}")
    for name in sorted(st):
        print(f"    {name}" + (f" -> {sorted(st[name])}" if st[name] else ""))

    print(f"\n{'FAILED' if failures else 'all size-of-risk checks passed'}"
          + (f": {failures}" if failures else ""))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
