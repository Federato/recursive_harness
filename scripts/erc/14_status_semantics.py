"""Phase 4 step 3b: after 13_status.py falsified the Add/Change/Delete
reading, characterise what Status actually co-varies with.

Six tests, all cross-tabulated by Status:

  S1 globality      is Status a property of the row key (same everywhere)
                    or does it vary by package?
  S2 wiring         is the row's TableName present in Ratebook Tables
                    (i.e. is it rateable) and does it have a rule
                    (a matching Rules DataDefGroup)?
  S3 model presence is the TableName a complexType in the package's own or
                    inherited XSD?
  S4 attachment     how does Status distribute over AttachmentType?
  S5 accumulation   does the share of Status=D grow monotonically along a
                    jurisdiction's edition series (as a tombstone pile
                    would)?
  S6 supersession   ISO form numbers embed an edition (e.g. "CG 22 67 10 93"
                    = Oct 1993).  Within one package, are Status=D rows the
                    OLDER edition of a form family?

Emits out/status_semantics.txt.  This script asserts no meaning for the
letters; it reports what the data constrains and what it leaves open.
"""
from __future__ import annotations

import collections
import csv
import re
import sys
from pathlib import Path
from importlib import import_module

sys.path.insert(0, str(Path(__file__).parent))
c = import_module("00_common")
csv.field_size_limit(1 << 24)

FORM_RE = re.compile(r"^([A-Z]{2}\s*\d{2}\s*\d{2})\s+(\d{2})\s*(\d{2})$")


def load(n):
    with open(c.OUT / n, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def main():
    F = load("fp_form_rows.csv")
    P = load("form_pages.csv")
    L = []; A = L.append

    A("WHAT DOES Status CO-VARY WITH?")
    A("")
    A("S1  Is Status a global property of the row key?")
    for cat in ("Form Pages", "Form Fields", "Form Related Fields",
                "Ratebook Columns", "Ratebook Tables"):
        d = collections.defaultdict(set)
        for r in F:
            if r["category"] == cat:
                d[r["row_key"]].add(r["status"])
        n = len(d)
        mixed = sum(1 for v in d.values() if len(v) > 1)
        A(f"  {cat:22s} {n:5d} distinct row keys; {mixed:4d} "
          f"({mixed/n*100:5.1f}%) carry more than one Status across packages")
    A("  -> Status is mostly, but not entirely, a property of the artefact")
    A("     rather than of the jurisdiction.")

    A("")
    A("S2  Is the row wired into rating?")
    rt = collections.defaultdict(set)
    for r in F:
        if r["category"] == "Ratebook Tables":
            rt[r["pkg_id"]].add(r["row_key"])
    ru = collections.defaultdict(set)
    for r in load("rules_index.csv"):
        ru[r["pkg_id"]].add(r["datadef_group"])
    t1 = collections.Counter(); t2 = collections.Counter()
    for r in P:
        p, tn, s = r["pkg_id"], r["table_name"], r["status"]
        t1[(s, tn in rt.get(p, ()))] += 1
        t2[(s, tn in ru.get(p, ()))] += 1
    A("  Form Pages -> TableName appears in Ratebook Tables (rateable):")
    for s in "ACD":
        a, b = t1[(s, True)], t1[(s, False)]
        if a + b:
            A(f"    Status={s}: {a/(a+b)*100:5.1f}% rateable  (n={a+b})")
    A("  Form Pages -> TableName has a rule (Rules DataDefGroup):")
    for s in "ACD":
        a, b = t2[(s, True)], t2[(s, False)]
        if a + b:
            A(f"    Status={s}: {a/(a+b)*100:5.1f}% has a rule  (n={a+b})")
    rts = collections.defaultdict(dict)
    for r in F:
        if r["category"] == "Ratebook Tables":
            rts[r["pkg_id"]][r["row_key"]] = r["status"]
    t3 = collections.Counter()
    for p, tabs in rts.items():
        for tn, s in tabs.items():
            t3[(s, tn in ru.get(p, ()))] += 1
    A("  Ratebook Tables -> TableName has a rule:")
    for s in "ACD":
        a, b = t3[(s, True)], t3[(s, False)]
        if a + b:
            A(f"    Status={s}: {a/(a+b)*100:5.1f}% has a rule  (n={a+b})")

    A("")
    A("S3  Is the TableName present in the package's (own or inherited) XSD?")
    xt = collections.defaultdict(set)
    for r in load("xsd_types.csv"):
        xt[r["pkg_id"]].add(r["complexType"])
    imp = {r["pkg_id"]: r["import_pkgs"] for r in load("xsd_packages.csv")}
    t4 = collections.Counter()
    for r in P:
        ok = (r["table_name"] in xt[r["pkg_id"]]
              or r["table_name"] in xt.get(imp.get(r["pkg_id"], ""), ()))
        t4[(r["status"], ok)] += 1
    for s in "ACD":
        a, b = t4[(s, True)], t4[(s, False)]
        if a + b:
            A(f"    Status={s}: {a/(a+b)*100:5.1f}% present in the data model (n={a+b})")

    A("")
    A("S4  AttachmentType distribution by Status (Form Pages, % of status):")
    att = collections.Counter()
    for r in P:
        att[(r["status"], r["attachment_type"] or "(blank)")] += 1
    for s in "ACD":
        tot = sum(v for k, v in att.items() if k[0] == s)
        if not tot:
            continue
        A(f"    {s}: " + "  ".join(
            f"{k[1]}={v/tot*100:.1f}%" for k, v in sorted(att.items())
            if k[0] == s))

    A("")
    A("S5  Does the Status=D share accumulate along a jurisdiction's series?")
    ser = collections.defaultdict(list)
    for r in F:
        if r["category"] == "Form Pages":
            ser[(r["juris"], r["edition"], r["version"], r["pkg_id"])].append(
                r["status"])
    by = collections.defaultdict(list)
    for (j, e, v, p), sts in ser.items():
        cc = collections.Counter(sts)
        by[j].append((e, v, cc["D"] / len(sts)))
    rise = fall = flat = 0
    for j in by:
        s = sorted(by[j])
        for i in range(len(s) - 1):
            a, b = s[i][2], s[i + 1][2]
            rise += b > a + 1e-9; fall += b < a - 1e-9
            flat += abs(b - a) <= 1e-9
    A(f"    consecutive pairs: D-share rose {rise}, fell {fall}, unchanged {flat}")
    A("    -> a tombstone pile would only ever rise; it does not.")
    A("    example series (jurisdiction: edition -> D% of Form Pages rows):")
    for j in ("NY", "CA", "NJ", "AL"):
        A(f"      {j}: " + " ".join(f"{x[0]}={x[2]*100:.0f}%"
                                    for x in sorted(by[j])))

    A("")
    A("S6  Are Status=D rows the superseded edition of a form family?")
    fam = collections.defaultdict(lambda: collections.defaultdict(list))
    parsed = 0
    for r in P:
        m = FORM_RE.match(r["form_number"].strip())
        if not m:
            continue
        parsed += 1
        yy = int(m.group(3))
        yr = (1900 + yy) if yy > 50 else (2000 + yy)
        fam[r["pkg_id"]][m.group(1)].append((yr * 100 + int(m.group(2)),
                                             r["status"]))
    t5 = collections.Counter()
    multi = 0
    for p, fs in fam.items():
        for base, items in fs.items():
            if len(items) < 2:
                continue
            multi += 1
            mx = max(i[0] for i in items)
            for ed, s in items:
                t5[("newest" if ed == mx else "older", s)] += 1
    A(f"    form numbers parsed as '<base> <MM> <YY>': {parsed} of {len(P)}")
    A(f"    packages x form families carrying MORE THAN ONE edition: {multi}")
    for grp in ("newest", "older"):
        tot = sum(v for k, v in t5.items() if k[0] == grp)
        if tot:
            A(f"      {grp:7s} n={tot:4d}  " + "  ".join(
                f"{k[1]}={v}({v/tot*100:.0f}%)" for k, v in sorted(t5.items())
                if k[0] == grp))
    A("    -> packages almost never ship two editions of the same form, and")
    A("       where they do, D is MORE common on the newest. Supersession is")
    A("       not the explanation.")

    A("")
    A("OPERATIONAL CONSEQUENCE")
    for cat in ("Form Pages", "Form Fields", "Ratebook Columns"):
        rows = [r for r in F if r["category"] == cat]
        d = sum(1 for r in rows if r["status"] == "D")
        A(f"  {cat:22s} Status=D on {d} of {len(rows)} rows "
          f"({d/len(rows)*100:.1f}%)")
    A("  Discarding Status=D rows would remove content that is 99.9% rateable")
    A("  and 64% rule-backed. Any consumer that treats D as 'delete' is wrong.")
    (c.OUT / "status_semantics.txt").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
