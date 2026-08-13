"""OI-40: every load-bearing "latest edition" count, RE-MEASURED AS OF A DATE.

Why this script exists
----------------------
`31_migration_asof.py` established the defect: "latest package per jurisdiction"
describes a FUTURE state, because the corpus holds 82 state packages effective
after today. That script fixed one figure (the 2027 class-basis cliff). This one
re-tests the rest of the figures that were measured the same way and are now
load-bearing — they size phases and seed class lists.

Five figures, each reported for every as-of date given:

  F1  TERRITORY SCHEME MIX   "all 51 resolve: 27 ZIP / 20 constant / 4 county-place"
      Build plan section 12, phase 3 EXIT CRITERION. Invariant ERC-TER-001.
  F2  COUNTRYWIDE TABLE POPULATION   "138 of 272 CW rate tables are header-only"
      N7. Drives load-time assertions. OI-19 flagged it as one-edition-only.
  F3  PREM/OPS CLASS INVENTORY   "238 pre-2027 only / 204 2027 only / 959 both"
      README finding 4. Seeds the class list.
  F4  RATING-VS-CAPTURE   "16 RATE_DRIVEN / 383 CAPTURE / 78 aggregators"
      The headline scope number. Build plan sections 3 and 13.
  F5  GATE-CITED LAYER TABLES   the "0 rows (header only)" claims in gates 334,
      336 and 335, plus the loss-cost tables filed under SPLIT NAMES (OI-20).

METHOD (N4). The as-of date is a REQUIRED argument. There is no default, and
"latest" is never taken to mean "now". For each date:

  * each jurisdiction resolves to the latest package effective ON OR BEFORE it;
  * the countrywide layer resolves to the parent that resolved package DECLARES
    (habit 1 / N5), read from the XSD import — never to the newest CW package;
  * identity comes from the XSD targetNamespace, never the directory (N6).

    python 32_asof_recount.py 20260811 20270401 99999999
    python 32_asof_recount.py 20260811 --only F1

`99999999` is the end state (all filings in force) and is what every figure above
was originally measured over. Any figure that differs across the columns is a
claim whose tense needs fixing.
"""
from __future__ import annotations

import csv
import io
import os
import re
import sys
from collections import Counter, defaultdict

ROOT = r"C:\Projects\ISO_ERC_Files\General_Liability"
EXCLUDE = {"_quarantine_misfiled", ".claude"}
CLIFF = "20270401"

NS_RE = re.compile(r'targetNamespace="http://www\.verisk\.com/iso/erc/([^/"]+)/')
IMPORT_RE = re.compile(r'namespace="http://www\.verisk\.com/iso/erc/(GL_CW_[^/"]+)/')
RULE_RE = re.compile(r'<rul:Rule Name="([^"]+)"[^>]*?DataDefGroup="([^"]+)"[^>]*>(.*?)</rul:Rule>', re.S)
WRITES_PREM = re.compile(r'ToDataDef="((?:[A-Za-z]*)Premium)"')
# Kept in step with 25_rating_vs_capture.py. `AdjustedRate` was missing from both
# until 2026-08-11; see the note there.
RATE_SRC = re.compile(r'From(?:DataDef|Constant)="[^"]*'
                      r'(FinalRate|BaseRate|LossCost|ELP|AdjustedBaseRate|AdjustedRate)')
MANUAL_RE = re.compile(r'FromDataDef="(?:\.\./)*ManualPremium"')


# ----------------------------------------------------------------- discovery

def _read(path: str, limit: int = -1) -> str:
    with open(path, encoding="utf-8-sig", errors="replace") as fh:
        return fh.read() if limit < 0 else fh.read(limit)


def discover() -> dict[str, list[tuple[str, str, str, str]]]:
    """juris -> [(effective, pkg_id, declared CW parent pkg_id, content dir)].

    Identity and parentage both come from the XSD (N6), not the directory name.
    Every package directory holding a DataDefs/ is considered, so a jurisdiction's
    population is the whole population, not the subset that happens to match a
    naming convention (N4's second clause).
    """
    out: dict[str, list[tuple[str, str, str, str]]] = defaultdict(list)
    for dirpath, dirnames, filenames in os.walk(ROOT):
        if any(x in dirpath for x in EXCLUDE):
            dirnames[:] = [d for d in dirnames if d not in EXCLUDE]
        if os.path.basename(dirpath) != "DataDefs":
            continue
        dirnames[:] = []
        content = os.path.dirname(dirpath)
        for fn in sorted(filenames):
            if not fn.endswith(".xsd"):
                continue
            txt = _read(os.path.join(dirpath, fn), 40000)
            m = NS_RE.search(txt)
            if not m:
                continue
            pkg_id = m.group(1)
            parts = pkg_id.split("_")          # GL_XX_YYYYMMDD_Vnn
            if len(parts) < 3:
                continue
            juris, eff = parts[1], parts[2]
            par = IMPORT_RE.search(txt)
            out[juris].append((eff, pkg_id, par.group(1) if par else "", content))
            break
    # de-duplicate: the same package can be unpacked in two sibling directories
    for j, v in out.items():
        by_id: dict[str, tuple[str, str, str, str]] = {}
        for t in sorted(v):
            by_id.setdefault(t[1], t)
        out[j] = sorted(by_id.values())
    return out


def resolve(rows, asof: str):
    """N4: discard editions effective after `asof`, take the latest remaining."""
    eligible = [t for t in sorted(rows) if t[0] <= asof]
    return eligible[-1] if eligible else None


# ------------------------------------------------------------------- tables

def rows_of(path: str) -> list[list[str]]:
    if not os.path.exists(path):
        return []
    r = list(csv.reader(io.StringIO(_read(path))))
    return [x for x in r[1:] if any(c.strip() for c in x)] if r else []


def table(content: str, kind: str, name: str) -> list[list[str]]:
    return rows_of(os.path.join(content, kind, name))


# ------------------------------------------------------------------ F1 terr

def _prem_ops_terr_tables(content: str) -> list[str]:
    """Domain tables that carry the PREMISES/OPERATIONS rating territory.

    Discovered by scanning the directory, never by assuming one file name — five
    distinct names are in use across the corpus (`DomainPremisesOperationsTerr`,
    `DomainPremOpsTerr`, `DomainPremOpsTerritory`, `DomainPremisesOperationsTerritory`,
    `DomainTerritoryAssignmentPremOps`) and a classifier hardcoding the commonest
    one silently loses Delaware. Excluded: the `*Override` / `*OvrdFinal` shells,
    the special-class and deductible assignment tables, and every Terrorism table —
    none of them is the rating territory.
    """
    d = os.path.join(content, "Domain Tables")
    if not os.path.isdir(d):
        return []
    out = []
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".DomainTable.csv"):
            continue
        stem = fn[: -len(".DomainTable.csv")]
        if "Terrorism" in stem or "Terr" not in stem:
            continue
        if not ("PremOps" in stem or "PremisesOperations" in stem):
            continue
        if any(x in stem for x in ("Override", "Ovrd", "IncrdLimit",
                                   "SpecialClass", "Ded")):
            continue
        out.append(fn)
    return out


def territory_scheme(content: str) -> tuple[str, str, list[str]]:
    """(scheme, detail, tables consulted) from the package's own domain tables.

    Read from the files, not from the table's name. The countrywide layer carries
    both territory tables as header-only stubs in all ten CW editions — verified
    before this classifier was written, not assumed — so the state layer is the
    only place territory is populated, and a state package alone decides its scheme.
    """
    zips = table(content, "Domain Tables",
                 "DomainTerritoryCodeByZipCode.DomainTable.csv")
    if zips:
        return "ZIP", f"{len({r[1] for r in zips if len(r) > 1})} ZIPs", \
            ["DomainTerritoryCodeByZipCode"]
    tabs = _prem_ops_terr_tables(content)
    codes: set[str] = set()
    for fn in tabs:
        for r in table(content, "Domain Tables", fn):
            v = r[-1].strip()
            if v and v != "Other":
                codes.add(v)
    names = [t[len("Domain"): -len(".DomainTable.csv")] for t in tabs]
    if not codes:
        return "UNRESOLVED", "no populated territory table", names
    if not all(v.isdigit() for v in codes):
        return "PLACE", f"{len(codes)} values, non-numeric present", names
    if len(codes) == 1:
        return "SINGLE", next(iter(codes)), names
    return "MULTI_CODE", f"{len(codes)} numeric codes, no ZIP map", names


# ------------------------------------------------------------------- F2 pop

def rate_table_population(content: str) -> tuple[int, int]:
    d = os.path.join(content, "Rate Tables")
    if not os.path.isdir(d):
        return 0, 0
    n = empty = 0
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".RateTable.csv"):
            continue
        n += 1
        if not rows_of(os.path.join(d, fn)):
            empty += 1
    return n, empty


# ----------------------------------------------------------------- F3 class

def prem_ops_classes(content: str) -> set[str]:
    return {r[1] for r in table(content, "Rate Tables",
                                "PremOpsIncrdLimitTableAssignment.RateTable.csv")
            if len(r) > 1}


# ------------------------------------------------------------------ F4 rate

def classify_premium_rules(content: str) -> list[tuple[str, str]]:
    """(DataDefGroup, class) for every rule writing a Premium in one package."""
    res = []
    rules_dir = os.path.join(content, "Rules")
    if not os.path.isdir(rules_dir):
        return res
    for dp, _dn, fns in os.walk(rules_dir):
        for fn in fns:
            if not fn.endswith(".xml"):
                continue
            txt = _read(os.path.join(dp, fn))
            for _name, grp, body in RULE_RE.findall(txt):
                if not WRITES_PREM.search(body):
                    continue
                res.append((grp, "RATE_DRIVEN" if RATE_SRC.search(body)
                            else "CAPTURE" if MANUAL_RE.search(body) else "OTHER"))
    return res


# --------------------------------------------------------------- F5 gates

# The rating tables each passed gate cited as "0 rows (header only)" countrywide
# and populated in the state layer. Named here so the claim is re-testable rather
# than re-asserted.
GATE_TABLES = {
    "334": ["PremOpsLossCost", "ILFPremOps", "PremOpsIncrdLimitTableAssignment",
            "PremOpsELP", "PremOpsELPText"],
    "336": ["ProdsCompldOpsLossCost", "ILFProds", "ProdsCompldOpsELPFactor",
            "ProdsCompldOpsELPText"],
    "335": ["OwnersContractorsLossCost", "OwnersContractorsELP",
            "OwnersContractorsELPText", "ILFOwnersContractors"],
}
SPLIT_RE = re.compile(r"^(?P<base>[A-Za-z]+LossCost)(?P<suffix>.+)\.RateTable\.csv$")


def gate_tables(resolved, cw_all, asof: str):
    print("\nF5  GATE-CITED LAYER TABLES  (334, 336, 335 section 5)")
    parents = sorted({r[2] for r in resolved.values() if r[2] and r[2] in cw_all})
    print(f"      countrywide parents in force at this date: {len(parents)} "
          f"({', '.join(parents)})")
    for gate, tabs in GATE_TABLES.items():
        for t in tabs:
            cw_rows = {p: len(rows_of(os.path.join(cw_all[p][1], "Rate Tables",
                                                   t + ".RateTable.csv")))
                       for p in parents}
            st_pop = st_rows = 0
            for _j, (_e, _p, _par, content) in resolved.items():
                n = len(table(content, "Rate Tables", t + ".RateTable.csv"))
                if n:
                    st_pop += 1
                    st_rows += n
            cw_note = ("0 rows in every parent" if set(cw_rows.values()) == {0}
                       else f"POPULATED: {cw_rows}")
            print(f"      [{gate}] {t:<34} CW {cw_note:<24} "
                  f"state {st_pop:>2}/{len(resolved)} juris, {st_rows:>6} rows")


def split_tables(resolved):
    """Loss costs a jurisdiction files under per-territory table NAMES.

    Found while re-testing N7: four jurisdictions leave the base `PremOpsLossCost`
    header-only and file the rows under `PremOpsLossCost<ST>Terr<nnn>` instead. A
    reader that knows only the base name sees an empty table and no error.
    """
    print("\nF5b SPLIT LOSS-COST TABLE NAMES  (found re-testing N7)")
    for j, (_e, _p, _par, content) in sorted(resolved.items()):
        d = os.path.join(content, "Rate Tables")
        if not os.path.isdir(d):
            continue
        fams: dict[str, list[str]] = defaultdict(list)
        for fn in os.listdir(d):
            mm = SPLIT_RE.match(fn)
            if mm and mm.group("suffix"):
                fams[mm.group("base")].append(fn)
        for base, fns in sorted(fams.items()):
            if rows_of(os.path.join(d, base + ".RateTable.csv")):
                continue        # base is populated; the suffixed ones are extra
            n = sum(len(rows_of(os.path.join(d, f))) for f in fns)
            print(f"      {j}  {base} is header-only; {len(fns)} suffixed tables "
                  f"carry {n:,} rows")


# -------------------------------------------------------------------- report

def cw_population(pk, asof: str):
    """The countrywide packages the as-of state packages actually DECLARE."""
    cw = {}
    for eff, pkg_id, _par, content in pk.get("CW", []):
        cw[pkg_id] = (eff, content)
    return cw


def run(pk, asof: str, only: set[str]):
    label = "latest filed (end state)" if asof == "99999999" else asof
    print(f"\n{'=' * 78}\nAS OF {label}\n{'=' * 78}")

    cw_all = cw_population(pk, asof)
    states = sorted(j for j in pk if j != "CW")
    resolved = {}
    for j in states:
        r = resolve(pk[j], asof)
        if r:
            resolved[j] = r

    print(f"jurisdictions resolving: {len(resolved)} of {len(states)}")
    if len(resolved) != len(states):
        print(f"  UNRESOLVED: {sorted(set(states) - set(resolved))}")

    pre = sum(1 for r in resolved.values() if r[0] < CLIFF)
    print(f"class basis: pre-2027 {pre} | 2027 {len(resolved) - pre}")

    # ---- F1 territory ----
    if "F1" in only:
        schemes = Counter()
        detail: dict[str, list[str]] = defaultdict(list)
        singles = Counter()
        odd = []
        for j, (_eff, _pid, _par, content) in sorted(resolved.items()):
            s, d, tabs = territory_scheme(content)
            schemes[s] += 1
            detail[s].append(j)
            if s == "SINGLE":
                singles[d] += 1
            if s in ("UNRESOLVED", "MULTI_CODE"):
                odd.append(f"{j} [{s}] {d} via {tabs}")
        print("\nF1  TERRITORY SCHEME  (phase 3 exit criterion; ERC-TER-001)")
        for s, n in schemes.most_common():
            js = detail[s]
            shown = ", ".join(js) if len(js) <= 8 else f"{', '.join(js[:8])} ... (+{len(js) - 8})"
            print(f"      {s:<12}{n:>4}   {shown}")
        if singles:
            print(f"      single-territory codes: "
                  f"{', '.join(f'{k}x{v}' for k, v in singles.most_common())}")
        for line in odd:
            print(f"      ! {line}")
        print(f"      all resolve to exactly one scheme: "
              f"{'YES' if not (schemes['UNRESOLVED'] or schemes['MULTI_CODE']) else 'NO'}")

    # ---- F2 table population ----
    if "F2" in only:
        declared = Counter(r[2] for r in resolved.values() if r[2])
        print("\nF2  COUNTRYWIDE RATE-TABLE POPULATION  (N7; OI-19)")
        print(f"      {'declared CW parent':<26}{'states':>7}{'tables':>8}"
              f"{'header-only':>13}{'populated':>11}")
        for pid, nstates in sorted(declared.items()):
            if pid not in cw_all:
                print(f"      {pid:<26}{nstates:>7}   PARENT NOT IN CORPUS")
                continue
            n, empty = rate_table_population(cw_all[pid][1])
            print(f"      {pid:<26}{nstates:>7}{n:>8}{empty:>13}{n - empty:>11}")
        cwr = resolve([(e, p, "", c) for p, (e, c) in cw_all.items()], asof)
        if cwr:
            n, empty = rate_table_population(cwr[3])
            print(f"      CW resolved as-of (not declared): {cwr[1]}  "
                  f"{n} tables, {empty} header-only")

    # ---- F3 class inventory ----
    if "F3" in only:
        prec: set[str] = set()
        postc: set[str] = set()
        for _j, (eff, _pid, _par, content) in resolved.items():
            (postc if eff >= CLIFF else prec).update(prem_ops_classes(content))
        print("\nF3  PREM/OPS CLASS INVENTORY  (README finding 4)")
        print(f"      in force as of this date: {len(prec | postc)} distinct class codes")
        print(f"      pre-2027 basis {len(prec)} | 2027 basis {len(postc)} | "
              f"pre-only {len(prec - postc)} | 2027-only {len(postc - prec)} | "
              f"both {len(prec & postc)}")

    # ---- F5 gate-cited tables ----
    if "F5" in only:
        gate_tables(resolved, cw_all, asof)
        split_tables(resolved)

    # ---- F4 rating vs capture ----
    if "F4" in only:
        grp = defaultdict(Counter)
        pkgs = [r[3] for r in resolved.values()]
        pkgs += [cw_all[p][1] for p in {r[2] for r in resolved.values()}
                 if p in cw_all]
        for content in pkgs:
            for g, cls in classify_premium_rules(content):
                grp[g][cls] += 1
        verdict = Counter("RATE_DRIVEN" if c["RATE_DRIVEN"] else
                          "CAPTURE" if c["CAPTURE"] else "OTHER"
                          for c in grp.values())
        print("\nF4  RATING VS CAPTURE  (build plan sections 3, 13)")
        print(f"      packages scanned: {len(pkgs)}   "
              f"distinct groups writing a Premium: {len(grp)}")
        print(f"      RATE_DRIVEN {verdict['RATE_DRIVEN']} | "
              f"CAPTURE {verdict['CAPTURE']} | OTHER (aggregators) {verdict['OTHER']}")
        return {g: ("RATE_DRIVEN" if c["RATE_DRIVEN"] else
                    "CAPTURE" if c["CAPTURE"] else "OTHER") for g, c in grp.items()}
    return None


def main() -> int:
    argv = [a for a in sys.argv[1:]]
    only = {"F1", "F2", "F3", "F4", "F5"}
    if "--only" in argv:
        i = argv.index("--only")
        only = set(argv[i + 1].split(","))
        del argv[i:i + 2]
    dates = [a for a in argv if not a.startswith("-")]
    if not dates:
        print(__doc__)
        print("ERROR: an as-of date is REQUIRED (N4). There is no default.",
              file=sys.stderr)
        return 2
    bad = [d for d in dates if not (len(d) == 8 and d.isdigit())]
    if bad:
        print(f"ERROR: not YYYYMMDD: {bad}", file=sys.stderr)
        return 2

    pk = discover()
    total = sum(len(v) for v in pk.values())
    print(f"packages discovered: {total} across {len(pk)} namespaces "
          f"(identity from XSD targetNamespace, N6)")

    verdicts = {}
    for d in dates:
        v = run(pk, d, only)
        if v is not None:
            verdicts[d] = v

    if len(verdicts) > 1 and "F4" in only:
        print(f"\n{'=' * 78}\nF4 DIFF ACROSS AS-OF DATES\n{'=' * 78}")
        keys = list(verdicts)
        base, last = verdicts[keys[0]], verdicts[keys[-1]]
        appeared = sorted(set(last) - set(base))
        gone = sorted(set(base) - set(last))
        changed = sorted(g for g in set(base) & set(last) if base[g] != last[g])
        print(f"groups only at {keys[-1]}: {len(appeared)}")
        for g in appeared[:15]:
            print(f"      + {g[:70]:<72} {last[g]}")
        print(f"groups only at {keys[0]}: {len(gone)}")
        for g in gone[:15]:
            print(f"      - {g[:70]:<72} {base[g]}")
        print(f"groups whose verdict changed: {len(changed)}")
        for g in changed[:15]:
            print(f"      ~ {g[:70]:<72} {base[g]} -> {last[g]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
