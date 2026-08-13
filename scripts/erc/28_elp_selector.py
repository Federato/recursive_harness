"""The rating-basis selector: is `*ELPText` a closed vocabulary, and does it agree
with the `LossCost == 0` test the rating rules actually branch on?

Raised by the subline-336 gate (PROCESS_LOG Step 28). If the two ever disagree, an engine
that branches on `LossCost == 0` alone mis-rates silently.
"""
import os, csv, sys
from collections import Counter, defaultdict

ROOT = r"C:\Projects\ISO_ERC_Files\General_Liability"

TEXT_TABLES = ["PremOpsELPText", "ProdsCompldOpsELPText", "LiquorELPText",
               "OwnersContractorsELPText"]


def read(path):
    with open(path, encoding="utf-8-sig", newline="") as fh:
        r = csv.reader(fh)
        head = next(r, None)
        if head is None:
            return [], []
        return head, list(r)


def pkg_dirs():
    for dirpath, dirnames, _ in os.walk(ROOT):
        if os.path.basename(dirpath) == "Rate Tables" and "_quarantine" not in dirpath:
            yield dirpath
            dirnames[:] = []


vocab = defaultdict(Counter)
pkgs = 0
# agreement test, Prem/Ops: selector says "Rate/Loss Cost Applies" <-> a non-zero loss cost exists
agree = disagree = untestable = 0
examples = []

for rt in pkg_dirs():
    pkgs += 1
    for t in TEXT_TABLES:
        p = os.path.join(rt, t + ".RateTable.csv")
        if not os.path.exists(p):
            continue
        _, rows = read(p)
        for row in rows:
            if len(row) >= 3:
                vocab[t][row[2]] += 1

    # Prem/Ops agreement, per class code, within this package
    tp = os.path.join(rt, "PremOpsELPText.RateTable.csv")
    lp = os.path.join(rt, "PremOpsLossCost.RateTable.csv")
    if not (os.path.exists(tp) and os.path.exists(lp)):
        continue
    _, trows = read(tp)
    _, lrows = read(lp)
    if not trows or not lrows:
        continue
    # class -> set of loss cost values across territories
    lc = defaultdict(set)
    for row in lrows:
        if len(row) >= 4:
            try:
                lc[row[2]].add(float(row[3]))
            except ValueError:
                pass
    for row in trows:
        if len(row) < 3:
            continue
        cls, sel = row[1], row[2]
        if cls not in lc:
            untestable += 1
            continue
        has_rate = any(v != 0.0 for v in lc[cls])
        says_rate = (sel == "Rate/Loss Cost Applies")
        if has_rate == says_rate:
            agree += 1
        else:
            disagree += 1
            if len(examples) < 12:
                examples.append((os.path.basename(os.path.dirname(rt)), cls, sel,
                                 sorted(lc[cls])[:4]))

print(f"packages with Rate Tables: {pkgs}\n")
print("=== selector vocabulary (closed?) ===")
for t, c in vocab.items():
    print(f"\n{t}  ({sum(c.values()):,} rows, {len(c)} distinct)")
    for v, n in c.most_common():
        print(f"   {n:8,}  {v!r}")

print("\n=== Prem/Ops: selector vs. `LossCost != 0` ===")
tot = agree + disagree
print(f"  agree      {agree:,}")
print(f"  DISAGREE   {disagree:,}" + (f"  ({disagree/tot:.4%})" if tot else ""))
print(f"  untestable {untestable:,}  (class absent from the loss-cost table)")
for e in examples:
    print("   e.g.", e)
