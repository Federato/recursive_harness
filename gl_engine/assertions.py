"""Load-time assertions. They FAIL. None of them warns.

Build plan section 10 lists these, and each was measured before it was written
down -- so a failure here means the corpus changed or we did, never that the
assertion was aspirational.

The distinction that matters throughout: **an assertion tests a property of the
corpus, not a property of the code that reads it.** A10 is the clearest case. It
asserts that both spellings of `ProductWithdraw(a)l` survive as distinct
artifacts, because at some point someone will "fix the typo" by normalising them
and quietly merge two different things.
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from decimal import Decimal

from .config import COUNTRYWIDE, MIN_ASOF
from .erc.tables import Population, Shape
from .errors import AssertionFailure

#: OI-47. Both spellings exist in ERC and they are NOT the same artifact.
WITHDRAWAL_SPELLINGS = ("ProductWithdrawl", "ProductWithdrawal")

#: ILF tables known to carry a ZERO in the factor column. A zero increased-limit
#: factor would price the highest limits at nil, so it is a sentinel (N13), not
#: the number nought -- and stage 1's job is to refuse to treat it as arithmetic.
#: Found on 2026-08-12 by A11, which was looking for something else.
#: 60 of 53,241 factor cells, in 3 of 54 resolved packages, at 2026-08-11.
#: The assertion is that the set of TABLES does not grow unnoticed; the count is
#: reported but is as-of-date dependent and is not itself asserted.
#: The one non-monotonic ILF series in the corpus, and why it is allowed past.
#: E20 / OI-68, raised 2026-08-12 by this assertion. Texas Elevator Contractor
#: publishes a factor of exactly 1.00 at 22 of its 26 aggregate limits and a
#: genuine 1.69-1.72 at four of them, so 1.00 there prices a 20,000,000
#: aggregate identically to a 50,000 one. Either 1.00 means "no increased-limit
#: load applies" or it is a placeholder -- ERC cannot say which, so it escalates.
#: ONE IS THE NEW ZERO, and it is worse: multiplying by a sentinel zero produces
#: a visible nil premium, multiplying by a sentinel one produces a plausible
#: wrong one.
#:
#: RECURS ACROSS EVERY TEXAS EDITION -- 26 of 30 rows at 1.00 in all six editions
#: from 2021-06-01 to 2025-08-01, and 11 of 15 in the 2027 one, which halves the
#: table while preserving all four genuine factors. A pattern stable across seven
#: consecutive filings over six years is not a typo, so "placeholder" is the
#: WEAKER reading and "no increased-limit load applies at this combination" the
#: stronger one. It still refers: the series is still non-monotonic, ERC still
#: carries no discriminator, and the safe direction is unchanged.
KNOWN_NONMONOTONIC = {
    ("GL_TX_20210601_V01", "ILFElevatorContractor"): "E20",
    ("GL_TX_20220401_V02", "ILFElevatorContractor"): "E20",
    ("GL_TX_20230501_V01", "ILFElevatorContractor"): "E20",
    ("GL_TX_20240101_V01", "ILFElevatorContractor"): "E20",
    ("GL_TX_20240801_V01", "ILFElevatorContractor"): "E20",
    ("GL_TX_20250801_V01", "ILFElevatorContractor"): "E20",
    ("GL_TX_20270401_V01", "ILFElevatorContractor"): "E20",
}

ZERO_FACTOR_TABLES = frozenset({
    "ILFLiquorWithSubLimit",
    "ILFElevatorContractors",
    "ILFElevatorContractorsOrInspectors",
})


@dataclass
class Check:
    code: str
    title: str
    passed: bool
    detail: str = ""
    counted: str = ""            # the 'n of N' this check actually measured

    def __str__(self) -> str:    # pragma: no cover - display only
        mark = "PASS" if self.passed else "FAIL"
        tail = f"  [{self.counted}]" if self.counted else ""
        return f"  {mark}  {self.code}  {self.title}{tail}\n        {self.detail}"


@dataclass
class Report:
    asof: str
    checks: list = field(default_factory=list)

    def add(self, *a, **kw):
        self.checks.append(Check(*a, **kw))

    @property
    def failures(self):
        return [c for c in self.checks if not c.passed]

    @property
    def ok(self) -> bool:
        return not self.failures

    def raise_if_failed(self):
        if self.failures:
            first = self.failures[0]
            raise AssertionFailure(
                first.code,
                f"{len(self.failures)} of {len(self.checks)} load-time "
                f"assertions failed; first: {first.title} -- {first.detail}",
                detail=self.failures)


# --------------------------------------------------------------------- suite

def run_all(resolver, asof: str, deep: bool = False) -> Report:
    """Every load-time assertion, at one as-of date.

    `deep=True` adds the checks that must open table CSVs across all 51
    jurisdictions. They are correct either way; they are just slow.
    """
    rep = Report(asof)
    _a1_identity(resolver, rep)
    _a2_namespace_consistency(resolver, rep)
    _a3_asof_floor(resolver, rep, asof)
    _a4_all_resolve(resolver, rep, asof)
    _a5_declared_parents(resolver, rep, asof)
    _a6_parent_not_newest(resolver, rep, asof)
    if deep:
        books = {j: r for j, r in _books(resolver, asof)}
        _a7_table_shapes(books, rep)
        _a8_header_reconciles(books, rep)
        _a9_split_families(books, rep)
        _a10_withdrawal_spellings(books, rep)
        _a11_ilf_monotonic(books, rep)
        _a12_value_alphabet(books, rep)
        _a13_zero_factor_sentinels(books, rep)
    return rep


def _books(resolver, asof: str):
    from .resolve.book import ResolvedBook
    for j in resolver.jurisdictions:
        yield j, ResolvedBook(resolver.resolve(j, asof))


# ------------------------------------------------------------------ A1 - A6

def _a1_identity(resolver, rep):
    pkgs = resolver.packages
    bad = [p for p in pkgs if not p.identity.raw]
    rep.add("A1", "every package identifies itself from its XSD namespace (N6)",
            not bad, f"{len(bad)} without an identity",
            f"{len(pkgs) - len(bad)} of {len(pkgs)} packages")


def _a2_namespace_consistency(resolver, rep):
    """A package whose XSDs disagree about which package they belong to."""
    bad = [(p.pkg_id, sorted(p.namespaces)) for p in resolver.packages
           if len(p.namespaces) != 1]
    rep.add("A2", "each package's XSDs all declare ONE namespace",
            not bad, str(bad[:3]) if bad else "no package disagrees with itself",
            f"{len(resolver.packages) - len(bad)} of {len(resolver.packages)} packages")


def _a3_asof_floor(resolver, rep, asof):
    ok = asof >= MIN_ASOF
    rep.add("A3", f"as-of date is on or after {MIN_ASOF} (OI-41)", ok,
            f"asked for {asof}" if ok else
            f"{asof} is below the floor; not all 51 jurisdictions resolve there")


def _a4_all_resolve(resolver, rep, asof):
    js = resolver.jurisdictions
    failed = []
    for j in js:
        try:
            resolver.resolve(j, asof)
        except Exception as e:
            failed.append((j, str(e)[:90]))
    rep.add("A4", "every jurisdiction resolves to an edition at this date (N4)",
            not failed, str(failed[:3]) if failed else
            f"all {len(js)} jurisdictions in force",
            f"{len(js) - len(failed)} of {len(js)} jurisdictions")


def _a5_declared_parents(resolver, rep, asof):
    """The parent each state DECLARES must exist. Never fall back (N5)."""
    missing = []
    for j in resolver.jurisdictions:
        try:
            r = resolver.resolve(j, asof)
        except Exception:
            continue
        if r.parent is None:
            missing.append((j, "no parent declared"))
    rep.add("A5", "every resolved state declares a parent present in the corpus (N5)",
            not missing, str(missing[:3]) if missing else
            "every declared parent resolved",
            f"{len(resolver.jurisdictions) - len(missing)} of "
            f"{len(resolver.jurisdictions)} jurisdictions")


def _a6_parent_not_newest(resolver, rep, asof):
    """Not a defect check -- a REGRESSION check on the rule itself.

    Several states declare a parent that is not the newest countrywide edition
    in force. If this ever counts zero, the resolver has started taking the
    newest, and every one of those states is being rated against rules it never
    adopted. The assertion is that the phenomenon still exists to be handled.
    """
    parents = resolver.declared_parents(asof)
    cw = [p for p in resolver.by_juris.get(COUNTRYWIDE, [])
          if p.identity.edition <= asof]
    newest = cw[-1].pkg_id if cw else None
    older = {p: js for p, js in parents.items() if p != newest}
    n_states = sum(len(js) for js in older.values())
    rep.add("A6", "declared parent is honoured even when it is not the newest (N5)",
            bool(older),
            f"newest CW in force is {newest}; {n_states} states declare an older "
            f"parent: {ureprs(older)}" if older else
            "NO state declares an older parent -- the rule is untested here",
            f"{len(parents)} distinct parents live at {asof}")


def ureprs(d):
    return ", ".join(f"{k} <- {len(v)} ({','.join(v[:6])}"
                     f"{'...' if len(v) > 6 else ''})" for k, v in d.items())


# ----------------------------------------------------------------- A7 - A12

def _a7_table_shapes(books, rep):
    """Every table classifies into a known shape. No 'other' bucket."""
    shapes = Counter()
    for b in books.values():
        for kind in ("Rate", "Domain"):
            for layer in (b.state, b.parent):
                if layer is None:
                    continue
                for n in layer.names(kind):
                    shapes[layer.table(kind, n).shape] += 1
    total = sum(shapes.values())
    rep.add("A7", "every table classifies into a declared shape",
            total > 0 and set(shapes) <= set(Shape),
            ", ".join(f"{k.value}={v}" for k, v in shapes.most_common()),
            # N stated explicitly: this is per-JURISDICTION-VIEW, so one
            # countrywide table is counted once per state that inherits it.
            # The deduplicated figure is smaller and `cli census` reports it.
            f"{total} table instances across {len(books)} jurisdiction views")


def _a8_header_reconciles(books, rep):
    """The CSV header equals KeyCols+ValueCols, in order, where a Def exists."""
    bad, n = [], 0
    for b in books.values():
        for kind in ("Rate", "Domain"):
            for layer in (b.state, b.parent):
                if layer is None:
                    continue
                for name in layer.names(kind):
                    t = layer.table(kind, name)
                    if not t.definition.declared or not t.rows:
                        continue
                    n += 1
                    if list(t.header) != t.definition.header:
                        bad.append(f"{t.package}/{name}")
    rep.add("A8", "CSV header reconciles with the declared column order",
            not bad, str(sorted(set(bad))[:3]) if bad else "exact in every case",
            f"{n - len(bad)} of {n} populated declared tables")


def _a9_split_families(books, rep):
    """OI-20: a split loss-cost family must have rows, or read as unavailable.

    The dangerous state is narrow and specific: **slices carry rows and the
    reader cannot find them**, so the base name yields zero and a finished
    premium comes out. A family where EVERYTHING is empty is not dangerous --
    `rating_table()` raises on it -- and at the 2027 cliff that state is normal
    rather than exceptional, because size-of-risk is withdrawn wholesale.

    The first version failed on those, which would have made the suite red at
    every date after 2027-04-01 for a corpus that is behaving correctly.

    Counted over every jurisdiction that HAS slices, not over the ones whose base
    table happens to sit in the same layer -- that narrower population is what
    the version before THAT measured, and it reported 1 family where there are 6.
    """
    fams, broken, empty_base, withdrawn = 0, [], 0, []
    for j, b in books.items():
        for name in sorted({n for layer in (b.state, b.parent) if layer
                            for n in layer.families("Rate")}):
            sibs = b.sibling_tables(name, "Rate")
            if not sibs:
                continue
            fams += 1
            rows = sum(len(t) for t in sibs)
            # The base name is DERIVED from the slice names, so it need not
            # exist as a table at all -- and in most of these jurisdictions it
            # does not. `no base` is the strongest form of the OI-20 defect.
            layer = b.declares(name, "Rate")
            base_empty = layer is None or b.table(name, "Rate").is_empty
            empty_base += bool(base_empty)
            if rows:
                continue
            if base_empty:
                # nothing anywhere: withdrawn. A rating read must still fail.
                try:
                    b.rating_table(name, "Rate")
                except Exception:
                    withdrawn.append(f"{j}/{name}")
                else:
                    broken.append(f"{j}/{name} reads as available while empty")
            else:
                broken.append(f"{j}/{name}")
    rep.add("A9", "split loss-cost slices carry rows, or the family fails loudly (OI-20)",
            not broken, str(broken[:3]) if broken else
            f"{fams} split families across {len(books)} jurisdictions; "
            f"{empty_base} have an EMPTY OR ABSENT base name that would "
            f"otherwise resolve upward to a header-only countrywide table; "
            f"{len(withdrawn)} withdrawn entirely and refusing to rate "
            f"{sorted(withdrawn) if withdrawn else ''}",
            f"{fams - len(broken)} of {fams} split families")


def _a10_withdrawal_spellings(books, rep):
    """OI-47. Both spellings must survive as DISTINCT artifacts."""
    seen = Counter()
    for b in books.values():
        for layer in (b.state, b.parent):
            if layer is None:
                continue
            for kind in ("Rate", "Domain"):
                for n in layer.names(kind):
                    for sp in WITHDRAWAL_SPELLINGS:
                        # the shorter spelling is a substring of the longer one,
                        # so match the shorter only where the longer is absent
                        if sp == "ProductWithdrawl" and "ProductWithdrawal" in n:
                            continue
                        if sp in n:
                            seen[sp] += 1
    both = all(seen.get(s) for s in WITHDRAWAL_SPELLINGS)
    rep.add("A10", "both spellings of ProductWithdraw(a)l survive distinctly (OI-47)",
            both, ", ".join(f"{k}={v}" for k, v in sorted(seen.items())),
            f"{len(seen)} of {len(WITHDRAWAL_SPELLINGS)} spellings present")


_ILF_RE = re.compile(r"^ILF")

#: A limit as ISO writes it: `'1,000,000 CSL'`, `'500,000 BI'`, `'300,000'`.
#: The suffix is the basis -- combined single limit, bodily injury, property
#: damage. Limits with DIFFERENT bases are not comparable and must never be
#: sorted into one series.
_LIMIT = re.compile(r"^([\d,]+)(?:\s+(CSL|BI|PD))?$")


def _limit_axes(table):
    """Which columns of an ILF table are ORDERABLE limits. Measured per table.

    Not chosen by name. `IncreasedLimitsTableAssignmentPremOpsFinal` contains
    the word `Limit`, is not a limit, and is the reason this function exists --
    the first version of A11 matched it by name and asserted that factors rise
    with the table-assignment number, which is meaningless. Worse, the same
    selector is an INTEGER 1/2/3 in `ILFPremOps` and the LETTERS A/B/C in
    `ILFProds`, so no type test catches it either.

    The test here is behavioural: a column is a limit axis only if every value
    in it parses as an amount. That is the counting discipline applied to
    columns -- the predicate may not define the population.
    """
    axes = []
    for i, h in enumerate(table.header):
        if "Limit" not in h or "Assignment" in h:
            continue
        if table.definition.type_of(h) != "string":
            continue
        vals = [str(r[i]) for r in table.rows if r[i] is not None]
        if vals and all(_LIMIT.match(v) for v in vals):
            axes.append(i)
    return axes


def _limit_key(raw: str):
    m = _LIMIT.match(str(raw))
    return (m.group(2) or "", int(m.group(1).replace(",", ""))) if m else None


def _a12_value_alphabet(books, rep):
    """Cells declared numeric must be numeric or a known marker.

    A string surviving into a `decimal` column is either a sentinel we have not
    catalogued or a corrupt cell, and both need a human. This is where N13's
    eight meanings of zero get caught before they become premiums.
    """
    offenders = Counter()
    checked = 0
    for b in books.values():
        for kind in ("Rate",):
            for layer in (b.state, b.parent):
                if layer is None:
                    continue
                for name in layer.names(kind):
                    t = layer.table(kind, name)
                    if not t.rows:
                        continue
                    types = [t.definition.type_of(h) for h in t.header]
                    num = [i for i, ty in enumerate(types)
                           if ty in ("decimal", "integer", "long")]
                    for row in t.rows:
                        for i in num:
                            checked += 1
                            v = row[i]
                            if v is None or isinstance(v, (int, Decimal)):
                                continue
                            offenders[str(v)[:20]] += 1
    rep.add("A12", "numeric columns hold numbers or nothing, never stray text",
            not offenders,
            ", ".join(f"{k!r}x{v}" for k, v in offenders.most_common(5))
            or "no non-numeric value in any numeric column",
            f"{checked - sum(offenders.values())} of {checked} numeric cells")


def _a11_ilf_monotonic(books, rep):
    """Increased limit factors must not fall as a limit rises -- in BOTH axes.

    An ILF table is a grid: occurrence limit one way, aggregate limit the other.
    The property is checked one axis at a time with every other column held
    fixed, and only within one basis -- a CSL limit and a BI limit of the same
    face amount are different things and sorting them together would invent a
    violation.

    A falling ILF prices a higher limit below a lower one. No filing intends it,
    and a mis-keyed lookup produces it silently.
    """
    bad, series, axes_seen, skipped, escalated = [], 0, 0, 0, 0
    for j, b in books.items():
        for layer in (b.state, b.parent):
            if layer is None:
                continue
            for name in layer.names("Rate"):
                if not _ILF_RE.match(name):
                    continue
                t = layer.table("Rate", name)
                if not t.rows:
                    continue
                types = [t.definition.type_of(h) for h in t.header]
                vals = [i for i, ty in enumerate(types) if ty == "decimal"]
                if not vals:
                    continue
                vi = vals[0]
                axes = _limit_axes(t)
                axes_seen += len(axes)
                for ax in axes:
                    groups = {}
                    for row in t.rows:
                        k = _limit_key(row[ax])
                        if k is None or not isinstance(row[vi], Decimal):
                            continue
                        if row[vi] == 0:
                            # a zero factor is a sentinel, not a value (N13).
                            # Ordering it as a number is what produced the only
                            # eight "violations" this assertion ever reported.
                            skipped += 1
                            continue
                        # everything except the axis and the factor, PLUS the
                        # basis suffix -- that is what "holding the rest fixed"
                        # means here
                        rest = tuple(row[i] for i in range(len(t.header))
                                     if i not in (ax, vi)) + (k[0],)
                        groups.setdefault(rest, []).append((k[1], row[vi]))
                    for rest, pts in groups.items():
                        if len(pts) < 2:
                            continue
                        series += 1
                        pts.sort()
                        drop = [(a, x, c, y) for (a, x), (c, y)
                                in zip(pts, pts[1:]) if y < x]
                        if drop:
                            if (t.package, name) in KNOWN_NONMONOTONIC:
                                escalated += 1
                                continue
                            a, x, c, y = drop[0]
                            bad.append(f"{t.package}/{name} "
                                       f"[{t.header[ax]}] {a:,}->{c:,} {x}->{y}")
    rep.add("A11", "ILF factors never decrease as a limit rises, in either axis",
            not bad, "; ".join(sorted(set(bad))[:3]) if bad else
            f"monotonic in every series across {axes_seen} limit axes "
            f"({skipped} sentinel zeros excluded -- see A13; "
            f"{escalated} series escalated, see KNOWN_NONMONOTONIC)",
            f"{series - len(bad)} of {series} ILF series")


def _a13_zero_factor_sentinels(books, rep):
    """A zero in a FACTOR column is a sentinel, and the set of them is fixed.

    N13: zero has eight meanings in this corpus and only one is the number
    nought. A zero increased-limit factor cannot be arithmetic -- it would price
    the highest limits at nil premium -- so it is a marker whose meaning the
    interpreter must resolve, and stage 1's duty is to notice it and hand it on
    rather than multiply by it.

    This assertion does NOT pin the count, which moves with the as-of date. It
    pins the set of TABLE NAMES, so a zero appearing somewhere new fails the load
    and gets a human rather than a free policy.
    """
    hits = Counter()
    checked = 0
    for b in books.values():
        for layer in (b.state, b.parent):
            if layer is None:
                continue
            for name in layer.names("Rate"):
                if not _ILF_RE.match(name):
                    continue
                t = layer.table("Rate", name)
                if not t.rows:
                    continue
                vi = [i for i, h in enumerate(t.header)
                      if t.definition.type_of(h) == "decimal"]
                if not vi:
                    continue
                for row in t.rows:
                    checked += 1
                    if row[vi[0]] == 0:
                        hits[name] += 1
    novel = sorted(set(hits) - ZERO_FACTOR_TABLES)
    rep.add("A13", "zero ILF factors appear only in tables known to use the sentinel (N13)",
            not novel,
            f"NEW table carrying a zero factor: {novel}" if novel else
            f"{sum(hits.values())} zero factors, all in "
            + ", ".join(f"{k}({v})" for k, v in sorted(hits.items())),
            f"{len(hits)} of {len(ZERO_FACTOR_TABLES)} known sentinel tables seen; "
            f"{checked} factor cells scanned")
