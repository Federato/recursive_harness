"""The submission schema, as ISO files it.

The build plan expected stage 4 to **derive** the submission shape from the 53
RAaS payloads. It is better than that: **ISO files the schema.**

`Form Fields/Fields.FormField.csv` declares, per jurisdiction and per field:
its `Type`, its label, whether it is required on a policy or a quote, its
default, minimum and maximum, the condition under which it applies at all, and
**the domain table naming its legal values**.

`Ratebook Columns/RatebookColumns.FormPage.csv` adds `RatingRequiredCondition`
-- required *to rate*, which is a different and stricter question than required
on a form.

Measured over 570 packages (`scripts/erc/47_input_schema.py`): countrywide
declares **1,381 fields over 429 tables**, and a state adds between **2 and 104**
of its own. **No field is required in every jurisdiction**, which is why the
schema is per-jurisdiction and not one global shape with exceptions.

**A caution the field data itself makes necessary.** `Type` is a *form control*
-- `TEXT`, `SELECT`, `CHECKBOX`, `HIDDEN`, `TEXTAREA`, `BUTTON`, `ANCHOR` -- and
not a data type. It says how ISO's own screen renders the field, and a validator
that reads `TEXT` as "string" would accept an exposure of `"banana"`. Data types
come from the DataDefs, and legal values from the domain table.
"""
from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from ..erc.discovery import read_text

FIELD_FILE = Path("Form Fields") / "Fields.FormField.csv"
RATEBOOK_FILE = Path("Ratebook Columns") / "RatebookColumns.FormPage.csv"

#: Form-control types, not data types. Kept so the distinction is explicit
#: rather than implied by the absence of a comment.
CONTROL_TYPES = frozenset({"TEXT", "SELECT", "CHECKBOX", "HIDDEN", "TEXTAREA",
                           "BUTTON", "ANCHOR", ""})

#: Controls that never carry a submitted value.
NON_INPUT = frozenset({"BUTTON", "ANCHOR"})


@dataclass(frozen=True)
class Field:
    """One field ISO declares for one jurisdiction."""

    table: str
    column: str
    control: str                 # the FORM control, not a data type
    label: str = ""
    policy_required: bool = False
    quote_required: bool = False
    domain: str = ""             # domain table naming the legal values
    default: str = ""
    minimum: str = ""
    maximum: str = ""
    condition: str = ""          # when the field applies at all
    required_condition: str = ""
    rating_required: str = ""    # from RatebookColumns; "" means never

    @property
    def key(self) -> tuple[str, str]:
        return (self.table, self.column)

    @property
    def is_input(self) -> bool:
        return self.control not in NON_INPUT

    @property
    def conditional(self) -> bool:
        """Required only when a condition holds.

        The condition dialect is XPath-shaped and is **not** the rule language
        of stages 2 and 3 -- 138 distinct expressions, nearly all of the form
        `Subline[.='...']`. It is not evaluated here: a schema that guessed at
        a condition would report a field missing that ISO does not want, which
        is worse than reporting nothing.
        """
        return bool(self.condition or self.required_condition)

    def __str__(self) -> str:          # pragma: no cover - display only
        bits = [f"{self.table}.{self.column}", f"({self.control})"]
        if self.policy_required:
            bits.append("required")
        if self.domain:
            bits.append(f"values<-{self.domain}")
        return " ".join(bits)


def _rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rdr = csv.DictReader(io.StringIO(read_text(path)))
    return [r for r in rdr if r]


class Schema:
    """Every field ISO declares for one resolved rulebook.

    State over countrywide, by field name -- the same wholesale-by-name
    override N3 gives tables and stage 3 gives rules. A state that declares a
    field replaces the countrywide declaration of it wholesale, including when
    the state makes it optional and countrywide made it required.
    """

    def __init__(self, book):
        self.book = book
        self.juris = book.juris
        self._fields: dict[tuple[str, str], Field] = {}
        self._load()

    @classmethod
    def for_book(cls, book) -> "Schema":
        return cls(book)

    # ------------------------------------------------------------------ load

    def _load(self) -> None:
        layers = [self.book.parent, self.book.state]     # parent first, state wins
        rating_required: dict[tuple[str, str], str] = {}
        for layer in layers:
            if layer is None:
                continue
            for r in _rows(layer.package.content / RATEBOOK_FILE):
                cond = (r.get("RatingRequiredCondition") or "").strip()
                if cond:
                    rating_required[(r["TableName"], r["ColumnName"])] = cond

        for layer in layers:
            if layer is None:
                continue
            for r in _rows(layer.package.content / FIELD_FILE):
                key = (r.get("TableName", ""), r.get("ColumnName", ""))
                if not key[1]:
                    continue
                self._fields[key] = Field(
                    table=key[0], column=key[1],
                    control=(r.get("Type") or "").strip(),
                    label=(r.get("Label") or "").strip(),
                    policy_required=r.get("PolicyRequired") == "True",
                    quote_required=r.get("QuoteRequired") == "True",
                    domain=(r.get("DomainTableName") or "").strip(),
                    default=(r.get("Default") or "").strip(),
                    minimum=(r.get("Minimum") or "").strip(),
                    maximum=(r.get("Maximum") or "").strip(),
                    condition=(r.get("Condition") or "").strip(),
                    required_condition=(r.get("RequiredCondition") or "").strip(),
                    rating_required=rating_required.get(key, ""),
                )

    # --------------------------------------------------------------- queries

    def __len__(self) -> int:
        return len(self._fields)

    def __iter__(self):
        return iter(self._fields.values())

    def get(self, table: str, column: str) -> Field | None:
        return self._fields.get((table, column))

    def tables(self) -> tuple[str, ...]:
        return tuple(sorted({f.table for f in self}))

    def for_table(self, table: str) -> tuple[Field, ...]:
        return tuple(sorted((f for f in self if f.table == table),
                            key=lambda f: f.column))

    def required(self, unconditional_only: bool = True) -> tuple[Field, ...]:
        """Fields required on a policy.

        `unconditional_only` because a conditionally-required field is only
        required when its condition holds, and the condition dialect is not
        evaluated here. Reporting those as missing would be a guess.
        """
        return tuple(f for f in self
                     if f.policy_required
                     and not (unconditional_only and f.conditional))

    def rating_required(self) -> tuple[Field, ...]:
        return tuple(f for f in self if f.rating_required)

    @lru_cache(maxsize=None)
    def legal_values(self, table: str, column: str) -> tuple[str, ...]:
        """The values ISO's own domain table permits, or () if unconstrained.

        Read from the domain table rather than from anything we wrote down --
        this is the same content stage 5's workbook publishes.
        """
        f = self.get(table, column)
        if f is None or not f.domain:
            return ()
        # `DomainTableName` names the table WITHOUT the `Domain` prefix the
        # files carry: `YesNo` is `DomainYesNo.DomainTable.csv`. Both spellings
        # are tried so a future filing that drops the prefix still resolves.
        t = None
        for candidate in (f"Domain{f.domain}", f.domain):
            try:
                t = self.book.table(candidate, "Domain")
                break
            except Exception:                            # noqa: BLE001
                continue
        if t is None:
            return ()
        if not t.rows:
            return ()

        # **`DataValue` is the stored value; `DisplayValue` is what ISO's
        # screen shows.** The convention is universal across the domain tables
        # in this corpus. Taking "the first column that is not the state" --
        # the obvious guess, and the first thing tried here -- returns the ZIP
        # from a ZIP-to-territory table and reports every real territory as
        # illegal.
        #
        # Some domains carry LEADING dependency columns: the legal set for
        # `IncreasedLimitsTableAssignmentPremOps` depends on the class code.
        # Those are unioned rather than resolved, which makes the result a
        # **safe superset** -- a value outside it is certainly illegal, a value
        # inside it may still be wrong for the particular dependency. Resolving
        # the dependency would mean evaluating the condition dialect, which
        # this module deliberately does not do.
        if "DataValue" not in t.header:
            return ()
        i = t.col("DataValue")
        state_i = t.col("StateCode") if "StateCode" in t.header else None
        seen, out = set(), []
        for row in t.rows:
            if state_i is not None and row[state_i] not in (self.juris, "CW"):
                continue
            v = row[i]
            if v is None:
                continue
            v = str(v)
            if v in seen:
                continue
            seen.add(v)
            out.append(v)
        return tuple(out)

    def dependent_domain(self, table: str, column: str) -> bool:
        """True when the legal set depends on another field's value.

        Reported so a caller knows the check is a superset rather than exact.
        """
        f = self.get(table, column)
        if f is None or not f.domain:
            return False
        for candidate in (f"Domain{f.domain}", f.domain):
            try:
                t = self.book.table(candidate, "Domain")
            except Exception:                            # noqa: BLE001
                continue
            extra = [h for h in t.header
                     if h not in ("StateCode", "Status", "MetadataCodes",
                                  "DisplayValue", "DataValue")]
            return bool(extra)
        return False

    def summary(self) -> dict:
        return {
            "jurisdiction": self.juris,
            "packages": [self.book.state.pkg_id]
                        + ([self.book.parent.pkg_id] if self.book.parent else []),
            "fields": len(self),
            "tables": len(self.tables()),
            "required_unconditional": len(self.required()),
            "required_conditional": sum(1 for f in self
                                        if f.policy_required and f.conditional),
            "rating_required": len(self.rating_required()),
            "with_domain": sum(1 for f in self if f.domain),
        }

    def __repr__(self) -> str:          # pragma: no cover - display only
        return f"<Schema {self.juris} {len(self)} fields>"
