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

from dataclasses import dataclass

from ..interp import tree
from ..rating.submission import from_raas

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
                f"; e.g. {list(legal)[:3]})"))

    for f in schema.required():
        if not f.is_input:
            continue
        if f.key not in present and f.table == "GeneralLiability":
            findings.append(Finding(
                ERROR, "V2", f"GeneralLiability.{f.column}",
                f"required on a policy in {schema.juris} and not supplied"))

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
