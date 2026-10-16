"""The Carrier Filings screen: every filing we have worked on, from the filings log and the carrier store.

Read-only (B-20's demo view: no editing, no approval). A filing's entry comes from `docs/deviations/FILINGS-LOG.md` (one `## DEV-nnn` section each, rendered
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
LOG = ROOT / "docs" / "deviations" / "FILINGS-LOG.md"     # FILINGS_LOG overrides it (start-demo.bat: an empty one)


def _log() -> Path:
    import os
    return Path(os.environ.get("FILINGS_LOG") or LOG)
KINDS = {".pdf": "pdf", ".csv": "csv", ".md": "html"}


def _impact_dir() -> Path:
    import os
    return Path(os.environ.get("IMPACT_DIR") or ROOT / "results" / "impact")


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
            line = d.get("line", "")
            keys = 0
            for m in (base / co / "compiled" / line).glob(f"*/{d.get('filing')}.v{d.get('version')}/manifest.json"):
                keys += sum(int(t.get("rows", 0)) for t in _json(m).get("tables", {}).values())
            out.append({"company": co, "file": f"{co}/authored/{a.name}", "filing": d.get("filing"),
                        "version": d.get("version"), "rows": len(d.get("rows", [])), "status": w["status"],
                        "signers": w["signers"], "lastAt": last.get("ts"), "lastAction": last.get("action"),
                        "line": line, "juris": d.get("juris", []), "new_eff": d.get("new_eff"),
                        "renewal_eff": d.get("renewal_eff"), "compiledKeys": keys,
                        "detail": [{"target": r.get("target"), "scope": r.get("scope") or {}, "value": str(r.get("value")),
                                    "mode": r.get("mode"), "cite": r.get("cite", ""), "note": r.get("note", "")}
                                   for r in d.get("rows", [])]})
    return out


def _json(p: Path) -> dict:
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return {}


def impacts(companies: list, line: str, states: list, serff: str = "") -> list:
    """The impact previews (B-18; drafts, B-20) of this filing: for its companies, line and states, and rated under
    it -- its SERFF number in the draft's ref or in a state's filing in force. The summaries the screen draws, not
    every risk. Built filings first, then drafts, each company's newest last."""
    out = []
    for p in sorted(_impact_dir().glob("*.json")):
        d = _json(p)
        if d.get("company") not in companies or d.get("line") != line or not set(d.get("states", {})) & set(states):
            continue
        refs = [d.get("draft") or ""] + [str(v.get("filing") or "") for v in d.get("states", {}).values()]
        if serff and not any(serff in r for r in refs):
            continue
        out.append({"file": p.name, "company": d["company"], "draft": d.get("draft"), "generated": d.get("generated"),
                    "states": d["states"], "all": d.get("all"), "byRiskType": d.get("by_risk_type", {}),
                    "byCoverage": d.get("by_coverage", {}), "byState": d.get("by_state", {}),
                    "drivers": d.get("drivers", []), "refused": len(d.get("refused", [])),
                    "current": d.get("current"), "vsCurrent": d.get("vs_current")})
    return sorted(out, key=lambda x: (x["company"], bool(x["draft"]), x.get("generated") or ""))


def _proof(suite):
    """The proving suite's last recorded run (deviations.suite_log), or None when the filing names none."""
    if not suite:
        return None
    try:
        from deviations import suite_log
        got = suite_log.load(suite)
    except Exception:                                          # noqa: BLE001
        return None
    if not got:
        return {"suite": suite, "ran": False}
    checks = got.get("checks", [])
    return {"suite": suite, "ran": True, "passed": got.get("passed"), "checks": len(checks),
            "ok": sum(1 for _, ok in checks if ok), "ranAt": got.get("ran_at"), "commit": got.get("commit")}


def board() -> dict:
    """Every writing company by line and state: what rates there (B-20's filings board). A cell is a company's
    compiled filing in a state; a state with none rates on technical only."""
    from deviations import files as F
    base = _carriers()
    companies, cells = [], []
    for cj in sorted(base.glob("*/*/company.json")):
        cdir, carrier = cj.parent, cj.parent.parent.name
        c = _json(cj)
        code = c.get("code", cdir.name)
        try:
            need = int(_json(cdir.parent / "carrier.json").get("approval", {}).get("signoffs", 1))
        except ValueError:
            need = 1
        companies.append({"carrier": carrier, "code": code, "name": c.get("name", ""), "naic": c.get("naic", "")})
        for m in sorted(cdir.glob("compiled/*/*/*/manifest.json")):
            d = _json(m)
            line, juris = m.parent.parent.parent.name, m.parent.parent.name
            w = F.workflow_status(cdir, d.get("filing", ""), int(d.get("version", 1)), need)
            cells.append({"company": code, "carrier": carrier, "line": line, "state": juris,
                          "filing": d.get("filing"), "version": d.get("version"), "status": w["status"],
                          "new_eff": d.get("new_eff"), "renewal_eff": d.get("renewal_eff")})
        # drafts: authored, not approved -- on their own cell, or tagged on the filing in force they would replace
        for a in sorted(cdir.glob("authored/*.json")):
            d = _json(a)
            w = F.workflow_status(cdir, d.get("filing", ""), int(d.get("version", 1)), need)
            if w["status"] in ("approved", "withdrawn", "rejected"):
                continue                       # in force, or ended: only a version still in the works is a draft
            for juris in d.get("juris", []):
                line = d.get("line", "")
                live = next((x for x in cells if x["company"] == code and x["line"] == line and x["state"] == juris
                             and x.get("filing")), None)
                if live:
                    live.setdefault("drafts", []).append(f"{d.get('filing')} v{d.get('version')}")
                else:
                    cells.append({"company": code, "carrier": carrier, "line": line, "state": juris,
                                  "filing": d.get("filing"), "version": d.get("version"), "status": "draft",
                                  "new_eff": d.get("new_eff"), "renewal_eff": d.get("renewal_eff")})
    from console import plain as P
    for x in cells:
        x["plain"] = {"status": P.CELL.get(x["status"], x["status"]),
                      "since": P.money_date(x.get("new_eff")) if x.get("new_eff") else ""}
    cols = sorted({(x["line"], x["state"]) for x in cells})
    # the carrier picker: every carrier in the store, by its own name (carrier.json), even one with no filing yet
    carriers = [{"code": d.name, "name": _json(d / "carrier.json").get("name") or d.name}
                for d in sorted(base.iterdir()) if (d / "carrier.json").exists()] if base.exists() else []
    return {"companies": companies, "cells": cells, "carriers": carriers,
            "columns": [{"line": a, "state": b, "plain": f"{P.line(a)} · {P.state(b)}"} for a, b in cols]}


def _extras(s: dict, carrier: str, companies: list, line: str, states) -> dict:
    """The filing sheet (rendered), the proving suite's last run, and the impact previews for this filing."""
    states = [states] if isinstance(states, str) else list(states)
    sheet, raw = "", ""
    if s.get("sheet") and carrier:
        p = _carriers() / carrier / "sources" / s.get("serff", "") / s["sheet"]
        if p.is_file():
            raw = p.read_text(encoding="utf-8-sig")
            sheet = render(raw)
    return {"sheet": sheet, "_sheetRaw": raw, "proof": _proof(s.get("suite")), "impacts": impacts(companies, line, states, s.get("serff", "")),
            "stageDeclared": s.get("stage")}


STAGES = ("Received", "Mapped", "Draft impact", "Built", "Proved")


def _stage(row: dict) -> str:
    """Where a filing is: what source.json says, else what the store shows."""
    if row.get("stageDeclared") in STAGES:
        return row["stageDeclared"]
    built = any(v["status"] == "approved" and v.get("compiledKeys") for v in row.get("versions", []))
    if built:
        return "Proved" if (row.get("proof") or {}).get("passed") else "Built"
    if any(i.get("draft") for i in row.get("impacts", [])):
        return "Draft impact"
    if row.get("sheet") or row.get("versions"):
        return "Mapped"
    return "Received"


def _company_name(carrier: str, code: str) -> str:
    return _json(_carriers() / carrier / code / "company.json").get("name") or code


def _plain(r: dict, sheet_raw: str, log_raw: str) -> dict:
    """The filing in plain words (console/plain.py): what the main view shows."""
    from console import plain as P
    carrier = _json(_carriers() / r["carrier"] / "carrier.json").get("name") or r["carrier"]
    new = sorted({v.get("new_eff") for v in r["versions"] if v.get("new_eff")})
    ren = sorted({v.get("renewal_eff") for v in r["versions"] if v.get("renewal_eff")})
    for v in r["versions"]:
        v["plain"] = {"company": _company_name(r["carrier"], v["company"]),
                      "changes": P.company_rows(v.get("detail") or []),
                      "status": P.CELL.get(v["status"], v["status"]),
                      "rows": [{"what": P.target(x["target"]), "where": ("the whole policy" if str(x["target"]).startswith(("MIN:", "PCT:"))
                                          else P.scope(x.get("scope"))),
                                "change": P.row_change(x), "note": x.get("note", "")}
                               for x in v.get("detail") or []]}
    st = [x.strip() for x in str(r.get("state", "")).split(",")]
    for i in r.get("impacts", []):
        own = [i["byState"][x] for x in st if i.get("byState", {}).get(x)]
        a = own[0] if len(own) == 1 else (i.get("all") or {})
        vc = i.get("vsCurrent") or {}
        has_now = any(vc.get("filings", {}).values())
        i["plain"] = {"company": _company_name(r["carrier"], i["company"]),
                      "vsIso": P.change(a.get("change"), "ISO") if a else "",
                      "vsNow": (P.change(vc.get("change"), "today's rates") if has_now else "") if vc else "",
                      "risks": a.get("rated") if a else None,
                      "byType": {k: {"vsIso": P.change(v.get("change"), "ISO"),
                                     "vsNow": P.change((vc.get("by_risk_type") or {}).get(k), "today") if has_now else ""}
                                 for k, v in (i.get("byRiskType") or {}).items()}}
    return {"title": f"{carrier} · {P.line(r.get('line', ''))} · {P.state(r.get('state', ''))}",
            "carrier": carrier, "line": P.line(r.get("line", "")), "state": P.state(r.get("state", "")),
            "step": P.STAGES.get(r["stage"], r["stage"]), "steps": P.STEPS,
            "effective": ("New policies from " + " / ".join(P.money_date(x) for x in new)
                          + ("; renewals from " + " / ".join(P.money_date(x) for x in ren) if ren else "")) if new else "",
            "inShort": P.in_short(sheet_raw) or P.in_short(log_raw),
            "historyShort": P.in_short(log_raw),
            "proof": (f"Checked: {r['proof']['ok']} of {r['proof']['checks']} automatic tests pass"
                      if (r.get("proof") or {}).get("ran") else "")}


def filings() -> dict:
    log = _log()
    text = log.read_text(encoding="utf-8") if log.exists() else ""
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
                     "entry": render(sections.get(dev, "")), "_logRaw": sections.get(dev, ""),
                     **_extras(s, carrier, companies, r.get("Line", ""), r.get("State", ""))})
    # archived but not yet in the log: shown, so nothing received goes unseen
    for serff, s in src.items():
        if serff not in seen:
            rows.append({"id": "", "carrier": s["carrier"], "companies": s.get("companies", []),
                         "line": s.get("line", ""), "state": ", ".join(s.get("juris", [])), "serff": serff,
                         "effective": "", "status": "Received, not logged", "received": s.get("received"),
                         "sources": s["files"], "archived": True,
                         "versions": _versions(s["carrier"], s.get("companies", []), serff), "entry": "",
                         **_extras(s, s["carrier"], s.get("companies", []), s.get("line", ""), s.get("juris", []))})
    for r in rows:
        r["stage"] = _stage(r)
        if r["stage"] not in ("Built", "Proved"):
            r["proof"] = None                  # a suite's last run proves a built filing, not a draft
        r["plain"] = _plain(r, r.pop("_sheetRaw", ""), r.pop("_logRaw", ""))
    return {"filings": rows, "log": "docs/deviations/FILINGS-LOG.md", "store": str(_carriers()), "stages": list(STAGES)}


def source(query: dict):
    """One archived source document, as received: (bytes, kind), or None."""
    carrier, serff, name = (str(query.get(k) or "") for k in ("carrier", "serff", "file"))
    if not all((carrier, serff, name)) or any(x in v for v in (carrier, serff, name) for x in ("..", "/", "\\")):
        return None
    p = _carriers() / carrier / "sources" / serff / name
    if not p.is_file() or name == "source.json":
        return None
    if p.suffix.lower() == ".md":                              # a filing sheet: shown rendered
        body = render(p.read_text(encoding="utf-8-sig"))
        page = ("<!doctype html><meta charset='utf-8'><title>" + H.escape(name) + "</title><style>"
                "body{font:14px system-ui;max-width:980px;margin:24px auto;padding:0 16px}table{border-collapse:collapse}"
                "td,th{border-top:1px solid #ddd;padding:3px 8px;text-align:left;vertical-align:top}</style>" + body)
        return page.encode("utf-8"), "html"
    return p.read_bytes(), KINDS.get(p.suffix.lower(), "text")


# --------------------------------------------------------- packet upload (B-20)
# A filing packet (deviations/packet.py) uploaded on the Carrier Filings screen: checked, then written to the carrier
# store (never approved), then each draft's impact preview runs in the background. One job per SERFF number.

JOBS: dict = {}


def upload(body: dict) -> tuple[int, dict]:
    import base64
    import threading
    from deviations import packet as PK
    try:
        data = base64.b64decode(str(body.get("data") or ""), validate=True)
    except ValueError:
        return 400, {"error": "the upload is not base64"}
    try:
        rep = PK.ingest(data, _carriers())
    except PK.PacketError as exc:
        return 400, {"error": str(exc)}
    rep["name"] = str(body.get("name") or "")
    from console import plain as P
    docs = [w for w in rep.get("writes", []) if "/sources/" in w]
    props = rep.get("validation", [])
    rep["plain"] = {
        "headline": (f"Received {_json(_carriers() / rep['carrier'] / 'carrier.json').get('name') or rep['carrier']}'s "
                     f"{P.line(rep['line'])} filing for {P.state(', '.join(rep['juris']))}." if rep["ok"]
                     else "This packet couldn't be accepted. Nothing was saved."),
        "saved": (f"{len(docs)} document{'s' if len(docs) != 1 else ''} saved; "
                  f"{sum(1 for v in props if v['ok'])} of {len(props)} proposal{'s' if len(props) != 1 else ''} checked "
                  f"and valid." + (" Already had everything else." if rep.get("skips") else "")) if rep["ok"] else "",
        "problems": list(dict.fromkeys(P.problem(x) for x in rep.get("problems", [])))}
    if rep["ok"]:
        todo = [v["draft"] for v in rep.get("validation", []) if v["ok"]]
        if todo and JOBS.get(rep["serff"], {}).get("state") != "running":
            job = {"serff": rep["serff"], "state": "running", "total": len(todo), "done": 0, "messages": [],
                   "started": __import__("time").strftime("%Y-%m-%dT%H:%M:%S")}
            JOBS[rep["serff"]] = job
            threading.Thread(target=_impact_job, args=(job, todo), daemon=True).start()
        rep["impact"] = JOBS.get(rep["serff"])
    return 200, rep


def _impact_job(job: dict, drafts: list) -> None:
    from deviations.impact import run_draft, write
    for rel in drafts:
        try:
            rep = run_draft(_carriers() / rel)
            write(rep, _impact_dir())
            job["messages"].append(f"{rel}: {rep['all']['change']}% vs pure ISO"
                                   + (f", {rep['vs_current']['change']}% vs in force" if rep.get("vs_current") else ""))
            from console import plain as P
            now = rep.get("vs_current") or {}
            job.setdefault("plain", []).append(
                f"{_company_name(rel.split('/')[0], rep['company'])}: {P.change(rep['all']['change'], 'ISO')}"
                + (f", {P.change(now['change'], 'its rates today')}" if any((now.get('filings') or {}).values()) else ""))
        except Exception as exc:                               # noqa: BLE001  (shown on the screen)
            job["messages"].append(f"{rel}: no impact preview ({str(exc)[:200]})")
        job["done"] += 1
    job["state"] = "done"


def jobs() -> dict:
    return {"jobs": list(JOBS.values())}
