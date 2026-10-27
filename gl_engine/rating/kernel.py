"""The rating kernel: a submission goes in, a premium comes out.

Stage 3. Everything below the surface is stages 1 and 2 -- resolve the rulebook,
build the tree, execute ISO's rules -- and this module is the thing a caller
actually holds.

**Two modes, one code path.** `strict-erc` reproduces ISO exactly and is the
mode the Phase 2 RAaS comparison runs in; any difference there is our defect
until proven otherwise. `underwriting` runs the same rules and additionally
enforces the referral register, so a condition ISO prices silently but the
manual says refer becomes a referral rather than a number. **They must never be
two implementations** -- a second code path is a second thing to be wrong, and
the whole point of strict mode is that it is the same engine.

**Dispositions are monotonic (D02).** A referral, once raised, is not cancelled
by anything later in the run. ERC re-evaluates coverages in the 14
`PremiumToReachMinCoverage` groups and California's older parent recomputes 213
DataDefs, so a value genuinely can be produced twice -- and no oracle exists for
whether a second pass should un-raise a referral, because RAaS has no notion of
one. That makes it a design choice, and the conservative direction cannot
produce a wrong price.
"""
from __future__ import annotations

import copy
import json
import os
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

from ..errors import EngineError
from ..interp import Interpreter, Node
from ..interp import tree
from ..resolve import EditionResolver, ResolvedBook
from . import checks, referrals
from .checks import TOTAL, TOTAL_CHECK, RatingError  # noqa: F401  (OI-139: the checks are plain functions)
from .submission import from_raas, load as load_submission

#: The two behavioural modes. One engine, one code path, two policies.
#: OI-134: "on" refuses a submission missing a required rating input; "off" for measuring (57_rating_inputs.py).
RATING_INPUTS_CHECK = os.environ.get("ERC_RATING_INPUTS", "on")

STRICT = "strict-erc"
UNDERWRITING = "underwriting"
MODES = (STRICT, UNDERWRITING)

#: Where the analysis phase left the referral register.
REGISTER = (Path(__file__).resolve().parent.parent.parent
            / "scripts" / "erc" / "out" / "referral_register.json")

#: Header fields we own (DEVIATIONS-PLAN.md §3b): removed before ISO's rules
#: run and before any call to ISO's service (M6).
OWN_HEADER = ("WritingCompany", "PolicyType")

@dataclass
class Referral:
    """A condition ISO will not price, raised against a rating."""

    code: str
    condition: str
    kind: str
    needs: str | None = None          # the input that would clear it (D01)
    where: str = ""

    @property
    def resolvable(self) -> bool:
        return self.needs is not None

    def __str__(self) -> str:          # pragma: no cover - display only
        tail = f"; supply `{self.needs}` to clear" if self.needs else ""
        return f"[{self.code}] {self.condition}{tail}"


@dataclass
class Rating:
    """What a rating produced: the number, the evidence, and the refusals."""

    juris: str
    asof: str
    mode: str
    book: ResolvedBook
    tree: Node
    trace: list
    premium: Decimal | None = None
    #: ISO's own validation messages, raised by its rules through
    #: `MessageHelper`. These are a RAaS response's `RatingMessages`.
    messages: list = field(default_factory=list)
    by_coverage: dict = field(default_factory=dict)
    referrals: list = field(default_factory=list)
    complete: bool = False
    stopped: Exception | None = None
    #: Set only when a writing company rated (DEVIATIONS-PLAN.md §3c): what the
    #: company's filing did, beside the ISO-shaped tree.
    deviation: dict | None = None
    #: The technical rating from the same call, when asked for (`with_technical`).
    technical: "Rating | None" = None
    #: The rating graph, when asked for (`graph=True`: a `RatingGraph`); None otherwise.
    deps: object = None
    #: Our own warnings, on every rating in every mode (OI-130, B-07): coverages ISO's table marks "Not
    #: Applicable" for the class (not offered), and coverages on the policy that priced $0 or $1 silently
    #: (R30; a referral too in underwriting mode). ISO's own messages stay in `messages`.
    notices: list = field(default_factory=list)

    @property
    def packages(self) -> tuple[str, ...]:
        p = (self.book.resolution.state.pkg_id,)
        if self.book.resolution.parent:
            p += (self.book.resolution.parent.pkg_id,)
        return p

    def raise_referral(self, r: Referral) -> None:
        """Monotonic (D02): add, never remove, and never duplicate a code."""
        if any(x.code == r.code for x in self.referrals):
            return
        self.referrals.append(r)

    def __str__(self) -> str:          # pragma: no cover - display only
        head = (f"{self.juris}@{self.asof} [{self.mode}] "
                f"{' over '.join(self.packages)}")
        if not self.complete:
            return f"{head}\n  INCOMPLETE: {self.stopped}"
        lines = [head, f"  premium: {self.premium}"]
        for k, v in sorted(self.by_coverage.items()):
            lines.append(f"    {k:56s} {v}")
        for r in self.referrals:
            lines.append(f"  REFER {r}")
        return "\n".join(lines)


def _load_register() -> list:
    return referrals.load_register()


class Kernel:
    """Rates submissions against one corpus.

    Holds the resolver so the package scan is paid once rather than per
    submission -- discovery is ~0.9s and a batch run would otherwise pay it
    every time.
    """

    def __init__(self, mode: str = STRICT, rounding: str = "ROUND_HALF_UP",
                 resolver: EditionResolver | None = None):
        if mode not in MODES:
            raise RatingError(f"unknown mode {mode!r}; expected one of {MODES}")
        self.mode = mode
        self.rounding = rounding
        self.resolver = resolver or EditionResolver()
        self.register = _load_register()
        self._schemas: dict = {}           # OI-134: one Schema per resolved package pair

    # ------------------------------------------------------------------ rate

    def rate(self, payload: dict | str | Path,
            version: str | None = None, *, company: str | None = None,
            with_technical: bool = False, waterfall: bool = True,
            root: Path | None = None, graph: bool = False) -> Rating:
        """Rate one RAaS-shaped submission.

        `version`, if given, pins the SAME package version the payload was
        built against instead of letting the resolver take the newest again.
        **The payload itself carries no such field** -- ISO's own live
        service has no equivalent input to pin its own version choice -- so
        a caller that built a submission at a pinned version (`variants.py`
        `package_version`) and then rates it here without passing `version`
        silently re-resolves to newest, which is not the same submission it
        looks like: the values were built against one rulebook and priced
        against another. `sweep.run_config` is the one place both are read
        from the same config together.
        """
        if isinstance(payload, (str, Path)):
            data, juris, asof = load_submission(payload)
        else:
            header = payload.get("header") or {}
            if company or any(k in header for k in OWN_HEADER):
                return self._rate_company(payload, version, company, with_technical,
                                          waterfall, root, graph)
            data, juris, asof = from_raas(payload)

        book = ResolvedBook(self.resolver.resolve(juris, asof, version))
        return self._rate_book(data, juris, asof, book, graph)

    def _rate_book(self, data: Node, juris: str, asof: str, book, graph: bool = False) -> Rating:
        """One rating of one tree on one book (ISO's, or a company's in front of it)."""
        interp = Interpreter(book, rounding=self.rounding)
        if graph:
            from ..interp.graph import RatingGraph
            interp.deps = RatingGraph()

        result = Rating(juris=juris, asof=asof, mode=self.mode, book=book,
                        tree=data, trace=interp.trace,
                        messages=interp.messages)
        try:
            self._refuse_missing_rating_inputs(data, book)
        except RatingError as exc:
            result.stopped = exc
            return result
        try:
            interp.run(data)
            result.complete = True
            result.deps = interp.deps
            if hasattr(interp.deps, "finalize"):
                interp.deps.finalize(data)
        except Exception as exc:                     # noqa: BLE001 - reported
            result.stopped = self._ilf_override_needed(data, exc) or exc
            return result

        try:
            self._refuse_null_loss_cost(result)
            self._collect(result)
        except EngineError as exc:
            result.complete = False
            result.stopped = exc
            return result
        checks.add_notices(result)
        if self.mode == UNDERWRITING:
            self._apply_register(result)
        return result

    # ------------------------------------------------ a writing company (P2)

    def _rate_company(self, payload: dict, version, company, with_technical, waterfall,
                      root, graph: bool = False) -> Rating:
        """Technical and carrier from one call (DEVIATIONS-PLAN.md §3, §4).

        Our header fields are removed before anything else (M6); with no
        company named that is all that happens. With one, submitted LCMs are
        removed (D13), technical is rated on the edition the carrier uses (M3),
        and the carrier is rated through the company's book.
        """
        header = payload.get("header") or {}
        wc = company or header.get("WritingCompany")
        clean = copy.deepcopy(payload)
        for k in OWN_HEADER:
            clean.setdefault("header", {}).pop(k, None)
        if not wc:
            return self.rate(clean, version, graph=graph)

        from deviations import engine as dv, report
        lcm_warnings: list = []
        # a list of policies, or one object: strip_lcms walks either
        dv.strip_lcms((clean.get("body") or {}).get("GeneralLiability"), lcm_warnings,
                      "GeneralLiability", key="LCM")
        data, juris, asof = from_raas(clean)
        date = f"{asof[:4]}-{asof[4:6]}-{asof[6:]}"
        iso_book = ResolvedBook(self.resolver.resolve(juris, asof, version))
        try:
            plan = dv.plan_for("GL", wc, juris, date, header.get("PolicyType"),
                               **({"root": root} if root else {}))
            book = iso_book                  # the edition in force: no pins (2026-10-16)
            for w in lcm_warnings:
                plan.warn(w)
            technical = self._rate_book(data, juris, asof, book, graph)
            cbook = dv.CompanyBook(book, plan)
        except dv.Refused as exc:
            out = Rating(juris=juris, asof=asof, mode=self.mode, book=iso_book,
                         tree=data, trace=[], stopped=exc)
            out.deviation = {"writingCompany": wc, "refused": str(exc)}
            return out

        def again(book_, g=False):
            return self._rate_book(from_raas(clean)[0], juris, asof, book_, g)

        def policy(p, r):
            # B-21: the filing's policy minimum on a rated carrier, after the rules (ISO's service never sees it)
            if p.policy and r.complete:
                got = dv.apply_policy(p, "GL", r.tree)
                if got:
                    r.premium = got["premium"]
                    if got["topUp"] is not None:
                        r.by_coverage["PolicyWritingMinimum"] = got["topUp"]
            return r

        carrier = policy(plan, again(cbook, graph))
        carrier.deviation = report.build(
            plan, book.resolution.state.pkg_id,
            str(technical.premium) if technical.complete else None,
            str(carrier.premium) if carrier.complete else None,
            technical.tree, carrier.tree,
            lambda p: policy(p, again(dv.CompanyBook(book, p))).premium, waterfall)
        if with_technical:
            carrier.technical = technical
        return carrier

    # ------------------------------------- the checks around ISO's rules (OI-139)
    # Plain functions in `checks` since OI-139, so a caller that runs ISO's rules some other way makes the same
    # checks without a Kernel; these call them in place.

    def _refuse_missing_rating_inputs(self, data: Node, book) -> None:
        """OI-134 / OI-130: `checks.refuse_missing_rating_inputs`, unless `ERC_RATING_INPUTS=off` (the measuring
        script needs it off)."""
        if RATING_INPUTS_CHECK == "off":
            return
        checks.refuse_missing_rating_inputs(data, book, self._schemas)

    #: The Loss of Electronic Data hosts whose `SetILF` copies `ILFOverride` in a refer band.
    LOED_HOSTS = checks.LOED_HOSTS

    @classmethod
    def _ilf_override_needed(cls, data: Node, exc: Exception) -> "RatingError | None":
        """OI-129: `checks.ilf_override_needed`."""
        return checks.ilf_override_needed(data, exc)

    def _refuse_null_loss_cost(self, result: Rating) -> None:
        """OI-94: `checks.refuse_null_loss_cost`."""
        checks.refuse_null_loss_cost(result)

    def _collect(self, result: Rating) -> None:
        """Read the premium and its parts out of the rated tree: `checks.collect`."""
        checks.collect(result)

    # ------------------------------------------------------------- referrals

    def _apply_register(self, result: Rating) -> None:
        """Enforce the referral register (underwriting mode only).

        Detectors observe the rated tree, the trace and the resolved book.
        Every register entry has an explicit disposition -- see
        `gl_engine/rating/referrals.py` -- so nothing is silently skipped.
        """
        by_code = {e["id"]: e for e in self.register}
        for f in referrals.run_detectors(result):
            entry = by_code.get(f.code, {})
            result.raise_referral(Referral(
                code=f.code,
                condition=entry.get("condition", f.detail),
                kind=entry.get("kind", ""),
                needs=entry.get("needs"),
                where=f"{f.where}: {f.detail}"))

    # ------------------------------------------------- register transparency

    def coverage(self) -> dict:
        """How much of the register this build actually enforces.

        Returned rather than asserted, because the honest number is small and
        hiding it would make the register read as coverage it does not have.
        """
        out = {referrals.DETECTED: [], referrals.NOT_REFERRAL: [],
               referrals.CONFIG: [], referrals.PENDING: []}
        for e in self.register:
            out[referrals.disposition(e["id"])].append(e["id"])
        return {k: tuple(sorted(v)) for k, v in out.items()}

    @property
    def enforced(self) -> tuple[str, ...]:
        return self.coverage()[referrals.DETECTED]

    @property
    def unenforced(self) -> tuple[str, ...]:
        """Carried but NOT checked. Named individually, never a count."""
        return self.coverage()[referrals.PENDING]


# --------------------------------------------------------------- detectors

def _refer_marker(result: Rating) -> str:
    """ISO's own 'Refer To Co.' text arriving in a rated value."""
    found = []

    def walk(n):
        if n.text and "refer" in str(n.text).lower():
            found.append(f"{n.path} = {n.text}")
        for c in n.children:
            walk(c)

    walk(result.tree)
    return "; ".join(found[:3])


#: Register entries this build detects. **Deliberately small and explicit.**
#: `Kernel.unenforced` names every one of the other 27, because a register that
#: claims 28 conditions and silently checks 1 reads as coverage it does not have.
#:
#: R03 is the refer sentinel -- ISO's own `Refer To Co.` text arriving where a
#: number was expected -- and it is the one condition detectable from the rated
#: tree alone. The rest need either load-time table inspection (R11, R13) or
#: hooks inside the rating path (R10, R12, R14, R15), which is stage 3 work
#: still to do rather than stage 3 work declared done.
_DETECTORS = {
    "R03": _refer_marker,
}


def rate(payload, mode: str = STRICT, **kw) -> Rating:
    """Convenience: rate one submission with a throwaway kernel."""
    return Kernel(mode=mode, **kw).rate(payload)
