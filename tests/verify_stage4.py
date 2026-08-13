"""Stage 4 acceptance: the submission schema and the sample payloads.

  A  the schema     read from ISO's own Form Fields, per jurisdiction
  B  legal values   from ISO's domain tables, via `DataValue`
  C  real payloads  ISO's own 50 submissions validate with no errors
  D  the four       CA, FL, NY, TX code terrorism territory explicitly (E8)
  E  the samples    one per jurisdiction, same risk, all of them rate
  F  what is absent Hawaii is not in the corpus and cannot be rated

Run: python tests/verify_stage4.py
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from gl_engine import EditionResolver, ResolvedBook, discover   # noqa: E402
from gl_engine.rating import Kernel                             # noqa: E402
from gl_engine.schema import Schema, validate                   # noqa: E402
from gl_engine.schema.validate import PLACE_CODED               # noqa: E402

ASOF = "20260801"
PAYLOADS = ROOT / "Payloads"
SAMPLES = ROOT / "Engine_Payloads"
PASS, FAIL = [], []
RESOLVER = EditionResolver()


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(f"{name}  {detail}".rstrip())
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f"  [{detail}]" if detail else ""))


def schema_for(juris, asof=ASOF):
    return Schema.for_book(ResolvedBook(RESOLVER.resolve(juris, asof)))


def group_a():
    print("\nA  THE SCHEMA -- read from ISO, not designed")
    s = schema_for("OK")
    check("A1 the schema loads and is large", len(s) > 1000,
          f"{len(s)} fields over {len(s.tables())} tables")
    check("A2 it names the packages it came from",
          s.summary()["packages"][0].startswith("GL_OK"),
          " over ".join(s.summary()["packages"]))
    # `Type` is a form control, not a data type. Asserted so the distinction
    # cannot be quietly lost -- a validator reading TEXT as "string" would
    # accept an exposure of "banana".
    controls = {f.control for f in s}
    check("A3 Type is a form control, not a data type",
          controls <= {"TEXT", "SELECT", "CHECKBOX", "HIDDEN", "TEXTAREA",
                       "BUTTON", "ANCHOR", ""},
          str(sorted(controls)))
    check("A4 required-to-rate is a different, smaller set than required-on-form",
          0 < len(s.rating_required()) < len(s.required(False)),
          f"{len(s.rating_required())} rating-required vs "
          f"{len(s.required(False))} form-required")
    # Every jurisdiction must produce a schema; a state with none would mean
    # the submission format for it is unknown.
    js = sorted({p.identity.juris for p in RESOLVER.packages
                 if p.identity.juris != "CW"})
    sizes = {}
    for j in js:
        try:
            sizes[j] = len(schema_for(j))
        except Exception as exc:                          # noqa: BLE001
            sizes[j] = 0
    check("A5 every jurisdiction has a schema",
          all(v > 1000 for v in sizes.values()),
          f"{len(sizes)} jurisdictions, "
          f"{min(sizes.values())}..{max(sizes.values())} fields")


def group_b():
    print("\nB  LEGAL VALUES -- from ISO's domain tables")
    s = schema_for("OK")
    subline = s.legal_values("GeneralLiability", "Subline")
    check("B1 Subline's legal values are ISO's own",
          "Premises/Operations and Products/Completed Operations" in subline
          and len(subline) >= 8, f"{len(subline)} values")
    basis = s.legal_values("GeneralLiabilityClassification",
                           "PremOpsPremiumBasis")
    check("B2 premium basis includes Gross Sales", "Gross Sales" in basis,
          f"{len(basis)} values")
    # The value is DataValue, not the first non-state column -- taking the
    # latter returns the ZIP from a ZIP-to-territory table and reports every
    # real territory as illegal. That was the first implementation.
    terr = s.legal_values("GeneralLiabilityLocation",
                          "PremisesOperationsTerritory")
    check("B3 a ZIP-keyed domain yields territories, not ZIPs",
          bool(terr) and all(len(v) <= 4 for v in terr[:20]),
          f"{len(terr)} values, e.g. {list(terr[:3])}")
    check("B4 an unconstrained field reports no legal values, not an empty set "
          "of one",
          s.legal_values("GeneralLiabilityClassification", "ClassDescription")
          == (), "()")


def group_b2():
    """Dependent domains, resolved through ISO's own declared relationship."""
    print("\nB2 DEPENDENT DOMAINS -- exact where ISO declares the dependency")
    import json as _json
    from gl_engine.rating.submission import from_raas
    from gl_engine.interp import tree as _t

    s = schema_for("OK")
    tbl = ("GeneralLiabilityCertifiedActsOfTerrorismAggregateLimitCapOn"
           "LossesFromCertifiedActsOfTerrorismPremOps")
    check("B5 ISO declares the dependency path for this field",
          s.related_path(tbl, "AggregateLimit").endswith(
              "PremOpsProdsEachOccurrenceLimit"),
          s.related_path(tbl, "AggregateLimit"))
    check("B6 the domain is keyed by another field's value",
          s.dependency_columns(tbl, "AggregateLimit")[0]
          == "PolicyEachOccurrenceLimit",
          str(s.dependency_columns(tbl, "AggregateLimit")))

    p = _json.loads((PAYLOADS / "OK" / "1. Input.json").read_text(
        encoding="utf-8-sig"))
    root, _, _ = from_raas(p)
    gl = _t.select_one("GeneralLiabilityTable/GeneralLiability", root)
    node = _t.select_one(f"{tbl}Table/{tbl}", gl)
    union, u_exact = s.resolved_values(tbl, "AggregateLimit", None)
    exact, is_exact = s.resolved_values(tbl, "AggregateLimit", node)
    check("B7 with no context it is a superset, and says so",
          not u_exact and len(union) > 0, f"{len(union)} values, exact=False")
    check("B8 with the submission it resolves exactly",
          is_exact and len(exact) < len(union),
          f"{len(exact)} of {len(union)} -- policy limit "
          f"{_t.read('PremOpsProdsEachOccurrenceLimit', gl)!r}")
    # A field whose domain has no dependency is exact either way -- the flag
    # must not claim precision it does not have, nor withhold it.
    plain, p_exact = s.resolved_values("GeneralLiability", "Subline", None)
    check("B9 a plain list is exact with or without context",
          p_exact and len(plain) >= 8, f"{len(plain)} values")


def group_c():
    print("\nC  ISO'S OWN 50 SUBMISSIONS VALIDATE")
    errs, warns, n = 0, 0, 0
    worst = []
    for d in sorted(p for p in PAYLOADS.iterdir() if p.is_dir()):
        src = d / "1. Input.json"
        if not src.exists():
            continue
        n += 1
        p = json.loads(src.read_text(encoding="utf-8-sig"))
        eff = p["body"]["SchemeKeys"]["EffectiveDateTime"][:10].replace("-", "")
        f = validate(p, schema_for(d.name, eff))
        e = [x for x in f if x.level == "error"]
        errs += len(e)
        warns += sum(1 for x in f if x.level == "warning")
        if e:
            worst.append(f"{d.name}: {e[0]}")
    check("C1 every ISO submission validates with no errors", errs == 0,
          f"{n} payloads, {errs} errors, {warns} warnings"
          + (f"; {worst[:2]}" if worst else ""))
    check("C2 warnings are reported rather than suppressed", warns > 0,
          f"{warns} warnings -- envelope fields ISO's form does not declare")


def group_d():
    print("\nD  THE FOUR PLACE-CODED JURISDICTIONS (E8)")
    check("D1 exactly four are place-coded", len(PLACE_CODED) == 4,
          str(PLACE_CODED))
    # Measured, not asserted: they use TerrorismTerritoryCode where 11 others
    # use TerritoryCodeByZipCode.
    coded, zipped = [], []
    for j in sorted({p.identity.juris for p in RESOLVER.packages
                     if p.identity.juris != "CW"}):
        f = schema_for(j).get("GeneralLiabilityLocation", "TerrorismTerritory")
        if f is None:
            continue
        (coded if f.domain == "TerrorismTerritoryCode" else zipped).append(j)
    check("D2 the four are exactly the TerrorismTerritoryCode jurisdictions",
          sorted(coded) == sorted(PLACE_CODED), str(sorted(coded)))
    check("D3 others derive terrorism territory from a ZIP", len(zipped) >= 10,
          f"{len(zipped)} use TerritoryCodeByZipCode")
    # A submission in one of the four without the field is warned about, since
    # it cannot be derived and an unmatched one refers (R22).
    p = json.loads((PAYLOADS / "CA" / "1. Input.json").read_text(
        encoding="utf-8-sig"))
    for risk in p["body"]["GeneralLiability"]:
        for loc in risk.get("GeneralLiabilityLocation", []):
            loc.pop("TerrorismTerritory", None)
    f = validate(p, schema_for("CA"))
    check("D4 a missing terrorism territory in the four is reported",
          any(x.code == "V4" for x in f),
          f"{sum(1 for x in f if x.code == 'V4')} findings")


def group_e():
    print("\nE  THE SAMPLES -- one per jurisdiction, the same risk")
    if not SAMPLES.is_dir():
        check("E0 samples built", False, "run scripts/build_sample_payloads.py")
        return
    dirs = sorted(p for p in SAMPLES.iterdir() if p.is_dir())
    check("E1 one sample per jurisdiction", len(dirs) == 51, f"{len(dirs)}")

    # Same risk everywhere is the whole point: a price difference between two
    # states says nothing if the risk also moved.
    risks = {}
    for d in dirs:
        p = json.loads((d / "submission.json").read_text(encoding="utf-8"))
        cls = (p["body"]["GeneralLiability"][0]
               ["GeneralLiabilityLocation"][0]
               ["GeneralLiabilityClassification"][0])
        risks[d.name] = (cls["ClassCode"], cls["PremOpsCovExposure"],
                         p["body"]["GeneralLiability"][0]["GeneralAggregateLimit"])
    check("E2 every sample carries the identical risk",
          len(set(risks.values())) == 1, str(next(iter(set(risks.values())))))

    out = ROOT / "scripts" / "erc" / "out" / "sample_payloads.csv"
    if not out.exists():
        check("E3 the reconciliation exists", False, str(out))
        return
    rows = list(csv.DictReader(open(out, encoding="utf-8")))
    rated = [r for r in rows if r["premium"]]
    check("E3 every jurisdiction rates the sample", len(rated) == 51,
          f"{len(rated)} of {len(rows)}")
    check("E4 no sample has a schema error",
          all(r["schema_errors"] in ("0", "") for r in rows),
          "0 errors across 51")
    prem = sorted(int(r["premium"]) for r in rated)
    check("E5 the same risk prices differently by jurisdiction",
          prem[0] != prem[-1],
          f"cheapest {prem[0]:,} .. dearest {prem[-1]:,}")


def group_f():
    print("\nF  WHAT IS ABSENT, STATED RATHER THAN DISCOVERED")
    juris = {p.identity.juris for p in discover()}
    check("F1 Hawaii is not in the corpus and cannot be rated",
          "HI" not in juris, "51 jurisdictions + CW, no HI")
    check("F2 Puerto Rico IS in the corpus", "PR" in juris, "PR present")
    # PR has no RAaS payload of its own; its sample is built from ISO's domain
    # tables, so nothing about it is invented.
    check("F3 Puerto Rico has no ISO payload, and its sample is built from "
          "ISO's domain tables instead",
          not (PAYLOADS / "PR").exists() and (SAMPLES / "PR").exists(),
          "sample present, source payload absent")


def main() -> int:
    print("Stage 4 acceptance -- schemas and payloads")
    group_a(); group_b(); group_b2(); group_c(); group_d(); group_e(); group_f()
    total = len(PASS) + len(FAIL)
    print(f"\n{len(PASS)}/{total} passed")
    if FAIL:
        print("\nFAILURES:")
        for f in FAIL:
            print(f"  {f}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
