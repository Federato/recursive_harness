"""A state's own Group II inputs for a test policy moved out of Oregon (chunk 28 C28-17).

Oregon's territories exist nowhere else, so the portable test policies used to drop them, and ISO priced the building's
Group II at $0 for want of a territory. Since C28-17 that refuses (the user's decision: a missing input that zeroes an
attached coverage is invalid), and the user directed (2026-10-05) "we need to input the correct territory". This picks
them from the state's own filed tables, as chunk 2's state sweep (`11_chunk2_enumerate_states.inputs_for`) does:

  * the territory: the first Group II territory the state's `BasicGroupIIRate` files, else (Florida, whose rate table is
    header-only) its `BasicGroupIIRatingTerrConverted`, else its `BCEGFactor` (a state with none keeps none);
  * the BCEG grade: the building's own grade if `BCEGFactor` files it for that territory, else the first grade the
    state files for it (BCEGFactor is keyed on the Group II territory and the grade; a pair with no row refuses).
"""
from __future__ import annotations


def _col(t, name):
    return t.header.index(name) if name in t.header else None


def state_territories(book) -> list:
    """The Group II territories this state files, in file order (see `group2_inputs`)."""
    for name in ("BasicGroupIIRate", "BasicGroupIIRatingTerrConverted", "BCEGFactor"):
        if not book.declares(name):
            continue
        t = book.table(name)
        ti = _col(t, "BasicGroupIIRatingTerr")
        if not t.is_empty and ti is not None:
            terrs = list(dict.fromkeys(str(r[ti]) for r in t.rows if r[ti] not in (None, "")))
            if terrs:
                return terrs
    return []


def group2_symbol(book, construction: str | None, stories: str | None) -> str | None:
    """The Group II construction symbol for a building, from the state's (else countrywide's) table, as chunk 2 does."""
    if not book.declares("BasicGroupIIConstructionSymbol") or not construction:
        return None
    t = book.table("BasicGroupIIConstructionSymbol")
    c = _col(t, "ConstructionType") if _col(t, "ConstructionType") is not None else _col(t, "ConstructionTypeBldg")
    n = _col(t, "NumStories") if _col(t, "NumStories") is not None else _col(t, "NumOfStoriesInBldg")
    y = _col(t, "Symbol")
    if t.is_empty or None in (c, y):
        return None
    for r in t.rows:
        if str(r[c]) == construction and (n is None or stories in (None, "") or str(r[n]) == str(stories)):
            return str(r[y])
    return None


def group2_inputs(book, grade: str | None = None) -> dict:
    """{"BasicGroupIIRatingTerr": …, "BCEG": …} for this book's state, or {} where the state files no territory."""
    # the territories the state files: its Group II rate table, else (FL) its territory-conversion table, else the
    # territories its BCEG table is keyed on
    terrs = []
    for name in ("BasicGroupIIRate", "BasicGroupIIRatingTerrConverted", "BCEGFactor"):
        if not book.declares(name):
            continue
        t = book.table(name)
        ti = _col(t, "BasicGroupIIRatingTerr")
        if not t.is_empty and ti is not None:
            terrs = list(dict.fromkeys(str(r[ti]) for r in t.rows if r[ti] not in (None, "")))
        if terrs:
            break
    if not terrs:
        return {}
    out = {"BasicGroupIIRatingTerr": terrs[0]}
    if not book.declares("BCEGFactor"):
        return out
    bceg = book.table("BCEGFactor")
    bt, bg = _col(bceg, "BasicGroupIIRatingTerr"), _col(bceg, "BldgCodeEffectivenessGrade2")
    if bceg.is_empty or bt is None or bg is None:
        return out
    for terr in terrs:
        grades = [str(r[bg]) for r in bceg.rows if str(r[bt]) == terr]
        if grades:
            out["BasicGroupIIRatingTerr"] = terr
            out["BCEG"] = grade if grade in grades else grades[0]
            return out
    return out


def localize_group2(sub: dict, juris: str, asof: str = "20260917", replace: bool = True) -> dict:
    """Give every location of `sub` without a Group II territory the state's own, and its buildings a BCEG grade the
    state files for that territory (the building's own grade kept where it is filed); a building with a territory but
    no BCEG gets a grade filed for its territory. Returns `sub`."""
    from cf_engine.resolve import book_for
    book = book_for(juris, asof)
    for cp in sub["CommercialPropertyTable"]["CommercialProperty"]:
        for loc in cp.get("CommercialPropertyLocationTable", {}).get("CommercialPropertyLocation", []):
            structs = loc.get("CommercialPropertyStructureTable", {}).get("CommercialPropertyStructure", [])
            filed = state_territories(book)
            if replace and filed and loc.get("BasicGroupIIRatingTerr") not in (None, "")                     and str(loc["BasicGroupIIRatingTerr"]) not in filed:
                loc.pop("BasicGroupIIRatingTerr")       # another state's territory (Oregon's "Entire State" in FL): not this one's
            for st in structs:
                # the rule that writes the Group II symbol keys it on ConstructionType AND NumStories, and writes ""
                # without both (CW SetBasicGroupIISymbol); a building with no stories then refuses in NY, at ISO too
                # (C28-17 probe). "1-3", the stories chunk 2's state sweep sends.
                if st.get("ConstructionType") not in (None, "") and st.get("NumStories") in (None, ""):
                    st["NumStories"] = "1-3"
                if st.get("BasicGroupIISymbol") in (None, ""):
                    sym = group2_symbol(book, st.get("ConstructionType"), st.get("NumStories"))
                    if sym:
                        st["BasicGroupIISymbol"] = sym
            has_terr = loc.get("BasicGroupIIRatingTerr") not in (None, "")
            if has_terr and all(st.get("BCEG") not in (None, "") for st in structs):
                continue
            gi = group2_inputs(book, next((st.get("BCEG") for st in structs if st.get("BCEG")), None))
            if not has_terr:
                if "BasicGroupIIRatingTerr" not in gi:
                    continue
                loc["BasicGroupIIRatingTerr"] = gi["BasicGroupIIRatingTerr"]
            elif gi.get("BasicGroupIIRatingTerr") != loc["BasicGroupIIRatingTerr"]:
                gi.pop("BCEG", None)              # a grade for another territory would not match this one
            for st in structs:
                if "BCEG" in gi and (not has_terr or st.get("BCEG") in (None, "")):
                    st["BCEG"] = gi["BCEG"]       # a grade this state files for the territory (BCEG blank zeroes Group II)
    return sub


def localize(sub: dict, juris: str, asof: str = "20260917", replace: bool = True) -> dict:
    """The state's own inputs a moved test policy lacks (C28-17): its Group II territory and BCEG (`localize_group2`),
    and Arizona's location `BasicGroupIReductionCredit` (1.0, the value chunk 1's state sweep sends; a number, as
    ISO's request view types it). Idempotent; a value already present is kept. Returns `sub`."""
    localize_group2(sub, juris, asof, replace)  # Oregon too: its Group II territory is "Entire State"
    if juris == "NY":
        # NY prices Group II through its Builders Risk rule, keyed on CompletedBasicGroupIISymbol, on every building
        # unless it is "Not Applicable" (chunk 24; OI-103: blank on an ordinary building refuses, at ISO too)
        for cp in sub["CommercialPropertyTable"]["CommercialProperty"]:
            for loc in cp.get("CommercialPropertyLocationTable", {}).get("CommercialPropertyLocation", []):
                for st in loc.get("CommercialPropertyStructureTable", {}).get("CommercialPropertyStructure", []):
                    if st.get("CompletedBasicGroupIISymbol") in (None, ""):
                        st["CompletedBasicGroupIISymbol"] = "Not Applicable"
    if juris == "AZ":
        for cp in sub["CommercialPropertyTable"]["CommercialProperty"]:
            for loc in cp.get("CommercialPropertyLocationTable", {}).get("CommercialPropertyLocation", []):
                if loc.get("BasicGroupIReductionCredit") in (None, ""):
                    loc["BasicGroupIReductionCredit"] = 1.0
    return sub


def localize_request(req: dict, juris: str, asof: str = "20260917") -> dict:
    """`localize` for an ISO request body (records are plain lists there, no `…Table` wrappers). Returns `req`."""
    body = req.get("body", req)
    wrapped = {"CommercialPropertyTable": {"CommercialProperty": [
        {**cp, "CommercialPropertyLocationTable": {"CommercialPropertyLocation": [
            {**loc, "CommercialPropertyStructureTable": {"CommercialPropertyStructure": loc.get("CommercialPropertyStructure", [])}}
            for loc in cp.get("CommercialPropertyLocation", [])]}}
        for cp in body.get("CommercialProperty", [])]}}
    localize(wrapped, juris, asof)
    for cp, wcp in zip(body.get("CommercialProperty", []), wrapped["CommercialPropertyTable"]["CommercialProperty"]):
        for loc, wloc in zip(cp.get("CommercialPropertyLocation", []),
                             wcp["CommercialPropertyLocationTable"]["CommercialPropertyLocation"]):
            for k in ("BasicGroupIIRatingTerr", "BasicGroupIReductionCredit"):
                # filled where missing, and replaced where the state does not file it (another state's territory)
                if k in wloc and loc.get(k) != wloc[k]:
                    loc[k] = wloc[k]
            # the structures are the same dict objects, so their BCEG is already set
    return req
