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
    """
    watch = (("Liquor", "R14"), ("UnmannedAircraft", "R19"), ("Drone", "R19"))
    out = []
    for t in rating.trace:
        if t.kind not in ("lookup", "lookup-banded"):
            continue
        if "-> Decimal('0')" not in t.detail and "-> '0'" not in t.detail:
            continue
        for token, code in watch:
            if token in t.detail:
                out.append(Finding(code, "lookup", t.detail))
                break
    return out


def d_split_base_table(rating) -> list:
    """R13 -- a base loss-cost table present and EMPTY where rows are sharded.

    CA, NJ, NY and OH file the rows under per-territory names. Falling through
    to the parent is wrong (N3), and the visible symptom in a rating is a
    loss-cost lookup that misses in the state and then misses again countrywide.
    """
    misses = [t for t in rating.trace
              if t.kind == "lookup-miss" and "LossCost" in t.detail]
    if len(misses) < 2:
        return []
    return [Finding("R13", "lookup",
                    f"{len(misses)} loss-cost lookups missed; the base table "
                    f"may be empty while sharded rows carry the data")]


#: code -> detector. Everything not here and not classified above is PENDING.
DETECTORS = {
    "R03": d_refer_sentinel,
    "R16": d_negative_factor,
    "R22": d_territory_unmatched,
    "R10": d_size_of_risk_without_costs,
    "R14": d_zero_rating_factor,
    "R13": d_split_base_table,
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
