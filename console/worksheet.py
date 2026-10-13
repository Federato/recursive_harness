"""The worksheet map (TC-20): our engine's fields aligned to ISO's response fields, per line, by stable ID.

Both lines run on the one interpreter, and both already compare with ISO the same way (`scripts/diff_payload.py` for
GL, `157_` / `154_` for CP): every leaf of ISO's response body against every leaf of our rated tree, paths put in one
shape. This module is that alignment, kept in one place for the console, plus what the comparisons never needed:

  * **stable ID**: the path with every index removed (`/CommercialProperty/CommercialPropertyLocation/
    CommercialPropertyBuilding/BuildingBasicGroupICoverage/Premium`), the same field on every risk;
  * **row**: the path with its indices kept, so two buildings are two rows;
  * **ERC source**: the rule file and package that wrote the field, and the tables read just before it, from the
    interpreter's trace (`write` entries carry the node, rule file and package);
  * **order**: when our engine wrote it, so the first divergent step can be found (TC-21).

`console/config/worksheet.json` (built by `scripts/tc/tc20_build_worksheet.py`) is the versioned catalog of stable IDs
per line: which ISO publishes, which we write, which rules write them.
"""
from __future__ import annotations

import json
import re
import sys
from decimal import Decimal, InvalidOperation
from functools import lru_cache
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = Path(__file__).resolve().parent / "config" / "worksheet.json"
_IDX = re.compile(r"\[\d+\]")

for _p in (ROOT, ROOT / "scripts", ROOT / "scripts" / "cf"):
    if str(_p) not in sys.path:
        sys.path.append(str(_p))


def normalise(path: str) -> str:
    """`diff_payload.normalise`: drop `[0]` and the `XTable` containers ISO's response does not emit."""
    parts = [p for p in path.replace("[0]", "").split("/") if p]
    out = []
    for i, p in enumerate(parts):
        nxt = parts[i + 1] if i + 1 < len(parts) else ""
        if p.endswith("Table") and p[:-5] == nxt.split("[")[0]:
            continue
        out.append(p)
    return "/" + "/".join(out)


def stable_id(path: str) -> str:
    return _IDX.sub("", path)


def record_of(path: str) -> str:
    return path.rsplit("/", 1)[0] or "/"


def _num(v):
    if isinstance(v, bool):
        return None
    try:
        return Decimal(str(v))
    except (InvalidOperation, ValueError, TypeError):
        return None


_US_DATE = re.compile(r"^(\d{2})/(\d{2})/(\d{4})$")
_ISO_DATE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})(T00:00:00(\.0+)?Z?)?$")
_GUID = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")


def _date(v):
    s = str(v)
    m = _US_DATE.match(s)
    if m:
        return (m.group(3), m.group(1), m.group(2))
    m = _ISO_DATE.match(s)
    return (m.group(1), m.group(2), m.group(3)) if m else None


_CODE_FIELD = re.compile(r"(Code|Indicator|Ind|Id|Number|Subline\w*|Identification\w*)$")


def kind(v, field: str = "") -> str:
    """'number' | 'code' | 'date' | 'id' | 'text': how a value is compared, and whether it can be a rating step.
    A field named as a code (`RatingIdentificationCode`, `Subline...`, `...StatCode`) is a code even when its value
    looks numeric: it identifies, it is not arithmetic, and Trace Diff does not look for the first divergence in it."""
    if field and _CODE_FIELD.search(field):
        return "code"
    if v is None:
        return "text"
    if _num(v) is not None:
        return "number"
    if _date(v):
        return "date"
    if _GUID.match(str(v)):
        return "id"
    return "text"


def same(a, b) -> bool:
    """Numbers by value (ISO's 7386.0 is our 7386); dates whatever their format (we write 10/01/2026, ISO
    2026-10-01T00:00:00); identifiers (GUIDs each side mints) never differ; everything else as text."""
    na, nb = _num(a), _num(b)
    if na is not None and nb is not None:
        return na == nb
    da, db = _date(a) if a is not None else None, _date(b) if b is not None else None
    if da and db:
        return da == db
    if a is not None and b is not None and _GUID.match(str(a)) and _GUID.match(str(b)):
        return True
    return ("" if a is None else str(a)) == ("" if b is None else str(b))


def iso_leaves(obj, prefix="", out=None) -> dict:
    """Every scalar ISO published, by normalised path."""
    out = {} if out is None else out
    if isinstance(obj, dict):
        for k, v in obj.items():
            iso_leaves(v, f"{prefix}/{k}", out)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            iso_leaves(v, f"{prefix}[{i}]", out)
    elif obj is not None:
        out[normalise(prefix)] = obj
    return out


def our_leaves(node, prefix="", out=None, ids=None) -> tuple[dict, dict]:
    """Every scalar in our rated tree by normalised path, and node id -> path (to place the trace's writes)."""
    out = {} if out is None else out
    ids = {} if ids is None else ids
    seen: dict = {}
    for c in node.children:
        i = seen.get(c.tag, 0)
        seen[c.tag] = i + 1
        p = f"{prefix}/{c.tag}[{i}]"
        if c.text not in (None, ""):
            np = normalise(p)
            out[np] = c.text
            ids[id(c)] = np
        our_leaves(c, p, out, ids)
    return out, ids


def sources(trace, ids: dict) -> dict:
    """path -> {order, rule_file, package, op, tables} for every field the trace shows us writing (the last write
    wins, as in the tree); `tables` are the lookups made since the previous write, the ones that fed it."""
    out, tables = {}, []
    for n, t in enumerate(trace):
        if t.kind.startswith("lookup"):
            d = t.data or {}
            if d.get("table"):
                tables.append(f"{d.get('package', '')}/{d.get('table')}[{d.get('column', '')}]")
        elif t.kind == "write":
            d = t.data or {}
            p = ids.get(d.get("node"))
            if p is not None:
                out[p] = {"order": n, "rule_file": d.get("rule_file", ""), "package": d.get("package", ""),
                          "op": t.source, "tables": tables[-4:]}
            tables = []
    return out


def align(line: str, tree, trace, body: dict) -> list:
    """Rows: every field in either side, ours vs ISO, with its ERC source and write order. Ordered as our tree reads,
    ISO-only fields after the record they belong to."""
    ours, ids = our_leaves(tree)
    tops = tuple(f"/{k}" for k in body)          # ISO answers for the line's records; ours carries policy bookkeeping too
    ours = {p: v for p, v in ours.items() if p.startswith(tops)}
    iso = iso_leaves(body)
    src = sources(trace, ids)
    rows, placed = [], set()
    for p, v in ours.items():
        s = src.get(p, {})
        rows.append({"path": p, "id": stable_id(p), "record": record_of(p), "field": p.rsplit("/", 1)[-1],
                     "ours": v, "iso": iso.get(p), "in_iso": p in iso, "in_ours": True,
                     "match": same(v, iso[p]) if p in iso else None, "written": bool(s), "kind": kind(iso.get(p, v), p.rsplit("/", 1)[-1]),
                     "order": s.get("order"), "rule_file": s.get("rule_file", ""), "package": s.get("package", ""),
                     "op": s.get("op", ""), "tables": s.get("tables", [])})
        placed.add(p)
    for p, v in iso.items():
        if p not in placed:
            rows.append({"path": p, "id": stable_id(p), "record": record_of(p), "field": p.rsplit("/", 1)[-1],
                         "ours": None, "iso": v, "in_iso": True, "in_ours": False, "match": False, "written": False, "kind": kind(v, p.rsplit("/", 1)[-1]),
                         "order": None, "rule_file": "", "package": "", "op": "", "tables": []})
    return rows


# ---- rating a stored request, per line -----------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _cp():
    return import_module("154_chunk13_rc5_fields_messages")


@lru_cache(maxsize=4)
def _kernel(mode: str = "strict-erc"):
    from gl_engine.rating import Kernel
    return Kernel(mode=mode)


def rate(line: str, request: dict, mode: str = "strict-erc"):
    """(tree, trace, premium) for a stored request, on today's engine. Raises what the engine raises."""
    if line == "CP":
        data, ip = _cp().rate(request)
        tot = None
        for t in data.children:
            if t.tag == "CommercialPropertyTable" and t.children:
                for c in t.children[0].children:
                    if c.tag == "ErcCalculatedTotalPremium":
                        tot = c.text
        return data, ip.trace, tot
    r = _kernel(mode).rate(request)
    if not r.complete:
        raise RuntimeError(f"engine stopped: {r.stopped}")
    return r.tree, r.trace, str(r.premium)


def body_of(line: str, response: dict) -> dict:
    """The part of ISO's response that mirrors our tree: its Body, the line's records only."""
    b = response.get("Body", response)
    key = "CommercialProperty" if line == "CP" else "GeneralLiability"
    return {key: b.get(key)} if key in b else b


def catalog() -> dict:
    return json.loads(CATALOG.read_text(encoding="utf-8")) if CATALOG.exists() else {}
