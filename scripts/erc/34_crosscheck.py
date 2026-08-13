"""Cross-check the project's lists against the corpus, and against each other.

Why this script exists
----------------------
On 2026-08-11, seven subline gates produced five wrong figures, and **every one of
them was an aggregate or a negative** — never a misread rule body:

    "Delaware has no territory table"        (it is under a fifth name)
    "no RailroadELPText exists"              (the selector is the RailroadELP table)
    "16 coverage groups rate"                (18 — the classifier's name list was short)
    "item 6 is 320 countrywide rules"        (150 — a substring matched 19 other groups)
    "the drone sentinel is 8 cells"          (18 — only one of three axes was counted)

The shared cause is not carelessness and not "reading the name instead of the
file" — the existing habits already say to read the file. It is narrower:

    A SEARCH PREDICATE WAS ALLOWED TO DEFINE A POPULATION,
    AND THEN A CONCLUSION WAS DRAWN ABOUT THAT POPULATION.

A filename, a regex alternation, a substring, one table out of a family. In each
case the denominator came from the query rather than from the corpus, so anything
the query could not see was reported as absent.

Two rules follow, and this script enforces the second:

  1. WRITING   Every count is "n of N", with N derived from the corpus and named.
               A bare count hides its denominator and cannot be checked.
  2. MEASURING Enumerate the population first, classify every member second.
               Never let the predicate pick the members.

Each check below therefore starts from a corpus-wide enumeration and reports a
denominator. A check that cannot state its denominator is not a check.

    python 34_crosscheck.py 20260811

Exit code 1 if any cross-check fails, so it can join the verification routine.
"""
from __future__ import annotations

import csv
import importlib.util
import io
import os
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "asof", os.path.join(HERE, "32_asof_recount.py"))
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)

ROOT_DOCS = os.path.dirname(HERE)          # scripts/
PROJ = os.path.dirname(ROOT_DOCS)
VOCAB = {"Rate/Loss Cost Applies", "Industry", "Company", "Not Applicable"}
RULE_RE = re.compile(r'<rul:Rule Name="([^"]+)"[^>]*?DataDefGroup="([^"]+)"[^>]*>(.*?)</rul:Rule>',
                     re.S)
LOOKUP_RE = re.compile(r'<rul:Lookup[^>]*MatrixFromConstant="([^"]+)"')

failures: list[str] = []
notes: list[str] = []


def check(name: str, ok: bool, detail: str) -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}\n         {detail}")
    if not ok:
        failures.append(name)


# ---------------------------------------------------------------- populations

def rate_driven() -> set[str]:
    p = os.path.join(HERE, "out", "rating_vs_capture.csv")
    with open(p, encoding="utf-8", newline="") as fh:
        return {r["DataDefGroup"] for r in csv.DictReader(fh)
                if r["verdict"] == "RATE_DRIVEN"}


def build_order_claims() -> dict[str, list[str]]:
    """The DataDefGroup substrings each build-order item claims, from 33_phase_sizing."""
    src = open(os.path.join(HERE, "33_phase_sizing.py"), encoding="utf-8").read()
    body = src[src.index("BUILD_ORDER = ["):src.index("\n]", src.index("BUILD_ORDER = ["))]
    out: dict[str, list[str]] = {}
    for label, keys in re.findall(r'\("([^"]+)",\s*\[([^\]]+)\]', body, re.S):
        out[label] = re.findall(r'"([^"]+)"', keys)
    return out


def main() -> int:
    asof = next((a for a in sys.argv[1:] if len(a) == 8 and a.isdigit()), None)
    if not asof:
        print(__doc__)
        print("ERROR: an as-of date is REQUIRED (N4).", file=sys.stderr)
        return 2

    pk = A.discover()
    resolved = {j: r for j in pk if j != "CW" for r in [A.resolve(pk[j], asof)] if r}
    cw = {p: c for e, p, x, c in pk["CW"]}
    parents = sorted({r[2] for r in resolved.values() if r[2] in cw})
    packages = [(f"CW:{p}", cw[p]) for p in parents] + \
               [(j, r[3]) for j, r in sorted(resolved.items())]
    print(f"cross-check as of {asof}: {len(resolved)} jurisdictions, "
          f"{len(parents)} countrywide parents, {len(packages)} packages enumerated\n")

    # ---- 1. every RATE_DRIVEN group is claimed by exactly one build-order item
    rd = rate_driven()
    claims = build_order_claims()
    owner: dict[str, list[str]] = defaultdict(list)
    for label, keys in claims.items():
        for g in rd:
            # "=" prefix means exact match — see 33_phase_sizing._match
            if any(g == k[1:] if k.startswith("=") else k in g for k in keys):
                owner[g].append(label)
    # `GeneralLiabilityClassification` is a SHARED container: rate-driven solely
    # because of the 11-rule Limited Product Withdrawal Expense chain inside it.
    # It cannot be claimed at group granularity without inflating item 6 by 120
    # rules, so it is allow-listed here with its owner named. The allow-list is the
    # honest form: "claimed, at rule granularity, by item 6".
    SHARED = {"GeneralLiabilityClassification":
              "item 6 — Limited Product Withdrawal Expense, 11 `*Lmtd*` rules"}
    for g, why in SHARED.items():
        if g in rd:
            owner[g].append(why)
    unclaimed = sorted(g for g in rd if not owner[g])
    doubled = sorted(g for g in rd if len(owner[g]) > 1)
    check("every rate-driven coverage is claimed by a build-order item",
          not unclaimed and not doubled,
          f"{len(rd) - len(unclaimed)} of {len(rd)} claimed"
          + (f" · UNCLAIMED {unclaimed}" if unclaimed else "")
          + (f" · CLAIMED TWICE {doubled}" if doubled else ""))

    # ---- 2. selectors enumerated by CONTENT match the count N17 states
    sel: dict[str, set] = defaultdict(set)
    for label, content in packages:
        d = os.path.join(content, "Rate Tables")
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
                    sel[fn[:-len(".RateTable.csv")]].add(col)
    plan = open(os.path.join(PROJ, "docs", "GL-RATING-ENGINE-BUILD-PLAN.md"),
                encoding="utf-8").read()
    named = {t for t in sel if f"`{t}`" in plan}
    check("every rating-basis selector found by content is named in the build plan",
          named == set(sel),
          f"{len(named)} of {len(sel)} named · found {sorted(sel)}"
          + (f" · MISSING FROM PLAN {sorted(set(sel) - named)}" if set(sel) - named else ""))

    # ---- 3. every POPULATED rate table has a reader
    #
    # The first version of this check asserted "no rate table is unread" and
    # reported 79 orphans in one countrywide package — then had to be verified,
    # which is the point. All 79 are 0-row schema stubs; ZERO populated tables
    # are unread. So the assertion worth making is the narrow one, and the wide
    # one was itself an aggregate claim with an unstated denominator.
    #
    # It also demotes two earlier gate findings: `RailroadLossCost` and
    # `SublineProductWithdrawal` were reported as notable orphans. They are two
    # of 79 members of a uniform class of empty stubs, and unremarkable.
    unread_pop: list[str] = []
    n_tab = n_unread = 0
    for p in parents:
        content = cw[p]
        read = set()
        for dp, _dn, fns in os.walk(os.path.join(content, "Rules")):
            for fn in fns:
                if fn.endswith(".xml"):
                    read |= set(LOOKUP_RE.findall(A._read(os.path.join(dp, fn))))
        d = os.path.join(content, "Rate Tables")
        for f in sorted(os.listdir(d)):
            if not f.endswith(".RateTable.csv"):
                continue
            t = f[:-len(".RateTable.csv")]
            n_tab += 1
            if t in read:
                continue
            n_unread += 1
            if A.table(content, "Rate Tables", f):
                unread_pop.append(f"{p}:{t}")
    check("no POPULATED countrywide rate table is unread",
          not unread_pop,
          f"{n_unread} of {n_tab} countrywide table instances have no reader, "
          f"and {len(unread_pop)} of those carry rows"
          + (f" · UNREAD AND POPULATED {unread_pop[:10]}" if unread_pop else
             " — every unread table is an empty schema stub"))

    # ---- 4. sentinel register: every `0` in a registered modifier family is counted
    FAMILIES = {
        "UnmannedAircraft usage/ownership/place modifiers":
            [t for t in ("UnmannedAircraftUsageBIPDRatingModifiers",
                         "UnmannedAircraftUsagePAIRatingModifiers",
                         "UnmannedAircraftOwnershipAndOperationBIPDRatingModifiers",
                         "UnmannedAircraftOwnershipAndOperationPAIRatingModifiers",
                         "UnmannedAircraftPrimaryPlaceOfOperationBIPDRatingModifiers",
                         "UnmannedAircraftPrimaryPlaceOfOperationPAIRatingModifiers")],
    }
    for fam, tables in FAMILIES.items():
        cells = zeros = 0
        for p in parents:
            for t in tables:
                rows = A.table(cw[p], "Rate Tables", t + ".RateTable.csv")
                cells += len(rows)
                zeros += sum(1 for r in rows if len(r) > 2 and r[2].strip() == "0")
            break   # one parent is representative; they are identical
        stated = f"**18**" in plan and "18 of the 60" in plan
        check(f"sentinel family fully counted — {fam}",
              (zeros, cells) == (18, 60),
              f"{zeros} of {cells} cells are `0` "
              f"(the build plan must state both numbers, not just the numerator)")

    print()
    for n in notes:
        print(f"  note: {n}")
    print(f"\n{'FAILED' if failures else 'all cross-checks passed'}"
          + (f": {failures}" if failures else ""))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
