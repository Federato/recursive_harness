"""The kernel's checks around ISO's rules, as plain functions. **OI-139.**

A rating is ISO's rules run on a tree, with checks the kernel makes before and after them: a missing rating input or
an answer off ISO's list refuses before the rules (OI-134, OI-130); a Loss of Electronic Data limit in a refer band
is named when the run stops on it (OI-129); a null loss cost refuses after (OI-94); the premium and its parts are
read out of the rated tree; our own notices are added. They were `Kernel` methods; they are functions here so a
caller that runs ISO's rules some other way -- the sister project ISOComputeGraph's compiled graph (its C-42) --
makes the same checks without holding a `Kernel`. `Kernel` calls them in place; **nothing they do changed**.

The OI-134 switch stays the kernel's (`kernel.RATING_INPUTS_CHECK`, `ERC_RATING_INPUTS`): the kernel reads it
before calling `refuse_missing_rating_inputs`, and a caller without a kernel reads the same switch.
"""
from __future__ import annotations

from decimal import Decimal

from ..errors import EngineError
from ..interp import Node
from ..interp import tree
from . import referrals

#: Paths the kernel reads a result out of, relative to a `GeneralLiability`.
TOTAL = "Premium"
TOTAL_CHECK = "ErcCalculatedTotalPremium"

#: The Loss of Electronic Data hosts whose `SetILF` copies `ILFOverride` in a refer band.
LOED_HOSTS = ("GeneralLiabilityClassificationLossOfElectronicDataPremOpsCoverage",
              "GeneralLiabilityClassificationLossOfElectronicDataProdsCompldOpsCoverage")


class RatingError(EngineError):
    """The submission could not be rated."""


# --------------------------------------------- OI-134, a missing rating input

def refuse_missing_rating_inputs(data: Node, book, schemas: dict | None = None) -> None:
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
    cannot read reports nothing rather than guess. `schemas` keeps one `Schema` per resolved package pair
    across calls (the kernel's own dict); without it the schema is built for this call.
    """
    from ..schema import Schema
    from ..schema.validate import (invalid_values, list_inputs, missing_required, stop_gap_conflict,
                                   stop_gap_unrated_limits)
    key = tuple(getattr(x, "pkg_id", None) for x in (book.resolution.state, book.resolution.parent))
    schema = schemas.get(key) if schemas is not None else None
    if schema is None:
        schema = Schema.for_book(book)
        if schemas is not None:
            schemas[key] = schema
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

def ilf_override_needed(data: Node, exc: Exception) -> "RatingError | None":
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
            if child.tag in LOED_HOSTS:
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

def refuse_null_loss_cost(result) -> None:
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

def collect(result) -> None:
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


def add_notices(result) -> None:
    """Our own warnings on a rated result (OI-130, B-07): coverages ISO's table marks "Not Applicable" for the class,
    and coverages that priced $0 or $1 silently (R30), with the terrorism endorsement factor check."""
    for code, covs in referrals.not_offered(result).items():
        result.notices.append(f"Not offered: {', '.join(covs)} for class {code} (ISO's table reads "
                              f"\"Not Applicable\"); it prices $0 or the $1 minimum by design")
    for f in referrals.d_silent_zero(result) + referrals.d_terrorism_endorsement_factor(result):
        result.notices.append(f"{f.code} {f.where}: {f.detail}")
