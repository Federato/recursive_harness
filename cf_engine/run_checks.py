"""Property's own steps around a rating: the outcome layer chunk 28 built (C28-21, moved here from `gl_engine`).

ISO files one rule language, so the interpreter is shared (`gl_engine.interp`). What a Property rating does *around*
the rules is not ERC's but Property's, and is decided here: refusing a known-older package (C28-19), refusing an input
whose absence prices an attached coverage at $0 (C28-17), dropping the answers ISO's request reader drops (OI-112),
not reading a submitted value a rule writes later (OI-125), and referring to company below a supplied minimum premium
(OI-113). Until chunk 28 C28-21 these lived in GL's interpreter behind Property-only flags; GL never ran them, but the
GL engine carried them.

The interpreter calls a book's `run_hooks` (`CFResolvedBook.run_hooks` is a `PropertyRunChecks`) at three points:

* `before(ip, data)`: before the rules run; may raise (the outcome is *refused* with the exception's `outcome_kind`)
* `after(ip, data, pending)`: after the rules ran, with what `before` returned; may raise
* `finish(ip, data)`: once the rating stands; may set the outcome (refer to company)

Moved, not changed: every step runs in the same order, on the same conditions, as it did inside the interpreter.
"""
from __future__ import annotations

from decimal import Decimal

from gl_engine.interp.tree import Node
from gl_engine.interp.values import InterpretError

__all__ = ["InvalidInput", "OlderPackage", "PropertyRunChecks"]


class InvalidInput(InterpretError):
    """A Property submission refused because an input it lacks would price a coverage at $0 (chunk 28 C28-17).

    ISO rates these silently at $0; refusing them is the user's decision (2026-10-05), stricter than ISO on purpose.
    """
    outcome_kind = "invalid input"


class OlderPackage(InterpretError):
    """A Property request refused because ISO is known to rate its date on a package the corpus lacks (chunk 28 C28-19).

    Ours would rate on an older package and be known not to be ISO's answer; refused by the user's decision (2026-10-06).
    Lifted by importing the package (C28-20).
    """
    outcome_kind = "older package"


class PropertyRunChecks:
    """The Property steps around one rating; stateless, one instance shared by every Property book."""

    #: The inputs whose absence ISO prices at $0 silently (C28-15, `CF-CHUNK28-SILENT-ZEROS.md`): refused only where
    #: the absence actually zeroes a coverage that is attached (the user's rule for the territory, 2026-10-05, and,
    #: by the same reasoning, for every check: New York and DC read no BCEG, so a missing BCEG there zeroes nothing).
    #: (record tag, field, state or None, the building coverage it zeroes, also needs CauseOfLoss in this set)
    SILENT_ZERO_INPUTS = (
        ("CommercialPropertyLocation", "BasicGroupIIRatingTerr", None, "BuildingBasicGroupIICoverage", None),
        ("CommercialPropertyStructure", "BCEG", None, "BuildingBasicGroupIICoverage", None),
        ("CommercialPropertyLocation", "BasicGroupIReductionCredit", "AZ", "BuildingBasicGroupICoverage", None),
        ("CommercialPropertyStructure", "Deductible", None, "BuildingBroadCoverage", {"Broad"}),
        ("CommercialPropertyStructure", "Deductible", None, "BuildingSpecialCoverage", {"Special"}),
    )

    # ------------------------------------------------------------------ the three hook points

    def before(self, ip, data: Node) -> list:
        """Before the rules: older package first (rates nothing), then the inputs ISO drops or a rule owns.

        The OI-125 look-ahead is itself a rating (`ip._lookahead`); it runs only the OI-112 drop, as before.
        Returns the silent-zero inputs found missing, for `after`.
        """
        lookahead = getattr(ip, "_lookahead", False)
        if not lookahead:
            self.refuse_older_package(ip)            # first: a known-older package rates nothing (C28-19)
        dropped = ip.book.ignored_inputs
        if dropped:
            self.ignore_inputs(ip, data, dropped)
        if lookahead:
            return []
        self.ignore_submitted_owned(ip, data)
        return self.missing_inputs(ip, data)

    def after(self, ip, data: Node, missing: list) -> None:
        if missing:
            self.refuse_silent_zeros(missing)

    def finish(self, ip, data: Node) -> None:
        self.refer_to_company(ip, data)

    # ------------------------------------------------------------------ C28-19

    def refuse_older_package(self, ip) -> None:
        """Refuse a date ISO is known to rate on a package the corpus lacks (C28-19)."""
        got = ip.book.older_than_iso()
        if got:
            ours, iso = got
            raise OlderPackage(
                f"{ip.book.juris} on {ip.book.asof}: ISO rates on {iso}; the corpus holds only {ours}, an older "
                f"package. Refused by decision until {iso} is imported (chunk 28 C28-19)", "C28-19", ours)

    # ------------------------------------------------------------------ C28-17

    def missing_inputs(self, ip, data: Node) -> list:
        """(check, record node) for every silent-zero input absent from the submission, before the rules run."""
        out, stack = [], [data]
        juris = getattr(ip.book, "juris", None)
        while stack:
            n = stack.pop()
            stack.extend(n.children)
            for chk in self.SILENT_ZERO_INPUTS:
                tag, field, state, _, causes = chk
                if n.tag != tag or (state and state != juris):
                    continue
                if tag == "CommercialPropertyStructure" and (n.first("CovType") is not None
                                                             and n.first("CovType").text not in (None, "", "Building")):
                    continue
                if causes and (n.first("CauseOfLoss") is None or n.first("CauseOfLoss").text not in causes):
                    continue
                f = n.first(field)
                if f is None or f.text in (None, ""):
                    out.append((chk, n))
        return out

    def refuse_silent_zeros(self, missing: list) -> None:
        """Refuse when a missing input's coverage is attached and priced $0 (C28-17)."""
        for (tag, field, _, cov, _), n in missing:
            structures = [n] if tag == "CommercialPropertyStructure" else \
                [s for t in n.kids("CommercialPropertyStructureTable") for s in t.kids("CommercialPropertyStructure")]
            for st in structures:
                for t in st.kids(f"CommercialPropertyStructure{cov}Table") or [st]:
                    for c in t.kids(f"CommercialPropertyStructure{cov}"):
                        on, prem = c.first("CoverageOnPolicyIndicator"), c.first("Premium")
                        if on is not None and str(on.text) in ("1", "1.0", "True", "true") \
                                and prem is not None and prem.text not in (None, "") and Decimal(prem.text) == 0:
                            raise InvalidInput(
                                f"{tag}.{field} is missing, and {cov} is attached and priced $0 because of it. ISO "
                                f"rates this silently at $0; refused by decision (chunk 28 C28-17)", "C28-17", tag)

    # ------------------------------------------------------------------ OI-113

    def refer_to_company(self, ip, data: Node) -> None:
        """Minimum premium is a company input (OI-113): refer when one is supplied and the total is below it."""
        for t in data.kids("CommercialPropertyTable"):
            for cp in t.kids("CommercialProperty"):
                mn, tot = cp.first("CompanyMinimumPremium"), cp.first("ErcCalculatedTotalPremium")
                if mn is None or mn.text in (None, "") or tot is None or tot.text in (None, ""):
                    continue
                if Decimal(tot.text) < Decimal(mn.text):
                    ip.outcome = {"status": "refer to company",
                                  "reasons": [{"kind": "minimum premium", "minimum": mn.text, "rated": tot.text}]}

    # ------------------------------------------------------------------ OI-112

    def ignore_inputs(self, ip, data: Node, dropped: frozenset) -> None:
        """Submitted values the book says ISO's request reader drops (OI-112): not read, noted in the trace."""
        stack = [data]
        while stack:
            n = stack.pop()
            stack.extend(n.children)
            if not n.children and n.parent is not None and (n.parent.tag, n.tag) in dropped \
                    and n.text not in (None, ""):
                ip.note("submitted-input-dropped",
                        f"{n.parent.tag}.{n.tag} = {n.text!r} submitted; ISO drops it on this edition", "OI-112")
                n.text = None

    # ------------------------------------------------------------------ OI-125

    def ignore_submitted_owned(self, ip, data: Node) -> None:
        """A submitted value for a field a rule writes later in the run is not read: as if never sent (OI-125).

        Chunk 26 K4d: `RatingType` submitted on the occupancies is counted before `OccupClass.SetRatingType` copies
        the building's; ISO counts 0. Measured on 1,692 stored requests ISO rated (`251_`, chunk 28 C28-08): 1,688
        submit at least one such value; hiding each one until its rule writes it fixes K4d, breaks nothing and moves
        no premium. A submitted value no rule writes in THIS run (an `IsNull`-guarded input, or a conditional write
        that does not fire, such as the 2020 editions' IRPM) is read as before, as ISO reads it: a static "some rule
        can write it" test was built first and moved 15 requests ISO agrees with, so it is not used.

        Exactly as measured: a look-ahead pass rates a copy of the request (trace off, the engine's own builtins,
        the interpreter's write recording on) and records which submitted values a rule writes; those are blanked
        before the real run. It roughly doubles a Property rating's time. A refusal in the look-ahead keeps the
        writes seen so far; the real run decides.
        """
        copy_of: dict[int, Node] = {}
        # Every copy stays referenced until the pass is read (OI-135, B-28). `copy_of` is keyed by `id()`, and a
        # rule's `Remove` detaches copies from the twin; a freed copy's id could be reused by a node the pass
        # creates later, so a write there blanked an unrelated submitted value. It depended on memory layout:
        # chunk23_rc3_Z6's EQLimitToUse came out None (ISO: 400000) after some requests and not others.
        keep: list[Node] = []

        def clone(n: Node, parent: Node | None) -> Node:
            c = Node(n.tag, parent, n.text)
            copy_of[id(c)] = n
            keep.append(c)
            c.children = [clone(k, c) for k in n.children]
            return c

        twin = clone(data, None)
        look = type(ip)(ip.book, rounding=ip.rounding_name, trace=False,
                        null_arithmetic=ip.null_arithmetic, guard_null_premium=ip.guard_null_premium,
                        strict_single_result=ip.strict_single_result, null_premium=ip.null_premium)
        look._writes = set()
        look._lookahead = True
        try:
            look.run(twin)
        except InterpretError:
            pass
        for cid in look._writes:
            orig = copy_of.get(cid)
            if orig is not None and not orig.children and orig.text not in (None, ""):
                ip.note("submitted-owned-ignored",
                        f"{orig.parent.tag if orig.parent else ''}.{orig.tag} = {orig.text!r} submitted; "
                        f"a rule writes it later, so it is not read", "OI-125")
                orig.text = None
