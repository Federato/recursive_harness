"""OCP (subline 335): does the rating-basis selector explain every zero, and is
`Company` equivalent to the manual's Refer-To-Company marker?

Raised by the subline-335 gate (PROCESS_LOG Step 29). OCP is the strongest test of N17
available: its loss-cost table is ABSENT in 43 of 51 jurisdictions, so almost every risk
takes the ELP path, and an ELP of 0 on a refer class would produce a free policy.

Tests, per (jurisdiction, class) on the latest edition of each jurisdiction:
  A  selector == "Rate/Loss Cost Applies"  <->  a non-zero OwnersContractorsLossCost
  B  selector == "Company"                 <->  OwnersContractorsELP == 0
  C  selector == "Industry"                <->  OwnersContractorsELP != 0

Test B is the load-bearing one. The manual's ELP Supplement prints "RTC" for exactly the
classes ERC marks "Company" (GL-AK-2020-LC-001-C p.9, Table 5.C. OCP & PP ELPs), so
"Company" means refer-to-company, NOT "look up a company ELP".
"""
from __future__ import annotations

import csv
import os
import re
from collections import Counter, defaultdict

ROOT = r"C:\Projects\ISO_ERC_Files\General_Liability"
NS_RE = re.compile(r'targetNamespace="http://www\.verisk\.com/iso/erc/([^/"]+)/')


def latest_packages():
    best: dict[str, tuple[str, str]] = {}
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
                ns = m.group(1)
                j = ns.split("_")[1]
                if j not in best or ns > best[j][0]:
                    best[j] = (ns, pkg)
            break
    return best


def table(pkg: str, name: str) -> dict[str, str] | None:
    """class code -> value, for the (state, class, value) 3-column OCP tables."""
    p = os.path.join(pkg, "Rate Tables", name + ".RateTable.csv")
    if not os.path.exists(p):
        return None
    out = {}
    with open(p, encoding="utf-8-sig", newline="") as fh:
        r = csv.reader(fh)
        next(r, None)
        for row in r:
            if len(row) >= 3:
                out[row[1]] = row[2]
    return out


def num(x) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


best = latest_packages()
vocab = Counter()
A = Counter()
B = Counter()
C = Counter()
refer_classes: dict[str, set[str]] = defaultdict(set)
violations = []

for j, (ns, pkg) in sorted(best.items()):
    sel = table(pkg, "OwnersContractorsELPText")
    if not sel:
        continue
    lc = table(pkg, "OwnersContractorsLossCost") or {}
    elp = table(pkg, "OwnersContractorsELP") or {}
    for cls, s in sel.items():
        vocab[s] += 1
        has_lc = num(lc.get(cls)) != 0.0
        has_elp = num(elp.get(cls)) != 0.0

        ok_a = has_lc == (s == "Rate/Loss Cost Applies")
        A["agree" if ok_a else "DISAGREE"] += 1

        if s == "Company":
            refer_classes[j].add(cls)
            B["agree" if not has_elp else "DISAGREE"] += 1
            if has_elp:
                violations.append(("B", j, cls, s, elp.get(cls)))
        elif s == "Industry":
            if cls == "15191":
                # Not a table ELP at all: SetELP special-cases 15191 to
                # PrincipalsProtvLiabFactor x WorkersCompensationRate (a submission input).
                # A zero here is the third kind of zero, and the rules discriminate it by
                # class code. Counted separately so it stays visible rather than excused.
                C["input-derived (15191)"] += 1
            else:
                C["agree" if has_elp else "DISAGREE"] += 1
                if not has_elp:
                    violations.append(("C", j, cls, s, elp.get(cls)))
        if not ok_a:
            violations.append(("A", j, cls, s, lc.get(cls)))

print(f"jurisdictions with an OCP selector table: {sum(1 for j,(n,p) in best.items() if table(p,'OwnersContractorsELPText'))}"
      f" of {len(best)}\n")
print(f"selector vocabulary: {dict(vocab)}  ({sum(vocab.values()):,} rows)\n")
for lbl, c in (("A  selector 'Rate/Loss Cost Applies' <-> non-zero loss cost", A),
               ("B  selector 'Company'                <-> ELP == 0  (refer)", B),
               ("C  selector 'Industry'               <-> ELP != 0", C)):
    tot = sum(c.values())
    extra = c.get("input-derived (15191)", 0)
    print(f"{lbl}\n     agree {c['agree']:,}   DISAGREE {c['DISAGREE']:,}"
          + (f"   input-derived via class 15191 {extra}" if extra else "")
          + f"   of {tot:,}")
print()
if violations:
    print("VIOLATIONS:")
    for v in violations[:25]:
        print("   ", v)
else:
    print("no violations — the selector explains every zero in the OCP tables")

n_ref = sum(len(v) for v in refer_classes.values())
print(f"\nrefer-to-company (state, class) pairs: {n_ref} across "
      f"{len(refer_classes)} jurisdictions")
allc = Counter()
for v in refer_classes.values():
    allc.update(v)
print("  most common refer classes:", allc.most_common(8))
