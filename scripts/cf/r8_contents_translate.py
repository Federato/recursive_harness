"""R-8 Phase 2b-ii -- the formula translator for per-record Contents columns.

Pure functions, no Excel. `109_r8_phase2b_repoint_contents.py` imports this and feeds
it formulas read live from the workbook; it can also be dry-run against a dump.

**The rule it implements.** Today every Contents column is one fused item, and its
formulas read column-C-style references on `IN - Location`, `CALC - CoreScratchpad`
and `CALC - Bldg Rating`. After R-8 a Contents column is one *contents record*, so
every reference is re-resolved by what level it belongs to:

    contents-level input   -> the record's own row in IN - Schedule CONTENTS
    occupancy-level input  -> INDEX into IN - Schedule OCCUPANCY CLASS by OccIdx
    building/location      -> INDEX('IN - Location'!$C{r}:$L{r}, 1, ParentCol)
    CoreScratchpad, building-level   -> INDEX(...$C{r}:$L{r}, 1, ParentCol)
    CoreScratchpad, record-level     -> a per-record copy on the Contents sheet
    Bldg Rating                      -> INDEX(...$C{r}:$L{r}, 1, ParentCol)

A CoreScratchpad row is *record-level* if it reads a contents- or occupancy-level
input, directly or through another record-level row. Those rows get copied onto the
Contents sheet (appended below row 110), one copy per record column. Everything else
stays on CoreScratchpad, keyed per building, and is read through the parent.

`TOTAL LIMIT` (row 138) is the one deliberate cut: it is rebuilt on CoreScratchpad as
a per-building roll-up over contents records, so it is building-level by construction
and everything downstream of it (the banded deductible factors) stays building-level.
"""
from __future__ import annotations

import re

IL, CS, BR, CR, SC = ("IN - Location", "CALC - CoreScratchpad", "CALC - Bldg Rating",
                      "CALC - Contents Rating", "IN - Schedule")
PASS_THROUGH_PREFIXES = ("TBL - ", "IN - Policy")

#: IN - Location row -> IN - Schedule CONTENTS column
CONT_COL = {9: "D", 45: "E", 46: "F", 69: "G", 67: "H", 97: "I", 100: "J", 103: "K"}
#: IN - Location row -> IN - Schedule OCCUPANCY CLASS column
OCC_COL = {27: "D", 32: "E", 33: "F", 34: "G", 10: "H", 30: "I"}

SCHED_CONT_FIRST = 134              # CONTENTS block data rows 134..173
SCHED_OCC = (91, 130)               # OCCUPANCY CLASS data rows
SCHED_BLDG = (48, 87)               # BUILDING data rows
RECORDS = 40
FIRST_COL, LAST_COL = 3, 42         # C..AP

#: Contents sheet rows appended below the existing chain (append, never insert)
KEY_HDR, ROW_ID, ROW_ACTIVE, ROW_OCC, ROW_PC = 112, 113, 114, 115, 116
COPY_HDR, COPY_FIRST = 118, 119

#: CoreScratchpad rows whose per-record copy is NOT a plain translation.
#: R-5 split: the Contents copy of the wind/hail chain reads the CONTENTS election
#: (IN - Location row 97 -> IN - Schedule CONTENTS.WindHailExcl), not the policy one.
CS_OVERRIDES = {
    60: "='IN - Location'!C97",
    205: "=CONCATENATE('IN - Location'!C97,C2,'IN - Location'!C64)",
}
#: Building's own copies of the same two rows read the BUILDING election (row 96).
CS_BUILDING_SPLIT = {
    60: "='IN - Location'!{c}96",
    205: "=CONCATENATE('IN - Location'!{c}96,{c}2,'IN - Location'!{c}64)",
}
#: Rows never treated as record-level: rebuilt as building-level roll-ups.
CS_CUT = {138}

REF = re.compile(
    r"(?P<sheet>'[^']+'!|[A-Za-z_][A-Za-z0-9_]*!)?"
    r"(?<![A-Za-z0-9_$.])(?P<cd>\$?)(?P<col>[A-Z]{1,3})(?P<rd>\$?)(?P<row>\d+)"
    r"(?![\d(A-Za-z_])"
    r"(?P<rng>:\$?[A-Z]{1,3}\$?\d+)?")


def colname(n: int) -> str:
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def _strip_strings(f: str) -> list[tuple[bool, str]]:
    """Split a formula into (is_string_literal, text) chunks."""
    out, i = [], 0
    for m in re.finditer(r'"(?:[^"]|"")*"', f):
        out.append((False, f[i:m.start()]))
        out.append((True, m.group(0)))
        i = m.end()
    out.append((False, f[i:]))
    return out


def refs(f: str, home: str):
    """Yield (sheet, col, row, is_range) for every cell reference in `f`."""
    for lit, chunk in _strip_strings(f):
        if lit:
            continue
        for m in REF.finditer(chunk):
            sh = (m.group("sheet") or "").rstrip("!").strip("'") or home
            yield sh, m.group("col"), int(m.group("row")), bool(m.group("rng"))


def record_level_rows(cs_formula: dict[int, str], seeds: set[int]) -> set[int]:
    """Transitive closure of CoreScratchpad rows (reachable from `seeds`) that read a
    contents- or occupancy-level input. `cs_formula` maps row -> column-C formula."""
    memo: dict[int, bool] = {}

    def is_rec(r: int, stack=()) -> bool:
        if r in memo:
            return memo[r]
        if r in CS_CUT or r in stack or r not in cs_formula:
            return False
        f = CS_OVERRIDES.get(r, cs_formula[r])
        res = False
        for sh, col, row, rng in refs(f, CS):
            if sh == IL and col == "C" and (row in CONT_COL or row in OCC_COL):
                res = True
            elif sh == CS and col == "C" and not rng and is_rec(row, stack + (r,)):
                res = True
        memo[r] = res
        return res

    needed: set[int] = set()

    def walk(r: int, seen: set[int]):
        if r in seen or r in CS_CUT or r not in cs_formula:
            return
        seen.add(r)
        if not is_rec(r):
            return
        needed.add(r)
        f = CS_OVERRIDES.get(r, cs_formula[r])
        for sh, col, row, rng in refs(f, CS):
            if sh == CS and col == "C" and not rng:
                walk(row, seen)

    seen: set[int] = set()
    for s in seeds:
        walk(s, seen)
    return needed


class Translator:
    def __init__(self, rec_rows: set[int]):
        self.rec_rows = sorted(rec_rows)
        self.copy_row = {r: COPY_FIRST + i for i, r in enumerate(self.rec_rows)}

    def translate(self, f: str, home: str, k: int) -> str:
        """Rewrite a column-C template formula for record `k` (1..40)."""
        X = colname(FIRST_COL + k - 1)
        R = SCHED_CONT_FIRST + k - 1
        out = []
        for lit, chunk in _strip_strings(f):
            if lit:
                out.append(chunk)
                continue
            out.append(REF.sub(lambda m: self._one(m, home, X, R), chunk))
        return "".join(out)

    def _one(self, m, home, X, R) -> str:
        raw = m.group(0)
        sh = (m.group("sheet") or "").rstrip("!").strip("'") or home
        if sh.startswith(PASS_THROUGH_PREFIXES):
            return raw
        col, row, rd, rng = m.group("col"), int(m.group("row")), m.group("rd"), m.group("rng")
        if sh not in (IL, CS, BR, CR):
            raise ValueError(f"unexpected sheet reference {raw!r}")
        if rng or m.group("cd") or col != "C":
            raise ValueError(f"non-template reference {raw!r} on {sh}")
        pc, oc = f"{X}${ROW_PC}", f"{X}${ROW_OCC}"
        if sh == IL:
            if row in CONT_COL:
                return f"'{SC}'!${CONT_COL[row]}${R}"
            if row in OCC_COL:
                c = OCC_COL[row]
                return f"INDEX('{SC}'!${c}${SCHED_OCC[0]}:${c}${SCHED_OCC[1]},{oc})"
            return f"INDEX('{IL}'!$C${row}:$L${row},1,{pc})"
        if sh == CS:
            if row in self.copy_row:
                return f"'{CR}'!{X}{self.copy_row[row]}" if home != CR else f"{X}{self.copy_row[row]}"
            return f"INDEX('{CS}'!$C${row}:$L${row},1,{pc})"
        if sh == BR:
            return f"INDEX('{BR}'!$C${row}:$L${row},1,{pc})"
        # sh == CR: a local reference on the Contents sheet
        return f"{X}{rd}{row}" if home == CR else f"'{CR}'!{X}{rd}{row}"


def key_formulas(k: int) -> dict[int, str]:
    """The four per-record key rows for record `k`.

    ParentCol and OccIdx fall back to 1, never 0: INDEX(row, 1, 0) returns the
    whole row, which dynamic-array Excel would try to spill. An empty record reads
    building 1 harmlessly and its premium rows are gated to zero on Active."""
    R = SCHED_CONT_FIRST + k - 1
    o0, o1 = SCHED_OCC
    b0, b1 = SCHED_BLDG
    return {
        ROW_ID: f"=IF('{SC}'!$A${R}=\"\",\"\",'{SC}'!$A${R})",
        ROW_ACTIVE: f"=IF('{SC}'!$C${R}=\"Yes\",\"Yes\",\"No\")",
        ROW_OCC: f"=IFERROR(MATCH('{SC}'!$B${R},'{SC}'!$A${o0}:$A${o1},0),1)",
        ROW_PC: f"=IFERROR(MATCH('{SC}'!$L${R},'{SC}'!$A${b0}:$A${b1},0),1)",
    }


def sched_parent_bldg(R: int) -> str:
    """IN - Schedule CONTENTS column L: the record's building, via its occupancy."""
    o0, o1 = SCHED_OCC
    return (f"=IF($B{R}=\"\",\"\",IFERROR(INDEX($B${o0}:$B${o1},"
            f"MATCH($B{R},$A${o0}:$A${o1},0)),\"\"))")


def total_limit(c: str) -> str:
    """CoreScratchpad row 138 for building column `c`: the building's own limit plus
    every active contents record whose parent building is this one, plus Special
    Class limits linked to it (C215, unchanged)."""
    s0, s1 = SCHED_CONT_FIRST, SCHED_CONT_FIRST + RECORDS - 1
    return (f"='{IL}'!{c}43+SUMIFS('{SC}'!$E${s0}:$E${s1},"
            f"'{SC}'!$L${s0}:$L${s1},'{IL}'!{c}6,'{SC}'!$C${s0}:$C${s1},\"Yes\")"
            f"+{c}215")
