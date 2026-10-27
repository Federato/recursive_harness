"""A once-only record sent as a list: ISO's request reader keeps the record and drops its fields (OI-145, OI-150;
found by ISOComputeGraph C-73, 2026-10-27).

ISO's data definitions declare most coverage records once-only (`maxOccurs="1"`) under their parent, and ISO's own
requests send them as a JSON object. Sent as a one-item list instead (`[{"Indicator": "Yes", "Limit": 25010}]`),
ISO's reader keeps the record but reads none of its fields: its response echoes none of them, and the coverage's
`CoverageOnPolicyIndicator` and `Premium` come out 0. Measured on every stored ISO answer: **101 of 101** once-only
records sent as a list came back without their fields; **3,849 of 3,849** sent as an object kept them. Ours read the
two alike, so it priced the special cause-of-loss extra limits ISO kept off the policy (OI-145, 11 requests) and gave
the computer-operations limit message on a coverage ISO never saw (OI-150, 4); read as ISO reads them, all 101
equal ISO on premium and messages.

    from cf_engine.iso_reader import as_iso_reads
    dropped = as_iso_reads(body["CommercialProperty"], book)    # in place, before the request is converted

Only a list on a field the edition declares once-only changes; a repeating record (`maxOccurs="unbounded"`) and an
object are read as before.
"""
from __future__ import annotations

import re
from pathlib import Path

__all__ = ["as_iso_reads", "once_only"]

_TYPES: dict[tuple, dict] = {}
_COMPLEX = re.compile(r'<xs:complexType name="(\w+)">(.*?)</xs:complexType>', re.S)
_ELEMENT = re.compile(r'<xs:element\b([^>]*)>')


def once_only(book) -> dict[str, dict[str, tuple[str, str]]]:
    """record type -> {child element: (maxOccurs as filed or None, child type)}, from the book's data definitions
    (state over parent). Only an explicit `maxOccurs="1"` counts as once-only."""
    res = book.resolution
    key = tuple(p.pkg_id for p in (res.parent, res.state) if p is not None)
    if key not in _TYPES:
        types: dict[str, dict] = {}
        for pkg in (res.parent, res.state):
            if pkg is None:
                continue
            d = Path(pkg.content) / "DataDefs"
            for f in sorted(d.glob("*.xsd")) if d.is_dir() else ():
                text = f.read_text(encoding="utf-8-sig", errors="replace")
                for name, body in _COMPLEX.findall(text):
                    kids = types.setdefault(name, {})
                    for attrs in _ELEMENT.findall(body):
                        nm = re.search(r'\bname="(\w+)"', attrs)
                        if nm is None:
                            continue
                        occ = re.search(r'\bmaxOccurs="(\w+)"', attrs)
                        typ = re.search(r'\btype="(\w+)"', attrs)
                        kids[nm.group(1)] = (occ.group(1) if occ else None, typ.group(1) if typ else nm.group(1))
        _TYPES[key] = types
    return _TYPES[key]


def as_iso_reads(records, book, root: str = "CommercialProperty") -> list[str]:
    """Each once-only record sent as a list becomes an empty record, in place; the paths changed."""
    types = once_only(book)
    out: list[str] = []

    def walk(node, typ, path):
        kids = types.get(typ, {})
        for k, v in list(node.items()):
            occ, child = kids.get(k, (None, k))
            if isinstance(v, list) and v and all(isinstance(x, dict) for x in v) and occ == "1" and k in kids:
                node[k] = {}
                out.append(f"{path}/{k}")
            elif isinstance(v, dict):
                walk(v, child, f"{path}/{k}")
            elif isinstance(v, list):
                for i, x in enumerate(v):
                    if isinstance(x, dict):
                        walk(x, child, f"{path}/{k}[{i + 1}]")

    for i, rec in enumerate(records if isinstance(records, list) else [records]):
        if isinstance(rec, dict):
            walk(rec, root, f"{root}[{i + 1}]")
    return out
