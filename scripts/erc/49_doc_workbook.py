"""Rule #1's payoff: the DOC workbook ISO ships in every package.

`48_directory_census.py` found five directories the engine had never opened.
`DOC` is the largest prize: **one Excel workbook per package**, with six sheets,
and at least three of them answer questions this project derived the hard way.

  Refer to Company     ISO's OWN declared refer conditions, with the manual
                       rule number, the form number, a description and
                       "Customer Implementation Guidelines". The referral
                       register was derived from the rules and the manuals;
                       **this is ISO stating it directly**
  Not Supported        what ISO's machine-readable content does not do
  Special Consideration caveats with implementation guidance
  Base RaaS Overrides  TABLE, COLUMN, **DATA TYPE**, STATE / COUNTRYWIDE --
                       the data types stage 4 said would have to come from the
                       DataDefs
  Full Form Name       form titles per table

Read with the standard library only: an .xlsx is a zip of XML.

Emits out/doc_workbook.txt, out/doc_refer.csv, out/doc_types.csv.
"""
from __future__ import annotations

import csv
import sys
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
c = import_module("00_common")
rules_packages = import_module("42_node_surface").rules_packages

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
RNS = "{http://schemas.openxmlformats.org/package/2006/relationships}"
RID = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"


def sheets(path: Path) -> dict:
    """Every sheet in an .xlsx, as {name: [[cell, ...], ...]}."""
    z = zipfile.ZipFile(path)
    shared = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall(f"{NS}si"):
            shared.append("".join(t.text or "" for t in si.iter(f"{NS}t")))
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    relmap = {r.get("Id"): r.get("Target")
              for r in rels.findall(f"{RNS}Relationship")}
    out = {}
    for sh in wb.find(f"{NS}sheets"):
        tgt = relmap[sh.get(RID)].lstrip("/")
        p = tgt if tgt.startswith("xl/") else "xl/" + tgt
        rows = []
        for row in ET.fromstring(z.read(p)).iter(f"{NS}row"):
            cells = []
            for cell in row.findall(f"{NS}c"):
                t = cell.get("t")
                if t == "inlineStr":
                    # An inline string carries its text in <is><t>, not <v>.
                    # Reading only <v> silently returns blank for every string
                    # cell -- which is exactly what it did the first time.
                    node = cell.find(f"{NS}is")
                    txt = "".join(x.text or "" for x in node.iter(f"{NS}t"))                         if node is not None else ""
                else:
                    v = cell.find(f"{NS}v")
                    txt = "" if v is None else (
                        shared[int(v.text)] if t == "s" else v.text)
                cells.append((txt or "").strip())
            if any(cells):
                rows.append(cells)
        out[sh.get("name")] = rows
    return out


def main() -> None:
    pkgs, _, _ = rules_packages()
    sheet_names = Counter()
    refer_rows, type_rows = [], []
    not_supported, special, class_rows = [], [], []
    n_docs = 0
    per_sheet_rows = defaultdict(list)

    for pk in pkgs:
        d = pk.content / "DOC"
        if not d.is_dir():
            continue
        files = [f for f in d.iterdir() if f.suffix.lower() == ".xlsx"]
        if not files:
            continue
        n_docs += 1
        try:
            sh = sheets(files[0])
        except Exception:                                 # noqa: BLE001
            continue
        for name, rows in sh.items():
            sheet_names[name] += 1
            per_sheet_rows[name].append(max(0, len(rows) - 1))
            body = rows[1:] if rows else []
            if name == "Refer to Company":
                for r in body:
                    refer_rows.append([pk.juris, pk.pkg_id] + r[:5])
            elif name == "Not Supported":
                for r in body:
                    not_supported.append([pk.juris] + r[:5])
            elif name == "Special Consideration":
                for r in body:
                    special.append([pk.juris] + r[:4])
            elif name == "Base RaaS Overrides":
                for r in body:
                    type_rows.append([pk.juris] + r[:5])
            elif name.startswith("Class Description"):
                # (code, description) in either order depending on the sheet;
                # the code is the numeric one.
                for r in body:
                    cells = [x for x in r[:3] if x]
                    if len(cells) < 2:
                        continue
                    code = next((x for x in cells if x.replace(",", "").isdigit()), "")
                    desc = next((x for x in cells if x != code), "")
                    if code:
                        class_rows.append([pk.juris, name, code, desc])

    for fname, header, rows in (
        ("doc_refer.csv",
         ["juris", "pkg", "rule_number", "rule_name", "form_number",
          "description", "guidelines"], refer_rows),
        ("doc_types.csv",
         ["juris", "table", "column", "data_type", "state", "countrywide"],
         type_rows),
        ("doc_class_codes.csv", ["juris", "sheet", "code", "description"],
         class_rows),
    ):
        with open(c.OUT / fname, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(header)
            w.writerows(rows)

    L = []; A = L.append
    A("THE DOC WORKBOOK ISO SHIPS IN EVERY PACKAGE")
    A("")
    A(f"    packages with a DOC workbook: {n_docs} of {len(pkgs)}")
    A("")
    A("W1  SHEETS")
    A(f"    {'sheet':26s} {'pkgs':>5s} {'rows: min..max':>16s}")
    for name, n in sheet_names.most_common():
        v = sorted(per_sheet_rows[name])
        A(f"    {name:26s} {n:5d} {v[0]:7d}..{v[-1]:<7d}")
    A("")
    A("W2  REFER TO COMPANY -- ISO's own declared refer conditions")
    A(f"    total rows across the corpus: {len(refer_rows)}")
    by_rule = Counter(r[2] for r in refer_rows)
    A(f"    distinct manual rule numbers: {len(by_rule)}")
    for k, n in by_rule.most_common(12):
        A(f"      {k:22s} {n}")
    by_j = Counter(r[0] for r in refer_rows)
    A(f"    jurisdictions declaring at least one: {len(by_j)}")
    names = Counter(r[3] for r in refer_rows)
    A("    rule names:")
    for k, n in names.most_common(10):
        A(f"      {k[:60]:60s} {n}")
    A("")
    A("W3  NOT SUPPORTED")
    A(f"    total rows: {len(not_supported)}  "
      f"jurisdictions: {len(Counter(r[0] for r in not_supported))}")
    for k, n in Counter(r[2] for r in not_supported).most_common(8):
        A(f"      {k[:64]:64s} {n}")
    A("")
    A("W4  SPECIAL CONSIDERATION")
    A(f"    total rows: {len(special)}  "
      f"jurisdictions: {len(Counter(r[0] for r in special))}")
    A("")
    A("W5  CLASS DESCRIPTIONS")
    A(f"    rows: {len(class_rows)}   distinct codes: "
      f"{len({r[2] for r in class_rows})}")
    A("")
    A("W6  BASE RAAS OVERRIDES -- the DATA TYPES")
    A(f"    total rows: {len(type_rows)}")
    A(f"    distinct (table, column): "
      f"{len({(r[1], r[2]) for r in type_rows})}")
    for k, n in Counter(r[3] for r in type_rows).most_common():
        A(f"      {k or '(blank)':16s} {n}")

    (c.OUT / "doc_workbook.txt").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
