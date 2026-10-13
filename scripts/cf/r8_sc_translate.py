"""R-8 Phase 4c -- translator for `CALC - Special Class`.

That sheet holds two coverages in one set of columns: the Special Class item
(rows 1-87) and its Business Income (rows 88-158). After 4c:

    rows 1-87    column k = Schedule SPECIAL CLASS row 219+k    (context "SC")
    rows 88-158  column k = Schedule SC BUSINESS INCOME row 262+k (context "SCBI")

A Special Class item hangs off a LOCATION, not a building, so it gets its own LocIdx.
An SC Business Income record hangs off a Special Class item (SCParent), and reaches
the location through it.

**What the old sheet borrowed from "building k", and what replaces it** (backlog W-8,
decided 2026-09-22 in ISO's favour and confirmed live by `114_...`):

    CoreScratchpad 2  (state)            -> the item's location's State
    CoreScratchpad 59 (BGII rate key)    -> state + location BGIITerr + the ITEM's symbol
    CoreScratchpad 72 (lowest-rate key)  -> state + the ITEM's symbol
    CoreScratchpad 138 (TOTAL LIMIT)     -> the linked building's, when included in it
    Bldg Rating 4 (LCM)                  -> LCM looked up on the item's state
    Bldg Rating 30/31/61/110/111         -> column C: policy-level cyber factors

`IN - Special Class` rows 7/8/9 (zip, city, state) are location attributes: they
resolve through the location. Every CoreScratchpad row the sheet reaches that reads
`IN - Special Class` is copied per record, once per context.
"""
from __future__ import annotations

import re

from r8_contents_translate import REF, _strip_strings, colname
import r8_building_translate as B

ISC, SCC = "IN - Special Class", "CALC - Special Class"
CS, BR, SC, IL = B.CS, B.BR, B.SC, B.IL
PASS = ("TBL - ", "IN - Policy")
AP = colname(B.LAST_COL)

SC_ROWS, SCBI_ROWS = (220, 259), (263, 302)
SC_HDR, SCBI_HDR = 219, 262
SPLIT = 88                                    # rows < 88: SC context; >= 88: SCBI

#: IN - Special Class row -> Schedule SPECIAL CLASS column
SC_COL = {6: "A", 4: "B", 10: "D", 12: "E", 13: "F", 14: "G", 15: "H", 16: "I",
          17: "J", 19: "K", 21: "L", 22: "M", 24: "N", 25: "O", 27: "P", 30: "Q",
          31: "R", 33: "S", 36: "T", 49: "U", 51: "V", 53: "W"}
#: IN - Special Class row -> Schedule SC BUSINESS INCOME column. Limit is row 20,
#: the input the rater prices on (row 42 is an unread duplicate -- see 4c record).
SCBI_COL = {38: "D", 39: "E", 40: "F", 41: "G", 20: "H", 18: "I", 44: "J", 45: "K",
            46: "L", 50: "M", 52: "N", 54: "O"}
#: IN - Special Class row -> Schedule LOCATION column (the item's location)
LOC_OF = {9: "C", 7: "D", 8: "E"}
SC_HEADERS = {"A": "ID", "B": "ParentID", "D": "ItemDesc", "K": "BuildingLimit",
              "M": "LinkedBuildingItemID", "R": "ConstrSymbol", "W": "TheftExcl"}
SCBI_HEADERS = {"A": "ID", "B": "ParentID", "D": "CovType", "H": "Limit", "I": "Coinsurance",
                "O": "TheftExcl"}
BR_POLICY = {30, 31, 61, 110, 111}
CS_SPECIAL = {2, 59, 72, 138}

# key rows on CALC - Special Class (appended below row 158)
SC_KEY_HDR, SC_ID, SC_ACTIVE, SC_LOC = 160, 161, 162, 163
BI_KEY_HDR, BI_ID, BI_ACTIVE, BI_PARENT = 165, 166, 167, 168
COPY_HDR, COPY_FIRST = 170, 171


def cs_deps(f: str) -> set[int]:
    """CoreScratchpad rows (same column) a CoreScratchpad or SC formula reads."""
    out = set()
    for lit, chunk in _strip_strings(f):
        if lit:
            continue
        for m in REF.finditer(chunk):
            sh = (m.group("sheet") or "").rstrip("!").strip("'")
            if sh == CS and not m.group("cd") and m.group("col") == "C":
                out.add(int(m.group("row")))
    return out


def cs_local_deps(f: str) -> set[int]:
    """Rows a CoreScratchpad formula reads on its own sheet (unqualified or qualified)."""
    out = set()
    for lit, chunk in _strip_strings(f):
        if lit:
            continue
        for m in REF.finditer(chunk):
            sh = (m.group("sheet") or "").rstrip("!").strip("'") or CS
            if sh == CS and not m.group("cd") and m.group("col") == "C" and not m.group("rng"):
                out.add(int(m.group("row")))
    return out


def copy_set(cs_f: dict[int, str], seeds: set[int]) -> list[int]:
    seen, stack = set(), [s for s in seeds if s not in CS_SPECIAL]
    while stack:
        r = stack.pop()
        if r in seen or r in CS_SPECIAL:
            continue
        if r not in cs_f:
            raise ValueError(f"CoreScratchpad row {r} is read but holds no formula")
        seen.add(r)
        stack.extend(cs_local_deps(cs_f[r]) - seen)
    return sorted(seen)


class SCTranslator:
    def __init__(self, sc_copy: dict[int, int], bi_copy: dict[int, int]):
        self.copy = {"SC": sc_copy, "SCBI": bi_copy}

    # -- context helpers -------------------------------------------------------------
    def _own(self, ctx, k):
        return (SC_ROWS[0] if ctx == "SC" else SCBI_ROWS[0]) + k - 1

    def _sc_field(self, ctx, col, X, k):
        if ctx == "SC":
            return f"'{SC}'!${col}${self._own(ctx, k)}"
        return f"INDEX('{SC}'!${col}${SC_ROWS[0]}:${col}${SC_ROWS[1]},{X}${BI_PARENT})"

    def _locidx(self, ctx, X):
        if ctx == "SC":
            return f"{X}${SC_LOC}"
        return f"INDEX($C${SC_LOC}:${AP}${SC_LOC},1,{X}${BI_PARENT})"

    def _loc_field(self, ctx, col, X):
        l0, l1 = B.LOC_ROWS
        return f"INDEX('{SC}'!${col}${l0}:${col}${l1},{self._locidx(ctx, X)})"

    def _state(self, ctx, X):
        return self._loc_field(ctx, "C", X)

    # -- the translation -------------------------------------------------------------
    def translate(self, f: str, src: str, ctx: str, k: int) -> str:
        X = colname(B.FIRST_COL + k - 1)
        out = []
        for lit, chunk in _strip_strings(f):
            out.append(chunk if lit else REF.sub(lambda m: self._one(m, src, ctx, X, k), chunk))
        return "".join(out)

    def _one(self, m, src, ctx, X, k) -> str:
        raw = m.group(0)
        sh = (m.group("sheet") or "").rstrip("!").strip("'") or src
        if sh.startswith(PASS):
            return raw
        col, row, rng = m.group("col"), int(m.group("row")), m.group("rng")
        if rng or m.group("cd") or col != "C":
            raise ValueError(f"non-template reference {raw!r} on {sh}")
        if sh == ISC:
            if row in SC_COL:
                return self._sc_field(ctx, SC_COL[row], X, k)
            if row in SCBI_COL:
                if ctx != "SCBI":
                    raise ValueError(f"SC context reads SCBI field row {row}")
                return f"'{SC}'!${SCBI_COL[row]}${self._own(ctx, k)}"
            if row in LOC_OF:
                return self._loc_field(ctx, LOC_OF[row], X)
            raise ValueError(f"IN - Special Class row {row} has no Schedule home")
        if sh == CS:
            if row == 2:
                return self._state(ctx, X)
            if row == 59:
                return (f"CONCATENATE({self._state(ctx, X)},{self._loc_field(ctx, 'I', X)},"
                        f"{self._sc_field(ctx, 'R', X, k)})")
            if row == 72:
                return f"CONCATENATE({self._state(ctx, X)},{self._sc_field(ctx, 'R', X, k)})"
            if row == 138:
                b0, b1 = B.BLDG_ROWS
                return (f"IFERROR(INDEX('{CS}'!$C$138:${AP}$138,1,MATCH("
                        f"{self._sc_field(ctx, 'M', X, k)},'{SC}'!$A${b0}:$A${b1},0)),0)")
            if row in self.copy[ctx]:
                return f"{X}{self.copy[ctx][row]}"
            raise ValueError(f"CoreScratchpad row {row} not copied for {ctx}")
        if sh == BR:
            if row == 4:
                return (f"IFERROR(INDEX('TBL - LCM'!$B$2:$B$47,MATCH({self._state(ctx, X)},"
                        f"'TBL - LCM'!$A$2:$A$47,0)),0)")
            if row in BR_POLICY:
                return f"'{BR}'!$C${row}"
            raise ValueError(f"Bldg Rating row {row} not mapped")
        if sh == SCC:
            if ctx == "SCBI" and row < SPLIT:
                return f"INDEX($C${row}:${AP}${row},1,{X}${BI_PARENT})"
            return f"{X}{m.group('rd')}{row}"
        if sh == IL:
            raise ValueError(f"unexpected IN - Location reference {raw!r}")
        raise ValueError(f"unexpected sheet reference {raw!r}")


def keys(k: int) -> dict[int, str]:
    s, b = SC_ROWS[0] + k - 1, SCBI_ROWS[0] + k - 1
    l0, l1 = B.LOC_ROWS
    return {
        SC_ID: f"=IF('{SC}'!$A${s}=\"\",\"\",'{SC}'!$A${s})",
        SC_ACTIVE: f"=IF('{SC}'!$C${s}=\"Yes\",\"Yes\",\"No\")",
        SC_LOC: f"=IFERROR(MATCH('{SC}'!$B${s},'{SC}'!$A${l0}:$A${l1},0),1)",
        BI_ID: f"=IF('{SC}'!$A${b}=\"\",\"\",'{SC}'!$A${b})",
        BI_ACTIVE: f"=IF('{SC}'!$C${b}=\"Yes\",\"Yes\",\"No\")",
        BI_PARENT: f"=IFERROR(MATCH('{SC}'!$B${b},'{SC}'!$A${SC_ROWS[0]}:$A${SC_ROWS[1]},0),1)",
    }
