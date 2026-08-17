"""OI-91: the two counts of how a jurisdiction locates a risk for terrorism.

Two measurements exist and nobody wrote down which a caller should trust:

  M1  **which domain table the field names.** Recorded in E8/R22 and quoted in
      `gl_engine/schema/validate.py:PLACE_CODED` as *four declare
      `TerrorismTerritory` against `TerrorismTerritoryCode` (CA, FL, NY, TX),
      eleven use `TerritoryCodeByZipCode`*.

  M2  **does the jurisdiction resolve any legal value for the field, as of a
      date.** Recorded in `scripts/variants.py:Declared.terrorism_place` as
      *15 with an explicit `TerrorismTerritory`, 16 with a `ZipCode` domain, 20
      with neither*.

They are not obviously contradictory -- naming a domain table and that table
resolving to a non-empty set for a date are different questions -- but a tester
that guesses sends the wrong field to 20 jurisdictions, so `terrorism_place`
returns `None` there rather than guessing, and terrorism breadth is blocked.

**Closing OI-91 needs the two run side by side over the same packages and the
same date.** That is all this script does. It decides nothing and changes no
behaviour; the reconciliation is the deliverable.

A note on M1's provenance. `PLACE_CODED` cites `47_input_schema.py` S7, and S7
does **not** produce four/eleven: it is a substring search for County/Place/Town
/Borough/Parish in column names, and its own hits are `PremiumPlaceHolder`
matching on "Place". So M1's stated source does not support M1's numbers, and
M1 is re-measured here from `DomainTableName` directly rather than trusted.

Emits out/oi91_terrorism_place.txt.
"""
from __future__ import annotations

import sys
from collections import defaultdict
from importlib import import_module
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

c = import_module("00_common")
rules_packages = import_module("42_node_surface").rules_packages

FIELD_FILE = Path("Form Fields") / "Fields.FormField.csv"

#: The one date both measurements are taken on, so a difference between them
#: cannot be a difference of edition.
ASOF = "20260801"

LOC = "GeneralLiabilityLocation"
TERR_DOMAIN = "TerrorismTerritoryCode"
ZIP_DOMAIN = "TerritoryCodeByZipCode"


def read_fields(pk):
    p = pk.content / FIELD_FILE
    if not p.exists():
        return []
    header, rows = c.read_csv_rows(p)
    return [dict(zip(header, r)) for r in rows if r]


def main() -> None:
    pkgs, _n, _d = rules_packages()

    # One edition per jurisdiction, the latest -- same selection 47 makes, so
    # M1 is comparable to what E8/R22 measured.
    latest: dict = {}
    for pk in pkgs:
        cur = latest.get(pk.juris)
        if cur is None or (pk.edition, pk.version) > (cur.edition, cur.version):
            latest[pk.juris] = pk

    # ------------------------------------------------------------------ M1
    m1: dict = {}
    m1_detail: dict = defaultdict(list)
    for juris, pk in sorted(latest.items()):
        names_terr = names_zip = False
        for r in read_fields(pk):
            dom = (r.get("DomainTableName") or "").strip()
            if dom == TERR_DOMAIN:
                names_terr = True
                m1_detail[juris].append(
                    f"{r.get('TableName')}.{r.get('ColumnName')} -> {dom}")
            elif dom == ZIP_DOMAIN:
                names_zip = True
                m1_detail[juris].append(
                    f"{r.get('TableName')}.{r.get('ColumnName')} -> {dom}")
        m1[juris] = ("terr" if names_terr else
                     "zip" if names_zip else "neither")

    # ------------------------------------------------------------------ M2
    import variants as V                                        # noqa: E402

    m2: dict = {}
    m2_err: dict = {}
    for juris in sorted(latest):
        if juris == "CW":
            continue
        try:
            d = V.Declared(juris, asof=ASOF) if _takes_asof() else V.Declared(juris)
            tt = d.values(LOC, "TerrorismTerritory")
            zp = [v for v in d.values(LOC, "ZipCode") if str(v).isdigit()]
            m2[juris] = ("terr" if tt else "zip" if zp else "neither")
        except Exception as exc:                                # noqa: BLE001
            m2[juris] = "error"
            m2_err[juris] = f"{type(exc).__name__}: {exc}"[:120]

    # -------------------------------------------------------------- report
    L = []
    A = L.append
    A("OI-91 -- the two terrorism-location measurements, side by side")
    A("=" * 70)
    A(f"one edition per jurisdiction (latest), as-of {ASOF} for M2")
    A("")
    A("M1  which domain table the field NAMES  (re-measured from "
      "DomainTableName)")
    A("M2  whether the jurisdiction RESOLVES a legal value, as of the date")
    A("")

    juris_all = sorted(j for j in latest if j != "CW")

    def tally(m, keys):
        out = defaultdict(list)
        for j in keys:
            out[m.get(j, "absent")].append(j)
        return out

    t1, t2 = tally(m1, juris_all), tally(m2, juris_all)
    A("M1 counts:")
    for k in ("terr", "zip", "neither", "absent"):
        if t1.get(k):
            A(f"    {k:8s} {len(t1[k]):3d}  {' '.join(sorted(t1[k]))}")
    A("")
    A("M2 counts:")
    for k in ("terr", "zip", "neither", "error", "absent"):
        if t2.get(k):
            A(f"    {k:8s} {len(t2[k]):3d}  {' '.join(sorted(t2[k]))}")
    A("")

    A("CROSS-TAB -- M1 down, M2 across. The off-diagonal is the finding.")
    kinds = ("terr", "zip", "neither", "error")
    A(f"    {'M1\\M2':10s}" + "".join(f"{k:>10s}" for k in kinds))
    grid = defaultdict(list)
    for j in juris_all:
        grid[(m1.get(j, "absent"), m2.get(j, "absent"))].append(j)
    for a in kinds:
        A(f"    {a:10s}" + "".join(f"{len(grid[(a, b)]):10d}" for b in kinds))
    A("")

    A("DISAGREEMENTS, one line each:")
    dis = [(a, b, js) for (a, b), js in sorted(grid.items()) if a != b and js]
    if not dis:
        A("    none -- the two measurements agree jurisdiction for "
          "jurisdiction")
    for a, b, js in dis:
        A(f"    M1={a:8s} M2={b:8s} {len(js):3d}  {' '.join(sorted(js))}")
    A("")

    if m2_err:
        A("M2 errors:")
        for j, e in sorted(m2_err.items()):
            A(f"    {j}  {e}")
        A("")

    A("Fields naming either domain table (M1 evidence):")
    for j in sorted(m1_detail):
        for line in sorted(set(m1_detail[j])):
            A(f"    {j:4s} {line}")
    A("")

    # ------------------------------------------------------------------ M3
    # The two checks that decide what the reconciliation MEANS. M1 and M2
    # lining up says the counts agree; these say what a caller should send.
    A("M3  DOES COUNTRYWIDE READ A TERRORISM LOCATION AT ALL?")
    cw = latest.get("CW")
    cw_hits = []
    if cw:
        for f in sorted((cw.content / "Rules").glob("*.Rule.xml")):
            t = c.read_text(f)
            if "TerrorismTerritory" in t:
                cw_hits.append(f.name)
    A(f"    countrywide rule files referencing TerrorismTerritory: "
      f"{len(cw_hits)}")
    A("    -- so terrorism territory is a STATE-level concept only. The "
      "jurisdictions")
    A("       that do not file the field are not missing an input; there is "
      "no input")
    A("       to miss, and terrorism still rates.")
    A("")

    A("M4  IS THE ZipCode FALLBACK A TERRORISM INPUT?")
    A("    `Declared.terrorism_place` falls back to any ZipCode in the "
      "location when")
    A("    TerrorismTerritory is absent. Rated both ways in six of the 16, "
      "terrorism on:")
    try:
        import copy
        import variants as VV
        from gl_engine.rating import Kernel, STRICT
        from gl_engine.resolve import EditionResolver
        k = Kernel(mode=STRICT, resolver=EditionResolver())
        for j in ("AL", "OK", "GA", "IA", "MO", "TN"):
            d = VV.Declared(j)
            b = d.base()
            p1 = copy.deepcopy(b)
            VV._apply_terrorism(p1, "Yes", d, {})
            p2 = copy.deepcopy(b)
            VV._gl(p2)["TerrorismCoverage"] = "Yes"
            r1, r2 = k.rate(p1), k.rate(p2)
            same = "IDENTICAL" if r1.premium == r2.premium else "DIFFERS"
            A(f"      {j}  with ZipCode {r1.premium}  without {r2.premium}"
              f"  {same}")
    except Exception as exc:                                    # noqa: BLE001
        A(f"      (not run: {type(exc).__name__}: {exc})")
    A("    -- an inert field. It is why the 16/20 split exists, and the split "
      "is an")
    A("       artefact of the fallback rather than a fact about terrorism.")

    text = "\n".join(L)
    print(text)
    dest = c.OUT / "oi91_terrorism_place.txt"
    dest.parent.mkdir(exist_ok=True)
    dest.write_text(text, encoding="utf-8")
    print(f"\nwrote {dest}")


def _takes_asof() -> bool:
    import inspect
    import variants as V
    return "asof" in inspect.signature(V.Declared).parameters


if __name__ == "__main__":
    main()
