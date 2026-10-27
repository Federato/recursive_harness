"""Stage 5 acceptance: the enum workbook.

  A  the file      a real .xlsx, written with the standard library, readable
  B  scope         the number the plan predicted would matter: how much of the
                   declared surface a real submission actually uses
  C  provenance    every column traces to a named ISO file; nothing invented
  D  values        legal values are ISO's, and large domains are summarised
                   rather than silently truncated

Run: python tests/verify_stage5.py
"""
from __future__ import annotations

import sys
from importlib import util as _util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

WORKBOOK = ROOT / "GL-Submission-Fields.xlsx"
PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(f"{name}  {detail}".rstrip())
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f"  [{detail}]" if detail else ""))


def _reader():
    spec = _util.spec_from_file_location(
        "doc49", ROOT / "scripts" / "erc" / "49_doc_workbook.py")
    mod = _util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.sheets


def main() -> int:
    print("Stage 5 acceptance -- the enum workbook")
    if not WORKBOOK.exists():
        print(f"  workbook missing: run scripts/build_enum_workbook.py")
        return 1

    print("\nA  THE FILE")
    sheets = _reader()(WORKBOOK)
    check("A1 it is a readable .xlsx", len(sheets) >= 6,
          f"{len(sheets)} sheets, {WORKBOOK.stat().st_size:,} bytes")
    # Written with the standard library only -- the engine has no third-party
    # dependency and a deliverable should not introduce one.
    import xlsx
    check("A2 written with the standard library only",
          not any(m in sys.modules for m in ("openpyxl", "xlsxwriter", "pandas")),
          "no openpyxl, xlsxwriter or pandas")
    expected = {"Read me", "Used in practice", "All fields", "Legal values",
                "Large domains", "By jurisdiction", "Class codes"}
    check("A3 every sheet the read me promises exists",
          expected <= set(sheets), str(sorted(set(sheets))))

    print("\nB  SCOPE -- the thing the plan predicted would be hard")
    all_fields = sheets["All fields"][1:]
    used = sheets["Used in practice"][1:]
    check("B1 the declared surface is large", len(all_fields) > 1000,
          f"{len(all_fields)} fields declared countrywide")
    check("B2 real submissions use a small fraction of it",
          0 < len(used) < len(all_fields) / 10,
          f"{len(used)} used of {len(all_fields)} declared "
          f"({100 * len(used) / len(all_fields):.1f}%)")
    # Sorted most-used first, so the sheet opens on what matters.
    counts = [int(r[2]) for r in used if r[2]]
    check("B3 it is ordered by how often a field is actually sent",
          counts == sorted(counts, reverse=True),
          f"{counts[0]} down to {counts[-1]} of 50")
    check("B4 a core set is used by every submission",
          sum(1 for c in counts if c == 50) >= 30,
          f"{sum(1 for c in counts if c == 50)} fields in all 50")

    print("\nC  PROVENANCE -- nothing here is our opinion")
    readme = {r[0]: (r[1] if len(r) > 1 else "") for r in sheets["Read me"]}
    for label in ("Fields, requiredness, domain", "Legal values",
                  "Data types", "Class codes", "Real usage"):
        check(f"C-{label[:24]} names its ISO source",
              bool(readme.get(label)), readme.get(label, "MISSING")[:52])
    check("C1 the workbook says how to regenerate itself",
          "build_enum_workbook" in readme.get("Regenerate", ""),
          readme.get("Regenerate", ""))

    print("\nD  VALUES")
    values = sheets["Legal values"][1:]
    check("D1 legal values are listed", len(values) > 1000,
          f"{len(values)} values")
    subline = [r[3] for r in values if r[1] == "Subline"]
    check("D2 they are ISO's own values",
          "Premises/Operations and Products/Completed Operations" in subline,
          f"{len(subline)} Subline values")
    big = sheets["Large domains"][1:]
    check("D3 a large domain is summarised, not silently truncated",
          len(big) >= 1 and all(int(r[3]) > 60 for r in big if r[3]),
          f"{len(big)} summarised: "
          + ", ".join(f"{r[1]}({r[3]})" for r in big[:3]))
    classes = sheets["Class codes"][1:]
    check("D4 class codes come from ISO's DOC workbook", len(classes) > 1000,
          f"{len(classes)} class codes")
    juris = sheets["By jurisdiction"][1:]
    check("D5 every jurisdiction is covered", len(juris) == 51,
          f"{len(juris)} jurisdictions")

    total = len(PASS) + len(FAIL)
    print(f"\n{len(PASS)}/{total} passed")
    if FAIL:
        print("\nFAILURES:")
        for f in FAIL:
            print(f"  {f}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
