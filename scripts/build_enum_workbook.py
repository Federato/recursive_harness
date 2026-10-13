"""Stage 5: the enum workbook -- every field a payload can carry, and its
legal values, from ISO's own filings.

The build plan expected the hard part to be **scope, not extraction** -- *"which
of 1,906 fields a payload actually needs, and we expect the 53 real submissions
to answer that better than the corpus does"*. That prediction held, and the
numbers are the reason this workbook is worth having:

* ISO declares **~1,280 fields** for a jurisdiction
* the 50 real submissions between them use **77**
* **41** are used by all 50; a single submission carries **43-54**

**The 50 real submissions between them use 6% of the declared surface, and any
single one uses about 3%.** A workbook that
lists 1,280 fields and stops has answered the wrong question; this one says
which of them anyone has ever sent.

Every column comes from filed content, and the `Read me` sheet says which file:

| Source | Gives |
|---|---|
| `Form Fields/Fields.FormField.csv` | the field, its control, requiredness, condition, its domain |
| `Domain Tables/` | the legal values (`DataValue`) |
| `Form Related Fields/` | which fields have a dependency ISO declares |
| `Ratebook Columns/` | required **to rate**, as opposed to required on a form |
| `DOC/*.xlsx` -> `Base RaaS Overrides` | the **data type** |
| `DOC/*.xlsx` -> `Class Description - CGL` | class codes and descriptions |
| `Payloads/` | how many of the 50 real submissions use the field |

    python scripts/build_enum_workbook.py
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from xlsx import Workbook                                     # noqa: E402
from gl_engine import EditionResolver, ResolvedBook           # noqa: E402
from gl_engine.interp import tree                             # noqa: E402
from gl_engine.rating.submission import from_raas             # noqa: E402
from gl_engine.schema import Schema                           # noqa: E402
from gl_engine.schema.validate import _walk, PLACE_CODED      # noqa: E402

OUT = ROOT / "GL-Submission-Fields.xlsx"
PAYLOADS = ROOT / "Payloads"
ASOF = "20260801"
#: The jurisdiction whose declared surface is the master list. Countrywide is
#: the base every state overrides, so it is the right spine for the workbook.
SPINE = "CW"
#: Domains larger than this are summarised rather than listed -- ZipCode alone
#: is 765 values and is a lookup, not a choice a human makes.
MAX_VALUES = 60

OUT_DIR = ROOT / "scripts" / "erc" / "out"


def used_by_submissions():
    """(table, column) -> how many of the 50 real submissions carry it."""
    used = Counter()
    where = defaultdict(set)
    for d in sorted(p for p in PAYLOADS.iterdir() if p.is_dir()):
        src = d / "1. Input.json"
        if not src.exists():
            continue
        root, _, _ = from_raas(json.loads(src.read_text(encoding="utf-8-sig")))
        leaves = []
        for risk in tree.select("GeneralLiabilityTable/GeneralLiability", root):
            _walk(risk, "GeneralLiability", leaves)
        for t, c, _n in leaves:
            used[(t, c)] += 1
            where[(t, c)].add(d.name)
    return used, where


def doc_rows(name: str) -> list:
    """A sheet already extracted from the DOC workbooks by script 49."""
    p = OUT_DIR / name
    if not p.exists():
        return []
    return list(csv.DictReader(open(p, encoding="utf-8")))


def main() -> int:
    resolver = EditionResolver()
    used, used_where = used_by_submissions()
    spine = Schema.for_book(ResolvedBook(resolver.resolve(SPINE, ASOF)))

    types = {}
    for r in doc_rows("doc_types.csv"):
        if r["table"] and r["column"]:
            types.setdefault((r["table"], r["column"]), r["data_type"])

    wb = Workbook()

    # ---------------------------------------------------------------- read me
    wb.sheet("Read me", ["", ""], [
        ["GL Submission Fields", ""],
        ["", ""],
        ["What this is",
         "Every field a General Liability submission can carry, and its legal "
         "values, taken from ISO's own filed content."],
        ["Nothing here is our opinion",
         "Each column names the ISO file it came from. No field, value or type "
         "was invented or inferred."],
        ["", ""],
        ["The number that matters", ""],
        ["ISO declares (countrywide)", len(spine)],
        ["Used by the 50 real ISO submissions", len(used)],
        ["Used by all 50", sum(1 for v in used.values() if v == 50)],
        ["A single submission carries", "43 to 54 fields"],
        ["So a real submission uses",
         "6% of the declared surface -- see the 'Used in practice' sheet"],
        ["", ""],
        ["Sheets", ""],
        ["Used in practice",
         "the fields real submissions actually carry, most common first. Start here"],
        ["All fields",
         "every field ISO declares countrywide, with requiredness, type and domain"],
        ["Legal values",
         f"the permitted values, for domains of {MAX_VALUES} or fewer; larger "
         f"ones are summarised"],
        ["By jurisdiction",
         "field counts per state, what each adds, and the four that code "
         "terrorism territory explicitly"],
        ["Class codes", "class codes and descriptions, from ISO's DOC workbook"],
        ["", ""],
        ["Sources", ""],
        ["Fields, requiredness, domain", "Form Fields/Fields.FormField.csv"],
        ["Legal values", "Domain Tables/ (the DataValue column)"],
        ["Declared dependencies", "Form Related Fields/RelatedFields.FormField.csv"],
        ["Required to rate", "Ratebook Columns/RatebookColumns.FormPage.csv"],
        ["Data types", "DOC/*.xlsx -> Base RaaS Overrides"],
        ["Class codes", "DOC/*.xlsx -> Class Description - CGL"],
        ["Real usage", "the 50 ISO-priced example submissions"],
        ["", ""],
        ["Regenerate", "python scripts/build_enum_workbook.py"],
        ["Corpus", f"570 packages; spine {SPINE} as of {ASOF}"],
    ])

    # ------------------------------------------------------- used in practice
    rows = []
    for (t, c), n in used.most_common():
        f = spine.get(t, c)
        vals = spine.legal_values(t, c) if f else ()
        rows.append([
            t, c, n, round(100 * n / 50),
            f.control if f else "(not declared countrywide)",
            types.get((t, c), ""),
            "yes" if f and f.policy_required else "",
            "yes" if f and f.rating_required else "",
            f.domain if f else "",
            len(vals) if vals else "",
            ", ".join(sorted(used_where[(t, c)])[:6])
            + (" ..." if len(used_where[(t, c)]) > 6 else ""),
        ])
    wb.sheet("Used in practice",
             ["table", "field", "submissions using it", "% of 50", "control",
              "data type", "required", "required to rate", "domain table",
              "legal values", "jurisdictions"], rows)

    # ------------------------------------------------------------- all fields
    rows = []
    for f in sorted(spine, key=lambda x: (x.table, x.column)):
        vals = spine.legal_values(f.table, f.column)
        deps = spine.dependency_columns(f.table, f.column)
        rows.append([
            f.table, f.column, f.label, f.control,
            types.get((f.table, f.column), ""),
            "yes" if f.policy_required else "",
            "yes" if f.conditional else "",
            "yes" if f.rating_required else "",
            f.domain, len(vals) if vals else "",
            ", ".join(deps) if deps else "",
            "declared" if spine.related_path(f.table, f.column)
            else ("NOT declared" if deps else ""),
            f.default, f.minimum, f.maximum,
            used.get((f.table, f.column), 0),
        ])
    wb.sheet("All fields",
             ["table", "field", "label", "control", "data type", "required",
              "conditional", "required to rate", "domain table",
              "legal values", "depends on", "dependency", "default", "min",
              "max", "used by N of 50"], rows)

    # ----------------------------------------------------------- legal values
    rows, big = [], []
    for f in sorted(spine, key=lambda x: (x.table, x.column)):
        if not f.domain:
            continue
        vals = spine.legal_values(f.table, f.column)
        if not vals:
            continue
        if len(vals) > MAX_VALUES:
            big.append([f.table, f.column, f.domain, len(vals),
                        ", ".join(vals[:5]) + " ..."])
            continue
        for v in vals:
            rows.append([f.table, f.column, f.domain, v,
                         used.get((f.table, f.column), 0)])
    wb.sheet("Legal values",
             ["table", "field", "domain table", "legal value",
              "used by N of 50"], rows)
    wb.sheet("Large domains",
             ["table", "field", "domain table", "how many values", "first few"],
             big)

    # --------------------------------------------------------- by jurisdiction
    rows = []
    spine_keys = {(f.table, f.column) for f in spine}
    for j in sorted({p.identity.juris for p in resolver.packages
                     if p.identity.juris != "CW"}):
        try:
            s = Schema.for_book(ResolvedBook(resolver.resolve(j, ASOF)))
        except Exception as exc:                            # noqa: BLE001
            rows.append([j, "", "", "", "", f"{type(exc).__name__}"])
            continue
        keys = {(f.table, f.column) for f in s}
        rows.append([
            j, len(s), len(s.required()), len(s.rating_required()),
            len(keys - spine_keys),
            "explicit TerrorismTerritoryCode" if j in PLACE_CODED else "",
        ])
    wb.sheet("By jurisdiction",
             ["jurisdiction", "fields", "required", "required to rate",
              "fields not in countrywide", "note"], rows)

    # ------------------------------------------------------------- class codes
    rows = []
    seen = set()
    for r in doc_rows("doc_class_codes.csv"):
        key = (r.get("code"), r.get("description"))
        if key in seen or not key[0]:
            continue
        seen.add(key)
        rows.append([r.get("juris", ""), r.get("code"), r.get("description")])
    if rows:
        wb.sheet("Class codes", ["jurisdiction", "class code", "description"],
                 rows)

    path = wb.save(OUT)
    print(f"WROTE {path}  ({path.stat().st_size:,} bytes)")
    print()
    print(f"    ISO declares (countrywide)      : {len(spine)} fields")
    print(f"    used by the 50 real submissions : {len(used)}")
    print(f"    used by all 50                  : "
          f"{sum(1 for v in used.values() if v == 50)}")
    print(f"    class codes listed              : {len(rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
