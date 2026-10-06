"""Which rating paths one rating walked (TC-10), read from the engine's own output, never from the request alone.

The path ids are `console/config/paths.json`'s. A path is walked when the rating actually priced through it: a form
with a non-zero premium, a lookup the trace shows, a field the rules wrote. A request that attaches something the
rules never reach walks nothing for it (D15's INERT idea, at path level).

  * **CP** (`cp_signature(data)`): the rated data tree (`cmp.rate`'s first return), by the records and forms that
    priced and the inputs the rules read.
  * **GL** (`gl_signature(rating)`): `gl_engine.rating.Rating.trace` -- its `write` (`Field = value`) and `lookup`
    entries (`table`, `keys`, `value`), per TC-05's signatures.
"""
from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation


def _num(v) -> Decimal:
    try:
        return Decimal(str(v))
    except (InvalidOperation, ValueError):
        return Decimal(0)


# ------------------------------------------------------------------------------------------------------------- CP

#: record tag fragment (as in the data tree) -> (path prefix)
_CP_RECORDS = (("CommercialPropertyStructureBuilding", "cp.bldg"),
               ("CommercialPropertyPersonalPropertyPrsnlProp", "cp.bpp"),
               ("CommercialPropertyBusinessIncome", "cp.bi"))


def _walk(node, path=()):
    yield node, path
    for c in node.children:
        yield from _walk(c, path + (node.tag,))


def _premium(node) -> Decimal:
    p = node.first("Premium")
    return _num(p.text) if p is not None and p.text not in (None, "") else Decimal(0)


def _text(node, field: str) -> str:
    f = node.first(field)
    return "" if f is None or f.text is None else str(f.text)


def cp_signature(data) -> set:
    """The CP paths a rated data tree walked."""
    walked = set()
    for node, _ in _walk(data):
        tag = node.tag
        for rec, prefix in _CP_RECORDS:
            if not tag.startswith(rec) or not tag.endswith("Coverage"):
                continue
            if _premium(node) <= 0:
                continue
            form = tag[len(rec):]
            if form == "BasicGroupICoverage":
                walked.add(prefix + ".g1")
                walked.add("cp.col.basic")
            elif form == "BasicGroupIICoverage":
                walked.add(prefix + ".g2")
                walked.add("cp.col.basic")
            elif form == "SpecialCoverage":
                walked.add("cp.col.special")
            elif form == "BroadCoverage":
                walked.add("cp.col.broad")
        if tag == "CommercialPropertyStructure":
            priced = any(_premium(c) > 0 for c, _ in _walk(node) if c.tag.endswith("Coverage"))
            if not priced:
                continue
            if _text(node, "RatingType") in ("Specific", "Tentative"):
                walked.add("cp.bldg.specific" if _text(node, "CovType") in ("", "Building") else "cp.bpp.specific")
            if _text(node, "BCEG") and _num(_text(node, "BCEGFactor")) not in (0, 1):
                walked.add("cp.bldg.bceg")
            if _text(node, "WindstormOrHailDeductible").strip().endswith("%"):
                walked.add("cp.whded.pct")
        # coinsurance sits on the record itself (Structure / PersonalProperty carry a factor; BI carries none)
        coins = {"CommercialPropertyStructure": "cp.bldg.coins", "CommercialPropertyPersonalProperty": "cp.bpp.coins",
                 "CommercialPropertyBusinessIncome": "cp.bi.coins"}.get(tag)
        if coins and _text(node, "Coinsurance") and (tag == "CommercialPropertyBusinessIncome"
                                                     or _num(_text(node, "CoinsuranceFactor")) > 0) \
                and any(_premium(c) > 0 for c, _ in _walk(node) if c.tag.endswith("Coverage")):
            walked.add(coins)
        if "ExtraExpense" in tag and _premium(node) > 0:
            walked.add("cp.ee")
    return walked


# ------------------------------------------------------------------------------------------------------------- GL

_WRITE = re.compile(r"^(\w+) = (.*)$")
_BASIS = {"Payroll": "payroll", "Area": "area", "Gross Sales": "sales", "Units": "units"}


def gl_signature(rating) -> set:
    """The GL paths a `Rating` walked, from its trace."""
    walked = set()
    writes, lookups = {}, []
    for t in rating.trace:
        if t.kind == "write":
            m = _WRITE.match(t.detail)
            if m:
                writes.setdefault(m.group(1), []).append(m.group(2).strip("'\""))
        elif t.kind == "lookup":
            lookups.append(t.data)
    tables = {d.get("table", "") for d in lookups}
    value_of = {}
    for d in lookups:
        value_of.setdefault(d.get("table", ""), []).append(str(d.get("value", "")))

    for b in writes.get("PremiumBasis", []):
        walked.add("gl.po.basis." + _BASIS.get(b, "other"))
    if any(t.startswith("PremOpsELPText") for t in tables):
        for v in value_of.get("PremOpsELPText", []):
            walked.add("gl.po.elp.industry" if v == "Industry" else "gl.po.elp.company" if v == "Company" else "")
    if any(t.startswith("ProdsCompldOpsELPText") for t in tables):
        for v in value_of.get("ProdsCompldOpsELPText", []):
            walked.add("gl.pco.elp.industry" if v == "Industry" else "gl.pco.elp.company" if v == "Company" else "")
    if "ILFPremOps" in tables:
        walked.add("gl.po.ilf.direct")
    if "ILFProds" in tables:
        walked.add("gl.pco.ilf.direct")
    if any(v.endswith((" BI", " PD")) for v in writes.get("EachOccurrenceLimit", [])):
        walked.add("gl.po.ilf.split")
    if "Yes" in writes.get("SizeOfRiskRatingApplies", []) or any(t.startswith("PremOpsSizeOfRisk") and t != "PremOpsSizeOfRiskRelativityTableAssignment"
                                                                 for t in tables if value_of.get(t, ["0"])[0] not in ("", "0")):
        walked.add("gl.po.sor")
    if "PremOpsLCM" in tables or "ProdsCompldOpsLCM" in tables:
        walked.add("gl.po.lcm.filed")
    elif writes.get("LCM"):
        walked.add("gl.po.lcm.company")
    if "PremOpsMinPremium" in tables:
        walked.add("gl.po.minprem")
    if "ProdsCompldOpsMinPremium" in tables:
        walked.add("gl.pco.minprem")
    pco_basis = writes.get("ProdsCompldOpsPremiumBasis", [])
    for b in pco_basis:
        if b in ("Gross Sales", "Payroll"):
            walked.add("gl.pco.basis." + ("sales" if b == "Gross Sales" else "payroll"))
    if any("Included" in v for v in writes.get("ProdsCompldOpsCov", []) + writes.get("OtherThanProdsCompldOpsCov", [])):
        walked.add("gl.pco.included")
    for t in tables:
        m = re.match(r"DedFactor(PremOps|Prods)(BI|PD|CSL)$", t)
        if m:
            cov = "po" if m.group(1) == "PremOps" else "pco"
            part = {"BI": "bi", "PD": "pd", "CSL": "bipd"}[m.group(2)]
            for d in lookups:
                if d.get("table") == t:
                    keys = str(d.get("keys", ""))
                    if "Per Claim" in keys or "Per Occurrence" in keys:
                        basis = "claim" if "Per Claim" in keys else "occ"
                        # walked only when a deductible was chosen, not when the lookup ran on the default (TC-05)
                        if writes.get(f"{m.group(1)}{m.group(2) if m.group(2) != 'CSL' else 'BIPD'}Deductible", ["No Deductible"])[0] \
                                not in ("", "No Deductible") or (d.get("value") not in ("0", "0.0", "")):
                            walked.add(f"gl.ded.{cov}.{part}.{basis}")
    medpay = writes.get("MedPayLimit", []) + writes.get("MedicalPaymentsLimit", [])
    if "MedPayFactor" in tables:
        walked.add("gl.covc.increased")
    elif "IncreasedMedPayLimitFactor" in tables:
        walked.add("gl.covc.increased.2027")
    elif any(v == "Excluded" for v in medpay):
        walked.add("gl.covc.excluded")
    else:
        walked.add("gl.covc.basic")
    if any(writes.get("PersonalAndAdvertisingInjuryExcl", ["No"])[0] == "Yes" for _ in [0]):
        walked.add("gl.covb.excluded")
    else:
        walked.add("gl.covb.included")
    if any(t.startswith("PremOpsClaimsMadeMultiplier") or t.startswith("ClaimsMadeMultiplier") for t in tables):
        walked.add("gl.po.claimsmade")
    # a state exception: a rating rule the STATE package files in place of countrywide's (TC-05: ILF, base rate,
    # territory loss cost, exposure, size of risk, medical payments), not every state-sourced call
    # Only `Set...` rules in the classification rule files count: messages, terrorism and location percentages are
    # state rules too, but not rating overrides (measured against TC-05's census, 2026-10-06).
    state = getattr(rating.book, "juris", "")
    rating_rule = re.compile(r"\.Set\w*(IncrdLimit|ILF|BaseRate|LossCost|Exposure|SizeOfRisk|MedicalPayments)")
    for t in rating.trace:
        if not (t.kind == "call" and t.source and state and f"_{state}_" in str(t.source) and rating_rule.search(t.detail)):
            continue
        if t.detail.startswith("GeneralLiabilityClassificationProdsCompldOpsCoverageRules."):
            walked.add("gl.pco.stateexc")
        elif t.detail.startswith(("GeneralLiabilityClassificationPremOpsCoverageRules.", "GeneralLiabilityClassificationRules.")):
            walked.add("gl.po.stateexc")
    walked.discard("")
    return walked
