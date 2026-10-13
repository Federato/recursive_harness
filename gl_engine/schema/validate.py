"""Check a submission against ISO's own declared schema, before rating it.

**Findings, not exceptions.** A submission with three problems should report
three, not the first one; and validation must never be the thing that decides
whether a rating happens, because the engine's own refusals (stages 1-3) are
stricter and better placed. This tells a caller what ISO would object to.

**It walks the ERC data tree, not the raw JSON.** The tree is what stage 3
builds and stage 2 rates, so a table name here is the one ISO's field file uses
-- including the dotted names nested tables carry -- and a `RelatedXPath` can
actually be resolved, because the tree has parents and the `../../` dialect is
the one `interp/tree.py` already implements.

Five checks, and each says what it does *not* cover:

  V1 unknown field     a field ISO does not declare for this jurisdiction.
                       **A warning, not an error** -- ISO's own request format
                       carries envelope fields the form does not declare
  V2 missing required  a field ISO marks required on a policy, unconditionally.
                       Conditionally-required fields are NOT reported: the
                       condition dialect is not evaluated, and guessing would
                       report a field ISO does not want
  V3 illegal value     a value outside the domain ISO names. **Exact when ISO
                       declares the dependency, a safe superset when it does
                       not, and the finding says which** -- see V5
  V4 the four          CA, FL, NY and TX declare `TerrorismTerritory` against a
                       state-specific `TerrorismTerritoryCode` domain rather
                       than the ZIP-derived one 11 other jurisdictions use.
                       **It cannot be derived from a ZIP** -- E8 and R22
  V5 superset in use   reported once per rating: how many dependent domains
                       were checked exactly and how many only as a superset,
                       so the strength of V3 is never assumed
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from ..interp import tree
from ..rating.submission import from_raas
from .condition import ConditionError, holds

#: Measured, not asserted: exactly these four back
#: `GeneralLiabilityLocation.TerrorismTerritory` with `TerrorismTerritoryCode`,
#: whose values no ZIP can derive. **Eleven others declare the same field**
#: against `TerritoryCodeByZipCode`, and four plus eleven is the whole
#: population of fifteen that file a terrorism location at all -- a
#: subdivision, not two camps plus a remainder (OI-91, closed 2026-08-17).
#: The other 36 file none, and countrywide reads none, so terrorism there is
#: not located at all rather than located some other way.
#:
#: Source: `scripts/erc/52_oi91_terrorism_place.py`, M1. It previously cited
#: `47_input_schema.py` S7, **which does not produce these numbers** -- S7 is a
#: substring search for County/Place/Town/Borough/Parish whose own hits are
#: `PremiumPlaceHolder` matching on "Place".
PLACE_CODED = ("CA", "FL", "NY", "TX")

ERROR = "error"
WARNING = "warning"
INFO = "info"


@dataclass(frozen=True)
class Finding:
    level: str
    code: str
    where: str
    detail: str

    def __str__(self) -> str:          # pragma: no cover - display only
        return f"[{self.level.upper()} {self.code}] {self.where}: {self.detail}"


def _is_wrapper(node) -> bool:
    """`XTable` holding repeated `X` -- a container ISO's field file omits."""
    return (node.tag.endswith("Table")
            and any(c.tag == node.tag[:-5] for c in node.children))


def _walk(node, table: str, out: list) -> None:
    """Yield (table, column, node) for every leaf, with ISO's table naming.

    A repeated element starts a **new** table under its own bare name; a nested
    single object is **dotted** onto its parent. That is exactly how
    `Fields.FormField.csv` names them.
    """
    for c in node.children:
        if _is_wrapper(c):
            for item in c.children:
                _walk(item, c.tag[:-5], out)
        elif c.children:
            _walk(c, f"{table}.{c.tag}" if table else c.tag, out)
        elif c.text not in (None, ""):
            # Only leaves that CARRY A VALUE are fields. An empty object in the
            # request -- `"GeneralLiabilityMedPayCoverage": {}` -- arrives as a
            # childless node with no text, and reporting it as an undeclared
            # field is an artefact of the walk, not a finding.
            out.append((table, c.tag, c))


#: The required fields whose absence changes the premium without a refusal (OI-134). Measured, not chosen:
#: `scripts/erc/57_rating_inputs.py` drops each ISO-required field a request carries, one at a time, in every
#: state, and lists those where the premium moves and the engine does not stop. Regenerate it when ISO files.
RATING_INPUTS_FILE = Path(__file__).with_name("rating_inputs.json")


def _inputs_file() -> dict:
    global _RATING_INPUTS
    if _RATING_INPUTS is None:
        try:
            _RATING_INPUTS = json.loads(RATING_INPUTS_FILE.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            _RATING_INPUTS = {}
    return _RATING_INPUTS


def rating_inputs() -> frozenset:
    """`Table.Column` names that must not be missing or blank (`fields`); empty if the file is absent."""
    return frozenset(_inputs_file().get("fields", ()))


def list_inputs() -> frozenset:
    """`Table.Column` names whose value must be on ISO's list for the edition (`list_fields`, OI-130)."""
    return frozenset(_inputs_file().get("list_fields", ()))


_RATING_INPUTS = None


STOP_GAP = "GeneralLiabilityStopGapEmployersLiabilityCoverageEndorsementPolLvl"


def stop_gap_conflict(root) -> str | None:
    """OI-130 (B-07 part 3c): Stop Gap details sent, but the Stop Gap question not answered "Yes".

    "unanswered" -- the details are there and `StopGap` is absent or blank: the engine refuses (3c1; ISO's form
    requires the answer only from 2027, and before that the endorsement silently prices 0).
    "no" -- the details are there and `StopGap` is "No": $0 is right, the details look like a leftover (3c2, a
    warning). None otherwise.
    """
    for risk in tree.select("GeneralLiabilityTable/GeneralLiability", root):
        if not any(c.tag in (STOP_GAP, STOP_GAP + "Table") for c in risk.children):
            continue
        ans = risk.first("StopGap")
        if _unanswered(ans):
            return "unanswered"
        if str(ans.text).strip() == "No":
            return "no"
    return None


def stop_gap_unrated_limits(root) -> bool:
    """OI-130 (B-07 part 3c, route (e)): Stop Gap bought with limits ISO's rules cannot rate, and no manual premium.

    ISO's `SetStopGapIncrdLimitFactor` (every ND / WA edition) looks the ILF up only when the accident limit equals
    the each-employee disease limit; otherwise the factor is 0 and Stop Gap prices $0 with no message -- the
    manual's "refer to company" combination, which ISO's form expects a `ManualPremium` for.
    """
    for risk in tree.select("GeneralLiabilityTable/GeneralLiability", root):
        if str(tree.read("StopGap", risk) or "").strip() != "Yes":
            continue
        for rec in tree.select(f"{STOP_GAP}Table/{STOP_GAP}", risk) + [c for c in risk.children if c.tag == STOP_GAP]:
            acc = str(tree.read("LimitBodilyInjuryByAccident", rec) or "").strip()
            emp = str(tree.read("LimitBodilyInjuryByDiseaseEachEmployee", rec) or "").strip()
            try:
                manual = float(str(tree.read("ManualPremium", rec) or 0)) > 0
            except ValueError:
                manual = False
            if acc and acc != emp and not manual:
                return True
    return False


def invalid_values(root, schema, only: frozenset | None = None) -> list:
    """`(Table.Column, value, legal sample)` for every answer not on ISO's list for this edition.

    The list is `Schema.resolved_values`: exact where ISO declares a dependency, otherwise a safe superset --
    which can let an illegal value through but never rejects a legal one, so a refusal built on this never
    refuses a value ISO accepts. `only` restricts it to those names (the engine passes `list_inputs()`).
    """
    leaves: list = []
    for risk in tree.select("GeneralLiabilityTable/GeneralLiability", root):
        _walk(risk, "GeneralLiability", leaves)
    out = []
    for table, column, node in leaves:
        name = f"{table}.{column}"
        if only is not None and name not in only:
            continue
        f = schema.get(table, column)
        if f is None or not f.domain:
            continue
        legal, _exact = schema.resolved_values(table, column, node)
        value = node.text
        if legal and value not in ("", None) and str(value) not in legal:
            out.append((name, str(value), sorted(legal)[:4]))
    return out


def _rows(node, table: str, out: list) -> list:
    """(table, row) for every row of every table, with ISO's table naming (as `_walk` names leaves)."""
    out.append((table, node))
    for c in node.children:
        if _is_wrapper(c):
            for item in c.children:
                _rows(item, c.tag[:-5], out)
        elif c.children:
            _rows(c, f"{table}.{c.tag}", out)
    return out


@dataclass(frozen=True)
class Missing:
    """An ISO-required input absent from a row where ISO's conditions say it is required."""

    table: str
    column: str
    condition: str          # ISO's RequiredCondition (or display Condition) that held; "" when unconditional
    rating_input: bool      # in rating_inputs.json: leaving it out changes the premium silently

    @property
    def name(self) -> str:
        return f"{self.table}.{self.column}"


def _unanswered(node) -> bool:
    """Absent, or present and blank. A blank answer is no answer (B-07 part 1, the user's decision 2026-10-13):
    ISO's rules read `""` exactly as they read an absent field -- `Subline: ""` priced the policy at $0 past the
    OI-134 check, which had only looked for absence."""
    return node is None or (not node.children and (node.text is None or not str(node.text).strip()))


def missing_required(root, schema) -> tuple[list, list]:
    """Every required input absent where ISO's conditions hold, and the conditions that could not be read.

    `root` is the data tree (`from_raas(...)[0]`). A field is required on a row when ISO marks it
    PolicyRequired, it is an input, and both its display `Condition` and its `RequiredCondition` (when present)
    hold for that row -- evaluated by `condition.holds`. A condition outside that evaluator's slice is returned
    in the second list and the field is NOT reported: never guess a requirement.
    """
    by_table: dict = {}
    for risk in tree.select("GeneralLiabilityTable/GeneralLiability", root):
        for t, n in _rows(risk, "GeneralLiability", []):
            by_table.setdefault(t, []).append(n)
    inputs = rating_inputs()
    out, unread, seen = [], [], set()
    for f in schema:
        if not f.policy_required or not f.is_input:
            continue
        for row in by_table.get(f.table, ()):
            held, ok = "", True
            for cond in (f.condition, f.required_condition):
                if not cond:
                    continue
                try:
                    if not holds(cond, row):
                        ok = False
                        break
                    held = cond
                except ConditionError:
                    unread.append(cond)
                    ok = False
                    break
            if ok and _unanswered(row.first(f.column)) and (f.table, f.column) not in seen:
                seen.add((f.table, f.column))
                out.append(Missing(f.table, f.column, held, f"{f.table}.{f.column}" in inputs))
    return out, unread


def validate(payload: dict, schema) -> list:
    """Every finding, in payload order. Never raises on a bad submission."""
    try:
        root, _juris, _asof = from_raas(payload)
    except ValueError as exc:
        return [Finding(ERROR, "V0", "submission", str(exc))]

    findings: list[Finding] = []
    leaves: list = []
    for risk in tree.select("GeneralLiabilityTable/GeneralLiability", root):
        _walk(risk, "GeneralLiability", leaves)

    present = set()
    exact_n = superset_n = 0
    for table, column, node in leaves:
        present.add((table, column))
        f = schema.get(table, column)
        if f is None:
            findings.append(Finding(
                WARNING, "V1", f"{table}.{column}",
                f"not declared for {schema.juris}; it may be an envelope field "
                f"or a field this jurisdiction does not use"))
            continue
        if not f.domain:
            continue

        legal, exact = schema.resolved_values(table, column, node)
        if schema.dependency_columns(table, column):
            exact_n += 1 if exact else 0
            superset_n += 0 if exact else 1
        value = node.text
        if legal and value not in ("", None) and str(value) not in legal:
            findings.append(Finding(
                ERROR, "V3", f"{table}.{column}",
                f"{value!r} is not in {f.domain} "
                f"({len(legal)} legal value(s), "
                f"{'exact' if exact else 'superset -- dependency not declared'}"
                f"; e.g. {list(legal)[:3]})"
                + ("; it changes the premium, so the engine refuses (OI-130)"
                   if f"{table}.{column}" in list_inputs() else "")))

    for f in schema.required():
        if not f.is_input:
            continue
        if f.key not in present and f.table == "GeneralLiability":
            findings.append(Finding(
                ERROR, "V2", f"GeneralLiability.{f.column}",
                f"required on a policy in {schema.juris} and not supplied"))

    # V6 / V7 (OI-134): conditional requirements too, evaluated. A rating input missing is an error (the engine
    # refuses it); any other required field missing is a warning -- ISO rates without it.
    reported = {(x.code, x.where) for x in findings}
    missing, unread = missing_required(root, schema)
    for m in missing:
        if m.rating_input:
            findings.append(Finding(
                ERROR, "V7", m.name,
                f"a rating input ISO requires{' when ' + m.condition if m.condition else ''}, not supplied: "
                f"leaving it out changes the premium, so the engine refuses (OI-134)"))
        elif ("V2", m.name) not in reported:
            findings.append(Finding(
                WARNING, "V6", m.name,
                f"ISO's form requires it{' when ' + m.condition if m.condition else ''}; not supplied "
                f"(ISO rates without it; it does not change the premium)"))
    sg = stop_gap_conflict(root)
    if sg == "unanswered":
        findings.append(Finding(
            ERROR, "V8", "GeneralLiability.StopGap",
            "Stop Gap details are sent but the Stop Gap question is not answered: the engine refuses (OI-130)"))
    elif sg == "no":
        findings.append(Finding(
            WARNING, "V8", "GeneralLiability.StopGap",
            "Stop Gap is answered \"No\" but Stop Gap details are sent; they are ignored (Stop Gap prices $0)"))
    if stop_gap_unrated_limits(root):
        findings.append(Finding(
            ERROR, "V8", f"{STOP_GAP}.ManualPremium",
            "the accident limit differs from the each-employee limit, which ISO's rules do not rate: give a "
            "ManualPremium (the engine refuses without one, OI-130)"))
    if unread:
        findings.append(Finding(
            INFO, "V6", "conditions",
            f"{len(set(unread))} required-field condition(s) outside the evaluated slice; those fields not checked"))

    if schema.juris in PLACE_CODED:
        for i, loc in enumerate(tree.select(
                "GeneralLiabilityTable/GeneralLiability/"
                "GeneralLiabilityLocationTable/GeneralLiabilityLocation",
                root)):
            if not tree.read("TerrorismTerritory", loc):
                findings.append(Finding(
                    WARNING, "V4", f"GeneralLiabilityLocation[{i}]",
                    f"{schema.juris} codes terrorism territory explicitly "
                    f"(TerrorismTerritoryCode) and it cannot be derived from a "
                    f"ZIP -- E8; an unmatched one refers, R22"))

    if exact_n or superset_n:
        findings.append(Finding(
            INFO, "V5", "dependent domains",
            f"{exact_n} checked exactly against ISO's declared dependency, "
            f"{superset_n} against a superset because ISO declares none "
            f"(29 of 90 dependent domains carry a RelatedXPath)"))
    return findings
