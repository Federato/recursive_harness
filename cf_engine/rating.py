"""Rate one Commercial Property request: ISO-only, or for a writing company (DEVIATIONS-PLAN.md P2).

    from cf_engine.rating import rate
    r = rate(request)                          # ISO-only: today's engine, unchanged
    r = rate(request, with_technical=True)     # header.WritingCompany -> carrier + technical

**Without a company** this is exactly the console's Property rating (`scripts/cf/154_...rate`): the same
request conversion, the same book, the same interpreter settings. None of the company layer is imported (I4),
and `tests/verify_deviations_engine.py` holds the two identical over the stored population (T1).

**With a company** (`header.WritingCompany`, or `company=`) the request is rated twice from one call:

  * **technical** -- pure ISO content on the same edition the carrier rates on (M3), with every submitted
    LCM removed (D13) and our header fields gone (M6). This is the request ISO's service checks.
  * **carrier** -- the same, through `deviations.engine.CompanyBook`: the company's LCMs on the records, its
    group LCMs in each group's rate (D17), its table overrides in front of ISO's tables.

The carrier tree stays ISO-shaped; what the company did is reported beside it in `deviation` (§3c): the filing
used, both premiums, the waterfall, every changed field and every warning. A request the company layer cannot
honour is refused with the reason, never quietly rated as technical.

The request conversion helpers still live in `scripts/cf` (`125_`, `145_`), as the console's do; moving them into
`cf_engine` is a refactor of its own and deliberately not bundled here.
"""
from __future__ import annotations

import copy
import sys
from dataclasses import dataclass, field
from datetime import date
from importlib import import_module
from pathlib import Path

from gl_engine.interp.interpreter import Interpreter
from gl_engine.interp.tree import Node
from gl_engine.interp.values import InterpretError

from .config import NULL_ARITHMETIC, ROUNDING
from .resolve import book_for

_CF_SCRIPTS = Path(__file__).resolve().parent.parent / "scripts" / "cf"
_rp = None


def _helpers():
    global _rp
    if _rp is None:
        if str(_CF_SCRIPTS) not in sys.path:
            sys.path.append(str(_CF_SCRIPTS))
        _rp = import_module("145_chunk13_c13-03_replay")
    return _rp


#: Header fields we own (§3b). They never reach ISO's rules or ISO's service (M6).
OWN_HEADER = ("WritingCompany", "PolicyType")


@dataclass
class PropertyRating:
    juris: str
    asof: str
    packages: list
    tree: Node | None = None
    ip: Interpreter | None = None
    premium: str | None = None
    outcome: dict = field(default_factory=dict)
    deviation: dict | None = None
    technical: "PropertyRating | None" = None

    @property
    def complete(self) -> bool:
        return self.outcome.get("status") != "refused" and self.tree is not None


def _scheme(request: dict) -> tuple[str, str]:
    sk = request["body"]["SchemeKeys"]
    return sk["ProductName"].split()[-1], sk["EffectiveDateTime"][:10]


def _run(request: dict, book, trace: bool = True) -> PropertyRating:
    """One rating on one book, the console's way (154_'s `rate`), with a refusal kept as the outcome."""
    rp = _helpers()
    st, eff = _scheme(request)
    d = date.fromisoformat(eff)
    sub = {"EffDate": d.strftime("%m/%d/%Y"), "ExpDate": d.replace(year=d.year + 1).strftime("%m/%d/%Y")}
    sub.update(rp.unwrap(rp.to_engine({"CommercialProperty": request["body"]["CommercialProperty"]}),
                         rp.singletons(book)))
    res = book.resolution
    out = PropertyRating(st, eff, [res.state.pkg_id] + ([res.parent.pkg_id] if res.parent else []))
    ip = Interpreter(book, rounding=ROUNDING, null_arithmetic=NULL_ARITHMETIC, trace=trace)
    data = Node.from_dict(f"MasterCF{st}", sub)
    out.ip = ip
    try:
        ip.run(data)
    except InterpretError as exc:
        out.outcome = ip.outcome if ip.outcome.get("status") == "refused" else {
            "status": "refused", "reasons": [{"kind": getattr(exc, "outcome_kind", "refused"),
                                              "detail": str(exc)[:300]}]}
        return out
    out.tree, out.outcome = data, ip.outcome
    out.premium = _total(data)
    return out


def _total(data: Node) -> str | None:
    for t in data.children:
        if t.tag == "CommercialPropertyTable" and t.children:
            c = t.children[0].first("ErcCalculatedTotalPremium")
            return c.text if c is not None else None
    return None


def rate(request: dict, company: str | None = None, *, with_technical: bool = False,
         waterfall: bool = True, trace: bool = True, root: Path | None = None,
         track: bool = False) -> PropertyRating:
    """Rate a Property request; with a writing company, the carrier result with `deviation` set."""
    header = dict(request.get("header") or {})
    wc = company or header.get("WritingCompany")
    if not wc and not any(k in header for k in OWN_HEADER):
        st, eff = _scheme(request)
        return _run(request, book_for(st, eff.replace("-", "")), trace)

    clean = copy.deepcopy(request)
    for k in OWN_HEADER:
        clean.setdefault("header", {}).pop(k, None)
    if not wc:                       # PolicyType alone: our field, removed; rated as ISO-only
        st, eff = _scheme(clean)
        return _run(clean, book_for(st, eff.replace("-", "")), trace)

    from deviations import engine as dv
    st, eff = _scheme(clean)
    lcm_warnings: list = []
    # the block is a list of policies, or ONE object (ISO accepts both; stored requests use both)
    dv.strip_lcms(clean["body"]["CommercialProperty"], lcm_warnings, "CommercialProperty")
    try:
        plan = dv.plan_for("CF", wc, st, eff, header.get("PolicyType"),
                           **({"root": root} if root else {}))
        book = dv.book_for(plan)
    except dv.Refused as exc:
        r = PropertyRating(st, eff, [])
        r.outcome = {"status": "refused", "reasons": [{"kind": exc.outcome_kind, "detail": str(exc)}]}
        r.deviation = {"writingCompany": wc, "refused": str(exc)}
        return r
    plan.track = track
    if company and header.get("WritingCompany") and header["WritingCompany"] != company:
        plan.warn(f"company={company} given; header.WritingCompany {header['WritingCompany']} not used")
    for w in lcm_warnings:
        plan.warn(w)
    if plan.manifest and plan.manifest["iso_edition"]["new"]["state"] != book.state.pkg_id:
        plan.warn(f"ISO revised since {plan.ref} compiled: compiled on "
                  f"{plan.manifest['iso_edition']['new']['state']}, rating on {book.state.pkg_id}; "
                  f"replace rows keep their value, multiply rows follow ISO (D9)")

    technical = _run(clean, book, trace)
    try:
        cbook = dv.CompanyBook(book, plan)
    except dv.Refused as exc:
        r = PropertyRating(st, eff, technical.packages)
        r.outcome = {"status": "refused", "reasons": [{"kind": exc.outcome_kind, "detail": str(exc)}]}
        r.deviation = {"writingCompany": wc, "refused": str(exc), "warnings": plan.warnings}
        r.technical = technical if with_technical else None
        return r
    carrier = _run(clean, cbook, trace)
    carrier.deviation = _deviation(plan, book, technical, carrier, clean, trace, waterfall)
    if with_technical:
        carrier.technical = technical
    return carrier


# ------------------------------------------------------------------ the Deviation block

def _deviation(plan, book, technical, carrier, clean, trace, waterfall) -> dict:
    from deviations import engine as dv, report
    current = None
    if waterfall and plan.pin:
        current = _run(clean, dv.iso.book("CF", plan.juris, plan.date), trace=False).premium
    dev = report.build(plan, book.state.pkg_id, technical.premium, carrier.premium,
                       technical.tree, carrier.tree,
                       lambda p: _run(clean, dv.CompanyBook(book, p), trace=False).premium,
                       current, waterfall)
    if technical.outcome.get("status") == "refused":
        dev["warnings"].append("technical was refused: " + "; ".join(
            r.get("detail", "") for r in technical.outcome.get("reasons", [])))
    return dev
