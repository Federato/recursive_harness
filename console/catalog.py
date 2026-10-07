"""The dimension catalog (TC-26): what a test plan may vary, per line and state, read from ISO's own files.

  * **GL** is `variants`' controls (the ones `/tester` and the Workbench offer): each control's legal values come from
    ISO's declared domains for the state and date (`Control.options`). D20's pieces are already there: the class code
    is keyed by the premium basis (**basis-first**), `classifications` sets several classes (**multi-class**), and the
    effective date offers the state's own package dates.
  * **CP** had no catalog. Its dimensions are the request fields the coverages turn on, each with its legal values
    from the state's domain tables (the schema reads `Domain<name>.DomainTable.csv` exactly as GL's does): cause of
    loss, construction, stories, coinsurance, deductibles, sprinklers, valuation, BCEG, territory, occupancy (category
    first, then its class codes from `OccupCategoryRiskSeverity`: basis-first for Property -- ISO files nearly the same
    ~154 class codes under every category, the category being a rating input of its own, so the list is the category's
    legal set rather than a partition), limits, and the effective date from the state's own package dates. Blanket-only
    values are left out (a plan varies a single-location risk). `cp_build` applies a CP config to the state's sample.

Every dimension names its **edges** (its first and last legal value, or the bounds of a range), which the plan
builder uses for edge cases, and the matrix coverage it exercises.
"""
from __future__ import annotations

import copy
import sys
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for _p in (ROOT / "scripts", ROOT / "scripts" / "cf"):
    if str(_p) not in sys.path:
        sys.path.append(str(_p))

CP_EFFECTIVE = "2026-09-17"          # the sample's date (property_rating.EFFECTIVE), the default for a CP plan

#: CP dimensions: (id, label, group, coverage, where it is set, engine (table, column) for its domain, fixed values).
#: `where`: "bldg" (the building), "bpp" (personal property), "bi" (business income), "loc" (the location),
#: "occ" (occupancy class), "all" (building, BPP and BI alike).
CP_DIMS = (
    ("cause_of_loss", "Cause of loss", "Coverage form", "Causes of loss", "all", None, ("Basic", "Broad", "Special")),
    ("construction", "Construction", "Building", "Building", "bldg", ("CommercialPropertyStructure", "ConstructionType"), ()),
    ("stories", "Stories", "Building", "Building", "bldg", ("CommercialPropertyStructure", "NumStories"), ()),
    ("bldg_coinsurance", "Building coinsurance", "Building", "Building", "bldg", ("CommercialPropertyStructure", "Coinsurance"), ()),
    ("bldg_deductible", "Deductible", "Building", "Building", "bldg", ("CommercialPropertyStructure", "Deductible"), ()),
    ("wind_hail_deductible", "Wind / hail deductible", "Building", "Wind/hail ded.", "bldg",
     ("CommercialPropertyStructure", "WindstormOrHailDeductible"), ()),
    ("sprinkler", "Sprinklers", "Building", "Building", "bldg", ("CommercialPropertyStructure", "SprinklerSystem"), ()),
    ("valuation", "Valuation", "Building", "Building", "bldg", ("CommercialPropertyStructure", "ValuationType"), ()),
    ("bceg", "BCEG grade", "Building", "Building", "bldg", ("CommercialPropertyStructure", "BCEG"), ()),
    ("bldg_limit", "Building limit", "Building", "Building", "bldg", None, ("100000", "500000", "2000000", "10000000")),
    ("protect_class", "Protection class", "Location", "Building", "loc", None, tuple(str(i) for i in range(1, 11))),
    ("group1_territory", "Group I territory", "Location", "Building", "loc", ("CommercialPropertyLocation", "BasicGroupIRatingTerr"), ()),
    ("occupancy", "Occupancy category", "Occupancy", "BPP", "occ", ("CommercialPropertyOccupClass", "OccupCategory"), ()),
    ("class_code", "Class code (by category)", "Occupancy", "BPP", "occ", None, ()),
    ("bpp_coinsurance", "Personal property coinsurance", "Personal property", "BPP", "bpp",
     ("CommercialPropertyPersonalProperty", "Coinsurance"), ()),
    ("bpp_limit", "Personal property limit", "Personal property", "BPP", "bpp", None, ("50000", "150000", "1000000")),
    ("bi_coinsurance", "Business income coinsurance", "Business income", "Business income", "bi",
     ("CommercialPropertyBusinessIncome", "Coinsurance"), ()),
    ("bi_type_of_risk", "Business income type of risk", "Business income", "Business income", "bi",
     ("CommercialPropertyBusinessIncome", "TypeOfRisk"), ()),
    ("bi_limit", "Business income limit", "Business income", "Business income", "bi", None, ("50000", "200000", "1000000")),
    ("effective_date", "Effective date", "Timing", "", "policy", None, ()),
)
CP_BY_ID = {d[0]: d for d in CP_DIMS}
#: Dimensions whose legal values belong to one state: a plan takes each state's own edges for them.
STATE_SPECIFIC = frozenset({"group1_territory"})
_NOT = {"Not Applicable", "None", ""}       # placeholder values a plan does not vary to


def _asof(date: str | None) -> str:
    return (date or CP_EFFECTIVE).replace("-", "")


@lru_cache(maxsize=64)
def _cp_schema(state: str, asof: str):
    from cf_engine.resolve import book_for
    from gl_engine.schema import Schema
    b = book_for(state, asof)
    return b, Schema.for_book(b)


@lru_cache(maxsize=1)
def _cp_resolver():
    from cf_engine.resolve.resolver import CFEditionResolver
    return CFEditionResolver()


def cp_dates(state: str) -> tuple:
    """The state's own CP package dates (its rulebook's edition history), as YYYY-MM-DD."""
    pkgs = _cp_resolver().by_juris.get(state, [])
    return tuple(sorted({f"{p.identity.edition[:4]}-{p.identity.edition[4:6]}-{p.identity.edition[6:]}" for p in pkgs
                         if p.identity.edition >= "20230801"}))


def cp_class_codes(state: str, category: str | None = None, asof: str | None = None) -> tuple:
    b, _ = _cp_schema(state, _asof(asof))
    t = b.table("OccupCategoryRiskSeverity")
    h = list(t.header)
    si, ci, ki = h.index("StateCode"), h.index("OccupCategory"), h.index("ClassCode")
    # Only classes the state rates by class: a code with no Group I rate here refuses (C28-03), at ISO as in ours,
    # so offering it would only manufacture refusals (50 of 154 in OH, e.g. 0300).
    g1 = b.table("BasicGroupIRate")
    gh = list(g1.header)
    rated = {str(r[gh.index("ClassCode")]) for r in g1.rows if r[gh.index("StateCode")] in (state, "CW")}
    return tuple(dict.fromkeys(str(r[ki]) for r in t.rows if r[si] in (state, "CW") and (not category or r[ci] == category)
                               and str(r[ki]) in rated))


def cp_values(dim: str, state: str, config: dict | None = None, asof: str | None = None) -> tuple:
    d = CP_BY_ID[dim]
    if dim == "effective_date":
        return cp_dates(state)
    if dim == "class_code":
        return cp_class_codes(state, (config or {}).get("occupancy"), asof)
    if d[6]:
        return d[6]
    _, s = _cp_schema(state, _asof(asof))
    # Blanket values need a blanket set up (a different risk); a plan varies within a single-location policy.
    return tuple(v for v in s.legal_values(*d[5]) if v not in _NOT and "Blanket" not in v)


def edges(values) -> tuple:
    vs = list(values)
    return tuple(dict.fromkeys([vs[0], vs[-1]])) if vs else ()


#: GL class codes a plan starts from (the user's choice, 2026-10-07): a mix of ten across manufacturing, apartments,
#: lessor's risk, retail and construction, each legal in all 51 GL jurisdictions and rating in each state checked.
GL_CLASS_MIX = (("56911", "Manufacturing"), ("53733", "Manufacturing"), ("60010", "Apartments"),
                ("60011", "Apartments"), ("61212", "Lessor's risk"), ("61217", "Lessor's risk"), ("18501", "Retail"),
                ("11127", "Retail"), ("91340", "Construction"), ("98482", "Construction"))


def dimensions(line: str, state: str, config: dict | None = None, asof: str | None = None) -> list:
    """Every dimension of the line in one state, with its legal values (given the answers in `config`) and edges."""
    config = config or {}
    if line == "GL":
        import variants as V
        d = V.Declared(state, str(config.get("effective_date") or asof or V.DEFAULT_ASOF))
        out = []
        for cid in V.ORDER:
            c = V.BY_ID[cid]
            try:
                vals = tuple(str(v) for v in c.options(d, config))
            except Exception:                                 # noqa: BLE001 -- a control this state cannot offer
                vals = ()
            dim = {"id": cid, "label": c.label, "group": c.group, "kind": c.kind, "values": list(vals),
                   "edges": list(edges(vals)), "keyedBy": list(c.keyed_by) + (["premium_basis"] if cid == "class_code" else []),
                   "exercises": c.exercises}
            if cid == "class_code":
                mix = [code for code, _ in GL_CLASS_MIX if code in set(vals)]
                labels = {}
                for code, grp in GL_CLASS_MIX:
                    if code in mix:
                        try:
                            labels[code] = f"{code} {d.description(code)} ({grp})"
                        except Exception:                     # noqa: BLE001 -- no declared description here
                            labels[code] = f"{code} ({grp})"
                dim.update(suggested=mix, labels=labels)
            out.append(dim)
        return out
    out = []
    for d in CP_DIMS:
        try:
            vals = cp_values(d[0], state, config, asof)
        except Exception:                                     # noqa: BLE001
            vals = ()
        out.append({"id": d[0], "label": d[1], "group": d[2], "coverage": d[3], "kind": "select", "values": list(vals),
                    "edges": list(edges(vals)), "keyedBy": ["occupancy"] if d[0] == "class_code" else [],
                    "perState": d[0] in STATE_SPECIFIC})
    return out


# ---- CP: a config applied to the state's sample risk ---------------------------------------------------------------

def _records(cp: dict):
    for loc in cp.get("CommercialPropertyLocation", []) or []:
        for st in loc.get("CommercialPropertyStructure", []) or []:
            yield "loc", loc
            yield "bldg", st
            for occ in st.get("CommercialPropertyOccupClass", []) or []:
                yield "occ", occ
                for pp in occ.get("CommercialPropertyPersonalProperty", []) or []:
                    yield "bpp", pp
            for bi in st.get("CommercialPropertyBusinessIncome", []) or []:
                yield "bi", bi


_FIELD = {"cause_of_loss": "CauseOfLoss", "construction": "ConstructionType", "stories": "NumStories",
          "bldg_coinsurance": "Coinsurance", "bldg_deductible": "Deductible", "wind_hail_deductible": "WindstormOrHailDeductible",
          "sprinkler": "SprinklerSystem", "valuation": "ValuationType", "bceg": "BCEG", "protect_class": "ProtectClass",
          "group1_territory": "BasicGroupIRatingTerr", "occupancy": "OccupCategory", "bpp_coinsurance": "Coinsurance",
          "bi_coinsurance": "Coinsurance", "bi_type_of_risk": "TypeOfRisk"}


def cp_build(state: str, config: dict | None = None) -> dict:
    """The state's sample risk (`property_rating.sample`) with a CP config applied. Limits move their full values
    with them (a limit above the full value would be a different risk); a class code is set on the structure and its
    occupancy class alike."""
    import property_rating as pr
    config = {k: v for k, v in (config or {}).items() if v not in (None, "")}
    q = pr.sample(state, config["effective_date"]) if config.get("effective_date") else pr.sample(state)
    q = copy.deepcopy(q)
    cp = q["body"]["CommercialProperty"][0]
    for kind, rec in _records(cp):
        for dim, v in config.items():
            if dim in ("effective_date", "class_code", "bldg_limit", "bpp_limit", "bi_limit"):
                continue
            where = CP_BY_ID[dim][4]
            if where == kind or (where == "all" and kind in ("bldg", "bpp", "bi")):
                rec[_FIELD[dim]] = v
        if kind == "bldg":
            if "class_code" in config:
                rec["ClassCode"] = config["class_code"]
            if "bldg_limit" in config:
                rec["Limit"] = rec["FullBldgValue"] = int(config["bldg_limit"])
        if kind == "occ" and "class_code" in config:
            rec["ClassCode"] = config["class_code"]
        if kind == "bpp" and "bpp_limit" in config:
            rec["Limit"] = rec["FullPrsnlPropValue"] = int(config["bpp_limit"])
        if kind == "bi" and "bi_limit" in config:
            rec["Limit"] = int(config["bi_limit"])
    return q


def build(line: str, state: str, config: dict | None = None) -> dict:
    """The request for one plan scenario."""
    if line == "CP":
        return cp_build(state, config)
    import variants as V
    cfg = V.clean(config or {})
    d = V.Declared(state, str(cfg.get("effective_date") or V.DEFAULT_ASOF), cfg.get("package_version") or None)
    if any(isinstance(v, str) and v.startswith("@") for v in cfg.values()):
        import layers                                     # `/tests`' positions (@lowest...), resolved per state
        cfg = layers.resolve(cfg, d)
    return V.build(cfg, d)
