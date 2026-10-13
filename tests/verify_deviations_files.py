"""T10: the deviation files say what people wrote (DEVIATIONS-PLAN.md, P1 gate).

Run: python tests/verify_deviations_files.py      (offline; makes no ISO calls)

  A  ufg         the P0 filing (UFG Iowa CF, both companies) validates, compiles
                 to the LCMs the exception page prints, and reads back exactly
  B  import      the same filing imported from its sheet (CSV and .xlsx)
                 compiles to byte-identical tables; the sheet's dates lose to
                 the PDF's, out loud (D18)
  C  refusals    validate refuses each bad case, by name
  D  approval    only a version approved in the file AND the log compiles (D6, M4)
  E  compose     replace / multiply / specificity, and show reads them back
  F  all states  the shortcut expands as of its date; opt-out removes a state
  G  overrides   an ISO table override compiles in ISO's keys and reads back
  H  diff        versions compare row by row
  I  GL          the same machinery on a GL LCM filing

Every case works in a temporary copy: nothing here writes under CARRIERS_ROOT.
Needs the CF and GL corpora (CF_ERC_ROOT / GL_ERC_ROOT), as every suite does.
"""
from __future__ import annotations

import csv
import io
import json
import shutil
import sys
import tempfile
import zipfile
from decimal import Decimal
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from deviations import iso                                        # noqa: E402
from deviations.compile import CompileError, compile_filing, show  # noqa: E402
from deviations.diff import diff_versions                         # noqa: E402
from deviations.files import load_filing, log_action, write_json  # noqa: E402
from deviations.sheets import import_sheet                        # noqa: E402
from deviations.validate import validate                          # noqa: E402

FIX = ROOT / "tests" / "fixtures" / "deviations"
REF = "IA-CF-UNFG-134289779.v1"
FAILED = []


CHECKS = []


def check(label: str, ok: bool, detail: str = "") -> None:
    CHECKS.append((label, ok))
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}"
          + (f"\n          {detail}" if detail and not ok else ""))
    if not ok:
        FAILED.append(label)


def tmp_root() -> Path:
    d = Path(tempfile.mkdtemp(prefix="deviations_"))
    shutil.copytree(FIX / "UFG", d / "UFG")
    return d


def approve(path: Path, *names: str) -> None:
    f = load_filing(path)
    log_action(f.company_dir, f.filing, f.version, "propose", names[0] if names else "Tester")
    for n in names or ("Tester",):
        log_action(f.company_dir, f.filing, f.version, "sign-off", n)


def build(path: Path):
    f = load_filing(path)
    rep = validate(f)
    if not rep.ok:
        raise AssertionError("\n".join(rep.errors))
    return rep, compile_filing(rep)


def compiled_rows(d: Path, name="GroupLCM.Company.RateTable.csv") -> dict:
    rows = list(csv.reader(io.StringIO((d / name).read_text(encoding="utf-8-sig"))))
    h = rows[0]
    return {tuple(r[:h.index("Factor") if "Factor" in h else len(h) - 3]): r for r in rows[1:]}


def same_rows(a: list, b: list) -> bool:
    def norm(rows):
        return [{k: (Decimal(str(v)) if k == "value" else v) for k, v in r.items()
                 if k in ("target", "scope", "value", "mode", "note")} for r in rows]
    return norm(a) == norm(b)


def new_filing(company_dir: Path, rows: list, *, filing="TEST-CF", version=1, line="CF",
               juris=("IA",), new="2025-06-01", renewal="2025-10-01", status="approved",
               **extra) -> Path:
    d = {"filing": filing, "company": company_dir.name, "line": line, "juris": list(juris),
         "version": version, "status": status, "new_eff": new, "renewal_eff": renewal,
         "rows": rows, **extra}
    p = company_dir / "authored" / f"{filing}.v{version}.json"
    write_json(p, json.loads(json.dumps(d), parse_float=Decimal))
    return p


def errors_of(path: Path) -> str:
    return "\n".join(validate(load_filing(path)).errors)


# ------------------------------------------------------------------------- A

def a_ufg() -> None:
    print("\nA  the UFG Iowa CF filing (P0) compiles and reads back")
    root = tmp_root()
    expect = {  # company -> class -> (Group I, Group II/Broad/Special, Earthquake), exception page pp. 2-3
        "UFC": {"0545": ("1.067", "2.448", "2.11"), "0511": ("0.875", "2.062", "2.11"),
                "0074": ("1.511", "3.28", "2.11")},
        "ADD": {"0545": ("1.279", "2.938", "2.64"), "0511": ("1.051", "2.474", "2.64"),
                "0074": ("1.813", "3.934", "2.64")},
    }
    for co, classes in expect.items():
        p = root / "UFG" / co / "authored" / f"{REF}.json"
        rep = validate(load_filing(p))
        check(f"A1 {co} validates", rep.ok, "; ".join(rep.errors))
        n = sum(len(k) for _, _, comp, _, _ in rep.plans.values() for k in comp.values())
        check(f"A2 {co} reaches every key once: 5 groups x 2 bases x 154 classes",
              n == 1540, f"got {n}")
        check(f"A3 {co} both dates fall in CF_IA_20250401_V01",
              rep.plans["IA"][3]["state"] == "CF_IA_20250401_V01" == rep.plans["IA"][4]["state"])
        approve(p)
        _, dirs = build(p)
        rows = compiled_rows(dirs[0])
        bad = []
        for cls, (g1, g2, eq) in classes.items():
            for basis in ("Specific", "Class"):
                for grp, want in (("GroupI", g1), ("GroupII", g2), ("Broad", g2),
                                  ("Special", g2), ("Earthquake", eq)):
                    got = rows[("IA", grp, basis, cls)][4]
                    if got != want:
                        bad.append(f"{grp}/{basis}/{cls}={got} (want {want})")
        check(f"A4 {co} class groups A, B and all-other carry the filed LCMs", not bad,
              ", ".join(bad))
        s = show(root / "UFG" / co, "CF", REF)
        check(f"A5 {co} show reads the compiled tables back as the 13 authored rows",
              same_rows(s["rows"], json.loads(p.read_text(), parse_float=Decimal)["rows"]))
        m = json.loads((dirs[0] / "manifest.json").read_text())
        check(f"A6 {co} manifest keeps citations and the ISO edition",
              m["rows"][0]["cite"].startswith("Exc") and
              m["iso_edition"]["new"]["countrywide"] == "CF_CW_20230801_V02")
    shutil.rmtree(root)


# ------------------------------------------------------------------------- B

def _xlsx_from_csv(src: Path, dst: Path) -> None:
    """A minimal real .xlsx (inline strings) holding the CSV's cells."""
    rows = list(csv.reader(io.StringIO(src.read_text(encoding="utf-8-sig"))))
    def ref(r, c):
        s = ""
        c += 1
        while c:
            c, rem = divmod(c - 1, 26)
            s = chr(65 + rem) + s
        return f"{s}{r + 1}"
    data = "".join(
        f'<row r="{i + 1}">' + "".join(
            f'<c r="{ref(i, j)}" t="inlineStr"><is><t>{escape(v)}</t></is></c>'
            for j, v in enumerate(r) if v) + "</row>" for i, r in enumerate(rows))
    ns = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
    rel = 'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
    with zipfile.ZipFile(dst, "w") as z:
        z.writestr("xl/workbook.xml", f'<workbook {ns} {rel}><sheets>'
                   f'<sheet name="LCMs" sheetId="1" r:id="rId1"/></sheets></workbook>')
        z.writestr("xl/_rels/workbook.xml.rels",
                   '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Target="worksheets/sheet1.xml" '
                   'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"/>'
                   '</Relationships>')
        z.writestr("xl/worksheets/sheet1.xml", f"<worksheet {ns}><sheetData>{data}</sheetData></worksheet>")


def b_import() -> None:
    print("\nB  the same filing imported from its sheet")
    hand = tmp_root()
    for co in ("UFC", "ADD"):
        p = hand / "UFG" / co / "authored" / f"{REF}.json"
        approve(p)
        build(p)
    sheet = FIX / "UFG_IA_CP_LCMs.csv"
    xlsx = Path(tempfile.mkdtemp()) / "UFG_IA_CP_LCMs.xlsx"
    _xlsx_from_csv(sheet, xlsx)
    for label, src in (("CSV", sheet), ("xlsx", xlsx)):
        root = Path(tempfile.mkdtemp(prefix="deviations_import_"))
        files, warns = import_sheet(
            src, root, carrier="UFG", line="CF", juris=["IA"], filing="IA-CF-UNFG-134289779",
            version=1, company_map={"United Fire & Casualty": "UFC", "Addison": "ADD"},
            new_eff="2025-06-01", renewal_eff="2025-10-01")
        check(f"B1 {label}: one authored file per company (G3)", len(files) == 2)
        check(f"B2 {label}: the sheet's 7/15 and 12/1 dates are refused aloud for the PDF's (D18)",
              len(warns) == 2 and all("D18" in w for w in warns), "; ".join(warns))
        cj = json.loads((root / "UFG" / "carrier.json").read_text())
        hj = json.loads((FIX / "UFG" / "carrier.json").read_text())
        check(f"B3 {label}: class groups land at carrier level, as hand-written (G7)",
              cj["class_groups"] == hj["class_groups"])
        for co in ("UFC", "ADD"):
            p = root / "UFG" / co / "authored" / f"{REF}.json"
            d = json.loads(p.read_text(), parse_float=Decimal)
            check(f"B4 {label} {co}: imports as a draft", d["status"] == "draft")
            d["status"] = "approved"
            write_json(p, d)
            approve(p)
            _, dirs = build(p)
            mine = (dirs[0] / "GroupLCM.Company.RateTable.csv").read_bytes()
            theirs = (hand / "UFG" / co / "compiled" / "CF" / "IA" / REF /
                      "GroupLCM.Company.RateTable.csv").read_bytes()
            check(f"B5 {label} {co}: compiled table byte-identical to hand-authoring",
                  mine == theirs)
        shutil.rmtree(root)
    shutil.rmtree(hand)
    shutil.rmtree(xlsx.parent)


# ------------------------------------------------------------------------- C

def c_refusals() -> None:
    print("\nC  validate refuses each bad case")
    root = tmp_root()
    co = root / "UFG" / "UFC"
    ok_row = {"target": "LCM:GroupI", "scope": {}, "value": "1.1", "mode": "replace"}
    cases = [
        ("C1 an unknown target", [dict(ok_row, target="LCM:Hail")], {}, "is not one CF has"),
        ("C2 a class the edition doesn't have", [dict(ok_row, scope={"class": "9999"})], {},
         "9999 is not a class"),
        ("C3 an undefined class group", [dict(ok_row, scope={"class_group": "UFG-Z@v1"})], {},
         "not defined"),
        ("C4 a class and a class group at once",
         [dict(ok_row, scope={"class": "0545", "class_group": "UFG-A@v1"})], {}, "both a class"),
        ("C5 a territory-keyed LCM (later, named)", [dict(ok_row, scope={"territory": "001"})], {},
         "not supported yet"),
        ("C6 a mode that isn't replace or multiply", [dict(ok_row, mode="add")], {}, "mode 'add'"),
        ("C7 a value of zero", [dict(ok_row, value="0")], {}, "above 0"),
        ("C8 two replace rows at one specificity",
         [ok_row, dict(ok_row, value="1.2")], {}, "same specificity"),
        ("C9 renewal before new business", [ok_row], {"renewal": "2025-05-01"}, "before new_eff"),
        ("C10 a date that isn't one", [ok_row], {"new": "6/1/2025"}, "is not a date"),
        ("C11 an LCM outside its band without a note", [dict(ok_row, value="3.5")], {},
         "outside 0.25-3"),
        ("C12 an unknown rating basis", [dict(ok_row, scope={"rating_basis": "Blanket"})], {},
         "rating basis"),
        ("C13 an ISO table the edition doesn't have",
         [dict(ok_row, target="TABLE:NoSuchTable.Factor")], {}, "no rate table"),
        ("C14 a value column ISO's table doesn't have",
         [dict(ok_row, target="TABLE:BCEGFactor.Rate")], {}, "no value column"),
        ("C15 a key column ISO's table doesn't have",
         [dict(ok_row, target="TABLE:BCEGFactor.Factor", scope={"Zone": "1"})], {},
         "no key column"),
        ("C16 a key value ISO's table doesn't have",
         [dict(ok_row, target="TABLE:BCEGFactor.Factor",
               scope={"BldgCodeEffectivenessGrade2": "ZZ"})], {}, "has no row"),
        ("C17 a banded ISO table", [dict(ok_row, target="TABLE:DeductibleFactor.Factor")], {},
         "banded"),
    ]
    for label, rows, kw, want in cases:
        p = new_filing(co, rows, **kw)
        errs = errors_of(p)
        check(label, want in errs, errs or "validated")
        p.unlink()
    p = new_filing(co, [dict(ok_row, value="3.5", note="filed as a surcharge territory")])
    check("C18 the same out-of-band LCM passes with a note", not errors_of(p), errors_of(p))
    p.unlink()
    p = new_filing(co, [ok_row])
    p.rename(p.with_name("misnamed.json"))
    check("C19 a file whose name isn't its filing version",
          "lives in TEST-CF.v1.json" in errors_of(p.with_name("misnamed.json")))
    write_json(root / "UFG" / "carrier.json",
               {"carrier": "UFG", "class_groups": {"UFG-X@v1": ["0074-0078", "0080-9999"]}})
    p = new_filing(co, [dict(ok_row, scope={"class_group": "UFG-X@v1"})])
    check("C20 a class range whose endpoint the edition doesn't have",
          "9999 not a class" in errors_of(p))
    p = new_filing(co, [ok_row], filing="TEST-C21")
    check("C21 ...but only when the filing uses that group (a carrier's other groups "
          "are not this filing's problem)", not errors_of(p), errors_of(p))
    shutil.rmtree(root)


# ------------------------------------------------------------------------- D

def d_approval() -> None:
    print("\nD  only approved versions compile (D6, M4)")
    root = tmp_root()
    co = root / "UFG" / "UFC"
    row = [{"target": "LCM:GroupI", "scope": {}, "value": "1.1", "mode": "replace"}]

    def compiles(p) -> bool:
        try:
            compile_filing(validate(load_filing(p)))
            return True
        except CompileError:
            return False

    p = new_filing(co, row, status="draft")
    approve(p)
    check("D1 a draft file does not compile, whatever the log says", not compiles(p))
    p = new_filing(co, row, filing="TEST-D2")
    check("D2 an approved file with no sign-off does not compile", not compiles(p))
    approve(p)
    check("D3 propose + sign-off compiles", compiles(p))
    f = load_filing(p)
    log_action(f.company_dir, f.filing, f.version, "reject", "Reviewer")
    check("D4 a later reject wins over the sign-off (latest line wins)", not compiles(p))
    log_action(f.company_dir, f.filing, f.version, "propose", "Author")
    check("D5 a new propose clears earlier sign-offs", not compiles(p))
    write_json(root / "UFG" / "carrier.json",
               json.loads((FIX / "UFG" / "carrier.json").read_text()) | {"approval": {"signoffs": 2}})
    p = new_filing(co, row, filing="TEST-D6")
    approve(p, "Ann", "Ann")
    check("D6 under a two-sign-off policy the same person twice is not enough", not compiles(p))
    f = load_filing(p)
    log_action(f.company_dir, f.filing, f.version, "sign-off", "Bob")
    check("D7 two different people sign off -> compiles", compiles(p))
    shutil.rmtree(root)


# ------------------------------------------------------------------------- E

def e_compose() -> None:
    print("\nE  replace, multiply and specificity")
    root = tmp_root()
    co = root / "UFG" / "UFC"
    rows = [
        {"target": "LCM:All", "scope": {}, "value": "1.10", "mode": "replace"},
        {"target": "LCM:GroupI", "scope": {"class_group": "UFG-A@v1"}, "value": "1.05",
         "mode": "multiply"},
        {"target": "LCM:Earthquake", "scope": {"class": "0545", "rating_basis": "Specific"},
         "value": "0.9", "mode": "replace"},
        {"target": "LCM:Special", "scope": {}, "value": "0.5", "mode": "multiply"},
        {"target": "LCM:Special", "scope": {"class": "0074"}, "value": "2", "mode": "replace"},
    ]
    p = new_filing(co, rows)
    approve(p)
    _, dirs = build(p)
    r = compiled_rows(dirs[0])
    get = lambda g, b, c: (r[("IA", g, b, c)][4], r[("IA", g, b, c)][5])
    check("E1 replace across all groups", get("GroupII", "Class", "0511") == ("1.1", "replace"))
    check("E2 a more specific multiply stacks on the replace: 1.10 x 1.05",
          get("GroupI", "Class", "0545") == ("1.155", "replace"), str(get("GroupI", "Class", "0545")))
    check("E3 the multiply stays inside its class group",
          get("GroupI", "Class", "0511") == ("1.1", "replace"))
    check("E4 the most specific replace wins at its key",
          get("Earthquake", "Specific", "0545") == ("0.9", "replace")
          and get("Earthquake", "Class", "0545") == ("1.1", "replace"))
    check("E5 a multiply as specific as the replace applies on top: 1.10 x 0.5",
          get("Special", "Class", "0511") == ("0.55", "replace"))
    check("E6 a multiply less specific than the winning replace is overridden",
          get("Special", "Class", "0074") == ("2", "replace"))
    s = show(co, "CF", "TEST-CF.v1")
    check("E7 show reads all five rows back", same_rows(s["rows"], json.loads(
        p.read_text(), parse_float=Decimal)["rows"]), json.dumps(s["rows"], default=str)[:400])
    p2 = new_filing(co, [{"target": "LCM:GroupI", "scope": {}, "value": "1.2", "mode": "multiply"}],
                    filing="TEST-E8")
    approve(p2)
    _, d2 = build(p2)
    check("E8 a multiply with no replace stays a multiply of ISO's own LCM",
          compiled_rows(d2[0])[("IA", "GroupI", "Class", "0074")][5] == "multiply")
    shutil.rmtree(root)


# ------------------------------------------------------------------------- F

def f_all_states() -> None:
    print("\nF  the all-states shortcut and opt-out (I2)")
    root = tmp_root()
    co = root / "UFG" / "UFC"
    row = [{"target": "LCM:Earthquake", "scope": {}, "value": "1.2", "mode": "replace"}]
    states = iso.jurisdictions("CF", "2025-06-01")
    p = new_filing(co, row, juris=["ALL"], juris_asof="2025-06-01", opt_out=["IA"])
    rep = validate(load_filing(p))
    check("F1 ALL expands to every jurisdiction on its date, less the opt-out",
          rep.ok and rep.juris == [j for j in states if j != "IA"],
          f"{len(rep.juris)} vs {len(states)}; {rep.errors[:2]}")
    check("F2 the expansion is a real population (more than 40 states)", len(states) > 40,
          str(len(states)))
    p = new_filing(co, row, filing="TEST-F3", juris=["ALL"])
    check("F3 ALL without the date it was taken is refused", "juris_asof" in errors_of(p))
    p = new_filing(co, row, filing="TEST-F4", juris=["ALL"], juris_asof="2025-06-01",
                   opt_out=["ZZ"])
    check("F4 opting out of a state that doesn't exist is refused", "opt_out 'ZZ'" in errors_of(p))
    shutil.rmtree(root)


# ------------------------------------------------------------------------- G

def g_overrides() -> None:
    print("\nG  ISO table overrides")
    root = tmp_root()
    co = root / "UFG" / "UFC"
    # FloodLossCost: three keys, each with more than one value in Iowa, so every
    # scope key below really narrows (a key that doesn't is warned about, G5)
    t = iso.table("CF", "IA", "2025-06-01", "FloodLossCost")
    k1, k2, _ = iso.table_keys(t)
    first = t.rows[0]
    v1 = str(first[t.col(k1)])
    rows = [
        {"target": "TABLE:FloodLossCost.LossCost", "scope": {k1: v1}, "value": "1.1", "mode": "multiply"},
        {"target": "TABLE:FloodLossCost.LossCost",
         "scope": {k1: v1, k2: str(first[t.col(k2)])}, "value": "0.95", "mode": "replace"},
    ]
    p = new_filing(co, rows)
    approve(p)
    _, dirs = build(p)
    d = dirs[0]
    name = "Rate Tables/FloodLossCost.Company.RateTable.csv"
    check("G1 the override compiles in ISO's own table name and keys",
          (d / name).exists() and (d / "Rate Tables/FloodLossCost.CompanyDef.RateTableDef.xml").exists())
    hdr = next(csv.reader(io.StringIO((d / name).read_text(encoding="utf-8-sig"))))
    check("G2 its key columns are ISO's, in ISO's order", hdr[:4] == ["StateCode", *iso.table_keys(t)],
          str(hdr))
    n = sum(1 for r in t.rows if str(r[t.col(k1)]) == v1)
    got = (d / name).read_text(encoding="utf-8-sig").count("\n") - 1
    check("G3 one row per ISO key the scope reaches", got == n, f"{got} vs {n}")
    s = show(co, "CF", "TEST-CF.v1")
    check("G4 show reads both override rows back", same_rows(
        s["rows"], json.loads(p.read_text(), parse_float=Decimal)["rows"]),
        json.dumps(s["rows"], default=str))
    t2 = iso.table("CF", "IA", "2025-06-01", "BCEGFactor")
    k = iso.table_keys(t2)[0]
    p = new_filing(co, [{"target": "TABLE:BCEGFactor.Factor",
                         "scope": {k: str(t2.rows[0][t2.col(k)])}, "value": "1.1",
                         "mode": "multiply"}], filing="TEST-G5")
    w = validate(load_filing(p)).warnings
    check("G5 a scope key that narrows nothing is warned about", any("narrows nothing" in x for x in w),
          "; ".join(w))
    shutil.rmtree(root)


# ------------------------------------------------------------------------- H

def h_diff() -> None:
    print("\nH  diff")
    root = tmp_root()
    a = root / "UFG" / "UFC" / "authored" / f"{REF}.json"
    d = json.loads(a.read_text(), parse_float=Decimal)
    d["version"] = 2
    d["rows"][1]["value"] = Decimal("1.10")
    d["rows"].append({"target": "LCM:GroupI", "scope": {"class": "0545"}, "value": Decimal("1.2"),
                      "mode": "replace"})
    d["renewal_eff"] = "2025-11-01"
    b = a.with_name("IA-CF-UNFG-134289779.v2.json")
    write_json(b, d)
    out = diff_versions(load_filing(a), load_filing(b))
    check("H1 a changed value is reported", any("1.067 (replace) -> 1.10" in x for x in out),
          "\n".join(out))
    check("H2 an added row is reported", any(x.startswith("+ LCM:GroupI") for x in out))
    check("H3 a changed date is reported", any("renewal_eff" in x for x in out))
    shutil.rmtree(root)


# ------------------------------------------------------------------------- I

def i_gl() -> None:
    print("\nI  a GL LCM filing")
    root = tmp_root()
    co = root / "UFG" / "UFC"
    classes = iso.class_codes("GL", "TX", "2026-07-01")
    rows = [{"target": "LCM:PremOps", "scope": {}, "value": "1.12", "mode": "replace"},
            {"target": "LCM:PremOps", "scope": {"class": classes[0]}, "value": "1.08",
             "mode": "multiply"},
            {"target": "LCM:ProdsCompldOps", "scope": {}, "value": "1.25", "mode": "replace"}]
    p = new_filing(co, rows, filing="TX-GL", line="GL", juris=["TX"], new="2026-07-01",
                   renewal="2026-08-01")
    approve(p)
    _, dirs = build(p)
    r = compiled_rows(dirs[0], "LCM.Company.RateTable.csv")
    check("I1 GL compiles to LCM keyed by coverage and class",
          r[("TX", "PremOps", classes[0])][3] == "1.2096"
          and r[("TX", "ProdsCompldOps", classes[0])][3] == "1.25")
    check("I2 GL's class universe is ISO's 1,188 classifications", len(classes) > 1000,
          str(len(classes)))
    s = show(co, "GL", "TX-GL.v1")
    check("I3 show reads the GL rows back",
          same_rows(s["rows"], json.loads(p.read_text(), parse_float=Decimal)["rows"]))
    p = new_filing(co, [dict(rows[0], scope={"rating_basis": "Class"})], filing="TX-GL2",
                   line="GL", juris=["TX"], new="2026-07-01", renewal="2026-08-01")
    check("I4 a rating basis is a CF scope, refused on GL", "not an LCM scope for GL" in errors_of(p))
    shutil.rmtree(root)


def main() -> int:
    for step in (a_ufg, b_import, c_refusals, d_approval, e_compose, f_all_states,
                 g_overrides, h_diff, i_gl):
        step()
    from deviations import suite_log
    suite_log.record("files", CHECKS)
    print(f"\n{'FAILED: ' + ', '.join(FAILED) if FAILED else 'all passed'}")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
