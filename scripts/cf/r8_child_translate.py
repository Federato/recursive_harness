"""R-8 Phase 4 -- translator for a coverage whose record hangs off a building.

The Contents translator (`r8_contents_translate.py`) generalised, now that Building
itself reads the Schedule (Phase 4a). A child record in column k reads:

    its own inputs          -> its own row in its Schedule block
    building-level inputs   -> INDEX(Schedule BUILDING column, ParentCol)
    location-level inputs   -> INDEX(Schedule LOCATION column,
                                     INDEX(CoreScratchpad LocIdx row, ParentCol))
    CoreScratchpad / Bldg Rating, building-level -> INDEX($C{r}:$AP{r}, ParentCol)
    CoreScratchpad, record-level                  -> a per-record copy on its own sheet

A CoreScratchpad row is record-level when it reads one of the record's own inputs,
directly or through another record-level row.
"""
from __future__ import annotations

from r8_contents_translate import REF, _strip_strings, colname
import r8_building_translate as B

IL, CS, BR, SC = B.IL, B.CS, B.BR, B.SC
PASS = ("TBL - ", "IN - Policy")


def record_level_rows(cs_formula: dict[int, str], seeds, own_rows: set[int]) -> set[int]:
    memo: dict[int, bool] = {}

    def is_rec(r, stack=()):
        if r in memo:
            return memo[r]
        if r in stack or r not in cs_formula:
            return False
        res = False
        for lit, chunk in _strip_strings(cs_formula[r]):
            if lit:
                continue
            for m in REF.finditer(chunk):
                sh = (m.group("sheet") or "").rstrip("!").strip("'") or CS
                row = int(m.group("row"))
                if m.group("cd") or m.group("col") != "C":
                    continue
                if sh == IL and row in own_rows:
                    res = True
                elif sh == CS and not m.group("rng") and is_rec(row, stack + (r,)):
                    res = True
        memo[r] = res
        return res

    needed, seen = set(), set()

    def walk(r):
        if r in seen or r not in cs_formula:
            return
        seen.add(r)
        if not is_rec(r):
            return
        needed.add(r)
        for lit, chunk in _strip_strings(cs_formula[r]):
            if lit:
                continue
            for m in REF.finditer(chunk):
                sh = (m.group("sheet") or "").rstrip("!").strip("'") or CS
                if sh == CS and m.group("col") == "C" and not m.group("cd"):
                    walk(int(m.group("row")))

    for s in seeds:
        walk(s)
    return needed


class ChildTranslator:
    def __init__(self, home: str, own_col: dict[int, str], own_first: int,
                 pc_row: int, copy_row: dict[int, int]):
        self.home, self.own_col, self.own_first = home, own_col, own_first
        self.pc_row, self.copy_row = pc_row, copy_row

    def translate(self, f: str, src_home: str, k: int) -> str:
        X = colname(B.FIRST_COL + k - 1)
        R = self.own_first + k - 1
        out = []
        for lit, chunk in _strip_strings(f):
            out.append(chunk if lit else REF.sub(lambda m: self._one(m, src_home, X, R), chunk))
        return "".join(out)

    def _one(self, m, src_home, X, R) -> str:
        raw = m.group(0)
        sh = (m.group("sheet") or "").rstrip("!").strip("'") or src_home
        if sh.startswith(PASS):
            return raw
        col, row, rd, rng = m.group("col"), int(m.group("row")), m.group("rd"), m.group("rng")
        if rng or m.group("cd") or col != "C":
            raise ValueError(f"non-template reference {raw!r} ({sh})")
        pc = f"{X}${self.pc_row}"
        if sh == IL:
            if row in self.own_col:
                return f"'{SC}'!${self.own_col[row]}${R}"
            if row in B.BLD_COL:
                c = B.BLD_COL[row]
                return f"INDEX('{SC}'!${c}${B.BLDG_ROWS[0]}:${c}${B.BLDG_ROWS[1]},{pc})"
            if row in B.LOC_COL:
                c = B.LOC_COL[row]
                AP = colname(B.LAST_COL)
                return (f"INDEX('{SC}'!${c}${B.LOC_ROWS[0]}:${c}${B.LOC_ROWS[1]},"
                        f"INDEX('{CS}'!$C${B.ROW_LOC}:${AP}${B.ROW_LOC},1,{pc}))")
            raise ValueError(f"IN - Location row {row} has no Schedule home")
        if sh == CS and row in self.copy_row:
            return f"{X}{self.copy_row[row]}"          # copies live on the home sheet
        if sh in (CS, BR):
            AP = colname(B.LAST_COL)
            return f"INDEX('{sh}'!$C${row}:${AP}${row},1,{pc})"
        if sh == self.home:
            return f"{X}{rd}{row}"
        raise ValueError(f"unexpected sheet reference {raw!r}")
