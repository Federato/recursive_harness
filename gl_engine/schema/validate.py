"""Check a submission against ISO's own declared schema, before rating it.

**Findings, not exceptions.** A submission with three problems should report
three, not the first one; and validation must never be the thing that decides
whether a rating happens, because the engine's own refusals (stages 1–3) are
stricter and better placed. This tells a caller what ISO would object to.

Four checks, and each says what it does *not* cover:

  V1 unknown field     a field ISO does not declare for this jurisdiction.
                       **A warning, not an error** -- ISO's own request format
                       carries envelope fields the form does not declare
  V2 missing required  a field ISO marks required on a policy, unconditionally.
                       Conditionally-required fields are NOT reported: the
                       condition dialect is not evaluated, and guessing would
                       report a field ISO does not want
  V3 illegal value     a value outside the domain table ISO names for it
  V4 the four          CA, FL, NY and TX declare `TerrorismTerritory` against a
                       state-specific `TerrorismTerritoryCode` domain rather
                       than the ZIP-derived one 11 other jurisdictions use.
                       **It cannot be derived from a ZIP** -- E8 and R22
"""
from __future__ import annotations

from dataclasses import dataclass

#: Measured, not asserted: exactly these four declare `TerrorismTerritory`
#: against `TerrorismTerritoryCode`. Eleven others use `TerritoryCodeByZipCode`
#: (`scripts/erc/47_input_schema.py`, S7).
PLACE_CODED = ("CA", "FL", "NY", "TX")

ERROR = "error"
WARNING = "warning"


@dataclass(frozen=True)
class Finding:
    level: str
    code: str
    where: str
    detail: str

    def __str__(self) -> str:          # pragma: no cover - display only
        return f"[{self.level.upper()} {self.code}] {self.where}: {self.detail}"


def _walk(obj, table: str, path: str, out: list):
    """Yield (table, column, value, path) for every scalar in the payload.

    **Nested tables carry a DOTTED name in ISO's field file** --
    `GeneralLiability.GeneralLiabilityTerrorismEndorsementCoverage` -- so the
    table name accumulates as the walk descends. Passing only the innermost
    name makes every nested field look undeclared, which is how the first run
    of this reported five spurious warnings.
    """
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, dict):
                _walk(v, f"{table}.{k}", f"{path}/{k}", out)
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    _walk(item, k, f"{path}/{k}[{i}]", out)
            else:
                out.append((table, k, v, path))
    return out


def validate(payload: dict, schema) -> list:
    """Every finding, in payload order. Never raises on a bad submission."""
    body = payload.get("body", payload)
    risks = body.get("GeneralLiability") or []
    findings: list[Finding] = []

    scalars: list = []
    for i, risk in enumerate(risks):
        _walk(risk, "GeneralLiability", f"GeneralLiability[{i}]", scalars)

    present: set = set()
    for table, column, value, path in scalars:
        present.add((table, column))
        f = schema.get(table, column)
        if f is None:
            findings.append(Finding(
                WARNING, "V1", f"{path}/{column}",
                f"not declared for {schema.juris}; it may be an envelope field "
                f"or a field this jurisdiction does not use"))
            continue
        legal = schema.legal_values(table, column)
        if legal and value not in ("", None) and str(value) not in legal:
            findings.append(Finding(
                ERROR, "V3", f"{path}/{column}",
                f"{value!r} is not in {f.domain} "
                f"({len(legal)} legal values, e.g. {list(legal)[:3]})"))

    for f in schema.required():
        if not f.is_input:
            continue
        if f.key not in present and f.table == "GeneralLiability":
            findings.append(Finding(
                ERROR, "V2", f"GeneralLiability/{f.column}",
                f"required on a policy in {schema.juris} and not supplied"))

    if schema.juris in PLACE_CODED:
        for i, risk in enumerate(risks):
            locs = risk.get("GeneralLiabilityLocation") or []
            for j, loc in enumerate(locs):
                if not loc.get("TerrorismTerritory"):
                    findings.append(Finding(
                        WARNING, "V4",
                        f"GeneralLiability[{i}]/GeneralLiabilityLocation[{j}]",
                        f"{schema.juris} codes terrorism territory explicitly "
                        f"(TerrorismTerritoryCode) and it cannot be derived "
                        f"from a ZIP -- E8; an unmatched one refers, R22"))
    return findings
