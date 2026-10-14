"""The referral register, wired to the engine.

Stage 3's second owed item. The register is 28 conditions and 13 decisions,
emitted as JSON by the analysis phase. Loading it was the easy half; **the
conditions are prose written for a human**, and turning each into something the
engine can detect is the work.

**Every entry gets an explicit disposition. There is no silent middle.**

| | |
|---|---|
| `NOT_REFERRAL` | decided **not** to be a referral. It must never raise, and saying so is a behaviour, not an omission |
| `CONFIG` | a setting rather than a detection — it is answered once, when the engine is configured, not per rating |
| `DETECTED` | a detector runs on every rating in `underwriting` mode |
| `PENDING` | genuinely not built, **named individually with what it would take** |

A register that reports "28 conditions loaded" while checking one reads as
coverage it does not have. `Kernel.coverage()` returns the four counts and
`Kernel.unenforced` names every `PENDING` entry, so the gap is always visible
from the outside.

**Detectors observe the rating, they do not re-derive it.** Each reads the rated
tree, the trace, or the resolved book — never a second implementation of a
rating rule, because a detector that recomputes a premium is a second thing to
be wrong.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ..interp import tree

REGISTER_PATH = (Path(__file__).resolve().parent.parent.parent
                 / "scripts" / "erc" / "out" / "referral_register.json")

NOT_REFERRAL = "NOT_REFERRAL"
CONFIG = "CONFIG"
DETECTED = "DETECTED"
PENDING = "PENDING"

#: Decided **not** to be referrals. Recorded here so the engine's silence on
#: them is a deliberate behaviour rather than an unbuilt detector.
#:
#: R24 is a special case: it IS enforced, but by stage 1 refusing the date
#: outright, which is a load error and not a referral. The register's own text
#: says *fail loudly, never fall back*.
NOT_REFERRALS = {
    "R21": "a 0 final relativity while the flag is Yes -- decided 2026-08-12 "
           "NOT a referral",
    "R24": "an effective date below the corpus floor -- enforced by stage 1 as "
           "a hard ResolutionError, which is louder than a referral",
    "R27": "conditional-exclusion prorating -- ERC implements the full-term "
           "treatment and the manual permits it",
    "R28": "Puerto Rico Schedule & Experience is confirmed adopted; only "
           "composite rating is open, and that is not rated here",
}

#: Answered when the engine is configured, not per rating.
CONFIGS = {
    "R18": "an LCM of exactly 1 is a company input, not a rate. The engine "
           "takes ISO's filed content as filed; supplying a company LCM is a "
           "phase 4 concern (company deviations)",
}


@dataclass(frozen=True)
class Finding:
    """One detector firing on one rating."""

    code: str
    where: str
    detail: str


# --------------------------------------------------------------- detectors
#
# Each returns a list of Finding. They are deliberately small and each names
# the evidence it reads.

def _rows(rating, path):
    return tree.select(path, rating.tree)


def _num(text):
    try:
        return Decimal(str(text))
    except (InvalidOperation, TypeError, ValueError):
        return None


def d_refer_sentinel(rating) -> list:
    """R03 -- ISO's own refer marker arriving in a rated value.

    `Refer To Co.` x49 and `Refer to Company` x1 live inside
    `GL_CW_20270401_V01`. If one reaches the output tree, ISO has declined to
    price this and the engine must not hand back the text as if it were data.
    """
    out = []

    def walk(n):
        t = n.text
        if t and "refer" in str(t).lower():
            out.append(Finding("R03", n.path, f"{n.tag} = {t!r}"))
        for c in n.children:
            walk(c)

    walk(rating.tree)
    return out


def d_negative_factor(rating) -> list:
    """R16 -- `FinalILF = CSLILF - DeductibleFactor` has no floor.

    Two guards are all that stand between this and a negative premium. A
    negative factor or premium anywhere is not a price, so it is caught here
    regardless of which coverage produced it.
    """
    out = []

    def walk(n):
        if n.text is not None and (
                n.tag.endswith("ILF") or n.tag.endswith("Factor")
                or n.tag == "Premium" or n.tag.endswith("Premium")):
            v = _num(n.text)
            if v is not None and v < 0:
                out.append(Finding("R16", n.path, f"{n.tag} = {v}"))
        for c in n.children:
            walk(c)

    walk(rating.tree)
    return out


def d_territory_unmatched(rating) -> list:
    """R22 -- county or place unmatched in CA, FL, NY or TX (E8).

    Those four resolve territory by county or place, so an unmatched key is a
    missing submission field rather than a zero. **Never a fuzzy match** --
    that was decided by E8.
    """
    if rating.juris not in ("CA", "FL", "NY", "TX"):
        return []
    return [Finding("R22", "lookup", t.detail)
            for t in rating.trace
            if t.kind == "lookup-miss" and "Territory" in t.detail]


def d_size_of_risk_without_costs(rating) -> list:
    """R10/R11 -- size-of-risk applies but the apparatus is empty.

    Two register entries with one observable shape: the submission asks for
    size-of-risk and the relativity comes back null or zero, which prices the
    whole coverage at nothing. R11 is the same failure arriving through the
    2027 countrywide edition, which strips the assignment, minimum and maximum
    tables.
    """
    out = []
    for risk in _rows(rating, "GeneralLiabilityTable/GeneralLiability"):
        if (tree.read("SizeOfRiskRatingApplies", risk) or "").strip() != "Yes":
            continue
        for cov in ("PremOps", "ProdsCompldOps"):
            for cls in tree.select(
                    "GeneralLiabilityLocationTable/GeneralLiabilityLocation/"
                    "GeneralLiabilityClassificationTable/"
                    "GeneralLiabilityClassification", risk):
                rel = tree.read(f"GeneralLiabilityClassification{cov}Coverage/"
                                f"{cov}SizeOfRiskFinalRelativity", cls)
                v = _num(rel)
                if rel is None or (v is not None and v == 0):
                    code = ("R11" if rating.book.resolution.parent
                            and rating.book.resolution.parent.pkg_id
                            == "GL_CW_20270401_V01" else "R10")
                    out.append(Finding(
                        code, cls.path,
                        f"{cov} size-of-risk applies but the relativity is "
                        f"{rel!r}"))
    return out


def d_zero_rating_factor(rating) -> list:
    """R14/R19/R20 -- a zero where a factor was required.

    N13 catalogued eight meanings of zero and only one is the number nought.
    These three entries are the ones where a zero factor multiplies a real
    premium: the ten unguarded liquor deductible cells (R14), and the drone
    cells that are refer-to-company or `Unknown`/`Not Applicable` markers
    (R19/R20, decided 2026-08-12 to refer).

    **Scoped to those cells (OI-131, B-10).** Matching any `Liquor` or drone
    table referred every liquor risk on `DedFactorLiquor['No Deductible']`,
    the one legitimate zero, and a Company class's `LiquorELP` (R29's, by
    ISO's own message); and every drone policy on `UnmannedAircraftMinPremium`,
    a one-row $0 floor, not a rating cell.
    """
    out = []
    for t in rating.trace:
        if t.kind not in ("lookup", "lookup-banded"):
            continue
        if "-> Decimal('0')" not in t.detail and "-> '0'" not in t.detail:
            continue
        table = t.detail.split("[", 1)[0]
        if table == "DedFactorLiquor":
            if "'No Deductible'" not in t.detail:
                out.append(Finding("R14", "lookup", t.detail))
        elif table.startswith("UnmannedAircraft") and "MinPremium" not in table:
            out.append(Finding("R19", "lookup", t.detail))
    return out


def d_elp_override_needed(rating) -> list:
    """R29 -- OI-95: ISO's own filed rules already ask for the input we never
    supply, and nothing acts on the answer.

    A class filed `(a)` -- refer to company -- falls through to an Estimated
    Loss Potential. Where ISO publishes one (`Industry`), the countrywide rules
    already resolve it correctly: confirmed against OK's own STC fixture,
    class `50017`, `FinalProdsCompldOpsELP` lands on `0.82` exactly as ISO's
    own certified output does, with no code here doing anything ELP-specific
    -- the generic interpreter running ISO's filed `Lookup` is enough.

    Where no ELP is published (`Company`, ISO's `RTC`), ISO's own filed rules
    call `MessageHelper.AddErrorMessage` with *"Must enter Estimated Loss
    Potential Override for ..."* -- the same generic mechanism every one of
    the corpus's 4,347 validation-message sites uses. **The message already
    exists in `rating.messages`; nothing here re-derives the classification
    from a rate table.** What was missing is that nothing consulted it: the
    rating completes anyway and prices that classification at the `(a)`
    table's filed `0` -- the free-policy failure mode
    `docs/rating-engine/13-LOSS-COSTS-AND-ELP.md` S13.4 names.

    Deliberately narrow, matching this one message family rather than all
    4,347 possible `AddErrorMessage` sites -- treating every filed message as
    referral-worthy is a measurement this project has not done, and would be
    the same blunt-instrument mistake OI-88's `FirstNonNull` fix was rejected
    for.
    """
    text = "Must enter Estimated Loss Potential Override"
    return [Finding("R29", "messages", m) for m in rating.messages if text in m]


def d_split_base_table(rating) -> list:
    """R13 -- a base loss-cost table present and EMPTY where rows are sharded.

    CA, NJ, NY and OH file the rows under per-territory names. Falling through
    to the parent is wrong (N3), and the visible symptom in a rating is a
    loss-cost lookup that misses in the state and then misses again countrywide.

    A miss on a table that a later lookup resolved does not count (OI-131, B-10):
    every drone loss cost records one exact-key miss before its weight band
    resolves (`UnmannedAircraftLimitedLiabilityBIPDLossCost` -> 154.26), which
    referred every drone policy.
    """
    resolved = {t.detail.split("[", 1)[0] for t in rating.trace
                if t.kind in ("lookup", "lookup-banded") and "LossCost" in t.detail}
    misses = [t for t in rating.trace
              if t.kind == "lookup-miss" and "LossCost" in t.detail
              and t.detail.split("[", 1)[0] not in resolved]
    if len(misses) < 2:
        return []
    return [Finding("R13", "lookup",
                    f"{len(misses)} loss-cost lookups missed; the base table "
                    f"may be empty while sharded rows carry the data")]


def not_offered(rating) -> dict:
    """`{class code: [coverage, ...]}` where ISO's ELP text for the class reads "Not Applicable".

    GATE-336: `ELPText = "Not Applicable"` means **the coverage is not offered for this class** -- NOT_OFFERED,
    never a silent 0 (OI-130 (b), B-07 part 3e). The rules still price it at $0 (or the $1 floor in 2027);
    this names why, from ISO's own lookup, so the $0 is labelled rather than mistaken for a failure.
    """
    out: dict = {}
    for t in rating.trace or ():
        d = str(getattr(t, "detail", ""))
        if t.kind == "lookup" and "ELPText[" in d and d.endswith("-> 'Not Applicable'"):
            cov = d.split("ELPText[", 1)[0]
            keys = d.split("keys=", 1)[-1].split("]", 1)[0]
            code = keys.strip("[]").split(",")[-1].strip(" '")
            out.setdefault(code, set()).add(cov)
    return {k: sorted(v) for k, v in out.items()}


def d_terrorism_endorsement_factor(rating) -> list:
    """R31 (OI-130, B-07 part 3f, the user's decision 2026-10-13: refer, not refuse).

    Terrorism bought, an endorsement on the policy carrying a manual premium, and no
    `CertifiedActsofTerrorismExposureClassFactor`: the terrorism charge on those endorsements prices $0 (pre-2027)
    or the $1 floor (2027) with no message (offline 2026-10-13: OK, $4 -> $0 / $1).
    """
    out = []
    for risk in tree.select("GeneralLiabilityTable/GeneralLiability", rating.tree):
        if str(tree.read("TerrorismCoverage", risk) or "").strip() != "Yes":
            continue
        te = risk.first("GeneralLiabilityTerrorismEndorsementCoverage")
        if te is None or str(getattr(te.first("CoverageOnPolicyIndicator"), "text", "")).strip() not in ("1", "1.0"):
            continue
        fac = te.first("CertifiedActsofTerrorismExposureClassFactor")
        if fac is not None and str(fac.text or "").strip() not in ("", "0", "0.0"):
            continue
        priced = False
        stack = [c for c in risk.children if c is not te]
        while stack and not priced:
            n = stack.pop()
            mp = n.first("ManualPremium") if n.children else None
            try:
                priced = mp is not None and Decimal(str(mp.text)) > 0
            except (InvalidOperation, ValueError, TypeError):
                pass
            stack.extend(n.children)
        if priced:
            out.append(Finding("R31", "GeneralLiabilityTerrorismEndorsementCoverage",
                               "terrorism is bought and an endorsement carries a premium, but no exposure-class "
                               "factor (CertifiedActsofTerrorismExposureClassFactor) was given: the terrorism charge "
                               "on endorsements prices $0 or the $1 minimum"))
    return out


#: An ISO message that asks for an input (the 17 ISO-messaged OI-130 routes all do), as against a form message.
_ASKS_FOR_INPUT = re.compile(r"\bmust enter\b|\bmust be entered\b|\bplease enter\b", re.I)


def d_silent_zero(rating) -> list:
    """R30 (OI-130 / B-07 part 5, the user's decision 2026-10-13): a safety net under ISO's quiet failures.

    A coverage ISO's own rules put on the policy (`CoverageOnPolicyIndicator = 1`) whose premium came out $0 or
    the $1 minimum. Every silent route the OI-130 reproduction found ends here -- a lookup that matched no row,
    an unanswered question, an off-list value -- and ISO prices them the same way, so no comparison catches
    them. A warning on every rating (`Rating.notices`), a referral in underwriting mode; never a refusal,
    because some $0s are right (OK files a Products loss cost of 0; a tiny exposure rounds to 0). Top-up
    records (`...PremiumToReachMin...`) are skipped: $0 there means the minimum was already met.
    """
    out = []
    # ISO already asked for an input ("Must enter ...", "... must be entered", "Please enter ..."): the $0 is
    # messaged, not silent, and stays as ISO prices it (B-07 part 4). ISO's messages do not name the coverage, so
    # the whole rating is quiet -- a second, unrelated $0 on the same policy goes unflagged here. ISO's form
    # messages ("... cannot be attached") ask for nothing and do not count.
    if any(_ASKS_FOR_INPUT.search(str(m)) for m in rating.messages or ()):
        return out
    labelled = not_offered(rating)

    no_terror = {id(r) for r in tree.select("GeneralLiabilityTable/GeneralLiability", rating.tree)
                 if str(tree.read("TerrorismCoverage", r) or "").strip() != "Yes"}

    def is_labelled(node) -> bool:
        # the terrorism charge on endorsements is $0 (pre-2027) or the $1 floor (2027) whenever no endorsement
        # carries a premium -- by design; its real failure, a missing exposure-class factor, is R31's
        if node.tag == "GeneralLiabilityTerrorismEndorsementCoverage":
            return True
        # terrorism not bought: its coverages sit on the policy at $0 by design (measured: 11 of the 15 clean
        # requests R30 first flagged, 2026-10-13)
        if "Terrorism" in node.tag:
            p = node.parent
            while p is not None and p.tag != "GeneralLiability":
                p = p.parent
            if p is not None and id(p) in no_terror:
                return True
        cc = node.first("ClassCode")
        covs = labelled.get(str(cc.text).strip(), ()) if cc is not None else ()
        return any(cov and cov in node.tag for cov in covs)

    def walk(node, path):
        for c in node.children:
            here = f"{path}/{c.tag}"
            ind = c.first("CoverageOnPolicyIndicator")
            prem = c.first("Premium")
            if (ind is not None and str(ind.text).strip() in ("1", "1.0") and prem is not None
                    and "PremiumToReachMin" not in c.tag and not is_labelled(c)):
                try:
                    v = Decimal(str(prem.text))
                except (InvalidOperation, ValueError, TypeError):
                    v = None
                # a $1 from a real filed rate is a small premium, not a floor over a failure (B-35, 2026-10-14):
                # LoED's Prem/Ops host, FinalRate 0.0001 on $5M, is ISO's own $1. Every silent route rates at 0.
                rate = _num(c.first("FinalRate").text) if c.first("FinalRate") is not None else None
                if v == Decimal(1) and rate is not None and rate > 0:
                    v = None
                if v is not None and v in (Decimal(0), Decimal(1)):
                    out.append(Finding("R30", here.rsplit("/", 1)[-1],
                                       f"on the policy but priced ${v:.0f} with no refusal: an unanswered question, "
                                       f"an answer off ISO's list or a lookup that matched nothing prices this way "
                                       f"silently (ISO too); check the request"))
            walk(c, here)

    walk(rating.tree, "")
    return out


#: code -> detector. Everything not here and not classified above is PENDING.
#: R29 is not one of the 28 entries the analysis phase produced (`REGISTER_PATH`,
#: as-of 2026-08-12) -- it is OI-95, found afterward. `Kernel.coverage()` only
#: counts codes present in that frozen register, so R29 runs and raises but
#: does not appear in its tallies -- the same way OI-94's `_refuse_null_loss_cost`
#: sits outside this dict entirely. `disposition()` still reports it DETECTED.
DETECTORS = {
    "R03": d_refer_sentinel,
    "R16": d_negative_factor,
    "R22": d_territory_unmatched,
    "R10": d_size_of_risk_without_costs,
    "R14": d_zero_rating_factor,
    "R13": d_split_base_table,
    "R29": d_elp_override_needed,
    "R30": d_silent_zero,
    "R31": d_terrorism_endorsement_factor,
}

#: Detectors that report under more than one code.
ALSO_COVERED = {"R11": "R10", "R19": "R14", "R20": "R14"}


def load_register(path: Path | None = None) -> list:
    p = path or REGISTER_PATH
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8")).get("entries", [])


def disposition(code: str) -> str:
    if code in NOT_REFERRALS:
        return NOT_REFERRAL
    if code in CONFIGS:
        return CONFIG
    if code in DETECTORS or code in ALSO_COVERED:
        return DETECTED
    return PENDING


def run_detectors(rating) -> list:
    """Every detector, in register order. Findings are de-duplicated by code."""
    found = []
    for code, fn in DETECTORS.items():
        found.extend(fn(rating))
    return found
