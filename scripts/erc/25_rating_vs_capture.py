#!/usr/bin/env python
"""Corpus-wide verification of the rating-vs-capture split.

Classifies every rule that writes a Premium across all ERC packages:

  RATE_DRIVEN  computes from a rate/loss cost/ELP   -> the engine must implement the algorithm
  CAPTURE      Premium = ManualPremium x factor(s)  -> the engine validates and aggregates
  OTHER        writes Premium some other way        -> inspect individually

Counts distinct DataDefGroups (coverage units), not rule instances, since the same
group repeats across 567 packages.

    python scripts/erc/25_rating_vs_capture.py

Produces out/rating_vs_capture.csv and a summary on stdout.
"""
import os, re, sys, csv, json
from collections import defaultdict, Counter
from concurrent.futures import ProcessPoolExecutor

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = r"C:\Projects\ISO_ERC_Files\General_Liability"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")

RULE = re.compile(r'<rul:Rule Name="([^"]+)"[^>]*?DataDefGroup="([^"]+)"[^>]*?'
                  r'(?:MetadataCodes="([^"]*)")?[^>]*>(.*?)</rul:Rule>', re.S)
WRITES_PREM = re.compile(r'ToDataDef="((?:[A-Za-z]*)Premium)"')
# `AdjustedRate` was MISSING from this list until 2026-08-11 and its absence
# misclassified two real rating paths as aggregators — the two Unmanned Aircraft
# coverages, which compute `Premium = AdjustedRate x ILF x mods` and were reported
# as 'OTHER' for that reason alone. The headline was 16/383/78; it is 18/383/76.
# Any addition here must be justified by reading the rule body that motivated it.
RATE_SRC = re.compile(r'From(?:DataDef|Constant)="[^"]*'
                      r'(FinalRate|BaseRate|LossCost|ELP|AdjustedBaseRate|AdjustedRate)')
MANUAL = re.compile(r'FromDataDef="(?:\.\./)*ManualPremium"')


def scan(pkgdir):
    res = []
    for f in [p for p in _rulefiles(pkgdir)]:
        try:
            t = open(f, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        for name, grp, meta, body in RULE.findall(t):
            targets = set(WRITES_PREM.findall(body))
            if not targets:
                continue
            has_rate = bool(RATE_SRC.search(body))
            has_manual = bool(MANUAL.search(body))
            if has_rate:
                cls = "RATE_DRIVEN"
            elif has_manual:
                cls = "CAPTURE"
            else:
                cls = "OTHER"
            res.append((grp, name, cls, meta or "", sorted(targets)[0]))
    return res


def _rulefiles(pkgdir):
    for dp, dn, fn in os.walk(pkgdir):
        if os.path.basename(dp) == "Rules":
            for f in fn:
                if f.endswith(".xml"):
                    yield os.path.join(dp, f)


def packages():
    out = []
    for st in sorted(os.listdir(ROOT)):
        d = os.path.join(ROOT, st)
        if not os.path.isdir(d) or st == "_quarantine_misfiled":
            continue
        for p in sorted(os.listdir(d)):
            pp = os.path.join(d, p)
            if os.path.isdir(pp):
                out.append(pp)
    return out


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    pkgs = packages()
    print(f"scanning {len(pkgs)} package directories ...", flush=True)

    grp_cls = defaultdict(Counter)      # DataDefGroup -> class counts
    grp_pkgs = defaultdict(set)         # DataDefGroup -> packages carrying it
    rows = 0
    with ProcessPoolExecutor(max_workers=10) as ex:
        for i, res in enumerate(ex.map(scan, pkgs, chunksize=4)):
            pkg = pkgs[i]
            for grp, name, cls, meta, tgt in res:
                grp_cls[grp][cls] += 1
                grp_pkgs[grp].add(pkg)
                rows += 1
            if i % 100 == 0:
                print(f"  {i}/{len(pkgs)}", flush=True)

    # a group is RATE_DRIVEN if ANY package rates it
    verdict = {}
    for g, c in grp_cls.items():
        verdict[g] = ("RATE_DRIVEN" if c["RATE_DRIVEN"] else
                      "CAPTURE" if c["CAPTURE"] else "OTHER")

    tally = Counter(verdict.values())
    print(f"\n  premium-writing rule instances scanned: {rows:,}")
    print(f"  distinct DataDefGroups writing a Premium: {len(verdict)}")
    for k in ("RATE_DRIVEN", "CAPTURE", "OTHER"):
        print(f"    {k:12} {tally[k]:>5}")

    print("\n=== RATE_DRIVEN coverage groups (the engine must implement these) ===")
    for g in sorted(v for v in verdict if verdict[v] == "RATE_DRIVEN"):
        print(f"   {g[:76]:78} {len(grp_pkgs[g]):>4} pkgs")

    print("\n=== OTHER (inspect) ===")
    for g in sorted(v for v in verdict if verdict[v] == "OTHER")[:20]:
        print(f"   {g[:76]:78} {len(grp_pkgs[g]):>4} pkgs")

    with open(os.path.join(OUT, "rating_vs_capture.csv"), "w",
              newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["DataDefGroup", "verdict", "rate_driven_rules",
                    "capture_rules", "other_rules", "packages"])
        for g in sorted(verdict):
            c = grp_cls[g]
            w.writerow([g, verdict[g], c["RATE_DRIVEN"], c["CAPTURE"],
                        c["OTHER"], len(grp_pkgs[g])])
    print(f"\nwrote {os.path.join(OUT,'rating_vs_capture.csv')}")
