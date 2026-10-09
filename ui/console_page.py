"""The ISO Rating Test Console, `/console` (docs/TC-PLAN.md, RC-2 onward).

TC-14 is the shell every screen sits in: the seven tabs, the call-cap strip and
the shared legend, in the prototype's look (D7) with no external fonts or
libraries. The screens fill in task by task; until one is built its tab says
which task builds it.

The cap strip reads the call ledger (`console.ledger`) and nothing else, so it
shows exactly what `scripts/raas.py` admits against: 250 a day in three lanes,
reset at 00:00 Eastern. The legend reads `console.status`, so the glyphs and
labels here are the ones every screen shares (TC-08).

    from ui import console_page
    console_page.dispatch(method, path, query, body)   # mounted by app.py (Handler._console)
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone

from console import ledger, status

from . import variables

#: The screens (Upload & Compare, the landing screen, then the brief's seven), the hash each opens on, and the task
#: that builds it.
SCREENS = (
    ("compare", "Upload & Compare", "TC-39"),
    ("board", "Coverage Board", "TC-18"),
    ("matrix", "Readiness Matrix", "TC-16"),
    ("plan", "Test Plan Builder", "TC-27"),
    ("trace", "Trace Diff", "TC-21"),
    ("workbench", "Scenario Workbench", "TC-23"),
    ("library", "Regression Library", "TC-33"),
    ("queue", "Queue & Run Log", "TC-31"),
    ("proof", "Deviations Proof", "P4"),
    ("filings", "Carrier Filings", "DEV"),
)

LANE_NAMES = {"active": "Active plans", "refresh": "Change & stale refresh", "adhoc": "Ad hoc & triage"}


def cap(now: datetime | None = None) -> dict:
    """The call-cap strip: used, left and queued per lane, and when the day resets."""
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    d = ledger.day(now)
    u = ledger.used(d)
    # Next 00:00 Eastern: step forward by the minute until the ledger's day changes (DST-safe, no tz database).
    et = ledger._et(now)
    reset = now + timedelta(seconds=(24 * 3600 - (et.hour * 3600 + et.minute * 60 + et.second)))
    while ledger.day(reset) == d:
        reset += timedelta(minutes=1)
    overrides = sum(1 for e in ledger.entries(d) if e.get("override"))
    return {
        "day": d,
        "cap": ledger.CAP,
        "used": u["total"],
        "left": max(0, ledger.CAP - u["total"]),
        "queued": _queued(),             # scenarios waiting for a call in plans not finished (TC-30)
        "overrides": overrides,
        "resets_at": reset.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "resets_in_s": int((reset - now).total_seconds()),
        "lanes": [{"key": k, "name": LANE_NAMES[k], "cap": c, "used": u.get(k, 0)}
                  for k, c in ledger.LANES.items()],
    }


def _queued() -> int:
    try:
        from console import plans as P
        return sum(1 for p in P.all_plans() if p["status"] in ("queued", "running", "paused")
                   for s in p["scenarios"] if s["status"] == "queued")
    except Exception:                                         # noqa: BLE001 -- the strip never fails for this
        return 0


def legend() -> list:
    return [{"key": s.key, "glyph": s.glyph, "board": s.board, "matrix": s.matrix, "meaning": s.meaning,
             "needs": status.NEEDS.get(s.key, "")} for s in status.ALL]


STATE_NAMES = {
    "AK": "Alaska", "AL": "Alabama", "AR": "Arkansas", "AZ": "Arizona", "CA": "California", "CO": "Colorado",
    "CT": "Connecticut", "DC": "District of Columbia", "DE": "Delaware", "FL": "Florida", "GA": "Georgia",
    "HI": "Hawaii", "IA": "Iowa", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "KS": "Kansas", "KY": "Kentucky",
    "LA": "Louisiana", "MA": "Massachusetts", "MD": "Maryland", "ME": "Maine", "MI": "Michigan", "MN": "Minnesota",
    "MO": "Missouri", "MS": "Mississippi", "MT": "Montana", "NC": "North Carolina", "ND": "North Dakota",
    "NE": "Nebraska", "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NV": "Nevada", "NY": "New York",
    "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "PR": "Puerto Rico", "RI": "Rhode Island",
    "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VA": "Virginia",
    "VT": "Vermont", "WA": "Washington", "WI": "Wisconsin", "WV": "West Virginia", "WY": "Wyoming",
}


def classify(body: dict) -> tuple[int, dict]:
    """TC-22: classify a scenario's difference with ISO (TC-11's taxonomy), with a note. The premiums the tolerance is
    judged on are the scenario's evidence (what the matrix rolls up), else the diff's totals. Append-only: the latest
    classification wins and the matrix and board follow on their next read."""
    from console import evidence, mismatch
    sid, cat = str(body.get("scenario") or "").strip(), str(body.get("category") or "").strip()
    if not sid or cat not in mismatch.BY_KEY:
        return 400, {"error": f"need a scenario and one of {sorted(mismatch.BY_KEY)}"}
    ev = next((r for r in evidence.records() if r["scenario"] == sid), None)
    ours, iso = (ev or {}).get("ours"), (ev or {}).get("iso")
    if ours is None or iso is None:
        ours, iso = body.get("ours"), body.get("iso")
    rec = mismatch.classify(sid, cat, note=str(body.get("note") or ""), by=str(body.get("by") or ""), ours=ours, iso=iso)
    within = None
    if ours is not None and iso is not None:
        from decimal import Decimal
        within = mismatch.within(cat, Decimal(str(ours)), Decimal(str(iso)))
    return 200, {**rec, "withinTolerance": within, "inEvidence": ev is not None}


def workbench(method: str, op: str, query: dict, b: dict):
    """TC-23's routes. Every one is free except `send`, which spends one call through the ledger (or reuses)."""
    from console import workbench as WB
    line = "CP" if (b.get("line") or query.get("lob") or "").upper() == "CP" else "GL"
    state = (b.get("state") or query.get("state") or "").upper()
    js = lambda code, o: (code, json.dumps(o), "json")    # noqa: E731
    try:
        if op == "spec":
            if line == "GL":
                import variants as V
                spec = variables.specs()
                return js(200, {"line": "GL", "states": sorted(V.Declared.jurisdictions()), "modes": WB.modes(),
                                "roundings": list(WB.ROUNDINGS),
                                "controls": [{k: c.get(k) for k in ("id", "label", "group", "kind", "note")}
                                             for c in spec["controls"]]})
            import property_rating as pr
            return js(200, {"line": "CP", "states": pr.states(), "modes": [], "roundings": []})
        if op == "options" and method == "POST":
            return js(200, variables.for_juris(state, b.get("config") or {}))
        if op == "request":
            if b.get("hash") or query.get("hash"):
                e = next(x for x in store_refs() if x["hash"] == (b.get("hash") or query.get("hash")))
                req = next(f for f in e["files"] if f.endswith("_request.json"))
                from console.store import ROOT as R
                return js(200, json.loads((R / req).read_text(encoding="utf-8")))
            return js(200, WB.build(line, state))
        if op == "rate" and method == "POST":
            p = WB.build(line, state, b.get("config"), b.get("request"))
            return js(200, {**WB.rate(line, p, b.get("mode") or "strict-erc", b.get("rounding") or "ROUND_HALF_UP"),
                            "request": p})
        if op == "send" and method == "POST":
            p = WB.build(line, state, b.get("config"), b.get("request"))
            return js(200, WB.send(line, p, reuse=b.get("reuse", True) is not False, override=b.get("override") or None))
        if op == "generate":
            # Upload & Compare's generator: the Workbench's base request for a line and state (GL from ISO's declared
            # domains, CP the state's sample risk), returned as text for the page to keep as it would an uploaded file
            return js(200, {"line": line, "state": state, "text": json.dumps(WB.build(line, state), indent=1)})
        if op == "companies":
            # Upload & Compare's writing-company picker (deviations P4): every company with a compiled filing
            return js(200, {"companies": WB.companies()})
        if op == "worksheet" and method == "POST":
            # the rating worksheet for one uploaded request: Technical | ISO | Deviated, field by field (free)
            try:
                req = json.loads(b["text"]) if "text" in b else b.get("request")
                if isinstance(req, list):
                    req = req[int(b.get("index") or 0)]
                who = WB.identify(req)
            except (ValueError, IndexError) as exc:
                return js(400, {"error": str(exc)[:400]})
            return js(200, WB.worksheet(who["line"], req, (b.get("company") or "").strip(), b.get("policyType") or "New"))
        if op == "why" and method == "POST":
            # G2: why a worksheet value is what it is -- its ancestry from the worksheet's rating graph
            return js(200, WB.why(str(b.get("token") or ""), b.get("side") or "technical", int(b.get("gid") or 0),
                                  int(b.get("depth") or 3)))
        if op in ("upload", "upload-send") and method == "POST":
            # Upload & Compare: the request as given (GL or CP, read from its ProductName); rated free, or one call
            # parsed here, from the text as uploaded: a browser's JSON round trip turns 1.0 into 1, so the request
            # would no longer hash to ISO's stored answer for it
            try:
                req = json.loads(b["text"]) if "text" in b else b.get("request")
                if isinstance(req, list):
                    req = req[int(b.get("index") or 0)]
                who = WB.identify(req)
            except (ValueError, IndexError) as exc:
                return js(400, {"error": str(exc)[:400]})
            company = (b.get("company") or "").strip()
            if op == "upload-send":
                if company:              # D21: ISO is sent the NON-DEVIATED payload only, never a company's LCMs
                    return js(200, {**who, **WB.send_technical(who["line"], req, company,
                                                               reuse=b.get("reuse", True) is not False,
                                                               override=b.get("override") or None)})
                return js(200, {**who, **WB.send(who["line"], req, reuse=b.get("reuse", True) is not False,
                                                 override=b.get("override") or None)})
            if company:                  # Technical / ISO / Carrier for one request (P4)
                return js(200, {**who, **WB.rate_company(who["line"], req, company,
                                                         b.get("policyType") or "New")})
            return js(200, {**who, **WB.rate(who["line"], req, b.get("mode") or "strict-erc",
                                             b.get("rounding") or "ROUND_HALF_UP")})
        if op == "where" and method == "POST":
            import variants as V
            cfg = V.clean(b.get("config") or {})
            return js(200, {**variables.legality(cfg), "describes": V.describe(cfg)})
        if op == "every" and method == "POST":
            import variants as V
            cfg = V.clean(b.get("config") or {})
            leg = variables.legality(cfg)
            sts = leg.get("applicable") or []
            out = WB.every_state(cfg, sts, b.get("mode") or "strict-erc", b.get("rounding") or "ROUND_HALF_UP")
            return js(200, {**out, "notApplicable": leg.get("not_applicable", {}), "describes": V.describe(cfg)})
        if op == "curve":
            import runstore
            cid = query.get("control", "")
            return js(200, {"control": cid, "series": runstore.response_curve(cid)})
    except Exception as exc:                                  # noqa: BLE001 -- shown on the page, never a crash
        return js(400, {"error": f"{type(exc).__name__}: {exc}"[:400]})
    return js(404, {"error": f"no workbench route {op!r}"})


def _dispatcher_on():
    """The dispatcher runs inside the app (one thread); `TC_DISPATCH=0` keeps it off (tests)."""
    import os
    if os.environ.get("TC_DISPATCH", "1") != "0":
        from console import dispatcher
        dispatcher.start()


def planning(method: str, path: str, query: dict, b: dict):
    """RC-4's routes: the catalog, plan preview / Tier 0 / commit / controls, the run log, refusals, override, run
    files, and a plan's read-only report (D17). Only a running plan spends calls, through the dispatcher."""
    from console import catalog as C, dispatcher as D, invariants, plans as P, runlog
    js = lambda code, o: (code, json.dumps(o), "json")    # noqa: E731
    line = "CP" if (b.get("line") or query.get("lob") or "").upper() == "CP" else "GL"
    try:
        if path == "/api/console/catalog":
            st = (query.get("state") or "").upper()
            if not st:
                import variants as V
                import property_rating as pr
                return js(200, {"line": line, "states": pr.states() if line == "CP" else sorted(V.Declared.jurisdictions())})
            cfg = json.loads(query.get("config") or "{}")
            return js(200, {"line": line, "state": st, "dimensions": C.dimensions(line, st, cfg)})
        if path == "/api/console/plan/preview" and method == "POST":
            return js(200, P.preview(b["spec"]))
        if path == "/api/console/plan/tier0" and method == "POST":
            sts = (b.get("states") or [])[:8]
            out = invariants.run(line, sts)
            out["note"] = "" if len(b.get("states") or []) <= 8 else f"the first 8 of {len(b['states'])} states, to keep this quick"
            return js(200, out)
        if path == "/api/console/plan/commit" and method == "POST":
            plan = P.commit(b["spec"], by=str(b.get("by") or ""), name=str(b.get("name") or ""))
            if b.get("start"):
                plan = P.control(plan["id"], "start", str(b.get("by") or ""))
                _dispatcher_on()
            return js(200, P.summary(plan))
        if path == "/api/console/plans":
            from console import inspection as I
            return js(200, {"plans": [{**P.summary(p), "inspection": I.plan_view(p)["counts"]} for p in reversed(P.all_plans())]})
        if path == "/api/console/plan":
            p = P.load(query.get("id", ""))
            return js(200, {**p, "summary": P.summary(p)})
        if path == "/api/console/plan/control" and method == "POST":
            p = P.control(str(b.get("id")), str(b.get("action")), str(b.get("by") or ""))
            if p["status"] == "running":
                _dispatcher_on()
            return js(200, P.summary(p))
        if path == "/api/console/runlog":
            return js(200, {"entries": list(reversed(runlog.entries(query.get("plan") or None, 400)))})
        if path == "/api/console/refused":
            from console import store, tracediff
            refs = [e for e in store.load()["references"] if e["outcome"] == "refused"]
            refs.sort(key=lambda e: e.get("stored_at", ""), reverse=True)
            return js(200, {"total": len(refs), "refused": [{"scenario": tracediff.scenario_id(e["line"], e["state"], e["hash"]),
                                                              "line": e["line"], "state": e["state"], "date": e["date"],
                                                              "stored_at": e.get("stored_at", ""), "message": e.get("message", "")}
                                                             for e in refs[:200]]})
        if path == "/api/console/override":
            if method == "POST":
                return js(200, D.set_override(str(b.get("reason") or ""), int(b.get("calls") or 0), str(b.get("by") or "")))
            return js(200, {"override": D.override()})
        if path == "/api/console/runs":
            from console import store as S
            rid = query.get("id")
            lines = [json.loads(x) for f in sorted(S.RES.glob("runs-*.jsonl"))
                     for x in f.read_text(encoding="utf-8").splitlines() if x.strip()]
            if rid:
                ln = next((l for l in lines if l.get("id") == rid), None)
                return js(200 if ln else 404, ln or {"error": "no such run"})
            out = [{"id": l.get("id"), "at": l.get("at_iso"), "label": l.get("label", ""), "batch": l.get("batch", ""),
                    "describes": (l.get("summary") or {}).get("describes", ""), "compared": (l.get("summary") or {}).get("compared"),
                    "rated": (l.get("summary") or {}).get("rated"), "agree": (l.get("summary") or {}).get("agree"),
                    "differ": len((l.get("summary") or {}).get("differ") or []), "total": (l.get("summary") or {}).get("total")}
                   for l in reversed(lines)]
            return js(200, {"runs": out[:300], "total": len(out)})
        if path.startswith("/console/report/"):
            return 200, report(P.load(path.rsplit("/", 1)[-1]), runlog.entries(path.rsplit("/", 1)[-1], 2000)), "html"
    except (KeyError, ValueError, FileNotFoundError) as exc:
        return js(400, {"error": f"{type(exc).__name__}: {exc}"[:300]})
    return js(404, {"error": "no such planning route"})


def inspect_routes(method: str, path: str, query: dict, b: dict):
    """Results inspection: a plan's results with their verdicts, a verdict, pass-all-matches, sign-off, and the
    verdicts for a list of scenarios (Trace Diff, the board's cell panel)."""
    from console import inspection as I, plans as P
    js = lambda code, o: (code, json.dumps(o), "json")    # noqa: E731
    try:
        if path == "/api/console/inspect/plan":
            return js(200, I.plan_view(P.load(query.get("id", ""))))
        if path == "/api/console/inspect/verdicts":
            v = I.latest()
            return js(200, {s: v.get(s) for s in (query.get("ids") or "").split(",") if s})
        if method != "POST":
            return js(405, {"error": "POST only"})
        if path == "/api/console/inspect":
            return js(200, I.record(str(b.get("scenario") or ""), str(b.get("verdict") or ""), by=str(b.get("by") or ""),
                                    reason=str(b.get("reason") or ""), category=str(b.get("category") or ""),
                                    plan=str(b.get("plan") or "")))
        if path == "/api/console/inspect/pass-matches":
            return js(200, {"passed": I.pass_matches(P.load(str(b.get("plan"))), by=str(b.get("by") or ""))})
        if path == "/api/console/inspect/signoff":
            return js(200, I.signoff(P.load(str(b.get("plan"))), by=str(b.get("by") or "")))
    except (I.InspectionError, KeyError, ValueError, FileNotFoundError) as exc:
        return js(400, {"error": str(exc)[:300]})
    return js(404, {"error": "no such inspection route"})


def library_routes(method: str, path: str, query: dict, b: dict):
    """RC-5: the library view, a re-run (free, in its own process so the app stays responsive), the stale answers and
    a refresh plan for them (queued in the refresh lane; it spends only when started from the Queue)."""
    import subprocess
    from console import regression as R
    js = lambda code, o: (code, json.dumps(o), "json")    # noqa: E731
    try:
        if path == "/api/console/library":
            return js(200, R.view())
        if path == "/api/console/library/rerun" and method == "POST":
            if R.PROGRESS.exists():
                return js(409, {"error": "a re-run is already going", "progress": json.loads(R.PROGRESS.read_text(encoding="utf-8"))})
            R.RUNS.mkdir(parents=True, exist_ok=True)
            script = R.ROOT / "scripts" / "tc" / "tc34_rerun_library.py"
            if getattr(sys, "frozen", False) or not script.exists():
                # the packaged app: its "python" is the app itself, so the re-run goes on a thread, one entry at a time
                import threading
                threading.Thread(target=R.run, kwargs={"workers": 1}, name="tc-library-rerun", daemon=True).start()
                return js(200, {"started": True, "inProcess": True})
            log = open(R.RUNS / "last_rerun.log", "w", encoding="utf-8")
            subprocess.Popen([sys.executable, "-X", "utf8", str(script)], cwd=R.ROOT, stdout=log, stderr=subprocess.STDOUT)
            return js(200, {"started": True})
        if path == "/api/console/library/stale":
            return js(200, R.stale())
        if path == "/api/console/library/refresh" and method == "POST":
            from console import plans as P
            return js(200, P.summary(R.refresh_plan(by=str(b.get("by") or ""))))
    except (KeyError, ValueError) as exc:
        return js(400, {"error": f"{type(exc).__name__}: {exc}"[:300]})
    return js(404, {"error": "no such library route"})


SNAPSHOT_TRACES = ("CP-FL-865e8e3634", "CP-FL-a423e73917", "CP-OH-7164f29b0a", "CP-OH-c473de0f0e")


def snapshot(traces: tuple = SNAPSHOT_TRACES, gl_traces: int = 1) -> str:
    """D6: the console as one read-only page, for Ideation. Every answer the Matrix, the Board, the Library, the Queue
    & Run Log and the chosen Trace Diffs read is computed now and embedded; a stand-in `fetch` serves them, refuses
    every write, and says what is not in the snapshot. No server, no calls."""
    import subprocess
    import time as _t
    from console import plans as P, store, tracediff
    get = lambda path, q=None: json.loads(dispatch("GET", path, q or {}, None)[1])    # noqa: E731
    gl = [s for s in tracediff.scenarios("GL") if s["outcome"] == "rated"][:gl_traces]
    ids = list(traces) + [s["scenario"] for s in gl]
    snap = {"/api/console/cap": get("/api/console/cap"), "/api/console/readiness": get("/api/console/readiness"),
            "/api/console/library": get("/api/console/library"), "/api/console/library/stale": get("/api/console/library/stale"),
            "/api/console/plans": get("/api/console/plans"), "/api/console/runlog": get("/api/console/runlog"),
            "/api/console/override": get("/api/console/override"), "/api/console/refused": get("/api/console/refused"),
            "/api/console/runs": get("/api/console/runs")}
    for line in ("GL", "CP"):
        snap[f"/api/console/board?lob={line}"] = get("/api/console/board", {"lob": line})
        snap[f"/api/console/controls?lob={line}"] = get("/api/console/controls", {"lob": line})
    for p in snap["/api/console/plans"]["plans"]:
        snap[f"/api/console/plan?id={p['id']}"] = get("/api/console/plan", {"id": p["id"]})
        snap[f"/api/console/runlog?plan={p['id']}"] = get("/api/console/runlog", {"plan": p["id"]})
    keep = set()
    for sid in ids:
        try:
            d = tracediff.diff(sid)
        except KeyError:
            continue
        snap[f"/api/console/trace?scenario={sid}"] = d
        keep.add(sid)
    for line in ("CP", "GL"):
        sc = [s for s in tracediff.scenarios(line) if s["scenario"] in keep]
        snap[f"/api/console/trace/scenarios?lob={line}"] = {"scenarios": sc, "total": len(sc)}
        snap[f"/api/console/trace/scenarios?lob={line}&differ=1"] = {"scenarios": [s for s in sc if s["agree"] is False],
                                                                     "total": sum(1 for s in sc if s["agree"] is False)}
    try:
        build = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=store.ROOT, capture_output=True, text=True,
                               timeout=10).stdout.strip()
    except Exception:                                         # noqa: BLE001
        build = ""
    meta = {"at": _t.strftime("%Y-%m-%d %H:%M"), "build": build, "traces": sorted(keep)}
    shim = """<script>
window.SNAP=__SNAP__;window.SNAPMETA=__META__;
(function(){const ok=(o,s)=>Promise.resolve(new Response(JSON.stringify(o),{status:s||200,headers:{'Content-Type':'application/json'}}));
window.fetch=function(u,o){u=String(u).replace(location.origin,'');
  if(o&&o.method&&o.method!=='GET')return ok({error:'This is a read-only snapshot: nothing can be changed or sent here. Use the console in the app.'},403);
  if(u in SNAP)return ok(SNAP[u]);
  const base=u.split('&state=')[0].split('&differ=')[0];
  if(u.startsWith('/api/console/trace/scenarios')&&(base in SNAP))return ok(SNAP[base]);
  return ok({error:'Not in this read-only snapshot ('+SNAPMETA.at+'). Open the console in the app for the live screen.'},404);};
document.addEventListener('DOMContentLoaded',()=>{const m=document.querySelector('main');if(m)m.insertAdjacentHTML('afterbegin',
  '<div class="mx-need" style="margin-bottom:12px"><span class="chip internal">·</span><div><b>Read-only snapshot</b> of the ISO Rating Test Console, '+SNAPMETA.at+(SNAPMETA.build?' · build '+SNAPMETA.build:'')+
  '<div class="mx-msg">The Matrix, the Coverage Board, the Regression Library, the Queue &amp; Run Log and '+SNAPMETA.traces.length+' Trace Diffs, as they stood. Nothing here sends or changes anything; the live console is in the app (Windows and Mac downloads on the ISO Project page).</div></div></div>');});
})();
</script>"""
    shim = shim.replace("__SNAP__", json.dumps(snap).replace("</", "<\\/")).replace("__META__", json.dumps(meta))
    html = page(app_only=frozenset({"compare", "plan", "workbench", "proof", "filings"}))
    i = html.index("<script>")
    return html[:i] + shim + html[i:]


def report(plan: dict, log: list) -> str:
    """D17: a plan's shareable, read-only report (no scripts, no calls), published with D6's snapshots."""
    from console import plans as P
    import html as H
    s = P.summary(plan)
    e = H.escape
    rows = "".join(
        f"<tr><td>{e(x['state'])}</td><td>{e(', '.join(f'{k}={v}' for k, v in x['config'].items()) or 'base risk')}</td>"
        f"<td>{e(x['kind'])}</td><td>{e(x['status'])}</td><td class=n>{e(str(x.get('oursNow') or x.get('ours') or ''))}</td>"
        f"<td class=n>{e(str(x.get('iso') or ''))}</td><td>{e(x.get('scenario', ''))}</td></tr>" for x in plan["scenarios"])
    na = "".join(f"<tr><td>{e(x['state'])}</td><td>{e(json.dumps(x['config']))}</td><td>{e(x.get('detail', ''))}</td></tr>"
                 for x in plan.get("notApplicable", []))
    p3 = plan.get("pass3") or {}
    logs = "".join(f"<tr><td>{e(x['at'])}</td><td>{e(x['event'])}</td><td>{e(x.get('state', ''))}</td><td>{e(x.get('detail', ''))}</td></tr>"
                   for x in log)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Plan report · {e(plan['name'])}</title><style>
:root{{--bg:#f3f2f2;--ink:#201f1d;--mute:#605d5d;--line:color-mix(in srgb,#201f1d 16%,transparent);--accent:#7d5411}}
body{{margin:0;background:var(--bg);color:var(--ink);font:13px/1.45 Georgia,serif}}main{{max-width:1100px;margin:0 auto;padding:24px 16px 60px}}
h1{{font-weight:400;font-size:32px;margin:0}}h2{{font-size:18px;margin:24px 0 6px}}.sub{{color:var(--mute)}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px;margin:16px 0;border-top:1px solid var(--ink);padding-top:10px}}
.stats b{{display:block;font-size:24px;font-weight:400}}.stats span{{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--mute)}}
table{{width:100%;border-collapse:collapse;font-size:12px}}td,th{{padding:4px 6px;border-top:1px solid var(--line);text-align:left;vertical-align:top}}
td.n{{text-align:right;font-variant-numeric:tabular-nums}}.wrap{{overflow-x:auto}}</style></head><body><main>
<div class=sub>ISO Rating Test Console · plan report (read-only)</div><h1>{e(plan['name'])}</h1>
<div class=sub>{e(plan['line'])} · committed {e(plan['committed_at'])}{' by ' + e(plan['by']) if plan.get('by') else ''} · status {e(plan['status'])} · lane {e(plan.get('lane', 'active'))}</div>
<div class=stats><div><span>Scenarios</span><b>{s['scenarios']}</b></div><div><span>Calls sent</span><b>{s['sent']}</b></div>
<div><span>Reused answers</span><b>{s['reused']}</b></div><div><span>Match</span><b>{s['match']}</b></div><div><span>Mismatch</span><b>{s['mismatch']}</b></div>
<div><span>Refused</span><b>{s['refused']}</b></div><div><span>Not reached</span><b>{s['notReached']}</b></div><div><span>Not expressible</span><b>{s['notApplicable']}</b></div></div>
<h2>Scenarios</h2><div class=wrap><table><tr><th>State</th><th>Config</th><th>Kind</th><th>Result</th><th>Ours</th><th>ISO</th><th>Scenario</th></tr>{rows}</table></div>
{'<h2>Not expressible in a state</h2><div class=wrap><table><tr><th>State</th><th>Config</th><th>Why</th></tr>' + na + '</table></div>' if na else ''}
{'<h2>Pass 3 (D15)</h2><div class=sub>' + e(json.dumps(p3.get('counts'))) + '</div>' if p3 else ''}
<h2>Run log</h2><div class=wrap><table><tr><th>At</th><th>Event</th><th>State</th><th>Detail</th></tr>{logs}</table></div>
</main></body></html>"""


def store_refs() -> list:
    from console import store
    return store.load()["references"]


def categories() -> list:
    from console import mismatch
    return [{"key": c.key, "label": c.label, "meaning": c.meaning} for c in mismatch.CATEGORIES]


def _line(query: dict) -> str:
    return "CP" if (query.get("lob") or "").upper() == "CP" else "GL"


def controls(line: str) -> dict:
    """D18's control x state grid beside the Coverage Board: which input controls have been rated (or only declined)
    in which states. GL's comes from the run store, the same data `/tester` drew it from (T11); CP has no control
    catalog until its dimension catalog (TC-26)."""
    if line != "GL":
        return {"line": line, "available": False,
                "why": "CP's controls arrive with its dimension catalog (TC-26); until then its paths are the grid."}
    import runstore
    cov = runstore.coverage()
    spec = variables.specs()
    rows = [{"id": c["id"], "label": c["label"], "group": c.get("group", ""),
             "rated": cov["rated"].get(c["id"], []), "declined": cov["declined"].get(c["id"], []),
             "values": cov["values"].get(c["id"], [])} for c in spec["controls"]]
    return {"line": line, "available": True, "states": sorted(spec["jurisdictions"]), "controls": rows,
            "exercised": sum(1 for r in rows if r["rated"])}


def sign_off(body: dict) -> tuple[int, dict]:
    """D4: a person may sign off a Passed cell; an empty name withdraws a sign-off. Nothing else is accepted."""
    from console import readiness
    line, state, cov, by = (str(body.get(k) or "").strip() for k in ("lob", "state", "coverage", "by"))
    cells = [c for c in readiness.get(line, state)["cells"] if c["coverage"] == cov and c["state"] == state]
    if not cells:
        return 404, {"error": f"no cell {line} {state} {cov}"}
    if by and cells[0]["status"] != "verified":
        return 409, {"error": "only a Passed cell can be signed off (D4)", "status": cells[0]["status"]}
    return 200, readiness.sign_off(line, state, cov, by)


def dispatch(method: str, path: str, query: dict, body):
    """Handle a console route, or return None so the caller keeps looking."""
    if method == "POST" and path == "/api/console/signoff":
        code, out = sign_off(body or {})
        return code, json.dumps(out), "json"
    if path.startswith("/api/console/plan") or path in ("/api/console/catalog", "/api/console/runlog",
                                                        "/api/console/refused", "/api/console/override",
                                                        "/api/console/runs") or path.startswith("/console/report/"):
        return planning(method, path, query, body or {})
    if method == "GET" and path.startswith("/runs/"):
        # D17: the standalone run files `/tests` wrote stay browsable (read-only), and `/`'s "Run files" link keeps working
        from console.store import RES
        name = path.rsplit("/", 1)[-1] or "index.html"
        f = RES / "runs" / name
        if ".." in name or "/" in name or "\\" in name or not f.is_file():
            return 404, json.dumps({"error": "no such run file"}), "json"
        return 200, f.read_text(encoding="utf-8"), "html"
    if method == "GET" and path == "/api/console/presets":
        from console import presets
        return 200, json.dumps({"presets": presets.presets()}), "json"
    if path.startswith("/api/console/inspect"):
        return inspect_routes(method, path, query, body or {})
    if path.startswith("/api/console/library"):
        return library_routes(method, path, query, body or {})
    if path.startswith("/api/console/workbench/"):
        return workbench(method, path.rsplit("/", 1)[-1], query, body or {})
    if method == "POST" and path == "/api/console/promote":
        from console import library
        b = body or {}
        try:
            e = library.promote(scenario=str(b.get("scenario") or ""), line=str(b.get("line") or ""),
                                state=str(b.get("state") or ""), origin=str(b.get("origin") or ""),
                                request_hash=str(b.get("hash") or ""), request=b.get("request"), ours=b.get("ours"),
                                by=str(b.get("by") or ""), note=str(b.get("note") or ""))
        except ValueError as exc:
            return 400, json.dumps({"error": str(exc)}), "json"
        return 200, json.dumps(e), "json"
    if method == "POST" and path == "/api/console/classify":
        code, out = classify(body or {})
        return code, json.dumps(out), "json"
    if method == "GET" and path == "/api/console/trace/scenarios":
        from console import tracediff
        sc = tracediff.scenarios(query.get("lob") or None, (query.get("state") or "").upper() or None)
        if query.get("differ") == "1":
            sc = [s for s in sc if s["agree"] is False]
        return 200, json.dumps({"scenarios": sc[:600], "total": len(sc)}), "json"
    if method == "GET" and path == "/api/console/trace":
        from console import tracediff
        try:
            return 200, json.dumps(tracediff.diff(query.get("scenario", ""))), "json"
        except KeyError as exc:
            return 404, json.dumps({"error": str(exc)}), "json"
    if method == "GET" and path == "/api/console/filings":
        from console import filings
        return 200, json.dumps(filings.filings()), "json"
    if method == "GET" and path == "/api/console/filings/source":
        from console import filings
        got = filings.source(query)
        if got is None:
            return 404, json.dumps({"error": "no such source document"}), "json"
        return 200, got[0], got[1]
    if method == "GET" and path == "/api/console/deviations/proof":
        from console import deviations_proof
        return 200, json.dumps(deviations_proof.proof()), "json"
    if method != "GET":
        return None
    if path == "/console":
        _dispatcher_on()                  # a plan left running resumes when the app restarts and the console opens
        return 200, page(), "html"
    if path == "/api/console/cap":
        return 200, json.dumps(cap()), "json"
    if path == "/api/console/legend":
        return 200, json.dumps(legend()), "json"
    if path == "/api/console/board":
        from console import board
        return 200, json.dumps(board.board(_line(query))), "json"
    if path == "/api/console/board/cell":
        from console import board
        return 200, json.dumps(board.cell(_line(query), query.get("state", "").upper(), query.get("path", ""))), "json"
    if path == "/api/console/board/find":
        from console import pathfind
        return 200, json.dumps(pathfind.find(_line(query), query.get("state", "").upper(), query.get("path", ""),
                                             want=min(int(query.get("want") or 3), 6))), "json"
    if path == "/api/console/controls":
        return 200, json.dumps(controls(_line(query))), "json"
    if path == "/api/console/readiness":
        from console import readiness
        return 200, json.dumps(readiness.get(query.get("lob"), query.get("state"),
                                             force=query.get("refresh") == "1")), "json"
    return None


def page(app_only: frozenset = frozenset()) -> str:
    """The console. `app_only`: screens a read-only snapshot replaces with a note (they need the running app)."""
    tabs = "".join(f'<a class="tab" href="#{k}" data-k="{k}">{label.replace("&", "&amp;")}</a>'
                   for k, label, _ in SCREENS)
    screens = "".join(
        (f'<section class="screen" id="s-{k}" hidden><div class="eyebrow">Interactive · in the app</div>'
         f'<h1>{label.replace("&", "&amp;")}</h1><div class="pending">This screen builds and rates scenarios, so it '
         f'needs the running app: start RecursiveHarness (Windows) or start.command (Mac) and open /console.'
         f'<span class="filter"></span></div></section>') if k in app_only else
        BUILT.get(k) or (f'<section class="screen" id="s-{k}" hidden><div class="eyebrow">Screen {i} of 7</div>'
                         f'<h1>{label.replace("&", "&amp;")}</h1><div class="pending">Built in {task} '
                         f'(docs/TC-PLAN.md).<span class="filter"></span></div></section>')
        for i, (k, label, task) in enumerate(SCREENS, 1))
    return (PAGE.replace("{{TABS}}", tabs).replace("{{SCREENS}}", screens)
            .replace("/*{{CSS}}*/", INSP_CSS + UP_CSS + MATRIX_CSS + BOARD_CSS + TRACE_CSS + WB_CSS + PLAN_CSS + QUEUE_CSS + LIB_CSS + PROOF_CSS + FILINGS_CSS)
            .replace("/*{{JS}}*/", INSP_JS + UP_JS + MATRIX_JS + BOARD_JS + TRACE_JS + WB_JS + PLAN_JS + QUEUE_JS + LIB_JS + PROOF_JS + FILINGS_JS)
            .replace("{{BOOT}}", json.dumps({"cap": cap(), "legend": legend(), "names": STATE_NAMES, "categories": categories()})))


# ---- TC-16: the Readiness Matrix -------------------------------------------------------------------------------------
# Rows: every state, alphabetical (D3). Columns: GL's coverages, then CP's. A cell's status is the server's (§3); the
# page only draws it. Click selects (the side panel says what the cell needs, §7); double-click opens the Coverage
# Board on that line and state. Sign-off (D4) only on a Passed cell. Nothing on this screen spends a call.

MATRIX_HTML = """<section class="screen" id="s-matrix" hidden><div class="mx-wrap"><div class="mx-main">
  <div class="mx-head"><div><div class="eyebrow">What's passed · what's still needed</div><h1>Readiness Matrix</h1></div>
    <p>Passed = every rating path in the coverage is RaaS-verified, with no open mismatches and no stale references.
    Click a cell to see what it needs; double-click to open it on the Coverage Board.</p></div>
  <div class="mx-stats" id="mx-stats"></div>
  <div class="mx-trend"><div class="mx-trend-hd"><span>Agreement with ISO over time</span><span class="mx-key" id="mx-key"></span></div>
    <div id="mx-chart"></div></div>
  <div class="mx-scroll"><div id="mx-grid" class="mx-grid" role="grid" aria-label="Readiness by state and coverage">
    <div class="mx-loading">Loading the matrix… (the first build after a change takes about half a minute)</div></div></div>
</div><aside class="mx-side" id="mx-side" aria-live="polite"></aside></div></section>"""

BUILT = {"matrix": MATRIX_HTML}

MATRIX_CSS = """
.mx-wrap{display:flex;gap:0;margin:0 -28px -32px;min-height:calc(100vh - 140px)}
.mx-main{flex:1;min-width:0;padding:0 28px 32px;display:flex;flex-direction:column;gap:16px}
.mx-head{display:flex;align-items:flex-end;gap:24px;flex-wrap:wrap}
.mx-head p{margin:0;padding-bottom:6px;font-size:13px;color:var(--color-neutral-700);max-width:560px}
.mx-stats{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));border-top:1px solid var(--color-text);
  border-bottom:1px solid var(--color-divider)}
.mx-stats div{padding:12px 18px 12px 0;border-right:1px solid var(--color-divider);margin-right:18px}
.mx-stats div:last-child{border-right:0}
.mx-stats span{display:block;font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--color-neutral-700)}
.mx-stats b{font:400 32px/1.1 var(--font-heading)}
.mx-stats small{font-size:12px;color:var(--color-neutral-700);margin-left:6px}
.mx-trend-hd{display:flex;justify-content:space-between;align-items:baseline;font-size:11px;letter-spacing:.08em;
  text-transform:uppercase;color:var(--color-neutral-700);margin-bottom:4px}
.mx-key{display:flex;gap:14px;text-transform:none;letter-spacing:0;font-size:12px;color:var(--color-text)}
.mx-key i{display:inline-block;width:14px;height:2px;vertical-align:middle;margin-right:5px;border-radius:1px}
#mx-chart{position:relative;height:120px}
#mx-chart svg{display:block;width:100%;height:100%;overflow:visible}
.mx-empty{height:100%;display:flex;align-items:center;justify-content:center;border:1px dashed var(--color-neutral-400);
  border-radius:var(--radius-md);color:var(--color-neutral-700);font-size:12.5px}
.mx-tip{position:absolute;pointer-events:none;background:#fff;border:1px solid var(--color-divider);border-radius:4px;
  box-shadow:0 3px 10px color-mix(in srgb,#2d2b2b 16%,transparent);padding:6px 9px;font-size:12px;white-space:nowrap;z-index:5}
.mx-scroll{overflow-x:auto}
.mx-grid{display:grid;gap:4px;min-width:1040px}
.mx-loading{grid-column:1/-1;padding:24px;color:var(--color-neutral-700)}
.mx-lob{font:600 18px var(--font-heading);border-bottom:1px solid var(--color-text);padding-bottom:3px}
.mx-col{font-size:12px;line-height:1.2;padding:0 2px 4px;align-self:end}
.mx-colr{font-size:10.5px;color:var(--color-neutral-700);text-align:right;padding-bottom:4px;align-self:end}
.mx-st{display:flex;align-items:center;gap:8px;min-width:0}
.mx-st b{font:600 18px var(--font-heading);width:28px;flex:none}
.mx-st span{font-size:12px;color:var(--color-neutral-700);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.mx-sum{display:flex;align-items:center;justify-content:flex-end;font-weight:600}
.mx-cell{width:auto;overflow:hidden;height:40px;border-radius:2px;cursor:pointer;display:flex;flex-direction:column;align-items:flex-start;
  justify-content:center;padding:0 6px;line-height:1.2;text-align:left;font:inherit;min-width:0;position:relative}
.mx-cell:hover{filter:brightness(.95)}
.mx-cell:focus-visible,.mx-cell.sel{outline:2px solid var(--color-text);outline-offset:2px}
.mx-cell .l1,.mx-cell .l2{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%}
.mx-cell .l1{font-size:11.5px;font-weight:600;letter-spacing:-.01em}
.mx-cell .l2{font-size:10.5px}
.mx-cell .so{position:absolute;top:3px;right:5px;font-size:10px}
.mx-side{width:380px;flex:none;position:sticky;top:var(--hdr,66px);align-self:flex-start;max-height:calc(100vh - var(--hdr,66px));overflow-y:auto;border-left:1px solid var(--color-divider);padding:24px;background:#f8f4f4;
  display:flex;flex-direction:column;gap:14px}
.mx-back{font-size:12px;text-decoration:none}
.mx-list{display:flex;flex-direction:column}
.mx-lh,.mx-li{display:grid;grid-template-columns:22px 30px 28px minmax(0,1fr) 56px;gap:8px;align-items:center}
.mx-lh{padding-bottom:5px;border-bottom:1px solid var(--color-text);font-size:10.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--color-neutral-700)}
.mx-lh span:last-child,.mx-ln{text-align:right}
.mx-li{padding:7px 0;border:0;border-bottom:1px solid var(--color-divider);background:transparent;font:inherit;font-size:12.5px;
  color:var(--color-text);text-align:left;cursor:pointer}
.mx-li:hover{background:var(--color-accent-100)}
.mx-li .chip{width:20px;height:16px;font-size:10px}
.mx-lc{display:flex;flex-direction:column;line-height:1.25;min-width:0}
.mx-lc small,.mx-ln small{font-size:11.5px;color:var(--color-neutral-700)}
.mx-ln small{display:block;font-size:10px}
.mx-more{align-self:flex-start;border:0;background:transparent;color:var(--color-accent-700);cursor:pointer;font:inherit;font-size:12.5px;padding:0;text-decoration:underline}
.mx-side h2{margin:0;font:600 24px/1.15 var(--font-heading)}
.mx-side .cap2{font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--color-neutral-700)}
.mx-side table{width:100%;border-collapse:collapse;font-size:12.5px}
.mx-side td{padding:6px 0;border-bottom:1px solid var(--color-divider);vertical-align:top}
.mx-side td:last-child{text-align:right;white-space:nowrap;padding-left:10px}
.mx-need{display:flex;gap:10px;align-items:center;padding:10px 12px;border:1px solid var(--color-divider);border-radius:4px;background:var(--color-bg)}
.mx-need b{font:600 16px var(--font-heading)}
.mx-so{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.mx-so input{font:inherit;padding:6px 8px;border:1px solid var(--color-divider);border-radius:4px;background:#fff;flex:1;min-width:120px}
.btn{border:1px solid var(--color-accent);color:var(--color-accent-700);background:transparent;border-radius:4px;
  padding:7px 12px;cursor:pointer;font:600 14px var(--font-heading)}
.btn:hover{background:var(--color-accent-100)}
.btn[disabled]{opacity:.5;cursor:default}
.mx-msg{font-size:12px;color:var(--color-neutral-700)}
@media (max-width:1100px){.mx-wrap{flex-direction:column}.mx-side{width:auto;border-left:0;border-top:1px solid var(--color-divider)}
  .mx-stats{grid-template-columns:repeat(2,minmax(0,1fr))}}
"""

MATRIX_JS = r"""
const MX={data:null,sel:null,all:false};
const SERIES={GL:{name:'General Liability',color:'#2f72a8'},CP:{name:'Commercial Property',color:'#9a6214'}};
const LG=Object.fromEntries(BOOT.legend.map(s=>[s.key,s]));
const SHORT={internal:'Internal',na:'n/a'};   // the cell's own label; the full one is in the title and side panel
function mxCols(r){const g=r.columns.GL||[],c=r.columns.CP||[];  // GL first, as the prototype
  return '150px'+(g.length?' repeat('+g.length+',minmax(0,1fr)) 52px':'')+(g.length&&c.length?' 24px':'')+(c.length?' repeat('+c.length+',minmax(0,1fr)) 52px':'');}
function mxLoad(force){
  return fetch('/api/console/readiness'+(force?'?refresh=1':'')).then(r=>r.json()).then(r=>{MX.data=r;mxDraw();});
}
function mxKey(c){return c.lob+'|'+c.state+'|'+c.coverage}
function mxCell(c){
  const s=LG[c.status],p=c.paths;
  const l2=c.status==='na'?'not filed':(p.raasVerified+' / '+p.inScope+' paths');
  return '<button class="mx-cell chip '+c.status+(MX.sel===mxKey(c)?' sel':'')+'" data-k="'+esc(mxKey(c))+'" role="gridcell" '+
    'title="'+esc(c.state+' · '+c.lob+' · '+c.coverage+' · '+s.matrix)+'"><span class="l1">'+esc(s.glyph+' '+(SHORT[c.status]||s.matrix))+
    '</span><span class="l2">'+esc(l2)+'</span>'+(c.signedOffBy?'<span class="so" title="Signed off by '+esc(c.signedOffBy)+'">✍</span>':'')+'</button>';
}
function mxDraw(){
  const r=MX.data,T=r.totals,lobs=['GL','CP'].filter(l=>r.columns[l]);
  const stat=(k,v,sub)=>'<div><span>'+k+'</span><b>'+v+'</b>'+(sub?'<small>'+sub+'</small>':'')+'</div>';
  document.getElementById('mx-stats').innerHTML=lobs.map(l=>stat(l+' passed',T[l].passed+' <small>of '+T[l].cells+'</small>',
      T[l].signedOff?T[l].signedOff+' signed off':'')).join('')+
    stat('Still to test',T.stillToTest)+stat('Est. RaaS calls to finish',T.estCallsToFinish.toLocaleString(),
      T.staleCalls?T.staleCalls+' from the refresh lane':'')+stat('At 150/day',T.daysAtActiveLane+' days');
  mxTrend(r.agreement||{});
  const by={};r.cells.forEach(c=>by[mxKey(c)]=c);
  const states=[...new Set(r.cells.map(c=>c.state))].sort();
  const g=document.getElementById('mx-grid');g.style.gridTemplateColumns=mxCols(r);
  let h='<span></span>';
  lobs.forEach((l,i)=>{if(i)h+='<span></span>';h+='<span class="mx-lob" style="grid-column:span '+(r.columns[l].length+1)+'">'+SERIES[l].name+'</span>';});
  h+='<span class="mx-colr" style="text-align:left;letter-spacing:.08em;text-transform:uppercase">State</span>';
  lobs.forEach((l,i)=>{if(i)h+='<span></span>';h+=r.columns[l].map(c=>'<span class="mx-col">'+esc(c)+'</span>').join('')+'<span class="mx-colr">Passed</span>';});
  states.forEach(st=>{
    h+='<span class="mx-st"><b>'+st+'</b><span>'+esc(BOOT.names[st]||'')+'</span></span>';
    lobs.forEach((l,i)=>{if(i)h+='<span></span>';
      const row=r.columns[l].map(cov=>by[l+'|'+st+'|'+cov]);
      if(!row[0]){h+='<span class="mx-colr" style="grid-column:span '+(row.length+1)+';align-self:center;text-align:left">'+l+' not offered here</span>';return;}
      h+=row.map(mxCell).join('');
      const counted=row.filter(c=>c.status!=='na'),pass=counted.filter(c=>c.status==='verified').length;
      h+='<span class="mx-sum" style="color:'+(counted.length&&pass===counted.length?'var(--color-accent-700)':'var(--color-text)')+'">'+pass+'/'+counted.length+'</span>';
    });
  });
  g.innerHTML=h;
  if(MX.sel&&by[MX.sel])mxSide(by[MX.sel]);else{MX.sel=null;mxList();}
}
function mxTrend(A){
  const el=document.getElementById('mx-chart'),key=document.getElementById('mx-key');
  const lines=Object.keys(SERIES).filter(l=>(A[l]||[]).some(d=>d.compared));
  key.innerHTML=lines.map(l=>'<span><i style="background:'+SERIES[l].color+'"></i>'+l+'</span>').join('');
  if(!lines.length){el.innerHTML='<div class="mx-empty">No comparisons with ISO recorded yet. The trend starts with the first scenario that has both premiums.</div>';return;}
  const days=[...new Set(lines.flatMap(l=>A[l].map(d=>d.day)))].sort();
  const W=el.clientWidth||800,H=120,L=36,R=60,Tp=8,B=20;
  const x=d=>days.length<2?L+(W-L-R)/2:L+(W-L-R)*days.indexOf(d)/(days.length-1),y=p=>Tp+(H-Tp-B)*(1-p/100);
  let s='<svg viewBox="0 0 '+W+' '+H+'" role="img" aria-label="Agreement with ISO over time, per line">';
  [0,50,100].forEach(p=>s+='<line x1="'+L+'" x2="'+(W-R)+'" y1="'+y(p)+'" y2="'+y(p)+'" stroke="var(--color-divider)" stroke-width="1"/>'+
    '<text x="'+(L-6)+'" y="'+(y(p)+4)+'" text-anchor="end" font-size="10.5" fill="var(--color-neutral-700)">'+p+'%</text>');
  [days[0],days[days.length-1]].filter((d,i,a)=>a.indexOf(d)===i).forEach((d,i)=>s+='<text x="'+x(d)+'" y="'+(H-4)+'" text-anchor="'+(days.length<2?'middle':i?'end':'start')+'" font-size="10.5" fill="var(--color-neutral-700)">'+d+'</text>');
  const ends={};lines.forEach(l=>{const d=A[l].filter(v=>v.compared).pop();ends[l]=y(100*d.agreed/d.compared);});
  if(lines.length===2&&Math.abs(ends[lines[0]]-ends[lines[1]])<13){const m=(ends[lines[0]]+ends[lines[1]])/2,up=ends[lines[0]]<=ends[lines[1]]?0:1;
    ends[lines[up]]=m-6.5;ends[lines[1-up]]=m+6.5;}   // keep the two end labels from overlapping
  lines.forEach(l=>{const pts=A[l].filter(d=>d.compared).map(d=>[x(d.day),y(100*d.agreed/d.compared),d]);
    s+='<polyline fill="none" stroke="'+SERIES[l].color+'" stroke-width="2" stroke-linejoin="round" points="'+pts.map(p=>p[0]+','+p[1]).join(' ')+'"/>';
    pts.forEach(p=>s+='<circle cx="'+p[0]+'" cy="'+p[1]+'" r="4" fill="'+SERIES[l].color+'" stroke="var(--color-bg)" stroke-width="2"/>');
    const e=pts[pts.length-1];s+='<text x="'+(e[0]+8)+'" y="'+(ends[l]+4)+'" font-size="11" fill="var(--color-text)">'+l+' '+Math.round(100*e[2].agreed/e[2].compared)+'%</text>';});
  s+='<line id="mx-x" y1="'+Tp+'" y2="'+(H-B)+'" stroke="var(--color-neutral-500)" stroke-width="1" visibility="hidden"/></svg><div class="mx-tip" id="mx-tip" hidden></div>';
  el.innerHTML=s;
  const svg=el.querySelector('svg'),tip=document.getElementById('mx-tip'),xl=document.getElementById('mx-x');
  svg.addEventListener('mousemove',ev=>{const bx=svg.getBoundingClientRect(),px=(ev.clientX-bx.left)*W/bx.width;
    let best=days[0];days.forEach(d=>{if(Math.abs(x(d)-px)<Math.abs(x(best)-px))best=d;});
    xl.setAttribute('x1',x(best));xl.setAttribute('x2',x(best));xl.setAttribute('visibility','visible');
    tip.innerHTML='<b>'+best+'</b>'+lines.map(l=>{const d=A[l].find(v=>v.day===best);return d?'<div><span style="color:'+SERIES[l].color+'">●</span> '+l+': '+d.agreed+' of '+d.compared+' agree ('+Math.round(100*d.agreed/d.compared)+'%)</div>':'';}).join('');
    tip.hidden=false;tip.style.left=Math.min(x(best)*bx.width/W+12,bx.width-220)+'px';tip.style.top='4px';});
  svg.addEventListener('mouseleave',()=>{tip.hidden=true;xl.setAttribute('visibility','hidden');});
}
function mxSide(c){
  const s=LG[c.status],p=c.paths,labels=(MX.data.pathLabels||{})[c.lob]||{};
  let h='<a href="#matrix" class="mx-back" id="mx-back">← Still to test</a><div class="cap2">'+esc(c.lob+' · '+(BOOT.names[c.state]||c.state))+'</div><h2>'+esc(c.coverage)+'</h2>';
  h+='<div class="mx-need"><span class="chip '+c.status+'">'+esc(s.glyph)+'</span><div><b>'+esc(s.matrix)+'</b><div class="mx-msg">'+
    esc(c.status==='na'?'The state files no such path; never counted as a gap (D5).':c.status==='verified'?'Nothing needed.':
      s.needs+' · about '+c.estRemainingCalls+' call'+(c.estRemainingCalls===1?'':'s'))+'</div></div></div>';
  if(p.inScope){h+='<div class="cap2">Paths · '+p.raasVerified+' of '+p.inScope+' verified, '+p.walked+' walked</div><table>'+
    Object.entries(p.byPath).map(([id,st])=>'<tr><td>'+esc(labels[id]||id)+'</td><td><span class="chip '+st+'" title="'+esc(LG[st].matrix)+'">'+esc(LG[st].glyph)+'</span> '+esc(LG[st].board)+'</td></tr>').join('')+'</table>';}
  if(p.descoped.length)h+='<div class="cap2">Descoped</div><table>'+p.descoped.map(d=>'<tr><td>'+esc(labels[d.pathId]||d.pathId)+'</td><td>'+esc(d.reason)+'</td></tr>').join('')+'</table>';
  if(c.openMismatches.length)h+='<div class="cap2">Open mismatches</div><table>'+c.openMismatches.map(m=>'<tr><td>'+esc(m.scenarioId)+'<div class="mx-msg">'+esc(m.category.replace(/_/g,' '))+'</div></td><td>'+esc((+m.delta>0?'+':'')+m.delta)+'</td></tr>').join('')+'</table>';
  h+='<table><tr><td>Scenarios</td><td>'+c.scenarios+'</td></tr><tr><td>Content in force</td><td>'+esc(c.contentVersion||'—')+'</td></tr><tr><td>Last evidence</td><td>'+esc(c.lastChangedAt||'—')+'</td></tr></table>';
  if(c.status==='verified'){
    h+='<div class="cap2">Sign-off (optional)</div>'+(c.signedOffBy?
      '<div class="mx-so"><span>✍ Signed off by <b>'+esc(c.signedOffBy)+'</b>, '+esc((c.signedOffAt||'').slice(0,10))+'</span><button class="btn" id="mx-unsign">Withdraw</button></div>':
      '<div class="mx-so"><input id="mx-by" placeholder="Your name" aria-label="Your name"><button class="btn" id="mx-sign">Sign off</button></div>')+
      '<div class="mx-msg">A sign-off clears itself if the cell leaves Passed (D4).</div><div class="mx-msg" id="mx-somsg"></div>';
  }
  h+='<button class="btn" id="mx-open" style="margin-top:auto">Open on the Coverage Board</button>';
  const side=document.getElementById('mx-side');side.innerHTML=h;
  const send=by=>fetch('/api/console/signoff',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({lob:c.lob,state:c.state,coverage:c.coverage,by})}).then(r=>r.json().then(j=>{if(!r.ok)throw j.error;}))
    .then(()=>mxLoad()).catch(e=>{const m=document.getElementById('mx-somsg');if(m)m.textContent=String(e);});
  const sb=document.getElementById('mx-sign');if(sb)sb.onclick=()=>{const v=document.getElementById('mx-by').value.trim();if(v){sb.disabled=true;send(v);}};
  const ub=document.getElementById('mx-unsign');if(ub)ub.onclick=()=>{ub.disabled=true;send('');};
  document.getElementById('mx-open').onclick=()=>mxOpen(c);
  document.getElementById('mx-back').onclick=ev=>{ev.preventDefault();MX.sel=null;
    document.querySelectorAll('.mx-cell.sel').forEach(x=>x.classList.remove('sel'));mxList();};
}
// TC-17: "Still to test" (§6 without waves, D3): mismatch, stale, internal-only, untested; then most calls first.
function mxList(){
  const L=MX.data.stillToTest||[],T=MX.data.totals,n=MX.all?L.length:Math.min(14,L.length);
  let h='<div class="cap2">Still to test · '+L.length+' state-coverage'+(L.length===1?'':'s')+'</div>'+
    '<div class="mx-msg">Mismatches first, then stale, internal-only, untested; within each, the most calls first. Click a row to see the cell.</div>';
  if(!L.length){h+='<div class="mx-need"><span class="chip verified">✓</span><div><b>Nothing left</b><div class="mx-msg">Every applicable cell has Passed.</div></div></div>';}
  else{
    h+='<div class="mx-list"><div class="mx-lh"><span></span><span>St.</span><span>LOB</span><span>Coverage · needs</span><span>Calls</span></div>'+
      L.slice(0,n).map(g=>'<button class="mx-li" data-k="'+esc(g.lob+'|'+g.state+'|'+g.coverage)+'"><span class="chip '+g.status+'">'+esc(LG[g.status].glyph)+'</span>'+
        '<b>'+esc(g.state)+'</b><span>'+esc(g.lob)+'</span><span class="mx-lc"><span>'+esc(g.coverage)+'</span><small>'+esc(LG[g.status].matrix+' · '+g.needs)+
        '</small></span><span class="mx-ln">'+g.calls+(g.lane==='refresh'?'<small>refresh</small>':'')+'</span></button>').join('')+'</div>';
    if(L.length>14)h+='<button class="mx-more" id="mx-more">'+(MX.all?'Show the first 14':'Show all '+L.length)+'</button>';
  }
  h+='<table><tr><td>Est. RaaS calls to finish</td><td>'+T.estCallsToFinish.toLocaleString()+'</td></tr>'+
    '<tr><td>Days at the active lane (150/day)</td><td>'+T.daysAtActiveLane+'</td></tr>'+
    (T.staleCalls?'<tr><td>Of which stale refreshes, in the refresh lane (50/day)</td><td>'+T.staleCalls+' · '+T.daysAtRefreshLane+' days</td></tr>':'')+'</table>'+
    '<div class="mx-msg">Estimates are one call per unverified path (or per stale reference, or per open mismatch to re-verify); the pairwise design of a test plan and stored answers bring them down.</div>';
  if(L.length)h+='<button class="btn" id="mx-plan" style="margin-top:auto">Build a test plan from these gaps</button><div class="mx-msg">No calls are spent until a plan is committed.</div>';
  const side=document.getElementById('mx-side');side.innerHTML=h;
  side.querySelectorAll('.mx-li').forEach(b=>b.onclick=()=>{const c=MX.data.cells.find(x=>mxKey(x)===b.dataset.k);if(!c)return;
    MX.sel=b.dataset.k;document.querySelectorAll('.mx-cell.sel').forEach(x=>x.classList.remove('sel'));
    const el=document.querySelector('.mx-cell[data-k="'+CSS.escape(MX.sel)+'"]');if(el){el.classList.add('sel');el.scrollIntoView({block:'center',behavior:'smooth'});}
    mxSide(c);});
  const more=document.getElementById('mx-more');if(more)more.onclick=()=>{MX.all=!MX.all;mxList();};
  const plan=document.getElementById('mx-plan');if(plan)plan.onclick=()=>{
    const lob=L[0].lob,G=L.filter(g=>g.lob===lob);   // one line per plan: the line of the most urgent gap
    location.hash='#plan?lob='+lob+'&states='+encodeURIComponent([...new Set(G.map(g=>g.state))].join(','))+'&coverages='+encodeURIComponent([...new Set(G.map(g=>g.coverage))].join('|'));};
}
function mxOpen(c){location.hash='#board?lob='+encodeURIComponent(c.lob)+'&state='+encodeURIComponent(c.state)+'&coverage='+encodeURIComponent(c.coverage);}
document.getElementById('mx-grid').addEventListener('click',ev=>{const b=ev.target.closest('.mx-cell');if(!b)return;
  MX.sel=b.dataset.k;document.querySelectorAll('.mx-cell.sel').forEach(x=>x.classList.remove('sel'));b.classList.add('sel');
  const c=MX.data.cells.find(x=>mxKey(x)===MX.sel);if(c)mxSide(c);});
document.getElementById('mx-grid').addEventListener('dblclick',ev=>{const b=ev.target.closest('.mx-cell');if(!b)return;
  const c=MX.data.cells.find(x=>mxKey(x)===b.dataset.k);if(c)mxOpen(c);});
addEventListener('resize',()=>{if(MX.data)mxTrend(MX.data.agreement||{});});
mxLoad().catch(e=>{document.getElementById('mx-grid').innerHTML='<div class="mx-loading">Could not load the matrix: '+esc(String(e))+'</div>';});
setInterval(()=>{if(!document.getElementById('s-matrix').hidden)mxLoad().catch(()=>{});},60000);
"""


# D7: the prototype's palette, radii and type scale, in one stylesheet. Its fonts (Cormorant Garamond, Lora) are
# used when installed and otherwise fall back to system serifs; nothing is fetched.
PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ISO Rating Test Console</title>
<style>
:root{
  --color-bg:#f3f2f2;--color-surface:#eae9e9;--color-text:#201f1d;
  --color-divider:color-mix(in srgb,#201f1d 16%,transparent);
  --color-accent:#b68235;--color-accent-100:#fff3e4;--color-accent-300:#facb8d;--color-accent-400:#e1ad66;
  --color-accent-500:#c28d41;--color-accent-700:#7d5411;--color-accent-800:#5a3b0a;
  --color-neutral-300:#d7d3d3;--color-neutral-400:#bab6b6;--color-neutral-500:#9b9797;--color-neutral-600:#7d7979;
  --color-neutral-700:#605d5d;--color-neutral-900:#2d2b2b;
  --ox:oklch(0.50 0.14 28);--ox-tint:oklch(0.96 0.025 28);--ox-deep:oklch(0.42 0.13 28);
  --font-heading:"Cormorant Garamond",Garamond,"Iowan Old Style",Georgia,serif;
  --font-body:"Lora",Georgia,"Times New Roman",serif;
  --radius-sm:2px;--radius-md:4px;--radius-lg:7px;
}
*{box-sizing:border-box}
body{margin:0;background:var(--color-bg);color:var(--color-text);font:13px/1.45 var(--font-body);
  font-variant-numeric:tabular-nums}
a{color:var(--color-accent-700)}
header{position:sticky;top:0;z-index:30;display:flex;align-items:stretch;gap:20px;padding:0 24px;min-height:66px;
  background:var(--color-bg);border-bottom:1px solid var(--color-divider);flex-wrap:wrap}
.brand{display:flex;flex-direction:column;justify-content:center;gap:1px;min-width:200px}
.brand b{font:600 21px/1.1 var(--font-heading);letter-spacing:-.01em}
.brand span{font-size:11px;color:var(--color-neutral-700)}
nav{display:flex;align-items:stretch;gap:4px;flex-wrap:wrap}
.tab{display:flex;align-items:center;padding:0 8px;border-bottom:2px solid transparent;color:var(--color-text);
  text-decoration:none;font:600 14.5px var(--font-heading);white-space:nowrap}
.tab:hover{color:var(--color-accent-700)}
.tab[aria-current="page"]{color:var(--color-accent-700);border-bottom-color:var(--color-accent)}
.cap{margin-left:auto;display:flex;align-items:center;gap:16px;padding:8px 0}
.lanes{display:flex;flex-direction:column;gap:5px;width:370px;max-width:100%}
.lanes .hd{display:flex;justify-content:space-between;font-size:10.5px;letter-spacing:.08em;text-transform:uppercase;
  color:var(--color-neutral-700)}
.lanes .bars,.lanes .lbl{display:flex;gap:3px}
.lanes .bars{height:10px}
.lanes .bars div{border:1px solid var(--color-accent-400);border-radius:2px;overflow:hidden;display:flex}
.lanes .bars i{display:block;height:100%}
.lanes .lbl div{font-size:10px;color:var(--color-neutral-700);white-space:nowrap;min-width:0}
.lanes .full{border-color:var(--ox)!important}
.nums{display:flex;gap:14px;align-items:baseline}
.nums div{display:flex;flex-direction:column}
.nums span{font-size:10.5px;color:var(--color-neutral-700);letter-spacing:.06em;text-transform:uppercase}
.nums b{font:600 22px/1 var(--font-heading)}
.nums b.left{color:var(--color-accent-700)}
.nums small{font-size:12.5px;line-height:1.3}
main{padding:24px 28px 32px}
.eyebrow{font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--color-accent-700)}
h1{margin:2px 0 0;font:400 38px/1.15 var(--font-heading)}
.pending{margin-top:18px;padding:18px;border:1px dashed var(--color-neutral-400);border-radius:var(--radius-lg);
  color:var(--color-neutral-700);max-width:640px}
.legend{display:flex;align-items:center;gap:22px;flex-wrap:wrap;font-size:12px;margin:0 0 18px;padding:10px 0;
  border-bottom:1px solid var(--color-divider)}
.legend>span:first-child{font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--color-neutral-700)}
.legend .k{display:flex;align-items:center;gap:7px}
.chip{width:26px;height:18px;display:inline-flex;align-items:center;justify-content:center;border-radius:2px;font-size:11px}
.chip.verified{background:var(--color-accent-700);color:var(--color-accent-100);border:1px solid var(--color-accent-700)}
.chip.internal{background:var(--color-accent-100);color:var(--color-accent-800);border:1px solid var(--color-accent-300)}
.chip.mismatch{background:var(--ox-tint);color:var(--ox-deep);border:1.5px solid var(--ox)}
.chip.stale{background:repeating-linear-gradient(135deg,var(--color-neutral-300) 0 1.5px,transparent 1.5px 6px);
  color:var(--color-neutral-900);border:1px solid var(--color-neutral-500)}
.chip.untested{background:transparent;color:var(--color-neutral-600);border:1px dashed var(--color-neutral-400)}
.chip.na{background:var(--color-surface);color:var(--color-neutral-500);border:1px solid var(--color-surface)}
@media (max-width:900px){header{padding:0 16px}main{padding:16px}.cap{margin-left:0;flex-wrap:wrap}}
/*{{CSS}}*/
</style></head><body>
<header>
  <div class="brand"><b>ISO Rating Test Console</b><span>Internal engine vs. ISO RaaS (UAT) · GL &amp; CP · <a href="/" title="The rating page: paste or edit one submission and rate it">Rate a submission</a></span></div>
  <nav>{{TABS}}</nav>
  <div class="cap" title="Every ISO call, wherever it starts, counts here (D21)">
    <div class="lanes"><div class="hd"><span id="cap-hd"></span><span id="cap-ov"></span></div>
      <div class="bars" id="cap-bars"></div><div class="lbl" id="cap-lbl"></div></div>
    <div class="nums">
      <div><span>Used</span><b id="cap-used"></b></div>
      <div><span>Left</span><b class="left" id="cap-left"></b></div>
      <div><span>Queued</span><b id="cap-queued"></b></div>
      <div><span>Resets</span><small id="cap-reset"></small></div>
    </div>
  </div>
</header>
<main>
  <div class="legend" id="legend"><span>Cell state</span></div>
  {{SCREENS}}
</main>
<script>
const BOOT={{BOOT}};
const FILL={active:'var(--color-accent-700)',refresh:'var(--color-accent-500)',adhoc:'var(--color-accent-300)'};
function esc(s){return String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
function drawCap(c){
  document.getElementById('cap-hd').textContent='RaaS UAT · daily cap '+c.cap;
  document.getElementById('cap-ov').textContent=c.overrides?c.overrides+' override'+(c.overrides>1?'s':'')+' today':'';
  document.getElementById('cap-bars').innerHTML=c.lanes.map(l=>'<div style="flex:'+l.cap+'" class="'+(l.used>=l.cap?'full':'')+
    '" title="'+esc(l.name)+': '+l.used+' of '+l.cap+'"><i style="width:'+Math.min(100,100*l.used/l.cap)+'%;background:'+FILL[l.key]+'"></i></div>').join('');
  document.getElementById('cap-lbl').innerHTML=c.lanes.map(l=>'<div style="flex:'+l.cap+'">'+esc(l.name.split(' ')[0])+' '+l.used+'/'+l.cap+'</div>').join('');
  document.getElementById('cap-used').textContent=c.used;
  document.getElementById('cap-left').textContent=c.left;
  document.getElementById('cap-queued').textContent=c.queued;
  const m=Math.round(c.resets_in_s/60);
  document.getElementById('cap-reset').textContent='00:00 ET · '+Math.floor(m/60)+'h '+(m%60)+'m';
}
function drawLegend(L){
  document.getElementById('legend').insertAdjacentHTML('beforeend',L.map(s=>'<span class="k" title="'+esc(s.meaning)+
    '"><span class="chip '+s.key+'">'+esc(s.glyph)+'</span>'+esc(s.key==='verified'?s.board+' / '+s.matrix:s.board)+'</span>').join(''));
}
function route(){
  const [k,q]=(location.hash||'#compare').slice(1).split('?');
  const ok=document.getElementById('s-'+k)?k:'compare';
  const f=document.querySelector('#s-'+ok+' .filter');
  if(f)f.textContent=q?' Opened for '+[...new URLSearchParams(q).values()].join(' · ')+'.':'';
  document.querySelectorAll('.screen').forEach(s=>s.hidden=s.id!=='s-'+ok);
  document.querySelectorAll('.tab').forEach(t=>t.dataset.k===ok?t.setAttribute('aria-current','page'):t.removeAttribute('aria-current'));
}
drawCap(BOOT.cap);drawLegend(BOOT.legend);route();
// the header wraps on narrow windows; sticky panels sit below its real height
const hdr=()=>document.documentElement.style.setProperty('--hdr',document.querySelector('header').offsetHeight+'px');
hdr();addEventListener('resize',hdr);
addEventListener('hashchange',route);
setInterval(()=>fetch('/api/console/cap').then(r=>r.json()).then(drawCap).catch(()=>{}),30000);
/*{{JS}}*/
</script>
</body></html>"""


# ---- TC-18: the Coverage Board --------------------------------------------------------------------------------------
# One line at a time: states (alphabetical, D3) x rating paths, grouped under their most specific coverage; a cell's
# number is the scenarios that walked the path there (mismatch and stale cells show the affected count first). The
# verdict per state is `console.board.verdict`. Beside it, D18's control x state grid. Nothing here spends a call.

BOARD_HTML = """<section class="screen" id="s-board" hidden><div class="mx-wrap"><div class="mx-main">
  <div class="mx-head"><div><div class="eyebrow">Go / no-go · straight ISO build</div><h1>Coverage Board</h1></div>
    <p>Rows: states · Columns: rating paths, grouped by coverage · Click a cell for its scenarios, a state for its
    readiness. Number = scenarios in the cell (mismatch and stale cells show the affected count).</p>
    <div class="bd-lines" id="bd-lines" role="group" aria-label="Line"><button data-l="GL">General Liability</button><button data-l="CP">Commercial Property</button></div></div>
  <div class="mx-stats bd-stats" id="bd-stats"></div>
  <div class="mx-scroll bd-scroll"><div id="bd-grid" class="bd-grid"><div class="mx-loading">Loading the board…</div></div></div>
  <div class="bd-ctl"><div class="mx-trend-hd"><span>Controls × states · which inputs have been rated where</span>
    <span class="mx-key"><span><b class="bd-dot r"></b>rated there</span><span><b class="bd-dot d"></b>asked, not declarable there</span><span><b class="bd-dot"></b>never run</span></span></div>
    <div class="mx-scroll"><div id="bd-ctl"></div></div></div>
</div><aside class="mx-side" id="bd-side" aria-live="polite"></aside></div></section>"""

BUILT["board"] = BOARD_HTML

BOARD_CSS = """
.bd-lines{margin-left:auto;display:flex;border:1px solid var(--color-divider);border-radius:4px;overflow:hidden}
.bd-lines button{border:0;border-right:1px solid var(--color-divider);background:transparent;padding:7px 16px;cursor:pointer;
  font:inherit;font-size:13px;color:var(--color-text)}
.bd-lines button:last-child{border-right:0}
.bd-lines button[aria-pressed="true"]{background:var(--color-accent-100);color:var(--color-accent-800);box-shadow:inset 0 -2px 0 var(--color-accent)}
.bd-stats{grid-template-columns:1fr 1fr 1.6fr 1fr 1fr 1fr}
.bd-cats{display:grid;grid-template-columns:1fr auto;gap:1px 10px;font-size:11.5px;margin-top:4px}
.bd-cats .def{color:var(--ox-deep)}
.bd-grid{display:grid;gap:3px;align-items:stretch}
.bd-grp{font-size:10.5px;letter-spacing:.03em;color:var(--color-neutral-700);border-bottom:1px solid var(--color-text);
  padding-bottom:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bd-ph{writing-mode:vertical-rl;transform:rotate(180deg);font-size:10.5px;line-height:1.1;height:132px;overflow:hidden;
  text-overflow:ellipsis;white-space:nowrap;padding:2px 0;justify-self:center;color:var(--color-text)}
.bd-ph.hl{font-weight:700;color:var(--color-accent-800)}
.bd-colhl{height:3px;border-radius:2px}
.bd-colhl.hl{background:var(--color-accent)}
.bd-st{position:sticky;left:0;z-index:2;background:var(--color-bg);display:flex;align-items:center;gap:6px;border:0;padding:0;
  cursor:pointer;font:inherit;color:var(--color-text);text-align:left;min-width:0}
.bd-st b{font:600 16px var(--font-heading);width:26px;flex:none}
.bd-st span{font-size:11.5px;color:var(--color-neutral-700);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bd-st.sel b{color:var(--color-accent-700);text-decoration:underline}
.bd-c{width:auto;height:30px;padding:0;display:flex;flex-direction:column;align-items:center;justify-content:center;line-height:1;
  cursor:pointer;font:inherit;gap:1px}
.bd-c i{font-style:normal;font-size:10px}
.bd-c small{font-size:9.5px}
.bd-c.na{cursor:default}
.bd-c.sel{outline:2px solid var(--color-text);outline-offset:1px}
.bd-c.descoped{background:var(--color-surface);color:var(--color-neutral-600);border:1px dotted var(--color-neutral-500)}
.bd-v{display:flex;align-items:center;gap:8px;padding:0 8px 0 2px;min-width:0}
.bd-stk{position:sticky;left:130px;z-index:2;background:var(--color-bg);border-right:1px solid var(--color-divider)}
.bd-badge{border:1px solid var(--color-neutral-400);color:var(--color-neutral-700);padding:2px 8px;border-radius:3px;font-size:11.5px;
  font-weight:600;white-space:nowrap}
.bd-badge.Go{border-color:var(--color-accent-700);color:var(--color-accent-800);background:var(--color-accent-100)}
.bd-badge.Hold{border-color:var(--color-accent-400);color:var(--color-accent-800)}
.bd-badge.Hold.mm{border-color:var(--ox);color:var(--ox-deep)}
.bd-v span:last-child{font-size:11px;color:var(--color-neutral-700);line-height:1.2;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bd-counts{display:flex;gap:6px}
.bd-counts span{flex:1;display:flex;flex-direction:column;align-items:center;padding:5px 0;border-radius:2px;width:auto;height:auto}
.bd-counts b{font-size:15px}
.bd-counts small{font-size:10px}
.bd-ctl{margin-top:8px}
.bd-dot{display:inline-block;width:10px;height:10px;border-radius:50%;border:1px dashed var(--color-neutral-400);vertical-align:middle;margin-right:5px}
.bd-dot.r{background:var(--color-accent-700);border:1px solid var(--color-accent-700)}
.bd-dot.d{background:transparent;border:1.5px solid var(--color-accent-700)}
.bd-cg{display:grid;gap:2px;align-items:center;font-size:11.5px}
.bd-cg .h{font-size:9.5px;color:var(--color-neutral-700);writing-mode:vertical-rl;transform:rotate(180deg);justify-self:center;height:22px}
.bd-cg .lab{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;padding-right:6px;position:sticky;left:0;background:var(--color-bg)}
.bd-cg .grp{grid-column:1/-1;font:600 13px var(--font-heading);padding-top:6px;border-bottom:1px solid var(--color-divider)}
.bd-cg .dot{justify-self:center}
.bd-cg .dot .bd-dot{margin-right:0}
.bd-cg .n{font-size:10.5px;color:var(--color-neutral-700);text-align:right}
.bd-tbl td.st{white-space:nowrap}
"""

BOARD_JS = r"""
const BD={line:'GL',data:null,ctl:{},sel:null,state:null,hl:null,cell:null};
function bdLoad(){
  const line=BD.line;
  document.querySelectorAll('#bd-lines button').forEach(b=>b.setAttribute('aria-pressed',b.dataset.l===line));
  const a=fetch('/api/console/board?lob='+line).then(r=>r.json()).then(d=>{if(BD.line===line){BD.data=d;bdDraw();}});
  if(!BD.ctl[line])fetch('/api/console/controls?lob='+line).then(r=>r.json()).then(c=>{BD.ctl[line]=c;if(BD.line===line)bdCtl();});
  else bdCtl();
  return a;
}
function bdCellTxt(v){const st=v[0],n=v[1],aff=v[2];if(st==='na')return['·',''];if(st==='descoped')return['⊘',''];
  return[LG[st].glyph,st==='mismatch'||st==='stale'?aff+'/'+n:(n?String(n):'')];}
function bdDraw(){
  const d=BD.data,S=d.summary,cols=d.columns.flatMap(g=>g.paths);
  const pct=(a,b)=>b?Math.round(100*a/b)+'%':'—';
  const cats=S.categories.filter(c=>S.byCategory[c.key]).map(c=>'<span class="'+(c.key==='true_engine_defect'?'def':'')+'">'+esc(c.label)+'</span><b>'+S.byCategory[c.key]+'</b>').join('')+
    (S.byCategory.unclassified?'<span>Unclassified</span><b>'+S.byCategory.unclassified+'</b>':'');
  document.getElementById('bd-stats').innerHTML=
    '<div><span>Path coverage</span><b>'+pct(S.walked,S.applicable)+'</b><small>'+S.walked+' of '+S.applicable+' walked</small></div>'+
    '<div><span>RaaS-verified paths</span><b>'+pct(S.verified,S.applicable)+'</b><small>'+S.verified+' of '+S.applicable+'</small></div>'+
    '<div><span>Open mismatches</span><b>'+S.openMismatches+'</b>'+(cats?'<div class="bd-cats">'+cats+'</div>':'')+'</div>'+
    '<div class="aw" id="bd-aw" title="Plan results nobody has inspected yet (a layer beside ISO\'s agreement)"><span>Awaiting inspection</span><b>'+(S.awaitingInspection||0)+(S.awaitingInspection?' ▸':'')+'</b><small>plan results not yet reviewed</small></div>'+
    '<div><span>Verification days left</span><b>'+S.days+'</b><small>'+S.calls.toLocaleString()+' calls at 150/day</small></div>'+
    '<div><span>States</span><b>'+S.verdicts.Go+' <small>Go</small></b><small>'+S.verdicts.Hold+' Hold · '+S.verdicts['Not ready']+' Not ready</small></div>';
  const g=document.getElementById('bd-grid');
  g.style.gridTemplateColumns='130px 190px repeat('+cols.length+',26px)';   // the verdict beside the state, never scrolled away
  const hl=p=>BD.hl&&BD.hl.lob===d.line&&p.coverages.includes(BD.hl.coverage);
  let h='<span class="bd-st" style="cursor:default"></span><span class="bd-v bd-stk"></span>';
  d.columns.forEach(gr=>h+='<span class="bd-grp" style="grid-column:span '+gr.paths.length+'" title="'+esc(gr.coverage)+'">'+esc(gr.coverage)+'</span>');
  h+='<span class="bd-st" style="cursor:default;align-self:end"><span style="letter-spacing:.08em;text-transform:uppercase;font-size:10.5px">State</span></span>'+
    '<span class="bd-v bd-stk" style="align-self:stretch;align-items:flex-end;padding-bottom:4px"><span style="font-size:10.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--color-neutral-700)">Readiness</span></span>';
  cols.forEach(p=>h+='<span class="bd-ph'+(hl(p)?' hl':'')+'" title="'+esc(p.label)+'">'+esc(p.label)+'</span>');
  h+='<span class="bd-st" style="cursor:default"></span><span class="bd-v bd-stk"></span>'+cols.map(p=>'<span class="bd-colhl'+(hl(p)?' hl':'')+'"></span>').join('');
  d.rows.forEach(r=>{
    h+='<button class="bd-st'+(BD.state===r.state?' sel':'')+'" data-s="'+r.state+'" title="'+esc(BOOT.names[r.state]||r.state)+'"><b>'+r.state+'</b><span>'+esc(BOOT.names[r.state]||'')+'</span></button>';
    h+='<span class="bd-v bd-stk"><span class="bd-badge '+r.verdict.replace(' ','')+(r.counts.mismatch?' mm':'')+'">'+esc(r.verdict)+'</span><span title="'+esc(r.note)+'">'+esc(r.note)+'</span></span>';
    const aw=(d.awaiting||{})[r.state]||{};
    cols.forEach(p=>{const v=r.cells[p.id]||['untested',0,0],t=bdCellTxt(v),k=r.state+'|'+p.id;
      h+='<button class="bd-c chip '+v[0]+(aw[p.id]?' aw':'')+(BD.sel===k?' sel':'')+'" data-k="'+esc(k)+'" title="'+esc(r.state+' · '+p.label+' · '+(v[0]==='descoped'?'descoped':LG[v[0]].board)+(v[1]?' · '+v[1]+' scenario'+(v[1]>1?'s':''):''))+'"><i>'+esc(t[0])+'</i>'+(t[1]?'<small>'+t[1]+'</small>':'')+'</button>';});
  });
  g.innerHTML=h;
  const awb=document.getElementById('bd-aw');if(awb)awb.onclick=()=>{location.hash='#queue';};
  if(BD.sel)bdCell(BD.sel,false);else if(BD.state)bdState(BD.state);else bdOverview();
}
function bdOverview(){
  const S=BD.data.summary;
  document.getElementById('bd-side').innerHTML='<div class="cap2">Readiness · '+(BD.line==='GL'?'General Liability':'Commercial Property')+'</div>'+
    '<h2>'+S.verdicts.Go+' Go · '+S.verdicts.Hold+' Hold · '+S.verdicts['Not ready']+' Not ready</h2>'+
    '<div class="mx-msg">Go: every applicable path RaaS-verified. Hold: an open mismatch, a stale reference, or verification part-way. Not ready: nothing verified yet.</div>'+
    '<div class="mx-msg">Click a state for its counts, or a cell for the scenarios behind it.</div>';
}
function bdCounts(c){return '<div class="bd-counts">'+['verified','internal','mismatch','stale','untested'].map(k=>'<span class="chip '+k+'"><b>'+c[k]+'</b><small>'+esc(LG[k].board)+'</small></span>').join('')+'</div>';}
function bdState(st){
  const r=BD.data.rows.find(x=>x.state===st);if(!r)return bdOverview();
  document.getElementById('bd-side').innerHTML='<a href="#" class="mx-back" id="bd-back">← Overview</a><div class="cap2">Readiness · '+BD.line+'</div>'+
    '<div style="display:flex;gap:12px;align-items:center"><h2>'+esc(BOOT.names[st]||st)+'</h2><span class="bd-badge '+r.verdict.replace(' ','')+(r.counts.mismatch?' mm':'')+'">'+esc(r.verdict)+'</span></div>'+
    '<div>'+esc(r.note)+'</div>'+bdCounts(r.counts)+
    '<div class="cap2" style="margin-top:14px">Quick smoke</div><div class="mx-msg">One retail risk at standard selections'+
    (BD.line==='GL'?' (class 11127, $1M sales, premises and products, 1M/2M/2M)':' (class 0567, Special form, $1M building, $250K contents)')+', sent to ISO for '+esc(st)+'.</div>'+
    '<div class="td-tools"><button class="btn" id="bd-smoke">Run quick smoke for '+esc(st)+'…</button></div><div id="bd-sconf"></div>'+
    '<button class="btn" id="bd-tomx" style="margin-top:auto">See '+st+' on the Readiness Matrix</button>';
  document.getElementById('bd-smoke').onclick=()=>fetch('/api/console/presets').then(r=>r.json()).then(j=>{
    const p=j.presets.find(x=>x.id===(BD.line==='GL'?'smoke-gl':'smoke-cp'));
    bdPlan(BD.line,st,p.spec.configs,'Quick smoke · '+BD.line+' · '+st,document.getElementById('bd-sconf'));});
  document.getElementById('bd-back').onclick=ev=>{ev.preventDefault();BD.state=null;BD.sel=null;bdDraw();};
  document.getElementById('bd-tomx').onclick=()=>{location.hash='#matrix';};
}
function bdCell(k,fetchIt){
  const st=k.split('|')[0],pid=k.split('|')[1];
  if(fetchIt===false&&BD.cell&&BD.cell.key===k)return bdCellDraw(BD.cell);
  document.getElementById('bd-side').innerHTML='<div class="mx-msg">Loading the scenarios…</div>';
  fetch('/api/console/board/cell?lob='+BD.line+'&state='+st+'&path='+encodeURIComponent(pid)).then(r=>r.json())
    .then(c=>{if(c.error){document.getElementById('bd-side').innerHTML='<div class="mx-msg">'+esc(c.error)+'</div>';return;}
      c.key=k;BD.cell=c;if(BD.sel===k)bdCellDraw(c);});
}
function bdCellDraw(c){
  const s=c.status==='descoped'?{glyph:'⊘',board:'Descoped',meaning:'taken out of scope with a reason'}:LG[c.status];
  let h='<a href="#" class="mx-back" id="bd-back">← '+esc(BOOT.names[c.state]||c.state)+'</a><div class="cap2">Selected cell · '+esc(c.line+' · '+c.state)+'</div>'+
    '<div style="display:flex;gap:10px;align-items:center"><span class="chip '+c.status+'">'+esc(s.glyph)+'</span><h2 style="font-size:19px">'+esc(c.label)+'</h2></div>'+
    '<div class="mx-msg">'+esc(s.board+' — '+s.meaning)+'</div>';
  if(!c.applies)h+='<div class="mx-msg">Not filed in '+esc(c.state)+': '+esc(c.why||'the state files no such path')+' (D5).</div>';
  else if(!c.scenarios.length)h+='<div class="mx-msg">No scenario has walked this path in '+esc(c.state)+' yet.</div>';
  else h+='<div class="cap2">Scenarios · '+c.scenarios.length+'</div><table class="bd-tbl"><tr><td><b>Scenario</b></td><td class="st"><b>State</b></td><td><b>Ours / ISO</b></td></tr>'+
    c.scenarios.map(x=>'<tr><td>'+((x.source||'').startsWith('run ')?esc(x.scenario):'<a href="#trace?lob='+c.line+'&scenario='+encodeURIComponent(x.scenario)+'">'+esc(x.scenario)+'</a>')+'<div class="mx-msg">'+esc((x.source||'')+(x.at?' · '+x.at.slice(0,10):''))+'</div></td>'+
      '<td class="st">'+(x.status==='inert'?'<span class="mx-msg">inert</span>':'<span class="chip '+x.status+'">'+esc(LG[x.status].glyph)+'</span>')+'</td>'+
      '<td>'+esc(x.ours==null?'—':x.ours)+' / '+esc(x.iso==null?'—':x.iso)+(x.inspectable?'<div>'+ivHTML(x.scenario,x.plan,x.verdict)+'</div>':'')+(x.delta&&+x.delta!==0?'<div class="mx-msg">Δ '+esc((+x.delta>0?'+':'')+x.delta)+(x.category?' · '+esc(x.category.replace(/_/g,' ')):' · unclassified')+'</div>':'')+'</td></tr>').join('')+'</table>'+
    '<div class="mx-msg">A linked scenario opens in Trace Diff, step by step. QA-run rows (source "run …") hold ISO’s premium only, no answer to diff.</div>';
  if(c.applies&&c.status!=='descoped')h+='<div class="cap2" style="margin-top:14px">Run tests for this cell</div>'+
    '<div class="mx-msg">Find risks that walk this path in '+esc(c.state)+': each candidate is rated on our engine (free) and kept only if its trace walks the path. Then send the ones you choose to ISO.</div>'+
    '<div class="td-tools"><button class="btn" id="bd-find">Find scenarios (free)</button></div><div id="bd-found"></div>';
  document.getElementById('bd-side').innerHTML=h;
  document.getElementById('bd-back').onclick=ev=>{ev.preventDefault();BD.sel=null;BD.state=c.state;bdDraw();};
  const f=document.getElementById('bd-find');if(f)f.onclick=()=>bdFind(c);
}
function bdFind(c){
  const out=document.getElementById('bd-found'),btn=document.getElementById('bd-find');btn.disabled=true;
  out.innerHTML='<div class="mx-msg">Rating candidates on our engine… (up to 30 seconds)</div>';
  fetch('/api/console/board/find?lob='+c.line+'&state='+c.state+'&path='+encodeURIComponent(c.path||BD.sel.split('|')[1])).then(r=>r.json()).then(j=>{
    btn.disabled=false;if(BD.sel!==c.key)return;
    if(j.error){out.innerHTML='<div class="mx-msg">'+esc(j.error)+'</div>';return;}
    if(!j.found.length){out.innerHTML='<div class="mx-msg">None of '+j.tried+' candidates walked this path ('+j.seconds+' s). No single control in the catalog reaches it in '+esc(c.state)+'; the Scenario Workbench can set a stored request by hand.</div>';return;}
    BD.found=j.found;
    out.innerHTML='<table class="bd-tbl"><tr><td></td><td><b>Scenario</b></td><td><b>Ours</b></td><td><b>ISO</b></td></tr>'+j.found.map((x,i)=>
      '<tr><td><input type="checkbox" data-i="'+i+'"'+(x.stored&&x.stored.freshness==='fresh'?'':' checked')+'></td><td>'+esc(x.label)+
      (x.classification&&x.classification.label?'<div class="mx-msg">'+esc(x.classification.basis+': '+x.classification.label)+'</div>':'')+'</td><td>'+esc(x.premium)+'</td>'+
      '<td>'+(x.stored?(x.stored.iso?esc(x.stored.iso):esc(x.stored.outcome))+'<div class="mx-msg">'+esc(x.stored.freshness||'')+'</div>':'<span class="mx-msg">not asked</span>')+'</td></tr>').join('')+'</table>'+
      '<div class="mx-msg">'+j.found.length+' found in '+j.tried+' tries ('+j.seconds+' s). Ticked: no fresh answer from ISO yet.</div>'+
      '<div class="td-tools"><button class="btn" id="bd-send">Send ticked to ISO…</button></div><div id="bd-conf"></div>';
    document.getElementById('bd-send').onclick=()=>bdSend(c);
  }).catch(e=>{btn.disabled=false;out.innerHTML='<div class="mx-msg">'+esc(String(e))+'</div>';});
}
function bdPlan(line,state,configs,name,el,onDone){
  const spec={line:line,states:[state],dims:{},configs:configs,edges:false};
  el.innerHTML='<div class="mx-msg">Counting calls…</div>';
  fetch('/api/console/plan/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({spec:spec})}).then(r=>r.json()).then(p=>{
    if(p.error){el.innerHTML='<div class="mx-msg">'+esc(p.error)+'</div>';return;}
    el.innerHTML='<div class="mx-msg"><b>'+p.calls+' call'+(p.calls===1?'':'s')+'</b> to ISO from the active lane ('+p.activeLeftToday+' left today)'+(p.alreadyAnswered?'; '+p.alreadyAnswered+' already answered, reused':'')+'. It runs as a plan in the Queue.</div>'+
      '<div class="td-tools"><button class="btn" id="bd-go"'+(p.scenarios?'':' disabled')+'>Send now</button><button class="btn" id="bd-no">Cancel</button></div><div class="mx-msg" id="bd-msg"></div>';
    document.getElementById('bd-no').onclick=()=>el.innerHTML='';
    document.getElementById('bd-go').onclick=()=>{document.getElementById('bd-msg').textContent='Writing the plan…';
      fetch('/api/console/plan/commit',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({spec:spec,name:name,start:true})}).then(r=>r.json()).then(j=>{
        if(j.error){document.getElementById('bd-msg').textContent=j.error;return;}location.hash='#queue?plan='+encodeURIComponent(j.id);});};});
}
function bdSend(c){
  const cfgs=[...document.querySelectorAll('#bd-found input[data-i]:checked')].map(x=>BD.found[+x.dataset.i].config);
  const el=document.getElementById('bd-conf');if(!cfgs.length){el.innerHTML='<div class="mx-msg">Tick at least one.</div>';return;}
  bdPlan(c.line,c.state,cfgs,c.line+' '+c.state+' · '+c.label,el);
}
function bdCtl(){
  const c=BD.ctl[BD.line],el=document.getElementById('bd-ctl');if(!c)return;
  if(!c.available){el.innerHTML='<div class="mx-empty" style="height:60px">'+esc(c.why)+'</div>';return;}
  const n=c.states.length;let h='<div class="bd-cg" style="grid-template-columns:220px repeat('+n+',16px) 54px;min-width:'+(280+18*n)+'px"><span></span>'+
    c.states.map(s=>'<span class="h">'+s+'</span>').join('')+'<span class="n">States</span>';
  let grp=null;
  c.controls.forEach(r=>{if(r.group!==grp){grp=r.group;h+='<span class="grp">'+esc(grp||'Other')+'</span>';}
    const R=new Set(r.rated),D=new Set(r.declined);
    h+='<span class="lab" title="'+esc(r.label+(r.values.length?' · values run: '+r.values.join(', '):''))+'">'+esc(r.label)+'</span>'+
      c.states.map(s=>'<span class="dot" title="'+esc(r.label+' · '+s+': '+(R.has(s)?'rated':D.has(s)?'asked, not declarable':'never run'))+'"><b class="bd-dot'+(R.has(s)?' r':D.has(s)?' d':'')+'"></b></span>').join('')+
      '<span class="n">'+R.size+'</span>';});
  el.innerHTML=h+'</div><div class="mx-msg" style="margin-top:6px">'+c.exercised+' of '+c.controls.length+' controls have been rated somewhere. From the GL run store (the grid /tester showed).</div>';
}
function bdRoute(){
  const parts=(location.hash||'').slice(1).split('?');if(parts[0]!=='board')return;
  const p=new URLSearchParams(parts[1]||'');
  if(p.get('lob')){BD.line=p.get('lob')==='CP'?'CP':'GL';BD.hl=p.get('coverage')?{lob:BD.line,coverage:p.get('coverage')}:null;
    BD.state=p.get('state')||null;BD.sel=null;}
  bdLoad().then(()=>{if(BD.state){const b=document.querySelector('.bd-st[data-s="'+BD.state+'"]');if(b)b.scrollIntoView({block:'center'});}});
}
document.getElementById('bd-lines').addEventListener('click',ev=>{const b=ev.target.closest('button');if(!b||b.dataset.l===BD.line)return;
  BD.line=b.dataset.l;BD.sel=null;BD.state=null;BD.hl=null;bdLoad();});
document.getElementById('bd-grid').addEventListener('click',ev=>{
  const c=ev.target.closest('.bd-c');if(c&&!c.classList.contains('na')){BD.sel=c.dataset.k;BD.state=c.dataset.k.split('|')[0];
    document.querySelectorAll('.bd-c.sel').forEach(x=>x.classList.remove('sel'));c.classList.add('sel');bdCell(BD.sel);return;}
  const s=ev.target.closest('.bd-st[data-s]');if(s){BD.state=s.dataset.s;BD.sel=null;
    document.querySelectorAll('.bd-st.sel,.bd-c.sel').forEach(x=>x.classList.remove('sel'));s.classList.add('sel');bdState(BD.state);}});
addEventListener('hashchange',bdRoute);
document.addEventListener('iv:changed',()=>{if(!document.getElementById('s-board').hidden&&BD.data){BD.cell=null;bdLoad();}});
if((location.hash||'').startsWith('#board'))bdRoute();
setInterval(()=>{if(!document.getElementById('s-board').hidden&&BD.data)bdLoad().catch(()=>{});},60000);
"""


# ---- TC-21 / TC-22: Trace Diff and classification -------------------------------------------------------------------
# One stored scenario, ours vs ISO row by row on today's engine (`console.tracediff`). Matching records collapsed; the
# first divergent step marked, later differences tagged "flows from"; each row's rule file and package; seen before
# (D16) with its classification; a copy-brief button (D16); classify with a note (TC-22). Rating a stored request
# spends nothing.

TRACE_HTML = """<section class="screen" id="s-trace" hidden><div class="mx-wrap"><div class="mx-main">
  <div class="mx-head"><div><div class="eyebrow">Seeing why · ours vs ISO, step by step</div><h1>Trace Diff</h1></div>
    <p>A stored ISO answer re-rated on today's engine and lined up field by field. The first divergent step is the
    earliest number we computed that ISO disagrees with; what follows from it is tagged. Re-rating spends no call.</p></div>
  <div class="td-pick"><div class="bd-lines" id="td-lines" role="group" aria-label="Line"><button data-l="CP">Commercial Property</button><button data-l="GL">General Liability</button></div>
    <input id="td-state" placeholder="State" maxlength="2" aria-label="State filter">
    <label class="td-chk"><input type="checkbox" id="td-differ"> differing only</label>
    <select id="td-sel" aria-label="Scenario"></select><span class="mx-msg" id="td-count"></span></div>
  <div id="td-body"><div class="mx-empty" style="height:120px">Pick a scenario, or open one from a Coverage Board cell.</div></div>
</div><aside class="mx-side" id="td-side" aria-live="polite"></aside></div></section>"""

BUILT["trace"] = TRACE_HTML

TRACE_CSS = """
.td-pick{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.td-pick .bd-lines{margin-left:0}
.td-pick input#td-state{width:64px;font:inherit;padding:6px 8px;border:1px solid var(--color-divider);border-radius:4px;background:#fff;text-transform:uppercase}
.td-pick select{font:inherit;padding:6px 8px;border:1px solid var(--color-divider);border-radius:4px;background:#fff;max-width:420px}
.td-chk{font-size:12.5px;display:flex;gap:5px;align-items:center}
.td-head{display:flex;gap:18px;align-items:baseline;flex-wrap:wrap}
.td-head h2{margin:0;font:600 22px var(--font-heading)}
.td-root{border:1.5px solid var(--ox);background:var(--ox-tint);border-radius:4px;padding:10px 12px;margin:6px 0}
.td-root.ok{border-color:var(--color-accent-700);background:var(--color-accent-100)}
.td-root b{font:600 15px var(--font-heading)}
.td-root code,.td-row code{font-size:11px;word-break:break-all}
.td-tools{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.td-recs{display:flex;flex-direction:column;gap:4px}
.td-rec{border:1px solid var(--color-divider);border-radius:4px;background:var(--color-bg)}
.td-rec>button{width:100%;display:flex;gap:10px;align-items:center;padding:6px 10px;border:0;background:transparent;cursor:pointer;font:inherit;
  text-align:left;color:var(--color-text)}
.td-rec>button span:first-child{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:12px}
.td-rec.bad{border-color:var(--ox)}
.td-rows{width:100%;border-collapse:collapse;font-size:12px;table-layout:fixed}
.td-rows td:nth-child(1){width:38%}.td-rows td:nth-child(2),.td-rows td:nth-child(3){width:20%}
.td-rows td{overflow-wrap:anywhere}
#td-body{min-width:0;overflow-x:hidden}
.td-rows td{padding:4px 8px;border-top:1px solid var(--color-divider);vertical-align:top}
.td-rows td.v{text-align:right;font-variant-numeric:tabular-nums}
.td-rows tr.first td{background:var(--ox-tint)}
.td-rows tr.flows td{background:color-mix(in srgb,var(--ox-tint) 50%,transparent)}
.td-tag{font-size:10.5px;padding:1px 6px;border-radius:3px;border:1px solid var(--color-neutral-400);white-space:nowrap}
.td-tag.first{border-color:var(--ox);color:var(--ox-deep);font-weight:600}
.td-tag.flows{color:var(--ox-deep)}
.td-src{font-size:10.5px;color:var(--color-neutral-700)}
.td-cls select,.td-cls input,.td-cls textarea{font:inherit;padding:6px 8px;border:1px solid var(--color-divider);border-radius:4px;background:#fff;width:100%}
.td-cls textarea{min-height:60px;resize:vertical}
"""

TRACE_JS = r"""
const TD={line:'CP',list:[],cur:null,open:{},all:false};
function tdList(){
  const st=document.getElementById('td-state').value.trim().toUpperCase(),dif=document.getElementById('td-differ').checked;
  document.querySelectorAll('#td-lines button').forEach(b=>b.setAttribute('aria-pressed',b.dataset.l===TD.line));
  return fetch('/api/console/trace/scenarios?lob='+TD.line+(st?'&state='+st:'')+(dif?'&differ=1':'')).then(r=>r.json()).then(j=>{
    TD.list=j.scenarios;const sel=document.getElementById('td-sel');
    sel.innerHTML='<option value="">— '+j.total+' stored answer'+(j.total===1?'':'s')+' —</option>'+j.scenarios.map(s=>'<option value="'+esc(s.scenario)+'"'+(TD.cur&&TD.cur.scenario===s.scenario?' selected':'')+'>'+
      esc((s.agree===false?'× ':s.agree?'✓ ':'· ')+s.scenario+' · '+s.date+' · '+s.source)+'</option>').join('');
    document.getElementById('td-count').textContent=j.total>j.scenarios.length?'first '+j.scenarios.length+' shown':'';});
}
function tdOpen(id){
  if(!id)return;document.getElementById('td-body').innerHTML='<div class="mx-msg">Re-rating on today’s engine and lining up the fields…</div>';
  return fetch('/api/console/trace?scenario='+encodeURIComponent(id)).then(r=>r.json()).then(d=>{if(d.error){document.getElementById('td-body').innerHTML='<div class="mx-empty" style="height:80px">'+esc(d.error)+'</div>';return;}
    TD.cur=d;TD.open={};TD.all=false;const sel=document.getElementById('td-sel');
    if(d.line!==TD.line){TD.line=d.line;tdList();}else if([...sel.options].some(o=>o.value===d.scenario))sel.value=d.scenario;tdDraw();});
}
function tdVal(v){return v===null||v===undefined?'<span class="mx-msg">absent</span>':esc(String(v));}
function tdDraw(){tdDraw0();ivFill(document.getElementById('td-body'));}
function tdDraw0(){
  const d=TD.cur,b=document.getElementById('td-body');
  const slot='<span class="insp-slot" data-sid="'+esc(d.scenario)+'"></span>';
  const head='<div class="td-head"><h2>'+esc(d.scenario)+'</h2><span>'+esc(d.line+' · '+(BOOT.names[d.state]||d.state)+' · effective '+d.date)+'</span>'+slot+'</div>';
  if(d.isoRefused){
    let h=head+'<div class="td-root"><b>ISO refused this request</b><div class="mx-msg">'+esc(d.isoRefused)+'</div></div>';
    if(d.bothRefuse)h+='<div class="td-root ok"><b>Ours refuses too'+(d.sameTable?', at the same table':', for a different reason')+'.</b><div class="mx-msg">'+esc(d.refused)+'</div></div>';
    else{h+='<div class="mx-stats" style="grid-template-columns:repeat(2,minmax(0,1fr))"><div><span>Ours</span><b>'+tdVal(d.oursTotal)+'</b><small>we rate it</small></div><div><span>ISO</span><b>refused</b></div></div>';
      d.roots.forEach(r=>h+='<div class="td-root"><b>'+(r.role==='first'?'First divergent step':'Separate divergence')+'</b> · ours read <code>'+esc(r.field)+'</code> = '+esc(String(r.ours))+
        '<div class="td-src">from '+esc(r.package||'?')+' · keys '+esc(r.tables[0])+(r.downstream?' · read '+r.downstream+' more time'+(r.downstream===1?'':'s')+' at other keys':'')+' · ISO found no rows in this table and refused</div></div>');
      if(!d.roots.length)h+='<div class="td-root"><b>Ours rates where ISO refused</b>, and no table ISO names was read by us: compare the messages.</div>';}
    h+='<div class="td-tools"><button class="btn" id="td-brief">Copy brief</button><span class="mx-msg" id="td-copied"></span></div>';
    b.innerHTML=h;
    document.getElementById('td-brief').onclick=()=>{const m=document.getElementById('td-copied');(navigator.clipboard?navigator.clipboard.writeText(d.brief):Promise.reject()).then(()=>m.textContent='Copied.').catch(()=>{m.textContent='Select and copy:';const t=document.createElement('textarea');t.value=d.brief;t.style.width='100%';t.rows=8;m.after(t);t.select();});};
    tdSide();return;}
  if(d.refused){b.innerHTML=head+'<div class="td-root"><b>Our engine refuses this request</b><div>'+esc(d.refused)+'</div><div class="mx-msg">ISO rated it; a refusal where ISO rates is D15’s "our refusal vs ISO’s narrowing" when it is not by decision.</div></div>';tdSide();return;}
  const c=d.counts;
  let h='<div class="td-head"><h2>'+esc(d.scenario)+'</h2><span>'+esc(d.line+' · '+(BOOT.names[d.state]||d.state)+' · effective '+d.date)+'</span><span class="mx-msg">ISO package '+esc(d.isoPackage||'?')+(d.freshness==='stale'?' · <b>stale</b>: '+esc(d.staleReason):'')+'</span>'+slot+'</div>';
  h+='<div class="mx-stats" style="grid-template-columns:repeat(5,minmax(0,1fr))"><div><span>Ours</span><b>'+tdVal(d.oursTotal)+'</b></div><div><span>ISO</span><b>'+tdVal(d.isoTotal)+'</b></div>'+
    '<div><span>Fields agree</span><b>'+c.agree+'</b><small>of '+c.compared+' compared</small></div><div><span>Steps differ</span><b>'+c.steps+'</b><small>'+c.roots+' divergence'+(c.roots===1?'':'s')+'</small></div>'+
    '<div><span>Other</span><b>'+c.other+'</b><small>codes, dates, text · '+c.isoOnly+' ISO-only</small></div></div>';
  if(!d.roots.length)h+='<div class="td-root ok"><b>No divergent step.</b> Every number we computed that ISO publishes agrees'+(c.other?'; '+c.other+' codes / dates / text differ (below).':'.')+'</div>';
  d.roots.forEach(r=>h+='<div class="td-root"><b>'+(r.role==='first'?'First divergent step':'Separate divergence')+'</b> · <code>'+esc(r.path)+'</code><div>Ours '+tdVal(r.ours)+' · ISO '+tdVal(r.iso)+
    (r.downstream?' · '+r.downstream+' later difference'+(r.downstream===1?'':'s')+' flow from it':'')+'</div><div class="td-src">Written by '+esc(r.rule_file||'?')+' · '+esc(r.package||'?')+(r.tables.length?' · tables read: '+esc(r.tables.join(', ')):'')+'</div></div>');
  h+='<div class="td-tools"><button class="btn" id="td-all">'+(TD.all?'Collapse matching records':'Expand all records')+'</button><button class="btn" id="td-brief">Copy brief</button><span class="mx-msg" id="td-copied"></span></div>';
  const byRec={};d.rows.forEach(r=>(byRec[r.record]=byRec[r.record]||[]).push(r));
  const isOpen=R=>TD.all||(TD.open[R.record]!==undefined?TD.open[R.record]:!R.collapsed);
  h+='<div class="td-recs">'+d.records.map(R=>{const open=isOpen(R);
    let s='<div class="td-rec'+(R.differ?' bad':'')+'"><button data-rec="'+esc(R.record)+'"><span title="'+esc(R.record)+'">'+(open?'▾ ':'▸ ')+esc(R.record)+'</span><span class="mx-msg">'+
      (R.differ?R.differ+' differ · ':'')+R.compared+' compared'+(R.isoOnly?' · '+R.isoOnly+' ISO-only':'')+'</span></button>';
    if(open)s+='<table class="td-rows">'+byRec[R.record].map(r=>{const st=r.match===true?'verified':r.match===false?'mismatch':'untested';
      return '<tr class="'+(r.role||'')+'"><td>'+esc(r.field)+(r.rule_file?'<div class="td-src">'+esc(r.rule_file)+'</div>':'')+'</td><td class="v">'+tdVal(r.ours)+'</td><td class="v">'+tdVal(r.iso)+'</td>'+
        '<td><span class="chip '+st+'" style="width:18px;height:15px;font-size:9.5px">'+(r.match===true?'✓':r.match===false?'×':'·')+'</span> '+
        (r.role==='first'?'<span class="td-tag first">first divergence</span>':r.role==='divergence'?'<span class="td-tag first">divergence</span>':r.role==='flows'?'<span class="td-tag flows">flows from '+esc(r.flowsFrom.split('/').slice(-2).join('/'))+'</span>':r.role==='other'?'<span class="td-tag">'+esc(r.kind)+'</span>':(!r.in_iso?'<span class="td-tag">ours only</span>':!r.in_ours?'<span class="td-tag">ISO only</span>':''))+'</td></tr>';}).join('')+'</table>';
    return s+'</div>';}).join('')+'</div>';
  b.innerHTML=h;
  b.querySelectorAll('.td-rec>button').forEach(x=>x.onclick=()=>{const R=d.records.find(r=>r.record===x.dataset.rec);TD.open[R.record]=!isOpen(R);tdDraw();});
  document.getElementById('td-all').onclick=()=>{TD.all=!TD.all;tdDraw();};
  document.getElementById('td-brief').onclick=()=>{const m=document.getElementById('td-copied');
    (navigator.clipboard?navigator.clipboard.writeText(d.brief):Promise.reject()).then(()=>m.textContent='Copied.').catch(()=>{m.textContent='Select and copy:';
      const t=document.createElement('textarea');t.value=d.brief;t.style.width='100%';t.rows=8;m.after(t);t.select();});};
  tdSide();
}
function tdSide(){
  const d=TD.cur,s=document.getElementById('td-side');
  let h='<div class="cap2">Classify this scenario</div>';
  const cl=d.classification;
  h+=cl?'<div class="mx-need"><span class="chip mismatch">×</span><div><b>'+esc(cl.category.replace(/_/g,' '))+'</b><div class="mx-msg">'+esc((cl.by||'')+' · '+(cl.at||'').slice(0,16)+(cl.note?' · '+cl.note:''))+'</div></div></div>':
    '<div class="mx-msg">'+(d.roots.length?'Unclassified: an open mismatch until classified (TC-11).':'Nothing to classify: no divergent step.')+'</div>';
  h+='<div class="td-cls" style="display:flex;flex-direction:column;gap:8px"><select id="td-cat"><option value="">Category…</option>'+BOOT.categories.map(c=>'<option value="'+c.key+'">'+esc(c.label)+'</option>').join('')+'</select>'+
    '<textarea id="td-note" placeholder="Note (what you found, the open item)"></textarea><input id="td-by" placeholder="Your name"><button class="btn" id="td-save">Save classification</button><div class="mx-msg" id="td-msg"></div></div>'+
    '<div class="mx-msg">Rounding (±$1) and interpolation (±0.5%) can clear a cell; the others never do until fixed and re-verified. The matrix and board follow on their next read.</div>';
  if((d.seenBefore||[]).length)h+='<div class="cap2">Seen before</div><table>'+d.seenBefore.map(x=>'<tr><td>'+esc(x.scenario)+'<div class="mx-msg">'+esc(x.field)+'</div></td><td>'+(x.classification?esc(x.classification.category.replace(/_/g,' ')):'<span class="mx-msg">unclassified</span>')+'</td></tr>').join('')+'</table>';
  h+='<div class="cap2">Files</div><div class="mx-msg">'+d.files.map(esc).join('<br>')+'</div>';
  h+='<button class="btn" id="td-promote" style="margin-top:auto">Promote to Regression Library</button><div class="mx-msg" id="td-pmsg"></div>';
  s.innerHTML=h;
  document.getElementById('td-save').onclick=()=>{const cat=document.getElementById('td-cat').value,m=document.getElementById('td-msg');if(!cat){m.textContent='Pick a category.';return;}
    fetch('/api/console/classify',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({scenario:d.scenario,category:cat,
      note:document.getElementById('td-note').value,by:document.getElementById('td-by').value,ours:d.oursTotal,iso:d.isoTotal})}).then(r=>r.json()).then(j=>{
      if(j.error){m.textContent=j.error;return;}d.classification=j;m.textContent='Saved.'+(j.withinTolerance===true?' Within its tolerance: it no longer blocks Passed.':j.withinTolerance===false?' Outside any tolerance: the cell stays a mismatch until fixed.':'');tdSide();});};
  const pb=document.getElementById('td-promote');if(pb)pb.onclick=()=>tdPromote(d.scenario,d.hash,d.line,d.state,'trace');
}
function tdPromote(sid,hash,line,state,origin){
  const m=document.getElementById('td-pmsg');
  fetch('/api/console/promote',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({scenario:sid,hash:hash,line:line,state:state,origin:origin})})
    .then(r=>r.json()).then(j=>{if(m)m.textContent=j.error?j.error:(j.already?'Already in the library.':'Promoted: the Regression Library (TC-33) re-runs it on every build.');});
}
function tdRoute(){const p=(location.hash||'').slice(1).split('?');if(p[0]!=='trace')return;const q=new URLSearchParams(p[1]||'');
  if(q.get('lob'))TD.line=q.get('lob')==='GL'?'GL':'CP';
  tdList().then(()=>{if(q.get('scenario'))tdOpen(q.get('scenario'));});}
document.getElementById('td-lines').addEventListener('click',ev=>{const b=ev.target.closest('button');if(!b||b.dataset.l===TD.line)return;TD.line=b.dataset.l;tdList();});
document.getElementById('td-state').addEventListener('change',tdList);
document.getElementById('td-differ').addEventListener('change',tdList);
document.getElementById('td-sel').addEventListener('change',ev=>tdOpen(ev.target.value));
addEventListener('hashchange',tdRoute);
if((location.hash||'').startsWith('#trace'))tdRoute();else tdList();
"""


# ---- TC-23 / TC-24: the Scenario Workbench ---------------------------------------------------------------------------
# One scenario: GL from ISO's declared domains (the controls /tester offered), CP from the state's sample or a stored
# request edited as itself. Rate internally (free; GL with /'s mode and rounding, D22); Send to RaaS (one call, after
# the store is asked for an exact stored answer, and a reason when the lane is full); check where it applies and run in
# every state (D19, free; committing it as a plan is RC-4's); response curves (D18); promote to the library (TC-24).

WB_HTML = """<section class="screen" id="s-workbench" hidden><div class="mx-wrap"><div class="mx-main">
  <div class="mx-head"><div><div class="eyebrow">One scenario · free, or one call</div><h1>Scenario Workbench</h1></div>
    <p>Build a risk from ISO's own domains, rate it on our engine for free, and send it to ISO only when no stored answer
    already covers it. Nothing here spends a call until you confirm one.</p>
    <div class="bd-lines" id="wb-lines" role="group" aria-label="Line"><button data-l="GL">General Liability</button><button data-l="CP">Commercial Property</button></div></div>
  <div class="wb-top"><label>State <select id="wb-state"></select></label>
    <label id="wb-model">Mode <select id="wb-mode"></select></label><label id="wb-roundl">Rounding <select id="wb-round"></select></label></div>
  <div id="wb-inputs"></div>
  <div class="td-tools"><button class="btn" id="wb-rate">Rate internally · free</button><button class="btn" id="wb-send">Send to RaaS · 1 call…</button>
    <button class="btn" id="wb-where">Check where it applies · free</button><button class="btn" id="wb-every">Run in every state…</button></div>
  <div id="wb-confirm"></div>
  <div id="wb-out"></div>
  <div class="mx-trend"><div class="mx-trend-hd"><span>Response curve · premium by value, from the runs that varied one control</span>
    <span class="mx-key"><span><i style="background:#9a6214"></i>ours</span><span><b class="bd-dot r" style="background:#2f72a8;border-color:#2f72a8"></b>ISO</span></span></div>
    <div class="td-tools"><select id="wb-curve"></select><span class="mx-msg" id="wb-curvemsg"></span></div><div id="wb-chart" style="position:relative;height:180px"></div></div>
</div><aside class="mx-side" id="wb-side" aria-live="polite"><div class="mx-msg">Rate a scenario to see what it walked, and whether ISO already answered it.</div></aside></div></section>"""

BUILT["workbench"] = WB_HTML

WB_CSS = """
.wb-top{display:flex;gap:16px;flex-wrap:wrap;align-items:center;font-size:12.5px}
.wb-top select,.wb-in select,.wb-in input,#wb-req,.wb-conf input{font:inherit;padding:5px 7px;border:1px solid var(--color-divider);border-radius:4px;background:#fff;max-width:100%}
.wb-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:8px 14px}
.wb-in{display:flex;flex-direction:column;gap:3px;font-size:12px}
.wb-in select,.wb-in input{width:100%}
.wb-grp{grid-column:1/-1;font:600 14px var(--font-heading);border-bottom:1px solid var(--color-divider);margin-top:6px}
#wb-req{width:100%;min-height:220px;font-family:ui-monospace,Menlo,monospace;font-size:11.5px}
.wb-conf{border:1.5px solid var(--color-accent);background:var(--color-accent-100);border-radius:4px;padding:12px;display:flex;flex-direction:column;gap:8px}
.wb-conf.full{border-color:var(--ox);background:var(--ox-tint)}
.wb-res{border:1px solid var(--color-divider);border-radius:4px;padding:12px;background:var(--color-bg)}
.wb-res b.big{font:400 30px var(--font-heading)}
.wb-tbl{width:100%;border-collapse:collapse;font-size:12px}
.wb-tbl td{padding:3px 6px;border-top:1px solid var(--color-divider)}
.wb-tbl td.v{text-align:right;font-variant-numeric:tabular-nums}
"""

WB_JS = r"""
const WB={line:'GL',spec:{},opts:null,config:{},last:null};
function wbJSON(url,body){return fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}).then(r=>r.json());}
function wbLoad(){
  document.querySelectorAll('#wb-lines button').forEach(b=>b.setAttribute('aria-pressed',b.dataset.l===WB.line));
  const go=s=>{WB.spec[WB.line]=s;const sel=document.getElementById('wb-state'),cur=sel.value;
    sel.innerHTML=s.states.map(x=>'<option'+(x===cur?' selected':'')+'>'+x+'</option>').join('');if(!cur&&s.states.includes('OH'))sel.value='OH';
    document.getElementById('wb-mode').innerHTML=s.modes.map(m=>'<option>'+m+'</option>').join('');
    document.getElementById('wb-round').innerHTML=s.roundings.map(m=>'<option>'+m+'</option>').join('');
    document.getElementById('wb-model').hidden=document.getElementById('wb-roundl').hidden=WB.line!=='GL';
    document.getElementById('wb-where').hidden=document.getElementById('wb-every').hidden=WB.line!=='GL';
    document.getElementById('wb-curve').innerHTML=WB.line==='GL'?'<option value="">Control…</option>'+s.controls.map(c=>'<option value="'+c.id+'">'+esc(c.label)+'</option>').join(''):'<option value="">CP curves arrive with its control catalog (TC-26)</option>';
    wbInputs();};
  return WB.spec[WB.line]?Promise.resolve(go(WB.spec[WB.line])):fetch('/api/console/workbench/spec?lob='+WB.line).then(r=>r.json()).then(go);
}
function wbState(){return document.getElementById('wb-state').value;}
function wbInputs(){
  const el=document.getElementById('wb-inputs');
  if(WB.line==='CP'){el.innerHTML='<div class="mx-msg">The CP request itself, starting from '+esc(wbState())+'’s sample risk. Edit any field; CP’s dimension catalog (TC-26) brings dropdowns.</div><textarea id="wb-req" spellcheck="false"></textarea>';
    fetch('/api/console/workbench/request?lob=CP&state='+wbState()).then(r=>r.json()).then(j=>document.getElementById('wb-req').value=JSON.stringify(j,null,1));return;}
  wbJSON('/api/console/workbench/options',{state:wbState(),config:WB.config}).then(o=>{WB.opts=o;
    let h='<div class="wb-grid">',grp=null;
    WB.spec.GL.controls.forEach(c=>{const oc=o.controls[c.id]||{};if(c.group!==grp){grp=c.group;h+='<div class="wb-grp">'+esc(grp)+'</div>';}
      const v=WB.config[c.id]??'';
      h+='<label class="wb-in" title="'+esc(c.note||'')+'">'+esc(c.label)+(oc.values?'<select data-c="'+c.id+'"><option value="">(base)</option>'+oc.values.map(x=>'<option'+(String(x)===String(v)?' selected':'')+'>'+esc(String(x))+'</option>').join('')+'</select>':
        '<input data-c="'+c.id+'" value="'+esc(String(v))+'" placeholder="(base)">')+'</label>';});
    el.innerHTML=h+'</div>';
    el.querySelectorAll('[data-c]').forEach(x=>x.onchange=()=>{const k=x.dataset.c;if(x.value==='')delete WB.config[k];else WB.config[k]=x.value;wbInputs();});});
}
function wbBody(extra){const b={line:WB.line,state:wbState(),mode:document.getElementById('wb-mode').value,rounding:document.getElementById('wb-round').value,...(extra||{})};
  if(WB.line==='GL')b.config=WB.config;else{try{b.request=JSON.parse(document.getElementById('wb-req').value);}catch(e){throw new Error('The CP request is not valid JSON: '+e.message);}}return b;}
function wbStoredBox(s,ours){if(!s)return '<div class="mx-msg">No stored ISO answer for this exact request.</div>';
  const agree=s.iso&&ours&&(+s.iso===+ours);
  return '<div class="mx-need"><span class="chip '+(s.outcome!=='rated'?'untested':agree?'verified':'mismatch')+'">'+(s.outcome!=='rated'?'·':agree?'✓':'×')+'</span><div><b>ISO already answered this exact request</b><div class="mx-msg">'+
    esc(s.outcome==='rated'?'ISO '+s.iso+(ours?' · ours '+ours+(agree?' · agree':' · differ'):''):'ISO refused: '+s.message)+' · stored '+esc((s.stored_at||'').slice(0,10))+(s.freshness==='stale'?' · stale':'')+'</div>'+
    (s.outcome==='rated'?'<a href="#trace?lob='+WB.line+'&scenario='+encodeURIComponent(s.scenario)+'">Open in Trace Diff</a>':'')+'</div></div>';}
function wbRate(){
  let body;try{body=wbBody();}catch(e){document.getElementById('wb-out').innerHTML='<div class="td-root">'+esc(e.message)+'</div>';return;}
  document.getElementById('wb-out').innerHTML='<div class="mx-msg">Rating on our engine…</div>';
  wbJSON('/api/console/workbench/rate',body).then(r=>{WB.last={...r,body};
    const o=document.getElementById('wb-out');
    if(r.error){o.innerHTML='<div class="td-root">'+esc(r.error)+'</div>';return;}
    o.innerHTML='<div class="wb-res">'+(r.outcome==='rated'?'<span class="cap2">Our premium</span><div><b class="big">'+esc(r.premium)+'</b> <span class="mx-msg">'+esc((r.packages||[]).join(' over '))+(r.mode?' · '+r.mode+' · '+r.rounding:'')+'</span></div>'+
      (r.classification?'<div>Class '+esc(r.classification.code+' '+r.classification.description)+' · <b>'+esc(r.classification.basis)+'</b>: '+esc(r.classification.label)+'</div>':''):
      '<b>Our engine '+(r.outcome==='stopped'?'stopped':'refused')+'</b><div class="mx-msg">'+esc(r.detail||'')+'</div>')+wbStoredBox(r.stored,r.premium)+'</div>';
    wbSide(r);});
}
function wbSide(r){
  const labels=(MX.data&&MX.data.pathLabels&&MX.data.pathLabels[r.line])||{};
  let h='<div class="cap2">Paths this scenario walked · '+(r.paths||[]).length+'</div>'+((r.paths||[]).length?'<table>'+r.paths.map(p=>'<tr><td>'+esc(labels[p]||p)+'</td></tr>').join('')+'</table>':'<div class="mx-msg">None.</div>');
  h+='<div class="cap2">Request</div><div class="mx-msg">hash '+esc(r.hash)+'</div>';
  h+='<button class="btn" id="wb-promote" style="margin-top:auto">Promote to Regression Library</button><div class="mx-msg" id="wb-pmsg">'+(r.stored&&r.stored.outcome==='rated'?'Kept with ISO’s stored answer as its reference.':'No ISO answer yet: kept with our premium as its reference (regression, not verification).')+'</div>';
  document.getElementById('wb-side').innerHTML=h;
  document.getElementById('wb-promote').onclick=()=>{const s=r.stored&&r.stored.outcome==='rated'?r.stored:null;
    wbJSON('/api/console/promote',{scenario:s?s.scenario:(r.line+'-'+r.body.state+'-wb-'+r.hash.slice(0,10)),line:r.line,state:r.body.state,origin:'workbench',
      hash:s?s.hash:'',request:s?null:r.request,ours:r.premium}).then(j=>document.getElementById('wb-pmsg').textContent=j.error?j.error:j.already?'Already in the library.':'Promoted.');};
}
function wbSendDialog(){
  let body;try{body=wbBody();}catch(e){document.getElementById('wb-confirm').innerHTML='<div class="td-root">'+esc(e.message)+'</div>';return;}
  fetch('/api/console/cap').then(r=>r.json()).then(c=>{
    const ad=c.lanes.find(l=>l.key==='adhoc'),full=ad.used>=ad.cap||c.used>=c.cap;
    wbJSON('/api/console/workbench/rate',body).then(r=>{
      const el=document.getElementById('wb-confirm');
      let h='<div class="wb-conf'+(full?' full':'')+'"><b>Send this scenario to ISO?</b><div>'+(r.stored?'<b>A stored answer covers this exact request.</b> Reusing it costs nothing.':'No stored answer covers it: this spends <b>1 call</b> from the ad hoc lane.')+'</div>'+
        '<div class="mx-msg">Ad hoc lane: '+ad.used+' of '+ad.cap+' used today · '+c.left+' of '+c.cap+' left in all'+(full?' · <b>full</b>: a call needs a reason, logged with it.':'')+'</div>';
      if(r.stored)h+='<div class="td-tools"><button class="btn" id="wb-reuse">Use the stored answer · free</button>'+(full?'<input id="wb-reason" placeholder="Reason, to spend past the cap" style="flex:1">':'')+'<button class="btn" id="wb-spend">Spend a call anyway</button><button class="btn" id="wb-cancel">Cancel</button></div>';
      else h+='<div class="td-tools">'+(full?'<input id="wb-reason" placeholder="Reason for going past the cap" style="flex:1">':'')+'<button class="btn" id="wb-spend">Send · 1 call</button><button class="btn" id="wb-cancel">Cancel</button></div>';
      el.innerHTML=h+'<div class="mx-msg" id="wb-sendmsg"></div></div>';
      const done=j=>{const m=document.getElementById('wb-sendmsg');if(j.error){m.textContent=j.error;return;}el.innerHTML='';
        document.getElementById('wb-out').insertAdjacentHTML('afterbegin','<div class="mx-msg">'+(j.reused?'Used the stored answer; no call spent.':'Sent: 1 call, logged in the ledger; ISO’s answer is in the store.')+'</div>');
        fetch('/api/console/cap').then(r=>r.json()).then(drawCap);wbRate();};
      const reuse=document.getElementById('wb-reuse');if(reuse)reuse.onclick=()=>wbJSON('/api/console/workbench/send',{...body,reuse:true}).then(done);
      document.getElementById('wb-spend').onclick=()=>{const rs=document.getElementById('wb-reason');if(full&&rs&&!rs.value.trim()){document.getElementById('wb-sendmsg').textContent='A reason is needed past the cap.';return;}
        wbJSON('/api/console/workbench/send',{...body,reuse:false,override:rs?rs.value.trim():''}).then(done);};
      document.getElementById('wb-cancel').onclick=()=>{el.innerHTML='';};
    });});
}
function wbWhere(){
  document.getElementById('wb-out').innerHTML='<div class="mx-msg">Checking every state against ISO’s declared domains…</div>';
  wbJSON('/api/console/workbench/where',{config:WB.config}).then(j=>{const na=Object.entries(j.not_applicable||{});
    document.getElementById('wb-out').innerHTML='<div class="wb-res"><span class="cap2">'+esc(j.describes||'the base risk')+'</span><div><b class="big">'+j.applicable.length+'</b> states it applies in · '+na.length+' it does not</div>'+
      (na.length?'<table class="wb-tbl">'+na.slice(0,60).map(([s,w])=>'<tr><td>'+s+'</td><td>'+esc(w)+'</td></tr>').join('')+'</table>':'')+'</div>';});
}
function wbEvery(){
  document.getElementById('wb-out').innerHTML='<div class="mx-msg">Rating this config in every state where it applies, on our engine (free)…</div>';
  wbJSON('/api/console/workbench/every',{config:WB.config,mode:document.getElementById('wb-mode').value,rounding:document.getElementById('wb-round').value}).then(j=>{
    if(j.error){document.getElementById('wb-out').innerHTML='<div class="td-root">'+esc(j.error)+'</div>';return;}
    document.getElementById('wb-out').innerHTML='<div class="wb-res"><span class="cap2">'+esc(j.describes||'the base risk')+' · every state</span><div><b class="big">'+j.applicable+'</b> states rated free · <b>'+j.callsToSend+'</b> would need a call (no stored answer) · '+j.storedAgree+' already verified against a stored answer</div>'+
      '<div class="td-tools"><button class="btn" id="wb-toplan">Build a plan from this…</button><span class="mx-msg">Sending these is a one-config test plan; nothing is spent here.</span></div>'+
      '<table class="wb-tbl">'+j.rows.map(x=>'<tr><td>'+x.state+'</td><td class="v">'+esc(x.premium||'')+'</td><td>'+esc(x.outcome)+'</td><td>'+(x.stored?'ISO '+esc(x.stored.iso||x.stored.outcome):x.needsCall?'<span class="mx-msg">needs a call</span>':'')+'</td></tr>').join('')+'</table></div>';
    const tp=document.getElementById('wb-toplan');if(tp)tp.onclick=()=>{const sts=j.rows.filter(x=>x.outcome!=='not applicable').map(x=>x.state);
      location.hash='#plan?lob=GL&states='+encodeURIComponent(sts.join(','))+'&config='+encodeURIComponent(JSON.stringify(WB.config));};});
}
function wbCurve(){
  const cid=document.getElementById('wb-curve').value,el=document.getElementById('wb-chart'),msg=document.getElementById('wb-curvemsg');if(!cid){el.innerHTML='';msg.textContent='';return;}
  fetch('/api/console/workbench/curve?control='+cid).then(r=>r.json()).then(j=>{const st=wbState(),pts=(j.series||{})[st]||[],n=Object.values(j.series||{}).filter(v=>v.length>=2).length;
    msg.textContent=pts.length>=2?st+': '+pts.length+' values run · '+n+' states have a curve':pts.length?st+': only one value run so far · '+n+' states have a curve':'no runs varied this control in '+st+' · '+n+' states have a curve';
    if(pts.length<2){el.innerHTML='<div class="mx-empty">Run two or more values of this control in '+esc(st)+' (Run in every state, or the Test Plan Builder) to draw its curve.</div>';return;}
    const num=v=>parseFloat(String(v).replace(/[^0-9.\-]/g,''))||0;pts.sort((a,b)=>num(a.value)-num(b.value));
    const W=el.clientWidth||700,H=180,L=56,R=16,T=10,B=34,ys=pts.flatMap(p=>[+p.ours,p.iso?+p.iso:null]).filter(v=>v!=null&&!isNaN(v)),lo=Math.min(...ys),hi=Math.max(...ys);
    const x=i=>L+(W-L-R)*(pts.length<2?0.5:i/(pts.length-1)),y=v=>T+(H-T-B)*(1-(hi===lo?0.5:(v-lo)/(hi-lo)));
    let s='<svg viewBox="0 0 '+W+' '+H+'" width="100%" height="100%" role="img" aria-label="Premium by value of '+esc(cid)+' in '+st+'">';
    [lo,hi].forEach(v=>s+='<line x1="'+L+'" x2="'+(W-R)+'" y1="'+y(v)+'" y2="'+y(v)+'" stroke="var(--color-divider)"/><text x="'+(L-6)+'" y="'+(y(v)+4)+'" text-anchor="end" font-size="10.5" fill="var(--color-neutral-700)">'+Math.round(v).toLocaleString()+'</text>');
    s+='<polyline fill="none" stroke="#9a6214" stroke-width="2" points="'+pts.map((p,i)=>x(i)+','+y(+p.ours)).join(' ')+'"/>';
    pts.forEach((p,i)=>{s+='<circle cx="'+x(i)+'" cy="'+y(+p.ours)+'" r="4" fill="#9a6214" stroke="var(--color-bg)" stroke-width="2"><title>'+esc(p.value+': ours '+p.ours+(p.iso?' · ISO '+p.iso:''))+'</title></circle>';
      if(p.iso)s+='<circle cx="'+x(i)+'" cy="'+y(+p.iso)+'" r="6" fill="none" stroke="#2f72a8" stroke-width="2"><title>'+esc(p.value+': ISO '+p.iso)+'</title></circle>';
      s+='<text x="'+x(i)+'" y="'+(H-12)+'" text-anchor="middle" font-size="10" fill="var(--color-neutral-700)">'+esc(String(p.value).slice(0,14))+'</text>';});
    el.innerHTML=s+'</svg>';});
}
document.getElementById('wb-lines').addEventListener('click',ev=>{const b=ev.target.closest('button');if(!b||b.dataset.l===WB.line)return;WB.line=b.dataset.l;WB.config={};wbLoad();});
document.getElementById('wb-state').addEventListener('change',()=>{wbInputs();wbCurve();});
document.getElementById('wb-rate').onclick=wbRate;
document.getElementById('wb-send').onclick=wbSendDialog;
document.getElementById('wb-where').onclick=wbWhere;
document.getElementById('wb-every').onclick=wbEvery;
document.getElementById('wb-curve').onchange=wbCurve;
let wbStarted=false;function wbRoute(){if((location.hash||'').startsWith('#workbench')&&!wbStarted){wbStarted=true;wbLoad();}}
addEventListener('hashchange',wbRoute);wbRoute();
"""


# ---- Upload & Compare: the landing screen ---------------------------------------------------------------------------
# Requests the user already has (GL or CP, ISO's own request format, one per file or a list): the line and state read
# from ProductName, each rated on our engine (free) beside ISO's stored answer for exactly that request when there is
# one; the rest sent to ISO only after a confirmation that says what it spends (ad hoc lane, through the ledger).

UP_HTML = """<section class="screen" id="s-compare" hidden><div class="mx-wrap"><div class="mx-main">
  <div class="mx-head"><div><div class="eyebrow">Your requests · free to rate, one call each to ask ISO</div><h1>Upload &amp; Compare</h1></div>
    <p>Drop in GL or Property requests in ISO's request format. Each is rated on our engine for free and set beside ISO's
    answer when one is already stored for that exact request. Or generate a working request for any state. Asking ISO about the rest spends calls, and nothing is sent until you confirm.</p></div>
  <div class="up-gen"><b>Generate a request</b>
    <label>Line <select id="up-lob"><option value="GL">General Liability</option><option value="CP">Commercial Property</option></select></label>
    <label>State <select id="up-state"></select></label><button class="btn" id="up-gen">Generate and rate · free</button>
    <span class="mx-msg">a working request for the state: GL from ISO's own options, Property the state's sample risk</span></div>
  <div class="up-gen up-co"><b>Writing company</b>
    <label><select id="up-company"><option value="">None: ISO only</option></select></label>
    <label>Business <select id="up-pt"><option>New</option><option>Renewal</option></select></label>
    <span class="mx-msg" id="up-comsg">With a company, each request is rated twice: <b>technical</b> (pure ISO, the request ISO is asked about)
    and <b>carrier</b> (through the company's filing, never sent to ISO). Click a carrier figure to see what the deviations did.</span></div>
  <label class="up-drop" id="up-drop"><input type="file" id="up-file" accept=".json,application/json" multiple hidden>
    <b>Drop request files here, or choose files</b><span class="mx-msg">.json · one request per file, or a list of them · GL and Property can be mixed</span></label>
  <details class="up-paste"><summary>Or paste a request</summary><textarea id="up-text" spellcheck="false" placeholder='{"header": {...}, "body": {"SchemeKeys": {"ProductName": "General Liability OH", ...}, ...}}'></textarea>
    <div class="td-tools"><button class="btn" id="up-add">Add and rate · free</button></div></details>
  <div class="td-tools"><button class="btn" id="up-send" disabled>Compare with ISO…</button><button class="btn" id="up-clear">Clear</button><span class="mx-msg" id="up-msg"></span></div>
  <div id="up-confirm"></div>
  <div id="up-out"><div class="mx-empty">No requests yet.</div></div>
  <div id="up-ws"></div>
</div><aside class="mx-side" id="up-side" aria-live="polite"></aside></div></section>"""

BUILT["compare"] = UP_HTML

UP_CSS = """
.up-drop{display:flex;flex-direction:column;gap:4px;align-items:center;justify-content:center;text-align:center;min-height:110px;margin:14px 0 10px;
  border:1.5px dashed var(--color-neutral-400);border-radius:var(--radius-lg);background:var(--color-bg);cursor:pointer;padding:16px}
.up-drop.over{border-color:var(--color-accent-700);background:var(--color-accent-100)}
.up-paste summary{cursor:pointer;font-size:12.5px;margin-bottom:6px}
#up-text{width:100%;min-height:160px;font:11.5px ui-monospace,Menlo,monospace;padding:6px;border:1px solid var(--color-divider);border-radius:4px}
.up-tbl{width:100%;border-collapse:collapse;font-size:12.5px;margin-top:10px}
.up-tbl th{text-align:left;font-weight:600;font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--color-neutral-700);padding:4px 6px}
.up-tbl td{padding:6px;border-top:1px solid var(--color-divider);vertical-align:top}
.up-tbl .v{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.up-tbl .file{max-width:240px;overflow-wrap:anywhere}
.up-tbl .x{border:0;background:none;cursor:pointer;color:var(--color-neutral-600);font-size:15px}
.up-res{display:flex;gap:6px;align-items:flex-start}
.up-gen{display:flex;gap:12px;flex-wrap:wrap;align-items:center;font-size:12.5px;margin-top:14px;padding:10px 12px;border:1px solid var(--color-divider);border-radius:var(--radius-lg)}
.up-gen select{font:inherit;padding:5px 7px;border:1px solid var(--color-divider);border-radius:4px;background:#fff}
.up-tbl .acts{white-space:nowrap}.up-tbl .acts a{margin-right:8px;cursor:pointer}
.ws{margin-top:18px;border-top:2px solid var(--color-neutral-700);padding-top:10px}
.ws-hd{display:flex;gap:18px;flex-wrap:wrap;align-items:baseline}.ws-hd h2{margin:0;font-size:18px}
.ws-prem{display:flex;gap:22px;margin:8px 0}.ws-prem div{font-size:12px}.ws-prem b{display:block;font-size:20px;font-variant-numeric:tabular-nums}
.ws-tools{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:6px 0 4px;font-size:12.5px}
.ws-tools button.on{background:var(--color-accent-100);border-color:var(--color-accent-700)}
.ws-tbl{width:100%;border-collapse:collapse;font-size:12px}
.ws-tbl th{text-align:left;font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--color-neutral-700);padding:4px 6px;position:sticky;top:0;background:var(--color-bg)}
.ws-tbl td{padding:3px 6px;border-top:1px solid var(--color-divider);vertical-align:top}
.ws-tbl .v{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.ws-tbl tr.rec td{background:var(--color-neutral-100,#eee);font-weight:600;cursor:pointer;overflow-wrap:anywhere}
.ws-tbl td.bad{color:#9b1c1c;font-weight:600}.ws-tbl td.chg{background:var(--color-accent-100);font-weight:600}
.ws-tbl a.ws-why{cursor:pointer;color:inherit;text-decoration:underline dotted;text-underline-offset:2px}
.wy ul{list-style:none;margin:0;padding-left:14px;border-left:1px solid var(--color-divider)}.wy ul.wy-root{padding-left:0;border:0}
.wy li{margin:3px 0;font-size:12px;overflow-wrap:anywhere}.wy-v{font-weight:600;font-variant-numeric:tabular-nums}
.wy-k{color:var(--color-neutral-700);font-size:10.5px;text-transform:uppercase;letter-spacing:.04em}
.wy li.wy-aff>.wy-v,.wy li.wy-aff>.wy-name{background:var(--color-accent-100)}.wy li.wy-ctl>.wy-name{font-style:italic}
.wy-more{cursor:pointer;font-size:11px;margin-left:4px}.wy-src li{border:0}
.ws-tbl tr.ws-app td{border-top:1px dashed var(--color-accent-700)}.ws-tbl tr.ws-app td:first-child{font-weight:600}
.ws-tbl .src{color:var(--color-neutral-700);font-size:11px;overflow-wrap:anywhere;max-width:340px}
.ws-scroll{max-height:70vh;overflow:auto;border:1px solid var(--color-divider);border-radius:4px}
.up-co{margin-top:8px}.up-tbl a.car{cursor:pointer;font-weight:600}.up-tbl tr.sel td{background:var(--color-accent-100)}
.up-dv table{width:100%;font-size:12px;table-layout:fixed}.up-dv td{padding:2px 0;overflow-wrap:anywhere;vertical-align:top}
.up-dv td:first-child{width:42%;padding-right:6px}.up-dv td+td{text-align:right}.up-dv .w{color:var(--color-neutral-700);font-size:11.5px;margin-top:6px}
"""

UP_JS = r"""
const UP={rows:[],seq:0,busy:false,q:Promise.resolve(),spec:{}};
function upAdd(name,text){
  let v;try{v=JSON.parse(text);}catch(e){UP.rows.push({id:++UP.seq,name,err:'Not valid JSON: '+e.message});upDraw();return;}
  const list=Array.isArray(v)?v:[v];
  list.forEach((_,i)=>{const row={id:++UP.seq,name:list.length>1?name+' #'+(i+1):name,text,index:i,list:Array.isArray(v),busy:'rating'};UP.rows.push(row);upRate(row);});
  upDraw();
}
function upRate(row){row.busy='rating';
  const co=UP.company||'',pt=UP.pt||'New';
  return UP.q=UP.q.then(()=>wbJSON('/api/console/workbench/upload',{text:row.text,index:row.index,company:co,policyType:pt}).then(r=>{row.busy='';if(r.error)row.err=r.error;else{row.err='';row.r=r;}upDraw();})
    .catch(e=>{row.busy='';row.err=String(e);upDraw();}));}
function upNeeds(){return UP.rows.filter(x=>x.r&&!x.r.stored&&!x.busy);}
function upVerdict(r){const s=r.stored;
  if(!s)return '<span class="mx-msg">not asked yet</span>';
  if(s.outcome!=='rated')return '<span class="up-res"><span class="chip untested">·</span><span>ISO refused<div class="mx-msg">'+esc((s.message||'').slice(0,160))+'</div></span></span>';
  if(r.outcome!=='rated')return '<span class="up-res"><span class="chip mismatch">×</span><span>ISO rated it; ours '+esc(r.outcome)+'</span></span>';
  const d=Number(r.premium)-Number(s.iso);
  return d===0?'<span class="up-res"><span class="chip verified">✓</span><span>Agree</span></span>':
    '<span class="up-res"><span class="chip mismatch">×</span><span>Differ by '+esc((d>0?'+':'')+d.toFixed(2))+'</span></span>';}
function upDraw(){
  const out=document.getElementById('up-out');
  if(!UP.rows.length)out.innerHTML='<div class="mx-empty">No requests yet.</div>';
  else out.innerHTML='<table class="up-tbl"><tr><th>Request</th><th>Line · state</th><th>Effective</th><th class="v">Technical</th><th class="v">ISO</th><th class="v">Carrier</th><th>ISO test</th><th></th></tr>'+
    UP.rows.map(x=>{const r=x.r,s=r&&r.stored,rm='<button class="x" data-x="'+x.id+'" title="Remove">×</button>';
      if(x.err)return '<tr><td class="file">'+esc(x.name)+'</td><td colspan="6"><span class="up-res"><span class="chip mismatch">!</span><span>'+esc(x.err)+'</span></span></td><td>'+rm+'</td></tr>';
      if(!r)return '<tr><td class="file">'+esc(x.name)+'</td><td colspan="6" class="mx-msg">Rating on our engine…</td><td></td></tr>';
      const ours=r.outcome==='rated'?esc(r.premium):esc(r.outcome);
      const iso=x.busy==='sending'?'<span class="mx-msg">asking ISO…</span>':!s?'<span class="mx-msg">—</span>':s.outcome==='rated'?esc(s.iso)+'<div class="mx-msg">stored '+esc((s.stored_at||s.date||'').slice(0,10))+(s.freshness==='stale'?' · stale':'')+'</div>':'refused';
      return '<tr'+(UP.sel===x.id?' class="sel"':'')+'><td class="file">'+esc(x.name)+(r.outcome!=='rated'?'<div class="mx-msg">'+esc((r.detail||'').slice(0,200))+'</div>':'')+'</td><td>'+(r.line==='GL'?'General Liability':'Property')+' · '+esc(r.state)+'</td><td>'+esc(r.effective)+
        '</td><td class="v">'+ours+'</td><td class="v">'+iso+'</td><td class="v">'+upCarrier(x)+'</td><td>'+upVerdict(r)+'</td><td>'+
        '<span class="acts">'+(s&&s.outcome==='rated'?'<a href="#trace?lob='+r.line+'&scenario='+encodeURIComponent(s.scenario)+'">Trace Diff</a>':'')+'<a data-ws="'+x.id+'" title="Every field, Technical | ISO | Deviated">Worksheet</a><a data-dl="'+x.id+'" title="Save this request as a .json file">Download</a><a data-ed="'+x.id+'" title="Copy into the paste box to change it">Edit</a></span>'+rm+'</td></tr>';}).join('')+'</table>';
  const n=upNeeds().length,b=document.getElementById('up-send');
  b.disabled=!n||UP.busy;b.textContent=n?'Compare with ISO · '+n+' call'+(n>1?'s':'')+'…':'Compare with ISO…';
  upSide();
}
function upCarrier(x){const r=x.r,c=r&&r.carrier;
  if(!c)return '<span class="mx-msg">—</span>';
  if(c.outcome!=='rated')return '<a class="car" data-dv="'+x.id+'">refused</a>';
  const d=r.premium!=null?Number(c.premium)-Number(r.premium):null;
  return '<a class="car" data-dv="'+x.id+'" title="What the deviations did">'+esc(c.premium)+'</a>'+(d!==null?'<div class="mx-msg">'+(d>=0?'+':'')+d.toFixed(0)+' vs technical</div>':'');}
function upDev(x){const r=x.r,d=r.deviation||{},k=(t,v)=>'<tr><td>'+t+'</td><td style="text-align:right">'+v+'</td></tr>';
  const f=(d.filings||[]).map(f=>esc(f.id)+' v'+f.version+'<br>new '+esc(f.new_eff)+'<br>renewal '+esc(f.renewal_eff)).join('<br>')||'<i>no filing in force</i>';
  return '<div class="cap2">What the deviations did</div><div class="up-dv"><b>'+esc(x.name)+'</b><table>'+
    k('Writing company',esc(r.company)+' · '+esc(r.policyType))+k('Filing',f)+k('ISO edition',esc(d.edition||'')+(d.pinned?' (pinned)':''))+
    k('Technical (pure ISO)',esc(d.technicalPremium??'—'))+k('Carrier',esc(d.carrierPremium??'—'))+'</table>'+
    '<div class="cap2" style="margin-top:8px">Step by step</div><table>'+(d.waterfall||[]).map(s=>k(esc(s.step),(Number(s.effect)>=0?'+':'')+esc(s.effect))).join('')+'</table>'+
    '<div class="mx-msg">'+(d.changedFields||0)+' fields differ from technical. ISO is asked about the non-deviated request only; the carrier is never sent.</div>'+
    (d.refused?'<div class="w"><b>Refused:</b> '+esc(d.refused)+'</div>':'')+
    ((d.warnings||[]).length?'<div class="w"><b>Warnings</b><br>'+d.warnings.map(esc).join('<br>')+'</div>':'')+
    '<div class="td-tools"><a data-unsel="1" style="cursor:pointer">Back to the upload summary</a></div></div>';}
function upCompanies(){fetch('/api/console/workbench/companies').then(r=>r.json()).then(j=>{const sel=document.getElementById('up-company');
  (j.companies||[]).forEach(c=>{const o=document.createElement('option');o.value=c.code;
    const fs=c.filings.filter(f=>f.approved).map(f=>f.line+' '+f.juris).join(', ');
    o.textContent=c.code+' · '+c.name+' ('+c.carrier+(fs?': '+fs:'')+')';sel.appendChild(o);});}).catch(()=>{});}
function upRerate(){UP.company=document.getElementById('up-company').value;UP.pt=document.getElementById('up-pt').value;UP.sel=null;
  UP.rows.filter(x=>!x.err&&x.text).forEach(x=>{x.r=null;upRate(x);});upDraw();}
const WS={d:null,name:'',filter:'all',q:'',shut:new Set(),view:'calc',why:null};
function wsOpen(x){const el=document.getElementById('up-ws');WS.name=x.name;WS.shut=new Set();
  el.innerHTML='<div class="ws"><div class="mx-msg">Building the worksheet for '+esc(x.name)+'… (two ratings, no ISO call)</div></div>';el.scrollIntoView({block:'start'});
  wbJSON('/api/console/workbench/worksheet',{text:x.text,index:x.index,company:(x.r&&x.r.company)||'',policyType:(x.r&&x.r.policyType)||'New'})
    .then(d=>{WS.d=d;wsDraw();}).catch(e=>{el.innerHTML='<div class="ws"><div class="mx-empty">'+esc(String(e))+'</div></div>';});}
function wsShown(){const d=WS.d,q=WS.q.toLowerCase();
  return d.rows.filter(r=>(WS.filter==='all'||(WS.filter==='diff'&&(r.techIso===false||r.changed))||(WS.filter==='dev'&&r.changed)||
    (WS.filter==='iso'&&r.techIso===false)||(WS.filter==='num'&&r.kind==='number'))&&(!q||(r.path+' '+r.rule).toLowerCase().includes(q)));}
function wsCell(v){return v===null||v===undefined?'<span class="mx-msg">—</span>':esc(String(v));}
function wsVal(r,side){const v=side==='technical'?r.technical:r.deviated,g=side==='technical'?r.tg:r.dg;
  return g===undefined||g===null||v===null||v===undefined?wsCell(v):'<a class="ws-why" data-side="'+side+'" data-gid="'+g+'" title="Why this value">'+esc(String(v))+'</a>';}
function wsDraw(){const d=WS.d,el=document.getElementById('up-ws');
  if(d.error){el.innerHTML='<div class="ws"><div class="mx-empty">'+esc(d.error)+'</div></div>';return;}
  const hasDev=!!d.company,P=d.premium,isoNote=d.iso==='rated'?'':d.iso==='refused'?' (ISO refused it)':' (not asked yet: Compare with ISO to fill this column)';
  const rows=wsShown(),by={};
  if(WS.view==='calc'){const keep=new Set(rows.map(r=>r.path)),all={};d.rows.forEach(r=>{all[r.path]=r;});
    (d.sections||[]).forEach(sc=>{const rs=sc.paths.filter(p=>keep.has(p)).map(p=>all[p]);if(rs.length)by[sc.label]=rs;});}
  else rows.forEach(r=>{(by[r.record]=by[r.record]||[]).push(r);});
  const cnt=f=>d.rows.filter(f).length,btn=(k,t)=>'<button class="btn'+(WS.filter===k?' on':'')+'" data-wf="'+k+'">'+t+'</button>';
  el.innerHTML='<div class="ws"><div class="ws-hd"><h2>Rating worksheet · '+esc(WS.name)+'</h2><span class="mx-msg">'+(d.line==='GL'?'General Liability':'Property')+' · '+esc(d.state)+
    (hasDev?' · writing company '+esc(d.company)+' · '+esc(d.policyType):' · no writing company')+'</span><a data-wclose="1" style="cursor:pointer;margin-left:auto">Close</a></div>'+
    '<div class="ws-prem"><div>Technical<b>'+wsCell(P.technical)+'</b>our engine, pure ISO</div><div>ISO<b>'+wsCell(P.iso)+'</b>its answer to the same request'+esc(isoNote)+'</div>'+
    (hasDev?'<div>Deviated<b>'+wsCell(P.deviated)+'</b>our engine with the filing, never sent to ISO</div>':'')+'</div>'+
    '<div class="ws-tools">'+btn('all','All fields · '+d.rows.length)+btn('diff','Any difference · '+cnt(r=>r.techIso===false||r.changed))+
    (hasDev?btn('dev','Deviated changes · '+cnt(r=>r.changed)):'')+btn('iso','Technical ≠ ISO · '+cnt(r=>r.techIso===false))+btn('num','Numbers only')+
    '<span style="margin-left:8px">View</span>'+['calc','record'].map(v=>'<button class="btn'+(WS.view===v?' on':'')+'" data-wv="'+v+'">'+(v==='calc'?'By calculation':'By record')+'</button>').join('')+
    '<input id="ws-q" placeholder="Find a field, record or rule" value="'+esc(WS.q)+'" style="flex:1;min-width:180px"><button class="btn" data-wcsv="1">Download CSV</button></div>'+
    '<div class="ws-scroll"><table class="ws-tbl"><tr><th>Field</th><th class="v">Technical</th><th class="v">ISO</th>'+(hasDev?'<th class="v">Deviated</th>':'')+'<th>Written by (technical)</th></tr>'+
    Object.entries(by).map(([rec,rs])=>{const shut=WS.shut.has(rec);
      const calc=WS.view==='calc',parts=calc?[]:rec.split('/').filter(Boolean),name=calc?rec:(parts.pop()||'(policy)'),trail=parts.map(x=>x.replace(/^CommercialProperty|^GeneralLiability/,'')||x).join(' › ');
      return '<tr class="rec" data-rec="'+esc(rec)+'" title="'+esc(rec)+'"><td colspan="'+(hasDev?5:4)+'">'+(shut?'▸ ':'▾ ')+esc(name)+' <span class="mx-msg">'+rs.length+' field'+(rs.length>1?'s':'')+(trail?' · in '+esc(trail):'')+'</span></td></tr>'+
        (shut?'':rs.map(r=>'<tr'+(r.applied?' class="ws-app"':'')+'><td title="'+esc(r.path)+'">'+esc(calc?(r.label||r.field):r.field)+(r.note?'<div class="mx-msg">'+esc(r.note)+'</div>':'')+'</td><td class="v">'+wsVal(r,'technical')+'</td><td class="v'+(r.techIso===false&&d.iso==='rated'?' bad':'')+'">'+wsCell(r.iso)+'</td>'+
          (hasDev?'<td class="v'+(r.changed?' chg':'')+'">'+wsVal(r,'deviated')+'</td>':'')+'<td class="src">'+esc(r.rule||'')+(r.tables&&r.tables.length?' · '+esc(r.tables.join(', ')):'')+'</td></tr>').join(''));}).join('')+
    '</table></div><div class="mx-msg">Click a technical or deviated value to see what it was computed from. By calculation: one section per coverage group of each rated item, its factors in the order our engine computed them (inputs first). <b>LCM applied</b>: the LCM that group rate was multiplied by (Property applies one per coverage group; ISO and technical apply the one record LCM to every group). Red ISO value: technical and ISO differ there. Highlighted deviated value: the filing changed it. "Written by" is the ERC rule file (and the tables read just before) that wrote the technical value.</div></div>';
  const q=document.getElementById('ws-q');q.oninput=()=>{WS.q=q.value;const pos=q.selectionStart;wsDraw();const n=document.getElementById('ws-q');n.focus();n.setSelectionRange(pos,pos);};}
function wsCSV(){const d=WS.d,hasDev=!!d.company,qq=v=>v===null||v===undefined?'':'"'+String(v).replace(/"/g,'""')+'"';
  const head=['Section','Record','Field','Technical','ISO'].concat(hasDev?['Deviated']:[]).concat(['Technical vs ISO','Changed by deviations','Written by','Tables']);
  const rank={};(d.sections||[]).forEach((sc,i)=>sc.paths.forEach((p,j)=>{rank[p]=[i,j];}));
  const shown=wsShown().slice().sort((a,b)=>{const x=rank[a.path]||[1e9,0],y=rank[b.path]||[1e9,0];return x[0]-y[0]||x[1]-y[1];});
  const lines=[head.map(qq).join(',')].concat(shown.map(r=>[r.sectionLabel||'',r.record,r.label||r.field,r.technical,r.iso].concat(hasDev?[r.deviated]:[])
    .concat([r.techIso===null?'':r.techIso?'agree':'differ',hasDev?(r.changed?'yes':'no'):'',r.rule,(r.tables||[]).join('; ')]).map(qq).join(',')));
  const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([lines.join('\r\n')],{type:'text/csv'}));
  a.download='worksheet-'+d.line+'-'+d.state+(d.company?'-'+d.company:'')+'.csv';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);}
function wsWhy(side,gid){WS.why={loading:true,side};upSide();
  wbJSON('/api/console/workbench/why',{token:WS.d.graph,side,gid,depth:3}).then(j=>{WS.why=j;upSide();}).catch(e=>{WS.why={error:String(e)};upSide();});}
function wyFind(n,id){if(n.id===id)return n;for(const c of n.from||[]){const f=wyFind(c,id);if(f)return f;}return null;}
function wyNode(n){const kind=n.kind==='table'?(n.company?'company table row':'table'):n.kind==='company'?'filing':n.kind==='input'?'input':(n.op||'');
  const more=n.inputs&&!(n.from&&n.from.length)?' <a class="wy-more" data-wexp="'+n.id+'">show its '+n.inputs+' input'+(n.inputs>1?'s':'')+'</a>':'';
  return '<li class="'+(n.affected?'wy-aff':'')+(n.edge==='control'?' wy-ctl':'')+'"><span class="wy-v">'+esc(n.value??'—')+'</span> <span class="wy-name">'+esc(n.name||'')+'</span>'+
    ' <span class="wy-k">'+esc(n.edge==='control'?'decides whether · ':'')+esc(kind)+'</span>'+(n.kind==='company'&&n.explain?'<div class="mx-msg">'+esc(n.explain)+'</div>':'')+more+
    (n.from&&n.from.length?'<ul>'+n.from.map(wyNode).join('')+'</ul>':'')+'</li>';}
function wyHtml(w){if(w.loading)return '<div class="cap2">Why this value</div><div class="mx-msg">Reading the rating graph…</div>';
  if(w.error)return '<div class="cap2">Why this value</div><div class="mx-empty">'+esc(w.error)+'</div><a data-wyback="1" style="cursor:pointer">Back</a>';
  const S=w.sources||[],k=t=>S.filter(x=>x.kind===t),li=x=>'<li><span class="wy-v">'+esc(x.value??'—')+'</span> '+esc(x.name)+(x.kind==='table'?' <span class="wy-k">'+esc(x.package||'')+'</span>':'')+'</li>';
  return '<div class="cap2">Why this value · '+(w.side==='deviated'?'deviated':'technical')+'</div><div class="wy">'+
    '<ul class="wy-root">'+wyNode(w.node)+'</ul>'+
    (w.side==='deviated'?'<div class="mx-msg">Highlighted: reached by the carrier filing. </div>':'')+
    '<div class="cap2" style="margin-top:10px">Everything it came from</div>'+
    (k('company').length?'<div class="mx-msg">Filing</div><ul class="wy-src">'+k('company').map(li).join('')+'</ul>':'')+
    (k('table').length?'<div class="mx-msg">Tables · '+k('table').length+'</div><ul class="wy-src">'+k('table').map(li).join('')+'</ul>':'')+
    (k('input').length?'<div class="mx-msg">Inputs · '+k('input').length+'</div><ul class="wy-src">'+k('input').map(li).join('')+'</ul>':'')+
    '<div class="td-tools"><a data-wyback="1" style="cursor:pointer">Back to the upload summary</a></div></div>';}
document.getElementById('up-side').addEventListener('click',ev=>{
  if(ev.target.closest('[data-wyback]')){WS.why=null;upSide();return;}
  const ex=ev.target.closest('[data-wexp]');if(ex&&WS.why&&WS.why.node){const id=Number(ex.dataset.wexp);
    wbJSON('/api/console/workbench/why',{token:WS.d.graph,side:WS.why.side,gid:id,depth:3}).then(j=>{const n=wyFind(WS.why.node,id);if(n&&j.node){n.from=j.node.from;}upSide();});}});
document.getElementById('up-ws').addEventListener('click',ev=>{const t=ev.target;
  const wy=t.closest('[data-gid]');if(wy){wsWhy(wy.dataset.side,Number(wy.dataset.gid));return;}
  if(t.closest('[data-wclose]')){document.getElementById('up-ws').innerHTML='';WS.d=null;WS.why=null;upSide();return;}
  if(t.closest('[data-wcsv]')){wsCSV();return;}
  const f=t.closest('[data-wf]');if(f){WS.filter=f.dataset.wf;wsDraw();return;}
  const v=t.closest('[data-wv]');if(v){WS.view=v.dataset.wv;WS.shut=new Set();wsDraw();return;}
  const rc=t.closest('[data-rec]');if(rc){const k=rc.dataset.rec;WS.shut.has(k)?WS.shut.delete(k):WS.shut.add(k);wsDraw();}});
function upSide(){
  if(WS.why){document.getElementById('up-side').innerHTML=wyHtml(WS.why);return;}
  const sx=UP.sel&&UP.rows.find(x=>x.id===UP.sel&&x.r&&x.r.carrier);
  if(sx){document.getElementById('up-side').innerHTML=upDev(sx);return;}
  const R=UP.rows.filter(x=>x.r).map(x=>x.r),both=R.filter(r=>r.stored&&r.stored.outcome==='rated'&&r.outcome==='rated');
  const agree=both.filter(r=>Number(r.premium)===Number(r.stored.iso)).length;
  const k=(t,v)=>'<tr><td>'+t+'</td><td style="text-align:right">'+v+'</td></tr>';
  document.getElementById('up-side').innerHTML='<div class="cap2">This upload</div><table>'+k('Requests',UP.rows.length)+k('Rated by our engine',R.filter(r=>r.outcome==='rated').length)+
    k('ISO answered',R.filter(r=>r.stored).length)+k('Agree with ISO',agree)+k('Differ from ISO',both.length-agree)+k('Not asked yet',upNeeds().length)+
    k('Could not be read',UP.rows.filter(x=>x.err).length)+'</table><div class="mx-msg">Rated with strict ERC and ROUND_HALF_UP, as the Workbench does; for another mode use <a href="/">the rating page</a>. '+
    'A request ISO already answered is never sent again: its stored answer is used, free. Each answer ISO gives is stored, so it shows in Trace Diff and counts as evidence.</div>';
}
function upSendDialog(){
  const need=upNeeds(),el=document.getElementById('up-confirm');if(!need.length)return;
  fetch('/api/console/cap').then(r=>r.json()).then(c=>{
    const ad=c.lanes.find(l=>l.key==='adhoc'),room=Math.max(0,Math.min(ad.cap-ad.used,c.left)),over=need.length>room,n=need.length,pl=n>1?'s':'';
    el.innerHTML='<div class="wb-conf'+(over?' full':'')+'"><b>Ask ISO about '+n+' request'+pl+'?</b>'+
      '<div>No stored answer covers '+(n>1?'them':'it')+': this spends <b>'+n+' call'+pl+'</b> from the ad hoc lane, one at a time, each logged in the ledger.</div>'+
      '<div class="mx-msg">Ad hoc lane: '+ad.used+' of '+ad.cap+' used today · '+c.left+' of '+c.cap+' left in all'+(over?' · <b>'+(n-room)+' would go past the cap</b>: they need a reason, logged with each.':'')+'</div>'+
      '<div class="td-tools">'+(over?'<input id="up-reason" placeholder="Reason for going past the cap" style="flex:1">':'')+'<button class="btn" id="up-go">Send · '+n+' call'+pl+'</button><button class="btn" id="up-cancel">Cancel</button></div><div class="mx-msg" id="up-cmsg"></div></div>';
    document.getElementById('up-cancel').onclick=()=>{el.innerHTML='';};
    document.getElementById('up-go').onclick=()=>{const rs=document.getElementById('up-reason'),why=rs?rs.value.trim():'';
      if(over&&!why){document.getElementById('up-cmsg').textContent='A reason is needed past the cap.';return;}
      el.innerHTML='';upSend(need,why);};});
}
async function upSend(rows,why){
  UP.busy=true;const msg=document.getElementById('up-msg');let sent=0,reused=0,stop='';
  for(const row of rows){
    row.busy='sending';upDraw();msg.textContent='Asking ISO: '+(sent+reused+1)+' of '+rows.length+'…';
    let j;try{j=await wbJSON('/api/console/workbench/upload-send',{text:row.text,index:row.index,reuse:true,override:why,company:(row.r&&row.r.company)||''});}catch(e){j={error:String(e)};}
    row.busy='';
    if(j.error){stop=(j.capped?'Stopped at the cap: ':'Stopped: ')+j.error;upDraw();break;}
    j.reused?reused++:sent++;row.r.stored=j.stored;upDraw();}
  UP.busy=false;fetch('/api/console/cap').then(r=>r.json()).then(drawCap);
  msg.textContent=(stop?stop+' · ':'Done: ')+sent+' call'+(sent===1?'':'s')+' spent'+(reused?', '+reused+' answered from the store':'')+'.';
  upDraw();
}
function upItem(x){const v=JSON.parse(x.text);return JSON.stringify(Array.isArray(v)?v[x.index]:v,null,1);}
function upDownload(x){const a=document.createElement('a'),r=x.r;
  a.href=URL.createObjectURL(new Blob([x.list?upItem(x):x.text],{type:'application/json'}));
  a.download=(r?r.line+'-'+r.state+(x.gen?'':'-'+x.name.replace(/\.json.*$/i,'')):x.name.replace(/\.json.*$/i,''))+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);}
function upEdit(x){const d=document.querySelector('.up-paste'),t=document.getElementById('up-text');d.open=true;t.value=x.list?upItem(x):x.text;
  UP.editName='Edited '+x.name.replace(/^(Generated|Edited) /,'');t.focus();t.setSelectionRange(0,0);t.scrollTop=0;t.scrollIntoView({block:'center'});}
function upGenStates(){const lob=document.getElementById('up-lob').value,sel=document.getElementById('up-state');
  const go=s=>{UP.spec[lob]=s;sel.innerHTML='<option value="*">All states ('+s.states.length+')</option>'+s.states.map(x=>'<option'+(x==='OH'?' selected':'')+'>'+x+'</option>').join('');};
  UP.spec[lob]?go(UP.spec[lob]):fetch('/api/console/workbench/spec?lob='+lob).then(r=>r.json()).then(go);}
function upGen(){const lob=document.getElementById('up-lob').value,st=document.getElementById('up-state').value,spec=UP.spec[lob];if(!spec)return;
  (st==='*'?spec.states:[st]).reduce((q,s)=>q.then(()=>fetch('/api/console/workbench/generate?lob='+lob+'&state='+s).then(r=>r.json()).then(j=>{
    if(j.error){UP.rows.push({id:++UP.seq,name:'Generated '+lob+' '+s,err:j.error});upDraw();return;}
    const n=UP.rows.length;upAdd('Generated '+(lob==='GL'?'GL':'Property')+' '+s,j.text);UP.rows.slice(n).forEach(x=>x.gen=true);})),Promise.resolve());}
function upFiles(files){[...files].forEach(f=>f.text().then(t=>upAdd(f.name,t)));}
(function(){const d=document.getElementById('up-drop'),f=document.getElementById('up-file');
  f.onchange=()=>{upFiles(f.files);f.value='';};
  ['dragenter','dragover'].forEach(e=>d.addEventListener(e,ev=>{ev.preventDefault();d.classList.add('over');}));
  ['dragleave','drop'].forEach(e=>d.addEventListener(e,ev=>{ev.preventDefault();d.classList.remove('over');}));
  d.addEventListener('drop',ev=>upFiles(ev.dataTransfer.files));
  document.getElementById('up-add').onclick=()=>{const t=document.getElementById('up-text');if(!t.value.trim())return;upAdd(UP.editName||'Pasted request',t.value);t.value='';UP.editName='';};
  document.getElementById('up-send').onclick=upSendDialog;
  document.getElementById('up-clear').onclick=()=>{if(UP.busy)return;UP.rows=[];document.getElementById('up-msg').textContent='';document.getElementById('up-confirm').innerHTML='';upDraw();};
  document.getElementById('up-out').addEventListener('click',ev=>{const dv=ev.target.closest('[data-dv]');
    if(dv){UP.sel=Number(dv.dataset.dv);upDraw();return;}
    const ws=ev.target.closest('[data-ws]');if(ws){const x=UP.rows.find(r=>String(r.id)===ws.dataset.ws);if(x)wsOpen(x);return;}
    const dl=ev.target.closest('[data-dl]'),ed=ev.target.closest('[data-ed]');
    if(dl||ed){const x=UP.rows.find(r=>String(r.id)===(dl||ed).dataset[dl?'dl':'ed']);if(x)(dl?upDownload:upEdit)(x);return;}
    const b=ev.target.closest('[data-x]');if(!b||UP.busy)return;UP.rows=UP.rows.filter(x=>String(x.id)!==b.dataset.x);upDraw();});
  document.getElementById('up-lob').onchange=upGenStates;
  document.getElementById('up-company').onchange=upRerate;document.getElementById('up-pt').onchange=upRerate;
  document.getElementById('up-side').addEventListener('click',ev=>{if(ev.target.closest('[data-unsel]')){UP.sel=null;upDraw();}});
  upCompanies();
  document.getElementById('up-gen').onclick=upGen;
  upGenStates();upSide();})();
"""

# ---- P4: the Deviations Proof board ---------------------------------------------------------------------------------
# T1-T10 of DEVIATIONS-PLAN.md as rows, each from the last run of the suite that proves it (`console.deviations_proof`);
# T3 and T8 list every case ISO answered, each linked into Trace Diff. Nothing here rates or spends a call.

PROOF_HTML = """<section class="screen" id="s-proof" hidden><div class="mx-wrap"><div class="mx-main">
  <div class="mx-head"><div><div class="eyebrow">Carrier deviations · Technical, ISO, Carrier</div><h1>Deviations Proof</h1></div>
    <p>Each row is one of the plan's ten tests, read from the last run of the suite that proves it. ISO is only ever asked about
    the non-deviated (technical) request; the carrier is proved against technical. Click a row for its checks, and for
    T3 and T8 the cases ISO answered, each opening in Trace Diff.</p></div>
  <div class="mx-stats" id="pf-stats"></div>
  <div id="pf-out"><div class="mx-loading">Loading…</div></div>
</div><aside class="mx-side" id="pf-side" aria-live="polite"></aside></div></section>"""

BUILT["proof"] = PROOF_HTML

PROOF_CSS = """
.pf-tbl{width:100%;border-collapse:collapse;font-size:12.5px;margin-top:10px}
.pf-tbl th{text-align:left;font-weight:600;font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--color-neutral-700);padding:4px 6px}
.pf-tbl td{padding:7px 6px;border-top:1px solid var(--color-divider);vertical-align:top}
.pf-tbl tr{cursor:pointer}.pf-tbl tr.sel td{background:var(--color-accent-100)}
.pf-tbl .v{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.pf-cases td,.pf-checks td{padding:2px 4px;font-size:11.5px;border-top:1px solid var(--color-divider)}
"""

PROOF_JS = r"""
const PF={d:null,sel:null};
function pfChip(s){return s==='pass'?'<span class="chip verified">✓</span>':s==='fail'?'<span class="chip mismatch">×</span>':'<span class="chip untested">·</span>';}
function pfDraw(){const d=PF.d;if(!d)return;
  const n=s=>d.tests.filter(t=>t.status===s).length;
  document.getElementById('pf-stats').innerHTML='<div><b>'+n('pass')+'</b> of 10 pass</div><div><b>'+n('fail')+'</b> fail</div><div><b>'+n('not run')+'</b> not run</div>';
  document.getElementById('pf-out').innerHTML='<table class="pf-tbl"><tr><th></th><th>Test</th><th>What it proves</th><th class="v">Checks</th><th>Suite</th><th>Last run</th></tr>'+
    d.tests.map(t=>'<tr data-t="'+t.test+'"'+(PF.sel===t.test?' class="sel"':'')+'><td>'+pfChip(t.status)+'</td><td><b>'+t.test+'</b></td><td>'+esc(t.claim)+
      (t.cases.length?'<div class="mx-msg">'+t.cases.filter(c=>c.verdict==='pass').length+' of '+t.cases.length+' ISO cases agree</div>':'')+
      '</td><td class="v">'+t.passed+' / '+t.total+'</td><td class="mx-msg">'+esc(t.suite)+'</td><td class="mx-msg">'+esc((t.ranAt||'never').replace('T',' '))+(t.commit?' · '+esc(t.commit):'')+'</td></tr>').join('')+'</table>'+
    '<div class="mx-msg" style="margin-top:8px">Gate record: '+esc(d.gate)+'. T1 over every stored Property request: '+esc(d.snapshot)+'.</div>';
  pfSide();}
function pfSide(){const el=document.getElementById('pf-side'),t=PF.d&&PF.d.tests.find(x=>x.test===PF.sel);
  if(!t){el.innerHTML='<div class="cap2">Deviations proof</div><div class="mx-msg">Click a test to see its checks. Re-run a suite to refresh its row: '+
    PF.d.tests.map(x=>x.command).filter((v,i,a)=>a.indexOf(v)===i).map(c=>'<div><code>'+esc(c)+'</code></div>').join('')+'</div>';return;}
  el.innerHTML='<div class="cap2">'+t.test+' · '+esc(t.claim)+'</div><div class="mx-msg"><code>'+esc(t.command)+'</code></div>'+
    '<table class="pf-checks">'+t.checks.map(c=>'<tr><td>'+(c[1]?'✓':'×')+'</td><td>'+esc(c[0])+'</td></tr>').join('')+'</table>'+
    (t.cases.length?'<div class="cap2" style="margin-top:8px">Cases ISO answered</div><table class="pf-cases">'+t.cases.map(c=>'<tr><td>'+pfChip(c.verdict==='known'?'':c.verdict)+'</td><td>'+esc(c.line+' '+c.state)+'</td><td>'+
      (c.scenario?'<a href="#trace?lob='+c.line+'&scenario='+encodeURIComponent(c.scenario)+'">Trace Diff</a>':'')+'</td></tr>').join('')+'</table>':'');}
function pfLoad(){fetch('/api/console/deviations/proof').then(r=>r.json()).then(d=>{PF.d=d;pfDraw();})
  .catch(e=>{document.getElementById('pf-out').innerHTML='<div class="mx-empty">Could not load the proof: '+esc(String(e))+'</div>';});}
document.getElementById('pf-out').addEventListener('click',ev=>{const tr=ev.target.closest('[data-t]');if(!tr)return;PF.sel=tr.dataset.t;pfDraw();});
addEventListener('hashchange',()=>{if((location.hash||'').startsWith('#proof'))pfLoad();});
if((location.hash||'').startsWith('#proof'))pfLoad();
"""


# ---- Carrier Filings: the filings log, in the console ---------------------------------------------------------------
# Every filing we have worked on (`console.filings`): its entry in docs/deviations/FILINGS-LOG.md, its source documents
# as received (re-hashed against source.json, openable), and where each writing company's authored versions stand.

FILINGS_HTML = """<section class="screen" id="s-filings" hidden><div class="mx-wrap"><div class="mx-main">
  <div class="mx-head"><div><div class="eyebrow">Carrier deviations · filings log</div><h1>Carrier Filings</h1></div>
    <p>Every carrier filing we have worked on, newest first: where it came from, what was built from it, what was decided and
    how it was proved. Source documents are kept exactly as received in the carrier store, and each is checked against the
    hash recorded when it arrived. Click a filing for its full entry and to open its documents.</p></div>
  <div class="mx-stats" id="fl-stats"></div>
  <div id="fl-out"><div class="mx-loading">Loading…</div></div>
  <div id="fl-entry"></div>
</div><aside class="mx-side" id="fl-side" aria-live="polite"></aside></div></section>"""

BUILT["filings"] = FILINGS_HTML

FILINGS_CSS = """
.fl-tbl{width:100%;border-collapse:collapse;font-size:12.5px;margin-top:10px}
.fl-tbl th{text-align:left;font-weight:600;font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--color-neutral-700);padding:4px 6px}
.fl-tbl td{padding:7px 6px;border-top:1px solid var(--color-divider);vertical-align:top}
.fl-tbl tr[data-f]{cursor:pointer}.fl-tbl tr.sel td{background:var(--color-accent-100)}
.fl-doc{border-top:1px solid var(--color-divider);padding:6px 0;font-size:12px;overflow-wrap:anywhere}
.fl-doc code{font-size:10.5px}
.fl-entry{font-size:12.5px;margin-top:18px;border-top:1px solid var(--color-divider);padding-top:8px;max-width:980px}
.fl-entry h4{margin:14px 0 4px;font-size:12.5px}.fl-entry p{margin:6px 0}.fl-entry ul{margin:4px 0;padding-left:18px}
.fl-entry code{overflow-wrap:anywhere}.fl-mdw{overflow-x:auto}
.fl-md{width:100%;border-collapse:collapse;font-size:12px;margin:6px 0}
.fl-md th{text-align:left;font-weight:600;font-size:11px;color:var(--color-neutral-700)}
.fl-md th,.fl-md td{padding:3px 6px;border-top:1px solid var(--color-divider);text-align:left;vertical-align:top}
.fl-md td:first-child{white-space:nowrap}
"""

FILINGS_JS = r"""
const FL={d:null,sel:null};
function flKey(f){return f.id||f.serff;}
function flVer(v){return esc(v.company)+' v'+esc(String(v.version))+' <span class="mx-msg">'+esc(v.status)+(v.signers.length?' · '+esc(v.signers.join(', ')):'')+'</span>';}
function flChip(ok){return ok?'<span class="chip verified">✓</span> ':'<span class="chip mismatch">×</span> ';}
function flDraw(){const d=FL.d;if(!d)return;const fs=d.filings;
  const docs=fs.reduce((n,f)=>n+f.sources.length,0),bad=fs.reduce((n,f)=>n+f.sources.filter(x=>!x.intact).length,0);
  document.getElementById('fl-stats').innerHTML='<div><b>'+fs.length+'</b> filings</div><div><b>'+docs+'</b> source documents</div><div><b>'+bad+'</b> missing or changed</div>';
  document.getElementById('fl-out').innerHTML=fs.length?'<table class="fl-tbl"><tr><th>#</th><th>Carrier</th><th>Line · state</th><th>SERFF</th><th>Effective</th><th>Companies</th><th>Sources</th><th>Status</th></tr>'+
    fs.map(f=>'<tr data-f="'+esc(flKey(f))+'"'+(FL.sel===flKey(f)?' class="sel"':'')+'><td><b>'+esc(f.id||'—')+'</b></td><td>'+esc(f.carrier)+'</td><td>'+esc(f.line+' · '+f.state)+'</td><td>'+esc(f.serff)+
      '</td><td class="mx-msg">'+esc(f.effective)+'</td><td>'+(f.versions.length?f.versions.map(flVer).join('<br>'):esc(f.companies.join(', ')))+'</td><td>'+
      (f.sources.length?flChip(f.sources.every(x=>x.intact))+f.sources.length:'<span class="mx-msg">not archived</span>')+
      '</td><td>'+esc(f.status)+'</td></tr>').join('')+'</table>'+
    '<div class="mx-msg" style="margin-top:8px">Log: '+esc(d.log)+' · source documents: '+esc(d.store)+'\\(carrier)\\sources\\(SERFF)</div>'
    :'<div class="mx-empty">No filings logged yet.</div>';
  flSide();}
function flSide(){const el=document.getElementById('fl-side'),f=FL.d&&FL.d.filings.find(x=>flKey(x)===FL.sel);
  if(!f){document.getElementById('fl-entry').innerHTML='';el.innerHTML='<div class="cap2">Carrier filings</div><div class="mx-msg">Click a filing for its log entry and its source documents. '+
    'For now filings are passed in the Claude Code session; each is archived as received and logged in '+esc(FL.d?FL.d.log:'the filings log')+'.</div>';return;}
  el.innerHTML='<div class="cap2">'+esc((f.id?f.id+' · ':'')+f.carrier+' '+f.line+' '+f.state)+'</div><div class="mx-msg">SERFF '+esc(f.serff)+(f.received?' · received '+esc(f.received):'')+'</div>'+
    '<div class="cap2" style="margin-top:8px">Source documents</div>'+(f.sources.length?f.sources.map(x=>'<div class="fl-doc">'+flChip(x.intact)+
      (x.present?'<a href="'+esc(x.url)+'" target="_blank" rel="noopener">'+esc(x.name)+'</a>':esc(x.name))+
      '<div class="mx-msg">'+esc(x.what)+'</div><div class="mx-msg">'+(x.intact?'unchanged since it arrived':x.present?'<b>changed since it arrived</b>':'<b>missing</b>')+
      ' · SHA-256 <code>'+esc(x.sha256||'')+'</code></div></div>').join(''):'<div class="mx-msg">Not archived.</div>')+
    (f.versions.length?'<div class="cap2" style="margin-top:8px">Authored</div>'+f.versions.map(v=>'<div class="fl-doc">'+flVer(v)+'<div class="mx-msg">'+esc(v.file)+' · '+v.rows+' rows'+
      (v.lastAt?' · '+esc(v.lastAction)+' '+esc(v.lastAt.replace('T',' ').replace('Z','')):'')+'</div></div>').join(''):'')+
    '';
  document.getElementById('fl-entry').innerHTML=f.entry?'<div class="fl-entry"><div class="cap2">'+esc(f.id)+' · log entry</div>'+f.entry+'</div>':'';}
function flLoad(){fetch('/api/console/filings').then(r=>r.json()).then(d=>{FL.d=d;if(!FL.sel&&d.filings.length)FL.sel=flKey(d.filings[0]);flDraw();})
  .catch(e=>{document.getElementById('fl-out').innerHTML='<div class="mx-empty">Could not load the filings: '+esc(String(e))+'</div>';});}
document.getElementById('fl-out').addEventListener('click',ev=>{const tr=ev.target.closest('[data-f]');if(!tr)return;FL.sel=tr.dataset.f;flDraw();});
addEventListener('hashchange',()=>{if((location.hash||'').startsWith('#filings'))flLoad();});
if((location.hash||'').startsWith('#filings'))flLoad();
"""


# ---- TC-27 / TC-29: the Test Plan Builder -----------------------------------------------------------------------------
# A line, states (no waves, D3) and per dimension the values to cover (from ISO's own domains, TC-26); a reduced grid,
# edges, an allowance that never drops a state (D20); live counters; Tier 0 at zero calls (TC-28); commit with a
# confirmation of what it will spend. Prefilled from the Readiness Matrix's gaps.

PLAN_HTML = """<section class="screen" id="s-plan" hidden><div class="mx-wrap"><div class="mx-main">
  <div class="mx-head"><div><div class="eyebrow">Planning · nothing spent until committed</div><h1>Test Plan Builder</h1></div>
    <p>Choose states and the dimensions to cover, from ISO's own domains. Pairwise covers every pair of values once;
    edges try each dimension at its extremes. Answers ISO already gave are reused, not asked again.</p>
    <div class="bd-lines" id="pl-lines" role="group" aria-label="Line"><button data-l="CP">Commercial Property</button><button data-l="GL">General Liability</button></div></div>
  <div class="pl-sec"><div class="cap2">States · <span id="pl-stc"></span></div>
    <div class="td-tools"><button class="btn" data-st="all">All</button><button class="btn" data-st="none">None</button><button class="btn" data-st="gaps">Still to test</button><span class="mx-msg" id="pl-prefill"></span></div>
    <div class="pl-chips" id="pl-states"></div></div>
  <div class="pl-sec"><div class="cap2">Start from (optional)</div><div class="td-tools"><select id="pl-preset"><option value="">a quick smoke, a QA tier or a layer…</option></select>
    <span class="mx-msg" id="pl-presetmsg"></span></div></div>
  <div class="pl-sec"><div class="cap2">Dimensions · values from <span id="pl-ref"></span>'s domains</div><div id="pl-dims"></div></div>
  <div class="pl-sec td-tools"><label class="td-chk"><input type="checkbox" id="pl-reduced"> reduced grid (edges only)</label>
    <label class="td-chk"><input type="checkbox" id="pl-edges" checked> edge cases</label>
    <label class="td-chk">allowance <input type="number" id="pl-allow" min="1" placeholder="no limit" style="width:90px"> calls</label>
    <label class="td-chk">name <input id="pl-name" placeholder="plan name" style="width:220px"></label></div>
</div><aside class="mx-side" id="pl-side"></aside></div></section>"""

BUILT["plan"] = PLAN_HTML

PLAN_CSS = """
.pl-sec{display:flex;flex-direction:column;gap:6px}
.pl-chips{display:flex;flex-wrap:wrap;gap:4px}
.pl-chip{font:inherit;font-size:11.5px;padding:3px 7px;border-radius:12px;border:1px solid var(--color-divider);background:#fff;cursor:pointer;color:var(--color-text)}
.pl-chip[aria-pressed="true"]{background:var(--color-accent-700);border-color:var(--color-accent-700);color:var(--color-accent-100)}
.pl-dim{border:1px solid var(--color-divider);border-radius:4px;padding:6px 8px;margin-bottom:4px;background:var(--color-bg)}
.pl-dim>label{display:flex;gap:8px;align-items:center;font-size:12.5px;cursor:pointer}
.pl-dim .pl-chips{margin:6px 0 0 22px}
.pl-grp{font:600 14px var(--font-heading);margin:8px 0 4px;border-bottom:1px solid var(--color-divider)}
.pl-count{display:grid;grid-template-columns:1fr auto;gap:2px 10px;font-size:12.5px}
.pl-count b{font:600 16px var(--font-heading);text-align:right}
.pl-big{font:400 34px var(--font-heading)}
"""

PLAN_JS = r"""
const PL={line:'CP',states:new Set(),dims:{},cat:null,allStates:[],timer:null,prev:null};
const PL_COV_GL={'Prem/Ops':['Limits','Classification'],'Prod/CO':['Limits','Classification'],'Deductibles':['Deductibles'],'Cov B · P&AI':['Coverage form'],'Cov C · Med pay':['Coverage form']};
function plRef(){return [...PL.states].sort()[0]||PL.allStates[0]||'OH';}
function plLoad(prefill){
  document.querySelectorAll('#pl-lines button').forEach(b=>b.setAttribute('aria-pressed',b.dataset.l===PL.line));
  return fetch('/api/console/catalog?lob='+PL.line).then(r=>r.json()).then(j=>{PL.allStates=j.states;
    if(prefill&&prefill.states)PL.states=new Set(prefill.states.filter(s=>j.states.includes(s)));
    plStates();return plDims(prefill);});
}
function plStates(){
  document.getElementById('pl-states').innerHTML=PL.allStates.map(s=>'<button class="pl-chip" data-s="'+s+'" aria-pressed="'+PL.states.has(s)+'" title="'+esc(BOOT.names[s]||s)+'">'+s+'</button>').join('');
  document.getElementById('pl-stc').textContent=PL.states.size+' of '+PL.allStates.length;
}
function plDims(prefill){
  const ref=plRef();document.getElementById('pl-ref').textContent=ref;
  return fetch('/api/console/catalog?lob='+PL.line+'&state='+ref).then(r=>r.json()).then(j=>{PL.cat=j.dimensions;
    if(prefill&&prefill.coverages){PL.dims={};const cov=prefill.coverages;
      j.dimensions.forEach(d=>{const hit=PL.line==='CP'?cov.includes(d.coverage):cov.some(c=>(PL_COV_GL[c]||[]).includes(d.group));
        if(hit&&d.values.length>1&&d.id!=='class_code'&&d.id!=='effective_date')PL.dims[d.id]=d.edges.slice();});}
    plDimsDraw();plPreview();});
}
function plDimsDraw(){
  let h='',grp=null;
  PL.cat.forEach(d=>{if(d.group!==grp){grp=d.group;h+='<div class="pl-grp">'+esc(grp)+'</div>';}
    const on=d.id in PL.dims,sel=new Set(PL.dims[d.id]||[]),vals=d.values,many=vals.length>16;
    h+='<div class="pl-dim"><label><input type="checkbox" data-d="'+d.id+'"'+(on?' checked':'')+(vals.length<2?' disabled':'')+'> '+esc(d.label)+' <span class="mx-msg">'+vals.length+' value'+(vals.length===1?'':'s')+(d.coverage?' · '+esc(d.coverage):'')+'</span></label>';
    if(on&&d.perState)h+='<div class="mx-msg" style="margin-left:22px">Each state uses its own edge values (its territories are its own).</div>';
    else if(on&&d.suggested){   // GL class codes: the chosen mix (with ISO's descriptions), then any other code by number
      const shown=d.suggested.concat([...sel].filter(v=>!d.suggested.includes(v)));
      h+='<div class="pl-chips">'+shown.map(v=>'<button class="pl-chip" data-d="'+d.id+'" data-v="'+esc(v)+'" aria-pressed="'+sel.has(v)+'" title="'+esc((d.labels||{})[v]||v)+'">'+esc((d.labels||{})[v]||v)+'</button>').join('')+'</div>'+
        '<div class="td-tools" style="margin:4px 0 0 22px"><span class="mx-msg">A mix of ten: manufacturing, apartments, lessor’s risk, retail, construction. Add another of the '+vals.length+' codes:</span>'+
        '<input class="pl-addcode" data-d="'+d.id+'" placeholder="class code" maxlength="5" style="width:90px"></div>';}
    else if(on)h+='<div class="pl-chips">'+(many?vals.filter(v=>sel.has(v)||d.edges.includes(v)).concat(vals.filter(v=>!sel.has(v)&&!d.edges.includes(v)).slice(0,12)):vals).map(v=>'<button class="pl-chip" data-d="'+d.id+'" data-v="'+esc(v)+'" aria-pressed="'+sel.has(v)+'">'+esc(v)+'</button>').join('')+
      (many?'<span class="mx-msg"> +'+(vals.length-12)+' more in ISO’s domain</span>':'')+'</div>';
    h+='</div>';});
  document.getElementById('pl-dims').innerHTML=h;
}
function plSpec(){const a=parseInt(document.getElementById('pl-allow').value,10);
  return {line:PL.line,states:[...PL.states].sort(),dims:PL.dims,configs:PL.configs||[],reduced:document.getElementById('pl-reduced').checked,edges:document.getElementById('pl-edges').checked,allowance:isNaN(a)?null:a};}
function plPresetNote(label){const m=document.getElementById('pl-presetmsg');const n=(PL.configs||[]).length;
  m.innerHTML=n?esc(label)+': '+n+' scenario'+(n===1?'':'s')+' per state, added to the dimensions below · <a href="#" id="pl-clearp">clear</a>':'';
  const c=document.getElementById('pl-clearp');if(c)c.onclick=e=>{e.preventDefault();PL.configs=[];document.getElementById('pl-preset').value='';plPresetNote('');plPreview();};}
fetch('/api/console/presets').then(r=>r.json()).then(j=>{PL.presets=j.presets;document.getElementById('pl-preset').innerHTML='<option value="">a quick smoke, a QA tier or a layer…</option>'+
  j.presets.map(p=>'<option value="'+p.id+'" title="'+esc(p.what)+'">'+esc(p.name)+' ('+p.line+')</option>').join('');}).catch(()=>{});
document.getElementById('pl-preset').addEventListener('change',ev=>{const p=(PL.presets||[]).find(x=>x.id===ev.target.value);if(!p)return;
  PL.line=p.line;PL.configs=p.spec.configs;PL.dims={};plLoad({states:p.spec.states}).then(()=>{plPresetNote(p.name);});});
function plPreview(){clearTimeout(PL.timer);PL.timer=setTimeout(()=>{
  const side=document.getElementById('pl-side');if(!PL.states.size){side.innerHTML='<div class="mx-msg">Choose at least one state.</div>';return;}
  side.innerHTML='<div class="mx-msg">Counting… (each scenario is built and checked against the stored answers)</div>';
  fetch('/api/console/plan/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({spec:plSpec()})}).then(r=>r.json()).then(p=>{PL.prev=p;plSide();});},350);}
function plSide(){
  const p=PL.prev;if(!p||p.error){document.getElementById('pl-side').innerHTML='<div class="td-root">'+esc(p&&p.error||'')+'</div>';return;}
  let h='<div class="cap2">This plan</div><div><span class="pl-big">'+p.calls+'</span> call'+(p.calls===1?'':'s')+' · '+p.days+' day'+(p.days===1?'':'s')+' at 150/day</div>'+
    '<div class="pl-count"><span>Cartesian (every combination)</span><b>'+p.cartesian.toLocaleString()+'</b><span>Tier 0 checks (free)</span><b>'+p.tier0+'</b>'+
    '<span>Pairwise</span><b>'+p.pairwise+'</b><span>Edge cases</span><b>'+p.edges+'</b>'+(p.presets?'<span>From the tier / layer / Workbench</span><b>'+p.presets+'</b>':'')+'<span>Already answered by ISO (reused)</span><b>'+p.alreadyAnswered+'</b>'+
    '<span>Not expressible in a state</span><b>'+p.notApplicable+'</b>'+(p.thinned?'<span>Thinned by the allowance</span><b>'+p.thinned+'</b>':'')+
    '<span>States kept</span><b>'+p.statesKept+' of '+p.states+'</b><span>Active lane left today</span><b>'+p.activeLeftToday+'</b></div>'+
    '<button class="btn" id="pl-t0">Run Tier 0 now · free</button><div id="pl-t0out"></div>'+
    '<div id="pl-conf"></div><button class="btn" id="pl-commit" style="margin-top:auto"'+(p.scenarios?'':' disabled')+'>Commit plan…</button>';
  document.getElementById('pl-side').innerHTML=h;
  document.getElementById('pl-t0').onclick=()=>{const o=document.getElementById('pl-t0out');o.innerHTML='<div class="mx-msg">Rating the invariants on our engine…</div>';
    fetch('/api/console/plan/tier0',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({line:PL.line,states:[...PL.states].sort()})}).then(r=>r.json()).then(j=>{
      o.innerHTML='<div class="mx-need"><span class="chip '+(j.failed.length?'mismatch':'verified')+'">'+(j.failed.length?'×':'✓')+'</span><div><b>'+j.passed+' of '+j.checks+' Tier 0 checks pass</b><div class="mx-msg">'+esc(j.note||'')+'</div></div></div>'+
        (j.failed.length?'<table>'+j.failed.map(f=>'<tr><td>'+f.state+' · '+esc(f.check)+'</td><td>'+esc(f.detail)+'</td></tr>').join('')+'</table>':'');});};
  document.getElementById('pl-commit').onclick=plConfirm;
}
function plConfirm(){
  const p=PL.prev,el=document.getElementById('pl-conf');
  el.innerHTML='<div class="wb-conf"><b>Commit this plan?</b><div>'+p.scenarios+' scenarios in '+p.statesKept+' state'+(p.statesKept===1?'':'s')+': <b>'+p.calls+' call'+(p.calls===1?'':'s')+'</b> from the <b>active lane</b> ('+p.activeLeftToday+' left today); '+p.alreadyAnswered+' answered already, reused at no cost.</div>'+
    '<div class="mx-msg">At 150 a day: about '+p.days+' day'+(p.days===1?'':'s')+'. Each scenario is rated on our engine now (free) to order the queue by what it would teach. The dispatcher checks the store again before every call.</div>'+
    '<div class="td-tools"><input id="pl-by" placeholder="Your name"><label class="td-chk"><input type="checkbox" id="pl-start" checked> start dispatching now</label></div>'+
    '<div class="td-tools"><button class="btn" id="pl-go">Commit</button><button class="btn" id="pl-cancel">Cancel</button></div><div class="mx-msg" id="pl-msg"></div></div>';
  document.getElementById('pl-cancel').onclick=()=>el.innerHTML='';
  document.getElementById('pl-go').onclick=()=>{document.getElementById('pl-msg').textContent='Rating each scenario on our engine and writing the plan…';
    fetch('/api/console/plan/commit',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({spec:plSpec(),name:document.getElementById('pl-name').value,
      by:document.getElementById('pl-by').value,start:document.getElementById('pl-start').checked})}).then(r=>r.json()).then(j=>{
      if(j.error){document.getElementById('pl-msg').textContent=j.error;return;}location.hash='#queue?plan='+encodeURIComponent(j.id);});};
}
document.getElementById('pl-lines').addEventListener('click',ev=>{const b=ev.target.closest('button');if(!b||b.dataset.l===PL.line)return;PL.line=b.dataset.l;PL.states=new Set();PL.dims={};plLoad();});
document.getElementById('s-plan').addEventListener('click',ev=>{
  const s=ev.target.closest('#pl-states .pl-chip');if(s){const k=s.dataset.s;PL.states.has(k)?PL.states.delete(k):PL.states.add(k);s.setAttribute('aria-pressed',PL.states.has(k));
    document.getElementById('pl-stc').textContent=PL.states.size+' of '+PL.allStates.length;if(plRef()!==document.getElementById('pl-ref').textContent)plDims();else plPreview();return;}
  const q=ev.target.closest('[data-st]');if(q){const k=q.dataset.st;
    if(k==='all')PL.states=new Set(PL.allStates);else if(k==='none')PL.states=new Set();
    else if(MX.data)PL.states=new Set((MX.data.stillToTest||[]).filter(g=>g.lob===PL.line).map(g=>g.state).filter(s=>PL.allStates.includes(s)));
    plStates();plDims();return;}
  const v=ev.target.closest('#pl-dims .pl-chip');if(v){const d=v.dataset.d,val=v.dataset.v,cur=new Set(PL.dims[d]||[]);cur.has(val)?cur.delete(val):cur.add(val);
    PL.dims[d]=PL.cat.find(x=>x.id===d).values.filter(x=>cur.has(x));v.setAttribute('aria-pressed',cur.has(val));plPreview();}
});
document.getElementById('pl-dims').addEventListener('change',ev=>{const c=ev.target.closest('input[data-d]');if(!c)return;const d=PL.cat.find(x=>x.id===c.dataset.d);
  if(c.checked)PL.dims[d.id]=(d.suggested&&d.suggested.length?d.suggested:d.edges).slice();else delete PL.dims[d.id];plDimsDraw();plPreview();});
document.getElementById('pl-dims').addEventListener('keydown',ev=>{const t=ev.target.closest('.pl-addcode');if(!t||ev.key!=='Enter')return;
  const d=PL.cat.find(x=>x.id===t.dataset.d),v=t.value.trim();if(!d.values.includes(v)){t.value='';t.placeholder='not legal here';return;}
  PL.dims[d.id]=[...new Set((PL.dims[d.id]||[]).concat(v))];plDimsDraw();plPreview();});
['pl-reduced','pl-edges','pl-allow'].forEach(i=>document.getElementById(i).addEventListener('change',plPreview));
let plStarted=false;
function plRoute(){const p=(location.hash||'').slice(1).split('?');if(p[0]!=='plan')return;const q=new URLSearchParams(p[1]||'');
  const pre=q.get('states')?{states:q.get('states').split(','),coverages:(q.get('coverages')||'').split('|').filter(Boolean)}:null;
  if(q.get('lob'))PL.line=q.get('lob')==='GL'?'GL':'CP';
  if(pre&&q.get('config')){PL.configs=[JSON.parse(q.get('config'))];plStarted=true;
    document.getElementById('pl-prefill').textContent='From the Workbench: one config in '+pre.states.length+' state(s).';plLoad({states:pre.states}).then(()=>plPresetNote('The Workbench config'));}
  else if(pre){document.getElementById('pl-prefill').textContent='Prefilled from the Readiness Matrix: '+pre.states.length+' state(s), '+pre.coverages.length+' coverage(s).';plStarted=true;plLoad(pre);}
  else if(!plStarted){plStarted=true;plLoad();}}
addEventListener('hashchange',plRoute);plRoute();
"""

# ---- TC-31 / TC-32: the Queue & Run Log ------------------------------------------------------------------------------

QUEUE_HTML = """<section class="screen" id="s-queue" hidden><div class="mx-wrap"><div class="mx-main">
  <div class="mx-head"><div><div class="eyebrow">Spending calls · every one logged</div><h1>Queue &amp; Run Log</h1></div>
    <p>Committed plans and what they spend, lane by lane; the dispatch order; every call and what came of it. Pause,
    resume, or stop a plan and keep what it found.</p></div>
  <div class="mx-stats" id="qu-lanes" style="grid-template-columns:repeat(4,minmax(0,1fr))"></div>
  <div id="qu-insp" hidden></div>
  <div class="cap2">Plans</div><div id="qu-plans"></div>
  <div class="cap2">Dispatch queue · next up</div><div id="qu-next"></div>
  <div class="cap2">Run log</div><div class="td-tools"><select id="qu-filter"><option value="">all plans</option></select></div><div id="qu-log"></div>
</div><aside class="mx-side" id="qu-side"></aside></div></section>"""

BUILT["queue"] = QUEUE_HTML

QUEUE_CSS = """
.qu-plan{border:1px solid var(--color-divider);border-radius:4px;padding:8px 10px;margin-bottom:6px;background:var(--color-bg);display:flex;flex-direction:column;gap:6px}
.qu-plan .hd{display:flex;gap:10px;align-items:baseline;flex-wrap:wrap}
.qu-plan .hd b{font:600 16px var(--font-heading)}
.qu-bar{display:flex;height:10px;border-radius:2px;overflow:hidden;background:var(--color-surface)}
.qu-bar i{display:block;height:100%}
.qu-st{font-size:11px;padding:1px 7px;border-radius:3px;border:1px solid var(--color-neutral-400)}
.qu-st.running{border-color:var(--color-accent);color:var(--color-accent-800);background:var(--color-accent-100)}
.qu-st.done{border-color:var(--color-accent-700);color:var(--color-accent-800)}
.qu-tbl{width:100%;border-collapse:collapse;font-size:12px}
.qu-tbl td{padding:4px 6px;border-top:1px solid var(--color-divider);vertical-align:top}
.qu-ev{font-size:11px;padding:1px 6px;border-radius:3px;border:1px solid var(--color-neutral-400);white-space:nowrap}
.qu-ev.match{border-color:var(--color-accent-700);color:var(--color-accent-800)}
.qu-ev.mismatch,.qu-ev.error,.qu-ev.capped{border-color:var(--ox);color:var(--ox-deep)}
.qu-ev.override{border-color:var(--ox);background:var(--ox-tint);color:var(--ox-deep)}
#qu-side td,#qu-side td:last-child{text-align:left}
"""

QUEUE_JS = r"""
const QU={plan:'',timer:null,insp:'',show:'',result:''};
function quJSON(u,b){return fetch(u,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)}).then(r=>r.json());}
function quLoad(){
  Promise.all([fetch('/api/console/cap').then(r=>r.json()),fetch('/api/console/plans').then(r=>r.json()),fetch('/api/console/runlog'+(QU.plan?'?plan='+encodeURIComponent(QU.plan):'')).then(r=>r.json()),fetch('/api/console/override').then(r=>r.json())])
  .then(([c,p,l,o])=>{drawCap(c);quLanes(c,o.override);quPlans(p.plans);quLog(l.entries);quNext(p.plans);});
}
function quLanes(c,ov){
  document.getElementById('qu-lanes').innerHTML=c.lanes.map(l=>'<div><span>'+esc(l.name)+'</span><b>'+l.used+' <small>of '+l.cap+'</small></b></div>').join('')+
    '<div><span>Today · resets 00:00 ET</span><b>'+c.left+' <small>left of '+c.cap+'</small></b>'+(ov?'<small>Override: '+ov.left+' of '+ov.calls+' left · '+esc(ov.reason)+'</small>':'')+'</div>';
}
function quPlans(ps){
  const sel=document.getElementById('qu-filter'),cur=QU.plan;sel.innerHTML='<option value="">all plans</option>'+ps.map(p=>'<option value="'+esc(p.id)+'"'+(p.id===cur?' selected':'')+'>'+esc(p.name)+' · '+esc(p.id)+'</option>').join('');
  if(!ps.length){document.getElementById('qu-plans').innerHTML='<div class="mx-empty" style="height:70px">No plans yet. Build one in the Test Plan Builder.</div>';return;}
  document.getElementById('qu-plans').innerHTML=ps.map(p=>{const n=p.scenarios||1,seg=(k,c)=>p[k]?'<i style="width:'+(100*p[k]/n)+'%;background:'+c+'" title="'+k+' '+p[k]+'"></i>':'';
    const btn=(a,l)=>'<button class="btn" data-a="'+a+'" data-id="'+esc(p.id)+'">'+l+'</button>';
    const acts=p.status==='queued'?btn('start','Start')+btn('stop','Stop and keep'):p.status==='running'?btn('pause','Pause')+btn('stop','Stop and keep'):p.status==='paused'?btn('resume','Resume')+btn('stop','Stop and keep'):'';
    return '<div class="qu-plan"><div class="hd"><b>'+esc(p.name)+'</b><span class="qu-st '+p.status+'">'+p.status+'</span><span class="mx-msg">'+esc(p.line+' · '+p.states+' state(s) · '+p.scenarios+' scenarios · committed '+p.committed_at.replace('T',' ')+(p.by?' by '+p.by:''))+'</span></div>'+
      '<div class="qu-bar">'+seg('match','var(--color-accent-700)')+seg('mismatch','var(--ox)')+seg('refused','var(--color-neutral-500)')+seg('error','var(--ox-deep)')+seg('notReached','var(--color-neutral-300)')+'</div>'+
      '<div class="mx-msg">'+p.sent+' sent · '+p.reused+' reused · '+p.match+' match · '+p.mismatch+' mismatch · '+p.refused+' refused · '+p.error+' error · '+p.queued+' queued'+(p.notReached?' · '+p.notReached+' never reached':'')+(p.notApplicable?' · '+p.notApplicable+' not expressible':'')+(p.pass3?' · pass 3 '+esc(JSON.stringify(p.pass3)):'')+'</div>'+
      '<div class="td-tools">'+acts+(p.inspection&&p.inspection.total?'<button class="btn" data-a="inspect" data-id="'+esc(p.id)+'">Inspect results'+(p.inspection.awaiting?' · '+p.inspection.awaiting+' awaiting':' · all inspected')+'</button>':'')+
      '<a href="/console/report/'+encodeURIComponent(p.id)+'" target="_blank" rel="noopener">Report</a><button class="btn" data-a="open" data-id="'+esc(p.id)+'">Scenarios</button></div></div>';}).join('');
}
function quNext(ps){
  const running=ps.filter(p=>p.status==='running');
  if(!running.length){document.getElementById('qu-next').innerHTML='<div class="mx-msg">Nothing running.</div>';return;}
  Promise.all(running.map(p=>fetch('/api/console/plan?id='+encodeURIComponent(p.id)).then(r=>r.json()))).then(full=>{
    const q=full.flatMap(p=>p.scenarios.filter(s=>s.status==='queued'||s.status==='reuse').map(s=>({...s,plan:p.name}))).sort((a,b)=>(b.status==='reuse')-(a.status==='reuse')||b.score-a.score).slice(0,10);
    document.getElementById('qu-next').innerHTML='<table class="qu-tbl">'+q.map(s=>'<tr><td>'+s.state+'</td><td>'+esc(Object.entries(s.config).map(([k,v])=>k+'='+v).join(', ')||'base risk')+'</td><td>'+esc(s.kind)+'</td><td>'+(s.status==='reuse'?'stored answer, no call':'score '+s.score)+'</td><td class="mx-msg">'+esc(s.plan)+'</td></tr>').join('')+'</table>';});
}
function quLog(es){
  document.getElementById('qu-log').innerHTML=es.length?'<table class="qu-tbl">'+es.slice(0,150).map(e=>{const k=e.outcome||e.event;
    return '<tr><td class="mx-msg">'+esc(e.at.replace('T',' '))+'</td><td><span class="qu-ev '+esc(k)+'">'+esc(e.event==='sent'?'sent · '+(e.outcome||''):e.event)+'</span></td><td>'+esc(e.state||'')+'</td><td>'+
      (e.scenario?'<a href="#trace?scenario='+encodeURIComponent(e.scenario)+'">'+esc(e.scenario)+'</a> · ':'')+esc(e.detail||'')+'</td></tr>';}).join('')+'</table>':'<div class="mx-msg">No events yet.</div>';
}
function quSide(){
  const s=document.getElementById('qu-side');
  s.innerHTML='<div class="cap2">Override the cap (TC-32)</div><div class="mx-msg">For today only: lets the dispatcher go past a full lane for this many calls, each logged with the reason.</div>'+
    '<div class="td-cls" style="display:flex;flex-direction:column;gap:6px"><input id="qu-reason" placeholder="Reason"><input id="qu-calls" type="number" min="1" placeholder="Calls"><input id="qu-by" placeholder="Your name"><button class="btn" id="qu-ov">Set override</button><div class="mx-msg" id="qu-ovmsg"></div></div>'+
    '<div class="cap2">Refused payloads (D16)</div><div id="qu-ref" class="mx-msg">Loading…</div>'+
    '<div class="cap2">Earlier run files (D17)</div><div id="qu-runs" class="mx-msg">Loading…</div>';
  document.getElementById('qu-ov').onclick=()=>quJSON('/api/console/override',{reason:document.getElementById('qu-reason').value,calls:document.getElementById('qu-calls').value,by:document.getElementById('qu-by').value})
    .then(j=>{document.getElementById('qu-ovmsg').textContent=j.error?j.error:'Set: '+j.calls+' call(s) past the cap today.';quLoad();});
  fetch('/api/console/refused').then(r=>r.json()).then(j=>{document.getElementById('qu-ref').innerHTML=j.total+' refusals stored.<table>'+j.refused.slice(0,25).map(x=>'<tr><td><a href="#trace?lob='+x.line+'&scenario='+encodeURIComponent(x.scenario)+'">'+esc(x.scenario)+'</a><div class="mx-msg">'+esc(x.message.slice(0,140))+'</div></td></tr>').join('')+'</table>';});
  fetch('/api/console/runs').then(r=>r.json()).then(j=>{document.getElementById('qu-runs').innerHTML='<a href="/runs/index.html" target="_blank" rel="noopener">The standalone run files (/tests) ↗</a><div class="mx-msg">'+j.total+' runs in the GL run store; click one for its rows.</div><table>'+
    j.runs.slice(0,40).map(x=>'<tr data-run="'+esc(x.id)+'" style="cursor:pointer"><td>'+esc((x.at||'').slice(0,16))+'<div class="mx-msg">'+esc(x.describes||x.label||x.id)+'</div></td><td>'+(x.compared?(x.agree||0)+'/'+(x.total||0)+' agree':'ours only')+'</td></tr>').join('')+'</table>';
    document.querySelectorAll('#qu-runs tr[data-run]').forEach(tr=>tr.onclick=()=>quRun(tr.dataset.run));});
}
function quRun(id){
  fetch('/api/console/runs?id='+encodeURIComponent(id)).then(r=>r.json()).then(l=>{const s=l.summary||{};
    document.getElementById('qu-side').innerHTML='<a href="#" class="mx-back" id="qu-back">← Overrides and files</a><div class="cap2">Run '+esc(id)+'</div><div>'+esc(s.describes||l.label||'')+'</div>'+
      '<div class="mx-msg">'+esc((l.at_iso||'').replace('T',' '))+' · '+esc(s.mode||'')+' · as of '+esc(s.asof||'')+(s.compared?' · compared with ISO':' · ours only')+'</div><table class="qu-tbl">'+
      (l.rows||[]).map(r=>'<tr><td>'+esc(r.juris||'')+'</td><td>'+esc(r.status||'')+'</td><td class="v">'+esc(r.ours||'')+'</td><td class="v">'+esc(r.iso||'')+'</td><td class="mx-msg">'+esc((r.detail||r.first_differences||'').slice(0,120))+'</td></tr>').join('')+'</table>';
    document.getElementById('qu-back').onclick=e=>{e.preventDefault();quSide();};});
}
document.getElementById('qu-plans').addEventListener('click',ev=>{const b=ev.target.closest('button[data-a]');if(!b)return;
  if(b.dataset.a==='inspect'){location.hash='#queue?inspect='+encodeURIComponent(b.dataset.id);return;}
  if(b.dataset.a==='open'){fetch('/api/console/plan?id='+encodeURIComponent(b.dataset.id)).then(r=>r.json()).then(p=>{document.getElementById('qu-side').innerHTML='<a href="#" class="mx-back" id="qu-back">← Overrides and files</a><div class="cap2">'+esc(p.name)+'</div><table class="qu-tbl">'+
    p.scenarios.map(s=>'<tr><td>'+s.state+'<div class="mx-msg">'+esc(Object.entries(s.config).map(([k,v])=>k+'='+v).join(', ')||'base risk')+'</div></td><td>'+esc(s.status)+'</td><td>'+(s.scenario?'<a href="#trace?scenario='+encodeURIComponent(s.scenario)+'">diff</a>':'')+'</td></tr>').join('')+'</table>';
    document.getElementById('qu-back').onclick=e=>{e.preventDefault();quSide();};});return;}
  quJSON('/api/console/plan/control',{id:b.dataset.id,action:b.dataset.a}).then(()=>quLoad());});
document.getElementById('qu-filter').addEventListener('change',ev=>{QU.plan=ev.target.value;quLoad();});
let quStarted=false;
function quInsp(){
  const el=document.getElementById('qu-insp');if(!QU.insp){el.hidden=true;el.innerHTML='';return;}el.hidden=false;
  fetch('/api/console/inspect/plan?id='+encodeURIComponent(QU.insp)).then(r=>r.json()).then(v=>{
    if(v.error){el.innerHTML='<div class="mx-msg">'+esc(v.error)+'</div>';return;}
    const c=v.counts,n=c.total||1,show=QU.show||(c.awaiting?'awaiting':'all');
    const seg=(k,col)=>c[k]?'<i style="width:'+(100*c[k]/n)+'%;background:'+col+'" title="'+k+' '+c[k]+'"></i>':'';
    const rows=v.rows.filter(r=>(show==='all'||!r.verdict)&&(!QU.result||r.result===QU.result));
    const nm=v.rows.filter(r=>r.result==='match'&&!r.verdict).length;
    const chip=(k,val,l)=>'<button class="pl-chip" data-f="'+k+'" data-v="'+val+'" aria-pressed="'+((k==='show'?show:QU.result)===val)+'">'+l+'</button>';
    const msg=m=>{const x=/"Message":"([^"]*)"/.exec(m);return x?x[1]:m;};
    // settings every result shares are said once, above the table; a row shows only what differs
    const keys=[...new Set(v.rows.flatMap(r=>Object.keys(r.config)))];
    const same=keys.filter(k=>v.rows.every(r=>k in r.config&&String(r.config[k])===String(v.rows[0].config[k])));
    const own=r=>Object.entries(r.config).filter(([k])=>!same.includes(k)).map(([k,x])=>k+'='+x).join(', ');
    let h='<div class="qu-plan" style="gap:10px"><div class="in-hd"><a href="#queue" id="in-back">‹ Plans</a><b>Inspect results · '+esc(v.name)+'</b><span class="mx-msg">'+esc(v.line+' · '+v.status+' · '+v.plan)+'</span></div>'+
      '<div class="in-hd"><span class="in-bar">'+seg('pass','var(--color-accent-700)')+seg('fail','var(--ox)')+seg('excuse','var(--color-neutral-500)')+'</span><span>'+c.inspected+' of '+c.total+' inspected</span>'+
      '<span class="mx-msg">'+c.pass+' ✓ passed · '+c.fail+' × failed · '+c.excuse+' ⊘ excused · <b>'+c.awaiting+' awaiting</b></span></div>'+
      '<div class="td-tools in-flt">Show '+chip('show','awaiting','Awaiting')+chip('show','all','All')+' · Result '+chip('result','','All')+chip('result','match','Match')+chip('result','mismatch','Mismatch')+chip('result','refused','Refused')+chip('result','error','Error')+
      '<label class="mx-msg" style="margin-left:auto">Your name <input id="in-by" value="'+esc(IV.by)+'" style="width:120px"></label>'+
      (nm?'<button class="btn iv-pass" id="in-all">✓ Pass all '+nm+' matches</button>':'')+'</div>'+
      (same.length?'<div class="mx-msg">Every result: '+esc(same.map(k=>k+'='+v.rows[0].config[k]).join(', '))+'</div>':'')+
      '<table class="qu-tbl in-tbl"><tr><td><b>St</b></td><td><b>Scenario</b></td><td class="n"><b>Ours</b></td><td class="n"><b>ISO</b></td><td><b>Auto</b></td><td><b>Inspector</b></td><td></td></tr>'+
      (rows.length?rows.map(r=>'<tr><td><b>'+esc(r.state)+'</b></td><td>'+esc(own(r)||(same.length?'the plan\'s risk':'base risk'))+
        (r.message?'<div class="mx-msg">'+esc(msg(r.message))+'</div>':'')+'</td><td class="n">'+esc(r.ours==null?'—':r.ours)+'</td><td class="n">'+esc(r.iso==null?'—':r.iso)+'</td>'+
        '<td><span class="qu-ev '+esc(r.result)+'">'+esc(r.result)+'</span></td><td>'+ivHTML(r.scenario,v.plan,r.verdict)+'</td><td><a href="#trace?scenario='+encodeURIComponent(r.scenario)+'">Trace ↗</a></td></tr>').join('')
        :'<tr><td colspan="7" class="mx-msg">'+(show==='awaiting'?'Nothing awaiting inspection.':'No results match the filter.')+'</td></tr>')+'</table>'+
      '<div class="td-tools">'+(v.signoff?'<span class="iv-done pass">Signed off by '+esc(v.signoff.by)+' · '+esc(ivWhen(v.signoff.at))+' · '+esc(v.signoff.reason)+'</span>':
        '<button class="btn" id="in-sign"'+(c.awaiting?' disabled title="'+c.awaiting+' still awaiting"':'')+'>Sign off this plan</button><span class="mx-msg" id="in-msg">'+(c.awaiting?'Enabled once nothing is awaiting.':'Records your name and the counts.')+'</span>')+
      '<a href="/console/report/'+encodeURIComponent(v.plan)+'" target="_blank" rel="noopener">Report ↗</a></div></div>';
    el.innerHTML=h;
    document.getElementById('in-by').onchange=e=>ivSetBy(e.target.value.trim());
    el.querySelectorAll('[data-f]').forEach(b=>b.onclick=()=>{if(b.dataset.f==='show')QU.show=b.dataset.v;else QU.result=b.dataset.v;quInsp();});
    const all=document.getElementById('in-all');if(all)all.onclick=()=>{all.disabled=true;quJSON('/api/console/inspect/pass-matches',{plan:v.plan,by:IV.by}).then(()=>{quInsp();quLoad();});};
    const sg=document.getElementById('in-sign');if(sg)sg.onclick=()=>quJSON('/api/console/inspect/signoff',{plan:v.plan,by:IV.by}).then(j=>{if(j.error){document.getElementById('in-msg').textContent=j.error;return;}quInsp();});
  });
}
document.addEventListener('iv:changed',()=>{if(QU.insp&&!document.getElementById('s-queue').hidden){quInsp();quLoad();}});
function quRoute(){const p=(location.hash||'').slice(1).split('?');if(p[0]!=='queue')return;const q=new URLSearchParams(p[1]||'');QU.plan=q.get('plan')||QU.plan;
  const ins=q.get('inspect')||'';if(ins!==QU.insp){QU.insp=ins;QU.show='';QU.result='';}quInsp();
  quLoad();if(!quStarted){quStarted=true;quSide();}clearInterval(QU.timer);QU.timer=setInterval(()=>{if(!document.getElementById('s-queue').hidden)quLoad();},5000);}
addEventListener('hashchange',quRoute);quRoute();
"""


# ---- TC-33..TC-35: the Regression Library ---------------------------------------------------------------------------
# Every promoted scenario with its reference, the content version and date it was verified on, its last build's result
# and its defect history (D18); a free re-run; the stale answers and a refresh plan for the refresh lane.

LIB_HTML = """<section class="screen" id="s-library" hidden><div class="mx-wrap"><div class="mx-main">
  <div class="mx-head"><div><div class="eyebrow">Keeping it true · re-run on every build, free</div><h1>Regression Library</h1></div>
    <p>Every scenario we trust: ISO's fixtures, the golden cases, the app's samples and what you promote. Each re-run
    rates them all on today's engine against their reference and spends nothing.</p></div>
  <div class="mx-stats" id="lb-stats" style="grid-template-columns:repeat(5,minmax(0,1fr))"></div>
  <div class="td-tools"><button class="btn" id="lb-rerun">Re-run now · free</button><span class="mx-msg" id="lb-prog"></span></div>
  <div class="td-tools lb-filters">
    <select id="lb-line"><option value="">both lines</option><option>CP</option><option>GL</option></select>
    <select id="lb-origin"><option value="">every origin</option><option value="fixture">ISO fixtures</option><option value="golden">golden cases</option><option value="sample">samples</option><option value="trace">promoted from Trace Diff</option><option value="workbench">promoted from the Workbench</option></select>
    <select id="lb-result"><option value="">every result</option><option value="pass">pass</option><option value="fields">premiums pass, a number differs</option><option value="diverged">diverged</option><option value="refused">refused</option><option value="error">error</option><option value="never">not run yet</option><option value="open">open defects</option></select>
    <select id="lb-ref"><option value="">either reference</option><option value="iso">ISO's answer</option><option value="ours">our own premium</option></select>
    <input id="lb-state" placeholder="State" maxlength="2" style="width:64px"><span class="mx-msg" id="lb-count"></span></div>
  <div class="mx-scroll"><table class="qu-tbl" id="lb-table"></table></div>
</div><aside class="mx-side" id="lb-side"></aside></div></section>"""

BUILT["library"] = LIB_HTML

LIB_CSS = """
.lb-filters select,.lb-filters input{font:inherit;padding:5px 7px;border:1px solid var(--color-divider);border-radius:4px;background:#fff}
#lb-table th{font-size:10.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--color-neutral-700);text-align:left;padding:4px 6px;border-bottom:1px solid var(--color-text)}
.lb-r{font-size:11px;padding:1px 6px;border-radius:3px;border:1px solid var(--color-neutral-400);white-space:nowrap}
.lb-r.pass{border-color:var(--color-accent-700);color:var(--color-accent-800);background:var(--color-accent-100)}
.lb-r.fields{border-color:var(--color-accent-400);color:var(--color-accent-800)}
.lb-r.diverged,.lb-r.error{border-color:var(--ox);color:var(--ox-deep);background:var(--ox-tint)}
#lb-side td,#lb-side td:last-child{text-align:left}
"""

LIB_JS = r"""
const LB={data:null,timer:null};
function lbLoad(){return fetch('/api/console/library').then(r=>r.json()).then(d=>{const was=LB.data&&LB.data.lastRun&&LB.data.lastRun.run;LB.data=d;lbDraw();lbProg(d.progress);if(was&&d.lastRun&&d.lastRun.run!==was)lbSide();});}
function lbProg(p){const m=document.getElementById('lb-prog'),b=document.getElementById('lb-rerun');
  if(p){m.textContent='Re-running: '+p.done+' of '+p.total+' · '+p.seconds+' s';b.disabled=true;clearTimeout(LB.timer);LB.timer=setTimeout(lbLoad,3000);}
  else{b.disabled=false;const r=LB.data&&LB.data.lastRun;m.textContent=r?'Last run '+r.run+' on build '+r.build+' · '+r.seconds+' s · '+r.callsSpent+' calls':'Never run.';}}
function lbDraw(){
  const d=LB.data,r=d.lastRun,c=(r&&r.counts)||{},E=d.entries;
  const n=k=>c[k]||0;
  document.getElementById('lb-stats').innerHTML='<div><span>Scenarios</span><b>'+E.length+'</b><small>'+E.filter(e=>e.reference==='iso').length+' against ISO</small></div>'+
    '<div><span>Pass</span><b>'+(n('pass')+n('fields'))+'</b><small>'+n('pass')+' clean on every number</small></div>'+
    '<div><span>Diverged</span><b>'+n('diverged')+'</b><small>a premium moved</small></div>'+
    '<div><span>Refused / error</span><b>'+(n('refused')+n('error'))+'</b></div>'+
    '<div><span>Open defects</span><b>'+E.filter(e=>e.open).length+'</b><small>first / last seen kept</small></div>';
  const f=id=>document.getElementById(id).value,st=document.getElementById('lb-state').value.trim().toUpperCase();
  const rows=E.filter(e=>(!f('lb-line')||e.line===f('lb-line'))&&(!f('lb-origin')||e.origin===f('lb-origin'))&&(!f('lb-ref')||e.reference===f('lb-ref'))&&(!st||e.state===st)&&
    (!f('lb-result')||(f('lb-result')==='never'?!e.last:f('lb-result')==='open'?e.open:e.last&&e.last.result===f('lb-result'))));
  document.getElementById('lb-count').textContent=rows.length+' shown';
  document.getElementById('lb-table').innerHTML='<tr><th>Scenario</th><th>Line</th><th>St.</th><th>Origin</th><th>Reference</th><th>Content</th><th>Verified</th><th>Last build</th><th>Defect</th></tr>'+
    rows.slice(0,400).map(e=>{const l=e.last;return '<tr><td>'+(e.reference==='iso'&&!e.scenario.startsWith('FX-')&&!e.scenario.startsWith('SAMPLE-')?'<a href="#trace?scenario='+encodeURIComponent(e.scenario)+'">'+esc(e.scenario)+'</a>':esc(e.scenario))+'</td><td>'+e.line+'</td><td>'+e.state+'</td><td>'+esc(e.origin)+'</td><td>'+(e.reference==='iso'?'ISO':'ours')+'</td>'+
      '<td class="mx-msg">'+esc(e.contentVersion||'')+(e.freshness==='stale'?' · <b>stale</b>':'')+'</td><td class="mx-msg">'+esc((e.verified||'').slice(0,10))+'</td>'+
      '<td>'+(l?'<span class="lb-r '+l.result+'" title="'+esc(l.detail||'')+'">'+esc(l.result==='fields'?'premiums pass':l.result)+'</span> <span class="mx-msg">'+esc(l.build)+'</span>':'<span class="mx-msg">not run</span>')+'</td>'+
      '<td class="mx-msg">'+(e.firstSeen?'first '+esc(e.firstSeen.at.slice(0,10))+' ('+esc(e.firstSeen.build)+')'+(e.open?', open':', last '+esc(e.lastSeen.at.slice(0,10))):'')+'</td></tr>';}).join('')+
    (rows.length>400?'<tr><td colspan="9" class="mx-msg">The first 400 of '+rows.length+'; narrow the filters.</td></tr>':'');
}
function lbChanges(){
  const c=LB.data&&LB.data.changes;if(!c)return '<div class="cap2">Since the previous run</div><div class="mx-msg">One run so far.</div>';
  const n=(k,l)=>'<span>'+l+'</span><b>'+c[k].length+'</b>';
  return '<div class="cap2">Since the previous run</div><div class="mx-msg">'+esc(c.from.run)+' ('+esc(c.from.build)+') → '+esc(c.to.run)+' ('+esc(c.to.build)+')</div><div class="pl-count">'+
    n('fixed','Fixed')+n('new','Newly failing')+n('still','Still failing')+n('newlyRefusing','Newly refusing')+n('premiumMoved','Our premium moved')+n('added','Added to the library')+'</div>'+
    (c.premiumMoved.length?'<table>'+c.premiumMoved.slice(0,15).map(m=>'<tr><td>'+esc(m.scenario)+'</td><td>'+esc(m.was)+' → '+esc(m.now)+'</td></tr>').join('')+'</table>':'')+
    (c.new.length?'<div class="mx-msg">Newly failing: '+esc(c.new.slice(0,15).join(', '))+'</div>':'');
}
function lbSide(){
  const s=document.getElementById('lb-side');s.innerHTML='<div class="cap2">Stale answers (TC-35)</div><div class="mx-msg">Loading…</div>';
  fetch('/api/console/library/stale').then(r=>r.json()).then(j=>{
    let h=lbChanges()+'<div class="cap2">Stale answers (TC-35)</div><div class="mx-msg">ISO answered these on a package that is no longer the one in force for their state and date. A refresh re-sends the same request in the refresh lane (50 a day).</div>'+
      '<div class="pl-count"><span>Full answers, stale</span><b>'+j.answers.length+'</b><span>... with their request on disk (can be re-sent)</span><b>'+j.sendable+'</b><span>GL premium-level rows, stale</span><b>'+j.premiumRows.length+'</b></div>';
    h+=j.answers.length?'<table>'+j.answers.slice(0,20).map(a=>'<tr><td>'+esc(a.line+' '+a.state+' · '+a.date)+'<div class="mx-msg">'+esc(a.stale_reason)+'</div><div class="mx-msg"><b>'+
      (a.remedy==='corpus'?'ISO is ahead of our corpus: asking again changes nothing; the corpus needs '+esc(a.iso_package):'Our corpus moved on: a re-send gets the current answer')+'</b></div></td></tr>').join('')+'</table>':'';
    if(j.premiumRows.length)h+='<div class="mx-msg">The premium-level GL rows hold no request to re-send: re-run their QA configs (Test Plan Builder) instead. '+esc([...new Set(j.premiumRows.map(r=>r.state))].join(', '))+'.</div>';
    if(j.sendable)h+='<div id="lb-conf"></div><button class="btn" id="lb-refresh">Queue a refresh · '+j.sendable+' call'+(j.sendable===1?'':'s')+'…</button>';
    s.innerHTML=h;
    const b=document.getElementById('lb-refresh');if(b)b.onclick=()=>{document.getElementById('lb-conf').innerHTML='<div class="wb-conf"><b>Queue a refresh plan?</b><div>'+j.sendable+' request'+(j.sendable===1?'':'s')+' re-sent in the <b>refresh lane</b> when you start the plan in the Queue. Nothing is spent until then.</div>'+
      '<div class="td-tools"><input id="lb-by" placeholder="Your name"><button class="btn" id="lb-go">Queue it</button><button class="btn" id="lb-cancel">Cancel</button></div><div class="mx-msg" id="lb-msg"></div></div>';
      document.getElementById('lb-cancel').onclick=()=>document.getElementById('lb-conf').innerHTML='';
      document.getElementById('lb-go').onclick=()=>fetch('/api/console/library/refresh',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({by:document.getElementById('lb-by').value})})
        .then(r=>r.json()).then(p=>{if(p.error){document.getElementById('lb-msg').textContent=p.error;return;}location.hash='#queue?plan='+encodeURIComponent(p.id);});};
  });
}
document.getElementById('lb-rerun').onclick=()=>fetch('/api/console/library/rerun',{method:'POST'}).then(r=>r.json()).then(j=>{if(j.error)document.getElementById('lb-prog').textContent=j.error;setTimeout(lbLoad,1500);});
['lb-line','lb-origin','lb-result','lb-ref','lb-state'].forEach(i=>document.getElementById(i).addEventListener(i==='lb-state'?'input':'change',()=>LB.data&&lbDraw()));
let lbStarted=false;function lbRoute(){if(!(location.hash||'').startsWith('#library')||lbStarted)return;lbStarted=true;lbLoad();lbSide();}
addEventListener('hashchange',lbRoute);lbRoute();
"""


# ---- Results inspection: a person's verdict on each plan result (pass / fail / excuse), beside ISO's agreement -------

INSP_CSS = """
.iv{display:inline-flex;gap:4px;align-items:center;flex-wrap:nowrap;white-space:nowrap}
.in-tbl td:nth-child(6),.in-tbl td:nth-child(7){white-space:nowrap}
.iv .btn{padding:2px 8px;font-size:12px}
.iv .btn.iv-pass{border-color:var(--color-accent-700);color:var(--color-accent-800)}
.iv .btn.iv-fail{border-color:var(--ox);color:var(--ox-deep)}
.iv .btn.iv-exc{border-color:var(--color-neutral-500);color:var(--color-neutral-800)}
.iv-done{font-size:12px;white-space:nowrap}
.iv-done.pass{color:var(--color-accent-800)}.iv-done.fail{color:var(--ox-deep)}.iv-done.excuse{color:var(--color-neutral-700)}
.iv-done a{margin-left:6px}
.iv-form{display:flex;flex-direction:column;gap:6px;border:1px dashed var(--ox);border-radius:4px;padding:8px;margin-top:6px;max-width:460px;background:var(--color-bg)}
.iv-form input,.iv-form select{font:inherit;padding:4px 6px}
.td-head .insp-slot{margin-left:auto}
.in-hd{display:flex;gap:12px;align-items:baseline;flex-wrap:wrap}
.in-hd b{font:600 18px var(--font-heading)}
.in-bar{display:flex;height:12px;border-radius:2px;overflow:hidden;background:var(--color-surface);max-width:420px;flex:1 1 220px}
.in-bar i{display:block;height:100%}
.in-flt .pl-chip{font-size:12px}
.qu-tbl td.n{text-align:right;font-variant-numeric:tabular-nums}
.bd-c.aw{position:relative}
.bd-c.aw::after{content:"";position:absolute;top:2px;right:2px;width:6px;height:6px;border-radius:50%;background:var(--ox)}
.bd-stats div.aw{cursor:pointer}
"""

INSP_JS = r"""
const IV={by:''};
try{IV.by=localStorage.getItem('tc.by')||'';}catch(e){}
function ivSetBy(v){IV.by=v;try{localStorage.setItem('tc.by',v);}catch(e){}}
function ivWhen(at){return (at||'').replace('T',' ').slice(5,16);}
function ivHTML(sid,plan,v){
  if(v){const L={pass:'✓ Passed',fail:'× Failed',excuse:'⊘ Excused'}[v.verdict]||v.verdict;
    return '<span class="iv-done '+v.verdict+'" title="'+esc((v.reason||'')+(v.category?' · '+v.category.replace(/_/g,' '):''))+'">'+L+(v.by?' · '+esc(v.by):'')+' '+esc(ivWhen(v.at))+
      '<a href="#" data-iv="undo" data-sid="'+esc(sid)+'" data-plan="'+esc(plan||'')+'">undo</a></span>';}
  return '<span class="iv"><button class="btn iv-pass" data-iv="pass" data-sid="'+esc(sid)+'" data-plan="'+esc(plan||'')+'" title="Our result is right">✓ Pass</button>'+
    '<button class="btn iv-fail" data-iv="fail" data-sid="'+esc(sid)+'" data-plan="'+esc(plan||'')+'" title="Our result is wrong (reason and category)">× Fail</button>'+
    '<button class="btn iv-exc" data-iv="excuse" data-sid="'+esc(sid)+'" data-plan="'+esc(plan||'')+'" title="Not a test of our engine (reason)">⊘ Excuse</button></span>';
}
function ivFill(root){   // every .insp-slot[data-sid] under root gets its verdict or the buttons
  const slots=[...(root||document).querySelectorAll('.insp-slot[data-sid]')];if(!slots.length)return;
  const ids=[...new Set(slots.map(s=>s.dataset.sid))];
  fetch('/api/console/inspect/verdicts?ids='+encodeURIComponent(ids.join(','))).then(r=>r.json()).then(v=>{
    slots.forEach(s=>{s.innerHTML=ivHTML(s.dataset.sid,s.dataset.plan,v[s.dataset.sid]);});});
}
function ivPost(body){
  return fetch('/api/console/inspect',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...body,by:IV.by})}).then(r=>r.json());
}
function ivChanged(sid){document.dispatchEvent(new CustomEvent('iv:changed',{detail:{scenario:sid}}));}
document.addEventListener('click',ev=>{
  const b=ev.target.closest('[data-iv]');if(!b)return;ev.preventDefault();
  const sid=b.dataset.sid,plan=b.dataset.plan,v=b.dataset.iv;
  if(v==='pass'||v==='undo'){ivPost({scenario:sid,verdict:v,plan:plan}).then(j=>{if(j.error){alertless(b,j.error);return;}ivChanged(sid);});return;}
  const host=b.closest('.iv')||b.parentNode;const old=host.parentNode.querySelector('.iv-form');if(old)old.remove();
  const f=document.createElement('div');f.className='iv-form';
  f.innerHTML='<b>'+(v==='fail'?'× Fail':'⊘ Excuse')+' · '+esc(sid)+'</b>'+
    (v==='fail'?'<select class="iv-cat"><option value="">Category…</option>'+BOOT.categories.map(c=>'<option value="'+c.key+'" title="'+esc(c.meaning)+'">'+esc(c.label)+'</option>').join('')+'</select>':'')+
    '<input class="iv-why" placeholder="'+(v==='fail'?'What is wrong':'Why this is not a test of our engine')+'">'+
    '<input class="iv-by" placeholder="Your name" value="'+esc(IV.by)+'">'+
    '<div class="td-tools"><button class="btn iv-save">Save</button><button class="btn iv-cancel">Cancel</button><span class="mx-msg iv-msg"></span></div>';
  host.after(f);f.querySelector('.iv-why').focus();
  f.querySelector('.iv-cancel').onclick=e=>{e.preventDefault();f.remove();};
  f.querySelector('.iv-save').onclick=e=>{e.preventDefault();ivSetBy(f.querySelector('.iv-by').value.trim());
    const cat=f.querySelector('.iv-cat');
    ivPost({scenario:sid,verdict:v,plan:plan,reason:f.querySelector('.iv-why').value,category:cat?cat.value:''}).then(j=>{
      if(j.error){f.querySelector('.iv-msg').textContent=j.error;return;}f.remove();ivChanged(sid);});};
});
function alertless(el,msg){const m=document.createElement('span');m.className='mx-msg';m.textContent=' '+msg;el.after(m);setTimeout(()=>m.remove(),5000);}
document.addEventListener('iv:changed',()=>ivFill(document));
"""
