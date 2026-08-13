"""Which rules apply, for this state, on this date.

Five steps, and every one of them has a tempting shortcut that is wrong:

1. **Packages for the jurisdiction**, identity from the XSD (N6) -- not the path.
2. **Discard editions effective after the date** (N4). "Latest" is never "now":
   this corpus holds 82 state packages effective after today, so any figure taken
   over the newest edition describes the future.
3. **Latest remaining, tie-broken on version.** Same-day filings exist.
4. **The parent the resolved package DECLARES** (N5) -- read from its `xs:import`,
   not the newest countrywide package. For five states today the declared parent
   is *not* the newest, and nothing but this rule catches them.
5. **Parent absent -> hard failure.** Never a fallback. A fallback here produces
   a complete, plausible, wrong premium.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

from ..config import COUNTRYWIDE, MIN_ASOF
from ..errors import ResolutionError
from ..erc.discovery import Package, discover


@dataclass(frozen=True)
class Resolution:
    """The answer: a state package, its declared parent, and the date asked."""

    juris: str
    asof: str
    state: Package
    parent: Package | None       # None only when the jurisdiction IS countrywide

    @property
    def layers(self) -> tuple[Package, ...]:
        """State first -- override order. Countrywide is the fallback layer."""
        return (self.state,) if self.parent is None else (self.state, self.parent)

    def __repr__(self) -> str:   # pragma: no cover - display only
        par = self.parent.pkg_id if self.parent else "-"
        return f"<Resolution {self.juris}@{self.asof} {self.state.pkg_id} -> {par}>"


def _valid_date(asof: str) -> str:
    if not (isinstance(asof, str) and len(asof) == 8 and asof.isdigit()):
        raise ResolutionError(f"as-of date must be YYYYMMDD, got {asof!r}")
    if asof < MIN_ASOF:
        raise ResolutionError(
            f"as-of {asof} is before {MIN_ASOF}; below that date this corpus "
            f"cannot resolve all 51 jurisdictions (OI-41). Refusing rather than "
            f"serving a partial answer.")
    return asof


class EditionResolver:
    """Holds the discovered corpus and answers (jurisdiction, date) questions."""

    def __init__(self, packages: list[Package] | None = None,
                 root: Path | None = None):
        self._packages = list(packages) if packages is not None else discover(root)

    # ------------------------------------------------------------- inventory

    @property
    def packages(self) -> list[Package]:
        return list(self._packages)

    @cached_property
    def by_juris(self) -> dict[str, list[Package]]:
        out: dict[str, list[Package]] = {}
        for p in self._packages:
            out.setdefault(p.identity.juris, []).append(p)
        for v in out.values():
            v.sort(key=lambda p: p.identity.sort_key)
        return out

    @cached_property
    def by_id(self) -> dict[str, Package]:
        return {p.pkg_id: p for p in self._packages}

    @cached_property
    def jurisdictions(self) -> list[str]:
        """Every jurisdiction in the corpus, countrywide excluded."""
        return sorted(j for j in self.by_juris if j != COUNTRYWIDE)

    # ------------------------------------------------------------- resolving

    def editions(self, juris: str, asof: str) -> list[Package]:
        """Editions of `juris` in force on or before `asof`, oldest first."""
        asof = _valid_date(asof)
        return [p for p in self.by_juris.get(juris.upper(), [])
                if p.identity.edition <= asof]

    def resolve(self, juris: str, asof: str) -> Resolution:
        juris = juris.upper()
        asof = _valid_date(asof)
        pool = self.by_juris.get(juris)
        if not pool:
            raise ResolutionError(
                f"no packages for jurisdiction {juris!r}; the corpus holds "
                f"{len(self.jurisdictions)} jurisdictions and this is not one "
                f"of them")
        eligible = [p for p in pool if p.identity.edition <= asof]
        if not eligible:
            first = pool[0].identity.edition
            raise ResolutionError(
                f"{juris} has no edition in force on {asof}; its earliest is "
                f"{first}")
        state = eligible[-1]                      # sorted by (edition, version)

        if state.is_countrywide:
            return Resolution(juris, asof, state, None)

        declared = state.declared_parent
        if not declared:
            raise ResolutionError(
                f"{state.pkg_id} declares no countrywide parent; there is no "
                f"correct default and guessing one would rate the risk against "
                f"rules the state never adopted (N5)")
        parent = self.by_id.get(declared)
        if parent is None:
            raise ResolutionError(
                f"{state.pkg_id} declares parent {declared} which is not in the "
                f"corpus; refusing to fall back to the newest countrywide "
                f"edition (N5)")
        return Resolution(juris, asof, state, parent)

    def resolve_all(self, asof: str) -> dict[str, Resolution]:
        """Every jurisdiction at one date. Raises on the first that will not."""
        return {j: self.resolve(j, asof) for j in self.jurisdictions}

    def declared_parents(self, asof: str) -> dict[str, list[str]]:
        """parent package id -> the jurisdictions declaring it, at this date.

        More than one entry is normal and is the point: three countrywide
        editions are live today and three at the 2027 cliff. There is no date at
        which one parent suffices.
        """
        out: dict[str, list[str]] = {}
        for j, r in self.resolve_all(asof).items():
            if r.parent:
                out.setdefault(r.parent.pkg_id, []).append(j)
        return {k: sorted(v) for k, v in sorted(out.items())}
