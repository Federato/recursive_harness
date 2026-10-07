"""Trace Diff (TC-21): one stored scenario, ours against ISO's answer, row by row, on today's engine.

  * **rows** are the worksheet map's (`console.worksheet.align`): every field either side publishes, with our value,
    ISO's, and the rule file / package / tables that wrote ours;
  * **the first divergent step** is the earliest field *we computed* (trace order) whose number differs from ISO's;
    inputs that differ come before any computation (an input-mapping question, not arithmetic). Codes, dates and text
    are listed apart: they are not steps, and a code that differs while every premium agrees must not hide the one
    that matters;
  * a later difference **flows from** a divergence when its record is that divergence's record, or holds it, or sits
    under it (a premium rolling up); a difference in an unrelated record is a divergence of its own;
  * **records that match entirely are collapsed**;
  * **seen before** (D16): each scenario's divergences are kept (`results/tc/divergences.jsonl`, append-only); another
    scenario that diverged at the same stable ID is named with its classification;
  * **brief** (D16): the diff as plain text, to paste into an open item.

Nothing here rates for anyone else: the premium is the engine's, the agreement rule is `console.worksheet.same`.
"""
from __future__ import annotations

import json
import re
import time
from collections import OrderedDict
from pathlib import Path

from . import evidence, mismatch, store, worksheet as W

ROOT = Path(__file__).resolve().parent.parent
SEEN = ROOT / "results" / "tc" / "divergences.jsonl"
_CACHE: "OrderedDict[tuple, dict]" = OrderedDict()


def scenario_id(line: str, state: str, h: str) -> str:
    """The id the seed gives a stored answer (TC-19), so evidence, classifications and diffs share one name."""
    return f"{line}-{state}-{h[:10]}"


def _ref_files(e: dict) -> tuple[str | None, str | None]:
    """(request, ISO's answer): a `_response.json` when ISO rated; a `_refusal.json` or the failed-call capture's
    `response.txt` when it refused."""
    files = e.get("files", [])
    req = next((f for f in files if f.endswith("request.json")), None)
    if e.get("outcome") == "refused":
        resp = [f for f in files if f.endswith(("_refusal.json", "response.txt"))]
    else:
        resp = [f for f in files if f.endswith("_response.json")]
    return req, (resp[-1] if resp else None)


def scenarios(line: str | None = None, state: str | None = None) -> list:
    """Every stored answer Trace Diff can open (a request and a response on disk), with its evidence status."""
    ev = {r.get("hash"): r for r in evidence.records() if r.get("hash")}
    out = []
    for e in store.load()["references"]:
        if (line and e["line"] != line) or (state and e["state"] != state):
            continue
        req, resp = _ref_files(e)
        if not (req and resp):
            continue
        r = ev.get(e["hash"])
        agree = None
        if r and r.get("ours") is not None and r.get("iso") is not None:
            agree = W.same(r["ours"], r["iso"])
        out.append({"scenario": (r or {}).get("scenario") or scenario_id(e["line"], e["state"], e["hash"]),
                    "hash": e["hash"], "line": e["line"], "state": e["state"], "date": e["date"], "outcome": e["outcome"],
                    "stored_at": e.get("stored_at", ""), "source": Path(resp).name, "agree": agree,
                    "freshness": e.get("freshness", "")})
    out.sort(key=lambda s: (s["agree"] is not False, s["line"], s["state"], s["stored_at"]))
    return out


def _find(key: str) -> dict:
    for e in store.load()["references"]:
        if e["hash"] == key or scenario_id(e["line"], e["state"], e["hash"]) == key:
            return e
    for r in evidence.records():
        if r["scenario"] == key and r.get("hash"):
            return _find(r["hash"])
    raise KeyError(f"no stored answer for {key!r}")


def _related(a: str, b: str) -> bool:
    """Same record, or one holds the other (a premium rolls up its record's children)."""
    return a == b or a.startswith(b + "/") or b.startswith(a + "/")


def diff(key: str, line_hint: str | None = None) -> dict:
    e = _find(key)
    line, state, h = e["line"], e["state"], e["hash"]
    req_f, resp_f = _ref_files(e)
    if not (req_f and resp_f):
        raise KeyError(f"{key}: the request or ISO's response is not on disk")
    ck = (h, req_f, resp_f)
    if ck in _CACHE:
        _CACHE.move_to_end(ck)
        out = dict(_CACHE[ck])
        out["classification"] = mismatch.classifications().get(out["scenario"])
        out["seenBefore"] = seen_before(out["scenario"], [r["id"] for r in out["roots"]])
        out["brief"] = brief(out)
        return out
    req = json.loads((ROOT / req_f).read_text(encoding="utf-8"))
    if e["outcome"] == "refused":
        return _refusal_diff(e, req, (ROOT / resp_f).read_text(encoding="utf-8", errors="replace"))
    resp = json.loads((ROOT / resp_f).read_text(encoding="utf-8"))
    sid = scenario_id(line, state, h)
    ev = next((r for r in evidence.records() if r.get("hash") == h), None)
    if ev:
        sid = ev["scenario"]
    base = {"scenario": sid, "hash": h, "line": line, "state": state, "date": e["date"],
            "files": [Path(f).name for f in e["files"]], "isoPackage": e.get("iso_package", ""),
            "freshness": e.get("freshness", ""), "staleReason": e.get("stale_reason", "")}
    try:
        tree, trace, ours_total = W.rate(line, req)
    except Exception as exc:                                  # noqa: BLE001 -- our refusal is an answer, shown as one
        return {**base, "refused": f"{type(exc).__name__}: {exc}", "rows": [], "records": [], "roots": [],
                "other": [], "counts": {}, "seenBefore": [], "brief": ""}
    rows = W.align(line, tree, trace, W.body_of(line, resp))
    iso_total = _iso_total(line, resp)

    def nonzero(v):
        n = W._num(v)
        return n is not None and n != 0

    # A step differs when both sides have it and the numbers disagree, or when only one side has a non-zero number
    # for it: a premium we computed on a record ISO's answer leaves out (OI-116's shape), or one ISO publishes that we
    # never write. Inputs only we echo are not steps (ISO does not echo every input).
    written_orders = [(r["record"], r["order"]) for r in rows if r["order"] is not None]
    for r in rows:
        if r["kind"] == "number" and r["in_ours"] and not r["in_iso"] and r["written"] and nonzero(r["ours"]):
            r["match"] = False
        if r["kind"] == "number" and not r["in_ours"] and nonzero(r["iso"]):
            near = [o for rec, o in written_orders if _related(rec, r["record"])]
            r["order"] = (min(near) - 0.5) if near else None
            r["match"] = False
    steps = sorted((r for r in rows if r["kind"] == "number" and r["match"] is False and (
                       (r["in_iso"] and r["in_ours"]) or
                       (r["in_ours"] and not r["in_iso"] and r["written"] and nonzero(r["ours"])) or
                       (r["in_iso"] and not r["in_ours"] and nonzero(r["iso"])))),
                   key=lambda r: (-1 if r["order"] is None else r["order"], r["path"]))
    roots = []
    for r in steps:
        parent = next((x for x in roots if _related(r["record"], x["record"])), None)
        if parent is None:
            r["role"] = "first" if not roots else "divergence"
            roots.append(r)
        else:
            r["role"] = "flows"
            r["flowsFrom"] = parent["path"]
    for x in roots:
        x["downstream"] = sum(1 for r in steps if r.get("flowsFrom") == x["path"])
    other = [r for r in rows if r["in_iso"] and r["in_ours"] and r["match"] is False and r["kind"] != "number"]
    for r in other:
        r["role"] = "other"

    records = []
    by_rec: "OrderedDict[str, list]" = OrderedDict()
    for r in rows:
        by_rec.setdefault(r["record"], []).append(r)
    for rec, rs in by_rec.items():
        compared = [r for r in rs if r["in_iso"] and r["in_ours"]]
        bad = [r for r in rs if r["match"] is False and r["in_ours"] and r["in_iso"]]
        records.append({"record": rec, "rows": len(rs), "compared": len(compared), "differ": len(bad),
                        "isoOnly": sum(1 for r in rs if not r["in_ours"]),
                        "steps": sum(1 for r in bad if r["kind"] == "number"), "collapsed": not bad})
    counts = {"rows": len(rows), "compared": sum(1 for r in rows if r["in_iso"] and r["in_ours"]),
              "agree": sum(1 for r in rows if r["match"] is True), "steps": len(steps), "roots": len(roots),
              "other": len(other), "isoOnly": sum(1 for r in rows if not r["in_ours"]),
              "oursOnly": sum(1 for r in rows if not r["in_iso"])}
    out = {**base, "oursTotal": ours_total, "isoTotal": iso_total, "rows": rows, "records": records,
           "roots": [{k: r[k] for k in ("path", "id", "record", "field", "ours", "iso", "rule_file", "package",
                                        "tables", "downstream", "role")} for r in roots],
           "other": [{k: r[k] for k in ("path", "field", "ours", "iso", "kind")} for r in other][:50],
           "counts": counts, "classification": mismatch.classifications().get(sid)}
    remember(sid, line, state, out["roots"])
    _CACHE[ck] = out
    if len(_CACHE) > 24:
        _CACHE.popitem(last=False)
    out = dict(out)
    out["seenBefore"] = seen_before(sid, [r["id"] for r in out["roots"]])
    out["brief"] = brief(out)
    _CACHE[ck]["brief"] = out["brief"]
    return out


_MATRIX = re.compile(r"Matrix: (\w+)(?:, Project: ([A-Z]{2} [A-Z]{2} \d{8} V\d\d))?")


def _refusal_diff(e: dict, req: dict, iso_text: str) -> dict:
    """ISO refused this request. If ours refuses too, compare the tables each names; if ours rates, the divergence is
    where our engine read a table ISO says returned no rows (OI-133's shape: a fallback ISO does not make)."""
    line, state, h = e["line"], e["state"], e["hash"]
    sid = scenario_id(line, state, h)
    m = re.search(r'"(?:Message|message)"\s*:\s*"((?:[^"\\]|\\.)*)', iso_text)
    iso_msg = m.group(1) if m else iso_text[:2000]
    iso_tables = [(t, p) for t, p in _MATRIX.findall(iso_msg)]
    base = {"scenario": sid, "hash": h, "line": line, "state": state, "date": e["date"], "isoRefused": iso_msg,
            "isoTables": [t for t, _ in iso_tables], "files": [Path(f).name for f in e["files"]],
            "isoPackage": e.get("iso_package", ""), "freshness": e.get("freshness", ""),
            "staleReason": e.get("stale_reason", ""), "rows": [], "records": [], "other": [],
            "classification": mismatch.classifications().get(sid)}
    try:
        tree, trace, ours_total = W.rate(line, req)
    except Exception as exc:                                  # noqa: BLE001
        ours_msg = f"{type(exc).__name__}: {exc}"
        same_table = any(t in ours_msg for t, _ in iso_tables)
        out = {**base, "refused": ours_msg, "bothRefuse": True, "sameTable": same_table, "roots": [],
               "counts": {"steps": 0, "roots": 0}}
        out["brief"] = brief_refusal(out)
        return out
    roots = []
    for n, t in enumerate(trace):
        d = t.data or {}
        if t.kind.startswith("lookup") and d.get("table") in {x for x, _ in iso_tables}:
            have = next((r for r in roots if r["field"] == d.get("table")), None)
            if have:                                          # the same table again, other keys: one divergence
                have["downstream"] += 1
                continue
            roots.append({"path": f"lookup {d.get('table')}[{d.get('column', '')}]", "id": f"table:{d.get('table')}",
                          "record": "", "field": d.get("table"), "ours": d.get("value"), "iso": None,
                          "rule_file": "", "package": d.get("package", ""), "tables": [str(d.get("keys"))],
                          "downstream": 0, "role": "first" if not roots else "divergence", "order": n})
    out = {**base, "oursTotal": ours_total, "isoTotal": None, "roots": roots[:5],
           "counts": {"steps": len(roots), "roots": min(len(roots), 5), "compared": 0, "agree": 0, "other": 0,
                      "isoOnly": 0, "oursOnly": 0}, "oursRates": True}
    remember(sid, line, state, out["roots"])
    out["seenBefore"] = seen_before(sid, [r["id"] for r in out["roots"]])
    out["brief"] = brief_refusal(out)
    return out


def brief_refusal(d: dict) -> str:
    L = [f"Trace Diff · {d['scenario']} · {d['line']} {d['state']} · effective {d['date']} · ISO refused",
         f"ISO: {d['isoRefused'][:400]}"]
    if d.get("bothRefuse"):
        L.append(f"Ours refuses too{' at the same table' if d.get('sameTable') else ' (a different reason)'}: "
                 f"{d['refused'][:300]}")
    else:
        L.append(f"Ours rates it ({d.get('oursTotal')}).")
        for r in d["roots"]:
            L.append(f"- {'FIRST' if r['role'] == 'first' else 'Also'} divergence: ours read {r['field']} = {r['ours']} "
                     f"from {r['package'] or '?'} (keys {r['tables'][0]}) where ISO found no rows and refused"
                     + (f"; {r['downstream']} more read(s) of it at other keys" if r["downstream"] else ""))
    L.append("Files: " + ", ".join(d["files"]))
    return "\n".join(L)


def _iso_total(line: str, resp: dict):
    b = resp.get("Body", {})
    if line == "CP":
        cp = b.get("CommercialProperty")
        cp = cp[0] if isinstance(cp, list) and cp else cp or {}
        return cp.get("ErcCalculatedTotalPremium")
    gl = (b.get("GeneralLiability") or [{}])[0]
    return gl.get("Premium")


def remember(sid: str, line: str, state: str, roots: list) -> None:
    """Keep where a scenario diverged, once per (scenario, stable ID)."""
    have = {(r["scenario"], r["id"]) for r in _seen_all()}
    new = []
    for r in roots:
        if (sid, r["id"]) not in have:
            have.add((sid, r["id"]))
            new.append(r)
    if not new:
        return
    SEEN.parent.mkdir(parents=True, exist_ok=True)
    with SEEN.open("a", encoding="utf-8") as f:
        for r in new:
            f.write(json.dumps({"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "scenario": sid, "line": line,
                                "state": state, "id": r["id"], "field": r["field"]}) + "\n")


def _seen_all() -> list:
    if not SEEN.exists():
        return []
    return [json.loads(x) for x in SEEN.read_text(encoding="utf-8").splitlines() if x.strip()]


def seen_before(sid: str, ids: list) -> list:
    """Other scenarios that diverged at the same stable IDs, with their latest classification (D16)."""
    cls = mismatch.classifications()
    out = []
    for r in _seen_all():
        if r["id"] in ids and r["scenario"] != sid:
            c = cls.get(r["scenario"])
            out.append({**r, "classification": c and {k: c.get(k) for k in ("category", "note", "by", "at")}})
    return out[-20:]


def brief(d: dict) -> str:
    """The diff as text to paste into an open item (D16)."""
    L = [f"Trace Diff · {d['scenario']} · {d['line']} {d['state']} · effective {d['date']} · ISO package {d['isoPackage'] or '?'}",
         f"Totals: ours {d.get('oursTotal')} · ISO {d.get('isoTotal')}",
         f"Compared {d['counts'].get('compared', 0)} fields: {d['counts'].get('agree', 0)} agree, "
         f"{d['counts'].get('steps', 0)} numeric steps differ ({d['counts'].get('roots', 0)} divergence(s)), "
         f"{d['counts'].get('other', 0)} codes / dates / text differ, {d['counts'].get('isoOnly', 0)} ISO-only fields."]
    for r in d["roots"]:
        L.append(f"- {'FIRST' if r['role'] == 'first' else 'Also'} divergence at {r['path']}: ours "
                 f"{'absent' if r['ours'] is None else r['ours']} vs ISO {'absent' if r['iso'] is None else r['iso']} · written by {r['rule_file'] or '?'} ({r['package'] or '?'})"
                 + (f" · tables read: {', '.join(r['tables'])}" if r["tables"] else "")
                 + (f" · {r['downstream']} later difference(s) flow from it" if r["downstream"] else ""))
    for s in d.get("seenBefore", [])[:5]:
        c = s.get("classification")
        L.append(f"- Seen before: {s['scenario']} diverged at {s['id']}"
                 + (f" (classified {c['category']}{': ' + c['note'] if c.get('note') else ''})" if c else " (unclassified)"))
    L.append("Files: " + ", ".join(d["files"]))
    return "\n".join(L)
