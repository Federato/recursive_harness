"""Stage 4 deliverable: one sample submission per jurisdiction, same risk.

The build plan asks for *"sample payloads built from the RAaS inputs, same class
code and exposure everywhere so state differences are visible and
attributable"*. That last word is the point: if the risk varies, a price
difference between two states says nothing.

So each sample is **the same risk** -- one location, one classification, class
code `50017`, `5,000,000` of gross sales, `1,000,000 CSL` occurrence and
`2,000,000 CSL` aggregate limits, no deductible, no rating plans -- and the only
things that vary are the ones that **must**:

* the **jurisdiction** and its product name
* the **territory codes**, taken from that jurisdiction's own ISO payload,
  because a territory is a state's own code and cannot be held constant
* the **four place-coded jurisdictions** (CA, FL, NY, TX) keep their explicit
  `TerrorismTerritory`, which E8 says cannot be derived from a ZIP

Writes `Engine_Payloads/<JURIS>/submission.json` and a reconciliation of what
each one prices to, so the spread across the country is one table.

    python scripts/build_sample_payloads.py
"""
from __future__ import annotations

import csv
import json
import sys
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from gl_engine import EditionResolver, ResolvedBook          # noqa: E402
from gl_engine.rating import Kernel, UNDERWRITING            # noqa: E402
from gl_engine.schema import Schema, validate                # noqa: E402

OUT = ROOT / "Engine_Payloads"
PAYLOADS = ROOT / "Payloads"
ASOF = "2026-08-01T00:00:00"

#: The one risk every sample carries. Chosen because the Oklahoma golden case
#: uses it, so one sample is checkable against an ISO-published answer.
CLASS_CODE = "50017"
EXPOSURE = 5000000.0

#: Fields held constant across every jurisdiction.
CONSTANT = {
    "Subline": "Premises/Operations and Products/Completed Operations",
    "PremOpsProdsCoverageForm": "Occurrence",
    "PremOpsProdsEachOccurrenceLimit": "1,000,000 CSL",
    "GeneralAggregateLimit": "2,000,000 CSL",
    "ProdsCompldOpsAggregateLimit": "2,000,000 CSL",
    "MedicalPaymentsExcl": "No",
    "ExperienceRatingApplies": "No",
    "ScheduleRatingModificationApplies": "No",
    "SizeOfRiskRatingApplies": "No",
    "ProdsWithdrawalCoverage": "No",
    "TerrorismCoverage": "No",
    "PremOpsBIDeductible": "No Deductible",
    "PremOpsPDDeductible": "No Deductible",
    "PremOpsBIPDDeductible": "No Deductible",
    "ProdsCompldOpsBIDeductible": "No Deductible",
    "ProdsCompldOpsPDDeductible": "No Deductible",
    "ProdsCompldOpsBIPDDeductible": "No Deductible",
}

#: Location fields that are the jurisdiction's own and must be carried over.
TERRITORY_FIELDS = ("PremisesOperationsTerritory", "PremisesOperationsTerr",
                    "ProdsCompldOpsTerritory", "LiquorLiabTerritory",
                    "LiquorLiabTerr", "TerrorismTerritory", "ZipCode")


#: The jurisdiction whose payload is used as the STRUCTURAL template when a
#: jurisdiction has none of its own. Oklahoma, because its shape is the one
#: checked against an ISO-published answer.
TEMPLATE_JURIS = "OK"


def source_payload(juris: str):
    p = PAYLOADS / juris / "1. Input.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8-sig"))


def from_domains(juris: str, schema) -> dict | None:
    """Build a sample for a jurisdiction with no payload of its own.

    Puerto Rico is the only one (the plan records it as the sole ERC
    jurisdiction without a RAaS payload). The structure comes from the template
    jurisdiction and **every territory comes from ISO's own domain table for
    this jurisdiction**, so nothing is invented -- PR files exactly one
    premises/operations territory and one products territory.
    """
    tmpl = source_payload(TEMPLATE_JURIS)
    if tmpl is None:
        return None
    out = deepcopy(tmpl)
    risk = out["body"]["GeneralLiability"][0]
    locs = risk.get("GeneralLiabilityLocation") or []
    if not locs:
        return None
    loc = locs[0]
    for col in TERRITORY_FIELDS:
        if col not in loc:
            continue
        legal = schema.legal_values("GeneralLiabilityLocation", col)
        if legal:
            loc[col] = legal[0]
        else:
            loc.pop(col, None)
    return out


def build(juris: str, src: dict) -> dict:
    """One sample, from that jurisdiction's own payload, normalised."""
    risk = deepcopy(src["body"]["GeneralLiability"][0])

    for k, v in CONSTANT.items():
        if k in risk:
            risk[k] = v
    risk["State"] = juris

    locs = risk.get("GeneralLiabilityLocation") or []
    if locs:
        loc = locs[0]
        keep = {k: loc[k] for k in TERRITORY_FIELDS if k in loc}
        classes = loc.get("GeneralLiabilityClassification") or []
        cls = deepcopy(classes[0]) if classes else {}
        cls["ClassCode"] = CLASS_CODE
        cls["PremOpsCovExposure"] = EXPOSURE
        cls["ProdsCompldOpsCovExposure"] = EXPOSURE
        cls["PremOpsPremiumBasis"] = "Gross Sales"
        cls["ProdsCompldOpsPremiumBasis"] = "Gross Sales"
        cls["OtherThanProdsCompldOpsCov"] = "Premises/Operations"
        cls["ProdsCompldOpsCov"] = "Products/Completed Operations"
        new_loc = {k: v for k, v in loc.items()
                   if k not in ("GeneralLiabilityClassification",)}
        new_loc.update(keep)
        new_loc["GeneralLiabilityClassification"] = [cls]
        risk["GeneralLiabilityLocation"] = [new_loc]

    return {
        "header": {"quoteback": "", "authorization": {}},
        "body": {
            "SchemeKeys": {"ProductName": f"General Liability {juris}",
                           "EffectiveDateTime": ASOF},
            "GeneralLiability": [risk],
        },
    }


def main() -> int:
    resolver = EditionResolver()
    kernel = Kernel(mode=UNDERWRITING, resolver=resolver)
    jurisdictions = sorted({p.identity.juris for p in resolver.packages
                            if p.identity.juris != "CW"})

    OUT.mkdir(exist_ok=True)
    rows = []
    for juris in jurisdictions:
        try:
            book = ResolvedBook(resolver.resolve(juris, ASOF[:10].replace("-", "")))
            schema = Schema.for_book(book)
        except Exception as exc:                            # noqa: BLE001
            rows.append([juris, "", "", "", f"schema: {exc}"[:80], "", ""])
            continue

        src = source_payload(juris) or from_domains(juris, schema)
        if src is None:
            rows.append([juris, "", "", "", "no source payload", "", ""])
            continue
        sample = build(juris, src)
        d = OUT / juris
        d.mkdir(exist_ok=True)
        (d / "submission.json").write_text(
            json.dumps(sample, indent=2), encoding="utf-8")

        findings = validate(sample, schema)
        errs = sum(1 for f in findings if f.level == "error")
        warns = sum(1 for f in findings if f.level == "warning")

        try:
            r = kernel.rate(sample)
            if not r.complete:
                rows.append([juris, "", errs, warns, str(r.stopped)[:80],
                             "", ""])
                continue
            rows.append([juris, str(r.premium), errs, warns, "",
                         " over ".join(r.packages),
                         ";".join(x.code for x in r.referrals)])
        except Exception as exc:                            # noqa: BLE001
            rows.append([juris, "", errs, warns,
                         f"{type(exc).__name__}: {exc}"[:80], "", ""])

    out_csv = ROOT / "scripts" / "erc" / "out" / "sample_payloads.csv"
    with open(out_csv, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["juris", "premium", "schema_errors", "schema_warnings",
                    "stopped", "packages", "referrals"])
        w.writerows(rows)

    rated = [r for r in rows if r[1]]
    print(f"SAMPLE SUBMISSIONS -- same risk, {len(jurisdictions)} jurisdictions")
    print()
    print(f"    written to Engine_Payloads/<JURIS>/submission.json")
    print(f"    rate end to end : {len(rated)} of {len(jurisdictions)}")
    print()
    print(f"    {'juris':6s} {'premium':>10s} {'err':>4s} {'warn':>5s}  notes")
    for r in rows:
        note = r[4] or (f"refer {r[6]}" if r[6] else "")
        print(f"    {r[0]:6s} {r[1] or '-':>10s} {str(r[2]):>4s} "
              f"{str(r[3]):>5s}  {note[:60]}")
    if rated:
        prem = sorted((int(r[1]), r[0]) for r in rated)
        print()
        print(f"    same risk, cheapest {prem[0][1]} {prem[0][0]:,} .. "
              f"dearest {prem[-1][1]} {prem[-1][0]:,}")
    print(f"\n[wrote {out_csv}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
