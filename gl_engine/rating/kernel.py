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
from . import referrals
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

#: Paths the kernel reads a result out of, relative to a `GeneralLiability`.
TOTAL = "Premium"
TOTAL_CHECK = "ErcCalculatedTotalPremium"


class RatingError(EngineError):
    """The submission could not be rated."""


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
        for code, covs in referrals.not_offered(result).items():
            result.notices.append(f"Not offered: {', '.join(covs)} for class {code} (ISO's table reads "
                                  f"\"Not Applicable\"); it prices $0 or the $1 minimum by design")
        for f in referrals.d_silent_zero(result) + referrals.d_terrorism_endorsement_factor(result):
            result.notices.append(f"{f.code} {f.where}: {f.detail}")
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
            book = dv.book_for(plan) if plan.pin else iso_book
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

        carrier = again(cbook, graph)
        current = again(iso_book).premium if (waterfall and plan.pin) else None
        carrier.deviation = report.build(
            plan, book.resolution.state.pkg_id,
            str(technical.premium) if technical.complete else None,
            str(carrier.premium) if carrier.complete else None,
            technical.tree, carrier.tree,
            lambda p: again(dv.CompanyBook(book, p)).premium, current, waterfall)
        if with_technical:
            carrier.technical = technical
        return carrier

    # --------------------------------------------- OI-134, a missing rating input

    def _refuse_missing_rating_inputs(self, data: Node, book) -> None:
        """Refuse a submission that leaves out an input ISO requires and the premium depends on. **OI-134.**

        ISO's field file marks each input required, often only when a condition holds
        (`ProdsCompldOpsExclusion` when the subline includes Products). ISO's rating service does not apply
        its own form's requirements: left out, `ProdsCompldOpsExclusion` switches Products/Completed Ops off
        and ISO prices TX at $895 instead of $7,740, with no message (confirmed live 2026-10-13). Measured by
        `scripts/erc/57_rating_inputs.py`, fourteen such inputs move the premium silently when left out
        (`Subline` to $0, a premium basis to $6,783,982). **A missing rating input is not a zero-rated risk;
        it is an unrated one** -- the same distinction as OI-94 one step earlier.

        Only the inputs in `rating_inputs.json` refuse; every other missing required field is a validator
        warning (V6), because ISO rates without it and the premium does not move. A condition the evaluator
        cannot read reports nothing rather than guess. `ERC_RATING_INPUTS=off` disables the check (the
        measuring script needs it off).
        """
        if RATING_INPUTS_CHECK == "off":
            return
        from ..schema import Schema
        from ..schema.validate import (invalid_values, list_inputs, missing_required, stop_gap_conflict,
                                       stop_gap_unrated_limits)
        key = tuple(getattr(x, "pkg_id", None) for x in (book.resolution.state, book.resolution.parent))
        schema = self._schemas.get(key)
        if schema is None:
            schema = self._schemas[key] = Schema.for_book(book)
        if stop_gap_conflict(data) == "unanswered":
            raise RatingError(
                "Stop Gap details were sent but GeneralLiability.StopGap was not answered. Without the answer the "
                "rules price Stop Gap at $0 with no message (ISO's own service does the same). Answer StopGap "
                "\"Yes\" to price it, or \"No\" to leave it off (OI-130).")
        if stop_gap_unrated_limits(data):
            raise RatingError(
                "Stop Gap's accident limit differs from its each-employee disease limit and no ManualPremium was "
                "given. ISO's rules rate Stop Gap only when the two are equal; otherwise it prices $0 with no message "
                "(ISO's own service does the same). Give a ManualPremium, or equal limits, to rate (OI-130).")
        missing = [m for m in missing_required(data, schema)[0] if m.rating_input]
        if not missing:
            # OI-130 (B-07 part 2): an answer not on ISO's list for this edition -- a retired class code, last
            # edition's limit spelling -- matches no row and prices that part at $0 or the $1 floor, silently
            # (ISO does the same). Only the measured `list_fields` refuse; the rest stay validator V3 errors.
            bad = invalid_values(data, schema, list_inputs())
            if bad:
                name, value, legal = bad[0]
                more = f" (and {len(bad) - 1} more: {', '.join(b[0] for b in bad[1:4])})" if len(bad) > 1 else ""
                raise RatingError(
                    f"{name} = {value!r} is not on ISO's list for this edition (e.g. {legal}){more}. The rules "
                    f"match no row for it and price that part at $0 or the $1 minimum, with no message (ISO's "
                    f"own service does the same). Use a value from ISO's list to rate (OI-130).")
            return
        m = missing[0]
        others = f" (and {len(missing) - 1} more: {', '.join(x.name for x in missing[1:4])})" if len(missing) > 1 else ""
        raise RatingError(
            f"{m.name} is required{' when ' + m.condition if m.condition else ''} and was not supplied{others}. "
            f"ISO's form requires it and the premium depends on it: left out, the rules price the risk as if it "
            f"were absent, with no message (ISO's own service does the same). Supply it to rate (OI-134).")

    # ------------------------------------------- OI-129, LoED refer-to-company

    #: The Loss of Electronic Data hosts whose `SetILF` copies `ILFOverride` in a refer band.
    LOED_HOSTS = ("GeneralLiabilityClassificationLossOfElectronicDataPremOpsCoverage",
                  "GeneralLiabilityClassificationLossOfElectronicDataProdsCompldOpsCoverage")

    @classmethod
    def _ilf_override_needed(cls, data: Node, exc: Exception) -> "RatingError | None":
        """A Loss of Electronic Data limit in a refer band, with no `ILFOverride`, refuses by name. **OI-129.**

        `SetILF`'s first branch fires when the (limit, aggregate) pair falls in one of 13 filed "refer to company"
        bands -- $100,000 under a standard $2,000,000 aggregate is one -- and copies the submitted `ILFOverride`.
        Left out, `ILF` is null and the rating stops at `SetFinalILF` with a bare null-in-arithmetic, before
        `DoMessageILF` can say why. ISO's service (2 calls, IL@20270401, 2026-10-14) prices both hosts at
        `FinalILF 0`, LoED $0, and raises the error quoted below; with the override it matches us to the dollar.

        **Observed, not re-derived:** the bands are not copied here. This reads what ISO's rule did -- a host
        whose `ILF` was written null with no override answered -- and only turns that one stop into a refusal.
        ISO's schema cannot say it: it marks `ILFOverride` required whenever LoED applies, band or not.
        """
        from ..interp.values import NullInArithmetic
        from ..schema.validate import _unanswered
        if not isinstance(exc, NullInArithmetic):
            return None
        hosts = []

        def walk(node):
            for child in node.children:
                if child.tag in cls.LOED_HOSTS:
                    ilf = child.first("ILF")
                    if ilf is not None and ilf.text is None and _unanswered(child.first("ILFOverride")):
                        hosts.append(f"{child.tag}.ILFOverride")
                walk(child)

        walk(data)
        if not hosts:
            return None
        return RatingError(
            f"{', '.join(dict.fromkeys(hosts))} is required: the Loss of Electronic Data limit and the aggregate "
            f"fall in a filed refer-to-company band, where ISO's rules take the ILF from the submission. ISO's "
            f"service says \"The ILF for The Loss of Electronic data Limit and the General Aggregate Limit is refer "
            f"to company, please enter the ILF override\" and prices Loss of Electronic Data at $0. Supply the "
            f"company's ILF to rate; the Products/Completed Operations host reads the same bands against its own "
            f"aggregate (OI-129).")

    # ------------------------------------------------------ OI-94, the refusal

    def _refuse_null_loss_cost(self, result: Rating) -> None:
        """A loss cost that resolved to null makes the risk unratable. **OI-94.**

        ISO's own service refuses here. Its 400 is not a validation complaint
        but its rule engine failing: *"Matrix: PremOpsSizeOfRiskLossCost, Keys:
        CW, 502, 50017. No results have been found."* We reached the identical
        miss -- state, then the countrywide retry -- and then carried on,
        because the `FirstNonNull` exhausted and **C6 correctly returns null
        rather than raising**.

        **C6 is not the bug and must not be changed.** An exhausted
        `FirstNonNull` yielding null is what ISO relies on, at 4,327 sites that
        can exhaust. The mistake is downstream of the language: **a missing loss
        cost is not a zero-rated risk, it is an unratable one**, and only the
        rating layer knows the difference.

        `0` is a legal, filed loss cost and is left alone -- OK writes
        `ProdsCompldOpsLossCost = 0` on a risk that rates correctly. **Only a
        null is refused**, which is the distinction E20/OI-68 is about in a
        different place.

        Measured before it was written: **14 of 51 jurisdictions returned a
        premium this way with size-of-risk on, 0 of 51 without it**, and eight
        of the fourteen returned the identical `6845` on different base
        premiums -- a premium that does not depend on the state's loss cost.
        """
        bad = []

        def walk(node, path=""):
            for child in node.children:
                here = f"{path}/{child.tag}"
                if child.tag.endswith("LossCost") and child.text is None:
                    bad.append(here)
                walk(child, here)

        walk(result.tree)
        if not bad:
            return

        names = [b.rsplit("/", 1)[-1] for b in bad]
        # Name the table that actually came back empty, not the node the null
        # was written into. An adversarial review on 2026-08-17 caught this
        # message blaming `PremOpsLossCost` -- a healthy 9,504-row table in
        # Texas that had resolved 0.095 perfectly well -- when the empty table
        # was `PremOpsSizeOfRiskLossCost`, which Texas never filed. An
        # investigator following the old wording went to the wrong file.
        empty = [t.data.get("table") or t.detail.split("[")[0]
                 for t in (result.trace or [])
                 if t.kind == "lookup-miss"]
        sor = sorted({e for e in empty if "SizeOfRisk" in str(e)})
        why = ""
        if sor:
            why = (f" The lookup that came back empty is {sor[0]}, not the "
                   f"loss-cost table itself: this jurisdiction has not filed "
                   f"the size-of-risk rating plan, so no classification can "
                   f"rate under it.")
        raise RatingError(
            f"{names[0]} resolved to null and the risk cannot be rated.{why} "
            f"{len(bad)} null loss cost node(s): {', '.join(names[:4])}. "
            f"(OI-94)")

    # --------------------------------------------------------------- results

    def _collect(self, result: Rating) -> None:
        """Read the premium and its parts out of the rated tree."""
        risks = tree.select("GeneralLiabilityTable/GeneralLiability",
                            result.tree)
        if not risks:
            raise RatingError(
                "the rated tree carries no GeneralLiability risk; the "
                "submission mapping is wrong and a premium here would be "
                "fiction")

        total = Decimal(0)
        for risk in risks:
            raw = tree.read(TOTAL, risk)
            if raw is None:
                raise RatingError(
                    f"no {TOTAL} on a rated risk. ISO's own total rule wrote "
                    f"nothing, which is a defect in us, not a zero premium")
            total += Decimal(raw)

            # The check figure ISO writes alongside the total. They are computed
            # by the same rule, so a disagreement means we mis-executed it.
            check = tree.read(TOTAL_CHECK, risk)
            if check is not None and Decimal(check) != Decimal(raw):
                raise RatingError(
                    f"{TOTAL}={raw} disagrees with {TOTAL_CHECK}={check}")

            # The breakdown is every `Premium` ISO's rules mark as money (`PremiumIndicator = 1`), at whatever level it
            # sits, summed per coverage across locations and classifications (OI-132, B-11). It used to read the 14
            # policy-level `PremiumToReachMinCoverage` groups' `CoveragePremium`: pre-2027 that showed the coverage
            # under its minimum-premium top-up's name and dropped the top-up itself; from CW 2027, which stubs those
            # groups, the breakdown was empty on every rating. Measured 2026-10-14: the marked premiums add up to
            # ErcCalculatedTotalPremium on every request tried, both editions, every subline.
            def money(node):
                for c in node.children:
                    prem, ind = c.first("Premium"), c.first("PremiumIndicator")
                    if (prem is not None and ind is not None and str(ind.text).strip() in ("1", "1.0")
                            and prem.text not in (None, "")):
                        result.by_coverage[c.tag] = result.by_coverage.get(c.tag, Decimal(0)) + Decimal(prem.text)
                    money(c)
            money(risk)

        result.premium = total

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
