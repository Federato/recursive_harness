"""Commercial Property in the app: a state's sample, our rating, ISO's, and the two side by side.

`app.py` rates General Liability through `gl_engine.rating.Kernel`. Property has no kernel yet -- its chunk scripts
drive the shared interpreter directly (`119_payload_three_way.engine_premiums`) -- so this module does the same, from
the same public pieces: `cf_engine.resolve.book_for` for the rulebook in force, `gl_engine.interp.Interpreter` with
Property's rounding and null arithmetic (`cf_engine.config`), and the interpreter's `outcome` for refusals.

**The submission is ISO's request**, exactly what is sent to RAaS (`header` / `body.SchemeKeys` /
`body.CommercialProperty`), so one text box drives both answers. The engine reads ERC's `...Table` wrappers, which
`to_tree` restores, as 119_ does.

**The sample is one risk moved state to state**: an office building (class 0951, frame, 1-3 stories) with its
contents and Business Income with Extra Expense, all on the Special cause-of-loss form, so each record prices Basic
Group I, Basic Group II and Special. A state's own location inputs are read from its own filed tables, never typed in:
the Group II territory, symbol and BCEG (`scripts/cf/_state_inputs.localize_request`, chunk 28 C28-17), and here the
Group I territory, the Special (contents) territory, the wind hazard territory and the earthquake territory -- each
the state's first filed row, the way the chunk 1 and chunk 3 state sweeps pick them. Probed offline 2026-10-06: the
sample rates in 46 jurisdictions; ID, LA, MS and WA have no Property package and PR's Group I table is keyed
differently (PR is also off the ISO subscription).

    from property_rating import sample, rate
    rate(sample("OH"), compare=False)["premium"]
"""
from __future__ import annotations

import copy
import sys
import threading
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if getattr(sys, "frozen", False):        # the packaged app: this module sits in _internal, not _internal/scripts
    ROOT = Path(sys._MEIPASS)
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))

#: The sample's effective date: the date every chunk 28 state probe used (`_state_inputs` defaults to it).
EFFECTIVE = "2026-09-17"

#: The three records and three forms the sample prices, as ERC names their coverage records.
RECORDS = (("Building", "CommercialPropertyStructureBuilding"),
           ("Contents", "CommercialPropertyPersonalPropertyPrsnlProp"),
           ("Business Income", "CommercialPropertyBusinessIncome"))
FORMS = (("Group I", "BasicGroupI"), ("Group II", "BasicGroupII"), ("Special", "Special"))

#: Jurisdictions left out of the Property state list: PR's Group I rate is keyed on inputs the portable sample does
#: not carry, and ISO's subscription does not cover PR, so there is nothing to compare against there either.
NOT_OFFERED = {"PR": "Puerto Rico keys Group I differently and is not on the ISO subscription"}

TEMPLATE = {
    "header": {"quoteback": "", "authorization": {}},
    "body": {
        "SchemeKeys": {"ProductName": "Commercial Property OR", "EffectiveDateTime": f"{EFFECTIVE}T00:00:00"},
        "CommercialProperty": [{
            "State": "OR", "PolicyType": "Commercial Property Policy",
            "IRPMFactor": 1.0, "PackageModFactor": 1.0, "MultiPremiumAndDispersionCreditFactor": 1.0,
            "CommercialPropertyCyberIncidentExclusion": [{}],
            "CommercialPropertyLocation": [{
                "UnitNumber": 1, "ProtectClass": "3",
                "CommercialPropertyStructure": [{
                    "UnitNumber": 1, "RatingType": "Class", "ClassCode": "0951", "ConstructionType": "Frame",
                    "NumStories": "1-3", "CovType": "Building", "CauseOfLoss": "Special",
                    "Coinsurance": "80%", "Limit": 500000, "FullBldgValue": 500000,
                    "Deductible": "1,000", "TheftDeductible": "1,000", "WindstormOrHailDeductible": "1,000",
                    "SprinklerSystem": "None", "ValuationType": "Replacement Cost",
                    "RatingTypeBasicGroupII": "Class", "EQCovIndicator": "No Coverage",
                    "LossCostMultiplier": 1.0, "IncludedInBlkt": "No",
                    "PackageModFactor": 1.0, "MultiPremiumAndDispersionCreditFactor": 1.0,
                    "CommercialPropertyOccupClass": [{
                        "OccupCategory": "Offices", "ClassCode": "0951",
                        "CommercialPropertyPersonalProperty": [{
                            "CovType": "Personal Property", "CauseOfLoss": "Special", "Coinsurance": "80%",
                            "Limit": 150000, "FullPrsnlPropValue": 150000, "Deductible": "1,000",
                            "LossCostMultiplier": 1.0, "IncludedInBlkt": "No"}]}],
                    "CommercialPropertyBusinessIncome": [{
                        "CovType": "Business Income With Extra Expense", "TypeOfRisk": "Mercantile and Non-manufacturing",
                        "CauseOfLoss": "Special", "Coinsurance": "50%", "Limit": 200000,
                        "LossCostMultiplier": 1.0, "IncludedInBlkt": "No",
                        "MaxPeriod": "No", "MonthlyLimitOfIndemnity": "Not Applicable",
                        "FungusWetRotDryRotBacteriaCovIncrdPeriodRestorationIndicator": "No"}]}]}]}]}}

_LOCK = threading.Lock()
_STATES: list | None = None


def states() -> list:
    """The jurisdictions the Property corpus holds a package for, less `NOT_OFFERED`."""
    global _STATES
    with _LOCK:
        if _STATES is None:
            from cf_engine.resolve.resolver import CFEditionResolver
            _STATES = sorted(j for j in CFEditionResolver().jurisdictions if j != "CW" and j not in NOT_OFFERED)
        return list(_STATES)


def _first(book, table: str, col: str, juris: str | None = None):
    """The first filed value of `col` in `table` (the state's own rows only when `juris` is given), or None."""
    try:
        t = book.table(table)
    except Exception:                                       # noqa: BLE001 - a state that files no such table
        return None
    rows = [r for r in t.rows if juris is None or r[t.col("StateCode")] == juris]
    return rows[0][t.col(col)] if rows else None


def sample(juris: str, effective: str = EFFECTIVE) -> dict:
    """The sample risk as an ISO request for `juris`, with that state's own location inputs."""
    from _state_inputs import localize_request
    from cf_engine.resolve import book_for
    asof = effective.replace("-", "")
    q = copy.deepcopy(TEMPLATE)
    q["body"]["SchemeKeys"].update(ProductName=f"Commercial Property {juris}", EffectiveDateTime=f"{effective}T00:00:00")
    q["body"]["CommercialProperty"][0]["State"] = juris
    localize_request(q, juris, asof)
    book = book_for(juris, asof)
    loc = q["body"]["CommercialProperty"][0]["CommercialPropertyLocation"][0]
    terr = _first(book, "RatingTerritoryGroupIFactor", "BasicGroupIRatingTerritory")
    if terr is not None:
        loc["BasicGroupIRatingTerr"] = terr
    else:
        loc["BasicGroupIRatingTerrFactor"] = 1.0            # the state files no Group I territories (chunk 13's way)
    for table, col, field in (("PrsnlPropTerrMultiplier", "SpecialRatingTerr", "SpecialRatingTerr"),
                              ("GeographicWindHazardLevel", "GeographicWindHazardLevelTerritory",
                               "GeographicWindHazardLevelTerritory")):
        v = _first(book, table, col)
        if v is not None:
            loc[field] = v
    v = _first(book, "BCEGEQFactor", "EQTerr", juris)       # SC keys its BCEG factor on it even without EQ
    if v is not None:
        loc["EQTerr"] = v
    if juris == "CA":
        # California files no BasicGroupIRate: Group I is split into District I / II tables and the submitter picks
        # the district (chunk 4; AK derives its own from the territory). Without it Group I prices $0, silently.
        loc["District"] = "District I"
    _drop_withdrawn(q["body"]["CommercialProperty"][0], _withdrawn(book))
    return q


def _withdrawn(book) -> set:
    """The records (form `TableName`s) the state files only as withdrawn (`Status` "D") in its own `Pages` table.

    A state that does not offer a form marks it "D": FL withdrew the Cyber Incident Exclusion (CP 10 75), and ISO
    refuses a FL policy that attaches it, at FL's empty `CyberIncidentExclusionFactors` (OI-133, 2026-10-06).
    """
    if not book.state.has("FormPage", "Pages"):
        return set()
    t = book.state.table("FormPage", "Pages")
    tn, st = t.header.index("TableName"), t.header.index("Status")
    filed: dict = {}
    for r in t.rows:
        filed.setdefault(r[tn], set()).add(r[st])
    return {name for name, sts in filed.items() if sts == {"D"}}


def _drop_withdrawn(node, withdrawn: set) -> None:
    """Remove every attached record the state has withdrawn, at any depth: the sample offers only forms it files."""
    if isinstance(node, dict):
        for k in [k for k in node if k in withdrawn]:
            del node[k]
        for v in node.values():
            _drop_withdrawn(v, withdrawn)
    elif isinstance(node, list):
        for v in node:
            _drop_withdrawn(v, withdrawn)


def to_tree(obj):
    """ISO JSON -> the engine's submission shape: `X: [..]` becomes `XTable: {X: [..]}` (119_'s `to_tree`)."""
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if isinstance(v, list) and all(isinstance(i, dict) for i in v):
                out[f"{k}Table"] = {k: [to_tree(i) for i in v]}
            else:
                out[k] = to_tree(v)
        return out
    if isinstance(obj, float) and obj.is_integer():
        return str(int(obj)) if obj >= 1000 else str(obj)
    return obj if isinstance(obj, list) else (None if obj is None else str(obj))


def _juris(payload: dict) -> str:
    return ((payload.get("body", {}).get("SchemeKeys", {}).get("ProductName") or "").split() or [""])[-1]


def _num(v) -> str:
    """A premium as plain text: ISO's 1045.0 and our 1045 both read "1045"."""
    d = Decimal(str(v))
    return str(d.quantize(Decimal(1))) if d == d.to_integral_value() else str(d.normalize())


def _cells(premiums: dict) -> tuple[list, list]:
    """(rows of the record x form grid, every other coverage that carries a premium) from {coverage: premium}."""
    used, grid = set(), []
    for label, prefix in RECORDS:
        row = {"record": label, "forms": {}}
        for form, suffix in FORMS:
            name = f"{prefix}{suffix}Coverage"
            used.add(name)
            row["forms"][form] = _num(premiums[name]) if name in premiums else None
        grid.append(row)
    other = [{"coverage": k, "premium": _num(v)} for k, v in sorted(premiums.items())
             if k not in used and v != 0]
    return grid, other


def _engine(payload: dict):
    from cf_engine.config import NULL_ARITHMETIC, ROUNDING
    from cf_engine.resolve import book_for
    from gl_engine.interp.interpreter import Interpreter
    from gl_engine.interp.tree import Node
    juris = _juris(payload)
    eff = payload["body"]["SchemeKeys"]["EffectiveDateTime"][:10]
    book = book_for(juris, eff.replace("-", ""))
    res = book.resolution
    packages = [res.state.pkg_id] + ([res.parent.pkg_id] if res.parent is not None else [])
    sub = {"EffDate": f"{eff[5:7]}/{eff[8:10]}/{eff[:4]}",
           "CommercialPropertyTable": {"CommercialProperty": [to_tree(cp) for cp in payload["body"]["CommercialProperty"]]}}
    ip = Interpreter(book, rounding=ROUNDING, trace=False, null_arithmetic=NULL_ARITHMETIC)
    data = Node.from_dict(f"MasterCF{juris}", sub)
    try:
        ip.run(data)
    except Exception as exc:                                # noqa: BLE001 - a refusal is an answer, shown as one
        return juris, eff, packages, None, {}, [], {"status": "refused",
                                                    "reasons": [{"kind": getattr(exc, "outcome_kind", "refused"),
                                                                 "detail": str(exc)[:400]}]}
    premiums: dict = {}

    def walk(node):
        for c in node.children:
            if c.tag.endswith("Coverage"):
                p = c.first("Premium")
                if p is not None and p.text not in (None, ""):
                    premiums[c.tag] = premiums.get(c.tag, Decimal(0)) + Decimal(p.text)
            walk(c)
    walk(data)
    cp = data.first("CommercialPropertyTable").first("CommercialProperty")
    total = cp.first("Premium")
    return (juris, eff, packages, total.text if total is not None else None, premiums,
            list(ip.messages), ip.outcome)


def _iso_premiums(body) -> dict:
    """{coverage: premium} summed over ISO's response tree."""
    out: dict = {}

    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if k.endswith("Coverage") and isinstance(v, dict) and "Premium" in v:
                    out[k] = out.get(k, Decimal(0)) + Decimal(str(v.get("Premium") or 0))
                walk(v)
        elif isinstance(node, list):
            for i in node:
                walk(i)
    walk(body)
    return out


def compare(payload: dict, ours: dict, client, no_iso=frozenset()) -> dict:
    """ISO's answer for the same request, and whether it agrees with `ours` (the dict `rate` builds)."""
    juris = _juris(payload)
    if juris in no_iso:
        return {"available": False,
                "reason": f"{juris} is not on the ISO subscription, so there is no external answer to compare against"}
    if client is None:
        return {"available": False, "reason": "ISO client not configured"}
    try:
        live = client.rate(payload)
    except Exception as exc:                                # noqa: BLE001
        return {"available": False, "reason": f"{type(exc).__name__}: {exc}"[:300]}
    body = live.get("Body", {})
    cp = (body.get("CommercialProperty") or [{}])[0]
    iso_total = cp.get("Premium")
    parts = live.get("Header", {}).get("Scheme", "").split()
    iso_pkg = f"CF_{parts[1]}_{parts[2]}_{parts[3]}" if len(parts) >= 4 else ""
    grid, other = _cells(_iso_premiums(body))
    agrees = (iso_total is not None and ours.get("premium") is not None
              and Decimal(str(iso_total)) == Decimal(ours["premium"]))
    msgs = [m.get("Description", "") for kind in (body.get("RatingMessages") or {}).values()
            if isinstance(kind, list) for m in kind if isinstance(m, dict)]
    return {
        "available": True,
        "premium": _num(iso_total) if iso_total is not None else None,
        "agrees": agrees,
        "delta": _num(Decimal(ours["premium"]) - Decimal(str(iso_total)))
                 if iso_total is not None and ours.get("premium") is not None else "",
        "package": iso_pkg,
        "edition_agrees": (iso_pkg == ours["packages"][0]) if iso_pkg else None,
        "grid": grid, "other": other, "messages": msgs,
    }


def rate(payload: dict, compare_with=None, no_iso=frozenset()) -> dict:
    """Rate a Property request; with `compare_with` (a RAaS client, or a callable returning one) also ask ISO."""
    juris, eff, packages, total, premiums, messages, outcome = _engine(payload)
    result = {"line": "property", "jurisdiction": juris, "asof": eff, "packages": packages,
              "outcome": outcome, "messages": messages,
              "complete": outcome.get("status") != "refused" and total is not None}
    if result["complete"]:
        grid, other = _cells(premiums)
        result.update(premium=_num(total), grid=grid, other=other)
    else:
        result["stopped"] = "; ".join(r.get("detail", "") for r in outcome.get("reasons", [])) or "did not rate"
    if compare_with is not None:
        client = compare_with() if callable(compare_with) else compare_with
        result["iso"] = compare(payload, result, client, no_iso) if result["complete"] else {
            "available": False, "reason": "our engine refused, so ISO was not called"}
    return result


if __name__ == "__main__":                                  # offline: rate the sample in the states given
    for j in sys.argv[1:] or ["OR"]:
        r = rate(sample(j))
        print(j, r.get("premium") or r.get("stopped"), [(g["record"], g["forms"]) for g in r.get("grid", [])])
