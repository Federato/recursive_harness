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

import json
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

from ..errors import EngineError
from ..interp import Interpreter, Node
from ..interp import tree
from ..resolve import EditionResolver, ResolvedBook
from .submission import from_raas, load as load_submission

#: The two behavioural modes. One engine, one code path, two policies.
STRICT = "strict-erc"
UNDERWRITING = "underwriting"
MODES = (STRICT, UNDERWRITING)

#: Where the analysis phase left the referral register.
REGISTER = (Path(__file__).resolve().parent.parent.parent
            / "scripts" / "erc" / "out" / "referral_register.json")

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
    if not REGISTER.exists():
        return []
    return json.loads(REGISTER.read_text(encoding="utf-8")).get("entries", [])


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

    # ------------------------------------------------------------------ rate

    def rate(self, payload: dict | str | Path) -> Rating:
        """Rate one RAaS-shaped submission."""
        if isinstance(payload, (str, Path)):
            data, juris, asof = load_submission(payload)
        else:
            data, juris, asof = from_raas(payload)

        book = ResolvedBook(self.resolver.resolve(juris, asof))
        interp = Interpreter(book, rounding=self.rounding)

        result = Rating(juris=juris, asof=asof, mode=self.mode, book=book,
                        tree=data, trace=interp.trace,
                        messages=interp.messages)
        try:
            interp.run(data)
            result.complete = True
        except Exception as exc:                     # noqa: BLE001 - reported
            result.stopped = exc
            return result

        self._collect(result)
        if self.mode == UNDERWRITING:
            self._apply_register(result)
        return result

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

            for cov in risk.children:
                # `CoveragePremium` is where the money is in the 14
                # `PremiumToReachMinCoverage` groups; `Premium` sits alongside
                # it holding 0. Taking the first node that EXISTS finds the
                # zero and reports no coverages at all, so take the first that
                # carries a non-zero value and fall back to `Premium`.
                for tag in ("CoveragePremium", "Premium"):
                    node = cov.first(tag)
                    if node is not None and node.text not in (None, "", "0"):
                        result.by_coverage[cov.tag] = Decimal(node.text)
                        break

        result.premium = total

    # ------------------------------------------------------------- referrals

    def _apply_register(self, result: Rating) -> None:
        """Enforce the referral register (underwriting mode only).

        **Only the register entries whose condition the engine can actually
        detect are enforced**, and the rest are reported as un-enforced rather
        than quietly dropped. A register that claims 28 conditions and silently
        checks 4 is worse than no register, because it reads as coverage.
        """
        for entry in self.register:
            hook = _DETECTORS.get(entry["id"])
            if hook is None:
                continue
            hit = hook(result)
            if hit:
                result.raise_referral(Referral(
                    code=entry["id"], condition=entry["condition"],
                    kind=entry.get("kind", ""), needs=entry.get("needs"),
                    where=hit))

    @property
    def enforced(self) -> tuple[str, ...]:
        """Which register entries this build can actually detect."""
        return tuple(sorted(_DETECTORS))

    @property
    def unenforced(self) -> tuple[str, ...]:
        """Register entries carried but NOT checked. Named, never hidden."""
        return tuple(sorted(e["id"] for e in self.register
                            if e["id"] not in _DETECTORS))


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
