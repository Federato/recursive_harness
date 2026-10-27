"""R-8 Phase 5 -- make `IN - Schedule` the input, so the old input sheets can go.

Until now the first 10 rows of every Schedule block were formulas copying
`IN - Location` / `IN - Special Class` column by column. This module decides, cell by
cell, what each of those becomes:

* **Typed input** (the old cell held a constant) -> that value.
* **Policy default** (the old cell was a formula onto `IN - Policy`) -> the same link.
  A relative `IN - Policy` reference is anchored back to column C, which is what the
  drag-fill in columns D-L was meant to say.
* **Link to another input** (`=C75`, `=C44`, `=D26` ...) -> the Schedule cell that now
  holds that input, or -- if it has no Schedule home (the three exclusion masters,
  Building #) -- the referenced cell's own content, inlined.
* **Derived** (city/state from zip, class description, construction symbol, District,
  BGII territory, occupancy severity, contents group, the Special Class symbol and
  territory, every Active flag) -> a Schedule-native formula on all 40 rows, reading
  only the Schedule and the TBL sheets. **A typed override in the old sheet wins**:
  if the old cell held a constant, it stays a constant.

IDs and ParentIDs are keys and are written as values.
"""
from __future__ import annotations

import re

from r8_contents_translate import REF, _strip_strings, colname

IL, ISC, POL, SCH = "IN - Location", "IN - Special Class", "IN - Policy", "IN - Schedule"

#: block -> (first data row, header row)
BLOCKS = {"LOC": (5, 4), "BLD": (48, 47), "OCC": (91, 90), "CON": (134, 133),
          "BI": (177, 176), "SC": (220, 219), "SCBI": (263, 262)}
N = 40

#: (source sheet, source row) -> (block, schedule column)
MAP: dict[tuple[str, int], tuple[str, str]] = {}
for blk, pairs in {
    "LOC": {4: "A", 15: "C", 13: "D", 14: "E", 22: "F", 17: "G", 18: "H", 19: "I", 20: "J",
            57: "L", 58: "M", 55: "N"},
    "BLD": {6: "A", 8: "D", 26: "E", 29: "F", 28: "G", 60: "H", 62: "I", 64: "J", 63: "K",
            23: "L", 65: "M", 43: "N", 44: "O", 50: "P", 52: "Q", 54: "R", 53: "S", 67: "T",
            68: "U", 72: "V", 73: "W", 85: "X", 24: "Y", 79: "Z", 80: "AA", 81: "AB", 82: "AC",
            83: "AD", 96: "AE", 99: "AF", 102: "AG", 92: "AH", 61: "AI"},
    "OCC": {27: "D", 32: "E", 33: "F", 34: "G", 10: "H", 30: "I"},
    "CON": {9: "D", 45: "E", 46: "F", 69: "G", 97: "I", 100: "J", 103: "K",
            87: "M", 88: "N", 89: "O", 90: "P"},
    "BI": {11: "D", 36: "E", 37: "F", 38: "G", 47: "H", 48: "I", 70: "J", 39: "K", 40: "L",
           41: "M", 98: "N", 101: "O", 104: "P"},
}.items():
    for r, c in pairs.items():
        MAP.setdefault((IL, r), (blk, c))
# Fields held by more than one block, by the block that consumes them.
EXTRA = {("LOC", "K"): (IL, 53), ("CON", "H"): (IL, 67)}
for blk, pairs in {
    "SC": {6: "A", 10: "D", 12: "E", 13: "F", 14: "G", 15: "H", 16: "I", 17: "J", 19: "K",
           21: "L", 22: "M", 24: "N", 25: "O", 27: "P", 30: "Q", 31: "R", 33: "S", 36: "T",
           49: "U", 51: "V", 53: "W"},
    "SCBI": {38: "D", 39: "E", 40: "F", 41: "G", 20: "H", 18: "I", 44: "J", 45: "K", 46: "L",
             50: "M", 52: "N", 54: "O"},
}.items():
    for r, c in pairs.items():
        MAP[(ISC, r)] = (blk, c)

#: Every field converted cell-by-cell for the 10 mirrored rows: block -> {col: source row}
FIELDS: dict[str, dict[str, tuple[str, int]]] = {}
for (sh, r), (blk, c) in MAP.items():
    FIELDS.setdefault(blk, {})[c] = (sh, r)
for (blk, c), src in EXTRA.items():
    FIELDS[blk][c] = src
#: Parent keys are values: (block, col) -> (source sheet, source row)
FIELDS["BLD"]["B"] = (IL, 4)
FIELDS["SC"]["B"] = (ISC, 4)

#: Special sources with no Schedule home, resolved to a fixed expression.
SPECIAL_INLINE = {(ISC, 32): f"'{POL}'!$C$17"}

NEW_HEADERS = {("CON", "M"): "WatchmanService", ("CON", "N"): "BurglaryAlarmType",
               ("CON", "O"): "BurglaryRange", ("CON", "P"): "BurglaryFactor"}


def row_of(blk: str, i: int) -> int:
    return BLOCKS[blk][0] + i - 1


def _rng(blk, col):
    r0 = BLOCKS[blk][0]
    return f"${col}${r0}:${col}${r0 + N - 1}"


def _parent(blk_parent, col, key):
    """INDEX(parent block column, MATCH(key, parent IDs))."""
    return f"INDEX({_rng(blk_parent, col)},MATCH({key},{_rng(blk_parent, 'A')},0))"


def derived(blk: str, col: str, r: int) -> str | None:
    """Schedule-native formula for a derived field on Schedule row r, or None."""
    loc_state_of_loc = f"$C{r}"
    if blk == "LOC":
        return {
            "B": f'=IF($C{r}="State","No","Yes")',
            "C": (f"=IFERROR(INDEX('TBL - ZipCityState'!$C$2:$C$41750,MATCH($D{r},"
                  f"'TBL - ZipCityState'!$A$2:$A$41750,0)),\"State\")"),
            "E": (f"=IFERROR(INDEX('TBL - ZipCityState'!$B$2:$B$41750,MATCH($D{r},"
                  f"'TBL - ZipCityState'!$A$2:$A$41750,0)),\"City\")"),
            "H": (f'=IF($C{r}="NY",IFERROR(INDEX(\'TBL - BGI Territories\'!$I$2:$I$6,MATCH($G{r},'
                  f"'TBL - BGI Territories'!$H$2:$H$6,0)),\"All Other\"),IF($C{r}=\"AK\","
                  f"VLOOKUP($D{r},'TBL - BGI Territories'!$K$2:$M$274,3,FALSE),"
                  f'IF($C{r}="CA","Select","Not Applicable")))'),
            "I": _bgii_terr(loc_state_of_loc, f"$D{r}"),
        }.get(col)
    if blk == "BLD":
        return {
            "C": f"=IFERROR(IF({_parent('LOC', 'C', f'$B{r}')}=\"State\",\"No\",\"Yes\"),\"No\")",
            "F": (f"=IF($E{r}=\"\",\"\",INDEX('TBL - ClassCodes'!$B$2:$B$884,"
                  f"MATCH($E{r},'TBL - ClassCodes'!$A$2:$A$884,0)))"),
            "J": (f"=IFERROR(INDEX('TBL - Derivations'!$J$2:$J$151,MATCH($I{r}&$K{r},"
                  f"'TBL - Derivations'!$G$2:$G$151,0)),\"Construction Symbol\")"),
            "AI": (f"=IFERROR(INDEX('TBL - ConstructionCodes'!$B$2:$B$8,MATCH($H{r},"
                   f"'TBL - ConstructionCodes'!$A$2:$A$8,0)),\"\")"),
        }.get(col)
    if blk == "OCC":
        bldg_class = _parent("BLD", "E", f"$B{r}")
        state = _parent("LOC", "C", _parent("BLD", "B", f"$B{r}"))
        return {
            "C": f"=IFERROR({_parent('BLD', 'C', f'$B{r}')},\"No\")",
            "F": (f"=IFERROR(VLOOKUP({state}&$E{r}&{bldg_class},"
                  f"'TBL - ContentsTables'!$CK$2:$CO$56857,5,FALSE),\"Severity\")"),
            "G": (f"=IF(IFERROR(VLOOKUP({bldg_class},'TBL - Derivations'!$AH$2:$AI$11,2,FALSE),"
                  f"\"No\")=\"No\",\"Not Applicable\",IFERROR(VLOOKUP($D{r},"
                  f"'TBL - ContentsTables'!$A$2:$B$65,2,FALSE),\"C\"))"),
        }.get(col)
    if blk == "CON":
        return {
            "C": f"=IFERROR({_parent('OCC', 'C', f'$B{r}')},\"No\")",
            "O": f"=IFERROR(VLOOKUP($N{r},'TBL - ContentsTables'!$DD$2:$DE$5,2,FALSE),\"\")",
        }.get(col)
    if blk == "BI":
        return {"C": f"=IFERROR({_parent('BLD', 'C', f'$B{r}')},\"No\")"}.get(col)
    if blk == "SC":
        state = _parent("LOC", "C", f"$B{r}")
        s0 = BLOCKS["SCBI"][0]
        return {
            "C": (f"=IF(N($K{r})+SUMIFS($H${s0}:$H${s0 + N - 1},$B${s0}:$B${s0 + N - 1},$A{r})>0,"
                  f"\"Yes\",\"No\")"),
            "M": f'=IF($L{r}="Yes",$A{r},"N/A")',
            "Q": f"=IF($A{r}=\"\",\"Select\",IFERROR({_parent('LOC', 'I', f'$B{r}')},\"Select\"))",
            "R": (f"=IF($A{r}=\"\",\"Construction Symbol\",IFERROR(VLOOKUP({state}&$D{r},"
                  f"'TBL - Special Class'!$AK$2:$AO$3335,5,FALSE),\"Construction Symbol\"))"),
        }.get(col)
    if blk == "SCBI":
        return {"C": f'=IF(N($H{r})>0,"Yes","No")'}.get(col)
    return None


def _bgii_terr(state: str, zipc: str) -> str:
    """CoreScratchpad 54-58 (BGII territory by state keying) inlined for one location."""
    typ = f"VLOOKUP({state},'TBL - Derivations'!$L$2:$M$48,2,FALSE)"
    county = (f"VLOOKUP({state}&VLOOKUP({state}&{zipc},'TBL - BGIITerritory'!$D$2:$G$33643,4,FALSE),"
              f"'TBL - Derivations'!$O$2:$R$1016,4,FALSE)")
    by_zip = f"VLOOKUP({state}&{zipc},'TBL - Derivations'!$T$2:$W$7843,4,FALSE)"
    return (f"=IFERROR(IF({typ}=\"Constant\",\"Entire State\",IF({typ}=\"County\",{county},"
            f"IF({typ}=\"ZIP\",{by_zip},\"BGII Territory\"))),\"BGII Territory\")")


DERIVED = {(b, c) for b in BLOCKS for c in ("B", "C", "E", "F", "G", "H", "I", "J", "M",
                                             "O", "Q", "R", "AI") if derived(b, c, 5)}


def lit(v) -> str:
    if isinstance(v, str):
        return '"' + v.replace('"', '""') + '"'
    return repr(v) if v is not None else '""'


class Converter:
    """Turns one old cell (sheet, row, column j) into Schedule content."""

    def __init__(self, formulas: dict, values: dict):
        self.f, self.v = formulas, values          # keyed "Sheet!R{r}C{c}"

    def content(self, sh: str, r: int, c: int, depth: int = 0):
        """('value', v) or ('formula', '=...') for old cell (r, c) on sheet sh."""
        key = f"{sh}!R{r}C{c}"
        f = self.f.get(key)
        if f is None or not str(f).startswith("="):
            return "value", self.v.get(key)
        if (sh, r) in SPECIAL_INLINE:
            return "formula", "=" + SPECIAL_INLINE[(sh, r)]
        if depth > 6:
            raise ValueError(f"reference chain too deep at {key}")
        return "formula", self._translate(str(f), sh, c, depth)

    def _translate(self, f: str, home: str, c: int, depth: int) -> str:
        out = []
        for is_lit, chunk in _strip_strings(f):
            out.append(chunk if is_lit else REF.sub(lambda m: self._one(m, home, c, depth), chunk))
        return "".join(out)

    def _one(self, m, home, c, depth) -> str:
        raw = m.group(0)
        sh = (m.group("sheet") or "").rstrip("!").strip("'") or home
        if sh.startswith("TBL - "):
            return raw
        if m.group("rng"):
            raise ValueError(f"range {raw!r} in a converted cell")
        col = sum((ord(ch) - 64) * 26 ** i for i, ch in enumerate(reversed(m.group("col"))))
        row = int(m.group("row"))
        if sh == POL:
            if m.group("cd"):
                return raw
            return f"'{POL}'!${colname(col - (c - 3))}${row}"
        if sh in (IL, ISC):
            j = col - 2                                 # record index of the referenced cell
            if (sh, row) in MAP:
                blk, sc = MAP[(sh, row)]
                return f"'{SCH}'!${sc}${row_of(blk, j)}"
            if (sh, row) in SPECIAL_INLINE:
                return SPECIAL_INLINE[(sh, row)]
            kind, val = self.content(sh, row, col, depth + 1)
            return lit(val) if kind == "value" else f"({val[1:]})"
        raise ValueError(f"reference {raw!r} cannot be carried onto the Schedule")
