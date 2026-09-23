"""R-8 Phase 5 -- `IN - Schedule` becomes the input; `IN - Location` and
`IN - Special Class` are retired.

Stages, each gated; the script aborts WITHOUT saving on any failure:

1. **Convert the Schedule** (`r8_phase5_schedule.py`): typed values stay typed,
   policy defaults keep their `IN - Policy` link, derived fields get Schedule-native
   formulas on all 40 rows (typed overrides kept), keys become values. CONTENTS gains
   M..P (watchman service, burglary alarm type / range / factor), the only inputs the
   Schedule did not yet carry. Dropdown validations are carried across.
   GATE: premiums and every calc-sheet value unchanged; Schedule values unchanged on
   every active record.
2. **Decoupling proof**: the old sheets' inputs are scrambled in memory; no premium
   may move.
3. **Repoint and retire**: Contents rows 92/93 -> Schedule CONTENTS M/P; the 174 R-3
   checks mask on each sheet's own Active key row (widened to 40 records) instead of
   `IN_Loc_State`/`IN_SC_State`; the Diagnostics traps and edition table read the
   Schedule; CoreScratchpad rows that still read the old sheets and that nothing
   live reaches are cleared; the 123 names onto the old sheets are deleted; the two
   sheets are deleted.
   GATE: premiums, calc values, Diagnostics traps/editions unchanged; no `#REF!` in
   any formula or name.
4. **Moving**: a typed Schedule limit moves Building; a zip change re-derives the
   city; a construction-type change re-derives the symbol.
Then save, reopen, re-verify.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import r8_phase5_schedule as P                                     # noqa: E402
import r8_building_translate as B                                  # noqa: E402
from r8_contents_translate import colname                          # noqa: E402
from importlib import import_module                                # noqa: E402

p4a = import_module("112_r8_phase4a_building")
Gate, prem, show, grid, diff_rows, as_input, calc = (p4a.Gate, p4a.prem, p4a.show, p4a.grid,
                                                     p4a.diff_rows, p4a.as_input, p4a.calc)
CS, BR, CR, BI, SCC, DG = ("CALC - CoreScratchpad", "CALC - Bldg Rating", "CALC - Contents Rating",
                           "CALC - BI Rating", "CALC - Special Class", "OUT - Diagnostics")
OLD = (P.IL, P.ISC)
CALC_SPANS = {BR: 113, CR: 168, BI: 102, SCC: 219, CS: 285}
ACTIVE = {BR: "'CALC - CoreScratchpad'!$C$284:$AP$284", CR: "$C$114:$AP$114",
          BI: "$C$80:$AP$80"}
CONST_F = re.compile(r'^=\(?("(?:[^"]|"")*"|-?\d+(?:\.\d+)?)\)?$')


def com_retry(fn, tries=30):
    """Excel answers 'Call was rejected by callee' while busy; wait and retry."""
    import time
    import pywintypes
    for i in range(tries):
        try:
            return fn()
        except pywintypes.com_error as e:
            if e.args[0] != -2147418111 or i == tries - 1:
                raise
            time.sleep(1)


def calc_snapshot(wb):
    return {s: grid(wb.Worksheets(s), n, 42) for s, n in CALC_SPANS.items()}


def active_cols(wb, sheet, row):
    """0-based columns (from C) whose record is active, for a calc-sheet row."""
    if sheet == SCC:
        ws, key = wb.Worksheets(SCC), (162 if row < 88 else 167)
    elif sheet == CR:
        ws, key = wb.Worksheets(CR), 114
    elif sheet == BI:
        ws, key = wb.Worksheets(BI), 80
    else:
        ws, key = wb.Worksheets(CS), 284
    vals = ws.Range(ws.Cells(key, 3), ws.Cells(key, 42)).Value[0]
    return {i for i, v in enumerate(vals) if v == "Yes"}


def compare_calc(wb, snap, now, skip_cs_rows=()):
    """Active records must be identical; inactive differences are listed, not hidden."""
    live, idle = [], []
    for s in snap:
        for r in diff_rows(snap[s], now[s]):
            if s == CS and r in skip_cs_rows:
                continue
            act = active_cols(wb, s, r)
            for c, (a, b) in enumerate(zip(snap[s][r - 1], now[s][r - 1])):
                if a != b:
                    (live if c in act else idle).append((s, r, colname(3 + c), a, b))
    return live, idle


def read_old(wb):
    f, v = {}, {}
    for sh, last in ((P.IL, 104), (P.ISC, 54)):
        ws = wb.Worksheets(sh)
        rf = ws.Range(ws.Cells(1, 1), ws.Cells(last, 12)).Formula
        rv = ws.Range(ws.Cells(1, 1), ws.Cells(last, 12)).Value
        for i in range(last):
            for j in range(12):
                key = f"{sh}!R{i + 1}C{j + 1}"
                if rf[i][j] not in (None, ""):
                    f[key] = rf[i][j]
                v[key] = rv[i][j]
    return f, v


def write(cell, kind, x):
    if kind == "formula":
        m = CONST_F.match(x)
        if m:
            t = m.group(1)
            cell.Value = as_input(t[1:-1].replace('""', '"')) if t.startswith('"') else float(t)
            return
        cell.Formula = x
    else:
        cell.Value = as_input(x) if x is not None else None


def convert_schedule(app, wb) -> list[str]:
    sc = wb.Worksheets(P.SCH)
    old_f, old_v = read_old(wb)
    cv = P.Converter(old_f, old_v)
    notes = []
    for (blk, col), name in P.NEW_HEADERS.items():
        if sc.Range(f"{col}{P.BLOCKS[blk][1]}").Value not in (None, ""):
            raise Gate(f"Schedule {col}{P.BLOCKS[blk][1]} not empty")
        sc.Range(f"{col}{P.BLOCKS[blk][1]}").Value = name

    for blk, (r0, _) in P.BLOCKS.items():
        keys = ["A"] if blk == "LOC" else ["A", "B"]
        for i in range(1, 11):
            r = r0 + i - 1
            for k in keys:
                cell = sc.Range(f"{k}{r}")
                cell.Value = as_input(cell.Value)
        fields = dict(P.FIELDS.get(blk, {}))
        derived_cols = sorted({c for (b, c) in P.DERIVED if b == blk})
        for col in derived_cols:
            src = fields.get(col)
            fs = []
            for i in range(1, P.N + 1):
                r = r0 + i - 1
                if i <= 10 and src and not str(old_f.get(f"{src[0]}!R{src[1]}C{2 + i}", "=")).startswith("="):
                    fs.append(None)                         # typed override: written below
                else:
                    fs.append(P.derived(blk, col, r))
            for i, f in enumerate(fs, start=1):
                r = r0 + i - 1
                if f is None:
                    v = old_v.get(f"{src[0]}!R{src[1]}C{2 + i}")
                    sc.Range(f"{col}{r}").Value = as_input(v)
                    notes.append(f"{blk} {col} record {i}: typed override kept ({v!r})")
                else:
                    sc.Range(f"{col}{r}").Formula = f
        for col, (sh, srow) in fields.items():
            if col in keys or (blk, col) in P.DERIVED:
                continue
            for i in range(1, 11):
                kind, x = cv.content(sh, srow, 2 + i)
                write(sc.Range(f"{col}{r0 + i - 1}"), kind, x)
    return notes


def copy_validations(wb) -> list[str]:
    old = {P.IL: wb.Worksheets(P.IL), P.ISC: wb.Worksheets(P.ISC)}
    sc = wb.Worksheets(P.SCH)
    done, failed = 0, []
    for (sh, srow), (blk, col) in list(P.MAP.items()) + [((s, r), b) for b, (s, r) in P.EXTRA.items()]:
        try:
            v = old[sh].Cells(srow, 3).Validation
            if v.Type != 3:
                continue
            f1 = str(v.Formula1)
        except Exception:                                   # noqa: BLE001
            continue
        r0 = P.BLOCKS[blk][0]
        per_row = None
        if "C15" in f1 and blk == "LOC":
            per_row = lambda r, f1=f1: f1.replace("C15", f"$C{r}")      # noqa: E731
        elif "CoreScratchpad'!C52" in f1:
            per_row = lambda r: f"=INDIRECT(VLOOKUP($AI{r},'TBL - Derivations'!$D$2:$E$7,2,FALSE))"  # noqa: E731
        elif re.search(r"(?<![$A-Z])[A-Z]{1,2}\d+(?![\d(])", f1.replace("$", "§")) and "!" not in f1:
            failed.append(f"{blk}.{col}: relative validation {f1!r} not carried")
            continue
        try:
            if per_row:
                skipped = []
                for r in range(r0, r0 + P.N):
                    rng = sc.Range(f"{col}{r}")
                    rng.Validation.Delete()
                    try:
                        rng.Validation.Add(3, 1, 1, per_row(r))
                    except Exception:                       # noqa: BLE001
                        skipped.append(r)
                if skipped:
                    failed.append(f"{blk}.{col}: dependent dropdown not added on {len(skipped)} rows "
                                  f"whose list does not resolve yet (blank records)")
            else:
                rng = sc.Range(f"{col}{r0}:{col}{r0 + P.N - 1}")
                rng.Validation.Delete()
                rng.Validation.Add(3, 1, 1, f1)
            done += 1
        except Exception as e:                              # noqa: BLE001
            failed.append(f"{blk}.{col}: {f1!r} ({e})")
    return [f"{done} dropdowns carried"] + failed


def all_formulas(wb, skip=()):
    out = {}
    for ws in wb.Worksheets:
        name = ws.Name
        if name in skip or name.startswith("TBL - "):
            continue
        ur = ws.UsedRange
        f = ur.Formula
        if not isinstance(f, tuple):
            f = ((f,),)
        for i, row in enumerate(f):
            for j, x in enumerate(row):
                if isinstance(x, str) and x.startswith("="):
                    out[(name, ur.Row + i, ur.Column + j)] = x
    return out


def live_cs_rows(wb) -> tuple[set[int], dict[int, list[str]]]:
    """CoreScratchpad rows reachable from any live consumer (every sheet except the old
    input sheets and CoreScratchpad itself), and CoreScratchpad's formulas by row."""
    live = all_formulas(wb, skip=OLD + (CS,))
    rows = {38}                                             # a Schedule dropdown reads $C$38
    pat = re.compile(r"'CALC - CoreScratchpad'!\$?[A-Z]+\$?(\d+)(?::\$?[A-Z]+\$?(\d+))?")
    for x in live.values():
        for m in pat.finditer(x):
            a = int(m.group(1))
            rows |= set(range(a, int(m.group(2) or a) + 1))
    cs_f = {}
    for (name, r, c), x in all_formulas(wb).items():
        if name == CS:
            cs_f.setdefault(r, []).append(x)
    local = re.compile(r"(?<![A-Za-z!$'])\$?[A-Z]{1,2}\$?(\d+)(?::\$?[A-Z]{1,2}\$?(\d+))?")
    frontier = set(rows)
    while frontier:
        nxt = set()
        for r in frontier:
            for x in cs_f.get(r, []):
                body = re.sub(r"'[^']+'![$A-Z]+\$?\d+(:\$?[A-Z]+\$?\d+)?", "", x)
                for m in local.finditer(body):
                    a = int(m.group(1))
                    nxt |= set(range(a, int(m.group(2) or a) + 1))
                for m in pat.finditer(x):
                    a = int(m.group(1))
                    nxt |= set(range(a, int(m.group(2) or a) + 1))
        frontier = nxt - rows
        rows |= nxt
    return rows, cs_f


def translate_live_cs(wb) -> list[int]:
    """Live CoreScratchpad rows that still read IN - Location: building-level rows that
    Contents / BI read through ParentCol but that were outside Building's own chain in
    4a (e.g. 155 Broad Rate, 183 Special Territory). Translated with the 4a rule."""
    rows, cs_f = live_cs_rows(wb)
    cs = wb.Worksheets(CS)
    todo = sorted(r for r in rows if any(f"'{o}'!" in x for x in cs_f.get(r, []) for o in OLD))
    tr = B.Translator()
    for r in todo:
        tpl = str(cs.Cells(r, 3).Formula)
        try:
            fs = tuple(tr.translate(tpl, CS, k) for k in range(1, B.RECORDS + 1))
        except ValueError as e:
            raise Gate(f"live CoreScratchpad row {r} cannot move to the Schedule: {e}")
        cs.Range(cs.Cells(r, 3), cs.Cells(r, B.LAST_COL)).Formula = (fs,)
    return todo


def retire_corescratchpad(wb) -> list[int]:
    """Clear CoreScratchpad rows that read the old sheets and that nothing live reaches."""
    rows, cs_f = live_cs_rows(wb)
    cs = wb.Worksheets(CS)
    reads_old = {r for r, xs in cs_f.items() if any(any(f"'{o}'!" in x for o in OLD) for x in xs)}
    bad = sorted(reads_old & rows)
    if bad:
        raise Gate(f"CoreScratchpad rows still live AND reading the old sheets: {bad}")
    # Transitively: a dead row that feeds off a retired row would only show errors.
    local = re.compile(r"(?<![A-Za-z!$'])\$?[A-Z]{1,2}\$?(\d+)(?::\$?[A-Z]{1,2}\$?(\d+))?")
    self_ref = re.compile(r"'CALC - CoreScratchpad'!\$?[A-Z]+\$?(\d+)(?::\$?[A-Z]+\$?(\d+))?")
    retired = set(reads_old)
    changed = True
    while changed:
        changed = False
        for r, xs in cs_f.items():
            if r in retired or r in rows:
                continue
            deps = set()
            for x in xs:
                body = re.sub(r"'[^']+'![$A-Z]+\$?\d+(:\$?[A-Z]+\$?\d+)?", "", x)
                for m in local.finditer(body):
                    a = int(m.group(1))
                    deps |= set(range(a, int(m.group(2) or a) + 1))
                for m in self_ref.finditer(x):          # 'CALC - CoreScratchpad'!C172
                    a = int(m.group(1))
                    deps |= set(range(a, int(m.group(2) or a) + 1))
            if deps & retired:
                retired.add(r)
                changed = True
    for r in sorted(retired):
        com_retry(lambda r=r: cs.Range(cs.Cells(r, 3), cs.Cells(r, 42)).ClearContents())
        com_retry(lambda r=r: setattr(cs.Cells(r, 1), "Value", "retired R-8 P5"))
    return sorted(retired)


def repoint(wb) -> dict:
    counts = {}
    cr = wb.Worksheets(CR)
    n = 0
    for k in range(1, 41):
        c = 2 + k
        for row, src, dst in ((92, 87, "M"), (93, 90, "P")):
            f = str(cr.Cells(row, c).Formula)
            X = colname(c)
            nf = f.replace(f"INDEX('IN - Location'!$C${src}:$L${src},1,{X}$116)", f"'{P.SCH}'!${dst}${133 + k}")
            if nf != f:
                cr.Cells(row, c).Formula = nf
                n += 1
    if n != 80:
        raise Gate(f"expected 80 watchman/burglary cells on Contents, repointed {n}")
    counts["contents 92/93"] = n

    # CoreScratchpad 215 (Special Class limit included in a building -> TOTAL LIMIT) is
    # live and reads IN - Special Class rows 19/22 as whole-row ranges.
    cs = wb.Worksheets(CS)
    n = 0
    for c in range(3, 43):
        f = str(cs.Cells(215, c).Formula)
        nf = (f.replace("'IN - Special Class'!$C$22:$L$22", f"'{P.SCH}'!$M$220:$M$259")
               .replace("'IN - Special Class'!$C$19:$L$19", f"'{P.SCH}'!$K$220:$K$259"))
        if nf != f:
            cs.Cells(215, c).Formula = nf
            n += 1
    if n == 0:
        raise Gate("CoreScratchpad 215 did not read IN - Special Class as expected")
    counts["CS215"] = n

    pat = re.compile(r'\((IN_Loc_State|IN_SC_State)<>"State"\)\*\(C(\d+):L(\d+)=0\)')
    total = 0
    for sheet in (BR, CR, BI, SCC):
        ws = wb.Worksheets(sheet)
        col = ws.Range("AR1:AR300").Formula
        for i, (f,) in enumerate(col, start=1):
            if not (isinstance(f, str) and ("IN_Loc_State" in f or "IN_SC_State" in f)):
                continue
            act = ACTIVE.get(sheet) or ("$C$162:$AP$162" if i < 88 else "$C$167:$AP$167")
            nf = pat.sub(lambda m: f'({act}="Yes")*(C{m.group(2)}:AP{m.group(3)}=0)', f)
            if "IN_Loc_State" in nf or "IN_SC_State" in nf:
                raise Gate(f"{sheet}!AR{i}: check not recognised: {f!r}")
            ws.Range(f"AR{i}").Formula = nf
            total += 1
    counts["R-3 checks"] = total

    dg = wb.Worksheets(DG)
    sub = {
        '(IN_Loc_State<>"State")': f"('{P.SCH}'!$C$48:$C$87=\"Yes\")",
        "IN_Loc_ConstrCode": f"'{P.SCH}'!$H$48:$H$87",
        "IN_Loc_BuildingLimit": f"'{P.SCH}'!$N$48:$N$87",
        "IN_Loc_BuildingClassCode": f"'{P.SCH}'!$E$48:$E$87",
        "IN_Loc_BuildingCovType": f"'{P.SCH}'!$D$48:$D$87",
        "IN_Loc_AddlInsurableIntOption": f"'{P.SCH}'!$AH$48:$AH$87",
        "IN_SC_InclInBlanket": f"'{P.SCH}'!$F$220:$F$259",
    }
    nd = 0
    for r in list(range(13, 17)) + list(range(40, 50)):
        for c in (2, 3):
            f = str(dg.Cells(r, c).Formula)
            if not any(k in f for k in list(sub) + ["IN_Loc_State"]):
                continue
            nf = f
            for a, b in sub.items():
                nf = nf.replace(a, b)
            nf = re.sub(r"INDEX\(IN_Loc_State,1,(\d+)\)", rf"INDEX('{P.SCH}'!$C$5:$C$44,\1)", nf)
            if "IN_Loc_" in nf or "IN_SC_" in nf:
                raise Gate(f"Diagnostics R{r}C{c} not fully repointed: {nf!r}")
            dg.Cells(r, c).Formula = nf
            nd += 1
    counts["diagnostics"] = nd
    return counts


def migrate(app, wb):
    calc(app)
    base = prem(wb)
    show("baseline", base)
    snap = calc_snapshot(wb)
    sc = wb.Worksheets(P.SCH)
    sched0 = grid(sc, 302, 35, c0=1)
    dg0 = grid(wb.Worksheets(DG), 49, 5, c0=1)

    # ---- 1. convert ------------------------------------------------------------------
    notes = convert_schedule(app, wb)
    for n in notes:
        print("   ", n)
    for line in copy_validations(wb):
        print("    validation:", line)
    moved_cs = translate_live_cs(wb)
    print(f"    live CoreScratchpad rows moved off IN - Location (4a rule): {moved_cs}")
    calc(app)
    after = prem(wb)
    show("after Schedule conversion", after)
    if after != base:
        raise Gate("premiums moved on the Schedule conversion")
    live, idle = compare_calc(wb, snap, calc_snapshot(wb))
    for x in idle:
        print("     inactive-slot difference:", x)
    if live:
        raise Gate(f"calc values changed on ACTIVE records: {live[:10]}")
    sched1 = grid(sc, 302, 35, c0=1)
    active_rows = {r for blk, (r0, _) in P.BLOCKS.items() for r in range(r0, r0 + 10)
                   if sched1[r - 1][1 if blk == "LOC" else 2] == "Yes"}
    moved = [(r, colname(c + 1), sched0[r - 1][c], sched1[r - 1][c])
             for r in range(1, 303) for c in range(35)
             if sched0[r - 1][c] != sched1[r - 1][c] and not (133 <= r <= 173 and 12 <= c <= 15)]
    live_moves = [m for m in moved if m[0] in active_rows]
    if live_moves:
        raise Gate(f"Schedule values changed on ACTIVE records: {live_moves[:10]}")
    print(f"  GATE 1: premiums + every ACTIVE calc value unchanged; Schedule unchanged on all "
          f"{len(active_rows)} active records ({len(moved)} cosmetic changes on inactive/blank rows)")

    # ---- 2. decoupling proof ------------------------------------------------------------
    il, isc = wb.Worksheets(P.IL), wb.Worksheets(P.ISC)
    for r in (43, 44, 45, 46, 47, 22, 26, 60):
        for c in range(3, 13):
            il.Cells(r, c).Value = 987654
    il.Range("C13:L13").Value = 10001
    for r in (19, 20, 42, 27):
        for c in range(3, 13):
            isc.Cells(r, c).Value = 987654
    calc(app)
    if prem(wb) != base:
        raise Gate(f"premiums moved when the OLD sheets were scrambled: {prem(wb)}")
    print("  GATE 2: old input sheets scrambled -> no premium moved; nothing prices on them")

    # ---- 3. repoint, retire, delete --------------------------------------------------------
    counts = repoint(wb)
    print(f"  3. repointed: {counts}")
    retired = retire_corescratchpad(wb)
    print(f"     CoreScratchpad rows retired (dead: read the old sheets, or fed only off rows that did): "
          f"{len(retired)} -> {retired[0]}..{retired[-1]}")
    used = set()
    live_text = "\n".join(all_formulas(wb, skip=OLD).values())
    dead = [n for n in wb.Names if any(o in str(n.RefersTo) for o in OLD)]
    for n in dead:
        nm = str(n.Name).split("!")[-1]
        if re.search(rf"(?<![A-Za-z_]){re.escape(nm)}(?![A-Za-z_0-9])", live_text):
            used.add(nm)
    if used:
        raise Gate(f"names onto the old sheets are still used: {sorted(used)}")
    for n in dead:
        com_retry(n.Delete)
    print(f"     {len(dead)} names onto the old sheets deleted")
    app.DisplayAlerts = False
    com_retry(lambda: wb.Worksheets(P.IL).Delete())
    com_retry(lambda: wb.Worksheets(P.ISC).Delete())
    print("     IN - Location and IN - Special Class deleted")

    calc(app)
    final = prem(wb)
    show("after retirement", final)
    if final != base:
        raise Gate("premiums moved after retirement")
    live, idle = compare_calc(wb, snap, calc_snapshot(wb), skip_cs_rows=set(retired))
    print(f"     inactive-slot differences after retirement: {len(idle)}")
    if live:
        raise Gate(f"calc values changed on ACTIVE records after retirement: {live[:10]}")
    dg1 = grid(wb.Worksheets(DG), 49, 5, c0=1)
    dg_moved = diff_rows(dg0, dg1)
    if [r for r in dg_moved if r >= 13]:
        raise Gate(f"Diagnostics traps/editions changed: rows {dg_moved}")
    refs = [k for k, x in all_formulas(wb).items() if "#REF!" in x]
    bad_names = [n.Name for n in wb.Names if "#REF" in str(n.RefersTo)]
    if refs or bad_names:
        raise Gate(f"#REF! left behind: {refs[:10]} names {bad_names[:10]}")
    print(f"  GATE 3: premiums + calc values unchanged; Diagnostics traps/editions unchanged"
          f"{'' if not dg_moved else f' (R-3 roll-up rows {dg_moved} changed: mask now = Active records)'}; "
          f"no #REF! anywhere")
    if dg_moved:
        for r in dg_moved:
            print(f"     Diagnostics row {r}: {dg0[r - 1]} -> {dg1[r - 1]}")

    # ---- 4. moving ---------------------------------------------------------------------------
    def poke(cell, v):
        f = cell.Formula
        cell.Value = v
        app.CalculateFull()
        return f

    b0 = prem(wb)["OUT_Prem_Building"]
    f = poke(sc.Range("N48"), sc.Range("N48").Value + 100000)
    b1 = prem(wb)["OUT_Prem_Building"]
    sc.Range("N48").Formula = f
    city0 = sc.Range("E6").Value
    f = poke(sc.Range("D6"), 10001)
    city1 = sc.Range("E6").Value
    sc.Range("D6").Formula = f
    sym0 = sc.Range("J49").Value
    f = poke(sc.Range("I49"), "'Frame")
    sym1 = sc.Range("J49").Value
    sc.Range("I49").Formula = f
    app.CalculateFull()
    print(f"  GATE 4: typed Schedule limit +100k -> Building {b0:g} -> {b1:g}; zip 10001 -> city "
          f"{city0!r} -> {city1!r}; ConstrType Frame -> symbol {sym0!r} -> {sym1!r}")
    if b1 == b0 or city1 == city0 or sym1 == sym0:
        raise Gate("the Schedule is not live as an input")
    if prem(wb) != base:
        raise Gate("did not restore")
    return base


def main() -> int:
    if p4a.TARGET.name.lower() == p4a.FORBIDDEN:
        sys.exit("ABORT: refusing to write to the live rater.")
    pre = p4a.excel_pids()
    if pre:
        sys.exit(f"ABORT: Excel running {pre}")
    import win32com.client
    ok, base = False, None
    app = win32com.client.DispatchEx("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    app.EnableEvents = False
    wb = None
    try:
        wb = app.Workbooks.Open(str(p4a.TARGET), UpdateLinks=0)
        app.Calculation = -4135
        app.ScreenUpdating = False
        try:
            base = migrate(app, wb)
            ok = True
        except Gate as e:
            print(f"\n  GATE FAILED: {e}\n  NOT saving.")
        if ok:
            app.Calculation = -4105
            app.CalculateFull()
            wb.Save()
            print("  saved.")
        wb.Close(SaveChanges=False)
        wb = None
    finally:
        try:
            if wb is not None:
                wb.Close(SaveChanges=False)
        except Exception:                                   # noqa: BLE001
            pass
        app.Quit()
        del app
        p4a.reap_orphans(set(pre))
    if not ok:
        return 1

    app = win32com.client.DispatchEx("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    wb = None
    try:
        wb = app.Workbooks.Open(str(p4a.TARGET), UpdateLinks=0, ReadOnly=True)
        app.Calculation = -4135
        app.CalculateFull()
        final = prem(wb)
        show("after reopen", final)
        sheets = [w.Name for w in wb.Worksheets]
        checks = {
            "premiums": final == base,
            "old sheets gone": not any(o in sheets for o in OLD),
            "no #REF! formulas": not [k for k, x in all_formulas(wb).items() if "#REF!" in x],
            "no #REF names": not [n.Name for n in wb.Names if "#REF" in str(n.RefersTo)],
            "CONTENTS.WatchmanService header": wb.Worksheets(P.SCH).Range("M133").Value == "WatchmanService",
        }
        for k, v in checks.items():
            print(f"    {'ok ' if v else 'FAIL'} {k}")
        ok = all(checks.values())
        wb.Close(SaveChanges=False)
        wb = None
    finally:
        try:
            if wb is not None:
                wb.Close(SaveChanges=False)
        except Exception:                                   # noqa: BLE001
            pass
        app.Quit()
        del app
        p4a.reap_orphans(set(pre))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
