"""The `/api/rate` answer, built from a GL `Rating`: what `app.py` returns for one request. **OI-140.**

Moved out of `app.py` unchanged so a caller that rates some other way -- the sister project ISOComputeGraph's compiled
graph, which rates with no `Kernel` (its C-42, C-43) -- returns the same answer without importing `app.py`, which makes
two kernels when it loads. Nothing here rates, and nothing here calls ISO: the comparison with ISO stays in `app.py`
and is passed in (`answer(..., iso=...)`), at the same place in the answer.

* `answer(r, payload, rounding, resolver, with_technical, iso)` -- the whole answer, keys in `app.py`'s order
* `_subline_premiums`, `_chain`, `_rating`, `_factors` -- its parts, as `app.py` had them
"""
from __future__ import annotations

from decimal import Decimal

from gl_engine.interp import tree
from gl_engine.resolve import ResolvedBook
from gl_engine.schema import Schema, validate


#: Trace kinds that are a rating FACTOR -- a number that entered the premium
#: and can be pointed at. The rest of the trace is control flow.
FACTOR_KINDS = ("lookup", "lookup-banded", "lookup-interpolated", "round")


def _subline_premiums(rating) -> list:
    """Premium per subline, from the stat code ISO writes on each coverage.

    `Subline` is `334` for premises/operations and `336` for products, and it
    is written by `ErcSetStatisticalCodes` -- which was silently skipped until
    the `ancestor::` axis was implemented, because asking this very question is
    what exposed it.
    """
    out: dict[str, dict] = {}
    for risk in tree.select("GeneralLiabilityTable/GeneralLiability",
                            rating.tree):
        for loc in tree.select("GeneralLiabilityLocationTable/"
                               "GeneralLiabilityLocation", risk):
            for cls in tree.select("GeneralLiabilityClassificationTable/"
                                   "GeneralLiabilityClassification", loc):
                for cov in cls.children:
                    if not cov.children:
                        continue
                    sub = tree.read("Subline", cov)
                    prem = tree.read("Premium", cov)
                    if not sub or prem in (None, "", "0"):
                        continue
                    e = out.setdefault(sub, {"subline": sub, "premium": Decimal(0),
                                             "coverages": []})
                    e["premium"] += Decimal(prem)
                    e["coverages"].append({"coverage": cov.tag,
                                           "premium": str(Decimal(prem))})
    return [{**v, "premium": str(v["premium"])}
            for v in sorted(out.values(), key=lambda x: x["subline"])]


#: Written onto a coverage but not part of the price -- statistical reporting
#: codes and the subline they belong to.
def _is_stat(tag: str) -> bool:
    return tag.endswith("StatCode") or tag == "Subline"


#: The named milestones in a coverage's chain, so the eye can follow it.
MILESTONES = ("BaseRate", "FinalILF", "FinalRate", "BasicLimitPremium",
              "MedicalPaymentsCharge", "MinPremium", "Premium")


def _chain(cov) -> dict:
    """One coverage's rating chain, in the order the engine computed it.

    **Tree order is computation order** -- a node is appended when a rule
    writes it -- so the chain reads as the narrative it actually was:
    loss cost, LCM, base rate, ILF, deductible, size of risk, basic limit
    premium, final rate, premium.

    Zero-valued steps are omitted from `factors` and **named in `omitted`**
    rather than dropped silently. That distinction matters here more than
    most places: this corpus has eight meanings of zero, and a zero where a
    rate belonged is the defect this whole engine exists to refuse. A
    simplified view may not be the thing that hides one.
    """
    factors, omitted = [], []
    for ch in cov.children:
        if ch.children or _is_stat(ch.tag) or ch.text in (None, ""):
            continue
        try:
            v = Decimal(ch.text)
        except Exception:                                   # noqa: BLE001
            continue
        if v == 0:
            omitted.append(ch.tag)
            continue
        factors.append({"factor": ch.tag, "value": str(v),
                        **({"milestone": True} if ch.tag in MILESTONES else {})})
    prem = tree.read("Premium", cov)
    return {"coverage": cov.tag, "premium": prem,
            "subline": tree.read("Subline", cov),
            "factors": factors,
            "omitted_zero": omitted}


def _rating(rating) -> dict:
    """The simplified view: what actually rated, and what it came to."""
    covs = []
    for risk in tree.select("GeneralLiabilityTable/GeneralLiability",
                            rating.tree):
        for loc in tree.select("GeneralLiabilityLocationTable/"
                               "GeneralLiabilityLocation", risk):
            for cls in tree.select("GeneralLiabilityClassificationTable/"
                                   "GeneralLiabilityClassification", loc):
                for cov in cls.children:
                    if not cov.children:
                        continue
                    prem = tree.read("Premium", cov)
                    if prem in (None, "", "0"):
                        continue
                    c = _chain(cov)
                    c["class_code"] = tree.read("ClassCode", cls)
                    covs.append(c)
    return {"coverages": covs, "premium": str(rating.premium)}


def _factors(rating) -> list:
    """Every rating factor, in the order it was used, as structured data.

    The trace carries `data` for exactly this: a factor is a table, a set of
    keys, a value and the package it came from, and squeezing that into a
    sentence made it unreadable on a screen. `detail` is kept as a one-line
    summary; the parts are what the JSON panel renders.
    """
    out = []
    for i, t in enumerate(rating.trace):
        if t.kind not in FACTOR_KINDS:
            continue
        out.append({"step": len(out) + 1, "kind": t.kind, **t.data,
                    "summary": t.detail})
    return out


def answer(r, payload: dict, rounding: str, resolver, with_technical: bool = False, iso=None) -> dict:
    """The answer for a rating `r` of `payload`: `app.rate`'s, from the rating on. `iso(r)`, when given, is the
    comparison with ISO (`app.py`'s), placed where `app.rate` placed it."""
    result = {
        "jurisdiction": r.juris, "asof": r.asof, "mode": r.mode,
        "packages": list(r.packages), "complete": r.complete,
        "rounding": rounding,
    }
    if not r.complete:
        result["stopped"] = str(r.stopped)
        result["trace_len"] = len(r.trace)
        return result

    try:
        book = ResolvedBook(resolver.resolve(r.juris, r.asof))
        findings = validate(payload, Schema.for_book(book))
    except Exception as exc:                                # noqa: BLE001
        findings = []
        result["schema_error"] = str(exc)

    if r.deviation is not None:
        result["deviation"] = r.deviation
        # the two payloads (D21): the non-deviated one is what ISO is sent and what technical rates; the deviated
        # one, naming the company, is rated by our engine only, as carrier
        from deviations.engine import iso_request
        result["payloads"] = {"nonDeviated": iso_request(payload, "GL")[0], "deviated": payload}
        if with_technical and r.technical is not None:
            result["technical"] = {"premium": str(r.technical.premium) if r.technical.complete else None,
                                   "complete": r.technical.complete, "packages": list(r.technical.packages),
                                   "by_coverage": [{"coverage": k, "premium": str(v)}
                                                   for k, v in sorted(r.technical.by_coverage.items())]}
    if iso is not None:
        result["iso"] = iso(r)

    result.update({
        "premium": str(r.premium),
        "by_coverage": [{"coverage": k, "premium": str(v)}
                        for k, v in sorted(r.by_coverage.items(),
                                           key=lambda x: -x[1])],
        "by_subline": _subline_premiums(r),
        "rating": _rating(r),
        "factors": _factors(r),
        "factor_count": len(_factors(r)),
        "referrals": [{"code": x.code, "condition": x.condition,
                       "clears_with": x.needs or "", "where": x.where}
                      for x in r.referrals],
        "messages": r.messages,
        "notices": r.notices,
        "findings": [{"level": f.level, "code": f.code, "where": f.where,
                      "detail": f.detail} for f in findings],
        "trace_len": len(r.trace),
    })
    return result
