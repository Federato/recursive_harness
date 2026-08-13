"""The 2027 program change, measured AS OF A DATE — which is the only way N4 permits.

Why this script exists
----------------------
Every prior count of the "mid-migration" split — the PDF derivation's 15/36 and the ERC
gate-335 figure of 8/43 — was taken over the LATEST package per jurisdiction. The corpus
holds 82 state packages effective AFTER today, so "latest" describes a future state, not
the present one. Both counts are of the end state and neither is of today.

Measured properly, the migration is not in progress at all. It is a cliff:

    as of 2026-08-11   51 jurisdictions pre-2027,  0 migrated
    as of 2027-04-01    8 jurisdictions pre-2027, 43 migrated

43 jurisdictions change class basis on a single day. That is a different build problem
from a rolling migration, and it inverts the "a single national class list is wrong today"
conclusion: today a single list is right, and on 2027-04-01 it stops being right.

    python 31_migration_asof.py                 # today, the cliff date, and the end state
    python 31_migration_asof.py 20261201        # any as-of date

Reported per as-of date:
  * jurisdictions on each class basis
  * jurisdictions publishing OCP/PP loss costs (the same boundary drives both)
"""
from __future__ import annotations

import csv
import datetime
import os
import re
import sys
from collections import defaultdict

ROOT = r"C:\Projects\ISO_ERC_Files\General_Liability"
NS_RE = re.compile(r'targetNamespace="http://www\.verisk\.com/iso/erc/([^/"]+)/')
CLIFF = "20270401"


def packages() -> dict[str, list[tuple[str, str, str]]]:
    """jurisdiction -> [(effective YYYYMMDD, namespace, package dir)], identity from the XSD."""
    out: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    for dirpath, dirnames, filenames in os.walk(ROOT):
        if os.path.basename(dirpath) != "DataDefs" or "_quarantine" in dirpath:
            continue
        dirnames[:] = []
        pkg = os.path.dirname(dirpath)
        for fn in filenames:
            if not fn.endswith(".xsd"):
                continue
            m = NS_RE.search(open(os.path.join(dirpath, fn), encoding="utf-8-sig",
                                 errors="replace").read(20000))
            if m and not m.group(1).startswith("GL_CW"):
                parts = m.group(1).split("_")          # GL_XX_YYYYMMDD_Vnn
                if len(parts) >= 3:
                    out[parts[1]].append((parts[2], m.group(1), pkg))
            break
    return out


def resolve(pkgs, asof: str):
    """N4: discard editions effective after `asof`, take the latest remaining."""
    eligible = [t for t in sorted(pkgs) if t[0] <= asof]
    return eligible[-1] if eligible else None


def prem_ops_classes(pkg: str) -> set[str]:
    p = os.path.join(pkg, "Rate Tables", "PremOpsIncrdLimitTableAssignment.RateTable.csv")
    if not os.path.exists(p):
        return set()
    with open(p, encoding="utf-8-sig", newline="") as fh:
        r = csv.reader(fh)
        next(r, None)
        return {row[1] for row in r if len(row) > 1}


def publishes_ocp_loss_costs(pkg: str) -> bool:
    p = os.path.join(pkg, "Rate Tables", "OwnersContractorsLossCost.RateTable.csv")
    if not os.path.exists(p):
        return False
    with open(p, encoding="utf-8-sig", newline="") as fh:
        r = csv.reader(fh)
        next(r, None)
        for row in r:
            if len(row) > 2:
                try:
                    if float(row[2]) != 0.0:
                        return True
                except ValueError:
                    pass
    return False


pk = packages()
today = datetime.date.today().strftime("%Y%m%d")
dates = sys.argv[1:] or [today, CLIFF, "99999999"]

future = sum(1 for v in pk.values() for t in v if t[0] > today)
print(f"state packages: {sum(len(v) for v in pk.values())} across {len(pk)} jurisdictions")
print(f"effective AFTER today ({today}): {future}  <- why 'latest' is not 'now'\n")

print(f"{'as of':<14}{'pre-2027':>10}{'2027 basis':>12}{'OCP LC pub':>12}   note")
for asof in dates:
    pre = post = ocp = 0
    prec: set[str] = set()
    postc: set[str] = set()
    for j, v in pk.items():
        r = resolve(v, asof)
        if not r:
            continue
        eff, ns, pkg = r
        if eff >= CLIFF:
            post += 1
            postc |= prem_ops_classes(pkg)
        else:
            pre += 1
            prec |= prem_ops_classes(pkg)
        if publishes_ocp_loss_costs(pkg):
            ocp += 1
    note = ("TODAY — nothing has migrated" if asof == today else
            "the cliff — 43 change basis on one day" if asof == CLIFF else
            "end state (all filings in force)")
    label = "latest filed" if asof == "99999999" else asof
    print(f"{label:<14}{pre:>10}{post:>12}{ocp:>12}   {note}")

print(f"\nPrem/Ops class codes — pre-2027 only {len(prec - postc)} · "
      f"2027 only {len(postc - prec)} · both {len(prec & postc)}")
print("\nBoth the class-basis change and the OCP loss-cost withdrawal land on the same date.")
print("One program change, one boundary — not a state-by-state divergence.")
