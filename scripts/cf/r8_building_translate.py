"""R-8 Phase 4a -- formula translator for building-keyed columns.

`CALC - Bldg Rating` and the part of `CALC - CoreScratchpad` that Building depends
on are keyed one column per building. After 4a, column k (C..AP, k = 1..40) is
**row k of the `IN - Schedule` BUILDING block** (row 47+k), and every input comes
from the Schedule instead of `IN - Location`:

    building-level input   -> the building's own Schedule row
    location-level input   -> INDEX(LOCATION block column, LocIdx)
    CoreScratchpad / Bldg Rating (same column) -> the same row, column k

LocIdx is a key row appended to CoreScratchpad: the building's ParentLoc matched
against LOCATION.ID. Building never reads occupancy-, contents- or BI-level inputs
(verified by `112_...`'s survey), so no other key is needed.

`IN - Location` row 61 (construction description) is derived, and the Schedule did
not carry it, so 4a adds BUILDING column AI `ConstrDesc`, derived from ConstrCode by
the same formula `IN - Location` uses.
"""
from __future__ import annotations

import re

from r8_contents_translate import REF, _strip_strings, colname

IL, CS, BR, SC = ("IN - Location", "CALC - CoreScratchpad", "CALC - Bldg Rating",
                  "IN - Schedule")
PASS = ("TBL - ", "IN - Policy", "IN - Schedule", "IN - Special Class")

LOC_ROWS = (5, 44)
BLDG_ROWS = (48, 87)
RECORDS = 40
FIRST_COL, LAST_COL = 3, 42                 # C..AP
KEY_HDR, ROW_ID, ROW_ACTIVE, ROW_LOC = 282, 283, 284, 285

#: IN - Location row -> IN - Schedule BUILDING column
BLD_COL = {6: "A", 4: "B", 8: "D", 26: "E", 29: "F", 28: "G", 60: "H", 62: "I",
           64: "J", 63: "K", 23: "L", 65: "M", 43: "N", 44: "O", 50: "P", 52: "Q",
           54: "R", 53: "S", 67: "T", 68: "U", 72: "V", 73: "W", 85: "X", 24: "Y",
           79: "Z", 80: "AA", 81: "AB", 82: "AC", 83: "AD", 96: "AE", 99: "AF",
           102: "AG", 92: "AH", 61: "AI"}
#: IN - Location row -> IN - Schedule LOCATION column. (53 WindHailDed exists in both
#: blocks; building-keyed chains take the BUILDING one.)
LOC_COL = {15: "C", 13: "D", 14: "E", 22: "F", 17: "G", 18: "H", 19: "I", 20: "J",
           57: "L", 58: "M", 55: "N"}
BLD_HEADERS = {"A": "ID", "B": "ParentID", "D": "CovType", "E": "ClassCode",
               "H": "ConstrCode", "J": "ConstrSymbol", "N": "Limit", "Q": "Deductible",
               "S": "WindHailDed", "AE": "WindHailExcl", "AH": "AddlInsurableIntOption"}
LOC_HEADERS = {"A": "ID", "C": "State", "F": "ProtClass", "H": "District",
               "I": "BGIITerr", "N": "PerLocationDed"}


def _endpoints(m):
    """(col, row) for the start and, if a range, the end of a REF match."""
    out = [(m.group("col"), int(m.group("row")))]
    if m.group("rng"):
        e = re.match(r":\$?([A-Z]+)\$?(\d+)", m.group("rng"))
        out.append((e.group(1), int(e.group(2))))
    return out


def calc_deps(f: str, home: str) -> set[tuple[str, int]]:
    """Same-column CALC rows a column-C template formula reads, ranges expanded."""
    out = set()
    for lit, chunk in _strip_strings(f):
        if lit:
            continue
        for m in REF.finditer(chunk):
            sh = (m.group("sheet") or "").rstrip("!").strip("'") or home
            if sh not in (CS, BR) or m.group("cd"):
                continue
            ends = _endpoints(m)
            if all(c == "C" for c, _ in ends):
                r0, r1 = ends[0][1], ends[-1][1]
                out |= {(sh, r) for r in range(r0, r1 + 1)}
    return out


def closure(templates: dict[tuple[str, int], str], seeds) -> set[tuple[str, int]]:
    seen, stack = set(), list(seeds)
    while stack:
        n = stack.pop()
        if n in seen or n not in templates:
            continue
        seen.add(n)
        stack.extend(calc_deps(templates[n], n[0]) - seen)
    return seen


class Translator:
    def translate(self, f: str, home: str, k: int) -> str:
        X = colname(FIRST_COL + k - 1)
        B = BLDG_ROWS[0] + k - 1
        out = []
        for lit, chunk in _strip_strings(f):
            out.append(chunk if lit else REF.sub(lambda m: self._one(m, home, X, B), chunk))
        return "".join(out)

    def _one(self, m, home, X, B) -> str:
        raw = m.group(0)
        sh = (m.group("sheet") or "").rstrip("!").strip("'") or home
        if sh.startswith(PASS):
            if sh == "IN - Special Class" and not m.group("cd"):
                raise ValueError(f"relative Special Class reference {raw!r}")
            return raw
        col, row, rd, rng = m.group("col"), int(m.group("row")), m.group("rd"), m.group("rng")
        if sh == IL:
            if rng or m.group("cd") or col != "C":
                raise ValueError(f"non-template IN - Location reference {raw!r}")
            if row in BLD_COL:
                return f"'{SC}'!${BLD_COL[row]}${B}"
            if row in LOC_COL:
                c = LOC_COL[row]
                key = f"{X}${ROW_LOC}" if home == CS else f"'{CS}'!{X}${ROW_LOC}"
                return f"INDEX('{SC}'!${c}${LOC_ROWS[0]}:${c}${LOC_ROWS[1]},{key})"
            raise ValueError(f"IN - Location row {row} has no Schedule home")
        if sh in (CS, BR):
            prefix = m.group("sheet") or ""
            if m.group("cd"):
                # the only absolute CALC reference is a whole-row SUM ($C$r:$L$r)
                if rng and re.fullmatch(r":\$L\$\d+", rng) and col == "C":
                    return raw.replace(rng, rng.replace("$L$", f"${colname(LAST_COL)}$"))
                raise ValueError(f"absolute CALC reference {raw!r}")
            if col != "C":
                raise ValueError(f"non-template CALC reference {raw!r}")
            end = ""
            if rng:
                e = re.match(r":(\$?)([A-Z]+)(\$?)(\d+)", rng)
                if e.group(1) or e.group(2) != "C":
                    raise ValueError(f"non-vertical range {raw!r}")
                end = f":{X}{e.group(3)}{e.group(4)}"
            return f"{prefix}{X}{rd}{row}{end}"
        raise ValueError(f"unexpected sheet reference {raw!r}")


def keys(k: int) -> dict[int, str]:
    B = BLDG_ROWS[0] + k - 1
    l0, l1 = LOC_ROWS
    return {
        ROW_ID: f"=IF('{SC}'!$A${B}=\"\",\"\",'{SC}'!$A${B})",
        ROW_ACTIVE: f"=IF('{SC}'!$C${B}=\"Yes\",\"Yes\",\"No\")",
        # Falls back to 1, never 0: INDEX(col, 0) returns the whole column.
        ROW_LOC: f"=IFERROR(MATCH('{SC}'!$B${B},'{SC}'!$A${l0}:$A${l1},0),1)",
    }


def constr_desc(il61: str, row: int) -> str:
    """IN - Schedule BUILDING.ConstrDesc for schedule row `row`, from IN - Location
    row 61's own formula with its one input (row 60) repointed at ConstrCode."""
    f = il61.replace("'IN - Location'!C60", f"$H{row}")
    if "IN - Location" in f or re.search(r"(?<![A-Z$'])C60(?!\d)", f):
        raise ValueError(f"unexpected IN - Location row 61 formula: {il61!r}")
    return f"=IFERROR({f[1:]},\"\")"
