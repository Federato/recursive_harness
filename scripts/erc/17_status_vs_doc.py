"""Phase 4 step 6: does Status track the DOC exception register?

14_status_semantics.py left one hypothesis untested: that Status=C marks
content the package does not automate, which would make it the row-level
counterpart of the DOC workbook's "Refer to Company" / "Not Supported"
sheets.

This joins the two, within each package, on the ISO form number.  Form
numbers are normalised by removing whitespace and upper-casing, then
matched on the first six characters (the form family, e.g. "CG2267"),
because the DOC sheets cite a form as "CG 22 67" while Form Pages cites
the dated edition "CG 22 67 10 93".

Emits out/status_vs_doc.txt: the Status distribution of form pages whose
form family IS vs IS NOT cited in each exception sheet, with the lift.
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


def norm(s: str) -> str:
    return re.sub(r"\s+", "", s or "").upper()


def main():
    with open(c.OUT / "doc_exceptions.csv", encoding="utf-8", newline="") as fh:
        E = list(csv.DictReader(fh))
    with open(c.OUT / "form_pages.csv", encoding="utf-8", newline="") as fh:
        P = list(csv.DictReader(fh))

    exc = collections.defaultdict(lambda: collections.defaultdict(set))
    for e in E:
        fn = norm(e["c3"])
        if len(fn) >= 6:
            exc[e["pkg_id"]][e["sheet"]].add(fn[:6])

    tot = collections.Counter()
    matched = collections.Counter()
    for r in P:
        fn = norm(r["form_number"])
        if len(fn) < 6:
            continue
        d = exc.get(r["pkg_id"], {})
        for sheet, tag in (("Refer to Company", "RtC"),
                           ("Not Supported", "NS"),
                           ("Special Consideration", "SC")):
            hit = fn[:6] in d.get(sheet, ())
            tot[((tag if hit else "no" + tag), r["status"])] += 1
            matched[tag] += hit

    L = []; A = L.append
    A("DOES Status TRACK THE DOC EXCEPTION REGISTER?")
    A(f"  form pages with a parseable form number: "
      f"{sum(1 for r in P if len(norm(r['form_number'])) >= 6)} of {len(P)}")
    A(f"  packages with an exception register: {len(exc)}")
    A("")
    A(f"  {'group':8} {'n':>7}   A       C       D")
    for grp in ("RtC", "noRtC", "NS", "noNS", "SC", "noSC"):
        n = sum(v for k, v in tot.items() if k[0] == grp)
        if not n:
            continue
        A(f"  {grp:8} {n:7d} " +
          "  ".join(f"{s}={tot[(grp, s)]/n*100:5.1f}%" for s in "ACD"))
    A("")
    A("  LIFT (cited / not cited), per sheet and status:")
    for tag in ("RtC", "NS", "SC"):
        n1 = sum(v for k, v in tot.items() if k[0] == tag)
        n0 = sum(v for k, v in tot.items() if k[0] == "no" + tag)
        if not n1 or not n0:
            continue
        A(f"    {tag} (n cited={n1}):  " + "  ".join(
            f"{s}={(tot[(tag,s)]/n1)/(tot[('no'+tag,s)]/n0):.2f}x"
            if tot[("no" + tag, s)] else f"{s}=n/a" for s in "ACD"))
    A("")
    A("READING")
    A("  A form family cited in 'Refer to Company' is about twice as likely to")
    A("  carry Status=C, and roughly forty times LESS likely to carry Status=D,")
    A("  than one that is not cited. So C is enriched among content the package")
    A("  declines to rate automatically - but only mildly, and the majority of")
    A("  cited forms are still Status=A. 'Not Supported' matches too few form")
    A("  numbers to support any inference.")
    A("  This is evidence, not a determination: it further undermines any")
    A("  reading of D as 'withdrawn/unsupported' (D is DEPLETED among flagged")
    A("  forms), without establishing what C means.")
    (c.OUT / "status_vs_doc.txt").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
