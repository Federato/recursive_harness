"""Stage 4 step 1: the submission schema, as ISO files it.

The build plan expected stage 4 to *derive* the submission shape from the 53
RAaS payloads rather than design one. It is better than that: **ISO files the
schema.** `Form Fields/Fields.FormField.csv` declares, per jurisdiction and per
field, the type, the label, whether it is required on a policy or a quote, its
default, its minimum and maximum, the condition under which it applies, and the
**domain table naming its legal values**. `Ratebook Columns/RatebookColumns.FormPage.csv`
adds `RatingRequiredCondition` -- when a field is required *to rate*, as opposed
to required on the form.

So stage 4 reads a schema rather than inventing one, and stage 5's workbook is
the same content in another shape.

  S1 population   fields per jurisdiction, and how many jurisdictions deviate
  S2 types        every `Type` filed, which is what a validator must handle
  S3 required     how many fields are required, and the difference between
                  required-on-the-form and required-to-rate
  S4 domains      how many fields name a domain table, which is where legal
                  values come from
  S5 conditions   the `Condition` / `RequiredCondition` dialect, which is NOT
                  the rule language and has to be handled separately
  S6 deviation    which jurisdictions differ from countrywide, and by how much
  S7 the four     California, Florida, New York and Texas resolve territory by
                  county or place (E8) -- confirmed or refuted from the fields

Emits out/input_schema.txt and out/input_schema.csv.
"""
from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
c = import_module("00_common")
rules_packages = import_module("42_node_surface").rules_packages

FIELD_FILE = Path("Form Fields") / "Fields.FormField.csv"
RATEBOOK_FILE = Path("Ratebook Columns") / "RatebookColumns.FormPage.csv"


def read_csv(path: Path):
    if not path.exists():
        return []
    header, rows = c.read_csv_rows(path)
    return [dict(zip(header, r)) for r in rows if r]


def main() -> None:
    pkgs, n_dirs, _ = rules_packages()

    # Latest package per jurisdiction, so the schema is one edition per state
    # rather than a blur across editions.
    latest: dict[str, object] = {}
    for pk in pkgs:
        cur = latest.get(pk.juris)
        if cur is None or (pk.edition, pk.version) > (cur.edition, cur.version):
            latest[pk.juris] = pk

    per_juris = {}
    types = Counter()
    required_policy = Counter()
    domains = Counter()
    conditions = Counter()
    all_rows = []
    rating_required = defaultdict(set)

    for juris, pk in sorted(latest.items()):
        rows = read_csv(pk.content / FIELD_FILE)
        rb = read_csv(pk.content / RATEBOOK_FILE)
        per_juris[juris] = {
            "pkg": pk.pkg_id,
            "fields": len(rows),
            "tables": len({r["TableName"] for r in rows}),
            "required": sum(1 for r in rows if r.get("PolicyRequired") == "True"),
            "domained": sum(1 for r in rows if r.get("DomainTableName")),
            "conditional": sum(1 for r in rows if r.get("Condition")),
            "rating_required": sum(1 for r in rb
                                   if r.get("RatingRequiredCondition")),
        }
        for r in rows:
            types[r.get("Type", "")] += 1
            if r.get("PolicyRequired") == "True":
                required_policy[(r["TableName"], r["ColumnName"])] += 1
            if r.get("DomainTableName"):
                domains[r["DomainTableName"]] += 1
            if r.get("Condition"):
                conditions[r["Condition"][:70]] += 1
            all_rows.append({
                "juris": juris, "table": r.get("TableName", ""),
                "column": r.get("ColumnName", ""), "type": r.get("Type", ""),
                "policy_required": r.get("PolicyRequired", ""),
                "domain": r.get("DomainTableName", ""),
                "default": r.get("Default", ""),
                "minimum": r.get("Minimum", ""), "maximum": r.get("Maximum", ""),
                "condition": r.get("Condition", ""),
                "required_condition": r.get("RequiredCondition", ""),
            })
        for r in rb:
            if r.get("RatingRequiredCondition"):
                rating_required[juris].add(
                    (r["TableName"], r["ColumnName"]))

    with open(c.OUT / "input_schema.csv", "w", newline="",
              encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(all_rows[0]))
        w.writeheader()
        w.writerows(all_rows)

    cw = per_juris.get("CW", {})
    L = []; A = L.append
    A("THE SUBMISSION SCHEMA, AS ISO FILES IT")
    A("")
    A(f"    jurisdictions (latest edition each): {len(per_juris)}")
    A(f"    field declarations in total        : {len(all_rows)}")
    A("")
    A("S1  FIELDS PER JURISDICTION")
    A(f"    countrywide: {cw.get('fields', 0)} fields over "
      f"{cw.get('tables', 0)} tables")
    sizes = sorted((v["fields"], j) for j, v in per_juris.items() if j != "CW")
    A(f"    states: min {sizes[0]} .. max {sizes[-1]}")
    A(f"    {'juris':6s} {'fields':>7s} {'tables':>7s} {'required':>9s} "
      f"{'domained':>9s} {'conditional':>12s}")
    for j, v in sorted(per_juris.items()):
        A(f"    {j:6s} {v['fields']:7d} {v['tables']:7d} {v['required']:9d} "
          f"{v['domained']:9d} {v['conditional']:12d}")
    A("")
    A("S2  TYPES  (what a validator must handle)")
    for k, n in types.most_common():
        A(f"    {k or '(blank)':16s} {n}")
    A("")
    A("S3  REQUIRED")
    A(f"    distinct (table, column) required on a policy somewhere: "
      f"{len(required_policy)}")
    A(f"    required in EVERY jurisdiction: "
      f"{sum(1 for v in required_policy.values() if v == len(per_juris))}")
    A("    rating-required fields per jurisdiction (RatebookColumns):")
    rr = sorted((len(v), j) for j, v in rating_required.items())
    if rr:
        A(f"      min {rr[0]} .. max {rr[-1]}")
    A("")
    A("S4  DOMAIN TABLES  (legal values -- stage 5's workbook)")
    A(f"    distinct domain tables named: {len(domains)}")
    for k, n in domains.most_common(12):
        A(f"      {k:44s} {n}")
    A("")
    A("S5  CONDITION DIALECT  (NOT the rule language)")
    A(f"    distinct Condition expressions: {len(conditions)}")
    for k, n in conditions.most_common(8):
        A(f"      {k:72s} {n}")
    A("")
    A("S6  DEVIATION FROM COUNTRYWIDE")
    cwf = {(r["table"], r["column"]) for r in all_rows if r["juris"] == "CW"}
    dev = {}
    for j in per_juris:
        if j == "CW":
            continue
        f = {(r["table"], r["column"]) for r in all_rows if r["juris"] == j}
        dev[j] = (len(f - cwf), len(cwf - f))
    extra = sorted(dev.items(), key=lambda x: -x[1][0])
    A(f"    {'juris':6s} {'fields not in CW':>18s} {'CW fields absent':>18s}")
    for j, (a, b) in extra[:12]:
        A(f"    {j:6s} {a:18d} {b:18d}")
    A(f"    jurisdictions with NO extra field: "
      f"{sum(1 for a, _ in dev.values() if a == 0)} of {len(dev)}")
    A("")
    A("S7  THE FOUR TERRITORY-BY-PLACE JURISDICTIONS (E8)")
    place = [r for r in all_rows
             if any(t in r["column"] for t in ("County", "Place", "Town",
                                               "Borough", "Parish"))]
    by_j = defaultdict(set)
    for r in place:
        by_j[r["juris"]].add(f"{r['table']}.{r['column']}")
    A(f"    jurisdictions declaring a county/place field: {len(by_j)}")
    for j in sorted(by_j):
        A(f"      {j:4s} {sorted(by_j[j])}")

    (c.OUT / "input_schema.txt").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L[:60]))
    print(f"\n[wrote input_schema.txt and input_schema.csv]")


if __name__ == "__main__":
    main()
