"""Phase sizing, measured — the work each build-order item actually contains.

OI-40 gated this. The figures that size a phase had to be re-tested as-of a date
first (`32_asof_recount.py`), because sizing phase 16 from an end-state group count
or phase 3 from an end-state territory mix would have been sizing the wrong corpus.

This script does not estimate effort. It counts the things each phase must handle,
from the packages in force AS OF a required date:

  * rules to port, per coverage group, split countrywide / state
  * jurisdictions carrying a state rule for that group (the deviation surface)
  * rate tables the group's rules read, and how many are populated
  * whether the countrywide algorithm differs across the parents in force

Effort follows from those; they do not follow from effort.

    python 33_phase_sizing.py 20260811
    python 33_phase_sizing.py 20260811 20270401     # does the 2027 edition resize it?
"""
from __future__ import annotations

import hashlib
import importlib.util
import os
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "asof", os.path.join(HERE, "32_asof_recount.py"))
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)

RULE_RE = re.compile(
    r'<rul:Rule Name="([^"]+)"[^>]*?DataDefGroup="([^"]+)"[^>]*>(.*?)</rul:Rule>', re.S)
WS_RE = re.compile(r"\s+")
# A lookup names its table in MatrixFromConstant, not in any attribute called
# "Table" — checked against the rule XML rather than guessed from the element name.
LOOKUP_RE = re.compile(r'<rul:Lookup[^>]*MatrixFromConstant="([^"]+)"')

# The build order in section 8, keyed to the DataDefGroup substrings that carry it.
# Groups are matched by substring because ERC names them per coverage, not per
# subline, and the subline number is not in the group name.
#
# SUBSTRINGS OVER-MATCH, AND ONCE DID SO BADLY. `ProductWithdrawal` also matches
# 19 endorsement, coverage-form and minimum-premium groups, which inflated item 6
# from its real 150 countrywide / 17 state rules to 320 / 178 and produced a
# recommendation to split the item into three. Every match is therefore now
# intersected with the RATE_DRIVEN set from 25_rating_vs_capture.py: a phase is
# sized by the coverages it must RATE, and the endorsement groups that share a
# name belong to items 8, 12 and 13. Set SIZE_ALL=1 to see the unfiltered figures.
BUILD_ORDER = [
    ("1  Prem/Ops (334)",              ["ClassificationPremOpsCoverage"]),
    ("2  Prods/CompldOps (336)",       ["ClassificationProdsCompldOpsCoverage"]),
    ("3  OCP (335)",                   ["ClassificationOwnersContractorsCoverage"]),
    ("4  Liquor (332)",                ["ClassificationLiquorCoverage"]),
    ("5  Railroad Protective",         ["ClassificationRailroadCoverage"]),
    # NOTE `GeneralLiabilityClassification` is also RATE_DRIVEN and belongs to item 6 —
    # it carries the 11-rule Limited Product Withdrawal Expense chain. It is NOT listed
    # here, deliberately: it is a SHARED container holding classification-level rules for
    # every subline, so claiming the group would inflate item 6 from 150 rules to 270.
    # The unit of ownership is the RULE, not the group, once a group is shared. Sizing
    # for that chain is counted separately in 34_crosscheck.py.
    ("6  Withdrawal / LoED / Cyber",   ["ProductWithdrawal", "LossOfElectronicData",
                                        "CyberIncidentLiability",
                                        ]),
    # Item 7 rates: both groups compute Premium = AdjustedRate x ILF x mods. The
    # scope classifier called them aggregators until 2026-08-11 because its
    # rate-source list omitted `AdjustedRate` (OI-42).
    ("7  Unmanned Aircraft (370)",     ["UnmannedAircraftCovABIPDCoverage",
                                        "UnmannedAircraftCovBPAICoverage"]),
    # Special Protective & Highway is RATE_DRIVEN and exists in NO countrywide
    # edition — it is a NEW YORK-only rating coverage. Its group name carries no
    # state name, which is why it was counted as countrywide for three gates.
    ("11 State-specific: NY highway",  ["SpecialProtectiveHighway"]),
    ("11 State-specific: MD lead",     ["MarylandChangesLiabilityForHazardsOfLead"]),
    ("11 State-specific: MA lead x2",  ["MassachusettsChangesLeadPoisoning",
                                        "MassachusettsChangesSupplementalCovLeadPoisoning"]),
]


def scan_rules(content: str):
    """(DataDefGroup, rule name, tables read, body digest) for one package.

    The digest is whitespace-normalised, so two rules compare equal only when they
    really are the same rule — a rule NAME surviving an edition proves nothing.
    """
    out = []
    rd = os.path.join(content, "Rules")
    if not os.path.isdir(rd):
        return out
    for dp, _dn, fns in os.walk(rd):
        for fn in fns:
            if not fn.endswith(".xml"):
                continue
            txt = A._read(os.path.join(dp, fn))
            for name, grp, body in RULE_RE.findall(txt):
                out.append((grp, name, set(LOOKUP_RE.findall(body)),
                            hashlib.md5(WS_RE.sub("", body).encode()).hexdigest()))
    return out


def rate_driven_groups() -> set:
    """The RATE_DRIVEN DataDefGroups, read from 25_rating_vs_capture.py's output."""
    if os.environ.get("SIZE_ALL"):
        return set()
    p = os.path.join(HERE, "out", "rating_vs_capture.csv")
    if not os.path.exists(p):
        print("ERROR: run 25_rating_vs_capture.py first, or set SIZE_ALL=1",
              file=sys.stderr)
        sys.exit(2)
    import csv
    with open(p, encoding="utf-8", newline="") as fh:
        return {r["DataDefGroup"] for r in csv.DictReader(fh)
                if r["verdict"] == "RATE_DRIVEN"}


def main() -> int:
    dates = [a for a in sys.argv[1:] if len(a) == 8 and a.isdigit()]
    if not dates:
        print(__doc__)
        print("ERROR: an as-of date is REQUIRED (N4). There is no default.",
              file=sys.stderr)
        return 2

    pk = A.discover()
    keep = rate_driven_groups()
    print(f"sizing over {len(keep)} RATE_DRIVEN groups"
          if keep else "sizing over ALL matching groups (SIZE_ALL=1)")
    for asof in dates:
        resolved = {j: r for j in pk if j != "CW"
                    for r in [A.resolve(pk[j], asof)] if r}
        cw_all = {p: (e, c) for e, p, _x, c in pk["CW"]}
        parents = sorted({r[2] for r in resolved.values() if r[2] in cw_all})

        cw_rules = defaultdict(lambda: defaultdict(dict))  # parent -> grp -> name:digest
        cw_tables = defaultdict(set)                       # grp -> tables
        for p in parents:
            for grp, name, tabs, dig in scan_rules(cw_all[p][1]):
                cw_rules[p][grp][name] = dig
                cw_tables[grp] |= tabs

        st_rules: dict[str, Counter] = defaultdict(Counter)   # grp -> juris count
        st_names: dict[str, set] = defaultdict(set)
        for j, (_e, _p, _par, content) in resolved.items():
            for grp, name, tabs, _dig in scan_rules(content):
                st_rules[grp][j] += 1
                st_names[grp].add(name)
                cw_tables[grp] |= tabs

        print(f"\n{'=' * 96}\nPHASE SIZING AS OF {asof}   "
              f"({len(resolved)} jurisdictions, {len(parents)} countrywide parents "
              f"in force)\n{'=' * 96}")
        print(f"{'build-order item':<32}{'CW rules':>9}{'variants':>10}{'bodies differ':>15}"
              f"{'state rules':>12}{'juris':>7}{'tables':>8}{'populated':>11}")

        for label, keys in BUILD_ORDER:
            def _match(g):
                # A leading "=" means match the group name EXACTLY. Needed because
                # `GeneralLiabilityClassification` is a substring of six other
                # rate-driven group names — the same over-matching this column
                # exists to catch, committed inside the fix for it.
                return any(g == k[1:] if k.startswith("=") else k in g for k in keys)

            groups = sorted({g for p in parents for g in cw_rules[p] if _match(g)}
                            | {g for g in st_rules if _match(g)})
            if keep:
                groups = [g for g in groups if g in keep]
            merged = [{f"{g}/{n}": d for g in groups
                       for n, d in cw_rules[p][g].items()} for p in parents]
            per_parent = [len(x) for x in merged]
            ncw = max(per_parent) if per_parent else 0
            # A rule NAME surviving an edition proves nothing — compare bodies.
            nvar = len({tuple(sorted(x.items())) for x in merged}) if merged else 0
            base = merged[0] if merged else {}
            diff = max((sum(1 for k in base if base[k] != x.get(k)) for x in merged),
                       default=0)
            split = f"{nvar} of {len(parents)}"
            nst = sum(len(st_names[g]) for g in groups)
            njur = len({j for g in groups for j in st_rules[g]})
            tabs = {t for g in groups for t in cw_tables[g]}
            pop = 0
            for t in tabs:
                if any(A.table(r[3], "Rate Tables", t + ".RateTable.csv")
                       for r in resolved.values()):
                    pop += 1
            print(f"{label:<32}{ncw:>9}{split:>10}{diff:>15}{nst:>12}{njur:>7}"
                  f"{len(tabs):>8}{pop:>11}")

        print("\n  CW rules   distinct rule names in the countrywide parent, "
              "worst case across the parents in force")
        print("  variants   how many DISTINCT rule sets those parents hold — "
              "this is the number of calculators the phase must build")
        print("  bodies differ   rules whose body differs from the first parent's, "
              "worst case. Equal COUNTS do not mean equal rules")
        print("  state rules / juris   the deviation surface: distinct state rule "
              "names, and how many jurisdictions file one")
        print("  tables     distinct rate tables the rules read; 'populated' is how "
              "many any jurisdiction actually fills")
    return 0


if __name__ == "__main__":
    sys.exit(main())
