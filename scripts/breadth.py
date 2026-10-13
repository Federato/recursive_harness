"""Breadth: vary the SUBMISSION, not the jurisdiction. **OI-87.**

Phase 2 reached *50 of 50 jurisdictions agree with ISO on every published
field*, and that number is narrower than it sounds: **all 51 submissions are the
same risk** -- one location, one classification, class `50017`, gross sales, no
deductible, no rating plans, terrorism off. Stage 4 chose that deliberately so a
difference between states would be attributable, and it did its job. It is now
the limiting factor: whole factor chains in the engine have never had a non-zero
input.

    python scripts/breadth.py                    # build, validate, rate ours
    python scripts/breadth.py --list             # the catalogue, no rating
    python scripts/breadth.py --live             # ...and compare against ISO
    python scripts/breadth.py --group deductible --live
    python scripts/breadth.py --juris NY --live

**Live calls cost, so they are opt-in.** Without `--live` this builds every
variant, checks it against ISO's own declared schema and rates it through our
engine -- which is enough to find a variant the engine cannot rate at all, and
costs nothing.

### Every value here comes from ISO's declaration

Not from the sample submission, and not from a plausible-looking number. A
variant asks the `Schema` for the legal set and **fails loudly at build time**
if the value it wants is not in it -- `Declared.require`. That is deliberate:
a submission ISO would reject teaches us nothing about our arithmetic, and
sending one wastes a call to find out something the filing already said.

Two constraints the declaration supplied that were not obvious:

* **The split and combined deductibles are mutually exclusive.**
  `PremOpsBIPDDeductible` is a dependent domain keyed on the BI/PD pair, and its
  961 dependency keys say: with BI and PD both `No Deductible`, BIPD may be any
  of 31 values; with either one set, **the only legal BIPD is `No Deductible`**.
  A variant that set all three would have been rejected, and the rejection would
  have looked like an engine defect.
* **Terrorism drags in a ZIP.** `GeneralLiabilityLocation.ZipCode` is declared
  to apply when `TerrorismCoverage[.='Yes']`, and the base submissions carry no
  ZIP because they never turn terrorism on. In the eleven ZIP-derived
  jurisdictions the territory comes from it; in CA, FL, NY and TX it cannot
  (E8/R22), so those four take an explicit `TerrorismTerritory`.

### What a difference means here

The same doctrine as phase 2 -- **any difference is our defect until proven
otherwise** -- with one addition that matters on this run. A variant whose
premium is *identical to the base* is a finding too: it means the factor the
variant exists to exercise did not move the number, and a deductible that
changes nothing is either a credit ISO does not file for this class or a chain
we never wired. The report says which variants moved and which did not, because
on the first run of this script that column is the whole point.
"""
from __future__ import annotations

import argparse
import copy
import csv
import json
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from phase2_compare import _differ, compare_payload            # noqa: E402
from raas import NO_ISO, RaaS, RaaSError                        # noqa: E402
from gl_engine import EditionResolver, ResolvedBook             # noqa: E402
from gl_engine.rating import Kernel, STRICT                     # noqa: E402
from gl_engine.schema import Schema, validate                   # noqa: E402

SAMPLES = ROOT / "Engine_Payloads"
OUT = ROOT / "scripts" / "erc" / "out" / "breadth.csv"

#: The as-of date the base submissions carry. Read from the payload rather than
#: assumed, but needed to resolve a book before one is loaded.
DEFAULT_ASOF = "20260801"


class BreadthError(RuntimeError):
    """The harness tried to build an illegal submission. Our bug, not ISO's."""


# --------------------------------------------------------------- declaration

class Declared:
    """The legal values, as ISO files them. Nothing here invents a value."""

    def __init__(self, juris: str, asof: str = DEFAULT_ASOF):
        self.book = ResolvedBook(EditionResolver().resolve(juris, asof))
        self.schema = Schema.for_book(self.book)
        self.juris = juris

    def values(self, table: str, col: str) -> tuple[str, ...]:
        vals, _exact = self.schema.resolved_values(table, col)
        return vals

    def require(self, table: str, col: str, value):
        """Return `value`, or refuse to build the variant.

        The error names the field and shows the legal set, because the only way
        to hit it is a harness that guessed.
        """
        legal = self.values(table, col)
        if legal and str(value) not in legal:
            raise BreadthError(
                f"{table}.{col}={value!r} is not declared legal in "
                f"{self.juris}; {len(legal)} legal: {list(legal)[:8]}")
        return value

    def dependent(self, table: str, col: str, dep: str) -> tuple[str, ...]:
        """The legal values for one leading dependency value.

        `Schema.resolved_values` resolves a dependency through ISO's declared
        `RelatedXPath` against a rated tree. Here there is no tree yet -- the
        submission is still being built -- so the domain table is filtered
        directly on its first dependency column.
        """
        t = self.schema.domain_table(table, col)
        deps = self.schema.dependency_columns(table, col)
        if t is None or not deps:
            return self.values(table, col)
        di, vi = t.col(deps[0]), t.col("DataValue")
        si = t.col("StateCode") if "StateCode" in t.header else None
        out, seen = [], set()
        for row in t.rows:
            if si is not None and row[si] not in (self.juris, "CW"):
                continue
            if str(row[di]) != str(dep):
                continue
            v = str(row[vi])
            if v not in seen:
                seen.add(v)
                out.append(v)
        return tuple(out)

    def description(self, code: str) -> str:
        """ISO's own description for a class code.

        `DomainClassDescriptionByClassCodes`, keyed by
        `ClassCodeForClassDescription`. `ClassDescription` is rating-required
        and carries no domain of its own, so a variant that changes the class
        code must take the description from here rather than keep the previous
        one -- a code and a description that disagree is a submission no
        underwriter would send.
        """
        t = self.book.table("DomainClassDescriptionByClassCodes", "Domain")
        ci, vi = t.col("ClassCodeForClassDescription"), t.col("DataValue")
        for row in t.rows:
            if str(row[ci]) == str(code):
                return str(row[vi])
        raise BreadthError(f"class code {code} has no declared description "
                           f"in {self.juris}")

    def basis(self, code: str, which: str = "PremOps") -> str:
        """The premium basis ISO declares for a class code."""
        col = f"{which}PremiumBasis"
        vals = self.dependent("GeneralLiabilityClassification", col, code)
        if not vals:
            raise BreadthError(f"no {col} declared for class {code}")
        return vals[0]

    def codes_with_basis(self, basis: str, which: str = "PremOps") -> tuple[str, ...]:
        """Every class code whose declared premium basis is `basis`."""
        col = f"{which}PremiumBasis"
        t = self.schema.domain_table("GeneralLiabilityClassification", col)
        deps = self.schema.dependency_columns("GeneralLiabilityClassification", col)
        di, vi = t.col(deps[0]), t.col("DataValue")
        return tuple(str(r[di]) for r in t.rows if str(r[vi]) == basis)

    def zip_for(self) -> str:
        """A ZIP ISO declares for this jurisdiction.

        `GeneralLiabilityLocation.ZipCode` is a SELECT with a declared domain --
        765 values in OK -- and `Other` is one of them, which is a real value
        and not a placeholder. The first numeric one is taken.
        """
        for v in self.values("GeneralLiabilityLocation", "ZipCode"):
            if v.isdigit():
                return v
        raise BreadthError(f"{self.juris} declares no numeric ZipCode")

    def terrorism_place(self) -> tuple[str, str] | None:
        """How this jurisdiction locates a risk for terrorism, or None for none.

        **Asked of the declaration, not of a list of state codes**, so a filing
        that moves a jurisdiction between camps changes this without an edit.

        **Fifteen jurisdictions file a terrorism location and all fifteen file
        the same field**, `GeneralLiabilityLocation.TerrorismTerritory`. Four --
        CA, FL, NY, TX -- back it with `TerrorismTerritoryCode`, whose values
        cannot be derived from a ZIP (E8; an unmatched one refers, R22). The
        other eleven back it with `TerritoryCodeByZipCode`. **Four plus eleven
        is fifteen**: one population, not two (OI-91, closed 2026-08-17).

        `None` is the other 36, and it means **send nothing** -- countrywide
        reads no terrorism location, so there is no input to miss and terrorism
        rates anyway.
        """
        tt = self.values("GeneralLiabilityLocation", "TerrorismTerritory")
        return ("TerrorismTerritory", tt[0]) if tt else None


# ------------------------------------------------------------------- editing

def gl(p: dict) -> dict:
    return p["body"]["GeneralLiability"][0]


def locations(p: dict) -> list:
    return gl(p)["GeneralLiabilityLocation"]


def classifications(loc: dict) -> list:
    return loc["GeneralLiabilityClassification"]


def set_everywhere(p: dict, field: str, value) -> int:
    """Set a field at every level of the submission that already carries it.

    The deductible fields are declared on `GeneralLiability`, on
    `GeneralLiabilityLocation` **and** on `GeneralLiabilityClassification`, and
    the base submissions carry all three at `No Deductible`. Setting only the
    top one leaves the classification -- the level the rating actually reads --
    saying something different, which produces a difference from ISO that is
    the harness's fault. Only levels already present are touched: a field is
    never invented at a level ISO's own sample does not use it.
    """
    n = 0
    risk = gl(p)
    if field in risk:
        risk[field] = value
        n += 1
    for loc in locations(p):
        if field in loc:
            loc[field] = value
            n += 1
        for cls in classifications(loc):
            if field in cls:
                cls[field] = value
                n += 1
    if not n:
        raise BreadthError(f"{field} is not present anywhere in the base "
                           f"submission; setting it would be an invention")
    return n


def set_risk(p: dict, field: str, value) -> None:
    """Set (or add) a field on the risk itself."""
    gl(p)[field] = value


def set_classes(p: dict, field: str, value) -> None:
    for loc in locations(p):
        for cls in classifications(loc):
            cls[field] = value


def retag_class(p: dict, d: Declared, code: str, exposure: float) -> None:
    """Point every classification at a different class code, coherently.

    Code, description and both premium bases move together, each from ISO's own
    table. Changing the code alone leaves a description from a different class
    and a basis that may not be declared for the new one.
    """
    desc = d.description(code)
    prem_basis = d.basis(code, "PremOps")
    for loc in locations(p):
        for cls in classifications(loc):
            cls["ClassCode"] = code
            cls["ClassDescription"] = desc
            cls["PremOpsPremiumBasis"] = prem_basis
            cls["PremOpsCovExposure"] = exposure
            prods = d.dependent("GeneralLiabilityClassification",
                                "ProdsCompldOpsPremiumBasis", code)
            if prods:
                cls["ProdsCompldOpsPremiumBasis"] = prods[0]
                cls["ProdsCompldOpsCovExposure"] = exposure


# ------------------------------------------------------------------ variants

class Variant:
    """One generated submission, with why it exists and what it exercises."""

    def __init__(self, name: str, group: str, exercises: str, build):
        self.name = name
        self.group = group
        self.exercises = exercises
        self.build = build

    def payload(self, base: dict, d: Declared) -> dict:
        p = copy.deepcopy(base)
        self.build(p, d)
        return p


def catalogue(d: Declared) -> list[Variant]:
    """The variant set, ordered by how much of the engine each exercises.

    Ordered as `docs/BACKLOG-2026-08-14.md` orders it, which is by the size of
    the untested surface each one reaches -- not by how easy it is to write.
    """
    V: list[Variant] = []

    def add(name, group, exercises):
        def deco(fn):
            V.append(Variant(name, group, exercises, fn))
            return fn
        return deco

    # -- deductibles: a factor chain whose input has always been zero --------

    @add("premops-pd-5000-occ", "deductible",
         "the PD deductible credit chain, prem/ops")
    def _(p, d):
        set_everywhere(p, "PremOpsPDDeductible",
                       d.require("GeneralLiability", "PremOpsPDDeductible",
                                 "5,000 Per Occurrence"))

    @add("premops-bi-1000-claim", "deductible",
         "the BI deductible credit chain, and per-CLAIM rather than "
         "per-occurrence")
    def _(p, d):
        set_everywhere(p, "PremOpsBIDeductible",
                       d.require("GeneralLiability", "PremOpsBIDeductible",
                                 "1,000 Per Claim"))

    @add("premops-bipd-10000-occ", "deductible",
         "the COMBINED BI/PD deductible, legal only while BI and PD are both "
         "No Deductible")
    def _(p, d):
        legal = d.dependent("GeneralLiability", "PremOpsBIPDDeductible",
                            "No Deductible")
        want = "10,000 Per Occurrence"
        if want not in legal:
            raise BreadthError(f"{want} not legal as a combined BIPD "
                               f"deductible in {d.juris}")
        set_everywhere(p, "PremOpsBIPDDeductible", want)

    @add("prods-pd-2000-occ", "deductible",
         "the deductible chain on the products side, which is a separate set "
         "of tables")
    def _(p, d):
        set_everywhere(p, "ProdsCompldOpsPDDeductible",
                       d.require("GeneralLiability",
                                 "ProdsCompldOpsPDDeductible",
                                 "2,000 Per Occurrence"))

    @add("both-sides-pd-deductible", "deductible",
         "prem/ops and products deductibles at once -- two chains, one premium")
    def _(p, d):
        set_everywhere(p, "PremOpsPDDeductible",
                       d.require("GeneralLiability", "PremOpsPDDeductible",
                                 "5,000 Per Occurrence"))
        set_everywhere(p, "ProdsCompldOpsPDDeductible",
                       d.require("GeneralLiability",
                                 "ProdsCompldOpsPDDeductible",
                                 "5,000 Per Occurrence"))

    # -- structure: allocation, and the ForEach that was silently wrong once --

    @add("two-locations", "structure",
         "location allocation and the ForEach aggregation; two territories, "
         "so the territory factor differs between them")
    def _(p, d):
        terrs = d.values("GeneralLiabilityLocation",
                         "PremisesOperationsTerritory")
        if len(terrs) < 2:
            raise BreadthError(f"{d.juris} declares only {len(terrs)} "
                               f"prem/ops territor(ies); no second location")
        first, second = terrs[0], terrs[1]
        locs = locations(p)
        locs[0]["PremisesOperationsTerritory"] = first
        extra = copy.deepcopy(locs[0])
        extra["PremisesOperationsTerritory"] = second
        locs.append(extra)

    @add("two-classifications", "structure",
         "two classifications in one location -- the class loop, and a "
         "premium built from two class rates")
    def _(p, d):
        loc = locations(p)[0]
        first = classifications(loc)[0]
        others = [c for c in d.codes_with_basis("Gross Sales")
                  if c != str(first["ClassCode"])]
        if not others:
            raise BreadthError("no second Gross Sales class code declared")
        code = others[0]
        extra = copy.deepcopy(first)
        extra["ClassCode"] = code
        extra["ClassDescription"] = d.description(code)
        extra["PremOpsPremiumBasis"] = d.basis(code, "PremOps")
        prods = d.dependent("GeneralLiabilityClassification",
                            "ProdsCompldOpsPremiumBasis", code)
        if prods:
            extra["ProdsCompldOpsPremiumBasis"] = prods[0]
        classifications(loc).append(extra)

    @add("area-basis-class", "structure",
         "a premium basis that is not Gross Sales -- Area, whose exposure "
         "divisor and rounding differ")
    def _(p, d):
        codes = d.codes_with_basis("Area")
        if not codes:
            raise BreadthError(f"{d.juris} declares no Area-basis class")
        retag_class(p, d, codes[0], 50000.0)

    @add("if-any-basis", "structure",
         "IfAnyBasis=Yes -- a minimum-premium path where the exposure is "
         "declared not to rate")
    def _(p, d):
        set_classes(p, "IfAnyBasis",
                    d.require("GeneralLiabilityClassification", "IfAnyBasis",
                              "Yes"))

    # -- size of risk: built in stage 3, never exercised by a submission -----

    @add("size-of-risk", "sizeofrisk",
         "the interpolated banded lookups; SizeOfRiskRatingApplies is a "
         "one-field switch -- no other field names it in a condition")
    def _(p, d):
        set_risk(p, "SizeOfRiskRatingApplies",
                 d.require("GeneralLiability", "SizeOfRiskRatingApplies",
                           "Yes"))

    # -- limits: the ILF chain, at something other than the default ---------

    @add("occurrence-limit-500k", "limits",
         "the increased-limit factors below the 1,000,000 default, with "
         "aggregates ISO declares legal for that occurrence limit")
    def _(p, d):
        occ = d.require("GeneralLiability", "PremOpsProdsEachOccurrenceLimit",
                        "500,000 CSL")
        set_risk(p, "PremOpsProdsEachOccurrenceLimit", occ)
        for col in ("GeneralAggregateLimit", "ProdsCompldOpsAggregateLimit"):
            legal = d.dependent("GeneralLiability", col, occ)
            if not legal:
                raise BreadthError(f"no {col} declared legal with {occ}")
            gl(p)[col] = legal[0]

    @add("occurrence-limit-5m", "limits",
         "the increased-limit factors above the default, the other side of "
         "the same table")
    def _(p, d):
        occ = d.require("GeneralLiability", "PremOpsProdsEachOccurrenceLimit",
                        "5,000,000 CSL")
        set_risk(p, "PremOpsProdsEachOccurrenceLimit", occ)
        for col in ("GeneralAggregateLimit", "ProdsCompldOpsAggregateLimit"):
            legal = d.dependent("GeneralLiability", col, occ)
            if not legal:
                raise BreadthError(f"no {col} declared legal with {occ}")
            gl(p)[col] = legal[0]

    # -- the coverage form no sample uses -----------------------------------

    @add("claims-made-year-1", "form",
         "the claims-made form and its first-year factor; RetroactiveDate is "
         "declared to apply only when RetroactiveDateApplies=Yes, so this "
         "variant leaves it No and supplies YearInClaimsMade instead")
    def _(p, d):
        set_risk(p, "PremOpsProdsCoverageForm",
                 d.require("GeneralLiability", "PremOpsProdsCoverageForm",
                           "Claims Made"))
        set_risk(p, "RetroactiveDateApplies",
                 d.require("GeneralLiability", "RetroactiveDateApplies", "No"))
        # An INTEGER, not the string the control type suggests. `fields.py`
        # says it in as many words -- `Type` is a form control and not a data
        # type -- and this is the first submission in the project that pays for
        # ignoring it: ISO answered
        #   *"Element value 'YearInClaimsMade' has unexpected type of 'String'
        #    (was expecting 'Int32')"*
        set_risk(p, "YearInClaimsMade", 1)

    @add("claims-made-year-4", "form",
         "the mature claims-made year, which is a different row of the same "
         "table")
    def _(p, d):
        set_risk(p, "PremOpsProdsCoverageForm",
                 d.require("GeneralLiability", "PremOpsProdsCoverageForm",
                           "Claims Made"))
        set_risk(p, "RetroactiveDateApplies",
                 d.require("GeneralLiability", "RetroactiveDateApplies", "No"))
        set_risk(p, "YearInClaimsMade", 4)          # Int32, see year-1 above

    # -- the rating plans, and the cap R15 exists for -----------------------

    @add("schedule-rating-credit", "plans",
         "the schedule rating plan, one modification at ISO's declared "
         "maximum for that item")
    def _(p, d):
        set_risk(p, "ScheduleRatingModificationApplies",
                 d.require("GeneralLiability",
                           "ScheduleRatingModificationApplies", "Yes"))
        pcts = d.values("GeneralLiability", "SRPClassificationPct")
        if not pcts:
            raise BreadthError(f"{d.juris} declares no SRPClassificationPct")
        set_risk(p, "SRPClassificationPct", pcts[0])

    @add("schedule-rating-stacked", "plans",
         "every schedule-rating item ISO declares, each at its first declared "
         "value -- the case R15's +/-25% cap exists for")
    def _(p, d):
        set_risk(p, "ScheduleRatingModificationApplies",
                 d.require("GeneralLiability",
                           "ScheduleRatingModificationApplies", "Yes"))
        n = 0
        for f in d.schema:
            if not f.column.startswith("SRP") or not f.column.endswith("Pct"):
                continue
            if f.table != "GeneralLiability":
                continue
            vals = d.values(f.table, f.column)
            if vals:
                set_risk(p, f.column, vals[0])
                n += 1
        if not n:
            raise BreadthError(f"{d.juris} declares no SRP percentage fields")

    # -- terrorism: the coverage that cost 18 and was missing for a week ----

    @add("terrorism-on", "terrorism",
         "certified-acts terrorism, and the one field ISO locates a risk with "
         "-- TerrorismTerritory in the fifteen that file it, four of them "
         "against codes no ZIP can derive (E8/R22); nothing in the other 36, "
         "which rate it anyway (OI-91)")
    def _(p, d):
        set_risk(p, "TerrorismCoverage",
                 d.require("GeneralLiability", "TerrorismCoverage", "Yes"))
        place = d.terrorism_place()
        if place is None:
            return
        field, value = place
        for loc in locations(p):
            loc[field] = value

    return V


# -------------------------------------------------------------------- runner

def run(juris: str, groups, live: bool, listing: bool, limit: int) -> int:
    base_path = SAMPLES / juris / "submission.json"
    if not base_path.exists():
        print(f"no base submission for {juris} at {base_path}")
        return 1
    base = json.loads(base_path.read_text(encoding="utf-8"))

    d = Declared(juris)
    variants = catalogue(d)
    if groups:
        variants = [v for v in variants if v.group in groups]
    if limit:
        variants = variants[:limit]

    print(f"BREADTH -- {juris}, {d.book.state.pkg_id}"
          f"{' over ' + d.book.parent.pkg_id if d.book.parent else ''}")
    print(f"{len(variants)} variant(s) over "
          f"{len(sorted({v.group for v in variants}))} group(s); "
          f"every value from ISO's declared domains")
    print()
    if listing:
        for v in variants:
            print(f"  {v.group:11s} {v.name:26s} {v.exercises}")
        return 0

    kernel = Kernel(mode=STRICT, resolver=EditionResolver())
    client = None
    if live:
        if juris in NO_ISO:
            print(f"{juris} is not on the ISO subscription -- nothing to "
                  f"compare against (OI-86). Rating ours only.")
            live = False
        else:
            try:
                client = RaaS()
            except RaaSError as exc:
                print(f"cannot reach ISO: {exc}")
                return 1

    dp = _differ() if live else None

    # The base itself, so "did the premium move" is measured and not assumed.
    base_result = kernel.rate(copy.deepcopy(base))
    if not base_result.complete:
        print(f"the BASE submission does not rate: {base_result.stopped}")
        return 1
    base_premium = base_result.premium
    print(f"base premium (unvaried risk)             : {base_premium}")
    print()

    rows = []
    for v in variants:
        row = {"juris": juris, "group": v.group, "variant": v.name,
               "exercises": v.exercises, "base_premium": str(base_premium)}
        try:
            payload = v.payload(base, d)
        except BreadthError as exc:
            row.update(status="NOT BUILT", detail=str(exc)[:200])
            rows.append(row)
            print(f"  {v.name:26s} NOT BUILT     {exc}")
            continue

        # ISO's own schema, before ISO's own service. A variant that fails here
        # is the harness's fault and must not cost a call.
        findings = validate(payload, d.schema)
        errors = [f for f in findings if f.level == "error"]
        row["schema_errors"] = len(errors)
        if errors:
            row.update(status="ILLEGAL",
                       detail="; ".join(str(f) for f in errors)[:300])
            rows.append(row)
            print(f"  {v.name:26s} ILLEGAL       {errors[0]}")
            continue

        try:
            ours = kernel.rate(copy.deepcopy(payload))
        except Exception as exc:                              # noqa: BLE001
            row.update(status="OURS FAILED",
                       detail=f"{type(exc).__name__}: {exc}"[:200])
            rows.append(row)
            print(f"  {v.name:26s} OURS FAILED   {type(exc).__name__}: {exc}")
            continue
        if not ours.complete:
            row.update(status="OURS STOPPED", detail=str(ours.stopped)[:200])
            rows.append(row)
            print(f"  {v.name:26s} OURS STOPPED  {str(ours.stopped)[:90]}")
            continue

        row["ours"] = str(ours.premium)
        moved = ours.premium != base_premium
        row["moved"] = "yes" if moved else "NO"
        row["from_base"] = str(ours.premium - base_premium)

        if not live:
            row["status"] = "RATED"
            rows.append(row)
            note = (f"moved {ours.premium - base_premium:+}" if moved
                    else "UNCHANGED from base")
            print(f"  {v.name:26s} RATED   ours={str(ours.premium):>10s}  "
                  f"{note}")
            continue

        r = compare_payload(juris, payload, kernel, client, dp)
        row.update({k: v2 for k, v2 in r.items() if k != "juris"})
        line = (f"  {v.name:26s} {r['status']:13s} "
                f"ours={r.get('ours', '-'):>10s} iso={r.get('iso', '-'):>10s}")
        if not moved:
            line += "  UNCHANGED from base"
        if r.get("fields_differing"):
            line += f"  {r['fields_differing']} of {r['fields_compared']} fields differ"
        if r.get("detail"):
            line += f"  {str(r['detail'])[:70]}"
        print(line)
        if r.get("first_differences"):
            print(f"       {str(r['first_differences'])[:150]}")
        rows.append(row)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    keys = sorted({k for r in rows for k in r})
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)

    n = len(rows)
    print()
    if live:
        ok = sum(1 for r in rows if r.get("status") == "MATCH")
        print(f"    agree with ISO on premium and every field : {ok} of {n}")
        for label, st in (("premium agrees, fields differ",  "PREMIUM ONLY"),
                          ("disagree",                       "DIFF"),
                          ("our engine could not rate it",   "OURS FAILED"),
                          ("our engine refused",             "OURS STOPPED"),
                          ("ISO refused",                    "RAAS FAILED"),
                          ("illegal by ISO's own schema",     "ILLEGAL"),
                          ("not buildable",                  "NOT BUILT")):
            k = [r["variant"] for r in rows if r.get("status") == st]
            if k:
                print(f"    {label:41s} : {len(k)} ({', '.join(k)})")
    else:
        rated = [r for r in rows if r.get("status") == "RATED"]
        print(f"    rated through our engine : {len(rated)} of {n}")
        for label, st in (("illegal by ISO's own schema", "ILLEGAL"),
                          ("not buildable",              "NOT BUILT"),
                          ("could not rate",             "OURS FAILED"),
                          ("refused",                    "OURS STOPPED")):
            k = [r["variant"] for r in rows if r.get("status") == st]
            if k:
                print(f"    {label:24s} : {len(k)} ({', '.join(k)})")

    flat = [r["variant"] for r in rows if r.get("moved") == "NO"]
    if flat:
        print(f"    premium UNCHANGED from base : {len(flat)} "
              f"({', '.join(flat)})")
        print("      -- a variant that does not move the premium exercised "
              "nothing; that is a finding, not a pass.")
    if live and client is not None:
        print(f"    live calls made : {client.calls}")
    print()
    print("    Any difference is our defect until proven otherwise.")
    print(f"\n[wrote {OUT}]")
    return 0


def main(argv) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--juris", default="OK")
    ap.add_argument("--group", action="append", default=[],
                    help="restrict to a group; repeatable")
    ap.add_argument("--live", action="store_true",
                    help="also rate through ISO's service and compare")
    ap.add_argument("--list", action="store_true", dest="listing",
                    help="print the catalogue and stop")
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args(argv)
    return run(a.juris.upper(), set(a.group), a.live, a.listing, a.limit)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
