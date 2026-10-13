"""Spreadsheet import: a filing typed into a sheet becomes authored files (D5).

Two layouts are read, chosen by the header row:

  * **LCM table** -- one row per company and class group, one column per
    coverage group, as filings print their exception page:
      Company | NAIC | Class group | Group I specific | Group I class |
      Group II | Broad | Special | Earthquake | ...
    plus `Class group <label>` rows listing each group's codes (or "All other
    classes"), and an optional `Source` row. This is UFG's layout.
  * **Rows** -- one authored row per sheet row:
      Company | Target | Class | Class group | Rating basis | Value | Mode |
      Cite | Note | key:<ISO key column> ...

Either way the result is the same authored files a person would write by hand,
so the compiled tables are the same (T10).

`.xlsx` is read with the standard library: an xlsx is a zip of XML, and the
engine takes no dependencies (TESTING.md).
"""
from __future__ import annotations

import csv
import io
import re
import zipfile
import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .files import FileError, authored_path, carrier_json, read_json, write_json

_X = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
_R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"


def read_sheet(path: Path) -> list[list[str]]:
    path = Path(path)
    if path.suffix.lower() == ".csv":
        text = path.read_text(encoding="utf-8-sig")
        return [[c.strip() for c in r] for r in csv.reader(io.StringIO(text))]
    if path.suffix.lower() in (".xlsx", ".xlsm"):
        return _read_xlsx(path)
    raise FileError(f"{path.name}: import reads .csv or .xlsx")


def _col_index(ref: str) -> int:
    n = 0
    for ch in re.match(r"[A-Z]+", ref).group(0):
        n = n * 26 + ord(ch) - 64
    return n - 1


def _read_xlsx(path: Path) -> list[list[str]]:
    """The first worksheet's cell text, row by row."""
    with zipfile.ZipFile(path) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")).iter(_X + "si"):
                shared.append("".join(t.text or "" for t in si.iter(_X + "t")))
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        first = next(wb.iter(_X + "sheet"))
        rid = first.get(_R + "id")
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        target = next(r.get("Target") for r in rels if r.get("Id") == rid)
        target = target.lstrip("/")
        sheet = target if target.startswith("xl/") else "xl/" + target
        rows = []
        for r in ET.fromstring(z.read(sheet)).iter(_X + "row"):
            cells: dict[int, str] = {}
            for c in r.iter(_X + "c"):
                t, v = c.get("t"), c.find(_X + "v")
                if t == "s":
                    text = shared[int(v.text)]
                elif t == "inlineStr":
                    text = "".join(x.text or "" for x in c.iter(_X + "t"))
                else:
                    text = v.text if v is not None and v.text is not None else ""
                cells[_col_index(c.get("r"))] = text.strip()
            width = max(cells) + 1 if cells else 0
            rows.append([cells.get(i, "") for i in range(width)])
        return rows


# ---------------------------------------------------------------- import

#: LCM-table column -> (target, rating basis or None)
_WIDE = {"group i specific": ("GroupI", "Specific"), "group i class": ("GroupI", "Class"),
         "group ii": ("GroupII", None), "broad": ("Broad", None),
         "special": ("Special", None), "earthquake": ("Earthquake", None)}
_TARGET_ORDER = ("GroupI", "GroupII", "Broad", "Special", "Earthquake")


def _dec(s: str, where: str) -> Decimal:
    try:
        return Decimal(s.strip())
    except (InvalidOperation, AttributeError):
        raise FileError(f"{where}: {s!r} is not a number") from None


def _us_date(s: str) -> str:
    m, d, y = (int(x) for x in s.split("/"))
    return f"{y:04d}-{m:02d}-{d:02d}"


def import_sheet(path: Path, root: Path, *, carrier: str, line: str, juris: list[str],
                 filing: str, version: int, company_map: dict[str, str],
                 new_eff: str | None = None, renewal_eff: str | None = None,
                 approved: str | None = None, serff: str | None = None,
                 overwrite: bool = False) -> tuple[list[Path], list[str]]:
    """Write authored files (and class groups) from a sheet. Returns (files, warnings)."""
    rows = read_sheet(path)
    rows = [r for r in rows if any(c for c in r)]
    if not rows:
        raise FileError(f"{path.name}: empty sheet")
    head = [h.strip().lower() for h in rows[0]]
    warnings: list[str] = []
    meta = {"source": f"imported from {Path(path).name}"}

    if "class group" in head and any(h in _WIDE for h in head):
        by_company, groups, src = _wide(rows, head, path, carrier)
    elif "target" in head and "value" in head:
        by_company, groups, src = _long(rows, head, path), {}, None
    else:
        raise FileError(f"{path.name}: header matches neither the LCM-table layout "
                        f"(Company, Class group, Group I ...) nor the rows layout "
                        f"(Company, Target, Value, Mode ...)")

    if src:
        meta["sheet_source"] = src
        sn = re.search(r"(\d{1,2}/\d{1,2}/\d{4})\s*new", src)
        sr = re.search(r"(\d{1,2}/\d{1,2}/\d{4})\s*renewal", src)
        sa = re.search(r"approved\s*(\d{1,2}/\d{1,2}/\d{4})", src)
        for label, given, found in (("new", new_eff, sn), ("renewal", renewal_eff, sr)):
            if found and given and _us_date(found.group(1)) != given:
                warnings.append(f"the sheet's Source line says {label} {_us_date(found.group(1))}; "
                                f"using {given} as given (D18: the filed PDF wins)")
        new_eff = new_eff or (sn and _us_date(sn.group(1)))
        renewal_eff = renewal_eff or (sr and _us_date(sr.group(1)))
        approved = approved or (sa and _us_date(sa.group(1)))
        if not serff:
            m = re.search(r"SERFF\s+([A-Z]{4}-\d+)", src)
            serff = m.group(1) if m else None
    if not (new_eff and renewal_eff):
        raise FileError("effective dates are needed: pass --new-eff and --renewal-eff")

    carrier_dir = Path(root) / carrier
    if groups:
        cj = carrier_json(carrier_dir) or {"carrier": carrier, "approval": {"signoffs": 1}}
        have = cj.setdefault("class_groups", {})
        for g, codes in groups.items():
            if g in have and have[g] != codes and not overwrite:
                raise FileError(f"class group {g} already exists in carrier.json with "
                                f"different codes; version the name (e.g. @v2)")
            have[g] = codes
        write_json(carrier_dir / "carrier.json", cj)

    written = []
    for name, (naic, rws) in by_company.items():
        code = company_map.get(name)
        if not code:
            raise FileError(f"no company code for {name!r}: pass --company \"{name}=CODE\"")
        cdir = carrier_dir / code
        if not (cdir / "company.json").exists():
            write_json(cdir / "company.json", {"code": code, "name": name,
                                               **({"naic": naic} if naic else {})})
        out = {"filing": filing, "company": code, "line": line, "juris": juris,
               "version": version, "status": "draft"}
        if serff:
            out["serff"] = serff
        if approved:
            out["approved"] = approved
        out.update(new_eff=new_eff, renewal_eff=renewal_eff, rows=rws, meta=meta)
        p = authored_path(cdir, filing, version)
        if p.exists() and not overwrite:
            raise FileError(f"{p} exists; a filing version is never overwritten "
                            f"(use the next version, or --overwrite for a draft)")
        if p.exists() and read_json(p).get("status") == "approved":
            raise FileError(f"{p} is approved; it cannot be overwritten")
        write_json(p, out)
        written.append(p)
    return written, warnings


def _wide(rows, head, path, carrier):
    ci = head.index("company")
    gi = head.index("class group")
    ni = head.index("naic") if "naic" in head else None
    cols = {i: _WIDE[h] for i, h in enumerate(head) if h in _WIDE}

    groups: dict[str, list[str]] = {}
    all_other: set[str] = set()
    src = None
    data = []
    for n, r in enumerate(rows[1:], start=2):
        first = r[0] if r else ""
        m = re.match(r"(?i)class group\s+(\S+)$", first)
        if m:
            label, body = m.group(1), (r[1] if len(r) > 1 else "")
            if "all other" in body.lower():
                all_other.add(label)
            else:
                groups[f"{carrier}-{label}@v1"] = [c.strip() for c in body.split(",") if c.strip()]
            continue
        if first.lower() == "source":
            src = r[1] if len(r) > 1 else ""
            continue
        data.append((n, r))

    by_company: dict[str, tuple[str | None, list]] = {}
    per: dict[str, list] = {}
    naic: dict[str, str] = {}
    for n, r in data:
        name = r[ci]
        label = r[gi]
        if label not in all_other and f"{carrier}-{label}@v1" not in groups:
            raise FileError(f"{path.name} row {n}: class group {label!r} has no "
                            f"'Class group {label}' row")
        per.setdefault(name, []).append((n, label, r))
        if ni is not None and r[ni]:
            naic[name] = r[ni]

    for name, entries in per.items():
        # "all other classes" first: it is the least specific row, as a person writes it
        entries.sort(key=lambda e: (e[1] not in all_other))
        out = []
        for tgt in _TARGET_ORDER:
            cells = {}            # label -> {basis: (value, row n)}
            for n, label, r in entries:
                for i, (t, b) in cols.items():
                    if t == tgt and i < len(r) and r[i]:
                        cells.setdefault(label, {})[b] = (_dec(r[i], f"{path.name} row {n}"), n)
            if not cells:
                continue
            labels = [e[1] for e in entries if e[1] in cells]
            vals = {lb: {b: v for b, (v, _) in cells[lb].items()} for lb in labels}
            if tgt == "Earthquake" and len({tuple(v.values()) for v in vals.values()}) == 1:
                lb = labels[0]
                (v, n), = cells[lb].values()
                out.append(_row("LCM:Earthquake", {}, v, f"{path.name} rows "
                                + ", ".join(str(cells[x][None][1]) for x in labels)))
                continue
            for lb in labels:
                scope = {} if lb in all_other else {"class_group": f"{carrier}-{lb}@v1"}
                bv = cells[lb]
                if None in bv:
                    v, n = bv[None]
                    out.append(_row(f"LCM:{tgt}", scope, v, f"{path.name} row {n}"))
                elif len({v for v, _ in bv.values()}) == 1:
                    v, n = next(iter(bv.values()))
                    out.append(_row(f"LCM:{tgt}", scope, v, f"{path.name} row {n}"))
                else:
                    for b in ("Specific", "Class"):
                        if b in bv:
                            v, n = bv[b]
                            out.append(_row(f"LCM:{tgt}", dict(scope, rating_basis=b), v,
                                            f"{path.name} row {n}"))
        by_company[name] = (naic.get(name), out)
    return by_company, groups, src


def _long(rows, head, path):
    def col(name):
        return head.index(name) if name in head else None
    ci, ti, vi, mi = col("company"), col("target"), col("value"), col("mode")
    cl, cg, rb = col("class"), col("class group"), col("rating basis")
    cite, note = col("cite"), col("note")
    keys = {i: h[4:].strip() for i, h in enumerate(rows[0]) if h.lower().startswith("key:")}
    by: dict[str, tuple[None, list]] = {}
    for n, r in enumerate(rows[1:], start=2):
        g = lambda i: r[i] if i is not None and i < len(r) else ""
        scope = {}
        if g(cl):
            scope["class"] = g(cl)
        if g(cg):
            scope["class_group"] = g(cg)
        if g(rb):
            scope["rating_basis"] = g(rb)
        for i, k in keys.items():
            if g(i):
                scope[k] = g(i)
        row = _row(g(ti), scope, _dec(g(vi), f"{path.name} row {n}"),
                   g(cite) or f"{path.name} row {n}", mode=g(mi) or "replace")
        if g(note):
            row["note"] = g(note)
        by.setdefault(g(ci), (None, []))[1].append(row)
    return by


def _row(target, scope, value, cite, mode="replace") -> dict:
    return {"target": target, "scope": scope, "value": value, "mode": mode, "cite": cite}
