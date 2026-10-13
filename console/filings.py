"""The Carrier Filings screen: every filing we have worked on, from the filings log and the carrier store.

Read-only. A filing's entry comes from `docs/deviations/FILINGS-LOG.md` (one `## DEV-nnn` section each, rendered
here); its source documents from `<CARRIERS_ROOT>/<carrier>/sources/<SERFF>/source.json`, each re-hashed against the
SHA-256 recorded there; and where each writing company's authored versions stand from their `workflow.jsonl`.
"""
from __future__ import annotations

import hashlib
import html as H
import json
import re
from pathlib import Path
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "docs" / "deviations" / "FILINGS-LOG.md"
KINDS = {".pdf": "pdf", ".csv": "csv"}


def _carriers() -> Path:
    from deviations.config import CARRIERS_ROOT
    return Path(CARRIERS_ROOT)


def _sections(text: str) -> dict:
    """`## DEV-nnn` sections of the log, by id, without their heading."""
    out, cur, buf = {}, None, []
    for ln in text.splitlines():
        m = re.match(r"^## (DEV-\d+)\s*$", ln)
        if m or (cur and ln.startswith("## ")):
            if cur:
                out[cur] = "\n".join(buf).strip()
            cur, buf = (m.group(1) if m else None), []
            continue
        if cur:
            buf.append(ln)
    if cur:
        out[cur] = "\n".join(buf).strip()
    return out


def _rule(cells: list) -> bool:
    """A markdown table's separator row (`|---|:--|`), as opposed to a row of blank cells."""
    return bool(cells) and all(re.fullmatch(r":?-+:?", c) for c in cells)


def _index(text: str) -> list:
    """The log's index table: one dict per row, keyed by the header's cells."""
    rows, head = [], None
    for ln in text.split("## Index", 1)[-1].split("\n## ", 1)[0].splitlines():
        if not ln.startswith("|"):
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if head is None:
            head = cells
        elif not _rule(cells):
            rows.append(dict(zip(head, cells)))
    return rows


def _inline(s: str) -> str:
    s = H.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<![\w*])\*([^*]+)\*(?!\w)", r"<i>\1</i>", s)
    return re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)


def render(md: str) -> str:
    """The log's markdown, as far as it uses it: paragraphs, bullets, tables, bold, italics, code."""
    out, para, i, lines = [], [], 0, md.splitlines()

    def flush():
        if para:
            out.append("<p>" + _inline(" ".join(para)) + "</p>")
            para.clear()
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("|"):
            flush()
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not _rule(cells):
                    rows.append(cells)
                i += 1
            th = "".join(f"<th>{_inline(c)}</th>" for c in rows[0]) if rows and any(rows[0]) else ""
            tb = "".join("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in r) + "</tr>" for r in rows[1:])
            out.append('<div class="fl-mdw"><table class="fl-md">' + (f"<tr>{th}</tr>" if th else "") + tb + "</table></div>")
            continue
        if re.match(r"^\s*[-*] ", ln):
            flush()
            items = []
            while i < len(lines) and (re.match(r"^\s*[-*] ", lines[i]) or (lines[i].startswith("  ") and items)):
                if re.match(r"^\s*[-*] ", lines[i]):
                    items.append(re.sub(r"^\s*[-*] ", "", lines[i]))
                else:
                    items[-1] += " " + lines[i].strip()
                i += 1
            out.append("<ul>" + "".join(f"<li>{_inline(x)}</li>" for x in items) + "</ul>")
            continue
        if ln.startswith("#"):
            flush()
            out.append("<h4>" + _inline(ln.lstrip("#").strip()) + "</h4>")
        elif not ln.strip():
            flush()
        else:
            para.append(ln.strip())
        i += 1
    flush()
    return "".join(out)


def _sources() -> dict:
    """Every archived filing's `source.json`, by SERFF number, with each file re-hashed."""
    out = {}
    base = _carriers()
    for sj in sorted(base.glob("*/sources/*/source.json")):
        try:
            meta = json.loads(sj.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        files = []
        for f in meta.get("files", []):
            p = sj.parent / f["name"]
            got = hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
            files.append({"name": f["name"], "what": f.get("what", ""), "bytes": f.get("bytes"),
                          "sha256": f.get("sha256"), "present": got is not None,
                          "intact": got is not None and got == f.get("sha256"),
                          "url": "/api/console/filings/source?" + urlencode(
                              {"carrier": sj.parent.parent.parent.name, "serff": sj.parent.name, "file": f["name"]})})
        out[meta.get("serff") or sj.parent.name] = {**meta, "files": files, "carrier": sj.parent.parent.parent.name}
    return out


def _versions(carrier: str, companies: list, serff: str) -> list:
    """Each company's authored versions of the filing whose id names this SERFF number, and where each stands."""
    from deviations import files as F
    base = _carriers() / carrier
    try:
        need = int(json.loads((base / "carrier.json").read_text(encoding="utf-8")).get("approval", {}).get("signoffs", 1))
    except (OSError, ValueError):
        need = 1
    out = []
    for co in companies:
        for a in sorted((base / co / "authored").glob(f"*{serff}*.json")):
            try:
                d = json.loads(a.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            w = F.workflow_status(base / co, d.get("filing", ""), int(d.get("version", 1)), need)
            last = w["lines"][-1] if w["lines"] else {}
            out.append({"company": co, "file": f"{co}/authored/{a.name}", "filing": d.get("filing"),
                        "version": d.get("version"), "rows": len(d.get("rows", [])), "status": w["status"],
                        "signers": w["signers"], "lastAt": last.get("ts"), "lastAction": last.get("action")})
    return out


def filings() -> dict:
    text = LOG.read_text(encoding="utf-8") if LOG.exists() else ""
    sections, src = _sections(text), _sources()
    rows, seen = [], set()
    for r in _index(text):
        dev = re.sub(r"[\[\]]|\(.*?\)", "", r.get("#", "")).strip()
        serff = r.get("SERFF", "")
        s = src.get(serff, {})
        seen.add(serff)
        companies = s.get("companies") or [c.strip() for c in r.get("Companies", "").split(",") if c.strip()]
        carrier = s.get("carrier") or r.get("Carrier", "")
        rows.append({"id": dev, "carrier": carrier, "companies": companies, "line": r.get("Line", ""),
                     "state": r.get("State", ""), "serff": serff, "effective": r.get("Effective", ""),
                     "status": r.get("Status", ""), "received": s.get("received"), "sources": s.get("files", []),
                     "archived": bool(s), "versions": _versions(carrier, companies, serff) if carrier else [],
                     "entry": render(sections.get(dev, ""))})
    # archived but not yet in the log: shown, so nothing received goes unseen
    for serff, s in src.items():
        if serff not in seen:
            rows.append({"id": "", "carrier": s["carrier"], "companies": s.get("companies", []),
                         "line": s.get("line", ""), "state": ", ".join(s.get("juris", [])), "serff": serff,
                         "effective": "", "status": "Received, not logged", "received": s.get("received"),
                         "sources": s["files"], "archived": True,
                         "versions": _versions(s["carrier"], s.get("companies", []), serff), "entry": ""})
    return {"filings": rows, "log": "docs/deviations/FILINGS-LOG.md", "store": str(_carriers())}


def source(query: dict):
    """One archived source document, as received: (bytes, kind), or None."""
    carrier, serff, name = (str(query.get(k) or "") for k in ("carrier", "serff", "file"))
    if not all((carrier, serff, name)) or any(x in v for v in (carrier, serff, name) for x in ("..", "/", "\\")):
        return None
    p = _carriers() / carrier / "sources" / serff / name
    if not p.is_file() or name == "source.json":
        return None
    return p.read_bytes(), KINDS.get(p.suffix.lower(), "text")
