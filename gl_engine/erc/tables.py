"""Rate and domain tables: typed from ISO's own definitions, never inferred.

Every table in ERC arrives as a pair -- `FooDef.RateTableDef.xml` declaring the
key columns, their types and any banding, and `Foo.RateTable.csv` carrying the
rows. This module reads the definition first and types the CSV against it. The
reverse order, guessing types from the data, is how `"0"` becomes the number
nought instead of a refer marker.

What the corpus actually contains, measured over 27,717 definitions:

* **four declared types** -- `string`, `integer`, `decimal`, `long`
* **`CaseInsensitive` is `false` on all 67,661 key columns.** The attribute
  exists, so it is honoured, but nothing in this corpus exercises it
* **200 `Range` elements**, which are the banded lookups: a logical column backed
  by two physical `_From` / `_ToLessThan` columns, with a `RangeType` naming
  which end is inclusive
* **18 of those ranges carry `InterpolateMode="Linear"`** on the *value* side --
  size-of-risk relativity interpolates between two published relativities rather
  than stepping. A stepped reading is wrong by up to the width of a band
* **3,056 domain CSVs have no definition file at all**, so their shape is read
  from the header. They are declared undeclared rather than skipped
"""
from __future__ import annotations

import csv
import io
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from enum import Enum
from functools import lru_cache
from pathlib import Path

from ..errors import TableError
from .discovery import read_text

# --------------------------------------------------------------------- shape


class Shape(Enum):
    """How a table is READ. Measured, not assumed -- see `census()`."""

    EXACT = "exact"                  # every key column is a plain equality match
    BANDED = "banded"                # at least one key column is a From/To range
    INTERPOLATED = "interpolated"    # banded, and the VALUE interpolates across the band
    UNDECLARED = "undeclared"        # CSV with no Def; shape read from the header


class Population(Enum):
    """Whether a table has anything in it. Orthogonal to `Shape` (N7).

    N7 is the whole reason this is a separate axis: *presence is not population
    is not purpose*. A table can exist, be typed, and be deliberately empty --
    and empty means "not offered here", not "look somewhere else".
    """

    POPULATED = "populated"
    EMPTY = "empty"                  # declared and deliberately empty (N3, N7)
    SPLIT_FAMILY = "split-family"    # base is empty; suffixed siblings carry the rows (OI-20)


TYPES = ("string", "integer", "decimal", "long")

_RANGE_SUFFIXES = ("_From", "_ToLessThan", "_FromGreaterThan", "_To",
                   "_FromInclusive", "_ToInclusive")

#: `PremOpsLossCostCATerr001` where there is no `PremOpsLossCost` at all.
#: A reader that knows only the base name sees an empty table and no error --
#: the worst failure this corpus offers, because the premium comes out finished.
#:
#: The base is greedy so `PremOpsSizeOfRiskLossCostTerr001` groups under
#: `PremOpsSizeOfRiskLossCost`, not `PremOpsLossCost`.
SPLIT_RE = re.compile(r"^(?P<base>[A-Za-z]*LossCost)(?P<suffix>.+)$")

#: Which suffixes mean "this is a slice of the base table" -- an optional state
#: code, an optional `Terr`, an optional number, in that order.
#:
#: Built by enumerating ALL 75 loss-cost suffixes in the corpus, not from the
#: handful we had looked at. That enumeration is what separates the two kinds:
#: `Terr001`, `CATerr001`, `001` and `NY` are slices, while `OverOneHundred` and
#: `OverOneMillion` (54 packages each) are SEPARATE TABLES for high limits.
#: Treating those two as slices was the first version of this predicate and it
#: reported one split family where there are dozens.
TERRITORY_SUFFIX = re.compile(r"^(?:[A-Z]{2})?(?:Terr)?\d*$")


# ---------------------------------------------------------------- definition

@dataclass(frozen=True)
class Column:
    name: str
    type: str = "string"
    case_insensitive: bool = False


@dataclass(frozen=True)
class Range:
    """A logical column backed by two physical bound columns."""

    name: str
    type: str
    range_type: str            # 'FromInclusiveToExclusive', 'FromExclusiveToInclusive', ...
    lo_col: str
    hi_col: str
    interpolate: str | None = None     # 'Linear' on the value side, else None
    range_key_col: str | None = None   # which KEY range a value range interpolates along

    @property
    def lo_inclusive(self) -> bool:
        return "FromInclusive" in self.range_type or self.range_type == ""

    @property
    def hi_inclusive(self) -> bool:
        return "ToInclusive" in self.range_type


@dataclass
class TableDef:
    """ISO's declaration of a table's shape."""

    name: str
    kind: str                          # 'Rate' | 'Domain'
    metadata_codes: tuple[str, ...] = ()
    key_cols: tuple[Column, ...] = ()
    key_ranges: tuple[Range, ...] = ()
    value_cols: tuple[Column, ...] = ()
    value_ranges: tuple[Range, ...] = ()
    declared: bool = True              # False when reconstructed from a bare CSV

    @property
    def header(self) -> list[str]:
        """The physical column order ISO declares, ranges expanded in place."""
        out: list[str] = []
        for c in self.key_cols:
            out.append(c.name)
        for r in self.key_ranges:
            out += [r.lo_col, r.hi_col]
        for c in self.value_cols:
            out.append(c.name)
        for r in self.value_ranges:
            out += [r.lo_col, r.hi_col]
        return out

    @property
    def shape(self) -> Shape:
        if not self.declared:
            return Shape.UNDECLARED
        if any(r.interpolate for r in self.value_ranges):
            return Shape.INTERPOLATED
        if self.key_ranges:
            return Shape.BANDED
        return Shape.EXACT

    def type_of(self, col: str) -> str:
        for c in self.key_cols + self.value_cols:
            if c.name == col:
                return c.type
        for r in self.key_ranges + self.value_ranges:
            if col in (r.lo_col, r.hi_col):
                return r.type
        return "string"


def _cols(node, tag: str, ns: str) -> tuple[list[Column], list[Range]]:
    cols: list[Column] = []
    rngs: list[Range] = []
    if node is None:
        return cols, rngs
    for child in node:
        lt = child.tag.rsplit("}", 1)[-1]
        if lt in ("KeyCol", "ValueCol"):
            cols.append(Column(
                child.get("Name", ""),
                child.get("Type", "string"),
                child.get("CaseInsensitive", "false").lower() == "true"))
        elif lt == "Range":
            bounds = [g.get("Name", "") for g in child]
            if len(bounds) != 2:
                raise TableError(
                    f"Range {child.get('Name')!r} declares {len(bounds)} bound "
                    f"columns; exactly 2 are required")
            rngs.append(Range(
                child.get("Name", ""), child.get("Type", "string"),
                child.get("RangeType", ""), bounds[0], bounds[1],
                child.get("InterpolateMode"), child.get("RangeKeyCol")))
    return cols, rngs


def parse_def(path: Path, name: str, kind: str) -> TableDef:
    root = ET.fromstring(read_text(path))
    ns = root.tag.split("}")[0][1:] if root.tag.startswith("{") else ""

    def find(local):
        for ch in root:
            if ch.tag.rsplit("}", 1)[-1] == local:
                return ch
        return None

    md = find("MetaData")
    codes = tuple(c.text or "" for c in (md or ())
                  if c.tag.rsplit("}", 1)[-1] == "MetaDataCode")
    kc, kr = _cols(find("KeyCols"), "KeyCol", ns)
    vc, vr = _cols(find("ValueCols"), "ValueCol", ns)
    return TableDef(name, kind, codes, tuple(kc), tuple(kr), tuple(vc), tuple(vr))


# --------------------------------------------------------------------- table

def _coerce(raw: str, typ: str):
    """Text -> typed value. `Decimal` for every number (N10), never float.

    Returns the raw string when it cannot be coerced. It does NOT return None or
    zero: an unparseable cell is data we do not understand, and turning it into
    a number here is exactly the class of silent corruption N13 warns about. The
    caller sees the string and can decide, or the alphabet assertion catches it.
    """
    s = raw.strip()
    if s == "":
        return None
    if typ in ("integer", "long"):
        try:
            return int(s)
        except ValueError:
            return s
    if typ == "decimal":
        try:
            return Decimal(s)
        except InvalidOperation:
            return s
    return s


@dataclass
class Table:
    """A loaded ERC table: ISO's declaration plus its rows, typed."""

    name: str
    kind: str
    definition: TableDef
    header: tuple[str, ...]
    rows: list[tuple]                      # typed, in file order
    package: str                           # owning package id (from the XSD, N6)
    path: Path | None = None
    #: siblings that carry this table's rows when the base is empty (OI-20)
    split_siblings: tuple[str, ...] = ()

    @property
    def shape(self) -> Shape:
        return self.definition.shape

    @property
    def population(self) -> Population:
        if self.rows:
            return Population.POPULATED
        return Population.SPLIT_FAMILY if self.split_siblings else Population.EMPTY

    @property
    def is_empty(self) -> bool:
        return not self.rows

    def col(self, name: str) -> int:
        try:
            return self.header.index(name)
        except ValueError:
            raise TableError(
                f"{self.package}/{self.name}: no column {name!r}; header is "
                f"{list(self.header)}") from None

    def __len__(self) -> int:
        return len(self.rows)

    def __repr__(self) -> str:             # pragma: no cover - display only
        return (f"<Table {self.package}/{self.name} {self.shape.value}/"
                f"{self.population.value} {len(self.rows)} rows>")


#: `FormPage` was added for stage 2. The interpreter's single most common
#: `Lookup` target is `Pages`, which lives in `Form Pages/` and not in either
#: table directory -- 22,694 lookups for a form's `Name` and 22,694 for its
#: `Number`, out of 54,716 in the corpus. It arrives as a bare CSV with no
#: definition file, which `load_table` already supports.
_SUFFIX = {"Rate": (".RateTableDef.xml", ".RateTable.csv", "Rate Tables"),
           "Domain": (".DomainTableDef.xml", ".DomainTable.csv", "Domain Tables"),
           "FormPage": (".FormPageDef.xml", ".FormPage.csv", "Form Pages")}


def load_table(content: Path, kind: str, name: str, package: str,
               siblings: tuple[str, ...] = ()) -> Table:
    """Load one table by name from one package's content directory."""
    defsuf, datasuf, cat = _SUFFIX[kind]
    dpath = content / cat / f"{name}Def{defsuf}"
    cpath = content / cat / f"{name}{datasuf}"
    if not dpath.exists() and not cpath.exists():
        raise TableError(f"{package}: no {kind} table named {name!r}")

    if dpath.exists():
        d = parse_def(dpath, name, kind)
    else:
        d = TableDef(name, kind, declared=False)

    header: list[str] = []
    data: list[list[str]] = []
    if cpath.exists():
        rdr = csv.reader(io.StringIO(read_text(cpath)))
        for i, row in enumerate(rdr):
            if i == 0:
                header = [c.strip() for c in row]
                # 18 of 27,717 CSVs carry a trailing comma, producing a phantom
                # empty column. It is a formatting artifact, not a data column;
                # dropping it is what makes the header/def reconciliation exact.
                while header and header[-1] == "":
                    header.pop()
                continue
            if any(c.strip() for c in row):
                data.append(row)
    if not header:
        header = d.header
    if not d.declared:
        d = TableDef(name, kind, key_cols=tuple(Column(h) for h in header),
                     declared=False)

    types = [d.type_of(h) for h in header]
    rows = [tuple(_coerce(row[i] if i < len(row) else "", types[i])
                  for i in range(len(header)))
            for row in data]
    return Table(name, kind, d, tuple(header), rows, package, cpath, siblings)


def list_tables(content: Path, kind: str) -> list[str]:
    """Every table name in a package, by DIRECTORY LISTING.

    Not by matching an expected list. This is the counting discipline applied to
    file systems: the population is what is on disk, not what we went looking
    for.
    """
    defsuf, datasuf, cat = _SUFFIX[kind]
    d = content / cat
    if not d.is_dir():
        return []
    names: set[str] = set()
    for f in d.iterdir():
        n = f.name
        if n.endswith(datasuf):
            names.add(n[: -len(datasuf)])
        elif n.endswith(defsuf):
            base = n[: -len(defsuf)]
            names.add(base[:-3] if base.endswith("Def") else base)
    return sorted(names)


def split_families(names) -> dict[str, tuple[str, ...]]:
    """Group per-territory loss-cost slices under their base name (OI-20).

    **The base need not be present.** In California, New Jersey and Ohio the
    state package carries only the slices, so the base name resolves upward to a
    header-only countrywide table. Requiring the base locally -- which the first
    version did -- makes exactly those three states invisible, which is the whole
    defect OI-20 describes.
    """
    fams: dict[str, list[str]] = {}
    unambiguous: dict[str, bool] = {}
    for n in sorted(names):
        m = SPLIT_RE.match(n)
        if not m:
            continue
        suffix = m.group("suffix")
        if suffix and TERRITORY_SUFFIX.match(suffix):
            base = m.group("base")
            fams.setdefault(base, []).append(n)
            # A bare state code is ambiguous: `ProdsCompldLossCostNY` may be a
            # slice, or may simply be a table whose own name ends that way. A
            # digit or the token `Terr` is not ambiguous.
            if any(c.isdigit() for c in suffix) or "Terr" in suffix:
                unambiguous[base] = True
    # Keep a family only if it has more than one member or at least one member
    # names a territory outright. Without this, one header-only New York table
    # whose name merely ends in `NY` reads as a broken split family.
    return {k: tuple(v) for k, v in fams.items()
            if len(v) > 1 or unambiguous.get(k)}
