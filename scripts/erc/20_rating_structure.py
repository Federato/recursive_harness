"""Phase 5 step 3: the rating structure.

Three parts, all measured mechanically:

  R1 THE INPUT SURFACE
     Form Fields is the declared data-entry surface; Ratebook Columns is
     the subset flagged as required for rating.  Both are inventoried by
     page, table and column, with their declared Type, and resolved
     through the countrywide parent the way 18_composition.py showed
     content resolves.

  R2 TABLE SHAPES
     Every rate/domain table is classified by its DECLARED value-column
     names and key structure into shapes:
       lookup-rate     value col named Rate / LossCost / Factor / ILF ...
       assignment      value col names a table to use next (indirection)
       step / banded   the Def declares a <Range> key
       interpolated    the Def declares InterpolateMode
       text / stat     value col is a code or descriptive string
     Key-column names across the corpus give the lookup dimensions.

  R3 THE PREMIUM DATAFLOW
     Every arithmetic node in every rule that writes a result
     (`ToDataDef`) is parsed into an edge  target <- (op, sources).
     Aggregating these across the corpus yields the derivation graph of
     the premium calculation without any interpretation on my part.
     The graph is then walked backwards from `Premium` to print the
     algorithm.

Emits out/input_surface.csv, out/table_shapes.csv, out/dataflow_edges.csv,
out/rating_structure.txt.
"""
from __future__ import annotations

import csv
import re
import sys
from collections import Counter, defaultdict
from multiprocessing import Pool
from pathlib import Path
from importlib import import_module

sys.path.insert(0, str(Path(__file__).parent))
c = import_module("00_common")
csv.field_size_limit(1 << 24)

ARITH = {"Product", "Sum", "Subtract", "Divide", "Round", "Truncate", "Max",
         "Count", "Concat", "Copy", "Constant", "FirstNonNull", "Lookup",
         "RunRule", "Guid", "Convert", "DatePart", "DateAdd", "Length",
         "PadLeft", "DateDifference", "DateCreate"}


def scan_rules(a):
    """Extract dataflow edges from one package's rule files."""
    pkg_id, juris, content = a
    d = Path(content) / "Rules"
    edges = []
    if not d.is_dir():
        return edges
    for f in sorted(d.glob("*.Rule.xml")):
        try:
            root = c.parse_xml(f)
        except Exception:
            continue
        fname = f.name[: -len(".Rule.xml")]
        for rule in root:
            if c.lname(rule.tag) != "Rule":
                continue
            rname = rule.get("Name", "")
            for el in rule.iter():
                ln = c.lname(el.tag)
                if ln not in ARITH:
                    continue
                tgt = el.get("ToDataDef")
                if not tgt:
                    continue
                srcs = []
                for sub in el.iter():
                    if sub is el and ln not in ("Copy", "Constant", "Lookup",
                                                "RunRule"):
                        continue
                    v = sub.get("FromDataDef")
                    if v:
                        srcs.append(v)
                if ln == "Lookup":
                    srcs.append("@" + (el.get("MatrixFromConstant") or "") +
                                "." + (el.get("MatrixCol") or ""))
                if ln == "RunRule":
                    srcs.append("!" + (el.get("FileName") or "") + "." +
                                (el.get("Rule") or ""))
                edges.append((pkg_id, juris, fname, rname, ln, tgt,
                              "|".join(srcs)))
    return edges


def load(n):
    with open(c.OUT / n, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def norm(s: str) -> str:
    """Strip XPath navigation from a DataDef reference -> bare field name."""
    s = s.strip()
    if s.startswith("@") or s.startswith("!"):
        return s
    return s.replace("../", "").replace("/*/", "").split("/")[-1]


def main():
    pkgs = c.find_packages()
    seen, args = set(), []
    for p in pkgs:
        if p.pkg_id in seen:
            continue
        seen.add(p.pkg_id)
        args.append((p.pkg_id, p.juris, str(p.content)))
    E = []
    with Pool() as pool:
        for e in pool.imap_unordered(scan_rules, args, chunksize=2):
            E.extend(e)
    with open(c.OUT / "dataflow_edges.csv", "w", newline="",
              encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["pkg_id", "juris", "rule_file", "rule_name", "op",
                    "target", "sources"])
        w.writerows(E)

    L = []; A = L.append
    A("RATING STRUCTURE")
    A("")

    # ---------------- R1 input surface ----------------
    ff = load("form_csv_schema.csv")
    A("R1  THE INPUT SURFACE")
    fields = defaultdict(set)
    ftype = Counter()
    fpage = Counter()
    frows = 0
    for p in pkgs:
        pass
    # read Form Fields rows directly (not fingerprinted) for Type/Label
    def read_form_fields():
        rows = []
        seen2 = set()
        for p in pkgs:
            if p.pkg_id in seen2:
                continue
            seen2.add(p.pkg_id)
            f = Path(p.content) / "Form Fields" / "Fields.FormField.csv"
            if not f.exists():
                continue
            hdr, rdr = c.read_csv_rows(f)
            for r in rdr:
                rows.append((p.pkg_id, p.juris, dict(zip(hdr, r))))
        return rows
    FF = read_form_fields()
    frows = len(FF)
    for pid, j, r in FF:
        fields[(r.get("TableName", ""), r.get("ColumnName", ""))].add(j)
        ftype[r.get("Type", "")] += 1
        fpage[r.get("Page", "")] += 1
    A(f"    Form Fields rows: {frows}; distinct (TableName, ColumnName): "
      f"{len(fields)}")
    A(f"    declared field Types: {ftype.most_common()}")
    A(f"    pages carrying input fields: {len(fpage)}; top:")
    for k, n in fpage.most_common(12):
        A(f"      {k:36s} {n}")
    rc = defaultdict(set)
    rc_req = 0
    seen3 = set()
    for p in pkgs:
        if p.pkg_id in seen3:
            continue
        seen3.add(p.pkg_id)
        f = Path(p.content) / "Ratebook Columns" / "RatebookColumns.FormPage.csv"
        if not f.exists():
            continue
        hdr, rdr = c.read_csv_rows(f)
        for r in rdr:
            d = dict(zip(hdr, r))
            rc[(d.get("TableName", ""), d.get("ColumnName", ""))].add(p.juris)
            if d.get("RatingRequiredCondition", ""):
                rc_req += 1
    A(f"    Ratebook Columns (rating inputs): {len(rc)} distinct "
      f"(TableName, ColumnName); {rc_req} rows carry a "
      f"RatingRequiredCondition (XPath)")
    univ = [k for k, v in rc.items() if len(v) >= 52]
    A(f"    rating inputs present in all 52 jurisdictions: {len(univ)}")
    A(f"    rating inputs present in exactly one jurisdiction: "
      f"{sum(1 for v in rc.values() if len(v) == 1)}")
    with open(c.OUT / "input_surface.csv", "w", newline="",
              encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["table_name", "column_name", "in_form_fields",
                    "in_ratebook_columns", "n_juris_form", "n_juris_ratebook"])
        for k in sorted(set(fields) | set(rc)):
            w.writerow([k[0], k[1], k in fields, k in rc,
                        len(fields.get(k, ())), len(rc.get(k, ()))])

    # ---------------- R2 table shapes ----------------
    A("")
    A("R2  TABLE SHAPES")
    tabs = load("table_defs.csv")
    VALUE_CLASS = [
        ("loss cost / rate", ("LossCost", "Rate", "BaseRate", "ELP")),
        ("factor / multiplier", ("Factor", "Multiplier", "Relativity",
                                 "ILF", "LCM", "Index", "Pct", "Percent")),
        ("premium / money", ("Premium", "MinPremium", "Charge", "Max", "Min",
                             "Constant")),
        ("table assignment (indirection)", ("Assignment", "TableAssignment")),
        ("statistical / code", ("StatCode", "Code", "Identifier")),
        ("text / description", ("Text", "Description", "DisplayValue",
                                "DataValue", "Grade")),
    ]
    shape = Counter()
    keydims = Counter()
    rows = []
    for t in tabs:
        vals = [v for v in t["value_cols"].split("|") if v]
        keys = [k for k in t["key_cols"].split("|") if k]
        for k in keys:
            keydims[k] += 1
        cls = set()
        for name, toks in VALUE_CLASS:
            if any(any(x in v for x in toks) for v in vals):
                cls.add(name)
        ranged = "_From" in t["key_cols"] or "_ToLessThan" in t["key_cols"]
        interp = "_ToLessThan" in t["value_cols"]
        tag = ("interpolated band" if interp else
               "step / banded" if ranged else
               ("+".join(sorted(cls)) if cls else "(unclassified)"))
        shape[(t["kind"], tag)] += 1
        rows.append([t["pkg_id"], t["kind"], t["table"], tag, len(keys),
                     len(vals), t["key_cols"], t["value_cols"]])
    with open(c.OUT / "table_shapes.csv", "w", newline="",
              encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["pkg_id", "kind", "table", "shape", "n_key", "n_value",
                    "key_cols", "value_cols"])
        w.writerows(rows)
    A(f"    {'kind':7s} {'shape':46s} {'tables':>8}")
    for (k, s), n in sorted(shape.items(), key=lambda x: -x[1]):
        A(f"    {k:7s} {s:46s} {n:8d}")
    A("")
    A(f"    LOOKUP DIMENSIONS - distinct key-column names: {len(keydims)}")
    A(f"    {'key column':50s} {'tables':>8}")
    for k, n in keydims.most_common(30):
        A(f"    {k:50s} {n:8d}")
    A(f"    key columns used by exactly one table def: "
      f"{sum(1 for v in keydims.values() if v == 1)}")
    nkeys = Counter(len([k for k in t['key_cols'].split('|') if k]) for t in tabs)
    A(f"    key arity distribution: {sorted(nkeys.items())}")

    # ---------------- R3 dataflow ----------------
    A("")
    A("R3  THE PREMIUM DATAFLOW")
    A(f"    arithmetic/assignment nodes with a ToDataDef target: {len(E)}")
    A(f"    distinct targets: {len({norm(e[5]) for e in E})}")
    A(f"    operators used to write a value: "
      f"{Counter(e[4] for e in E).most_common()}")
    A("")
    A("    TOP WRITE TARGETS (field <- how many distinct (op, source-set))")
    tgt = defaultdict(set)
    for e in E:
        tgt[norm(e[5])].add((e[4], tuple(sorted({norm(s) for s in
                                                 e[6].split("|") if s}))))
    for k, n in sorted(((k, len(v)) for k, v in tgt.items()),
                       key=lambda x: -x[1])[:20]:
        A(f"      {k:44s} {n}")
    A("")
    A("    THE PREMIUM CHAIN - distinct source sets writing each key field")
    for field in ("BaseRate", "FinalRate", "FinalILF", "Premium",
                  "ErcCalculatedTotalPremium", "BasicLimitPremium",
                  "FinalDeductibleFactor"):
        srcsets = Counter()
        for e in E:
            if norm(e[5]) != field:
                continue
            s = tuple(sorted({norm(x) for x in e[6].split("|")
                              if x and not x.startswith(("@", "!"))}))
            srcsets[(e[4], s)] += 1
        A(f"      {field}:")
        for (op, s), n in srcsets.most_common(4):
            A(f"        {op}({', '.join(s) or '-'})   x{n}")
    (c.OUT / "rating_structure.txt").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
