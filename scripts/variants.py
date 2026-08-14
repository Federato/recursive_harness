"""What may be varied, what each option legally holds, and how to apply it.

**One definition, read by three callers**: `scripts/breadth.py` (the CLI variant
sweep), `ui/` (the dropdowns) and `tests/verify_tester.py`. A second list of
legal values maintained next to the first would drift, and the drift would look
like a rating defect.

Nothing here renders anything and nothing here imports `ui`. The dependency runs
one way: `ui` -> `variants` -> `gl_engine`. **`gl_engine` imports neither.**

### The rule this module exists to enforce

**Options come from ISO's declaration, per jurisdiction.** Not from the sample
submission, not from a hardcoded list, and not from what happened to work once.
`Control.options(declared)` reads the domain table; `Declared.require` refuses a
value that is not in it. A dropdown that offers an illegal value is a bug here,
not a finding about the engine.

### Three things the declaration says that a UI has to respect

* **A legal set is per state.** `Claims Made` is legal in **50 of 51** -- NY
  declares `Occurrence` as the only coverage form. **20 states declare exactly
  one prem/ops territory**, so a two-location test is not merely unusual there,
  it is undeclarable. Such a state is `NOT APPLICABLE`, which is a **third
  outcome** and must never be counted as a disagreement.
* **Some legal sets depend on other answers.** The combined BI/PD deductible is
  keyed on the BI/PD pair: with either one set, the only legal combined value is
  `No Deductible`. The aggregate limits are keyed on the occurrence limit.
  Applying one control therefore has to re-derive the others.
* **`Type` is a form control, not a data type** (`gl_engine/schema/fields.py`).
  `YearInClaimsMade` is declared `TEXT` and ISO rejects a string for it --
  OI-90, found by spending a live call. `Control.cast` carries the data type so
  that is asked once, here.
"""
from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass, field as dc_field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "Engine_Payloads"

from gl_engine import EditionResolver, ResolvedBook          # noqa: E402
from gl_engine.schema import Schema                          # noqa: E402

#: The as-of date the stored base submissions carry.
DEFAULT_ASOF = "20260801"

#: `Subline` has 8 to 10 declared values, and **the stored base submissions are
#: shaped for the premises/operations family only** -- a Liquor risk needs
#: Liquor classifications, a Liquor coverage form and its own class-code domain.
#: These three are buildable by editing the base; the other seven need a base
#: submission of their own, which is follow-on work and is shown in the UI as
#: exactly that rather than left out silently.
SUBLINES_FROM_THIS_BASE = (
    "Premises/Operations and Products/Completed Operations",
    "Premises/Operations",
    "Products/Completed Operations",
)


class VariantError(RuntimeError):
    """A value outside the declaration, or a shape this base cannot express."""


# --------------------------------------------------------------- declaration

class Declared:
    """ISO's declared legal values for one jurisdiction. Invents nothing."""

    _resolver = None

    def __init__(self, juris: str, asof: str = DEFAULT_ASOF):
        if Declared._resolver is None:
            # One corpus scan per process: it costs about four seconds and
            # every jurisdiction after the first costs about eighty
            # milliseconds. A page that rebuilt it per request would be unusable.
            Declared._resolver = EditionResolver()
        self.juris = juris
        self.asof = asof
        self.book = ResolvedBook(Declared._resolver.resolve(juris, asof))
        self.schema = Schema.for_book(self.book)

    @classmethod
    def resolver(cls):
        if cls._resolver is None:
            cls._resolver = EditionResolver()
        return cls._resolver

    @classmethod
    def jurisdictions(cls) -> tuple[str, ...]:
        """The jurisdictions that have a stored base submission."""
        if not SAMPLES.is_dir():
            return ()
        return tuple(sorted(p.name for p in SAMPLES.iterdir()
                            if p.is_dir() and (p / "submission.json").exists()))

    def base(self) -> dict:
        p = SAMPLES / self.juris / "submission.json"
        if not p.exists():
            raise VariantError(f"no base submission for {self.juris}")
        return json.loads(p.read_text(encoding="utf-8"))

    # ------------------------------------------------------------- values

    def values(self, table: str, col: str) -> tuple[str, ...]:
        vals, _exact = self.schema.resolved_values(table, col)
        return vals

    def require(self, table: str, col: str, value):
        legal = self.values(table, col)
        if legal and str(value) not in legal:
            raise VariantError(
                f"{table}.{col}={value!r} is not declared legal in "
                f"{self.juris}; {len(legal)} legal: {list(legal)[:6]}")
        return value

    def dependent(self, table: str, col: str, deps: dict) -> tuple[str, ...]:
        """The legal values once the dependency columns are pinned.

        `deps` maps a dependency column name to its value. **Every dependency
        column the table declares and `deps` names is matched**, which is what
        the combined deductible needs -- it is keyed on a pair, and matching
        only the first would return a set that is legal for the BI value and
        wrong for the PD one.

        `Schema.resolved_values` resolves ISO's declared `RelatedXPath` against
        a rated tree. Here there is no tree: the submission is still being
        built, so the domain table is filtered directly.
        """
        t = self.schema.domain_table(table, col)
        cols = self.schema.dependency_columns(table, col)
        if t is None or not cols:
            return self.values(table, col)
        pinned = [(t.col(c), str(deps[c])) for c in cols
                  if c in deps and c in t.header]
        if not pinned:
            return self.values(table, col)
        vi = t.col("DataValue")
        si = t.col("StateCode") if "StateCode" in t.header else None
        out, seen = [], set()
        for row in t.rows:
            if si is not None and row[si] not in (self.juris, "CW"):
                continue
            if any(str(row[i]) != want for i, want in pinned):
                continue
            v = str(row[vi])
            if v not in seen:
                seen.add(v)
                out.append(v)
        return tuple(out)

    def description(self, code: str) -> str:
        """ISO's own description for a class code.

        `ClassDescription` is rating-required and carries no domain of its own,
        so a code change must take the description from ISO's table -- a code
        and a description that disagree is a submission no underwriter sends.
        """
        t = self.book.table("DomainClassDescriptionByClassCodes", "Domain")
        ci, vi = t.col("ClassCodeForClassDescription"), t.col("DataValue")
        for row in t.rows:
            if str(row[ci]) == str(code):
                return str(row[vi])
        raise VariantError(f"class code {code} has no declared description "
                           f"in {self.juris}")

    def codes_for_basis(self, basis: str, which: str = "PremOps") -> tuple[str, ...]:
        col = f"{which}PremiumBasis"
        t = self.schema.domain_table("GeneralLiabilityClassification", col)
        cols = self.schema.dependency_columns("GeneralLiabilityClassification", col)
        if t is None or not cols:
            return ()
        di, vi = t.col(cols[0]), t.col("DataValue")
        si = t.col("StateCode") if "StateCode" in t.header else None
        out, seen = [], set()
        for row in t.rows:
            if si is not None and row[si] not in (self.juris, "CW"):
                continue
            if str(row[vi]) != basis:
                continue
            code = str(row[di])
            if code not in seen:
                seen.add(code)
                out.append(code)
        return tuple(out)

    def all_class_codes(self, which: str = "PremOps") -> tuple[str, ...]:
        """Every class code ISO declares, from the basis table's key column.

        **`ClassCode` is declared `TEXT` with no domain of its own**, so there
        is no list to read directly -- the enumerable list is the dependency
        column of `PremiumBasis{which}ClassCode`, which names a code per row.
        Asking the field for its legal values returns nothing, which is correct
        and useless; this is where the codes actually are.
        """
        t = self.schema.domain_table(CLS, f"{which}PremiumBasis")
        cols = self.schema.dependency_columns(CLS, f"{which}PremiumBasis")
        if t is None or not cols:
            return ()
        di = t.col(cols[0])
        si = t.col("StateCode") if "StateCode" in t.header else None
        out, seen = [], set()
        for row in t.rows:
            if si is not None and row[si] not in (self.juris, "CW"):
                continue
            code = str(row[di])
            if code not in seen:
                seen.add(code)
                out.append(code)
        return tuple(out)

    def basis_for(self, code: str, which: str = "PremOps") -> str:
        vals = self.dependent("GeneralLiabilityClassification",
                              f"{which}PremiumBasis", {"ClassCode": code})
        if not vals:
            raise VariantError(f"no {which} premium basis declared for class "
                               f"{code} in {self.juris}")
        return vals[0]

    def territories(self) -> tuple[str, ...]:
        return self.values("GeneralLiabilityLocation",
                           "PremisesOperationsTerritory")

    def terrorism_place(self) -> tuple[str, str] | None:
        """`(field, value)` for locating a risk, or None if neither is declared.

        Measured over all 51 as of 2026-08-01: **15 declare an explicit
        `TerrorismTerritory`, 16 declare a `ZipCode` domain, and 20 declare
        neither.** The four/eleven split recorded in E8/R22 was measured a
        different way -- by which domain table the field names -- and the two
        counts have not been reconciled (OI-91). Returning `None` is therefore
        an honest *"this jurisdiction tells us nothing to send"*, not an
        assertion that terrorism cannot be rated there.
        """
        tt = self.values("GeneralLiabilityLocation", "TerrorismTerritory")
        if tt:
            return ("TerrorismTerritory", tt[0])
        for v in self.values("GeneralLiabilityLocation", "ZipCode"):
            if v.isdigit():
                return ("ZipCode", v)
        return None


# ------------------------------------------------------------------ controls

@dataclass(frozen=True)
class Control:
    """One thing a person may vary, and everything a UI needs to offer it."""

    id: str
    label: str
    group: str
    exercises: str
    kind: str = "select"              # select | number
    table: str = ""
    column: str = ""
    #: Control ids whose values key this one's domain, mapped to the dependency
    #: COLUMN name ISO's domain table declares.
    keyed_by: dict = dc_field(default_factory=dict)
    #: Python type the request must carry. OI-90: the form control type is not
    #: this, and guessing cost a live call.
    cast: str = "str"
    unit_from: str = ""               # a control naming this one's units
    note: str = ""
    #: Set when the options are not a domain of this field's own. `ClassCode`
    #: is declared `TEXT` with no domain; its enumerable list is the key column
    #: of the premium-basis table. Naming that here keeps the exception in one
    #: place instead of spreading a special case through the callers.
    derive: str = ""

    def options(self, d: Declared, config: dict | None = None) -> tuple[str, ...]:
        """Legal values in this jurisdiction, given the answers so far."""
        if self.derive == "class_codes":
            basis = (config or {}).get("premium_basis")
            if basis:
                return d.codes_for_basis(str(basis))
            return d.all_class_codes()
        if not self.column:
            return ()
        if self.keyed_by and config:
            deps = {}
            for cid, dep_col in self.keyed_by.items():
                v = config.get(cid)
                if v not in (None, ""):
                    deps[dep_col] = v
            if deps:
                return d.dependent(self.table, self.column, deps)
        return d.values(self.table, self.column)


GL = "GeneralLiability"
LOC = "GeneralLiabilityLocation"
CLS = "GeneralLiabilityClassification"

CONTROLS: tuple[Control, ...] = (
    # ---------------------------------------------------- 1. deductibles (6)
    Control("premops_bi_deductible", "Prem/Ops BI deductible", "Deductibles",
            "the bodily-injury deductible credit chain, prem/ops",
            table=GL, column="PremOpsBIDeductible"),
    Control("premops_pd_deductible", "Prem/Ops PD deductible", "Deductibles",
            "the property-damage deductible credit chain, prem/ops",
            table=GL, column="PremOpsPDDeductible"),
    Control("premops_bipd_deductible", "Prem/Ops combined BI/PD", "Deductibles",
            "the combined deductible, which ISO declares legal only while BI "
            "and PD are both No Deductible",
            table=GL, column="PremOpsBIPDDeductible",
            keyed_by={"premops_bi_deductible": "PremOpsBIDeductible",
                      "premops_pd_deductible": "PremOpsPDDeductible"},
            note="Keyed on the BI/PD pair across 961 declared dependency keys."),
    Control("prods_bi_deductible", "Products BI deductible", "Deductibles",
            "the deductible chain on the products side, a separate table family",
            table=GL, column="ProdsCompldOpsBIDeductible"),
    Control("prods_pd_deductible", "Products PD deductible", "Deductibles",
            "the products-side PD deductible",
            table=GL, column="ProdsCompldOpsPDDeductible"),
    Control("prods_bipd_deductible", "Products combined BI/PD", "Deductibles",
            "the products-side combined deductible, same exclusion as prem/ops",
            table=GL, column="ProdsCompldOpsBIPDDeductible",
            keyed_by={"prods_bi_deductible": "ProdsCompldOpsBIDeductible",
                      "prods_pd_deductible": "ProdsCompldOpsPDDeductible"}),

    # --------------------------------------------------------- 2. limits (1)
    Control("occurrence_limit", "Each-occurrence limit", "Limits",
            "the increased-limit factor table, in both directions from the "
            "1,000,000 default; both aggregates are re-derived from ISO's "
            "dependent domain so the pair is always legal",
            table=GL, column="PremOpsProdsEachOccurrenceLimit",
            note="Setting this also sets GeneralAggregateLimit and "
                 "ProdsCompldOpsAggregateLimit to values ISO declares legal "
                 "with it."),

    # ------------------------------------------------- 3-4. classification (3)
    Control("premium_basis", "Premium basis", "Classification",
            "the exposure divisor and its rounding; every basis other than "
            "Gross Sales is untested territory",
            table=CLS, column="PremOpsPremiumBasis"),
    Control("class_code", "Class code", "Classification",
            "the loss cost, the ELP and the increased-limit table assignment "
            "-- the deepest single input in the submission",
            table=CLS, column="ClassCode", derive="class_codes",
            note="`ClassCode` is declared TEXT with no domain, so the options "
                 "are the class codes ISO declares for the chosen basis -- "
                 "narrowed as soon as a basis is picked. The description comes "
                 "from ISO's own table, never from the previous class."),
    Control("exposure", "Exposure amount", "Classification",
            "the size-of-risk bands and the minimum-premium comparison",
            kind="number", cast="float",
            unit_from="premium_basis"),

    # -------------------------------------------------- 5. coverage form (2)
    Control("coverage_form", "Coverage form", "Coverage form",
            "the claims-made form, which no stored sample uses",
            table=GL, column="PremOpsProdsCoverageForm",
            note="Declared legal in 50 of 51 jurisdictions; NY declares "
                 "Occurrence only."),
    Control("claims_made_year", "Year in claims-made", "Coverage form",
            "the claims-made maturity step, a different row of the same table",
            kind="number", cast="int",
            note="An Int32 -- OI-90. Applies only when the form is Claims Made."),

    # -------------------------------------------------------- 6. subline (1)
    Control("subline", "Subline", "Subline",
            "the premises/operations and products sides independently; only 1 "
            "of the 10 declared sublines has ever been rated",
            table=GL, column="Subline",
            note="Seven of the declared sublines need a base submission of "
                 "their own -- Liquor classifications, a Liquor coverage form "
                 "and its own class-code domain -- and are offered as "
                 "unbuildable from this base rather than hidden."),

    # ------------------------------------------------------ 7. structure (1)
    Control("locations", "Locations", "Structure",
            "location allocation and the ForEach aggregation that was "
            "silently wrong once; each location takes the next declared "
            "territory, so the territory factor differs between them",
            kind="number", cast="int",
            note="20 jurisdictions declare exactly one prem/ops territory. "
                 "Asking for two there is NOT APPLICABLE, not a failure."),

    # --------------------------------------------------- 8-9. the plans (4)
    Control("size_of_risk", "Size-of-risk rating", "Rating plans",
            "the interpolated banded lookups, built in stage 3 and never "
            "exercised by a stored submission",
            table=GL, column="SizeOfRiskRatingApplies",
            note="Reproduces OI-88 today: our engine refuses in OK where ISO "
                 "rates it at 8816."),
    Control("experience_rating", "Experience rating", "Rating plans",
            "the experience rating plan, and the credibility factor that "
            "gates schedule rating",
            table=GL, column="ExperienceRatingApplies",
            note="Turning this on alone is not enough to earn credibility -- "
                 "ISO declares about twenty further dated fields, which is "
                 "follow-on work (OI-89)."),
    Control("schedule_rating", "Schedule rating", "Rating plans",
            "the schedule rating plan and R15's plus/minus 25% cap",
            table=GL, column="ScheduleRatingModificationApplies"),
    Control("schedule_pct", "Schedule modification", "Rating plans",
            "one scheduled modification at a declared percentage",
            table=GL, column="SRPClassificationPct",
            note="On the prem/ops sublines ISO applies this only when "
                 "ERPCredibilityFactor >= 0.03, so it is a no-op without "
                 "experience credibility -- OI-89. It moves the premium in "
                 "jurisdictions whose own rules override that gate."),

    # ------------------------------------------------------ 10. terrorism (1)
    Control("terrorism", "Terrorism coverage", "Terrorism",
            "certified-acts terrorism, and the place ISO needs to rate it",
            table=GL, column="TerrorismCoverage",
            note="The ZIP or territory is supplied from the declaration. 20 "
                 "jurisdictions declare neither (OI-91)."),
)

BY_ID = {c.id: c for c in CONTROLS}
GROUPS = tuple(dict.fromkeys(c.group for c in CONTROLS))


# ------------------------------------------------------------------- editing

def _gl(p: dict) -> dict:
    return p["body"]["GeneralLiability"][0]


def _locations(p: dict) -> list:
    return _gl(p)["GeneralLiabilityLocation"]


def _classes(loc: dict) -> list:
    return loc["GeneralLiabilityClassification"]


def _set_everywhere(p: dict, field: str, value) -> int:
    """Set a field at every level of the submission that already carries it.

    The deductible fields are declared on the risk, on the location **and** on
    the classification, and the stored bases carry all three. Setting only the
    top one leaves the classification -- the level the rating reads -- saying
    something else, which produces a difference from ISO that is the harness's
    fault. Levels absent from the base are never invented.
    """
    n = 0
    risk = _gl(p)
    if field in risk:
        risk[field] = value
        n += 1
    for loc in _locations(p):
        if field in loc:
            loc[field] = value
            n += 1
        for cls in _classes(loc):
            if field in cls:
                cls[field] = value
                n += 1
    return n


def _cast(control: Control, value):
    if control.cast == "int":
        return int(value)
    if control.cast == "float":
        return float(value)
    return value


# Each applier mutates the payload and may raise VariantError with a reason a
# person can read. Signature: (payload, value, d, config) -> None
def _apply_deductible(field):
    def apply(p, value, d, config):
        if _set_everywhere(p, field, value) == 0:
            raise VariantError(
                f"{field} is absent from {d.juris}'s base submission at every "
                f"level; setting it would be an invention")
    return apply


def _apply_occurrence_limit(p, value, d, config):
    _gl(p)["PremOpsProdsEachOccurrenceLimit"] = value
    for col in ("GeneralAggregateLimit", "ProdsCompldOpsAggregateLimit"):
        legal = d.dependent(GL, col, {"EachOccurrenceLimit": value})
        if not legal:
            raise VariantError(f"{d.juris} declares no {col} legal with "
                               f"{value}")
        _gl(p)[col] = legal[0]


def _apply_class(p, value, d, config):
    """Code, description and both bases move together, each from ISO's table."""
    desc = d.description(value)
    prem = d.basis_for(value, "PremOps")
    prods = d.dependent(CLS, "ProdsCompldOpsPremiumBasis", {"ClassCode": value})
    for loc in _locations(p):
        for cls in _classes(loc):
            cls["ClassCode"] = value
            cls["ClassDescription"] = desc
            cls["PremOpsPremiumBasis"] = prem
            if prods:
                cls["ProdsCompldOpsPremiumBasis"] = prods[0]


def _apply_exposure(p, value, d, config):
    for loc in _locations(p):
        for cls in _classes(loc):
            if "PremOpsCovExposure" in cls:
                cls["PremOpsCovExposure"] = value
            if "ProdsCompldOpsCovExposure" in cls:
                cls["ProdsCompldOpsCovExposure"] = value


def _apply_premium_basis(p, value, d, config):
    """Only meaningful with a class code that declares it; the class applier
    sets the basis itself, so this exists to keep the two consistent when a
    basis is chosen and a code is not."""
    codes = d.codes_for_basis(value, "PremOps")
    if not codes:
        raise VariantError(f"{d.juris} declares no class code with premium "
                           f"basis {value!r}")
    if config.get("class_code"):
        return                      # the class applier is authoritative
    _apply_class(p, codes[0], d, config)


def _apply_coverage_form(p, value, d, config):
    _gl(p)["PremOpsProdsCoverageForm"] = value
    if value == "Claims Made":
        # ISO declares RetroactiveDate to apply only when this is Yes; leaving
        # it No keeps the variant to one change.
        _gl(p)["RetroactiveDateApplies"] = d.require(
            GL, "RetroactiveDateApplies", "No")
        _gl(p).setdefault("YearInClaimsMade", 1)


def _apply_claims_made_year(p, value, d, config):
    if _gl(p).get("PremOpsProdsCoverageForm") != "Claims Made":
        raise VariantError("a claims-made year applies only to the "
                           "claims-made form; set the coverage form first")
    _gl(p)["YearInClaimsMade"] = value          # Int32 -- OI-90


def _apply_subline(p, value, d, config):
    if value not in SUBLINES_FROM_THIS_BASE:
        raise VariantError(
            f"{value!r} needs a base submission of its own -- its own "
            f"classifications, coverage form and class-code domain. The "
            f"stored bases are shaped for the premises/operations family")
    _gl(p)["Subline"] = value


def _apply_locations(p, value, d, config):
    terrs = d.territories()
    n = int(value)
    if n < 1:
        raise VariantError("a submission needs at least one location")
    if n > len(terrs):
        raise VariantError(
            f"{d.juris} declares {len(terrs)} prem/ops territor"
            f"{'y' if len(terrs) == 1 else 'ies'}, so {n} locations in "
            f"different territories cannot be built here")
    locs = _locations(p)
    first = copy.deepcopy(locs[0])
    del locs[:]
    for i in range(n):
        loc = copy.deepcopy(first)
        loc["PremisesOperationsTerritory"] = terrs[i]
        locs.append(loc)


def _apply_risk_field(field):
    def apply(p, value, d, config):
        _gl(p)[field] = value
    return apply


def _apply_schedule_pct(p, value, d, config):
    if config.get("schedule_rating") != "Yes":
        raise VariantError("a scheduled modification applies only when "
                           "schedule rating is Yes")
    _gl(p)["SRPClassificationPct"] = value


def _apply_terrorism(p, value, d, config):
    _gl(p)["TerrorismCoverage"] = value
    if value != "Yes":
        return
    place = d.terrorism_place()
    if place is None:
        raise VariantError(
            f"{d.juris} declares neither a ZipCode domain nor a "
            f"TerrorismTerritory domain, so there is nothing to send that "
            f"locates the risk (OI-91)")
    field, val = place
    for loc in _locations(p):
        loc[field] = val


APPLIERS = {
    "premops_bi_deductible": _apply_deductible("PremOpsBIDeductible"),
    "premops_pd_deductible": _apply_deductible("PremOpsPDDeductible"),
    "premops_bipd_deductible": _apply_deductible("PremOpsBIPDDeductible"),
    "prods_bi_deductible": _apply_deductible("ProdsCompldOpsBIDeductible"),
    "prods_pd_deductible": _apply_deductible("ProdsCompldOpsPDDeductible"),
    "prods_bipd_deductible": _apply_deductible("ProdsCompldOpsBIPDDeductible"),
    "occurrence_limit": _apply_occurrence_limit,
    "premium_basis": _apply_premium_basis,
    "class_code": _apply_class,
    "exposure": _apply_exposure,
    "coverage_form": _apply_coverage_form,
    "claims_made_year": _apply_claims_made_year,
    "subline": _apply_subline,
    "locations": _apply_locations,
    "size_of_risk": _apply_risk_field("SizeOfRiskRatingApplies"),
    "experience_rating": _apply_risk_field("ExperienceRatingApplies"),
    "schedule_rating": _apply_risk_field("ScheduleRatingModificationApplies"),
    "schedule_pct": _apply_schedule_pct,
    "terrorism": _apply_terrorism,
}

#: Order matters: a control whose applier reads another's answer must run after
#: it. The coverage form writes a default claims-made year, so the year runs
#: later and overwrites it; the class code sets the basis, so the basis runs
#: first and defers.
ORDER = ("subline", "premium_basis", "class_code", "exposure", "locations",
         "occurrence_limit", "premops_bi_deductible", "premops_pd_deductible",
         "premops_bipd_deductible", "prods_bi_deductible",
         "prods_pd_deductible", "prods_bipd_deductible", "coverage_form",
         "claims_made_year", "size_of_risk", "experience_rating",
         "schedule_rating", "schedule_pct", "terrorism")


# ------------------------------------------------------------------ building

def clean(config: dict) -> dict:
    """Drop blanks and unknown ids. A blank means *leave the base alone*."""
    return {k: v for k, v in (config or {}).items()
            if k in BY_ID and v not in ("", None)}


def fingerprint(config: dict) -> str:
    """A stable id for a configuration, so runs of it can be compared later."""
    c = clean(config)
    blob = json.dumps({k: str(c[k]) for k in sorted(c)}, sort_keys=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:12]


def describe(config: dict) -> str:
    c = clean(config)
    if not c:
        return "the base risk, unvaried"
    return ", ".join(f"{BY_ID[k].label}={c[k]}" for k in ORDER if k in c)


def build(config: dict, d: Declared, base: dict | None = None) -> dict:
    """Apply a configuration to a jurisdiction's base submission.

    Raises `VariantError` with a readable reason when the jurisdiction cannot
    express the configuration -- which is a **third outcome**, distinct from
    disagreeing with ISO, and the caller must report it as one.
    """
    c = clean(config)
    p = copy.deepcopy(base if base is not None else d.base())
    for cid in ORDER:
        if cid not in c:
            continue
        control = BY_ID[cid]
        value = _cast(control, c[cid])
        if control.column:
            legal = control.options(d, c)
            if legal and str(value) not in [str(x) for x in legal]:
                raise VariantError(
                    f"{control.label}={value!r} is not declared legal in "
                    f"{d.juris}"
                    + (f" with {', '.join(BY_ID[k].label + '=' + str(c[k]) for k in control.keyed_by if k in c)}"
                       if control.keyed_by and any(k in c for k in control.keyed_by)
                       else "")
                    + f"; {len(legal)} legal: {list(legal)[:5]}")
        APPLIERS[cid](p, value, d, c)
    return p


def options_for(d: Declared, config: dict | None = None) -> dict:
    """Every control's legal options in one jurisdiction, given the answers.

    The numeric controls carry their bounds instead: `locations` is bounded by
    the declared territory count, which is the fact that makes a two-location
    test impossible in 20 jurisdictions.
    """
    c = clean(config or {})
    out = {}
    for control in CONTROLS:
        if control.kind == "number":
            if control.id == "locations":
                out[control.id] = {"kind": "number", "min": 1,
                                   "max": len(d.territories())}
            elif control.id == "claims_made_year":
                out[control.id] = {"kind": "number", "min": 1, "max": 10}
            else:
                out[control.id] = {"kind": "number", "min": 0, "max": None}
            continue
        vals = list(control.options(d, c))
        entry = {"kind": "select", "values": vals}
        if control.id == "subline":
            entry["unbuildable"] = [v for v in vals
                                    if v not in SUBLINES_FROM_THIS_BASE]
        out[control.id] = entry
    return out


def union_options(jurisdictions=None, asof: str = DEFAULT_ASOF) -> dict:
    """Every control's options across jurisdictions, with where each is legal.

    **This is the union, deliberately.** Offering only the intersection would
    remove `Claims Made` -- legal in 50 of 51 -- and every multi-location test,
    because one jurisdiction narrows each. A value is offered with the list of
    jurisdictions that declare it, and a run in a jurisdiction that does not
    reports `NOT APPLICABLE`.
    """
    js = list(jurisdictions or Declared.jurisdictions())
    acc: dict = {c.id: {} for c in CONTROLS}
    numeric: dict = {c.id: {} for c in CONTROLS if c.kind == "number"}
    failed = {}
    for j in js:
        try:
            d = Declared(j, asof)
        except Exception as exc:                             # noqa: BLE001
            failed[j] = f"{type(exc).__name__}: {exc}"
            continue
        opts = options_for(d)
        for cid, spec in opts.items():
            if spec["kind"] == "number":
                numeric[cid][j] = spec
                continue
            for v in spec["values"]:
                acc[cid].setdefault(v, []).append(j)
    out = {}
    for control in CONTROLS:
        if control.kind == "number":
            maxes = {j: s.get("max") for j, s in numeric[control.id].items()}
            out[control.id] = {
                "kind": "number",
                "max_by_juris": maxes,
                "max": max((m for m in maxes.values() if m), default=None),
            }
            continue
        vals = acc[control.id]
        out[control.id] = {
            "kind": "select",
            "values": [{"value": v, "states": sorted(w),
                        "everywhere": len(w) == len(js) - len(failed)}
                       for v, w in vals.items()],
            "unbuildable": ([v for v in vals if v not in SUBLINES_FROM_THIS_BASE]
                            if control.id == "subline" else []),
        }
    return {"asof": asof, "jurisdictions": js, "failed": failed,
            "controls": out}
