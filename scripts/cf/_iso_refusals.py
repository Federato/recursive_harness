"""Cases where ISO refuses a policy and, since chunk 28 C28-05, ours refuses too: the expected result, not a failure.

C28-05 made a `SingleResult` lookup that matches no row refuse the policy (Property only), as ISO's service does. Scripts
that pinned "ISO refuses; ours $0" (OI-99 / OI-103's shape) now see ours refuse at the same table. Each entry names the
script, its case id, the table, and where ISO's own refusal is on record; `refused_as_iso` accepts exactly that refusal
and nothing else, so a refusal at any other table, or on any other case, still fails the script.

Evidence: C28-02's live table (`docs/CF-CHUNK28-REFUSALS.md`, `245_`, 2026-10-02) and C28-06's probes (`248_`,
2026-10-05, 8 of 8 refused at the same table and keys). One entry is NOT ISO-confirmed and says so: Puerto Rico has no
RaaS entitlement.
"""
from __future__ import annotations

import re
from pathlib import Path

#: script number -> {case id: (table, evidence)}
EXPECTED = {
    "42": {"2": ("SpecialClassDescriptionConvertedOption", "C28-06 P10")},
    "54": {"12  Group II territory, moved": ("BCEGFactor", "C28-06 P9")},
    "35": {"all three elected at once": ("MaxPeriodOfIndemnityFactor", "C28-06 P6")},
    "88": {"Case 4": ("EQClassToUse", "C28-06 P5")},
    "117": {"Z8": ("LeaseholdInterestAnnuityConstant", "C11-23 Z8, C28-02"),
            "Z9": ("LeaseholdInterestAnnuityConstant", "C11-23 Z9, C28-02")},
    "151": {"Z4": ("TerrorismTerritoryTier", "C13-13 Z4, C28-02")},
    "160": {"O4": ("IRPMConversion", "C14-10 O4, C28-02")},
    "162": {"E3": ("EQPercentageDeductibleFactor", "C24-15, C28-02")},
    "163": {"Z1": ("TotalRatingModicationStatCode", "C14-19 Z1, C28-02"),
            "Z8": ("TotalRatingModicationStatCode", "C14-19 Z8, C28-02"),
            "Z10": ("TotalRatingModicationStatCode", "C14-19 Z10, C28-02")},
    "170": {"Z5": ("TotalRatingModicationStatCode", "C15-11 Z5, C28-02")},
    "182": {"Z6": ("WatercraftExclBuybackFactor", "C17-12 Z6, C28-02")},
    "189": {"P-spp-KS": ("VacancyPermitFactors", "C18-16 KS, C28-02")},
    "193": {"R1": ("ManufacturersConsequentialLossAssumptionFactor", "C19-13 R1, C28-02")},
    "209": {"Z7": ("LossAssessmentRate", "C21-10 Z7, C28-02 (MRZ's shape)")},
    "210": {"T8": ("PerilExclusionIndicatorBasicAndSpecialStatCode", "C21-12 T8, C28-02")},
}

#: refusals on record but NOT confirmed at ISO (no entitlement), accepted and labelled as such
UNCONFIRMED = {
    ("45", "PR"): ("ProtectionClassStatCode", "Puerto Rico: no RaaS entitlement; ours refuses, ISO unknown"),
    ("46", "PR"): ("ProtectionClassStatCode", "Puerto Rico: no RaaS entitlement; ours refuses, ISO unknown"),
}


def table_of(exc) -> str | None:
    m = re.search(r"SingleResult matched NO row in '(\w+)'", str(exc))
    return m.group(1) if m else None


def expected(script: str, cid: str):
    num = Path(script).name.split("_", 1)[0]
    return EXPECTED.get(num, {}).get(cid) or UNCONFIRMED.get((num, cid))


def refused_as_iso(script: str, cid: str, exc, indent: str = "") -> bool:
    """True (and prints why) when `exc` is the refusal ISO gives for this case, at the same table."""
    want = expected(script, cid)
    if not want or table_of(exc) != want[0]:
        return False
    tag = "UNCONFIRMED at ISO" if (Path(script).name.split("_", 1)[0], cid) in UNCONFIRMED else "as ISO does"
    print(f"{indent}{cid}: ours REFUSES {tag} ({want[0]}; {want[1]}; C28-05)")
    return True


def without_oregon_territories(sub: dict) -> dict:
    """An Oregon policy made portable to another state, `152_`'s way: Oregon's building territories ("Portland",
    "Entire State") exist nowhere else and ISO refuses them (C28-06 P7 FL, P8 VA); since C28-05 ours refuses too. The
    territories are removed and the Group I territory factor pinned to 1.0 (a submitted, IsNull-guarded field)."""
    for cp in sub["CommercialPropertyTable"]["CommercialProperty"]:
        for loc in cp["CommercialPropertyLocationTable"]["CommercialPropertyLocation"]:
            loc.pop("BasicGroupIRatingTerr", None)
            loc.pop("BasicGroupIIRatingTerr", None)
            loc["BasicGroupIRatingTerrFactor"] = "1.0"
    return sub


RAAS = Path(__file__).resolve().parents[2] / "results" / "cf-raas"


def saved_iso_refusal(fixture_id: str) -> str | None:
    """The table ISO named when it refused this ISO fixture (`STC_CP000012003` -> `*_F-12003_refusal.json`), or None.

    Only the as-filed sends count: the `t` variants (a terrorism or tier edit) are other requests."""
    n = fixture_id.replace("STC_CP", "").lstrip("0")
    for p in sorted(RAAS.glob(f"*_F-{n.zfill(5)}_refusal.json")):
        m = re.search(r"Matrix: (\w+)", p.read_text(encoding="utf-8", errors="replace"))
        if m:
            return m.group(1)
    return None


def no_eq(o):
    """Drop every earthquake input (209_'s way): for a test about something else, on a fixture whose earthquake keys
    its state no longer files (ISO refuses those, and since C28-05 ours does too)."""
    if isinstance(o, dict):
        for k in [k for k in o if k.startswith("EQ")]:
            del o[k]
        for v in o.values():
            no_eq(v)
    elif isinstance(o, list):
        for x in o:
            no_eq(x)
    return o
